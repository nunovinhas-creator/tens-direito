#!/usr/bin/env python3
"""
scripts/verificar_urls_como_pedir.py

Canário de URLs oficiais do cluster "Como Pedir" (SPEC-CLUSTER-COMO-PEDIR.md,
secção 6.1). Para cada guia do cluster, confirma que os URLs oficiais citados
(`data/urls_como_pedir.json` — nunca hardcoded aqui) continuam a responder
200. Mesma disciplina de `scripts/smoke_producao.sh`: retries com espera
entre tentativas, e falha (`exit 1`) sem mascarar nada — um 404/erro de rede
persistente é sempre reportado, nunca engolido em silêncio (ver CLAUDE.md,
"INVARIANTE — NENHUM ESTADO DE ERRO PODE PARECER SUCESSO").

`verificar_url()` é pura — recebe `fetch` injectado — para ser testável sem
rede real (mesmo padrão de `scripts/wayback_fallback.py`). Só `main()` usa
`requests` a sério, e só esse caminho precisa de rede (por isso este script
corre à parte da suite pytest determinística — ver o step "Canário de URLs
oficiais — Como Pedir" em `.github/workflows/integridade.yml`).

    python scripts/verificar_urls_como_pedir.py
"""
from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_URLS = RAIZ / "data" / "urls_como_pedir.json"

TENTATIVAS = 3
ESPERA_S = 5
TIMEOUT_S = 15
USER_AGENT = "TensDireito-URLCanary/1.0"


@dataclass(frozen=True)
class ResultadoUrl:
    url: str
    ok: bool
    status: Optional[int]
    motivo: str


def carregar_config(caminho: Path = CONFIG_URLS) -> Dict[str, List[dict]]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def verificar_url(
    url: str,
    fetch: Callable[[str], "FetchResposta"],
    *,
    tentativas: int = TENTATIVAS,
    espera_s: float = ESPERA_S,
    dormir: Callable[[float], None] = time.sleep,
) -> ResultadoUrl:
    """Faz até `tentativas` pedidos a `url`, com espera entre falhas.
    `fetch` é injectado — nunca chama rede directamente, para ser testável
    sem rede real."""
    ultimo_erro = "sem tentativas"
    ultimo_status: Optional[int] = None
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = fetch(url)
        except Exception as exc:  # noqa: BLE001 — qualquer falha de rede conta
            ultimo_erro = f"erro de rede: {exc}"
            ultimo_status = None
        else:
            ultimo_status = resposta.status_code
            if 200 <= resposta.status_code < 300:
                return ResultadoUrl(url, True, resposta.status_code, "OK")
            ultimo_erro = f"HTTP {resposta.status_code}"
        if tentativa < tentativas:
            dormir(espera_s)
    return ResultadoUrl(url, False, ultimo_status, f"falhou {tentativas}/{tentativas} tentativas — {ultimo_erro}")


class FetchResposta:
    def __init__(self, status_code: int):
        self.status_code = status_code


def _fetch_real(url: str) -> FetchResposta:
    import requests

    resp = requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S, allow_redirects=True)
    if resp.status_code >= 400:
        # Alguns servidores (incluindo seg-social.pt) não respondem bem a
        # HEAD — confirma com GET antes de desistir, nunca falha só por HEAD.
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S, allow_redirects=True)
    return FetchResposta(resp.status_code)


def main() -> int:
    config = carregar_config()
    falhas: List[ResultadoUrl] = []
    urls_ja_testados: Dict[str, ResultadoUrl] = {}

    print("=== Canário de URLs oficiais — Como Pedir ===")
    for guia, entradas in config.items():
        print(f"\n{guia}:")
        for entrada in entradas:
            url = entrada["url"]
            if url in urls_ja_testados:
                resultado = urls_ja_testados[url]
            else:
                resultado = verificar_url(url, _fetch_real)
                urls_ja_testados[url] = resultado
            estado = "OK" if resultado.ok else "FALHOU"
            print(f"  [{estado}] {url} ({entrada.get('descricao', '')}) — {resultado.motivo}")
            if not resultado.ok:
                falhas.append(resultado)

    print(f"\n=== Resultado: {len(urls_ja_testados)} URL(s) únicos verificados, {len(falhas)} falha(s) ===")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
