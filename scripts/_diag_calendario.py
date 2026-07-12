"""
Diagnóstico TEMPORÁRIO (Fase 3 do calendário de pagamentos) — ronda 2.

Ronda 1 (requests) provou que o portal antigo está morto para pedidos
simples: a notícia mensal, /noticias e /pagamentos2 redireccionam todos
para o gateway da SSD (/ptss/pssd/home?r=...), devolvendo só a shell de
cookies (213 chars). Esta ronda testa a via Playwright:

  A. deep-link do portal novo "Calendário" (valores-a-receber) — mesma
     família dos deep-links que o scraper de produção já usa com
     sucesso (perfil sem headers custom, espera explícita por âncora);
  B. a própria notícia mensal via Playwright — o parâmetro ?r= sugere
     que a SPA pode rotear de volta ao recurso pedido depois de carregar.

Só lê e imprime — nunca escreve ficheiros do repositório. Apagar este
script e o workflow correspondente no fim do diagnóstico.
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "https://www.seg-social.pt"

ALVOS = [
    # (nome, url, frase de âncora a esperar no DOM)
    ("calendario_portal_novo",
     f"{BASE}/ptss/pssd/menu/pagamentos-dividas/valores-a-receber/calendario",
     "alendário"),
    ("noticia_julho_via_spa",
     f"{BASE}/noticias/-/asset_publisher/kBZtOMZgstp3/content/"
     "datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-julho",
     "agamento"),
    ("noticia_agosto_via_spa",
     f"{BASE}/noticias/-/asset_publisher/kBZtOMZgstp3/content/"
     "datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-agosto",
     "agamento"),
]


def examinar(page, nome: str, url: str, ancora: str) -> None:
    print(f"\n{'='*78}\n[{nome}] {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_function(
                "frase => document.body && document.body.innerText.includes(frase)",
                arg=ancora, timeout=20000,
            )
            print(f"  âncora '{ancora}' encontrada no DOM")
        except Exception:
            print(f"  ⚠️ âncora '{ancora}' NUNCA apareceu em 20s")
        print(f"  url final: {page.url}")
        print(f"  title: {page.title()}")
        texto = page.evaluate("document.body ? document.body.innerText : ''")
        texto = re.sub(r"\n{3,}", "\n\n", texto.strip())
        print(f"  texto útil ({len(texto)} chars) — primeiros 7000:")
        print("  ---")
        print(texto[:7000])
        print("  ---")
        n_tabelas = page.evaluate("document.querySelectorAll('table').length")
        print(f"  tabelas no DOM: {n_tabelas}")
    except Exception as e:
        print(f"  ERRO: {e}")


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        # perfil provado no scraper de produção para seg-social:
        # sem extra_http_headers (causavam 500 real do backend),
        # locale/timezone PT
        context = browser.new_context(
            locale="pt-PT", timezone_id="Europe/Lisbon",
        )
        page = context.new_page()
        for nome, url, ancora in ALVOS:
            examinar(page, nome, url, ancora)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
