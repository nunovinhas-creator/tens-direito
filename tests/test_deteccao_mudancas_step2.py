r"""Falso positivo real — Issue #99 (`dre_psu`, 2026-08-18).

O Step 2 ("Detectar mudanças e registar") de `pipeline-diario.yml`
seleccionava o ficheiro "de hoje" de cada fonte por PREFIXO
(`f.startsWith(slug + '_') && f.includes(hoje)`), nunca por nome exacto.
Como `dre_psu_regulamentacao` também começa por `dre_psu_`, o slug
`dre_psu` apanhava os DOIS ficheiros do dia (`dre_psu_2026-08-18.json` e
`dre_psu_regulamentacao_2026-08-18.json`); depois de `.sort().reverse()`,
`'dre_psu_regulamentacao_...'` vem alfabeticamente à frente de
`'dre_psu_2026-08-18...'` ('r' > '2'), por isso `files[0]` era sempre o
ficheiro ERRADO — o conteúdo do sentinela irmão (Portarias de
regulamentação), nunca o conteúdo real da pesquisa PSU.

Esse conteúdo errado era depois escrito em `dre_psu_latest.json`,
corrompendo a baseline para o dia seguinte — foi essa escrita que gerou
a "mudança" fantasma reportada na Issue #99 (o hash do sentinela irmão,
`4c2a3850...`, a substituir o hash real do dia, `9df03d96...`).

Segundo bug, distinto, na mesma comparação: o Step 1 (scraper) já
reescreve `<slug>_latest.json` com o resultado de hoje, ANTES deste
step correr — por isso comparar "hoje" contra `_latest.json` comparava
sempre o mesmo conteúdo contra si próprio (baseline vazia/inútil), o
que mascarava mudanças reais e também alimentava a corrupção acima
(este step voltava a escrever no mesmo ficheiro que o scraper já tinha
escrito correctamente).

Corrigido: (1) o ficheiro de hoje é sempre `${slug}_${hoje}.json`, nome
exacto, nunca prefixo; (2) a baseline passa a ser o ficheiro diário
anterior mais recente (regex `^${slug}_\d{4}-\d{2}-\d{2}\.json$`,
excluindo o de hoje) com `status` `ok`/`ok_via_arquivo` e sem `aviso`;
(3) este step nunca mais escreve em `<slug>_latest.json` — o único
escritor do latest volta a ser `scraper_playwright._guardar_resultado`
(Step 1), como já documentado em CLAUDE.md para essa função.

Estes testes correm sobre o YAML real do workflow (nunca uma cópia) e
sobre a lógica de selecção replicada em Python (sem precisar de Node
para executar o step) — mesmo padrão de regressão já usado noutras
sessões para achados encontrados só depois de uma corrida real (ver
`tests/test_dre_habitacao_watchlist.py`, Issue #73).
"""
import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github/workflows/pipeline-diario.yml"
NOME_STEP = "Detectar mudanças e registar"


def _carregar_script_step2():
    dados = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    for step in dados["jobs"]["pipeline"]["steps"]:
        if step.get("name") == NOME_STEP:
            script = step.get("with", {}).get("script")
            assert script, f"Step '{NOME_STEP}' não tem 'with.script'"
            return script
    raise AssertionError(f"Step '{NOME_STEP}' não encontrado em {WORKFLOW_PATH}")


def test_step2_nunca_selecciona_ficheiro_de_hoje_por_prefixo():
    """O bug real: `startsWith(slug + '_')` apanhava qualquer outro slug
    com o mesmo prefixo (dre_psu ~ dre_psu_regulamentacao). Nunca deve
    voltar a aparecer no script deste step."""
    script = _carregar_script_step2()
    assert "startsWith(slug + '_')" not in script
    assert "startsWith(slug" not in script


def test_step2_constroi_nome_exacto_do_ficheiro_de_hoje():
    script = _carregar_script_step2()
    assert "${slug}_${hoje}.json" in script


def test_step2_nunca_escreve_em_caminho_latest():
    """A escrita em `<slug>_latest.json` por este step é a causa directa
    da corrupção da Issue #99 — o único escritor legítimo do latest é
    `scraper_playwright._guardar_resultado` (Step 1)."""
    script = _carregar_script_step2()
    for match in re.finditer(r"writeFileSync\(\s*([^,]+),", script):
        alvo = match.group(1)
        assert "latest" not in alvo, (
            f"writeFileSync a escrever num caminho com 'latest': {match.group(0)!r}"
        )


def test_step2_baseline_usa_regex_diario_ancorada_ao_slug_exacto():
    """A baseline nova tem de vir de um ficheiro `<slug>_AAAA-MM-DD.json`
    validado (status ok/ok_via_arquivo, sem aviso) — nunca de
    `_latest.json`, que já foi reescrito pelo Step 1 com o resultado de
    hoje antes deste step correr. `_latest.json` continua a aparecer em
    comentários explicativos (documentação do porquê), por isso o teste
    verifica a ausência da CONSTRUÇÃO de código (`${slug}_latest.json`),
    não a ausência da substring em qualquer sítio do script."""
    script = _carregar_script_step2()
    assert "${slug}_latest.json" not in script
    assert "regex_diario" in script
    assert "RegExp(`^${slug}_" in script
    assert "f !== ficheiro_hoje" in script
    assert "d.status === 'ok'" in script
    assert "!d.aviso" in script


def test_step2_mantem_camada_1_bloqueado_e_fallback_hashof():
    """A Camada 1 (ignorar `status === 'bloqueado'`) e o fallback de
    hash (`hashOf`, quando `hash_conteudo` não existir) são
    invariantes já testados noutro lado (scraper) — este step não pode
    perder nenhum dos dois ao ser corrigido."""
    script = _carregar_script_step2()
    assert "new_data.status === 'bloqueado'" in script
    assert "hashOf(new_data)" in script
    assert "hashOf(old_data)" in script


def test_selecao_por_nome_exacto_nunca_apanha_slug_com_prefixo_partilhado():
    """Réplica pura em Python (sem YAML, sem Node) do achado real: com
    os nomes de ficheiro reais do dia 2026-08-18, o slug 'dre_psu'
    resolvido por PREFIXO apanharia o ficheiro errado (o de
    'dre_psu_regulamentacao', que ordena depois alfabeticamente); por
    NOME EXACTO resolve sempre para o ficheiro certo."""
    nomes = [
        "dre_psu_2026-08-18.json",
        "dre_psu_regulamentacao_2026-08-18.json",
    ]
    slug = "dre_psu"
    hoje = "2026-08-18"

    # comportamento antigo (prefixo), replicado só para provar o bug:
    por_prefixo = sorted(
        (n for n in nomes if n.startswith(slug + "_") and hoje in n),
        reverse=True,
    )
    assert por_prefixo[0] == "dre_psu_regulamentacao_2026-08-18.json"

    # comportamento novo (nome exacto):
    ficheiro_hoje = f"{slug}_{hoje}.json"
    assert ficheiro_hoje in nomes
    assert ficheiro_hoje == "dre_psu_2026-08-18.json"
