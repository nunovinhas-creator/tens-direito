#!/usr/bin/env python3
"""
scripts/gerir_estado_fontes.py

Máquina de estados de fontes bloqueadas (Fase 2 do robustecimento do
Shadow Mode / higiene de Issues). Lê `data/bloqueios.json` (bloqueios
de hoje, escritos por `scraper_playwright.py`) e `data/estado_fontes.json`
(estado da corrida anterior, se existir) e calcula o novo estado por
fonte monitorizada: `{estado, dias_consecutivos_bloqueado, ultima_ok}`.

Puramente funcional na parte de decisão (`calcular_novo_estado`,
`fontes_para_issue`) — não cria, fecha nem comenta nenhuma Issue; isso
é feito pelo passo GitHub Actions seguinte no pipeline, que lê
`data/estado_fontes.json` já actualizado. Este módulo também não
importa `scraper_playwright` nem Playwright/BeautifulSoup — a lista de
fontes monitorizadas é a mesma lista usada no step "Detectar mudanças"
de `pipeline-diario.yml`, mantida aqui em sincronia deliberada (ver
`SLUGS_MONITORIZADOS`).

Regra: só se abre Issue `fonte-bloqueada` ao 3.º dia consecutivo de
bloqueio (`LIMIAR_DIAS_PARA_ISSUE`) — bloqueios de 1-2 dias a fontes
oficiais são frequentemente transitórios e ficam só registados aqui,
sem ruído no GitHub.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

LIMIAR_DIAS_PARA_ISSUE = 3

# Mesmas fontes do mapa `fontes` no step "Detectar mudanças" de
# pipeline-diario.yml — mantidas aqui à parte porque este módulo não
# importa scraper_playwright (evita puxar Playwright/BeautifulSoup só
# para calcular um estado).
SLUGS_MONITORIZADOS = (
    "seg_social_abono",
    "seg_social_rsi",
    "dge_ase",
    "dge_manuais",
    "mega_datas",
    "igefe_mega",
    "iefp_desemprego",
    "dre_psu",
    # Watchlist do cluster Habitação (Sessão 3, 2026-07-20) — mesma
    # máquina de estados de fontes bloqueadas do dre_psu.
    "dre_habitacao_paer",
    "dre_habitacao_garantia",
)


def calcular_novo_estado(
    estado_anterior: Dict[str, dict],
    slugs_bloqueados_hoje: List[str],
    todos_os_slugs: List[str],
    *,
    hoje: str,
) -> Dict[str, dict]:
    """Calcula o estado do dia para cada fonte monitorizada.

    Uma fonte que não aparece em `slugs_bloqueados_hoje` é tratada como
    recuperada/OK hoje — reinicia o contador de dias consecutivos e
    actualiza `ultima_ok`, mesmo que o estado anterior fosse BLOQUEADO.
    """
    estado_anterior = estado_anterior or {}
    bloqueados_hoje = set(slugs_bloqueados_hoje or [])
    novo_estado: Dict[str, dict] = {}

    for slug in todos_os_slugs:
        anterior = estado_anterior.get(slug) or {}
        ultima_ok = anterior.get("ultima_ok")

        if slug in bloqueados_hoje:
            novo_estado[slug] = {
                "estado": "BLOQUEADO",
                "dias_consecutivos_bloqueado": anterior.get("dias_consecutivos_bloqueado", 0) + 1,
                "ultima_ok": ultima_ok,
            }
        else:
            novo_estado[slug] = {
                "estado": "OK",
                "dias_consecutivos_bloqueado": 0,
                "ultima_ok": hoje,
            }

    return novo_estado


def fontes_para_issue(estado: Dict[str, dict], *, limiar: int = LIMIAR_DIAS_PARA_ISSUE) -> List[str]:
    """Slugs bloqueados com `dias_consecutivos_bloqueado >= limiar` hoje —
    candidatos a Issue (criada ao atingir o limiar, comentada nos dias
    seguintes enquanto o bloqueio persistir; dedup fica a cargo do passo
    que consome esta lista, por título já contém o slug)."""
    return sorted(
        slug
        for slug, info in (estado or {}).items()
        if info.get("estado") == "BLOQUEADO"
        and info.get("dias_consecutivos_bloqueado", 0) >= limiar
    )


def fontes_recuperadas(estado_anterior: Dict[str, dict], estado_novo: Dict[str, dict]) -> List[str]:
    """Slugs que estavam BLOQUEADO no estado anterior e passaram a OK
    nesta execução — candidatos a fecho automático da Issue
    correspondente (se existir)."""
    estado_anterior = estado_anterior or {}
    return sorted(
        slug
        for slug, novo in (estado_novo or {}).items()
        if (estado_anterior.get(slug) or {}).get("estado") == "BLOQUEADO"
        and novo.get("estado") == "OK"
    )


def carregar_estado(caminho: Path) -> Dict[str, dict]:
    if not caminho.exists():
        return {}
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        return conteudo if isinstance(conteudo, dict) else {}
    except Exception:
        return {}


def guardar_estado(caminho: Path, estado: Dict[str, dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
    )


def _slugs_bloqueados_hoje(bloqueios: list, hoje: str) -> List[str]:
    return sorted({
        b["slug"] for b in (bloqueios or [])
        if isinstance(b, dict) and isinstance(b.get("data"), str) and b["data"][:10] == hoje
    })


def main(*, raiz: Optional[Path] = None, hoje: Optional[str] = None) -> Dict[str, dict]:
    raiz = raiz or Path(__file__).resolve().parent.parent
    hoje = hoje or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    caminho_bloqueios = raiz / "data" / "bloqueios.json"
    caminho_estado = raiz / "data" / "estado_fontes.json"

    bloqueios = []
    if caminho_bloqueios.exists():
        try:
            bloqueios = json.loads(caminho_bloqueios.read_text(encoding="utf-8"))
        except Exception:
            bloqueios = []

    estado_anterior = carregar_estado(caminho_estado)
    slugs_bloqueados_hoje = _slugs_bloqueados_hoje(bloqueios, hoje)
    estado_novo = calcular_novo_estado(
        estado_anterior, slugs_bloqueados_hoje, list(SLUGS_MONITORIZADOS), hoje=hoje
    )
    guardar_estado(caminho_estado, estado_novo)

    para_issue = fontes_para_issue(estado_novo)
    recuperadas = fontes_recuperadas(estado_anterior, estado_novo)
    print(f"Estado de fontes actualizado ({hoje}): {len(para_issue)} para issue, {len(recuperadas)} recuperada(s)")
    for slug in para_issue:
        print(f"  - {slug}: {estado_novo[slug]['dias_consecutivos_bloqueado']} dia(s) consecutivos bloqueado")
    for slug in recuperadas:
        print(f"  - {slug}: recuperou hoje")

    return estado_novo


if __name__ == "__main__":
    main()
