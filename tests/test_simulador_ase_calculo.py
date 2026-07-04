"""
Testes da mecânica de cálculo do simulador de Ação Social Escolar (ASE)
(simulador-ase.html), executados num browser real (Chromium headless
via Playwright) — extrai o JS inline directamente do HTML real, nunca
uma cópia à parte (mesma filosofia de test_simulador_csi_calculo.py).

Os valores de CONFIG usados aqui SÃO os valores de produção (Despacho
n.º 8452-A/2015 + 5296/2017) — já fact-checked e publicados em
acao-social-escolar.html (verificado 24/06/2026). O caso 2 replica
literalmente o exemplo de RPC ("4 pessoas e 24.000€ anuais → 500€/mês")
já publicado no FAQ da própria página.

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


# ── Escalão A ────────────────────────────────────────────────────────────────
def test_escalao_a_rpc_abaixo_do_limite(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 12000, "numPessoas": 4, "tipoEscola": "publica"})
    assert r["escalao"] == "a"
    assert round(r["rpc"], 2) == 250.0


# ── Escalão B — replica o exemplo literal do FAQ publicado ──────────────────
def test_escalao_b_replica_exemplo_do_faq(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 24000, "numPessoas": 4, "tipoEscola": "publica"})
    assert r["escalao"] == "b"
    assert round(r["rpc"], 2) == 500.0


# ── Sem direito — acima do limite do escalão B ──────────────────────────────
def test_sem_direito_acima_do_limite(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 40000, "numPessoas": 2, "tipoEscola": "publica"})
    assert r["escalao"] == "nao"


# ── Fronteiras exactas ───────────────────────────────────────────────────────
def test_rpc_exactamente_no_limite_do_escalao_a(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 268.57 * 48, "numPessoas": 4, "tipoEscola": "publica"})
    assert r["escalao"] == "a"


def test_rpc_exactamente_no_limite_do_escalao_b(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 537.13 * 48, "numPessoas": 4, "tipoEscola": "publica"})
    assert r["escalao"] == "b"


# ── Escola privada sem protocolo — nunca calcula escalão ────────────────────
def test_escola_privada_sem_protocolo_fica_sem_escalao(pagina):
    r = _calcular(pagina, {"rendimentoAnual": 5000, "numPessoas": 4, "tipoEscola": "privada"})
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
    assert config["ias2026"] is not None
    assert config["limiteEscalaoA"] is not None
    assert config["limiteEscalaoB"] is not None
    for escalao in ("a", "b"):
        for chave, item in config["cobertura"][escalao].items():
            assert item["valor"] is not None, f"cobertura {escalao}.{chave}.valor é null"
