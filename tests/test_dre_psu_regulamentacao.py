"""Fecho do sentinela `dre_psu` original + sentinela irmão novo
(2026-08-16, Fase 2, Commit 5/5 — "sentinela dre_psu já cumpriu a
função, o decreto-lei saiu").

Dois achados nesta sessão, ambos cobertos aqui:

1. **`dre_psu` re-dispararia todos os dias sem correcção.**
   `_detectar_decreto_psu()` nunca teve corte de recência (`data_minima`)
   — não fazia falta enquanto a PSU não tinha decreto-lei nenhum. Agora
   que tem (Decreto-Lei n.º 166/2026, de 13 de agosto, em vigor desde
   14/08/2026), a pesquisa por '"prestação social única"' encontra
   sempre o próprio DL n.º 166/2026 nos resultados — sem corte de
   recência, isto dispararia a Issue "decreto-lei PSU detectado" todos
   os dias, para sempre (mesma classe de falso positivo do PAER, Issue
   #73, só que desta vez sobre o seu próprio alvo já conhecido).
   Corrigido com `data_minima="2026-08-16"` hardcoded dentro de
   `_detectar_decreto_psu()` — nunca no dict de `FONTES_PLAYWRIGHT`, que
   `test_dre_habitacao_watchlist.py::test_dre_psu_continua_a_usar_o_mecanismo_antigo_intocado`
   tranca à forma exacta de antes (`"detectar_decreto_lei" not in
   fonte`). `dre_psu` continua activa — um FUTURO decreto-lei que
   também mencione "prestação social única" ainda dispara.

2. **Sentinela novo — `dre_psu_regulamentacao`.** O Decreto-Lei n.º
   166/2026 deixa 2 pontos para regulamentação por Portaria posterior
   (confirmado directamente pelo Nuno na leitura do texto real, dre.pt
   continua bloqueado nesta sessão): artigo 17.º (fórmula de apoios à
   habitação com carácter de regularidade, dependente de uma estatística
   do INE actualizada por portaria) e artigos 32.º/59.º (procedimentos e
   meios de prova da candidatura). Mesmo mecanismo de pesquisa de frase
   exacta dos outros sentinelas DRE, mas pesquisando pelo NÚMERO do
   decreto-lei (mesmo padrão robusto de `dre_habitacao_garantia`) e
   filtrando só resultados do tipo Portaria (`detectar_portaria`, mesmo
   mecanismo do `dre_ias`).

Nunca calibrado contra um runner real nesta sessão (WebFetch/curl
bloqueados para domínios externos) — estes testes cobrem a lógica
Python testável offline, não o comportamento real do site
diariodarepublica.pt (mesma ressalva honesta já registada para
dre_habitacao_paer/dre_habitacao_garantia/dre_ias na 1.ª corrida).
"""
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


# ── 1. dre_psu — corte de recência acrescentado, mecanismo preservado ──


def test_dre_psu_config_e_perfil_continuam_100_por_cento_inalterados():
    """A fonte config (_FONTE_CONFIGS), o perfil de browser
    (_PERFIL_POR_SLUG) e a forma do dict em FONTES_PLAYWRIGHT nunca
    mudaram — só o corte de recência interno a _detectar_decreto_psu()."""
    config = sp._fonte_config("dre_psu")
    assert config.min_chars_uteis == 1500
    assert config.ancora_conteudo == ('"prestação social única"',)

    perfil = sp._perfil_fonte("dre_psu")
    assert perfil.headers_custom is False
    assert perfil.stealth is False

    fonte = _fonte_playwright("dre_psu")
    assert fonte.get("detectar_decreto_lei_psu") is True
    assert "detectar_decreto_lei" not in fonte
    assert fonte["pesquisa_interactiva"]["termo"] == '"prestação social única"'


def test_o_proprio_dl_166_2026_ja_nao_dispara_dre_psu(monkeypatch):
    """O achado real desta sessão: sem o corte de recência, este
    resultado (o próprio decreto-lei que a PSU já tem) dispararia a
    Issue "decreto-lei PSU detectado" todos os dias, para sempre —
    confirma que já não dispara depois da correcção."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 166/2026 - Diário da República n.º 156/2026, Série I de 2026-08-13",
        ],
        "paragrafos": ["Cria a prestação social única e regulamenta o seu regime."],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is False
    assert capturados == []


def test_um_decreto_lei_futuro_sobre_a_psu_ainda_dispara_dre_psu(monkeypatch):
    """dre_psu continua útil como rede de segurança geral: um decreto-lei
    FUTURO (datado depois do corte de recência) que também mencione
    "prestação social única" — ex.: uma alteração ao regime já criado —
    ainda dispara a Issue, exactamente como antes desta correcção."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 5/2027 - Diário da República n.º 10/2027, Série I de 2027-01-15",
        ],
        "paragrafos": ["Altera o Decreto-Lei n.º 166/2026, que cria a prestação social única."],
    }
    assert sp._detectar_decreto_psu("dre_psu", conteudo) is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_psu"
    assert motivo.startswith("dre_psu_decreto_detectado:")


# ── 2. dre_psu_regulamentacao — configuração ────────────────────────────


def test_dre_psu_regulamentacao_tem_config_com_ancora_de_frase_exacta():
    config = sp._fonte_config("dre_psu_regulamentacao")
    assert config.ancora_conteudo == ('"Decreto-Lei n.º 166/2026"',)
    assert config.min_chars_uteis >= 1000


def test_dre_psu_regulamentacao_tem_perfil_sem_headers_custom():
    perfil = sp._perfil_fonte("dre_psu_regulamentacao")
    assert perfil.headers_custom is False
    assert perfil.stealth is False


def test_dre_psu_regulamentacao_esta_em_fontes_playwright_com_pesquisa_interactiva():
    fonte = _fonte_playwright("dre_psu_regulamentacao")
    assert "pesquisa_interactiva" in fonte
    assert fonte["pesquisa_interactiva"]["campo"] == "input[type='search']"
    assert fonte["pesquisa_interactiva"]["termo"] == '"Decreto-Lei n.º 166/2026"'
    assert fonte["url"] == "https://diariodarepublica.pt/dr/home"


def test_dre_psu_regulamentacao_tem_deteccao_de_portaria_nunca_decreto_lei():
    fonte = _fonte_playwright("dre_psu_regulamentacao")
    deteccao = fonte.get("detectar_portaria")
    assert deteccao, "sem 'detectar_portaria'"
    assert "detectar_decreto_lei" not in fonte, (
        "esta fonte nunca deve disparar para um Decreto-Lei — esse é o "
        "trabalho de dre_psu, não deste sentinela"
    )
    assert deteccao["chave_aviso"] == "dre_psu_regulamentacao_portaria_detectada"
    assert "%s" in deteccao["mensagem_log"]


def test_dre_psu_regulamentacao_tem_corte_de_recencia_desde_a_activacao():
    fonte = _fonte_playwright("dre_psu_regulamentacao")
    assert fonte["detectar_portaria"].get("desde") == "2026-08-16"


def test_dre_psu_regulamentacao_esta_na_maquina_de_estados_de_fontes():
    assert "dre_psu_regulamentacao" in SLUGS_MONITORIZADOS


# ── 3. dre_psu_regulamentacao — detecção por item ───────────────────────


def test_portaria_que_cita_dl_166_2026_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 300/2026 - Diário da República n.º 220/2026, Série I de 2026-11-10",
        ],
        "paragrafos": ["Regulamenta o artigo 17.º do Decreto-Lei n.º 166/2026, de 13 de agosto."],
    }
    deteccao = _fonte_playwright("dre_psu_regulamentacao")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_psu_regulamentacao", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_psu_regulamentacao"
    assert motivo.startswith("dre_psu_regulamentacao_portaria_detectada:")
    assert "Portaria n.º 300/2026" in motivo


def test_decreto_lei_que_cita_dl_166_2026_nunca_dispara_este_sentinela(monkeypatch):
    """Um Decreto-Lei (não uma Portaria) que cite o DL 166/2026 é
    trabalho do dre_psu, nunca deste sentinela — mesmo que a pesquisa de
    frase exacta o devolva nos resultados."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 5/2027 - Diário da República n.º 10/2027, Série I de 2027-01-15",
        ],
        "paragrafos": ["Altera o Decreto-Lei n.º 166/2026, de 13 de agosto."],
    }
    deteccao = _fonte_playwright("dre_psu_regulamentacao")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_psu_regulamentacao", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
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
        "paragrafos": ["Menciona o Decreto-Lei n.º 166/2026 sem o regulamentar."],
    }
    deteccao = _fonte_playwright("dre_psu_regulamentacao")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_psu_regulamentacao", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is False
    assert capturados == []


def test_conteudo_vazio_nunca_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    deteccao = _fonte_playwright("dre_psu_regulamentacao")["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        "dre_psu_regulamentacao", {}, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao.get("desde"),
    )
    assert achou is False
    assert capturados == []


@pytest.mark.parametrize("slug", ["dre_psu", "dre_psu_regulamentacao"])
def test_ambos_os_sentinelas_partilham_o_mesmo_url_e_perfil_provados(slug):
    """Os 2 sentinelas do cluster PSU vivem no mesmo domínio (DRE), com o
    mesmo mecanismo já provado num runner real — nunca componentes de
    contexto não testados (extra_http_headers já causou um erro 500 real
    noutro domínio da Segurança Social)."""
    fonte = _fonte_playwright(slug)
    assert fonte["url"] == "https://diariodarepublica.pt/dr/home"
    perfil = sp._perfil_fonte(slug)
    assert perfil.headers_custom is False
