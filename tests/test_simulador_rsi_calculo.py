"""
Testes da mecânica de cálculo do simulador do RSI
(simulador-rsi.html), executados num browser real (Chromium headless
via Playwright) — extrai o JS inline directamente do HTML real, nunca
uma cópia à parte (mesma filosofia de
test_simulador_csi_calculo.py/test_simulador_subsidio_doenca_calculo.py).

Cobre a matriz de casos aprovada na Fase 3 do desenho deste simulador
(ver CLAUDE.md/histórico de sessão): casos simples, casais, família
monoparental, agregados numerosos (sem tecto), rendimento zero, limite
exacto/imediatamente abaixo/acima, património, residência, "não sei",
validação de inputs inválidos (decimais em adultos/menores, texto não-
-numérico em rendimentos — nunca convertido a 0 em silêncio), datas de
nascimento (elegibilidade por idade) e precisão numérica (nunca -0,00€
nem resíduos de ponto flutuante).

O caso "2 adultos + 2 crianças, subsídio de desemprego 450€ → 218,41€"
é o exemplo já publicado em rsi.html e no CLAUDE.md (secção
"Acumulação") — teste de regressão obrigatório (Fase 3, ponto 6 da
aprovação): se este valor mudar, há uma regressão.

Migração para o padrão OpenFisca (2026-08-24, ver
dados/parametros/rsi.yaml): PARAMETROS_RSI deixou de ser um objecto JS
inline — passa a ser carregado em runtime de /dados/parametros.json.
Os golden tests da mecânica pura (`calcularRSI`) constroem `params`
directamente a partir de dados/parametros.json (nunca de um
`PARAMETROS_RSI` global da página, que fica `null` na página em branco
usada pela fixture `pagina`) — mesmo padrão de
test_simulador_csi_calculo.py. O comportamento de runtime (fetch com
sucesso/falha, nunca calcular com valores em falta) tem os seus
próprios testes mais abaixo, servidos por um http.server real (nunca
file://).

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import json
import os
import re
import socket
import threading
import http.server
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
SIMULADOR_HTML = (RAIZ / "simulador-rsi.html").read_text(encoding="utf-8")
ARTIGO_HTML = (RAIZ / "rsi.html").read_text(encoding="utf-8")


def _extrair_script_inline(texto: str, marcador: str, nome_ficheiro: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", texto):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em {nome_ficheiro}")


CALCULO_JS = _extrair_script_inline(SIMULADOR_HTML, "function calcularRSI", "simulador-rsi.html")


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
    testes das funções puras (calcularRSI/validarInputRSI/calcularIdade/
    formatarEuro), sem depender de nenhum elemento de formulário."""
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
        page.goto(f"{servidor}/simulador-rsi.html", wait_until="domcontentloaded")
        # Os parâmetros carregam de forma assíncrona (fetch de
        # /dados/parametros.json) — esperar que o botão fique activo
        # antes de qualquer interacção, senão o clique acontece com o
        # botão ainda `disabled` (mesmo padrão de
        # test_simulador_csi_calculo.py).
        page.wait_for_function("document.getElementById('btnCalcularRSI').disabled === false", timeout=5000)
        yield page
        browser.close()


PARAMS_DEFAULT = {
    "adultos": 1, "menores": 0, "dependente": 0, "independente": 0,
    "subsidioDesemprego": 0, "outros": 0, "idade": 30,
    "residenciaLegal": "sim", "patrimonio": "dentro",
}


def _parametros_rsi_de_producao() -> dict:
    """Lê dados/parametros.json (a "nova fonte") e monta o mesmo formato
    que PARAMETROS_RSI tem em runtime (ver carregarParametrosRSI() em
    simulador-rsi.html) — nunca valores hardcoded aqui. O limite de
    património continua derivado do IAS (multiplicador × ias), nunca um
    valor em euros escrito à mão."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    rsi = todos["prestacoes"]["rsi"]
    limite_patrimonio_valor = rsi["limite_patrimonio_multiplicador_ias"]["valor"] * rsi["ias_2026"]["valor"]
    return {
        "anoReferencia": {"valor": 2026},
        "valorTitular": rsi["valor_titular_mensal"],
        "valorAdultoAdicional": rsi["valor_adulto_adicional_mensal"],
        "valorMenor": rsi["valor_menor_mensal"],
        "ias": rsi["ias_2026"],
        "limitePatrimonio": {
            "valor": limite_patrimonio_valor,
            "referencia_legal": rsi["limite_patrimonio_multiplicador_ias"]["referencia_legal"],
        },
        "percentagemDependente": rsi["percentagem_rendimento_trabalho_dependente"],
        "percentagemIndependente": rsi["percentagem_rendimento_trabalho_independente"],
        "percentagemSubsidioDesemprego": rsi["percentagem_subsidio_desemprego"],
        "percentagemOutros": rsi["percentagem_outros_rendimentos"],
        "idadeMinima": rsi["idade_minima_anos"],
    }


def _calcular(pagina, entrada):
    entrada_completa = dict(PARAMS_DEFAULT)
    entrada_completa.update(entrada)
    return pagina.evaluate(
        "([params, entrada]) => calcularRSI(params, entrada)",
        [_parametros_rsi_de_producao(), entrada_completa],
    )


def _validar(pagina, bruto_parcial):
    bruto = {
        "adultos": "", "menores": "", "dependente": "", "independente": "",
        "subsidioDesemprego": "", "outros": "", "dataNascimento": "2000-01-01",
        "dataHoje": "2026-07-13", "residenciaLegal": "sim", "patrimonio": "dentro",
    }
    bruto.update(bruto_parcial)
    return pagina.evaluate("(bruto) => validarInputRSI(bruto)", bruto)


def _idade(pagina, nascimento, referencia):
    return pagina.evaluate(
        "([n, r]) => calcularIdade(n, r)", [nascimento, referencia]
    )


def _formatar(pagina, valor):
    return pagina.evaluate("(v) => formatarEuro(v)", valor)


# ── A. Casos simples ─────────────────────────────────────────────────────────

def test_a1_pessoa_sozinha_sem_rendimento(pagina):
    r = _calcular(pagina, {"adultos": 1, "menores": 0})
    assert r["valorMaximo"] == 247.56
    assert r["rendimentoConsiderado"] == 0
    assert r["valorRSI"] == 247.56
    assert r["avisos"] == []


def test_a2_pessoa_sozinha_dependente_parcial(pagina):
    r = _calcular(pagina, {"adultos": 1, "dependente": 200})
    # 0,80 × 200 = 160,00 ; 247,56 − 160,00 = 87,56
    assert r["rendimentoConsiderado"] == 160.00
    assert r["valorRSI"] == 87.56


def test_a3_pessoa_sozinha_so_independente(pagina):
    r = _calcular(pagina, {"adultos": 1, "independente": 200})
    assert r["rendimentoConsiderado"] == 200.00
    assert r["valorRSI"] == 47.56


# ── B. Casais ─────────────────────────────────────────────────────────────────

def test_b1_casal_sem_rendimento(pagina):
    r = _calcular(pagina, {"adultos": 2})
    assert r["valorMaximo"] == 420.85
    assert r["valorRSI"] == 420.85
    assert len(r["componentesMaximo"]) == 2


def test_b2_casal_rendimento_dependente_supera_maximo(pagina):
    r = _calcular(pagina, {"adultos": 2, "dependente": 1000})
    # 420,85 − 800,00 = -379,15 → floor em 0
    assert r["valorRSI"] == 0
    assert r["rendimentoExcedeMaximo"] is True
    assert any(a["tipo"] == "valor_zero" for a in r["avisos"])


# ── C. Casais com filhos (incl. caso de regressão obrigatório) ──────────────

def test_c1_casal_1_filho_bate_com_tabela_do_artigo(pagina):
    r = _calcular(pagina, {"adultos": 2, "menores": 1})
    assert r["valorMaximo"] == 544.63
    assert "544,63" in ARTIGO_HTML


def test_c2_caso_de_regressao_publicado_no_artigo_e_no_claude_md(pagina):
    """Caso de regressão obrigatório (Fase 3, ponto 6, aprovado):
    2 adultos + 2 crianças, subsídio de desemprego 450€ → 218,41€. Este
    valor está publicado em rsi.html (FAQ + secção de acumulação) e no
    CLAUDE.md — nunca pode divergir sem ser uma regressão real."""
    r = _calcular(pagina, {"adultos": 2, "menores": 2, "subsidioDesemprego": 450})
    assert r["valorMaximo"] == 668.41
    assert r["rendimentoConsiderado"] == 450.00
    assert r["valorRSI"] == 218.41
    assert "668,41" in ARTIGO_HTML
    assert "218,41" in ARTIGO_HTML


def test_c3_casal_1_filho_rendimento_dependente(pagina):
    r = _calcular(pagina, {"adultos": 2, "menores": 1, "dependente": 300})
    assert r["valorMaximo"] == 544.63
    assert r["rendimentoConsiderado"] == 240.00
    assert r["valorRSI"] == 304.63


# ── D. Família monoparental ──────────────────────────────────────────────────

def test_d1_um_adulto_tres_filhos(pagina):
    r = _calcular(pagina, {"adultos": 1, "menores": 3})
    assert r["valorMaximo"] == 618.90
    assert len(r["componentesMaximo"]) == 2  # titular + menores, sem "adulto adicional"


def test_d2_um_adulto_um_filho_outros_rendimentos(pagina):
    r = _calcular(pagina, {"adultos": 1, "menores": 1, "outros": 100})
    assert r["valorMaximo"] == 371.34
    assert r["valorRSI"] == 271.34


# ── E. Agregados numerosos — sem tecto ───────────────────────────────────────

def test_e1_dois_adultos_cinco_menores_sem_tecto(pagina):
    r = _calcular(pagina, {"adultos": 2, "menores": 5})
    assert r["valorMaximo"] == 1039.75


def test_e2_quatro_adultos_seis_menores(pagina):
    r = _calcular(pagina, {"adultos": 4, "menores": 6})
    assert r["valorMaximo"] == 1510.11


# ── F. Rendimento zero ───────────────────────────────────────────────────────

def test_f1_todos_os_rendimentos_zero_ou_vazios(pagina):
    r = _calcular(pagina, {"adultos": 2, "menores": 1})
    assert r["rendimentoConsiderado"] == 0
    assert r["valorRSI"] == 544.63
    assert r["componentesRendimento"] == []


# ── G. Limite exacto / fronteiras de 1 cêntimo ──────────────────────────────

def test_g1_rendimento_exactamente_no_limite_nunca_menos_zero(pagina):
    r = _calcular(pagina, {"adultos": 1, "outros": 247.56})
    assert r["valorRSI"] == 0
    assert not (str(r["valorRSI"]).startswith("-"))
    formatado = _formatar(pagina, r["valorRSI"])
    assert formatado == "€0.00"


def test_g2_um_centimo_abaixo_do_limite(pagina):
    r = _calcular(pagina, {"adultos": 1, "outros": 247.55})
    assert r["valorRSI"] == 0.01


def test_g3_um_centimo_acima_do_limite(pagina):
    r = _calcular(pagina, {"adultos": 1, "outros": 247.57})
    assert r["valorRSI"] == 0
    assert r["rendimentoExcedeMaximo"] is True


def test_g4_rendimento_muito_acima_do_limite(pagina):
    r = _calcular(pagina, {"adultos": 1, "outros": 50000})
    assert r["valorRSI"] == 0


# ── H. Património acima do limite — breakdown nunca desaparece ─────────────

def test_h1_patrimonio_ultrapassa_mostra_breakdown_completo(pagina):
    r = _calcular(pagina, {"adultos": 2, "menores": 1, "dependente": 300, "patrimonio": "ultrapassa"})
    assert r["valorRSI"] == 304.63
    assert r["componentesMaximo"] != []
    assert r["componentesRendimento"] != []
    assert any(a["tipo"] == "patrimonio_ultrapassa" for a in r["avisos"])


def test_h2_patrimonio_ultrapassa_e_rendimento_cobre_maximo_dois_avisos(pagina):
    r = _calcular(pagina, {"adultos": 1, "outros": 300, "patrimonio": "ultrapassa"})
    tipos = [a["tipo"] for a in r["avisos"]]
    assert "patrimonio_ultrapassa" in tipos
    assert "valor_zero" in tipos
    assert r["valorRSI"] == 0


# ── I. Residência legal = Não ────────────────────────────────────────────────

def test_i1_sem_residencia_mostra_breakdown_completo(pagina):
    r = _calcular(pagina, {"adultos": 1, "residenciaLegal": "nao"})
    assert r["valorRSI"] == 247.56
    assert any(a["tipo"] == "residencia" for a in r["avisos"])


def test_i2_tres_gates_falhados_em_simultaneo(pagina):
    r = _calcular(pagina, {"adultos": 1, "idade": 16, "residenciaLegal": "nao", "patrimonio": "ultrapassa"})
    tipos = [a["tipo"] for a in r["avisos"]]
    assert set(tipos) == {"idade", "residencia", "patrimonio_ultrapassa"}
    assert r["valorMaximo"] == 247.56  # cálculo continua a aparecer


# ── J. Património "não sei" — nunca afecta o número ─────────────────────────

def test_j1_patrimonio_nao_sei_nunca_afecta_o_valor(pagina):
    r = _calcular(pagina, {"adultos": 2})
    r_nao_sei = _calcular(pagina, {"adultos": 2, "patrimonio": "nao_sei"})
    assert r["valorRSI"] == r_nao_sei["valorRSI"]
    assert any(a["tipo"] == "patrimonio_nao_sei" for a in r_nao_sei["avisos"])


# ── M. Casos extremos ────────────────────────────────────────────────────────

def test_m1_quatro_tipos_de_rendimento_simultaneos(pagina):
    r = _calcular(pagina, {
        "adultos": 2, "menores": 2, "dependente": 2000, "independente": 1000,
        "subsidioDesemprego": 800, "outros": 500,
    })
    # 0,8×2000 + 1000 + 800 + 500 = 1600+1000+800+500 = 3900
    assert r["rendimentoConsiderado"] == 3900.00
    assert r["valorRSI"] == 0
    assert len(r["componentesRendimento"]) == 4


def test_m2_agregado_muito_grande(pagina):
    r = _calcular(pagina, {"adultos": 10, "menores": 10})
    assert r["valorMaximo"] == 3044.97


def test_m3_rendimento_com_muitas_casas_decimais_arredonda_correctamente(pagina):
    r = _calcular(pagina, {"adultos": 1, "dependente": 333.333})
    # 0,8 × 333,333 = 266,6664 → arredondado a 266,67
    assert r["componentesRendimento"][0]["subtotal"] == 266.67


# ── N. Robustez de ponto flutuante ──────────────────────────────────────────

def test_n1_soma_de_percentagens_nunca_mostra_residuo_flutuante(pagina):
    r = _calcular(pagina, {"adultos": 1, "dependente": 100})
    assert r["componentesRendimento"][0]["subtotal"] == 80.00
    formatado = _formatar(pagina, r["componentesRendimento"][0]["subtotal"])
    assert formatado == "€80.00"


def test_n2_diferenca_exacta_nunca_fica_negativa_residual(pagina):
    r = _calcular(pagina, {"adultos": 2, "outros": 420.85})
    assert r["valorRSI"] == 0
    assert _formatar(pagina, r["valorRSI"]) == "€0.00"


def test_n3_idade_residencia_patrimonio_e_limite_exacto_em_simultaneo(pagina):
    r = _calcular(pagina, {
        "adultos": 1, "idade": 15, "outros": 247.56, "patrimonio": "nao_sei",
    })
    tipos = {a["tipo"] for a in r["avisos"]}
    assert tipos == {"idade", "patrimonio_nao_sei", "valor_zero"}
    assert r["valorRSI"] == 0


# ── Cálculo de idade — datas de nascimento (Fase 3, secção L) ───────────────

def test_l1_exactamente_18_anos_aniversario_hoje(pagina):
    assert _idade(pagina, "2008-07-13", "2026-07-13") == 18


def test_l2_17_anos_e_364_dias_vespera_do_18(pagina):
    assert _idade(pagina, "2008-07-14", "2026-07-13") == 17


def test_l3_nascido_em_29_fevereiro_ano_bissexto(pagina):
    assert _idade(pagina, "2008-02-29", "2026-07-13") == 18
    assert _idade(pagina, "2008-02-29", "2026-02-28") == 17


def test_l5_data_de_nascimento_muito_antiga_sem_teto_etario(pagina):
    assert _idade(pagina, "1900-01-01", "2026-07-13") == 126


# ── K. Validação — menores sem adultos / decimais / texto inválido ─────────

def test_k1_adultos_vazio_bloqueia_com_mensagem(pagina):
    v = _validar(pagina, {"adultos": "", "menores": "3"})
    assert v["valido"] is False
    assert any(e["campo"] == "adultos" for e in v["erros"])


def test_k1b_adultos_zero_bloqueia(pagina):
    v = _validar(pagina, {"adultos": "0"})
    assert v["valido"] is False


def test_k3_adultos_decimal_e_invalido_nunca_arredondado(pagina):
    v = _validar(pagina, {"adultos": "1.5"})
    assert v["valido"] is False
    assert "inteiro" in v["erros"][0]["mensagem"]


def test_k3b_menores_decimal_e_invalido(pagina):
    v = _validar(pagina, {"adultos": "2", "menores": "2.3"})
    assert v["valido"] is False


def test_campo_vazio_de_rendimento_e_zero_nunca_erro(pagina):
    v = _validar(pagina, {"adultos": "1", "dependente": ""})
    assert v["valido"] is True
    assert v["valoresNormalizados"]["dependente"] == 0


def test_texto_invalido_em_rendimento_nunca_convertido_a_zero_silenciosamente(pagina):
    v = _validar(pagina, {"adultos": "1", "dependente": "abc"})
    assert v["valido"] is False
    assert any(e["campo"] == "dependente" for e in v["erros"])


def test_rendimento_negativo_e_invalido(pagina):
    v = _validar(pagina, {"adultos": "1", "outros": "-50"})
    assert v["valido"] is False


def test_data_nascimento_vazia_bloqueia(pagina):
    v = _validar(pagina, {"adultos": "1", "dataNascimento": ""})
    assert v["valido"] is False


def test_data_nascimento_no_futuro_bloqueia(pagina):
    v = _validar(pagina, {"adultos": "1", "dataNascimento": "2026-12-31", "dataHoje": "2026-07-13"})
    assert v["valido"] is False


def test_rendimento_com_virgula_decimal_e_aceite(pagina):
    # PT-PT usa vírgula como separador decimal — o formulário aceita-a.
    v = _validar(pagina, {"adultos": "1", "dependente": "333,33"})
    assert v["valido"] is True
    assert round(v["valoresNormalizados"]["dependente"], 2) == 333.33


# ── Testes de interacção real com o formulário (validação de UI) ───────────

def test_ui_texto_invalido_bloqueia_submissao_e_mostra_erro(pagina_real):
    pagina_real.fill("#adultos", "1")
    pagina_real.fill("#dependente", "abc")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroDependente")
    assert not pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")


def test_ui_adultos_decimal_bloqueia_submissao(pagina_real):
    pagina_real.fill("#adultos", "1.5")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroAdultos")
    assert not pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")


def test_ui_caso_valido_mostra_breakdown_completo(pagina_real):
    pagina_real.fill("#adultos", "2")
    pagina_real.fill("#menores", "2")
    pagina_real.fill("#subsidioDesemprego", "450")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.click("button[type=submit]")
    assert pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")
    texto = pagina_real.inner_text("#resultado")
    assert "218.41" in texto or "218,41" in texto
    assert "Valor máximo" in texto
    assert "Rendimentos considerados" in texto
    assert "Cálculo final" in texto


def test_ui_patrimonio_ultrapassa_nunca_esconde_breakdown(pagina_real):
    pagina_real.fill("#adultos", "1")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.select_option("#patrimonio", "ultrapassa")
    pagina_real.click("button[type=submit]")
    assert pagina_real.eval_on_selector("#resultado", "el => el.classList.contains('show')")
    texto = pagina_real.inner_text("#resultado")
    assert "247.56" in texto or "247,56" in texto
    assert "património" in texto.lower()


def test_ui_aviso_psu_visivel_no_topo(pagina_real):
    assert pagina_real.is_visible(".aviso-psu-topo")
    assert "PSU" in pagina_real.inner_text(".aviso-psu-topo")


def test_ui_limpar_remove_resultado_e_erros(pagina_real):
    pagina_real.fill("#adultos", "abc")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.click("button[type=submit]")
    assert pagina_real.is_visible("#erroAdultos")
    pagina_real.click("#btnLimpar")
    assert not pagina_real.is_visible("#erroAdultos")


# ── Runtime real: fetch de /dados/parametros.json (sucesso e falha) ────────
# Migração 2026-08-24 — mesmo padrão de test_simulador_csi_calculo.py.
# `pagina_real` já espera o botão activar (ver a fixture acima), por isso
# estes dois testes cobrem exactamente o que essa espera está a garantir:
# o caso feliz (activa e calcula) e o caso de falha (nunca activa, nunca
# calcula, mesmo com bypass do `disabled`).

def test_runtime_fetch_com_sucesso_activa_o_botao_e_calcula(pagina_real):
    assert pagina_real.evaluate("document.getElementById('avisoParametrosErro').style.display") != "block"
    pagina_real.fill("#adultos", "2")
    pagina_real.fill("#menores", "2")
    pagina_real.fill("#subsidioDesemprego", "450")
    pagina_real.fill("#dataNascimento", "1990-01-01")
    pagina_real.click("button[type=submit]")
    pagina_real.wait_for_selector("#resultado.show", timeout=5000)
    texto = pagina_real.inner_text("#resultado")
    assert "218,41" in texto or "218.41" in texto  # mesmo exemplo do golden test


def test_runtime_fetch_com_falha_bloqueia_o_botao_e_nunca_calcula(servidor):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.route("**/dados/parametros.json", lambda route: route.abort())
        page.goto(f"{servidor}/simulador-rsi.html", wait_until="domcontentloaded")
        page.wait_for_function(
            "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000
        )
        assert page.evaluate("document.getElementById('btnCalcularRSI').disabled") is True
        assert page.evaluate("window.PARAMETROS_RSI === null || typeof window.PARAMETROS_RSI === 'undefined'") \
            or page.evaluate("PARAMETROS_RSI") is None

        # Mesmo contornando o `disabled` via JS, a guarda em
        # calcularRSIFormulario() nunca deixa o resultado aparecer sem
        # parâmetros carregados.
        page.evaluate("document.getElementById('btnCalcularRSI').removeAttribute('disabled')")
        page.fill("#adultos", "1")
        page.fill("#dataNascimento", "1990-01-01")
        page.click("#btnCalcularRSI")
        page.wait_for_timeout(300)
        assert "show" not in (page.get_attribute("#resultado", "class") or "")
        browser.close()


# ── Coerência artigo ↔ simulador ─────────────────────────────────────────────

def test_coerencia_artigo_simulador_constantes_de_producao(pagina):
    """Rede de segurança: se rsi.html for actualizado sem
    dados/parametros/rsi.yaml (ou vice-versa), este teste falha antes de
    qualquer divergência passar despercebida. Lê a mesma fonte que
    simulador-rsi.html consome em runtime (dados/parametros.json),
    nunca um PARAMETROS_RSI global — a página em branco da fixture
    `pagina` nunca faz fetch, por isso o global fica sempre `null` aqui."""
    params = _parametros_rsi_de_producao()

    assert params["valorTitular"]["valor"] == 247.56
    assert params["valorAdultoAdicional"]["valor"] == 173.29
    assert params["valorMenor"]["valor"] == 123.78
    assert params["ias"]["valor"] == 537.13
    assert params["limitePatrimonio"]["valor"] == 32227.80
    assert params["percentagemDependente"]["valor"] == 0.80
    assert params["percentagemIndependente"]["valor"] == 1.00
    assert params["percentagemSubsidioDesemprego"]["valor"] == 1.00
    assert params["percentagemOutros"]["valor"] == 1.00
    assert params["idadeMinima"]["valor"] == 18

    for valor_esperado in ["247,56", "173,29", "123,78", "537,13", "32.227,80"]:
        assert valor_esperado in ARTIGO_HTML, f"'{valor_esperado}' não encontrado em rsi.html"

    # anoReferencia e limitePatrimonio (derivado, sem verificado_em/
    # referencia_legal próprios no dicionário Python — vêm de dois
    # parâmetros combinados) ficam fora desta verificação; os restantes
    # 8 vêm directamente de dados/parametros/rsi.yaml.
    for chave in params:
        if chave in ("anoReferencia", "limitePatrimonio"):
            continue
        assert params[chave]["verificado_em"], f"{chave} sem verificado_em"
        assert params[chave]["referencia_legal"], f"{chave} sem referencia_legal"
        assert params[chave]["fonte_url"], f"{chave} sem fonte_url"


def test_nenhum_valor_legal_escrito_diretamente_na_logica_de_calculo():
    """Fase 3, ponto 7 (aprovado): nenhum valor legal solto no meio da
    lógica — confirma que os números "mágicos" 247.56/173.29/123.78/
    537.13/32227.80/2026 só aparecem dentro de PARAMETROS_RSI, nunca
    dentro do corpo de calcularRSI/validarInputRSI."""
    corpo_calcularRSI = re.search(
        r"function calcularRSI\(params, input\) \{([\s\S]*?)\n    \}\n\n    // ═",
        CALCULO_JS,
    )
    assert corpo_calcularRSI, "não encontrei o corpo de calcularRSI"
    for valor_proibido in ["247.56", "173.29", "123.78", "537.13", "32227.8", "2026"]:
        assert valor_proibido not in corpo_calcularRSI.group(1), (
            f"valor legal '{valor_proibido}' escrito directamente em calcularRSI() — "
            "tem de vir de PARAMETROS_RSI"
        )
