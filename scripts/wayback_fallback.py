"""
scripts/wayback_fallback.py

Fallback Wayback Machine (modo degradado, honesto) — usado por
`scraper_playwright.py` só depois de 3 tentativas directas falharem a
uma fonte. Consulta a API pública `https://archive.org/wayback/available`;
se existir snapshot com `JANELA_DIAS_SNAPSHOT_VALIDO` dias ou menos, o
estado do dia passa a `OK_VIA_ARQUIVO` — usado só para deteção de
mudança (hash SHA-256), nunca como fonte de factos para conteúdo.

BLOQUEADO nunca é disfarçado de OK: `OK_VIA_ARQUIVO` é sempre um estado
à parte (nunca reescrito como "OK") e não conta como dia bloqueado para
a máquina de estados de fontes (`gerir_estado_fontes.py`) — mas também
nunca é tratado, silenciosamente, como se a fonte tivesse respondido
directamente.

Sem chamadas de rede próprias: `fetch_json` é sempre injectado por quem
chamar (torna este módulo testável sem rede e sem depender de
`requests` estar instalado só para correr os testes).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

WAYBACK_API = "https://archive.org/wayback/available"
JANELA_DIAS_SNAPSHOT_VALIDO = 7


@dataclass(frozen=True)
class ResultadoWayback:
    disponivel: bool
    timestamp: Optional[str] = None  # formato Wayback: AAAAMMDDhhmmss
    url_snapshot: Optional[str] = None
    dias_desde_snapshot: Optional[int] = None


def _parse_timestamp_wayback(ts: Any) -> Optional[datetime]:
    if not isinstance(ts, str):
        return None
    try:
        return datetime.strptime(ts, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def consultar_snapshot(
    url: str,
    *,
    fetch_json: Callable[[str], dict],
    agora: Optional[datetime] = None,
) -> ResultadoWayback:
    """Consulta a API pública do Wayback Machine para `url`. Nunca lança
    excepção — qualquer falha (rede, JSON malformado, snapshot ausente)
    devolve `disponivel=False`, tratado a jusante como "sem fallback"."""
    agora = agora or datetime.now(timezone.utc)
    try:
        dados = fetch_json(f"{WAYBACK_API}?url={url}") or {}
    except Exception:
        return ResultadoWayback(disponivel=False)

    if not isinstance(dados, dict):
        return ResultadoWayback(disponivel=False)

    snapshot = (dados.get("archived_snapshots") or {}).get("closest") or {}
    if not isinstance(snapshot, dict) or not snapshot.get("available"):
        return ResultadoWayback(disponivel=False)

    timestamp = snapshot.get("timestamp")
    data_snapshot = _parse_timestamp_wayback(timestamp)
    if data_snapshot is None:
        return ResultadoWayback(disponivel=False)

    dias = (agora - data_snapshot).days
    return ResultadoWayback(
        disponivel=True,
        timestamp=timestamp,
        url_snapshot=snapshot.get("url"),
        dias_desde_snapshot=dias,
    )


def snapshot_e_recente(
    resultado: ResultadoWayback, *, limite_dias: int = JANELA_DIAS_SNAPSHOT_VALIDO
) -> bool:
    return (
        resultado.disponivel
        and resultado.dias_desde_snapshot is not None
        and 0 <= resultado.dias_desde_snapshot <= limite_dias
    )


def decidir_estado_apos_bloqueio(
    url: str,
    *,
    fetch_json: Callable[[str], dict],
    agora: Optional[datetime] = None,
    limite_dias: int = JANELA_DIAS_SNAPSHOT_VALIDO,
) -> Dict[str, Any]:
    """Chamado só depois de as 3 tentativas directas falharem. Devolve
    `{"estado": "OK_VIA_ARQUIVO" | "BLOQUEADO", "snapshot": {...} | None}`.

    `estado` nunca é `"OK"` — este módulo só decide entre um modo
    degradado explícito e o bloqueio continuar, nunca finge que a fonte
    respondeu normalmente.
    """
    resultado = consultar_snapshot(url, fetch_json=fetch_json, agora=agora)
    if snapshot_e_recente(resultado, limite_dias=limite_dias):
        return {
            "estado": "OK_VIA_ARQUIVO",
            "snapshot": {
                "timestamp": resultado.timestamp,
                "url": resultado.url_snapshot,
                "dias_desde_snapshot": resultado.dias_desde_snapshot,
            },
        }
    return {"estado": "BLOQUEADO", "snapshot": None}
