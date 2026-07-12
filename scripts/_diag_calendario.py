"""
Diagnóstico TEMPORÁRIO (Fase 3 do calendário de pagamentos) — ronda 3.

Ronda 1: portal antigo morto para pedidos simples (redirect universal
para o gateway SSD). Ronda 2: o deep-link "Calendário" do portal novo é
só uma página de serviço (sem tabela de datas); a notícia antiga não é
restaurada pela SPA — mas a home tem uma secção "Notícias" com link
"Aceder às notícias". Esta ronda navega a secção de notícias do portal
novo à procura da notícia mensal "datas de pagamento" e despeja o
artigo completo, para calibrar o parser da Fase 3.

Só lê e imprime — nunca escreve ficheiros do repositório. Apagar este
script e o workflow correspondente no fim do diagnóstico.
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "https://www.seg-social.pt"

CANDIDATOS_LISTAGEM = [
    f"{BASE}/ptss/pssd/noticias",
    f"{BASE}/ptss/pssd/menu/noticias",
]


def dump_links(page) -> list[tuple[str, str]]:
    pares = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href]'))
            .map(a => [a.getAttribute('href'), a.innerText.trim().replace(/\\s+/g, ' ')])
            .filter(([h, t]) => t.length > 0)"""
    )
    return [(h, t) for h, t in pares]


def examinar_listagem(page, url: str) -> str | None:
    """Devolve o href da notícia de datas de pagamento, se existir."""
    print(f"\n{'='*78}\n[listagem] {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_function(
                "() => document.body && document.body.innerText.length > 2000",
                timeout=20000,
            )
        except Exception:
            print("  ⚠️ corpo nunca passou de 2000 chars em 20s")
        print(f"  url final: {page.url}")
        links = dump_links(page)
        print(f"  links com texto: {len(links)} — os que mencionam notícia/pagamento:")
        alvo = None
        for h, t in links:
            tl = t.lower()
            if "pagamento" in tl or "notícia" in tl or "noticia" in (h or "").lower():
                print(f"    [{t[:80]}] -> {h}")
                if re.search(r"datas? de pagamento", tl) and alvo is None:
                    alvo = h
        # também despejar os títulos visíveis (cards sem <a> directo)
        texto = page.evaluate("document.body.innerText")
        m = re.findall(r"[^\n]*[Dd]atas? de pagamento[^\n]*", texto)
        print(f"  linhas com 'datas de pagamento' no texto: {m[:5]}")
        return alvo
    except Exception as e:
        print(f"  ERRO: {e}")
        return None


def examinar_artigo(page, href: str) -> None:
    url = href if href.startswith("http") else BASE + href
    print(f"\n{'='*78}\n[artigo] {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_function(
                "() => document.body && /datas? de pagamento/i.test(document.body.innerText)",
                timeout=20000,
            )
        except Exception:
            print("  ⚠️ 'datas de pagamento' nunca apareceu em 20s")
        print(f"  url final: {page.url}")
        texto = page.evaluate("document.body.innerText")
        texto = re.sub(r"\n{3,}", "\n\n", texto.strip())
        print(f"  texto útil ({len(texto)} chars) — completo até 9000:")
        print("  ---")
        print(texto[:9000])
        print("  ---")
        n_tabelas = page.evaluate("document.querySelectorAll('table').length")
        print(f"  tabelas no DOM: {n_tabelas}")
    except Exception as e:
        print(f"  ERRO: {e}")


def tentar_clicar_aceder(page) -> None:
    """A partir da home, segue o link 'Aceder às notícias' da SPA."""
    print(f"\n{'='*78}\n[home->aceder às notícias] {BASE}")
    try:
        page.goto(f"{BASE}/ptss/pssd/home", wait_until="domcontentloaded",
                  timeout=45000)
        page.wait_for_function(
            "() => document.body && document.body.innerText.includes('Aceder às notícias')",
            timeout=20000,
        )
        with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            page.get_by_text("Aceder às notícias", exact=False).first.click()
        print(f"  url após clique: {page.url}")
        links = dump_links(page)
        print("  links relevantes na página de notícias:")
        alvo = None
        for h, t in links:
            tl = t.lower()
            if "pagamento" in tl:
                print(f"    [{t[:90]}] -> {h}")
                if re.search(r"datas? de pagamento", tl) and alvo is None:
                    alvo = h
        texto = page.evaluate("document.body.innerText")
        m = re.findall(r"[^\n]*[Dd]atas? de pagamento[^\n]*", texto)
        print(f"  linhas com 'datas de pagamento': {m[:8]}")
        if alvo:
            examinar_artigo(page, alvo)
        else:
            # sem link directo — talvez os cards sejam clicáveis por texto
            cartoes = [t for _, t in links][:40]
            print(f"  (sem link 'datas de pagamento'; 1.os títulos: {cartoes[:15]})")
    except Exception as e:
        print(f"  ERRO: {e}")


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(locale="pt-PT", timezone_id="Europe/Lisbon")
        page = context.new_page()
        alvo = None
        for url in CANDIDATOS_LISTAGEM:
            alvo = examinar_listagem(page, url) or alvo
        if alvo:
            examinar_artigo(page, alvo)
        else:
            tentar_clicar_aceder(page)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
