"""
Barra do topo (BARRA-TOPO) — próximo pagamento + canal de WhatsApp, em
todas as páginas.

Duas metades:

1. Estática, sobre as páginas REAIS (mesmo padrão de test_nav_coerencia.py,
   parametrizado — uma página nova fica coberta sozinha): exactamente um
   bloco por página, logo a seguir ao skip-link, igual ao que o
   sincronizar_nav.py geraria; link do canal com utm_content=barra_topo;
   modo estático no gerador de documentos; zonas da REGRA DE OURO intactas
   (o sincronizar_nav.py nunca toca nas zonas do pipeline, o
   atualizar_calendario.py só toca na zona CAL-HOME e no JSON autorizado).
2. Chromium real (http.server, nunca file://), com relógio fixo: sem JS,
   prefers-reduced-motion, rotação com pausa ao hover/foco/botão, nunca uma
   data passada, falha do fetch, evento GA4 e rede-zero no gerador.
"""
from __future__ import annotations

import datetime as dt
import functools
import glob
import http.server
import json
import os
import re
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from atualizar_calendario import (  # noqa: E402
    BARRA_JSON,
    atualizar_homepage,
    carregar_dados,
)
from sincronizar_clusters import CLUSTERS_JSON, carregar_clusters, encontrar_paginas  # noqa: E402
from sincronizar_nav import (  # noqa: E402
    URL_DADOS_BARRA,
    barra_estatica,
    bootstrap_barra,
    render_barra_topo,
    sincronizar_conteudo,
)

PAGINAS = sorted(encontrar_paginas(), key=lambda p: str(p))
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]
CLUSTERS = carregar_clusters(CLUSTERS_JSON)

_RE_BLOCO = re.compile(r"<!-- BARRA-TOPO:INICIO -->\n([\s\S]*?)\n<!-- BARRA-TOPO:FIM -->")
_RE_WHATSAPP = re.compile(r'<a class="barra-topo-msg" data-destino="whatsapp" href="([^"]+)"([^>]*)>')
UTM_BARRA = (
    "https://whatsapp.com/channel/0029VbDwKbZCsU9QFFWi3K1W"
    "?utm_source=tensdireito&amp;utm_medium=site&amp;utm_campaign=canal_whatsapp&amp;utm_content=barra_topo"
)


def _rel(caminho: Path) -> str:
    return str(caminho.relative_to(RAIZ))


def _bloco(html: str) -> str:
    m = _RE_BLOCO.search(html)
    assert m, "bloco BARRA-TOPO em falta"
    return m.group(1)


# ── 1. Páginas reais ──────────────────────────────────────────────────────


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_exactamente_um_bloco_igual_ao_gerado(caminho):
    html = caminho.read_text(encoding="utf-8")
    assert html.count("<!-- BARRA-TOPO:INICIO -->") == 1
    assert html.count("<!-- BARRA-TOPO:FIM -->") == 1
    assert _bloco(html) == "  " + render_barra_topo(barra_estatica(_rel(caminho))), (
        f"{_rel(caminho)}: barra diferente da gerada — correr python scripts/sincronizar_nav.py"
    )


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_barra_logo_a_seguir_ao_skip_link_e_antes_da_nav(caminho):
    html = caminho.read_text(encoding="utf-8")
    skip = re.search(r'<a href="#main-content" class="skip-link">[^<]*</a>\n', html)
    assert skip, "skip-link em falta"
    assert html.index("<!-- BARRA-TOPO:INICIO -->") == skip.end() + 2  # 2 espaços de indentação
    assert html.index("<!-- BARRA-TOPO:FIM -->") < html.index("<!-- NAV:INICIO -->")


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_link_do_canal_com_utm_da_barra(caminho):
    links = _RE_WHATSAPP.findall(_bloco(caminho.read_text(encoding="utf-8")))
    assert len(links) == 1
    href, resto = links[0]
    assert href == UTM_BARRA
    assert 'target="_blank"' in resto and 'rel="noopener"' in resto


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_modo_estatico_so_no_gerador_de_documentos(caminho):
    html = caminho.read_text(encoding="utf-8")
    bloco = _bloco(html)
    if barra_estatica(_rel(caminho)):
        assert 'data-barra-modo="estatico"' in bloco
        assert 'data-destino="calendario"' not in bloco
        assert "barra-topo-pausa" not in bloco
        assert "data-barra-dados" not in bloco
        assert "hoje-lisboa.js" not in html
    else:
        assert f'data-barra-dados="{URL_DADOS_BARRA}"' in bloco
        assert re.search(r'<a class="barra-topo-msg" data-destino="calendario" href="[^"]+" hidden>', bloco)
        assert re.search(r'<button class="barra-topo-pausa"[^>]* hidden>', bloco)
        assert '<div class="barra-topo-mensagens" aria-live="off">' in bloco
        assert "/assets/js/hoje-lisboa.js" in html


def test_gerador_de_documentos_inteiro_em_modo_estatico():
    estaticas = {_rel(p) for p in PAGINAS if barra_estatica(_rel(p))}
    esperadas = {"documentos.html"} | {f"documentos/{p.name}" for p in (RAIZ / "documentos").glob("*.html")}
    assert estaticas == esperadas


def test_nenhum_resto_da_barra_antiga_da_homepage():
    for caminho in PAGINAS:
        html = caminho.read_text(encoding="utf-8")
        assert "cal-topo" not in html, _rel(caminho)
        assert "cal_home_clique" not in html, _rel(caminho)


def test_dados_da_barra_servidos_no_caminho_do_fetch():
    assert URL_DADOS_BARRA == "/" + BARRA_JSON.relative_to(RAIZ).as_posix()
    assert isinstance(json.loads(BARRA_JSON.read_text(encoding="utf-8")), dict)


# ── bootstrap ────────────────────────────────────────────────────────────


def test_bootstrap_insere_a_seguir_ao_skip_link():
    html = '<body>\n  <a href="#main-content" class="skip-link">Saltar para o conteúdo</a>\n  <!-- NAV:INICIO -->\n'
    novo, motivo = bootstrap_barra(html)
    assert novo == (
        '<body>\n  <a href="#main-content" class="skip-link">Saltar para o conteúdo</a>\n'
        "  <!-- BARRA-TOPO:INICIO -->\n  <!-- BARRA-TOPO:FIM -->\n  <!-- NAV:INICIO -->\n"
    )
    assert "bootstrap" in motivo


def test_bootstrap_recusa_sem_skip_link():
    novo, motivo = bootstrap_barra("<body>\n  <!-- NAV:INICIO -->\n")
    assert novo is None and "manual" in motivo


def test_bootstrap_recusa_com_a_barra_antiga_presente():
    html = ('<a href="#main-content" class="skip-link">Saltar</a>\n'
            '  <div class="cal-topo-regiao"><a class="cal-topo" href="/x">x</a></div>\n')
    novo, motivo = bootstrap_barra(html)
    assert novo is None and "manual" in motivo


# ── REGRA DE OURO: cada script só escreve nas suas zonas ──────────────────

_ZONAS_PIPELINE = ("DESTAQUE", "NOTICIA-HOME", "CAL-HOME")


def _trocar_zona(html: str, zona: str, conteudo: str) -> str:
    padrao = re.compile(rf"(<!-- {zona}:INICIO -->)[\s\S]*?(<!-- {zona}:FIM -->)")
    assert padrao.search(html), zona
    return padrao.sub(lambda m: f"{m.group(1)}\n{conteudo}\n{m.group(2)}", html)


def _sem_zona(html: str, zona: str) -> str:
    return re.sub(rf"<!-- {zona}:INICIO -->[\s\S]*?<!-- {zona}:FIM -->", f"<{zona}>", html)


def test_sincronizar_nav_nunca_toca_nas_zonas_do_pipeline_da_homepage():
    original = (RAIZ / "index.html").read_text(encoding="utf-8")
    entrada = original
    for zona in _ZONAS_PIPELINE:
        entrada = _trocar_zona(entrada, zona, f"SENTINELA-{zona}")
    entrada = re.sub(r'id="ultima-revisao-mes">[^<]*<', 'id="ultima-revisao-mes">SENTINELA-MES<', entrada)
    entrada = _trocar_zona(entrada, "BARRA-TOPO", "")  # barra por sincronizar
    saida, motivo = sincronizar_conteudo(entrada, "index.html", CLUSTERS)
    assert saida is not None, motivo
    for zona in _ZONAS_PIPELINE:
        assert f"<!-- {zona}:INICIO -->\nSENTINELA-{zona}\n<!-- {zona}:FIM -->" in saida, zona
    assert 'id="ultima-revisao-mes">SENTINELA-MES<' in saida
    # fora dos blocos NAV e BARRA-TOPO, a saída é a entrada byte a byte
    assert _sem_zona(_sem_zona(saida, "NAV"), "BARRA-TOPO") == _sem_zona(_sem_zona(entrada, "NAV"), "BARRA-TOPO")


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_sincronizar_nav_so_altera_nav_barra_e_head(caminho):
    """Página real com a barra por sincronizar: tudo o que muda fica dentro
    dos blocos NAV/BARRA-TOPO ou é a referência ao hoje-lisboa.js no <head>."""
    original = caminho.read_text(encoding="utf-8")
    entrada = _trocar_zona(original, "BARRA-TOPO", "")
    entrada = entrada.replace('  <script src="/assets/js/hoje-lisboa.js" defer></script>\n', "")
    saida, motivo = sincronizar_conteudo(entrada, _rel(caminho), CLUSTERS)
    assert saida == original, f"{_rel(caminho)}: {motivo}"


def test_atualizar_calendario_so_mexe_no_cal_home_da_homepage(tmp_path):
    original = (RAIZ / "index.html").read_text(encoding="utf-8")
    copia = tmp_path / "index.html"
    copia.write_text(_trocar_zona(original, "CAL-HOME", "    velho"), encoding="utf-8")
    assert atualizar_homepage(carregar_dados(), dt.date(2026, 11, 13), caminho=copia)
    saida = copia.read_text(encoding="utf-8")
    assert _sem_zona(saida, "CAL-HOME") == _sem_zona(original, "CAL-HOME")
    assert _bloco(saida) == _bloco(original)


def test_workflow_mensal_autoriza_e_commita_o_json_da_barra():
    wf = (RAIZ / ".github" / "workflows" / "calendario-mensal.yml").read_text(encoding="utf-8")
    rel = BARRA_JSON.relative_to(RAIZ).as_posix()
    assert f"              {rel}) ;;" in wf, "guardrail do calendario-mensal.yml não autoriza o JSON da barra"
    assert re.search(rf"git add [^\n]*{re.escape(rel)}", wf)


def test_pipeline_diario_nunca_escreve_a_barra():
    wf = (RAIZ / ".github" / "workflows" / "pipeline-diario.yml").read_text(encoding="utf-8")
    for proibido in ("calendario_barra", "sincronizar_nav", "atualizar_calendario", "BARRA-TOPO"):
        assert proibido not in wf, proibido
    sys.path.insert(0, str(RAIZ / "scripts"))
    import gerar_noticias
    assert "calendario_barra.json" not in gerar_noticias.FICHEIROS_AUTO_GERADOS


# ── 2. Chromium real ──────────────────────────────────────────────────────


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

ARTIGO = "/rsi.html"
MINUTA = "/documentos/carta-acompanhamento-csi.html"
# Relógio fixo e dados fixos (nunca os do mês real, que mudam todos os meses).
AGORA = dt.datetime(2026, 9, 10, 9, 0, tzinfo=dt.timezone.utc)
DADOS_SETEMBRO = {"2026-09": [{"dia": 3, "resumo": "Pensões"},
                              {"dia": 16, "resumo": "Abono e prestações familiares"},
                              {"dia": 30, "resumo": "RSI"}]}
CAL = '.barra-topo-msg[data-destino="calendario"]'
WA = '.barra-topo-msg[data-destino="whatsapp"]'
PAUSA = ".barra-topo-pausa"


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


def _abrir(browser, servidor, url, *, dados=DADOS_SETEMBRO, agora=AGORA, largura=375, **contexto):
    """Página com relógio controlado; o JSON da barra é servido com `dados`
    (None = pedido abortado; str = corpo tal e qual). Devolve (page, pedidos)."""
    ctx = browser.new_context(viewport={"width": largura, "height": 700}, **contexto)
    page = ctx.new_page()
    pedidos: list[str] = []
    page.on("request", lambda r: pedidos.append(r.url))
    page.route("https://www.googletagmanager.com/**", lambda r: r.abort())

    def _json(route):
        if dados is None:
            route.abort()
        else:
            corpo = dados if isinstance(dados, str) else json.dumps(dados)
            route.fulfill(status=200, content_type="application/json", body=corpo)
    page.route("**" + URL_DADOS_BARRA, _json)
    if contexto.get("java_script_enabled", True):
        page.clock.install(time=agora)
        # links da barra nunca saem da página durante o teste (o listener do
        # evento corre na mesma — preventDefault não pára a propagação)
        page.add_init_script("document.addEventListener('click', function (e) {"
                             " if (e.target.closest('.barra-topo-msg')) e.preventDefault(); }, true);")
    page.goto(servidor + url, wait_until="networkidle")
    page.evaluate("var c = document.getElementById('td-consent'); if (c) c.remove();")
    return page, pedidos


def _so_whatsapp(page):
    assert page.locator(WA).is_visible()
    assert page.locator(CAL).count() == 0 or page.locator(CAL).is_hidden()
    assert page.locator(PAUSA).count() == 0 or page.locator(PAUSA).is_hidden()


def _texto(page, seletor):
    return " ".join(page.locator(seletor).inner_text().split())


def _avancar(page, ms):
    page.clock.run_for(ms)
    page.wait_for_timeout(20)


@pytest.mark.parametrize("url", ["/index.html", ARTIGO, MINUTA])
def test_sem_js_mostra_so_o_whatsapp(browser, servidor, url):
    page, _ = _abrir(browser, servidor, url, java_script_enabled=False)
    _so_whatsapp(page)
    assert page.locator(WA).inner_text().strip().startswith("🔔")
    assert page.locator(".barra-topo-regiao").bounding_box()["height"] == 40
    page.context.close()


def test_reduced_motion_so_whatsapp_parado_e_sem_fetch(browser, servidor):
    page, pedidos = _abrir(browser, servidor, ARTIGO, reduced_motion="reduce")
    _avancar(page, 20000)
    _so_whatsapp(page)
    assert not any(URL_DADOS_BARRA in u for u in pedidos)
    page.context.close()


def test_roda_entre_as_duas_mensagens(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    assert page.locator(PAUSA).is_visible()
    assert page.locator(WA).is_visible() and page.locator(CAL).is_hidden()
    assert page.get_attribute(".barra-topo-mensagens", "aria-live") == "off"
    _avancar(page, 6500)
    assert page.locator(CAL).is_visible() and page.locator(WA).is_hidden()
    assert _texto(page, CAL) == "📅 Próximo pagamento: dia 16 →"
    _avancar(page, 6500)
    assert page.locator(WA).is_visible() and page.locator(CAL).is_hidden()
    page.context.close()


def test_ecra_largo_mostra_data_e_resumo(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO, largura=1200)
    _avancar(page, 6500)
    assert _texto(page, CAL) == (
        "📅 Próximo pagamento: 16 de setembro — Abono e prestações familiares →")
    page.context.close()


def test_telemovel_uma_linha_sem_overflow(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    for _ in range(2):
        assert page.locator(".barra-topo-regiao").bounding_box()["height"] == 40
        assert page.evaluate("document.documentElement.scrollWidth") <= 375
        _avancar(page, 6500)
    page.context.close()


# ── Posição: fixa só em ecrãs largos (>640px) ─────────────────────────────
# Em ecrãs estreitos a barra aparece no topo e sai com o scroll; só a nav
# fica fixa. O menu móvel fica sempre colado por baixo da nav (no topo da
# página e depois do scroll) e cabe no ecrã quando a nav está no topo. As
# âncoras passam o que estiver fixo: nav (+ barra, em ecrã largo) + 8px.
# Relações medidas na página, nunca alturas supostas — a nav tem 69px, não
# os 60px que o CSS antigo assumia. O menu começa no fundo da caixa interior
# da nav (top: 100%), por cima da borda de 1px.

_POSICOES = """() => {
    const r = el => document.querySelector(el).getBoundingClientRect();
    const menu = document.getElementById('navMobileMenu');
    const nav = document.querySelector('.nav-wrap');
    return {
        scroll: window.scrollY,
        alto: window.innerHeight,
        barra: r('.barra-topo-regiao').top,
        nav: r('.nav-wrap').top,
        navAltura: r('.nav-wrap').height,
        navInteriorFim: r('.nav-wrap').top + nav.clientTop + nav.clientHeight,
        navInterior: nav.clientHeight,
        menu: menu.getBoundingClientRect().top,
        menuFim: menu.getBoundingClientRect().bottom,
        padding: parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop),
    };
}"""


def _abrir_menu_comprido(page):
    """Abre o menu móvel e enche-o de conteúdo: a altura dele passa a ser a
    do max-height (o valor usado — o calculado fica em calc() com %)."""
    page.click(".nav-toggle")
    page.evaluate("""() => {
        const d = document.createElement('div');
        d.style.cssText = 'height: 3000px; flex: none';
        document.getElementById('navMobileMenu').appendChild(d);
    }""")


def _posicoes(page, scroll_y=None):
    if scroll_y is not None:
        page.evaluate(f"window.scrollTo({{top: {scroll_y}, behavior: 'instant'}})")
        page.wait_for_timeout(50)
    return page.evaluate(_POSICOES)


@pytest.mark.parametrize("url", [ARTIGO, "/index.html"])
def test_telemovel_barra_sai_com_o_scroll_e_so_a_nav_fica_fixa(browser, servidor, url):
    page, _ = _abrir(browser, servidor, url)
    _abrir_menu_comprido(page)  # antes de fazer scroll
    topo = _posicoes(page)
    assert topo["barra"] == 0 and topo["nav"] >= 40, topo  # na homepage o destaque fica pelo meio
    assert topo["menu"] == topo["navInteriorFim"], "menu móvel descolado da nav no topo da página"
    assert topo["padding"] == topo["navAltura"] + 8, "as âncoras só têm de passar a nav"
    # max-height = ecrã − nav: no topo da página o fim passa do ecrã (o scroll traz-o)
    assert topo["menuFim"] - topo["menu"] == topo["alto"] - topo["navInterior"]

    abaixo = _posicoes(page, 600)
    assert abaixo["scroll"] == 600
    assert abaixo["barra"] == -600, "a barra ficou fixa num ecrã estreito"
    assert abaixo["nav"] == 0, "a nav deixou de ficar fixa no topo"
    assert abaixo["menu"] == abaixo["navInteriorFim"], "menu móvel descolado da nav depois do scroll"
    assert abaixo["menuFim"] == abaixo["alto"], "o menu não acaba no fundo do ecrã"
    assert page.locator("#navMobileMenu").is_visible()
    page.context.close()


@pytest.mark.parametrize("largura", [700, 1200])
def test_ecra_largo_barra_e_nav_ficam_fixas(browser, servidor, largura):
    page, _ = _abrir(browser, servidor, ARTIGO, largura=largura)
    if largura == 700:  # o botão do menu móvel ainda aparece até 700px
        _abrir_menu_comprido(page)
    for scroll_y in (None, 600):
        pos = _posicoes(page, scroll_y)
        assert (pos["barra"], pos["nav"]) == (0, 40), pos
        assert pos["padding"] == 40 + pos["navAltura"] + 8, pos
        if largura == 700:
            assert pos["menu"] == pos["navInteriorFim"], pos
            assert pos["menuFim"] == pos["alto"], pos
    page.context.close()


def test_pausa_ao_hover(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    page.hover(WA)
    _avancar(page, 20000)
    assert page.locator(WA).is_visible()
    page.mouse.move(10, 600)
    _avancar(page, 6500)
    assert page.locator(CAL).is_visible()
    page.context.close()


def test_pausa_ao_foco(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    page.focus(WA)
    _avancar(page, 20000)
    assert page.locator(WA).is_visible()
    page.evaluate("document.activeElement.blur()")
    _avancar(page, 6500)
    assert page.locator(CAL).is_visible()
    page.context.close()


def test_botao_de_pausa_para_e_retoma(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    page.click(PAUSA)
    assert page.get_attribute(PAUSA, "aria-label") == "Retomar as mensagens"
    page.mouse.move(10, 600)
    page.evaluate("document.activeElement.blur()")
    _avancar(page, 20000)
    assert page.locator(WA).is_visible(), "rodou com a pausa activa"
    page.click(PAUSA)  # retoma mesmo com o rato e o foco no botão
    assert page.get_attribute(PAUSA, "aria-label") == "Pausar as mensagens"
    _avancar(page, 6500)
    assert page.locator(CAL).is_visible()
    page.context.close()


def test_ultimo_dia_do_mes_ainda_conta(browser, servidor):
    # 23h de 30/09 em Lisboa (22h UTC): o pagamento de hoje ainda é o próximo
    page, _ = _abrir(browser, servidor, ARTIGO,
                     agora=dt.datetime(2026, 9, 30, 22, 0, tzinfo=dt.timezone.utc))
    _avancar(page, 6500)
    assert _texto(page, CAL) == "📅 Próximo pagamento: dia 30 →"
    page.context.close()


@pytest.mark.parametrize("dados,agora", [
    (DADOS_SETEMBRO, dt.datetime(2026, 9, 30, 23, 30, tzinfo=dt.timezone.utc)),  # já 1/10 em Lisboa: setembro passou
    ({"2026-09": [{"dia": 3, "resumo": "Pensões"}]}, AGORA),                     # todos os pagamentos já passaram
    ({"2026-08": [{"dia": 20, "resumo": "Pensões"}]}, AGORA),                    # sem o mês corrente
    (None, AGORA),                                                               # fetch falhado
    ("{ inválido", AGORA),                                                       # JSON partido
], ids=["mes-seguinte-sem-dados", "tudo-pago", "mes-velho", "fetch-falha", "json-partido"])
def test_nunca_mostra_uma_data_passada(browser, servidor, dados, agora):
    page, _ = _abrir(browser, servidor, ARTIGO, dados=dados, agora=agora)
    _avancar(page, 20000)
    _so_whatsapp(page)
    assert "Próximo pagamento" not in page.locator(CAL).text_content()
    page.context.close()


def test_homepage_usa_os_dados_inline_sem_fetch(browser, servidor):
    page, pedidos = _abrir(browser, servidor, "/index.html",
                           agora=dt.datetime.combine(dt.date.today(), dt.time(9), tzinfo=dt.timezone.utc))
    assert not any(URL_DADOS_BARRA in u for u in pedidos)
    page.context.close()


def _eventos_barra(page):
    return page.evaluate("""(window.dataLayer || [])
        .filter(function (e) { return e && e[0] === 'event' && e[1] === 'barra_topo_clique'; })
        .map(function (e) { return e[2]; })""")


def test_evento_ga4_no_clique_so_com_o_destino(browser, servidor):
    page, _ = _abrir(browser, servidor, ARTIGO)
    page.click(WA)
    page.mouse.move(10, 600)
    page.evaluate("document.activeElement.blur()")
    _avancar(page, 6500)
    page.click(CAL)
    assert _eventos_barra(page) == [{"destino": "whatsapp"}, {"destino": "calendario"}]
    page.context.close()


def test_gerador_de_documentos_sem_fetch_nem_evento(browser, servidor):
    page, pedidos = _abrir(browser, servidor, MINUTA)
    page.click(WA)
    _avancar(page, 20000)
    _so_whatsapp(page)
    assert not any(URL_DADOS_BARRA in u or "hoje-lisboa" in u for u in pedidos), pedidos
    assert _eventos_barra(page) == []
    page.context.close()
