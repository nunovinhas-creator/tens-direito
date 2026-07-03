#!/usr/bin/env python3
"""
scripts/adicionar_autoria_artigos.py

Sessão E-E-A-T (2026-07-03): a NV Labs passou a ser resolvível como
entidade em `sobre.html` (secção `#nvlabs` + JSON-LD Organization). Este
script propaga essa autoria às páginas de conteúdo:

  1. JSON-LD — injecta `"author"`/`"publisher"` (ambos `{"@id":
     ".../sobre.html#nvlabs"}`) no bloco `FAQPage` de cada página. Válido
     em Schema.org: FAQPage herda de WebPage < CreativeWork, que já
     define `author`/`publisher`.
  2. Byline visível — na ÚLTIMA ocorrência de "Verificado a ..." de cada
     página (a canónica, a mesma que `sincronizar_clusters.extrair_verificado_em()`
     usa — mais próxima do bloco de fontes, nunca uma nota de secção),
     insere " pela redação do <a href=\"/sobre.html#metodo\">Tens
     Direito</a>" logo a seguir à data.

Decisão deliberada sobre a ordem: o brief original propunha "Verificado
pela redação do Tens Direito a [data]" (atribuição ANTES da data). Isto
partiria contiguidade de "Verificado a" em 3 sítios que dependem dela:
`scripts/sincronizar_clusters._REGEX_VERIFICADO`,
`scripts/auto_update_engine._REGEX_VERIFICADO_A` e o aviso (não bloqueante)
de `validar-conteudo.yml`. Colocando a atribuição DEPOIS da data
("Verificado a [data] pela redação do Tens Direito"), a substring
"Verificado a" seguida da data mantém-se 100% intacta — os 3 continuam a
funcionar sem qualquer alteração, confirmado por
`tests/test_adicionar_autoria_artigos.py` (reimporta as funções reais).

Âmbito automático (nunca uma lista fixa): todas as páginas com um bloco
`"@type": "FAQPage"` em `*.html`/`p/*.html`. `simulador-psu.html` não
tem JSON-LD (deliberadamente não publicado) — fica fora sem necessidade
de exclusão explícita. Páginas institucionais (`sobre.html`, `fontes.html`,
`privacidade.html`, `comecar-aqui.html`) e `404.html`/`index.html`/
`noticias.html` não têm FAQPage — ficam fora pelo mesmo motivo.

Idempotente: reexecuções são no-op (verifica se o `@id` já está presente
no JSON-LD e se a última ocorrência de "Verificado a" já tem a
atribuição a seguir).

Uso:
  python scripts/adicionar_autoria_artigos.py            # dry-run
  python scripts/adicionar_autoria_artigos.py --write     # aplica
"""
import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from sincronizar_clusters import _REGEX_VERIFICADO  # noqa: E402

ID_NVLABS = "https://tensdireito.com/sobre.html#nvlabs"
LINK_METODO = '<a href="/sobre.html#metodo">Tens Direito</a>'
ATRIBUICAO = f" pela redação do {LINK_METODO}"

_RE_FAQPAGE_TIPO = re.compile(r'([ \t]*)"@type":\s*"FAQPage",')


def injetar_autoria_jsonld(texto: str) -> tuple[str, bool]:
    """Insere author/publisher logo a seguir a `"@type": "FAQPage",`.
    Idempotente: não faz nada se o @id da NV Labs já estiver no ficheiro."""
    if ID_NVLABS in texto:
        return texto, False

    m = _RE_FAQPAGE_TIPO.search(texto)
    if not m:
        return texto, False

    indent = m.group(1)
    insercao = (
        f'\n{indent}"author": {{"@id": "{ID_NVLABS}"}},'
        f'\n{indent}"publisher": {{"@id": "{ID_NVLABS}"}},'
    )
    texto_novo = texto[: m.end()] + insercao + texto[m.end():]
    return texto_novo, True


def atualizar_byline_verificado(texto: str) -> tuple[str, bool]:
    """Acrescenta a atribuição à ÚLTIMA ocorrência de "Verificado a
    [data]" (a canónica). Idempotente: não duplica se já estiver lá."""
    matches = list(_REGEX_VERIFICADO.finditer(texto))
    if not matches:
        return texto, False

    ultimo = matches[-1]
    a_seguir = texto[ultimo.end(): ultimo.end() + len(ATRIBUICAO) + 20]
    if "redação do" in a_seguir and "Tens Direito" in a_seguir:
        return texto, False

    texto_novo = texto[: ultimo.end()] + ATRIBUICAO + texto[ultimo.end():]
    return texto_novo, True


def processar(texto: str) -> tuple[str, list[str]]:
    notas = []
    texto, mudou_jsonld = injetar_autoria_jsonld(texto)
    if mudou_jsonld:
        notas.append("author/publisher NV Labs adicionados ao FAQPage")
    texto, mudou_byline = atualizar_byline_verificado(texto)
    if mudou_byline:
        notas.append('byline "Verificado a" passa a atribuir à redação do Tens Direito')
    return texto, notas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true", help="Escreve as alterações (por omissão só mostra dry-run)")
    args = parser.parse_args()

    ficheiros = sorted(RAIZ.glob("*.html")) + sorted((RAIZ / "p").glob("*.html"))
    alterados = 0

    for caminho in ficheiros:
        original = caminho.read_text(encoding="utf-8")
        if '"@type": "FAQPage"' not in original:
            continue

        novo_texto, notas = processar(original)
        rel = caminho.relative_to(RAIZ)

        if not notas:
            print(f"[skip] {rel}: já sincronizado")
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
