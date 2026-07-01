"""
Testes para scripts/decisao_datas.py — Camada 3, motor de decisão que
transforma estado em ação, sem executar qualquer efeito real.

Esta camada não cria Issues, não escreve ficheiros, não faz scraping —
só devolve uma string de ação. A validação de "não executa efeitos
reais" é feita bloqueando I/O (open/os) durante as chamadas e
confirmando que nada falha.
"""
import builtins
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import decisao_datas
from decisao_datas import (
    Acao,
    decidir_acao,
    decidir_acao_estruturada,
    decidir_intent,
)


# ── Mapping obrigatório estado -> ação (com a guarda de AUTO_UPDATE activa) ─

@pytest.mark.parametrize(
    "estado, acao_esperada",
    [
        ("OK", Acao.IGNORAR),
        ("STATIC_REFERENCE", Acao.IGNORAR),
        ("BLOCKED_SOURCE", Acao.LOG_ONLY),
        ("OUTDATED_REVIEW_REQUIRED", Acao.CREATE_ISSUE),
        # AUTO_UPDATE_HABILITADO é False por omissão -> despromovido para LOG_ONLY.
        ("OUTDATED_AUTOFIXABLE", Acao.LOG_ONLY),
    ],
)
def test_decidir_acao_mapping(estado, acao_esperada):
    assert decidir_acao(estado, {}) == acao_esperada


def test_estado_desconhecido_e_ignorado_por_falha_segura():
    assert decidir_acao("ALGO_QUE_NAO_EXISTE", {}) == Acao.IGNORAR


# ── Intent puro (sem guarda) ────────────────────────────────────────────────

@pytest.mark.parametrize(
    "estado, intent_esperado",
    [
        ("OK", Acao.IGNORAR),
        ("STATIC_REFERENCE", Acao.IGNORAR),
        ("BLOCKED_SOURCE", Acao.LOG_ONLY),
        ("OUTDATED_REVIEW_REQUIRED", Acao.CREATE_ISSUE),
        ("OUTDATED_AUTOFIXABLE", Acao.AUTO_UPDATE),
    ],
)
def test_decidir_intent_sem_guarda(estado, intent_esperado):
    assert decidir_intent(estado) == intent_esperado


def test_guarda_de_seguranca_esta_desligada_por_omissao():
    assert decisao_datas.AUTO_UPDATE_HABILITADO is False


def test_habilitar_guarda_deixa_passar_auto_update(monkeypatch):
    # Confirma que a guarda é mesmo o que impede AUTO_UPDATE de sair —
    # não um acidente do mapeamento. Isto NÃO liga a guarda em produção,
    # só dentro deste teste isolado (monkeypatch é revertido no fim).
    monkeypatch.setattr(decisao_datas, "AUTO_UPDATE_HABILITADO", True)
    assert decidir_acao("OUTDATED_AUTOFIXABLE", {}) == Acao.AUTO_UPDATE


# ── Determinismo ────────────────────────────────────────────────────────────

def test_decidir_acao_e_deterministica():
    resultados = {decidir_acao("OUTDATED_REVIEW_REQUIRED", {}) for _ in range(20)}
    assert len(resultados) == 1


def test_contexto_nao_influencia_a_decisao():
    # A decisão depende só do estado — dois contextos diferentes para o
    # mesmo estado têm de produzir a mesma ação.
    a1 = decidir_acao("OUTDATED_REVIEW_REQUIRED", {"pagina": "x.html"})
    a2 = decidir_acao("OUTDATED_REVIEW_REQUIRED", {"pagina": "y.html", "extra": 1})
    assert a1 == a2


# ── AUTO_UPDATE não executa nenhum efeito real ─────────────────────────────

def test_auto_update_nao_faz_io(monkeypatch):
    """Bloqueia open()/os.remove/os.system durante a chamada — se
    decidir_acao alguma vez tentar um efeito real, o teste falha com
    RuntimeError em vez de silenciosamente escrever nalgum lado."""
    import os

    def _open_bloqueado(*a, **k):
        raise RuntimeError("decidir_acao não deve fazer I/O")

    monkeypatch.setattr(builtins, "open", _open_bloqueado)
    monkeypatch.setattr(os, "remove", _open_bloqueado)
    monkeypatch.setattr(os, "system", _open_bloqueado)

    resultado = decidir_acao("OUTDATED_AUTOFIXABLE", {"data": "IAS de 522,50 €"})
    assert resultado == Acao.LOG_ONLY


def test_auto_update_estruturado_tambem_nao_faz_io(monkeypatch):
    def _open_bloqueado(*a, **k):
        raise RuntimeError("decidir_acao_estruturada não deve fazer I/O")

    monkeypatch.setattr(builtins, "open", _open_bloqueado)

    resultado = decidir_acao_estruturada("OUTDATED_AUTOFIXABLE", {"data": "2020"})
    assert resultado["acao"] == Acao.LOG_ONLY


# ── Estrutura intermédia {estado, acao, contexto} ──────────────────────────

def test_decidir_acao_estruturada_devolve_campos_esperados():
    contexto = {"data": "2024/2025", "estado": "OUTDATED_REVIEW_REQUIRED"}
    resultado = decidir_acao_estruturada("OUTDATED_REVIEW_REQUIRED", contexto)
    assert set(resultado.keys()) == {"estado", "acao", "contexto"}
    assert resultado["estado"] == "OUTDATED_REVIEW_REQUIRED"
    assert resultado["acao"] == Acao.CREATE_ISSUE
    assert resultado["contexto"] == contexto


def test_decidir_acao_estruturada_consistente_com_decidir_acao():
    for estado in (
        "OK",
        "STATIC_REFERENCE",
        "BLOCKED_SOURCE",
        "OUTDATED_REVIEW_REQUIRED",
        "OUTDATED_AUTOFIXABLE",
    ):
        contexto = {"estado": estado}
        esperado = decidir_acao(estado, contexto)
        resultado = decidir_acao_estruturada(estado, contexto)
        assert resultado["acao"] == esperado


# ── Integração em verificar_datas.detectar_alertas ─────────────────────────
# A decisão é só metadado anexado ao alerta — os campos que o pipeline usa
# para criar Issues (pagina/tipo/titulo/corpo) têm de continuar intactos.

def test_deteccao_alerta_anexa_decisao_sem_alterar_campos_existentes():
    from verificar_datas import detectar_alertas

    html = (
        "<html><body>Bolsa de mérito para o ano lectivo 2024/2025. "
        "Valor: 1.200,00 €. Verificado a 10 de outubro de 2024."
        "</body></html>"
    )
    alerta = detectar_alertas(html, "bolsa-de-merito.html", 2026, 7)

    assert alerta is not None
    assert alerta["pagina"] == "bolsa-de-merito.html"
    assert alerta["tipo"] in ("ano_letivo", "data_mes_ano")
    assert alerta["titulo"].startswith("📅 REVER: bolsa-de-merito.html")
    assert "classificacao" in alerta
    assert "decisao" in alerta
    assert alerta["decisao"]["estado"] == alerta["classificacao"]["estado"]
    assert alerta["decisao"]["acao"] in (
        Acao.IGNORAR,
        Acao.LOG_ONLY,
        Acao.CREATE_ISSUE,
    )
    # A decisão é anexada como metadado — não substitui nem remove os
    # campos que o pipeline lê para criar a Issue.
    assert "corpo" in alerta and "titulo" in alerta
