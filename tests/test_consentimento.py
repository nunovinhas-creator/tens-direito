"""
Testes do banner de consentimento próprio (assets/js/consentimento.js),
que substituiu o CookieYes a 2026-07-11 e passou a Consent Mode v2
AVANÇADO a 2026-07-13.

A garantia central — mesma filosofia do teste de rede-zero do gerador de
documentos — é provada com Chromium real, nunca só por inspecção de texto:
o gtag.js do Google Analytics é SEMPRE pedido à rede, para todos os
visitantes, independentemente da escolha (Consent Mode avançado); o que
nunca acontece sem "Aceitar" explícito é o ESTADO do consentimento subir a
'granted' — e por isso nunca existe cookie `_ga`/`_ga_*` sem essa escolha.
"Rejeitar" (ou não responder) garante zero cookies de análise, nunca zero
pedidos de rede; a escolha sobrevive a reloads.

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


def test_carregarga_nunca_concede_consentimento_por_si_so():
    """Consent Mode avançado: carregarGA() injecta sempre o script (para
    todos, independentemente da escolha) — só concederConsentimento() sobe
    o estado a 'granted', e só é chamada a partir de aceitar()/do arranque
    com escolha já "aceite"."""
    js = (RAIZ / "assets" / "js" / "consentimento.js").read_text(encoding="utf-8")
    assert js.count("googletagmanager.com") == 1
    assert "sessionStorage" not in js

    assert js.count("function carregarGA") == 1
    inicio = js.index("function carregarGA")
    fim = js.index("function concederConsentimento", inicio)
    corpo_carregarga = js[inicio:fim]
    assert "granted" not in corpo_carregarga, (
        "carregarGA() não deve conceder consentimento directamente — "
        "isso quebraria o invariante 'denied por omissão'"
    )

    assert "function concederConsentimento" in js
    assert js.count("analytics_storage: 'granted'") == 1, (
        "a concessão a 'granted' tem de viver só dentro de concederConsentimento()"
    )

    # carregarGA() é chamada incondicionalmente no arranque do ficheiro —
    # nunca dentro de um "if (escolha === 'aceite')" isolado.
    arranque = js[js.rindex("var escolha = lerEscolha();"):]
    assert "\n  carregarGA(); // carrega para todos" in arranque


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
    (interceptados e abortados — nunca saem para a rede real). Em Consent
    Mode avançado isto acontece SEMPRE, independentemente da escolha — o
    que varia é o estado do consentimento, nunca o pedido em si."""
    page = browser.new_page()
    pedidos_gtm = []

    def _intercetar(route):
        pedidos_gtm.append(route.request.url)
        route.abort()

    page.route("https://www.googletagmanager.com/**", _intercetar)
    page.goto(f"{base_url}/{rel}", wait_until="networkidle", timeout=30000)
    return page, pedidos_gtm


def _data_layer(page):
    """dataLayer real, como lista de listas — cada entrada é um array de
    argumentos de gtag(...)."""
    return page.evaluate(
        "JSON.parse(JSON.stringify(window.dataLayer.map("
        "function(a){return Array.prototype.slice.call(a);})))"
    )


def _tem_update_granted(data_layer):
    return any(
        len(entry) >= 3
        and entry[0] == "consent"
        and entry[1] == "update"
        and isinstance(entry[2], dict)
        and entry[2].get("analytics_storage") == "granted"
        for entry in data_layer
    )


def _tem_cookie_ga(page):
    cookies = page.context.cookies()
    return any(c["name"] == "_ga" or c["name"].startswith("_ga_") for c in cookies)


@pytestmark_playwright
def test_primeira_visita_mostra_banner_e_pede_ga_em_modo_denied(servidor, browser):
    """Consent Mode avançado: o gtag.js É pedido logo na 1.ª visita, para
    todos — mas o consentimento fica 'denied' (nunca sobe a 'granted'
    sozinho) e nunca existe cookie de análise sem uma escolha explícita."""
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        banner = page.locator("#td-consent")
        assert banner.count() == 1, "banner de consentimento não renderizado na 1.ª visita"
        assert banner.locator(".td-consent-aceitar").inner_text().strip() == "Aceitar"
        assert banner.locator(".td-consent-recusar").inner_text().strip() == "Rejeitar"
        assert banner.locator('a[href="/privacidade.html"]').count() == 1

        assert any("gtag/js" in url for url in pedidos_gtm), (
            f"gtag.js NUNCA foi pedido (Consent Mode avançado exige pedido para todos): {pedidos_gtm}"
        )
        assert page.locator('script[src*="googletagmanager.com/gtag/js"]').count() == 1, (
            "o <script> do gtag.js tem de estar no DOM, mesmo sem escolha"
        )

        data_layer = _data_layer(page)
        assert not _tem_update_granted(data_layer), (
            f"consentimento subiu a 'granted' sem nenhuma escolha explícita: {data_layer}"
        )
        assert not _tem_cookie_ga(page), "cookie _ga presente antes de qualquer consentimento"

        # gtag global existe para os eventos dos simuladores nunca rebentarem.
        assert page.evaluate("typeof window.gtag") == "function"
        assert page.evaluate("localStorage.getItem('td_consentimento')") is None
    finally:
        page.close()


@pytestmark_playwright
def test_aceitar_concede_consentimento_e_persiste(servidor, browser):
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        page.click("#td-consent .td-consent-aceitar")
        page.wait_for_timeout(500)

        assert page.locator("#td-consent").count() == 0, "banner não fechou ao aceitar"
        assert _tem_update_granted(_data_layer(page)), (
            "nenhum ['consent','update',{analytics_storage:'granted'}] no dataLayer depois de Aceitar"
        )
        assert page.evaluate("localStorage.getItem('td_consentimento')") == "aceite"

        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        assert page.locator("#td-consent").count() == 0, "banner reapareceu depois de aceite"
        assert any("gtag/js" in url for url in pedidos_gtm), "gtag.js não foi pedido no reload"
        assert _tem_update_granted(_data_layer(page)), (
            "consentimento não se manteve 'granted' depois de um reload já aceite"
        )
    finally:
        page.close()


@pytestmark_playwright
def test_rejeitar_mantem_denied_sem_cookies_mas_ga_continua_a_carregar(servidor, browser):
    """Consent Mode avançado: rejeitar nunca impede o pedido do gtag.js
    (isso continua a acontecer para todos) — garante só que o estado nunca
    sobe a 'granted' e que nenhum cookie de análise é colocado."""
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        page.click("#td-consent .td-consent-recusar")
        page.wait_for_timeout(500)

        assert page.locator("#td-consent").count() == 0, "banner não fechou ao rejeitar"
        assert page.evaluate("localStorage.getItem('td_consentimento')") == "recusado"
        assert any("gtag/js" in url for url in pedidos_gtm), (
            f"gtag.js devia ter sido pedido mesmo com rejeição (Consent Mode avançado): {pedidos_gtm}"
        )
        assert not _tem_update_granted(_data_layer(page)), (
            "consentimento subiu a 'granted' apesar de 'Rejeitar'"
        )
        assert not _tem_cookie_ga(page), "cookie _ga presente apesar de 'Rejeitar'"

        pedidos_antes_do_reload = len(pedidos_gtm)
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(300)
        assert page.locator("#td-consent").count() == 0, "banner reapareceu depois de recusado"
        assert len(pedidos_gtm) > pedidos_antes_do_reload, "gtag.js não voltou a ser pedido no reload"
        assert not _tem_update_granted(_data_layer(page)), (
            "consentimento subiu a 'granted' num reload depois de 'Rejeitar'"
        )
        assert not _tem_cookie_ga(page), "cookie _ga presente num reload depois de 'Rejeitar'"
    finally:
        page.close()


@pytestmark_playwright
def test_consent_mode_avancado_golden(servidor, browser):
    """Golden test anti-regressão do Consent Mode v2 avançado — o guardrail
    que validar-conteudo.yml não cobre (esse confirma que a tag está
    PRESENTE no HTML estático, nunca que dispara com o consentimento
    correcto em runtime). Cobre exactamente os 4 pontos da migração:
    1) banner visível sem escolha guardada; 2) gtag.js presente no DOM
    para todos; 3) 'denied' nunca gera update->granted nem cookie _ga;
    4) "Aceitar" gera o update->granted no dataLayer."""
    page, pedidos_gtm = _abrir(browser, servidor)
    try:
        assert page.locator("#td-consent").count() == 1

        assert page.locator('script[src*="googletagmanager.com/gtag/js"]').count() == 1
        assert any("gtag/js" in url for url in pedidos_gtm)

        data_layer_antes = _data_layer(page)
        assert not _tem_update_granted(data_layer_antes)
        assert not _tem_cookie_ga(page)

        page.click("#td-consent .td-consent-aceitar")
        page.wait_for_timeout(300)
        assert _tem_update_granted(_data_layer(page)), (
            "clicar 'Aceitar' tem de gerar update->granted no dataLayer"
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
