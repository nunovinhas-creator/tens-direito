"""noticias.html só com os últimos meses; o resto em noticias-AAAA.html."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_noticias as gn  # noqa: E402
from gerar_noticias import ItemNoticia  # noqa: E402

BASE = """<!DOCTYPE html>
<html lang="pt-PT"><head>
<meta name="robots" content="index, follow">
<title>Atualidades — Tens Direito</title>
<meta name="description" content="O que mudou.">
<meta property="og:title" content="Atualidades — Tens Direito">
<meta property="og:description" content="O que mudou.">
<meta property="og:url" content="https://tensdireito.com/noticias.html">
<link rel="canonical" href="https://tensdireito.com/noticias.html">
</head><body>
<header class="hero"><h1>Atualidades</h1>
<p>O que mudou nos apoios.</p></header>
<main>
<!-- DESTAQUE-INICIO -->
<!-- DESTAQUE-FIM -->
<div id="cards-grid">
<!-- ARQUIVO-INICIO -->
<!-- ARQUIVO-FIM -->
</div>
<!-- ARQUIVO-ANOS-INICIO -->
<!-- ARQUIVO-ANOS-FIM -->
</main></body></html>
"""


def _item(data_iso, titulo):
    return ItemNoticia(data_iso=data_iso, titulo=titulo, fonte_nome="Ex", url=f"https://ex.pt/{titulo}",
                       resumo="R", categoria="apoios", cluster_id=None)


ITENS = [
    _item("2026-11-11", "nov"), _item("2026-10-02", "out"), _item("2026-09-30", "set"),
    _item("2026-08-31", "ago"), _item("2026-06-01", "jun"), _item("2025-12-20", "dez25"),
]


def test_janela_conta_a_partir_do_item_mais_recente():
    recentes, por_ano = gn.separar_por_janela(ITENS)
    assert [i.titulo for i in recentes] == ["nov", "out", "set"]
    assert {a: [i.titulo for i in v] for a, v in por_ano.items()} == {"2026": ["ago", "jun"], "2025": ["dez25"]}


def test_cada_noticia_numa_so_pagina(tmp_path):
    principal = tmp_path / "noticias.html"
    principal.write_text(BASE, encoding="utf-8")
    gn.regenerar_noticias_html(ITENS, caminho=principal)
    paginas = {p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("noticias*.html")}
    assert set(paginas) == {"noticias.html", "noticias-2026.html", "noticias-2025.html"}
    for item in ITENS:
        com = [n for n, t in paginas.items() if f"https://ex.pt/{item.titulo}\"" in t]
        assert len(com) == 1, (item.titulo, com)
    assert "https://ex.pt/ago\"" in paginas["noticias-2026.html"]


def test_pagina_principal_liga_aos_anos(tmp_path):
    principal = tmp_path / "noticias.html"
    principal.write_text(BASE, encoding="utf-8")
    gn.regenerar_noticias_html(ITENS, caminho=principal)
    t = principal.read_text(encoding="utf-8")
    assert t.index('href="/noticias-2026.html"') < t.index('href="/noticias-2025.html"')


def test_pagina_de_ano(tmp_path):
    principal = tmp_path / "noticias.html"
    principal.write_text(BASE, encoding="utf-8")
    gn.regenerar_noticias_html(ITENS, caminho=principal)
    t = (tmp_path / "noticias-2026.html").read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex, follow">' in t
    assert "<title>Notícias de 2026 — Tens Direito</title>" in t
    assert '<link rel="canonical" href="https://tensdireito.com/noticias-2026.html">' in t
    assert "https://tensdireito.com/noticias.html" not in t
    assert "<h1>Notícias de 2026</h1>" in t
    assert 'href="/noticias.html"' in t
    assert '<strong aria-current="page">2026</strong>' in t
    assert 'href="/noticias-2025.html"' in t
    assert 'class="destaque-card"' not in t


def test_regeneracao_idempotente(tmp_path):
    principal = tmp_path / "noticias.html"
    principal.write_text(BASE, encoding="utf-8")
    assert gn.regenerar_noticias_html(ITENS, caminho=principal) is True
    antes = {p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("*.html")}
    assert gn.regenerar_noticias_html(ITENS, caminho=principal) is False
    assert antes == {p.name: p.read_text(encoding="utf-8") for p in tmp_path.glob("*.html")}


def test_sem_marcador_de_anos_falha_em_vez_de_deixar_noticias_sem_ligacao(tmp_path):
    principal = tmp_path / "noticias.html"
    principal.write_text(BASE.replace("<!-- ARQUIVO-ANOS-INICIO -->\n<!-- ARQUIVO-ANOS-FIM -->\n", ""), encoding="utf-8")
    with pytest.raises(Exception, match="ARQUIVO-ANOS"):
        gn.regenerar_noticias_html(ITENS, caminho=principal)


def test_guardrail_aceita_so_noticias_com_ano(tmp_path):
    gn.escrever_ficheiro_seguro(str(tmp_path / "noticias-2027.html"), "x")
    for nome in ("noticias-abc.html", "noticias-2027-01.html", "abono-de-familia.html"):
        with pytest.raises(Exception, match="BLOQUEADO"):
            gn.escrever_ficheiro_seguro(str(tmp_path / nome), "x")


def test_ficheiros_reais_sincronizados_com_o_json():
    """noticias.html e noticias-AAAA.html reais = o que o gerador produz a
    partir de data/noticias.json (sem contar a sanitização do pipeline)."""
    itens = gn.carregar_itens(gn.NOTICIAS_JSON)
    recentes, por_ano = gn.separar_por_janela(itens)
    principal = (RAIZ / "noticias.html").read_text(encoding="utf-8")
    assert "<!-- ARQUIVO-ANOS-INICIO -->" in principal
    for ano, itens_ano in por_ano.items():
        assert f'href="/noticias-{ano}.html"' in principal
        pagina = RAIZ / f"noticias-{ano}.html"
        assert pagina.exists(), f"falta {pagina.name} — correr gerar_noticias.py --sync"
        assert pagina.read_text(encoding="utf-8").count('class="arquivo-card"') == len(itens_ano)
    assert principal.count('class="arquivo-card"') == len(recentes) - 1
