#!/usr/bin/env python3
"""
scripts/adicionar_canonicas.py

Auditoria de indexação (2026-07-04): nenhuma das 35 páginas HTML tinha
`<link rel="canonical">` — confirmado por varrimento real ao repositório
antes de escrever este script. É a causa técnica mais provável (e a
única evidência encontrada) para o "duplicada, o Google escolheu outra
canónica" no relatório do GSC: sem sinal explícito, o Google decide por
conta própria qual URL é a canónica de cada página.

Insere `<link rel="canonical" href="...">` auto-referente, absoluto,
sem `www` nem `/index.html`, logo a seguir à tag `og:url` (já presente
e correcta nas 35 páginas — confirmado, reutilizado como fonte do
próprio valor em vez de recalcular a partir do caminho do ficheiro).

Âmbito: todas as páginas HTML do repositório, incluindo institucionais,
`404.html` e `simulador-psu.html` (noindex não dispensa canónica — evita
qualquer ambiguidade se algum dia for indexada por engano).

Idempotente: não faz nada a um ficheiro que já tenha `rel="canonical"`.

Uso:
  python scripts/adicionar_canonicas.py            # dry-run
  python scripts/adicionar_canonicas.py --write     # aplica
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

_RE_OG_URL = re.compile(r'(<meta property="og:url" content="([^"]+)">)')


def injetar_canonica(texto: str) -> tuple[str, bool]:
    """Insere a canónica logo a seguir à tag og:url. Idempotente."""
    if 'rel="canonical"' in texto:
        return texto, False

    m = _RE_OG_URL.search(texto)
    if not m:
        return texto, False

    url = m.group(2)
    tag_canonica = f'\n  <link rel="canonical" href="{url}">'
    texto_novo = texto[: m.end()] + tag_canonica + texto[m.end():]
    return texto_novo, True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Escreve as alterações (por omissão só mostra dry-run)")
    args = parser.parse_args()

    ficheiros = sorted(RAIZ.glob("*.html")) + sorted((RAIZ / "p").glob("*.html"))
    alterados = 0

    for caminho in ficheiros:
        original = caminho.read_text(encoding="utf-8")
        novo_texto, mudou = injetar_canonica(original)
        rel = caminho.relative_to(RAIZ)

        if not mudou:
            print(f"[skip] {rel}: já tem canónica")
            continue

        alterados += 1
        modo = "write" if args.write else "dry-run"
        print(f"[{modo}] {rel}: canónica adicionada")
        if args.write:
            caminho.write_text(novo_texto, encoding="utf-8")

    print(f"\n{alterados} ficheiro(s) {'alterados' if args.write else 'seriam alterados'}.")
    if not args.write:
        print("Corre com --write para aplicar.")


if __name__ == "__main__":
    main()
