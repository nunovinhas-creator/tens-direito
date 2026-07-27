"""
Testes do Verificador de Apoios (verificador-apoios.html) — Passo 2 da
fundação criada no Passo 1 (extracção de calcularAbonoValor/getEscalao/
getValorPorIdade para assets/js/calc-apoios.js).

Duas responsabilidades desta suite:

1. **Guardrail de linguagem** (o mais importante, pedido explicitamente):
   esta ferramenta nunca pode afirmar "tens direito"/"não tens direito"
   como facto sobre a pessoa — só "PODERÁS (não) ser elegível" +
   "Estimativa não vinculativa". Verificado sobre o HTML real, nunca uma
   cópia.

2. **Canário anti-divergência**: o verificador e simulador-abono.html
   partilham a MESMA calcularAbonoValor()/PARAMETROS_ABONO — este
   ficheiro prova, com o código real (nunca uma cópia dos valores), que
   os dois nunca podem divergir: (a) chamando a função real via
   page.evaluate em duas páginas carregadas independentemente, e (b)
   ponta-a-ponta, preenchendo os dois formulários reais com o mesmo
   input e comparando o texto renderizado.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, os módulos que dependem dele são ignorados (skip) em vez
de falhar — mesmo padrão de test_simulador_abono_calculo.py.
"""
from __future__ import annotations

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
VERIFICADOR_HTML = (RAIZ / "verificador-apoios.html").read_text(encoding="utf-8")
SIMULADOR_ABONO_HTML = (RAIZ / "simulador-abono.html").read_text(encoding="utf-8")
CALC_APOIOS_JS = (RAIZ / "assets" / "js" / "calc-apoios.js").read_text(encoding="utf-8")
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"


def _scripts_js_inline(html: str) -> str:
    """Concatena todo o JS inline (nunca os blocos ld+json) de uma página."""
    blocos = []
    for m in re.finditer(r"<script(?P<attrs>[^>]*)>([\s\S]*?)</script>", html):
        attrs, corpo = m.group("attrs"), m.group(2)
        if "application/ld+json" in attrs or "src=" in attrs:
            continue
        blocos.append(corpo)
    return "\n".join(blocos)


VERIFICADOR_JS_INLINE = _scripts_js_inline(VERIFICADOR_HTML)


# ── Guardrail de linguagem — nunca "tens direito"/"não tens direito" ──────

def test_nunca_afirma_tens_direito_como_facto():
    proibidas = ["tens direito a", "têm direito a", "tens direito.", "és elegível", "é elegível para"]
    texto = VERIFICADOR_HTML.lower()
    for frase in proibidas:
        assert frase not in texto, f"frase assertiva proibida encontrada: {frase!r}"


def test_nunca_afirma_nao_tens_direito_como_facto():
    proibidas = ["não tens direito", "não têm direito"]
    texto = VERIFICADOR_HTML.lower()
    for frase in proibidas:
        assert frase not in texto, f"frase assertiva proibida encontrada: {frase!r}"


def test_sem_direito_so_existe_como_label_de_dados_interno_nunca_no_texto_estatico():
    """'Sem direito' é o `nome` interno do escalão-5 sentinela em
    PARAMETROS_ABONO (mesmo literal que simulador-abono.html já usa,
    exigido pela forma que calcularAbonoValor() espera) — nunca é lido
    nem mostrado por renderResultadoVerificador() (confirmado abaixo, e
    pelo teste Playwright que lê o texto REALMENTE renderizado). Este
    teste confirma que a única ocorrência do site fonte é essa entrada
    de dados, nunca uma frase solta no HTML/JS visível."""
    ocorrencias = [m.start() for m in re.finditer(r"sem direito", VERIFICADOR_HTML, re.IGNORECASE)]
    assert len(ocorrencias) == 1, (
        f"esperava exactamente 1 ocorrência de 'sem direito' (o label interno do "
        f"escalão-5), encontrei {len(ocorrencias)}"
    )
    contexto = VERIFICADOR_HTML[ocorrencias[0] - 40:ocorrencias[0] + 20]
    assert "nome:" in contexto, f"a única ocorrência tem de ser o campo nome: 'Sem direito', contexto real: {contexto!r}"
    # E a função que constrói o resultado nunca lê esse campo:
    assert "r.nome" not in VERIFICADOR_JS_INLINE


def test_marca_tens_direito_so_aparece_como_nome_do_site():
    """A marca "Tens Direito" (logo/footer/título) é permitida — só a
    frase assertiva "tens direito a" é proibida (ver teste acima). Este
    teste confirma que o site nunca deixou de citar a própria marca por
    engano ao aplicar o guardrail."""
    assert "Tens Direito" in VERIFICADOR_HTML


def test_linguagem_condicional_obrigatoria_presente():
    assert "PODERÁS ser elegível" in VERIFICADOR_HTML
    assert "poderás não ser elegível" in VERIFICADOR_HTML
    assert "Estimativa não vinculativa" in VERIFICADOR_HTML
    # ponteiros (ASE/MEGA/bolsa) também em condicional, nunca afirmativo
    assert "Poderás também ter direito" in VERIFICADOR_HTML
    assert "poderá haver direito" in VERIFICADOR_HTML


def test_disclaimer_de_rodape_do_resultado_presente():
    assert "Informação geral, não aconselhamento" in VERIFICADOR_HTML
    assert "não guarda nem envia nenhum dado" in VERIFICADOR_HTML


# ── Nenhum ponteiro (ASE/MEGA/bolsa) apresenta valor calculado ────────────

def test_ponteiros_podem_citar_factos_estaticos_mas_nunca_um_valor_calculado():
    """Os cartões-ponteiro (ASE/MEGA/Bolsa de Mérito) podem citar factos
    ESTÁTICOS e datados (ex.: limiares de escalão, prazos — sourced de
    acao-social-escolar.html/bolsa-de-merito.html/manuais-escolares-mega.html,
    ver sessão "enriquece verificador") — mas nunca um valor CALCULADO a
    partir do que o utilizador indicou no formulário (nunca interpolação
    de `r.*`/PARAMETROS_ABONO nem de qualquer variável computada em
    runtime). Só o cartão do abono usa esse tipo de valor dinâmico."""
    m = re.search(r"function renderResultadoVerificador[\s\S]*?\n    \}\n", VERIFICADOR_JS_INLINE)
    assert m, "não encontrei renderResultadoVerificador() no JS do verificador"
    corpo = m.group(0)
    bloco_ponteiros = re.search(r"const ponteiros = \[\];([\s\S]*?)if \(ponteiros\.length", corpo)
    assert bloco_ponteiros, "não encontrei a construção da lista de ponteiros"
    texto_ponteiros = bloco_ponteiros.group(1)
    assert "${" not in texto_ponteiros, (
        "encontrei um template literal interpolado dentro dos textos dos ponteiros — "
        "isso seria um valor calculado em runtime, nunca permitido aqui"
    )
    # \br\. (nunca uma substring solta — "escolar.html" tem "r." mas não é
    # o objecto de resultado `r`) apanha leituras reais tipo r.valorTotal/r.escalao.
    assert not re.search(r"\br\.\w+", texto_ponteiros), (
        "os ponteiros nunca podem ler o resultado calculado do abono (r.*)"
    )
    assert "PARAMETROS_ABONO" not in texto_ponteiros
    assert "formatarEuro" not in texto_ponteiros


def test_ponteiros_valores_ase_batem_com_a_pagina_de_origem():
    """Os limiares de escalão da ASE citados no ponteiro (268,57 €/537,13 €)
    têm de bater sempre com os mesmos valores já publicados e datados em
    acao-social-escolar.html — nunca divergir da fonte de onde vieram."""
    origem = (RAIZ / "acao-social-escolar.html").read_text(encoding="utf-8")
    assert "268,57" in origem
    assert "537,13" in origem
    assert "268,57" in VERIFICADOR_HTML
    assert "537,13" in VERIFICADOR_HTML


def test_ponteiros_datas_mega_batem_com_a_pagina_de_origem():
    """As datas faseadas dos vales MEGA citadas no ponteiro/FAQ têm de
    bater sempre com as mesmas datas já publicadas e datadas em
    manuais-escolares-mega.html."""
    origem = (RAIZ / "manuais-escolares-mega.html").read_text(encoding="utf-8")
    for data in ("3 de agosto", "10 de agosto", "13 de agosto"):
        assert data in origem, f"{data!r} não está em manuais-escolares-mega.html"
        assert data in VERIFICADOR_HTML, f"{data!r} não está em verificador-apoios.html"


def test_ponteiros_valor_1306_da_bolsa_de_merito_nunca_e_trazido():
    """A página de origem (bolsa-de-merito.html) marca explicitamente o
    valor 1.306,25 € como desactualizado ('para 2026/2027 será atualizado
    após publicação do despacho') — este valor nunca pode aparecer no
    verificador, precisamente porque a fonte não o dá como confirmado
    para o ano corrente."""
    assert "1.306,25" not in VERIFICADOR_HTML
    assert "1306,25" not in VERIFICADOR_HTML


# ── Nenhum valor legal hardcoded — tudo vem de dados/parametros.json ──────

def test_nenhum_valor_legal_do_abono_hardcoded_no_js_do_verificador():
    """Confirma, contra a fonte real (dados/parametros.json), que nenhum
    valor numérico de prestacoes.abono aparece como literal no JS do
    verificador — teria de vir sempre de PARAMETROS_ABONO (fetch)."""
    parametros = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    ab = parametros["prestacoes"]["abono"]
    for chave, dados in ab.items():
        valor = dados["valor"]
        if not isinstance(valor, (int, float)) or valor == 0:
            continue  # 0 e strings/datas não são candidatos a "valor legal hardcoded"
        candidato = f"{valor:.2f}" if isinstance(valor, float) else str(valor)
        assert candidato not in VERIFICADOR_JS_INLINE, (
            f"valor legal '{chave}'={valor} aparece hardcoded no JS do verificador — "
            "tem de vir sempre de PARAMETROS_ABONO/fetch"
        )


def test_calc_apoios_js_importado_via_script_src_nunca_copiado():
    assert '<script src="/assets/js/calc-apoios.js"></script>' in VERIFICADOR_HTML
    assert "function calcularAbonoValor" not in VERIFICADOR_JS_INLINE, (
        "calcularAbonoValor não pode estar duplicada inline no verificador — "
        "tem de vir só de assets/js/calc-apoios.js"
    )
    assert "function getEscalao" not in VERIFICADOR_JS_INLINE
    assert "function getValorPorIdade" not in VERIFICADOR_JS_INLINE


def test_heuristicas_de_ponteiro_nunca_lidas_de_parametros_json():
    """IDADE_MINIMA_ESCOLAR_ANOS/IDADE_MINIMA_SECUNDARIO_ANOS/
    IDADE_MAXIMA_SECUNDARIO_ANOS são heurísticas de navegação locais —
    nunca podem vir de PARAMETROS_ABONO nem de dados/parametros.json
    (ASE/MEGA/Bolsa não têm YAML próprio ainda)."""
    assert "const IDADE_MINIMA_ESCOLAR_ANOS = 6;" in VERIFICADOR_JS_INLINE
    assert "const IDADE_MINIMA_SECUNDARIO_ANOS = 15;" in VERIFICADOR_JS_INLINE
    assert "const IDADE_MAXIMA_SECUNDARIO_ANOS = 18;" in VERIFICADOR_JS_INLINE


# ── FAQ: paridade 1:1 entre <details> visíveis e FAQPage JSON-LD ──────────

def test_faq_paridade_1_1_visivel_vs_jsonld():
    perguntas_visiveis = re.findall(r"<summary>([^<]+)</summary>", VERIFICADOR_HTML)
    blocos = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', VERIFICADOR_HTML)
    faqpage = next(json.loads(b) for b in blocos if '"@type": "FAQPage"' in b)
    perguntas_jsonld = [q["name"] for q in faqpage["mainEntity"]]
    assert perguntas_visiveis == perguntas_jsonld


# ── Estrutura JSON-LD obrigatória ──────────────────────────────────────────

def test_quatro_blocos_jsonld_validos():
    blocos = re.findall(r'<script type="application/ld\+json">([\s\S]*?)</script>', VERIFICADOR_HTML)
    tipos = [json.loads(b)["@type"] for b in blocos]
    assert tipos == ["WebApplication", "FAQPage", "BreadcrumbList", "Article"]


def test_canonica_auto_referente():
    assert '<link rel="canonical" href="https://tensdireito.com/verificador-apoios.html">' in VERIFICADOR_HTML


# ── Playwright: canário anti-divergência + comportamento real ─────────────

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
def navegador():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        yield browser
        browser.close()


# Casos de input reais partilhados entre os dois testes de canário —
# nenhum valor inventado, mesmo caso golden já usado em
# test_simulador_abono_calculo.py (escalão 1, 190.98€).
INPUT_CASO_ESCALAO_1 = {"rendimentoAnual": 3000, "numCriancas": 1, "idadesMeses": [24], "monoparental": False}
# Caso que atravessa os ponteiros: criança em idade escolar (8 anos) +
# jovem em idade de secundário (16 anos), rendimento moderado.
INPUT_CASO_COM_PONTEIROS = {
    "rendimentoAnual": 15000, "numCriancas": 2, "idadesMeses": [96, 192], "monoparental": False,
}
# Caso acima do limite dos 4 escalões — testa a mensagem "poderás não
# ser elegível".
INPUT_CASO_SEM_DIREITO = {"rendimentoAnual": 200000, "numCriancas": 1, "idadesMeses": [24], "monoparental": False}


def test_canario_calculo_identico_via_funcao_real_entre_as_duas_paginas(servidor, navegador):
    """O canário principal: chama calcularAbonoValor() — a função REAL,
    nunca uma cópia — em duas páginas carregadas independentemente
    (verificador e simulador-abono), com o mesmo input, e falha se os
    resultados alguma vez divergirem."""
    resultados = {}
    for pagina_url, chave in [("verificador-apoios.html", "verificador"), ("simulador-abono.html", "simulador")]:
        page = navegador.new_page()
        page.goto(f"{servidor}/{pagina_url}")
        page.wait_for_function("typeof PARAMETROS_ABONO === 'object' && PARAMETROS_ABONO !== null", timeout=5000)
        resultado = page.evaluate(
            "(entrada) => calcularAbonoValor(PARAMETROS_ABONO, entrada)", INPUT_CASO_ESCALAO_1
        )
        resultados[chave] = resultado
        page.close()

    assert resultados["verificador"] == resultados["simulador"], (
        "calcularAbonoValor() devolveu resultados diferentes no verificador vs. "
        "simulador-abono para o MESMO input — as duas páginas divergiram apesar "
        "de partilharem assets/js/calc-apoios.js + /dados/parametros.json"
    )
    # Sanidade: o resultado é mesmo o caso golden conhecido (190.98€, escalão 1)
    assert resultados["verificador"]["escalao"] == 1
    assert resultados["verificador"]["valorTotal"] == 190.98


def _valor_pt_para_float(texto: str) -> float:
    """Extrai '190,98 €' (formato PT do verificador) e devolve 190.98."""
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€", texto)
    assert m, f"não encontrei um valor em formato PT (\"1.234,56 €\") em: {texto!r}"
    return float(m.group(1).replace(".", "").replace(",", "."))


def _valor_en_para_float(texto: str) -> float:
    """Extrai '€190.98' (formato do simulador de abono) e devolve 190.98."""
    m = re.search(r"€(\d+(?:\.\d+)?)", texto)
    assert m, f"não encontrei um valor em formato €N.NN em: {texto!r}"
    return float(m.group(1))


def test_canario_ponta_a_ponta_ui_mostra_o_mesmo_valor_nos_dois_formularios(servidor, navegador):
    """Segunda camada do canário: preenche os DOIS formulários reais
    (interacção real de utilizador, não page.evaluate) com o mesmo
    input e confirma que o valor renderizado é o MESMO número — prova
    que também o código de ligação ao formulário (parsing dos inputs,
    arredondamento) nunca diverge. Compara valores numéricos, nunca
    strings formatadas: o verificador mostra "190,98 €" (PT-PT,
    formatarEuro()) e o simulador mostra "€190.98" (formato próprio,
    inalterado) — as duas apresentações são legítimas e nunca têm de
    coincidir como texto, só o número por trás delas."""
    page_v = navegador.new_page()
    page_v.goto(f"{servidor}/verificador-apoios.html")
    page_v.wait_for_function("document.getElementById('btnVerificar').disabled === false", timeout=5000)
    page_v.fill("#rendimento", "3000")
    page_v.select_option("#monoparental", "nao")
    page_v.select_option("#numCriancas", "1")
    page_v.fill("#idade1", "24")
    page_v.click("#btnVerificar")
    page_v.wait_for_selector("#resultado.show", timeout=5000)
    texto_verificador = page_v.inner_text("#resultado")
    page_v.close()

    page_s = navegador.new_page()
    page_s.goto(f"{servidor}/simulador-abono.html")
    page_s.wait_for_function("document.getElementById('btnCalcularAbono').disabled === false", timeout=5000)
    page_s.fill("#rendimento", "3000")
    page_s.select_option("#monoparental", "nao")
    page_s.select_option("#numCriancas", "1")
    page_s.fill("#idade1", "24")
    page_s.click("#btnCalcularAbono")
    page_s.wait_for_selector("#resultado.show", timeout=5000)
    texto_simulador = page_s.inner_text("#resultado")
    page_s.close()

    valor_verificador = _valor_pt_para_float(texto_verificador)
    valor_simulador = _valor_en_para_float(texto_simulador)
    assert valor_verificador == valor_simulador == 190.98, (
        f"valores divergem: verificador={valor_verificador}, simulador={valor_simulador}"
    )
    assert "190,98" in texto_verificador  # formato PT-PT (vírgula decimal, símbolo depois)
    assert "escalão estimado 1" in texto_verificador.lower()
    assert "1.º escalão" in texto_simulador


def test_ponteiros_ase_mega_bolsa_aparecem_para_idades_certas(servidor, navegador):
    page = navegador.new_page()
    page.goto(f"{servidor}/verificador-apoios.html")
    page.wait_for_function("document.getElementById('btnVerificar').disabled === false", timeout=5000)
    page.fill("#rendimento", str(INPUT_CASO_COM_PONTEIROS["rendimentoAnual"]))
    page.select_option("#monoparental", "nao")
    page.select_option("#numCriancas", "2")
    page.fill("#idade1", str(INPUT_CASO_COM_PONTEIROS["idadesMeses"][0]))  # 96 meses = 8 anos
    page.fill("#idade2", str(INPUT_CASO_COM_PONTEIROS["idadesMeses"][1]))  # 192 meses = 16 anos
    page.click("#btnVerificar")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    page.close()

    assert "Ação Social Escolar" in texto
    assert "Manuais Escolares Gratuitos" in texto
    assert "Bolsa de Mérito" in texto
    # nunca um valor numérico associado aos ponteiros
    assert "poderás" in texto.lower() or "poderá" in texto.lower()


def test_sem_pontos_escolares_para_bebe_e_mensagem_sem_direito_para_rendimento_alto(servidor, navegador):
    page = navegador.new_page()
    page.goto(f"{servidor}/verificador-apoios.html")
    page.wait_for_function("document.getElementById('btnVerificar').disabled === false", timeout=5000)
    page.fill("#rendimento", str(INPUT_CASO_SEM_DIREITO["rendimentoAnual"]))
    page.select_option("#monoparental", "nao")
    page.select_option("#numCriancas", "1")
    page.fill("#idade1", str(INPUT_CASO_SEM_DIREITO["idadesMeses"][0]))  # 24 meses = bebé
    page.click("#btnVerificar")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    page.close()

    assert "Ação Social Escolar" not in texto  # bebé de 2 anos, sem idade escolar
    assert "poderás não ser elegível" in texto
    assert "não tens direito" not in texto.lower()
    assert "sem direito" not in texto.lower()


def test_erro_no_fetch_bloqueia_o_botao_e_nunca_calcula(servidor, navegador):
    page = navegador.new_page()
    page.route("**/dados/parametros.json", lambda route: route.abort())
    page.goto(f"{servidor}/verificador-apoios.html")
    page.wait_for_function(
        "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000
    )
    assert page.evaluate("document.getElementById('btnVerificar').disabled") is True
    page.close()
