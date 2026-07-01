"""
Testes para scripts/orquestrador_datas.py — Camada 5, ponto único de
controlo de execução. Verifica que AUTO_UPDATE só acontece com todas as
condições válidas, que qualquer falha nunca crasha nem executa
auto-update, e que STATIC_REFERENCE/BLOCKED_SOURCE nunca são
auto-actualizados.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import auto_update_engine
import decisao_datas
from auto_update_engine import AcaoAutoUpdate
from decisao_datas import Acao
from orquestrador_datas import processar_alerta

AGORA = "2026-07-01T00:00:00+00:00"


def _alerta(estado="OUTDATED_AUTOFIXABLE", acao_decidida="AUTO_UPDATE", novo_valor="537,13 €"):
    conteudo = "O valor de referência é IAS de 522,50 € (2025)."
    alerta = {
        "pagina": "pagina-ias.html",
        "tipo": "valor_ias",
        "classificacao": {
            "data": "522,50 €",
            "estado": estado,
            "contexto": conteudo,
        },
        "decisao": {"estado": estado, "acao": acao_decidida, "contexto": {}},
    }
    if novo_valor is not None:
        alerta["novo_valor"] = novo_valor
    return alerta


def _campos_obrigatorios(resultado):
    return {"estado", "acao_pretendida", "acao_executada", "motivo", "timestamp"} <= set(
        resultado.keys()
    )


# ── AUTO_UPDATE só executa com TODAS as condições válidas ──────────────────

def test_auto_update_executa_com_todas_as_condicoes_validas(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    resultado = processar_alerta(_alerta(), agora=AGORA)

    assert resultado["acao_executada"] == Acao.AUTO_UPDATE
    assert resultado["acao_pretendida"] == Acao.AUTO_UPDATE
    assert resultado["resultado_engine"]["acao"] == AcaoAutoUpdate.AUTO_UPDATE_APPLIED
    assert _campos_obrigatorios(resultado)


def test_flag_desligada_impede_auto_update_e_faz_fallback_create_issue():
    # AUTO_UPDATE_HABILITADO é False por omissão (verificado noutro teste)
    resultado = processar_alerta(_alerta(), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert "AUTO_UPDATE_HABILITADO" in resultado["motivo"]


def test_sem_novo_valor_impede_auto_update(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    resultado = processar_alerta(_alerta(novo_valor=None), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert "novo_valor" in resultado["motivo"]


def test_decisao_diferente_de_auto_update_nunca_chama_engine(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _engine_nao_deve_ser_chamado(*a, **k):
        raise AssertionError("engine não deveria ser chamado")

    monkeypatch.setattr(auto_update_engine, "aplicar_auto_update", _engine_nao_deve_ser_chamado)

    resultado = processar_alerta(_alerta(acao_decidida="CREATE_ISSUE"), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert resultado["acao_pretendida"] == Acao.CREATE_ISSUE


# ── STATIC_REFERENCE e BLOCKED_SOURCE nunca entram em auto-update ─────────

def test_static_reference_nunca_e_atualizado(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _engine_nao_deve_ser_chamado(*a, **k):
        raise AssertionError("engine não deveria ser chamado para STATIC_REFERENCE")

    monkeypatch.setattr(auto_update_engine, "aplicar_auto_update", _engine_nao_deve_ser_chamado)

    resultado = processar_alerta(_alerta(estado="STATIC_REFERENCE"), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert "STATIC_REFERENCE" in resultado["motivo"]


def test_blocked_source_nunca_entra_em_auto_update(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _engine_nao_deve_ser_chamado(*a, **k):
        raise AssertionError("engine não deveria ser chamado para BLOCKED_SOURCE")

    monkeypatch.setattr(auto_update_engine, "aplicar_auto_update", _engine_nao_deve_ser_chamado)

    resultado = processar_alerta(_alerta(estado="BLOCKED_SOURCE"), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert "BLOCKED_SOURCE" in resultado["motivo"]


# ── Fallback obrigatório: AUTO_UPDATE falha no engine -> CREATE_ISSUE ──────

def test_engine_recusa_update_faz_fallback_create_issue(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    monkeypatch.setattr(
        auto_update_engine,
        "aplicar_auto_update",
        lambda alerta, **k: {"acao": AcaoAutoUpdate.ABORTED_DIFERENCA_ANOMALA, "motivo": "diff"},
    )
    resultado = processar_alerta(_alerta(), agora=AGORA)
    assert resultado["acao_executada"] == Acao.CREATE_ISSUE
    assert resultado["resultado_engine"]["acao"] == AcaoAutoUpdate.ABORTED_DIFERENCA_ANOMALA


# ── Falha-safe global: erro inesperado nunca executa auto-update ──────────

def test_erro_inesperado_no_engine_faz_fallback_log_only_nunca_auto_update(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _engine_que_rebenta(*a, **k):
        raise RuntimeError("falha completamente inesperada no engine")

    monkeypatch.setattr(auto_update_engine, "aplicar_auto_update", _engine_que_rebenta)

    resultado = processar_alerta(_alerta(), agora=AGORA)
    assert resultado["acao_executada"] == Acao.LOG_ONLY
    assert resultado["acao_executada"] != Acao.AUTO_UPDATE
    assert "falha completamente inesperada" in resultado["motivo"]


def test_alerta_malformado_nao_crasha_e_nunca_executa_auto_update():
    resultado = processar_alerta(None, agora=AGORA)  # type: ignore[arg-type]
    assert resultado["acao_executada"] != Acao.AUTO_UPDATE
    assert _campos_obrigatorios(resultado)


def test_alerta_sem_decisao_nem_classificacao_nao_crasha():
    resultado = processar_alerta({"pagina": "x.html"}, agora=AGORA)
    assert resultado["acao_executada"] == Acao.IGNORAR
    assert _campos_obrigatorios(resultado)


def test_acao_pretendida_desconhecida_tem_fallback_log_only(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = _alerta(acao_decidida="ALGO_NAO_MAPEADO")
    resultado = processar_alerta(alerta, agora=AGORA)
    assert resultado["acao_executada"] == Acao.LOG_ONLY


# ── Logging sempre gerado ───────────────────────────────────────────────────

def test_logging_sempre_gerado_em_todos_os_cenarios(monkeypatch):
    cenarios = [
        _alerta(),  # flag off -> CREATE_ISSUE
        _alerta(estado="STATIC_REFERENCE"),
        _alerta(estado="BLOCKED_SOURCE"),
        _alerta(acao_decidida="LOG_ONLY"),
        _alerta(acao_decidida="IGNORAR"),
        None,
        {},
    ]
    for alerta in cenarios:
        resultado = processar_alerta(alerta, agora=AGORA)
        assert _campos_obrigatorios(resultado)
        assert isinstance(resultado["motivo"], str) and resultado["motivo"]
        assert resultado["timestamp"] == AGORA


# ── Determinismo ────────────────────────────────────────────────────────────

def test_processar_alerta_e_deterministico(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = _alerta()
    resultados = [processar_alerta(alerta, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


def test_processar_alerta_ineligivel_e_deterministico():
    alerta = _alerta()  # flag off
    resultados = [processar_alerta(alerta, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


# ── Regra arquitectural: só o orquestrador chama o auto_update_engine ──────

def test_apenas_orquestrador_chama_auto_update_engine():
    scripts_dir = Path(__file__).parent.parent / "scripts"
    ficheiros_com_chamada = []
    for caminho in scripts_dir.glob("*.py"):
        if caminho.name in ("orquestrador_datas.py", "auto_update_engine.py"):
            continue
        texto = caminho.read_text(encoding="utf-8")
        if "aplicar_auto_update(" in texto:
            ficheiros_com_chamada.append(caminho.name)
    assert ficheiros_com_chamada == [], (
        f"aplicar_auto_update chamado fora do orquestrador em: {ficheiros_com_chamada}"
    )
