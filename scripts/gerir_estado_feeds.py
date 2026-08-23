#!/usr/bin/env python3
"""
scripts/gerir_estado_feeds.py

Máquina de estados de saúde dos feeds de notícias (Fase 3 do
robustecimento de 2026-07-04, mesmo padrão de `gerir_estado_fontes.py`
para fontes bloqueadas do scraper). Lê `data/feeds_saude_hoje.json`
(escrito por `gerar_noticias.py` a cada corrida) e
`data/estado_feeds.json` (estado da corrida anterior, se existir) e
calcula o novo estado por feed: `{estado, dias_consecutivos_morto,
ultima_ok}`.

Puramente funcional na parte de decisão (`calcular_novo_estado`,
`feeds_para_issue`, `feeds_recuperados`) — não cria, fecha nem comenta
nenhuma Issue; isso é feito pelo passo GitHub Actions seguinte no
pipeline, que lê `data/estado_feeds.json` já actualizado.

Regra: só se abre Issue `feed-morto` ao 3.º dia consecutivo sem itens
(`LIMIAR_DIAS_PARA_ISSUE`) — um feed pode falhar transitoriamente 1-2
dias sem que isso indique um problema real (ex.: falha pontual de rede
do lado do Google News).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

LIMIAR_DIAS_PARA_ISSUE = 3


def calcular_novo_estado(
    estado_anterior: Dict[str, dict],
    feeds_mortos_hoje: List[str],
    todos_os_feeds: List[str],
    *,
    hoje: str,
) -> Dict[str, dict]:
    """Calcula o estado do dia para cada feed monitorizado.

    Um feed que não aparece em `feeds_mortos_hoje` é tratado como
    recuperado/OK hoje — reinicia o contador de dias consecutivos e
    actualiza `ultima_ok`, mesmo que o estado anterior fosse MORTO.
    """
    estado_anterior = estado_anterior or {}
    mortos_hoje = set(feeds_mortos_hoje or [])
    novo_estado: Dict[str, dict] = {}

    for nome in todos_os_feeds:
        anterior = estado_anterior.get(nome) or {}
        ultima_ok = anterior.get("ultima_ok")

        if nome in mortos_hoje:
            novo_estado[nome] = {
                "estado": "MORTO",
                "dias_consecutivos_morto": anterior.get("dias_consecutivos_morto", 0) + 1,
                "ultima_ok": ultima_ok,
            }
        else:
            novo_estado[nome] = {
                "estado": "OK",
                "dias_consecutivos_morto": 0,
                "ultima_ok": hoje,
            }

    return novo_estado


def feeds_para_issue(estado: Dict[str, dict], *, limiar: int = LIMIAR_DIAS_PARA_ISSUE) -> List[str]:
    """Nomes de feeds mortos com `dias_consecutivos_morto >= limiar` hoje —
    candidatos a Issue (criada ao atingir o limiar, comentada nos dias
    seguintes enquanto a morte persistir)."""
    return sorted(
        nome
        for nome, info in (estado or {}).items()
        if info.get("estado") == "MORTO"
        and info.get("dias_consecutivos_morto", 0) >= limiar
    )


def feeds_recuperados(estado_anterior: Dict[str, dict], estado_novo: Dict[str, dict]) -> List[str]:
    """Nomes de feeds que estavam MORTO no estado anterior e passaram a OK
    nesta execução — candidatos a fecho automático da Issue
    correspondente (se existir)."""
    estado_anterior = estado_anterior or {}
    return sorted(
        nome
        for nome, novo in (estado_novo or {}).items()
        if (estado_anterior.get(nome) or {}).get("estado") == "MORTO"
        and novo.get("estado") == "OK"
    )


def carregar_estado(caminho: Path) -> Dict[str, dict]:
    if not caminho.exists():
        return {}
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        return conteudo if isinstance(conteudo, dict) else {}
    except json.JSONDecodeError as exc:
        # Nunca em silêncio: cair para {} aqui reinicia a contagem de dias
        # consecutivos morto de TODOS os feeds -- se acontecer sem aviso
        # nenhum, um feed já a meio da contagem para Issue nunca a atinge.
        print(f"⚠ {caminho.name} malformado ({exc}) — estado dos feeds reiniciado a partir de zero.")
        return {}


def guardar_estado(caminho: Path, estado: Dict[str, dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _feeds_mortos_hoje(saude_hoje: list, hoje: str) -> List[str]:
    return sorted({
        s["nome"] for s in (saude_hoje or [])
        if isinstance(s, dict) and s.get("estado") == "MORTO" and isinstance(s.get("data"), str) and s["data"][:10] == hoje
    })


def _todos_os_feeds(saude_hoje: list) -> List[str]:
    return sorted({s["nome"] for s in (saude_hoje or []) if isinstance(s, dict) and "nome" in s})


def main(*, raiz: Optional[Path] = None, hoje: Optional[str] = None) -> Dict[str, dict]:
    raiz = raiz or Path(__file__).resolve().parent.parent
    hoje = hoje or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    caminho_saude_hoje = raiz / "data" / "feeds_saude_hoje.json"
    caminho_estado = raiz / "data" / "estado_feeds.json"

    saude_hoje = []
    if caminho_saude_hoje.exists():
        try:
            saude_hoje = json.loads(caminho_saude_hoje.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"⚠ {caminho_saude_hoje.name} malformado ({exc}) — tratado como sem dados de saúde hoje.")
            saude_hoje = []

    todos_os_feeds = _todos_os_feeds(saude_hoje)
    if not todos_os_feeds:
        # Sem dados de saúde hoje (ex.: gerar_noticias.py falhou antes de
        # escrever) — mantém o estado anterior intacto, nunca inventa
        # "morto" nem "OK" sem dados reais desta corrida.
        print("Sem data/feeds_saude_hoje.json (ou vazio) — estado dos feeds não alterado.")
        return carregar_estado(caminho_estado)

    estado_anterior = carregar_estado(caminho_estado)
    mortos_hoje = _feeds_mortos_hoje(saude_hoje, hoje)
    estado_novo = calcular_novo_estado(estado_anterior, mortos_hoje, todos_os_feeds, hoje=hoje)
    guardar_estado(caminho_estado, estado_novo)

    para_issue = feeds_para_issue(estado_novo)
    recuperados = feeds_recuperados(estado_anterior, estado_novo)
    print(f"Estado de feeds actualizado ({hoje}): {len(para_issue)} para issue, {len(recuperados)} recuperado(s)")
    for nome in para_issue:
        print(f"  - {nome}: {estado_novo[nome]['dias_consecutivos_morto']} dia(s) consecutivos morto")
    for nome in recuperados:
        print(f"  - {nome}: recuperou hoje")

    return estado_novo


if __name__ == "__main__":
    main()
