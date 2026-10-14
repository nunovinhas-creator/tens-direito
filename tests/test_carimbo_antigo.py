"""Regra própria para carimbos de verificação (issue #332).

A data de um carimbo ("Verificado a …") não entra na lógica de ano civil de
`_pagina_tem_alerta`; em vez disso, `carimbo_antigo` dispara quando um
carimbo tem mais de LIMITE_MESES_CARIMBO meses face ao mês de execução,
em qualquer mês. Testes de efeito, com a data de execução simulada.
"""
import glob
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import pytest  # noqa: E402

import verificar_datas as v  # noqa: E402


def _pagina(carimbo):
    return f"<main><p>Texto sem datas.</p><p class=\"verif\">{carimbo} pela redação do Tens Direito</p></main>"


def _tipo(html, ano, mes):
    alerta = v.detectar_alertas(html, "x.html", ano, mes)
    return alerta and alerta["tipo"]


@pytest.mark.parametrize("carimbo", [
    "Verificado a 02/09/2026",
    "Verificado a 2 de setembro de 2026",
    "Verificado a 2 setembro 2026",   # sem "de"
    "Verificado 02/09/2026",          # nota por secção, sem "a"
])
def test_carimbo_de_setembro_2026_so_alerta_passados_12_meses(carimbo):
    html = _pagina(carimbo)
    assert _tipo(html, 2027, 1) is None, "a data do carimbo não pode entrar na lógica de ano civil"
    assert _tipo(html, 2027, 9) is None, "12 meses certos ainda não é antigo"
    assert _tipo(html, 2027, 10) == "carimbo_antigo"


def test_carimbo_sem_de_e_detectado():
    assert [d.isoformat() for *_, d in v._carimbos(_pagina("Verificado a 14 outubro 2026"))] == ["2026-10-14"]


def test_alerta_em_qualquer_mes_fora_de_rever_em():
    # novembro não está em REVER_EM de nenhum tipo de data — o carimbo alerta na mesma
    assert 11 not in v.REVER_EM["data_mes_ano"]
    assert _tipo(_pagina("Verificado a 2 de setembro de 2026"), 2027, 11) == "carimbo_antigo"


def test_basta_um_carimbo_antigo_na_pagina():
    html = _pagina("Verificado a 2 de setembro de 2026") + "<p class=\"fonte-inline\">Verificado 24/06/2026</p>"
    assert _tipo(html, 2027, 6) is None
    assert _tipo(html, 2027, 7) == "carimbo_antigo"


def test_limite_vem_da_constante(monkeypatch):
    html = _pagina("Verificado a 2 de setembro de 2026")
    assert _tipo(html, 2027, 4) is None
    monkeypatch.setattr(v, "LIMITE_MESES_CARIMBO", 6)
    assert _tipo(html, 2027, 4) == "carimbo_antigo"


def test_data_fora_de_carimbo_continua_na_logica_de_ano_civil():
    html = "<p>As candidaturas fecharam a 2 de setembro de 2026.</p>"
    assert _tipo(html, 2027, 1) == "data_mes_ano"


def _paginas_reais():
    return sorted(glob.glob(str(RAIZ / "*.html")) + glob.glob(str(RAIZ / "p" / "*.html"))
                  + glob.glob(str(RAIZ / "documentos" / "*.html")))


@pytest.mark.parametrize("caminho", _paginas_reais(), ids=lambda c: os.path.relpath(c, RAIZ))
def test_carimbo_canonico_das_paginas_reais_e_reconhecido(caminho):
    html = Path(caminho).read_text(encoding="utf-8")
    canonico = v.verificado_em_do_texto(html)
    if canonico is None:
        return  # página sem carimbo — nada a reconhecer (sem skip, para não mexer na allow-list)
    assert canonico in {d for *_, d in v._carimbos(html)}
