r"""Issue #114 (`dre_habitacao_paer`, 2026-08-20) — fechada sem impacto no
PAER (a mudança real era um Regulamento da Série II, que não pode revogar
nem alterar o programa; só um Decreto-Lei o faria, e o sentinela específico
`dre_habitacao_paer_decreto_detectado` correctamente não disparou). Mas o
diagnóstico expôs uma lacuna genuína nas issues "Mudança detectada" do
`pipeline-diario.yml`: o corpo nunca dizia O QUE mudou (só "algo mudou,
vai verificar"), e a "Fonte" citada era sempre o URL genérico do mapa
`fontes` do Step 2 — para as fontes DRE de pesquisa interactiva
(`dre_habitacao_paer`, `dre_habitacao_garantia`, `dre_psu`,
`dre_psu_regulamentacao`, `dre_ias`) esse mapa aponta sempre para a página
de entrada (`/dr/home`), nunca para a página real de resultados
(`/dr/pesquisa`) onde a mudança de facto aconteceu.

Corrigido em dois sítios do mesmo workflow:

1. Step "Detectar mudanças e registar" — quando o hash muda, calcula o
   diff de `conteudo_extraido.itens_lista` entre a baseline e hoje (itens
   novos/removidos, capados a 10 de cada lado) e o URL real do scrape
   (`new_data.url`, com fallback ao mapa genérico só se o campo faltar) —
   ambos gravados em `data/mudancas.json`.
2. Step "Abrir Issues se mudanças detectadas" — usa esses dois campos: o
   corpo da issue ganha uma secção "### O que mudou" só quando há itens
   adicionados e/ou removidos (nunca uma secção vazia a fingir
   informação que não existe), e a linha "Fonte:" passa a citar o URL
   real em vez do genérico.

Mesmo padrão de regressão de `tests/test_deteccao_mudancas_step2.py`:
carrega o YAML real do workflow (nunca uma cópia), faz asserções
estáticas sobre o script de cada step, e replica a lógica central em
Python puro (sem precisar de Node) sobre os dados REAIS desta sessão —
o diff genuíno entre `data/scraped/dre_habitacao_paer_2026-08-19.json` e
`dre_habitacao_paer_2026-08-20.json` (Regulamento n.º 1124-A/2026 a
entrar, Regulamento n.º 1088/2025 a sair da lista de 19)."""
import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/pipeline-diario.yml"
NOME_STEP_DETECTAR = "Detectar mudanças e registar"
NOME_STEP_ISSUES = "Abrir Issues se mudanças detectadas"


def _carregar_script(nome_step: str) -> str:
    dados = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for step in dados["jobs"]["pipeline"]["steps"]:
        if step.get("name") == nome_step:
            script = step.get("with", {}).get("script")
            assert script, f"Step '{nome_step}' não tem 'with.script'"
            return script
    raise AssertionError(f"Step '{nome_step}' não encontrado em {WORKFLOW_PATH}")


# ── Réplica pura em Python da lógica de diff (Step "Detectar mudanças") ────

def _diff_itens_lista(new_data: dict, old_data: dict, limite: int = 10) -> tuple[list, list]:
    """Réplica exacta (mesma semântica, mesmo cap) do JS do Step 2."""
    itens_novos = ((new_data.get("conteudo_extraido") or {}).get("itens_lista")) or []
    itens_antigos = ((old_data.get("conteudo_extraido") or {}).get("itens_lista")) or []
    set_antigos = set(itens_antigos)
    set_novos = set(itens_novos)
    adicionados = [i for i in itens_novos if i not in set_antigos][:limite]
    removidos = [i for i in itens_antigos if i not in set_novos][:limite]
    return adicionados, removidos


def _url_real(new_data: dict, url_generico: str) -> str:
    return new_data.get("url") or url_generico


# ── Réplica pura em Python da construção do corpo da issue ─────────────────

def _construir_corpo_issue(slug: str, url: str, hoje: str, hora: str,
                            itens_adicionados: list, itens_removidos: list) -> str:
    linhas_diff: list[str] = []
    if itens_adicionados or itens_removidos:
        linhas_diff += ["", "### O que mudou"]
        if itens_adicionados:
            linhas_diff += ["", "**Itens novos:**"] + [f"- {i}" for i in itens_adicionados]
        if itens_removidos:
            linhas_diff += ["", "**Itens removidos:**"] + [f"- {i}" for i in itens_removidos]
    linhas = [
        f"## 🔔 Mudança detectada: `{slug}`",
        "",
        f"**Data/hora:** {hoje} {hora} UTC",
        f"**Fonte:** {url}",
        *linhas_diff,
        "",
        "### Acção necessária",
        f"1. Verificar a fonte manualmente: {url}",
        "2. Se os valores/condições mudaram: actualizar a página HTML correspondente",
        "3. Actualizar a data de verificação na página",
        "4. Fechar esta issue após correcção",
    ]
    return "\n".join(linhas)


# ── Testes estáticos sobre o script real do Step "Detectar mudanças" ───────

def test_step2_calcula_url_real_do_scrape_com_fallback_ao_generico():
    script = _carregar_script(NOME_STEP_DETECTAR)
    assert "const url_real = new_data.url || url;" in script


def test_step2_diff_de_itens_lista_capado_a_10_de_cada_lado():
    script = _carregar_script(NOME_STEP_DETECTAR)
    assert "conteudo_extraido.itens_lista" in script or "conteudo_extraido && new_data.conteudo_extraido.itens_lista" in script
    assert ".slice(0, 10)" in script
    assert "itens_adicionados" in script
    assert "itens_removidos" in script


def test_step2_grava_diff_e_url_real_em_mudancas_json():
    script = _carregar_script(NOME_STEP_DETECTAR)
    assert "url: m.url" in script
    assert "itens_adicionados: m.itens_adicionados" in script
    assert "itens_removidos: m.itens_removidos" in script


def test_step2_push_usa_url_real_nunca_o_generico_do_mapa():
    """O objecto empurrado para `mudancas` tem de usar `url_real`, nunca a
    variável `url` sozinha (o genérico do mapa `fontes`) — regressão
    directa do achado da Issue #114."""
    script = _carregar_script(NOME_STEP_DETECTAR)
    match = re.search(r"mudancas\.push\(\{([^}]*)\}\)", script)
    assert match, "mudancas.push(...) não encontrado no script"
    assert "url: url_real" in match.group(1)


# ── Testes estáticos sobre o script real do Step "Abrir Issues" ────────────

def test_step_issues_secao_diff_e_condicional():
    script = _carregar_script(NOME_STEP_ISSUES)
    assert "### O que mudou" in script
    assert "itens_adicionados.length > 0 || itens_removidos.length > 0" in script


def test_step_issues_usa_m_url_na_linha_fonte():
    script = _carregar_script(NOME_STEP_ISSUES)
    assert "**Fonte:** ${m.url}" in script


# ── Testes comportamentais (réplica Python) sobre dados REAIS desta sessão ─

def test_diff_real_paer_2026_08_20_encontra_item_novo_e_item_removido():
    """Dados genuínos desta sessão — nunca fixtures inventadas."""
    scraped_dir = REPO_ROOT / "data/scraped"
    with open(scraped_dir / "dre_habitacao_paer_2026-08-19.json", encoding="utf-8") as f:
        old_data = json.load(f)
    with open(scraped_dir / "dre_habitacao_paer_2026-08-20.json", encoding="utf-8") as f:
        new_data = json.load(f)

    adicionados, removidos = _diff_itens_lista(new_data, old_data)

    assert any("Regulamento n.º 1124-A/2026" in i for i in adicionados)
    assert any("Regulamento n.º 1088/2025" in i for i in removidos)
    assert len(adicionados) == 1
    assert len(removidos) == 1


def test_diff_real_paer_url_e_a_pagina_de_pesquisa_nunca_a_home():
    scraped_dir = REPO_ROOT / "data/scraped"
    with open(scraped_dir / "dre_habitacao_paer_2026-08-20.json", encoding="utf-8") as f:
        new_data = json.load(f)

    url_generico = "https://diariodarepublica.pt/dr/home"
    assert _url_real(new_data, url_generico) == "https://diariodarepublica.pt/dr/pesquisa"


def test_corpo_da_issue_inclui_seccao_diff_quando_ha_itens_novos():
    corpo = _construir_corpo_issue(
        slug="dre_habitacao_paer",
        url="https://diariodarepublica.pt/dr/pesquisa",
        hoje="2026-08-20",
        hora="07:13",
        itens_adicionados=["Regulamento n.º 1124-A/2026 - ..."],
        itens_removidos=["Regulamento n.º 1088/2025 - ..."],
    )
    assert "### O que mudou" in corpo
    assert "**Itens novos:**" in corpo
    assert "- Regulamento n.º 1124-A/2026 - ..." in corpo
    assert "**Itens removidos:**" in corpo
    assert "- Regulamento n.º 1088/2025 - ..." in corpo
    # a secção do diff vem sempre antes de "Acção necessária"
    assert corpo.index("### O que mudou") < corpo.index("### Acção necessária")


def test_corpo_da_issue_omite_seccao_diff_quando_nao_ha_itens():
    """Fontes cujo hash mudou por outro motivo (ex.: `titulo`/`paragrafos`,
    ou uma fonte sem `itens_lista`) nunca ganham uma secção "O que mudou"
    vazia — nunca fingir informação que não existe."""
    corpo = _construir_corpo_issue(
        slug="dge_ase",
        url="https://www.dge.mec.pt",
        hoje="2026-08-20",
        hora="07:13",
        itens_adicionados=[],
        itens_removidos=[],
    )
    assert "### O que mudou" not in corpo
    assert "**Itens novos:**" not in corpo
    assert "**Itens removidos:**" not in corpo


def test_corpo_da_issue_so_secao_novos_quando_so_ha_adicionados():
    corpo = _construir_corpo_issue(
        slug="dre_ias",
        url="https://diariodarepublica.pt/dr/pesquisa",
        hoje="2026-08-20",
        hora="07:13",
        itens_adicionados=["Portaria n.º 1/2027 - ..."],
        itens_removidos=[],
    )
    assert "**Itens novos:**" in corpo
    assert "**Itens removidos:**" not in corpo


def test_diff_nunca_excede_10_itens_de_cada_lado():
    new_data = {"conteudo_extraido": {"itens_lista": [f"novo-{i}" for i in range(30)]}}
    old_data = {"conteudo_extraido": {"itens_lista": [f"antigo-{i}" for i in range(30)]}}
    adicionados, removidos = _diff_itens_lista(new_data, old_data)
    assert len(adicionados) == 10
    assert len(removidos) == 10


def test_diff_sem_itens_lista_devolve_listas_vazias_nunca_excepcao():
    """Fontes sem `conteudo_extraido.itens_lista` (campo ausente, nunca
    `None` de facto neste repositório, mas defendido na mesma) não podem
    fazer o Step 2 rebentar."""
    new_data = {"conteudo_extraido": {"titulo": "x"}}
    old_data = {"conteudo_extraido": {"titulo": "y"}}
    adicionados, removidos = _diff_itens_lista(new_data, old_data)
    assert adicionados == []
    assert removidos == []
