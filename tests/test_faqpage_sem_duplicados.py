"""Cada pergunta aparece uma só vez no JSON-LD FAQPage de cada página.

Caso real (bolsa-de-merito.html, 2026-10-06): o FAQPage tinha 17 perguntas,
três delas repetidas (uma três vezes) — blocos colados em sessões diferentes
sem ninguém reparar, porque o JSON-LD não se vê na página.
"""

import json
import re
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import encontrar_paginas, RAIZ

PAGINAS = sorted(encontrar_paginas(), key=lambda p: str(p))
_JSONLD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def _normalizar(texto: str) -> str:
    return re.sub(r"\s+", " ", texto).strip().casefold()


def perguntas_faqpage(html: str) -> list[str]:
    perguntas = []
    for bloco in _JSONLD.findall(html):
        try:
            dados = json.loads(bloco)
        except json.JSONDecodeError:
            continue  # JSON inválido é apanhado por test_higiene_indexacao
        objectos = dados if isinstance(dados, list) else dados.get("@graph", [dados])
        for obj in objectos:
            if isinstance(obj, dict) and obj.get("@type") == "FAQPage":
                perguntas += [q.get("name", "") for q in obj.get("mainEntity", [])]
    return perguntas


def duplicadas(perguntas: list[str]) -> list[str]:
    vistas, repetidas = set(), []
    for p in perguntas:
        n = _normalizar(p)
        if n in vistas and p not in repetidas:
            repetidas.append(p)
        vistas.add(n)
    return repetidas


def test_detecta_repeticao_com_espacos_e_maiusculas_diferentes():
    assert duplicadas(["Quem tem direito?", "  quem  tem direito? ", "Outra?"]) == ["  quem  tem direito? "]
    assert duplicadas(["A?", "B?"]) == []


def test_detecta_repeticao_num_html():
    html = (
        '<script type="application/ld+json">{"@type": "FAQPage", "mainEntity": ['
        '{"@type": "Question", "name": "X?"}, {"@type": "Question", "name": "X?"}]}</script>'
    )
    assert duplicadas(perguntas_faqpage(html)) == ["X?"]


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: str(p.relative_to(RAIZ)))
def test_faqpage_sem_perguntas_repetidas(pagina):
    repetidas = duplicadas(perguntas_faqpage(pagina.read_text(encoding="utf-8")))
    assert repetidas == [], f"{pagina.name}: perguntas repetidas no FAQPage: {repetidas}"


def _perguntas_visiveis_bolsa(soup):
    pares = []
    for item in soup.select("section.faq-geo .faq-item"):
        pares.append((item.h3.get_text(" ", strip=True), item.p.get_text(" ", strip=True)))
    for det in soup.select("section.zona-cinzenta details"):
        ps = [p for p in det.select(".resposta p") if "fonte-inline" not in (p.get("class") or [])]
        pares.append((det.summary.get_text(" ", strip=True), " ".join(p.get_text(" ", strip=True) for p in ps)))
    return [(_normalizar(q), _normalizar(a)) for q, a in pares]


def test_bolsa_de_merito_faqpage_igual_ao_corpo():
    html = (RAIZ / "bolsa-de-merito.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    jsonld = []
    for bloco in _JSONLD.findall(html):
        dados = json.loads(bloco)
        if dados.get("@type") == "FAQPage":
            jsonld = [(_normalizar(q["name"]), _normalizar(q["acceptedAnswer"]["text"])) for q in dados["mainEntity"]]
    # get_text(" ") põe espaço antes da pontuação que segue uma tag
    visiveis = [(q, re.sub(r" ([,.])", r"\1", a)) for q, a in _perguntas_visiveis_bolsa(soup)]
    assert jsonld == visiveis
