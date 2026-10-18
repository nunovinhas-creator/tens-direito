"""DATAS_PERMANENTES (`scripts/verificar_datas.py`, issue #332): datas que
são facto permanente de UMA página. Auto-auditoria no padrão de
EXCECOES_DIPLOMAS_FONTES: entrada órfã falha, motivo numa linha, e a
supressão nunca passa para outra página."""

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from auditar_marcadores_historicos import (  # noqa: E402
    MARCADOR_DATAS_PERMANENTES,
    supressoes_da_pagina,
)
from verificar_datas import DATAS_PERMANENTES, detectar_alertas  # noqa: E402

ENTRADAS = sorted(DATAS_PERMANENTES)


@pytest.mark.parametrize("pagina,data", ENTRADAS)
def test_entrada_nao_esta_orfa(pagina, data):
    caminho = RAIZ / pagina
    assert caminho.is_file(), f"DATAS_PERMANENTES: {pagina} não existe — entrada órfã"
    assert data in caminho.read_text(encoding="utf-8"), (
        f"DATAS_PERMANENTES: {data!r} já não aparece em {pagina} — entrada órfã, "
        f"apagar ou corrigir para a data como está agora no texto"
    )


@pytest.mark.parametrize("pagina,data", ENTRADAS)
def test_motivo_numa_linha(pagina, data):
    motivo = DATAS_PERMANENTES[(pagina, data)]
    assert motivo.strip() and "\n" not in motivo


def _frase_sem_marcadores(data):
    # Nenhum marcador histórico na janela, e uma tag a partir a frase.
    return f"<p>Conta <strong>a data de {data}</strong> para este efeito.</p>"


# Ano lectivo (PR D do #332) só é revisto em junho e julho.
MESES = (1, 6, 7, 8, 9)


@pytest.mark.parametrize("pagina,data", ENTRADAS)
def test_suprime_na_propria_pagina_independentemente_do_html(pagina, data):
    conteudo = _frase_sem_marcadores(data)
    for mes in MESES:
        assert detectar_alertas(conteudo, pagina, 2030, mes) is None


@pytest.mark.parametrize("pagina,data", ENTRADAS)
def test_mesma_data_noutra_pagina_nao_e_suprimida(pagina, data):
    mes = 6 if "/" in data and len(data) == 9 and data[4] == "/" else 1
    alerta = detectar_alertas(_frase_sem_marcadores(data), "outra-pagina.html", 2030, mes)
    assert alerta is not None and alerta["tipo"] in ("data_mes_ano", "data_numerica", "ano_letivo")


def test_outra_data_na_mesma_pagina_nao_e_suprimida():
    pagina, _ = ENTRADAS[0]
    alerta = detectar_alertas(_frase_sem_marcadores("3 de março de 2019"), pagina, 2030, 1)
    assert alerta is not None


def test_auditor_regista_a_supressao_com_rotulo_proprio():
    pagina, data = ENTRADAS[0]
    registos = supressoes_da_pagina(_frase_sem_marcadores(data), pagina, ano=2030)
    assert registos and {r["marcador"] for r in registos} == {MARCADOR_DATAS_PERMANENTES}
    assert supressoes_da_pagina(_frase_sem_marcadores(data), "outra-pagina.html", ano=2030) == []
