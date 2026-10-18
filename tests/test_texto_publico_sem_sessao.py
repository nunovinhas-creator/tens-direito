"""Texto público nunca fala da "sessão" de trabalho da redação.

Frases como "bloqueado nesta sessão" ou "lida na sessão seguinte" descrevem
o processo interno de verificação, não o grau de confirmação de um facto —
contra a regra de nunca falar de automação em páginas públicas (CLAUDE.md,
"REGRAS DE CONTEÚDO" → "Não fazer"). O grau diz-se assim: "confirmado em
fonte secundária, não no texto oficial do Diário da República".

Âmbito: todo o texto que o leitor ou um motor de busca recebe — corpo,
atributos, meta tags e JSON-LD. Comentários HTML e JavaScript ficam de fora.
"Iniciar sessão" (entrar numa conta) é uso legítimo e continua permitido.
"""
import glob
import json
import os
import re
from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Comment

RAIZ = Path(__file__).parent.parent

PROIBIDO = re.compile(
    r"\b(?:n?esta|n?essa|desta|dessa|n?aquela|daquela|numa|duma|outra)\s+sess(?:ão|ões|ao)\b"
    r"|\b(?:na|da|pela|numa)\s+sess(?:ão|ões|ao)\s+(?:seguinte|anterior|de\s+verifica[çc][ãa]o)\b"
    r"|\bsess(?:ão|ões|ao)\s+(?:seguinte|anterior)\b",
    re.IGNORECASE,
)


def textos_publicos(html):
    """(origem, texto) de tudo o que é público: texto, atributos e JSON-LD."""
    soup = BeautifulSoup(html, "html.parser")
    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    res = []
    for sc in soup.find_all(["script", "style"]):
        if sc.name == "script" and sc.get("type") == "application/ld+json":
            res.append(("JSON-LD", json.dumps(json.loads(sc.string or "null"), ensure_ascii=False)))
        sc.extract()
    for el in soup.find_all(True):
        for nome, valor in el.attrs.items():
            if isinstance(valor, str):
                res.append((f"atributo {nome}", valor))
    res.append(("texto", " ".join(soup.get_text(" ").split())))
    return res


def ocorrencias(html):
    achados = []
    for origem, texto in textos_publicos(html):
        for m in PROIBIDO.finditer(texto):
            achados.append(f"{origem}: …{texto[max(0, m.start() - 80):m.end() + 40]}…")
    return achados


def _paginas():
    return sorted(glob.glob(str(RAIZ / "*.html")) + glob.glob(str(RAIZ / "p" / "*.html"))
                  + glob.glob(str(RAIZ / "documentos" / "*.html")))


@pytest.mark.parametrize("caminho", _paginas(), ids=lambda c: os.path.relpath(c, RAIZ))
def test_pagina_sem_sessao_de_trabalho_em_texto_publico(caminho):
    achados = ocorrencias(Path(caminho).read_text(encoding="utf-8"))
    assert not achados, "texto público fala da sessão de trabalho:\n" + "\n".join(achados)


@pytest.mark.parametrize("html", [
    "<p>Acesso directo bloqueado nesta sessão.</p>",
    "<p>Esta sessão não conseguiu confirmar a citação.</p>",
    "<p><strong>Lido directamente na sessão seguinte (2 de setembro de 2026):</strong></p>",
    "<p>Confirmado numa outra sessão.</p>",
    '<meta name="description" content="Verificado nesta sessão">',
    '<script type="application/ld+json">{"text": "bloqueado nesta sessão"}</script>',
])
def test_guarda_apanha_as_variantes(html):
    assert ocorrencias(html)


@pytest.mark.parametrize("html", [
    "<p>Inicia sessão com o teu NIF e palavra-passe.</p>",
    "<p>Passa a ser possível iniciar sessão com o teu email.</p>",
    "<p>Texto.</p><!-- acesso bloqueado nesta sessão -->",
    "<script>// confirmado nesta sessão\nvar x = 1;</script>",
])
def test_guarda_permite_iniciar_sessao_e_ignora_comentarios(html):
    assert not ocorrencias(html)
