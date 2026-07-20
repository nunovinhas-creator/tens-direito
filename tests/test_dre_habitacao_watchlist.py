"""Watchlist DRE do cluster Habitação (Sessão 3, 2026-07-20).

Estende o mecanismo já provado do sentinela `dre_psu` (pesquisa de frase
exacta no diariodarepublica.pt, Issue #54, 2026-07-07) a duas fontes
novas — `dre_habitacao_paer` (revogação do PAER / reforma "produto
único" dos apoios ao arrendamento) e `dre_habitacao_garantia`
(alteração/prorrogação da Garantia Pública, DL 44/2024). A lógica de
detecção foi generalizada em `_detectar_decreto_lei_generico`, mantendo
`_detectar_decreto_psu` como wrapper fino (ver
tests/test_dre_psu_pesquisa.py, que continua a cobrir esse caminho sem
alterações).

Nunca calibrado contra um runner real nesta sessão (WebFetch/curl
bloqueados para domínios externos) — estes testes cobrem a lógica
Python testável offline (config, detecção por item, integração com
FONTES_PLAYWRIGHT/SLUGS_MONITORIZADOS), não o comportamento real do
site diariodarepublica.pt.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402
from gerir_estado_fontes import SLUGS_MONITORIZADOS  # noqa: E402

NOVOS_SLUGS = ("dre_habitacao_paer", "dre_habitacao_garantia")


# ── 1. Configuração por fonte ───────────────────────────────────────────


def test_ambas_as_fontes_tem_config_com_ancora_de_frase_exacta():
    for slug in NOVOS_SLUGS:
        config = sp._fonte_config(slug)
        assert config.ancora_conteudo, f"{slug}: sem ancora_conteudo"
        assert config.ancora_conteudo[0].startswith('"') and config.ancora_conteudo[0].endswith('"'), (
            f"{slug}: âncora tem de ser uma frase entre aspas (pesquisa exacta), como no dre_psu"
        )
        assert config.min_chars_uteis >= 1000, f"{slug}: min_chars_uteis demasiado permissivo"


def test_dre_habitacao_paer_pesquisa_o_nome_oficial_do_paer():
    config = sp._fonte_config("dre_habitacao_paer")
    assert config.ancora_conteudo[0] == '"apoio extraordinário à renda"'


def test_dre_habitacao_garantia_pesquisa_a_citacao_do_diploma():
    config = sp._fonte_config("dre_habitacao_garantia")
    assert config.ancora_conteudo[0] == '"Decreto-Lei n.º 44/2024"'


def test_ambas_as_fontes_tem_perfil_sem_headers_custom():
    """Mesma precaução do dre_psu: extra_http_headers já causou um erro
    500 real noutro domínio (Segurança Social) — nunca acrescentar esse
    componente a uma fonte nova sem prova contra o backend real."""
    for slug in NOVOS_SLUGS:
        perfil = sp._perfil_fonte(slug)
        assert perfil.headers_custom is False, f"{slug}: headers_custom devia ser False"
        assert perfil.stealth is False, f"{slug}: stealth devia ser False (igual ao dre_psu)"


# ── 2. Presença e forma em FONTES_PLAYWRIGHT ────────────────────────────


def _fonte_playwright(slug):
    return next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == slug)


def test_ambas_as_fontes_estao_em_fontes_playwright_com_pesquisa_interactiva():
    for slug in NOVOS_SLUGS:
        fonte = _fonte_playwright(slug)
        assert "pesquisa_interactiva" in fonte, f"{slug}: sem pesquisa_interactiva"
        assert fonte["pesquisa_interactiva"]["campo"] == "input[type='search']"
        assert fonte["url"] == "https://diariodarepublica.pt/dr/home"


def test_ambas_as_fontes_tem_deteccao_configurada_com_chave_e_mensagem():
    for slug in NOVOS_SLUGS:
        fonte = _fonte_playwright(slug)
        deteccao = fonte.get("detectar_decreto_lei")
        assert deteccao, f"{slug}: sem 'detectar_decreto_lei'"
        assert deteccao["chave_aviso"] == f"{slug}_decreto_detectado"
        assert "%s" in deteccao["mensagem_log"]


def test_dre_psu_continua_a_usar_o_mecanismo_antigo_intocado():
    """dre_psu NUNCA foi migrado para 'detectar_decreto_lei' — mantém
    'detectar_decreto_lei_psu': True e o caminho de código próprio em
    scrape_playwright(), por compatibilidade com
    tests/test_dre_psu_pesquisa.py, que importa _detectar_decreto_psu
    directamente pelo nome."""
    fonte = _fonte_playwright("dre_psu")
    assert fonte.get("detectar_decreto_lei_psu") is True
    assert "detectar_decreto_lei" not in fonte


# ── 3. Detecção por item, uma por fonte — nunca texto concatenado ──────


def _avisos_capturados(monkeypatch):
    capturados = []
    monkeypatch.setattr(sp, "_registar_aviso",
                        lambda slug, motivo: capturados.append((slug, motivo)))
    return capturados


def test_decreto_lei_que_cita_paer_dispara_dre_habitacao_paer(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 150/2026 - Diário da República n.º 200/2026, Série I de 2026-10-15",
        ],
        "paragrafos": ["Revoga o Decreto-Lei n.º 20-B/2023 e cria um novo regime de apoio à renda."],
    }
    deteccao = _fonte_playwright("dre_habitacao_paer")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_paer", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"]
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_habitacao_paer"
    assert motivo.startswith("dre_habitacao_paer_decreto_detectado:")
    assert "Decreto-Lei n.º 150/2026" in motivo


def test_decreto_lei_que_cita_dl_44_2024_dispara_dre_habitacao_garantia(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Decreto-Lei n.º 210/2026 - Diário da República n.º 240/2026, Série I de 2026-12-05",
        ],
        "paragrafos": ["Prorroga o prazo previsto no Decreto-Lei n.º 44/2024, de 10 de julho."],
    }
    deteccao = _fonte_playwright("dre_habitacao_garantia")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_garantia", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"]
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == "dre_habitacao_garantia"
    assert motivo.startswith("dre_habitacao_garantia_decreto_detectado:")


def test_resultados_sem_decreto_lei_nunca_disparam(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 15/2026 - Diário da República n.º 20/2026, Série I de 2026-01-30",
            "Despacho n.º 500/2026 - Diário da República n.º 30/2026, Série II de 2026-02-10",
        ],
        "paragrafos": ["Menciona o apoio extraordinário à renda sem alterar o regime."],
    }
    deteccao = _fonte_playwright("dre_habitacao_paer")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_paer", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"]
    )
    assert achou is False
    assert capturados == []


def test_conteudo_vazio_nunca_dispara(monkeypatch):
    """Mesma garantia do invariante 'nenhum estado de erro pode parecer
    sucesso' já aplicada ao dre_psu — conteúdo vazio nunca é confundido
    com detecção positiva nem negativa silenciosa sem aviso nenhum."""
    capturados = _avisos_capturados(monkeypatch)
    deteccao = _fonte_playwright("dre_habitacao_garantia")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_garantia", {}, deteccao["chave_aviso"], deteccao["mensagem_log"]
    )
    assert achou is False
    assert capturados == []


# ── 4. Integração com a máquina de estados de fontes bloqueadas ────────


def test_ambos_os_slugs_novos_estao_monitorizados():
    """Herdam a mesma máquina de estados de fonte-bloqueada do dre_psu
    (Issue ao 3.º dia consecutivo, fecho automático ao recuperar) — sem
    isto, um bloqueio persistente da pesquisa nunca geraria alerta."""
    for slug in NOVOS_SLUGS:
        assert slug in SLUGS_MONITORIZADOS
