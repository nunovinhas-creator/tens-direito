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
    assert _valor_js(_ler("simulador-abono.html"), "ias2026") == IAS_2026


def test_ias_2026_simulador_ase():
    assert _valor_js(_ler("simulador-ase.html"), "ias2026") == IAS_2026


def test_ias_2026_visivel_no_texto():
    for pagina in ("simulador-abono.html", "simulador-ase.html", "simulador-subsidio-doenca.html"):
        assert "537,13" in _ler(pagina), f"{pagina}: IAS 2026 (537,13€) não visível no texto"


# ── Subsídio de doença — percentagens por escalão ───────────────────────────

def test_percentagens_escalao_subsidio_doenca():
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "taxaEscalao1") == 0.55
    assert _valor_js(html, "taxaEscalao2") == 0.60
    assert _valor_js(html, "taxaEscalao3") == 0.70
    assert _valor_js(html, "taxaEscalao4") == 0.75


def test_percentagens_tuberculose():
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "taxaTuberculoseAte2Familiares") == 0.80
    assert _valor_js(html, "taxaTuberculoseMais2Familiares") == 1.00


# ── Subsídio de doença — pisos mínimos ───────────────────────────────────────

def test_piso_diario_universal():
    assert _valor_js(_ler("simulador-subsidio-doenca.html"), "pisoDiarioUniversal") == 5.37


def test_pisos_proporcionais_300_325():
    html = _ler("simulador-subsidio-doenca.html")
    # 300€/mês ÷ 30 e 325€/mês ÷ 30 — ver CLAUDE.md "GATILHO AUTOBAIXA" (⚠️B)
    assert abs(_valor_js(html, "pisoDiarioProporcionalTaxa55") - 300 / 30) < 1e-9
    assert abs(_valor_js(html, "pisoDiarioProporcionalTaxa60") - 325 / 30) < 1e-9


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
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "diasEsperaContaOutrem") == 3
    assert _valor_js(html, "diasEsperaIndependente") == 10
    assert _valor_js(html, "diasEsperaSeguroSocialVoluntario") == 30


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
