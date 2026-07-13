"""
Testes da mecânica de cálculo do simulador do subsídio de desemprego
(simulador-subsidio-desemprego.html), executados num browser real
(Chromium headless via Playwright) — extrai o JS inline directamente do
HTML real, nunca uma cópia à parte (mesma filosofia de
test_simulador_rsi_calculo.py/test_simulador_subsidio_doenca_calculo.py).

Cobre a matriz de casos aprovada na Fase 3 do desenho deste simulador
(ver CLAUDE.md/histórico de sessão): casos simples, mínimo/mínimo
majorado, máximo/máximo majorado, prazo de garantia (regime geral e TI
com cessação de actividade), duração (escalões etários × escalões de
meses, majoração por carreira longa, redução por atraso na
apresentação), validação de inputs inválidos (decimais, texto não-
-numérico, campos obrigatórios vs. opcionais), datas de nascimento e
precisão numérica (nunca -0,00€ nem resíduos de ponto flutuante).

Os dois casos de regressão obrigatórios (Fase 3, aprovados): "1.200€/mês
→ 780€/mês" e "52 anos, >24 meses, 20 anos de registo → 780 dias" são
os exemplos já publicados em subsidio-desemprego.html.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
import socket
import threading
import http.server
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-subsidio-desemprego.html").read_text(encoding="utf-8")
ARTIGO_HTML = (RAIZ / "subsidio-desemprego.html").read_text(encoding="utf-8")


def _extrair_script_inline(texto: str, marcador: str, nome_ficheiro: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", texto):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em {nome_ficheiro}")


CALCULO_JS = _extrair_script_inline(
    SIMULADOR_HTML, "function calcularSubsidioDesemprego", "simulador-subsidio-desemprego.html"
)


def _localizar_chromium():
    """Mesma estratégia de localização multi-nível já usada nos outros
    simuladores — nunca assumir uma única convenção de path entre
    sandbox de desenvolvimento e CI (ver histórico em CLAUDE.md)."""
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
    """Página em branco + só o <script> de cálculo injectado — para os
    testes das funções puras (calcularSubsidioDesemprego/calcularDuracao/
    validarInputSubsidioDesemprego/calcularIdade/formatarEuro), sem
    depender de nenhum elemento de formulário."""
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor():
    """Servidor HTTP local para os testes de interacção real com o
    formulário (validação de UI) — a página real, não uma cópia,
    incluindo o formulário e os event listeners de produção."""
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
        page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
        page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
        page.goto(f"{servidor}/simulador-subsidio-desemprego.html", wait_until="domcontentloaded")
        yield page
        browser.close()


PARAMS_DEFAULT = {
    "remuneracao": 1200, "idade": 35, "meses": 30, "anosRegisto": 0,
    "diasApresentacao": 0, "vinculo": "conta_outrem", "ambosConjuges": False,
}


def _calcular(pagina, entrada):
    entrada_completa = dict(PARAMS_DEFAULT)
    entrada_completa.update(entrada)
    return pagina.evaluate(
        "([params, entrada]) => calcularSubsidioDesemprego(params, entrada)",
        [pagina.evaluate("PARAMETROS_SUBSIDIO_DESEMPREGO"), entrada_completa],
    )


def _duracao(pagina, entrada):
    entrada_completa = dict(PARAMS_DEFAULT)
    entrada_completa.update(entrada)
    return pagina.evaluate(
        "([params, entrada]) => calcularDuracao(params, entrada)",
        [pagina.evaluate("PARAMETROS_SUBSIDIO_DESEMPREGO"), entrada_completa],
    )


def _validar(pagina, bruto_parcial):
    bruto = {
        "remuneracao": "1200", "dataNascimento": "1990-01-01", "dataHoje": "2026-07-13",
        "meses": "30", "anosRegisto": "", "diasApresentacao": "",
        "vinculo": "conta_outrem", "ambosConjuges": False,
    }
    bruto.update(bruto_parcial)
    return pagina.evaluate("(bruto) => validarInputSubsidioDesemprego(bruto)", bruto)


def _idade(pagina, nascimento, referencia):
    return pagina.evaluate(
        "([n, r]) => calcularIdade(n, r)", [nascimento, referencia]
    )


def _formatar(pagina, valor):
    return pagina.evaluate("(v) => formatarEuro(v)", valor)


# ── A. Caso de regressão obrigatório — exemplo publicado no artigo ──────────

def test_a1_caso_de_regressao_1200_por_mes_780_euros(pagina):
    """1.200€/mês → 780€/mês, exemplo publicado em subsidio-desemprego.html
    (secção "Como se calcula")."""
    r = _calcular(pagina, {"remuneracao": 1200})
    assert r["rrDiaria"] == 40.00
    assert r["subsidioDiarioBruto"] == 26.00
    assert r["subsidioMensalBruto"] == 780.00
    assert r["valorMensal"] == 780.00
    assert "780" in ARTIGO_HTML


def test_a2_caso_de_regressao_duracao_52_anos_780_dias(pagina):
    """52 anos, >24 meses, 20 anos de registo → 540 + 240 = 780 dias,
    exemplo publicado em subsidio-desemprego.html (secção "Duração")."""
    d = _duracao(pagina, {"idade": 52, "meses": 30, "anosRegisto": 20})
    assert d["duracaoBase"] == 540
    assert d["acrescimo"] == 240
    assert d["duracaoFinal"] == 780
    assert "780 dias" in ARTIGO_HTML


# ── B. Mínimo e mínimo majorado ──────────────────────────────────────────────

def test_b1_remuneracao_baixa_aplica_minimo(pagina):
    r = _calcular(pagina, {"remuneracao": 300})
    # RR diária = 300×12/360 = 10,00 ; ×65% = 6,50/dia ; ×30 = 195,00 < mínimo
    assert r["subsidioMensalBruto"] == 195.00
    assert r["minimoAplicavel"] == 537.13  # remuneração < salário mínimo (920)
    assert r["valorMensal"] == 537.13
    assert r["minimoAplicado"] is True


def test_b2_remuneracao_igual_ao_salario_minimo_aplica_minimo_majorado(pagina):
    r = _calcular(pagina, {"remuneracao": 920})
    assert r["minimoAplicavel"] == 617.70
    # RR diária = 920×12/360 = 30,6667 ; ×65% = 19,9333 ; ×30 = 598,00 < 617,70
    assert r["valorMensal"] == 617.70
    assert r["minimoAplicado"] is True


def test_b3_remuneracao_um_centimo_abaixo_do_salario_minimo_nao_majora(pagina):
    r = _calcular(pagina, {"remuneracao": 919.99})
    assert r["minimoAplicavel"] == 537.13


# ── C. Máximo e máximo majorado ──────────────────────────────────────────────

def test_c1_remuneracao_alta_aplica_maximo(pagina):
    r = _calcular(pagina, {"remuneracao": 5000})
    # RR diária = 5000×12/360 = 166,6667 → arred. 166,67 ; ×65% = 108,3355
    # → arred. 108,34 ; ×30 = 3250,20 > máximo (cada passo arredondado a
    # cêntimos antes do próximo, por desenho — nunca só no fim)
    assert r["rrDiaria"] == 166.67
    assert r["subsidioDiarioBruto"] == 108.34
    assert r["subsidioMensalBruto"] == 3250.20
    assert r["maximoAplicavel"] == 1342.83
    assert r["valorMensal"] == 1342.83
    assert r["maximoAplicado"] is True


def test_c2_ambos_conjuges_aplica_maximo_majorado(pagina):
    r = _calcular(pagina, {"remuneracao": 5000, "ambosConjuges": True})
    assert r["maximoAplicavel"] == 1477.11
    assert r["valorMensal"] == 1477.11
    assert r["maximoAplicado"] is True


def test_c3_ambos_conjuges_sem_ultrapassar_maximo_normal_nao_muda_valor(pagina):
    r_normal = _calcular(pagina, {"remuneracao": 1200, "ambosConjuges": False})
    r_conjuges = _calcular(pagina, {"remuneracao": 1200, "ambosConjuges": True})
    assert r_normal["valorMensal"] == r_conjuges["valorMensal"] == 780.00


# ── D. Prazo de garantia — elegibilidade ─────────────────────────────────────

def test_d1_conta_outrem_360_dias_exatos_e_elegivel(pagina):
    r = _calcular(pagina, {"vinculo": "conta_outrem", "meses": 12})  # 12×30=360
    assert r["elegivel"] is True
    assert r["limiarGarantiaDias"] == 360


def test_d2_conta_outrem_um_mes_abaixo_nao_elegivel_mas_calculo_aparece(pagina):
    r = _calcular(pagina, {"vinculo": "conta_outrem", "meses": 11})  # 330 < 360
    assert r["elegivel"] is False
    assert r["valorMensal"] == 780.00  # breakdown nunca desaparece


def test_d3_ti_dependente_mesmo_limiar_que_conta_outrem(pagina):
    r = _calcular(pagina, {"vinculo": "ti_dependente", "meses": 12})
    assert r["limiarGarantiaDias"] == 360
    assert r["elegivel"] is True


def test_d4_ti_cessacao_exige_720_dias(pagina):
    r = _calcular(pagina, {"vinculo": "ti_cessacao", "meses": 24})  # 720 dias exatos
    assert r["limiarGarantiaDias"] == 720
    assert r["elegivel"] is True


def test_d5_ti_cessacao_23_meses_nao_elegivel(pagina):
    r = _calcular(pagina, {"vinculo": "ti_cessacao", "meses": 23})  # 690 < 720
    assert r["elegivel"] is False


# ── E. Duração — escalões etários × escalões de meses ────────────────────────

@pytest.mark.parametrize("idade,meses,dias_esperados", [
    (25, 10, 150), (25, 20, 210), (25, 30, 330),
    (35, 10, 180), (35, 20, 330), (35, 30, 420),
    (45, 10, 210), (45, 20, 360), (45, 30, 540),
    (55, 10, 270), (55, 20, 480), (55, 30, 540),
])
def test_e_tabela_duracao_base_por_idade_e_meses(pagina, idade, meses, dias_esperados):
    d = _duracao(pagina, {"idade": idade, "meses": meses, "anosRegisto": 0})
    assert d["duracaoBase"] == dias_esperados
    assert d["acrescimo"] == 0
    assert d["duracaoFinal"] == dias_esperados


def test_e_fronteira_15_16_meses_muda_de_escalao(pagina):
    d15 = _duracao(pagina, {"idade": 35, "meses": 15})
    d16 = _duracao(pagina, {"idade": 35, "meses": 16})
    assert d15["duracaoBase"] == 180
    assert d16["duracaoBase"] == 330


def test_e_fronteira_24_25_meses_muda_de_escalao(pagina):
    d24 = _duracao(pagina, {"idade": 35, "meses": 24})
    d25 = _duracao(pagina, {"idade": 35, "meses": 25})
    assert d24["duracaoBase"] == 330
    assert d25["duracaoBase"] == 420


def test_e_fronteira_idade_29_30(pagina):
    d29 = _duracao(pagina, {"idade": 29, "meses": 30})
    d30 = _duracao(pagina, {"idade": 30, "meses": 30})
    assert d29["duracaoBase"] == 330
    assert d30["duracaoBase"] == 420


def test_e_fronteira_idade_49_50(pagina):
    d49 = _duracao(pagina, {"idade": 49, "meses": 30})
    d50 = _duracao(pagina, {"idade": 50, "meses": 30})
    assert d49["duracaoBase"] == 540
    assert d50["duracaoBase"] == 540  # ambos 540, mas por linhas diferentes da tabela


def test_e_acrescimo_so_se_aplica_no_escalao_mais24(pagina):
    # <=24 meses nunca tem acréscimo, mesmo com anos de registo elevados
    d = _duracao(pagina, {"idade": 55, "meses": 20, "anosRegisto": 30})
    assert d["acrescimo"] == 0
    assert d["motivoAcrescimo"] is None


def test_e_acrescimo_menos_de_40_anos(pagina):
    d = _duracao(pagina, {"idade": 35, "meses": 30, "anosRegisto": 10})
    assert d["acrescimo"] == 60  # 2 grupos × 30 dias


def test_e_acrescimo_40_a_49_anos(pagina):
    d = _duracao(pagina, {"idade": 45, "meses": 30, "anosRegisto": 10})
    assert d["acrescimo"] == 90  # 2 grupos × 45 dias


def test_e_acrescimo_grupos_incompletos_nao_contam(pagina):
    # 9 anos = 1 grupo completo de 5 (o segundo grupo fica incompleto)
    d = _duracao(pagina, {"idade": 35, "meses": 30, "anosRegisto": 9})
    assert d["acrescimo"] == 30  # só 1 grupo


def test_e_atraso_na_apresentacao_reduz_duracao(pagina):
    d = _duracao(pagina, {"idade": 35, "meses": 30, "diasApresentacao": 100})
    # atraso = 100 - 90 = 10 dias
    assert d["atraso"] == 10
    assert d["duracaoFinal"] == d["duracaoTotal"] - 10


def test_e_dentro_do_prazo_nunca_gera_atraso(pagina):
    d = _duracao(pagina, {"idade": 35, "meses": 30, "diasApresentacao": 90})
    assert d["atraso"] == 0


def test_e_duracao_final_nunca_negativa(pagina):
    d = _duracao(pagina, {"idade": 25, "meses": 10, "diasApresentacao": 9999})
    assert d["duracaoFinal"] == 0


# ── F. Validação — obrigatórios vs. opcionais, decimais, texto inválido ─────

def test_f1_remuneracao_vazia_bloqueia(pagina):
    v = _validar(pagina, {"remuneracao": ""})
    assert v["valido"] is False
    assert any(e["campo"] == "remuneracao" for e in v["erros"])


def test_f2_remuneracao_texto_invalido_bloqueia(pagina):
    v = _validar(pagina, {"remuneracao": "abc"})
    assert v["valido"] is False


def test_f3_remuneracao_com_virgula_decimal_e_aceite(pagina):
    v = _validar(pagina, {"remuneracao": "1200,50"})
    assert v["valido"] is True
    assert v["valoresNormalizados"]["remuneracao"] == 1200.50


def test_f4_meses_vazio_bloqueia(pagina):
    v = _validar(pagina, {"meses": ""})
    assert v["valido"] is False
    assert any(e["campo"] == "meses" for e in v["erros"])


def test_f5_meses_decimal_e_invalido(pagina):
    v = _validar(pagina, {"meses": "12.5"})
    assert v["valido"] is False
    assert "inteiro" in v["erros"][0]["mensagem"] or any("inteiro" in e["mensagem"] for e in v["erros"])


def test_f6_anos_registo_vazio_e_zero_nunca_erro(pagina):
    v = _validar(pagina, {"anosRegisto": ""})
    assert v["valido"] is True
    assert v["valoresNormalizados"]["anosRegisto"] == 0


def test_f7_anos_registo_decimal_bloqueia(pagina):
    v = _validar(pagina, {"anosRegisto": "5.5"})
    assert v["valido"] is False


def test_f8_dias_apresentacao_vazio_e_zero_nunca_erro(pagina):
    v = _validar(pagina, {"diasApresentacao": ""})
    assert v["valido"] is True
    assert v["valoresNormalizados"]["diasApresentacao"] == 0


def test_f9_dias_apresentacao_decimal_bloqueia(pagina):
    v = _validar(pagina, {"diasApresentacao": "10.5"})
    assert v["valido"] is False


def test_f10_data_nascimento_vazia_bloqueia(pagina):
    v = _validar(pagina, {"dataNascimento": ""})
    assert v["valido"] is False


def test_f11_data_nascimento_no_futuro_bloqueia(pagina):
    v = _validar(pagina, {"dataNascimento": "2026-12-31", "dataHoje": "2026-07-13"})
    assert v["valido"] is False


def test_f12_varios_erros_simultaneos_todos_reportados(pagina):
    v = _validar(pagina, {"remuneracao": "", "meses": "abc", "anosRegisto": "1.5"})
    assert v["valido"] is False
    campos = {e["campo"] for e in v["erros"]}
    assert campos == {"remuneracao", "meses", "anosRegisto"}


# ── G. Cálculo de idade — datas de nascimento ───────────────────────────────

def test_g1_exatamente_18_anos_aniversario_hoje(pagina):
    assert _idade(pagina, "2008-07-13", "2026-07-13") == 18


def test_g2_vespera_do_aniversario(pagina):
    assert _idade(pagina, "2008-07-14", "2026-07-13") == 17


def test_g3_nascido_em_29_fevereiro(pagina):
    assert _idade(pagina, "2008-02-29", "2026-07-13") == 18
    assert _idade(pagina, "2008-02-29", "2026-02-28") == 17


# ── H. Precisão numérica — nunca -0,00€ nem resíduos de ponto flutuante ─────

def test_h1_valor_zero_nunca_negativo(pagina):
    r = _calcular(pagina, {"remuneracao": 0})
    assert r["valorMensal"] == 537.13  # cai sempre no mínimo, nunca fica zero/negativo
    formatado = _formatar(pagina, 0)
    assert formatado == "€0.00"
    assert not formatado.startswith("-")


def test_h2_arredondamento_a_centimos_sem_residuo(pagina):
    r = _calcular(pagina, {"remuneracao": 333.33})
    # RR diária = 333.33×12/360 = 11.1110 → arredondado 11.11
    assert r["rrDiaria"] == 11.11
    formatado = _formatar(pagina, r["rrDiaria"])
    assert formatado == "€11.11"


def test_h3_formatarEuro_nunca_mostra_menos_zero(pagina):
    assert _formatar(pagina, -0.001) != "-€0.00"
    assert _formatar(pagina, 0) == "€0.00"


# ── Testes de interacção real com o formulário (validação de UI) ───────────

def test_ui_remuneracao_vazia_bloqueia_submissao_e_mostra_erro(pagina_real):
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.fill("#meses", "30")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroRemuneracao")
    assert not pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")


def test_ui_meses_texto_invalido_bloqueia_submissao(pagina_real):
    pagina_real.fill("#remuneracao", "1200")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.fill("#meses", "abc")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroMeses")
    assert not pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")


def test_ui_caso_valido_mostra_breakdown_e_duracao(pagina_real):
    pagina_real.fill("#remuneracao", "1200")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.fill("#meses", "30")
    pagina_real.click("button[type=submit]")
    assert pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")
    texto = pagina_real.inner_text("#resultado")
    assert "780.00" in texto or "780,00" in texto
    assert "Duração estimada" in texto
    assert "Remuneração de Referência" in texto


def test_ui_inelegivel_nunca_esconde_breakdown(pagina_real):
    pagina_real.fill("#remuneracao", "1200")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.fill("#meses", "5")  # 150 dias < 360, inelegível
    pagina_real.click("button[type=submit]")
    assert pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")
    texto = pagina_real.inner_text("#resultado")
    assert "780.00" in texto or "780,00" in texto
    assert "prazo de garantia" in texto.lower()


def test_ui_campo_anos_registo_so_aparece_acima_de_24_meses(pagina_real):
    pagina_real.fill("#meses", "20")
    assert not pagina_real.eval_on_selector("#grupoAnosRegisto", "el => el.classList.contains('show')")
    pagina_real.fill("#meses", "25")
    assert pagina_real.eval_on_selector("#grupoAnosRegisto", "el => el.classList.contains('show')")


def test_ui_limpar_remove_resultado_e_erros(pagina_real):
    pagina_real.fill("#meses", "abc")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.fill("#remuneracao", "1200")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroMeses")
    pagina_real.click("#btnLimpar")
    assert not pagina_real.is_visible("#erroMeses")


# ── Coerência artigo ↔ simulador ─────────────────────────────────────────────

def test_coerencia_artigo_simulador_constantes_de_producao(pagina):
    """Rede de segurança: se subsidio-desemprego.html for actualizado sem
    o simulador (ou vice-versa), este teste falha antes de qualquer
    divergência passar despercebida."""
    params = pagina.evaluate("PARAMETROS_SUBSIDIO_DESEMPREGO")

    assert params["ias"]["valor"] == 537.13
    assert params["salarioMinimo"]["valor"] == 920.00
    assert params["percentagemRR"]["valor"] == 0.65
    assert params["divisorRR"]["valor"] == 360
    assert params["minimo"]["valor"] == 537.13
    assert params["minimoMajorado"]["valor"] == 617.70
    assert params["maximo"]["valor"] == 1342.83
    assert params["maximoMajorado"]["valor"] == 1477.11
    assert params["garantiaDiasGeral"]["valor"] == 360
    assert params["garantiaDiasTiCessacao"]["valor"] == 720
    assert params["prazoRequerimentoDias"]["valor"] == 90
    assert params["acrescimoAte40"]["valor"] == 30
    assert params["acrescimo40a49"]["valor"] == 45
    assert params["acrescimo50Mais"]["valor"] == 60

    for valor_esperado in ["537,13", "617,70", "349,13", "1.342,83", "1.477,11"]:
        assert valor_esperado in ARTIGO_HTML, f"'{valor_esperado}' não encontrado em subsidio-desemprego.html"

    for chave in params:
        assert params[chave]["verificado_em"] is not None, f"{chave} sem verificado_em"
        assert params[chave]["fonte"], f"{chave} sem fonte"


def test_nenhum_valor_legal_escrito_diretamente_na_logica_de_calculo():
    """Fase 3 (aprovada): nenhum valor legal solto no meio da lógica —
    confirma que os números "mágicos" só aparecem dentro de
    PARAMETROS_SUBSIDIO_DESEMPREGO, nunca dentro do corpo de
    calcularSubsidioDesemprego/calcularDuracao/validarInputSubsidioDesemprego."""
    corpo_calculo = re.search(
        r"function calcularSubsidioDesemprego\(params, input\) \{([\s\S]*?)\n    \}",
        CALCULO_JS,
    )
    assert corpo_calculo, "não encontrei o corpo de calcularSubsidioDesemprego"
    for valor_proibido in ["537.13", "617.70", "1342.83", "1477.11", "360", "720", "90"]:
        assert valor_proibido not in corpo_calculo.group(1), (
            f"valor legal '{valor_proibido}' escrito directamente em "
            "calcularSubsidioDesemprego() — tem de vir de PARAMETROS_SUBSIDIO_DESEMPREGO"
        )
