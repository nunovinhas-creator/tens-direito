"""
`<lastmod>` do sitemap = data da própria página.

Data da página: `dateModified` do JSON-LD ou, sem ele, o último carimbo
"Verificado a" (`scripts/sincronizar_sitemap_lastmod.py::data_da_pagina`).
Gerado por `python scripts/sincronizar_sitemap_lastmod.py --write`, nunca à
mão.

Falha se:
- uma página do sitemap fora de EXCECOES_SEM_LASTMOD não tiver `<lastmod>`,
  ou o tiver diferente da data da página;
- uma excepção tiver `<lastmod>`;
- uma excepção ficar órfã (a página saiu do sitemap; uma institucional
  ganhou data própria; uma "do pipeline" deixou de ser escrita pelo
  pipeline diário) — a excepção tem de sair.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import sincronizar_sitemap_lastmod as S  # noqa: E402

PIPELINE = (RAIZ / ".github" / "workflows" / "pipeline-diario.yml").read_text(encoding="utf-8")

# tipo "pipeline": alterada todos os dias pelo pipeline-diario.yml, que não
# escreve no sitemap — um lastmod fixo ficaria desactualizado no dia seguinte.
# tipo "sem_data": institucional, sem data editorial (sem dateModified nem
# "Verificado a") — não há data verdadeira para pôr no lastmod.
EXCECOES_SEM_LASTMOD = {
    "index.html": ("pipeline", "o pipeline diário reescreve o dateModified da homepage todos os dias e não escreve no sitemap"),
    "noticias.html": ("pipeline", "o pipeline diário regenera o arquivo de notícias todos os dias e não escreve no sitemap"),
    "comecar-aqui.html": ("sem_data", "quiz de orientação, institucional, sem data editorial"),
    "sobre.html": ("sem_data", "página institucional, sem data editorial"),
    "privacidade.html": ("sem_data", "página institucional, sem data editorial"),
    "acessibilidade.html": ("sem_data", "página institucional, sem data editorial"),
}

_URLS = re.findall(r"<url>(.*?)</url>", S.SITEMAP.read_text(encoding="utf-8"), re.S)


def _entradas():
    for corpo in _URLS:
        loc = re.search(r"<loc>(.*?)</loc>", corpo).group(1)
        lm = re.search(r"<lastmod>(.*?)</lastmod>", corpo)
        caminho = S.caminho_de_loc(loc)
        yield str(caminho.relative_to(RAIZ)), caminho, (lm.group(1) if lm else None)


ENTRADAS = list(_entradas())


@pytest.mark.parametrize("rel,caminho,lastmod", ENTRADAS, ids=[e[0] for e in ENTRADAS])
def test_lastmod_igual_a_data_da_pagina(rel, caminho, lastmod):
    if rel in EXCECOES_SEM_LASTMOD:
        assert lastmod is None, f"{rel} é excepção sem lastmod mas tem <lastmod>{lastmod}</lastmod>"
        return
    data = S.data_da_pagina(caminho)
    assert data, f"{rel}: sem dateModified nem 'Verificado a' — sem data, não pode ter lastmod nem ficar fora das excepções"
    assert lastmod is not None, f"{rel}: sem <lastmod> (data da página: {data}) — correr scripts/sincronizar_sitemap_lastmod.py --write"
    assert lastmod == data, f"{rel}: <lastmod>{lastmod}</lastmod> ≠ data da página {data}"


@pytest.mark.parametrize("rel", sorted(EXCECOES_SEM_LASTMOD))
def test_excecao_nao_esta_orfa(rel):
    tipo, motivo = EXCECOES_SEM_LASTMOD[rel]
    assert motivo.strip()
    assert rel in {e[0] for e in ENTRADAS}, f"{rel} já não está no sitemap — retirar a excepção"
    if tipo == "sem_data":
        data = S.data_da_pagina(RAIZ / rel)
        assert data is None, f"{rel} ganhou data própria ({data}) — retirar a excepção e gerar o lastmod"
    else:
        assert tipo == "pipeline"
        assert rel in PIPELINE, f"{rel} já não é escrita pelo pipeline-diario.yml — retirar a excepção"


def test_script_e_teste_tem_as_mesmas_excecoes():
    assert set(S.SEM_LASTMOD) == set(EXCECOES_SEM_LASTMOD)


def test_sitemap_sincronizado():
    xml = S.SITEMAP.read_text(encoding="utf-8")
    assert S.sincronizar(xml) == xml, "correr python scripts/sincronizar_sitemap_lastmod.py --write"


def test_verificador_apoios_e_noindex():
    html = (RAIZ / "verificador-apoios.html").read_text(encoding="utf-8")
    assert re.search(r'<meta name="robots" content="noindex[^"]*">', html), (
        "verificador-apoios.html é só um redireccionamento — tem de ser noindex"
    )


def test_calendario_psu_sem_checklist_assets():
    html = (RAIZ / "calendario-pagamentos-psu.html").read_text(encoding="utf-8")
    if "checklist-final" not in html:
        assert "checklist.css" not in html and "checklist.js" not in html


# ── Nenhum workflow avança a data de uma página com lastmod sem o sitemap ──
#
# Quem avança um dateModified ou um "Verificado a" corre
# scripts/sincronizar_sitemap_lastmod.py no mesmo commit. Um workflow não o
# faz hoje, por isso só pode tocar nessas datas em páginas sem lastmod
# (EXCECOES_SEM_LASTMOD). Cobre todos os .yml de .github/workflows e os
# scripts que eles correm.

WORKFLOWS = sorted((RAIZ / ".github" / "workflows").glob("*.yml"))
_RE_DATA_PAGINA = re.compile(r"dateModified|Verificado a|Verificado em")
_RE_SCRIPT = re.compile(r"scripts/([a-z_]+\.py)")

# Scripts corridos por workflows que mencionam estas datas só para as LER.
# Motivo obrigatório; uma entrada que deixe de ser corrida ou deixe de
# mencionar as datas tem de sair.
SCRIPTS_SO_LEEM_DATAS = {
    "verificar_datas.py": "compara datas do texto com o carimbo; só escreve data/alertas_datas.json",
}


def _linhas_de_escrita(texto: str):
    for n, linha in enumerate(texto.splitlines(), 1):
        if linha.strip().startswith("#"):
            continue
        if _RE_DATA_PAGINA.search(linha) and re.search(r"\bsed\b|\bperl\b|>\s*\S+\.html|write_text|\.replace\(", linha):
            yield n, linha


@pytest.mark.parametrize("workflow", WORKFLOWS, ids=[w.name for w in WORKFLOWS])
def test_workflow_so_escreve_datas_em_paginas_sem_lastmod(workflow):
    texto = workflow.read_text(encoding="utf-8")
    for n, linha in _linhas_de_escrita(texto):
        alvos = set(re.findall(r"[\w./-]+\.html", linha))
        assert alvos, f"{workflow.name}:{n} escreve uma data de página sem alvo .html identificável: {linha.strip()}"
        fora = {a for a in alvos if a not in EXCECOES_SEM_LASTMOD}
        assert not fora, (
            f"{workflow.name}:{n} altera dateModified/'Verificado a' de {sorted(fora)}, que têm lastmod no "
            "sitemap — o workflow tem de correr scripts/sincronizar_sitemap_lastmod.py no mesmo commit, "
            "ou a página entra em EXCECOES_SEM_LASTMOD com motivo"
        )


def _scripts_dos_workflows():
    nomes = set()
    for w in WORKFLOWS:
        nomes |= set(_RE_SCRIPT.findall(w.read_text(encoding="utf-8")))
    return sorted(n for n in nomes if (RAIZ / "scripts" / n).exists())


@pytest.mark.parametrize("script", _scripts_dos_workflows())
def test_scripts_dos_workflows_nao_mexem_em_datas_de_paginas(script):
    if script == "sincronizar_sitemap_lastmod.py":
        return
    texto = (RAIZ / "scripts" / script).read_text(encoding="utf-8")
    menciona = bool(_RE_DATA_PAGINA.search(texto))
    if script in SCRIPTS_SO_LEEM_DATAS:
        assert menciona, f"{script} já não menciona datas de página — retirar de SCRIPTS_SO_LEEM_DATAS"
        return
    assert not menciona, (
        f"scripts/{script} (corrido por um workflow) menciona dateModified/'Verificado a' — se as escreve, "
        "o workflow tem de correr scripts/sincronizar_sitemap_lastmod.py no mesmo commit; se só as lê, "
        "acrescentar a SCRIPTS_SO_LEEM_DATAS com motivo"
    )


def test_scripts_so_leem_datas_continuam_a_ser_corridos():
    corridos = set(_scripts_dos_workflows())
    orfaos = set(SCRIPTS_SO_LEEM_DATAS) - corridos
    assert not orfaos, f"{sorted(orfaos)} já não são corridos por nenhum workflow — retirar de SCRIPTS_SO_LEEM_DATAS"


def test_revalidacao_de_carimbo_ligada_exige_sitemap_no_mesmo_commit():
    """auto_update_engine.aplicar_refresh_carimbo avança "Verificado a" e
    dateModified. Enquanto REVALIDACAO_CARIMBO_HABILITADA (ou
    AUTO_UPDATE_HABILITADO) estiver a False não escreve nada. No dia em que
    passar a True, algum workflow tem de correr o sincronizador do sitemap."""
    import decisao_datas

    ligado = decisao_datas.REVALIDACAO_CARIMBO_HABILITADA or decisao_datas.AUTO_UPDATE_HABILITADO
    if not ligado:
        return
    corre = any("sincronizar_sitemap_lastmod.py" in w.read_text(encoding="utf-8") for w in WORKFLOWS)
    assert corre, (
        "REVALIDACAO_CARIMBO_HABILITADA/AUTO_UPDATE_HABILITADO ligado: o workflow que aplica o refresh de "
        "carimbo tem de correr scripts/sincronizar_sitemap_lastmod.py --write no mesmo commit e incluir "
        "sitemap.xml no seu guardrail"
    )
