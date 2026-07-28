"""Sentinela de SINAL para o IAS (Indexante dos Apoios Sociais), 2026-07-28.

Mesmo mecanismo já provado dos sentinelas `dre_psu` (Issue #54,
2026-07-07) e `dre_habitacao_paer`/`dre_habitacao_garantia` (Sessão 3,
2026-07-20): pesquisa de frase exacta no diariodarepublica.pt via
interacção real com a caixa de pesquisa (`pesquisa_interactiva`) —
nenhum parâmetro de URL filtra em navegação directa, o DRE guarda o
termo num cookie de sessão.

Diferença deliberada face aos sentinelas de decreto-lei: o IAS é fixado
por PORTARIA, não por decreto-lei — a detecção usa
`_detectar_portaria_generico` (regex `\\bportaria\\s+n`), thin wrapper do
mesmo núcleo `_detectar_item_juridico_generico` que já serve
`_detectar_decreto_lei_generico`.

Este sentinela é um SINAL puro — nunca extrai nem escreve nenhum valor
de IAS (isso continua 100% manual, ver o bloco de Issue em
pipeline-diario.yml). Nunca calibrado contra um runner real nesta sessão
(WebFetch/curl bloqueados para domínios externos) — estes testes cobrem
a lógica Python testável offline, não o comportamento real do site.

Corte de recência OBRIGATÓRIO desde o 1.º commit — a Portaria do IAS
existe todos os anos desde 2006; sem `data_minima`, a pesquisa de frase
exacta encontraria sempre Portarias antigas e dispararia uma Issue falsa
todos os dias (mesma lição já custada por uma Issue real em
dre_habitacao_paer, Issue #73, 2026-07-20).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402
from gerir_estado_fontes import SLUGS_MONITORIZADOS  # noqa: E402

SLUG = "dre_ias"
DATA_ATIVACAO = "2026-07-28"


# ── 1. Configuração da fonte ────────────────────────────────────────────


def test_config_tem_ancora_de_frase_exacta():
    config = sp._fonte_config(SLUG)
    assert config.ancora_conteudo, f"{SLUG}: sem ancora_conteudo"
    assert config.ancora_conteudo[0] == '"indexante dos apoios sociais"'
    assert config.ancora_conteudo[0].startswith('"') and config.ancora_conteudo[0].endswith('"'), (
        f"{SLUG}: âncora tem de ser uma frase entre aspas (pesquisa exacta), como no dre_psu"
    )
    assert config.min_chars_uteis >= 1000, f"{SLUG}: min_chars_uteis demasiado permissivo"


def test_perfil_sem_stealth_nem_headers_custom():
    """Mesma precaução do dre_psu/dre_habitacao_*: extra_http_headers já
    causou um erro 500 real noutro domínio (Segurança Social) — nunca
    acrescentar esse componente a uma fonte nova sem prova contra o
    backend real. dre_ias herda a calibração já provada, sem alteração."""
    perfil = sp._perfil_fonte(SLUG)
    assert perfil.headers_custom is False, f"{SLUG}: headers_custom devia ser False"
    assert perfil.stealth is False, f"{SLUG}: stealth devia ser False (igual ao dre_psu)"


# ── 2. Presença e forma em FONTES_PLAYWRIGHT ────────────────────────────


def _fonte_playwright(slug):
    return next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == slug)


def test_fonte_esta_em_fontes_playwright_com_pesquisa_interactiva():
    fonte = _fonte_playwright(SLUG)
    assert "pesquisa_interactiva" in fonte, f"{SLUG}: sem pesquisa_interactiva"
    assert fonte["pesquisa_interactiva"]["campo"] == "input[type='search']"
    assert fonte["pesquisa_interactiva"]["termo"] == '"indexante dos apoios sociais"'
    assert fonte["url"] == "https://diariodarepublica.pt/dr/home"


def test_fonte_tem_deteccao_de_portaria_configurada_com_chave_e_mensagem():
    fonte = _fonte_playwright(SLUG)
    deteccao = fonte.get("detectar_portaria")
    assert deteccao, f"{SLUG}: sem 'detectar_portaria'"
    assert deteccao["chave_aviso"] == "dre_ias_portaria_detectada"
    assert "%s" in deteccao["mensagem_log"]
    assert "IAS" in deteccao["mensagem_log"]


def test_fonte_tem_corte_de_recencia_desde_a_ativacao():
    """OBRIGATÓRIO desde o 1.º commit — nunca uma correcção a aplicar
    depois de uma Issue falsa (mesma lição de dre_habitacao_paer,
    Issue #73): a Portaria do IAS existe todos os anos desde 2006, sem
    corte de recência dispararia todos os dias."""
    fonte = _fonte_playwright(SLUG)
    assert fonte["detectar_portaria"].get("desde") == DATA_ATIVACAO, (
        f"{SLUG}: sem corte de recência 'desde' — repetiria o falso "
        f"positivo real já visto em dre_habitacao_paer (Issue #73)"
    )


def test_fonte_nunca_usa_o_mecanismo_de_decreto_lei():
    """dre_ias detecta uma PORTARIA, nunca um decreto-lei — não deve ter
    'detectar_decreto_lei' nem 'detectar_decreto_lei_psu'."""
    fonte = _fonte_playwright(SLUG)
    assert "detectar_decreto_lei" not in fonte
    assert "detectar_decreto_lei_psu" not in fonte


def test_dre_psu_e_dre_habitacao_continuam_com_o_mecanismo_antigo_intocado():
    """A generalização do núcleo de detecção (2026-07-28, para o
    sentinela do IAS reutilizar com um padrão diferente) não pode alterar
    o comportamento dos sentinelas de decreto-lei já existentes."""
    fonte_psu = _fonte_playwright("dre_psu")
    assert fonte_psu.get("detectar_decreto_lei_psu") is True
    assert "detectar_decreto_lei" not in fonte_psu
    assert "detectar_portaria" not in fonte_psu

    for slug in ("dre_habitacao_paer", "dre_habitacao_garantia"):
        fonte = _fonte_playwright(slug)
        assert "detectar_decreto_lei" in fonte
        assert "detectar_portaria" not in fonte


# ── 3. Detecção por item, uma por fonte — nunca texto concatenado ──────


def _avisos_capturados(monkeypatch):
    capturados = []
    monkeypatch.setattr(sp, "_registar_aviso",
                        lambda slug, motivo: capturados.append((slug, motivo)))
    return capturados


def test_portaria_do_ias_dispara(monkeypatch):
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 20/2027 - Diário da República n.º 15/2027, Série I de 2027-01-20",
        ],
        "paragrafos": ["Fixa o valor do indexante dos apoios sociais (IAS) para 2027."],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1
    slug, motivo = capturados[0]
    assert slug == SLUG
    assert motivo.startswith("dre_ias_portaria_detectada:")
    assert "Portaria n.º 20/2027" in motivo


def test_decreto_lei_ou_despacho_nunca_disparam(monkeypatch):
    """A pesquisa de frase exacta por 'indexante dos apoios sociais' pode
    devolver Despachos/Decretos-Lei que só citam o IAS (ex.: um Despacho
    que actualiza um valor derivado) — só a própria Portaria de fixação
    interessa a este sentinela."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Despacho n.º 500/2026 - Diário da República n.º 30/2026, Série II de 2026-08-10",
            "Decreto-Lei n.º 150/2026 - Diário da República n.º 200/2026, Série I de 2026-10-15",
        ],
        "paragrafos": ["Actualiza um valor calculado com base no indexante dos apoios sociais."],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False
    assert capturados == []


def test_conteudo_vazio_nunca_dispara(monkeypatch):
    """Mesma garantia do invariante 'nenhum estado de erro pode parecer
    sucesso' já aplicada aos outros sentinelas."""
    capturados = _avisos_capturados(monkeypatch)
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, {}, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False
    assert capturados == []


# ── 3b. Corte de recência — a armadilha crítica desta implementação ────


# Portarias reais do IAS de anos anteriores (2006-2026) — a pesquisa de
# frase exacta por "indexante dos apoios sociais" encontra sempre estas,
# porque cada Portaria anual cita a Portaria do ano anterior que revoga/
# substitui. Nunca reescritas à mão para simular um caso "conveniente" —
# são o cenário exacto que motivou o corte de recência obrigatório.
_PORTARIAS_HISTORICAS_IAS = [
    "Portaria n.º 480-A/2025/1 - Diário da República n.º 250/2025, Suplemento, Série I de 2025-12-30",
    "Portaria n.º 20/2025 - Diário da República n.º 10/2025, Série I de 2025-01-15",
    "Portaria n.º 6/2024 - Diário da República n.º 4/2024, Série I de 2024-01-05",
    "Portaria n.º 1/2011 - Diário da República n.º 1/2011, Série I de 2011-01-03",
    "Portaria n.º 1514/2007 - Diário da República n.º 246/2007, Série I de 2007-12-21",
    "Portaria n.º 6/2006 - Diário da República n.º 3/2006, Série I de 2006-01-04",
]


def test_portarias_historicas_do_ias_nunca_disparam():
    """A ARMADILHA CRÍTICA desta implementação: sem `data_minima`, este
    conjunto de Portarias antigas (todas anteriores à activação do
    sentinela) dispararia uma Issue falsa TODOS OS DIAS — exactamente o
    que aconteceu com dre_habitacao_paer (Issue #73, PAER existe desde
    2023). A Portaria do IAS existe desde 2006 — o risco é ainda maior."""
    conteudo = {
        "titulo": 'Resultados de Pesquisa: "indexante dos apoios sociais"',
        "itens_lista": _PORTARIAS_HISTORICAS_IAS,
        "paragrafos": _PORTARIAS_HISTORICAS_IAS,
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False, (
        "REGRESSÃO CRÍTICA: Portarias históricas do IAS dispararam o "
        "sentinela — o corte de recência não está a funcionar"
    )


def test_sem_data_minima_as_portarias_historicas_disparariam(monkeypatch):
    """Prova, por contraste directo, que o corte de recência é a única
    coisa que impede o falso positivo do teste anterior — sem
    `data_minima`, o mesmo conjunto de Portarias antigas dispara."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": _PORTARIAS_HISTORICAS_IAS,
        "paragrafos": _PORTARIAS_HISTORICAS_IAS,
    }
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, "dre_ias_portaria_detectada", "%s: teste\n%s",
    )
    assert achou is True
    assert len(capturados) == 1


def test_portaria_do_ias_genuinamente_nova_dispara_mesmo_misturada_com_antigas(monkeypatch):
    """O corte de recência nunca esconde uma Portaria genuinamente nova
    só porque aparece ao lado de Portarias antigas na mesma pesquisa."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": _PORTARIAS_HISTORICAS_IAS + [
            "Portaria n.º 10/2027 - Diário da República n.º 5/2027, Série I de 2027-01-10",
        ],
        "paragrafos": ["Fixa o valor do indexante dos apoios sociais para 2027."],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1
    assert "Portaria n.º 10/2027" in capturados[0][1]
    for antiga in ("480-A/2025", "20/2025", "6/2024", "1/2011", "1514/2007", "6/2006"):
        assert antiga not in capturados[0][1]


def test_item_sem_data_nem_ano_reconhecivel_nunca_e_descartado_em_silencio(monkeypatch):
    """Invariante 'nenhum estado de erro pode parecer sucesso' — nível 3
    da hierarquia (salvaguarda final). Um item cujo formato mudou tão
    radicalmente que nem sequer o ano do número do próprio acto é
    reconhecível ('n.º .../AAAA') conta sempre como potencial sinal,
    nunca é silenciosamente ignorado. Distinto do nível 2 (ano
    reconhecível) — este caso não tem "/AAAA" nenhum a seguir a "n.º"."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": ["Portaria n.º XPTO — formato totalmente novo do DRE, sem número nem data"],
        "paragrafos": [],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1


# ── 3c. Fallback de ano do número do acto — nível 2 da hierarquia ──────
#
# Achado real num runner (2026-07-28, run 30337389407): a pesquisa por
# "indexante dos apoios sociais" devolve consistentemente Portarias
# antigas e genuínas (2012, 2019, 2023 — confirmado via WebSearch, não
# são lixo/duplicados) cujo texto no DRE NUNCA inclui o sufixo de data
# completo — só o próprio número do acto. Sem este nível 2, ficavam
# presas no nível 3 (salvaguarda) para sempre, disparando a Issue todos
# os dias — o mesmo pesadelo do PAER (Issue #73), só que por ausência de
# data em vez de ausência de corte de recência.


def test_ano_do_numero_antigo_sem_data_e_excluido():
    """Regressão do achado real: um item SEM data completa mas com ano
    antigo embutido no próprio número ('Portaria n.º 257/2012') tem de
    ser EXCLUÍDO pelo nível 2 — nunca fica preso na salvaguarda do nível
    3 só porque falta a data completa. String real capturada no
    diagnóstico (run 30337389407), nunca reescrita à mão."""
    assert sp._data_item("Portaria n.º 257/2012") is None  # confirma que cai para o nível 2
    assert sp._ano_item("Portaria n.º 257/2012") == "2012"

    conteudo = {
        "titulo": "",
        "itens_lista": ["Portaria n.º 257/2012"],
        "paragrafos": [],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False, (
        "REGRESSÃO CRÍTICA: uma Portaria antiga sem data completa mas "
        "com ano reconhecível no número (2012) disparou o sentinela — "
        "o fallback de ano (nível 2) não está a excluir correctamente"
    )


def test_ano_do_numero_no_ano_de_ativacao_ou_posterior_e_mantido(monkeypatch):
    """Espelho do teste anterior: um item SEM data completa mas com ano
    >= ao ano de activação (2026) tem de ser MANTIDO como sinal — nunca
    esconder um acto do próprio ano de activação ou posterior só porque
    falta a data completa."""
    capturados = _avisos_capturados(monkeypatch)
    assert sp._data_item("Portaria n.º 5/2026") is None
    assert sp._ano_item("Portaria n.º 5/2026") == "2026"

    conteudo = {
        "titulo": "",
        "itens_lista": ["Portaria n.º 5/2026"],
        "paragrafos": [],
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is True
    assert len(capturados) == 1


def test_nivel_1_data_completa_ganha_sempre_que_presente(monkeypatch):
    """A hierarquia nunca é substituição — a data completa (nível 1)
    decide sozinha quando presente, mesmo que o ano do número (nível 2)
    daria um resultado diferente. Aqui a data completa é antiga
    (2020-01-31) mas o ano do número seria 2020 também — caso de
    controlo simples para confirmar que o nível 1 é sempre tentado
    primeiro e nunca ignorado."""
    capturados = _avisos_capturados(monkeypatch)
    texto = "Portaria n.º 27/2020 - Diário da República n.º 22/2020, Série I de 2020-01-31"
    assert sp._data_item(texto) == "2020-01-31"  # nível 1 encontra a data completa

    conteudo = {"titulo": "", "itens_lista": [texto], "paragrafos": []}
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False
    assert capturados == []


# Fixture real: os 28 itens_lista devolvidos pela pesquisa real
# "indexante dos apoios sociais" no run 30337389407 (2026-07-28) —
# inclui os 3 casos reais sem data completa (257/2012, 214/2019,
# 187/2023) que motivaram o nível 2. Nunca reescrita à mão.
_ITENS_REAIS_IAS_2026_07_28 = [
    "Portaria n.º 27/2020 - Diário da República n.º 22/2020, Série I de 2020-01-31",
    "Portaria n.º 4/2017 - Diário da República n.º 2/2017, Série I de 2017-01-03",
    "Portaria n.º 24/2019 - Diário da República n.º 12/2019, Série I de 2019-01-17",
    "Portaria n.º 21/2018 - Diário da República n.º 13/2018, Série I de 2018-01-18",
    "Portaria n.º 421/2023 - Diário da República n.º 237/2023, Série I de 2023-12-11",
    "Portaria n.º 480-A/2025/1 - Diário da República n.º 250/2025, Suplemento, Série I de 2025-12-30",
    "Portaria n.º 6-B/2025/1 - Diário da República n.º 3/2025, Suplemento, Série I de 2025-01-06",
    "Portaria n.º 298/2022 - Diário da República n.º 241/2022, Série I de 2022-12-16",
    "Portaria n.º 294/2021 - Diário da República n.º 239/2021, Série I de 2021-12-13",
    "Portaria n.º 106/2007 - Diário da República n.º 16/2007, Série I de 2007-01-23",
    "Resolução da Assembleia da República n.º 97/2017 - Diário da República n.º 108/2017, Série I de 2017-06-05",
    "Decreto-Lei n.º 323/2009 - Diário da República n.º 248/2009, Série I de 2009-12-24",
    "Portaria n.º 1514/2008 - Diário da República n.º 248/2008, Série I de 2008-12-24",
    "Resolução da Assembleia da República n.º 45/2009 - Diário da República n.º 125/2009, Série I de 2009-07-01",
    "Portaria n.º 9/2008 - Diário da República n.º 2/2008, Série I de 2008-01-03",
    "Decreto-Lei n.º 1/2016 - Diário da República n.º 3/2016, Série I de 2016-01-06",
    "Lei n.º 13/2003",
    "Portaria n.º 257/2012",
    "Portaria n.º 333/2025/1 - Diário da República n.º 193/2025, Série I de 2025-10-07",
    "Portaria n.º 214/2019",
    "Decreto-Lei n.º 50-B/2024 - Diário da República n.º 163/2024, Suplemento, Série I de 2024-08-23",
    "Lei n.º 54/2018 - Diário da República n.º 159/2018, Série I de 2018-08-20",
    "Portaria n.º 390/2023 - Diário da República n.º 227/2023, Série I de 2023-11-23",
    "Portaria n.º 187/2023",
    "Lei n.º 24/2023 - Diário da República n.º 103/2023, Série I de 2023-05-29",
    "Lei n.º 19/2022",
    "Portaria n.º 256/2014 - Diário da República n.º 238/2014, Série I de 2014-12-10",
    "Decreto-Lei n.º 28/2023 - Diário da República n.º 83/2023, Série I de 2023-04-28",
]


def test_regressao_resultado_real_2026_07_28_nunca_mais_dispara():
    """A pesquisa real do run 30337389407 (2026-07-28) gerava achou=True
    ANTES desta correcção, por causa dos 3 itens sem data completa. Com
    o nível 2 (fallback de ano), os 28 itens reais nunca mais disparam."""
    conteudo = {
        "titulo": 'Resultados de Pesquisa: "indexante dos apoios sociais"',
        "itens_lista": _ITENS_REAIS_IAS_2026_07_28,
        "paragrafos": _ITENS_REAIS_IAS_2026_07_28,
    }
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    achou = sp._detectar_portaria_generico(
        SLUG, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
        data_minima=deteccao["desde"],
    )
    assert achou is False


# ── 4. Núcleo partilhado — regressão dos sentinelas de decreto-lei ─────


def test_padrao_de_portaria_nunca_apanha_decreto_lei_nem_despacho():
    assert sp._PADRAO_PORTARIA.search("Decreto-Lei n.º 1/2026") is None
    assert sp._PADRAO_PORTARIA.search("Despacho n.º 1/2026") is None
    assert sp._PADRAO_PORTARIA.search("Portaria n.º 1/2026") is not None


def test_padrao_de_decreto_lei_nunca_apanha_portaria(monkeypatch):
    """Regressão do núcleo partilhado (`_detectar_item_juridico_generico`):
    a generalização para o sentinela do IAS não pode fazer o mecanismo de
    decreto-lei já existente passar a reagir a Portarias."""
    capturados = _avisos_capturados(monkeypatch)
    conteudo = {
        "titulo": "",
        "itens_lista": [
            "Portaria n.º 480-A/2025/1 - Diário da República n.º 250/2025, Série I de 2025-12-30",
        ],
        "paragrafos": ["Fixa o valor do indexante dos apoios sociais para 2026."],
    }
    achou = sp._detectar_decreto_lei_generico(
        "dre_psu", conteudo, "dre_psu_decreto_detectado", "%s: teste\n%s",
    )
    assert achou is False
    assert capturados == []


# ── 5. Integração com a máquina de estados de fontes bloqueadas ────────


def test_slug_esta_monitorizado():
    """Herda a mesma máquina de estados de fonte-bloqueada dos outros
    sentinelas DRE (Issue ao 3.º dia consecutivo, fecho automático ao
    recuperar) — sem isto, um bloqueio persistente da pesquisa nunca
    geraria alerta."""
    assert SLUG in SLUGS_MONITORIZADOS


# ── 6. Nunca extrai nem escreve valores — é só sinal ────────────────────


def test_deteccao_nunca_recebe_nem_devolve_um_valor_de_ias(monkeypatch):
    """A função de detecção só devolve um bool (achou/não achou) — nunca
    um valor extraído. O contrato de 'só sinal, nunca provider de valor'
    é estrutural: a assinatura não tem sequer forma de devolver um valor."""
    _avisos_capturados(monkeypatch)
    deteccao = _fonte_playwright(SLUG)["detectar_portaria"]
    resultado = sp._detectar_portaria_generico(
        SLUG,
        {"titulo": "", "itens_lista": [
            "Portaria n.º 1/2027 - Diário da República n.º 1/2027, Série I de 2027-01-05",
        ], "paragrafos": []},
        deteccao["chave_aviso"], deteccao["mensagem_log"], data_minima=deteccao["desde"],
    )
    assert isinstance(resultado, bool)
