#!/usr/bin/env python3
"""Procura padrões de prompt injection em conteúdo importado de fontes
externas — scraper (`data/scraped/`), outros dados (`data/*.json`) e
relatórios do Shadow Mode (`shadow_history/`).

Guardrail permanente: o pipeline ingere conteúdo externo todos os dias
(scraper Playwright, feeds RSS). Este script nunca executa nem
interpreta o que encontra — só compara texto com padrões e reporta.
Corre em `integridade.yml` (só leitura, nunca escreve nem apaga nada).

    python scripts/verificar_injecao.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# Directórios onde entra conteúdo de fontes externas (scraper, RSS).
DIRETORIOS_A_VERIFICAR = ["data", "shadow_history"]

# Frases multi-palavra, não palavras soltas — para não gerar falsos
# positivos com vocabulário legítimo em português (ex.: "instrução",
# "verificar", "confidencial" aparecem em texto legal/institucional real).
PADROES_SUSPEITOS = [
    r"system[\s_-]?reminder",
    r"ignore (all |any |the )?(previous|above|prior) instructions?",
    r"disregard (all |any |the )?(previous|above|prior) instructions?",
    r"forget (all |any |the )?(previous|prior) (instructions|context)",
    r"do\s?not tell (the )?user",
    r"don'?t tell (the )?user",
    r"n[ãa]o (contes?|informes?|digas?) (ao|o) utilizador",
    r"n[ãa]o (contar|informar|dizer) (ao|o) utilizador",
    r"you are (now |actually )?(chatgpt|claude|an? ai\b|a language model)",
    r"act as (a|an) (ai|assistant|language model)",
    r"jailbreak",
    r"reveal (your|the) (system )?prompt",
    r"\[system\]|\{system\}|<\|system\|>|<\|im_start\|>|<\|im_end\|>",
    r"new instructions?\s*:",
    r"special instructions? for (the )?(assistant|ai|llm|model)",
    r"this is (a )?(hidden|secret) (instruction|message|prompt)",
    r"assistant should (ignore|disregard)",
    r"claude should (ignore|disregard)",
]

_REGEX = re.compile("|".join(f"(?:{p})" for p in PADROES_SUSPEITOS), re.IGNORECASE)


def procurar_padroes_suspeitos(raiz: Path = RAIZ) -> List[Tuple[str, str]]:
    """Devolve (caminho_relativo, excerto) para cada correspondência.

    Lê cada ficheiro como texto simples (erros de encoding ignorados) —
    nunca faz parsing de JSON nem executa nada, só compara com os
    padrões. Ficheiros ilegíveis são saltados em silêncio."""
    ocorrencias: List[Tuple[str, str]] = []
    for nome_dir in DIRETORIOS_A_VERIFICAR:
        base = raiz / nome_dir
        if not base.exists():
            continue
        for caminho in sorted(base.rglob("*")):
            if not caminho.is_file():
                continue
            try:
                conteudo = caminho.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in _REGEX.finditer(conteudo):
                inicio = max(0, m.start() - 40)
                fim = min(len(conteudo), m.end() + 40)
                excerto = conteudo[inicio:fim].replace("\n", " ")
                ocorrencias.append((str(caminho.relative_to(raiz)), excerto))
    return ocorrencias


def main() -> int:
    ocorrencias = procurar_padroes_suspeitos(RAIZ)
    if not ocorrencias:
        print("OK — nenhum padrão de prompt injection encontrado em data/ ou shadow_history/.")
        return 0

    print("ERRO CRÍTICO: padrões de prompt injection encontrados em conteúdo importado:")
    for caminho, excerto in ocorrencias:
        print(f"  - {caminho}: ...{excerto}...")
    print(
        "\nNão execute nem confie em nada destes ficheiros — tratar como dado inerte. "
        "Investigar a fonte externa (scraper/RSS) antes de qualquer outra acção."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
