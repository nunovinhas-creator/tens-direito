"""
Testes para scripts/shadow_mode.py — ferramenta de validação que corre
toda a cadeia de decisão em modo de observação pura.

Cobertura pedida:
- nenhuma escrita ocorre
- nenhuma função destrutiva é chamada
- o relatório é determinístico
- o fluxo percorre todas as camadas existentes
- erros num provider ou no auto_update_engine nunca interrompem a
  análise dos restantes alertas
"""
import builtins
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import auto_update_engine
import decisao_datas
import orquestrador_datas
import shadow_mode
import source_adapter
from auto_update_engine import AcaoAutoUpdate
from decisao_datas import Acao
from shadow_mode import executar_shadow_mode

AGORA = "2026-07-01T00:00:00+00:00"

_CAMPOS_OBRIGATORIOS = {
    "pagina", "estado", "decisao", "acao_prevista", "provider", "fonte",
    "confianca", "motivo", "resultado_auto_update", "alterou_algo", "shadow_mode",
}


def _alerta_ias(novo_valor=None, acao="AUTO_UPDATE", estado="OUTDATED_AUTOFIXABLE"):
    conteudo = "O valor de referência é IAS de 522,50 € (2025)."
    alerta = {
        "pagina": "abono-de-familia.html",
        "tipo": "valor_ias",
        "classificacao": {"data": "522,50 €", "estado": estado, "contexto": conteudo},
        "decisao": {"estado": estado, "acao": acao, "contexto": {}},
    }
    if novo_valor is not None:
        alerta["novo_valor"] = novo_valor
    return alerta


def _alerta_create_issue():
    return {
        "pagina": "bolsa-de-merito.html",
        "tipo": "ano_letivo",
        "classificacao": {
            "data": "2024/2025",
            "estado": "OUTDATED_REVIEW_REQUIRED",
            "contexto": "Bolsa de mérito para o ano lectivo 2024/2025.",
        },
        "decisao": {
            "estado": "OUTDATED_REVIEW_REQUIRED",
            "acao": "CREATE_ISSUE",
            "contexto": {},
        },
    }


@pytest.fixture(autouse=True)
def _flag_desligada_por_omissao(monkeypatch):
    # Garante que cada teste começa com a flag no estado por omissão,
    # independentemente da ordem de execução dos testes de outras camadas.
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", False)


# ── Estrutura do relatório ──────────────────────────────────────────────────

def test_relatorio_tem_todos_os_campos_pedidos():
    relatorio = executar_shadow_mode([_alerta_create_issue()], agora=AGORA)
    assert len(relatorio) == 1
    assert _CAMPOS_OBRIGATORIOS <= set(relatorio[0].keys())


def test_shadow_mode_e_alterou_algo_sao_sempre_marcados_corretamente():
    for alerta in (_alerta_ias(), _alerta_create_issue(), {}, None):
        for entrada in executar_shadow_mode([alerta], agora=AGORA):
            assert entrada["shadow_mode"] is True
            assert entrada["alterou_algo"] is False


def test_lista_vazia_devolve_relatorio_vazio():
    assert executar_shadow_mode([], agora=AGORA) == []


# ── Fluxo percorre todas as camadas existentes ─────────────────────────────

def test_fluxo_consulta_orquestrador_e_source_adapter(monkeypatch):
    chamadas = {"orquestrador": 0, "source_adapter": 0}

    orquestrador_original = orquestrador_datas.processar_alerta
    fonte_original = source_adapter.obter_valor_oficial

    def _espiao_orquestrador(alerta, **kwargs):
        chamadas["orquestrador"] += 1
        return orquestrador_original(alerta, **kwargs)

    def _espiao_fonte(alerta, **kwargs):
        chamadas["source_adapter"] += 1
        return fonte_original(alerta, **kwargs)

    monkeypatch.setattr(orquestrador_datas, "processar_alerta", _espiao_orquestrador)
    monkeypatch.setattr(source_adapter, "obter_valor_oficial", _espiao_fonte)

    executar_shadow_mode([_alerta_create_issue()], agora=AGORA)

    assert chamadas["orquestrador"] == 1
    assert chamadas["source_adapter"] == 1


def test_acao_prevista_reflete_decisao_do_orquestrador():
    relatorio = executar_shadow_mode([_alerta_create_issue()], agora=AGORA)[0]
    assert relatorio["decisao"] == "CREATE_ISSUE"
    assert relatorio["acao_prevista"] == Acao.CREATE_ISSUE


def test_provider_e_fonte_vem_do_source_adapter():
    relatorio = executar_shadow_mode([_alerta_ias(acao="IGNORAR")], agora=AGORA)[0]
    assert relatorio["provider"] == "seguranca_social"
    assert "seg-social.pt" in relatorio["fonte"]


def test_auto_update_elegivel_e_reportado_via_orquestrador(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    relatorio = executar_shadow_mode(
        [_alerta_ias(novo_valor="537,13 €")], agora=AGORA
    )[0]
    assert relatorio["acao_prevista"] == Acao.AUTO_UPDATE
    assert relatorio["resultado_auto_update"]["acao"] == AcaoAutoUpdate.AUTO_UPDATE_APPLIED
    assert relatorio["alterou_algo"] is False


def test_flag_desligada_por_omissao_faz_fallback_create_issue():
    # Confirma que o Shadow Mode NUNCA liga a flag por si próprio -- com
    # a configuração real (desligada), um alerta com decisão AUTO_UPDATE
    # tem de aparecer como CREATE_ISSUE (fallback do orquestrador), não
    # como AUTO_UPDATE.
    relatorio = executar_shadow_mode(
        [_alerta_ias(novo_valor="537,13 €")], agora=AGORA
    )[0]
    assert relatorio["acao_prevista"] == Acao.CREATE_ISSUE
    assert decisao_datas.AUTO_UPDATE_HABILITADO is False


# ── Isolamento: erro num alerta nunca interrompe os restantes ─────────────

def test_erro_no_source_adapter_nao_interrompe_os_restantes(monkeypatch):
    def _fonte_que_rebenta(alerta, **kwargs):
        raise RuntimeError("source adapter indisponível")

    monkeypatch.setattr(source_adapter, "obter_valor_oficial", _fonte_que_rebenta)

    alertas = [_alerta_ias(acao="IGNORAR"), _alerta_create_issue()]
    relatorio = executar_shadow_mode(alertas, agora=AGORA)

    assert len(relatorio) == 2
    assert relatorio[0]["provider"] is None
    assert "source adapter indisponível" in relatorio[0]["motivo"]
    # O segundo alerta continua a ser processado normalmente.
    assert relatorio[1]["pagina"] == "bolsa-de-merito.html"
    assert relatorio[1]["acao_prevista"] == Acao.CREATE_ISSUE


def test_erro_no_orquestrador_nao_interrompe_os_restantes(monkeypatch):
    def _orquestrador_que_rebenta(alerta, **kwargs):
        raise RuntimeError("orquestrador indisponível")

    monkeypatch.setattr(orquestrador_datas, "processar_alerta", _orquestrador_que_rebenta)

    alertas = [_alerta_ias(acao="IGNORAR"), _alerta_create_issue()]
    relatorio = executar_shadow_mode(alertas, agora=AGORA)

    assert len(relatorio) == 2
    assert relatorio[0]["acao_prevista"] == Acao.LOG_ONLY
    assert "orquestrador indisponível" in relatorio[0]["motivo"]
    assert relatorio[1]["pagina"] == "bolsa-de-merito.html"


def test_erro_no_auto_update_engine_nao_interrompe_os_restantes(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _engine_que_rebenta(alerta, **kwargs):
        raise RuntimeError("engine indisponível")

    monkeypatch.setattr(auto_update_engine, "aplicar_auto_update", _engine_que_rebenta)

    alertas = [_alerta_ias(novo_valor="537,13 €"), _alerta_create_issue()]
    relatorio = executar_shadow_mode(alertas, agora=AGORA)

    assert len(relatorio) == 2
    # O orquestrador já converte isto em fail-safe LOG_ONLY (Camada 5) --
    # nunca AUTO_UPDATE, e o shadow mode continua para o alerta seguinte.
    assert relatorio[0]["acao_prevista"] == Acao.LOG_ONLY
    assert relatorio[1]["pagina"] == "bolsa-de-merito.html"


def test_alerta_completamente_malformado_nao_interrompe_os_restantes():
    alertas = ["isto-nao-e-um-dict", _alerta_create_issue()]
    relatorio = executar_shadow_mode(alertas, agora=AGORA)

    assert len(relatorio) == 2
    assert relatorio[0]["estado"] == "ERRO"
    assert relatorio[0]["alterou_algo"] is False
    assert relatorio[1]["pagina"] == "bolsa-de-merito.html"


# ── Determinismo ────────────────────────────────────────────────────────────

def test_shadow_mode_e_deterministico():
    alertas = [_alerta_ias(acao="IGNORAR"), _alerta_create_issue()]
    resultados = [executar_shadow_mode(alertas, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


def test_shadow_mode_com_auto_update_elegivel_e_deterministico(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    alertas = [_alerta_ias(novo_valor="537,13 €")]
    resultados = [executar_shadow_mode(alertas, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


# ── Segurança: nenhuma escrita, nenhuma função destrutiva ──────────────────

def test_modulo_nunca_importa_os_subprocess_ou_shutil():
    assert not hasattr(shadow_mode, "os")
    assert not hasattr(shadow_mode, "subprocess")
    assert not hasattr(shadow_mode, "shutil")


def test_nenhuma_escrita_real_em_nenhum_cenario(monkeypatch):
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)

    def _bloqueado(*a, **k):
        raise AssertionError("shadow_mode tentou fazer I/O real ou destrutivo")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)
    monkeypatch.setattr(subprocess, "Popen", _bloqueado)
    import os
    monkeypatch.setattr(os, "remove", _bloqueado)
    monkeypatch.setattr(os, "system", _bloqueado)

    alertas = [
        _alerta_ias(novo_valor="537,13 €"),
        _alerta_create_issue(),
        _alerta_ias(acao="IGNORAR"),
        {},
        None,
    ]
    relatorio = executar_shadow_mode(alertas, agora=AGORA)
    assert len(relatorio) == 5
    assert all(r["alterou_algo"] is False for r in relatorio)


def test_nao_importa_nenhuma_biblioteca_de_acesso_ao_github():
    # A docstring do módulo menciona "GitHub Issues" em prosa (a explicar
    # o que o módulo NUNCA faz) -- por isso o que se verifica aqui não é
    # ausência da palavra no texto, mas sim ausência de qualquer `import`
    # de bibliotecas de acesso ao GitHub e de qualquer atributo desse
    # tipo no módulo já carregado.
    assert not hasattr(shadow_mode, "github")
    assert not hasattr(shadow_mode, "requests")
    assert not hasattr(shadow_mode, "PyGithub")

    codigo = Path(shadow_mode.__file__).read_text(encoding="utf-8")
    linhas_import = [
        linha.strip() for linha in codigo.splitlines()
        if linha.strip().startswith(("import ", "from "))
    ]
    proibidos = ("github", "requests", "pygithub", "gh_")
    for linha in linhas_import:
        assert not any(p in linha.lower() for p in proibidos), linha
