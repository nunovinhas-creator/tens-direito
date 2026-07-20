"""
Canário de valores-âncora — 2026.

Este teste NÃO verifica lógica de cálculo (isso já é feito por
tests/test_simulador_*_calculo.py). Afirma explicitamente, com fonte e
data, os valores-base de 2026 que atravessam vários simuladores e
páginas do site. Extrai os valores reais dos ficheiros HTML publicados
(nunca uma cópia) — o mesmo princípio de test_pesquisa_indice.py.

Quando a lei mudar (tipicamente em janeiro, com a nova Portaria do
IAS), ESTE TESTE TEM DE FALHAR — é o comportamento desejado. Falhar
aqui força uma revisão consciente de todos os simuladores/páginas
afectados, em vez de uma alteração de um valor passar despercebida
sem que nenhuma "data de validade" de página a apanhe. Ao subir os
valores para o ano seguinte, actualizar também os `verificado_em` e a
fonte de cada simulador — nunca só este ficheiro.

Fonte: Portaria n.º 480-A/2025/1, de 30 de dezembro (IAS 2026) e
Decreto-Lei n.º 28/2004, na redação atual (subsídio de doença) — ver
CLAUDE.md secção "FONTES VERIFICADAS E APROVADAS".
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

IAS_2026 = 537.13


def _ler(nome: str) -> str:
    return (BASE_DIR / nome).read_text(encoding="utf-8")


def _valor_js(html: str, chave: str) -> float:
    """Extrai `<chave>: { valor: N, ...}` ou `<chave>: N,` de um objecto
    JS embutido no HTML — falha com uma mensagem clara se a chave não
    existir mais (renomeada ou removida), em vez de um KeyError mudo."""
    m = re.search(rf"\b{re.escape(chave)}\s*:\s*\{{\s*valor\s*:\s*([\d.]+)", html)
    if not m:
        m = re.search(rf"\b{re.escape(chave)}\s*:\s*([\d.]+)", html)
    assert m, f"chave {chave!r} não encontrada — renomeada ou removida?"
    return float(m.group(1))


def _title(pagina: str) -> str:
    m = re.search(r"<title>(.*?)</title>", _ler(pagina), re.S)
    assert m, f"{pagina}: sem <title>"
    return m.group(1)


def _meta_description(pagina: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', _ler(pagina))
    assert m, f'{pagina}: sem <meta name="description">'
    return m.group(1)


def _meta_og(pagina: str, propriedade: str) -> str:
    m = re.search(rf'<meta property="{propriedade}" content="([^"]*)"', _ler(pagina))
    assert m, f'{pagina}: sem <meta property="{propriedade}">'
    return m.group(1)


def _valores_eur(texto: str) -> list:
    """Extrai todos os valores em euros com formato PT (1.342,83€ ou
    590,84 €), na ordem em que aparecem no texto. Valores sem casas
    decimais (ex.: "670€") não são apanhados — não há ambiguidade nos
    casos usados aqui, todos os valores-âncora têm 2 casas decimais."""
    return [
        float(bruto.replace(".", "").replace(",", "."))
        for bruto in re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s?€", texto)
    ]


def _percentagens(texto: str) -> list:
    """Extrai todas as percentagens (ex.: "60%", "55%"), na ordem em que
    aparecem no texto."""
    return [float(p) for p in re.findall(r"(\d{1,3}(?:,\d+)?)\s?%", texto)]


# ── IAS 2026 ─────────────────────────────────────────────────────────────────

def test_ias_2026_simulador_abono():
    # Migrado para ler dados/parametros.json na sessão de 2026-07-19 —
    # PARAMETROS_ABONO deixou de ser um objecto JS inline (CONFIG); o
    # helper _param_abono() está definido mais abaixo, na secção
    # "Abono de família".
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    assert todos["prestacoes"]["abono"]["ias_2026"]["valor"] == IAS_2026


def test_ias_2026_simulador_ase():
    assert _valor_js(_ler("simulador-ase.html"), "ias2026") == IAS_2026


def test_ias_2026_visivel_no_texto():
    # simulador-subsidio-doenca.html saiu desta lista na sessão de
    # 2026-07-19: o piso diário deixou de ser calculado sobre o IAS (era
    # o erro corrigido nesta sessão) — passa a ser calculado sobre a
    # RMMG 2026 (920€), sem relação nenhuma com o IAS. Ver
    # test_piso_diario_minimo_baseado_na_rmmg_nunca_no_ias mais abaixo.
    #
    # simulador-abono.html saiu desta lista na mesma sessão: o simulador
    # aplica sempre o cenário (b) — pedidos novos, indexado ao IAS de
    # 2025 (522,50€) — e a Garantia para a Infância usa sempre o IAS de
    # 2024 (509,26€, corrigido nesta sessão); o IAS 2026 (537,13€) deixou
    # de ser um valor funcionalmente relevante nesta página. Continua
    # coberto como dado aberto (ias_2026 em dados/parametros/abono.yaml,
    # ver test_ias_2026_simulador_abono acima).
    for pagina in ("simulador-ase.html",):
        assert "537,13" in _ler(pagina), f"{pagina}: IAS 2026 (537,13€) não visível no texto"


# ── Subsídio de doença — percentagens/piso, lidos de dados/parametros.json ──
# Sessão "Parâmetros YAML + auditoria factual" (2026-07-19, Commit 1): o
# simulador deixou de ter PARAMETROS_SUBSIDIO_DOENCA como objecto JS inline —
# passa a ler de dados/parametros.json (gerado de
# dados/parametros/subsidio-doenca.yaml), mesmo padrão já usado pelo CSI
# nesta mesma sessão. Estes testes leem a MESMA fonte que o simulador
# consome em runtime, nunca uma cópia.
#
# CORRECÇÃO REAL DA AUDITORIA: o piso diário estava calculado sobre o IAS
# (5,37€ = 30% × 537,13€ ÷ 30) — o Guia Prático 5001 do ISS, I.P. (v4.55,
# 14/07/2026) fixa-o sobre a RMMG 2026 (920€): 30% × 920€ ÷ 30 = 9,20€. O
# segundo piso (300€/325€ mensais, ⚠️B) nunca teve confirmação de fonte
# primária e foi removido — ver dados/parametros/subsidio-doenca.yaml.

import json as _json_pisos  # noqa: E402 (nome local para não colidir com o import json mais abaixo no ficheiro)

_PARAMETROS_JSON_PATH = BASE_DIR / "dados" / "parametros.json"


def _param_subsidio_doenca(nome: str):
    todos = _json_pisos.loads(_PARAMETROS_JSON_PATH.read_text(encoding="utf-8"))
    return todos["prestacoes"]["subsidio-doenca"][nome]["valor"]


def test_percentagens_escalao_subsidio_doenca():
    assert _param_subsidio_doenca("taxa_escalao_ate_30_dias") == 0.55
    assert _param_subsidio_doenca("taxa_escalao_31_a_90_dias") == 0.60
    assert _param_subsidio_doenca("taxa_escalao_91_a_365_dias") == 0.70
    assert _param_subsidio_doenca("taxa_escalao_mais_365_dias") == 0.75


def test_percentagens_tuberculose():
    assert _param_subsidio_doenca("taxa_tuberculose_ate_2_familiares") == 0.80
    assert _param_subsidio_doenca("taxa_tuberculose_mais_2_familiares") == 1.00


# ── Subsídio de doença — piso diário mínimo ─────────────────────────────────

def test_piso_diario_minimo_baseado_na_rmmg_nunca_no_ias():
    """O piso é 30% da RMMG 2026 (920€) ÷ 30 = 9,20€ — nunca 30% do IAS
    (que daria 5,37€, o valor errado corrigido nesta sessão)."""
    assert _param_subsidio_doenca("remuneracao_minima_mensal_garantida_2026") == 920.00
    piso = _param_subsidio_doenca("piso_diario_minimo")
    assert abs(piso - round(0.30 * 920.00 / 30, 2)) < 1e-9
    assert piso == 9.20


def test_piso_300_325_nunca_reaparece_sem_confirmacao():
    """O piso de 300€/325€ mensais (⚠️B) nunca teve confirmação de fonte
    primária — removido nesta sessão. Nunca deve reaparecer em
    dados/parametros/subsidio-doenca.yaml sem uma citação legal primária
    nova, mesmo padrão de
    test_percentagem_rendimento_trabalho_nunca_reaparece_sem_confirmacao
    para o CSI."""
    todos = _json_pisos.loads(_PARAMETROS_JSON_PATH.read_text(encoding="utf-8"))
    sd = todos["prestacoes"]["subsidio-doenca"]
    assert "piso_diario_proporcional_taxa_55" not in sd
    assert "piso_diario_proporcional_taxa_60" not in sd

    for pagina in ("simulador-subsidio-doenca.html", "baixa-medica-subsidio-doenca.html"):
        html = _ler(pagina)
        sem_scripts = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        for valor in ("300 €", "325 €", "300€", "325€", "5,37"):
            assert valor not in sem_scripts, f"{pagina}: {valor!r} reapareceu fora de <script> — questão fechada"


# ── TITLE/META DESCRIPTION — valores legais em metadados (2026-07-06) ───────
#
# Regra CLAUDE.md ("REGRAS DE CONTEÚDO"): qualquer valor legal usado em
# <title> ou meta description tem de estar coberto por este ficheiro —
# nunca pode ficar desligado do IAS (ou da Portaria própria) e mudar
# silenciosamente. Disparado por uma sessão anterior que pôs "1.342,83€"
# (2,5 × IAS) directamente no <title> de subsidio-desemprego.html — se o
# IAS subir em janeiro, esse título fica errado e ninguém repara, porque
# é a promessa visível no Google, fora de qualquer página "com data de
# validade". Scan a todo o repositório (grep a <title>/<meta
# name="description"> por padrões de €/%) — resultado no fim do ficheiro.

def test_subsidio_desemprego_title_teto_2_5x_ias():
    titulo = _title("subsidio-desemprego.html")
    assert _valores_eur(titulo) == [round(IAS_2026 * 2.5, 2)], titulo


def test_subsidio_desemprego_meta_description_piso_ias():
    # A description passou a citar só o piso (2026-07-06, revisão de CTR) —
    # o teto de 2,5x IAS continua ancorado no <title> pelo teste acima.
    desc = _meta_description("subsidio-desemprego.html")
    assert _valores_eur(desc) == [IAS_2026], desc


def test_subsidio_desemprego_og_tags_espelham_title_e_description():
    # Guardrail extra: o cenário real que motivou este ficheiro foi um
    # valor actualizado só num sítio (o <title>) — impede que
    # title/description e og:title/og:description voltem a divergir.
    assert _meta_og("subsidio-desemprego.html", "og:title") == _title("subsidio-desemprego.html")
    assert _meta_og("subsidio-desemprego.html", "og:description") == _meta_description("subsidio-desemprego.html")


def test_cuidador_informal_meta_description_valor_1_1x_ias():
    desc = _meta_description("cuidador-informal.html")
    assert _valores_eur(desc) == [round(IAS_2026 * 1.1, 2)], desc


def test_acao_social_escolar_meta_description_ias_literal():
    desc = _meta_description("acao-social-escolar.html")
    assert _valores_eur(desc) == [IAS_2026], desc


def test_baixa_medica_meta_description_percentagens_batem_com_simulador():
    # As percentagens da description não estão ligadas ao IAS, mas às
    # mesmas taxaEscalao1/taxaEscalao4 já ancoradas acima — sem este
    # teste, a description podia divergir do simulador sem que nenhum
    # outro teste desta suite reparasse (o teste do simulador só lê o
    # próprio simulador, nunca este artigo).
    desc = _meta_description("baixa-medica-subsidio-doenca.html")
    assert _percentagens(desc) == [55.0, 75.0], desc


def test_simulador_subsidio_doenca_meta_description_percentagens_batem_com_o_js():
    desc = _meta_description("simulador-subsidio-doenca.html")
    assert _percentagens(desc) == [55.0, 75.0], desc


# ── Valores legais sem relação com o IAS — canário de consistência ──────────
#
# Vêm de Portarias/limiares próprios (não são múltiplo do IAS), por isso
# não há fórmula para verificar — mas continuam "valores legais em
# metadados" pela mesma regra. O canário aqui é de CONSISTÊNCIA: o valor
# da meta description tem de bater sempre com o valor publicado no
# corpo do próprio artigo, já fact-checked; se um dia divergirem, alguém
# editou um sítio e esqueceu o outro.

def test_abono_meta_description_bate_com_tabela_do_artigo():
    html = _ler("abono-de-familia.html")
    desc = _meta_description("abono-de-familia.html")
    assert _valores_eur(desc) == [190.98], desc
    assert "<td><strong>190,98 €</strong></td>" in html, "valor da tabela do 1.º escalão não encontrado no corpo"


def test_psi_meta_description_bate_com_o_corpo_do_artigo():
    html = _ler("prestacao-social-para-a-inclusao.html")
    desc = _meta_description("prestacao-social-para-a-inclusao.html")
    assert 333.64 in _valores_eur(desc), desc
    assert "333,64 €/mês" in html, "componente base da PSI não encontrada no corpo"
    assert 60.0 in _percentagens(desc), desc


def test_amim_meta_description_bate_com_o_limiar_do_artigo():
    html = _ler("amim.html")
    desc = _meta_description("amim.html")
    assert _percentagens(desc) == [60.0], desc
    assert "Limiar crítico: 60%" in html


def test_limiar_60_por_cento_nunca_diverge_entre_amim_e_psi():
    # Mesmo limiar de incapacidade (AMIM), citado em duas páginas
    # diferentes — nunca pode divergir entre elas.
    limiar_psi = _percentagens(_meta_description("prestacao-social-para-a-inclusao.html"))
    limiar_amim = _percentagens(_meta_description("amim.html"))
    assert limiar_psi == limiar_amim == [60.0]


def test_subsidio_desemprego_meta_description_percentagem_bate_com_o_corpo():
    # 65% é a taxa fixa do DL n.º 220/2006 (RR × 65%) — sem relação com o
    # IAS, canário de consistência com o corpo do artigo (já fact-checked).
    html = _ler("subsidio-desemprego.html")
    desc = _meta_description("subsidio-desemprego.html")
    assert _percentagens(desc) == [65.0], desc
    assert "RR × 65%" in html, "fórmula RR × 65% não encontrada no corpo"


# ── Subsídio de doença — dias de espera ──────────────────────────────────────

def test_dias_de_espera_por_vinculo():
    # Migrado para ler dados/parametros.json na sessão de 2026-07-19 —
    # PARAMETROS_SUBSIDIO_DOENCA deixou de ser um objecto JS inline
    # (ver _param_subsidio_doenca() mais acima).
    assert _param_subsidio_doenca("dias_espera_conta_outrem") == 3
    assert _param_subsidio_doenca("dias_espera_independente") == 10
    assert _param_subsidio_doenca("dias_espera_seguro_social_voluntario") == 30


# ── Cartão Europeu de Estacionamento (secção "Bónus", 2026-07-11) ────────────
# Valores do DL n.º 307/2003, na redação do DL n.º 128/2017 (fontes:
# imt-ip.pt e gov.pt, verificados a 2026-07-11). Sem relação com o IAS —
# canário de consistência: a mesma secção vive em 3 páginas e os limiares
# (≥60%, ≥95%) e a validade (10 anos) nunca podem divergir entre elas.

PAGINAS_CARTAO_ESTACIONAMENTO = (
    "amim.html",
    "prestacao-social-para-a-inclusao.html",
    "cuidador-informal.html",
)


def _seccao_cartao(pagina: str) -> str:
    html = _ler(pagina)
    m = re.search(
        r'<div class="card" id="cartao-estacionamento">(.*?)</div>\s*\n\s*(?:<!-- RELACIONADOS:INICIO -->)',
        html,
        re.S,
    )
    assert m, f"{pagina}: secção #cartao-estacionamento não encontrada"
    return m.group(1)


def test_cartao_estacionamento_limiares_e_validade_consistentes():
    for pagina in PAGINAS_CARTAO_ESTACIONAMENTO:
        seccao = _seccao_cartao(pagina)
        # 4 situações com limiar de 60% (motora, intelectual/PEA,
        # oncológica, Forças Armadas) e 1 com 95% (visual).
        assert seccao.count("≥ 60%") == 4, f"{pagina}: limiar 60% divergente na secção do cartão"
        assert seccao.count("≥ 95%") == 1, f"{pagina}: limiar 95% divergente na secção do cartão"
        assert "Validade: 10 anos" in seccao, f"{pagina}: validade de 10 anos em falta"
        assert "Decreto-Lei n.º 307/2003" in seccao, f"{pagina}: diploma base em falta"
        assert "Decreto-Lei n.º 128/2017" in seccao, f"{pagina}: diploma alterador em falta"
        assert "pessoal e intransmissível" in seccao, f"{pagina}: regra de uso em falta"


def test_cartao_estacionamento_liga_ao_guia_amim_excepto_no_proprio():
    for pagina in PAGINAS_CARTAO_ESTACIONAMENTO:
        seccao = _seccao_cartao(pagina)
        if pagina == "amim.html":
            assert '"/amim.html"' not in seccao, "amim.html não deve linkar para si próprio"
        else:
            assert 'href="/amim.html"' in seccao, f"{pagina}: sem link para o guia do AMIM"


# ── Assistência a filhos e família (2026-07-11) ──────────────────────────────
# Valores do Código do Trabalho (arts. 49.º/52.º/252.º) e do DL n.º 91/2009
# (art. 36.º na redação da Lei n.º 73-A/2025 — LOE2026), confirmados nos
# guias práticos da Segurança Social a 2026-07-11 (incl. 80%/100% RR
# pós-LOE2026, verificação do PASSO 0 dessa sessão). O mínimo diário de
# 14,32 € é IAS-derivado (80% de 1/30 do IAS) — recalculado aqui para
# falhar sozinho quando o IAS mudar; o tecto de 1.611,39 €/mês é 3 × IAS.

def test_assistencia_familia_dias_e_formularios():
    html = _ler("assistencia-familia-filhos.html")
    # Dias por modalidade (art. 49.º e 252.º CT)
    assert "30 dias por ano civil" in html, "30 dias (filho <12) em falta"
    assert "15 dias por ano civil" in html, "15 dias (filho ≥12) em falta"
    assert html.count("Modelo RP5052-DGSS") >= 2, "formulário RP5052-DGSS em falta"
    assert "Modelo RP5053" in html, "formulário RP5053 em falta"
    assert "Modelo RP5054" in html, "formulário RP5054 em falta"
    # Prazos de 6 meses (garantia e prazo para pedir)
    assert "6 meses de descontos" in html, "prazo de garantia de 6 meses em falta"
    assert "6 meses</strong> a contar do 1.º dia de falta" in html, "prazo para pedir (6 meses) em falta"


def test_assistencia_familia_minimo_diario_e_teto_derivados_do_ias():
    html = _ler("assistencia-familia-filhos.html")
    # Mínimo diário = 80% de 1/30 do IAS — falha sozinho quando o IAS mudar.
    minimo = round(IAS_2026 / 30 * 0.8, 2)
    assert minimo == 14.32
    assert html.count("14,32 €") >= 2, "mínimo diário de 14,32 € em falta (subsídio filho + avós)"
    assert "537,13 €" in html, "IAS 2026 em falta"
    # Tecto do subsídio deficiência/doença crónica/oncológica = 3 × IAS.
    teto = round(IAS_2026 * 3, 2)
    assert teto == 1611.39
    assert "1.611,39 €" in html, "tecto de 3 × IAS em falta"


def test_assistencia_familia_percentagens_pos_loe2026():
    # 80% RR (deficiência/doença crónica) e 100% RR (oncológica) — valores
    # em vigor desde 01/01/2026 (LOE2026), confirmados no guia prático da
    # Segurança Social e em garantiainfancia.gov.pt a 2026-07-11.
    html = _ler("assistencia-familia-filhos.html")
    assert "80% da remuneração de referência" in html
    assert "100% da remuneração de referência" in html
    # A description promete "30 dias" e "2026" — canário do metadado.
    desc = _meta_description("assistencia-familia-filhos.html")
    assert "30 dias" in desc and "2026" in desc and "subsídio" in desc


# ── Renovação do Cartão de Cidadão — preços administrativos (justica.gov.pt) ─
# Valores fixos por Portaria/tabela de emolumentos do IRN, sem relação com
# o IAS — canário de consistência entre title/meta description e o corpo
# já fact-checked (mesmo padrão de abono/PSI/AMIM acima), não uma fórmula.


def test_renovar_cc_title_bate_com_preco_online_do_corpo():
    html = _ler("renovar-cartao-cidadao.html")
    title = _title("renovar-cartao-cidadao.html")
    assert _valores_eur(title) == [16.20], title
    assert "<td>16,20 €</td>" in html, "preço online (25+) não encontrado na tabela do corpo"


def test_renovar_cc_meta_description_bate_com_precos_do_corpo():
    html = _ler("renovar-cartao-cidadao.html")
    desc = _meta_description("renovar-cartao-cidadao.html")
    valores = _valores_eur(desc)
    assert 16.20 in valores and 18.0 in valores, desc
    assert "<td>16,20 €</td>" in html
    assert "<td>18,00 €</td>" in html


def test_renovar_cc_precos_completos_por_idade_e_urgencia():
    # Tabela completa (normal/urgente/muito urgente × ≥25 anos/<25 anos) —
    # falha sozinho se algum valor for alterado sem rever a tabela inteira.
    html = _ler("renovar-cartao-cidadao.html")
    for valor in ("16,20 €", "18,00 €", "15,00 €", "33,00 €", "30,00 €", "53,00 €", "50,00 €"):
        assert f"<td>{valor}</td>" in html, f"{valor} em falta na tabela de preços"


# ── FASE 2 — dados/parametros/*.yaml como fonte, padrão OpenFisca ──────────
# (sessão de dados abertos, 2026-07-19). dados/parametros.json é gerado por
# scripts/gerar_parametros_json.py a partir de dados/parametros/*.yaml —
# este canário lê a MESMA fonte que os simuladores já migrados consomem em
# runtime (via fetch), nunca uma cópia. Quando um simulador novo migrar
# para este padrão, os seus valores ganham a mesma cobertura aqui.
import json  # noqa: E402
from datetime import date  # noqa: E402

import yaml  # noqa: E402

PARAMETROS_DIR = BASE_DIR / "dados" / "parametros"
PARAMETROS_JSON = BASE_DIR / "dados" / "parametros.json"


def test_csi_dados_parametros_json_bate_com_a_pagina_do_artigo():
    """dados/parametros.json (consumido em runtime por simulador-csi.html)
    tem de continuar a bater com os valores 2026 já fact-checked e
    publicados em complemento-solidario-idosos.html — corrigir SEMPRE na
    fonte (dados/parametros/csi.yaml + a própria página do artigo), nunca
    só aqui, quando a lei mudar.

    CORRECÇÃO PASSO 0 (2026-07-19): idade mínima passa a MESES TOTAIS
    (801 = 66 anos e 9 meses) — nunca só anos completos (66), que dava
    falso-elegível a alguém com, por exemplo, 66 anos e 3 meses.
    `percentagem_rendimento_trabalho` foi removido (ver
    test_percentagem_rendimento_trabalho_nunca_reaparece_sem_confirmacao
    mais abaixo) — trabalho passa a contar a 100%."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    csi = todos["prestacoes"]["csi"]
    assert csi["valor_referencia_individual_anual"]["valor"] == 8040
    assert csi["valor_referencia_casal_anual"]["valor"] == 14070
    assert csi["idade_minima_meses_totais"]["valor"] == 801

    artigo = _ler("complemento-solidario-idosos.html")
    assert "8.040" in artigo
    assert "14.070" in artigo
    assert "66 anos e 9 meses" in artigo


def test_percentagem_rendimento_trabalho_nunca_reaparece_sem_confirmacao():
    """Questão fechada com fonte primária (2026-07-19, mesmo dia): Guia
    Prático 8002 do ISS, I.P. ("Complemento Solidário para Idosos",
    v4.53, 21/05/2026), secção C1.1, lista os rendimentos considerados
    sem nenhuma regra de 80% — rendimentos de trabalho contam a 100%
    ("anuais brutos, antes dos descontos"). O parâmetro
    percentagem_rendimento_trabalho nunca deve reaparecer no YAML (não
    há nenhuma percentagem de redução a parametrizar quando a regra é
    "sem redução"), e a string "80%" nunca deve voltar a aparecer em
    nenhuma página do CSI — a 1.ª versão desta correcção só tinha
    tocado no simulador; o artigo complemento-solidario-idosos.html
    ainda afirmava 80% na sua tabela de rendimentos (facto de uma
    sessão anterior) até ser corrigido no mesmo commit desta versão do
    teste."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    assert "percentagem_rendimento_trabalho" not in todos["prestacoes"]["csi"]

    for pagina in ("simulador-csi.html", "complemento-solidario-idosos.html"):
        html = _ler(pagina)
        # Exclui blocos <script> (comentários JS documentam a remoção —
        # "removemos os 80%" é histórico legítimo para manutenção,
        # nunca uma afirmação activa ao utilizador; JSON-LD já não tem
        # "80%" desde a correcção, verificado por json.loads noutro
        # teste). Só o conteúdo visível/HTML é que nunca pode voltar a
        # mostrar "80%".
        sem_scripts = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        assert "80%" not in sem_scripts, f"{pagina}: '80%' reapareceu fora de <script> — questão fechada, não deve voltar sem novo facto"


def test_dados_parametros_json_sincronizado_com_os_yaml():
    """Rede de segurança contra editar um YAML e esquecer de correr
    `python scripts/gerar_parametros_json.py` — mesma verificação que
    `--check` faz, replicada aqui para aparecer na suite normal."""
    import subprocess
    import sys

    resultado = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts" / "gerar_parametros_json.py"), "--check"],
        capture_output=True, text=True,
    )
    assert resultado.returncode == 0, (
        "dados/parametros.json diverge de dados/parametros/*.yaml — correr "
        f"`python scripts/gerar_parametros_json.py` para regenerar.\n{resultado.stdout}{resultado.stderr}"
    )


def test_nenhum_parametro_vigente_fica_sem_verificado_em():
    """PASSO 0 (obrigatório para qualquer valor migrado para YAML): réplica
    visível na suite de testes da guarda dura de
    scripts/gerar_parametros_json.py::_valor_vigente — nenhum parâmetro
    cuja vigência já começou pode ter 'verificado_em' vazio. Confirmado a
    falhar de propósito nesta sessão (verificado_em esvaziado
    manualmente, gerar_parametros_json.py rejeitou com ERRO, revertido)."""
    hoje = date.today()
    for ficheiro in sorted(PARAMETROS_DIR.glob("*.yaml")):
        bruto = yaml.safe_load(ficheiro.read_text(encoding="utf-8")) or {}
        for nome_parametro, definicao in bruto.items():
            for entrada in definicao.get("valores", []):
                vigencia = date.fromisoformat(str(entrada["vigencia_inicio"]))
                if vigencia <= hoje:
                    assert entrada.get("verificado_em"), (
                        f"{ficheiro.name}:{nome_parametro} — vigência {vigencia} já "
                        "começou mas 'verificado_em' está vazio (PASSO 0 não cumprido)"
                    )
                    assert entrada.get("referencia_legal") and entrada.get("fonte_url"), (
                        f"{ficheiro.name}:{nome_parametro} — sem referencia_legal/fonte_url"
                    )
