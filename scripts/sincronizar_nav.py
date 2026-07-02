#!/usr/bin/env python3
"""
scripts/sincronizar_nav.py

Fase 4 da reorganização da arquitectura de informação: navegação
principal única, gerada a partir de `data/clusters.json` (dropdown
"Apoios") e injectada entre marcadores próprios — mesmo padrão de
`sincronizar_clusters.py` e `inserir_botao_partilhar.py`.

    <!-- NAV:INICIO -->
    <!-- NAV:FIM -->

Duas fases de funcionamento:

1. **Bootstrap** (só da primeira vez, por página): quando uma página
   ainda não tem os marcadores, tenta detectar e substituir a nav
   antiga por eles, com duas heurísticas (nunca inventa uma terceira):
   - Padrão A: `<div class="nav-wrap">...</div>` autocontido
     (index.html, simulador-abono.html)
   - Padrão B: `<header>...</header>` seguido, opcionalmente, de
     `<div class="mobile-menu" ...>...</div>` (a maioria dos artigos e
     pillar pages)
   Se nenhum padrão for reconhecido com segurança — incluindo o caso
   em que `<header>` contém um `<h1>` (sinal de estrutura atípica que
   arriscaria apagar conteúdo do artigo) — a página é reportada e
   NÃO é tocada.
2. **Sincronização** (idempotente): com os marcadores já presentes,
   substitui só o interior deles pelo HTML actual.

    python scripts/sincronizar_nav.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sincronizar_clusters import RAIZ, carregar_clusters, encontrar_paginas, EXCLUIDAS as _NAO_USADO  # noqa: F401
from sincronizar_clusters import Cluster, CLUSTERS_JSON

MARCADOR_NAV = ("NAV:INICIO", "NAV:FIM")

NVLABS_BADGE = """      <!-- NVLABS:HEADER:INICIO -->
      <div class="nv-labs-badge" aria-label="An NV Labs project" title="An NV Labs project">
        <svg class="nv-labs-light" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" role="img" aria-label="NV Labs">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="150" y="80" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="52" font-weight="bold" fill="#0b131f" text-anchor="middle" letter-spacing="2">NV</text>
  <line x1="105" y1="102" x2="195" y2="102" stroke="#1ea3b2" stroke-width="4" stroke-linecap="round"/>
  <text x="150" y="145" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="normal" fill="#0b131f" text-anchor="middle" letter-spacing="8">Labs</text>
</svg>
        <svg class="nv-labs-dark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" role="img" aria-label="NV Labs">
  <rect width="100%" height="100%" rx="12" fill="#0b131f"/>
  <text x="150" y="80" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="52" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="2">NV</text>
  <line x1="105" y1="102" x2="195" y2="102" stroke="#1ea3b2" stroke-width="4" stroke-linecap="round"/>
  <text x="150" y="145" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="normal" fill="#ffffff" text-anchor="middle" letter-spacing="8">Labs</text>
</svg>
      </div>
      <!-- NVLABS:HEADER:FIM -->"""

REFERENCIAS_HEAD = (
    '  <link rel="stylesheet" href="/assets/css/nav.css">\n'
    '  <script src="/assets/js/nav.js" defer></script>\n'
    '  <script src="/scripts/pesquisa.js" defer></script>\n'
)

_REGEX_NAV_WRAP = re.compile(r'<div class="nav-wrap">[\s\S]*?\n  </div>\n')
_REGEX_HEADER = re.compile(r'<header>[\s\S]*?</header>')
_REGEX_MOBILE_MENU_SEGUINTE = re.compile(r'\A\s*<div class="(?:mobile-menu|nav-mobile-menu)"[\s\S]*?</div>')
_REGEX_HEAD_FECHO = re.compile(r"</head\s*>", re.IGNORECASE)


@dataclass(frozen=True)
class Resultado:
    ficheiro: str
    alterado: bool
    motivo: str


def render_dropdown_apoios(clusters: List[Cluster]) -> str:
    itens = [f'            <a href="{c.pillar}" role="menuitem">{c.nome}</a>' for c in clusters]
    return "\n".join(itens)


def render_mobile_apoios(clusters: List[Cluster]) -> str:
    itens = [f'    <a href="{c.pillar}" class="nav-mobile-sub">{c.nome}</a>' for c in clusters]
    return "\n".join(itens)


def render_nav(clusters: List[Cluster]) -> str:
    return f"""<div class="nav-wrap">
    <nav>
      <a href="/" class="logo" aria-label="Tens Direito — página inicial">
        <svg width="34" height="34" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect width="36" height="36" rx="9" fill="#0F766E"/>
          <path d="M9 18 L16 25 L27 11" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="logo-text"><span class="tens">Tens </span><span class="direito">Direito</span></div>
      </a>
{NVLABS_BADGE}

      <div class="nav-links">
        <div class="nav-dropdown" id="navApoiosDropdown">
          <button class="nav-dropdown-btn" type="button" aria-haspopup="true" aria-expanded="false">Apoios</button>
          <div class="nav-dropdown-menu" role="menu">
{render_dropdown_apoios(clusters)}
          </div>
        </div>
        <a href="/comecar-aqui.html">Começa aqui</a>
        <a href="/noticias.html">Notícias</a>
      </div>

      <div class="nav-search" role="search">
        <input type="search" id="campo-pesquisa-nav" placeholder="Pesquisar…" aria-label="Pesquisar" autocomplete="off"
          oninput="mostrarResultados(pesquisar(this.value), this.value, 'resultados-pesquisa-nav')">
        <div id="resultados-pesquisa-nav" class="nav-search-resultados"></div>
      </div>

      <button class="nav-toggle" type="button" aria-label="Abrir menu" aria-expanded="false">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </nav>

    <div class="nav-mobile-menu" id="navMobileMenu" role="navigation" aria-label="Menu mobile">
      <div class="nav-search nav-search-movel" role="search">
        <input type="search" id="campo-pesquisa-nav-movel" placeholder="Pesquisar…" aria-label="Pesquisar" autocomplete="off"
          oninput="mostrarResultados(pesquisar(this.value), this.value, 'resultados-pesquisa-nav-movel')">
        <div id="resultados-pesquisa-nav-movel" class="nav-search-resultados"></div>
      </div>
      <span class="nav-mobile-label">Apoios</span>
{render_mobile_apoios(clusters)}
      <a href="/comecar-aqui.html">Começa aqui</a>
      <a href="/noticias.html">Notícias</a>
    </div>
  </div>"""


def _substituir_bloco(conteudo: str, marca: Tuple[str, str], novo_interior: str) -> Optional[str]:
    inicio, fim = marca
    padrao = re.compile(rf"(<!-- {re.escape(inicio)} -->)([\s\S]*?)(<!-- {re.escape(fim)} -->)")
    if not padrao.search(conteudo):
        return None
    return padrao.sub(lambda m: f"{m.group(1)}\n{novo_interior}\n{m.group(3)}", conteudo)


def _garantir_referencias_head(conteudo: str) -> str:
    faltam = [ref for ref in ("/assets/css/nav.css", "/assets/js/nav.js", "/scripts/pesquisa.js") if ref not in conteudo]
    if not faltam:
        return conteudo
    match = _REGEX_HEAD_FECHO.search(conteudo)
    if not match:
        return conteudo
    pos = match.start()
    return conteudo[:pos] + REFERENCIAS_HEAD + conteudo[pos:]


def bootstrap_nav(conteudo: str) -> Tuple[Optional[str], str]:
    """Detecta e substitui a nav antiga pelos marcadores NAV:INICIO/FIM.
    Devolve (None, motivo) se não for seguro aplicar automaticamente —
    a página fica para tratamento manual antes de correr o script."""
    if f"<!-- {MARCADOR_NAV[0]} -->" in conteudo:
        return conteudo, "já tem marcador"

    m = _REGEX_NAV_WRAP.search(conteudo)
    if m:
        novo = conteudo[:m.start()] + f"<!-- {MARCADOR_NAV[0]} -->\n<!-- {MARCADOR_NAV[1]} -->\n" + conteudo[m.end():]
        return novo, "bootstrap: padrão nav-wrap"

    m = _REGEX_HEADER.search(conteudo)
    if m:
        if "<h1" in m.group(0):
            return None, "header contém <h1> — estrutura atípica, requer intervenção manual antes do bootstrap"
        fim = m.end()
        m_mobile = _REGEX_MOBILE_MENU_SEGUINTE.match(conteudo[fim:])
        if m_mobile:
            fim += m_mobile.end()
        novo = conteudo[:m.start()] + f"<!-- {MARCADOR_NAV[0]} -->\n<!-- {MARCADOR_NAV[1]} -->" + conteudo[fim:]
        return novo, "bootstrap: padrão header"

    return None, "nenhum padrão de nav reconhecido — requer intervenção manual"


def processar_pagina(caminho: Path, clusters: List[Cluster], *, escrever: bool = True) -> Resultado:
    nome = caminho.name
    conteudo_original = caminho.read_text(encoding="utf-8")

    conteudo, motivo_bootstrap = bootstrap_nav(conteudo_original)
    if conteudo is None:
        return Resultado(nome, False, motivo_bootstrap)

    novo = _substituir_bloco(conteudo, MARCADOR_NAV, render_nav(clusters))
    if novo is None:
        return Resultado(nome, False, "marcador NAV em falta após bootstrap — não deveria acontecer")
    conteudo = _garantir_referencias_head(novo)

    if conteudo == conteudo_original:
        return Resultado(nome, False, "já sincronizado — sem alterações")

    if escrever:
        caminho.write_text(conteudo, encoding="utf-8")
    sufixo = "" if escrever else " (dry-run, não escrito)"
    return Resultado(nome, True, f"sincronizado [{motivo_bootstrap}]{sufixo}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza a navegação principal a partir de data/clusters.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apenas", nargs="*", help="processar só estes ficheiros (nomes, ex.: rsi.html index.html)")
    args = parser.parse_args()
    escrever = not args.dry_run

    clusters = carregar_clusters(CLUSTERS_JSON)

    paginas = encontrar_paginas()
    if args.apenas:
        paginas = [p for p in paginas if p.name in args.apenas]

    resultados = [processar_pagina(p, clusters, escrever=escrever) for p in paginas]

    alterados = [r for r in resultados if r.alterado]
    manuais = [r for r in resultados if not r.alterado and "manual" in r.motivo]

    print(f"=== Sincronização de nav {'(dry-run)' if args.dry_run else ''} ===")
    print(f"Páginas verificadas: {len(resultados)}")
    print(f"Páginas alteradas: {len(alterados)}")
    for r in resultados:
        if r.alterado:
            print(f"  - {r.ficheiro}: {r.motivo}")
    if manuais:
        print("\nRequerem intervenção manual antes do bootstrap:")
        for r in manuais:
            print(f"  - {r.ficheiro}: {r.motivo}")

    return 1 if manuais else 0


if __name__ == "__main__":
    sys.exit(main())
