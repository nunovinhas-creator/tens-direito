"""
Testes da mecânica de cálculo do simulador do CSI (simulador-csi.html),
executados num browser real (Chromium headless via Playwright) — extrai
o JS inline directamente do HTML real, nunca uma cópia à parte (mesma
filosofia de test_simulador_psu_calculo.py/test_pesquisa_hero.py).

FASE 2 da sessão de dados abertos (2026-07-19): PARAMETROS_CSI deixou de
ser um objecto JS inline — passa a ser carregado em runtime de
/dados/parametros.json (gerado de dados/parametros/csi.yaml). Os golden
tests da mecânica pura (`calcularCSI`) constroem `params` directamente a
partir de dados/parametros.json (a "nova fonte" pedida pela sessão),
nunca de um `PARAMETROS_CSI` global da página — `calcularCSI(params,
input)` continua uma função pura, testável sem depender de fetch/rede.
O comportamento de runtime (fetch com sucesso/falha, nunca calcular com
valores em falta) tem os seus próprios testes mais abaixo, servidos por
um http.server real (nunca file://).

CORRECÇÃO PASSO 0 (2026-07-19, mesma sessão): a 1.ª migração desta
sessão copiou os valores de PARAMETROS_CSI sem os revalidar contra a
fonte primária — os diplomas citados estavam errados (DL n.º 126-A/2017
é a lei base da PSI, nunca fixa valores do CSI de 2026). Corrigido após
verificação do Nuno contra fontes oficiais (Portaria n.º 480-D/2025/1,
Decreto-Lei n.º 232/2005, Decreto-Lei n.º 35/2024, Portaria n.º
358/2024/1): os valores em € mantêm-se (8.040€/14.070€ já estavam
correctos), mas a idade mínima passa a MESES TOTAIS (801 = 66 anos e 9
meses, nunca só 66 anos completos — a versão anterior dava
falso-elegível a alguém com, por exemplo, 66 anos e 3 meses) e o
parâmetro `percentagem_rendimento_trabalho` (80%) foi removido por
falta de citação legal primária confirmada — rendimentos de trabalho
passam a contar a 100%, a leitura conservadora.

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
SIMULADOR_HTML = (RAIZ / "simulador-csi.html").read_text(encoding="utf-8")
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-csi.html")


CALCULO_JS = _extrair_script_inline("function calcularCSI")


def _parametros_csi_de_producao() -> dict:
    """Lê dados/parametros.json (a "nova fonte") e monta o mesmo formato
    que PARAMETROS_CSI tinha em runtime — nunca valores hardcoded aqui."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    csi = todos["prestacoes"]["csi"]
    return {
        "valorReferenciaIndividual": csi["valor_referencia_individual_anual"],
        "valorReferenciaCasal": csi["valor_referencia_casal_anual"],
        "idadeMinimaMesesTotais": csi["idade_minima_meses_totais"],
    }


def _localizar_chromium():
    """Procura o binário do Chromium em todas as localizações plausíveis
    (variável de ambiente, convenção do sandbox, convenção do CI) — ver
    test_simulador_psu_calculo.py para o achado real que motivou isto."""
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
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _calcular(pagina, entrada):
    return pagina.evaluate(
        "([params, entrada]) => calcularCSI(params, entrada)",
        [_parametros_csi_de_producao(), entrada],
    )


# ── Elegibilidade por idade — em MESES TOTAIS, nunca só anos completos ─────
def test_idade_bem_abaixo_do_minimo_fica_inelegivel(pagina):
    r = _calcular(pagina, {"idadeAnos": 65, "idadeMeses": 0, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeElegivel"] is False


def test_idade_66_anos_8_meses_fica_inelegivel(pagina):
    # Fronteira exacta: 66*12+8 = 800 meses, 1 mês abaixo do mínimo (801).
    # Regressão directa do bug real: a versão anterior comparava só
    # `idade >= 66` (anos completos) e dava falso-elegível aqui.
    r = _calcular(pagina, {"idadeAnos": 66, "idadeMeses": 8, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeTotalMeses"] == 800
    assert r["idadeElegivel"] is False


def test_idade_66_anos_9_meses_e_elegivel(pagina):
    # Fronteira exacta: 66*12+9 = 801 meses, exactamente o mínimo.
    r = _calcular(pagina, {"idadeAnos": 66, "idadeMeses": 9, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeTotalMeses"] == 801
    assert r["idadeElegivel"] is True


def test_idade_bem_acima_do_minimo_e_elegivel(pagina):
    r = _calcular(pagina, {"idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeTotalMeses"] == 840
    assert r["idadeElegivel"] is True


def test_idade_meses_em_falta_conta_como_zero(pagina):
    # input.idadeMeses ausente (formulário nunca deveria permitir, mas a
    # função pura tem de ser robusta) — nunca deve promover alguém que
    # só tem os anos completos, sem os meses adicionais.
    r = _calcular(pagina, {"idadeAnos": 66, "situacao": "isolado", "pensoesRequerente": 0})
    assert r["idadeTotalMeses"] == 792
    assert r["idadeElegivel"] is False


# ── Sem rendimentos — CSI = valor de referência completo ────────────────────
def test_sem_rendimentos_isolado_recebe_o_valor_de_referencia_completo(pagina):
    r = _calcular(pagina, {"idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado"})
    assert r["valorReferencia"] == 8040
    assert r["rendimentoConsiderado"] == 0
    assert r["csiAnual"] == 8040
    assert r["csiMensal"] == 670.0
    assert r["temDireito"] is True


def test_sem_rendimentos_casal_recebe_o_valor_de_referencia_casal(pagina):
    r = _calcular(pagina, {"idadeAnos": 70, "idadeMeses": 0, "situacao": "casal"})
    assert r["valorReferencia"] == 14070
    assert r["csiAnual"] == 14070


# ── Exemplo real já publicado em complemento-solidario-idosos.html ─────────
def test_exemplo_pensao_5600_anuais_da_203_33_mes(pagina):
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado",
        "pensoesRequerente": 5600, "trabalhoRequerente": 0,
    })
    assert r["csiAnual"] == 2440
    assert round(r["csiMensal"], 2) == 203.33


# ── Rendimento de trabalho conta a 100% (correcção PASSO 0, 2026-07-19) ────
# O parâmetro percentagem_rendimento_trabalho (80%) foi removido de
# dados/parametros/csi.yaml — questão fechada no mesmo dia com fonte
# primária: Guia Prático 8002 do ISS, I.P. (v4.53, 21/05/2026), secção
# C1.1, lista os rendimentos considerados sem nenhuma regra de 80% —
# trabalho conta sempre a 100% ("bruto, antes dos descontos"). O
# artigo complemento-solidario-idosos.html, que ainda afirmava 80% na
# sua tabela de rendimentos, foi corrigido no mesmo commit — ver
# tests/test_valores_ancora.py::test_percentagem_rendimento_trabalho_nunca_reaparece_sem_confirmacao,
# que tranca "80%" fora de todas as páginas do CSI.
def test_rendimento_de_trabalho_conta_a_100_por_cento(pagina):
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado",
        "pensoesRequerente": 0, "trabalhoRequerente": 1000,
    })
    assert r["rendimentoConsiderado"] == 1000


def test_pensoes_contam_100_por_cento(pagina):
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado",
        "pensoesRequerente": 1000, "trabalhoRequerente": 0,
    })
    assert r["rendimentoConsiderado"] == 1000


# ── Casal — rendimentos do cônjuge somam-se ─────────────────────────────────
def test_casal_soma_rendimentos_dos_dois_membros(pagina):
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "casal",
        "pensoesRequerente": 6000, "pensoesConjuge": 5000,
    })
    assert r["rendimentoConsiderado"] == 11000
    assert r["csiAnual"] == 3070
    assert round(r["csiMensal"], 2) == 255.83


def test_casal_com_trabalho_dos_dois_a_100_por_cento(pagina):
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "casal",
        "trabalhoRequerente": 1000, "trabalhoConjuge": 1000,
    })
    assert r["rendimentoConsiderado"] == 2000


def test_rendimentos_do_conjuge_ignorados_se_isolado(pagina):
    # Regressão: se o formulário enviar pensoesConjuge por engano com
    # situacao=isolado, nunca deve entrar no cálculo.
    r = _calcular(pagina, {
        "idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado",
        "pensoesRequerente": 1000, "pensoesConjuge": 99999,
    })
    assert r["rendimentoConsiderado"] == 1000


# ── Sem direito quando o rendimento atinge/excede o valor de referência ─────
def test_rendimento_igual_ao_valor_de_referencia_fica_sem_direito(pagina):
    r = _calcular(pagina, {"idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado", "pensoesRequerente": 8040})
    assert r["csiAnual"] == 0
    assert r["temDireito"] is False


def test_rendimento_acima_do_valor_de_referencia_nunca_fica_negativo(pagina):
    r = _calcular(pagina, {"idadeAnos": 70, "idadeMeses": 0, "situacao": "isolado", "pensoesRequerente": 50000})
    assert r["csiAnual"] == 0
    assert r["csiMensal"] == 0
    assert r["temDireito"] is False


# ── Estado de produção nunca inventa valores ────────────────────────────────
def test_parametros_producao_tem_todos_os_valores_confirmados(pagina):
    params = _parametros_csi_de_producao()
    assert params["valorReferenciaIndividual"]["valor"] == 8040
    assert params["valorReferenciaCasal"]["valor"] == 14070
    assert params["idadeMinimaMesesTotais"]["valor"] == 801
    for chave in params:
        assert params[chave]["verificado_em"], f"{chave} sem verificado_em"
        assert params[chave]["referencia_legal"], f"{chave} sem referencia_legal"
        assert params[chave]["fonte_url"], f"{chave} sem fonte_url"


def test_percentagem_rendimento_trabalho_nao_existe_por_falta_de_confirmacao(pagina):
    """Tranca a remoção deliberada (PASSO 0, 2026-07-19): nunca deve
    reaparecer sem uma citação legal primária confirmada em
    dados/parametros/csi.yaml."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    assert "percentagem_rendimento_trabalho" not in todos["prestacoes"]["csi"]


# ── Runtime real: fetch de /dados/parametros.json (sucesso e falha) ────────
# Servido por um http.server real (nunca file://, mesmo padrão de
# test_acessibilidade.py) — só assim `fetch('/dados/parametros.json')`
# resolve como um pedido relativo real.
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


def test_runtime_fetch_com_sucesso_activa_o_botao_e_calcula(pagina_real):
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-csi.html")
    page.wait_for_function("document.getElementById('btnCalcularCSI').disabled === false", timeout=5000)
    assert page.evaluate("document.getElementById('avisoParametrosErro').style.display") != "block"

    page.fill("#idadeAnos", "70")
    page.fill("#idadeMeses", "0")
    page.select_option("#situacao", "isolado")
    page.fill("#pensoesRequerente", "5600")
    page.click("#btnCalcularCSI")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    assert "203" in texto  # 8040-5600=2440/ano -> 203,33/mês, mesmo exemplo do golden test


def test_runtime_fetch_com_idade_insuficiente_mostra_falta_de_direito(pagina_real):
    # Regressão de ponta-a-ponta do bug real corrigido nesta sessão:
    # 66 anos e 3 meses nunca pode aparecer como "com direito" na UI.
    page, servidor = pagina_real
    page.goto(f"{servidor}/simulador-csi.html")
    page.wait_for_function("document.getElementById('btnCalcularCSI').disabled === false", timeout=5000)

    page.fill("#idadeAnos", "66")
    page.fill("#idadeMeses", "3")
    page.select_option("#situacao", "isolado")
    page.click("#btnCalcularCSI")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    assert "Ainda sem direito por idade" in texto


def test_runtime_fetch_com_falha_bloqueia_o_botao_e_nunca_calcula(pagina_real):
    page, servidor = pagina_real
    page.route("**/dados/parametros.json", lambda route: route.abort())
    page.goto(f"{servidor}/simulador-csi.html")
    page.wait_for_function(
        "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000
    )
    assert page.evaluate("document.getElementById('btnCalcularCSI').disabled") is True
    assert page.evaluate("window.PARAMETROS_CSI === null || typeof window.PARAMETROS_CSI === 'undefined'") \
        or page.evaluate("PARAMETROS_CSI") is None

    # Mesmo tentando submeter directamente via JS (bypass do disabled do
    # browser), a guarda em calcularCSIFormulario() nunca deixa o
    # resultado aparecer sem parâmetros carregados.
    page.evaluate("document.getElementById('formCSI').requestSubmit ? "
                   "document.getElementById('btnCalcularCSI').removeAttribute('disabled') : null")
    page.fill("#idadeAnos", "70")
    page.click("#btnCalcularCSI")
    page.wait_for_timeout(300)
    assert "show" not in (page.get_attribute("#resultado", "class") or "")
