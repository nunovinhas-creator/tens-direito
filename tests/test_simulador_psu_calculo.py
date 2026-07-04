"""
Testes da mecânica de cálculo do simulador da PSU (simulador-psu.html),
executados num browser real (Chromium headless via Playwright) — extrai
o JS inline directamente do HTML real, nunca uma cópia à parte (mesma
filosofia de test_pesquisa_hero.py/test_pesquisa_ranking.py).

Todos os parâmetros usados aqui são FICTÍCIOS, criados só para validar
a mecânica da fórmula (adultos equivalentes, redução gradual da CIT,
limite de 50%, agregados de vários tamanhos) — nunca confundir com os
valores de PARAMETROS_PSU do ficheiro real, que são todos `null` até
ao decreto-lei (ver CLAUDE.md "IMPACTO DA PSU").

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-psu.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-psu.html")


CALCULO_JS = _extrair_script_inline("function calcularPSU")

# Parâmetros fictícios de teste — nunca reais. Valores redondos e
# artificiais escolhidos só para tornar as contas fáceis de verificar
# à mão (RSI e IAS reais nunca são exactamente 200/100).
PARAMS_FIXTURE_TESTE = {
    "valorReferencia": {"valor": 200, "fonte": "fixture de teste", "verificado_em": None},
    "valorMaximo": {"valor": 500, "fonte": "fixture de teste", "verificado_em": None},
    "coeficienteCIT": {"valor": 1, "min": 0.5, "max": 1, "fonte": "fixture de teste", "verificado_em": None},
    "majoracaoParentalidade": {"valor": 50, "fonte": "fixture de teste", "verificado_em": None},
    "adultosEquivalentes": {"requerente": 1, "outroAdulto": 0.5, "menorAte25": 0.5, "fonte": "fixture de teste", "verificado_em": None},
    "limitePatrimonio": {"multiplicadorIAS": 60, "fonte": "fixture de teste", "verificado_em": None},
}


def _localizar_chromium():
    """Procura o binário do Chromium em todas as localizações plausíveis —
    nunca assumir uma única convenção. `/opt/pw-browsers` é específico do
    sandbox do Claude Code; o CI (GitHub Actions) nunca define
    `PLAYWRIGHT_BROWSERS_PATH` e `playwright install` instala no cache
    por omissão (`~/.cache/ms-playwright`) — sem este segundo candidato,
    os testes ficavam sempre skipped no CI (achado real, 2026-07-05)."""
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


def _calcular(pagina, params, entrada):
    return pagina.evaluate(
        "([params, entrada]) => calcularPSU(params, entrada)",
        [params, entrada],
    )


# ── Estado de produção: nunca calcula com os valores reais (todos null) ────
def test_parametros_producao_ficam_sempre_em_aguarda_decreto(pagina):
    parametros_producao = pagina.evaluate("PARAMETROS_PSU")
    resultado = _calcular(pagina, parametros_producao, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "desempregado_apto", "temFilhos": False,
    })
    assert resultado["estado"] == "AGUARDA_DECRETO"
    assert "valor" not in resultado


def test_fixture_com_valor_referencia_null_fica_em_aguarda_decreto(pagina):
    params = dict(PARAMS_FIXTURE_TESTE)
    params["valorReferencia"] = {"valor": None, "fonte": "x", "verificado_em": None}
    resultado = _calcular(pagina, params, {"numAdultos": 1, "numMenoresAte25": 0})
    assert resultado["estado"] == "AGUARDA_DECRETO"


# ── Adultos equivalentes — agregados de vários tamanhos ─────────────────────
def test_adultos_equivalentes_pessoa_sozinha(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    assert resultado["adultosEquivalentes"] == 1


def test_adultos_equivalentes_casal_sem_filhos(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 2, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    # 1 (requerente) + 0.5 (outro adulto) = 1.5
    assert resultado["adultosEquivalentes"] == 1.5


def test_adultos_equivalentes_familia_grande(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 2, "numMenoresAte25": 3, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    # 1 + 0.5 (outro adulto) + 3 * 0.5 (menores) = 3.0
    assert resultado["adultosEquivalentes"] == 3.0


# ── CIT — redução gradual, nunca abaixo de 50% do valor base ────────────────
def test_cit_sem_rendimento_proprio_e_o_valor_base_completo(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "desempregado_apto", "temFilhos": False,
        "rendimentoProprioMensal": 0, "limiarReducaoCIT": 400,
    })
    # citBase = 200 * 1 = 200
    assert resultado["cit"] == 200


def test_cit_reduz_gradualmente_com_rendimento_proprio(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "desempregado_apto", "temFilhos": False,
        "rendimentoProprioMensal": 200, "limiarReducaoCIT": 400,
    })
    # fracaoRestante = max(0.5, 1 - 200/400) = max(0.5, 0.5) = 0.5 -> cit = 100
    assert resultado["cit"] == 100


def test_cit_nunca_desce_abaixo_de_50_por_cento_do_base(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "desempregado_apto", "temFilhos": False,
        # rendimento próprio muito acima do limiar — a fracaoRestante ficaria
        # negativa sem o piso de 0.5
        "rendimentoProprioMensal": 4000, "limiarReducaoCIT": 400,
    })
    assert resultado["cit"] == 100  # 50% de 200, nunca menos


def test_cit_e_zero_para_quem_ja_trabalha(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": False,
        "rendimentoProprioMensal": 0, "limiarReducaoCIT": 400,
    })
    assert resultado["cit"] == 0


# ── Majoração parentalidade ──────────────────────────────────────────────────
def test_majoracao_parentalidade_aplicada_so_com_filhos(pagina):
    com_filhos = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": True,
    })
    sem_filhos = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    assert com_filhos["majoracao"] == 50
    assert sem_filhos["majoracao"] == 0


# ── Valor final — rendimentos do agregado e limite máximo ───────────────────
def test_rendimentos_do_agregado_reduzem_o_valor_final(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 150,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    # base = 200 * 1 = 200; sem CIT nem majoração; 200 - 150 = 50
    assert resultado["valor"] == 50


def test_valor_nunca_fica_negativo(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 1, "numMenoresAte25": 0, "rendimentoAgregadoMensal": 10000,
        "situacaoLaboral": "outra", "temFilhos": False,
    })
    assert resultado["valor"] == 0


def test_valor_e_limitado_pelo_valor_maximo(pagina):
    resultado = _calcular(pagina, PARAMS_FIXTURE_TESTE, {
        "numAdultos": 2, "numMenoresAte25": 3, "rendimentoAgregadoMensal": 0,
        "situacaoLaboral": "desempregado_apto", "temFilhos": True,
        "rendimentoProprioMensal": 0, "limiarReducaoCIT": 400,
    })
    # base = 200 * 3.0 = 600; cit = 200; majoracao = 50 -> bruto = 850,
    # mas valorMaximo da fixture é 500
    assert resultado["valor"] == 500
