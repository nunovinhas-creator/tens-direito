"""MARCADORES_ISENTOS_DO_PORTAO (issue #186) — datas fixadas por lei,
citadas como facto permanente, que `_esta_suprimido()` suprime antes do
portão de confirmação (#183).

Cobre as duas direcções: as formulações permanentes do cluster PSU deixam de
alertar em 2027, e as frases prospectivas (issue #293) continuam expostas."""
import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from auditar_marcadores_historicos import supressoes_da_pagina  # noqa: E402
from sincronizar_clusters import verificado_em_do_texto  # noqa: E402
from verificar_datas import (  # noqa: E402
    MARCADORES_HISTORICOS,
    MARCADORES_ISENTOS_DO_PORTAO,
    PADROES,
    REVER_EM,
    _data_da_ocorrencia,
    _esta_suprimido,
    detectar_alertas,
)

TIPOS_COM_DATA = ("data_mes_ano", "data_numerica", "prazo_outono")


def _html(corpo: str) -> str:
    return f"<html><body>{corpo}</body></html>"


def _ler(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


def _ocorrencias(conteudo: str, contexto: str | None = None):
    """(padrao, match) de 31/12/2026 e variantes, opcionalmente só as que têm
    `contexto` nos 200 caracteres à volta."""
    for padrao in PADROES:
        if padrao["tipo"] not in TIPOS_COM_DATA:
            continue
        for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
            if "2026" not in m.group(0) or not ("dezembro" in m.group(0).lower() or "31/12" in m.group(0)):
                continue
            if contexto is not None and contexto not in conteudo[max(0, m.start() - 200):m.end() + 200]:
                continue
            yield padrao, m


def _suprimida_em(conteudo, padrao, m, ano, mes):
    return _esta_suprimido(
        conteudo, m.start(), m.end(), ano, mes,
        data_ocorrencia=_data_da_ocorrencia(padrao, m),
        verificado_em=verificado_em_do_texto(conteudo),
    )


# ── Contenção ───────────────────────────────────────────────────────────────

def test_isentos_estao_contidos_em_marcadores_historicos():
    """Cada marcador isento também é histórico — é isso que o põe no
    baseline auditado (test_auditar_marcadores_historicos.py)."""
    fora = [m for m in MARCADORES_ISENTOS_DO_PORTAO if m not in MARCADORES_HISTORICOS]
    assert fora == []


def test_isentos_sem_duplicados():
    assert len(MARCADORES_ISENTOS_DO_PORTAO) == len(set(MARCADORES_ISENTOS_DO_PORTAO))


# ── Unidade: isento vs. histórico normal ────────────────────────────────────

FRASE_ISENTA = ("O artigo 63.º do Decreto-Lei n.º 166/2026 fixa 31 de dezembro de 2026 "
                "como data de produção de efeitos. Verificado a 15 de setembro de 2026.")
FRASE_SO_HISTORICA = ("O Decreto-Lei n.º 166/2026 paga a partir de 31 de dezembro de 2026. "
                      "Verificado a 15 de setembro de 2026.")


@pytest.mark.parametrize("mes", REVER_EM["data_mes_ano"])
def test_isento_suprime_data_posterior_ao_carimbo_depois_de_passar(mes):
    assert detectar_alertas(_html(FRASE_ISENTA), "sintetica.html", 2027, mes) is None


def test_controlo_marcador_historico_normal_continua_sujeito_ao_portao():
    """Sem marcador isento, o mesmo "Decreto-Lei" deixa a data exposta em
    2027 — o portão continua activo para tudo o resto."""
    assert detectar_alertas(_html(FRASE_SO_HISTORICA), "sintetica.html", 2027, 1) is not None


@pytest.mark.parametrize("frase", [
    "o artigo 63.º fixa 31 de dezembro de 2026 como a data de produção de efeitos",
    "produção de efeitos a 31/12/2026 (art. 63.º)",
    "produção de efeitos a 31/12/2026 (artigo 63.º)",
    "Produção de efeitos: 31/12/2026",
    "a lei fixa-a como um evento único a 31 de dezembro de 2026",
    "com data fixada por lei para 31 de dezembro de 2026",
    "tem data fixada por lei, como evento único, a 31 de dezembro de 2026",
])
def test_cada_formulacao_permanente_e_isenta(frase):
    html = _html(f"<p>{frase}. Verificado a 15 de setembro de 2026.</p>")
    assert detectar_alertas(html, "sintetica.html", 2027, 1) is None


@pytest.mark.parametrize("frase", [
    "Pagamento efectivo a partir de 31/12/2026 (produção de efeitos, artigo 63.º)",
    "Até 31 de dezembro de 2026 (data de produção de efeitos do decreto-lei), mantém-se a prestação actual",
    "o mesmo artigo fixa a data de produção de efeitos em 31 de dezembro de 2026",
    "a lei fixa essa conversão para 31 de dezembro de 2026",
])
def test_formulacoes_prospectivas_nunca_sao_isentas(frase):
    html = _html(f"<p>Decreto-Lei n.º 166/2026: {frase}. Verificado a 15 de setembro de 2026.</p>")
    assert detectar_alertas(html, "sintetica.html", 2027, 1) is not None


# ── Páginas reais ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("pagina", [
    "psu-quem-tem-direito.html", "psu-vs-abono-familia.html", "simulador-psu.html",
])
def test_paginas_186_todas_as_ocorrencias_de_31_12_2026_suprimidas_em_2027(pagina):
    conteudo = _ler(pagina)
    ocorrencias = list(_ocorrencias(conteudo))
    assert ocorrencias, "a página deixou de citar 31/12/2026 — rever este teste"
    expostas = [m.group(0) for p, m in ocorrencias if not _suprimida_em(conteudo, p, m, 2027, 1)]
    assert expostas == []


@pytest.mark.parametrize("mes", sorted(set(REVER_EM["data_numerica"]) | set(REVER_EM["data_mes_ano"])))
def test_psu_vs_abono_familia_sem_alerta_em_2027(mes):
    assert detectar_alertas(_ler("psu-vs-abono-familia.html"), "psu-vs-abono-familia.html", 2027, mes) is None


@pytest.mark.parametrize("pagina,contexto", [
    ("como-pedir-psu.html", "pedido aprovado antes dessa data fica a aguardar"),
    ("calendario-pagamentos-psu.html", "Pagamento efectivo a partir de 31/12/2026"),
    ("prestacao-social-unica.html", "mantém-se a prestação actual para todos os 13 apoios"),
    ("psu-lista-13-apoios.html", "com regime transitório garantido até lá"),
    ("psu-quando-entra-em-vigor.html", "é só a partir dessa data que a PSU passa a ser paga de facto"),
    ("simulador-rsi.html", "enquanto isso não acontecer"),
])
def test_frases_prospectivas_continuam_expostas_em_2027(pagina, contexto):
    """Issue #293: estas frases só são verdade antes de 31/12/2026 — têm de
    alertar em 2027 para serem reescritas."""
    conteudo = _ler(pagina)
    ocorrencias = list(_ocorrencias(conteudo, contexto))
    assert ocorrencias, f"contexto não encontrado em {pagina}: {contexto!r}"
    assert any(not _suprimida_em(conteudo, p, m, 2027, 1) for p, m in ocorrencias)


# ── Auditoria ───────────────────────────────────────────────────────────────

def test_auditoria_regista_isento_mesmo_com_data_nao_antiga():
    """31/12/2026 não é "antiga" face a ANO_REFERENCIA = 2026, mas é
    posterior ao carimbo — a supressão isenta tem de aparecer no baseline já
    hoje, não só depois de a data passar."""
    registos = supressoes_da_pagina(_html(FRASE_ISENTA), "sintetica.html", ano=2026)
    marcadores = {r["marcador"] for r in registos}
    assert marcadores == {MARCADORES_ISENTOS_DO_PORTAO[0]}


def test_auditoria_nao_atribui_historicos_normais_a_data_posterior_ao_carimbo():
    """Na mesma janela há "decreto-lei", mas esse marcador não suprime uma
    data posterior ao carimbo — só o isento é atribuído."""
    registos = supressoes_da_pagina(_html(FRASE_ISENTA), "sintetica.html", ano=2026)
    assert "decreto-lei" not in {r["marcador"] for r in registos}


def test_auditoria_ignora_isento_sem_carimbo_posterior():
    """Data anterior ou igual ao carimbo e não antiga: nada a suprimir."""
    html = _html("O artigo 63.º fixa 31 de dezembro de 2026 como data de produção de efeitos. "
                 "Verificado a 31 de dezembro de 2026.")
    assert supressoes_da_pagina(html, "sintetica.html", ano=2026) == []


def test_data_posterior_ao_carimbo_e_a_condicao_da_auditoria():
    assert verificado_em_do_texto(_html(FRASE_ISENTA)) == date(2026, 9, 15)
