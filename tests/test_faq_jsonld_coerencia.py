"""
Guarda da FAQ: o JSON-LD `FAQPage` tem de dizer o mesmo que a FAQ visível.

O JSON-LD é escrito à mão, ao lado da FAQ visível, e as duas cópias já
divergiram: um facto corrigido no corpo ficava antigo no JSON-LD, e há
perguntas no JSON-LD que a página não mostra (issue #352). Corre sobre as
páginas reais.

Regras, por página com `FAQPage`:
1. cada pergunta do JSON-LD aparece na página (num `<summary>` ou no `h3`
   de um `.faq-item`) com o mesmo texto;
2. a resposta do JSON-LD é igual ao texto visível da resposta — espaços
   normalizados, HTML retirado, com o texto da `.fonte-inline` no fim;
3. a secção de FAQ visível não tem perguntas fora do JSON-LD.

O que conta como FAQ visível: `<details>`/`.faq-item` fora da navegação
cuja pergunta exista no JSON-LD, os `<details class="zona-cinzenta">`, e
todos os que estão num contentor cujo `h2` seja de perguntas
(`RE_TITULO_FAQ`). Os «Erros comuns» e as outras
caixas recolhíveis nunca contam.

Zero divergências, sem excepções: a lista de transição
(`FAQ_DIVERGENCIAS_POR_CORRIGIR`, com tecto) chegou a 0 e saiu. O JSON-LD é
gerado por `scripts/sincronizar_faq_jsonld.py`; `--check` do gerador é a
guarda principal (`test_gerador_check_sem_alteracoes`), e esta leitura
independente da FAQ fica como segunda verificação.
"""
import copy
import difflib
import json
import re
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import encontrar_paginas

RAIZ = Path(__file__).parent.parent

RE_TITULO_FAQ = re.compile(r"(?i)d[úu]vidas|perguntas|zonas cinzentas|problemas comuns")
# Par emparelhado quando a pergunta tem redacção diferente nos dois sítios.
LIMIAR_PERGUNTA_PARECIDA = 0.75

TIPOS = {
    "resposta_diferente": "a resposta do JSON-LD não é igual à visível",
    "pergunta_diferente": "a pergunta tem redacção diferente no JSON-LD e na página",
    "so_jsonld": "pergunta no JSON-LD que a página não mostra",
    "so_visivel": "pergunta da FAQ visível sem par no JSON-LD",
}


def _normalizar(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+([.,;:!?)»])", r"\1", texto)
    return re.sub(r"([(«])\s+", r"\1", texto)


def _texto(html_ou_el) -> str:
    if isinstance(html_ou_el, str):
        html_ou_el = BeautifulSoup(html_ou_el, "html.parser")
    return _normalizar(html_ou_el.get_text(" "))


def faq_jsonld(soup) -> dict:
    """Pergunta → resposta, de todos os `FAQPage` da página."""
    faq = {}
    for sc in soup.find_all("script", type="application/ld+json"):
        dados = json.loads(sc.string)
        objs = dados if isinstance(dados, list) else dados.get("@graph", [dados])
        for o in objs:
            if isinstance(o, dict) and o.get("@type") == "FAQPage":
                for q in o.get("mainEntity", []):
                    faq[_normalizar(q["name"])] = _texto(q["acceptedAnswer"]["text"])
    return faq


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


def faq_visivel(soup, perguntas_jsonld) -> dict:
    """Pergunta → resposta, da FAQ que a página mostra."""
    faq = {}
    for el in soup.select("details, .faq-item"):
        if _na_navegacao(el):
            continue
        cabeca = el.find("summary") if el.name == "details" else el.find("h3")
        if cabeca is None:
            continue
        pergunta = _normalizar(cabeca.get_text(" ", strip=True))
        classes = el.get("class") or []
        e_faq = (
            "faq-item" in classes
            or "zona-cinzenta" in classes  # <details class="zona-cinzenta"> solto no <main>
            or RE_TITULO_FAQ.search(_titulo_do_contentor(el))
        )
        if not (e_faq or pergunta in perguntas_jsonld) or pergunta in faq:
            continue  # pergunta repetida na página: conta a primeira
        resposta = copy.copy(el)
        for x in resposta.select("summary, h3"):
            x.decompose()
        fontes = [_texto(x) for x in resposta.select(".fonte-inline")]
        for x in resposta.select(".fonte-inline"):
            x.decompose()
        faq[pergunta] = _normalizar(" ".join([_texto(resposta), *fontes]))
    return faq


def divergencias_da_pagina(html: str) -> set:
    """(tipo, pergunta) de cada divergência. A pergunta é a do JSON-LD,
    excepto em `so_visivel`."""
    soup = BeautifulSoup(html, "html.parser")
    ld = faq_jsonld(soup)
    if not ld:
        return set()
    vis = faq_visivel(soup, ld)
    pares = {q: q for q in ld if q in vis}
    for q in ld:
        if q in pares:
            continue
        livres = [v for v in vis if v not in ld and v not in pares.values()]
        cands = sorted(
            ((difflib.SequenceMatcher(None, q.lower(), v.lower()).ratio(), v) for v in livres),
            reverse=True,
        )
        if cands and cands[0][0] >= LIMIAR_PERGUNTA_PARECIDA:
            pares[q] = cands[0][1]
    out = set()
    for q, resposta in ld.items():
        if q not in pares:
            out.add(("so_jsonld", q))
        elif pares[q] != q:
            out.add(("pergunta_diferente", q))
        elif vis[q] != resposta:
            out.add(("resposta_diferente", q))
    emparelhadas = set(pares.values())
    for v in vis:
        if v not in emparelhadas:
            out.add(("so_visivel", v))
    return out


def _paginas_com_faq():
    return [
        p for p in sorted(encontrar_paginas(RAIZ))
        if '"FAQPage"' in p.read_text(encoding="utf-8")
    ]


def _rel(p: Path) -> str:
    return p.relative_to(RAIZ).as_posix()


PAGINAS = _paginas_com_faq()


@pytest.mark.parametrize("pagina", PAGINAS, ids=_rel)
def test_faq_visivel_e_jsonld_coincidem(pagina):
    divs = sorted(divergencias_da_pagina(pagina.read_text(encoding="utf-8")))
    assert not divs, (
        "a FAQ visível e o JSON-LD divergem — corre "
        "`python scripts/sincronizar_faq_jsonld.py --write`:\n"
        + "\n".join(f"  - {TIPOS[t]}: «{q}»" for t, q in divs)
    )


def test_gerador_check_sem_alteracoes(capsys):
    import sincronizar_faq_jsonld as gerador

    codigo = gerador.main(["--check"])
    assert codigo == 0, capsys.readouterr().out


# ---------- casos sintéticos: cada falha é detectada ----------

def _pagina(ld_faq, visivel, titulo="Dúvidas frequentes", extra=""):
    ld = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
            for q, r in ld_faq
        ],
    }
    dets = "".join(
        f"<details><summary><h3>{q}</h3></summary><div class='resposta'><p>{r}</p>"
        f"<p class='fonte-inline'>Fonte: x · Verificado a 1/01/2026</p></div></details>"
        for q, r in visivel
    )
    return (
        f"<html><head><script type='application/ld+json'>{json.dumps(ld)}</script></head>"
        f"<body><section class='zona-cinzenta'><h2>{titulo}</h2>{dets}</section>{extra}</body></html>"
    )


FONTE = " Fonte: x · Verificado a 1/01/2026"


def test_sintetico_par_igual_nao_diverge():
    html = _pagina([("Quem?", "Todos, com <strong>A</strong>." + FONTE)], [("Quem?", "Todos, com <strong>A</strong>.")])
    assert divergencias_da_pagina(html) == set()


def test_sintetico_fonte_inline_em_falta_no_jsonld_diverge():
    html = _pagina([("Quem?", "Todos.")], [("Quem?", "Todos.")])
    assert divergencias_da_pagina(html) == {("resposta_diferente", "Quem?")}


def test_sintetico_resposta_diferente():
    html = _pagina([("Quem?", "Todos." + FONTE)], [("Quem?", "Só alguns.")])
    assert divergencias_da_pagina(html) == {("resposta_diferente", "Quem?")}


def test_sintetico_so_jsonld_e_so_visivel():
    html = _pagina([("Quanto custa?", "Nada.")], [("Onde peço?", "Na escola.")])
    assert divergencias_da_pagina(html) == {("so_jsonld", "Quanto custa?"), ("so_visivel", "Onde peço?")}


def test_sintetico_pergunta_com_redaccao_diferente():
    html = _pagina([("Quanto tempo dura o apoio em 2026?", "Um ano." + FONTE)], [("Quanto tempo dura o apoio?", "Um ano.")])
    assert divergencias_da_pagina(html) == {("pergunta_diferente", "Quanto tempo dura o apoio em 2026?")}


def test_sintetico_erros_comuns_nunca_contam_como_faq():
    extra = (
        "<section class='zona-cinzenta'><h2>Erros comuns</h2>"
        "<details><summary>Pensar que é automático</summary><p>Não é.</p></details></section>"
    )
    html = _pagina([("Quem?", "Todos." + FONTE)], [("Quem?", "Todos.")], extra=extra)
    assert divergencias_da_pagina(html) == set()
