"""
Testes para scripts/classificador_resposta.py — Camada 1 de classificação.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from classificador_resposta import (
    FonteConfig, Estado, classificar_resposta, avaliar_fonte,
)

# Config reutilizável
CFG_SEG = FonteConfig(
    nome="Seg. Social — teste",
    min_chars_uteis=500,
    dominios_login=("app.seg-social.pt",),
)
CFG_DGE = FonteConfig(nome="DGE — teste", min_chars_uteis=300)
CFG_GERAL = FonteConfig(nome="Geral", min_chars_uteis=500)

HTML_REAL = "<html><body>" + ("conteúdo real " * 100) + "</body></html>"  # ~1400 chars úteis


def _c(**kw):
    defaults = dict(status_code=200, corpo="", url_final="https://example.pt", config=CFG_GERAL)
    defaults.update(kw)
    return classificar_resposta(**defaults)


# ── DRE bloqueado (0 chars) ────────────────────────────────────────────────────
def test_dre_zero_chars_bloqueado():
    c = _c(corpo="", config=CFG_DGE)
    assert c.bloqueado
    assert c.hash is None
    assert any("texto_util" in m for m in c.motivos)


def test_dre_html_minimo_bloqueado():
    c = _c(corpo="<html></html>", config=CFG_DGE)
    assert c.bloqueado
    assert c.hash is None


# ── Seg-social: página de login ────────────────────────────────────────────────
def test_seg_social_titulo_login_bloqueado():
    html = "<html><head><title>Segurança Social Direta</title></head><body>login</body></html>"
    c = _c(corpo=html, config=CFG_SEG)
    assert c.bloqueado
    assert c.hash is None
    assert any("titulo_login" in m for m in c.motivos)


def test_seg_social_redirect_login_bloqueado():
    html = "<html><body>" + ("x " * 300) + "</body></html>"
    c = classificar_resposta(
        status_code=200,
        corpo=html,
        url_final="https://app.seg-social.pt/ptss/ssd",
        config=CFG_SEG,
    )
    assert c.bloqueado
    assert any("redirect_login" in m for m in c.motivos)


# ── Status HTTP de bloqueio ────────────────────────────────────────────────────
def test_status_403_bloqueado():
    c = _c(status_code=403, corpo=HTML_REAL)
    assert c.bloqueado
    assert any("status_http=403" in m for m in c.motivos)


def test_status_429_bloqueado():
    c = _c(status_code=429, corpo=HTML_REAL)
    assert c.bloqueado
    assert any("status_http=429" in m for m in c.motivos)


# ── Cloudflare challenge ───────────────────────────────────────────────────────
def test_cloudflare_just_a_moment_bloqueado():
    html = "<html><body>Just a moment... Checking your browser</body></html>"
    c = _c(corpo=html)
    assert c.bloqueado
    assert any("desafio" in m for m in c.motivos)


def test_cloudflare_cf_chl_bloqueado():
    html = "<html><body>cf-chl-bypass</body></html>"
    c = _c(corpo=html)
    assert c.bloqueado


# ── Página real: OK com hash ───────────────────────────────────────────────────
def test_pagina_real_ok_com_hash():
    c = _c(corpo=HTML_REAL, config=CFG_DGE)
    assert not c.bloqueado
    assert c.estado == Estado.OK
    assert c.hash is not None
    assert len(c.hash) == 64  # sha256 hex


# ── Hash igual: OK (sem mudança) ───────────────────────────────────────────────
def test_mesmo_hash_ok():
    c1 = _c(corpo=HTML_REAL, config=CFG_DGE)
    c2 = avaliar_fonte(
        status_code=200, corpo=HTML_REAL, url_final="https://example.pt",
        config=CFG_DGE, hash_anterior=c1.hash,
    )
    assert c2.estado == Estado.OK


# ── Hash diferente: MUDOU ──────────────────────────────────────────────────────
def test_hash_diferente_mudou():
    html2 = HTML_REAL.replace("conteúdo real", "conteúdo alterado")
    c1 = _c(corpo=HTML_REAL, config=CFG_DGE)
    c2 = avaliar_fonte(
        status_code=200, corpo=html2, url_final="https://example.pt",
        config=CFG_DGE, hash_anterior=c1.hash,
    )
    assert c2.estado == Estado.MUDOU


# ── Bloqueio com hash_anterior: continua BLOQUEADO (nunca MUDOU) ───────────────
def test_bloqueio_com_hash_anterior_nao_muda():
    html_login = "<html><head><title>Segurança Social Direta</title></head><body></body></html>"
    c = avaliar_fonte(
        status_code=200,
        corpo=html_login,
        url_final="https://www.seg-social.pt/login",
        config=CFG_SEG,
        hash_anterior="hash_qualquer_anterior",
    )
    assert c.bloqueado
    assert c.estado == Estado.BLOQUEADO
    assert c.estado != Estado.MUDOU


if __name__ == "__main__":
    import traceback
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for fn in testes:
        try:
            fn()
            print(f"  ✓ {fn.__name__}")
        except Exception:
            print(f"  ✗ {fn.__name__}")
            traceback.print_exc()
            falhas += 1
    print(f"\n{len(testes) - falhas}/{len(testes)} passed")
    sys.exit(falhas)
