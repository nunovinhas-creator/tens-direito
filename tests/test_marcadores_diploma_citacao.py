"""Marcadores de diploma restringidos à citação (issue #332, PR 2).

`portaria`, `decreto-lei`, `decreto\\s+lei` e `lei\\s+n\\.?º` só suprimem a
data que faz parte da própria citação ("<diploma> n.º X/AAAA, de D de mês de
AAAA"). Uma data a menos de JANELA caracteres de um diploma, mas fora da
citação, deixa de ser suprimida. `despacho` e `\\bdl\\s*n` ficam como estavam.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import verificar_datas as v  # noqa: E402


def _ocorrencias(html, texto):
    return [m for m in re.finditer(re.escape(texto), html)]


def _janela_tem(html, m, marcador):
    return re.search(marcador, v._janela_contexto(html, m.start(), m.end()), re.IGNORECASE) is not None


def test_portaria_305_2022_em_creche_gratuita_continua_suprimida():
    html = (RAIZ / "creche-gratuita.html").read_text(encoding="utf-8")
    ocorrencias = _ocorrencias(html, "22 de dezembro de 2022")
    assert len(ocorrencias) == 2, "a página deixou de citar a Portaria n.º 305/2022 duas vezes — rever este teste"
    for m in ocorrencias:
        assert v._citacao_de_diploma(html, m.start()).lower().startswith("portaria n.º 305/2022")
        assert v.marcador_historico_aplica("portaria", v._janela_contexto(html, m.start(), m.end()), html, m.start(), "prazo_outono")
        assert v._esta_suprimido(html, m.start(), m.end(), 2027, 1, tipo="prazo_outono")


def test_data_perto_de_diploma_mas_fora_da_citacao_deixa_de_ser_suprimida():
    html = ("<p>O Governo anunciou em fevereiro de 2025 que o programa vai acabar "
            "(Decreto-Lei n.º 43/2024, Portaria n.º 1/2024, Lei n.º 2/2024).</p>")
    m = _ocorrencias(html, "fevereiro de 2025")[0]
    for marcador in v.MARCADORES_SO_CITACAO[:2] + (v.MARCADORES_SO_CITACAO[3],):
        assert _janela_tem(html, m, marcador), f"teste vácuo: {marcador!r} fora da janela"
    assert not v._esta_suprimido(html, m.start(), m.end(), 2026, 1, tipo="data_mes_ano")
    alerta = v.detectar_alertas(html, "x.html", 2026, 1)
    assert alerta is not None and alerta["tipo"] == "data_mes_ano"


def test_citacao_com_data_numerica_continua_suprimida():
    html = "<p>Base legal: Portaria n.º 7-A/2024, de 05/01/2024.</p>"
    m = _ocorrencias(html, "05/01/2024")[0]
    assert v._esta_suprimido(html, m.start(), m.end(), 2026, 1, tipo="data_numerica")


def test_citacao_de_decreto_lei_suprimida_pelos_marcadores_do_proprio_diploma():
    html = "<p>Regime: Decreto-Lei n.º 91/2009, de 9 de abril de 2009. Ver também a Portaria geral.</p>"
    m = _ocorrencias(html, "9 de abril de 2009")[0]
    janela = v._janela_contexto(html, m.start(), m.end())
    assert v.marcador_historico_aplica("decreto-lei", janela, html, m.start(), "prazo_outono")
    assert v.marcador_historico_aplica(r"lei\s+n\.?º", janela, html, m.start(), "prazo_outono")
    # "Portaria" está na janela, mas a citação é de um decreto-lei
    assert re.search("portaria", janela, re.IGNORECASE)
    assert not v.marcador_historico_aplica("portaria", janela, html, m.start(), "prazo_outono")
    assert v._esta_suprimido(html, m.start(), m.end(), 2026, 1, tipo="prazo_outono")


def test_despacho_ja_nao_suprime_por_proximidade():
    # PR B do #332: despacho passou a só suprimir a data da própria citação.
    html = "<p>O prazo terminou em março de 2025, conforme o Despacho n.º 8452-A/2015.</p>"
    m = _ocorrencias(html, "março de 2025")[0]
    assert not v._esta_suprimido(html, m.start(), m.end(), 2026, 1, tipo="data_mes_ano")


def test_ano_letivo_e_valor_ias_continuam_a_ser_suprimidos_por_proximidade():
    # Não são datas de citação: a restrição só se aplica a datas.
    html = "<p>O valor de referência é IAS de 522,50 €, fixado pela Portaria n.º 42/2025/1 (2025).</p>"
    assert v.detectar_alertas(html, "x.html", 2026, 1) is None
