"""
Verificador mensal do calendário de pagamentos (Fase 3 de
CALENDARIO-PAGAMENTOS-SPEC.md) — corrido por
.github/workflows/calendario-mensal.yml (dia 25 + retry 28 + dia 1 +
manual).

Contexto provado pelo diagnóstico de 2026-07-12 (4 rondas num runner
real — ver docs/FONTE-CALENDARIO.md): com a migração do portal da
Segurança Social, a notícia mensal pública das datas de pagamento
DEIXOU DE EXISTIR — o portal antigo redirecciona tudo para o gateway
SSD, a listagem /ptss/pssd/noticias não tem nenhuma notícia de datas
de pagamento, e o "Calendário" do portal novo exige login. Por isso o
fluxo é SEMIAUTOMÁTICO, exactamente o fallback que a spec previa:

  1. Se data/calendario_pagamentos.json JÁ tem o mês alvo (posto lá por
     uma sessão manual verificada) → estado `dados_ok`: o workflow corre
     a injecção idempotente + testes + commit confinado.
  2. Se não tem → este script SONDA as rotas oficiais conhecidas (a
     listagem de notícias da SPA, via Playwright) para detectar se a
     Segurança Social voltou a publicar o calendário publicamente; o
     resultado da sonda vai no corpo da Issue `calendario-manual`, com
     um prompt pronto a colar — estado `precisa_manual`. Nunca inventa
     datas, nunca escreve dados, nunca faz commit parcial.

Mês alvo: dia >= 20 → mês seguinte (fluxo do dia 25/28); dia < 20 →
mês corrente (fluxo do dia 1: virar a página quando o JSON já o tem).

Saídas (GITHUB_OUTPUT quando disponível, sempre no stdout):
  estado=dados_ok|precisa_manual
  mes_alvo=AAAA-MM
Relatório markdown (para o corpo da Issue) escrito em --relatorio.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import json  # noqa: E402

from atualizar_calendario import (  # noqa: E402
    DADOS,
    MESES_PT,
    _encontrar_mes,
    _mes_seguinte,
    carregar_dados,
    hoje_lisboa,
    validar_dados,
)
from scraper_calendario import URL as URL_PAGAMENTOS  # noqa: E402
from scraper_calendario import ScraperError, raspar_mes  # noqa: E402

BASE = "https://www.seg-social.pt"
LISTAGEM_NOTICIAS = f"{BASE}/ptss/pssd/noticias"
DIA_CORTE_MES_SEGUINTE = 20


def tentar_scraper_e_gravar(dados: dict, ano: int, mes: int) -> tuple[bool, list[str]]:
    """Tenta obter o mês da fonte pública oficial (/ptss/pssd/pagamentos)
    e, em caso de sucesso, grava-o em data/calendario_pagamentos.json.
    Devolve (sucesso, linhas de relatório). Nunca grava dados que não
    passem a validação — INVARIANTE: um erro nunca parece sucesso."""
    linhas = [f"### Scraper automático ({URL_PAGAMENTOS})"]
    try:
        mes_novo = raspar_mes(ano, mes)
    except ScraperError as e:
        linhas.append(f"- ❌ Scraper falhou: {e}")
        return False, linhas
    except Exception as e:  # rede/timeout/Playwright — nunca rebenta o workflow
        linhas.append(f"- ⚠️ Scraper indisponível ({type(e).__name__}): {e}")
        return False, linhas

    novos = {"meses": [m for m in dados.get("meses", [])
                       if not (m["ano"] == ano and m["mes"] == mes)] + [mes_novo]}
    fundido = dict(dados)
    fundido["meses"] = sorted(novos["meses"], key=lambda m: (m["ano"], m["mes"]))
    fundido["atualizado_em"] = hoje_lisboa().isoformat()
    fundido["fonte_url"] = URL_PAGAMENTOS

    problemas = validar_dados(fundido)
    if problemas:
        linhas.append("- ❌ Dados raspados falharam a validação (não gravados):")
        linhas += [f"  - {p}" for p in problemas]
        return False, linhas

    DADOS.write_text(
        json.dumps(fundido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    dias = ", ".join(str(p["dia"]) for p in mes_novo["pagamentos"])
    linhas.append(
        f"- ✅ {MESES_PT[mes]} de {ano} obtido automaticamente da fonte oficial "
        f"e gravado em `data/calendario_pagamentos.json` (dias: {dias})."
    )
    return True, linhas


def mes_alvo(hoje: dt.date, forcar_seguinte: bool = False) -> tuple[int, int]:
    if forcar_seguinte or hoje.day >= DIA_CORTE_MES_SEGUINTE:
        return _mes_seguinte(hoje.year, hoje.month)
    return (hoje.year, hoje.month)


def sondar_fonte_oficial(ano: int, mes: int) -> list[str]:
    """Sonda a listagem de notícias da SPA à procura de uma notícia de
    datas de pagamento. Devolve linhas de relatório — nunca dados."""
    linhas: list[str] = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ["- ⚠️ Playwright indisponível neste ambiente — sonda não corrida."]

    def _chromium_fallback():
        import glob
        bases = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH"),
                 "/opt/pw-browsers",
                 os.path.expanduser("~/.cache/ms-playwright")]
        for base in bases:
            if not base:
                continue
            c = sorted(glob.glob(os.path.join(base, "chromium-*",
                                              "chrome-linux*", "chrome")))
            if c:
                return c[-1]
        return None

    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception:
                exe = _chromium_fallback()
                if not exe:
                    raise
                browser = pw.chromium.launch(executable_path=exe)
            page = browser.new_context(
                locale="pt-PT", timezone_id="Europe/Lisbon"
            ).new_page()
            page.goto(LISTAGEM_NOTICIAS, wait_until="domcontentloaded",
                      timeout=45000)
            page.wait_for_function(
                "() => document.querySelectorAll(\"a[href*='/ptss/pssd/noticias/']\").length > 3",
                timeout=20000,
            )
            pares = page.evaluate(
                """() => Array.from(document.querySelectorAll("a[href*='/ptss/pssd/noticias/']"))
                    .map(a => [a.getAttribute('href'), a.innerText.trim().replace(/\\s+/g,' ').slice(0,120)])"""
            )
            browser.close()
    except Exception as e:
        return [f"- ⚠️ Sonda falhou com erro: {e}"]

    relevantes = [
        (h, t) for h, t in pares
        if re.search(r"datas? de pagamento|calend[áa]rio de pagamento", t, re.I)
    ]
    linhas.append(
        f"- Listagem `{LISTAGEM_NOTICIAS}`: {len(pares)} notícias visíveis."
    )
    if relevantes:
        linhas.append(
            "- 🔎 **Possível fonte oficial reaparecida** — notícias com "
            "'datas de pagamento' encontradas (validar o mês no CONTEÚDO, "
            "nunca no URL):"
        )
        for h, t in relevantes:
            linhas.append(f"  - `{h}` — {t}")
    else:
        linhas.append(
            "- Nenhuma notícia de datas de pagamento na listagem pública — "
            "mesmo estado do diagnóstico de 2026-07-12 (fonte pública "
            "inexistente desde a migração do portal). Usar triangulação de "
            "fontes que reproduzam o calendário oficial, como documentado."
        )
    return linhas


def prompt_sessao_manual(ano: int, mes: int) -> str:
    nome = f"{MESES_PT[mes]} de {ano}"
    return f"""```
Actualização mensal do calendário de pagamentos da Segurança Social —
mês alvo: {nome}. Ver CLAUDE.md secção "CALENDÁRIO DE PAGAMENTOS DA
SEGURANÇA SOCIAL" e docs/FONTE-CALENDARIO.md antes de tocar em nada.

1. Verifica se a Segurança Social já divulgou o calendário de {nome}:
   primeiro as rotas oficiais (relatório da sonda nesta Issue); sem
   fonte oficial pública acessível, triangula >=3 fontes independentes
   que reproduzam explicitamente o calendário oficial (mesmo padrão da
   sessão de 2026-07-12). Nunca aceitar datas que possam ser previsão
   por regra de dias fixos.
2. Acrescenta o mês a data/calendario_pagamentos.json (slugs da
   allow-list PRESTACOES em scripts/atualizar_calendario.py; actualiza
   "atualizado_em" e, se aplicável, "fonte_url").
3. Corre: python scripts/atualizar_calendario.py
   e depois: python -m pytest tests/test_calendario_frescura.py -q
4. Commit directo em main: "feat(calendario): calendário de {nome}".
5. Sem confirmação robusta das datas -> NÃO publicar nada: a página
   degrada sozinha para o estado "consultar fonte oficial" e este
   workflow volta a tentar/lembrar. Nunca inventar datas.
```"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--relatorio", type=Path, default=None,
                        help="ficheiro markdown para o corpo da Issue")
    parser.add_argument("--forcar-seguinte", action="store_true",
                        help="alvo é sempre o mês seguinte (testes/dispatch)")
    args = parser.parse_args(argv)

    hoje = hoje_lisboa()
    ano, mes = mes_alvo(hoje, args.forcar_seguinte)
    alvo_txt = f"{ano}-{mes:02d}"

    dados = carregar_dados()
    problemas = validar_dados(dados)
    tem_alvo = _encontrar_mes(dados, ano, mes) is not None and not problemas

    if problemas:
        print("AVISO: o JSON actual falha a validação:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)

    linhas = [
        f"## Estado do calendário — alvo {MESES_PT[mes]} de {ano}",
        "",
        f"- Corrida de {hoje.isoformat()} (`verificar_calendario_mensal.py`).",
        f"- `data/calendario_pagamentos.json` {'JÁ TEM' if tem_alvo else 'NÃO tem'} o mês alvo.",
    ]

    if tem_alvo:
        estado = "dados_ok"
    else:
        # 1.º: tentar a fonte pública oficial automaticamente (scraper).
        linhas.append("")
        sucesso, linhas_scraper = tentar_scraper_e_gravar(dados, ano, mes)
        linhas += linhas_scraper
        if sucesso:
            estado = "dados_ok"
        else:
            # 2.º: fallback manual — sonda + Issue com prompt pronto.
            estado = "precisa_manual"
            linhas.append("")
            linhas.append("### Sonda às rotas oficiais (fallback)")
            linhas += sondar_fonte_oficial(ano, mes)
            linhas.append("")
            linhas.append("### Prompt pronto para a sessão manual")
            linhas.append(prompt_sessao_manual(ano, mes))

    relatorio = "\n".join(linhas) + "\n"
    print(relatorio)
    if args.relatorio:
        args.relatorio.write_text(relatorio, encoding="utf-8")

    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a", encoding="utf-8") as f:
            f.write(f"estado={estado}\n")
            f.write(f"mes_alvo={alvo_txt}\n")
    print(f"estado={estado} mes_alvo={alvo_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
