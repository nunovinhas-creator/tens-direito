"""
Testes golden para os 2 blocos da FASE 1 de MELHORIAS-SPEC.md:
".resposta-rapida" (reaproveita ".resposta-direta" já existente no hero,
acrescentando o rótulo "⚡ Resposta rápida" + "📖 Leitura completa: X min")
e ".checklist-final" (checklist accionável antes da secção de FAQ, com
checkboxes interactivas cujo estado vive só em memória — nunca em
localStorage).

Aplicados nesta fase a 4 artigos: baixa-medica-subsidio-doenca.html
(artigo-alvo explícito da spec) e os 3 artigos com mais tráfego GSC
confirmados pelo Nuno (manuais-escolares-mega.html,
acao-social-escolar.html, subsidio-desemprego.html).

Duas camadas de verificação:
1. Estrutural (BeautifulSoup) — presença/ordem/contagem de palavras,
   sem precisar de browser.
2. Funcional (Playwright/Chromium real) — viewport mobile 390px sem
   overflow horizontal, e a interactividade real das checkboxes
   (contador a actualizar, estado nunca sobrevive a um reload).

Se o Chromium do Playwright não estiver disponível, só a camada 2 é
ignorada (skip) — mesmo padrão de test_acessibilidade.py/test_share_js.py.
"""
from __future__ import annotations

import glob
import http.server
import os
import re
import socket
import threading
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

RAIZ = Path(__file__).parent.parent

PAGINAS_ALVO = [
    "baixa-medica-subsidio-doenca.html",
    "manuais-escolares-mega.html",
    "acao-social-escolar.html",
    "subsidio-desemprego.html",
]

# Só as páginas com secção "Dúvidas frequentes" dedicada é que permitem
# verificar a ordem "checklist antes do FAQ" directamente — o MEGA não
# tem essa secção visível (FAQ só existe como JSON-LD), por isso o
# checklist foi colocado antes de RELACIONADOS (fim do corpo do artigo),
# nunca inventando uma secção que a página não tem.
MARCADOR_FAQ_POR_PAGINA = {
    "baixa-medica-subsidio-doenca.html": "Dúvidas frequentes",
    "acao-social-escolar.html": "Dúvidas frequentes",
    "subsidio-desemprego.html": "Dúvidas frequentes",
    "manuais-escolares-mega.html": None,
}

MAX_PALAVRAS_RESPOSTA_RAPIDA = 60


def _ler(pagina: str) -> str:
    return (RAIZ / pagina).read_text(encoding="utf-8")


def _sopa(pagina: str) -> BeautifulSoup:
    return BeautifulSoup(_ler(pagina), "html.parser")


# ── Camada 1: estrutural ────────────────────────────────────────────────

@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_resposta_rapida_presente_com_label_e_tempo(pagina):
    sopa = _sopa(pagina)
    bloco = sopa.select_one(".resposta-rapida")
    assert bloco is not None, f"{pagina}: bloco .resposta-rapida em falta"
    assert bloco.select_one(".resposta-rapida-label"), f"{pagina}: falta o rótulo ⚡ Resposta rápida"
    assert "resposta rápida" in bloco.select_one(".resposta-rapida-label").get_text(strip=True).lower()
    tempo = bloco.select_one(".resposta-rapida-tempo")
    assert tempo is not None, f"{pagina}: falta '📖 Leitura completa: X min'"
    assert re.search(r"\d+\s*min", tempo.get_text()), f"{pagina}: tempo de leitura sem número de minutos"


@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_resposta_rapida_tem_no_maximo_60_palavras(pagina):
    sopa = _sopa(pagina)
    texto = sopa.select_one(".resposta-rapida-texto")
    assert texto is not None, f"{pagina}: falta .resposta-rapida-texto"
    n_palavras = len(texto.get_text(strip=True).split())
    assert n_palavras <= MAX_PALAVRAS_RESPOSTA_RAPIDA, (
        f"{pagina}: resposta rápida com {n_palavras} palavras, acima do limite de "
        f"{MAX_PALAVRAS_RESPOSTA_RAPIDA} da spec"
    )


@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_resposta_rapida_continua_dentro_do_hero(pagina):
    """A caixa continua a viver dentro do <header class="hero"> — nunca
    duplicada como um segundo bloco fora do hero."""
    sopa = _sopa(pagina)
    hero = sopa.select_one("header.hero")
    assert hero is not None, f"{pagina}: sem <header class='hero'>"
    assert hero.select_one(".resposta-rapida") is not None, f"{pagina}: .resposta-rapida fora do hero"


@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_checklist_final_presente_com_checkboxes(pagina):
    sopa = _sopa(pagina)
    bloco = sopa.select_one(".checklist-final")
    assert bloco is not None, f"{pagina}: bloco .checklist-final em falta"
    assert bloco.select_one("h2"), f"{pagina}: .checklist-final sem <h2>"
    checkboxes = bloco.select('input[type="checkbox"]')
    assert len(checkboxes) >= 4, f"{pagina}: checklist com poucos itens accionáveis ({len(checkboxes)})"
    progresso = bloco.select_one(".checklist-progresso")
    assert progresso is not None, f"{pagina}: falta o contador .checklist-progresso"
    # cada checkbox tem de estar dentro de um <label> (associação implícita, acessível)
    for cb in checkboxes:
        assert cb.find_parent("label") is not None, f"{pagina}: checkbox fora de <label>"


@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_checklist_final_vem_antes_do_faq(pagina):
    marcador = MARCADOR_FAQ_POR_PAGINA[pagina]
    if marcador is None:
        pytest.skip(f"{pagina}: sem secção de FAQ visível dedicada nesta página")
    html = _ler(pagina)
    pos_checklist = html.find('class="checklist-final"')
    pos_faq = html.find(marcador)
    assert pos_checklist != -1, f"{pagina}: .checklist-final não encontrado"
    assert pos_faq != -1, f"{pagina}: marcador de FAQ '{marcador}' não encontrado"
    assert pos_checklist < pos_faq, f"{pagina}: .checklist-final devia vir antes de '{marcador}'"


@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_assets_checklist_ligados_no_head(pagina):
    html = _ler(pagina)
    assert '/assets/css/checklist.css' in html, f"{pagina}: checklist.css não ligado"
    assert '/assets/js/checklist.js' in html, f"{pagina}: checklist.js não ligado"


def test_checklist_js_nunca_usa_localstorage():
    """Requisito explícito da spec: 'estado em memória, SEM localStorage'.
    O comentário do módulo menciona a palavra para explicar a decisão —
    o que nunca pode existir é uma chamada real à API."""
    js = (RAIZ / "assets" / "js" / "checklist.js").read_text(encoding="utf-8")
    assert "localStorage." not in js
    assert "sessionStorage." not in js


# ── Camada 2: funcional (Playwright real) ───────────────────────────────

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


@pytestmark_playwright
@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_blocos_sem_overflow_horizontal_em_mobile_390px(servidor, browser, pagina):
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.route("https://cdn-cookieyes.com/**", lambda route: route.abort())
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    try:
        page.goto(f"{servidor}/{pagina}", wait_until="networkidle", timeout=30000)

        for seletor in (".resposta-rapida", ".checklist-final"):
            elemento = page.locator(seletor)
            assert elemento.count() > 0, f"{pagina}: {seletor} não renderizado"
            caixa = elemento.first.bounding_box()
            assert caixa is not None, f"{pagina}: {seletor} sem bounding box (invisível?)"
            assert caixa["width"] <= 390, (
                f"{pagina}: {seletor} com {caixa['width']}px de largura, excede o viewport de 390px"
            )
    finally:
        page.close()


@pytestmark_playwright
@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_checklist_contador_actualiza_ao_marcar_e_desmarcar(servidor, browser, pagina):
    page = browser.new_page()
    page.route("https://cdn-cookieyes.com/**", lambda route: route.abort())
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    try:
        page.goto(f"{servidor}/{pagina}", wait_until="networkidle", timeout=30000)

        progresso = page.locator(".checklist-final .checklist-progresso").first
        checkboxes = page.locator('.checklist-final input[type="checkbox"]')
        total = checkboxes.count()

        assert progresso.inner_text().strip() == f"0 de {total} concluídos"

        checkboxes.nth(0).check()
        checkboxes.nth(1).check()
        assert progresso.inner_text().strip() == f"2 de {total} concluídos"

        checkboxes.nth(0).uncheck()
        assert progresso.inner_text().strip() == f"1 de {total} concluídos"
    finally:
        page.close()


@pytestmark_playwright
@pytest.mark.parametrize("pagina", PAGINAS_ALVO)
def test_checklist_nunca_persiste_estado_entre_reloads(servidor, browser, pagina):
    """Requisito explícito da spec: estado só em memória — recarregar a
    página tem de repor todas as checkboxes por marcar, e nunca deve
    existir nenhuma chave de checklist em localStorage."""
    page = browser.new_page()
    page.route("https://cdn-cookieyes.com/**", lambda route: route.abort())
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    try:
        page.goto(f"{servidor}/{pagina}", wait_until="networkidle", timeout=30000)

        checkboxes = page.locator('.checklist-final input[type="checkbox"]')
        checkboxes.nth(0).check()
        assert checkboxes.nth(0).is_checked()

        tamanho_local_storage = page.evaluate("Object.keys(window.localStorage).length")
        assert tamanho_local_storage == 0, f"{pagina}: localStorage não devia ter nenhuma chave"

        page.reload(wait_until="networkidle")
        checkboxes = page.locator('.checklist-final input[type="checkbox"]')
        assert not checkboxes.nth(0).is_checked(), f"{pagina}: checkbox sobreviveu a um reload"

        progresso = page.locator(".checklist-final .checklist-progresso").first
        total = checkboxes.count()
        assert progresso.inner_text().strip() == f"0 de {total} concluídos"
    finally:
        page.close()
