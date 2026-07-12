"""
Canário de frescura do calendário de pagamentos — o coração do
invariante de CALENDARIO-PAGAMENTOS-SPEC.md: a página publicada NUNCA
pode mostrar um mês passado como se fosse o corrente, e nenhum estado
de erro pode parecer sucesso (ver CLAUDE.md "INVARIANTE").

FALHAR AQUI É O COMPORTAMENTO DESEJADO quando o mês vira sem o
calendário ter sido actualizado (workflow mensal da Fase 3 falhado, ou
Fase 3 ainda por implementar) — CI vermelho força a actualização, em
vez de deixar datas velhas em produção em silêncio.

Cobre o invariante completo da Fase 4: canário de frescura,
idempotência, estado degradado, caminhos de falha da validação, e os
testes Playwright mobile (375px sem overflow, âncoras por prestação,
guarda JS de mês velho — com Chromium real, nunca file://).
"""
from __future__ import annotations

import datetime as dt
import functools
import glob
import http.server
import os
import re
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from atualizar_calendario import (  # noqa: E402
    PAGINA,
    atualizar_pagina,
    carregar_dados,
    hoje_lisboa,
    render_corpo,
    render_meta,
    validar_dados,
)

HTML = PAGINA.read_text(encoding="utf-8")


# ── canário de frescura (o invariante) ─────────────────────────────────────


def _mes_renderizado() -> str | None:
    """Valor de data-mes em #cal-corrente ('' = estado degradado explícito)."""
    m = re.search(r'id="cal-corrente" data-mes="(\d{4}-\d{2}|)"', HTML)
    return m.group(1) if m else None


def test_canario_pagina_nunca_mostra_mes_passado_como_corrente():
    mes = _mes_renderizado()
    assert mes is not None, (
        "não encontrei #cal-corrente[data-mes] na página — a zona CAL:CORPO "
        "foi apagada ou o formato mudou sem actualizar este canário"
    )
    if mes == "":
        # Estado degradado: honesto e explícito por construção, nunca falha.
        assert "cal-degradado" in HTML
        return
    hoje = hoje_lisboa()
    corrente = f"{hoje.year}-{hoje.month:02d}"
    assert mes >= corrente, (
        f"A página mostra {mes} como mês corrente mas já estamos em {corrente} — "
        "correr o workflow mensal / scripts/atualizar_calendario.py com dados novos "
        "da fonte oficial (ver docs/FONTE-CALENDARIO.md). Este vermelho é deliberado."
    )


def test_pagina_esta_sincronizada_com_os_dados_e_script_e_idempotente():
    """O ficheiro publicado tem de ser exactamente o que o script geraria
    hoje — apanha tanto uma edição manual dentro das zonas CAL:* como um
    JSON actualizado sem a injecção ter corrido."""
    dados = carregar_dados()
    assert validar_dados(dados) == []
    mudou = atualizar_pagina(dados, hoje_lisboa(), escrever=False)
    assert not mudou, (
        "scripts/atualizar_calendario.py produziria conteúdo diferente do "
        "publicado — correr o script e commitar o resultado"
    )


# ── dados reais ────────────────────────────────────────────────────────────


def test_dados_reais_passam_a_validacao():
    assert validar_dados(carregar_dados()) == []


def test_marcadores_de_injecao_presentes_na_pagina():
    for marcador in ("CAL:META:INICIO", "CAL:META:FIM",
                     "CAL:CORPO:INICIO", "CAL:CORPO:FIM"):
        assert f"<!-- {marcador} -->" in HTML, f"marcador {marcador} em falta"


# ── estado degradado (JSON vazio ou só com meses passados) ────────────────


_HOJE_FIXO = dt.date(2026, 7, 12)
_MES_PASSADO = {
    "ano": 2026, "mes": 6,
    "pagamentos": [{"dia": 8, "prestacoes": ["pensoes"],
                    "metodo": ["transferencia_bancaria"]}],
}


def test_json_sem_mes_corrente_rende_estado_degradado_nunca_tabela():
    dados = {"fonte_url": "https://www.seg-social.pt", "meses": []}
    corpo = render_corpo(dados, _HOJE_FIXO)
    assert "cal-degradado" in corpo
    assert 'data-mes=""' in corpo
    assert "<table" not in corpo
    assert "https://www.seg-social.pt" in corpo  # link à fonte oficial


def test_mes_passado_no_json_nunca_e_renderizado():
    dados = {"fonte_url": "https://www.seg-social.pt", "meses": [_MES_PASSADO]}
    corpo = render_corpo(dados, _HOJE_FIXO)
    assert "junho" not in corpo.lower()
    assert "cal-degradado" in corpo


def test_meta_degradada_nunca_tem_mes_velho():
    dados = {"fonte_url": "https://www.seg-social.pt", "meses": [_MES_PASSADO]}
    meta = render_meta(dados, _HOJE_FIXO)
    assert "junho" not in meta.lower()
    assert "2026" in meta  # degrada para o ano, nunca para um mês velho


def test_mes_seguinte_e_renderizado_quando_disponivel():
    mes_corrente = {
        "ano": 2026, "mes": 7,
        "pagamentos": [{"dia": 8, "prestacoes": ["pensoes"],
                        "metodo": ["transferencia_bancaria"]}],
    }
    mes_seguinte = {
        "ano": 2026, "mes": 8,
        "pagamentos": [{"dia": 7, "prestacoes": ["pensoes"],
                        "metodo": ["transferencia_bancaria"]}],
    }
    dados = {"fonte_url": "https://www.seg-social.pt",
             "meses": [mes_corrente, mes_seguinte]}
    corpo = render_corpo(dados, _HOJE_FIXO)
    assert "Calendário de julho de 2026" in corpo
    assert "Calendário de agosto de 2026" in corpo
    assert "cal-degradado" not in corpo


# ── caminhos de falha da validação (nunca só o caminho feliz) ─────────────


def _base_valida() -> dict:
    return {
        "fonte_url": "https://www.seg-social.pt/noticias/x",
        "meses": [{
            "ano": 2026, "mes": 7,
            "pagamentos": [{"dia": 8, "prestacoes": ["pensoes"],
                            "metodo": ["transferencia_bancaria"]}],
        }],
    }


def test_validacao_rejeita_prestacao_fora_da_allow_list():
    dados = _base_valida()
    dados["meses"][0]["pagamentos"][0]["prestacoes"] = ["prestacao_inventada"]
    assert any("prestacao_inventada" in p for p in validar_dados(dados))


def test_validacao_rejeita_dia_impossivel():
    dados = _base_valida()
    dados["meses"][0]["pagamentos"][0]["dia"] = 32
    assert any("dia inválido" in p for p in validar_dados(dados))


def test_validacao_rejeita_lista_de_prestacoes_vazia():
    dados = _base_valida()
    dados["meses"][0]["pagamentos"][0]["prestacoes"] = []
    assert any("vazio" in p for p in validar_dados(dados))


def test_validacao_rejeita_fonte_fora_de_seg_social():
    dados = _base_valida()
    dados["fonte_url"] = "https://blog-aleatorio.example.com/datas"
    assert any("fonte_url" in p for p in validar_dados(dados))


def test_validacao_rejeita_mes_duplicado():
    dados = _base_valida()
    dados["meses"].append(dados["meses"][0].copy())
    assert any("duplicado" in p for p in validar_dados(dados))


# ── Fase 4: âncoras por prestação (verificação estática) ──────────────────

ANCORAS_SPEC = [
    "pensoes", "csi", "psi", "abono-familia", "subsidio-desemprego",
    "subsidio-doenca", "rsi", "apoio-renda", "cuidador-informal",
]


def test_ancoras_por_prestacao_presentes_quando_ha_mes_corrente():
    if _mes_renderizado() == "":
        pytest.skip("estado degradado — sem tabela por prestação para ancorar")
    for anchor in ANCORAS_SPEC:
        assert f'id="{anchor}"' in HTML, f"âncora #{anchor} em falta na página"


# ── Fase 4: Playwright mobile 375px (Chromium real, nunca file://) ────────


def _localizar_chromium():
    bases = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH")]
    bases += ["/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")]
    for base in bases:
        if not base:
            continue
        candidatos = sorted(glob.glob(
            os.path.join(base, "chromium-*", "chrome-linux*", "chrome")))
        if candidatos:
            return candidatos[-1]
    return None


try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_DISPONIVEL = _localizar_chromium() is not None
except ImportError:
    _PLAYWRIGHT_DISPONIVEL = False

PAGINA_URL = "/calendario-pagamentos-seguranca-social.html"
PAGINA_VELHA_URL = "/_calendario_mes_velho_teste.html"


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Serve o repositório real; o caminho especial de teste devolve a
    página com data-mes adulterado para um mês passado — só em memória,
    nunca um ficheiro escrito no repositório."""

    def do_GET(self):  # noqa: N802 (API do http.server)
        if self.path == PAGINA_VELHA_URL:
            corpo = HTML.replace(
                re.search(r'data-mes="\d{4}-\d{2}"', HTML).group(0),
                'data-mes="2000-01"',
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        super().do_GET()

    def log_message(self, *args):  # silêncio no output do pytest
        pass


@pytest.fixture(scope="module")
def servidor():
    handler = functools.partial(_Handler, directory=str(RAIZ))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


@pytest.mark.skipif(not _PLAYWRIGHT_DISPONIVEL,
                    reason="Playwright/Chromium indisponível neste ambiente")
class TestMobilePlaywright:
    def test_mobile_375px_tabela_visivel_sem_overflow_e_ancoras(self, servidor):
        if _mes_renderizado() == "":
            pytest.skip("estado degradado — sem tabela para verificar")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            erros = []
            page.on("pageerror", lambda e: erros.append(str(e)))
            page.goto(servidor + PAGINA_URL)
            page.wait_for_load_state("networkidle")

            assert page.locator("#mes-corrente").is_visible()
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert overflow == 0, f"overflow horizontal de {overflow}px a 375px"

            for anchor in ANCORAS_SPEC:
                assert page.locator(f"#{anchor}").count() == 1, f"âncora #{anchor}"
            # navegar por âncora posiciona a página (funciona de facto)
            page.goto(servidor + PAGINA_URL + "#rsi")
            page.wait_for_load_state("networkidle")
            assert page.evaluate("window.scrollY") > 0

            # estado normal: aviso de desatualização escondido
            assert page.locator("#cal-aviso-desatualizado").is_hidden()
            assert erros == [], f"erros JS: {erros}"
            browser.close()

    def test_guarda_js_mostra_aviso_quando_mes_renderizado_e_passado(self, servidor):
        if _mes_renderizado() == "":
            pytest.skip("estado degradado — a guarda não se aplica (já explícito)")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            page.goto(servidor + PAGINA_VELHA_URL)
            page.wait_for_load_state("networkidle")
            aviso = page.locator("#cal-aviso-desatualizado")
            assert aviso.is_visible(), (
                "página com data-mes no passado não mostrou o aviso de "
                "desatualização — a guarda JS regrediu"
            )
            assert page.locator("#cal-mes-actual-nome").text_content().strip()
            browser.close()
