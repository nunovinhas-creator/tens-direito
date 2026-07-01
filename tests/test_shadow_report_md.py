"""
Testes para scripts/shadow_report_md.py — camada de apresentação em
Markdown dos resultados do Shadow Mode.

Cobertura pedida:
- output sempre string válida
- estrutura Markdown consistente
- funcionamento com analytics vazio
- funcionamento com erros/parciais
- determinismo (mesmo input -> mesmo output)
"""
import builtins
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import shadow_report_md
from shadow_report_md import NIVEIS_RISCO, gerar_relatorio_markdown

_TERMOS_TECNICOS_PROIBIDOS = ("payload", "dispatcher", "pipeline", "provider", "{", "}")


def _analytics(
    total_alertas=10,
    ok=6,
    outdated_autofixable=1,
    outdated_review_required=2,
    static_reference=0,
    blocked_source=1,
    auto_update_elegiveis=1,
    auto_update_bloqueados=0,
    erros=0,
    erros_por_provider=None,
    confianca_media=0.4,
):
    return {
        "total_alertas": total_alertas,
        "por_estado": {
            "OK": ok,
            "OUTDATED_AUTOFIXABLE": outdated_autofixable,
            "OUTDATED_REVIEW_REQUIRED": outdated_review_required,
            "STATIC_REFERENCE": static_reference,
            "BLOCKED_SOURCE": blocked_source,
        },
        "por_acao": {"IGNORAR": 6, "LOG_ONLY": 1, "CREATE_ISSUE": 2, "AUTO_UPDATE": 1},
        "auto_update_elegiveis": auto_update_elegiveis,
        "auto_update_bloqueados": auto_update_bloqueados,
        "taxa_sucesso_estimada": 1.0,
        "erros": erros,
        "erros_por_provider": erros_por_provider or {},
        "confianca_media": confianca_media,
    }


# ── Output sempre string válida ─────────────────────────────────────────────

def test_output_e_sempre_string():
    assert isinstance(gerar_relatorio_markdown(_analytics()), str)


def test_output_nao_esta_vazio():
    assert len(gerar_relatorio_markdown(_analytics()).strip()) > 0


# ── Estrutura Markdown consistente ──────────────────────────────────────────

def test_estrutura_tem_todas_as_seccoes_pedidas():
    texto = gerar_relatorio_markdown(_analytics())
    for seccao in (
        "# 📊 Relatório do Sistema — Shadow Mode",
        "## Resumo geral",
        "## Distribuição dos alertas",
        "## Auto-update (simulado)",
        "## Avaliação do sistema",
        "## Observações importantes",
    ):
        assert seccao in texto


def test_estrutura_contem_valores_esperados():
    texto = gerar_relatorio_markdown(_analytics())
    assert "Alertas analisados: 10" in texto
    assert "Confiança média do sistema: 40%" in texto
    assert "Elegíveis: 1" in texto
    assert "Bloqueados por segurança: 0" in texto


def test_nao_contem_termos_tecnicos_nem_json():
    texto = gerar_relatorio_markdown(_analytics(erros=2, erros_por_provider={"iefp": 2}))
    minusculas = texto.lower()
    for termo in _TERMOS_TECNICOS_PROIBIDOS:
        assert termo not in minusculas, f"termo técnico '{termo}' encontrado no relatório"


def test_data_opcional_aparece_quando_fornecida():
    texto = gerar_relatorio_markdown(_analytics(), data="2026-07-01")
    assert "2026-07-01" in texto


def test_sem_data_nao_ha_referencia_a_data_no_relatorio():
    texto = gerar_relatorio_markdown(_analytics())
    assert "Gerado a:" not in texto


def test_rodape_de_seguranca_presente():
    texto = gerar_relatorio_markdown(_analytics())
    assert "nenhuma alteração real foi feita" in texto.lower()


# ── Risco / avaliação coerentes ─────────────────────────────────────────────

def test_risco_alto_quando_ha_erros():
    texto = gerar_relatorio_markdown(_analytics(erros=1))
    assert "Risco global: ALTO" in texto
    assert "não ativar" in texto


def test_risco_medio_com_fonte_bloqueada_sem_erros():
    texto = gerar_relatorio_markdown(_analytics(erros=0, blocked_source=3))
    assert "Risco global: MÉDIO" in texto
    assert "manter em observação" in texto


def test_risco_medio_so_com_casos_para_revisao_sem_fonte_bloqueada():
    texto = gerar_relatorio_markdown(
        _analytics(erros=0, blocked_source=0, outdated_review_required=4)
    )
    assert "Risco global: MÉDIO" in texto
    assert "precisam de ser revistos por uma pessoa" in texto


def test_risco_baixo_sem_problemas():
    texto = gerar_relatorio_markdown(
        _analytics(ok=10, outdated_autofixable=0, outdated_review_required=0,
                   blocked_source=0, erros=0, auto_update_elegiveis=0)
    )
    assert "Risco global: BAIXO" in texto


def test_recomenda_ativar_apenas_com_risco_baixo_e_confianca_alta():
    texto = gerar_relatorio_markdown(
        _analytics(ok=10, outdated_autofixable=1, outdated_review_required=0,
                   blocked_source=0, erros=0, auto_update_elegiveis=2,
                   confianca_media=0.9)
    )
    assert "Risco global: BAIXO" in texto
    assert "Recomendação: ativar" in texto


def test_niveis_risco_conhecidos():
    assert NIVEIS_RISCO == ("BAIXO", "MÉDIO", "ALTO")


# ── Analytics vazio ──────────────────────────────────────────────────────────

def test_analytics_vazio_nao_crasha_e_devolve_relatorio_coerente():
    texto = gerar_relatorio_markdown({})
    assert isinstance(texto, str)
    assert "Alertas analisados: 0" in texto
    assert "Risco global: BAIXO" in texto


def test_analytics_none_nao_crasha():
    texto = gerar_relatorio_markdown(None)  # type: ignore[arg-type]
    assert isinstance(texto, str)
    assert "# 📊 Relatório do Sistema — Shadow Mode" in texto


# ── Analytics parcial / malformado ─────────────────────────────────────────

def test_analytics_parcial_sem_confianca_nem_por_estado():
    texto = gerar_relatorio_markdown({"total_alertas": 3, "erros": 0})
    assert isinstance(texto, str)
    assert "Alertas analisados: 3" in texto
    assert "Confiança média do sistema: 0%" in texto


def test_analytics_com_tipos_invalidos_nao_crasha():
    analytics_malformado = {
        "total_alertas": "muitos",
        "por_estado": "isto-nao-e-um-dict",
        "confianca_media": None,
        "erros": [1, 2, 3],
        "auto_update_elegiveis": {},
    }
    texto = gerar_relatorio_markdown(analytics_malformado)
    assert isinstance(texto, str)
    assert len(texto.strip()) > 0


def test_erros_por_fonte_usa_nomes_amigaveis():
    texto = gerar_relatorio_markdown(
        _analytics(erros=3, erros_por_provider={"seguranca_social": 2, "sem_provider": 1})
    )
    assert "Segurança Social (2)" in texto
    assert "sem fonte identificada (1)" in texto
    assert "seguranca_social" not in texto


# ── Determinismo ─────────────────────────────────────────────────────────────

def test_determinismo_mesmo_input_mesmo_output():
    analytics = _analytics(erros=1, erros_por_provider={"dge": 1})
    resultados = [gerar_relatorio_markdown(analytics, data="2026-07-01") for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


def test_determinismo_sem_data_e_sempre_igual_independente_do_relogio():
    analytics = _analytics()
    r1 = gerar_relatorio_markdown(analytics)
    r2 = gerar_relatorio_markdown(analytics)
    assert r1 == r2


# ── Segurança: sem I/O, sem dependências de outras camadas ─────────────────

def test_modulo_nunca_importa_os_subprocess_ou_shutil():
    assert not hasattr(shadow_report_md, "os")
    assert not hasattr(shadow_report_md, "subprocess")
    assert not hasattr(shadow_report_md, "shutil")


def test_modulo_nao_depende_de_nenhuma_outra_camada_do_sistema():
    proibidos = {
        "shadow_mode", "shadow_mode_analytics", "verificar_datas",
        "classificar_datas", "decisao_datas", "auto_update_engine",
        "orquestrador_datas", "source_adapter",
    }
    assert not (proibidos & set(vars(shadow_report_md).keys()))


def test_nenhuma_escrita_real_ao_gerar_relatorio(monkeypatch):
    def _bloqueado(*a, **k):
        raise AssertionError("shadow_report_md tentou fazer I/O real")

    monkeypatch.setattr(builtins, "open", _bloqueado)
    monkeypatch.setattr(subprocess, "run", _bloqueado)
    monkeypatch.setattr(subprocess, "Popen", _bloqueado)
    import os
    monkeypatch.setattr(os, "remove", _bloqueado)
    monkeypatch.setattr(os, "system", _bloqueado)

    texto = gerar_relatorio_markdown(_analytics(erros=2, erros_por_provider={"iefp": 2}))
    assert isinstance(texto, str) and len(texto) > 0
