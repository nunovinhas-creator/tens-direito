"""
Sincroniza o `<lastmod>` de cada URL de `sitemap.xml` com a data da própria
página — nunca uma data escrita à mão.

Data da página (`data_da_pagina()`): o `dateModified` do JSON-LD; sem ele, o
último carimbo "Verificado a" (`extrair_verificado_em()`, o mesmo critério de
`sincronizar_clusters.py`). Página sem nenhuma das duas: sem `<lastmod>` —
nunca uma data inventada.

`SEM_LASTMOD`: páginas deixadas deliberadamente sem `<lastmod>` (alteradas
todos os dias pelo pipeline, que não escreve no sitemap, ou institucionais
sem data editorial).

Ordem dentro de cada `<url>`: loc → lastmod → changefreq → priority, a do
protocolo de sitemaps.org. O `<lastmod>` existente é sempre retirado e
reinserido logo a seguir ao `<loc>` — actualizar e inserir dão a mesma ordem.

Uso: python scripts/sincronizar_sitemap_lastmod.py [--write | --check]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import extrair_verificado_em  # noqa: E402

SITEMAP = RAIZ / "sitemap.xml"
DOMINIO = "https://tensdireito.com/"

# Páginas deliberadamente sem <lastmod>. O motivo de cada uma vive em
# tests/test_sitemap_lastmod.py (EXCECOES_SEM_LASTMOD), que confirma que
# este conjunto e o do teste são o mesmo.
SEM_LASTMOD = {
    "index.html",
    "noticias.html",
    "comecar-aqui.html",
    "sobre.html",
    "privacidade.html",
    "acessibilidade.html",
}

_RE_DATE_MODIFIED = re.compile(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})')
_RE_URL = re.compile(r"(?P<indent>[ \t]*)<url>(?P<corpo>.*?)</url>", re.S)
# A quebra de linha e a indentação antes do <loc> são reaproveitadas para o
# <lastmod>, que fica logo a seguir, à mesma indentação.
_RE_LOC = re.compile(r"(?P<antes>\n[ \t]*)?<loc>(?P<loc>[^<]*)</loc>")
_RE_LASTMOD = re.compile(r"\n?[ \t]*<lastmod>[^<]*</lastmod>")


def caminho_de_loc(loc: str) -> Path:
    rel = loc[len(DOMINIO):] if loc.startswith(DOMINIO) else loc
    return RAIZ / (rel or "index.html")


def data_da_pagina(caminho: Path) -> str | None:
    datas = sorted(set(_RE_DATE_MODIFIED.findall(caminho.read_text(encoding="utf-8"))))
    if datas:
        return datas[-1]
    v = extrair_verificado_em(caminho)
    return v.isoformat() if v else None


def lastmod_esperado(caminho: Path) -> str | None:
    if str(caminho.relative_to(RAIZ)) in SEM_LASTMOD:
        return None
    return data_da_pagina(caminho)


def sincronizar(xml: str) -> str:
    def _url(m: re.Match) -> str:
        indent, corpo = m.group("indent"), m.group("corpo")
        data = lastmod_esperado(caminho_de_loc(_RE_LOC.search(corpo).group("loc")))
        corpo = _RE_LASTMOD.sub("", corpo)
        if data:
            m_loc = _RE_LOC.search(corpo)
            antes = m_loc.group("antes") or f"\n{indent}  "
            corpo = f"{corpo[:m_loc.end()]}{antes}<lastmod>{data}</lastmod>{corpo[m_loc.end():]}"
        return f"{indent}<url>{corpo}</url>"

    return _RE_URL.sub(_url, xml)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    original = SITEMAP.read_text(encoding="utf-8")
    novo = sincronizar(original)
    if novo == original:
        print("sitemap.xml: lastmod já sincronizado")
        return 0
    if args.check:
        print("sitemap.xml: lastmod divergente — correr scripts/sincronizar_sitemap_lastmod.py --write")
        return 1
    if args.write:
        SITEMAP.write_text(novo, encoding="utf-8")
        print("sitemap.xml: lastmod actualizado")
    else:
        print("sitemap.xml: lastmod a actualizar (dry-run)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
