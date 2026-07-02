#!/usr/bin/env python3
"""Gera noticias.html a partir de feeds RSS — corre via GitHub Action diária.

Escreve também a mesma notícia escolhida no bloco NOTICIA-HOME de
index.html, entre marcadores — nunca fora deles (ver SECCOES_PERMITIDAS
e _verificar_escrita_confinada)."""

import feedparser
import html
import os
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape

# Guardrail: ficheiro HTML de escrita livre por este script.
FICHEIROS_AUTO_GERADOS = ["noticias.html"]

# Guardrail: ficheiros HTML onde este script só pode escrever dentro de uma
# secção marcada — qualquer diferença fora dela bloqueia a escrita. Mudança
# de segurança (index.html deixa de estar 100% fora de alcance do script de
# notícias) — ver tests/test_gerar_noticias_guardrail.py.
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
    nome = os.path.basename(caminho)

    if nome in FICHEIROS_AUTO_GERADOS:
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(conteudo)
        return

    if nome.endswith(".html") and nome not in SECCOES_PERMITIDAS:
        raise Exception(
            f"BLOQUEADO: tentativa de escrever em ficheiro protegido: {nome}. "
            f"Apenas {FICHEIROS_AUTO_GERADOS + list(SECCOES_PERMITIDAS)} podem ser "
            f"modificados automaticamente."
        )

    if nome.endswith(".html"):
        marcador_inicio, marcador_fim = SECCOES_PERMITIDAS[nome]
        _verificar_escrita_confinada(caminho, conteudo, marcador_inicio, marcador_fim)

    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)

FEEDS = [
    "https://news.google.com/rss/search?q=apoios+sociais+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://news.google.com/rss/search?q=segurança+social+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://news.google.com/rss/search?q=IRS+subsidios+portugal+2026&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://dre.pt/rss/dr1s.rss",
]

KEYWORDS = [
    "apoio", "apoios", "prestação", "prestações", "subsídio", "subsídios",
    "rsi", "abono", "desemprego", "pensão", "pensões", "ias", "rmg",
    "segurança social", "iefp", "irs", "at ", "finanças", "habitação",
    "renda", "arrendamento", "psu", "prestação social única",
]

STOPWORDS = ["publicidade", "patrocinado", "sponsored", "advertisement"]

CAT_KEYWORDS = {
    "apoios": ["abono", "rsi", "prestação", "apoio social", "segurança social", "psu", "ias", "rmg", "pensão"],
    "educacao": ["escola", "ensino", "ase", "manuais", "bolsa", "universitário", "educação", "dge"],
    "emprego": ["desemprego", "iefp", "trabalho", "emprego", "contrato", "salário"],
    "habitacao": ["habitação", "renda", "arrendamento", "ihru", "casa", "imóvel"],
    "fiscal": ["irs", "at ", "finanças", "imposto", "fiscal", "declaração"],
    "legislacao": ["decreto-lei", "portaria", "lei n.º", "dre", "diário da república", "legislação"],
}


def score_entry(entry):
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    if any(s in text for s in STOPWORDS):
        return -1
    return sum(1 for kw in KEYWORDS if kw in text)


def detect_category(entry):
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    for cat, kws in CAT_KEYWORDS.items():
        if any(kw in text for kw in kws):
            return cat
    return "apoios"


def fetch_entries():
    entries = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries[:10]:
            e["_feed_url"] = url
            entries.append(e)
    return entries


def best_entry(entries):
    scored = [(score_entry(e), e) for e in entries]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored and scored[0][0] > 0 else None


def parse_date(entry):
    try:
        dt = parsedate_to_datetime(entry.get("published", ""))
        return dt.astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def format_date_pt(dt):
    months = [
        "", "jan", "fev", "mar", "abr", "mai", "jun",
        "jul", "ago", "set", "out", "nov", "dez"
    ]
    return f"{dt.day} {months[dt.month]}. {dt.year}"


def format_date_iso(dt):
    return dt.strftime("%Y-%m-%d")


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def limpar_texto(texto):
    """Limpa entidades HTML e espaços múltiplos do texto."""
    if not texto:
        return ""
    # Limpar non-breaking spaces em todas as formas possíveis
    texto = texto.replace('\xa0', ' ')
    texto = texto.replace('&amp;nbsp;', ' ')   # duplamente codificado
    texto = texto.replace('&nbsp;&nbsp;', ' ')
    texto = texto.replace('&nbsp;', ' ')
    texto = texto.replace('&#160;', ' ')
    # Converter entidades HTML restantes
    texto = unescape(texto)
    # Segunda passagem após unescape (apanha &amp;nbsp; → &nbsp; → espaço)
    texto = texto.replace('&nbsp;', ' ')
    texto = texto.replace('&#160;', ' ')
    # Remover tags HTML residuais
    texto = re.sub(r'<[^>]+>', '', texto)
    # Limpar espaços múltiplos
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


CAT_LABELS = {
    "apoios": "Apoios Sociais",
    "educacao": "Educação",
    "emprego": "Emprego",
    "habitacao": "Habitação",
    "fiscal": "Fiscalidade",
    "legislacao": "Legislação",
}


def render_destaque(entry):
    title = html.escape(limpar_texto(entry.get("title", "Sem título")))
    summary = html.escape(limpar_texto(entry.get("summary", "")))[:400]
    link = html.escape(entry.get("link", "#"))
    dt = parse_date(entry)
    date_str = format_date_pt(dt)
    date_iso = format_date_iso(dt)
    cat = detect_category(entry)
    cat_label = CAT_LABELS.get(cat, "Apoios Sociais")

    return f"""<!-- DESTAQUE-INICIO -->
          <article class="destaque-card" data-cat="{cat}">
            <div class="destaque-meta">
              <span class="cat-badge cat-{cat}"><span class="cat-dot"></span><span class="cat-label">{cat_label}</span></span>
              <time datetime="{date_iso}">{date_str}</time>
            </div>
            <h2 class="destaque-titulo">{title}</h2>
            <p class="destaque-resumo">{summary}…</p>
            <a href="{link}" class="destaque-link" target="_blank" rel="noopener noreferrer">Ler notícia completa →</a>
            <p class="disclaimer-noticia">Resumo informativo. Lê a notícia completa na fonte antes de tomar decisões.</p>
          </article>
        <!-- DESTAQUE-FIM -->"""


def render_archive_card(entry):
    """Render a card for the archive grid (from a destaque entry dict or feedparser entry)."""
    title = html.escape(limpar_texto(entry.get("title", "Sem título")))
    summary = html.escape(limpar_texto(entry.get("summary", "")))[:200]
    link = html.escape(entry.get("link", "#"))
    dt = parse_date(entry)
    date_str = format_date_pt(dt)
    date_iso = format_date_iso(dt)
    cat = detect_category(entry) if "title" in entry else entry.get("cat", "apoios")
    cat_label = CAT_LABELS.get(cat, "Apoios Sociais")

    return f"""          <article class="arquivo-card" data-cat="{cat}">
            <div class="arquivo-meta">
              <span class="cat-badge cat-{cat}"><span class="cat-dot"></span><span class="cat-label">{cat_label}</span></span>
              <time datetime="{date_iso}">{date_str}</time>
            </div>
            <h3 class="arquivo-titulo">{title}</h3>
            <p class="arquivo-resumo">{summary}…</p>
            <a href="{link}" class="arquivo-link" target="_blank" rel="noopener noreferrer">Ler →</a>
          </article>"""


def extract_destaque_as_archive(content):
    """Extract current destaque block and convert to archive card HTML."""
    m = re.search(
        r"<!-- DESTAQUE-INICIO -->(.*?)<!-- DESTAQUE-FIM -->",
        content, re.DOTALL
    )
    if not m:
        return None
    block = m.group(1)

    title_m = re.search(r'class="destaque-titulo">(.*?)</h2>', block)
    summary_m = re.search(r'class="destaque-resumo">(.*?)</p>', block, re.DOTALL)
    link_m = re.search(r'class="destaque-link"[^>]*href="([^"]*)"', block)
    if not link_m:
        link_m = re.search(r'href="([^"]*)"[^>]*class="destaque-link"', block)
    date_m = re.search(r'datetime="([^"]*)"', block)
    cat_m = re.search(r'data-cat="([^"]*)"', block)
    cat_label_m = re.search(r'class="cat-label">([^<]*)</span>', block)

    title = limpar_texto(title_m.group(1)) if title_m else "Notícia anterior"
    summary = (limpar_texto(summary_m.group(1)) if summary_m else "")[:200]
    link = link_m.group(1) if link_m else "#"
    date_iso = date_m.group(1) if date_m else ""
    cat = cat_m.group(1) if cat_m else "apoios"
    cat_label = cat_label_m.group(1) if cat_label_m else CAT_LABELS.get(cat, "Apoios Sociais")
    date_str = date_iso  # fallback; ideally reformat

    # Reformat date_iso to PT format
    try:
        dt = datetime.strptime(date_iso, "%Y-%m-%d")
        months = ["", "jan", "fev", "mar", "abr", "mai", "jun",
                  "jul", "ago", "set", "out", "nov", "dez"]
        date_str = f"{dt.day} {months[dt.month]}. {dt.year}"
    except Exception:
        date_str = date_iso

    return f"""          <article class="arquivo-card" data-cat="{cat}">
            <div class="arquivo-meta">
              <span class="cat-badge cat-{cat}"><span class="cat-dot"></span><span class="cat-label">{cat_label}</span></span>
              <time datetime="{date_iso}">{date_str}</time>
            </div>
            <h3 class="arquivo-titulo">{title}</h3>
            <p class="arquivo-resumo">{summary}</p>
            <a href="{link}" class="arquivo-link" target="_blank" rel="noopener noreferrer">Ler →</a>
          </article>"""


def render_noticia_home(entry):
    """Card compacto para a homepage — reutiliza as classes CSS já
    existentes em index.html (noticia-card/badge-hoje/link-ler). Mostra
    sempre a data real da notícia, nunca "hoje"; liga directamente à
    fonte externa, nunca a um link interno inventado."""
    title = html.escape(limpar_texto(entry.get("title", "Sem título")))
    summary = html.escape(limpar_texto(entry.get("summary", "")))[:220]
    link = html.escape(entry.get("link", "#"))
    dt = parse_date(entry)
    date_str = format_date_pt(dt)

    return (
        '    <div class="noticia-card">\n'
        f'      <span class="badge-hoje">{date_str}</span>\n'
        f'      <h3>{title}</h3>\n'
        f'      <p>{summary}…</p>\n'
        f'      <a href="{link}" class="link-ler" target="_blank" rel="noopener noreferrer">Ler notícia completa →</a>\n'
        '    </div>'
    )


def load_template():
    with open("noticias.html", encoding="utf-8") as f:
        return f.read()


def save(content):
    escrever_ficheiro_seguro("noticias.html", content)


def atualizar_index_home(entry, caminho="index.html"):
    """Injecta a mesma notícia escolhida também no bloco NOTICIA-HOME do
    index.html — segunda fonte de frescura da homepage, junto de
    'Atualizado recentemente' (gerado por sincronizar_clusters.py a
    partir das datas reais dos artigos)."""
    marcador_inicio, marcador_fim = SECCOES_PERMITIDAS["index.html"]
    padrao = re.compile(
        rf"<!-- {re.escape(marcador_inicio)} -->[\s\S]*?<!-- {re.escape(marcador_fim)} -->"
    )

    with open(caminho, encoding="utf-8") as f:
        conteudo = f.read()

    if not padrao.search(conteudo):
        print(f"AVISO: marcadores {marcador_inicio}/{marcador_fim} não encontrados em {caminho} — sem injecção")
        return

    novo_bloco = f"<!-- {marcador_inicio} -->\n{render_noticia_home(entry)}\n    <!-- {marcador_fim} -->"
    novo_conteudo = padrao.sub(lambda m: novo_bloco, conteudo, count=1)

    if novo_conteudo == conteudo:
        print(f"{caminho}: notícia já actualizada — sem alterações")
        return

    escrever_ficheiro_seguro(caminho, novo_conteudo)
    print(f"{caminho}: bloco de notícias actualizado")


def main():
    entries = fetch_entries()
    entry = best_entry(entries)
    if not entry:
        print("Nenhuma notícia relevante encontrada hoje.")
        return

    content = load_template()

    # 1. Extract current destaque and convert to archive card
    old_destaque_card = extract_destaque_as_archive(content)

    # 2. Build new destaque block
    new_destaque = render_destaque(entry)

    # 3. Replace destaque block
    content = re.sub(
        r"<!-- DESTAQUE-INICIO -->.*?<!-- DESTAQUE-FIM -->",
        new_destaque,
        content,
        flags=re.DOTALL,
    )

    # 4. Prepend old destaque as archive card (after ARQUIVO-INICIO marker)
    if old_destaque_card:
        content = re.sub(
            r"(<!-- ARQUIVO-INICIO -->)",
            r"\1\n" + old_destaque_card,
            content,
        )

    save(content)
    print(f"Notícia publicada: {entry.get('title', '')[:80]}")

    atualizar_index_home(entry)


if __name__ == "__main__":
    main()
