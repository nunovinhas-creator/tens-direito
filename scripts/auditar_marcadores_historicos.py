#!/usr/bin/env python3
"""Auditoria de MARCADORES_HISTORICOS (`scripts/verificar_datas.py`) contra
o corpus completo de páginas — Issue #183, passo 1.

Para cada entrada de `MARCADORES_HISTORICOS`, percorre todas as páginas
reais do site e regista cada ocorrência de data/valor "antiga" (mesmo
critério usado por `_pagina_tem_alerta` — ano anterior ao ano de
referência) cuja janela de contexto (`_janela_contexto`, 220 caracteres
para cada lado, o mesmo raio usado em produção) corresponde ao regex desse
marcador. Uma ocorrência pode ficar registada contra mais do que um
marcador, se a janela contiver mais do que um deles.

Isto é uma reimplementação deliberada, não uma reutilização de
`_esta_suprimido()` — essa função só devolve um booleano (suprimido/não),
sem dizer QUAL marcador foi responsável; aqui precisamos da atribuição
individual, marcador a marcador, para o baseline poder identificar cada
supressão pela entrada exacta que a causa.

`MARCADORES_EXEMPLO` e `MARCADORES_PENDENTE` (as outras duas listas usadas
por `_esta_suprimido`) ficam deliberadamente fora — o âmbito desta
auditoria é só `MARCADORES_HISTORICOS`, por instrução da Issue #183.

Issue #183, passo 2 — portão de confirmação espelhado: `_esta_suprimido()`
já não trata um marcador de `MARCADORES_HISTORICOS` como permanente sem
mais nada — só o é se a data protegida for anterior (ou igual) ao carimbo
"Verificado a" da página; posterior a isso, expira à mesma data (ver
`scripts/verificar_datas.py`). Sem espelhar esse portão aqui, esta
auditoria continuaria a registar como "suprimida" uma ocorrência que
`_esta_suprimido()` já expôs de facto — o baseline mentiria sobre o que a
produção realmente faz. `_fica_exposta_ao_portao()` decide isto por
correspondência (não reutiliza `_esta_suprimido()` directamente — essa
função não devolve qual marcador respondeu, só um booleano agregado).

Ano de referência FIXO (nunca `datetime.now()`): mesma disciplina já usada
em `tests/test_verificar_datas.py` (`ANO = 2026`, fixo) — um teste de
regressão não pode ficar dependente do calendário. Se `ANO_REFERENCIA`
ficasse a acompanhar o ano real, uma menção a "2026" que hoje não é
"antiga" passaria a sê-lo em 2027 só por o calendário avançar, sem
nenhuma alteração ao código nem ao conteúdo — o teste falharia por uma
razão que não tem nada a ver com uma regressão real. Fixar o ano à data
desta auditoria (2026) torna o resultado uma função só de
MARCADORES_HISTORICOS + conteúdo das páginas, nunca do dia em que a
suite corre.

Identidade de cada supressão (issue #264): (pagina, marcador, tipo,
correspondencia, frase, ordinal). `frase` é a frase envolvente da
ocorrência (ver `frase_envolvente()`), e `ordinal` só desempata ocorrências
com a MESMA frase na mesma página (ex.: a FAQ repetida no corpo e no
JSON-LD). Antes, o ordinal contava todas as ocorrências com a mesma
correspondência na página: inserir um cartão novo antes de um antigo
deslocava as entradas antigas e fazia-as aparecer como «novas» (#260,
Portaria n.º 158/2024/1). Agora, uma edição fora da frase não muda nada;
uma edição dentro da frase aparece como uma entrada órfã (frase antiga)
mais uma nova (frase actual) — obriga a olhar para a frase alterada.

Issue #186 — `MARCADORES_ISENTOS_DO_PORTAO` (subconjunto de
MARCADORES_HISTORICOS): datas fixadas por lei, citadas como facto
permanente, que `_esta_suprimido()` suprime antes do portão. A auditoria
regista-as mesmo quando a data não é "antiga" face a `ANO_REFERENCIA` — basta
ser posterior ao carimbo "Verificado a" (o conjunto que o portão exporia mais
tarde). Sem isto, estas supressões só apareceriam no baseline depois de a data
passar, e nunca teriam sido revistas linha a linha antes de entrarem em vigor.
Nesses casos só os marcadores isentos são atribuídos: os restantes marcadores
históricos da janela não suprimem uma data posterior ao carimbo.

Nunca escreve HTML nem altera MARCADORES_HISTORICOS — só lê.
"""

import argparse
import html
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import encontrar_paginas, verificado_em_do_texto  # noqa: E402
from verificar_datas import (  # noqa: E402
    AUTO_GERADOS,
    MARCADORES_HISTORICOS,
    MARCADORES_ISENTOS_DO_PORTAO,
    PADROES,
    _data_da_ocorrencia,
    _janela_contexto,
)

BASELINE_PATH = RAIZ / "tests" / "marcadores_historicos_baseline.json"

# Fixo — ver docstring do módulo.
ANO_REFERENCIA = 2026


def paginas_do_corpus(raiz: Path = RAIZ) -> list[Path]:
    """Mesmo corpus que `verificar_datas.main()` processa — reutiliza o
    enumerador canónico `sincronizar_clusters.encontrar_paginas()` (raiz +
    p/ + documentos/) e aplica a mesma exclusão de `AUTO_GERADOS`
    (index.html/noticias.html/404.html — regeneradas todos os dias pelo
    pipeline; incluí-las tornaria o baseline instável por razões que nada
    têm a ver com uma alteração aos marcadores ou a uma página de
    conteúdo manual)."""
    return [
        p for p in encontrar_paginas(raiz)
        if p.name not in AUTO_GERADOS
    ]


def _e_ocorrencia_antiga(padrao: dict, match: re.Match, conteudo: str, ano: int) -> bool:
    """Mesmo critério de "antiga" usado por `_pagina_tem_alerta` em
    `verificar_datas.py`, mas por correspondência individual (aqui
    precisamos de decidir isto ocorrência a ocorrência, não só "a página
    tem, pelo menos, uma")."""
    tipo = padrao["tipo"]
    if tipo == "ano_letivo":
        return int(match.group(1)) < ano
    if tipo == "valor_ias":
        janela = _janela_contexto(conteudo, match.start(), match.end())
        anos_proximos = [int(a) for a in re.findall(r"\b(20\d{2})\b", janela)]
        return any(a < ano for a in anos_proximos)
    return int(match.group(padrao["ano_grupo"])) < ano


def _fica_exposta_ao_portao(data_ocorrencia, verificado_em, ano: int) -> bool:
    """Mesma decisão do portão de confirmação de `_esta_suprimido()`
    (issue #183, passo 2), aplicada aqui à data de referência fixa desta
    auditoria — nunca ao calendário real. Sem `data_ocorrencia` (tipo sem
    data própria) ou sem `verificado_em` (página sem carimbo — hoje só
    páginas sem citações de diploma) preserva-se o comportamento anterior:
    o marcador continua a contar como supressão permanente, nunca
    "sem carimbo = expõe tudo". Esta auditoria não tem um "mês" próprio
    (só `ANO_REFERENCIA`, fixo por desenho) — usa o último dia do ano de
    referência como o ponto no tempo a comparar, o mais tarde possível
    dentro desse ano; um prazo que só ultrapassa isso num ano posterior
    continua correctamente suprimido nesta auditoria."""
    if data_ocorrencia is None or verificado_em is None:
        return False
    if data_ocorrencia <= verificado_em:
        return False  # já era um facto fechado à última verificação — permanente
    return data_ocorrencia <= date(ano, 12, 31)


def _posterior_ao_carimbo(data_ocorrencia, verificado_em) -> bool:
    """Data que o portão de confirmação acabaria por expor (posterior ao
    carimbo "Verificado a") — só usada para os marcadores isentos (#186)."""
    return data_ocorrencia is not None and verificado_em is not None and data_ocorrencia > verificado_em


# Tags que não partem uma frase: pôr uma palavra a negrito ou num link não
# muda a identidade da supressão. Qualquer outra tag (p, li, td, h3, …) é
# limite de bloco.
_TAGS_INLINE = frozenset({
    "a", "abbr", "b", "code", "em", "i", "mark", "small", "span", "strong", "sub", "sup",
})
_REGEX_JSONLD = re.compile(r'<script type="application/ld\+json">.*?</script>', re.S)
_REGEX_TAG = re.compile(r"<[^>]*>")
_REGEX_NOME_TAG = re.compile(r"</?\s*([a-zA-Z0-9]+)")
# Fim de frase: pontuação final, espaço e maiúscula. "art. 4.º" e
# "n.º 307" não partem a frase (a seguir ao ponto não vem espaço+maiúscula).
_REGEX_FIM_FRASE = re.compile(
    r'[.!?…]["»”)]?(?:\s|&nbsp;|&#160;)+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÀÇ«"“(])'
)
# NBSP e espaços finos/estreitos contam como espaço normal na frase.
_ESPACOS_ESPECIAIS = dict.fromkeys(map(ord, "\u00a0\u2007\u2009\u200a\u202f"), " ")


def _e_tag_inline(tag: str) -> bool:
    nome = _REGEX_NOME_TAG.match(tag)
    return bool(nome) and nome.group(1).lower() in _TAGS_INLINE


def _normalizar_frase(texto: str, em_jsonld: bool) -> str:
    texto = html.unescape(texto)
    if em_jsonld:
        texto = texto.replace('\\"', '"')
    texto = unicodedata.normalize("NFC", texto.translate(_ESPACOS_ESPECIAIS))
    return re.sub(r"\s+", " ", texto).strip()


def _dentro_de_jsonld(conteudo: str, inicio: int) -> bool:
    return any(m.start() < inicio < m.end() for m in _REGEX_JSONLD.finditer(conteudo))


def _valor_de_atributo(conteudo: str, inicio: int, fim: int) -> str | None:
    """Se a ocorrência está dentro de uma tag (ex.: meta description), a
    frase é o valor do atributo que a contém."""
    abre = conteudo.rfind("<", 0, inicio)
    if abre == -1 or conteudo.rfind(">", 0, inicio) > abre:
        return None
    for aspa in ('"', "'"):
        esq = conteudo.rfind(aspa, abre, inicio)
        dir_ = conteudo.find(aspa, fim)
        if esq != -1 and dir_ != -1 and conteudo.find(">", fim, dir_) == -1:
            return conteudo[esq + 1:dir_]
    return None


def frase_envolvente(conteudo: str, inicio: int, fim: int) -> str:
    """Frase que contém a ocorrência `conteudo[inicio:fim]`, normalizada.

    Expande a partir da ocorrência até ao limite do bloco — tag de bloco,
    string JSON (só dentro de JSON-LD; fora dele as aspas são texto) — com
    as tags inline transparentes; dentro do bloco, corta na frase; tira as
    tags, desfaz entidades, converte NBSP/espaços finos em espaço, aplica
    NFC e colapsa espaços. Dentro de um atributo, a frase é o valor do
    atributo."""
    comentario = conteudo.rfind("<!--", 0, inicio)
    fim_comentario = conteudo.find("-->", comentario) if comentario != -1 else -1
    if comentario != -1 and fim_comentario >= fim:
        # Dentro de um comentário HTML: o bloco é o próprio comentário.
        return _frase_no_bloco(conteudo, comentario + 4, fim_comentario, inicio, fim, False)

    atributo = _valor_de_atributo(conteudo, inicio, fim)
    if atributo is not None:
        return _normalizar_frase(atributo, em_jsonld=False)

    em_jsonld = _dentro_de_jsonld(conteudo, inicio)

    i = inicio
    while i > 0:
        ch = conteudo[i - 1]
        if ch == ">":
            j = conteudo.rfind("<", 0, i - 1)
            if j != -1 and _e_tag_inline(conteudo[j:i]):
                i = j
                continue
            break
        if em_jsonld and ch == '"' and conteudo[i - 2:i - 1] != "\\":
            break
        i -= 1

    k = fim
    while k < len(conteudo):
        ch = conteudo[k]
        if ch == "<":
            j = conteudo.find(">", k)
            if j != -1 and _e_tag_inline(conteudo[k:j + 1]):
                k = j + 1
                continue
            break
        if em_jsonld and ch == '"' and conteudo[k - 1] != "\\":
            break
        k += 1
    return _frase_no_bloco(conteudo, i, k, inicio, fim, em_jsonld)


def _frase_no_bloco(conteudo: str, i: int, k: int, inicio: int, fim: int, em_jsonld: bool) -> str:
    """Corta, dentro do bloco `conteudo[i:k]`, a frase que contém a
    ocorrência `conteudo[inicio:fim]`, depois de tirar as tags inline."""
    bloco = conteudo[i:k]
    pedacos, pos, removidos_antes = [], 0, 0
    for m in _REGEX_TAG.finditer(bloco):
        pedacos.append(bloco[pos:m.start()])
        if m.end() <= inicio - i:
            removidos_antes += m.end() - m.start()
        pos = m.end()
    pedacos.append(bloco[pos:])
    texto = "".join(pedacos)
    ini_ocorrencia = inicio - i - removidos_antes
    fim_ocorrencia = ini_ocorrencia + (fim - inicio)

    ini_frase, fim_frase = 0, len(texto)
    for m in _REGEX_FIM_FRASE.finditer(texto):
        if m.end() <= ini_ocorrencia:
            ini_frase = m.end()
        elif m.start() >= fim_ocorrencia:
            fim_frase = m.start() + 1
            break
    return _normalizar_frase(texto[ini_frase:fim_frase], em_jsonld)


def supressoes_da_pagina(conteudo: str, pagina: str, ano: int = ANO_REFERENCIA) -> list[dict]:
    """Todas as (ocorrência antiga, marcador) desta página — sem `ordinal`
    ainda, essa desambiguação de frases repetidas é feita a nível do
    corpus inteiro em `auditar_corpus()`."""
    verificado_em = verificado_em_do_texto(conteudo)
    registos = []
    for padrao in PADROES:
        for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
            janela = _janela_contexto(conteudo, m.start(), m.end())
            data_ocorrencia = _data_da_ocorrencia(padrao, m)
            antiga = _e_ocorrencia_antiga(padrao, m, conteudo, ano)
            isentos = [mk for mk in MARCADORES_ISENTOS_DO_PORTAO if re.search(mk, janela, re.IGNORECASE)]
            if antiga and not _fica_exposta_ao_portao(data_ocorrencia, verificado_em, ano):
                candidatos = MARCADORES_HISTORICOS
            elif isentos and (antiga or _posterior_ao_carimbo(data_ocorrencia, verificado_em)):
                candidatos = isentos  # só a isenção a suprime (#186) — ver docstring do módulo
            else:
                continue
            frase = None
            for marcador in candidatos:
                if re.search(marcador, janela, re.IGNORECASE):
                    if frase is None:
                        frase = frase_envolvente(conteudo, m.start(), m.end())
                    registos.append({
                        "pagina": pagina,
                        "marcador": marcador,
                        "tipo": padrao["tipo"],
                        "correspondencia": _normalizar_frase(m.group(0), em_jsonld=False),
                        "frase": frase,
                    })
    return registos


def auditar_corpus(raiz: Path = RAIZ, ano: int = ANO_REFERENCIA) -> list[dict]:
    """Todas as supressões do corpus, com `ordinal` (1-based, por ordem de
    aparição no ficheiro) só para desambiguar a MESMA frase repetida na
    mesma página (ex.: FAQ no corpo e no JSON-LD) — nunca conta ocorrências
    noutras frases, que é o que tornava as entradas antigas sensíveis a
    texto inserido antes delas (issue #264). Ordenado de forma determinística
    (nunca pela ordem de varrimento do glob/regex, que não é garantida
    entre corridas) para o baseline nunca gerar diffs espúrios de
    ordenação."""
    todos = []
    contador: Counter = Counter()
    for caminho in paginas_do_corpus(raiz):
        pagina = str(caminho.relative_to(raiz))
        try:
            conteudo = caminho.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Erro ao ler {pagina}: {e}", file=sys.stderr)
            continue
        for registo in supressoes_da_pagina(conteudo, pagina, ano):
            chave = (registo["pagina"], registo["marcador"], registo["tipo"],
                     registo["correspondencia"], registo["frase"])
            contador[chave] += 1
            registo["ordinal"] = contador[chave]
            todos.append(registo)

    todos.sort(key=identidade)
    return todos


def identidade(registo: dict) -> tuple:
    """Chave de comparação e de ordenação (issue #264): a frase envolvente
    identifica a supressão; o ordinal só desempata a mesma frase repetida."""
    return (registo["pagina"], registo["marcador"], registo["tipo"],
            registo["correspondencia"], registo["frase"], registo["ordinal"])


def carregar_baseline(caminho: Path = BASELINE_PATH) -> list[dict]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_baseline(registos: list[dict], caminho: Path = BASELINE_PATH) -> None:
    caminho.write_text(
        json.dumps(registos, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _imprimir_relatorio(registos: list[dict]) -> None:
    por_marcador: dict[str, list[dict]] = {}
    for r in registos:
        por_marcador.setdefault(r["marcador"], []).append(r)

    print(f"{len(registos)} supressão(ões) em {len(por_marcador)}/{len(MARCADORES_HISTORICOS)} marcador(es) activos\n")

    for marcador in MARCADORES_HISTORICOS:
        entradas = por_marcador.get(marcador, [])
        print(f"--- {marcador!r} ({len(entradas)}) ---")
        for r in entradas:
            print(f"  {r['pagina']} [{r['tipo']}] {r['correspondencia']!r}")
        if not entradas:
            print("  (nenhuma supressão)")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write", action="store_true",
        help="Regenera tests/marcadores_historicos_baseline.json a partir do corpus actual "
             "(passo manual, nunca automático — revisar o diff antes de commitar).",
    )
    args = parser.parse_args()

    registos = auditar_corpus()

    if args.write:
        gravar_baseline(registos)
        print(f"Baseline regenerado: {len(registos)} registo(s) em {BASELINE_PATH.relative_to(RAIZ)}")
        return 0

    _imprimir_relatorio(registos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
