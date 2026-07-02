#!/usr/bin/env python3
"""Migração única de noticias.html (HTML como base) para data/noticias.json
(fonte de verdade) — Fase 1 da reformulação do sistema de notícias.

NÃO corre no pipeline diário — é uma ferramenta de sessão manual, corrida
uma única vez. Depois da migração, `gerar_noticias.py` já não lê o HTML
para saber o que já foi publicado, só o JSON.

Faz limpeza ao migrar:
- descarta registos vazios/corrompidos (sem título, sem data ou com
  href="#" — nunca representam uma notícia real)
- deduplica por URL normalizado OU título semelhante, mantendo sempre a
  ocorrência com a data mais antiga (a primeira publicação real)

    python scripts/migrar_noticias.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gerar_noticias import (  # noqa: E402
    RAIZ,
    NOTICIAS_JSON,
    ItemNoticia,
    detectar_cluster,
    encontrar_duplicado,
    guardar_itens,
    separar_titulo_e_fonte,
)

NOTICIAS_HTML = RAIZ / "noticias.html"

MESES_ABREV_IDX = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}

_REGEX_ARTICLE = re.compile(r'<article\s+class="([^"]+)"\s+data-cat="([^"]*)">([\s\S]*?)</article>')


def _parse_data_dd_mmm_aaaa(texto: str) -> Optional[str]:
    """'23 Jun 2026' (maiúscula/minúscula indiferente) -> '2026-06-23'."""
    m = re.match(r"(\d{1,2})\s+([A-Za-zçÇ]{3})\w*\s+(\d{4})", texto.strip())
    if not m:
        return None
    dia, mes_abrev, ano = m.group(1), m.group(2).lower(), m.group(3)
    mes = MESES_ABREV_IDX.get(mes_abrev)
    if not mes:
        return None
    return f"{ano}-{mes:02d}-{int(dia):02d}"


def _extrair_bloco_marcado(conteudo: str, inicio: str, fim: str) -> str:
    m = re.search(rf"<!-- {re.escape(inicio)} -->([\s\S]*?)<!-- {re.escape(fim)} -->", conteudo)
    return m.group(1) if m else ""


def extrair_itens_legado(conteudo_html: str) -> Tuple[List[ItemNoticia], int]:
    """Percorre o destaque actual + todo o arquivo (nos dois formatos de
    card que coexistem hoje: `arquivo-card`/`destaque-card`, gerados pelo
    script, e `noticia-card`, herdado de antes do script existir) e
    devolve (itens válidos, nº de blocos `<article>` vazios/corrompidos
    descartados — ex.: o placeholder "Notícia anterior" sem data nem
    URL, deixado por um bug antigo do extractor do destaque)."""
    itens: List[ItemNoticia] = []
    invalidos = 0

    bloco_destaque = _extrair_bloco_marcado(conteudo_html, "DESTAQUE-INICIO", "DESTAQUE-FIM")
    bloco_arquivo = _extrair_bloco_marcado(conteudo_html, "ARQUIVO-INICIO", "ARQUIVO-FIM")

    # O destaque não usa <article class="..." data-cat="...">; adaptar.
    m_destaque = re.search(
        r'<article class="destaque-card" data-cat="([^"]*)">([\s\S]*?)</article>',
        bloco_destaque,
    )
    blocos = []
    if m_destaque:
        blocos.append(("destaque-card", m_destaque.group(1), m_destaque.group(2)))
    blocos += [
        (m.group(1), m.group(2), m.group(3))
        for m in _REGEX_ARTICLE.finditer(bloco_arquivo)
    ]

    for classe, categoria, corpo in blocos:
        item = _extrair_item_de_corpo(classe, categoria, corpo)
        if item is not None:
            itens.append(item)
        else:
            invalidos += 1

    return itens, invalidos


def _extrair_item_de_corpo(classe: str, categoria: str, corpo: str) -> Optional[ItemNoticia]:
    if "arquivo-card" in classe or "destaque-card" in classe:
        titulo_m = re.search(r'class="(?:arquivo|destaque)-titulo">(.*?)</h[23]>', corpo, re.DOTALL)
        resumo_m = re.search(r'class="(?:arquivo|destaque)-resumo">(.*?)</p>', corpo, re.DOTALL)
        link_m = re.search(r'class="(?:arquivo|destaque)-link"[^>]*href="([^"]*)"', corpo)
        if not link_m:
            link_m = re.search(r'href="([^"]*)"[^>]*class="(?:arquivo|destaque)-link"', corpo)
        data_m = re.search(r'datetime="([^"]*)"', corpo)

        titulo_bruto = _limpar(titulo_m.group(1)) if titulo_m else ""
        resumo_bruto = _limpar(resumo_m.group(1)) if resumo_m else ""
        resumo_bruto = resumo_bruto[:-1] if resumo_bruto.endswith("…") else resumo_bruto
        url = link_m.group(1) if link_m else ""
        data_iso = data_m.group(1) if data_m else ""

    elif "noticia-card" in classe:
        titulo_m = re.search(r'<h3>(.*?)</h3>', corpo, re.DOTALL)
        resumo_m = re.search(r'class="card-resumo">(.*?)</p>', corpo, re.DOTALL)
        link_m = re.search(r'class="card-fonte"[^>]*href="([^"]*)"', corpo)
        if not link_m:
            link_m = re.search(r'href="([^"]*)"[^>]*class="card-fonte"', corpo)
        data_m = re.search(r'class="card-data">(.*?)</span>', corpo)

        titulo_bruto = _limpar(titulo_m.group(1)) if titulo_m else ""
        resumo_bruto = _limpar(resumo_m.group(1)) if resumo_m else ""
        url = link_m.group(1) if link_m else ""
        data_iso = _parse_data_dd_mmm_aaaa(data_m.group(1)) if data_m else None
        data_iso = data_iso or ""
    else:
        return None

    if not titulo_bruto or not data_iso or not url or url == "#":
        return None  # registo vazio/corrompido (ex.: placeholder "Notícia anterior")

    titulo, fonte_nome = separar_titulo_e_fonte(titulo_bruto)
    if not fonte_nome:
        fonte_nome = _dominio_de_url(url)

    return ItemNoticia(
        data_iso=data_iso,
        titulo=titulo,
        fonte_nome=fonte_nome,
        url=url,
        resumo=resumo_bruto,
        categoria=categoria or "apoios",
        cluster_id=detectar_cluster(titulo, resumo_bruto),
    )


def _dominio_de_url(url: str) -> str:
    if url.startswith("/"):
        return "Tens Direito"
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else url


def _limpar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip()


def deduplicar_mantendo_mais_antiga(itens: List[ItemNoticia]) -> Tuple[List[ItemNoticia], List[Tuple[ItemNoticia, str]]]:
    """Ordena por data ASC (título como desempate) e mantém só a primeira
    ocorrência de cada grupo de duplicados — que, por construção da
    ordenação, é sempre a de data mais antiga."""
    por_data_asc = sorted(itens, key=lambda i: (i.data_iso, i.titulo))
    mantidos: List[ItemNoticia] = []
    removidos: List[Tuple[ItemNoticia, str]] = []
    for item in por_data_asc:
        duplicado = encontrar_duplicado(item.titulo, item.url, mantidos)
        if duplicado is not None:
            removidos.append((item, duplicado.data_iso))
        else:
            mantidos.append(item)
    return mantidos, removidos


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra noticias.html para data/noticias.json (corre uma vez)")
    parser.add_argument("--dry-run", action="store_true", help="mostra o antes/depois sem escrever noticias.json")
    args = parser.parse_args()

    if NOTICIAS_JSON.exists():
        print(f"AVISO: {NOTICIAS_JSON} já existe — a migração é para correr uma única vez. A parar.")
        return 1

    conteudo = NOTICIAS_HTML.read_text(encoding="utf-8")
    brutos, invalidos = extrair_itens_legado(conteudo)
    mantidos, removidos = deduplicar_mantendo_mais_antiga(brutos)

    print("=== Migração noticias.html → data/noticias.json ===")
    print(f"Blocos <article> vazios/corrompidos descartados: {invalidos}")
    print(f"Itens válidos encontrados no HTML: {len(brutos)}")
    print(f"Duplicados removidos: {len(removidos)}")
    for item, data_mantida in removidos:
        print(f"  - descartado ({item.data_iso}): {item.titulo[:70]} — mantida a ocorrência de {data_mantida}")
    print(f"Itens finais (únicos): {len(mantidos)}")
    for item in sorted(mantidos, key=lambda i: i.data_iso, reverse=True):
        print(f"  - {item.data_iso} [{item.categoria}] {item.titulo[:70]} — {item.fonte_nome}")

    if args.dry_run:
        print("\n--dry-run: data/noticias.json NÃO foi escrito.")
        return 0

    guardar_itens(mantidos)
    print(f"\nEscrito {NOTICIAS_JSON}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
