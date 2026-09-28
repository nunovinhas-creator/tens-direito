"""
Testes de ponta-a-ponta de simulador-universal.html (PR 11 da série
"simulador universal"): o assistente percorrido como um utilizador, num
Chromium headless real, servido por um http.server local (nunca file:// —
só assim o fetch('/dados/condicoes.json') resolve como um pedido real).

Cobre: a página lê mesmo dados/condicoes.json (nenhuma lista de apoios no
HTML); ordem das perguntas (rendimentos no fim, criança só com filhos); os
três grupos de resultado; aviso do filho mais novo; aviso RSI → PSU com a
data vinda dos dados; falha a carregar dados mostra erro e nunca "sem
direito"; Voltar; número negativo rejeitado; Recomeçar limpa tudo.

Uma única instância de browser por módulo (cada teste abre um contexto
novo) — é o que mantém o custo destes testes baixo no CI.

Se o Chromium do Playwright não estiver disponível, o módulo é ignorado.
"""
import glob
import http.server
import json
import os
import socket
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PAGINA = "simulador-universal.html"
CONDICOES = json.loads((RAIZ / "dados" / "condicoes.json").read_text(encoding="utf-8"))
PARAMETROS = json.loads((RAIZ / "dados" / "parametros.json").read_text(encoding="utf-8"))
PERGUNTAS = CONDICOES["perguntas"]


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

pytestmark = pytest.mark.skipif(
    not (_PLAYWRIGHT_DISPONIVEL and _CHROMIUM_PATH),
    reason="Playwright/Chromium não disponível neste ambiente",
)


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _SemLog(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def servidor():
    porta = _porta_livre()
    handler = lambda *a, **kw: _SemLog(*a, directory=str(RAIZ), **kw)  # noqa: E731
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


def _abrir(browser, servidor, rotas=None):
    contexto = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    # Escolha de cookies já feita ("recusado"): sem o banner fixo por cima dos
    # botões, cada clique deixa de esperar ~2 s pelas novas tentativas do
    # Playwright — é o que mantém este módulo rápido no CI.
    contexto.add_init_script("try { localStorage.setItem('td_consentimento', 'recusado'); } catch (e) {}")
    page = contexto.new_page()
    # Nada sai da máquina de teste (GA4, fontes) — só o servidor local.
    page.route("**/*", lambda r: r.continue_() if r.request.url.startswith(servidor) else r.abort())
    for padrao, handler in (rotas or {}).items():
        page.route(padrao, handler)
    page.goto(f"{servidor}/{PAGINA}")
    return contexto, page


@pytest.fixture()
def pagina(browser, servidor):
    contexto, page = _abrir(browser, servidor)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null", timeout=10000)
    yield page
    contexto.close()


def _estado(page):
    return page.evaluate(
        "({respostas: {...window.simuladorUniversal.respostas},"
        " historico: [...window.simuladorUniversal.historico],"
        " campoAtual: window.simuladorUniversal.campoAtual})"
    )


RESPOSTAS_PADRAO = {
    "data_nascimento_requerente": "1990-01-01",
    "data_nascimento_crianca": "2020-05-01",
    "tem_filhos_a_cargo": "sim",
}


def _valor_para(campo, respostas_fixas):
    if campo in respostas_fixas:
        return respostas_fixas[campo]
    d = PERGUNTAS[campo]
    if d["tipo"] == "categorica":
        return d["opcoes"][0]
    if d["tipo"] == "data":
        return "1990-01-01"
    return 0


def _responder_atual(page, respostas_fixas=RESPOSTAS_PADRAO):
    """Responde à pergunta actual como um utilizador (clique ou teclado)."""
    campo = _estado(page)["campoAtual"]
    valor = _valor_para(campo, respostas_fixas)
    n_antes = len(_estado(page)["historico"])
    if PERGUNTAS[campo]["tipo"] == "categorica":
        page.click(f"#opcoes button[data-valor='{valor}']")
    else:
        page.fill("#campoResposta", str(valor))
        page.click("#btnContinuar")
    page.wait_for_function(f"window.simuladorUniversal.historico.length === {n_antes + 1}")
    return campo


def _percorrer_ate_ao_fim(page, respostas_fixas=RESPOSTAS_PADRAO, limite=80):
    ordem = []
    for _ in range(limite):
        if page.is_visible("#resultados"):
            return ordem
        ordem.append(_responder_atual(page, respostas_fixas))
    raise AssertionError("o assistente não terminou")


def _cartoes(page, grupo_id):
    return page.eval_on_selector_all(
        f"#{grupo_id} li.apoio-card",
        "els => els.map(e => ({apoio: e.dataset.apoio, motivo: e.querySelector('.apoio-motivo').textContent,"
        " link: e.querySelector('a').getAttribute('href')}))",
    )


# ── Dados ────────────────────────────────────────────────────────────────


def test_le_mesmo_condicoes_json_e_nao_tem_apoios_no_html(browser, servidor):
    pedidos = []
    contexto, page = _abrir(browser, servidor)
    page.on("request", lambda r: pedidos.append(r.url))
    page.reload()
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    assert any(u.endswith("/dados/condicoes.json") for u in pedidos)

    primeiro = _estado(page)["campoAtual"]
    assert page.inner_text("#perguntaTexto") == PERGUNTAS[primeiro]["pergunta"]

    page.click("#btnVerResultados")
    page.wait_for_selector("#resultados:not([hidden])")
    mostrados = {c["apoio"] for c in _cartoes(page, "grupoIndeterminado")}
    assert mostrados == set(CONDICOES["apoios"]), "sem respostas, todos os apoios dos dados ficam em «Falta saber»"
    contexto.close()

    html = (RAIZ / PAGINA).read_text(encoding="utf-8")
    for apoio in CONDICOES["apoios"].values():
        assert apoio["titulo"] not in html, f"'{apoio['titulo']}' escrito no HTML — a lista tem de vir dos dados"


def test_apoio_novo_nos_dados_aparece_sem_tocar_na_pagina(browser, servidor):
    dados = json.loads(json.dumps(CONDICOES))
    dados["apoios"]["apoio-de-teste"] = {
        "titulo": "Apoio de Teste Inventado",
        "simulador": "/simuladores.html",
        "tipo_link": "guia",
        "operador": "all",
        "condicoes": [{"id": "x", "tipo": "categorica", "campo": "reside_legalmente_pt",
                       "operador_comparacao": "eq", "valor": "sim"}],
    }
    rotas = {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                            body=json.dumps(dados))}
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    page.click("#btnVerResultados")
    assert "Apoio de Teste Inventado" in page.inner_text("#grupoIndeterminado")
    contexto.close()


# ── Texto do link (PR 12): "simulador dedicado" só para simuladores ────────

TEXTO_LINK = {"simulador": "Abrir o simulador dedicado →", "guia": "Ler o guia completo →"}


def _links(page):
    return page.eval_on_selector_all(
        "li.apoio-card",
        "els => Object.fromEntries(els.map(e => [e.dataset.apoio,"
        " e.querySelector('a') ? {href: e.querySelector('a').getAttribute('href'),"
        " texto: e.querySelector('a').textContent} : null]))",
    )


def test_texto_do_link_segue_o_tipo_link_dos_dados(pagina):
    pagina.click("#btnVerResultados")
    pagina.wait_for_selector("#resultados:not([hidden])")
    links = _links(pagina)
    assert set(links) == set(CONDICOES["apoios"])
    tipos = {a["tipo_link"] for a in CONDICOES["apoios"].values()}
    assert tipos == {"simulador", "guia"}, "os dados reais têm de cobrir os dois tipos"
    for apoio_id, apoio in CONDICOES["apoios"].items():
        assert links[apoio_id] == {"href": apoio["simulador"], "texto": TEXTO_LINK[apoio["tipo_link"]]}, apoio_id
    assert links["creche"]["texto"] == "Ler o guia completo →"


def test_tipo_link_desconhecido_nao_mostra_link_nenhum(browser, servidor):
    dados = json.loads(json.dumps(CONDICOES))
    dados["apoios"]["creche"]["tipo_link"] = "inventado"
    del dados["apoios"]["abono"]["tipo_link"]
    rotas = {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                            body=json.dumps(dados))}
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    page.click("#btnVerResultados")
    links = _links(page)
    assert links["creche"] is None and links["abono"] is None
    assert links["csi"]["texto"] == TEXTO_LINK["simulador"]
    contexto.close()


def test_faq_explica_os_dois_destinos_do_link():
    html = (RAIZ / PAGINA).read_text(encoding="utf-8")
    frase = "ou para o guia completo quando o apoio não tem simulador"
    assert html.count(frase) == 2, "FAQ visível e JSON-LD têm de dizer o mesmo"


# ── PR 12 (revisão): indeterminado sem pergunta em falta mostra o motivo ─


def _so_creche():
    dados = json.loads(json.dumps(CONDICOES))
    dados["apoios"] = {"creche": dados["apoios"]["creche"]}
    return {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                           body=json.dumps(dados))}


def _nascimento_com_3_anos():
    # 3 anos e ~3 meses à data real em que o teste corre: sempre na zona
    # indeterminada (a página usa a data do dia, não uma data fixa).
    from datetime import date, timedelta
    hoje = date.today()
    return (hoje.replace(year=hoje.year - 3) - timedelta(days=90)).isoformat()


def test_creche_com_3_anos_mostra_o_motivo_dos_dados(browser, servidor):
    contexto, page = _abrir(browser, servidor, _so_creche())
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    _percorrer_ate_ao_fim(page, {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": _nascimento_com_3_anos()})
    cartoes = _cartoes(page, "grupoIndeterminado")
    assert [c["apoio"] for c in cartoes] == ["creche"]
    motivo = CONDICOES["apoios"]["creche"]["condicoes"][-1]["motivo_indeterminado"]
    assert cartoes[0]["motivo"] == f"Não é possível decidir: {motivo}. Confirma no guia completo."
    assert not page.is_visible("#btnContinuarResponder"), "nenhuma resposta muda isto — não há mais perguntas"
    contexto.close()


# ── Ordem das perguntas ──────────────────────────────────────────────────


def _monetario(campo):
    return "EUR" in str(PERGUNTAS[campo].get("unidade", ""))


def _da_crianca(campo):
    return (PERGUNTAS[campo].get("aplicavel_se") or {}).get("campo") == "tem_filhos_a_cargo"


def test_ordem_rendimentos_no_fim_e_crianca_so_com_filhos(pagina):
    ordem = _percorrer_ate_ao_fim(pagina)
    monetarios = [i for i, c in enumerate(ordem) if _monetario(c)]
    nao_monetarios = [i for i, c in enumerate(ordem) if not _monetario(c)]
    assert monetarios, "esperava perguntas de rendimentos"
    assert max(nao_monetarios) < min(monetarios), f"rendimentos têm de ficar no fim: {ordem}"
    crianca = [i for i, c in enumerate(ordem) if _da_crianca(c)]
    assert crianca and min(crianca) > ordem.index("tem_filhos_a_cargo")

    pagina.click("#btnRecomecar")
    sem_filhos = _percorrer_ate_ao_fim(pagina, {**RESPOSTAS_PADRAO, "tem_filhos_a_cargo": "nao"})
    assert not [c for c in sem_filhos if _da_crianca(c)], "perguntou pela criança a quem não tem filhos"


# ── Resultados ───────────────────────────────────────────────────────────


def test_tres_grupos_por_ordem_com_motivo_e_link(pagina):
    for _ in range(4):
        _responder_atual(pagina)
    pagina.click("#btnVerResultados")
    pagina.wait_for_selector("#resultados:not([hidden])")
    assert _cartoes(pagina, "grupoIndeterminado"), "a meio, tem de haver apoios em «Falta saber»"
    assert pagina.is_visible("#btnContinuarResponder")

    pagina.click("#btnContinuarResponder")
    pagina.wait_for_selector("#assistente:not([hidden])")
    _percorrer_ate_ao_fim(pagina)
    assert not pagina.is_visible("#btnContinuarResponder"), "sem perguntas em falta, «Continuar a responder» some"

    titulos = pagina.eval_on_selector_all("#resultados .grupo h3", "els => els.map(e => e.textContent.trim())")
    assert titulos == ["Provavelmente tens direito", "Falta saber", "Não tens direito"]
    elegiveis = _cartoes(pagina, "grupoElegivel")
    inelegiveis = _cartoes(pagina, "grupoInelegivel")
    assert elegiveis and inelegiveis
    for cartao in elegiveis + inelegiveis:
        assert cartao["motivo"].strip()
        assert cartao["link"] == CONDICOES["apoios"][cartao["apoio"]]["simulador"]
    # O motivo de um "Não tens direito" cita a pergunta que o excluiu.
    assert any("«" in c["motivo"] for c in inelegiveis)


def test_aviso_filho_mais_novo_so_com_filhos(pagina):
    _percorrer_ate_ao_fim(pagina)
    assert pagina.is_visible("#avisoFilhos")
    assert "Tens mais filhos?" in pagina.inner_text("#avisoFilhos")
    assert "filho mais novo" in pagina.inner_text("#avisoFilhos")

    pagina.click("#btnRecomecar")
    _percorrer_ate_ao_fim(pagina, {**RESPOSTAS_PADRAO, "tem_filhos_a_cargo": "nao"})
    assert not pagina.is_visible("#avisoFilhos")


def _data_pt(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def test_aviso_rsi_psu_usa_a_data_dos_dados(browser, servidor):
    data = CONDICOES["apoios"]["rsi"]["substituido_a_partir_de"]
    assert data == PARAMETROS["prestacoes"]["psu"]["data_producao_efeitos"]["valor"]

    contexto, page = _abrir(browser, servidor)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    page.click("#btnVerResultados")
    aviso = page.inner_text("[data-substituido='rsi']")
    assert _data_pt(data) in aviso and "PSU" in aviso
    contexto.close()

    # Mudar a data nos dados muda o aviso — nada hard-coded na página.
    dados = json.loads(json.dumps(CONDICOES))
    dados["apoios"]["rsi"]["substituido_a_partir_de"] = "2031-03-15"
    rotas = {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                            body=json.dumps(dados))}
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    page.click("#btnVerResultados")
    assert "15/03/2031" in page.inner_text("[data-substituido='rsi']")
    contexto.close()


@pytest.mark.parametrize("falha", ["abort", "http500"])
def test_falha_a_carregar_dados_mostra_erro_e_nunca_sem_direito(browser, servidor, falha):
    def handler(rota):
        if falha == "abort":
            rota.abort()
        else:
            rota.fulfill(status=500, body="erro")

    contexto, page = _abrir(browser, servidor, {"**/dados/condicoes.json": handler})
    page.wait_for_selector("#avisoErro:not([hidden])", timeout=10000)
    assert not page.is_visible("#assistente")
    assert not page.is_visible("#resultados")
    assert not page.is_visible("#carregando")
    assert "Isto não quer dizer que não tenhas direito" in page.inner_text("#avisoErro")
    contexto.close()


# ── Navegação do assistente ──────────────────────────────────────────────


def test_voltar_desfaz_a_ultima_resposta(pagina):
    primeiro = _responder_atual(pagina)
    segundo = _responder_atual(pagina)
    assert _estado(pagina)["historico"] == [primeiro, segundo]

    pagina.click("#btnVoltar")
    estado = _estado(pagina)
    assert estado["historico"] == [primeiro]
    assert estado["campoAtual"] == segundo
    assert segundo not in estado["respostas"]
    assert pagina.inner_text("#perguntaTexto") == PERGUNTAS[segundo]["pergunta"]

    pagina.click("#btnVoltar")
    assert _estado(pagina)["historico"] == []
    assert pagina.is_disabled("#btnVoltar")


def test_numero_negativo_rejeitado_sem_avancar(pagina):
    for _ in range(30):
        campo = _estado(pagina)["campoAtual"]
        if PERGUNTAS[campo]["tipo"] == "numero":
            break
        _responder_atual(pagina)
    else:
        raise AssertionError("nunca chegou a uma pergunta numérica")

    antes = _estado(pagina)
    pagina.fill("#campoResposta", "-5")
    pagina.click("#btnContinuar")
    assert "igual ou superior a 0" in pagina.inner_text("#erroResposta")
    depois = _estado(pagina)
    assert depois["campoAtual"] == campo
    assert depois["historico"] == antes["historico"]
    assert campo not in depois["respostas"]


def test_recomecar_limpa_respostas_e_historico(pagina):
    _responder_atual(pagina)
    _responder_atual(pagina)
    assert len(_estado(pagina)["historico"]) == 2
    pagina.click("#btnVerResultados")
    pagina.wait_for_selector("#resultados:not([hidden])")
    pagina.click("#btnRecomecar")
    estado = _estado(pagina)
    assert estado["respostas"] == {}
    assert estado["historico"] == []
    assert pagina.is_visible("#assistente")
    assert not pagina.is_visible("#resultados")


def test_script_da_pagina_nao_polui_o_ambito_global(pagina):
    # O IIFE existe para que pesquisa.js (mostrarResultados global) não
    # sobreponha funções da página — nada da página fica global além do
    # objecto de testes.
    assert pagina.evaluate("typeof mostrarResultadosSimulador") == "undefined"
    assert pagina.evaluate("typeof CONDICOES") == "undefined"
    assert pagina.evaluate("typeof window.mostrarResultados") == "function"  # o de pesquisa.js, intacto


# ── Carimbo "Verificado a" ───────────────────────────────────────────────


def test_carimbo_verificado_vem_dos_dados_e_nao_da_data_de_hoje(browser, servidor):
    contexto, page = _abrir(browser, servidor)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    assert page.is_visible("#carimboVerificacao")
    assert page.inner_text("#dataVerificacao") == "Verificado a " + _data_pt(CONDICOES["verificado_em"])
    contexto.close()

    # Outra data nos dados → outro carimbo; nada escrito à mão na página.
    dados = json.loads(json.dumps(CONDICOES))
    dados["verificado_em"] = "2025-01-15"
    rotas = {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                            body=json.dumps(dados))}
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    assert page.inner_text("#dataVerificacao") == "Verificado a 15/01/2025"
    contexto.close()

    # Sem data nos dados, ou sem dados, o carimbo não aparece — nunca uma data inventada.
    dados["verificado_em"] = None
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    assert not page.is_visible("#carimboVerificacao")
    contexto.close()
    contexto, page = _abrir(browser, servidor, {"**/dados/condicoes.json": lambda r: r.abort()})
    page.wait_for_selector("#avisoErro:not([hidden])")
    assert not page.is_visible("#carimboVerificacao")
    contexto.close()


def test_carimbo_estatico_bate_com_os_dados_e_com_o_date_modified():
    # O HTML traz a data já escrita (para quem lê a página sem JS e para os
    # testes de carimbo/coerência, que lêem o fonte), mas nunca à mão: tem de
    # ser sempre o verificado_em de dados/condicoes.json. Ao regenerar os
    # dados com outra data, este teste obriga a actualizar os dois sítios.
    import re

    html = (RAIZ / "simulador-universal.html").read_text(encoding="utf-8")
    m = re.search(r'<strong id="dataVerificacao">Verificado a ([^<]*)</strong>', html)
    assert m, "#dataVerificacao com 'Verificado a <data>' não encontrado"
    assert m.group(1) == _data_pt(CONDICOES["verificado_em"])
    assert f'"dateModified": "{CONDICOES["verificado_em"]}"' in html
