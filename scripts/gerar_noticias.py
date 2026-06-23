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


def score_entry(entry):
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    if any(s in text for s in STOPWORDS):
        return -1
    return sum(1 for kw in KEYWORDS if kw in text)


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
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]
    return f"{dt.day} de {months[dt.month]} de {dt.year}"


def strip_tags(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def render_article(entry):
    title = html.escape(strip_tags(entry.get("title", "Sem título")))
    summary = html.escape(strip_tags(entry.get("summary", "")))[:400]
    link = html.escape(entry.get("link", "#"))
    source = html.escape(entry.get("source", {}).get("title", link[:60]))
    dt = parse_date(entry)
    date_str = format_date_pt(dt)

    return f"""    <article class="noticia">
      <div class="meta">{date_str} · Apoios Sociais</div>
      <h2>{title}</h2>
      <p>{summary}…</p>
      <a href="{link}" class="fonte" target="_blank" rel="noopener">→ Fonte: {source}</a>
      <div class="disclaimer-noticia">Resumo informativo. Lê a notícia completa na fonte antes de tomar decisões.</div>
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

    article_html = render_article(entry)
    template = load_template()

    new_content = re.sub(
        r"<!-- INÍCIO NOTÍCIAS GERADAS AUTOMATICAMENTE -->.*?<!-- FIM NOTÍCIAS GERADAS AUTOMATICAMENTE -->",
        f"<!-- INÍCIO NOTÍCIAS GERADAS AUTOMATICAMENTE -->\n{article_html}\n    <!-- FIM NOTÍCIAS GERADAS AUTOMATICAMENTE -->",
        template,
        flags=re.DOTALL,
    )
    save(new_content)
    print(f"Notícia publicada: {entry.get('title', '')[:80]}")


if __name__ == "__main__":
    main()
