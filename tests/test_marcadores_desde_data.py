"""Marcadores «desde», isentos da produção de efeitos e citações (#332, PR B; #335).

- `desde …` / `em vigor desde` só suprimem a data que regem (logo a seguir,
  só com o dia ou «de» pelo meio); nunca «desde 1 de janeiro de AAAA».
- Os isentos da produção de efeitos só suprimem a própria data.
- `despacho`, `\\bdl\\s*n`, `diário da república` e `dre.pt` só suprimem a data
  da própria citação.
Testes de efeito com a data de execução simulada (janeiro de 2027).
"""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import verificar_datas as v  # noqa: E402


def _tipo(html, ano=2027, mes=1, pagina="x.html"):
    alerta = v.detectar_alertas(html, pagina, ano, mes)
    return alerta and alerta["tipo"]


# --- «desde» rege a data -----------------------------------------------------

@pytest.mark.parametrize("frase", [
    "<p>O decreto-lei está em vigor desde 14 de agosto de 2026.</p>",
    "<p>Obrigatório desde 16/05/2026.</p>",
    "<p>Desde 16 de maio de 2026, entrar exige um segundo código.</p>",
    "<p>Em vigor desde <strong>14 de agosto de 2026</strong>.</p>",
    "<p>Desde junho de 2023, as candidaturas são contínuas.</p>",
])
def test_data_regida_por_desde_continua_suprimida(frase):
    assert _tipo(frase) is None


@pytest.mark.parametrize("frase", [
    # colateral: o «desde» rege outra data; a do fim fica exposta
    "<p>Em vigor desde 14/08/2026 · Pagamento até 30/11/2026.</p>",
    "<p>Fechado desde 15-03-2023. Estado actual em julho de 2026.</p>",
    "<p>Em vigor desde 1 de agosto de 2026 — a recomendação é de 2 de julho de 2026.</p>",
])
def test_data_so_perto_de_um_desde_fica_exposta(frase):
    assert _tipo(frase) in ("data_mes_ano", "data_numerica")


@pytest.mark.parametrize("frase", [
    "<p>Os valores produzem efeitos desde 1 de janeiro de 2026.</p>",
    "<p>Valores reforçados desde 1.º de janeiro de 2026.</p>",
    "<p>Em vigor desde 01/01/2026.</p>",
    "<p>Em vigor desde 1/1/2026.</p>",
])
def test_desde_1_de_janeiro_nunca_e_suprimido(frase):
    assert _tipo(frase) in ("data_mes_ano", "data_numerica")


def test_restricao_so_vale_para_datas():
    # par de ano lectivo: continua a valer a proximidade
    assert _tipo("<p>Desde 2016/2017, esta regra aplica-se a todos (ver 2024/2025).</p>", 2027, 6) is None


# --- isentos da produção de efeitos -----------------------------------------

LINHA_FONTES = ("<p>Decreto-Lei n.º 166/2026 · Aprovado em CM 30/07/2026 · Publicado em DR 13/08/2026"
                " · Produção de efeitos: 31/12/2026</p>")


def _suprimida(html, data, ano=2027, mes=1):
    m = re.search(re.escape(data), html)
    d = [int(x) for x in data.split("/")]
    return v._esta_suprimido(html, m.start(), m.end(), ano, mes,
                             data_ocorrencia=v.date(d[2], d[1], d[0]), tipo="data_numerica")


def test_isento_suprime_a_propria_data():
    assert _suprimida(LINHA_FONTES, "31/12/2026")


@pytest.mark.parametrize("data", ["30/07/2026", "13/08/2026"])
def test_isento_ja_nao_suprime_as_outras_datas_da_linha(data):
    assert not _suprimida(LINHA_FONTES, data)


def test_isento_como_data_de_producao_de_efeitos_suprime_a_data_antes():
    html = "<p>O artigo 63.º fixa <strong>31 de dezembro de 2026</strong> como a data de produção de efeitos.</p>"
    assert _tipo(html) is None


def test_isento_como_data_de_producao_nao_suprime_data_mais_atras():
    html = ("<p>Publicado a 13 de agosto de 2026; o artigo 63.º fixa 31 de dezembro de 2026"
            " como a data de produção de efeitos.</p>")
    assert _tipo(html) == "data_mes_ano"


# --- despacho, DL, Diário da República, dre.pt: só a data da citação -------

@pytest.mark.parametrize("frase", [
    "<p>Despacho n.º 8452-A/2015, de 22 de junho de 2015.</p>",
    "<p>DL n.º 176/2003, de 2 de agosto de 2003.</p>",
    "<p>Diário da República n.º 45/2023, Série I, de 3 de março de 2023.</p>",
])
def test_data_da_propria_citacao_continua_suprimida(frase):
    assert _tipo(frase) is None


@pytest.mark.parametrize("frase", [
    "<p>O prazo terminou em março de 2025, conforme o Despacho n.º 8452-A/2015.</p>",
    "<p>Confirmado em fevereiro de 2026 (DL n.º 176/2003).</p>",
    "<p>Em fevereiro de 2026 o Governo anunciou a revogação, ainda não publicada em Diário da República.</p>",
    "<p>Fonte: dre.pt, consultado em fevereiro de 2026.</p>",
])
def test_data_perto_de_despacho_dl_dr_ou_dre_fica_exposta(frase):
    assert _tipo(frase) == "data_mes_ano"


# --- páginas reais -----------------------------------------------------------

@pytest.mark.parametrize("pagina, data", [
    ("cuidador-informal.html", "1 de janeiro de 2026"),
    ("cuidador-informal.html", "1/1/2026"),
    ("cuidador-informal.html", "01/01/2026"),
    ("caixa-geral-aposentacoes.html", "1 de janeiro de 2015"),
    ("majoracao-subsidio-desemprego.html", "1 de janeiro de 2022"),
    ("fontes.html", "1 de janeiro de 2022"),
    ("fontes.html", "1 de janeiro de 2023"),
    ("fontes.html", "1 de janeiro de 2006"),
])
def test_inicio_de_lei_a_1_de_janeiro_esta_em_datas_permanentes(pagina, data):
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    assert (pagina, data) in v.DATAS_PERMANENTES
    spans = v.spans_datas_permanentes(html, pagina)
    for m in re.finditer(r"(?:janeiro de \d{4}|\d{1,2}/\d{1,2}/\d{4})", html):
        if data.endswith(m.group(0)) and html[max(0, m.end() - len(data)):m.end()] == data:
            assert v.em_data_permanente(spans, m.start(), m.end())


@pytest.mark.parametrize("pagina", [
    "prestacao-social-para-a-inclusao.html",
    "garantia-para-a-infancia.html",
    "assistencia-familia-filhos.html",
])
def test_valores_anuais_desde_1_de_janeiro_ficam_expostos_em_2027(pagina):
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    ver = v.verificado_em_do_texto(html)
    padrao = next(p for p in v.PADROES if p["tipo"] == "data_mes_ano")
    expostas = [
        m for m in re.finditer(r"desde 1 de (janeiro de 2026)", html)
        if not v._esta_suprimido(html, m.start(1), m.end(1), 2027, 1,
                                 data_ocorrencia=v._data_da_ocorrencia(padrao, re.match(padrao["regex"], m.group(1))),
                                 verificado_em=ver, tipo="data_mes_ano")
    ]
    assert expostas, f"{pagina}: «desde 1 de janeiro de 2026» continua suprimido"
