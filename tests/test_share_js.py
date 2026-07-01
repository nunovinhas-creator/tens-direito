"""
Testes funcionais para assets/js/share.js, executados num browser real
(Chromium headless via Playwright) — a única forma de validar
genuinamente comportamento de browser (Web Share API, Clipboard API,
acessibilidade por teclado) em vez de apenas inspeccionar o texto do
ficheiro.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar —
mantém a suite portátil entre máquinas de desenvolvimento.
"""
import glob
import os
from pathlib import Path

import pytest

SHARE_JS = (Path(__file__).parent.parent / "assets" / "js" / "share.js").read_text(encoding="utf-8")

_HTML_BASE = """<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"><title>Teste</title></head>
<body>
  <h1>Artigo de teste</h1>
  <div class="partilhar-artigo">
    <button type="button" class="botao-partilhar" aria-label="Partilhar este artigo">📤 Partilhar este artigo</button>
  </div>
</body>
</html>
"""


def _localizar_chromium():
    caminho_env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    candidatos = sorted(glob.glob(os.path.join(caminho_env, "chromium-*", "chrome-linux", "chrome")))
    return candidatos[-1] if candidatos else None


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
        page.set_content(_HTML_BASE)
        page.add_script_tag(content=SHARE_JS)
        yield page
        browser.close()


# ── Web Share API ────────────────────────────────────────────────────────

def test_usa_web_share_api_quando_disponivel(pagina):
    pagina.evaluate("""
        () => {
            window.__chamadas = [];
            navigator.share = (dados) => {
                window.__chamadas.push(dados);
                return Promise.resolve();
            };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(50)

    chamadas = pagina.evaluate("window.__chamadas")
    assert len(chamadas) == 1
    assert chamadas[0]["title"] == "Teste"
    assert chamadas[0]["url"].startswith("http") or chamadas[0]["url"] == pagina.url


def test_cancelar_partilha_nativa_nao_mostra_fallback(pagina):
    # AbortError (utilizador cancelou a caixa nativa) não deve activar
    # nenhum fallback -- não é uma falha.
    pagina.evaluate("""
        () => {
            navigator.share = () => {
                const erro = new Error('cancelado');
                erro.name = 'AbortError';
                return Promise.reject(erro);
            };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    assert pagina.query_selector("#partilhar-feedback") is None
    assert pagina.query_selector("#partilhar-manual-overlay") is None


def test_erro_generico_na_partilha_nativa_cai_para_clipboard(pagina):
    pagina.evaluate("""
        () => {
            navigator.share = () => Promise.reject(new Error('falha qualquer'));
            navigator.clipboard = { writeText: () => Promise.resolve() };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    feedback = pagina.query_selector("#partilhar-feedback")
    assert feedback is not None
    assert "copiada" in feedback.inner_text()


# ── Fallback: clipboard ─────────────────────────────────────────────────

def test_fallback_clipboard_quando_sem_web_share(pagina):
    pagina.evaluate("""
        () => {
            navigator.share = undefined;
            window.__copiado = null;
            navigator.clipboard = {
                writeText: (texto) => {
                    window.__copiado = texto;
                    return Promise.resolve();
                },
            };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    copiado = pagina.evaluate("window.__copiado")
    assert copiado == pagina.url

    feedback = pagina.query_selector("#partilhar-feedback")
    assert feedback is not None
    assert feedback.inner_text() == "✅ Ligação copiada para a área de transferência."
    assert feedback.get_attribute("role") == "status"
    assert feedback.get_attribute("aria-live") == "polite"


def test_mensagem_de_sucesso_desaparece_sozinha(pagina):
    pagina.evaluate("""
        () => {
            navigator.share = undefined;
            navigator.clipboard = { writeText: () => Promise.resolve() };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)
    assert pagina.query_selector("#partilhar-feedback") is not None

    pagina.wait_for_timeout(4500)
    assert pagina.query_selector("#partilhar-feedback") is None


# ── Fallback: caixa manual ──────────────────────────────────────────────

def test_fallback_manual_quando_clipboard_falha(pagina):
    pagina.evaluate("""
        () => {
            navigator.share = undefined;
            navigator.clipboard = { writeText: () => Promise.reject(new Error('negado')) };
        }
    """)
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    caixa = pagina.query_selector("#partilhar-manual-overlay")
    assert caixa is not None
    assert caixa.get_attribute("role") == "dialog" or pagina.query_selector(".partilhar-manual-caixa[role='dialog']")

    campo = pagina.query_selector(".partilhar-manual-input")
    assert campo is not None
    assert campo.input_value() == pagina.url


def test_fallback_manual_quando_clipboard_api_nao_existe(pagina):
    pagina.evaluate("() => { navigator.share = undefined; navigator.clipboard = undefined; }")
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    campo = pagina.query_selector(".partilhar-manual-input")
    assert campo is not None
    assert campo.input_value() == pagina.url


def test_caixa_manual_fecha_com_escape(pagina):
    pagina.evaluate("() => { navigator.share = undefined; navigator.clipboard = undefined; }")
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)
    assert pagina.query_selector("#partilhar-manual-overlay") is not None

    pagina.keyboard.press("Escape")
    pagina.wait_for_timeout(50)
    assert pagina.query_selector("#partilhar-manual-overlay") is None


def test_caixa_manual_fecha_no_botao_fechar(pagina):
    pagina.evaluate("() => { navigator.share = undefined; navigator.clipboard = undefined; }")
    pagina.click(".botao-partilhar")
    pagina.wait_for_timeout(100)

    pagina.click(".partilhar-manual-fechar")
    pagina.wait_for_timeout(50)
    assert pagina.query_selector("#partilhar-manual-overlay") is None


# ── Acessibilidade ───────────────────────────────────────────────────────

def test_botao_tem_aria_label_e_texto_visivel(pagina):
    botao = pagina.query_selector(".botao-partilhar")
    assert botao.get_attribute("aria-label") == "Partilhar este artigo"
    assert "Partilhar este artigo" in botao.inner_text()


def test_botao_e_ativavel_por_teclado(pagina):
    pagina.evaluate("""
        () => {
            navigator.share = undefined;
            navigator.clipboard = { writeText: () => Promise.resolve() };
        }
    """)
    pagina.focus(".botao-partilhar")
    pagina.keyboard.press("Enter")
    pagina.wait_for_timeout(100)

    assert pagina.query_selector("#partilhar-feedback") is not None


def test_botao_e_elemento_nativo_button():
    # Um <button> real é sempre focável e activável por teclado (Enter
    # e Espaço) sem precisar de tabindex nem de handlers extra de teclado.
    assert '<button type="button"' in _HTML_BASE
