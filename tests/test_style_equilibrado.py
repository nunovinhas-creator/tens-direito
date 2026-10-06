"""Cada <style> abre e fecha uma vez, nunca aninhado.

O HTML não aninha <style>: o primeiro </style> fecha o bloco, e o CSS que
ficar entre um </style> a mais e o seguinte aparece como texto no topo da
página (caso real: tarifa-social-energia.html, regra
".comparacao td:first-child{font-weight:600}" visível em produção).
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import encontrar_paginas, RAIZ

PAGINAS = sorted(encontrar_paginas(), key=lambda p: str(p))
_TAGS = re.compile(r"<style\b|</style\s*>", re.IGNORECASE)


def erros_style(html: str) -> list[str]:
    erros, aberto = [], False
    for m in _TAGS.finditer(html):
        linha = html.count("\n", 0, m.start()) + 1
        if m.group().lower().startswith("</"):
            if not aberto:
                erros.append(f"linha {linha}: </style> sem <style> aberto")
            aberto = False
        else:
            if aberto:
                erros.append(f"linha {linha}: <style> dentro de outro <style>")
            aberto = True
    if aberto:
        erros.append("<style> nunca fechado")
    return erros


def test_detecta_o_caso_real():
    html = "<style>\n<style>\na{}\n</style>\n.x{}\n</style>"
    assert erros_style(html) == [
        "linha 2: <style> dentro de outro <style>",
        "linha 6: </style> sem <style> aberto",
    ]


def test_aceita_blocos_separados():
    assert erros_style("<style>a{}</style><p></p><style media='print'>b{}</style>") == []


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: str(p.relative_to(RAIZ)))
def test_style_equilibrado(pagina):
    assert erros_style(pagina.read_text(encoding="utf-8")) == []
