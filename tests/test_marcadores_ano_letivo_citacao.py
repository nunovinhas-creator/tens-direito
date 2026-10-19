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


# ── Data-limite e evento só na data que regem (PR D) ────────────────────────

@pytest.mark.parametrize("marcador,frase,data", [
    (r"celebrados?\s+at[ée]\b", "Só para contratos celebrados até 15 de março de 2023.", "março de 2023"),
    (r"\bposterior a\b", "Contratos de data posterior a 15 de março de 2023.", "março de 2023"),
    (r"\banterior(?:es)?\s+a\b", "Contratos anteriores a 15/03/2023.", "15/03/2023"),
    ("revisão urgente", "Pediu uma revisão urgente em agosto de 2025.", "agosto de 2025"),
])
def test_marcador_suprime_a_data_que_rege(marcador, frase, data):
    html = f"<p>{frase}</p>"
    m = _primeira(html, data)
    janela = v._janela_contexto(html, m.start(), m.end())
    assert v.marcador_historico_aplica(marcador, janela, html, m.start(), "data_mes_ano", m.end())


@pytest.mark.parametrize("marcador,frase", [
    (r"celebrados?\s+at[ée]\b",
     "Só para contratos celebrados até 15 de março de 2023. O Governo anunciou em fevereiro de 2025 a revogação."),
    (r"\bposterior a\b",
     "Contratos de data posterior a 15 de março de 2023. O Governo anunciou em fevereiro de 2025 a revogação."),
    (r"\banterior(?:es)?\s+a\b",
     "A regra vale desde a revisão, mas se a avaliação for anterior a essa data, anunciada em fevereiro de 2025, mantém-se."),
    ("revisão urgente",
     "Pediu uma revisão urgente em agosto de 2024. O Governo anunciou em fevereiro de 2025 a revogação."),
])
def test_data_so_perto_do_marcador_deixa_de_ser_suprimida(marcador, frase):
    html = f"<p>{frase}</p>"
    m = _primeira(html, "fevereiro de 2025")
    janela = v._janela_contexto(html, m.start(), m.end())
    assert re.search(marcador, janela, re.IGNORECASE), "teste vácuo"
    assert not v.marcador_historico_aplica(marcador, janela, html, m.start(), "data_mes_ano", m.end())
    alerta = v.detectar_alertas(html, "x.html", 2026, 1)
    assert alerta is not None and alerta["tipo"] == "data_mes_ano"


def test_marcadores_data_seguinte_continuam_por_proximidade_no_ano_letivo():
    html = "<p>Contratos celebrados até ao fim de 2023/2024.</p>"
    m = _primeira(html, "2023/2024")
    janela = v._janela_contexto(html, m.start(), m.end())
    assert v.marcador_historico_aplica(r"celebrados?\s+at[ée]\b", janela, html, m.start(), "ano_letivo", m.end())


@pytest.mark.parametrize("pagina,marcador,data", [
    ("p/habitacao.html", r"celebrados?\s+at[ée]\b", "fevereiro de 2026"),
    # apoio-extraordinario-renda.html («revisão urgente» + «fevereiro de 2026») saiu:
    # a frase só existia no FAQPage JSON-LD, gerado da FAQ visível desde #352.
])
def test_paginas_reais_supressoes_por_acaso_deixam_de_valer(pagina, marcador, data):
    """Só as ocorrências com o marcador na janela — as outras «fevereiro de
    2026» da página já estavam expostas antes."""
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    perto = [m for m in re.finditer(re.escape(data), html)
             if re.search(marcador, v._janela_contexto(html, m.start(), m.end()), re.IGNORECASE)]
    assert perto, "teste vácuo: nenhuma ocorrência com o marcador por perto"
    assert any(not v._esta_suprimido(html, m.start(), m.end(), 2027, 1, tipo="data_mes_ano") for m in perto)


def test_calendario_plurianual_2024_2025_e_permanente_e_2027_2028_fica_exposto():
    pagina = "calendario-escolar-apoios.html"
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    pad = next(p for p in v.PADROES if p["tipo"] == "ano_letivo")
    sem_resto = re.sub(r"\b(?!2024/2025\b|2027/2028\b)20\d{2}/20\d{2}\b", "", html)
    assert "2024/2025" in sem_resto and "2027/2028" in sem_resto
    assert not v._pagina_tem_alerta(sem_resto, pad, 2027, 6, pagina=pagina)
    assert v._pagina_tem_alerta(sem_resto, pad, 2028, 6, pagina=pagina)
