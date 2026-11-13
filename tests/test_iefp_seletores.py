"""Selectores do iefp_desemprego confinados ao artigo (Issue #371).

Corre sobre o HTML real guardado em tests/fixtures/iefp_desemprego_real.html.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import scraper_playwright as sp  # noqa: E402

HTML = (RAIZ / "tests" / "fixtures" / "iefp_desemprego_real.html").read_text(encoding="utf-8")


def _fonte():
    return next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == "iefp_desemprego")


def _extrair():
    return sp._extrair_conteudo(HTML, _fonte()["seletores"])


def test_itens_de_lista_nao_trazem_menu_nem_rodape():
    itens = _extrair()["itens_lista"]
    menu = {"Quem Somos", "Ofertas de Emprego", "Registar Ofertas de Emprego",
            "Política de Privacidade de Dados Pessoais", "Destaques / Notícias"}
    assert itens, "sem itens de lista — o contentor do artigo mudou?"
    assert not [i for i in itens if i in menu or "Quem Somos" in i]


def test_itens_de_lista_trazem_os_passos_do_guia():
    itens = _extrair()["itens_lista"]
    assert any("90 dias" in i for i in itens)
    assert any("Requerimento do Subsídio de Desemprego" in i for i in itens)


def test_paragrafos_e_titulo_continuam_a_vir_do_artigo():
    c = _extrair()
    assert c["titulo"] == "Subsídio de desemprego"
    assert c["paragrafos"]
    assert sp._conteudo_chars(c) >= sp.MIN_CHARS_CONTEUDO


def test_sem_o_contentor_do_artigo_o_conteudo_fica_suspeito():
    html_sem_artigo = HTML.replace("journal-content-article", "outro-nome")
    c = sp._extrair_conteudo(html_sem_artigo, _fonte()["seletores"])
    assert c["itens_lista"] == [] and c["paragrafos"] == []
    assert sp._conteudo_chars(c) < sp.MIN_CHARS_CONTEUDO
