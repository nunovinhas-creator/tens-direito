#!/usr/bin/env python3
"""
Scraper para fontes oficiais portuguesas.
- Fontes Playwright (Chromium headless): portais .pt com browser real
- Fontes DRE: RSS público da Série I (https://dre.pt/rss/dr1s.rss)

Guarda resultados em data/scraped/[slug]_[YYYY-MM-DD].json
e data/scraped/[slug]_latest.json.

Modo de uso:
  python scripts/scraper_playwright.py               # scrape completo
  python scripts/scraper_playwright.py --mode=detect # só comparação de hashes
"""

import argparse
import hashlib
import json
import logging
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from classificador_resposta import classificar_resposta, Estado, FonteConfig  # noqa: E402
from wayback_fallback import decidir_estado_apos_bloqueio  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DIR = BASE_DIR / "data" / "scraped"
LOG_DIR = Path(__file__).resolve().parent / "logs"

SCRAPED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

BLOQUEIOS_PATH = BASE_DIR / "data" / "bloqueios.json"

# FonteConfig por slug — calibrado com dados reais (2026-06-30)
# seg_social reais esperados >>500 chars; login page = 23 chars (título apenas)
# dge/mega reais: 1731–2534 chars; iefp real: 4280 chars
_FONTE_CONFIGS: dict[str, FonteConfig] = {
    # As URLs planas (antigas e novas) redireccionam sempre para o portal
    # de autenticação /ptss/pssd/home — confirmado num runner real, com e
    # sem Playwright. "app.seg-social.pt" continua para compatibilidade
    # com dados antigos; "seg-social.pt/ptss/pssd/home" apanha o gateway
    # sem apanhar os deep-links /ptss/pssd/menu/... usados abaixo (ver
    # CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
    "seg_social_abono": FonteConfig(
        nome="Segurança Social — Abono de Família",
        min_chars_uteis=500,
        dominios_login=("app.seg-social.pt", "seg-social.pt/ptss/pssd/home"),
        ancora_conteudo=("abono de família",),
        metodo="playwright",
    ),
    "seg_social_rsi": FonteConfig(
        nome="Segurança Social — RSI",
        min_chars_uteis=500,
        dominios_login=("app.seg-social.pt", "seg-social.pt/ptss/pssd/home"),
        ancora_conteudo=("rendimento social de inserção",),
        metodo="playwright",
    ),
    "dge_ase": FonteConfig(nome="DGE — ASE", min_chars_uteis=300),
    "dge_manuais": FonteConfig(nome="DGE — Manuais Escolares", min_chars_uteis=300),
    "iefp_desemprego": FonteConfig(
        nome="IEFP — Subsídio de Desemprego",
        min_chars_uteis=500,
        ancora_conteudo=("subsídio de desemprego",),
        metodo="http",
    ),
    "mega_datas": FonteConfig(nome="DGE — MEGA datas", min_chars_uteis=300),
    # IGeFE, I.P. é a entidade que emite de facto os vouchers MEGA aos
    # encarregados de educação — mega_datas/dge_manuais só vigiam
    # dge.mec.pt, que pode não ser a 1.ª fonte a reflectir o anúncio (ver
    # CLAUDE.md "PÁGINAS COM DATAS SAZONAIS"). Calibrado com dados reais
    # de um runner (2026-07-06): conteúdo útil real (título + parágrafo
    # ".ig-publicsite-paragraph") ~1000 chars — 300 dá margem sem deixar
    # passar um "conteúdo suspeito" como OK. "voucher" só aparece no
    # parágrafo de conteúdo real, nunca na navegação/menu/rodapé.
    "igefe_mega": FonteConfig(
        nome="IGeFE — Vouchers MEGA",
        min_chars_uteis=300,
        ancora_conteudo=("voucher",),
        metodo="http",
    ),
    # Pesquisa de frase exacta no diariodarepublica.pt via interacção real
    # com a caixa de pesquisa (ver "pesquisa_interactiva" em
    # FONTES_PLAYWRIGHT). A âncora é o eco do termo COM aspas na página de
    # resultados ('Resultados de: "prestação social única"') — só aparece
    # quando o filtro foi de facto aplicado; a navegação directa por URL
    # devolve o índice inteiro da legislação (2,2M resultados) SEM esse
    # eco, por isso nunca fica OK por engano. min_chars calibrado com
    # dados reais de um runner (2026-07-07): página filtrada (2 resultados)
    # ~2400 chars de texto útil; página de erro do DRE ~800.
    "dre_psu": FonteConfig(
        nome="DRE — Pesquisa PSU decreto-lei",
        min_chars_uteis=1500,
        ancora_conteudo=('"prestação social única"',),
    ),
    # Watchlist do cluster Habitação (Sessão 3, 2026-07-20) — mesmo
    # mecanismo de pesquisa de frase exacta do dre_psu, nunca calibrado
    # contra um runner real nesta sessão (WebFetch/curl bloqueados para
    # domínios externos, mesma limitação documentada em várias sessões
    # anteriores) — a 1.ª corrida real do pipeline é que confirma os
    # min_chars_uteis; um valor de 1500 (igual ao dre_psu, mesmo tipo de
    # pesquisa de frase exacta no mesmo site) é o ponto de partida honesto,
    # não um número calibrado. Cobre os gatilhos 1+2 da watchlist (revogação
    # do PAER e a eventual reforma "produto único" que o funda com outros
    # apoios — qualquer diploma que reforme ou revogue o PAER tem de
    # referir o seu nome oficial na ementa para ser juridicamente válido).
    "dre_habitacao_paer": FonteConfig(
        nome="DRE — Pesquisa Apoio Extraordinário à Renda / reforma do arrendamento",
        min_chars_uteis=1500,
        ancora_conteudo=('"apoio extraordinário à renda"',),
    ),
    # Gatilho 3 da watchlist — prorrogação ou alteração da Garantia
    # Pública (DL 44/2024), crítico perto do prazo de 31/12/2026 já
    # registado em dados/parametros/habitacao.yaml. Pesquisa pela citação
    # do próprio diploma — qualquer decreto-lei que o altere ou prorrogue
    # tem de o citar na ementa, mais robusto do que pesquisar pelo nome
    # popular da medida (que pode variar).
    "dre_habitacao_garantia": FonteConfig(
        nome="DRE — Pesquisa alteração/prorrogação da Garantia Pública (DL 44/2024)",
        min_chars_uteis=1500,
        ancora_conteudo=('"Decreto-Lei n.º 44/2024"',),
    ),
    # Sentinela de SINAL para a Portaria anual que fixa o IAS (Indexante
    # dos Apoios Sociais) — 2026-07-28. Mesmo mecanismo de pesquisa de
    # frase exacta do dre_psu/dre_habitacao_* (pesquisa_interactiva,
    # frase entre aspas — o DRE guarda o termo de pesquisa num cookie de
    # sessão, nenhum parâmetro de URL filtra em navegação directa). O
    # termo é a frase que a própria Portaria usa para se identificar
    # ("fixa o valor do indexante dos apoios sociais para..."). Nunca
    # extrai nem escreve nenhum valor de IAS — é só sinal para revisão
    # MANUAL, nunca um provider de valor (ver source_adapter.py, peça
    # morta, e a decisão de não a usar). Nunca calibrado contra um
    # runner real nesta sessão (WebFetch/curl bloqueados para domínios
    # externos) — a 1.ª corrida real do pipeline confirma o
    # min_chars_uteis; 1500 (igual ao dre_psu/dre_habitacao_*, mesmo
    # tipo de pesquisa de frase exacta no mesmo site) é o ponto de
    # partida honesto, não um número calibrado.
    "dre_ias": FonteConfig(
        nome="DRE — Pesquisa Portaria do IAS",
        min_chars_uteis=1500,
        ancora_conteudo=('"indexante dos apoios sociais"',),
    ),
    # Sentinela irmão do dre_psu, criado a 2026-08-16 (Fase 2, Commit
    # 5/5 — fecho do sentinela dre_psu original): vigia as Portarias de
    # regulamentação do Decreto-Lei n.º 166/2026 (a PSU) que o próprio
    # diploma deixa por publicar — confirmado directamente pelo Nuno na
    # leitura do texto real (dre.pt continua bloqueado nesta sessão):
    # artigo 17.º (fórmula de apoios à habitação com carácter de
    # regularidade, dependente de uma estatística do INE actualizada por
    # portaria — já documentado como "único ponto ainda sem valor
    # concreto" em psu-quando-entra-em-vigor.html/simulador-psu.html) e
    # artigos 32.º/59.º (procedimentos e meios de prova da candidatura).
    # Mesmo mecanismo de pesquisa de frase exacta do dre_psu/dre_ias, mas
    # pesquisando pelo NÚMERO do decreto-lei (mesmo padrão robusto de
    # dre_habitacao_garantia — qualquer Portaria que o regulamente tem de
    # o citar na ementa) em vez de uma frase descritiva, e filtrando só
    # resultados do tipo Portaria (nunca Decreto-Lei — esse já existe).
    # min_chars_uteis 1500 é o ponto de partida honesto (nunca calibrado
    # contra um runner real nesta sessão — WebFetch/curl bloqueados),
    # mesmo padrão já usado para dre_habitacao_paer/dre_habitacao_garantia/
    # dre_ias.
    "dre_psu_regulamentacao": FonteConfig(
        nome="DRE — Pesquisa Portaria(s) de regulamentação da PSU",
        min_chars_uteis=1500,
        ancora_conteudo=('"Decreto-Lei n.º 166/2026"',),
    ),
}

# Slugs que vigiam a mesma transição real (datas de emissão dos vales MEGA
# para o novo ano lectivo) e por isso partilham a mesma lógica rica de
# detecção (_detectar_datas_mega) e a mesma chave de aviso — para que o
# pipeline dispare a MESMA Issue independentemente de qual fonte a detectar
# primeiro (ver CLAUDE.md "PÁGINAS COM DATAS SAZONAIS").
MEGA_SLUGS_DATAS_RICAS = ("mega_datas", "igefe_mega")


def _fonte_config(slug: str) -> FonteConfig:
    return _FONTE_CONFIGS.get(slug, FonteConfig(nome=slug))


# Perfil de browser por fonte — omissão = comportamento de produção
# inalterado (stealth + headers custom + viewport fixo, como sempre foi).
# Só fontes com uma entrada em _PERFIL_POR_SLUG abrem um browser context
# à parte, com um perfil diferente — usado para isolar qual componente
# do contexto Playwright está a despoletar um redirect/bloqueio numa
# fonte específica (ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
@dataclass(frozen=True)
class PerfilBrowser:
    stealth: bool = True
    headers_custom: bool = True
    viewport_fixo: bool = True


# seg_social_abono/rsi: diagnóstico num runner real (2026-07-03, 4 perfis
# x 2 deep-links) isolou extra_http_headers como o único componente que
# faz o deep-link cair — não num simples redirect de login, mas num erro
# 500 real do backend (/ptss/fraw/errors/500?dswid=...). stealth e
# viewport fixo passaram isoladamente sem problema, tal como "nu" — só
# headers_custom=True falhou nos 2 alvos. Ver CLAUDE.md "SEG-SOCIAL —
# ESTRATÉGIA DE FETCH".
_PERFIL_POR_SLUG: dict[str, PerfilBrowser] = {
    "seg_social_abono": PerfilBrowser(headers_custom=False),
    "seg_social_rsi": PerfilBrowser(headers_custom=False),
    # dre_psu: perfil idêntico ao do diagnóstico real que provou a pesquisa
    # interactiva a funcionar (2026-07-07, runner com contexto UA/locale/
    # timezone/viewport, SEM stealth e SEM extra_http_headers) — mesma
    # lição do seg-social: nunca acrescentar componentes de contexto não
    # provados contra o backend real (extra_http_headers chegou a provocar
    # um erro 500 genuíno no portal da Segurança Social).
    "dre_psu": PerfilBrowser(stealth=False, headers_custom=False),
    # Mesmo perfil do dre_psu — mesmo site (diariodarepublica.pt), mesma
    # precaução contra o erro 500 real já confirmado com extra_http_headers
    # noutro domínio da Segurança Social (ver "SEG-SOCIAL — ESTRATÉGIA DE
    # FETCH" no CLAUDE.md) — nunca acrescentar um componente de contexto
    # não provado contra um backend que já se sabe sensível a headers.
    "dre_habitacao_paer": PerfilBrowser(stealth=False, headers_custom=False),
    "dre_habitacao_garantia": PerfilBrowser(stealth=False, headers_custom=False),
    # dre_ias: mesmo site (diariodarepublica.pt), mesmo mecanismo de
    # pesquisa interactiva — herda a calibração provada do dre_psu sem
    # qualquer alteração (extra_http_headers já provocou um erro 500
    # real no backend da Segurança Social noutro domínio; nunca
    # acrescentar esse componente a uma fonte nova sem prova própria).
    "dre_ias": PerfilBrowser(stealth=False, headers_custom=False),
    # dre_psu_regulamentacao: mesmo site, mesma precaução — sem prova
    # própria de que extra_http_headers/stealth funcionam contra este
    # backend, herda a calibração já provada para dre_psu/dre_ias.
    "dre_psu_regulamentacao": PerfilBrowser(stealth=False, headers_custom=False),
}


def _perfil_fonte(slug: str) -> PerfilBrowser:
    return _PERFIL_POR_SLUG.get(slug, PerfilBrowser())


def _criar_context(browser, perfil: PerfilBrowser):
    kwargs = dict(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        locale="pt-PT",
        timezone_id="Europe/Lisbon",
    )
    if perfil.headers_custom:
        kwargs["extra_http_headers"] = {
            "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    if perfil.viewport_fixo:
        kwargs["viewport"] = {"width": 1280, "height": 900}

    context = browser.new_context(**kwargs)
    if perfil.stealth:
        from playwright_stealth import Stealth
        Stealth().apply_stealth_sync(context)
    return context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scraper_playwright.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ── Fontes Playwright ──────────────────────────────────────────────────────────
FONTES_PLAYWRIGHT = [
    {
        # URL plana redirecciona sempre para o gateway de autenticação
        # (confirmado num runner real, com e sem Playwright) — usa-se o
        # deep-link do portal novo, que serve o conteúdo real sem sessão
        # desde que se espere pela âncora renderizada (ver _obter_html).
        "slug": "seg_social_abono",
        "url": "https://www.seg-social.pt/ptss/pssd/menu/familia/desenvolvimento-criancas-jovens/abono-familia-criancas-jovens",
        "titulo_js": True,
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
            "tabelas": "table",
        },
    },
    {
        "slug": "seg_social_rsi",
        "url": "https://www.seg-social.pt/ptss/pssd/menu/acao-social/apoios-respostas-sociais/rendimento-social-insercao",
        "titulo_js": True,
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    # dge.mec.pt/acao-social-escolar devolve 403 para bots.
    # Estratégia: homepage DGE para links/notícias ASE + DRE API para diplomas.
    {
        "slug": "dge_ase",
        "url": "https://www.dge.mec.pt",
        "url_fallback": "https://dre.pt/pesquisa?q=acao+social+escolar",
        "nota": "dge.mec.pt/acao-social-escolar bloqueado — usar DRE como fonte primária para ASE",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
            "links": "a[href]",
        },
    },
    {
        "slug": "dge_manuais",
        "url": "https://www.dge.mec.pt/manuais-escolares",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    # IEFP só recebe o pedido; decisão e pagamento são da Seg. Social.
    # URL correcto: /subsidio-desemprego (sem /en/ e sem hífen duplo).
    # metodo="http" (ver _FONTE_CONFIGS) — página real acessível via
    # pedido simples, confirmado num runner real; sem url_fallback porque
    # scrape_http() não tem lógica de fallback própria.
    {
        "slug": "iefp_desemprego",
        "url": "https://www.iefp.pt/subsidio-desemprego",
        "nota": "IEFP recebe pedido; decisão e pagamento são da Segurança Social",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
    },
    {
        "slug": "mega_datas",
        "url": "https://www.dge.mec.pt/manuais-escolares",
        "nota": "DGE manuais escolares — detectar datas de atribuição de vouchers 2026/2027",
        "seletores": {
            "titulo": "h1",
            "paragrafos": "p",
            "listas": "ul li, ol li",
        },
        "detectar_ano": "2026/2027",
    },
    {
        # metodo="http" (ver _FONTE_CONFIGS) — página real acessível via
        # pedido simples, confirmado num runner real (2026-07-06). O
        # conteúdo real (secção "Emissão de Vouchers", hoje ainda para o
        # ano letivo 2025/2026) vive num <div class="ig-publicsite-paragraph">,
        # nunca dentro de <p> — confirmado por inspecção directa da
        # estrutura HTML, não assumido a partir de um selector genérico.
        "slug": "igefe_mega",
        "url": "https://www.igefe.mec.pt/Page/Index/199",
        "nota": (
            "IGeFE, I.P. — entidade que emite os vouchers MEGA aos encarregados "
            "de educação; complementa mega_datas/dge_manuais, que só vigiam "
            "dge.mec.pt (ver CLAUDE.md 'PÁGINAS COM DATAS SAZONAIS')"
        ),
        "seletores": {
            "titulo": "h1",
            "paragrafos": ".ig-publicsite-paragraph",
            "listas": "ul li, ol li",
        },
        "detectar_ano": "2026/2027",
    },
    {
        "slug": "dre_psu",
        # Detectar a publicação do DECRETO-LEI da PSU (prazo PRR: 31 ago 2026).
        # Mecanismo confirmado num runner real com browser interactivo
        # (2026-07-07, Issue #54): a pesquisa do diariodarepublica.pt é uma
        # SPA OutSystems que guarda o termo num cookie — NENHUM parâmetro de
        # URL (?q=, ?termo=, caminho antigo/novo) filtra em navegação
        # directa (devolve sempre o índice inteiro: 2,2M resultados). A URL
        # antiga (dre.pt/pesquisa?q=...) devolve hoje um soft-404. Por isso
        # esta fonte usa "pesquisa_interactiva": navegar à home, escrever o
        # termo na caixa (input[type='search']) e premir Enter — com ASPAS,
        # que forçam frase exacta no Elasticsearch por trás (confirmado:
        # 2 resultados vs 12.651 sem aspas). Selectores calibrados com o
        # markup real: cada resultado é um <a href="/dr/detalhe/..."> com o
        # título do acto; títulos/designações vivem em span[data-expression],
        # nunca em <p>.
        "url": "https://diariodarepublica.pt/dr/home",
        "nota": "DRE — vigiar publicação do decreto-lei da PSU (prazo PRR: 31 ago 2026)",
        "pesquisa_interactiva": {
            "campo": "input[type='search']",
            "termo": '"prestação social única"',
        },
        "seletores": {
            "titulo": "h1",
            "paragrafos": "span[data-expression]",
            "listas": "a[href*='/dr/detalhe/']",
        },
        "detectar_decreto_lei_psu": True,
    },
    {
        "slug": "dre_habitacao_paer",
        # Watchlist do cluster Habitação (Sessão 3, 2026-07-20) — vigiar a
        # revogação/reestruturação do Apoio Extraordinário à Renda (PAER)
        # e uma eventual reforma "produto único" que o funda com Porta 65/
        # Porta 65+/Arrendar para Subarrendar (o Governo manifestou essa
        # intenção sem projecto de lei publicado à data de verificação —
        # ver primeiro-direito.html/porta-65.html). Mesmo mecanismo do
        # dre_psu (pesquisa_interactiva, frase exacta entre aspas) — nunca
        # calibrado contra um runner real nesta sessão (WebFetch/curl
        # bloqueados para domínios externos); a 1.ª corrida do pipeline
        # confirma o min_chars_uteis real.
        "url": "https://diariodarepublica.pt/dr/home",
        "nota": "DRE — vigiar revogação do PAER ou reforma dos apoios ao arrendamento",
        "pesquisa_interactiva": {
            "campo": "input[type='search']",
            "termo": '"apoio extraordinário à renda"',
        },
        "seletores": {
            "titulo": "h1",
            "paragrafos": "span[data-expression]",
            "listas": "a[href*='/dr/detalhe/']",
        },
        "detectar_decreto_lei": {
            "chave_aviso": "dre_habitacao_paer_decreto_detectado",
            "mensagem_log": "%s: DECRETO-LEI sobre o Apoio Extraordinário à Renda detectado em "
                             "DRE — confirmar se revoga/substitui o PAER!\n%s",
            # Corte de recência (achado real na 1.ª corrida do pipeline,
            # 2026-07-20): a pesquisa devolve sempre o diploma fundador do
            # PAER (DL n.º 20-B/2023) e as suas alterações já conhecidas —
            # sem isto, dispararia todos os dias. Só conta "novo" um item
            # datado a partir da activação desta watchlist.
            "desde": "2026-07-20",
        },
    },
    {
        "slug": "dre_habitacao_garantia",
        # Watchlist do cluster Habitação (Sessão 3, 2026-07-20) — vigiar
        # prorrogação ou alteração da Garantia Pública no crédito
        # habitação (DL 44/2024), crítico perto do prazo actual de
        # 31/12/2026 (dados/parametros/habitacao.yaml). Pesquisa pela
        # citação do próprio diploma — qualquer decreto-lei que o altere
        # tem de o citar na ementa. Mesmo mecanismo do dre_psu, mesma
        # ressalva de calibração (nunca testado contra um runner real
        # nesta sessão).
        "url": "https://diariodarepublica.pt/dr/home",
        "nota": "DRE — vigiar alteração/prorrogação da Garantia Pública (DL 44/2024, prazo actual: 31 dez 2026)",
        "pesquisa_interactiva": {
            "campo": "input[type='search']",
            "termo": '"Decreto-Lei n.º 44/2024"',
        },
        "seletores": {
            "titulo": "h1",
            "paragrafos": "span[data-expression]",
            "listas": "a[href*='/dr/detalhe/']",
        },
        "detectar_decreto_lei": {
            "chave_aviso": "dre_habitacao_garantia_decreto_detectado",
            "mensagem_log": "%s: DECRETO-LEI que cita o DL 44/2024 (Garantia Pública) detectado em "
                             "DRE — confirmar se altera/prorroga o prazo!\n%s",
            # Mesmo corte de recência do dre_habitacao_paer — mesma
            # precaução, mesmo que a 1.ª corrida real (2026-07-20) tenha
            # devolvido zero resultados para esta fonte.
            "desde": "2026-07-20",
        },
    },
    {
        "slug": "dre_ias",
        # Sentinela de SINAL (2026-07-28) — vigiar a publicação de uma
        # nova Portaria que fixa o IAS (Indexante dos Apoios Sociais),
        # base de cálculo de várias prestações (abono, subsídio de
        # doença, CSI, IMT Jovem/Garantia Pública em Habitação, ASE por
        # derivação 50%/100% do IAS). Nunca extrai nem escreve nenhum
        # valor — só avisa para revisão MANUAL dos YAML de parâmetros
        # (ver "detectar_portaria" abaixo e o bloco de Issue em
        # pipeline-diario.yml). Mesmo mecanismo do dre_psu/dre_habitacao_*
        # (pesquisa_interactiva, frase exacta entre aspas — o DRE guarda
        # o termo de pesquisa num cookie de sessão, nenhum parâmetro de
        # URL filtra em navegação directa).
        "url": "https://diariodarepublica.pt/dr/home",
        "nota": "DRE — vigiar nova Portaria do IAS (revisão MANUAL de dados/parametros/*.yaml)",
        "pesquisa_interactiva": {
            "campo": "input[type='search']",
            "termo": '"indexante dos apoios sociais"',
        },
        "seletores": {
            "titulo": "h1",
            "paragrafos": "span[data-expression]",
            "listas": "a[href*='/dr/detalhe/']",
        },
        "detectar_portaria": {
            "chave_aviso": "dre_ias_portaria_detectada",
            "mensagem_log": "%s: Nova PORTARIA do IAS detectada em DRE — rever valores MANUALMENTE!\n%s",
            # Corte de recência OBRIGATÓRIO desde o 1.º commit — a
            # Portaria do IAS existe todos os anos desde 2006 (nunca uma
            # "correcção a fazer depois": a mesma lição já custou uma
            # Issue falsa real em dre_habitacao_paer, Issue #73,
            # 2026-07-20 — sem isto, a pesquisa de frase exacta encontra
            # sempre as Portarias antigas do IAS e dispara todos os
            # dias). Só conta como "nova" uma Portaria datada a partir da
            # activação desta watchlist.
            "desde": "2026-07-28",
        },
    },
    {
        "slug": "dre_psu_regulamentacao",
        # Sentinela irmão do dre_psu (2026-08-16, Fase 2, Commit 5/5) —
        # ver o comentário completo junto à entrada em _FONTE_CONFIGS.
        # Vigia Portaria(s) que regulamentem o DL 166/2026 (art. 17.º
        # renda de referência; arts. 32.º/59.º procedimentos e meios de
        # prova). Pesquisa pelo número do decreto-lei (padrão robusto de
        # dre_habitacao_garantia), filtrando só resultados do tipo
        # Portaria.
        "url": "https://diariodarepublica.pt/dr/home",
        "nota": ("DRE — vigiar Portaria(s) de regulamentação da PSU "
                 "(art. 17.º renda de referência; arts. 32.º/59.º "
                 "procedimentos e meios de prova)"),
        "pesquisa_interactiva": {
            "campo": "input[type='search']",
            "termo": '"Decreto-Lei n.º 166/2026"',
        },
        "seletores": {
            "titulo": "h1",
            "paragrafos": "span[data-expression]",
            "listas": "a[href*='/dr/detalhe/']",
        },
        "detectar_portaria": {
            "chave_aviso": "dre_psu_regulamentacao_portaria_detectada",
            "mensagem_log": "%s: Portaria de regulamentação da PSU detectada em "
                             "DRE — confirmar se é o art. 17.º ou os arts. "
                             "32.º/59.º!\n%s",
            # Corte de recência: tecnicamente redundante (o DL 166/2026 é
            # novo de 13/08/2026, não pode haver Portaria antiga a citá-lo)
            # — mantido por hábito defensivo consistente com
            # dre_habitacao_paer/dre_habitacao_garantia/dre_ias, custo zero.
            "desde": "2026-08-16",
        },
    },
]

# O DRE não disponibiliza feed RSS acessível nos runners GitHub Actions.
# Verificação de nova legislação é feita manualmente em https://dre.pt
# quando o validador de conteúdo detecta mudanças nas fontes principais.
# Ver data/scraped/dre_status.json para o estado actual.


# ── Utilitários Playwright ─────────────────────────────────────────────────────

def _texto_limpo(el) -> str:
    return " ".join(el.get_text(separator=" ").split()) if el else ""


def _extrair_conteudo(html: str, seletores: dict) -> dict:
    soup = BeautifulSoup(html, "lxml")
    conteudo: dict = {}

    if "titulo" in seletores:
        el = soup.select_one(seletores["titulo"])
        conteudo["titulo"] = _texto_limpo(el)

    if "paragrafos" in seletores:
        conteudo["paragrafos"] = [
            _texto_limpo(p)
            for p in soup.select(seletores["paragrafos"])
            if len(p.get_text(strip=True)) > 40
        ][:15]

    if "listas" in seletores:
        conteudo["itens_lista"] = [
            _texto_limpo(li)
            for li in soup.select(seletores["listas"])
            if len(li.get_text(strip=True)) > 10
        ][:30]

    if "tabelas" in seletores:
        tabelas = []
        for table in soup.select(seletores["tabelas"])[:3]:
            rows = []
            for tr in table.find_all("tr"):
                row = [_texto_limpo(td) for td in tr.find_all(["th", "td"])]
                if any(row):
                    rows.append(row)
            if rows:
                tabelas.append(rows)
        conteudo["tabelas"] = tabelas

    if "links" in seletores:
        conteudo["links_uteis"] = [
            {"texto": _texto_limpo(a), "href": a.get("href", "")}
            for a in soup.select(seletores["links"])
            if a.get("href", "").startswith("http") and len(a.get_text(strip=True)) > 5
        ][:20]

    return conteudo


def _tentar_goto(page, url: str) -> bool:
    for attempt in range(1, 4):
        try:
            response = page.goto(url, timeout=30_000, wait_until="networkidle")
            if response and response.status in (200, 301, 302):
                return True
            log.warning("HTTP %s em %s (tentativa %d)", response.status if response else "N/A", url, attempt)
        except Exception as exc:
            log.warning("Erro tentativa %d para %s: %s", attempt, url, exc)
        if attempt < 3:
            time.sleep(2 ** attempt)
    return False


# Só se marca BLOQUEADO no dia se estas 3 tentativas (Camada 1: recepção +
# classificação, não apenas o goto de rede) falharem todas — bloqueios de
# gov.pt a runners do GitHub são frequentemente transitórios. Espera aleatória
# entre tentativas para não bater sempre no mesmo padrão temporal.
TENTATIVAS_BLOQUEIO = 3
ESPERA_MIN_S = 30
ESPERA_MAX_S = 120


def _obter_html(page, url: str, url_fallback: str | None, slug: str,
                 ancora: str | None = None) -> tuple[str, str] | None:
    """Navega para `url` (com fallback opcional) e devolve `(url_usado,
    html)`. Devolve None só em falha de navegação (rede/timeout) —
    distinto de "conteúdo bloqueado", decidido a jusante pela Camada 1.

    Com `ancora` (fonte com verificação positiva configurada — ver
    ancora_conteudo em FonteConfig): espera explicitamente que a frase
    apareça no DOM em vez de confiar em `networkidle` + sleep fixo — o
    portal novo seg-social.pt/ptss/pssd é uma SPA que reporta "carregada"
    antes do conteúdo real renderizar."""
    url_usado = url
    ok = _tentar_goto(page, url)

    if not ok and url_fallback:
        log.warning("%s: URL principal falhou — a tentar fallback %s", slug, url_fallback)
        url_usado = url_fallback
        ok = _tentar_goto(page, url_fallback)

    if not ok:
        log.error("Falhou após 3 tentativas (principal%s): %s",
                  " + fallback" if url_fallback else "", url)
        return None

    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass

    if ancora:
        try:
            page.wait_for_function(
                "text => document.body && document.body.innerText.toLowerCase().includes(text)",
                arg=ancora.lower(),
                timeout=15_000,
            )
        except Exception as exc:
            log.warning("%s: âncora %r não apareceu no DOM em 15s: %s", slug, ancora, exc)
    else:
        time.sleep(5)

    return url_usado, page.content()


def _obter_html_pesquisa(page, url: str, pesquisa: dict, slug: str,
                         ancora: str | None) -> tuple[str, str] | None:
    """Fluxo interactivo para SPAs cuja pesquisa não é accionável por URL.

    Caso real (dre_psu, confirmado num runner com browser real a
    2026-07-07): o diariodarepublica.pt guarda o termo de pesquisa num
    cookie de sessão — nenhuma query string filtra em navegação directa,
    que devolve sempre o índice inteiro com HTTP 200 (um falso sucesso
    perfeito). Este fluxo navega à página com a caixa de pesquisa,
    escreve o termo e prime Enter; a `ancora` (o eco do termo na página
    de resultados) é a prova de que o filtro foi de facto aplicado — sem
    ela o resultado classifica MUDOU/BLOQUEADO a jusante, nunca OK.

    Qualquer falha de interacção devolve a página no estado em que ficou,
    para a Camada 1 a classificar honestamente — nunca devolve None por
    falha de interacção (None é só para falha de navegação, como em
    _obter_html)."""
    if not _tentar_goto(page, url):
        log.error("%s: navegação para %s falhou após 3 tentativas", slug, url)
        return None
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass

    try:
        campo = page.locator(pesquisa["campo"]).first
        campo.wait_for(state="visible", timeout=15_000)
        campo.click()
        campo.fill(pesquisa["termo"])
        campo.press("Enter")
    except Exception as exc:
        log.warning("%s: interacção com a caixa de pesquisa falhou (%s) — "
                    "a devolver a página actual para classificação honesta", slug, exc)
        return page.url, page.content()

    if ancora:
        try:
            page.wait_for_function(
                "text => document.body && document.body.innerText.toLowerCase().includes(text)",
                arg=ancora.lower(),
                timeout=20_000,
            )
        except Exception as exc:
            log.warning("%s: âncora %r não apareceu após a pesquisa em 20s: %s",
                        slug, ancora, exc)
    # A âncora (eco do termo) aparece antes de a lista de resultados acabar
    # de renderizar — dar tempo à SPA de completar os pedidos e pintar os
    # resultados antes de capturar o HTML.
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except Exception:
        pass
    time.sleep(3)
    return page.url, page.content()


def scrape_playwright(page, fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    url_fallback = fonte.get("url_fallback")
    nota = fonte.get("nota", "")
    log.info("A scrape (Playwright): %s", url)

    config = _fonte_config(slug)
    ancora = config.ancora_conteudo[0] if config.ancora_conteudo else None
    pesquisa = fonte.get("pesquisa_interactiva")
    url_usado, html, classif = url, "", None

    for tentativa in range(1, TENTATIVAS_BLOQUEIO + 1):
        if pesquisa:
            obtido = _obter_html_pesquisa(page, url, pesquisa, slug, ancora)
        else:
            obtido = _obter_html(page, url, url_fallback, slug, ancora=ancora)
        if obtido is None:
            # Falha de navegação (rede/timeout), não de conteúdo bloqueado —
            # já esgotou as suas próprias 3 tentativas dentro de _tentar_goto,
            # sem sentido voltar a tentar aqui.
            return None

        url_usado, html = obtido
        classif = classificar_resposta(status_code=200, corpo=html, url_final=page.url, config=config)

        if classif.estado == Estado.OK:
            break

        log.warning("%s: tentativa %d/%d classificada como %s — motivos: %s",
                    slug, tentativa, TENTATIVAS_BLOQUEIO, classif.estado.value, classif.motivos)
        if tentativa < TENTATIVAS_BLOQUEIO:
            espera = random.uniform(ESPERA_MIN_S, ESPERA_MAX_S)
            log.info("%s: a aguardar %.0fs antes da próxima tentativa", slug, espera)
            time.sleep(espera)

    if classif.estado != Estado.OK:
        return _tratar_nao_ok(slug, url_usado, fonte["seletores"], nota, classif)

    _limpar_bloqueio_hoje(slug)
    conteudo = _extrair_conteudo(html, fonte["seletores"])

    if fonte.get("titulo_js"):
        try:
            titulo_js = page.evaluate(
                "document.querySelector('h1')?.innerText || "
                "document.querySelector('.page-title')?.innerText || "
                "document.title || ''"
            )
            if titulo_js and titulo_js.strip():
                conteudo["titulo"] = titulo_js.strip()
                log.info("%s: título via JS: %s", slug, conteudo["titulo"][:80])
        except Exception as exc:
            log.warning("%s: page.evaluate título falhou: %s", slug, exc)

    resultado = {
        "url": url_usado,
        "url_original": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "conteudo_extraido": conteudo,
    }
    if nota:
        resultado["nota"] = nota

    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado["hash_conteudo"] = hashlib.sha256(hash_payload.encode()).hexdigest()

    _guardar_resultado(slug, resultado)

    # Detectar ano lectivo novo e datas MEGA (ex: MEGA 2026/2027)
    ano_detectar = fonte.get("detectar_ano")
    if ano_detectar and slug in MEGA_SLUGS_DATAS_RICAS:
        _detectar_datas_mega(slug, html, conteudo, ano_detectar)
    elif ano_detectar and ano_detectar in html:
        _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
        log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)

    # Detecção do decreto-lei da PSU em DRE
    if fonte.get("detectar_decreto_lei_psu") and slug == "dre_psu":
        if not _detectar_decreto_psu(slug, conteudo):
            log.info("%s: decreto-lei PSU ainda não publicado em DRE "
                     "(pesquisa de frase exacta sem nenhum Decreto-Lei nos resultados)", slug)

    # Watchlist do cluster Habitação (Sessão 3, 2026-07-20) — mesmo
    # mecanismo genérico acima, config por fonte em "detectar_decreto_lei"
    # (dict com chave_aviso/mensagem_log), nunca hardcoded ao slug como
    # o bloco da PSU acima (histórico, mantido por compatibilidade com os
    # testes existentes).
    deteccao = fonte.get("detectar_decreto_lei")
    if deteccao:
        achou = _detectar_decreto_lei_generico(
            slug, conteudo, deteccao["chave_aviso"], deteccao["mensagem_log"],
            data_minima=deteccao.get("desde"),
        )
        if not achou:
            log.info("%s: nenhum Decreto-Lei novo detectado na pesquisa (%s)",
                      slug, deteccao["chave_aviso"])

    # Sentinela do IAS (2026-07-28) — mesmo mecanismo genérico acima
    # (config por fonte em "detectar_portaria"), só que procura uma
    # Portaria nova em vez de um Decreto-Lei. Nunca extrai nem escreve
    # nenhum valor de IAS — só regista o sinal para revisão MANUAL (ver
    # o bloco de Issue correspondente em pipeline-diario.yml).
    deteccao_portaria = fonte.get("detectar_portaria")
    if deteccao_portaria:
        achou = _detectar_portaria_generico(
            slug, conteudo, deteccao_portaria["chave_aviso"], deteccao_portaria["mensagem_log"],
            data_minima=deteccao_portaria.get("desde"),
        )
        if not achou:
            log.info("%s: nenhuma Portaria nova detectada na pesquisa (%s)",
                      slug, deteccao_portaria["chave_aviso"])

    return resultado


_PADRAO_DATA_FINAL_ITEM = re.compile(r"(\d{4}-\d{2}-\d{2})\s*$")


def _data_item(texto: str) -> str | None:
    """Extrai a data ISO (AAAA-MM-DD) do fim de uma entrada de resultado do
    DRE — ex.: "Decreto-Lei n.º 130/2023 - Diário da República n.º
    248/2023, Série I de 2023-12-27" → "2023-12-27". `None` se não houver
    data reconhecível (nunca assumido "recente" nem "antigo" por omissão —
    ver `_detectar_decreto_lei_generico`)."""
    m = _PADRAO_DATA_FINAL_ITEM.search(texto)
    return m.group(1) if m else None


# Ano embutido no próprio número do acto ("Portaria n.º 257/2012" → "2012")
# — fallback de nível 2 do corte de recência, achado real num runner
# (2026-07-28, calibração do sentinela dre_ias): a pesquisa por
# "indexante dos apoios sociais" devolve consistentemente actos antigos
# e genuínos (ex.: Portaria n.º 257/2012 — RSI, Portaria n.º 214/2019 —
# Programa Regressar, Portaria n.º 187/2023 — actualização IAS) cujo
# texto no DRE nunca inclui o sufixo "Diário da República n.º .../..., Série
# I de AAAA-MM-DD" — só o próprio número do acto. `_data_item` devolve
# sempre `None` para estes, e sem este fallback ficavam presos no nível
# 3 (salvaguarda "nunca descartar") para sempre, disparando a Issue todos
# os dias — o mesmo pesadelo do PAER (Issue #73), só que por ausência de
# data em vez de ausência de corte de recência. Confirmado via WebSearch
# que os 3 são actos reais, não lixo/duplicados — o ano do próprio número
# é a única informação temporal disponível para eles.
_PADRAO_ANO_NUMERO_ATO = re.compile(r"n\.?[ºo]\s*[\w\-]*\/(\d{4})", re.IGNORECASE)


def _ano_item(texto: str) -> str | None:
    """Extrai o ano embutido no número do próprio acto (ex.: "Portaria
    n.º 257/2012" → "2012"; "Portaria n.º 480-A/2025/1 - ..." → "2025",
    o primeiro ano a seguir ao número, antes de qualquer sufixo de
    suplemento/série). `None` se o próprio número não seguir o padrão
    "n.º .../AAAA" (formato totalmente inesperado — ver o nível 3 da
    hierarquia em `_detectar_item_juridico_generico`)."""
    m = _PADRAO_ANO_NUMERO_ATO.search(texto)
    return m.group(1) if m else None


_PADRAO_DECRETO_LEI = re.compile(r"\bdecreto[\s-]?lei\s+n", re.IGNORECASE)
_PADRAO_PORTARIA = re.compile(r"\bportaria\s+n", re.IGNORECASE)


def _detectar_item_juridico_generico(slug: str, conteudo: dict, chave_aviso: str,
                                      mensagem_log: str, padrao: re.Pattern,
                                      data_minima: str | None = None) -> bool:
    """Núcleo partilhado de detecção entre os resultados de uma pesquisa de
    frase exacta no DRE (mecanismo `pesquisa_interactiva`, ver
    `_obter_html_pesquisa`). `padrao` decide QUE tipo de acto conta como
    sinal (Decreto-Lei para `_detectar_decreto_lei_generico`, Portaria
    para `_detectar_portaria_generico` — sentinela do IAS, 2026-07-28) —
    o resto da lógica (verificação por item, corte de recência) é
    idêntico e reutilizado sem duplicação.

    Generalização (Sessão 3, 2026-07-20 — watchlist do cluster Habitação;
    estendida em 2026-07-28 para o sentinela do IAS) da lógica original
    de `_detectar_decreto_psu` — mesmo princípio, reutilizável por
    qualquer fonte que use pesquisa de frase exacta: como a pesquisa usa
    aspas (frase exacta no Elasticsearch do DRE — confirmado num runner
    real para dre_psu: 2 resultados vs 12.651 sem aspas), TODOS os
    resultados extraídos dizem já respeito à frase — basta o título de
    um resultado (itens_lista: um <a href="/dr/detalhe/..."> por acto)
    bater com `padrao` para haver sinal real.

    Verificação por item, deliberadamente — nunca sobre todo o texto
    concatenado, que dispararia com um acto do tipo certo num resultado e
    o termo pesquisado noutro resultado sem relação (falso positivo
    latente já visto nas Issues #55/#56 do MEGA).

    `data_minima` (Issue real, 1.ª corrida do pipeline após a activação
    da watchlist do cluster Habitação, 2026-07-20 — Issue #73): a
    suposição original de que "qualquer acto do tipo certo nos resultados
    é sinal de novidade" só vale para algo que ainda não existe (dre_psu
    — a PSU literalmente não tem diploma nenhum antes do decreto-lei que
    a cria). Para uma watchlist sobre um acto que já existe todos os anos
    (PAER, Garantia Pública, e a Portaria do IAS — publicada anualmente
    desde 2006), a pesquisa de frase exacta encontra sempre o(s)
    diploma(s) anterior(es) — confirmado num runner real para
    dre_habitacao_paer: a pesquisa por "apoio extraordinário à renda"
    devolveu correctamente o DL n.º 20-B/2023 (o diploma fundador do
    PAER) e as suas alterações de 2023-2025, gerando uma Issue falsa que
    dispararia todos os dias sem excepção.

    Corte de recência com hierarquia de 3 níveis (nível 2 acrescentado em
    2026-07-28, calibração do sentinela dre_ias — ver `_ano_item`), nunca
    uma substituição do nível anterior, sempre uma cascata:

    1. Data completa (`_data_item` — "de AAAA-MM-DD" no fim da entrada).
       Se existir, decide sozinha: `>= data_minima` inclui, senão exclui.
       Ganha sempre que está presente — os outros níveis nem são
       tentados.
    2. Só se a data completa faltar: ano embutido no próprio número do
       acto (`_ano_item` — "n.º XXX/AAAA" → "AAAA"). Achado real: a
       pesquisa por "indexante dos apoios sociais" devolve
       consistentemente Portarias antigas e genuínas (2012, 2019, 2023)
       cujo texto no DRE nunca inclui o sufixo de data — sem este nível,
       ficavam presas no nível 3 para sempre, disparando a Issue todos
       os dias (mesmo pesadelo do PAER, só que por ausência de data em
       vez de ausência de corte). Regra: `ano_item < ano(data_minima)`
       exclui (é antigo); `>= ano(data_minima)` mantém como sinal —
       nunca esconde um acto do próprio ano de activação ou posterior,
       mesmo sem a data exacta.
    3. Salvaguarda final, só se NEM a data completa NEM o ano do número
       forem extraíveis (formato totalmente inesperado): mantém sempre
       como potencial sinal (mesmo invariante "nenhum estado de erro
       pode parecer sucesso") — nunca esconde um acto genuinamente novo
       só porque o DRE mudou o formato da entrada de uma forma que nem
       sequer o próprio número do acto é reconhecível.

    O corte de recência (níveis 2+3 dependem de `data_minima` estar
    presente) é OBRIGATÓRIO desde o primeiro commit de qualquer
    watchlist nova sobre um acto já existente — nunca uma correcção a
    aplicar depois de uma Issue falsa já ter sido criada."""
    candidatos = [conteudo.get("titulo", "")] + list(conteudo.get("itens_lista", []))
    achados_brutos = [t for t in candidatos if t and padrao.search(t)]
    if data_minima:
        achados = []
        ano_minimo = data_minima[:4]
        for t in achados_brutos:
            data_t = _data_item(t)
            if data_t is not None:
                # Nível 1 — data completa, decide sozinha.
                if data_t >= data_minima:
                    achados.append(t)
                continue
            ano_t = _ano_item(t)
            if ano_t is not None:
                # Nível 2 — ano do número do acto, só sem data completa.
                if ano_t >= ano_minimo:
                    achados.append(t)
                continue
            # Nível 3 — salvaguarda: nem data nem ano reconhecíveis,
            # nunca descartado em silêncio.
            achados.append(t)
    else:
        achados = achados_brutos
    if not achados:
        return False
    excertos_txt = "\n".join(f"- {t[:300]}" for t in achados[:5])
    _registar_aviso(slug, f"{chave_aviso}:{excertos_txt[:500]}")
    log.warning(mensagem_log, slug, excertos_txt)
    return True


def _detectar_decreto_lei_generico(slug: str, conteudo: dict, chave_aviso: str,
                                    mensagem_log: str,
                                    data_minima: str | None = None) -> bool:
    """Detecta um Decreto-Lei entre os resultados de uma pesquisa de frase
    exacta no DRE — thin wrapper de `_detectar_item_juridico_generico`
    com `padrao=_PADRAO_DECRETO_LEI`. Assinatura e comportamento 100%
    inalterados face à versão anterior a 2026-07-28 (a generalização foi
    só do núcleo interno, para o sentinela do IAS poder reutilizá-lo com
    um padrão diferente — ver `_detectar_portaria_generico`) — mantida
    por compatibilidade com `tests/test_dre_habitacao_watchlist.py` e
    `_detectar_decreto_psu`, que a chamam directamente por nome."""
    return _detectar_item_juridico_generico(
        slug, conteudo, chave_aviso, mensagem_log, _PADRAO_DECRETO_LEI,
        data_minima=data_minima,
    )


def _detectar_portaria_generico(slug: str, conteudo: dict, chave_aviso: str,
                                 mensagem_log: str,
                                 data_minima: str | None = None) -> bool:
    """Detecta uma Portaria entre os resultados de uma pesquisa de frase
    exacta no DRE — mesmo mecanismo de `_detectar_decreto_lei_generico`,
    thin wrapper de `_detectar_item_juridico_generico` com
    `padrao=_PADRAO_PORTARIA`. Sentinela do IAS (2026-07-28): a Portaria
    anual que fixa o Indexante dos Apoios Sociais é o único acto que
    interessa aqui — nunca um Decreto-Lei nem um Despacho, que a pesquisa
    de frase exacta por "indexante dos apoios sociais" também pode
    devolver (ex.: um Despacho que actualiza um valor derivado do IAS
    sem ser a própria Portaria de fixação)."""
    return _detectar_item_juridico_generico(
        slug, conteudo, chave_aviso, mensagem_log, _PADRAO_PORTARIA,
        data_minima=data_minima,
    )


def _detectar_decreto_psu(slug: str, conteudo: dict) -> bool:
    """Detecta o decreto-lei da PSU — ver `_detectar_decreto_lei_generico`
    para o mecanismo completo. Mantido como função própria (em vez de só
    uma chamada inline) porque `tests/test_dre_psu_pesquisa.py` a importa
    directamente por nome; assinatura e fonte config (`_FONTE_CONFIGS`/
    `FONTES_PLAYWRIGHT`) 100% inalteradas desde a Issue #54.

    Corte de recência acrescentado a 2026-08-16 (Fase 2, Commit 5/5 —
    fecho do sentinela): o Decreto-Lei n.º 166/2026, de 13 de agosto, foi
    publicado — sem este corte, a pesquisa por '"prestação social única"'
    encontraria sempre o próprio DL n.º 166/2026 nos resultados e
    dispararia esta Issue todos os dias, para sempre (mesma classe de
    falso positivo já visto no PAER, Issue #73, só que desta vez sobre o
    seu próprio alvo já conhecido, não um alvo antigo). `data_minima`
    hardcoded aqui (nunca no dict de `FONTES_PLAYWRIGHT`, que
    `tests/test_dre_habitacao_watchlist.py::test_dre_psu_continua_a_usar_o_mecanismo_antigo_intocado`
    tranca à forma exacta de antes — `"detectar_decreto_lei" not in
    fonte`) — a fonte continua activa: um FUTURO Decreto-Lei que também
    mencione "prestação social única" (ex.: uma alteração ao regime já
    criado) ainda dispara; só o DL 166/2026 já conhecido deixa de
    re-disparar todos os dias. Sentinela irmão para o que falta
    regulamentar por Portaria (art. 17.º; arts. 32.º/59.º) —
    `dre_psu_regulamentacao`, mais abaixo neste ficheiro."""
    return _detectar_decreto_lei_generico(
        slug, conteudo, "dre_psu_decreto_detectado",
        "%s: DECRETO-LEI PSU DETECTADO EM DRE — rever cluster e publicar valores!\n%s",
        data_minima="2026-08-16",
    )


# ── Guardar resultado ──────────────────────────────────────────────────────────

AVISOS_LOG = SCRAPED_DIR / "avisos.log"
MIN_CHARS_CONTEUDO = 100


def _conteudo_chars(conteudo: dict) -> int:
    """Conta caracteres totais do conteúdo extraído (títulos + parágrafos + listas)."""
    total = len(conteudo.get("titulo", ""))
    for p in conteudo.get("paragrafos", []):
        total += len(p)
    for li in conteudo.get("itens_lista", []):
        total += len(li)
    for r in conteudo.get("resultados", []):
        total += len(r.get("titulo", "")) + len(r.get("sumario", ""))
    return total


def _registar_aviso(slug: str, motivo: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    linha = f"{ts} AVISO slug={slug} motivo={motivo}\n"
    with open(AVISOS_LOG, "a", encoding="utf-8") as f:
        f.write(linha)
    log.warning("AVISO registado em avisos.log: %s — %s", slug, motivo)


def _detectar_datas_mega(slug: str, html: str, conteudo: dict, ano_detectar: str) -> None:
    """Detecta o ano lectivo novo e datas de emissão dos vales MEGA
    (julho/agosto). Partilhada por scrape_playwright()/scrape_http() —
    qualquer fonte em MEGA_SLUGS_DATAS_RICAS usa a mesma lógica e a
    mesma chave de aviso (mega_2026_2027_publicadas), para que o
    pipeline dispare a MESMA Issue independentemente de qual fonte a
    detectar primeiro (dge.mec.pt via mega_datas, ou igefe.mec.pt via
    igefe_mega — ver CLAUDE.md 'PÁGINAS COM DATAS SAZONAIS')."""
    import re as _re
    html_lower = html.lower()
    ano_confirmado = ano_detectar in html
    # Bug real encontrado em produção 2× (2026-07-06, Issues #55 e #56 —
    # ver CLAUDE.md): tanto o padrão solto \d{1,2}\s+de\s+(julho|agosto)
    # (sem âncora ao ano) como uma janela de proximidade de 60 chars
    # (1.ª tentativa de correcção — ainda insuficiente, confirmado no
    # pipeline real: "2026" aparece a menos de 60 chars de "julho" no
    # HTML bruto do igefe_mega mesmo sem relação nenhuma, provavelmente
    # markup/atributos entre o texto visível) geravam falso positivo com
    # a data antiga "28 de julho de 2025" (ano letivo 2025/2026 ainda a
    # decorrer). Corrigido exigindo a frase completa e inequívoca — só
    # "julho de 2026"/"agosto de 2026" (com ou sem o dia à frente) conta,
    # nunca uma proximidade aproximada.
    datas_confirmadas = bool(
        _re.search(r"\b(?:\d{1,2}\s+de\s+)?(julho|agosto)\s+de\s+2026\b", html_lower)
    )
    if ano_confirmado:
        _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
        log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)
    if datas_confirmadas:
        excertos = []
        for p in conteudo.get("paragrafos", []) + conteudo.get("itens_lista", []):
            if any(kw in p.lower() for kw in ["julho", "agosto", "voucher", "vale"]):
                excertos.append(p[:200])
        excertos_txt = "\n".join(f"- {e}" for e in excertos[:5]) or "(sem excertos — ver scrape JSON)"
        _registar_aviso(slug, f"mega_2026_2027_publicadas:{excertos_txt[:300]}")
        log.warning(
            "%s: DATAS MEGA 2026/2027 DETECTADAS — actualizar manuais-escolares-mega.html!\n%s",
            slug, excertos_txt
        )


def _registar_bloqueio(slug: str, url: str, classif) -> None:
    """Acrescenta entrada a data/bloqueios.json (lida pelo pipeline para abrir Issue)."""
    entrada = {
        "slug": slug,
        "url": url,
        "data": datetime.now(timezone.utc).isoformat(),
        "motivos": classif.motivos,
        "chars_uteis": classif.chars_uteis,
    }
    bloqueios: list = []
    if BLOQUEIOS_PATH.exists():
        try:
            bloqueios = json.loads(BLOQUEIOS_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    # Substituir entrada anterior do mesmo slug para o mesmo dia
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bloqueios = [b for b in bloqueios if not (b["slug"] == slug and b["data"][:10] == hoje)]
    bloqueios.append(entrada)
    BLOQUEIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    BLOQUEIOS_PATH.write_text(json.dumps(bloqueios, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Bloqueio registado: %s → %s", slug, BLOQUEIOS_PATH)


def _limpar_bloqueio_hoje(slug: str) -> None:
    """Remove qualquer entrada de hoje desta fonte em data/bloqueios.json
    quando ela recupera (OK). Sem isto, uma fonte bloqueada numa corrida
    e recuperada numa corrida seguinte no mesmo dia (ex.: workflow_dispatch
    manual repetido) ficava presa em BLOQUEADO na máquina de estados de
    gerir_estado_fontes.py até ao dia seguinte -- _registar_bloqueio já
    substituía a entrada de hoje ao registar um NOVO bloqueio, mas nada
    a removia quando a fonte simplesmente recuperava. Descoberto e
    corrigido em 2026-07-03 (ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE
    FETCH")."""
    if not BLOQUEIOS_PATH.exists():
        return
    try:
        bloqueios = json.loads(BLOQUEIOS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    novo = [b for b in bloqueios if not (b.get("slug") == slug and b.get("data", "")[:10] == hoje)]
    if len(novo) != len(bloqueios):
        BLOQUEIOS_PATH.write_text(json.dumps(novo, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("%s: bloqueio de hoje removido (fonte recuperou)", slug)


def _registar_mudanca_estrutural(slug: str, url: str, classif) -> None:
    """MUDOU: a fonte respondeu (sem sinais reais de bloqueio) mas o
    conteúdo esperado (ancora_conteudo) desapareceu — revisão manual,
    nunca disfarçado de BLOQUEADO. Nunca escreve em data/bloqueios.json:
    não é o mesmo que um dia bloqueado na máquina de estados de
    gerir_estado_fontes.py. Criação de Issue dedicada para este caso
    ainda não implementada — ver CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE
    FETCH" (registado para o futuro)."""
    _registar_aviso(slug, f"mudanca_estrutural:motivos={classif.motivos}:chars_uteis={classif.chars_uteis}")


def _tratar_nao_ok(slug: str, url_usado: str, seletores: dict, nota: str, classif) -> dict | None:
    """Ponto único chamado depois de esgotar TENTATIVAS_BLOQUEIO sem OK.
    MUDOU nunca tenta o fallback Wayback (a fonte respondeu — só o
    conteúdo esperado desapareceu) nem conta como bloqueio; BLOQUEADO
    segue o caminho já existente (Wayback, depois bloqueios.json)."""
    if classif.estado == Estado.MUDOU:
        log.warning("%s: MUDOU após %d tentativas — motivos: %s", slug, TENTATIVAS_BLOQUEIO, classif.motivos)
        _registar_mudanca_estrutural(slug, url_usado, classif)
        return None

    log.warning("%s: BLOQUEADO após %d tentativas — motivos: %s", slug, TENTATIVAS_BLOQUEIO, classif.motivos)
    resultado_arquivo = _tentar_fallback_wayback(slug, url_usado, seletores, nota)
    if resultado_arquivo is not None:
        return resultado_arquivo
    _registar_bloqueio(slug, url_usado, classif)
    return None


def _fetch_json_wayback(url_completo: str) -> dict:
    resp = requests.get(url_completo, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _tentar_fallback_wayback(slug: str, url: str, seletores: dict, nota: str) -> dict | None:
    """Só chamado depois de TENTATIVAS_BLOQUEIO tentativas directas
    falharem. Devolve um resultado com `status: "ok_via_arquivo"` se
    existir snapshot Wayback recente (`wayback_fallback.decidir_estado_apos_bloqueio`),
    ou None se não houver — o chamador trata então como BLOQUEADO normal.
    Nunca escreve em `data/bloqueios.json`: modo arquivo não é a mesma
    coisa que bloqueado, e não deve contar como dia bloqueado na máquina
    de estados de fontes (`gerir_estado_fontes.py`)."""
    decisao = decidir_estado_apos_bloqueio(url, fetch_json=_fetch_json_wayback)
    if decisao["estado"] != "OK_VIA_ARQUIVO":
        # Sem isto, "sem snapshot recente" e "consulta ao Wayback nunca
        # sequer tentada" ficam indistinguíveis no log.
        log.info("%s: sem snapshot Wayback recente disponível — a manter BLOQUEADO", slug)
        return None

    snapshot = decisao["snapshot"]
    try:
        resp = requests.get(snapshot["url"], timeout=20)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("%s: snapshot Wayback encontrado mas falhou a obter conteúdo: %s", slug, exc)
        return None

    conteudo = _extrair_conteudo(resp.text, seletores)
    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado = {
        "url": url,
        "url_original": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok_via_arquivo",
        "modo": "arquivo",
        "data_snapshot": snapshot["timestamp"],
        "url_snapshot": snapshot["url"],
        "conteudo_extraido": conteudo,
        "hash_conteudo": hashlib.sha256(hash_payload.encode()).hexdigest(),
    }
    if nota:
        resultado["nota"] = nota

    log.warning(
        "%s: modo degradado OK_VIA_ARQUIVO — snapshot de %s (%s dia(s) atrás)",
        slug, snapshot["timestamp"], snapshot["dias_desde_snapshot"],
    )
    _registar_aviso(slug, f"modo_arquivo:snapshot={snapshot['timestamp']}:dias={snapshot['dias_desde_snapshot']}")
    _guardar_resultado(slug, resultado)
    return resultado


def _guardar_resultado(slug: str, resultado: dict) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_path = SCRAPED_DIR / f"{slug}_{today}.json"
    latest_path = SCRAPED_DIR / f"{slug}_latest.json"

    # Validação mínima de conteúdo
    conteudo = resultado.get("conteudo_extraido", {})
    chars = _conteudo_chars(conteudo)
    if chars < MIN_CHARS_CONTEUDO:
        motivo = f"conteúdo suspeito: apenas {chars} caracteres (mínimo {MIN_CHARS_CONTEUDO})"
        _registar_aviso(slug, motivo)
        # Achado de 2026-07-05: "conteúdo suspeito" (status "ok", sem sinal
        # de bloqueio, mas conteúdo extraído insuficiente — ex.: dre_psu,
        # 0 chars desde a criação da fonte, nunca detectado) ficava só
        # neste log, sem nunca contar para a máquina de estados de
        # gerir_estado_fontes.py nem gerar Issue — uma fonte podia ficar
        # "OK" e inútil indefinidamente. Reutiliza _registar_bloqueio (a
        # mesma infra-estrutura testada de fonte-bloqueada, 3 dias
        # consecutivos → Issue, fecho automático ao recuperar) em vez de
        # criar uma máquina de estados paralela.
        _registar_bloqueio(
            slug, resultado.get("url", ""),
            SimpleNamespace(motivos=[motivo], chars_uteis=chars),
        )
        # Guardar o ficheiro diário mesmo assim (para auditoria), mas NÃO actualizar latest
        resultado["aviso"] = motivo
        with open(daily_path, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        log.warning("%s: latest NÃO actualizado — %s", slug, motivo)
        return

    with open(daily_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Guardado: %s", daily_path)

    if latest_path.exists():
        try:
            old = json.loads(latest_path.read_text(encoding="utf-8"))
            if old.get("hash_conteudo") == resultado["hash_conteudo"]:
                log.info("%s: conteúdo idêntico ao latest — sem atualização", slug)
                return
        except Exception:
            pass

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    log.info("Atualizado latest: %s", latest_path)


# ── Fontes via HTTP simples (sem browser) ───────────────────────────────────────
# Para fontes cuja página real é acessível com um pedido simples (ver
# CLAUDE.md "SEG-SOCIAL — ESTRATÉGIA DE FETCH": confirmado num runner real
# para iefp_desemprego) — mais rápido e sem depender do Chromium.
_HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_http(fonte: dict) -> dict | None:
    url = fonte["url"]
    slug = fonte["slug"]
    nota = fonte.get("nota", "")
    log.info("A scrape (http): %s", url)

    config = _fonte_config(slug)
    classif = None
    resp = None

    for tentativa in range(1, TENTATIVAS_BLOQUEIO + 1):
        try:
            resp = requests.get(url, headers=_HEADERS_HTTP, timeout=30)
        except Exception as exc:
            log.warning("%s: erro de rede na tentativa %d/%d: %s", slug, tentativa, TENTATIVAS_BLOQUEIO, exc)
            classif = None
            if tentativa < TENTATIVAS_BLOQUEIO:
                time.sleep(random.uniform(ESPERA_MIN_S, ESPERA_MAX_S))
            continue

        classif = classificar_resposta(
            status_code=resp.status_code, corpo=resp.text, url_final=str(resp.url), config=config,
        )
        if classif.estado == Estado.OK:
            break

        log.warning("%s: tentativa %d/%d classificada como %s — motivos: %s",
                    slug, tentativa, TENTATIVAS_BLOQUEIO, classif.estado.value, classif.motivos)
        if tentativa < TENTATIVAS_BLOQUEIO:
            espera = random.uniform(ESPERA_MIN_S, ESPERA_MAX_S)
            log.info("%s: a aguardar %.0fs antes da próxima tentativa", slug, espera)
            time.sleep(espera)

    if classif is None:
        log.error("%s: falhou todas as %d tentativas por erro de rede", slug, TENTATIVAS_BLOQUEIO)
        return None

    if classif.estado != Estado.OK:
        return _tratar_nao_ok(slug, url, fonte["seletores"], nota, classif)

    _limpar_bloqueio_hoje(slug)
    conteudo = _extrair_conteudo(resp.text, fonte["seletores"])
    resultado = {
        "url": url,
        "url_original": url,
        "data_acesso": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "conteudo_extraido": conteudo,
    }
    if nota:
        resultado["nota"] = nota

    hash_payload = json.dumps(conteudo, sort_keys=True, ensure_ascii=False)
    resultado["hash_conteudo"] = hashlib.sha256(hash_payload.encode()).hexdigest()

    _guardar_resultado(slug, resultado)

    ano_detectar = fonte.get("detectar_ano")
    if ano_detectar and slug in MEGA_SLUGS_DATAS_RICAS:
        _detectar_datas_mega(slug, resp.text, conteudo, ano_detectar)
    elif ano_detectar and ano_detectar in resp.text:
        _registar_aviso(slug, f"ano_lectivo_detectado:{ano_detectar}")
        log.info("%s: ano lectivo %s detectado — pode haver novas datas", slug, ano_detectar)

    return resultado


# ── Main ───────────────────────────────────────────────────────────────────────

def _reportar_resultado(resultados: dict, slug: str, r: dict | None) -> None:
    if r:
        resultados[slug] = r.get("status", "ok")
        c = r.get("conteudo_extraido", {})
        if r.get("status") == "ok_via_arquivo":
            print(f"⚠ OK_VIA_ARQUIVO — snapshot de {r.get('data_snapshot')}")
        else:
            print(f"✓ OK — título: {c.get('titulo', '')[:80]}")
        print(f"  hash: {r.get('hash_conteudo', '')[:16]}…")
    else:
        resultados[slug] = "falhou"
        print("✗ Falhou")


def main(mode: str = "scrape"):
    from playwright.sync_api import sync_playwright

    resultados = {}

    fontes_http = [f for f in FONTES_PLAYWRIGHT if _fonte_config(f["slug"]).metodo == "http"]
    fontes_pw = [f for f in FONTES_PLAYWRIGHT if _fonte_config(f["slug"]).metodo != "http"]

    # ── HTTP simples (sem browser) ───────────────────────────────────────────
    for fonte in fontes_http:
        print(f"\n{'='*60}")
        print(f"[HTTP] {fonte['slug']} — {fonte['url']}")
        print("=" * 60)
        try:
            r = scrape_http(fonte)
            _reportar_resultado(resultados, fonte["slug"], r)
        except Exception as exc:
            resultados[fonte["slug"]] = f"erro: {exc}"
            log.exception("Erro inesperado em %s", fonte["slug"])
            print(f"✗ Erro: {exc}")

    # ── Playwright ────────────────────────────────────────────────────────────
    # Agrupadas por perfil de browser (_perfil_fonte) — por omissão todas
    # partilham o mesmo perfil de sempre (um único context, como antes
    # desta secção); só uma fonte com entrada em _PERFIL_POR_SLUG abre um
    # context à parte, com um perfil diferente.
    grupos: dict[PerfilBrowser, list[dict]] = {}
    for fonte in fontes_pw:
        perfil = _perfil_fonte(fonte["slug"])
        grupos.setdefault(perfil, []).append(fonte)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        for perfil, fontes_grupo in grupos.items():
            context = _criar_context(browser, perfil)
            page = context.new_page()

            for fonte in fontes_grupo:
                print(f"\n{'='*60}")
                print(f"[Playwright] {fonte['slug']} — {fonte['url']} (perfil={perfil})")
                print("=" * 60)
                try:
                    r = scrape_playwright(page, fonte)
                    _reportar_resultado(resultados, fonte["slug"], r)
                except Exception as exc:
                    resultados[fonte["slug"]] = f"erro: {exc}"
                    log.exception("Erro inesperado em %s", fonte["slug"])
                    print(f"✗ Erro: {exc}")

            page.close()
            context.close()

        browser.close()

    # ── DRE — estado manual ───────────────────────────────────────────────────
    dre_status = {
        "status": "manual",
        "nota": (
            "O DRE não tem feed público acessível nos runners GitHub Actions — "
            "verificação de nova legislação é feita manualmente em https://dre.pt "
            "quando o validador de conteúdo detecta mudanças nas fontes principais"
        ),
        "data": datetime.now(timezone.utc).date().isoformat(),
    }
    dre_status_path = SCRAPED_DIR / "dre_status.json"
    dre_status_path.write_text(json.dumps(dre_status, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n[DRE] Estado manual registado em dre_status.json")

    print(f"\n{'='*60}")
    print("RESUMO")
    print("=" * 60)
    icones = {"ok": "✓", "ok_via_arquivo": "⚠"}
    for slug, estado in resultados.items():
        icone = icones.get(estado, "✗")
        print(f"  {icone} {slug}: {estado}")

    ok = sum(1 for v in resultados.values() if v in ("ok", "ok_via_arquivo"))
    print(f"\n{ok}/{len(resultados)} fontes scraped com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="scrape", choices=["scrape", "detect"])
    args = parser.parse_args()
    main(args.mode)
