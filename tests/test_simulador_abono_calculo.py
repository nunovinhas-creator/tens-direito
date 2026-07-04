"""
Testes da mecânica de cálculo do simulador de Abono de Família
(simulador-abono.html), executados num browser real (Chromium headless
via Playwright) — extrai o JS inline directamente do HTML real, nunca
uma cópia à parte (mesma filosofia de test_simulador_csi_calculo.py).

Os valores de CONFIG usados aqui SÃO os valores de produção (Portaria
n.º 60/2026/1) — já fact-checked e publicados em abono-de-familia.html
(verificado 24/06/2026), por isso os casos de teste são calculados à
mão a partir da mesma tabela/exemplos já publicados nesse artigo (ex.:
o caso 2 replica literalmente o exemplo "190,98 × 1,5 = 286,47 €/mês"
do próprio artigo).

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-abono.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-abono.html")


CALCULO_JS = _extrair_script_inline("function calcularAbonoValor")


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


def _calcular(pagina, input_):
    return pagina.evaluate(
        "([config, entrada]) => calcularAbonoValor(config, entrada)",
        [pagina.evaluate("CONFIG"), input_],
    )


# ── Caso base — 1.º escalão, bebé até 36 meses ──────────────────────────────
def test_bebe_1_escalao_recebe_valor_base(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 3000, "numCriancas": 1, "idadesMeses": [24], "monoparental": False,
    })
    assert r["escalao"] == 1
    assert r["valorTotal"] == 190.98
    assert r["garantiaAplicada"] is False


# ── Exemplo literal já publicado em abono-de-familia.html ───────────────────
def test_majoracao_monoparental_replica_exemplo_publicado(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 3000, "numCriancas": 1, "idadesMeses": [24], "monoparental": True,
    })
    assert r["majoracao"] == 95.49
    assert round(r["valorTotal"], 2) == 286.47


# ── Garantia para a Infância — piso mínimo no 1.º escalão ───────────────────
def test_garantia_infancia_aplicada_quando_valor_base_e_baixo(pagina):
    # 3 crianças com > 72 meses no 1.º escalão: valor base = 75,13 × 3 = 225,39;
    # mínimo da garantia = 127,33 × 3 = 381,99 > valor base -> garantia aplica-se.
    r = _calcular(pagina, {
        "rendimentoAnual": 2000, "numCriancas": 3, "idadesMeses": [100, 100, 100], "monoparental": False,
    })
    assert r["escalao"] == 1
    assert r["garantiaAplicada"] is True
    assert round(r["valorTotal"], 2) == 381.99


def test_garantia_infancia_nao_aplicada_quando_valor_base_ja_e_maior(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 3000, "numCriancas": 1, "idadesMeses": [24], "monoparental": False,
    })
    assert r["garantiaAplicada"] is False


# ── Fronteira exacta do 1.º escalão ──────────────────────────────────────────
def test_rr_exactamente_no_limite_do_1_escalao(pagina):
    # RR = 3657.50 / (1+1) = ... rendimento = 7315.00 -> RR = 3657.50 (== limite)
    r = _calcular(pagina, {
        "rendimentoAnual": 7315.00, "numCriancas": 1, "idadesMeses": [24], "monoparental": False,
    })
    assert r["escalao"] == 1


# ── 4.º escalão, criança > 72 meses: sem direito nessa faixa etária ─────────
def test_quarto_escalao_crianca_acima_72_meses_recebe_zero(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 30000, "numCriancas": 1, "idadesMeses": [100], "monoparental": False,
    })
    assert r["escalao"] == 4
    assert r["valorTotal"] == 0


# ── 3.º escalão, duas crianças com idades em faixas diferentes ──────────────
def test_terceiro_escalao_duas_criancas_idades_diferentes(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 30000, "numCriancas": 2, "idadesMeses": [24, 80], "monoparental": False,
    })
    assert r["escalao"] == 3
    assert round(r["valorTotal"], 2) == 186.42


# ── Acima do limite máximo — 5.º escalão, sem direito ───────────────────────
def test_rendimento_muito_acima_fica_no_5_escalao_sem_direito(pagina):
    r = _calcular(pagina, {
        "rendimentoAnual": 200000, "numCriancas": 1, "idadesMeses": [24], "monoparental": False,
    })
    assert r["escalao"] == 5
    assert r["valorTotal"] == 0


# ── Sanidade — nenhum campo de CONFIG a null (simulador activo, não PSU) ────
def test_config_producao_sem_nenhum_campo_null(pagina):
    config = pagina.evaluate("CONFIG")
    assert config["ias2026"] is not None
    assert config["garantiaInfancia"] is not None
    assert config["limiteGarantia"] is not None
    for escalao in config["escaloes"]:
        assert escalao["limite"] is not None
        for chave, valor in escalao["valores"].items():
            assert valor is not None, f"escalão {escalao['id']} campo {chave} é null"
