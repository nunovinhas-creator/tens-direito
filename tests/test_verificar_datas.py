"""
Testes para scripts/verificar_datas.py — deteção de conteúdo potencialmente
desactualizado, sem falsos positivos por referências históricas/legais.

Casos cobertos (auditoria de 2026-07-01 às Issues #33-#46, mais a
contra-auditoria seguinte que encontrou testes vácuos e um falso negativo
real em produção):
- diploma 2025
- exemplo ilustrativo
- ano letivo inexistente numa página sem contexto escolar
- página escolar realmente desatualizada
- página escolar correta
- conteúdo "aguarda despacho" (dentro e fora do prazo anunciado)
- facto permanente "desde <ano>"
- citação dentro de link
- "rendimentos de <ano anterior>" e comparação "Em <ano>, ..." — nunca
  colidem com nenhum padrão de data (ver nota em cada teste)
- regressão: "desde que" (condicional) não deve mascarar uma data antiga
  não relacionada
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verificar_datas import detectar_alertas, PADROES

ANO = 2026
MES = 7  # julho — activa data_mes_ano, data_numerica e ano_letivo


def _html(corpo):
    return f"<html><body>{corpo}</body></html>"


def _tem_correspondencia_de_ano_antigo(conteudo, ano):
    """Confirma que o HTML de teste contém pelo menos uma correspondência de
    ano < `ano` nalgum PADRAO — evita testes "vácuos" que passam só por não
    haver nenhuma correspondência a suprimir, sem exercitar a lógica real."""
    for padrao in PADROES:
        if padrao["tipo"] == "ano_letivo":
            for m in re.finditer(padrao["regex"], conteudo):
                if int(m.group(1)) < ano:
                    return True
        elif padrao["tipo"] == "valor_ias":
            continue
        else:
            for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
                if int(m.group(padrao["ano_grupo"])) < ano:
                    return True
    return False


# ── Falsos positivos identificados na auditoria ────────────────────────────────

def test_diploma_2025_nao_gera_alerta():
    html = _html(
        "Fonte: Portaria n.º 480-A/2025/1, de 30 de dezembro de 2025. "
        "Verificado a 24 de junho de 2026."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_rendimentos_ano_anterior_nao_gera_alerta():
    # "rendimentos de 2025" não tem nome de mês nem formato DD/MM/AAAA nem
    # AAAA/AAAA — nunca entra no ramo de "ano antigo" de nenhum PADRAO, por
    # isso não precisa de (nem deve ter) um marcador de supressão dedicado.
    html = _html(
        "Para novos pedidos em 2026, usa-se o rendimento anual de 2025 "
        "para calcular o escalão. Verificado a 24 de junho de 2026."
    )
    assert not _tem_correspondencia_de_ano_antigo(html, ANO)
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_comparacao_historica_2025_vs_2026_nao_gera_alerta():
    # "Em 2025, ..." também não coincide com nenhum PADRAO pelo mesmo motivo.
    html = _html(
        "Em 2025, o valor de referência individual era 8.010,00 €. "
        "Valor em 2026: 8.040,00 €. Verificado a 25/06/2026."
    )
    assert not _tem_correspondencia_de_ano_antigo(html, ANO)
    assert detectar_alertas(html, "pagina.html", ANO, MES) is None


def test_exemplo_ilustrativo_nao_gera_alerta():
    html = _html(
        "Exemplo: licença a começar em agosto de 2026 — os 8 meses "
        "anteriores incluem dezembro de 2025 a julho de 2026. "
        "Verificado a 24 de junho de 2026."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
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
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    assert detectar_alertas(html, "manuais-escolares-mega.html", ANO, MES) is None


def test_ano_antigo_dentro_de_link_nao_gera_alerta():
    # Citação de outra página pelo seu próprio nome — não é uma afirmação
    # desta página sobre o seu próprio conteúdo.
    html = _html(
        '<li><a href="/bolsa-de-merito.html">Bolsa de mérito 2025/2026 — '
        "para alunos do secundário com escalão ASE</a></li> "
        "Verificado a 24 de junho de 2026."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
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
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    assert detectar_alertas(html, "bolsa-de-merito.html", ANO, MES) is None


# ── Regressões encontradas na contra-auditoria ─────────────────────────────────

def test_desde_que_condicional_nao_mascara_data_antiga():
    # "desde que" é uma conjunção condicional ("desde que cumpras as
    # condições"), não uma referência a um ano histórico — não pode activar
    # o marcador "desde <ano>". Antes da correção, o marcador `\bdesde\b`
    # sem exigir um número a seguir apanhava isto por engano e mascarava a
    # data de verificação genuinamente antiga a seguir.
    html = _html(
        "Tens direito ao subsídio desde que cumpras as condições de "
        "recursos. Verificado a 12 de março de 2024."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    alerta = detectar_alertas(html, "pagina.html", ANO, MES)
    assert alerta is not None


def test_rendimento_generico_nao_mascara_valor_desatualizado():
    # A palavra "rendimento" nas proximidades não deve, por si só, suprimir
    # um alerta — só a ausência de correspondência de padrão (caso acima)
    # ou um marcador legítimo o devem fazer. Aqui há uma data de verificação
    # antiga genuína junto da palavra "rendimento", sem qualquer referência
    # legal, exemplo ou aviso de pendência — deve continuar a ser sinalizada.
    html = _html(
        "O valor de referência para rendimentos é de 8.010,00 €. "
        "Consulta o rendimento do agregado familiar. "
        "Verificado a 10 de março de 2025."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    alerta = detectar_alertas(html, "pagina.html", ANO, MES)
    assert alerta is not None


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


def test_valor_monetario_antigo_sem_ano_letivo_gera_alerta():
    # Valor monetário associado a uma data antiga, numa página sem qualquer
    # relação com ano lectivo, sem referência legal nem aviso de pendência.
    html = _html(
        "O subsídio mensal é de 400,00 €. Verificado a 15 de fevereiro de 2024."
    )
    alerta = detectar_alertas(html, "pagina.html", ANO, MES)
    assert alerta is not None


def test_ja_beneficiou_ano_letivo_antigo_nao_gera_alerta():
    # "quem já beneficiou de X em <ano antigo>" é uma afirmação sobre o
    # passado, não uma alegação de que esse ano ainda está em vigor.
    html = _html(
        "Renovação automática: quem já beneficiou de ASE em 2025/2026 "
        "poderá ter renovação automática para o mesmo escalão. "
        "Verificado a 24 de junho de 2026."
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    assert detectar_alertas(html, "acao-social-escolar.html", ANO, MES) is None


def test_par_explicado_propaga_para_ocorrencia_repetida_distante():
    # O mesmo par "2025/2026", repetido bem mais adiante na página (ex.: um
    # cabeçalho FAQ separado da explicação) — a única explicação válida está
    # perto da PRIMEIRA ocorrência; a segunda, sem qualquer marcador por
    # perto, deve ainda assim ser considerada explicada por ser o mesmo par.
    html = _html(
        "O valor de 2025/2026 aguarda publicação do despacho anual, "
        "previsto para setembro de 2026. "
        + ("Texto de enchimento para simular uma página longa. " * 40)
        + "Pergunta frequente: qual é o valor da bolsa em 2025/2026?"
    )
    assert _tem_correspondencia_de_ano_antigo(html, ANO), "teste vácuo — nada a suprimir"
    assert detectar_alertas(html, "bolsa-de-merito.html", ANO, MES) is None


def test_valor_ias_antigo_sem_contexto_gera_alerta():
    # valor_ias só é revisto em janeiro/fevereiro (REVER_EM).
    html = _html(
        "O valor de referência é IAS de 522,50 € (2025). Valor mensal: 400 €."
    )
    assert detectar_alertas(html, "pagina.html", ANO, 1) is not None


def test_valor_ias_com_referencia_legal_nao_gera_alerta():
    html = _html(
        "O valor de referência é IAS de 522,50 €, fixado pela Portaria "
        "n.º 42/2025/1 (2025)."
    )
    assert detectar_alertas(html, "pagina.html", ANO, 1) is None


def test_valor_ias_sem_ano_antigo_proximo_nao_gera_alerta():
    # IAS mencionado só com o ano actual por perto — nada a suprimir nem a sinalizar.
    html = _html("O valor de referência é IAS de 537,13 € (2026).")
    assert detectar_alertas(html, "pagina.html", ANO, 1) is None


def test_data_esperada_ignora_mencao_anterior_a_maior_ja_encontrada():
    # Três datas no mesmo aviso: a mais distante (setembro) aparece antes da
    # mais próxima (agosto) — a segunda menção não deve substituir a maior
    # já encontrada. Avaliado em agosto: setembro ainda não passou, continua
    # suprimido.
    html = _html(
        "Verificado a 10 de maio de 2025. Confirmação final aguarda-se "
        "para setembro de 2026, com uma previsão inicial em agosto de 2026."
    )
    assert detectar_alertas(html, "pagina.html", 2026, 8) is None


def test_prazo_outono_antigo_gera_alerta():
    # prazo_outono só é revisto em agosto/setembro (REVER_EM).
    html = _html("As candidaturas encerraram a 15 de setembro de 2024.")
    assert detectar_alertas(html, "pagina.html", ANO, 8) is not None


def test_prazo_outono_com_aviso_pendente_nao_gera_alerta():
    html = _html(
        "O prazo de 15 de setembro de 2024 já passou; o novo prazo aguarda "
        "confirmação, previsto para setembro de 2026."
    )
    assert detectar_alertas(html, "pagina.html", ANO, 8) is None


def test_par_de_ano_letivo_distante_e_nao_relacionado_ainda_gera_alerta():
    # Risco documentado: a propagação de "par explicado" é à escala da
    # página. Este teste confirma que, quando NENHUMA ocorrência do par
    # antigo tem uma explicação válida em qualquer ponto da página, todas
    # continuam por sinalizar — mesmo havendo, bem distante, um aviso de
    # pendência sobre um par DIFERENTE (2026/2027, já actual, não entra no
    # conjunto de pares antigos explicados).
    html = _html(
        "O ano lectivo é 2025/2026. "
        + ("Texto de enchimento para simular uma página longa. " * 40)
        + "Nota: candidaturas para 2026/2027 aguardam publicação do "
        "despacho, previsto para setembro de 2026."
    )
    alerta = detectar_alertas(html, "pagina.html", ANO, MES)
    assert alerta is not None
