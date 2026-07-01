"""
Testes para scripts/classificar_datas.py — Camada 2, classificação
intermédia de datas/valores antes da decisão de criar Issue.

Esta camada não decide se uma Issue é criada (isso é
`verificar_datas.detectar_alertas`) — só atribui um dos 5 estados de
`EstadoData` com base em heurísticas de texto.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from classificar_datas import (
    EstadoData,
    classificar_data,
    classificar_data_estruturada,
)

ANO = 2026


# ── OK — data actual/futura, ou sem ano identificável ──────────────────────

def test_data_actual_e_ok():
    estado = classificar_data(
        "Verificado a 24 de junho de 2026.", "junho de 2026", ano_atual=ANO
    )
    assert estado == EstadoData.OK.value


def test_data_futura_e_ok():
    estado = classificar_data(
        "Candidaturas abrem em setembro de 2027.", "setembro de 2027", ano_atual=ANO
    )
    assert estado == EstadoData.OK.value


def test_sem_ano_identificavel_e_ok():
    estado = classificar_data("Política de privacidade.", "sem data", ano_atual=ANO)
    assert estado == EstadoData.OK.value


# ── STATIC_REFERENCE — referência legal/histórica, nunca expira ───────────

def test_diploma_legal_e_static_reference():
    estado = classificar_data(
        "Fonte: Portaria n.º 480-A/2025/1, de 30 de dezembro de 2025.",
        "dezembro de 2025",
        ano_atual=ANO,
    )
    assert estado == EstadoData.STATIC_REFERENCE.value


def test_facto_desde_ano_antigo_e_static_reference():
    estado = classificar_data(
        "Desde 2016/2017, os manuais escolares são gratuitos.",
        "2016/2017",
        ano_atual=ANO,
    )
    assert estado == EstadoData.STATIC_REFERENCE.value


# ── BLOCKED_SOURCE — conteúdo pendente de publicação oficial ──────────────

def test_aguarda_confirmacao_e_blocked_source():
    # Sem "despacho"/"portaria"/"lei" na janela — só sinal de pendência, para
    # não colidir com os marcadores históricos (que têm prioridade, tal como
    # em `verificar_datas._esta_suprimido`).
    estado = classificar_data(
        "O valor de 2025/2026 aguarda confirmação oficial, prevista para "
        "setembro de 2026.",
        "2025/2026",
        ano_atual=ANO,
    )
    assert estado == EstadoData.BLOCKED_SOURCE.value


def test_estimativa_provisoria_e_blocked_source():
    estado = classificar_data(
        "Valor estimado para 2024, ainda provisório.",
        "2024",
        ano_atual=ANO,
    )
    assert estado == EstadoData.BLOCKED_SOURCE.value


# ── OUTDATED_AUTOFIXABLE — valor com substituição mecânica conhecida ──────

def test_valor_ias_antigo_e_outdated_autofixable():
    estado = classificar_data(
        "O valor de referência é IAS de 522,50 € (2025).",
        "IAS de 522,50 €",
        ano_atual=ANO,
    )
    assert estado == EstadoData.OUTDATED_AUTOFIXABLE.value


def test_salario_minimo_antigo_e_outdated_autofixable():
    estado = classificar_data(
        "O salário mínimo em 2024 era de 820,00 €.",
        "2024",
        ano_atual=ANO,
    )
    assert estado == EstadoData.OUTDATED_AUTOFIXABLE.value


# ── OUTDATED_REVIEW_REQUIRED — resto do texto expirado ─────────────────────

def test_ano_letivo_antigo_e_outdated_review_required():
    estado = classificar_data(
        "Bolsa de mérito para o ano lectivo 2024/2025. Valor: 1.200,00 €.",
        "2024/2025",
        ano_atual=ANO,
    )
    assert estado == EstadoData.OUTDATED_REVIEW_REQUIRED.value


def test_prazo_antigo_sem_marcadores_e_outdated_review_required():
    estado = classificar_data(
        "As candidaturas encerraram a 15 de setembro de 2024.",
        "15 de setembro de 2024",
        ano_atual=ANO,
    )
    assert estado == EstadoData.OUTDATED_REVIEW_REQUIRED.value


# ── Determinismo ────────────────────────────────────────────────────────────

def test_classificacao_e_deterministica():
    contexto = "O subsídio mensal é de 400,00 €. Verificado a 15 de fevereiro de 2024."
    data = "15 de fevereiro de 2024"
    resultados = {classificar_data(contexto, data, ano_atual=ANO) for _ in range(20)}
    assert len(resultados) == 1


def test_ano_atual_omitido_usa_ano_corrente_real():
    # Sem ano_atual explícito, usa datetime.now().year — um ano claramente
    # muito antigo continua expirado seja qual for o ano de execução real.
    estado = classificar_data(
        "O subsídio mensal é de 400,00 €. Verificado a 15 de fevereiro de 2001.",
        "15 de fevereiro de 2001",
    )
    assert estado == EstadoData.OUTDATED_REVIEW_REQUIRED.value


# ── Estrutura intermédia {data, estado, contexto} ──────────────────────────

def test_classificar_data_estruturada_devolve_campos_esperados():
    contexto = "O valor de referência é IAS de 522,50 € (2025)."
    data = "IAS de 522,50 €"
    resultado = classificar_data_estruturada(contexto, data, ano_atual=ANO)
    assert set(resultado.keys()) == {"data", "estado", "contexto"}
    assert resultado["data"] == data
    assert resultado["contexto"] == contexto
    assert resultado["estado"] == EstadoData.OUTDATED_AUTOFIXABLE.value


def test_classificar_data_estruturada_consistente_com_classificar_data():
    contexto = "Bolsa de mérito para o ano lectivo 2024/2025."
    data = "2024/2025"
    esperado = classificar_data(contexto, data, ano_atual=ANO)
    resultado = classificar_data_estruturada(contexto, data, ano_atual=ANO)
    assert resultado["estado"] == esperado
