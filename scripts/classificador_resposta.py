"""
CAMADA 1 — Classificacao de resposta (TENS DIREITO, scraping resiliente).
Distingue "recebi a PAGINA" de "recebi o SEGURANCA A PORTA" ANTES de calcular
hash.

Verificacao positiva primeiro (2026-07-03, corrige o falso positivo
confirmado em iefp_desemprego): uma pagina com as ancoras de conteudo
configuradas e tamanho suficiente e OK de imediato, independentemente de
substrings tipo "recaptcha" aparecerem num <script> passivo qualquer no
resto da pagina -- um script incluido nao e um desafio activo. Sem essa
confirmacao positiva, so ha BLOQUEADO com um sinal REAL (status HTTP de
bloqueio, redirect/titulo de login, ou um marcador de desafio forte numa
pagina pequena); sem nenhum sinal real e sem as ancoras esperadas, o
resultado e MUDOU -- a fonte respondeu mas o conteudo mudou de forma
inesperada, nunca disfarcado de BLOQUEADO.
"""
from __future__ import annotations
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Estado(str, Enum):
    OK = "OK"
    BLOQUEADO = "BLOQUEADO"
    MUDOU = "MUDOU"


# Sinais de desafio ACTIVO -- widgets/interstitials que só aparecem quando
# um desafio está mesmo a ser apresentado. Deliberadamente SEM "recaptcha"
# nem "cloudflare" soltos: um <script src=".../recaptcha/api.js"> ou um
# CDN Cloudflare aparecem passivamente em páginas totalmente normais (caso
# real: iefp.pt inclui sempre esse script, sem nenhum desafio a bloquear
# conteúdo) — só contam combinados com página pequena (ver LIMIAR_TAMANHO_PEQUENO).
_MARCADORES_DESAFIO_FORTE = (
    "just a moment", "checking your browser", "cf-chl", "__cf_chl",
    "turnstile", "g-recaptcha", "grecaptcha.execute", "hcaptcha",
    "captcha-container", "challenge-container", "attention required",
    "enable javascript and cookies", "please verify you are a human",
)
_STATUS_BLOQUEIO = {401, 403, 407, 429, 503}

# "Página < 15KB" (spec da Fase de correcção do classificador): abaixo
# disto, um marcador de desafio forte é tratado como sinal real; acima,
# é tratado como ruído passivo (script incluído, não desafio activo).
LIMIAR_TAMANHO_PEQUENO = 15_000


@dataclass(frozen=True)
class FonteConfig:
    nome: str
    min_chars_uteis: int = 500
    dominios_login: tuple = ()
    titulos_bloqueio: tuple = (
        "login", "iniciar sessao", "seguranca social direta",
        "autenticacao", "acesso restrito",
    )
    # Frases que uma página legítima desta fonte tem SEMPRE — 2-3 no
    # máximo, escolhidas por serem específicas ao conteúdo real (não a
    # navegação/rodapé genéricos do site). Vazio por omissão: fontes sem
    # âncoras configuradas mantêm o comportamento anterior a esta secção
    # (nunca ficam MUDOU por omissão — só as fontes migradas para este
    # sistema, ver CLAUDE.md "CLASSIFICADOR — VERIFICAÇÃO POSITIVA").
    ancora_conteudo: tuple = ()
    # "http" (requests/urllib simples) ou "playwright" — usado por
    # scraper_playwright.py para decidir a estratégia de obtenção por
    # fonte (ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
    metodo: str = "playwright"


@dataclass
class Classificacao:
    estado: Estado
    motivos: list = field(default_factory=list)
    chars_uteis: int = 0
    hash: Optional[str] = None
    @property
    def bloqueado(self) -> bool:
        return self.estado == Estado.BLOQUEADO


def _normalizar(t: str) -> str:
    t = (t or "").lower()
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def texto_util(html: str) -> str:
    if not html:
        return ""
    s = _SCRIPT_STYLE_RE.sub(" ", html)
    s = _TAG_RE.sub(" ", s)
    return _WS_RE.sub(" ", s).strip()


def _titulo(html: str) -> str:
    m = _TITLE_RE.search(html or "")
    return m.group(1).strip() if m else ""


def _ancoras_presentes(config: FonteConfig, util_norm: str) -> bool:
    if not config.ancora_conteudo:
        return False
    return all(_normalizar(a) in util_norm for a in config.ancora_conteudo)


def classificar_resposta(*, status_code, corpo, url_final, config, headers=None):
    corpo = corpo or ""
    util = texto_util(corpo)
    n = len(util)
    util_norm = _normalizar(util)

    # Status HTTP de bloqueio é sempre um sinal real — nem o corpo parecer
    # ter as âncoras certas o sobrepõe (um WAF pode devolver uma página de
    # erro com texto coincidente).
    if status_code in _STATUS_BLOQUEIO:
        return Classificacao(Estado.BLOQUEADO, [f"status_http={status_code}"], n)

    # 1) Verificação positiva primeiro: âncoras todas presentes + tamanho
    # suficiente -> OK de imediato, independentemente de qualquer outro
    # marcador (recaptcha passivo incluído) no resto da página.
    if _ancoras_presentes(config, util_norm) and n >= config.min_chars_uteis:
        h = hashlib.sha256(corpo.encode("utf-8")).hexdigest()
        return Classificacao(Estado.OK, [], n, h)

    # 2) Sem confirmação positiva: só BLOQUEADO com sinais reais.
    motivos = []

    url_norm = _normalizar(url_final)
    for dom in config.dominios_login:
        if dom and _normalizar(dom) in url_norm:
            motivos.append(f"redirect_login:{dom}")
            break

    titulo_norm = _normalizar(_titulo(corpo))
    tem_titulo_login = False
    if titulo_norm:
        for f in config.titulos_bloqueio:
            if _normalizar(f) in titulo_norm:
                motivos.append(f"titulo_login:{f}")
                tem_titulo_login = True
                break

    if n < config.min_chars_uteis:
        motivos.append(f"texto_util={n}<min={config.min_chars_uteis}")

    # Marcador de desafio forte só conta como sinal real numa página
    # pequena (ou já com título de login) — nessas condições um recaptcha
    # de facto costuma ser um desafio activo, não um script incluído à
    # toa numa página de dezenas de KB de conteúdo real.
    if len(corpo) < LIMIAR_TAMANHO_PEQUENO or tem_titulo_login:
        corpo_norm = _normalizar(corpo)
        for m in _MARCADORES_DESAFIO_FORTE:
            if m in corpo_norm:
                motivos.append(f"desafio:{m}")
                break

    if motivos:
        return Classificacao(Estado.BLOQUEADO, motivos, n)

    # 3) Sem sinais reais de bloqueio. Se a fonte tem âncoras configuradas
    # mas não foram encontradas, o conteúdo esperado desapareceu — MUDOU,
    # nunca disfarçado de BLOQUEADO. Fontes sem âncoras configuradas
    # mantêm o comportamento anterior (OK).
    if config.ancora_conteudo:
        return Classificacao(Estado.MUDOU, ["ancoras_nao_encontradas"], n)

    h = hashlib.sha256(corpo.encode("utf-8")).hexdigest()
    return Classificacao(Estado.OK, [], n, h)


def avaliar_fonte(*, status_code, corpo, url_final, config,
                  hash_anterior=None, headers=None):
    c = classificar_resposta(status_code=status_code, corpo=corpo,
                             url_final=url_final, config=config, headers=headers)
    if c.bloqueado:
        return c
    if hash_anterior is not None and c.hash != hash_anterior:
        c.estado = Estado.MUDOU
    return c


def de_requests(r, *, config, hash_anterior=None):
    return avaliar_fonte(status_code=r.status_code, corpo=r.text,
                         url_final=str(r.url), config=config,
                         hash_anterior=hash_anterior, headers=dict(r.headers))


def de_playwright(resp, corpo_html, *, config, hash_anterior=None):
    return avaliar_fonte(status_code=resp.status, corpo=corpo_html,
                         url_final=resp.url, config=config,
                         hash_anterior=hash_anterior, headers=dict(resp.headers))


def issue_bloqueio(config, c):
    titulo = f"⚠️ Scraper BLOQUEADO em {config.nome} — verificacao automatica cega"
    corpo = (
        f"O scraper nao recebeu a pagina real de **{config.nome}**. "
        f"Classificado como BLOQUEADO (nao mudanca de conteudo).\n\n"
        f"**Sinais:**\n" + "".join(f"- `{m}`\n" for m in c.motivos)
        + f"\n**Texto util:** {c.chars_uteis} chars\n\n"
        f"**Acao:** confirmar o valor manualmente na fonte oficial. O site mantem "
        f"o ultimo `last_verified_by_human`. NAO publicar valor nao confirmado.\n\n"
        f"_Estamos cegos a esta fonte — isto NAO significa que ela mudou._"
    )
    return titulo, corpo
