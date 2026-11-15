"""scripts/inserir_botao_imprimir.py — todos os guias têm o botão, mais nenhuma página."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import inserir_botao_imprimir as ibi  # noqa: E402


def test_todos_os_guias_tem_o_botao():
    assert ibi.main(["--check"]) == 0


def test_so_os_guias_tem_o_botao():
    alvo = set(ibi.paginas_alvo())
    com = {
        str(p.relative_to(RAIZ))
        for p in list(RAIZ.glob("*.html")) + list(RAIZ.glob("p/*.html")) + list(RAIZ.glob("documentos/*.html"))
        if "botao-imprimir" in p.read_text(encoding="utf-8")
    }
    assert com == alvo


def test_insercao_e_idempotente():
    html = (
        "<h1>X</h1>\n<!-- partilhar:inicio -->\n<div class=\"partilhar-artigo\">\n"
        "  <button type=\"button\" class=\"botao-partilhar\" aria-label=\"Partilhar este artigo\">"
        "📤 Partilhar este artigo</button>\n</div>\n<!-- partilhar:fim -->\n"
    )
    uma = ibi.com_botao(html)
    assert uma.count("botao-imprimir") == 1
    assert ibi.com_botao(uma) == uma


def test_pagina_sem_bloco_de_partilha_nao_e_alterada():
    assert ibi.com_botao("<h1>X</h1><main></main>") is None
