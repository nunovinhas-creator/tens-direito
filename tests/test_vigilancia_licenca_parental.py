"""Vigilância da proposta de alteração à licença parental (PR #330).

A secção "O que pode mudar" de subsidio-parental.html promete voltar a
confirmar o estado da proposta até 15 de novembro de 2026. Testa o efeito,
não a redacção: com a data simulada a 01/12/2026, verificar_datas.py tem de
dar alerta por causa dessa frase; a 14/10/2026 (dia da verificação), não.
"""
import re
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_REPO / "scripts"))

import verificar_datas as v  # noqa: E402

PAGINA = RAIZ_REPO / "subsidio-parental.html"
DATA = "15 de novembro de 2026"


def _html():
    return PAGINA.read_text(encoding="utf-8")


def _frase_da_data(html):
    """A frase (entre fins de frase/tags) que contém DATA."""
    ocorrencias = [m.start() for m in re.finditer(re.escape(DATA), html)]
    assert len(ocorrencias) == 1, f"esperada 1 ocorrência de {DATA!r}, encontradas {len(ocorrencias)}"
    i = ocorrencias[0]
    inicio = max(html.rfind(".", 0, i), html.rfind(">", 0, i)) + 1
    fim = html.index(".", i + len(DATA)) + 1
    return inicio, fim


def _frase_da_alerta(html, ano, mes):
    """Mesma decisão de _compromisso_futuro_expirado, restrita à frase da DATA."""
    inicio, fim = _frase_da_data(html)
    verificado_em = v.verificado_em_do_texto(html)
    for m in re.finditer(v.REGEX_COMPROMISSO_FUTURO, html, re.IGNORECASE):
        if not (inicio <= m.start() < fim):
            continue
        d = v._data_do_compromisso(m)
        if d is None or (d.year, d.month) >= (ano, mes):
            continue
        if v._esta_suprimido(html, m.start(), m.end(), ano, mes,
                             data_ocorrencia=d, verificado_em=verificado_em):
            continue
        return True
    return False


def test_sem_alerta_no_dia_da_verificacao():
    html = _html()
    assert not _frase_da_alerta(html, 2026, 10)
    assert v.detectar_alertas(html, PAGINA.name, 2026, 10) is None


def test_alerta_a_1_de_dezembro_de_2026():
    html = _html()
    assert _frase_da_alerta(html, 2026, 12), (
        f"a frase com {DATA!r} já não dá alerta em dezembro de 2026"
    )
    alerta = v.detectar_alertas(html, PAGINA.name, 2026, 12)
    assert alerta is not None and alerta["tipo"] == "compromisso_futuro"
