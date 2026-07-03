#!/usr/bin/env python3
"""Sincroniza o badge NV Labs (header) e o bloco de atribuição NV Labs
(footer) nas páginas HTML publicadas — fonte de verdade são os blocos
`BLOCO_HEADER`/`BLOCO_FOOTER` abaixo.

Idempotente nos dois sentidos:
  - página sem os marcadores ainda: bootstrap — insere o bloco em pontos
    de fronteira fixos (fecho de `.logo`, `</footer>`, `</head>`); nunca
    reescreve GA4, OG tags, JSON-LD, disclaimer ou qualquer outro
    conteúdo existente.
  - página já com os marcadores: sincronização — substitui só o
    conteúdo entre `INICIO`/`FIM` pelo bloco canónico actual (no-op se
    já estiver igual). É o que permite ao footer voltar a mudar no
    futuro (e-mail, AdSense, afiliados) sem editar 29 ficheiros à mão.

Âmbito automático (derivado da estrutura de cada página, não de uma lista fixa):
  - badge no header: só páginas com `<a href="/" class="logo">`
  - bloco no footer: só páginas com `</footer>`
  - link para branding.css: só páginas onde pelo menos uma das anteriores foi inserida

Uso:
  python scripts/atualizar_branding_nvlabs.py            # dry-run (mostra o que mudaria)
  python scripts/atualizar_branding_nvlabs.py --write     # aplica as alterações
"""
import argparse
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

MARCADOR_HEADER_INICIO = "<!-- NVLABS:HEADER:INICIO -->"
MARCADOR_HEADER_FIM = "<!-- NVLABS:HEADER:FIM -->"
MARCADOR_FOOTER_INICIO = "<!-- NVLABS:FOOTER:INICIO -->"
MARCADOR_FOOTER_FIM = "<!-- NVLABS:FOOTER:FIM -->"
LINK_CSS = '<link rel="stylesheet" href="/assets/css/branding.css">'

SVG_NV_LABS_LIGHT = """<svg class="nv-labs-light" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" role="img" aria-label="NV Labs">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="150" y="80" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="52" font-weight="bold" fill="#0b131f" text-anchor="middle" letter-spacing="2">NV</text>
  <line x1="105" y1="102" x2="195" y2="102" stroke="#1ea3b2" stroke-width="4" stroke-linecap="round"/>
  <text x="150" y="145" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="normal" fill="#0b131f" text-anchor="middle" letter-spacing="8">Labs</text>
</svg>"""

SVG_NV_LABS_DARK = """<svg class="nv-labs-dark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 200" role="img" aria-label="NV Labs">
  <rect width="100%" height="100%" rx="12" fill="#0b131f"/>
  <text x="150" y="80" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="52" font-weight="bold" fill="#ffffff" text-anchor="middle" letter-spacing="2">NV</text>
  <line x1="105" y1="102" x2="195" y2="102" stroke="#1ea3b2" stroke-width="4" stroke-linecap="round"/>
  <text x="150" y="145" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="normal" fill="#ffffff" text-anchor="middle" letter-spacing="8">Labs</text>
</svg>"""

SVG_FOOTER_BRANDING = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 120" role="img" aria-label="An NV Labs project">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="200" y="45" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="18" fill="#1c1c1e" text-anchor="middle" letter-spacing="0.5">© 2026 Tens Direito</text>
  <text x="200" y="85" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="18" fill="#1c1c1e" text-anchor="middle" letter-spacing="0.5">
    An <tspan fill="#1ea3b2" font-weight="600" text-decoration="underline" dx="2" dy="0">NV Labs</tspan><tspan dx="2"> project</tspan>
  </text>
</svg>"""

INTERIOR_HEADER = f"""<div class="nv-labs-badge" aria-label="An NV Labs project" title="An NV Labs project">
        {SVG_NV_LABS_LIGHT}
        {SVG_NV_LABS_DARK}
      </div>"""

# O SVG mantém-se só decorativo (aria-label já o descreve); a atribuição
# passa a link real para a secção NV Labs em sobre.html — "An NV Labs
# project" mantém-se como texto (decisão do Nuno), agora clicável.
INTERIOR_FOOTER = f"""<a class="footer-nvlabs" href="/sobre.html#nvlabs" aria-label="An NV Labs project — saber mais sobre a NV Labs">
      {SVG_FOOTER_BRANDING}
    </a>"""

BLOCO_HEADER = f"""      {MARCADOR_HEADER_INICIO}
      {INTERIOR_HEADER}
      {MARCADOR_HEADER_FIM}
"""

BLOCO_FOOTER = f"""    {MARCADOR_FOOTER_INICIO}
    {INTERIOR_FOOTER}
    {MARCADOR_FOOTER_FIM}
"""

RE_LOGO = re.compile(r'(<a\s+href="/"\s+class="logo"[^>]*>.*?</a>)', re.DOTALL)


def _sincronizar_marcador(texto: str, marcador_inicio: str, marcador_fim: str, bloco_canonico: str) -> tuple[str, bool]:
    """Substitui tudo entre marcador_inicio/marcador_fim (inclusive) pelo
    bloco canónico actual. No-op se já estiver igual. Devolve
    (texto_novo, alterado)."""
    padrao = re.compile(re.escape(marcador_inicio) + r".*?" + re.escape(marcador_fim), re.DOTALL)
    m = padrao.search(texto)
    if not m:
        return texto, False
    bloco_actual = bloco_canonico.strip()
    if m.group(0) == bloco_actual:
        return texto, False
    return texto[:m.start()] + bloco_actual + texto[m.end():], True


def processar(texto: str, *, apenas_sincronizar: bool = False) -> tuple[str, list[str]]:
    notas = []
    tinha_marcadores = MARCADOR_HEADER_INICIO in texto or MARCADOR_FOOTER_INICIO in texto

    # Página já com marcadores: sincronizar em vez de saltar.
    if MARCADOR_HEADER_INICIO in texto:
        texto, alterado = _sincronizar_marcador(texto, MARCADOR_HEADER_INICIO, MARCADOR_HEADER_FIM, BLOCO_HEADER)
        if alterado:
            notas.append("badge NV Labs sincronizado no header")
    if MARCADOR_FOOTER_INICIO in texto:
        texto, alterado = _sincronizar_marcador(texto, MARCADOR_FOOTER_INICIO, MARCADOR_FOOTER_FIM, BLOCO_FOOTER)
        if alterado:
            notas.append("bloco NV Labs sincronizado no footer")
        return texto, notas

    if tinha_marcadores or apenas_sincronizar:
        return texto, notas

    # Bootstrap: página nunca processada.
    if RE_LOGO.search(texto):
        texto, n = RE_LOGO.subn(lambda m: m.group(1) + "\n" + BLOCO_HEADER, texto, count=1)
        if n:
            notas.append("badge NV Labs inserido no header")

    if "</footer>" in texto:
        texto = texto.replace("</footer>", BLOCO_FOOTER + "  </footer>", 1)
        notas.append("bloco NV Labs inserido no footer")

    if notas and "</head>" in texto:
        texto = texto.replace("</head>", f"  {LINK_CSS}\n</head>", 1)
        notas.append("branding.css ligado no <head>")

    return texto, notas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Escreve as alterações (por omissão só mostra dry-run)")
    parser.add_argument("--apenas-sincronizar", action="store_true",
                         help="Nunca faz bootstrap em páginas sem marcadores — só sincroniza as que já os têm")
    args = parser.parse_args()

    ficheiros = sorted(RAIZ.glob("*.html")) + sorted((RAIZ / "p").glob("*.html"))
    alterados = 0

    for caminho in ficheiros:
        original = caminho.read_text(encoding="utf-8")
        novo_texto, notas = processar(original, apenas_sincronizar=args.apenas_sincronizar)
        rel = caminho.relative_to(RAIZ)

        if not notas:
            motivo = "já sincronizado" if (MARCADOR_HEADER_INICIO in original or MARCADOR_FOOTER_INICIO in original) else "sem .logo nem </footer>"
            print(f"[skip] {rel}: {motivo}")
            continue

        alterados += 1
        modo = "write" if args.write else "dry-run"
        print(f"[{modo}] {rel}: {', '.join(notas)}")
        if args.write:
            caminho.write_text(novo_texto, encoding="utf-8")

    print(f"\n{alterados} ficheiro(s) {'alterados' if args.write else 'seriam alterados'}.")
    if not args.write:
        print("Corre com --write para aplicar.")


if __name__ == "__main__":
    main()
