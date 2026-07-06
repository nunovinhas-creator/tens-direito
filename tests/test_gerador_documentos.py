"""
Golden tests do Gerador de Documentos (Sessão 1 —
PROMPTGERADORDOCUMENTOSv1.md). Corre com Chromium real (Playwright)
sobre as páginas reais em documentos/, servidas por um http.server
local — nunca file://, mesmo motivo já documentado em
test_acessibilidade.py (caminhos absolutos "/assets/..." não carregam
sob file://).

Critérios de aceitação cobertos (secção "TESTES" do prompt):
  - preencher com dados de exemplo -> gerar -> output contém todos os
    campos preenchidos;
  - campo obrigatório vazio -> não gera + mensagem de erro visível;
  - validação de padrão (NISS != 11 dígitos) -> erro;
  - disclaimer presente na página E no texto gerado;
  - botão Copiar existe e fica activo após geração;
  - zero pedidos de rede depois do load ao interagir com o gerador.

Genérico sobre as 3 páginas (nunca hardcoded por minuta) — lê
CONFIG_DOCUMENTO directamente do browser, mesma filosofia de
test_simulador_csi_calculo.py (nunca uma cópia do JS/config).
"""
from __future__ import annotations

import glob
import http.server
import os
import socket
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent

PAGINAS_MINUTA = [
    "documentos/reclamacao-decisao-seguranca-social.html",
    "documentos/carta-acompanhamento-csi.html",
    "documentos/carta-acompanhamento-reavaliacao-abono.html",
]

DISCLAIMER = "Este documento é um modelo informativo e não substitui aconselhamento jurídico."


def _localizar_chromium():
    """Mesma busca em cascata (env var -> sandbox -> CI) documentada em
    test_acessibilidade.py/test_simulador_psu_calculo.py."""
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


def _abrir(browser, base_url, rel):
    page = browser.new_page()
    page.route("https://cdn-cookieyes.com/**", lambda route: route.abort())
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    page.goto(f"{base_url}/{rel}", wait_until="networkidle", timeout=30000)
    return page


def _valor_exemplo(campo, *, niss_valido="12345678901"):
    tipo = campo.get("tipo", "text")
    if campo["id"] == "niss":
        return niss_valido
    if tipo == "select":
        opcoes = campo.get("opcoes") or []
        return opcoes[0] if opcoes else ""
    if tipo == "date":
        return "2026-01-15"
    if tipo == "textarea":
        return "Texto de teste com informação suficiente para preencher este campo."
    return "Texto de teste"


def _data_pt(iso):
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


def _preencher_campo(page, campo, valor):
    seletor = f"#campo-{campo['id']}"
    tipo = campo.get("tipo", "text")
    if tipo == "select":
        if valor:
            page.select_option(seletor, label=valor)
    else:
        page.fill(seletor, valor)


def _preencher_tudo(page, config, excepto=None):
    for campo in config["campos"]:
        if campo["id"] == excepto:
            continue
        _preencher_campo(page, campo, _valor_exemplo(campo))


def _submeter(page, config):
    page.click(f"#form-{config['id']} button[type=submit]")


@pytest.mark.parametrize("rel", PAGINAS_MINUTA)
def test_formulario_preenchido_gera_documento_com_todos_os_campos(servidor, browser, rel):
    page = _abrir(browser, servidor, rel)
    config = page.evaluate("CONFIG_DOCUMENTO")
    _preencher_tudo(page, config)
    _submeter(page, config)
    page.wait_for_selector(f"#resultado-{config['id']}.show", timeout=5000)
    texto = page.inner_text(f"#texto-gerado-{config['id']}")

    for campo in config["campos"]:
        valor = _valor_exemplo(campo)
        if campo.get("tipo") == "date":
            valor = _data_pt(valor)
        assert valor in texto, (
            f"{rel}: valor de exemplo do campo '{campo['id']}' não aparece no texto gerado"
        )
    page.close()


@pytest.mark.parametrize("rel", PAGINAS_MINUTA)
def test_campo_obrigatorio_vazio_nao_gera_e_mostra_erro(servidor, browser, rel):
    page = _abrir(browser, servidor, rel)
    config = page.evaluate("CONFIG_DOCUMENTO")
    obrigatorios = [c for c in config["campos"] if c.get("obrigatorio")]
    assert obrigatorios, f"{rel}: nenhum campo obrigatório na config — verificar CONFIG_DOCUMENTO"

    alvo = obrigatorios[0]
    _preencher_tudo(page, config, excepto=alvo["id"])
    _submeter(page, config)

    # nunca gera com um obrigatório vazio
    assert "show" not in (page.get_attribute(f"#resultado-{config['id']}", "class") or "")
    erro = page.inner_text(f"#erro-{alvo['id']}")
    assert erro.strip(), f"{rel}: campo obrigatório '{alvo['id']}' vazio não mostrou mensagem de erro"
    resumo = page.inner_text(".gerador-erro-resumo")
    assert resumo.strip(), f"{rel}: resumo de erros vazio"
    page.close()


def test_niss_invalido_mostra_erro_de_padrao(servidor, browser):
    rel = "documentos/reclamacao-decisao-seguranca-social.html"
    page = _abrir(browser, servidor, rel)
    config = page.evaluate("CONFIG_DOCUMENTO")
    _preencher_tudo(page, config)
    page.fill("#campo-niss", "123")  # inválido: não tem 11 dígitos
    _submeter(page, config)

    assert "show" not in (page.get_attribute(f"#resultado-{config['id']}", "class") or "")
    erro = page.inner_text("#erro-niss")
    assert "11 dígitos" in erro
    page.close()


@pytest.mark.parametrize("rel", PAGINAS_MINUTA)
def test_disclaimer_presente_na_pagina_e_no_texto_gerado(servidor, browser, rel):
    page = _abrir(browser, servidor, rel)
    html = page.content()
    assert DISCLAIMER in html, f"{rel}: disclaimer em falta na página"

    config = page.evaluate("CONFIG_DOCUMENTO")
    _preencher_tudo(page, config)
    _submeter(page, config)
    page.wait_for_selector(f"#resultado-{config['id']}.show", timeout=5000)
    texto = page.inner_text(f"#texto-gerado-{config['id']}")
    assert DISCLAIMER in texto, f"{rel}: disclaimer em falta no texto gerado"
    page.close()


@pytest.mark.parametrize("rel", PAGINAS_MINUTA)
def test_botao_copiar_existe_e_fica_activo_apos_gerar(servidor, browser, rel):
    page = _abrir(browser, servidor, rel)
    config = page.evaluate("CONFIG_DOCUMENTO")
    botao = page.locator(f"#btn-copiar-{config['id']}")
    assert botao.count() == 1
    assert botao.is_disabled()

    _preencher_tudo(page, config)
    _submeter(page, config)
    page.wait_for_selector(f"#resultado-{config['id']}.show", timeout=5000)
    assert not botao.is_disabled(), f"{rel}: botão Copiar continua desactivado depois de gerar"

    botao_descarregar = page.locator(f"#btn-descarregar-{config['id']}")
    assert not botao_descarregar.is_disabled()
    page.close()


def test_consistencia_hub_documentos():
    """Cada card em /documentos.html aponta para uma página que existe,
    e cada minuta tem link de volta para o hub — mesmo espírito do
    hub de simuladores (sem teste equivalente ainda no repositório)."""
    import re

    html_hub = (RAIZ / "documentos.html").read_text(encoding="utf-8")
    hrefs_cards = re.findall(r'class="doc-card[^"]*">.*?href="([^"]+)"', html_hub, re.DOTALL)
    assert len(hrefs_cards) == len(PAGINAS_MINUTA)
    for href in hrefs_cards:
        assert (RAIZ / href.lstrip("/")).exists(), f"card do hub aponta para '{href}', sem ficheiro"
        assert href.lstrip("/") in PAGINAS_MINUTA

    for rel in PAGINAS_MINUTA:
        html_minuta = (RAIZ / rel).read_text(encoding="utf-8")
        assert 'href="/documentos.html"' in html_minuta, f"{rel}: sem link de volta ao hub /documentos.html"


@pytest.mark.parametrize("rel", PAGINAS_MINUTA)
def test_zero_pedidos_de_rede_ao_interagir_com_o_gerador(servidor, browser, rel):
    page = _abrir(browser, servidor, rel)
    config = page.evaluate("CONFIG_DOCUMENTO")

    pedidos = []
    page.on("request", lambda req: pedidos.append(req.url))

    _preencher_tudo(page, config)
    _submeter(page, config)
    page.wait_for_selector(f"#resultado-{config['id']}.show", timeout=5000)
    page.click(f"#btn-copiar-{config['id']}")
    page.click(f"#btn-descarregar-{config['id']}")
    page.wait_for_timeout(200)

    assert pedidos == [], (
        f"{rel}: {len(pedidos)} pedido(s) de rede ao interagir com o gerador (esperava zero): {pedidos}"
    )
    page.close()
