"""Vigilância da proposta de alteração à licença parental (PR #330).

A secção "O que pode mudar" de subsidio-parental.html promete voltar a
confirmar o estado da proposta até 15 de novembro de 2026. Este teste
falha se essa data deixar de ser detectada por verificar_datas.py, se
deixar de ser tratada como pendente (MARCADORES_PENDENTE), ou se passar
a ser suprimida por outro marcador — em particular um marcador histórico
apanhado por proximidade, como acontece com "13 de outubro de 2026" no
aviso do topo (que fica perto do "Decreto-Lei n.º 91/2009" do carimbo).
"""
import re
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_REPO / "scripts"))

import verificar_datas as v  # noqa: E402

PAGINA = RAIZ_REPO / "subsidio-parental.html"
DATA = "15 de novembro de 2026"


def _ocorrencia():
    html = PAGINA.read_text(encoding="utf-8")
    ocorrencias = [m for m in re.finditer(re.escape(DATA), html)]
    assert len(ocorrencias) == 1, f"esperada 1 ocorrência de {DATA!r}, encontradas {len(ocorrencias)}"
    return html, ocorrencias[0]


def test_data_de_revisao_e_detectada_pelos_padroes():
    html, alvo = _ocorrencia()
    tipos = {
        p["tipo"]
        for p in v.PADROES
        if p["ano_grupo"] is not None
        for m in re.finditer(p["regex"], html, re.IGNORECASE)
        if m.start() <= alvo.start() < m.end() or alvo.start() <= m.start() < alvo.end()
    }
    assert {"data_mes_ano", "prazo_outono"} <= tipos


def test_data_de_revisao_so_tem_marcador_pendente():
    html, alvo = _ocorrencia()
    janela = v._janela_contexto(html, alvo.start(), alvo.end())
    assert v._tem_algum(v.MARCADORES_PENDENTE, janela)
    for nome in ("MARCADORES_HISTORICOS", "MARCADORES_ISENTOS_DO_PORTAO", "MARCADORES_EXEMPLO"):
        apanhados = [p for p in getattr(v, nome) if re.search(p, janela, re.IGNORECASE)]
        assert apanhados == [], f"{DATA!r} suprimida por {nome}: {apanhados}"


def test_data_de_revisao_pendente_ate_novembro_e_exposta_depois():
    html, alvo = _ocorrencia()
    assert v._esta_suprimido(html, alvo.start(), alvo.end(), 2026, 11) is True
    assert v._esta_suprimido(html, alvo.start(), alvo.end(), 2026, 12) is False
    assert v._esta_suprimido(html, alvo.start(), alvo.end(), 2027, 1) is False
