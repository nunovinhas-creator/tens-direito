import feedparser

FEEDS = {
    "irs_fiscalidade": "https://news.google.com/rss/search?q=IRS+declara%C3%A7%C3%A3o+de+rendimentos+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "ias_valor_referencia": "https://news.google.com/rss/search?q=IAS+indexante+apoios+sociais+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "calendario_pagamentos_seg_social": "https://news.google.com/rss/search?q=calend%C3%A1rio+pagamentos+seguran%C3%A7a+social+pens%C3%B5es+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "habitacao_arrendamento": "https://news.google.com/rss/search?q=apoio+arrendamento+habita%C3%A7%C3%A3o+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "salario_minimo": "https://news.google.com/rss/search?q=sal%C3%A1rio+m%C3%ADnimo+nacional+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "csi_idosos": "https://news.google.com/rss/search?q=complemento+solid%C3%A1rio+para+idosos+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
}

for nome, url in FEEDS.items():
    feed = feedparser.parse(url)
    print(f"=== {nome} ===")
    print(f"  bozo={feed.bozo} n_entradas={len(feed.entries)}")
    for e in feed.entries[:5]:
        print(f"  - [{e.get('published', '?')}] {e.get('title', '?')[:100]}")
    print()
