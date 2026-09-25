"""
Prepara o rascunho diário do canal de WhatsApp — nunca publica.

Gatilhos, por ordem de prioridade (ver CLAUDE.md → "CANAL DE WHATSAPP —
GATILHO EDITORIAL DE PUBLICAÇÃO" → "Mecanismo"). O gatilho de "notícia
relevante" ficou deliberadamente por construir — medição real de agosto
de 2026 mostrou ~20 dias/mês com pelo menos uma vencedora do
gerar_noticias.py, dos quais só 2 tinham sinal legal directo no título
— e esses 2 já coincidiam com o gatilho 1. Ver ROADMAP.md → "À espera
de um sinal" → "Canal de WhatsApp" para o raciocínio completo antes de
o reabrir.

1a. ALTERAÇÃO LEGAL CONFIRMADA — data/canal_pendente.json
    (`{"_nota": "...", "entradas": [{"titulo", "resumo", "paginas": [...]}]}`)
    é uma fila preenchida à MÃO por uma sessão editorial, no mesmo
    commit em que corrige uma página por causa de um facto legal
    confirmado (nunca por refactor/limpeza/reorganização — mesma regra
    já documentada em CLAUDE.md). O campo `_nota` explica o mecanismo
    directamente no ficheiro (mesmo padrão de data/destaque_evento.json)
    e é preservado em todas as escritas deste script — nunca apagado
    numa reescrita automática. Este script NUNCA decide sozinho se algo
    é "uma alteração real" — só formata e entrega o que um humano já
    decidiu e escreveu. Produz um rascunho `confirmado: true`.

1b. ALTERAÇÃO LEGAL POR CONFIRMAR — caminho automático, sem fila
    manual: quando um dos 6 sentinelas dirigidos (`dre_psu`,
    `dre_psu_regulamentacao`, `dre_habitacao_paer`,
    `dre_habitacao_garantia`, `dre_habitacao_garantia_portaria`,
    `dre_ias` — ver `SENTINELAS_DIRIGIDOS`)
    escreve a sua chave de aviso em `data/scraped/avisos.log` no dia de
    hoje, este script prepara logo um rascunho — sem esperar que uma
    sessão editorial confirme e preencha 1a primeiro. Nunca confunde-se
    com 1a: o rascunho nasce `confirmado: false` e o texto nunca é
    pronto a copiar — é só o excerto bruto detectado em dre.pt, a
    aguardar verificação humana contra a fonte oficial antes de
    qualquer publicação (o próprio step de Issues do workflow escreve o
    aviso "NÃO PUBLICAR AINDA" no corpo, ver pipeline-diario.yml).
    Motivo de existir a par de 1a: os sentinelas já dispararam por
    ruído confirmado depois (Regulamento da Série II na Issue #114,
    falso positivo do próprio DL 166/2026 na Issue #132) — um rascunho
    "por confirmar" nunca deve ser tratado como pronto, mas também não
    faz sentido perder o sinal só porque ninguém preencheu 1a ainda.
    Deduplicado por OCORRÊNCIA, não por dia: se o mesmo sentinela
    continuar a devolver o mesmo excerto em dias seguintes (já
    aconteceu na prática, ver `SENTINELAS_DIRIGIDOS`/Issue #132), só o
    1.º dia produz rascunho — `data/canal_estado.json` guarda o último
    excerto já rascunhado por sentinela (`sentinelas_rascunhadas`) e só
    volta a disparar quando o excerto for genuinamente diferente (um
    acto novo, não o mesmo a persistir na pesquisa).

3. CALENDÁRIO DE PAGAMENTOS — UMA mensagem por mês, a partir do
   primeiro dia útil, com as datas do mês inteiro, geradas de
   data/calendario_pagamentos.json (fonte já verificada por
   scripts/atualizar_calendario.py / scripts/scraper_calendario.py).
   Produz sempre `confirmado: true` — é informação já verificada, sem
   julgamento humano por fazer.

4. AVISO DE PAGAMENTO NA VÉSPERA (2026-09-25) — para cada dia de
   pagamento de data/calendario_pagamentos.json, um rascunho no dia
   útil ANTERIOR (o pipeline arranca perto do meio-dia UTC; no próprio
   dia chegaria tarde). Várias prestações no mesmo dia = uma só
   mensagem. A descrição de cada prestação é a 1.ª frase de texto que
   já existe no site (resposta rápida, ou a resposta directa do topo
   da página) — nunca escrita aqui. Prestação sem página no site
   (`VISTA_PRESTACOES` de atualizar_calendario.py sem URL) fica só com
   o nome, e a mensagem termina sempre com o link do calendário.
   Estado em data/canal_estado.json (`avisos_pagamento_entregues`, datas
   de pagamento já avisadas) — nunca repete o mesmo dia. Nunca é
   adiado por colisão: um aviso de pagamento no dia seguinte já não
   serve para nada, por isso vai SEMPRE, na mesma Issue que o rascunho
   do gatilho 1/3 desse dia, em bloco separado.

(Numeração alinhada com CLAUDE.md → "Publica-se quando"; o gatilho 2
desse texto — página corrigida por facto legal — entra aqui pela
mesma fila manual de 1a.)

"Dia útil" = segunda a sexta, excepto os feriados obrigatórios do
artigo 234.º do Código do Trabalho (`feriados_nacionais()`). Os
feriados municipais e a Terça-feira de Carnaval (facultativos) não
contam — a Segurança Social paga a nível nacional.

Regra de volume: no máximo 1 rascunho/dia dos gatilhos 1 e 3, mais o
aviso de pagamento (4) quando houver. Prioridade fixa entre 1 e 3:
1a (fila manual, já confirmada) > 1b (sentinela, por confirmar) > 3
(calendário). Se mais do que um tiver algo pendente no mesmo dia, os de
prioridade mais baixa ficam em espera — nunca são descartados
(`calendario_devido()` continua a devolver o mês enquanto não for
entregue; um sentinela por confirmar continua a re-detectar o mesmo
excerto todos os dias até ser rascunhado), por isso a corrida seguinte
sem nada de prioridade mais alta entrega-os.

Saída: escreve /tmp/canal_rascunho_hoje.json (efémero, fora do
repositório, nunca commitado) para o step de Issues do workflow
consumir — `{"data", "titulo", "confirmado", "blocos": [...]}`, um
bloco por rascunho (o step cria UMA Issue com todos os blocos). Os
campos do 1.º bloco são repetidos no topo por compatibilidade. Sem nada
a publicar hoje, não escreve nada — silêncio é o
comportamento correcto (mesma regra de honestidade já aplicada ao
resto do site, ver CLAUDE.md → "FRESCURA DA HOMEPAGE").

Risco residual documentado, aceite por desenho: se o passo de criação
da Issue falhar por um motivo transitório DEPOIS deste script já ter
consumido a entrada da fila / marcado o mês como entregue, essa
mensagem específica fica por publicar sem retry automático (o estado já
foi commitado). Dado tratar-se de uma ferramenta de sugestão, não de um
sistema crítico, este risco foi considerado aceitável em vez de
construir semântica "exactamente uma vez" à volta de uma chamada de API
que falha raramente — nunca escondido, registado aqui e em CLAUDE.md.

Uso (corrido pelo pipeline-diario.yml, sempre antes do push diário):
    python3 scripts/preparar_canal.py
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
from pathlib import Path
from typing import Optional

RAIZ_MODULO = Path(__file__).resolve().parent.parent
SAIDA_OMISSAO = Path("/tmp/canal_rascunho_hoje.json")

DOMINIO = "https://tensdireito.com"

sys.path.insert(0, str(RAIZ_MODULO / "scripts"))
from atualizar_calendario import MESES_PT, PRESTACOES, VISTA_PRESTACOES  # noqa: E402

# Os 6 sentinelas dirigidos que já geram Issue própria em
# pipeline-diario.yml (labels "verificar"/"fonte-alterada") — mesma
# chave de aviso escrita em data/scraped/avisos.log por
# scripts/scraper_playwright.py (`_registar_aviso`, chamada com
# `chave_aviso` a partir de `_detectar_decreto_psu`/
# `_detectar_decreto_lei_generico`/`_detectar_portaria_generico`).
# Ordem = a mesma dos blocos de Issue no workflow; só usada para
# desempate determinístico se mais do que um disparar no mesmo dia
# (nunca aleatório — nunca dois rascunhos no mesmo dia de qualquer
# forma, ver regra de volume acima).
SENTINELAS_DIRIGIDOS = {
    "dre_psu_decreto_detectado": "Decreto-Lei sobre a Prestação Social Única (PSU)",
    "dre_habitacao_paer_decreto_detectado": (
        "Decreto-Lei sobre o Apoio Extraordinário à Renda (PAER)"
    ),
    "dre_habitacao_garantia_decreto_detectado": (
        "Decreto-Lei que cita a Garantia Pública no crédito habitação"
    ),
    "dre_ias_portaria_detectada": "Portaria do Indexante dos Apoios Sociais (IAS)",
    "dre_psu_regulamentacao_portaria_detectada": (
        "Portaria que regulamenta o Decreto-Lei da PSU"
    ),
    "dre_habitacao_garantia_portaria_detectada": (
        "Portaria que altera o protocolo da Garantia Pública no crédito habitação"
    ),
}


def _carregar_json(caminho: Path, omissao):
    if not caminho.exists():
        return omissao
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"AVISO: {caminho} inválido ({e}) — a tratar como vazio")
        return omissao
    return conteudo


def _guardar_json(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _carregar_fila_pendente(caminho: Path) -> dict:
    """
    Devolve o documento inteiro de data/canal_pendente.json — nunca só a
    lista de entradas. `{"_nota": "...", "entradas": [...]}`, mesmo
    padrão de data/destaque_evento.json (nota explicativa como campo
    normal do JSON, para nunca desaparecer numa reescrita automática —
    lição real de 12 dias de instruções não lidas nesse ficheiro).
    Uma forma inesperada (lista solta antiga, chave em falta) é tratada
    como vazia, com aviso, nunca um crash.
    """
    dados = _carregar_json(caminho, {"entradas": []})
    if not isinstance(dados, dict) or not isinstance(dados.get("entradas"), list):
        print(
            f"AVISO: {caminho} não tem a forma esperada "
            '({"_nota": ..., "entradas": [...]}) — a tratar como vazio'
        )
        return {"entradas": []}
    return dados


def obter_pendente_legal(fila: list) -> tuple[dict | None, list]:
    """
    Devolve (entrada, fila_restante). A entrada é a mais antiga da fila
    com um `resumo` não vazio — entradas malformadas antes dela são
    descartadas com aviso (nunca bloqueiam a fila para sempre), nunca
    silenciosamente.
    """
    restante = list(fila)
    while restante:
        candidata = restante.pop(0)
        if not isinstance(candidata, dict) or not str(candidata.get("resumo", "")).strip():
            print(f"AVISO: entrada malformada em canal_pendente.json descartada: {candidata!r}")
            continue
        return candidata, restante
    return None, restante


def avisos_de_hoje(caminho_avisos_log: Path, hoje_iso: str) -> list[str]:
    """
    Linhas de data/scraped/avisos.log datadas de hoje — mesmo filtro do
    step "Abrir Issues se mudanças detectadas" em pipeline-diario.yml
    (`avisos_txt.split('\\n').filter(l => l.startsWith(hoje))`),
    reproduzido aqui para nunca divergir. O ficheiro é cumulativo e
    nunca rotacionado — sem este filtro, uma linha de dias/semanas
    atrás reapareceria como "detectada hoje" para sempre (mesmo bug já
    corrigido nas Issues #55-#58 do MEGA).
    """
    if not caminho_avisos_log.exists():
        return []
    texto = caminho_avisos_log.read_text(encoding="utf-8")
    return [linha for linha in texto.split("\n") if linha.startswith(hoje_iso)]


def obter_deteccao_sentinela(
    avisos_hoje: list[str], ja_rascunhados: dict
) -> tuple[str, str] | None:
    """
    Devolve (chave_aviso, excerto) do primeiro sentinela dirigido com um
    sinal NOVO hoje entre os de `SENTINELAS_DIRIGIDOS` — "novo" quer
    dizer: o excerto detectado hoje é diferente do último excerto para o
    qual este script já preparou um rascunho para essa mesma chave
    (`ja_rascunhados`, vindo de data/canal_estado.json). `None` se
    nenhum sentinela tiver sinal novo hoje.

    Nunca dispara duas vezes para a mesma ocorrência — o mesmo
    decreto-lei/portaria a persistir nos resultados da pesquisa dia
    após dia (já aconteceu na prática: Issue #132, dre_psu a re-detectar
    o próprio DL 166/2026 vários dias seguidos antes de o corte de
    recência ser corrigido). `ja_rascunhados` só regista uma chave
    quando um rascunho foi de facto produzido para ela — se o sinal
    apareceu num dia em que outra origem de maior prioridade ocupou o
    único slot diário, fica por rascunhar e continua elegível no dia
    seguinte (nunca perdido silenciosamente).
    """
    for chave_aviso in SENTINELAS_DIRIGIDOS:
        linha = next((linha for linha in avisos_hoje if chave_aviso in linha), None)
        if linha is None:
            continue
        match = re.search(re.escape(chave_aviso) + r":(.*)$", linha)
        excerto = match.group(1).strip() if match else ""
        if not excerto:
            continue
        if ja_rascunhados.get(chave_aviso) == excerto:
            continue  # mesma ocorrência já rascunhada — nunca repetir
        return chave_aviso, excerto
    return None


def formatar_rascunho_sentinela(chave_aviso: str, excerto: str) -> str:
    nome = SENTINELAS_DIRIGIDOS.get(chave_aviso, chave_aviso)
    linhas = [
        f"[POR CONFIRMAR — {nome}]",
        f"Sinal detectado automaticamente em dre.pt: {excerto}",
        "Confirma o facto na fonte oficial e reescreve este texto em "
        "PT-PT simples antes de sequer pensar em publicar.",
    ]
    return "\n\n".join(linhas)


def calendario_devido(hoje: dt.date, estado: dict, dados_calendario: dict) -> dict | None:
    """
    Devolve os dados do mês corrente se o calendário mensal ainda não
    foi entregue este mês, hoje for dia útil (`e_dia_util`) e o mês corrente
    já estiver presente em data/calendario_pagamentos.json — nunca
    antes disso, para nunca inventar um mês que a fonte oficial ainda
    não confirmou (mesmo invariante de `atualizar_calendario.py`: um
    mês sem dados degrada para "consultar a fonte oficial", nunca uma
    tabela inventada).
    """
    mes_corrente = f"{hoje.year:04d}-{hoje.month:02d}"
    if estado.get("ultimo_calendario_publicado") == mes_corrente:
        return None
    if not e_dia_util(hoje):  # fim-de-semana ou feriado nacional
        return None
    for m in dados_calendario.get("meses", []):
        if m.get("ano") == hoje.year and m.get("mes") == hoje.month:
            return m
    return None


def formatar_rascunho_legal(entrada: dict) -> str:
    linhas = [str(entrada.get("resumo", "")).strip()]
    paginas = entrada.get("paginas") or []
    if paginas:
        links = " · ".join(f"{DOMINIO}/{p}" for p in paginas)
        linhas.append(links)
    return "\n\n".join(linha for linha in linhas if linha)


def formatar_rascunho_calendario(mes_dados: dict) -> str:
    nome_mes = MESES_PT[mes_dados["mes"]]
    linhas = [
        f"📅 Calendário de pagamentos da Segurança Social — {nome_mes} de {mes_dados['ano']}",
        "",
    ]
    for p in sorted(mes_dados.get("pagamentos", []), key=lambda x: x.get("dia", 0)):
        nomes = " + ".join(PRESTACOES.get(s, s) for s in p.get("prestacoes", []))
        linhas.append(f"• dia {p.get('dia')}: {nomes}")
    linhas.append("")
    linhas.append(
        f"Calendário completo: {DOMINIO}/calendario-pagamentos-seguranca-social.html"
    )
    return "\n".join(linhas)


# ── Aviso de pagamento na véspera (gatilho 4) ───────────────────────────

URL_CALENDARIO = f"{DOMINIO}/calendario-pagamentos-seguranca-social.html"
DIAS_SEMANA_PT = [
    "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
    "Sexta-feira", "Sábado", "Domingo",
]
# Datas de pagamento já avisadas mais antigas do que isto saem do estado
# — nunca voltam a ser elegíveis de qualquer forma (já passaram).
RETENCAO_AVISOS_DIAS = 60


def _domingo_de_pascoa(ano: int) -> dt.date:
    # Algoritmo anónimo gregoriano (Meeus/Jones/Butcher).
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ll = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ll) // 451
    mes, dia = divmod(h + ll - 7 * m + 114, 31)
    return dt.date(ano, mes, dia + 1)


def feriados_nacionais(ano: int) -> set[dt.date]:
    """Feriados obrigatórios — artigo 234.º, n.º 1, do Código do Trabalho."""
    pascoa = _domingo_de_pascoa(ano)
    fixos = [(1, 1), (4, 25), (5, 1), (6, 10), (8, 15), (10, 5), (11, 1),
             (12, 1), (12, 8), (12, 25)]
    return {dt.date(ano, m, d) for m, d in fixos} | {
        pascoa - dt.timedelta(days=2),   # Sexta-Feira Santa
        pascoa,                          # Domingo de Páscoa
        pascoa + dt.timedelta(days=60),  # Corpo de Deus
    }


def e_dia_util(dia: dt.date) -> bool:
    return dia.weekday() < 5 and dia not in feriados_nacionais(dia.year)


def vespera_util(dia: dt.date) -> dt.date:
    """Último dia útil estritamente anterior a `dia`."""
    anterior = dia - dt.timedelta(days=1)
    while not e_dia_util(anterior):
        anterior -= dt.timedelta(days=1)
    return anterior


def pagamentos_por_data(dados_calendario: dict) -> dict[dt.date, list[str]]:
    """
    {data: [slugs]} — entradas do mesmo dia (métodos diferentes) fundidas
    numa só lista, pela ordem do JSON, sem repetidos.
    """
    por_data: dict[dt.date, list[str]] = {}
    for m in dados_calendario.get("meses", []):
        for p in m.get("pagamentos", []):
            try:
                data = dt.date(int(m["ano"]), int(m["mes"]), int(p["dia"]))
            except (KeyError, TypeError, ValueError):
                print(f"AVISO: pagamento malformado no calendário ignorado: {p!r}")
                continue
            lista = por_data.setdefault(data, [])
            for slug in p.get("prestacoes", []):
                if slug not in lista:
                    lista.append(slug)
    return por_data


def aviso_pagamento_devido(
    hoje: dt.date, estado: dict, dados_calendario: dict
) -> tuple[dt.date, list[str]] | None:
    """
    (data_pagamento, slugs) do pagamento mais próximo cuja véspera útil
    já chegou (`vespera_util(data) <= hoje < data`) e que ainda não foi
    avisado. `<=` e não `==`: se a corrida da véspera falhar, a de um
    dia seguinte ainda antes do pagamento (ex.: sábado, para segunda)
    recupera o aviso. No próprio dia do pagamento, nunca.
    """
    entregues = set(estado.get("avisos_pagamento_entregues", []))
    for data in sorted(pagamentos_por_data(dados_calendario)):
        slugs = pagamentos_por_data(dados_calendario)[data]
        if not (vespera_util(data) <= hoje < data):
            continue
        if data.isoformat() in entregues or not slugs:
            continue
        return data, slugs
    return None


_PRIMEIRA_FRASE = re.compile(r"^(.+?[.!?])(?=\s+[A-ZÁÉÍÓÚÂÊÔÃÕÀÇ]|\s*$)", re.S)


def _texto_limpo(fragmento_html: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragmento_html)).split())


def descricao_da_pagina(raiz: Path, url: str) -> str | None:
    """
    1.ª frase do texto de resumo que a página já publica — a resposta
    rápida (`.resposta-rapida-texto`) ou, sem ela, a resposta directa do
    topo (`.resposta-direta`). Nunca texto escrito aqui; sem página ou
    sem nenhum dos dois blocos, None.
    """
    caminho = raiz / url.lstrip("/")
    if not caminho.exists():
        print(f"AVISO: página {url} não encontrada — aviso de pagamento sem descrição")
        return None
    fonte = caminho.read_text(encoding="utf-8")
    bloco = re.search(r'<p class="resposta-rapida-texto">(.*?)</p>', fonte, re.S) or re.search(
        r'<div class="resposta-direta[^"]*">(.*?)</div>', fonte, re.S
    )
    if not bloco:
        return None
    texto = _texto_limpo(bloco.group(1))
    frase = _PRIMEIRA_FRASE.match(texto)
    return (frase.group(1) if frase else texto) or None


def paginas_da_prestacao(slug: str) -> list[tuple[str, str]]:
    """[(nome, url)] das páginas do site que cobrem a prestação."""
    return [(nome, url) for _a, nome, slugs, url in VISTA_PRESTACOES if slug in slugs and url]


def _quando(hoje: dt.date, data: dt.date) -> str:
    if (data - hoje).days == 1:
        return f"Amanhã (dia {data.day})"
    return f"{DIAS_SEMANA_PT[data.weekday()]} (dia {data.day})"


def formatar_aviso_pagamento(raiz: Path, hoje: dt.date, data: dt.date, slugs: list[str]) -> str:
    linhas = [f"{_quando(hoje, data)}, a Segurança Social paga:", ""]
    for slug in slugs:
        linhas.append(f"• {PRESTACOES.get(slug, slug)}")
        paginas = paginas_da_prestacao(slug)
        for nome, url in paginas:
            descricao = descricao_da_pagina(raiz, url)
            prefixo = f"{nome}: " if len(paginas) > 1 else ""
            if descricao:
                linhas.append(f"  {prefixo}{descricao}")
            elif prefixo:
                linhas.append(f"  {nome}:")
            linhas.append(f"  {DOMINIO}{url}")
    linhas += ["", f"Todas as datas de pagamento: {URL_CALENDARIO}"]
    return "\n".join(linhas)


def _escolher_principal(
    raiz: Path, hoje_data: dt.date, estado: dict
) -> dict | None:
    """
    Gatilhos 1a > 1b > 3 — no máximo um por dia. Actualiza `estado` em
    memória (o chamador persiste). Consome a fila manual em disco.
    """
    caminho_pendente = raiz / "data" / "canal_pendente.json"
    documento_pendente = _carregar_fila_pendente(caminho_pendente)
    fila = documento_pendente["entradas"]

    entrada, resto = obter_pendente_legal(fila)
    if resto != fila:
        # Só o campo "entradas" muda — "_nota" (e qualquer outra chave)
        # sobrevive intacta, nunca reescrita a partir do zero.
        documento_pendente["entradas"] = resto
        _guardar_json(caminho_pendente, documento_pendente)

    if entrada is not None:
        print("Rascunho preparado (alteração legal, confirmada)")
        return {
            "gatilho": "alteracao_legal",
            "origem": "fila_manual",
            "confirmado": True,
            "titulo": str(entrada.get("titulo") or "Alteração legal confirmada"),
            "texto": formatar_rascunho_legal(entrada),
        }

    avisos_hoje = avisos_de_hoje(raiz / "data" / "scraped" / "avisos.log", hoje_data.isoformat())
    ja_rascunhados = estado.get("sentinelas_rascunhadas", {})
    deteccao = obter_deteccao_sentinela(avisos_hoje, ja_rascunhados)
    if deteccao is not None:
        chave_aviso, excerto = deteccao
        estado["sentinelas_rascunhadas"] = {**ja_rascunhados, chave_aviso: excerto}
        print("Rascunho preparado (sentinela, por confirmar)")
        return {
            "gatilho": "alteracao_legal",
            "origem": "sentinela",
            "confirmado": False,
            "sentinela": chave_aviso,
            # Sem prefixo "Por confirmar —" aqui: o step de Issues do
            # workflow já antepõe "⚠️ Canal (por confirmar)" ao título
            # (confirmado === false) — duplicar aqui deixaria o título
            # da Issue com "por confirmar" repetido duas vezes.
            "titulo": SENTINELAS_DIRIGIDOS[chave_aviso],
            "texto": formatar_rascunho_sentinela(chave_aviso, excerto),
        }

    dados_calendario = _carregar_json(raiz / "data" / "calendario_pagamentos.json", {})
    mes_dados = calendario_devido(hoje_data, estado, dados_calendario)
    if mes_dados is not None:
        estado["ultimo_calendario_publicado"] = f"{hoje_data.year:04d}-{hoje_data.month:02d}"
        print(f"Rascunho preparado (calendário): {mes_dados['mes']}/{mes_dados['ano']}")
        return {
            "gatilho": "calendario",
            "origem": "calendario",
            "confirmado": True,
            "titulo": f"Calendário de pagamentos — {MESES_PT[mes_dados['mes']]} de {mes_dados['ano']}",
            "texto": formatar_rascunho_calendario(mes_dados),
        }
    return None


def _preparar_aviso_pagamento(raiz: Path, hoje_data: dt.date, estado: dict) -> dict | None:
    dados_calendario = _carregar_json(raiz / "data" / "calendario_pagamentos.json", {})
    devido = aviso_pagamento_devido(hoje_data, estado, dados_calendario)
    if devido is None:
        return None
    data, slugs = devido
    limite = (hoje_data - dt.timedelta(days=RETENCAO_AVISOS_DIAS)).isoformat()
    entregues = [d for d in estado.get("avisos_pagamento_entregues", []) if d >= limite]
    estado["avisos_pagamento_entregues"] = sorted(set(entregues) | {data.isoformat()})
    print(f"Aviso de pagamento preparado: {data.isoformat()} ({len(slugs)} prestações)")
    return {
        "gatilho": "pagamento",
        "origem": "calendario",
        "confirmado": True,
        "data_pagamento": data.isoformat(),
        "titulo": f"Pagamentos de {data.day} de {MESES_PT[data.month]}",
        "texto": formatar_aviso_pagamento(raiz, hoje_data, data, slugs),
    }


def main(
    *,
    raiz: Optional[Path] = None,
    hoje: Optional[str] = None,
    saida: Optional[Path] = None,
) -> Optional[dict]:
    """
    Devolve o rascunho preparado (ou None se não houver nada a publicar
    hoje) — o mesmo dicionário escrito em `saida`. `raiz`/`hoje`/`saida`
    são sempre opcionais (produção usa os valores reais); testes passam
    um `tmp_path` e uma data fixa, sem monkeypatch.
    """
    raiz = raiz or RAIZ_MODULO
    hoje_data = (
        dt.date.fromisoformat(hoje) if hoje else dt.datetime.now(dt.timezone.utc).date()
    )
    saida = saida or SAIDA_OMISSAO
    caminho_estado = raiz / "data" / "canal_estado.json"
    estado = _carregar_json(caminho_estado, {})

    blocos = [
        b for b in (
            _escolher_principal(raiz, hoje_data, estado),
            # Nunca adiado por colisão — um aviso de véspera no dia
            # seguinte já não serve para nada.
            _preparar_aviso_pagamento(raiz, hoje_data, estado),
        ) if b is not None
    ]
    if not blocos:
        print("Nada a publicar no canal hoje.")
        return None

    estado["ultima_entrega_canal"] = hoje_data.isoformat()
    _guardar_json(caminho_estado, estado)
    rascunho = {
        **blocos[0],
        "titulo": " + ".join(b["titulo"] for b in blocos),
        "confirmado": all(b["confirmado"] for b in blocos),
        "data": hoje_data.isoformat(),
        "blocos": blocos,
    }
    _guardar_json(saida, rascunho)
    return rascunho


if __name__ == "__main__":
    main()
