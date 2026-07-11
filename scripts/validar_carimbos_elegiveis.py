#!/usr/bin/env python3
"""
Validação manual das simulações de "carimbos elegíveis" do Shadow Mode.

É o passo humano do critério de activação registado em ROADMAP.md/CLAUDE.md
("REVALIDAÇÃO DE CARIMBO"): ≥14 relatórios shadow consecutivos com
simulações CORRECTAS (zero falsos elegíveis) antes de alguma vez ligar
`REVALIDACAO_CARIMBO_HABILITADA`. Os relatórios provam que a simulação
corre; este script prova que ela está certa — corrido numa sessão manual,
nunca no pipeline. **Só leitura — nunca escreve nada.**

O que verifica, para cada página elegível de hoje:
1. A lista recalculada com a função REAL (`calcular_carimbos_elegiveis`)
   bate certo com a secção "Carimbos elegíveis" do relatório de hoje.
2. Todas as fontes mapeadas estão `OK` em `data/estado_fontes.json`.
3. hash do scrape de hoje == hash de ontem, para cada fonte.
4. O conteúdo extraído de hoje é real (≥ MIN_CHARS_CONTEUDO chars) e o
   status é `ok` — nunca `ok_via_arquivo` (Wayback nunca dá elegibilidade).
5. (Zona cega documentada) A fonte mudou de hash em algum dia DESDE a data
   do carimbo da página? Mudanças com URL diferente entre os dois scrapes
   são classificadas como artefacto do nosso próprio scraper (correcção de
   fetch — caso real: seg-social 03/07, dre_psu 07/07); com a MESMA URL
   ficam como aviso ⚠️ para juízo humano — nunca falham o script sozinhas,
   porque a simulação usa, por desenho, só a janela de 24h.

Exit 0 = simulação de hoje validada (avisos possíveis, listados).
Exit 1 = problema real: falso elegível hoje, scrape em falta, ou
divergência entre o recalculado e o relatório.

Uso:
    python scripts/validar_carimbos_elegiveis.py            # hoje/ontem reais
    python scripts/validar_carimbos_elegiveis.py --hoje 2026-07-11
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

RAIZ = Path(__file__).parent.parent

MIN_CHARS_CONTEUDO = 200

_RE_RELATORIO = re.compile(r"página\(s\) seriam elegíveis hoje: (.+)$", re.M)
_RE_NENHUMA = re.compile(r"Nenhuma página elegível hoje")


def _ler_json(caminho: Path) -> Optional[dict]:
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def _scrape(raiz: Path, slug: str, dia: str) -> Optional[dict]:
    return _ler_json(raiz / "data" / "scraped" / f"{slug}_{dia}.json")


def historico_hashes(raiz: Path, slug: str) -> List[tuple]:
    """[(data, hash, url)] por ordem cronológica, só scrapes com hash."""
    registos = []
    for f in sorted((raiz / "data" / "scraped").glob(f"{slug}_2???-??-??.json")):
        d = _ler_json(f)
        if d and d.get("hash_conteudo"):
            data_scrape = f.stem.rsplit("_", 1)[1]
            registos.append((data_scrape, d["hash_conteudo"], d.get("url", "")))
    return registos


def elegiveis_do_relatorio(raiz: Path, hoje: str) -> Optional[List[str]]:
    """Lista da secção 'Carimbos elegíveis' do relatório de hoje, ou None
    se o relatório (ou a secção) não existir."""
    relatorio = raiz / "shadow_history" / f"shadow_report_{hoje}.md"
    if not relatorio.exists():
        return None
    texto = relatorio.read_text(encoding="utf-8")
    if _RE_NENHUMA.search(texto):
        return []
    m = _RE_RELATORIO.search(texto)
    if not m:
        return None
    return sorted(re.findall(r"`([^`]+)`", m.group(1)))


@dataclass
class ResultadoPagina:
    pagina: str
    fontes: List[str]
    problemas: List[str] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    carimbo: Optional[str] = None


def verificar_pagina(raiz: Path, pagina: str, fontes: List[str],
                     estado_fontes: dict, hoje: str, ontem: str) -> ResultadoPagina:
    r = ResultadoPagina(pagina=pagina, fontes=fontes)

    caminho_pagina = raiz / pagina
    if caminho_pagina.exists():
        try:
            sys.path.insert(0, str(raiz / "scripts"))
            from sincronizar_clusters import extrair_verificado_em
            carimbo = extrair_verificado_em(caminho_pagina)
            r.carimbo = carimbo.isoformat() if carimbo else None
        except Exception:
            r.carimbo = None
    else:
        r.problemas.append("ficheiro da página não existe")

    for f in fontes:
        ef = estado_fontes.get(f)
        if not ef or ef.get("estado") != "OK":
            r.problemas.append(f"{f}: estado {'ausente' if not ef else ef.get('estado')} (esperava OK)")

        s_hoje, s_ontem = _scrape(raiz, f, hoje), _scrape(raiz, f, ontem)
        if not s_hoje or not s_ontem:
            r.problemas.append(f"{f}: scrape de {'hoje' if not s_hoje else 'ontem'} em falta")
            continue
        if s_hoje["hash_conteudo"] != s_ontem["hash_conteudo"]:
            r.problemas.append(f"{f}: hash de hoje ≠ ontem — página NÃO devia ser elegível")
        if s_hoje.get("status") != "ok":
            r.problemas.append(f"{f}: status '{s_hoje.get('status')}' (esperava 'ok' — nunca ok_via_arquivo)")
        chars = len(json.dumps(s_hoje.get("conteudo_extraido") or {}, ensure_ascii=False))
        if chars < MIN_CHARS_CONTEUDO:
            r.problemas.append(f"{f}: conteúdo suspeito ({chars} chars < {MIN_CHARS_CONTEUDO})")

        # Zona cega documentada: mudanças de hash desde o carimbo da página.
        if r.carimbo:
            regs = [x for x in historico_hashes(raiz, f) if x[0] >= r.carimbo]
            for i in range(1, len(regs)):
                if regs[i][1] != regs[i - 1][1]:
                    if regs[i][2] != regs[i - 1][2]:
                        r.avisos.append(
                            f"{f}: hash mudou {regs[i-1][0]}→{regs[i][0]} mas a URL também mudou — "
                            "artefacto de correcção do nosso scraper, não da fonte"
                        )
                    else:
                        r.avisos.append(
                            f"⚠️ {f}: hash mudou {regs[i-1][0]}→{regs[i][0]} com a MESMA URL — "
                            "possível mudança real da fonte DEPOIS do carimbo; confirmar manualmente"
                        )
    return r


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hoje", default=date.today().isoformat(),
                        help="data a validar (AAAA-MM-DD); por omissão, hoje")
    args = parser.parse_args()
    hoje = args.hoje
    ontem = (date.fromisoformat(hoje) - timedelta(days=1)).isoformat()

    sys.path.insert(0, str(RAIZ / "scripts"))
    from run_shadow_daily import calcular_carimbos_elegiveis

    elegiveis = sorted(calcular_carimbos_elegiveis(RAIZ, hoje=hoje, ontem=ontem))
    print(f"Elegíveis recalculados para {hoje}: {len(elegiveis)}")

    problemas_globais: List[str] = []

    do_relatorio = elegiveis_do_relatorio(RAIZ, hoje)
    if do_relatorio is None:
        print(f"(sem relatório shadow de {hoje} com a secção — comparação saltada)")
    elif do_relatorio != elegiveis:
        problemas_globais.append(
            f"DIVERGÊNCIA relatório vs recalculado: relatório={do_relatorio} recalculado={elegiveis}"
        )
    else:
        print("Relatório de hoje bate certo com o recalculado ✓")

    estado = _ler_json(RAIZ / "data" / "estado_fontes.json") or {}
    mapa = _ler_json(RAIZ / "data" / "pagina_fonte.json") or {}

    total_avisos = 0
    print()
    for pagina in elegiveis:
        r = verificar_pagina(RAIZ, pagina, mapa.get(pagina, []), estado, hoje, ontem)
        simbolo = "✗" if r.problemas else "✓"
        print(f"{simbolo} {pagina} (carimbo {r.carimbo or '?'}, fontes: {', '.join(r.fontes) or '—'})")
        for p in r.problemas:
            print(f"    PROBLEMA: {p}")
            problemas_globais.append(f"{pagina}: {p}")
        for a in r.avisos:
            print(f"    aviso: {a}")
        total_avisos += len(r.avisos)

    print()
    if problemas_globais:
        print(f"RESULTADO: {len(problemas_globais)} problema(s) — a simulação de {hoje} NÃO conta como validada.")
        return 1
    print(f"RESULTADO: simulação de {hoje} validada — zero falsos elegíveis ({total_avisos} aviso(s) de juízo humano).")
    print("Regista este dia na contagem de ≥14 simulações correctas (ROADMAP.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
