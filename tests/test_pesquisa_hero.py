"""
Testes funcionais para a pesquisa do hero do index.html (chips + botão de
lupa + Enter), executados num browser real (Chromium headless via
Playwright) — só assim se apanha o bug real encontrado nesta sessão: o
listener "fechar ao clicar fora" (pesquisa.js) fechava os resultados no
mesmo clique que os abria, porque o clique no chip/lupa não era nem o
campo nem o próprio dropdown.

Extrai o JS directamente do index.html real (não uma cópia à parte) —
mesma filosofia de test_breadcrumb_coerencia.py/test_nav_coerencia.py:
testar a fonte real, para nunca divergir dela silenciosamente.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PESQUISA_JS = (RAIZ / "scripts" / "pesquisa.js").read_text(encoding="utf-8")
INDEX_HTML = (RAIZ / "index.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    """Extrai o <script>...</script> do index.html real que contém
    `marcador` — falha alto e claro se a estrutura mudar, em vez de
    testar silenciosamente uma cópia desactualizada."""
    for m in re.finditer(r"<script>([\s\S]*?)</script>", INDEX_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em index.html")


PESQUISA_HERO_JS = _extrair_script_inline("function preencherPesquisa")


def _extrair_regra_css(seletor: str) -> str:
    m = re.search(re.escape(seletor) + r"\s*\{[^}]*\}", INDEX_HTML)
    if not m:
        raise AssertionError(f"Não encontrei a regra CSS '{seletor}' em index.html")
    return m.group(0)


HERO_SEARCH_BTN_CSS = _extrair_regra_css(".hero-search-btn")

_HTML_BASE = """<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"><title>Teste</title></head>
<body>
  <div class="hero-search" role="search" style="position:relative;">
    <form onsubmit="return false;">
      <button type="button" class="hero-search-btn" aria-label="Pesquisar" onclick="executarPesquisaHero(event)">🔍</button>
      <input type="search" id="campo-pesquisa" placeholder="Pesquisar…" aria-label="Pesquisar"
        autocomplete="off"
        oninput="mostrarResultados(pesquisar(this.value), this.value)"
        onkeydown="if (event.key === 'Enter') { event.preventDefault(); executarPesquisaHero(event); }">
    </form>
    <div id="resultados-pesquisa" style="display:none;position:absolute;"></div>
  </div>
  <div class="hero-chips">
    <button type="button" class="chip" onclick="preencherPesquisa(event, 'Abono de Família')">Abono de Família</button>
  </div>
  <h1>Fora da pesquisa</h1>
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
        page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        page.set_content(_HTML_BASE)
        page.add_style_tag(content=HERO_SEARCH_BTN_CSS)
        page.add_script_tag(content=PESQUISA_JS)
        page.add_script_tag(content=PESQUISA_HERO_JS)
        yield page
        browser.close()


def _display(pagina):
    return pagina.eval_on_selector("#resultados-pesquisa", "el => getComputedStyle(el).display")


def test_chip_preenche_campo_e_mostra_resultados(pagina):
    pagina.click("button.chip")
    pagina.wait_for_timeout(100)

    assert pagina.locator("#campo-pesquisa").input_value() == "Abono de Família"
    assert _display(pagina) == "block"
    assert pagina.locator("#resultados-pesquisa a").count() > 0


def test_lupa_pesquisa_o_valor_atual_do_campo(pagina):
    pagina.fill("#campo-pesquisa", "bolsa de mérito")
    pagina.evaluate("document.getElementById('resultados-pesquisa').style.display = 'none'")

    pagina.click(".hero-search-btn")
    pagina.wait_for_timeout(100)

    assert _display(pagina) == "block"
    assert pagina.locator("#resultados-pesquisa a").count() > 0


def test_lupa_tem_touch_target_minimo_44px(pagina):
    box = pagina.locator(".hero-search-btn").bounding_box()
    assert box["width"] >= 43.9  # tolerância sub-pixel do motor de layout
    assert box["height"] >= 43.9


def test_lupa_e_um_botao_com_aria_label(pagina):
    botao = pagina.locator(".hero-search-btn")
    assert botao.get_attribute("type") == "button"
    assert botao.get_attribute("aria-label")


def test_enter_no_campo_pesquisa_e_nao_recarrega_a_pagina(pagina):
    pagina.fill("#campo-pesquisa", "rsi")
    pagina.evaluate("document.getElementById('resultados-pesquisa').style.display = 'none'")
    url_antes = pagina.url

    pagina.locator("#campo-pesquisa").press("Enter")
    pagina.wait_for_timeout(100)

    assert _display(pagina) == "block"
    assert pagina.locator("#resultados-pesquisa a").count() > 0
    assert pagina.url == url_antes  # sem reload/navegação


def test_clique_fora_continua_a_fechar_os_resultados(pagina):
    """Regressão: o fix do bug (stopPropagation no chip/lupa) não pode
    quebrar o comportamento de fechar ao clicar mesmo fora."""
    pagina.click("button.chip")
    pagina.wait_for_timeout(100)
    assert _display(pagina) == "block"

    pagina.click("h1")
    pagina.wait_for_timeout(100)
    assert _display(pagina) == "none"
