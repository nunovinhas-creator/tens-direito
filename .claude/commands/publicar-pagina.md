# /publicar-pagina

Publica uma nova página de conteúdo seguindo o pipeline scraper-first obrigatório do CLAUDE.md.

## Uso

```
/publicar-pagina [slug] [titulo] [fonte]
```

Exemplos:
- `/publicar-pagina rsi "RSI 2026: rendimento, condições e como pedir" seg_social_rsi`
- `/publicar-pagina desemprego "Subsídio de desemprego 2026" iefp_desemprego`

## Passos de execução (obrigatórios e pela ordem indicada)

### Passo 1 — Scrape da fonte primária

Corre o scraper correspondente à fonte indicada:

```bash
python scripts/scraper_fontes.py
```

Verifica que o ficheiro `data/scraped/[fonte]_[data].json` foi criado.
Se o scraper falhar: registar em `VERIFICACAO-PENDENTE.md` e **PARAR** — nunca avançar com dados de memória.

### Passo 2 — Validar o JSON extraído

Abrir o JSON e confirmar:
- Campo `status` é `"ok"` (não `"erro"`)
- `conteudo_extraido.paragrafos` tem pelo menos 2 entradas não-vazias
- Os valores numéricos fazem sentido (IAS ~537 €, não 5 € nem 5000 €)
- Não é uma página de erro (sem "404", "não encontrada", "unavailable")

Se inválido: registar motivo em `VERIFICACAO-PENDENTE.md` e **PARAR**.

### Passo 3 — Gerar o HTML

Usar a skill `estrutura-pagina` para o template base.
Preencher com os factos extraídos do JSON — **nunca de memória**.
Cada secção de factos deve incluir:

```html
<!-- FONTE: [url] | scraped: [data_acesso] -->
```

Guardar em `[slug].html` na raiz do repositório.

### Passo 4 — Auditar todos os links

Para cada `href` na página gerada, usar a skill `verificar-url`:
- **200** → manter
- **403** → substituir pela página-mãe (ex: `seg-social.pt` em vez de `seg-social.pt/sub/path`)
- **404** → remover o link, texto fica sem âncora
- **timeout** → marcar com `[VERIFICAR — timeout em DD/MM/AAAA]`

Nunca publicar um link não testado.

### Passo 5 — Actualizar sitemap.xml

Adicionar entrada em `sitemap.xml`:

```xml
<url>
  <loc>https://tensdireito.com/[slug].html</loc>
  <changefreq>monthly</changefreq>
  <priority>0.9</priority>
</url>
```

### Passo 6 — Adicionar card no index.html

Inserir card na `<main>` do `index.html` com título, resumo de 1 linha e link para a página.

### Passo 7 — Actualizar data/scraped/_index.json

```json
{
  "pagina": "[slug].html",
  "fonte": "[url_fonte]",
  "data_scrape": "[ISO date]",
  "proxima_revisao": "[ISO date +30 dias]"
}
```

### Passo 8 — Commit com mensagem padronizada

```
feat: [slug] — [titulo curto]

fonte: [url] | scraped: [data] | próxima revisão: [data+30d]
```

## Checklist antes do commit

- [ ] JSON do scraper existe e tem status "ok"
- [ ] Todos os links testados (nenhum com 404)
- [ ] JSON-LD FAQPage e HowTo presentes
- [ ] Disclaimer de independência presente
- [ ] Data de verificação visível na página
- [ ] sitemap.xml actualizado
- [ ] index.html tem card da nova página
