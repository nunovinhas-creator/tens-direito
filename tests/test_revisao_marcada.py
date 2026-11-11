"""`data-rever-ate` — revisão marcada de estados legislativos pendentes (#331).

Regras para TODAS as páginas servidas:
1. O bloco `.aviso-lei` é o lugar de uma lei aprovada no Parlamento e
   ainda não publicada; quem o usa tem de marcar a data da próxima revisão em `data-rever-ate`. Esperas por
   portaria/regulamentação têm o seu próprio canário (test_espera_legal.py,
   marcador ESPERA-LEGAL) e os sentinelas DRE — não entram aqui.
2. Cada `data-rever-ate` é uma data ISO válida, nunca anterior ao carimbo
   "Verificado a" da página e no máximo `MAX_DIAS` depois — impede escapar à
   vigilância com uma data longínqua, e uma revisão sem carimbo novo.
3. `verificar_datas` alerta quando a data passa (qualquer mês), quando o
   valor é inválido, e nunca antes.
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_REPO / "scripts"))

import verificar_datas as v  # noqa: E402
from sincronizar_clusters import encontrar_paginas, verificado_em_do_texto  # noqa: E402

MAX_DIAS = 120
REGEX_PENDENTE = re.compile(r'class="aviso-lei"')

PAGINAS = sorted(encontrar_paginas(RAIZ_REPO))


@pytest.mark.parametrize("caminho", PAGINAS, ids=lambda p: str(p.relative_to(RAIZ_REPO)))
def test_estado_pendente_tem_revisao_marcada(caminho):
    html = caminho.read_text(encoding="utf-8")
    if not REGEX_PENDENTE.search(html):
        return
    assert v.revisoes_marcadas(html), (
        f"{caminho.name} descreve lei aprovada e por publicar mas não tem data-rever-ate"
    )


@pytest.mark.parametrize("caminho", PAGINAS, ids=lambda p: str(p.relative_to(RAIZ_REPO)))
def test_revisao_marcada_valida_e_proxima_do_carimbo(caminho):
    html = caminho.read_text(encoding="utf-8")
    revs = v.revisoes_marcadas(html)
    if not revs:
        return
    verificado = verificado_em_do_texto(html)
    assert verificado is not None, f"{caminho.name}: data-rever-ate sem carimbo 'Verificado a'"
    for bruto, d in revs:
        assert d is not None, f"{caminho.name}: data-rever-ate inválido {bruto!r}"
        assert verificado <= d <= verificado + timedelta(days=MAX_DIAS), (
            f"{caminho.name}: data-rever-ate {bruto} fora de [{verificado}, +{MAX_DIAS} dias]"
        )


def _pagina(rever):
    return (
        "<html><body><p>Verificado a 11 de novembro de 2026 pela redação.</p>"
        f'<div class="aviso-lei" data-rever-ate="{rever}">Lei aprovada, ainda não está em vigor.</div>'
        "</body></html>"
    )


def test_sem_alerta_ate_ao_proprio_dia():
    html = _pagina("2026-12-15")
    assert v.detectar_alertas(html, "x.html", 2026, 11, dia=11) is None
    assert v.detectar_alertas(html, "x.html", 2026, 12, dia=15) is None


def test_alerta_no_dia_seguinte():
    alerta = v.detectar_alertas(_pagina("2026-12-15"), "x.html", 2026, 12, dia=16)
    assert alerta["tipo"] == "revisao_marcada"
    assert "2026-12-15" in alerta["corpo"]


def test_sem_dia_compara_ao_mes():
    html = _pagina("2026-12-15")
    assert v.detectar_alertas(html, "x.html", 2026, 12) is None
    assert v.detectar_alertas(html, "x.html", 2027, 1)["tipo"] == "revisao_marcada"


@pytest.mark.parametrize("mes", range(1, 13))
def test_alerta_em_qualquer_mes_depois_do_prazo(mes):
    alerta = v.detectar_alertas(_pagina("2026-12-15"), "x.html", 2027, mes, dia=1)
    assert alerta is not None and alerta["tipo"] == "revisao_marcada"


@pytest.mark.parametrize("bruto", ["", "15/12/2026", "2026-13-01", "2026-02-30", "brevemente"])
def test_valor_invalido_alerta_sempre(bruto):
    alerta = v.detectar_alertas(_pagina(bruto), "x.html", 2026, 11, dia=11)
    assert alerta is not None and alerta["tipo"] == "revisao_marcada"


def test_marcadores_de_supressao_nao_escondem_a_revisao():
    """'confirmar', 'aguarda', 'desde', diplomas por perto — nada disso suprime."""
    html = (
        "<p>Verificado a 11 de novembro de 2026.</p>"
        '<div data-rever-ate="2026-12-15">Aguarda publicação; voltamos a confirmar. '
        "Em vigor desde 1 de janeiro de 2026 (Decreto-Lei n.º 91/2009).</div>"
    )
    alerta = v.detectar_alertas(html, "x.html", 2026, 12, dia=16)
    assert alerta is not None and alerta["tipo"] == "revisao_marcada"


def test_um_so_alerta_por_pagina_mesmo_com_varias_revisoes():
    html = _pagina("2026-12-15") + '<p data-rever-ate="2026-12-20"></p>'
    alerta = v.detectar_alertas(html, "x.html", 2027, 1, dia=5)
    assert alerta["tipo"] == "revisao_marcada"
    assert "2026-12-15" in alerta["corpo"] and "2026-12-20" in alerta["corpo"]
