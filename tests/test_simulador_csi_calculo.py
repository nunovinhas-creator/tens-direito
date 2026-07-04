"""
Testes da mecânica de cálculo do simulador do CSI (simulador-csi.html),
executados num browser real (Chromium headless via Playwright) — extrai
o JS inline directamente do HTML real, nunca uma cópia à parte (mesma
filosofia de test_simulador_psu_calculo.py/test_pesquisa_hero.py).

Os valores de PARAMETROS_CSI usados aqui SÃO os valores de produção
(8.040€/14.070€/66 anos/80%) — ao contrário do simulador da PSU, estes
já estão fact-checked e publicados (ver complemento-solidario-idosos.html,
verificado 25/06/2026), por isso não há necessidade de uma fixture
fictícia à parte: os números já são redondos o suficiente para conferir
à mão (8040/12 = 670,00 exacto).

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-csi.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-csi.html")


CALCULO_JS = _extrair_script_inline("function calcularCSI")


def _localizar_chromium():
    """Procura o binário do Chromium em todas as localizações plausíveis
    (variável de ambiente, convenção do sandbox, convenção do CI) — ver
    test_simulador_psu_calculo.py para o achado real que motivou isto."""
    bases = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH")]
    bases += ["/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")]
    for base in bases:
        if not base:
            continue
        candidatos = sorted(glob.glob(os.path.join(base, "chromium-*", "chrome-linux*", "chrome")))
        if candidatos:
            return candidatos[-1]
    return None


try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    _PLAYWRIGHT_DISPONIVEL = False

_CHROMIUM_PATH = _localizar_chromium() if _PLAYWRIGHT_DISPONIVEL else None

pytestmark = pytest.mark.skipif(
    not (_PLAYWRIGHT_DISPONIVEL and _CHROMIUM_PATH),
    reason="Playwright/Chromium não disponível neste ambiente",
)


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _calcular(pagina, entrada):
    return pagina.evaluate(
        "([params, entrada]) => calcularCSI(params, entrada)",
        [pagina.evaluate("PARAMETROS_CSI"), entrada],
    )


# ── Elegibilidade por idade ─────────────────────────────────────────────────
def test_idade_abaixo_do_minimo_fica_inelegivel(pagina):
    r = _calcular(pagina, {"idade": 65, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeElegivel"] is False


def test_idade_exactamente_no_minimo_e_elegivel(pagina):
    r = _calcular(pagina, {"idade": 66, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeElegivel"] is True


def test_idade_acima_do_minimo_e_elegivel(pagina):
    r = _calcular(pagina, {"idade": 70, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeElegivel"] is True


# ── Sem rendimentos — CSI = valor de referência completo ────────────────────
def test_sem_rendimentos_isolado_recebe_o_valor_de_referencia_completo(pagina):
    r = _calcular(pagina, {"idade": 70, "situacao": "isolado"})
    assert r["valorReferencia"] == 8040
    assert r["rendimentoConsiderado"] == 0
    assert r["csiAnual"] == 8040
    assert r["csiMensal"] == 670.0
    assert r["temDireito"] is True


def test_sem_rendimentos_casal_recebe_o_valor_de_referencia_casal(pagina):
    r = _calcular(pagina, {"idade": 70, "situacao": "casal"})
    assert r["valorReferencia"] == 14070
    assert r["csiAnual"] == 14070


# ── Exemplo real já publicado em complemento-solidario-idosos.html ─────────
def test_exemplo_pensao_5600_anuais_da_203_33_mes(pagina):
    r = _calcular(pagina, {
        "idade": 70, "situacao": "isolado",
        "pensoesRequerente": 5600, "trabalhoRequerente": 0,
    })
    assert r["csiAnual"] == 2440
    assert round(r["csiMensal"], 2) == 203.33


# ── Rendimento de trabalho conta só 80% ──────────────────────────────────────
def test_rendimento_de_trabalho_conta_apenas_80_por_cento(pagina):
    r = _calcular(pagina, {
        "idade": 70, "situacao": "isolado",
        "pensoesRequerente": 0, "trabalhoRequerente": 1000,
    })
    assert r["rendimentoConsiderado"] == 800


def test_pensoes_contam_100_por_cento(pagina):
    r = _calcular(pagina, {
        "idade": 70, "situacao": "isolado",
        "pensoesRequerente": 1000, "trabalhoRequerente": 0,
    })
    assert r["rendimentoConsiderado"] == 1000


# ── Casal — rendimentos do cônjuge somam-se ─────────────────────────────────
def test_casal_soma_rendimentos_dos_dois_membros(pagina):
    r = _calcular(pagina, {
        "idade": 70, "situacao": "casal",
        "pensoesRequerente": 6000, "pensoesConjuge": 5000,
    })
    assert r["rendimentoConsiderado"] == 11000
    assert r["csiAnual"] == 3070
    assert round(r["csiMensal"], 2) == 255.83


def test_casal_com_trabalho_dos_dois_a_80_por_cento(pagina):
    r = _calcular(pagina, {
        "idade": 70, "situacao": "casal",
        "trabalhoRequerente": 1000, "trabalhoConjuge": 1000,
    })
    assert r["rendimentoConsiderado"] == 1600


def test_rendimentos_do_conjuge_ignorados_se_isolado(pagina):
    # Regressão: se o formulário enviar pensoesConjuge por engano com
    # situacao=isolado, nunca deve entrar no cálculo.
    r = _calcular(pagina, {
        "idade": 70, "situacao": "isolado",
        "pensoesRequerente": 1000, "pensoesConjuge": 99999,
    })
    assert r["rendimentoConsiderado"] == 1000


# ── Sem direito quando o rendimento atinge/excede o valor de referência ─────
def test_rendimento_igual_ao_valor_de_referencia_fica_sem_direito(pagina):
    r = _calcular(pagina, {"idade": 70, "situacao": "isolado", "pensoesRequerente": 8040})
    assert r["csiAnual"] == 0
    assert r["temDireito"] is False


def test_rendimento_acima_do_valor_de_referencia_nunca_fica_negativo(pagina):
    r = _calcular(pagina, {"idade": 70, "situacao": "isolado", "pensoesRequerente": 50000})
    assert r["csiAnual"] == 0
    assert r["csiMensal"] == 0
    assert r["temDireito"] is False


# ── Estado de produção nunca inventa valores ────────────────────────────────
def test_parametros_producao_tem_todos_os_valores_confirmados(pagina):
    params = pagina.evaluate("PARAMETROS_CSI")
    assert params["valorReferenciaIndividual"]["valor"] == 8040
    assert params["valorReferenciaCasal"]["valor"] == 14070
    assert params["idadeMinimaAnos"]["valor"] == 66
    assert params["percentagemRendimentoTrabalho"]["valor"] == 0.8
    for chave in params:
        assert params[chave]["verificado_em"] is not None, f"{chave} sem verificado_em"
