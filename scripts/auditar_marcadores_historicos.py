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

Nunca escreve HTML nem altera MARCADORES_HISTORICOS — só lê.
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import encontrar_paginas, verificado_em_do_texto  # noqa: E402
from verificar_datas import (  # noqa: E402
    AUTO_GERADOS,
    MARCADORES_HISTORICOS,
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


def _normalizar_contexto(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


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


def supressoes_da_pagina(conteudo: str, pagina: str, ano: int = ANO_REFERENCIA) -> list[dict]:
    """Todas as (ocorrência antiga, marcador) desta página — sem `ordinal`
    ainda, essa desambiguação de duplicados exactos é feita a nível do
    corpus inteiro em `auditar_corpus()`."""
    verificado_em = verificado_em_do_texto(conteudo)
    registos = []
    for padrao in PADROES:
        for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
            if not _e_ocorrencia_antiga(padrao, m, conteudo, ano):
                continue
            janela = _janela_contexto(conteudo, m.start(), m.end())
            data_ocorrencia = _data_da_ocorrencia(padrao, m)
            if _fica_exposta_ao_portao(data_ocorrencia, verificado_em, ano):
                continue  # já não é permanente à data de referência — ver docstring do módulo
            for marcador in MARCADORES_HISTORICOS:
                if re.search(marcador, janela, re.IGNORECASE):
                    registos.append({
                        "pagina": pagina,
                        "marcador": marcador,
                        "tipo": padrao["tipo"],
                        "correspondencia": m.group(0),
                        "contexto": _normalizar_contexto(janela),
                    })
    return registos


def auditar_corpus(raiz: Path = RAIZ, ano: int = ANO_REFERENCIA) -> list[dict]:
    """Todas as supressões do corpus, com `ordinal` (1-based, por ordem de
    aparição no ficheiro) para desambiguar duplicados exactos — a mesma
    (pagina, marcador, tipo, correspondencia) pode legitimamente aparecer
    mais do que uma vez na mesma página. Ordenado de forma determinística
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
            chave = (registo["pagina"], registo["marcador"], registo["tipo"], registo["correspondencia"])
            contador[chave] += 1
            registo["ordinal"] = contador[chave]
            todos.append(registo)

    todos.sort(key=lambda r: (r["pagina"], r["marcador"], r["tipo"], r["correspondencia"], r["ordinal"]))
    return todos


def identidade(registo: dict) -> tuple:
    """Chave de comparação — nunca inclui `contexto` (ver docstring do
    módulo: o contexto é só informativo, sensível a edições próximas mas
    irrelevantes; comparar por ele tornaria o baseline demasiado frágil)."""
    return (registo["pagina"], registo["marcador"], registo["tipo"],
            registo["correspondencia"], registo["ordinal"])


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
