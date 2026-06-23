#!/usr/bin/env python3
"""
Scraper modular de fontes oficiais portuguesas para o Tens Direito.
Respeita robots.txt, simula browser real, retry com backoff exponencial.
Guarda resultados em data/scraped/ e regista erros em scripts/logs/scraper.log
"""

import json
import logging
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DIR = BASE_DIR / "data" / "scraped"
LOG_DIR = Path(__file__).resolve().parent / "logs"
VERIFICACAO_PENDENTE = BASE_DIR / "VERIFICACAO-PENDENTE.md"

SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

TIMEOUT = 10
MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def _robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        return True  # se não conseguir ler robots.txt, assumir permitido


def _fetch(url: str) -> requests.Response | None:
    if not _robots_allowed(url):
        log.warning("robots.txt proíbe acesso a %s", url)
        return None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp
            log.warning("HTTP %s em %s (tentativa %d)", resp.status_code, url, attempt)
        except requests.RequestException as exc:
            log.warning("Erro na tentativa %d para %s: %s", attempt, url, exc)
        if attempt < MAX_RETRIES:
            time.sleep(2 ** attempt)  # 2s, 4s, 8s

    _registar_pendente(url, f"Falhou após {MAX_RETRIES} tentativas")
    return None


def _save(fonte: str, data: dict) -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = SCRAPED_DIR / f"{fonte}_{today}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Guardado: %s", filename)
    return filename


def _resultado(url: str, status: str, conteudo: dict) -> dict:
    return {
        "url": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "conteudo_extraido": conteudo,
    }


def _is_error_page(soup: BeautifulSoup) -> bool:
    title = soup.title.string.lower() if soup.title else ""
    text = soup.get_text().lower()
    error_signals = ["404", "página não encontrada", "page not found", "erro", "unavailable"]
    return any(s in title or s in text[:500] for s in error_signals)


def _registar_pendente(url: str, motivo: str):
    log.error("VERIFICAÇÃO PENDENTE — %s: %s", url, motivo)
    entry = (
        f"\n## Verificação pendente — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"- **URL:** {url}\n"
        f"- **Motivo:** {motivo}\n"
    )
    with open(VERIFICACAO_PENDENTE, "a", encoding="utf-8") as f:
        f.write(entry)


def _texto_limpo(el) -> str:
    return " ".join(el.get_text(separator=" ").split()) if el else ""


# ---------------------------------------------------------------------------
# Scrapers por fonte
# ---------------------------------------------------------------------------

def scrape_seg_social_abono() -> dict | None:
    url = "https://www.seg-social.pt/abono-de-familia"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
        "tabelas": [],
    }

    for table in soup.find_all("table")[:3]:
        rows = []
        for tr in table.find_all("tr"):
            row = [_texto_limpo(td) for td in tr.find_all(["th", "td"])]
            if any(row):
                rows.append(row)
        if rows:
            conteudo["tabelas"].append(rows)

    resultado = _resultado(url, "ok", conteudo)
    _save("seg_social_abono", resultado)
    return resultado


def scrape_seg_social_rsi() -> dict | None:
    url = "https://www.seg-social.pt/rendimento-social-de-insercao"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
    }

    resultado = _resultado(url, "ok", conteudo)
    _save("seg_social_rsi", resultado)
    return resultado


def scrape_dge_ase() -> dict | None:
    url = "https://www.dge.mec.pt/acao-social-escolar"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
        "links_uteis": [
            {"texto": _texto_limpo(a), "href": a.get("href", "")}
            for a in soup.find_all("a", href=True)
            if "escalão" in a.get_text().lower() or "candidatur" in a.get_text().lower()
        ][:10],
    }

    resultado = _resultado(url, "ok", conteudo)
    _save("dge_ase", resultado)
    return resultado


def scrape_dge_bolsa_merito() -> dict | None:
    url = "https://www.dge.mec.pt/bolsas-de-merito"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
    }

    resultado = _resultado(url, "ok", conteudo)
    _save("dge_bolsa_merito", resultado)
    return resultado


def scrape_mega_manuais() -> dict | None:
    url = "https://mega.mec.pt"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
    }

    resultado = _resultado(url, "ok", conteudo)
    _save("mega_manuais", resultado)
    return resultado


def scrape_dre_legislacao(termo: str) -> dict | None:
    url = f"https://dre.pt/pesquisa?q={requests.utils.quote(termo)}&type=DR1S"
    log.info("A fazer scrape DRE para '%s': %s", termo, url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    # Tenta extrair o primeiro resultado da pesquisa
    diplomas = []
    for item in soup.select(".search-result, .result-item, article")[:5]:
        titulo_el = item.find(["h2", "h3", "h4", "strong"])
        link_el = item.find("a", href=True)
        data_el = item.find(class_=lambda c: c and ("date" in c or "data" in c))
        diplomas.append({
            "titulo": _texto_limpo(titulo_el) if titulo_el else "",
            "url": urljoin("https://dre.pt", link_el["href"]) if link_el else "",
            "data": _texto_limpo(data_el) if data_el else "",
        })

    conteudo = {"termo": termo, "diplomas": diplomas}
    resultado = _resultado(url, "ok", conteudo)
    _save(f"dre_{termo.replace(' ', '_')[:30]}", resultado)
    return resultado


def scrape_iefp_desemprego() -> dict | None:
    url = "https://www.iefp.pt/subsidio-de-desemprego"
    log.info("A fazer scrape: %s", url)
    resp = _fetch(url)
    if not resp:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    if _is_error_page(soup):
        _registar_pendente(url, "Página de erro devolvida")
        return None

    conteudo = {
        "titulo": _texto_limpo(soup.find("h1")),
        "paragrafos": [_texto_limpo(p) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40][:15],
        "listas": [
            [_texto_limpo(li) for li in ul.find_all("li")]
            for ul in soup.find_all(["ul", "ol"])
            if len(ul.find_all("li")) > 1
        ][:5],
    }

    resultado = _resultado(url, "ok", conteudo)
    _save("iefp_desemprego", resultado)
    return resultado


# ---------------------------------------------------------------------------
# Execução directa — testa todas as fontes
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    scrapers = [
        ("seg_social_abono", scrape_seg_social_abono),
        ("seg_social_rsi", scrape_seg_social_rsi),
        ("dge_ase", scrape_dge_ase),
        ("dge_bolsa_merito", scrape_dge_bolsa_merito),
        ("mega_manuais", scrape_mega_manuais),
        ("dre_abono_de_familia", lambda: scrape_dre_legislacao("abono de família 2026")),
        ("iefp_desemprego", scrape_iefp_desemprego),
    ]

    resultados = {}
    for nome, fn in scrapers:
        print(f"\n{'='*60}")
        print(f"A testar: {nome}")
        print('='*60)
        try:
            r = fn()
            if r:
                resultados[nome] = "ok"
                print(f"✓ STATUS: {r['status']}")
                conteudo = r.get("conteudo_extraido", {})
                if conteudo.get("titulo"):
                    print(f"  Título: {conteudo['titulo'][:80]}")
                if conteudo.get("paragrafos"):
                    print(f"  1.º parágrafo: {conteudo['paragrafos'][0][:120]}…")
            else:
                resultados[nome] = "falhou"
                print("✗ Falhou (ver VERIFICACAO-PENDENTE.md e scripts/logs/scraper.log)")
        except Exception as exc:
            resultados[nome] = f"erro: {exc}"
            log.exception("Erro inesperado em %s", nome)
            print(f"✗ Erro: {exc}")

    print(f"\n{'='*60}")
    print("RESUMO")
    print('='*60)
    for nome, estado in resultados.items():
        icone = "✓" if estado == "ok" else "✗"
        print(f"  {icone} {nome}: {estado}")
