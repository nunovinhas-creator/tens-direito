"""
Testes da mecânica de cálculo do simulador de IMT Jovem
(simulador-imt-jovem.html), executados num browser real (Chromium
headless via Playwright) — extrai o JS inline directamente do HTML real,
nunca uma cópia à parte (mesma filosofia de test_simulador_csi_calculo.py).

Sessão 2 do cluster Habitação (2026-07-20). Os golden tests constroem
`params` directamente a partir de dados/parametros.json (gerado de
dados/parametros/habitacao.yaml — a fonte única de qualquer valor de IMT,
incluindo a tabela geral 2026 e os limites das Regiões Autónomas), nunca
de valores hardcoded. Todos os valores esperados foram calculados à mão a
partir da tabela verificada no PASSO 0:

  Tabela geral IMT 2026 (HPP, Continente):
    até 106.346€ → 0%
    até 145.470€ → 2%, abater 2.126,92€
    até 198.347€ → 5%, abater 6.491,02€
    até 330.539€ → 7%, abater 10.457,96€
    até 660.982€ → 8%, abater 13.763,35€
    até 1.150.853€ → 6% (taxa única, sem parcela)
    acima → 7,5% (taxa única, sem parcela)
  Imposto do Selo da aquisição: 0,8%.
  IMT Jovem (Continente): isenção total ≤330.539€; parcial ≤660.982€
  (8% IMT + 0,8% IS só sobre o excedente); acima, tabela geral.

Validação cruzada com o exemplo JÁ PUBLICADO em imt-jovem.html desde a
Sessão 1 (fonte: Doutor Finanças): casa de 340.000€ → 832,57€ com isenção
vs 16.156,65€ sem — poupança 15.324,08€. A tabela verificada nesta sessão
reproduz esses três números ao cêntimo (ver
test_exemplo_publicado_340000_reproduzido_ao_centimo), o que tranca a
coerência artigo↔simulador.

Cobertura regional: SÓ CONTINENTE (decisão do PASSO 0 — as parcelas a
abater da tabela geral RA não foram confirmadas de forma conclusiva; os
limites RA do IMT Jovem estão no YAML e na página do guia, mas o
simulador nunca compara contra uma tabela não confirmada).

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import http.server
import json
import os
import re
import socket
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-imt-jovem.html").read_text(encoding="utf-8")
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(
        f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-imt-jovem.html"
    )


CALCULO_JS = _extrair_script_inline("function calcularIMTJovem")


def _parametros_de_producao() -> dict:
    """Lê dados/parametros.json e monta o mesmo formato que
    PARAMETROS_IMT_JOVEM tem em runtime — nunca valores hardcoded aqui."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    hab = todos["prestacoes"]["habitacao"]
    return {
        "isencaoTotalLimite": hab["imt_isencao_total_limite_eur"],
        "isencaoParcialLimite": hab["imt_isencao_parcial_limite_eur"],
        "taxaExcedente": hab["imt_taxa_sobre_excedente_pct"],
        "limiteIsento": hab["imt_geral_hpp_limite_isento_eur"],
        "esc2Limite": hab["imt_geral_hpp_esc2_limite_eur"],
        "esc2Taxa": hab["imt_geral_hpp_esc2_taxa_pct"],
        "esc2Abater": hab["imt_geral_hpp_esc2_abater_eur"],
        "esc3Limite": hab["imt_geral_hpp_esc3_limite_eur"],
        "esc3Taxa": hab["imt_geral_hpp_esc3_taxa_pct"],
        "esc3Abater": hab["imt_geral_hpp_esc3_abater_eur"],
        "esc4Taxa": hab["imt_geral_hpp_esc4_taxa_pct"],
        "esc4Abater": hab["imt_geral_hpp_esc4_abater_eur"],
        "esc5Taxa": hab["imt_geral_hpp_esc5_taxa_pct"],
        "esc5Abater": hab["imt_geral_hpp_esc5_abater_eur"],
        "esc6Limite": hab["imt_geral_hpp_esc6_limite_eur"],
        "esc6Taxa": hab["imt_geral_hpp_esc6_taxa_pct"],
        "esc7Taxa": hab["imt_geral_hpp_esc7_taxa_pct"],
        "isTaxa": hab["is_aquisicao_taxa_pct"],
    }


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

TODAS_AS_CONDICOES = {"temIdade": True, "naoDependente": True, "semPropriedade": True}


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _calcular(pagina, entrada):
    return pagina.evaluate(
        "([params, entrada]) => calcularIMTJovem(params, entrada)",
        [_parametros_de_producao(), entrada],
    )


# ── Coerência interna dos parâmetros (a própria tabela é auto-consistente) ──
def test_parcelas_a_abater_derivam_exactamente_dos_limites(pagina):
    """A tabela prática oficial é matematicamente auto-consistente:
    abater_n = abater_{n-1} + limite_{n-1} × (taxa_n − taxa_{n-1}). Se a
    actualização anual mudar um limite sem recalcular as parcelas (ou
    vice-versa), este teste falha sozinho."""
    p = _parametros_de_producao()
    v = lambda nome: p[nome]["valor"]  # noqa: E731
    assert round(v("esc2Abater"), 2) == round(v("limiteIsento") * v("esc2Taxa") / 100, 2)
    assert round(v("esc3Abater"), 2) == round(
        v("esc2Abater") + v("esc2Limite") * (v("esc3Taxa") - v("esc2Taxa")) / 100, 2)
    assert round(v("esc4Abater"), 2) == round(
        v("esc3Abater") + v("esc3Limite") * (v("esc4Taxa") - v("esc3Taxa")) / 100, 2)
    assert round(v("esc5Abater"), 2) == round(
        v("esc4Abater") + v("isencaoTotalLimite") * (v("esc5Taxa") - v("esc4Taxa")) / 100, 2)


def test_taxa_do_excedente_e_a_taxa_marginal_do_5o_escalao(pagina):
    # Por lei (art. 9.º-A remete para os escalões do art. 17.º), a taxa de
    # 8% da isenção parcial É a taxa marginal do escalão 330.539-660.982€.
    p = _parametros_de_producao()
    assert p["taxaExcedente"]["valor"] == p["esc5Taxa"]["valor"]


def test_parametros_producao_todos_verificados(pagina):
    params = _parametros_de_producao()
    assert params["isencaoTotalLimite"]["valor"] == 330539
    assert params["isencaoParcialLimite"]["valor"] == 660982
    assert params["isTaxa"]["valor"] == 0.8
    for chave in params:
        assert params[chave]["verificado_em"], f"{chave} sem verificado_em"
        assert params[chave]["referencia_legal"], f"{chave} sem referencia_legal"
        assert params[chave]["fonte_url"], f"{chave} sem fonte_url"


# ── Golden tests — isenção total ────────────────────────────────────────────
def test_250000_isencao_total_imt_e_is_zero(pagina):
    # Caso-âncora da spec: 250.000€ → 0€/0€ com isenção; sem isenção,
    # 250.000×7% − 10.457,96 = 7.042,04€ de IMT + 2.000,00€ de IS.
    r = _calcular(pagina, {"valorCompra": 250000, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "total"
    assert r["imtComIsencao"] == 0
    assert r["isComIsencao"] == 0
    assert r["imtSemIsencao"] == 7042.04
    assert r["isSemIsencao"] == 2000.00
    assert r["poupancaTotal"] == 9042.04


def test_fronteira_exacta_330539_ainda_isencao_total(pagina):
    r = _calcular(pagina, {"valorCompra": 330539, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "total"
    assert r["imtComIsencao"] == 0
    # Sem isenção: 330.539×7% − 10.457,96 = 23.137,73 − 10.457,96 = 12.679,77
    assert r["imtSemIsencao"] == 12679.77


def test_fronteira_330540_ja_paga_sobre_1_euro_de_excedente(pagina):
    r = _calcular(pagina, {"valorCompra": 330540, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "parcial"
    assert r["excedente"] == 1
    assert r["imtComIsencao"] == 0.08   # 8% × 1€
    assert r["isComIsencao"] == 0.01    # 0,8% × 1€ = 0,008 → 0,01


# ── Golden tests — isenção parcial ──────────────────────────────────────────
def test_400000_isencao_parcial_caso_ancora_da_spec(pagina):
    # 400.000 − 330.539 = 69.461€ de excedente:
    #   IMT = 8% × 69.461 = 5.556,88€ · IS = 0,8% × 69.461 = 555,69€
    # Sem isenção: 400.000×8% − 13.763,35 = 18.236,65€ · IS = 3.200,00€
    r = _calcular(pagina, {"valorCompra": 400000, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "parcial"
    assert r["excedente"] == 69461
    assert r["imtComIsencao"] == 5556.88
    assert r["isComIsencao"] == 555.69
    assert r["imtSemIsencao"] == 18236.65
    assert r["isSemIsencao"] == 3200.00
    assert r["poupancaIMT"] == 12679.77
    assert r["poupancaIS"] == 2644.31
    assert r["poupancaTotal"] == 15324.08


def test_exemplo_publicado_340000_reproduzido_ao_centimo(pagina):
    """imt-jovem.html publica desde a Sessão 1 (fonte: Doutor Finanças):
    340.000€ → 832,57€ pagos com a isenção vs 16.156,65€ sem ela —
    poupança de 15.324,08€. A tabela verificada nesta sessão tem de
    reproduzir os três números ao cêntimo; e a página tem de continuar a
    dizer o mesmo (coerência artigo↔simulador, nunca divergem)."""
    r = _calcular(pagina, {"valorCompra": 340000, **TODAS_AS_CONDICOES})
    total_com = round(r["imtComIsencao"] + r["isComIsencao"], 2)
    total_sem = round(r["imtSemIsencao"] + r["isSemIsencao"], 2)
    assert total_com == 832.57
    assert total_sem == 16156.65
    assert r["poupancaTotal"] == 15324.08
    artigo = (RAIZ / "imt-jovem.html").read_text(encoding="utf-8")
    for publicado in ("832,57", "16.156,65", "15.324,08"):
        assert publicado in artigo, f"exemplo publicado ({publicado}) desapareceu do artigo"


def test_fronteira_exacta_660982_ultimo_euro_com_isencao_parcial(pagina):
    r = _calcular(pagina, {"valorCompra": 660982, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "parcial"
    assert r["excedente"] == 330443
    assert r["imtComIsencao"] == 26435.44  # 8% × 330.443
    assert r["isComIsencao"] == 2643.54    # 0,8% × 330.443 = 2.643,544 → 2.643,54


def test_fronteira_660983_ja_sem_isencao_taxa_unica_6(pagina):
    r = _calcular(pagina, {"valorCompra": 660983, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "sem_isencao"
    assert r["imtComIsencao"] == r["imtSemIsencao"] == 39658.98  # 6% × 660.983
    assert r["poupancaTotal"] == 0


# ── Golden tests — sem isenção (tabela geral) ───────────────────────────────
def test_700000_caso_ancora_da_spec_tabela_geral(pagina):
    # 660.982 < 700.000 ≤ 1.150.853 → taxa única de 6% sobre o total:
    # IMT = 42.000,00€ · IS = 0,8% × 700.000 = 5.600,00€ · poupança 0.
    r = _calcular(pagina, {"valorCompra": 700000, **TODAS_AS_CONDICOES})
    assert r["escalao"] == "sem_isencao"
    assert r["imtComIsencao"] == r["imtSemIsencao"] == 42000.00
    assert r["isComIsencao"] == r["isSemIsencao"] == 5600.00
    assert r["poupancaIMT"] == 0
    assert r["poupancaIS"] == 0
    assert r["poupancaTotal"] == 0


def test_acima_de_1150853_taxa_unica_7_5(pagina):
    r = _calcular(pagina, {"valorCompra": 1200000, **TODAS_AS_CONDICOES})
    assert r["imtSemIsencao"] == 90000.00  # 7,5% × 1.200.000
    r2 = _calcular(pagina, {"valorCompra": 1150853, **TODAS_AS_CONDICOES})
    assert r2["imtSemIsencao"] == 69051.18  # 6% × 1.150.853 (último euro do escalão de 6%)


# ── Tabela geral — escalões baixos (só relevantes para a coluna sem isenção)
def test_tabela_geral_ate_ao_limite_isento_nao_paga_imt(pagina):
    r = _calcular(pagina, {"valorCompra": 106346, **TODAS_AS_CONDICOES})
    assert r["imtSemIsencao"] == 0
    assert r["isSemIsencao"] == 850.77  # o IS de 0,8% é devido mesmo abaixo do limite de IMT


def test_tabela_geral_1_euro_acima_do_limite_isento(pagina):
    r = _calcular(pagina, {"valorCompra": 106347, **TODAS_AS_CONDICOES})
    assert r["imtSemIsencao"] == 0.02  # 106.347×2% − 2.126,92 = 2.126,94 − 2.126,92


def test_tabela_geral_escalao_5_por_cento(pagina):
    # 180.000×5% − 6.491,02 = 9.000 − 6.491,02 = 2.508,98 (exemplo real
    # confirmado no PASSO 0 em fonte independente).
    r = _calcular(pagina, {"valorCompra": 180000, **TODAS_AS_CONDICOES})
    assert r["imtSemIsencao"] == 2508.98


# ── Elegibilidade — checklist incompleta nunca mostra poupança ─────────────
@pytest.mark.parametrize("em_falta", ["temIdade", "naoDependente", "semPropriedade"])
def test_qualquer_condicao_em_falta_fica_inelegivel(pagina, em_falta):
    condicoes = dict(TODAS_AS_CONDICOES)
    condicoes[em_falta] = False
    r = _calcular(pagina, {"valorCompra": 250000, **condicoes})
    assert r["elegivel"] is False


def test_todas_as_condicoes_marcadas_fica_elegivel(pagina):
    r = _calcular(pagina, {"valorCompra": 250000, **TODAS_AS_CONDICOES})
    assert r["elegivel"] is True


# ── VPT — a base é sempre o maior entre preço e VPT ─────────────────────────
def test_vpt_superior_ao_preco_usa_o_vpt(pagina):
    r = _calcular(pagina, {"valorCompra": 300000, "vpt": 350000, **TODAS_AS_CONDICOES})
    assert r["usouVPT"] is True
    assert r["base"] == 350000
    assert r["escalao"] == "parcial"  # 350.000 > 330.539 por causa do VPT


def test_vpt_inferior_ao_preco_usa_o_preco(pagina):
    r = _calcular(pagina, {"valorCompra": 350000, "vpt": 300000, **TODAS_AS_CONDICOES})
    assert r["usouVPT"] is False
    assert r["base"] == 350000


def test_vpt_ausente_usa_o_preco(pagina):
    r = _calcular(pagina, {"valorCompra": 250000, **TODAS_AS_CONDICOES})
    assert r["usouVPT"] is False
    assert r["base"] == 250000


# ── Formatação PT determinística ────────────────────────────────────────────
def test_formatar_euro_pt_e_nunca_menos_zero(pagina):
    assert pagina.evaluate("formatarEuro(5556.88)") == "5.556,88 €"
    assert pagina.evaluate("formatarEuro(0)") == "0,00 €"
    assert pagina.evaluate("formatarEuro(-0)") == "0,00 €"
    assert pagina.evaluate("formatarEuro(1150853)") == "1.150.853,00 €"


# ── Runtime real: fetch de /dados/parametros.json (sucesso e falha) ────────
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


@pytest.fixture()
def pagina_real(servidor):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        yield page, servidor
        browser.close()


def _preencher_e_submeter(page, valor, vpt=None, marcar=("chkIdade", "chkNaoDependente", "chkSemPropriedade")):
    page.fill("#valorCompra", str(valor))
    if vpt is not None:
        page.fill("#vpt", str(vpt))
    for chk in marcar:
        page.check(f"#{chk}")
    page.click("#btnCalcularIMTJovem")
    page.wait_for_selector("#resultado.show", timeout=5000)
    return page.inner_text("#resultado")


def test_runtime_fetch_com_sucesso_calcula_o_caso_400000(pagina_real):
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-imt-jovem.html")
    page.wait_for_function(
        "document.getElementById('btnCalcularIMTJovem').disabled === false", timeout=5000)
    assert page.evaluate("document.getElementById('avisoParametrosErro').style.display") != "block"

    texto = _preencher_e_submeter(page, 400000)
    assert "5.556,88" in texto      # IMT com isenção
    assert "18.236,65" in texto     # IMT sem isenção
    assert "15.324,08" in texto     # poupança total


def test_runtime_checklist_incompleta_nunca_mostra_poupanca(pagina_real):
    # Decisão explícita da spec: NUNCA mostrar valores de poupança a um
    # inelegível — verificada de ponta a ponta, não só na função pura.
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-imt-jovem.html")
    page.wait_for_function(
        "document.getElementById('btnCalcularIMTJovem').disabled === false", timeout=5000)

    texto = _preencher_e_submeter(page, 400000, marcar=("chkIdade", "chkNaoDependente"))
    assert "Sem direito à isenção" in texto
    assert "Poupas" not in texto
    for valor in ("5.556,88", "18.236,65", "15.324,08"):
        assert valor not in texto, f"valor de poupança ({valor}) mostrado a um inelegível"


def test_runtime_vpt_superior_mostra_o_aviso_e_usa_o_vpt(pagina_real):
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-imt-jovem.html")
    page.wait_for_function(
        "document.getElementById('btnCalcularIMTJovem').disabled === false", timeout=5000)

    texto = _preencher_e_submeter(page, 300000, vpt=350000)
    assert "VPT" in texto
    assert "350.000,00" in texto  # a base mostrada é o VPT, não o preço


def test_runtime_fetch_com_falha_bloqueia_o_botao_e_nunca_calcula(pagina_real):
    page, servidor = pagina_real
    page.route("**/dados/parametros.json", lambda route: route.abort())
    page.goto(f"{servidor}/simulador-imt-jovem.html")
    page.wait_for_function(
        "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000)
    assert page.evaluate("document.getElementById('btnCalcularIMTJovem').disabled") is True

    # Mesmo tentando contornar o disabled via JS, a guarda em
    # calcularIMTJovemFormulario() nunca deixa o resultado aparecer.
    page.evaluate("document.getElementById('btnCalcularIMTJovem').removeAttribute('disabled')")
    page.fill("#valorCompra", "400000")
    page.check("#chkIdade")
    page.check("#chkNaoDependente")
    page.check("#chkSemPropriedade")
    page.click("#btnCalcularIMTJovem")
    page.wait_for_timeout(300)
    assert "show" not in (page.get_attribute("#resultado", "class") or "")
