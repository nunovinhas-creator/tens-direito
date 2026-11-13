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

Também escreve a barra do topo — próximo pagamento + canal de WhatsApp —
entre marcadores próprios, logo a seguir ao link "Saltar para o conteúdo":

    <!-- BARRA-TOPO:INICIO -->
    <!-- BARRA-TOPO:FIM -->

Bootstrap: se faltarem, os marcadores são inseridos a seguir ao skip-link;
sem skip-link, ou com a barra antiga do calendário (`cal-topo`) ainda na
página, a página é reportada e NÃO é tocada. Só a parte fixa vive no HTML
(a mensagem do WhatsApp, visível sem JS); as datas vêm de
data/calendario_barra.json (escrito por atualizar_calendario.py) e são
lidas pelo nav.js — nunca escritas aqui, para nenhum workflow ter de
reescrever as páginas protegidas todos os meses (REGRA DE OURO). No gerador
de documentos a barra é estática (só WhatsApp, sem fetch nem evento GA4) —
garantia de rede-zero (ver PAGINAS_BARRA_ESTATICA).

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
MARCADOR_BARRA = ("BARRA-TOPO:INICIO", "BARRA-TOPO:FIM")

# Ícone do canal de WhatsApp no cabeçalho — mesmo canal já divulgado no fim
# de vários artigos (ver "CANAL WHATSAPP" em index.html/abono-de-familia.html/
# etc.), mas com utm_content próprio ("header_nav") para separar quem vem do
# cabeçalho de quem vem do convite no fim dos artigos.
URL_CANAL_WHATSAPP = (
    "https://whatsapp.com/channel/0029VbDwKbZCsU9QFFWi3K1W"
    "?utm_source=tensdireito&amp;utm_medium=site&amp;utm_campaign=canal_whatsapp&amp;utm_content=header_nav"
)

# Barra do topo: mesmo canal, utm_content próprio ("barra_topo").
URL_CANAL_WHATSAPP_BARRA = URL_CANAL_WHATSAPP.replace("utm_content=header_nav", "utm_content=barra_topo")
URL_CALENDARIO = "/calendario-pagamentos-seguranca-social.html"
URL_DADOS_BARRA = "/data/calendario_barra.json"
REFERENCIA_HOJE_LISBOA = '  <script src="/assets/js/hoje-lisboa.js" defer></script>\n'

# Gerador de documentos: "zero pedidos de rede depois do load" (CLAUDE.md,
# secção GERADOR DE DOCUMENTOS) — a barra fica só com a mensagem do
# WhatsApp, sem fetch das datas nem evento GA4 (decisão do Nuno,
# 2026-11-13). O hub entra também, por coerência com as minutas.
def barra_estatica(caminho_relativo: str) -> bool:
    return caminho_relativo == "documentos.html" or caminho_relativo.startswith("documentos/")


REFERENCIAS_HEAD = (
    '  <link rel="stylesheet" href="/assets/css/nav.css">\n'
    '  <script src="/assets/js/nav.js" defer></script>\n'
    '  <script src="/scripts/pesquisa.js" defer></script>\n'
)

_REGEX_NAV_WRAP = re.compile(r'<div class="nav-wrap">[\s\S]*?\n  </div>\n')
_REGEX_HEADER = re.compile(r'<header>[\s\S]*?</header>')
_REGEX_MOBILE_MENU_SEGUINTE = re.compile(r'\A\s*<div class="(?:mobile-menu|nav-mobile-menu)"[\s\S]*?</div>')
_REGEX_HEAD_FECHO = re.compile(r"</head\s*>", re.IGNORECASE)
_REGEX_SKIP_LINK = re.compile(r'<a href="#main-content" class="skip-link">[^<]*</a>\n')


@dataclass(frozen=True)
class Resultado:
    ficheiro: str
    alterado: bool
    motivo: str


def render_dropdown_apoios(clusters: List[Cluster]) -> str:
    # Clusters oculta_em_apoios (ex.: "Como Pedir") não são um apoio —
    # têm o seu próprio link fora do dropdown (ver render_nav()).
    itens = [f'            <a href="{c.pillar}" role="menuitem">{c.nome}</a>' for c in clusters if not c.oculta_em_apoios]
    return "\n".join(itens)


def render_mobile_apoios(clusters: List[Cluster]) -> str:
    itens = [f'    <a href="{c.pillar}" class="nav-mobile-sub">{c.nome}</a>' for c in clusters if not c.oculta_em_apoios]
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

      <div class="nav-links">
        <div class="nav-dropdown" id="navApoiosDropdown">
          <button class="nav-dropdown-btn" type="button" aria-haspopup="true" aria-expanded="false" aria-controls="navApoiosDropdownMenu">Apoios</button>
          <div class="nav-dropdown-menu" id="navApoiosDropdownMenu" role="menu">
{render_dropdown_apoios(clusters)}
          </div>
        </div>
        <a href="/comecar-aqui.html">Começa aqui</a>
        <a href="/calendario-pagamentos-seguranca-social.html">📅 Calendário</a>
        <a href="/simuladores.html">🧮 Simuladores</a>
        <a href="/documentos.html">📄 Documentos</a>
        <a href="/p/como-pedir.html">🔑 Como Pedir</a>
        <a href="/noticias.html">Notícias</a>
      </div>

      <div class="nav-search" role="search" aria-label="Pesquisa da navegação">
        <input type="search" id="campo-pesquisa-nav" placeholder="Pesquisar…" aria-label="Pesquisar" autocomplete="off"
          oninput="mostrarResultados(pesquisar(this.value), this.value, 'resultados-pesquisa-nav')">
        <div id="resultados-pesquisa-nav" class="nav-search-resultados"></div>
      </div>

      <a class="nav-whatsapp" href="{URL_CANAL_WHATSAPP}" target="_blank" rel="noopener" aria-label="Segue o canal do Tens Direito no WhatsApp">
        <svg width="22" height="22" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
          <path d="M13.601 2.326A7.85 7.85 0 0 0 7.994 0C3.627 0 .068 3.558.064 7.926c0 1.399.366 2.76 1.057 3.965L0 16l4.204-1.102a7.9 7.9 0 0 0 3.79.965h.004c4.368 0 7.926-3.558 7.93-7.93A7.9 7.9 0 0 0 13.6 2.326zM7.994 14.521a6.6 6.6 0 0 1-3.356-.92l-.24-.144-2.494.654.666-2.433-.156-.251a6.56 6.56 0 0 1-1.007-3.505c0-3.626 2.957-6.584 6.591-6.584a6.56 6.56 0 0 1 4.66 1.931 6.56 6.56 0 0 1 1.928 4.66c-.004 3.639-2.961 6.592-6.592 6.592m3.615-4.934c-.197-.099-1.17-.578-1.353-.646-.182-.065-.315-.099-.445.099-.133.197-.513.646-.627.775-.114.133-.232.148-.43.05-.197-.1-.836-.308-1.592-.985-.59-.525-.985-1.175-1.103-1.372-.114-.198-.011-.304.088-.403.087-.087.197-.232.296-.346.1-.114.133-.198.198-.33.065-.134.034-.248-.015-.347-.05-.099-.445-1.076-.612-1.47-.16-.389-.323-.335-.445-.34-.114-.007-.247-.007-.38-.007a.73.73 0 0 0-.529.246c-.182.198-.691.677-.691 1.654s.71 1.916.81 2.049c.098.133 1.394 2.132 3.383 2.992.47.205.84.326 1.129.418.475.152.904.129 1.246.08.38-.058 1.171-.48 1.337-.943.164-.464.164-.86.114-.943-.049-.084-.182-.133-.38-.232"/>
        </svg>
      </a>

      <button class="nav-toggle" type="button" aria-label="Abrir menu" aria-expanded="false" aria-controls="navMobileMenu">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
    </nav>

    <div class="nav-mobile-menu" id="navMobileMenu" role="navigation" aria-label="Menu mobile">
      <div class="nav-search nav-search-movel" role="search" aria-label="Pesquisa do menu móvel">
        <input type="search" id="campo-pesquisa-nav-movel" placeholder="Pesquisar…" aria-label="Pesquisar" autocomplete="off"
          oninput="mostrarResultados(pesquisar(this.value), this.value, 'resultados-pesquisa-nav-movel')">
        <div id="resultados-pesquisa-nav-movel" class="nav-search-resultados"></div>
      </div>
      <div class="nav-mobile-grid">
        <a href="/calendario-pagamentos-seguranca-social.html" class="nav-mobile-card"><span class="nav-mobile-card-icone" aria-hidden="true">📅</span><span>Calendário</span></a>
        <a href="/simuladores.html" class="nav-mobile-card"><span class="nav-mobile-card-icone" aria-hidden="true">🧮</span><span>Simuladores</span></a>
        <a href="/documentos.html" class="nav-mobile-card"><span class="nav-mobile-card-icone" aria-hidden="true">📄</span><span>Documentos</span></a>
        <a href="/p/como-pedir.html" class="nav-mobile-card"><span class="nav-mobile-card-icone" aria-hidden="true">🔑</span><span>Como Pedir</span></a>
      </div>
      <a href="/comecar-aqui.html" class="nav-mobile-destaque">Começa aqui</a>
      <details class="nav-mobile-acordeao" id="navMobileApoios">
        <summary><span aria-hidden="true">📋</span> Apoios</summary>
{render_mobile_apoios(clusters)}
      </details>
      <a href="/noticias.html">Notícias</a>
    </div>
  </div>"""


def render_barra_topo(estatica: bool = False) -> str:
    """Barra do topo. Sem JS (e no modo estático) só se vê a mensagem do
    WhatsApp; a do calendário e o botão de pausa nascem `hidden` e só o
    nav.js os mostra, quando há um pagamento a partir de hoje (Lisboa) no
    mês corrente."""
    whatsapp = (
        f'      <a class="barra-topo-msg" data-destino="whatsapp" href="{URL_CANAL_WHATSAPP_BARRA}" target="_blank" rel="noopener">\n'
        '        <span class="barra-topo-texto">🔔 <span class="barra-topo-longo">Recebe no WhatsApp o aviso na véspera de cada pagamento da Segurança Social</span>'
        '<span class="barra-topo-curto">Aviso na véspera, no WhatsApp</span></span> <span class="barra-topo-seta" aria-hidden="true">→</span>\n'
        '      </a>'
    )
    if estatica:
        return (
            '<div class="barra-topo-regiao" role="region" aria-label="Avisos de pagamento" data-barra-modo="estatico">\n'
            '    <div class="barra-topo-mensagens">\n'
            f'{whatsapp}\n'
            '    </div>\n'
            '  </div>'
        )
    return (
        f'<div class="barra-topo-regiao" role="region" aria-label="Avisos de pagamento" data-barra-dados="{URL_DADOS_BARRA}">\n'
        '    <div class="barra-topo-mensagens" aria-live="off">\n'
        f'      <a class="barra-topo-msg" data-destino="calendario" href="{URL_CALENDARIO}" hidden>\n'
        '        <span class="barra-topo-texto"><span class="barra-topo-longo">📅 Calendário de pagamentos da Segurança Social</span>'
        '<span class="barra-topo-curto">📅 Calendário de pagamentos</span></span> <span class="barra-topo-seta" aria-hidden="true">→</span>\n'
        '      </a>\n'
        f'{whatsapp}\n'
        '    </div>\n'
        '    <button class="barra-topo-pausa" type="button" aria-label="Pausar as mensagens" data-pausado="false" hidden>'
        '<svg class="barra-topo-icone-pausa" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" focusable="false">'
        '<rect x="2" y="1" width="3.5" height="12" rx="1" fill="currentColor"/><rect x="8.5" y="1" width="3.5" height="12" rx="1" fill="currentColor"/></svg>'
        '<svg class="barra-topo-icone-retomar" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true" focusable="false">'
        '<path d="M3 1.5v11l9.5-5.5z" fill="currentColor"/></svg></button>\n'
        '  </div>'
    )


def bootstrap_barra(conteudo: str) -> Tuple[Optional[str], str]:
    """Insere os marcadores BARRA-TOPO a seguir ao skip-link, se faltarem."""
    if f"<!-- {MARCADOR_BARRA[0]} -->" in conteudo:
        return conteudo, "já tem marcador"
    if 'class="cal-topo' in conteudo:
        return None, "barra antiga do calendário (cal-topo) presente — requer intervenção manual"
    m = _REGEX_SKIP_LINK.search(conteudo)
    if not m:
        return None, "sem skip-link para ancorar a barra do topo — requer intervenção manual"
    novo = (conteudo[:m.end()] + f"  <!-- {MARCADOR_BARRA[0]} -->\n  <!-- {MARCADOR_BARRA[1]} -->\n"
            + conteudo[m.end():])
    return novo, "bootstrap: barra do topo"


def _substituir_bloco(conteudo: str, marca: Tuple[str, str], novo_interior: str) -> Optional[str]:
    inicio, fim = marca
    padrao = re.compile(rf"(<!-- {re.escape(inicio)} -->)([\s\S]*?)(<!-- {re.escape(fim)} -->)")
    if not padrao.search(conteudo):
        return None
    return padrao.sub(lambda m: f"{m.group(1)}\n{novo_interior}\n{m.group(3)}", conteudo)


def _garantir_referencias_head(conteudo: str, *, hoje_lisboa: bool = False) -> str:
    """nav.css/nav.js/pesquisa.js em todas as páginas; hoje-lisboa.js (data
    de hoje em Lisboa, para a barra do topo) onde a barra lê datas — só se a
    página ainda não o carregar noutro sítio (ex.: fim do <body>)."""
    faltam = [ref for ref in ("/assets/css/nav.css", "/assets/js/nav.js", "/scripts/pesquisa.js") if ref not in conteudo]
    if faltam:
        match = _REGEX_HEAD_FECHO.search(conteudo)
        if match:
            pos = match.start()
            conteudo = conteudo[:pos] + REFERENCIAS_HEAD + conteudo[pos:]
    if hoje_lisboa and "/assets/js/hoje-lisboa.js" not in conteudo:
        match = _REGEX_HEAD_FECHO.search(conteudo)
        if match:
            pos = match.start()
            conteudo = conteudo[:pos] + REFERENCIA_HOJE_LISBOA + conteudo[pos:]
    return conteudo


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


def sincronizar_conteudo(conteudo_original: str, nome: str, clusters: List[Cluster]) -> Tuple[Optional[str], str]:
    """Transformação pura de uma página (sem I/O): NAV + BARRA-TOPO +
    referências no <head>. Devolve (None, motivo) quando a página exige
    intervenção manual; nunca altera nada fora dos dois blocos marcados e
    das referências do <head> (ver tests/test_barra_topo.py)."""
    conteudo, motivo_bootstrap = bootstrap_nav(conteudo_original)
    if conteudo is None:
        return None, motivo_bootstrap

    novo = _substituir_bloco(conteudo, MARCADOR_NAV, render_nav(clusters))
    if novo is None:
        return None, "marcador NAV em falta após bootstrap — não deveria acontecer"

    conteudo, motivo_barra = bootstrap_barra(novo)
    if conteudo is None:
        return None, motivo_barra
    estatica = barra_estatica(nome)
    novo = _substituir_bloco(conteudo, MARCADOR_BARRA, "  " + render_barra_topo(estatica))
    if novo is None:
        return None, "marcador BARRA-TOPO em falta após bootstrap — não deveria acontecer"
    return _garantir_referencias_head(novo, hoje_lisboa=not estatica), motivo_bootstrap


def processar_pagina(caminho: Path, clusters: List[Cluster], *, escrever: bool = True) -> Resultado:
    nome = str(caminho.relative_to(RAIZ))
    conteudo_original = caminho.read_text(encoding="utf-8")

    conteudo, motivo = sincronizar_conteudo(conteudo_original, nome, clusters)
    if conteudo is None:
        return Resultado(nome, False, motivo)

    if conteudo == conteudo_original:
        return Resultado(nome, False, "já sincronizado — sem alterações")

    if escrever:
        caminho.write_text(conteudo, encoding="utf-8")
    sufixo = "" if escrever else " (dry-run, não escrito)"
    return Resultado(nome, True, f"sincronizado [{motivo}]{sufixo}")


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
