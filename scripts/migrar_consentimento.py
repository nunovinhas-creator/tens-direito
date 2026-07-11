#!/usr/bin/env python3
"""
Migração CookieYes → banner de consentimento próprio (2026-07-11).

Substitui, no <head> de cada página servida (raiz + p/ + documentos/), o
bloco antigo:

    <script id="cookieyes" ... src="https://cdn-cookieyes.com/..."></script>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-..."></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-...');
    </script>

pelo bloco novo (stub inline com Consent Mode v2 negado por omissão +
assets/js/consentimento.js, que só carrega o gtag.js DEPOIS de o visitante
aceitar — bloqueio real de script, sem serviços externos):

    <!-- Consentimento de cookies (banner próprio) — o Google Analytics só carrega após aceitação (assets/js/consentimento.js) -->
    <script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
    gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'});</script>
    <script src="/assets/js/consentimento.js" data-ga4="G-..." defer></script>

Idempotente: páginas já migradas (sem CookieYes, com consentimento.js) não
são tocadas. Mesmo padrão de adicionar_canonicas.py: inventário por
omissão, --write para aplicar. Uma página com CookieYes mas cujo bloco não
corresponda ao padrão esperado é reportada e NUNCA alterada às cegas.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent

# O ID do GA4 é capturado da própria página (nunca hardcoded aqui) e
# reutilizado no atributo data-ga4 — o validador de conteúdo continua a
# encontrar o literal "G-XP46PM8H1Q" em cada página.
PADRAO_BLOCO_ANTIGO = re.compile(
    r'(?P<indent>[ \t]*)<script id="cookieyes"[^>]*></script>\s*\n'
    r'[ \t]*<!-- Google tag \(gtag\.js\) -->\s*\n'
    r'[ \t]*<script async src="https://www\.googletagmanager\.com/gtag/js\?id=(?P<ga4>G-[A-Z0-9]+)"></script>\s*\n'
    r'[ \t]*<script>[^<]*?gtag\(\'config\',\s*\'(?P=ga4)\'\);?[^<]*?</script>\n'
)

MARCA_NOVO = "assets/js/consentimento.js"


def bloco_novo(indent: str, ga4: str) -> str:
    return (
        f"{indent}<!-- Consentimento de cookies (banner próprio) — o Google Analytics só carrega após aceitação (assets/js/consentimento.js) -->\n"
        f"{indent}<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}\n"
        f"{indent}gtag('consent','default',{{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:'denied'}});</script>\n"
        f'{indent}<script src="/assets/js/consentimento.js" data-ga4="{ga4}" defer></script>\n'
    )


def encontrar_paginas() -> list[Path]:
    paginas = sorted(RAIZ.glob("*.html"))
    paginas += sorted((RAIZ / "p").glob("*.html"))
    paginas += sorted((RAIZ / "documentos").glob("*.html"))
    return paginas


def migrar_pagina(caminho: Path, write: bool) -> str:
    html = caminho.read_text(encoding="utf-8")
    tem_cookieyes = "cookieyes" in html.lower()
    tem_novo = MARCA_NOVO in html

    if not tem_cookieyes and tem_novo:
        return "OK (já migrada)"
    if not tem_cookieyes and not tem_novo:
        return "SEM ANALYTICS (nada a fazer)"

    match = PADRAO_BLOCO_ANTIGO.search(html)
    if not match:
        return "ERRO: tem CookieYes mas o bloco não corresponde ao padrão esperado — rever à mão"

    novo_html = PADRAO_BLOCO_ANTIGO.sub(
        lambda m: bloco_novo(m.group("indent"), m.group("ga4")), html, count=1
    )
    # Garantia dura: nunca deixar dois blocos, nunca deixar restos.
    if "cookieyes" in novo_html.lower():
        return "ERRO: restos de CookieYes depois da substituição — rever à mão"

    if write:
        caminho.write_text(novo_html, encoding="utf-8")
        return "MIGRADA"
    return "A MIGRAR (dry-run)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="aplica as alterações (por omissão é só inventário)")
    args = parser.parse_args()

    erros = 0
    migradas = 0
    for caminho in encontrar_paginas():
        resultado = migrar_pagina(caminho, args.write)
        rel = caminho.relative_to(RAIZ)
        print(f"{rel}: {resultado}")
        if resultado.startswith("ERRO"):
            erros += 1
        elif resultado in ("MIGRADA", "A MIGRAR (dry-run)"):
            migradas += 1

    print(f"\nTotal: {migradas} página(s) migrada(s)/por migrar, {erros} erro(s).")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
