r"""Issue #158 (`dre_habitacao_garantia`, 2026-09-03) — o termo de pesquisa
"garantia pessoal do Estado" (corrigido na Issue #151, ver
`scripts/scraper_playwright.py`) está correcto: é a expressão legal exacta
do DL n.º 44/2024, e o detector dedicado (`detectar_decreto_lei`, chave
`dre_habitacao_garantia_decreto_detectado`) já filtra correctamente por
tipo (só Decreto-Lei) + corte de recência — nunca disparou por engano.

O ruído real da Issue #158 vinha de outro sítio: o step genérico "Detectar
mudanças e registar" de `pipeline-diario.yml` compara `itens_lista` em
bruto, sem filtro nenhum de tipo. Confirmado com os dados reais desta
sessão (`data/scraped/dre_habitacao_garantia_2026-09-0{2,3}.json`, nunca
fixtures inventadas): a pesquisa devolveu 24 itens no total, dos quais 22
eram "Resolução do Conselho de Ministros" de 1997-2021 sem relação nenhuma
com crédito habitação jovem (confirmada por pesquisa externa: a RCM
n.º 30/2021 autoriza uma garantia do Estado no âmbito de uma convenção
Portugal-Angola) — e só 2 eram Portarias genuinamente ligadas ao DL
44/2024 (a já conhecida n.º 236-A/2024/1, e a sua 1.ª alteração, a
n.º 187/2025/1, achado real desta triagem, ainda não citada em
`dados/parametros/habitacao.yaml`).

Corrigido só para `dre_habitacao_garantia`: o diff genérico passa a operar
sobre uma allow-list de tipos de acto legal (Decreto-Lei/Lei/Portaria/
Despacho — os únicos que os 5 detectores dedicados deste repositório
alguma vez tratam como sinal), extraída só de `itens_lista` (nunca
`paragrafos`, um recorte truncado e instável dos primeiros resultados
renderizados — achado lateral: "Decreto-Lei n.º 7/2002", sem relação
nenhuma com o DL 44/2024, aparecia em `paragrafos` mas nunca em
`itens_lista`). Quando a lista filtrada fica vazia dos dois lados, nenhuma
"mudança" é registada — nunca uma issue "mudou algo" sem nada de
accionável.

**Nunca generalizado às outras 4 fontes DRE de pesquisa interactiva**
nesta sessão: `dre_habitacao_paer` tem um caso real e já testado em
`tests/test_diff_mudancas_issue.py` (Issue #114) em que o sinal relevante
era um "Regulamento" — um tipo fora desta allow-list. Aplicar o mesmo
filtro ali sem confirmar primeiro o perfil de ruído real dessa fonte
regrediria uma detecção já validada; `dre_psu`/`dre_psu_regulamentacao`/
`dre_ias` nunca foram examinadas nesta sessão. Generalizar por analogia,
sem confirmar contra dados reais, é exactamente o erro que já custou duas
rondas a este sentinela (Issues #147/#148/#151)."""
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github/workflows/pipeline-diario.yml"
NOME_STEP_DETECTAR = "Detectar mudanças e registar"


def _carregar_script(nome_step: str) -> str:
    dados = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for step in dados["jobs"]["pipeline"]["steps"]:
        if step.get("name") == nome_step:
            script = step.get("with", {}).get("script")
            assert script, f"Step '{nome_step}' não tem 'with.script'"
            return script
    raise AssertionError(f"Step '{nome_step}' não encontrado em {WORKFLOW_PATH}")


# ── Réplica pura em Python da allow-list de tipos de acto legal ────────────

ACTO_LEGAL_REGEX = re.compile(r"^(Decreto-Lei|Lei|Portaria|Despacho)\s", re.IGNORECASE)


def _extrair_atos_legais(conteudo: dict) -> set[str]:
    """Réplica exacta de `extrairAtosLegais()` no Step 2 — só `itens_lista`,
    nunca `paragrafos` (ver docstring do módulo)."""
    itens = (conteudo or {}).get("itens_lista") or []
    return {t for t in itens if ACTO_LEGAL_REGEX.match(t)}


def _diff_atos_legais(new_data: dict, old_data: dict, limite: int = 10) -> tuple[list, list]:
    atos_novos = _extrair_atos_legais(new_data.get("conteudo_extraido"))
    atos_antigos = _extrair_atos_legais(old_data.get("conteudo_extraido"))
    adicionados = [i for i in atos_novos if i not in atos_antigos][:limite]
    removidos = [i for i in atos_antigos if i not in atos_novos][:limite]
    return adicionados, removidos


def _diff_itens_lista_bruto(new_data: dict, old_data: dict) -> tuple[list, list]:
    """Réplica do diff SEM filtro (comportamento anterior, ainda usado tal
    e qual para qualquer fonte fora da allow-list)."""
    itens_novos = ((new_data.get("conteudo_extraido") or {}).get("itens_lista")) or []
    itens_antigos = ((old_data.get("conteudo_extraido") or {}).get("itens_lista")) or []
    set_antigos = set(itens_antigos)
    set_novos = set(itens_novos)
    adicionados = [i for i in itens_novos if i not in set_antigos][:10]
    removidos = [i for i in itens_antigos if i not in set_novos][:10]
    return adicionados, removidos


# ── Testes estáticos sobre o script real do Step "Detectar mudanças" ───────

def test_step2_tem_allow_list_de_atos_legais_para_dre():
    script = _carregar_script(NOME_STEP_DETECTAR)
    assert "ACTO_LEGAL_REGEX" in script
    assert "DRE_SLUGS_PESQUISA" in script
    assert "extrairAtosLegais" in script


def test_step2_allow_list_scoped_so_a_dre_habitacao_garantia():
    """Generalizar às outras 4 fontes DRE sem confirmar cada uma contra
    dados reais regrediria `dre_habitacao_paer` (sinal real = "Regulamento",
    fora desta allow-list, Issue #114) — nunca alargar este `Set` só por
    analogia. Se uma sessão futura confirmar (contra dados reais) que outra
    fonte também beneficia deste filtro, este teste tem de ser actualizado
    conscientemente, nunca por acidente."""
    script = _carregar_script(NOME_STEP_DETECTAR)
    match = re.search(r"const DRE_SLUGS_PESQUISA = new Set\(\[([^\]]*)\]\)", script)
    assert match, "DRE_SLUGS_PESQUISA não encontrado no script"
    slugs = re.findall(r"'([^']+)'", match.group(1))
    assert slugs == ["dre_habitacao_garantia"]


def test_step2_extrai_atos_legais_so_de_itens_lista_nunca_paragrafos():
    """`paragrafos` é um recorte truncado e instável (achado real: um
    Decreto-Lei de 2002 sem relação com o DL 44/2024 aparecia lá mas nunca
    em `itens_lista`) — nunca deve entrar na allow-list."""
    script = _carregar_script(NOME_STEP_DETECTAR)
    match = re.search(r"const extrairAtosLegais = \(conteudo\) => \{([^}]*)\}", script, re.DOTALL)
    assert match, "extrairAtosLegais não encontrado no script"
    corpo = match.group(1)
    assert "itens_lista" in corpo
    assert "paragrafos" not in corpo


def test_step2_suprime_mudanca_dre_quando_filtro_fica_vazio():
    script = _carregar_script(NOME_STEP_DETECTAR)
    assert "itens_adicionados.length === 0 && itens_removidos.length === 0" in script
    assert "continue" in script


# ── Testes comportamentais sobre dados REAIS desta sessão (Issue #158) ─────

def test_raw_diff_da_issue_158_e_dominado_por_ruido_rcm():
    """Confirma o problema — a mesma comparação que gerou a Issue #158 real
    (baseline vazia de 2026-09-02 → 24 itens em 2026-09-03) devolve, sem
    filtro, uma maioria esmagadora de Resoluções do Conselho de Ministros
    sem relação com o DL 44/2024."""
    scraped_dir = REPO_ROOT / "data/scraped"
    old_data = __import__("json").loads((scraped_dir / "dre_habitacao_garantia_2026-09-02.json").read_text(encoding="utf-8"))
    new_data = __import__("json").loads((scraped_dir / "dre_habitacao_garantia_2026-09-03.json").read_text(encoding="utf-8"))

    adicionados, removidos = _diff_itens_lista_bruto(new_data, old_data)

    assert removidos == []
    assert len(adicionados) == 10  # capado pelo limite de 10 do step real
    n_rcm = sum(1 for i in adicionados if i.startswith("Resolução do Conselho de Ministros"))
    assert n_rcm == 10, "os 10 primeiros itens do diff em bruto são todos RCM (ruído)"


def test_filtro_de_atos_legais_isola_so_as_2_portarias_relevantes():
    """A correcção: a mesma comparação, filtrada pela allow-list, devolve
    só os 2 actos genuinamente ligados ao DL 44/2024 — nenhuma RCM."""
    scraped_dir = REPO_ROOT / "data/scraped"
    old_data = __import__("json").loads((scraped_dir / "dre_habitacao_garantia_2026-09-02.json").read_text(encoding="utf-8"))
    new_data = __import__("json").loads((scraped_dir / "dre_habitacao_garantia_2026-09-03.json").read_text(encoding="utf-8"))

    adicionados, removidos = _diff_atos_legais(new_data, old_data)

    assert removidos == []
    assert len(adicionados) == 2
    assert any("187/2025/1" in i for i in adicionados), "a 1.ª alteração à Portaria 236-A/2024/1 tem de ser encontrada"
    assert any("236-A/2024/1" in i for i in adicionados)
    assert not any(i.startswith("Resolução do Conselho de Ministros") for i in adicionados)


def test_portaria_187_2025_1_ainda_nao_esta_citada_no_yaml_de_parametros():
    """Achado real desta triagem: a Portaria n.º 187/2025/1 (1.ª alteração
    à Portaria n.º 236-A/2024/1, confirmada por pesquisa externa) ainda não
    está referenciada em `dados/parametros/habitacao.yaml` — registado em
    ROADMAP.md para uma sessão de fact-checking dedicada, nunca aplicado
    sem confirmar primeiro se altera algum valor já publicado."""
    yaml_path = REPO_ROOT / "dados/parametros/habitacao.yaml"
    conteudo = yaml_path.read_text(encoding="utf-8")
    assert "187/2025" not in conteudo, (
        "se este teste falhar, a Portaria 187/2025/1 já foi incorporada — "
        "óptimo, mas confirmar que a nota em ROADMAP.md foi removida a par"
    )


def test_filtro_nunca_afecta_dre_habitacao_paer_regulamento_ja_testado():
    """Regressão directa: o caso real de `dre_habitacao_paer` (Issue #114,
    `tests/test_diff_mudancas_issue.py`) usa "Regulamento" como sinal — um
    tipo fora da allow-list. Como esta fonte NUNCA entra em
    `DRE_SLUGS_PESQUISA` (ver `test_step2_allow_list_scoped_so_a_dre_habitacao_garantia`),
    o diff continua em bruto e encontra exactamente o mesmo resultado de
    sempre."""
    scraped_dir = REPO_ROOT / "data/scraped"
    old_data = __import__("json").loads((scraped_dir / "dre_habitacao_paer_2026-08-19.json").read_text(encoding="utf-8"))
    new_data = __import__("json").loads((scraped_dir / "dre_habitacao_paer_2026-08-20.json").read_text(encoding="utf-8"))

    # Se esta fonte alguma vez entrar na allow-list, o filtro apagaria o
    # sinal real (Regulamento não bate com ACTO_LEGAL_REGEX) — confirmar
    # aqui que continua a não bater, para o dia em que alguém a adicionar
    # por engano a `DRE_SLUGS_PESQUISA` sem os devidos testes.
    adicionados_filtrado, removidos_filtrado = _diff_atos_legais(new_data, old_data)
    assert adicionados_filtrado == []
    assert removidos_filtrado == []

    adicionados_bruto, removidos_bruto = _diff_itens_lista_bruto(new_data, old_data)
    assert any("Regulamento n.º 1124-A/2026" in i for i in adicionados_bruto)
    assert any("Regulamento n.º 1088/2025" in i for i in removidos_bruto)


def test_filtro_devolve_vazio_quando_so_ha_ruido_rcm_dos_dois_lados():
    """Cenário sintético (nunca fixture inventada para os dados reais
    acima, só para o caso de fronteira "tudo ruído"): duas baselines cuja
    única diferença é uma RCM a entrar/sair — o filtro tem de devolver
    listas vazias dos dois lados, para o Step 2 nunca criar uma issue sem
    nada de accionável."""
    old_data = {"conteudo_extraido": {"itens_lista": [
        "Resolução do Conselho de Ministros n.º 1/98 - Diário da República n.º 1/1998, Série I-B de 1998-01-01",
    ]}}
    new_data = {"conteudo_extraido": {"itens_lista": [
        "Resolução do Conselho de Ministros n.º 2/99 - Diário da República n.º 2/1999, Série I-B de 1999-01-01",
    ]}}
    adicionados, removidos = _diff_atos_legais(new_data, old_data)
    assert adicionados == []
    assert removidos == []
