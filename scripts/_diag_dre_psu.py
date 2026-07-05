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

CANDIDATOS = [
    "https://dre.pt/pesquisa?q=presta%C3%A7%C3%A3o+social+%C3%BAnica",
    "https://dre.pt/dre/pesquisa?termo=presta%C3%A7%C3%A3o+social+%C3%BAnica",
    "https://dre.pt/dre/pesquisa-avancada",
    "https://dre.pt/web/guest/pesquisa",
    "https://dre.pt/pesquisa-avancada?tipo=texto&texto=presta%C3%A7%C3%A3o+social+%C3%BAnica",
    "https://dre.pt/",
]


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = _criar_context(browser, _perfil_fonte("dre_psu"))
        page = context.new_page()

        for url in CANDIDATOS:
            print(f"\n===== {url} =====")
            try:
                resp = page.goto(url, timeout=30_000, wait_until="networkidle")
                print(f"HTTP status: {resp.status if resp else 'N/A'}")
            except Exception as exc:
                print(f"ERRO no goto: {exc}")
                continue
            page.wait_for_timeout(3000)
            print(f"page.title(): {page.title()!r}")
            print(f"page.url final: {page.url}")
            body_text = page.evaluate("() => document.body.innerText")
            print(f"body.innerText length: {len(body_text)}")
            print(body_text[:600])


if __name__ == "__main__":
    main()
