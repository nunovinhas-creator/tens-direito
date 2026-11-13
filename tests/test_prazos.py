"""
data/prazos.json → etiqueta «Prazo a decorrer» e cartões «Datas a não
perder» (scripts/prazos.py, gerados por scripts/sincronizar_clusters.py).

1. O ficheiro real valida: cada frase existe na página e cita a data de
   fim — se a página mudar o prazo, este teste falha (vigilância).
2. Os caminhos de falha da validação (frase ausente, data que a frase não
   cita, permanente com mês, anual com ano, fixa sem ano…).
3. As páginas reais estão sincronizadas com o gerador: a zona
   PRAZOS:HOME da homepage e as listas de guias são exactamente o que o
   script escreveria (o HTML não depende da data de hoje).
4. «Tem simulador»: o simulador existe, é uma ferramenta, e a página
   liga-lhe.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import prazos as P  # noqa: E402
import sincronizar_clusters as S  # noqa: E402


def _prazo(**kw) -> P.Prazo:
    base = dict(
        id="x", pagina="prova-escolar.html", tipo="prazo", icone="📋", titulo="Teste",
        texto="Até 31 de dezembro de 2026.", frase="Se a entregares até 31 de dezembro",
        inicio=None, fim="2026-12-31",
    )
    base.update(kw)
    return P.Prazo(**base)


# ── 1. Ficheiro real ─────────────────────────────────────────────────────


def test_prazos_reais_validam():
    assert P.validar(P.carregar_prazos()) == []


def test_ficheiro_real_tem_nota_explicativa():
    dados = json.loads(P.PRAZOS_JSON.read_text(encoding="utf-8"))
    assert "frase" in dados["_nota"] and "sincronizar_clusters" in dados["_nota"]


# ── 2. Caminhos de falha ─────────────────────────────────────────────────


def test_frase_que_ja_nao_esta_na_pagina_falha():
    erros = P.validar([_prazo(frase="até 31 de dezembro e uma frase que não existe")])
    assert any("já não está em prova-escolar.html" in e for e in erros)


def test_frase_sem_a_data_de_fim_falha():
    erros = P.validar([_prazo(frase="recebes os meses em atraso", fim="2026-12-31")])
    assert any("não cita a data de fim" in e for e in erros)


def test_fim_de_mes_aceita_fim_de():
    assert P.frase_tem_a_data("ficam fixados no fim de dezembro de 2026", P.date(2026, 12, 31))
    assert not P.frase_tem_a_data("ficam fixados no fim de dezembro", P.date(2026, 12, 30))


def test_pagina_inexistente_falha():
    assert any("não existe" in e for e in P.validar([_prazo(pagina="nao-existe.html")]))


def test_tipo_desconhecido_falha():
    assert any("desconhecido" in e for e in P.validar([_prazo(tipo="urgente")]))


def test_id_repetido_falha():
    assert any("repetido" in e for e in P.validar([_prazo(), _prazo()]))


def test_permanente_com_mes_ou_datas_falha():
    erros = P.validar([_prazo(id="p", tipo="permanente", fim=None, texto="Pede em setembro.")])
    assert any("nome de mês" in e for e in erros)
    erros = P.validar([_prazo(id="p", tipo="permanente", texto="Pede quando quiseres.")])
    assert any("não tem datas" in e for e in erros)


def test_data_fixa_sem_ano_no_texto_falha():
    erros = P.validar([_prazo(texto="Até 31 de dezembro.")])
    assert any("sem o ano" in e for e in erros)


def test_anual_com_ano_no_texto_falha():
    erros = P.validar([_prazo(recorrente="anual", inicio="08-01", fim="12-31",
                              texto="Até 31 de dezembro de 2026.")])
    assert any("prazo anual com ano" in e for e in erros)


def test_formatos_de_data_errados_falham():
    assert any("inválido" in e for e in P.validar([_prazo(fim="31/12/2026")]))
    assert any("inválido" in e for e in P.validar([_prazo(recorrente="anual", fim="2026-12-31")]))
    assert any("inicio depois do fim" in e for e in P.validar([_prazo(inicio="2027-01-01")]))


def test_intervalo_fixo_e_anual():
    assert _prazo(inicio="2026-10-03", fim="2027-05-31").intervalo() == "2026-10-03/2027-05-31"
    assert _prazo(fim="2026-12-31").intervalo() == "/2026-12-31"
    assert _prazo(recorrente="anual", inicio="08-01", fim="12-31").intervalo() == "--08-01/--12-31"


# ── 3. Páginas reais sincronizadas com o gerador ─────────────────────────


def _zona(html: str, marca: tuple[str, str]) -> str:
    m = re.search(rf"<!-- {re.escape(marca[0])} -->(.*?)<!-- {re.escape(marca[1])} -->", html, re.S)
    assert m, f"marcador {marca[0]} em falta"
    return m.group(1)


def test_zona_prazos_da_homepage_igual_ao_gerado():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    zona = " ".join(_zona(html, S.MARCADOR_PRAZOS).split())
    gerado = " ".join(P.render_cartoes_home(P.carregar_prazos()).split())
    assert zona == gerado, "index.html desactualizado — corre python scripts/sincronizar_clusters.py"


def test_zona_prazos_dentro_de_datas_a_nao_perder():
    html = (RAIZ / "index.html").read_text(encoding="utf-8")
    i = html.index('<div class="urgente-cards" role="list">')
    assert i < html.index("<!-- PRAZOS:HOME:INICIO -->") < html.index("<!-- PRAZOS:HOME:FIM -->")


def test_todas_as_paginas_sincronizadas():
    """Correr o sincronizador agora não mudaria nada — listas de guias,
    etiquetas e cartões estão iguais ao gerado."""
    clusters = S.carregar_clusters()
    resultados = [S.processar_home(RAIZ / "index.html", clusters, escrever=False)]
    resultados += [S.processar_pagina(p, clusters, escrever=False)
                   for p in S.encontrar_paginas() if p.name != "index.html"]
    alterados = [r.ficheiro for r in resultados if r.alterado]
    assert not alterados, f"desactualizadas: {alterados} — corre python scripts/sincronizar_clusters.py"


def test_etiqueta_de_prazo_nas_listas_de_guias():
    lista = (RAIZ / "p" / "apoios-escolares.html").read_text(encoding="utf-8")
    li = re.search(r'<li><a href="/prova-escolar.html">.*?</li>', lista).group(0)
    assert 'class="etiqueta etiqueta-prazo" data-prazo="--08-01/--12-31" hidden' in li


def test_so_prazos_ganham_etiqueta_nao_datas_nem_permanentes():
    por = P.prazos_por_pagina(P.carregar_prazos())
    assert all(p.tipo == "prazo" for lista in por.values() for p in lista)
    assert "passe-sub23.html" not in por and "prestacao-social-unica.html" not in por


def test_etiqueta_vazia_sem_prazos():
    assert P.etiqueta_prazo([]) == ""


# ── 4. «Tem simulador» ───────────────────────────────────────────────────

_COM_SIMULADOR = [(p.slug, p.simulador) for c in S.carregar_clusters() for p in c.paginas if p.simulador]


def test_ha_paginas_com_simulador():
    assert len(_COM_SIMULADOR) >= 5


@pytest.mark.parametrize("slug, simulador", _COM_SIMULADOR)
def test_simulador_existe_e_e_ferramenta_e_a_pagina_lhe_liga(slug, simulador):
    tipos = {p.slug: p.tipo for c in S.carregar_clusters() for p in c.paginas}
    assert tipos.get(simulador) == "ferramenta"
    assert (RAIZ / simulador).exists()
    html = (RAIZ / slug).read_text(encoding="utf-8")
    assert re.search(rf'href="/?{re.escape(simulador)}["#?]', html), (
        f"{slug} diz que tem simulador ({simulador}) mas não lhe liga"
    )


def test_simulador_invalido_e_reportado(tmp_path):
    dados = {"clusters": [{
        "id": "a", "nome": "A", "descricao_curta": "", "icone": "", "pillar": "/p/a.html",
        "paginas": [{"slug": "x.html", "titulo": "X", "tipo": "artigo", "destaque": False,
                     "simulador": "y.html"},
                    {"slug": "y.html", "titulo": "Y", "tipo": "artigo", "destaque": False}],
        "relacionados": [],
    }]}
    caminho = tmp_path / "clusters.json"
    caminho.write_text(json.dumps(dados), encoding="utf-8")
    problemas = S.validar_consistencia(S.carregar_clusters(caminho), raiz=tmp_path)
    assert any("não é uma página tipo ferramenta" in p for p in problemas)


def test_render_etiquetas():
    p = S.Pagina(slug="prova-escolar.html", titulo="T", tipo="artigo", destaque=False, simulador="s.html")
    html = S.render_etiquetas(p, P.prazos_por_pagina(P.carregar_prazos()))
    assert html.startswith('<span class="etiquetas">')
    assert "🧮 Tem simulador" in html and "⏳ Prazo a decorrer" in html
    vazio = S.Pagina(slug="nada.html", titulo="T", tipo="artigo", destaque=False)
    assert S.render_etiquetas(vazio, {}) == ""
