#!/usr/bin/env python3
"""
Gerador de páginas HTML para o Tens Direito.
Usa o scraper para obter factos verificados antes de gerar qualquer HTML.
Marca cada secção com [FONTE VERIFICADA: data] ou [VERIFICAR MANUALMENTE: motivo].
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scraper_fontes import (  # noqa: E402
    scrape_dge_ase,
    scrape_dge_bolsa_merito,
    scrape_mega_manuais,
    scrape_seg_social_abono,
    scrape_seg_social_rsi,
    scrape_iefp_desemprego,
)

SCRAPERS = {
    "abono-de-familia": scrape_seg_social_abono,
    "rsi": scrape_seg_social_rsi,
    "ase": scrape_dge_ase,
    "bolsa-de-merito": scrape_dge_bolsa_merito,
    "mega": scrape_mega_manuais,
    "desemprego": scrape_iefp_desemprego,
}


def _badge_verificado(data_acesso: str) -> str:
    dt = datetime.fromisoformat(data_acesso).strftime("%d/%m/%Y")
    return f'<span class="badge-verificado">✓ FONTE VERIFICADA: {dt}</span>'


def _badge_verificar(motivo: str) -> str:
    return f'<span class="badge-verificar">⚠ VERIFICAR MANUALMENTE: {motivo}</span>'


def _extrair_paragrafos(resultado: dict, max_p: int = 5) -> list[str]:
    return resultado.get("conteudo_extraido", {}).get("paragrafos", [])[:max_p]


def _extrair_listas(resultado: dict, max_l: int = 3) -> list[list]:
    return resultado.get("conteudo_extraido", {}).get("listas", [])[:max_l]


def _secao_factos(resultado: dict | None, fonte_nome: str) -> str:
    """Gera bloco HTML de factos com badge de verificação."""
    if resultado is None or resultado.get("status") != "ok":
        badge = _badge_verificar(f"fonte {fonte_nome} inacessível em {datetime.now(timezone.utc).strftime('%d/%m/%Y')}")
        return f"""
    <div class="factos-pendentes">
      {badge}
      <p>Os valores e condições desta secção carecem de verificação manual na fonte oficial.</p>
    </div>"""

    paragrafos = _extrair_paragrafos(resultado)
    listas = _extrair_listas(resultado)
    badge = _badge_verificado(resultado["data_acesso"])

    linhas_p = "\n".join(f"      <p>{p}</p>" for p in paragrafos) if paragrafos else ""
    linhas_l = ""
    for lista in listas:
        items = "\n".join(f"        <li>{item}</li>" for item in lista if item)
        linhas_l += f"      <ul>\n{items}\n      </ul>\n"

    return f"""
    <div class="factos-verificados">
      {badge}
      {linhas_p}
      {linhas_l}
    </div>"""


def gerar_pagina(slug: str, titulo: str, descricao: str) -> str:
    """
    Gera HTML completo para uma página, fazendo scrape da fonte antes de redigir.
    Retorna o HTML como string.
    """
    scraper = SCRAPERS.get(slug)
    if scraper is None:
        raise ValueError(f"Sem scraper configurado para slug '{slug}'. Disponíveis: {list(SCRAPERS)}")

    print(f"A verificar fonte para '{slug}'…")
    resultado = scraper()

    secao_factos = _secao_factos(resultado, slug)

    if resultado and resultado.get("status") == "ok":
        status_verificacao = f"Verificado automaticamente em {datetime.now(timezone.utc).strftime('%d/%m/%Y')}"
        cor_status = "#0F766E"
    else:
        status_verificacao = f"[VERIFICAR MANUALMENTE — fonte inacessível em {datetime.now(timezone.utc).strftime('%d/%m/%Y')}]"
        cor_status = "#b45309"

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="index, follow">
  <title>{titulo}</title>
  <meta name="description" content="{descricao}">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: system-ui, sans-serif; background: #f8f9fa; color: #212529; line-height: 1.6; }}
    header {{ background: #fff; border-bottom: 2px solid #0F766E; padding: 1rem 1.5rem; }}
    nav {{ display: flex; align-items: center; gap: 1.5rem; max-width: 900px; margin: 0 auto; }}
    .logo {{ display: flex; align-items: center; gap: .75rem; text-decoration: none; }}
    .logo-text {{ font-size: 1.4rem; font-weight: 700; }}
    .logo-text .tens {{ color: #0F172A; }}
    .logo-text .direito {{ color: #0D9488; }}
    nav a.nav-link {{ color: #0F172A; text-decoration: none; font-size: .95rem; }}
    .hero {{ background: #0F766E; color: white; padding: 2.5rem 1.5rem; }}
    .hero h1 {{ font-size: 1.75rem; line-height: 1.3; }}
    main {{ max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    .card {{ background: white; border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    .card h2 {{ color: #0F766E; margin-bottom: .75rem; }}
    .badge-verificado {{ display:inline-block; background:#e6f4f1; color:#0F766E; font-size:.78rem; font-weight:700; padding:.2rem .6rem; border-radius:4px; margin-bottom:.75rem; }}
    .badge-verificar {{ display:inline-block; background:#fff3cd; color:#856404; font-size:.78rem; font-weight:700; padding:.2rem .6rem; border-radius:4px; margin-bottom:.75rem; }}
    .factos-verificados, .factos-pendentes {{ padding: .75rem 0; }}
    .factos-verificados p, .factos-pendentes p {{ color: #495057; margin-bottom: .5rem; }}
    .factos-verificados ul {{ padding-left: 1.4rem; color: #495057; margin-bottom: .5rem; }}
    .factos-verificados li {{ margin-bottom: .3rem; }}
    .status-bar {{ font-size: .85rem; color: {cor_status}; margin-top: 1rem; }}
    .disclaimer {{ background:#fff3cd; border-left:4px solid #ffc107; padding:1rem 1.25rem; border-radius:4px; font-size:.9rem; line-height:1.6; margin-bottom:2rem; }}
    footer {{ text-align:center; padding:2rem; color:#6c757d; font-size:.85rem; border-top:1px solid #dee2e6; }}
    footer a {{ color:#6c757d; }}
  </style>
</head>
<body>
  <header>
    <nav>
      <a href="/" class="logo">
        <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect width="36" height="36" rx="9" fill="#0F766E"/>
          <path d="M9 18 L16 25 L27 11" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="logo-text"><span class="tens">Tens </span><span class="direito">Direito</span></div>
      </a>
      <a href="/noticias.html" class="nav-link">Notícias</a>
      <a href="/sobre.html" class="nav-link">Sobre</a>
    </nav>
  </header>
  <section class="hero">
    <div style="max-width:900px;margin:0 auto">
      <h1>{titulo}</h1>
    </div>
  </section>
  <main>
    <div class="card">
      <h2>Informação oficial</h2>
      {secao_factos}
      <p class="status-bar">{status_verificacao}</p>
    </div>
    <div class="disclaimer">
      <strong>Aviso de independência:</strong> O Tens Direito é um site informativo independente,
      sem qualquer relação com o Estado ou entidades públicas. Para confirmação oficial,
      consulta diretamente a fonte indicada acima.
    </div>
  </main>
  <footer>
    <p>tensdireito.com — Informação verificada para cidadãos portugueses</p>
    <p style="margin-top:.5rem">
      <a href="/sobre.html">Sobre</a> · <a href="/fontes.html">Fontes</a> · <a href="/privacidade.html">Privacidade</a>
    </p>
  </footer>
</body>
</html>"""
    return html


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gera página HTML com factos verificados")
    parser.add_argument("slug", choices=list(SCRAPERS), help="Identificador da página")
    parser.add_argument("--titulo", required=True, help="Título da página")
    parser.add_argument("--descricao", default="", help="Meta description")
    parser.add_argument("--output", help="Ficheiro de saída (ex: rsi.html)")
    args = parser.parse_args()

    html = gerar_pagina(args.slug, args.titulo, args.descricao)
    output = args.output or f"{args.slug}.html"
    Path(output).write_text(html, encoding="utf-8")
    print(f"\n✓ Página gerada: {output}")
