"""
Testes do parser do scraper do calendário (scripts/scraper_calendario.py).

`parse_innertext` é puro (sem rede) — testado com o texto REAL do painel
de agosto de 2026 capturado no diagnóstico de 2026-07-12 num runner
(ver docs/FONTE-CALENDARIO.md), nunca uma cópia inventada. Cobre também
os caminhos de falha (INVARIANTE — nenhum estado de erro pode parecer
sucesso): prestação fora da allow-list e mês vazio fazem falhar,
nunca são descartados em silêncio.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from scraper_calendario import ScraperError, parse_innertext  # noqa: E402

# Texto visível do painel "agosto 2026" exactamente como o runner o leu
# (innerText), incluindo os fragmentos "03"/"AGO" partidos do cabeçalho e
# os métodos concatenados ("Transferência bancáriaVale de correio").
AGOSTO_REAL = """junho 2026
julho 2026
agosto 2026
03 AGO
03
AGO
Doença Profissional: pensões e subsídios
Transferência bancáriaVale de correio
07 AGO
07
AGO
Rendas
Transferência bancária
Pensões
Transferência bancáriaVale de correio
Complemento Solidário para Idosos
Transferência bancáriaVale de correio
Reembolso de Despesas de Funeral
Transferência bancáriaVale de correio
Prestação Social para a Inclusão
Transferência bancáriaVale de correio
14 AGO
14
AGO
Prestações familiares
Transferência bancáriaVale de correio
1º pagamento desemprego / doença / parentalidade / ação social
Transferência bancáriaVale de correio
21 AGO
21
AGO
Subsídio por Suspensão da Atividade Cultural
Transferência bancáriaVale de correio
Fundo de Garantia de Alimentos Devidos a Menores
Transferência bancáriaVale de correio
Fundo de Garantia Salarial
Transferência bancária
Rendimento Social de Inserção
Transferência bancáriaVale de correio
28 AGO
28
AGO
2º pagamento desemprego / doença / parentalidade / ação social
Transferência bancáriaVale de correio
Subsídio de Apoio ao Cuidador Informal
Transferência bancáriaVale de correio
A sua opinião é importante
Partilhar opinião"""


def test_parse_agosto_real_estrutura_completa():
    m = parse_innertext(AGOSTO_REAL, 2026, 8)
    assert m["ano"] == 2026 and m["mes"] == 8
    dias = {p["dia"]: p for p in m["pagamentos"]}
    assert sorted(dias) == [3, 7, 14, 21, 28]

    assert dias[3]["prestacoes"] == ["doenca_profissional"]
    assert dias[3]["metodo"] == ["transferencia_bancaria", "vale_de_correio"]

    # dia 7 — pensões antecipadas (8 ago é sábado): rendas só transferência,
    # depois pensões/CSI/reembolso/PSI por transferência + vale
    assert dias[7]["prestacoes"] == [
        "apoio_renda", "pensoes", "csi", "reembolso_despesas_funeral", "psi",
    ]
    assert dias[7]["metodo"] == ["transferencia_bancaria", "vale_de_correio"]

    assert dias[14]["prestacoes"] == [
        "prestacoes_familiares", "desemprego_doenca_parentalidade_acao_social_1",
    ]
    assert dias[21]["prestacoes"] == [
        "subsidio_suspensao_atividade_cultural", "fgadm", "fgs", "rsi",
    ]
    assert dias[28]["prestacoes"] == [
        "desemprego_doenca_parentalidade_acao_social_2", "cuidador_informal",
    ]


def test_todos_os_slugs_extraidos_existem_na_allow_list():
    """Os slugs que o parser devolve têm de existir em PRESTACOES —
    senão o injector rejeita o mês na validação."""
    from atualizar_calendario import PRESTACOES
    m = parse_innertext(AGOSTO_REAL, 2026, 8)
    for p in m["pagamentos"]:
        for slug in p["prestacoes"]:
            assert slug in PRESTACOES, f"slug '{slug}' fora de PRESTACOES"


def test_metodo_so_transferencia_e_reconhecido():
    # "Rendas" é só transferência bancária — confirma que o parser distingue
    # "só transferência" de "transferência + vale" a nível de prestação/dia.
    texto = "07 JUL\n07\nJUL\nRendas\nTransferência bancária\nA sua opinião é importante"
    d = parse_innertext(texto, 2026, 7)
    assert d["pagamentos"] == [
        {"dia": 7, "prestacoes": ["apoio_renda"], "metodo": ["transferencia_bancaria"]}
    ]


# ── caminhos de falha (nunca só o caminho feliz) ──────────────────────────

def test_prestacao_desconhecida_faz_falhar_nunca_descarta():
    texto = (
        "03 AGO\n03\nAGO\n"
        "Prestação Inventada Que Não Existe\nTransferência bancária\n"
        "A sua opinião é importante"
    )
    with pytest.raises(ScraperError, match="allow-list"):
        parse_innertext(texto, 2026, 8)


def test_mes_sem_dias_faz_falhar():
    texto = "junho 2026\njulho 2026\nagosto 2026\nA sua opinião é importante"
    with pytest.raises(ScraperError, match="nenhum dia"):
        parse_innertext(texto, 2026, 8)


def test_dias_de_outro_mes_sao_ignorados():
    """Se por engano aparecerem dias de julho no texto ao pedir agosto,
    nunca entram no resultado de agosto."""
    texto = (
        "16 JUL\n16\nJUL\nPrestações familiares\nTransferência bancáriaVale de correio\n"
        "03 AGO\n03\nAGO\nDoença Profissional: pensões e subsídios\nTransferência bancáriaVale de correio\n"
        "A sua opinião é importante"
    )
    m = parse_innertext(texto, 2026, 8)
    assert [p["dia"] for p in m["pagamentos"]] == [3]


def test_metodo_sem_prestacao_faz_falhar():
    texto = "03 AGO\n03\nAGO\nTransferência bancária\nA sua opinião é importante"
    with pytest.raises(ScraperError, match="sem prestação"):
        parse_innertext(texto, 2026, 8)
