"""Marcadores de diploma e ano lectivo (issue #332, PR D).

`despacho`, `decreto-lei`, `lei n.º`, `diário da república`, `dre.pt` (e os
restantes de MARCADORES_SO_CITACAO) só suprimem um ano lectivo "AAAA/AAAA"
quando o par é o próprio número do diploma citado — a mesma restrição que o
PR 2 aplicou às datas. Um ano lectivo perto de um diploma, ou na ementa da
citação, deixa de ser suprimido por eles. Os outros marcadores (ex.:
"desde") continuam por proximidade no ano lectivo.

Também: o ramo do ano lectivo de `_pagina_tem_alerta` passa o tipo a
`_esta_suprimido`; sem isso, a regra só valia no auditor.
"""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import verificar_datas as v  # noqa: E402
from auditar_marcadores_historicos import supressoes_da_pagina  # noqa: E402

DIPLOMA = {
    "despacho": "Despacho n.º 8368/2024",
    "decreto-lei": "Decreto-Lei n.º 12/2024",
    r"lei\s+n\.?º": "Lei n.º 12/2024",
    "diário da república": "Diário da República n.º 45/2024",
    r"dre\.pt": "dre.pt",
}


def _primeira(html, texto):
    m = re.search(re.escape(texto), html)
    assert m, texto
    return m


@pytest.mark.parametrize("marcador", sorted(DIPLOMA))
def test_ano_letivo_perto_de_diploma_deixa_de_ser_suprimido(marcador):
    html = f"<p>Fonte: {DIPLOMA[marcador]} — calendário escolar 2025/2026.</p>"
    m = _primeira(html, "2025/2026")
    janela = v._janela_contexto(html, m.start(), m.end())
    assert re.search(marcador, janela, re.IGNORECASE), "teste vácuo: marcador fora da janela"
    assert not v.marcador_historico_aplica(marcador, janela, html, m.start(), "ano_letivo", m.end())
    assert not v._esta_suprimido(html, m.start(), m.end(), 2027, 6, tipo="ano_letivo")


def test_ano_letivo_que_e_o_numero_do_diploma_continua_suprimido():
    html = "<p>Ver o Despacho n.º 2025/2026 para o regime.</p>"
    m = _primeira(html, "2025/2026")
    assert v._esta_suprimido(html, m.start(), m.end(), 2027, 6, tipo="ano_letivo")
    assert v.detectar_alertas(html, "x.html", 2027, 6) is None


def test_numero_de_outro_diploma_nao_e_suprimido_pelo_marcador_errado():
    html = "<p>Portaria n.º 2025/2026, ver também o despacho anual.</p>"
    m = _primeira(html, "2025/2026")
    janela = v._janela_contexto(html, m.start(), m.end())
    assert not v.marcador_historico_aplica("despacho", janela, html, m.start(), "ano_letivo", m.end())
    assert v.marcador_historico_aplica("portaria", janela, html, m.start(), "ano_letivo", m.end())


def test_desde_continua_a_suprimir_ano_letivo_por_proximidade():
    html = "<p>Desde 2016/2017 os manuais são gratuitos.</p>"
    m = _primeira(html, "2016/2017")
    assert v._esta_suprimido(html, m.start(), m.end(), 2027, 6, tipo="ano_letivo")


def test_pagina_tem_alerta_aplica_a_regra_em_producao():
    """O ramo do ano lectivo passa o tipo: sem ele a regra só valia no
    auditor e a página continuava sem alerta."""
    html = "<p>Despacho n.º 8368/2024 — calendário escolar 2025/2026.</p>"
    alerta = v.detectar_alertas(html, "x.html", 2027, 6)
    assert alerta is not None and alerta["tipo"] == "ano_letivo"


def test_auditor_nao_atribui_marcador_de_diploma_a_ano_letivo_vizinho():
    html = "<html><body><p>Despacho n.º 8368/2024 — calendário escolar 2025/2026.</p></body></html>"
    registos = supressoes_da_pagina(html, "x.html", 2027)
    assert not [r for r in registos if r["tipo"] == "ano_letivo"]


@pytest.mark.parametrize("pagina,par", [
    ("simulador-ase.html", "2026/2027"),
    ("calendario-escolar-apoios.html", "2026/2027"),
    ("bolsa-de-estudo-ensino-superior.html", "2025/2026"),
])
def test_paginas_reais_passam_a_alertar_ano_letivo_em_junho_de_2027(pagina, par):
    """Antes do PR D estes pares eram «explicados» por um despacho ou
    decreto-lei por perto e a página não alertava em junho de 2027."""
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    assert par in html
    pad = next(p for p in v.PADROES if p["tipo"] == "ano_letivo")
    assert v._pagina_tem_alerta(html, pad, 2027, 6, pagina=pagina)
