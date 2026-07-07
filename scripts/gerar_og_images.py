#!/usr/bin/env python3
"""
scripts/gerar_og_images.py

Imagens de partilha social POR PÁGINA (2026-07-07, evolução do
adicionar_og_image.py do mesmo dia): em vez da imagem única do site,
cada página ganha a sua própria imagem 1200×630 com o título real do
artigo (o `og:title`, curado à mão) e o guia/cluster a que pertence —
estilo jornal. Renderizadas com Chromium real (Playwright) a partir de
um template HTML com a marca do site (teal #0F766E + visto do
favicon.svg), guardadas em `assets/img/og/<slug>.jpg` (JPEG q88, ~55KB
cada — PNG seriam ~260KB, 5× mais pesado no repositório, sem ganho
visível numa pré-visualização social).

Script de SESSÃO MANUAL (mesma categoria de sincronizar_clusters.py)
— nunca corre no pipeline automático. Correr ao publicar uma página
nova ou ao mudar um <title>/og:title:

  python scripts/gerar_og_images.py            # dry-run
  python scripts/gerar_og_images.py --write    # gera + actualiza metas

Idempotente por manifest: `assets/img/og/manifest.json` guarda o
título/chip usados em cada imagem — uma página só é re-renderizada se
o título ou o chip tiverem mudado (ou a imagem não existir; `--force`
regenera tudo). A actualização das metas `og:image`/`og:image:alt` no
HTML é sempre idempotente (no-op se já estiverem certas).

O chip (canto do cartão) vem de `data/clusters.json` (fonte única):
nome do cluster para artigos/ferramentas/pillars; "Gerador de
documentos" para o hub e as minutas; "Simuladores e calculadoras" para
o hub de simuladores; sem chip nas institucionais.
"""
from __future__ import annotations

import argparse
import html as _html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_OG = RAIZ / "assets" / "img" / "og"
MANIFEST = DIR_OG / "manifest.json"
DOMINIO = "https://tensdireito.com"
LARGURA, ALTURA = 1200, 630
QUALIDADE_JPEG = 88

_RE_OG_TITLE = re.compile(r'<meta property="og:title" content="([^"]*)">')
_RE_OG_IMAGE = re.compile(r'(<meta property="og:image" content=")[^"]*(">)')
_RE_OG_ALT = re.compile(r'(<meta property="og:image:alt" content=")[^"]*(">)')

_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-PT">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1200px; height: 630px;
    font-family: -apple-system, "Segoe UI", Roboto, "DejaVu Sans", sans-serif;
    background: linear-gradient(135deg, #0F766E 0%, #0B5D57 100%);
    color: #fff;
    display: flex; flex-direction: column; justify-content: center;
    padding: 0 96px;
    position: relative; overflow: hidden;
  }}
  .marca-agua {{
    position: absolute; right: -70px; bottom: -90px;
    width: 460px; height: 460px; opacity: 0.10;
  }}
  .topo {{ display: flex; align-items: center; gap: 22px; margin-bottom: 40px; }}
  .logo {{
    width: 76px; height: 76px; border-radius: 17px; background: #fff;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }}
  .nome {{ font-size: 46px; font-weight: 800; letter-spacing: -0.5px; }}
  .chip {{
    margin-left: auto;
    font-size: 24px; font-weight: 600;
    background: rgba(255,255,255,0.14);
    border: 2px solid rgba(255,255,255,0.35);
    border-radius: 999px; padding: 10px 24px;
    white-space: nowrap;
  }}
  .titulo {{
    font-size: {tamanho_titulo}px; font-weight: 700; line-height: 1.22;
    max-width: 980px; margin-bottom: 34px;
    display: -webkit-box; -webkit-line-clamp: 4;
    -webkit-box-orient: vertical; overflow: hidden;
  }}
  .selo {{
    display: inline-flex; align-items: center; gap: 12px;
    font-size: 25px; font-weight: 600; width: fit-content;
  }}
  .selo svg {{ flex-shrink: 0; }}
  .dominio {{
    position: absolute; bottom: 42px; right: 96px;
    font-size: 25px; font-weight: 600; opacity: 0.85; letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
  <svg class="marca-agua" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 16 L13 22 L25 10" fill="none" stroke="#fff"
          stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div class="topo">
    <div class="logo">
      <svg width="48" height="48" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 16 L13 22 L25 10" fill="none" stroke="#0F766E"
              stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>
    <div class="nome">Tens Direito</div>
    {chip_html}
  </div>
  <div class="titulo">{titulo}</div>
  <div class="selo">
    <svg width="24" height="24" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
      <path d="M7 16 L13 22 L25 10" fill="none" stroke="#fff"
            stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    Verificado em fontes oficiais
  </div>
  <div class="dominio">tensdireito.com</div>
</body>
</html>
"""


def encontrar_paginas() -> list[Path]:
    return (
        sorted(RAIZ.glob("*.html"))
        + sorted((RAIZ / "p").glob("*.html"))
        + sorted((RAIZ / "documentos").glob("*.html"))
    )


def slug_imagem(rel: str) -> str:
    """abono-de-familia.html → abono-de-familia; p/familia.html → p-familia."""
    return rel[: -len(".html")].replace("/", "-")


def titulo_para_cartao(og_title: str) -> str:
    """O cartão já tem o wordmark 'Tens Direito' — remover a marca do
    título quando presente (ex.: index.html, 404.html) para não duplicar."""
    t = og_title.strip()
    for prefixo in ("Tens Direito — ", "Tens Direito - "):
        if t.startswith(prefixo):
            return t[len(prefixo):]
    for sufixo in (" — Tens Direito", " - Tens Direito", " | Tens Direito"):
        if t.endswith(sufixo):
            return t[: -len(sufixo)]
    return t


def _mapa_chips() -> dict[str, str]:
    """rel-path → texto do chip, a partir de data/clusters.json (fonte
    única). Páginas fora de qualquer categoria não têm chip."""
    mapa: dict[str, str] = {}
    clusters = json.loads((RAIZ / "data" / "clusters.json").read_text(encoding="utf-8"))["clusters"]
    for c in clusters:
        mapa[c["pillar"].lstrip("/")] = c["nome"]
        for pag in c["paginas"]:
            mapa[pag["slug"]] = c["nome"]
    mapa["documentos.html"] = "Gerador de documentos"
    for doc in sorted((RAIZ / "documentos").glob("*.html")):
        mapa[f"documentos/{doc.name}"] = "Gerador de documentos"
    mapa["simuladores.html"] = "Simuladores e calculadoras"
    return mapa


def tamanho_fonte(titulo: str) -> int:
    n = len(titulo)
    if n <= 40:
        return 58
    if n <= 60:
        return 52
    if n <= 85:
        return 46
    if n <= 110:
        return 40
    return 34


def render_html_cartao(titulo: str, chip: str | None) -> str:
    chip_html = f'<div class="chip">{_html.escape(chip)}</div>' if chip else ""
    return _TEMPLATE.format(
        titulo=_html.escape(titulo),
        chip_html=chip_html,
        tamanho_titulo=tamanho_fonte(titulo),
    )


def actualizar_metas(texto: str, url_imagem: str, alt: str) -> tuple[str, bool]:
    """Aponta og:image/og:image:alt da página à sua própria imagem.
    Idempotente. Exige as tags já presentes (inseridas por
    adicionar_og_image.py) — nunca as cria do zero aqui."""
    novo = _RE_OG_IMAGE.sub(lambda m: m.group(1) + url_imagem + m.group(2), texto, count=1)
    novo = _RE_OG_ALT.sub(lambda m: m.group(1) + _html.escape(alt, quote=True) + m.group(2), novo, count=1)
    return novo, novo != texto


def _localizar_chromium() -> str | None:
    """Mesma estratégia de fallback documentada em tests/: env var →
    /opt/pw-browsers → cache por omissão do Playwright."""
    import glob
    import os
    candidatos = []
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env:
        candidatos.append(env)
    candidatos += ["/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")]
    for base in candidatos:
        for padrao in ("chromium", "chromium-*/chrome-linux*/chrome"):
            achados = sorted(glob.glob(os.path.join(base, padrao)))
            if achados:
                return achados[-1]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Gera as imagens e actualiza as metas")
    parser.add_argument("--force", action="store_true", help="Regenera todas as imagens, mesmo sem mudança")
    args = parser.parse_args()

    manifest: dict[str, dict] = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    chips = _mapa_chips()
    plano: list[tuple[Path, str, str, str, str | None, bool]] = []
    for caminho in encontrar_paginas():
        rel = str(caminho.relative_to(RAIZ))
        texto = caminho.read_text(encoding="utf-8")
        m = _RE_OG_TITLE.search(texto)
        if not m:
            print(f"[AVISO] {rel}: sem og:title — página saltada, rever manualmente")
            continue
        og_title = _html.unescape(m.group(1))
        titulo = titulo_para_cartao(og_title)
        chip = chips.get(rel)
        slug = slug_imagem(rel)
        imagem = DIR_OG / f"{slug}.jpg"
        precisa_render = (
            args.force
            or not imagem.exists()
            or manifest.get(slug, {}).get("titulo") != titulo
            or manifest.get(slug, {}).get("chip") != chip
        )
        plano.append((caminho, rel, slug, titulo, chip, precisa_render))

    a_renderizar = [p for p in plano if p[5]]
    print(f"{len(plano)} página(s); {len(a_renderizar)} imagem(ns) a renderizar.")

    if not args.write:
        for _, rel, slug, titulo, chip, render in plano:
            estado = "render" if render else "ok"
            print(f"[dry-run:{estado}] {rel} → assets/img/og/{slug}.jpg | {titulo!r}" + (f" | chip={chip!r}" if chip else ""))
        print("\nCorre com --write para aplicar.")
        return

    DIR_OG.mkdir(parents=True, exist_ok=True)

    if a_renderizar:
        from playwright.sync_api import sync_playwright

        exe = _localizar_chromium()
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=exe) if exe and not exe.endswith("pw-browsers") else pw.chromium.launch()
            page = browser.new_page(viewport={"width": LARGURA, "height": ALTURA}, device_scale_factor=1)
            for _, rel, slug, titulo, chip, render in plano:
                if not render:
                    continue
                page.set_content(render_html_cartao(titulo, chip))
                page.wait_for_timeout(120)
                page.screenshot(path=str(DIR_OG / f"{slug}.jpg"), type="jpeg", quality=QUALIDADE_JPEG)
                print(f"[render] assets/img/og/{slug}.jpg")
            browser.close()

    metas_alteradas = 0
    for caminho, rel, slug, titulo, chip, _ in plano:
        url = f"{DOMINIO}/assets/img/og/{slug}.jpg"
        texto = caminho.read_text(encoding="utf-8")
        novo, mudou = actualizar_metas(texto, url, titulo)
        if mudou:
            caminho.write_text(novo, encoding="utf-8")
            metas_alteradas += 1
            print(f"[meta] {rel}: og:image → {url}")
        manifest[slug] = {"titulo": titulo, "chip": chip, "pagina": rel}

    # remover imagens/entradas órfãs (página apagada/renomeada)
    slugs_validos = {p[2] for p in plano}
    for antigo in list(manifest):
        if antigo not in slugs_validos:
            (DIR_OG / f"{antigo}.jpg").unlink(missing_ok=True)
            del manifest[antigo]
            print(f"[limpeza] assets/img/og/{antigo}.jpg (página já não existe)")

    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n{len(a_renderizar)} imagem(ns) renderizada(s); {metas_alteradas} página(s) com metas actualizadas.")


if __name__ == "__main__":
    main()
