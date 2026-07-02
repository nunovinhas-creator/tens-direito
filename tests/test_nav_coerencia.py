"""
Rede de segurança da Fase 4: confirma, sobre as páginas REAIS do
repositório, que a nav unificada (scripts/sincronizar_nav.py) está
correctamente aplicada — exactamente um bloco NAV por página, zero
resíduos da nav antiga (classes/ids/handlers que já não existem no
template partilhado), e as referências a nav.css/nav.js/pesquisa.js
presentes.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import encontrar_paginas, RAIZ

PAGINAS = sorted(encontrar_paginas(), key=lambda p: str(p))
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]

RESIDUOS_NAV_ANTIGA = [
    'class="nav-link"',
    'class="hamburger"',
    'id="menuMobile"',
    'onclick="toggleMobileMenu',
    'onclick="toggleMenu(',
    'onclick="toggleSimDropdown',
    'id="navSimDropdown"',
    'id="mobileMenu"',
    'id="mob"',
]


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_exactamente_um_bloco_nav(caminho):
    html = caminho.read_text(encoding="utf-8")
    n_inicio = len(re.findall(r"<!-- NAV:INICIO -->", html))
    n_fim = len(re.findall(r"<!-- NAV:FIM -->", html))
    assert n_inicio == 1, f"{caminho.name}: {n_inicio} marcador(es) NAV:INICIO, esperava 1"
    assert n_fim == 1, f"{caminho.name}: {n_fim} marcador(es) NAV:FIM, esperava 1"


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_sem_residuos_da_nav_antiga(caminho):
    html = caminho.read_text(encoding="utf-8")
    encontrados = [r for r in RESIDUOS_NAV_ANTIGA if r in html]
    assert not encontrados, f"{caminho.name}: resíduos da nav antiga ainda presentes: {encontrados}"


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_referencias_nav_presentes(caminho):
    html = caminho.read_text(encoding="utf-8")
    for ref in ("/assets/css/nav.css", "/assets/js/nav.js", "/scripts/pesquisa.js"):
        assert ref in html, f"{caminho.name}: referência '{ref}' em falta no <head>"


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_nav_tem_dropdown_apoios_e_pesquisa(caminho):
    html = caminho.read_text(encoding="utf-8")
    m = re.search(r"<!-- NAV:INICIO -->([\s\S]*?)<!-- NAV:FIM -->", html)
    assert m, f"{caminho.name}: bloco NAV vazio ou em falta"
    bloco = m.group(1)
    assert 'id="navApoiosDropdown"' in bloco, f"{caminho.name}: dropdown Apoios em falta na nav"
    assert 'id="campo-pesquisa-nav"' in bloco, f"{caminho.name}: pesquisa da nav (desktop) em falta"
    assert 'id="campo-pesquisa-nav-movel"' in bloco, f"{caminho.name}: pesquisa da nav (mobile) em falta"
    assert bloco.count('href="/comecar-aqui.html"') >= 1, f"{caminho.name}: link 'Começa aqui' em falta na nav"
