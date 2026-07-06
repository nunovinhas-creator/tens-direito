"""
Testes da mecânica de cálculo do simulador de subsídio de doença
(simulador-subsidio-doenca.html), executados num browser real
(Chromium headless via Playwright) — extrai o JS inline directamente
do HTML real, nunca uma cópia à parte (mesma filosofia de
test_simulador_csi_calculo.py/test_simulador_psu_calculo.py).

Os valores de PARAMETROS_SUBSIDIO_DOENCA usados aqui SÃO os valores de
produção (55%/60%/70%/75%, IAS 5,37€/dia, dias de espera 3/10/30,
tetos 1095/365) — já fact-checked e publicados em
baixa-medica-subsidio-doenca.html (verificado 05/07/2026).

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
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-subsidio-doenca.html").read_text(encoding="utf-8")
ARTIGO_HTML = (RAIZ / "baixa-medica-subsidio-doenca.html").read_text(encoding="utf-8")


def _extrair_script_inline(texto: str, marcador: str, nome_ficheiro: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", texto):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em {nome_ficheiro}")


CALCULO_JS = _extrair_script_inline(SIMULADOR_HTML, "function calcularSubsidioDoenca", "simulador-subsidio-doenca.html")


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
        [pagina.evaluate("PARAMETROS_SUBSIDIO_DOENCA"), entrada_completa],
    )


# ── Caso 1 — TEM de bater com o exemplo publicado no artigo ─────────────────
def test_caso1_1400_100_dias_conta_outrem_bate_com_o_artigo(pagina):
    # RR diária = 46,666667€. Dias 1-3: espera. Dias 4-30 (27d) a 55% =
    # 693,00. Dias 31-90 (60d) a 60% = 1.680,00. Dias 91-100 (10d) a 70%
    # = 326,67. Total = 2.699,67€ — exemplo publicado em
    # baixa-medica-subsidio-doenca.html.
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


# ── Caso 4 — majoração automática por RR ≤ 500€ + piso 5,37€ exercitado ─────
def test_caso4_450_30_dias_majoracao_automatica(pagina):
    # RR mensal = 450€ ≤ 500€ → majoração automática (55% -> 60%).
    # RR diária = 15,00€; 60% × 15,00 = 9,00€/dia — acima do piso
    # universal de 5,37€ (o piso não morde a este salário, mas o
    # caminho de código que o aplica é exercitado: max(9.00, 5.37)==9.00).
    r = _calcular(pagina, {"salario": 450, "duracaoDias": 30, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is True
    assert r["diasPagos"] == 27
    assert round(r["desagregacao"][0]["valorDia"], 2) == 9.00
    assert round(r["totalGeral"], 2) == 243.00


# ── Caso 5 — zona onde o piso 300€/325€ morde ───────────────────────────────
def test_caso5_510_60_dias_piso_300_325_morde(pagina):
    # RR mensal = 510€ > 500€ (sem majoração). RR diária = 17,00€.
    # Escalão 55%: 17,00×0,55=9,35€ < piso 300÷30=10,00€ -> usa 10,00€.
    # Escalão 60%: 17,00×0,60=10,20€ < piso 325÷30=10,8333€ -> usa 10,8333€.
    # Total = 27×10,00 + 30×10,8333 = 270,00 + 325,00 = 595,00€.
    r = _calcular(pagina, {"salario": 510, "duracaoDias": 60, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is False
    assert round(r["desagregacao"][0]["valorDia"], 4) == 10.00
    assert round(r["desagregacao"][1]["valorDia"], 4) == 10.8333
    assert round(r["totalGeral"], 2) == 595.00


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


# ── Piso universal (5,37€/dia) a morder de facto — RR muito baixa ──────────

def test_piso_universal_5_37_morde_com_rr_muito_baixa(pagina):
    # RR mensal=100€ (≤500€ → majoração automática 55%→60%). RR diária=
    # 3,3333€; 60%×3,3333=2,00€/dia < piso universal 5,37€ → usa 5,37€.
    # Dias 4-10 (7d, dentro do escalão de 30 dias) × 5,37 = 37,59€.
    r = _calcular(pagina, {"salario": 100, "duracaoDias": 10, "vinculo": "conta_outrem"})
    assert r["majoracaoAplicavel"] is True
    assert r["diasPagos"] == 7
    assert round(r["desagregacao"][0]["valorDia"], 2) == 5.37
    assert round(r["totalGeral"], 2) == 37.59


# ── Majoração via checkbox (nunca só automática por RR≤500€) ────────────────

def test_majoracao_via_checkbox_com_rr_acima_de_500(pagina):
    # RR mensal=3.000€ (>500€, sem majoração automática), mas
    # majoracaoFamiliar=True activa-a na mesma. RR diária=100,00€;
    # taxa=0,55+0,05=0,60; valorDia=60,00€ (piso 300/325 não morde).
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


def test_coerencia_artigo_simulador_constantes_de_producao(pagina):
    """Se um dia o artigo for actualizado sem o simulador (ou
    vice-versa), este teste é a rede — reimporta os PARAMETROS reais do
    simulador e confirma que batem certo com os factos publicados em
    baixa-medica-subsidio-doenca.html."""
    params = pagina.evaluate("PARAMETROS_SUBSIDIO_DOENCA")

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
    assert params["limiteRRParaMajoracaoOuPiso"]["valor"] == 500
    assert params["pisoDiarioUniversal"]["valor"] == 5.37

    # As mesmas constantes têm de aparecer no corpo do artigo publicado
    # — nunca só no simulador.
    for valor_esperado in ["55%", "60%", "70%", "75%", "80%", "100%", "5,37", "300", "325", "1095", "365"]:
        assert valor_esperado in ARTIGO_HTML, f"'{valor_esperado}' não encontrado no artigo publicado"

    for chave in params:
        assert params[chave]["verificado_em"] is not None, f"{chave} sem verificado_em"
        assert params[chave]["fonte"], f"{chave} sem fonte"
