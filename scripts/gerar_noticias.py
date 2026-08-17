#!/usr/bin/env python3
"""Gera noticias.html a partir de feeds RSS — corre via GitHub Action diária.

`data/noticias.json` é a fonte de verdade (Fase 1, 2026-07-02): cada corrida
escolhe até `MAX_VENCEDORES_POR_DIA` vencedores (Fase 4, 2026-07-04 — no
máximo 1 por categoria, nunca 2 do mesmo tema no mesmo dia) entre os
candidatos com score positivo, dentro da janela de recência
(`JANELA_RECENCIA_DIAS`), que ainda não estejam no JSON (por URL ou por
título semelhante), acrescenta-os, e regenera noticias.html (destaque +
arquivo agrupado por mês, ordenado por data real desc) e o bloco
NOTICIA-HOME de index.html (2-3 mais recentes) a partir do JSON — nunca por
patch incremental do HTML anterior.

"Nenhuma notícia hoje" é um resultado aceitável — nunca forçar um candidato
fraco, duplicado ou antigo de mais só para ter alguma coisa a publicar; o
mesmo vale por categoria, sempre oportunista e nunca quota (ver
`selecionar_vencedores()`). Mesmo sem nenhum vencedor, `main()` chama
sempre `sincronizar_saidas()` no fim — nunca deixa noticias.html/index.html
atrasados face a data/noticias.json, mesmo que a alteração ao JSON tenha
vindo de outra via (ex.: migração manual).

Fase 2 do diagnóstico de 2026-07-04 (issue reportada pelo Nuno: notícia real
de abono de família não apanhada): os feeds passaram a ser um por TEMA do
site (`FEEDS`) em vez de pesquisas genéricas, e a selecção ganhou um corte
de recência (`JANELA_RECENCIA_DIAS`) — ver comentários junto a essas
constantes para o raciocínio completo. Fase 3: cada corrida regista a saúde
de cada feed (`data/feeds_saude_hoje.json`, consumido por
`gerir_estado_feeds.py`) e um log auditável de candidatos/decisões
(`data/noticias_candidatos.json`) — para que "nenhuma notícia hoje" seja
sempre distinguível de uma avaria, nunca um resultado silencioso.

    python scripts/gerar_noticias.py          # corrida normal (fetch + selecção + sync)
    python scripts/gerar_noticias.py --sync   # só resincroniza as saídas com o JSON actual, sem fetch

Escreve em index.html só dentro do bloco NOTICIA-HOME, entre marcadores —
nunca fora deles (ver SECCOES_PERMITIDAS e _verificar_escrita_confinada)."""

from __future__ import annotations

import difflib
import feedparser
import html
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RAIZ = Path(__file__).resolve().parent.parent
NOTICIAS_JSON = RAIZ / "data" / "noticias.json"
FEEDS_SAUDE_HOJE_JSON = RAIZ / "data" / "feeds_saude_hoje.json"
NOTICIAS_CANDIDATOS_JSON = RAIZ / "data" / "noticias_candidatos.json"

# Guardrail: ficheiros de escrita livre por este script (allow-list — um
# ficheiro que não conste aqui nem em SECCOES_PERMITIDAS é sempre bloqueado,
# nunca escrito "por omissão").
FICHEIROS_AUTO_GERADOS = [
    "noticias.html", "noticias.json",
    "feeds_saude_hoje.json", "noticias_candidatos.json",
]

# Guardrail: ficheiros HTML onde este script só pode escrever dentro de uma
# secção marcada — qualquer diferença fora dela bloqueia a escrita.
SECCOES_PERMITIDAS = {
    "index.html": ("NOTICIA-HOME:INICIO", "NOTICIA-HOME:FIM"),
}


def _verificar_escrita_confinada(caminho, conteudo_novo, marcador_inicio, marcador_fim):
    """Garante que `conteudo_novo` só difere do ficheiro em disco dentro da
    secção marcada — nunca fora dela. Levanta excepção caso contrário, ou
    se o marcador nem sequer existir no ficheiro em disco."""
    with open(caminho, encoding="utf-8") as f:
        atual = f.read()

    padrao = re.compile(
        rf"<!-- {re.escape(marcador_inicio)} -->[\s\S]*?<!-- {re.escape(marcador_fim)} -->"
    )
    if not padrao.search(atual):
        raise Exception(
            f"BLOQUEADO: marcador {marcador_inicio}/{marcador_fim} não encontrado "
            f"em {os.path.basename(caminho)} — escrita recusada."
        )

    atual_mascarado = padrao.sub("__SECCAO_PERMITIDA__", atual, count=1)
    novo_mascarado = padrao.sub("__SECCAO_PERMITIDA__", conteudo_novo, count=1)
    if atual_mascarado != novo_mascarado:
        raise Exception(
            f"BLOQUEADO: escrita em {os.path.basename(caminho)} fora da secção "
            f"permitida ({marcador_inicio}/{marcador_fim})."
        )


def escrever_ficheiro_seguro(caminho, conteudo):
    """Allow-list estrita: só `FICHEIROS_AUTO_GERADOS` (escrita livre) e
    `SECCOES_PERMITIDAS` (escrita confinada a um marcador) podem ser
    escritos por este script — qualquer outro nome é sempre bloqueado,
    nunca escrito por omissão."""
    nome = os.path.basename(caminho)

    if nome in FICHEIROS_AUTO_GERADOS:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return

    if nome in SECCOES_PERMITIDAS:
        marcador_inicio, marcador_fim = SECCOES_PERMITIDAS[nome]
        _verificar_escrita_confinada(caminho, conteudo, marcador_inicio, marcador_fim)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return

    raise Exception(
        f"BLOQUEADO: tentativa de escrever em ficheiro protegido: {nome}. "
        f"Apenas {FICHEIROS_AUTO_GERADOS + list(SECCOES_PERMITIDAS)} podem ser "
        f"modificados automaticamente."
    )


# Um feed de pesquisa Google News por TEMA do site, em vez de 3 pesquisas
# genéricas ("apoios sociais portugal" etc.) — diagnóstico de 2026-07-04
# (issue reportada pelo Nuno: notícia de abono de família de 2 jul nunca
# apanhada) confirmou que os feeds genéricos ficam dominados pelo tema mais
# "linkado" do momento (PSU) e enterram temas mais específicos a partir da
# posição ~78 — muito além do que qualquer pipeline realista examina. Cada
# feed por tema foi testado com fetch real num workflow_dispatch temporário
# antes de entrar aqui (nenhum feed sem essa confirmação).
#
# `dre.pt/rss/dr1s.rss` (e as 2 variantes testadas, `serie1s.rss` e
# `diariodarepublica.pt/dr/rss`) foram removidos — XML malformado
# (`not well-formed (invalid token)`) confirmado em 3 sessões de
# investigação diferentes, nunca contribuiu um único artigo. Candidatos a
# fonte oficial testados e também mortos: `seg-social.pt/rss` (entidade XML
# indefinida), `portugal.gov.pt/pt/gc25/comunicacao/rss` (404) — não existe
# hoje um substituto oficial vivo; ver CLAUDE.md secção "FRESCURA DA
# HOMEPAGE" para o registo completo.
#
# 6 feeds novos (2026-07-04, pedido do Nuno — cobrir categorias Fiscalidade
# e Habitação que ficavam a zero, mais IAS/calendário de pagamentos/salário
# mínimo/CSI): todos testados com fetch real num `workflow_dispatch`
# temporário antes de entrar aqui (mesma disciplina dos 7 feeds originais) —
# `irs_fiscalidade` (98 entradas, notícias reais de prazo de entrega),
# `ias_valor_referencia` (48, cobertura concentrada em torno da actualização
# anual de dez/jan — normal para um tema sazonal, não um sinal de feed
# fraco), `calendario_pagamentos_seg_social` (100, calendário mensal de
# pensões/prestações), `habitacao_arrendamento` (85, apoios ao arrendamento
# para além do Porta 65 — sobreposição ocasional com `porta65_arrendamento`
# é esperada e tratada pelo dedup existente, não pelo feed), `salario_minimo`
# (100) e `csi_idosos` (88). Nenhum tinha `bozo=True` nem 0 entradas.
FEEDS = {
    "abono_familia": "https://news.google.com/rss/search?q=abono+de+fam%C3%ADlia+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "subsidio_desemprego": "https://news.google.com/rss/search?q=subs%C3%ADdio+de+desemprego+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "rsi": "https://news.google.com/rss/search?q=RSI+rendimento+social+de+inser%C3%A7%C3%A3o+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "psu_pensoes": "https://news.google.com/rss/search?q=presta%C3%A7%C3%A3o+social+%C3%BAnica+pens%C3%B5es+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "acao_social_escolar": "https://news.google.com/rss/search?q=a%C3%A7%C3%A3o+social+escolar+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "cuidador_informal": "https://news.google.com/rss/search?q=cuidador+informal+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "porta65_arrendamento": "https://news.google.com/rss/search?q=Porta+65+arrendamento+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "irs_fiscalidade": "https://news.google.com/rss/search?q=IRS+declara%C3%A7%C3%A3o+de+rendimentos+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "ias_valor_referencia": "https://news.google.com/rss/search?q=IAS+indexante+apoios+sociais+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "calendario_pagamentos_seg_social": "https://news.google.com/rss/search?q=calend%C3%A1rio+pagamentos+seguran%C3%A7a+social+pens%C3%B5es+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "habitacao_arrendamento": "https://news.google.com/rss/search?q=apoio+arrendamento+habita%C3%A7%C3%A3o+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "salario_minimo": "https://news.google.com/rss/search?q=sal%C3%A1rio+m%C3%ADnimo+nacional+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "csi_idosos": "https://news.google.com/rss/search?q=complemento+solid%C3%A1rio+para+idosos+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
}

# Quantos itens de cada feed são examinados por corrida. Antes eram 10 — o
# diagnóstico mostrou que o factor decisivo foi a especificidade da query
# (o item de abono de 1 jul apareceu em 1.º lugar no feed dedicado), não
# este limite; sobe-se ligeiramente para 15 por margem de segurança, a
# custo desprezável (15 × 13 feeds = 195 entradas/corrida).
LIMITE_ENTRADAS_POR_FEED = 15

# Corte de recência: só candidatos publicados nos últimos N dias podem
# vencer — elimina o "banco" de artigos antigos (ex.: PSU de há 2 meses)
# que, por pontuarem alto em keywords, escondiam notícias mais recentes e
# mais específicas. N=7 porque: cobre uma semana inteira mesmo que o
# pipeline falhe uma corrida; todo o conteúdo genuinamente fresco
# encontrado no diagnóstico de 2026-07-04 estava dentro de 0-3 dias: uma
# janela de 7 dias é folgada sem ressuscitar o histórico antigo da PSU
# (que já teria mais de 3-4 semanas a essa data).
JANELA_RECENCIA_DIAS = 7

# "salário mínimo"/"retribuição mínima" e "complemento solidário"
# acrescentados 2026-07-04, ao ligar os feeds salario_minimo/csi_idosos:
# confirmado contra os títulos reais do diagnóstico que, sem estas frases,
# 5/5 manchetes reais de salário mínimo e 4/5 de CSI pontuavam 0 (nenhum
# outro termo desta lista aparece nelas) — nunca passariam do corte de
# score > 0, tornando os dois feeds inúteis para a selecção por muito que
# a categoria tivesse slot disponível. Frases completas (não palavras
# soltas) para não repetir o risco de ambiguidade já corrigido para "ias".
KEYWORDS = [
    "apoio", "apoios", "prestação", "prestações", "subsídio", "subsídios",
    "rsi", "abono", "desemprego", "pensão", "pensões", "ias", "rmg",
    "segurança social", "iefp", "irs", "at ", "finanças", "habitação",
    "renda", "arrendamento", "psu", "prestação social única",
    "salário mínimo", "retribuição mínima", "complemento solidário",
]

STOPWORDS = ["publicidade", "patrocinado", "sponsored", "advertisement"]

# Notícias sobre OUTROS PAÍSES — achado real (Nuno, screenshot de produção,
# 2026-08-17): 2 dos 84 itens já publicados em data/noticias.json eram sobre
# o desemprego/salário mínimo dos EUA e do Brasil, não de Portugal —
# "Pedidos de subsídio de desemprego nos EUA sobem para 209 mil..." (SÁBADO)
# e "Enquanto o salário mínimo no Brasil é de R$ 1.621, em Portugal o valor
# é extremamente maior" (Diário do Comércio, publicação brasileira). Os dois
# pontuavam > 0 pela keyword "desemprego"/"salário mínimo" sem qualquer
# verificação de que o artigo é sobre Portugal — `gl=PT`/`hl=pt-PT` no URL
# do feed só define a edição geográfica da pesquisa do Google News, nunca
# filtra o país do conteúdo devolvido; um artigo em português sobre outro
# país, publicado por um órgão de comunicação que o Google associa a
# Portugal (ou que só cita "Portugal" numa comparação, como o do Brasil),
# continua a bater com a query. Regra 1 de "REGRAS DE CONTEÚDO" do
# CLAUDE.md ("nunca PT-BR") e a própria razão de ser do site — notícias
# sobre APOIOS SOCIAIS PORTUGUESES — tornam isto sempre uma rejeição, nunca
# só uma penalização: mesmo tratamento de STOPWORDS (score = -1, hard
# reject, nunca chega ao corte de qualidade > 0). Regex, não substring
# simples, porque "eua" sozinho é curto de mais (mesmo risco já documentado
# para "ias") — sem risco conhecido para "brasil"/"r$" (nenhuma palavra
# portuguesa corrente contém "brasil" como substring não relacionada, e "R$"
# nunca aparece em texto PT-PT, que usa sempre "€"), mas mantidos na mesma
# regex por consistência. Lista deliberadamente pequena e sourced só dos 2
# casos reais encontrados — nunca especulativa (ex.: Espanha/Angola/
# Moçambique ficam de fora até haver um falso positivo real que os
# justifique, mesma disciplina de "nunca resolver por suspeita" já seguida
# no resto deste ficheiro).
_REGEX_PAIS_ESTRANGEIRO = re.compile(r"\beua\b|estados unidos|brasil|r\$")


def _e_noticia_de_pais_estrangeiro(texto: str) -> bool:
    return bool(_REGEX_PAIS_ESTRANGEIRO.search(texto))


# "ias" (IAS, o Indexante dos Apoios Sociais) é curta de mais para
# `kw in texto` simples — é substring de palavras portuguesas correntes
# sem relação nenhuma com o tema (a mais comum: "dias"; também
# "família"/"famílias") — descoberto ao adicionar o feed `ias_valor_referencia`
# (2026-07-04): um título real sobre IRS ("...arriscam multas... famílias...")
# ficava "apoios" em vez de "fiscal" só por conter "famílias". Exige
# fronteira de palavra só para esta keyword; as restantes mantêm o
# comportamento de substring simples (nenhuma outra é ambígua ao ponto de
# aparecer dentro de palavras comuns não relacionadas).
_REGEX_PALAVRA_IAS = re.compile(r"\bias\b")


def _contem_keyword(kw: str, texto: str) -> bool:
    if kw == "ias":
        return bool(_REGEX_PALAVRA_IAS.search(texto))
    return kw in texto

CAT_KEYWORDS = {
    "apoios": ["abono", "rsi", "prestação", "apoio social", "segurança social", "psu", "ias", "rmg", "pensão"],
    "educacao": ["escola", "ensino", "ase", "manuais", "bolsa", "universitário", "educação", "dge"],
    "emprego": ["desemprego", "iefp", "trabalho", "emprego", "contrato", "salário"],
    "habitacao": ["habitação", "renda", "arrendamento", "ihru", "casa", "imóvel"],
    "fiscal": ["irs", "at ", "finanças", "imposto", "fiscal", "declaração"],
    "legislacao": ["decreto-lei", "portaria", "lei n.º", "dre", "diário da república", "legislação"],
}

CAT_LABELS = {
    "apoios": "Apoios Sociais",
    "educacao": "Educação",
    "emprego": "Emprego",
    "habitacao": "Habitação",
    "fiscal": "Fiscalidade",
    "legislacao": "Legislação",
}

# Classificação best-effort para ligação futura ao guia do cluster
# (Fase 3 — "Relacionado: o nosso guia sobre X"). Não é garantidamente
# precisa; apenas a melhor correspondência por palavra-chave.
#
# "habitacao" estava em falta (gap encontrado 2026-07-04, ao ligar o feed
# `habitacao_arrendamento`) — o cluster existe em data/clusters.json desde
# 3 jul 2026 (p/habitacao.html) mas nunca tinha sido adicionado aqui.
CLUSTER_KEYWORDS = {
    "prestacao-social-unica": ["psu", "prestação social única"],
    "apoios-escolares": ["ase", "ação social escolar", "bolsa de mérito", "manuais escolares", "manuais gratuitos", "passe sub-23", "passe sub23"],
    "familia": ["abono de família", "abono", "licença parental", "subsídio parental"],
    "idosos-incapacidade-cuidadores": ["csi", "complemento solidário", "cuidador informal", "amim", "incapacidade multiuso"],
    "trabalho-rendimento": ["subsídio de desemprego", "desemprego", "iefp", "rsi", "rendimento social de inserção", "salário mínimo"],
    "habitacao": ["porta 65", "apoio ao arrendamento", "apoio à renda", "arrendamento", "ihru"],
    "como-pedir": ["chave móvel digital", "cartão de cidadão", "niss", "segurança social direta", "iban"],
}

MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
MESES_ABREV_PT = [
    "", "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]

LIMIAR_SEMELHANCA_TITULO = 0.90


@dataclass
class ItemNoticia:
    data_iso: str
    titulo: str
    fonte_nome: str
    url: str
    resumo: str
    categoria: str
    cluster_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "data_iso": self.data_iso,
            "titulo": self.titulo,
            "fonte_nome": self.fonte_nome,
            "url": self.url,
            "resumo": self.resumo,
            "categoria": self.categoria,
            "cluster_id": self.cluster_id,
        }

    @staticmethod
    def from_dict(d: dict) -> "ItemNoticia":
        return ItemNoticia(
            data_iso=d["data_iso"],
            titulo=d["titulo"],
            fonte_nome=d.get("fonte_nome", ""),
            url=d["url"],
            resumo=d.get("resumo", ""),
            categoria=d.get("categoria", "apoios"),
            cluster_id=d.get("cluster_id"),
        )


@dataclass
class Candidato:
    entry: dict
    score: int
    titulo: str
    url: str
    data_iso: str
    feed_url: str
    feed_nome: str = "?"
    categoria: str = "apoios"


@dataclass
class Rejeicao:
    titulo: str
    motivo: str


@dataclass
class SaudeFeed:
    nome: str
    url: str
    bozo: bool
    n_entradas: int

    @property
    def estado(self) -> str:
        return "OK" if (not self.bozo and self.n_entradas > 0) else "MORTO"

    @property
    def motivo(self) -> str:
        if self.bozo:
            return "erro_parsing_xml"
        if self.n_entradas == 0:
            return "sem_entradas"
        return ""


@dataclass
class ResultadoSelecao:
    """`vencedores`: até `MAX_VENCEDORES_POR_DIA` candidatos, no máximo 1 por
    categoria (Fase 4, 2026-07-04) — oportunista, nunca quota: uma categoria
    sem candidato válido (score positivo, dentro da janela, não duplicado)
    simplesmente não preenche o slot; nunca se baixa a fasquia de qualidade
    para forçar diversidade (decisão explícita do Nuno)."""
    candidatos_por_feed: Dict[str, int] = field(default_factory=dict)
    top_candidatos: List[Candidato] = field(default_factory=list)
    rejeitados: List[Rejeicao] = field(default_factory=list)
    vencedores: List[Candidato] = field(default_factory=list)


@dataclass
class DecisaoCandidato:
    """Um item por candidato dentro da janela de recência, para o log de
    auditoria completo (`data/noticias_candidatos.json`) — ao contrário de
    `ResultadoSelecao.rejeitados`, cobre TODOS os candidatos elegíveis por
    data, não só os avaliados até se encontrar um vencedor."""
    titulo: str
    feed_nome: str
    data_iso: str
    score: int
    decisao: str  # "vencedor" | "rejeitado_score" | "rejeitado_duplicado" | "nao_escolhido"
    motivo: str = ""


# ── Normalização e dedup ──────────────────────────────────────────────────

def normalizar_titulo(titulo: str) -> str:
    """minúsculas, sem pontuação, espaços colapsados — para comparar
    títulos vindos de fontes/formatações diferentes."""
    t = titulo.lower()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalizar_url(url: str) -> str:
    """Só remove espaços em volta e o fragmento (#...) — mantém a query
    string, porque em geral é significativa (só o link opaco do Google
    News é que repete o mesmo valor em dias diferentes, e nesse caso a
    comparação exacta já chega, confirmado no diagnóstico da Fase 0)."""
    return url.strip().split("#", 1)[0]


_REGEX_URL_GENERICA = re.compile(r"^https?://[^/]+/?$")


def _url_e_especifica(url: str) -> bool:
    """False para URLs que são só a homepage de um domínio (ex.: usadas
    em itens antigos manuscritos como 'fonte: seg-social.pt', sem
    apontar a um artigo concreto) — duas notícias diferentes podem
    legitimamente citar a mesma homepage como fonte, por isso um URL
    genérico nunca chega, sozinho, para as considerar duplicadas."""
    return not _REGEX_URL_GENERICA.match(url.strip())


def titulos_semelhantes(a: str, b: str) -> bool:
    if a == b:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= LIMIAR_SEMELHANCA_TITULO


def encontrar_duplicado(
    titulo: str, url: str, itens_existentes: List[ItemNoticia]
) -> Optional[ItemNoticia]:
    """Duplicado se o título (normalizado) for igual/semelhante — sinal
    sempre válido — ou se o URL canónico for exactamente igual E for um
    URL específico (não a homepage genérica de um domínio, partilhável
    por notícias diferentes sem serem a mesma)."""
    url_norm = normalizar_url(url)
    titulo_norm = normalizar_titulo(titulo)
    url_especifica = _url_e_especifica(url_norm)
    for item in itens_existentes:
        if titulos_semelhantes(titulo_norm, normalizar_titulo(item.titulo)):
            return item
        if url_especifica and normalizar_url(item.url) == url_norm:
            return item
    return None


# ── Scoring e classificação ────────────────────────────────────────────────

def score_entry(entry) -> int:
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    if any(s in text for s in STOPWORDS):
        return -1
    if _e_noticia_de_pais_estrangeiro(text):
        return -1
    return sum(1 for kw in KEYWORDS if _contem_keyword(kw, text))


def detect_category(entry) -> str:
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    for cat, kws in CAT_KEYWORDS.items():
        if any(_contem_keyword(kw, text) for kw in kws):
            return cat
    return "apoios"


def detectar_cluster(titulo: str, resumo: str) -> Optional[str]:
    text = (titulo + " " + resumo).lower()
    for cluster_id, kws in CLUSTER_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cluster_id
    return None


def fetch_entries() -> Tuple[List[dict], List[SaudeFeed]]:
    """Vai a cada feed uma única vez — devolve as entradas (para pontuação/
    selecção) e a saúde de cada feed (para `data/feeds_saude_hoje.json`,
    consumido por `gerir_estado_feeds.py`). Um feed com erro de parsing XML
    (`bozo`) ou 0 entradas está MORTO nesta corrida, independentemente de o
    HTTP ter respondido 200 — foi exactamente o caso do DRE (200 com XML
    malformado)."""
    entries = []
    saude = []
    for nome, url in FEEDS.items():
        feed = feedparser.parse(url)
        saude.append(SaudeFeed(nome=nome, url=url, bozo=bool(feed.bozo), n_entradas=len(feed.entries)))
        for e in feed.entries[:LIMITE_ENTRADAS_POR_FEED]:
            e["_feed_url"] = url
            e["_feed_nome"] = nome
            entries.append(e)
    return entries, saude


def parse_date(entry) -> datetime:
    try:
        dt = parsedate_to_datetime(entry.get("published", ""))
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def format_date_pt(dt: datetime) -> str:
    return f"{dt.day} {MESES_ABREV_PT[dt.month]}. {dt.year}"


def format_date_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def limpar_texto(texto: Optional[str]) -> str:
    """Limpa entidades HTML e espaços múltiplos do texto."""
    if not texto:
        return ""
    texto = texto.replace('\xa0', ' ')
    texto = texto.replace('&amp;nbsp;', ' ')
    texto = texto.replace('&nbsp;&nbsp;', ' ')
    texto = texto.replace('&nbsp;', ' ')
    texto = texto.replace('&#160;', ' ')
    texto = unescape(texto)
    texto = texto.replace('&nbsp;', ' ')
    texto = texto.replace('&#160;', ' ')
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


_REGEX_SEPARADOR_FONTE = re.compile(r"^(.*)\s+-\s+([^-]+)$")


def separar_titulo_e_fonte(titulo_bruto: str) -> Tuple[str, str]:
    """Os títulos do Google News vêm no formato 'Título - Fonte'. Separa
    os dois — evita mostrar a fonte duas vezes (uma no título, outra no
    campo dedicado) e permite comparar títulos sem ruído do agregador."""
    m = _REGEX_SEPARADOR_FONTE.match(titulo_bruto)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return titulo_bruto.strip(), ""


def construir_item_de_entry(entry: dict) -> ItemNoticia:
    titulo_bruto = limpar_texto(entry.get("title", "Sem título"))
    titulo, fonte_nome = separar_titulo_e_fonte(titulo_bruto)
    resumo = limpar_texto(entry.get("summary", ""))[:220]
    url = entry.get("link", "#")
    dt = parse_date(entry)
    categoria = detect_category(entry)
    cluster_id = detectar_cluster(titulo, resumo)
    return ItemNoticia(
        data_iso=format_date_iso(dt),
        titulo=titulo,
        fonte_nome=fonte_nome,
        url=url,
        resumo=resumo,
        categoria=categoria,
        cluster_id=cluster_id,
    )


# ── Selecção com dedup, corte de recência e observabilidade ───────────────

def _data_iso_para_date(data_iso: str):
    return datetime.strptime(data_iso, "%Y-%m-%d").date()


# Fase 4 (2026-07-04, pedido do Nuno): de "1 vencedor/dia" para "até
# MAX_VENCEDORES_POR_DIA/dia, no máximo 1 por categoria" — sem isto, um dia
# com candidatos válidos de Fiscalidade E de Habitação só publicava o que
# tivesse mais keywords de "apoios"/PSU (a maioria das KEYWORDS genéricas é
# desse tema), mesmo depois de existirem feeds dedicados para as outras
# categorias (ver diagnóstico real: 14/17 itens publicados eram "apoios",
# 0 "fiscal", 0 "habitacao", 0 "emprego"). Oportunista, nunca quota: uma
# categoria sem candidato com score positivo, dentro da janela e não
# duplicado simplesmente não preenche o slot — o corte de qualidade
# (score > 0, recência, dedup) aplica-se sempre antes da diversidade,
# nunca ao contrário.
MAX_VENCEDORES_POR_DIA = 3


def _construir_candidatos(entries: List[dict]) -> List[Candidato]:
    return [
        Candidato(
            entry=e,
            score=score_entry(e),
            titulo=limpar_texto(e.get("title", "Sem título")),
            url=e.get("link", "#"),
            data_iso=format_date_iso(parse_date(e)),
            feed_url=e.get("_feed_url", "?"),
            feed_nome=e.get("_feed_nome", e.get("_feed_url", "?")),
            categoria=detect_category(e),
        )
        for e in entries
    ]


def selecionar_vencedores(
    entries: List[dict],
    itens_existentes: List[ItemNoticia],
    *,
    hoje: Optional[datetime] = None,
    janela_recencia_dias: int = JANELA_RECENCIA_DIAS,
    max_vencedores: int = MAX_VENCEDORES_POR_DIA,
) -> ResultadoSelecao:
    """Escolhe até `max_vencedores` candidatos por corrida, no máximo 1 por
    categoria: score positivo, dentro da janela de recência, e não
    duplicado de um item já existente NEM de um vencedor já escolhido nesta
    mesma corrida (ex.: 2 feeds diferentes a apanhar a mesma notícia sob
    categorias diferentes). Candidatos antigos de mais são rejeitados
    mesmo com score alto — é o que impede um artigo de há 2 meses (ex.:
    PSU) de continuar a vencer todos os dias só por pontuar mais em
    keywords do que uma notícia genuína mas mais recente e mais específica
    (diagnóstico de 2026-07-04)."""
    resultado = ResultadoSelecao()
    hoje = hoje or datetime.now(timezone.utc)
    limite_recencia = (hoje - timedelta(days=janela_recencia_dias)).date()

    for e in entries:
        feed_nome = e.get("_feed_nome", e.get("_feed_url", "?"))
        resultado.candidatos_por_feed[feed_nome] = resultado.candidatos_por_feed.get(feed_nome, 0) + 1

    candidatos = _construir_candidatos(entries)
    candidatos.sort(key=lambda c: c.score, reverse=True)
    resultado.top_candidatos = candidatos[:3]

    vencedores_por_categoria: Dict[str, Candidato] = {}
    itens_escolhidos: List[ItemNoticia] = []

    for c in candidatos:
        if c.score <= 0:
            break  # candidatos já ordenados por score desc — nenhum a seguir serve
        if len(vencedores_por_categoria) >= max_vencedores:
            break  # slots do dia esgotados — resto irrelevante para a selecção
        if c.categoria in vencedores_por_categoria:
            continue  # categoria já tem vencedor hoje — próximo candidato
        if _data_iso_para_date(c.data_iso) < limite_recencia:
            resultado.rejeitados.append(
                Rejeicao(titulo=c.titulo, motivo=f"antigo (antes de {limite_recencia.isoformat()}, janela de {janela_recencia_dias} dias)")
            )
            continue
        duplicado = encontrar_duplicado(c.titulo, c.url, itens_existentes + itens_escolhidos)
        if duplicado is not None:
            resultado.rejeitados.append(
                Rejeicao(titulo=c.titulo, motivo=f"duplicado de {duplicado.data_iso}")
            )
            continue
        vencedores_por_categoria[c.categoria] = c
        itens_escolhidos.append(construir_item_de_entry(c.entry))

    resultado.vencedores = sorted(vencedores_por_categoria.values(), key=lambda c: c.score, reverse=True)
    return resultado


def analisar_candidatos_na_janela(
    entries: List[dict],
    itens_existentes: List[ItemNoticia],
    *,
    hoje: Optional[datetime] = None,
    janela_recencia_dias: int = JANELA_RECENCIA_DIAS,
    max_vencedores: int = MAX_VENCEDORES_POR_DIA,
) -> Tuple[List[DecisaoCandidato], Dict[str, int]]:
    """Classifica TODOS os candidatos dentro da janela de recência — não só
    os avaliados até `selecionar_vencedores()` esgotar os slots do dia —
    para que o log de auditoria (`data/noticias_candidatos.json`) responda
    sempre "o sistema viu a notícia X, e porque não venceu?". Os
    candidatos fora da janela só entram como contagem por feed (2.º valor
    devolvido) — o próprio título deles já não interessa para auditoria,
    visto que nunca poderiam vencer.

    Reimplementa (deliberadamente, não reutiliza) a mesma lógica de
    `selecionar_vencedores()` — aqui sem early-exit por score/categoria,
    porque o objectivo é classificar todos os itens, não só escolher os
    vencedores. "nao_escolhido" cobre as duas razões de não-selecção que
    não são score nem duplicado — categoria já preenchida hoje, ou slots
    do dia já esgotados — sem inventar mais rótulos: nenhum consumidor do
    log distingue as duas."""
    hoje = hoje or datetime.now(timezone.utc)
    limite_recencia = (hoje - timedelta(days=janela_recencia_dias)).date()

    candidatos = _construir_candidatos(entries)

    fora_da_janela_por_feed: Dict[str, int] = {}
    dentro_da_janela = []
    for c in candidatos:
        if _data_iso_para_date(c.data_iso) < limite_recencia:
            fora_da_janela_por_feed[c.feed_nome] = fora_da_janela_por_feed.get(c.feed_nome, 0) + 1
        else:
            dentro_da_janela.append(c)

    dentro_da_janela.sort(key=lambda c: c.score, reverse=True)

    decisoes: List[DecisaoCandidato] = []
    vencedores_por_categoria: Dict[str, Candidato] = {}
    itens_escolhidos: List[ItemNoticia] = []
    for c in dentro_da_janela:
        if c.score <= 0:
            decisoes.append(DecisaoCandidato(c.titulo, c.feed_nome, c.data_iso, c.score, "rejeitado_score", "score <= 0"))
            continue
        if len(vencedores_por_categoria) >= max_vencedores:
            decisoes.append(DecisaoCandidato(c.titulo, c.feed_nome, c.data_iso, c.score, "nao_escolhido", f"limite de {max_vencedores} vencedores/dia já atingido"))
            continue
        if c.categoria in vencedores_por_categoria:
            decisoes.append(DecisaoCandidato(c.titulo, c.feed_nome, c.data_iso, c.score, "nao_escolhido", f"categoria '{c.categoria}' já tem vencedor hoje"))
            continue
        duplicado = encontrar_duplicado(c.titulo, c.url, itens_existentes + itens_escolhidos)
        if duplicado is not None:
            decisoes.append(DecisaoCandidato(c.titulo, c.feed_nome, c.data_iso, c.score, "rejeitado_duplicado", f"duplicado de {duplicado.data_iso}"))
            continue
        decisoes.append(DecisaoCandidato(c.titulo, c.feed_nome, c.data_iso, c.score, "vencedor", f"score={c.score}, categoria={c.categoria}"))
        vencedores_por_categoria[c.categoria] = c
        itens_escolhidos.append(construir_item_de_entry(c.entry))

    return decisoes, fora_da_janela_por_feed


def imprimir_relatorio(resultado: ResultadoSelecao) -> None:
    print("=== Selecção de notícias ===")
    for feed_nome, n in resultado.candidatos_por_feed.items():
        print(f"  candidatos em {feed_nome}: {n}")
    print("  top 3 candidatos:")
    for c in resultado.top_candidatos:
        print(f"    score={c.score} [{c.data_iso}] | {c.titulo[:80]}")
    for r in resultado.rejeitados:
        print(f"  rejeitado: {r.titulo[:80]} — {r.motivo}")
    if resultado.vencedores:
        for v in resultado.vencedores:
            print(f"  vencedor [{v.categoria}]: {v.titulo[:80]} (score={v.score})")
    else:
        print("  vencedores: nenhum — sem candidato novo, recente e não-duplicado hoje")


# ── Persistência data/noticias.json ────────────────────────────────────────

def carregar_itens(caminho: Path = NOTICIAS_JSON) -> List[ItemNoticia]:
    if not caminho.exists():
        return []
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [ItemNoticia.from_dict(d) for d in dados.get("itens", [])]


def guardar_itens(itens: List[ItemNoticia], caminho: Path = NOTICIAS_JSON) -> None:
    itens_ordenados = ordenar_itens(itens)
    conteudo = json.dumps(
        {"itens": [i.to_dict() for i in itens_ordenados]},
        ensure_ascii=False, indent=2,
    ) + "\n"
    escrever_ficheiro_seguro(str(caminho), conteudo)


def ordenar_itens(itens: List[ItemNoticia]) -> List[ItemNoticia]:
    """Data desc; título como desempate — determinístico, nunca aleatório."""
    return sorted(itens, key=lambda i: (i.data_iso, i.titulo), reverse=True)


def agrupar_por_mes(itens: List[ItemNoticia]) -> List[Tuple[str, List[ItemNoticia]]]:
    """Itens já ordenados por data desc — agrupa mantendo essa ordem."""
    grupos: List[Tuple[str, List[ItemNoticia]]] = []
    for item in itens:
        ano, mes, _ = item.data_iso.split("-")
        chave = f"{ano}-{mes}"
        if grupos and grupos[-1][0] == chave:
            grupos[-1][1].append(item)
        else:
            grupos.append((chave, [item]))
    return grupos


def label_mes(chave: str) -> str:
    ano, mes = chave.split("-")
    return f"{MESES_PT[int(mes)].capitalize()} {ano}"


# ── Renderização HTML a partir do JSON ─────────────────────────────────────

def render_destaque(item: ItemNoticia) -> str:
    cat_label = CAT_LABELS.get(item.categoria, "Apoios Sociais")
    data_str = _iso_para_pt(item.data_iso)
    titulo_completo = f"{item.titulo} - {item.fonte_nome}" if item.fonte_nome else item.titulo
    return f"""<!-- DESTAQUE-INICIO -->
          <article class="destaque-card" data-cat="{item.categoria}">
            <div class="destaque-meta">
              <span class="cat-badge cat-{item.categoria}"><span class="cat-dot"></span><span class="cat-label">{cat_label}</span></span>
              <time datetime="{item.data_iso}">{data_str}</time>
            </div>
            <h2 class="destaque-titulo">{html.escape(titulo_completo)}</h2>
            <p class="destaque-resumo">{html.escape(item.resumo)}…</p>
            <a href="{html.escape(item.url)}" class="destaque-link" target="_blank" rel="noopener noreferrer">Ler notícia completa →</a>
            <p class="disclaimer-noticia">Resumo informativo. Lê a notícia completa na fonte antes de tomar decisões.</p>
          </article>
        <!-- DESTAQUE-FIM -->"""


def render_arquivo_card(item: ItemNoticia) -> str:
    cat_label = CAT_LABELS.get(item.categoria, "Apoios Sociais")
    data_str = _iso_para_pt(item.data_iso)
    titulo_completo = f"{item.titulo} - {item.fonte_nome}" if item.fonte_nome else item.titulo
    ano, mes, _ = item.data_iso.split("-")
    return f"""          <article class="arquivo-card" data-cat="{item.categoria}" data-mes="{ano}-{mes}">
            <div class="arquivo-meta">
              <span class="cat-badge cat-{item.categoria}"><span class="cat-dot"></span><span class="cat-label">{cat_label}</span></span>
              <time datetime="{item.data_iso}">{data_str}</time>
            </div>
            <h3 class="arquivo-titulo">{html.escape(titulo_completo)}</h3>
            <p class="arquivo-resumo">{html.escape(item.resumo)}…</p>
            <a href="{html.escape(item.url)}" class="arquivo-link" target="_blank" rel="noopener noreferrer">Ler →</a>
          </article>"""


def _iso_para_pt(data_iso: str) -> str:
    dt = datetime.strptime(data_iso, "%Y-%m-%d")
    return f"{dt.day} {MESES_ABREV_PT[dt.month]}. {dt.year}"


def render_arquivo(itens: List[ItemNoticia]) -> str:
    """Todos os itens excepto o mais recente (esse vai para o destaque),
    ordenados por data desc e agrupados por mês com um cabeçalho por
    grupo (marcador data-mes já presente em cada card — os cabeçalhos
    aqui são só a versão estática/sem-JS; ver assets de noticias.html
    para a versão dinâmica usada durante a paginação)."""
    if not itens:
        return ""
    resto = itens[1:]
    blocos = []
    for chave, grupo in agrupar_por_mes(resto):
        blocos.append(f'          <h3 class="mes-header" data-mes="{chave}">{label_mes(chave)}</h3>')
        blocos.extend(render_arquivo_card(i) for i in grupo)
    return "\n".join(blocos)


def render_noticia_home(itens: List[ItemNoticia], limite: int = 3) -> str:
    """Bloco NOTICIA-HOME do index.html — os `limite` itens mais recentes,
    cada um com a sua data real (nunca "hoje") e link directo à fonte
    externa (nunca um link interno inventado)."""
    cartoes = []
    for item in itens[:limite]:
        data_str = _iso_para_pt(item.data_iso)
        titulo_completo = f"{item.titulo} - {item.fonte_nome}" if item.fonte_nome else item.titulo
        cartoes.append(
            '    <div class="noticia-card">\n'
            f'      <span class="badge-hoje">{data_str}</span>\n'
            f'      <h3>{html.escape(titulo_completo)}</h3>\n'
            f'      <p>{html.escape(item.resumo)}…</p>\n'
            f'      <a href="{html.escape(item.url)}" class="link-ler" target="_blank" rel="noopener noreferrer">Ler notícia completa →</a>\n'
            '    </div>'
        )
    return "\n".join(cartoes)


def regenerar_noticias_html(itens: List[ItemNoticia], caminho: Path = RAIZ / "noticias.html") -> bool:
    """Substitui só os blocos DESTAQUE e ARQUIVO — nunca a nav, o hero, os
    filtros ou o rodapé, que ficam fora do alcance deste script. Devolve
    True se o conteúdo mudou."""
    itens_ordenados = ordenar_itens(itens)
    conteudo = caminho.read_text(encoding="utf-8")
    original = conteudo

    if itens_ordenados:
        novo_destaque = render_destaque(itens_ordenados[0])
        conteudo = re.sub(
            r"<!-- DESTAQUE-INICIO -->[\s\S]*?<!-- DESTAQUE-FIM -->",
            lambda m: novo_destaque,
            conteudo,
        )

    novo_arquivo = render_arquivo(itens_ordenados)
    conteudo = re.sub(
        r"(<!-- ARQUIVO-INICIO -->)[\s\S]*?(<!-- ARQUIVO-FIM -->)",
        lambda m: f"{m.group(1)}\n{novo_arquivo}\n        {m.group(2)}",
        conteudo,
    )

    if conteudo == original:
        return False
    escrever_ficheiro_seguro(str(caminho), conteudo)
    return True


def atualizar_index_home(itens: List[ItemNoticia], caminho: str = "index.html", limite: int = 3) -> bool:
    """Injecta os `limite` itens mais recentes no bloco NOTICIA-HOME do
    index.html — segunda fonte de frescura da homepage, junto de
    'Atualizado recentemente' (gerado por sincronizar_clusters.py)."""
    marcador_inicio, marcador_fim = SECCOES_PERMITIDAS["index.html"]
    padrao = re.compile(
        rf"<!-- {re.escape(marcador_inicio)} -->[\s\S]*?<!-- {re.escape(marcador_fim)} -->"
    )

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    if not padrao.search(conteudo):
        print(f"AVISO: marcadores {marcador_inicio}/{marcador_fim} não encontrados em {caminho} — sem injecção")
        return False

    itens_ordenados = ordenar_itens(itens)
    novo_bloco = f"<!-- {marcador_inicio} -->\n{render_noticia_home(itens_ordenados, limite)}\n    <!-- {marcador_fim} -->"
    novo_conteudo = padrao.sub(lambda m: novo_bloco, conteudo, count=1)

    if novo_conteudo == conteudo:
        print(f"{caminho}: notícia já actualizada — sem alterações")
        return False

    escrever_ficheiro_seguro(caminho, novo_conteudo)
    print(f"{caminho}: bloco de notícias actualizado ({min(limite, len(itens_ordenados))} itens)")
    return True


def sincronizar_saidas(
    itens: Optional[List[ItemNoticia]] = None,
    noticias_caminho: Path = RAIZ / "noticias.html",
    index_caminho: str = "index.html",
) -> None:
    """Regenera noticias.html e o bloco NOTICIA-HOME de index.html a
    partir de data/noticias.json — idempotente (sem alterações se já
    estiverem em sincronia) e independente de qualquer corrida de RSS.

    Único ponto de saída partilhado por `main()` (corrida diária) e por
    `scripts/migrar_noticias.py` (migração única) — nunca duplicar esta
    lógica noutro sítio. Utilizável também como passo manual isolado:
    `python scripts/gerar_noticias.py --sync`."""
    if itens is None:
        itens = carregar_itens(NOTICIAS_JSON)
    itens_ordenados = ordenar_itens(itens)
    regenerar_noticias_html(itens_ordenados, caminho=noticias_caminho)
    atualizar_index_home(itens_ordenados, caminho=index_caminho)


# ── Observabilidade permanente (Fase 3, 2026-07-04) ───────────────────────

def registar_saude_feeds_hoje(
    saude: List[SaudeFeed], *, caminho: Path = FEEDS_SAUDE_HOJE_JSON, hoje: Optional[str] = None
) -> None:
    """Snapshot da saúde de cada feed HOJE — espelha `data/bloqueios.json`
    do scraper. Consumido por `gerir_estado_feeds.py` (máquina de estados,
    Issue `feed-morto` ao 3.º dia consecutivo) — este ficheiro nunca decide
    nada sozinho, só regista o facto bruto desta corrida."""
    hoje = hoje or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dados = [
        {"nome": s.nome, "url": s.url, "estado": s.estado, "motivo": s.motivo, "n_entradas": s.n_entradas, "data": hoje}
        for s in saude
    ]
    escrever_ficheiro_seguro(str(caminho), json.dumps(dados, ensure_ascii=False, indent=2) + "\n")


HISTORICO_DIAS_CANDIDATOS = 14


def registar_candidatos_log(
    entries: List[dict],
    itens_existentes: List[ItemNoticia],
    saude: List[SaudeFeed],
    *,
    caminho: Path = NOTICIAS_CANDIDATOS_JSON,
    hoje: Optional[datetime] = None,
    janela_recencia_dias: int = JANELA_RECENCIA_DIAS,
    historico_dias: int = HISTORICO_DIAS_CANDIDATOS,
) -> None:
    """Acrescenta um registo de auditoria completo por corrida: TODOS os
    candidatos dentro da janela de recência (título, feed, data, score,
    decisão/motivo — via `analisar_candidatos_na_janela()`), contagem por
    feed dos que ficaram fora da janela, saúde dos feeds e os vencedores
    (lista, possivelmente vazia — Fase 4, 2026-07-04: até
    `MAX_VENCEDORES_POR_DIA`, no máximo 1 por categoria). "Nenhuma notícia
    hoje" tem sempre resposta a "o sistema viu a notícia X?" — nunca um
    resultado silencioso, indistinguível de uma avaria. Histórico limitado
    aos últimos `historico_dias` dias (não corridas — 2 corridas no mesmo
    dia, ex.: `workflow_dispatch` manual, não expulsam entradas mais
    antigas fora de tempo) para não crescer sem limite.

    Nota de schema: entradas do histórico anteriores a esta fase têm
    `"vencedor"` (singular, dict ou null) em vez de `"vencedores"` (lista)
    — inofensivo, nada lê de volta o conteúdo de entradas antigas do
    histórico, só a chave `"data"` para a retenção."""
    hoje = hoje or datetime.now(timezone.utc)
    hoje_str = hoje.strftime("%Y-%m-%d")

    candidatos_por_feed: Dict[str, int] = {}
    for e in entries:
        nome = e.get("_feed_nome", e.get("_feed_url", "?"))
        candidatos_por_feed[nome] = candidatos_por_feed.get(nome, 0) + 1

    decisoes, fora_da_janela_por_feed = analisar_candidatos_na_janela(
        entries, itens_existentes, hoje=hoje, janela_recencia_dias=janela_recencia_dias
    )
    vencedores = [d for d in decisoes if d.decisao == "vencedor"]

    historico = []
    if caminho.exists():
        try:
            historico = json.loads(caminho.read_text(encoding="utf-8"))
        except Exception:
            historico = []

    registo = {
        "data": hoje_str,
        "saude_feeds": {s.nome: s.estado for s in saude},
        "candidatos_por_feed": candidatos_por_feed,
        "fora_da_janela_por_feed": fora_da_janela_por_feed,
        "candidatos": [
            {"titulo": d.titulo, "feed_nome": d.feed_nome, "data_iso": d.data_iso, "score": d.score, "decisao": d.decisao, "motivo": d.motivo}
            for d in decisoes
        ],
        "vencedores": [
            {"titulo": v.titulo, "feed_nome": v.feed_nome, "score": v.score}
            for v in vencedores
        ],
    }
    historico.append(registo)

    limite_data = (hoje - timedelta(days=historico_dias)).strftime("%Y-%m-%d")
    historico = [r for r in historico if isinstance(r, dict) and r.get("data", "") >= limite_data]

    escrever_ficheiro_seguro(str(caminho), json.dumps(historico, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    if "--sync" in sys.argv:
        sincronizar_saidas()
        return

    itens_existentes = carregar_itens()
    entries, saude = fetch_entries()
    resultado = selecionar_vencedores(entries, itens_existentes)
    imprimir_relatorio(resultado)

    registar_saude_feeds_hoje(saude)
    registar_candidatos_log(entries, itens_existentes, saude)

    if not resultado.vencedores:
        print("Nenhuma notícia relevante encontrada hoje.")
    else:
        novos_itens = [construir_item_de_entry(v.entry) for v in resultado.vencedores]
        itens_existentes = itens_existentes + novos_itens
        guardar_itens(itens_existentes)
        for item in novos_itens:
            print(f"Notícia publicada [{item.categoria}]: {item.titulo[:80]}")

    # Sincroniza sempre as saídas com o estado actual do JSON — mesmo
    # sem vencedores novos hoje, garante que noticias.html/index.html nunca
    # ficam atrás de uma alteração feita por outra via (ex.: migração,
    # edição manual). Idempotente: sem alterações se já estiver tudo
    # sincronizado.
    sincronizar_saidas(itens_existentes)


if __name__ == "__main__":
    main()
