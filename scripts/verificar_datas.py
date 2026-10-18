#!/usr/bin/env python3
"""Verifica datas e valores potencialmente expirados em todos os HTML da raiz.

Cada correspondência de data é avaliada com o ano que ela própria capta —
não com uma verificação solta de "o ano antigo aparece algures nesta
página". Só é tratada como expirada se esse ano for anterior ao ano actual
E não estiver explicado por um contexto legítimo: referência legal/
histórica (portaria, decreto-lei, despacho, "em vigor desde", "desde
<ano>"), exemplo ilustrativo de cálculo, citação dentro de um link (nome
de outra página), ou aviso explícito de conteúdo pendente ("aguarda",
"previsto", "confirmar") cujo prazo anunciado ainda não passou.

Frases como "rendimentos de 2025 para prestações de 2026" ou "Em 2025,
o valor era X" nunca precisam de um marcador de supressão dedicado: não
têm nome de mês nem formato de data reconhecido por nenhum PADRAO, por
isso nunca entram no ramo de "ano antigo" a começar.

Issue #183, passo 2 — portão de confirmação: um marcador de
MARCADORES_HISTORICOS só suprime PERMANENTEMENTE uma ocorrência se a
própria data protegida for anterior (ou igual) ao carimbo "Verificado a"
da página. Uma data posterior a esse carimbo descreve um compromisso
ainda por cumprir à última verificação — um prazo em vigor que a lei
pode prorrogar, nunca um facto já fechado (ex.: "contratos celebrados
até 31 de dezembro de 2026", garantia-publica-credito-habitacao.html:
o mesmo marcador `celebrados?\\s+at[ée]\\b` que fecha correctamente o
PAER, já ultrapassado, mascarava para sempre um prazo que ainda nem
chegou). Nesse caso o marcador comporta-se como MARCADORES_PENDENTE:
suprimido só até a data passar, depois exposto. Sem carimbo (só
fontes.html, entre as páginas com citações de diploma), preserva-se o
comportamento anterior — nunca "sem carimbo = expõe tudo", que
regrediria as dezenas de citações permanentes dessa página só por lhe
faltar a referência; ver o carimbo acrescentado a fontes.html no mesmo
commit desta correcção.

Carimbos de verificação (issue #332): a data de um carimbo
("Verificado a 2 de setembro de 2026", "Verificado 24/06/2026", "Fontes
verificadas — 2 de setembro de 2026", "Última atualização: …", "confirmado
a …" — lista completa junto a REGEX_CARIMBO) diz quando
a página foi conferida, não descreve um facto com validade no ano civil.
Por isso fica fora da lógica de ano civil de `_pagina_tem_alerta` (e dos
marcadores de supressão) e tem regra própria: alerta `carimbo_antigo`
quando um carimbo tem mais de LIMITE_MESES_CARIMBO meses face ao mês de
execução, em qualquer mês do ano.

Âmbito deliberado, sem data prevista de expansão: só os 3 tipos com uma
data própria e sem ambiguidade — data_mes_ano, data_numerica,
prazo_outono. `ano_letivo` (par de anos, sem dia) e `valor_ias` (ano
solto na janela, sem grupo dedicado) ficam de fora — nenhum caso
concreto os exige, e derivar uma data única a partir deles seria
ambíguo (ver CLAUDE.md, secção do portão de confirmação).
"""

import glob
import html as _html
import json
import os
import re
from datetime import date, datetime

from classificar_datas import classificar_data_estruturada
from decisao_datas import decidir_acao_estruturada
from sincronizar_clusters import verificado_em_do_texto

# Ficheiros que o pipeline gera — ignorar
AUTO_GERADOS = ["index.html", "noticias.html", "404.html"]

JANELA = 220  # caracteres de contexto para cada lado da correspondência
JANELA_LINK = 300  # caracteres a olhar para trás ao detectar se está dentro de um <a>

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

REGEX_MES_ANO = (
    r"\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|"
    r"setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})\b"
)

# Carimbo de verificação: "Verificado a 2 de setembro de 2026", "Verificado
# a 2 setembro 2026", "Verificado a 02/09/2026", as notas por secção
# "Verificado 24/06/2026" (sem "a") e o cabeçalho do bloco de fontes
# "Fontes verificadas — 7 de setembro de 2026". Os grupos captam só a data.
# Também (#332, PR 3) as outras formas cuja data certifica conteúdo
# publicado, visível ou em comentário HTML/JS: "Última atualização: …",
# "confirmado(s)/confirmada(s) a …", "Datas confirmadas na Segurança Social
# a …", "caminho conferido pelo Nuno a …", "confirmados em várias fontes
# secundárias independentes (…)", "À data de verificação desta página (…)",
# "Lido por inteiro em fonte primária (…)", "lida directamente a …" e
# "Verificado via pesquisa … — DD/MM/AAAA" (#332, PR A). Ficam de fora as
# frases de conteúdo ("revisão urgente em agosto de 2025", "valores
# actualizados produzem efeitos desde …"). Só para esta regra:
# verificado_em_do_texto (portão do #187) tem regex própria e continua a ler
# só "Verificado a …".
_MESES_RE = (
    r"janeiro|fevereiro|março|abril|maio|junho|julho|agosto|"
    r"setembro|outubro|novembro|dezembro"
)
REGEX_CARIMBO = (
    r"(?:\bverificad[oa]\s+(?:a\s+)?|\bfontes\s+verificadas\s*[—–-]\s*"
    r"|(?<!\w)[úu]ltima\s+atualiza[çc][ãa]o:\s*"
    r"|\bconfirmad[oa]s?\s+(?:na\s+segurança\s+social\s+)?a\s+"
    r"|\bconferid[oa]s?\s+pel[oa]\s+\w+\s+a\s+"
    r"|\bconfirmad[oa]s?\s+em\s+várias\s+fontes\s+secundárias\s+independentes\s*\(\s*"
    r"|\blid[oa]s?\s+por\s+inteiro\s+em\s+fonte\s+primária\s*\(\s*"
    r"|\blid[oa]s?\s+directamente\s+a\s+"
    r"|\bverificad[oa]\s+via\s+pesquisa\b[^—–<>]{0,250}?[—–]\s*"
    r"|\bdata\s+de\s+verificação\s+desta\s+página\s*\(\s*)"
    r"(?:(\d{1,2})/(\d{1,2})/(\d{4})"
    r"|(\d{1,2})\s+(?:de\s+)?(" + _MESES_RE + r")\s+(?:de\s+)?(\d{4}))"
)
LIMITE_MESES_CARIMBO = 12  # carimbo com mais do que isto, face ao mês de execução → alerta

# Referência legal/histórica permanente — nunca "expira".
# "\bdesde\s+(?:\d|<mês>\s+de\s+\d)" exige um número logo a seguir, directamente
# ou depois de um nome de mês (ex.: "desde 2016/2017", "em vigor desde 1 de
# dezembro", "Desde junho de 2023" — issue #52, porta-65.html: sem o ramo do
# nome de mês, "desde junho de 2023" não batia certo com o marcador, que só
# reconhecia "desde <ano>" cru) — sem isto, apanhava também "desde que"
# (conjunção condicional, ex.: "tens direito desde que cumpras as condições"),
# que não tem nada a ver com uma data histórica e mascarava datas realmente
# antigas.
# Data fixada por lei, citada como facto legal permanente — isenta do portão
# de confirmação (issue #186). O portão expõe qualquer data posterior ao
# carimbo "Verificado a"; estas formulações dizem só o que a lei fixa
# (31/12/2026 do artigo 63.º/57.º do Decreto-Lei n.º 166/2026) e remetem a
# confirmação do pagamento para a Segurança Social — continuam verdade depois
# da data. Estreitas de propósito: as frases prospectivas do cluster PSU
# ("pagamento a partir de", "até 31/12/2026 mantém-se") NUNCA podem ser
# apanhadas aqui — têm de ficar expostas em 2027 (issue #293). Cada entrada
# também está em MARCADORES_HISTORICOS (contenção testada), por isso entra no
# baseline de tests/marcadores_historicos_baseline.json.
MARCADORES_ISENTOS_DO_PORTAO = [
    # "o artigo 63.º fixa 31 de dezembro de 2026 como (a) data de produção de efeitos"
    r"como\s+(?:a\s+)?data\s+de\s+produ[çc][ãa]o\s+de\s+efeitos",
    # "produção de efeitos a 31/12/2026 (art. 63.º)" — aviso/meta/tabela
    r"produ[çc][ãa]o\s+de\s+efeitos\s+a\s+31/12/2026\s+\(art(?:igo|\.)\s*63\.º\)",
    # ficha do diploma no bloco de fontes: "Produção de efeitos: 31/12/2026"
    r"produ[çc][ãa]o\s+de\s+efeitos:\s+31/12/2026",
    # conversão oficiosa do artigo 57.º descrita como evento único fixado por lei
    r"fixa-a\s+como\s+um\s+evento\s+[úu]nico|data\s+fixada\s+por\s+lei(?:\s+para|,\s+como\s+evento\s+[úu]nico)",
]

MARCADOR_DESDE = (
    r"\bdesde\s+(?:\d|(?:janeiro|fevereiro|março|abril|maio|junho|julho|"
    r"agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d)"
)

MARCADORES_HISTORICOS = [
    r"portaria", r"decreto-lei", r"decreto\s+lei", r"despacho", r"\bdl\s*n",
    r"lei\s+n\.?º", r"diário da república", r"dre\.pt", r"em vigor desde",
    MARCADOR_DESDE,
    # Elegibilidade fixa por data-limite de contrato — nunca muda com o tempo,
    # é a própria definição do critério (issue #51, apoio-extraordinario-renda.html:
    # "contrato ... posterior a 15 de março de 2023", "celebrados até 15 de
    # março de 2023"). "\b...a\b" (não "\bposterior at[ée]") para não apanhar
    # "posterior até" (ressarcimento posterior até X€, sem data-limite nenhuma).
    r"\bposterior a\b", r"celebrados?\s+at[ée]\b",
    # Mesma família de #51, formulação inversa encontrada ao tornar a
    # detecção recursiva (2026-07-07, p/habitacao.html: "contrato anterior
    # a 15 de março de 2023", "contratos de arrendamento anteriores a 15 de
    # março de 2023" — a data-limite fixa de elegibilidade do PAER, nunca
    # expira). "\b...\s+a\b" ancorado como "posterior a" — nunca apanha
    # "anterior" solto (ex.: "no ano anterior, março de..." não suprime).
    r"\banterior(?:es)?\s+a\b",
    # Citação datada de um facto histórico específico (queixa/pedido/anúncio já
    # ocorrido), não um valor ou prazo corrente (issue #51: "pediu ... uma
    # revisão urgente em agosto de 2025").
    r"revisão urgente",
    # Regra antiga descrita como já revogada, com a data-limite da mudança
    # (issue #53, baixa-medica-subsidio-doenca.html: "já não existe o limite
    # mínimo de 30 dias que existia antes de 1 de abril de 2024" — descreve
    # permanentemente um estado passado, nunca "expira"; a citação legal
    # "em vigor desde 1 de abril de 2024" mais abaixo na página está fora da
    # janela de 220 caracteres desta ocorrência específica, por isso precisa
    # do seu próprio marcador). "exist(?:e|ia|iam)" para não apanhar um
    # "antes de" genérico sem relação com uma regra revogada.
    r"exist(?:e|ia|iam)\s+antes\s+de\b",
    # Data de emissão de um documento, usada para delimitar uma geração/
    # modelo — facto técnico permanente, nunca "expira" (achado ao corrigir
    # renovar-cartao-cidadao.html, 2026-07-18: "cartões com MRZ mas sem chip
    # de contacto, emitidos até 10 de junho de 2024"). Cobre "emitido(s)
    # entre/até/a partir de" — confirmado sem colisão com nenhum outro match
    # real de data no resto do site antes de aplicar.
    r"\bemitidos?\s+(?:entre|at[ée]|a\s+partir\s+de)\b",
    # Citação de quando uma notícia circulou ou um esclarecimento oficial foi
    # emitido — evento de imprensa datado, permanentemente no passado, nunca
    # um prazo a rever (mesma família de "revisão urgente" acima; achado no
    # mesmo commit: "circularam notícias em dezembro de 2025", "esclarecimento
    # de 30/12/2025").
    r"circularam\s+not[íi]cias",
    r"esclarecimento\s+(?:oficial\s+)?de\s+\d",
    # Citação de uma informação vinculativa da AT (ficha doutrinária) e da
    # data em que foi divulgada — doutrina administrativa datada,
    # permanentemente no passado, nunca um prazo a rever (achado na Sessão 2
    # do cluster Habitação, 2026-07-20, imt-jovem.html: "informação
    # vinculativa divulgada em outubro de 2025" sobre a exclusão de terrenos
    # do IMT Jovem). Âncora estreita — a expressão só aparece em citações de
    # doutrina fiscal, nunca junto a um prazo corrente; confirmado por grep
    # sem colisão com nenhum outro match de data no site antes de aplicar.
    r"informa[çc][ãa]o\s+vinculativa",
    # Regra antiga revogada numa data concreta - facto histórico permanente,
    # mesma família de "exist(e|ia|iam) antes de" acima, formulação inversa
    # (issue #126, simulador-subsidio-desemprego.html, 2026-08-25: "a redução
    # de 10% aos 180 dias ... foi REVOGADA em janeiro de 2018"). O match nunca
    # tinha disparado antes: o texto estava desde a criação da página, mas
    # partido por uma quebra de linha de comentário JS ("janeiro\n    // de
    # 2018") - o prefixo "// " da linha de continuação quebrava o \s+ da
    # regex; a migração para YAML (2026-08-24) fez reflow do comentário para
    # uma única linha e expôs o match, já sem marcador de supressão. Nunca
    # apanha uma pergunta hipotética sobre revogação futura (ex.: "...quando
    # for revogado?", sem "foi"); confirmado por grep sem colisão com nenhum
    # outro match de data no site antes de aplicar.
    r"\bfoi\s+revogad[ao]\s+em\b",
    # Referência ao "período de transição" do Brexit (Acordo de Saída do
    # Reino Unido) — expressão fixa e específica de um evento histórico
    # único (terminou a 31/12/2020, nunca se repete), achado ao publicar
    # reforma-reino-unido-brexit.html (2026-09-06). Âncora estreita —
    # confirmado por grep que a única outra ocorrência no site
    # (psu-vs-abono-familia.html) não tem nenhuma data de mês+ano nas
    # proximidades, por isso não há risco de mascarar um prazo real.
    r"per[íi]odo\s+de\s+transi[çc][ãa]o",
    # Datas de fecho/inscrição da Caixa Geral de Aposentações — fronteiras
    # históricas fixas (1993, 2005/2006), nunca "expiram" porque a CGA está
    # fechada a novas inscrições desde 2006 (achado ao publicar
    # caixa-geral-aposentacoes.html, 2026-09-06). Confirmado por grep sem
    # colisão com nenhuma outra página do site (só fontes.html, mesmo tema).
    r"novas\s+inscri[çc][õo]es", r"\bse\s+inscreveu\b",
    r"\binscritos?\s+a\s+partir\s+de\b",
    # Citação de um Regulamento europeu pelo formato oficial "Regulamento
    # (CE/UE) n.º NNN/AAAA" — mesma família das citações de diploma
    # português já cobertas acima (portaria/decreto-lei/lei/despacho),
    # nunca coberta até agora porque o site nunca tinha citado um
    # regulamento europeu antes de carreiras-contributivas-estrangeiro.html
    # (2026-09-06). Note-se: "n\.?[ºo]" exige o "n.º"/"n.o" literal — o
    # Regulamento (UE) 2025/1208 citado em renovar-cartao-cidadao.html
    # nunca usa esse formato ("Regulamento (UE) 2025/1208", sem "n.º"),
    # por isso esta âncora não colide com essa página (confirmado por
    # grep antes de aplicar).
    r"regulamento\s*\((?:ce|ue)\)\s*n\.?[ºo]",
    # Cláusula de salvaguarda transitória com data-limite fixa (issue #170,
    # fontes.html, 2026-09-07): "a salvaguarda de 36 anos de serviço + 60 de
    # idade a 31 de dezembro de 2005 (art. 7.º)" — mesma família das
    # fronteiras da CGA já cobertas acima (1993/2006), mas o parágrafo do
    # card de fontes.html é longo o suficiente para o "Lei n.º 60/2005" do
    # H2 ficar fora da janela de 220 caracteres desta ocorrência específica
    # (em caixa-geral-aposentacoes.html o mesmo facto já ficava suprimido
    # pelos marcadores "lei\s+n\.?º"/"se inscreveu", por estar mais perto).
    #
    # Restrição (issue #172, revisão pós-merge, 2026-09-07): a versão
    # original desta entrada era a palavra solta `\bsalvaguarda\b` — a única
    # da lista sem nenhuma especificidade de frase, ao contrário de todas as
    # outras (ex.: "novas inscrições", "período de transição"). Este módulo
    # não tem nenhum mecanismo de restrição por ficheiro (`_esta_suprimido`
    # nunca recebe o nome da página — confirmado por leitura do código);
    # qualquer marcador aqui é sempre global, para qualquer HTML do site.
    # Por isso a supressão é feita pela ESPECIFICIDADE do padrão, mesmo
    # princípio de todas as entradas acima: exige a forma real da cláusula,
    # "salvaguarda [transitória] de <número>", em vez da palavra a solo.
    # Isto exclui deliberadamente o uso verbal de "salvaguarda" (ex.:
    # reforma-reino-unido-brexit.html, "o n.º 2 salvaguarda direitos
    # relativos a períodos anteriores" — sem "de" a seguir, nunca corresponde)
    # e qualquer menção genérica futura ("salvaguarda dos direitos do
    # utilizador", "salvaguarda de dados") que pudesse coincidir, por acaso,
    # com uma data de mês+ano genuinamente expirada na mesma janela de 220
    # caracteres — risco real da palavra solta, confirmado com um caso
    # sintético antes desta restrição. As 3 ocorrências reais no site
    # continuam cobertas: `fontes.html` ("salvaguarda de 36") e as duas
    # ocorrências equivalentes em `caixa-geral-aposentacoes.html` (essa
    # página já ficava suprimida de qualquer forma pelos marcadores
    # "lei\s+n\.?º"/"se inscreveu" mais próximos — confirmado sem regressão).
    r"\bsalvaguarda\s+(?:transit[óo]ria\s+)?de\s+\d",
    # Elegibilidade fixa por data de nascimento — "nascida/nascido/nasceu
    # a partir de <data>" (creche-gratuita.html: "poderá ter direito se
    # tiver nascido a partir de 1 de setembro de 2021" — condição de
    # acesso do artigo 5.º/2.º da Portaria n.º 305/2022, nunca "expira":
    # qualquer criança nascida nessa data ou depois continua elegível
    # para sempre). Mesma família de "posterior a"/"anterior(es) a" já
    # cobertas acima (data-limite fixa de elegibilidade do PAER), mas
    # aqui a direcção é inversa ("a partir de", não "até"/"anterior a") e
    # o sujeito é uma data de nascimento, não um contrato.
    #
    # Ancorado ao radical "nasc" (não a "\ba partir de\b" sozinho, de
    # propósito): "a partir de <data>" é uma preposição genérica, usada
    # em várias páginas do site para factos genuinamente sujeitos a
    # revisão quando a data passa — ex. "a PSU só é paga de facto a
    # partir de 31 de dezembro de 2026" (prestacao-social-unica.html,
    # como-pedir-psu.html), "esta redação vai mudar a partir de 31 de
    # dezembro de 2026" (majoracao-subsidio-desemprego.html). Suprimir
    # "a partir de" a solo mascararia essas datas depois de passarem,
    # quando é exactamente aí que precisam de ficar expostas para
    # revisão humana (mesmo risco já documentado para `\bsalvaguarda\b`
    # sozinha, issue #172). Confirmado por grep ao site inteiro antes de
    # aplicar: `nasc[a-zç]*\s+a\s+partir\s+de` só ocorre em
    # creche-gratuita.html.
    r"nasc\w*\s+a\s+partir\s+de\b",
] + MARCADORES_ISENTOS_DO_PORTAO

# Exemplo ilustrativo de cálculo — datas fixas usadas só para exemplificar o método.
MARCADORES_EXEMPLO = [r"exemplo", r"ilustrat", r"\bex\.\s*:"]

# Nota: não há marcadores separados para "ano de rendimentos" ou "comparação
# histórica" (ex.: "Em 2025, ..."). Essas frases nunca coincidem com nenhum
# padrão em PADROES (não têm nome de mês nem formato DD/MM/AAAA nem AAAA/AAAA
# junto ao ano), por isso nunca entram no ramo de "ano antigo" — não precisam
# de supressão porque nunca geram falso positivo. Confirmado por auditoria:
# adicionar esses marcadores como substring solta só introduzia risco de
# mascarar datas antigas genuinamente desactualizadas sem beneficiar nenhum
# caso real (ver histórico do commit).

# Conteúdo que já assume, de forma explícita, que está pendente de confirmação.
# "confirmar" no infinitivo (pendente) — não "confirmado" (já feito).
# Marcadores de diploma (issue #332): só suprimem a data que faz parte da
# própria citação — "Portaria n.º 305/2022, de 22 de dezembro de 2022".
# Uma data que só está perto de um diploma (carimbo, prazo, anúncio na
# mesma linha das fontes) deixa de ser suprimida por eles. Desde o PR B
# também `despacho`, `\bdl\s*n`, `diário da república` ("Diário da República
# n.º 45/2023, Série I, de …") e `dre.pt` — que não tem forma de citação com
# data, por isso nunca suprime uma data.
MARCADORES_SO_CITACAO = (
    r"portaria", r"decreto-lei", r"decreto\s+lei", r"lei\s+n\.?º",
    r"despacho", r"\bdl\s*n", r"diário da república", r"dre\.pt",
)
# Datas: só a data da citação. Ano lectivo (PR D do #332): só o par que é o
# próprio número do diploma ("Despacho n.º 2026/2027", forma que o site hoje
# não usa) — um ano lectivo perto de um diploma, mesmo na ementa da citação
# ("— calendário escolar 2024/2025 a 2027/2028"), deixa de ser suprimido por
# eles. O valor do IAS continua por proximidade. O compromisso no futuro
# também fica como estava: a correspondência começa no verbo, não na data,
# e uma frase "vai mudar a 1 de janeiro…" não é citação.
TIPOS_DATA_CITACAO = ("data_mes_ano", "data_numerica", "prazo_outono")
TIPOS_NUMERO_CITACAO = ("ano_letivo",)
assert set(MARCADORES_SO_CITACAO) <= set(MARCADORES_HISTORICOS)
REGEX_CITACAO_DIPLOMA = re.compile(
    r"(?:decreto-lei|decreto\s+lei|\blei|portaria|despacho|\bdl"
    r"|di[áa]rio\s+da\s+rep[úu]blica)\s*n\.?\s*[ºo°]\s*[\w\-/\.]+"
    r"(?:,?\s*(?:s[ée]rie\s+[ivx]+|\d\.ª\s+s[ée]rie))?"
    r",?\s+de\s+(?:\d{1,2}\s+de\s+)?$",
    re.IGNORECASE,
)
# Texto logo antes de um ano lectivo que é o número do diploma citado.
REGEX_NUMERO_DIPLOMA = re.compile(
    r"(?:decreto-lei|decreto\s+lei|\blei|portaria|despacho|\bdl"
    r"|di[áa]rio\s+da\s+rep[úu]blica)\s*n\.?\s*[ºo°]\s*[\w\-]*(?:/[\w\-]+)*/?$",
    re.IGNORECASE,
)

# Marcadores «desde» (issue #332, PR B; #335): só suprimem a data que regem —
# a que vem logo a seguir, só com o dia ou «de» pelo meio («em vigor desde 14
# de agosto de 2026», «desde 16/05/2026»). Uma data só perto de um «desde»
# (a produção de efeitos na mesma linha, um prazo) deixa de ser suprimida.
# Excepção: «desde 1 de janeiro de AAAA» nunca é suprimido por estes
# marcadores — no site é quase sempre a vigência de valores anuais; as datas
# de início de lei com 1 de janeiro estão em DATAS_PERMANENTES.
MARCADORES_DESDE = {MARCADOR_DESDE: r"\bdesde", r"em vigor desde": r"\bem\s+vigor\s+desde"}
_CAUDA_DESDE = r"\s+(?:o\s+dia\s+)?(?:(\d{1,2})(?:\.º)?\s+de\s+)?$"

# Marcadores de data-limite e de evento (PR D do #332): `celebrados até`,
# `posterior a`, `anterior(es) a` e `revisão urgente` só suprimem a data logo
# a seguir — «celebrados até 15 de março de 2023», «revisão urgente em agosto
# de 2025». Uma data só perto deles (outra frase, «anterior a essa data»)
# deixa de ser suprimida. No ano lectivo e no IAS continuam por proximidade.
MARCADORES_DATA_SEGUINTE = {
    r"celebrados?\s+at[ée]\b": r"\bcelebrados?\s+at[ée]",
    r"\bposterior a\b": r"\bposterior\s+a",
    r"\banterior(?:es)?\s+a\b": r"\banterior(?:es)?\s+a",
    r"revisão urgente": r"\brevis[ãa]o\s+urgente\s+em",
}
_CAUDA_DATA_SEGUINTE = r"\s+(?:o\s+dia\s+)?(?:\d{1,2}(?:\.º)?\s+de\s+)?$"
assert set(MARCADORES_DATA_SEGUINTE) <= set(MARCADORES_HISTORICOS)

# Marcadores isentos da produção de efeitos (PR B): só suprimem a própria data
# — dentro da expressão («Produção de efeitos: 31/12/2026») ou logo antes de
# «como (a) data de produção de efeitos». As outras datas da mesma linha
# (Publicado em DR, Aprovado em CM) deixam de ser suprimidas por eles.
ISENTOS_DATA_PROPRIA = tuple(mk for mk in MARCADORES_ISENTOS_DO_PORTAO if "efeitos" in mk)


def _texto_antes(conteudo, inicio, n=200):
    antes = re.sub(r"<[^>]+>", " ", conteudo[max(0, inicio - n):inicio])
    return re.sub(r"\s+", " ", _html.unescape(antes))


def _rege_por_desde(marcador, conteudo, inicio):
    """O «desde» deste marcador vem logo antes da data, e a data não é 1 de janeiro?"""
    m = re.search(MARCADORES_DESDE[marcador] + _CAUDA_DESDE, _texto_antes(conteudo, inicio), re.IGNORECASE)
    if not m:
        return False
    data = conteudo[inicio:inicio + 20]
    num = re.match(r"(\d{1,2})/(\d{1,2})/", data)
    if num:
        return not (int(num.group(1)) == 1 and int(num.group(2)) == 1)
    return not (m.group(1) is not None and int(m.group(1)) == 1 and data.lower().startswith("janeiro"))


def _rege_logo_a_seguir(marcador, conteudo, inicio):
    """O marcador vem logo antes da data, só com o dia ou «de» pelo meio?"""
    padrao = MARCADORES_DATA_SEGUINTE[marcador] + _CAUDA_DATA_SEGUINTE
    return re.search(padrao, _texto_antes(conteudo, inicio), re.IGNORECASE) is not None


def _data_propria_do_isento(marcador, conteudo, inicio, fim):
    a0 = max(0, inicio - JANELA)
    for m in re.finditer(marcador, conteudo[a0:fim + JANELA], re.IGNORECASE):
        a, b = a0 + m.start(), a0 + m.end()
        if a <= inicio and fim <= b:
            return True
        if marcador.startswith("como") and fim <= a and not _texto_antes(conteudo, a, a - fim).strip():
            return True
    return False


def _citacao_de_diploma(conteudo, inicio):
    """Se a data que começa em `inicio` é a data de uma citação
    "<diploma> n.º X/AAAA, de …", devolve o texto dessa citação; senão None.
    Olha só para o texto imediatamente antes da data."""
    m = REGEX_CITACAO_DIPLOMA.search(_texto_antes(conteudo, inicio))
    return m.group(0) if m else None


def marcador_historico_aplica(marcador, janela, conteudo, inicio, tipo=None, fim=None):
    """Um marcador de MARCADORES_HISTORICOS suprime esta ocorrência?
    Única regra, partilhada por `_esta_suprimido` e pelo auditor. Em datas,
    um marcador de diploma só conta se a data for a da citação desse mesmo
    diploma ("lei n.º" nunca suprime a data de uma Portaria) e num ano
    lectivo só se o par for o número desse diploma; um «desde», um
    «celebrados até», «posterior/anterior a» ou «revisão urgente» só a data
    que rege e um isento da produção de efeitos só a própria data."""
    if not re.search(marcador, janela, re.IGNORECASE):
        return False
    if tipo in TIPOS_NUMERO_CITACAO and marcador in MARCADORES_SO_CITACAO:
        numero = REGEX_NUMERO_DIPLOMA.search(_texto_antes(conteudo, inicio, 80))
        return numero is not None and re.search(marcador, numero.group(0), re.IGNORECASE) is not None
    if tipo not in TIPOS_DATA_CITACAO:
        return True
    if marcador in MARCADORES_DESDE:
        return _rege_por_desde(marcador, conteudo, inicio)
    if marcador in MARCADORES_DATA_SEGUINTE:
        return _rege_logo_a_seguir(marcador, conteudo, inicio)
    if marcador in ISENTOS_DATA_PROPRIA:
        return _data_propria_do_isento(marcador, conteudo, inicio, fim if fim is not None else inicio)
    if marcador in MARCADORES_SO_CITACAO:
        citacao = _citacao_de_diploma(conteudo, inicio)
        return citacao is not None and re.search(marcador, citacao, re.IGNORECASE) is not None
    return True


# Datas que são facto permanente de UMA página (issue #332): (página, data
# exactamente como aparece no texto) → motivo, numa linha. Cada ocorrência
# dessa data nessa página fica suprimida, sejam quais forem os marcadores ou
# o HTML à volta; a mesma data noutra página nunca. Uma data que é facto
# permanente de uma página entra aqui, não num marcador global. Entrada órfã
# (a data já não está na página) faz falhar tests/test_datas_permanentes.py.
DATAS_PERMANENTES: dict[tuple[str, str], str] = {
    ("creche-gratuita.html", "1 de setembro de 2021"):
        "Data de nascimento a partir da qual há direito à creche gratuita (Portaria n.º 305/2022, art. 5.º, n.º 1, al. a)) — condição fixa.",
    ("fontes.html", "1 de setembro de 2021"):
        "Data de referência da creche gratuita citada no cartão da Portaria n.º 158/2024/1 — condição fixa.",
    ("fontes.html", "11 de dezembro de 2023"):
        "Data da consolidação do DRE contra a qual o texto foi verificado — facto fixo; a actualidade da versão é tema da revisão da página.",
    ("fontes.html", "20 de novembro de 2023"):
        "Data da versão consolidada do DRE contra a qual o texto foi verificado — facto fixo; a actualidade da versão é tema da revisão da página.",
    ("fontes.html", "31 de janeiro de 2013"):
        "Fim da norma transitória do subsídio por morte introduzida pelo DL 13/2013 — facto passado.",
    ("caixa-geral-aposentacoes.html", "1 de setembro de 1993"):
        "Fronteira da fórmula de cálculo da pensão CGA (Lei n.º 60/2005, art. 5.º) — data fixa.",
    ("caixa-geral-aposentacoes.html", "31 de agosto de 1993"):
        "Último dia antes da fronteira de 1/9/1993 (Lei n.º 60/2005, arts. 5.º e 6.º) — data fixa.",
    ("caixa-geral-aposentacoes.html", "1 de janeiro de 2006"):
        "Fecho da CGA a novas inscrições (Lei n.º 60/2005, arts. 2.º e 9.º) — data fixa.",
    ("caixa-geral-aposentacoes.html", "31 de dezembro de 2005"):
        "Data de corte da salvaguarda e da parcela P1 (Lei n.º 60/2005, arts. 5.º e 7.º) — data fixa.",
    # «desde 1 de janeiro de AAAA» que é início de lei, não vigência de valores
    # anuais — a restrição do «desde» nunca o suprime (PR B do #332).
    ("caixa-geral-aposentacoes.html", "1 de janeiro de 2015"):
        "Desde quando a idade de acesso da CGA é a do regime geral (Lei n.º 60/2005, art. 3.º e Anexo I) — data fixa.",
    ("cuidador-informal.html", "1 de janeiro de 2026"):
        "Início de efeitos do Decreto-Lei n.º 138/2025 (subsídio deixa de contar para o abono) — data fixa.",
    ("cuidador-informal.html", "1/1/2026"):
        "Início de efeitos do Decreto-Lei n.º 138/2025 — data fixa.",
    ("cuidador-informal.html", "01/01/2026"):
        "Início de efeitos do Decreto-Lei n.º 138/2025 — data fixa.",
    ("majoracao-subsidio-desemprego.html", "1 de janeiro de 2022"):
        "Entrada em vigor da majoração (art. 28.º-A do DL 220/2006, aditado pelo DL 119/2021) — data fixa.",
    ("fontes.html", "1 de janeiro de 2022"):
        "Entrada em vigor da majoração de 10% (DL 119/2021) — data fixa.",
    ("fontes.html", "1 de janeiro de 2023"):
        "Início de efeitos do Decreto-Lei n.º 18/2023 — data fixa.",
    ("fontes.html", "1 de janeiro de 2006"):
        "Fecho da CGA a novas inscrições e início da parcela P2 (Lei n.º 60/2005) — data fixa.",
    # Datas históricas que só estavam suprimidas por um «desde» ou um «Diário
    # da República» por perto (aprovadas pelo Nuno, PR B do #332).
    ("fontes.html", "31 de agosto de 1993"):
        "Fronteira fixa da Lei n.º 60/2005.",
    ("fontes.html", "10 de março de 2023"):
        "Data da versão consolidada lida; actualidade é tema da revisão de conteúdo.",
    ("subsidio-por-morte.html", "julho de 2012"):
        "Limite de um regime passado.",
    ("subsidio-por-morte.html", "janeiro de 2013"):
        "Limite de um regime passado.",
    # Publicação e aprovação do DL 166/2026 (aprovado pelo Nuno, PR B do #332).
    ("calendario-pagamentos-psu.html", "13/08/2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("como-pedir-psu.html", "13/08/2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("prestacao-social-unica.html", "13/08/2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("psu-quando-entra-em-vigor.html", "13/08/2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("psu-quem-tem-direito.html", "13/08/2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("prestacao-social-unica.html", "13 de agosto de 2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("psu-lista-13-apoios.html", "13 de agosto de 2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("psu-quando-entra-em-vigor.html", "13 de agosto de 2026"):
        "Publicação do Decreto-Lei n.º 166/2026 em Diário da República — facto fixo.",
    ("calendario-escolar-apoios.html", "2024/2025"):
        "Início fixo do calendário escolar plurianual 2024/2025 a 2027/2028 (Despacho n.º 8368/2024) — facto fixo; o 2027/2028 fica exposto.",
    ("prestacao-social-unica.html", "30/07/2026"):
        "Aprovação do Decreto-Lei n.º 166/2026 em Conselho de Ministros — facto fixo.",
    ("psu-quando-entra-em-vigor.html", "30/07/2026"):
        "Aprovação do Decreto-Lei n.º 166/2026 em Conselho de Ministros — facto fixo.",
}


def spans_datas_permanentes(conteudo, pagina):
    """(início, fim) de cada ocorrência de uma data de DATAS_PERMANENTES
    desta página."""
    return [
        (m.start(), m.end())
        for (p, data) in DATAS_PERMANENTES if p == pagina
        for m in re.finditer(re.escape(data), conteudo)
    ]


def em_data_permanente(spans, inicio, fim):
    return any(a <= inicio and fim <= b for a, b in spans)


MARCADORES_PENDENTE = [
    r"aguarda", r"previst", r"provis[oó]ri", r"\bconfirmar\b", r"estimad",
    r"deverá ser", r"após publicação",
]

PADROES = [
    {
        "regex": REGEX_MES_ANO,
        "tipo": "data_mes_ano",
        "descricao": "Data com mês e ano",
        "ano_grupo": 2,
    },
    {
        "regex": r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        "tipo": "data_numerica",
        "descricao": "Data numérica",
        "ano_grupo": 3,
    },
    {
        "regex": r"\b(IAS|indexante)\s+de\s+[\d,\.]+\s*[€e]",
        "tipo": "valor_ias",
        "descricao": "Valor do IAS",
        "ano_grupo": None,
    },
    {
        "regex": r"\b(20\d{2})/(20\d{2})\b",
        "tipo": "ano_letivo",
        "descricao": "Ano letivo",
        "ano_grupo": None,
    },
    {
        "regex": r"\b(\d{1,2})\s+de\s+(setembro|outubro|novembro|dezembro)\s+(?:de\s+)?(\d{4})\b",
        "tipo": "prazo_outono",
        "descricao": "Prazo de outono",
        "ano_grupo": 3,
    },
]

# Meses em que cada tipo de padrão deve ser revisto
REVER_EM = {
    "data_mes_ano": [1, 7, 8, 9],
    "data_numerica": [1, 7, 8, 9],
    "valor_ias": [1, 2],
    "ano_letivo": [6, 7],
    "prazo_outono": [8, 9],
}


# Compromisso no futuro com data (2026-10-06): "as candidaturas abrem em
# setembro de 2026" ficou na bolsa-de-merito.html depois de setembro, porque os
# PADROES só dão alerta a anos anteriores ao corrente e "data_mes_ano" só é
# revisto em jan/jul/ago/set. Aqui a comparação é ao mês, todos os meses: um
# verbo no presente/futuro seguido de uma data cujo mês já passou é uma frase
# desactualizada. Só formas de presente/futuro (nunca o pretérito —
# "terminaram", "comecei" são factos passados) e nunca com "desde" entre o
# verbo e a data (a data é então o início de outra coisa — caso real:
# psu-trabalho-social.html, "começa a ser paga — ... em vigor desde 28 de
# agosto de 2026"). Medido sobre as páginas reais antes de ligar: 9
# ocorrências, todas frases prospectivas da PSU/Garantia Pública que expiram
# a 31/12/2026 — zero falsos positivos.
_VERBOS_FUTURO = (
    r"abre|abrem|abrir[áã]o|abrirá"
    r"|come[çc]a|come[çc]am|come[çc]ar[áã]o|começará"
    r"|arranca|arrancam|arrancar[áã]o|arrancará"
    r"|decorre|decorrem|decorrer[áã]o|decorrerá"
    r"|termina|terminam|terminar[áã]o|terminará"
    r"|entra|entram|entrar[áã]o|entrará"
    r"|ser[áã]o?|vai\s+\w+|v[ãa]o\s+\w+|ir[áã]o?\s+\w+"
)
REGEX_COMPROMISSO_FUTURO = (
    r"\b(?:" + _VERBOS_FUTURO + r")\b"
    r"(?:(?!\bdesde\b)[^.!?<>\n]){0,60}?"
    r"(?:(?:(\d{1,2})\s+de\s+)?(janeiro|fevereiro|março|abril|maio|junho|julho|"
    r"agosto|setembro|outubro|novembro|dezembro)\s+(?:de\s+)?(\d{4})"
    r"|(\d{1,2})/(\d{1,2})/(\d{4}))"
)
PADRAO_COMPROMISSO_FUTURO = {
    "regex": REGEX_COMPROMISSO_FUTURO,
    "tipo": "compromisso_futuro",
    "descricao": "Compromisso no futuro com data já passada",
}


def _data_do_compromisso(m):
    try:
        if m.group(3):
            return date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1) or 1))
        return date(int(m.group(6)), int(m.group(5)), int(m.group(4)))
    except ValueError:
        return None


def _compromisso_futuro_expirado(conteudo, ano, mes, verificado_em=None, pagina=None):
    permanentes = spans_datas_permanentes(conteudo, pagina)
    for m in re.finditer(REGEX_COMPROMISSO_FUTURO, conteudo, re.IGNORECASE):
        d = _data_do_compromisso(m)
        if d is None or (d.year, d.month) >= (ano, mes):
            continue  # mês ainda não passou
        grupo_data = 1 if m.group(1) else (2 if m.group(3) else 4)
        if em_data_permanente(permanentes, m.start(grupo_data), m.end()):
            continue
        if _esta_suprimido(conteudo, m.start(), m.end(), ano, mes,
                           data_ocorrencia=d, verificado_em=verificado_em):
            continue
        return True
    return False


def _janela_contexto(conteudo, inicio, fim):
    return conteudo[max(0, inicio - JANELA):fim + JANELA]


def _tem_algum(padroes, texto):
    return any(re.search(p, texto, re.IGNORECASE) for p in padroes)


def _proxima_data_esperada(texto):
    """Devolve a data mais distante referida no texto (ex.: 'setembro de 2026')."""
    melhor = None
    for m in re.finditer(REGEX_MES_ANO, texto, re.IGNORECASE):
        candidato = datetime(int(m.group(2)), MESES[m.group(1).lower()], 1)
        if melhor is None or candidato > melhor:
            melhor = candidato
    return melhor


def _data_da_ocorrencia(padrao, m):
    """Data (aproximada ao dia 1 quando o padrão não captura o dia) da
    própria correspondência em avaliação — usada pelo portão de
    confirmação de `_esta_suprimido()` (issue #183, passo 2) para a
    comparar contra o carimbo "Verificado a" da página. Só definida para
    os 3 tipos com data própria sem ambiguidade; devolve None para
    qualquer outro (o portão fica então um no-op, comportamento
    inalterado)."""
    tipo = padrao["tipo"]
    try:
        if tipo == "data_mes_ano":
            return date(int(m.group(2)), MESES[m.group(1).lower()], 1)
        if tipo == "data_numerica":
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if tipo == "prazo_outono":
            return date(int(m.group(3)), MESES[m.group(2).lower()], int(m.group(1)))
    except ValueError:
        return None
    return None


def _dentro_de_link(conteudo, inicio):
    """Um token de data dentro do texto visível de um <a> é uma citação a outra
    página/recurso (ex.: link para outro artigo pelo seu próprio nome), não uma
    afirmação desta página sobre o seu próprio conteúdo."""
    antes = conteudo[max(0, inicio - JANELA_LINK):inicio]
    ultima_abertura = antes.rfind("<a ")
    ultimo_fecho = antes.rfind("</a>")
    return ultima_abertura != -1 and ultima_abertura > ultimo_fecho


def _esta_suprimido(conteudo, inicio, fim, ano, mes, data_ocorrencia=None, verificado_em=None, tipo=None):
    if _dentro_de_link(conteudo, inicio):
        return True

    janela = _janela_contexto(conteudo, inicio, fim)

    if _tem_algum(MARCADORES_EXEMPLO, janela):
        return True  # data hipotética de exemplo — nunca passa pelo portão

    if any(marcador_historico_aplica(mk, janela, conteudo, inicio, tipo, fim) for mk in MARCADORES_ISENTOS_DO_PORTAO):
        return True  # data fixada por lei, citada como facto permanente (#186)

    if any(marcador_historico_aplica(mk, janela, conteudo, inicio, tipo, fim) for mk in MARCADORES_HISTORICOS):
        if data_ocorrencia is not None and verificado_em is not None and data_ocorrencia > verificado_em:
            # Compromisso ainda por cumprir à data da última verificação desta
            # página — um marcador histórico (ex.: `celebrados? at[ée]`) pode
            # descrever tanto um limite já fechado para sempre (PAER) como um
            # prazo em vigor que a lei ainda pode prorrogar (Garantia Pública)
            # — a mesma frase serve os dois. Comporta-se então como
            # MARCADORES_PENDENTE: suprimido só até a data passar.
            return datetime(ano, mes, 1) < datetime(data_ocorrencia.year, data_ocorrencia.month, 1)
        return True  # comportamento anterior — permanente

    if _tem_algum(MARCADORES_PENDENTE, janela):
        data_esperada = _proxima_data_esperada(janela)
        # Sem data explícita, ou prazo anunciado ainda não decorrido: continua pendente.
        if data_esperada is None or data_esperada >= datetime(ano, mes, 1):
            return True
        return False  # o prazo anunciado já passou — deixa de estar coberto pelo aviso

    return False


def _carimbos(conteudo):
    """(início, fim, data) da parte de data de cada carimbo de verificação."""
    res = []
    for m in re.finditer(REGEX_CARIMBO, conteudo, re.IGNORECASE):
        try:
            if m.group(3):
                d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                ini = m.start(1)
            else:
                d = date(int(m.group(6)), MESES[m.group(5).lower()], int(m.group(4)))
                ini = m.start(4)
        except ValueError:
            continue
        res.append((ini, m.end(), d))
    return res


def _em_carimbo(carimbos, inicio, fim):
    return any(inicio < c_fim and c_ini < fim for c_ini, c_fim, _ in carimbos)


def _carimbo_antigo(conteudo, ano, mes):
    """Algum carimbo com mais de LIMITE_MESES_CARIMBO meses face a ano/mes?"""
    for _, _, d in _carimbos(conteudo):
        if (ano * 12 + mes) - (d.year * 12 + d.month) > LIMITE_MESES_CARIMBO:
            return True
    return False


PADRAO_CARIMBO = {
    "regex": REGEX_CARIMBO,
    "tipo": "carimbo_antigo",
    "descricao": f"Carimbo de verificação com mais de {LIMITE_MESES_CARIMBO} meses",
}


def _pagina_tem_alerta(conteudo, padrao, ano, mes, verificado_em=None, pagina=None):
    tipo = padrao["tipo"]

    if tipo == "ano_letivo":
        # Duas passagens: primeiro identifica que pares "antigos" já têm, em
        # ALGUM ponto da página, uma explicação válida (referência legal ou
        # aviso de pendência ainda dentro do prazo). Uma vez explicado, o
        # mesmo par repetido noutros pontos da página (ex.: um cabeçalho FAQ
        # e a respectiva resposta, ou uma citação em JSON-LD) não é
        # sinalizado em duplicado.
        #
        # Risco aceite: a propagação é à escala da página inteira, não só do
        # parágrafo. Cada HTML deste site cobre um único apoio/tema, por isso
        # o mesmo par de anos repetido na mesma página refere-se sempre ao
        # mesmo ciclo — mas se uma página alguma vez misturar dois assuntos
        # distintos que citem coincidentemente o mesmo par (ex.: "2025/2026"),
        # uma afirmação não relacionada e genuinamente desactualizada poderia
        # ficar mascarada pela explicação da outra. Ver auditoria.
        permanentes = spans_datas_permanentes(conteudo, pagina)
        ocorrencias = [m for m in re.finditer(padrao["regex"], conteudo)
                       if not em_data_permanente(permanentes, m.start(), m.end())]
        pares_explicados = {
            m.group(0) for m in ocorrencias
            if int(m.group(1)) < ano and _esta_suprimido(conteudo, m.start(), m.end(), ano, mes, tipo=tipo)
        }
        for m in ocorrencias:
            if int(m.group(1)) >= ano:
                continue  # par actual ou futuro
            if m.group(0) in pares_explicados:
                continue
            return True
        return False

    if tipo == "valor_ias":
        for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
            janela = _janela_contexto(conteudo, m.start(), m.end())
            anos_proximos = [int(a) for a in re.findall(r"\b(20\d{2})\b", janela)]
            if not any(a < ano for a in anos_proximos):
                continue  # nenhum ano antigo anotado junto ao valor
            if _esta_suprimido(conteudo, m.start(), m.end(), ano, mes):
                continue
            return True
        return False

    carimbos = _carimbos(conteudo)
    permanentes = spans_datas_permanentes(conteudo, pagina)
    for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
        ano_match = int(m.group(padrao["ano_grupo"]))
        if ano_match >= ano:
            continue  # data actual ou futura
        if _em_carimbo(carimbos, m.start(), m.end()):
            continue  # data de carimbo — regra própria (_carimbo_antigo)
        if em_data_permanente(permanentes, m.start(), m.end()):
            continue  # facto permanente desta página (DATAS_PERMANENTES)
        if _esta_suprimido(
            conteudo, m.start(), m.end(), ano, mes,
            data_ocorrencia=_data_da_ocorrencia(padrao, m),
            verificado_em=verificado_em,
            tipo=padrao["tipo"],
        ):
            continue
        return True
    return False


def _contexto_representativo(conteudo, padrao):
    """Localiza a primeira correspondência do padrão do alerta, para dar à
    camada de classificação (classificar_datas) um exemplo real do texto e
    da janela de contexto — sem repetir a procura de supressão já feita
    por `_pagina_tem_alerta`."""
    m = re.search(padrao["regex"], conteudo, re.IGNORECASE)
    if not m:
        return None, None
    return m.group(0), _janela_contexto(conteudo, m.start(), m.end())


def detectar_alertas(conteudo, nome_pagina, ano, mes):
    """Devolve o alerta (dict) para `nome_pagina`, ou None se nada de expirado for encontrado."""
    verificado_em = verificado_em_do_texto(conteudo)
    for padrao in PADROES + [PADRAO_COMPROMISSO_FUTURO, PADRAO_CARIMBO]:
        if padrao is PADRAO_COMPROMISSO_FUTURO:
            tem_alerta = _compromisso_futuro_expirado(conteudo, ano, mes, verificado_em, nome_pagina)
        elif padrao is PADRAO_CARIMBO:
            tem_alerta = _carimbo_antigo(conteudo, ano, mes)
        elif mes not in REVER_EM[padrao["tipo"]]:
            continue
        else:
            tem_alerta = _pagina_tem_alerta(conteudo, padrao, ano, mes, verificado_em=verificado_em,
                                            pagina=nome_pagina)
        if tem_alerta:
            alerta = {
                "pagina": nome_pagina,
                "tipo": padrao["tipo"],
                "titulo": f"📅 REVER: {nome_pagina} — {padrao['descricao']}",
                "corpo": (
                    f"A página `{nome_pagina}` contém datas ou valores que podem "
                    f"estar desactualizados para {ano}.\n\n"
                    f"**Tipo detectado:** {padrao['descricao']}\n"
                    f"**Mês actual:** {mes}/{ano}\n\n"
                    f"**Acção:** abrir a página, verificar cada data/valor com a "
                    f"fonte oficial e actualizar se necessário.\n\n"
                    f"Esta Issue foi gerada automaticamente pelo pipeline diário."
                ),
            }
            # Camada 2 (classificar_datas) + Camada 3 (decisao_datas):
            # metadado informativo, adicionado sem influenciar se o alerta
            # é gerado nem os campos que o pipeline usa para criar a Issue
            # (pagina/titulo/corpo). decidir_acao_estruturada não executa
            # nenhum efeito real — devolve só uma string de ação.
            data_bruta, contexto = _contexto_representativo(conteudo, padrao)
            if data_bruta is not None:
                classificacao = classificar_data_estruturada(
                    contexto, data_bruta, ano_atual=ano
                )
                alerta["classificacao"] = classificacao
                alerta["decisao"] = decidir_acao_estruturada(
                    classificacao["estado"], classificacao
                )
            return alerta
    return None


def main():
    hoje = datetime.now()
    ano, mes = hoje.year, hoje.month

    alertas = []
    # Raiz + pillars + minutas — até 2026-07-07 o glob era só "*.html"
    # (não recursivo), deixando p/ e documentos/ (17 páginas servidas)
    # totalmente fora da vigilância de datas expiradas. `nome` é o caminho
    # relativo (ex.: "p/habitacao.html") — para as páginas da raiz é
    # idêntico ao basename de sempre, nada muda nas Issues existentes.
    paginas = (sorted(glob.glob("*.html"))
               + sorted(glob.glob("p/*.html"))
               + sorted(glob.glob("documentos/*.html")))
    for html_path in paginas:
        nome = html_path.replace(os.sep, "/")
        if os.path.basename(html_path) in AUTO_GERADOS:
            continue
        try:
            with open(html_path, encoding="utf-8") as f:
                conteudo = f.read()
        except Exception as e:
            print(f"Erro ao ler {html_path}: {e}")
            continue

        alerta = detectar_alertas(conteudo, nome, ano, mes)
        if alerta:
            alertas.append(alerta)

    os.makedirs("data", exist_ok=True)
    with open("data/alertas_datas.json", "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    print(f"{len(alertas)} páginas com potencial desactualização detectadas")
    for a in alertas:
        print(f"  - {a['pagina']}: {a['tipo']}")


if __name__ == "__main__":
    main()
