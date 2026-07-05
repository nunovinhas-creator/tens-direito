#!/usr/bin/env python3
"""Diagnóstico temporário — estrutura real da página de pesquisa do DRE
para a PSU. Corre só num runner real (GitHub Actions) com acesso à
internet; o sandbox de desenvolvimento não alcança dre.pt. Apagado no
fim da investigação — não faz parte do pipeline.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
from scraper_playwright import _criar_context, _perfil_fonte  # noqa: E402

URL = "https://dre.pt/pesquisa?q=presta%C3%A7%C3%A3o+social+%C3%BAnica"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = _criar_context(browser, _perfil_fonte("dre_psu"))
        page = context.new_page()
        print(f"A navegar para {URL}")
        resp = page.goto(URL, timeout=30_000, wait_until="networkidle")
        print(f"HTTP status: {resp.status if resp else 'N/A'}")
        page.wait_for_timeout(3000)

        print(f"page.title(): {page.title()!r}")
        body_text = page.evaluate("() => document.body.innerText")
        print(f"body.innerText length (após networkidle+3s): {len(body_text)}")
        print("--- primeiros 2000 chars de body.innerText ---")
        print(body_text[:2000])

        # Esperar mais e comparar — testa se é preciso mais tempo de render
        page.wait_for_timeout(8000)
        body_text_2 = page.evaluate("() => document.body.innerText")
        print(f"\nbody.innerText length (após +8s adicionais): {len(body_text_2)}")
        if len(body_text_2) != len(body_text):
            print("--- cresceu! primeiros 2000 chars da versão mais tardia ---")
            print(body_text_2[:2000])

        # Contar candidatos a selectores de resultados
        for sel in ["h1", "p", "article", "li", ".resultado", ".result-item",
                    ".diploma", "table tr", "[class*='result']", "[class*='resultado']",
                    "[class*='pesquisa']", "[class*='search']"]:
            try:
                n = page.eval_on_selector_all(sel, "els => els.length")
            except Exception as exc:
                n = f"erro: {exc}"
            print(f"selector {sel!r}: {n}")

        html = page.content()
        print(f"\nHTML total: {len(html)} chars")
        Path("/tmp/dre_psu_dump.html").write_text(html, encoding="utf-8")

        browser.close()


if __name__ == "__main__":
    main()
