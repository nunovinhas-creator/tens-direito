"""
Testes do banner de consentimento próprio (assets/js/consentimento.js),
que substituiu o CookieYes a 2026-07-11.

A garantia central — mesma filosofia do teste de rede-zero do gerador de
documentos — é provada com Chromium real, nunca só por inspecção de texto:
o gtag.js do Google Analytics NUNCA é pedido à rede antes de o visitante
clicar "Aceitar"; "Rejeitar" (ou não responder) mantém a página sem
qualquer pedido de analytics, e a escolha sobrevive a reloads.

Parte estática (sem browser): nenhuma página servida pode voltar a
referenciar o CookieYes, e todas têm o bloco novo (stub inline com
Consent Mode negado por omissão + consentimento.js com o ID do GA4).

Se o Chromium do Playwright não estiver disponível, só os testes de
browser são ignorados (skip) — mesmo padrão de test_acessibilidade.py.
"""
from __future__ import annotations

import glob
import http.server
import os
import socket
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from migrar_consentimento import encontrar_paginas  # noqa: E402

PAGINAS = encontrar_paginas()
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]

GA4_ID = "G-XP46PM8H1Q"


# ---------------------------------------------------------------------------
# Estático — todas as páginas servidas (raiz + p/ + documentos/)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_nenhuma_pagina_referencia_cookieyes(caminho):
    html = caminho.read_text(encoding="utf-8")
    assert "cookieyes" not in html.lower(), (
        f"{caminho.name}: ainda referencia o CookieYes — removido a 2026-07-11, "
        "correr scripts/migrar_consentimento.py --write"
    )


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_toda_a_pagina_tem_o_bloco_de_consentimento_proprio(caminho):
    html = caminho.read_text(encoding="utf-8")
    assert "/assets/js/consentimento.js" in html, f"{caminho.name}: sem consentimento.js"
    assert f'data-ga4="{GA4_ID}"' in html, f"{caminho.name}: sem o ID GA4 no data-ga4"
    assert "gtag('consent','default'" in html, (
        f"{caminho.name}: sem o stub inline de Consent Mode negado por omissão"
    )
    assert "analytics_storage:'denied'" in html, (
        f"{caminho.name}: o Consent Mode por omissão tem de negar analytics_storage"
    )
    # O gtag.js nunca pode voltar a ser carregado estaticamente no <head> —
    # só o consentimento.js o pode injectar, depois da aceitação.
    assert "googletagmanager.com/gtag/js" not in html, (
        f"{caminho.name}: gtag.js carregado estaticamente — contorna o consentimento"
    )
    # Ordem: o stub (consent default) tem de vir antes do consentimento.js.
    assert html.index("gtag('consent','default'") < html.index("/assets/js/consentimento.js"), (
        f"{caminho.name}: o consent default tem de ser definido antes de consentimento.js"
    )


def test_consentimento_js_nunca_carrega_ga_sem_aceitacao_explicita():
    js = (RAIZ / "assets" / "js" / "consentimento.js").read_text(encoding="utf-8")
    # O carregamento do gtag.js vive numa única função, só chamada com
    # escolha "aceite" (guardada ou acabada de clicar).
    assert js.count("googletagmanager.com") == 1
    assert "sessionStorage" not in js


# ---------------------------------------------------------------------------
# Browser real (Chromium via Playwright)
# ---------------------------------------------------------------------------

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

pytestmark_playwright = pytest.mark.skipif(
    not (_PLAYWRIGHT_DISPONIVEL and _CHROMIUM_PATH),
    reason="Playwright/Chromium não disponível neste ambiente",
)


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


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        yield b
        b.close()


def _abrir(browser, base_url, rel="index.html"):
    """Página nova + registo de todos os pedidos a googletagmanager.com
    (interceptados e abortados — nunca saem para a rede real)."""
    page = browser.new_page()
    pedidos_gtm = []

    def _intercetar(route):
        pedidos_gtm.append(route.request.url)
        route.abort()

    page.route("https://www.googletagmanager.com/**", _intercetar)
    page.goto(f"{base_url}/{rel}", wait_until="networkidle", timeout=30000)
    return page, pedidos_gtm


@pytestmark_playwright
def test_primeira_visita_mostra_banner_e_nao_pede_ga(servidor, browser):
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        banner = page.locator("#td-consent")
        assert banner.count() == 1, "banner de consentimento não renderizado na 1.ª visita"
        assert banner.locator(".td-consent-aceitar").inner_text().strip() == "Aceitar"
        assert banner.locator(".td-consent-recusar").inner_text().strip() == "Rejeitar"
        assert banner.locator('a[href="/privacidade.html"]').count() == 1

        assert pedidos_gtm == [], (
            f"gtag.js pedido ANTES de qualquer escolha (esperava zero): {pedidos_gtm}"
        )
        # gtag global existe para os eventos dos simuladores nunca rebentarem.
        assert page.evaluate("typeof window.gtag") == "function"
        assert page.evaluate("localStorage.getItem('td_consentimento')") is None
    finally:
        page.close()


@pytestmark_playwright
def test_aceitar_carrega_ga_persiste_e_banner_nao_volta(servidor, browser):
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        page.click("#td-consent .td-consent-aceitar")
        page.wait_for_timeout(500)

        assert page.locator("#td-consent").count() == 0, "banner não fechou ao aceitar"
        assert any("gtag/js" in url for url in pedidos_gtm), (
            f"gtag.js nunca foi pedido depois de Aceitar: {pedidos_gtm}"
        )
        assert page.evaluate("localStorage.getItem('td_consentimento')") == "aceite"

        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        assert page.locator("#td-consent").count() == 0, "banner reapareceu depois de aceite"
        assert len(pedidos_gtm) >= 2, "GA não voltou a carregar num reload já aceite"
    finally:
        page.close()


@pytestmark_playwright
def test_rejeitar_nunca_carrega_ga_e_persiste(servidor, browser):
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        page.click("#td-consent .td-consent-recusar")
        page.wait_for_timeout(500)

        assert page.locator("#td-consent").count() == 0, "banner não fechou ao rejeitar"
        assert page.evaluate("localStorage.getItem('td_consentimento')") == "recusado"

        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        assert page.locator("#td-consent").count() == 0, "banner reapareceu depois de recusado"
        assert pedidos_gtm == [], (
            f"gtag.js pedido apesar de recusado (esperava zero): {pedidos_gtm}"
        )
    finally:
        page.close()


@pytestmark_playwright
def test_botao_gerir_cookies_reabre_o_banner(servidor, browser):
    page, _ = _abrir(browser, servidor, "privacidade.html")
    try:
        page.click("#td-consent .td-consent-recusar")
        assert page.locator("#td-consent").count() == 0

        page.click(".botao-gerir-cookies")
        assert page.locator("#td-consent").count() == 1, (
            "o botão 'Gerir cookies' de privacidade.html não reabriu o banner"
        )
    finally:
        page.close()
