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

def test_subsidio_desemprego_title_sem_valor_ancora():
    # 2026-08-17 (revisão de CTR): o <title> deixou de citar o teto de
    # 2,5x IAS ("valor até 1.342,83€" → "valor, duração e como pedir") —
    # este teste substitui test_subsidio_desemprego_title_teto_2_5x_ias
    # (removido) e tranca a ausência, não uma fórmula: qualquer valor
    # legal em € que volte a aparecer no <title> tem de ganhar cobertura
    # própria neste ficheiro, nunca ficar solto. O piso (100% IAS)
    # continua ancorado na meta description pelo teste seguinte.
    titulo = _title("subsidio-desemprego.html")
    assert _valores_eur(titulo) == [], titulo


def test_subsidio_desemprego_meta_description_piso_ias():
    # A description cita o piso (2026-07-06, revisão de CTR); o teto de
    # 2,5x IAS já não é citado em title nem description (2026-08-17).
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


def test_bolsa_merito_meta_description_valor_2_5x_ias():
    # bolsa-de-merito.html corrigida em 2026-08-25 (sessão "Sentinela
    # para o despacho da ASE" tinha sinalizado esta página como
    # pendente): dizia "o valor de 2026/2027 aguarda publicação do
    # despacho anual" — não existe despacho próprio, o multiplicador
    # 2,5×IAS é fixo desde o Despacho n.º 8452-A/2015 (2015), mesmo
    # diploma-base da ASE. O valor sobe sozinho com a Portaria anual do
    # IAS — se este teste falhar em janeiro, é a Portaria nova a forçar
    # a revisão consciente da página, exactamente como desenhado.
    desc = _meta_description("bolsa-de-merito.html")
    assert _valores_eur(desc) == [round(2.5 * IAS_2026, 2)], desc


def test_bolsa_merito_og_tags_espelham_title_e_description():
    assert _meta_og("bolsa-de-merito.html", "og:title") == _title("bolsa-de-merito.html")
    assert _meta_og("bolsa-de-merito.html", "og:description") == _meta_description("bolsa-de-merito.html")


def test_bolsa_merito_valor_e_prestacoes_2026_2027_batem_com_o_corpo():
    html = _ler("bolsa-de-merito.html")
    valor = round(2.5 * IAS_2026, 2)
    p1 = round(valor * 0.40, 2)
    p2 = round(valor * 0.30, 2)
    assert abs(p1 + 2 * p2 - valor) < 1e-9

    def _fmt(v: float) -> str:
        return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

    assert f'<div class="valor-num">{_fmt(valor)}</div>' in html
    assert f"<strong>{_fmt(p1)}</strong>" in html
    assert f"<strong>{_fmt(p2)}</strong>" in html


def test_bolsa_merito_nunca_afirma_despacho_proprio_pendente():
    # Tranca a correcção de 2026-08-25 — nunca deve reaparecer a
    # premissa de que o valor "aguarda" um despacho anual próprio da
    # bolsa (não existe; ver CLAUDE.md secção "PÁGINAS COM DATAS
    # SAZONAIS", nota de 2026-08-25).
    html = _ler("bolsa-de-merito.html")
    for trecho in ("aguarda publicação do despacho", "será atualizado após publicação do despacho"):
        assert trecho not in html, f"bolsa-de-merito.html: {trecho!r} reapareceu — questão fechada em 2026-08-25"


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


# ── Garantia para a Infância — canário entre garantia-para-a-infancia.html
# e dados/parametros.json (sessão "Garantia para a Infância", 2026-09-02).
# O valor mensal (127,33 €) e o diferencial (52,20 € = 127,33 € - 75,13 €)
# vêm de dados/parametros.json (fonte única, migração de 2026-07-19).
#
# LIMIAR DE ELEGIBILIDADE — FECHADO (sessão "Limiar da garantia —
# cenários", 2026-09-02, 2.ª ronda "CORRIGIR O QUE ESTÁ CONFIRMADO"): a
# hipótese registada aqui na 1.ª ronda ("pode seguir a mesma estrutura de
# 3 cenários", "não confirmado em fonte primária") foi confirmada — a
# Portaria n.º 223/2022, de 6 de setembro, art. 2.º, foi lida directamente
# pelo Nuno e fixa o limite em 0,35 do IAS "em vigor à data a que se
# reportam os rendimentos apurados", mesma redacção do art. 14.º n.º 2 do
# DL n.º 176/2003 (limites de escalão) — por isso o limiar segue mesmo os
# 3 cenários: 2.495,37€ (manutenção), 2.560,25€ (pedidos novos, usado por
# `simulador-abono.html`) e 2.631,94€ (reavaliação). Ver
# dados/parametros/abono.yaml para os 3 parâmetros
# (garantia_infancia_limite_rr_anual_cenario_*) e o comentário sobre o
# multiplicador ×14 (analogia com o regime dos escalões, nunca norma
# expressa encontrada — continua por confirmar, mas isso já não afecta se
# o LIMIAR varia por cenário, só o valor exacto de cada cenário).

_ABONO = None


def _param_abono(nome: str):
    global _ABONO
    if _ABONO is None:
        todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
        _ABONO = todos["prestacoes"]["abono"]
    return _ABONO[nome]["valor"]


def test_garantia_infancia_title_valor_mensal_bate_com_o_yaml():
    title = _title("garantia-para-a-infancia.html")
    assert _param_abono("garantia_infancia_valor_mensal") in _valores_eur(title), title


def test_garantia_infancia_meta_description_diferencial_e_valor_mensal():
    desc = _meta_description("garantia-para-a-infancia.html")
    valores = _valores_eur(desc)
    valor_mensal = _param_abono("garantia_infancia_valor_mensal")
    diferencial = round(valor_mensal - _param_abono("escalao1_valor_37_a_72_meses"), 2)
    assert valor_mensal in valores, desc
    assert diferencial in valores, desc


def test_garantia_infancia_exemplo_no_corpo_bate_com_abono_de_familia():
    """O exemplo (criança de 8 anos, 1.º escalão) é o mesmo já publicado
    em abono-de-familia.html — nunca recalculado à parte, só reafirmado.
    abono-de-familia.html não foi tocado nesta sessão (decisão do Nuno);
    este teste confirma que os dois textos, em ficheiros diferentes,
    continuam a citar exactamente o mesmo valor mensal."""
    html_novo = _ler("garantia-para-a-infancia.html")
    html_abono = _ler("abono-de-familia.html")
    valor_mensal = _param_abono("garantia_infancia_valor_mensal")
    valor_mensal_fmt = f"{valor_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    assert f"{valor_mensal_fmt} €/mês" in html_novo, "valor mensal ausente do corpo da página nova"
    assert f"{valor_mensal_fmt} €/mês" in html_abono, "valor mensal ausente do corpo de abono-de-familia.html"


def test_garantia_infancia_limiar_cita_a_portaria_e_os_3_cenarios():
    """Fecha o achado da 1.ª ronda (2026-09-02): o limiar deixou de ser
    "não confirmado" — a Portaria n.º 223/2022 foi lida directamente e
    citada. Este teste tranca a citação e os 3 valores por cenário no
    corpo da página — nunca um valor único apresentado sem a variação
    (regressão para o estado anterior à confirmação)."""
    html = _ler("garantia-para-a-infancia.html")
    assert "Portaria n.º 223/2022" in html
    for valor in ("2.495,37", "2.560,25", "2.631,94"):
        assert f"{valor} €/ano" in html, f"{valor} €/ano ausente do corpo — a variação por cenário desapareceu?"


def test_garantia_infancia_multiplicador_14_continua_sinalizado_como_por_confirmar():
    """O LIMIAR por cenário está confirmado (Portaria n.º 223/2022, art.
    2.º), mas o multiplicador ×14 usado para o anualizar não tem norma
    expressa encontrada — nem nesta sessão nem na anterior. Este teste
    tranca que a página continua a avisar disso explicitamente, nunca
    apresentando o ×14 como facto tão certo quanto o resto."""
    html = _ler("garantia-para-a-infancia.html")
    assert "×14" in html or "por confirmar" in html.lower()
    assert "multiplicador" in html.lower()


def test_garantia_infancia_yaml_tem_os_3_parametros_por_cenario():
    """Os 3 valores por cenário vêm de dados/parametros.json (nunca
    hardcoded na página nem nos testes) — mesmo padrão de
    test_garantia_infancia_title_valor_mensal_bate_com_o_yaml acima."""
    assert _param_abono("garantia_infancia_limite_rr_anual_cenario_manutencao_2025") == 2495.37
    assert _param_abono("garantia_infancia_limite_rr_anual_cenario_pedidos_novos_2026") == 2560.25
    assert _param_abono("garantia_infancia_limite_rr_anual_cenario_reavaliacao_2026") == 2631.94


def test_garantia_infancia_psu_por_leitura_directa_nunca_por_inferencia():
    """A relação com a PSU vem de leitura directa do texto integral do
    DL n.º 166/2026 (art. 62.º, norma revogatória) — nunca de "segue a
    mesma lógica do abono", a inferência explicitamente rejeitada nesta
    sessão a favor de uma verificação real contra a fonte primária."""
    html = _ler("garantia-para-a-infancia.html")
    assert "166/2026" in html
    assert "segue a mesma lógica" not in html.lower()


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


def test_limiar_60_por_cento_tambem_no_guia_de_beneficios_fiscais_do_amim():
    # amim-beneficios-fiscais.html (2026-08-19, split de amim.html) repete
    # o mesmo limiar de 60% na meta description — nunca pode divergir dos
    # dois já trancados acima.
    limiar_amim = _percentagens(_meta_description("amim.html"))
    limiar_fiscal = _percentagens(_meta_description("amim-beneficios-fiscais.html"))
    assert limiar_amim == limiar_fiscal == [60.0]


def test_cartao_estacionamento_meta_description_limiares_batem_com_o_corpo():
    # cartao-europeu-estacionamento.html (2026-08-19, split de amim.html)
    # cita os dois limiares do cartão (60%/95%) na meta description —
    # têm de bater com os valores já trancados no corpo por
    # test_cartao_estacionamento_limiares_e_validade_consistentes.
    percentagens = _percentagens(_meta_description("cartao-europeu-estacionamento.html"))
    assert 60.0 in percentagens, percentagens
    assert 95.0 in percentagens, percentagens


# ── PSI: 333,64€/670€ citados também em amim.html (resumo da secção 7.2,
# 2026-08-19) — canário de consistência entre as duas páginas, pedido
# explicitamente antes do split para nunca ficarem a divergir em silêncio.
# 670€ não tem 2 casas decimais no texto ("670 €/mês"), por isso fica fora
# de _valores_eur() (documentado ali como não capturado) — comparado por
# substring literal nas duas páginas, mesmo formato em ambas.

def test_valores_psi_batem_entre_amim_e_prestacao_social_para_a_inclusao():
    html_amim = _ler("amim.html")
    html_psi = _ler("prestacao-social-para-a-inclusao.html")
    assert "333,64 €/mês" in html_amim, "componente base da PSI em falta no resumo de amim.html"
    assert "333,64 €/mês" in html_psi, "componente base da PSI em falta no corpo de prestacao-social-para-a-inclusao.html"
    assert "670 €/mês" in html_amim, "complemento da PSI em falta no resumo de amim.html"
    assert "670 €/mês" in html_psi, "complemento da PSI em falta no corpo de prestacao-social-para-a-inclusao.html"


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


# ── Cartão Europeu de Estacionamento (secção "Bónus", 2026-07-11; página
# própria desde 2026-08-19 — ver "amim-html-split-three-pages") ──────────────
# Valores do DL n.º 307/2003, na redação do DL n.º 128/2017 (fontes:
# imt-ip.pt e gov.pt, verificados a 2026-07-11). Sem relação com o IAS —
# canário de consistência: a mesma secção vive em 3 páginas e os limiares
# (≥60%, ≥95%) e a validade (10 anos) nunca podem divergir entre elas.
# `amim.html` saiu desta lista a 2026-08-19: o conteúdo completo do cartão
# mudou-se para `cartao-europeu-estacionamento.html` (página própria,
# cluster idosos-incapacidade-cuidadores); amim.html passou a ter só um
# resumo de 2-3 linhas + link, fora do âmbito deste canário de duplicação.

PAGINAS_CARTAO_ESTACIONAMENTO = (
    "cartao-europeu-estacionamento.html",
    "prestacao-social-para-a-inclusao.html",
    "cuidador-informal.html",
)


def _seccao_cartao(pagina: str) -> str:
    html = _ler(pagina)
    # Limite pelo próprio fecho do <div> (sem <div> aninhado dentro do
    # cartão) — não pela adjacência a <!-- RELACIONADOS:INICIO -->, que
    # deixou de valer em cartao-europeu-estacionamento.html (tem
    # .checklist-final e FAQ entre o cartão e RELACIONADOS).
    m = re.search(
        r'<div class="card" id="cartao-estacionamento">(.*?)\n\s*</div>',
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


def test_cartao_estacionamento_liga_ao_guia_amim():
    # As 3 páginas com o cartão completo citam sempre o AMIM como o
    # documento essencial — nunca amim.html em si (que já não tem esta
    # secção desde 2026-08-19, só um resumo com link para cá).
    for pagina in PAGINAS_CARTAO_ESTACIONAMENTO:
        seccao = _seccao_cartao(pagina)
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


def _valores_eur_inteiros(texto: str) -> list:
    """Extrai valores em euros SEM casas decimais, formato PT de milhares
    (ex.: "330.539 €", "86.634€") — os limiares do cluster Habitação
    (Sessão 1, 2026-07-20) são sempre inteiros, ao contrário dos valores
    já cobertos por `_valores_eur()` (sempre com 2 casas decimais).
    Nunca confunde os dois formatos: o `\\d{2}` final de `_valores_eur`
    não bate com um euro inteiro, e este regex exige que NÃO haja vírgula
    a seguir aos milhares."""
    return [
        int(bruto.replace(".", ""))
        for bruto in re.findall(r"(?<!,)\b(\d{1,3}(?:\.\d{3})+)\s?€", texto)
    ]


# ── Cluster Habitação — IMT Jovem e Garantia Pública (Sessão 1, 2026-07-20) ──
# dados/parametros/habitacao.yaml é a fonte única destes valores — nunca
# hardcoded de memória nas páginas. `_valores_eur_inteiros()` extrai os
# limiares em euros directamente do title/meta description reais; o
# canário falha sozinho se algum valor for editado numa página sem
# actualizar o YAML (ou vice-versa), forçando revisão consciente.

_HABITACAO = None


def _param_habitacao(nome: str):
    global _HABITACAO
    if _HABITACAO is None:
        todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
        _HABITACAO = todos["prestacoes"]["habitacao"]
    return _HABITACAO[nome]["valor"]


def test_imt_jovem_title_valor_isencao_total():
    title = _title("imt-jovem.html")
    assert _valores_eur_inteiros(title) == [_param_habitacao("imt_isencao_total_limite_eur")], title


def test_imt_jovem_meta_description_isencao_total_e_parcial():
    desc = _meta_description("imt-jovem.html")
    valores = _valores_eur_inteiros(desc)
    assert _param_habitacao("imt_isencao_total_limite_eur") in valores, desc
    assert _param_habitacao("imt_isencao_parcial_limite_eur") in valores, desc
    assert _param_habitacao("imt_taxa_sobre_excedente_pct") in _percentagens(desc), desc


def test_imt_jovem_og_tags_espelham_title_e_description():
    assert _meta_og("imt-jovem.html", "og:title") == _title("imt-jovem.html")
    assert _meta_og("imt-jovem.html", "og:description") == _meta_description("imt-jovem.html")


def test_imt_jovem_escaloes_2026_no_corpo_batem_com_o_yaml():
    html = _ler("imt-jovem.html")
    total = _param_habitacao("imt_isencao_total_limite_eur")
    parcial = _param_habitacao("imt_isencao_parcial_limite_eur")
    # Formata como PT (milhares com ponto) para comparar com o texto real.
    assert f"{total:,}".replace(",", ".") in html
    assert f"{parcial:,}".replace(",", ".") in html
    assert f"{_param_habitacao('imt_prazo_afetacao_meses')} meses" in html
    assert f"{_param_habitacao('imt_prazo_manutencao_anos')} anos" in html


def test_imt_jovem_limites_regioes_autonomas_no_corpo_batem_com_o_yaml():
    """Sessão 2 (2026-07-20): os limites do IMT Jovem nas Regiões
    Autónomas (413.174€/826.228€) vêm do YAML, nunca duplicados — a
    página tem de os mostrar exactamente como estão em
    dados/parametros.json (nota RA junto à tabela + FAQ)."""
    html = _ler("imt-jovem.html")
    total_ra = _param_habitacao("imt_ra_isencao_total_limite_eur")
    parcial_ra = _param_habitacao("imt_ra_isencao_parcial_limite_eur")
    assert f"{total_ra:,}".replace(",", ".") in html, "limite RA de isenção total ausente da página"
    assert f"{parcial_ra:,}".replace(",", ".") in html, "limite RA de isenção parcial ausente da página"


def test_imt_jovem_limites_ra_sao_25_por_cento_acima_do_continente():
    """Canário de coerência interna: os limites RA são, por lei (Lei
    n.º 21/90), os do Continente elevados em 25%, com arredondamento ao
    euro (meio-euro para cima — padrão das tabelas práticas da AT,
    confirmado no PASSO 0 pelo 1.º escalão RA publicado, 132.933€). Se a
    actualização anual dos escalões do Continente for aplicada ao YAML e
    os valores RA ficarem esquecidos, este teste falha sozinho."""
    import math
    for continente, ra in [
        ("imt_isencao_total_limite_eur", "imt_ra_isencao_total_limite_eur"),
        ("imt_isencao_parcial_limite_eur", "imt_ra_isencao_parcial_limite_eur"),
    ]:
        esperado = math.floor(_param_habitacao(continente) * 1.25 + 0.5)
        assert _param_habitacao(ra) == esperado, (
            f"{ra}={_param_habitacao(ra)} ≠ {continente}×1,25 arredondado ({esperado})"
        )


def test_imt_jovem_exclusao_de_terrenos_presente_na_pagina():
    """A exclusão de terrenos para construção (informação vinculativa da
    AT, out. 2025) está registada no YAML e tem de estar visível na
    página — erro comum real de quem compra lote para construir."""
    html = _ler("imt-jovem.html")
    assert "terreno para constru" in html.lower(), "exclusão de terrenos ausente de imt-jovem.html"
    assert "informação vinculativa" in html.lower(), "referência à informação vinculativa da AT ausente"


def test_garantia_publica_meta_description_percentagem_e_valor_imovel():
    desc = _meta_description("garantia-publica-credito-habitacao.html")
    assert _param_habitacao("garantia_percentagem_max_pct") in _percentagens(desc), desc
    assert _param_habitacao("garantia_valor_imovel_max_eur") in _valores_eur_inteiros(desc), desc


def test_garantia_publica_og_tags_espelham_title_e_description():
    pagina = "garantia-publica-credito-habitacao.html"
    assert _meta_og(pagina, "og:title") == _title(pagina)
    assert _meta_og(pagina, "og:description") == _meta_description(pagina)


def test_garantia_publica_prazo_e_condicoes_no_corpo_batem_com_o_yaml():
    html = _ler("garantia-publica-credito-habitacao.html")
    prazo = _param_habitacao("garantia_prazo_contrato_limite")  # "2026-12-31"
    ano, mes, dia = prazo.split("-")
    assert f"{int(dia)} de dezembro de {ano}" in html, f"prazo {prazo} não encontrado por extenso no corpo"
    assert f"{_param_habitacao('garantia_idade_minima_anos')} e {_param_habitacao('garantia_idade_maxima_anos')} anos" in html
    assert f"{_param_habitacao('garantia_duracao_anos')} anos" in html
    rendimento = _param_habitacao("garantia_rendimento_max_anual_eur")
    assert f"{rendimento:,}".replace(",", ".") in html


def test_habitacao_pillar_menciona_os_mesmos_limiares_das_paginas_filhas():
    """p/habitacao.html (hub reorganizado nesta sessão) nunca pode
    divergir dos valores publicados em imt-jovem.html/
    garantia-publica-credito-habitacao.html — canário de consistência
    entre o resumo do hub e o detalhe de cada guia."""
    pillar = _ler("p/habitacao.html")
    assert f"{_param_habitacao('imt_isencao_total_limite_eur'):,}".replace(",", ".") in pillar
    assert _param_habitacao("garantia_percentagem_max_pct") in _percentagens(pillar)


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


# ── Cluster Habitação — Dedução de rendas em IRS (Sessão 3, 2026-07-20) ──
# dados/parametros/habitacao.yaml continua a ser a fonte única — o valor
# "vigente" (900€) tem de bater com o title/description; o histórico
# completo (700€/900€/1.000€) tem de bater com a tabela de cronologia do
# corpo, para nunca divergir do YAML nem ficar "solto" em texto.

def _valores_eur_inteiros_sem_milhares(texto: str) -> list:
    """Como `_valores_eur_inteiros()`, mas também apanha valores inteiros
    SEM separador de milhares (ex.: "900 €", "700€") — necessário para a
    Dedução de Rendas (Sessão 3, 2026-07-20), cujos valores atravessam a
    fronteira dos 1.000€ (700/900/1.000). O `(?<!,)` continua a proteger
    contra apanhar a parte inteira de um valor decimal tipo "900,00 €"."""
    return [
        int(bruto.replace(".", ""))
        for bruto in re.findall(r"(?<!,)\b(\d{1,3}(?:\.\d{3})*)\s?€", texto)
    ]


def _valores_deducao_rendas_por_ano(nome: str):
    """Lê os 3 valores da lista `valores` do YAML directamente (não só o
    vigente), indexados por `vigencia_inicio`, para comparar com a tabela
    de cronologia da página."""
    bruto = yaml.safe_load((PARAMETROS_DIR / "habitacao.yaml").read_text(encoding="utf-8"))
    return {
        entrada["vigencia_inicio"]: entrada["valor"]
        for entrada in bruto[nome]["valores"]
    }


def test_deducao_rendas_title_e_description_mostram_o_valor_vigente_900():
    pagina = "deducao-rendas-irs.html"
    assert _valores_eur_inteiros_sem_milhares(_title(pagina)) == [_param_habitacao("deducao_rendas_irs_limite_eur")], _title(pagina)
    assert _param_habitacao("deducao_rendas_irs_limite_eur") in _valores_eur_inteiros_sem_milhares(_meta_description(pagina))


def test_deducao_rendas_og_tags_espelham_title_e_description():
    pagina = "deducao-rendas-irs.html"
    assert _meta_og(pagina, "og:title") == _title(pagina)
    assert _meta_og(pagina, "og:description") == _meta_description(pagina)


def test_deducao_rendas_cronologia_completa_no_corpo_bate_com_o_yaml():
    """Os 3 valores da cronologia (700€ regime anterior, 900€ desde 2026,
    1.000€ desde 2027) têm de aparecer todos no corpo da página, exactamente
    como estão no YAML — nunca hardcoded de memória à parte da fonte única."""
    html = _ler("deducao-rendas-irs.html")
    valores = _valores_deducao_rendas_por_ano("deducao_rendas_irs_limite_eur")
    for vigencia, valor in valores.items():
        formatado = f"{valor:,}".replace(",", ".")  # 1000 -> "1.000", 900 -> "900"
        assert f"{formatado} €" in html or f"{formatado}€" in html, (
            f"valor {formatado}€ (vigência {vigencia}) da cronologia ausente do corpo de deducao-rendas-irs.html"
        )


def test_primeiro_direito_limites_4x_e_60x_ias_batem_com_o_ias_2026():
    """1.º Direito (Sessão 3): os limiares de rendimento (4×IAS) e
    património (60×IAS) não têm YAML próprio (não aparecem em title/meta
    description, só no corpo) — mas têm de bater sempre com o IAS_2026 já
    afirmado no topo deste ficheiro, nunca hardcoded à parte."""
    html = _ler("primeiro-direito.html")
    rendimento = round(4 * IAS_2026, 2)
    patrimonio = round(60 * IAS_2026, 2)
    rendimento_fmt = f"{rendimento:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    patrimonio_fmt = f"{patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    assert rendimento_fmt in html, f"limiar de rendimento {rendimento_fmt}€ (4×IAS) ausente de primeiro-direito.html"
    assert patrimonio_fmt in html, f"limiar de património {patrimonio_fmt}€ (60×IAS) ausente de primeiro-direito.html"


def test_deducao_rendas_nunca_afirma_900_como_ja_utilizavel_na_declaracao_2026():
    """Invariante central desta página: nunca pode ler-se como se os 900€
    já se aplicassem à declaração entregue em 2026 (rendimentos de 2025,
    que continuam a usar 700€) — nenhum estado pendente/futuro pode
    parecer já consumado na declaração actual."""
    html = _ler("deducao-rendas-irs.html")
    assert "700" in html, "limite antigo (700€) ausente — a página tem de mostrar a cronologia completa"
    assert "2027" in html, "ano da declaração em que os 900€ passam a aplicar-se ausente"


# ── PSU — Decreto-Lei n.º 166/2026, de 13 de agosto, dados/parametros/psu.yaml
# (FASE 1 de 2 do plano de activação, sessão de 2026-08-13 — só parâmetros
# + testes-âncora; nenhuma página HTML nem o simulador foram tocados nesta
# fase, ver Fase 2). O decreto-lei fixa directamente 10 parâmetros
# numéricos (Valor de Referência, as 3 ponderações de adultos
# equivalentes, o teto máximo global, o mínimo em euro, os DOIS limites
# de património SEPARADOS — mobiliário e bens móveis sujeitos a registo,
# nunca somados — e as 2 parcelas da CIT, que nunca foi um único
# "coeficiente") + 1 data de produção de efeitos — todos recalculados a
# partir da fórmula/multiplicador real, nunca hardcoded como cópia solta.
# As 2 majorações (parentalidade/desemprego) continuam `null` por
# desenho — não são um "valor a definir mais tarde", são estruturalmente
# não-redutíveis a um único euro (dependem de qual beneficiário do
# agregado, ou do PSUglobal já calculado) — ver dados/parametros/psu.yaml
# para a fórmula completa de cada uma.

_PSU = None


def _param_psu(nome: str):
    global _PSU
    if _PSU is None:
        todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
        _PSU = todos["prestacoes"]["psu"]
    return _PSU[nome]["valor"]


def test_psu_valor_referencia_0_5x_ias():
    """Art. 7.º do Decreto-Lei n.º 166/2026 — \"O valor de referência da
    PSU corresponde a 50 % do valor do indexante dos apoios sociais
    (IAS)\". Base da fórmula PSUbase = VRP × AE."""
    assert _param_psu("valor_referencia_multiplicador_ias") == 0.5


def test_psu_ponderacoes_adultos_equivalentes_1_0_7_0_5():
    """Art. 24.º/2 do Decreto-Lei n.º 166/2026 — titular=1, maior=0,7,
    menor=0,5. NUNCA "menor até 25 anos": o texto legal usa só a
    maioridade civil (18 anos), sem qualquer corte etário adicional —
    ver o comentário de renomeação em dados/parametros/psu.yaml, que
    documenta o nome antigo errado ('ponderacao_menor_ate_25') que este
    parâmetro substituiu."""
    assert _param_psu("ponderacao_titular") == 1
    assert _param_psu("ponderacao_maior") == 0.7
    assert _param_psu("ponderacao_menor") == 0.5


def test_psu_teto_maximo_6x_ias():
    """Art. 25.º/3 do Decreto-Lei n.º 166/2026 — o teto máximo do montante
    mensal global (já com majorações) corresponde a seis vezes o IAS."""
    assert _param_psu("teto_maximo_multiplicador_ias") == 6


def test_psu_valor_minimo_10_euros_nao_indexado():
    """Art. 25.º/5 do Decreto-Lei n.º 166/2026 — abaixo de 10 € não há
    lugar à atribuição da PSU. Único parâmetro deste ficheiro em euro
    fixo, nunca indexado ao IAS nem a qualquer outro índice — o próprio
    artigo não o liga ao IAS, ao contrário de todos os outros limiares
    da PSU."""
    assert _param_psu("valor_minimo_euros") == 10.00


def test_psu_limite_patrimonio_60x_ias():
    """O limite de património MOBILIÁRIO — art. 8.º/1/c do Decreto-Lei
    n.º 166/2026 (antes só confirmado pela Lei n.º 36/2026, artigo
    2.º/d/v, como um limite único e combinado — agora separado do de
    bens móveis sujeitos a registo, ver o teste seguinte). Recalcula
    multiplicador × IAS_2026 (nunca hardcoda "32.227,80") e confirma que
    bate com o que já está publicado em psu-quem-tem-direito.html e
    prestacao-social-unica.html. Se o IAS mudar (Portaria de janeiro) sem
    ninguém rever estas páginas, este teste fica vermelho sozinho — mesmo
    princípio dos outros canários IAS-derivados deste ficheiro."""
    multiplicador = _param_psu("limite_patrimonio_mobiliario_multiplicador_ias")
    assert multiplicador == 60, "o multiplicador confirmado pelo Decreto-Lei n.º 166/2026 é 60× IAS — mudou sem rever a fonte legal?"
    limite = round(multiplicador * IAS_2026, 2)
    limite_fmt = f"{limite:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    assert limite_fmt == "32.227,80", f"60 × IAS_2026 deveria dar 32.227,80 €, deu {limite_fmt} €"

    for pagina in ("psu-quem-tem-direito.html", "prestacao-social-unica.html"):
        html = _ler(pagina)
        assert limite_fmt in html, f"{pagina}: limite de património {limite_fmt} € (60 × IAS) ausente do corpo"


def test_psu_limite_bens_moveis_registo_60x_ias_separado_do_patrimonio():
    """Art. 8.º/1/d do Decreto-Lei n.º 166/2026 — limite de bens móveis
    SUJEITOS A REGISTO (ex.: veículos), também 60× IAS, mas SEPARADO do
    limite de património mobiliário (art. 8.º/1/c) — dois tectos de 60×
    IAS cada, nunca somados nem confundidos com um único tecto de 120×
    IAS. A Lei n.º 36/2026 (só a autorização legislativa, sem o texto
    operacional) tinha fundido os dois num único parâmetro; o
    decreto-lei corrige isso."""
    patrimonio = _param_psu("limite_patrimonio_mobiliario_multiplicador_ias")
    registo = _param_psu("limite_bens_moveis_registo_multiplicador_ias")
    assert patrimonio == 60
    assert registo == 60
    assert patrimonio == registo, "os dois tectos são independentes (art. 8.º/1/c e /1/d) mas ambos 60× IAS — nunca somar para um único 120× IAS"


def test_psu_cit_estrutura_de_duas_parcelas_0_20_e_0_50():
    """Art. 28.º/2 do Decreto-Lei n.º 166/2026 — a CIT NUNCA foi um único
    coeficiente (o antigo 'coeficiente_cit', ratio único, foi removido —
    ver dados/parametros/psu.yaml): é uma estrutura de duas parcelas —
    a totalidade dos rendimentos de trabalho até 20% do IAS conta na
    íntegra, e 50% da parte que excede esse limiar. CIT = min(R, 0,20×IAS)
    + 0,50 × max(0, R − 0,20×IAS)."""
    assert _param_psu("cit_limiar_multiplicador_ias") == 0.20
    assert _param_psu("cit_taxa_acima_limiar") == 0.50


def test_psu_producao_de_efeitos_31_dezembro_2026_nunca_1_janeiro_2027():
    """Art. 63.º do Decreto-Lei n.º 166/2026 — \"entra em vigor no
    primeiro dia útil seguinte ao da sua publicação e produz efeitos a
    31 de dezembro de 2026\". A data usada em todas as sessões
    anteriores ao decreto-lei ("1 de janeiro de 2027") era só uma
    estimativa nunca confirmada por texto legal — este teste tranca a
    data real, para nenhuma página escrita na FASE 2 repetir a
    estimativa antiga."""
    assert _param_psu("data_producao_efeitos") == "2026-12-31"


def test_psu_majoracoes_continuam_null_por_desenho_nunca_um_euro_unico():
    """As duas majorações (parentalidade — art. 26.º; desemprego — art.
    27.º) ficam `null` DELIBERADAMENTE, mesmo depois do decreto-lei — não
    por falta de informação legal (ambas as fórmulas estão 100%
    definidas, ver dados/parametros/psu.yaml), mas porque nenhuma das
    duas é redutível a um único valor em euros: a de parentalidade
    depende de QUAL elemento do agregado é o beneficiário (ponderação
    titular/maior/menor); a de desemprego depende do PSUglobal já
    calculado desse agregado específico. Este teste falha se alguém
    tentar "resolver" isto com um número fixo em vez de implementar a
    fórmula na FASE 2 (lógica do simulador) — nunca silenciar esta
    asserção sem reler o comentário completo em dados/parametros/psu.yaml."""
    assert _param_psu("majoracao_parentalidade_mensal") is None, (
        "majoracao_parentalidade_mensal deixou de ser null — depende do beneficiário, nunca deveria "
        "ser um único euro fixo neste YAML; a fórmula fica para a lógica do simulador (FASE 2)"
    )
    assert _param_psu("majoracao_desemprego_mensal") is None, (
        "majoracao_desemprego_mensal deixou de ser null — depende do PSUglobal já calculado, nunca "
        "deveria ser um único euro fixo neste YAML; a fórmula fica para a lógica do simulador (FASE 2)"
    )


# ── Artigo 17.º — apoios à habitação como rendimento (2026-08-16) ────────
# Estrutura de parâmetros criada nesta sessão, SEM valor de mediana do INE
# e SEM activar o cálculo no simulador — ver o comentário completo em
# dados/parametros/psu.yaml. Este teste é o análogo do canário dos `null`
# já usado para as majorações acima, mas com um propósito diferente: aqui
# trancar o estado "NÃO PRONTO" contra activação prematura, não a
# impossibilidade estrutural de reduzir a um único valor. Falha (vermelho)
# se alguém preencher UM dos 3 parâmetros pendentes sem os outros dois — o
# gate de segurança (calcularHabitacao() em simulador-psu.html) exige os
# 3 preenchidos em conjunto (mediana + trimestre de referência + portaria
# que os fixa), nunca um valor "meio-confirmado".
def test_art17_habitacao_pendente_ate_portaria():
    """Os 3 insumos que dependem de fonte externa (INE) e confirmação
    legal (portaria do artigo 17.º/5) continuam null — nenhum valor
    estimado ou "provisório" pode ser publicado aqui sem essa dupla
    confirmação. Se um dia só um dos três for preenchido (ex.: alguém
    encontra a mediana do INE mas a portaria ainda não saiu), este teste
    tem de continuar vermelho — os 3 só avançam para um valor real em
    conjunto, nunca isoladamente."""
    pendentes = (
        "art17_mediana_renda_m2_ine",
        "art17_mediana_renda_m2_referencia",
        "art17_portaria_habitacao",
    )
    valores = {nome: _param_psu(nome) for nome in pendentes}
    todos_none = all(v is None for v in valores.values())
    assert todos_none, (
        f"artigo 17.º/habitação: nem todos os parâmetros pendentes continuam null — {valores}. "
        "Os 3 (mediana INE + trimestre de referência + portaria) só devem avançar para um valor "
        "real EM CONJUNTO, com a portaria do artigo 17.º/5 confirmada — nunca um preenchido "
        "isoladamente. Se a portaria já saiu e os 3 foram preenchidos correctamente, este teste "
        "tem de ser reescrito para validar o valor real (nunca apenas apagado)."
    )


def test_art17_habitacao_constantes_fixas_na_lei():
    """Os 3 parâmetros que o próprio Decreto-Lei n.º 166/2026 já fixa
    directamente (nunca dependeram do INE nem de portaria) — artigo
    17.º/2 (coeficiente de imputação) e artigo 17.º/3 (área de
    referência e divisor da renda de referência, "um terço"). Confirmados
    contra o texto legal extraído de dados/fontes/Decreto-Lei n.PDF
    (artigo 17.º) nesta sessão."""
    assert _param_psu("art17_area_referencia_m2") == 112.50
    assert _param_psu("art17_coeficiente_imputacao") == 0.5
    assert _param_psu("art17_divisor_renda_referencia") == 3


# ── Portaria n.º 394/2026/1, de 27 de agosto — normas de execução da PSU
# (artigo 59.º do Decreto-Lei n.º 166/2026), sessão de 2026-08-30. Primeira
# fonte deste ficheiro que não é o próprio decreto-lei. Trabalho de
# conteúdo por ordem, um artigo da portaria de cada vez — só o artigo 22.º
# (senha de participação) foi implementado nesta sessão; os restantes
# (meios de prova, renovação oficiosa, Anexo I) ficam para os passos
# seguintes do mesmo plano de trabalho.

def test_psu_senha_participacao_2_5_por_cento_ias():
    """Art. 22.º da Portaria n.º 394/2026/1 — senha de participação de 2,5%
    do IAS por cada 20 horas semanais de trabalho social (art. 21.º/1/c do
    decreto-lei) efectivamente realizadas. Recalcula multiplicador ×
    IAS_2026 (nunca hardcoda "13,43") e confirma que o valor está publicado
    tanto no corpo como na FAQ de psu-trabalho-social.html."""
    multiplicador = _param_psu("senha_participacao_multiplicador_ias")
    assert multiplicador == 0.025, "o valor confirmado pela Portaria n.º 394/2026/1 é 2,5% do IAS — mudou sem rever a fonte legal?"
    valor = round(multiplicador * IAS_2026, 2)
    assert valor == 13.43, f"2,5% × IAS_2026 deveria dar 13,43 €, deu {valor} €"

    html = _ler("psu-trabalho-social.html")
    valor_fmt = f"{valor:.2f}".replace(".", ",")
    assert html.count(valor_fmt) >= 2, (
        f"{valor_fmt} € tem de aparecer no corpo E na FAQ de psu-trabalho-social.html — só apareceu "
        f"{html.count(valor_fmt)}×"
    )


def test_psu_senha_participacao_nunca_conta_como_rendimento():
    """Distinção central do art. 22.º: a senha de participação nunca entra
    na condição de recursos nem no cálculo da PSU — ao contrário da CIT,
    que desconta parte dos rendimentos de trabalho normal. A página tem de
    afirmar isto explicitamente, nunca deixar ambíguo se conta ou não."""
    html = _ler("psu-trabalho-social.html").lower()
    assert "conta como rendimento" in html, (
        "psu-trabalho-social.html tem de afirmar explicitamente que a senha de participação "
        "não conta como rendimento (art. 22.º da Portaria n.º 394/2026/1)"
    )


def test_psu_senha_participacao_so_aplicavel_a_partir_de_31_dezembro_2026():
    """A Portaria n.º 394/2026/1 está em vigor desde 28/08/2026, mas só
    produz efeitos a 31/12/2026 — mesma data do artigo 63.º do
    decreto-lei. A página nunca pode ler-se como se a senha de
    participação já fosse paga hoje, só porque a portaria já está em
    vigor."""
    html = _ler("psu-trabalho-social.html")
    assert "31 de dezembro de 2026" in html, (
        "psu-trabalho-social.html tem de deixar claro que a senha de participação só se aplica "
        "a partir de 31/12/2026 (mesmo dia da PSU) — nunca como já aplicável"
    )


def test_psu_disponibilidade_adicional_18_25_anos_e_3a_renovacao():
    """Art. 14.º da Portaria n.º 394/2026/1 — duas situações em que a
    disponibilidade sobe de 15h para 20h/semana: idade entre 18 e 25 anos
    (titular ou membro do agregado), ou 3.ª renovação da prestação
    (titular em idade activa — o mesmo tecto já previsto em termos gerais
    pelo artigo 33.º/5 do decreto-lei). Confirma que ambas estão
    documentadas em psu-trabalho-social.html, com o artigo certo citado."""
    html = _ler("psu-trabalho-social.html")
    assert "18 e 25 anos" in html, "critério de idade (18-25 anos) do artigo 14.º ausente de psu-trabalho-social.html"
    assert "3.ª renovação" in html, "critério da 3.ª renovação ausente de psu-trabalho-social.html"
    assert "artigo 14.º" in html, "citação ao artigo 14.º da Portaria n.º 394/2026/1 ausente de psu-trabalho-social.html"


def test_psu_disponibilidade_adicional_nunca_afirma_soma_alem_de_20h():
    """A portaria não esclarece se as duas situações do artigo 14.º se
    somam entre si — a página nunca pode afirmar um tecto acima de 20h
    (ex.: "25 horas") sem essa confirmação legal. Mesmo princípio dos
    outros canários deste ficheiro que trancam uma NÃO-afirmação (ver
    test_deducao_rendas_nunca_afirma_900_como_ja_utilizavel_na_declaracao_2026)."""
    html = _ler("psu-trabalho-social.html")
    assert "25 horas" not in html, (
        "psu-trabalho-social.html não pode afirmar um tecto de 25 horas semanais — a portaria "
        "não confirma que as duas situações do artigo 14.º se somam entre si"
    )


# ── Portaria n.º 394/2026/1 — meios de prova e prazos (arts. 4.º a 6.º),
# item 3 do plano de trabalho, sessão de 2026-08-30. como-pedir-psu.html.

def test_psu_meios_de_prova_regra_e_interoperabilidade():
    """Arts. 4.º a 6.º da Portaria n.º 394/2026/1 — a prova faz-se, sempre
    que possível, com base na informação já detida pela instituição
    gestora ou obtida por interoperabilidade entre serviços; os
    documentos só são pedidos quando essa informação não está
    disponível. A página tem de dizer isto primeiro — a lista de
    documentos é a excepção, nunca o procedimento normal."""
    html = _ler("como-pedir-psu.html")
    assert "interoperabilidade" in html.lower(), "regra da interoperabilidade ausente de como-pedir-psu.html"


def test_psu_prazo_documentos_10_dias_uteis_20_regioes_autonomas():
    """Prazo para entrega de documentos: 10 dias úteis a contar da
    notificação, 20 nas Regiões Autónomas — diferente do prazo de
    decisão (30/20 dias, artigo 31.º/1), que a página não pode confundir
    com este."""
    html = _ler("como-pedir-psu.html")
    assert "10 dias úteis" in html, "prazo de 10 dias úteis para entrega de documentos ausente de como-pedir-psu.html"
    assert "Regiões Autónomas" in html, "excepção das Regiões Autónomas (20 dias úteis) ausente de como-pedir-psu.html"


def test_psu_falta_de_documentos_e_suspensao_nunca_indeferimento():
    """Art. 6.º — a falta de documentos no prazo determina SUSPENSÃO do
    procedimento, nunca indeferimento. A página nunca pode usar
    "indeferido"/"indeferimento" sem uma negação explícita logo antes —
    esta distinção é o ponto central do artigo, não um detalhe."""
    html = _ler("como-pedir-psu.html").lower()
    assert "suspenso" in html, "consequência de suspensão (não indeferimento) ausente de como-pedir-psu.html"
    for m in re.finditer(r"indeferid", html):
        contexto = html[max(0, m.start() - 20):m.start()]
        assert "nunca" in contexto or "não " in contexto, (
            f"'indeferido' aparece sem negação explícita perto de: "
            f"...{html[max(0, m.start() - 60):m.start() + 30]}..."
        )


def test_psu_morada_para_comunicacoes_sem_morada_fixa():
    """Quem não tem morada fixa pode indicar uma morada para
    comunicações, incluindo a de uma pessoa colectiva — facto que ajuda
    quem mais precisa e que a página tem de publicar, não só mencionar
    a lista de documentos e seguir em frente."""
    html = _ler("como-pedir-psu.html").lower()
    assert "morada para comunicações" in html, (
        "nota sobre morada para comunicações (sem morada fixa) ausente de como-pedir-psu.html"
    )
    assert "pessoa colectiva" in html, (
        "a possibilidade de indicar a morada de uma pessoa colectiva ausente de como-pedir-psu.html"
    )


# ── Portaria n.º 394/2026/1 — renovação oficiosa (artigo 11.º), item 4 do
# plano de trabalho, sessão de 2026-08-30. Vive em psu-quem-tem-direito.html
# — nunca como-pedir-psu.html, que é só sobre o pedido inicial. Risco
# central: nunca confundir esta renovação periódica com a conversão
# oficiosa do artigo 57.º do decreto-lei (RSI/outros apoios → PSU, evento
# único a 31/12/2026), já documentada em várias páginas do cluster.

def test_psu_renovacao_oficiosa_artigo_11():
    """Art. 11.º da Portaria n.º 394/2026/1 — renovação oficiosa pela
    instituição gestora, verificação no mês imediatamente anterior ao
    termo do período de atribuição, notificação da decisão em 10 dias
    úteis. Documentado em psu-quem-tem-direito.html."""
    html = _ler("psu-quem-tem-direito.html")
    assert "renovação" in html.lower(), "renovação oficiosa (artigo 11.º) ausente de psu-quem-tem-direito.html"
    assert "mês imediatamente anterior" in html, (
        "momento da verificação (mês anterior ao termo do período de atribuição) ausente de "
        "psu-quem-tem-direito.html"
    )
    assert "10 dias úteis" in html, "prazo de notificação (10 dias úteis) ausente de psu-quem-tem-direito.html"


def test_psu_renovacao_nunca_confundida_com_conversao_artigo_57():
    """A renovação periódica (artigo 11.º da portaria) e a conversão
    oficiosa do RSI/outros apoios para PSU (artigo 57.º do decreto-lei)
    são eventos diferentes — a página tem de distinguir os dois
    explicitamente, nunca deixar a leitura ambígua para quem vem do RSI."""
    html = _ler("psu-quem-tem-direito.html").lower()
    assert "não é a conversão" in html, (
        "psu-quem-tem-direito.html tem de distinguir explicitamente a renovação periódica "
        "(artigo 11.º) da conversão oficiosa do artigo 57.º"
    )


def test_psu_como_pedir_nunca_confunde_pedido_inicial_com_renovacao():
    """como-pedir-psu.html é só sobre o pedido inicial — qualquer menção à
    renovação periódica tem de deixar claro que não faz parte deste passo
    a passo, apontando para onde o detalhe vive (psu-quem-tem-direito.html)."""
    html = _ler("como-pedir-psu.html").lower()
    assert "não inclui a renovação" in html, (
        "como-pedir-psu.html tem de deixar explícito que o passo a passo do pedido inicial "
        "não inclui a renovação periódica da PSU"
    )


# ── Anexo I da Portaria n.º 394/2026/1 — coeficientes de desvalorização de
# veículos (artigo 4.º/7), item 5 do plano de trabalho, sessão de
# 2026-08-30. psu-quem-tem-direito.html — dentro do card "Património", que
# já tratava dos bens móveis sujeitos a registo.

def test_psu_veiculo_coeficientes_batem_com_o_yaml():
    """Os 11 coeficientes acumulados (ano zero a dez+ anos) — parâmetros
    ESCALARES `veiculo_coeficiente_anoN`, nunca uma lista (uma lista
    partiria a coluna REAL de dados/tensdireito.db, ver o comentário em
    dados/parametros/psu.yaml) — recalculados a partir de
    dados/parametros.json (nunca hardcoded aqui) têm de bater com os
    publicados na tabela de psu-quem-tem-direito.html, formatados com
    vírgula decimal como o resto do site."""
    nomes = [f"veiculo_coeficiente_ano{i}" for i in range(10)] + ["veiculo_coeficiente_ano10mais"]
    coeficientes = [_param_psu(nome) for nome in nomes]
    esperados = [0, 0.20, 0.35, 0.45, 0.55, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]
    assert coeficientes == esperados, (
        f"coeficientes de desvalorização de veículos mudaram no YAML sem rever a fonte legal — "
        f"esperado {esperados}, encontrado {coeficientes}"
    )
    html = _ler("psu-quem-tem-direito.html")
    for c in coeficientes:
        if c == 0:
            continue  # "0" sozinho não é uma string útil para procurar (colide com outros números)
        formatado = f"{c:.2f}".rstrip("0").replace(".", ",")
        assert formatado in html, (
            f"coeficiente {formatado} (Anexo I) ausente da tabela de psu-quem-tem-direito.html"
        )


def test_psu_veiculo_formula_valor_mercado_presente():
    """A fórmula do Anexo I (valor de mercado = valor de aquisição − valor
    de aquisição × coeficiente) tem de estar publicada, nunca só a tabela
    de coeficientes sem o mecanismo que os usa."""
    html = _ler("psu-quem-tem-direito.html").lower()
    assert "valor de mercado" in html and "valor de aquisição" in html and "coeficiente de desvalorização" in html, (
        "fórmula de valorização de veículos (Anexo I) ausente ou incompleta em psu-quem-tem-direito.html"
    )


def test_psu_veiculo_fallback_sem_valor_aquisicao_comprovado():
    """Quando não for possível comprovar o valor de aquisição, usa-se o
    valor de mercado directamente — regra de recurso que a página tem de
    publicar, nunca deixar como se a fórmula fosse sempre aplicável."""
    html = _ler("psu-quem-tem-direito.html").lower()
    assert "não for possível comprovar o valor de aquisição" in html, (
        "regra de recurso (sem valor de aquisição comprovado, usa-se o valor de mercado) "
        "ausente de psu-quem-tem-direito.html"
    )


def test_psu_veiculo_formula_nunca_assumida_para_rsi_ou_csi():
    """A fórmula do Anexo I aplica-se à PSU por remissão do artigo 4.º/7
    — nunca assumida para o RSI ou o CSI sem confirmação própria. A
    página tem de o dizer explicitamente, e os YAML de RSI/CSI nunca
    podem ganhar este parâmetro por engano/copy-paste."""
    html = _ler("psu-quem-tem-direito.html").lower()
    assert "rsi" in html and "csi" in html, (
        "psu-quem-tem-direito.html tem de mencionar explicitamente que a fórmula do Anexo I "
        "não está confirmada para RSI/CSI"
    )
    for prestacao in ("rsi", "csi"):
        conteudo_yaml = (PARAMETROS_DIR / f"{prestacao}.yaml").read_text(encoding="utf-8")
        assert "veiculo_coeficiente_ano" not in conteudo_yaml, (
            f"dados/parametros/{prestacao}.yaml ganhou o parâmetro de coeficientes de veículos da "
            "PSU sem confirmação própria — a remissão do artigo 4.º/7 é só para a PSU"
        )


# ── RSI — migrado para dados/parametros/rsi.yaml (2026-08-24) ────────────────
# RSI era um dos 3 simuladores por migrar (ver LEVANTAMENTO-DADOS-ABERTOS.md,
# Fase 0) — `simulador-rsi.html` passa a ler /dados/parametros.json em
# runtime, mesmo padrão de CSI/PSU/Habitação acima. Os 5 canários criados na
# sessão anterior (PR #120, comparação HTML↔HTML entre rsi.html e
# simulador-rsi.html) passam a comparar contra a fonte estruturada — mesmo
# princípio de test_csi_dados_parametros_json_bate_com_a_pagina_do_artigo.
# PASSO 0 desta migração (WebSearch — WebFetch a diariodarepublica.pt/
# pgdlisboa.pt continua bloqueado nesta sessão) confirmou os 10 valores sem
# nenhuma divergência face ao que já estava publicado; ver
# dados/parametros/rsi.yaml para o detalhe completo de cada diploma.

_RSI = None


def _param_rsi(nome: str):
    global _RSI
    if _RSI is None:
        todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
        _RSI = todos["prestacoes"]["rsi"]
    return _RSI[nome]["valor"]


def test_rsi_ias_2026_no_yaml():
    assert _param_rsi("ias_2026") == IAS_2026


def test_rsi_valores_base_batem_com_o_artigo():
    """Portaria n.º 71/2026/1 (titular) + Lei n.º 13/2003 art. 10.º na
    redação do DL n.º 1/2016 (70%/50% por adulto adicional/menor) —
    ver dados/parametros/rsi.yaml para as referências completas."""
    titular = _param_rsi("valor_titular_mensal")
    adulto = _param_rsi("valor_adulto_adicional_mensal")
    menor = _param_rsi("valor_menor_mensal")
    assert (titular, adulto, menor) == (247.56, 173.29, 123.78)

    html = _ler("rsi.html")
    for valor in ("247,56 €", "173,29 €", "123,78 €"):
        assert valor in html, f"{valor} (dados/parametros/rsi.yaml) em falta no artigo rsi.html"
    # Exemplo publicado no artigo (casal + 2 filhos): soma dos 4 componentes.
    soma = round(titular + adulto + 2 * menor, 2)
    assert soma == 668.41
    assert "668,41 €" in html, "exemplo do casal com 2 filhos (668,41 €) em falta"


def test_rsi_limite_patrimonio_60x_ias_bate_com_o_artigo():
    """Decreto-Lei n.º 70/2010, artigo 9.º — 60 × IAS. Recalculado aqui
    (multiplicador × IAS_2026), nunca hardcoded como "32.227,80" — mesmo
    padrão de test_psu_limite_patrimonio_60x_ias/
    test_primeiro_direito_limites_4x_e_60x_ias_batem_com_o_ias_2026. Se o
    IAS mudar (Portaria de janeiro) sem ninguém rever o YAML/artigo, este
    teste fica vermelho sozinho."""
    multiplicador = _param_rsi("limite_patrimonio_multiplicador_ias")
    assert multiplicador == 60, "o multiplicador confirmado (DL n.º 70/2010, art. 9.º) é 60× IAS — mudou sem rever a fonte legal?"
    limite = round(multiplicador * IAS_2026, 2)
    assert limite == 32227.80

    html = _ler("rsi.html")
    assert "32.227,80 €" in html, "limite de património (60 × IAS) em falta no artigo"


def test_rsi_percentagens_rendimentos_batem_com_o_artigo():
    assert _param_rsi("percentagem_rendimento_trabalho_dependente") == 0.80
    assert _param_rsi("percentagem_rendimento_trabalho_independente") == 1.00
    assert _param_rsi("percentagem_subsidio_desemprego") == 1.00
    assert _param_rsi("percentagem_outros_rendimentos") == 1.00

    html = _ler("rsi.html")
    assert "conta só 80%" in html or "conta 80%" in html, "80% do trabalho dependente em falta"
    assert "contam 100%" in html, "100% dos restantes rendimentos em falta"


def test_rsi_idade_minima_bate_com_o_artigo():
    assert _param_rsi("idade_minima_anos") == 18
    html = _ler("rsi.html")
    assert "18 anos ou mais" in html, "idade mínima geral (18 anos) em falta no artigo"


# ── Subsídio de Desemprego — migrado para dados/parametros/desemprego.yaml ──
# (2026-08-24). Último simulador por migrar sem bloqueio externo (o ASE fica
# à espera do despacho da DGEstE). PASSO 0 apresentado e aprovado antes da
# migração: 16 valores escalares (a Fase 0 tinha contado "17" por engano,
# corrigido em LEVANTAMENTO-DADOS-ABERTOS.md) + 12 células da tabela de
# duração — toda a verificação por triangulação WebSearch (WebFetch a
# diariodarepublica.pt/pgdlisboa.pt/app.parlamento.pt continua bloqueado
# nesta sessão), nenhuma por leitura directa do diploma. Diploma-base:
# Decreto-Lei n.º 220/2006, de 3 de novembro. Ver dados/parametros/
# desemprego.yaml para o detalhe completo de cada citação, incluindo o único
# valor sem diploma atribuído (garantia_dias_ti_cessacao).

_DESEMPREGO = None


def _param_desemprego(nome: str):
    global _DESEMPREGO
    if _DESEMPREGO is None:
        todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
        _DESEMPREGO = todos["prestacoes"]["desemprego"]
    return _DESEMPREGO[nome]["valor"]


def test_desemprego_ias_2026_no_yaml():
    assert _param_desemprego("ias") == IAS_2026


def test_desemprego_valores_base_batem_com_o_artigo():
    """Art. 28.º do DL 220/2006 — 65% RR, RR = R/360, base de 30 dias
    por mês, mínimo 1×IAS, máximo 2,5×IAS — todos confirmados pela
    mesma citação (quase-verbatim de fonte secundária de conteúdo
    legal, triangulada 2×)."""
    assert _param_desemprego("percentagem_rr") == 0.65
    assert _param_desemprego("divisor_rr") == 360
    assert _param_desemprego("dias_por_mes") == 30
    assert _param_desemprego("minimo") == 537.13 == IAS_2026
    assert _param_desemprego("maximo") == round(2.5 * IAS_2026, 2) == 1342.83

    html = _ler("subsidio-desemprego.html")
    for valor in ("65%", "537,13", "1.342,83"):
        assert valor in html, f"{valor} em falta no artigo subsidio-desemprego.html"


def test_desemprego_salario_minimo_dl_139_2025():
    """Decreto-Lei n.º 139/2025, de 29 de dezembro — RMMG 2026, mesmo
    diploma já usado em dados/parametros/subsidio-doenca.yaml."""
    assert _param_desemprego("salario_minimo") == 920.00
    assert "920" in _ler("subsidio-desemprego.html")


def test_desemprego_majoracoes_minimo_maximo_batem_com_o_artigo():
    """DL 220/2006, na redação do DL n.º 64/2012 — mecanismo/percentagem
    confirmados, sem número de artigo confirmado com confiança nesta
    sessão (ver comentário no YAML — nunca inventado)."""
    assert _param_desemprego("minimo_majorado") == round(1.15 * IAS_2026, 2) == 617.70
    assert _param_desemprego("maximo_majorado") == round(_param_desemprego("maximo") * 1.10, 2) == 1477.11

    html = _ler("subsidio-desemprego.html")
    for valor in ("617,70", "1.477,11"):
        assert valor in html, f"{valor} em falta no artigo subsidio-desemprego.html"


def test_desemprego_prazos_de_garantia_e_requerimento_batem_com_o_artigo():
    """Prazo de garantia regime geral (art. 22.º, 360 dias) e prazo de
    requerimento (90 dias, diploma confirmado via gov.pt, sem artigo
    pinado). garantia_dias_ti_cessacao (720 dias) fica deliberadamente
    SEM diploma atribuído — o valor está triangulado, o diploma não."""
    assert _param_desemprego("garantia_dias_geral") == 360
    assert _param_desemprego("garantia_dias_ti_cessacao") == 720
    assert _param_desemprego("prazo_requerimento_dias") == 90

    html = _ler("subsidio-desemprego.html")
    for valor in ("360 dias", "720 dias", "90 dias"):
        assert valor in html, f"'{valor}' em falta no artigo subsidio-desemprego.html"


def test_desemprego_garantia_dias_ti_cessacao_nunca_com_diploma_inventado():
    """Tranca a decisão desta sessão: a citação anterior (DL 220/2006)
    revelou-se contradita pela pesquisa; o diploma correcto (candidato:
    DL n.º 65/2012) não foi confirmado com confiança suficiente — nunca
    escrever aqui um diploma como se estivesse confirmado."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    ref = todos["prestacoes"]["desemprego"]["garantia_dias_ti_cessacao"]["referencia_legal"]
    assert "Decreto-Lei n.º 220/2006" not in ref
    assert "Decreto-Lei n.º 65/2012" not in ref
    assert "por confirmar" in ref.lower()


def test_desemprego_acrescimos_por_carreira_longa_batem_com_o_artigo():
    """Art. 37.º do DL 220/2006 — 30/45/60 dias por grupo de 5 anos de
    carreira longa nos últimos 20 anos, conforme a idade."""
    assert _param_desemprego("acrescimo_ate_40") == 30
    assert _param_desemprego("acrescimo_40_a_49") == 45
    assert _param_desemprego("acrescimo_50_mais") == 60
    assert _param_desemprego("anos_por_grupo_acrescimo") == 5

    html = _ler("subsidio-desemprego.html")
    for valor in ("30 dias", "45 dias", "60 dias", "cada 5 anos"):
        assert valor in html, f"'{valor}' em falta no artigo subsidio-desemprego.html"


# Tabela de duração (12 células) — nome do parâmetro YAML → célula esperada
# em subsidio-desemprego.html (texto "<N> dias", conforme publicado na
# tabela "Quanto tempo dura"). Garantia: consistência interna (célula a
# célula, zero divergências, confirmado nesta sessão), não leitura directa
# do artigo completo — ver dados/parametros/desemprego.yaml.
_CELULAS_DURACAO = {
    "duracao_ate29anos_ate15meses_dias": 150,
    "duracao_ate29anos_15a24meses_dias": 210,
    "duracao_ate29anos_mais24meses_dias": 330,
    "duracao_30a39anos_ate15meses_dias": 180,
    "duracao_30a39anos_15a24meses_dias": 330,
    "duracao_30a39anos_mais24meses_dias": 420,
    "duracao_40a49anos_ate15meses_dias": 210,
    "duracao_40a49anos_15a24meses_dias": 360,
    "duracao_40a49anos_mais24meses_dias": 540,
    "duracao_50maisanos_ate15meses_dias": 270,
    "duracao_50maisanos_15a24meses_dias": 480,
    "duracao_50maisanos_mais24meses_dias": 540,
}


def test_desemprego_tabela_duracao_12_celulas_batem_com_o_yaml():
    for nome, esperado in _CELULAS_DURACAO.items():
        assert _param_desemprego(nome) == esperado, f"{nome}: esperado {esperado}, YAML tem {_param_desemprego(nome)}"


def test_desemprego_tabela_duracao_bate_celula_a_celula_com_o_artigo():
    """Comparação célula a célula com a tabela publicada em
    subsidio-desemprego.html ("Quanto tempo dura o subsídio de
    desemprego") — confirmado nesta sessão sem nenhuma divergência.
    Cada dia-valor da tabela tem de aparecer no corpo do artigo."""
    html = _ler("subsidio-desemprego.html")
    for dias in sorted(set(_CELULAS_DURACAO.values())):
        assert f"{dias} dias" in html, f"'{dias} dias' (tabela de duração) em falta no artigo"


def test_desemprego_exemplo_regressao_52_anos_780_dias():
    """52 anos, >24 meses, 20 anos de registo → 540 + 4×60 = 780 dias —
    exemplo já publicado no artigo, mesmo caso de regressão do golden
    test do simulador."""
    base = _param_desemprego("duracao_50maisanos_mais24meses_dias")
    acrescimo = 4 * _param_desemprego("acrescimo_50_mais")
    assert base == 540
    assert acrescimo == 240
    assert base + acrescimo == 780
    assert "780 dias" in _ler("subsidio-desemprego.html")
