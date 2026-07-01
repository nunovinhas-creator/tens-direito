"""
Testes para scripts/shadow_mode_analytics.py — ferramenta de análise e
métricas dos relatórios do Shadow Mode.

Cobertura pedida:
- contagem correta de estados
- agregação correta de ações
- consistência de output com inputs repetidos
- ausência de side effects (zero I/O)
- robustez a relatórios malformados
"""
import builtins
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import shadow_mode_analytics
from shadow_mode_analytics import (
    ACOES_CONHECIDAS,
    ESTADOS_CONHECIDOS,
    analisar_shadow_mode,
    comparar_execucoes,
    exportar_relatorio_json,
    filtrar_auto_update_candidatos,
)


def _relatorio(
    pagina="pagina.html",
    estado="OK",
    decisao="IGNORAR",
    acao_prevista="IGNORAR",
    provider=None,
    fonte=None,
    confianca=0.0,
    motivo="ok",
    resultado_auto_update=None,
):
    return {
        "pagina": pagina,
        "estado": estado,
        "decisao": decisao,
        "acao_prevista": acao_prevista,
        "provider": provider,
        "fonte": fonte,
        "confianca": confianca,
        "motivo": motivo,
        "resultado_auto_update": resultado_auto_update,
        "alterou_algo": False,
        "shadow_mode": True,
    }


# ── Contagem correta de estados ─────────────────────────────────────────────

def test_por_estado_pre_populado_com_as_5_categorias_conhecidas():
    analise = analisar_shadow_mode([])
    assert set(ESTADOS_CONHECIDOS) <= set(analise["por_estado"].keys())
    assert all(v == 0 for v in analise["por_estado"].values())


def test_contagem_correta_de_estados():
    relatorios = [
        _relatorio(estado="OK"),
        _relatorio(estado="OK"),
        _relatorio(estado="OUTDATED_AUTOFIXABLE"),
        _relatorio(estado="OUTDATED_REVIEW_REQUIRED"),
        _relatorio(estado="STATIC_REFERENCE"),
        _relatorio(estado="BLOCKED_SOURCE"),
        _relatorio(estado="BLOCKED_SOURCE"),
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["por_estado"]["OK"] == 2
    assert analise["por_estado"]["OUTDATED_AUTOFIXABLE"] == 1
    assert analise["por_estado"]["OUTDATED_REVIEW_REQUIRED"] == 1
    assert analise["por_estado"]["STATIC_REFERENCE"] == 1
    assert analise["por_estado"]["BLOCKED_SOURCE"] == 2
    assert analise["total_alertas"] == 7


def test_estado_desconhecido_e_contabilizado_como_categoria_extra():
    analise = analisar_shadow_mode([_relatorio(estado="ERRO")])
    assert analise["por_estado"]["ERRO"] == 1
    # As 5 categorias conhecidas continuam presentes, a 0.
    assert all(analise["por_estado"][e] == 0 for e in ESTADOS_CONHECIDOS)


# ── Agregação correta de ações ──────────────────────────────────────────────

def test_por_acao_pre_populado_com_as_4_categorias_conhecidas():
    analise = analisar_shadow_mode([])
    assert set(ACOES_CONHECIDAS) <= set(analise["por_acao"].keys())


def test_agregacao_correta_de_acoes():
    relatorios = [
        _relatorio(acao_prevista="IGNORAR"),
        _relatorio(acao_prevista="LOG_ONLY"),
        _relatorio(acao_prevista="LOG_ONLY"),
        _relatorio(acao_prevista="CREATE_ISSUE"),
        _relatorio(acao_prevista="CREATE_ISSUE"),
        _relatorio(acao_prevista="CREATE_ISSUE"),
        _relatorio(acao_prevista="AUTO_UPDATE"),
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["por_acao"] == {
        "IGNORAR": 1, "LOG_ONLY": 2, "CREATE_ISSUE": 3, "AUTO_UPDATE": 1,
    }


# ── AUTO_UPDATE elegíveis vs bloqueados e taxa de sucesso ──────────────────

def test_auto_update_elegiveis_e_bloqueados():
    relatorios = [
        _relatorio(decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE"),
        _relatorio(decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE"),
        _relatorio(decisao="AUTO_UPDATE", acao_prevista="CREATE_ISSUE"),
        _relatorio(decisao="AUTO_UPDATE", acao_prevista="LOG_ONLY"),
        _relatorio(decisao="CREATE_ISSUE", acao_prevista="CREATE_ISSUE"),  # não é candidato
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["auto_update_elegiveis"] == 2
    assert analise["auto_update_bloqueados"] == 2
    assert analise["taxa_sucesso_estimada"] == 0.5


def test_taxa_sucesso_sem_tentativas_e_zero_sem_crashar():
    analise = analisar_shadow_mode([_relatorio(decisao="IGNORAR")])
    assert analise["auto_update_elegiveis"] == 0
    assert analise["auto_update_bloqueados"] == 0
    assert analise["taxa_sucesso_estimada"] == 0.0


# ── Confiança média ──────────────────────────────────────────────────────────

def test_confianca_media_calculada_corretamente():
    relatorios = [
        _relatorio(confianca=0.0),
        _relatorio(confianca=1.0),
        _relatorio(confianca=0.5),
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["confianca_media"] == 0.5


def test_confianca_media_sem_relatorios_e_zero():
    assert analisar_shadow_mode([])["confianca_media"] == 0.0


# ── Erros e erros por provider ──────────────────────────────────────────────

def test_erros_contabilizados_por_estado_erro_ou_motivo():
    relatorios = [
        _relatorio(estado="ERRO", provider=None, motivo="erro inesperado em shadow mode"),
        _relatorio(estado="OK", provider="iefp", motivo="erro ao consultar source_adapter: x"),
        _relatorio(estado="OK", provider="seguranca_social", motivo="tudo bem"),
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["erros"] == 2
    assert analise["erros_por_provider"]["sem_provider"] == 1
    assert analise["erros_por_provider"]["iefp"] == 1
    assert "seguranca_social" not in analise["erros_por_provider"]


# ── Consistência com inputs repetidos (determinismo) ───────────────────────

def test_consistencia_com_inputs_repetidos():
    relatorios = [
        _relatorio(estado="OK", acao_prevista="IGNORAR"),
        _relatorio(estado="OUTDATED_AUTOFIXABLE", decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE", confianca=0.8),
        _relatorio(estado="BLOCKED_SOURCE", acao_prevista="LOG_ONLY"),
    ]
    resultados = [analisar_shadow_mode(relatorios) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


def test_lista_vazia_e_deterministica_e_zerada():
    esperado = {
        "total_alertas": 0,
        "por_estado": {e: 0 for e in ESTADOS_CONHECIDOS},
        "por_acao": {a: 0 for a in ACOES_CONHECIDAS},
        "auto_update_elegiveis": 0,
        "auto_update_bloqueados": 0,
        "taxa_sucesso_estimada": 0.0,
        "erros": 0,
        "erros_por_provider": {},
        "confianca_media": 0.0,
    }
    assert analisar_shadow_mode([]) == esperado
    assert analisar_shadow_mode(None) == esperado  # type: ignore[arg-type]


# ── Robustez a relatórios malformados ───────────────────────────────────────

def test_robustez_a_relatorios_malformados_nao_crasha():
    relatorios = [
        "isto-nao-e-um-dict",
        None,
        42,
        {},  # dict válido mas sem nenhum campo
        _relatorio(estado="OK"),
    ]
    analise = analisar_shadow_mode(relatorios)
    assert analise["total_alertas"] == 5
    # As 3 entradas não-dict contam como erro; o dict vazio não.
    assert analise["erros"] == 3
    assert analise["erros_por_provider"]["sem_provider"] == 3
    assert analise["por_estado"]["OK"] == 1
    assert analise["por_estado"].get("DESCONHECIDO") == 1  # o dict vazio


# ── Exportação JSON (sem escrita em disco) ─────────────────────────────────

def test_exportar_relatorio_json_produz_json_valido_equivalente():
    import json as json_stdlib

    analise = analisar_shadow_mode([_relatorio(estado="OK")])
    texto = exportar_relatorio_json(analise)
    assert isinstance(texto, str)
    assert json_stdlib.loads(texto) == analise


# ── Filtrar candidatos a AUTO_UPDATE ────────────────────────────────────────

def test_filtrar_auto_update_candidatos():
    relatorios = [
        _relatorio(pagina="a.html", decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE"),
        _relatorio(pagina="b.html", decisao="AUTO_UPDATE", acao_prevista="CREATE_ISSUE"),
        _relatorio(pagina="c.html", decisao="CREATE_ISSUE", acao_prevista="CREATE_ISSUE"),
        "malformado",
    ]
    candidatos = filtrar_auto_update_candidatos(relatorios)
    assert {c["pagina"] for c in candidatos} == {"a.html", "b.html"}


# ── Comparação atual vs anterior (delta) ────────────────────────────────────

def test_comparar_execucoes_delta_numerico_e_por_dict():
    atual = analisar_shadow_mode([
        _relatorio(estado="OK", acao_prevista="IGNORAR"),
        _relatorio(estado="OK", acao_prevista="IGNORAR"),
        _relatorio(estado="OUTDATED_AUTOFIXABLE", decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE"),
    ])
    anterior = analisar_shadow_mode([
        _relatorio(estado="OK", acao_prevista="IGNORAR"),
    ])
    delta = comparar_execucoes(atual, anterior)
    assert delta["total_alertas"] == 2
    assert delta["por_estado"]["OK"] == 1
    assert delta["por_acao"]["IGNORAR"] == 1
    assert delta["por_acao"]["AUTO_UPDATE"] == 1
    assert delta["auto_update_elegiveis"] == 1


def test_comparar_execucoes_com_dicts_vazios_nao_crasha():
    assert comparar_execucoes({}, {}) == {}
    assert comparar_execucoes(None, None) == {}  # type: ignore[arg-type]


def test_comparar_execucoes_campo_nao_numerico_nao_dict_fica_como_par():
    # Campo hipotético fora do schema actual (ex.: um texto livre) --
    # sem interpretação numérica possível, guarda os dois valores lado a
    # lado em vez de tentar subtraí-los.
    delta = comparar_execucoes({"versao": "v2"}, {"versao": "v1"})
    assert delta["versao"] == {"atual": "v2", "anterior": "v1"}


# ── Ausência de side effects (zero I/O) ─────────────────────────────────────

def test_modulo_nunca_importa_os_subprocess_ou_shutil():
    assert not hasattr(shadow_mode_analytics, "os")
    assert not hasattr(shadow_mode_analytics, "subprocess")
    assert not hasattr(shadow_mode_analytics, "shutil")


def test_modulo_nao_depende_de_shadow_mode_nem_de_outras_camadas():
    proibidos = {
        "shadow_mode", "verificar_datas", "classificar_datas",
        "decisao_datas", "auto_update_engine", "orquestrador_datas",
        "source_adapter",
    }
    assert not (proibidos & set(vars(shadow_mode_analytics).keys()))


def test_nenhuma_escrita_real_em_nenhuma_funcao_publica(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("shadow_mode_analytics tentou fazer I/O real")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)
    monkeypatch.setattr(subprocess, "Popen", _bloqueado)
    import os
    monkeypatch.setattr(os, "remove", _bloqueado)
    monkeypatch.setattr(os, "system", _bloqueado)

    relatorios = [
        _relatorio(estado="OK", decisao="AUTO_UPDATE", acao_prevista="AUTO_UPDATE"),
        _relatorio(estado="BLOCKED_SOURCE", provider="iefp"),
        "malformado",
    ]
    analise = analisar_shadow_mode(relatorios)
    exportar_relatorio_json(analise)
    filtrar_auto_update_candidatos(relatorios)
    comparar_execucoes(analise, analise)
    # Se algum "open"/"os.remove"/"subprocess.run" tivesse sido chamado,
    # o AssertionError acima já teria interrompido o teste.
