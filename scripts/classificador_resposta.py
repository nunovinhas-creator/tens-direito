"""
CAMADA 1 — Classificacao de resposta (TENS DIREITO, scraping resiliente).
Distingue "recebi a PAGINA" de "recebi o SEGURANCA A PORTA" ANTES de calcular
hash. Regra de ouro: QUALQUER sinal de bloqueio -> BLOQUEADO.
"""
from __future__ import annotations
import hashlib, re, unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Estado(str, Enum):
    OK = "OK"
    BLOQUEADO = "BLOQUEADO"
    MUDOU = "MUDOU"


_MARCADORES_DESAFIO = (
    "just a moment", "checking your browser", "cloudflare", "cf-chl",
    "__cf_chl", "turnstile", "g-recaptcha", "recaptcha", "attention required",
    "enable javascript and cookies", "please verify you are a human",
)
_STATUS_BLOQUEIO = {401, 403, 407, 429, 503}


@dataclass(frozen=True)
class FonteConfig:
    nome: str
    min_chars_uteis: int = 500
    dominios_login: tuple = ()
    titulos_bloqueio: tuple = (
        "login", "iniciar sessao", "seguranca social direta",
        "autenticacao", "acesso restrito",
    )


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


def classificar_resposta(*, status_code, corpo, url_final, config, headers=None):
    motivos, corpo = [], corpo or ""
    if status_code in _STATUS_BLOQUEIO:
        motivos.append(f"status_http={status_code}")
    url_norm = _normalizar(url_final)
    for dom in config.dominios_login:
        if dom and _normalizar(dom) in url_norm:
            motivos.append(f"redirect_login:{dom}"); break
    corpo_norm = _normalizar(corpo)
    for m in _MARCADORES_DESAFIO:
        if m in corpo_norm:
            motivos.append(f"desafio:{m}"); break
    titulo_norm = _normalizar(_titulo(corpo))
    if titulo_norm:
        for f in config.titulos_bloqueio:
            if _normalizar(f) in titulo_norm:
                motivos.append(f"titulo_login:{f}"); break
    util = texto_util(corpo); n = len(util)
    if n < config.min_chars_uteis:
        motivos.append(f"texto_util={n}<min={config.min_chars_uteis}")
    if motivos:
        return Classificacao(Estado.BLOQUEADO, motivos, n)
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
