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


def main():
    print("=" * 70)
    print("DIAGNÓSTICO DE FEEDS — sistema de notícias")
    print("=" * 70)

    todas_entradas = []

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
        print(f"n.º entradas: {len(feed.entries)}")

        for e in feed.entries[:15]:
            e["_feed_url"] = url
            todas_entradas.append(e)
            item = gn.construir_item_de_entry(e)
            score = gn.score_entry(e)
            print(
                f"  [{item.data_iso}] score={score:2d} cat={item.categoria:10s} "
                f"cluster={str(item.cluster_id):28s} | {item.titulo[:90]}"
            )

    print("\n" + "=" * 70)
    print("BUSCA POR 'ABONO' EM TODOS OS FEEDS")
    print("=" * 70)
    encontrados = [
        e for e in todas_entradas
        if "abono" in (e.get("title", "") + " " + e.get("summary", "")).lower()
    ]
    if not encontrados:
        print("NENHUMA entrada com 'abono' encontrada em nenhum feed configurado.")
    else:
        for e in encontrados:
            item = gn.construir_item_de_entry(e)
            score = gn.score_entry(e)
            print(f"  [{item.data_iso}] score={score} feed={e['_feed_url']}")
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
