"""
Auditoria de indexação e higiene SEO técnica (2026-07-04) — rede de
segurança permanente. Falha se:

  1. um URL do sitemap.xml não tiver ficheiro correspondente no repo;
  2. uma página pública indexável não estiver no sitemap.xml, sem estar
     na lista `EXCLUSOES_SITEMAP` (deliberadas e justificadas abaixo);
  3. uma página pública não tiver `<link rel="canonical">`
     auto-referente, absoluto, sem `www` e sem `/index.html` explícito;
  4. uma página pública com FAQPage não tiver o objecto `Article`
     JSON-LD válido (author/publisher/datePublished/dateModified);
  5. uma página pública for órfã — inalcançável a partir de
     `index.html` navegando só por `href`s internos das próprias
     páginas (a mesma nav/HTML estático que o Google rastreia).

Corre no job "testes-python" do CI (`integridade.yml`), a cada push a
`main` — mesmo padrão de `test_nav_coerencia.py`/`test_breadcrumb_coerencia.py`.
"""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import encontrar_paginas  # noqa: E402

SITEMAP = RAIZ / "sitemap.xml"
DOMINIO = "https://tensdireito.com"

# Páginas públicas que existem mas são deliberadamente excluídas do
# sitemap — justificação por página, nunca "esquecimento":
EXCLUSOES_SITEMAP = {
    "404.html": "página de erro, robots noindex, sem conteúdo editorial (ver CLAUDE.md 'PÁGINAS INSTITUCIONAIS')",
}

PAGINAS = encontrar_paginas()
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]


def _url_para_ficheiro(url: str) -> str:
    caminho = url.replace(f"{DOMINIO}/", "")
    return "index.html" if caminho == "" else caminho


def _ficheiro_para_url(rel: str) -> str:
    return f"{DOMINIO}/" if rel == "index.html" else f"{DOMINIO}/{rel}"


def _urls_sitemap() -> list[str]:
    tree = ET.parse(SITEMAP)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [u.find("s:loc", ns).text for u in tree.findall("s:url", ns)]


# ── Passo 1: sitemap vs ficheiros reais ───────────────────────────────────

def test_sitemap_sem_www_http_ou_index_explicito():
    locs = "\n".join(_urls_sitemap())
    assert "www." not in locs
    assert "http://" not in locs
    assert "/index.html" not in locs


@pytest.mark.parametrize("url", _urls_sitemap())
def test_url_do_sitemap_tem_ficheiro_correspondente(url):
    rel = _url_para_ficheiro(url)
    assert (RAIZ / rel).exists(), f"sitemap referencia {url}, sem ficheiro {rel}"


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_pagina_publica_esta_no_sitemap_ou_tem_exclusao_justificada(caminho):
    rel = str(caminho.relative_to(RAIZ))
    urls_sitemap = set(_urls_sitemap())
    url_esperado = _ficheiro_para_url(rel)
    if rel in EXCLUSOES_SITEMAP:
        assert url_esperado not in urls_sitemap, (
            f"{rel} está marcada como exclusão deliberada do sitemap mas aparece lá — "
            "actualizar EXCLUSOES_SITEMAP ou o sitemap"
        )
        return
    assert url_esperado in urls_sitemap, (
        f"{rel} é uma página pública mas não está no sitemap.xml e não consta de "
        "EXCLUSOES_SITEMAP — adicionar ao sitemap ou justificar a exclusão"
    )


# ── Passo 2: canónicas ─────────────────────────────────────────────────────

_RE_CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)">')


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_pagina_tem_canonica_auto_referente(caminho):
    html = caminho.read_text(encoding="utf-8")
    m = _RE_CANONICAL.search(html)
    assert m, f"{caminho.name}: sem <link rel=\"canonical\">"

    href = m.group(1)
    assert href.startswith(f"{DOMINIO}/"), f"{caminho.name}: canónica não é absoluta/sem www: {href}"
    assert "www." not in href
    assert not href.endswith("/index.html"), f"{caminho.name}: canónica aponta a index.html explícito"

    rel = str(caminho.relative_to(RAIZ))
    esperado = _ficheiro_para_url(rel)
    assert href == esperado, f"{caminho.name}: canónica {href} != auto-referente esperado {esperado}"

    # nunca duplicada
    assert len(_RE_CANONICAL.findall(html)) == 1, f"{caminho.name}: mais de uma tag canonical"


# ── Passo 4b: Article JSON-LD ──────────────────────────────────────────────

def _paginas_com_faqpage():
    return [p for p in PAGINAS if '"@type": "FAQPage"' in p.read_text(encoding="utf-8")]


_PAGINAS_FAQ = _paginas_com_faqpage()
_IDS_FAQ = [str(p.relative_to(RAIZ)) for p in _PAGINAS_FAQ]


def test_pelo_menos_20_paginas_de_conteudo_reais():
    assert len(_PAGINAS_FAQ) >= 20


@pytest.mark.parametrize("caminho", _PAGINAS_FAQ, ids=_IDS_FAQ)
def test_pagina_de_conteudo_tem_article_jsonld_valido(caminho):
    html = caminho.read_text(encoding="utf-8")
    blocos = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', html)
    artigos = [json.loads(b) for b in blocos if '"@type": "Article"' in b]
    assert len(artigos) == 1, f"{caminho.name}: esperava 1 bloco Article, encontrou {len(artigos)}"

    artigo = artigos[0]
    assert artigo["@context"] == "https://schema.org"
    assert artigo["headline"]
    assert artigo["author"]["@id"] == f"{DOMINIO}/sobre.html#nvlabs"
    assert artigo["publisher"]["@id"] == f"{DOMINIO}/sobre.html#nvlabs"
    assert re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", artigo["datePublished"])
    assert re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", artigo["dateModified"])

    rel = str(caminho.relative_to(RAIZ))
    assert artigo["mainEntityOfPage"] == _ficheiro_para_url(rel)


# ── Passo 4a: páginas órfãs ─────────────────────────────────────────────────

_RE_HREF_INTERNO = re.compile(r'href="(/[a-zA-Z0-9_\-/]*\.html)"')


def _links_internos(caminho: Path) -> set[str]:
    html = caminho.read_text(encoding="utf-8")
    return {m.group(1).lstrip("/") for m in _RE_HREF_INTERNO.finditer(html)}


def _grafo_alcancavel_a_partir_do_index() -> set[str]:
    grafo = {str(p.relative_to(RAIZ)): _links_internos(p) for p in PAGINAS}
    existentes = set(grafo)
    alcancado = {"index.html"}
    fila = deque(["index.html"])
    while fila:
        actual = fila.popleft()
        for destino in grafo.get(actual, set()):
            if destino in existentes and destino not in alcancado:
                alcancado.add(destino)
                fila.append(destino)
    return alcancado


_ALCANCAVEIS = _grafo_alcancavel_a_partir_do_index()

# Páginas deliberadamente sem links de entrada — mesma lista/motivo de
# EXCLUSOES_SITEMAP (404 só é atingida por URLs partidos; o simulador da
# PSU está pronto mas por publicar).
EXCLUSOES_ORFAS = set(EXCLUSOES_SITEMAP)


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_pagina_publica_nao_e_orfa(caminho):
    rel = str(caminho.relative_to(RAIZ))
    if rel in EXCLUSOES_ORFAS:
        assert rel not in _ALCANCAVEIS, (
            f"{rel} está marcada como exclusão deliberada (nunca linkada) mas é alcançável — "
            "actualizar EXCLUSOES_ORFAS se isso for intencional agora"
        )
        return
    assert rel in _ALCANCAVEIS, (
        f"{rel} é uma página pública mas não é alcançável a partir de index.html "
        "seguindo apenas hrefs internos — página órfã, sem sinal de rastreio para o Google"
    )
