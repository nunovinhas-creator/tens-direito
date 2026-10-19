"""Testes de `scripts/sincronizar_faq_jsonld.py` (issue #352)."""
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "tests"))
import sincronizar_faq_jsonld as g  # noqa: E402
import test_faq_jsonld_coerencia as guarda  # noqa: E402

AUTOR = {"@id": "https://tensdireito.com/sobre.html#nvlabs"}


def _ld(bloco):
    return f'  <script type="application/ld+json">\n  {json.dumps(bloco, ensure_ascii=False)}\n  </script>\n'


def _faqpage(perguntas):
    return {
        "@context": "https://schema.org", "@type": "FAQPage",
        "author": AUTOR, "publisher": AUTOR,
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
            for q, r in perguntas
        ],
    }


HOWTO = {"@context": "https://schema.org", "@type": "HowTo", "name": "Como pedir", "step": []}


def _pagina(ld_blocos, corpo):
    return "<html><head>\n" + "".join(_ld(b) for b in ld_blocos) + "</head><body>" + corpo + "</body></html>"


def _blocos(html):
    return [json.loads(m.group(2)) for m in g.RE_BLOCO_LD.finditer(html)]


ZONA = (
    "<section class='zona-cinzenta'><h2>Dúvidas frequentes</h2>"
    "<details><summary><h3>Quem tem direito?</h3></summary><div class='resposta'>"
    "<p>Quem cumprir <strong>A</strong> e <a href='/x'>B</a>.</p>"
    "<p class='fonte-inline'>Fonte: x · Verificado a 1/01/2026</p></div></details>"
    "</section>"
)


@pytest.mark.parametrize("corpo, esperado", [
    (ZONA, [("Quem tem direito?", "Quem cumprir A e B. Fonte: x · Verificado a 1/01/2026")]),
    ("<main><details class='zona-cinzenta'><summary>Demora?</summary><p>Não.</p></details></main>",
     [("Demora?", "Não.")]),
    ("<section class='faq-section'><h2>Perguntas frequentes</h2><details><summary>Vinculativo?</summary>"
     "<div class='faq-resposta'>Não é.</div></details></section>", [("Vinculativo?", "Não é.")]),
    ("<section class='faq-geo'><h2>Perguntas frequentes</h2><div class='faq-item'><h3>Quanto?</h3>"
     "<p>Até 20 €.</p></div></section>", [("Quanto?", "Até 20 €.")]),
])
def test_le_os_padroes_em_uso(corpo, esperado):
    assert g.faq_visivel(_pagina([], corpo)) == esperado


def test_erros_comuns_e_navegacao_nunca_sao_faq():
    corpo = (
        "<nav class='nav-wrap'><div class='zona-cinzenta'><details><summary>📋 Apoios</summary>x</details></div></nav>"
        "<section class='zona-cinzenta'><h2>Erros comuns</h2><details><summary>Pensar que é automático</summary>"
        "<p>Não é.</p></details></section>"
    )
    assert g.faq_visivel(_pagina([], corpo)) == []


def test_reescreve_so_o_mainentity_e_mantem_author_publisher_e_howto():
    html = _pagina([_faqpage([("Pergunta velha?", "Texto velho.")]), HOWTO], ZONA)
    faq, howto = _blocos(g.sincronizar(html))
    assert faq["author"] == AUTOR and faq["publisher"] == AUTOR and faq["@context"] == "https://schema.org"
    assert [q["name"] for q in faq["mainEntity"]] == ["Quem tem direito?"]
    assert faq["mainEntity"][0]["acceptedAnswer"]["text"] == "Quem cumprir A e B. Fonte: x · Verificado a 1/01/2026"
    assert howto == HOWTO


def test_resposta_sem_html_e_com_a_fonte_inline_no_fim():
    faq, = _blocos(g.sincronizar(_pagina([_faqpage([])], ZONA)))
    texto = faq["mainEntity"][0]["acceptedAnswer"]["text"]
    assert "<" not in texto and texto.endswith("Fonte: x · Verificado a 1/01/2026")


def test_duas_seccoes_de_faq_entram_ambas_sem_repetidos():
    corpo = ZONA + (
        "<section class='faq-geo'><h2>Perguntas frequentes</h2>"
        "<div class='faq-item'><h3>Quanto?</h3><p>Até 20 €.</p></div>"
        "<div class='faq-item'><h3>Quem tem direito?</h3><p>Repetida.</p></div></section>"
    )
    faq, = _blocos(g.sincronizar(_pagina([_faqpage([])], corpo)))
    assert [q["name"] for q in faq["mainEntity"]] == ["Quem tem direito?", "Quanto?"]


def test_sem_faq_visivel_sai_o_faqpage_e_fica_o_resto():
    html = _pagina([_faqpage([("Só no JSON-LD?", "Sim.")]), HOWTO], "<p>Sem FAQ.</p>")
    assert _blocos(g.sincronizar(html)) == [HOWTO]


def test_faqpage_dentro_de_lista_tambem_e_tratado():
    html = _pagina([[_faqpage([("Velha?", "x")]), HOWTO]], ZONA)
    lista, = _blocos(g.sincronizar(html))
    assert lista[1] == HOWTO
    assert [q["name"] for q in lista[0]["mainEntity"]] == ["Quem tem direito?"]


def test_pagina_ja_sincronizada_fica_byte_a_byte_igual():
    html = _pagina([_faqpage([("Quem tem direito?", "Quem cumprir A e B. Fonte: x · Verificado a 1/01/2026")])], ZONA)
    assert g.sincronizar(html) == html


def test_check_falha_quando_algo_mudaria(tmp_path, monkeypatch):
    p = tmp_path / "pagina.html"
    p.write_text(_pagina([_faqpage([("Velha?", "x")])], ZONA), encoding="utf-8")
    monkeypatch.setattr(g, "RAIZ", tmp_path)
    assert g.main(["--check", "pagina.html"]) == 1
    assert g.main(["--write", "pagina.html"]) == 0
    assert g.main(["--check", "pagina.html"]) == 0


# ---------- sobre as páginas reais ----------

PAGINAS = g.paginas_com_faq()


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.relative_to(RAIZ).as_posix())
def test_real_idempotente_e_json_valido(pagina):
    uma = g.sincronizar(pagina.read_text(encoding="utf-8"))
    assert g.sincronizar(uma) == uma
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', uma):
        json.loads(m.group(1))


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.relative_to(RAIZ).as_posix())
def test_real_depois_de_gerar_a_guarda_nao_ve_divergencias(pagina):
    """O gerador e o teste de guarda lêem a mesma FAQ visível."""
    assert guarda.divergencias_da_pagina(g.sincronizar(pagina.read_text(encoding="utf-8"))) == set()
