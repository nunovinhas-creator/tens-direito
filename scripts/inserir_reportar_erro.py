"""
Insere (ou sincroniza) o link "Reportar um erro nesta página" logo a seguir
ao carimbo canónico "Verificado a [data] pela redação do Tens Direito" de cada
página — guias, pillars, simuladores, minutas e hubs com carimbo.

O carimbo canónico é a âncora de atribuição já inserida por
`adicionar_autoria_artigos.py` (`pela redação do <a href="/sobre.html#metodo">
Tens Direito</a>`) — uma por página. O link fica entre marcadores
`<!-- REPORTAR-ERRO:INICIO/FIM -->`; numa 2.ª corrida só o interior é
regenerado (idempotente). Página sem carimbo: não é tocada.

Uso: python scripts/inserir_reportar_erro.py [--write]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

ANCORA_CARIMBO = 'pela redação do <a href="/sobre.html#metodo">Tens Direito</a>'
INICIO = "<!-- REPORTAR-ERRO:INICIO -->"
FIM = "<!-- REPORTAR-ERRO:FIM -->"
BLOCO = (
    f'{INICIO} · <a class="reportar-erro" href="/sobre.html#contacto">'
    f"Reportar um erro nesta página</a>{FIM}"
)
_RE_BLOCO = re.compile(re.escape(INICIO) + r".*?" + re.escape(FIM), re.S)


def processar(html: str) -> str:
    if INICIO in html:
        return _RE_BLOCO.sub(lambda _m: BLOCO, html)
    i = html.rfind(ANCORA_CARIMBO)
    if i == -1:
        return html
    fim = i + len(ANCORA_CARIMBO)
    return html[:fim] + BLOCO + html[fim:]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)
    alteradas = []
    for caminho in sorted(encontrar_paginas(RAIZ)):
        original = caminho.read_text(encoding="utf-8")
        novo = processar(original)
        if novo != original:
            alteradas.append(caminho.relative_to(RAIZ))
            if args.write:
                caminho.write_text(novo, encoding="utf-8")
    acao = "alteradas" if args.write else "a alterar (dry-run)"
    print(f"{len(alteradas)} página(s) {acao}")
    for p in alteradas:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
