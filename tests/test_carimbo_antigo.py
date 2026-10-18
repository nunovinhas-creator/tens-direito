"""Regra própria para carimbos de verificação (issue #332).

A data de um carimbo ("Verificado a …") não entra na lógica de ano civil de
`_pagina_tem_alerta`; em vez disso, `carimbo_antigo` dispara quando um
carimbo tem mais de LIMITE_MESES_CARIMBO meses face ao mês de execução,
em qualquer mês. Testes de efeito, com a data de execução simulada.
"""
import glob
import os
import re
import sys
from datetime import date
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
    "Fontes verificadas — 2 de setembro de 2026",  # cabeçalho do bloco de fontes
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


# --- Outras formas de carimbo (#332, PR 3) ---------------------------------
# A data certifica conteúdo publicado, visível ou em comentário HTML/JS.

@pytest.mark.parametrize("carimbo", [
    "Última atualização: 2 de setembro de 2026",
    "Estado confirmado a 02/09/2026.",
    "Valores confirmados a 02/09/2026 no Guia Prático",
    "<!-- datas confirmadas a 02/09/2026 por triangulação -->",
    "Datas confirmadas na Segurança Social a 02/09/2026",
    "<!-- caminho conferido pelo Nuno a 02/09/2026 -->",
    "<script>// Valores confirmados por triangulação externa (02/09/2026): DECO</script>",
    "À data de verificação desta página (02/09/2026), não foi possível confirmar",
])
def test_outras_formas_de_carimbo_so_alertam_passados_12_meses(carimbo):
    html = _pagina(carimbo)
    assert _tipo(html, 2027, 1) is None, "a data do carimbo não pode entrar na lógica de ano civil"
    assert _tipo(html, 2027, 9) is None
    assert _tipo(html, 2027, 10) == "carimbo_antigo"


@pytest.mark.parametrize("frase", [
    "<p>A Provedoria pediu uma revisão urgente em agosto de 2025.</p>",
    "<p>Os valores actualizados produzem efeitos desde 1 de janeiro de 2026.</p>",
])
def test_frases_de_conteudo_nao_sao_carimbo(frase):
    assert v._carimbos(frase) == []
    assert _tipo(frase, 2028, 1) != "carimbo_antigo"


def test_portao_187_continua_a_ler_so_o_verificado_a():
    # Os carimbos de secção entram em carimbo_antigo, mas nunca em
    # verificado_em_do_texto (data canónica da página, portão do #187).
    html = ("<p>Estado confirmado a 14/10/2026.</p><p>Última atualização: 20 de outubro de 2026</p>"
            "<p>Verificado a 1 de julho de 2026 pela redação do Tens Direito</p>"
            "<!-- caminho conferido pelo Nuno a 05/10/2026 -->")
    assert v.verificado_em_do_texto(html) == date(2026, 7, 1)
    assert v.verificado_em_do_texto("<p>Última atualização: 4 de julho de 2026</p>") is None


@pytest.mark.parametrize("pagina, meses_sem_alerta, mes_alerta", [
    # «Última atualização: 13 de julho de 2026» é a única data da página
    ("privacidade.html", range(1, 8), 8),
    # carimbo em comentário HTML («caminho conferido pelo Nuno a 05/10/2026»)
    ("documentos/carta-acompanhamento-comunicacao-alteracao.html", range(1, 8), 8),
])
def test_paginas_reais_com_outras_formas(pagina, meses_sem_alerta, mes_alerta):
    html = (RAIZ / pagina).read_text(encoding="utf-8")
    for mes in meses_sem_alerta:
        assert _tipo(html, 2027, mes) is None, f"{pagina}: alerta inesperado em {mes}/2027"
    assert _tipo(html, 2027, mes_alerta) == "carimbo_antigo"


def _meses_depois(d, n):
    total = d.year * 12 + d.month - 1 + n
    return total // 12, total % 12 + 1


def test_calendario_data_confirmada_e_carimbo():
    # «Datas confirmadas na Segurança Social a DD/MM/AAAA» (gerado por
    # atualizar_calendario.py, reescrito todos os meses) é carimbo, não data
    # de ano civil; passados 12 meses sem actualização, dá carimbo_antigo.
    html = (RAIZ / "calendario-pagamentos-seguranca-social.html").read_text(encoding="utf-8")
    m = re.search(r"Datas confirmadas na Segurança Social a (\d{2})/(\d{2})/(\d{4})", html)
    assert m, "linha de dados do calendário não encontrada"
    d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    assert d in {c for *_, c in v._carimbos(html)}
    sintetica = _pagina(m.group(0))
    assert _tipo(sintetica, *_meses_depois(d, 12)) is None
    assert _tipo(sintetica, *_meses_depois(d, 13)) == "carimbo_antigo"
