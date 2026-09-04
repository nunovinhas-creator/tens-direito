"""
Testes funcionais para o ranking/apresentação da pesquisa interna
(scripts/pesquisa.js), executados num browser real (Chromium headless
via Playwright) — carrega o ficheiro real, nunca uma cópia.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PESQUISA_JS = (RAIZ / "scripts" / "pesquisa.js").read_text(encoding="utf-8")

_HTML_BASE = """<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"><title>Teste</title></head>
<body>
  <input id="campo-pesquisa" type="search">
  <div id="resultados-pesquisa" style="display:none;"></div>
</body>
</html>
"""


def _localizar_chromium():
    """Procura o binário do Chromium em todas as localizações plausíveis —
    nunca assumir uma única convenção. `/opt/pw-browsers` é específico do
    sandbox do Claude Code; o CI (GitHub Actions) nunca define
    `PLAYWRIGHT_BROWSERS_PATH` e `playwright install` instala no cache
    por omissão (`~/.cache/ms-playwright`) — sem este segundo candidato,
    os testes ficavam sempre skipped no CI (achado real, 2026-07-05)."""
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


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        page.set_content(_HTML_BASE)
        page.add_script_tag(content=PESQUISA_JS)
        yield page
        browser.close()


def _pesquisar(pagina, termo):
    return pagina.evaluate("(t) => pesquisar(t)", termo)


def _mostrar(pagina, termo):
    pagina.evaluate(
        "(t) => mostrarResultados(pesquisar(t), t)", termo
    )


# ── Mínimo de caracteres ───────────────────────────────────────────────────

def test_um_caracter_nao_dispara_pesquisa(pagina):
    resultados = _pesquisar(pagina, "s")
    assert resultados == []


def test_um_caracter_nao_mostra_dropdown(pagina):
    _mostrar(pagina, "s")
    display = pagina.eval_on_selector("#resultados-pesquisa", "el => getComputedStyle(el).display")
    assert display == "none"


def test_dois_caracteres_ja_pesquisa(pagina):
    resultados = _pesquisar(pagina, "as")
    assert isinstance(resultados, list)  # não rebenta, pode ou não ter resultados


# ── Ranking em camadas ───────────────────────────────────────────────────

def test_sub_devolve_resultados_de_titulo_antes_dos_de_keywords(pagina):
    resultados = _pesquisar(pagina, "sub")
    assert len(resultados) > 0

    camadas = [r["camada"] for r in resultados]
    assert camadas == sorted(camadas)  # nunca uma camada 3 antes de uma camada 1/2

    # "Passe sub-23 gratuito" tem "sub" no título -> camada 1, tem de vir primeiro
    assert resultados[0]["camada"] == 1
    assert "sub" in resultados[0]["titulo"].lower()


def test_resultados_limitados_a_8(pagina):
    resultados = _pesquisar(pagina, "de")
    assert len(resultados) <= 8


def test_psu_encontra_o_cluster_inteiro(pagina):
    resultados = _pesquisar(pagina, "psu")
    urls = {r["url"] for r in resultados}
    assert "/prestacao-social-unica.html" in urls
    # o cluster da PSU tem mais páginas do que o limite de 8 — confirmar
    # que pelo menos várias páginas do mesmo cluster aparecem
    assert sum(1 for r in resultados if r["cluster"] == "prestacao-social-unica") >= 3


def test_termo_sem_correspondencia_devolve_lista_vazia(pagina):
    resultados = _pesquisar(pagina, "xyz")
    assert resultados == []


# ── Contexto do match (excerto) ───────────────────────────────────────────

def test_match_em_titulo_destaca_o_titulo(pagina):
    resultados = _pesquisar(pagina, "abono")
    alvo = next(r for r in resultados if r["url"] == "/abono-de-familia.html")
    assert alvo["camada"] == 1
    assert "<mark>" in alvo["tituloHtml"].lower() or "<mark>" in alvo["tituloHtml"]


def test_match_fora_do_titulo_mostra_excerto_destacado(pagina):
    # Páginas sem o termo no título mas com o termo na descrição/keywords
    # têm de aparecer com <mark> no excerto. Não fixamos uma página
    # concreta — o teste verifica o mecanismo de camada 2/3, não a
    # posição de ranking de uma página específica. Termo escolhido
    # deliberadamente ("segurança social") em vez do "sub" original
    # (2026-09-04): "sub" cresceu para exactamente 8 títulos que contêm
    # "sub" (subsídio/sub-23/substituir) — MAX_RESULTADOS=8 satura só
    # com camada 1, sem sobrar nenhuma vaga para camada 2/3, tornando o
    # teste falso-negativo por crescimento orgânico do site (mesmo risco
    # já documentado no histórico deste teste). "segurança social" tem
    # muito mais matches de camada 2/3 do que o cap de 8, por isso é
    # robusto ao mesmo crescimento.
    resultados = _pesquisar(pagina, "segurança social")
    fora_do_titulo = [r for r in resultados if r["camada"] in (2, 3)]
    assert fora_do_titulo, "Pesquisa por 'segurança social' devia devolver pelo menos um resultado por descrição/keywords"
    assert all("<mark>" in r["excertoHtml"] for r in fora_do_titulo)


# ── Badges de cluster/ferramenta ───────────────────────────────────────────

def test_resultado_de_pagina_de_cluster_tem_nome_do_cluster(pagina):
    resultados = _pesquisar(pagina, "abono")
    alvo = next(r for r in resultados if r["url"] == "/abono-de-familia.html")
    assert alvo["clusterNome"] == "Família e Crianças"


def test_resultado_de_ferramenta_tem_tipo_ferramenta(pagina):
    resultados = _pesquisar(pagina, "simulador")
    alvo = next(r for r in resultados if r["url"] == "/simulador-abono.html")
    assert alvo["tipo"] == "ferramenta"


# ── Renderização no dropdown ───────────────────────────────────────────────

def test_dropdown_mostra_badge_do_cluster(pagina):
    _mostrar(pagina, "abono")
    html_dropdown = pagina.eval_on_selector("#resultados-pesquisa", "el => el.innerHTML")
    assert "resultado-badge" in html_dropdown
    assert "Família e Crianças" in html_dropdown


def test_estado_vazio_tem_link_para_todos_os_guias(pagina):
    _mostrar(pagina, "xyz")
    html_dropdown = pagina.eval_on_selector("#resultados-pesquisa", "el => el.innerHTML")
    assert "resultado-vazio" in html_dropdown
    assert "guias-de-apoios" in html_dropdown
    display = pagina.eval_on_selector("#resultados-pesquisa", "el => getComputedStyle(el).display")
    assert display == "block"
