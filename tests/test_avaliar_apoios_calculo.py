"""
Testes da mecânica de avaliação do motor de apoios (avaliarApoios,
assets/js/calc-apoios.js), executados num browser real (Chromium headless
via Playwright) — mesma filosofia de test_simulador_csi_calculo.py /
test_simulador_abono_calculo.py: o JS real, nunca uma cópia à parte.

PR 3 da série "simulador universal". Os casos-âncora usam o CSI real
(dados/condicoes/csi.yaml compilado em dados/condicoes.json pelo PR 2) —
não uma fixture sintética — para que uma regressão no schema real do CSI
apareça aqui, não só no gerar_condicoes_json.py. O caso do grupo `any`
aninhado (idade normal OU excepção de invalidez) e o de perguntas em
falta usam fixtures sintéticas próprias, para não depender de o CSI
continuar a ter exactamente essa forma no futuro.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import json
import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
CALC_APOIOS_JS = (RAIZ / "assets" / "js" / "calc-apoios.js").read_text(encoding="utf-8")
CONDICOES_JSON = RAIZ / "dados" / "condicoes.json"


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


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALC_APOIOS_JS)
        yield page
        browser.close()


def _avaliar(pagina, condicoes_json, respostas, hoje="2026-09-27"):
    return pagina.evaluate(
        "([condicoesJson, respostas, hoje]) => avaliarApoios(condicoesJson, respostas, hoje)",
        [condicoes_json, respostas, hoje],
    )


# ── CSI real (dados/condicoes.json de produção) ─────────────────────────────


def _condicoes_reais() -> dict:
    if not CONDICOES_JSON.exists():
        pytest.skip("dados/condicoes.json não gerado neste checkout — correr gerar_condicoes_json.py primeiro")
    return json.loads(CONDICOES_JSON.read_text(encoding="utf-8"))


def test_csi_real_elegivel_por_idade_normal(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento": "1955-01-01",  # bem acima do mínimo em 2026
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "elegivel"


def test_csi_real_inelegivel_por_idade_sem_excepcao(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento": "2000-01-01",  # jovem, sem excepção de invalidez
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
        "tem_pensao_invalidez_sem_reavaliacao": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "inelegivel"


def test_csi_real_elegivel_por_excepcao_de_invalidez_apesar_da_idade(pagina):
    # Regressão directa da correcção do PR 2: idade normal falha, mas a
    # excepção (grupo `any`) torna o apoio elegível na mesma.
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento": "2000-01-01",
        "tem_pensao_invalidez_sem_reavaliacao": "sim",
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "elegivel"


def test_csi_real_indeterminado_quando_falta_residencia(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento": "1955-01-01",
        "reside_legalmente_pt": "sim",
        # anos_residencia_pt em falta — o grupo idade_minima já resolveu
        # (elegivel por idade normal), mas o apoio como um todo ainda não.
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "indeterminado"
    assert "anos_residencia_pt" in r["csi"]["perguntasEmFalta"]


def test_csi_real_inelegivel_por_residencia_mesmo_sem_saber_a_idade(pagina):
    # Short-circuit do operador `all`: uma condição já inelegível decide
    # o apoio, mesmo que a idade nunca tenha sido perguntada — é isto que
    # evita perguntar tudo antes de poder dizer "sem direito".
    condicoes = _condicoes_reais()
    respostas = {"reside_legalmente_pt": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "inelegivel"


# ── Fixtures sintéticas — grupo `any` isolado e agregação de perguntas em falta ──


CONDICOES_SINTETICAS_ANY = {
    "apoios": {
        "teste": {
            "operador": "all",
            "condicoes": [
                {
                    "id": "grupo",
                    "operador": "any",
                    "condicoes": [
                        {
                            "id": "a",
                            "tipo": "categorica",
                            "campo": "campo_a",
                            "operador_comparacao": "eq",
                            "valor": "sim",
                        },
                        {
                            "id": "b",
                            "tipo": "categorica",
                            "campo": "campo_b",
                            "operador_comparacao": "eq",
                            "valor": "sim",
                        },
                    ],
                }
            ],
        }
    }
}


def test_grupo_any_elegivel_quando_uma_folha_cumpre_mesmo_com_a_outra_em_falta(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "sim"})
    assert r["teste"]["estado"] == "elegivel"


def test_grupo_any_indeterminado_quando_nenhuma_folha_cumpre_mas_falta_uma(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "nao"})
    assert r["teste"]["estado"] == "indeterminado"
    assert r["teste"]["perguntasEmFalta"] == ["campo_b"]


def test_grupo_any_inelegivel_quando_todas_as_folhas_respondidas_falham(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "nao", "campo_b": "nao"})
    assert r["teste"]["estado"] == "inelegivel"


def test_apoio_totalmente_indeterminado_sem_nenhuma_resposta(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {})
    assert r["teste"]["estado"] == "indeterminado"
    assert set(r["teste"]["perguntasEmFalta"]) == {"campo_a", "campo_b"}


# ── Vários apoios em simultâneo ──────────────────────────────────────────────


def test_avalia_varios_apoios_independentemente(pagina):
    condicoes = {
        "apoios": {
            "x": {
                "operador": "all",
                "condicoes": [
                    {"id": "c1", "tipo": "categorica", "campo": "f1", "operador_comparacao": "eq", "valor": "sim"}
                ],
            },
            "y": {
                "operador": "all",
                "condicoes": [
                    {"id": "c2", "tipo": "categorica", "campo": "f2", "operador_comparacao": "eq", "valor": "sim"}
                ],
            },
        }
    }
    r = _avaliar(pagina, condicoes, {"f1": "sim", "f2": "nao"})
    assert r["x"]["estado"] == "elegivel"
    assert r["y"]["estado"] == "inelegivel"
