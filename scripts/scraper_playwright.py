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
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from classificador_resposta import classificar_resposta, Estado, FonteConfig  # noqa: E402
from wayback_fallback import decidir_estado_apos_bloqueio  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DIR = BASE_DIR / "data" / "scraped"
LOG_DIR = Path(__file__).resolve().parent / "logs"

SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

BLOQUEIOS_PATH = BASE_DIR / "data" / "bloqueios.json"

# FonteConfig por slug — calibrado com dados reais (2026-06-30)
# seg_social reais esperados >>500 chars; login page = 23 chars (título apenas)
# dge/mega reais: 1731–2534 chars; iefp real: 4280 chars
_FONTE_CONFIGS: dict[str, FonteConfig] = {
    # As URLs planas (antigas e novas) redireccionam sempre para o portal
    # de autenticação /ptss/pssd/home — confirmado num runner real, com e
    # sem Playwright. "app.seg-social.pt" continua para compatibilidade
    # com dados antigos; "seg-social.pt/ptss/pssd/home" apanha o gateway
    # sem apanhar os deep-links /ptss/pssd/menu/... usados abaixo (ver
    # CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
    "seg_social_abono": FonteConfig(
        nome="Segurança Social — Abono de Família",
        min_chars_uteis=500,
        dominios_login=("app.seg-social.pt", "seg-social.pt/ptss/pssd/home"),
        ancora_conteudo=("abono de família",),
        metodo="playwright",
    ),
    "seg_social_rsi": FonteConfig(
        nome="Segurança Social — RSI",
        min_chars_uteis=500,
        dominios_login=("app.seg-social.pt", "seg-social.pt/ptss/pssd/home"),
        ancora_conteudo=("rendimento social de inserção",),
        metodo="playwright",
    ),
    "dge_ase": FonteConfig(nome="DGE — ASE", min_chars_uteis=300),
    "dge_manuais": FonteConfig(nome="DGE — Manuais Escolares", min_chars_uteis=300),
    "iefp_desemprego": FonteConfig(
        nome="IEFP — Subsídio de Desemprego",
        min_chars_uteis=500,
        ancora_conteudo=("subsídio de desemprego",),
        metodo="http",
    ),
    "mega_datas": FonteConfig(nome="DGE — MEGA datas", min_chars_uteis=300),
    # DRE search — min baixo porque a página de resultados pode ter pouco texto extraível
    "dre_psu": FonteConfig(nome="DRE — Pesquisa PSU decreto-lei", min_chars_uteis=50),
}


def _fonte_config(slug: str) -> FonteConfig:
    return _FONTE_CONFIGS.get(slug, FonteConfig(nome=slug))


# Perfil de browser por fonte — omissão = comportamento de produção
# inalterado (stealth + headers custom + viewport fixo, como sempre foi).
# Só fontes com uma entrada em _PERFIL_POR_SLUG abrem um browser context
# à parte, com um perfil diferente — usado para isolar qual componente
# do contexto Playwright está a despoletar um redirect/bloqueio numa
# fonte específica (ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
@dataclass(frozen=True)
class PerfilBrowser:
    stealth: bool = True
    headers_custom: bool = True
    viewport_fixo: bool = True


# seg_social_abono/rsi: diagnóstico num runner real (2026-07-03, 4 perfis
# x 2 deep-links) isolou extra_http_headers como o único componente que
# faz o deep-link cair — não num simples redirect de login, mas num erro
# 500 real do backend (/ptss/fraw/errors/500?dswid=...). stealth e
# viewport fixo passaram isoladamente sem problema, tal como "nu" — só
# headers_custom=True falhou nos 2 alvos. Ver CLAUDE.md "SEG-SOCIAL —
# ESTRATÉGIA DE FETCH".
_PERFIL_POR_SLUG: dict[str, PerfilBrowser] = {
    "seg_social_abono": PerfilBrowser(headers_custom=False),
    "seg_social_rsi": PerfilBrowser(headers_custom=False),
}


def _perfil_fonte(slug: str) -> PerfilBrowser:
    return _PERFIL_POR_SLUG.get(slug, PerfilBrowser())


def _criar_context(browser, perfil: PerfilBrowser):
    kwargs = dict(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        locale="pt-PT",
        timezone_id="Europe/Lisbon",
    )
    if perfil.headers_custom:
        kwargs["extra_http_headers"] = {
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    if perfil.viewport_fixo:
        kwargs["viewport"] = {"width": 1280, "height": 900}

    context = browser.new_context(**kwargs)
    if perfil.stealth:
        from playwright_stealth import Stealth
        Stealth().apply_stealth_sync(context)
    return context

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
        # URL plana redirecciona sempre para o gateway de autenticação
        # (confirmado num runner real, com e sem Playwright) — usa-se o
        # deep-link do portal novo, que serve o conteúdo real sem sessão
        # desde que se espere pela âncora renderizada (ver _obter_html).
        "slug": "seg_social_abono",
        "url": "https://www.seg-social.pt/ptss/pssd/menu/familia/desenvolvimento-criancas-jovens/abono-familia-criancas-jovens",
        "titulo_js": True,
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
            "tabelas": "table",
        },
    },
    {
        "slug": "seg_social_rsi",
        "url": "https://www.seg-social.pt/ptss/pssd/menu/acao-social/apoios-respostas-sociais/rendimento-social-insercao",
        "titulo_js": True,
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
    # metodo="http" (ver _FONTE_CONFIGS) — página real acessível via
    # pedido simples, confirmado num runner real; sem url_fallback porque
    # scrape_http() não tem lógica de fallback própria.
    {
        "slug": "iefp_desemprego",
        "url": "https://www.iefp.pt/subsidio-desemprego",
        "nota": "IEFP recebe pedido; decisão e pagamento são da Segurança Social",
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
    {
        "slug": "dre_psu",
        # Pesquisa DRE por "prestação social única" — detectar publicação do decreto-lei.
        # A lei de autorização legislativa (Jun 2026) está publicada; queremos o DECRETO-LEI
        # que regulamenta valores e procedimentos (prazo PRR: 31 ago 2026).
        "url": "https://dre.pt/pesquisa?q=presta%C3%A7%C3%A3o+social+%C3%BAnica",
        "nota": "DRE — vigiar publicação do decreto-lei da PSU (prazo PRR: 31 ago 2026)",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li, .result-title, .resultado, h2, h3",
            "links": "a[href]",
        },
        "detectar_decreto_lei_psu": True,
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


# Só se marca BLOQUEADO no dia se estas 3 tentativas (Camada 1: recepção +
# classificação, não apenas o goto de rede) falharem todas — bloqueios de
# gov.pt a runners do GitHub são frequentemente transitórios. Espera aleatória
# entre tentativas para não bater sempre no mesmo padrão temporal.
TENTATIVAS_BLOQUEIO = 3
ESPERA_MIN_S = 30
ESPERA_MAX_S = 120


def _obter_html(page, url: str, url_fallback: str | None, slug: str,
                 ancora: str | None = None) -> tuple[str, str] | None:
    """Navega para `url` (com fallback opcional) e devolve `(url_usado,
    html)`. Devolve None só em falha de navegação (rede/timeout) —
    distinto de "conteúdo bloqueado", decidido a jusante pela Camada 1.

    Com `ancora` (fonte com verificação positiva configurada — ver
    ancora_conteudo em FonteConfig): espera explicitamente que a frase
    apareça no DOM em vez de confiar em `networkidle` + sleep fixo — o
    portal novo seg-social.pt/ptss/pssd é uma SPA que reporta "carregada"
    antes do conteúdo real renderizar."""
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

    if ancora:
        try:
            page.wait_for_function(
                "text => document.body && document.body.innerText.toLowerCase().includes(text)",
                arg=ancora.lower(),
                timeout=15_000,
            )
        except Exception as exc:
            log.warning("%s: âncora %r não apareceu no DOM em 15s: %s", slug, ancora, exc)
    else:
        time.sleep(5)

    return url_usado, page.content()


def scrape_playwright(page, fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    url_fallback = fonte.get("url_fallback")
    nota = fonte.get("nota", "")
    log.info("A scrape (Playwright): %s", url)

    config = _fonte_config(slug)
    ancora = config.ancora_conteudo[0] if config.ancora_conteudo else None
    url_usado, html, classif = url, "", None

    for tentativa in range(1, TENTATIVAS_BLOQUEIO + 1):
        obtido = _obter_html(page, url, url_fallback, slug, ancora=ancora)
        if obtido is None:
            # Falha de navegação (rede/timeout), não de conteúdo bloqueado —
            # já esgotou as suas próprias 3 tentativas dentro de _tentar_goto,
            # sem sentido voltar a tentar aqui.
            return None

        url_usado, html = obtido
        classif = classificar_resposta(status_code=200, corpo=html, url_final=page.url, config=config)

        if classif.estado == Estado.OK:
            break

        log.warning("%s: tentativa %d/%d classificada como %s — motivos: %s",
                    slug, tentativa, TENTATIVAS_BLOQUEIO, classif.estado.value, classif.motivos)
        if tentativa < TENTATIVAS_BLOQUEIO:
            espera = random.uniform(ESPERA_MIN_S, ESPERA_MAX_S)
            log.info("%s: a aguardar %.0fs antes da próxima tentativa", slug, espera)
            time.sleep(espera)

    if classif.estado != Estado.OK:
        return _tratar_nao_ok(slug, url_usado, fonte["seletores"], nota, classif)

    _limpar_bloqueio_hoje(slug)
    conteudo = _extrair_conteudo(html, fonte["seletores"])

    if fonte.get("titulo_js"):
        try:
            titulo_js = page.evaluate(
                "document.querySelector('h1')?.innerText || "
                "document.querySelector('.page-title')?.innerText || "
                "document.title || ''"
            )
            if titulo_js and titulo_js.strip():
                conteudo["titulo"] = titulo_js.strip()
                log.info("%s: título via JS: %s", slug, conteudo["titulo"][:80])
        except Exception as exc:
            log.warning("%s: page.evaluate título falhou: %s", slug, exc)

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

    # Detectar ano lectivo novo e datas MEGA (ex: MEGA 2026/2027)
    ano_detectar = fonte.get("detectar_ano")
    if ano_detectar and slug == "mega_datas":
        import re as _re
        html_lower = html.lower()
        ano_confirmado = ano_detectar in html
        datas_confirmadas = bool(
            _re.search(r"\b(julho|agosto)\b.*\b2026\b", html_lower) or
            _re.search(r"\b2026\b.*\b(julho|agosto)\b", html_lower) or
            _re.search(r"\b\d{1,2}\s+de\s+(julho|agosto)\b", html_lower)
        )
        if ano_confirmado:
            _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
            log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)
        if datas_confirmadas:
            # Extrair excertos relevantes para facilitar actualização manual
            excertos = []
            for p in conteudo.get("paragrafos", []) + conteudo.get("itens_lista", []):
                if any(kw in p.lower() for kw in ["julho", "agosto", "voucher", "vale"]):
                    excertos.append(p[:200])
            excertos_txt = "\n".join(f"- {e}" for e in excertos[:5]) or "(sem excertos — ver scrape JSON)"
            _registar_aviso(slug, f"mega_datas_publicadas:2026/2027:{excertos_txt[:300]}")
            log.warning(
                "%s: DATAS MEGA 2026/2027 DETECTADAS — actualizar manuais-escolares-mega.html!\n%s",
                slug, excertos_txt
            )
    elif ano_detectar and ano_detectar in html:
        _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
        log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)

    # Detecção do decreto-lei da PSU em DRE
    if fonte.get("detectar_decreto_lei_psu") and slug == "dre_psu":
        import re as _re
        # Juntar todo o texto extraído para pesquisa
        todo_texto = " ".join([
            conteudo.get("titulo", ""),
            *conteudo.get("paragrafos", []),
            *conteudo.get("itens_lista", []),
            *[lnk.get("texto", "") for lnk in conteudo.get("links_uteis", [])],
        ])
        todo_lower = todo_texto.lower()

        # Detectar DECRETO-LEI (não "Lei" — a lei de autorização já foi publicada)
        # O decreto-lei terá "decreto-lei n.º" e "prestação social única" no mesmo documento
        decreto_psu = bool(
            _re.search(r"decreto.lei\b.*\bpresta", todo_lower) or
            _re.search(r"presta[çc][aã]o\s+social\s+[uú]nica.*decreto.lei\b", todo_lower)
        )

        if decreto_psu:
            excertos = []
            for item in conteudo.get("paragrafos", []) + conteudo.get("itens_lista", []):
                if "decreto" in item.lower() and "prest" in item.lower():
                    excertos.append(item[:300])
            excertos_txt = "\n".join(f"- {e}" for e in excertos[:5]) or "(ver data/scraped/dre_psu_latest.json)"
            _registar_aviso(slug, f"dre_psu_decreto_detectado:{excertos_txt[:500]}")
            log.warning(
                "%s: DECRETO-LEI PSU DETECTADO EM DRE — rever cluster e publicar valores!\n%s",
                slug, excertos_txt
            )
        else:
            log.info("%s: decreto-lei PSU ainda não publicado em DRE (só lei de autorização)", slug)

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


def _registar_bloqueio(slug: str, url: str, classif) -> None:
    """Acrescenta entrada a data/bloqueios.json (lida pelo pipeline para abrir Issue)."""
    entrada = {
        "slug": slug,
        "url": url,
        "data": datetime.now(timezone.utc).isoformat(),
        "motivos": classif.motivos,
        "chars_uteis": classif.chars_uteis,
    }
    bloqueios: list = []
    if BLOQUEIOS_PATH.exists():
        try:
            bloqueios = json.loads(BLOQUEIOS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Substituir entrada anterior do mesmo slug para o mesmo dia
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bloqueios = [b for b in bloqueios if not (b["slug"] == slug and b["data"][:10] == hoje)]
    bloqueios.append(entrada)
    BLOQUEIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOQUEIOS_PATH.write_text(json.dumps(bloqueios, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Bloqueio registado: %s → %s", slug, BLOQUEIOS_PATH)


def _limpar_bloqueio_hoje(slug: str) -> None:
    """Remove qualquer entrada de hoje desta fonte em data/bloqueios.json
    quando ela recupera (OK). Sem isto, uma fonte bloqueada numa corrida
    e recuperada numa corrida seguinte no mesmo dia (ex.: workflow_dispatch
    manual repetido) ficava presa em BLOQUEADO na máquina de estados de
    gerir_estado_fontes.py até ao dia seguinte -- _registar_bloqueio já
    substituía a entrada de hoje ao registar um NOVO bloqueio, mas nada
    a removia quando a fonte simplesmente recuperava. Descoberto e
    corrigido em 2026-07-03 (ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE
    FETCH")."""
    if not BLOQUEIOS_PATH.exists():
        return
    try:
        bloqueios = json.loads(BLOQUEIOS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    novo = [b for b in bloqueios if not (b.get("slug") == slug and b.get("data", "")[:10] == hoje)]
    if len(novo) != len(bloqueios):
        BLOQUEIOS_PATH.write_text(json.dumps(novo, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("%s: bloqueio de hoje removido (fonte recuperou)", slug)


def _registar_mudanca_estrutural(slug: str, url: str, classif) -> None:
    """MUDOU: a fonte respondeu (sem sinais reais de bloqueio) mas o
    conteúdo esperado (ancora_conteudo) desapareceu — revisão manual,
    nunca disfarçado de BLOQUEADO. Nunca escreve em data/bloqueios.json:
    não é o mesmo que um dia bloqueado na máquina de estados de
    gerir_estado_fontes.py. Criação de Issue dedicada para este caso
    ainda não implementada — ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE
    FETCH" (registado para o futuro)."""
    _registar_aviso(slug, f"mudanca_estrutural:motivos={classif.motivos}:chars_uteis={classif.chars_uteis}")


def _tratar_nao_ok(slug: str, url_usado: str, seletores: dict, nota: str, classif) -> dict | None:
    """Ponto único chamado depois de esgotar TENTATIVAS_BLOQUEIO sem OK.
    MUDOU nunca tenta o fallback Wayback (a fonte respondeu — só o
    conteúdo esperado desapareceu) nem conta como bloqueio; BLOQUEADO
    segue o caminho já existente (Wayback, depois bloqueios.json)."""
    if classif.estado == Estado.MUDOU:
        log.warning("%s: MUDOU após %d tentativas — motivos: %s", slug, TENTATIVAS_BLOQUEIO, classif.motivos)
        _registar_mudanca_estrutural(slug, url_usado, classif)
        return None

    log.warning("%s: BLOQUEADO após %d tentativas — motivos: %s", slug, TENTATIVAS_BLOQUEIO, classif.motivos)
    resultado_arquivo = _tentar_fallback_wayback(slug, url_usado, seletores, nota)
    if resultado_arquivo is not None:
        return resultado_arquivo
    _registar_bloqueio(slug, url_usado, classif)
    return None


def _fetch_json_wayback(url_completo: str) -> dict:
    resp = requests.get(url_completo, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _tentar_fallback_wayback(slug: str, url: str, seletores: dict, nota: str) -> dict | None:
    """Só chamado depois de TENTATIVAS_BLOQUEIO tentativas directas
    falharem. Devolve um resultado com `status: "ok_via_arquivo"` se
    existir snapshot Wayback recente (`wayback_fallback.decidir_estado_apos_bloqueio`),
    ou None se não houver — o chamador trata então como BLOQUEADO normal.
    Nunca escreve em `data/bloqueios.json`: modo arquivo não é a mesma
    coisa que bloqueado, e não deve contar como dia bloqueado na máquina
    de estados de fontes (`gerir_estado_fontes.py`)."""
    decisao = decidir_estado_apos_bloqueio(url, fetch_json=_fetch_json_wayback)
    if decisao["estado"] != "OK_VIA_ARQUIVO":
        # Sem isto, "sem snapshot recente" e "consulta ao Wayback nunca
        # sequer tentada" ficam indistinguíveis no log.
        log.info("%s: sem snapshot Wayback recente disponível — a manter BLOQUEADO", slug)
        return None

    snapshot = decisao["snapshot"]
    try:
        resp = requests.get(snapshot["url"], timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("%s: snapshot Wayback encontrado mas falhou a obter conteúdo: %s", slug, exc)
        return None

    conteudo = _extrair_conteudo(resp.text, seletores)
    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado = {
        "url": url,
        "url_original": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok_via_arquivo",
        "modo": "arquivo",
        "data_snapshot": snapshot["timestamp"],
        "url_snapshot": snapshot["url"],
        "conteudo_extraido": conteudo,
        "hash_conteudo": hashlib.sha256(hash_payload.encode()).hexdigest(),
    }
    if nota:
        resultado["nota"] = nota

    log.warning(
        "%s: modo degradado OK_VIA_ARQUIVO — snapshot de %s (%s dia(s) atrás)",
        slug, snapshot["timestamp"], snapshot["dias_desde_snapshot"],
    )
    _registar_aviso(slug, f"modo_arquivo:snapshot={snapshot['timestamp']}:dias={snapshot['dias_desde_snapshot']}")
    _guardar_resultado(slug, resultado)
    return resultado


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


# ── Fontes via HTTP simples (sem browser) ───────────────────────────────────────
# Para fontes cuja página real é acessível com um pedido simples (ver
# CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH": confirmado num runner real
# para iefp_desemprego) — mais rápido e sem depender do Chromium.
_HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_http(fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    nota = fonte.get("nota", "")
    log.info("A scrape (http): %s", url)

    config = _fonte_config(slug)
    classif = None
    resp = None

    for tentativa in range(1, TENTATIVAS_BLOQUEIO + 1):
        try:
            resp = requests.get(url, headers=_HEADERS_HTTP, timeout=30)
        except Exception as exc:
            log.warning("%s: erro de rede na tentativa %d/%d: %s", slug, tentativa, TENTATIVAS_BLOQUEIO, exc)
            classif = None
            if tentativa < TENTATIVAS_BLOQUEIO:
                time.sleep(random.uniform(ESPERA_MIN_S, ESPERA_MAX_S))
            continue

        classif = classificar_resposta(
            status_code=resp.status_code, corpo=resp.text, url_final=str(resp.url), config=config,
        )
        if classif.estado == Estado.OK:
            break

        log.warning("%s: tentativa %d/%d classificada como %s — motivos: %s",
                    slug, tentativa, TENTATIVAS_BLOQUEIO, classif.estado.value, classif.motivos)
        if tentativa < TENTATIVAS_BLOQUEIO:
            espera = random.uniform(ESPERA_MIN_S, ESPERA_MAX_S)
            log.info("%s: a aguardar %.0fs antes da próxima tentativa", slug, espera)
            time.sleep(espera)

    if classif is None:
        log.error("%s: falhou todas as %d tentativas por erro de rede", slug, TENTATIVAS_BLOQUEIO)
        return None

    if classif.estado != Estado.OK:
        return _tratar_nao_ok(slug, url, fonte["seletores"], nota, classif)

    _limpar_bloqueio_hoje(slug)
    conteudo = _extrair_conteudo(resp.text, fonte["seletores"])
    resultado = {
        "url": url,
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
    return resultado


# ── Main ───────────────────────────────────────────────────────────────────────

def _reportar_resultado(resultados: dict, slug: str, r: dict | None) -> None:
    if r:
        resultados[slug] = r.get("status", "ok")
        c = r.get("conteudo_extraido", {})
        if r.get("status") == "ok_via_arquivo":
            print(f"⚠ OK_VIA_ARQUIVO — snapshot de {r.get('data_snapshot')}")
        else:
            print(f"✓ OK — título: {c.get('titulo', '')[:80]}")
        print(f"  hash: {r.get('hash_conteudo', '')[:16]}…")
    else:
        resultados[slug] = "falhou"
        print("✗ Falhou")


def main(mode: str = "scrape"):
    from playwright.sync_api import sync_playwright

    resultados = {}

    fontes_http = [f for f in FONTES_PLAYWRIGHT if _fonte_config(f["slug"]).metodo == "http"]
    fontes_pw = [f for f in FONTES_PLAYWRIGHT if _fonte_config(f["slug"]).metodo != "http"]

    # ── HTTP simples (sem browser) ───────────────────────────────────────────
    for fonte in fontes_http:
        print(f"\n{'='*60}")
        print(f"[HTTP] {fonte['slug']} — {fonte['url']}")
        print("=" * 60)
        try:
            r = scrape_http(fonte)
            _reportar_resultado(resultados, fonte["slug"], r)
        except Exception as exc:
            resultados[fonte["slug"]] = f"erro: {exc}"
            log.exception("Erro inesperado em %s", fonte["slug"])
            print(f"✗ Erro: {exc}")

    # ── Playwright ────────────────────────────────────────────────────────────
    # Agrupadas por perfil de browser (_perfil_fonte) — por omissão todas
    # partilham o mesmo perfil de sempre (um único context, como antes
    # desta secção); só uma fonte com entrada em _PERFIL_POR_SLUG abre um
    # context à parte, com um perfil diferente.
    grupos: dict[PerfilBrowser, list[dict]] = {}
    for fonte in fontes_pw:
        perfil = _perfil_fonte(fonte["slug"])
        grupos.setdefault(perfil, []).append(fonte)

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

        for perfil, fontes_grupo in grupos.items():
            context = _criar_context(browser, perfil)
            page = context.new_page()

            for fonte in fontes_grupo:
                print(f"\n{'='*60}")
                print(f"[Playwright] {fonte['slug']} — {fonte['url']} (perfil={perfil})")
                print("=" * 60)
                try:
                    r = scrape_playwright(page, fonte)
                    _reportar_resultado(resultados, fonte["slug"], r)
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
    icones = {"ok": "✓", "ok_via_arquivo": "⚠"}
    for slug, estado in resultados.items():
        icone = icones.get(estado, "✗")
        print(f"  {icone} {slug}: {estado}")

    ok = sum(1 for v in resultados.values() if v in ("ok", "ok_via_arquivo"))
    print(f"\n{ok}/{len(resultados)} fontes scraped com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="scrape", choices=["scrape", "detect"])
    args = parser.parse_args()
    main(args.mode)
