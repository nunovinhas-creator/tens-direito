#!/usr/bin/env python3
"""Diagnóstico temporário — confirmar estrutura da página real de
resultados do DRE (dre.pt/dre/pesquisa?termo=...) antes de corrigir o
scraper. Corre só num runner real; apagado no fim da investigação.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from scraper_playwright import _criar_context, _perfil_fonte  # noqa: E402

URL = "https://dre.pt/dre/pesquisa?termo=presta%C3%A7%C3%A3o+social+%C3%BAnica"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = _criar_context(browser, _perfil_fonte("dre_psu"))
        page = context.new_page()
        resp = page.goto(URL, timeout=30_000, wait_until="networkidle")
        print(f"HTTP status: {resp.status if resp else 'N/A'}")
        print(f"page.url final: {page.url}")

        for espera in (2000, 5000, 10000):
            page.wait_for_timeout(espera)
            texto = page.evaluate("() => document.body.innerText")
            print(f"\n--- após +{espera}ms: innerText length = {len(texto)} ---")

        print("\n===== innerText completo =====")
        print(texto)

        print("\n===== contagem de selectores =====")
        for sel in ["h1", "h2", "h3", "p", "article", "li", "table tr",
                    "[class*='result']", "[class*='resultado']", "[class*='item']",
                    "[class*='card']", "[class*='diploma']", "a[href*='/dr/detalhe']"]:
            try:
                n = page.eval_on_selector_all(sel, "els => els.length")
            except Exception as exc:
                n = f"erro: {exc}"
            print(f"selector {sel!r}: {n}")

        print("\n===== primeiros 10 hrefs com '/dr/' =====")
        hrefs = page.eval_on_selector_all(
            "a[href*='/dr/']",
            "els => els.map(e => ({texto: e.innerText.trim().slice(0,120), href: e.href}))",
        )
        for h in hrefs[:15]:
            print(h)

        browser.close()


if __name__ == "__main__":
    main()
