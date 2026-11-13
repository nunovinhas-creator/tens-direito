"""
Chromium real (http.server, nunca file://), com relógio fixo:

1. «Datas a não perder» e «Prazo a decorrer»: só aparece o que está em
   curso pela data de Lisboa (prazo fixo, prazo anual, início futuro),
   mesmo com o fuso do aparelho noutro dia; sem JavaScript nenhuma data
   aparece; o cartão do próximo pagamento lê #cal-home-dados.
2. Versão para imprimir: sem nav, barra, rodapé nem botões; perguntas
   abertas; ligações externas com o endereço; endereço da página no fim.
"""
from __future__ import annotations

import datetime as dt
import functools
import glob
import http.server
import json
import os
import re
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent


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
    _PLAYWRIGHT = _localizar_chromium() is not None
except ImportError:
    _PLAYWRIGHT = False

# Dados fixos do calendário (nunca os do mês real, que mudam todos os meses).
DADOS_CAL = {
    "2026-11": [{"dia": 6, "resumo": "Pensões"}, {"dia": 16, "resumo": "Abono e prestações familiares"}],
    "2026-12": [{"dia": 4, "resumo": "Pensões"}],
}


class _Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def servidor():
    if not _PLAYWRIGHT:
        pytest.skip("Playwright/Chromium indisponível neste ambiente")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Handler, directory=str(RAIZ)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.fixture(scope="module")
def browser(servidor):
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=_localizar_chromium())
        yield b
        b.close()


def _index_com_dados_fixos() -> str:
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    novo, n = re.subn(
        r'(<script id="cal-home-dados" type="application/json"[^>]*>).*?(</script>)',
        lambda m: m.group(1) + json.dumps(DADOS_CAL, ensure_ascii=False) + m.group(2),
        html, count=1, flags=re.S,
    )
    assert n == 1
    return novo


def _abrir(browser, servidor, url, agora, *, js=True, fuso="Europe/Lisbon", media=None):
    ctx = browser.new_context(java_script_enabled=js, timezone_id=fuso, viewport={"width": 1100, "height": 900})
    page = ctx.new_page()
    page.route("https://www.googletagmanager.com/**", lambda r: r.abort())
    page.route("**/data/calendario_barra.json", lambda r: r.fulfill(
        status=200, content_type="application/json", body=json.dumps(DADOS_CAL)))
    if url.startswith("/index.html"):
        page.route("**/index.html", lambda r: r.fulfill(
            status=200, content_type="text/html; charset=utf-8", body=_index_com_dados_fixos()))
    if js:
        page.clock.install(time=agora)
    if media:
        page.emulate_media(media=media)
    page.goto(servidor + url, wait_until="networkidle")
    if js:
        page.evaluate("var c = document.getElementById('td-consent'); if (c) c.remove();")
    return page


def _cartoes_visiveis(page) -> list[str]:
    return page.eval_on_selector_all(
        ".urgente-cards .urgente-card",
        "els => els.filter(e => e.offsetParent !== null).map(e => e.querySelector('h3').textContent.trim())",
    )


def _utc(ano, mes, dia, hora=10):
    return dt.datetime(ano, mes, dia, hora, 0, tzinfo=dt.timezone.utc)


# ── 1. Prazos ────────────────────────────────────────────────────────────


def test_novembro_mostra_os_prazos_em_curso_e_o_proximo_pagamento(browser, servidor):
    page = _abrir(browser, servidor, "/index.html", _utc(2026, 11, 13))
    visiveis = _cartoes_visiveis(page)
    assert visiveis[0] == "Próximo pagamento: 16 de novembro"
    assert set(visiveis[1:]) == {
        "Prova Escolar", "Garantia pública na compra de casa", "O que muda em 2027",
        "Prestação Social Única", "Bolsa de estudo do ensino superior", "Passe sub-23",
    }
    texto = page.locator("[data-cartao-pagamento] p").inner_text()
    assert texto == "Abono e prestações familiares"


def test_janeiro_esconde_o_que_acabou_e_mantem_o_que_continua(browser, servidor):
    page = _abrir(browser, servidor, "/index.html", _utc(2027, 1, 2))
    visiveis = _cartoes_visiveis(page)
    assert "Bolsa de estudo do ensino superior" in visiveis
    for acabou in ("Prova Escolar", "Garantia pública na compra de casa",
                   "Prestação Social Única", "O que muda em 2027"):
        assert acabou not in visiveis
    # sem dados de janeiro de 2027: o cartão do pagamento fica a ligação ao calendário
    assert visiveis[0] == "Calendário de pagamentos"


def test_prazo_anual_volta_no_ano_seguinte_e_inicio_futuro_espera(browser, servidor):
    page = _abrir(browser, servidor, "/index.html", _utc(2027, 8, 15))
    visiveis = _cartoes_visiveis(page)
    assert "Prova Escolar" in visiveis
    assert "Bolsa de estudo do ensino superior" not in visiveis  # acabou a 31/05/2027
    page = _abrir(browser, servidor, "/index.html", _utc(2026, 9, 1))
    assert "Bolsa de estudo do ensino superior" not in _cartoes_visiveis(page)  # começa a 3/10


def test_conta_o_dia_de_lisboa_nao_o_do_aparelho(browser, servidor):
    """31/12 às 12h UTC: em Auckland já é 1 de janeiro, em Lisboa ainda é 31."""
    page = _abrir(browser, servidor, "/index.html", _utc(2026, 12, 31, 12), fuso="Pacific/Auckland")
    assert "Garantia pública na compra de casa" in _cartoes_visiveis(page)


def test_sem_javascript_nenhuma_data_aparece(browser, servidor):
    page = _abrir(browser, servidor, "/index.html", None, js=False)
    assert _cartoes_visiveis(page) == ["Calendário de pagamentos", "Passe sub-23"]
    page = _abrir(browser, servidor, "/p/apoios-escolares.html", None, js=False)
    assert page.locator(".etiqueta-prazo:visible").count() == 0
    assert page.locator(".etiqueta-simulador:visible").count() >= 1


def test_etiqueta_prazo_a_decorrer_na_lista_de_guias(browser, servidor):
    seletor = 'li:has(a[href="/prova-escolar.html"]) .etiqueta-prazo'
    page = _abrir(browser, servidor, "/p/apoios-escolares.html", _utc(2026, 11, 13))
    assert page.locator(seletor).is_visible()
    assert page.locator('li:has(a[href="/acao-social-escolar.html"]) .etiqueta-simulador').is_visible()
    page = _abrir(browser, servidor, "/p/apoios-escolares.html", _utc(2027, 1, 2))
    assert page.locator(seletor).is_hidden()
    # o invólucro vazio também desaparece (nada de espaço solto)
    assert page.locator('li:has(a[href="/prova-escolar.html"]) .etiquetas').is_hidden()


# ── 2. Impressão ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("url", ["/rsi.html", "/p/apoios-escolares.html", "/simulador-abono.html"])
def test_impressao_so_conteudo(browser, servidor, url):
    page = _abrir(browser, servidor, url, _utc(2026, 11, 13), media="print")
    for seletor in (".nav-wrap", ".barra-topo-regiao", "footer", ".skip-link"):
        if page.locator(seletor).count():
            assert page.locator(seletor).first.is_hidden(), f"{seletor} visível na impressão de {url}"
    assert page.locator("h1").first.is_visible()
    fundo = page.evaluate("getComputedStyle(document.body).backgroundColor")
    assert fundo in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)")
    rodape = page.evaluate("getComputedStyle(document.body, '::after').content")
    assert "Impresso de" in rodape and url in rodape


def test_impressao_artigo_sem_partilha_e_com_perguntas_abertas(browser, servidor):
    page = _abrir(browser, servidor, "/rsi.html", _utc(2026, 11, 13), media="print")
    assert page.locator(".botao-partilhar").first.is_hidden()
    assert page.locator(".cluster-relacionados").first.is_hidden()
    resposta = page.locator(".zona-cinzenta details .resposta").first
    assert resposta.is_visible(), "resposta de uma pergunta fechada não aparece na impressão"
    cor = page.evaluate("getComputedStyle(document.querySelector('.hero h1')).color")
    assert cor == "rgb(0, 0, 0)"
    externo = page.evaluate(
        "getComputedStyle(document.querySelector('main a[href^=\"http\"]'), '::after').content")
    assert "http" in externo


def test_beforeprint_abre_as_perguntas_e_afterprint_repoe(browser, servidor):
    page = _abrir(browser, servidor, "/rsi.html", _utc(2026, 11, 13))
    fechadas = page.evaluate("document.querySelectorAll('main details:not([open])').length")
    assert fechadas > 0
    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert page.evaluate("document.querySelectorAll('main details:not([open])').length") == 0
    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert page.evaluate("document.querySelectorAll('main details:not([open])').length") == fechadas


def test_ecra_normal_continua_igual(browser, servidor):
    page = _abrir(browser, servidor, "/rsi.html", _utc(2026, 11, 13))
    assert page.locator(".nav-wrap").is_visible()
    assert page.evaluate("getComputedStyle(document.body, '::after').content") in ("none", "normal")


def test_pdf_gera(browser, servidor):
    page = _abrir(browser, servidor, "/rsi.html", _utc(2026, 11, 13))
    pdf = page.pdf(format="A4")
    assert pdf[:4] == b"%PDF" and len(pdf) > 10_000
