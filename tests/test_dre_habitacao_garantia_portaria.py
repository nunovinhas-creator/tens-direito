"""Sentinela irmão do `dre_habitacao_garantia` (2026-09-15) — levantamento
da caducidade da Garantia Pública (DL 44/2024, prazo actual: 31/12/2026),
ponto 5 pedido pelo Nuno.

Motivo de existir: `fontes.html` já documenta que o protocolo do Estado
(Portaria n.º 236-A/2024/1) se mantém vigente "até 31 de dezembro de
2026, ou outra data que posteriormente corresponder ao termo de uma
eventual prorrogação" — ou seja, o mecanismo legal mais plausível para
prorrogar este prazo é uma PORTARIA que altera o protocolo, não
necessariamente um novo Decreto-Lei que altere o DL 44/2024.
`dre_habitacao_garantia` só tem `detectar_decreto_lei` — nunca dispararia
para essa via.

Mesmo padrão exacto do par `dre_psu`/`dre_psu_regulamentacao`: MESMO
termo de pesquisa (`'"garantia pessoal do Estado"'`, já calibrado contra
o motor real na Issue #151), filtros opostos
(`detectar_decreto_lei` vs `detectar_portaria`) — os dois sentinelas
vêem os mesmos resultados brutos do DRE, mas reagem a metades opostas.
Nunca redundância, nunca apagar um por parecer duplicado com o outro —
ver `tests/test_dre_psu_regulamentacao.py` para o mesmo princípio.

Deliberadamente NÃO adicionado a `DRE_SLUGS_PESQUISA` (allow-list de
tipos de acto legal do diff genérico "Detectar mudanças" em
`pipeline-diario.yml`, que hoje cobre só `dre_habitacao_garantia`) —
mesmo precedente exacto de `dre_psu_regulamentacao`: apesar de
partilhar o termo de pesquisa com uma fonte já na allow-list de outro
cluster, nunca foi adicionado a ela por analogia (ver
`tests/test_diff_mudancas_allow_list_dre.py::test_step2_allow_list_scoped_so_a_dre_habitacao_garantia`,
que tranca esse Set a um único slug). Alargar essa allow-list é decisão
à parte, sujeita à mesma exigência de confirmação contra dados reais —
fora do âmbito deste sentinela.

Nunca calibrado contra um runner real nesta sessão (WebFetch/curl
bloqueados para domínios externos) — estes testes cobrem a lógica
Python testável offline (config, detecção por item, integração com
FONTES_PLAYWRIGHT/SLUGS_MONITORIZADOS), não o comportamento real do
site diariodarepublica.pt. A Secção 4 usa dados REAIS já capturados
(`data/scraped/dre_habitacao_garantia_2026-09-03.json`, Issue #158) —
a prova mais próxima disponível sem fabricar dados: o MESMO termo, o
MESMO motor, confirmam que as duas Portarias já conhecidas do regime
(n.º 236-A/2024/1, n.º 187/2025/1) ficam excluídas pelo corte de
recência, sem precisar de `numero_conhecido`.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402
from gerir_estado_fontes import SLUGS_MONITORIZADOS  # noqa: E402


def _fonte_playwright(slug):
    return next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == slug)


def _avisos_capturados(monkeypatch):
    capturados = []
    monkeypatch.setattr(sp, "_registar_aviso",
                        lambda slug, motivo: capturados.append((slug, motivo)))
    return capturados


# ── 1. dre_habitacao_garantia — mecanismo antigo intocado ───────────────


def test_dre_habitacao_garantia_config_e_deteccao_continuam_inalterados():
    """A fonte config, o perfil de browser e a detecção de Decreto-Lei do
    sentinela original nunca mudam com a introdução do sentinela irmão —
    só o corte de recência interno de cada `detectar_*` é independente."""
    config = sp._fonte_config("dre_habitacao_garantia")
    assert config.ancora_conteudo == ('"garantia pessoal do Estado"',)

    perfil = sp._perfil_fonte("dre_habitacao_garantia")
    assert perfil.headers_custom is False
    assert perfil.stealth is False

    fonte = _fonte_playwright("dre_habitacao_garantia")
    deteccao = fonte.get("detectar_decreto_lei")
    assert deteccao, "dre_habitacao_garantia perdeu a sua detecção original"
    assert deteccao["chave_aviso"] == "dre_habitacao_garantia_decreto_detectado"
    assert "detectar_portaria" not in fonte, (
        "dre_habitacao_garantia nunca deve disparar para Portaria — esse "
        "é o trabalho do sentinela irmão, não deste"
    )


# ── 2. dre_habitacao_garantia_portaria — configuração ───────────────────


def test_dre_habitacao_garantia_portaria_tem_config_com_ancora_de_frase_exacta():
    """A âncora é a MESMA frase temática de dre_habitacao_garantia —
    deliberado, nunca a citação do diploma por número (a citação por
    número nunca devolveu resultado nenhum, Issue #147)."""
    config = sp._fonte_config("dre_habitacao_garantia_portaria")
    assert config.ancora_conteudo == ('"garantia pessoal do Estado"',)
    assert config.ancora_conteudo == sp._fonte_config("dre_habitacao_garantia").ancora_conteudo
    assert config.min_chars_uteis >= 1000


def test_dre_habitacao_garantia_portaria_tem_perfil_sem_headers_custom():
    perfil = sp._perfil_fonte("dre_habitacao_garantia_portaria")
    assert perfil.headers_custom is False
    assert perfil.stealth is False


def test_dre_habitacao_garantia_portaria_esta_em_fontes_playwright_com_pesquisa_interactiva():
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    assert "pesquisa_interactiva" in fonte
    assert fonte["pesquisa_interactiva"]["campo"] == "input[type='search']"
    assert fonte["pesquisa_interactiva"]["termo"] == '"garantia pessoal do Estado"'
    assert fonte["url"] == "https://diariodarepublica.pt/dr/home"


def test_dre_habitacao_garantia_portaria_termo_e_identico_ao_dre_habitacao_garantia_mas_filtros_opostos():
    """A sobreposição de termo é deliberada, não redundância. Provado
    aqui: mesmo termo, mesmo url; um só reconhece Decreto-Lei, o outro
    só Portaria — nunca os dois disparam para o mesmo item."""
    fonte_decreto = _fonte_playwright("dre_habitacao_garantia")
    fonte_portaria = _fonte_playwright("dre_habitacao_garantia_portaria")
    assert (fonte_decreto["pesquisa_interactiva"]["termo"]
            == fonte_portaria["pesquisa_interactiva"]["termo"])
    assert "detectar_decreto_lei" in fonte_decreto
    assert "detectar_portaria" not in fonte_decreto
    assert "detectar_decreto_lei" not in fonte_portaria
    assert "detectar_portaria" in fonte_portaria


def test_dre_habitacao_garantia_portaria_tem_deteccao_de_portaria_nunca_decreto_lei():
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    deteccao = fonte.get("detectar_portaria")
    assert deteccao, "sem 'detectar_portaria'"
    assert "detectar_decreto_lei" not in fonte, (
        "esta fonte nunca deve disparar para um Decreto-Lei — esse é o "
        "trabalho de dre_habitacao_garantia, não deste sentinela"
    )
    assert deteccao["chave_aviso"] == "dre_habitacao_garantia_portaria_detectada"
    assert "%s" in deteccao["mensagem_log"]


def test_dre_habitacao_garantia_portaria_tem_corte_de_recencia_desde_a_activacao():
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    assert fonte["detectar_portaria"].get("desde") == "2026-09-15"


def test_dre_habitacao_garantia_portaria_esta_na_maquina_de_estados_de_fontes():
    assert "dre_habitacao_garantia_portaria" in SLUGS_MONITORIZADOS


# ── 3. dre_habitacao_garantia_portaria — detecção por item ──────────────


def test_portaria_que_altera_o_protocolo_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 300/2026/1 - Diário da República n.º 220/2026, Série I de 2026-11-10",
        ],
        "paragrafos": ["Altera a Portaria n.º 236-A/2024/1, de 27 de setembro, prorrogando o prazo."],
    }
    deteccao = _fonte_playwright("dre_habitacao_garantia_portaria")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_habitacao_garantia_portaria"
    assert motivo.startswith("dre_habitacao_garantia_portaria_detectada:")
    assert "Portaria n.º 300/2026/1" in motivo


def test_decreto_lei_que_cita_dl_44_2024_nunca_dispara_este_sentinela(monkeypatch):
    """Um Decreto-Lei (não uma Portaria) que cite o DL 44/2024 é trabalho
    do dre_habitacao_garantia, nunca deste sentinela — mesmo que a
    pesquisa de frase exacta o devolva nos resultados."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 5/2027 - Diário da República n.º 10/2027, Série I de 2027-01-15",
        ],
        "paragrafos": ["Altera o Decreto-Lei n.º 44/2024, de 10 de julho."],
    }
    deteccao = _fonte_playwright("dre_habitacao_garantia_portaria")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is False
    assert capturados == []


def test_resultados_sem_portaria_nunca_disparam(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Despacho n.º 500/2026 - Diário da República n.º 30/2026, Série II de 2026-02-10",
        ],
        "paragrafos": ["Menciona o Decreto-Lei n.º 44/2024 sem o regulamentar."],
    }
    deteccao = _fonte_playwright("dre_habitacao_garantia_portaria")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is False
    assert capturados == []


def test_conteudo_vazio_nunca_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    deteccao = _fonte_playwright("dre_habitacao_garantia_portaria")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", {}, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is False
    assert capturados == []


@pytest.mark.parametrize("slug", ["dre_habitacao_garantia", "dre_habitacao_garantia_portaria"])
def test_ambos_os_sentinelas_partilham_o_mesmo_url_e_perfil_provados(slug):
    """Os 2 sentinelas da Garantia Pública vivem no mesmo domínio (DRE),
    com o mesmo mecanismo já provado — nunca componentes de contexto não
    testados (extra_http_headers já causou um erro 500 real noutro
    domínio da Segurança Social)."""
    fonte = _fonte_playwright(slug)
    assert fonte["url"] == "https://diariodarepublica.pt/dr/home"
    perfil = sp._perfil_fonte(slug)
    assert perfil.headers_custom is False


# ── 4. Validação contra dado REAL, não inferido (Issue #158, ────────────
#      2026-09-03) — as duas Portarias já conhecidas do regime têm de
#      ficar excluídas pelo corte de recência.
#
# `data/scraped/dre_habitacao_garantia_2026-09-03.json` foi capturado
# pelo pipeline real de produção — nunca reescrito à mão. Não é a mesma
# coisa que correr este sentinela contra o motor real (rede bloqueada
# nesta sessão), mas é a prova mais próxima disponível sem fabricar
# dados: o MESMO termo, o MESMO motor, devolveu genuinamente estes itens.
_CAMINHO_DRE_GARANTIA_09_03 = (
    Path(__file__).parent.parent / "data" / "scraped" / "dre_habitacao_garantia_2026-09-03.json"
)


def _itens_reais_dre_habitacao_garantia_2026_09_03() -> list[str]:
    dados = json.loads(_CAMINHO_DRE_GARANTIA_09_03.read_text(encoding="utf-8"))
    return dados["conteudo_extraido"]["itens_lista"]


def test_fixture_real_existe_e_tem_as_duas_portarias_conhecidas():
    """Guarda contra o próprio fixture desaparecer/mudar sem se notar —
    se isto falhar, os testes abaixo estão a testar outra coisa."""
    itens = _itens_reais_dre_habitacao_garantia_2026_09_03()
    assert any("236-A/2024/1" in item for item in itens)
    assert any("187/2025/1" in item for item in itens)


def test_termo_encontra_as_duas_portarias_conhecidas_sem_corte(monkeypatch):
    """Sem corte de recência, as duas Portarias já conhecidas SERIAM
    sinalizadas — prova de que é o corte de recência (não uma falha do
    filtro em reconhecê-las) que as suprime no teste seguinte."""
    _avisos_capturados(monkeypatch)
    itens_reais = _itens_reais_dre_habitacao_garantia_2026_09_03()
    conteudo = {"titulo": "", "itens_lista": itens_reais, "paragrafos": []}
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    deteccao = fonte["detectar_portaria"]

    achados = [t for t in itens_reais if sp._PADRAO_PORTARIA.search(t)]
    assert len(achados) == 2, "o filtro de tipo teria de isolar exactamente as 2 Portarias reais"

    achou_sem_corte = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=None,
    )
    assert achou_sem_corte is True


def test_corte_de_recencia_suprime_as_duas_portarias_ja_conhecidas_em_dados_reais(monkeypatch):
    """Com o `desde` real ("2026-09-15"), a mesma pesquisa real NUNCA
    dispara para nenhuma das duas — já são conhecidas do regime, sem
    relação com uma prorrogação nova. A Portaria n.º 236-A/2024/1 (sem
    data completa) é excluída pelo nível 2 (ano do número, "2024" <
    "2026"); a n.º 187/2025/1 (com data completa "2025-04-15") é
    excluída pelo nível 1 — nenhuma precisa de `numero_conhecido`."""
    capturados = _avisos_capturados(monkeypatch)
    itens_reais = _itens_reais_dre_habitacao_garantia_2026_09_03()
    conteudo = {"titulo": "", "itens_lista": itens_reais, "paragrafos": []}
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    deteccao = fonte["detectar_portaria"]

    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False
    assert capturados == []


def test_uma_futura_portaria_de_prorrogacao_ainda_dispara_apos_o_corte(monkeypatch):
    """O corte de recência nunca cega o sentinela a uma prorrogação
    genuína — só suprime as 2 Portarias já tratadas. Uma Portaria
    genuinamente nova, datada depois do corte, continua a disparar,
    mesmo misturada com os 24 resultados reais de hoje (dominados por
    Resoluções do Conselho de Ministros sem relação com o regime)."""
    capturados = _avisos_capturados(monkeypatch)
    itens_reais = _itens_reais_dre_habitacao_garantia_2026_09_03()
    itens = itens_reais + [
        "Portaria n.º 450/2026/1 - Diário da República n.º 200/2026, Série I de 2026-10-15",
    ]
    conteudo = {"titulo": "", "itens_lista": itens, "paragrafos": []}
    fonte = _fonte_playwright("dre_habitacao_garantia_portaria")
    deteccao = fonte["detectar_portaria"]

    achou = sp._detectar_portaria_generico(
        "dre_habitacao_garantia_portaria", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_habitacao_garantia_portaria"
    assert "Portaria n.º 450/2026/1" in motivo
    assert "236-A/2024/1" not in motivo
    assert "187/2025/1" not in motivo
