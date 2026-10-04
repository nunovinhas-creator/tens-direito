"""
Testes do canário de URLs oficiais do cluster "Como Pedir"
(SPEC-CLUSTER-COMO-PEDIR.md, secção 6.1).

Dois níveis, deliberadamente separados:
1. Estrutural/determinístico (corre sempre, sandbox e CI): a configuração
   `data/urls_como_pedir.json` cobre todos os guias do cluster "como-pedir",
   cada URL é https:// e não está vazio. Nunca depende de rede.
2. Unitário da lógica de retry (`verificar_url`), com `fetch` falso
   injectado — nunca toca em rede real, mesmo padrão de
   `tests/test_scraper_fallback.py` para `wayback_fallback.py`.

A verificação real contra a rede (HEAD/GET a seg-social.pt, autenticacao.gov.pt)
corre só em CI, via `scripts/verificar_urls_como_pedir.py` — ver
`.github/workflows/canario-urls.yml` (diário, fora do push a main desde
2026-09-30).
Não faz sentido embutir pedidos de rede reais na suite pytest determinística
(mesma razão por que `smoke_producao.sh`/`verificar_calendario_mensal.py`
também vivem fora do pytest — só um runner real do GitHub Actions tem
acesso à internet completo, ver CLAUDE.md).
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import carregar_clusters  # noqa: E402
from verificar_urls_como_pedir import (  # noqa: E402
    CONFIG_URLS,
    ESPERAS_S,
    FetchResposta,
    carregar_config,
    corpo_da_issue,
    verificar_url,
)

CLUSTERS = carregar_clusters()
CLUSTER_COMO_PEDIR = next(c for c in CLUSTERS if c.id == "como-pedir")


def test_config_e_json_valido():
    assert CONFIG_URLS.exists(), f"{CONFIG_URLS} não existe"
    dados = json.loads(CONFIG_URLS.read_text(encoding="utf-8"))
    assert isinstance(dados, dict)
    assert dados, "configuração de URLs vazia"


@pytest.mark.parametrize(
    "pagina", [p.slug for p in CLUSTER_COMO_PEDIR.paginas if p.tipo == "artigo"],
)
def test_cada_guia_do_cluster_tem_pelo_menos_um_url_configurado(pagina):
    config = carregar_config()
    assert pagina in config, f"{pagina} não tem entrada em {CONFIG_URLS.name}"
    assert len(config[pagina]) >= 1, f"{pagina} não tem nenhum URL configurado"


def test_todas_as_entradas_da_config_correspondem_a_paginas_reais_do_cluster():
    config = carregar_config()
    slugs_cluster = {p.slug for p in CLUSTER_COMO_PEDIR.paginas}
    for guia in config:
        assert guia in slugs_cluster, (
            f"'{guia}' em {CONFIG_URLS.name} não é uma página do cluster 'como-pedir'"
        )


def test_todos_os_urls_sao_https_e_nao_vazios():
    config = carregar_config()
    for guia, entradas in config.items():
        for entrada in entradas:
            assert entrada["url"].startswith("https://"), f"{guia}: URL não-https: {entrada['url']}"
            assert entrada.get("descricao"), f"{guia}: URL sem descrição — {entrada['url']}"


# --- Lógica de retry, sem rede real ---------------------------------------

def _sem_dormir(_):
    pass


def test_verificar_url_sucesso_na_primeira_tentativa():
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        return FetchResposta(200, 200, None, url)

    resultado = verificar_url("https://exemplo.pt", fetch, dormir=_sem_dormir)
    assert resultado.ok is True
    assert resultado.status == 200
    assert resultado.tentativas == 1
    assert len(chamadas) == 1


def test_405_seguido_de_200_recupera_com_esperas_crescentes():
    """Caso real: 405 intermitente em www.sns24.gov.pt (set. 2026)."""
    respostas = iter([FetchResposta(405, 405, 405, "https://www.sns24.gov.pt/"),
                      FetchResposta(200, 200, None, "https://www.sns24.gov.pt/")])
    esperas = []
    resultado = verificar_url("https://www.sns24.gov.pt", lambda u: next(respostas), dormir=esperas.append)
    assert resultado.ok is True
    assert resultado.tentativas == 2
    assert esperas == [ESPERAS_S[0]]


def test_404_falha_logo_sem_retry():
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        return FetchResposta(404, 404, 404, url)

    resultado = verificar_url("https://exemplo.pt/pagina-inexistente", fetch, dormir=_sem_dormir)
    assert resultado.ok is False
    assert resultado.status == 404
    assert len(chamadas) == 1
    assert "definitiva" in resultado.motivo


def test_dominio_inexistente_falha_logo_sem_retry():
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        raise ConnectionError("HTTPSConnectionPool: NameResolutionError: Failed to resolve")

    resultado = verificar_url("https://nao-existe.gov.pt", fetch, dormir=_sem_dormir)
    assert resultado.ok is False
    assert len(chamadas) == 1


def test_405_persistente_falha_a_4a_tentativa_com_as_tres_esperas():
    esperas = []
    resultado = verificar_url(
        "https://www.sns24.gov.pt", lambda u: FetchResposta(405, 405, 405, u), dormir=esperas.append
    )
    assert resultado.ok is False
    assert resultado.tentativas == 4
    assert esperas == list(ESPERAS_S) == [15, 45, 90]
    assert "4/4" in resultado.motivo
    assert (resultado.status_head, resultado.status_get) == (405, 405)


def test_timeout_e_transitorio_e_tem_retry():
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        raise TimeoutError("Connection to www.autenticacao.gov.pt timed out. (connect timeout=15)")

    resultado = verificar_url("https://www.autenticacao.gov.pt", fetch, dormir=_sem_dormir)
    assert resultado.ok is False
    assert len(chamadas) == 4
    assert "timed out" in resultado.motivo


def test_corpo_da_issue_tem_mencao_e_status_head_get_de_cada_url():
    resultados = [
        {"url": "https://www.sns24.gov.pt", "ok": False, "status": 405, "motivo": "falhou 4/4 tentativas — HTTP 405",
         "status_head": 405, "status_get": 405, "url_final": "https://www.sns24.gov.pt/", "tentativas": 4},
        {"url": "https://www.gov.pt", "ok": True, "status": 200, "motivo": "OK",
         "status_head": 200, "status_get": None, "url_final": "https://www.gov.pt/", "tentativas": 1},
    ]
    corpo = corpo_da_issue(resultados, "2026-10-01 07:23", "https://github.com/x/y/actions/runs/1")
    assert corpo.startswith("@nunovinhas-creator")
    assert "| ❌ https://www.sns24.gov.pt | 405 | 405 | https://www.sns24.gov.pt/ | 4 |" in corpo
    assert "| ✅ https://www.gov.pt | 200 | — | https://www.gov.pt/ | 1 |" in corpo
    assert "**1 URL(s) a falhar**, de 2 verificados" in corpo
