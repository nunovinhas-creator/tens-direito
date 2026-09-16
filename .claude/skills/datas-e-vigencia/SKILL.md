# Skill: datas-e-vigencia

O maquinismo de datas do repositório — o que existe para detectar e
suprimir datas expiradas, o que cada peça garante, e onde a cobertura
pára. Nunca decide se um facto está certo (`fact-check/SKILL.md`) nem
como se escreve o texto que o comunica (`texto-utilizador/SKILL.md`) —
só o mecanismo que vigia se esse texto continua dentro do prazo.

## Uso

Invocar antes de: editar `MARCADORES_HISTORICOS`
(`scripts/verificar_datas.py`) ou qualquer uma das outras duas listas
de supressão; mover o carimbo "Verificado a" de uma página com um
marcador histórico próximo de uma data futura; criar um sentinela
dirigido novo em `scripts/scraper_playwright.py`; ou escrever um
prazo/data-limite que ainda não passou. Complementa
`fact-check/SKILL.md` (o facto está certo, e com que grau) e
`texto-utilizador/SKILL.md` (como se escreve — "VOZ IMPERATIVA CADUCA"
é o mesmo problema desta skill, visto do lado da redacção em vez do
mecanismo).

## AS PEÇAS

- **`scripts/verificar_datas.py`** — Camada 1, a única que decide se um
  alerta é gerado. Procura `data_mes_ano`/`data_numerica`/`prazo_outono`
  (e, à parte, `ano_letivo`/`valor_ias`, sem grupo de ano dedicado) em
  título, meta description e corpo de cada página (raiz + `p/` +
  `documentos/`), só nos meses de `REVER_EM` por tipo.
  `classificar_datas.py`/`decisao_datas.py` (Camadas 2-3) só anexam
  metadado informativo (`alerta["classificacao"]`/`["decisao"]`) —
  nunca influenciam se a Issue é criada. Já houve o engano inverso:
  assumir que `"decisao": {"acao": "IGNORAR"}` gravado no próprio
  alerta significava que não tinha gerado Issue (achado #51/#52,
  `apoio-extraordinario-renda.html`/`porta-65.html`) — a única coisa
  que decide é `_esta_suprimido()`, aplicado ocorrência a ocorrência.
- **`MARCADORES_HISTORICOS`** — lista de regex em `verificar_datas.py`
  que suprime ocorrências legítimas (citação de diploma, data-limite de
  elegibilidade fixa, facto histórico permanente). Cada entrada é
  global ao site, nunca restrita a uma página — a supressão vem sempre
  da especificidade da frase, nunca do ficheiro onde aparece (issue
  #172: `\bsalvaguarda\b` sozinha apanhava qualquer menção verbal;
  corrigida para `\bsalvaguarda\s+(?:transit[óo]ria\s+)?de\s+\d`).
  Baseline exacto de que ocorrência cada entrada suprime, em cada
  página real: `tests/marcadores_historicos_baseline.json`, gerado por
  `scripts/auditar_marcadores_historicos.py` e auditado por
  `tests/test_auditar_marcadores_historicos.py`.
- **`EXCECOES_DIPLOMAS_FONTES`** (`tests/test_fontes_coerencia.py`) —
  todo diploma citado em texto visível no formato "Tipo n.º NNN/AAAA"
  precisa de cartão em `fontes.html`, ou entrada aqui com o motivo.
- **`EXCECOES_ANOS_HISTORICOS`** (`tests/test_anos_metadados.py`) —
  mesma ideia para anos civis em `<title>`/meta description: um ano
  anterior ao corrente (`ANO_ATUAL = datetime.now().year`, nunca fixo)
  só passa se for número de diploma ou facto histórico permanente.
- **Tabela "PÁGINAS COM DATAS SAZONAIS"** (`CLAUDE.md`) — orientação
  humana, não mecanismo. `verificar_datas.py` cobre qualquer página com
  um padrão reconhecido esteja ou não listada; a tabela incompleta
  engana quem a lê a pensar que só essas páginas têm datas a rever.
  Acrescentar uma página nova com data sazonal à tabela é documentação,
  nunca condição de cobertura.
- **`dados/parametros/*.yaml` + `tests/test_valores_ancora.py`** —
  valor canónico único por parâmetro, com vigência e
  `referencia_legal`/`fonte_url`/`verificado_em`. Os canários ligam
  página ↔ YAML (recalculam `multiplicador × IAS` ou comparam por
  presença de string), nunca o inverso — o YAML nunca deriva de uma
  página.

Nota: o carimbo "Verificado a" que o portão abaixo usa é extraído por
`sincronizar_clusters.verificado_em_do_texto()` — a mesma função que
alimenta o bloco "Atualizado recentemente" da homepage e a revalidação
de carimbo (`auto_update_engine.aplicar_refresh_carimbo`, Fase 4,
`REVALIDACAO_CARIMBO_HABILITADA = False`). Mexer no carimbo mexe nos
três ao mesmo tempo.

## O PORTÃO DE CONFIRMAÇÃO (#183)

Um marcador de `MARCADORES_HISTORICOS` só suprime **permanentemente**
uma ocorrência se a data que ele protege for anterior ou igual ao
carimbo "Verificado a" da página (`verificar_datas._esta_suprimido()`).
Se a data protegida for **posterior** ao carimbo, o marcador passa a
comportar-se como `MARCADORES_PENDENTE`: suprimido só até essa data
passar, depois exposto normalmente.

Razão: a mesma frase pode descrever tanto um limite já fechado para
sempre (PAER, "celebrados até 15 de março de 2023" — já passou, fecha
para sempre) como um prazo em vigor que a lei ainda pode prorrogar
(Garantia Pública, "contratos celebrados até 31 de dezembro de 2026" —
ainda não passou). O mesmo marcador `celebrados?\s+at[ée]\b` cobre os
dois; só o portão os distingue.

Consequência prática: **mover o carimbo "Verificado a" não é um gesto
neutro**. Avançar a data move a fronteira do portão — uma data que
antes ficava exposta (posterior ao carimbo antigo) pode passar a ficar
suprimida (anterior ao carimbo novo), ou o inverso. Antes de avançar um
carimbo numa página com marcador histórico próximo de uma data futura,
confirmar que a supressão resultante ainda é a correcta.

Sem carimbo (só `fontes.html`, entre as páginas com citações de
diploma): preserva-se o comportamento antigo, supressão sempre
permanente — nunca "sem carimbo = expõe tudo".

## AS TRÊS LISTAS DE SUPRESSÃO, MESMO PADRÃO

`MARCADORES_HISTORICOS`/baseline, `EXCECOES_DIPLOMAS_FONTES` e
`EXCECOES_ANOS_HISTORICOS` são a mesma ideia três vezes: uma lista de
excepções versionada, nunca um limiar numérico. Cada uma precisa dos
mesmos três braços de auto-auditoria:

1. **Nova/em falta** — algo no corpus que a lista ainda não cobre
   (supressão nova não aprovada; diploma citado sem cartão; ano
   civil antigo sem excepção).
2. **Órfã** — uma entrada da lista que já não corresponde a nada real
   no corpus (marcador que deixou de disparar; diploma que ganhou
   cartão; ano que já não aparece na página).
3. **Baseline por ocorrência** (só `MARCADORES_HISTORICOS`/
   `EXCECOES_ANOS_HISTORICOS`) — comparação exacta do contexto de cada
   ocorrência, não só presença — uma 2.ª ocorrência do mesmo
   marcador/ano por um motivo diferente e nunca revisto não pode ficar
   suprimida em silêncio pela mesma entrada.

O braço de órfã **tem de usar o mesmo critério de detecção** da
supressão que está a validar — nunca uma variante mais frouxa. Já
correu mal uma vez: `EXCECOES_ANOS_HISTORICOS` nasceu (issue #208) com
o braço de órfã a testar `str(ano) in texto` — substring solta, que
aceitaria "2007" dentro de "12007" ou de um valor monetário sem relação
nenhuma — em vez do mesmo `REGEX_ANO` (`\b(19|20)\d{2}\b`) com fronteira
de palavra que a asserção principal usa. Corrigido para os três braços
reais (`test_excecoes_sao_orfas_ou_ja_resolvidas`,
`test_excecoes_contexto_bate_com_o_registado`,
`test_excecoes_contexto_registado_contem_o_proprio_ano`). Ao criar uma
lista de supressão nova neste repositório, este é o padrão a copiar —
não os dois braços mais fracos que já existiram noutra lista.

## O QUE NENHUM DESTES APANHA

Três lacunas conhecidas, já materializadas — não hipotéticas.

**Texto interpolado em runtime.** Um banner gerado por JavaScript a
partir de um parâmetro nunca existe literalmente no ficheiro HTML —
invisível a `verificar_datas.py`, que só lê o disco. Só a versão
estática de *fallback* passa pelo scan. Caso real: um banner de
`simulador-psu.html` passava a dizer "a PSU já está a ser paga" assim
que o relógio do visitante cruzasse 31/12/2026, sem qualquer
confirmação — nunca detectado porque a frase nunca existia no HTML, só
era composta pelo JS (ver `texto-utilizador/SKILL.md` →
"FACTO LEGAL vs FACTO OPERACIONAL"). Ao alterar um destes, confirma
sempre que a versão estática e a versão interpolada dizem o mesmo.

**Valores escritos à mão em várias ocorrências.** O canário do YAML
(`tests/test_valores_ancora.py`) costuma verificar só *presença* — a
data/valor aparece pelo menos uma vez no corpo — nunca as restantes
ocorrências da mesma página ou de páginas irmãs (ver
`test_paer_data_limite_contrato_15_marco_2023_no_corpo`, cujo próprio
docstring diz "testa só a presença, nunca a contagem exacta de
ocorrências"). A Garantia Pública é o caso extremo: a data de
31/12/2026 está escrita à mão em 3 páginas diferentes
(`garantia-publica-credito-habitacao.html` — meta/og description, FAQ,
HowTo, resposta rápida, checklist, aviso —, mais `fontes.html` e
`p/habitacao.html`), mais de uma dezena de ocorrências ao todo, nenhuma
a ler o valor em runtime. Não fies a contagem exacta que o `CLAUDE.md`
registou numa sessão passada — já divergiu (`grep -o "31 de dezembro de
2026" garantia-publica-credito-habitacao.html | wc -l` dava 9 quando
essa nota foi escrita; dá 10 hoje). Antes de dar por terminada uma
correcção a um valor com várias ocorrências, conta-as de novo
(`grep -c` na página e nas páginas irmãs do mesmo cluster) — não
assumas que o teste que passou, ou a nota antiga, cobriu todas.

**Prazos que caducam sem a data ficar falsa.** Ver
`texto-utilizador/SKILL.md` → "VOZ IMPERATIVA CADUCA": uma data-limite
que passa não fica tecnicamente errada, mas um passo de `HowTo` ou uma
checkbox escritos na voz imperativa ("Fecha o contrato até [data]")
continuam a parecer accionáveis depois de a janela fechar — pior do que
uma data errada, porque instrui para uma acção já impossível sem
avisar disso. Nenhuma das três peças de supressão detecta este
problema; é sempre revisão humana no dia seguinte ao prazo.

## SENTINELAS DE ALTERAÇÃO LEGISLATIVA

Um sentinela DRE que só reconhece Decreto-Lei (`detectar_decreto_lei`/
`_detectar_decreto_lei_generico`) fica cego se o diploma que vigia
puder ser alterado por Portaria — caso real duas vezes: `dre_psu` só
via Decreto-Lei sobre a PSU, mas o artigo 17.º (habitação) e os
artigos 32.º/59.º (procedimentos) só podiam ser regulamentados por
Portaria — daí o sentinela irmão `dre_psu_regulamentacao`
(`detectar_portaria`). Mesma coisa para `dre_habitacao_garantia`
(Decreto-Lei que altera o DL 44/2024) e `dre_habitacao_garantia_portaria`
(Portaria que altera o protocolo). Padrão: **mesmo termo de pesquisa**,
filtros opostos — os dois sentinelas vêem os mesmos resultados brutos
do DRE, cada um reage só ao tipo de acto que lhe compete. Antes de
confiar num sentinela existente ou de criar um novo: confirmar que via
legal a alteração pode tomar (ver o articulado, não a ementa —
`fact-check/SKILL.md` → "NÃO ASSUMIR 'ALTERAÇÃO SÓ DE FORMA'"); se
houver mais do que uma via, precisa de mais do que um sentinela.

Termo de pesquisa nunca em forma de citação de diploma ("n.º" + barra +
ano) — foi essa forma, não um bloqueio real do DRE, que deixou
`dre_habitacao_garantia` (44 dias) e `dre_psu_regulamentacao` (16 dias)
sem devolver um único resultado; guardrail permanente em
`tests/test_dre_termos_pesquisa.py`.

**Um sentinela novo tem de ter a sua chave em `SENTINELAS_DIRIGIDOS`
(`scripts/preparar_canal.py`)** — sem isso, o sentinela dispara a
Issue normal em `pipeline-diario.yml` (Step 8) mas o canal de WhatsApp
nunca reage (gatilho 1b, `obter_deteccao_sentinela()` só olha para as
chaves desse dict). A chave é a mesma escrita em
`data/scraped/avisos.log` por `scraper_playwright._registar_aviso()`
(chamada a partir de `_detectar_decreto_psu`/
`_detectar_decreto_lei_generico`/`_detectar_portaria_generico`) — hoje
`dre_psu_decreto_detectado`, `dre_psu_regulamentacao_portaria_detectada`,
`dre_habitacao_paer_decreto_detectado`,
`dre_habitacao_garantia_decreto_detectado`,
`dre_habitacao_garantia_portaria_detectada`,
`dre_ias_portaria_detectada`. Criar o sentinela em
`scraper_playwright.py` e esquecer este passo é um sentinela
funcionalmente mudo para o canal, mesmo gerando Issues perfeitamente.

## DATA QUE SE APROXIMA

Uma data-limite futura decide-se **antes**, não no dia em que passa. O
texto para o cenário "não houve prorrogação" escreve-se com
antecedência e fica guardado — nunca aplicado até o facto estar
confirmado na fonte primária. Padrão já usado para
`garantia-publica-credito-habitacao.html` (`CLAUDE.md` → "CLUSTER
HABITAÇÃO" → esqueleto de redacção para o cenário sem prorrogação):
tabela zona-a-zona (meta description, resposta rápida, passo do
`HowTo`, checkbox do checklist, FAQ, `.aviso-atencao`) com a redacção
actual e a proposta, marcada explicitamente "NUNCA APLICADO" até
`dre_habitacao_garantia_portaria` (ou verificação manual) confirmar o
que aconteceu de facto ao prazo de 31/12/2026.

Aplicar esse texto antes da confirmação é exactamente o erro que
`texto-utilizador/SKILL.md` descreve em "FACTO LEGAL vs FACTO
OPERACIONAL" — escrever como se um facto operacional (a medida
terminou) decorresse só da passagem da data. A aprovação de texto
visível segue sempre `steward/SKILL.md` → "TEXTO VISÍVEL AO
UTILIZADOR".

## REGRA AO ALTERAR UMA SUPRESSÃO

Qualquer entrada de qualquer uma das três listas precisa dos braços
completos descritos acima — nunca só o braço "nova/em falta". Antes de
alterar `MARCADORES_HISTORICOS`, um termo de sentinela, ou qualquer
filtro/keyword/regex desta máquina: medir contra o corpus real com o
número esperado declarado (`steward/SKILL.md` → "MEDIR ANTES DE
APLICAR"), e confirmar o guardrail a falhar de propósito antes de o dar
por bom (`steward/SKILL.md` → "PROVAR O GUARDRAIL A FALHAR").

O que se escala em vez de se resolver sozinho — lista completa em
`steward/SKILL.md` → "O QUE SE ESCALA, EM VEZ DE RESOLVER" — inclui
directamente esta skill: relaxar qualquer lista de supressão/baseline/
excepção, e alterar filtro/termo/corte de recência de um sentinela.

## VER TAMBÉM

`fact-check/SKILL.md` — se o facto por trás da data está confirmado, e
em que grau, antes de escrever. `texto-utilizador/SKILL.md` — como
fica escrito depois de confirmado, incluindo a mesma questão de voz
imperativa e factos operacionais vistos pelo lado da redacção.
`steward/SKILL.md` — processo de PR, o que escala, convenções.

## VERIFICAÇÃO FINAL

Suite + `ruff check scripts/ --select E,F,W --ignore E501 .`. PR sem
"Closes".
