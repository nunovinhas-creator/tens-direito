"""
Rede de segurança para o JSON-LD BreadcrumbList: como é editado à mão
(cada artigo tem um formato ligeiramente diferente — ver histórico),
este teste compara-o com o breadcrumb visível injectado por
sincronizar_clusters.py (marcador CLUSTER-BADGE) e falha se divergirem
no cluster (nome/URL do pillar) ou na página final.

Corre sobre os artigos REAIS do repositório (não fixtures sintéticas)
— é o único ficheiro de testes deste projecto que faz isso
deliberadamente, porque o que está em risco é precisamente a
consistência do conteúdo publicado, editado à mão.
"""
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import carregar_clusters

RAIZ = Path(__file__).parent.parent
CLUSTERS = carregar_clusters(RAIZ / "data" / "clusters.json")

CASOS = [
    (p.slug, c)
    for c in CLUSTERS
    for p in c.paginas
    if p.tipo == "artigo"
]
IDS = [slug for slug, _ in CASOS]


def _extrair_links_badge(html: str):
    m = re.search(r"<!-- CLUSTER-BADGE:INICIO -->([\s\S]*?)<!-- CLUSTER-BADGE:FIM -->", html)
    assert m, "marcador CLUSTER-BADGE não encontrado ou vazio"
    links = re.findall(r'<a href="([^"]+)">([^<]*)</a>', m.group(1))
    assert len(links) >= 2, f"esperava pelo menos 2 links no bloco CLUSTER-BADGE, encontrei {links}"
    return links


def _extrair_breadcrumb_jsonld(html: str):
    for m in re.finditer(r'<script type="application/ld\+json">([\s\S]*?)</script>', html):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        candidatos = data if isinstance(data, list) else [data]
        for item in candidatos:
            if isinstance(item, dict) and item.get("@type") == "BreadcrumbList":
                return sorted(item["itemListElement"], key=lambda i: i["position"])
    return None


def _sem_dominio(url: str) -> str:
    sem = url.replace("https://tensdireito.com", "")
    return sem or "/"


@pytest.mark.parametrize("slug,cluster", CASOS, ids=IDS)
def test_breadcrumb_visivel_coincide_com_jsonld(slug, cluster):
    html = (RAIZ / slug).read_text(encoding="utf-8")

    links_badge = _extrair_links_badge(html)
    href_cluster_visivel = links_badge[1][0]
    assert href_cluster_visivel == cluster.pillar, (
        f"{slug}: breadcrumb visível aponta para '{href_cluster_visivel}', "
        f"esperava o pillar do cluster '{cluster.pillar}'"
    )

    itens = _extrair_breadcrumb_jsonld(html)
    assert itens is not None, f"{slug}: BreadcrumbList em falta no JSON-LD"
    assert len(itens) == 3, f"{slug}: esperava 3 níveis no BreadcrumbList (Início/cluster/artigo), encontrei {len(itens)}"

    item_cluster = itens[1]
    url_cluster_jsonld = _sem_dominio(item_cluster["item"])
    assert url_cluster_jsonld == cluster.pillar, (
        f"{slug}: JSON-LD BreadcrumbList (posição 2) aponta para '{url_cluster_jsonld}', "
        f"esperava o pillar do cluster '{cluster.pillar}'"
    )
    assert cluster.nome in item_cluster["name"] or item_cluster["name"] in cluster.nome, (
        f"{slug}: nome do cluster no JSON-LD ('{item_cluster['name']}') não corresponde a '{cluster.nome}'"
    )

    url_artigo_jsonld = _sem_dominio(itens[-1]["item"]).lstrip("/")
    assert url_artigo_jsonld == slug, (
        f"{slug}: último item do BreadcrumbList aponta para '/{url_artigo_jsonld}', esperava '/{slug}'"
    )
