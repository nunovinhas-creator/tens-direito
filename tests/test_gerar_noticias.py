"""
Testes para scripts/gerar_noticias.py — dedup, scoring com observabilidade,
ordenação/agrupamento por mês e renderização a partir de data/noticias.json.

Todos os testes isolam o sistema de ficheiros com `tmp_path` — nunca tocam
nos dados reais do repositório.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gerar_noticias import (
    ItemNoticia,
    SaudeFeed,
    agrupar_por_mes,
    carregar_itens,
    construir_item_de_entry,
    detect_category,
    detectar_cluster,
    encontrar_duplicado,
    guardar_itens,
    label_mes,
    normalizar_titulo,
    normalizar_url,
    ordenar_itens,
    registar_candidatos_log,
    registar_saude_feeds_hoje,
    regenerar_noticias_html,
    render_arquivo,
    render_destaque,
    score_entry,
    selecionar_vencedor,
    separar_titulo_e_fonte,
    sincronizar_saidas,
    titulos_semelhantes,
)

# Data de referência fixa para selecionar_vencedor() nestes testes — nunca
# datetime.now() real, que tornaria os testes dependentes de quando correm
# (as entradas fixture estão datadas "01 Jul 2026"; sem isto, o corte de
# recência rejeitá-las-ia silenciosamente passados 7 dias reais). Mesmo
# padrão de ANO/MES fixos em tests/test_verificar_datas.py.
HOJE_TESTE = datetime(2026, 7, 2, tzinfo=timezone.utc)


def _item(data_iso, titulo, url="https://exemplo.pt/a", **kw):
    return ItemNoticia(
        data_iso=data_iso, titulo=titulo, fonte_nome=kw.get("fonte_nome", "Exemplo"),
        url=url, resumo=kw.get("resumo", "Resumo."), categoria=kw.get("categoria", "apoios"),
        cluster_id=kw.get("cluster_id"),
    )


def _entry(titulo, resumo="", link="https://exemplo.pt/x", published="Wed, 01 Jul 2026 10:00:00 GMT", feed="feedA"):
    return {"title": titulo, "summary": resumo, "link": link, "published": published, "_feed_url": feed}


# ── Normalização ───────────────────────────────────────────────────────────

def test_normalizar_titulo_minusculas_sem_pontuacao():
    assert normalizar_titulo("PSU: o que MUDA, afinal?!") == "psu o que muda afinal"


def test_normalizar_url_remove_espacos_e_fragmento():
    assert normalizar_url("  https://exemplo.pt/a?x=1#topo  ") == "https://exemplo.pt/a?x=1"


def test_separar_titulo_e_fonte():
    titulo, fonte = separar_titulo_e_fonte("Pensões e apoios em julho - Notícias ao Minuto")
    assert titulo == "Pensões e apoios em julho"
    assert fonte == "Notícias ao Minuto"


def test_separar_titulo_e_fonte_sem_separador():
    titulo, fonte = separar_titulo_e_fonte("PSU aprovada no Parlamento")
    assert titulo == "PSU aprovada no Parlamento"
    assert fonte == ""


# ── Dedup ────────────────────────────────────────────────────────────────

def test_titulos_semelhantes_identicos():
    assert titulos_semelhantes("psu aprovada", "psu aprovada") is True


def test_titulos_semelhantes_quase_iguais():
    a = normalizar_titulo("Pensões, subsídios e outros apoios: descubra já quando os recebe em julho")
    b = normalizar_titulo("Pensões subsídios e outros apoios descubra já quando os recebe em julho!")
    assert titulos_semelhantes(a, b) is True


def test_titulos_diferentes_nao_sao_semelhantes():
    a = normalizar_titulo("Candidaturas à ASE abrem em setembro")
    b = normalizar_titulo("Bolsas de mérito 2026 candidaturas abertas")
    assert titulos_semelhantes(a, b) is False


def test_encontrar_duplicado_por_url_identico():
    existentes = [_item("2026-06-20", "Título A", url="https://exemplo.pt/artigo-1")]
    dup = encontrar_duplicado("Título completamente diferente", "https://exemplo.pt/artigo-1", existentes)
    assert dup is not None


def test_encontrar_duplicado_por_titulo_semelhante_url_diferente():
    """Simula o Google News a dar um link opaco diferente ao mesmo artigo."""
    existentes = [_item("2026-06-20", "Pensões e apoios em julho", url="https://news.google.com/rss/articles/AAA")]
    dup = encontrar_duplicado("Pensões e apoios em julho", "https://news.google.com/rss/articles/BBB", existentes)
    assert dup is not None


def test_url_generica_sozinha_nao_e_duplicado():
    """Duas notícias diferentes que citam a homepage genérica do mesmo
    domínio como fonte (ex.: 'seg-social.pt') não são a mesma notícia —
    bug real encontrado na migração (ASE vs Bolsas de mérito, ambas
    apontando para dge.mec.pt)."""
    existentes = [_item("2026-06-18", "Bolsas de mérito 2026: candidaturas abertas", url="https://www.dge.mec.pt")]
    dup = encontrar_duplicado("Candidaturas à ASE abrem em setembro", "https://www.dge.mec.pt", existentes)
    assert dup is None


def test_url_generica_mas_titulo_semelhante_e_duplicado():
    existentes = [_item("2026-06-18", "Bolsas de mérito 2026: candidaturas abertas", url="https://www.dge.mec.pt")]
    dup = encontrar_duplicado("Bolsas de mérito 2026 candidaturas abertas!", "https://www.dge.mec.pt", existentes)
    assert dup is not None


def test_sem_duplicado_quando_titulo_e_url_diferentes():
    existentes = [_item("2026-06-18", "Bolsas de mérito 2026", url="https://exemplo.pt/a")]
    dup = encontrar_duplicado("Subsídio de desemprego: novas regras", "https://exemplo.pt/b", existentes)
    assert dup is None


# ── Scoring e classificação ─────────────────────────────────────────────

def test_score_entry_conta_keywords():
    e = _entry("Abono de família e subsídio de desemprego sobem em 2026")
    assert score_entry(e) >= 2


def test_score_entry_stopword_da_score_negativo():
    e = _entry("Publicidade: apoios sociais com desconto")
    assert score_entry(e) == -1


def test_detect_category_educacao():
    assert detect_category(_entry("Bolsas de mérito e manuais escolares 2026")) == "educacao"


def test_detectar_cluster_psu():
    assert detectar_cluster("PSU aprovada no parlamento", "") == "prestacao-social-unica"


def test_detectar_cluster_sem_correspondencia():
    assert detectar_cluster("Notícia qualquer sem palavras-chave conhecidas", "") is None


# ── Selecção com dedup e observabilidade ──────────────────────────────────

def test_selecionar_vencedor_escolhe_melhor_score():
    entries = [
        _entry("Notícia sem relevância nenhuma"),
        _entry("Abono de família e subsídio de desemprego sobem"),
    ]
    resultado = selecionar_vencedor(entries, [], hoje=HOJE_TESTE)
    assert resultado.vencedor is not None
    assert "Abono" in resultado.vencedor.titulo


def test_selecionar_vencedor_nenhum_candidato_relevante():
    entries = [_entry("Notícia qualquer sobre futebol")]
    resultado = selecionar_vencedor(entries, [], hoje=HOJE_TESTE)
    assert resultado.vencedor is None


def test_selecionar_vencedor_rejeita_duplicado_e_escolhe_seguinte():
    existentes = [_item("2026-06-20", "Abono de família sobe em 2026", url="https://exemplo.pt/ja-existe")]
    entries = [
        # duplicado (mesmo título) mas com score mais alto que a alternativa,
        # para garantir que é avaliado primeiro e realmente testa a rejeição
        _entry(
            "Abono de família sobe em 2026",
            resumo="Aumento do subsídio de desemprego e da prestação também prevista.",
            link="https://exemplo.pt/outro-link",
        ),
        _entry("Subsídio de desemprego: novas regras do IEFP", link="https://exemplo.pt/novo"),
    ]
    resultado = selecionar_vencedor(entries, existentes, hoje=HOJE_TESTE)
    assert resultado.vencedor is not None
    assert "Subsídio de desemprego" in resultado.vencedor.titulo
    assert len(resultado.rejeitados) == 1
    assert "duplicado de 2026-06-20" in resultado.rejeitados[0].motivo


def test_selecionar_vencedor_todos_duplicados_resulta_em_nenhum():
    existentes = [_item("2026-06-20", "Abono de família sobe em 2026", url="https://exemplo.pt/ja-existe")]
    entries = [_entry("Abono de família sobe em 2026", link="https://exemplo.pt/outro-link")]
    resultado = selecionar_vencedor(entries, existentes, hoje=HOJE_TESTE)
    assert resultado.vencedor is None
    assert len(resultado.rejeitados) == 1


def test_selecionar_vencedor_regista_candidatos_por_feed():
    entries = [_entry("Abono de família sobe", feed="feedA"), _entry("RSI muda em 2026", feed="feedB")]
    resultado = selecionar_vencedor(entries, [], hoje=HOJE_TESTE)
    assert resultado.candidatos_por_feed == {"feedA": 1, "feedB": 1}


def test_selecionar_vencedor_top3_ordenado_por_score():
    entries = [
        _entry("apoio"),  # score baixo
        _entry("apoio subsídio abono rsi desemprego"),  # score alto
        _entry("apoio subsídio"),  # score médio
    ]
    resultado = selecionar_vencedor(entries, [], hoje=HOJE_TESTE)
    scores = [c.score for c in resultado.top_candidatos]
    assert scores == sorted(scores, reverse=True)


def test_construir_item_de_entry_usa_data_real_e_separa_fonte():
    e = _entry("PSU aprovada - Observador", resumo="Resumo qualquer", published="Wed, 24 Jun 2026 08:00:00 GMT")
    item = construir_item_de_entry(e)
    assert item.data_iso == "2026-06-24"
    assert item.titulo == "PSU aprovada"
    assert item.fonte_nome == "Observador"


# ── Ordenação e agrupamento por mês ───────────────────────────────────────

def test_ordenar_itens_data_desc():
    itens = [_item("2026-06-10", "A"), _item("2026-07-01", "B"), _item("2026-06-20", "C")]
    ordenados = ordenar_itens(itens)
    assert [i.data_iso for i in ordenados] == ["2026-07-01", "2026-06-20", "2026-06-10"]


def test_ordenar_itens_desempate_por_titulo_deterministico():
    itens = [_item("2026-06-10", "Zebra"), _item("2026-06-10", "Abelha")]
    ordenados = ordenar_itens(itens)
    assert [i.titulo for i in ordenados] == ["Zebra", "Abelha"]  # título desc, sempre a mesma ordem


def test_agrupar_por_mes():
    itens = ordenar_itens([_item("2026-07-01", "A"), _item("2026-06-20", "B"), _item("2026-06-10", "C")])
    grupos = agrupar_por_mes(itens)
    assert [chave for chave, _ in grupos] == ["2026-07", "2026-06"]
    assert len(grupos[1][1]) == 2


def test_label_mes():
    assert label_mes("2026-07") == "Julho 2026"


# ── Renderização ───────────────────────────────────────────────────────────

def test_render_destaque_contem_data_real_e_link_externo():
    html_out = render_destaque(_item("2026-07-01", "PSU aprovada", url="https://exemplo.pt/psu"))
    assert "1 jul. 2026" in html_out
    assert 'href="https://exemplo.pt/psu"' in html_out
    assert "DESTAQUE-INICIO" in html_out and "DESTAQUE-FIM" in html_out


def test_render_arquivo_exclui_o_mais_recente_e_agrupa_por_mes():
    itens = ordenar_itens([_item("2026-07-01", "Mais recente"), _item("2026-06-20", "Antiga junho"), _item("2026-05-15", "Antiga maio")])
    html_out = render_arquivo(itens)
    assert "Mais recente" not in html_out  # esse vai para o destaque, não para o arquivo
    assert "Antiga junho" in html_out and "Antiga maio" in html_out
    assert "Junho 2026" in html_out
    assert "Maio 2026" in html_out


# ── Persistência JSON ──────────────────────────────────────────────────────

def test_guardar_e_carregar_itens_round_trip(tmp_path):
    caminho = tmp_path / "noticias.json"
    itens = [_item("2026-06-20", "A"), _item("2026-07-01", "B")]
    guardar_itens(itens, caminho=caminho)
    carregados = carregar_itens(caminho=caminho)
    assert {i.titulo for i in carregados} == {"A", "B"}


def test_carregar_itens_sem_ficheiro_devolve_lista_vazia(tmp_path):
    assert carregar_itens(caminho=tmp_path / "nao-existe.json") == []


# ── Regeneração de noticias.html — marcadores, idempotência ───────────────

_NOTICIAS_HTML_BASE = """<!DOCTYPE html>
<html>
<body>
  <!-- DESTAQUE-INICIO -->
  <article class="destaque-card" data-cat="apoios"><h2 class="destaque-titulo">Antigo</h2></article>
  <!-- DESTAQUE-FIM -->
  <div class="cards-grid" id="cards-grid">
  <!-- ARQUIVO-INICIO -->
  <!-- ARQUIVO-FIM -->
  </div>
</body>
</html>
"""


def test_regenerar_noticias_html_idempotente(tmp_path):
    caminho = tmp_path / "noticias.html"
    caminho.write_text(_NOTICIAS_HTML_BASE, encoding="utf-8")
    itens = ordenar_itens([_item("2026-06-20", "Notícia B"), _item("2026-07-01", "Notícia A")])

    mudou1 = regenerar_noticias_html(itens, caminho=caminho)
    conteudo1 = caminho.read_text(encoding="utf-8")
    mudou2 = regenerar_noticias_html(itens, caminho=caminho)
    conteudo2 = caminho.read_text(encoding="utf-8")

    assert mudou1 is True
    assert mudou2 is False
    assert conteudo1 == conteudo2
    assert "Notícia A" in conteudo1  # destaque = mais recente
    assert "Notícia B" in conteudo1  # arquivo = resto


# ── sincronizar_saidas — resync de index.html + noticias.html a partir ────
# ── do JSON, independente de haver ou não notícia nova no dia (Bug 1) ────

_INDEX_HOME_BASE = """<!DOCTYPE html>
<html>
<body>
  <section class="noticia-section">
    <div class="noticia-grid">
    <!-- NOTICIA-HOME:INICIO -->
    <div class="noticia-card">
      <span class="badge-hoje">25 jun. 2026</span>
      <h3>Notícia antiga presa no marcador</h3>
      <p>Resumo antigo.</p>
      <a href="https://exemplo.pt/antiga" class="link-ler">Ler notícia completa →</a>
    </div>
    <!-- NOTICIA-HOME:FIM -->
    </div>
  </section>
</body>
</html>
"""


def test_sincronizar_saidas_atualiza_index_para_o_item_mais_recente(tmp_path):
    """Regressão do Bug 1: o bloco NOTICIA-HOME não pode ficar preso ao
    conteúdo antigo do marcador quando o JSON já tem itens mais
    recentes — falha se a homepage ficar atrás do JSON."""
    noticias_caminho = tmp_path / "noticias.html"
    noticias_caminho.write_text(_NOTICIAS_HTML_BASE, encoding="utf-8")
    index_caminho = tmp_path / "index.html"
    index_caminho.write_text(_INDEX_HOME_BASE, encoding="utf-8")

    itens = [_item("2026-06-20", "Antiga"), _item("2026-06-29", "A mais recente do JSON")]

    sincronizar_saidas(itens, noticias_caminho=noticias_caminho, index_caminho=str(index_caminho))

    conteudo_index = index_caminho.read_text(encoding="utf-8")
    assert "A mais recente do JSON" in conteudo_index
    assert "Notícia antiga presa no marcador" not in conteudo_index

    conteudo_noticias = noticias_caminho.read_text(encoding="utf-8")
    assert "A mais recente do JSON" in conteudo_noticias


def test_sincronizar_saidas_e_idempotente(tmp_path):
    noticias_caminho = tmp_path / "noticias.html"
    noticias_caminho.write_text(_NOTICIAS_HTML_BASE, encoding="utf-8")
    index_caminho = tmp_path / "index.html"
    index_caminho.write_text(_INDEX_HOME_BASE, encoding="utf-8")

    itens = [_item("2026-06-29", "Item único")]

    sincronizar_saidas(itens, noticias_caminho=noticias_caminho, index_caminho=str(index_caminho))
    conteudo1_index = index_caminho.read_text(encoding="utf-8")
    conteudo1_noticias = noticias_caminho.read_text(encoding="utf-8")

    sincronizar_saidas(itens, noticias_caminho=noticias_caminho, index_caminho=str(index_caminho))
    conteudo2_index = index_caminho.read_text(encoding="utf-8")
    conteudo2_noticias = noticias_caminho.read_text(encoding="utf-8")

    assert conteudo1_index == conteudo2_index
    assert conteudo1_noticias == conteudo2_noticias


def test_sincronizar_saidas_carrega_do_json_quando_itens_nao_dados(tmp_path, monkeypatch):
    """`sincronizar_saidas()` sem argumentos tem de ler o JSON do disco —
    é o que torna possível correr `--sync` como passo manual isolado."""
    import gerar_noticias

    noticias_json = tmp_path / "noticias.json"
    noticias_json.write_text(
        '{"itens": [{"data_iso": "2026-06-29", "titulo": "Do JSON em disco", '
        '"fonte_nome": "X", "url": "https://x.pt", "resumo": "r", "categoria": "apoios", "cluster_id": null}]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(gerar_noticias, "NOTICIAS_JSON", noticias_json)

    noticias_caminho = tmp_path / "noticias.html"
    noticias_caminho.write_text(_NOTICIAS_HTML_BASE, encoding="utf-8")
    index_caminho = tmp_path / "index.html"
    index_caminho.write_text(_INDEX_HOME_BASE, encoding="utf-8")

    sincronizar_saidas(noticias_caminho=noticias_caminho, index_caminho=str(index_caminho))

    assert "Do JSON em disco" in index_caminho.read_text(encoding="utf-8")


# ── Corte de recência (Fase 2, diagnóstico 2026-07-04) ────────────────────
# Casos reais capturados no workflow_dispatch de diagnóstico: um artigo de
# PSU de maio (score alto) tinha estado a vencer todos os dias em vez de
# notícias mais recentes e específicas (ex.: abono de família), porque a
# selecção não olhava a data — só ao score. Estes testes usam os títulos e
# datas reais encontrados nesse diagnóstico como fixtures.

def test_recencia_rejeita_artigo_antigo_mesmo_com_score_alto():
    hoje = datetime(2026, 7, 4, tzinfo=timezone.utc)
    entries = [
        _entry(
            "Governo aprova prestação social única. Quais são os 13 apoios agregados?",
            resumo="Prestação social única, apoio, apoios, subsídio, IAS.",
            published="Fri, 29 May 2026 10:00:00 GMT",
            feed="psu_pensoes",
        ),
        _entry(
            "Governo está a rever abono e alarga pagamento automático a mais famílias",
            published="Wed, 01 Jul 2026 14:55:00 GMT",
            feed="abono_familia",
        ),
    ]
    resultado = selecionar_vencedor(entries, [], hoje=hoje)
    assert resultado.vencedor is not None
    assert "abono" in resultado.vencedor.titulo.lower()
    assert any("antigo" in r.motivo for r in resultado.rejeitados)


def test_recencia_aceita_candidato_na_borda_da_janela():
    # janela de 7 dias a partir de 2026-07-04 -> limite é 2026-06-27 (incluído)
    hoje = datetime(2026, 7, 4, tzinfo=timezone.utc)
    entries = [_entry("Abono de família sobe este mês", published="Sat, 27 Jun 2026 10:00:00 GMT")]
    resultado = selecionar_vencedor(entries, [], hoje=hoje)
    assert resultado.vencedor is not None


def test_recencia_rejeita_um_dia_antes_da_borda():
    hoje = datetime(2026, 7, 4, tzinfo=timezone.utc)
    entries = [_entry("Abono de família notícia antiga", published="Fri, 26 Jun 2026 10:00:00 GMT")]
    resultado = selecionar_vencedor(entries, [], hoje=hoje)
    assert resultado.vencedor is None
    assert "antigo" in resultado.rejeitados[0].motivo


def test_recencia_janela_e_configuravel():
    hoje = datetime(2026, 7, 4, tzinfo=timezone.utc)
    entries = [_entry("Abono de família notícia de há 10 dias", published="Mon, 24 Jun 2026 10:00:00 GMT")]
    # com janela maior, o mesmo candidato passa a ser aceite
    resultado = selecionar_vencedor(entries, [], hoje=hoje, janela_recencia_dias=15)
    assert resultado.vencedor is not None


# ── Saúde dos feeds e log de candidatos (Fase 3) ──────────────────────────

def test_saude_feed_ok_quando_sem_bozo_e_com_entradas():
    s = SaudeFeed(nome="abono_familia", url="https://x", bozo=False, n_entradas=10)
    assert s.estado == "OK"
    assert s.motivo == ""


def test_saude_feed_morto_por_bozo_mesmo_com_entradas():
    """Caso real do DRE: HTTP 200 mas XML malformado — bozo=True. Nunca
    pode contar como OK só porque o HTTP respondeu."""
    s = SaudeFeed(nome="dre", url="https://x", bozo=True, n_entradas=0)
    assert s.estado == "MORTO"
    assert s.motivo == "erro_parsing_xml"


def test_saude_feed_morto_por_zero_entradas_sem_bozo():
    s = SaudeFeed(nome="x", url="https://x", bozo=False, n_entradas=0)
    assert s.estado == "MORTO"
    assert s.motivo == "sem_entradas"


def test_registar_saude_feeds_hoje_grava_snapshot(tmp_path):
    caminho = tmp_path / "feeds_saude_hoje.json"
    saude = [
        SaudeFeed(nome="abono_familia", url="https://x", bozo=False, n_entradas=10),
        SaudeFeed(nome="dre", url="https://y", bozo=True, n_entradas=0),
    ]
    registar_saude_feeds_hoje(saude, caminho=caminho, hoje="2026-07-04")
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert {d["nome"]: d["estado"] for d in dados} == {"abono_familia": "OK", "dre": "MORTO"}
    assert all(d["data"] == "2026-07-04" for d in dados)


def test_registar_candidatos_log_acrescenta_e_limita_historico(tmp_path):
    caminho = tmp_path / "noticias_candidatos.json"
    resultado = selecionar_vencedor(
        [_entry("Abono de família sobe", published="Wed, 01 Jul 2026 10:00:00 GMT", feed="abono_familia")],
        [], hoje=datetime(2026, 7, 2, tzinfo=timezone.utc),
    )
    saude = [SaudeFeed(nome="abono_familia", url="https://x", bozo=False, n_entradas=1)]

    registar_candidatos_log(resultado, saude, caminho=caminho, hoje="2026-07-01", limite_historico=2)
    registar_candidatos_log(resultado, saude, caminho=caminho, hoje="2026-07-02", limite_historico=2)
    registar_candidatos_log(resultado, saude, caminho=caminho, hoje="2026-07-03", limite_historico=2)

    historico = json.loads(caminho.read_text(encoding="utf-8"))
    assert len(historico) == 2  # limitado, o mais antigo (07-01) caiu fora
    assert [r["data"] for r in historico] == ["2026-07-02", "2026-07-03"]
    assert historico[-1]["vencedor"]["titulo"] == "Abono de família sobe"


def test_registar_candidatos_log_regista_nenhum_vencedor(tmp_path):
    caminho = tmp_path / "noticias_candidatos.json"
    resultado = selecionar_vencedor([_entry("Notícia irrelevante sobre futebol")], [], hoje=HOJE_TESTE)
    registar_candidatos_log(resultado, [], caminho=caminho, hoje="2026-07-02")
    historico = json.loads(caminho.read_text(encoding="utf-8"))
    assert historico[0]["vencedor"] is None
