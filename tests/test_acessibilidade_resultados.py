"""
Auditoria axe-core ao estado COM RESULTADO de cada simulador.

`test_acessibilidade.py` só audita as páginas tal como carregam — num
simulador, isso é o formulário vazio. O HTML que o cálculo injecta
(tabelas, avisos, botões de copiar, cartões de apoio) nunca era auditado.
Aqui faz-se um cálculo por simulador (no universal, até aos resultados) e
corre-se o mesmo axe vendorizado, com o mesmo limiar.

Além do axe, duas garantias que o axe não verifica:
- o contentor do resultado é uma região viva (`aria-live`/`role="status"`)
  já presente antes do cálculo — um leitor de ecrã só anuncia mudanças numa
  região viva que já existia quando o conteúdo mudou;
- no universal, a região viva não está escondida antes dos resultados e o
  foco vai para o título dos resultados depois do cálculo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_acessibilidade import (  # noqa: E402
    AXE_JS,
    LIMIAR_MODERADO_MINOR,
    RAIZ,
    browser,  # noqa: F401  (fixture)
    pytestmark,  # noqa: F401  (mesmo skip sem Chromium)
    servidor,  # noqa: F401  (fixture)
)

CONDICOES = json.loads((RAIZ / "dados" / "condicoes.json").read_text(encoding="utf-8"))


def _esperar_botao(page, botao):
    page.wait_for_function(f"document.getElementById('{botao}').disabled === false", timeout=10000)


def _abono(page):
    _esperar_botao(page, "btnCalcularAbono")
    page.fill("#rendimento", "3000")
    page.select_option("#monoparental", "nao")
    page.select_option("#numCriancas", "1")
    page.fill("#idade1", "24")
    page.click("#btnCalcularAbono")


def _ase(page):
    page.select_option("#escalaoAbono", "1")
    page.select_option("#tipoEscola", "publica")
    page.click("#formASE button[type=submit]")


def _condicoes_reforma(page):
    _esperar_botao(page, "btnCalcularCondicoesReforma")
    page.select_option("#mesNascimento", "6")
    page.fill("#anoNascimento", "1965")
    page.fill("#anosCarreira", "42")
    page.fill("#idadeInicio", "16")
    page.select_option("#mesmaEmpresa", "nao")
    page.click("#btnCalcularCondicoesReforma")


def _csi(page):
    _esperar_botao(page, "btnCalcularCSI")
    page.fill("#idadeAnos", "70")
    page.fill("#idadeMeses", "0")
    page.select_option("#situacao", "isolado")
    page.fill("#pensoesRequerente", "5600")
    page.click("#btnCalcularCSI")


def _imt_jovem(page):
    _esperar_botao(page, "btnCalcularIMTJovem")
    page.fill("#valorCompra", "250000")
    for chk in ("chkIdade", "chkNaoDependente", "chkSemPropriedade"):
        page.check(f"#{chk}")
    page.click("#btnCalcularIMTJovem")


def _psu(page):
    _esperar_botao(page, "botaoCalcularPSU")
    page.click("#botaoCalcularPSU")


def _rsi(page):
    _esperar_botao(page, "btnCalcularRSI")
    page.fill("#adultos", "1")
    page.fill("#dataNascimento", "1990-01-01")
    page.select_option("#residenciaLegal", "sim")
    page.select_option("#patrimonio", "dentro")
    page.click("#btnCalcularRSI")


def _subsidio_desemprego(page):
    _esperar_botao(page, "btnCalcularDesemprego")
    page.select_option("#vinculo", "conta_outrem")
    page.fill("#remuneracao", "1200")
    page.fill("#dataNascimento", "1990-01-01")
    page.fill("#meses", "30")
    page.click("#btnCalcularDesemprego")


def _subsidio_doenca(page):
    _esperar_botao(page, "btnCalcularSubsidioDoenca")
    page.fill("#salario", "1400")
    page.fill("#duracaoDias", "100")
    page.select_option("#vinculo", "conta_outrem")
    page.click("#btnCalcularSubsidioDoenca")


SIMULADORES = {
    "simulador-abono.html": _abono,
    "simulador-ase.html": _ase,
    "simulador-condicoes-reforma.html": _condicoes_reforma,
    "simulador-csi.html": _csi,
    "simulador-imt-jovem.html": _imt_jovem,
    "simulador-psu.html": _psu,
    "simulador-rsi.html": _rsi,
    "simulador-subsidio-desemprego.html": _subsidio_desemprego,
    "simulador-subsidio-doenca.html": _subsidio_doenca,
}

RESPOSTAS_UNIVERSAL = {
    "data_nascimento_requerente": "1990-01-01",
    "data_nascimento_crianca": "2020-05-01",
    "tem_filhos_a_cargo": "sim",
}


def _responder_universal_ate_aos_resultados(page, limite=80):
    for _ in range(limite):
        if page.is_visible("#resultados"):
            return
        campo = page.evaluate("window.simuladorUniversal.campoAtual")
        n = page.evaluate("window.simuladorUniversal.historico.length")
        d = CONDICOES["perguntas"][campo]
        if campo in RESPOSTAS_UNIVERSAL:
            valor = RESPOSTAS_UNIVERSAL[campo]
        elif d["tipo"] == "categorica":
            valor = d["opcoes"][0]
        elif d["tipo"] == "data":
            valor = "1990-01-01"
        else:
            valor = 0
        if d["tipo"] == "categorica":
            page.click(f"#opcoes button[data-valor='{valor}']")
        else:
            page.fill("#campoResposta", str(valor))
            page.click("#btnContinuar")
        page.wait_for_function(
            f"window.simuladorUniversal.historico.length === {n + 1} || !document.getElementById('resultados').hidden"
        )
    raise AssertionError("o simulador universal não chegou aos resultados")


def _abrir(browser, servidor, rel):  # noqa: F811
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    page.goto(f"{servidor}/{rel}", wait_until="networkidle", timeout=30000)
    return page


def _axe(page):
    # O resultado entra com uma animação (opacidade) — auditar a meio dela
    # mede cores semi-transparentes, não as reais.
    page.evaluate("Promise.all(document.getAnimations().map((a) => a.finished))")
    page.wait_for_timeout(100)
    page.add_script_tag(content=AXE_JS)
    return page.evaluate(
        """async () => (await axe.run(document, {
            runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'] }
        })).violations"""
    )


def _verificar_axe(rel, violacoes):
    graves = [v for v in violacoes if v.get("impact") in ("critical", "serious")]
    assert not graves, (
        f"{rel} (com resultado): {len(graves)} violação(ões) critical/serious — "
        + "; ".join(f"{v['id']} ({v['impact']}, {len(v['nodes'])} elemento(s))" for v in graves)
    )
    menores = [v for v in violacoes if v.get("impact") in ("moderate", "minor")]
    total = sum(len(v["nodes"]) for v in menores)
    assert total <= LIMIAR_MODERADO_MINOR, (
        f"{rel} (com resultado): {total} ocorrência(s) moderate/minor — "
        + "; ".join(f"{v['id']} ({v['impact']}, {len(v['nodes'])} elemento(s))" for v in menores)
    )


_E_REGIAO_VIVA = """(el) => !!el && (
    ['polite', 'assertive'].includes(el.getAttribute('aria-live'))
    || ['status', 'alert'].includes(el.getAttribute('role')))"""


@pytest.mark.parametrize("rel", sorted(SIMULADORES))
def test_simulador_com_resultado_sem_violacoes(servidor, browser, rel):  # noqa: F811
    page = _abrir(browser, servidor, rel)
    try:
        assert page.eval_on_selector("#resultado", _E_REGIAO_VIVA), (
            f"{rel}: #resultado tem de ser uma região viva (aria-live/role=status) antes do cálculo"
        )
        SIMULADORES[rel](page)
        page.wait_for_selector("#resultado.show", timeout=10000)
        assert page.inner_text("#resultado").strip(), f"{rel}: o cálculo não produziu resultado"
        _verificar_axe(rel, _axe(page))
    finally:
        page.close()


def test_simulador_universal_com_resultados_sem_violacoes(servidor, browser):  # noqa: F811
    rel = "simulador-universal.html"
    page = _abrir(browser, servidor, rel)
    try:
        page.wait_for_function("window.simuladorUniversal && window.simuladorUniversal.campoAtual !== null", timeout=10000)
        regiao = page.evaluate(
            f"""() => {{
                const viva = ({_E_REGIAO_VIVA});
                const el = [...document.querySelectorAll('[aria-live], [role=status]')]
                    .find((e) => viva(e) && e.dataset.regiao === 'resultados');
                if (!el) return null;
                return {{ id: el.id, escondida: !!el.closest('[hidden]') || getComputedStyle(el).display === 'none',
                          texto: el.textContent.trim() }};
            }}"""
        )
        assert regiao, "falta a região viva dos resultados (data-regiao=\"resultados\")"
        assert not regiao["escondida"], (
            "a região viva dos resultados tem de estar no DOM, fora de qualquer [hidden], antes de ser preenchida"
        )
        assert regiao["texto"] == "", "antes dos resultados, a região viva tem de estar vazia"

        _responder_universal_ate_aos_resultados(page)
        page.wait_for_selector("#resultados:not([hidden])")
        assert page.evaluate("document.activeElement && document.activeElement.id") == "resultadosTitulo", (
            "depois do cálculo, o foco tem de ir para o título dos resultados"
        )
        assert page.inner_text(f"#{regiao['id']}").strip(), "a região viva tem de anunciar os resultados"
        _verificar_axe(rel, _axe(page))
    finally:
        page.close()


def test_simulador_universal_tem_link_estatico_para_os_guias():
    """Sem JS o simulador não funciona — tem de haver uma saída para os guias no HTML."""
    from bs4 import BeautifulSoup

    sopa = BeautifulSoup((RAIZ / "simulador-universal.html").read_text(encoding="utf-8"), "html.parser")
    main = sopa.find("main")
    links = [
        a for a in main.find_all("a", href=True)
        if a["href"] in ("/#guias-de-apoios", "/index.html#guias-de-apoios") and not a.find_parent(attrs={"hidden": True})
    ]
    assert links, "falta um link estático (fora de [hidden]) para /#guias-de-apoios em simulador-universal.html"


def test_calc_apoios_carregado_com_defer():
    html = (RAIZ / "simulador-universal.html").read_text(encoding="utf-8")
    assert '<script src="/assets/js/calc-apoios.js" defer></script>' in html


def test_todos_os_simuladores_tem_um_calculo_auditado():
    reais = {p.name for p in RAIZ.glob("simulador-*.html")} - {"simulador-universal.html"}
    assert reais == set(SIMULADORES), (
        f"simuladores sem cálculo auditado: {sorted(reais - set(SIMULADORES))}; "
        f"entradas sem página: {sorted(set(SIMULADORES) - reais)}"
    )
