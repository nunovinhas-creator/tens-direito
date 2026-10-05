"""
Link "Reportar um erro nesta página" junto ao carimbo canónico "Verificado a
[data] pela redação do Tens Direito" — inserido por
`scripts/inserir_reportar_erro.py`, nunca à mão. Toda a página com carimbo
tem o link exactamente uma vez, logo a seguir à atribuição, a apontar para
/sobre.html#contacto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from inserir_reportar_erro import ANCORA_CARIMBO, BLOCO, FIM, INICIO, processar  # noqa: E402
from sincronizar_clusters import encontrar_paginas  # noqa: E402

PAGINAS = sorted(encontrar_paginas(RAIZ), key=str)
COM_CARIMBO = [p for p in PAGINAS if ANCORA_CARIMBO in p.read_text(encoding="utf-8")]


def test_ha_paginas_com_carimbo():
    assert len(COM_CARIMBO) > 50


@pytest.mark.parametrize("caminho", COM_CARIMBO, ids=[str(p.relative_to(RAIZ)) for p in COM_CARIMBO])
def test_link_reportar_erro_logo_a_seguir_ao_carimbo(caminho):
    html = caminho.read_text(encoding="utf-8")
    assert html.count(INICIO) == 1 and html.count(FIM) == 1, "link em falta ou duplicado"
    assert html.count('href="/sobre.html#contacto">Reportar um erro nesta página</a>') == 1
    assert ANCORA_CARIMBO + BLOCO in html, "o link tem de vir imediatamente a seguir ao carimbo canónico"


def test_paginas_sem_carimbo_nao_tem_o_link():
    for p in PAGINAS:
        html = p.read_text(encoding="utf-8")
        if ANCORA_CARIMBO not in html:
            assert INICIO not in html, f"{p.name}: link sem carimbo"


def test_processar_e_idempotente_e_ignora_paginas_sem_carimbo():
    base = "<p>Verificado a 01/01/2026 " + ANCORA_CARIMBO + " · Fontes</p>"
    uma = processar(base)
    assert uma == "<p>Verificado a 01/01/2026 " + ANCORA_CARIMBO + BLOCO + " · Fontes</p>"
    assert processar(uma) == uma
    antigo = uma.replace("Reportar um erro nesta página", "texto antigo")
    assert processar(antigo) == uma
    assert processar("<p>sem carimbo</p>") == "<p>sem carimbo</p>"


def test_sobre_sem_js_tem_frase_coerente():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    assert "a carregar contacto" not in html
    assert "<noscript>" not in html
    assert html.count(
        '<span class="email-ofuscado" data-user="contacto" data-dominio="tensdireito.com">'
        "contacto (arroba) tensdireito (ponto) com</span>"
    ) == 2
    assert 'id="contacto"' in html
