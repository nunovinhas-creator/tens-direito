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

### Passo 6 — Actualizar scripts/pesquisa.js

`pesquisa.js` é uma lista manual (não gerada a partir de `clusters.json` — ver
CLAUDE.md secção "FECHO DO PROJECTO"). Adicionar uma entrada `{url, titulo,
keywords}` para `[slug].html`.

### Passo 7 — Botão de partilha

```bash
python scripts/inserir_botao_partilhar.py
```

Idempotente — insere `assets/js/share.js` + `assets/css/share.css` e o botão
"Partilhar este artigo" só em páginas que ainda não o têm.

### Passo 8 — Registar no cluster e sincronizar

Se `[slug].html` pertence a um dos 5 clusters (ver CLAUDE.md secção "SISTEMA
DE CLUSTERS" — não é o caso de páginas institucionais como sobre/fontes):

1. Adicionar a entrada em `data/clusters.json`, dentro de `paginas[]` do
   cluster correspondente: `{"slug": "[slug].html", "titulo": "...",
   "tipo": "artigo", "destaque": false}` (`destaque: true` só por decisão
   explícita — ver regra dos cartões da homepage).
2. Correr:

```bash
python scripts/sincronizar_clusters.py
```

Idempotente — injecta `CLUSTER-BADGE`/`RELACIONADOS` na página nova (só
`tipo: "artigo"`; ferramentas ficam de fora — ver secção "SISTEMA DE
CLUSTERS", ponto 6), actualiza o `PILLAR-LISTA` do pillar do cluster, e o
`CLUSTERS:HOME`/`DESTAQUES:HOME` do `index.html` se aplicável.
Correr sempre primeiro com `--dry-run` para conferir o diff.

### Passo 9 — Sincronizar a navegação principal

```bash
python scripts/sincronizar_nav.py
```

Idempotente — a página nova ainda não tem o bloco `NAV:INICIO/FIM`; o script
faz o bootstrap automático a partir da estrutura `<header><nav>` do template
`estrutura-pagina`. Correr sempre depois do Passo 8 (a nav lista os 5
pillars, não páginas individuais, por isso a ordem com o Passo 8 não é
crítica, mas mantém-se esta para bater certo com a checklist do CLAUDE.md).

### Passo 10 — Testes de coerência

```bash
python -m pytest tests/test_breadcrumb_coerencia.py tests/test_nav_coerencia.py tests/test_sincronizar_clusters.py
```

Estes testes correm sobre as páginas **reais** do repositório (parametrizados),
por isso a página nova entra automaticamente — não precisa de nenhum caso
novo escrito à mão. Se algum falhar: corrigir antes de avançar, nunca
ignorar (nenhum `--no-verify`, nenhum skip).

### Passo 11 — Actualizar data/scraped/_index.json

```json
{
  "pagina": "[slug].html",
  "fonte": "[url_fonte]",
  "data_scrape": "[ISO date]",
  "proxima_revisao": "[ISO date +30 dias]"
}
```

### Passo 12 — Commit com mensagem padronizada

```
feat: [slug] — [titulo curto]

fonte: [url] | scraped: [data] | próxima revisão: [data+30d]
```

## Checklist antes do commit

- [ ] `git branch` mostra `* main`
- [ ] JSON do scraper existe e tem status "ok"
- [ ] Todos os links testados (nenhum com 404)
- [ ] JSON-LD FAQPage + HowTo + BreadcrumbList presentes
- [ ] Disclaimer de independência presente
- [ ] Data de verificação ("Verificado a...") visível na página
- [ ] `sitemap.xml` actualizado
- [ ] `scripts/pesquisa.js` actualizado
- [ ] `python scripts/inserir_botao_partilhar.py` corrido
- [ ] `data/clusters.json` actualizado (se a página pertence a um cluster) e `python scripts/sincronizar_clusters.py` corrido
- [ ] `python scripts/sincronizar_nav.py` corrido — página nova tem bloco `NAV:INICIO/FIM`
- [ ] `test_breadcrumb_coerencia.py` e `test_nav_coerencia.py` a passar
- [ ] Commit e push directamente para `main`
