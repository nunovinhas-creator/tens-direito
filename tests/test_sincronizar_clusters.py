"""
Testes para scripts/sincronizar_clusters.py — injecção idempotente de
navegação de clusters a partir de data/clusters.json.

Todos os testes isolam o sistema de ficheiros com `tmp_path` e um
clusters.json de teste — nunca tocam nos ficheiros reais do repositório.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from sincronizar_clusters import (
    carregar_clusters,
    processar_pagina,
    processar_home,
    validar_consistencia,
    render_home_cards,
    artigos_relacionados,
    contagem_str,
)

_CLUSTERS_TESTE = {
    "clusters": [
        {
            "id": "cluster-a",
            "nome": "Cluster A",
            "descricao_curta": "Descrição do cluster A.",
            "icone": "🅰️",
            "pillar": "/p/cluster-a.html",
            "paginas": [
                {"slug": "artigo-1.html", "titulo": "Artigo 1", "tipo": "artigo", "destaque": True},
                {"slug": "artigo-2.html", "titulo": "Artigo 2", "tipo": "artigo", "destaque": False},
            ],
            "relacionados": ["cluster-b"],
        },
        {
            "id": "cluster-b",
            "nome": "Cluster B",
            "descricao_curta": "Descrição do cluster B.",
            "icone": "🅱️",
            "pillar": "/p/cluster-b.html",
            "paginas": [
                {"slug": "artigo-3.html", "titulo": "Artigo 3", "tipo": "artigo", "destaque": True},
            ],
            "relacionados": [],
        },
    ]
}

_ARTIGO_COM_MARCADORES = """<!DOCTYPE html>
<html lang="pt">
<head><title>Artigo 1</title></head>
<body>
  <main>
    <!-- CLUSTER-BADGE:INICIO -->
    <!-- CLUSTER-BADGE:FIM -->
    <h1>Artigo 1</h1>
    <p>Conteúdo do artigo.</p>
    <!-- RELACIONADOS:INICIO -->
    <!-- RELACIONADOS:FIM -->
  </main>
</body>
</html>
"""

_ARTIGO_SEM_MARCADORES = """<!DOCTYPE html>
<html lang="pt">
<head><title>Artigo 1</title></head>
<body>
  <main>
    <h1>Artigo 1</h1>
    <p>Conteúdo sem nenhum marcador de cluster.</p>
  </main>
</body>
</html>
"""

_HOME_COM_MARCADOR = """<!DOCTYPE html>
<html lang="pt">
<body>
  <section id="guias-de-apoios">
    <!-- CLUSTERS:HOME:INICIO -->
    <!-- CLUSTERS:HOME:FIM -->
  </section>
  <section id="guias-principais">
    <!-- DESTAQUES:HOME:INICIO -->
    <!-- DESTAQUES:HOME:FIM -->
  </section>
</body>
</html>
"""


def _clusters(tmp_path):
    caminho = tmp_path / "clusters.json"
    caminho.write_text(json.dumps(_CLUSTERS_TESTE, ensure_ascii=False), encoding="utf-8")
    return carregar_clusters(caminho)


def _escrever(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


# ── Injecção básica ──────────────────────────────────────────────────────

def test_injeta_badge_e_relacionados_num_artigo_membro(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "artigo-1.html", _ARTIGO_COM_MARCADORES)

    resultado = processar_pagina(caminho, clusters, raiz=tmp_path)

    assert resultado.alterado is True
    conteudo = caminho.read_text(encoding="utf-8")
    assert "Cluster A" in conteudo
    assert "Artigo 2" in conteudo  # irmão do mesmo cluster, sugerido como relacionado
    assert "/noticias.html" in conteudo


def test_injeta_lista_numa_pillar_page(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(
        tmp_path, "p/cluster-a.html",
        "<html><body><ul><!-- PILLAR-LISTA:INICIO -->\n<!-- PILLAR-LISTA:FIM --></ul></body></html>",
    )

    resultado = processar_pagina(caminho, clusters, raiz=tmp_path)

    assert resultado.alterado is True
    conteudo = caminho.read_text(encoding="utf-8")
    assert "<li><a href=\"/artigo-1.html\">Artigo 1</a></li>" in conteudo
    assert "<li><a href=\"/artigo-2.html\">Artigo 2</a></li>" in conteudo


def test_injeta_cartoes_na_home(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "index.html", _HOME_COM_MARCADOR)

    resultado = processar_home(caminho, clusters)

    assert resultado.alterado is True
    conteudo = caminho.read_text(encoding="utf-8")
    assert "Cluster A" in conteudo
    assert "Cluster B" in conteudo
    assert "2 guias" in conteudo  # cluster-a tem 2 artigos
    assert "1 guia<" in conteudo  # cluster-b tem 1 artigo (singular, não "1 guias")
    assert "/artigo-1.html" in conteudo  # destaque do cluster-a
    assert "/artigo-3.html" in conteudo  # destaque do cluster-b
    assert "/artigo-2.html" not in conteudo  # não é destaque — não aparece nos "guias principais"


# ── Idempotência (obrigatória) ───────────────────────────────────────────

def test_correr_duas_vezes_nao_altera_na_segunda(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "artigo-1.html", _ARTIGO_COM_MARCADORES)

    r1 = processar_pagina(caminho, clusters, raiz=tmp_path)
    conteudo_apos_primeira = caminho.read_text(encoding="utf-8")

    r2 = processar_pagina(caminho, clusters, raiz=tmp_path)
    conteudo_apos_segunda = caminho.read_text(encoding="utf-8")

    assert r1.alterado is True
    assert r2.alterado is False
    assert "já sincronizado" in r2.motivo
    assert conteudo_apos_primeira == conteudo_apos_segunda


def test_home_correr_duas_vezes_e_estavel(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "index.html", _HOME_COM_MARCADOR)

    processar_home(caminho, clusters)
    conteudo_apos_primeira = caminho.read_text(encoding="utf-8")
    r2 = processar_home(caminho, clusters)

    assert r2.alterado is False
    assert caminho.read_text(encoding="utf-8") == conteudo_apos_primeira


# ── Marcador em falta ────────────────────────────────────────────────────

def test_pagina_sem_marcadores_nao_e_alterada(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "artigo-1.html", _ARTIGO_SEM_MARCADORES)
    conteudo_antes = caminho.read_text(encoding="utf-8")

    resultado = processar_pagina(caminho, clusters, raiz=tmp_path)

    assert resultado.alterado is False
    assert "marcador(es) em falta" in resultado.motivo
    assert "CLUSTER-BADGE" in resultado.motivo
    assert "RELACIONADOS" in resultado.motivo
    assert caminho.read_text(encoding="utf-8") == conteudo_antes


def test_home_sem_marcador_nao_e_alterada(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "index.html", "<html><body>sem marcador aqui</body></html>")
    conteudo_antes = caminho.read_text(encoding="utf-8")

    resultado = processar_home(caminho, clusters)

    assert resultado.alterado is False
    assert "em falta" in resultado.motivo
    assert caminho.read_text(encoding="utf-8") == conteudo_antes


# ── dry-run ──────────────────────────────────────────────────────────────

def test_dry_run_nao_escreve_ficheiro(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "artigo-1.html", _ARTIGO_COM_MARCADORES)
    conteudo_antes = caminho.read_text(encoding="utf-8")

    resultado = processar_pagina(caminho, clusters, raiz=tmp_path, escrever=False)

    assert resultado.alterado is True
    assert "dry-run" in resultado.motivo
    assert caminho.read_text(encoding="utf-8") == conteudo_antes


# ── Validação de consistência ────────────────────────────────────────────

def test_pagina_no_json_sem_ficheiro_e_reportada(tmp_path):
    clusters = _clusters(tmp_path)
    # Nenhum ficheiro artigo-1.html/artigo-2.html/artigo-3.html criado em tmp_path,
    # nem as respectivas pillar pages.
    problemas = validar_consistencia(clusters, raiz=tmp_path)

    assert any("artigo-1.html" in p for p in problemas)
    assert any("artigo-3.html" in p for p in problemas)
    assert any("p/cluster-a.html" in p for p in problemas)


def test_ficheiro_sem_entrada_no_json_e_reportado(tmp_path):
    clusters = _clusters(tmp_path)
    for pagina in ("artigo-1.html", "artigo-2.html"):
        _escrever(tmp_path, pagina, _ARTIGO_COM_MARCADORES)
    _escrever(tmp_path, "artigo-3.html", _ARTIGO_COM_MARCADORES)
    _escrever(tmp_path, "p/cluster-a.html", "<html></html>")
    _escrever(tmp_path, "p/cluster-b.html", "<html></html>")
    _escrever(tmp_path, "orfao.html", "<html><body>página sem cluster</body></html>")

    problemas = validar_consistencia(clusters, raiz=tmp_path)

    assert any("orfao.html" in p for p in problemas)
    assert not any("artigo-1.html' no JSON" in p for p in problemas)


def test_pagina_excluida_nao_e_reportada_como_orfa(tmp_path):
    clusters = _clusters(tmp_path)
    for pagina in ("artigo-1.html", "artigo-2.html", "artigo-3.html"):
        _escrever(tmp_path, pagina, _ARTIGO_COM_MARCADORES)
    _escrever(tmp_path, "p/cluster-a.html", "<html></html>")
    _escrever(tmp_path, "p/cluster-b.html", "<html></html>")
    _escrever(tmp_path, "index.html", "<html></html>")
    _escrever(tmp_path, "sobre.html", "<html></html>")

    problemas = validar_consistencia(clusters, raiz=tmp_path)

    assert problemas == []


# ── Contagem por tipo (guias vs simuladores) ────────────────────────────

def test_contagem_separa_guias_de_simuladores(tmp_path):
    clusters = _clusters(tmp_path)
    cluster_a = clusters[0]  # 2 artigos, sem ferramentas

    assert contagem_str(cluster_a) == "2 guias"


def test_contagem_com_um_artigo_e_uma_ferramenta():
    from sincronizar_clusters import Cluster, Pagina

    cluster = Cluster(
        id="x", nome="X", descricao_curta="", icone="🔧", pillar="/p/x.html",
        paginas=[
            Pagina(slug="a.html", titulo="A", tipo="artigo", destaque=True),
            Pagina(slug="b.html", titulo="B", tipo="artigo", destaque=False),
            Pagina(slug="c.html", titulo="C", tipo="artigo", destaque=False),
            Pagina(slug="d.html", titulo="D", tipo="artigo", destaque=False),
            Pagina(slug="e.html", titulo="E", tipo="ferramenta", destaque=False),
        ],
        relacionados=[],
    )

    assert contagem_str(cluster) == "4 guias · 1 simulador"


# ── Regras de relevância de "relacionados" ──────────────────────────────

def test_relacionados_prioriza_irmaos_depois_clusters_relacionados(tmp_path):
    clusters = _clusters(tmp_path)
    cluster_a = clusters[0]

    resultado = artigos_relacionados(clusters, cluster_a, "artigo-1.html")

    slugs = [p.slug for p in resultado]
    assert slugs == ["artigo-2.html", "artigo-3.html"]  # irmão primeiro, depois cluster-b


def test_relacionados_nunca_inclui_a_propria_pagina(tmp_path):
    clusters = _clusters(tmp_path)
    cluster_a = clusters[0]

    resultado = artigos_relacionados(clusters, cluster_a, "artigo-1.html")

    assert "artigo-1.html" not in [p.slug for p in resultado]


# ── Secção final: dois blocos separados ─────────────────────────────────

def test_render_relacionados_separa_irmaos_de_cross_cluster(tmp_path):
    from sincronizar_clusters import render_relacionados

    clusters = _clusters(tmp_path)
    cluster_a = clusters[0]

    html = render_relacionados(clusters, cluster_a, "artigo-1.html")

    pos_titulo_irmaos = html.index("Outros artigos deste cluster")
    pos_artigo2 = html.index("Artigo 2")
    pos_titulo_cross = html.index("Pode também interessar")
    pos_artigo3 = html.index("Artigo 3")
    pos_noticias = html.index("/noticias.html")

    assert pos_titulo_irmaos < pos_artigo2 < pos_titulo_cross < pos_artigo3 < pos_noticias


def test_render_relacionados_omite_cabecalho_sem_itens(tmp_path):
    from sincronizar_clusters import render_relacionados

    clusters = _clusters(tmp_path)
    cluster_b = clusters[1]  # sem irmãos (1 só página) nem relacionados[]

    html = render_relacionados(clusters, cluster_b, "artigo-3.html")

    assert "Outros artigos deste cluster" not in html
    assert "Pode também interessar" not in html
    assert "/noticias.html" in html


# ── Referência a clusters.css ────────────────────────────────────────────

def test_injeta_referencia_clusters_css_num_artigo_membro(tmp_path):
    clusters = _clusters(tmp_path)
    caminho = _escrever(tmp_path, "artigo-1.html", _ARTIGO_COM_MARCADORES)

    processar_pagina(caminho, clusters, raiz=tmp_path)

    conteudo = caminho.read_text(encoding="utf-8")
    assert conteudo.count("/assets/css/clusters.css") == 1
    assert conteudo.index("clusters.css") < conteudo.index("</head>")


def test_clusters_css_nao_duplica_em_pagina_ja_com_referencia(tmp_path):
    clusters = _clusters(tmp_path)
    pagina_com_css = _ARTIGO_COM_MARCADORES.replace(
        "<head><title>Artigo 1</title></head>",
        '<head><title>Artigo 1</title><link rel="stylesheet" href="/assets/css/clusters.css"></head>',
    )
    caminho = _escrever(tmp_path, "artigo-1.html", pagina_com_css)

    processar_pagina(caminho, clusters, raiz=tmp_path)

    conteudo = caminho.read_text(encoding="utf-8")
    assert conteudo.count("/assets/css/clusters.css") == 1
