"""
Guardrail: os cards manuscritos de cada pillar (`.apoio-mini`/`.card-mini`)
têm de cobrir TODAS as páginas da PILLAR-LISTA dessa pillar.

A PILLAR-LISTA (marcador `PILLAR-LISTA:INICIO/FIM`) é gerada por
`scripts/sincronizar_clusters.py` a partir de `data/clusters.json` —
nunca fica incompleta, por desenho. Os cards `.apoio-mini`/`.card-mini`
são manuscritos: cada um tem texto editorial rico (valores, diplomas,
nuances de elegibilidade) que `data/clusters.json` não guarda para
todas as páginas — só as `destaque: true` têm `desc`/`emoji`, e mesmo
essas são descrições curtas, sem o detalhe dos cards reais. Decisão
consciente (ver CLAUDE.md → "SISTEMA DE CLUSTERS"): manter os cards
manuscritos e vigiar a divergência com este teste, em vez de os gerar
a partir do JSON.

Achado real que motivou este ficheiro (2026-09): 8 páginas publicadas
em 3 clusters (apoios-escolares, idosos-incapacidade-cuidadores,
habitacao) ficaram na PILLAR-LISTA sem card correspondente — nenhum
mecanismo comparava os dois lados, por isso ninguém reparou.

Duas famílias de card manuscrito coexistem no site:
- `.apoio-mini` — um `<div>` por página, com um ou mais links
  `.ver-guia` lá dentro (mais do que um quando o mesmo card também
  liga ao simulador irmão — ver `p/trabalho-rendimento.html`).
- `.card-mini` — um `<a class="card-mini">` por página, usado em
  `p/como-pedir.html` (agrupado por secção temática, `.grelha-cards`).

Ambos os padrões são reconhecidos por este teste — não há necessidade
de "abranger" ou de excepção documentada para nenhum dos dois: a
extracção é genérica ao padrão, não a uma página específica.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Set

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import MARCADOR_PILLAR_LISTA, carregar_clusters  # noqa: E402

RAIZ = Path(__file__).parent.parent
CLUSTERS = carregar_clusters(RAIZ / "data" / "clusters.json")

# Pillars cuja página nunca teve — por desenho editorial, não por
# esquecimento — um card individual por página-filha. Cada entrada exige
# justificação; test_excecoes_nunca_tem_cards_individuais confirma que
# a página não ganhou, entretanto, o padrão apoio-mini/card-mini (o que
# tornaria a excepção órfã e escondia um gap real).
PILLARS_SEM_CARDS_INDIVIDUAIS = {
    "prestacao-social-unica.html": (
        "pillar narrativo sobre a reforma da PSU — não é um índice de "
        "guias com um card por página-filha, ao contrário dos restantes "
        "pillars; liga às 8 páginas-filhas via PILLAR-LISTA + links "
        "pontuais no corpo + CTA do simulador, nunca um card dedicado "
        "por página."
    ),
}


def _caminho_pillar(cluster) -> Path:
    return RAIZ / cluster.pillar.lstrip("/")


def _extrair_pillar_lista(html: str) -> Set[str]:
    ini, fim = MARCADOR_PILLAR_LISTA
    m = re.search(rf"<!-- {ini} -->([\s\S]*?)<!-- {fim} -->", html)
    assert m, "marcador PILLAR-LISTA não encontrado ou vazio"
    return set(re.findall(r'<li><a href="/([^"]+)"', m.group(1)))


def _bloco_balanceado(html: str, tag_abertura: "re.Match[str]") -> str:
    """Conteúdo entre a tag <div ...> já encontrada e o </div> que lhe
    corresponde, contando profundidade — nunca um </div> ingénuo, que
    quebraria em silêncio se um card ganhasse um <div> aninhado no
    futuro (nenhum tem hoje, confirmado, mas a extracção não deve
    depender disso continuar a ser verdade)."""
    pos = tag_abertura.end()
    profundidade = 1
    for m in re.finditer(r"<div\b[^>]*>|</div>", html[pos:]):
        profundidade += 1 if m.group().startswith("<div") else -1
        if profundidade == 0:
            return html[pos:pos + m.start()]
    raise AssertionError("<div class=\"apoio-mini\"> sem </div> correspondente")


def _hrefs_apoio_mini(html: str) -> Set[str]:
    hrefs: Set[str] = set()
    for m in re.finditer(r'<div class="apoio-mini">', html):
        bloco = _bloco_balanceado(html, m)
        for hm in re.finditer(r"<a\s+[^>]*>", bloco):
            tag = hm.group()
            if not re.search(r'class="[^"]*\bver-guia\b[^"]*"', tag):
                continue
            href_m = re.search(r'href="/([^"]+)"', tag)
            if href_m:
                hrefs.add(href_m.group(1))
    return hrefs


def _hrefs_card_mini(html: str) -> Set[str]:
    hrefs: Set[str] = set()
    for m in re.finditer(r"<a\s+[^>]*>", html):
        tag = m.group()
        if not re.search(r'class="[^"]*\bcard-mini\b[^"]*"', tag):
            continue
        href_m = re.search(r'href="/([^"]+)"', tag)
        if href_m:
            hrefs.add(href_m.group(1))
    return hrefs


def _hrefs_cards(html: str) -> Set[str]:
    return _hrefs_apoio_mini(html) | _hrefs_card_mini(html)


CASOS = [
    c for c in CLUSTERS
    if _caminho_pillar(c).name not in PILLARS_SEM_CARDS_INDIVIDUAIS
]
IDS = [c.id for c in CASOS]


@pytest.mark.parametrize("cluster", CASOS, ids=IDS)
def test_todas_as_paginas_da_pillar_lista_tem_card(cluster):
    caminho = _caminho_pillar(cluster)
    html = caminho.read_text(encoding="utf-8")
    pillar_lista = _extrair_pillar_lista(html)
    cards = _hrefs_cards(html)
    orfaos = pillar_lista - cards
    assert not orfaos, (
        f"{cluster.pillar}: página(s) na PILLAR-LISTA sem card "
        f"correspondente (.apoio-mini/.card-mini): {sorted(orfaos)} — "
        f"escrever o card em falta (nunca gerar automaticamente, ver "
        f"cabeçalho deste ficheiro) ou, se for um desenho editorial "
        f"deliberado, documentar em PILLARS_SEM_CARDS_INDIVIDUAIS."
    )


def test_todas_as_paginas_da_pillar_lista_existem_em_disco():
    """Confirma que nenhuma página listada na PILLAR-LISTA é um link
    morto — falso positivo óbvio a evitar antes de confiar no resto
    deste ficheiro."""
    for cluster in CLUSTERS:
        html = _caminho_pillar(cluster).read_text(encoding="utf-8")
        for slug in _extrair_pillar_lista(html):
            assert (RAIZ / slug).is_file(), (
                f"{cluster.pillar}: PILLAR-LISTA aponta para "
                f"'{slug}', que não existe em disco"
            )


@pytest.mark.parametrize(
    "slug,justificacao", sorted(PILLARS_SEM_CARDS_INDIVIDUAIS.items())
)
def test_excecoes_nunca_tem_cards_individuais(slug, justificacao):
    """Uma excepção só se justifica enquanto a página genuinamente não
    usar o padrão apoio-mini/card-mini — se ganhar esse padrão (ex.:
    reescrita de UX), a excepção fica órfã e esconde um gap real."""
    assert justificacao, f"{slug}: excepção sem justificação"
    html = (RAIZ / slug).read_text(encoding="utf-8")
    assert not _hrefs_cards(html), (
        f"{slug} está em PILLARS_SEM_CARDS_INDIVIDUAIS mas já tem cards "
        f".apoio-mini/.card-mini — a excepção ficou órfã, remover e "
        f"deixar o teste principal cobrir esta pillar"
    )
