#!/usr/bin/env python3
"""
scripts/inserir_botao_partilhar.py

Insere automaticamente o botão "Partilhar este artigo"
(assets/js/share.js + assets/css/share.css) em todas as páginas HTML
manuais do projecto, sem editar nenhum ficheiro à mão.

    python scripts/inserir_botao_partilhar.py

Páginas processadas: todo o `*.html` na raiz e em `p/`, EXCEPTO as da
lista `AUTO_GERADOS` (reutilizada de `verificar_datas.py` —
`index.html`, `noticias.html`, `404.html`), que já estão fora de toda a
restante automação deste repositório pelo mesmo motivo: são geradas ou
reescritas por outros scripts, não são "artigos" manuais.

Idempotência (obrigatória): cada página só é alterada uma vez — a
marca `botao-partilhar` já presente no ficheiro é o sinal de que a
página já foi tratada, e o script não lhe toca outra vez. Reexecutar
este script sobre páginas já tratadas produz um ficheiro byte a byte
idêntico ao anterior.

Estratégia de inserção (uma única regra, aplicada da mesma forma a
todas as páginas):
1. As referências a `assets/css/share.css` e `assets/js/share.js` são
   inseridas imediatamente antes do único `</head>` da página.
2. O bloco do botão é inserido imediatamente a seguir ao único `</h1>`
   da página (todas as páginas actuais têm exactamente um). Se uma
   página não tiver `<h1>`, insere-se antes do único `</main>` (fim da
   zona principal do artigo). Sem `<h1>` nem `<main>`, a página é
   reportada como não alterável — nunca se adivinha um ponto de
   inserção arriscado.

Este script só toca no conteúdo indicado acima — nunca altera título,
meta description, dados estruturados (JSON-LD), URLs ou o resto do
conteúdo de cada página.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verificar_datas import AUTO_GERADOS  # reutiliza a lista já existente — sem duplicar

RAIZ = Path(__file__).resolve().parent.parent

MARCADOR_IDEMPOTENCIA = "botao-partilhar"

BLOCO_BOTAO = (
    "\n<!-- partilhar:inicio -->\n"
    '<div class="partilhar-artigo">\n'
    '  <button type="button" class="botao-partilhar" aria-label="Partilhar este artigo">'
    "📤 Partilhar este artigo</button>\n"
    "</div>\n"
    "<!-- partilhar:fim -->\n"
)

TAGS_HEAD = (
    '  <link rel="stylesheet" href="/assets/css/share.css">\n'
    '  <script src="/assets/js/share.js" defer></script>\n'
)

_REGEX_H1_FECHO = re.compile(r"</h1\s*>", re.IGNORECASE)
_REGEX_MAIN_FECHO = re.compile(r"</main\s*>", re.IGNORECASE)
_REGEX_HEAD_FECHO = re.compile(r"</head\s*>", re.IGNORECASE)


@dataclass(frozen=True)
class ResultadoPagina:
    ficheiro: str
    alterada: bool
    motivo: str


def _inserir_bloco_botao(conteudo: str) -> Optional[str]:
    """Devolve o conteúdo com o bloco do botão inserido, ou None se não
    houver nenhum ponto de inserção seguro (nem <h1> nem <main>)."""
    match_h1 = _REGEX_H1_FECHO.search(conteudo)
    if match_h1:
        pos = match_h1.end()
        return conteudo[:pos] + BLOCO_BOTAO + conteudo[pos:]

    match_main = _REGEX_MAIN_FECHO.search(conteudo)
    if match_main:
        pos = match_main.start()
        return conteudo[:pos] + BLOCO_BOTAO + conteudo[pos:]

    return None


def _inserir_referencias_head(conteudo: str) -> str:
    """Acrescenta as tags de CSS/JS antes de </head>, a não ser que já
    lá estejam (idempotência independente da do botão, para recuperar
    correctamente de um estado parcial improvável)."""
    if "/assets/js/share.js" in conteudo:
        return conteudo
    match_head = _REGEX_HEAD_FECHO.search(conteudo)
    if not match_head:
        return conteudo
    pos = match_head.start()
    return conteudo[:pos] + TAGS_HEAD + conteudo[pos:]


def processar_pagina(caminho: Path, *, raiz: Path = RAIZ) -> ResultadoPagina:
    """Processa uma única página. Nunca lança excepção — qualquer
    problema (ficheiro ilegível, sem ponto de inserção) é devolvido
    como um ResultadoPagina com `alterada=False` e o motivo."""
    try:
        nome = str(caminho.relative_to(raiz))
    except ValueError:
        nome = str(caminho)

    try:
        conteudo_original = caminho.read_text(encoding="utf-8")
    except Exception as e:
        return ResultadoPagina(nome, False, f"erro ao ler ficheiro: {e}")

    if MARCADOR_IDEMPOTENCIA in conteudo_original:
        return ResultadoPagina(nome, False, "já tem o botão — sem alterações")

    tinha_h1 = bool(_REGEX_H1_FECHO.search(conteudo_original))
    novo_conteudo = _inserir_bloco_botao(conteudo_original)
    if novo_conteudo is None:
        return ResultadoPagina(nome, False, "sem <h1> nem <main> — sem ponto de inserção seguro")

    novo_conteudo = _inserir_referencias_head(novo_conteudo)

    try:
        caminho.write_text(novo_conteudo, encoding="utf-8")
    except Exception as e:
        return ResultadoPagina(nome, False, f"erro ao escrever ficheiro: {e}")

    motivo = "botão inserido após <h1>" if tinha_h1 else "botão inserido antes de </main> (sem <h1>)"
    return ResultadoPagina(nome, True, motivo)


def encontrar_paginas_alvo(raiz: Path = RAIZ) -> List[Path]:
    candidatos = sorted(raiz.glob("*.html")) + sorted(raiz.glob("p/*.html"))
    return [c for c in candidatos if c.name not in AUTO_GERADOS]


def _imprimir_relatorio(resultados: List[ResultadoPagina]) -> None:
    alteradas = [r for r in resultados if r.alterada]
    ja_tinham = [r for r in resultados if not r.alterada and r.motivo.startswith("já tem")]
    nao_alteraveis = [r for r in resultados if not r.alterada and not r.motivo.startswith("já tem")]

    print("=== Relatório — inserção do botão \"Partilhar este artigo\" ===\n")
    print(f"Páginas verificadas: {len(resultados)}")
    print(f"Páginas alteradas agora: {len(alteradas)}")
    print(f"Páginas já com o botão (sem alterações): {len(ja_tinham)}")
    print(f"Páginas não alteráveis: {len(nao_alteraveis)}")
    print(f"Excluídas automaticamente (AUTO_GERADOS): {', '.join(AUTO_GERADOS)}\n")

    if alteradas:
        print("Alteradas agora:")
        for r in alteradas:
            print(f"  - {r.ficheiro}: {r.motivo}")
        print()

    if nao_alteraveis:
        print("Não alteráveis (motivo):")
        for r in nao_alteraveis:
            print(f"  - {r.ficheiro}: {r.motivo}")
        print()

    print("Para adicionar o botão a novas páginas no futuro, basta voltar a")
    print("correr: python scripts/inserir_botao_partilhar.py")


def main() -> None:
    resultados = [processar_pagina(p) for p in encontrar_paginas_alvo()]
    _imprimir_relatorio(resultados)


if __name__ == "__main__":
    main()
