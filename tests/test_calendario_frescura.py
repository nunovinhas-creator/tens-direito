"""
Canário de frescura do calendário de pagamentos — o coração do
invariante de CALENDARIO-PAGAMENTOS-SPEC.md: a página publicada NUNCA
pode mostrar um mês passado como se fosse o corrente, e nenhum estado
de erro pode parecer sucesso (ver CLAUDE.md "INVARIANTE").

FALHAR AQUI É O COMPORTAMENTO DESEJADO quando o mês vira sem o
calendário ter sido actualizado (workflow mensal da Fase 3 falhado, ou
Fase 3 ainda por implementar) — CI vermelho força a actualização, em
vez de deixar datas velhas em produção em silêncio.

Este ficheiro adianta da Fase 4 apenas o núcleo do invariante (canário
+ idempotência + estado degradado + caminhos de falha da validação).
O resto da Fase 4 (Playwright mobile 375px, âncoras clicáveis) fica
para a sessão da Fase 3+4, conforme a spec.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

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
