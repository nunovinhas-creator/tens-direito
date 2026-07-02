"""
Testes para scripts/wayback_fallback.py — fallback Wayback Machine (modo
degradado, honesto) consultado só depois de 3 tentativas directas do
scraper falharem. Sem chamadas de rede reais: `fetch_json` é sempre
injectado.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from wayback_fallback import (
    JANELA_DIAS_SNAPSHOT_VALIDO,
    consultar_snapshot,
    decidir_estado_apos_bloqueio,
    snapshot_e_recente,
)

_AGORA = datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)


def _resposta_com_snapshot(dias_atras: int, *, url_snapshot="https://web.archive.org/web/20260625000000/https://example.pt") -> dict:
    data_snapshot = _AGORA - timedelta(days=dias_atras)
    ts = data_snapshot.strftime("%Y%m%d%H%M%S")
    return {
        "archived_snapshots": {
            "closest": {"available": True, "url": url_snapshot, "timestamp": ts, "status": "200"}
        }
    }


def _resposta_sem_snapshot() -> dict:
    return {"archived_snapshots": {}}


# ── consultar_snapshot ───────────────────────────────────────────────────

def test_snapshot_disponivel_e_parseado():
    resultado = consultar_snapshot(
        "https://example.pt", fetch_json=lambda u: _resposta_com_snapshot(3), agora=_AGORA
    )
    assert resultado.disponivel is True
    assert resultado.dias_desde_snapshot == 3
    assert resultado.url_snapshot.startswith("https://web.archive.org/")


def test_sem_snapshot_disponivel():
    resultado = consultar_snapshot(
        "https://example.pt", fetch_json=lambda u: _resposta_sem_snapshot(), agora=_AGORA
    )
    assert resultado.disponivel is False


def test_fetch_json_lanca_excecao_nao_propaga():
    def _falha(u):
        raise ConnectionError("sem rede")
    resultado = consultar_snapshot("https://example.pt", fetch_json=_falha, agora=_AGORA)
    assert resultado.disponivel is False


def test_resposta_nao_e_dict_nao_crasha():
    resultado = consultar_snapshot("https://example.pt", fetch_json=lambda u: None, agora=_AGORA)
    assert resultado.disponivel is False


def test_timestamp_invalido_nao_crasha():
    resposta = {"archived_snapshots": {"closest": {"available": True, "url": "x", "timestamp": "nao-e-uma-data"}}}
    resultado = consultar_snapshot("https://example.pt", fetch_json=lambda u: resposta, agora=_AGORA)
    assert resultado.disponivel is False


def test_url_e_incluido_no_pedido():
    urls_pedidos = []

    def _fetch(u):
        urls_pedidos.append(u)
        return _resposta_sem_snapshot()

    consultar_snapshot("https://www.iefp.pt/subsidio-desemprego", fetch_json=_fetch, agora=_AGORA)
    assert "https://www.iefp.pt/subsidio-desemprego" in urls_pedidos[0]


# ── snapshot_e_recente ───────────────────────────────────────────────────

def test_snapshot_dentro_da_janela_e_recente():
    resultado = consultar_snapshot("https://example.pt", fetch_json=lambda u: _resposta_com_snapshot(5), agora=_AGORA)
    assert snapshot_e_recente(resultado) is True


def test_snapshot_no_limite_da_janela_e_recente():
    resultado = consultar_snapshot(
        "https://example.pt", fetch_json=lambda u: _resposta_com_snapshot(JANELA_DIAS_SNAPSHOT_VALIDO), agora=_AGORA
    )
    assert snapshot_e_recente(resultado) is True


def test_snapshot_fora_da_janela_nao_e_recente():
    resultado = consultar_snapshot("https://example.pt", fetch_json=lambda u: _resposta_com_snapshot(30), agora=_AGORA)
    assert snapshot_e_recente(resultado) is False


def test_indisponivel_nunca_e_recente():
    resultado = consultar_snapshot("https://example.pt", fetch_json=lambda u: _resposta_sem_snapshot(), agora=_AGORA)
    assert snapshot_e_recente(resultado) is False


# ── decidir_estado_apos_bloqueio: 3 falhas + snapshot -> OK_VIA_ARQUIVO ─────

def test_snapshot_recente_apos_bloqueio_da_ok_via_arquivo():
    decisao = decidir_estado_apos_bloqueio(
        "https://www.seg-social.pt/abono-de-familia",
        fetch_json=lambda u: _resposta_com_snapshot(2),
        agora=_AGORA,
    )
    assert decisao["estado"] == "OK_VIA_ARQUIVO"
    assert decisao["snapshot"]["dias_desde_snapshot"] == 2


def test_decisao_ok_via_arquivo_nunca_e_so_ok():
    # BLOQUEADO nunca é disfarçado de OK -- o estado devolvido tem sempre
    # de distinguir explicitamente o modo degradado.
    decisao = decidir_estado_apos_bloqueio(
        "https://www.seg-social.pt/abono-de-familia",
        fetch_json=lambda u: _resposta_com_snapshot(1),
        agora=_AGORA,
    )
    assert decisao["estado"] != "OK"


# ── decidir_estado_apos_bloqueio: 3 falhas + sem snapshot -> BLOQUEADO ──────

def test_sem_snapshot_apos_bloqueio_continua_bloqueado():
    decisao = decidir_estado_apos_bloqueio(
        "https://www.iefp.pt/subsidio-desemprego",
        fetch_json=lambda u: _resposta_sem_snapshot(),
        agora=_AGORA,
    )
    assert decisao["estado"] == "BLOQUEADO"
    assert decisao["snapshot"] is None


def test_snapshot_antigo_apos_bloqueio_continua_bloqueado():
    decisao = decidir_estado_apos_bloqueio(
        "https://www.iefp.pt/subsidio-desemprego",
        fetch_json=lambda u: _resposta_com_snapshot(60),
        agora=_AGORA,
    )
    assert decisao["estado"] == "BLOQUEADO"


def test_falha_de_rede_na_consulta_resulta_em_bloqueado():
    def _falha(u):
        raise TimeoutError("wayback indisponível")
    decisao = decidir_estado_apos_bloqueio(
        "https://www.iefp.pt/subsidio-desemprego", fetch_json=_falha, agora=_AGORA
    )
    assert decisao["estado"] == "BLOQUEADO"
