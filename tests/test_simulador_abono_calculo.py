"""
Testes da mecânica de cálculo do simulador de Abono de Família
(simulador-abono.html), executados num browser real (Chromium headless
via Playwright) — extrai o JS inline directamente do HTML real, nunca
uma cópia à parte (mesma filosofia de test_simulador_csi_calculo.py).

Sessão "Parâmetros YAML + auditoria factual" (2026-07-19, Commit 2):
CONFIG deixou de ser um objecto JS inline — passa a ser carregado em
runtime de /dados/parametros.json (gerado de
dados/parametros/abono.yaml), mesmo padrão do CSI/subsídio de doença.
Os golden tests da mecânica pura (`calcularAbonoValor`) constroem
`config` directamente a partir de dados/parametros.json (a "nova
fonte"), nunca de um `CONFIG` global da página — a função continua
pura, testável sem depender de fetch/rede.

CORRECÇÃO REAL DA AUDITORIA (2026-07-19), contra a fonte primária — Guia
Prático 4001 do ISS, I.P., v4.80, de 30/06/2026 (PDF oficial lido pelo
Nuno): o limite de elegibilidade da Garantia para a Infância estava
calculado com o IAS do ano corrente (0,35 × 537,13€ × 14 = 2.631,94€) —
o Guia Prático fixa este cálculo sempre com o IAS de 2024 (509,26€):
0,35 × 509,26€ × 14 = 2.495,37€. Os valores mensais por escalão/idade e
os limites de RR do cenário (b) — pedidos novos em 2026 — mantêm-se
inalterados (já batiam certo com o Guia Prático desde a publicação).

Os valores usados aqui SÃO os valores de produção (Portaria n.º
60/2026/1) — já fact-checked e publicados em abono-de-familia.html, por
isso os casos de teste são calculados à mão a partir da mesma
tabela/exemplos já publicados nesse artigo (ex.: o caso 2 replica
literalmente o exemplo "190,98 × 1,5 = 286,47 €/mês" do próprio
artigo).

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import http.server
import json
import os
import re
import socket
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-abono.html").read_text(encoding="utf-8")
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
CALC_APOIOS_JS = RAIZ / "assets" / "js" / "calc-apoios.js"


# calcularAbonoValor/getEscalao/getValorPorIdade foram extraídas para
# assets/js/calc-apoios.js (script partilhado, fundação do verificador
# multi-apoio, 2026-07-27) — deixaram de viver inline em simulador-abono.html,
# por isso o JS real a testar passa a ser lido directamente do ficheiro
# partilhado, nunca uma cópia (mesma filosofia de sempre, só a fonte real
# mudou de sítio).
CALCULO_JS = CALC_APOIOS_JS.read_text(encoding="utf-8")


def _parametros_abono_de_producao() -> dict:
    """Lê dados/parametros.json (a "nova fonte") e monta o mesmo formato
    (CONFIG-like) que PARAMETROS_ABONO tinha em runtime — nunca valores
    hardcoded aqui, mesma construção feita em simulador-abono.html."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    ab = todos["prestacoes"]["abono"]
    return {
        "garantiaInfancia": ab["garantia_infancia_valor_mensal"]["valor"],
        "limiteGarantia": ab["garantia_infancia_limite_rr_anual"]["valor"],
        "majoracaoMonoparentalFracao": ab["majoracao_monoparental_fracao"]["valor"],
        "escaloes": [
            {"id": 1, "limite": ab["escalao1_limite_cenario_pedidos_novos_2026"]["valor"],
             "valores": {"a36": ab["escalao1_valor_ate_36_meses"]["valor"], "a72": ab["escalao1_valor_37_a_72_meses"]["valor"], "mais72": ab["escalao1_valor_mais_72_meses"]["valor"]},
             "cor": "escalo-1", "nome": "1.º escalão"},
            {"id": 2, "limite": ab["escalao2_limite_cenario_pedidos_novos_2026"]["valor"],
             "valores": {"a36": ab["escalao2_valor_ate_36_meses"]["valor"], "a72": ab["escalao2_valor_37_a_72_meses"]["valor"], "mais72": ab["escalao2_valor_mais_72_meses"]["valor"]},
             "cor": "escalo-2", "nome": "2.º escalão"},
            {"id": 3, "limite": ab["escalao3_limite_cenario_pedidos_novos_2026"]["valor"],
             "valores": {"a36": ab["escalao3_valor_ate_36_meses"]["valor"], "a72": ab["escalao3_valor_37_a_72_meses"]["valor"], "mais72": ab["escalao3_valor_mais_72_meses"]["valor"]},
             "cor": "escalo-3", "nome": "3.º escalão"},
            {"id": 4, "limite": ab["escalao4_limite_cenario_pedidos_novos_2026"]["valor"],
             "valores": {"a36": ab["escalao4_valor_ate_36_meses"]["valor"], "a72": ab["escalao4_valor_37_a_72_meses"]["valor"], "mais72": ab["escalao4_valor_mais_72_meses"]["valor"]},
             "cor": "escalo-4", "nome": "4.º escalão"},
            {"id": 5, "limite": float("inf"), "valores": {"a36": 0, "a72": 0, "mais72": 0}, "cor": "escalo-5", "nome": "Sem direito"},
        ],
    }


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
        [_parametros_abono_de_producao(), input_],
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
    # RR = 2000/(3+1) = 500€ — abaixo do limite corrigido (2.495,37€) e do
    # limite antigo/errado (2.631,94€), por isso este caso não distingue as
    # duas versões (ver test_limite_garantia_infancia_corrigido mais abaixo
    # para um caso que só passa com o valor corrigido).
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


# ── Correcção real da auditoria (2026-07-19): limite da Garantia ───────────
def test_limite_garantia_infancia_corrigido_2495_37_nunca_2631_94(pagina):
    # RR = 5000/(1+1) = 2.500€ — ACIMA do limite corrigido (2.495,37€),
    # mas ABAIXO do limite antigo/errado (2.631,94€). Com o valor
    # corrigido, a Garantia NÃO se aplica aqui — se este teste falhar
    # com garantiaAplicada=True, o bug do IAS do ano corrente voltou.
    r = _calcular(pagina, {
        "rendimentoAnual": 5000, "numCriancas": 1, "idadesMeses": [100], "monoparental": False,
    })
    assert r["escalao"] == 1
    assert r["rr"] == 2500.0
    assert r["garantiaAplicada"] is False
    assert round(r["valorTotal"], 2) == 75.13  # valor base do 1.º escalão, >72 meses — sem garantia


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


# ── Sanidade — nenhum campo de PARAMETROS_ABONO a null (não PSU) ────────────
def test_parametros_producao_sem_nenhum_campo_null(pagina):
    config = _parametros_abono_de_producao()
    assert config["garantiaInfancia"] is not None
    assert config["limiteGarantia"] is not None
    assert config["majoracaoMonoparentalFracao"] is not None
    for escalao in config["escaloes"]:
        assert escalao["limite"] is not None
        for chave, valor in escalao["valores"].items():
            assert valor is not None, f"escalão {escalao['id']} campo {chave} é null"


def test_parametros_producao_tem_todos_os_valores_confirmados():
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    ab = todos["prestacoes"]["abono"]
    assert ab["garantia_infancia_limite_rr_anual"]["valor"] == 2495.37
    for chave, dados in ab.items():
        assert dados["verificado_em"], f"{chave} sem verificado_em"
        assert dados["referencia_legal"], f"{chave} sem referencia_legal"
        assert dados["fonte_url"], f"{chave} sem fonte_url"


# ── Coerência artigo ↔ simulador ─────────────────────────────────────────────

def test_coerencia_artigo_simulador_garantia_infancia():
    """O limite corrigido (2.495,37€) tem de aparecer no artigo
    publicado, nunca só no simulador — e o valor antigo/errado
    (2.631,94€) nunca deve reaparecer em nenhum dos dois."""
    artigo = (RAIZ / "abono-de-familia.html").read_text(encoding="utf-8")
    assert "2.495,37" in artigo
    assert "2.495,37" in SIMULADOR_HTML
    assert "2.631,94" not in artigo
    assert "2.631,94" not in re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", SIMULADOR_HTML, flags=re.IGNORECASE)


# ── Runtime real: fetch de /dados/parametros.json (sucesso e falha) ────────
def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor():
    porta = _porta_livre()
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(RAIZ), **kw)  # noqa: E731
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{porta}"
    httpd.shutdown()
    thread.join(timeout=5)


@pytest.fixture()
def pagina_real(servidor):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        yield page, servidor
        browser.close()


def test_runtime_fetch_com_sucesso_activa_o_botao_e_calcula(pagina_real):
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-abono.html")
    page.wait_for_function("document.getElementById('btnCalcularAbono').disabled === false", timeout=5000)
    assert page.evaluate("document.getElementById('avisoParametrosErro').style.display") != "block"

    page.fill("#rendimento", "3000")
    page.select_option("#monoparental", "nao")
    page.select_option("#numCriancas", "1")
    page.fill("#idade1", "24")
    page.click("#btnCalcularAbono")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    assert "190.98" in texto  # mesmo exemplo do golden test


def test_runtime_fetch_com_falha_bloqueia_o_botao_e_nunca_calcula(pagina_real):
    page, servidor = pagina_real
    page.route("**/dados/parametros.json", lambda route: route.abort())
    page.goto(f"{servidor}/simulador-abono.html")
    page.wait_for_function(
        "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000
    )
    assert page.evaluate("document.getElementById('btnCalcularAbono').disabled") is True
    assert page.evaluate(
        "window.PARAMETROS_ABONO === null || typeof window.PARAMETROS_ABONO === 'undefined'"
    ) or page.evaluate("PARAMETROS_ABONO") is None

    page.evaluate("document.getElementById('btnCalcularAbono').removeAttribute('disabled')")
    page.fill("#rendimento", "3000")
    page.select_option("#numCriancas", "1")
    page.fill("#idade1", "24")
    page.click("#btnCalcularAbono")
    page.wait_for_timeout(300)
    assert "show" not in (page.get_attribute("#resultado", "class") or "")
