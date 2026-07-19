#!/usr/bin/env python3
"""
FASE 1 (sessão de dados abertos, 2026-07-19) — Git scraping: historial
auditável dos dados extraídos das fontes oficiais.

Lê `data/scraped/<slug>_latest.json` (só existe quando o scraper
classificou a fonte como OK ou OK_VIA_ARQUIVO — nunca bloqueado, ver
`scraper_playwright._guardar_resultado`) e grava/actualiza
`dados/observacoes/<slug>.json` — um ficheiro por fonte, sobrescrito no
lugar. O HISTORIAL não vive num array a crescer dentro do próprio JSON:
vive no `git log -- dados/observacoes/<slug>.json` de cada ficheiro —
por isso este script só reescreve quando `sha256_conteudo` mudar face
ao já registado, para que cada commit represente uma mudança
substantiva real, nunca ruído diário.

Regra de ruído (porque isto não precisa de normalização própria):
`hash_conteudo` já é calculado por `scraper_playwright.py` só sobre
`conteudo_extraido` (título/parágrafos/itens de lista já limpos de
tags/scripts) — nunca sobre `data_acesso`, o URL final ou qualquer
outro campo dinâmico. O HTML bruto (com os seus timestamps/tokens
CSRF/etc.) nunca chega a este script — já foi descartado pelo scraper.
Por construção, o mesmo texto extraído produz sempre o mesmo hash, dia
após dia, mesmo que a página de origem mude elementos irrelevantes de
um pedido para o outro.

Um bloqueio nunca é gravado como se fosse sucesso: `_latest.json` só é
escrito pelo scraper quando o classificador confirma OK/OK_VIA_ARQUIVO
(nunca para BLOQUEADO — ver `scraper_playwright._tratar_nao_ok`, que só
chama `_guardar_resultado`/`_registar_bloqueio`, nunca ambos). Este
script confirma isso de novo a partir do campo `status` em vez de
assumir — se algum dia essa garantia arquitectural deixar de valer,
`estado` fica `DESCONHECIDO`, nunca `OK` por omissão, e
`valores_extraidos` fica `null` com `motivo` explícito.

    python scripts/registar_observacao.py             # todas as SLUGS_MONITORIZADOS
    python scripts/registar_observacao.py --slug=X    # só uma fonte (depuração)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from gerir_estado_fontes import SLUGS_MONITORIZADOS  # noqa: E402

SCRAPED_DIR = RAIZ / "data" / "scraped"
OBSERVACOES_DIR = RAIZ / "dados" / "observacoes"

_ESTADOS_SUCESSO = {"ok": "OK", "ok_via_arquivo": "OK"}


def _caminho_observacao(slug: str) -> Path:
    """Allow-list estrita, mesmo espírito de `escrever_ficheiro_seguro()`
    em `gerar_noticias.py`: este script só escreve um ficheiro por slug
    monitorizado, nunca um caminho arbitrário."""
    if slug not in SLUGS_MONITORIZADOS:
        raise ValueError(f"BLOQUEADO: slug '{slug}' não está em SLUGS_MONITORIZADOS.")
    return OBSERVACOES_DIR / f"{slug}.json"


def construir_observacao(slug: str, latest: dict) -> dict:
    status = latest.get("status", "")
    estado = _ESTADOS_SUCESSO.get(status, "DESCONHECIDO")
    conteudo = latest.get("conteudo_extraido")

    obs = {
        "fonte": slug,
        "fonte_url": latest.get("url") or latest.get("url_original", ""),
        "data_extracao": latest.get("data_acesso", ""),
        "sha256_conteudo": latest.get("hash_conteudo", ""),
        "estado": estado,
        "valores_extraidos": conteudo if (estado == "OK" and conteudo) else None,
    }
    if obs["valores_extraidos"] is None:
        obs["motivo"] = (
            f"estado={estado} status_bruto={status!r} — sem conteúdo fiável "
            "para registar (nunca gravado como sucesso)"
        )
    if latest.get("modo") == "arquivo":
        obs["modo"] = "arquivo"
        obs["data_snapshot"] = latest.get("data_snapshot")
        obs["url_snapshot"] = latest.get("url_snapshot")
    return obs


def registar(slug: str) -> str:
    """Devolve 'atualizado', 'sem_alteracao' ou 'sem_dados' — nunca lança
    excepção só porque uma fonte nova ainda não tem nenhum scrape
    bem-sucedido."""
    latest_path = SCRAPED_DIR / f"{slug}_latest.json"
    if not latest_path.exists():
        print(f"{slug}: sem data/scraped/{slug}_latest.json ainda — nada a registar.")
        return "sem_dados"

    try:
        latest = json.loads(latest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"{slug}: {latest_path.name} malformado ({exc}) — nada a registar.")
        return "sem_dados"

    nova_obs = construir_observacao(slug, latest)
    caminho = _caminho_observacao(slug)

    if caminho.exists():
        try:
            anterior = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            anterior = {}
        if (
            anterior.get("sha256_conteudo") == nova_obs["sha256_conteudo"]
            and anterior.get("estado") == nova_obs["estado"]
        ):
            print(f"{slug}: sha256/estado inalterados — sem novo commit de observação.")
            return "sem_alteracao"

    OBSERVACOES_DIR.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(nova_obs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{slug}: observação actualizada ({nova_obs['estado']}, sha256={nova_obs['sha256_conteudo'][:12]}…).")
    return "atualizado"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default=None, help="Só uma fonte (depuração)")
    args = parser.parse_args()

    slugs = [args.slug] if args.slug else list(SLUGS_MONITORIZADOS)
    resultados = {slug: registar(slug) for slug in slugs}

    atualizados = [s for s, r in resultados.items() if r == "atualizado"]
    print(f"\n{len(atualizados)}/{len(slugs)} observação(ões) actualizada(s): {atualizados}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
