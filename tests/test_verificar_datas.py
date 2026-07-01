"""
Testes para scripts/verificar_datas.py — deteção de conteúdo potencialmente
desactualizado, sem falsos positivos por referências históricas/legais.

Casos cobertos (auditoria de 2026-07-01 às Issues #33-#46):
- diploma 2025
- rendimentos 2025
- comparação 2025 vs 2026
- exemplo ilustrativo
- ano letivo inexistente numa página sem contexto escolar
- página escolar realmente desatualizada
- página escolar correta
- conteúdo "aguarda despacho" (dentro e fora do prazo anunciado)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verificar_datas import detectar_alertas

ANO = 2026
MES = 7  # julho — activa data_mes_ano, data_numerica e ano_letivo


def _html(corpo):
    return f"<html><body>{corpo}</body></html>"


# ── Falsos positivos identificados na auditoria ────────────────────────────────

def test_diploma_2025_nao_gera_alerta():
    html = _html(
        "Fonte: Decreto-Lei n.º 138/2025, de 29 de dezembro. "
        "Verificado a 29 de junho de 2026."
    )
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_rendimentos_ano_anterior_nao_gera_alerta():
    html = _html(
        "Para novos pedidos em 2026, usa-se o rendimento anual de 2025 "
        "para calcular o escalão. Verificado a 24 de junho de 2026."
    )
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_comparacao_historica_2025_vs_2026_nao_gera_alerta():
    html = _html(
        "Em 2025, o valor de referência individual era 8.010,00 €. "
        "Valor em 2026: 8.040,00 €. Verificado a 25/06/2026."
    )
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_exemplo_ilustrativo_nao_gera_alerta():
    html = _html(
        "Exemplo: licença a começar em agosto de 2026 — os 8 meses "
        "anteriores incluem dezembro de 2025 a julho de 2026. "
        "Verificado a 24 de junho de 2026."
    )
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_pagina_sem_contexto_escolar_ignora_regra_ano_letivo():
    # Página sem qualquer par de anos lectivos — a regra "ano_letivo" não
    # deve ser aplicada só por a página não mencionar o par actual.
    html = _html("Política de privacidade. Última actualização: 24 de junho de 2026.")
    assert detectar_alertas(html, "privacidade.html", ANO, MES) is None


def test_facto_permanente_desde_ano_antigo_nao_gera_alerta():
    html = _html(
        "Desde 2016/2017, os manuais escolares são gratuitos para todos os "
        "alunos do ensino público. Verificado a 24 de junho de 2026."
    )
    assert detectar_alertas(html, "manuais-escolares-mega.html", ANO, MES) is None


def test_ano_antigo_dentro_de_link_nao_gera_alerta():
    # Citação de outra página pelo seu próprio nome — não é uma afirmação
    # desta página sobre o seu próprio conteúdo.
    html = _html(
        '<li><a href="/bolsa-de-merito.html">Bolsa de mérito 2025/2026 — '
        "para alunos do secundário com escalão ASE</a></li> "
        "Verificado a 24 de junho de 2026."
    )
    assert detectar_alertas(html, "passe-sub23.html", ANO, MES) is None


def test_pagina_escolar_correta_nao_gera_alerta():
    html = _html(
        "Candidaturas para o ano lectivo 2026/2027 abrem em setembro de 2026. "
        "Verificado a 24 de junho de 2026."
    )
    assert detectar_alertas(html, "acao-social-escolar.html", ANO, MES) is None


def test_aguarda_despacho_dentro_do_prazo_nao_gera_alerta():
    html = _html(
        "O valor mais recente confirmado é o de 2025/2026. O valor de "
        "2026/2027 aguarda publicação do despacho anual, previsto para "
        "setembro de 2026."
    )
    assert detectar_alertas(html, "bolsa-de-merito.html", ANO, MES) is None


# ── Casos que devem continuar a ser detectados ─────────────────────────────────

def test_pagina_escolar_realmente_desatualizada_gera_alerta():
    # Ano lectivo 2024/2025, sem qualquer aviso de pendência nem referência legal.
    html = _html(
        "Bolsa de mérito para o ano lectivo 2024/2025. Valor: 1.200,00 €. "
        "Verificado a 10 de outubro de 2024."
    )
    alerta = detectar_alertas(html, "bolsa-de-merito.html", ANO, MES)
    assert alerta is not None
    assert alerta["tipo"] in ("ano_letivo", "data_mes_ano")


def test_data_verificacao_antiga_sem_contexto_gera_alerta():
    html = _html("Verificado a 12 de março de 2024. Valor actual: 500 €.")
    alerta = detectar_alertas(html, "pagina.html", ANO, MES)
    assert alerta is not None
    assert alerta["tipo"] == "data_mes_ano"


def test_aguarda_despacho_com_prazo_ja_passado_gera_alerta():
    # A mesma construção "aguarda ... previsto para agosto de 2026", mas
    # avaliada em setembro — o prazo anunciado já passou, deixa de estar
    # coberto pelo aviso e volta a ser sinalizado.
    html = _html(
        "Verificado a 10 de maio de 2025. O valor aguarda confirmação, "
        "prevista para agosto de 2026."
    )
    alerta = detectar_alertas(html, "pagina.html", 2026, 9)
    assert alerta is not None
