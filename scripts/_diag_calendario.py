"""
Diagnóstico TEMPORÁRIO (Fase 3 do calendário de pagamentos) — ronda 4.

Rondas 1-3: portal antigo morto (redirect universal p/ SSD); deep-link
"Calendário" é página de serviço sem tabela; /ptss/pssd/noticias rende
a listagem real mas sem nenhuma notícia "datas de pagamento" na 1.ª
página. Esta ronda: (a) pagina a listagem toda (botão "ver/carregar
mais", se existir) e despeja TODOS os slugs; (b) testa slugs candidatos
directos; (c) explora a secção Pagamentos e dívidas à procura de um
calendário público.

Só lê e imprime. Apagar este script e o workflow no fim do diagnóstico.
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright

BASE = "https://www.seg-social.pt"

SLUGS_CANDIDATOS = [
    "/ptss/pssd/noticias/datas-pagamento-subsidios-sociais-pensoes-julho-2026",
    "/ptss/pssd/noticias/datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-julho",
    "/ptss/pssd/noticias/datas-pagamento-julho-2026",
    "/ptss/pssd/noticias/calendario-pagamentos-julho-2026",
]

PAGINAS_EXPLORAR = [
    "/ptss/pssd/menu/pagamentos-dividas",
    "/ptss/pssd/menu/pagamentos-dividas/valores-a-receber",
]


def corpo(page) -> str:
    return page.evaluate("document.body ? document.body.innerText : ''")


def listar_toda_a_listagem(page) -> None:
    print(f"\n{'='*78}\n[listagem paginada] {BASE}/ptss/pssd/noticias")
    page.goto(f"{BASE}/ptss/pssd/noticias", wait_until="domcontentloaded",
              timeout=45000)
    page.wait_for_function(
        "() => document.querySelectorAll(\"a[href*='/ptss/pssd/noticias/']\").length > 3",
        timeout=20000,
    )
    for ronda in range(12):
        botoes = page.get_by_role("button").all()
        alvo = None
        for b in botoes:
            try:
                t = (b.inner_text() or "").lower()
            except Exception:
                continue
            if re.search(r"ver mais|carregar|mostrar mais|mais notícias", t):
                alvo = b
                break
        if alvo is None:
            # tentar link em vez de botão
            try:
                link = page.get_by_text(re.compile(
                    r"ver mais|carregar mais|mostrar mais", re.I)).first
                if link.count() == 0:
                    break
                alvo = link
            except Exception:
                break
        try:
            alvo.click(timeout=5000)
            page.wait_for_timeout(1500)
        except Exception:
            break
    pares = page.evaluate(
        """() => Array.from(document.querySelectorAll("a[href*='/ptss/pssd/noticias/']"))
            .map(a => [a.getAttribute('href'), a.innerText.trim().replace(/\\s+/g,' ').slice(0,90)])"""
    )
    vistos = set()
    print(f"  total de links de notícia após paginação: {len(pares)}")
    for h, t in pares:
        if h in vistos:
            continue
        vistos.add(h)
        print(f"    {h}  [{t}]")
    texto = corpo(page)
    m = re.findall(r"[^\n]*[Dd]atas? de pagamento[^\n]*", texto)
    print(f"  linhas com 'datas de pagamento': {m[:5]}")


def testar_slug(page, slug: str) -> None:
    url = BASE + slug
    print(f"\n{'='*78}\n[slug candidato] {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(4000)
        texto = corpo(page)
        tem = bool(re.search(r"datas? de pagamento", texto, re.I))
        print(f"  url final: {page.url}")
        print(f"  contém 'datas de pagamento': {tem}; chars: {len(texto)}")
        if tem:
            print("  ---")
            print(re.sub(r"\n{3,}", "\n\n", texto.strip())[:7000])
            print("  ---")
    except Exception as e:
        print(f"  ERRO: {e}")


def explorar(page, caminho: str) -> None:
    url = BASE + caminho
    print(f"\n{'='*78}\n[explorar] {url}")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_function(
            "() => document.body && document.body.innerText.length > 1500",
            timeout=20000,
        )
        pares = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href]'))
                .map(a => [a.getAttribute('href'), a.innerText.trim().replace(/\\s+/g,' ').slice(0,80)])
                .filter(([h,t]) => t.length > 0 && (h.includes('pagamento') || h.includes('calendario') || /calend|pagament/i.test(t)))"""
        )
        print("  links de pagamento/calendário:")
        for h, t in pares:
            print(f"    {h}  [{t}]")
        texto = corpo(page)
        m = re.findall(r"[^\n]*[Cc]alend[^\n]*", texto)
        print(f"  linhas com 'calend…': {m[:8]}")
    except Exception as e:
        print(f"  ERRO: {e}")


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context(locale="pt-PT", timezone_id="Europe/Lisbon")
        page = context.new_page()
        listar_toda_a_listagem(page)
        for slug in SLUGS_CANDIDATOS:
            testar_slug(page, slug)
        for caminho in PAGINAS_EXPLORAR:
            explorar(page, caminho)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
