"""Caminhos de menu da Segurança Social Direta — só os conferidos.

Um caminho de menu ("A → B → C", também com ">" ou "&gt;") escrito num bloco
de texto depois de uma menção à Segurança Social Direta tem de estar em
CAMINHOS_PERMITIDOS. A lista só cresce com um caminho conferido por uma
pessoa no próprio portal (issue/PR #304; conferidos pelo Nuno a 05/10/2026)
— nunca de memória nem copiado de outra página do site.

Blocos: cada string do JSON-LD e cada bloco de texto visível (li, p, div,
td, …). Comentários HTML, <script> e <style> não contam.
"""

import html
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

CAMINHOS_PERMITIDOS = (
    # Pedir o abono de família.
    "Família → Abono de Família e de Pré-Natal → Pedir e consultar → Pedir novo abono de família",
    # Pedir a reavaliação do abono de família.
    "Família → Abono de Família e de Pré-Natal → Pedir e consultar → Pedir reavaliação do abono de família",
    # Alterar o IBAN.
    "Perfil → Conta Bancária",
    # Pedir a majoração do subsídio de desemprego.
    "Trabalho → Desemprego → Subsídio de Desemprego → Consultar e Pedir Majoração de Subsídio de Desemprego",
    # Pedir a PSI.
    "Família → Deficiência e incapacidade → Prestação Social para a Inclusão → Consultar e pedir",
    # Entregar a Declaração de Situação Familiar.
    "Família → Agregado e Relações Familiares → Declarações de Situação Familiar",
    # Pedir o RSI e o CSI no e-Clic.
    "Evento de vida: Apoio social → Assunto: Rendimento Social de Inserção → Motivo: Apresentar um pedido",
    "Evento de vida: Apoio social → Assunto: Complemento Solidário para Idosos → Motivo: Apresentar um pedido",
    # Consultar o NISS.
    "Perfil → Dados pessoais",
    # Prova escolar: representação de um menor e pensão de sobrevivência.
    "Perfil → Representações → Registar Representação Legal",
    "Pensões → Prova Escolar",
)

MENCAO = re.compile(r"Segurança Social Direta|SS Direta", re.I)
SEP = r"\s*(?:→|>)\s*"
SEGMENTO = r"[^→>.,;()\[\]]+"
CAMINHO = re.compile(rf"{SEGMENTO}(?:{SEP}{SEGMENTO})+")
FIM_DE_BLOCO = re.compile(
    r"</(?:li|p|div|td|th|h[1-6]|dt|dd|summary|pre|section|header|footer|main)>",
    re.I,
)


def _normalizar(texto: str) -> str:
    texto = re.sub(r"[\"'“”‘’«»]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _segmentos(caminho: str) -> list[str]:
    return [_normalizar(s) for s in re.split(SEP, caminho)]


PERMITIDOS = [_segmentos(c) for c in CAMINHOS_PERMITIDOS]


def _strings_json(valor):
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for v in valor.values():
            yield from _strings_json(v)
    elif isinstance(valor, list):
        for v in valor:
            yield from _strings_json(v)


def blocos(fonte: str) -> list[str]:
    resultado = []
    for bloco in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', fonte, re.S
    ):
        resultado.extend(_strings_json(json.loads(bloco)))
    corpo = re.sub(r"<!--.*?-->", " ", fonte, flags=re.S)
    corpo = re.sub(r"<(script|style)\b.*?</\1>", " ", corpo, flags=re.S | re.I)
    for parte in FIM_DE_BLOCO.split(corpo):
        texto = html.unescape(re.sub(r"<[^>]+>", " ", parte))
        resultado.append(re.sub(r"\s+", " ", texto))
    return resultado


def _permitido(segs: list[str]) -> bool:
    for p in PERMITIDOS:
        cauda = segs[-len(p):]
        if len(cauda) != len(p) or cauda[1:] != p[1:]:
            continue
        if not cauda[0].lower().endswith(p[0].lower()):
            continue
        # O que vem antes da cauda só pode ser o próprio portal.
        resto = segs[: len(segs) - len(p)]
        if all(MENCAO.search(s) for s in resto):
            return True
    return False


def caminhos_depois_da_mencao(texto: str) -> list[str]:
    m = MENCAO.search(texto)
    if not m:
        return []
    achados = []
    for c in CAMINHO.finditer(texto):
        if c.end() <= m.start():
            continue
        segs = _segmentos(c.group())
        if len([s for s in segs if s]) < 2 or not all(segs):
            continue
        # "Segurança Social Direta → X" sem mais nada não é um caminho de menu.
        if len(segs) == 2 and MENCAO.search(segs[0]):
            continue
        achados.append(" → ".join(segs))
    return achados


PAGINAS = encontrar_paginas(RAIZ)


@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: str(p.relative_to(RAIZ)))
def test_caminhos_ssd_so_os_conferidos(pagina):
    fonte = pagina.read_text(encoding="utf-8")
    nao_conferidos = [
        c
        for b in blocos(fonte)
        for c in caminhos_depois_da_mencao(b)
        if not _permitido(_segmentos(c))
    ]
    assert nao_conferidos == [], (
        "Caminho de menu da Segurança Social Direta fora de CAMINHOS_PERMITIDOS "
        f"(tests/test_caminhos_ssd.py): {nao_conferidos}"
    )


def test_cada_caminho_permitido_ainda_existe_no_site():
    texto_site = " ".join(
        " → ".join(_segmentos(c.group()))
        for pagina in PAGINAS
        for b in blocos(pagina.read_text(encoding="utf-8"))
        for c in CAMINHO.finditer(b)
    )
    orfaos = [c for c in CAMINHOS_PERMITIDOS if " → ".join(_segmentos(c)) not in texto_site]
    assert orfaos == [], f"Entradas órfãs em CAMINHOS_PERMITIDOS: {orfaos}"


@pytest.mark.parametrize(
    "texto",
    [
        "Na Segurança Social Direta, vai a Prestações → Crianças e Jovens → Abono.",
        "Segurança Social Direta (Perfil &gt; Agregado e relações familiares)",
        "Segurança Social Direta → Apoios Sociais → Complemento Solidário para Idosos.",
        "Entra na Segurança Social Direta e vai a Família → Abono de Família e de Pré-Natal → Pedir e consultar → Pedir outra coisa.",
    ],
)
def test_caminho_nao_conferido_falha(texto):
    achados = caminhos_depois_da_mencao(html.unescape(texto))
    assert achados and not all(_permitido(_segmentos(c)) for c in achados)


@pytest.mark.parametrize(
    "texto",
    [
        "na Segurança Social Direta (Família > Deficiência e incapacidade > Prestação Social para a Inclusão > Consultar e pedir)",
        "Entra na Segurança Social Direta → Perfil → Conta Bancária, indica o IBAN novo.",
        "Portal das Finanças (Dados Cadastrais → Morada) e na Segurança Social Direta, por telefone.",
        "Segurança Social Direta → Pagamentos",
    ],
)
def test_caminho_conferido_ou_anterior_a_mencao_passa(texto):
    achados = caminhos_depois_da_mencao(texto)
    assert all(_permitido(_segmentos(c)) for c in achados)
