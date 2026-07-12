"""
Diagnóstico TEMPORÁRIO — verificar se /ptss/pssd/pagamentos é uma fonte
pública real do calendário (pista do Nuno, 2026-07-12), ao contrário de
/pagamentos2 e do "Calendário" de valores-a-receber, que redireccionam
para o gateway de login.

Testa o URL por 3 vias e despeja tudo o que for preciso para decidir se
dá para scraping automático (tabela de dias + prestações por mês, com
separadores por mês):
  A. requests simples — vê se redirecciona para o gateway SSD;
  B. Playwright (perfil seg-social: locale/timezone PT, SEM headers
     custom) — despeja o texto, tabelas, e procura separadores de mês
     (julho/agosto/…) e dias de pagamento;
  C. se houver separadores/botões de mês, tenta clicar no mês seguinte
     e volta a despejar.

Só lê e imprime — nunca escreve ficheiros do repositório. Apagar este
script e o workflow no fim.
"""
from __future__ import annotations

import re
import sys

import requests
from playwright.sync_api import sync_playwright

BASE = "https://www.seg-social.pt"
URL = f"{BASE}/ptss/pssd/pagamentos"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
         "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
}


def via_requests() -> None:
    print(f"\n{'='*78}\n[A · requests] {URL}")
    try:
        r = requests.get(URL, headers=HEADERS, timeout=30, allow_redirects=True)
        print(f"  status={r.status_code} final_url={r.url} bytes={len(r.text)}")
        print(f"  redirecciona p/ gateway SSD: {'/ptss/pssd/home' in r.url}")
    except Exception as e:
        print(f"  ERRO: {e}")


def _dump(page, etiqueta: str) -> None:
    texto = re.sub(r"\n{3,}", "\n\n", page.evaluate("document.body ? document.body.innerText : ''").strip())
    print(f"  [{etiqueta}] url={page.url}")
    print(f"  [{etiqueta}] title={page.title()!r} chars={len(texto)}")
    n_tab = page.evaluate("document.querySelectorAll('table').length")
    print(f"  [{etiqueta}] tabelas no DOM: {n_tab}")
    # separadores/botões de mês
    meses_vis = [m for m in MESES if re.search(rf"\b{m}\b", texto, re.I)]
    print(f"  [{etiqueta}] meses mencionados: {meses_vis}")
    # elementos clicáveis com nome de mês (tabs/botões/links)
    tabs = page.evaluate(
        """(meses) => Array.from(document.querySelectorAll('button, a, [role=tab], li'))
            .map(e => (e.innerText||'').trim().replace(/\\s+/g,' '))
            .filter(t => t && meses.some(m => new RegExp('\\\\b'+m+'\\\\b','i').test(t)) && t.length < 40)""",
        MESES,
    )
    print(f"  [{etiqueta}] candidatos a separador de mês: {sorted(set(tabs))[:15]}")
    # dias de pagamento (linhas com 'dia N' ou padrões de data)
    linhas_dia = re.findall(r"[^\n]*\b([0-2]?\d|3[01])\b[^\n]*(pens|abono|desemprego|rsi|renda|subs|complemento)[^\n]*", texto, re.I)
    print(f"  [{etiqueta}] linhas dia+prestação (amostra): {[' '.join(x) for x in linhas_dia[:6]]}")
    print(f"  [{etiqueta}] --- texto (primeiros 5000) ---")
    print(texto[:5000])
    print(f"  [{etiqueta}] --- fim ---")


def via_playwright() -> None:
    print(f"\n{'='*78}\n[B · playwright]")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(locale="pt-PT", timezone_id="Europe/Lisbon")
        page = ctx.new_page()
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=45000)
            # esperar por algum sinal de conteúdo real (mês ou tabela)
            try:
                page.wait_for_function(
                    "() => document.body && (document.querySelector('table') || /julho|agosto|pagamento/i.test(document.body.innerText))",
                    timeout=20000,
                )
            except Exception:
                print("  ⚠️ nenhum sinal de conteúdo (tabela/mês/pagamento) em 20s")
            _dump(page, "inicial")

            # C. tentar clicar num separador de mês seguinte, se existir
            for alvo in ("agosto", "setembro"):
                try:
                    loc = page.get_by_text(re.compile(rf"\b{alvo}\b", re.I)).first
                    if loc.count() and loc.is_visible():
                        loc.click(timeout=5000)
                        page.wait_for_timeout(1500)
                        _dump(page, f"após clicar '{alvo}'")
                        break
                except Exception as e:
                    print(f"  (clique em '{alvo}' falhou: {e})")
        except Exception as e:
            print(f"  ERRO: {e}")
        finally:
            b.close()


def main() -> int:
    via_requests()
    via_playwright()
    return 0


if __name__ == "__main__":
    sys.exit(main())
