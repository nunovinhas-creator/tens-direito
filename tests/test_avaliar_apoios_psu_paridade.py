"""
Paridade entre a fórmula `psu_valor_positivo` do motor de condições
(assets/js/calc-apoios.js, PR 10 da série "simulador universal") e a
mecânica de cálculo real do simulador da PSU (simulador-psu.html).

A fórmula da PSU existe em dois sítios — o simulador (que calcula o valor) e
o motor de condições (que só decide se há direito). Duplicar uma fórmula
legal é o tipo de coisa que diverge em silêncio quando um dos lados muda;
este teste torna essa divergência impossível de passar despercebida:
percorre uma grelha de agregados e exige que "o simulador dá valor > 0" e
"o motor diz elegivel" coincidam em todos os casos. Ambos os lados correm o
JS real, com os parâmetros reais de dados/parametros.json.

Se o Chromium do Playwright não estiver disponível, o módulo é ignorado.
"""
import glob
import json
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
CALC_APOIOS_JS = (RAIZ / "assets" / "js" / "calc-apoios.js").read_text(encoding="utf-8")
SIMULADOR_HTML = (RAIZ / "simulador-psu.html").read_text(encoding="utf-8")
CONDICOES_JSON = RAIZ / "dados" / "condicoes.json"
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-psu.html")


CALCULO_SIMULADOR_JS = _extrair_script_inline("function calcularPSU")


def _localizar_chromium():
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


def _parametros_do_simulador() -> dict:
    """Constrói os parâmetros exactamente como carregarParametrosPSU() o faz."""
    psu = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))["prestacoes"]["psu"]
    ias = psu["ias_2026"]["valor"]
    return {
        "valorReferencia": psu["valor_referencia_multiplicador_ias"]["valor"] * ias,
        "teto": psu["teto_maximo_multiplicador_ias"]["valor"] * ias,
        "valorMinimo": psu["valor_minimo_euros"]["valor"],
        "ponderacaoTitular": psu["ponderacao_titular"]["valor"],
        "ponderacaoMaior": psu["ponderacao_maior"]["valor"],
        "ponderacaoMenor": psu["ponderacao_menor"]["valor"],
        "citLimiar": psu["cit_limiar_multiplicador_ias"]["valor"] * ias,
        "citTaxaAcimaLimiar": psu["cit_taxa_acima_limiar"]["valor"],
        "dataProducaoEfeitos": psu["data_producao_efeitos"]["valor"],
        "art17Habitacao": {"pronto": False},
    }


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_SIMULADOR_JS)
        page.add_script_tag(content=CALC_APOIOS_JS)
        yield page
        browser.close()


def test_motor_de_condicoes_coincide_com_o_simulador_da_psu_numa_grelha_de_agregados(pagina):
    if not CONDICOES_JSON.exists():
        pytest.skip("dados/condicoes.json não gerado neste checkout")
    condicoes = json.loads(CONDICOES_JSON.read_text(encoding="utf-8"))
    formula = next(c for c in condicoes["apoios"]["psu"]["condicoes"] if c.get("tipo") == "formula")

    divergencias = pagina.evaluate(
        """([params, formula]) => {
          const divergencias = [];
          let total = 0;
          for (const adicionais of [0, 1, 2, 3]) {
            for (const menores of [0, 1, 2, 3]) {
              for (const trabalho of [0, 50, 107, 108, 200, 300, 500, 800, 1200, 2000]) {
                for (const outros of [0, 10, 50, 150, 300, 600, 1000]) {
                  total += 1;
                  const sim = calcularPSU(params, {
                    numAdultos: 1 + adicionais, numMenores: menores,
                    rendimentoTrabalho: trabalho, outrosRendimentos: outros,
                    majoracao: 'nenhuma', beneficiarioMajoracao: 'titular',
                    recebeApoioHabitacao: false, rendaPagaHabitacao: 0,
                  });
                  const motor = avaliarCondicao(formula, {
                    rendimento_trabalho_mensal_agregado: trabalho,
                    outros_rendimentos_mensais_agregado: outros,
                    numero_adultos_adicionais_agregado: adicionais,
                    numero_menores_agregado: menores,
                  }, '2026-09-27');
                  const simDizElegivel = sim.valor > 0;
                  const motorDizElegivel = motor.estado === 'elegivel';
                  if (simDizElegivel !== motorDizElegivel) {
                    divergencias.push({ adicionais, menores, trabalho, outros, simValor: sim.valor, motor: motor.estado });
                  }
                }
              }
            }
          }
          return { total, divergencias };
        }""",
        [_parametros_do_simulador(), formula],
    )

    assert divergencias["total"] == 4 * 4 * 10 * 7
    assert divergencias["divergencias"] == [], (
        "O motor de condições e o simulador da PSU divergem — a fórmula foi alterada num dos lados: "
        f"{divergencias['divergencias'][:5]}"
    )
