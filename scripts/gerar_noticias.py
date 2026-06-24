#!/usr/bin/env python3
"""Gera noticias.html a partir de feeds RSS — corre via GitHub Action diária."""

import feedparser
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

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


CAT_LABELS = {
    "apoios": "Apoios Sociais",
    "educacao": "Educação",
    "emprego": "Emprego",
    "habitacao": "Habitação",
    "fiscal": "Fiscalidade",
    "legislacao": "Legislação",
}


def render_destaque(entry):
    title = html.escape(strip_tags(entry.get("title", "Sem título")))
    summary = html.escape(strip_tags(entry.get("summary", "")))[:400]
    link = html.escape(entry.get("link", "#"))
    source = html.escape(entry.get("source", {}).get("title", link[:60]))
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
    title = html.escape(strip_tags(entry.get("title", "Sem título")))
    summary = html.escape(strip_tags(entry.get("summary", "")))[:200]
    link = html.escape(entry.get("link", "#"))
    source = html.escape(entry.get("source", {}).get("title", link[:60]))
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

    title = title_m.group(1) if title_m else "Notícia anterior"
    summary = (summary_m.group(1) if summary_m else "")[:200]
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


def load_template():
    with open("noticias.html", encoding="utf-8") as f:
        return f.read()


def save(content):
    with open("noticias.html", "w", encoding="utf-8") as f:
        f.write(content)


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


if __name__ == "__main__":
    main()
