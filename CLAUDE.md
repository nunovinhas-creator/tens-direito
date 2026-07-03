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
- `noticias.html` — arquivo de notícias, gerado a partir de `data/noticias.json` (ficheiro inteiro, sem marcadores)
- `data/noticias.json` — fonte de verdade das notícias (ver secção "FRESCURA DA HOMEPAGE")
- `CLAUDE.md` — data de revisão automática
- `README.md` — estado do repositório
- `data/scraped/*.json` — dados do scraper
- `data/estado_fontes.json` — máquina de estados de fontes bloqueadas (ver secção "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS")
- `data/feeds_saude_hoje.json` — snapshot diário da saúde de cada feed de notícias (Fase 3, ver secção "FRESCURA DA HOMEPAGE")
- `data/estado_feeds.json` — máquina de estados de feeds mortos, escrito por `gerir_estado_feeds.py` (mesmo padrão de `estado_fontes.json`)
- `data/noticias_candidatos.json` — log auditável de candidatos/decisões de cada corrida de notícias (últimas 60 corridas)

**TODOS os outros HTML são manuais e protegidos.**
Esta regra aplica-se a páginas actuais E futuras.
Qualquer novo HTML criado está automaticamente protegido — não precisa de ser adicionado a listas.

O guardrail está implementado em dois locais:
1. `scripts/gerar_noticias.py` — função `escrever_ficheiro_seguro()` é uma allow-list estrita: `FICHEIROS_AUTO_GERADOS` (`noticias.html`, `noticias.json`, `feeds_saude_hoje.json`, `noticias_candidatos.json` — escrita livre) ou `SECCOES_PERMITIDAS` (`index.html`, só dentro de `NOTICIA-HOME:INICIO/FIM` — `_verificar_escrita_confinada()` compara o ficheiro em disco com o novo conteúdo fora da secção marcada; qualquer diferença aí, ou o marcador não existir, bloqueia a escrita). Qualquer nome fora das listas é **sempre bloqueado**, nunca escrito por omissão (corrigido na Fase 1 do sistema de notícias — antes havia um "fallthrough" que escrevia livremente qualquer ficheiro não-HTML não listado). Ver `tests/test_gerar_noticias_guardrail.py`. `data/estado_feeds.json` fica fora desta allow-list de propósito — é escrito directamente por `gerir_estado_feeds.py`, script dedicado e de confiança por construção, mesmo padrão de `estado_fontes.json`/`gerir_estado_fontes.py`.
2. `.github/workflows/pipeline-diario.yml` — step "Verificar ficheiros protegidos" faz `exit 1` se algum HTML protegido for detectado como modificado antes do commit (ficheiros `.json` em `data/` nunca passam por este guardrail — só HTML é protegido)

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
| Pesquisa interna | `scripts/pesquisa.js` (JS puro, 27 páginas indexadas — todas excepto `index.html` e `404.html`; ranking em camadas + excerto + badge de cluster — ver nota de manutenção abaixo) |
| Scraper | Playwright + BeautifulSoup (`scripts/scraper_playwright.py`), com `playwright-stealth`, retries com jitter e fallback Wayback (`OK_VIA_ARQUIVO`) — ver secção "SCRAPER — ROBUSTEZ CONTRA BLOQUEIOS" |
| Extracção valores | `scripts/extrair_valores.py` → `data/divergencias.json` |
| Notícias | `data/noticias.json` (fonte de verdade) + `scripts/gerar_noticias.py` (7 feeds RSS por tema + corte de recência de 7 dias) → `noticias.html` (arquivo por mês) + 2-3 cards em `index.html` (`NOTICIA-HOME`) — ver secção "FRESCURA DA HOMEPAGE" |
| Partilha social | `assets/js/share.js` + `assets/css/share.css`, inserido em cada página via `scripts/inserir_botao_partilhar.py` (idempotente, sem bibliotecas externas) |
| Clusters/navegação | `data/clusters.json` (fonte única) + `scripts/sincronizar_clusters.py` (idempotente, injecta entre marcadores — ver secção "SISTEMA DE CLUSTERS") |

**Ranking e apresentação da pesquisa (`scripts/pesquisa.js`)** — reformulado
2026-07-02: antes, "sub" devolvia páginas sem o termo no título
misturadas sem ordem nenhuma com as que tinham, numa lista sem limite
a ocupar o ecrã inteiro em mobile. Agora:

1. **Dados por página**: `url`, `titulo`, `descricao` (a meta
   description real, extraída de cada página — nunca inventada),
   `keywords` (curadas à mão, mais ricas do que `clusters.json`
   consegue oferecer) e `cluster`/`clusterNome`/`tipo`. Estes três
   últimos campos **têm de bater certo com `data/clusters.json`**
   (fonte única) — verificado por `tests/test_pesquisa_indice.py`, que
   corre sobre o `pesquisa.js` real e falha se divergir (cluster
   inexistente, nome errado, tipo errado, página de cluster sem
   `cluster` atribuído, ou vice-versa). Título/descrição/keywords
   continuam curados à mão — `clusters.json` não guarda essa riqueza.
2. **Ranking em 3 camadas, nunca misturadas**: 1) termo no título,
   2) termo na descrição, 3) termo nas keywords. Dentro de cada
   camada, ordem alfabética (determinística, nunca aleatória).
   Limitado a 8 resultados visíveis (`MAX_RESULTADOS`).
3. **Contexto do match**: resultados de camada 1 mostram o título com
   o termo destacado (`<mark>`) e a descrição como linha secundária;
   resultados de camada 2/3 mostram um excerto (~30 caracteres de
   contexto para cada lado, `RAIO_EXCERTO`) à volta da 1.ª ocorrência,
   com o termo destacado — é como se percebe porquê "Estatuto do
   Cuidador Informal" aparece a pesquisar "sub" (a palavra "subsídio"
   na descrição).
4. **Mínimo de 2 caracteres** (`MIN_CARACTERES`) antes de pesquisar —
   1 carácter nunca dispara, dropdown fica escondido.
5. **Badge do cluster** em cada resultado (`clusterNome`, mais
   "Ferramenta" se `tipo === 'ferramenta'`) e **estado vazio explícito**
   ("Sem resultados para 'x' — Vê todos os guias →", a apontar para
   `/#guias-de-apoios`, a secção de clusters da homepage).
6. **CSS partilhado**: `.resultado-item`/`.resultado-titulo`/
   `.resultado-excerto`/`.resultado-badge`/`.resultado-vazio` vivem em
   `assets/css/nav.css` (carregado em todas as páginas) — usados tanto
   pelos dropdowns da nav como pela pesquisa do hero em `index.html`,
   que também ganhou `max-height: 60vh` + scroll interno (classe
   `.hero-search-resultados`, antes estilo inline) — mesmo tratamento
   já existente em `.nav-search-resultados`.

Testado com Chromium real em `tests/test_pesquisa_ranking.py`
(ranking, camadas, excertos, badges, limite de 8, mínimo de
caracteres, estado vazio) — carrega o `pesquisa.js` real, nunca uma
cópia.

**Pesquisa do hero (`index.html`) — nota de manutenção**: `pesquisa.js`
tem um listener global (`document.addEventListener('click', ...)`) que
fecha `#resultados-pesquisa` sempre que o clique não é no campo nem no
próprio dropdown — inclui **qualquer botão que abra a pesquisa por
clique** (chips, botão de lupa). Sem `event.stopPropagation()` no
handler desse botão, o clique que abre os resultados também os fecha
no mesmo evento (bug real corrigido nesta sessão — `preencherPesquisa()`
e `executarPesquisaHero()`, ambas em `index.html`, chamam
`e.stopPropagation()` antes de mais nada). **Qualquer botão novo que
dispare pesquisa por clique tem de seguir o mesmo padrão.** A tecla
Enter não sofre disto (é `keydown`, não `click`). Testado com
Chromium real (não é possível apanhar isto só por inspecção de texto)
em `tests/test_pesquisa_hero.py`, que extrai o JS/CSS directamente do
`index.html` real em vez de manter uma cópia à parte.

### Workflows (5 — 2 fazem push, âmbitos disjuntos)

| Ficheiro | Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | cron `0 6 * * *` | Scrape → detectar mudanças → notícias → validar valores → README → push único | ✅ sim (`data/`, `index.html`, `noticias.html`, `README.md`, `CLAUDE.md`) |
| `shadow-daily.yml` | `workflow_run` após "Pipeline Diário" + cron `0 8 * * *` (rede de segurança) | `run_shadow_daily.py`: Shadow Mode → analytics → relatório Markdown → guarda em `shadow_history/` | ✅ sim (só `shadow_history/*.md`) |
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
| `psu-trabalho-social.html` | Trabalho social na PSU: aprovado vs. por definir | 3 jul. 2026 |
| `p/habitacao.html` | Apoios à Habitação em Portugal 2026 — Guia Completo | 3 jul. 2026 |
| `porta-65.html` | Porta 65 Jovem e Porta 65+ 2026 | 3 jul. 2026 |
| `apoio-extraordinario-renda.html` | Apoio Extraordinário à Renda 2026: o que aconteceu e alternativas | 3 jul. 2026 |
| `prova-escolar.html` | Prova Escolar 2026: prazo 31 de julho — quem tem de fazer e como | 3 jul. 2026 |
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
│   ├── gerar_noticias.py     ← RSS por tema + data/noticias.json → noticias.html + cards em index.html (NOTICIA-HOME)
│   ├── gerir_estado_feeds.py ← máquina de estados de feeds de notícias mortos (Step 3a do pipeline)
│   ├── migrar_noticias.py    ← migração única do noticias.html legado para data/noticias.json (não corre no pipeline)
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
│   ├── gerir_estado_fontes.py ← máquina de estados de fontes bloqueadas (Step 1b do pipeline)
│   ├── wayback_fallback.py   ← fallback Wayback Machine, puro, sem I/O próprio (fetch_json injectado)
│   ├── pesquisa.js           ← pesquisa interna (JS puro, sem servidor)
│   └── logs/                 ← logs do scraper
├── tests/                    ← pytest; inclui test_sincronizar_clusters.py,
│                                test_breadcrumb_coerencia.py e test_nav_coerencia.py
│                                (estes dois últimos correm sobre as páginas reais, não fixtures)
├── data/
│   ├── clusters.json         ← fonte única de verdade da arquitectura de clusters
│   ├── noticias.json         ← fonte de verdade das notícias (ver "FRESCURA DA HOMEPAGE")
│   ├── scraped/              ← JSONs diários por fonte + *_latest.json
│   ├── mudancas.json         ← mudanças detectadas pelo pipeline
│   ├── divergencias.json     ← valores scraped vs publicado
│   ├── bloqueios.json        ← bloqueios do dia (Camada 1 do scraper), consumido por gerir_estado_fontes.py
│   ├── estado_fontes.json    ← máquina de estados por fonte (ver "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS")
│   ├── feeds_saude_hoje.json ← snapshot diário da saúde de cada feed de notícias, consumido por gerir_estado_feeds.py
│   ├── estado_feeds.json     ← máquina de estados por feed de notícias (ver "FRESCURA DA HOMEPAGE")
│   ├── noticias_candidatos.json ← log auditável de candidatos/decisões, últimas 60 corridas (ver "FRESCURA DA HOMEPAGE")
│   └── pagina_fonte.json     ← mapeamento manual página → fonte(s) (ver "REVALIDAÇÃO DE CARIMBO")
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
4. **Clusters actuais — todos os 6 pillars existem:**

   | Cluster | Pillar |
   |---|---|
   | Apoios Escolares | `p/apoios-escolares.html` |
   | Prestação Social Única | `prestacao-social-unica.html` |
   | Família e Crianças | `p/familia.html` |
   | Idosos, Incapacidade e Cuidadores | `p/idosos-incapacidade-cuidadores.html` (inclui `amim.html`) |
   | Trabalho e Rendimento | `p/trabalho-rendimento.html` |
   | Habitação | `p/habitacao.html` (criado 3 jul 2026 — Porta 65 Jovem/+ e Apoio Extraordinário à Renda) |

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

### A) "Últimas notícias" — `data/noticias.json` + `gerar_noticias.py` + `NOTICIA-HOME:INICIO/FIM`

**Fase 1 (2026-07-02)**: `data/noticias.json` passou a ser a fonte de
verdade — `noticias.html` deixou de ser a própria base de dados (patch
incremental do HTML anterior) e passa a ser **gerado do JSON** a cada
corrida (destaque + arquivo agrupado por mês, ordenado por data real
desc — nunca por ordem de inserção). `index.html` mostra os 2-3 itens
mais recentes (antes era só 1).

Cada item: `data_iso`, `titulo` (sem o sufixo "- Fonte" do Google
News), `fonte_nome`, `url`, `resumo`, `categoria` (para os filtros do
`noticias.html`) e `cluster_id` (classificação best-effort por
palavra-chave — `CLUSTER_KEYWORDS` — preparada para a Fase 3 ligar
cada notícia ao guia do cluster; ainda não renderizada em lado nenhum).

**Migração** (`scripts/migrar_noticias.py`, corre uma única vez, nunca
no pipeline): parseou o `noticias.html` legado nos dois formatos de
card que coexistiam (`arquivo-card`, do script; `noticia-card`,
manuscrito antes do script existir), descartou 1 registo vazio/
corrompido (placeholder `"Notícia anterior"` com `href="#"`, resíduo
de um bug antigo do extractor do destaque) e deduplicou os restantes
14 — 4 eram duplicados reais (mesma notícia publicada em dias
diferentes, sem dedup nenhum a proteger) — mantendo sempre a
ocorrência de **data mais antiga** (primeira publicação real). Resultado:
**10 itens únicos**. Ver `tests/test_migrar_noticias.py`.

**Dedup no pipeline** (`encontrar_duplicado()` — o bug mais grave
encontrado no diagnóstico da Fase 0: a mesma notícia chegou a ser
"republicada" 4× em dias diferentes): compara o candidato vencedor
contra `data/noticias.json` por **título normalizado** (minúsculas,
sem pontuação, `difflib` com limiar de 0.90 de semelhança — sempre
válido) e por **URL canónico exacto**, mas só quando o URL não é a
homepage genérica de um domínio (`_url_e_especifica()`) — descoberto
durante a migração: dois artigos manuscritos genuinamente diferentes
citavam ambos `dge.mec.pt` como fonte e o URL sozinho dava-os como
duplicados um do outro. Se o vencedor inicial for duplicado,
`selecionar_vencedor()` passa ao candidato seguinte com score
positivo; se todos forem duplicados ou não houver nenhum com score
positivo, o resultado é `None` — **"nenhuma notícia hoje" é aceitável,
nunca se força um candidato fraco ou repetido**.

**Observabilidade**: cada corrida regista no log (`imprimir_relatorio()`)
o nº de candidatos por feed, os 3 melhores com o respectivo score, cada
rejeição por dedup com o motivo (`"duplicado de AAAA-MM-DD"`) e o
vencedor final com o motivo. Antes da Fase 1 não havia nenhuma
visibilidade sobre quantos candidatos existiam nem porque um venceu.

Mostra sempre a data real da notícia (nunca "hoje") e liga directamente
à fonte externa (nunca um link interno inventado). Se não houver
vencedor, `data/noticias.json` não é tocado.

**`sincronizar_saidas()`** — ponto único que regenera `noticias.html` e
o bloco `NOTICIA-HOME` a partir do JSON actual em disco; idempotente
(zero alterações se já estiverem sincronizados) e independente de
qualquer corrida de RSS. `main()` chama-o **sempre no fim, com ou sem
vencedor novo no dia** — corrigido um bug real desta sessão: antes,
`main()` terminava a corrida assim que não havia vencedor, sem nunca
regenerar as saídas; se o JSON tivesse mudado por outra via (ex.:
`migrar_noticias.py`, edição manual), `noticias.html`/`index.html`
ficavam presos ao conteúdo antigo indefinidamente, só se resincronizando
por coincidência no dia em que a corrida também encontrasse notícia
nova. Utilizável como passo manual isolado, sem tocar no RSS:
`python scripts/gerar_noticias.py --sync`. `migrar_noticias.py` chama-o
automaticamente no fim da migração — nunca mais é preciso um passo
manual à parte para sincronizar depois de migrar. Testado em
`tests/test_gerar_noticias.py` (idempotência + carrega do JSON em
disco quando não recebe itens explícitos + o item mais recente do
JSON tem sempre de aparecer no bloco NOTICIA-HOME após a chamada).

**Guardrail estendido** (mudança de segurança, reforçada na Fase 1):
`escrever_ficheiro_seguro()` em `gerar_noticias.py` é agora uma
allow-list estrita — `FICHEIROS_AUTO_GERADOS` (`noticias.html`,
`noticias.json`, escrita livre) ou `SECCOES_PERMITIDAS` (`index.html`,
só dentro de `NOTICIA-HOME:INICIO/FIM`, via `_verificar_escrita_confinada()`).
Qualquer nome fora das duas listas é **sempre bloqueado** — corrigido
um "fallthrough" que antes escrevia livremente qualquer ficheiro não-
HTML não listado (nunca chegou a ser explorado na prática, porque o
próprio script nunca chamava a função com outro nome, mas era uma
allow-list incompleta). Coberto por `tests/test_gerar_noticias_guardrail.py`.

**Bugs de correspondência de classes encontrados e corrigidos em
`noticias.html`** (nenhum introduzido pela Fase 1 — todos pré-existentes,
descobertos ao regenerar o ficheiro a partir do JSON): o JS de
paginação/filtros seleccionava `.noticia-card`, mas o script gerava
`.arquivo-card` — a contagem por categoria e a paginação só "viam" os
3 cards manuscritos antigos, nunca os gerados automaticamente; o CSS
não tinha nenhuma regra para `.arquivo-card` (cards sem estilo nenhum);
`.cat-badge.apoios` (CSS) nunca correspondia a `class="cat-badge
cat-apoios"` (HTML real) — os badges de categoria nunca mostravam cor;
`#destaque-wrap` era referenciado no JS mas não existia no HTML — o
destaque nunca era escondido ao filtrar por categoria. Unificada a
classe (`arquivo-card`, uma só, para itens manuscritos e gerados),
corrigidos os 3 selectores, confirmado no browser (Playwright): 9/9
cards visíveis pela contagem e pela paginação, badge com cor correcta,
destaque a esconder/mostrar correctamente ao filtrar.

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

### Fontes RSS — diagnóstico e correcção de 2026-07-04

Sintoma reportado pelo Nuno: uma notícia real sobre abono de família (2
jul) nunca foi apanhada pelo pipeline, apesar de correr diariamente com
sucesso. Diagnóstico feito com fetch real num `workflow_dispatch`
temporário (política de rede da sessão de desenvolvimento bloqueia
`news.google.com`/`dre.pt` — mesma limitação já documentada, só o
runner real é fiável para isto):

1. **`data/noticias.json` confirmado a actualizar diariamente**, mas
   sempre com artigos cada vez mais antigos sobre a PSU (8 jun a 29
   jun, um por dia) — nunca conteúdo genuinamente novo.
2. **Causa raiz, com evidência real**: os 3 feeds genéricos antigos
   (`apoios sociais portugal`, `segurança social portugal`, `IRS
   subsidios portugal 2026`) devolviam a notícia de abono real (quando
   existia) na posição 78+ de 100 — muito além de qualquer limite
   realista (`fetch_entries()` só examinava as primeiras 10). Um feed
   dedicado por tema (`abono de família portugal`) encontrou a mesma
   notícia (ou uma da mesma janela temporal, 1 jul) **na 1.ª posição**
   — confirma que a especificidade da query, não o limite por feed, é
   o factor decisivo.
3. **Factor agravante confirmado**: a selecção nunca considerava a
   data — só o score de keywords — por isso um artigo de PSU de há 2
   meses (muitas keywords: "prestação", "apoio", "psu", etc.) continua
   a vencer todos os dias em vez de notícias mais recentes e mais
   específicas com score mais baixo.
4. **DRE confirmado morto em 3 investigações diferentes** (XML
   malformado, `not well-formed (invalid token)`, sempre no mesmo
   ponto) — testados também 2 URLs alternativos do DRE, ambos com o
   mesmo erro. Candidatos a fonte oficial testados e mortos:
   `seg-social.pt/rss` (entidade XML indefinida), `portugal.gov.pt/.../rss`
   (404). **Não existe hoje um substituto oficial vivo** — não é falta
   de tentativa, é confirmado por fetch real.

**Correcção aplicada** (`scripts/gerar_noticias.py`):
- `FEEDS` passa de 3 pesquisas genéricas + DRE para **7 feeds, um por
  tema do site** (`abono_familia`, `subsidio_desemprego`, `rsi`,
  `psu_pensoes`, `acao_social_escolar`, `cuidador_informal`,
  `porta65_arrendamento`) — todos testados com fetch real antes de
  entrar no código. DRE removido sem substituto (documentado, não um
  placeholder morto).
- **Corte de recência** (`JANELA_RECENCIA_DIAS = 7`): candidatos mais
  antigos que 7 dias são rejeitados mesmo com score alto — elimina o
  "banco" de artigos antigos da PSU. Motivo registado no log
  (`"antigo (antes de AAAA-MM-DD, janela de 7 dias)"`).
- `LIMITE_ENTRADAS_POR_FEED` sobe de 10 para 15 (margem de segurança
  barata — o diagnóstico mostrou que a query específica, não este
  limite, era o que importava).
- Testado com os títulos e datas **reais** capturados no diagnóstico
  como fixtures (`tests/test_gerar_noticias.py`) — o artigo de PSU de
  maio é rejeitado pelo corte de recência mesmo com score mais alto do
  que o artigo de abono de julho, que vence.

**Observabilidade permanente** (Fase 3, mesmo padrão de
`gerir_estado_fontes.py`):
- `data/feeds_saude_hoje.json` — snapshot diário por feed (`OK`/`MORTO`,
  motivo, n.º de entradas) — um feed com `bozo=True` (erro de parsing
  XML, o caso do DRE) conta sempre como `MORTO`, **mesmo com HTTP 200**.
- `scripts/gerir_estado_feeds.py` (Step 3a do pipeline) — máquina de
  estados pura (`data/estado_feeds.json`), mesma lógica de
  `gerir_estado_fontes.py`: só cria Issue `feed-morto` ao 3.º dia
  consecutivo, fecho automático ao recuperar. Sem dados de saúde da
  corrida (ex.: `gerar_noticias.py` falhou antes de escrever), mantém o
  último estado conhecido — nunca inventa "tudo OK" nem "tudo morto".
- `data/noticias_candidatos.json` — log auditável das últimas 60
  corridas (candidatos por feed, top 3, rejeitados com motivo,
  vencedor ou `null`) — "nenhuma notícia hoje" deixa de ser
  indistinguível de uma avaria; é sempre possível confirmar a
  posteriori que a selecção correu e porque não escolheu nada.

Testado em `tests/test_gerar_noticias.py` (corte de recência, saúde de
feed, logs), `tests/test_estado_feeds.py` (máquina de estados, mesmos
casos de `test_estado_fontes.py`) e `tests/test_gerar_noticias_guardrail.py`
(allow-list dos 2 novos ficheiros).

**Verificado no pipeline real** (`workflow_dispatch` de
`pipeline-diario.yml`, não só no runner de diagnóstico): ver entrada de
revisão no fim deste ficheiro para o resultado real, não assumido.

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
| `prova-escolar.html` | Junho (ano letivo seguinte) | Calendário anual — ver nota abaixo |

**`prova-escolar.html` — nota de manutenção sazonal**: a página refere o
ano letivo "2026/2027" (título, meta description, `og:title`, breadcrumb
JSON-LD, fonte-bloco) e a data "31 de julho de 2026" (H1, título,
`prazo-topo`, resposta directa) — ambos têm de ser revistos **todos os
anos em junho**, antes do próximo prazo de 31 de julho, para o ano
letivo seguinte. O conteúdo normativo (quem tem de fazer, tabela de
prazos/consequências, passo a passo na SSD) não muda todos os anos —
só as referências ao ano concreto. Candidata natural para
`verificar_datas.py`: o padrão "2026/2027" nesta página deve expirar em
**junho de 2027**, não antes — se `MARCADORES_PENDENTE`/supressões
gerarem um alerta prematuro (por exemplo, logo em 2026), é um falso
positivo a corrigir na Camada 1, não um sinal de que a página está
desactualizada.

---

## IMPACTO DA PSU (Prestação Social Única)

Estado: aprovada parlamento 25/06/2026.
Aguarda: decreto-lei com valores + publicação DR.
Prazo PRR decreto-lei: 31 ago 2026.
Entrada em vigor para beneficiários: 1 jan 2027 (texto inicial, não confirmado pelo decreto-lei).
Cluster publicado: 1 jul 2026 (pillar + 4 páginas filhas); + `psu-trabalho-social.html` a 3 jul 2026
(5.ª página filha — ver "PÁGINAS PUBLICADAS").

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

**`simulador-psu.html` já existe** (desde 3 jul 2026), pronto e testado
(`tests/test_simulador_psu_calculo.py`), mas deliberadamente **não publicado**
— fora de `sitemap.xml`, `scripts/pesquisa.js` e `data/clusters.json`, com
`<meta name="robots" content="noindex, nofollow">` e `ESTADO_SIMULADOR =
'AGUARDA_DECRETO'`. Publicar (não criar) é o gatilho: decreto-lei da PSU
publicado em dre.pt com Valor de Referência, valor máximo e coeficiente CIT
confirmados — ver o Passo 5a de `.claude/commands/atualizar-cluster-psu.md`.

### Plano de acção (quando DR for publicado)

1. Actualizar `prestacao-social-unica.html` com valores reais do decreto-lei
2. Actualizar `psu-quando-entra-em-vigor.html`, `psu-quem-tem-direito.html` e
   `psu-trabalho-social.html` (secção "Por definir" — obrigatoriedade do
   trabalho social) com valores/factos confirmados
3. Criar `como-pedir-psu.html` e `calendario-pagamentos-psu.html`; publicar
   `simulador-psu.html` (Passo 5a do comando `atualizar-cluster-psu`)
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

## CLUSTER HABITAÇÃO

Criado a 3 jul 2026 — pillar `p/habitacao.html` + 2 artigos-filho
(`porta-65.html`, `apoio-extraordinario-renda.html`), sexto cluster do
site. Fact-check prévio obrigatório (bloqueante, ver "REGRAS DE
CONTEÚDO") feito via `WebSearch` nesta sessão — `WebFetch` está
completamente bloqueado neste ambiente de sessão (403 em qualquer URL,
incluindo domínios fora de `.gov.pt`, ex.: `en.wikipedia.org` — não é
um bloqueio específico a portais oficiais, é o próprio `WebFetch` que
não funciona nesta sessão). As páginas citam sempre a URL oficial como
fonte, mesmo sem acesso directo — mesmo padrão já usado no site para
fontes que devolvem 403 a bots (ver "FONTES VERIFICADAS E APROVADAS").

### Estado real verificado (jul 2026)

- **Porta 65 Jovem / Porta 65+**: candidaturas contínuas, sem prazo,
  desde junho de 2023; avaliação mensal desde setembro de 2024. Porta
  65 Jovem = 18-35 anos; Porta 65+ = sem limite de idade, para quebra
  de rendimentos >20% ou monoparentalidade (desde OE2026, também
  vítimas de violência doméstica com estatuto reconhecido). A Renda
  Máxima de Referência do concelho deixou de excluir candidaturas —
  só serve para calcular o apoio. Fontes secundárias consultadas
  divergiam no limite de idade exacto do 2.º elemento de um casal
  (36 vs. 37 anos) — a página não fixa esse número, remete para o
  Portal da Habitação em vez de arriscar um valor errado.
- **Apoio Extraordinário à Renda (PAER)**: confirmado **fechado a
  novos beneficiários** — só contratos de arrendamento celebrados até
  15/03/2023. Mantém-se em vigor a pagar quem já foi aprovado
  (pagamentos até 31/12/2028; ~4.700 beneficiários pagos, situação de
  jul 2026). Provedoria de Justiça denunciou irregularidades graves em
  ago 2025 (~mil queixas); Governo anunciou em fev 2026 a intenção de
  revogar e substituir por novo programa — **ainda não publicado em DR
  à data de verificação (3 jul 2026)**. Por isso `apoio-extraordinario-renda.html`
  não é um guia de candidatura — é uma página "estado actual +
  alternativas", apontando para o Porta 65.

### Backlog — outros apoios de habitação vivos em 2026 (sem página ainda)

Registados por pedido explícito da sessão — **não criar páginas agora**,
só quando houver prioridade dedicada:

| Apoio | Estado confirmado (jul 2026) | Nota |
|---|---|---|
| Garantia pública para crédito habitação jovem | Vivo — contratos até final de 2026, cobre até 15% do valor da transacção | Permite financiamento a 100% em vez do limite geral de 90% |
| Isenção de IMT/Imposto do Selo para jovens (até 35 anos) | Vivo — limites actualizados no OE2026 (+2%); isenção total até 330.539€, parcial até 660.982€ (2026) | Acumulável com a garantia pública |
| Regime Simplificado de Arrendamento Acessível (RSAA) | Vivo — Decreto-Lei n.º 97/2026, de 20 mai | Benefício fiscal para **senhorios** que praticam rendas moderadas (IRS reduzido a 10%, ou isenção total abaixo de 20% da mediana do concelho) — não é apoio directo ao inquilino, ângulo de página diferente dos outros dois artigos deste cluster |
| 1.º Direito — Programa de Apoio ao Acesso à Habitação | Vivo — programa PRR, gerido pelos municípios (Estratégia Local de Habitação), alterado por DL n.º 44/2025 (mar 2025) | Não é candidatura directa do cidadão ao IHRU — passa pela câmara municipal; ângulo de página diferente (processo institucional, não formulário pessoal) |

---

## MONETIZAÇÃO — POLÍTICA DE AFILIADOS (futuro)

Registado a pedido explícito da sessão de 3 jul 2026 — **nenhum link de
afiliado existe hoje no site; nada foi adicionado nesta sessão.**
Puramente documental, para quando essa decisão for tomada.

Quando (e se) links de afiliados forem introduzidos:

1. **Divulgação explícita** junto de cada bloco de conteúdo afiliado
   (ex.: "contém links de parceiros") — nunca escondida em letras
   pequenas ou só no rodapé.
2. **Separação visual** clara do conteúdo editorial — nunca um link de
   afiliado misturado, sem aviso, no meio de uma lista de fontes
   oficiais ou de um passo-a-passo de candidatura.
3. **Âmbito restrito a produtos alinhados** com o tema do site (ex.:
   seguros de habitação, comparadores de tarifas) — **nunca** em
   páginas de prestações sociais, simuladores, ou `comecar-aqui.html`.
   Estas páginas existem para ajudar alguém a aceder a um direito, não
   para gerar receita a partir dessa necessidade.
4. O "Aviso de independência", já presente em todas as páginas de
   conteúdo, passa a explicitar também a política de afiliados quando
   esta existir — não é um texto novo, é uma extensão do já existente.
5. **Qualquer implementação é decisão manual do Nuno**, tomada numa
   sessão dedicada — nunca introduzida incidentalmente como parte de
   outra tarefa.

---

## E-E-A-T — NV LABS COMO ENTIDADE RESOLVÍVEL

Sessão de 2026-07-03: sem autor pessoal público (decisão do Nuno,
mantida), o E-E-A-T do site joga-se a nível de entidade + método. A
**NV Labs** — estúdio independente português, responsável editorial do
Tens Direito — passa a ser **resolvível**: antes, "An NV Labs project"
no footer não linkava para lado nenhum; agora tem secção própria em
`sobre.html#nvlabs`, JSON-LD `Organization` e um `sameAs` real (o
próprio repositório GitHub, único link "NV Labs" que existe de facto —
nunca um perfil inventado).

### `sobre.html` — 5 blocos + excepção à regra de JSON-LD

Reescrito com: 1) o que é o site; 2) quem está por trás — NV Labs
(`id="nvlabs"`, link para o repositório); 3) método de verificação
(`id="metodo"`, bloco central — fontes exclusivamente oficiais, scraper
diário + revisão humana antes de qualquer actualização, carimbo
"Verificado a", redação assistida por IA com verificação humana de
factos, o que o site não faz); 4) correcções (GitHub Issues + marcador
`CONTACTO-EMAIL`); 5) contacto (só GitHub Issues). Nenhuma pessoa,
credencial ou e-mail inventados.

`sobre.html` ganha JSON-LD — única página institucional a fazê-lo,
excepção deliberada à regra "institucionais sem JSON-LD" (ver secção
"PÁGINAS INSTITUCIONAIS"): `AboutPage` (mainEntity → Organization),
`Organization` (`@id=".../sobre.html#nvlabs"`, `sameAs` só com o
repositório real) e `WebSite` (publisher → Organization). Válido
porque `FAQPage`/`WebPage` herdam `author`/`publisher` de
`CreativeWork` — confirmado por `tests/test_sobre_jsonld.py`, que
carrega e valida os 3 blocos como JSON real, nunca uma cópia.

### Marcador `CONTACTO-EMAIL` — preparado, não activo

`sobre.html` tem `<!-- CONTACTO-EMAIL:INICIO --><!-- quando existir:
contacto@tens-direito.com --><!-- CONTACTO-EMAIL:FIM -->` — o endereço
só existe dentro do comentário, nunca como `mailto:` real (verificado
por teste). **Activação futura**: quando o e-mail existir, preencher
este marcador em `sobre.html` com o link real e rever a frase "GitHub
Issues é o único canal de contacto". Até lá, a regra "Não inventar
e-mails — usar GitHub Issues" mantém-se inalterada.

### Footer — "An NV Labs project" passa a link

`scripts/atualizar_branding_nvlabs.py` deixou de ser só bootstrap
(insere uma vez, nunca mais toca) e passou a **sincronizador
idempotente nos dois sentidos**: página sem marcadores → bootstrap;
página já com marcadores → substitui o conteúdo entre
`NVLABS:HEADER`/`NVLABS:FOOTER` pelo bloco canónico actual, no-op se já
estiver igual (novo `--apenas-sincronizar` impede bootstrap acidental
em páginas que nunca tiveram o bloco — usado para excluir `404.html`,
que não tem `</footer>` nem badge NV Labs por não ter sido processada
antes, fora do âmbito desta sessão). O bloco footer (`<div>` → `<a
href="/sobre.html#nvlabs">`) envolve agora o SVG existente — o texto
"An NV Labs project" mantém-se exactamente igual (decisão do Nuno),
só passou a ser clicável. Corrido com `--apenas-sincronizar --write`
nas 34 páginas que já tinham o bloco; idempotência confirmada.
`assets/css/branding.css` ajustado (`.footer-nvlabs` de `<div>` para
`<a>`, com `:focus-visible`).

### Autoria nos artigos — `scripts/adicionar_autoria_artigos.py`

Novo script, âmbito automático (todas as páginas com `"@type":
"FAQPage"` em `*.html`/`p/*.html` — 27 no total, `simulador-psu.html`
fica fora por não ter JSON-LD nenhum, deliberadamente não publicado):

1. Injecta `"author"`/`"publisher"` (`{"@id": ".../sobre.html#nvlabs"}`)
   no bloco `FAQPage` — válido em Schema.org (`FAQPage` < `WebPage` <
   `CreativeWork`, que já define ambas as propriedades).
2. Acrescenta atribuição à **última** ocorrência de "Verificado a
   [data]" de cada página (a canónica — mesmo critério de
   `sincronizar_clusters.extrair_verificado_em()`, nunca uma nota de
   secção `.fonte-inline`): `Verificado a [data] pela redação do
   <a href="/sobre.html#metodo">Tens Direito</a>`.

**Desvio deliberado da ordem proposta no brief original** ("Verificado
pela redação do Tens Direito a [data]", atribuição antes da data): essa
ordem quebra a contiguidade literal "Verificado a" + data de que
dependem 3 sítios — `sincronizar_clusters._REGEX_VERIFICADO`,
`auto_update_engine._REGEX_VERIFICADO_A` e o aviso (não bloqueante) de
`validar-conteudo.yml`. Colocando a atribuição **depois** da data, a
substring "Verificado a [data]" mantém-se 100% intacta e nenhuma das 3
regexes precisou de ser alterada — confirmado por
`tests/test_adicionar_autoria_artigos.py`, que reimporta as 2 regexes
reais e a função `extrair_verificado_em()` e verifica que continuam a
reconhecer o carimbo depois de alterado. Zero mudança de comportamento
fora do texto visível.

Páginas sem "Verificado a" próprio (`simulador-abono.html`,
`simulador-ase.html`, pillar pages como `p/apoios-escolares.html`) só
recebem o `author`/`publisher` no JSON-LD — não há carimbo nenhum para
atribuir.

Bug corrigido durante esta sessão (nunca chegou a `main`): a primeira
versão do script inseria `"publisher": {...}` sem vírgula a seguir,
partindo o JSON de 27 páginas — apanhado por validação local de JSON
antes do commit, corrigido no próprio script (vírgula em falta) e
reaplicado; `tests/test_adicionar_autoria_artigos.py` valida
explicitamente que o JSON continua parseável depois da inserção.

### Testes desta sessão

`tests/test_sobre_jsonld.py` (JSON-LD de `sobre.html`, secções
`#nvlabs`/`#metodo`, marcador `CONTACTO-EMAIL`, footer com link nas
páginas reais), `tests/test_atualizar_branding_nvlabs.py` (bootstrap +
sincronização idempotentes, isolado em memória) e
`tests/test_adicionar_autoria_artigos.py` (unidade + rede de segurança
sobre os artigos reais + compatibilidade das 2 regexes dependentes).
704 testes a passar (69 novos), ruff limpo.

### Verificação pós-merge (2026-07-03) — tipos de JSON-LD nas 27 páginas

Confirmado por varrimento real das 27 páginas de conteúdo: os únicos
tipos JSON-LD presentes são `FAQPage`, `HowTo`, `HowToStep`,
`BreadcrumbList`, `ListItem`, `Question`, `Answer` — **nenhuma tem um
objecto `Article` ou `WebPage` próprio**. O `author`/`publisher` da NV
Labs injectado por `adicionar_autoria_artigos.py` vive hoje só dentro do
`FAQPage` (schema.org-válido, `FAQPage` < `WebPage` < `CreativeWork`,
mas a Google Search Central documenta que a Pesquisa Google **não
consome autoria a partir de `FAQPage`** — só de tipos como `Article`/
`NewsArticle`/`BlogPosting` ou `WebPage`).

*Registado para o futuro, não implementado nesta sessão*: acrescentar
um objecto `Article` (ou `WebPage`) próprio por página de conteúdo, com
`author`/`publisher` → `.../sobre.html#nvlabs` e `datePublished`/
`dateModified` (a extrair do "Verificado a" real de cada página, nunca
inventada — mesma fonte que `sincronizar_clusters.extrair_verificado_em()`
já usa). Só faz sentido como sessão dedicada: exige decidir se
`datePublished` vem da tabela "PÁGINAS PUBLICADAS" deste ficheiro (nem
sempre com dia exacto, só mês) ou de outro sítio, e validar com o
Rich Results Test que o novo tipo não colide com o `FAQPage` existente
na mesma página.

### Fast-forward para `main` e limpeza de branch (2026-07-03)

`claude/new-session-2oea8g` (1 commit à frente de `origin/main` no
momento do merge) foi integrada em `main` por fast-forward puro, sem
PR, a pedido explícito do Nuno — mesmo padrão já usado noutras sessões
para respeitar a "REGRA ABSOLUTA — GIT". Nota técnica: o `main` local
desta sessão estava **desactualizado e com histórico não relacionado**
(`git merge-base` não encontrou ancestral comum com `origin/main` —
provavelmente um ref local nunca sincronizado desde uma reescrita de
histórico anterior); resolvido com `git checkout -B main origin/main`
antes do fast-forward — sem perda de trabalho, o `origin/main` remoto
já continha tudo o que havia de real.

Tentativa de apagar a branch remota `claude/new-session-2oea8g`:
**403 na API** (mesma limitação já registada nas revisões anteriores
deste ficheiro para `claude/nv-labs-branding-update-xq4kb4` e
`claude/cool-cannon-zn5nfy` — sem `gh` CLI nem ferramenta MCP com
permissão para apagar branches neste ambiente). Fica também para
apagar manualmente.

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
   O Shadow Mode (ponto 8) **nunca lê esse ficheiro** — corre
   `detectar_alertas` outra vez, em runtime, sobre o próprio checkout.
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
8. **Execução diária** (`run_shadow_daily.py` + `.github/workflows/shadow-daily.yml`)
   — liga os três módulos da Camada 7 e guarda 1 relatório/dia
   em `shadow_history/shadow_report_AAAA-MM-DD.md`. Guardrail próprio no
   workflow recusa (sem commitar) qualquer alteração fora de `shadow_history/`
   ou qualquer ficheiro de histórico apagado.
   Trigger: `workflow_run` assim que "Pipeline Diário" termina (sucesso ou
   falha — o Shadow lê o checkout directamente, nunca depende do pipeline
   ter tido sucesso), com `cron '0 8 * * *'` como rede de segurança caso o
   `workflow_run` nunca chegue a disparar. Guarda anti-duplicado própria (step
   "Verificar se já existe relatório de hoje"): se `shadow_report_<hoje>.md`
   já existir, sai sem gerar nem commitar de novo.
   `executar_shadow_daily` passa `paginas_analisadas`/`hora_execucao_utc` a
   `shadow_report_md.gerar_relatorio_markdown`, que marca "0 alertas" com
   mais de `LIMIAR_ANOMALIA_PAGINAS` (25) páginas analisadas como **anomalia
   explícita** em vez de "sistema estável" — "0" nunca é lido em silêncio
   como "está tudo bem" (ver `tests/test_run_shadow_daily_fonte_propria.py`).
   **Limitação conhecida, descoberta ao correr o pipeline real na Fase 5**:
   `_paginas_elegiveis()` usa `raiz.glob("*.html")` (não recursivo) — as 22
   páginas contadas são só as da raiz; as pillar pages em `p/*.html` nunca
   entram nesta contagem (mesma limitação pré-existente em
   `verificar_datas.py main()`, não introduzida por esta fase). Com 22 < 25,
   o limiar de anomalia nunca dispara no estado actual do repositório —
   registado para o futuro: baixar o limiar ou tornar `_paginas_elegiveis()`
   recursivo (`**/*.html`), não decidido, sem prazo.

**Diagnóstico "0 alertas" (2026-07-02)**: os relatórios `shadow_report_2026-07-01/02.md`
mostravam "Alertas analisados: 0" ao mesmo tempo que o pipeline tinha
Issues `data-expirada` (#37, #45) abertas. Investigação confirmou que
`run_shadow_daily.py` **já** corria a Camada 1 em runtime sobre o checkout
(nunca dependeu de `data/alertas_datas.json` gerado por outro workflow) — não
era um bug de leitura de dados. A causa real: o commit `eeefa1c` (correcção
de falsos positivos em `verificar_datas.py`, datado depois da criação de
#37/#45) tornou "0 alertas" genuinamente verdadeiro para o conteúdo actual
das páginas — confirmado correndo `detectar_alertas` localmente sobre o
repositório real. As Issues #37/#45 ficaram órfãs desse mesmo fix (fechadas
automaticamente pela máquina de estados — ver secção seguinte). `fonte-bloqueada`
(#47-#49) é um domínio totalmente à parte do Shadow Mode: vem de
`data/bloqueios.json`, escrito pela Camada 1 do scraper
(`scraper_playwright.py`), nunca passa por `verificar_datas.py`.

**Estado actual: sistema 100% observacional.** Nenhuma camada activa
auto-update real, nenhuma cria/fecha Issues por si própria, nenhuma escreve
HTML. Antes de alguma vez pôr `AUTO_UPDATE_HABILITADO = True`: rever
`shadow_history/` com dados reais acumulados, confirmar que os providers do
`source_adapter` já devolvem valores reais (não só placeholders) e fazer essa
mudança numa sessão manual dedicada, nunca de ânimo leve.

---

## MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS

Higiene de Issues automáticas (Fase 2 do robustecimento do Shadow Mode,
2026-07-02) — tudo vive em `pipeline-diario.yml` e nos scripts que chama; o
`shadow-daily.yml` continua sem tocar em Issues.

### `fonte-bloqueada`

`scripts/gerir_estado_fontes.py` (Step 1b do pipeline, logo a seguir ao
scrape) lê `data/bloqueios.json` (bloqueios de hoje) e o `data/estado_fontes.json`
anterior, e recalcula, por fonte monitorizada (as mesmas 7 slugs do step
"Detectar mudanças" — `SLUGS_MONITORIZADOS`): `{estado, dias_consecutivos_bloqueado,
ultima_ok}`. Uma fonte que não aparece nos bloqueios de hoje é tratada como
recuperada — reinicia o contador, mesmo vindo de `BLOQUEADO`. Puramente
funcional, não cria/fecha nenhuma Issue — só calcula e persiste o estado.

O Step 8 (Issues) lê `data/estado_fontes.json` já actualizado:
- só cria Issue `fonte-bloqueada` ao **3.º dia consecutivo** de bloqueio
  (`LIMIAR_DIAS_PARA_ISSUE`) — dias 1-2 ficam só no JSON, sem ruído no GitHub;
- enquanto o bloqueio persistir, comenta na Issue existente em vez de
  duplicar (dedup por slug no título, já existia);
- **fecho automático**: qualquer Issue `fonte-bloqueada` aberta cujo slug
  esteja `OK` no estado actual é fechada com um comentário
  ("Fonte recuperou a AAAA-MM-DD — fechado pelo pipeline"), independentemente
  de quantos dias esteve bloqueada.

### `data-expirada`

Sem ficheiro de estado dedicado — usa directamente `data/alertas_datas.json`
de hoje (já gerado pela Camada 1). Dedup por página no título já existia
(`REVER: <página>`, independente do tipo de padrão). Novo nesta fase: **fecho
automático** — qualquer Issue `data-expirada` aberta cuja página não apareça
nos alertas de hoje (porque foi corrigida manualmente, ou porque a própria
deteção melhorou, como em `eeefa1c`) é fechada com um comentário. Foi assim
que #37 (`amim.html`) e #45 (`manuais-escolares-mega.html`) — órfãs desde o
diagnóstico acima — fecharam sozinhas na primeira corrida seguinte do
pipeline. Regressão trancada por `tests/test_amim_real_nao_gera_alerta_issue_37`
e `test_manuais_escolares_mega_real_nao_gera_alerta_issue_45` em
`tests/test_verificar_datas.py` — carregam o HTML real das duas páginas, não
uma amostra sintética.

**Correcção adicional (#51/#52, 2026-07-03)**: `classificacao`/`decisao`
(Camadas 2-3) são metadados informativos anexados ao alerta — **não
influenciam se a Issue é criada**, só a Camada 1 (`_esta_suprimido`) decide
isso (confirmado ao investigar #51: o alerta tinha `"decisao": {"acao":
"IGNORAR"}` gravado no próprio `alertas_datas.json` e ainda assim gerou
Issue — não é um bug de leitura, é o desenho deliberado descrito no próprio
`verificar_datas.detectar_alertas()`). As Issues #51
(`apoio-extraordinario-renda.html`) e #52 (`porta-65.html`), abertas pelo
`workflow_dispatch` de verificação da sessão anterior, eram os dois casos
reais: citações permanentes ("posterior a 15 de março de 2023"/"celebrados
até 15 de março de 2023" — elegibilidade fixa do PAER; "revisão urgente em
agosto de 2025" — queixa à Provedoria; "Desde junho de 2023"/"Desde setembro
de 2024" — início das candidaturas contínuas ao Porta 65) que os marcadores
existentes não cobriam (`\bdesde\s+\d` exigia dígito logo a seguir a
"desde", sem aceitar um nome de mês pelo meio). `MARCADORES_HISTORICOS`
ganhou 3 padrões novos, ancorados aos matches reais — nunca supressão
global — e o `\bposterior a\b` novo foi desenhado com `\b` para não apanhar
"posterior até" (ressarcimento, sem data-limite) por sobreposição de
substring. 7 testes novos (incluindo regressão sobre o HTML real das duas
páginas e guarda contra sobre-supressão) em `tests/test_verificar_datas.py`.

**Correcção a uma frase anterior desta secção** (falsificada pela
investigação de #51 acima): não é verdade que uma correspondência marcada
como `STATIC_REFERENCE` por `classificar_datas.py` "nunca chega a gerar
alerta" — só é assim quando é a **mesma ocorrência** que a Camada 1 também
suprime. `_contexto_representativo()` usa `re.search()` (primeira
ocorrência da página) só para dar um exemplo à Camada 2, independente de
qual ocorrência fez `_pagina_tem_alerta()` devolver `True`; por isso um
alerta pode ter `"decisao": {"acao": "IGNORAR"}` gravado no seu próprio
`alertas_datas.json` e mesmo assim ter gerado Issue (foi o caso de #51,
confirmado nesta sessão) — a classificação descrevia a 1.ª ocorrência da
página (`"julho de 2026"`, correctamente inofensiva), não a ocorrência que
realmente disparou o alerta (`"março de 2023"`/`"agosto de 2025"`, ambas
sem marcador de supressão até esta correcção). `classificacao`/`decisao`
continuam a ser só metadados informativos, nunca gate de nada — a única
coisa que decide se uma Issue é criada é `verificar_datas._esta_suprimido`,
aplicado individualmente a cada ocorrência.

Testado em `tests/test_estado_fontes.py` (limiar de 3 dias, reset ao
recuperar, persistência ida-e-volta, fluxo `main()` isolado em `tmp_path` —
nunca toca no `data/estado_fontes.json` real).

---

## SCRAPER — ROBUSTEZ CONTRA BLOQUEIOS

Fase 3 do robustecimento do Shadow Mode (2026-07-02). Princípio: **nunca
disfarçar `BLOQUEADO` como `OK`** — o objectivo é reduzir a frequência real
de bloqueio e ter um modo degradado honesto, não esconder bloqueios.

1. **Perfil de browser realista** (`scraper_playwright.py`, `main()`):
   `playwright-stealth` (`Stealth().apply_stealth_sync(context)`) aplicado ao
   `BrowserContext` antes de abrir a página — mascara `navigator.webdriver` e
   outros sinais triviais de automação; UA Chrome estável actualizado,
   `locale="pt-PT"` (já existia) + `timezone_id="Europe/Lisbon"` (novo).
   Não é suposto contornar nada mais forte do que uma verificação
   superficial — só reduzir bloqueios triviais nos runners do GitHub.
2. **Retries com backoff + jitter** (`TENTATIVAS_BLOQUEIO = 3`,
   `ESPERA_MIN_S`/`ESPERA_MAX_S` = 30–120s): uma fonte só é `BLOQUEADO` no
   dia se as 3 tentativas — cada uma com a página recebida E classificada
   pela Camada 1 (`classificador_resposta.classificar_resposta`) — falharem
   todas. Espera aleatória entre tentativas, nunca fixa. Distinto dos
   retries já existentes em `_tentar_goto` (falha de rede/timeout, 3
   tentativas com backoff exponencial curto) — este novo nível trata de
   conteúdo recebido mas classificado como bloqueado (recaptcha, login
   page), não de falhas de navegação.
3. **Hora aleatória**: `pipeline-diario.yml` ganhou o step "Espera aleatória
   antes do scrape" (`sleep $((RANDOM % 1800))`), só em disparos por cron
   (`workflow_dispatch` continua imediato, para não atrasar testes) — scraping
   exactamente às 06:00 UTC todos os dias é um padrão fácil de bloquear.
4. **Fallback Wayback Machine — modo degradado honesto** (`scripts/wayback_fallback.py`,
   módulo puro, sem `requests` nem I/O próprios — `fetch_json` é sempre
   injectado, testado sem rede em `tests/test_scraper_fallback.py`): só
   chamado depois das 3 tentativas directas falharem. Consulta
   `https://archive.org/wayback/available`; se existir snapshot com
   ≤`JANELA_DIAS_SNAPSHOT_VALIDO` (7) dias, `scraper_playwright._tentar_fallback_wayback`
   obtém o HTML do snapshot, extrai conteúdo com os mesmos selectores da
   fonte e guarda um resultado com `"status": "ok_via_arquivo"`,
   `"modo": "arquivo"`, `"data_snapshot"` e `"url_snapshot"` — usado **só**
   para deteção de mudança por hash, nunca como fonte de factos para
   conteúdo. Este resultado **nunca** escreve em `data/bloqueios.json` — o
   dia não conta como bloqueado na máquina de estados de fontes (secção
   anterior), mas fica registado em `data/scraped/avisos.log`
   (`modo_arquivo:snapshot=...:dias=...`) para auditoria. Sem snapshot
   recente, cai no caminho `BLOQUEADO` normal (`_registar_bloqueio`) — nunca
   finge que a fonte respondeu.
5. **Fontes estruturadas alternativas — investigação concluída em
   2026-07-02, testada ao vivo num runner real** (`workflow_dispatch`
   dedicado e temporário, apagado depois de recolher os resultados) —
   ver secção "FONTES — ALTERNATIVAS POR FONTE" para a tabela completa e
   o veredicto por fonte. Resumo: nenhuma das 3 fontes migrou — para
   `seg_social_abono`/`seg_social_rsi` não foi encontrado candidato
   equivalente acessível; `iefp_desemprego` revelou-se um falso positivo
   do próprio classificador (ver essa secção), não uma fonte bloqueada.

Testes: `tests/test_scraper_fallback.py` (15 testes, mocks — sem rede real),
cobre snapshot recente/antigo/inexistente, falha de rede na consulta
Wayback, e a garantia de que a decisão nunca devolve `"estado": "OK"`
directamente (só `OK_VIA_ARQUIVO` ou `BLOQUEADO`).

---

## FONTES — ALTERNATIVAS POR FONTE

Investigação de 2026-07-02, feita num `workflow_dispatch` temporário
(`diagnostico-fontes-temp.yml`, apagado no fim — nunca ficou como
workflow permanente) porque `WebFetch`/`curl` a partir do ambiente de
sessão levam bloqueio a domínios `.gov.pt` fora da lista permitida; só
é fiável testar isto a partir de um runner real do GitHub Actions.

| Fonte | Candidato testado | Acessível do runner? | Equivalência | Decisão |
|---|---|---|---|---|
| `seg_social_abono` | `eportugal.gov.pt` (sitemap) | Sitemap devolve só 3 sub-sitemaps Liferay (`www2.gov.pt/sitemap.xml?...`) sem URLs directos — SPA Next.js, provavelmente exige JS | Não avaliável sem mais investigação | Não migrado |
| `seg_social_abono` / `seg_social_rsi` | `seg-social.pt/guias-praticos` (PDFs) | Página responde 200 mas 0 links `.pdf` encontrados no HTML estático — lista de guias é provavelmente carregada via JS/AJAX | Nenhuma (sem PDFs visíveis a um pedido simples) | Não migrado |
| `seg_social_abono` / `seg_social_rsi` | `dados.gov.pt` (API CKAN `package_search`) | 404 — endpoint testado não existe nesta instância (portal não é CKAN "de raiz" nesse caminho, ou a API vive noutro caminho) | Não avaliável | Não migrado |
| `seg_social_abono` / `seg_social_rsi` | **A própria URL original**, mas via `urllib` simples (sem Playwright) | Sim, HTTP 200 — mas o servidor redirecciona sempre para `seg-social.pt/ptss/pssd/home?r=...` ("Segurança Social Direta", portal de autenticação, 241 chars úteis) | Nenhuma — mesmo comportamento com ou sem Playwright/stealth | Confirma que **não é bloqueio a IP/fingerprint de bot**: é o próprio servidor a redireccionar pedidos sem sessão válida para o gateway de autenticação, para qualquer cliente. Sem solução simples do lado do cliente. |
| `iefp_desemprego` | **A própria URL original**, via `urllib` simples | Sim, HTTP 200, 89 515 chars, título real "Subsídio de Desemprego - IEFP, I.P.", conteúdo real confirmado (17× "subsídio de desemprego", 15× "IAS", 3× "prazo") | **Total** — é a página real, completa | **Não é uma fonte bloqueada.** `classificador_resposta._MARCADORES_DESAFIO` apanha a substring `"recaptcha"` em qualquer ponto do HTML; a única ocorrência na página é um `<script src="https://www.google.com/recaptcha/api.js?...">` passivo (provavelmente de um widget de contacto no template do site, nada a ver com bloqueio de conteúdo) — zero ocorrências de `g-recaptcha`, `grecaptcha.execute`, `challenge`, `captcha-container` ou qualquer outro sinal real de desafio. **Falso positivo confirmado no classificador, não uma fonte inacessível.** |

**Porque não houve Fase de migração (piloto) nesta sessão**: o plano de
migração do robustecimento (secção "SCRAPER — ROBUSTEZ CONTRA
BLOQUEIOS") pressupõe encontrar uma **fonte alternativa** com
equivalência total. Isso não aconteceu para nenhuma das 3 — para
`seg_social_abono`/`seg_social_rsi` porque nenhum candidato testado
devolveu conteúdo utilizável, e para `iefp_desemprego` porque o
problema real não é a fonte (que está perfeitamente acessível) mas sim
uma falha do nosso próprio classificador. Migrar `iefp_desemprego`
"para si própria" não faz sentido — o que falta é uma correcção
cirúrgica e testada a `classificador_resposta._MARCADORES_DESAFIO`
(distinguir um `<script src="recaptcha/api.js">` passivo de um desafio
real, ex.: só marcar bloqueio se houver também `g-recaptcha`,
`grecaptcha.execute` ou o resto do conteúdo for insuficiente). **Ainda
não corrigido** — é uma mudança de comportamento à parte, com o seu
próprio raciocínio e testes, deliberadamente fora do âmbito desta
investigação (que era sobre migrar para fontes alternativas, não sobre
rever a lógica do classificador). Registado para sessão dedicada.

**Corrigido na sessão seguinte (2026-07-03)** — ver secção
"CLASSIFICADOR — VERIFICAÇÃO POSITIVA" logo abaixo: em vez de só
ajustar `_MARCADORES_DESAFIO_FORTE`, o classificador passou a verificar
o conteúdo esperado primeiro.

*Registado para o futuro*: confirmar se `eportugal.gov.pt`/
`seg-social.pt/guias-praticos` têm conteúdo relevante por trás de
JavaScript (precisaria de Playwright em vez de `urllib` simples para
confirmar) antes de descartar definitivamente como candidatos para
`seg_social_abono`/`seg_social_rsi`; encontrar o caminho correcto da
API de `dados.gov.pt` (o testado, `/api/3/action/package_search`,
devolve 404 nesta instância).

---

## CLASSIFICADOR — VERIFICAÇÃO POSITIVA

`scripts/classificador_resposta.py` reescrito (2026-07-03): em vez de só
detectar sinais de bloqueio, verifica primeiro se o conteúdo esperado
está presente — é essa verificação positiva que resolve o falso
positivo do IEFP documentado na secção anterior.

- `FonteConfig` ganhou `ancora_conteudo` (tuple de 2-3 frases que uma
  página legítima da fonte tem sempre — ex. `iefp_desemprego`:
  `"subsídio de desemprego"`) e `metodo` (`"http"` ou `"playwright"` —
  ver secção seguinte). Ambos vazios/`"playwright"` por omissão: fontes
  não migradas para este sistema mantêm o comportamento anterior a
  esta secção sem qualquer alteração.
- Nova ordem de decisão em `classificar_resposta()`:
  1. Status HTTP de bloqueio (401/403/407/429/503) — sempre BLOQUEADO,
     nem as âncoras o sobrepõem (um WAF pode devolver texto coincidente).
  2. Âncoras todas presentes + `texto_util >= min_chars_uteis` → **OK**
     de imediato, independentemente de qualquer marcador tipo
     `recaptcha` aparecer noutro ponto da página (script incluído,
     não desafio activo).
  3. Sem confirmação positiva: só BLOQUEADO com um sinal real — texto
     útil insuficiente, redirect/título de login, ou um marcador de
     desafio forte (`_MARCADORES_DESAFIO_FORTE`) numa página
     `< 15KB` (`LIMIAR_TAMANHO_PEQUENO`) ou já com título de login.
  4. Sem nenhum sinal real e a fonte tem `ancora_conteudo` configuradas
     mas não encontradas → **MUDOU** — a fonte respondeu, mas o
     conteúdo esperado desapareceu (revisão manual), nunca disfarçado
     de BLOQUEADO.
  5. Fontes sem `ancora_conteudo` (`()`, omissão): comportamento
     idêntico ao anterior a esta secção — nunca ficam `MUDOU` por esta
     via, só OK/BLOQUEADO como antes.

Testado com os 5 HTML reais obtidos num runner via `workflow_dispatch`
temporário (nunca reescritos à mão, `tests/fixtures/*.html`): a página
real do IEFP (87KB, "subsídio de desemprego" 17×, script recaptcha
passivo) classifica OK de imediato; a shell de login do portal
seg-social (13KB, ~241 chars úteis, sem as âncoras) nunca classifica
OK; o conteúdo real dos deep-links do portal novo (ver secção
seguinte) classifica OK. `tests/test_classificador_resposta.py` — 19
testes (12 pré-existentes inalterados + 7 novos), incluindo a garantia
de que uma fonte sem âncoras configuradas nunca fica MUDOU.

## SEG-SOCIAL — ESTRATÉGIA DE FETCH

Contexto: seg-social.pt está em migração — o portal antigo (URLs
planas) coexiste com o novo `/ptss/pssd/` (SPA com sessão `dswid`).
Confirmado num runner real (`workflow_dispatch` temporário, apagado no
fim, mesmo padrão desta secção):

| Fonte | URL testada | Resultado |
|---|---|---|
| `seg_social_abono`/`seg_social_rsi` | URLs planas (`abono-de-familia-para-criancas-e-jovens`, `rendimento-social-de-insercao`), via `urllib` simples e via Playwright+stealth | **Sempre** redirecciona para `seg-social.pt/ptss/pssd/home?r=...` (gateway de autenticação) — confirma que não é bloqueio a IP/fingerprint: é o próprio servidor a negar sessão anónima nessas rotas, com qualquer cliente |
| `seg_social_abono`/`seg_social_rsi` | deep-links do portal novo (`/ptss/pssd/menu/familia/desenvolvimento-criancas-jovens/abono-familia-criancas-jovens`, `/ptss/pssd/menu/acao-social/apoios-respostas-sociais/rendimento-social-insercao`), via Playwright com espera explícita pela âncora (`page.wait_for_function`, não só `networkidle`) | Conteúdo real servido sem sessão — "abono de família" 19×, "rendimento social de inserção" 11× |
| `iefp_desemprego` | URL original, via `urllib` simples | Página real e completa (já confirmado na secção anterior) |

Aplicado a `scripts/scraper_playwright.py`:

- `iefp_desemprego`: `metodo="http"` — nova `scrape_http()` (requests +
  headers realistas, mesmo padrão de retries/jitter de
  `scrape_playwright`), corre **antes** de o browser Chromium sequer
  abrir, sem depender dele. `main()` separa `FONTES_PLAYWRIGHT` em
  `fontes_http`/`fontes_pw` por `FonteConfig.metodo`.
- `seg_social_abono`/`seg_social_rsi`: `metodo="playwright"`
  (inalterado), mas a `url` em `FONTES_PLAYWRIGHT` passou a ser o
  deep-link do portal novo — nunca mais a URL plana, que nunca vinga.
  `_obter_html()` ganhou o parâmetro `ancora`: quando a fonte tem
  `ancora_conteudo`, espera explicitamente que a frase apareça no DOM
  (`page.wait_for_function`) em vez do `time.sleep(5)` fixo anterior —
  necessário porque a SPA reporta "carregada" (`networkidle`) antes do
  conteúdo real renderizar.
- `dominios_login` das 2 fontes ganhou `"seg-social.pt/ptss/pssd/home"`
  — apanha só o gateway de autenticação, deliberadamente restrito para
  nunca apanhar os deep-links `/ptss/pssd/menu/...` usados como alvo.

**MUDOU vs BLOQUEADO — nunca disfarçados um do outro**: nova
`_tratar_nao_ok()` (chamada por `scrape_playwright` e `scrape_http`
depois de esgotar `TENTATIVAS_BLOQUEIO`) bifurca por estado — BLOQUEADO
segue o caminho já existente (fallback Wayback, depois
`data/bloqueios.json`); MUDOU nunca tenta Wayback (a fonte respondeu,
só o conteúdo mudou) e nunca escreve em `bloqueios.json` — não conta
como dia bloqueado na máquina de estados de `gerir_estado_fontes.py` —
só regista em `avisos.log` via nova `_registar_mudanca_estrutural()`.

**Gap conhecido, não fechado nesta sessão**: MUDOU não cria nenhuma
Issue — só o log em `avisos.log`. A máquina de estados de
`fonte-bloqueada` só entende BLOQUEADO/OK; não existe hoje um tipo de
Issue "conteúdo mudou de forma inesperada" nem um consumidor de
`avisos.log` para o padrão `mudanca_estrutural:`. Registado para o
futuro, sem prazo.

**Aviso de migração viva**: as URLs planas antigas podem deixar de
responder de todo, sem aviso, a qualquer momento — o classificador
nunca as disfarça de BLOQUEADO nesse caso: sem âncoras encontradas e
sem sinal real de bloqueio, o resultado é sempre MUDOU (ver secção
anterior).

**Verificação no pipeline real (2026-07-03) — resultado misto, honesto**:
disparado `pipeline-diario.yml` em `main` depois de aplicar esta secção
(commit `ef686b9`). `iefp_desemprego` confirmou-se OK de imediato
(`metodo="http"`, âncora encontrada) — Issue #49 (`fonte-bloqueada`)
fechou-se sozinha pela máquina de estados, exactamente como esperado.
`seg_social_abono`/`seg_social_rsi` **continuaram BLOQUEADO** no
pipeline real, ao contrário do runner de diagnóstico: as 3 tentativas
de cada uma navegaram para o mesmo deep-link, mas caíram sempre no
gateway de login (`titulo_login:seguranca social direta`,
`texto_util=173<min=500`, âncora nunca apareceu no DOM em 15s) — Issues
#47/#48 continuam abertas, correctamente (o classificador nunca
disfarçou o bloqueio real de OK). `data/estado_fontes.json` confirma:
`iefp_desemprego` → `OK`, `seg_social_abono`/`seg_social_rsi` → `BLOQUEADO`
(2 dias consecutivos, `ultima_ok: null` — nunca chegaram a OK com este
sistema).

**Culpado isolado e corrigido (2026-07-03, sessão seguinte)**: a
hipótese acima (stealth) estava errada. Novo `PerfilBrowser`
(`stealth`/`headers_custom`/`viewport_fixo`, todos `True` por omissão —
comportamento de produção inalterado para qualquer fonte sem entrada em
`_PERFIL_POR_SLUG`) + `_criar_context()` em `scraper_playwright.py`
tornam o perfil de browser configurável por fonte; `main()` agrupa
`fontes_pw` por perfil e abre um `browser.new_context()` à parte por
grupo. Workflow de diagnóstico temporário (`workflow_dispatch`, apagado
no fim) testou os 2 deep-links seg-social × 4 perfis isolados (nu,
só stealth, só headers, só viewport) num runner real:

| Perfil | `seg_social_abono` | `seg_social_rsi` |
|---|---|---|
| nu | ✓ passou (85142 chars, âncora 19×) | ✓ passou (80173 chars, âncora 11×) |
| só stealth | ✓ passou | ✓ passou |
| **só headers** | **✗ erro 500 real do backend** (`/ptss/fraw/errors/500?dswid=...`) | **✗ idêntico** |
| só viewport | ✓ passou | ✓ passou |

O culpado é `extra_http_headers` (`Accept-Language`/`Accept` customizados)
— não o `Stealth()`, como se suspeitava. Não é sequer um redirect de
login: o backend do portal novo devolve genuinamente um erro 500 quando
recebe esses headers nesta rota. `stealth` e `viewport` fixo passaram
isoladamente sem qualquer problema. `_PERFIL_POR_SLUG` fixa
`headers_custom=False` só para `seg_social_abono`/`seg_social_rsi`
(mantêm `stealth=True`/`viewport_fixo=True`, tal como as restantes
fontes); nenhuma outra fonte foi tocada.

**Confirmado no pipeline real**: `seg_social_abono`/`seg_social_rsi`
ficaram OK de imediato (sem retries, ~4-7s cada, âncora e título
correctos via JS) — Issues #47/#48 fecharam-se sozinhas pela máquina de
estados. `data/estado_fontes.json` confirma as 7 fontes monitorizadas
em `OK`.

**Bug lateral descoberto e corrigido durante esta verificação**: a
1.ª tentativa de confirmação (mesmo dia, pipeline disparado 2× por
`workflow_dispatch` manual — uma vez antes da correcção, outra depois)
mostrou o scrape genuinamente OK mas as Issues #47/#48 não fecharam.
Causa: `data/bloqueios.json` ainda tinha entradas de **hoje** da
corrida anterior (antes da correcção) — `_registar_bloqueio` só
substituía a entrada do dia ao registar um **novo** bloqueio, nunca a
removia quando a fonte simplesmente recuperava; `gerir_estado_fontes.py`
compara só por data (`YYYY-MM-DD`), por isso via a entrada antiga como
"bloqueado hoje" apesar do scrape actual ter tido sucesso. Nova
`_limpar_bloqueio_hoje(slug)`, chamada no caminho OK de
`scrape_playwright()`/`scrape_http()`: remove qualquer entrada de hoje
dessa fonte em `bloqueios.json` quando recupera. Só se manifesta em
corridas múltiplas no mesmo dia (`workflow_dispatch` manual repetido)
— o pipeline automático corre uma vez/dia via cron, onde este bug nunca
se manifestava na prática. Testado (579 testes a passar) e confirmado
no pipeline real seguinte: #47/#48 fecharam correctamente.

---

## IDEIAS RECUPERADAS — cascata de fontes (cool-cannon)

Análise de 2026-07-03 de uma branch órfã antiga (`claude/cool-cannon-zn5nfy`),
divergida de `main` desde antes de toda a reorganização de arquitectura de
informação (~19 790 linhas de diferença — remergear directamente apagaria
trabalho posterior). Cherry-pick **proibido nesta sessão**: o código foi
escrito contra um estado anterior do `source_adapter`/classificador e
aplicar-se-ia limpo sem necessariamente estar certo hoje. Em vez disso, os 2
commits reais da branch (`c765017`, `29b6133` — o resto já estava mergeado
ou é ruído de diagnóstico) foram lidos e resumidos aqui; qualquer
reimplementação parte deste resumo, escrita de raiz sobre o código actual,
numa sessão dedicada.

### O que a cascata fazia

`scripts/cascata_fontes.py` (nunca chegou a `main`): para cada **rubrica**
(um valor publicado, ex.: `ias_2026`), definia uma lista ORDENADA de passos
por robustez decrescente — `RubricaConfig.cascata`:

1. **LEGISLATIVA** — fonte primária (portaria/DRE), a mais estável.
2. **SERVICO** — página-serviço (seg-social.pt, iefp.pt), confirmação.
3. **CONGELADO** — fallback final: `ValorCongelado` com o último valor
   verificado por humano + data dessa verificação.

`resolver_rubrica()` percorria a cascata por ordem: para cada passo, chamava
um `fetcher` injectado + **a mesma** `classificador_resposta.classificar_resposta()`
(Camada 1, inalterada até hoje) — só aceitava um valor de uma fonte `OK`;
`BLOQUEADO` (ou o extractor não encontrar o valor esperado numa página
genuinamente `OK`) fazia cair para o passo seguinte, nunca produzia um
valor. Se a cascata inteira falhasse, devolvia sempre o congelado — nunca
`SEM_VALOR` havendo um congelado definido. `resolucao.publicavel` só era
`False` no caso limite de não haver cascata nem congelado (não devia
acontecer na prática).

`scripts/rubricas_config.py` tinha a única rubrica configurada, `ias_2026`:
- **LEGISLATIVA**: `diariodarepublica.pt/dr/detalhe/portaria/480-a-2025-993056222`
  (o permalink da própria portaria, não uma página de pesquisa) — testado
  via Playwright num runner real em 2026-06-30: 200, 3943 chars, "537,13"
  presente no texto renderizado.
- **SERVICO**: `seg-social.pt/abono-de-familia` (fallback).
- **CONGELADO**: `"537,13"`, verificado por humano a 2026-06-28.

`tests/test_cascata_fontes.py` tinha 11/11 testes a passar (não trazidos,
ficaram só na branch).

### Comparação com o estado actual

| Peça da cascata | Equivalente hoje | Cobre o mesmo? |
|---|---|---|
| Classificação OK/BLOQUEADO por passo | `classificador_resposta.py` (Camada 1, inalterado) | Sim — compatibilidade total, é a mesma função |
| Fallback quando uma fonte falha | `wayback_fallback.py` (Fase 3 desta sessão) | **Não** — mecanismo diferente: Wayback é "snapshot arquivado da mesma URL", nunca fonte de factos (`OK_VIA_ARQUIVO` só serve deteção de mudança); a cascata é "outra fonte OFICIAL diferente para o mesmo valor". Complementares, não sobrepostos. |
| "Qual é o valor oficial?" por alerta | `source_adapter.py` (Camada 6) | Só na intenção — `source_adapter` continua com providers 100% placeholder (`encontrado=False` sempre), nunca ligado ao orquestrador; a cascata era a implementação real que faltava, mas com uma arquitectura diferente (config expĺicita por rubrica vs. dispatch por palavra-chave do alerta) |
| Fallback SERVICO da rubrica IAS (`seg-social.pt/abono-de-familia`) | Secção "FONTES — ALTERNATIVAS POR FONTE" (esta sessão) | **Confirmado morto**: esta sessão provou, com `urllib` simples e com Playwright+stealth, que este URL redirecciona sempre para o portal de autenticação — o passo SERVICO desta rubrica nunca resolveria, teria de ser reconfigurado ou removido antes de qualquer reimplementação |

### Veredicto

O **conceito** (cascata ordenada de fontes oficiais com fallback seguro
para um valor congelado, nunca aceitando um valor de fonte não-`OK`) é
sólido e preenche uma lacuna real — é a peça que falta para `source_adapter.py`
deixar de ser só placeholders. **Não vale a pena reimplementar agora**: o
único fallback SERVICO configurado está confirmado morto por esta sessão,
o `source_adapter.py` continua sem nenhum consumidor real (nunca ligado ao
orquestrador — mesma lacuna que já tinha), e o objectivo actual do projecto
é consolidar a camada de observação (Shadow Mode, máquina de estados,
simulação de carimbo) antes de investir em infra-estrutura de resolução de
valores para um `AUTO_UPDATE_HABILITADO` que continua — e deve continuar —
`False`. Registado para quando essa prioridade mudar: reimplementar de
raiz, reutilizando `classificador_resposta.py` tal como está, tornando o
resolver ciente de `OK_VIA_ARQUIVO` (tratar como não-resolutivo, igual a
`BLOQUEADO`, nunca como fonte de valor), e revalidando cada URL de fonte
antes de a configurar.

---

## REVALIDAÇÃO DE CARIMBO (proposta com travão, simulada e desligada)

Fase 4 do robustecimento do Shadow Mode (2026-07-02). Responde ao
objectivo de "actualização automática de datas expiradas" sem violar a
regra de nunca activar auto-update de valores.

**Distinção crítica:**
- **Valores** (montantes, escalões, prazos legais) — continuam 100%
  manuais. `decisao_datas.AUTO_UPDATE_HABILITADO` não é tocado por nada
  nesta fase.
- **Carimbo "Verificado a DD de mês de AAAA"** — é a única coisa
  candidata a refresh automático, e só quando for *honesto*: a fonte
  oficial de que a página depende foi verificada hoje pelo scraper
  (`OK`, nunca `OK_VIA_ARQUIVO`) **e** o hash SHA-256 dessa fonte está
  inalterado. Nesse caso "verificado" é literalmente verdade — o sistema
  confirmou que nada mudou na fonte.

**Tudo o que existe nesta fase está desligado por omissão:**

1. Nova flag `decisao_datas.REVALIDACAO_CARIMBO_HABILITADA = False` —
   mesmo aviso da flag `AUTO_UPDATE_HABILITADO` já existente: nunca
   mudar sem sessão manual dedicada.
2. `data/pagina_fonte.json` — mapeamento manual página HTML → fonte(s)
   do scraper de que depende (ex.: `"rsi.html": ["seg_social_rsi"]`).
   Curado à mão, como `data/clusters.json` — não é escrito pelo
   pipeline. Sem entrada no mapeamento, a página nunca é elegível.
3. `auto_update_engine.py` ganhou a operação `aplicar_refresh_carimbo`
   (continua sandbox, só memória, nunca escreve ficheiros): substitui só
   a data dentro de "Verificado a ..." + `dateModified` do JSON-LD, nada
   mais. Confinamento verificado por `_apenas_carimbo_alterado` (mascara
   as duas zonas regex e compara o resto — mesmo princípio de
   `gerar_noticias._verificar_escrita_confinada()`, adaptado a zonas por
   regex em vez de marcadores de comentário); qualquer diff fora delas
   aborta com `ABORTED_ESCRITA_FORA_DE_ZONA` em vez de aplicar.
   `elegivel_refresh_carimbo(fonte_estado, hash_inalterado)` é a função
   pura de elegibilidade, reutilizável sem chamar a operação em si.
4. **Shadow Mode simula esta decisão diariamente**: `run_shadow_daily.calcular_carimbos_elegiveis`
   lê `data/pagina_fonte.json` + `data/estado_fontes.json` +
   `data/scraped/*.json` (todos escritos pelo pipeline, nunca por este
   script) e devolve as páginas que SERIAM elegíveis hoje — nunca liga a
   flag, nunca chama `aplicar_refresh_carimbo`, só a verificação pura. O
   relatório ganha a secção "Carimbos elegíveis para revalidação
   (simulado)".
   **Simplificação assumida, a rever no período de observação**: "hash
   inalterado" compara o scrape de hoje com o de ontem (ambos já
   existem em `data/scraped/{slug}_AAAA-MM-DD.json`, escritos todos os
   dias independentemente de mudança) — é uma aproximação de "a fonte
   não mudou recentemente", não o ideal "desde a última edição manual
   da própria página". Refinar isso (ex.: guardar o hash no momento em
   que um humano editou o carimbo) é trabalho para quando a activação
   estiver a ser considerada a sério, não antes.
5. **Critério de activação — decisão do Nuno, nunca do Claude Code**: só
   ligar `REVALIDACAO_CARIMBO_HABILITADA` depois de ≥14 relatórios
   shadow consecutivos com simulações correctas (zero falsos elegíveis —
   confirmar manualmente contra as páginas listadas) e com as fontes
   correspondentes maioritariamente `OK` (a secção "SCRAPER — ROBUSTEZ
   CONTRA BLOQUEIOS" tem de estar a reduzir bloqueios primeiro, senão
   quase nada chega a ser elegível).

Testes: `tests/test_auto_update_engine.py` (elegibilidade — só `OK` +
hash igual; `OK_VIA_ARQUIVO`/`BLOQUEADO` nunca elegíveis; flag desligada
devolve `SKIPPED_SAFE_MODE` sem tocar no conteúdo; confinamento aborta
alteração fora de zona; determinismo) e `tests/test_carimbos_elegiveis.py`
(simulação diária isolada em `tmp_path` — múltiplas fontes por página,
hash mudado, sem scrape de ontem, página sem mapeamento, ordenação,
nunca escreve nada).

---

*Última revisão: 2026-06-28 — CSI e PSU publicadas; fact-checking completo; GSTACK adicionado; PSU destaque; datas sazonais; simulador abono (fix múltiplas crianças); simulador ASE completo; plano impacto PSU documentado*

---

*Última revisão: 2026-07-01 — corrigido bug de dedup em `pipeline-diario.yml` que gerava Issues duplicadas (data-expirada, fonte-bloqueada, fonte-alterada, divergências de valores); 8 Issues duplicadas fechadas*

---

*Última revisão: 2026-07-02 — investigado um `<system-reminder>` suspeito recebido numa sessão anterior; busca exaustiva ao repositório (186 ficheiros trackeados, `data/scraped/`, `shadow_history/`, log do scraper) não encontrou nenhum vestígio de prompt injection — conclusão: artefacto do harness, não conteúdo importado; adicionado guardrail permanente `scripts/verificar_injecao.py` (procura padrões de injection em `data/` e `shadow_history/`, só leitura, nunca executa o que encontra) + novo job em `integridade.yml`; nova secção "SEGURANÇA — PROMPT INJECTION EM DADOS IMPORTADOS"; 9 testes novos em `tests/test_verificar_injecao.py`, 409 testes a passar*

---

*Última revisão automática: 2026-07-03*

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

---

*Última revisão: 2026-07-02 — Fase 1 do sistema de notícias: `data/noticias.json` passa a ser a fonte de verdade (antes era o próprio `noticias.html`); migração única (`scripts/migrar_noticias.py`) dos 15 registos legados — 1 descartado (placeholder vazio, resíduo de bug antigo), 4 duplicados removidos (mantida sempre a data mais antiga), 10 itens finais; `gerar_noticias.py` reescrito com dedup (`encontrar_duplicado()` — título normalizado + URL específico, nunca homepage genérica sozinha), observabilidade completa no log (candidatos por feed, top 3, rejeições, vencedor) e "nenhuma notícia hoje" como resultado aceitável; `noticias.html` passa a ser gerado do JSON (destaque + arquivo por mês, ordem por data real desc) em vez de patch incremental; `index.html` (`NOTICIA-HOME`) mostra 2-3 itens em vez de 1; corrigidos 3 bugs pré-existentes de correspondência de classes em `noticias.html` (JS de paginação apontava a `.noticia-card` em vez de `.arquivo-card`, `.arquivo-card` não tinha CSS nenhum, `.cat-badge.apoios` nunca correspondia a `cat-apoios` real, `#destaque-wrap` não existia) — confirmado no browser via Playwright (contagens e paginação a verem os 9/9 itens reais, badges com cor, destaque a esconder/mostrar ao filtrar); guardrail de `escrever_ficheiro_seguro()` endurecido para allow-list estrita nos dois sentidos; `verificar_injecao.py` confirmado a cobrir `data/noticias.json` sem alterações (já estava dentro de `data/`); 453 testes a passar (49 novos); idempotência de `regenerar_noticias_html()`/`atualizar_index_home()` confirmada nos ficheiros reais; passo de diagnóstico de feeds candidatos registado para a Fase 2, não feito ainda*

---

*Última revisão: 2026-07-02 — dois bugs pós-Fase 1 corrigidos: 1) `main()` de `gerar_noticias.py` terminava sem regenerar `noticias.html`/`index.html` quando não havia notícia nova no dia — extraída `sincronizar_saidas()` como ponto único de regeneração, chamado sempre no fim (com ou sem vencedor) e também por `migrar_noticias.py` no fim da migração; novo `--sync` para correr manualmente sem tocar no RSS; 2) a lupa da pesquisa do hero (`index.html`) era um `<span>` decorativo sem qualquer interactividade — passou a `<button>` real com `aria-label` e touch target 44px; e descoberto (e corrigido) que tanto os chips como a nova lupa tinham os resultados fechados no mesmo clique que os abria, pelo listener global "fechar ao clicar fora" de `pesquisa.js` — corrigido com `event.stopPropagation()` nos handlers dos botões, documentado como padrão obrigatório para qualquer botão futuro de pesquisa por clique; Enter no campo já funcionava (é `keydown`, não sofre do mesmo bug) mas ganhou um handler explícito por robustez; tudo confirmado com Chromium real via Playwright (viewport mobile); novo `tests/test_pesquisa_hero.py` extrai o JS/CSS reais do `index.html` (não uma cópia), incluindo teste de regressão a confirmar que clicar mesmo fora continua a fechar os resultados; 462 testes a passar*

---

*Última revisão: 2026-07-02 — pesquisa interna reformulada: ranking em 3 camadas nunca misturadas (título → descrição → keywords), ordem alfabética determinística dentro de cada camada, limite de 8 resultados; cada resultado ganhou excerto com o termo destacado (`<mark>`) — mostra o contexto do match quando não está no título — e badge do cluster/"Ferramenta"; mínimo de 2 caracteres antes de pesquisar; estado vazio explícito com link para `/#guias-de-apoios`; dropdown com `max-height: 60vh` + scroll interno (hero e nav); `cluster`/`clusterNome`/`tipo` de cada página em `pesquisa.js` verificados contra `data/clusters.json` por `tests/test_pesquisa_indice.py` (fonte única para essa parte dos dados — título/descrição/keywords continuam curados à mão); `descricao` de cada página extraída das meta descriptions reais, nunca inventada; CSS de resultado partilhado movido para `assets/css/nav.css`; confirmado no browser real (Chromium/Playwright, viewport mobile): "sub" com ranking correcto, "psu" a devolver o cluster inteiro, "xyz" com estado vazio, 1 carácter sem disparar; 557 testes a passar (95 novos), idempotência confirmada, ruff limpo*

---

*Última revisão: 2026-07-02 — robustecimento do Shadow Mode e higiene de Issues (Fases 0-5), disparado por "0 alertas" nos relatórios shadow enquanto o pipeline tinha Issues `data-expirada` abertas. Fase 0: diagnóstico confirmou que `run_shadow_daily.py` já corria a Camada 1 em runtime (não dependia de `data/alertas_datas.json` doutro workflow) e que "0" era genuinamente correcto — o commit `eeefa1c` tinha corrigido os falsos positivos que geraram #37/#45, que ficaram órfãs. Fase 1: relatório ganhou secção de proveniência (páginas analisadas + hora) e marca 0 alertas com >25 páginas como anomalia explícita; `shadow-daily.yml` passa a `workflow_run` após "Pipeline Diário" + cron `0 8 * * *` de segurança com guarda anti-duplicado. Fase 2: nova máquina de estados `scripts/gerir_estado_fontes.py` + `data/estado_fontes.json` — `fonte-bloqueada` só abre Issue ao 3.º dia consecutivo, fecho automático ao recuperar; `data-expirada` ganha fecho automático quando a página deixa de ter o padrão (fechou #37/#45 num run real). Fase 3: `scraper_playwright.py` ganha `playwright-stealth`, retries com jitter (3 tentativas, 30-120s) e fallback Wayback Machine (`OK_VIA_ARQUIVO`, novo `scripts/wayback_fallback.py`, puro/sem I/O) — nunca disfarça BLOQUEADO de OK; hora aleatória antes do scrape só em disparos por cron. Fase 4: `REVALIDACAO_CARIMBO_HABILITADA=False` (separada de `AUTO_UPDATE_HABILITADO`, nunca tocada), `data/pagina_fonte.json`, `auto_update_engine.aplicar_refresh_carimbo`/`elegivel_refresh_carimbo` (sandbox, confinamento verificado) e `run_shadow_daily.calcular_carimbos_elegiveis` simulam diariamente sem nunca aplicar nada — critério de activação (≥14 relatórios correctos, decisão do Nuno) documentado.

Fase 5 — verificação em produção (`workflow_dispatch` real em `main`, não simulado): `shadow-daily.yml` correu e correctamente saltou a geração (relatório de hoje já existia — guarda anti-duplicado confirmada); `pipeline-diario.yml` correu o scrape completo — as 3 fontes historicamente bloqueadas (`seg_social_abono`, `seg_social_rsi`, `iefp_desemprego`) fizeram as 3 tentativas com esperas aleatórias 30-120s cada (confirmado nos logs), continuaram `BLOQUEADO` (sem snapshot Wayback recente disponível — ninguém tentou `dominios.gov.pt` no wayback ainda, esperado), e ficaram registadas em `data/estado_fontes.json` como dia 1 (primeira execução real do script, contador começa do zero); as Issues #37/#45 (`data-expirada`) fecharam-se sozinhas nesse run; #47/#48/#49 (`fonte-bloqueada`) mantiveram-se abertas sem duplicar nem comentar (dia 1 < limiar de 3); guardrail "Verificar ficheiros protegidos" passou, só `data/`, `README.md` e `noticias.html` foram tocados. Encontrado e corrigido um gap de observabilidade real nesse run: `_tentar_fallback_wayback` não deixava nenhum rasto no log quando não havia snapshot recente — corrigido com uma linha de log, sem alterar o comportamento de segurança. Também documentada uma limitação pré-existente (não desta fase): `LIMIAR_ANOMALIA_PAGINAS=25` nunca dispara com o estado actual do repositório porque `_paginas_elegiveis()` só conta as 22 páginas da raiz (não recursivo, mesma limitação de `verificar_datas.py`) — as pillar pages em `p/*.html` nunca entram na contagem; registado para o futuro, não corrigido nesta sessão.

Sessão correu numa branch de trabalho (`claude/shadow-mode-issues-scraper-5u0syf`, exigida pelo ambiente remoto) e foi depois integrada em `main` por fast-forward (histórico linear, sem merge commit) a pedido explícito do Nuno, para respeitar a REGRA ABSOLUTA — GIT deste ficheiro; a branch remota não pôde ser apagada por falta de permissão da sessão (fica órfã mas inofensiva, totalmente contida em `main`). 92 testes novos (`test_run_shadow_daily_fonte_propria.py`, `test_estado_fontes.py`, `test_scraper_fallback.py`, `test_carimbos_elegiveis.py` + extensões a `test_auto_update_engine.py`/`test_verificar_datas.py`), 572 testes a passar, ruff limpo.*

---

*Última revisão: 2026-07-02 — duas tarefas de seguimento à sessão anterior. 1) Verificação pedida sobre #37/#45: confirmado com as funções reais (não de memória) que NÃO é regressão — é o efeito do commit `eeefa1c`, que corrigiu um "scan solto" da página inteira (`tem_ano_antigo`) para uma verificação ancorada à própria correspondência regex; `amim.html` nunca teve um match real de padrão de data (só substrings de "2025" em citações legais), `manuais-escolares-mega.html` tem um match real (`ano_letivo`, "2025/2026") correctamente suprimido por `MARCADORES_PENDENTE` enquanto o prazo anunciado não passar. 2) Investigação de fontes alternativas para `seg_social_abono`/`seg_social_rsi`/`iefp_desemprego` (secção "FONTES — ALTERNATIVAS POR FONTE", nova) via `workflow_dispatch` temporário e real: nenhum candidato equivalente encontrado para as duas fontes da Segurança Social (redireccionam sempre para o portal de autenticação, com ou sem Playwright — não é bloqueio de IP/fingerprint); descoberta principal — `iefp_desemprego` **não está bloqueada**, é um falso positivo do próprio `classificador_resposta.py` (a substring "recaptcha" aparece só num `<script>` passivo, sem nenhum sinal real de desafio) — corrigir isso é uma mudança cirúrgica à parte, registada mas não feita nesta sessão. Branch órfã `claude/shadow-mode-issues-scraper-5u0syf` continua sem poder ser apagada (403 na API, sem `gh` CLI nem ferramenta MCP equivalente disponível) — fica para apagar manualmente. Sessão continuou directamente em `main`, sem branches novas.*

---

*Última revisão: 2026-07-03 — duas tarefas de limpeza de branches. 1) Badge NV Labs removido do header por decisão do Nuno: o cherry-pick directo do commit pendente em `claude/nv-labs-branding-update-xq4kb4` entrou em conflito em quase todas as páginas (a nav foi reescrita pela unificação da Fase 4 depois desse commit existir); resolvido na fonte — o badge estava embutido no próprio template de `scripts/sincronizar_nav.py` (`render_nav()`), removido ali e corrido o sincronizador nas 29 páginas (idempotência reconfirmada); CSS exclusivo do badge removido de `assets/css/branding.css`, atribuição do footer mantida; zero vestígios confirmados por grep ao repositório inteiro. 2) `claude/cool-cannon-zn5nfy` (branch antiga, divergida ~19 790 linhas de `main`) analisada sem cherry-pick — nova secção "IDEIAS RECUPERADAS — cascata de fontes (cool-cannon)" resume os 2 commits reais (`cascata_fontes.py` + `rubricas_config.py`, nunca mergeados) e regista o veredicto: conceito sólido mas não vale a pena reimplementar agora — o único fallback configurado (`seg-social.pt/abono-de-familia`) está confirmado morto pela investigação desta mesma sessão, e `source_adapter.py` continua sem consumidor real. `claude/nv-labs-branding-update-xq4kb4` e `claude/cool-cannon-zn5nfy` continuam sem poder ser apagadas pela sessão (403 na API, mesma limitação já registada) — ficam para apagar manualmente; `claude/phase-2-rollback-cleanup-adtecx` e `claude/resolve-open-issues-u1cooz` (já mergeadas, sem commits próprios) entretanto desapareceram do remoto por si (apagadas fora desta sessão, confirmado por `git fetch --prune`). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False`; 572 testes a passar, ruff limpo.*

---

*Última revisão: 2026-07-03 — corrigido o falso positivo do IEFP e definida a estratégia de fetch da Segurança Social (novas secções "CLASSIFICADOR — VERIFICAÇÃO POSITIVA" e "SEG-SOCIAL — ESTRATÉGIA DE FETCH"). `classificador_resposta.py` reescrito: `FonteConfig` ganhou `ancora_conteudo` (frases que uma página legítima tem sempre) e `metodo` ("http"/"playwright"); nova ordem de decisão — âncoras presentes + tamanho suficiente é sempre OK (mesmo com `recaptcha` passivo no resto da página); sem âncoras só há BLOQUEADO com um sinal real (status, redirect/título de login, desafio forte em página pequena); sem âncoras e sem sinal real é MUDOU, nunca BLOQUEADO por engano. Testado com 5 HTML reais obtidos num runner via `workflow_dispatch` temporário (apagado no fim, `tests/fixtures/*.html`): página real do IEFP (87KB, recaptcha passivo) → OK; shell de login do portal seg-social → nunca OK; conteúdo real dos deep-links do portal novo → OK — 19/19 testes em `tests/test_classificador_resposta.py` (12 pré-existentes inalterados + 7 novos). Confirmado num segundo runner que as URLs planas da Segurança Social (antigas e novas) redireccionam sempre para o gateway de autenticação, com ou sem Playwright, mas os deep-links do portal novo servem conteúdo real via Playwright com espera explícita pela âncora (`page.wait_for_function`, não só `networkidle`) — `scraper_playwright.py` actualizado: `iefp_desemprego` passa a `metodo="http"` (nova `scrape_http()`, corre sem abrir o Chromium); `seg_social_abono`/`seg_social_rsi` mantêm `metodo="playwright"` mas apontam aos deep-links, com `_obter_html()` a esperar pela âncora em vez de um `time.sleep(5)` fixo; novo `_tratar_nao_ok()` bifurca BLOQUEADO (fallback Wayback, depois `bloqueios.json`, como antes) de MUDOU (só `avisos.log` via nova `_registar_mudanca_estrutural()`, nunca conta como dia bloqueado na máquina de estados). Gap registado para o futuro: MUDOU ainda não cria Issue, só fica em log. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False`; 579 testes a passar (7 novos), ruff limpo; workflow de diagnóstico temporário apagado no fim.*

---

*Última revisão: 2026-07-03 — verificação no pipeline real (`workflow_dispatch` de `pipeline-diario.yml`, commit `ef686b9`): resultado misto, reportado com honestidade em vez de assumido. `iefp_desemprego` confirmou-se OK (`metodo="http"`) — Issue #49 fechou-se sozinha pela máquina de estados. `seg_social_abono`/`seg_social_rsi` continuaram BLOQUEADO no pipeline real (redirect para o gateway de login em todas as tentativas), ao contrário do runner de diagnóstico isolado que tinha validado o mesmo deep-link — Issues #47/#48 continuam abertas, correctamente: o classificador nunca disfarçou este bloqueio real de OK. Hipótese registada (não confirmada) na secção "SEG-SOCIAL — ESTRATÉGIA DE FETCH": a diferença pode estar no contexto Playwright de produção (`Stealth()` + `extra_http_headers` + `viewport`, ausentes no runner de diagnóstico) a despoletar o mesmo redirect que a versão "nua" evitou — por investigar numa sessão dedicada, isolando cada componente do contexto. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False` neste run.*

---

*Última revisão: 2026-07-03 — sessão de seguimento: isolado e corrigido o culpado real do bloqueio seg-social, registado como hipótese por confirmar na entrada anterior. Novo `PerfilBrowser` (`stealth`/`headers_custom`/`viewport_fixo`) + `_PERFIL_POR_SLUG` em `scraper_playwright.py` tornam o perfil de browser configurável por fonte, sem alterar o comportamento das restantes; `main()` agrupa fontes Playwright por perfil, um `browser.new_context()` por grupo. Workflow de diagnóstico temporário (apagado no fim) testou os 2 deep-links seg-social × 4 perfis isolados (nu/stealth/headers/viewport) num runner real: `extra_http_headers` é o único culpado — devolve um **erro 500 real do backend** (não um simples redirect de login) nos 2 alvos; `stealth` e `viewport` fixo passam isoladamente sem problema, tal como "nu". `_PERFIL_POR_SLUG` fixa `headers_custom=False` só para `seg_social_abono`/`seg_social_rsi`. Confirmado no pipeline real: as 2 fontes ficaram OK de imediato (sem retries). Durante a verificação, descoberto e corrigido um bug lateral: `gerir_estado_fontes.py` compara bloqueios só por data, e `data/bloqueios.json` nunca limpava a entrada do dia quando uma fonte recuperava dentro do mesmo dia (só substituía ao registar um *novo* bloqueio) — só se manifesta com corridas múltiplas no mesmo dia via `workflow_dispatch` manual, nunca no cron diário; corrigido com nova `_limpar_bloqueio_hoje()`, chamada no caminho OK do scraper. Resultado final confirmado: Issues #47/#48 fechadas automaticamente pela máquina de estados, `data/estado_fontes.json` com as 7 fontes monitorizadas em `OK`. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False`; 579 testes a passar, ruff limpo; workflow de diagnóstico apagado no fim.*

---

*Última revisão: 2026-07-03 — pacote PSU (decreto iminente) + novo cluster Habitação. Parte A: fact-check via `WebSearch` (`WebFetch` está completamente bloqueado nesta sessão — 403 em qualquer URL, mesmo fora de `.gov.pt`, ex. `en.wikipedia.org`) confirmou o estado real do trabalho social na PSU — até 15h/semana, isenções (crianças, idosos, pensionistas, estudantes, cuidadores informais, incapacidade ≥80%), a controvérsia real da Associação Portuguesa de Deficientes sobre o limiar de 60-79%, e a disputa pública PS ("facultativo") vs. PSD ("obrigatório") ainda por resolver no decreto-lei; publicado `psu-trabalho-social.html` (5.ª página do cluster PSU) com essa honestidade "aprovado vs. por definir", incluindo o fact-check do Polígrafo a uma alegação falsa que circulava. Construído `simulador-psu.html` — `PARAMETROS_PSU` centralizado (fonte + verificado_em por parâmetro, todos `null` por desenho), `ESTADO_SIMULADOR = 'AGUARDA_DECRETO'`, mecânica de cálculo (`calcularPSU`/`calcularCIT` com redução gradual até 50%) testada com 13 casos fictícios em `tests/test_simulador_psu_calculo.py` (Playwright real, mesmo padrão de `test_pesquisa_hero.py`) — deliberadamente **não publicado**: `noindex`, fora de `sitemap.xml`/`pesquisa.js`/`clusters.json`, com entrada própria em `EXCLUIDAS` (`sincronizar_clusters.py`) e `NAO_INDEXADAS` (`test_pesquisa_indice.py`). `.claude/commands/atualizar-cluster-psu.md` ganhou o Passo 5a (publicar o simulador no dia do decreto) e referências a `psu-trabalho-social.html`/`test_simulador_psu_calculo.py` nos passos existentes.

Parte B: fact-check bloqueante confirmou Porta 65 Jovem/Porta 65+ com candidaturas contínuas desde 2023 (sem prazo) e, mais importante, que o Apoio Extraordinário à Renda está **fechado a novos beneficiários** desde 15/03/2023, com revogação anunciada em fev 2026 mas ainda não publicada em DR — por isso `apoio-extraordinario-renda.html` foi escrito como página "estado actual + alternativas", nunca como guia de candidatura para um apoio fechado (decisão condicional do brief, aplicada correctamente após o fact-check confirmar o cenário). Novo cluster `habitacao` (6.º cluster) em `data/clusters.json`, pillar `p/habitacao.html`, mais `porta-65.html`; nav com 6 clusters confirmada visualmente (Playwright, desktop + mobile) sem overflow. Backlog registado (não implementado): garantia pública crédito jovem, isenção IMT jovem, Regime Simplificado de Arrendamento Acessível (DL 97/2026), 1.º Direito — nova secção "CLUSTER HABITAÇÃO".

Nova secção "MONETIZAÇÃO — POLÍTICA DE AFILIADOS (futuro)" — puramente documental, zero links/infraestrutura de afiliados nesta sessão.

`sincronizar_clusters.py` e `sincronizar_nav.py` corridos com sucesso (idempotência reconfirmada — 2.ª corrida sempre zero alterações); `inserir_botao_partilhar.py` confirmado sem alterações (páginas novas já escritas com o botão). 627 testes a passar (48 novos: 13 do simulador + 35 nas 4 páginas novas via testes parametrizados existentes), ruff limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False` (inalterados por esta sessão — não é scraper).

---

*Última revisão: 2026-07-03 — nova página `prova-escolar.html` no cluster `apoios-escolares`, urgente (prazo 31 de julho). Fact-check via `WebSearch` (`WebFetch` continua completamente bloqueado nesta sessão) cruzando gov.pt (serviço "Fazer a prova escolar"), seg-social.pt/prova-escolar e o Guia Prático — Prova Escolar do ISS, I.P.: confirmado o passo omitido pelos portais oficiais — verificar primeiro em "Provas registadas" na Segurança Social Direta antes de assumir que é preciso agir, já que a prova é frequentemente dada oficiosamente pelo próprio estabelecimento de ensino; confirmados os 3 grupos que têm mesmo de a fazer (14+ com abono no secundário, por efeito na Bolsa de Estudo; 16+ com abono; 18+ com pensão de sobrevivência) e a tabela de prazos/consequências (até 31 jul = OK; 1 ago-31 dez = suspensão em setembro com retroativos ao regularizar; a partir de 1 jan sem justificação = perda definitiva das prestações suspensas; excepção até 31 dez para o ensino superior). Página inclui passo a passo na SSD (com o registo de representação legal para menores e a repetição por cada jovem), casos especiais (deficiência <24 anos, formação profissional com equivalência, acumulação abono+pensão numa única prova) e a clarificação Bolsa de Estudo (automática/oficiosa) vs. Bolsa de Mérito (candidatura à parte, já coberta por `bolsa-de-merito.html`) — primeira página do site a documentar essa distinção. FAQ JSON-LD com as 4 perguntas do brief.

Integração completa: adicionada a `data/clusters.json` (cluster `apoios-escolares`, `descricao_curta` actualizada) e sincronizada com `sincronizar_clusters.py`/`sincronizar_nav.py` (breadcrumb, "pertence ao guia", relacionados, nav — idempotência confirmada); cartão "URGENTE" novo (reaproveita `.badge-novo`) como primeiro item de "Datas a não perder" no `index.html`; cross-link automático a partir de `acao-social-escolar.html` (sibling do mesmo cluster, via `RELACIONADOS` gerado) e cross-link manual novo em `abono-de-familia.html` (`zona-cinzenta`, página noutro cluster — fora do alcance do sync automático); `scripts/pesquisa.js` e `sitemap.xml` actualizados. Avaliado e conscientemente não forçado: "notícia do dia" via `gerar_noticias.py` — o pipeline selecciona por pontuação de palavras-chave sobre feeds RSS reais, não é um mecanismo para inserir manualmente a publicação de uma página; "nenhuma notícia hoje" continua a ser o resultado correcto quando não há candidato genuíno, mesma regra já documentada em "FRESCURA DA HOMEPAGE".

Nota de manutenção sazonal registada em "PÁGINAS COM DATAS SAZONAIS": as referências ao ano lectivo ("2026/2027") e ao prazo ("31 de julho de 2026") têm de ser revistas todos os anos em junho — confirmado contra a lógica real de `verificar_datas.py` (padrão `ano_letivo`, `REVER_EM=[6,7]`) que "2026/2027" só seria assinalado como desactualizado a partir de 2027, nunca antes. 635 testes a passar (8 novos), ruff limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False`.

---

*Última revisão: 2026-07-03 — E-E-A-T: NV Labs passa a entidade resolvível. `sobre.html` reescrito em 5 blocos (o que é o site; NV Labs com `id="nvlabs"` e link para o repositório GitHub real; método de verificação em `id="metodo"`; correcções via GitHub Issues + marcador `<!-- CONTACTO-EMAIL:INICIO/FIM -->` preparado mas não activo; contacto) e ganha JSON-LD (`AboutPage`/`Organization`/`WebSite`) — única página institucional a fazê-lo, excepção deliberada à regra existente, válida porque `FAQPage`/`WebPage` herdam `author`/`publisher` de `CreativeWork`. `scripts/atualizar_branding_nvlabs.py` deixou de só fazer bootstrap e passou a sincronizador idempotente nos dois sentidos (novo `--apenas-sincronizar`); o footer "An NV Labs project" (texto inalterado, decisão do Nuno) passa a link real para `sobre.html#nvlabs` nas 34 páginas que já tinham o bloco (404.html fica de fora, gap pré-existente sem relação com esta sessão). Novo `scripts/adicionar_autoria_artigos.py`: injecta `author`/`publisher` no JSON-LD `FAQPage` das 27 páginas que o têm, e acrescenta " pela redação do Tens Direito" (link para `#metodo`) à última ocorrência (a canónica) de "Verificado a" em cada uma — **ordem invertida face ao brief original** para preservar a contiguidade literal "Verificado a [data]" de que dependem `sincronizar_clusters._REGEX_VERIFICADO`, `auto_update_engine._REGEX_VERIFICADO_A` e o aviso não-bloqueante de `validar-conteudo.yml`; as 3 continuam a reconhecer o carimbo sem qualquer alteração de código, confirmado por teste dedicado. Nova secção "E-E-A-T — NV LABS COMO ENTIDADE RESOLVÍVEL" documenta tudo em detalhe. 704 testes a passar (69 novos: `test_sobre_jsonld.py`, `test_atualizar_branding_nvlabs.py`, `test_adicionar_autoria_artigos.py`), ruff limpo. Nenhuma pessoa, credencial ou e-mail inventados; regra "usar GitHub Issues" mantém-se até o e-mail existir.

---

*Última revisão: 2026-07-03 — fecho da sessão E-E-A-T: fast-forward de `claude/new-session-2oea8g` para `main` (sem PR, a pedido explícito) — 403 confirmado ao tentar apagar a branch remota, registada acima para apagar manualmente, mesma limitação já vista com `claude/nv-labs-branding-update-xq4kb4`/`claude/cool-cannon-zn5nfy`. Varrimento real das 27 páginas de conteúdo confirmou que `author`/`publisher` NV Labs vive só dentro de `FAQPage` — sem `Article`/`WebPage` próprio nenhum — registado acima como melhoria futura, não implementado.

**Verificação real em produção** (`workflow_dispatch` de `pipeline-diario.yml`, run [28673015810](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28673015810), commit `da55ef9`, concluído com sucesso): Step 6 (`sed` do carimbo de `index.html`) correu sem erro — log confirma `"Revisão atualizada: julho 2026 (dateModified: 2026-07-03)"` — o novo texto "Verificado a [data] pela redação do Tens Direito" nos artigos não interfere com este `sed`, que nunca tocou nesse texto (opera só em `id="ultima-revisao-mes"` e `dateModified` de `index.html`, sempre foi assim). O guardrail "Verificar ficheiros protegidos" passou — log confirma `"Guardrail OK — 13 ficheiro(s) modificado(s), nenhum protegido afectado"`; a lista real dos 13 ficheiros do commit `auto: pipeline diário 2026-07-03` (`c70925e`) confirma que **nenhum HTML manual foi tocado**: só `README.md`, `noticias.html` e `data/*.json` (scraped, `alertas_datas.json`, `avisos.log`, `noticias.json`) — `index.html` e `CLAUDE.md` nem sequer entraram no commit porque o conteúdo já estava idêntico (sem alterações a aplicar). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False` em `scripts/decisao_datas.py` após o merge. Sessão E-E-A-T encerrada com o footer, a autoria e o pipeline todos verificados em produção, não assumidos.

---

*Última revisão: 2026-07-03 — duas tarefas de diagnóstico em `main` após o merge E-E-A-T. 1) O commit `6301240` mostrava 7/8 checks — identificado via API o job real: **"pages build and deployment" → "Deploy to GitHub Pages"**, `##[error]Deployment failed, try again later.` — erro genérico e transitório da infra-estrutura do GitHub Pages, sem qualquer relação com o conteúdo do merge (sobre.html/JSON-LD/footer/carimbo). Confirmado por `rerun_workflow_run`: 2.ª tentativa (`run_attempt: 2`) terminou `success` sem qualquer alteração de código — reportado com honestidade antes de mexer, como pedido, e resolvido só com o retry (nenhum "commit de correcção" de conteúdo era necessário nem teria feito sentido para uma falha de infra-estrutura). 2) Issues #51 (`apoio-extraordinario-renda.html`) e #52 (`porta-65.html`) — mesmo padrão de #37/#45: matches reais eram citações factuais permanentes (elegibilidade fixa do PAER, queixa à Provedoria, início das candidaturas contínuas ao Porta 65), não datas desactualizadas. `MARCADORES_HISTORICOS` em `scripts/verificar_datas.py` ganhou 3 padrões novos ancorados aos matches reais (nunca supressão global) — ver nova secção em "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS", que também corrige uma frase imprecisa da revisão anterior sobre `classificacao`/`decisao` nunca gerarem alerta quando `STATIC_REFERENCE` (falsificada pela própria investigação de #51: a classificação anexada ao alerta descreve a 1.ª ocorrência da página, não necessariamente a ocorrência que disparou o alerta). Issues #51/#52 fechadas manualmente com justificação, commit `cc71f5f` (7 testes novos, incluindo regressão sobre o HTML real das duas páginas e guarda contra sobre-supressão). 711 testes a passar, ruff limpo, `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — diagnóstico e correcção do sistema de notícias (sintoma reportado pelo Nuno: notícia real de abono de família de 2 jul nunca apanhada). Diagnóstico com fetch real via `workflow_dispatch` temporário: os 3 feeds Google News genéricos devolviam a notícia (quando existia) na posição 78+ de 100 — muito além do que `fetch_entries()` examinava (10); um feed dedicado por tema ("abono de família portugal") encontrou-a em 1.º lugar, confirmando que a causa era cobertura/especificidade de query, não pontuação. Factor agravante confirmado: a selecção nunca olhava à data, só ao score — um artigo de PSU de 2 meses continuava a vencer todos os dias. DRE confirmado morto pela 3.ª vez (XML malformado, testados 2 URLs alternativos, ambos mortos); candidatos a fonte oficial (`seg-social.pt/rss`, `portugal.gov.pt/.../rss`) também mortos — sem substituto oficial vivo encontrado.

Correcção em `scripts/gerar_noticias.py`: `FEEDS` passa a 7 feeds por tema (todos testados com fetch real antes de entrar no código), DRE removido sem substituto; corte de recência de 7 dias (`JANELA_RECENCIA_DIAS`) rejeita candidatos antigos mesmo com score alto; limite por feed sobe de 10 para 15. Observabilidade permanente (Fase 3, mesmo padrão de `gerir_estado_fontes.py`): novo `scripts/gerir_estado_feeds.py` + `data/estado_feeds.json` (Issue `feed-morto` ao 3.º dia consecutivo morto, fecho automático), `data/feeds_saude_hoje.json` (snapshot diário, XML malformado com HTTP 200 conta sempre como `MORTO`) e `data/noticias_candidatos.json` (log auditável das últimas 60 corridas) — os 2 últimos na allow-list de `escrever_ficheiro_seguro()`; `estado_feeds.json` escrito directamente pelo seu próprio script, fora dessa allow-list, mesmo padrão de `estado_fontes.json`. `pipeline-diario.yml` ganhou o Step 3a (actualizar estado dos feeds), Step 7c (label `feed-morto`) e o bloco de Issues correspondente no Step 8. 35 testes novos com fixtures reais capturadas no diagnóstico (título/data/score exactos), incluindo o caso do artigo de PSU de maio rejeitado pelo corte de recência.

**Verificado no pipeline real** (`workflow_dispatch` de `pipeline-diario.yml`, run 28684312236, commit `404f760`, sucesso): vencedor da selecção foi "Prestação social única: reforma altera 13 apoios do Estado" datado **2026-06-26** — exactamente na borda dos 7 dias a partir de 3 jul, não um artigo de há meses; o log confirma a rejeição real de um candidato de 2026-06-25 (1 dia antes da borda) com o motivo `"antigo (antes de 2026-06-26, janela de 7 dias)"`, provando o corte a funcionar com precisão de dia. Não foi a notícia de abono especificamente a vencer neste run — dentro da janela de 7 dias elegíveis, um candidato de PSU pontuou mais alto (score=5) — comportamento correcto e esperado do desenho (o corte elimina o histórico de meses, não impõe "mais recente vence sempre dentro da janela"). Guardrail "Verificar ficheiros protegidos" confirmou "13 ficheiro(s) modificado(s), nenhum protegido afectado"; a lista real de ficheiros do commit `404f760` confirma exactamente os 3 ficheiros novos como `added` (`data/estado_feeds.json`, `data/feeds_saude_hoje.json`, `data/noticias_candidatos.json`) mais `data/noticias.json`/`index.html`/`noticias.html` como `modified` — nenhum HTML manual tocado. Estado dos feeds: as 7 fontes ficaram `OK` logo no dia 1 (nenhuma Issue `feed-morto` criada, correctamente — dia 1 < limiar de 3); sem entrada nenhuma para DRE (removido do código, não apenas marcado morto). Workflow e script de diagnóstico temporários apagados. 799 testes a passar, ruff limpo, `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.
