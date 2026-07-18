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
    INDEX,
    PAGINA,
    _encontrar_mes,
    atualizar_homepage,
    atualizar_pagina,
    carregar_dados,
    hoje_lisboa,
    render_corpo,
    render_meta,
    validar_dados,
)

HTML = PAGINA.read_text(encoding="utf-8")
INDEX_HTML = INDEX.read_text(encoding="utf-8")


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


# ── auditoria 2026-07-18: injector corre sempre + limites de plausibilidade ─
#
# Provam o CAMINHO DE FALHA (não só o feliz): a produção degrada server-side
# quando o mês vira sem dados, e um dia implausível nunca é publicado às cegas.

_SO_AGOSTO = {
    "fonte_url": "https://www.seg-social.pt",
    "meses": [{
        "ano": 2026, "mes": 8,
        "pagamentos": [
            {"dia": 7, "prestacoes": ["pensoes"], "metodo": ["transferencia_bancaria"]},
            {"dia": 28, "prestacoes": ["cuidador_informal"],
             "metodo": ["transferencia_bancaria", "vale_de_correio"]},
        ],
    }],
}


def test_1_setembro_scraper_falhado_pagina_degrada_sem_tabela_de_agosto():
    """1 de setembro, setembro ausente do JSON (scraper falhou e ninguém
    preencheu), agosto presente mas já passado. O injector, correndo agora
    em qualquer ramo com hoje=1 de setembro, TEM de degradar server-side —
    nunca manter a tabela de agosto como se fosse a corrente (era a lacuna
    crítica da auditoria)."""
    corpo = render_corpo(_SO_AGOSTO, dt.date(2026, 9, 1))
    assert "cal-degradado" in corpo
    assert 'data-mes=""' in corpo
    assert "agosto" not in corpo.lower(), "mês passado nunca renderizado"
    assert "<table" not in corpo, "nenhuma tabela velha na página degradada"


def test_25_agosto_injector_nao_degrada_e_e_idempotente_sobre_agosto(tmp_path):
    """25 de agosto (mês-alvo do scraper = setembro, ainda ausente): o
    injector corre na mesma, mas rende com hoje=agosto → agosto corrente,
    NUNCA degradado. E, sobre uma página já sincronizada com agosto (corrida
    de 1 de agosto), a 2.ª injecção não muda nada → zero commits espúrios."""
    corpo = render_corpo(_SO_AGOSTO, dt.date(2026, 8, 25))
    assert "cal-degradado" not in corpo
    assert "Calendário de agosto de 2026" in corpo

    pagina = tmp_path / "cal.html"
    pagina.write_text(PAGINA.read_text(encoding="utf-8"), encoding="utf-8")
    atualizar_pagina(_SO_AGOSTO, dt.date(2026, 8, 1), caminho=pagina, escrever=True)
    apos_1ago = pagina.read_text(encoding="utf-8")
    assert 'id="cal-corrente" data-mes="2026-08"' in apos_1ago
    # A classe .cal-degradado existe sempre no CSS e no banner de aviso JS
    # (fora da zona CAL:CORPO); a assinatura única do BLOCO degradado é o texto.
    assert "Ainda não temos o calendário verificado" not in apos_1ago
    mudou_25 = atualizar_pagina(_SO_AGOSTO, dt.date(2026, 8, 25),
                                caminho=pagina, escrever=False)
    assert not mudou_25, "injecção a 25 Ago sobre página já de agosto não deve mudar nada"


def test_validacao_rejeita_dia_fora_do_intervalo_plausivel():
    """Pensões no dia 25 é implausível (referência ~dia 8) — a validação
    falha, o main() sai antes de escrever, JSON e HTML ficam intactos."""
    dados = _base_valida()
    dados["meses"][0]["pagamentos"][0]["dia"] = 25  # pensoes: intervalo [5-12]
    problemas = validar_dados(dados)
    assert any("intervalo plausível" in p for p in problemas), problemas


def test_intervalos_plausiveis_cobrem_toda_a_allow_list_e_o_historico_real():
    """Sem buracos: toda a prestação da allow-list tem intervalo, e todos os
    meses reais já publicados passam (zero falsos positivos retroactivos)."""
    from atualizar_calendario import DIAS_PLAUSIVEIS, PRESTACOES
    assert set(PRESTACOES) == set(DIAS_PLAUSIVEIS)
    assert validar_dados(carregar_dados()) == []


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


# ── Destaque "Próximo pagamento" no topo (verificação estática) ───────────

def test_destaque_topo_estatico_presente_quando_ha_mes_corrente():
    """A camada estática do destaque (todas as datas do mês) tem de estar
    sempre visível no topo, sem depender de JS — é o que responde ao
    utilizador que só quer o relance imediato das datas."""
    if _mes_renderizado() == "":
        pytest.skip("estado degradado — sem destaque de datas")
    assert 'id="cal-destaque"' in HTML
    assert 'id="cal-dados"' in HTML
    assert re.search(r"Datas de pagamento em \w+:", HTML), (
        "linha estática com as datas do mês em falta no destaque do topo"
    )
    # o destaque vem ANTES do h2/tabela do mês (é o topo do conteúdo)
    assert HTML.index('id="cal-destaque"') < HTML.index('id="mes-corrente"')


def test_cal_dados_json_valido_e_coerente_com_o_json_de_dados():
    if _mes_renderizado() == "":
        pytest.skip("estado degradado — sem #cal-dados")
    import json as _json
    m = re.search(r'<script id="cal-dados" type="application/json">(.*?)</script>',
                  HTML, re.S)
    assert m, "#cal-dados em falta"
    itens = _json.loads(m.group(1))
    assert itens and all("dia" in it and "resumo" in it for it in itens)
    dados = carregar_dados()
    hoje = hoje_lisboa()
    atual = _encontrar_mes(dados, hoje.year, hoje.month)
    dias_esperados = sorted(p["dia"] for p in atual["pagamentos"])
    assert [it["dia"] for it in itens] == dias_esperados, (
        "os dias de #cal-dados não batem com o JSON de dados — o destaque "
        "e a tabela deixariam de estar sincronizados"
    )


# ── Barra fixa "Próximo pagamento" da homepage (zona CAL-HOME) ────────────


def test_homepage_tem_marcadores_e_dados_da_barra_do_calendario():
    for marcador in ("CAL-HOME:INICIO", "CAL-HOME:FIM"):
        assert f"<!-- {marcador} -->" in INDEX_HTML, f"marcador {marcador} em falta na homepage"
    assert 'id="cal-home-dados"' in INDEX_HTML


def test_homepage_barra_sincronizada_com_os_dados_e_idempotente():
    """A zona CAL-HOME publicada tem de ser exactamente o que o injector
    geraria hoje — apanha um JSON actualizado sem a injecção ter corrido."""
    dados = carregar_dados()
    assert validar_dados(dados) == []
    mudou = atualizar_homepage(dados, hoje_lisboa(), escrever=False)
    assert not mudou, (
        "scripts/atualizar_calendario.py produziria uma barra CAL-HOME diferente "
        "da publicada em index.html — correr o script e commitar o resultado"
    )


def test_homepage_cal_home_dados_coerente_com_o_json_e_mes_corrente():
    import json as _json
    m = re.search(
        r'<script id="cal-home-dados" type="application/json" data-mes="(\d{4}-\d{2}|)">(.*?)</script>',
        INDEX_HTML, re.S)
    assert m, "#cal-home-dados em falta na homepage"
    data_mes, payload = m.group(1), m.group(2)
    itens = _json.loads(payload)
    hoje = hoje_lisboa()
    atual = _encontrar_mes(carregar_dados(), hoje.year, hoje.month)
    if atual is None:
        # sem mês corrente no JSON: barra degrada — data-mes vazio, sem dias.
        assert data_mes == "" and itens == []
        return
    assert data_mes == f"{hoje.year}-{hoje.month:02d}"
    dias_esperados = sorted(p["dia"] for p in atual["pagamentos"])
    assert [it["dia"] for it in itens] == dias_esperados, (
        "os dias de #cal-home-dados não batem com o JSON de dados"
    )
    assert all("dia" in it and "resumo" in it for it in itens)


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
INDEX_URL = "/index.html"
INDEX_VELHO_URL = "/_index_mes_velho_teste.html"


class _Handler(http.server.SimpleHTTPRequestHandler):
    """Serve o repositório real; os caminhos especiais de teste devolvem a
    página / a homepage com data-mes adulterado para um mês passado — só em
    memória, nunca um ficheiro escrito no repositório."""

    def _servir(self, corpo: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):  # noqa: N802 (API do http.server)
        if self.path == PAGINA_VELHA_URL:
            self._servir(HTML.replace(
                re.search(r'data-mes="\d{4}-\d{2}"', HTML).group(0),
                'data-mes="2000-01"',
            ).encode("utf-8"))
            return
        if self.path == INDEX_VELHO_URL:
            self._servir(re.sub(
                r'(id="cal-home-dados"[^>]*data-mes=")\d{4}-\d{2}(")',
                r'\g<1>2000-01\g<2>', INDEX_HTML,
            ).encode("utf-8"))
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

    def test_destaque_promove_proximo_pagamento_no_mes_corrente(self, servidor):
        if _mes_renderizado() == "":
            pytest.skip("estado degradado — sem destaque")
        hoje = dt.date.today()
        if _mes_renderizado() != f"{hoje.year}-{hoje.month:02d}":
            pytest.skip("página não é do mês corrente hoje (o canário de frescura cobre isso)")
        import json as _json
        itens = _json.loads(re.search(
            r'<script id="cal-dados" type="application/json">(.*?)</script>',
            HTML, re.S).group(1))
        dias = sorted(it["dia"] for it in itens)
        futuros = [d for d in dias if d >= hoje.day]
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            page.goto(servidor + PAGINA_URL)
            page.wait_for_load_state("networkidle")
            # a camada estática está sempre visível
            assert page.locator(".cal-destaque-linha").is_visible()
            prox = page.locator(".cal-destaque-proximo")
            assert prox.count() == 1 and prox.is_visible()
            texto = prox.text_content()
            if futuros:
                assert f"{futuros[0]} de " in texto, (
                    f"esperava promover o dia {futuros[0]}, obteve: {texto!r}")
            else:
                assert "processados" in texto.lower()
            browser.close()

    def test_destaque_nunca_promove_proximo_num_mes_velho(self, servidor):
        """Num mês renderizado no passado, o destaque nunca inventa uma
        'próxima' data — mas a camada estática das datas mantém-se."""
        if _mes_renderizado() == "":
            pytest.skip("estado degradado — sem destaque")
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            page.goto(servidor + PAGINA_VELHA_URL)
            page.wait_for_load_state("networkidle")
            assert page.locator(".cal-destaque-proximo").count() == 0
            assert page.locator(".cal-destaque-linha").is_visible()
            browser.close()

    def test_barra_homepage_promove_proximo_pagamento_no_mes_corrente(self, servidor):
        """A barra fixa da homepage promove a próxima data a contar de hoje,
        SÓ quando os dados (#cal-home-dados[data-mes]) são do mês corrente."""
        import json as _json
        m = re.search(
            r'<script id="cal-home-dados"[^>]*data-mes="(\d{4}-\d{2}|)">(.*?)</script>',
            INDEX_HTML, re.S)
        assert m, "#cal-home-dados em falta"
        data_mes, payload = m.group(1), m.group(2)
        hoje = dt.date.today()
        if data_mes != f"{hoje.year}-{hoje.month:02d}":
            pytest.skip("barra da homepage não é do mês corrente hoje")
        dias = sorted(it["dia"] for it in _json.loads(payload))
        futuros = [d for d in dias if d >= hoje.day]
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            page.goto(servidor + INDEX_URL)
            page.wait_for_load_state("networkidle")
            texto = page.locator(".cal-topo .cal-topo-texto").inner_text().strip()
            if futuros:
                assert "Próximo pagamento" in texto and f"{futuros[0]} de " in texto, (
                    f"esperava promover o dia {futuros[0]}, obteve: {texto!r}")
            else:
                # todos processados: nunca inventa — mantém o rótulo genérico
                assert "Próximo pagamento" not in texto
            browser.close()

    def test_barra_homepage_nunca_promove_num_mes_velho(self, servidor):
        """Com dados de um mês passado (data-mes adulterado), a barra mantém
        o rótulo genérico — nunca inventa uma 'próxima' data velha."""
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=_localizar_chromium())
            page = browser.new_page(viewport={"width": 375, "height": 800})
            page.goto(servidor + INDEX_VELHO_URL)
            page.wait_for_load_state("networkidle")
            texto = page.locator(".cal-topo .cal-topo-texto").inner_text().strip()
            assert "Próximo pagamento" not in texto, (
                f"barra promoveu uma data num mês velho: {texto!r}")
            assert "Calendário de pagamentos" in texto
            browser.close()
