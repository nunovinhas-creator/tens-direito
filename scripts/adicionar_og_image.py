#!/usr/bin/env python3
"""
scripts/adicionar_og_image.py

Partilha em redes sociais (2026-07-07): nenhuma das páginas tinha
`og:image` — confirmado por grep ao repositório inteiro antes de
escrever este script. Sem ela, o Facebook/WhatsApp/LinkedIn mostram a
pré-visualização só com texto (reportado pelo Nuno com um screenshot
real de uma partilha de `abono-de-familia.html`).

Insere, logo a seguir à última tag `og:*` existente de cada página:
  - `og:image` — imagem única do site (1200×630, formato standard),
    URL absoluto (obrigatório para os crawlers sociais)
  - `og:image:width`/`og:image:height` — permitem ao Facebook renderizar
    a pré-visualização à primeira partilha, sem esperar pelo fetch
  - `og:image:alt` — acessibilidade
  - `twitter:card = summary_large_image` — mesma imagem no X/Twitter

A imagem vive em `assets/img/og-default.png` (gerada com a marca real
do site — quadrado teal #0F766E + visto branco do favicon.svg — nunca
um logótipo inventado). Uma imagem única para o site inteiro é a
decisão pragmática: imagens por página seriam um projecto à parte.

Âmbito: todas as páginas HTML servidas (raiz, `p/`, `documentos/`),
incluindo `404.html`/`simulador-psu.html` — uma og:image não faz mal a
uma página noindex, e qualquer página pode ser partilhada por link.

Idempotente: não faz nada a um ficheiro que já tenha `og:image`.

Uso:
  python scripts/adicionar_og_image.py            # dry-run
  python scripts/adicionar_og_image.py --write    # aplica
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

URL_IMAGEM = "https://tensdireito.com/assets/img/og-default.png"
LARGURA, ALTURA = 1200, 630
ALT = "Tens Direito — Apoios sociais em Portugal, verificado em fontes oficiais"

_RE_META_OG = re.compile(r'<meta property="og:[^"]+" content="[^"]*">')

BLOCO = (
    f'\n  <meta property="og:image" content="{URL_IMAGEM}">'
    f'\n  <meta property="og:image:width" content="{LARGURA}">'
    f'\n  <meta property="og:image:height" content="{ALTURA}">'
    f'\n  <meta property="og:image:alt" content="{ALT}">'
    f'\n  <meta name="twitter:card" content="summary_large_image">'
)


def injetar_og_image(texto: str) -> tuple[str, bool]:
    """Insere o bloco og:image a seguir à última tag og:* existente.
    Idempotente; páginas sem nenhuma tag og:* ficam intocadas (não
    existe hoje nenhuma — todas ganharam OG tags até à Fase 5)."""
    if "og:image" in texto:
        return texto, False

    ultimo = None
    for m in _RE_META_OG.finditer(texto):
        ultimo = m
    if ultimo is None:
        return texto, False

    return texto[: ultimo.end()] + BLOCO + texto[ultimo.end():], True


def encontrar_paginas() -> list[Path]:
    return (
        sorted(RAIZ.glob("*.html"))
        + sorted((RAIZ / "p").glob("*.html"))
        + sorted((RAIZ / "documentos").glob("*.html"))
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Escreve as alterações (por omissão só mostra dry-run)")
    args = parser.parse_args()

    alterados, sem_og = 0, []
    for caminho in encontrar_paginas():
        original = caminho.read_text(encoding="utf-8")
        novo_texto, mudou = injetar_og_image(original)
        rel = caminho.relative_to(RAIZ)

        if not mudou:
            if "og:image" in original:
                print(f"[skip] {rel}: já tem og:image")
            else:
                sem_og.append(rel)
                print(f"[AVISO] {rel}: sem nenhuma tag og:* — intocada, rever manualmente")
            continue

        alterados += 1
        modo = "write" if args.write else "dry-run"
        print(f"[{modo}] {rel}: og:image adicionada")
        if args.write:
            caminho.write_text(novo_texto, encoding="utf-8")

    print(f"\n{alterados} ficheiro(s) {'alterados' if args.write else 'seriam alterados'}; "
          f"{len(sem_og)} sem OG tags.")
    if not args.write:
        print("Corre com --write para aplicar.")


if __name__ == "__main__":
    main()
