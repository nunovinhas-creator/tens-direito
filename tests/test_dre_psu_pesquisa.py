"""Testes da correcção do sentinela dre_psu (Issue #54, 2026-07-07).

A fonte passou de uma URL de pesquisa morta (dre.pt/pesquisa?q=...,
soft-404) para pesquisa interactiva de frase exacta no
diariodarepublica.pt — confirmado num runner real com browser
interactivo que NENHUM parâmetro de URL filtra (devolve sempre o índice
inteiro, 2,2M resultados, HTTP 200 — um falso sucesso perfeito) e que a
pesquisa com aspas na caixa devolve exactamente os actos que contêm a
frase (2 resultados à data do diagnóstico).

Cobre as duas pontas do invariante "nenhum estado de erro pode parecer
sucesso":
1. Classificação — só a página de resultados FILTRADA (com o eco do
   termo entre aspas) classifica OK; o índice inteiro nunca fica OK.
2. Detecção — um Decreto-Lei nos resultados dispara o aviso; a lógica é
   por item, nunca sobre o texto todo concatenado (o falso positivo
   latente da versão antiga).

Fixtures construídas a partir do texto REAL capturado no diagnóstico
(runs 28860869507 e 28861231682), nunca inventadas.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402
from classificador_resposta import classificar_resposta, Estado  # noqa: E402

CONFIG_DRE_PSU = sp._fonte_config("dre_psu")

# Texto real da página de resultados FILTRADA (diagnóstico 2026-07-07,
# pesquisa com aspas — 2 resultados). O padding simula o resto do texto
# da página real (~2400 chars úteis), acima de min_chars_uteis.
_HTML_FILTRADO = (
    "<html><head><title>Resultados de pesquisa | DR</title></head><body>"
    "<div>Início</div><div>Resultados de: \"prestação social única\"</div>"
    "<div>Resultados de Pesquisa: \"prestação social única\" 2 de 2 resultados</div>"
    "<div><a href='/dr/detalhe/lei/73-b-2025-993315589'>"
    "<span data-expression=''>Lei n.º 73-B/2025 - Diário da República n.º 251/2025, "
    "Suplemento, Série I de 2025-12-31</span></a></div>"
    "<div><span data-expression=''>Aprova as Grandes Opções para 2025-2029.</span></div>"
    "<div><span data-expression=''>Designa para exercer as funções de técnica especialista "
    "no Gabinete da Ministra do Trabalho, Solidariedade e Segurança Social a licenciada "
    "Margarida Alexandra dos Mártires Rodrigues Jordão.</span></div>"
    "<div><a href='/dr/detalhe/despacho/7619-2025-923848060'>"
    "<span data-expression=''>Despacho n.º 7619/2025 - Diário da República n.º 128/2025, "
    "Série II de 2025-07-07</span></a></div>"
    + "<div>Refinar Pesquisa Ordenar por frequência de resultado</div>" * 40
    + "</body></html>"
)

# Texto real da página NÃO filtrada (índice inteiro — navegação directa
# com ?termo=/?q=): "Resultados de:" SEM o eco do termo.
_HTML_INDICE_INTEIRO = (
    "<html><head><title>Resultados de pesquisa | DR</title></head><body>"
    "<div>Início</div><div>Resultados de:</div>"
    "<div>25 de 2248834 resultados</div>"
    "<div>Filtrar Ocultar revogados Mostrar apenas em vigor Série II 1850225 I 298792</div>"
    + "<div>Use a tecla de seta para baixo para abrir o calendário</div>" * 40
    + "</body></html>"
)

# Texto real do soft-404 da URL antiga (dre.pt/pesquisa?q=...).
_HTML_SOFT_404 = (
    "<html><head><title></title></head><body>"
    "<div>A página não se encontra disponível. Ir para a página inicial</div>"
    "</body></html>"
)


# ── 1. Classificação ───────────────────────────────────────────────────


def test_pagina_filtrada_classifica_ok():
    c = classificar_resposta(
        status_code=200, corpo=_HTML_FILTRADO,
        url_final="https://diariodarepublica.pt/dr/pesquisa", config=CONFIG_DRE_PSU,
    )
    assert c.estado == Estado.OK


def test_indice_inteiro_nunca_fica_ok():
    """O modo de falha real que motivou a decisão de não trocar a URL em
    2026-07-05: HTTP 200 com o índice inteiro, sem filtro aplicado. Sem o
    eco do termo, nunca pode ser OK."""
    c = classificar_resposta(
        status_code=200, corpo=_HTML_INDICE_INTEIRO,
        url_final="https://diariodarepublica.pt/dr/pesquisa", config=CONFIG_DRE_PSU,
    )
    assert c.estado != Estado.OK
    assert c.estado == Estado.MUDOU  # respondeu, mas sem o conteúdo esperado


def test_soft_404_nunca_fica_ok():
    c = classificar_resposta(
        status_code=200, corpo=_HTML_SOFT_404,
        url_final="https://diariodarepublica.pt/dr/error", config=CONFIG_DRE_PSU,
    )
    assert c.estado != Estado.OK


def test_ancora_exige_aspas_do_eco():
    """A âncora inclui as aspas — o eco 'Resultados de: prestação social
    única' SEM aspas (pesquisa fuzzy, 12.651 resultados) não pode
    classificar OK: não prova frase exacta."""
    html_sem_aspas = _HTML_FILTRADO.replace('"prestação social única"',
                                            "prestação social única")
    c = classificar_resposta(
        status_code=200, corpo=html_sem_aspas,
        url_final="https://diariodarepublica.pt/dr/pesquisa", config=CONFIG_DRE_PSU,
    )
    assert c.estado != Estado.OK


# ── 2. Extracção com os selectores reais ───────────────────────────────


def test_extraccao_apanha_titulos_dos_resultados():
    fonte = next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == "dre_psu")
    conteudo = sp._extrair_conteudo(_HTML_FILTRADO, fonte["seletores"])
    itens = conteudo.get("itens_lista", [])
    assert any("Lei n.º 73-B/2025" in i for i in itens)
    assert any("Despacho n.º 7619/2025" in i for i in itens)
    # a designação vem via paragrafos (span[data-expression]); nota: o
    # filtro de _extrair_conteudo exige >40 chars — designações curtas
    # (ex.: a da Lei n.º 73-B/2025, exactamente 40) ficam de fora, e não
    # fazem falta: a detecção decide pelos títulos em itens_lista
    assert any("técnica especialista" in p for p in conteudo.get("paragrafos", []))


# ── 3. Detecção do decreto-lei — por item, nunca texto concatenado ─────


def _avisos_capturados(monkeypatch):
    capturados = []
    monkeypatch.setattr(sp, "_registar_aviso",
                        lambda slug, motivo: capturados.append((slug, motivo)))
    return capturados


def test_resultados_actuais_reais_nao_disparam(monkeypatch):
    """Os 2 resultados reais de hoje (Lei + Despacho) nunca podem disparar
    o aviso — nenhum é um Decreto-Lei."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Lei n.º 73-B/2025 - Diário da República n.º 251/2025, Suplemento, Série I de 2025-12-31",
            "Despacho n.º 7619/2025 - Diário da República n.º 128/2025, Série II de 2025-07-07",
        ],
        "paragrafos": ["Aprova as Grandes Opções para 2025-2029."],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is False
    assert capturados == []


def test_decreto_lei_nos_resultados_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Lei n.º 73-B/2025 - Diário da República n.º 251/2025, Série I de 2025-12-31",
            "Decreto-Lei n.º 99/2026 - Diário da República n.º 160/2026, Série I de 2026-08-20",
        ],
        "paragrafos": ["Cria a prestação social única e regulamenta o seu regime."],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_psu"
    assert motivo.startswith("dre_psu_decreto_detectado:")
    assert "Decreto-Lei n.º 99/2026" in motivo


def test_falso_positivo_da_versao_antiga_nao_dispara(monkeypatch):
    """Regressão do falso positivo latente: a versão antiga fazia
    `decreto.lei\\b.*\\bpresta` sobre TODO o texto concatenado — um item
    com 'decreto-lei' e OUTRO item com 'prestação' disparavam juntos.
    A detecção por item não pode disparar quando 'decreto-lei' só aparece
    numa designação (paragrafo), nunca no título de um resultado."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 10/2026 - Diário da República n.º 5/2026, Série I de 2026-01-08",
        ],
        # designação menciona um decreto-lei alheio + a frase — não é o acto
        "paragrafos": [
            "Procede à regulamentação prevista no Decreto-Lei n.º 126-A/2017.",
            "Actualiza os valores da prestação social para a inclusão.",
        ],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is False
    assert capturados == []


def test_conteudo_vazio_nao_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    assert sp._detectar_decreto_psu("dre_psu", {}) is False
    assert capturados == []


def test_linha_referencia_sem_data_do_alvo_conhecido_nao_dispara(monkeypatch):
    """Regressão da Issue #132 (2026-08-30): a 27/08/2026 apareceu uma
    Portaria nova (n.º 394/2026/1) que cita o DL 166/2026, e o DRE listou
    ao lado uma linha-referência SEM data completa — só "Decreto-Lei n.º
    166/2026", sem sufixo "Série I de ...". Sem `numero_conhecido`, o
    nível 2 do corte de recência comparava só o ano ("2026" >= "2026" de
    `data_minima`) e deixava passar — reabrindo a Issue que o corte de
    2026-08-16 (Fase 2, Commit 5/5) já tinha fechado para o mesmo acto.
    Dados reais capturados no scrape de 2026-08-27 (dre_psu_2026-08-27.json),
    nunca inventados."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Lei n.º 36/2026 - Diário da República n.º 143/2026, Série I de 2026-07-27",
            "Portaria n.º 394/2026/1 - Diário da República n.º 166/2026, Série I de 2026-08-27",
            "Decreto-Lei n.º 166/2026",
            "Decreto-Lei n.º 166/2026 - Diário da República n.º 156/2026, Série I de 2026-08-13",
            "Lei n.º 36/2026",
            "Lei n.º 73-B/2025 - Diário da República n.º 251/2025, Suplemento, Série I de 2025-12-31",
            "Despacho n.º 9782/2026 - Diário da República n.º 149/2026, Série II de 2026-08-04",
            "Despacho n.º 9777/2026 - Diário da República n.º 149/2026, Série II de 2026-08-04",
            "Despacho n.º 7619/2025 - Diário da República n.º 128/2025, Série II de 2025-07-07",
        ],
        "paragrafos": [],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is False
    assert capturados == []


def test_linha_sem_data_com_numero_diferente_do_conhecido_continua_a_disparar(monkeypatch):
    """`numero_conhecido` exclui só o acto já conhecido (166/2026) — um
    Decreto-Lei GENUINAMENTE novo, listado sem data completa (o mesmo
    formato do achado real acima, mas com outro número), continua a
    disparar. Nunca uma supressão cega de "qualquer item sem data"."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 200/2026",
        ],
        "paragrafos": ["Altera o regime da prestação social única."],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is True
    assert len(capturados) == 1
    assert "Decreto-Lei n.º 200/2026" in capturados[0][1]


def test_numero_item_extrai_o_numero_completo_do_acto():
    assert sp._numero_item("Decreto-Lei n.º 166/2026") == "166/2026"
    assert sp._numero_item(
        "Decreto-Lei n.º 166/2026 - Diário da República n.º 156/2026, Série I de 2026-08-13"
    ) == "166/2026"
    assert sp._numero_item("Despacho n.º 7619/2025") == "7619/2025"
    assert sp._numero_item("formato totalmente inesperado, sem número") is None
