"""Texto público nunca fala do processo interno de verificação.

Frases como "bloqueado nesta sessão", "lida na sessão seguinte",
"triangulação", "acesso automatizado bloqueado" ou "devolve 403 a pedidos
automatizados" descrevem o processo interno, não o grau de confirmação de
um facto — contra a regra de nunca falar de automação em páginas públicas
(CLAUDE.md, "REGRAS DE CONTEÚDO" → "Não fazer"). O grau diz-se assim:
"confirmado em várias fontes secundárias independentes, não no texto
oficial do Diário da República".

Âmbito: todo o texto que o leitor ou um motor de busca recebe — corpo,
atributos, meta tags e JSON-LD. Comentários HTML e JavaScript ficam de fora.
"Iniciar sessão" (entrar numa conta) é uso legítimo e continua permitido, tal
como "bloqueado" fora de acesso a sites (vales MEGA, calculadora à espera
dos parâmetros, direito à dedução).
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
    # sessão de trabalho
    r"\b(?:n?esta|n?essa|desta|dessa|n?aquela|daquela|numa|duma|outra)\s+sess(?:ão|ões|ao)\b"
    r"|\b(?:na|da|pela|numa)\s+sess(?:ão|ões|ao)\s+(?:seguinte|anterior|de\s+verifica[çc][ãa]o)\b"
    r"|\bsess(?:ão|ões|ao)\s+(?:seguinte|anterior)\b"
    # método interno
    r"|\btriangul\w*"
    r"|\b(?:acesso|pedidos?|leitura|consulta)\s+automatizad\w*"
    # bloqueio ou código HTTP ligado a acesso a sites
    r"|\bacesso\b(?:[^.]|\.(?=\w)){0,80}?\bbloquead\w*"  # o ponto de um domínio não corta a frase
    r"|\bbloquead\w*\s+(?:nesta|a)\s+(?:verifica\w*|sess\w*|pedidos|bots?)\b"
    r"|\b(?:devolve|responde\s+com|dá)\s+(?:um\s+)?(?:erro\s+)?[45]\d\d\b"
    r"|\b[45]\d\d\s+(?:a|aos?)\s+(?:pedidos|bots?)\b",
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
def test_pagina_sem_processo_interno_em_texto_publico(caminho):
    achados = ocorrencias(Path(caminho).read_text(encoding="utf-8"))
    assert not achados, "texto público fala do processo interno de verificação:\n" + "\n".join(achados)


@pytest.mark.parametrize("html", [
    "<p>Acesso directo bloqueado nesta sessão.</p>",
    "<p>Esta sessão não conseguiu confirmar a citação.</p>",
    "<p><strong>Lido directamente na sessão seguinte (2 de setembro de 2026):</strong></p>",
    "<p>Confirmado numa outra sessão.</p>",
    '<meta name="description" content="Verificado nesta sessão">',
    '<script type="application/ld+json">{"text": "bloqueado nesta sessão"}</script>',
    "<p>Confirmado por triangulação de várias fontes.</p>",
    "<p>As três datas foram trianguladas por fontes secundárias.</p>",
    "<p>O acesso automatizado a bportugal.pt está bloqueado nesta verificação.</p>",
    "<p>O portal oficial devolve 403 a pedidos automatizados.</p>",
    "<p>Acesso directo a diariodarepublica.pt bloqueado.</p>",
])
def test_guarda_apanha_as_variantes(html):
    assert ocorrencias(html)


@pytest.mark.parametrize("html", [
    "<p>Inicia sessão com o teu NIF e palavra-passe.</p>",
    "<p>Passa a ser possível iniciar sessão com o teu email.</p>",
    "<p>Texto.</p><!-- acesso bloqueado nesta sessão -->",
    "<script>// confirmado nesta sessão\nvar x = 1;</script>",
    "<p>Se ele não o fizer, o teu direito à dedução não fica bloqueado.</p>",
    "<p>Os vales do ano seguinte ficam bloqueados para o NIF do educando.</p>",
    "<p>Esta calculadora fica bloqueada até os parâmetros carregarem.</p>",
    "<p>Página não encontrada (erro 404).</p>",
    "<p>Confirmado em várias fontes secundárias independentes, não no texto oficial do Diário da República.</p>",
])
def test_guarda_permite_usos_legitimos_e_ignora_comentarios(html):
    assert not ocorrencias(html)
