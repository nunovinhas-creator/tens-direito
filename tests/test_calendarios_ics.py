"""Calendários subscrevíveis (calendario/*.ics) e os botões 📅 da lista
«Quando recebo?» da página do calendário de pagamentos.

Os ficheiros publicados têm de bater certo com data/calendario_pagamentos.json
(regenerados com a data de geração que trazem) — se o JSON mudar sem
regenerar, este teste falha.
"""
import datetime as dt
import glob
import http.server
import os
import re
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from atualizar_calendario import METODOS, carregar_dados  # noqa: E402
from gerar_calendarios_ics import (  # noqa: E402
    PASTA,
    atualizar_ics,
    data_de_geracao,
    eventos,
    feeds,
    ligacoes,
    render_ics,
    render_ics_cga,
    render_subscrever,
)

PAGINA = RAIZ / "calendario-pagamentos-seguranca-social.html"
WORKFLOW = RAIZ / ".github" / "workflows" / "calendario-mensal.yml"

DADOS_TESTE = {
    "meses": [
        {"ano": 2026, "mes": 10, "pagamentos": [
            {"dia": 8, "prestacoes": ["pensoes", "csi"], "metodo": ["transferencia_bancaria", "vale_de_correio"]},
            {"dia": 16, "prestacoes": ["prestacoes_familiares", "desemprego_doenca_parentalidade_acao_social_1"],
             "metodo": ["transferencia_bancaria"]},
            {"dia": 28, "prestacoes": ["desemprego_doenca_parentalidade_acao_social_2"],
             "metodo": ["transferencia_bancaria", "vale_de_correio"]},
        ]},
        {"ano": 2026, "mes": 11, "pagamentos": [
            {"dia": 9, "prestacoes": ["pensoes"], "metodo": ["transferencia_bancaria"]},
        ]},
    ]
}


def _ler(caminho):
    return caminho.read_bytes().decode("utf-8")


def _eventos_ics(conteudo):
    desdobrado = conteudo.replace("\r\n ", "")
    blocos = re.findall(r"BEGIN:VEVENT\r\n(.*?)END:VEVENT", desdobrado, re.S)
    out = []
    for b in blocos:
        campos = {}
        for linha in b.split("\r\n"):
            if ":" in linha and not linha.startswith(("BEGIN:VALARM", "END:VALARM", "ACTION", "TRIGGER")):
                chave, valor = linha.split(":", 1)
                campos.setdefault(chave, valor)
        out.append(campos)
    return out


# ── Ficheiros publicados ─────────────────────────────────────────────────


def test_um_ficheiro_por_prestacao_e_nada_mais():
    esperados = {f"{ancora}.ics" for ancora, _n, _s in feeds()} | {"pensoes-cga.ics"}
    assert {p.name for p in PASTA.glob("*")} == esperados


@pytest.mark.parametrize("ancora,nome,slugs", feeds(), ids=[f[0] for f in feeds()])
def test_ficheiro_publicado_bate_com_o_json(ancora, nome, slugs):
    conteudo = _ler(PASTA / f"{ancora}.ics")
    gerado = data_de_geracao(conteudo)
    assert gerado, "falta X-TD-GERADO-EM"
    assert conteudo == render_ics(ancora, nome, slugs, carregar_dados(), gerado), (
        "calendario/*.ics desactualizado face a data/calendario_pagamentos.json — "
        "corre python scripts/atualizar_calendario.py"
    )


def test_ficheiro_publicado_da_cga_bate_com_a_regra():
    conteudo = _ler(PASTA / "pensoes-cga.ics")
    gerado = data_de_geracao(conteudo)
    assert gerado, "falta X-TD-GERADO-EM"
    assert conteudo == render_ics_cga(gerado), (
        "calendario/pensoes-cga.ics desactualizado — corre python scripts/atualizar_calendario.py"
    )


@pytest.mark.parametrize("ancora", [f[0] for f in feeds()] + ["pensoes-cga"])
def test_ficheiro_publicado_e_ics_valido(ancora):
    conteudo = _ler(PASTA / f"{ancora}.ics")
    assert conteudo.startswith("BEGIN:VCALENDAR\r\n") and conteudo.endswith("END:VCALENDAR\r\n")
    assert "\n" not in conteudo.replace("\r\n", "")
    for linha in conteudo.split("\r\n"):
        assert len(linha.encode("utf-8")) <= 75, linha


# ── Geração ──────────────────────────────────────────────────────────────


def test_so_datas_de_hoje_em_diante_e_por_ordem():
    ev = eventos(DADOS_TESTE, ["pensoes"], dt.date(2026, 10, 8))
    assert [e["dia"] for e in ev] == [dt.date(2026, 10, 8), dt.date(2026, 11, 9)]
    ev = eventos(DADOS_TESTE, ["pensoes"], dt.date(2026, 10, 9))
    assert [e["dia"] for e in ev] == [dt.date(2026, 11, 9)]


def test_lotes_entram_os_dois_com_1o_ou_2o_pagamento():
    conteudo = render_ics("subsidio-desemprego", "Subsídio de desemprego",
                          ["desemprego_doenca_parentalidade_acao_social_1",
                           "desemprego_doenca_parentalidade_acao_social_2"],
                          DADOS_TESTE, dt.date(2026, 10, 1))
    ev = _eventos_ics(conteudo)
    assert [e["DTSTART;VALUE=DATE"] for e in ev] == ["20261016", "20261028"]
    for e in ev:
        assert e["SUMMARY"] == "Pagamento da Segurança Social: Subsídio de desemprego (1.º ou 2.º pagamento)"
        assert "pode ser este dia ou o outro" in e["DESCRIPTION"]


def test_evento_normal_titulo_metodo_uid_e_aviso():
    conteudo = render_ics("pensoes", "Pensões", ["pensoes"], DADOS_TESTE, dt.date(2026, 10, 1))
    ev = _eventos_ics(conteudo)[0]
    assert ev["UID"] == "pensoes-20261008@tensdireito.com"
    assert ev["DTEND;VALUE=DATE"] == "20261009"
    assert ev["SUMMARY"] == "Pagamento da Segurança Social: Pensões"
    assert "(1.º ou 2.º" not in ev["SUMMARY"]
    assert ("Por " + METODOS["transferencia_bancaria"] + " ou " + METODOS["vale_de_correio"]) in ev["DESCRIPTION"]
    assert "DESCRIPTION:Amanhã a Segurança Social paga: Pensões" in conteudo.replace("\r\n ", "")
    assert "X-WR-CALNAME:Pagamentos da Segurança Social: Pensões" in conteudo
    assert "X-TD-GERADO-EM:2026-10-01" in conteudo


def test_virgulas_escapadas_e_sem_datas_e_valido():
    conteudo = render_ics("csi", "Complemento, teste; x", ["csi"], DADOS_TESTE, dt.date(2026, 12, 1))
    assert "X-WR-CALNAME:Pagamentos da Segurança Social: Complemento\\, teste\\; x" in conteudo.replace("\r\n ", "")
    assert "BEGIN:VEVENT" not in conteudo


def test_atualizar_e_idempotente_e_nao_reescreve_so_pela_data(tmp_path):
    hoje = dt.date(2026, 10, 1)
    assert len(atualizar_ics(DADOS_TESTE, hoje, pasta=tmp_path)) == len(feeds()) + 1
    assert atualizar_ics(DADOS_TESTE, hoje, pasta=tmp_path) == []
    # Dia seguinte, mesmos eventos: não reescreve (zero commits sem nada novo).
    assert atualizar_ics(DADOS_TESTE, dt.date(2026, 10, 2), pasta=tmp_path) == []
    # Passou o dia 8: as pensões perdem um evento — reescreve.
    assert "pensoes.ics" in atualizar_ics(DADOS_TESTE, dt.date(2026, 10, 9), pasta=tmp_path)
    # Mês novo no JSON: reescreve.
    dados = {"meses": DADOS_TESTE["meses"] + [
        {"ano": 2026, "mes": 12, "pagamentos": [{"dia": 9, "prestacoes": ["rsi"], "metodo": ["transferencia_bancaria"]}]}]}
    assert "rsi.ics" in atualizar_ics(dados, dt.date(2026, 10, 9), pasta=tmp_path)


def test_dry_run_nao_escreve(tmp_path):
    assert atualizar_ics(DADOS_TESTE, dt.date(2026, 10, 1), pasta=tmp_path, escrever=False)
    assert not list(tmp_path.glob("*.ics"))


# ── Secção da página ─────────────────────────────────────────────────────


def test_ics_da_cga_doze_meses_com_extras_de_julho_e_novembro():
    ev = _eventos_ics(render_ics_cga(dt.date(2026, 10, 20)))
    datas = [e["DTSTART;VALUE=DATE"] for e in ev]
    assert datas[0] == "20261119" and datas[1] == "20261218"
    assert len(datas) == 11  # outubro já passou; 12 meses a contar de outubro
    resumo = {e["DTSTART;VALUE=DATE"]: e["SUMMARY"] for e in ev}
    assert resumo["20261119"] == "Pagamento da pensão da CGA (inclui o subsídio de Natal)"
    assert resumo["20270719"] == "Pagamento da pensão da CGA (inclui o 14.º mês)"
    assert resumo["20261218"] == "Pagamento da pensão da CGA"
    assert all(e["UID"].startswith("pensoes-cga-") for e in ev)


def test_lista_tem_um_botao_por_calendario_publicado():
    """Cada .ics publicado tem um 📅 na lista do mês corrente, e só um."""
    corpo = re.search(r"<!-- CAL:CORPO:INICIO -->(.*?)<!-- CAL:CORPO:FIM -->",
                      _ler(PAGINA), re.S).group(1)
    corpo = re.sub(r"<template.*?</template>", "", corpo, flags=re.S)
    for ics in PASTA.glob("*.ics"):
        webcal, google = ligacoes(ics.stem)
        assert corpo.count(f'href="{webcal}" data-google="{google}"') == 1, ics.name
    assert corpo.count('class="cal-sub"') == len(list(PASTA.glob("*.ics")))


def test_pagina_publicada_tem_a_seccao_gerada():
    pagina = _ler(PAGINA)
    zona = re.search(r"<!-- CAL:SUBSCREVER:INICIO -->\n(.*?)\n<!-- CAL:SUBSCREVER:FIM -->", pagina, re.S)
    assert zona and zona.group(1) == render_subscrever()


def test_workflow_mensal_pode_escrever_e_commita_os_ics():
    wf = WORKFLOW.read_text(encoding="utf-8")
    assert "calendario/*.ics) ;;" in wf
    assert re.search(r"git add [^\n]*calendario/", wf)


# ── Página real (Chromium) ───────────────────────────────────────────────


def _localizar_chromium():
    bases = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH"), "/opt/pw-browsers",
             os.path.expanduser("~/.cache/ms-playwright")]
    for base in bases:
        if base:
            candidatos = sorted(glob.glob(os.path.join(base, "chromium-*", "chrome-linux*", "chrome")))
            if candidatos:
                return candidatos[-1]
    return None


try:
    from playwright.sync_api import sync_playwright
    _CHROMIUM = _localizar_chromium()
except ImportError:
    sync_playwright, _CHROMIUM = None, None


class _SemLog(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def _servir():
    httpd = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), lambda *a, **kw: _SemLog(*a, directory=str(RAIZ), **kw))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}"


UA_IPHONE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
             "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
UA_ANDROID = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36")


def _botao_e_evento(browser, servidor, user_agent):
    contexto = browser.new_context(user_agent=user_agent)
    page = contexto.new_page()
    page.route("https://www.googletagmanager.com/**", lambda r: r.abort())
    page.goto(f"{servidor}/calendario-pagamentos-seguranca-social.html")
    # Não sair da página ao carregar no botão (webcal:// e o Google).
    page.evaluate("document.addEventListener('click', e => { if (e.target.closest('a')) e.preventDefault(); })")
    botao = page.locator("#rsi a.cal-sub")
    botao.click()
    href, alvo = botao.get_attribute("href"), botao.get_attribute("target")
    eventos_ga = page.evaluate(
        "(window.dataLayer || []).map(a => Array.from(a)).filter(e => e[1] === 'calendario_subscrito')")
    contexto.close()
    return href, alvo, eventos_ga


@pytest.mark.skipif(not _CHROMIUM, reason="Playwright/Chromium não disponível neste ambiente")
def test_botao_abre_o_calendario_certo_e_evento_so_com_o_destino():
    webcal, google = ligacoes("rsi")
    httpd, servidor = _servir()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=_CHROMIUM)
            assert _botao_e_evento(browser, servidor, UA_IPHONE) == (
                webcal, None, [["event", "calendario_subscrito", {"destino": "apple"}]])
            assert _botao_e_evento(browser, servidor, UA_ANDROID) == (
                google, "_blank", [["event", "calendario_subscrito", {"destino": "google"}]])
            browser.close()
    finally:
        httpd.shutdown()
