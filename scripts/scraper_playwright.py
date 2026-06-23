#!/usr/bin/env python3
"""
Scraper com Playwright (Chromium headless) para fontes oficiais portuguesas.
Usa IPs limpos do GitHub Actions e simula browser real.
Guarda resultados em data/scraped/[slug]_[YYYY-MM-DD].json
e data/scraped/[slug]_latest.json.

Modo de uso:
  python scripts/scraper_playwright.py               # scrape completo
  python scripts/scraper_playwright.py --mode=detect # só comparação de hashes
"""

import argparse
import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DIR = BASE_DIR / "data" / "scraped"
LOG_DIR = Path(__file__).resolve().parent / "logs"

SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper_playwright.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

FONTES = [
    {
        "slug": "seg_social_abono",
        "url": "https://www.seg-social.pt/abono-de-familia",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
            "tabelas": "table",
        },
    },
    {
        "slug": "seg_social_rsi",
        "url": "https://www.seg-social.pt/rendimento-social-de-insercao",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "dge_ase",
        "url": "https://www.dge.mec.pt/acao-social-escolar",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "dge_bolsa_merito",
        "url": "https://www.dge.mec.pt/bolsas-de-merito",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "dge_manuais",
        "url": "https://www.dge.mec.pt/manuais-escolares",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "iefp_desemprego",
        "url": "https://www.iefp.pt/subsidio-de-desemprego",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
]


def _texto_limpo(el) -> str:
    return " ".join(el.get_text(separator=" ").split()) if el else ""


def _extrair_conteudo(html: str, seletores: dict) -> dict:
    soup = BeautifulSoup(html, "lxml")
    conteudo: dict = {}

    if "titulo" in seletores:
        el = soup.select_one(seletores["titulo"])
        conteudo["titulo"] = _texto_limpo(el)

    if "paragrafos" in seletores:
        conteudo["paragrafos"] = [
            _texto_limpo(p)
            for p in soup.select(seletores["paragrafos"])
            if len(p.get_text(strip=True)) > 40
        ][:15]

    if "listas" in seletores:
        conteudo["itens_lista"] = [
            _texto_limpo(li)
            for li in soup.select(seletores["listas"])
            if len(li.get_text(strip=True)) > 10
        ][:30]

    if "tabelas" in seletores:
        tabelas = []
        for table in soup.select(seletores["tabelas"])[:3]:
            rows = []
            for tr in table.find_all("tr"):
                row = [_texto_limpo(td) for td in tr.find_all(["th", "td"])]
                if any(row):
                    rows.append(row)
            if rows:
                tabelas.append(rows)
        conteudo["tabelas"] = tabelas

    return conteudo


def scrape_fonte(page, fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    log.info("A scrape: %s", url)

    for attempt in range(1, 4):
        try:
            response = page.goto(url, timeout=30_000, wait_until="networkidle")
            if response and response.status in (200, 301, 302):
                break
            log.warning("HTTP %s em %s (tentativa %d)", response.status if response else "N/A", url, attempt)
        except Exception as exc:
            log.warning("Erro tentativa %d para %s: %s", attempt, url, exc)
        if attempt < 3:
            time.sleep(2 ** attempt)
    else:
        log.error("Falhou após 3 tentativas: %s", url)
        return None

    # Aguardar estabilização
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass

    time.sleep(2)

    html = page.content()
    conteudo = _extrair_conteudo(html, fonte["seletores"])

    resultado = {
        "url": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "conteudo_extraido": conteudo,
    }

    # Calcular hash do conteúdo (sem data_acesso)
    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado["hash_conteudo"] = hashlib.sha256(hash_payload.encode()).hexdigest()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = SCRAPED_DIR / f"{slug}_{today}.json"
    latest_path = SCRAPED_DIR / f"{slug}_latest.json"

    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Guardado: %s", daily_path)

    # Actualizar latest apenas se conteúdo mudou
    if latest_path.exists():
        try:
            old = json.loads(latest_path.read_text(encoding="utf-8"))
            if old.get("hash_conteudo") == resultado["hash_conteudo"]:
                log.info("%s: conteúdo idêntico ao latest — sem actualização", slug)
                return resultado
        except Exception:
            pass

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Actualizado latest: %s", latest_path)

    return resultado


def main(mode: str = "scrape"):
    from playwright.sync_api import sync_playwright

    resultados = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="pt-PT",
            extra_http_headers={
                "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        for fonte in FONTES:
            print(f"\n{'='*60}")
            print(f"Fonte: {fonte['slug']} — {fonte['url']}")
            print("=" * 60)
            try:
                r = scrape_fonte(page, fonte)
                if r:
                    resultados[fonte["slug"]] = "ok"
                    c = r.get("conteudo_extraido", {})
                    print(f"✓ OK — título: {c.get('titulo', '')[:80]}")
                    print(f"  hash: {r.get('hash_conteudo', '')[:16]}…")
                else:
                    resultados[fonte["slug"]] = "falhou"
                    print("✗ Falhou")
            except Exception as exc:
                resultados[fonte["slug"]] = f"erro: {exc}"
                log.exception("Erro inesperado em %s", fonte["slug"])
                print(f"✗ Erro: {exc}")

        page.close()
        context.close()
        browser.close()

    print(f"\n{'='*60}")
    print("RESUMO")
    print("=" * 60)
    for slug, estado in resultados.items():
        icone = "✓" if estado == "ok" else "✗"
        print(f"  {icone} {slug}: {estado}")

    ok = sum(1 for v in resultados.values() if v == "ok")
    print(f"\n{ok}/{len(resultados)} fontes scraped com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="scrape", choices=["scrape", "detect"])
    args = parser.parse_args()
    main(args.mode)
