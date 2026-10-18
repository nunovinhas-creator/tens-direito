"""
Gera o `mainEntity` do JSON-LD `FAQPage` a partir da FAQ que a página
mostra — a FAQ visível é a fonte, o JSON-LD é cópia (issue #352).

Não uniformiza markup: lê os padrões que as páginas já usam, pela lista
`SELECTORES_FAQ`. Uma caixa recolhível num contentor cujo `h2` diz «Erros
comuns» nunca é FAQ (`RE_TITULO_NAO_FAQ`), nem a navegação. Pergunta = texto
do `<summary>` (ou do `h3` de um `.faq-item`); resposta = texto simples do
resto, sem `.fonte-inline` e sem HTML. Perguntas repetidas na página entram
uma só vez (a primeira).

Só reescreve o `mainEntity`: `@context`, `author`, `publisher` e qualquer
outro campo do `FAQPage` ficam; `HowTo`, `Article` e os restantes blocos
não são tocados. Página com `FAQPage` e sem FAQ visível: sai o `FAQPage`.

Uso: python scripts/sincronizar_faq_jsonld.py [--dry-run | --check | --write]
     [páginas…]   (sem páginas: todas as que têm `FAQPage`)
Sessão manual — nunca no pipeline diário (HTML protegido, ver CLAUDE.md).
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

# Os padrões de FAQ visível em uso no site (medidos a 18/10/2026, #352).
SELECTORES_FAQ = (
    ".zona-cinzenta details",   # section/div.zona-cinzenta > details > summary + div.resposta
    "details.zona-cinzenta",    # details soltos no <main> (calendário de pagamentos, deferimento)
    ".faq-section details",     # simuladores: summary + .faq-resposta
    ".faq-geo .faq-item",       # .faq-item > h3 + p
)
RE_TITULO_NAO_FAQ = re.compile(r"(?i)erros\s+comuns")
RE_BLOCO_LD = re.compile(r'(<script type="application/ld\+json">)([\s\S]*?)(</script>)')


def normalizar(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+([.,;:!?)»])", r"\1", texto)
    return re.sub(r"([(«])\s+", r"\1", texto)


def _na_navegacao(el) -> bool:
    return any(
        "nav" in " ".join(a.get("class") or []) + (a.get("id") or "")
        for a in el.parents if a.name
    )


def _titulo_do_contentor(el) -> str:
    for a in el.parents:
        if a.name in ("section", "div"):
            h2 = a.find("h2", recursive=False)
            if h2:
                return h2.get_text(" ", strip=True)
    return ""


def faq_visivel(html: str) -> list[tuple[str, str]]:
    """(pergunta, resposta) da FAQ visível, pela ordem da página."""
    soup = BeautifulSoup(html, "html.parser")
    vistos, faq = set(), []
    itens = soup.select(", ".join(SELECTORES_FAQ))
    for el in itens:
        if _na_navegacao(el) or RE_TITULO_NAO_FAQ.search(_titulo_do_contentor(el)):
            continue
        cabeca = el.find("summary") if el.name == "details" else el.find("h3")
        if cabeca is None:
            continue
        pergunta = normalizar(cabeca.get_text(" ", strip=True))
        if not pergunta or pergunta in vistos:
            continue
        resposta = copy.copy(el)
        for x in resposta.select("summary, h3, .fonte-inline"):
            x.decompose()
        texto = normalizar(resposta.get_text(" "))
        if texto:
            vistos.add(pergunta)
            faq.append((pergunta, texto))
    return faq


def _main_entity(faq):
    return [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
        for q, r in faq
    ]


def _indentar(dados, base: str) -> str:
    corpo = json.dumps(dados, ensure_ascii=False, indent=2)
    return "\n" + "\n".join(base + linha for linha in corpo.splitlines()) + "\n" + base


def sincronizar(html: str) -> str:
    """HTML com o `FAQPage` gerado a partir da FAQ visível (igual se nada muda)."""
    faq = faq_visivel(html)
    saida, pos = [], 0
    for m in RE_BLOCO_LD.finditer(html):
        dados = json.loads(m.group(2))
        objs = dados if isinstance(dados, list) else dados.get("@graph") if isinstance(dados, dict) and "@graph" in dados else None
        alvo = None
        if isinstance(dados, dict) and dados.get("@type") == "FAQPage":
            alvo = "raiz"
        elif objs is not None and any(isinstance(o, dict) and o.get("@type") == "FAQPage" for o in objs):
            alvo = "lista"
        if alvo is None:
            continue
        inicio_linha = html.rfind("\n", 0, m.start()) + 1
        base = re.match(r"[ \t]*", html[inicio_linha:m.start()]).group(0)
        if alvo == "raiz":
            if not faq:
                fim = m.end()
                if html[fim:fim + 1] == "\n":
                    fim += 1
                saida.append(html[pos:inicio_linha])
                pos = fim
                continue
            novo = dict(dados)
            novo["mainEntity"] = _main_entity(faq)
        else:
            lista = [o for o in objs if not (isinstance(o, dict) and o.get("@type") == "FAQPage")] if not faq else [
                {**o, "mainEntity": _main_entity(faq)} if isinstance(o, dict) and o.get("@type") == "FAQPage" else o
                for o in objs
            ]
            novo = lista if isinstance(dados, list) else {**dados, "@graph": lista}
        if novo == dados:
            continue
        saida.append(html[pos:m.start(2)])
        saida.append(_indentar(novo, base + "  "))
        pos = m.end(2)
    saida.append(html[pos:])
    return "".join(saida)


def paginas_com_faq(raiz: Path = RAIZ) -> list[Path]:
    return [p for p in sorted(encontrar_paginas(raiz)) if '"FAQPage"' in p.read_text(encoding="utf-8")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="lista o que mudaria (omissão)")
    g.add_argument("--check", action="store_true", help="falha se alguma página mudaria")
    g.add_argument("--write", action="store_true")
    ap.add_argument("paginas", nargs="*")
    a = ap.parse_args(argv)
    alvos = [RAIZ / p for p in a.paginas] if a.paginas else paginas_com_faq()
    mudam = []
    for p in alvos:
        antes = p.read_text(encoding="utf-8")
        depois = sincronizar(antes)
        if depois != antes:
            mudam.append(p.relative_to(RAIZ).as_posix())
            if a.write:
                p.write_text(depois, encoding="utf-8")
    acao = "alteradas" if a.write else "a alterar"
    print(f"Páginas com FAQPage: {len(alvos)} · {acao}: {len(mudam)}")
    for m in mudam:
        print(f"  - {m}")
    return 1 if (a.check and mudam) else 0


if __name__ == "__main__":
    sys.exit(main())
