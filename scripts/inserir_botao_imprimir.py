#!/usr/bin/env python3
"""Botão «Imprimir» nos guias — idempotente.

Insere, dentro do bloco do botão de partilha (`<div class="partilhar-artigo">`,
entre `<!-- partilhar:inicio/fim -->`), um segundo botão:

    <button type="button" class="botao-imprimir" hidden>🖨️ Imprimir</button>

Nasce `hidden`: sem JavaScript não há como imprimir por um botão, por isso
só aparece quando `assets/js/nav.js` (iniciarImpressao) o mostra e lhe liga
`window.print()`. A versão para imprimir em si é o `@media print` de
`assets/css/nav.css`, que já esconde o bloco inteiro.

Páginas-alvo (os guias): as páginas `tipo: "artigo"` e os pillars de
`data/clusters.json`, mais `EXTRAS`. Simuladores, gerador de documentos e
páginas institucionais ficam de fora.

Uso:
    python scripts/inserir_botao_imprimir.py           # só mostra
    python scripts/inserir_botao_imprimir.py --write   # escreve
    python scripts/inserir_botao_imprimir.py --check   # exit 1 se faltar
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

BOTAO = '<button type="button" class="botao-imprimir" hidden>🖨️ Imprimir</button>'

# Guias que não estão em data/clusters.json.
EXTRAS = (
    "o-que-muda-em-2027.html",
    "calendario-pagamentos-seguranca-social.html",
    "pagamento-apos-deferimento.html",
)

_REGEX_BLOCO = re.compile(
    r'(<!-- partilhar:inicio -->\s*<div class="partilhar-artigo">\s*'
    r'<button type="button" class="botao-partilhar"[^>]*>[^<]*</button>)'
    r'(\s*)(</div>\s*<!-- partilhar:fim -->)'
)


def paginas_alvo(raiz: Path = RAIZ) -> list[str]:
    dados = json.loads((raiz / "data" / "clusters.json").read_text(encoding="utf-8"))
    clusters = dados["clusters"] if isinstance(dados, dict) else dados
    alvo = set(EXTRAS)
    for c in clusters:
        alvo.add(c["pillar"].lstrip("/"))
        for p in c["paginas"]:
            if p.get("tipo") == "artigo":
                alvo.add(p["slug"])
    return sorted(alvo)


def com_botao(html: str) -> str | None:
    """Devolve o HTML com o botão, o próprio HTML se já o tiver, ou None
    se não houver bloco de partilha reconhecível."""
    if "botao-imprimir" in html:
        return html
    m = _REGEX_BLOCO.search(html)
    if not m:
        return None
    return html[: m.start()] + m.group(1) + "\n  " + BOTAO + "\n" + m.group(3) + html[m.end():]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    em_falta, sem_bloco = [], []
    for nome in paginas_alvo():
        caminho = RAIZ / nome
        if not caminho.exists():
            sem_bloco.append(f"{nome} (ficheiro não existe)")
            continue
        html = caminho.read_text(encoding="utf-8")
        novo = com_botao(html)
        if novo is None:
            sem_bloco.append(nome)
        elif novo != html:
            em_falta.append(nome)
            if args.write:
                caminho.write_text(novo, encoding="utf-8")

    for nome in sem_bloco:
        print(f"⚠️  sem bloco de partilha reconhecível: {nome}")
    acao = "inserido" if args.write else "em falta"
    for nome in em_falta:
        print(f"{'✓' if args.write else '·'} botão {acao}: {nome}")
    print(f"{len(em_falta)} página(s) {acao}, {len(sem_bloco)} sem bloco.")
    if sem_bloco or (args.check and em_falta):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
