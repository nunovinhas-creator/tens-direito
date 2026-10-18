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
   normalizados, HTML retirado, `.fonte-inline` excluída;
3. a secção de FAQ visível não tem perguntas fora do JSON-LD.

O que conta como FAQ visível: `<details>`/`.faq-item` fora da navegação
cuja pergunta exista no JSON-LD, os `<details class="zona-cinzenta">`, e
todos os que estão num contentor cujo `h2` seja de perguntas
(`RE_TITULO_FAQ`). Os «Erros comuns» e as outras
caixas recolhíveis nunca contam.

`FAQ_DIVERGENCIAS_POR_CORRIGIR` (`tests/faq_divergencias_por_corrigir.json`)
é a lista de transição das divergências antigas. Falha: uma divergência
fora da lista; uma entrada da lista que já não diverge (tem de sair); e a
lista maior do que `TETO_FAQ_DIVERGENCIAS`. O tecto só desce (CLAUDE.md).
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
FICHEIRO_LISTA = RAIZ / "tests" / "faq_divergencias_por_corrigir.json"

# Só desce: ao corrigir divergências, tirá-las da lista e baixar este número.
TETO_FAQ_DIVERGENCIAS = 334

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
        for x in resposta.select("summary, h3, .fonte-inline"):
            x.decompose()
        faq[pergunta] = _texto(resposta)
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


def _carregar_lista():
    entradas = json.loads(FICHEIRO_LISTA.read_text(encoding="utf-8"))
    return [(e["pagina"], e["tipo"], e["pergunta"]) for e in entradas]


FAQ_DIVERGENCIAS_POR_CORRIGIR = _carregar_lista()
PAGINAS = _paginas_com_faq()


@pytest.fixture(scope="module")
def divergencias_reais():
    return {
        (_rel(p), tipo, q)
        for p in PAGINAS
        for tipo, q in divergencias_da_pagina(p.read_text(encoding="utf-8"))
    }


def test_lista_nunca_maior_que_o_teto():
    assert len(FAQ_DIVERGENCIAS_POR_CORRIGIR) <= TETO_FAQ_DIVERGENCIAS, (
        f"FAQ_DIVERGENCIAS_POR_CORRIGIR tem {len(FAQ_DIVERGENCIAS_POR_CORRIGIR)} entradas, "
        f"acima do tecto de {TETO_FAQ_DIVERGENCIAS}. A lista só encolhe: corrige a FAQ "
        "em vez de a acrescentar."
    )


def test_lista_sem_duplicados_e_com_tipos_validos():
    assert len(set(FAQ_DIVERGENCIAS_POR_CORRIGIR)) == len(FAQ_DIVERGENCIAS_POR_CORRIGIR)
    invalidos = [e for e in FAQ_DIVERGENCIAS_POR_CORRIGIR if e[1] not in TIPOS]
    assert not invalidos, f"tipos inválidos: {invalidos}"


@pytest.mark.parametrize("pagina", PAGINAS, ids=_rel)
def test_faq_visivel_e_jsonld_coincidem(pagina, divergencias_reais):
    rel = _rel(pagina)
    permitidas = {e for e in FAQ_DIVERGENCIAS_POR_CORRIGIR if e[0] == rel}
    reais = {e for e in divergencias_reais if e[0] == rel}
    novas = sorted(reais - permitidas)
    assert not novas, "divergências novas entre a FAQ visível e o JSON-LD:\n" + "\n".join(
        f"  - {TIPOS[t]}: «{q}»" for _, t, q in novas
    )


def test_entradas_da_lista_ainda_divergem(divergencias_reais):
    resolvidas = sorted(set(FAQ_DIVERGENCIAS_POR_CORRIGIR) - divergencias_reais)
    assert not resolvidas, (
        "entradas de FAQ_DIVERGENCIAS_POR_CORRIGIR que já não divergem — tira-as da "
        "lista e baixa TETO_FAQ_DIVERGENCIAS:\n"
        + "\n".join(f"  - {p} · {t} · «{q}»" for p, t, q in resolvidas)
    )


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


def test_sintetico_par_igual_nao_diverge():
    html = _pagina([("Quem?", "Todos, com <strong>A</strong>.")], [("Quem?", "Todos, com <strong>A</strong>.")])
    assert divergencias_da_pagina(html) == set()


def test_sintetico_resposta_diferente():
    html = _pagina([("Quem?", "Todos.")], [("Quem?", "Só alguns.")])
    assert divergencias_da_pagina(html) == {("resposta_diferente", "Quem?")}


def test_sintetico_so_jsonld_e_so_visivel():
    html = _pagina([("Quanto custa?", "Nada.")], [("Onde peço?", "Na escola.")])
    assert divergencias_da_pagina(html) == {("so_jsonld", "Quanto custa?"), ("so_visivel", "Onde peço?")}


def test_sintetico_pergunta_com_redaccao_diferente():
    html = _pagina([("Quanto tempo dura o apoio em 2026?", "Um ano.")], [("Quanto tempo dura o apoio?", "Um ano.")])
    assert divergencias_da_pagina(html) == {("pergunta_diferente", "Quanto tempo dura o apoio em 2026?")}


def test_sintetico_erros_comuns_nunca_contam_como_faq():
    extra = (
        "<section class='zona-cinzenta'><h2>Erros comuns</h2>"
        "<details><summary>Pensar que é automático</summary><p>Não é.</p></details></section>"
    )
    html = _pagina([("Quem?", "Todos.")], [("Quem?", "Todos.")], extra=extra)
    assert divergencias_da_pagina(html) == set()
