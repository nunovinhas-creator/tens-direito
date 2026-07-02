# CLAUDE.md — Tens Direito

Instruções globais para o Claude Code neste repositório.
Ler sempre antes de qualquer tarefa.

---

## REGRA DE OURO — FICHEIROS AUTO-GERADOS vs MANUAIS

O pipeline automático (`pipeline-diario.yml`) só pode escrever em:
- `index.html` — só dentro de três zonas marcadas, nunca o resto da página:
  - data de verificação (`id="ultima-revisao-mes"` + `dateModified` do JSON-LD) — `sed`, Step 6
  - `<!-- DESTAQUE:INICIO/FIM -->` — banner sazonal/evento, Step 6a
  - `<!-- NOTICIA-HOME:INICIO/FIM -->` — card "Últimas notícias", Step 3 (`gerar_noticias.py`)
- `noticias.html` — notícia do dia via RSS (ficheiro inteiro, sem marcadores)
- `CLAUDE.md` — data de revisão automática
- `README.md` — estado do repositório
- `data/scraped/*.json` — dados do scraper

**TODOS os outros HTML são manuais e protegidos.**
Esta regra aplica-se a páginas actuais E futuras.
Qualquer novo HTML criado está automaticamente protegido — não precisa de ser adicionado a listas.

O guardrail está implementado em dois locais:
1. `scripts/gerar_noticias.py` — função `escrever_ficheiro_seguro()` bloqueia qualquer escrita em HTML que não seja `noticias.html` (escrita livre) ou `index.html` (só dentro de `NOTICIA-HOME:INICIO/FIM` — `_verificar_escrita_confinada()` compara o ficheiro em disco com o novo conteúdo fora da secção marcada; qualquer diferença aí, ou o marcador não existir, bloqueia a escrita — ver `tests/test_gerar_noticias_guardrail.py`)
2. `.github/workflows/pipeline-diario.yml` — step "Verificar ficheiros protegidos" faz `exit 1` se algum HTML protegido for detectado como modificado antes do commit

Nota: o marcador `<!-- ATUALIZACOES:HOME:INICIO/FIM -->` (bloco "Atualizado
recentemente") também vive em `index.html`, mas é escrito por
`scripts/sincronizar_clusters.py` — um script de **sessão manual**, não do
pipeline automático (mesma categoria que `CLUSTERS:HOME`/`DESTAQUES:HOME` —
ver secção "SISTEMA DE CLUSTERS"). Não entra nesta lista porque não é o
pipeline `pipeline-diario.yml` a escrevê-lo.

**Segundo workflow com push, âmbito completamente separado**: `shadow-daily.yml`
só pode escrever em `shadow_history/*.md` (relatórios do Shadow Mode — ver secção
"SHADOW MODE" mais abaixo). Guardrail próprio no próprio workflow: falha
(`exit 1`, sem commit) se detectar qualquer alteração fora de `shadow_history/`
ou qualquer ficheiro de histórico apagado. Nunca escreve HTML, nunca toca em
Issues, nunca activa auto-update real.

Para modificar uma página de conteúdo:
1. Sessão Claude Code manual
2. Fact-checking prévio da informação
3. Commit manual com mensagem descritiva
4. **Nunca via pipeline automático**

---

## REGRA ABSOLUTA — GIT

NUNCA criar branches. SEMPRE trabalhar em main.

Workflow obrigatório em TODOS os commits:
  git add .
  git commit -m "mensagem"
  git push origin main

PROIBIDO:
  git checkout -b [qualquer nome]
  git switch -c [qualquer nome]
  Criar Pull Requests
  Trabalhar em qualquer branch que não seja main

Se o Claude Code sugerir criar uma branch: RECUSAR.
Se estiver numa branch diferente de main: fazer
merge imediato para main antes de qualquer trabalho.

Verificação obrigatória antes de cada push:
  git branch  → deve mostrar * main
  Se não mostrar: git checkout main primeiro

---

## O QUE É ESTE PROJECTO

Site informativo PT-PT sobre apoios sociais, direitos e burocracia em Portugal.
Cada facto tem data de verificação e ligação à fonte oficial.

- **Domínio**: tensdireito.com
- **Hosting**: GitHub Pages (branch main, raiz /)
- **Ficheiros críticos**: `CNAME` (não apagar), `.nojekyll` (não apagar)
- **Pipeline automático**: diário às 06:00 UTC via `pipeline-diario.yml`

---

## STACK TÉCNICO ACTUAL

| Componente | Detalhe |
|---|---|
| Hosting | GitHub Pages, branch main, raiz / |
| HTML | Estático puro — sem Jekyll, sem SSG |
| Analytics | GA4: `G-XP46PM8H1Q` |
| Consentimento | CookieYes: `cdn-cookieyes.com/client_data/522e43e147a82ddc222c861fa2abead7/script.js` |
| Pesquisa interna | `scripts/pesquisa.js` (JS puro, 27 páginas indexadas — todas excepto `index.html` e `404.html`) |
| Scraper | Playwright + BeautifulSoup (`scripts/scraper_playwright.py`) |
| Extracção valores | `scripts/extrair_valores.py` → `data/divergencias.json` |
| Notícias | `scripts/gerar_noticias.py` → `noticias.html` + card em `index.html` (`NOTICIA-HOME`) |
| Partilha social | `assets/js/share.js` + `assets/css/share.css`, inserido em cada página via `scripts/inserir_botao_partilhar.py` (idempotente, sem bibliotecas externas) |
| Clusters/navegação | `data/clusters.json` (fonte única) + `scripts/sincronizar_clusters.py` (idempotente, injecta entre marcadores — ver secção "SISTEMA DE CLUSTERS") |

### Workflows (5 — 2 fazem push, âmbitos disjuntos)

| Ficheiro | Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | cron `0 6 * * *` | Scrape → detectar mudanças → notícias → validar valores → README → push único | ✅ sim (`data/`, `index.html`, `noticias.html`, `README.md`, `CLAUDE.md`) |
| `shadow-daily.yml` | cron `0 3 * * *` | `run_shadow_daily.py`: Shadow Mode → analytics → relatório Markdown → guarda em `shadow_history/` | ✅ sim (só `shadow_history/*.md`) |
| `verificar-links.yml` | cron `0 7 * * 1` (segunda) | lychee testa todos os links HTML + Issue se 404 | ❌ não |
| `validar-conteudo.yml` | push para main `**.html` | Valida GA4, OG tags, JSON-LD, disclaimer, data verificação + HTML5 validator | ❌ não |
| `integridade.yml` | push a main, cron semanal, manual | Gitleaks (segredos) + Ruff + pip-audit + validador HTML5 + `verificar_injecao.py` (prompt injection em `data/`/`shadow_history/`) | ❌ não |

**`pipeline-diario.yml` e `shadow-daily.yml` são os únicos que fazem `git push`,
cada um com um âmbito de escrita disjunto e garantido por guardrail próprio**
(ficheiros de conteúdo/dados vs. só `shadow_history/*.md`). Os restantes só lêem.
Isto elimina race conditions entre workflows concorrentes.

---

## PÁGINAS PUBLICADAS

| Ficheiro | Título | Publicada |
|---|---|---|
| `index.html` | Tens Direito — Apoios sociais em Portugal | jun. 2026 |
| `abono-de-familia.html` | Abono de Família 2026 | jun. 2026 |
| `acao-social-escolar.html` | Ação Social Escolar 2026/2027 | jun. 2026 |
| `bolsa-de-merito.html` | Bolsa de Mérito 2026 | jun. 2026 |
| `manuais-escolares-mega.html` | Manuais Escolares Gratuitos MEGA | jun. 2026 |
| `passe-sub23.html` | Passe Sub-23 Gratuito | jun. 2026 |
| `p/apoios-escolares.html` | Apoios Escolares em Portugal 2026/2027 — Guia Completo | 30 jun. 2026 |
| `complemento-solidario-idosos.html` | Complemento Solidário para Idosos (CSI) 2026 | 28 jun. 2026 |
| `prestacao-social-unica.html` | Prestação Social Única (PSU) 2026 | 28 jun. 2026 |
| `amim.html` | AMIM — Atestado Médico de Incapacidade Multiuso | 1 jul. 2026 |
| `psu-quando-entra-em-vigor.html` | PSU 2026: o que já foi aprovado e o que ainda falta decidir | 1 jul. 2026 |
| `psu-quem-tem-direito.html` | Quem tem direito à PSU — condições de acesso aprovadas | 1 jul. 2026 |
| `psu-vs-abono-familia.html` | PSU e Abono de Família: são apoios diferentes | 1 jul. 2026 |
| `psu-lista-13-apoios.html` | As 13 prestações que a PSU vai substituir (lista completa 2026) | 1 jul. 2026 |
| `rsi.html` | RSI 2026 — Rendimento Social de Inserção | jun. 2026 |
| `subsidio-desemprego.html` | Subsídio de Desemprego 2026 | jun. 2026 |
| `subsidio-parental.html` | Licença Parental 2026 | jun. 2026 |
| `cuidador-informal.html` | Estatuto do Cuidador Informal 2026 | jun. 2026 |
| `comecar-aqui.html` | Começa Aqui — encontra o teu apoio | jun. 2026 |
| `simulador-abono.html` | Simulador de Abono de Família 2026 | jun. 2026 |
| `simulador-ase.html` | Simulador de Ação Social Escolar (ASE) 2026/2027 | jun. 2026 |
| `p/familia.html` | Apoios para Família e Crianças em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `p/idosos-incapacidade-cuidadores.html` | Apoios para Idosos, Incapacidade e Cuidadores em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `p/trabalho-rendimento.html` | Apoios de Trabalho e Rendimento em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `noticias.html` | Notícias | jun. 2026 |
| `sobre.html` | Sobre o Tens Direito | jun. 2026 |
| `fontes.html` | Fontes Oficiais | jun. 2026 |
| `privacidade.html` | Política de Privacidade | jun. 2026 |
| `404.html` | Página não encontrada | jun. 2026 |

*Tabela corrigida a 2026-07-02 — faltavam 7 páginas já publicadas (rsi, subsidio-desemprego,
subsidio-parental, cuidador-informal, comecar-aqui, simulador-abono, simulador-ase).*

---

## CHECKLIST OBRIGATÓRIA ANTES DE QUALQUER COMMIT

Antes de qualquer `git commit`, verificar cada ponto:

- [ ] `git branch` mostra `* main`
- [ ] Factos retirados de `data/scraped/` ou pesquisa verificada — **NUNCA de memória**
- [ ] Links testados — só usar URLs da lista verificada ou homepage do domínio oficial
- [ ] Página tem GA4 snippet `G-XP46PM8H1Q`
- [ ] CookieYes script **ANTES** do GA4 no `<head>`
- [ ] `og:title`, `og:description`, `og:url`, `og:locale` presentes
- [ ] JSON-LD `FAQPage` + `HowTo` + `BreadcrumbList` presentes
- [ ] `"Verificado a [data]"` visível no corpo da página
- [ ] Disclaimer de independência (`Aviso de independência`) presente
- [ ] `sitemap.xml` actualizado se nova página
- [ ] `scripts/pesquisa.js` actualizado com nova página (se nova página de conteúdo)
- [ ] Nova página de conteúdo? Correr `python scripts/inserir_botao_partilhar.py` (idempotente — adiciona o botão "Partilhar este artigo" só às páginas que ainda não o têm)
- [ ] Nova página pertence a um cluster? Actualizar `data/clusters.json` e correr `python scripts/sincronizar_clusters.py` (ver secção "SISTEMA DE CLUSTERS")
- [ ] Nova página? Correr `python scripts/sincronizar_nav.py` para injectar a nav principal única (ver secção "NAVEGAÇÃO PRINCIPAL")
- [ ] Testes de coerência a passar: `pytest tests/test_breadcrumb_coerencia.py tests/test_nav_coerencia.py` (parametrizados sobre as páginas reais — cobrem a página nova automaticamente)
- [ ] Alterado algum `.py`? Correr `ruff check scripts/ --select E,F,W --ignore E501 .` — mesmo comando do job "Qualidade Python (Ruff)" em `integridade.yml` (nota: a `ruff-action` acrescenta a raiz do repo aos alvos, por isso `tests/` também é verificado, apesar do `scripts/` explícito no comando)
- [ ] Commit e push directamente para `main`

---

## ESTRUTURA DE FICHEIROS ACTUAL

```
tens-direito/
├── *.html                    ← páginas estáticas publicadas (raiz = GitHub Pages)
├── assets/
│   ├── js/share.js           ← lógica do botão "Partilhar este artigo" (vanilla JS)
│   ├── js/nav.js             ← interacção da nav principal (dropdown, hamburger) — partilhado
│   ├── css/share.css         ← estilo do botão/mensagens de partilha
│   ├── css/clusters.css      ← estilo do breadcrumb/pertence/relacionados injectados nos artigos
│   └── css/nav.css           ← estilo da nav principal única (todas as páginas)
├── scripts/
│   ├── scraper_playwright.py ← Playwright + BS4, scrapes 6 fontes
│   ├── extrair_valores.py    ← compara valores scraped vs HTML publicado
│   ├── gerar_noticias.py     ← RSS → noticias.html + card em index.html (NOTICIA-HOME)
│   ├── gerar_pagina.py       ← utilitário de geração HTML
│   ├── inserir_botao_partilhar.py ← insere assets/js/share.js + assets/css/share.css (idempotente)
│   ├── verificar_datas.py    ← Camada 1: deteção de datas/valores expirados
│   ├── classificar_datas.py  ← Camada 2: classifica cada correspondência (EstadoData)
│   ├── decisao_datas.py      ← Camada 3: estado → acção (AUTO_UPDATE_HABILITADO=False)
│   ├── auto_update_engine.py ← Camada 4: auto-update sandbox, só em memória
│   ├── orquestrador_datas.py ← Camada 5: único ponto autorizado a chamar a Camada 4
│   ├── source_adapter.py     ← Camada 6: obtenção de valores oficiais (providers placeholder)
│   ├── shadow_mode.py        ← corre a cadeia completa em modo observação pura
│   ├── shadow_mode_analytics.py ← agrega relatórios do Shadow Mode em métricas
│   ├── shadow_report_md.py   ← métricas → relatório Markdown legível
│   ├── run_shadow_daily.py   ← orquestrador único: liga os 3 acima + guarda histórico
│   ├── sincronizar_clusters.py ← lê data/clusters.json, injecta breadcrumb/relacionados/pillar-lista (idempotente)
│   ├── sincronizar_nav.py    ← bootstrap + sincroniza a nav principal única (idempotente)
│   ├── verificar_injecao.py  ← guardrail: prompt injection em data/ e shadow_history/ (integridade.yml)
│   ├── pesquisa.js           ← pesquisa interna (JS puro, sem servidor)
│   └── logs/                 ← logs do scraper
├── tests/                    ← pytest; inclui test_sincronizar_clusters.py,
│                                test_breadcrumb_coerencia.py e test_nav_coerencia.py
│                                (estes dois últimos correm sobre as páginas reais, não fixtures)
├── data/
│   ├── clusters.json         ← fonte única de verdade da arquitectura de clusters
│   ├── scraped/              ← JSONs diários por fonte + *_latest.json
│   ├── mudancas.json         ← mudanças detectadas pelo pipeline
│   └── divergencias.json     ← valores scraped vs publicado
├── shadow_history/
│   └── shadow_report_AAAA-MM-DD.md ← 1 relatório/dia, gerado por shadow-daily.yml
├── .github/workflows/
│   ├── pipeline-diario.yml   ← pipeline de conteúdo/dados, com push
│   ├── shadow-daily.yml      ← Shadow Mode diário, com push (só shadow_history/)
│   ├── verificar-links.yml   ← lychee (só lê)
│   ├── validar-conteudo.yml  ← validador HTML (só lê)
│   └── integridade.yml       ← verificações de integridade (só lê)
├── .claude/
│   ├── commands/             ← /publicar-pagina, /verificar-fontes, /nova-noticia
│   └── skills/               ← estrutura-pagina, verificar-url
├── CNAME                     ← tensdireito.com — NÃO APAGAR
├── .nojekyll                 ← força HTML estático — NÃO APAGAR
├── sitemap.xml
├── favicon.svg
└── CLAUDE.md                 ← este ficheiro
```

---

## FONTES VERIFICADAS E APROVADAS

### Regra absoluta
NUNCA escrever valores, condições ou prazos de memória.
Sempre ir à fonte primária ANTES de redigir.
Se a fonte não confirmar o facto, o facto não entra no site.

### URLs confirmados a funcionar

| Tema | URL | Notas |
|---|---|---|
| Abono de família | https://www.seg-social.pt/abono-de-familia | OK |
| Abono — simulador | https://www.seg-social.pt/ptss/sps/simulador/6 | OK |
| Segurança Social Direta | https://www.seg-social.pt | OK (usar homepage — /ptss/ssd devolve 404 sem autenticação) |
| Segurança Social (geral) | https://www.seg-social.pt | OK |
| ASE — DGE homepage | https://www.dge.mec.pt | OK (subpath /acao-social-escolar devolve 403) |
| MEGA — manuais | https://www.dge.mec.pt/manuais-escolares | OK |
| MEGA — portal público | https://www.manuaisescolares.pt | OK |
| Bolsa de mérito | https://dre.pt | OK (subpath DGE devolve 403 — usar DRE) |
| Passe sub-23 | https://www.gov.pt | OK |
| CP | https://www.cp.pt | OK (subpath /passageiros/... pode dar 404) |
| IEFP | https://www.iefp.pt/subsidio-desemprego | OK (sem hífen antes de desemprego) |
| IEFP — fallback | https://www.seg-social.pt/subsidio-de-desemprego | OK |
| DRE | https://dre.pt | OK (RSS inacessível nos runners GitHub) |
| Gov.pt | https://www.gov.pt | OK |
| SNS | https://www.sns.gov.pt | OK |
| IHRU | https://www.ihru.pt | OK |
| IMT | https://www.imt-ip.pt | OK |
| Portal Finanças | https://www.portaldasfinancas.gov.pt | OK |

### Diplomas legais confirmados (link para homepage diariodarepublica.pt)

| Diploma | Tema | Nota |
|---|---|---|
| Portaria n.º 480-A/2025/1 | IAS 2026 = 537,13 € | 30 dez 2025 |
| Portaria n.º 60/2026/1 | Abono família — valores 2026 | 5 fev 2026 |
| Portaria n.º 71/2026/1 | RSI base 2026 = 247,56 € | 13 fev 2026 |
| DL n.º 220/2006 | Subsídio desemprego — regime jurídico | 3 nov 2006 |
| DL n.º 91/2009 | Subsídio parental — regime jurídico | 9 abr 2009 |
| Despacho n.º 8452-A/2015 | ASE e bolsa de mérito | link directo DR disponível |
| Despacho n.º 5296/2017 | Alteração ao ASE 8452-A/2015 | link directo DR disponível |
| Lei n.º 13/2003 | RSI — lei base | 21 mai 2003 |
| Portaria n.º 7-A/2024 | Passe sub-23 gratuito | 5 jan 2024 |

### Valores de referência (2026)
- **IAS 2026**: 537,13 € (Portaria n.º 480-A/2025/1, de 30 de dezembro)
- **Salário mínimo 2026**: 920,00 €
- **RSI base 2026**: 247,56 € (Portaria n.º 71/2026/1)
- **Abono 1.º escalão ≤36 meses**: 190,98 €/mês (Portaria n.º 60/2026/1)
- **Abono 1.º escalão >72 meses**: 75,13 €/mês (Portaria n.º 60/2026/1)
- **Subsídio desemprego mínimo**: 537,13 €/mês (100% IAS)
- **Subsídio desemprego máximo**: 1.342,83 €/mês (2,5 × IAS)
- **Bolsa de mérito 2025/2026**: 1.306,25 € (2,5 × IAS 2025 = 2,5 × 522,50 €)
- Limite 2.º escalão abono: 1,5 × 537,13 = **805,70 €/mês** per capita

**✓ Confirmados após fact-checking completo (2026-06-28)**: Todos os valores de referência foram verificados e confirmados em páginas publicadas. Nenhuma discrepância encontrada entre valores scraped e valores publicados. CSI e PSU fact-checked e publicadas.

### Regra de links
NUNCA inventar subpaths de portais oficiais.
Quando um subpath devolve erro: usar a homepage do domínio.
Se não houver URL confirmado: escrever "consulta nos serviços da escola/agrupamento" sem link.

### URLs PROIBIDOS (devolvem 404 ou área privada)
| URL proibido | Motivo | Usar em substituição |
|---|---|---|
| `https://app.seg-social.pt/ptss/ssd` | Área privada — 404 sem autenticação | `https://www.seg-social.pt` |

---

## REGRAS DE CONTEÚDO

1. **Português de Portugal** em todo o conteúdo — nunca PT-BR.
2. **Só fontes primárias**: DR, gov.pt, seg-social.pt, iefp.pt, portais `.gov.pt`.
3. **Condicional sempre**: "poderás ter direito SE cumprires A e B" — nunca assertivo sobre o caso pessoal do leitor.
4. **Nunca copiar** texto de bancos, jornais ou agregadores — reescrever sempre.
5. **Data em cada facto**: "Verificado a [data] · Fonte: [link]".
6. **Disclaimer** de independência em todas as páginas (`Aviso de independência`).
7. **JSON-LD** FAQPage/HowTo em todas as páginas de conteúdo.
8. **Dúvidas frequentes** com `<details>`/`<summary>` e classe `.zona-cinzenta`.
9. **Long-tail**: responder às "zonas cinzentas" que os portais oficiais não respondem directamente (ex: trabalhadores independentes, mudança de escalão a meio do ano, cumulação de apoios).
10. **Independência declarada**: sem imitar o Estado, sem logótipos oficiais.

### Não fazer
- Não usar Jekyll ou qualquer SSG
- Não apagar `CNAME` nem `.nojekyll`
- Não publicar sem fonte datada
- Não dar veredictos pessoais ("tu tens direito a X")
- Não inventar emails — usar link GitHub Issues para contacto
- Não usar subpaths de portais sem confirmar que devolvem 200

---

## ESTRUTURA HTML OBRIGATÓRIA POR PÁGINA

Ordem no `<head>`:
1. `<meta charset="UTF-8">`
2. CookieYes script
3. GA4 script (`G-XP46PM8H1Q`)
4. favicon, viewport, title, description
5. OG tags: `og:title`, `og:description`, `og:url`, `og:type`, `og:locale`, `og:site_name`
6. JSON-LD: `FAQPage` + `HowTo` + `BreadcrumbList`

Conteúdo obrigatório no `<body>`:
- `"Verificado a [data]"` visível
- Disclaimer com texto `"Aviso de independência"`
- Fontes com links para portais oficiais

---

## AGENTES DISPONÍVEIS

**Commands** (`.claude/commands/`) — invocar com `/nome`:
- `/publicar-pagina` — pipeline completo: scrape → validar → gerar HTML → auditar links → commit
- `/verificar-fontes` — audita todos os links de todas as páginas publicadas
- `/nova-noticia` — lê RSS, selecciona notícia relevante, actualiza noticias.html
- `/atualizar-cluster-psu` — executa o plano de acção da Issue do decreto-lei PSU, com confirmação obrigatória dos valores antes de tocar em ficheiros

**Skills** (`.claude/skills/`) — usadas internamente:
- `estrutura-pagina` — template HTML com as secções obrigatórias e JSON-LD pronto a preencher
- `verificar-url` — testa se um URL existe e devolve acção correcta (200/403/404/timeout)

---

## SISTEMA DE CLUSTERS — ARQUITECTURA DE INFORMAÇÃO

Reorganização da navegação do site por clusters temáticos, em curso desde
2026-07-02. Mesmo princípio do botão de partilha: **"automático" = script
Python idempotente, corrido em sessão manual, que injecta HTML estático
entre marcadores** — nunca fetch de JSON no browser, nunca SSG.

1. **`data/clusters.json`** — fonte única de verdade: cada cluster tem
   `id`, `nome`, `descricao_curta`, `icone`, `pillar` (URL da página
   agregadora), `paginas[]` (`slug`/`titulo`/`tipo`/`destaque`) e
   `relacionados[]` (ids de outros clusters, usados como 2.º nível nas
   sugestões de "relacionados").
2. **`scripts/sincronizar_clusters.py`** — idempotente, `--dry-run`
   disponível. Injecta HTML só entre estes marcadores; se um marcador
   não existir numa página que devia tê-lo, reporta e não altera nada:
   - `<!-- CLUSTERS:HOME:INICIO/FIM -->` — cartões de clusters no `index.html`
   - `<!-- DESTAQUES:HOME:INICIO/FIM -->` — um cartão por cluster (o(s) `destaque: true`), no `index.html`
   - `<!-- ATUALIZACOES:HOME:INICIO/FIM -->` — 3-4 artigos mais recentemente verificados (data real extraída de "Verificado a ..." em cada página, nunca inventada), no `index.html` — ver secção "FRESCURA DA HOMEPAGE"
   - `<!-- CLUSTER-BADGE:INICIO/FIM -->` — breadcrumb visível + "este artigo pertence ao guia X", num artigo
   - `<!-- RELACIONADOS:INICIO/FIM -->` — secção final de artigos relacionados, num artigo
   - `<!-- PILLAR-LISTA:INICIO/FIM -->` — lista de artigos do cluster, numa pillar page
   Também corre `validar_consistencia()`: reporta páginas do JSON sem
   ficheiro, pillars por criar, e ficheiros HTML sem entrada no JSON
   (fora da lista `EXCLUIDAS`: `index.html`, `noticias.html`,
   `comecar-aqui.html`, `sobre.html`, `fontes.html`, `privacidade.html`,
   `404.html`).
3. **Regras de relevância para "relacionados"** (determinísticas, sem
   aleatoriedade, máx. 4 links): 1.º irmãos do mesmo cluster, 2.º
   páginas dos `relacionados[]` explícitos do cluster.
4. **Clusters actuais — todos os 5 pillars existem:**

   | Cluster | Pillar |
   |---|---|
   | Apoios Escolares | `p/apoios-escolares.html` |
   | Prestação Social Única | `prestacao-social-unica.html` |
   | Família e Crianças | `p/familia.html` |
   | Idosos, Incapacidade e Cuidadores | `p/idosos-incapacidade-cuidadores.html` (inclui `amim.html`) |
   | Trabalho e Rendimento | `p/trabalho-rendimento.html` |

   Todos os pillars têm a lista de artigos entre `<!-- PILLAR-LISTA:INICIO/FIM -->`,
   gerada pelo `sincronizar_clusters.py` — nunca editar essa lista à mão.

5. **Testes**: `tests/test_sincronizar_clusters.py` — idempotência,
   marcador em falta, página no JSON sem ficheiro, ficheiro sem entrada
   no JSON, contagem por tipo. `tests/test_breadcrumb_coerencia.py` —
   corre sobre os artigos **reais** do repositório (não fixtures) e
   compara o breadcrumb visível com o JSON-LD `BreadcrumbList` de cada
   um: falha se o nome/URL do cluster ou a página final divergirem.
   Necessário porque o `BreadcrumbList` é editado à mão (formato varia
   por artigo) — é a rede de segurança contra esse trabalho manual.
6. **Ferramentas (simuladores) não recebem `CLUSTER-BADGE`/`RELACIONADOS`.**
   `simulador-abono.html` e `simulador-ase.html` são páginas-membro do
   respectivo cluster (aparecem no `PILLAR-LISTA` e contam para
   "guias · simuladores" nos cartões da homepage) mas usam um hero
   claro (fundo branco), incompatível com o texto branco do
   `clusters.css` (pensado para o hero escuro `#0F766E` dos artigos).
   Decisão: só páginas `tipo: "artigo"` ganham navegação contextual.
   Ficam sinalizadas no `PILLAR-LISTA` com um badge discreto
   ("Ferramenta", classe `.badge` já existente em todas as pillar
   pages) para se distinguirem visualmente dos guias — ver secção
   "NAVEGAÇÃO PRINCIPAL" / distinção Guias-Ferramentas da Fase 5.
   *Registado para o futuro*: se um dia se quiser dar navegação
   contextual também às ferramentas, a via é criar uma variante clara
   de `clusters.css` (texto escuro) em vez de forçar o hero escuro
   nos simuladores — não decidido, sem prazo.

**Estado actual (Fases 1 a 5 concluídas):** fundação de dados pronta,
os 5 pillars existem com a lista de artigos sincronizada (com badge
"Ferramenta" nas páginas `tipo: "ferramenta"`), a `index.html` está
reorganizada por clusters, e os 15 artigos (todos os `tipo: "artigo"`
de `clusters.json`) têm breadcrumb visível + "pertence ao guia" +
secção de relacionados, sincronizados com o `BreadcrumbList` de cada
um (`tests/test_breadcrumb_coerencia.py` confirma consistência nos
15). Ao aplicar, foram removidos blocos manuais antigos de "artigos
relacionados" (classe `.cluster-escolar`) em 14 desses artigos —
vários já apontavam para o cluster errado (ex.: `amim.html` ainda
linkava para `prestacao-social-unica.html`; `cuidador-informal.html`
e `complemento-solidario-idosos.html` linkavam-se um ao outro apesar
de estarem hoje em clusters diferentes). Ver o commit da Fase 3
Etapa B para a lista completa por ficheiro. Fase 5 fechou o projecto
com UX (espaçamento, distinção Guias/Ferramentas, touch targets) e
SEO/integridade (JSON-LD, links, sitemap, pesquisa) — ver secção
"FECHO DO PROJECTO" para o resumo completo.

---

## NAVEGAÇÃO PRINCIPAL (Fase 4)

Nav única em todas as 29 páginas, gerada a partir de `data/clusters.json`
e injectada entre `<!-- NAV:INICIO -->` / `<!-- NAV:FIM -->` por
`scripts/sincronizar_nav.py`. Estrutura: **Logo | Apoios ▾ (5 clusters,
pelos pillars) | Começa aqui | Notícias | Pesquisa**. "Guias" saiu
(redundante com "Apoios ▾"), os simuladores saíram da nav (vivem nos
clusters e na homepage), "Sobre" ficou só no footer (já estava em
todas as páginas).

1. **`scripts/sincronizar_nav.py`** — duas fases:
   - *Bootstrap* (uma vez por página): detecta a nav antiga com 2
     heurísticas — `<div class="nav-wrap">...</div>` autocontido, ou
     `<header>...</header>` + `<div class="mobile-menu">...</div>`
     opcional a seguir. **Recusa sempre** tocar num `<header>` que
     contenha um `<h1>` (estrutura atípica — arriscaria apagar
     conteúdo do artigo); nesse caso a página fica para intervenção
     manual antes de voltar a correr o script.
   - *Sincronização* (idempotente): com os marcadores já presentes,
     regenera só o interior.
2. **`assets/css/nav.css`** + **`assets/js/nav.js`** — nav e
   interacção (dropdown "Apoios", hamburger, fecho ao clicar fora)
   partilhados por todas as páginas; elimina o JS inline duplicado
   (e ligeiramente diferente) que existia página a página.
3. **`scripts/pesquisa.js`** — `mostrarResultados()` recebe um 3.º
   parâmetro opcional (id do contentor de resultados), o que permite
   pesquisa na nav e no hero do `index.html` em simultâneo, com ids
   distintos (`campo-pesquisa-nav`/`resultados-pesquisa-nav` na nav;
   `campo-pesquisa`/`resultados-pesquisa` reservados ao hero do
   `index.html`).
4. **`404.html` tem a nav completa (dropdown + pesquisa) — decisão
   deliberada**, não descuido: é exactamente onde um utilizador
   perdido mais precisa de saídas para continuar a navegar.
5. **Nenhuma página perdeu pontos de entrada.** As 7 páginas que
   antes tinham "Por onde começar?" no fim do menu (em vez de "Começa
   aqui") apontavam todas para o mesmo `/comecar-aqui.html` — a nova
   nav cobre esse caminho com "Começa aqui", mesmo destino.
6. **`simulador-ase.html` foi restruturado antes do bootstrap**
   (commit à parte): era a única página do repositório com o `<h1>`
   dentro do `<header>` — o título, o botão de partilha e o subtítulo
   passaram para uma `<section class="hero">` própria, como em
   `simulador-abono.html`. O estilo teal saiu de `header{}` e entrou
   em `.hero{}`.
7. **Testes**: `tests/test_nav_coerencia.py` corre sobre as 29
   páginas reais e confirma: exactamente 1 bloco `NAV` por página,
   zero resíduos da nav antiga (classes/ids/handlers antigos),
   referências a `nav.css`/`nav.js`/`pesquisa.js` presentes, e o
   dropdown "Apoios" + pesquisa (desktop e mobile) + "Começa aqui"
   presentes dentro do bloco.

**Dívida técnica conhecida (fora do âmbito da Fase 4, ainda por resolver):**
- CSS morto: as regras da nav antiga (`.mobile-menu`, `.hamburger`,
  `.nav-mobile-sim-label`, etc.) continuam nos `<style>` de cada
  página — inofensivas (nada as usa) mas não foram removidas, para
  manter o diff desta fase pequeno. *Registado para o futuro*: limpeza
  cosmética, sem prazo, sem risco.

Dois achados sinalizados no fecho da Fase 4 (não relacionados com o
ponto acima) — JSON-LD inválido em `simulador-ase.html` e OG
tags/disclaimer em falta nas páginas institucionais — **foram
corrigidos na Fase 5** — ver secção "PÁGINAS INSTITUCIONAIS" e o
commit de correcções da Fase 5.

---

## PÁGINAS INSTITUCIONAIS — OG tags e disclaimer

Decisão tomada página a página na Fase 5, sem alterar nenhum facto:

| Página | OG tags | Disclaimer "Aviso de independência" | Justificação |
|---|---|---|---|
| `404.html` | ✅ adicionado | ❌ dispensado, deliberado | Página de erro, `robots: noindex`, sem conteúdo editorial — nada a desmentir |
| `sobre.html` | ✅ adicionado | ✅ adicionado | Página institucional com afirmações sobre o projecto |
| `fontes.html` | ✅ adicionado | ✅ adicionado | Lista fontes oficiais — disclaimer reforça que a lista é informativa |
| `privacidade.html` | ✅ adicionado | ✅ adicionado | Consistência com as restantes páginas institucionais |
| `comecar-aqui.html` | já existia | ✅ adicionado | O teste sugere apoios com base nas respostas — é orientação, precisa do aviso |

`simulador-ase.html`: corrigido o JSON-LD inválido (dois objectos JSON
no mesmo `<script>`, sem `[...]`) — passou a dois `<script>` separados,
mesmo padrão usado noutras páginas com múltiplos tipos JSON-LD.

---

## FECHO DO PROJECTO — REORGANIZAÇÃO DA ARQUITECTURA DE INFORMAÇÃO (Fases 0-5)

Projecto concluído a 2026-07-02. Visão geral consolidada — as secções
"SISTEMA DE CLUSTERS", "NAVEGAÇÃO PRINCIPAL" e "PÁGINAS INSTITUCIONAIS"
acima têm o detalhe; esta secção é o mapa completo e o resumo de fecho.

### Arquitectura final, num relance

Duas fontes de verdade em `data/`, dois scripts idempotentes que
injectam HTML estático entre marcadores — nunca fetch de JSON no
browser, nunca SSG, mesmo princípio do `inserir_botao_partilhar.py`:

| Fonte de verdade | Script sincronizador | Marcadores que possui |
|---|---|---|
| `data/clusters.json` | `scripts/sincronizar_clusters.py` | `CLUSTERS:HOME`, `DESTAQUES:HOME`, `CLUSTER-BADGE`, `RELACIONADOS`, `PILLAR-LISTA` |
| `data/clusters.json` (reaproveitado) | `scripts/sincronizar_nav.py` | `NAV:INICIO`/`NAV:FIM` |

Ambos: `--dry-run` disponível, correm sobre as páginas reais (não
fixtures), 2.ª corrida = zero alterações (idempotência confirmada em
todo o repositório nesta sessão de fecho), e recusam-se a alterar uma
página se o marcador esperado não existir — nunca inventam estrutura.

CSS/JS partilhados que resultaram deste projecto:
`assets/css/clusters.css` (breadcrumb/pertence/relacionados),
`assets/css/nav.css` + `assets/js/nav.js` (nav principal única).

Checklist de publicação (secção "CHECKLIST OBRIGATÓRIA") já inclui os
passos dos dois scripts — nenhuma página nova deve ser publicada sem
correr ambos.

### O que mudou, fase a fase

- **Fase 0** — inventário do estado existente (29 páginas, 7 estruturas
  de nav distintas, nenhuma arquitectura de clusters) antes de tocar
  em qualquer ficheiro.
- **Fase 1 (+ 1b)** — fundação de dados: `data/clusters.json` (5
  clusters) e `scripts/sincronizar_clusters.py`; criadas as 3 pillar
  pages em falta (`p/familia.html`, `p/idosos-incapacidade-cuidadores.html`,
  `p/trabalho-rendimento.html`), adiantadas porque as fases seguintes
  já precisavam de linkar para elas.
- **Fase 2** — homepage reorganizada por clusters: hero com pesquisa,
  "Comece por aqui", cartões de cluster, guias principais em destaque,
  como funciona, prazos, notícia do dia.
- **Fase 3** — navegação contextual nos 15 artigos (breadcrumb visível
  + "pertence ao guia" + relacionados), com limpeza de 14 blocos
  manuais desactualizados que já apontavam para clusters errados.
- **Fase 4** — nav principal única nas 29 páginas via
  `sincronizar_nav.py`, com `simulador-ase.html` restruturado à parte
  (único `<h1>` dentro de `<header>` do repositório).
- **Fase 5** — fecho: correcção dos 2 achados pendentes da Fase 4
  (JSON-LD de `simulador-ase.html`, OG/disclaimer institucionais); UX
  (espaçamento entre secções, badge "Ferramenta" nas pillar lists,
  touch targets ≥44px em chips/dropdown/menu); SEO/integridade
  verificados nas 29 páginas sem amostragem (JSON-LD válido, zero
  links internos partidos, sitemap completo, `pesquisa.js` com
  cobertura de 27/27 páginas elegíveis); esta secção de fecho.

### Decisões tomadas que vale a pena lembrar

- Ferramentas (simuladores) ficam de fora da navegação contextual
  (`CLUSTER-BADGE`/`RELACIONADOS`) por incompatibilidade de hero
  claro/escuro — recebem apenas um badge "Ferramenta" no `PILLAR-LISTA`.
- `404.html` tem nav completa (decisão deliberada) mas não tem
  disclaimer (também deliberado — página de erro sem conteúdo
  editorial).
- `pesquisa.js` mantém-se lista manual, não gerada a partir de
  `clusters.json` — o ficheiro cobre pillars e páginas institucionais
  que não estão no JSON de clusters; gerar automaticamente exigiria
  primeiro unificar as duas fontes, fora do âmbito desta reorganização.

### Registado para o futuro (sem prazo, sem decisão tomada)

1. **Densidade da PSU na homepage** — reduzir dos 6 pontos actuais
   quando o tema arrefecer após o decreto-lei (ver secção "IMPACTO DA
   PSU", plano de acção, ponto 7 — candidatos: banner do topo e
   cartão de prazos).
2. **Variante clara de `clusters.css`** — se um dia se quiser dar
   breadcrumb/relacionados também aos simuladores, criar uma variante
   de texto escuro em vez de forçar hero escuro nas ferramentas (ver
   secção "SISTEMA DE CLUSTERS", ponto 6).
3. **CSS morto da nav antiga** — limpeza cosmética nos `<style>`
   de cada página (ver secção "NAVEGAÇÃO PRINCIPAL", dívida técnica).

---

## FRESCURA DA HOMEPAGE — NOTÍCIAS E ATUALIZAÇÕES

Reformulação de 2026-07-02: o antigo bloco "Notícia do dia" no
`index.html` era HTML estático desde 25/06 — nenhum script alguma vez
lhe tocava (confirmado por diagnóstico antes de mexer: `noticias.html`,
esse sim, já era actualizado diariamente pelo pipeline desde
2026-06-30, com título/link/data a mudar de facto a cada corrida —
só a homepage é que nunca reflectia isso). A homepage passou a ter
**duas fontes de frescura, ambas automáticas e nenhuma inventa datas**:

### A) "Últimas notícias" — `gerar_noticias.py` + `NOTICIA-HOME:INICIO/FIM`

Mesma notícia escolhida por `best_entry()` (a que já vai para
`noticias.html`) passa também a ser injectada no `index.html`, entre
`<!-- NOTICIA-HOME:INICIO/FIM -->`, por `render_noticia_home()` +
`atualizar_index_home()`. Mostra sempre a data real da notícia (nunca
"hoje") e liga directamente à fonte externa (nunca um link interno
inventado). Se o RSS não devolver nada relevante nesse dia,
`main()` termina antes de chamar `atualizar_index_home()` — o bloco
mantém a última notícia real publicada, nunca um `[VAZIO]` nem uma
data adivinhada.

**Guardrail estendido** (mudança de segurança): `escrever_ficheiro_seguro()`
em `gerar_noticias.py` passou de "só `noticias.html`" para "`noticias.html`
(livre) ou `index.html` (só dentro de `NOTICIA-HOME:INICIO/FIM`)".
`_verificar_escrita_confinada()` compara o ficheiro em disco com o novo
conteúdo fora da secção marcada — qualquer diferença aí, ou o marcador
não existir, bloqueia a escrita com excepção. Coberto por
`tests/test_gerar_noticias_guardrail.py` (escrita livre em
`noticias.html`, bloqueio a qualquer outro HTML, escrita permitida
dentro do marcador, bloqueio fora do marcador, bloqueio se o marcador
não existir, idempotência de `atualizar_index_home()`).

### B) "Atualizado recentemente" — `sincronizar_clusters.py` + `ATUALIZACOES:HOME:INICIO/FIM`

3-4 artigos com o "Verificado a ..." mais recente (extraído do corpo
real de cada página `tipo: "artigo"`, nunca do RSS, nunca inventado) —
sempre verdadeiro por construção, porque reflecte edições reais do
site. `extrair_verificado_em()` aceita os 3 formatos usados nos
artigos publicados (`DD/MM/AAAA`, "D de mês de AAAA", "D mês AAAA") e
usa sempre a **última** ocorrência no ficheiro (a mais próxima do
bloco de fontes no fim do corpo — as anteriores são notas por secção).
Ordem determinística: data decrescente, slug como desempate — nunca
aleatória, para a saída ser idempotente. Escrito por
`scripts/sincronizar_clusters.py` (script de **sessão manual**, não do
pipeline automático — ver "REGRA DE OURO").

**Posição na homepage**: logo a seguir a "Guias principais"
(`DESTAQUES:HOME`) e antes de "Como funciona" — a leitura mais literal
de "depois dos destaques, antes dos prazos" (⏰ "Datas a não perder" é
a secção `urgente-banda`, mais abaixo).

### Regra de honestidade

Nenhum dos dois blocos mostra alguma vez "hoje" ou uma data inventada.
Se uma fonte falhar (RSS sem itens relevantes, ou um artigo sem
"Verificado a" reconhecível), o bloco correspondente simplesmente não
é actualizado nessa corrida — mantém o último conteúdo real. Zero
factos de memória, mesma regra do resto do site.

### Fontes RSS — estado a 2026-07-02

`gerar_noticias.py` usa 4 feeds: 3 pesquisas Google News (`apoios
sociais portugal`, `segurança social portugal`, `IRS subsidios
portugal 2026`) e `https://dre.pt/rss/dr1s.rss`. Este último já está
documentado como inacessível nos runners GitHub (ver "FONTES
VERIFICADAS", linha DRE) — na prática só as 3 pesquisas Google News
alimentam a selecção. Não foi possível testar os feeds ao vivo nesta
sessão (política de rede do ambiente bloqueia `news.google.com` e
`dre.pt` fora da lista de domínios permitidos); a avaliação de cadência
baseia-se no histórico real de commits a `noticias.html`: conteúdo
genuinamente diferente (título/link/data) em cada corrida do pipeline
desde 2026-06-30, o que indica feeds populados. Ressalva: `best_entry()`
escolhe por pontuação de palavras-chave, não por recência — a data
mostrada é a data real do artigo escolhido, que por isso pode
ocasionalmente recuar face ao dia anterior (Google News reapresenta
artigos mais antigos nos resultados de pesquisa). É esperado e correcto
por desenho — nunca é uma data inventada, só nem sempre é a mais
recente possível. *Registado para o futuro*: decidir se vale a pena
remover o feed DRE morto e/ou acrescentar fontes com cadência mais
previsível — não decidido, sem prazo.

---

## AUTO-ACTUALIZAÇÃO DESTE FICHEIRO

Sempre que houver mudança significativa, actualizar o CLAUDE.md no mesmo commit.

Triggers obrigatórios de actualização:
- Alteração a `.github/workflows/`
- Alteração a `scripts/`
- Adição ou remoção de página HTML publicada
- Mudança nas regras de conteúdo ou de links
- Mudança na stack (novos serviços, remoção de dependências)

---

---

## PÁGINAS COM DATAS SAZONAIS

Páginas que têm datas que expiram e precisam de revisão manual anual:

| Página | Data a rever | Trigger |
|---|---|---|
| `manuais-escolares-mega.html` | Julho (datas MEGA) | Issue automática do scraper |
| `acao-social-escolar.html` | Setembro (prazo ASE) | Calendário anual |
| `bolsa-de-merito.html` | Setembro (prazo bolsa) | Calendário anual |
| `abono-de-familia.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `rsi.html` | Janeiro (novo IAS/RSI) | Issue automática do scraper |
| `complemento-solidario-idosos.html` | Janeiro (novo valor CSI) | Issue automática do scraper |
| `prestacao-social-unica.html` | Ago 2026 (decreto-lei) + Jan 2027 (entrada vigor) | Verificação manual/news dre.pt |
| `psu-quando-entra-em-vigor.html` | Ago 2026 (decreto-lei) + Jan 2027 (entrada vigor) | Verificação manual/news dre.pt |
| `psu-quem-tem-direito.html` | Ago 2026 (valores confirmados pelo decreto-lei) | Decreto-lei publicado |
| `subsidio-desemprego.html` | Janeiro (novos limites) | Issue automática do scraper |
| `subsidio-parental.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `amim.html` | Janeiro (novo IAS: afeta IRS 4×/2,5×IAS e valor PSI) | Issue automática do scraper |

---

## IMPACTO DA PSU (Prestação Social Única)

Estado: aprovada parlamento 25/06/2026.
Aguarda: decreto-lei com valores + publicação DR.
Prazo PRR decreto-lei: 31 ago 2026.
Entrada em vigor para beneficiários: 1 jan 2027 (texto inicial, não confirmado pelo decreto-lei).
Cluster publicado: 1 jul 2026 (pillar + 4 páginas filhas).

### Páginas NÃO afectadas pela PSU

Estas páginas mantêm-se inalteradas — os subsistemas/apoios são explicitamente excluídos do âmbito da PSU:

- `abono-de-familia.html` — subsistema familiar (excluído)
- `acao-social-escolar.html` — educação (excluído)
- `bolsa-de-merito.html` — educação (excluído)
- `manuais-escolares-mega.html` — educação (excluído)
- `passe-sub23.html` — transporte (excluído)
- `complemento-solidario-idosos.html` — CSI explicitamente excluído (confirmado audição parlamentar)
- `simulador-abono.html` — ferramenta abono (excluído)
- `simulador-ase.html` — ferramenta ASE (excluído)

### Páginas com aviso PSU activo

Manter avisos de transição até DR publicado:

| Página | Absorção | Aviso |
|---|---|---|
| `rsi.html` | Absorvido integralmente | "RSI será absorvido pela PSU" |
| `subsidio-desemprego.html` | Só subsídio SOCIAL absorvido | "Subsídio SOCIAL absorvido; CONTRIBUTIVO não afectado" |
| `subsidio-parental.html` | Só apoios NÃO contributivos absorvidos | "Apoios não-contributivos absorvidos; contributivo mantém-se" |

### Cluster PSU — páginas em espera (NÃO criar ainda)

| Página | Gatilho para escrever |
|---|---|
| `como-pedir-psu.html` | Decreto-lei da PSU publicado em dre.pt com procedimento definido |
| `calendario-pagamentos-psu.html` | Decreto-lei da PSU publicado em dre.pt com valores e datas |

### Plano de acção (quando DR for publicado)

1. Actualizar `prestacao-social-unica.html` com valores reais do decreto-lei
2. Actualizar `psu-quando-entra-em-vigor.html` e `psu-quem-tem-direito.html` com valores confirmados
3. Criar `como-pedir-psu.html` e `calendario-pagamentos-psu.html`
4. Transformar `rsi.html` em página de transição RSI→PSU com redirecionamento interno
5. Actualizar avisos em `subsidio-desemprego.html` e `subsidio-parental.html`
6. **NUNCA apagar páginas antigas** — redirecionar para PSU via links internos para evitar 404s
7. Quando o tema arrefecer (algumas semanas depois do decreto-lei):
   reduzir a densidade da PSU na homepage — hoje aparece 6×
   (banner `DESTAQUE:INICIO/FIM`, cartão "Comece por aqui", cartão de
   cluster, cartão de destaque, cartão de prazos, notícia do dia).
   Candidatos a remover primeiro: o banner do topo e o cartão de
   prazos — os outros 4 continuam a fazer sentido como navegação
   permanente do cluster.
8. Actualizar `descricao_curta` do cluster `prestacao-social-unica` em `data/clusters.json`
   (deixa de dizer "ainda não em vigor — aguarda decreto-lei") e correr
   `python scripts/sincronizar_clusters.py` para propagar a mudança ao cartão da
   homepage e a qualquer bloco "pertence ao guia" já injectado nos artigos do cluster

---

## GSTACK

Skills disponíveis via gstack instalado globalmente.

### Instalação (ambiente local)

```bash
git clone --single-branch --depth 1 \
  https://github.com/garrytan/gstack.git \
  ~/.claude/skills/gstack \
  && cd ~/.claude/skills/gstack \
  && ./setup

# Desactivar telemetria
gstack-config set telemetry off
```

### Skills relevantes para este projecto

- **`/design-html`** — gerar infografias e calculadoras em HTML com design de alta qualidade
- **`/browse`** — navegação com anti-bot stealth (substitui Playwright quando bloqueado)
- **`/qa`** — revisão de qualidade antes de publicar páginas
- **`/review`** — revisão de código e HTML gerado
- **`/careful`** — modo seguro para edições críticas em páginas de conteúdo

**Usar `/browse` em vez de Playwright/mcp__claude-in-chrome__* tools quando o site-alvo tem proteção anti-bot.**

### Skills NÃO relevantes para este projecto (não usar)

- `/office-hours`, `/plan-ceo-review` — gestão startup (não aplicável)
- `/land-and-deploy` — deploy já é via GitHub Pages (não precisa)
- `/setup-gbrain` — base de dados (não usamos)

### Telemetria

Desactivada globalmente via `gstack-config set telemetry off`.

---

## SEGURANÇA — PROMPT INJECTION EM DADOS IMPORTADOS

`scripts/verificar_injecao.py` — guardrail permanente, corrido em
`integridade.yml` (push a main, cron semanal, manual). Procura, em
`data/` e `shadow_history/`, frases multi-palavra associadas a prompt
injection (`system-reminder`, "ignore previous instructions", "não
contes ao utilizador", marcadores de chat tipo `<|system|>`, etc.) —
nunca palavras soltas, para não gerar falsos positivos com vocabulário
legítimo em português (ex.: "instrumento", "verificado", "confidencial"
aparecem em texto legal/institucional real). Só lê e reporta — nunca
executa, interpreta nem apaga o conteúdo que encontra; falha
(`exit 1`) sem tocar em nenhum ficheiro. Testado em
`tests/test_verificar_injecao.py`.

Justificação: o pipeline ingere conteúdo externo todos os dias
(scraper Playwright em `data/scraped/`, feeds RSS via
`gerar_noticias.py`) — é a única categoria de dados no repositório que
vem de fora do controlo do projecto.

Origem: investigação de 2026-07-02 a um `<system-reminder>` suspeito
recebido num resultado de ferramenta numa sessão anterior (a instruir
a IA a ocultar uma alteração e a confiar em conteúdo divergente do
disco). Busca exaustiva a todos os ficheiros trackeados, a
`data/scraped/`, a `shadow_history/` e ao log do scraper não encontrou
nenhum vestígio desse texto no repositório nem no histórico git — a
conclusão foi que o aviso não veio de conteúdo importado, mas sim de
um artefacto do próprio harness (não ficou confirmado com certeza
absoluta). Ainda assim, este guardrail fica como protecção permanente
daqui para a frente, independentemente da causa desse incidente
específico.

---

## SHADOW MODE — SISTEMA DE OBSERVAÇÃO (deteção de datas expiradas)

Camadas incrementais construídas sobre `verificar_datas.py`, todas com testes
próprios em `tests/`. Cada uma só faz a sua parte — nenhuma decide sozinha se
uma Issue é criada ou um valor é alterado:

1. **Deteção** (`verificar_datas.py`) — encontra datas/valores potencialmente
   expirados em cada HTML; continua a ser a única coisa que gera
   `data/alertas_datas.json` e as Issues `data-expirada` do `pipeline-diario.yml`.
2. **Classificação** (`classificar_datas.py`) — `EstadoData`: `OK`,
   `OUTDATED_AUTOFIXABLE`, `OUTDATED_REVIEW_REQUIRED`, `STATIC_REFERENCE`,
   `BLOCKED_SOURCE`.
3. **Decisão** (`decisao_datas.py`) — estado → acção (`IGNORAR`/`LOG_ONLY`/
   `CREATE_ISSUE`/`AUTO_UPDATE`). `AUTO_UPDATE_HABILITADO = False` — **nunca
   mudar isto sem decisão explícita e revisão de segurança à parte**.
4. **Auto-update engine** (`auto_update_engine.py`) — sandbox: só actua em
   memória, nunca escreve ficheiros; nunca chamado directamente por outro
   módulo além do orquestrador.
5. **Orquestrador** (`orquestrador_datas.py`) — único ponto autorizado a
   chamar a Camada 4; falha sempre para `LOG_ONLY` em caso de erro inesperado.
6. **Source adapter** (`source_adapter.py`) — providers ainda placeholder
   (Segurança Social, IEFP, DGE, Diário da República); nunca inventa valores.
7. **Shadow Mode** (`shadow_mode.py` + `shadow_mode_analytics.py` +
   `shadow_report_md.py`) — corre a cadeia inteira em modo observação pura e
   produz um relatório humano em Markdown, sem qualquer efeito real.
8. **Execução diária** (`run_shadow_daily.py` + `.github/workflows/shadow-daily.yml`,
   cron `0 3 * * *`) — liga os três módulos da Camada 7 e guarda 1 relatório/dia
   em `shadow_history/shadow_report_AAAA-MM-DD.md`. Guardrail próprio no
   workflow recusa (sem commitar) qualquer alteração fora de `shadow_history/`
   ou qualquer ficheiro de histórico apagado.

**Estado actual: sistema 100% observacional.** Nenhuma camada activa
auto-update real, nenhuma cria/fecha Issues por si própria, nenhuma escreve
HTML. Antes de alguma vez pôr `AUTO_UPDATE_HABILITADO = True`: rever
`shadow_history/` com dados reais acumulados, confirmar que os providers do
`source_adapter` já devolvem valores reais (não só placeholders) e fazer essa
mudança numa sessão manual dedicada, nunca de ânimo leve.

---

*Última revisão: 2026-06-28 — CSI e PSU publicadas; fact-checking completo; GSTACK adicionado; PSU destaque; datas sazonais; simulador abono (fix múltiplas crianças); simulador ASE completo; plano impacto PSU documentado*

---

*Última revisão: 2026-07-01 — corrigido bug de dedup em `pipeline-diario.yml` que gerava Issues duplicadas (data-expirada, fonte-bloqueada, fonte-alterada, divergências de valores); 8 Issues duplicadas fechadas*

---

*Última revisão: 2026-07-02 — investigado um `<system-reminder>` suspeito recebido numa sessão anterior; busca exaustiva ao repositório (186 ficheiros trackeados, `data/scraped/`, `shadow_history/`, log do scraper) não encontrou nenhum vestígio de prompt injection — conclusão: artefacto do harness, não conteúdo importado; adicionado guardrail permanente `scripts/verificar_injecao.py` (procura padrões de injection em `data/` e `shadow_history/`, só leitura, nunca executa o que encontra) + novo job em `integridade.yml`; nova secção "SEGURANÇA — PROMPT INJECTION EM DADOS IMPORTADOS"; 9 testes novos em `tests/test_verificar_injecao.py`, 409 testes a passar*

---

*Última revisão automática: 2026-07-02*

---

*Última revisão: 2026-07-01 — criado sistema reutilizável de botão "Partilhar este artigo" (`assets/js/share.js`, `assets/css/share.css`, `scripts/inserir_botao_partilhar.py`, idempotente, sem bibliotecas externas); aplicado às 23 páginas de conteúdo manuais (excepto `index.html`/`noticias.html`/`404.html`)*

---

*Última revisão: 2026-07-01 — criado `shadow-daily.yml` (cron `0 3 * * *`, push restrito a `shadow_history/*.md`, guardrail próprio); documentado o subsistema Shadow Mode completo (Camadas 2-8: classificação, decisão, auto-update engine sandbox, orquestrador, source adapter, Shadow Mode + analytics + relatório Markdown, execução diária); actualizada tabela de workflows (5, 2 com push, âmbitos disjuntos)*

---

*Última revisão: 2026-07-02 — Fase 0+1 da reorganização de arquitectura de informação: corrigida tabela "PÁGINAS PUBLICADAS" (faltavam 7 páginas) e contagem do `pesquisa.js` (21, não 6); criado `data/clusters.json` (5 clusters: Apoios Escolares, Prestação Social Única, Família e Crianças, Idosos/Incapacidade/Cuidadores, Trabalho e Rendimento — AMIM integrado no cluster de incapacidade) e `scripts/sincronizar_clusters.py` idempotente com `--dry-run`, testado em `tests/test_sincronizar_clusters.py`; nova secção "SISTEMA DE CLUSTERS"; nenhuma página HTML alterada ainda (Fases 2-5 por fazer)*

---

*Última revisão: 2026-07-02 — criadas as 3 pillar pages em falta (`p/familia.html`, `p/idosos-incapacidade-cuidadores.html`, `p/trabalho-rendimento.html`), adiantadas da Fase 4 porque a Fase 2/3 já precisam de linkar para elas; checklist completa (GA4, JSON-LD, disclaimer, "Verificado a", botão partilhar) e conteúdo sourced só de factos já publicados nos artigos-filho; retrofit do marcador `PILLAR-LISTA` em `p/apoios-escolares.html` e `prestacao-social-unica.html`; `sincronizar_clusters.py` corrido com sucesso nos 5 pillars (idempotência confirmada); `sitemap.xml` e `scripts/pesquisa.js` (24 páginas) actualizados

---

*Última revisão: 2026-07-02 — Fase 2 (homepage): `index.html` reorganizada — hero com pesquisa (`#campo-pesquisa` movido da nav, chips de sugestão) → "Comece por aqui" (5 cartões por necessidade) → clusters (`CLUSTERS:HOME`) → guias principais (novo marcador `DESTAQUES:HOME`, um destaque por cluster) → como funciona → prazos → notícia do dia; `data/clusters.json` ganhou campos opcionais `emoji`/`desc` por página (só nas 5 páginas `destaque: true`, sourced dos cartões antigos/meta description já publicados); testado no browser (desktop + mobile, Playwright) sem erros de consola; idempotência confirmada

---

*Última revisão: 2026-07-02 — Fase 3 completa (navegação contextual nos artigos): novo `assets/css/clusters.css`; `sincronizar_clusters.py` ganhou `render_relacionados()` com dois blocos ("Outros artigos deste cluster" / "Pode também interessar"), `_garantir_clusters_css()` idempotente, e a regra de que só `tipo: "artigo"` recebe `CLUSTER-BADGE`/`RELACIONADOS` (ferramentas ficam de fora — hero incompatível); aplicado aos 15 artigos (`abono-de-familia.html` na Etapa A, os outros 14 na Etapa B); removidos 14 blocos manuais `.cluster-escolar` desactualizados (vários apontavam para clusters errados); `BreadcrumbList` de cada artigo actualizado à mão para 3 níveis (as 4 páginas do cluster PSU já estavam correctas); novo `tests/test_breadcrumb_coerencia.py` corre sobre os artigos reais e confirma consistência breadcrumb-visível ↔ JSON-LD nos 15; idempotência confirmada (2ª corrida = zero diff); 266 testes a passar

---

*Última revisão: 2026-07-02 — Fase 4 completa (nav principal única): nova secção "NAVEGAÇÃO PRINCIPAL"; `scripts/sincronizar_nav.py` (bootstrap com 2 heurísticas + sincronização idempotente), `assets/css/nav.css` e `assets/js/nav.js` partilhados por todas as páginas; `pesquisa.js` ganhou 3.º parâmetro opcional em `mostrarResultados()` para a pesquisa coexistir na nav e no hero do `index.html`; `simulador-ase.html` restruturado em commit à parte (único `<header>` com `<h1>` do repositório — passou para `<section class="hero">` própria); aplicado às 29 páginas (`rsi.html`+`index.html` na Etapa A, as outras 27 na Etapa B); `404.html` passa a ter nav completa por decisão deliberada; as 7 páginas com "Por onde começar?" mantêm o mesmo destino via "Começa aqui"; novo `tests/test_nav_coerencia.py` (116 casos) confirma 1 bloco NAV por página e zero resíduos da nav antiga; idempotência confirmada em todo o repositório; 382 testes a passar; flagged (não corrigido, fora do âmbito): JSON-LD inválido pré-existente em `simulador-ase.html`, e OG/JSON-LD/"Verificado a" em falta em `404.html`/`sobre.html`/`fontes.html`/`privacidade.html`/`comecar-aqui.html` (gaps anteriores à Fase 4)

---

*Última revisão: 2026-07-02 — Fase 5 bloco 1 (correcções): corrigido o JSON-LD inválido de `simulador-ase.html` (dois objectos no mesmo `<script>` sem `[...]` — passou a dois `<script>` separados); adicionadas OG tags a `404.html`/`sobre.html`/`fontes.html`/`privacidade.html`; adicionado disclaimer "Aviso de independência" a `sobre.html`/`fontes.html`/`privacidade.html`/`comecar-aqui.html` (não a `404.html`, decisão deliberada — página de erro sem conteúdo editorial, ver secção "PÁGINAS INSTITUCIONAIS"); corrigido `</main>` em falta em `fontes.html`

---

*Última revisão: 2026-07-02 — Fase 5 bloco 2 (UX): espaçamento entre secções da homepage (`<hr class="divider">` entre clusters/destaques e antes da notícia do dia); distinção visual Guias/Ferramentas via badge "Ferramenta" no `PILLAR-LISTA`, gerado por `render_pillar_lista()` em `sincronizar_clusters.py` (reaproveita a classe `.badge` já existente nas pillar pages — nada à mão); touch targets ≥44px em `.chip` (homepage), `.nav-dropdown-btn`/`.nav-dropdown-menu a`/`.nav-toggle`/`.nav-mobile-menu a` (`assets/css/nav.css`)

---

*Última revisão: 2026-07-02 — Fase 5 bloco 3 (SEO/integridade): verificado sem amostragem nas 29 páginas — JSON-LD válido em todas (3 institucionais sem JSON-LD por decisão, as restantes 26 válidas), zero links internos partidos, `sitemap.xml` completo (28 entradas, os 3 pillars novos confirmados, `404.html` correctamente excluído); `scripts/pesquisa.js` ganhou as 3 entradas em falta (`sobre.html`/`fontes.html`/`privacidade.html`), cobertura 24→27 de 27 páginas elegíveis (todas excepto `index.html`/`404.html`); mantida decisão de `pesquisa.js` como lista manual (cobre pillars e institucionais fora de `clusters.json`)

---

*Última revisão: 2026-07-02 — Fase 5 bloco 4 (docs) e fecho do projecto: nova secção "FECHO DO PROJECTO" com o mapa completo da arquitectura (fontes de verdade, scripts sincronizadores, marcadores), resumo fase a fase (0 a 5) e os 3 pontos registados para o futuro sem prazo (densidade da PSU na homepage, variante clara de `clusters.css` para os simuladores, limpeza do CSS morto da nav antiga); clarificada a frase ambígua sobre "os dois achados" na secção "NAVEGAÇÃO PRINCIPAL"; 382 testes a passar, idempotência de `sincronizar_clusters.py` e `sincronizar_nav.py` reconfirmada em todo o repositório — reorganização da arquitectura de informação (Fases 0-5) concluída*

---

*Última revisão: 2026-07-02 — "Notícia do dia" reformulada para "homepage sempre atual": diagnóstico confirmou que `noticias.html` já era actualizado diariamente pelo pipeline desde 2026-06-30, mas o bloco do `index.html` era 100% estático desde 25/06 e nenhum script lhe tocava; nova secção "FRESCURA DA HOMEPAGE — NOTÍCIAS E ATUALIZAÇÕES" documenta as duas fontes de frescura novas, ambas automáticas e sem datas inventadas — A) "Últimas notícias" via `gerar_noticias.py` + marcador `NOTICIA-HOME:INICIO/FIM`, com guardrail estendido (`escrever_ficheiro_seguro()` passa a aceitar `index.html` só dentro do marcador, testado em `tests/test_gerar_noticias_guardrail.py`); B) "Atualizado recentemente" via `sincronizar_clusters.py` + novo marcador `ATUALIZACOES:HOME:INICIO/FIM`, calculado a partir do "Verificado a" real de cada artigo (`extrair_verificado_em()`); actualizada a "REGRA DE OURO" com as três zonas de escrita agora existentes em `index.html`; feed RSS `dre.pt/rss/dr1s.rss` confirmado já documentado como inacessível nos runners GitHub — cadência real assente nas 3 pesquisas Google News; 400 testes a passar, idempotência de `sincronizar_clusters.py` reconfirmada*

---

*Última revisão: 2026-07-02 — corrigido `F401` em `tests/test_sincronizar_clusters.py` (import `render_home_cards` não usado, pré-existente desde a Fase 4 — passava despercebido porque o job "Qualidade Python (Ruff)" do `integridade.yml` estava a falhar desde o commit `06d62726` sem ninguém ter reparado); checklist obrigatória ganhou o bullet `ruff check scripts/ --select E,F,W --ignore E501 .` (mesmo comando do CI, incluindo a nota de que a `ruff-action` também varre `tests/` apesar do `scripts/` explícito) — é essa lacuna na checklist que explica o lint ter escapado a vários commits seguidos*
