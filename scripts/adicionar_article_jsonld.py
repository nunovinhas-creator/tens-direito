#!/usr/bin/env python3
"""
scripts/adicionar_article_jsonld.py

Auditoria de indexação (2026-07-04): varrimento da sessão E-E-A-T
anterior confirmou que as 27 páginas de conteúdo (as que têm bloco
`"@type": "FAQPage"`) não tinham nenhum objecto `Article`/`WebPage`
próprio — o `author`/`publisher` da NV Labs vivia só dentro do
`FAQPage`, que a Google Search Central documenta NÃO consumir para
autoria (só `Article`/`NewsArticle`/`BlogPosting`/`WebPage`). Esta era
uma melhoria registada no CLAUDE.md, agora implementada.

Insere um novo bloco `<script type="application/ld+json">` (separado do
FAQPage/HowTo/BreadcrumbList existentes — Article não se mistura com
FAQPage no mesmo objecto) com:
  - `headline`  — de `og:title` (já correcto e específico por página)
  - `author`/`publisher` — `{"@id": ".../sobre.html#nvlabs"}`, mesmo
    padrão de `adicionar_autoria_artigos.py`
  - `datePublished` — de `DATAS_PUBLICACAO` (fonte: tabela "PÁGINAS
    PUBLICADAS" do CLAUDE.md; nem todas têm dia exacto — usa-se
    `AAAA-MM` nesses casos, uma data ISO 8601 parcial válida, nunca um
    dia inventado)
  - `dateModified` — de `extrair_verificado_em()` (a mesma fonte que
    `sincronizar_clusters.py` já usa para o "Verificado a" real);
    páginas sem esse carimbo (simuladores, pillar pages) usam
    `datePublished` como `dateModified` — nunca inventa uma data mais
    recente
  - `mainEntityOfPage` — de `og:url` (a própria página)

Âmbito: mesmas 27 páginas de `adicionar_autoria_artigos.py` (qualquer
página com `"@type": "FAQPage"` em `*.html`/`p/*.html`) — institucionais,
`404.html`, `noticias.html` e `simulador-psu.html` ficam fora por não
terem FAQPage. `sobre.html` já tem o seu próprio JSON-LD (`AboutPage`)
e fica fora desta lista deliberadamente.

Idempotente: não faz nada a um ficheiro que já tenha `"@type": "Article"`.

Uso:
  python scripts/adicionar_article_jsonld.py            # dry-run
  python scripts/adicionar_article_jsonld.py --write     # aplica
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from sincronizar_clusters import extrair_verificado_em  # noqa: E402

ID_NVLABS = "https://tensdireito.com/sobre.html#nvlabs"

# Fonte: tabela "PÁGINAS PUBLICADAS" do CLAUDE.md (2026-07-04). Só o mês
# é conhecido para as páginas publicadas em "jun. 2026" sem dia exacto
# registado — usa-se data ISO 8601 parcial (AAAA-MM), nunca um dia
# inventado.
DATAS_PUBLICACAO = {
    "calendario-pagamentos-seguranca-social.html": "2026-07-12",
    "pagamento-apos-deferimento.html": "2026-07-12",
    "abono-de-familia.html": "2026-06",
    "acao-social-escolar.html": "2026-06",
    "bolsa-de-merito.html": "2026-06",
    "manuais-escolares-mega.html": "2026-06",
    "passe-sub23.html": "2026-06",
    "p/apoios-escolares.html": "2026-06-30",
    "complemento-solidario-idosos.html": "2026-06-28",
    "prestacao-social-unica.html": "2026-06-28",
    "amim.html": "2026-07-01",
    "psu-quando-entra-em-vigor.html": "2026-07-01",
    "psu-quem-tem-direito.html": "2026-07-01",
    "psu-vs-abono-familia.html": "2026-07-01",
    "psu-lista-13-apoios.html": "2026-07-01",
    "rsi.html": "2026-06",
    "subsidio-desemprego.html": "2026-06",
    "subsidio-parental.html": "2026-06",
    "cuidador-informal.html": "2026-06",
    "simulador-abono.html": "2026-06",
    "simulador-ase.html": "2026-06",
    "p/familia.html": "2026-07-02",
    "p/idosos-incapacidade-cuidadores.html": "2026-07-02",
    "p/trabalho-rendimento.html": "2026-07-02",
    "psu-trabalho-social.html": "2026-07-03",
    "p/habitacao.html": "2026-07-03",
    "porta-65.html": "2026-07-03",
    "apoio-extraordinario-renda.html": "2026-07-03",
    "prova-escolar.html": "2026-07-03",
    "prestacao-social-para-a-inclusao.html": "2026-07-04",
    "baixa-medica-subsidio-doenca.html": "2026-07-05",
    "bolsa-de-estudo-ensino-superior.html": "2026-07-06",
    "assistencia-familia-filhos.html": "2026-07-11",
    "como-pedir-niss.html": "2026-07-14",
    "calendario-escolar-apoios.html": "2026-07-14",
    "declaracao-situacao-contributiva.html": "2026-07-14",
    "senha-seguranca-social-direta.html": "2026-07-17",
    "iban-seguranca-social.html": "2026-07-17",
    "chave-movel-digital.html": "2026-07-17",
    "alterar-morada.html": "2026-07-18",
    "renovar-cartao-cidadao.html": "2026-07-18",
}

_RE_OG_TITLE = re.compile(r'<meta property="og:title" content="([^"]+)">')
_RE_OG_URL = re.compile(r'<meta property="og:url" content="([^"]+)">')


def _fim_do_ultimo_bloco_ldjson(texto: str) -> int | None:
    """Posição logo a seguir ao </script> do último bloco JSON-LD
    existente na página (FAQPage/HowTo/BreadcrumbList). None se não
    houver nenhum bloco JSON-LD (página fora de âmbito)."""
    posicoes = [m.end() for m in re.finditer(r"application/ld\+json[\s\S]*?</script>", texto)]
    return posicoes[-1] if posicoes else None


def construir_article_jsonld(rel_slug: str, texto: str) -> str | None:
    if rel_slug not in DATAS_PUBLICACAO:
        return None

    m_titulo = _RE_OG_TITLE.search(texto)
    m_url = _RE_OG_URL.search(texto)
    if not m_titulo or not m_url:
        return None

    headline = m_titulo.group(1)
    url = m_url.group(1)
    data_publicacao = DATAS_PUBLICACAO[rel_slug]

    data_verificacao = extrair_verificado_em(RAIZ / rel_slug)
    data_modificacao = data_verificacao.isoformat() if data_verificacao else data_publicacao

    return (
        '\n\n  <!-- JSON-LD Article -->\n'
        '  <script type="application/ld+json">\n'
        '  {\n'
        '    "@context": "https://schema.org",\n'
        '    "@type": "Article",\n'
        f'    "headline": "{headline}",\n'
        f'    "mainEntityOfPage": "{url}",\n'
        f'    "author": {{"@id": "{ID_NVLABS}"}},\n'
        f'    "publisher": {{"@id": "{ID_NVLABS}"}},\n'
        f'    "datePublished": "{data_publicacao}",\n'
        f'    "dateModified": "{data_modificacao}"\n'
        '  }\n'
        '  </script>'
    )


def injetar_article(texto: str, rel_slug: str) -> tuple[str, bool]:
    if '"@type": "Article"' in texto:
        return texto, False

    bloco = construir_article_jsonld(rel_slug, texto)
    if bloco is None:
        return texto, False

    pos = _fim_do_ultimo_bloco_ldjson(texto)
    if pos is None:
        return texto, False

    texto_novo = texto[:pos] + bloco + texto[pos:]
    return texto_novo, True


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

        rel = str(caminho.relative_to(RAIZ))
        novo_texto, mudou = injetar_article(original, rel)

        if not mudou:
            print(f"[skip] {rel}: já sincronizado ou fora de âmbito")
            continue

        alterados += 1
        modo = "write" if args.write else "dry-run"
        print(f"[{modo}] {rel}: Article JSON-LD adicionado")
        if args.write:
            caminho.write_text(novo_texto, encoding="utf-8")

    print(f"\n{alterados} ficheiro(s) {'alterados' if args.write else 'seriam alterados'}.")
    if not args.write:
        print("Corre com --write para aplicar.")


if __name__ == "__main__":
    main()
