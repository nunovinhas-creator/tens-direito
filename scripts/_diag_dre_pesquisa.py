#!/usr/bin/env python3
"""Diagnóstico TEMPORÁRIO — mecanismo real de pesquisa do DRE/diariodarepublica.pt.

Corre num runner real (workflow_dispatch), nunca no sandbox de sessão
(política de rede bloqueia dre.pt/diariodarepublica.pt — confirmado).

Objectivo: encontrar um mecanismo FIÁVEL para a fonte `dre_psu` — uma URL
de navegação directa que devolva resultados FILTRADOS pelo termo, ou o
endpoint de API/XHR que a SPA usa por baixo. O endpoint actual
(dre.pt/pesquisa?q=...) devolve soft-404; o candidato anterior
(dre.pt/dre/pesquisa?termo=...) devolvia o índice inteiro (2,2M
resultados) — qualquer solução tem de provar filtragem real, nunca só
HTTP 200 (ver CLAUDE.md "INVARIANTE — NENHUM ESTADO DE ERRO PODE
PARECER SUCESSO").

Apagar este ficheiro (e o workflow que o chama) no fim do diagnóstico.
"""
from __future__ import annotations

import json
import re
import sys

from playwright.sync_api import sync_playwright

TERMO = "prestação social única"
TERMO_URL = "presta%C3%A7%C3%A3o%20social%20%C3%BAnica"
TERMO_URL_PLUS = "presta%C3%A7%C3%A3o+social+%C3%BAnica"

CANDIDATAS_DIRECTAS: list[tuple[str, str]] = []

PALAVRAS_REDE = ("pesquisa", "search", "api", "query", "solr", "elastic", "resultado")


def _contar_resultados(texto: str) -> str:
    """Extrai o texto de contagem de resultados, se existir."""
    padroes = [
        r"\d[\d\s.,]*\s+de\s+[\d\s.,]+\s+resultados?",
        r"[\d.,]+\s+resultados?",
        r"resultados?\s*[:—-]?\s*[\d.,]+",
    ]
    for p in padroes:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            return m.group(0)
    return "(nenhum padrão de contagem encontrado)"


def _resumo_pagina(page, rotulo: str) -> None:
    corpo = ""
    try:
        corpo = page.inner_text("body")
    except Exception as e:  # noqa: BLE001
        print(f"    [!] inner_text falhou: {e}")
    corpo_limpo = " ".join(corpo.split())
    print(f"    url_final : {page.url}")
    try:
        print(f"    titulo    : {page.title()!r}")
    except Exception:  # noqa: BLE001
        pass
    print(f"    chars body: {len(corpo_limpo)}")
    print(f"    contagem  : {_contar_resultados(corpo_limpo)}")
    ocorr = corpo_limpo.lower().count("prestação social única")
    print(f"    ocorrências do termo no body: {ocorr}")
    print("    primeiros 900 chars do body:")
    print("    " + corpo_limpo[:900].replace("\n", " "))
    # Títulos de resultados prováveis
    for sel in ("h2", "h3", ".result-title", "a[href*='detalhe']"):
        try:
            els = page.locator(sel)
            n = min(els.count(), 8)
            if n:
                textos = [" ".join(els.nth(i).inner_text().split())[:120] for i in range(n)]
                textos = [t for t in textos if t]
                if textos:
                    print(f"    {sel} (até 8): {textos}")
        except Exception:  # noqa: BLE001
            pass
    print(f"[RESUMO-FIM] {rotulo}")


def _instalar_captura_rede(page, registos: list) -> None:
    def on_response(resp):
        url = resp.url
        low = url.lower()
        if not any(p in low for p in PALAVRAS_REDE):
            return
        if any(ext in low for ext in (".js", ".css", ".png", ".svg", ".woff", ".jpg", ".gif", ".ico")):
            return
        entrada = {
            "metodo": resp.request.method,
            "url": url[:400],
            "status": resp.status,
            "tipo": resp.headers.get("content-type", "?")[:60],
        }
        try:
            if "json" in entrada["tipo"]:
                corpo = resp.body()
                if corpo and len(corpo) < 400_000:
                    entrada["json_inicio"] = corpo.decode("utf-8", "replace")[:1000]
        except Exception as e:  # noqa: BLE001
            entrada["erro_body"] = str(e)[:120]
        registos.append(entrada)

    page.on("response", on_response)


def _dump_resultados(page) -> None:
    """Inventário do markup dos resultados: links, títulos e um exemplo
    de outerHTML — para configurar os selectores reais do scraper."""
    corpo = " ".join(page.inner_text("body").split())
    print("    body chars 900-5500 (zona de resultados):")
    print("    " + corpo[900:5500])
    print("    links com texto longo (até 30):")
    try:
        links = page.locator("a")
        total = links.count()
        vistos = 0
        for i in range(total):
            if vistos >= 30:
                break
            el = links.nth(i)
            try:
                txt = " ".join((el.inner_text() or "").split())
                href = el.get_attribute("href") or ""
            except Exception:  # noqa: BLE001
                continue
            if len(txt) > 30 or "detalhe" in href:
                print(f"      [{i}] href={href[:120]!r} texto={txt[:140]!r}")
                vistos += 1
    except Exception as e:  # noqa: BLE001
        print(f"    [!] inventário de links falhou: {e}")
    try:
        primeiro = page.locator("a[href*='detalhe']").first
        html_avo = primeiro.evaluate(
            "el => el.parentElement && el.parentElement.parentElement"
            " ? el.parentElement.parentElement.outerHTML : el.outerHTML"
        )
        print("    outerHTML do avô do 1.º link 'detalhe' (até 2500 chars):")
        print("    " + " ".join(html_avo.split())[:2500])
    except Exception as e:  # noqa: BLE001
        print(f"    [!] outerHTML falhou: {e}")


def _pesquisa_interactiva(ctx, termo: str, rotulo: str, dump: bool = False) -> None:
    print(f"\n{'=' * 72}\n[INTERACTIVA] {rotulo} — termo: {termo!r}")
    page = ctx.new_page()
    try:
        page.goto("https://diariodarepublica.pt/dr/home",
                  wait_until="domcontentloaded", timeout=45_000)
        page.wait_for_timeout(6_000)
        campo = page.locator("input[type='search']").first
        campo.click()
        campo.fill(termo)
        page.wait_for_timeout(800)
        campo.press("Enter")
        page.wait_for_timeout(12_000)
        _resumo_pagina(page, rotulo)
        if dump:
            _dump_resultados(page)
    except Exception as e:  # noqa: BLE001
        print(f"    [ERRO interactiva] {e}")
    finally:
        page.close()


def main() -> int:
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="pt-PT",
            timezone_id="Europe/Lisbon",
            viewport={"width": 1280, "height": 900},
        )

        # ── Fase 0 (2.ª iteração): frase exacta com aspas + markup ─────
        _pesquisa_interactiva(ctx, f'"{TERMO}"', "frase exacta com aspas", dump=True)
        ctx.clear_cookies()
        _pesquisa_interactiva(ctx, TERMO, "sem aspas (referência)", dump=False)
        ctx.clear_cookies()

        # ── Fase 1: candidatas de navegação directa ────────────────────
        for rotulo, url in CANDIDATAS_DIRECTAS:
            print(f"\n{'=' * 72}\n[CANDIDATA] {rotulo}\n  {url}")
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(10_000)
                _resumo_pagina(page, rotulo)
            except Exception as e:  # noqa: BLE001
                print(f"    [ERRO] {e}")
            finally:
                page.close()

        # ── Fase 2: pesquisa interactiva com captura de rede ──────────
        print(f"\n{'=' * 72}\n[INTERACTIVA] diariodarepublica.pt — pesquisa real na caixa")
        registos: list = []
        page = ctx.new_page()
        url_final_interactiva = None
        try:
            _instalar_captura_rede(page, registos)
            page.goto("https://diariodarepublica.pt/dr/home",
                      wait_until="domcontentloaded", timeout=45_000)
            page.wait_for_timeout(8_000)
            print(f"    home carregada: {page.url}")

            campo = None
            seletores_campo = [
                "input[type='search']",
                "input[placeholder*='esquis']",
                "input[name*='pesquis']",
                "input[id*='pesquis']",
                "input[id*='search']",
                "input[class*='search']",
                "input[type='text']",
            ]
            for sel in seletores_campo:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible():
                    campo = loc.first
                    print(f"    campo de pesquisa encontrado: {sel}")
                    break
            if campo is None:
                print("    [!] nenhum campo visível — inventário de todos os inputs:")
                for i in range(page.locator("input").count()):
                    el = page.locator("input").nth(i)
                    try:
                        print(f"      input[{i}]: "
                              f"type={el.get_attribute('type')} "
                              f"id={el.get_attribute('id')} "
                              f"name={el.get_attribute('name')} "
                              f"placeholder={el.get_attribute('placeholder')} "
                              f"visivel={el.is_visible()}")
                    except Exception:  # noqa: BLE001
                        pass
            else:
                campo.click()
                campo.fill(TERMO)
                page.wait_for_timeout(1_000)
                campo.press("Enter")
                page.wait_for_timeout(12_000)
                url_final_interactiva = page.url
                _resumo_pagina(page, "pesquisa interactiva")
        except Exception as e:  # noqa: BLE001
            print(f"    [ERRO interactiva] {e}")
        finally:
            page.close()

        print(f"\n{'=' * 72}\n[REDE] pedidos relevantes capturados: {len(registos)}")
        for r in registos:
            print(json.dumps(r, ensure_ascii=False)[:1400])

        # ── Fase 3: reproduzir a URL final da interactiva numa página nova
        if url_final_interactiva and "pesquisa" in url_final_interactiva.lower():
            print(f"\n{'=' * 72}\n[REPRODUCAO] navegação directa à URL da interactiva:")
            print(f"  {url_final_interactiva}")
            page = ctx.new_page()
            try:
                page.goto(url_final_interactiva, wait_until="domcontentloaded", timeout=45_000)
                page.wait_for_timeout(12_000)
                _resumo_pagina(page, "reprodução directa")
            except Exception as e:  # noqa: BLE001
                print(f"    [ERRO] {e}")
            finally:
                page.close()
        else:
            print("\n[REPRODUCAO] saltada — interactiva não produziu URL de pesquisa")

        browser.close()
    print("\n[DIAG] concluído")
    return 0


if __name__ == "__main__":
    sys.exit(main())
