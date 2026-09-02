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


def test_dre_habitacao_garantia_pesquisa_a_frase_tematica_nao_a_citacao():
    """Corrigido de vez 2026-09-02 (Issue #151), calibrado contra o
    motor real: a citação por número ('"Decreto-Lei n.º 44/2024"')
    nunca devolveu um resultado em 44 dias seguidos; a 1.ª correcção
    (2026-09-01, "Garantia Pública no crédito habitação") nunca chegou
    a ser confirmada contra o motor real e continuou cega mais 4 dias
    (Issue #151) — confirmado nesse dia a devolver 0 resultados, mesmo
    com contexto/cookies limpos e retry. Trocada para "garantia pessoal
    do Estado" — a expressão exacta usada, repetidamente, no texto do
    próprio DL 44/2024 (lida directamente da página de detalhe em
    dre.pt) — testada a devolver 24 resultados reais à 1.ª tentativa,
    incluindo a Portaria n.º 236-A/2024/1 que regulamenta este mesmo
    DL (ver o comentário completo em scripts/scraper_playwright.py,
    junto a _FONTE_CONFIGS["dre_habitacao_garantia"], para a prova
    completa; ver tests/test_dre_termos_pesquisa.py para o guardrail
    que impede a regressão a um termo com forma de citação)."""
    config = sp._fonte_config("dre_habitacao_garantia")
    assert config.ancora_conteudo[0] == '"garantia pessoal do Estado"'
    fonte = next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == "dre_habitacao_garantia")
    assert fonte["pesquisa_interactiva"]["termo"] == '"garantia pessoal do Estado"'


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


def test_ambas_as_fontes_tem_corte_de_recencia_desde_a_activacao():
    """Achado real na 1.ª corrida do pipeline (2026-07-20): sem corte de
    recência, a pesquisa por 'apoio extraordinário à renda' encontra
    sempre o diploma fundador do PAER (DL 20-B/2023) e as suas alterações
    já conhecidas — dispararia todos os dias. Ver
    _detectar_decreto_lei_generico."""
    for slug in NOVOS_SLUGS:
        fonte = _fonte_playwright(slug)
        assert fonte["detectar_decreto_lei"].get("desde") == "2026-07-20", (
            f"{slug}: sem corte de recência 'desde' — repetirá o falso "
            f"positivo real da Issue criada em 2026-07-20"
        )


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


# ── 3b. Corte de recência — regressão do falso positivo real (2026-07-20) ──


# Fixture real: dre_habitacao_paer_latest.json capturado na 1.ª corrida
# real do pipeline (workflow_dispatch, 2026-07-20T18:22:24Z) — a pesquisa
# de frase exacta funcionou (devolveu o diploma fundador do PAER e as
# suas alterações), mas SEM corte de recência isto criava uma Issue
# falsa todos os dias. Nunca reescrito à mão — cópia fiel do
# `itens_lista` real devolvido pelo DRE.
_ITENS_REAIS_PAER_2026_07_20 = [
    "Decreto-Lei n.º 130/2023 - Diário da República n.º 248/2023, Série I de 2023-12-27",
    "Decreto-Lei n.º 103-B/2023 - Diário da República n.º 217/2023, 1º Suplemento, Série I de 2023-11-09",
    "Decreto Legislativo Regional n.º 27/2025/A - Diário da República n.º 250/2025, Série I de 2025-12-30",
    "Decreto-Lei n.º 13-A/2025 - Diário da República n.º 48/2025, Suplemento, Série I de 2025-03-10",
    "Decreto-Lei n.º 105/2026 - Diário da República n.º 101/2026, Série I de 2026-05-26",
    "Lei n.º 73-A/2025 - Diário da República n.º 250/2025, Suplemento, Série I de 2025-12-30",
    "Regulamento n.º 576/2021 - Diário da República n.º 121/2021, Série II de 2021-06-24",
    "Regulamento n.º 275/2025 - Diário da República n.º 39/2025, Série II de 2025-02-25",
    "Regulamento n.º 791/2023 - Diário da República n.º 140/2023, Série II de 2023-07-20",
]


def test_regressao_paer_pesquisa_real_2026_07_20_nunca_mais_dispara(monkeypatch):
    """A Issue real criada em 2026-07-20 (dre_habitacao_paer) nunca deve
    voltar a acontecer para este mesmo conjunto de resultados — todos os
    diplomas são anteriores à activação da watchlist (2026-07-20)."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": 'Resultados de Pesquisa: "apoio extraordinário à renda"',
        "itens_lista": _ITENS_REAIS_PAER_2026_07_20,
        "paragrafos": _ITENS_REAIS_PAER_2026_07_20,
    }
    deteccao = _fonte_playwright("dre_habitacao_paer")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_paer", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False
    assert capturados == []


def test_decreto_lei_genuinamente_novo_dispara_mesmo_misturado_com_antigos(monkeypatch):
    """O corte de recência nunca esconde um decreto-lei genuinamente novo
    só porque aparece ao lado de diplomas antigos na mesma pesquisa."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": _ITENS_REAIS_PAER_2026_07_20 + [
            "Decreto-Lei n.º 200/2026 - Diário da República n.º 210/2026, Série I de 2026-08-15",
        ],
        "paragrafos": ["Revoga o Decreto-Lei n.º 20-B/2023 e cria um novo regime de apoio à renda."],
    }
    deteccao = _fonte_playwright("dre_habitacao_paer")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_paer", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1
    assert "Decreto-Lei n.º 200/2026" in capturados[0][1]
    # nenhum diploma antigo deve ter entrado nos excertos reportados
    for antigo in ("130/2023", "103-B/2023", "105/2026"):
        assert antigo not in capturados[0][1]


def test_item_sem_data_reconhecivel_nunca_e_descartado_em_silencio(monkeypatch):
    """Invariante 'nenhum estado de erro pode parecer sucesso': um item
    cujo formato mudou (sem data ISO no fim) conta sempre como potencial
    sinal, nunca é silenciosamente ignorado só por não bater com o
    padrão de data esperado."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": ["Decreto-Lei n.º 999/2026 - formato inesperado, sem data reconhecível"],
        "paragrafos": [],
    }
    deteccao = _fonte_playwright("dre_habitacao_paer")["detectar_decreto_lei"]
    achou = sp._detectar_decreto_lei_generico(
        "dre_habitacao_paer", conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1


def test_data_item_extrai_a_data_iso_do_fim_da_entrada():
    assert sp._data_item(
        "Decreto-Lei n.º 130/2023 - Diário da República n.º 248/2023, Série I de 2023-12-27"
    ) == "2023-12-27"
    assert sp._data_item("sem data nenhuma aqui") is None


def test_sem_data_minima_comportamento_identico_ao_original_dre_psu(monkeypatch):
    """Sem `data_minima` (omissão, caso do dre_psu), o corte de recência
    nunca se aplica — comportamento 100% inalterado do mecanismo
    original, mesmo com diplomas "antigos" nos resultados."""
    capturados = _avisos_capturados(monkeypatch)
    achou = sp._detectar_decreto_lei_generico(
        "dre_psu", {"titulo": "", "itens_lista": _ITENS_REAIS_PAER_2026_07_20, "paragrafos": []},
        "dre_psu_decreto_detectado", "%s: teste\n%s",
    )
    assert achou is True
    assert len(capturados) == 1


# ── 4. Integração com a máquina de estados de fontes bloqueadas ────────


def test_ambos_os_slugs_novos_estao_monitorizados():
    """Herdam a mesma máquina de estados de fonte-bloqueada do dre_psu
    (Issue ao 3.º dia consecutivo, fecho automático ao recuperar) — sem
    isto, um bloqueio persistente da pesquisa nunca geraria alerta."""
    for slug in NOVOS_SLUGS:
        assert slug in SLUGS_MONITORIZADOS
