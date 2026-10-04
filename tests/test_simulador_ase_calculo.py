"""
Testes da mecânica de cálculo do simulador de Ação Social Escolar (ASE)
(simulador-ase.html), executados num browser real (Chromium headless
via Playwright) — extrai o JS inline directamente do HTML real, nunca
uma cópia à parte (mesma filosofia de test_simulador_csi_calculo.py).

Os valores de CONFIG usados aqui SÃO os valores de produção (Despacho
n.º 8452-A/2015 + 5296/2017) — já fact-checked e publicados em
acao-social-escolar.html (verificado 04/10/2026). Desde a issue #295 o
escalão vem do escalão do abono de família (1.º → A, 2.º → B, 3.º ou
superior → sem auxílios), nunca de um rendimento por pessoa.

Inclui uma regressão dedicada ao bug real encontrado nesta sessão: o
simulador afirmava que o escalão B tinha transporte GRATUITO — a fonte
já fact-checked (acao-social-escolar.html) diz que só o escalão A é
gratuito, o B tem apenas desconto.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-ase.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-ase.html")


CALCULO_JS = _extrair_script_inline("function calcularASEValor")


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
        "([config, entrada]) => calcularASEValor(config, entrada)",
        [pagina.evaluate("CONFIG"), input_],
    )


# ── Issue #295: escalão ASE = escalão do abono (Despacho n.º 8452-A/2015) ──
@pytest.mark.parametrize("abono,esperado", [
    ("1", "a"),
    ("2", "b"),
    ("3_ou_superior", "sem_auxilios"),
    ("nao_sei", "nao_sei"),
])
def test_escalao_ase_e_o_escalao_do_abono(pagina, abono, esperado):
    r = _calcular(pagina, {"escalaoAbono": abono, "tipoEscola": "publica"})
    assert r == {"escalao": esperado}


def test_valor_desconhecido_nunca_inventa_escalao(pagina):
    r = _calcular(pagina, {"escalaoAbono": "", "tipoEscola": "publica"})
    assert r["escalao"] == "nao_sei"


def test_select_do_formulario_bate_com_a_correspondencia():
    opcoes = re.findall(r'<option value="([^"]+)">', SIMULADOR_HTML.split('id="escalaoAbono"')[1].split("</select>")[0])
    assert opcoes == ["1", "2", "3_ou_superior", "nao_sei"]


def test_simulador_nunca_pede_rendimento_nem_pessoas():
    assert 'id="rendimento"' not in SIMULADOR_HTML
    assert 'id="numPessoas"' not in SIMULADOR_HTML


# ── Escola privada sem protocolo — nunca calcula escalão ────────────────────
def test_escola_privada_sem_protocolo_fica_sem_escalao(pagina):
    r = _calcular(pagina, {"escalaoAbono": "1", "tipoEscola": "privada"})
    assert r["escalao"] == "privada"


# ── Regressão: transporte do escalão B nunca é "gratuito" ───────────────────
def test_cobertura_escalao_b_transporte_nao_e_gratuito(pagina):
    config = pagina.evaluate("CONFIG")
    valor_transporte_b = config["cobertura"]["b"]["transportes"]["valor"].lower()
    assert "gratuit" not in valor_transporte_b, (
        "Bug real desta sessão: só o escalão A tem transporte gratuito — "
        "o B tem desconto, confirmado em acao-social-escolar.html"
    )
    assert config["cobertura"]["a"]["transportes"]["valor"].lower() == "gratuito"


# ── Sanidade — nenhum campo de CONFIG a null ─────────────────────────────────
def test_config_producao_sem_nenhum_campo_null(pagina):
    config = pagina.evaluate("CONFIG")
    assert config["escalaoPorAbono"] == {"1": "a", "2": "b", "3_ou_superior": "sem_auxilios"}
    for escalao in ("a", "b"):
        for chave, item in config["cobertura"][escalao].items():
            assert item["valor"] is not None, f"cobertura {escalao}.{chave}.valor é null"
