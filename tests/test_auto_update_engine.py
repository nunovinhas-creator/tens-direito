"""
Testes para scripts/auto_update_engine.py — Camada 4, motor de auto-update
controlado. Desligado por omissão (reutiliza
decisao_datas.AUTO_UPDATE_HABILITADO); só actua com decisão AUTO_UPDATE
E a flag explicitamente a True.

Cobertura obrigatória:
- AUTO_UPDATE não executa quando a flag está desligada
- rollback funciona em caso de erro simulado
- alterações são bloqueadas se a diferença for anormal
- nenhum ficheiro é alterado sem autorização explícita (em nenhum cenário)
"""
import builtins
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import decisao_datas
import auto_update_engine
from auto_update_engine import (
    AcaoAutoUpdate,
    AcaoRefreshCarimbo,
    aplicar_auto_update,
    aplicar_refresh_carimbo,
    buscar_novo_valor_mock,
    elegivel_refresh_carimbo,
)


def _alerta_ias(novo_valor=None, acao="AUTO_UPDATE"):
    conteudo = "O valor de referência é IAS de 522,50 € (2025)."
    alerta = {
        "pagina": "pagina-ias.html",
        "tipo": "valor_ias",
        "classificacao": {
            "data": "522,50 €",
            "estado": "OUTDATED_AUTOFIXABLE",
            "contexto": conteudo,
        },
        "decisao": {"estado": "OUTDATED_AUTOFIXABLE", "acao": acao, "contexto": {}},
    }
    if novo_valor is not None:
        alerta["novo_valor"] = novo_valor
    return alerta


# ── Não autorizado -> SKIPPED_SAFE_MODE exacto, nada tocado ────────────────

def test_flag_desligada_por_omissao():
    assert decisao_datas.AUTO_UPDATE_HABILITADO is False


def test_flag_desligada_devolve_skipped_safe_mode_exato():
    alerta = _alerta_ias(novo_valor="537,13 €")
    resultado = aplicar_auto_update(alerta)
    assert resultado == {
        "acao": AcaoAutoUpdate.SKIPPED_SAFE_MODE,
        "motivo": "AUTO_UPDATE desativado ou não elegível",
    }


def test_acao_diferente_de_auto_update_e_sempre_skipped_mesmo_com_flag_ligada(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = _alerta_ias(novo_valor="537,13 €", acao="CREATE_ISSUE")
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.SKIPPED_SAFE_MODE


def test_flag_ligada_mas_decisao_ausente_e_skipped(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = {"pagina": "x.html", "classificacao": {"data": "1", "contexto": "1"}}
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.SKIPPED_SAFE_MODE


# ── Autorizado, sem novo valor -> nada aplicado ────────────────────────────

def test_autorizado_sem_novo_valor_nao_aplica_nada(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = _alerta_ias()  # sem "novo_valor"
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.SKIPPED_SEM_NOVO_VALOR
    assert "conteudo_novo" not in resultado
    assert resultado["snapshot"] == alerta["classificacao"]["contexto"]


def test_buscar_novo_valor_mock_nunca_inventa_valor():
    assert buscar_novo_valor_mock({"pagina": "x.html"}) is None
    assert buscar_novo_valor_mock({"novo_valor": "537,13 €"}) == "537,13 €"


# ── Diferença anómala -> bloqueado ──────────────────────────────────────────

def test_diferenca_numerica_anomala_aborta_update(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    conteudo_original = "O valor de referência é IAS de 522,50 € (2025)."
    alerta = _alerta_ias(novo_valor="52250,00 €")  # 100x — claramente anómalo
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.ABORTED_DIFERENCA_ANOMALA
    assert "conteudo_novo" not in resultado
    assert resultado["snapshot"] == conteudo_original


def test_diferenca_textual_anomala_aborta_update(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = {
        "pagina": "pagina-prazo.html",
        "tipo": "prazo_outono",
        "classificacao": {
            "data": "15 de setembro de 2024",
            "estado": "OUTDATED_AUTOFIXABLE",
            "contexto": "As candidaturas encerraram a 15 de setembro de 2024.",
        },
        "decisao": {"acao": "AUTO_UPDATE"},
        "novo_valor": "x",  # comprimento absurdamente menor -> rácio fora do limite
    }
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.ABORTED_DIFERENCA_ANOMALA


def test_valor_antigo_nao_encontrado_no_conteudo_aborta(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = {
        "pagina": "x.html",
        "classificacao": {
            "data": "999,99 €",
            "estado": "OUTDATED_AUTOFIXABLE",
            "contexto": "Este texto não contém esse valor.",
        },
        "decisao": {"acao": "AUTO_UPDATE"},
        "novo_valor": "537,13 €",
    }
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.ABORTED_VALOR_NAO_ENCONTRADO


# ── Diferença razoável, autorizado -> aplica e regista log ────────────────

def test_update_valido_e_autorizado_aplica_e_gera_log(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    conteudo_original = "O valor de referência é IAS de 522,50 € (2025)."
    alerta = _alerta_ias(novo_valor="537,13 €")

    resultado = aplicar_auto_update(alerta, agora="2026-07-01T00:00:00+00:00")

    assert resultado["acao"] == AcaoAutoUpdate.AUTO_UPDATE_APPLIED
    assert "537,13 €" in resultado["conteudo_novo"]
    assert "522,50 €" not in resultado["conteudo_novo"]
    assert resultado["snapshot"] == conteudo_original  # original preservado
    assert resultado["log"] == {
        "pagina": "pagina-ias.html",
        "tipo": "valor_ias",
        "estado": "OUTDATED_AUTOFIXABLE",
        "valor_antigo": "522,50 €",
        "valor_novo": "537,13 €",
        "aplicado_em": "2026-07-01T00:00:00+00:00",
    }
    # A string original nunca é mutada (imutabilidade + snapshot próprio).
    assert alerta["classificacao"]["contexto"] == conteudo_original


# ── Rollback em erro simulado ────────────────────────────────────────────────

def test_rollback_em_erro_simulado_preserva_snapshot(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    conteudo_original = "O valor de referência é IAS de 522,50 € (2025)."

    def _fetcher_corrompido(alerta):
        # Simula uma fonte externa corrompida a devolver um tipo
        # inesperado (não string) -- deve ser apanhado e revertido, nunca
        # propagado como excepção nem aplicado ao conteúdo.
        return 52713

    alerta = _alerta_ias(novo_valor="qualquer coisa")  # ignorado; usamos fetcher custom
    resultado = aplicar_auto_update(alerta, buscar_novo_valor=_fetcher_corrompido)

    assert resultado["acao"] == AcaoAutoUpdate.ROLLED_BACK
    assert resultado["snapshot"] == conteudo_original
    assert resultado["conteudo"] == conteudo_original


def test_rollback_nao_lanca_excepcao_para_o_chamador(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _fetcher_que_rebenta(alerta):
        raise RuntimeError("fonte externa indisponível")

    alerta = _alerta_ias(novo_valor="x")
    resultado = aplicar_auto_update(alerta, buscar_novo_valor=_fetcher_que_rebenta)
    assert resultado["acao"] == AcaoAutoUpdate.ROLLED_BACK
    assert "fonte externa indisponível" in resultado["motivo"]


# ── Nenhuma escrita real de ficheiro, em nenhum cenário ────────────────────

def test_modulo_nunca_importa_os_nem_subprocess():
    assert not hasattr(auto_update_engine, "os")
    assert not hasattr(auto_update_engine, "subprocess")
    assert not hasattr(auto_update_engine, "shutil")


def test_nenhuma_escrita_real_mesmo_quando_autorizado_e_aplicado(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _bloqueado(*a, **k):
        raise AssertionError("auto_update_engine tentou fazer I/O real")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)
    monkeypatch.setattr(subprocess, "Popen", _bloqueado)

    alerta = _alerta_ias(novo_valor="537,13 €")
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.AUTO_UPDATE_APPLIED


def test_nenhuma_escrita_real_quando_nao_autorizado(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("auto_update_engine tentou fazer I/O real")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)

    alerta = _alerta_ias(novo_valor="537,13 €")
    resultado = aplicar_auto_update(alerta)
    assert resultado["acao"] == AcaoAutoUpdate.SKIPPED_SAFE_MODE


# ── Determinismo ────────────────────────────────────────────────────────────

def test_aplicar_auto_update_e_deterministico(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alerta = _alerta_ias(novo_valor="537,13 €")
    resultados = [
        aplicar_auto_update(alerta, agora="2026-07-01T00:00:00+00:00")
        for _ in range(10)
    ]
    assert all(r == resultados[0] for r in resultados)


# ── refresh_carimbo (Fase 4, simulada/desligada) ────────────────────────────

_PAGINA_EXEMPLO = (
    "<html><body>"
    "<p>Verificado a 24 de junho de 2026 · fonte oficial.</p>"
    '<script type="application/ld+json">{"@type": "Article", "dateModified": "2026-06-24"}</script>'
    "</body></html>"
)


def test_flag_revalidacao_carimbo_desligada_por_omissao():
    assert decisao_datas.REVALIDACAO_CARIMBO_HABILITADA is False


def test_elegivel_com_fonte_ok_e_hash_inalterado():
    assert elegivel_refresh_carimbo("OK", True) is True


def test_ok_via_arquivo_nunca_elegivel():
    assert elegivel_refresh_carimbo("OK_VIA_ARQUIVO", True) is False


def test_bloqueado_nunca_elegivel():
    assert elegivel_refresh_carimbo("BLOQUEADO", True) is False


def test_hash_alterado_nunca_elegivel():
    assert elegivel_refresh_carimbo("OK", False) is False


def test_hash_desconhecido_nunca_elegivel():
    assert elegivel_refresh_carimbo("OK", None) is False


def test_flag_desligada_devolve_skipped_safe_mode_sem_tocar_no_conteudo():
    resultado = aplicar_refresh_carimbo(
        _PAGINA_EXEMPLO,
        fonte_estado="OK",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.SKIPPED_SAFE_MODE
    assert resultado["conteudo_novo"] == _PAGINA_EXEMPLO


def test_flag_ligada_mas_nao_elegivel_e_skipped(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)
    resultado = aplicar_refresh_carimbo(
        _PAGINA_EXEMPLO,
        fonte_estado="OK_VIA_ARQUIVO",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.SKIPPED_NAO_ELEGIVEL
    assert resultado["conteudo_novo"] == _PAGINA_EXEMPLO


def test_flag_ligada_e_elegivel_substitui_carimbo_e_date_modified(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)
    resultado = aplicar_refresh_carimbo(
        _PAGINA_EXEMPLO,
        fonte_estado="OK",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.CARIMBO_REFRESHED
    assert "Verificado a 2 de julho de 2026" in resultado["conteudo_novo"]
    assert '"dateModified": "2026-07-02"' in resultado["conteudo_novo"]
    # Só as duas zonas confinadas mudaram -- resto da página intacto.
    assert "fonte oficial" in resultado["conteudo_novo"]
    assert '"@type": "Article"' in resultado["conteudo_novo"]


def test_sem_carimbo_reconhecivel_e_skipped(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)
    resultado = aplicar_refresh_carimbo(
        "<html><body>Sem nenhum carimbo aqui.</body></html>",
        fonte_estado="OK",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.SKIPPED_SEM_CARIMBO


def test_alteracao_fora_da_zona_confinada_e_abortada(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)
    # Simula um regex que "escapa" e mexe em texto fora das duas zonas
    # esperadas -- a verificação de confinamento tem de apanhar isto.
    monkeypatch.setattr(
        auto_update_engine,
        "_apenas_carimbo_alterado",
        lambda antigo, novo: False,
    )
    resultado = aplicar_refresh_carimbo(
        _PAGINA_EXEMPLO,
        fonte_estado="OK",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.ABORTED_ESCRITA_FORA_DE_ZONA
    assert resultado["conteudo_novo"] == _PAGINA_EXEMPLO


def test_refresh_carimbo_nunca_escreve_ficheiro_real(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)

    def _bloqueado(*a, **k):
        raise AssertionError("auto_update_engine tentou fazer I/O real")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)

    resultado = aplicar_refresh_carimbo(
        _PAGINA_EXEMPLO,
        fonte_estado="OK",
        hash_inalterado=True,
        nova_data_extenso="2 de julho de 2026",
        nova_data_iso="2026-07-02",
    )
    assert resultado["acao"] == AcaoRefreshCarimbo.CARIMBO_REFRESHED


def test_refresh_carimbo_e_deterministico(monkeypatch):
    monkeypatch.setattr(decisao_datas, "REVALIDACAO_CARIMBO_HABILITADA", True)
    resultados = [
        aplicar_refresh_carimbo(
            _PAGINA_EXEMPLO,
            fonte_estado="OK",
            hash_inalterado=True,
            nova_data_extenso="2 de julho de 2026",
            nova_data_iso="2026-07-02",
        )
        for _ in range(10)
    ]
    assert all(r == resultados[0] for r in resultados)
