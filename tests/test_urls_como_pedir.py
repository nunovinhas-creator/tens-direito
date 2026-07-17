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
corre só em CI, via `scripts/verificar_urls_como_pedir.py` — ver o step
"Canário de URLs oficiais — Como Pedir" em `.github/workflows/integridade.yml`.
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
    FetchResposta,
    carregar_config,
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

def _fetch_fixo(status_code):
    def _fetch(url):
        return FetchResposta(status_code)
    return _fetch


def test_verificar_url_sucesso_na_primeira_tentativa():
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        return FetchResposta(200)

    resultado = verificar_url("https://exemplo.pt", fetch, tentativas=3, dormir=lambda s: None)
    assert resultado.ok is True
    assert resultado.status == 200
    assert len(chamadas) == 1


def test_verificar_url_recupera_apos_falha_transitoria():
    respostas = iter([503, 503, 200])
    chamadas = []

    def fetch(url):
        chamadas.append(url)
        return FetchResposta(next(respostas))

    esperas = []
    resultado = verificar_url(
        "https://exemplo.pt", fetch, tentativas=3, espera_s=1, dormir=lambda s: esperas.append(s)
    )
    assert resultado.ok is True
    assert len(chamadas) == 3
    assert esperas == [1, 1]


def test_verificar_url_falha_persistente_esgota_tentativas_e_reporta():
    def fetch(url):
        return FetchResposta(404)

    resultado = verificar_url("https://exemplo.pt/pagina-inexistente", fetch, tentativas=3, dormir=lambda s: None)
    assert resultado.ok is False
    assert resultado.status == 404
    assert "3/3" in resultado.motivo


def test_verificar_url_erro_de_rede_nunca_e_disfarcado_de_sucesso():
    def fetch(url):
        raise ConnectionError("timeout")

    resultado = verificar_url("https://exemplo.pt", fetch, tentativas=2, dormir=lambda s: None)
    assert resultado.ok is False
    assert "erro de rede" in resultado.motivo
