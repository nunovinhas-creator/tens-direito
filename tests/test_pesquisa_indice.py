"""
Testes de consistência do índice de pesquisa (scripts/pesquisa.js) —
`cluster`/`clusterNome`/`tipo` têm de bater certo com data/clusters.json
(fonte única para essa parte dos dados; título/descrição/keywords
continuam curados à mão em pesquisa.js, porque clusters.json não tem
essa riqueza). Corre sobre os ficheiros reais do repositório — mesma
filosofia de test_breadcrumb_coerencia.py/test_nav_coerencia.py.
"""
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import carregar_clusters, encontrar_paginas  # noqa: E402

PESQUISA_JS = (RAIZ / "scripts" / "pesquisa.js").read_text(encoding="utf-8")

# Fora do sistema de clusters e sem entrada esperada no índice de pesquisa
# (decisão documentada no CLAUDE.md — index.html tem a sua própria pesquisa
# do hero, 404.html não faz sentido como resultado de pesquisa,
# simulador-psu.html está deliberadamente não publicado até ao decreto-lei
# da PSU — ver EXCLUIDAS em sincronizar_clusters.py).
NAO_INDEXADAS = {"index.html", "404.html", "simulador-psu.html"}


def carregar_indice_pesquisa():
    m = re.search(r"var paginas = \[([\s\S]*?)\n\];", PESQUISA_JS)
    assert m, "Não encontrei 'var paginas = [...]' em scripts/pesquisa.js"
    corpo = m.group(1)
    entradas = []
    for bloco in re.findall(r"\{[\s\S]*?\}", corpo):
        def campo(nome, bloco=bloco):
            m2 = re.search(nome + r":\s*'([^']*)'", bloco)
            return m2.group(1) if m2 else None
        entradas.append({
            "url": campo("url"),
            "titulo": campo("titulo"),
            "descricao": campo("descricao"),
            "keywords": campo("keywords"),
            "cluster": campo("cluster"),
            "clusterNome": campo("clusterNome"),
            "tipo": campo("tipo"),
        })
    return entradas


INDICE = carregar_indice_pesquisa()
CLUSTERS = carregar_clusters()


def test_indice_nao_esta_vazio():
    assert len(INDICE) >= 20


@pytest.mark.parametrize(
    "caminho", encontrar_paginas(), ids=lambda p: str(p.relative_to(RAIZ))
)
def test_todas_as_paginas_elegiveis_estao_no_indice(caminho):
    if caminho.name in NAO_INDEXADAS:
        pytest.skip(f"{caminho.name} deliberadamente fora do índice de pesquisa")
    slug = str(caminho.relative_to(RAIZ))
    urls_indexados = {e["url"].lstrip("/") for e in INDICE}
    assert slug in urls_indexados, f"{slug} não está em scripts/pesquisa.js"


@pytest.mark.parametrize("entrada", INDICE, ids=lambda e: e["url"])
def test_url_de_cada_entrada_corresponde_a_ficheiro_real(entrada):
    caminho = RAIZ / entrada["url"].lstrip("/")
    assert caminho.exists(), f"{entrada['url']} não corresponde a nenhum ficheiro real"


@pytest.mark.parametrize("entrada", [e for e in INDICE if e["cluster"]], ids=lambda e: e["url"])
def test_cluster_da_entrada_bate_certo_com_clusters_json(entrada):
    slug = entrada["url"].lstrip("/")
    cluster_real = next((c for c in CLUSTERS if c.id == entrada["cluster"]), None)
    assert cluster_real is not None, f"cluster '{entrada['cluster']}' não existe em clusters.json"
    assert entrada["clusterNome"] == cluster_real.nome

    e_pillar = cluster_real.pillar.lstrip("/") == slug
    membro = next((p for p in cluster_real.paginas if p.slug == slug), None)

    assert e_pillar or membro is not None, (
        f"{slug} diz pertencer ao cluster '{entrada['cluster']}' mas não é "
        f"nem o pillar nem uma página membro em clusters.json"
    )
    if e_pillar:
        assert entrada["tipo"] == "pillar"
    else:
        assert entrada["tipo"] == membro.tipo


@pytest.mark.parametrize(
    "entrada", [e for e in INDICE if e["url"].lstrip("/") not in {
        p.slug for c in CLUSTERS for p in c.paginas
    } and e["url"].lstrip("/") not in {c.pillar.lstrip("/") for c in CLUSTERS}],
    ids=lambda e: e["url"],
)
def test_paginas_fora_de_clusters_nao_tem_cluster_atribuido(entrada):
    assert entrada["cluster"] is None
    assert entrada["clusterNome"] is None
