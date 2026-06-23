# /nova-noticia

Publica uma nova notícia em `noticias.html` a partir dos feeds RSS oficiais.

## Uso

```
/nova-noticia
```

Sem argumentos — selecciona automaticamente a notícia mais relevante do dia.

## Passos de execução

### Passo 1 — Ler feeds RSS

Feeds por ordem de prioridade:

```python
FEEDS = [
    "https://news.google.com/rss/search?q=apoios+sociais+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://news.google.com/rss/search?q=segurança+social+portugal&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://news.google.com/rss/search?q=IRS+subsidios+portugal+2026&hl=pt-PT&gl=PT&ceid=PT:pt",
    "https://dre.pt/rss/dr1s.rss",
]
```

Correr: `python scripts/gerar_noticias.py`

### Passo 2 — Seleccionar notícia mais relevante

Critérios de relevância (por ordem):
1. Tema: apoios sociais, direitos, burocracia, finanças pessoais PT
2. Fonte: preferência por DRE, gov.pt, seg-social.pt, iefp.pt
3. Frescura: publicada nas últimas 24 horas
4. Impacto: afecta directamente cidadãos (não apenas comentário político)

Rejeitar automaticamente:
- Publicidade ou conteúdo patrocinado
- Notícias sem relevância para o público do site
- Duplicados de notícias já publicadas nos últimos 7 dias

### Passo 3 — Reescrever em PT-PT

**Regras obrigatórias:**
- Nunca copiar texto da fonte — reescrever sempre com palavras próprias
- Máximo 3 linhas de contexto
- Tom factual e neutro — sem opinião, sem dramatismo
- Condicional quando há incerteza: "poderá", "deverá", "segundo X"
- Terminar sempre com link para a fonte original

Estrutura do card:

```html
<article class="noticia">
  <div class="meta">[DD de mês de AAAA] · [Categoria]</div>
  <h2>[Título reescrito — máx. 80 caracteres]</h2>
  <p>[Resumo próprio em 2-3 linhas — nunca copiado da fonte]</p>
  <a href="[url-fonte]" class="fonte" target="_blank" rel="noopener">
    → Fonte: [nome da publicação]
  </a>
  <div class="disclaimer-noticia">
    Resumo informativo. Lê a notícia completa na fonte antes de tomar decisões.
  </div>
</article>
```

### Passo 4 — Validar o link da fonte

Usar a skill `verificar-url` no link da notícia original.
Se o link não retornar 200: não publicar esta notícia, passar para a seguinte.

### Passo 5 — Inserir em noticias.html

Inserir o novo card entre os marcadores:

```html
<!-- INÍCIO NOTÍCIAS GERADAS AUTOMATICAMENTE -->
[novo card aqui — acima dos anteriores]
<!-- FIM NOTÍCIAS GERADAS AUTOMATICAMENTE -->
```

Manter máximo de 7 notícias na página (remover a mais antiga se necessário).

### Passo 6 — Commit

```
auto: notícia [DD/MM/AAAA] — [título curto]

fonte: [url] | relevância: [score]/10
```
