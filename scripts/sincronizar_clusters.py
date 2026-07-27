#!/usr/bin/env python3
"""
scripts/sincronizar_clusters.py

`data/clusters.json` é a fonte única de verdade da arquitectura de
clusters do site. Este script lê-o e injecta, entre marcadores
próprios, o HTML estático correspondente (sem JS em runtime — SEO
preservado):

    <!-- CLUSTERS:HOME:INICIO/FIM -->     cartões de clusters na homepage
    <!-- DESTAQUES:HOME:INICIO/FIM -->    um cartão por cluster em destaque, na homepage
    <!-- ATUALIZACOES:HOME:INICIO/FIM --> 3-4 artigos mais recentemente
                                          verificados, por "Verificado a"
                                          real de cada página, na homepage
    <!-- CLUSTER-BADGE:INICIO/FIM -->     breadcrumb visível + "este artigo
                                          pertence ao guia X", num artigo
    <!-- RELACIONADOS:INICIO/FIM -->      secção final de artigos
                                          relacionados, num artigo
    <!-- PILLAR-LISTA:INICIO/FIM -->      lista de artigos do cluster,
                                          numa pillar page
    <!-- PILLAR-JSONLD:INICIO/FIM -->     JSON-LD CollectionPage + ItemList
                                          da pillar page (no <head>)

Idempotente: correr duas vezes seguidas produz ficheiros byte a byte
idênticos. Nunca escreve fora dos marcadores; se uma página deveria ter
um marcador (por estar referenciada em `clusters.json`) e ele não
existir, a página é reportada e não é tocada.

CLUSTER-BADGE e RELACIONADOS só se aplicam a páginas `tipo: "artigo"`.
As ferramentas (simuladores) são membros do cluster mas usam um hero
claro incompatível com o texto branco do clusters.css — ficam de fora
da navegação contextual (decisão documentada no CLAUDE.md).

    python scripts/sincronizar_clusters.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional, Tuple

RAIZ = Path(__file__).resolve().parent.parent
CLUSTERS_JSON = RAIZ / "data" / "clusters.json"
DOMINIO = "https://tensdireito.com"

# Páginas fora do sistema de clusters — nunca tocadas por este script.
EXCLUIDAS = {
    "index.html", "noticias.html", "comecar-aqui.html",
    "sobre.html", "fontes.html", "privacidade.html", "404.html",
    "acessibilidade.html",
    # Hub cross-cluster dos simuladores — agrega ferramentas de 3 clusters
    # diferentes (familia, apoios-escolares, idosos-incapacidade-cuidadores),
    # não pertence a nenhum cluster único. Mesma categoria de comecar-aqui.html.
    "simuladores.html",
    # Ferramenta pronta mas deliberadamente não publicada — aguarda o
    # decreto-lei da PSU (ver PARAMETROS_PSU no próprio ficheiro e
    # CLAUDE.md "IMPACTO DA PSU"). Fica fora de clusters.json até ao dia
    # do decreto (ver .claude/commands/atualizar-cluster-psu.md).
    "simulador-psu.html",
    # Hub cross-cluster do Gerador de Documentos — mesma categoria de
    # simuladores.html (agrega minutas de vários temas, não pertence a
    # um único cluster).
    "documentos.html",
    # As 3 minutas vivem em documentos/ — fora do sistema de clusters
    # por desenho: cluster_da_pagina()/processar_pagina() comparam
    # p.slug só contra caminho.name (basename), pensado para páginas na
    # raiz; estender isso a caminhos com subdirectório é um refactor à
    # parte, fora do âmbito desta sessão (ver ROADMAP.md). A reclamação
    # é também genérica a qualquer prestação, sem cluster único óbvio —
    # mesma razão de comecar-aqui.html. Integração feita por fora do
    # sistema de clusters: nav, sitemap, pesquisa.js, hub /documentos.html
    # e cross-links manuais a partir de abono-de-familia.html e
    # complemento-solidario-idosos.html.
    "reclamacao-decisao-seguranca-social.html",
    "carta-acompanhamento-csi.html",
    "carta-acompanhamento-reavaliacao-abono.html",
    # Sessão 2 do Gerador de Documentos (2026-07-06) — candidatas 4-12
    # verificadas e publicadas, mesma categoria/razão das 3 anteriores.
    "recurso-hierarquico-seguranca-social.html",
    "exposicao-atraso-processamento.html",
    "carta-acompanhamento-divida-prestacoes.html",
    "carta-acompanhamento-svi-recurso.html",
    "carta-acompanhamento-comunicacao-alteracao.html",
    "requerimento-reavaliacao-escalao-ase.html",
    "pedido-acesso-documentos-administrativos.html",
    "requerimento-generico-seguranca-social.html",
    "pedido-declaracao-comprovativo-prestacoes.html",
    # Calendário de pagamentos — página utilitária cross-cluster (as
    # datas cobrem pensões, abono, desemprego, RSI, CSI, PSI, cuidador
    # informal…), mesma categoria de simuladores.html/comecar-aqui.html.
    # Corpo gerado por scripts/atualizar_calendario.py entre marcadores
    # CAL:META/CAL:CORPO (ver docs/FONTE-CALENDARIO.md).
    "calendario-pagamentos-seguranca-social.html",
    # Pedido deferido: quando cai o primeiro pagamento — página utilitária
    # cross-cluster (cobre desemprego, abono, RSI, pensão, CSI…, um por
    # cluster diferente), mesma categoria de comecar-aqui.html/calendário.
    "pagamento-apos-deferimento.html",
    # Dados Abertos (FASE 3 da sessão de dados abertos, 2026-07-19) —
    # página institucional/dataset (parâmetros legais + historial de
    # observações), não pertence a nenhum cluster único, mesma categoria
    # de acessibilidade.html/sobre.html.
    "dados.html",
    # Verificador de Apoios (2026-07-27) — ferramenta cross-cluster que
    # aponta para apoios de vários clusters diferentes (abono/família,
    # apoios-escolares), mesma categoria de simuladores.html/
    # comecar-aqui.html. Só calcula o abono (via assets/js/calc-apoios.js,
    # partilhado com simulador-abono.html); os restantes apoios são
    # ponteiros condicionais, sem cluster único a atribuir.
    "verificador-apoios.html",
}

MARCADOR_HOME = ("CLUSTERS:HOME:INICIO", "CLUSTERS:HOME:FIM")
MARCADOR_DESTAQUES = ("DESTAQUES:HOME:INICIO", "DESTAQUES:HOME:FIM")
MARCADOR_ATUALIZACOES = ("ATUALIZACOES:HOME:INICIO", "ATUALIZACOES:HOME:FIM")
MARCADOR_BADGE = ("CLUSTER-BADGE:INICIO", "CLUSTER-BADGE:FIM")
MARCADOR_RELACIONADOS = ("RELACIONADOS:INICIO", "RELACIONADOS:FIM")
MARCADOR_PILLAR_LISTA = ("PILLAR-LISTA:INICIO", "PILLAR-LISTA:FIM")
MARCADOR_PILLAR_JSONLD = ("PILLAR-JSONLD:INICIO", "PILLAR-JSONLD:FIM")

MAX_RELACIONADOS = 4
MAX_ATUALIZACOES = 4

MESES_PT = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}
MESES_ABREV_PT = [
    "", "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]

# Os artigos publicados usam 3 formatos para "Verificado a ...": DD/MM/AAAA,
# "D de mês de AAAA" e "D mês AAAA" (sem "de" a separar dia e mês).
_REGEX_VERIFICADO = re.compile(
    r"Verificado a\s+(?:"
    r"(?P<d1>\d{1,2})/(?P<m1>\d{1,2})/(?P<y1>\d{4})"
    r"|(?P<d2>\d{1,2})\s+de\s+(?P<mes2>" + "|".join(MESES_PT) + r")\s+de\s+(?P<y2>\d{4})"
    r"|(?P<d3>\d{1,2})\s+(?P<mes3>" + "|".join(MESES_PT) + r")\s+(?P<y3>\d{4})"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Pagina:
    slug: str
    titulo: str
    tipo: str
    destaque: bool
    emoji: str = ""
    desc: str = ""


@dataclass(frozen=True)
class Cluster:
    id: str
    nome: str
    descricao_curta: str
    icone: str
    pillar: str
    paginas: List[Pagina]
    relacionados: List[str]
    # Clusters utilitários (ex.: "Como Pedir") não são um "apoio" — ficam
    # de fora do dropdown "Apoios" da nav e dos cartões de "Guias de
    # Apoios"/"Guias principais" da homepage, mas continuam com pillar,
    # PILLAR-LISTA, PILLAR-JSONLD, CLUSTER-BADGE e RELACIONADOS normais.
    oculta_em_apoios: bool = False


@dataclass(frozen=True)
class Resultado:
    ficheiro: str
    alterado: bool
    motivo: str


def carregar_clusters(caminho: Path = CLUSTERS_JSON) -> List[Cluster]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    clusters = []
    for c in dados["clusters"]:
        paginas = [Pagina(**p) for p in c["paginas"]]
        clusters.append(Cluster(
            id=c["id"], nome=c["nome"], descricao_curta=c["descricao_curta"],
            icone=c["icone"], pillar=c["pillar"], paginas=paginas,
            relacionados=list(c.get("relacionados", [])),
            oculta_em_apoios=bool(c.get("oculta_em_apoios", False)),
        ))
    return clusters


def cluster_da_pagina(clusters: List[Cluster], nome_ficheiro: str) -> Optional[Cluster]:
    for c in clusters:
        if any(p.slug == nome_ficheiro for p in c.paginas):
            return c
    return None


def cluster_do_pillar(clusters: List[Cluster], caminho_relativo: str) -> Optional[Cluster]:
    alvo = "/" + caminho_relativo
    for c in clusters:
        if c.pillar == alvo:
            return c
    return None


def _substituir_bloco(conteudo: str, marca: Tuple[str, str], novo_interior: str) -> Optional[str]:
    """Substitui o interior entre os marcadores `marca` por `novo_interior`.
    Devolve None se o par de marcadores não existir no conteúdo."""
    inicio, fim = marca
    padrao = re.compile(
        rf"(<!-- {re.escape(inicio)} -->)([\s\S]*?)(<!-- {re.escape(fim)} -->)"
    )
    if not padrao.search(conteudo):
        return None
    return padrao.sub(
        lambda m: f"{m.group(1)}\n{novo_interior}\n  {m.group(3)}",
        conteudo,
    )


def contagem_str(cluster: Cluster) -> str:
    """'4 guias · 1 simulador' — conta por tipo para não contradizer
    descrições que falam de um número fixo de guias (ex.: "os quatro
    apoios escolares" quando o cluster também tem um simulador)."""
    guias = sum(1 for p in cluster.paginas if p.tipo == "artigo")
    ferramentas = sum(1 for p in cluster.paginas if p.tipo == "ferramenta")
    partes = []
    if guias:
        partes.append(f"{guias} guia" + ("" if guias == 1 else "s"))
    if ferramentas:
        partes.append(f"{ferramentas} simulador" + ("" if ferramentas == 1 else "es"))
    return " · ".join(partes) if partes else "0 guias"


def render_home_cards(clusters: List[Cluster]) -> str:
    cartoes = []
    for c in clusters:
        if c.oculta_em_apoios:
            continue
        contagem = contagem_str(c)
        cartoes.append(
            f'      <a href="{c.pillar}" class="apoio-card">\n'
            f'        <div class="emoji">{c.icone}</div>\n'
            f'        <h3>{c.nome}</h3>\n'
            f'        <p class="desc">{c.descricao_curta}</p>\n'
            f'        <span class="tag-verif">{contagem}</span>\n'
            f'        <span class="link-ver">→ Ver guias</span>\n'
            f'      </a>'
        )
    return "\n".join(cartoes)


def render_destaques_home(clusters: List[Cluster]) -> str:
    """Um cartão por cluster (o(s) `destaque: true` do JSON) — substitui
    a antiga grelha de 14 cartões hardcoded; ver secção "Guias principais"
    do plano de reorganização."""
    cartoes = []
    for c in clusters:
        if c.oculta_em_apoios:
            continue
        for p in c.paginas:
            if not p.destaque:
                continue
            cartoes.append(
                f'      <a href="/{p.slug}" class="apoio-card">\n'
                f'        <div class="emoji">{p.emoji}</div>\n'
                f'        <h3>{p.titulo}</h3>\n'
                f'        <p class="desc">{p.desc}</p>\n'
                f'        <span class="link-ver">→ Ver guia</span>\n'
                f'      </a>'
            )
    return "\n".join(cartoes)


def extrair_verificado_em(caminho: Path) -> Optional[date]:
    """Data da última ocorrência de 'Verificado a ...' no ficheiro — é a
    que fica mais perto do bloco de fontes no fim do corpo, a canónica
    da página (as ocorrências anteriores são notas por secção). Devolve
    None se o ficheiro não existir ou não tiver nenhuma data válida —
    nunca inventa nem assume "hoje"."""
    if not caminho.exists():
        return None
    conteudo = caminho.read_text(encoding="utf-8")
    matches = list(_REGEX_VERIFICADO.finditer(conteudo))
    if not matches:
        return None
    g = matches[-1].groupdict()
    try:
        if g["d1"]:
            dia, mes, ano = int(g["d1"]), int(g["m1"]), int(g["y1"])
        elif g["d2"]:
            dia, mes, ano = int(g["d2"]), MESES_PT[g["mes2"].lower()], int(g["y2"])
        else:
            dia, mes, ano = int(g["d3"]), MESES_PT[g["mes3"].lower()], int(g["y3"])
        return date(ano, mes, dia)
    except ValueError:
        return None


def render_atualizacoes_home(clusters: List[Cluster], raiz: Path = RAIZ, limite: int = MAX_ATUALIZACOES) -> str:
    """3-4 artigos mais recentemente verificados, por data real extraída
    do corpo de cada página (nunca do RSS, nunca inventada) — reflecte
    edições reais do site. Ordem determinística: data desc, slug asc
    como desempate (nunca aleatório, para a saída ser idempotente)."""
    candidatos: List[Tuple[date, Pagina]] = []
    for c in clusters:
        for p in c.paginas:
            if p.tipo != "artigo":
                continue
            data_verificacao = extrair_verificado_em(raiz / p.slug)
            if data_verificacao is not None:
                candidatos.append((data_verificacao, p))

    candidatos.sort(key=lambda par: (-par[0].toordinal(), par[1].slug))
    escolhidos = candidatos[:limite]

    cartoes = []
    for data_verificacao, p in escolhidos:
        data_str = f"{data_verificacao.day} {MESES_ABREV_PT[data_verificacao.month]}. {data_verificacao.year}"
        cartoes.append(
            f'      <a href="/{p.slug}" class="apoio-card">\n'
            f'        <div class="emoji">🕓</div>\n'
            f'        <h3>{p.titulo}</h3>\n'
            f'        <p class="desc">Verificado a {data_str}.</p>\n'
            f'        <span class="link-ver">→ Ler guia</span>\n'
            f'      </a>'
        )
    return "\n".join(cartoes)


def render_pillar_lista(cluster: Cluster) -> str:
    """Itens de <li> — a página envolve o marcador no seu próprio <ul>
    (ver p/apoios-escolares.html, prestacao-social-unica.html).
    Ferramentas ganham um badge discreto (classe .badge, já existente em
    todas as pillar pages) para se distinguirem dos guias na mesma lista."""
    itens = []
    for p in cluster.paginas:
        badge = ' <span class="badge">Ferramenta</span>' if p.tipo == "ferramenta" else ""
        itens.append(f'      <li><a href="/{p.slug}">{p.titulo}</a>{badge}</li>')
    return "\n".join(itens)


def render_pillar_jsonld(cluster: Cluster) -> str:
    """Bloco JSON-LD CollectionPage + ItemList da pillar page, gerado a
    partir de data/clusters.json (fonte única). O ItemList lista as páginas
    do cluster, por ordem, com URL absoluto e `position` sequencial; a
    CollectionPage é o tipo desta página como colecção e amarra-se ao
    WebSite único (`isPartOf`, mesmo @id da homepage). Determinístico
    (`json.dumps` estável) — idempotente por construção."""
    itens = [
        {
            "@type": "ListItem",
            "position": i,
            "url": f"{DOMINIO}/{p.slug}",
            "name": p.titulo,
        }
        for i, p in enumerate(cluster.paginas, start=1)
    ]
    dados = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": f"{DOMINIO}{cluster.pillar}#collection",
        "url": f"{DOMINIO}{cluster.pillar}",
        "name": cluster.nome,
        "isPartOf": {"@id": f"{DOMINIO}/#website"},
        "mainEntity": {
            "@type": "ItemList",
            "numberOfItems": len(cluster.paginas),
            "itemListElement": itens,
        },
    }
    corpo = json.dumps(dados, ensure_ascii=False, indent=2)
    corpo_indentado = "\n".join("  " + linha for linha in corpo.split("\n"))
    return f'  <script type="application/ld+json">\n{corpo_indentado}\n  </script>'


def render_badge(cluster: Cluster, titulo_pagina: str) -> str:
    breadcrumb = (
        '    <nav class="breadcrumb-visivel" aria-label="Breadcrumb">'
        f'<a href="/">Início</a> › <a href="{cluster.pillar}">{cluster.nome}</a> › '
        f'<span>{titulo_pagina}</span></nav>'
    )
    pertence = (
        '    <p class="pertence-guia">Este artigo pertence ao guia '
        f'<a href="{cluster.pillar}">{cluster.nome}</a>.</p>'
    )
    return breadcrumb + "\n" + pertence


def artigos_relacionados(
    clusters: List[Cluster], cluster: Cluster, slug_atual: str, maximo: int = MAX_RELACIONADOS
) -> List[Pagina]:
    """1.º irmãos do mesmo cluster, 2.º páginas dos clusters relacionados[]
    explícitos — ordem determinística, sem aleatoriedade."""
    escolhidos: List[Pagina] = []

    for p in cluster.paginas:
        if p.slug == slug_atual:
            continue
        escolhidos.append(p)
        if len(escolhidos) >= maximo:
            return escolhidos

    for rel_id in cluster.relacionados:
        rel = next((c for c in clusters if c.id == rel_id), None)
        if not rel:
            continue
        for p in rel.paginas:
            if p.slug == slug_atual or p in escolhidos:
                continue
            escolhidos.append(p)
            if len(escolhidos) >= maximo:
                return escolhidos

    return escolhidos


def render_relacionados(clusters: List[Cluster], cluster: Cluster, slug_atual: str) -> str:
    """Secção final com dois blocos separados — irmãos do cluster
    ('Artigos relacionados') e páginas de clusters
    relacionados[] ('Pode também interessar') — seguindo a mesma
    ordem/limite de artigos_relacionados(), só reparte a exibição."""
    itens = artigos_relacionados(clusters, cluster, slug_atual)
    irmaos = [p for p in itens if p in cluster.paginas]
    cross = [p for p in itens if p not in cluster.paginas]

    def _lista(paginas: List[Pagina]) -> List[str]:
        return [f'        <li><a href="/{p.slug}">{p.titulo}</a></li>' for p in paginas]

    blocos = ['    <div class="cluster-relacionados">']
    if irmaos:
        blocos.append('      <h2>Artigos relacionados</h2>')
        blocos.append('      <ul>')
        blocos += _lista(irmaos)
        blocos.append('      </ul>')
    if cross:
        blocos.append('      <h2>Pode também interessar</h2>')
        blocos.append('      <ul>')
        blocos += _lista(cross)
        blocos.append('      </ul>')
    blocos.append('      <p class="relacionados-noticias"><a href="/noticias.html">Ver todas as atualizações →</a></p>')
    blocos.append('    </div>')
    return "\n".join(blocos)


_REGEX_HEAD_FECHO = re.compile(r"</head\s*>", re.IGNORECASE)


def _garantir_clusters_css(conteudo: str) -> str:
    """Acrescenta a referência a /assets/css/clusters.css antes de
    </head>, a não ser que já lá esteja (idempotente, mesmo padrão do
    inserir_botao_partilhar.py)."""
    if "/assets/css/clusters.css" in conteudo:
        return conteudo
    match = _REGEX_HEAD_FECHO.search(conteudo)
    if not match:
        return conteudo
    pos = match.start()
    return conteudo[:pos] + '  <link rel="stylesheet" href="/assets/css/clusters.css">\n' + conteudo[pos:]


def encontrar_paginas(raiz: Path = RAIZ) -> List[Path]:
    return (
        sorted(raiz.glob("*.html"))
        + sorted(raiz.glob("p/*.html"))
        + sorted(raiz.glob("documentos/*.html"))
    )


def validar_consistencia(clusters: List[Cluster], raiz: Path = RAIZ) -> List[str]:
    problemas: List[str] = []
    existentes = {str(p.relative_to(raiz)) for p in encontrar_paginas(raiz)}
    referenciados = set()
    pillares = {c.pillar.lstrip("/") for c in clusters}

    for c in clusters:
        for p in c.paginas:
            referenciados.add(p.slug)
            if p.slug not in existentes:
                problemas.append(f"{c.id}: página '{p.slug}' no JSON não tem ficheiro correspondente")
        if c.pillar.lstrip("/") not in existentes:
            problemas.append(f"{c.id}: pillar '{c.pillar}' não tem ficheiro correspondente")

    for nome in sorted(existentes):
        base = Path(nome).name
        if base in EXCLUIDAS or nome in pillares or base in referenciados:
            continue
        problemas.append(f"'{nome}' existe no repositório mas não está em nenhum cluster nem em EXCLUIDAS")

    return problemas


def processar_pagina(caminho: Path, clusters: List[Cluster], *, raiz: Path = RAIZ, escrever: bool = True) -> Resultado:
    nome = str(caminho.relative_to(raiz))

    if caminho.name in EXCLUIDAS:
        return Resultado(nome, False, "excluída do sistema de clusters")

    pillar = cluster_do_pillar(clusters, nome)
    membro = cluster_da_pagina(clusters, caminho.name)

    if not pillar and not membro:
        return Resultado(nome, False, "sem entrada em clusters.json — página órfã")

    conteudo_original = caminho.read_text(encoding="utf-8")
    conteudo = conteudo_original
    faltam: List[str] = []

    if pillar:
        novo = _substituir_bloco(conteudo, MARCADOR_PILLAR_LISTA, render_pillar_lista(pillar))
        if novo is None:
            faltam.append("PILLAR-LISTA")
        else:
            conteudo = novo

        novo = _substituir_bloco(conteudo, MARCADOR_PILLAR_JSONLD, render_pillar_jsonld(pillar))
        if novo is None:
            faltam.append("PILLAR-JSONLD")
        else:
            conteudo = novo

    pagina_atual = None
    if membro:
        pagina_atual = next(p for p in membro.paginas if p.slug == caminho.name)

    # Só artigos ganham navegação contextual (breadcrumb/pertence/relacionados).
    # Ferramentas (simuladores) usam um hero claro incompatível com o CSS de
    # clusters.css (texto branco sobre fundo escuro) — ver CLAUDE.md.
    if membro and pagina_atual.tipo == "artigo":
        novo = _substituir_bloco(conteudo, MARCADOR_BADGE, render_badge(membro, pagina_atual.titulo))
        if novo is None:
            faltam.append("CLUSTER-BADGE")
        else:
            conteudo = novo

        novo = _substituir_bloco(conteudo, MARCADOR_RELACIONADOS, render_relacionados(clusters, membro, caminho.name))
        if novo is None:
            faltam.append("RELACIONADOS")
        else:
            conteudo = novo

        if not faltam:
            conteudo = _garantir_clusters_css(conteudo)

    if faltam:
        return Resultado(nome, False, f"marcador(es) em falta: {', '.join(faltam)} — sem alterações")

    if conteudo == conteudo_original:
        return Resultado(nome, False, "já sincronizado — sem alterações")

    if escrever:
        caminho.write_text(conteudo, encoding="utf-8")
    return Resultado(nome, True, "sincronizado" if escrever else "sincronizado (dry-run, não escrito)")


def processar_home(caminho: Path, clusters: List[Cluster], *, raiz: Path = RAIZ, escrever: bool = True) -> Resultado:
    conteudo_original = caminho.read_text(encoding="utf-8")
    conteudo = conteudo_original
    faltam: List[str] = []

    novo = _substituir_bloco(conteudo, MARCADOR_HOME, render_home_cards(clusters))
    if novo is None:
        faltam.append("CLUSTERS:HOME")
    else:
        conteudo = novo

    novo = _substituir_bloco(conteudo, MARCADOR_DESTAQUES, render_destaques_home(clusters))
    if novo is None:
        faltam.append("DESTAQUES:HOME")
    else:
        conteudo = novo

    novo = _substituir_bloco(conteudo, MARCADOR_ATUALIZACOES, render_atualizacoes_home(clusters, raiz))
    if novo is None:
        faltam.append("ATUALIZACOES:HOME")
    else:
        conteudo = novo

    if faltam:
        return Resultado(caminho.name, False, f"marcador(es) em falta: {', '.join(faltam)} — sem alterações")
    if conteudo == conteudo_original:
        return Resultado(caminho.name, False, "já sincronizado — sem alterações")
    if escrever:
        caminho.write_text(conteudo, encoding="utf-8")
    return Resultado(caminho.name, True, "sincronizado" if escrever else "sincronizado (dry-run, não escrito)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sincroniza a navegação de clusters a partir de data/clusters.json")
    parser.add_argument("--dry-run", action="store_true", help="mostra o que mudaria, sem escrever ficheiros")
    args = parser.parse_args()
    escrever = not args.dry_run

    clusters = carregar_clusters()

    problemas = validar_consistencia(clusters)
    if problemas:
        print("=== Inconsistências entre clusters.json e o repositório ===")
        for p in problemas:
            print(f"  - {p}")
        print()

    resultados = [processar_home(RAIZ / "index.html", clusters, raiz=RAIZ, escrever=escrever)]
    resultados += [
        processar_pagina(p, clusters, escrever=escrever)
        for p in encontrar_paginas()
        if p.name != "index.html"
    ]

    alterados = [r for r in resultados if r.alterado]
    print(f"=== Sincronização de clusters {'(dry-run)' if args.dry_run else ''} ===")
    print(f"Páginas verificadas: {len(resultados)}")
    print(f"Páginas alteradas: {len(alterados)}")
    for r in resultados:
        if r.alterado or "falta" in r.motivo or "órfã" in r.motivo:
            print(f"  - {r.ficheiro}: {r.motivo}")

    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
