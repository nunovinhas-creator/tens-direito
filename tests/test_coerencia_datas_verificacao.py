"""
Canário de coerência interna de datas de verificação por página
(2026-07-27, sessão seguinte à correcção de bolsa-de-merito.html).

Motivo: o commit 39ee747 carimbou "Verificado a 30/06/2026" no
<meta name="description">/og:description de bolsa-de-merito.html, quando
o resto da página (FAQ JSON-LD, tabela, fontes, dateModified do Article)
dizia "24/06/2026" — uma reescrita de título/descrição que carimbou a
data do próprio commit em vez de manter a data do fact-check original.
tests/test_anos_metadados.py só apanha ANOS civis desactualizados, cego a
duas datas do mesmo ano civil divergirem entre si — exactamente este caso
nunca teria sido apanhado por esse teste.

## O que é comparado, e porquê não "todas as ocorrências têm de ser iguais"

Uma 1.ª versão deste teste tentou "todas as ocorrências de 'Verificado a'
na página têm de ser a mesma data" — falso em ~7 páginas reais, porque o
site segue deliberadamente a regra 5 de "REGRAS DE CONTEÚDO" ("Data em
cada facto") — uma citação específica (ex.: um valor da tabela do abono,
ou a secção "Bónus: Cartão Europeu de Estacionamento" acrescentada a
`amim.html`/`cuidador-informal.html`/`prestacao-social-para-a-inclusao.html`
a 11/07/2026, sempre distinta do resto da página por desenho) pode ter a
sua própria data, mais antiga do que a revisão mais recente da página, e
nunca é sincronizada — nem devia ser.

O que TEM de ser sempre uma só data, sem excepção legítima possível:

1. **`<meta name="description">`/`og:description`** — nunca uma citação
   de facto específico, é sempre um resumo ao nível da página inteira.
   Foi exactamente aqui que o bug de bolsa-de-merito aconteceu.
2. **A ÚLTIMA ocorrência de "Verificado a" no ficheiro** — mesma
   convenção já usada por `sincronizar_clusters.extrair_verificado_em()`
   (que alimenta o bloco "Atualizado recentemente" da homepage): é a
   ocorrência mais próxima do bloco de fontes/disclaimer no fim do
   corpo, a canónica da página. Ocorrências anteriores no ficheiro são
   notas por secção e podem legitimamente ser mais antigas — só a
   última é que tem de bater certo com o resto.

Ambas comparadas com o `dateModified` do `Article` JSON-LD, sempre à
precisão do valor menos preciso (um `dateModified` parcial tipo
"2026-06", sem dia, só é comparado a ano+mês, nunca falha por o dia
estar ausente — ver `simulador-ase.html`).

Corre só sobre páginas com exactamente um bloco `Article` JSON-LD — o
universo onde "esta página foi verificada nesta data" é uma afirmação
com sentido. Exclui por construção `index.html` e hubs (`documentos.html`,
`simuladores.html`, `dados.html`), que não têm `Article` e listam/citam
datas de vários artigos diferentes por desenho (nunca uma única data de
página).

**Zero excepções documentadas nesta versão** — a investigação real desta
sessão (correndo o teste sem excepção nenhuma contra as ~68 páginas com
Article único) confirmou que este âmbito (meta/og description + última
ocorrência) já não precisa de nenhuma, ao contrário de uma 1.ª tentativa
mais ampla. Encontrou, em vez disso, 3 bugs reais da mesma classe do de
bolsa-de-merito — ver ROADMAP.md/CLAUDE.md para o resultado dessa
investigação. Se uma futura página legítima precisar mesmo de uma
excepção (mesmo padrão de `EXCECOES_ANOS_HISTORICOS` em
`test_anos_metadados.py`), acrescentar aqui — nunca silenciar um teste
vermelho sem essa justificação registada.

Corre sobre as páginas reais (mesmo padrão de test_anos_metadados.py/
test_higiene_indexacao.py), nunca uma cópia.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import _REGEX_VERIFICADO, MESES_PT, encontrar_paginas  # noqa: E402

_REGEX_DATE_MODIFIED = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
_REGEX_ARTICLE_JSONLD = re.compile(r'<script type="application/ld\+json">([\s\S]*?)</script>')
_REGEX_META_DESCRIPTION = re.compile(
    r'<meta (?:name="description"|property="og:description") content="([^"]*)"'
)


def _paginas_com_article_unico() -> list[Path]:
    resultado = []
    for p in sorted(encontrar_paginas(RAIZ), key=lambda x: str(x)):
        html = p.read_text(encoding="utf-8")
        blocos = _REGEX_ARTICLE_JSONLD.findall(html)
        if sum(1 for b in blocos if '"@type": "Article"' in b) == 1:
            resultado.append(p)
    return resultado


PAGINAS = _paginas_com_article_unico()
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]


def _parse_match(g: dict) -> date:
    if g["d1"]:
        return date(int(g["y1"]), int(g["m1"]), int(g["d1"]))
    if g["d2"]:
        return date(int(g["y2"]), MESES_PT[g["mes2"].lower()], int(g["d2"]))
    return date(int(g["y3"]), MESES_PT[g["mes3"].lower()], int(g["d3"]))


def _precisao(ano: int, mes: int | None, dia: int | None) -> tuple[int, ...]:
    """Trunca uma data à precisão pedida — mes/dia None ficam de fora."""
    partes = [ano]
    if mes is not None:
        partes.append(mes)
        if dia is not None:
            partes.append(dia)
    return tuple(partes)


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_datas_de_verificacao_coerentes_dentro_da_pagina(caminho):
    pagina = str(caminho.relative_to(RAIZ))
    html = caminho.read_text(encoding="utf-8")

    blocos = _REGEX_ARTICLE_JSONLD.findall(html)
    artigos = [json.loads(b) for b in blocos if '"@type": "Article"' in b]
    assert len(artigos) == 1, f"{pagina}: esperava 1 bloco Article, encontrou {len(artigos)}"

    dm_raw = artigos[0].get("dateModified", "")
    m_dm = _REGEX_DATE_MODIFIED.match(dm_raw)
    assert m_dm, f"{pagina}: dateModified inválido: {dm_raw!r}"
    ano_dm, mes_dm, dia_dm = m_dm.groups()
    precisao_dm = _precisao(int(ano_dm), int(mes_dm) if mes_dm else None, int(dia_dm) if dia_dm else None)
    n_precisao = len(precisao_dm)

    todas = list(_REGEX_VERIFICADO.finditer(html))
    if not todas:
        pytest.skip(f"{pagina}: nenhuma ocorrência de 'Verificado a' no corpo/meta")

    # (a) meta name="description" / og:description — nunca uma citação de
    # facto específico, é sempre o resumo da página inteira.
    candidatos = [
        _REGEX_VERIFICADO.search(conteudo_meta)
        for conteudo_meta in _REGEX_META_DESCRIPTION.findall(html)
    ]
    candidatos = [m for m in candidatos if m]

    # (b) a última ocorrência no ficheiro — mesma convenção de
    # extrair_verificado_em(), a canónica da página.
    candidatos.append(todas[-1])

    valores = {precisao_dm}
    for m in candidatos:
        d = _parse_match(m.groupdict())
        valores.add(_precisao(d.year, d.month, d.day)[:n_precisao])

    assert len(valores) == 1, (
        f"{pagina}: datas de verificação incoerentes — dateModified={dm_raw!r}, "
        f"valores encontrados (à precisão do dateModified) na meta description/"
        f"og:description e/ou na última ocorrência de 'Verificado a' do "
        f"ficheiro={sorted(valores)!r}. Corrija a que estiver desactualizada — "
        "nunca uma excepção sem justificação documentada (ver docstring deste "
        "ficheiro)."
    )


def test_pelo_menos_50_paginas_cobertas():
    """Guarda contra `encontrar_paginas()`/a extracção de Article partir
    em silêncio e o teste passar vazio sem cobrir nada."""
    assert len(PAGINAS) >= 50
