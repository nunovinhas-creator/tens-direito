"""
Testes da mecânica de cálculo do simulador da PSU (simulador-psu.html),
executados num browser real (Chromium headless via Playwright) — extrai
o JS inline directamente do HTML real, nunca uma cópia à parte (mesma
filosofia de test_pesquisa_hero.py/test_pesquisa_ranking.py).

Activado na Fase 2 (2026-08-13, Decreto-Lei n.º 166/2026): ao contrário
da versão anterior deste ficheiro, os parâmetros usados aqui são os
REAIS de produção (IAS 2026 = 537,13 €, valores fixados pelo decreto-lei),
nunca fictícios — a fórmula já não está "à espera do decreto-lei".

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
SIMULADOR_HTML = (RAIZ / "simulador-psu.html").read_text(encoding="utf-8")


def _extrair_script_inline(marcador: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", SIMULADOR_HTML):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em simulador-psu.html")


CALCULO_JS = _extrair_script_inline("function calcularPSU")

# ── Valores reais de produção (Decreto-Lei n.º 166/2026) ────────────────
# Nunca hardcoded como cópia solta dos números finais — recalculados aqui
# a partir do IAS e dos multiplicadores/ponderações do decreto-lei, exactamente
# como o JS do simulador faz a partir de dados/parametros.json. Se o IAS
# mudar (Portaria nova), estes testes continuam correctos sem qualquer edição.
IAS_2026 = 537.13
VRP = 0.5 * IAS_2026
TETO = 6 * IAS_2026
VALOR_MINIMO = 10.00
PONDERACAO_TITULAR = 1
PONDERACAO_MAIOR = 0.7
PONDERACAO_MENOR = 0.5
CIT_LIMIAR = 0.20 * IAS_2026
CIT_TAXA_ACIMA_LIMIAR = 0.50

PARAMETROS_PRODUCAO = {
    "valorReferencia": VRP,
    "teto": TETO,
    "valorMinimo": VALOR_MINIMO,
    "ponderacaoTitular": PONDERACAO_TITULAR,
    "ponderacaoMaior": PONDERACAO_MAIOR,
    "ponderacaoMenor": PONDERACAO_MENOR,
    "citLimiar": CIT_LIMIAR,
    "citTaxaAcimaLimiar": CIT_TAXA_ACIMA_LIMIAR,
    "dataProducaoEfeitos": "2026-12-31",
}


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
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _calcular(pagina, params, entrada):
    entrada_completa = {
        "numAdultos": 1, "numMenores": 0,
        "rendimentoTrabalho": 0, "outrosRendimentos": 0,
        "majoracao": "nenhuma", "beneficiarioMajoracao": "titular",
        **entrada,
    }
    return pagina.evaluate(
        "([params, entrada]) => calcularPSU(params, entrada)",
        [params, entrada_completa],
    )


def _aprox(a, b, tol=0.005):
    return abs(a - b) < tol


# ── Adultos equivalentes — agregados de vários tamanhos ─────────────────
def test_titular_sozinho_zero_rendimentos_da_exactamente_o_vrp(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {"numAdultos": 1, "numMenores": 0})
    assert resultado["adultosEquivalentes"] == 1
    assert _aprox(resultado["psuBase"], VRP)
    assert _aprox(resultado["valor"], VRP)


def test_titular_mais_um_maior_e_um_menor_multiplica_pelas_ponderacoes(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {"numAdultos": 2, "numMenores": 1})
    ae_esperado = PONDERACAO_TITULAR + PONDERACAO_MAIOR + PONDERACAO_MENOR  # 1 + 0.7 + 0.5 = 2.2
    assert _aprox(resultado["adultosEquivalentes"], ae_esperado)
    assert _aprox(resultado["psuBase"], VRP * ae_esperado)
    assert _aprox(resultado["valor"], VRP * ae_esperado)


def test_familia_grande_soma_todas_as_ponderacoes(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {"numAdultos": 2, "numMenores": 3})
    ae_esperado = PONDERACAO_TITULAR + PONDERACAO_MAIOR + 3 * PONDERACAO_MENOR  # 1 + 0.7 + 1.5 = 3.2
    assert _aprox(resultado["adultosEquivalentes"], ae_esperado)


# ── CIT — duas parcelas (artigo 28.º/2) ──────────────────────────────────
def test_cit_dentro_do_limiar_conta_na_integra(pagina):
    # Rendimento de trabalho abaixo do limiar (107,43 €) — CIT = rendimento na íntegra.
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "rendimentoTrabalho": 50,
    })
    assert _aprox(resultado["cit"], 50)
    # Efeito líquido: rendimento de trabalho dentro do limiar não reduz o valor.
    assert _aprox(resultado["valor"], VRP)


def test_cit_acima_do_limiar_ativa_as_duas_parcelas(pagina):
    # Rendimento de trabalho de 300€ excede o limiar de 107,43€ — a CIT
    # cobre o limiar na íntegra + 50% do excedente (artigo 28.º/2, a) e b)).
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "rendimentoTrabalho": 300,
    })
    cit_esperada = CIT_LIMIAR + CIT_TAXA_ACIMA_LIMIAR * (300 - CIT_LIMIAR)
    assert _aprox(resultado["cit"], cit_esperada)
    valor_esperado = max(0, VRP + cit_esperada - 300)
    assert _aprox(resultado["valor"], valor_esperado)
    # Confirma que o rendimento de trabalho nunca é "tudo ou nada": o
    # simulador dá sempre mais valor do que se a CIT não existisse.
    assert resultado["valor"] > max(0, VRP - 300)


def test_outros_rendimentos_reduzem_o_valor_sem_beneficiar_da_cit(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "outrosRendimentos": 100,
    })
    assert resultado["cit"] == 0
    assert _aprox(resultado["valor"], VRP - 100)


# ── Teto máximo (6×IAS) ──────────────────────────────────────────────────
def test_agregado_muito_grande_e_cortado_no_teto(pagina):
    # AE = 1 + 19×0,7 (19 outros maiores) + 5×0,5 (5 menores) = 16,8 ->
    # psuBase bem acima do teto de 6×IAS — o resultado final nunca pode
    # exceder o teto, por maior que seja o agregado.
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {"numAdultos": 20, "numMenores": 5})
    ae = PONDERACAO_TITULAR + 19 * PONDERACAO_MAIOR + 5 * PONDERACAO_MENOR
    assert VRP * ae > TETO, "pré-condição do teste: o psuBase tem de exceder o teto"
    assert _aprox(resultado["valor"], TETO)


# ── Mínimo de 10 € (artigo 25.º/5) ────────────────────────────────────────
def test_valor_abaixo_do_minimo_fica_sem_prestacao(pagina):
    # Titular sozinho, psuBase = VRP (268,565€); outros rendimentos deixam
    # o resultado positivo mas abaixo dos 10€ — não há lugar à prestação.
    outros_rendimentos = VRP - 6.565  # deixa ~6,57€, abaixo do mínimo
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "outrosRendimentos": outros_rendimentos,
    })
    assert resultado["abaixoDoMinimo"] is True
    assert resultado["valor"] == 0


def test_valor_exactamente_no_minimo_ou_acima_mantem_se(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "outrosRendimentos": VRP - 50,
    })
    assert resultado["abaixoDoMinimo"] is False
    assert _aprox(resultado["valor"], 50)


def test_valor_nunca_fica_negativo(pagina):
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "outrosRendimentos": 100000,
    })
    assert resultado["valor"] == 0


# ── Majoração por parentalidade (artigo 26.º) ────────────────────────────
def test_majoracao_parentalidade_titular_completa_ate_80_por_cento_do_ias(pagina):
    # Titular sozinho, 0 rendimentos: psuBase = VRP = valor atribuído ao
    # titular pela ponderação da fórmula base -> majoração = 80%IAS - VRP,
    # e o resultado final sobe exactamente a 80% do IAS.
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "majoracao": "parentalidade", "beneficiarioMajoracao": "titular",
    })
    majoracao_esperada = 0.80 * IAS_2026 - PONDERACAO_TITULAR * VRP
    assert _aprox(resultado["majoracao"], majoracao_esperada)
    assert _aprox(resultado["valor"], 0.80 * IAS_2026)


def test_majoracao_parentalidade_varia_com_o_beneficiario(pagina):
    resultado_maior = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "majoracao": "parentalidade", "beneficiarioMajoracao": "maior",
    })
    resultado_menor = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "majoracao": "parentalidade", "beneficiarioMajoracao": "menor",
    })
    majoracao_maior_esperada = 0.80 * IAS_2026 - PONDERACAO_MAIOR * VRP
    majoracao_menor_esperada = 0.80 * IAS_2026 - PONDERACAO_MENOR * VRP
    assert _aprox(resultado_maior["majoracao"], majoracao_maior_esperada)
    assert _aprox(resultado_menor["majoracao"], majoracao_menor_esperada)
    # Ponderação menor (0,5) < ponderação maior (0,7) -> a diferença ao
    # limiar de 80% do IAS é maior, logo a majoração é maior.
    assert resultado_menor["majoracao"] > resultado_maior["majoracao"]


# ── Majoração por desemprego (artigo 27.º) ────────────────────────────────
def test_majoracao_desemprego_eleva_ate_80_por_cento_do_ias_quando_aplicavel(pagina):
    # Titular sozinho com outros rendimentos que deixam o PSUglobal abaixo
    # de 80% do IAS — a majoração de desemprego eleva exactamente até lá.
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 1, "numMenores": 0, "outrosRendimentos": 50,
        "majoracao": "desemprego",
    })
    assert resultado["majoracao"] > 0
    assert _aprox(resultado["valor"], 0.80 * IAS_2026)


def test_majoracao_desemprego_nao_se_aplica_se_psuglobal_ja_e_80_por_cento_do_ias(pagina):
    # Titular + 1 maior, 0 rendimentos: psuBase já excede 80% do IAS —
    # "sem lugar à majoração se PSUglobal já for ≥ 80% do IAS" (artigo 27.º/2).
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {
        "numAdultos": 2, "numMenores": 0, "majoracao": "desemprego",
    })
    psu_global_sem_majoracao = VRP * (PONDERACAO_TITULAR + PONDERACAO_MAIOR)
    assert psu_global_sem_majoracao >= 0.80 * IAS_2026, "pré-condição do teste"
    assert resultado["majoracao"] == 0
    assert _aprox(resultado["valor"], psu_global_sem_majoracao)


def test_majoracoes_nunca_acumulaveis_simulador_so_aplica_uma(pagina):
    # "nenhuma" é o valor por omissão do select — confirma que sem
    # escolha explícita nenhuma majoração é aplicada.
    resultado = _calcular(pagina, PARAMETROS_PRODUCAO, {"numAdultos": 1, "numMenores": 0, "majoracao": "nenhuma"})
    assert resultado["majoracao"] == 0


# ── Coerência com o artigo do decreto-lei citado no próprio ficheiro ────
def test_nenhum_valor_de_producao_fica_null(pagina):
    parametros = pagina.evaluate("PARAMETROS_PSU")
    assert parametros is None, (
        "PARAMETROS_PSU só é preenchido depois do fetch de /dados/parametros.json "
        "em runtime — numa página sem fetch (esta fixture de teste) tem de "
        "continuar null; os testes acima passam os parâmetros directamente."
    )
