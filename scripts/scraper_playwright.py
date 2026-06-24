#!/usr/bin/env python3
"""
Scraper para fontes oficiais portuguesas.
- Fontes Playwright (Chromium headless): portais .pt com browser real
- Fontes DRE: RSS público da Série I (https://dre.pt/rss/dr1s.rss)

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

import requests
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

# ── Fontes Playwright ──────────────────────────────────────────────────────────
FONTES_PLAYWRIGHT = [
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
    # dge.mec.pt/acao-social-escolar devolve 403 para bots.
    # Estratégia: homepage DGE para links/notícias ASE + DRE API para diplomas.
    {
        "slug": "dge_ase",
        "url": "https://www.dge.mec.pt",
        "url_fallback": "https://dre.pt/pesquisa?q=acao+social+escolar",
        "nota": "dge.mec.pt/acao-social-escolar bloqueado — usar DRE como fonte primária para ASE",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
            "links": "a[href]",
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
    # IEFP só recebe o pedido; decisão e pagamento são da Seg. Social.
    # URL correcto: /subsidio-desemprego (sem /en/ e sem hífen duplo).
    # Fallback: seg-social.pt que é a entidade pagadora.
    {
        "slug": "iefp_desemprego",
        "url": "https://www.iefp.pt/subsidio-desemprego",
        "url_fallback": "https://www.seg-social.pt/subsidio-de-desemprego",
        "nota": "IEFP recebe pedido; decisão e pagamento são da Segurança Social — fallback para seg-social.pt",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "mega_datas",
        "url": "https://www.dge.mec.pt/manuais-escolares",
        "nota": "DGE manuais escolares — detectar datas de atribuição de vouchers 2026/2027",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
        "detectar_ano": "2026/2027",
    },
]

# O DRE não disponibiliza feed RSS acessível nos runners GitHub Actions.
# Verificação de nova legislação é feita manualmente em https://dre.pt
# quando o validador de conteúdo detecta mudanças nas fontes principais.
# Ver data/scraped/dre_status.json para o estado actual.


# ── Utilitários Playwright ─────────────────────────────────────────────────────

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

    if "links" in seletores:
        conteudo["links_uteis"] = [
            {"texto": _texto_limpo(a), "href": a.get("href", "")}
            for a in soup.select(seletores["links"])
            if a.get("href", "").startswith("http") and len(a.get_text(strip=True)) > 5
        ][:20]

    return conteudo


def _tentar_goto(page, url: str) -> bool:
    for attempt in range(1, 4):
        try:
            response = page.goto(url, timeout=30_000, wait_until="networkidle")
            if response and response.status in (200, 301, 302):
                return True
            log.warning("HTTP %s em %s (tentativa %d)", response.status if response else "N/A", url, attempt)
        except Exception as exc:
            log.warning("Erro tentativa %d para %s: %s", attempt, url, exc)
        if attempt < 3:
            time.sleep(2 ** attempt)
    return False


def scrape_playwright(page, fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    url_fallback = fonte.get("url_fallback")
    nota = fonte.get("nota", "")
    log.info("A scrape (Playwright): %s", url)

    url_usado = url
    ok = _tentar_goto(page, url)

    if not ok and url_fallback:
        log.warning("%s: URL principal falhou — a tentar fallback %s", slug, url_fallback)
        url_usado = url_fallback
        ok = _tentar_goto(page, url_fallback)

    if not ok:
        log.error("Falhou após 3 tentativas (principal%s): %s",
                  " + fallback" if url_fallback else "", url)
        return None

    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass
    time.sleep(5)

    html = page.content()
    conteudo = _extrair_conteudo(html, fonte["seletores"])

    resultado = {
        "url": url_usado,
        "url_original": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "conteudo_extraido": conteudo,
    }
    if nota:
        resultado["nota"] = nota

    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado["hash_conteudo"] = hashlib.sha256(hash_payload.encode()).hexdigest()

    _guardar_resultado(slug, resultado)

    # Detectar ano lectivo novo (ex: MEGA 2026/2027)
    ano_detectar = fonte.get("detectar_ano")
    if ano_detectar and ano_detectar in html:
        _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
        log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)

    return resultado


# ── Guardar resultado ──────────────────────────────────────────────────────────

AVISOS_LOG = SCRAPED_DIR / "avisos.log"
MIN_CHARS_CONTEUDO = 100


def _conteudo_chars(conteudo: dict) -> int:
    """Conta caracteres totais do conteúdo extraído (títulos + parágrafos + listas)."""
    total = len(conteudo.get("titulo", ""))
    for p in conteudo.get("paragrafos", []):
        total += len(p)
    for li in conteudo.get("itens_lista", []):
        total += len(li)
    for r in conteudo.get("resultados", []):
        total += len(r.get("titulo", "")) + len(r.get("sumario", ""))
    return total


def _registar_aviso(slug: str, motivo: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    linha = f"{ts} AVISO slug={slug} motivo={motivo}\n"
    with open(AVISOS_LOG, "a", encoding="utf-8") as f:
        f.write(linha)
    log.warning("AVISO registado em avisos.log: %s — %s", slug, motivo)


def _guardar_resultado(slug: str, resultado: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = SCRAPED_DIR / f"{slug}_{today}.json"
    latest_path = SCRAPED_DIR / f"{slug}_latest.json"

    # Validação mínima de conteúdo
    conteudo = resultado.get("conteudo_extraido", {})
    chars = _conteudo_chars(conteudo)
    if chars < MIN_CHARS_CONTEUDO:
        motivo = f"conteúdo suspeito: apenas {chars} caracteres (mínimo {MIN_CHARS_CONTEUDO})"
        _registar_aviso(slug, motivo)
        # Guardar o ficheiro diário mesmo assim (para auditoria), mas NÃO actualizar latest
        resultado["aviso"] = motivo
        with open(daily_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        log.warning("%s: latest NÃO actualizado — %s", slug, motivo)
        return

    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Guardado: %s", daily_path)

    if latest_path.exists():
        try:
            old = json.loads(latest_path.read_text(encoding="utf-8"))
            if old.get("hash_conteudo") == resultado["hash_conteudo"]:
                log.info("%s: conteúdo idêntico ao latest — sem atualização", slug)
                return
        except Exception:
            pass

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Atualizado latest: %s", latest_path)


# ── Main ───────────────────────────────────────────────────────────────────────

def main(mode: str = "scrape"):
    from playwright.sync_api import sync_playwright

    resultados = {}

    # ── Playwright ────────────────────────────────────────────────────────────
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

        for fonte in FONTES_PLAYWRIGHT:
            print(f"\n{'='*60}")
            print(f"[Playwright] {fonte['slug']} — {fonte['url']}")
            print("=" * 60)
            try:
                r = scrape_playwright(page, fonte)
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

    # ── DRE — estado manual ───────────────────────────────────────────────────
    dre_status = {
        "status": "manual",
        "nota": (
            "O DRE não tem feed público acessível nos runners GitHub Actions — "
            "verificação de nova legislação é feita manualmente em https://dre.pt "
            "quando o validador de conteúdo detecta mudanças nas fontes principais"
        ),
        "data": datetime.now(timezone.utc).date().isoformat(),
    }
    dre_status_path = SCRAPED_DIR / "dre_status.json"
    dre_status_path.write_text(json.dumps(dre_status, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[DRE] Estado manual registado em dre_status.json")

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
