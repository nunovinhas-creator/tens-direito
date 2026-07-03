#!/usr/bin/env python3
"""Script de diagnóstico TEMPORÁRIO — sessão de investigação do sistema de
notícias (2026-07-04). Corre num runner real via workflow_dispatch porque a
política de rede da sessão de desenvolvimento bloqueia news.google.com e
dre.pt. Apagado no fim da investigação, junto com o workflow que o invoca.

Para cada feed configurado em gerar_noticias.FEEDS:
  - HTTP status real (via requests, feedparser esconde isto às vezes)
  - feed.bozo (erro de parsing) e feed.bozo_exception
  - n.º de entradas devolvidas, data da mais recente
  - lista completa de título + data + score + categoria/cluster detectado

Também procura, em todas as entradas de todos os feeds, qualquer título que
mencione "abono" — para confirmar se a notícia de 2 de julho sobre abono de
família aparece nalgum feed configurado.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import feedparser  # noqa: E402
import requests  # noqa: E402

import gerar_noticias as gn  # noqa: E402

# Candidatos a feed novo/substituto — testados aqui antes de qualquer decisão
# (nenhum feed é adicionado ao gerar_noticias.py sem fetch real confirmado).
#
# Grupo A — pesquisa Google News por TEMA específico (um por tema do site),
# em vez do feed genérico onde estes temas ficam enterrados na posição 78+.
CANDIDATOS_TEMA = {
    "abono_familia": "https://news.google.com/rss/search?q=abono+de+fam%C3%ADlia+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "subsidio_desemprego": "https://news.google.com/rss/search?q=subs%C3%ADdio+de+desemprego+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "rsi": "https://news.google.com/rss/search?q=RSI+rendimento+social+de+inser%C3%A7%C3%A3o+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "psu_pensoes": "https://news.google.com/rss/search?q=presta%C3%A7%C3%A3o+social+%C3%BAnica+pens%C3%B5es+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "acao_social_escolar": "https://news.google.com/rss/search?q=a%C3%A7%C3%A3o+social+escolar+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "cuidador_informal": "https://news.google.com/rss/search?q=cuidador+informal+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "porta65_arrendamento": "https://news.google.com/rss/search?q=Porta+65+arrendamento+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
}

# Grupo B — fontes oficiais (Segurança Social/gov.pt) e substitutos para o
# DRE morto — todos palpites a confirmar por fetch real, nunca assumidos vivos.
CANDIDATOS_OFICIAIS = {
    "seg_social_rss": "https://www.seg-social.pt/rss",
    "gov_pt_comunicacao": "https://www.portugal.gov.pt/pt/gc25/comunicacao/rss",
    "dre_serie1_alt": "https://dre.pt/rss/serie1s.rss",
    "dre_rss_alt2": "https://diariodarepublica.pt/dr/rss",
}

# Grupo C — media generalista com RSS tipicamente estável (feed de publicação
# cronológica, não pesquisa por relevância — reduz o risco de "banco de
# artigos antigos" que afecta as pesquisas Google News).
CANDIDATOS_MEDIA = {
    "observador": "https://observador.pt/rss",
    "eco_sapo": "https://eco.sapo.pt/feed/",
}

CANDIDATOS = {**CANDIDATOS_TEMA, **CANDIDATOS_OFICIAIS, **CANDIDATOS_MEDIA}


def testar_candidatos():
    print("\n" + "=" * 70)
    print("CANDIDATOS A FEED NOVO/SUBSTITUTO — teste real")
    print("=" * 70)
    resumo = []
    for nome, url in CANDIDATOS.items():
        print(f"\n--- CANDIDATO [{nome}]: {url} ---")
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TensDireitoBot/1.0)"},
                timeout=20,
            )
            print(f"HTTP status: {resp.status_code}, bytes: {len(resp.content)}")
        except Exception as e:
            print(f"ERRO HTTP: {e}")
            resumo.append((nome, "ERRO_HTTP", 0, None))
            continue

        feed = feedparser.parse(url)
        print(f"bozo={feed.bozo} bozo_exception={getattr(feed, 'bozo_exception', None)}")
        print(f"n.º entradas: {len(feed.entries)}")

        if feed.bozo or not feed.entries:
            resumo.append((nome, f"MORTO (bozo={feed.bozo}, entradas={len(feed.entries)})", len(feed.entries), None))
            continue

        tem_abono = False
        mais_recente = None
        for e in feed.entries:
            texto = (e.get("title", "") + " " + e.get("summary", "")).lower()
            if "abono" in texto:
                tem_abono = True
            dt = gn.parse_date(e)
            if mais_recente is None or dt > mais_recente:
                mais_recente = dt

        for e in feed.entries[:8]:
            e["_feed_url"] = url
            item = gn.construir_item_de_entry(e)
            score = gn.score_entry(e)
            print(f"  [{item.data_iso}] score={score:2d} | {item.titulo[:90]}")

        resumo.append((nome, "VIVO", len(feed.entries), mais_recente, tem_abono))

    print("\n" + "=" * 70)
    print("RESUMO DOS CANDIDATOS")
    print("=" * 70)
    for linha in resumo:
        print(" ", linha)


def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE FEEDS — sistema de notícias")
    print("=" * 70)

    todas_entradas = []       # espelha fetch_entries() real (top 10/feed) — usado na simulação
    todas_entradas_completas = []  # TODAS as entradas devolvidas por cada feed (até 100) — só para a busca por "abono"

    for url in gn.FEEDS:
        print(f"\n--- FEED: {url} ---")
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; TensDireitoBot/1.0)"},
                timeout=20,
            )
            print(f"HTTP status: {resp.status_code}, bytes: {len(resp.content)}")
        except Exception as e:
            print(f"ERRO HTTP: {e}")
            continue

        feed = feedparser.parse(url)
        print(f"bozo={feed.bozo} bozo_exception={getattr(feed, 'bozo_exception', None)}")
        print(f"n.º entradas TOTAL devolvidas pelo feed: {len(feed.entries)}")

        for e in feed.entries:
            e["_feed_url"] = url
            todas_entradas_completas.append(e)

        print(f"  (mostrando as primeiras 15 de {len(feed.entries)} — fetch_entries() real só usa as 10 primeiras)")
        for e in feed.entries[:15]:
            todas_entradas.append(e)
            item = gn.construir_item_de_entry(e)
            score = gn.score_entry(e)
            print(
                f"  [{item.data_iso}] score={score:2d} cat={item.categoria:10s} "
                f"cluster={str(item.cluster_id):28s} | {item.titulo[:90]}"
            )

    print("\n" + "=" * 70)
    print(f"BUSCA POR 'ABONO' — em TODAS as {len(todas_entradas_completas)} entradas devolvidas pelos feeds (não só o top 10/15)")
    print("=" * 70)
    encontrados = [
        e for e in todas_entradas_completas
        if "abono" in (e.get("title", "") + " " + e.get("summary", "")).lower()
    ]
    if not encontrados:
        print("NENHUMA entrada com 'abono' encontrada em NENHUM feed configurado, mesmo olhando a todas as entradas devolvidas.")
    else:
        for e in encontrados:
            item = gn.construir_item_de_entry(e)
            score = gn.score_entry(e)
            # posição real dentro do feed de origem (0-based) — para saber se
            # fetch_entries() real (só top 10) alguma vez a veria
            feed_url = e["_feed_url"]
            posicao = [x for x in todas_entradas_completas if x["_feed_url"] == feed_url].index(e)
            print(f"  [{item.data_iso}] score={score} feed={feed_url}")
            print(f"    posição no feed: {posicao} (fetch_entries() real só vê posições 0-9)")
            print(f"    título: {item.titulo}")
            print(f"    resumo: {item.resumo[:150]}")
            print(f"    link: {item.url}")

    print("\n" + "=" * 70)
    print("SIMULAÇÃO DE SELECÇÃO COM O ESTADO ACTUAL DE data/noticias.json")
    print("=" * 70)
    itens_existentes = gn.carregar_itens()
    resultado = gn.selecionar_vencedor(todas_entradas, itens_existentes)
    gn.imprimir_relatorio(resultado)

    print("\n" + "=" * 70)
    print("TOP 15 CANDIDATOS POR SCORE (com data, para ver o efeito de recência)")
    print("=" * 70)
    candidatos = sorted(
        (
            (gn.score_entry(e), gn.construir_item_de_entry(e), e.get("_feed_url"))
            for e in todas_entradas
        ),
        key=lambda t: t[0],
        reverse=True,
    )
    for score, item, feed_url in candidatos[:15]:
        print(f"  score={score:2d} [{item.data_iso}] {item.titulo[:80]}")


if __name__ == "__main__":
    main()
    testar_candidatos()
