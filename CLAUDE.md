# CLAUDE.md — Tens Direito

Instruções globais para o Claude Code neste repositório.
Ler sempre antes de qualquer tarefa.

---

## REGRA DE OURO — FICHEIROS AUTO-GERADOS vs MANUAIS

O pipeline automático (`pipeline-diario.yml`) só pode escrever em:
- `index.html` — actualização da data de verificação
- `noticias.html` — notícia do dia via RSS
- `CLAUDE.md` — data de revisão automática
- `README.md` — estado do repositório
- `data/scraped/*.json` — dados do scraper

**TODOS os outros HTML são manuais e protegidos.**
Esta regra aplica-se a páginas actuais E futuras.
Qualquer novo HTML criado está automaticamente protegido — não precisa de ser adicionado a listas.

O guardrail está implementado em dois locais:
1. `scripts/gerar_noticias.py` — função `escrever_ficheiro_seguro()` bloqueia qualquer escrita em HTML que não seja `noticias.html`
2. `.github/workflows/pipeline-diario.yml` — step "Verificar ficheiros protegidos" faz `exit 1` se algum HTML protegido for detectado como modificado antes do commit

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
| Pesquisa interna | `scripts/pesquisa.js` (JS puro, 24 páginas indexadas) |
| Scraper | Playwright + BeautifulSoup (`scripts/scraper_playwright.py`) |
| Extracção valores | `scripts/extrair_valores.py` → `data/divergencias.json` |
| Notícias | `scripts/gerar_noticias.py` → `noticias.html` |
| Partilha social | `assets/js/share.js` + `assets/css/share.css`, inserido em cada página via `scripts/inserir_botao_partilhar.py` (idempotente, sem bibliotecas externas) |
| Clusters/navegação | `data/clusters.json` (fonte única) + `scripts/sincronizar_clusters.py` (idempotente, injecta entre marcadores — ver secção "SISTEMA DE CLUSTERS") |

### Workflows (5 — 2 fazem push, âmbitos disjuntos)

| Ficheiro | Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | cron `0 6 * * *` | Scrape → detectar mudanças → notícias → validar valores → README → push único | ✅ sim (`data/`, `index.html`, `noticias.html`, `README.md`, `CLAUDE.md`) |
| `shadow-daily.yml` | cron `0 3 * * *` | `run_shadow_daily.py`: Shadow Mode → analytics → relatório Markdown → guarda em `shadow_history/` | ✅ sim (só `shadow_history/*.md`) |
| `verificar-links.yml` | cron `0 7 * * 1` (segunda) | lychee testa todos os links HTML + Issue se 404 | ❌ não |
| `validar-conteudo.yml` | push para main `**.html` | Valida GA4, OG tags, JSON-LD, disclaimer, data verificação + HTML5 validator | ❌ não |
| `integridade.yml` | ver ficheiro | Verificações de integridade adicionais | ❌ não |

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
- [ ] Commit e push directamente para `main`

---

## ESTRUTURA DE FICHEIROS ACTUAL

```
tens-direito/
├── *.html                    ← páginas estáticas publicadas (raiz = GitHub Pages)
├── assets/
│   ├── js/share.js           ← lógica do botão "Partilhar este artigo" (vanilla JS)
│   └── css/share.css         ← estilo do botão/mensagens de partilha
├── scripts/
│   ├── scraper_playwright.py ← Playwright + BS4, scrapes 6 fontes
│   ├── extrair_valores.py    ← compara valores scraped vs HTML publicado
│   ├── gerar_noticias.py     ← RSS → noticias.html
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
│   ├── sincronizar_clusters.py ← lê data/clusters.json, injecta nav entre marcadores (idempotente)
│   ├── pesquisa.js           ← pesquisa interna (JS puro, sem servidor)
│   └── logs/                 ← logs do scraper
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
   no JSON, contagem por tipo.

**Estado actual (Fases 1 e 2 concluídas):** fundação de dados pronta,
os 5 pillars existem com a lista de artigos sincronizada, e a
`index.html` foi reorganizada pela ordem hero (com pesquisa) → "Comece
por aqui" → clusters → guias principais → como funciona → prazos →
notícia do dia. A pesquisa (`#campo-pesquisa`) foi movida da nav para o
hero, com chips de sugestão (`preencherPesquisa()`); a antiga grelha de
14 cartões foi substituída pelos 5 cartões de cluster (`CLUSTERS:HOME`)
mais 5 cartões de destaque, um por cluster (`DESTAQUES:HOME`); o
`id="guias-de-apoios"` manteve-se na secção de clusters para não
partir o link `/#guias-de-apoios` já usado noutras páginas.

Ainda faltam os marcadores `CLUSTER-BADGE`/`RELACIONADOS` nos 20
artigos-membro (`--dry-run` reporta-os como "marcador em falta" —
esperado até à Fase 3). Próximos passos: injectar navegação contextual
nos artigos (Fase 3), simplificar a nav principal com um
`sincronizar_nav.py` (Fase 4), passar UX/SEO final (Fase 5).

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
7. Actualizar `descricao_curta` do cluster `prestacao-social-unica` em `data/clusters.json`
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

*Última revisão automática: 2026-07-01*

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
