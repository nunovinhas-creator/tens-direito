#!/usr/bin/env python3
"""
scripts/verificar_urls_como_pedir.py

Canário de URLs oficiais do cluster "Como Pedir" (SPEC-CLUSTER-COMO-PEDIR.md,
secção 6.1). Para cada guia do cluster, confirma que os URLs oficiais citados
(`data/urls_como_pedir.json` — nunca hardcoded aqui) continuam a responder
2xx. Falha (`exit 1`) sem mascarar nada — um erro persistente é sempre
reportado, nunca engolido em silêncio (ver CLAUDE.md, "INVARIANTE — NENHUM
ESTADO DE ERRO PODE PARECER SUCESSO").

Dois tipos de falha (ver `_e_definitiva`):
- definitiva (404, 410, domínio inexistente) — falha logo, sem retry: o
  endereço deixou de existir, esperar não muda nada;
- transitória (403, 405, 429, 5xx, timeouts, erros de ligação) — até
  `len(ESPERAS_S) + 1` tentativas, com esperas crescentes. Casos reais que
  motivaram isto (integridade.yml, set. 2026): HTTP 405 intermitente em
  www.sns24.gov.pt, mesmo no GET de recurso, e connect timeouts pontuais em
  autenticacao.gov.pt e registocriminal.justica.gov.pt.

Cada pedido regista o status do HEAD, o do GET de recurso (só feito quando
o HEAD dá ≥ 400) e o URL final, para o próximo caso ser diagnosticável.

`verificar_url()` é pura — recebe `fetch` injectado — para ser testável sem
rede real. Só `main()` usa `requests`, e corre só no workflow
`.github/workflows/canario-urls.yml`.

    python scripts/verificar_urls_como_pedir.py [--relatorio caminho.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
CONFIG_URLS = RAIZ / "data" / "urls_como_pedir.json"

# Esperas entre tentativas (segundos): 4 tentativas no total.
ESPERAS_S = (15, 45, 90)
TIMEOUT_S = 15
USER_AGENT = "TensDireito-URLCanary/1.0"
# O GET de recurso apresenta-se como um navegador: o 405 intermitente da
# sns24 persistia no GET com o User-Agent do canário.
CABECALHOS_NAVEGADOR = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-PT,pt;q=0.9",
}
STATUS_DEFINITIVOS = frozenset({404, 410})
ASSINATURAS_DNS = ("NameResolutionError", "Name or service not known", "nodename nor servname")


@dataclass(frozen=True)
class FetchResposta:
    status_code: int
    status_head: Optional[int] = None
    status_get: Optional[int] = None
    url_final: Optional[str] = None


@dataclass(frozen=True)
class ResultadoUrl:
    url: str
    ok: bool
    status: Optional[int]
    motivo: str
    status_head: Optional[int] = None
    status_get: Optional[int] = None
    url_final: Optional[str] = None
    tentativas: int = 0


def carregar_config(caminho: Path = CONFIG_URLS) -> Dict[str, List[dict]]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _e_definitiva(status: Optional[int], erro: Optional[str]) -> bool:
    if status is not None:
        return status in STATUS_DEFINITIVOS
    return bool(erro) and any(a in erro for a in ASSINATURAS_DNS)


def verificar_url(
    url: str,
    fetch: Callable[[str], FetchResposta],
    *,
    esperas_s: tuple = ESPERAS_S,
    dormir: Callable[[float], None] = time.sleep,
) -> ResultadoUrl:
    """Até `len(esperas_s) + 1` tentativas; uma falha definitiva pára logo.
    `fetch` é injectado — nunca chama rede directamente."""
    total = len(esperas_s) + 1
    resposta: Optional[FetchResposta] = None
    erro: Optional[str] = None
    for tentativa in range(1, total + 1):
        resposta, erro = None, None
        try:
            resposta = fetch(url)
        except Exception as exc:  # noqa: BLE001 — qualquer falha de rede conta
            erro = f"erro de rede: {exc}"
        status = resposta.status_code if resposta else None
        if status is not None and 200 <= status < 300:
            return ResultadoUrl(url, True, status, "OK", resposta.status_head,
                                resposta.status_get, resposta.url_final, tentativa)
        motivo = erro or f"HTTP {status}"
        if _e_definitiva(status, erro):
            return ResultadoUrl(url, False, status, f"falha definitiva à tentativa {tentativa} — {motivo}",
                                resposta and resposta.status_head, resposta and resposta.status_get,
                                resposta and resposta.url_final, tentativa)
        if tentativa < total:
            dormir(esperas_s[tentativa - 1])
    return ResultadoUrl(url, False, status, f"falhou {total}/{total} tentativas — {motivo}",
                        resposta and resposta.status_head, resposta and resposta.status_get,
                        resposta and resposta.url_final, total)


def _fetch_real(url: str) -> FetchResposta:
    import requests

    head = requests.head(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S, allow_redirects=True)
    if head.status_code < 400:
        return FetchResposta(head.status_code, head.status_code, None, head.url)
    # Alguns servidores não respondem bem a HEAD — confirma com GET antes de
    # desistir, nunca falha só por HEAD.
    get = requests.get(url, headers=CABECALHOS_NAVEGADOR, timeout=TIMEOUT_S, allow_redirects=True)
    return FetchResposta(get.status_code, head.status_code, get.status_code, get.url)


def _fmt(status: Optional[int]) -> str:
    return "—" if status is None else str(status)


def corpo_da_issue(resultados: List[dict], data_utc: str, url_run: str) -> str:
    """Corpo da issue única `canario-urls`, com os status HEAD/GET de cada URL."""
    falhas = [r for r in resultados if not r["ok"]]
    linhas = [
        "@nunovinhas-creator — o canário de URLs oficiais falhou.",
        "",
        f"Corrida: {url_run} ({data_utc} UTC). Esta issue é actualizada a cada "
        "corrida com falhas e fecha-se sozinha na primeira corrida verde.",
        "",
        f"**{len(falhas)} URL(s) a falhar**, de {len(resultados)} verificados:",
        "",
        "| URL | HEAD | GET | URL final | Tentativas | Motivo |",
        "|---|---|---|---|---|---|",
    ]
    for r in sorted(resultados, key=lambda r: (r["ok"], r["url"])):
        estado = "✅" if r["ok"] else "❌"
        linhas.append(
            f"| {estado} {r['url']} | {_fmt(r['status_head'])} | {_fmt(r['status_get'])} | "
            f"{r['url_final'] or '—'} | {r['tentativas']} | {r['motivo'].replace('|', '/')} |"
        )
    linhas += [
        "",
        "GET só é feito quando o HEAD dá ≥ 400. 404/410 e domínio inexistente "
        "falham à primeira; o resto tem 4 tentativas, com esperas de 15, 45 e 90 s.",
    ]
    return "\n".join(linhas)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Canário de URLs oficiais — Como Pedir")
    parser.add_argument("--relatorio", type=Path, help="grava o resultado em JSON (usado pelo workflow)")
    args = parser.parse_args(argv)

    config = carregar_config()
    resultados: Dict[str, ResultadoUrl] = {}

    print("=== Canário de URLs oficiais — Como Pedir ===")
    for guia, entradas in config.items():
        print(f"\n{guia}:")
        for entrada in entradas:
            url = entrada["url"]
            if url not in resultados:
                resultados[url] = verificar_url(url, _fetch_real)
            r = resultados[url]
            estado = "OK" if r.ok else "FALHOU"
            print(f"  [{estado}] {url} ({entrada.get('descricao', '')}) — HEAD={_fmt(r.status_head)} "
                  f"GET={_fmt(r.status_get)} final={r.url_final or '—'} — {r.motivo}")

    falhas = [r for r in resultados.values() if not r.ok]
    print(f"\n=== Resultado: {len(resultados)} URL(s) únicos verificados, {len(falhas)} falha(s) ===")
    if args.relatorio:
        dicts = [asdict(r) for r in resultados.values()]
        url_run = "{}/{}/actions/runs/{}".format(
            os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
            os.environ.get("GITHUB_REPOSITORY", "?"), os.environ.get("GITHUB_RUN_ID", "?"))
        data_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        relatorio = {
            "falhas": sorted(r.url for r in falhas),
            "corpo": corpo_da_issue(dicts, data_utc, url_run) if falhas else "",
            "resultados": dicts,
        }
        args.relatorio.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
