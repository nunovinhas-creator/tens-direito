"""
Testes da mecânica de cálculo do simulador de subsídio de doença
(simulador-subsidio-doenca.html), executados num browser real
(Chromium headless via Playwright) — extrai o JS inline directamente
do HTML real, nunca uma cópia à parte (mesma filosofia de
test_simulador_csi_calculo.py/test_simulador_psu_calculo.py).

Sessão "Parâmetros YAML + auditoria factual" (2026-07-19, Commit 1):
PARAMETROS_SUBSIDIO_DOENCA deixou de ser um objecto JS inline — passa a
ser carregado em runtime de /dados/parametros.json (gerado de
dados/parametros/subsidio-doenca.yaml), mesmo padrão do CSI. Os golden
tests da mecânica pura (`calcularSubsidioDoenca`) constroem `params`
directamente a partir de dados/parametros.json (a "nova fonte"), nunca
de um `PARAMETROS_SUBSIDIO_DOENCA` global da página — a função continua
pura, testável sem depender de fetch/rede. O comportamento de runtime
(fetch com sucesso/falha, nunca calcular com valores em falta) tem os
seus próprios testes mais abaixo, servidos por um http.server real
(nunca file://).

CORRECÇÃO REAL DA AUDITORIA (2026-07-19), contra a fonte primária — Guia
Prático 5001 do ISS, I.P., v4.55, de 14/07/2026 (PDF oficial lido pelo
Nuno): o piso diário mínimo estava calculado sobre o IAS (30% ×
537,13€ ÷ 30 = 5,37€) — o Guia Prático fixa-o sobre a Remuneração
Mínima Mensal Garantida (RMMG) 2026: 30% × 920€ ÷ 30 = 9,20€. O segundo
piso (300€/325€ mensais quando a RR mensal era superior a 500€, ⚠️B)
nunca teve confirmação de fonte primária e foi removido — o Guia
Prático descreve só um piso diário único, com uma excepção: se a RR
diária da pessoa for inferior a esse piso, recebe a sua própria RR
diária, nunca um valor superior ao que realmente ganha.

Todos os casos golden estão calculados à mão nos comentários — se um
resultado divergir 1 cêntimo, investigar arredondamento antes de mexer
no simulador OU no artigo (ver test_coerencia_artigo_simulador no fim).

RR diária para salário=1400: (1400×6)÷180 = 8400÷180 = 140/3 = 46,666666...7€/dia
  — nota: 140/3 × 0,55 × 9 (múltiplos de 9 dias) dá sempre um resultado
  exacto (77×9/3=231, 77×27/3=693, etc.), por isso os casos com 1400€
  batem certo ao cêntimo sem arredondamentos intermédios.

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
SIMULADOR_HTML = (RAIZ / "simulador-subsidio-doenca.html").read_text(encoding="utf-8")
ARTIGO_HTML = (RAIZ / "baixa-medica-subsidio-doenca.html").read_text(encoding="utf-8")
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"


def _extrair_script_inline(texto: str, marcador: str, nome_ficheiro: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", texto):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em {nome_ficheiro}")


CALCULO_JS = _extrair_script_inline(SIMULADOR_HTML, "function calcularSubsidioDoenca", "simulador-subsidio-doenca.html")


def _parametros_subsidio_doenca_de_producao() -> dict:
    """Lê dados/parametros.json (a "nova fonte") e monta o mesmo formato
    que PARAMETROS_SUBSIDIO_DOENCA tinha em runtime — nunca valores
    hardcoded aqui."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    sd = todos["prestacoes"]["subsidio-doenca"]
    return {
        "taxaEscalao1": sd["taxa_escalao_ate_30_dias"],
        "taxaEscalao2": sd["taxa_escalao_31_a_90_dias"],
        "taxaEscalao3": sd["taxa_escalao_91_a_365_dias"],
        "taxaEscalao4": sd["taxa_escalao_mais_365_dias"],
        "taxaTuberculoseAte2Familiares": sd["taxa_tuberculose_ate_2_familiares"],
        "taxaTuberculoseMais2Familiares": sd["taxa_tuberculose_mais_2_familiares"],
        "diasEsperaContaOutrem": sd["dias_espera_conta_outrem"],
        "diasEsperaIndependente": sd["dias_espera_independente"],
        "diasEsperaSeguroSocialVoluntario": sd["dias_espera_seguro_social_voluntario"],
        "tetoDuracaoContaOutrem": sd["teto_duracao_conta_outrem_dias"],
        "tetoDuracaoIndependenteSSV": sd["teto_duracao_independente_ssv_dias"],
        "majoracaoPontosPercentuais": sd["majoracao_pontos_percentuais"],
        "limiteRRParaMajoracao": sd["limite_rr_mensal_para_majoracao"],
        "pisoDiarioMinimo": sd["piso_diario_minimo"],
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
    entrada_completa = {
        "salario": 0, "duracaoDias": 0, "vinculo": "conta_outrem",
        "situacaoEspecial": "nenhuma", "familiaresACargo": 0, "majoracaoFamiliar": False,
    }
    entrada_completa.update(entrada)
    return pagina.evaluate(
        "([params, entrada]) => calcularSubsidioDoenca(params, entrada)",
        [_parametros_subsidio_doenca_de_producao(), entrada_completa],
    )


# ── Caso 1 — TEM de bater com o exemplo publicado no artigo ─────────────────
def test_caso1_1400_100_dias_conta_outrem_bate_com_o_artigo(pagina):
    # RR diária = 46,666667€. Dias 1-3: espera. Dias 4-30 (27d) a 55% =
    # 693,00. Dias 31-90 (60d) a 60% = 1.680,00. Dias 91-100 (10d) a 70%
    # = 326,67. Total = 2.699,67€ — exemplo publicado em
    # baixa-medica-subsidio-doenca.html. RR diária (46,67€) está bem
    # acima do piso (9,20€) em todos os escalões — o piso nunca morde
    # neste caso, com ou sem a correcção desta sessão.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 100, "vinculo": "conta_outrem"})
    assert round(r["totalGeral"], 2) == 2699.67
    assert r["diasEspera"] == 3
    assert r["diasPagos"] == 97
    assert len(r["desagregacao"]) == 3
    assert round(r["desagregacao"][0]["subtotal"], 2) == 693.00
    assert round(r["desagregacao"][1]["subtotal"], 2) == 1680.00
    assert round(r["desagregacao"][2]["subtotal"], 2) == 326.67


def test_caso1_bate_com_o_valor_literal_do_artigo_publicado(pagina):
    # Rede de segurança extra: o texto "2.699,67" tem de existir no
    # artigo real — se um dia o artigo for editado sem o simulador (ou
    # vice-versa), este teste falha antes de qualquer divergência ao
    # cêntimo passar despercebida.
    assert "2.699,67" in ARTIGO_HTML


# ── Caso 2 — só escalão 55%, baixa curta ────────────────────────────────────
def test_caso2_1400_12_dias_so_escalao_55(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 12, "vinculo": "conta_outrem"})
    assert r["diasPagos"] == 9
    assert len(r["desagregacao"]) == 1
    assert r["desagregacao"][0]["taxaPct"] == 0.55
    assert round(r["totalGeral"], 2) == 231.00


# ── Caso 3 — fronteira 90/91 ─────────────────────────────────────────────────
def test_caso3_1400_91_dias_fronteira_90_91(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 91, "vinculo": "conta_outrem"})
    assert len(r["desagregacao"]) == 3
    assert r["desagregacao"][2]["dias"] == 1
    assert r["desagregacao"][2]["taxaPct"] == 0.70
    assert round(r["totalGeral"], 2) == 2405.67


# ── Caso 4 — majoração automática por RR ≤ 500€, piso 9,20€ a morder ───────
def test_caso4_450_30_dias_majoracao_automatica_piso_920_morde(pagina):
    # RR mensal = 450€ ≤ 500€ → majoração automática (55% -> 60%).
    # RR diária = 15,00€; 60% × 15,00 = 9,00€/dia — ABAIXO do novo piso
    # de 9,20€ (RMMG), mas a RR diária (15,00€) é maior que o piso, por
    # isso o piso eleva o valor pago para 9,20€ (não para a RR diária).
    # Dias 4-30 (27 dias) × 9,20€ = 248,40€.
    r = _calcular(pagina, {"salario": 450, "duracaoDias": 30, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is True
    assert r["diasPagos"] == 27
    assert round(r["desagregacao"][0]["valorDia"], 2) == 9.20
    assert round(r["totalGeral"], 2) == 248.40


# ── Caso 5 — piso 9,20€ morde sem majoração (RR > 500€) ─────────────────────
def test_caso5_501_10_dias_piso_920_morde_sem_majoracao(pagina):
    # RR mensal = 501€ > 500€ (sem majoração automática). RR diária =
    # 16,70€. Escalão 55%: 16,70×0,55 = 9,185€ < piso 9,20€ → usa
    # 9,20€ (a RR diária, 16,70€, é maior que o piso — recebe o piso,
    # não a RR). Dias 4-10 (7 dias) × 9,20€ = 64,40€.
    r = _calcular(pagina, {"salario": 501, "duracaoDias": 10, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is False
    assert round(r["desagregacao"][0]["valorDia"], 4) == 9.20
    assert round(r["totalGeral"], 2) == 64.40


# ── Caso novo — RR diária abaixo do piso: paga-se a RR, nunca o piso ────────
def test_rr_diaria_abaixo_do_piso_paga_a_propria_rr_nunca_o_piso(pagina):
    # Caso central da correcção desta sessão: salário=90€ → RR diária =
    # 3,00€ (bem abaixo do piso de 9,20€). RR mensal=90€≤500€ →
    # majoração automática (taxa=0,60). 0,60×3,00=1,80€ — mas a RR
    # diária (3,00€) já é inferior ao piso, por isso NUNCA se aplica o
    # piso (que pagaria mais do que a pessoa realmente ganha): o valor
    # pago é exactamente a RR diária, 3,00€ — nem 1,80€ (taxa×RR sem
    # piso), nem 9,20€ (o piso, que seria um erro). Dias 4-10 (7 dias)
    # × 3,00€ = 21,00€.
    r = _calcular(pagina, {"salario": 90, "duracaoDias": 10, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is True
    assert round(r["desagregacao"][0]["valorDia"], 2) == 3.00
    assert round(r["totalGeral"], 2) == 21.00


# ── Caso 6 — independente: 10 dias de espera ────────────────────────────────
def test_caso6_1400_30_dias_independente_10_dias_espera(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 30, "vinculo": "independente"})
    assert r["diasEspera"] == 10
    assert r["diasPagos"] == 20
    assert round(r["totalGeral"], 2) == 513.33


# ── Caso 7 — internamento: zero dias de espera ──────────────────────────────
def test_caso7_1400_20_dias_internamento_zero_espera(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 20, "situacaoEspecial": "internamento_cirurgia"})
    assert r["diasEspera"] == 0
    assert r["diasPagos"] == 20
    assert round(r["totalGeral"], 2) == 513.33


# ── Caso 8 — tuberculose: 100%, sem teto de duração ─────────────────────────
def test_caso8_tuberculose_3_familiares_100_por_cento_sem_teto(pagina):
    # 1200 dias excederia o teto de 1095 (conta de outrem) — usado aqui
    # deliberadamente para provar que a tuberculose NÃO tem esse limite.
    r = _calcular(pagina, {
        "salario": 1400, "duracaoDias": 1200, "vinculo": "conta_outrem",
        "situacaoEspecial": "tuberculose", "familiaresACargo": 3,
    })
    assert r["diasEspera"] == 0
    assert r["duracaoExcedeTeto"] is False
    assert r["duracaoEfetiva"] == 1200
    assert r["desagregacao"][0]["taxaPct"] == 1.00
    assert round(r["totalGeral"], 2) == 56000.00


def test_tuberculose_ate_2_familiares_e_80_por_cento(pagina):
    r = _calcular(pagina, {
        "salario": 1400, "duracaoDias": 10,
        "situacaoEspecial": "tuberculose", "familiaresACargo": 2,
    })
    assert r["desagregacao"][0]["taxaPct"] == 0.80


# ── Caso 9 — mistura de escalões 70%/75% ────────────────────────────────────
def test_caso9_1400_400_dias_mistura_70_75(pagina):
    # Tiers: 27d@55%=693,00; 60d@60%=1680,00; 275d@70%=8.983,33;
    # 35d@75%=1.225,00. Total = 12.581,33€.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 400, "vinculo": "conta_outrem"})
    assert len(r["desagregacao"]) == 4
    assert r["desagregacao"][2]["dias"] == 275
    assert r["desagregacao"][2]["taxaPct"] == 0.70
    assert r["desagregacao"][3]["dias"] == 35
    assert r["desagregacao"][3]["taxaPct"] == 0.75
    assert round(r["totalGeral"], 2) == 12581.33


# ── Caso 10 — teto de 1095 dias com aviso ───────────────────────────────────
def test_caso10_1200_dias_conta_outrem_cap_1095_com_aviso(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 1200, "vinculo": "conta_outrem"})
    assert r["duracaoExcedeTeto"] is True
    assert r["duracaoEfetiva"] == 1095
    assert r["tetoDuracao"] == 1095
    assert round(r["totalGeral"], 2) == 36906.33


# ── Duração excede teto para independente/SSV também ────────────────────────
def test_independente_teto_365_dias(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 400, "vinculo": "independente"})
    assert r["duracaoExcedeTeto"] is True
    assert r["duracaoEfetiva"] == 365
    assert r["tetoDuracao"] == 365


# ── Nunca fica negativo / duração zero ──────────────────────────────────────
def test_duracao_menor_que_dias_de_espera_nao_paga_nada(pagina):
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 2, "vinculo": "conta_outrem"})
    assert r["diasPagos"] == 0
    assert r["totalGeral"] == 0
    assert r["desagregacao"] == []


# ── Caso de fronteira explícito da spec: baixa de exactamente 3 dias ────────
def test_baixa_de_exactamente_3_dias_iguala_periodo_de_espera_nao_paga_nada(pagina):
    # Para conta de outrem, diasEspera=3 — uma baixa de exactamente 3 dias
    # esgota-se inteira no período de espera: zero dias pagos.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 3, "vinculo": "conta_outrem"})
    assert r["diasEspera"] == 3
    assert r["diasPagos"] == 0
    assert r["totalGeral"] == 0
    assert r["desagregacao"] == []


def test_baixa_de_4_dias_paga_exactamente_1_dia_apos_o_periodo_de_espera(pagina):
    # O dia seguinte (4.º dia) já é pago — confirma a fronteira exacta
    # entre "período de espera" e "primeiro dia pago", nos dois lados.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 4, "vinculo": "conta_outrem"})
    assert r["diasPagos"] == 1
    assert round(r["totalGeral"], 2) == 25.67


# ── Fase 2 (auditoria 2026-07-06) — fronteiras de escalão em falta ──────────

def test_fronteira_30_31_escalao_55_para_60(pagina):
    # Dias 4-30 (27d) a 55% = 693,00€ (igual ao caso1). Dia 31 (1d) já cai
    # no escalão de 60%: 46,6667×0,60 = 28,00€. Total = 721,00€.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 31, "vinculo": "conta_outrem"})
    assert len(r["desagregacao"]) == 2
    assert r["desagregacao"][0]["dias"] == 27
    assert r["desagregacao"][0]["taxaPct"] == 0.55
    assert r["desagregacao"][1]["dias"] == 1
    assert r["desagregacao"][1]["taxaPct"] == 0.60
    assert round(r["desagregacao"][1]["subtotal"], 2) == 28.00
    assert round(r["totalGeral"], 2) == 721.00


def test_fronteira_365_366_escalao_70_para_75(pagina):
    # 27d@55%=693,00; 60d@60%=1.680,00; 275d@70%=8.983,33 (dias 91-365);
    # 1d@75%=35,00 (dia 366). Total = 11.391,33€.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 366, "vinculo": "conta_outrem"})
    assert len(r["desagregacao"]) == 4
    assert r["desagregacao"][2]["dias"] == 275
    assert r["desagregacao"][2]["taxaPct"] == 0.70
    assert r["desagregacao"][3]["dias"] == 1
    assert r["desagregacao"][3]["taxaPct"] == 0.75
    assert round(r["desagregacao"][3]["subtotal"], 2) == 35.00
    assert round(r["totalGeral"], 2) == 11391.33


def test_teto_exactamente_no_limite_nao_dispara_aviso(pagina):
    # 1095 dias exactos (não 1096) — duracaoExcedeTeto usa ">" estrito,
    # nunca ">=", por isso o limite exacto não deve disparar o aviso.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 1095, "vinculo": "conta_outrem"})
    assert r["duracaoExcedeTeto"] is False
    assert r["duracaoEfetiva"] == 1095
    assert r["tetoDuracao"] == 1095


# ── Majoração via checkbox (nunca só automática por RR≤500€) ────────────────

def test_majoracao_via_checkbox_com_rr_acima_de_500(pagina):
    # RR mensal=3.000€ (>500€, sem majoração automática), mas
    # majoracaoFamiliar=True activa-a na mesma. RR diária=100,00€;
    # taxa=0,55+0,05=0,60; valorDia=60,00€ (bem acima do piso de 9,20€).
    # Dias 4-10 (7d) × 60,00 = 420,00€.
    r = _calcular(pagina, {
        "salario": 3000, "duracaoDias": 10, "vinculo": "conta_outrem",
        "majoracaoFamiliar": True,
    })
    assert r["majoracaoAplicavel"] is True
    assert round(r["desagregacao"][0]["valorDia"], 2) == 60.00
    assert round(r["totalGeral"], 2) == 420.00


def test_sem_majoracao_e_sem_checkbox_rr_acima_de_500_nao_majora(pagina):
    # Mesmo salário/duração do teste anterior, mas sem o checkbox —
    # confirma que a majoração nunca é automática acima de 500€ sem a
    # condição familiar assinalada. Taxa fica em 0,55 (não 0,60).
    r = _calcular(pagina, {"salario": 3000, "duracaoDias": 10, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is False
    assert r["desagregacao"][0]["taxaPct"] == 0.55


# ── Seguro social voluntário — 30 dias de espera consomem todo o 1.º escalão ─

def test_seguro_social_voluntario_30_dias_espera(pagina):
    # 30 dias de espera esgotam por completo o escalão de 1-30 dias — zero
    # dias pagos a 55%. Só o dia 31-35 (5d) é pago, já a 60%: 46,6667×0,60=
    # 28,00€/dia × 5 = 140,00€.
    r = _calcular(pagina, {"salario": 1400, "duracaoDias": 35, "vinculo": "seguro_social_voluntario"})
    assert r["diasEspera"] == 30
    assert r["diasPagos"] == 5
    assert len(r["desagregacao"]) == 1
    assert r["desagregacao"][0]["taxaPct"] == 0.60
    assert round(r["totalGeral"], 2) == 140.00


# ── Estado de produção nunca inventa valores ────────────────────────────────

def test_parametros_producao_tem_todos_os_valores_confirmados(pagina):
    params = _parametros_subsidio_doenca_de_producao()
    assert params["taxaEscalao1"]["valor"] == 0.55
    assert params["taxaEscalao4"]["valor"] == 0.75
    assert params["pisoDiarioMinimo"]["valor"] == 9.20
    for chave in params:
        assert params[chave]["verificado_em"], f"{chave} sem verificado_em"
        assert params[chave]["referencia_legal"], f"{chave} sem referencia_legal"
        assert params[chave]["fonte_url"], f"{chave} sem fonte_url"


def test_piso_300_325_nao_existe_por_falta_de_confirmacao(pagina):
    """Tranca a remoção deliberada (2026-07-19): o piso de 300€/325€
    mensais nunca teve confirmação de fonte primária — nunca deve
    reaparecer sem uma citação legal primária nova."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    sd = todos["prestacoes"]["subsidio-doenca"]
    assert "piso_diario_proporcional_taxa_55" not in sd
    assert "piso_diario_proporcional_taxa_60" not in sd


# ── Coerência artigo ↔ simulador ─────────────────────────────────────────────

def test_gravidez_de_risco_fora_do_ambito_coerente_com_o_artigo():
    """A auditoria de 2026-07-06 encontrou o simulador silencioso sobre
    gravidez de risco (o artigo já a trata como prestação distinta desde
    a publicação) — corrigido com uma FAQ nova. Confirma que os 3 factos-
    -chave (100%, 1.º dia, data provável do parto) batem certo nos dois
    sítios, nunca só num deles."""
    assert "gravidez de risco" in SIMULADOR_HTML.lower()
    for facto in ["100%", "1.º dia", "data provável do parto"]:
        assert facto in SIMULADOR_HTML, f"'{facto}' não encontrado no simulador"
        assert facto in ARTIGO_HTML, f"'{facto}' não encontrado no artigo"


def test_coerencia_artigo_simulador_constantes_de_producao():
    """Se um dia o artigo for actualizado sem o simulador (ou
    vice-versa), este teste é a rede — lê os parâmetros reais de
    dados/parametros.json e confirma que batem certo com os factos
    publicados em baixa-medica-subsidio-doenca.html."""
    params = _parametros_subsidio_doenca_de_producao()

    assert params["taxaEscalao1"]["valor"] == 0.55
    assert params["taxaEscalao2"]["valor"] == 0.60
    assert params["taxaEscalao3"]["valor"] == 0.70
    assert params["taxaEscalao4"]["valor"] == 0.75
    assert params["taxaTuberculoseAte2Familiares"]["valor"] == 0.80
    assert params["taxaTuberculoseMais2Familiares"]["valor"] == 1.00
    assert params["diasEsperaContaOutrem"]["valor"] == 3
    assert params["diasEsperaIndependente"]["valor"] == 10
    assert params["diasEsperaSeguroSocialVoluntario"]["valor"] == 30
    assert params["tetoDuracaoContaOutrem"]["valor"] == 1095
    assert params["tetoDuracaoIndependenteSSV"]["valor"] == 365
    assert params["majoracaoPontosPercentuais"]["valor"] == 0.05
    assert params["limiteRRParaMajoracao"]["valor"] == 500
    assert params["pisoDiarioMinimo"]["valor"] == 9.20

    # As mesmas constantes têm de aparecer no corpo do artigo publicado
    # — nunca só no simulador. "5,37"/"300"/"325" nunca devem reaparecer
    # (ver test_valores_ancora.py::test_piso_300_325_nunca_reaparece_sem_confirmacao).
    for valor_esperado in ["55%", "60%", "70%", "75%", "80%", "100%", "9,20", "1095", "365"]:
        assert valor_esperado in ARTIGO_HTML, f"'{valor_esperado}' não encontrado no artigo publicado"

    for chave in params:
        assert params[chave]["verificado_em"] is not None, f"{chave} sem verificado_em"
        assert params[chave]["referencia_legal"], f"{chave} sem referencia_legal"


# ── Runtime real: fetch de /dados/parametros.json (sucesso e falha) ────────
# Servido por um http.server real (nunca file://, mesmo padrão de
# test_simulador_csi_calculo.py) — só assim
# `fetch('/dados/parametros.json')` resolve como um pedido relativo real.
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
    page.goto(f"{servidor}/simulador-subsidio-doenca.html")
    page.wait_for_function(
        "document.getElementById('btnCalcularSubsidioDoenca').disabled === false", timeout=5000
    )
    assert page.evaluate("document.getElementById('avisoParametrosErro').style.display") != "block"

    page.fill("#salario", "1400")
    page.fill("#duracaoDias", "100")
    page.select_option("#vinculo", "conta_outrem")
    page.click("#btnCalcularSubsidioDoenca")
    page.wait_for_selector("#resultado.show", timeout=5000)
    texto = page.inner_text("#resultado")
    assert "2.699,67" in texto or "2699.67" in texto  # mesmo exemplo do golden test


def test_runtime_fetch_com_falha_bloqueia_o_botao_e_nunca_calcula(pagina_real):
    page, servidor = pagina_real
    page.route("**/dados/parametros.json", lambda route: route.abort())
    page.goto(f"{servidor}/simulador-subsidio-doenca.html")
    page.wait_for_function(
        "document.getElementById('avisoParametrosErro').style.display === 'block'", timeout=5000
    )
    assert page.evaluate("document.getElementById('btnCalcularSubsidioDoenca').disabled") is True
    assert page.evaluate("document.getElementById('avisoCarregandoParametros').style.display") == "none"
    assert page.evaluate(
        "window.PARAMETROS_SUBSIDIO_DOENCA === null || typeof window.PARAMETROS_SUBSIDIO_DOENCA === 'undefined'"
    ) or page.evaluate("PARAMETROS_SUBSIDIO_DOENCA") is None

    # Mesmo tentando submeter directamente via JS (bypass do disabled do
    # browser), a guarda em calcularSubsidioDoencaFormulario() nunca deixa
    # o resultado aparecer sem parâmetros carregados.
    page.evaluate("document.getElementById('btnCalcularSubsidioDoenca').removeAttribute('disabled')")
    page.fill("#salario", "1400")
    page.fill("#duracaoDias", "10")
    page.click("#btnCalcularSubsidioDoenca")
    page.wait_for_timeout(300)
    assert "show" not in (page.get_attribute("#resultado", "class") or "")
