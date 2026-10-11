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


def _responder_ecra(page, respostas_fixas=RESPOSTAS_PADRAO):
    """Responde ao ecrã actual como um utilizador (clique ou teclado).
    Devolve os campos do ecrã — mais do que um quando é um grupo."""
    campos = page.evaluate("window.simuladorUniversal.camposAtuais")
    n_antes = page.evaluate("window.simuladorUniversal.ecras")
    if len(campos) > 1:
        for campo in campos:
            page.fill(f"#campo-{campo}", str(_valor_para(campo, respostas_fixas)))
        page.click("#btnContinuarConjunto")
    elif PERGUNTAS[campos[0]]["tipo"] == "categorica":
        page.click(f"#opcoes button[data-valor='{_valor_para(campos[0], respostas_fixas)}']")
    else:
        page.fill("#campoResposta", str(_valor_para(campos[0], respostas_fixas)))
        page.click("#btnContinuar")
    page.wait_for_function(f"window.simuladorUniversal.ecras === {n_antes + 1}")
    return campos


def _responder_atual(page, respostas_fixas=RESPOSTAS_PADRAO):
    return _responder_ecra(page, respostas_fixas)[0]


def _percorrer_ate_ao_fim(page, respostas_fixas=RESPOSTAS_PADRAO, limite=80):
    ordem = []
    for _ in range(limite):
        if page.is_visible("#resultados"):
            return ordem
        ordem.extend(_responder_ecra(page, respostas_fixas))
    raise AssertionError("o assistente não terminou")


def _cartoes(page, grupo_id):
    return page.eval_on_selector_all(
        f"#{grupo_id} li.apoio-card",
        "els => els.map(e => ({apoio: e.dataset.apoio, motivo: e.querySelector('.apoio-motivo').textContent,"
        " link: e.querySelector('a.apoio-link').getAttribute('href')}))",
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
        " e.querySelector('a.apoio-link') ? {href: e.querySelector('a.apoio-link').getAttribute('href'),"
        " texto: e.querySelector('a.apoio-link').textContent} : null]))",
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


def test_creche_com_4_anos_mostra_o_texto_proprio_e_nao_o_generico(browser, servidor):
    from datetime import date
    hoje = date.today()
    nascimento = hoje.replace(year=hoje.year - 5).isoformat()
    contexto, page = _abrir(browser, servidor, _so_creche())
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    _percorrer_ate_ao_fim(page, {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": nascimento})
    cartoes = _cartoes(page, "grupoInelegivel")
    assert [c["apoio"] for c in cartoes] == ["creche"]
    motivo = CONDICOES["apoios"]["creche"]["condicoes"][-1]["motivo_inelegivel"]
    assert cartoes[0]["motivo"] == motivo
    assert "Não cumpres" not in cartoes[0]["motivo"]
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
        sozinho = len(pagina.evaluate("window.simuladorUniversal.camposAtuais")) == 1
        if PERGUNTAS[campo]["tipo"] == "numero" and sozinho:
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


def _ate_ao_ecra_do_agregado(page, respostas_fixas=RESPOSTAS_PADRAO, limite=40):
    for _ in range(limite):
        if len(page.evaluate("window.simuladorUniversal.camposAtuais")) > 1:
            return
        _responder_ecra(page, respostas_fixas)
    raise AssertionError("nunca chegou ao ecrã do agregado")


GRUPO_AGREGADO = ["numero_adultos_adicionais_agregado", "numero_menores_agregado"]


def test_ecra_do_agregado_pergunta_adultos_e_menores_juntos(pagina):
    _ate_ao_ecra_do_agregado(pagina)
    assert pagina.evaluate("window.simuladorUniversal.camposAtuais") == GRUPO_AGREGADO
    titulo = PERGUNTAS[GRUPO_AGREGADO[0]]["grupo"]["titulo"]
    assert pagina.inner_text("#perguntaTexto") == titulo
    assert pagina.get_attribute("#perguntaTexto", "for") is None
    assert not pagina.is_visible("#campoLinha") and not pagina.is_visible("#opcoes")
    for campo in GRUPO_AGREGADO:
        rotulo = pagina.inner_text(f"label[for='campo-{campo}']")
        assert rotulo == PERGUNTAS[campo]["pergunta"]
        assert pagina.get_attribute(f"#campo-{campo}", "type") == "number"
    assert pagina.evaluate("document.activeElement.id") == f"campo-{GRUPO_AGREGADO[0]}"


def test_ecra_do_agregado_so_avanca_com_os_dois_numeros_validos(pagina):
    _ate_ao_ecra_do_agregado(pagina)
    antes = _estado(pagina)
    pagina.fill(f"#campo-{GRUPO_AGREGADO[0]}", "1")
    pagina.click("#btnContinuarConjunto")
    assert pagina.inner_text("#erroResposta") == "Indica um número."
    assert pagina.evaluate("document.activeElement.id") == f"campo-{GRUPO_AGREGADO[1]}"
    pagina.fill(f"#campo-{GRUPO_AGREGADO[1]}", "-1")
    pagina.click("#btnContinuarConjunto")
    assert "igual ou superior a 0" in pagina.inner_text("#erroResposta")
    depois = _estado(pagina)
    assert depois["historico"] == antes["historico"]
    assert not set(GRUPO_AGREGADO) & set(depois["respostas"])

    pagina.fill(f"#campo-{GRUPO_AGREGADO[1]}", "2")
    pagina.click("#btnContinuarConjunto")
    pagina.wait_for_function(f"window.simuladorUniversal.ecras === {len(antes['historico']) + 1}")
    respostas = _estado(pagina)["respostas"]
    assert respostas[GRUPO_AGREGADO[0]] == 1 and respostas[GRUPO_AGREGADO[1]] == 2


def test_voltar_desfaz_o_ecra_do_agregado_inteiro(pagina):
    _ate_ao_ecra_do_agregado(pagina)
    n = pagina.evaluate("window.simuladorUniversal.ecras")
    _responder_ecra(pagina)
    assert set(GRUPO_AGREGADO) <= set(_estado(pagina)["respostas"])
    pagina.click("#btnVoltar")
    estado = _estado(pagina)
    assert pagina.evaluate("window.simuladorUniversal.ecras") == n
    assert not set(GRUPO_AGREGADO) & set(estado["respostas"])
    assert pagina.evaluate("window.simuladorUniversal.camposAtuais") == GRUPO_AGREGADO
    assert pagina.is_visible(f"#campo-{GRUPO_AGREGADO[1]}")


def _etapas(page):
    return page.eval_on_selector_all(
        "#etapas li",
        "els => els.map(e => ({etapa: e.dataset.etapa, texto: e.textContent, oculta: e.hidden,"
        " feita: e.classList.contains('feita'), atual: e.getAttribute('aria-current')}))",
    )


def test_etapas_avancam_com_as_perguntas(pagina):
    etapas = _etapas(pagina)
    assert [e["texto"] for e in etapas] == ["Sobre ti", "O teu filho mais novo", "Rendimentos e poupanças"]
    assert etapas[0]["atual"] == "step" and not any(e["feita"] for e in etapas)

    vistas = set()
    for _ in range(80):
        if pagina.is_visible("#resultados"):
            break
        campo = _estado(pagina)["campoAtual"]
        etapa = pagina.evaluate("d => etapaDaPergunta(d)", PERGUNTAS[campo])
        etapas = _etapas(pagina)
        assert [e["atual"] for e in etapas] == ["step" if i == etapa else None for i in range(3)], campo
        assert [e["feita"] for e in etapas] == [i < etapa for i in range(3)], campo
        vistas.add(etapa)
        _responder_ecra(pagina)
    assert vistas == {0, 1, 2}


def test_etapa_do_filho_desaparece_a_quem_nao_tem_filhos(pagina):
    sem_filhos = {**RESPOSTAS_PADRAO, "tem_filhos_a_cargo": "nao"}
    for _ in range(40):
        if "tem_filhos_a_cargo" in _estado(pagina)["respostas"]:
            break
        _responder_ecra(pagina, sem_filhos)
    assert [e["oculta"] for e in _etapas(pagina)] == [False, True, False]
    while "tem_filhos_a_cargo" in _estado(pagina)["respostas"]:
        pagina.click("#btnVoltar")
    assert not any(e["oculta"] for e in _etapas(pagina))


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


# ── Ecrã de resultados: resumo, «Não tens direito» fechado, partilha, canal ─

LINK_WHATSAPP_TEXTO = (
    "Experimenta o simulador do Tens Direito: mostra a que apoios sociais podes ter direito, "
    "uma pergunta de cada vez. https://tensdireito.com/simulador-universal.html"
    "?utm_source=whatsapp&utm_medium=partilha&utm_campaign=simulador_universal"
)


def _so_apoio_de_teste():
    dados = json.loads(json.dumps(CONDICOES))
    dados["apoios"] = {
        "apoio-de-teste": {
            "titulo": "Apoio de Teste Inventado",
            "simulador": "/simuladores.html",
            "tipo_link": "guia",
            "operador": "all",
            "condicoes": [{"id": "x", "tipo": "categorica", "campo": "reside_legalmente_pt",
                           "operador_comparacao": "eq", "valor": "sim"}],
        }
    }
    return {"**/dados/condicoes.json": lambda r: r.fulfill(status=200, content_type="application/json",
                                                           body=json.dumps(dados))}


def _resumo(page):
    return page.evaluate(
        "({numero: document.getElementById('resumoNumero').textContent,"
        " numeroVisivel: !document.getElementById('resumoNumero').hidden,"
        " texto: document.getElementById('resumoTexto').textContent,"
        " resto: document.getElementById('resumoResto').textContent,"
        " vazio: document.getElementById('resumoResultados').classList.contains('resumo-vazio'),"
        " contagem: document.getElementById('contagemInelegivel').textContent})"
    )


def test_resumo_bate_com_os_cartoes_de_cada_grupo(pagina):
    _percorrer_ate_ao_fim(pagina)
    n_eleg = len(_cartoes(pagina, "grupoElegivel"))
    n_ind = len(_cartoes(pagina, "grupoIndeterminado"))
    n_inel = len(_cartoes(pagina, "grupoInelegivel"))
    assert n_eleg > 1, "o percurso padrão tem de dar mais de um apoio provável"
    r = _resumo(pagina)
    assert r == {
        "numero": str(n_eleg), "numeroVisivel": True, "texto": "apoios com provável direito",
        "resto": f"{n_ind} em que falta saber · {n_inel} sem direito", "vazio": False,
        "contagem": f"({n_inel})",
    }
    assert pagina.is_visible("#resumoResultados")


def test_resumo_sem_apoio_provavel_nunca_mostra_numero(pagina):
    pagina.click("#btnVerResultados")
    pagina.wait_for_selector("#resultados:not([hidden])")
    r = _resumo(pagina)
    assert r["texto"] == "Por agora, nenhum apoio com provável direito"
    assert not r["numeroVisivel"] and r["numero"] == "" and r["vazio"]
    assert r["resto"] == f"{len(CONDICOES['apoios'])} em que falta saber · 0 sem direito"


def test_resumo_singular_com_um_so_apoio(browser, servidor):
    contexto, page = _abrir(browser, servidor, _so_apoio_de_teste())
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    _percorrer_ate_ao_fim(page, {"reside_legalmente_pt": "sim"})
    r = _resumo(page)
    assert (r["numero"], r["texto"], r["resto"]) == ("1", "apoio com provável direito", "0 em que falta saber · 0 sem direito")
    page.click("#btnRecomecar")
    _percorrer_ate_ao_fim(page, {"reside_legalmente_pt": "nao"})
    r = _resumo(page)
    assert r["texto"] == "Por agora, nenhum apoio com provável direito" and r["contagem"] == "(1)"
    contexto.close()


def test_nao_tens_direito_fechado_por_defeito_e_ao_recomecar(pagina):
    _percorrer_ate_ao_fim(pagina)
    assert pagina.evaluate("document.getElementById('detalhesInelegivel').open") is False
    assert _cartoes(pagina, "grupoInelegivel"), "os cartões existem mesmo com a lista fechada"
    assert not pagina.is_visible("#grupoInelegivel li.apoio-card")
    pagina.click("#detalhesInelegivel summary")
    assert pagina.is_visible("#grupoInelegivel li.apoio-card")
    pagina.click("#btnRecomecar")
    _percorrer_ate_ao_fim(pagina)
    assert pagina.evaluate("document.getElementById('detalhesInelegivel').open") is False


def test_partilha_whatsapp_leva_so_a_ligacao_nunca_respostas(pagina):
    from urllib.parse import parse_qs, urlsplit

    href_inicial = pagina.get_attribute("#linkPartilharWhatsapp", "href")
    _percorrer_ate_ao_fim(pagina)
    href = pagina.get_attribute("#linkPartilharWhatsapp", "href")
    assert href == href_inicial, "a ligação de partilha nunca muda com as respostas"
    partes = urlsplit(href)
    assert (partes.scheme, partes.netloc) == ("https", "wa.me")
    # Igualdade exacta ao texto fixo: nada das respostas pode lá estar.
    assert parse_qs(partes.query) == {"text": [LINK_WHATSAPP_TEXTO]}
    assert pagina.get_attribute("#linkPartilharWhatsapp", "rel") == "noopener noreferrer"
    # "Outras formas" reutiliza share.js, que partilha o URL da página — sem estado.
    assert pagina.evaluate("location.search + location.hash") == ""
    assert pagina.get_attribute("#btnPartilharOutras", "class").split()[-1] == "botao-partilhar"


def test_partilha_whatsapp_regista_so_o_pathname(pagina):
    _percorrer_ate_ao_fim(pagina)
    pagina.evaluate("document.getElementById('linkPartilharWhatsapp')"
                    ".addEventListener('click', (e) => e.preventDefault())")
    pagina.click("#linkPartilharWhatsapp")
    eventos = pagina.evaluate(
        "window.dataLayer.map((a) => Array.from(a)).filter((a) => a[0] === 'event' && a[1] === 'partilha_whatsapp')"
    )
    assert eventos == [["event", "partilha_whatsapp", {"pagina": "/simulador-universal.html"}]]


def test_resultados_convidam_para_o_canal_com_a_promessa_do_site(pagina):
    _percorrer_ate_ao_fim(pagina)
    aviso = pagina.locator("#resultados .aviso-canal")
    assert aviso.is_visible()
    href = aviso.locator("a").get_attribute("href")
    assert href.startswith("https://whatsapp.com/channel/")
    assert "utm_content=simulador-universal-resultado" in href
    assert "Avisamos na véspera de cada pagamento da Segurança Social" in aviso.inner_text()


# ── Próximo pagamento e ficheiro de calendário (.ics) ───────────────────

MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
            "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _hoje_lisboa():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Europe/Lisbon")).date()


def _calendario_sintetico(datas_por_slug):
    """{slug: [date, ...]} → mesmo formato de data/calendario_pagamentos.json."""
    meses = {}
    for slug, datas in datas_por_slug.items():
        for d in datas:
            mes = meses.setdefault((d.year, d.month), {})
            mes.setdefault(d.day, []).append(slug)
    return {
        "atualizado_em": "2026-01-01",
        "meses": [
            {"ano": a, "mes": m, "pagamentos": [{"dia": dia, "prestacoes": sl, "metodo": ["transferencia_bancaria"]}
                                                for dia, sl in sorted(dias.items())]}
            for (a, m), dias in sorted(meses.items())
        ],
    }


def _rota_calendario(dados):
    corpo = json.dumps(dados)
    return {"**/data/calendario_pagamentos.json":
            lambda r: r.fulfill(status=200, content_type="application/json", body=corpo)}


def _por_extenso(d, hoje):
    texto = f"{d.day} de {MESES_PT[d.month - 1]}"
    return texto if d.year == hoje.year else f"{texto} de {d.year}"


def _abrir_com_calendario(browser, servidor, rotas):
    contexto, page = _abrir(browser, servidor, rotas)
    page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null")
    return contexto, page


def _pagamentos_nos_cartoes(page):
    return page.eval_on_selector_all(
        "li.apoio-card",
        "els => Object.fromEntries(els.map(e => { const c = e.querySelector('.apoio-pagamento');"
        " return [e.dataset.apoio, c ? {data: c.dataset.data, texto: c.querySelector('strong').textContent,"
        " fonte: c.querySelector('a').getAttribute('href')} : null]; }))",
    )


def test_proximo_pagamento_so_nos_apoios_provaveis_com_calendario(browser, servidor):
    from datetime import timedelta
    hoje = _hoje_lisboa()
    futuro, mais_tarde = hoje + timedelta(days=5), hoje + timedelta(days=35)
    dados = _calendario_sintetico({
        "prestacoes_familiares": [hoje - timedelta(days=1), mais_tarde, futuro],
        "rsi": [futuro], "csi": [futuro],
    })
    contexto, page = _abrir_com_calendario(browser, servidor, _rota_calendario(dados))
    _percorrer_ate_ao_fim(page)
    elegiveis = {c["apoio"] for c in _cartoes(page, "grupoElegivel")}
    assert "abono" in elegiveis and "rsi" not in elegiveis and "csi" not in elegiveis
    pagamentos = _pagamentos_nos_cartoes(page)
    assert pagamentos["abono"] == {
        "data": futuro.isoformat(),
        "texto": "Próximo pagamento: " + _por_extenso(futuro, hoje),
        "fonte": "/calendario-pagamentos-seguranca-social.html",
    }, "o mais próximo a partir de hoje — nunca um dia já passado"
    sem_data = {a for a, p in pagamentos.items() if p is None}
    assert sem_data == set(CONDICOES["apoios"]) - {"abono"}, "só um apoio provável e ligado ao calendário tem data"
    assert page.is_visible("#blocoCalendario")
    contexto.close()


def test_hoje_conta_como_proximo_pagamento(browser, servidor):
    hoje = _hoje_lisboa()
    contexto, page = _abrir_com_calendario(
        browser, servidor, _rota_calendario(_calendario_sintetico({"prestacoes_familiares": [hoje]})))
    _percorrer_ate_ao_fim(page)
    assert _pagamentos_nos_cartoes(page)["abono"]["data"] == hoje.isoformat()
    contexto.close()


@pytest.mark.parametrize("falha", ["abort", "http404", "sem_meses", "so_passado"])
def test_sem_datas_futuras_os_resultados_nao_mostram_datas_nem_calendario(browser, servidor, falha):
    from datetime import timedelta
    passado = _calendario_sintetico({"prestacoes_familiares": [_hoje_lisboa() - timedelta(days=3)]})
    rotas = {
        "abort": {"**/data/calendario_pagamentos.json": lambda r: r.abort()},
        "http404": {"**/data/calendario_pagamentos.json": lambda r: r.fulfill(status=404, body="")},
        "sem_meses": _rota_calendario({"atualizado_em": "2026-01-01"}),
        "so_passado": _rota_calendario(passado),
    }[falha]
    contexto, page = _abrir_com_calendario(browser, servidor, rotas)
    _percorrer_ate_ao_fim(page)
    assert _cartoes(page, "grupoElegivel"), "os resultados aparecem na mesma"
    assert all(p is None for p in _pagamentos_nos_cartoes(page).values())
    assert not page.is_visible("#blocoCalendario")
    assert page.is_visible("#resultados .aviso-canal"), "o convite ao canal fica sempre"
    contexto.close()


def test_entradas_malformadas_do_calendario_sao_ignoradas(browser, servidor):
    from datetime import timedelta
    hoje = _hoje_lisboa()
    bom = hoje + timedelta(days=9)
    dados = _calendario_sintetico({"prestacoes_familiares": [bom]})
    dados["meses"].append({"ano": hoje.year + 1, "mes": 13, "pagamentos": [{"dia": 1, "prestacoes": ["prestacoes_familiares"]}]})
    dados["meses"].append({"ano": hoje.year, "mes": hoje.month, "pagamentos": [
        {"dia": "1", "prestacoes": ["prestacoes_familiares"]},
        {"dia": 40, "prestacoes": ["prestacoes_familiares"]},
        {"dia": 2, "prestacoes": "prestacoes_familiares"},
    ]})
    contexto, page = _abrir_com_calendario(browser, servidor, _rota_calendario(dados))
    _percorrer_ate_ao_fim(page)
    eventos = page.evaluate("window.simuladorUniversal.eventosCalendario")
    assert eventos == [{"apoioId": "abono", "titulo": CONDICOES["apoios"]["abono"]["titulo"], "iso": bom.isoformat()}]
    contexto.close()


def _linhas_ics(texto):
    assert texto.endswith("\r\n") and "\n" not in texto.replace("\r\n", "")
    for linha in texto.split("\r\n"):
        assert len(linha.encode("utf-8")) <= 75, f"linha com mais de 75 octetos: {linha!r}"
    # Desdobrar as linhas continuadas (RFC 5545).
    return texto.replace("\r\n ", "").split("\r\n")[:-1]


def test_ficheiro_ics_tem_um_evento_por_data_futura_e_nada_das_respostas(browser, servidor):
    from datetime import timedelta
    hoje = _hoje_lisboa()
    d1, d2 = hoje + timedelta(days=2), hoje + timedelta(days=33)
    contexto, page = _abrir_com_calendario(
        browser, servidor, _rota_calendario(_calendario_sintetico({"prestacoes_familiares": [d2, d1]})))
    _percorrer_ate_ao_fim(page)
    page.evaluate("window.dataLayer = []")
    with page.expect_download() as info:
        page.click("#btnCalendario")
    download = info.value
    assert download.suggested_filename == "pagamentos-seguranca-social.ics"
    texto = Path(download.path()).read_bytes().decode("utf-8")  # sem converter CRLF
    linhas = _linhas_ics(texto)
    assert linhas[0] == "BEGIN:VCALENDAR" and linhas[-1] == "END:VCALENDAR"
    titulo = CONDICOES["apoios"]["abono"]["titulo"]
    inicios = [ln for ln in linhas if ln.startswith("DTSTART")]
    assert inicios == [f"DTSTART;VALUE=DATE:{d:%Y%m%d}" for d in (d1, d2)]
    fins = [ln for ln in linhas if ln.startswith("DTEND")]
    assert fins == [f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}" for d in (d1, d2)]
    assert [ln for ln in linhas if ln.startswith("UID:")] == [f"UID:abono-{d:%Y%m%d}@tensdireito.com" for d in (d1, d2)]
    assert linhas.count(f"SUMMARY:Pagamento da Segurança Social: {titulo}") == 2
    assert linhas.count(f"DESCRIPTION:Amanhã a Segurança Social paga: {titulo}") == 2
    assert linhas.count("TRIGGER:-PT12H") == 2
    for valor in ("1990", "2020-05", "19900101", "20200501"):
        assert valor not in texto, "o ficheiro nunca leva respostas"
    eventos = page.evaluate(
        "window.dataLayer.map((a) => Array.from(a)).filter((a) => a[0] === 'event' && a[1] === 'calendario_descarregado')")
    assert eventos == [["event", "calendario_descarregado", {"pagina": "/simulador-universal.html"}]]
    contexto.close()


def test_ics_escapa_virgulas_e_dobra_linhas_longas(pagina):
    texto = pagina.evaluate(
        "window.simuladorUniversal.gerarICS([{apoioId: 'x', titulo: 'Apoio, com; vírgulas e acentos — ' + 'é'.repeat(60),"
        " iso: '2031-12-31'}], new Date(Date.UTC(2031, 0, 2, 3, 4, 5)))"
    )
    linhas = _linhas_ics(texto)
    assert "DTSTAMP:20310102T030405Z" in linhas
    assert "DTEND;VALUE=DATE:20320101" in linhas, "o dia seguinte vira o ano"
    resumo = next(ln for ln in linhas if ln.startswith("SUMMARY:"))
    assert resumo.startswith(r"SUMMARY:Pagamento da Segurança Social: Apoio\, com\; vírgulas")
