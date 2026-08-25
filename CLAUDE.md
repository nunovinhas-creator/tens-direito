# CLAUDE.md — Tens Direito

Instruções globais para o Claude Code neste repositório.
Ler sempre antes de qualquer tarefa.

**Próximos passos e gatilhos: ver `ROADMAP.md`** — índice único (privado,
nunca servido) de tudo o que está à espera de um sinal, automático ou manual.

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
- `data/noticias_candidatos.json` — log auditável de candidatos/decisões de cada corrida de notícias (últimos 14 dias)
- `dados/observacoes/<slug>.json` — historial auditável de observações do scraper, um ficheiro por fonte monitorizada, escrito por `scripts/registar_observacao.py` (Fase 1 de "DADOS ABERTOS", só quando `sha256_conteudo` mudar — ver essa secção)
- `dados/parametros.json` — consolidado dos parâmetros legais (Fase 2 de "DADOS ABERTOS"), gerado por `scripts/gerar_parametros_json.py` a partir de `dados/parametros/*.yaml` (esses YAML continuam curados manualmente, nunca escritos pelo pipeline)
- `dados/tensdireito.db` — base SQLite pública (Fase 3 de "DADOS ABERTOS"), gerada por `scripts/gerar_base_dados.py`

**TODOS os outros HTML são manuais e protegidos.**
Esta regra aplica-se a páginas actuais E futuras.
Qualquer novo HTML criado está automaticamente protegido — não precisa de ser adicionado a listas.

O guardrail está implementado em dois locais:
1. `scripts/gerar_noticias.py` — função `escrever_ficheiro_seguro()` é uma allow-list estrita: `FICHEIROS_AUTO_GERADOS` (`noticias.html`, `noticias.json`, `feeds_saude_hoje.json`, `noticias_candidatos.json` — escrita livre) ou `SECCOES_PERMITIDAS` (`index.html`, só dentro de `NOTICIA-HOME:INICIO/FIM` — `_verificar_escrita_confinada()` compara o ficheiro em disco com o novo conteúdo fora da secção marcada; qualquer diferença aí, ou o marcador não existir, bloqueia a escrita). Qualquer nome fora das listas é **sempre bloqueado**, nunca escrito por omissão (corrigido na Fase 1 do sistema de notícias — antes havia um "fallthrough" que escrevia livremente qualquer ficheiro não-HTML não listado). Ver `tests/test_gerar_noticias_guardrail.py`. `data/estado_feeds.json` fica fora desta allow-list de propósito — é escrito directamente por `gerir_estado_feeds.py`, script dedicado e de confiança por construção, mesmo padrão de `estado_fontes.json`/`gerir_estado_fontes.py`.
2. `.github/workflows/pipeline-diario.yml` — step "Verificar ficheiros protegidos" faz `exit 1` se algum HTML protegido for detectado como modificado antes do commit (ficheiros `.json` em `data/` nunca passam por este guardrail — só HTML é protegido). `dados/observacoes/<slug>.json` fica fora da allow-list de `escrever_ficheiro_seguro()` de propósito — mesmo padrão de `data/estado_feeds.json`: é escrito directamente por `scripts/registar_observacao.py`, que tem a sua própria allow-list restrita a `SLUGS_MONITORIZADOS` (ver secção "DADOS ABERTOS").

Nota: o marcador `<!-- ATUALIZACOES:HOME:INICIO/FIM -->` (bloco "Atualizado
recentemente") também vive em `index.html`, mas é escrito por
`scripts/sincronizar_clusters.py` — um script de **sessão manual**, não do
pipeline automático (mesma categoria que `CLUSTERS:HOME`/`DESTAQUES:HOME` —
ver secção "SISTEMA DE CLUSTERS"). Não entra nesta lista porque não é o
pipeline `pipeline-diario.yml` a escrevê-lo.

Nota 2: o marcador `<!-- CAL-HOME:INICIO/FIM -->` (dados da barra fixa
"Próximo pagamento" no topo da homepage) também vive em `index.html`, mas é
escrito por `scripts/atualizar_calendario.py`, corrido pelo workflow
**`calendario-mensal.yml`** — não pelo `pipeline-diario.yml`. É a única zona
de `index.html` fora do âmbito do pipeline diário; o guardrail próprio de
`calendario-mensal.yml` permite `index.html` exactamente por causa desta zona
(ver secção "CALENDÁRIO DE PAGAMENTOS"). O `pipeline-diario.yml` nunca toca em
`CAL-HOME` (só nas suas 3 zonas), por isso os dois workflows coexistem sem
colidir — mais o `concurrency: main-writes` partilhado a serializar os pushes.

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

**Rede automática (2026-07-06)**: esta regra já não depende só de disciplina —
`.github/workflows/limpar-branches.yml` corre diariamente (mais push a `main` e
manual) com o GITHUB_TOKEN do próprio Actions e apaga sozinho qualquer branch
remota != `main` que já esteja totalmente integrada (0 commits únicos), sem
depender de uma sessão estar logada. Uma branch com trabalho por integrar nunca
é apagada — fica registada numa Issue única até alguém a trazer para `main` ou
a apagar manualmente. Ver secção "LIMPEZA AUTOMÁTICA DE BRANCHES".

**Protocolo de fim de sessão — sessões remotas em branch designada
(2026-07-17):** o resumo final de qualquer sessão remota que trabalhe numa
branch designada pelo ambiente termina OBRIGATORIAMENTE com o estado de
integração explícito — "PR: #nn (aberto|merged)" ou "SEM PR — branch não
integrada" — para que "feito e enviado" nunca se confunda com "em produção".
Motivo real (2026-07-17): a sessão do menu móvel terminou com o trabalho
apenas na branch, e a sessão seguinte partiu do princípio errado de que já
estava integrado em main.

**Arranque de sessão (handoff) (2026-07-20):** guarda simétrica ao
protocolo de fim de sessão acima — para o erro de 2026-07-17 nunca se
repetir na direcção inversa (a sessão seguinte a assumir "integrado" sem
verificar). Antes de qualquer trabalho novo:

- Verificar o estado de integração da sessão anterior:
  `git log --oneline -5 main` e comparar com o último resumo relevante
  no `ROADMAP.md` (secção "✅ CONCLUÍDO RECENTEMENTE" ou equivalente).
- Se o `ROADMAP.md` (ou a última entrada de revisão do `CLAUDE.md`)
  indicar uma branch "SEM PR — branch não integrada" que ainda não
  aparece em `main`: **PARAR e reportar ao utilizador antes de começar
  trabalho novo** — nunca presumir que entretanto foi integrada.
- Nunca construir trabalho novo sobre o pressuposto de que a branch da
  sessão anterior foi integrada sem o confirmar em `git` — o resumo de
  uma sessão descreve a intenção registada nessa altura, não o estado
  actual do repositório.

**Excepção única e deliberada — workflows de diagnóstico (2026-07-16):**
workflows de diagnóstico (permanentes OU temporários) nunca são commitados em
`main`. Vão sempre para branch própria, com trigger `on: push` limitado a essa
branch. Corre-se, lê-se o output, apaga-se a branch. Razão: `workflow_dispatch`
exige o ficheiro em `main`; `on: push` numa branch dispensa isso e evita que
uma limpeza falhada deixe um workflow órfão a correr em `main` — um erro que
pareceria sucesso. Esta é a única excepção à regra "NUNCA criar branches"
deste ficheiro — nenhuma outra tarefa a herda por analogia. Substitui o
padrão usado em sessões anteriores (documentado em várias entradas de revisão
mais abaixo neste ficheiro: `diagnostico-dre-psu-temp.yml`,
`diagnostico-fontes-temp.yml`, `diagnostico-igefe-temp.yml`,
`diagnostico-calendario-temp.yml`, `diagnostico-logo-temp.yml` — todos
committed directamente em `main` e apagados no fim); essas entradas ficam
como estavam escritas nessa altura, sem reescrever o passado, mas o padrão
delas já não é o que se segue daqui para a frente.

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
| Analytics | GA4: `G-XP46PM8H1Q` — **Consent Mode v2 AVANÇADO** (desde 2026-07-13): o gtag.js carrega sempre, para todos os visitantes; em `denied` (omissão) só envia pings sem cookies, cookies reais só depois de "Aceitar" (nunca gtag.js estático no `<head>`) |
| Consentimento | Banner próprio self-hosted: `assets/js/consentimento.js` (substituiu o CookieYes a 2026-07-11 — o plano gratuito tinha limite de 5.000 pageviews/mês; zero serviços externos, zero limites; **Consent Mode v2 AVANÇADO desde 2026-07-13** — o gtag.js carrega sempre, para todos, e o GA4 envia pings sem cookies em `denied` [omissão], que a Google usa para modelar estatisticamente os não consentidos; só ao "Aceitar" o consentimento sobe a `granted` e passam a existir cookies `_ga`/`_ga_*`; escolha em localStorage `td_consentimento`; `window.tdGerirConsentimento()` reabre o banner — botão "Gerir cookies" em `privacidade.html`; testado em `tests/test_consentimento.py`) |
| Pesquisa interna | `scripts/pesquisa.js` (JS puro, 27 páginas indexadas — todas excepto `index.html` e `404.html`; ranking em camadas + excerto + badge de cluster — ver nota de manutenção abaixo) |
| Scraper | Playwright + BeautifulSoup (`scripts/scraper_playwright.py`), com `playwright-stealth`, retries com jitter e fallback Wayback (`OK_VIA_ARQUIVO`) — ver secção "SCRAPER — ROBUSTEZ CONTRA BLOQUEIOS" |
| Extracção valores | `scripts/extrair_valores.py` → `data/divergencias.json` |
| Notícias | `data/noticias.json` (fonte de verdade) + `scripts/gerar_noticias.py` (13 feeds RSS por tema + corte de recência de 7 dias) → `noticias.html` (arquivo por mês) + 2-3 cards em `index.html` (`NOTICIA-HOME`) — ver secção "FRESCURA DA HOMEPAGE" |
| Partilha social | `assets/js/share.js` + `assets/css/share.css`, inserido em cada página via `scripts/inserir_botao_partilhar.py` (idempotente, sem bibliotecas externas) |
| Clusters/navegação | `data/clusters.json` (fonte única) + `scripts/sincronizar_clusters.py` (idempotente, injecta entre marcadores — ver secção "SISTEMA DE CLUSTERS") |
| Checklist final | `assets/js/checklist.js` + `assets/css/checklist.css` — bloco `.checklist-final` (FASE 1 de `MELHORIAS-SPEC.md`, ver secção "RESPOSTA RÁPIDA + CHECKLIST FINAL"), sem localStorage |
| Gerador de Documentos | `assets/js/gerador-documentos.js` (motor único config-driven) + `assets/css/gerador-documentos.css` + hub `/documentos.html` + páginas em `documentos/*.html` — minutas 100% client-side, zero rede/localStorage (ver secção "GERADOR DE DOCUMENTOS") |

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

### Workflows (8 — 3 fazem push de conteúdo, 1 apaga branches remotas)

| Ficheiro | Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | cron `0 6 * * *` | Scrape → detectar mudanças → notícias → validar valores → README → push único | ✅ sim (`data/`, `index.html`, `noticias.html`, `README.md`, `CLAUDE.md`) |
| `shadow-daily.yml` | `workflow_run` após "Pipeline Diário" + cron `0 8 * * *` (rede de segurança) | `run_shadow_daily.py`: Shadow Mode → analytics → relatório Markdown → guarda em `shadow_history/` | ✅ sim (só `shadow_history/*.md`) |
| `verificar-links.yml` | cron `0 7 * * 1` (segunda) | lychee testa todos os links HTML + Issue se 404 | ❌ não |
| `validar-conteudo.yml` | push para main `**.html` | Valida GA4, OG tags, JSON-LD, disclaimer, data verificação + HTML5 validator | ❌ não |
| `integridade.yml` | push a main, **pull_request para main** (2026-07-17), cron semanal, manual | Gitleaks (segredos) + Ruff + pip-audit + validador HTML5 + `verificar_injecao.py` (prompt injection em `data/`/`shadow_history/`) + **suite `pytest` completa** (job `testes-python`, 2026-07-04). Em PRs correm só os jobs determinísticos (dependem apenas do checkout); o canário de URLs oficiais tem `if: github.event_name != 'pull_request'` — validar portais externos a cada push de PR arriscaria flakiness/rate-limit sem validar o código do PR. `concurrency` com `cancel-in-progress` só em PRs (pushes sucessivos cancelam runs obsoletos; em main/schedule nunca cancela) | ❌ não |
| `smoke-producao.yml` | `push` a main + cron `30 6 * * *` (rede de segurança) + manual | `scripts/smoke_producao.sh`: `curl` às páginas críticas em produção (lista em `scripts/urls_criticas.txt`), com retry/backoff; falha se alguma não devolver 200, ou se um simulador devolver 200 com conteúdo errado/antigo (ver secção "SMOKE TEST DE PRODUÇÃO") | ❌ não |
| `calendario-mensal.yml` | cron `0 6 25 * *` + `0 6 28 * *` (retry) + `30 5 1 * *` (virar mês) + manual | Calendário de pagamentos: se o JSON já tem o mês → injecção + testes + commit confinado; senão → **raspa a fonte pública oficial** (`/ptss/pssd/pagamentos`) e grava o mês; só se o scraper falhar abre Issue `calendario-manual` (ver secção "CALENDÁRIO DE PAGAMENTOS") | ✅ sim (SÓ `data/calendario_pagamentos.json` + `calendario-pagamentos-seguranca-social.html` entre marcadores CAL:* + `index.html` só na zona `CAL-HOME:*` — barra "Próximo pagamento" da homepage; guardrail próprio) |
| `limpar-branches.yml` | `push` a main + cron `0 5 * * *` + manual | Apaga automaticamente branches remotas != `main` já totalmente integradas (via GITHUB_TOKEN do Actions, nunca depende de sessão logada); as que têm commits únicos ficam registadas numa Issue única — ver secção "LIMPEZA AUTOMÁTICA DE BRANCHES" | ❌ não faz push de conteúdo — a única escrita é apagar refs `heads/*` != `main` (`contents: write`) + gerir a Issue (`issues: write`) |

**`pipeline-diario.yml`, `shadow-daily.yml` e `calendario-mensal.yml` são os
únicos que fazem `git push` de conteúdo, cada um com um âmbito de escrita
disjunto e garantido por guardrail próprio** (ficheiros de conteúdo/dados vs.
só `shadow_history/*.md` vs. só o JSON do calendário + a página do calendário
entre marcadores CAL:* + a barra `CAL-HOME:*` do `index.html`).
`limpar-branches.yml` é uma terceira categoria de escrita, à parte — nunca toca
em conteúdo do repositório, só apaga refs de branch e gere uma Issue. Os
restantes só lêem. Isto elimina race conditions entre workflows concorrentes.

---

## SMOKE TEST DE PRODUÇÃO

Rede de segurança final, depois de todos os workflows de conteúdo/CI:
confirma que a produção real (`tensdireito.com`, não o checkout) está
de facto a servir o que se espera. Motivo directo: o deploy do GitHub
Pages já falhou silenciosamente **duas vezes** nesta fase do projecto
(`##[error]Deployment failed, try again later.` em
`actions/deploy-pages@v5`) — sem qualquer sinal de erro no resto do
pipeline, nenhum job vermelho, nenhuma Issue. Nas duas vezes só foi
descoberto ao visitar a página manualmente e encontrar 404. Nenhum dos
outros 5 workflows verifica a produção real — todos correm sobre o
checkout local do repositório.

1. **`.github/workflows/smoke-producao.yml`** — três triggers:
   - `push` a `main` — dispara em todos os pushes, incluindo os do
     pipeline automático. **Substituiu `workflow_run` sobre "pages
     build and deployment" a 2026-07-05** — ver "GATILHO CORRIGIDO"
     abaixo, esse nunca disparou.
   - `schedule` `30 6 * * *` — rede de segurança, depois do
     `pipeline-diario.yml` (06:00 UTC); garante que uma falha de deploy
     nunca fica por detectar até alguém reparar manualmente.
   - `workflow_dispatch` — para testar manualmente (usado nesta sessão
     para confirmar o falso-404 antes de publicar).
2. **`scripts/smoke_producao.sh`** — lê `scripts/urls_criticas.txt`
   (único sítio a editar — nunca hardcoded no script nem no workflow),
   faz `curl` a cada página com `User-Agent` identificado
   (`TensDireito-SmokeTest/1.0`), **9 tentativas com 30s de espera entre
   elas (até ~4,5 min, desde 2026-07-05 — ver "GATILHO CORRIGIDO")**
   (absorve flutuações momentâneas do CDN e a latência de propagação do
   Pages, sem mascarar uma falha real). Para as páginas de simulador
   (`SIMULADORES` no topo do script — `simulador-abono.html`,
   `simulador-ase.html`, `simulador-csi.html`), confirma também que o
   corpo da resposta contém literalmente `"Verificado a"` — apanha o
   caso de a página responder 200 mas servir conteúdo errado ou
   desactualizado (cache do CDN com uma versão antiga), não só o 404.
   Essa verificação de conteúdo nunca tem retry — se o 200 já chegou, o
   conteúdo não muda entre tentativas, por isso falha de imediato em
   vez de esperar mais tempo para nada.
3. **`scripts/urls_criticas.txt`** — uma página por linha, caminho
   relativo ao domínio; linhas vazias ou a começar por `#` são
   ignoradas. Cobre: homepage, o hub `/simuladores.html`, os 3
   simuladores, `/sitemap.xml` e 4 páginas evergreen de topo (abono,
   RSI, subsídio de desemprego, baixa médica). Adicionar uma página
   nova importante é só acrescentar uma linha aqui.

### RECUPERAÇÃO AUTOMÁTICA DO DEPLOY (2026-07-05) — sem intervenção manual

A falha de infra-estrutura "`##[error]Deployment failed, try again
later.`" (secção acima) já aconteceu **3 vezes** — sempre descoberta e
corrigida por um humano: o Nuno vê a notificação de email do GitHub
("Some jobs were not successful"), reporta à sessão, e o Code corre
`rerun_workflow_run` manualmente pela API. Como "pages build and
deployment" é um workflow **dinâmico** (sem ficheiro `.yml` no
repositório — confirmado via API, `path: "dynamic/pages/pages-build-
deployment"`), nunca é possível editar-lhe a lógica nem acrescentar-lhe
retries internos.

**Corrigido com um script novo, chamado de fora**: `scripts/
garantir_deploy_pages.sh` corre logo antes do smoke test nos **3
sítios** que já verificam produção (`smoke-producao.yml` e o smoke
inline de `pipeline-diario.yml`/`shadow-daily.yml`) — espera que o
deploy do commit actual (`GITHUB_SHA`) termine (polling via `gh api`,
até 180s por tentativa) e, se falhar, dispara-o de novo
automaticamente via `POST .../actions/runs/{id}/rerun`, até 3
tentativas. **Nunca é um gate rígido** — se não conseguir confirmar ou
recuperar dentro do tempo limite, sai com sucesso na mesma (`exit 0`)
e deixa o smoke test a seguir ser a verificação real; o objectivo é só
eliminar a necessidade de um humano ver uma notificação e correr um
comando à mão, não substituir o smoke test como fonte de verdade.
Requer `permissions: actions: write` nos 3 workflows (novo, só para
poder disparar o rerun via API — nada mais muda de comportamento).

**Verificado no incidente real que motivou esta correcção**: o deploy
do commit `cdaee04` falhou com o erro genérico habitual; corrigido
manualmente nessa altura (`rerun_workflow_run`, sucesso na 2.ª
tentativa, confirmado por `smoke-producao.yml` a seguir) — este script
existe precisamente para a *próxima* vez que isto acontecer não
precisar de repetir esse processo manual.

### GATILHO CORRIGIDO (2026-07-05) — `workflow_run` nunca disparou

Sintoma: depois do deploy do commit `f9030b7` (nova página
`baixa-medica-subsidio-doenca.html`), o smoke test não correu sozinho —
só via disparo manual. Diagnóstico antes de mexer: listado o histórico
completo de `smoke-producao.yml` desde a criação (3 runs) — **os 3
foram `workflow_dispatch`, zero `workflow_run`**. O gatilho automático
nunca funcionou, nem uma única vez, desde que o workflow foi criado —
não é uma regressão recente, é um defeito de origem que passou
despercebido porque as duas primeiras vezes que o smoke test "correu a
seguir a um deploy" foi sempre por disparo manual imediatamente a
seguir, nunca pelo `workflow_run` de facto.

**Causa raiz**: "pages build and deployment" é um workflow **dinâmico**,
gerido internamente pelo GitHub Pages — não tem ficheiro `.yml` no
repositório (confirmado via API: `path: "dynamic/pages/pages-build-deployment"`,
`event: "dynamic"`). O gatilho `workflow_run` do GitHub Actions só
encadeia de forma fiável workflows reais do repositório (com ficheiro
`.yml` próprio); não consegue escutar um workflow gerido pela própria
plataforma. **Lição generalizável, para qualquer workflow futuro**:
nunca usar `on: workflow_run` para escutar "pages build and
deployment", Dependabot, ou qualquer outro workflow que apareça no
separador Actions mas não tenha ficheiro `.yml` no repositório — só
funciona com workflows definidos por nós.

**Correcção**: `on: push: branches: [main]` substitui o `workflow_run`
partido — dispara sempre, de forma garantida (é um evento nativo do
Git, não depende de outro workflow terminar). Risco considerado: o job
arranca quase instantaneamente após o push, antes de o deploy do Pages
estar necessariamente publicado — mitigado subindo `TENTATIVAS` de 3
para 9 em `scripts/smoke_producao.sh` (até ~4,5 min de tolerância; o
deploy real deste site estático completa tipicamente em segundos —
confirmado 26s no deploy do commit `f9030b7` — por isso o caso comum
sai do ciclo na 1.ª ou 2.ª tentativa, sem penalizar o tempo de CI).

**Testado no mesmo commit desta correcção**: push directo, confirmado
via API que o `smoke-producao.yml` disparou sozinho por `push` (não por
`workflow_dispatch`) e terminou com sucesso — ver entrada de revisão no
fim deste ficheiro para o run real.
4. **Falha = vermelho no Actions, sem mais nada** — decisão deliberada
   desta sessão: sem notificações externas, sem referências públicas.
   Suficiente como alerta por agora; se o volume de falsos alarmes
   justificar mais no futuro, é uma decisão à parte.

**Verificado com um falso-404 real** (não simulado): acrescentada
temporariamente a `scripts/urls_criticas.txt` a linha
`/pagina-inventada-para-teste-smoke-nao-deve-existir.html`, commit,
push, e `workflow_dispatch` manual contra a produção real (run
[28721561322](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28721561322)).
Resultado exactamente como esperado: as 9 páginas reais responderam
200 em ~2,5s no total (confirmando de caminho que `/simuladores.html`
e os 3 simuladores estão mesmo em produção — resolve a dúvida em
aberto da sessão anterior sobre o deploy do commit `121686b`); o URL
inventado falhou 404 nas 3 tentativas, com exactamente 30s entre cada
uma (`22:24:11` → `22:24:41` → `22:25:11`), e o job terminou vermelho
(`conclusion: failure`) ao fim de ~63s. Linha de teste removida no
commit seguinte. Lógica de sucesso/404/conteúdo-em-falta também
confirmada localmente com um `http.server` a fazer de produção (via
override `DOMINIO=http://localhost:PORTA`), sem tocar em produção real
para esses três casos.

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
| `simulador-csi.html` | Simulador do Complemento Solidário para Idosos (CSI) 2026 | 4 jul. 2026 |
| `simuladores.html` | Simuladores e Calculadoras (hub) | 4 jul. 2026 |
| `p/familia.html` | Apoios para Família e Crianças em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `p/idosos-incapacidade-cuidadores.html` | Apoios para Idosos, Incapacidade e Cuidadores em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `p/trabalho-rendimento.html` | Apoios de Trabalho e Rendimento em Portugal 2026 — Guia Completo | 2 jul. 2026 |
| `psu-trabalho-social.html` | Trabalho social na PSU: aprovado vs. por definir | 3 jul. 2026 |
| `p/habitacao.html` | Apoios à Habitação em Portugal 2026 — Guia Completo | 3 jul. 2026 |
| `porta-65.html` | Porta 65 Jovem e Porta 65+ 2026 | 3 jul. 2026 |
| `apoio-extraordinario-renda.html` | Apoio Extraordinário à Renda 2026: o que aconteceu e alternativas | 3 jul. 2026 |
| `prova-escolar.html` | Prova Escolar 2026: prazo 31 de julho — quem tem de fazer e como | 3 jul. 2026 |
| `prestacao-social-para-a-inclusao.html` | Prestação Social para a Inclusão (PSI) 2026 | 4 jul. 2026 |
| `baixa-medica-subsidio-doenca.html` | Baixa médica e subsídio de doença 2026 | 5 jul. 2026 |
| `bolsa-de-estudo-ensino-superior.html` | Bolsa de Estudo do Ensino Superior 2026/2027 | 6 jul. 2026 |
| `assistencia-familia-filhos.html` | Faltas e licenças para assistência a filhos e família 2026 | 11 jul. 2026 |
| `documentos.html` | Gerador de Documentos (hub) | 6 jul. 2026 |
| `documentos/reclamacao-decisao-seguranca-social.html` | Reclamação de decisão da Segurança Social | 6 jul. 2026 |
| `documentos/carta-acompanhamento-csi.html` | Carta de acompanhamento — pedido de CSI | 6 jul. 2026 |
| `documentos/carta-acompanhamento-reavaliacao-abono.html` | Carta de acompanhamento — reavaliação do escalão do abono | 6 jul. 2026 |
| `documentos/recurso-hierarquico-seguranca-social.html` | Recurso hierárquico de decisão da Segurança Social | 6 jul. 2026 |
| `documentos/exposicao-atraso-processamento.html` | Exposição por atraso no processamento de prestação | 6 jul. 2026 |
| `documentos/carta-acompanhamento-divida-prestacoes.html` | Carta de acompanhamento — dívida em prestações | 6 jul. 2026 |
| `documentos/carta-acompanhamento-svi-recurso.html` | Carta de acompanhamento — recurso de decisão do SVI | 6 jul. 2026 |
| `documentos/carta-acompanhamento-comunicacao-alteracao.html` | Carta de acompanhamento — alteração de morada/agregado/rendimentos | 6 jul. 2026 |
| `documentos/requerimento-reavaliacao-escalao-ase.html` | Pedido de reavaliação do escalão de ASE | 6 jul. 2026 |
| `documentos/pedido-acesso-documentos-administrativos.html` | Pedido de acesso a documentos administrativos (LADA) | 6 jul. 2026 |
| `documentos/requerimento-generico-seguranca-social.html` | Requerimento genérico à Segurança Social | 6 jul. 2026 |
| `documentos/pedido-declaracao-comprovativo-prestacoes.html` | Pedido de declaração/comprovativo de prestações | 6 jul. 2026 |
| `calendario-pagamentos-seguranca-social.html` | Calendário de Pagamentos da Segurança Social | 12 jul. 2026 |
| `pagamento-apos-deferimento.html` | Pedido deferido: quando cai o primeiro pagamento | 12 jul. 2026 |
| `como-pedir-niss.html` | Como pedir o NISS 2026 | 14 jul. 2026 |
| `calendario-escolar-apoios.html` | Calendário de Apoios Escolares 2026/2027 | 14 jul. 2026 |
| `declaracao-situacao-contributiva.html` | Declaração de situação contributiva: certidão de não dívida 2026 | 14 jul. 2026 |
| `p/como-pedir.html` | Como Pedir — Documentos, Senhas e Certidões (pillar) | 17 jul. 2026 |
| `senha-seguranca-social-direta.html` | Como pedir (e recuperar) a senha da Segurança Social Direta | 17 jul. 2026 |
| `iban-seguranca-social.html` | Como alterar o IBAN na Segurança Social | 17 jul. 2026 |
| `chave-movel-digital.html` | Como ativar a Chave Móvel Digital | 17 jul. 2026 |
| `alterar-morada.html` | Como alterar a morada no Cartão de Cidadão | 18 jul. 2026 |
| `renovar-cartao-cidadao.html` | Renovar o Cartão de Cidadão 2026: desde 16,20 € e prazos | 18 jul. 2026 |
| `imt-jovem.html` | IMT Jovem 2026: isenção até 330.539 € na 1.ª casa | 20 jul. 2026 |
| `garantia-publica-credito-habitacao.html` | Garantia Pública 2026: crédito habitação jovem até 100% | 20 jul. 2026 |
| `simulador-imt-jovem.html` | Simulador de IMT Jovem 2026 — quanto poupas na primeira casa | 20 jul. 2026 |
| `deducao-rendas-irs.html` | Dedução de rendas no IRS 2026: até 900 € por ano | 20 jul. 2026 |
| `primeiro-direito.html` | 1.º Direito 2026: apoio a quem vive em habitação indigna | 20 jul. 2026 |
| `noticias.html` | Notícias | jun. 2026 |
| `sobre.html` | Sobre o Tens Direito | jun. 2026 |
| `fontes.html` | Fontes Oficiais | jun. 2026 |
| `privacidade.html` | Política de Privacidade | jun. 2026 |
| `acessibilidade.html` | Acessibilidade | 4 jul. 2026 |
| `dados.html` | Dados Abertos | 19 jul. 2026 |
| `404.html` | Página não encontrada | jun. 2026 |

*Tabela corrigida a 2026-07-02 — faltavam 7 páginas já publicadas (rsi, subsidio-desemprego,
subsidio-parental, cuidador-informal, comecar-aqui, simulador-abono, simulador-ase).*

---

## CHECKLIST OBRIGATÓRIA ANTES DE QUALQUER COMMIT

Antes de qualquer `git commit`, verificar cada ponto:

- [ ] `git branch` mostra `* main`
- [ ] Factos retirados de `data/scraped/` ou pesquisa verificada — **NUNCA de memória**
- [ ] Links testados — só usar URLs da lista verificada ou homepage do domínio oficial
- [ ] Página tem o bloco de consentimento próprio no `<head>`: stub inline (Consent Mode v2 negado por omissão) + `<script src="/assets/js/consentimento.js" data-ga4="G-XP46PM8H1Q" defer>` — **nunca** gtag.js estático (contornaria o consentimento; `tests/test_consentimento.py` falha se aparecer)
- [ ] `og:title`, `og:description`, `og:url`, `og:locale`, `og:image` presentes — página nova: correr `python scripts/adicionar_og_image.py --write` (insere o bloco og:image) e depois `python scripts/gerar_og_images.py --write` (gera a imagem própria da página, 1200×630, com o título no cartão, e aponta o og:image para ela); mudar um `og:title` exige regenerar (`gerar_og_images.py --write`) — `tests/test_og_image.py` falha se esquecido
- [ ] JSON-LD `FAQPage` + `HowTo` + `BreadcrumbList` presentes
- [ ] `"Verificado a [data]"` visível no corpo da página
- [ ] Disclaimer de independência (`Aviso de independência`) presente
- [ ] `sitemap.xml` actualizado se nova página
- [ ] `scripts/pesquisa.js` actualizado com nova página (se nova página de conteúdo)
- [ ] Nova página de conteúdo? Correr `python scripts/inserir_botao_partilhar.py` (idempotente — adiciona o botão "Partilhar este artigo" só às páginas que ainda não o têm)
- [ ] Nova página pertence a um cluster? Actualizar `data/clusters.json` e correr `python scripts/sincronizar_clusters.py` (ver secção "SISTEMA DE CLUSTERS")
- [ ] Nova página? Correr `python scripts/sincronizar_nav.py` para injectar a nav principal única (ver secção "NAVEGAÇÃO PRINCIPAL")
- [ ] Testes de coerência a passar: `pytest tests/test_breadcrumb_coerencia.py tests/test_nav_coerencia.py` (parametrizados sobre as páginas reais — cobrem a página nova automaticamente) — desde 2026-07-04 a suite completa também corre no CI a cada push a `main` (job "Suite de Testes (pytest)" em `integridade.yml`), mas correr localmente primeiro continua a poupar uma volta de CI vermelho
- [ ] Página nova nasce a passar `pytest tests/test_acessibilidade.py` (axe-core real, WCAG 2.1 AA — ver secção "ACESSIBILIDADE — WCAG 2.1 AA") — parametrizado sobre as páginas reais, cobre a página nova automaticamente; zero tolerância a critical/serious, limiar documentado para moderate/minor
- [ ] Novo artigo de conteúdo? Inclui obrigatoriamente os dois blocos da FASE 1 de `MELHORIAS-SPEC.md` — ver secção "RESPOSTA RÁPIDA + CHECKLIST FINAL": `.resposta-rapida` (rótulo "⚡ Resposta rápida" + tempo de leitura, dentro do `.resposta-direta` já existente no hero, ≤60 palavras) e `.checklist-final` (checklist accionável antes do FAQ, liga `assets/css/checklist.css` + `assets/js/checklist.js`)
- [ ] Editou `<title>` ou `<meta name="description">` com um valor legal em € ou %? Tem de estar coberto por `tests/test_valores_ancora.py` — ver secção "CANÁRIO DE VALORES-ÂNCORA — TITLE/META DESCRIPTION"
- [ ] Página nova de prestação com valores anuais? `<title>`/description devem incluir o ano corrente; qualquer ano civil anterior citado tem de ter excepção explícita em `tests/test_anos_metadados.py` — ver secção "CANÁRIO DE ANOS EM METADADOS"
- [ ] Alterado algum `.py`? Correr `ruff check scripts/ --select E,F,W --ignore E501 .` — mesmo comando do job "Qualidade Python (Ruff)" em `integridade.yml` (nota: a `ruff-action` acrescenta a raiz do repo aos alvos, por isso `tests/` também é verificado, apesar do `scripts/` explícito no comando)
- [ ] Commit e push directamente para `main`
- [ ] Se o ambiente desta sessão impôs uma branch designada (`claude/<nome>`, imposta de fora do repositório — ver "REGRA ABSOLUTA — GIT" → "Protocolo de fim de sessão"), este último passo é substituído pelo protocolo de reporte de lá: terminar com o estado de integração explícito ("PR: #nn (aberto|merged)" ou "SEM PR — branch não integrada"), nunca com um commit/push directo a `main` que não é possível fazer. É uma imposição externa do harness, nunca uma flexibilização desta regra — a checklist não foi violada, só a via de chegada a `main` é diferente

---

## ESTRUTURA DE FICHEIROS ACTUAL

```
tens-direito/
├── *.html                    ← páginas estáticas publicadas (raiz = GitHub Pages)
├── assets/
│   ├── js/share.js           ← lógica do botão "Partilhar este artigo" (vanilla JS)
│   ├── js/nav.js             ← interacção da nav principal (dropdown, hamburger) — partilhado
│   ├── js/checklist.js       ← contador do bloco .checklist-final (vanilla JS, sem localStorage)
│   ├── css/share.css         ← estilo do botão/mensagens de partilha
│   ├── css/clusters.css      ← estilo do breadcrumb/pertence/relacionados injectados nos artigos
│   ├── css/nav.css           ← estilo da nav principal única (todas as páginas)
│   └── css/checklist.css     ← estilo do bloco .checklist-final (FASE 1 de MELHORIAS-SPEC.md)
├── scripts/
│   ├── scraper_playwright.py ← Playwright + BS4, scrapes 6 fontes
│   ├── extrair_valores.py    ← compara valores scraped vs HTML publicado
│   ├── gerar_noticias.py     ← RSS por tema + data/noticias.json → noticias.html + cards em index.html (NOTICIA-HOME)
│   ├── gerir_estado_feeds.py ← máquina de estados de feeds de notícias mortos (Step 3a do pipeline)
│   ├── migrar_noticias.py    ← migração única do noticias.html legado para data/noticias.json (não corre no pipeline)
│   ├── gerar_pagina.py       ← utilitário de geração HTML
│   ├── inserir_botao_partilhar.py ← insere assets/js/share.js + assets/css/share.css (idempotente)
│   ├── adicionar_canonicas.py ← insere <link rel="canonical"> auto-referente nas 35 páginas (idempotente)
│   ├── adicionar_og_image.py ← bootstrap: insere o bloco og:image em páginas novas (idempotente)
│   ├── gerar_og_images.py    ← gera assets/img/og/<slug>.jpg por página (Chromium real, manifest, idempotente)
│   ├── adicionar_article_jsonld.py ← insere JSON-LD Article (author/publisher/datas) nas 27 páginas de conteúdo (idempotente)
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
│   ├── validar_carimbos_elegiveis.py ← validação manual das simulações de carimbo (só leitura, sessão manual — passo humano do critério ≥14)
│   ├── sincronizar_clusters.py ← lê data/clusters.json, injecta breadcrumb/relacionados/pillar-lista (idempotente)
│   ├── sincronizar_nav.py    ← bootstrap + sincroniza a nav principal única (idempotente)
│   ├── limpar_css_morto_nav.py ← inventário/remoção de CSS morto da nav antiga (idempotente, --check p/ CI)
│   ├── inventario_css_morto.py ← generaliza o script acima a TODO o CSS do site (externo + inline), idempotente, `--check`/`--csv` disponíveis, não wired ao CI (ver "LIMPEZA DE CSS MORTO — SITE INTEIRO")
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
│   ├── noticias_candidatos.json ← log auditável de candidatos/decisões, últimos 14 dias (ver "FRESCURA DA HOMEPAGE")
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
11. **Valor legal em `<title>` ou meta description**: qualquer valor em € ou % com origem legal (IAS, um tecto/piso derivado do IAS, ou um valor próprio de Portaria/limiar) usado num `<title>` ou `<meta name="description">` tem de estar coberto por um teste em `tests/test_valores_ancora.py` — nunca pode ficar um valor "solto" em metadados, invisível a qualquer teste, a ficar errado em silêncio quando a lei mudar (ver secção "CANÁRIO DE VALORES-ÂNCORA — TITLE/META DESCRIPTION").
12. **Ano civil em `<title>` ou meta description**: um `<title>`/description de uma prestação com valores anuais deve incluir o ano corrente quando fizer sentido editorial (os utilizadores pesquisam com o ano, ex.: "cuidador informal 2026") — páginas atemporais (institucionais, hubs, quiz) ficam de fora por critério editorial, não por omissão. Qualquer ano civil *anterior* ao ano corrente num `<title>`/description tem de estar numa excepção explícita em `tests/test_anos_metadados.py` (citação de diploma legal ou facto histórico permanente) — nunca um esquecimento silencioso (ver secção "CANÁRIO DE ANOS EM METADADOS").

### Não fazer
- Não usar Jekyll ou qualquer SSG
- Não apagar `CNAME` nem `.nojekyll`
- Não publicar sem fonte datada
- Não dar veredictos pessoais ("tu tens direito a X")
- Contacto oficial = **contacto@tensdireito.com** (forwarding ImprovMX → caixa pessoal, activo desde 2026-07-03), sempre ofuscado via JavaScript (`.email-ofuscado`, `sobre.html`), nunca literal em HTML público
- Não usar subpaths de portais sem confirmar que devolvem 200
- **Páginas públicas nunca mencionam GitHub, repositório, código aberto, IA/inteligência artificial ou automação de redação** (decisão do Nuno, 2026-07-03) — vocabulário público é "a redação", "monitorização diária", "verificação contra fontes oficiais"; menções a GitHub/infra continuam permitidas em `scripts/`, workflows, `CLAUDE.md` e docs internos

---

## LINGUAGEM PARA O UTILIZADOR

Política editorial permanente (2026-07-14, na sequência da auditoria de
linguagem para baixa literacia digital — ver a entrada "Última revisão:
2026-07-14" que aplicou as correcções). O objectivo é que **qualquer
pessoa consiga usar o site, independentemente do nível de escolaridade ou
de literacia digital**. Aplica-se a todo o texto visível ao utilizador —
corpo dos artigos, títulos, botões, mensagens (sucesso/erro/aviso),
rótulos de campos, `placeholder` e `aria-label` — nunca a `scripts/`,
workflows, `CLAUDE.md` ou outros docs internos.

### Regras

1. **Português europeu simples.** Todo o texto visível é escrito em PT-PT
   claro e directo — nunca PT-BR (regra 1 de "REGRAS DE CONTEÚDO"), nunca
   frases que soem a tradução literal do inglês.
2. **Anglicismos só quando não há alternativa natural.** Preferir sempre a
   palavra portuguesa quando ela é igualmente clara: "navegador" (não
   "browser"), "palavra-passe" (não "password"), "descarregar" (não
   "download"), "iniciar sessão" (não "fazer login"), "página de
   simuladores" (não "hub"). Excepção: anglicismos plenamente
   estabelecidos em PT-PT e usados pelos próprios portais do Estado
   ("online", "site", "email", "app") — substituí-los pioraria a
   naturalidade, mantêm-se.
3. **Sem linguagem técnica de desenvolvimento no texto visível.** Termos
   como "cluster", "pipeline", "cache", "fallback", "área de
   transferência", "desagregação", "shadow mode" são jargão interno —
   nunca aparecem numa página. Descrever a funcionalidade por aquilo que
   ela faz ("mostra cada parcela do cálculo", "já a podes colar"), não
   pelo termo técnico.
4. **Siglas explicadas na primeira ocorrência da página.** Escrever o
   nome por extenso a primeira vez, com a sigla entre parênteses —
   "Chave Móvel Digital (CMD)", "Remuneração de Referência (RR)",
   "Certificado de Incapacidade Temporária (CIT)" — e só depois usar a
   sigla à solta. Uma checklist ou secção que possa ser lida isolada
   repete o nome por extenso.
5. **Termos oficiais pouco conhecidos vêm com explicação simples.** Os
   nomes legais das prestações e dos actos mantêm-se (é por eles que as
   pessoas pesquisam e é o que está nas cartas oficiais), mas emparelhados
   com o nome popular ou uma glosa curta: "Declaração de Situação
   Contributiva (a certidão de não dívida)", "deferido (aprovado)",
   "remuneração ilíquida (o salário bruto, antes dos descontos)". Nunca
   substituir o termo oficial — acrescentar a explicação ao lado.
6. **Consistência terminológica obrigatória em todo o site.** O mesmo
   conceito usa sempre a mesma palavra em todas as páginas — nunca
   "navegador" numa página e "browser" noutra. Antes de introduzir um
   termo novo, confirmar como o resto do site já lhe chama.

### Checklist antes de publicar uma página nova

Além da "CHECKLIST OBRIGATÓRIA ANTES DE QUALQUER COMMIT" (que continua a
aplicar-se por inteiro), qualquer página nova de conteúdo confirma:

- [ ] Linguagem simples — uma pessoa com baixa literacia digital percebe
- [ ] Português europeu, sem frases que soem a tradução literal do inglês
- [ ] Sem anglicismos desnecessários (ver regra 2 acima)
- [ ] Siglas explicadas por extenso na primeira ocorrência
- [ ] Termos legais/oficiais pouco conhecidos acompanhados de explicação simples
- [ ] Botões e mensagens (sucesso/erro/aviso) em linguagem clara e accionável
- [ ] Consistência terminológica com o resto do site

---

## ESTRUTURA HTML OBRIGATÓRIA POR PÁGINA

Ordem no `<head>`:
1. `<meta charset="UTF-8">`
2. Stub inline de consentimento (`window.dataLayer` + `gtag()` global + `gtag('consent','default',{...denied})`)
3. `<script src="/assets/js/consentimento.js" data-ga4="G-XP46PM8H1Q" defer>` — é este script que carrega o gtag.js (Consent Mode v2 avançado: para todos, sempre; cookies só depois de "Aceitar"); nunca um `<script>` gtag.js estático
4. favicon, viewport, title, description
5. OG tags: `og:title`, `og:description`, `og:url`, `og:type`, `og:locale`, `og:site_name`, `og:image` (+ `og:image:width/height/alt` e `twitter:card`) — imagem PRÓPRIA de cada página (1200×630, título do artigo + chip do cluster no cartão), gerada por `scripts/gerar_og_images.py` em `assets/img/og/<slug>.jpg`; `scripts/adicionar_og_image.py` é só o bootstrap do bloco de metas em páginas novas
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
   - `<!-- PILLAR-JSONLD:INICIO/FIM -->` — JSON-LD `CollectionPage` + `ItemList` da pillar page (no `<head>`), gerado por `render_pillar_jsonld()` (ver secção "SCHEMA.ORG — GRAFO DO SITE")
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

**Dívida técnica conhecida (fora do âmbito da Fase 4):**
- CSS morto da nav antiga — **totalmente limpo a 2026-07-07**, em duas
  passagens no mesmo dia, por `scripts/limpar_css_morto_nav.py`. Regra do
  script, deliberadamente global e conservadora: uma regra só é removida
  se TODOS os seletores exigirem um token (classe/id) ausente de TODAS as
  55 páginas servidas E não-adicionável por nenhum JS do site (mutações
  `classList.add/toggle`, `class=` em strings JS, `className=` — leituras
  tipo `querySelector` não contam); qualquer correspondência em qualquer
  página → AMBÍGUO, intocado, nunca removido "por o nome parecer antigo".
  1.ª passagem: 170 regras em 35 páginas (`.hamburger`, `nav a.nav-link*`,
  `.nav-mobile-sim-label/link`, `@media` esvaziados); as regras
  `.mobile-menu*` ficaram AMBÍGUAS porque 8 páginas ainda tinham um
  `<div id="menu-mobile" class="mobile-menu">` órfão da nav antiga (real,
  invisível). 2.ª passagem (aprovada pelo Nuno na mesma sessão): removidos
  os 8 divs órfãos, os 16 `<script>` inline mortos (`toggleMobileMenu`) e
  a variante própria do `index.html` (`toggleMenu`/`toggleSimDropdown`,
  ids `#mobileMenu`/`#navSimDropdown` inexistentes) — com o HTML residual
  fora, as 165 regras `.mobile-menu*` passaram a provadamente mortas e o
  próprio script limpou-as. **Zero resíduos da nav antiga em todas as 55
  páginas** (confirmado por grep de token exacto). O script mantém-se no
  repositório: `--check` (exit ≠ 0 se voltar a existir regra morta
  removível) e idempotência provada (2.ª corrida `--write` = zero
  alterações). Nota preventiva: o código morto propagava-se por cópia de
  páginas existentes ao criar páginas novas (ex.:
  `bolsa-de-estudo-ensino-superior.html`, publicada a 2026-07-06, já
  nasceu com o script morto) — com as 16 instâncias removidas, a fonte de
  contágio desapareceu; o template `estrutura-pagina.md` sempre esteve
  limpo.

Dois achados sinalizados no fecho da Fase 4 (não relacionados com o
ponto acima) — JSON-LD inválido em `simulador-ase.html` e OG
tags/disclaimer em falta nas páginas institucionais — **foram
corrigidos na Fase 5** — ver secção "PÁGINAS INSTITUCIONAIS" e o
commit de correcções da Fase 5.

---

## LIMPEZA DE CSS MORTO — SITE INTEIRO (2026-07-18)

Generaliza `limpar_css_morto_nav.py` (só cobria a família de tokens da nav
antiga, ver secção anterior) a **todo** o CSS do site: os 6 ficheiros de
`assets/css/*.css` e o `<style>` inline de cada uma das 70 páginas servidas
(raiz + `p/` + `documentos/`) — ~19KB de CSS externo + ~329KB de CSS
inline. Objectivo: reduzir ao que é usado, sem alterar um único pixel do
que renderiza. Conservador por desenho: um seletor só é removido se
**provado morto nas 3 camadas** — nunca por suspeita.

### `scripts/inventario_css_morto.py` — as 3 camadas de uso

Para cada classe/id exigido por um seletor, todas as camadas seguintes são
verificadas antes de declarar morto — encontrar o token numa só já chega
para manter a regra:

1. **HTML estático** das 70 páginas (`class=`/`id=` reais).
2. **JavaScript** — duas sub-camadas: mutações reais (`classList.add/
   toggle`, `class=`/`className=` atribuído por string) E uma verificação
   **permissiva de texto** — qualquer identificador-tipo-classe presente
   em qualquer ponto do ficheiro (`assets/js/*.js`, `scripts/pesquisa.js`,
   `<script>` inline de cada página) conta como usado. Esta 2.ª sub-camada
   foi necessária durante a sessão: `cor: 'escalo-1'` (dados do simulador
   de abono) e `tagCor: 'verde'` (dados do quiz de `comecar-aqui.html`)
   são strings literais guardadas num objecto de dados, nunca escritas
   como `classList.add('literal')` nem `class="literal"` — só aparecem
   depois de concatenadas/interpoladas em runtime. Sem esta camada, ambas
   ficariam como falsos-MORTO.
3. **Python** — mesmo princípio: qualquer identificador-tipo-classe
   presente em `scripts/*.py` conta como usado (ex.: `className:
   "gerador-form-group"` num objecto passado ao helper `elemento()` de
   `gerador-documentos.js` não é uma mutação `.className =`, é uma chave
   de objecto — só a verificação de texto ampla apanha isto).

Mais um mecanismo de **prefixos dinâmicos** (JS template literals `` `${var}`
`` e f-strings Python `{var}` dentro de `class="..."`) para o caso em que
a classe nunca aparece como string completa em lado nenhum — ex.:
`class="cat-badge cat-{item.categoria}"` em `scripts/gerar_noticias.py`
(as 6 categorias reais — `cat-apoios`/`cat-educacao`/`cat-emprego`/
`cat-habitacao`/`cat-fiscal`/`cat-legislacao` — já estavam de qualquer
forma presentes em `noticias.html` real, gerado pelo pipeline, por isso
esta sessão nunca precisou do mecanismo de facto — ficou como rede de
segurança para uma categoria nova sem notícia ainda publicada). Um token
que só bate com um prefixo dinâmico fica **AMBIGUO**, nunca removido.

Três categorias, nunca duas: **USADO** (confirmado nalguma camada) /
**AMBIGUO** (só prefixo dinâmico — fica, com justificação) /
**MORTO-CONFIRMADO** (ausente das 3 camadas E de qualquer prefixo
dinâmico — só estas são removidas). Um seletor sem classe/id exigido
(tag/pseudo/atributo puro — `body`, `:root`, `[data-mes]`, `a:hover`) é
sempre USADO por desenho, nunca há prova suficiente para o remover. Uma
regra com seletores separados por vírgula só é removível se **todos**
forem MORTO-CONFIRMADO.

### Bug apanhado antes de qualquer commit — colapso de whitespace global

A 1.ª versão da função de remoção reaproveitava a normalização de linhas
em branco de `limpar_css_morto_nav.py` mas aplicava-a ao texto **inteiro**
da fonte (`re.sub(...)` sobre toda a página), em vez de restrita ao
interior do `<style>` como o script original fazia. Confirmado por
`git diff` antes do commit: uma linha em branco do **corpo HTML** de
`rsi.html` (nada a ver com CSS) tinha sido apagada. Corrigido isolando o
colapso ao interior de cada `<style>` para fontes inline (CSS externo
continua a colapsar o ficheiro inteiro, que já é só CSS) — `git diff`
confirmado depois só a tocar nas linhas `<style>` removidas.

### Resultado desta sessão

Inventário: 3770 regras / 3921 seletores nas 76 fontes. Depois de afinar
as camadas JS/Python (1.ª passagem tinha 45 falsos-MORTO — quase todos
`.gerador-*` do gerador de documentos e `.resultado-card.escalo-N` do
simulador de abono, ambos por causa exactamente das duas lacunas
descritas acima): **9 selectores / 10 regras genuinamente mortas**, 1470
bytes removidos em 5 ficheiros —

- `assets/css/gerador-documentos.css`: `.gerador-aviso-formulario`
  (+ `a`) e `.gerador-card` (+ variante `@media`) — nunca usadas por
  nenhuma das 12 páginas do gerador (confirmado por grep dedicado antes
  de remover; provavelmente resíduo de uma iteração de design anterior à
  implementação actual).
- `index.html`: `.apoio-card.em-breve`, `.apoio-card .badge-breve`,
  `.apoio-card .link-aviso` — estilos de placeholder "em breve" de uma
  fase anterior do site (todos os `.apoio-card` reais de hoje são links
  simples, sem sub-elementos de aviso).
- `baixa-medica-subsidio-doenca.html` e `subsidio-desemprego.html`:
  `.aviso-ss` — superado por `.aviso-info` (mesmas cores/borda,
  introduzida depois), nunca usada em nenhuma das duas páginas.
- `rsi.html`: `.aviso-valores` — nunca referenciada no corpo da página.

Zero AMBIGUOS por resolver nesta sessão (a lista ficou vazia depois das
duas camadas de texto — nada por justificar/deixar para trás).

### Baseline visual — zero diferenças

Screenshots Chromium reais (375px e 1200px) de 10 páginas representativas
(`index`, pillar PSU, cluster Família, calendário, simulador de abono,
hub Como Pedir, `comecar-aqui`, uma página do gerador de documentos,
`noticias`, `404`) antes e depois da remoção, comparadas pixel-a-pixel
(`PIL.ImageChops.difference`, `bbox()` teria apanhado qualquer diferença,
por mínima que fosse): **20/20 capturas idênticas byte-a-byte** — zero
diferença visual, confirmando que as 10 regras removidas eram mesmo
inertes.

### Guardrail — decisão de não adicionar ao CI (Fase 4)

`--check` funciona (exit ≠ 0 se sobrar alguma regra morta removível,
confirmado a passar depois da remoção) e a remoção é idempotente (2.ª
corrida = zero alterações). **Decisão desta sessão: não adicionar ao
CI**, pelo mesmo motivo por que `limpar_css_morto_nav.py --check` (a sua
irmã, já existente antes desta sessão) nunca foi ligado a
`integridade.yml` apesar do comentário "p/ CI" no ficheiro — a
verificação de texto ampla das camadas JS/Python é deliberadamente
permissiva para nunca remover algo em uso (prioridade correcta), mas
isso significa que um padrão de construção de classe genuinamente novo
(uma variável cujo valor nunca aparece como substring em lado nenhum do
JS/Python, só computado em runtime a partir de dados externos) escaparia
às 3 camadas e apareceria como MORTO-CONFIRMADO por engano — um falso
positivo que partiria o CI por uma razão que não é responsabilidade de
quem fez o commit a resolver. Mesma lição já registada por esta sessão
para os dois casos reais encontrados (`escalo-N`, `tagCor`) — a lista de
padrões dinâmicos nunca pode ser assumida completa. `--check`/`--csv`
ficam disponíveis para verificação manual periódica (mesmo padrão da
irmã) — correr `python scripts/inventario_css_morto.py` (sem flags) numa
sessão dedicada, nunca como gate automático.

Suite completa + `scripts/verificar_skips_permitidos.py` + axe-core
reconfirmados sem regressões (ver entrada de revisão no fim deste
ficheiro para os números exactos); `ruff check scripts/
inventario_css_morto.py --select E,F,W --ignore E501` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados
(script não tem relação com o Shadow Mode).

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
3. **CSS morto da nav antiga** — ~~limpeza cosmética nos `<style>`
   de cada página~~ **concluído a 2026-07-07** (`scripts/limpar_css_morto_nav.py`,
   duas passagens: CSS morto + HTML/JS residual) — zero resíduos da nav
   antiga nas 55 páginas; ver secção "NAVEGAÇÃO PRINCIPAL" (dívida técnica).

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
- `data/noticias_candidatos.json` — log auditável dos últimos 14 dias
  (retenção por dias corridos, não por n.º de corridas — 2 corridas no
  mesmo dia, ex.: `workflow_dispatch` manual, nunca expulsam uma
  entrada de um dia mais antigo fora de tempo). **Revisto em
  2026-07-04** para auditoria completa: em vez de só top 3 + rejeitados
  parciais (o `selecionar_vencedor()` original pára assim que encontra
  um vencedor, por isso nunca classificava os candidatos a seguir),
  `analisar_candidatos_na_janela()` classifica **todos** os candidatos
  dentro da janela de recência (título, feed, data, score, decisão —
  `vencedor`/`rejeitado_score`/`rejeitado_duplicado`/`nao_escolhido`),
  para que "o sistema viu a notícia X?" tenha sempre resposta. Os
  candidatos fora da janela ficam só como contagem por feed
  (`fora_da_janela_por_feed`) — o título deles já não interessa para
  auditoria, nunca poderiam vencer. `analisar_candidatos_na_janela()`
  reimplementa deliberadamente a mesma lógica de `selecionar_vencedor()`
  em vez de a reutilizar — o objectivo é classificar tudo, não só
  encontrar o primeiro vencedor (early-exit deixaria de fazer sentido).

Testado em `tests/test_gerar_noticias.py` (corte de recência, saúde de
feed, classificação completa de candidatos, retenção por dias),
`tests/test_estado_feeds.py` (máquina de estados, mesmos casos de
`test_estado_fontes.py`) e `tests/test_gerar_noticias_guardrail.py`
(allow-list dos 2 novos ficheiros).

**Verificado no pipeline real** (`workflow_dispatch` de
`pipeline-diario.yml`, não só no runner de diagnóstico): ver entrada de
revisão no fim deste ficheiro para o resultado real, não assumido.

---

## RESPOSTA RÁPIDA + CHECKLIST FINAL (FASE 1 de MELHORIAS-SPEC.md)

Dois componentes reutilizáveis, aplicados nesta fase a 4 artigos:
`baixa-medica-subsidio-doenca.html` (alvo explícito da spec) e os 3
artigos com mais tráfego GSC confirmados pelo Nuno —
`manuais-escolares-mega.html`, `acao-social-escolar.html`,
`subsidio-desemprego.html`.

### `.resposta-rapida` — reaproveita `.resposta-direta`, não duplica

Achado antes de implementar: os ~28 artigos do site já têm um bloco
`.resposta-direta` no hero (caixa teal, resposta directa de 2-3 frases)
com exactamente o mesmo objectivo SEO (featured snippet) que a spec
pede para `.resposta-rapida`. Decisão (confirmada com o Nuno): **nunca
duplicar a caixa** — a mesma `.resposta-direta` ganhou a classe extra
`resposta-rapida` mais dois elementos novos:

```html
<div class="resposta-direta resposta-rapida">
  <span class="resposta-rapida-label">⚡ Resposta rápida</span>
  <p class="resposta-rapida-texto">[texto já existente, ≤60 palavras]</p>
  <span class="resposta-rapida-tempo">📖 Leitura completa: X min</span>
</div>
```

CSS inline por página (mesmo padrão de `.resposta-direta`, nunca um
ficheiro partilhado — cada artigo já define os seus próprios
componentes inline). Tempo de leitura calculado uma vez (palavras do
`<main>` ÷ 200 ppm, arredondado) e escrito como texto estático — não é
recalculado em runtime. **Achado de acessibilidade durante a
implementação**: a 1.ª versão usava `opacity` no rótulo/tempo para
hierarquia visual — reduzia o contraste do texto branco sobre o fundo
teal (`#0F766E`) de 5.47:1 para 4.41:1, abaixo do mínimo AA de 4.5:1
(apanhado por `tests/test_acessibilidade.py`, não por inspecção visual).
Corrigido removendo o `opacity` — texto branco sólido, mesmo contraste
já auditado e aprovado do resto do `.resposta-direta`.

### `.checklist-final` — novo, reutilizável via `assets/`

Ao contrário de `.resposta-direta`, este componente é genuinamente
novo. Segue o padrão de `share.js`/`share.css` (ficheiro partilhado em
`assets/`, ligado via `<link>`/`<script>` no `<head>`, nunca duplicado
inline por página):

- **`assets/css/checklist.css`** — caixa no mesmo estilo de `.card`,
  contador de progresso, lista de checkboxes com touch target ≥44px
  (o `<label>` inteiro é o alvo clicável, não só a checkbox de 22px).
- **`assets/js/checklist.js`** — actualiza o contador ("X de N
  concluídos") em `change`, delegado em `document` (mesmo padrão de
  `share.js`). **Estado só em memória** — nunca chama
  `localStorage`/`sessionStorage`; recarregar a página repõe todas as
  checkboxes por marcar, por desenho, exactamente como a spec exige.

HTML por artigo (sem ficheiro de template — cada página escreve o seu
próprio `<section class="checklist-final">`, com itens sourced do
`HowTo` JSON-LD já publicado nessa página, nunca inventados):

```html
<section class="checklist-final" aria-label="Checklist final">
  <h2>Checklist: [tarefa do artigo]</h2>
  <p class="checklist-progresso" aria-live="polite">0 de N concluídos</p>
  <ul class="checklist-lista">
    <li><label><input type="checkbox"><span>[item accionável]</span></label></li>
    ...
  </ul>
</section>
```

Posicionado antes da secção "Dúvidas frequentes" nos 3 artigos que a
têm; `manuais-escolares-mega.html` não tem uma secção de FAQ visível
dedicada (só JSON-LD) — o checklist foi colocado antes de
`RELACIONADOS`, ainda assim no fim do corpo do artigo, sem inventar uma
secção que a página não tem.

**Achado lateral, não relacionado com os blocos novos**: ao validar
`acao-social-escolar.html` com o `vnu.jar` (HTML5), encontrado um bug
pré-existente (não introduzido nesta sessão, confirmado por
`git show HEAD`) — um `<div class="tabela-wrap">` (tabela) dentro de um
`<span>` no passo 1 do "Como candidatar", inválido porque `<span>` só
aceita conteúdo de fraseado. Corrigido trocando esse `<span>` por
`<div>` (o `<ol>` já usa `display:flex` via `.passos li`, que
"blockifica" o filho de qualquer forma — zero mudança visual) e
ajustada a regra CSS `.passos li span` para `.passos li span, .passos
li > div`, preservando a cor/alinhamento exactos.

### Retrofit dos 3 artigos GSC — decisão do Nuno, não assumida

A spec pedia "retrofit nos 3 artigos com mais tráfego GSC (confirmar
quais na sessão)" — sem acesso ao Google Search Console, a sessão
perguntou directamente e o Nuno confirmou os 3: `manuais-escolares-
mega.html`, `acao-social-escolar.html`, `subsidio-desemprego.html`.
Não são um palpite nem um valor por omissão.

### Testes

`tests/test_resposta_rapida_checklist.py` (37 casos, parametrizados
sobre os 4 artigos reais): estrutural (rótulo + tempo presentes, ≤60
palavras, caixa continua dentro do hero, checklist com checkboxes
dentro de `<label>`, ordem antes do FAQ, assets ligados no `<head>`,
`checklist.js` nunca chama `localStorage`/`sessionStorage`) e funcional
via Chromium real (viewport mobile 390px sem overflow horizontal nos 2
blocos, contador a actualizar ao marcar/desmarcar, e a garantia
explícita de que um reload nunca preserva o estado das checkboxes —
requisito "SEM localStorage" da spec, verificado a sério, não só por
ausência da string no código). Suite existente (`test_nav_coerencia.py`,
`test_breadcrumb_coerencia.py`, `test_higiene_indexacao.py`,
`test_acessibilidade.py`) reconfirmada sem regressões nos 4 artigos
tocados.

### Critérios de aceitação da spec — confirmados

- Blocos renderizam correctamente em mobile (viewport 390px) — testado
  com Chromium real, sem overflow horizontal.
- Validação HTML5 passa — confirmado com `vnu.jar` nas 4 páginas
  (incluindo a correcção do bug pré-existente acima).
- Zero dependências externas novas — `checklist.js`/`checklist.css` são
  vanilla JS/CSS, mesmo padrão de `share.js`/`share.css`.

---

## GERADOR DE DOCUMENTOS

Diferenciador do site (2026-07-06, Sessão 1 de 2 —
`PROMPTGERADORDOCUMENTOSv1.md`): minutas de requerimentos, reclamações e
cartas dirigidas à Segurança Social, geradas 100% no browser. Ver
`ROADMAP.md` → "GERADOR DE DOCUMENTOS — ESTADO" para o índice rápido do
que falta para a Sessão 2.

### Arquitectura — motor único config-driven

Nenhuma minuta tem JS próprio:

- **`assets/js/gerador-documentos.js`** — motor genérico. Lê um objecto
  `CONFIG_DOCUMENTO` (inline, `<script>` no fim da página), renderiza o
  formulário a partir de `CONFIG_DOCUMENTO.campos`, valida obrigatórios
  + padrões (regex) antes de gerar, substitui `{{campo}}` no
  `template`, e mostra o resultado num `<pre>` com botão **Copiar**
  (Clipboard API, fallback `execCommand`) e **Descarregar .txt** (Blob
  + URL). Campos opcionais vazios resolvem para `campo.valorVazio`
  (por omissão, string vazia); campos `tipo: "date"` são formatados
  automaticamente de ISO para `DD/MM/AAAA`; `data_hoje`/
  `data_hoje_extenso` são injectados automaticamente em todos os
  templates, sem serem campos do formulário.
- **`assets/css/gerador-documentos.css`** — estilo partilhado
  (`.gerador-*`), mesmo padrão visual dos simuladores.
- **`documentos/*.html`** — uma página por minuta (landing page própria
  para SEO). `documentos/*.html` foi acrescentado a
  `encontrar_paginas()` em `scripts/sincronizar_clusters.py` (mesmo
  padrão de `p/*.html`) — por isso as páginas desta pasta entram
  automaticamente em todos os testes que já usam essa função
  (`test_nav_coerencia.py`, `test_higiene_indexacao.py`,
  `test_acessibilidade.py`, `test_pesquisa_indice.py`).
- **`/documentos.html`** — hub com cards, mesmo padrão de
  `/simuladores.html`.

**Restrição dura verificada por teste real** (`tests/test_gerador_documentos.py::test_zero_pedidos_de_rede_ao_interagir_com_o_gerador`):
zero chamadas de rede depois do load, mesmo ao gerar o documento — por
isso o motor **nunca** dispara eventos GA4 ao clicar em "Gerar
documento" (ao contrário dos simuladores, que disparam `calc_resultado`
via `gtag`). Decisão deliberada desta sessão: o próprio prompt exige um
teste de rede que falha com qualquer pedido, e um evento GA4 é uma
chamada de rede real — a mensagem "os dados que preenches nunca saem do
teu dispositivo" tem de ser verificada a sério, não só quanto ao
conteúdo do formulário. Zero `localStorage`/`sessionStorage` — estado
só em memória (mesmo padrão de `checklist.js`).

### Integração no sistema de clusters — decisão desta sessão

`cluster_da_pagina()`/`processar_pagina()` em `sincronizar_clusters.py`
comparam `Pagina.slug` só contra `caminho.name` (basename) — desenhado
para páginas na raiz, nunca precisou de suportar sub-caminhos como
`documentos/...` (ao contrário do `pillar`, que já tinha uma função
própria, `cluster_do_pillar()`, para caminhos com `/`). Estender o
matching de `paginas[].slug` para aceitar sub-caminhos é um refactor à
parte, fora do âmbito desta sessão. Por isso as 4 páginas do gerador
(`documentos.html` + as 3 minutas) ficam em `EXCLUIDAS` — mesma
categoria de `comecar-aqui.html`/`simuladores.html` — e a integração é
feita inteiramente por fora do sistema de clusters: nav (link "📄
Documentos" em `scripts/sincronizar_nav.py`, mesmo padrão do link
"🧮 Simuladores"), `sitemap.xml`, `scripts/pesquisa.js`, cards no hub
`/documentos.html`, e cross-links manuais a partir de
`abono-de-familia.html` e `complemento-solidario-idosos.html` para as
duas cartas de acompanhamento respectivas. *Registado para o futuro*:
se o número de minutas crescer muito, vale a pena generalizar
`Pagina.slug` para aceitar caminhos relativos completos e dar-lhes
cluster membership a sério (badge "Ferramenta" no `PILLAR-LISTA`,
contagem no cartão da homepage) — não decidido, sem prazo.

### PORTÃO DE VERIFICAÇÃO — resultado das 3 candidatas da Sessão 1

Núcleo do prompt original, as 3 candidatas de maior prioridade,
verificadas uma a uma antes de escrever qualquer template:

1. **Reclamação de decisão da Segurança Social** — **publicada
   integralmente** (`documentos/reclamacao-decisao-seguranca-social.html`).
   Verificado via pesquisa a fontes que reproduzem o texto consolidado
   do Código do Procedimento Administrativo (Decreto-Lei n.º 4/2015, de
   7 de janeiro): o artigo 191.º consagra a reclamação em regime geral,
   **sem exigir formulário próprio** — um texto livre e fundamentado é
   um canal legítimo, com prazo geral de 15 dias úteis "quando a lei
   não estabeleça prazo diferente" e decisão em 30 dias (artigo 192.º,
   n.º 2); recurso hierárquico nos artigos 193.º a 198.º. É a única das
   3 candidatas que não precisou de pivot.
2. **Pedido de reavaliação de escalão de abono de família** — **pivot
   obrigatório**, diferente do que o prompt original assumia (só
   sinalizava pivot como "provável" para a CSI). Achado: o nosso
   próprio artigo já fact-checked `abono-de-familia.html` documenta
   que a reavaliação usa o **Modelo GF58-DGSS** (disponível em
   seg-social.pt) e que o canal normal e mais rápido é o **pedido
   online** na Segurança Social Direta (Família → Abono de Família →
   Pedido de reavaliação do escalão), com uma carência de 90 dias desde
   a última verificação/alteração. Publicada como
   `documentos/carta-acompanhamento-reavaliacao-abono.html` — carta de
   acompanhamento do Modelo GF58-DGSS, nunca um substituto, com aviso
   destacado (`.aviso-pivot`) a apontar primeiro para o canal online.
3. **CSI** — **pivot confirmado**, exactamente como o prompt
   antecipava. O nosso próprio artigo já fact-checked
   `complemento-solidario-idosos.html` documenta "Modelos CSI 1, CSI
   1/1 e CSI 1/2 (obrigatório)" — requerimento inicial de prestação,
   caso típico da regra do portão ("nunca apresentar uma minuta como
   substituto de um Mod. oficial"). Publicada como
   `documentos/carta-acompanhamento-csi.html` — carta de
   acompanhamento, com link directo para `seg-social.pt/formularios`.

**Nenhuma candidata ficou de fora na Sessão 1** — as 3 do núcleo
passaram o portão (2 com pivot, 1 sem).

### PORTÃO DE VERIFICAÇÃO — resultado das candidatas 4-12 (Sessão 2, 2026-07-06)

As 9 candidatas de expansão do prompt foram todas verificadas e
publicadas — **nenhuma rejeitada**, 6 sem pivot e 3 com pivot:

4. **Recurso hierárquico de decisão da Segurança Social** — publicado
   sem pivot (`documentos/recurso-hierarquico-seguranca-social.html`).
   Artigos 193.º a 198.º do CPA, sem Mod. próprio — complementa a
   reclamação já publicada (dirigido ao superior hierárquico, não ao
   mesmo órgão que decidiu).
5. **Pedido de pagamento de dívida à SS em prestações** — **pivot**
   (`documentos/carta-acompanhamento-divida-prestacoes.html`).
   Confirmado Mod. próprio: "Requerimento para Pagamento em
   Prestações" (IMP.PN.01.01), submetido via Segurança Social Direta
   ou por email para igfss-divida@seg-social.pt.
6. **Comunicação de alteração de agregado/morada/rendimentos** —
   **pivot** (`documentos/carta-acompanhamento-comunicacao-alteracao.html`).
   Desde jul. 2023 existe a "Declaração de Situação Familiar" na
   Segurança Social Direta como canal principal; formulários mais
   antigos ligados a encargos familiares (Mod. GF 37-DGSS, Mod. GF
   54-DGSS) também encontrados — sem Mod. universal único, tratado
   como pivot por prudência (mesma lição do GF58).
7. **Exposição por atraso no processamento de prestação** — publicado
   sem pivot (`documentos/exposicao-atraso-processamento.html`).
   Artigos 128.º (prazo geral de 90 dias) e 129.º (dever de decisão)
   do CPA — sem Mod. próprio.
8. **Reclamação de decisão do SVI / junta médica** — **pivot**
   (`documentos/carta-acompanhamento-svi-recurso.html`). Confirmado
   Mod. SVI 55-DGSS obrigatório ("Requerimento — Comissão de
   Reavaliação/Comissão de Recurso"), prazo de **10 dias** — mais
   curto do que os 15 dias da reclamação em regime geral, destacado na
   página. Distinto do processo de recurso do AMIM (JMAI, Ministério
   da Saúde, 30 dias) — **nunca cross-linkado com `amim.html`
   deliberadamente**, para não conflacionar os dois sistemas de junta
   médica diferentes (SVI é da Segurança Social, para prestações
   contributivas; AMIM é da Saúde, atestado multiuso).
9. **Pedido de reavaliação de escalão ASE** — publicado sem pivot
   (`documentos/requerimento-reavaliacao-escalao-ase.html`). Processo
   descentralizado por agrupamento de escolas, sem Mod. nacional da
   DGE — página recomenda confirmar se a escola tem impresso próprio.
10. **Pedido de consulta do processo / acesso a documentos (CPA)** —
    publicado sem pivot (`documentos/pedido-acesso-documentos-administrativos.html`).
    Lei n.º 26/2016 (LADA), artigo 12.º exige só requerimento escrito
    (sem Mod. numerado), artigo 15.º fixa prazo de 10 dias úteis.
11. **Requerimento genérico à Segurança Social** — publicado sem pivot
    (`documentos/requerimento-generico-seguranca-social.html`).
    Template catch-all, direito de petição (artigo 52.º CRP) — página
    avisa explicitamente para nunca ser usado a substituir um Mod.
    oficial existente nem para contestar uma decisão já tomada.
12. **Pedido de declaração/comprovativo de situação de prestações** —
    publicado sem pivot forte (`documentos/pedido-declaracao-comprovativo-prestacoes.html`).
    Sem Mod. numerado — emitido em auto-serviço pela Segurança Social
    Direta; a página recomenda esse canal como mais rápido e trata
    esta minuta como alternativa em papel.

**Excluída à partida** (decisão do prompt original, nunca avaliada):
procurações e qualquer documento com efeitos de representação legal.

### Integração e cross-links da Sessão 2

Mesmo padrão da Sessão 1: as 9 páginas novas entram em `EXCLUIDAS` de
`sincronizar_clusters.py` (mesma limitação de sub-caminhos já
documentada acima), hub `/documentos.html` ganhou 9 cards novos,
`sitemap.xml`/`scripts/pesquisa.js` actualizados. Cross-links
adicionados: `reclamacao-decisao-seguranca-social.html` → recurso
hierárquico (FAQ); `acao-social-escolar.html` → requerimento de
reavaliação de ASE (FAQ já existente sobre reavaliação); `abono-de-familia.html`
→ carta de comunicação de alteração; e um aviso novo (`aviso-info`,
reaproveitando a classe já existente onde disponível) em
`rsi.html`/`subsidio-desemprego.html`/`baixa-medica-subsidio-doenca.html`/
`prestacao-social-para-a-inclusao.html` a apontar para a reclamação —
nenhuma destas 4 páginas tinha até agora qualquer menção a "o que fazer
se o pedido for indeferido".

**Título da carta de CSI encurtado** (79 → 50 caracteres): a versão da
Sessão 1 incluía o sufixo "— não substitui o Mod. CSI 1" no `<title>`,
arriscando corte no Google (o `og:title` já usava a versão curta,
inconsistência corrigida). Meta descriptions das 3 páginas da Sessão 1
também revistas para CTR (mais curtas, lideram com a pergunta/benefício
concreto, sem repetir "Gera uma..." em todas).

**Achado real, corrigido antes do commit**: um teste falhou
(`test_sem_ano_civil_desactualizado_em_title_ou_description`) porque a
meta description do pedido de acesso a documentos cita "Lei n.º
26/2016" — o canário de anos em metadados apanhou correctamente "2016"
como um ano potencialmente desactualizado. Mesma categoria já
documentada para `cuidador-informal.html`/`subsidio-desemprego.html`
(número de diploma, não data de vigência) — nova excepção registada em
`EXCECOES_ANOS_HISTORICOS` (`tests/test_anos_metadados.py`).

Suite completa: **1738 passed, 4 skipped** (76 testes novos: 45 golden
tests do gerador — 5 por página × 9 páginas novas — mais 31 de
higiene/nav/pesquisa/acessibilidade parametrizados sobre as páginas
reais); `ruff check scripts/ tests/ --select E,F,W --ignore E501 .`
limpo.

**Excluída à partida, conforme instrução do prompt**: procurações e
qualquer documento com efeitos de representação legal — nunca
avaliadas nem candidatas, decisão tomada antes de qualquer
verificação.

### Disclaimer obrigatório

Presente em texto idêntico nas 4 páginas E no texto gerado de cada
minuta (verificado por `tests/test_gerador_documentos.py::test_disclaimer_presente_na_pagina_e_no_texto_gerado`):
> "Este documento é um modelo informativo e não substitui aconselhamento
> jurídico. Confirme sempre os requisitos junto da Segurança Social ou de
> um advogado/solicitador."

### Testes desta sessão

`tests/test_gerador_documentos.py` (17 testes, Chromium real via
Playwright, mesmo padrão de `test_acessibilidade.py` — nunca `file://`):
formulário preenchido gera texto com todos os campos, campo obrigatório
vazio bloqueia + mostra erro, NISS inválido bloqueia com mensagem de
padrão, disclaimer presente na página e no texto gerado, botão Copiar
existe e fica activo após gerar, consistência do hub (cada card aponta
para ficheiro real, cada minuta linka de volta), e zero pedidos de rede
ao interagir com o gerador. Genérico sobre as 3 páginas via
`page.evaluate("CONFIG_DOCUMENTO")` — nunca hardcoded por minuta, mesma
filosofia de `test_simulador_csi_calculo.py`. Mais: `test_nav_tem_link_documentos`
novo em `tests/test_nav_coerencia.py` (mesmo padrão de
`test_nav_tem_link_simuladores`). Suite completa reconfirmada sem
regressões (ver entrada de revisão no fim deste ficheiro), ruff limpo.

---

## CALENDÁRIO DE PAGAMENTOS DA SEGURANÇA SOCIAL

Página evergreen `calendario-pagamentos-seguranca-social.html` (Fases
0+1+2 de `CALENDARIO-PAGAMENTOS-SPEC.md`, 2026-07-12 — documento
externo, mesmo padrão de `MELHORIAS-SPEC.md`). URL única que acumula
autoridade; o conteúdo do mês é injectado, nunca reescrito à mão.

**Invariante crítico**: a página NUNCA mostra um mês passado como
corrente, e nenhuma data vem de memória — só da fonte oficial da
Segurança Social (ver `docs/FONTE-CALENDARIO.md`, Fase 0: notícia
mensal no portal antigo + página Calendário do portal novo `/ptss/pssd/`;
⚠️ o slug da notícia é reciclável entre meses — validar sempre o mês no
CONTEÚDO, nunca no URL). Sem dados do mês corrente, a página degrada
para um bloco explícito "consultar fonte oficial" com link — nunca uma
tabela velha silenciosa.

### Arquitectura

- **`data/calendario_pagamentos.json`** — fonte de verdade
  (`atualizado_em`, `fonte_url`, `meses[].pagamentos[]` com
  dia/prestações/método/nota). Julho 2026 triangulado por ≥5 fontes
  independentes que reproduzem o calendário oficial (seg-social.pt
  bloqueado nesta sessão — mesmo padrão de fact-check documentado para
  o cluster Habitação). **Agosto deliberadamente ausente**: as únicas
  fontes eram indistinguíveis de previsão por regra de dias fixos.
- **`scripts/atualizar_calendario.py`** — injecção idempotente (2.ª
  corrida = zero alterações, `--dry-run` disponível), confinada a dois
  marcadores: `CAL:META:INICIO/FIM` (title + meta description com o mês
  corrente) e `CAL:CORPO:INICIO/FIM` (tabela do mês, secção "Quando
  recebo a minha prestação?" com as âncoras da spec —
  `#pensoes`/`#csi`/`#psi`/`#abono-familia`/`#subsidio-desemprego`/
  `#subsidio-doenca`/`#rsi`/`#apoio-renda`/`#cuidador-informal` — e o
  mês seguinte quando disponível). Validação dura antes de escrever
  (allow-list `PRESTACOES`, dias 1-31, listas não vazias, `fonte_url`
  só de seg-social.pt, mês duplicado) — falha sem tocar no HTML.
  Meses passados nunca são renderizados, mesmo presentes no JSON.
- **`og:title` estável, sem mês** (decisão deliberada): o manifest das
  imagens og (`tests/test_og_image.py`) exige og:title == manifest —
  um og:title mensal obrigaria a regenerar a imagem (Chromium) todos os
  meses. Só `<title>`/description variam com o mês.
- **Destaque "Próximo pagamento" no topo** (2026-07-12, pedido do Nuno —
  é a informação por que a maioria vem à página): logo no início do
  conteúdo, antes da tabela, o injector escreve duas camadas, ambas sem
  rede — (1) estática, sempre visível mesmo sem JS, com todas as datas
  do mês num relance (`.cal-destaque-linha`); (2) `#cal-dados` (JSON com
  `dia`+`resumo` curto por pagamento) que o script de runtime lê para
  **promover a próxima data a contar de hoje** (`.cal-destaque-proximo`:
  "📅 Próximo pagamento: 16 de julho · …"). Só promove quando o mês
  renderizado é o mês corrente do visitante — num mês velho (aviso de
  desatualização activo) ou no estado degradado nunca inventa um
  "próximo", e a camada estática mantém-se. `RESUMO_CURTO` em
  `atualizar_calendario.py` dá os rótulos curtos (a tabela mantém os
  nomes longos). Testado com Chromium real (promoção do dia certo,
  ausência de promoção num mês velho, linha estática sempre visível,
  0px de overflow a 375px).
- **Guarda JS em runtime** (progressive enhancement, zero rede): script
  inline compara `#cal-corrente[data-mes]` com a data do visitante e
  mostra `#cal-aviso-desatualizado` se a página tiver ficado velha —
  testado com Chromium real (cópia adulterada com mês anterior mostra o
  aviso; estado normal não).
- **`tests/test_calendario_frescura.py`** — canário de frescura (FALHA
  quando o mês renderizado < mês real: CI vermelho força actualização —
  provado a falhar de propósito com `data-mes` adulterado, e revertido),
  sincronização página↔script↔JSON, estado degradado (JSON vazio ou só
  com meses passados nunca rende tabela), e os caminhos de falha da
  validação. Adiantado da Fase 4 só este núcleo do invariante; o resto
  (Playwright mobile no CI, workflow) fica para a sessão da Fase 3+4.
- Integração: `EXCLUIDAS` em `sincronizar_clusters.py` (página
  utilitária cross-cluster, mesma categoria de `simuladores.html`),
  nav/sitemap/pesquisa.js/og-image próprios, cross-links nos dois
  sentidos com 7 páginas de prestações (parágrafo "📅 Em que dia do mês
  é pago?" antes do bloco de fontes, com âncora directa) + botão em
  `comecar-aqui.html` (link sem âncora — o grafo de órfãs de
  `test_higiene_indexacao.py` não segue hrefs com `#fragmento`, achado
  real desta sessão).

### Fases 3+4 — IMPLEMENTADAS (2026-07-12, mesma data das Fases 0-2)

**FONTE PÚBLICA REAL — scraping automático (2026-07-12, pista do Nuno;
detalhe em `docs/FONTE-CALENDARIO.md`)**: `https://www.seg-social.pt/ptss/pssd/pagamentos`
é uma página PÚBLICA (HTTP 200, NÃO redirecciona para o gateway de
login), SPA com um separador por mês; ao clicar num mês mostra a tabela
oficial (dia → prestações → método), com as datas publicadas antes do
início do mês. Uma ronda de diagnóstico anterior tinha concluído,
erradamente, que "scraping é impossível" — porque testou `/pagamentos2`,
`/noticias` e o "Calendário" de valores-a-receber (esses de facto
inúteis), mas **não** este URL. Confirmado num runner e implementado
scraping automático de verdade; o fluxo manual passa a ser só o
*fallback*.

- **`scripts/scraper_calendario.py`** — `parse_innertext()` (função pura:
  texto do painel do mês → schema do JSON; testada com o texto REAL de
  agosto) + `raspar_mes()` (Playwright: clica no separador do mês, espera
  pelo cabeçalho do mês E por uma linha de método + settle, extrai).
  Mapeamento estrito `NOME_PARA_SLUG`; prestação fora da allow-list, mês
  vazio ou método órfão fazem **falhar** (`ScraperError`) — nunca
  descarta em silêncio (INVARIANTE). Prestação nova real já apanhada por
  aqui: "Subsídio por Suspensão da Atividade Cultural" (dia 21 de agosto).
- **`.github/workflows/calendario-mensal.yml`** — dia 25 + retry 28
  (alvo: mês seguinte) e dia 1 às 05:30 (alvo: mês corrente — vira a
  página quando o JSON já tem o mês novo); `workflow_dispatch` com
  input `forcar_seguinte`. Se o JSON tem o mês alvo → injecção
  idempotente + `pytest tests/test_calendario_frescura.py` + guardrail
  (falha se QUALQUER ficheiro fora do JSON + página aparecer
  modificado) + commit/push + `garantir_deploy_pages.sh` + smoke
  inline; fecha automaticamente a Issue `calendario-manual` do mês.
  Se não tem → **tenta o scraper**; sucesso grava o mês no JSON e segue
  `dados_ok`. Só se o scraper falhar → **nunca commit parcial**: sonda
  as rotas oficiais e abre/actualiza (dedup por título) a Issue
  `calendario-manual` com o erro do scraper + sonda + prompt pronto.
  `concurrency: main-writes`.
- **`scripts/verificar_calendario_mensal.py`** — decide o mês alvo
  (dia ≥ 20 → mês seguinte); se o JSON não o tem, chama
  `tentar_scraper_e_gravar()` (grava só dados que passem a validação);
  fallback = sonda `/ptss/pssd/noticias` + Issue. Emite `estado`/
  `mes_alvo` via `GITHUB_OUTPUT`.
- Provado ponta-a-ponta num runner: **agosto de 2026 foi raspado ao
  vivo da fonte oficial, validado, injectado e commitado automaticamente**
  (`fonte_url` do JSON passou para `/ptss/pssd/pagamentos`; run mensal
  29201776013 → commit do bot `3f1dca8`; Issue manual de agosto fechada
  sozinha). `tests/test_scraper_calendario.py` tranca o parser com o
  texto real + os caminhos de falha. Fase 4 completa:
  `tests/test_calendario_frescura.py` tem os testes Playwright mobile
  (375px sem overflow, 9 âncoras, navegação por âncora, guarda JS com
  mês velho em memória).

Para o `pipeline-diario.yml`, esta página continua a ser HTML manual
protegido como qualquer outra. **Fase 5 — concluída (2026-07-12):**
`pagamento-apos-deferimento.html` ("Pedido deferido: quando cai o
primeiro pagamento"), página evergreen cross-cluster com tabela por
prestação (desemprego/doença/parental/abono/RSI/pensão/CSI) e
cross-links nos dois sentidos com o calendário — ver a entrada de
revisão no fim deste ficheiro.

**Cross-link PSU (2026-07-18)** — nota não-alarmista junto às 4 linhas da
tabela "Quando recebo a minha prestação?" cujo regime **não-contributivo**
está confirmado na lista dos 13 apoios (RSI, pensão social de velhice/
invalidez, subsídio social de desemprego, subsídios sociais de
parentalidade): "🔄 Vai ser integrado na PSU — o pagamento continua normal
até ao decreto-lei", com link à pillar `/prestacao-social-unica.html`.
CSI e PSI ficam deliberadamente de fora — o CSI está excluído da PSU
(confirmado em audição parlamentar) e a PSI ainda não tem a inclusão/
exclusão confirmada pelo decreto-lei. Implementado em `PSU_NOTAS`
(`scripts/atualizar_calendario.py`), aplicado dentro de
`_seccao_por_prestacao()` — sobrevive a qualquer regeneração mensal do
`calendario-mensal.yml`, nunca um add-on manual que a próxima corrida
apagaria (mesmo princípio da REGRA DE OURO: nada de manual dentro de uma
zona `CAL:CORPO:*`). Nova linha "Subsídios de parentalidade" acrescentada
a `VISTA_PRESTACOES` — a batch `desemprego_doenca_parentalidade_acao_social_*`
já pagava prestações de parentalidade mas não tinha linha própria na
tabela (só desemprego/doença); ganhou também o cross-link recíproco em
`subsidio-parental.html` (mesmo padrão "📅 Em que dia do mês é pago?" já
usado nas outras 7 páginas de prestações). 6.ª FAQ acrescentada (JSON-LD +
visível, paridade 1:1 confirmada) sobre mudança de IBAN, com link para
`/iban-seguranca-social.html` (nav path verificado contra esse guia:
Segurança Social Direta → Perfil → Conta Bancária — não inventado).
`dateModified`/"Verificado a" avançados para 18/07/2026.

---

## MEDIÇÃO DE CONVERSÃO — EVENTOS GA4

Instrumentação de conversão (2026-07-16, sessão de medição — sem qualquer
alteração de layout/conteúdo/Schema). Objectivo: ter baseline fiável de
conversão para, em meados de agosto, decidir a simplificação da homepage. Os
eventos foram acrescentados **nos JS já existentes de cada funcionalidade**,
nunca num ficheiro global novo — menos superfície nova, nenhum `eventos.js`
partilhado criado.

**Padrão obrigatório de qualquer evento novo**: guarda `typeof gtag ===
'function'` antes de chamar (o gtag.js carrega sempre com Consent Mode v2
avançado; em `denied` os eventos seguem como pings sem cookies — comportamento
correcto, nunca contornar). **Nenhum parâmetro transporta dados introduzidos
pelo utilizador** — só o facto de a acção ter terminado (mais, quando o
simulador o determina, um veredicto de elegibilidade, que é uma conclusão do
simulador, nunca um valor introduzido).

| Evento | Onde | Parâmetros | Notas |
|---|---|---|---|
| `simulacao_concluida` | inline nos 6 simuladores publicados (abono, ase, csi, subsidio_doenca, rsi, subsidio_desemprego), a par do `calc_resultado` já existente | `simulador` (slug), `elegivel` (só onde há veredicto binário) | `elegivel` presente em abono (`escalão ≠ 5`), ase (com/sem direito), csi (`temDireito`), subsidio_desemprego (prazo de garantia); **omitido** em subsidio_doenca e rsi — não têm veredicto binário limpo (rsi é multi-factor e auto-declara-se incompleto). `simulador-psu.html` fica de fora (noindex, não publicado). |
| `partilha_clique` | `assets/js/share.js`, nos dois pontos de sucesso (Web Share API e cópia para a área de transferência) | `pagina` (pathname) | Nunca no fallback da caixa manual (falha de cópia) nem em cancelamento (AbortError). Nunca envia o título. |
| `comecar_aqui_percurso` | `comecar-aqui.html` | evento de início (`etapa: 'inicio'`, primeira escolha) e evento final (`etapa: 'fim'`, `destino` = pathname recomendado) | Mede a taxa de conclusão do funil. `destino` é o apoio recomendado (primeiro card) ou `/#guias-de-apoios`, nunca as respostas do quiz. |
| `cal_home_clique` | `index.html`, clique na barra fixa `.cal-topo` (é um `<a>`, é clicável) | — | GA4 usa `sendBeacon` por omissão, por isso o evento sobrevive à navegação. |

**`documento_gerado` — deliberadamente NÃO implementado** (decisão do Nuno
nesta sessão): o gerador de documentos tem a invariante dura, documentada e
testada, de **zero pedidos de rede depois do load**
(`tests/test_gerador_documentos.py::test_zero_pedidos_de_rede_ao_interagir_com_o_gerador`),
que sustenta a promessa "os dados que preenches nunca saem do teu
dispositivo". Um evento GA4 é um pedido de rede (mesmo o ping sem cookies em
`denied`), por isso instrumentar o gerador quebraria essa garantia. Fica sem
medição por escolha consciente — a privacidade do gerador vale mais do que o
baseline deste evento. O comentário em `gerador-documentos.js` e o teste de
rede-zero mantêm-se intactos; `tests/test_eventos_ga4.py::test_gerador_documentos_nunca_dispara_gtag`
tranca essa decisão.

**Testes**: `tests/test_eventos_ga4.py` (asserções sobre o fonte, portáteis,
sem Playwright — guarda `typeof gtag`, slug/parâmetro certos, e um varrimento
global anti-dados-pessoais com denylist de tokens de input/DOM) +
`tests/test_share_js.py` (5 testes funcionais Chromium para `partilha_clique`:
dispara no clipboard e no Web Share, nunca em cancelamento nem no fallback
manual, e corre sem gtag definido).

### HEADERS HTTP — LIMITAÇÃO ACEITE

O GitHub Pages não permite headers HTTP personalizados (CSP, X-Frame-Options,
Permissions-Policy, etc.). Decisão registada: **ACEITAR** esta limitação — o
site é estático, sem autenticação e sem formulários que recolham dados
pessoais (o gerador de documentos corre 100% no browser, ver secção "GERADOR
DE DOCUMENTOS"). Alternativas avaliadas e **rejeitadas**: meta-CSP no `<head>`
(cobertura parcial — não substitui os headers reais, e arriscava partir o
gtag.js/consentimento) e Cloudflare à frente do Pages (introduz um serviço
externo, contra a regra "zero serviços externos novos"). **Reavaliar apenas
se o site passar a recolher dados** (login, formulários com dados pessoais no
servidor, pagamentos).

### PASSO MANUAL PARA O NUNO — key events no GA4

Os eventos disparam sozinhos, mas marcá-los como **key events** (conversões)
não é possível por código — é na interface do GA4 (Admin → Events → marcar
como key event). Marcar: `simulacao_concluida`, `comecar_aqui_percurso` (o
evento final, `etapa: 'fim'`) e — quando/se instrumentado — `documento_gerado`
(hoje não existe, ver acima). `partilha_clique` e `cal_home_clique` são úteis
como micro-conversões, opcional marcá-los.

---

## SCHEMA.ORG — GRAFO DO SITE (WebSite + CollectionPage)

Intervenção cirúrgica de 2026-07-16 (Sessão 2 — só JSON-LD ao nível do
site; o JSON-LD dos artigos, `FAQPage`/`HowTo`/`BreadcrumbList`/`Article`,
está correcto e **não foi tocado**). O défice era ao nível do grafo do
site, não dos artigos.

### WebSite único, na homepage

- O bloco `WebSite` vive **só** em `index.html`, com `@id`
  `https://tensdireito.com/#website`, `publisher` a referenciar a
  `Organization` da NV Labs por `@id`
  (`https://tensdireito.com/sobre.html#nvlabs`, definida em `sobre.html`).
- **`potentialAction` (`SearchAction`) — adicionado a 2026-07-16, removido
  a 2026-07-18.** Na altura, o `urlTemplate`
  (`https://tensdireito.com/?pesquisa={search_term_string}`) foi verificado
  contra um handler real (`index.html` lê `?pesquisa=` no
  `DOMContentLoaded`, injecta o termo no campo de pesquisa do hero via
  `pesquisa.js`) — nunca inventado. Removido depois de o GSC reportar
  `https://tensdireito.com/?pesquisa={search_term_string}` como "Rastreada
  — atualmente não indexada": a Google descontinuou a sitelinks search box
  em outubro de 2024, por isso o markup deixou de ter função e só gerava
  uma URL fantasma nos relatórios de cobertura. A funcionalidade de
  pesquisa em si (`?pesquisa=`, `pesquisa.js`) **não foi tocada** — só o
  `potentialAction` estruturado, dirigido ao Google, é que saiu; o
  `canonical` da homepage (`https://tensdireito.com/`, sem query params)
  já absorve qualquer variante `?pesquisa=...` que o Google tenha
  rastreado. Nenhum script gera este bloco (é escrito à mão em
  `index.html`, como sempre foi) — não havia origem a corrigir.
- **Decisão da Tarefa 1, ponto 3 — opção (a)** (2026-07-16): o `WebSite`
  que vivia em `sobre.html` (sem `@id`) foi **removido**; passa a haver um
  único `WebSite` no site, na homepage, com `@id`. Nunca dois `WebSite`
  com `@id` diferentes. `sobre.html` mantém `AboutPage` + `Organization`
  (a entidade NV Labs continua resolvível lá). `tests/test_sobre_jsonld.py`
  actualizado (validava 3 blocos em `sobre.html`; agora valida 2 lá + o
  `WebSite` com `@id`/`publisher` na `index.html`, sem `potentialAction`
  desde 2026-07-18).
- Cuidado de manutenção: o `pipeline-diario.yml` (Step 6, `sed`)
  actualiza o campo `"dateModified"` deste bloco `WebSite` em `index.html`
  — a linha foi preservada intacta, o `sed` continua a funcionar.

### CollectionPage + ItemList nas 6 pillar pages

- Gerado a partir de `data/clusters.json` (fonte única) por
  `render_pillar_jsonld()` em `scripts/sincronizar_clusters.py`, injectado
  no `<head>` de cada pillar entre `<!-- PILLAR-JSONLD:INICIO/FIM -->`.
  **Nunca escrito à mão** — divergiria do JSON na primeira sincronização.
  Idempotente (`json.dumps` estável; 2.ª corrida = zero alterações),
  `--dry-run` funciona.
- Estrutura: `CollectionPage` (`@id` `<pillar>#collection`, `url`,
  `name` = nome do cluster, `isPartOf` → `@id` do `WebSite` único) com
  `mainEntity` = `ItemList` cujos `itemListElement` são as páginas do
  cluster, `position` sequencial (1..N) e `url` absoluto — 1:1 com
  `clusters.json`, incluindo simuladores (`tipo: "ferramenta"`), tal como
  o `PILLAR-LISTA`. As 6 pillars: as 5 em `p/*.html` + `prestacao-social-unica.html`
  (pillar em raiz). Cada pillar fica com `Article` + `FAQPage` +
  `BreadcrumbList` + `CollectionPage` — sem duplicar tipos (não havia
  `WebPage`/`CollectionPage` antes).
- Testes: `tests/test_sincronizar_clusters.py` estendido — injecção,
  idempotência do novo bloco, 1:1 `ItemList`↔`clusters.json` (unidade em
  `tmp_path` **e** guarda sobre os 6 pillars reais), e pillar com
  `PILLAR-LISTA` mas sem `PILLAR-JSONLD` é reportada sem escrever (a
  presença dos dois marcadores passa a ser obrigatória numa pillar).
  `test_breadcrumb_coerencia.py` reconfirmado sem regressão.

### PASSO MANUAL PARA O NUNO — validar depois do deploy

Depois do deploy, validar no **Rich Results Test**
(search.google.com/test/rich-results) e/ou no **Search Console** (relatório
de dados estruturados): a homepage (`WebSite`, sem `SearchAction` desde
2026-07-18) e uma ou duas pillar pages (`CollectionPage` +
`ItemList`). Não é possível validar por código contra a Google — a
validação local é estrutural (JSON real, `@id` coerentes, `position`
sequencial, URLs absolutos).

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
| `manuais-escolares-mega.html` | **Datas de emissão 2026/2027 já publicadas (13/07/2026): 3 ago (1.º–4.º), 10 ago (5.º–9.º), 13 ago (10.º–12.º)** — próxima revisão jun. 2027 | Issue automática do scraper (`dge.mec.pt` **e** `igefe.mec.pt`, desde 2026-07-06) — ver nota abaixo |
| `acao-social-escolar.html` | Setembro — prazo de candidatura ("até 30 de setembro"), **nunca** escalões (ver nota abaixo) | Redundante com `calendario-escolar-apoios.html`, mantida por cautela |
| `bolsa-de-merito.html` | Setembro — valor do ano lectivo (2,5×IAS em vigor), **nunca** um despacho próprio (ver nota abaixo) | Calendário anual — texto da própria página desactualizado, ver nota |
| `abono-de-familia.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `rsi.html` | Janeiro (novo IAS/RSI) | Issue automática do scraper |
| `complemento-solidario-idosos.html` | Janeiro (novo valor CSI) | Issue automática do scraper |
| `prestacao-social-unica.html` | Ago 2026 (decreto-lei) + Jan 2027 (entrada vigor) | Verificação manual/news dre.pt |
| `psu-quando-entra-em-vigor.html` | Ago 2026 (decreto-lei) + Jan 2027 (entrada vigor) | Verificação manual/news dre.pt |
| `psu-quem-tem-direito.html` | Ago 2026 (valores confirmados pelo decreto-lei) | Decreto-lei publicado |
| `subsidio-desemprego.html` | Janeiro (novos limites) | Issue automática do scraper |
| `subsidio-parental.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `amim.html` | Janeiro (novo IAS: afeta IRS 4×/2,5×IAS e valor PSI) | Issue automática do scraper |
| `prestacao-social-para-a-inclusao.html` | Janeiro/Fevereiro (nova portaria de actualização da PSI) | Verificação manual/news dre.pt |
| `prova-escolar.html` | Junho (ano letivo seguinte) | Calendário anual — ver nota abaixo |
| `bolsa-de-estudo-ensino-superior.html` | Verão (Despacho anual de prazos, ex.: Despacho n.º 7994/2026 para 2026/2027 — a data muda de ano para ano) | Verificação manual/news dges.gov.pt |
| `calendario-escolar-apoios.html` | Junho/Julho (antes do início do próximo ciclo de prazos) — `verificar_datas.py` confirmado a **não** disparar em jul. 2026 (mês de publicação) mas a disparar em 2027 nos meses 1/7/8/9 (padrão `data_mes_ano`, "setembro de 2026" na FAQ do início das aulas) — comportamento desejado, mesma lógica de `prova-escolar.html` | Calendário anual — agrega prazos de 6 páginas do cluster, revisão obrigatória sempre que qualquer um desses prazos mudar |
| `renovar-cartao-cidadao.html` | Nota de verificação para **3 de agosto de 2031** — prazo-limite real remanescente (cartões com MRZ mas sem chip de contacto, emitidos até 10/06/2024; Regulamento (UE) 2025/1208). Corrigido a 2026-07-18: o prazo de 3/08/2026 **não** se aplica ao Cartão de Cidadão normal (tem MRZ desde 2007) — só afecta duas excepções raras (CC do Tratado de Porto Seguro, BI vitalício), conforme esclarecimento oficial do IRN de 30/12/2025. `verificar_datas.py` continua a disparar em 2027 nos meses 1/7/8/9 (o texto ainda cita "2026") — sem acção obrigatória nessa altura, só confirmar que a secção "Preciso de renovar antes do prazo?" continua correcta | Sem gatilho de acção — nota de contexto, a rever se saírem novos esclarecimentos oficiais do IRN antes de 2031 |

**`manuais-escolares-mega.html` — nota de manutenção sazonal (2026-07-06,
actualizada 2026-07-06)**: a lacuna de vigilância identificada na sessão
anterior (o scraper só vigiava `dge.mec.pt`, entidade que não gere de
facto a plataforma MEGA) **está fechada** — nova fonte `igefe_mega`
(`scripts/scraper_playwright.py`, `metodo="http"`) vigia directamente
`https://www.igefe.mec.pt/Page/Index/199`, a página real onde a IGeFE,
I.P. (a entidade que emite os vouchers aos encarregados de educação)
publica a secção "Emissão de Vouchers". Confirmado num runner real
(2026-07-06) que o conteúdo útil desta página não vive em `<p>` — está
num `<div class="ig-publicsite-paragraph">` — por isso os selectores são
específicos a esta fonte (`paragrafos: ".ig-publicsite-paragraph"`, não
o `"p"` genérico usado nas outras fontes); `min_chars_uteis=300` e
`ancora_conteudo=("voucher",)` calibrados com o conteúdo real (~1000
chars úteis, "voucher" nunca aparece na navegação/rodapé, só no
parágrafo de conteúdo). `mega_datas` (`dge.mec.pt`) e `igefe_mega`
partilham a mesma lógica rica de detecção e a mesma chave de aviso
(`mega_2026_2027_publicadas`, via `MEGA_SLUGS_DATAS_RICAS` e
`_detectar_datas_mega()`) — a Issue automática
"📅 MEGA 2026/2027 — datas de emissão detectadas" dispara sempre que
**qualquer uma** das duas detectar o padrão, independentemente de qual
publicar primeiro. Testado com fixtures reais (conteúdo actual de
2025/2026 classifica OK; conteúdo simulado com "2026/2027" + data de
julho/agosto dispara o aviso; conteúdo vazio nunca classifica OK — as
3 pontas do invariante "nenhum estado de erro pode parecer sucesso").

**O que continua manual**: o scraper só *alerta* — nunca escreve HTML
de artigos (ver "REGRA DE OURO — FICHEIROS AUTO-GERADOS vs MANUAIS", só
`index.html`/`noticias.html`/`CLAUDE.md`/`README.md`/`data/*.json` podem
ser escritos pelo pipeline). Uma Issue `mega_2026_2027_publicadas`
continua a exigir uma sessão manual para confirmar as datas exactas e
editar `manuais-escolares-mega.html` — o que mudou é só a rapidez e a
cobertura da detecção (2 fontes independentes em vez de 1), não quem
faz a edição. **Verificação manual semanal por `WebSearch` deixa de ser
necessária** como rede de segurança principal — mantém-se só como
reforço oportunista se alguém estiver a rever a página por outro
motivo, já que nenhuma automação garante 100% de cobertura (ex.: um
anúncio que apareça primeiro num canal que nenhuma das duas fontes
vigia, como redes sociais ou imprensa).

EduQA (`eduqa.pt`) **não foi adicionada como fonte** — confirmado que o
calendário que gere (registo SIME-MEGA, requisição de manuais em
braille/digital, Despacho n.º 3026/2024) é o processo de **adopção de
manuais pelas escolas**, distinto do processo de **emissão de vouchers
aos encarregados de educação** que esta página documenta; scraper essa
fonte não ajudaria a detectar o sinal que importa aqui.

**`acao-social-escolar.html`/`bolsa-de-merito.html` — nota de manutenção
sazonal, correcção de premissa (2026-08-25)**: sessão "Sentinela para o
despacho da ASE" investigou onde é publicado o "despacho anual da
DGEstE com os escalões ASE" que a migração do ASE para YAML dava como
bloqueio (ver `ROADMAP.md` → "TRABALHO FUTURO REGISTADO") — **não
existe nenhum acto desse tipo**. `WebFetch` continua bloqueado nesta
sessão para qualquer domínio `.gov.pt`/`.mec.pt`/`diariodarepublica.pt`
(confirmado de novo: `EGRESS_BLOCKED` mesmo para domínios fora do
Estado, ex. `google.com` — mesma limitação documentada em várias
sessões anteriores), por isso a investigação foi feita inteiramente por
triangulação `WebSearch` (várias pesquisas independentes, nunca uma
fonte só), sem acesso directo ao texto de nenhum diploma.

O regime substantivo da ASE — escalões A/B como % do IAS, tectos de
material escolar (16€/8€) e visitas de estudo (20€/10€) em euros,
desconto nas refeições (gratuita no A, 50% no B) — está fixado desde
2015 pelos Despachos n.º 8452-A/2015, 5296/2017 e 7255/2018, **sem
nenhuma república anual**: os valores de 2025/2026 encontrados via
`WebSearch` (16€/8€ material, 20€/10€ visitas) são idênticos aos já
citados no site desde a publicação original — nenhuma fonte encontrada
menciona um despacho novo a alterá-los. A única variável real é o
IAS, publicado por Portaria própria (tipicamente dezembro/janeiro) —
**já vigiado pelo sentinela `dre_ias`** (Issue automática de janeiro,
ver "PÁGINAS COM DATAS SAZONAIS" acima). O mesmo se aplica à Bolsa de
Mérito: o valor é sempre 2,5×IAS, calculado a partir do mesmo Despacho
n.º 8452-A/2015 — **nunca** um despacho anual próprio. O texto de
`bolsa-de-merito.html` ("o valor de 2026/2027 aguarda publicação do
despacho anual") herda a mesma premissa errada — o valor 2026/2027
(1.342,83 € = 2,5 × IAS 2026, já confirmado desde janeiro) é calculável
hoje, sem esperar por nada; **página não corrigida nesta sessão**
(fora do âmbito — só documentação), registado para uma sessão dedicada.

O prazo de "30 de setembro" em `acao-social-escolar.html` é uma regra
fixa do regime-base (não republicada ano a ano); a única coisa que o
podia genuinamente deslocar é um despacho de calendário escolar/
matrículas novo — já agregado por `calendario-escolar-apoios.html`
(ver a entrada dessa página nesta tabela). A revisão de setembro deste
artigo fica por isso redundante com essa página, mantida por cautela.

Único acto do Ministério da Educação com cadência quase-anual
encontrado nesta investigação e relacionado com a ASE — mas **não
adoptado como sentinela**: o preço-tecto da refeição escolar (indexado
ao IPC desde o ano lectivo 2024/2025, 1,46 € desde então, sem alteração
confirmada para 2026/2027). Decisão consciente de não vigiar: o site
expressa sempre o custo da refeição como desconto percentual (gratuita/
50%), nunca o valor em euros, por isso este acto nunca afecta um valor
publicado — ver `ROADMAP.md` → "À ESPERA DE UM SINAL" → "Manuais".

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

Estado: aprovada parlamento 25/06/2026. Autorização legislativa promulgada
pelo Presidente da República a 17/07/2026 (válida por 120 dias) e **publicada
em Diário da República a 27/07/2026 como Lei n.º 36/2026** (referendada pelo
Primeiro-Ministro a 20/07/2026) — dá ao Governo o poder de aprovar o
decreto-lei em Conselho de Ministros. Mudança relevante face ao plano inicial
do Executivo: os valores e as condições de acesso terão de ser fixados
directamente pelo decreto-lei, e não por portaria como o Governo previa a
princípio — mais escrutínio, com promulgação obrigatória do PR e possível
apreciação parlamentar do próprio decreto-lei.

O texto integral da Lei n.º 36/2026 (artigos 1.º a 3.º) confirma, ao
pormenor, o que o site já documentava e acrescenta factos novos — ver
entrada de revisão de 28/07/2026 no fim deste ficheiro para o detalhe
completo. Resumo: a lista dos 13 apoios (artigo 1.º/2) bate certo com a
soma das 8 alíneas legais (a alínea dos subsídios de parentalidade
desdobra-se em 6 apoios distintos); o mecanismo de dispensa das actividades
de solidariedade social para incapacidade ≥80% (com avaliação individual
entre 60%-79%) está agora confirmado por lei, não só por proposta do
Governo; despedimento por facto imputável ao trabalhador não impede acesso
à PSU (sem prejuízo de condições específicas por componente); as
ponderações de "adultos equivalentes" têm de ser diferenciadas entre
adultos 18+ e crianças/jovens (valores exactos ainda por fixar pelo
decreto-lei — nunca assumir que são iguais); "apoios à habitação com
caráter de regularidade" entram nos rendimentos considerados; e a lei
prevê revisão do CSI em 90 dias para não deixar ninguém excluído com a
extinção da pensão social de velhice.

**FECHADO — decreto-lei publicado (2026-08-13).** O Decreto-Lei n.º
166/2026, de 13 de agosto (Diário da República n.º 156/2026, Série I),
foi publicado e está **em vigor desde 14 de agosto de 2026** — dentro do
prazo PRR (31 ago 2026) e da janela de 120 dias da autorização
legislativa (Lei n.º 36/2026). **Produção de efeitos para
beneficiários: 31 de dezembro de 2026 (artigo 63.º)** — corrige o "1 de
janeiro de 2027" que este ficheiro citava como "texto inicial, não
confirmado" antes do decreto-lei sair; o valor real e definitivo é
31/12/2026, nunca 1/1/2027. Todos os valores, ponderações e a fórmula de
cálculo estão fixados directamente no diploma — ver
`dados/parametros/psu.yaml` para os valores e a secção "Plano de acção"
mais abaixo para o detalhe completo da activação (Fase 2, Commits 1-4,
concluída a 2026-08-16).

Cluster publicado: 1 jul 2026 (pillar + 4 páginas filhas); + `psu-trabalho-social.html` a 3 jul 2026
(5.ª página filha — ver "PÁGINAS PUBLICADAS"). As 6 páginas do cluster
(pillar + 5 filhas) foram actualizadas a 18/07/2026 com a milestone da
promulgação, a 28/07/2026 com a publicação da Lei n.º 36/2026 em DR, e a
2026-08-13/16 com os valores reais do decreto-lei (Fase 2) — ver
entradas de revisão no fim deste ficheiro. **Mais 3 páginas novas
publicadas na Fase 2**: `como-pedir-psu.html` e
`calendario-pagamentos-psu.html` (Commit 2/5), e `simulador-psu.html`
activado — `index,follow`, fórmula real, banner de vigência ligado a
`data_producao_efeitos` (Commit 3/5) — cluster com 8 páginas no total
(pillar + 7 filhas, incluindo o simulador).

**Sentinela automático (`dre_psu`) — CORRIGIDO DE VEZ a 2026-07-07
(Issue #54), com o mecanismo confirmado num runner com browser
interactivo real** — o trabalho que estava registado como pendente
desde a auditoria de 2026-07-05. O que o diagnóstico provou (runs
28860869507/28861231682, workflow temporário apagado no fim):
- A hipótese da auditoria estava certa: a pesquisa do
  diariodarepublica.pt é uma SPA OutSystems que guarda o termo num
  **cookie de sessão** — nenhum parâmetro de URL (`?q=`, `?termo=`,
  caminho antigo/novo) filtra em navegação directa; devolve sempre o
  índice inteiro (2,2M resultados) com HTTP 200, o falso sucesso
  perfeito. A URL antiga (`dre.pt/pesquisa?q=...`) devolve soft-404.
- A pesquisa **interactiva** (escrever na caixa `input[type='search']`
  da home + Enter) funciona; e **com aspas** força frase exacta no
  Elasticsearch por trás: `"prestação social única"` → 2 resultados
  (vs 12.651 sem aspas) — hoje uma Lei (73-B/2025, Grandes Opções) e
  um Despacho. O dia em que um **Decreto-Lei** entrar nesta lista é o
  sinal exacto do sentinela.

Implementação (`scraper_playwright.py`): nova opção
`pesquisa_interactiva` por fonte + `_obter_html_pesquisa()` (home →
preencher caixa → Enter → esperar pelo **eco do termo com aspas** na
página de resultados via `wait_for_function`); a âncora
(`ancora_conteudo=('"prestação social única"',)`) é a prova de que o
filtro foi aplicado — o índice inteiro não tem esse eco e classifica
`MUDOU`, nunca `OK` (testado). Selectores calibrados ao markup real
OutSystems (`a[href*='/dr/detalhe/']` = um título de acto por
resultado; `span[data-expression]` = títulos/designações — nunca
`<p>`). Detecção do decreto (`_detectar_decreto_psu()`) passou a ser
**por item** — dispara quando o título de um resultado é um
Decreto-Lei — corrigindo um falso positivo latente da versão antiga
(regex `decreto.lei.*presta` sobre o texto todo concatenado, que
dispararia com um decreto-lei num resultado e "prestação" noutro sem
relação; nunca se manifestou só porque a fonte nunca extraiu
conteúdo). Perfil de browser fixado ao provado no diagnóstico
(`PerfilBrowser(stealth=False, headers_custom=False)` — mesma lição do
seg-social: nunca acrescentar componentes de contexto não provados
contra o backend real). Testes: `tests/test_dre_psu_pesquisa.py`
(9 casos, fixtures do texto real do diagnóstico — índice inteiro nunca
OK, eco sem aspas nunca OK, resultados actuais reais nunca disparam,
decreto dispara, falso positivo antigo não dispara).

**Sentinela FECHADO/RECONFIGURADO — 2026-08-16 (Fase 2, Commit 5/5)**: o
sinal que `dre_psu` vigiava (publicação do decreto-lei) já cumpriu a
função — o Decreto-Lei n.º 166/2026 está publicado. Decisão tomada:
**nem desactivar por completo, nem deixar tal e qual** — as duas coisas
seriam erradas por motivos diferentes.

- **Porque não deixar tal e qual**: `_detectar_decreto_psu()` nunca teve
  corte de recência (`data_minima`) — não fazia falta enquanto a PSU não
  tinha decreto-lei nenhum. Agora que tem, a pesquisa por `'"prestação
  social única"'` encontra sempre o próprio DL n.º 166/2026 nos
  resultados — sem correcção, isto dispararia a Issue "decreto-lei PSU
  detectado" **todos os dias, para sempre** (mesma classe de falso
  positivo já visto no PAER, Issue #73, só que desta vez sobre o
  próprio alvo já conhecido do sentinela, não um alvo antigo alheio).
- **Porque não desactivar por completo**: `dre_psu` continua útil como
  rede de segurança geral — um decreto-lei FUTURO que também mencione
  "prestação social única" (ex.: uma alteração ao regime já criado)
  ainda deve disparar. E há dois pontos reais e concretos que o
  Decreto-Lei n.º 166/2026 deixa por regulamentar (confirmados
  directamente pelo Nuno na leitura do texto real — dre.pt continua
  bloqueado nesta sessão, mesma limitação de sempre): o **artigo 17.º**
  (fórmula de apoios à habitação com carácter de regularidade,
  dependente de uma estatística do INE actualizada por portaria — já
  documentado como "único ponto ainda sem valor concreto" em
  `psu-quando-entra-em-vigor.html`/`simulador-psu.html`) e os
  **artigos 32.º/59.º** (procedimentos e meios de prova da candidatura).

**Correcção aplicada**: `_detectar_decreto_psu()` ganhou
`data_minima="2026-08-16"`, hardcoded dentro da função — **nunca** no
dict de `FONTES_PLAYWRIGHT` (que `tests/test_dre_habitacao_watchlist.py::test_dre_psu_continua_a_usar_o_mecanismo_antigo_intocado`
tranca à forma exacta de antes: `"detectar_decreto_lei" not in fonte`).
O próprio DL n.º 166/2026 (datado 13/08/2026, antes do corte) deixa de
disparar; um decreto-lei futuro datado depois do corte continua a
disparar normalmente. `dre_psu` mantém-se em `SLUGS_MONITORIZADOS`,
`FONTES_PLAYWRIGHT` e no bloco de Issue de `pipeline-diario.yml`, 100%
inalterados na forma.

**Sentinela irmão novo — `dre_psu_regulamentacao`**: mesmo mecanismo de
pesquisa de frase exacta, mas a pesquisar pelo **número** do
decreto-lei (`'"Decreto-Lei n.º 166/2026"'`, mesmo padrão robusto de
`dre_habitacao_garantia` — qualquer Portaria que o regulamente tem de o
citar na ementa) em vez de uma frase descritiva, e a filtrar só
resultados do tipo **Portaria** (`detectar_portaria`, mesmo mecanismo do
`dre_ias`) — nunca Decreto-Lei, que já não interessa a este sentinela
(é trabalho do `dre_psu`). Corte de recência `"desde": "2026-08-16"`
acrescentado por hábito defensivo consistente (tecnicamente redundante
— o DL 166/2026 é demasiado novo para ter Portarias antigas a citá-lo).
Cobre os dois pontos em aberto (art. 17.º; arts. 32.º/59.º) com um único
sentinela — quando disparar, a Issue automática pede para confirmar qual
dos dois é. Nunca calibrado contra um runner real nesta sessão
(WebFetch/curl bloqueados) — a 1.ª corrida real do pipeline confirma
`min_chars_uteis`, mesmo padrão honesto já usado para
`dre_habitacao_paer`/`dre_habitacao_garantia`/`dre_ias`.

Testes: `tests/test_dre_psu_regulamentacao.py` (15 casos) — confirma que
`dre_psu` mantém config/perfil/forma 100% inalterados, que o próprio DL
166/2026 já não dispara `dre_psu` (regressão do achado real desta
sessão), que um decreto-lei futuro sobre a PSU ainda dispara `dre_psu`,
e cobre `dre_psu_regulamentacao` (config, presença em
`FONTES_PLAYWRIGHT`, corte de recência, detecção por item — Portaria
dispara, Decreto-Lei nunca dispara este sentinela específico, conteúdo
vazio nunca dispara).

### Páginas NÃO afectadas pela PSU

Estas páginas mantêm-se inalteradas — os subsistemas/apoios são explicitamente excluídos do âmbito da PSU:

- `abono-de-familia.html` — subsistema familiar (excluído)
- `acao-social-escolar.html` — educação (excluído)
- `bolsa-de-merito.html` — educação (excluído)
- `manuais-escolares-mega.html` — educação (excluído)
- `passe-sub23.html` — transporte (excluído)
- `complemento-solidario-idosos.html` — CSI explicitamente excluído (confirmado audição parlamentar)
- `prestacao-social-para-a-inclusao.html` — PSI não consta da lista dos 13 apoios (exclusão por omissão, não explícita como o CSI — ver "PENDÊNCIA PSI vs PSU — FECHADA" abaixo)
- `simulador-abono.html` — ferramenta abono (excluído)
- `simulador-ase.html` — ferramenta ASE (excluído)

### PENDÊNCIA PSI vs PSU — FECHADA (2026-07-18)

A secção "PSI e a Prestação Social Única" de `prestacao-social-para-a-inclusao.html`
tratava a exclusão da PSI como **provisória**, à espera do decreto-lei
(ver o antigo item 9 do "Plano de acção" abaixo, e a entrada de revisão de
2026-07-04 mais abaixo neste ficheiro). Facto novo, verificado pelo Nuno a
18/07/2026 (lista oficial via ECO + proposta do Governo + Guia Prático do
ISS da PSI): **a PSI não está entre as 13 prestações da PSU — e não é uma
questão em aberto**. O perímetro da PSU foi fixado pela autorização
legislativa promulgada a 17/07/2026 (ver "Estado" mais abaixo); o
decreto-lei regulamenta os 13 apoios já listados, não pode alargar essa
lista. Não é preciso esperar pelo decreto-lei para esta conclusão.

**Diferença de força probatória, nunca escrever como sinónimos**: o CSI
foi **explicitamente excluído** (confirmado pela Secretária de Estado em
audição parlamentar); a PSI fica de fora **por omissão** — simplesmente
não consta da lista oficial. Nunca escrever "a PSI foi excluída" — é
"a PSI não consta da lista".

**Nuance crítica, fonte real de confusão em sites de finanças pessoais**:
a lista dos 13 apoios inclui a "pensão social de invalidez especial"
(prestação #2, ver `psu-lista-13-apoios.html`) — prestação **distinta**
da PSI. A PSI (Decreto-Lei n.º 126-A/2017) substituiu essa pensão social
de invalidez para novos requerentes desde 2017, mas é hoje um regime
autónomo, com o seu próprio diploma. As duas nunca são a mesma coisa.

**Alterações aplicadas nesta sessão**: `prestacao-social-para-a-inclusao.html`
(§7 reescrita com a certeza nova + a distinção de força probatória +
aviso de desambiguação da pensão social de invalidez; FAQ "A PSI vai ser
integrada na Prestação Social Única?" reescrita — a pergunta já existia
com fraseado ligeiramente diferente, "vai ser absorvida", actualizada em
vez de duplicada; corrigido de caminho um gap pré-existente e sem relação
com esta sessão: a FAQ visível "A PSI conta como rendimento para o IRS?"
não tinha par no `FAQPage` JSON-LD desde a publicação — descoberto ao
verificar programaticamente a paridade 1:1, corrigido acrescentando-a;
checklist final ajustada — já não sugere "acompanhar o decreto-lei", a
questão está fechada); `psu-lista-13-apoios.html` (novo `.aviso-info`
logo a seguir à lista dos 13 apoios, com a mesma desambiguação);
`prestacao-social-unica.html` (secção "O que NÃO integra a PSU" ganhou um
3.º parágrafo sobre a PSI, ao lado do CSI, com a mesma distinção de força
probatória); `scripts/atualizar_calendario.py` (comentário junto a
`PSU_NOTAS` reescrito para fechar a pendência de vez — "psi" nunca deve
ganhar entrada nesse dicionário, com o raciocínio completo, para nenhuma
sessão futura reabrir a dúvida por engano). `dateModified`/"Verificado a"
avançados para 18/07/2026 nas 3 páginas HTML tocadas.

### Páginas com aviso PSU activo

Avisos de transição activos até **31 de dezembro de 2026** (produção de
efeitos, artigo 63.º do DL 166/2026) — reescritos na Fase 2 (Commit 4/5,
2026-08-16) com o facto real (conversão oficiosa, artigo 57.º), a
substituir o texto pré-decreto ("aprovada... aguarda decreto-lei"):

| Página | Absorção | Aviso |
|---|---|---|
| `rsi.html` | Absorvido integralmente | DL 166/2026 em vigor, conversão oficiosa (art. 57.º) a partir de 31/12/2026 |
| `subsidio-desemprego.html` | Só subsídio SOCIAL absorvido | Idem; CONTRIBUTIVO não afectado |
| `subsidio-parental.html` | Só apoios NÃO contributivos absorvidos | Idem; contributivo mantém-se |

### Cluster PSU — activado (Fase 2, 2026-08-16)

**As duas páginas antes "em espera" já estão publicadas** (Commit 2/5):
`como-pedir-psu.html` e `calendario-pagamentos-psu.html`.

**`simulador-psu.html` activado** (Commit 3/5, 2026-08-16): `robots`
passou de `noindex,nofollow` para `index,follow`, `ESTADO_SIMULADOR`
passou de `'AGUARDA_DECRETO'` para dinâmico (fetch de
`dados/parametros.json` em runtime, mesmo padrão dos outros
simuladores), fórmula real implementada e testada
(`tests/test_simulador_psu_calculo.py`, 18 golden tests), banner de
vigência ligado a `data_producao_efeitos` do YAML (nunca uma string
solta) — mostra "simulação informativa, pagamento só a partir de
31/12/2026" enquanto essa data não chegar. Artigo 17.º (apoios à
habitação com carácter de regularidade) explicitamente **não
implementado** neste Commit 3/5 — campo marcado "não considerado nesta
versão", nunca inventado um valor sem a Portaria de regulamentação (ver
sentinela `dre_psu_regulamentacao` acima). **Estrutura (gated)
implementada numa sessão de auditoria seguinte, ainda no mesmo dia
(2026-08-16) — ver subsecção "Artigo 17.º — estrutura pronta, cálculo
desactivado" logo abaixo.**

### Artigo 17.º — estrutura pronta, cálculo desactivado (2026-08-16)

Sessão de auditoria seguida de implementação, no mesmo dia da activação
do cluster PSU (Fase 2, acima) — objectivo: preparar a ESTRUTURA do
artigo 17.º (apoios à habitação como rendimento) no simulador, **sem**
o valor da mediana do INE e **sem** activar o cálculo. Princípio de
segurança (o mesmo padrão já usado para os `null` das majorações da
Fase 1/2): o campo de habitação só pode ficar funcional quando existir
em `dados/parametros/psu.yaml` um valor de mediana €/m² **E** uma
referência à portaria que o legitima. Enquanto qualquer um faltar, o
campo mostra-se **desactivado** com explicação, e `calcularPSU()`
**nunca** soma habitação — trancado em duas camadas independentes:
um teste-âncora (`tests/test_valores_ancora.py::
test_art17_habitacao_pendente_ate_portaria`) e um gate na própria
função pura do JS (`calcularHabitacao()`), nunca confiado só ao
atributo `disabled` do HTML.

**Fórmula confirmada contra o texto real do artigo 17.º** (extraído de
`dados/fontes/Decreto-Lei n.PDF`, n.º 2-3): renda de referência = ⅓ ×
mediana €/m² de novos contratos (últimos 12 meses, ref. 3.º trimestre
do ano anterior, INE) × 112,50 m²; imputado = 0,5 × max(0, renda de
referência − renda paga). O teto de 450×IAS do artigo 14.º/3
**não** se aplica aqui — é específico dos rendimentos prediais (valor
patrimonial do imóvel de habitação própria e permanente), uma categoria
de rendimento inteiramente distinta.

**Âmbito do n.º 2 — deliberadamente por esclarecer**: o n.º 1 define
"apoios à habitação" de forma ampla ("habitação social e todos os
apoios à habitação, com caráter de regularidade... independentemente
da natureza jurídica da entidade que os atribui"), mas a fórmula dos
50% do n.º 2 refere-se literalmente só a "apoios imputados à habitação
social, incluindo os que decorrem de programas de arrendamento
subsidiado" — não fica claro se se generaliza a qualquer apoio do n.º 1
ou é específica desse subconjunto. Registado em comentário no próprio
`dados/parametros/psu.yaml`, para a portaria (ou uma leitura jurídica
mais aprofundada) resolver antes de qualquer activação.

**`dados/parametros/psu.yaml`** ganhou o bloco `art17_*` (prefixo — o
consolidador não suporta agrupamento nativo, mesmo padrão já usado para
`abono.yaml`/`cit_*`): `art17_area_referencia_m2` (112,50), `art17_
coeficiente_imputacao` (0,5) e `art17_divisor_renda_referencia` (3) —
todos fixos na lei, com valor desde já; `art17_mediana_renda_m2_ine`,
`art17_mediana_renda_m2_referencia` e `art17_portaria_habitacao` —
todos `null`, deliberadamente pendentes.

**`simulador-psu.html`**: `carregarParametrosPSU()` constrói
`PARAMETROS_PSU.art17Habitacao = { pronto, medianaRendaM2,
medianaReferencia, portaria, areaReferencia, coeficienteImputacao,
divisorRendaReferencia }` — `pronto` só é `true` quando
`art17_mediana_renda_m2_ine` **e** `art17_portaria_habitacao` tiverem
ambos valor não-null. `calcularHabitacao(parametros, recebeApoio,
rendaPaga)` devolve sempre 0 enquanto `!pronto`, independentemente do
input — soma directamente ao rendimento considerado em `calcularPSU()`,
**nunca** passa pela CIT (exclusiva de rendimentos de trabalho, artigo
28.º). Novo campo no formulário — checkbox "Recebo apoio à habitação
social ou arrendamento subsidiado (artigo 17.º)" + campo condicional de
renda paga — nasce sempre com o atributo `disabled` próprio (não herdado
do `fieldsetPSU` geral: `aplicarEstadoHabitacao()` gere-o à parte, dupla
garantia com o gate da função pura), com um `aviso-info` persistente
("Ainda não disponível — aguarda portaria de regulamentação"),
explicando também que, quando activo, marcar o apoio **aumenta** o
rendimento considerado e por isso **reduz** o valor da PSU — para não
parecer um bug quando a portaria sair.

**Testes**: `tests/test_valores_ancora.py` ganhou 2 testes (o canário
que tranca os 3 `null` em conjunto — confirmado a falhar de propósito
com um valor injectado isoladamente — e a confirmação dos 3 valores
fixos). `tests/test_simulador_psu_calculo.py` ganhou 6 golden tests
(gate fechado nunca soma habitação mesmo com input explícito; fail-safe
sem a chave `art17Habitacao` no objecto; fórmula correcta com uma
mediana **fictícia** — só no ficheiro de teste, nunca em produção;
gate aberto mas checkbox desmarcado não soma; renda paga acima da
referência nunca fica negativa) mais 2 testes de runtime real
(`http.server`, página completa, fetch real de `/dados/parametros.json`):
o checkbox nasce `disabled` e o aviso fica visível; um bypass
deliberado do `disabled` via DevTools simulado nunca produz um valor de
habitação > 0 no resultado renderizado — confirma, contra a página real,
que produção continua sem mostrar nenhum valor de habitação.

**Passos para activar, quando `dre_psu_regulamentacao` disparar para o
artigo 17.º** (ver sentinela na secção acima): 1) confirmar em dre.pt
qual dos dois pontos a portaria regulamenta (art. 17.º ou arts.
32.º/59.º); 2) se for o art. 17.º, esclarecer primeiro o âmbito do n.º 2
(ver acima); 3) preencher os 3 `null` em `dados/parametros/psu.yaml`
(mediana + trimestre de referência + portaria, os 3 em conjunto, nunca
isoladamente) com `referencia_legal`/`fonte_url`/`verificado_em` reais;
4) regenerar `dados/parametros.json`
(`python scripts/gerar_parametros_json.py`); 5) `test_art17_habitacao_
pendente_ate_portaria` passa a ficar vermelho sozinho — reescrever para
validar o valor real (nunca apenas apagar); 6) confirmar que o
formulário activa o checkbox e o campo de renda paga em produção. Nunca
tocar nas páginas de conteúdo do cluster (`psu-quando-entra-em-vigor.html`
já explica a fórmula sem número) até este ponto — ficam como estão até
à portaria.

### Plano de acção — CONCLUÍDO (Fase 2, Commits 1-4, 2026-08-16)

Registo histórico do plano original, com o estado real de cada item:

1. ✅ **Feito (Commit 1/5)** — `prestacao-social-unica.html` actualizada
   com valores reais do decreto-lei.
2. ✅ **Feito (Commit 1/5)** — `psu-quando-entra-em-vigor.html`,
   `psu-quem-tem-direito.html` e `psu-trabalho-social.html` actualizadas
   com valores/factos confirmados (trabalho social: "obrigatório, com
   excepções").
3. ✅ **Feito (Commits 2/5 + 3/5)** — `como-pedir-psu.html` e
   `calendario-pagamentos-psu.html` criadas; `simulador-psu.html`
   publicado.
4. ❌ **Nunca feito, e correctamente assim** — "transformar `rsi.html`
   em página de transição RSI→PSU com redirecionamento interno" era uma
   suposição do plano original, escrita antes de se conhecer o texto
   real do decreto-lei. O regime transitório real (artigo 57.º) mantém o
   RSI a funcionar exactamente como hoje até 31/12/2026, com conversão
   oficiosa só depois — não há nada para redireccionar antes disso, e
   mesmo depois o conteúdo de `rsi.html` continua útil para quem procura
   entender o que aconteceu. `rsi.html` manteve-se como guia normal do
   RSI, só com o aviso de transição actualizado (item 5).
5. ✅ **Feito (Commit 4/5)** — avisos em `subsidio-desemprego.html` e
   `subsidio-parental.html` actualizados com o facto real (mesmo commit
   que actualizou `rsi.html`).
6. ✅ **Confirmado, continua a valer** — nenhuma página antiga foi
   apagada.
7. **Ainda pendente, sem prazo** — reduzir a densidade da PSU na
   homepage "quando o tema arrefecer" — julgamento do Nuno, registado em
   `ROADMAP.md` → "À espera de um sinal" → "Manuais".
8. ✅ **Feito (Commit 4/5)** — `descricao_curta` do cluster
   `prestacao-social-unica` actualizada em `data/clusters.json`
   ("Decreto-Lei n.º 166/2026 em vigor — pagamento a partir de
   31/12/2026"), `scripts/sincronizar_clusters.py` corrido.
9. ✅ **Já estava fechado antes do decreto-lei** (2026-07-18, ver
   "PENDÊNCIA PSI vs PSU — FECHADA" acima) — confirmado, sem alteração
   necessária: a PSI continua fora da lista dos 13 apoios, o decreto-lei
   nunca poderia ter alargado esse perímetro.

---

## GATILHO AUTOBAIXA

Registado a 2026-07-05 — mesmo padrão do "Cluster PSU — páginas em
espera": um gatilho documentado para uma página futura, **não criada
nesta sessão nem antes de disparar**.

**Página em espera**: `autobaixa.html` — landing dedicada às queries
"autobaixa" / "autodeclaração de doença", hoje cobertas apenas pela
secção 8 de `baixa-medica-subsidio-doenca.html`.

**Condição de disparo**: o Nuno confirma no Google Search Console que
`baixa-medica-subsidio-doenca.html` acumula impressões relevantes para
essas queries — decisão manual dele, não automatizável (o Code não tem
acesso ao GSC). Nenhum limiar numérico fixado; é julgamento do Nuno
sobre quando o volume justifica uma página dedicada.

**Ação quando disparar**:
1. Criar `autobaixa.html`, reaproveitando e aprofundando a secção 8
   ("Autodeclaração de doença — guia completo") do artigo pilar.
2. O artigo pilar mantém uma versão resumida dessa secção, com um link
   "→ guia completo sobre autodeclaração de doença" para a landing —
   nunca apagar o conteúdo todo do pilar, só encurtar.
3. **Evitar canibalização de SEO**: `title`/H1 da landing centrados em
   "autodeclaração de doença (autobaixa)"; o pilar mantém-se centrado em
   "baixa médica e subsídio de doença". Descrições e `meta description`
   também não podem ser quase-idênticas.
4. Cross-links nos dois sentidos (pilar → landing na secção resumida;
   landing → pilar como "guia completo do subsídio de doença").
5. Cluster: `trabalho-rendimento` (mesmo do pilar), `tipo: "artigo"`.
6. Checklist obrigatória completa (GA4, JSON-LD, disclaimer, "Verificado
   a", canónica, autoria, sitemap, pesquisa.js, testes).

**Pontos ⚠️ a re-verificar nesse momento** (já documentados em
`baixa-medica-subsidio-doenca.html`, mas com potencial de terem mudado
entretanto):
- Comunicação da autodeclaração ao empregador — à data de 05/07/2026,
  não automática (código SMS/e-mail); confirmar se entretanto passou a
  automática antes de reafirmar na landing.

O anteprojecto de reforma laboral ("Trabalho XXI") sobre autodeclaração
fraudulenta como justa causa de despedimento **deixou de ser um ponto a
re-verificar** — foi removido da página em 2026-07-05 (ver entrada de
revisão no fim deste ficheiro): a Proposta de Lei n.º 77/XVII/1.ª foi
chumbada na Assembleia da República, não é lei nem proposta viva. Não
reintroduzir sem um facto novo e confirmado.

---

## CLUSTER HABITAÇÃO

Criado a 3 jul 2026 — pillar `p/habitacao.html` + 2 artigos-filho
(`porta-65.html`, `apoio-extraordinario-renda.html`). Expandido a 20 jul
2026 (Sessão 1 do plano "Expansão do Cluster Habitação") com mais 2
artigos-filho de compra (`imt-jovem.html`,
`garantia-publica-credito-habitacao.html`), e fechado no mesmo dia
(Sessão 3) com mais 2 artigos-filho — um de arrendamento
(`deducao-rendas-irs.html`) e um de carência habitacional
(`primeiro-direito.html`) — **7 páginas no total** (+ hub + simulador),
sexto cluster do site, reorganizado em três secções no hub: 🏠 Arrendar
/ 🔑 Comprar / 🏚️ Situações de carência. Fact-check prévio obrigatório
(bloqueante, ver "REGRAS DE CONTEÚDO") feito via `WebSearch` em todas as
sessões — `WebFetch` está completamente bloqueado neste ambiente de
sessão (403 em qualquer URL, incluindo domínios fora de `.gov.pt`, ex.:
`en.wikipedia.org` — não é um bloqueio específico a portais oficiais, é
o próprio `WebFetch` que não funciona nesta sessão). As páginas citam
sempre a URL oficial como fonte, mesmo sem acesso directo — mesmo
padrão já usado no site para fontes que devolvem 403 a bots (ver
"FONTES VERIFICADAS E APROVADAS").

**Regra de dados (20 jul 2026, reforçada na Sessão 2)**: qualquer valor
legal do IMT Jovem ou da Garantia Pública (limiares em €, percentagens,
prazos, idades — **incluindo os limites das Regiões Autónomas e a
tabela geral de IMT** de habitação própria e permanente, escalões/taxas/
parcelas a abater) vem SEMPRE de `dados/parametros/habitacao.yaml` (padrão OpenFisca, mesmo
princípio de `csi.yaml`/`subsidio-doenca.yaml`/`abono.yaml`) —
consolidado em `dados/parametros.json` por
`scripts/gerar_parametros_json.py`. Nunca escrever um destes valores
directamente numa página nova sem primeiro confirmar (ou acrescentar)
a entrada correspondente no YAML, com `referencia_legal`/`fonte_url`/
`verificado_em` — é o que `tests/test_valores_ancora.py` verifica
(secção "Cluster Habitação").

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
  à data de verificação (20 jul 2026, reconfirmado na Sessão 3)**. Por
  isso `apoio-extraordinario-renda.html` não é um guia de candidatura —
  é uma página "estado actual + alternativas", apontando para o Porta 65.
  **Reforma "produto único" (Sessão 3, 20 jul 2026)**: o Governo
  manifestou intenção de fundir Porta 65/Porta 65+/PAER/Arrendar para
  Subarrendar num único produto — confirmado só como intenção anunciada,
  **sem** projecto de lei nem consulta pública publicados; nota de
  watchlist não-alarmista acrescentada a `porta-65.html`. Distinta da
  reforma mais ampla do arrendamento aprovada em Conselho de Ministros a
  9/07/2026 ("Construir Portugal" — antecipação do fim do controlo de
  rendas em contratos novos, novas regras para contratos pré-1990,
  despejo ao fim de 2 meses de renda em atraso) e do **Fundo de
  Emergência para a Habitação** (FEH, criado no mesmo Conselho de
  Ministros — apoio automático em 10 dias para despejados por
  incapacidade de pagar renda ou vítimas de violência doméstica, até
  2.300€/mês) — **também só aprovado em CM, não confirmado publicado em
  DR** à data de verificação; `primeiro-direito.html` menciona-o com essa
  ressalva explícita, nunca como recurso já disponível.
- **Dedução de rendas no IRS** (`deducao-rendas-irs.html`, publicada
  20 jul 2026, Sessão 3): Decreto-Lei n.º 97/2026, de 20 de maio —
  **já publicado**, com efeitos desde 1 de janeiro de 2026 (excepto o
  IVA a 6%, desde 1 jul 2026). Sobe o limite de dedução (15% das rendas
  pagas) de **700€** (regime anterior, ainda o limite da declaração
  entregue em 2026, sobre rendimentos de 2025) para **900€** nas rendas
  de 2026 (declaração de 2027) e **1.000€** a partir de 2027 — ponto de
  maior confusão pública, por isso tratado com uma tabela de cronologia
  dedicada. Condição: contrato comunicado à Autoridade Tributária —
  desde 1 ago 2025 o inquilino pode comunicá-lo (função «Comunicação de
  Locatário ou Sublocatário», Portaria n.º 106/2025/1) se o senhorio não
  o fizer no prazo. Mesmo diploma cria o **Regime Simplificado de
  Arrendamento Acessível (RSAA)**, efeitos desde 1 set 2026 — isenção de
  IRS/IRC para senhorios com rendas até 80% da mediana do concelho;
  benefício do senhorio, não do inquilino, tratado como nota breve.
- **1.º Direito** (`primeiro-direito.html`, publicada 20 jul 2026,
  Sessão 3): DL n.º 37/2018 alterado por DL n.º 44/2025 (27 mar 2025,
  alarga o âmbito + regime especial de comparticipação). Gerido pelo
  IHRU, mas **candidatura nunca directa** — passa sempre pelo município,
  no âmbito de uma Estratégia Local de Habitação (ELH) já aprovada;
  circuito família → município → IHRU. 4 tipologias de carência
  habitacional: precariedade, insalubridade/insegurança, sobrelotação,
  inadequação. Elegibilidade: rendimento médio mensal <4×IAS (2026:
  2.148,52€) e património mobiliário <60×IAS (2026: 32.227,80€) —
  mesma fórmula já usada no RSI, sem YAML próprio (valores só no corpo,
  nunca em title/meta, validados contra o `IAS_2026` do canário). Página
  gere expectativas explicitamente: programa estrutural, resposta em
  meses/anos, nunca uma resposta de emergência.
- **IMT Jovem** (`imt-jovem.html`, publicada 20 jul 2026): isenção total
  de IMT e Imposto do Selo até **330.539€** (2026), parcial (8% sobre o
  excedente) até **660.982€** — em 2025 eram 324.058€/648.022€, sobem
  todos os anos com a actualização geral dos escalões de IMT (+2% em
  2026, Lei n.º 73-A/2025, Orçamento do Estado). Condições: até 35 anos
  à data da escritura, não-dependente em IRS, sem propriedade nos
  últimos 3 anos, 1.ª habitação própria e permanente; perde-se se não
  afectar o imóvel em 6 meses ou não manter o destino por 6 anos.
  Herança **indivisa** não exclui a isenção; herança **partilhada**
  (mesmo uma quota pequena) exclui. Base legal: Lei n.º 30-A/2024, DL
  n.º 48-A/2024 (regime), DL n.º 48-D/2024 (emolumentos de registo).
- **Garantia Pública no crédito habitação** (`garantia-publica-credito-habitacao.html`,
  publicada 20 jul 2026): o Estado garante até **15%** do valor de
  aquisição (imóvel até **450.000€**), permitindo financiamento até
  100% sem entrada, para 18-35 anos (ambos os titulares, se forem
  dois) com rendimento até ao 8.º escalão de IRS (**86.634€/ano** em
  2026). Duração da garantia: 10 anos. **Prazo-limite: contratos
  celebrados até 31 de dezembro de 2026**, sem prorrogação confirmada
  (2 reforços de dotação já anunciados, o mais recente +750M€ em abr
  2026, elevando o total a ~2,3 mil milhões — não é o mesmo que
  prorrogar o prazo). Não há candidatura ao Estado — pede-se
  directamente ao banco, que continua a decidir livremente. Acumulável
  com o IMT Jovem. Base legal: DL n.º 44/2024, Portaria n.º
  236-A/2024/1.

### Backlog — histórico (plano "Expansão do Cluster Habitação" fechado a 20 jul 2026)

O plano de 3 sessões está **concluído** — registo mantido para memória:

| Apoio/tarefa | Estado | Nota |
|---|---|---|
| ~~Regime Simplificado de Arrendamento Acessível (RSAA)~~ | **Concluído (Sessão 3)** — nota de caixa em `deducao-rendas-irs.html`, sem página própria dedicada (benefício do senhorio, não do inquilino — fora do foco do cluster) | Ver "Estado real verificado" acima |
| ~~1.º Direito~~ | **Concluído (Sessão 3)** — `primeiro-direito.html` | Ver "Estado real verificado" acima |
| ~~Dedução de rendas em IRS~~ | **Concluído (Sessão 3)** — `deducao-rendas-irs.html` | Ver "Estado real verificado" acima |
| ~~Simulador de IMT Jovem (`simulador-imt-jovem.html`)~~ | **Concluído (Sessão 2)** — 7.º simulador do site, tabela geral de IMT 2026 verificada e parametrizada no YAML | Ver entrada de revisão da Sessão 2 no fim deste ficheiro |
| ~~Watchlist automática DRE~~ | **Concluído e calibrado contra um runner real (2026-07-20, sessão de integração)** — `dre_habitacao_paer` (revogação do PAER/reforma "produto único") e `dre_habitacao_garantia` (alteração/prorrogação DL 44/2024), mesmo mecanismo `pesquisa_interactiva` do `dre_psu`. A 1.ª corrida real (`workflow_dispatch`) confirmou um falso positivo genuíno em `dre_habitacao_paer`: a pesquisa de frase exacta funcionou correctamente e devolveu o DL n.º 20-B/2023 (diploma fundador do PAER, confirmado por `WebSearch`) e as suas alterações já conhecidas (2023-2025) — sem corte de recência, isto criaria a mesma Issue todos os dias, porque a suposição original ("qualquer Decreto-Lei nos resultados é sinal de novidade", válida para o `dre_psu` porque a PSU ainda não tem diploma nenhum) não se aplica a uma lei já em vigor há anos. Corrigido com `data_minima`/`"desde": "2026-07-20"` em `_detectar_decreto_lei_generico` (`scripts/scraper_playwright.py`) — só conta "novo" um item datado a partir da activação da watchlist; um item sem data reconhecível nunca é descartado em silêncio (mesmo invariante "nenhum estado de erro pode parecer sucesso"). `dre_psu` confirmado 100% inalterado (sem corte de recência, testado). Issue #73 fechada com a explicação. `dre_habitacao_garantia` devolveu zero resultados na 1.ª corrida (comportamento seguro, nunca disparou) — causa por investigar sem prioridade. 6 testes de regressão novos em `tests/test_dre_habitacao_watchlist.py` (18 no total), incluindo fixture com os dados reais desta corrida; ver ROADMAP.md → "Automáticos" | Regulamentação do RSAA não incluída como gatilho — já publicada (DL 97/2026), nunca esteve pendente |

**Registado para o futuro, sem prazo, sem decisão tomada**: nova tabela
de rendas máximas de referência do Porta 65 (publicação anual, fora do
alcance da watchlist DRE — é um PDF administrativo, não um decreto-lei;
ver ROADMAP.md → "À espera de um sinal").

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

**Reescrito em 2026-07-03 (2.ª vez, tarde) por decisão do Nuno**: zero
menções a GitHub/repositório/código aberto e zero menções a
inteligência artificial/automação de redação em qualquer página
pública — regra permanente registada em "REGRAS DE CONTEÚDO" → "Não
fazer". Estrutura de 5 blocos mantida: 1) o que é o
site; 2) quem está por trás — NV Labs (`id="nvlabs"`, sem link
GitHub); 3) método de verificação (`id="metodo"`, bloco central —
fontes exclusivamente oficiais, "a redação monitoriza diariamente"
(nunca "sistema automático"), carimbo "Verificado a", o que o site não
faz); 4) correcções (email ofuscado + marcador `CONTACTO-EMAIL`);
5) contacto (`id="contacto"`, só o email ofuscado). Nenhuma pessoa,
credencial ou e-mail inventados.

`sobre.html` mantém JSON-LD — única página institucional a fazê-lo,
excepção deliberada à regra "institucionais sem JSON-LD" (ver secção
"PÁGINAS INSTITUCIONAIS"): `AboutPage` (mainEntity → Organization),
`Organization` (`@id=".../sobre.html#nvlabs"`, sem `sameAs` — o único
que existia apontava para o repositório GitHub, removido nesta
revisão) e `WebSite` (publisher → Organization). Válido porque
`FAQPage`/`WebPage` herdam `author`/`publisher` de `CreativeWork` —
confirmado por `tests/test_sobre_jsonld.py`, que carrega e valida os 3
blocos como JSON real, nunca uma cópia.

### Marcador `CONTACTO-EMAIL` — preenchido e activo

O email oficial **contacto@tensdireito.com** (forwarding ImprovMX →
caixa pessoal, testado e activo desde 2026-07-03) é o único canal de
contacto do site. Nunca aparece literal no HTML fonte de nenhuma
página pública — `sobre.html` tem `<span class="email-ofuscado"
data-user="contacto" data-dominio="tensdireito.com">`, preenchido em
runtime por um `<script>` inline no fim do `<body>` (concatena
`data-user + '@' + data-dominio`, monta o `mailto:` e o texto visível,
substitui o `<span>` por um `<a>` real), com fallback `<noscript>`
("contacto (arroba) tensdireito (ponto) com"). Sem dependências
externas. O marcador `<!-- CONTACTO-EMAIL:INICIO/FIM -->` mantém-se
nos blocos "Correcções"/"Contacto" como âncora documental — nunca com
o endereço literal dentro do comentário (um comentário HTML continua a
ser texto simples no fonte, por isso quebraria a mesma regra).
Qualquer outra página que precise de referenciar contacto liga para
`/sobre.html#contacto` — nunca duplica o email nem o script de
desofuscação. `tests/test_sobre_jsonld.py` confirma: literal
`contacto@tensdireito.com` ausente de todo o HTML público, `mailto:`
presente só dentro do `<script>` de desofuscação, marcador presente.

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

**Implementado em 2026-07-04** (ver secção "AUDITORIA DE INDEXAÇÃO E
HIGIENE SEO TÉCNICA" mais abaixo) — `scripts/adicionar_article_jsonld.py`
acrescenta o objecto `Article` a cada uma das 27 páginas de conteúdo,
`datePublished` extraído da tabela "PÁGINAS PUBLICADAS" deste ficheiro
(ISO 8601 parcial, `AAAA-MM`, quando só o mês é conhecido) e
`dateModified` de `extrair_verificado_em()`.

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
permissão para apagar branches neste ambiente). Ficou registada para
apagar manualmente.

**Actualização (2026-07-04)**: confirmado via `list_branches` da API
(não só `git fetch --prune` local) que o repositório remoto tem hoje
**apenas `main`** — `claude/new-session-2oea8g` já não existe (apagada
manualmente ou pela limpeza automática do GitHub entretanto, fora desta
sessão), e o mesmo se aplica às restantes órfãs documentadas nesta
secção e nas revisões anteriores (`claude/nv-labs-branding-update-xq4kb4`,
`claude/cool-cannon-zn5nfy`, `claude/shadow-mode-issues-scraper-5u0syf`).
Nenhuma branch por apagar manualmente neste momento.

---

## AUDITORIA DE INDEXAÇÃO E HIGIENE SEO TÉCNICA (2026-07-04)

Disparada pelo export do GSC de 30/06 (18 indexadas, 11 não — 3 "página
com redirecionamento", 1 "duplicada sem canónica selecionada", 5
"rastreada não indexada", 2 "detetada não indexada"). Objectivo:
eliminar qualquer causa técnica do nosso lado; as "rastreadas/detetadas"
são discrição do Google num domínio novo — não inventado nenhum fix
para essas duas categorias.

### Passo 1 — sitemap.xml

Auditoria programática (comparação directa sitemap × ficheiros reais,
não amostragem): as 35 páginas HTML do repositório menos as 2 exclusões
deliberadas (`404.html` — erro, `robots: noindex`; `simulador-psu.html`
— ferramenta pronta mas por publicar, `robots: noindex,nofollow`) dão
33 páginas indexáveis — **exactamente as 33 entradas já presentes no
sitemap**, sem nenhum ficheiro em falta e sem nenhuma entrada fantasma.
Zero `www.`, zero `http://` (fora do `xmlns` do schema), zero
`/index.html` explícito. `lastmod` coerente com o carimbo "Verificado
a" real em todas as 14 páginas que o têm (verificado com
`extrair_verificado_em()`, a mesma função que `sincronizar_clusters.py`
já usa — nunca recalculado à parte). **O sitemap já estava correcto
antes desta sessão** — não houve nada para corrigir neste passo.

### Passo 2 — canónicas (a causa técnica real encontrada)

Achado principal desta auditoria: **nenhuma das 35 páginas tinha
`<link rel="canonical">`** — confirmado por grep ao repositório inteiro
antes de escrever qualquer código. Investigado também se havia alguma
duplicação de conteúdo real entre páginas semelhantes (candidato óbvio:
os pares do cluster PSU, mencionados no brief) — `difflib.SequenceMatcher`
sobre o texto de `<main>` das 6 páginas do cluster PSU deu uma
similaridade máxima de 14% entre qualquer par; **não há duplicação de
conteúdo real**. A causa mais provável (e a única evidência técnica
encontrada) para "duplicada, o Google escolheu outra canónica" é
exactamente a ausência do sinal: sem canónica explícita, o Google
decide por conta própria.

Corrigido por `scripts/adicionar_canonicas.py` (idempotente, `--write`):
insere `<link rel="canonical" href="https://tensdireito.com/...">`
auto-referente logo a seguir à tag `og:url` já existente e já correcta
em todas as páginas (reaproveitada como fonte do valor, nunca
recalculada a partir do caminho do ficheiro) — aplicado às 35 páginas,
incluindo `404.html`/`simulador-psu.html` (uma canónica não faz mal a
uma página `noindex`, e evita qualquer ambiguidade se algum dia for
indexada por engano).

### Passo 3 — redireccionamentos

Confirmado via `CNAME` (`tensdireito.com`, domínio apex, sem entrada
`www` no repositório): `www→apex` e `http→https` são geridos
inteiramente pela infra-estrutura do GitHub Pages (enforce HTTPS é uma
definição da plataforma, não fica no repositório) — nada para
configurar ou corrigir aqui. Confirmado que nenhum URL do sitemap
aponta para uma variante `www`/`http`. As 3 páginas "com
redirecionamento" do GSC são, com toda a probabilidade, exactamente
estas variantes automáticas — comportamento correcto, nada a corrigir.

### Passo 4a — páginas órfãs

Grafo de alcançabilidade construído a partir dos `href`s internos reais
de cada página (BFS a partir de `index.html`, mesmo HTML estático que o
Google rastreia — não depende de JS em runtime): as 33 páginas públicas
indexáveis estão todas alcançáveis em ≤2 cliques a partir de
`index.html`. As únicas 2 páginas inalcançáveis são exactamente as 2
exclusões deliberadas do Passo 1 (`404.html`, `simulador-psu.html`) —
nenhuma órfã por acidente.

### Passo 4b — Article JSON-LD

Implementa a melhoria já registada na sessão E-E-A-T anterior (ver
secção "E-E-A-T — NV LABS COMO ENTIDADE RESOLVÍVEL" → "Verificação
pós-merge"): as 27 páginas de conteúdo (as que têm `FAQPage`) só tinham
`author`/`publisher` dentro do próprio `FAQPage`, que a Google Search
Central documenta não consumir para autoria.

`scripts/adicionar_article_jsonld.py` (idempotente, `--write`) insere
um novo bloco `<script type="application/ld+json">` (`Article` — nunca
misturado no mesmo objecto que o `FAQPage`) com:
- `headline` — de `og:title` (já correcto e específico por página);
- `author`/`publisher` — `{"@id": ".../sobre.html#nvlabs"}`, mesmo
  padrão de `adicionar_autoria_artigos.py`;
- `datePublished` — de `DATAS_PUBLICACAO`, um dicionário sourced
  directamente da tabela "PÁGINAS PUBLICADAS" deste ficheiro; onde só o
  mês é conhecido (não o dia), usa-se ISO 8601 parcial (`AAAA-MM`) —
  decisão registada como pendente na sessão anterior, resolvida agora
  em vez de inventar um dia;
- `dateModified` — de `extrair_verificado_em()`; páginas sem "Verificado
  a" próprio (2 simuladores, 4 pillar pages sem carimbo) usam
  `datePublished` como `dateModified` — nunca uma data mais recente
  inventada;
- `mainEntityOfPage` — de `og:url`.

Validado: as 0 blocos JSON-LD malformados em nenhuma das 27 páginas
(`json.loads()` sobre todos os blocos `ld+json` do repositório).
`validator.schema.org` continua bloqueado nesta sessão (mesma
limitação de rede já documentada nas sessões anteriores — `WebFetch`
devolve 403 para qualquer domínio) — validação feita por leitura
estrutural directa contra o schema Article (propriedades obrigatórias
presentes, tipos correctos, `@id` de autor/editor consistente com o
`Organization` já definido em `sobre.html`).

### Passo 5 — testes permanentes

Novo `tests/test_higiene_indexacao.py` (167 casos, parametrizado sobre
as páginas reais — mesmo padrão de `test_nav_coerencia.py`): falha se
um URL do sitemap não tiver ficheiro correspondente, se uma página
pública não estiver no sitemap sem constar de `EXCLUSOES_SITEMAP`
(justificada por página, nunca "esquecimento"), se uma canónica
estiver ausente/não-auto-referente/com `www`/`index.html`, se uma
página de conteúdo não tiver o `Article` JSON-LD válido, ou se uma
página pública for órfã (sem estar em `EXCLUSOES_ORFAS`). Corre no job
"Suite de Testes (pytest)" do `integridade.yml`, a cada push a `main`,
como toda a suite.

### Resultado

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados
`False`. Idempotência de `adicionar_canonicas.py` e
`adicionar_article_jsonld.py` confirmada (2.ª corrida de cada = zero
alterações). `ruff check scripts/ --select E,F,W --ignore E501 .`
limpo. Zero regressões na suite existente.

---

## ACESSIBILIDADE — WCAG 2.1 AA (2026-07-04)

Auditoria e correcção completas, nas 36 páginas reais do repositório.
Metodologia: axe-core **4.12.1** vendorizado em
`tests/vendor/axe-core/axe.min.js` (MPL-2.0, sem CDN em runtime, mesmo
princípio de zero dependências externas nas páginas), corrido via
Playwright contra um `http.server` local enraizado na raiz do
repositório — **nunca `file://`**: a 1.ª tentativa desta sessão usou
`file://` e reportou 34/36 páginas com `color-contrast` — quase tudo
falso positivo, porque `<link>`/`<script>` de caminho absoluto (ex.
`/assets/css/nav.css`) nunca carregam sob `file://` (resolvem contra a
raiz do filesystem, não do repo). Corrigido antes de qualquer análise
válida. Complementado com auditoria manual de código para o que o axe
não cobre bem (skip-link, foco visível, Escape no menu).

### Achado lateral, não planeado: corrupção de pseudo-selectores CSS em 9 páginas

Ao investigar porque a badge "URGENTE"/"NOVO" de `index.html` tinha
texto preto sobre fundo vermelho (4.34:1, abaixo do mínimo), descoberto
que **todas** as variáveis CSS (`--teal`, `--white`, `--muted`, etc.)
de `index.html` resolviam para string vazia — `": root"` (espaço a
mais depois do `:`) invalida o token da pseudo-classe e o browser
descarta a regra inteira. O mesmo padrão (espaço a mais depois de `:`
antes de `hover`/`last-child`/`before`/`after`/etc.) existia em mais 8
páginas (`404.html`, `acao-social-escolar.html`, `bolsa-de-merito.html`,
`fontes.html`, `manuais-escolares-mega.html`, `passe-sub23.html`,
`privacidade.html`, `sobre.html`) — provavelmente resíduo de algum
processamento de texto anterior à sessão, nunca investigado até à
raiz. Corrigido com uma correcção cirúrgica (regex restrito a dentro de
`<style>`, só actua quando o nome a seguir ao `:` é um pseudo-selector
CSS conhecido — nunca um valor como `cursor: not-allowed`, apanhado e
corrigido como falso positivo antes de aplicar). Confirmado visualmente
(Chromium real, antes/depois): contadores de passos, checkmarks de
checklist, scrollbar customizada e vários `:hover` estavam
silenciosamente inertes — nada disto tinha sido tocado por esta sessão,
achado ao investigar a causa raiz em vez de aplicar um remendo
superficial só na badge.

### Fase 1 — auditoria (relatório completo antes de qualquer correcção)

Zero violações `critical`. Achados por regra (impacto axe):
`color-contrast` (serious, 34/36 páginas, 586 ocorrências — 19
combinações de cor distintas, a maior: `#0D9488` como texto sobre
branco, 3.74:1, insuficiente para 4.5:1 exigido); `link-in-text-block`
(serious, 17/36 — breadcrumbs sem sublinhado nem contraste suficiente
face ao texto vizinho); `region`/`landmark-one-main`/`landmark-unique`/
`aria-allowed-role`/`empty-table-header` (moderate/minor, best-practice
— não são critérios WCAG formais, mas 100% das páginas tinham o hero
fora de qualquer landmark). Manual: sem skip-link em nenhuma página
(2.4.1), foco totalmente invisível nos 3 campos de pesquisa de
`index.html` (`outline:none` sem substituto, 2.4.7), sem Escape a
fechar dropdown/hambúrguer, `aria-controls` em falta, `lang="pt-PT"`
inconsistente com `lang="pt"` em 34 páginas.

### Fase 2 — correcção

**Cores**: `#0D9488` (marca) mantém-se em logo/fundos/bordas/elementos
grandes (só precisam de 3:1); todo o texto e links sobre fundos claros
passam a `#0F766E` (5.47:1). Cinzento muted `#6C757D` → `#5C6770`
(5.49:1). Fundos translúcidos sobre o hero (`.resposta-direta`,
`.valor-destaque`, breadcrumb) tornados sólidos. ~15 combinações
pontuais (timeline, filtros de `noticias.html`, footer-note,
exemplo-box do RSI) ajustadas dentro da mesma família de cor —
escurecido até ≥4.5:1, nunca inventada cor nova fora da paleta. Novos
tokens `--cor-marca`/`--cor-texto-marca`/`--cor-texto-muted` em
`assets/css/nav.css` (carregado em todas as páginas) para não voltar a
divergir.

**Links**: sublinhado (`text-decoration: underline` +
`text-underline-offset`) em breadcrumbs (articles e pillar pages) e em
links dentro de texto corrido (parágrafos, `.fonte-bloco`,
`.fonte-inline`, `.aviso-info`, `.nota-tabela`, `.destaque-verde`,
`.zona-cinzenta`, `.resumo-rapido` — regra partilhada em `nav.css`).
Cards, listas de navegação (relacionados, pillar-lista, "Comece por
aqui") e a nav mantêm-se sem sublinhado, por não serem texto corrido.

**Skip-link**: `<a href="#main-content" class="skip-link">Saltar para
o conteúdo</a>` como primeiro elemento focável de cada página (36/36),
visível só ao receber foco (`.skip-link:focus { top: 0 }`, em
`nav.css`). Todas as páginas ganharam `id="main-content"` no `<main>`
— `404.html` e `index.html` não tinham nenhum `<main>` (`landmark-one-main`),
corrigido a envolver o conteúdo existente.

**Landmarks/`region`**: `.hero` (secção ou div, conforme a página)
passou a `<header class="hero">` nas 35 páginas que o têm — dá um
landmark "banner" real ao H1/breadcrumb/badge/resposta-direta que
antes ficavam fora de qualquer landmark. Confirmado por script que
localiza o `</section>`/`</div>` correcto (sem nesting de `<section>`
dentro do hero em nenhuma página, verificado antes de aplicar; para
`<div>` usado tracking de profundidade). `#destaque-sazonal` (banner
sazonal, escrito pelo pipeline entre `<!-- DESTAQUE:INICIO/FIM -->`) e
`.aviso-transicao-psu` (aviso estático em `rsi.html`/
`subsidio-desemprego.html`/`subsidio-parental.html`) ganharam
`role="region"` — para o banner sazonal, o wrapper `role="region"`
fica **fora** dos marcadores `DESTAQUE:INICIO/FIM` deliberadamente,
para nunca ser apagado pela próxima escrita do pipeline (que só troca
o conteúdo entre os marcadores, nunca o que está à volta).

**`landmark-unique`**: os 3 `role="search"` de `index.html`
(nav desktop, nav mobile, hero) ganharam `aria-label` distintos
("Pesquisa da navegação", "Pesquisa do menu móvel", "Pesquisa
principal").

**Foco visível**: `.nav-search form`/`.nav-mobile-menu form`/
`.hero-search form` de `index.html` ganharam `:focus-within` com
`border-color: #0F766E` + `box-shadow` — mesmo padrão já usado (e
confirmado correcto por cálculo de contraste, 5.47:1) nos simuladores.

**Escape + fecho ao perder o foco**: `assets/js/nav.js` reescrito —
Escape fecha o dropdown "Apoios" e o menu móvel (com foco a voltar
para o botão que os abriu) e ambos fecham também em `focusout` quando
o foco sai do menu, seguindo o padrão "disclosure" do WAI-ARIA
Authoring Practices. `aria-controls` adicionado a `.nav-toggle`
(→ `navMobileMenu`) e `.nav-dropdown-btn` (→ novo id
`navApoiosDropdownMenu`) em `scripts/sincronizar_nav.py`, propagado às
36 páginas por `sincronizar_nav.py` (idempotente).

**`aria-allowed-role`**: `role="listitem"` não é permitido em `<a
href>` (implícito `link`) — a secção "Comece por aqui" de `index.html`
passou de `<a role="listitem">` para `<ul><li><a>` semântico real, com
`.necessidade-grid li { display: contents }` para os `<li>` não
interferirem no `display:grid` (o `<a>` continua a ser o grid item
visual).

**`empty-table-header`**: `<th></th>` vazio (célula de canto da tabela
comparativa Porta 65 Jovem vs 65+) ganhou texto "Critério".

**`lang`**: as 34 páginas com `lang="pt"` passaram a `lang="pt-PT"`
(as 2 que já tinham, `amim.html`/`prestacao-social-para-a-inclusao.html`,
ficaram como estavam) — site é explicitamente PT-PT, ajuda leitores de
ecrã a escolher a voz europeia. Confirmado que nenhum teste asserta
`lang="pt"` sobre conteúdo real (só fixtures sintéticas de teste, sem
relação com as páginas reais).

Resultado confirmado por re-auditoria axe completa: **0 violações em
36/36 páginas**, todas as categorias (`color-contrast`,
`link-in-text-block`, `region`, `landmark-one-main`, `landmark-unique`,
`aria-allowed-role`, `empty-table-header`).

### Fase 3 — blindagem permanente

`tests/test_acessibilidade.py` — axe-core real (mesmo `axe.min.js`
vendorizado) sobre as 36 páginas, servidas por um `http.server` local
próprio do teste (porta livre escolhida em runtime, nunca fixa).
Threshold documentado no próprio ficheiro (mesmo espírito do guardrail
de skips): zero tolerância a `critical`/`serious`; `moderate`/`minor`
têm um limiar explícito (`LIMIAR_MODERADO_MINOR = 0`, confirmado por
esta auditoria) — subir este número exige decisão consciente, nunca
uma regressão silenciosa. Corre no job "Suite de Testes (pytest)" do
CI, mesmo padrão de `test_higiene_indexacao.py`. Checklist da secção
"CHECKLIST OBRIGATÓRIA" ganhou o item "página nova nasce a passar
`test_acessibilidade.py`".

Nova página `acessibilidade.html` — compromisso WCAG 2.1 AA, lista do
que está implementado, e como reportar barreiras (aponta para
`/sobre.html#contacto`, mesmo canal de contacto único do site,
ofuscado). Segue o padrão das páginas institucionais (OG tags,
disclaimer de independência, sem JSON-LD FAQPage/HowTo). Adicionada a
`sitemap.xml`, `scripts/pesquisa.js`, `EXCLUIDAS` de
`scripts/sincronizar_clusters.py` (institucional, não pertence a
nenhum cluster) e ligada no rodapé de ~34 páginas (index.html,
articles, pillar pages, simuladores) — não fica órfã.

### Verificação final

Suite completa + `test_acessibilidade.py`: **1135 passed, 6 skipped**
localmente (mesmos 6 skips documentados, sem relação com este
trabalho). `ruff check scripts/ --select E,F,W --ignore E501 .` limpo.
Idempotência de `sincronizar_nav.py` confirmada (2.ª corrida sem
alterações no bloco NAV). Zero regressões na suite pré-existente.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados
`False` (inalterados por esta sessão).

---

## AUDITORIA DE INFRAESTRUTURA E ROBUSTEZ (2026-07-05)

Sessão pedida a partir de uma análise externa feita só a partir deste
ficheiro, sem acesso ao código — as 6 hipóteses foram investigadas
antes de qualquer correcção. Resultado: **3 confirmadas como problema
real (uma delas mais grave e diferente da hipótese original), 1 já
resolvida antes desta sessão, 2 reportadas sem acção** (histórico Git
e ranking da pesquisa, fora do âmbito).

### 1. Achado principal — `dre_psu` nunca extraiu conteúdo real

A hipótese original ("pipeline em modo degradado crónico") estava
errada para 6 das 7 fontes monitorizadas — `seg_social_abono/rsi`,
`iefp_desemprego`, `dge_ase`, `dge_manuais`, `mega_datas` estão
genuinamente `OK`, com conteúdo real extraído todos os dias pelo
runner (o bloqueio de `WebFetch` que existe nesta sessão de
desenvolvimento é uma política de rede exclusiva do sandbox — não se
aplica ao runner de produção, que tem acesso à internet completo).

Mas `dre_psu` — o único sentinela automático que vigia a publicação
do decreto-lei da PSU — está marcada `OK` em `estado_fontes.json`
desde a sua criação (`26818af`, 2026-07-03) **sem nunca ter extraído
conteúdo real**: `titulo`/`paragrafos` sempre vazios, `avisos.log`
com "conteúdo suspeito: 0 caracteres" todos os dias desde 01/07.
Diagnosticado num runner real (`workflow_dispatch` temporário,
apagado no fim, mesmo padrão de sessões anteriores): a URL configurada
(`dre.pt/pesquisa?q=...`) devolve hoje um soft-404 ("A página não se
encontra disponível", HTTP 200) — o parâmetro de pesquisa mudou de
`q=` para `termo=` e o caminho de `/pesquisa` para `/dre/pesquisa`
(confirmado: `dre.pt/dre/pesquisa?termo=...` devolve
`page.title(): 'Resultados de pesquisa | DR'`, HTTP 200, redirecciona
para `diariodarepublica.pt/dr/pesquisa`).

**Decisão deliberada: não trocar a URL.** O novo endpoint devolve
"25 de 2.248.417 resultados" — o índice inteiro da legislação, não
filtrado pelo termo de pesquisa (confirmado com espera de até 10s,
sem alteração). O parâmetro `termo=` não parece ser lido pela SPA em
navegação directa — precisaria de simular a interacção real com a
caixa de pesquisa (evento JS), não só um GET com query string. Trocar
a URL agora criaria um estado **pior** do que o actual: pareceria
"conteúdo real" (chars > 100, contornando o guardrail abaixo) mas
nunca detectaria genuinamente o decreto-lei (o texto de 2,2M de
resultados genéricos não contém as palavras do decreto específico) —
uma falha silenciosa disfarçada de sucesso. Registado para uma sessão
com acesso a browser interactivo real, que consiga confirmar o
mecanismo correcto de disparo da pesquisa antes de qualquer troca de
URL.

**Corrigida a causa raiz do silêncio** (`scripts/scraper_playwright.py`,
`_guardar_resultado()`): "conteúdo suspeito" (status `ok`, sem sinal
de bloqueio, mas conteúdo insuficiente) só escrevia uma linha em
`avisos.log` — nunca contava para `data/estado_fontes.json` nem gerava
Issue, por isso uma fonte podia ficar `OK` e inútil indefinidamente,
sem qualquer alerta visível. Agora reaproveita `_registar_bloqueio()`
(a mesma infra-estrutura já testada de `fonte-bloqueada` — 3 dias
consecutivos → Issue, fecho automático ao recuperar) em vez de criar
uma máquina de estados paralela; `dre_psu` vai gerar a sua primeira
Issue `fonte-bloqueada` real no 3.º dia consecutivo a partir de agora,
finalmente visível. Testado em
`tests/test_scraper_conteudo_suspeito.py` (conteúdo insuficiente
regista bloqueio; conteúdo suficiente não regista nada; confirma que
`gerir_estado_fontes.py` trata este caso exactamente como um bloqueio
real, sem precisar de nenhuma alteração nesse script).

### 2. Concorrência de writes em `main` — sem `concurrency:`

`pipeline-diario.yml` e `shadow-daily.yml` são os únicos dois
workflows que fazem `git push` a `main`, e nenhum tinha bloco
`concurrency:` (confirmado por grep). Ambos fazem
`git pull --rebase origin main && git push` sem retry se o push
falhar por non-fast-forward. O desenho actual já mitiga o caso mais
comum (`shadow-daily` corre via `workflow_run` só depois de
`pipeline-diario` terminar — confirmado nos runs reais de hoje,
aecc32b→b6326e6 com 17s de intervalo, sem colisão), mas não protege
contra um `workflow_dispatch` manual a correr em paralelo com o cron,
ou uma sessão humana a fazer push no mesmo instante. Corrigido:
`concurrency: { group: main-writes, cancel-in-progress: false }`
adicionado aos dois workflows — nunca cancela um push a meio, só
serializa a fila.

### 3. Smoke test de produção — não disparava para os commits automáticos

Achado mais sério do que "ruído de commits de dados": confirmado, ao
cruzar o histórico de runs de `smoke-producao.yml` com os commits
reais, que **nenhum dos 7 runs correspondia a um commit
`github-actions[bot]`** — só a commits de sessões humanas/Claude.
Causa: pushes feitos com o `GITHUB_TOKEN` por omissão (o caso de
`pipeline-diario.yml`/`shadow-daily.yml`, sem PAT/App token próprio)
**nunca disparam outros workflows via `on: push`** — protecção
anti-recursão nativa do GitHub Actions, sem forma de contornar sem um
token dedicado. A "correcção" da sessão anterior (trocar `workflow_run`
por `push`, commit `f75170c`) funcionou para os pushes de sessão que a
testaram, mas nunca cobriu o pipeline automático — exactamente o fluxo
que já causou as duas falhas silenciosas de deploy documentadas nesta
secção "SMOKE TEST DE PRODUÇÃO". Só o cron de segurança `30 6 * * *`
cobria os commits automáticos, com risco real de disparar antes do
commit do dia (espera aleatória de até 30 min + tempo de scrape podem
empurrar o push do pipeline para depois das 6:30).

**Corrigido com smoke inline**: novo step "Smoke test de produção
(inline, pós-push)" em `pipeline-diario.yml` e `shadow-daily.yml`,
condicionado a `steps.commit_push.outputs.pushed == 'true'`, corre
`bash scripts/smoke_producao.sh` — o mesmo script, sem duplicar
lógica — no mesmo run que fez o push. Resolve por causalidade (o
smoke corre sempre que este workflow publicou de facto um commit),
não por timing (o cron `30 6 * * *` mantém-se como rede de segurança
adicional, não como cobertura principal). `smoke-producao.yml`
standalone mantém-se inalterado — continua a cobrir pushes humanos
directos a HTML, fora do pipeline.

**Lição registada**: um token por omissão nunca deve ser assumido
capaz de disparar workflows a jusante — qualquer automação futura que
precise disso (Issues são excepção, criadas via API directamente, não
via evento `push`) precisa de um PAT/App token dedicado, ou de correr
inline no mesmo workflow que fez o push, como aqui.

### 4. Testes fantasma no CI — só o caso já corrigido, nada novo

Grep a todo `scripts/`/`tests/` por outros paths hardcoded de sandbox
ou fallbacks só-locais: só as 9 referências a `/opt/pw-browsers` já
corrigidas na sessão anterior (fallback de 3 níveis: env var →
`/opt/pw-browsers` → `~/.cache/ms-playwright`). Nenhum padrão novo
encontrado — falso alarme parcial (o caso já estava resolvido).

### 5. Segredos no histórico Git — não verificável nesta sessão

`gitleaks` CLI não está instalado no sandbox de desenvolvimento e a
rede desta sessão está limitada ao repositório `tens-direito`
(tentativa de descarregar o binário do GitHub Releases bloqueada:
*"GitHub access to this repository is not enabled for this
session"*). O job "Verificar Segredos (Gitleaks)" do CI usa
`fetch-depth: 0` (checkout completo) e passa em todos os pushes
recentes, mas não ficou confirmado se `gitleaks-action@v2` em eventos
`push` escaneia sempre o histórico completo ou só os commits do push
— **não reportado como limpo nem sujo com confiança**. Recomendado ao
Nuno correr `gitleaks detect --source . --log-opts="--all"` localmente
antes de tornar o repositório privado. Nada alterado.

### 6. Pesquisa interna — ranking por camadas, corte por saturação

Confirmado: `pesquisa.js` (20,7 KB) já não ordena por ordem de
ficheiro — 3 camadas (título/descrição/keywords) + alfabética dentro
de cada camada — mas corta a 8 resultados (`MAX_RESULTADOS`) por
saturação, não por relevância real. Com mais páginas a conter "sub" no
título, exemplos mais antigos são empurrados para fora do topo — o
mesmo efeito já observado e documentado na sessão da página de baixa
médica. Ranking por relevância real (pontuação por posição do termo)
resolveria isto, mas é decisão de UX — fora do âmbito desta sessão,
só reportado.

### Canário de valores-âncora — novo, independente da investigação

Novo `tests/test_valores_ancora.py`: afirma explicitamente os
valores-base de 2026 que atravessam vários simuladores — IAS
(537,13€), percentagens do subsídio de doença (55/60/70/75%, mais
80/100% tuberculose), pisos mínimos (5,37€/dia universal; 300€/325€
proporcional) e dias de espera por vínculo (3/10/30) — extraídos dos
ficheiros HTML reais (`simulador-abono.html`, `simulador-ase.html`,
`simulador-subsidio-doenca.html`), nunca uma cópia. **Falhar aqui é o
comportamento desejado** quando a lei mudar (tipicamente em janeiro,
nova Portaria do IAS) — força uma revisão consciente de todos os
simuladores afectados em vez de uma alteração silenciosa. Confirmado
a falhar de propósito: valor do IAS adulterado manualmente para
999.99 → teste falha com mensagem clara (`assert 999.99 == 537.13`);
revertido e confirmado a passar de novo.

### Verificação final

Suite completa localmente (sandbox sem Playwright/feedparser
instalados, mesma limitação documentada em sessões anteriores): 1081
passed, 135 skipped — os 3 novos testes (`test_valores_ancora.py`,
`test_scraper_conteudo_suspeito.py`) confirmados a passar. `ruff check
scripts/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados por esta sessão). Workflow e script de
diagnóstico temporários (`diagnostico-dre-psu-temp.yml`,
`scripts/_diag_dre_psu.py`) apagados no fim, mesmo padrão de sessões
anteriores.

---

## INVARIANTE — NENHUM ESTADO DE ERRO PODE PARECER SUCESSO

Princípio extraído da sessão de fecho da auditoria de infraestrutura
(2026-07-05), depois de os três achados da sessão original se
revelarem, na prática, a mesma classe de bug:

1. **`dre_psu`** — uma extracção de 0 caracteres ficava classificada
   `OK` (sem captcha, sem redirect de login — nada que o classificador
   reconhecesse como bloqueio), por isso nunca gerava alerta. Zero
   conteúdo == sucesso, aos olhos do sistema.
2. **`smoke-producao.yml`** — o `on: push` "corrigido" parecia
   funcionar (testado com um push de sessão) mas nunca disparava para
   os commits automáticos do pipeline — exactamente o caso que motivou
   a criação do smoke test. Verde na aparência, sem nunca correr onde
   importava.
3. **Gitleaks** — o job "Verificar Segredos" está verde em todos os
   pushes a `main` há semanas, mas isso nunca provou o histórico
   limpo: `gitleaks-action@v2` só faz scan completo (`--all`) quando
   disparado por `workflow_dispatch`; em `push`, aparentemente só
   avalia os commits desse push. Verde não incluía o histórico que
   supostamente estava a proteger.

Nos três casos, o mecanismo de verificação existia, corria, e reportava
sucesso — e o sucesso era falso. Nenhum dos três era "sem verificação
nenhuma"; eram verificações com uma zona cega específica que produzia
exactamente o sinal que se esperaria de um estado saudável.

**Regra para qualquer fonte, teste, workflow ou verificação nova (ou
alterada) neste repositório**: antes de aceitar como pronta, provar
explicitamente o caminho onde ela FALHA — não só o caminho onde
funciona. Perguntas obrigatórias:
- Uma fonte nova: o que acontece se a extracção vier vazia mas o HTTP
  for 200 sem qualquer sinal de bloqueio? Fica `OK` por omissão, ou
  exige confirmação positiva de conteúdo?
- Um workflow novo (ou gatilho alterado): o disparo foi confirmado
  contra o evento REAL que importa (ex.: um commit de bot, não só um
  push de sessão), ou só contra o evento mais conveniente de testar?
- Um guardrail de segurança/qualidade: "0 problemas encontrados"
  significa mesmo "verificado e limpo", ou pode significar "não
  chegou a verificar tudo"? Confirmar o âmbito real do scan, não
  assumir pelo nome do job.

Teste que só cobre o caminho feliz não é teste — é uma confirmação de
que o código faz o que já se espera dele quando tudo corre bem. O
valor está em provar o caminho de falha, com uma asserção que falharia
se a lacuna reaparecesse (ver `tests/test_scraper_conteudo_suspeito.py`,
`test_ponta_a_ponta_conteudo_vazio_nunca_fica_ok_e_gera_issue_ao_3o_dia`,
para o padrão a seguir: liga as duas pontas reais — scraper e máquina
de estados — em vez de testar cada uma isolada e assumir que a
integração funciona).

---

## DADOS ABERTOS — GIT SCRAPING, PARÂMETROS OPENFISCA E PUBLICAÇÃO (FASES 1-3)

Sessão de infra-estrutura de dados abertos (2026-07-19), 3 fases
incrementais — cada uma útil sozinha, todas concluídas nesta sessão.
Objectivo: transformar o site de "páginas que informam" em "fonte de
dados auditável", sem violar nenhuma regra existente (nunca um valor
legal hardcoded fora da fonte canónica que esta sessão criou; nunca um
estado de erro a parecer sucesso; `escrever_ficheiro_seguro()`/allow-
lists próprias continuam a ser a única via de escrita automática).

### Fase 1 — Git scraping: historial auditável (`dados/observacoes/`)

O pipeline diário passa a commitar os dados extraídos das fontes
oficiais, criando um historial público (`git log -- dados/observacoes/<slug>.json`)
de quando cada valor mudou — um ficheiro por fonte monitorizada
(`SLUGS_MONITORIZADOS`, a mesma lista de `gerir_estado_fontes.py`),
sobrescrito no lugar; **o historial vive no `git log`, nunca num array a
crescer dentro do próprio JSON**.

- `scripts/registar_observacao.py` — lê `data/scraped/<slug>_latest.json`
  e grava/actualiza `dados/observacoes/<slug>.json` só quando
  `sha256_conteudo` mudar face ao já registado. **Regra de ruído**: nunca
  precisou de normalização própria — `hash_conteudo` já é calculado por
  `scraper_playwright.py` só sobre `conteudo_extraido` (título/
  parágrafos/itens já limpos de tags/scripts), nunca sobre `data_acesso`/
  URL/outros campos dinâmicos; o HTML bruto (timestamps, tokens CSRF)
  nunca chega a este script. **Um bloqueio nunca aparece como sucesso**:
  `data/scraped/<slug>_latest.json` só é escrito pelo scraper para
  OK/OK_VIA_ARQUIVO (nunca BLOQUEADO — confirmado lendo
  `scraper_playwright._guardar_resultado`/`_tratar_nao_ok`, nunca
  assumido); `registar_observacao.py` confirma isso de novo a partir do
  campo `status`, nunca assume `OK` por omissão — um estado inesperado
  fica `DESCONHECIDO`, com `valores_extraidos: null` + `motivo`.
- `dados/observacoes/schema.json` — JSON Schema (Draft 7) de cada
  observação; validado por `tests/test_observacoes_schema.py`
  (`jsonschema`, nova dependência em `requirements.txt`) — JSON
  malformado ou fora do schema é um teste vermelho, nunca um sucesso
  silencioso, coberto pela suite normal do job "Suite de Testes
  (pytest)" em `integridade.yml` (sem job novo).
- `pipeline-diario.yml`, novo Step 1c ("Git scraping — registar
  observações auditáveis"), logo a seguir ao scrape: corre o script e,
  para cada ficheiro de `dados/observacoes/` que mudou, faz **um commit
  por fonte** (`dados: atualização <slug> <data>`, autor
  `github-actions[bot]`) — nunca um commit a misturar várias fontes, é
  essa granularidade que torna o `git log` de cada ficheiro legível como
  historial real. `scripts/verificar_injecao.py` (guardrail de prompt
  injection) estendido a `dados/` (mesma categoria de conteúdo externo
  de `data/scraped/`).
- Bootstrap real desta sessão: as 8 fontes monitorizadas já tinham
  `_latest.json` reais em produção — `dados/observacoes/*.json` nasceu
  já com conteúdo real, não vazio. Confirmado nesta sessão: idempotência
  (2.ª corrida = zero alterações), SHA forçado a divergir produz
  observação nova, e o guard "sem `_latest.json` ainda" nunca lança
  excepção (fonte nova no dia 1).

### Fase 2 — Padrão OpenFisca: parâmetros legais em YAML versionado

Convenção OpenFisca (parâmetros com vigência, separados da lógica de
cálculo) — **sem instalar a biblioteca OpenFisca**, só o padrão.
`dados/parametros/<prestacao>.yaml`, um ficheiro por prestação; cada
parâmetro tem uma lista `valores` com `vigencia_inicio`/`valor`/
`referencia_legal`/`fonte_url`/`verificado_em` por entrada — permite
série temporal completa (valores de anos anteriores nunca são
apagados, só deixam de ser o "vigente").

- **PASSO 0, guarda dura**: `scripts/gerar_parametros_json.py` **falha**
  (`exit 1`, nunca escreve) se qualquer entrada cuja vigência já tenha
  começado (`vigencia_inicio <= hoje`) não tiver `verificado_em`,
  `referencia_legal` ou `fonte_url` preenchidos — nunca publica um
  placeholder como se fosse dado real. Confirmado a falhar de propósito
  nesta sessão (verificado_em esvaziado manualmente, revertido).
  `dados/parametros/csi.yaml` migrado nesta sessão **sem reverificação
  de raiz** — os 4 valores (8.040€/14.070€/66 anos/80%) já estavam
  fact-checked e publicados em `complemento-solidario-idosos.html`
  (verificado 25/06/2026, com `fonte`/`verificado_em` já anexados em
  `simulador-csi.html::PARAMETROS_CSI`) — a confirmação humana já
  existia, migrada tal e qual, nunca recalculada.
- `scripts/gerar_parametros_json.py` consolida `dados/parametros/*.yaml`
  num único `dados/parametros.json` (um valor **vigente** por
  parâmetro — a entrada com `vigencia_inicio` mais recente já iniciada);
  `--check` valida sem escrever (usado como rede de segurança em
  `tests/test_valores_ancora.py::test_dados_parametros_json_sincronizado_com_os_yaml`
  — esquecer de regenerar depois de editar um YAML fica vermelho).
- **`simulador-csi.html` migrado** (o simulador escolhido, com 14 golden
  tests pré-existentes): `PARAMETROS_CSI` deixou de ser um objecto JS
  inline — passa a `let PARAMETROS_CSI = null`, populado por
  `carregarParametrosCSI()` via `fetch('/dados/parametros.json')` no
  `DOMContentLoaded`. **Nunca calcula com valores em falta** (invariante
  1 da sessão): o botão "Calcular CSI" nasce `disabled`, só é activado
  depois do fetch ter sucesso; se o fetch falhar, `#avisoParametrosErro`
  (`.aviso-teto`, mesmo estilo já usado em `simulador-rsi.html`) fica
  visível e o botão mantém-se desactivado; `calcularCSIFormulario()`
  tem uma guarda própria (`if (!PARAMETROS_CSI) { ...; return; }`) como
  segunda linha de defesa. A função pura `calcularCSI(params, input)`
  **não foi tocada** — continua testável sem rede.
- Golden tests (`tests/test_simulador_csi_calculo.py`) actualizados
  para construir `params` directamente de `dados/parametros.json` (a
  "nova fonte") em vez de ler um `PARAMETROS_CSI` global da página —
  todos os 14 valores esperados permanecem **exactamente os mesmos**
  (invariante 5 da sessão). 2 testes novos, servidos por um
  `http.server` real (mesmo padrão de `test_acessibilidade.py`, nunca
  `file://`): sucesso do fetch activa o botão e calcula correctamente
  (mesmo exemplo já publicado, 203,33€/mês); falha do fetch
  (`page.route(...).abort()`) mantém o botão bloqueado e o formulário
  nunca produz resultado, mesmo tentando contornar o `disabled` via JS.
- `tests/test_valores_ancora.py` ganhou 3 testes ligados à mesma fonte:
  os 4 valores do CSI em `dados/parametros.json` continuam a bater com
  `complemento-solidario-idosos.html`; `dados/parametros.json` está
  sincronizado com os YAML (`--check`); e nenhum parâmetro vigente fica
  sem `verificado_em` (réplica visível na suite da guarda dura do PASSO 0).
- **Não migrado nesta sessão** (registado para o futuro, um simulador
  por commit, mesmo padrão do CSI): `simulador-abono.html`,
  `simulador-ase.html`, `simulador-subsidio-doenca.html` continuam com
  `PARAMETROS_*` como objecto JS inline — a afirmação "HTML e JS nunca
  contêm valores, só referências" aplica-se hoje só ao CSI.

### Fase 3 — Publicação: `dados.html` + SQLite + Datasette Lite

`scripts/gerar_base_dados.py` consolida `dados/parametros/*.yaml` (TODAS
as vigências, não só a vigente — série temporal completa, diferente de
`dados/parametros.json`) e o historial de `dados/observacoes/` numa base
SQLite única, **sem servidor** (ficheiro binário estático, servido tal e
qual pelo GitHub Pages):

- Tabela `parametros` (prestacao/parametro/descricao/unidade/valor/
  vigencia_inicio/referencia_legal/fonte_url/verificado_em) — uma linha
  por (prestação, parâmetro, vigência).
- Tabela `historial` (fonte/commit_sha/data_commit/mensagem) — derivada
  de `git log --format=... --name-only -- dados/observacoes/`,
  **parseado, nunca reinventado** (o separador de campos usa `\x1e`/
  `\x1f`, não `\x00` — `subprocess`/argv não aceita NUL embutido,
  achado real desta sessão, corrigido antes do primeiro commit).
- **Determinismo deliberado**: nenhuma tabela guarda um campo tipo
  `gerado_em`/timestamp de geração — por isso duas corridas sobre o
  mesmo estado do repositório produzem `dados/tensdireito.db`
  **byte-idêntico** (confirmado por hash em
  `tests/test_gerar_base_dados.py::test_gerar_e_deterministico`), a
  mesma condição que já vale para `registar_observacao.py`: o pipeline
  só precisa de commitar quando o conteúdo mudar de facto, nunca ruído
  diário.
- `pipeline-diario.yml`, novo Step 1d ("Publicar base de dados aberta"),
  logo a seguir ao Step 1c: corre `gerar_parametros_json.py` +
  `gerar_base_dados.py` e commita `dados/parametros.json`/
  `dados/tensdireito.db` **só se algo mudou** — corre depois do Step 1c
  de propósito, para a tabela `historial` do SQLite já reflectir o
  commit de observações do próprio dia.
- `dados.html` — página nova (cluster: nenhum, `EXCLUIDAS` em
  `sincronizar_clusters.py`, mesma categoria de `acessibilidade.html`/
  `sobre.html`): explica as 3 camadas, link directo para o Datasette
  Lite (`https://lite.datasette.io/?url=https://tensdireito.com/dados/tensdireito.db`
  — corre inteiramente no browser via WebAssembly, zero servidor),
  downloads de `/dados/parametros.json` e `/dados/tensdireito.db`, nota
  de licença **CC BY 4.0** (atribuição "tensdireito.com") com o aviso
  de que a fonte autoritativa de qualquer valor legal é sempre o
  diploma citado em `referencia_legal`, nunca estes dados. JSON-LD
  `Dataset` (schema.org) com `distribution` (`DataDownload` para os dois
  ficheiros) e `creator`/`isPartOf` a apontar para as entidades já
  definidas (`Organization` da NV Labs, `WebSite` único da homepage —
  ver secção "SCHEMA.ORG — GRAFO DO SITE"), elegível para o Google
  Dataset Search. Ligada a partir do footer de `index.html` (link "Dados
  Abertos", junto de "Fontes"/"Privacidade") — sem isso ficaria órfã
  (apanhado por `tests/test_higiene_indexacao.py`, corrigido antes do
  commit). Nasceu já com canónica/OG-image própria/botão de partilha/nav
  correctos, confirmado por `adicionar_canonicas.py`/`gerar_og_images.py
  --write`/`sincronizar_nav.py`/`inserir_botao_partilhar.py`, todos a
  **zero alterações**.
- `scripts/smoke_producao.sh` estendido: `/dados.html`,
  `/dados/parametros.json` e `/dados/tensdireito.db` entram em
  `scripts/urls_criticas.txt`; `parametros.json` ganha uma verificação
  extra — o corpo tem de parsear como JSON válido, não só devolver 200
  (apanha um 200 com corpo truncado/corrompido, ex.: cache de CDN a
  meio de um deploy); `tensdireito.db` ganha uma verificação de
  `Access-Control-Allow-Origin` — **nunca falha o smoke test por isto**
  (só `::warning::`), porque confirma comportamento da plataforma
  (GitHub Pages), não do nosso código; útil como confirmação contínua
  de que o Datasette Lite consegue mesmo ler o ficheiro de outro
  domínio, nunca testado directamente contra produção real nesta sessão
  (sandbox sem acesso à internet completo, mesma limitação documentada
  em várias sessões anteriores) — **PASSO MANUAL PARA O NUNO**:
  confirmar que `https://lite.datasette.io/?url=https://tensdireito.com/dados/tensdireito.db`
  abre mesmo depois do deploy.

### Efeito lateral corrigido no mesmo commit — sem relação com dados abertos

Ao correr `scripts/sincronizar_clusters.py` (passo obrigatório do
checklist para qualquer página nova), o bloco `ATUALIZACOES:HOME` de
`index.html` estava desactualizado de uma sessão anterior (2 cartões
apontavam para páginas já não entre as 4 mais recentemente verificadas)
— corrigido pela própria sincronização idempotente, sem relação com
`dados.html`; registado aqui por transparência, mesma disciplina de
sessões anteriores.

### O que fica registado para o futuro, sem prazo

1. ~~Migrar `simulador-abono.html`/`simulador-ase.html`/
   `simulador-subsidio-doenca.html` para o padrão de parâmetros YAML +
   fetch, um por commit, mesmo padrão do CSI.~~ **`simulador-subsidio-doenca.html`
   e `simulador-abono.html` migrados a 2026-07-19** (sessão "Parâmetros
   YAML + auditoria factual") — ver essa entrada de revisão. `simulador-ase.html`
   continua por migrar, bloqueado à espera do despacho anual da DGEstE
   (ver ROADMAP.md).
2. Confirmar em produção real (depois do deploy) que o Datasette Lite
   abre `dados/tensdireito.db` sem erro de CORS — não verificável do
   sandbox desta sessão.
3. `gitleaks` (job "Verificar Segredos") — confirmar que o novo
   binário `dados/tensdireito.db` nunca é lido como texto/escaneado
   por engano (SQLite é binário; não observado nenhum problema nos
   testes locais, mas nunca confirmado em CI real por esta sessão).

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
   ~~Limitação conhecida (Fase 5): `_paginas_elegiveis()`/`verificar_datas.main()`
   só cobriam a raiz~~ — **fechada a 2026-07-07**: ambos passaram a cobrir
   também `p/` e `documentos/` (52 páginas elegíveis; mudam sempre juntos,
   são a mesma fonte por desenho). Antes de ligar a recursividade, a
   simulação prévia sobre as 17 páginas novas encontrou exactamente 1 falso
   positivo que dispararia no dia 1 (`p/habitacao.html`, "contrato anterior
   a 15 de março de 2023" — a data-limite fixa do PAER, família de #51/#52)
   — corrigido primeiro com o marcador `anterior(es) a` em
   `MARCADORES_HISTORICOS`, nunca depois de a Issue falsa existir. Ver
   testes novos em `tests/test_verificar_datas.py` (regressão sobre o
   pillar real, guarda anti-sobre-supressão, `main()` a cobrir os 3
   directórios com nomes relativos).

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
6. **Ferramenta da validação manual (2026-07-11)**:
   `scripts/validar_carimbos_elegiveis.py` — sessão manual, só leitura,
   nunca no pipeline. Recalcula a elegibilidade com a função REAL
   (`calcular_carimbos_elegiveis`), compara com a secção do relatório de
   hoje, e verifica por página elegível: fontes `OK`, hash hoje==ontem,
   conteúdo real (≥200 chars), status `ok` (nunca `ok_via_arquivo`).
   Cobre também a zona cega documentada no ponto 4: mudanças de hash da
   fonte DESDE o carimbo da página — com URL diferente entre os dois
   scrapes são classificadas como artefacto das nossas correcções de
   fetch (casos reais: seg-social 03/07, dre_psu 07/07); com a mesma URL
   ficam como aviso ⚠️ para juízo humano, nunca falham sozinhas.
   Exit 0 = o dia conta para a contagem de ≥14; exit 1 = falso elegível
   real/scrape em falta/divergência com o relatório — o dia NÃO conta.
   Testado em `tests/test_validar_carimbos_elegiveis.py` (11 casos,
   todos os caminhos de falha provados). **Contagem iniciada: 2026-07-11
   = dia 1 validado** (9 avisos, todos artefactos de scraper) — registo
   corrente no ROADMAP.md, linha do gatilho.

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

*Última revisão automática: 2026-08-25*

---

*Última revisão: 2026-07-05 — criado `ROADMAP.md` (índice único, privado,
nunca servido — é `.md`, fora do sitemap/pesquisa.js/qualquer link de
página), consolidando os gatilhos e o trabalho pendente já espalhados por
mais de 15 secções deste ficheiro: gatilhos manuais (autobaixa, auto-update
de carimbo, densidade da PSU, backlog de Habitação), gatilhos automáticos
(decreto-lei da PSU + dependência quebrada do `dre_psu`, datas expiradas,
fontes/feeds bloqueados), trabalho futuro registado com apontador para a
secção de detalhe, datas fixas de revisão sazonal, e o que foi concluído
recentemente. Nada inventado — só extraído e apontado, nunca copiado, para
nunca divergir do detalhe que continua a viver aqui. Adicionada a linha de
apontador no topo deste ficheiro. Zero HTML tocado nesta sessão.

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

---

*Última revisão: 2026-07-04 — duas tarefas de seguimento. 1) `data/noticias_candidatos.json` completado: o formato anterior só registava top 3 + rejeitados parciais porque `selecionar_vencedor()` pára assim que encontra um vencedor (early-exit) — "o sistema viu a notícia X?" não tinha resposta garantida. Nova `analisar_candidatos_na_janela()` classifica **todos** os candidatos dentro da janela de recência (título, feed, data, score, decisão — `vencedor`/`rejeitado_score`/`rejeitado_duplicado`/`nao_escolhido`), reimplementando deliberadamente a lógica de `selecionar_vencedor()` sem early-exit (reutilizá-la não fazia sentido — o objectivo é classificar tudo). Candidatos fora da janela ficam só como contagem por feed (`fora_da_janela_por_feed`), sem detalhe, para não inchar o log. Retenção mudou de "últimas 60 corridas" para **últimos 14 dias corridos** — 2 corridas no mesmo dia (`workflow_dispatch` manual) já não conseguiam expulsar uma entrada mais antiga fora de tempo com o critério antigo. 2) Branches remotas: confirmado via `list_branches` da API (não só `git fetch --prune` local) que o repositório tem hoje **apenas `main`** — `claude/new-session-2oea8g` e todas as órfãs documentadas em revisões anteriores já não existem; nenhuma branch por apagar manualmente neste momento (secção "Fast-forward para `main` e limpeza de branch" actualizada). 12 testes novos (classificação completa, retenção por dias, borda exacta dos 14 dias). 805 testes a passar, ruff limpo, `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-03 — limpeza site-wide por decisão do Nuno: zero menções a GitHub/repositório/código aberto e zero menções a inteligência artificial/automação de redação em qualquer página pública; email oficial **contacto@tensdireito.com** (forwarding ImprovMX, testado e activo) passa a único canal de contacto, sempre ofuscado. Levantamento (`grep -ri`) confirmou 8 páginas afectadas: `sobre.html` (JSON-LD `sameAs` GitHub, blocos "NV Labs"/"Método"/"Correções"/"Contacto"), `privacidade.html`, `index.html` (footer), e as 5 pillar pages (`p/*.html`, link "Reportar erro"). `sobre.html` reescrito: bloco NV Labs perde o parágrafo sobre código/histórico público; bloco Método troca "um sistema automático verifica" por "a redação monitoriza" e perde inteiramente o parágrafo sobre redação assistida por IA; blocos Correções/Contacto perdem GitHub Issues e ganham o email ofuscado; `id="contacto"` novo no bloco Contacto para as outras páginas linkarem. JSON-LD `Organization` perde `sameAs` (apontava só para o repositório, sem substituto — não inventar um perfil). `privacidade.html`/`index.html`/5 pillar pages: link GitHub Issues substituído por `/sobre.html#contacto`.

**Ofuscação do email** (`sobre.html`, único ponto que o expõe): `<span class="email-ofuscado" data-user="contacto" data-dominio="tensdireito.com">`, sem "@" no HTML fonte, preenchido por um `<script>` inline no fim do `<body>` (`data-user + '@' + data-dominio` → `mailto:` + texto visível, substitui o `<span>` por um `<a>` real), com fallback `<noscript>` ("contacto (arroba) tensdireito (ponto) com"). Sem dependências externas, sem duplicar a lógica — as outras páginas linkam para `/sobre.html#contacto` em vez de repetir o email/script. Marcador `<!-- CONTACTO-EMAIL:INICIO/FIM -->` mantido como âncora documental nos blocos Correções/Contacto, mas sem o endereço literal dentro do próprio comentário (um comentário HTML é texto simples no fonte — colocá-lo lá quebraria a mesma regra).

Nova secção em "REGRAS DE CONTEÚDO" → "Não fazer": contacto oficial e regra permanente de vocabulário público (GitHub/IA/automação só em `scripts/`/workflows/`CLAUDE.md`/docs internos, nunca em página pública). Secção "E-E-A-T — NV LABS COMO ENTIDADE RESOLVÍVEL" actualizada (`sobre.html` — 5 blocos, marcador `CONTACTO-EMAIL`) para reflectir o estado actual em vez do estado de quando o email ainda não existia; entradas de revisão anteriores a esta (histórico de 2026-07-03 mais cedo) mantidas tal como estavam escritas nessa altura, sem reescrever o passado.

Testes: `tests/test_sobre_jsonld.py` actualizado — `sameAs` GitHub removido da asserção (agora confirma a sua ausência), teste do marcador CONTACTO-EMAIL reescrito para confirmar activação (email nunca literal, `data-user`/`data-dominio` presentes, `mailto:` só dentro do script), novo teste parametrizado sobre as 35 páginas públicas reais (raiz + `p/*.html`) que falha se o literal `contacto@tensdireito.com` ou a palavra "github" aparecerem em qualquer uma. `grep -rliE` final ao repositório confirma zero ocorrências de `github`/`inteligência artificial`/`\bIA\b`/`issues`/`código aberto`/`repositório`/`assistida por`/`automação` em HTML público, e zero ocorrências do email literal. 786 testes a passar nesta sessão (768 + 18 skipped, incluindo os 78 de `test_sobre_jsonld.py`) — 3 ficheiros de notícias (`test_gerar_noticias.py`/`test_gerar_noticias_guardrail.py`/`test_migrar_noticias.py`) não recolhidos por falta do módulo `feedparser` neste sandbox (limitação do ambiente local, não desta mudança — inalterados por esta sessão), ruff limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` confirmados `False`.

---

*Última revisão: 2026-07-04 — fecho da tarefa de limpeza `sobre.html`. Fast-forward de `claude/sobre-html-cleanup-o9dete` para `main` (commit `2a0e256`, sem PR, mesma REGRA ABSOLUTA — GIT de sempre); tentativa de apagar a branch remota deu **403** (mesma limitação já registada várias vezes nesta secção para outras branches — sem `gh` CLI nem tool MCP com permissão de apagar refs neste ambiente) — `claude/sobre-html-cleanup-o9dete` fica registada para apagar manualmente.

Ao pedir confirmação de que a suite completa (incluindo os 3 ficheiros de notícias dependentes de `feedparser`) corre em CI real, descoberto que **nenhum dos 5 workflows do repositório alguma vez correu `pytest`** — `integridade.yml` só tinha gitleaks/ruff/pip-audit/html5validator/`verificar_injecao.py`, `validar-conteudo.yml` usa um validador próprio via BeautifulSoup; a suite sempre foi só um passo manual do checklist (secção "CHECKLIST OBRIGATÓRIA"). Reportado antes de mexer, por pedido explícito. Decisão: fechar a lacuna de vez em vez de contornar — novo job **`testes-python`** em `integridade.yml` (`pip install -r requirements.txt` + `pytest` + `playwright install chromium --with-deps`, corre `pytest tests/ -q` em cada push a `main`); commit `3c3f993`. Confirmado no run real (`28697865007`, job `85110610336`): **839 passed, 50 skipped em 1.61s** — os 3 ficheiros de notícias correram com `feedparser` disponível no runner e passaram, tal como os testes Playwright-dependentes. Todos os 6 jobs do workflow (incluindo `testes-python`) e os 3 checks do commit anterior (`Validar Conteúdo HTML`, `pages build and deployment`) terminaram com sucesso. Checklist e tabela de workflows actualizadas — a nota "testes só correm manualmente" já não é verdade; correr localmente primeiro continua recomendado só para poupar uma volta de CI vermelho.

Verificação da página live (`tensdireito.com/sobre.html`): `WebFetch` e `curl` directo confirmaram **403 da política de rede da sessão** para este domínio (`recentRelayFailures` da proxy: "gateway answered 403 to CONNECT (policy denial)") — o próprio README da proxy é explícito em não contornar e reportar o host bloqueado, por isso não foi tentada nenhuma alternativa técnica. **O Nuno reportou externamente à sessão** (fora desta conversa, no browser dele) que a página live tem os 5 blocos correctos, zero termos proibidos no HTML servido, ofuscação do email a funcionar com fallback `<noscript>` visível a clientes sem JS, e o footer com link funcional para `#nvlabs` — registado aqui como relato do Nuno, não como verificação feita por esta sessão (distinção deliberada, mesma disciplina que o site aplica a factos publicados: nunca afirmar "confirmado" quando não foi esta sessão a confirmar). O que esta sessão confirmou directamente: o commit `2a0e256` (o mesmo revisto e testado localmente) foi o que o "pages build and deployment" publicou com sucesso — logo o HTML servido é, por construção, o mesmo já validado localmente e em CI.

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` em `scripts/decisao_datas.py` no final desta sessão.

---

*Última revisão: 2026-07-04 — auditoria de indexação e higiene SEO técnica, disparada pelo export do GSC de 30/06 (18 indexadas, 11 não). Nova secção "AUDITORIA DE INDEXAÇÃO E HIGIENE SEO TÉCNICA (2026-07-04)" com o detalhe completo. Resumo: (1) `sitemap.xml` já estava correcto — 33 entradas para as 33 páginas indexáveis (35 páginas reais menos `404.html`/`simulador-psu.html`, exclusões deliberadas), `lastmod` coerente com o carimbo real, nada a corrigir; (2) achado principal — nenhuma das 35 páginas tinha `<link rel="canonical">`, causa técnica mais provável do "duplicada, o Google escolheu outra canónica" do GSC (confirmado que não há duplicação de conteúdo real entre as páginas do cluster PSU, similaridade máxima 14%); corrigido por novo `scripts/adicionar_canonicas.py` (idempotente), canónica auto-referente nas 35 páginas; (3) `www→apex`/`http→https` confirmados geridos pela infra-estrutura do GitHub Pages via `CNAME`, nada a configurar no repositório — as 3 páginas "com redirecionamento" do GSC são essas variantes automáticas, comportamento correcto; (4) confirmado que nenhuma das 33 páginas públicas é órfã (alcançáveis em ≤2 cliques a partir de `index.html` por BFS sobre os `href`s reais); implementada a melhoria já registada na sessão E-E-A-T anterior — novo `scripts/adicionar_article_jsonld.py` (idempotente) acrescenta `Article` JSON-LD (author/publisher/datePublished/dateModified) às 27 páginas de conteúdo, `datePublished` sourced da tabela "PÁGINAS PUBLICADAS" deste ficheiro; (5) novo `tests/test_higiene_indexacao.py` (167 casos parametrizados sobre as páginas reais) no job "Suite de Testes (pytest)" do CI. `validator.schema.org` continua bloqueado nesta sessão (mesma limitação de rede documentada nas sessões anteriores) — validação feita por leitura estrutural directa. 935 testes a passar localmente + 50 skipped (3 ficheiros de notícias não recolhidos por falta de `feedparser` neste sandbox, mesma limitação documentada nas sessões anteriores — corre completo no CI), ruff limpo, idempotência de ambos os scripts novos confirmada (2.ª corrida = zero alterações), `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — 6 feeds novos em `scripts/gerar_noticias.py` (pedido do Nuno: cobrir Fiscalidade/IRS, IAS, calendário de pagamentos SS/pensões, Habitação/arrendamento além do Porta 65, salário mínimo, CSI — as duas primeiras categorias estavam a zero). `FEEDS` sobe de 7 para 13: `irs_fiscalidade`, `ias_valor_referencia`, `calendario_pagamentos_seg_social`, `habitacao_arrendamento`, `salario_minimo`, `csi_idosos` — todos testados com fetch real num `workflow_dispatch` temporário (`diagnostico-feeds-temp.yml`, apagado no fim, mesmo padrão das sessões anteriores) antes de entrar no código: nenhum `bozo`, todos com dezenas/centenas de entradas reais e relevantes (48-100). `LIMITE_ENTRADAS_POR_FEED` mantido em 15 (195 entradas/corrida); janela de recência de 7 dias e guardrails (`escrever_ficheiro_seguro`, allow-list) inalterados. Sem alteração nenhuma a `gerir_estado_feeds.py`/`pipeline-diario.yml` — ambos já são genéricos sobre os nomes de `data/feeds_saude_hoje.json`, os 6 feeds novos entram na máquina de estados e na criação de Issues `feed-morto` sem código adicional.

Dois achados corrigidos ao ligar os feeds novos: 1) `CLUSTER_KEYWORDS` nunca tinha ganho uma entrada para o cluster `habitacao` (existe em `data/clusters.json` desde 3 jul 2026) — corrigido, mais `"salário mínimo"` acrescentado a `trabalho-rendimento`; novo teste de regressão compara `CLUSTER_KEYWORDS` contra os clusters reais do JSON para nunca mais faltar um. 2) Bug real de substring encontrado ao testar `detect_category` com um título real do diagnóstico (artigo de IRS ficava classificado como "apoios" em vez de "fiscal"): a keyword `"ias"` (para IAS) é substring de palavras portuguesas correntes sem relação nenhuma com o tema — a mais grave, "dias" — pelo que qualquer notícia que mencionasse "dias" ganhava pontos/categoria de "apoios" por engano; nova `_contem_keyword()` exige fronteira de palavra (`\bias\b`) só para esta keyword ambígua, usada por `score_entry`/`detect_category`, mantendo substring simples para todas as outras (nenhuma outra colide com palavras comuns ao ponto de justificar o mesmo tratamento).

Avaliação pedida (mudar de "1 vencedor/dia" para "top 2-3/dia com dedup por cluster") reportada ao Nuno antes de qualquer implementação — nada codificado para essa parte nesta revisão. 1015 testes a passar localmente + 50 skipped (mesma limitação de `feedparser` no sandbox local, não no CI), ruff limpo, `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — implementada a mudança de "1 vencedor/dia" para "até `MAX_VENCEDORES_POR_DIA` (3) vencedores/dia, no máximo 1 por categoria", aprovada pelo Nuno com uma condição explícita: os slots são oportunistas, nunca quotas — uma categoria sem candidato com score positivo, dentro da janela de 7 dias e não duplicado fica simplesmente vazia, nunca se publica um artigo fraco só para preencher diversidade (o corte de qualidade aplica-se sempre antes da diversidade). Grounding real antes da correcção: `data/noticias.json` tinha 14/17 itens "apoios", 0 "fiscal"/"emprego"/"habitacao" — confirmava que a selecção global por score afogava sistematicamente as categorias novas mesmo já com feeds dedicados.

Terminologia corrigida face ao pedido original: agrupamento por `categoria` (`CAT_KEYWORDS`, sempre preenchida, 6 valores) em vez de `cluster_id` (só ~metade dos temas têm cluster no site — Fiscalidade não tem nenhum) — "dedup por cluster" estrito deixaria Fiscalidade/calendário de pagamentos/salário mínimo todos no mesmo balde "sem cluster", o que anularia o objectivo.

`scripts/gerar_noticias.py`: `ResultadoSelecao.vencedor`/`motivo_vencedor` (singular) substituídos por `vencedores: List[Candidato]`; `Candidato` ganhou o campo `categoria`; `selecionar_vencedor()` renomeada para `selecionar_vencedores()` (nova lógica: 1 vencedor por categoria, corte de score/recência/dedup igual a antes, dedup entre vencedores da mesma corrida acrescentado — evita que 2 feeds diferentes apanhem a mesma notícia sob categorias diferentes); `analisar_candidatos_na_janela()` actualizada com a mesma lógica (sem early-exit, para auditoria completa) — "nao_escolhido" continua a cobrir as duas razões de não-selecção que não são score/duplicado (categoria já preenchida hoje, ou slots esgotados), sem inventar mais rótulos porque nada no log os distingue; `registar_candidatos_log()` grava `"vencedores"` (lista) em vez de `"vencedor"` (schema muda só para a frente — entradas antigas do histórico ficam com a chave antiga, inofensivo, nada relê o conteúdo de registos passados); `main()` passa a publicar todos os vencedores da corrida, não só 1.

Achado adicional ao escrever os testes do multi-vencedor: `KEYWORDS` (a lista geral de scoring, distinta de `CAT_KEYWORDS`) não cobria vocabulário de salário mínimo/CSI — confirmado com os títulos reais do diagnóstico de feeds: **5/5** manchetes reais de salário mínimo e **4/5** de CSI pontuavam 0, nunca passariam do corte de qualidade por muito que a categoria tivesse slot disponível (o feed `irs_fiscalidade` não tinha este problema — "irs" já cobria as 5/5 manchetes reais). Adicionadas as frases completas `"salário mínimo"`, `"retribuição mínima"` e `"complemento solidário"` a `KEYWORDS` — frases inteiras, não palavras soltas, para não repetir o risco de ambiguidade já corrigido para `"ias"`.

23 testes novos/reescritos em `tests/test_gerar_noticias.py` (multi-vencedor por categoria, limite configurável, nunca 2 vencedores da mesma categoria, categoria sem candidato válido fica vazia, scoring de salário mínimo/CSI com títulos reais). 1024 testes a passar localmente + 50 skipped (mesma limitação de `feedparser` no sandbox local, não no CI), ruff limpo, idempotência de `sincronizar_saidas()` reconfirmada (`--sync` sem alterações), `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — nova página `prestacao-social-para-a-inclusao.html` (PSI), cluster `idosos-incapacidade-cuidadores`. Fact-check via `WebSearch` (`WebFetch` continua bloqueado nesta sessão — 403 em qualquer domínio externo, incluindo DRE e seg-social.pt; triangulado por múltiplas pesquisas independentes, mesmo padrão já documentado para outras sessões com a mesma limitação) confirmou: Decreto-Lei n.º 126-A/2017 (cria a PSI, 3 componentes — base, complemento, majoração ainda não em vigor — e substitui a antiga pensão social de invalidez); valores 2026 da Portaria n.º 58-A/2026/1, de 3 de fevereiro (componente base 333,64 €/mês = 4.003,68 €/ano; complemento com valor de referência anual de 8.040 €, até 670 €/mês; limite de acumulação com trabalho de 12.880 €/ano), todos confirmados de forma independente em múltiplas fontes (governamentais, financeiras e associações de pessoas com deficiência) — com retroativos a janeiro de 2026, pagos em fevereiro; a regra dos 55 anos (certificação da incapacidade requerida antes dessa idade) e a condição de grau ≥ 80% para acumulação com pensão de invalidez, ambas confirmadas. Secção obrigatória "PSI e a Prestação Social Única": verificado contra a lista real dos 13 apoios já documentada em `psu-lista-13-apoios.html` e contra cobertura jornalística (Observador) do texto aprovado a 25/06/2026 — a PSI **não consta** dessa lista; a página regista essa conclusão com a data da verificação e a ressalva explícita de que o decreto-lei da PSU ainda não foi publicado (prazo PRR: 31 ago 2026), nunca afirmando uma exclusão definitiva antes desse diploma sair.

`amim.html` actualizado no mesmo commit: a secção 7.3 (PSI) tinha valores de 2025 (Portaria n.º 113/2025/1) — substituídos pelos valores 2026 confirmados nesta sessão, com link para o novo guia; carimbo "Verificado a" (3 ocorrências, incluindo a `dateModified` do JSON-LD `Article`) actualizado de 1 para 4 de julho de 2026, reflectindo a correcção factual real feita na página. `data/clusters.json` (cluster ganha a 4.ª página e `descricao_curta` actualizada), `scripts/pesquisa.js`, `sitemap.xml` (páginas nova e `amim.html`) e `scripts/adicionar_article_jsonld.py` (`DATAS_PUBLICACAO`) actualizados a par; `scripts/sincronizar_clusters.py` corrido com sucesso — regenerou `index.html` (bloco `ATUALIZACOES:HOME`, cartão do cluster com "4 guias"), `p/idosos-incapacidade-cuidadores.html` (`PILLAR-LISTA`) e o `RELACIONADOS` dos 4 artigos do cluster (cross-link automático nos dois sentidos, sem edição manual); idempotência confirmada (2.ª corrida = zero alterações). `scripts/adicionar_canonicas.py`, `adicionar_article_jsonld.py` e `adicionar_autoria_artigos.py` corridos sobre a página nova (`--write`); achado ao correr por esta ordem: como o `Article` JSON-LD já traz o `@id` da NV Labs, `adicionar_autoria_artigos.py` viu o `@id` já presente e saltou a inserção no bloco `FAQPage` — corrigido à mão, adicionando `author`/`publisher` directamente ao `FAQPage` para ficar consistente com o padrão das restantes páginas (que tiveram os dois scripts corridos pela ordem inversa em 2026-07-03/04). Confirmado com Chromium real (Playwright, mesmo padrão de `tests/test_pesquisa_hero.py`): título, H1, breadcrumb, disclaimer, 17 blocos `<details>`, pesquisa da nav a devolver a página nova e o AMIM para "psi", nav com o dropdown de clusters funcional — sem erros de página (os 2 avisos de consola são recursos externos bloqueados pela política de rede da sessão, GA4/CookieYes, não um bug da página). 996 testes a passar localmente + 6 skipped (mais 3 ficheiros de notícias não recolhidos por falta de `feedparser` neste sandbox, mesma limitação documentada em sessões anteriores — corre completo no CI), ruff limpo, `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-05 — auditoria à suite de testes pedida pelo Nuno depois de a sessão anterior ter reportado "996 passed + 6 skipped" (queda aparente face aos "1024 passed + 50 skipped" da sessão anterior a essa, com a aritmética a não bater certo). Investigação confirmou **zero testes removidos, consolidados ou reparametrizados** — `git diff tests/` entre os dois commits de sessão (`5422252`→`992b6d3`) está vazio. A causa foi inteiramente ambiental: o "996+6" da sessão anterior era um sandbox local sem `feedparser` instalável (`sgmllib3k` falha a compilar neste ambiente — contornado nesta sessão extraindo `sgmllib.py` manualmente para `site-packages`), com 3 ficheiros de notícias postos de fora via `--ignore` sem essa ressalva ficar clara no relato. Números reconciliados via **CI real** (`mcp__github__get_job_logs`, não assumidos): commit `5422252` → 1024 passed + 50 skipped = 1074; commit `992b6d3` (página PSI) → 1041 passed + 50 skipped = 1091 — a diferença de +17 bate certo com a parametrização sobre páginas reais que a página nova + os 4 artigos do cluster actualizados introduzem em `test_breadcrumb_coerencia.py`/`test_nav_coerencia.py`/`test_higiene_indexacao.py`/etc.

**Achado real, mais grave do que a pergunta original**: os 50 skipped do CI (constantes nos dois commits) escondiam um bug de ambiente, não skips legítimos. `test_pesquisa_hero.py`, `test_pesquisa_ranking.py`, `test_share_js.py` e `test_simulador_psu_calculo.py` (44 testes) usavam `os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")` — `/opt/pw-browsers` é uma convenção exclusiva do sandbox do Claude Code; o CI (GitHub Actions) nunca define essa variável e `playwright install chromium --with-deps` instala em `~/.cache/ms-playwright/`. Resultado: **estes 44 testes nunca correram no CI desde a criação do job `testes-python`** (commit `3c3f993`, confirmado também no run mais antigo desse job — `28697865007` — que já mostrava "839 passed, 50 skipped"). Achado e corrigido em duas iterações, ambas verificadas contra o CI real (não só localmente, onde `/opt/pw-browsers` sempre mascarou o problema):
1. `3ed2974` — `_localizar_chromium()` passou a tentar `PLAYWRIGHT_BROWSERS_PATH`, depois `/opt/pw-browsers`, depois `~/.cache/ms-playwright`. Insuficiente sozinho: o CI continuou a reportar 50 skipped — o log do "Instalar dependências" revelou que o build "Chrome for Testing" (revisão 1223) que o CI descarrega extrai para `chrome-linux64/`, não `chrome-linux/` (a convenção mais antiga, ainda usada na revisão 1194 empacotada no sandbox).
2. `aeeb22b` — glob alargado para `chrome-linux*/chrome`, cobrindo as duas variantes; confirmado por simulação isolada da função com a estrutura real do CI (`chromium-1223/chrome-linux64/chrome`) antes do push, e depois **confirmado no CI real**: run `28707427757`, job "Suite de Testes (pytest)" → `1085 passed, 6 skipped` — os 44 testes correram e passaram, pela primeira vez, no GitHub Actions.

**Lição registada**: um path específico do sandbox nunca pode ser a única estratégia de localização de um binário externo — qualquer helper deste tipo tem de tentar múltiplas convenções plausíveis (variável de ambiente explícita → convenção do ambiente de desenvolvimento → convenção por omissão da ferramenta), nunca assumir que o ambiente de desenvolvimento e o CI colocam as coisas no mesmo sítio.

**Guardrail anti-recorrência**: novo passo em `integridade.yml` ("Guardrail — limiar de testes skipped") falha o job se o total de skipped exceder o limiar documentado de 6 — testado a falhar propositadamente no primeiro push desta correcção (50 > 6, exit 1, confirmado no run `28707289867`) e a passar depois da correcção completa (`6 (limiar: 6)`, run `28707427757`). Qualquer skip legítimo futuro exige subir este número conscientemente, nunca por acidente de ambiente.

**Branches remotas** (`git ls-remote --heads origin`): só `main` e `claude/psi-social-benefit-page-p41ath`, ambas no mesmo commit (`992b6d3` no momento da verificação) — a segunda é órfã (idêntica a `main`, integrada por fast-forward na sessão anterior), sem trabalho por perder; fica registada para o Nuno apagar manualmente no browser (mesma limitação de sempre — sem `gh` CLI nem ferramenta MCP com permissão para apagar branches nesta sessão).

**Checklist do gatilho PSU**: novo item 9 no plano de acção da secção "IMPACTO DA PSU" — revalidar a secção "PSI e a Prestação Social Única" de `prestacao-social-para-a-inclusao.html` contra a lista definitiva dos 13 apoios no decreto-lei publicado, actualizando `psu-lista-13-apoios.html` e o cluster no mesmo commit.

Suite completa local (com `feedparser` e Playwright ambos disponíveis, depois da correcção): **1085 passed, 6 skipped** — idêntico ao CI real, confirmando que a suite está agora totalmente reconciliada entre ambientes. `ruff check scripts/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`. Nenhuma branch nova criada — trabalho directo em `main`, 3 commits (`3ed2974`, `aeeb22b`, e este de documentação).

---

*Última revisão: 2026-07-04 — auditoria e correcção completas de acessibilidade WCAG 2.1 AA nas 36 páginas reais, com axe-core 4.12.1 vendorizado (`tests/vendor/axe-core/`) e auditoria manual complementar — ver secção "ACESSIBILIDADE — WCAG 2.1 AA" para o detalhe completo. Fase 1 (auditoria): zero `critical`, `color-contrast` em 34/36 páginas (586 ocorrências) e `link-in-text-block` em 17/36 eram os únicos critérios WCAG formais falhados; o resto (`region`, `landmark-one-main`, `landmark-unique`, `aria-allowed-role`, `empty-table-header`) é best-practice do axe, não critério formal. Manual: sem skip-link, foco invisível nos 3 campos de pesquisa de `index.html`, sem Escape no menu, `lang` inconsistente. Achado lateral não planeado: corrupção de pseudo-selectores CSS (`": root"`/`": hover"` com espaço a mais, inválido) em 9 páginas, incluindo `index.html` — nenhuma variável CSS de `index.html` resolvia, causando (entre outras coisas) o próprio `color-contrast` da badge urgente; corrigido na raiz, não com um remendo local.

Fase 2 (correcção): `#0D9488` (marca) mantém-se em logo/fundos/bordas/elementos grandes; texto e links passam a `#0F766E` (5.47:1); `#6C757D` → `#5C6770`; fundos translúcidos sobre o hero tornados sólidos; ~15 casos pontuais ajustados dentro da mesma paleta — nunca inventada cor nova. Novos tokens `--cor-marca`/`--cor-texto-marca`/`--cor-texto-muted` em `nav.css`. Sublinhado em breadcrumbs e links de texto corrido (cards/listas de navegação mantêm-se sem). Skip-link + `id="main-content"` nas 36 páginas (`404.html`/`index.html` ganharam `<main>`, não tinham nenhum). `.hero` → `<header class="hero">` em 35 páginas (landmark banner real). `aria-label` distintos nos 3 `role="search"` de `index.html`. Foco visível (`:focus-within`) nos 3 campos de pesquisa de `index.html`, mesmo padrão dos simuladores. `nav.js` ganhou Escape + fecho ao perder o foco (padrão APG); `aria-controls` adicionado ao template de `sincronizar_nav.py`, propagado às 36 páginas. `role="listitem"` inválido em `<a>` (index.html) corrigido para `<ul><li><a>` semântico real. `<th>` vazio de `porta-65.html` ganhou texto. As 34 páginas com `lang="pt"` passaram a `lang="pt-PT"`.

Fase 3 (blindagem): `tests/test_acessibilidade.py` — axe-core real sobre as 36 páginas, zero tolerância a critical/serious, limiar documentado (0) para moderate/minor; novo item na checklist de publicação; nova página `acessibilidade.html` (compromisso WCAG AA, como reportar barreiras), ligada no rodapé de ~34 páginas, em `sitemap.xml` e `scripts/pesquisa.js`.

Resultado confirmado por re-auditoria completa: **0 violações em 36/36 páginas** (todas as categorias). Suite completa + a nova: **1135 passed, 6 skipped** localmente (mesmos 6 skips já documentados). `ruff check scripts/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — nova página `simulador-csi.html` (Calculadora 3 de `CALCULADORAS-SPEC.md` — as calculadoras 1/2, abono e ASE, já existiam desde jun. 2026). Valores da fórmula (8.040€/ano isolado, 14.070€/ano casal, 66 anos e 9 meses, rendimento de trabalho a 80%) reaproveitados de `complemento-solidario-idosos.html` — já fact-checked e publicados (verificado 25/06/2026), sem necessidade de nova verificação de fonte. Simplificação deliberada face à Segurança Social real: não modela saldos bancários acima de 10.500€, outros imóveis nem rendimentos fictícios sobre patrimônio — a Segurança Social ajusta o valor final com esses factores; o disclaimer da página e uma pergunta do FAQ deixam isso explícito. `PARAMETROS_CSI` segue o mesmo padrão de `PARAMETROS_PSU` em `simulador-psu.html` (cada valor com `fonte`/`verificado_em` próprios), mas activo desde já (não há decreto-lei a aguardar). JSON-LD: `WebApplication` (novo neste site, `applicationCategory: "FinanceApplication"`) + `FAQPage` + `BreadcrumbList` + `Article` (obrigatório sempre que há `FAQPage`, confirmado por `tests/test_higiene_indexacao.py`). Adicionada a `data/clusters.json` (cluster `idosos-incapacidade-cuidadores`, tipo `ferramenta`, mesmo padrão de `simulador-abono.html`/`simulador-ase.html`), `scripts/pesquisa.js` e `sitemap.xml`; `scripts/sincronizar_clusters.py` corrido com sucesso — regenerou automaticamente o `PILLAR-LISTA` de `p/idosos-incapacidade-cuidadores.html` (badge "Ferramenta"), o cartão do cluster na homepage ("4 guias · 1 simulador") e o `RELACIONADOS` dos 4 artigos do cluster (cross-link automático, sem edição manual); idempotência confirmada (2.ª corrida = zero alterações). `scripts/adicionar_canonicas.py`/`adicionar_article_jsonld.py` corridos em modo `--write` só para confirmar que os blocos escritos à mão já batiam certo com o que os scripts gerariam (0 ficheiros alterados — nenhum a mais além do já inserido). `scripts/inserir_botao_partilhar.py` confirmou o botão já presente (idempotente). Testado com Chromium real via Playwright: 3 casos de simulação (isolado com pensão, idade abaixo do mínimo, casal com dois rendimentos) a dar o valor esperado na UI, sem erros de consola próprios da página. Golden tests novos em `tests/test_simulador_csi_calculo.py` (14 testes, mesma filosofia de `test_simulador_psu_calculo.py` — extrai o JS real do HTML, nunca uma cópia; aqui os parâmetros de teste SÃO os valores de produção, já fact-checked, ao contrário da PSU). Suite completa: 1076 passed, 7 skipped (mesma limitação de `feedparser` neste sandbox, documentada em revisões anteriores — corre completo no CI), `ruff check scripts/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 (sessão seguinte) — sessão de correcções, 4 tarefas. 1) **404 de `simulador-csi.html` em produção**: causa raiz confirmada via API do GitHub Actions — o run "pages build and deployment" do commit `142c29b` (o próprio commit do CSI) tinha **falhado** no passo "Deploy to GitHub Pages" com `##[error]Deployment failed, try again later.`, um erro transitório e genérico da infra-estrutura do GitHub Pages, sem qualquer relação com o conteúdo (`actions/deploy-pages@v5`, mesmo padrão já documentado numa sessão anterior para o commit `6301240`) — o ficheiro, o `git add`/commit e o `sitemap.xml` estavam sempre correctos; a produção só nunca recebeu o deploy. Corrigido com `rerun_workflow_run` (retry, sem qualquer alteração de código) — 2.ª tentativa (`run_attempt: 2`) terminou `success`.

2) **Alinhamento de `simulador-abono.html`/`simulador-ase.html` com `CALCULADORAS-SPEC.md`**: auditoria com tabela de verificação apresentada antes de qualquer correcção (todos os valores cruzados com `abono-de-familia.html`/`acao-social-escolar.html`, ambos já fact-checked). Encontrado um **erro factual real** no simulador ASE (não um valor "sem fonte" — um valor que contradizia a fonte já verificada): o objecto `cobertura` e os dois FAQs (JSON-LD e visível) afirmavam que o escalão B tinha transporte **gratuito** — `acao-social-escolar.html` diz que só o escalão A é gratuito, o B tem **desconto**; corrigido nos 3 sítios, com regressão dedicada em `tests/test_simulador_ase_calculo.py::test_cobertura_escalao_b_transporte_nao_e_gratuito`. Também tingido "Escalão B: refeições com valor reduzido" para o valor exacto já publicado ("desconto de 50%"). Ambos os simuladores reescritos: valores consolidados num único objecto `CONFIG` por ficheiro (cada campo com o diploma de origem em comentário — Portaria n.º 60/2026/1 para o abono, Despacho n.º 8452-A/2015 + 5296/2017 para a ASE), lógica de cálculo extraída para uma função pura (`calcularAbonoValor`/`calcularASEValor`) separada da manipulação de DOM, `WebApplication` JSON-LD adicionado (faltava nos dois, só existia no CSI), `aria-live="polite"` no `#resultado`, `inputmode="numeric"` em todos os inputs numéricos, frase "Simulação indicativa. O valor final é determinado pela [Segurança Social/secretaria da escola]." acrescentada ao disclaimer, e evento GA4 `calc_resultado` (mesmo padrão do CSI). Email/contacto: nenhuma das páginas expõe endereço literal — nada a corrigir, já conforme. Golden tests novos: `tests/test_simulador_abono_calculo.py` (9 casos, incluindo um que replica literalmente o exemplo "190,98 × 1,5 = 286,47€/mês" já publicado em `abono-de-familia.html`) e `tests/test_simulador_ase_calculo.py` (8 casos, incluindo a regressão do bug do transporte), ambos com teste de sanidade "nenhum campo de CONFIG a null". Achado adicional durante a auditoria: **nenhum dos 3 simuladores** (incluindo o CSI da sessão anterior) tinha o selo visível "Verificado a DD/MM/YYYY" exigido no ponto 0 da spec — acrescentado aos três (`24/06/2026` abono/ASE, `25/06/2026` CSI), com o texto formatado exactamente como `pela redação do <a href="/sobre.html#metodo">Tens Direito</a>` para bater certo com o padrão de atribuição já usado em todo o site (ver ponto 3 abaixo — este texto não era decorativo, tinha de reconhecer o regex existente).

3) **Job pytest em `integridade.yml`**: o job "Suite de Testes (pytest)" já existia (criado numa sessão anterior, 2026-07-04 mais cedo) e já falha o workflow em caso de teste falhado (`set -o pipefail`, sem `|| true`) — mas **estava a falhar em `main`** desde o commit do CSI, por um motivo não notado nessa altura: o guardrail de skips (limiar documentado de 6) via 7 skips reais, porque `test_adicionar_autoria_artigos.py` conta como skip legítimo qualquer página sem carimbo "Verificado a" — e nem o CSI nem (já agora, verificado) o abono/ASE tinham esse carimbo. Corrigido na raiz (acrescentar o carimbo às 3 páginas, ponto 2 acima) em vez de simplesmente subir o limiar; total final de skips confirmado em **4**, todos legítimos e documentados (`p/apoios-escolares.html` sem carimbo, `404.html`/`index.html`/`simulador-psu.html` fora do índice de pesquisa) — limiar do guardrail actualizado de 6 para 4. Acrescentada cache de dependências (`actions/setup-python` com `cache: pip`) e cache dedicada dos browsers do Playwright (`actions/cache` sobre `~/.cache/ms-playwright`, chave por hash de `requirements.txt`) para poupar o download de ~113 MiB do Chromium em pushes que não alterem `requirements.txt`. Tempos reais medidos no run do commit `142c29b` (antes da cache): "Instalar dependências" 29s, "Correr suite completa" 93s, job completo ~2m9s — **não é pesado o suficiente para justificar dividir em "rápidos no push + completo agendado"**; a suite inteira já corre em menos de 2m30s por push, dentro do orçamento normal de CI para um site deste tamanho — decisão tomada e aplicada nesta sessão (não perguntada à parte, como pedido, com os tempos mostrados aqui).

4) **Verificação final**: suite completa local (sem os 3 ficheiros de notícias dependentes de `feedparser`, mesma limitação de sandbox documentada, corre completo no CI) — **1096 passed, 4 skipped**; `ruff check scripts/ --select E,F,W --ignore E501 .` limpo; `html5validator` (venv à parte, mesmo binário `vnu.jar` do CI) sem erros nas 3 páginas de simuladores; validador de conteúdo próprio do site (GA4/OG/JSON-LD/disclaimer/"Verificado a", mesma lógica de `validar-conteudo.yml`) sem avisos nas 3 páginas; os 3 blocos JSON-LD de cada simulador confirmados como JSON válido (`WebApplication`/`FAQPage`/`BreadcrumbList`/`Article`). Testado com Chromium real via Playwright: abono (bebé 24 meses, monoparental → 286,47€/mês, sem erros de consola), ASE (4 pessoas/24.000€ → Escalão B, texto "Com desconto" confirmado no transporte, sem erros de consola), CSI já confirmado na sessão anterior. Trabalho directo em `main`, sem branches (regra absoluta). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — visibilidade dos 3 simuladores (abono, ASE, CSI) na navegação do site. Nova página `simuladores.html` (hub, template igual às restantes páginas — hero teal, cards, disclaimer, footer) com JSON-LD `CollectionPage` (`hasPart` com os 3 `WebApplication`) + `BreadcrumbList`; excluída do sistema de clusters (`EXCLUIDAS` em `sincronizar_clusters.py`, mesma categoria de `comecar-aqui.html` — agrega ferramentas de 3 clusters diferentes, não pertence a nenhum único). Link "🧮 Simuladores" acrescentado à **fonte** da nav (`render_nav()` em `scripts/sincronizar_nav.py`, desktop + mobile) e propagado às 39 páginas reais correndo o script — nunca editado página a página. Homepage ganhou secção "Simuladores e Calculadoras" (3 `apoio-card`, reaproveitando a classe já existente da secção "Todos os guias") logo a seguir ao herói, antes de "Comece por aqui". Os 3 simuladores ganharam `BreadcrumbList` JSON-LD de 3 níveis (Início > Simuladores > [nome], a apontar para `/simuladores.html`) e um breadcrumb visível no hero (cores adaptadas ao hero de cada página — texto escuro no hero claro de abono/CSI, `#EDF6F5`/branco sólido no hero teal da ASE, nunca `rgba` translúcido sobre cor — resultado do achado da auditoria WCAG anterior sobre fundos translúcidos). Corrigido de caminho um gap pré-existente: `comecar-aqui.html` só linkava abono/ASE na secção "Ferramentas & Calculadoras", nunca tinha sido actualizado com o CSI — acrescentado, mais um link para o hub novo. `data/clusters.json` inalterado (o hub não pertence a nenhum cluster). Adicionado a `sitemap.xml` e `scripts/pesquisa.js` (cluster/tipo `null`, mesmo padrão de `comecar-aqui.html`). Novo teste `test_nav_tem_link_simuladores` em `tests/test_nav_coerencia.py` (parametrizado sobre as páginas reais, confirma o link em ambos os menus desktop/mobile do bloco NAV). Achado durante a auditoria de acessibilidade da página nova: violação `heading-order` (moderate) por `<h1>` seguido directamente de `<h3>` sem `<h2>` a meio — corrigido com um `<h2>` visível ("Escolhe o teu simulador") antes da grelha de cards, sem esconder nada via CSS. Confirmado com Chromium real (Playwright): hub com 3 cards e nav funcional, homepage com a secção nova e o link na nav (3 ocorrências: dropdown context + desktop + mobile), breadcrumb do abono a mostrar "Início › Simuladores › Abono de Família". Suite completa: 1149 passed, 4 skipped (mesmos skips já documentados); `ruff check scripts/ --select E,F,W --ignore E501 .` limpo; `html5validator` sobre as páginas tocadas sem erros novos (os 2 avisos de CSS `text-underline-offset`/`scrollbar-width` são falsos positivos pré-existentes do `vnu.jar`, já presentes noutras páginas publicadas — confirmado comparando com `p/apoios-escolares.html` antes de assumir que era um problema novo); 0 violações de acessibilidade nas 39 páginas reais (incluindo a nova). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-04 — smoke test de produção pós-deploy, para apanhar falhas silenciosas do GitHub Pages como as duas já documentadas (`##[error]Deployment failed, try again later.` em `actions/deploy-pages@v5`, sem qualquer sinal de erro no resto do pipeline). Novo `.github/workflows/smoke-producao.yml` (`workflow_run` sobre "pages build and deployment" + cron `30 6 * * *` de segurança, depois do `pipeline-diario.yml`, + `workflow_dispatch` manual) e `scripts/smoke_producao.sh` (retry 3× com 30s de espera, `User-Agent` identificado, lista de páginas em `scripts/urls_criticas.txt` — único sítio a editar). Para as 3 páginas de simulador, confirma também que o corpo da resposta contém `"Verificado a"` — apanha 200 com conteúdo errado/antigo, não só 404; essa verificação nunca tem retry (conteúdo não muda entre tentativas). Nova secção "SMOKE TEST DE PRODUÇÃO" documenta tudo. Testado com um falso-404 real contra produção (`workflow_dispatch`, run 28721561322): as 9 páginas reais passaram em ~2,5s (confirmando de caminho que `/simuladores.html` e os 3 simuladores estão mesmo em produção — resolve a dúvida em aberto da sessão anterior sobre o deploy do commit `121686b`), o URL inventado falhou 404 nas 3 tentativas com exactamente 30s entre cada uma, job terminou vermelho ao fim de ~63s — linha de teste removida no commit seguinte. Lógica de sucesso/404/conteúdo-em-falta também confirmada localmente com um `http.server` a fazer de produção, sem tocar em produção real para esses três casos. Decisão desta sessão: falha = vermelho no Actions é suficiente por agora, sem notificações externas nem referências públicas. Nenhuma alteração a `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` (continuam `False`) — este workflow só lê a produção, nunca escreve nada.

---

*Última revisão: 2026-07-05 (sessão seguinte) — simulador de subsídio de doença (4.ª calculadora) + gatilho autobaixa registado. Nova secção "GATILHO AUTOBAIXA" no CLAUDE.md, mesmo padrão do "Cluster PSU — páginas em espera": página `autobaixa.html` fica registada como gatilho futuro (condição: Nuno confirmar no GSC impressões relevantes para "autobaixa"/"autodeclaração de doença" em `baixa-medica-subsidio-doenca.html`), não criada nesta sessão.

Fact-check prévio via `WebSearch` dos 3 pontos ⚠️ ainda em aberto do artigo:
- **⚠️A (retroatividade dos dias de espera):** **não confirmado** — nenhuma fonte encontrada sustenta que os 3 dias de espera são pagos retroactivamente quando a baixa ultrapassa 30 dias. A pista mais provável é confusão com "registo de remuneração equivalente" (Decreto-Lei n.º 28/2004) — um conceito de carreira contributiva, não de pagamento em dinheiro. Implementada a versão conservadora: dias de espera nunca pagos, excepto nas 3 excepções legais já documentadas (internamento/cirurgia/tuberculose).
- **⚠️B (piso 300€/325€ em períodos parciais):** as fontes confirmam o piso mensal mas não especificam a aplicação a períodos parciais. Implementada a versão conservadora indicada no brief: piso diário proporcional (300÷30=10,00€; 325÷30=10,8333€), documentado como interpretação conservadora tanto no simulador como no FAQ.
- **⚠️C (tratamento fiscal):** **confirmado** via 2 fontes independentes — o subsídio de doença é isento de IRS e a Segurança Social não aplica descontos adicionais sobre o próprio subsídio (ao contrário do salário normal, que gera descontos TSU/IRS). O simulador mostra sempre o valor bruto/estimado da prestação, com nota explicativa.

Nova página `simulador-subsidio-doenca.html` (hero claro, fora da navegação contextual — mesmo padrão de `simulador-abono.html`/`simulador-ase.html`/`simulador-csi.html`, JSON-LD `WebApplication`+`FAQPage`+`BreadcrumbList`+`Article`, nada inventado face ao padrão real). `PARAMETROS_SUBSIDIO_DOENCA` com `fonte`/`verificado_em` por constante. Função pura `calcularSubsidioDoenca()` — escalões contados desde o dia 1 da incapacidade (os dias de espera consomem escalão, mas não são pagos), majoração automática por RR≤500€ ou condição familiar, piso universal 5,37€/dia, piso proporcional 300€/325€, tetos de duração 1095/365/sem limite (tuberculose), com aviso visível quando a duração excede o teto. Desagregação por escalão sempre visível no resultado (dias × taxa × valor/dia = subtotal) — decisão deliberada do brief para tornar o resultado auditável. Opção avançada de 6 meses de salário **não implementada** (permitida pelo brief como opcional "sem complexidade excessiva" — mantido o campo único de salário mensal constante, com nota a explicar a simplificação).

15 golden tests em `tests/test_simulador_subsidio_doenca_calculo.py`, todos calculados à mão nos comentários (fracções exactas onde possível — ex. RR diária de 1.400€ = 140/3€, o que torna vários casos exactos ao cêntimo sem arredondamento intermédio): caso 1 (1.400€/100 dias → 2.699,67€) confirmado idêntico ao exemplo já publicado no artigo, com um teste extra que verifica literalmente a substring "2.699,67" no HTML do artigo — nunca deixa os dois divergirem em silêncio. Caso 5 (510€/60 dias) confirma o piso 300/325 a morder de facto (9,35€ e 10,20€/dia calculados sobem para 10,00€ e 10,8333€). Caso 8 usa 1200 dias de tuberculose deliberadamente (excederia o teto de 1095 do regime geral) para provar a ausência de limite. Teste de coerência artigo↔simulador dedicado — reimporta `PARAMETROS_SUBSIDIO_DOENCA` real e confirma que as constantes batem certo com os valores publicados no artigo (nunca só no simulador).

Integração: `data/clusters.json` (cluster `trabalho-rendimento`, tipo `ferramenta`); `sincronizar_clusters.py` corrido com sucesso — regenerou automaticamente o `PILLAR-LISTA` de `p/trabalho-rendimento.html` (badge "Ferramenta"), o cartão do cluster na homepage ("3 guias · 1 simulador") e o `RELACIONADOS` de `rsi.html`/`subsidio-desemprego.html`/`baixa-medica-subsidio-doenca.html`; idempotência confirmada. `sincronizar_nav.py`/`inserir_botao_partilhar.py` confirmaram idempotência (marcadores já inseridos manualmente, mesmo padrão dos outros simuladores). `adicionar_canonicas.py --write` sem alterações (canónica já inline). `simuladores.html` (hub) e a secção "Simuladores e Calculadoras" do `index.html` ganharam o 4.º cartão; `sim-grid` do hub passou de `repeat(3,1fr)` para `repeat(auto-fit, minmax(220px,1fr))` para acomodar o crescimento sem novas alterações manuais no futuro. Cross-link nos dois sentidos com o artigo (secção "Quanto se recebe" do artigo deixou de anunciar "brevemente" e passa a linkar directamente).

Confirmado com Chromium real: caso 1 renderiza exactamente "€2699.67" com 3 linhas de desagregação; caso 10 (1200 dias) mostra o aviso de teto visível. Suite completa: 1201 passed, 4 skipped (mesma limitação de `feedparser` neste sandbox, corre completo no CI); `ruff check scripts/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-05 — nova página `baixa-medica-subsidio-doenca.html`, cluster `trabalho-rendimento`. Fact-check prévio via `WebSearch` (`WebFetch` continua completamente bloqueado nesta sessão — 403 em todos os domínios, mesma limitação documentada em sessões anteriores), triangulando sempre ≥2-3 fontes secundárias por facto e citando o diploma legal quando disponível: percentagens do subsídio (55%/60%/70%/75% por duração, 80%/100% tuberculose), majoração de +5pp e as duas garantias mínimas (5,37€/dia universal; 300€/325€ quando RR>500€, via Guia Prático do ISS), dias de espera por regime (3/10/30) e as 4 excepções sem espera, autodeclaração de doença (3 dias/episódio, 2/ano, comunicação à SS automática desde 29/07/2025 mas ao empregador via código, não automática), prazos e limites do CIT por patologia (Portaria n.º 11/2024), fiscalização e juntas médicas (Decreto-Lei n.º 8/2024 — verificação desde o 4.º dia, convocatória SMS/e-mail, exame por videochamada/domiciliário), e regimes especiais (independentes, desempregados, pensionistas, acidente de trabalho vs. doença profissional). Dois pontos verificados e conscientemente deixados incertos no texto ("depende das regras em vigor"): a redução do prazo de convocação da junta médica da função pública de 60 para 30 dias (achado apenas como proposta do OE2024, não confirmado como já em vigor — texto remete para a DGAEP sem fixar o número) e o regime de pagamento do isolamento profilático em 2026 (fontes encontradas eram da era COVID). O anteprojecto de reforma laboral sobre autodeclaração fraudulenta e despedimento é apresentado como proposta em debate, não lei em vigor. Gravidez de risco tratada deliberadamente como prestação distinta (100% da RR desde o 1.º dia até à data provável do parto), nunca listada junto das excepções ao período de espera do subsídio de doença comum.

Estrutura: tabela de desambiguação autodeclaração/CIT/atestado privado logo no topo (ângulo diferenciador do artigo), exemplo de cálculo com valores 2026 a atravessar 3 escalões (recalculado à mão: RR diária 46,67€, 100 dias de baixa → 2.699,67€ ao todo), tabela de prorrogações por patologia (oncologia/AVC/doença isquémica cardíaca 90 dias, pós-operatório 60, tuberculose 180), e 9 perguntas na secção "Dúvidas frequentes" (sair de casa, viajar, período experimental, despedimento, subsídio de férias/Natal, IRS, falta à junta médica, atestado privado vs. CIT, prorrogação no limite) — 8 delas também no JSON-LD `FAQPage`, mais uma sobre independentes. `HowTo` com 6 passos (consulta → CIT electrónico → entrega ao empregador em 5 dias úteis → recepção automática pela SS → prorrogação → pagamento). Nenhum simulador criado (fora do âmbito desta sessão) — uma frase no texto anuncia um simulador futuro, sem link morto.

Integração completa: `data/clusters.json` (3.ª página do cluster Trabalho e Rendimento, `descricao_curta` actualizada) e `sincronizar_clusters.py`/`sincronizar_nav.py`/`inserir_botao_partilhar.py` corridos com sucesso (idempotência confirmada nos dois primeiros na 2.ª corrida); `adicionar_canonicas.py` → `adicionar_autoria_artigos.py` → `adicionar_article_jsonld.py`, por esta ordem específica, para evitar o bug já documentado (2026-07-04) em que o `@id` da NV Labs no `Article` faz `adicionar_autoria_artigos.py` saltar a inserção no `FAQPage` — confirmado sem necessidade de correcção manual desta vez. `sitemap.xml` e `scripts/pesquisa.js` actualizados; `scripts/urls_criticas.txt` deliberadamente não tocado (a lista do smoke test cobre só um punhado de páginas evergreen de topo — abono, RSI, subsídio de desemprego — não todos os artigos do site).

Achado real durante a verificação da suite: `tests/test_pesquisa_ranking.py::test_match_fora_do_titulo_mostra_excerto_destacado` fixava a pesquisa por "sub" a devolver sempre `cuidador-informal.html` num resultado de camada 2 — com a página nova (título "Baixa médica e **sub**sídio de doença") a somar-se aos títulos já existentes com "sub" (`subsidio-parental`, `subsidio-desemprego`, `passe-sub23`, `psu-lista-13-apoios`), os 8 resultados ficam todos preenchidos antes de chegar ao Cuidador Informal — confirmado correndo `pesquisar('sub')` num Chromium real antes de mexer, não assumido. Não é um bug do conteúdo novo, é o limite de `MAX_RESULTADOS = 8` a ser atingido por crescimento orgânico do site — o mesmo voltará a acontecer com a próxima página cujo título contenha "sub". Corrigido generalizando o teste (confirma que *algum* resultado de camada 2/3 aparece com `<mark>` no excerto, sem fixar uma página específica) em vez de pinar `cuidador-informal.html` para sempre — preserva a intenção original do teste (validar o mecanismo de excerto) sem ficar frágil a cada nova página com "sub" no título.

Suite completa: 1168 passed, 4 skipped localmente (3 ficheiros de notícias não recolhidos por falta de `feedparser` neste sandbox — `sgmllib3k` falha a compilar, mesma limitação documentada em sessões anteriores, corre completo no CI); `html5validator` não instalável neste sandbox (erro de build `install_layout` do `setuptools`/`distutils` do sistema, afecta qualquer pacote com `setup.py` legado — validação estrutural feita manualmente com `json.loads()` sobre os 4 blocos JSON-LD, confirmação via CI depois do push); `ruff check scripts/ --select E,F,W --ignore E501 .` limpo. Confirmado com Chromium real: título, H1, breadcrumb de 3 níveis, 9 blocos `<details>` a abrir/fechar, skip-link presente, pesquisa da nav a devolver a página nova para "baixa". `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-05 (sessão de correcções pontuais) — duas remoções factuais definitivas em `baixa-medica-subsidio-doenca.html`, verificadas via `WebSearch` antes de mexer. 1) **Anteprojecto "Trabalho XXI"** (autodeclaração fraudulenta equiparada a justa causa de despedimento): removido por completo do parágrafo final da secção "Autodeclaração de doença" — confirmado que a Proposta de Lei n.º 77/XVII/1.ª foi **chumbada** na Assembleia da República (~20 jun 2026, votos contra de Chega/PS/Livre/PCP/BE/PAN/JPP, só PSD/CDS/IL a favor); o Código do Trabalho mantém-se inalterado nesse ponto. Não é uma nota histórica que se mantém marcada como "chumbada" — é remoção total, por decisão do Nuno: informação sobre uma proposta rejeitada não pertence a um guia prático de direitos. 2) **Isolamento profilático**: removida a subsecção inteira (`h3`+parágrafo) de "Regimes especiais" — estava marcada "depende das regras em vigor" desde a publicação por não ter sido possível confirmar o regime de pagamento pós-COVID; instrução explícita desta sessão: sem confirmação, sai, não fica meio-dito.

Verificação de efeitos colaterais antes de remover (não apenas depois): nenhuma das duas passagens correspondia a uma pergunta do JSON-LD `FAQPage` (as 9 perguntas do schema são todas sobre percentagens, dias de espera, despedimento por doença — tema distinto —, IRS, junta médica, viagens, duração e independentes; nenhuma sobre a reforma laboral ou isolamento) nem a um dos 9 blocos `<details>` visíveis da secção "Dúvidas frequentes" — confirmado por grep a `<summary>` antes de editar. A página não tem índice/sumário com âncoras internas, por isso não havia risco de link morto para uma secção removida. Nenhum facto de cálculo, percentagem, prazo ou o exemplo dos 2.699,67€ foi tocado. Carimbo "Verificado a" mantido em 05/07/2026 (mesma sessão de calendário da publicação original, sem alteração de data necessária).

Secção "GATILHO AUTOBAIXA" actualizada: o ponto "Anteprojecto de reforma laboral… confirmar o estado real" deixou de constar da lista de pontos ⚠️ a re-verificar — passou de "em aberto" a "resolvido e removido definitivamente", com nota explícita para não reintroduzir nenhum dos dois temas sem um facto novo e confirmado. Suite completa + `ruff check scripts/ --select E,F,W --ignore E501 .` a correr antes do commit; `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`.

---

*Última revisão: 2026-07-05 — auditoria de infraestrutura e robustez, pedida a partir de uma análise externa feita só sobre este ficheiro (6 hipóteses, investigadas antes de qualquer correcção — ver nova secção "AUDITORIA DE INFRAESTRUTURA E ROBUSTEZ (2026-07-05)"). Achado principal, diferente da hipótese original: `dre_psu` (o único sentinela automático da publicação do decreto-lei da PSU) nunca extraiu conteúdo real desde a criação (2026-07-03) — a URL configurada devolve hoje um soft-404 (`q=` → `termo=`, `/pesquisa` → `/dre/pesquisa`, confirmado num runner real); decidido não trocar a URL porque o endpoint novo devolve o índice inteiro da legislação (2,2M resultados) não filtrado pelo termo, o que criaria uma falha silenciosa disfarçada de sucesso. Corrigida a causa raiz do silêncio: "conteúdo suspeito" passa a reaproveitar a máquina de estados já testada de `fonte-bloqueada` (`scripts/scraper_playwright.py::_guardar_resultado`), gerando Issue ao 3.º dia consecutivo em vez de ficar indefinidamente `OK` e inútil. Confirmado e corrigido: nenhum dos dois workflows que fazem `git push` (`pipeline-diario.yml`/`shadow-daily.yml`) tinha bloco `concurrency:` — adicionado `{ group: main-writes, cancel-in-progress: false }` aos dois. Achado mais sério do que "ruído": `smoke-producao.yml` nunca disparou para nenhum commit automático (`github-actions[bot]`) — pushes feitos com o `GITHUB_TOKEN` por omissão não disparam outros workflows via `on: push`, protecção anti-recursão nativa do GitHub Actions; corrigido com smoke inline (novo step nos dois workflows automáticos, reutilizando `scripts/smoke_producao.sh`, condicionado a ter havido push nesse run). Falsos alarmes confirmados: testes fantasma (já corrigidos numa sessão anterior, nada novo); pesquisa interna (ranking já em camadas, corte por saturação é decisão de UX). Sem acção, só reportado: segredos no histórico Git (`gitleaks` CLI indisponível neste sandbox, sem rede para o instalar — recomendado ao Nuno correr localmente antes de tornar o repositório privado). Novo `tests/test_valores_ancora.py` (canário de valores-âncora 2026 — IAS, percentagens/pisos/dias de espera do subsídio de doença — confirmado a falhar de propósito com um valor adulterado, depois revertido) e `tests/test_scraper_conteudo_suspeito.py`. Suite completa localmente (sandbox sem Playwright/feedparser, mesma limitação documentada): 1081 passed, 135 skipped; `ruff` limpo; `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`. Trabalho feito na branch `claude/infrastructure-audit-robustness-10k2wc` (exigida pelo ambiente remoto desta sessão).

---

*Última revisão: 2026-07-05 (fecho da auditoria) — quatro decisões definitivas antes do merge. 1) **Gitleaks**: os 8 "leaks" confirmados falsos positivos um por um (nunca só "porque sim") — token de sessão JSF (`CTKN_DYN`) pertence sempre a uma sessão anónima pré-autenticação numa página pública (login gateway ou deep-link de informação da Segurança Social, nunca área com dados de cidadão) e chave de widget de chatbot é pública por design; nenhum concedia acesso a nada de sensível, mesmo no instante do commit. Silenciados em `.gitleaksignore` (nunca reescrita de histórico), com justificação por fingerprint; confirmado no runner real que o scan volta a "no leaks found". 2) **dre_psu**: confirmado que a correcção da sessão anterior não recriava o silêncio — `_guardar_resultado()` escreve directamente em `data/bloqueios.json` (o mesmo ficheiro que `gerir_estado_fontes.py` lê), independente da classificação `Estado.OK` do `classificador_resposta.py`; novo teste de ponta-a-ponta (`test_ponta_a_ponta_conteudo_vazio_nunca_fica_ok_e_gera_issue_ao_3o_dia`) liga os dois módulos reais ao longo de 3 dias simulados e prova: conteúdo vazio nunca é `OK`, fica elegível a Issue exactamente no 3.º dia. URL do DRE mantém-se por corrigir (trabalho futuro, ligado à secção "IMPACTO DA PSU"). 3) **Merge para `main`**: fast-forward directo (`12c7ad8`), sem PR — CI real confirmado: Gitleaks limpo, ruff limpo, HTML5 limpo, prompt-injection limpo (todos via evento `push` real, não `workflow_dispatch`). 4) **Prova real do smoke inline**: `pipeline-diario.yml` disparado via `workflow_dispatch` (run `28743926685`) fez scrape completo das 7 fontes, commit real como `github-actions[bot]` (`047739a auto: pipeline diário 2026-07-05`) e o step "Smoke test de produção (inline, pós-push)" correu **no mesmo run**, imediatamente a seguir ao commit, com sucesso — a prova que faltava desde a sessão anterior, de que um commit de bot real fica coberto por verificação de produção no mesmo run, não só por push de sessão. Cron `30 6 * * *` mantém-se como segunda rede, não cobertura principal. Nota operacional: o job "Suite de Testes (pytest)" mostrou lentidão anómala (>9 min) quando corrido via `workflow_dispatch` nesta sessão, sem explicação encontrada — via `push` real a `main` corre normalmente (~2 min); registado como observação, não bloqueou o merge (suite local sempre verde, 1082 passed/135 skipped). Nova secção "INVARIANTE — nenhum estado de erro pode parecer sucesso" fecha a sessão como princípio permanente do repositório. Branch `claude/infrastructure-audit-robustness-10k2wc` fica órfã após o fast-forward — para o Nuno apagar manualmente (mesma limitação de sempre, sem permissão de API para apagar branches nesta sessão).*

---

*Última revisão: 2026-07-05 — FASE 1 de `MELHORIAS-SPEC.md` (nova secção
"RESPOSTA RÁPIDA + CHECKLIST FINAL"). Antes de implementar, achado
real: os ~28 artigos já têm `.resposta-direta` no hero com o mesmo
objectivo SEO que a spec pedia para `.resposta-rapida` — confirmado com
o Nuno para reaproveitar em vez de duplicar (acrescentado só o rótulo
"⚡ Resposta rápida" + tempo de leitura, mesma caixa). Os "3 artigos com
mais tráfego GSC" do ponto 1.3 também foram confirmados directamente
pelo Nuno (sem acesso do Code ao Search Console):
`manuais-escolares-mega.html`, `acao-social-escolar.html`,
`subsidio-desemprego.html` — mais `baixa-medica-subsidio-doenca.html`
(alvo explícito da spec), 4 artigos no total. `.checklist-final` é
novo: `assets/css/checklist.css` + `assets/js/checklist.js` (mesmo
padrão de `share.css`/`share.js`), checkboxes com estado só em memória
(nunca `localStorage`), itens sourced do `HowTo` JSON-LD já publicado
em cada artigo. Dois achados corrigidos durante a implementação, ambos
apanhados pelos testes reais e não por inspecção: 1) a 1.ª versão da
`.resposta-rapida` usava `opacity` no rótulo/tempo, reduzindo o
contraste do texto branco sobre o hero teal de 5.47:1 para 4.41:1
(abaixo do mínimo AA de 4.5:1) — apanhado por
`tests/test_acessibilidade.py`, corrigido removendo o `opacity`; 2) bug
de HTML5 pré-existente (não desta sessão, confirmado por `git show
HEAD`) em `acao-social-escolar.html` — um `<div>` (tabela) dentro de um
`<span>`, inválido — corrigido trocando para `<div>` sem alterar o
visual (o `<ol>` já usa `display:flex`, que blockifica o filho de
qualquer forma). Novo `tests/test_resposta_rapida_checklist.py` (37
casos: estrutural + Chromium real — viewport mobile 390px sem overflow,
contador do checklist a actualizar, e a garantia explícita de que um
reload nunca preserva o estado das checkboxes). Checklist obrigatória
ganhou o item "novo artigo inclui os dois blocos"; `sitemap.xml`/
`data/clusters.json` inalterados (nenhuma página nova, só 4 artigos
existentes modificados). Suite completa: 1249 passed, 5 skipped (3
ficheiros de notícias não recolhidos por falta de `feedparser` neste
sandbox, mesma limitação documentada em sessões anteriores — corre
completo no CI); `ruff check scripts/ tests/ --select E,F,W --ignore
E501 .` limpo; `html5validator` (vnu.jar) sem erros nas 4 páginas.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados por esta sessão). Trabalho feito na branch
`claude/melhorias-spec-phase-1-anlctz` (designada pelo ambiente remoto
desta sessão). FASE 2 (calculadora de subsídio de doença — nota: já
existe `simulador-subsidio-doenca.html`, publicado numa sessão anterior;
confirmar com o Nuno se a FASE 2 da spec já está coberta por essa página
antes de a reimplementar), FASE 3 (gerador de documentos) e FASE 4
(árvore de decisão PSU, com gatilho no decreto-lei) ficam para sessões
seguintes, pela ordem definida em `MELHORIAS-SPEC.md`.*

---

*Última revisão: 2026-07-05 — sessão de continuidade do MELHORIAS-SPEC.md,
duas tarefas. 1) **Merge para `main`**: `claude/melhorias-spec-phase-1-
anlctz` (FASE 1) estava presa numa branch, violando a REGRA ABSOLUTA —
GIT — confirmado que `origin/main` não tinha avançado desde a criação
da branch (merge-base = HEAD de `main`), por isso fast-forward puro,
sem conflitos; push directo para `main` (commit `774cb51`). Branch
local apagado; branch remoto deu 403 na API (mesma limitação de sempre,
sem `gh` CLI nem tool MCP com permissão) — fica para o Nuno apagar
manualmente. `smoke-producao.yml` confirmado `success` no commit do
merge (run 28758600078). 2) **Auditoria da FASE 2** (`simulador-
subsidio-doenca.html`, já existia de uma sessão anterior) — **NÃO
reimplementado de raiz**, conforme pedido; os 4 pontos da spec
confirmados, não assumidos:
- **Valores/escalões**: reconfirmados por `WebSearch` directamente
  contra `seg-social.pt/subsidio-de-doenca` e fontes secundárias
  cruzadas (percentagens 55/60/70/75%, tuberculose 80/100%, dias de
  espera 3/10/30, tectos 1095/365/sem limite, prazo de garantia 6
  meses, piso universal 5,37€/dia) — todos batem certo com o já
  implementado, zero divergências. Reforçada a citação de `fonte` de
  `pisoDiarioProporcionalTaxa55`/`60` (antes "Guia Prático do ISS",
  vago e sem URL — já confirmado noutra sessão como inacessível
  directamente) para apontar a `seg-social.pt/subsidio-de-doenca`
  directamente. Ponto ⚠️A (retroactividade dos dias de espera)
  re-investigado a fundo depois de várias fontes secundárias (blogs)
  alegarem retroactividade em baixas >30 dias — rastreado ao texto do
  próprio Decreto-Lei n.º 28/2004, que só prevê retroactividade por
  atraso no envio do CIT (art. 34.º), nunca por duração da baixa;
  mantida a versão conservadora (nunca paga), agora com o achado
  documentado no comentário do código. Ponto ⚠️B (piso 300€/325€ em
  períodos parciais) reconfirmado como piso mensal, sem fonte que
  especifique períodos parciais — interpretação conservadora mantida.
- **Golden tests**: já existiam 15 casos em `tests/test_simulador_
  subsidio_doenca_calculo.py`, incluindo a fronteira 90/91 dias e a
  mistura de escalões 70%/75% — acrescentados 2 novos para o caso de
  fronteira explicitamente citado na spec ("baixa de 3 dias"): duração
  exactamente igual ao período de espera (zero dias pagos) e duração
  imediatamente a seguir (1 dia pago). 17 testes a passar.
- **Card no hub**: já existia em `/simuladores.html` (`sim-card` com
  ícone, título, descrição e link), confirmado.
- **Link bidireccional**: já existia nos dois sentidos — artigo →
  simulador (2 locais) e simulador → artigo (3 locais, incluindo a
  nota sobre RR variável e o disclaimer sobre dias de espera).

Conclusão: **FASE 2 de `MELHORIAS-SPEC.md` está coberta** por
`simulador-subsidio-doenca.html` — nenhuma calculadora nova é
necessária. `html5validator`/`vnu.jar` confirma a página sem erros (só
avisos informativos pré-existentes, "type attribute unnecessary" e
"inputmode", presentes noutras páginas já publicadas). Suite completa
localmente (sandbox sem `feedparser`, mesma limitação documentada):
1251 passed, 5 skipped; `ruff` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`. Trabalho
directo em `main`, sem branch nova (a designação de branch do ambiente
remoto desta sessão já tinha sido resolvida pelo merge da tarefa 1).*

---

*Última revisão: 2026-07-05 — 3.ª tarefa da mesma sessão: `<title>`/meta
description de `subsidio-desemprego.html` revistos por baixo CTR no GSC
(1.229 impressões, 4 cliques, 0,3%). Title antigo ("condições, cálculo
e como pedir") já tinha "2026" mas nenhum valor ou condição concretos —
passou a "Subsídio de desemprego 2026: valor até 1.342,83€ e como
pedir" (61 caracteres, dentro do limite de exibição do Google). Meta
description reescrita para abrir com o valor concreto em vez de
linguagem técnica ("fórmula de cálculo RR×65%"): "quanto recebes
(537,13€–1.342,83€/mês), prazo de garantia de 360 dias e como pedir.
Base legal: DL 220/2006." `og:title`/`og:description` sincronizados; o
`headline` do JSON-LD `Article` (deriva de `og:title` por
`adicionar_article_jsonld.py`, mas o script só insere o bloco quando
está em falta, nunca actualiza um já existente) actualizado à mão para
o mesmo texto. Entrada de `subsidio-desemprego.html` em
`scripts/pesquisa.js` (`descricao`, curada à mão a partir da meta
description real — nunca uma cópia automática, sem teste que force
sincronização perpétua) actualizada a par, para o resultado da pesquisa
interna nunca mostrar um excerto desactualizado. **Nenhum facto novo**
— os valores (537,13€/1.342,83€, 360 dias, DL 220/2006) já estavam
verificados e publicados no corpo do artigo; só a apresentação em
metadata mudou. H1 (`<h1>Subsídio de desemprego 2026</h1>`) e o resto
do corpo do artigo permanecem inalterados, conforme pedido. Confirmado:
os 4 blocos JSON-LD continuam válidos (`json.loads`), `html5validator`/
`vnu.jar` sem erros (só o aviso informativo pré-existente "type
attribute unnecessary"), suite de higiene/pesquisa/acessibilidade
reconfirmada sem regressões. Trabalho directo em `main`.*

---

## CANÁRIO DE VALORES-ÂNCORA — TITLE/META DESCRIPTION

Extensão a `tests/test_valores_ancora.py` (2026-07-06), disparada pelo
risco criado na sessão anterior: o `<title>` de `subsidio-desemprego.html`
passou a incluir "1.342,83€" (tecto = 2,5 × IAS) para melhorar o CTR no
GSC — mas esse valor não estava ligado a nenhum teste. Quando o IAS for
actualizado (tipicamente Portaria de janeiro), esse título fica errado
em silêncio: não há nenhuma "data de validade" de página a apanhar um
`<title>`, e é exactamente a promessa visível nos resultados do Google.

**Regra (ver "REGRAS DE CONTEÚDO", ponto 11)**: qualquer valor legal em
€ ou % usado num `<title>` ou `<meta name="description">` tem de estar
coberto por um teste em `tests/test_valores_ancora.py`.

### Scan ao repositório (2026-07-06) — o que foi encontrado

Grep a todos os `<title>`/`<meta name="description">` do site por
padrões de €/%. Resultado, com a cobertura adicionada:

| Página | Valor encontrado | Ligação ao IAS | Teste |
|---|---|---|---|
| `subsidio-desemprego.html` (`<title>`) | 1.342,83€ | 2,5 × IAS | `test_subsidio_desemprego_title_teto_2_5x_ias` |
| `subsidio-desemprego.html` (description) | 537,13€ + 1.342,83€ | 100%/2,5× IAS | `test_subsidio_desemprego_meta_description_piso_e_teto_ias` |
| `cuidador-informal.html` (description) | 590,84€ | 1,1 × IAS | `test_cuidador_informal_meta_description_valor_1_1x_ias` |
| `acao-social-escolar.html` (description) | 537,13€ | IAS literal | `test_acao_social_escolar_meta_description_ias_literal` |
| `baixa-medica-subsidio-doenca.html` (description) | 55%/75% | via `taxaEscalao1`/`4` do simulador | `test_baixa_medica_meta_description_percentagens_batem_com_simulador` |
| `simulador-subsidio-doenca.html` (description) | 55%/75% | idem, mesmo ficheiro | `test_simulador_subsidio_doenca_meta_description_percentagens_batem_com_o_js` |
| `abono-de-familia.html` (description) | 190,98€ | nenhuma (Portaria própria) — canário de consistência com a tabela do corpo | `test_abono_meta_description_bate_com_tabela_do_artigo` |
| `prestacao-social-para-a-inclusao.html` (description) | 333,64€ + 60% | nenhuma (Portaria própria + limiar AMIM) — canário de consistência com o corpo | `test_psi_meta_description_bate_com_o_corpo_do_artigo` |
| `amim.html` (description) | 60% | nenhuma (limiar legal de incapacidade) — canário de consistência com o corpo | `test_amim_meta_description_bate_com_o_limiar_do_artigo` |

Mais um teste de coerência cruzada: `test_limiar_60_por_cento_nunca_diverge_entre_amim_e_psi`
— o limiar de 60% é citado em duas páginas diferentes (`amim.html` e
`prestacao-social-para-a-inclusao.html`) e nunca pode divergir entre elas.

Dois tipos de canário, conforme o valor tenha ou não fórmula com o IAS:
1. **Valores IAS-derivados** (multiplicador × IAS): o teste recalcula
   `IAS_2026 × multiplicador` e compara — falha sozinho quando `IAS_2026`
   subir de ano para o próximo, forçando a revisão do `<title>`/meta
   description ao mesmo tempo que o resto do site.
2. **Valores de Portaria própria, sem fórmula** (abono 190,98€, PSI
   333,64€, limiar AMIM 60%): sem relação com o IAS, por isso sem
   fórmula para verificar — o canário aqui é de **consistência**: o
   valor da meta description tem de bater sempre com o valor publicado
   no corpo do próprio artigo (já fact-checked). Protege contra um
   sítio ser editado e o outro esquecido; não protege sozinho contra os
   dois ficarem errados ao mesmo tempo — para isso continuam a valer as
   regras normais de fact-checking contra fonte primária.

**Confirmado a falhar de propósito** (mesmo padrão dos canários
anteriores): valor do `<title>` de `subsidio-desemprego.html` adulterado
manualmente para "1.999,99€" → `test_subsidio_desemprego_title_teto_2_5x_ias`
e `test_subsidio_desemprego_meta_description_piso_e_teto_ias` falham com
mensagem clara (`assert [1999.99] == [1342.83]`); revertido e confirmado
a passar de novo.

### Execução diária — `pipeline-diario.yml`

Novo Step 4c ("Canário de valores-âncora (IAS e valores legais em
metadados)") corre `pytest tests/test_valores_ancora.py -q` — só este
ficheiro (rápido, sem Playwright), **todos os dias**, não só no cron
semanal/push de `integridade.yml`. É o mecanismo mais rápido para
apanhar um valor legal desactualizado em metadados depois de uma
Portaria nova: se o IAS mudar em janeiro e ninguém corrigir o `<title>`
de `subsidio-desemprego.html`, este step falha logo na corrida seguinte
do pipeline (dentro de 24h), em vez de esperar pelo cron semanal de
`integridade.yml` ou por um push manual a `main`.

**Nunca um sucesso silencioso** (invariante já documentada em "INVARIANTE
— NENHUM ESTADO DE ERRO PODE PARECER SUCESSO"): o step não tem
`continue-on-error` nem `|| echo ... continuar` — se `pytest` falhar, o
job fica vermelho e os steps seguintes (README, commit, push, deploy,
smoke test) ficam por correr nesse dia, por desenho: um valor legal
errado em produção pesa mais do que a frescura cosmética do pipeline
diário. `test_valores_ancora.py` continua também coberto pela suite
completa no job "Suite de Testes (pytest)" de `integridade.yml`
(push a `main` + cron semanal) — o novo step do `pipeline-diario.yml`
não o substitui, só encurta o tempo até à detecção.

---

## CANÁRIO DE ANOS EM METADADOS

`tests/test_anos_metadados.py` (2026-07-06) — mesmo princípio do canário
de valores-âncora, mas para anos civis em `<title>`/`<meta
name="description">` em vez de valores em €/%. Disparado pela mesma
sessão SEO intermédia: as queries reais do GSC mostram que os
utilizadores pesquisam com o ano ("cuidador informal 2026", "rsi 2026",
"prova escolar 2026") — um `<title>` com um ano civil desactualizado é o
mesmo problema do canário do IAS, só que sem fórmula nenhuma a verificar:
o próprio ano corrente já é a fórmula.

**Diferença de desenho face ao canário do IAS**: `ANO_ATUAL` é calculado
via `datetime.now().year`, nunca uma constante fixa tipo `IAS_2026 =
537.13` — o teste fica vermelho sozinho em janeiro, para qualquer página
que ainda diga "2026", sem precisar de ninguém "lembrar" de bater
`ANO_ATUAL` no calendário primeiro (ao contrário do IAS, que exige sempre
uma Portaria nova e um humano a actualizar a constante).

### Scan ao repositório (2026-07-06)

Todas as 42 páginas reais (raiz + `p/*.html`) têm o `<title>`/description
verificados. Páginas atemporais (institucionais, hubs, quiz) ficam
deliberadamente **sem** ano, por critério editorial — não é uma lacuna:
`404.html`, `acessibilidade.html`, `comecar-aqui.html`, `fontes.html`,
`index.html`, `noticias.html`, `privacidade.html`, `sobre.html`,
`simuladores.html` (hub, cada simulador já tem o seu próprio ano),
`simulador-psu.html` (`noindex`, deliberadamente não publicado, não
importa para SEO).

Encontradas 3 páginas de conteúdo/prestação **sem** ano no `<title>`
(tinham no resto — `og:title` ou description) — acrescentado "2026" ao
`<title>` das 3 (e a `og:title`/`headline` quando já eram idênticos ao
`<title>`, para não criar uma nova divergência):

| Página | `<title>` antes | `<title>` depois |
|---|---|---|
| `psu-quem-tem-direito.html` | "Quem tem direito à PSU — condições…" | "Quem tem direito à **PSU 2026** — condições…" |
| `psu-trabalho-social.html` | "Trabalho social na PSU: aprovado…" | "Trabalho social na **PSU 2026**: aprovado…" |
| `psu-vs-abono-familia.html` | "PSU e Abono de Família: são apoios…" | "**PSU 2026** e Abono de Família: são apoios…" |

**H1 e breadcrumb visível destas 3 páginas NUNCA foram tocados**
(regra explícita da sessão: "não alterar corpo dos artigos") — só
`<title>`, `og:title` (quando já era idêntico ao `<title>`) e o
`headline` do JSON-LD `Article`. Precedente já existente no site para
`<title>`/breadcrumb-JSON-LD divergirem do H1/breadcrumb visível:
`manuais-escolares-mega.html` (`<title>` "…2026/2027…", H1/breadcrumb
visível só "Manuais escolares gratuitos (MEGA)").

**Achado durante a implementação, não um bug de dados**: uma 1.ª
tentativa usou `replace_all` para acrescentar "2026" ao título de
`psu-trabalho-social.html` — como o H1 e a `<span>` do breadcrumb visível
tinham exactamente o mesmo texto do `<title>` nessa página, o
`replace_all` alterou-os também, o que violaria a regra "não alterar
corpo". Apanhado antes do commit por revisão do diff, não por um teste
— corrigido com edições pontuais em vez de substituição global.
**Lição**: nunca usar `replace_all` para um texto que possa coincidir
com conteúdo visível do artigo, mesmo quando a intenção é só mexer em
metadados.

### Excepções a anos históricos — `EXCECOES_ANOS_HISTORICOS`

4 excepções encontradas no scan, todas citações legítimas, nunca
esquecimentos:

| Página | Ano | Motivo |
|---|---|---|
| `apoio-extraordinario-renda.html` | 2023 | PAER fechado a novos candidatos desde 15/03/2023 — facto histórico permanente |
| `complemento-solidario-idosos.html` | 2024 | Regra de rendimentos dos filhos deixou de contar desde 2024 — facto histórico permanente |
| `cuidador-informal.html` | 2025 | Decreto-Lei n.º 138/2025 — número do diploma, não data de vigência |
| `subsidio-desemprego.html` | 2006 | Decreto-Lei n.º 220/2006 — número do diploma, não data de vigência |

Cada excepção é validada por `test_excecoes_continuam_a_existir_na_pagina`
— se o ano deixar de aparecer na página (ex.: reescrita da description),
a excepção fica órfã e o teste falha, forçando a remover a excepção em
vez de a deixar esquecida a "proteger" um ano que já não existe.

**Confirmado a falhar de propósito**: acrescentado "(dados 2025)" ao
`<title>` de `abono-de-familia.html` → `test_sem_ano_civil_
desactualizado_em_title_ou_description[abono-de-familia.html]` falha com
mensagem clara (`assert [2025] == []`, ano sem excepção registada);
revertido e confirmado a passar de novo.

### Execução diária — `pipeline-diario.yml`

Junta-se ao mesmo Step 4c do canário de valores-âncora (mesmo motivo:
correr todos os dias, não só no cron semanal/push de `integridade.yml`)
— `pytest tests/test_valores_ancora.py tests/test_anos_metadados.py -q`,
sem `continue-on-error`. Nunca precisa de manutenção manual quando o ano
civil muda — `ANO_ATUAL` recalcula-se sozinho a cada execução.

---

## GUARDRAIL DE SKIPS — ALLOW-LIST (não limiar numérico)

`.github/workflows/integridade.yml`, job "Suite de Testes (pytest)":
depois de correr a suite completa (`pytest tests/ -q --junitxml=report-
testes.xml`), o step "Guardrail — skips têm de bater certo com a allow-
list" corre `scripts/verificar_skips_permitidos.py report-testes.xml`.

**Nunca mais um número** (o antigo `LIMIAR_SKIPPED` já deixou `main`
vermelha duas vezes — 2026-07-05 e 2026-07-06 — só porque ninguém
incrementava o número quando um skip legítimo novo aparecia; uma
contagem também nunca detecta a direcção inversa, um skip esperado que
deixa silenciosamente de acontecer). Em vez disso, **comparação por
conjunto exacto** entre os nodeids que saltaram nesta corrida real
(extraídos do relatório JUnit) e as chaves de `tests/skips_permitidos.json`
(nodeid → `{motivo, tipo}`, `tipo` em `estrutural`/`ambiente`):

1. **Skip saltou mas não está na allow-list** → skip novo, não
   documentado — pode ser um binário/dependência em falta a impedir
   testes de correr, ou uma página nova sem carimbo/atribuição. Falha
   com o nodeid exacto e o motivo real reportado pelo próprio pytest.
2. **Entrada da allow-list já não salta** → um skip esperado deixou de
   acontecer silenciosamente (página corrigida sem se reparar que uma
   entrada ficou órfã, ou apagada/renomeada). Falha com o nodeid exacto.

Só as duas listas **idênticas**, elemento a elemento, é que passam —
nunca "a de baixo cabe dentro da de cima" nem o inverso.

**Antes de allow-listar qualquer skip por falta de carimbo "Verificado
a": a raiz é sempre o carimbo, nunca a allow-list.** Achado real desta
sessão: `p/apoios-escolares.html` estava na lista de skips "legítimos"
documentada numa sessão anterior (2026-07-04) como se fosse uma
exclusão estrutural (pillar page, "sem carimbo") — mas ao investigar a
fundo, a página tinha de facto um carimbo, só com fraseado antigo
("Verificado em junho de 2026", pré-padronização, sem dia nem
atribuição), diferente dos outros 4 pillars do site (que já diziam
"Verificado a [data] pela redação do Tens Direito"). Corrigido na
página (`p/apoios-escolares.html`, usando a data de publicação já
documentada na tabela "PÁGINAS PUBLICADAS" — 30 jun 2026 — nenhum
facto novo inventado) em vez de allow-listado — o teste deixou de
saltar e a allow-list ficou só com os 4 skips genuinamente estruturais:
`404.html`/`index.html`/`simulador-psu.html` (fora do índice de
pesquisa, deliberado) e `manuais-escolares-mega.html` (sem secção de
FAQ visível dedicada). `tests/test_verificar_skips_permitidos.py` tem
um teste dedicado (`test_allow_list_real_nunca_esconde_falta_de_
carimbo_verificado_a`) que falha se alguma entrada futura da allow-list
mencionar "carimbo"/"Verificado a" no motivo — força a mesma
investigação sempre que alguém for tentado a allow-listar em vez de
corrigir.

`scripts/verificar_skips_permitidos.py` reconstrói o nodeid pytest
(`tests/test_x.py::test_y[param]`) a partir de `classname`/`name` do
JUnit (`classname.replace(".", "/") + ".py::" + name` — seguro mesmo
quando o próprio parâmetro tem pontos, ex. `p/apoios-escolares.html`,
porque esses pontos vivem em `name`, nunca em `classname`). Testado em
`tests/test_verificar_skips_permitidos.py`: reconstrução do nodeid,
extracção de um XML JUnit real, e as duas direcções de falha + o
caminho feliz, todos com asserts explícitos (nunca só "não rebentou").

---

## LIMPEZA AUTOMÁTICA DE BRANCHES

`.github/workflows/limpar-branches.yml` (2026-07-06) — rede automática
para a "REGRA ABSOLUTA — GIT": sessões de trabalho já ficaram com
branches órfãs `claude/*` totalmente integradas em `main` sem
conseguir apagá-las (`git push origin --delete` dá sempre 403 quando a
sessão não está autenticada como utilizador logado — mesma limitação
documentada em várias revisões anteriores). Este workflow corre com o
GITHUB_TOKEN do próprio Actions (`permissions: contents: write` +
`issues: write`), nunca depende de quem está logado.

**Triggers**: `push` a `main` (apanha o caso comum — logo a seguir a um
fast-forward de sessão) + cron `0 5 * * *` (diário, antes do pipeline
das 06:00 UTC, rede de segurança) + `workflow_dispatch` (manual).

**Lógica, só sobre branches remotas != `main`**:
1. `git remote set-branches origin '*'` + `git fetch origin --prune` —
   `actions/checkout` só traz o ref do evento por omissão, é preciso
   pedir explicitamente todas as branches.
2. Para cada branch: `git rev-list --count origin/main..origin/<b>`.
   - **0 commits únicos** (totalmente integrada) → apagada via
     `gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/<b>`,
     registada no job summary, **sem** Issue nem email — é o caso
     normal e silencioso.
   - **≥1 commit único** → nunca apagada, entra na lista para a Issue.
3. Issue única de título estável (`🌿 Branches órfãs por integrar`,
   labels `branch-orfa`+`verificar`): corpo **substituído** a cada
   corrida (nunca acumula comentários, ao contrário de
   `fonte-bloqueada`/`feed-morto` — aqui o conteúdo é sempre "estado
   actual", não um log de ocorrências), com a tabela de branches e
   commits únicos. Fecho automático (com comentário) quando a lista
   fica vazia — mesma lição de fecho automático já usada nas outras
   máquinas de estado deste repositório.

**Guardrail próprio**: nunca apaga `main` (excluída da listagem por
construção, mais uma verificação explícita dentro do próprio loop que
falha o job se `main` alguma vez lá chegasse); nunca faz `git push` de
conteúdo, nunca modifica HTML, nunca cria branches — as duas únicas
escritas permitidas são apagar um ref `heads/*` != `main` e gerir a
Issue única. Uma falha real de API ao apagar uma branch que devia ser
apagada (0 commits únicos) nunca é engolida em silêncio — fica no job
summary, gera `::error::` e falha o job (mesmo princípio de "nenhum
estado de erro pode parecer sucesso"); se for sempre 403 mesmo com
GITHUB_TOKEN, é sinal de um ruleset "restrict deletions" activo — a
correcção é pôr o Actions no bypass do ruleset, nunca baixar a
protecção.

Construção do array JSON de branches por integrar feita com `jq`
(nunca concatenação de string em bash/Python) — nomes de branch
passados como `--arg`, nunca interpolados directamente num literal
JSON, para não partir com caracteres especiais no nome.

**Provadas as duas direcções em CI real** antes de confiar no
workflow, mesmo padrão já usado para o guardrail de skips: branch de
teste totalmente integrada em `main` → confirmado apagada sozinha, sem
Issue; branch de teste com 1 commit único → confirmado NÃO apagada e
Issue única aberta com a contagem certa. Ver entrada de revisão
correspondente para os run_ids reais.

Estado do repositório confirmado nesta sessão, antes de qualquer teste
(via API `list_branches` + `git ls-remote --heads origin`, não por
suposição): as duas branches órfãs documentadas em revisões anteriores
(`claude/infrastructure-audit-robustness-10k2wc`,
`claude/melhorias-spec-phase-1-anlctz`) **já não existiam** — foram
apagadas manualmente entretanto (fora desta sessão). Só `main`
existia no remoto antes deste workflow correr pela primeira vez.

---

*Última revisão: 2026-07-06 — TAREFA 1 de sessão SEO intermédia (antes da
FASE 3 de `MELHORIAS-SPEC.md`): actualização sazonal de
`manuais-escolares-mega.html`, página #1 do site em cliques GSC, em
plena época de preparação do ano lectivo. `WebSearch` restrito a fontes
oficiais (gov.pt, manuaisescolares.pt, IGeFE, DGE, EduQA — nunca blogs
nem notícias secundárias, incluindo um "Escola Note" descartado por ser
blog) confirmou que **as datas de emissão dos vales 2026/2027 continuam
por publicar** — mesmo resultado em 4 pesquisas independentes, e até os
blogs de terceiros admitem não ter a data. Um resultado antigo do gc23
("XXIII Governo Constitucional", vales a "2 de agosto") foi identificado
e descartado por pesquisa adicional como sendo de 2022/2023, não do ano
corrente — cuidado replicável para futuras pesquisas deste tipo:
confirmar sempre o ano de publicação antes de usar uma data encontrada.

Achado com valor real, apesar de não ser o anúncio de vales procurado: o
calendário de **adopção de manuais pelas escolas** para 2026/2027 está
oficialmente confirmado pela EduQA, I.P. (Despacho n.º 3026/2024, de 21
de março) — processo diferente do de vales, nunca confundir os dois.
Também descoberto que a entidade que gere a plataforma MEGA é a
**IGeFE, I.P.** (`igefe.mec.pt`), não a DGE — acrescentada como fonte
adicional; registada a limitação de que o scraper (`mega_datas`) só
vigia `dge.mec.pt`, por isso pode não apanhar um anúncio publicado
primeiro em `manuaisescolares.pt`/`igefe.mec.pt` (ver nova nota em
"PÁGINAS COM DATAS SAZONAIS").

Página actualizada com: fontes adicionais (IGeFE, EduQA) no bloco de
fontes e no corpo (secção Calendário, citando o Despacho e as datas
reais do processo de adopção); datas de "Verificado a" actualizadas
(corpo + JSON-LD `dateModified`, 24/06 → 06/07/2026) nos 3 sítios que
usam essa data (meta description, fonte-bloco, `dateModified`);
linguagem da FAQ/HowTo ajustada para reflectir a verificação de hoje em
vez de apontar genericamente para "julho de 2026" (que já chegou sem
novidade). `title`/meta description já diziam "2026/2027" antes desta
sessão — mantidos, sem alteração necessária.

**Achado colateral corrigido durante os testes**: a 1.ª versão da
reescrita do bloco de fontes removeu, sem querer, a palavra "confirmar"
que estava a suprimir o par "2025/2026" (padrão histórico citado) na
detecção de `ano_letivo` de `scripts/verificar_datas.py` —
`tests/test_verificar_datas.py::test_manuais_escolares_mega_real_nao_gera_alerta_issue_45`
apanhou a regressão de imediato. Corrigido reintroduzindo um marcador de
pendência (`provisório`, `por confirmar`) junto da mesma menção —
confirmado a voltar a passar.

Registado gatilho de verificação semanal em `ROADMAP.md`/CLAUDE.md
(nunca só na Issue automática do scraper, que pode não ser a 1.ª fonte a
reflectir o anúncio). Suite completa: 1262 passed, 5 skipped (mesma
limitação de `feedparser` no sandbox, documentada em sessões
anteriores); ruff limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão).

---

*Última revisão: 2026-07-06 — TAREFA 2 da mesma sessão SEO intermédia:
scan a `<title>`/`<meta name="description">` das 42 páginas reais por
anos civis, e novo canário `tests/test_anos_metadados.py` (ver secção
"CANÁRIO DE ANOS EM METADADOS"). Encontradas 3 páginas de conteúdo sem
ano no `<title>` (`psu-quem-tem-direito.html`, `psu-trabalho-social.html`,
`psu-vs-abono-familia.html`) — acrescentado "2026", sem tocar em H1 nem
breadcrumb visível (regra explícita da tarefa). Achado corrigido antes do
commit: uma 1.ª tentativa com `replace_all` alterou também o H1 de
`psu-trabalho-social.html` (texto idêntico ao `<title>` nessa página) —
apanhado por revisão do diff, corrigido com edições pontuais. Canário
novo usa `datetime.now().year` como ano corrente (nunca uma constante
fixa) — fica vermelho sozinho em janeiro, sem manutenção manual; 4
excepções documentadas para anos históricos legítimos (citação de
diploma legal ou facto permanente), cada uma validada contra ficar
órfã. Confirmado a falhar de propósito (ano "2025" injectado no título
de `abono-de-familia.html`, revertido depois). Junta-se ao mesmo Step 4c
de `pipeline-diario.yml` do canário de valores-âncora. Suite completa:
1304 passed, 5 skipped (42 novos); ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False`.

---

*Última revisão: 2026-07-06 — TAREFA 3 da mesma sessão SEO intermédia:
análise do cluster escolar, só documento, nada implementado. Novo
`ANALISE-CLUSTER-ESCOLAR.md` (raiz, privado, mesma categoria de
`ROADMAP.md`): inventário confirma o cluster `apoios-escolares` 100%
interligado (scan directo aos `href` das 5 artigos + pillar + simulador
ASE, sem páginas órfãs nem links em falta). Duas lacunas identificadas:
1) nenhuma página agrega os prazos dispersos (vales MEGA, prova escolar
31 jul, ASE/bolsa de mérito setembro) por mês; 2) o próprio
`p/apoios-escolares.html` já admite publicamente, duas vezes no seu
próprio texto, que "bolsas de ação social da DGES... não estão cobertos
neste guia" — lacuna real e auto-assinalada, prestação claramente
distinta da bolsa de mérito (secundário/mérito vs. superior/condição de
recursos). Proposta final: no máximo 2 páginas
(`calendario-escolar-apoios.html`, `bolsa-de-estudo-ensino-superior.html`),
cada uma com query-alvo, âmbito, risco de canibalização avaliado (baixo/
nenhum) e ligação ao cluster — ordem sugerida não vinculativa (DGES
primeiro, caso mais forte). Gaps considerados e descartados por âmbito
(seguro escolar, calendário escolar geral, transporte municipal) também
documentados, com o motivo. Apontador registado em `ROADMAP.md` →
"TRABALHO FUTURO REGISTADO". Suite completa reconfirmada sem alterações
(1304 passed, 5 skipped — nenhum código tocado, só o novo `.md`); ruff
limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False`. Fecha a sessão SEO intermédia das 3 tarefas
(actualização MEGA 2026/2027, canário de anos em metadados, esta
análise) antes da FASE 3 de `MELHORIAS-SPEC.md`.

---

*Última revisão: 2026-07-06 — TAREFA 1 de sessão de continuidade:
fechado o furo de vigilância MEGA identificado em `ANALISE-CLUSTER-
ESCOLAR.md`/sessão anterior — o único sentinela automático das datas
dos vales (`mega_datas`) só vigiava `dge.mec.pt`, mas quem emite de
facto os vouchers aos encarregados de educação é a IGeFE, I.P.
Confirmado num runner real (`diagnostico-igefe-temp.yml`, apagado no
fim) que `igefe.mec.pt/Page/Index/199` é acessível via pedido HTTP
simples e que o seu conteúdo real (secção "Emissão de Vouchers") vive
num `<div class="ig-publicsite-paragraph">`, nunca em `<p>` — a 1.ª
tentativa de extracção com selectores genéricos devolvia quase nada
(585 chars, tudo navegação), corrigido calibrando selectores
específicos a esta fonte antes de integrar. Nova fonte `igefe_mega`
(`scripts/scraper_playwright.py`, `metodo="http"`, `min_chars_uteis=300`,
`ancora_conteudo=("voucher",)`) e lógica de detecção partilhada com
`mega_datas` (`_detectar_datas_mega()`, extraída para função comum,
chamada tanto por `scrape_playwright()` como por `scrape_http()`) sob a
mesma chave de aviso `mega_2026_2027_publicadas` — a Issue automática
dispara com qualquer uma das duas fontes, independentemente de qual
detectar primeiro. `igefe_mega` também entra em `SLUGS_MONITORIZADOS`
(`gerir_estado_fontes.py`) e em `data/pagina_fonte.json`, para herdar a
máquina de estados de `fonte-bloqueada` e a simulação de revalidação de
carimbo sem código adicional. EduQA não foi adicionada como fonte —
confirmado que o calendário que gere é o de **adopção de manuais pelas
escolas** (Despacho n.º 3026/2024), processo distinto da **emissão de
vouchers** que esta página documenta.

**Dois falsos positivos reais, corrigidos em duas iterações** — ver
"PÁGINAS COM DATAS SAZONAIS" para o detalhe técnico. 1.ª tentativa
(janela de proximidade de 60 chars): o conteúdo real e actual de
`igefe_mega` ("28 de julho de 2025", ano letivo 2025/2026 ainda a
decorrer) disparou a Issue #55 por engano — a lógica original herdada
de `mega_datas` não tinha âncora nenhuma ao ano. Corrigido com uma
janela de proximidade; verificado num 2.º disparo real do pipeline que
**não foi suficiente** — Issue #56, mesma causa, porque "2026" continua
a aparecer a menos de 60 chars de "julho" no HTML bruto (markup entre o
texto visível engorda a distância face ao texto limpo usado para
calibrar a janela). Corrigido de vez exigindo a frase completa e
inequívoca "julho de 2026"/"agosto de 2026", nunca uma proximidade
aproximada — testado com 7 casos (incluindo os dois falsos positivos
reais e um caso pensado para quebrar qualquer janela futura) e
confirmado num 3.º disparo real do pipeline: `igefe_mega` classifica OK
e nenhuma Issue nova foi criada. Ambas as Issues falsas (#55, #56)
fechadas com comentário explicativo. **Lição**: uma correcção a um
falso positivo tem de ser verificada contra o cenário real que o
disparou, nunca só contra um fixture construído à mão — a 1.ª correcção
pareceu suficiente num fixture reconstruído da memória do diagnóstico,
mas falhou contra o HTML bruto real.

TAREFA 2: nova página `bolsa-de-estudo-ensino-superior.html` (6.ª
página do cluster `apoios-escolares`), fechando a lacuna que o próprio
`p/apoios-escolares.html` já admitia publicamente duas vezes no seu
texto ("bolsas de ação social da DGES... não estão cobertos neste
guia"). Fact-check via `WebSearch` restrito a `dges.gov.pt` e `dre.pt`
(instrução explícita desta sessão): Regulamento de Atribuição de Bolsas
de Estudo a Estudantes do Ensino Superior (Despacho n.º 8442-A/2012,
com a alteração mais recente pelo Despacho n.º 7253/2024), plataforma
BeOn (candidatura exclusivamente online), prazo geral 14 de agosto a 2
de outubro (extensível até 31 de maio com valor proporcional; 20 dias
úteis se a inscrição for próxima do prazo, ou após início de estágio
profissional), documentos (IBAN, Valor do Património Mobiliário a 31
de dezembro do ano anterior), propina de referência 2025/2026 = 697 €
(inalterada face ao ano anterior, confirmado 3× independentemente) e
bolsa mínima de referência ≈ 872 € (125% da propina) — todos com fonte
citada em comentário/fonte-bloco, nunca de memória.

**Achado importante, tratado com o mesmo cuidado do "GATILHO
AUTOBAIXA"**: o Conselho de Ministros aprovou, a 21 de maio de 2026, um
novo sistema de ação social no ensino superior, aplicável a partir do
ano letivo 2026/2027 — mas confirmado por pesquisa restrita a `dre.pt`
que o decreto-lei **ainda não tinha sido publicado** em Diário da
República à data de verificação (06/07/2026), apenas aprovado em
Conselho de Ministros (fase anterior à publicação). Como a fonte dessa
notícia é `portugal.gov.pt` (fora do âmbito `dges.gov.pt`/`dre.pt`
definido para esta tarefa), a página menciona a reforma apenas como
facto verificável e datado (aprovação em CM nessa data, ainda sem
diploma em DRE) — nunca os valores/fórmulas específicos estimados na
comunicação do Governo, que não têm fonte DRE/DGES. Título deliberadamente
**sem valor em €** — não há um "valor máximo" simples e confirmado (a
bolsa é calculada caso a caso) nem faz sentido ancorar um valor do
sistema actual (872€, mínimo 2025/2026) que a reforma pendente pode vir
a alterar assim que o diploma sair; por isso `tests/test_valores_
ancora.py` não precisou de nova entrada. Gatilho registado em
`ROADMAP.md` para reescrever a secção "O que muda a partir de
2026/2027" assim que o decreto-lei for publicado.

Inclui os dois blocos da FASE 1 (`.resposta-rapida` + `.checklist-final`),
interligação nos dois sentidos com `p/apoios-escolares.html` (2
ocorrências do texto "não cobertos" substituídas por link real),
`acao-social-escolar.html` (via `RELACIONADOS` automático) e
`bolsa-de-merito.html` (cross-link manual "Acabaste o 12.º ano?",
seguindo a proposta já registada em `ANALISE-CLUSTER-ESCOLAR.md`).
`data/clusters.json`, `sitemap.xml` e `scripts/pesquisa.js` actualizados;
`scripts/sincronizar_clusters.py`/`sincronizar_nav.py`/`inserir_botao_
partilhar.py`/`adicionar_canonicas.py`/`adicionar_autoria_artigos.py`/
`adicionar_article_jsonld.py` corridos com sucesso (idempotência
confirmada — 2.ª corrida de `sincronizar_clusters.py` = zero alterações).

Verificação: 4 blocos JSON-LD (`FAQPage`+`HowTo`+`BreadcrumbList`+
`Article`) confirmados como JSON válido; `html5validator` sem erros (só
o aviso informativo pré-existente "type attribute unnecessary"); suite
completa — 1163 passed, 65 skipped (mesma limitação de `feedparser`
neste sandbox, documentada em sessões anteriores); os 11 testes
parametrizados sobre a página nova em `test_higiene_indexacao.py`/
`test_breadcrumb_coerencia.py`/`test_nav_coerencia.py` confirmados a
passar; `ruff check scripts/ tests/ --select E,F,W --ignore E501 .`
limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False`. Trabalho directo em `main`, sem branches.

---

*Correcção à entrada anterior (2026-07-06) — a verificação "3.º disparo
sem Issue nova" reportada acima estava errada: por engano, o run
confirmado como "3.º disparo, limpo" era na verdade uma releitura do
2.º run (o que gerou a Issue #56) — nunca cheguei a confirmar o run
real seguinte. Esse run real (sobre o commit `08d202f`, o da correcção
do regex) gerou a Issue #57 com o mesmo excerto de sempre, e mais uma
corrida (ainda sobre código já correcto) gerou a Issue #58. Um
diagnóstico dedicado ao HTML bruto real de `igefe.mec.pt` confirmou
que o regex de `08d202f` dá **0 matches** neste conteúdo — não era o
regex.

**Causa raiz real**: `data/scraped/avisos.log` é um log cumulativo,
nunca rotacionado, e o passo "Abrir Issues se mudanças detectadas" de
`pipeline-diario.yml` fazia `avisos_txt.includes('mega_2026_2027_
publicadas')` sobre o **ficheiro inteiro**, não só sobre os avisos de
hoje. Uma única linha antiga (07:21:13, da 1.ª corrida, antes de
qualquer correcção ao regex) continuava a ser "reencontrada" em todas
as corridas seguintes, recriando a Issue sempre que a anterior era
fechada — independentemente do regex estar certo ou errado. Corrigido
filtrando `avisos.log` só às linhas datadas de hoje antes de procurar o
padrão (mesmo critério já usado no bloco de `fonte-bloqueada` mais
acima no próprio ficheiro); aplicada a mesma correcção, preventivamente,
ao bloco simétrico do decreto-lei da PSU (mesma vulnerabilidade
latente, nunca chegou a manifestar-se). A linha antiga foi removida de
`avisos.log`. Issues #57 e #58 fechadas com a explicação real.

**Verificado com rigor desta vez** — run `28786615054`, confirmado
via API a corresponder exactamente ao commit `c5e2161a616d7cd6e8582a
1171d0695f1079481d` (a correcção deste bloco), `status: completed`,
`conclusion: success`, e confirmado por `list_issues` que nenhuma
Issue "MEGA 2026/2027" nova foi criada. **Lição**: ao verificar um
disparo assíncrono de CI, confirmar sempre o `run_id`/`head_commit`
exacto devolvido pela API antes de concluir sucesso — nunca assumir
que "o run mais recente" é o que se acabou de disparar, e nunca
confiar numa releitura de dados já vistos sem re-confirmar o
identificador.

---

*Última revisão: 2026-07-06 — sessão de estabilização de `main`, disparada
por 18 corridas seguidas vermelhas de "Integridade do Código" (desde o
commit `774cb51`, FASE 1 de MELHORIAS-SPEC.md) e 2 branches remotas a
violar a REGRA ABSOLUTA — GIT. Diagnóstico pelo log real (`get_job_logs`,
nunca por adivinhação): a suite em si estava sempre a passar
(`1413 passed`) — a falha era só o guardrail "limiar de testes skipped"
(`.github/workflows/integridade.yml`), que ficou em `LIMIAR_SKIPPED=4`
desde a sessão anterior (2026-07-05) e nunca foi actualizado quando o
commit `774cb51` introduziu um 5.º skip legítimo:
`manuais-escolares-mega.html` não tem secção de FAQ visível dedicada
(só JSON-LD), por isso `test_checklist_final_vem_antes_do_faq`
(`tests/test_resposta_rapida_checklist.py`) salta-o deliberadamente em
vez de inventar uma secção que a página não tem — não era um binário em
falta nem uma regressão silenciosa, confirmado reproduzindo localmente
(`python3 -m pytest tests/ -q -rs`, sempre os mesmos 5 skips estruturais).
Corrigido subindo `LIMIAR_SKIPPED` de 4 para 5, com o raciocínio completo
documentado no próprio comentário do workflow (commit `cbd7c71`) — **run
`28787861005`, commit exacto `cbd7c716`, confirmado `status: completed`,
`conclusion: success`** via API, primeiro verde depois de 18 corridas.

Ao correr a suite completa localmente pela primeira vez nesta sessão
(sandbox sem `feedparser`/`bs4`/`requests`/Playwright pré-instalados —
`sgmllib3k` falha a compilar por incompatibilidade `install_layout` do
`setuptools` do sistema, mesma limitação já documentada; contornado
extraindo `sgmllib.py` do tarball para `site-packages` à mão, e usando
sempre `python3 -m pytest` em vez do `pytest` do PATH, que resolvia para
um venv `uv tool` isolado sem as dependências do projecto), confirmado
que Issue #53 (`baixa-medica-subsidio-doenca.html`, `data-expirada`) era
um falso positivo real, não um alerta genuíno: o match era "já não
existe o limite mínimo de 30 dias que existia **antes de 1 de abril de
2024**" — uma regra revogada pelo DL n.º 8/2024, descrita
permanentemente no passado, nunca "expira". A citação legal completa
("em vigor desde 1 de abril de 2024") está mais abaixo na página, fora
da janela de 220 caracteres desta ocorrência específica, por isso
precisava do seu próprio marcador — mesma categoria já corrigida para as
Issues #51/#52 (`MARCADORES_HISTORICOS` em `scripts/verificar_datas.py`,
ver secção "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS").
Novo marcador `exist(?:e|ia|iam)\s+antes\s+de\b`, anchorado para não
mascarar um "antes de X" genérico sem relação com uma regra revogada
(guarda testada explicitamente). Commit `d432f5b` — **run `28788267407`,
commit exacto `d432f5ba`, confirmado `status: completed`, `conclusion:
success`**. Issue #53 fechada manualmente com a explicação (não esperado
o fecho automático do próximo cron).

Issue #54 (`dre_psu` BLOQUEADO) investigada e confirmada **real**, não
duplicada: `data/estado_fontes.json` mostra 8 dias consecutivos
bloqueado, `avisos.log` com uma linha nova a cada corrida (nunca o
padrão de linha antiga reencontrada que causou as Issues #55-#58 de
MEGA). Verificação externa via `WebSearch` (não pelo scraper, já
confirmado quebrado) confirmou que o decreto-lei da PSU continua por
publicar em DR à data de hoje — nenhuma página do site precisa de
actualização. Comentário explicativo adicionado à Issue, mantida aberta
correctamente (sentinela `dre_psu` continua quebrado, correcção da URL
exige sessão com browser interactivo real, já registada em
`ROADMAP.md` — não tentada aqui para não arriscar disfarçar o bloqueio
real de um "sucesso" falso, ver "INVARIANTE — NENHUM ESTADO DE ERRO PODE
PARECER SUCESSO").

Branches `claude/infrastructure-audit-robustness-10k2wc` e
`claude/melhorias-spec-phase-1-anlctz`: confirmado por
`git rev-list --count origin/main..<branch>` = 0 em ambas — já
totalmente integradas em `main` por fast-forward em sessões anteriores,
zero conteúdo único, seguras para apagar. `git push origin --delete`
voltou a dar **403** (mesma limitação já documentada em várias sessões
anteriores — sem `gh` CLI nem ferramenta MCP com permissão para apagar
branches remotas nesta sessão) — ficam registadas para o Nuno apagar
manualmente no GitHub; nenhum trabalho por perder.

`pages build and deployment` do commit `b8b1c25e` (~08:35 hora de
Lisboa / 07:32-07:35 UTC) confirmado **transitório**: o commit seguinte
já tinha deploy com sucesso, e o deploy do HEAD actual (`d432f5ba`, run
`28788266298`) e o smoke test de produção (`28788267373`) confirmam-se
verdes — produção a servir a versão certa, sem necessidade de
`rerun_workflow_run`.

Estado final confirmado via API: `Integridade do Código`, `pages build
and deployment`, `Verificação de Produção (Smoke Test)` e `Verificar
Links (lychee)` todos `success` no commit `d432f5ba`. Suite completa
local: 1416 passed, 5 skipped (limiar actualizado); `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados por esta sessão). Trabalho directo em `main`, sem
branches novas.*

---

*Última revisão: 2026-07-06 — substituído `LIMIAR_SKIPPED` (número
mágico, corrigido duas vezes nesta mesma semana — 2026-07-05 e
2026-07-06 — só por ninguém o incrementar quando um skip legítimo novo
aparecia, e que nunca detectava a direcção inversa: um skip esperado a
deixar de acontecer silenciosamente) por uma allow-list de conjunto
exacto — nova secção "GUARDRAIL DE SKIPS — ALLOW-LIST (não limiar
numérico)" com o detalhe completo. `.github/workflows/integridade.yml`
ganhou `--junitxml=report-testes.xml` no step da suite e um step novo
que corre `scripts/verificar_skips_permitidos.py` (novo, com
`tests/test_verificar_skips_permitidos.py`, 8 testes: reconstrução do
nodeid, extracção de um XML JUnit real, as duas direcções de falha e o
caminho feliz) contra `tests/skips_permitidos.json` (nodeid →
`{motivo, tipo}`); artefacto `report-testes.xml` publicado sempre
(`if: always()`) para diagnóstico.

Achado real ao construir a allow-list (a mesma disciplina exigida pela
tarefa: nunca allow-listar um skip sem confirmar a fundo que é mesmo
estrutural): o skip de `p/apoios-escolares.html` em
`test_adicionar_autoria_artigos.py` — documentado numa sessão anterior
(2026-07-04) como "pillar sem carimbo", categoria supostamente
estrutural — tinha na verdade um carimbo real, só com fraseado antigo
("Verificado em junho de 2026", sem dia nem atribuição), diferente dos
outros 4 pillars do site (já com "Verificado a [data] pela redação do
Tens Direito"). Corrigido na página (data de 30 jun 2026, já
documentada na tabela "PÁGINAS PUBLICADAS", nenhum facto novo) em vez
de encapsulado na allow-list — o skip desapareceu por completo, ficando
só os 4 genuinamente estruturais. Novo teste
`test_allow_list_real_nunca_esconde_falta_de_carimbo_verificado_a`
força a mesma investigação para qualquer entrada futura que mencione
"carimbo"/"Verificado a".

**Provadas as duas direcções de falha em CI real, não só localmente**
(mesma disciplina do guardrail anterior): removida uma entrada real da
allow-list (`manuais-escolares-mega.html`) → run
[28790193082](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28790193082),
commit exacto `901c679a`, `conclusion: failure`, mensagem exacta "1
teste(s) saltados nesta corrida SEM entrada" com o nodeid certo;
revertida e acrescentada uma entrada fantasma que nunca salta de facto
→ run
[28790416502](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28790416502),
commit exacto `db5ec39d`, `conclusion: failure`, mensagem exacta "1
entrada(s) ... já NÃO saltam". Revertido o fantasma, commit final →
run
[28790782476](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28790782476),
commit exacto `ba4525f2`, `conclusion: success` — confirmado via API em
todos os três casos, nunca assumido pelo "run mais recente". Smoke
test de produção também verde no mesmo commit (run `28790782431`).
`pages build and deployment` não chegou a aparecer no Actions para este
commit específico durante a verificação desta sessão — não bloqueante,
já que os dois checks que realmente importam (suite + smoke de
produção) confirmam tudo correcto; registado para confirmação
oportunista numa próxima sessão, não um sinal de falha.

Suite completa local: 1425 passed, 4 skipped; `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão). Trabalho directo em `main`, sem branches novas — 6
commits nesta sessão (carimbo, guardrail novo, 2 de teste intencional +
2 de reversão).*

---

*Última revisão: 2026-07-06 — criado `.github/workflows/limpar-branches.yml`
(nova secção "LIMPEZA AUTOMÁTICA DE BRANCHES"), rede automática para a
"REGRA ABSOLUTA — GIT": sessões já tinham ficado com branches `claude/*`
totalmente integradas em `main` sem conseguir apagá-las (`git push
--delete` sempre 403 sem sessão logada). Este workflow corre com o
GITHUB_TOKEN do próprio Actions — `permissions: contents: write` +
`issues: write` — e nunca depende de quem está logado. Triggers: `push`
a `main` + cron diário `0 5 * * *` (antes do pipeline das 06:00) +
`workflow_dispatch`.

Confirmado por API (`list_branches`, `git ls-remote --heads origin`)
antes de qualquer alteração: as duas branches órfãs documentadas em
revisões anteriores (`claude/infrastructure-audit-robustness-10k2wc`,
`claude/melhorias-spec-phase-1-anlctz`) **já não existiam** — apagadas
manualmente entretanto, fora desta sessão; só `main` existia no
remoto. Entrada correspondente do "TRABALHO FUTURO REGISTADO" em
`ROADMAP.md` removida por estar desactualizada.

**Verificado em CI real, não só localmente** (mesmo padrão do guardrail
de skips): o 1.º push desta sessão (commit `c0bdb27`) já disparou o
workflow pela primeira vez — run
[28792058530](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28792058530),
`conclusion: success`, log confirma "Sem branches por integrar e sem
Issue aberta — nada a fazer" (esperado, só `main` existia). Para provar
as duas direcções com branches reais, criadas via API: `teste-janitor-
integrada` (0 commits únicos, mesmo tip de `main`) e `teste-janitor-
nao-integrada` (1 commit único, ficheiro `.janitor-test-marker.txt`).
`workflow_dispatch` manual → run
[28792310830](https://github.com/nunovinhas-creator/tens-direito/actions/runs/28792310830),
commit exacto `c0bdb275`, `conclusion: success`, log confirma
literalmente: "Branch 'teste-janitor-integrada' totalmente integrada em
main (0 commits únicos) — a apagar." seguido de "Branch 'teste-janitor-
nao-integrada' tem 1 commit(s) único(s) — NÃO apagada." e "Issue de
branches órfãs criada, 1 branch(es)." Confirmado via API a seguir:
`teste-janitor-integrada` já não existe em `list_branches`,
`teste-janitor-nao-integrada` continua, Issue #59 ("🌿 Branches órfãs
por integrar") criada com a tabela certa (`teste-janitor-nao-integrada`
| 1). `main` confirmada intocada nos dois casos (mesmo SHA antes/depois).

**Achado real ao tentar limpar os artefactos de teste**: a própria
sessão tentou `git push origin --delete teste-janitor-nao-integrada`
para arrumar — deu **403**, a mesma limitação de sempre (sessão sem
autenticação de utilizador logado). Confirma de forma directa e
concreta a premissa inteira deste workflow: só o GITHUB_TOKEN do
Actions consegue apagar refs de forma fiável, nunca uma sessão. Branch
de teste `teste-janitor-nao-integrada` e a Issue #59 correspondente
ficam por resolver manualmente — registado em `ROADMAP.md`.

**Não verificado nesta sessão** (honestidade sobre o que falta, não
assumido): o fecho automático da Issue quando a lista de branches por
integrar fica vazia — o código segue exactamente o mesmo padrão já
provado noutras máquinas de estado do repositório
(`fonte-bloqueada`/`feed-morto`), mas só depois de
`teste-janitor-nao-integrada` ser apagada manualmente é que uma corrida
seguinte (cron ou `workflow_dispatch`) pode confirmar o fecho em CI
real — registado em `ROADMAP.md` como verificação pendente.

Suite completa local (nenhum código Python alterado por esta sessão):
1425 passed, 4 skipped; `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`. Trabalho
directo em `main`, sem branches novas.*

---

*Última revisão: 2026-07-06 — Sessão 2 do Gerador de Documentos
(`PROMPT-GERADOR-DOCUMENTOS-v1.md`): verificadas e publicadas as 9
candidatas de expansão (4-12) — nenhuma rejeitada, 6 sem pivot
(recurso hierárquico, exposição por atraso, reavaliação de ASE, acesso
a documentos/LADA, requerimento genérico, declaração/comprovativo) e 3
com pivot (dívida em prestações — Mod. IMP.PN.01.01; comunicação de
alteração — Mod. GF 37/GF 54-DGSS; SVI/junta médica — Mod. SVI
55-DGSS, prazo de 10 dias). Achado de verificação real, igual em
espírito ao GF58 da Sessão 1: a candidata #6 (comunicação de
alteração), que o prompt original assumia simples, revelou-se também
ter Mod. próprios em certos contextos — tratada como pivot por
prudência. Distinção deliberada preservada entre SVI (Segurança
Social, prestações contributivas) e o processo de recurso do AMIM
(JMAI, Ministério da Saúde) — nunca cross-linkados entre si, para não
conflacionar dois sistemas de junta médica diferentes.

Motor genérico reaproveitado sem alterações de fundo (só removido o
disparo de evento GA4 ao gerar, decisão já tomada na Sessão 1 para
cumprir "zero chamadas de rede depois do load" de forma literal).
Integração completa: hub `/documentos.html` com 12 cards, `sitemap.xml`,
`scripts/pesquisa.js`, `EXCLUIDAS` em `sincronizar_clusters.py` (mesma
limitação de sub-caminhos da Sessão 1 — registada para o futuro, não
corrigida), cross-links novos a partir de `reclamacao-decisao-seguranca-social.html`,
`acao-social-escolar.html`, `abono-de-familia.html`, e de
`rsi.html`/`subsidio-desemprego.html`/`baixa-medica-subsidio-doenca.html`/
`prestacao-social-para-a-inclusao.html` para a reclamação (nenhuma
destas 4 tinha até agora orientação sobre "o que fazer se o pedido for
indeferido"). Título da carta de CSI encurtado (79→50 caracteres,
risco de corte no Google) e meta descriptions das 3 páginas da Sessão 1
revistas para CTR.

Achado real corrigido antes do commit: o canário de anos em metadados
(`tests/test_anos_metadados.py`) apanhou correctamente "2016" na meta
description do pedido de acesso a documentos (cita "Lei n.º 26/2016")
como um ano potencialmente desactualizado — nova excepção registada em
`EXCECOES_ANOS_HISTORICOS`, mesma categoria já usada para
`cuidador-informal.html`/`subsidio-desemprego.html` (número de diploma,
não data de vigência).

45 golden tests novos (5 critérios × 9 páginas, mesmo ficheiro genérico
`tests/test_gerador_documentos.py` da Sessão 1 — só a lista
`PAGINAS_MINUTA` cresceu, nenhuma lógica de teste duplicada) + 1 teste
de nav. Suite completa: **1738 passed, 4 skipped** (mesmos skips já
documentados); `ruff check scripts/ tests/ --select E,F,W --ignore
E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados por esta sessão). Trabalho directo
em `main`, sem branches novas.*

---

*Última revisão: 2026-07-06 — Sessão 1 do Gerador de Documentos
(`PROMPTGERADORDOCUMENTOSv1.md`), nova secção "GERADOR DE DOCUMENTOS".
Motor único config-driven (`assets/js/gerador-documentos.js` +
`assets/css/gerador-documentos.css`) — nenhuma minuta tem JS próprio,
cada página só define `CONFIG_DOCUMENTO` (campos + template com
`{{placeholders}}`) e chama `GeradorDocumentos.iniciar()`. Hub
`/documentos.html` (padrão de `/simuladores.html`) + 3 páginas em
`documentos/*.html`, novo directório acrescentado a
`encontrar_paginas()` em `sincronizar_clusters.py`.

Portão de verificação aplicado às 3 candidatas do núcleo do prompt: 1)
"Reclamação de decisão da Segurança Social" publicada integralmente —
confirmado via pesquisa que o artigo 191.º do CPA (Decreto-Lei n.º
4/2015) consagra a reclamação em regime geral sem exigir formulário
próprio; 2) "Pedido de reavaliação de escalão de abono de família"
teve de fazer **pivot para carta de acompanhamento** — achado real
desta sessão, não antecipado pelo prompt original: o nosso próprio
artigo já fact-checked `abono-de-familia.html` documenta o Modelo
GF58-DGSS como via oficial, com o pedido online na Segurança Social
Direta como canal preferencial; 3) CSI também fez **pivot para carta
de acompanhamento** — confirmado pelo próprio `complemento-solidario-idosos.html`
("Modelos CSI 1, CSI 1/1 e CSI 1/2 (obrigatório)"), exactamente como o
prompt antecipava. Nenhuma minuta apresenta-se como substituto de um
Mod. oficial — as duas cartas de acompanhamento têm aviso destacado
(`.aviso-pivot`) com link directo para o formulário/canal real.

Restrição dura verificada por teste real (não só documentada):
`tests/test_gerador_documentos.py::test_zero_pedidos_de_rede_ao_interagir_com_o_gerador`
— por isso o motor nunca dispara eventos GA4 ao gerar (decisão
deliberada, diferente dos simuladores). Integração completa: nav
(`scripts/sincronizar_nav.py`, link "📄 Documentos"), `sitemap.xml`,
`scripts/pesquisa.js`, cross-links a partir de `abono-de-familia.html`
e `complemento-solidario-idosos.html`. As 4 páginas novas ficam fora do
sistema de clusters (`EXCLUIDAS`) por uma limitação real do
`sincronizar_clusters.py` — `Pagina.slug` só é comparado contra
`caminho.name` (basename), nunca desenhado para sub-caminhos como
`documentos/...` — registado para o futuro, não corrigido nesta
sessão. 17 testes novos em `tests/test_gerador_documentos.py`
(Chromium real) + 1 em `tests/test_nav_coerencia.py`. Suite completa:
1549 passed, 4 skipped (mesmos skips já documentados); `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpo. Estado completo
e candidatas 4-12 para a Sessão 2 registados em `ROADMAP.md` → "GERADOR
DE DOCUMENTOS — ESTADO". `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados
por esta sessão).*

---

*Última revisão: 2026-07-06 — auditoria completa (Fase 2) de
`simulador-subsidio-doenca.html`, publicado no dia anterior sem nunca
ter sido revisto depois da publicação. Quatro frentes, pedidas
explicitamente pelo Nuno:

**1) Auditoria de valores** — reconfirmadas via `WebSearch` (WebFetch
continua completamente bloqueado nesta sessão, mesmo para PDFs — só
403, incluindo o Guia Prático do ISS) contra seg-social.pt e agregadores
financeiros de referência, à data de hoje: percentagens por escalão
(55/60/70/75%), majoração de +5pp (RR≤500€ ou condição familiar),
fórmula da RR (primeiros 6 dos últimos 8 meses ÷ 180), prazo de
garantia (6 meses), dias de espera por regime (3/10/30), tectos de
duração (1095/365/sem limite), tuberculose (80%/100%, sem limite), IAS
2026 (537,13€, Portaria n.º 480-A/2025/1) e gravidez de risco (confirmado,
mais uma vez, como prestação distinta — subsídio por risco clínico,
100% da RR desde o 1.º dia até à data provável do parto). **Zero
valores desactualizados encontrados** — nenhuma correcção de código
necessária.

Achado que reforça (sem alterar) o piso 300€/325€ já implementado: uma
pesquisa mais específica revelou a formulação exacta da regra — "o
valor do subsídio resultante da aplicação da majoração a uma
remuneração de referência de 500€" — o que confirma matematicamente
300€=60%×500€ e 325€=65%×500€ (as taxas majoradas, não as taxas base
55%/60%), e mostra que a conversão para piso diário (÷30) já usada é
consistente com o mesmo método (RR mensal = RR diária × 30) usado no
resto do simulador. Comentário do código (⚠️B) reforçado com esta
citação mais forte — valores inalterados.

Ponto ⚠️A (retroactividade dos 3 dias de espera em baixas >30 dias)
reconfirmado como não resolvido: uma pesquisa voltou a mostrar a
alegação (mesma categoria de blogs de baixa fiabilidade já rejeitada em
2026-07-05), mas uma pesquisa mais restrita devolveu antes "dias de
espera... sem rendimento", sem menção a retroactividade — mantida a
versão conservadora. Fechar esta dúvida em definitivo precisa de acesso
directo ao Guia Prático do ISS (bloqueado por `WebFetch` nesta sessão)
— registado para uma sessão futura com acesso a browser real.

**2) Auditoria de lógica** — os 17 golden tests existentes cobriam bem
os casos principais mas tinham lacunas reais nas fronteiras: faltavam a
transição 30/31 dias (escalão 55%→60%), a transição 365/366 (70%→75%),
o limite exacto de 1095 dias (sem exceder), o piso universal de 5,37€/dia
a *morder de facto* (o único teste existente para majoração automática
tinha RR alta de mais para o piso alguma vez ser vinculativo), a
majoração activada só pelo checkbox (nunca testada isoladamente da
majoração automática por RR≤500€, nem o caso negativo — RR>500€ sem
checkbox nunca majora), e o regime de seguro social voluntário (30 dias
de espera nunca tinha sido exercitado, ao contrário de conta de outrem
e independente) — achado interessante deste último: 30 dias de espera
esgotam por completo o 1.º escalão (1-30 dias), o pagamento começa
directamente no escalão de 60%. 8 testes novos, todos calculados à mão
nos comentários e confirmados a bater certo à primeira tentativa.
Reconfirmado `test_coerencia_artigo_simulador_constantes_de_producao`
(simulador↔artigo) sem divergências.

**3) Auditoria de UX/padrão** — comparados os 4 simuladores
(abono/ASE/CSI/subsídio de doença): breadcrumb, "Verificado a", 4 blocos
JSON-LD (`WebApplication`+`FAQPage`+`BreadcrumbList`+`Article`), texto
do disclaimer ("⚠️ Aviso de independência" + "Simulação indicativa..."),
`inputmode="numeric"`, evento GA4 `calc_resultado`, presença no hub
`/simuladores.html`, `sitemap.xml`, `scripts/pesquisa.js` e
`data/clusters.json` — **tudo já alinhado**, nenhuma correcção
necessária. Achado real de UX (não um desvio de padrão, uma lacuna
genuína): o simulador não dizia nada sobre gravidez de risco — um
utilizador nessa situação podia usar o formulário sem perceber que está
a calcular a prestação errada. Corrigido com uma FAQ nova (JSON-LD +
visível) e uma nota no campo "Situação especial", com os mesmos 3 factos
já publicados no artigo (100% da RR, desde o 1.º dia, até à data
provável do parto) — novo teste de coerência garante que os dois nunca
divergem.

**4) Relatório** — carimbo actualizado (`Verificado a 06/07/2026`,
`dateModified` do JSON-LD `Article`, e os 16 `verificado_em` de
`PARAMETROS_SUBSIDIO_DOENCA`). Resumo em `ROADMAP.md` →
"CONCLUÍDO RECENTEMENTE", apontando para esta secção — nem
`MELHORIAS-SPEC.md` nem `CALCULADORAS-SPEC.md` (citados na instrução
original) existem neste repositório: são documentos externos referidos
em sessões anteriores, nunca commitados (mesmo padrão de
`PROMPTGERADORDOCUMENTOSv1.md`) — a auditoria seguiu os 4 pontos
explícitos do pedido do Nuno, sem depender desses ficheiros.

25 testes em `tests/test_simulador_subsidio_doenca_calculo.py` (17→25).
Suite completa: **1747 passed, 4 skipped** (mesmos skips estruturais já
documentados); `ruff check scripts/ tests/ --select E,F,W --ignore
E501 .` limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados por esta sessão). Trabalho directo
em `main`, sem branches novas.*

---

*Última revisão: 2026-07-06 (continuação) — ponto ⚠️A **fechado**: o
Nuno confirmou directamente, com detalhe legal, que **não existe
qualquer retroactividade** dos dias de espera — são sempre uma perda
efectiva de rendimento, seja qual for a duração da baixa, confirmando a
versão conservadora já implementada desde a publicação (nenhuma
alteração de código necessária, só de texto/citação). Actualizado
`simulador-subsidio-doenca.html` (comentário JS ⚠️A marcado "FECHADO",
FAQ JSON-LD + visível e nota do `formula-box` reformuladas de forma
assertiva, em vez da formulação anterior "não encontrámos nenhuma regra
que...") e `baixa-medica-subsidio-doenca.html` (novo parágrafo explícito
sobre ausência de retroactividade, mais duas nuances novas trazidas pelo
Nuno e antes não documentadas: 1. baixas intermitentes com menos de 60
dias de intervalo não voltam a aplicar o período de espera — mesma
regra de "fusão de baixas" já existente para o tecto de duração, agora
também referida aqui; 2. nota sobre Contratos Colectivos de Trabalho que,
nalguns sectores, obrigam a entidade patronal a pagar o vencimento
destes dias, apesar de a Segurança Social não o fazer — distinto de
acidente de trabalho, já coberto noutra secção do artigo). Carimbo do
artigo actualizado para 06/07/2026 (`Verificado a`, `dateModified`,
fonte-bloco).

Ponto ⚠️B (piso 300€/325€ em períodos parciais) continua em aberto —
nenhuma informação nova recebida sobre esse ponto nesta continuação.

Nenhum teste dependia do texto exacto alterado (confirmado por grep
antes de editar); JSON-LD validado (`json.loads`) nos dois ficheiros.
Suite completa reconfirmada sem regressões; `ruff` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False`. Trabalho directo em `main`, sem branches novas.*

---

*Última revisão: 2026-07-07 — limpeza de CSS morto da nav antiga (dívida
técnica registada na Fase 4, 2026-07-02). Novo
`scripts/limpar_css_morto_nav.py` (padrão dos `sincronizar_*.py`:
inventário por omissão, `--write` para aplicar, `--check` para CI, exit
≠ 0 em estado inesperado — parse CSS falhado ou remoção que não converge
nunca parecem sucesso). Inventário primeiro, nunca assumido: tabela
ficheiro/seletor/correspondências sobre as 55 páginas servidas (raiz +
`p/` + `documentos/`), correspondência por token exacto de classe/id
(nunca substring — `nav-mobile-menu` da nav nova contém "mobile-menu" e
teria sido um falso positivo desastroso), mais detecção de classes que o
JS consegue adicionar em runtime (`classList.add/toggle`, `class=` em
strings JS, `className=` — leituras `querySelector` não contam).
**Removidas 170 regras em 35 páginas (12.528 bytes, diff só de remoções,
zero inserções)**: `.hamburger` (×2/página), `nav a.nav-link`/`:hover`/
`.active`, `.nav-mobile-sim-label`/`.nav-mobile-sim-link` (só
`index.html`) e os `@media (max-width:700px)` que ficaram vazios.

**Achado principal do inventário — não estava no mapa**: 8 páginas
(`amim`, `complemento-solidario-idosos`, `prestacao-social-para-a-inclusao`
e as 5 do cluster PSU) ainda têm um `<div id="menu-mobile"
class="mobile-menu">` completo da nav antiga logo a seguir a
`<!-- NAV:FIM -->` (links desactualizados — "Por onde começar?",
simuladores antigos), invisível por `display:none` e sem hamburger que o
abra. Por isso **as regras `.mobile-menu*` ficaram intocadas nas 34
páginas onde aparecem** (AMBÍGUO pela regra global: um seletor que
corresponde a algo em qualquer página nunca é removido — e removê-las
nas 8 páginas tornaria o div visível). `.mobile-menu.aberto` também
ficou (a classe `aberto` é adicionável pelo `nav.js` — a prova de morte
tem de ser por token nunca-adicionável, não por combinação improvável).
16 páginas têm ainda um `<script>` inline morto (`toggleMobileMenu`,
nunca chamado, só leituras) — fora do âmbito CSS desta sessão. Remoção
dos divs órfãos + scripts + CSS `.mobile-menu` registada em `ROADMAP.md`
como sessão dedicada futura. 18 seletores mortos FORA da família nav
também encontrados e deliberadamente não tocados — vários são
falsos-mortos por interpolação JS (`escalo-${n}` no simulador de abono,
`cat-${categoria}` em notícias): lição registada — detecção estática de
classes "mortas" nunca pode tocar em classes construídas dinamicamente.

Verificação: idempotência provada (2.ª corrida `--write` = 0 alterações;
`--check` exit 0); Playwright real a 375px em
`index`/`manuais-escolares-mega`/`acao-social-escolar`/
`subsidio-desemprego`/`amim` — nav abre, 10/10 links do menu clicáveis
(elementFromPoint, sem sobreposições), div órfão continua invisível,
scrollWidth idêntico antes/depois (o overflow de 462px em
`acao-social-escolar.html` é pré-existente — tabela larga — confirmado
igual na versão HEAD, não é regressão desta limpeza); suite pytest
completa sem regressões; `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados).*

---

*Última revisão: 2026-07-07 (mesma sessão, 2.ª passagem — aprovada pelo
Nuno depois do relatório da limpeza de CSS morto) — removido o resíduo
HTML/JS da nav antiga que tinha deixado as regras `.mobile-menu*` como
AMBÍGUAS: os 8 `<div id="menu-mobile" class="mobile-menu">` órfãos
(blocos byte-idênticos, confirmado por hash antes de remover), os 16
`<script>` inline mortos `toggleMobileMenu` (idem) e a variante própria
do `index.html` (`toggleMenu`/`toggleSimDropdown`, a apontar para ids
`#mobileMenu`/`#navSimDropdown` que não existem em página nenhuma —
apanhada por grep de token exacto, não pelo padrão dos outros 16). Com o
HTML fora, `limpar_css_morto_nav.py --write` reclassificou as 165 regras
`.mobile-menu*` de AMBÍGUO para MORTO e limpou-as (17.271 bytes, 33
páginas) — zero resíduos da nav antiga nas 55 páginas, zero AMBÍGUOS no
inventário final, `--check` verde. A fonte de contágio (código morto
copiado de páginas existentes para páginas novas — a página de bolsa do
superior, publicada na véspera, já nascia com ele) desapareceu; o
template `estrutura-pagina.md` confirmado sempre limpo.

Na mesma passagem, corrigidos os 4 únicos overflows horizontais a 375px
de todo o site (scan Playwright às 55 páginas, não amostragem; todos
pré-existentes, confirmados idênticos em HEAD antes de mexer):
`acao-social-escolar.html` (link-botão do `.portal-cta` com
`white-space: nowrap` — removido também em `manuais-escolares-mega.html`
e `prova-escolar.html`, mesmo padrão copiado, ainda sem sintoma);
`prestacao-social-unica.html` e `psu-quando-entra-em-vigor.html`
(`.timeline-item .desc` é filho flex sem `min-width: 0` — o token
inquebrável "Chega+Livre+PCP+BE+PAN+JPP" no texto real dos votos definia
a largura mínima; adicionado `min-width: 0` + `overflow-wrap:
break-word`); `complemento-solidario-idosos.html` (`.checklist li` é
flex e o `<ul>` aninhado dos valores de referência virava item flex AO
LADO do texto em vez de abaixo — `flex-wrap: wrap` no li +
`flex-basis: 100%` no ul). Cada correcção testada primeiro por injecção
de CSS no browser real (447→375, 462→375, 439→375) e só depois aplicada
ao ficheiro. Scan final: 0 de 55 páginas com overflow a 375px; menu
mobile aberto e 10/10 links clicáveis (elementFromPoint) nas 13 páginas
verificadas. Suite pytest completa sem regressões, ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados).*

---

*Última revisão: 2026-07-07 — sentinela `dre_psu` corrigido de vez
(Issue #54, bloqueado há 9 dias consecutivos). Executado o trabalho que
estava registado como pendente desde a auditoria de 2026-07-05: sessão
com browser interactivo real (workflow `workflow_dispatch` temporário,
2 iterações — runs 28860869507 e 28861231682 — apagado no fim, mesmo
padrão das sessões anteriores) para confirmar o mecanismo real de
pesquisa do DRE antes de qualquer troca de URL. Confirmado: a pesquisa
do diariodarepublica.pt é uma SPA OutSystems que guarda o termo num
cookie — NENHUM parâmetro de URL filtra em navegação directa (índice
inteiro, 2,2M resultados, HTTP 200); a pesquisa interactiva na caixa
funciona, e com aspas força frase exacta no Elasticsearch (2 resultados
vs 12.651 sem aspas). O endpoint API interno
(`screenservices/.../DataActionGetPesquisas`) foi identificado mas
deliberadamente não usado — exige tokens CSRF/versão de módulo
OutSystems que mudam a cada deploy do DRE, uma fragilidade pior do que
a interacção real com a página. Correcção completa na secção "IMPACTO
DA PSU" → nota do sentinela: `pesquisa_interactiva` +
`_obter_html_pesquisa()` + âncora com o eco do termo entre aspas +
detecção por item (`_detectar_decreto_psu()`, corrige falso positivo
latente) + perfil de browser provado. 9 testes novos
(`tests/test_dre_psu_pesquisa.py`, fixtures do texto real do
diagnóstico); suite completa local 1438 passed sem regressões
(feedparser/Playwright indisponíveis no sandbox, mesma limitação
documentada — CI corre tudo); ruff limpo. Verificado no pipeline real
(`workflow_dispatch` de `pipeline-diario.yml`) — ver o run exacto na
Issue #54; fecho automático da Issue pela máquina de estados ao
primeiro dia OK. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados por esta sessão). Trabalho directo
em `main`.*

---

*Última revisão: 2026-07-07 — og:image em todas as partilhas sociais.
Sintoma reportado pelo Nuno com screenshot real: partilhar um artigo no
Facebook mostrava a pré-visualização só com texto, sem imagem nenhuma —
confirmado por grep que **nenhuma** das 55 páginas servidas tinha
`og:image` (as restantes OG tags existiam todas desde a Fase 5). Criada
`assets/img/og-default.png` (1200×630, formato standard do
Facebook/WhatsApp/LinkedIn), gerada com Chromium real a partir da marca
existente (quadrado teal #0F766E + visto branco do `favicon.svg` —
nunca um logótipo inventado): logo + "Tens Direito" + tagline "Apoios
sociais, direitos e burocracia em Portugal" + selo "Verificado em
fontes oficiais" + domínio. Novo `scripts/adicionar_og_image.py`
(idempotente, `--write`, mesmo padrão de `adicionar_canonicas.py`):
insere `og:image` (URL absoluto), `og:image:width`/`height` (permitem
render à primeira partilha), `og:image:alt` e `twitter:card =
summary_large_image` a seguir à última tag `og:*` de cada página —
aplicado às 55 páginas (raiz + `p/` + `documentos/`, incluindo
`404.html`/`simulador-psu.html`: og:image não faz mal a páginas
noindex), 2.ª corrida = zero alterações. Decisão pragmática: **uma
imagem única para o site inteiro** — imagens por página seriam um
projecto à parte, registável se um dia se justificar. Novo
`tests/test_og_image.py` (57 casos): og:image presente em todas as
páginas com o URL certo, metadados width/height a bater com as
dimensões REAIS do PNG em disco (lidas do cabeçalho IHDR, nunca números
soltos), imagem existe e é 1200×630, twitter:card presente — uma página
nova sem og:image falha o CI. Checklist obrigatória e "ESTRUTURA HTML
OBRIGATÓRIA" actualizadas. Suite completa local: 1724 passed, 4 skipped
(desta vez com os testes Playwright a correr no sandbox); ruff limpo.
Nota operacional para partilhas já feitas: o Facebook guarda a
pré-visualização em cache — para a refrescar num link já partilhado,
usar o Sharing Debugger (developers.facebook.com/tools/debug) e "Scrape
Again"; partilhas novas apanham a imagem automaticamente.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False`. Trabalho directo em `main`.*

---

*Última revisão: 2026-07-07 (continuação, pedida pelo Nuno na mesma
conversa do og:image) — imagens de partilha social POR PÁGINA, estilo
jornal. `scripts/gerar_og_images.py` (sessão manual, nunca pipeline):
renderiza com Chromium real um cartão 1200×630 por página — título real
do artigo (o `og:title` curado, com a marca "Tens Direito" removida do
texto quando duplicaria o wordmark do cartão), chip com o nome do
cluster (de `data/clusters.json`, fonte única; "Gerador de documentos"
para as minutas, "Simuladores e calculadoras" para o hub), selo
"Verificado em fontes oficiais" e domínio — guardado em
`assets/img/og/<slug>.jpg` (JPEG q88, ~55KB/imagem, ~3,2MB pelas 55 —
PNG seria 5× mais pesado sem ganho visível). Tamanho de fonte do título
adaptativo ao comprimento (58→34px) + line-clamp de 4 linhas.
Idempotente por manifest (`assets/img/og/manifest.json`: slug →
título/chip usados): só re-renderiza quando o título/chip muda ou a
imagem falta (`--force` regenera tudo); remove imagens órfãs de páginas
apagadas/renomeadas; actualiza `og:image`/`og:image:alt` de cada página
para a sua imagem. `adicionar_og_image.py` fica como bootstrap do bloco
de metas em páginas novas (a imagem única `og-default.png` mantém-se
como alvo provisório desse bootstrap até o gerador correr).
`tests/test_og_image.py` reescrito (112 casos): cada página aponta para
a SUA imagem, o JPEG existe e é mesmo 1200×630 (dimensões lidas do
cabeçalho SOF, nunca números soltos), e o manifest tem de bater com o
`og:title` actual — mudar um título sem regenerar falha o CI
(**provado a falhar de propósito**: og:title do abono adulterado →
teste vermelho com mensagem clara; revertido → verde). Sem imagens
órfãs (teste dedicado). Chip mais longo do site ("Idosos, Incapacidade
e Cuidadores") confirmado a caber no layout por inspecção visual real.
Nota de cache do Facebook mantém-se: links já partilhados precisam de
"Scrape Again" no Sharing Debugger. Trabalho directo em `main`.*

---

*Última revisão: 2026-07-07 (continuação) — detecção de datas expiradas
tornada recursiva, fechando a limitação documentada desde a Fase 5 do
Shadow Mode: `verificar_datas.main()` e `run_shadow_daily._paginas_elegiveis()`
(sempre juntos — mesma fonte por desenho) passaram a cobrir também `p/`
e `documentos/`, que até hoje tinham **zero vigilância de datas** (17
páginas servidas fora do âmbito). Clarificação importante face à análise
que motivou a sessão: o aviso "⚠️ ANOMALIA: 0 alertas" dos relatórios de
4 e 7 de julho NÃO era sintoma deste gap — é o sinal de honestidade
desenhado (raiz cresceu além das 25 páginas do limiar; nos dias 5-6
havia alertas reais, por isso a linha não aparecia). Antes de ligar a
recursividade, simulação prévia com o `detectar_alertas()` real sobre as
17 páginas: exactamente 1 falso positivo dispararia no dia 1 —
`p/habitacao.html`, "contrato anterior a 15 de março de 2023" (3
ocorrências; a data-limite fixa de elegibilidade do PAER, mesma família
das Issues #51/#52 mas com a formulação inversa "anterior a", que os
marcadores existentes não cobriam). Ordem deliberada: 1.º o marcador
`\\banterior(?:es)?\\s+a\\b` em `MARCADORES_HISTORICOS` (ancorado como
"posterior a" — "anterior" solto nunca suprime, testado), 2.º a
recursividade — nunca deixar a Issue falsa nascer para a fechar depois.
Nomes de página passam a caminho relativo (`p/habitacao.html`) nos
alertas/Issues — para as páginas da raiz nada muda. 5 testes novos em
`tests/test_verificar_datas.py` (41 no ficheiro): regressão sobre o
pillar real, estado trancado "0 alertas nas 17 páginas de p/ e
documentos/", guarda anti-sobre-supressão do marcador novo, supressão do
caso real isolado, e `main()` a percorrer os 3 directórios com data
fixada em julho (o padrão `data_mes_ano` só é revisto em 1/7/8/9 — sem
isso o teste ficaria sazonalmente vermelho de Outubro a Junho).
Verificação ponta-a-ponta local com o código novo: 52 páginas
elegíveis, 0 alertas — exactamente o resultado previsto na simulação.
Suite completa: 1784 passed, 4 skipped; ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados). Trabalho directo em `main`.*

---

*Última revisão: 2026-07-11 — expansão de `subsidio-desemprego.html` (pedido
do Nuno, com fact-check obrigatório sobre um rascunho que continha erros
reais). **Fact-check corrigiu o rascunho em 3 pontos** antes de publicar,
por triangulação de 3 fontes independentes (Montepio, DECO PROteste, CGD
Saldo Positivo — `WebFetch`/`curl` continuam bloqueados nesta sessão, 403
via proxy, mesma limitação documentada; dre.tretas.org também inacessível):
1) os escalões intermédios da tabela de duração propostos (240/270/330
dias) estavam errados — os valores reais do art. 37.º do DL n.º 220/2006
são **330** (30-39 anos), **360** (40-49) e **480** (50+) dias para o
escalão "mais de 15 até 24 meses"; 2) o acréscimo por carreira longa não é
"30 dias para os 50+" — é **30 dias (menos de 40 anos), 45 dias (40-49) e
60 dias (50+)** por cada 5 anos com registo de remunerações nos últimos 20
anos, só no escalão >24 meses de descontos; 3) o exemplo proposto (52 anos,
20 anos de descontos → 660 dias) estava errado — o valor correcto é **780
dias** (540 + 4×60), publicado assim. Adicionado: secção "Quanto tempo dura
o subsídio de desemprego em 2026" (tabela completa 4 idades × 3 escalões,
antes de "Como pedir"), secção "Subsídio de desemprego parcial" (fórmula
verificada: subsídio + 35% − remuneração do trabalho, com exemplo
500/350→325 €; nunca excede o subsídio base; prazo de 90 dias), 3 FAQs
novas (duração; IRS/descontos — não sujeito a IRS, sem descontos SS, conta
para a reforma por equivalência, confirmado em fontes fiscais; part-time),
bullet de duração no resumo rápido, tempo de leitura recalculado (7→11
min). Meta description e `og:description` ganharam "quanto tempo dura"
(canários `test_valores_ancora.py` continuam a passar — 537,13 € e 65%
intactos; `<title>` com 1.342,83 € intocado, já optimizado a 2026-07-05);
entrada de `scripts/pesquisa.js` sincronizada (descricao + keywords
duração/parcial/irs). **Pedido do rascunho deliberadamente não aplicado**:
converter as FAQs de `<details>/<summary>` para `<h3>` abertos — viola a
regra 8 de "REGRAS DE CONTEÚDO" (padrão de todo o site) e o conteúdo já é
indexável (HTML estático + JSON-LD `FAQPage`, que é o que alimenta os rich
results); título proposto também rejeitado (o actual, com o valor em €, foi
optimizado com canário há dias para o mesmo problema de CTR). Testes:
1035 passed nos ficheiros de higiene/canários/nav/breadcrumb/pesquisa/og,
36 passed em `test_resposta_rapida_checklist.py` (Chromium real), axe da
página a passar; JSON-LD dos 4 blocos validado (`json.loads`). Sem
alterações a `.py` (ruff não aplicável). `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*

---

*Última revisão: 2026-07-11 (fecho do merge) — a expansão de
`subsidio-desemprego.html` foi integrada em `main` por rebase +
fast-forward (commit `ae3d88f`, depois de `main` ter avançado com os
pipelines de 09-10/07). Ao verificar o CI do merge, encontrado e corrigido
um vermelho **pré-existente** (desde o push de 08/07, sem relação com esta
sessão): `test_acessibilidade` falhava em `noticias.html` com
`color-contrast` (serious) nas badges de categoria `Habitação`
(`#16A34A`, 3.30:1) e `Emprego` (`#D97706`, 3.19:1) — categorias novas
dos feeds de 2026-07-04 cuja primeira notícia só chegou ao arquivo a
08/07, altura em que o axe passou a vê-las renderizadas. Corrigido nas
variáveis CSS do próprio `noticias.html` (o `<head>` é estático — o
pipeline só escreve entre `DESTAQUE`/`ARQUIVO`, a correcção persiste):
`--cat-emprego: #B45309` (5.02:1) e `--cat-habitacao: #15803D` (5.02:1),
mesma família de cor escurecida, prática da auditoria WCAG. As outras 4
cores de categoria foram verificadas por cálculo directo e já cumpriam
(apoios 5.47, educacao 5.17, fiscal 5.70, legislacao 4.83) — nenhuma
regressão latente ficou à espera da primeira notícia dessas categorias.
Axe local de `noticias.html` a passar após a correcção.*

---

*Última revisão: 2026-07-11 — CookieYes removido e substituído por banner de
consentimento próprio, gratuito e self-hosted (pedido do Nuno: o plano
gratuito do CookieYes atingiu 80% do limite de 5.000 pageviews/mês — ao
chegar a 100%, o banner deixaria de aparecer, com risco RGPD). Nota: as
alternativas WordPress consideradas inicialmente (Complianz, etc.) não se
aplicam — o site é HTML estático puro no GitHub Pages. Solução no mesmo
padrão de `share.js`/`nav.js`: novo `assets/js/consentimento.js` (vanilla
JS, ~6KB, estilos injectados pelo próprio script, zero dependências
externas, zero limites) com **bloqueio real de script** — o gtag.js do GA4
deixou de estar estático no `<head>` e passa a ser injectado pelo próprio
`consentimento.js` SÓ depois de o visitante clicar "Aceitar"; "Rejeitar"
(ou não responder) mantém a página sem qualquer pedido de rede de
analytics. Consent Mode v2 negado por omissão num stub inline (que também
define o `gtag()` global de que os simuladores dependem para
`calc_resultado`); escolha em localStorage (`td_consentimento`), com
`window.tdGerirConsentimento()` a reabrir o banner — novo botão "Gerir
cookies" em `privacidade.html`, cuja secção de cookies foi reescrita
(GA4 só após aceitação, escolha revogável) e datada de 11/07/2026.
Migração das 55 páginas servidas por novo `scripts/migrar_consentimento.py`
(idempotente, dry-run por omissão, recusa páginas cujo bloco não
corresponda ao padrão esperado — 55/55 migradas, 0 erros, 2.ª corrida =
zero alterações, zero restos de "cookieyes" em HTML confirmado por grep).
Novo `tests/test_consentimento.py` (115 casos): estático (nenhuma página
volta a referenciar CookieYes; todas têm o stub + `data-ga4`; gtag.js
estático proibido — o teste falha se voltar a aparecer; ordem stub →
consentimento.js) e Chromium real com intercepção de rede (banner na 1.ª
visita com zero pedidos ao googletagmanager; Aceitar carrega GA e persiste
entre reloads; Rejeitar nunca carrega e persiste; "Gerir cookies" reabre o
banner). Testes existentes adaptados: `test_acessibilidade.py` audita as
55 páginas COM o banner visível (experiência real da 1.ª visita — 0
violações axe, contraste do banner desenhado com a paleta já auditada,
branco sobre `#0F766E` 5.47:1, touch targets ≥44px); os testes que clicam
(`test_gerador_documentos.py`, `test_resposta_rapida_checklist.py`)
removem o banner do DOM sem tocar em localStorage (o teste "zero chaves"
do checklist continua válido) — as rotas mortas de `cdn-cookieyes.com`
foram removidas dos 3 ficheiros. `CLAUDE.md` (stack, checklist, estrutura
HTML) e `.claude/commands/atualizar-cluster-psu.md` actualizados. Suite
completa: **1988 passed, 4 skipped** (mesmos 4 skips estruturais da
allow-list); ruff limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados).
Depois do deploy: apagar o site/conta CookieYes no painel deles é opcional
mas recomendado — o script já não é chamado por nenhuma página.*

---

*Última revisão: 2026-07-11 — secção "Bónus: Cartão Europeu de
Estacionamento" adicionada a 3 páginas de incapacidade: `amim.html`
(alvo principal — o cartão exige o AMIM; a subsecção 7.6 e o checklist
final passam a linkar à secção nova por âncora `#cartao-estacionamento`),
`prestacao-social-para-a-inclusao.html` e `cuidador-informal.html`
(ambas com link para o guia do AMIM). Factos exclusivamente do pacote
verificado pelo Nuno a 2026-07-11 (fontes: imt-ip.pt e gov.pt) — DL
n.º 307/2003 na redação do DL n.º 128/2017; limiares ≥60% (motora,
intelectual/PEA, oncológica com AMIM, Forças Armadas) e ≥95% (visual);
gratuito via Serviços IMT Online ou balcão; pessoal e intransmissível;
validade 10 anos salvo reavaliação. Páginas com menção meramente
incidental a "incapacidade" (baixa médica = incapacidade temporária
para o trabalho, CSI, cluster PSU) e o pillar (agregador, já lista o
amim.html) ficaram deliberadamente de fora. Carimbos de página e
`dateModified` NÃO foram tocados (o resto do conteúdo não foi
re-verificado) — a secção nova leva a sua própria linha "Verificado a
11/07/2026", regra "Data em cada facto". Canário novo em
`tests/test_valores_ancora.py` (limiares 60/95%, validade 10 anos e
diplomas nunca podem divergir entre as 3 cópias da secção; link ao AMIM
obrigatório excepto no próprio). Verificado: `detectar_alertas()` real
sem falsos positivos nas 3 páginas (os anos 2003/2017 dos diplomas não
disparam nada), 0px de overflow a 375px com Chromium real,
`sincronizar_clusters.py` corrido (refrescou o bloco ATUALIZACOES:HOME
do `index.html`, que estava desactualizado da sessão anterior — datas
reais dos carimbos, as 3 páginas desta sessão não entram porque os
carimbos delas não mudaram). Suite completa + ruff limpos.*

---

*Última revisão: 2026-07-11 — nova página `assistencia-familia-filhos.html`
(cluster `familia`, 4.ª página — "Faltas e licenças para assistência a
filhos e família 2026"), cobrindo as 4 modalidades + subsídios: faltas
para assistência a filho (art. 49.º CT — 30 dias/ano <12 anos ou
deficiência/doença crónica sem limite de idade, 15 dias ≥12, +1 dia por
filho além do 1.º, nunca os dois progenitores em simultâneo), subsídio
para assistência a filho (100% RRL, nunca <65% RR, mínimo diário 14,32 €
= 80% de 1/30 do IAS 2026, +2% Regiões Autónomas, garantia 6 meses, CIT
do SNS dispensa requerimento senão Mod. RP5052-DGSS, urgências nunca
contam como certificação, pago desde o 1.º dia, não declarado em IRS),
licença para assistência a filho (art. 52.º CT — até 2 anos, 3 com 3+
filhos, NÃO remunerada, comunicação escrita 30 dias antes), assistência
a filho com deficiência/doença crónica/oncológica (Mod. RP5053; não
acumula com subsídio social de desemprego, acumula com RSI), faltas para
membro do agregado (art. 252.º CT — 15 dias/ano SEM subsídio, destacado
na resposta rápida como o ponto que mais surpreende) e avós (Mod. RP5054
— nascimento de neto de adolescente <16 anos: 30 dias a 100% RR;
doença de neto menor: até 30 dias a 65% RR).

**PASSO 0 da tarefa (valor em transição) cumprido**: a LOE2026 (Lei
n.º 73-A/2025, art. 253.º) alterou o art. 36.º do DL 91/2009 — o PDF do
Guia Prático está bloqueado pela política de rede desta sessão (mesma
limitação documentada), mas o valor foi confirmado por triangulação de
duas fontes oficiais independentes via WebSearch (o próprio guia
2026 em seg-social.pt indexado + anúncio em garantiainfancia.gov.pt):
**80% da RR** para deficiência/doença crónica e **100% da RR** para
doença oncológica, desde 01/01/2026, com tecto mensal de **1.611,39 €**
(3 × IAS 2026) — sem divergência face aos factos fornecidos; o tecto é
um facto adicional confirmado nessa verificação e citado na página.

FAQ pedida "afeta férias/antiguidade?" deliberadamente NÃO incluída —
não havia facto verificado no pacote da tarefa que a suportasse (zero
factos de memória); substituída por FAQs cobertas pelos factos (filho
≥12 anos; cuidar de pais/cônjuge). Integração completa: `data/clusters.json`
(+`descricao_curta` actualizada), `sincronizar_clusters.py`
(PILLAR-LISTA de `p/familia.html`, cartão da homepage "3 guias · 1
simulador", RELACIONADOS cruzados com abono/parental), `sitemap.xml`
(com `lastmod`), `scripts/pesquisa.js`, `DATAS_PUBLICACAO`, imagem og
própria (`gerar_og_images.py`), scripts idempotentes todos a 0
alterações na 2.ª corrida. 3 âncoras novas em `tests/test_valores_ancora.py`
(dias/formulários RP5052-4; mínimo 14,32 € e tecto 1.611,39 €
IAS-derivados — falham sozinhos quando o IAS mudar; percentagens
pós-LOE2026). Verificado: axe zero violações, 0px overflow a 375px,
`detectar_alertas()` sem falsos positivos, JSON-LD 4 blocos válidos.*

---

*Última revisão: 2026-07-11 — novo `scripts/validar_carimbos_elegiveis.py`
(sessão manual, só leitura, nunca no pipeline): o passo humano do
critério de activação da revalidação de carimbo, nascido da validação
manual feita nesta sessão a pedido do Nuno. Recalcula a elegibilidade com
a função real (`calcular_carimbos_elegiveis`), compara com o relatório
shadow do dia, verifica cada página elegível (fontes OK, hash 24h,
conteúdo real, status nunca `ok_via_arquivo`) e cobre a zona cega
documentada da simplificação de 24h — mudanças de hash da fonte desde o
carimbo da página, classificadas como artefacto do scraper (URL mudou
entre scrapes) ou aviso ⚠️ de possível mudança real (mesma URL, juízo
humano). Exit 0 = dia conta para a contagem de ≥14 simulações correctas;
exit 1 = falso elegível/scrape em falta/divergência. Corrido contra os
dados reais de 2026-07-11: 14/14 elegíveis validados, zero falsos
elegíveis, 9 avisos todos rastreados às correcções de fetch de 03/07
(seg-social/iefp) e 07/07 (dre_psu) — nunca a mudanças externas das
fontes. **Contagem do gatilho iniciada: 2026-07-11 = dia 1 validado**
(registo corrente na linha do gatilho em ROADMAP.md). Secção
"REVALIDAÇÃO DE CARIMBO" ganhou o ponto 6 com a ferramenta. 11 testes
novos em `tests/test_validar_carimbos_elegiveis.py` (todos os caminhos
de falha provados, isolados em tmp_path); ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` — este script não muda nenhum comportamento, só observa.*
---

*Última revisão: 2026-07-12 — Fases 0+1+2 de `CALENDARIO-PAGAMENTOS-SPEC.md`:
nova página evergreen `calendario-pagamentos-seguranca-social.html` (ver nova
secção "CALENDÁRIO DE PAGAMENTOS DA SEGURANÇA SOCIAL"). Fase 0: fonte oficial
identificada e documentada em `docs/FONTE-CALENDARIO.md` — notícia mensal do
portal antigo (`/noticias/-/asset_publisher/kBZtOMZgstp3/content/datas-de-pagamento-...`,
com a fragilidade real de o slug ser reciclado entre meses — validar o mês
sempre no conteúdo, nunca no URL) + página Calendário do portal novo
(`/ptss/pssd/menu/pagamentos-dividas/valores-a-receber/calendario`);
seg-social.pt continua bloqueado nesta sessão (403 na proxy, `WebFetch` e
`curl`) — julho 2026 triangulado por ≥5 fontes independentes que reproduzem o
calendário oficial (3/7/8/16/21/23/28 jul; tudo por transferência + vale de
correio excepto apoio à renda, só transferência; subsídio de férias dos
pensionistas pago com a pensão de julho). **Agosto deliberadamente não
incluído** — as 2 únicas fontes encontradas (blogs) são indistinguíveis de
previsão por regra de dias fixos; fica para a Fase 3. Fase 1:
`data/calendario_pagamentos.json` (fonte de verdade). Fase 2: página com
tabela do mês + secção "Quando recebo a minha prestação?" (9 âncoras, links
aos guias), FAQ (5 perguntas, factos só das fontes trianguladas), JSON-LD
`FAQPage`+`BreadcrumbList`+`Article`, e injecção idempotente por
`scripts/atualizar_calendario.py` (zonas `CAL:META`/`CAL:CORPO`; validação
dura com allow-list de prestações; estado degradado explícito "consultar
fonte oficial" quando falta o mês corrente — meses passados nunca renderizados;
og:title estável sem mês para não obrigar a regenerar a imagem og
mensalmente). Guarda JS em runtime mostra aviso se a página ficar velha no
browser do visitante (zero rede). Canário de frescura adiantado da Fase 4
(`tests/test_calendario_frescura.py`, 13 testes): página com mês passado =
CI vermelho deliberado — provado a falhar de propósito e revertido; caminhos
de falha da validação todos cobertos (invariante "nenhum estado de erro pode
parecer sucesso"). Achado real: o grafo de órfãs de `test_higiene_indexacao.py`
não segue hrefs com `#fragmento` — os 7 cross-links com âncora não contavam,
resolvido com link simples em `comecar-aqui.html` (Ferramentas). Integração
completa: EXCLUIDAS, nav, sitemap, pesquisa.js, og-image própria,
`DATAS_PUBLICACAO`, cross-links em 7 páginas de prestações. Verificado com
Chromium real: aviso de desatualização a disparar na cópia com mês velho e
escondido no estado normal, âncoras a funcionar, 0px de overflow a 375px,
zero erros JS; axe a passar; `detectar_alertas()` sem falsos positivos na
página nova. Fases 3+4 (workflow mensal, até 31 jul) e 5 registadas em
ROADMAP.md. Ruff limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
não tocados.*
---

*Última revisão: 2026-07-12 (mesma sessão, continuação) — Fases 3+4 de
`CALENDARIO-PAGAMENTOS-SPEC.md`, com um achado que mudou o desenho.
Diagnóstico em runner real (4 rondas de `workflow_dispatch` temporário,
`diagnostico-calendario-temp.yml` + `scripts/_diag_calendario.py`, ambos
apagados no fim — runs 29191741983/29191780772/29191873395/29191994617):
**a fonte oficial pública do calendário deixou de existir com a migração
do portal da Segurança Social** — o portal antigo (notícia mensal,
`/noticias`, `/pagamentos2`) redirecciona tudo para o gateway SSD (213
chars de shell de cookies via requests; via Playwright a SPA carrega a
home e ignora o parâmetro `r=`); o portal novo não tem nenhuma notícia
de datas de pagamento na listagem pública (13 itens, sem paginação),
slugs candidatos dão 404 real (`/ptss/fraw/errors/404`) e o "Calendário"
de valores-a-receber é funcionalidade com login. Scraping automático é
hoje impossível, não apenas frágil — implementado o fallback
semiautomático que a spec previa: novo `.github/workflows/calendario-mensal.yml`
(cron dia 25 + retry 28 para o mês seguinte; cron dia 1 às 05:30 que
vira a página quando o JSON já tem o mês novo; `workflow_dispatch` com
`forcar_seguinte`; `concurrency: main-writes`; guardrail próprio — falha
se qualquer ficheiro fora de `data/calendario_pagamentos.json` + a
página aparecer modificado; pós-push: `garantir_deploy_pages.sh` + smoke
inline; fecho automático da Issue do mês ao ficar resolvida) + novo
`scripts/verificar_calendario_mensal.py` (decide o mês alvo — dia ≥ 20 →
seguinte; sonda `/ptss/pssd/noticias` via Playwright para detectar a
publicação oficial a reaparecer; relatório da sonda + prompt pronto a
colar no corpo da Issue `calendario-manual`, dedup por título com o
mês; nunca commit parcial, nunca dados inventados). Fase 4 completa:
`tests/test_calendario_frescura.py` passou de 13 para 16 testes —
Playwright mobile 375px (tabela visível, 0px de overflow, 9 âncoras da
spec presentes e navegação por âncora real) e a guarda JS provada com a
página de mês velho servida em memória por um handler HTTP de teste
(nunca um ficheiro escrito no repositório, para o guardrail do workflow
nunca tropeçar em restos de teste). Tabela de workflows actualizada
(8 workflows, 3 com push de conteúdo, âmbitos disjuntos).
`docs/FONTE-CALENDARIO.md` reescrito com o achado e o desenho final.
Verificado em CI real por run_id exacto (ver entrada seguinte se
aplicável): caminho `dados_ok` (no-op, sem commit) e caminho
`precisa_manual` (Issue de agosto criada com sonda + prompt) — a Issue
de agosto fica deliberadamente aberta como tracking real até à sessão
manual que publicar agosto. Ruff limpo; suite completa local verde
(2081+ testes; única falha local era `lxml` em falta no sandbox,
instalado e confirmado a passar).
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*
---

*Última revisão: 2026-07-12 — Fase 5 de `CALENDARIO-PAGAMENTOS-SPEC.md`:
nova página evergreen `pagamento-apos-deferimento.html` ("Pedido
deferido: quando cai o primeiro pagamento"), a long-tail identificada
na spec — responde à dúvida real de quem já foi deferido mas ainda não
recebeu. Fact-check prévio via `WebSearch` (WebFetch continua bloqueado
nesta sessão), triangulando o enquadramento de cada prestação: prazo
geral de decisão de 90 dias do CPA (DL n.º 4/2015, dever de decisão);
subsídio de desemprego (1.º pagamento em 30 dias a contar do
requerimento completo, direito desde a data do requerimento);
subsídio de doença (desde o fim do período de espera); parental (desde
a data do parto); abono de família (retroativos só se pedido dentro dos
6 meses — a excepção que penaliza quem se atrasa; fora do prazo, só a
partir do mês seguinte ao pedido); RSI (direito desde o requerimento
instruído; se o contrato de inserção não for celebrado em 60 dias por
facto não imputável, devido a partir do 61.º dia); pensão de velhice
(processamento de meses, 1.º pagamento com retroativos, possível pensão
provisória); CSI (a partir do mês seguinte ao pedido). Mensagem central
honesta: deferido ≠ pago, e o 1.º pagamento nem sempre cai na 1.ª data
do calendário — mas em regra inclui retroativos. Estrutura: card de
enquadramento (CPA), tabela por prestação com cross-link ao guia de
cada uma, HowTo "como acompanhar o 1.º pagamento" (SSD → IBAN →
pagamentos → exposição por atraso), FAQ (5 perguntas), JSON-LD
`Article`+`HowTo`+`FAQPage`+`BreadcrumbList`. Cross-links nos dois
sentidos com `calendario-pagamentos-seguranca-social.html` (a FAQ de
deferimento do calendário passa a linkar aqui — é o que torna a página
alcançável, não órfã) e com os geradores de `exposicao-atraso-processamento`
e `reclamacao-decisao-seguranca-social`. Integração: `EXCLUIDAS`
(utilitária cross-cluster, mesma categoria do calendário/comecar-aqui),
sitemap, pesquisa.js, `DATAS_PUBLICACAO`, og-image própria; scripts
idempotentes (partilhar/canónica/autoria/article) a zero — a página
nasceu conforme. Verificado: axe 0 violações, 0px de overflow a 375px,
`detectar_alertas()` sem falsos positivos (o "2015" do DL vive no corpo,
fora de title/description), 4 blocos JSON-LD válidos, suite dos testes
parametrizados verde. Título deliberadamente sem ano (procedimento
evergreen, como `comecar-aqui`; o canário de anos só rejeita anos
passados, não exige o corrente). Ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.
Fecha o projecto CALENDÁRIO-PAGAMENTOS (Fases 0-5).*
---

*Última revisão: 2026-07-12 — destaque "Próximo pagamento" no topo de
`calendario-pagamentos-seguranca-social.html` (pedido do Nuno: é a
informação por que a maioria vem à página, tem de estar visível no topo
sem scroll). Duas camadas sem rede, dentro do sistema de injecção mensal
existente (zonas CAL:*): camada estática sempre visível com todas as
datas do mês (funciona sem JS) + `#cal-dados` (JSON dia+resumo curto) que
o script de runtime lê para promover a próxima data a contar de hoje
(`.cal-destaque-proximo`). Progressive enhancement rigoroso: num mês
renderizado no passado (aviso de desatualização) ou no estado degradado
nunca inventa um "próximo" — só promove quando `#cal-corrente[data-mes]`
== mês corrente do visitante; a camada estática mantém-se sempre. Novo
`RESUMO_CURTO` em `atualizar_calendario.py` (rótulos curtos para o
destaque; a tabela mantém os nomes longos de `PRESTACOES`). 4 testes
novos em `tests/test_calendario_frescura.py` (16→20): destaque estático
presente e antes da tabela, `#cal-dados` JSON válido e com os mesmos dias
do JSON de dados, promoção do dia certo a contar de hoje (Chromium real),
e ausência de promoção num mês velho com a camada estática intacta. axe 0
violações (contraste do destaque na paleta já auditada), 0px de overflow
a 375px, injector idempotente (2.ª corrida zero alterações), ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*
---

*Última revisão: 2026-07-12 — scraper automático do calendário de
pagamentos (pista do Nuno, que reverte a conclusão anterior de "scraping
impossível"). A fonte pública real é `https://www.seg-social.pt/ptss/pssd/pagamentos`
— confirmado num runner: HTTP 200 sem redirect para login, SPA com um
separador por mês, tabela oficial por dia (prestações + método), datas
publicadas antes do início do mês (a ronda de diagnóstico anterior só
falhou porque testou `/pagamentos2`/`/noticias`/"Calendário de
valores-a-receber", nunca este URL). Novo `scripts/scraper_calendario.py`:
`parse_innertext()` puro (texto do painel → schema do JSON, testado com o
texto real de agosto) + `raspar_mes()` via Playwright (clica no separador,
espera pelo cabeçalho do mês E por uma linha de método + settle — sem o
settle, ler cedo dava "dia sem prestações"; foi o único bug, corrigido e
provado). Mapeamento `NOME_PARA_SLUG` estrito: prestação fora da
allow-list, mês vazio ou método órfão fazem `ScraperError` — nunca
descarta em silêncio (INVARIANTE). Prestação nova real apanhada:
"Subsídio por Suspensão da Atividade Cultural" (dia 21 ago), acrescentada
a `PRESTACOES`/`RESUMO_CURTO`. `verificar_calendario_mensal.py` passa a
tentar o scraper quando falta o mês (grava só dados que passem a
validação); a Issue manual fica só como fallback. **Provado ponta-a-ponta
num runner: agosto de 2026 raspado ao vivo, validado, injectado, testado
e commitado automaticamente** (run mensal 29201776013 → commit do bot
`3f1dca8`; `fonte_url` do JSON agora `/ptss/pssd/pagamentos`; Issue #61
de agosto fechada sozinha; agosto servido como "mês seguinte" na página).
`tests/test_scraper_calendario.py` (7 casos: parser com o texto real +
desconhecida/vazio/outro-mês/método-órfão). `docs/FONTE-CALENDARIO.md` e
esta secção reescritos. Ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*

---

*Última revisão: 2026-07-12 — link "📅 Calendário" na nav principal (desktop
+ mobile, `sincronizar_nav.py`, 58 páginas) e **barra fixa "Próximo
pagamento" sempre visível no topo da homepage** (pedido do Nuno: é uma das
razões mais frequentes de visita). A barra (`.cal-topo`, sticky acima da nav
já sticky; combinador de irmão `.cal-topo-regiao ~ .nav-wrap` desce a nav só
na homepage, sem tocar nas outras páginas; envolvida em `role="region"` pela
regra axe) mostra por omissão "Calendário de pagamentos SS" e, por
progressive enhancement (zero rede), promove a próxima data a contar de hoje
— "📅 Próximo pagamento: 16 de julho". Mesma honestidade do resto do
calendário: um script de runtime só promove quando `#cal-home-dados[data-mes]`
(zona `CAL-HOME`, escrita por `scripts/atualizar_calendario.py`) é igual ao
mês corrente do visitante; num mês por actualizar ou sem dados, mantém o
rótulo genérico — nunca inventa uma data velha (provado com cópia adulterada
`data-mes="2000-01"`). `atualizar_calendario.py` ganhou `render_home()`/
`atualizar_homepage()` (reaproveitando `_dados_js()`, extraído de
`_destaque_topo()`); `main()` sincroniza agora a página do calendário E a
barra da homepage. `calendario-mensal.yml` passa a permitir `index.html` no
guardrail (só a zona `CAL-HOME`) e a incluí-lo no commit — 2.ª zona de escrita
de `index.html`, disjunta das 3 do `pipeline-diario.yml`, que nunca toca em
`CAL-HOME`; `concurrency: main-writes` serializa. REGRA DE OURO (Nota 2) e a
tabela de workflows actualizadas. Verificado com Chromium a 1200/375px: barra
promove "16 de julho" sem overflow nem erros JS, cópia de mês velho mantém o
rótulo genérico. `test_calendario_frescura.py` e `test_nav_coerencia.py`
estendidos (barra da homepage: markers, JSON coerente com os dados,
idempotência da injecção, promoção Playwright no mês corrente, sem promoção
num mês velho; link de nav em desktop+mobile). Ruff limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*

---

*Última revisão: 2026-07-13 — gatilho sazonal MEGA disparado: as datas de
emissão dos vales 2026/2027 foram publicadas. `manuais-escolares-mega.html`
(página #1 em cliques GSC) actualizada de "datas por publicar / padrão
histórico" para o calendário confirmado: **3 de agosto (1.º–4.º ano), 10 de
agosto (5.º–9.º ano), 13 de agosto (10.º–12.º ano)**. Fact-check com
`WebSearch` (WebFetch/official 403 em toda a sessão, mesmo padrão
documentado): triangulado por várias fontes independentes que reproduzem o
anúncio oficial (Executive Digest, Postal, WOOK). **Dois conjuntos de datas
recicladas apanhados e evitados** — "28 jul/4 ago/11 ago" é o calendário de
2025/2026 (juntava o 9.º ano ao 1.º ciclo; um dos próprios links enviados
pelo Nuno, pplware, mostrava estas); "2 de agosto" é do gc23 (2022). Sinal de
autenticidade do calendário novo: o 9.º ano mudou da fase do 1.º ciclo para a
fase de 10 de agosto. Actualizados: tabela do calendário, resposta rápida,
2 respostas JSON-LD (FAQ + HowTo passo 4), item da checklist, meta
description, `dateModified` (2026-07-13) e o carimbo "Verificado a" (13/07,
com nota da metodologia de triangulação). Achado de detecção de datas: a
menção a "2025/2026" (a explicar as datas recicladas) fazia
`test_verificar_datas.py::test_manuais_escolares_mega_real_nao_gera_alerta_issue_45`
falhar (ano_letivo passado sem marcador de supressão) — resolvido reescrevendo
"2025/2026" como "ano letivo anterior" nas 3 ocorrências (visível + JSON-LD +
comentário), em vez de reintroduzir um marcador de pendência falso
(`provisório`/`por confirmar`) — as datas estão confirmadas, não pendentes.
`sincronizar_clusters.py` corrido (promoveu a página para o topo de
ATUALIZACOES:HOME, 13 jul). Verificado com Chromium (1200/375px): tabela
3/10/13 ago, 0px overflow, zero erros JS; axe, higiene, canários de anos/
valores-âncora e breadcrumb todos verdes; 4 blocos JSON-LD válidos; ruff
limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.*

---

*Última revisão: 2026-07-13 (continuação) — migração para GOOGLE CONSENT
MODE V2 AVANÇADO em `assets/js/consentimento.js`. Motivo: o modo anterior
("básico"/carregamento condicional — gtag.js só carregava depois de
"Aceitar") só media consenters, e o GA4 tinha caído ~90% desde a
substituição do CookieYes (2026-07-11). Mudança de comportamento, banner e
texto inalterados: o gtag.js passa a carregar SEMPRE, para TODOS os
visitantes, logo no arranque da página — nunca mais à espera de "Aceitar".
O que decide se há cookies continua a ser só o estado do consentimento
(`analytics_storage`, negado por omissão no stub inline de cada página,
inalterado): em `denied` o GA4 envia à Google medições sem cookies ("pings
cookieless", usados para modelar estatisticamente os não consentidos);
`granted` só depois de "Aceitar", e só aí passam a existir cookies
`_ga`/`_ga_*`. `recusar()` mantém-se sem alterações (envia `denied` +
`apagarCookiesGA()`).

`carregarGA()` deixou de conceder consentimento — só injecta o `<script>`
do gtag.js (chamada incondicional no arranque, `gaCarregado` continua a
garantir uma só vez por página). Nova `concederConsentimento()` isola o
`gtag('consent','update',{analytics_storage:'granted'})`, chamada por
`aceitar()` e pelo arranque quando `lerEscolha() === 'aceite'` (repõe
`granted` antes do primeiro ping da carga da página — sem isso, quem já
tinha aceite passaria por `denied` a cada reload). "Sem aceitação, nenhum
cookie de análise é colocado" no texto do banner continua verdadeiro (ping
sem cookies ≠ cookie) — texto do banner intocado.

**Testes reescritos, não enfraquecidos** (`tests/test_consentimento.py`) —
os dois que assumiam "zero pedidos ao Google antes de aceitar" e "zero
pedidos mesmo depois de rejeitar" tornaram-se falsos com o novo
comportamento correcto e foram reescritos para o invariante novo, nunca
apagados nem contornados: `test_primeira_visita_mostra_banner_e_pede_ga_em_modo_denied`
(gtag.js pedido para todos; dataLayer nunca com `update->granted`; sem
cookie `_ga`), `test_aceitar_concede_consentimento_e_persiste` (dataLayer
com `update->granted` só depois de "Aceitar", persistente ao reload),
`test_rejeitar_mantem_denied_sem_cookies_mas_ga_continua_a_carregar`
(gtag.js continua a ser pedido, mas nunca `granted` nem cookie `_ga`, no
banner e no reload). Novo golden `test_consent_mode_avancado_golden` cobre
os 4 pontos da migração num único teste, lendo o `dataLayer` real via
`page.evaluate` (nunca inspecção de texto) — o guardrail que
`validar-conteudo.yml` não cobre (esse só confirma a tag presente no HTML
estático, nunca que dispara com o consentimento certo em runtime). Novo
teste estático `test_carregarga_nunca_concede_consentimento_por_si_so`
tranca `carregarGA()` a nunca conter `'granted'` no corpo e a concessão a
viver só dentro de `concederConsentimento()`. 122 testes a passar (era
`test_consentimento_js_nunca_carrega_ga_sem_aceitacao_explicita`, renomeado
e reescrito). Mantidos sem alteração:
`test_nenhuma_pagina_referencia_cookieyes`, o bloco estático do stub
`denied` por omissão (58/58 páginas confirmadas antes de mexer em
qualquer código), e `test_botao_gerir_cookies_reabre_o_banner`.

`privacidade.html` actualizada (secção "Cookies e análise de tráfego"):
divulga explicitamente que, em Consent Mode avançado, são enviadas
medições anónimas sem cookies ao GA4 mesmo sem consentimento, e que
cookies só são colocados após "Aceitar" — data de "Última atualização"
subida para 13/07/2026. **Redação sinalizada para revisão humana do Nuno**
— é uma divulgação nova em página com implicações RGPD, nunca publicada
sem essa revisão.

Stack (`CLAUDE.md`, secções "STACK TÉCNICO ACTUAL" e "ESTRUTURA HTML
OBRIGATÓRIA POR PÁGINA") actualizada para descrever o avançado em vez do
básico. Suite completa local: 2081+ testes sem regressões (só
`test_consentimento.py` tocado nesta sessão); `ruff` não aplicável (zero
`.py` alterados). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
não tocados.

**Fora do âmbito / verificação manual do Nuno**: validar com o Tag
Assistant da Google (tagassistant.google.com) — nunca no Brave, que
bloqueia por omissão os pings do GA4 — confirmando ping cookieless em
`denied` e hit completo depois de "Aceitar"; a modelação do Google só
arranca com volume mínimo e alguns dias, os números do GA4 recuperam
gradualmente, não de imediato — GSC continua a ser a fonte de verdade
para alcance total entretanto.*

---

*Última revisão: 2026-07-13 — novo `simulador-rsi.html`, 5.º simulador do
site, cluster `trabalho-rendimento`. Sessão conduzida em 7 fases
aprovadas sequencialmente pelo Nuno (auditoria legal → definição
funcional → matriz de casos de cálculo → arquitetura → implementação),
cada uma só avançando após aprovação explícita — nenhum código escrito
antes da Fase 5.

**Fase 1 (auditoria)**: valores 2026 confirmados por triangulação
externa (DRE, Jornal de Negócios, e-konomista, Doutor Finanças) contra
os já publicados em `rsi.html` — RSI base 247,56€ (46,09% do IAS),
adulto adicional 173,29€ (70%), menor 123,78€ (50%), sem qualquer tecto
ao número de elementos do agregado; limite de património 32.227,80€
(60×IAS); trabalho dependente conta 80%, independente/subsídio de
desemprego/outros contam 100%.

**Fase 4/5 (arquitetura e implementação)**: `simulador-rsi.html`
reutiliza integralmente o CSS/estrutura de `simulador-subsidio-doenca.html`
(`:root` vars, `.calc-card`, `.resultado-card`, `.desagregacao-wrap`,
`.formula-box`, `.faq-section`, `.disclaimer`, `.info-box`, `.aviso-teto`,
`.aviso-info`) — zero classes novas de fundo, só 2 classes de layout
(`.form-secao-titulo`, `.aviso-psu-topo`) e o padrão `.erro-campo` para
mensagens de validação inline. JS organizado nas 8 secções pedidas
(constantes/mensagens/utilitários/validação/cálculo/renderização/
eventos/inicialização): `PARAMETROS_RSI` (cada valor com `fonte`/
`verificado_em`, mesmo padrão de `PARAMETROS_CSI`/`PARAMETROS_SUBSIDIO_DOENCA`),
`MENSAGENS_RSI` centralizado (erros/avisos/caixa de fiabilidade, nunca
repetidos), `calcularRSI()` 100% pura (nunca toca no DOM, devolve
componentes estruturados com `label`/`valor`/`regra`/`subtotal` — a
mesma estrutura serve as duas tabelas do resultado via
`renderTabelaComponentes()` genérico), `calcularIdade()` isolada
(comparação por componentes de data, nunca subtração de milissegundos —
evita o erro clássico de fuso horário/duração variável dos meses).

**Divergência arquitetural deliberada face aos 4 simuladores anteriores**
(decisão aprovada nas Fases 2/3, documentada em comentário no próprio
código): `validarInputRSI()` é uma camada nova que distingue "campo
vazio → 0€" de "texto inválido → erro bloqueante" — os outros
simuladores usam sempre `parseFloat(x) || 0`, que nunca faz essa
distinção. Por isso os campos de rendimento e de composição do agregado
usam `type="text"` com `inputmode` (não `type="number"`, que bloquearia
a entrada de texto inválido no próprio browser e tornaria a validação
impossível de exercitar). Adultos/menores rejeitam decimais (regex de
inteiro estrito, nunca arredondados); nenhum tecto (`max`) no HTML, só
`min` — confirmado na Fase 1 que a lei não impõe limite ao agregado.

**Transparência do resultado** (Fase 2/3, decisão aprovada): o
breakdown (valor máximo por componente + rendimentos por tipo, cada um
com a regra aplicada) nunca desaparece, mesmo com avisos de idade
<18 anos, residência não-legal ou património acima do limite — os
avisos (`.aviso-teto`/`.aviso-info`, reutilizados sem variante nova)
aparecem a seguir ao cartão do resultado, nunca substituem o cálculo.
Precisão numérica: `arredondarCentimos()` aplicado em cada subtotal
antes de qualquer soma/subtração subsequente (nunca só no passo de
exibição) e `formatarEuro()` elimina explicitamente `-0.00`.

Integração completa: `data/clusters.json` (`simulador-rsi.html`, tipo
`ferramenta`, cluster `trabalho-rendimento`), `sincronizar_clusters.py`
corrido com sucesso (actualizou `index.html`/`p/trabalho-rendimento.html`/
`baixa-medica-subsidio-doenca.html`/`subsidio-desemprego.html` —
`RELACIONADOS` cruzado e cartão do cluster/homepage), `sincronizar_nav.py`/
`inserir_botao_partilhar.py`/`adicionar_canonicas.py`/
`adicionar_autoria_artigos.py`/`adicionar_article_jsonld.py` confirmados
a **zero alterações** (a página já nasceu com todos os blocos correctos,
escritos à mão seguindo o padrão exacto dos scripts — idempotência
confirmada antes de qualquer commit); `gerar_og_images.py --write`
gerou a imagem própria. Cross-link novo em `rsi.html` (secção "Cálculo
do valor"), 5.º cartão em `simuladores.html`/`index.html`/`data/clusters.json`,
entrada em `sitemap.xml` e `scripts/pesquisa.js`.

**Testes**: `tests/test_simulador_rsi_calculo.py` (50 testes) cobre a
matriz completa da Fase 3 — casos simples/casais/monoparental/agregados
numerosos sem tecto, rendimento zero, limite exacto e fronteiras de 1
cêntimo, robustez de ponto flutuante (nunca `-0.00` nem resíduos),
património/residência/idade (isolados e em combinação, breakdown sempre
visível), datas de nascimento (aniversário exacto, véspera do 18.º ano,
29 de fevereiro), validação de inputs inválidos (decimais em
adultos/menores, texto não-numérico em rendimentos, datas futuras/vazias
— nunca convertidos a 0€ em silêncio) e um teste dedicado que confirma
nenhum valor legal escrito directamente no corpo de `calcularRSI()`
(só via `PARAMETROS_RSI`). Caso de regressão obrigatório: 2 adultos + 2
crianças + subsídio de desemprego 450€ → 218,41€, idêntico ao já
publicado em `rsi.html` e no histórico deste ficheiro. Suite completa
do repositório reconfirmada sem regressões: **2243 passed, 4 skipped**
(os mesmos 4 skips estruturais já documentados — nenhum skip novo).
`ruff check scripts/ tests/ --select E,F,W --ignore E501 .` limpo; os 4
blocos JSON-LD (`WebApplication`+`FAQPage`+`BreadcrumbList`+`Article`)
confirmados como JSON válido. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão). Trabalho feito no branch `claude/rsi-simulator-audit-dxy93p`
(designado pelo ambiente remoto desta sessão).*

---

*Última revisão: 2026-07-13 (continuação) — optimização pós-lançamento
do simulador do RSI: `rsi.html` ganhou 5 CTAs (após a introdução, antes
e depois da fórmula, antes da FAQ, final antes de "Outros artigos deste
cluster"), todos reutilizando o mesmo componente visual já existente na
página (a caixa azul `#EFF6FF`/`#2563EB` já usada para os links de
reclamação e calendário de pagamentos) — zero CSS novo. O link ao
simulador que já existia na secção "Cálculo do valor" foi promovido a
esse mesmo componente em vez de ficar como link simples.

FAQ expandida com 5 perguntas novas de intenção de pesquisa (como
calcular passo a passo, quanto recebe uma pessoa sozinha, quanto recebe
um casal com filhos, quem pode pedir, como funciona o limite de
património — esta última com o facto novo da regra "1/12 do maior
entre rendimentos de capitais ou 5% do património", já verificado via
seg-social.pt/Guia Prático na sessão de auditoria do simulador),
sincronizadas 1:1 entre os `<details>` visíveis e o `FAQPage` JSON-LD.
Intenções já cobertas por FAQs existentes (subsídio de desemprego conta
para o RSI, RSI conta como rendimento, valor do RSI em 2026) não foram
duplicadas — mantidas como estavam, para não criar conteúdo quase-
-idêntico. `dateModified`/"Verificado a"/"Fontes verificadas" avançados
para 13/07/2026 (novo facto adicionado, mesmo padrão do resto do site).

SEO interno: `p/trabalho-rendimento.html` ganhou um 2.º link `.ver-guia`
no mini-card do RSI apontando ao simulador — mesmo padrão já usado no
mini-card do Abono em `p/familia.html`, só não tinha sido retrofit ao
RSI por o simulador ainda não existir. `subsidio-desemprego.html` ganhou
um cross-link contextual (não artificial) na secção do subsídio social —
quem não cumpre as condições de recursos desse subsídio é um público
real para o RSI como alternativa. Nenhum link forçado para
`simulador-csi.html`/CSI — população-alvo diferente (idosos ≥66a9m vs.
pobreza extrema geral), sem facto verificado de acumulação a citar.

Verificado: 4 blocos JSON-LD de `rsi.html` válidos (13 perguntas no
FAQPage, 10 `<details>` visíveis — a mesma assimetria parcial já existia
antes desta sessão, não introduzida agora), todos os links internos
novos resolvem para ficheiros reais, `test_breadcrumb_coerencia.py`/
`test_higiene_indexacao.py`/`test_valores_ancora.py`/
`test_anos_metadados.py` (392 casos) e `test_acessibilidade.py` nas 4
páginas tocadas (`rsi.html`, `subsidio-desemprego.html`,
`p/trabalho-rendimento.html`, `simulador-rsi.html`) confirmados sem
regressões. Suite completa: **2243 passed, 4 skipped** (mesmos skips
estruturais já documentados). `ruff` não aplicável (zero `.py`
alterados). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
não tocados.*

---

*Última revisão: 2026-07-13 — novo `simulador-subsidio-desemprego.html`,
6.º simulador do site, cluster `trabalho-rendimento`. Mesmo processo de
7 fases do RSI (auditoria legal → definição funcional → matriz de casos
→ arquitetura → implementação), cada fase aprovada explicitamente pelo
Nuno antes de avançar, sem reabertura de decisões já fechadas.

**Fase 1 (auditoria)**: valores 2026 confirmados por triangulação
externa (DECO PROteste, ABANCA, CGD, Montepio, Doutor Finanças, Fed
Finance, sem divergências) — RR diária = remuneração×12÷360, subsídio
diário = RR×65%, mínimo 537,13€ (100% IAS) ou 617,70€ majorado (115%
IAS, quando a remuneração-base era ≥ salário mínimo de 920€), máximo
1.342,83€ (2,5× IAS) ou 1.477,11€ majorado (ambos os cônjuges
desempregados com filhos a cargo), prazo de garantia de 360 dias
(regime geral e TI economicamente dependente) ou 720 dias (TI com
cessação de actividade), duração por escalão etário × meses com
registo (150–540 dias base) + acréscimo de carreira longa (30/45/60
dias por grupo de 5 anos, só no escalão >24 meses), redução da duração
pelos dias de atraso além do prazo de 90 dias para requerer. Confirmada
e documentada a revogação em janeiro de 2018 da antiga redução de 10%
aos 180 dias — não modelada, nem deve voltar a sê-lo sem um facto novo.

**Decisões aprovadas (Fase 1), fechadas para as fases seguintes**: (1)
tecto de 75% da RR líquida e a excepção do mínimo absoluto de 349,13€
— nenhum dos dois é calculado (dependem da retenção de IRS, sem taxa
única), mostrados sempre como aviso, nunca como número; (2) Subsídio
Social de Desemprego — não calculado, só sinaliza elegibilidade
possível quando o prazo de garantia do subsídio normal não é cumprido;
(3) Subsídio de Desemprego Parcial — fora de âmbito desta versão; (4)
trabalhadores independentes cobertos via selector de 3 vínculos (conta
de outrem / TI economicamente dependente / TI com cessação de
actividade); (5) `subsidio-desemprego.html` actualizado primeiro, como
fonte de verdade, antes do simulador usar qualquer valor; (6)
Remuneração de Referência simplificada a um único campo (remuneração
mensal habitual), sem o detalhe dos 12 dos últimos 14 meses.

**Fase 2 (funcional), 2 melhorias aprovadas**: (1) "meses com registo
de remunerações" mantido como simplificação de UX, convertido
internamente para dias (`meses × 30`) e comparado contra os limiares
legais exactos (360/720 dias) — aproximação documentada no texto de
ajuda do campo e em comentário no código; (2) duração do subsídio
destacada em bloco próprio (`.duracao-card`, novo — único CSS
genuinamente novo desta sessão), sempre antes do breakdown financeiro,
mostrando duração total/base/majoração com motivo/redução por atraso.

**Fase 4/5 (arquitetura e implementação)**: `simulador-subsidio-desemprego.html`
reutiliza integralmente o CSS/estrutura de `simulador-rsi.html` (`:root`
vars, `.calc-card`, `.form-group`, `.resultado-card`,
`.desagregacao-wrap`, `.formula-box`, `.faq-section`, `.disclaimer`,
`.info-box`, `.aviso-teto`, `.aviso-info`, `.erro-campo`) — zero
duplicação de componentes visuais. JS nas mesmas 8 secções
(constantes/mensagens/utilitários/validação/cálculo/renderização/
eventos/inicialização). `PARAMETROS_SUBSIDIO_DESEMPREGO` (cada valor
com `fonte`/`verificado_em` próprios) e `TABELA_DURACAO_BASE` (12
combinações idade×meses) são a única fonte de valores legais —
confirmado por teste dedicado que nenhum valor "mágico" aparece solto
dentro de `calcularSubsidioDesemprego()`. `calcularDuracao()` e
`calcularSubsidioDesemprego()` são funções puras, isoladas, nunca
tocam no DOM — `calcularSubsidioDesemprego()` chama `calcularDuracao()`
internamente e devolve tudo num único objecto estruturado.
`validarInputSubsidioDesemprego()` segue o mesmo padrão estrito do RSI
(nunca `parseFloat(x)||0`): remuneração e meses são obrigatórios (vazio
→ erro), anos de registo e dias de apresentação são opcionais (vazio →
0), decimais rejeitados sempre com erro explícito em campos inteiros.
Transparência: o breakdown financeiro e a duração aparecem sempre,
mesmo quando o prazo de garantia não é cumprido — o aviso de
inelegibilidade aparece a par, nunca substitui o cálculo.

Integração completa: `data/clusters.json` (6.ª página do cluster
`trabalho-rendimento`, tipo `ferramenta`), `sincronizar_clusters.py`
corrido com sucesso (actualizou `index.html`/`p/trabalho-rendimento.html`
— `RELACIONADOS` cruzado e cartão do cluster/homepage), `sincronizar_nav.py`/
`inserir_botao_partilhar.py`/`adicionar_canonicas.py`/
`adicionar_autoria_artigos.py`/`adicionar_article_jsonld.py` confirmados
a **zero alterações** (página já nasceu com todos os blocos correctos,
idempotência confirmada antes do commit); `gerar_og_images.py --write`
gerou a imagem própria. `simuladores.html` (hub — 6.º card, `hasPart`
JSON-LD, "Cinco"→"Seis calculadoras" no `<h1>`/description/og,
descrição do `<head>` actualizada) e a secção "Simuladores e
Calculadoras" do `index.html` (6.º cartão) actualizados; entrada em
`sitemap.xml` e `scripts/pesquisa.js`. Mini-card do subsídio de
desemprego em `p/trabalho-rendimento.html` ganhou o 2.º link `.ver-guia`
para o simulador (mesmo padrão já usado no mini-card do RSI). Três CTAs
novos em `subsidio-desemprego.html` (após o exemplo de cálculo, após o
exemplo de duração, antes da secção de FAQ), mesmo componente visual
`#EFF6FF`/`#2563EB` já usado nas outras páginas do cluster — zero CSS
novo. `subsidio-desemprego.html` também ganhou, antes desta fase de
implementação, o valor do mínimo majorado (617,70€) na tabela de
limites e um aviso explícito sobre os dois factores não modelados
(tecto de 75% da RR líquida e mínimo absoluto de 349,13€), com
`dateModified`/"Verificado a"/"Fontes verificadas" avançados para
13/07/2026 — o artigo tinha de reflectir estes factos antes do
simulador os usar (Decisão 5 da Fase 1).

**Testes**: `tests/test_simulador_subsidio_desemprego_calculo.py` (62
testes) cobre a matriz completa da Fase 3 — os dois casos de regressão
obrigatórios (1.200€/mês → 780€/mês; 52 anos/>24 meses/20 anos de
registo → 780 dias, ambos idênticos aos exemplos já publicados em
subsidio-desemprego.html), mínimo/mínimo majorado/máximo/máximo
majorado (incluindo fronteiras exactas), elegibilidade por prazo de
garantia (regime geral vs. TI com cessação, incluindo fronteiras de 1
mês), duração (as 12 combinações da tabela idade×meses, fronteiras de
escalão, majoração por carreira longa nos 3 grupos etários, grupos
incompletos que não contam, redução por atraso, nunca negativa),
validação (obrigatórios vs. opcionais, decimais rejeitados, texto
inválido nunca convertido a 0 em silêncio, datas de nascimento e no
futuro), precisão numérica (arredondamento a cêntimos em cada passo
intermédio, nunca -0,00€), interacção real via Chromium (campo
condicional de anos de registo, bloqueio de submissão com erro visível,
breakdown nunca escondido mesmo inelegível, botão Limpar), e coerência
artigo↔simulador (constantes de produção batem com os valores
publicados). Achado durante a escrita dos testes: o arredondamento a
cêntimos aplicado em CADA passo intermédio (não só no fim) faz o
resultado divergir ligeiramente de um cálculo "tudo de uma vez" —
ex. remuneração 5.000€ dá subsídio mensal bruto de 3.250,20€, não
3.250,00€ — comportamento correcto e testado, não um bug.

Suite completa reconfirmada sem regressões nas páginas tocadas
(`subsidio-desemprego.html`, `simulador-subsidio-desemprego.html`,
`p/trabalho-rendimento.html`, `simuladores.html`, `index.html`) via
`test_higiene_indexacao.py`/`test_breadcrumb_coerencia.py`/
`test_nav_coerencia.py`/`test_valores_ancora.py`/
`test_anos_metadados.py`/`test_pesquisa_indice.py`/`test_og_image.py`/
`test_sincronizar_clusters.py`/`test_acessibilidade.py` (0 violações
critical/serious nas 5 páginas). `ruff check scripts/ tests/ --select
E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão).*

---

*Última revisão: 2026-07-14 — nova página `como-pedir-niss.html`, cluster
`trabalho-rendimento`, 1.ª página da nova Camada 3 editorial ("Como fazer X
no portal") — ver `ROADMAP.md` → "🪪 CAMADA 3" para o índice e os próximos
candidatos (`declaração de não dívida`, `primeiro acesso à SSD`, `mudar
morada no CC`). É evergreen puro, sem sazonalidade, e o passo mais a
montante de qualquer apoio do site — sem NISS não há Segurança Social
Direta, apoios nem simuladores.

**Fact-check via `WebSearch`** (`WebFetch` continua completamente bloqueado
nesta sessão — 403 em qualquer domínio, mesma limitação documentada em
todas as sessões anteriores; triangulação feita só por `WebSearch`, várias
queries independentes por facto): confirmado sem divergências o
pré-fact-check fornecido — NISS atribuído automaticamente com o Cartão de
Cidadão (verso do cartão); quem pede (estrangeiros sem CC, cidadãos com
Bilhete de Identidade vitalício, menores sem CC através de quem exerce
responsabilidades parentais); formulário "Pedido de NISS – Cidadão
Estrangeiro ou Cidadão Nacional sem obrigatoriedade de ter Cartão de
Cidadão", online e gratuito; documentos por perfil (estrangeiros: 3 tipos —
identificação, situação de trabalho, autorização de residência; UE/EEE/
Suíça: só documento de identificação civil do país de origem); pedido pela
entidade empregadora como representante legal, só depois de contrato de
trabalho celebrado, com a comunicação do vínculo na SSD sempre obrigatória
à parte; levantamento presencial (próprio, advogado com cédula + procuração
forense original, ou terceiro com procuração original/Mod. PA-12),
agendamento opcional via SIGA/SigaApp ou 210 548 888 / 300 088 888 (dias
úteis, 9h–18h, gratuito); consulta do NISS já atribuído (verso do CC; SSD →
Perfil → Dados pessoais, entrada possível com Chave Móvel Digital sem saber
o número); NISS único e vitalício, nunca expira; base legal Lei n.º 4/2007,
de 16 de janeiro, e Lei n.º 110/2009, de 16 de setembro, na redação atual.

**Ponto ⚠️ resolvido — carta registada vs. email, não é contradição, são
dois serviços diferentes**: triangulado por 4 fontes independentes
(gov.pt — página de serviço oficial do pedido de NISS —, seg-social.pt,
DECO PROteste, CGD Saldo Positivo) que o pedido **isolado** de NISS (o
formulário "Pedido de NISS – Cidadão Estrangeiro ou Cidadão Nacional sem
obrigatoriedade de Cartão de Cidadão", o caso coberto por esta página) é
sempre notificado por **carta registada** para a morada indicada no
formulário, a avisar que o NISS já pode ser levantado presencialmente —
nunca por email. As menções a "email" encontradas nalgumas fontes
secundárias (CGD, e-konomista) dizem respeito a um serviço **diferente**:
o balcão único de NIF + NISS + n.º de utente do SNS para estrangeiros,
gerido pela AIMA nos Espaços Cidadão (passaporte + Chave Móvel Digital
activada, presencial), que de facto notifica por email + área reservada do
ePortugal + app gov.pt. A página documenta os dois canais distintamente,
com o contraste explícito na secção "Pedir NIF + NISS + n.º de utente
juntos", em vez de escrever algo vago que cobrisse ambos por preguiça.

**Prazo**: confirmado que o gov.pt não define nenhum prazo legal para a
atribuição — a página nunca apresenta um número de dias como regra, só um
aviso a desencorajar confiança em estimativas de fóruns/intermediários e a
remeter para contacto directo com a Segurança Social em caso de urgência.

**Estrutura**: resposta rápida (reaproveita `.resposta-direta`, 45
palavras) + tabela de desambiguação por situação (tenho CC / sou
estrangeiro / BI vitalício / é para o meu filho / a empresa trata / preciso
também de NIF e utente) + `HowTo` de 6 passos + secção dedicada ao balcão
único AIMA + secção "Já tenho NISS mas não sei qual é" + `.checklist-final`
(5 itens) + FAQ de 8 perguntas (`<details>` + `FAQPage`, 1:1) — os dois
blocos da FASE 1 de `MELHORIAS-SPEC.md` (`.resposta-rapida`/
`.checklist-final`) incluídos por serem obrigatórios em qualquer artigo de
conteúdo novo, mesmo padrão de `assistencia-familia-filhos.html`.

**Integração**: `data/clusters.json` (7.ª página do cluster
`trabalho-rendimento`, `tipo: "artigo"`); `scripts/sincronizar_clusters.py`
corrido com sucesso — actualizou automaticamente `index.html`
(`ATUALIZACOES:HOME`) e `p/trabalho-rendimento.html` (`PILLAR-LISTA`,
"4 guias · 3 simuladores"); os blocos `CLUSTER-BADGE`/`RELACIONADOS` da
própria página nova foram escritos à mão seguindo exactamente o formato do
script — confirmado **0 alterações** ao correr o script sobre o ficheiro
já escrito (idempotência provada antes do commit, não só depois).
`sincronizar_nav.py`, `inserir_botao_partilhar.py`,
`adicionar_canonicas.py`, `adicionar_autoria_artigos.py` e
`adicionar_article_jsonld.py` (`DATAS_PUBLICACAO` ganhou a entrada
`"como-pedir-niss.html": "2026-07-14"`) confirmados todos a **0
alterações** pelo mesmo motivo — os 4 blocos JSON-LD, a nav, o botão de
partilha e a canónica já nasceram correctos. `scripts/gerar_og_images.py
--write` gerou a imagem própria (`assets/img/og/como-pedir-niss.jpg`,
1200×630, confirmado pelo cabeçalho JPEG real, chip "Trabalho e
Rendimento" herdado de `data/clusters.json`). `sitemap.xml` (com
`lastmod`) e `scripts/pesquisa.js` actualizados manualmente.

**Cross-links** (passo 7 da tarefa — avaliados um a um, nunca inseridos
por rotina): `subsidio-desemprego.html` (inscrição no IEFP/SSD exige NISS),
`abono-de-familia.html` (pedido para pais/filhos estrangeiros),
`pagamento-apos-deferimento.html` (NISS é pré-requisito de qualquer
requerimento) e `simuladores.html` (depois de simular, pedir a sério exige
NISS) — todos via o mesmo padrão `aviso-info`/caixa azul já usado no resto
do site para este tipo de nota, nunca inventado um componente novo. A
página nova, por sua vez, linka de volta para `pagamento-apos-deferimento.html`
e `simuladores.html`.

**Canário de valores-âncora**: não aplicável — esta página não usa nenhum
valor legal em € ou % no `<title>`/meta description (é puramente
procedimental), por isso `tests/test_valores_ancora.py` não precisou de
nova entrada; confirmado explicitamente antes do commit, não assumido por
omissão.

**Ambiente de sandbox desta sessão** (nota operacional, sem relação com o
conteúdo publicado): `playwright`, `beautifulsoup4` e `lxml` não estavam
instalados neste sandbox — instalados nesta sessão (`pip install`, browsers
Chromium já pré-instalados em `/opt/pw-browsers`, reaproveitados via
`executable_path`); `feedparser` continuava a falhar por causa do
`sgmllib3k` (mesmo bug de `install_layout`/`setuptools` já documentado em
sessões anteriores) — corrigido com o mesmo workaround já registado
(extrair `sgmllib.py` do tarball para `site-packages` à mão). Com o
ambiente completo, a suite completa correu **duas vezes** para confirmar:
1.ª corrida trancou 1 falha real mas irrelevante ao conteúdo
(`test_dre_psu_pesquisa.py`, `bs4.exceptions.FeatureNotFound: lxml` — o
parser ainda não estava instalado nesse momento); instalado `lxml` e
reconfirmado **2356 passed, 4 skipped, 0 failed** na 2.ª corrida completa,
igual ao guardrail de skips (`scripts/verificar_skips_permitidos.py`
confirma os 4 skips reais a bater certo, elemento a elemento, com a
allow-list). `ruff check scripts/ tests/ --select E,F,W --ignore E501 .`
limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados por esta sessão — página evergreen sem
scraper próprio, sem revalidação automática de carimbo).*

---

*Última revisão: 2026-07-14 (sessão `calendario-escolar-apoios`) — 3 blocos.

**Bloco 1 (verificação)**: as datas MEGA 2026/2027 já tinham sido confirmadas
e publicadas numa sessão anterior (13/07/2026, commit `62a2ebb`) — nada por
fazer no conteúdo. Confirmado nesta sessão: `dge_manuais`/`igefe_mega`/
`mega_datas` em `OK` em `data/estado_fontes.json`, zero Issues abertas no
repositório, e `detectar_alertas()` real confirma zero falsos positivos na
página hoje. Entrada "Julho, até publicação" de `ROADMAP.md` → DATAS FIXAS
fechada e substituída por "Junho 2027" (próxima revisão sazonal).

**Bloco 2 (`bolsa-de-estudo-ensino-superior.html`)**: fact-check via
`WebSearch` (`WebFetch` continua bloqueado nesta sessão, 403, mesma
limitação documentada em todas as sessões anteriores) confirmou dois factos
novos, nenhum assumido de memória. 1) O prazo de candidatura 2026/2027
(14 ago-2 out, Despacho n.º 7994/2026) é genuinamente mais tardio do que em
anos anteriores — 2025/2026 decorreu entre 25 de junho e 30 de setembro,
confirmado por 3 fontes independentes (ULisboa, DGES, UTAD); a página
passou de apresentar essa data como "regra geral" sem contexto para
explicitar a comparação. 2) O novo sistema de ação social no ensino
superior (aprovado em CM a 21/05/2026, que a página já tratava como "ainda
não publicado") foi **promulgado pelo Presidente da República a 7 de julho
de 2026** — confirmado por 6+ fontes jornalísticas independentes (TVI, RTP,
DN, Notícias ao Minuto, Observador, Jornal Económico) e pelo comunicado
oficial do XXV Governo Constitucional, que já dá os parâmetros concretos:
bolsa mínima mantém-se em ≈872 €/ano, valor médio sobe de 1.734 € para
≈2.660 €, apoio de 160 €/mês para deslocados em residência, e uma nova
Bolsa de Incentivo de 1.045 € para bolseiros do escalão A da ASE que
ingressem pela 1.ª vez no ensino superior. **Limite reconhecido
explicitamente na própria página**: esta sessão não conseguiu confirmar a
citação exacta (número/data) do decreto-lei já publicado em Diário da
República — só a promulgação, um passo anterior à publicação — por isso a
secção "O que muda" cita o comunicado do Governo e o Regulamento já
publicado pela DGES/IES como fonte dos valores, com uma nota de
verificação explícita sobre essa lacuna, em vez de afirmar "já é lei" sem
confirmação directa. `<title>`/meta description mantidos sem valores em
€/% (só datas) — não foi necessária nova entrada em
`tests/test_valores_ancora.py`. `p/apoios-escolares.html` já tinha "IES,
I.P." correcto desde a publicação anterior; grep ao repositório confirmou
nenhuma outra página a citar o prazo antigo da bolsa.

**Bloco 3 (`calendario-escolar-apoios.html`, nova página, 7.ª do cluster
`apoios-escolares`)**: implementa a Proposta 1 de `ANALISE-CLUSTER-ESCOLAR.md`
(2026-07-06) — calendário único dos prazos de julho a outubro, agregando
sem duplicar (cada linha liga ao guia completo do apoio respectivo,
já fact-checked em sessões anteriores — só os 3 despachos do calendário
escolar/matrículas foram verificados de novo nesta sessão via `WebSearch`:
Despacho n.º 8368/2024, de 25 de julho, início das aulas 2026/2027 entre
11 e 15 de setembro; Despacho n.º 9989/2025, de 21 de agosto, confirmado a
alterar só o 1.º período de **2025/2026**, sem efeito em 2026/2027; Despacho
n.º 4472-A/2026, de 6 de abril, matrículas — datas já passadas à data de
publicação (14/07/2026), por isso tratadas como contexto na secção "Prazos
que se repetem todos os anos", não na linha temporal accionável). Linha
temporal julho→outubro + tabela-resumo (6 apoios) + FAQ de 6 perguntas
(`FAQPage`, 1:1 com a secção visível) + `.resposta-rapida`/`.checklist-final`
(FASE 1 de `MELHORIAS-SPEC.md`, obrigatórias em conteúdo novo) + JSON-LD
`Article`+`FAQPage`+`BreadcrumbList` (sem `HowTo` — mesmo precedente de
`calendario-pagamentos-seguranca-social.html`, página de referência sem
procedimento de pedido) + sem `ItemList` (avaliado, não acrescentava
validação extra face à linha temporal HTML já semântica).

Cross-links bidireccionais obtidos **automaticamente** por
`scripts/sincronizar_clusters.py` (adicionada como `tipo: "artigo"` em
`data/clusters.json`) — nunca editados à mão: a página nova entrou no
`PILLAR-LISTA` de `p/apoios-escolares.html` e no cartão do cluster da
homepage ("7 guias · 1 simulador"); o `RELACIONADOS` da própria página
(escrito à mão, 4 links por já saber a regra de "máx. 4, primeiros da
lista") confirmado **idêntico** ao que o script geraria — corrida real
confirma zero alterações a esse bloco. Os 6 outros artigos do cluster não
mudaram de `RELACIONADOS` porque a regra determinística mostra sempre os
4 primeiros irmãos da lista de `clusters.json` e a página nova entrou perto
do fim — comportamento esperado, não um bug.

**Detecção de datas sazonais** (pedido explícito da tarefa — "registar como
`verificar_datas.py` trata esta página"): confirmado com `detectar_alertas()`
real que a página **não** dispara hoje (julho de 2026, mês de publicação),
mas dispara sozinha em 2027 (meses 1/7/8/9, padrão `data_mes_ano`, âncorado
à frase "setembro de 2026" da FAQ do início das aulas) — comportamento
desejado, mesmo padrão de `prova-escolar.html`: força uma revisão consciente
todos os anos em vez de deixar o calendário ficar silenciosamente
desactualizado. Nova linha em CLAUDE.md → "PÁGINAS COM DATAS SAZONAIS" e em
`ROADMAP.md` → DATAS FIXAS ("Junho/Julho 2027").

Integração completa: `data/clusters.json`, `sitemap.xml` (com `lastmod`),
`scripts/pesquisa.js`, `scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO`, embora não usado — o `Article` já nasceu escrito à
mão), imagem OG própria (`gerar_og_images.py --write`, confirmada 1200×630
via cabeçalho JPEG real). `sincronizar_nav.py`/`inserir_botao_partilhar.py`/
`adicionar_canonicas.py`/`adicionar_autoria_artigos.py`/
`adicionar_article_jsonld.py` corridos sobre o repositório inteiro —
**zero alterações** às duas páginas desta sessão (escritas à mão já a
bater certo com o que os scripts gerariam); `sincronizar_nav.py` fez uma
correcção cosmética não relacionada em `noticias.html` (indentação do
bloco NAV gerado pelo pipeline diário, whitespace apenas).

**Ambiente de sandbox desta sessão**: `playwright`/`beautifulsoup4`/`lxml`/
`feedparser`/`pytest`/`playwright-stealth`/`ruff` não estavam instalados —
instalados nesta sessão (mesmo workaround já documentado para o
`sgmllib3k` do `feedparser`: `install_layout`/`setuptools` do sistema
falha a compilar, contornado extraindo `sgmllib.py` do tarball para
`site-packages` à mão); browsers Chromium reaproveitados de
`/opt/pw-browsers` via `PLAYWRIGHT_BROWSERS_PATH`. Suite completa:
**2382 passed, 4 skipped, 0 failed** (mesmos 4 skips estruturais da
allow-list, confirmados a bater certo elemento a elemento com
`tests/skips_permitidos.json`) — zero regressões nas páginas tocadas
(`bolsa-de-estudo-ensino-superior.html`) nem na página nova. `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados por esta sessão). Trabalho feito na branch
`claude/calendario-escolar-apoios-tsgjcp` (designada pelo ambiente remoto
desta sessão, per instrução do harness — a REGRA ABSOLUTA — GIT deste
ficheiro assume sessões locais em `main`; esta sessão remota opera sob a
designação de branch fornecida pelo ambiente, não uma branch criada por
iniciativa própria).*

---

*Última revisão: 2026-07-14 (sessão de integração `claude/calendario-escolar-apoios-tsgjcp`)
— corrige uma violação real da REGRA ABSOLUTA — GIT da sessão anterior: o
trabalho do calendário escolar/bolsa DGES tinha ido para uma branch em vez
de directamente para `main`.

**Integração**: `git log --oneline origin/main..claude/calendario-escolar-apoios-tsgjcp`
confirmou exactamente 1 commit por integrar (`718b9b9`) e `git diff --stat`
sem surpresas (13 ficheiros, mesmo diffstat já documentado na entrada
anterior). `origin/main` estava no mesmo commit-base da branch (`7fd08f1`),
por isso `git merge --ff-only` foi directo, sem rebase necessário — `main`
avançou de `7fd08f1` para `718b9b9` por fast-forward puro, sem merge
commit. Push directo (`git push origin main`, sem PR, conforme instruído).
`git push origin --delete claude/calendario-escolar-apoios-tsgjcp` deu
**403** (mesma limitação de sempre) — mas confirmado por
`limpar-branches.yml`, disparado automaticamente pelo próprio push a
`main`: a branch (0 commits únicos face a `main`) foi apagada sozinha pelo
GITHUB_TOKEN do Actions, sem intervenção manual — `list_branches` da API
confirma hoje só `main` no repositório remoto.

**CI no push real a `main`** (não os checks da branch, que nunca contam
como prova válida — só o evento `push` real): confirmados `success` para
o commit `718b9b9` — `Validar Conteúdo HTML`, `pages build and
deployment`, `Verificação de Produção (Smoke Test)`, `Limpar Branches
Órfãs`, e todos os 6 sub-jobs de `Integridade do Código` (`Qualidade
Python (Ruff)`, `Verificar Segredos (Gitleaks)`, `Vulnerabilidades
Packages (pip-audit)`, `Verificar Prompt Injection`, `Validação HTML
(W3C)`, e `Suite de Testes (pytest)` — este último foi o mais lento,
~7 min, correndo a suite completa + o guardrail de skips, ambos
`success`). Run completo:
`github.com/nunovinhas-creator/tens-direito/actions/runs/29325796062`.
Bate certo com a confirmação independente já feita localmente antes do
push: **2382 passed, 4 skipped, 0 failed**, os 4 skips a bater certo
elemento a elemento com `tests/skips_permitidos.json`.

**Gatilho da bolsa DGES — mantido aberto, não fechado**: a entrada em
`ROADMAP.md` → "Novo sistema de ação social no ensino superior" foi
reescrita para deixar claro que só a **promulgação** (7/07/2026) está
confirmada — a publicação em Diário da República e a citação exacta do
decreto-lei continuam por confirmar (acesso a dre.pt bloqueado em duas
sessões seguidas). Confirmado por grep que **nenhum** valor da bolsa
(872€/2.660€/160€/1.045€) tinha sido coberto por `tests/test_valores_ancora.py`
na sessão anterior — nada a remover. Confirmado por leitura da página que
o texto nunca afirma "já é lei", sempre "promulgado" com a lacuna de
publicação explicitada duas vezes (`aviso` + `Nota de verificação`) — não
precisou de correcção. Nova acção registada no ROADMAP para quando a
publicação for confirmada: verificar os valores contra o texto real do
diploma, citar o número do decreto-lei na página, e só depois disso cobrir
os valores em `test_valores_ancora.py` (nunca antes — um canário sobre um
valor de fonte secundária protegeria o número errado se o diploma
divergir).

**Sessão MEGA de 13/07 confirmada já documentada**: `CLAUDE.md` já tinha a
entrada "Última revisão: 2026-07-13 — gatilho sazonal MEGA disparado"
(linha 5448) com o raciocínio completo (datas 3/10/13 ago, fact-check,
carimbo actualizado) — nenhuma entrada retroactiva foi necessária.

**`scripts/urls_criticas.txt`**: `calendario-escolar-apoios.html`
acrescentada — mesma categoria de `calendario-pagamentos-seguranca-social.html`
(página de referência agregadora), critério editorial, não um limiar de
tráfego medido.

Alterações desta sessão são só a `.md`/`.txt` (nenhum código Python nem
teste tocado) — `ruff` não aplicável; confirmado por leitura directa que o
validador de conteúdo (`validar-conteudo.yml`) não se aplica a estes dois
ficheiros (só HTML). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` em `scripts/decisao_datas.py`, inalterados por esta
sessão. `git branch --show-current` = `main` confirmado no fim.*

---

*Última revisão: 2026-07-14 (sessão `declaracao-situacao-contributiva`) —
nova página `declaracao-situacao-contributiva.html`, cluster
`trabalho-rendimento`, 2.ª página da Camada 3 editorial ("Como fazer X no
portal" — ver ROADMAP.md → "🪪 CAMADA 3"). É o documento popularmente
conhecido como "certidão de não dívida à Segurança Social".

**Fact-check via `WebSearch`** (`WebFetch` continua completamente bloqueado
nesta sessão — 403 em qualquer domínio, mesma limitação documentada em
todas as sessões anteriores): confirmados sem divergências os 11 pontos do
pré-fact-check fornecido — nome oficial "Declaração da situação
contributiva" (seg-social.pt) vs. designação popular "certidão de não
dívida"; as 3 vias de situação regularizada (sem dívidas; dívida com
pagamento em prestações autorizado e cumprido; dívida reclamada/recorrida/
impugnada judicialmente com garantia prestada) — fora destas, a declaração
é emitida na mesma, com os valores discriminados; os 3 canais de pedido
(online SSD: Conta-corrente → Situação Contributiva → Obter declaração de
situação contributiva; correio: formulário RC3042-DGSS ao Centro Distrital
da morada; presencial); grátis, validade 4 meses; prazo de emissão na hora
quando regularizado online, até 10 dias úteis quando "Em análise", em
papel, ou pedido pelo Ministério Público; janela de 72 horas para um
pagamento se reflectir no sistema; código de verificação de autenticidade
no fim do PDF, confirmável na área de verificação da SSD; consentimento de
consulta a entidades públicas (nunca privadas — nunca um banco ou
senhorio) com início/fim definidos pelo próprio, informação consultada
válida até 6 meses; quem pode pedir (o próprio, representante legal,
entidades públicas autorizadas, qualquer credor — que só vê o n.º de meses
em dívida, nunca valores — ou o Ministério Público).

**Ponto ⚠️ da nuance crítica confirmado tal e qual o pré-fact-check
antecipava**: quem nunca trabalhou (por conta de outrem ou independente),
mesmo tendo NISS atribuído, não consegue pedir a declaração pela Segurança
Social Direta — o campo de início de actividade é obrigatório e, nesse
caso, nunca existiu; o pedido tem de ser feito presencialmente, com o
RC3042 preenchido. É o ângulo diferenciador da página (secção dedicada
"Nunca trabalhei — e agora?", com o exemplo real de uma candidatura a
bolsa/apoio).

**Ponto da certidão da AT resolvido, não deixado em aberto**: triangulado
por 3 fontes secundárias independentes (CGD Saldo Positivo, Doutor
Finanças, CRN Contabilidade) que a certidão equivalente das Finanças
(Certidão de Dívida e Não Dívida) passou a ter **também validade de 4
meses desde 1 de julho de 2025** — antes eram 3 meses. A secção "Serve
também para as Finanças?" desambigua as duas entidades/documentos e cita
esse facto, com o caminho no Portal das Finanças (Certidões → Certidão de
Dívida e Não Dívida) confirmado por 2 fontes tertiárias independentes.
Como a fonte directa é secundária (nunca confirmada em
`portaldasfinancas.gov.pt` — bloqueado nesta sessão como qualquer outro
domínio), a página nunca apresenta esse valor como se fosse tão certo
quanto os factos confirmados directamente em seg-social.pt/gov.pt — frase
formulada com essa cautela.

Estrutura: resposta rápida + resumo rápido (3 bullets) + tabela de
desambiguação (5 situações, incluindo cross-link para
`documentos/pedido-declaracao-comprovativo-prestacoes.html` — documento
diferente, para comprovar uma prestação específica, não a situação
contributiva) + "Quem pode pedir" + passo-a-passo `HowTo` (6 passos) + "E
se eu tiver dívidas?" (as 3 vias + janela de 72h) + "A alternativa sem
papel: consentimento de consulta" + "Nunca trabalhei — e agora?" +
`.checklist-final` (5 itens) + FAQ de 8 perguntas (`<details>` + JSON-LD
`FAQPage`, 1:1, confirmado programaticamente) + "Serve também para as
Finanças?" + `RELACIONADOS` do cluster. JSON-LD: `FAQPage` + `HowTo` (6
passos) + `BreadcrumbList` + `Article` — os 4 blocos confirmados como JSON
válido antes do commit.

**Cross-links avaliados um a um, nunca inseridos por rotina**:
`como-pedir-niss.html` (aviso-info existente estendido — depois de teres o
NISS, uma candidatura pode pedir-te esta declaração),
`bolsa-de-estudo-ensino-superior.html` (nota condicional no card
"Documentos necessários" — "se algum elemento do agregado tiver
rendimentos de trabalho, a instituição **pode** também pedir..." — nunca
afirmado como requisito confirmado, porque a página da bolsa não documenta
esse requisito explicitamente; frase deliberadamente condicional para não
inventar um facto), `documentos/pedido-declaracao-comprovativo-prestacoes.html`
(o card "O que saber sobre este pedido" ganhou o link para o guia novo —
esse gerador já cobria o pedido por escrito da mesma declaração, é o par
natural "como funciona" ↔ "gera a carta").

**Canário de valores-âncora — decisão de não cobrir, registada**: nem o
`<title>` nem a meta description desta página têm nenhum valor legal em €
ou % (só a duração "4 meses", que é uma validade administrativa, não um
valor legal derivado de fórmula nem uma Portaria) — fora do âmbito da
regra 11 de "REGRAS DE CONTEÚDO"/`tests/test_valores_ancora.py`, por isso
nenhuma entrada nova foi adicionada a esse ficheiro. Ano "2026" no
`<title>`/description é o ano corrente, sem excepção necessária em
`tests/test_anos_metadados.py`.

**`scripts/urls_criticas.txt` — decisão de não adicionar**: mesma decisão
já tomada para `como-pedir-niss.html` na sessão anterior (publicada no
mesmo dia) — é um artigo de conteúdo normal, não uma página de referência
agregadora cross-cluster como o calendário de pagamentos ou o calendário
escolar.

Integração completa: `data/clusters.json` (8.ª página do cluster
`trabalho-rendimento`, `tipo: "artigo"`), `sitemap.xml` (com `lastmod`),
`scripts/pesquisa.js`, `scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO`). `scripts/sincronizar_clusters.py` corrido com
sucesso — actualizou automaticamente `index.html` (`ATUALIZACOES:HOME`) e
`p/trabalho-rendimento.html` (`PILLAR-LISTA`); os blocos
`CLUSTER-BADGE`/`RELACIONADOS` da própria página nova (escritos à mão)
confirmados **idênticos** ao que o script geraria — idempotência provada
antes do commit (2.ª corrida = zero alterações). `scripts/sincronizar_nav.py`,
`scripts/adicionar_canonicas.py`, `scripts/adicionar_autoria_artigos.py`,
`scripts/adicionar_article_jsonld.py` e `scripts/inserir_botao_partilhar.py`
confirmados todos a **zero alterações** — a página já nasceu com nav,
canónica, autoria, `Article` JSON-LD e botão de partilha correctos.
`scripts/gerar_og_images.py --write` gerou a imagem própria
(`assets/img/og/declaracao-situacao-contributiva.jpg`, 1200×630 confirmado
pelo cabeçalho JPEG real).

**Ambiente de sandbox desta sessão**: `playwright`, `beautifulsoup4`,
`lxml`, `pytest`, `ruff` e `playwright-stealth` não estavam instalados —
instalados nesta sessão; `feedparser` continuava a falhar por causa do
`sgmllib3k` (mesmo bug de `install_layout`/`setuptools` do sistema já
documentado em várias sessões anteriores) — corrigido com o mesmo
workaround já registado (extrair `sgmllib.py` do tarball para
`site-packages` à mão). Browsers Chromium reaproveitados de
`/opt/pw-browsers` via `PLAYWRIGHT_BROWSERS_PATH` (já pré-instalados,
nenhum download novo).

Verificado: `detectar_alertas()` real sobre a página nova confirma **zero
falsos positivos** (nenhuma data/valor a disparar `data-expirada`); os 4
blocos JSON-LD válidos (`FAQPage` com 8 perguntas 1:1 com os `<details>`
visíveis, `HowTo` com 6 passos); `tests/test_acessibilidade.py` confirma
zero violações critical/serious nas 4 páginas tocadas
(`declaracao-situacao-contributiva.html`, `como-pedir-niss.html`,
`bolsa-de-estudo-ensino-superior.html`,
`documentos/pedido-declaracao-comprovativo-prestacoes.html`);
`tests/test_higiene_indexacao.py`/`test_breadcrumb_coerencia.py`/
`test_nav_coerencia.py`/`test_pesquisa_indice.py`/`test_og_image.py`/
`test_sincronizar_clusters.py`/`test_valores_ancora.py`/
`test_anos_metadados.py` confirmados sem regressões (1199 passed, 3
skipped nesse subconjunto). `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão — página evergreen sem scraper próprio, sem revalidação
automática de carimbo). Suite completa `pytest tests/` confirmada a
correr sem regressões antes do commit (ver resultado exacto no commit
desta sessão, se necessário reconfirmar via CI real no push).*

---

*Última revisão: 2026-07-14 — texto do bloco de relacionados renomeado:
"Outros artigos deste cluster" → "Artigos relacionados" (mais natural em
PT-PT e melhor para SEO). Alterado na fonte (`render_relacionados()` em
`scripts/sincronizar_clusters.py` — sem isto a próxima sincronização
reverteria os HTML), nos 26 artigos publicados que têm o bloco
`RELACIONADOS` e nas 2 asserções de `tests/test_sincronizar_clusters.py`
que fixavam a string antiga. Só o texto do `<h2>` visível mudou — zero
alterações a classes CSS, ids, atributos, JS, URLs, meta tags ou JSON-LD
(confirmado pelo diff: 26 ficheiros × 1 linha, sempre a mesma troca).
Idempotência reconfirmada (`sincronizar_clusters.py --dry-run` = 0
alterações após a mudança; pesquisa global sem nenhuma ocorrência antiga
fora desta secção histórica de 2026-07-02, que se mantém intocada pela
regra de nunca reescrever entradas de revisão passadas). 801 testes dos
ficheiros afectados a passar, ruff limpo.*

---

*Última revisão: 2026-07-14 — aplicadas as correcções da auditoria de
linguagem (baixa literacia digital), só texto visível ao utilizador, nada
mais: "cluster"→"tema" (homepage, única fuga de jargão interno);
"browser"→"navegador" uniformizado em 19 ocorrências visíveis (16 páginas
+ hub documentos/index/privacidade/p-familia — as meta descriptions e
JSON-LD com "browser" ficaram deliberadamente intocadas, por instrução
explícita de nunca mexer em SEO/dados estruturados nesta sessão);
"password"→"palavra-passe" (3 ocorrências visíveis; espelhos em HowTo
JSON-LD intocados); "CMD" expandido para "Chave Móvel Digital" na
checklist da declaração de situação contributiva; "Faz login"→"Inicia
sessão" (2); "download"→"descarregar" (1 visível); "hub de simuladores"→
"a página de simuladores" (com correcção de concordância do artigo);
"desagregação"→"mostra cada parcela do cálculo" (9 ocorrências visíveis +
1 descricao em scripts/pesquisa.js); mensagens de copiado ("…para a área
de transferência")→"✅ Ligação copiada. Já a podes colar." (share.js,
constante+docstring) e "✓ Texto copiado. Já o podes colar."
(gerador-documentos.js) — só strings, zero lógica; glosa "É o salário
bruto, antes dos descontos." no texto de ajuda do campo de remuneração do
simulador de subsídio de desemprego; glosa "(a aprovação do pedido)" na
1.ª ocorrência visível de "deferimento" em pagamento-apos-deferimento.html
(ocorrências seguintes ficam simples, por desenho); "formulário
electrónico dinâmico"→"formulário online" (visível; HowTo JSON-LD
intocado). Teste actualizado no mesmo commit: test_share_js.py (asserção
da mensagem de sucesso). Método: substituições exactas com guardrail de
"exactamente 1 ocorrência" — os 4 casos com duplicados (espelhos JSON-LD,
docstring) foram inspeccionados um a um antes de qualquer edição dirigida.
Suite completa: 2408 passed, 4 skipped (allow-list confirmada); ruff
limpo. Não alterado por decisão da auditoria: "online"/"site"/"email"/
"app"/"submeter candidatura", títulos oficiais, "Checklist" (achado
opcional, não aplicado). AUTO_UPDATE_HABILITADO/REVALIDACAO_CARIMBO_
HABILITADA não tocados.*

---

*Última revisão: 2026-07-16 — Sessão 1 (medição de conversão): instrumentação
de eventos GA4 para criar baseline antes de qualquer optimização — **zero
alterações de layout, homepage, Schema.org ou conteúdo**, só medição +
documentação. Nova secção "MEDIÇÃO DE CONVERSÃO — EVENTOS GA4" com a tabela
completa. 4 eventos implementados nos JS já existentes de cada
funcionalidade (nenhum `eventos.js` global criado): `simulacao_concluida`
(inline nos 6 simuladores publicados, a par do `calc_resultado` existente —
`elegivel` só onde há veredicto binário limpo: abono/ase/csi/subsidio_desemprego;
omitido em subsidio_doenca e rsi por não terem esse veredicto), `partilha_clique`
(`share.js`, nos dois pontos de sucesso — Web Share e clipboard —, `pagina`=pathname,
nunca no fallback manual nem em cancelamento), `comecar_aqui_percurso`
(`comecar-aqui.html`, início na 1.ª escolha + fim com `destino` recomendado) e
`cal_home_clique` (`index.html`, clique na barra `.cal-topo`). Todos com guarda
`typeof gtag === 'function'`; nenhum transporta dados do utilizador.

**`documento_gerado` deliberadamente NÃO feito** (decisão do Nuno via
AskUserQuestion): quebraria a invariante dura, documentada e testada, de
zero pedidos de rede do gerador de documentos ("os dados nunca saem do teu
dispositivo") — um ping GA4, mesmo cookieless em `denied`, é um pedido de
rede. `test_zero_pedidos_de_rede_ao_interagir_com_o_gerador` fica intacto;
novo `test_gerador_documentos_nunca_dispara_gtag` tranca a decisão.

Documentação (só texto): nota "HEADERS HTTP — LIMITAÇÃO ACEITE" (GitHub Pages
não permite headers personalizados; ACEITAR — site estático sem dados
pessoais; meta-CSP e Cloudflare avaliados e rejeitados; reavaliar só se
passar a recolher dados) e o lembrete do passo manual do Nuno (marcar
`simulacao_concluida` e `comecar_aqui_percurso` final como key events no GA4 —
não é possível por código).

Testes: `tests/test_eventos_ga4.py` (novo, 26 casos — asserções sobre o fonte,
portáteis sem Playwright: guarda `typeof gtag`, slug/parâmetro certos,
varrimento global anti-dados-pessoais) + 5 testes funcionais Chromium novos em
`tests/test_share_js.py`. Nenhuma lógica de cálculo dos simuladores tocada
(golden tests reconfirmados sem regressão). Suite completa + `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpos.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False`
(inalterados — não é scraper). Trabalho na branch
`claude/ga4-conversion-events-cxq9io` (designada pelo ambiente remoto).*

---

*Última revisão: 2026-07-16 — Sessão 2 (Schema.org cirúrgico): três
intervenções ao nível do grafo do site, **sem tocar no JSON-LD dos artigos**
(está correcto) nem adicionar tipos especulativos — ver nova secção
"SCHEMA.ORG — GRAFO DO SITE". (1) `WebSite` consolidado na homepage: ganhou
`@id` (`https://tensdireito.com/#website`) e `publisher` → `Organization` da
NV Labs por `@id`; o `SearchAction` já existia e o seu target
(`?pesquisa={search_term_string}`) foi **verificado** — `index.html` já lê
`?pesquisa=` no `DOMContentLoaded` e corre a pesquisa do hero, por isso não
foi preciso página de pesquisa nova nem tocar na homepage além deste bloco.
Decisão da Tarefa 1 ponto 3 = **opção (a)**: `WebSite` removido de
`sobre.html` (fica só `AboutPage` + `Organization`) — um único `WebSite` no
site, nunca dois com `@id` diferentes. A linha `"dateModified"` do bloco
(actualizada pelo `sed` do pipeline, Step 6) foi preservada intacta. (2)
`CollectionPage` + `ItemList` nas 6 pillar pages (5 em `p/*.html` +
`prestacao-social-unica.html`), gerado de `data/clusters.json` por
`render_pillar_jsonld()` em `scripts/sincronizar_clusters.py`, novo marcador
`<!-- PILLAR-JSONLD:INICIO/FIM -->` no `<head>` — idempotente, `--dry-run` ok,
1:1 com o JSON (`position` sequencial, URLs absolutos, `isPartOf` → `@id` do
`WebSite`); nunca escrito à mão. (3) Testes: `test_sincronizar_clusters.py`
estendido (injecção, idempotência, 1:1 em `tmp_path` e sobre os 6 pillars
reais, marcador em falta reportado sem escrever), `test_sobre_jsonld.py`
actualizado (WebSite mudou de `sobre.html` para a homepage),
`test_breadcrumb_coerencia.py` sem regressão. Todo o JSON-LD tocado validado
como JSON real; diff cirúrgico (index.html +2 linhas, sobre.html −9, pillars
só adição do bloco no `<head>`). Passo manual do Nuno: validar no Rich
Results Test / Search Console depois do deploy. Suite completa + `ruff` limpos.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` inalterados
(`False`). Trabalho directo em `main`.*

---

*Última revisão: 2026-07-16 — copy do banner de consentimento reescrita para
aumentar a taxa de aceitação, **por meios legítimos apenas** (RGPD). Contexto:
diagnóstico com o Nuno (Network + Console em produção) confirmou que os
eventos GA4 da Sessão 1 estão **correctos e deployed** — só não aparecem no
GA4 porque, em `denied` (banner por aceitar), o Consent Mode v2 envia o
`page_view` como ping de modelação mas **não** envia os eventos personalizados
como hits reais (`gtag('event',...)` manual só gerou `collect` depois de
forçar `analytics_storage:'granted'`). Não era bug — era estado de
consentimento. Para melhorar o baseline de conversão, o único lever ético é a
taxa de aceitação: `assets/js/consentimento.js` — texto do banner passou de
"Usamos cookies apenas para estatísticas anónimas…" para uma mensagem com
enquadramento de confiança ("Este site é gratuito e independente… nunca para
publicidade e nunca vendemos os teus dados. Só guardamos cookies se
aceitares, e podes mudar quando quiseres."). **Zero dark patterns**: os botões
"Aceitar"/"Rejeitar" mantêm os rótulos exactos (exigidos por
`tests/test_consentimento.py`), ambos a **um clique** e igualmente
alcançáveis — recusar continua tão fácil como aceitar (requisito RGPD);
banner não-bloqueante, sem nag, sem pré-selecção. Verificado: 132 testes de
`test_consentimento.py` a passar (comportamento de consentimento intacto),
axe sem violações com o banner visível, 0px de overflow a 375px, rótulos dos
botões confirmados. **Sinalizado para revisão do Nuno** — é copy com
implicações RGPD (mesmo tratamento de `privacidade.html`): a palavra
"anónimas" foi mantida por consistência com o texto anterior, mas a redação
legal exacta é decisão dele. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` não tocados. Trabalho directo em `main`.*

---

*Última revisão: 2026-07-16 — correcção pontual ao JSON-LD `Organization` da
NV Labs em `sobre.html`: `url` estava a apontar para `sobre.html` (a própria
página institucional), corrigido para a raiz do site
(`https://tensdireito.com/`) — o `url` de uma `Organization` representa a
entidade, não a página onde é descrita; o `AboutPage.url` continua
correctamente `sobre.html` (é a página). Pedido também um campo `logo`
(`assets/img/logo-nvlabs.png`, 512×512) — **não adicionado**: o ficheiro não
existe no repositório (só há `favicon.svg`, ícone do site, não logótipo da
NV Labs); adicioná-lo seria uma referência inventada que a Google tentaria
buscar e receberia 404, piorando a validação estruturada em vez de a
melhorar — contra a regra "nunca inventar factos/URLs". Adiado por decisão
do Nuno; gatilho registado: se um logo real da NV Labs for criado (ex.: pelo
mesmo método de `scripts/gerar_og_images.py`, Chromium real a partir da
marca existente), acrescentar o campo `logo` (`ImageObject` com
`url`/`width`/`height`) ao bloco `Organization`. `tests/test_sobre_jsonld.py`
reconfirmado sem regressão (nenhum teste fixava o `url` antigo). `ruff` não
aplicável (zero `.py` alterados).*

---

*Última revisão: 2026-07-18 — nova página `renovar-cartao-cidadao.html`,
7.ª página do cluster `como-pedir`, activando o card "Renovar o Cartão de
Cidadão" que estava marcado `Brevemente` em `p/como-pedir.html`. Fact-check
via `WebSearch` (`WebFetch` continua bloqueado nesta sessão — 403 em
`justica.gov.pt`/`gov.pt`, mesma limitação documentada em sessões
anteriores; triangulado por múltiplas pesquisas independentes por facto,
nunca uma fonte só) contra justica.gov.pt, irn.justica.gov.pt e gov.pt:
preços (presencial 18,00 €/15,00 € consoante ≥25 ou <25 anos; online só a
partir dos 25 anos, com desconto de 10% = 16,20 €; urgente 33,00 €/30,00 €;
muito urgente, só Lisboa/Porto, 53,00 €/50,00 €; serviço externo +40,00 €
+40,00 € se entrega em casa); prazos (em média 7 dias úteis ao balcão, até
30 dias com entrega em casa via CTT); renovação automática por carta com
código PIN, 60 dias antes da caducidade, só para quem tem 25+ anos e não
muda dados impressos; validade por idade (5 anos até aos 25, com recolha
presencial obrigatória de biometria a cada renovação; 10 anos a partir dos
25); janela de pedido de 6 meses antes da caducidade; cartão caducado só
renova presencialmente.

**Achado mais relevante da sessão, genuinamente urgente à data de
publicação**: o Regulamento (UE) 2025/1208 (novas normas de segurança para
documentos de identificação europeus) obriga a renovar **até 3 de agosto de
2026** — a menos de 3 semanas da verificação — os Cartões de Cidadão sem
zona de leitura ótica (MRZ, a faixa de caracteres no verso), mesmo que a
validade impressa seja posterior; cartões com MRZ mas sem chip de contacto
(emitidos entre 13 de agosto de 2021 e 9 de junho de 2024) só são válidos
até 3 de agosto de 2031, também independentemente da validade impressa; só
os cartões emitidos a partir de junho de 2024 seguem sempre a validade
impressa. Triangulado por múltiplas fontes jornalísticas independentes mais
o próprio aviso do IRN/gov.pt ("Cartão de Cidadão é válido até à data
impressa no documento", que também confirma a excepção). Dado o carácter
urgente e a origem só em fontes secundárias para o detalhe fino (o texto do
Regulamento em si não foi acedido directamente), a página trata o facto com
cautela — cita o Regulamento e a data, mas remete sempre para gov.pt/IRN
para confirmação do caso concreto do leitor, nunca afirma categoricamente
uma excepção não verificada em fonte primária.

Estrutura pedida: `.resposta-rapida` (60 palavras exactas, dentro do
limite) + secções "Quando renovar" (com o aviso do prazo de 2026/2031
destacado, `.aviso-atencao`), "Renovação automática", "Renovação online",
"Renovação presencial" (tabela de situações), "Preços e prazos" (tabela
completa) + `.checklist-final` (6 itens) + FAQ de 8 perguntas (`<details>` +
JSON-LD `FAQPage`, 1:1 confirmado) + `HowTo` (6 passos) + `BreadcrumbList` +
`Article`. Copiada a estrutura base de `alterar-morada.html` (sibling mais
recente do mesmo cluster `como-pedir`, publicada no dia anterior — melhor
correspondência estrutural do que `amim.html`/`cuidador-informal.html`,
sugeridas no pedido original mas de um padrão de página mais antigo) —
`data-ga4` continua lido do atributo do `<script>` de `consentimento.js`,
zero IDs hardcoded, mesmo padrão do resto do site.

Integração: `data/clusters.json` (7.ª página do cluster `como-pedir`, sem
alterar `oculta_em_apoios`), `scripts/sincronizar_clusters.py` corrido com
sucesso — actualizou automaticamente `index.html` (`ATUALIZACOES:HOME`) e
`p/como-pedir.html` (`PILLAR-LISTA` + `PILLAR-JSONLD`, `numberOfItems`
6→7); os blocos `CLUSTER-BADGE`/`RELACIONADOS` da própria página nova
(escritos à mão) confirmados **idênticos** ao que o script geraria —
idempotência provada antes do commit (2.ª corrida de
`sincronizar_clusters.py` = zero alterações). `scripts/sincronizar_nav.py`,
`scripts/adicionar_canonicas.py`, `scripts/adicionar_autoria_artigos.py` e
`scripts/inserir_botao_partilhar.py` confirmados todos a **zero
alterações** — a página já nasceu com nav, canónica, autoria e botão de
partilha correctos. `scripts/adicionar_article_jsonld.py` ganhou a entrada
`"renovar-cartao-cidadao.html": "2026-07-18"` em `DATAS_PUBLICACAO` e
confirmou o `Article` já escrito à mão como correcto. `scripts/
gerar_og_images.py --write` gerou a imagem própria (1200×630, confirmado
pelo cabeçalho JPEG real, chip "Como Pedir"). `sitemap.xml` e
`scripts/pesquisa.js` actualizados manualmente. Card do hub
`p/como-pedir.html` activado (badge `Brevemente` removido, link real para
`/renovar-cartao-cidadao.html`).

**Achado real, apanhado só pela suite completa (não pelos testes
parametrizados sobre páginas reais que costumam cobrir uma página nova
automaticamente)**: `tests/test_urls_como_pedir.py` — canário dedicado do
cluster `como-pedir` (`data/urls_como_pedir.json`, verificado contra a rede
só em CI via `scripts/verificar_urls_como_pedir.py`), criado numa sessão
anterior sem qualquer menção neste ficheiro até agora — exige que **todo**
artigo do cluster tenha pelo menos um URL oficial configurado; a página
nova falhava por não ter entrada. Corrigido com 3 URLs de homepage (nunca
subpaths não confirmados, mesma regra de sempre): `justica.gov.pt`,
`irn.justica.gov.pt`, `gov.pt` — mesmo padrão (URLs de topo, não deep-links)
já usado nas entradas existentes de `senha-seguranca-social-direta.html`/
`chave-movel-digital.html`/`alterar-morada.html`.

**Gap de documentação encontrado e parcialmente corrigido**: a criação do
cluster `como-pedir` (Fase 1, `p/como-pedir.html` + `senha-seguranca-social-
direta.html` + `iban-seguranca-social.html` + `chave-movel-digital.html` +
`como-pedir-niss.html` + `declaracao-situacao-contributiva.html` +
`alterar-morada.html`, publicadas entre 14 e 18 de julho de 2026, confirmado
por `git log`) nunca tinha sido registada na tabela "PÁGINAS PUBLICADAS"
deste ficheiro nem tinha entrada de "Última revisão" própria — corrigido só
a tabela (5 linhas em falta acrescentadas com título e data reais, extraídos
dos `<title>` publicados), sem reconstruir retroactivamente o resto do
histórico dessas sessões (fora do âmbito desta tarefa). Nova linha em
"PÁGINAS COM DATAS SAZONAIS": `renovar-cartao-cidadao.html` deve ser
revista depois de 3 de agosto de 2026 — `verificar_datas.py` confirmado a
**não** disparar em 2026 (padrão `data_mes_ano` sobre "3 de agosto de 2026"
fica `OK` enquanto o ano corrente é 2026) mas a disparar em 2027 nos meses
1/7/8/9, comportamento desejado (mesma lógica de `prova-escolar.html`/
`calendario-escolar-apoios.html`) — força rever se o aviso "Prazo a não
perder" ainda faz sentido depois da data passar.

Verificado: 4 blocos JSON-LD válidos (`json.loads`), 8 perguntas FAQ
1:1 entre `<details>` visíveis e JSON-LD, `.resposta-rapida` com
exactamente 60 palavras, checklist com 6 itens ("0 de 6"), zero páginas
órfãs (linkada do hub, do `RELACIONADOS` automático, e de 3 cross-links
manuais). `html5validator`/`vnu.jar` não instalável neste sandbox (mesmo
erro de build `install_layout`/`setuptools` do sistema, documentado em
várias sessões anteriores) — validado por leitura estrutural (parse real
via BeautifulSoup, sem erros) em vez de `vnu.jar`; validação HTML5 completa
fica para o CI (`integridade.yml`), como já acontecia noutras sessões com a
mesma limitação de sandbox. Suite completa: **2628 passed, 4 skipped, 0
failed** (a falha real do canário de URLs foi corrigida antes desta
contagem final, não escondida). `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados por
esta sessão). Trabalho na branch
`claude/cartao-cidadao-renewal-guide-i861no` (designada pelo ambiente
remoto desta sessão) — **SEM PR, branch não integrada em `main`** (protocolo
de fim de sessão desta secção "REGRA ABSOLUTA — GIT").*

---

*Última revisão: 2026-07-18 (sessão seguinte, revisão cruzada +
correcção factual) — duas tarefas sobre o cluster "Como Pedir". 1)
Revisão cruzada dos 3 guias novos (`alterar-morada.html`,
`renovar-cartao-cidadao.html`, `numero-utente-sns.html`): fact-check
via `WebSearch` sem divergências nos preços do CC, prazo de 60
dias/coima de alteração de morada e nos números de utente; corrigida
uma divergência de texto entre o `<summary>` visível e a pergunta do
`FAQPage` JSON-LD em `renovar-cartao-cidadao.html`; adicionados os 3
cross-links em falta entre as páginas (o mecanismo automático
`RELACIONADOS`, limitado aos 4 primeiros irmãos do cluster, nunca os
cobriria — são as páginas #6/#7/#8 de 8); registado em `ROADMAP.md` o
gatilho pós-3-agosto-2026 que já existia em `CLAUDE.md` mas faltava no
índice único. Sinalizada, sem editar, uma dúvida sobre o alcance exacto
do prazo de 2031 para confirmação manual do Nuno. 2) **Correcção
factual da mesma dúvida**, com fonte primária via imprensa
(esclarecimento oficial do IRN de 30/12/2025): o prazo de "3 de agosto
de 2026" do callout "Prazo a não perder" **nunca se aplicou** ao Cartão
de Cidadão normal — o CC português tem MRZ desde 2007, e a categoria
"sem MRZ" só afecta duas excepções raras (Cartão de Cidadão de cidadãos
brasileiros ao abrigo do Tratado de Porto Seguro, e o antigo Bilhete de
Identidade vitalício, emissão cessada a 31/12/2018); a linha "emitido
entre 13 de agosto de 2021 e 9 de junho de 2024" da categoria
"MRZ mas sem chip de contacto" também estava incorrecta — o intervalo
certo é "emitido até 10 de junho de 2024", o prazo real remanescente é
3 de agosto de 2031. Corrigidos, em `renovar-cartao-cidadao.html`: o
callout do hero (de `.aviso-atencao` alarmista para `.aviso-info` com
"✅ Esclarecimento oficial"), a lista de 3 categorias da secção "Preciso
de renovar antes do prazo?", a pergunta/resposta correspondente no
`FAQPage` JSON-LD e no `<summary>` visível (mantidos idênticos entre
si), e a entrada de "PÁGINAS COM DATAS SAZONAIS" logo acima —
despromovida de "revisão obrigatória pós-3-agosto-2026" para "nota de
verificação para 3 de agosto de 2031, sem gatilho de acção" (mesma
mudança espelhada em `ROADMAP.md`). Regulamento (UE) 2025/1208 mantido
como referência correcta (substitui o quadro de 2019). Nenhum outro
facto da página tocado — os preços, prazos de renovação e passo a
passo permanecem exactamente como estavam, já confirmados na revisão
anterior.

**Achado lateral durante a verificação, corrigido no mesmo commit**: ao
testar `verificar_datas.detectar_alertas()` sobre o texto corrigido,
descoberto um falso positivo real e **pré-existente** (já presente
desde a criação da página, 2026-07-18, antes de qualquer edição desta
sessão) — as datas "13 de agosto de 2021"/"9 de junho de 2024" da
categoria "MRZ mas sem chip de contacto" nunca tinham marcador de
supressão, disparando `data_mes_ano` já em julho de 2026 (o mês
corrente), não só em 2027. As novas datas históricas desta correcção
("dezembro de 2025", "30/12/2025") agravavam o mesmo problema.
`MARCADORES_HISTORICOS` (`scripts/verificar_datas.py`) ganhou 3
marcadores novos, cada um ancorado à ocorrência real que o motivou,
mesmo padrão das correcções #51/#52/#53 já documentadas: datas de
emissão de documento (`emitidos? entre/até/a partir de`), citações de
quando uma notícia circulou (`circularam notícias`), e citações de
quando um esclarecimento oficial foi emitido (`esclarecimento
(oficial) de \d`) — confirmado sem colisão com nenhum outro match de
data no resto do site antes de aplicar (grep dedicado + varrimento real
de `manuais-escolares-mega.html`, o único outro ficheiro com "emitidos
entre/até/a partir de"). Confirmado por varrimento site-wide real
(`detectar_alertas()`, 70 páginas, mês 7/2026): **0 alertas**, nenhum
falso positivo residual. O disparo em 2027 que persiste (tipo
`data_numerica`) é o mecanismo universal e desejado de qualquer página
do site — o carimbo "Verificado a 18/07/2026" envelhece como qualquer
outro, força revisão anual, não é um bug.

Verificado depois da correcção: os 4 blocos JSON-LD
continuam válidos, o `FAQPage` continua 1:1 com os `<summary>`
visíveis (8/8), zero overflow a 375px, zero erros de consola, 0
violações de acessibilidade nas 3 páginas tocadas na sessão. Suite
completa: **2655 passed, 4 skipped** (allow-list de skips confirmada
elemento a elemento); `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados).
Trabalho directo em `main` (commits `d50d81b` e o desta correcção).*

---

*Última revisão: 2026-07-18 (sessão seguinte) — removido o
`potentialAction` (`SearchAction`) do bloco `WebSite` JSON-LD de
`index.html`, disparado pelo GSC a reportar
`https://tensdireito.com/?pesquisa={search_term_string}` como "Rastreada
— atualmente não indexada": a Google descontinuou a sitelinks search box
em outubro de 2024, o markup já não tinha função e só gerava uma URL
fantasma nos relatórios de cobertura. Confirmado antes de mexer: nenhum
script gera este bloco (é escrito à mão em `index.html`, só validado por
`tests/test_sobre_jsonld.py` — nada a corrigir "na origem" além do
próprio HTML); a funcionalidade de pesquisa em si (`?pesquisa=`, lida no
`DOMContentLoaded`, e `scripts/pesquisa.js`) é independente do markup e
confirmada intacta com Chromium real (`?pesquisa=abono` continua a
preencher o campo e a mostrar resultados); o `canonical` da homepage já
apontava para `https://tensdireito.com/` sem query params, absorvendo
qualquer variante `?pesquisa=...` rastreada — nada a corrigir aí. Secção
"SCHEMA.ORG — GRAFO DO SITE" actualizada para reflectir o estado actual
(histórico do porquê ter sido adicionado a 2026-07-16 preservado, não
apagado); `tests/test_sobre_jsonld.py` — removida a asserção do
`SearchAction`, nova `test_homepage_website_ja_nao_tem_searchaction`
tranca a ausência. Suite completa + `verificar_skips_permitidos.py`
confirmados antes do commit; `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
não é scraper). Trabalho directo em `main`.*

---

*Última revisão: 2026-07-18 (sessão seguinte) — actualização de milestone
do cluster PSU: o Presidente da República promulgou, a 17 de julho de
2026, a autorização legislativa que permite ao Governo aprovar o
decreto-lei da PSU. Factos confirmados via `WebSearch` antes de qualquer
edição (PASSO 0 — Observador, ECO, Executive Digest, Jornal Económico,
RTP, DN, sem divergências): autorização válida por 120 dias; valores e
condições de acesso terão agora de ser fixados directamente pelo
decreto-lei — **não** por portaria, como o Governo previa a princípio —
o que sujeita o diploma a mais escrutínio (promulgação obrigatória do PR,
possível apreciação parlamentar); prazo PRR de 31 ago 2026 mantém-se
inalterado, dentro da janela dos 120 dias; regime transitório confirmado
com isenção de IRS mantida para quem já recebe qualquer um dos 13 apoios.

**Achado factual corrigido nesta sessão** (não introduzido por ela — a
página `psu-quem-tem-direito.html` já dizia, desde 1 jul 2026, que o
coeficiente CIT seria fixado por portaria separada do Valor de
Referência): confirmado por triangulação que essa distinção deixou de
ser verdade — ambos passam a ser fixados pelo mesmo decreto-lei. Corrigido
nas 2 páginas onde a frase aparecia (`psu-quando-entra-em-vigor.html`,
`psu-quem-tem-direito.html`).

Actualizadas as 6 páginas do cluster (pillar + 5 filhas): badge/hero/
alerta-crítico/timeline em `psu-quando-entra-em-vigor.html` (item novo de
17 jul na timeline, 2 FAQs novas) e `prestacao-social-unica.html` (idem);
reforço do regime transitório (isenção de IRS explícita) em todas as
menções a "quem já recebe" das 6 páginas; FAQ nova sobre a promulgação
em `psu-quem-tem-direito.html`, `psu-lista-13-apoios.html` e
`psu-trabalho-social.html`; `psu-vs-abono-familia.html` só actualizada na
célula "Estado em 2026" da tabela comparativa (a exclusão do Abono não é
afectada por esta milestone). `dateModified` do `Article` JSON-LD e
"Verificado a" avançados para 18/07/2026 nas 6 páginas.

**Achado lateral corrigido, pré-existente e sem relação com a milestone**:
`psu-trabalho-social.html` tinha uma pergunta visível ("Também posso ser
chamado se não for eu a pedir a PSU?") sem par no `FAQPage` JSON-LD desde
a publicação (3 jul 2026) — descoberto ao verificar programaticamente a
paridade 1:1 entre `<details>` visíveis e `Question` do JSON-LD nas 6
páginas tocadas (prática já seguida noutras sessões deste ficheiro).
Corrigido acrescentando a pergunta em falta ao JSON-LD, já agora com a
pergunta nova da promulgação a seguir.

**Scraper `dre_psu` verificado, não alterado**: o padrão de detecção
(`_detectar_decreto_psu()`, regex `\bdecreto[\s-]?lei\s+n`) já cobre
qualquer decreto-lei nos resultados da pesquisa de frase exacta
`"prestação social única"` — corrigido e testado numa sessão anterior
(2026-07-07, Issue #54). `dre_psu` está em `SLUGS_MONITORIZADOS`
(`gerir_estado_fontes.py`) e confirmado `OK` (`data/estado_fontes.json`,
`ultima_ok: 2026-07-18`). `pipeline-diario.yml` corre por cron diário
(`0 6 * * *`) sem data-limite — cobre a janela ago-nov 2026 (e qualquer
mês seguinte) sem precisar de nenhuma alteração. Nada a corrigir aqui.

Gatilho de alta prioridade reforçado em `ROADMAP.md` → "Automáticos": a
linha "Decreto-lei da PSU publicado" passa a assinalar a janela de 120
dias e a apontar, sem ambiguidade, para uma sessão imediata de valores +
activação do `simulador-psu.html` assim que a Issue automática disparar.
Corrigida também a contagem de páginas do cluster citada nessa linha (4→5
filhas) e na linha "Agosto 2026" da tabela "DATAS FIXAS".

Suite completa: **2656 passed, 4 skipped** (allow-list de skips
confirmada elemento a elemento, sem alteração); os 4 blocos JSON-LD de
cada uma das 6 páginas confirmados como JSON válido (`json.loads`) e a
paridade 1:1 FAQ↔JSON-LD confirmada nas 6. `ruff check scripts/ tests/
--select E,F,W --ignore E501 .` limpo (nenhum `.py` alterado nesta
sessão). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados). Trabalho feito na branch
`claude/psu-cluster-legislative-update-8rj5ca` (designada pelo ambiente
remoto desta sessão) — **SEM PR, branch não integrada em `main`**
(protocolo de fim de sessão desta secção "REGRA ABSOLUTA — GIT").*

---

*Última revisão: 2026-07-18 (sessão seguinte) — pedido para criar
`calendario-pagamentos-seguranca-social.html` como página nova; PASSO 0
revelou que **já existe por inteiro** desde 2026-07-12 (JSON de dados,
scraper, workflow mensal, canário de frescura próprio, agosto 2026 já
raspado e publicado) — nada recriado, sessão tornou-se auditoria de gaps
contra o novo pedido em vez de greenfield. Único gap real confirmado:
**cross-link PSU inexistente** junto às prestações abrangidas (só havia o
link genérico da nav) e **FAQ com 5 perguntas, pedido exigia ≥6** sem
pergunta dedicada a mudança de IBAN. Corrigidos os dois, mais um terceiro
achado durante a auditoria: a batch de pagamento "desemprego, doença,
parentalidade e ação social" nunca tinha linha própria para parentalidade
na tabela "Quando recebo a minha prestação?" (só desemprego/doença) — zero
visibilidade para quem recebe um subsídio parental, apesar de a própria
Segurança Social nomear a batch incluindo "parentalidade".

Cuidado arquitectural central desta sessão: a zona `CAL:CORPO` da página é
regenerada por `scripts/atualizar_calendario.py` a cada corrida do
`calendario-mensal.yml` (dia 1, 25, 28) — qualquer adição manual dentro
dela seria apagada silenciosamente na próxima regeneração. O cross-link
PSU e a linha de parentalidade foram implementados **dentro do próprio
gerador** (`PSU_NOTAS`, novo item em `VISTA_PRESTACOES`), nunca como
edição manual do HTML — sobrevivem a qualquer regeneração futura, mesmo
princípio da REGRA DE OURO aplicado a uma zona de página em vez de um
ficheiro inteiro. A 6.ª FAQ e o `dateModified`/"Verificado a" vivem fora
dessa zona, hand-editados em segurança.

**Escopo do cross-link PSU, decidido por verificação, não por lista
literal do pedido**: aplicado só às 4 linhas cujo regime não-contributivo
está confirmado nos 13 apoios (RSI, pensão social, subsídio social de
desemprego, subsídios sociais de parentalidade) — nunca aos respectivos
regimes contributivos, que a PSU não toca. CSI ficou de fora apesar de o
pedido dizer "CSI se aplicável": confirmado contra `prestacao-social-unica.html`
que o CSI está **explicitamente excluído** da PSU (audição parlamentar) —
"se aplicável" não se aplica. PSI também ficou de fora: a sua inclusão/
exclusão na lista final continua por confirmar pelo decreto-lei (ver
"IMPACTO DA PSU", plano de acção, ponto 9) — nunca afirmar o que ainda não
está fechado.

**Achado factual corrigido antes de publicar**: a 1.ª versão da FAQ do
IBAN inventou um caminho de navegação errado ("Dados Pessoais → Dados
Bancários") e um mecanismo não verificado (conversão automática para vale
de correio ao falhar a transferência) — nenhum dos dois está confirmado
em `iban-seguranca-social.html`. Corrigido para o caminho real e
verificado nesse guia ("Segurança Social Direta → Perfil → Conta
Bancária") e removida a alegação sem fonte.

Cross-link recíproco acrescentado a `subsidio-parental.html` (mesmo
padrão "📅 Em que dia do mês é pago?" já usado nas outras 7 páginas de
prestações) — só fazia sentido depois de a linha "parentalidade-social"
passar a existir na tabela.

Verificado antes do commit: `verificar_datas.detectar_alertas()` sem
falsos positivos nas 2 páginas tocadas; paridade 1:1 FAQ↔JSON-LD (6/6);
JSON-LD válido; idempotência do gerador confirmada (2.ª corrida = zero
alterações); axe sem violações críticas/sérias nas 2 páginas (incluindo o
novo azul `#1E40AF` do `.cal-psu-nota`); 0px de overflow a 375px com
Chromium real; zero erros JS; suíte dedicada
(`test_calendario_frescura.py` + `test_scraper_calendario.py`, 36 testes)
e os ficheiros de higiene/breadcrumb/nav/pesquisa/og/valores-ancora/anos/
clusters (1344 testes) confirmados sem regressões antes da suite
completa. Suite completa: **2656 passed, 4 skipped** (allow-list
inalterada); `ruff check scripts/ tests/ --select E,F,W --ignore E501 .`
limpo. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados — nenhuma das duas flags tocada).
`ROADMAP.md` não precisou de alteração — o gatilho automático mensal já
estava documentado com precisão desde 2026-07-12. Trabalho directo em
`main`.*

---

*Última revisão: 2026-07-18 (sessão seguinte) — resolvida a pendência
PSI vs PSU, fechada antes do decreto-lei (ver nova secção "PENDÊNCIA PSI
vs PSU — FECHADA" em "IMPACTO DA PSU" para o raciocínio completo). Factos
verificados pelo Nuno (lista oficial via ECO + proposta do Governo + Guia
Prático do ISS da PSI): a PSI não consta da lista dos 13 apoios da PSU —
o perímetro foi fixado pela autorização legislativa promulgada a
17/07/2026, o decreto-lei só regulamenta os 13 já listados, não os pode
alargar. Diferente do CSI (exclusão explícita, confirmada em audição
parlamentar), a PSI fica de fora por omissão — nunca escrever como
sinónimos. Nuance central: a lista inclui a "pensão social de invalidez
especial" (prestação #2), prestação distinta da PSI (que a substituiu só
para novos requerentes desde 2017, DL 126-A/2017) — confusão real já
detectada em sites de finanças pessoais.

Alterações: `scripts/atualizar_calendario.py` (comentário junto a
`PSU_NOTAS` reescrito, fechando a pendência que antes dizia "PSI ainda
não tem inclusão/exclusão confirmada" — "psi" nunca deve ganhar entrada
nesse dicionário; zero alteração de HTML gerado, confirmado por
`--dry-run`); `psu-lista-13-apoios.html` (novo `.aviso-info` a seguir à
lista dos 13 apoios com a desambiguação); `prestacao-social-unica.html`
("O que NÃO integra a PSU" ganhou um parágrafo sobre a PSI, ao lado do
CSI, com a distinção de força probatória); `prestacao-social-para-a-inclusao.html`
(§7 reescrita — já não trata a exclusão como provisória à espera do
decreto-lei; FAQ da PSU actualizada, não duplicada, apesar de o pedido
sugerir uma pergunta "nova" — já existia uma quase-idêntica desde a
publicação, actualizar em vez de duplicar evita conteúdo quase-repetido;
checklist final deixou de sugerir "acompanhar o decreto-lei").

**Achado lateral, pré-existente e sem relação com esta sessão**: a FAQ
visível "A PSI conta como rendimento para o IRS?" não tinha par no
`FAQPage` JSON-LD desde a publicação (4 jul 2026) — descoberto ao
verificar programaticamente a paridade 1:1 (mesma disciplina já seguida
em sessões anteriores para `psu-trabalho-social.html`). Corrigido
acrescentando a pergunta em falta ao JSON-LD.

Verificado antes do commit: `verificar_datas.detectar_alertas()` sem
falsos positivos nas 3 páginas tocadas; os 3 blocos JSON-LD de cada
página válidos (`json.loads`); paridade 1:1 FAQ↔JSON-LD confirmada nas 3
(6/6, 6/6, 12/12); axe sem violações críticas/sérias; suíte de
higiene/breadcrumb/nav/pesquisa/og/valores-âncora/anos/clusters/
calendário (1380 testes) e suite completa confirmadas sem regressões.
Suite completa: **2656 passed, 4 skipped** (allow-list inalterada);
`ruff check scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — nenhuma das duas flags tocada). Trabalho directo
em `main`.*

---

*Última revisão: 2026-07-19 — infra-estrutura de dados abertos, 3 fases
incrementais (git scraping/`dados/observacoes/`, parâmetros legais em
YAML no padrão OpenFisca migrando o CSI, publicação SQLite +
`dados.html` com Datasette Lite). Ver secção "DADOS ABERTOS — GIT
SCRAPING, PARÂMETROS OPENFISCA E PUBLICAÇÃO (FASES 1-3)" para o detalhe
completo. Suite local completa: **2702 passed, 4 skipped, 0 failed**
(527s); `ruff check scripts/ tests/ --select E,F,W --ignore E501`
limpo. **PR #69** (aberto contra `main`) — CI real ("Integridade do
Código") confirmado verde nos 6 jobs aplicáveis (Suite de Testes,
Ruff, pip-audit, Gitleaks, Validação HTML, Prompt Injection); o 7.º
job (canário de URLs oficiais externas) salta correctamente em eventos
`pull_request`, por desenho. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
nenhuma das duas flags tocada; esta sessão não é scraper). Trabalho
feito na branch `claude/new-session-kmnkvb` (designada pelo ambiente
remoto desta sessão) — **PR: #69 (aberto, CI verde, ainda não merged)**.*

---

*Correcção PASSO 0 ao PR #69 (2026-07-19, mesma sessão) — o Nuno
verificou os 4 valores de `dados/parametros/csi.yaml` contra fontes
oficiais antes do merge e encontrou 3 problemas reais na 1.ª migração
desta sessão: os diplomas citados estavam errados (Decreto-Lei n.º
126-A/2017 é a lei base da PSI, nunca fixa valores do CSI de 2026 —
substituído por Portaria n.º 480-D/2025/1 + Decreto-Lei n.º 232/2005
para o valor individual, e Decreto-Lei n.º 35/2024 para o coeficiente
1,75 do casal); a idade mínima estava simplificada a "66 anos"
completos, um **bug real** — a idade normal de acesso em 2026 é 66
anos e **9 meses** (Portaria n.º 358/2024/1), e comparar só anos dava
falso-elegível a alguém com, por exemplo, 66 anos e 3 meses; e o
parâmetro `percentagem_rendimento_trabalho` (80%) não tinha citação
legal primária confirmada.

Corrigido: `dados/parametros/csi.yaml` com as referências correctas
(diplomas + URLs reais do diariodarepublica.pt, confirmados por
`WebSearch` nesta sessão — nunca inventados); o parâmetro de idade
passou de `idade_minima_anos` (valor 66) para `idade_minima_meses_totais`
(valor 801 = 66×12+9) — correcção substantiva, não só de metadados.
`simulador-csi.html` reescrito em conformidade: formulário ganhou um
2.º campo (`idadeMeses`, 0-11) ao lado da idade em anos;
`calcularCSI()` compara `idadeTotalMeses >= idadeMinimaMesesTotais`;
rendimentos de trabalho passam a contar a 100% (percentagem_rendimento_trabalho
removido — nem a verificação do Nuno nem uma pesquisa independente
desta sessão via `WebSearch` encontraram base primária para os 80%
especificamente no CSI). Todo o texto visível e JSON-LD do simulador
que ainda citava "80%" ou o diploma errado foi actualizado a par
(formula-box, FAQ visível + `FAQPage` JSON-LD, disclaimer de
independência) — nunca deixado a descrever uma regra que o código já
não aplica.

**Discrepância encontrada e registada, não resolvida nesta correcção**:
o artigo já publicado `complemento-solidario-idosos.html` (linha ~427)
continua a afirmar "Rendimentos de trabalho dependente ou independente
— 80% do valor declarado" na sua tabela de rendimentos, um facto
fact-checked numa sessão anterior (25/06/2026). Nem a verificação do
Nuno nem esta sessão confirmaram essa percentagem contra uma fonte
primária — fica como uma inconsistência real entre o artigo e o
simulador, sinalizada aqui para decisão numa sessão dedicada (confirmar
a fonte do artigo, ou corrigi-lo também) — este ficheiro não foi
tocado por não ter sido pedido e por estar fora do âmbito desta
correcção específica ao PR.

Golden tests reescritos com casos de fronteira reais em meses totais
(66a8m = 800 meses, inelegível; 66a9m = 801 meses, elegível) e um teste
de regressão de ponta-a-ponta (Chromium real, 66 anos e 3 meses tem de
mostrar "Ainda sem direito por idade" na UI, não um resultado
positivo). `tests/test_valores_ancora.py` actualizado com o mesmo
raciocínio + um teste que tranca a remoção do parâmetro de 80% (nunca
reaparece sem confirmação). Suite completa reconfirmada localmente
sem regressões; `ruff` limpo. Push mantido no mesmo branch
`claude/new-session-kmnkvb`, sem merge — o merge continua a ser feito
manualmente pelo Nuno.*

---

*Fecho da questão dos 80% (2026-07-19, mesma sessão) — o Nuno encontrou
a fonte primária que faltava: Guia Prático 8002 do ISS, I.P.
("Complemento Solidário para Idosos", v4.53, 21/05/2026), secção C1.1,
lista os rendimentos considerados (trabalho dependente bruto incl.
subsídios de férias e Natal, trabalho independente, capitais,
prediais, incrementos patrimoniais, pensões e complementos, património
mobiliário/imobiliário excepto habitação própria) sem nenhuma regra de
80% — confirma que o simulador (já corrigido para 100% na correcção
anterior) estava certo; era o artigo publicado que estava errado.

`complemento-solidario-idosos.html` corrigido: tabela "O que conta (e
o que não conta) para o cálculo" alinhada com a categorização da
secção C1.1 (trabalho dependente/independente separados, rótulos
"rendimentos de capitais"/"rendimentos prediais"/"incrementos
patrimoniais" a bater com a nomenclatura do Guia), 80% removido. O
mesmo erro de diploma encontrado antes no simulador (DL n.º 126-A/2017
citado como lei base do CSI — é a lei base da PSI) estava espalhado
por 5 sítios adicionais neste artigo (nota da tabela, 3 citações
`fonte-inline` de FAQ, bloco de fontes no fim da página) — todos
corrigidos para Decreto-Lei n.º 232/2005, com o Guia Prático 8002
acrescentado como fonte corroborante. `dateModified`/"Verificado a"
avançados para 19/07/2026 (facto corrigido, não só cosmético).

`dados/parametros/csi.yaml` ganhou `fonte_url_complementar` (opcional,
nunca substitui `referencia_legal`/`fonte_url`) nos 3 parâmetros,
apontando ao Guia Prático 8002 — propagado a `dados/parametros.json`
(`gerar_parametros_json.py`) e à tabela `parametros` de
`dados/tensdireito.db` (`gerar_base_dados.py`, nova coluna
`fonte_url_complementar`). O parâmetro `percentagem_rendimento_trabalho`
**não foi reintroduzido** — não há nenhuma percentagem de redução a
parametrizar quando a regra confirmada é "sem redução, 100% bruto".

Novo canário em `test_valores_ancora.py` (`test_percentagem_rendimento_trabalho_nunca_reaparece_sem_confirmacao`,
reescrito): "80%" nunca pode voltar a aparecer em nenhuma página do
CSI (`simulador-csi.html`, `complemento-solidario-idosos.html`), fora
de comentários `<script>` (documentação histórica legítima do que foi
removido e porquê, nunca uma afirmação activa ao utilizador — achado
real ao correr o teste pela 1.ª vez: a própria explicação em comentário
JS continha a substring "80%", falso positivo corrigido restringindo o
canário ao HTML/JSON-LD visível). Suite completa reconfirmada sem
regressões; `ruff` limpo. Sem merge — mantido no mesmo branch
`claude/new-session-kmnkvb`, revisão final e merge continuam a ser do
Nuno.*

---

*Última revisão: 2026-07-19 (sessão seguinte, "Parâmetros YAML +
auditoria factual") — Commits 1 e 2 do plano de migração: subsídio de
doença e abono de família passam para o padrão OpenFisca de
`dados/parametros/*.yaml`, mesmo princípio do CSI. Commit 3 (ASE)
**bloqueado** — exige o despacho anual da DGEstE com os escalões
2026/2027, ainda não fornecido/verificado pelo Nuno; registado como
pendência em `ROADMAP.md`, sem qualquer alteração a `simulador-ase.html`
nem `acao-social-escolar.html` nesta sessão.

**Cada prestação tratada como pacote completo**: YAML de parâmetros
(fonte primária citada — Guia Prático 5001/4001 do ISS, I.P., PDFs
oficiais já lidos pelo Nuno antes desta sessão, PASSO 0 cumprido) →
migração do simulador para `fetch('/dados/parametros.json')` em runtime
(nunca calcula com valores em falta — botão nasce `disabled`, estado de
carregamento visível "⏳ A carregar valores oficiais…", `#avisoParametrosErro`
se o fetch falhar) → auditoria das páginas publicadas dessa prestação
contra os mesmos dados verificados, com qualquer divergência corrigida
no mesmo commit (mesmo precedente do erro dos "80%" do CSI).

**Commit 1 — subsídio de doença**: `dados/parametros/subsidio-doenca.yaml`
(15 parâmetros: percentagens por escalão, tuberculose, majoração,
dias de espera, tectos de duração, piso diário mínimo). **Correcção real
encontrada**: o piso diário estava calculado sobre o IAS (30% × 537,13€ ÷
30 = 5,37€) — o Guia Prático 5001 (v4.55, 14/07/2026) fixa-o sobre a
Remuneração Mínima Mensal Garantida 2026 (920€, DL n.º 139/2025): 30% ×
920€ ÷ 30 = 9,20€. Um segundo piso (300€/325€ mensais quando a RR
mensal excedia 500€, marcado ⚠️B em sessões anteriores como
"interpretação conservadora" sem fonte primária confirmada) foi
**removido** — o Guia Prático descreve só um piso único, com a excepção
central desta correcção: se a RR diária da pessoa já for inferior a
esse piso, recebe a sua própria RR diária, nunca um valor superior ao
que realmente ganha (`aplicarPiso()`, nova função pura). Aplicado
uniformemente aos 4 escalões e à tuberculose. `baixa-medica-subsidio-doenca.html`
corrigida nos mesmos pontos (resumo rápido, secção "Garantia mínima" —
antes "Duas garantias mínimas" com o piso 300/325 já removido, JSON-LD
FAQ, fonte-bloco) — "5,37"/"300 €"/"325 €" nunca mais aparecem fora de
comentários `<script>` (trancado por
`tests/test_valores_ancora.py::test_piso_300_325_nunca_reaparece_sem_confirmacao`).
Não modelado, declarado na UI: prazo de garantia de 6 meses, índice de
profissionalidade de 12 dias, tecto de 100% da RR líquida (após
descontos) — já correctamente documentados no artigo, sem divergência
encontrada aí. `tests/test_simulador_subsidio_doenca_calculo.py`
reescrito (29 testes): casos golden recalculados à mão para o piso
9,20€ (incluindo o caso central `test_rr_diaria_abaixo_do_piso_paga_a_propria_rr_nunca_o_piso`,
salário=90€ → paga exactamente a RR diária de 3,00€, nunca 9,20€ nem
1,80€) e 2 testes de runtime real (fetch sucesso/falha) com
`http.server`, mesmo padrão do CSI.

**Commit 2 — abono de família**: `dados/parametros/abono.yaml` (17
parâmetros: 12 limites de RR por escalão × 3 cenários — nome do
parâmetro sufixado com o cenário, já que o esquema flat de
`gerar_parametros_json.py` não suporta agrupamento nativo —, 12 valores
mensais por idade, Garantia para a Infância ×2, majoração
monoparental, IAS 2026 de referência). Armadilha estrutural confirmada:
há **três cenários simultâneos** (a: manutenção/pedidos de 2025,
rendimentos de 2024, IAS 509,26€; b: pedidos novos em 2026, rendimentos
de 2025, IAS 522,50€ — cenário simulado por omissão, declarado
explicitamente na UI e na FAQ nova "Este simulador considera todas as
regras especiais do abono?"; c: reavaliações em 2026, rendimentos de
2026, IAS 537,13€) — os limites de RR por escalão mudam consoante o
cenário, os valores mensais por idade não. **Correcção real
encontrada**: o limite de elegibilidade da Garantia para a Infância
estava calculado com o IAS do ano corrente (0,35 × 537,13€ × 14 =
2.631,94€) — o Guia Prático 4001 (v4.80, 30/06/2026) fixa este cálculo
sempre com o IAS de 2024 (509,26€), nunca actualizado: 0,35 × 509,26€ ×
14 = 2.495,37€. Corrigido no simulador e em `abono-de-familia.html`
(JSON-LD FAQ + visível). **2.ª correcção real, encontrada só na
auditoria do artigo** (a tabela de acréscimos por família numerosa
nunca foi consumida pelo simulador — só documentada no artigo): a linha
do 4.º escalão, 2 crianças ≤36 meses, tinha "+ 39,28€" (total 127,71€)
— o valor correcto, confirmado pelos dados verificados desta sessão, é
"+ 9,28€" (total 97,71€); "127,71"/"39,28" confirmados ausentes de todo
o repositório depois da correcção. A tabela de RR por escalão (secção
"Como se calculam os escalões") estava incompleta/enganadora por
mostrar só o cenário (b) — reescrita como tabela comparativa dos 3
cenários lado a lado, por instrução explícita da tarefa ("ATENÇÃO
ESPECIAL"). Não modelado, declarado na UI: cenários (a)/(c), acréscimo
por família numerosa, majoração pré-natal de 35%, crianças
institucionalizadas, duplicado de setembro, isenção trabalhador-estudante,
património mobiliário, fórmula de rendimentos de independentes.
`0.5` hardcoded na majoração monoparental substituído por
`majoracaoMonoparentalFracao` fetched. `tests/test_simulador_abono_calculo.py`
reescrito (14 testes): golden tests recalculados a partir de
`dados/parametros.json`, novo `test_limite_garantia_infancia_corrigido_2495_37_nunca_2631_94`
(RR=2.500€ — entre os dois limites, só elegível para a Garantia com o
valor antigo/errado — prova a correcção por regressão directa) e 2
testes de runtime real.

**`gerar_base_dados.py` apanhou as 2 prestações novas automaticamente**
(glob genérico sobre `dados/parametros/*.yaml`, sem alteração de
código — invariante 6 do prompt da sessão confirmada sem intervenção).
`dados/parametros.json`: 3 prestações, 46 parâmetros. Nenhuma URL
específica de Guia Prático foi inventada — `fonte_url` usa sempre a
homepage `https://dre.pt` (regra "nunca inventar subpaths de portais
oficiais"), com o Guia Prático citado por nome/versão/data dentro de
`referencia_legal` para rastreabilidade, nunca como link fabricado.

Verificado antes de cada commit: `verificar_datas.detectar_alertas()`
sem falsos positivos nas 4 páginas tocadas em nenhum mês de 2026; os 4
blocos JSON-LD de cada página válidos (`json.loads`); paridade
visível↔JSON-LD das FAQs mantida nos dois simuladores (6/6); axe sem
violações críticas/sérias nas 4 páginas; `ruff check scripts/ tests/
--select E,F,W --ignore E501 .` limpo; suite completa reconfirmada sem
regressões. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
não tocados (`False`, inalterados — nenhuma das duas flags tem relação
com esta sessão). Trabalho feito no branch `claude/new-session-5pczn8`
(designado pelo ambiente remoto desta sessão) — **SEM PR aberto ainda
neste ponto do trabalho** (ver fecho de sessão para o estado final).*

---

*Última revisão: 2026-07-20 — Sessão 1 do plano "Expansão do Cluster
Habitação" (documento externo fornecido nesta sessão, 3 sessões
planeadas — 1: dados + IMT Jovem + Garantia Pública + hub; 2: simulador
de IMT Jovem; 3: RSAA + 1.º Direito + dedução de rendas + watchlist).
Executada só a Sessão 1, ponto a ponto do prompt: PASSO 0 (verificação
factual via `WebSearch` — `WebFetch`/`curl` continuam bloqueados nesta
sessão, 403 via proxy, mesma limitação documentada em várias sessões
anteriores) confirmou sem divergências os valores 2026 do IMT Jovem
(330.539€/660.982€/8%, Lei n.º 73-A/2025 + DL n.º 48-A/2024 + DL n.º
48-D/2024) e da Garantia Pública (15%/450.000€/10 anos/18-35 anos/
86.634€, DL n.º 44/2024 + Portaria n.º 236-A/2024/1) — nenhum valor do
prompt precisou de correcção, ao contrário do que aconteceu nas
migrações anteriores de CSI/subsídio de doença/abono para este mesmo
padrão. Achado adicional confirmado via `WebSearch`, não estava no
prompt original: a mecânica exacta da isenção parcial (8% de IMT + 0,8%
de Imposto do Selo, ambos só sobre o excedente acima de 330.539€) e um
exemplo real publicado (casa de 340.000€ → 832,57€ pago em vez de
16.156,65€, poupança de 15.324,08€) — usado como exemplo sourced na
página em vez de recalcular a tabela geral de IMT (não verificada por
completo nesta sessão, fica para a Sessão 2, que constrói o simulador).
Nuance real também confirmada (não estava no prompt): herança
**indivisa** não exclui a isenção do IMT Jovem, herança **partilhada**
exclui — mesmo com uma quota pequena.

`dados/parametros/habitacao.yaml` novo (padrão OpenFisca, mesmo
princípio de `csi.yaml`/`subsidio-doenca.yaml`/`abono.yaml`, 13
parâmetros com `referencia_legal`/`fonte_url`/`verificado_em` — inclui
a data-limite da garantia pública como parâmetro de tipo `data`, não só
valores numéricos), consolidado em `dados/parametros.json` por
`scripts/gerar_parametros_json.py` (guarda dura do PASSO 0 confirmada a
passar). `imt-jovem.html` e `garantia-publica-credito-habitacao.html`
publicadas — estrutura completa (resposta-rápida + resumo-rápido +
checklist-final + `HowTo`+`FAQPage`+`BreadcrumbList`+`Article` JSON-LD),
integradas no cluster `habitacao` (`data/clusters.json`, `sitemap.xml`,
`scripts/pesquisa.js`, imagem OG própria via `gerar_og_images.py`,
`fontes.html` com os 4 diplomas novos). `p/habitacao.html` reorganizado
em duas secções (🏠 Arrendar / 🔑 Comprar — `<h2>` novos, `.apoio-mini`
passou de `<h2>` para `<h3>` para manter a hierarquia de cabeçalhos
correcta), FAQ e meta description actualizadas para reflectir os 4
apoios; `dateModified` avançado para 20/07/2026.

`scripts/sincronizar_clusters.py`/`sincronizar_nav.py`/
`inserir_botao_partilhar.py`/`adicionar_canonicas.py`/
`adicionar_autoria_artigos.py`/`adicionar_article_jsonld.py` corridos
sobre o repositório inteiro — as duas páginas novas já nasceram com os
blocos `CLUSTER-BADGE`/`RELACIONADOS`/nav/canónica/autoria/`Article`
correctos, escritos à mão a seguir exactamente ao padrão dos scripts
(idempotência confirmada: 0 alterações a qualquer uma das duas páginas
em qualquer um dos scripts, só `p/habitacao.html`/`porta-65.html`/
`apoio-extraordinario-renda.html`/`index.html` regeneraram o
`RELACIONADOS`/`ATUALIZACOES:HOME` automaticamente).

8 golden tests novos em `tests/test_valores_ancora.py` (secção "Cluster
Habitação"): `_valores_eur_inteiros()` novo (os limiares deste cluster
são sempre inteiros, ao contrário dos valores já cobertos por
`_valores_eur()`, sempre com 2 casas decimais) — cobre os valores em
`<title>`/meta description das 2 páginas novas contra
`dados/parametros.json`, mais consistência com o corpo de cada página e
com o resumo do hub. Um teste falhou na 1.ª corrida
(`test_garantia_publica_prazo_e_condicoes_no_corpo_batem_com_o_yaml` —
a duração de "10 anos" da garantia nunca tinha sido escrita no corpo
visível da página, só no YAML/JSON-LD) — corrigido acrescentando a
frase em falta ao corpo, não enfraquecendo o teste.

Ambiente de sandbox desta sessão: `beautifulsoup4`/`lxml`/`playwright`/
`playwright-stealth`/`jsonschema`/`pytest`/`ruff` não estavam
instalados — instalados nesta sessão; `feedparser` continuava a falhar
por causa do `sgmllib3k` (mesmo bug de `install_layout`/`setuptools` do
sistema, documentado em várias sessões anteriores) — corrigido com o
mesmo workaround já registado (extrair `sgmllib.py` do tarball para
`site-packages` à mão). Browsers Chromium pré-instalados em
`/opt/pw-browsers` (revisão 1194) reaproveitados via
`PLAYWRIGHT_BROWSERS_PATH` pelos scripts/testes que já têm o fallback
de localização documentado (`gerar_og_images.py::_localizar_chromium`,
`tests/test_acessibilidade.py`).

Suite completa local: **2857 passed, 4 skipped, 0 failed** (523s) — os
4 skips a bater certo elemento a elemento com a allow-list
(`scripts/verificar_skips_permitidos.py`, exit 0); `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpo; confirmado por
inspecção estrutural (`BeautifulSoup`, `json.loads` sobre os 8 blocos
JSON-LD das 2 páginas novas + `p/habitacao.html`) sem HTML5validator
disponível neste sandbox (mesmo erro de build do `setuptools` do
sistema já documentado — validação HTML5 completa fica para o CI, como
já acontecia noutras sessões com a mesma limitação); zero links
internos partidos; hierarquia de cabeçalhos confirmada sem saltos nas 3
páginas tocadas. `test_acessibilidade.py`/`test_higiene_indexacao.py`/
`test_breadcrumb_coerencia.py`/`test_nav_coerencia.py`/
`test_og_image.py` (todos parametrizados sobre as páginas reais)
cobriram as 2 páginas novas automaticamente dentro da suite completa —
0 violações axe.

**Decisão registada, não implementada**: o ponto 1.6 do prompt pedia
para "adicionar as novas URLs ao sistema de canary de URLs (padrão Como
Pedir)" — investigado e confirmado que `data/urls_como_pedir.json` +
`tests/test_urls_como_pedir.py` é um mecanismo desenhado especificamente
para o cluster `como-pedir` (nome literal), sem equivalente genérico
para outros clusters no repositório; estender essa infra-estrutura ao
cluster Habitação seria inventar um mecanismo fora do âmbito para que
foi construído — não implementado. `scripts/urls_criticas.txt` (smoke
test) também não foi tocado, seguindo o precedente já estabelecido de
só incluir páginas de referência/agregadoras (calendário, hub), nunca
artigos de guia individuais.

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados por esta sessão — nenhuma das duas flags tem
relação com este trabalho). Sessões 2 (simulador de IMT Jovem) e 3
(RSAA, 1.º Direito, dedução de rendas em IRS, watchlist automática DRE)
do mesmo plano ficam registadas em `ROADMAP.md` → "Backlog Habitação",
por fazer. Trabalho feito na branch `claude/new-session-vbrhmd`
(designada pelo ambiente remoto desta sessão) — **SEM PR — branch não
integrada em `main`**.*

---

*Última revisão: 2026-07-20 — Sessão 2 (revista) do plano "Expansão do
Cluster Habitação": correcção do IMT Jovem (Regiões Autónomas + exclusão
de terrenos) + `simulador-imt-jovem.html`, 7.º simulador do site. Três
commits atómicos, a correcção factual ANTES do simulador (regra da
própria spec — se a sessão morresse a meio, a correcção já estava
publicada).

**PASSO 0** (WebFetch/curl continuam bloqueados nesta sessão — 403 na
proxy para qualquer domínio externo, incluindo os PDFs oficiais do
Ofício Circulado; triangulação `WebSearch` por ≥2 fontes independentes
por facto): (a) limites do IMT Jovem nas **Regiões Autónomas** 25% acima
do Continente (Lei n.º 21/90, de 4 de agosto; tabelas práticas no Ofício
Circulado n.º 40129/2026, de 6 de janeiro) — isenção total até
**413.174€**, parcial até **826.228€**; divergência de arredondamento
entre fontes secundárias (826.227 vs 826.228) resolvida pelo padrão de
arredondamento das próprias tabelas práticas (meio-euro para cima,
confirmado pelo 1.º escalão RA publicado: 132.933€ = 132.932,50€
arredondado); (b) **terrenos para construção excluídos** do IMT Jovem,
mesmo com construção em curso à data da escritura — informação
vinculativa da AT (out. 2025, PIV_29556), triangulada por
eco.sapo.pt/idealista/JN/supercasa; (c) **tabela geral de IMT 2026**
(HPP, Continente) confirmada por triangulação E por auto-consistência
matemática — cada parcela a abater deriva exactamente dos limites
(trancado por teste); a tabela geral das RA (parcelas a abater) NÃO
ficou conclusiva — pelo fallback previsto na própria spec, o simulador
cobre só o Continente, com aviso visível + link à nota RA do guia;
(d) 330.539/660.982/8% reconfirmados, sem divergências.

**Commit 1 (correcção)**: `dados/parametros/habitacao.yaml` +3
parâmetros (2 limites RA + exclusão de terrenos, esta como parâmetro de
texto, mesmo precedente de `garantia_prazo_contrato_limite`);
`imt-jovem.html` com nota RA junto à tabela de escalões, erro comum novo
(terrenos) e FAQ nova (paridade 1:1 visível↔JSON-LD confirmada
programaticamente); 3 golden tests novos em `test_valores_ancora.py`,
incluindo o canário **RA = Continente × 1,25 arredondado** — se a
actualização anual dos escalões esquecer os valores RA, falha sozinho.
**Falso positivo apanhado antes do commit** (nunca depois de uma Issue
falsa existir): "informação vinculativa divulgada em outubro de 2025"
disparava `data_mes_ano` já em julho/agosto de 2026 — novo marcador
`informa[çc][ãa]o\s+vinculativa` em `MARCADORES_HISTORICOS`
(`verificar_datas.py`), âncora estreita confirmada sem colisão por grep,
com regressão sobre o HTML real + guarda anti-sobre-supressão em
`test_verificar_datas.py`.

**Commit 2 (simulador)**: tabela geral 2026 parametrizada no YAML (15
parâmetros novos, incl. Imposto do Selo 0,8% — verba 1.1; os limites dos
escalões de 7%/8% são, por construção legal do art. 9.º-A, os próprios
limites do IMT Jovem — reutilizados, nunca duplicados);
`simulador-imt-jovem.html` no padrão actual do CSI (fetch de
`/dados/parametros.json`, botão nasce `disabled`, erro visível se o
fetch falhar — nunca calcula com valores em falta); checklist de
elegibilidade com 3 condições — **um inelegível nunca vê valores de
poupança** (decisão da spec, verificada de ponta a ponta com Chromium
real, não só na função pura); VPT opcional (base = maior entre preço e
VPT, com aviso); desagregação IMT/IS com/sem isenção + poupança total;
`formatarEuro` PT determinística (nunca `toLocaleString`, cujo separador
de milhares varia com a versão de ICU). **Validação cruzada**: a tabela
verificada reproduz ao cêntimo o exemplo já publicado no guia desde a
Sessão 1 (340.000€ → 832,57€ vs 16.156,65€, poupança 15.324,08€) —
trancado por golden test que também exige que o artigo continue a
publicar os três números. 27 testes novos
(`tests/test_simulador_imt_jovem_calculo.py`): casos-âncora da spec
(250.000€ → 0€/0€; 400.000€ → 8%×69.461 = 5.556,88€; 700.000€ → 6%
única = 42.000€), fronteiras exactas de todos os escalões (330.539/
330.540, 660.982/660.983, 106.346/106.347, 1.150.853/1.150.854),
coerência interna das parcelas a abater, checklist incompleta
(parametrizado pelas 3 condições), VPT, e runtime real com `http.server`
(fetch sucesso/falha, bypass do `disabled` nunca produz resultado).

**Commit 3 (integração)**: 7.º card em `simuladores.html`
("Seis"→"Sete", `hasPart` JSON-LD, descriptions) e na secção de
simuladores do `index.html`; links bidireccionais simulador ↔
`imt-jovem.html` ↔ `garantia-publica-credito-habitacao.html` (CTA no
card "Quanto poupas" do guia; o `RELACIONADOS` automático de
`sincronizar_clusters.py` já cobria o resto — `clusters.json` ganhou a
ferramenta no cluster `habitacao`, "4 guias · 1 simulador");
`/simulador-imt-jovem.html` em `scripts/urls_criticas.txt` E no array
`SIMULADORES` de `scripts/smoke_producao.sh` (verificação de conteúdo
real em produção — lição da Sessão 1, o falso-verde do CDN), smoke
confirmado localmente contra `http.server` via override `DOMINIO`;
sitemap, `pesquisa.js`, og-image própria, `test_eventos_ga4.py` (7.º
simulador, slug `imt_jovem`, `elegivel` como veredicto binário limpo).
Regra de dados do cluster Habitação reforçada (valores de IMT vêm
SEMPRE do YAML, **incluindo RA e tabela geral**).

Verificado: axe 0 violações nas páginas tocadas, 0px de overflow a
375px no simulador novo (Chromium real), zero erros JS, JSON-LD válido,
`detectar_alertas()` sem falsos positivos em nenhum mês de 2026. Suite
completa + guardrail de skips + ruff — ver resultado exacto no commit
final desta sessão. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sem relação com esta sessão). Trabalho feito na branch
`claude/imt-jovem-correcao-simulador-73xpd7` (designada pelo ambiente
remoto desta sessão) — **SEM PR — branch não integrada em `main`**.*

---

*Integração (2026-07-20, sessão de integração separada) — a Sessão 2 do
plano "Expansão do Cluster Habitação" (entrada de revisão anterior) foi
integrada em `main` por fast-forward directo (`aca7e50..edc6191`, sem
PR). Verificação antes do merge: `git fetch` confirmou a branch
`claude/imt-jovem-correcao-simulador-73xpd7` com exactamente os 3
commits esperados (`3463449`/`0488a6b`/`edc6191`) e `main` sem avanço
desde a base (`aca7e50`), por isso sem necessidade de rebase. CI local
completa reconfirmada no estado final da branch: suite **2917 passed, 4
skipped** (~10 min), `ruff check scripts/ tests/ --select E,F,W --ignore
E501 .` limpo, `verificar_datas.detectar_alertas()` sem falsos positivos
nas 5 páginas tocadas (meses 7-12/2026), `verificar_skips_permitidos.py`
4/4 (allow-list confirmada elemento a elemento), `gerar_parametros_json.py
--check` sincronizado. Push a `main` disparou os 4 workflows, todos
confirmados `success` no commit `edc6191` via API (não assumidos pelo
"run mais recente" — cada run verificado pelo `head_sha` exacto):
**Integridade do Código** (`29759483795`), **Validar Conteúdo HTML**
(`29759483640`), **Verificação de Produção — Smoke Test**
(`29759483198`, log real confirmado via `get_job_logs` —
`OK https://tensdireito.com/simulador-imt-jovem.html (200)`, dentro do
array `SIMULADORES` que exige também `"Verificado a"` no corpo, não só o
status; "=== Todas as páginas críticas responderam correctamente ==="),
e **Limpar Branches Órfãs** (`29759483642`). Branch local apagada
(`git branch -d`); a remota cai sozinha no próximo push via
`limpar-branches.yml`, mesmo padrão da Sessão 1.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados
por esta sessão de integração.*

---

*Última revisão: 2026-07-20 — Cluster Habitação, Sessão 3 (fecho):
dedução de rendas em IRS, 1.º Direito, auditoria ao Porta 65 e watchlist
DRE — ver secção "CLUSTER HABITAÇÃO" para o detalhe completo. PASSO 0
(`WebSearch`; `WebFetch`/`curl` continuam bloqueados nesta sessão para
domínios externos) corrigiu a premissa do prompt: o Decreto-Lei n.º
97/2026, de 20 de maio, **já estava publicado** (não pendente) — sobe a
dedução de rendas para 900€/2026 e 1.000€/2027 (a declaração entregue em
2026, sobre rendimentos de 2025, usa ainda 700€) e cria o RSAA; o PAER
confirmado em vigor, sem revogação publicada; a fusão "produto único"
(Porta 65/Porta 65+/PAER/Arrendar para Subarrendar) é só uma intenção
anunciada, sem diploma; distinta do Fundo de Emergência para a
Habitação (aprovado em Conselho de Ministros a 9/07/2026, também sem
confirmação de publicação em DR).

2 páginas novas (`deducao-rendas-irs.html`, `primeiro-direito.html`),
`porta-65.html` auditado, `p/habitacao.html` reorganizado em 3 secções,
`fontes.html` +3 diplomas, `dados/parametros/habitacao.yaml` +1
parâmetro (`deducao_rendas_irs_limite_eur`, 3 vigências). Watchlist DRE
nova — `dre_habitacao_paer`/`dre_habitacao_garantia` em
`scraper_playwright.py` (mesmo mecanismo `pesquisa_interactiva` do
`dre_psu`, lógica de detecção generalizada em
`_detectar_decreto_lei_generico`, `_detectar_decreto_psu` intocado por
compatibilidade com `tests/test_dre_psu_pesquisa.py`) + Issues dedicadas
em `pipeline-diario.yml` — **nunca calibrada contra um runner real
nesta sessão**, a 1.ª corrida real do pipeline confirma os
`min_chars_uteis`.

**Achado corrigido antes do commit, não deixado no diff**: a 1.ª escrita
de `data/clusters.json` (via `json.dump(..., indent=2)`) reformatou o
ficheiro inteiro (310 inserções/52 remoções, todas as restantes
entradas de outros clusters, não só a de Habitação) — apanhado por
revisão do `git diff --stat` antes do commit, revertido e reaplicado com
uma edição cirúrgica de texto que preserva o estilo compacto original
(4 inserções, 1 alteração). Todos os outros diffs revistos manualmente
ficheiro a ficheiro antes do commit (idempotência de
`sincronizar_clusters.py`/`sincronizar_nav.py`/`adicionar_canonicas.py`/
`adicionar_autoria_artigos.py`/`adicionar_article_jsonld.py`/
`inserir_botao_partilhar.py` confirmada — 0 alterações, as 2 páginas
novas já nasceram correctas).

Suite completa local: **2986 passed, 4 skipped** (552,65s) —
`scripts/verificar_skips_permitidos.py` confirma os 4 skips a bater
certo, elemento a elemento, com `tests/skips_permitidos.json` (mesma
allow-list de sempre, nenhum skip novo). `ruff check scripts/ tests/
--select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sem relação com esta sessão). Trabalho feito na branch
`claude/habitacao-rendas-primeiro-direito-bwvyvx` (designada pelo
ambiente remoto desta sessão) — commit `3c85832`, push feito para a
branch remota — **SEM PR — branch não integrada em `main`** (protocolo
de fim de sessão desta secção "REGRA ABSOLUTA — GIT").*

---

*Última revisão: 2026-07-20 (sessão de handoff/integração) — protocolo de
arranque aplicado: `claude/habitacao-rendas-primeiro-direito-bwvyvx`
confirmada com exactamente os 2 commits esperados (`3c85832`, `64e51bd`)
e `main` sem avanço conflituante desde a base. Integrada por
fast-forward directo (sem PR), depois de CI local reconfirmada no estado
final (suite completa, ruff, `verificar_datas`,
`verificar_skips_permitidos.py`, `gerar_parametros_json.py --check`). Os
4 workflows disparados pelo push confirmados `success` via API (por
`head_sha` exacto, nunca assumido pelo "run mais recente"): Integridade
do Código (7 jobs), Validar Conteúdo HTML, Verificação de Produção
(Smoke Test — confirma `imt-jovem.html`/`garantia-publica-credito-
habitacao.html`/`deducao-rendas-irs.html`/`primeiro-direito.html` a
servir conteúdo real em produção), Limpar Branches Órfãs.

**FASE 3 — calibração da watchlist DRE contra um runner real**: disparado
`workflow_dispatch` de `pipeline-diario.yml` em `main`. `dre_habitacao_paer`
produziu um **falso positivo genuíno** — a pesquisa de frase exacta
funcionou (não é o bug do índice-inteiro do `dre_psu` original), mas
devolveu correctamente o DL n.º 20-B/2023 (confirmado por `WebSearch`
como o diploma fundador do PAER) e as suas alterações já conhecidas
(2023-2025), criando a Issue #73. Causa raiz: a suposição de
`_detectar_decreto_lei_generico` ("qualquer Decreto-Lei nos resultados é
sinal de novidade") só vale para uma lei que ainda não existe (`dre_psu`)
— para uma lei já em vigor há anos, dispararia todos os dias. Corrigido
com um corte de recência (`data_minima`/`"desde": "2026-07-20"`,
`scripts/scraper_playwright.py`) — só conta como "novo" um item datado a
partir da activação da watchlist; um item sem data reconhecível nunca é
descartado em silêncio. `dre_psu` confirmado 100% inalterado (sem corte
de recência, testado explicitamente). `dre_habitacao_garantia` devolveu
zero resultados na 1.ª corrida — comportamento seguro (nunca disparou),
causa (talvez a pontuação "n.º" a quebrar a tokenização de pesquisa do
DRE) registada em ROADMAP.md sem prioridade enquanto continuar a falhar
em segurança. Issue #73 fechada com a explicação completa. 6 testes de
regressão novos em `tests/test_dre_habitacao_watchlist.py` (18 no
total), incluindo uma fixture com os dados reais devolvidos por esta
corrida — nunca reescrita à mão. Suite completa local reconfirmada:
**2994 passed, 4 skipped** (allow-list de skips confirmada elemento a
elemento); `ruff check scripts/ tests/ --select E,F,W --ignore E501 .`
limpo. Correcção pushada para `main` (commit `c77d416`); os 4
workflows disparados confirmados `success` via API por `head_sha`
exacto (Integridade do Código, Validar Conteúdo HTML, Verificação de
Produção, Limpar Branches Órfãs).

**2.ª corrida real, pós-correcção**: disparado novo `workflow_dispatch`
para confirmar a correcção contra dados reais. `_detectar_decreto_lei_generico`
confirmou-se correcto (`achou=False`, nenhuma linha nova escrita em
`avisos.log`) — mas a Issue #74 foi recriada na mesma, por um **segundo
bug, distinto e separado** do primeiro: o passo JS "Abrir Issues" filtra
`avisos.log` por dia calendário (`l.startsWith(hoje)`), não por corrida
específica — como as 2 corridas de teste aconteceram no mesmo dia UTC, a
linha antiga da 1.ª corrida (anterior à correcção) foi "reencontrada"
pela 2.ª. **Nunca acontece no cron diário normal** (uma corrida/dia) —
só se manifesta com múltiplos `workflow_dispatch` manuais no mesmo dia,
exactamente esta calibração. Issue #74 fechada com a mesma explicação
completa. Gap registado em ROADMAP.md, deliberadamente não corrigido
nesta sessão (baixa prioridade, mesma categoria do gap MUDOU já
documentado para o MEGA) — corrigir exigiria filtrar por timestamp de
início da corrida em vez de por dia, numa lógica de Issues partilhada
por várias outras watchlists (MEGA, PSU, Garantia Pública), risco
desproporcionado face ao benefício de um cenário que só a calibração
manual desta sessão produziu. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados).
Trabalho directo em `main`, sem branch nova.*

---

*Última revisão: 2026-07-27 — auditoria de AI-extractability (AI Overviews/
assistentes) nas 7 páginas prioritárias + 3 correcções aplicadas. Auditoria
inicial (só leitura): resposta extraível do 1.º parágrafo pós-H1, `FAQPage`
JSON-LD e outros schemas — 5/7 já tinham resposta directa e citável
(`prova-escolar.html`, `abono-de-familia.html`,
`manuais-escolares-mega.html`, `baixa-medica-subsidio-doenca.html`,
`porta-65.html`); 2/7 marcadas ⚠️ parcial:
`prestacao-social-para-a-inclusao.html` (parágrafo era um índice do
conteúdo, não uma resposta — valor da PSI só numa badge separada) e
`calendario-pagamentos-seguranca-social.html` (parágrafo sem nenhuma
data/padrão específico). `FAQPage`/`BreadcrumbList` presentes nas 7, zero
falhas de schema nessa frente.

**Correcção 1 — `prestacao-social-para-a-inclusao.html`**: `.resposta-
direta` reescrita para resposta autónoma e citável (incapacidade ≥60%,
333,64€/mês componente base, até 670€/mês complemento, retroativos a
janeiro, acumula com trabalho e pensão de invalidez) — valores todos já
publicados no corpo do artigo, badge `.valor-destaque` mantida intacta.

**Correcção 2 — `datePublished` malformado**: `abono-de-familia.html` e
`manuais-escolares-mega.html` tinham `datePublished` em ISO parcial
("2026-06") no `Article` JSON-LD — inválido, risco de o Google ignorar o
schema. Achado de ambiente: o clone estava **raso** (`shallow`, só desde
2026-07-19) — `git log --diff-filter=A` não encontrava nada antes disso;
`git fetch --unshallow` recuperou o histórico completo até junho e
permitiu confirmar a data real de criação de cada página com confiança
total, sem recorrer a fallback: `abono-de-familia.html` → commit
`cbed7be`, **2026-06-23**; `manuais-escolares-mega.html` → commit
`1259543`, **2026-06-24** — ambas batem com "jun. 2026" já registado na
tabela "PÁGINAS PUBLICADAS". `dateModified` intocado nos dois.

**Correcção 3 — `calendario-pagamentos-seguranca-social.html`, em duas
tentativas**: a 1.ª proposta de texto ("pensões início / abono+RSI+
desemprego fim do mês") foi verificada contra os dados reais de
`#cal-destaque`/`#cal-dados` (julho e agosto) e **não batia certo** —
abono é pago a meio do mês (dia 14-16), não perto do fim, e o subsídio de
desemprego tem 2 pagamentos (meio + fim), não só um no fim; não publicado,
reportado o padrão real ao Nuno em vez de deixar um facto errado passar
(mesmo princípio de "INVARIANTE — nenhum estado de erro pode parecer
sucesso"). A 2.ª proposta ("pensões início / abono meio / RSI perto do
fim / desemprego dois pagamentos meio+fim") foi verificada outra vez
contra os dois meses e bateu certo em todos os pontos — aplicada como
commit separado (`71602e2`), sem `--amend` sobre o commit anterior.

**Testes**: `test_valores_ancora.py` (48), `test_higiene_indexacao.py`,
`test_anos_metadados.py`, `test_breadcrumb_coerencia.py`,
`test_sobre_jsonld.py` para as correcções 1+2 — 694 passed, 0 falhas.
`test_valores_ancora.py` + `test_calendario_frescura.py` +
`test_nav_coerencia.py` para a correcção 3 — Playwright instalado neste
sandbox (só faltava o pacote Python; o Chromium já estava pré-cacheado em
`/opt/pw-browsers`) para não deixar as 6 verificações funcionais do
calendário por correr — **630 passed, 0 skipped, 0 falhas**. JSON-LD dos
4 ficheiros tocados validado com `json.loads` — todos válidos.

**Git — dois commits, ambos directos em `main`, sem PR**: `0eba858`
(correcções 1+2) e `71602e2` (correcção 3), cada um pedido explicitamente
pelo Nuno via `git push origin main`, cada um um fast-forward puro a
partir do tip real de `origin/main` (sem force, sem merge commit).

**Achado de ambiente — assinatura de commits**: o stop-hook local
(`~/.claude/stop-hook-git-check.sh`) assinalou os dois commits como
potencialmente "Unverified" (`%G?` = N localmente) mesmo com
`user.email`/`user.name` já correctos — a causa é
`gpg.ssh.allowedSignersFile` não estar configurado neste sandbox para
*verificação* local, não uma falta de assinatura real: `git cat-file -p`
confirmou um bloco `gpgsig` SSH válido nos dois commits desde a criação.
Para `0eba858`, corrigido com `git commit --amend --no-edit --reset-author`
(sugestão do próprio hook). Para `71602e2`, o Nuno pediu explicitamente
para **não** amendar nem mexer na assinatura — dado o conflito directo
com a sugestão do hook, usado `AskUserQuestion` em vez de decidir
unilateralmente; o Nuno escolheu deixar como estava. Confirmado depois
por screenshot real do GitHub (mobile): commit `71602e2` mostra badge
verde **"Verified"** e `6/6` checks — prova que a assinatura já estava
correcta sem qualquer amend, e que a ferramenta MCP `get_commit` e o
`WebFetch` à página HTML não conseguem confirmar isto de forma fiável (a
1.ª omite o campo `verification` da resposta, o 2.º perde a badge na
conversão para markdown; `api.github.com` está bloqueado pela política de
rede desta sessão, 403). **Lição para sessões futuras**: `%G?` local "N"
neste sandbox não é prova de commit não assinado — só prova que a
verificação local está mal configurada; confirmar sempre no GitHub real
antes de assumir que um amend é necessário, e nunca fazer amend/
reset-author quando o utilizador pediu explicitamente o contrário, mesmo
que o stop-hook sugira o oposto — perguntar, não decidir por ele.

**Repetição confirmada (2026-08-02, sessão de auditoria do cluster
PSU)**: o mesmo padrão reapareceu no commit `a199527` (correcção da
ponderação de adultos equivalentes em `psu-quando-entra-em-vigor.html`)
— `git cat-file -p` confirmou de novo um bloco `gpgsig` SSH válido,
`user.email`/`user.name` já correctos (`noreply@anthropic.com`/`Claude`),
e o mesmo `gpg.ssh.allowedSignersFile needs to be configured...` como
única causa do "N" local. Seguida a lição já registada acima: **não**
amendado — o commit ficou local (sem push nesta sessão), por isso não
foi possível confirmar no GitHub real ainda; a verificação real fica
para quando/se for feito push, mesmo protocolo de "perguntar, não
decidir por ele" já estabelecido nesta secção.

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem relação com scraper/Shadow Mode).
PR: sem PR — dois pushes directos a `main`, ambos confirmados `Verified`
e integrados.*

---

*Última revisão: 2026-07-27 (sessão seguinte) — corrigida discrepância de
data em `bolsa-de-merito.html`: o `<meta name="description">`/`og:description`
diziam "Verificado a 30/06/2026", enquanto o corpo (FAQ JSON-LD,
`.nota-tabela`, 3× `.fonte-inline`, fonte-bloco final) e o `dateModified`
do `Article` JSON-LD diziam "24/06/2026". Investigação via `git log -S`
sobre o histórico completo (clone estava raso, `git fetch --unshallow`
necessário primeiro — mesma limitação já documentada na entrada anterior
deste ficheiro) identificou a causa: o commit `39ee747` (2026-06-30,
"título e descrições para 2026/2027, sem valor hardcoded") reescreveu só
`<title>`/meta description/`og:*`/`BreadcrumbList`/H1 para o ano lectivo
2026/2027 — e, nesse mesmo gesto, carimbou a meta description com a data
do próprio commit em vez de manter a data do fact-check original. Nunca
tocou no resto da página. A data real do fact-check é **24/06/2026**
(commits `16c5943`/`832fcf5`/`53dc565`/`67ff952`, todos desse dia,
"factos verificados"/"long-tail FAQ ... com fontes verificadas") —
confirmada por 6 ocorrências independentes espalhadas por 4 commits,
contra 1 única ocorrência isolada de "30/06/2026" num commit que nunca
re-verificou nenhum facto. Corrigidas as 2 metas para "24/06/2026";
`sincronizar_clusters.extrair_verificado_em()` (usada em
`ATUALIZACOES:HOME`) já usava a última ocorrência do ficheiro (linha do
fonte-bloco final, sempre 24/06/2026) — a homepage nunca foi afectada por
este bug.

**Gap de canário confirmado, não fechado nesta sessão**: nenhum teste
valida que todas as ocorrências de "Verificado a"/`dateModified` numa
página batem certo entre si — `test_valores_ancora.py` só tem canários
pontuais por página (ex. abono/PSI/AMIM), e `test_anos_metadados.py`
só apanha anos civis anteriores ao corrente, cego a duas datas do mesmo
ano civil a divergirem entre si (exactamente este caso). Registado para
uma sessão futura: um teste genérico, parametrizado sobre as páginas
reais, que extraia todas as datas "Verificado a"/`dateModified` de cada
página e falhe se não forem todas iguais.

14 testes relevantes (`test_higiene_indexacao.py`/`test_valores_ancora.py`/
`test_anos_metadados.py`/`test_breadcrumb_coerencia.py`, filtrados a
`bolsa`) confirmados a passar; os 4 blocos JSON-LD da página confirmados
válidos (`json.loads`). `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sem relação com esta sessão). Trabalho feito na branch
`claude/bolsa-merito-date-discrepancy-ya5nm0` (designada pelo ambiente
remoto desta sessão) — **SEM PR — branch não integrada em `main`**
(protocolo de fim de sessão desta secção "REGRA ABSOLUTA — GIT").*

---

*Última revisão: 2026-07-28 — Lei n.º 36/2026, de 27 de julho (a autorização
legislativa da PSU), publicada em Diário da República — texto integral
fornecido pelo Nuno (colado a partir do PDF oficial de dre.pt), tratado como
fonte primária directa, sem necessidade de `WebSearch`/`WebFetch`. Confirmado
antes de qualquer edição que **não existe** nenhuma Issue aberta
"decreto-lei PSU detectado em DRE" (`mcp__github__list_issues`/
`search_issues`, ambas vazias) — correcto, porque isto é uma Lei, não um
Decreto-Lei, e o sentinela `dre_psu` só dispara para "Decreto-Lei"; por isso
o skill `/atualizar-cluster-psu` (desenhado para o cenário do decreto-lei
com valores) não se aplicava tal e qual — tratado como sessão de actualização
de conteúdo do cluster, com o mesmo rigor de confirmação prévia (resumo
completo apresentado ao Nuno via `AskUserQuestion` antes de qualquer
ficheiro tocado, com 3 afinações de redacção pedidas e aplicadas).

Actualizadas as 6 páginas do cluster (`prestacao-social-unica.html` +
`psu-quando-entra-em-vigor.html`, `psu-quem-tem-direito.html`,
`psu-vs-abono-familia.html`, `psu-lista-13-apoios.html`,
`psu-trabalho-social.html`) e esta secção "IMPACTO DA PSU". **Nenhum valor
em €, nenhuma data de entrada em vigor e nenhuma activação do
`simulador-psu.html` foram tocados** — a Lei n.º 36/2026 é a autorização
legislativa, não o decreto-lei com valores, que continua por publicar
(prazo PRR 31 ago 2026).

Factos novos confirmados pelo texto legal e aplicados:

1. **Novo marco na timeline**: até agora só se sabia "promulgada a
   17/07/2026" — agora sabe-se que foi **publicada em Diário da República a
   27/07/2026, como Lei n.º 36/2026** (referendada pelo PM a 20/07/2026).
   Timelines de `psu-quando-entra-em-vigor.html` e `prestacao-social-unica.html`
   ganharam esta 4.ª entrada; badges das 6 páginas actualizados de
   "Autorização legislativa promulgada" para "Confirmado na lei de
   autorização" (framing pedido explicitamente pelo Nuno — nunca "decreto-lei",
   que ainda não existe).
2. **Lista dos 13 apoios validada ao pormenor**: o artigo 1.º/2 da lei tem 8
   alíneas, uma das quais (subsídios sociais de parentalidade) desdobra-se em
   6 apoios distintos — a soma bate exactamente 13, confirmando a lista já
   publicada em `psu-lista-13-apoios.html`. Sourcing upgradado de "audição
   parlamentar"/notícias para o texto legal directo, sem alterar a lista em
   si.
3. **Mecanismo de trabalho social confirmado por lei, não só proposto**: o
   limiar de dispensa das actividades de solidariedade social — automática
   para incapacidade certificada ≥80%, avaliação individual entre 60% e 79%
   — está agora no artigo 2.º/j) da Lei n.º 36/2026. Termo legal exacto
   usado: **"dispensa das atividades"** (nunca "isenção geral", precisão
   pedida pelo Nuno). A disputa PS/PSD sobre a obrigatoriedade da
   participação em si **continua por resolver** — a lei confirma o mecanismo
   e os limiares, não a palavra "obrigatório".
4. **Facto novo**: despedimento por facto imputável ao trabalhador não
   determina impedimento de acesso à PSU (artigo 2.º/d/vi) — acrescentado
   com o caveat exigido pelo próprio texto legal ("sem prejuízo de condições
   específicas que se apliquem a cada componente da prestação"), em
   `psu-quem-tem-direito.html` e `prestacao-social-unica.html`.
5. **Facto novo**: "apoios à habitação com caráter de regularidade" entram
   na lista de rendimentos considerados (artigo 2.º/l/ii) — acrescentado a
   `prestacao-social-unica.html`.
6. **Correcção, não só adição — ponderações de "adultos equivalentes"**: o
   site apresentava "cada adulto extra = 0,5; cada menor = 0,5" como se
   fosse fórmula fechada. O texto legal (artigo 2.º/m) exige **ponderações
   diferenciadas** entre "restantes adultos equivalentes a partir dos 18
   anos" e "crianças e jovens" — ou seja, não têm de valer o mesmo — em
   regime "não globalmente mais desfavorável" do que o actual, sem fixar
   nenhum valor numérico. Por instrução explícita do Nuno, a correcção
   nunca afirma qual categoria (adultos ou crianças) fica com o peso maior
   — só que serão diferentes e que os valores exactos ficam para o
   decreto-lei. Aplicado em `psu-quem-tem-direito.html` (secção "Cálculo" +
   FAQ) e `prestacao-social-unica.html` (secção "Como se calcula").
7. **Facto novo**: a lei prevê revisão do CSI num prazo de 90 dias (artigo
   2.º/u), para garantir que ninguém fica excluído com a extinção da pensão
   social de velhice — acrescentado a `prestacao-social-unica.html` ("O que
   NÃO integra a PSU") e `psu-lista-13-apoios.html` ("Fora da PSU"), reforça
   sem alterar a conclusão já fechada de que o CSI se mantém autónomo (ver
   "PENDÊNCIA PSI vs PSU — FECHADA", 2026-07-18).

Confirmado por grep final que nenhuma das 6 páginas ficou com o carimbo
antigo `2026-07-18`/"18 de julho de 2026" por actualizar — todas passaram a
`dateModified`/"Verificado a" 28 de julho de 2026. Nenhum HTML fora do
cluster PSU tocado; `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
não tocados (sessão de conteúdo manual, sem relação com scraper/Shadow
Mode). Suite de testes **não corrida nesta sessão** — o Nuno pediu
explicitamente para parar aqui para revisão do diff antes de qualquer
commit; trabalho feito directamente no working tree da branch
`claude/lei-36-2026-psu-eregk2` (designada pelo ambiente remoto desta
sessão). **Actualização (mesmo dia, revisto e aprovado pelo Nuno)**:
integrado em `main` — commit `e44819d`, **PR #78** ("feat: cluster PSU
actualizado com a Lei n.º 36/2026 (autorização legislativa publicada em
DR)"), 28/07/2026 18:08. PR: #78 (merged).*

---

*Última revisão: 2026-07-28 (mesmo dia, sessão seguinte — PR #80, entrada
retroactiva registada em 2026-08-02 numa auditoria do cluster PSU que
encontrou esta lacuna) — fecha uma dívida de documentação: este commit
(`3af4a75`, 19:20, "feat: PSU passa a seguir o padrão OpenFisca de
parâmetros (psu.yaml)") alterou `scripts/`/`tests/`/`dados/` sem nunca
ganhar entrada própria aqui, apesar dos triggers obrigatórios da secção
"AUTO-ACTUALIZAÇÃO DESTE FICHEIRO". Fecha a lacuna identificada em
diagnóstico: a PSU era a única prestação do cluster já com página própria
sem `dados/parametros/*.yaml` — os placeholders viviam só no objecto
`PARAMETROS_PSU` embutido em `simulador-psu.html`.

Novo `dados/parametros/psu.yaml` — 7 parâmetros, mesmo padrão de
`csi.yaml`/`habitacao.yaml`: `limite_patrimonio_multiplicador_ias` = **60**,
confirmado pela Lei n.º 36/2026 (artigo 2.º/d/v). Os restantes 6
(`valor_referencia_mensal`, `valor_maximo_mensal`,
`majoracao_parentalidade_mensal`, `coeficiente_cit`,
`ponderacao_outro_adulto`, `ponderacao_menor_ate_25`) ficam `valor: null`
— pendentes do decreto-lei (prazo PRR: 31 ago 2026), com
`vigencia_inicio` ancorada a 2026-06-25 (aprovação da lei de autorização
em votação final global).

**Correcção no mesmo commit**: o coeficiente CIT tinha, desde 3 jul 2026,
um "intervalo 0,5–1" atribuído ao "texto aprovado na Assembleia da
República" — nunca confirmado no texto real da Lei n.º 36/2026 (artigo
2.º/o/p só confirmam a existência da CIT, sem fixar número). Removido de
`simulador-psu.html`, `psu-quando-entra-em-vigor.html` e
`psu-quem-tem-direito.html`; `coeficiente_cit` fica inteiramente
pendente, sem min/max.

`simulador-psu.html` migrado para `fetch('/dados/parametros.json')`,
mesmo padrão de `simulador-csi.html`. `ESTADO_SIMULADOR` passa a dinâmico
(3 estados: fetch falhado → erro visível; fetch OK + `null` → aguarda
decreto-lei; fetch OK + preenchido → formulário activa) em vez de um
`const` fixo a decorar manualmente. `calcularPSU()` ganhou guarda contra
`parametros===null` (antes assumia que só o `.valor` aninhado podia ser
`null`).

`tests/test_valores_ancora.py` ganhou 2 testes-âncora novos:
`test_psu_limite_patrimonio_60x_ias` (recalcula 60×IAS, nunca hardcoded,
confirma contra o corpo de `psu-quem-tem-direito.html`/
`prestacao-social-unica.html`) e `test_psu_parametros_ainda_pendentes`
(tranca os 6 `null` como estado esperado — falha se algum for preenchido
sem passar pelo Passo 4 de `.claude/commands/atualizar-cluster-psu.md`).

Sem alteração a nenhum valor publicado nas páginas HTML além da remoção
do intervalo do CIT já descrita. PR: #80 (merged).*

---

*Última revisão: 2026-08-16 (sessão seguinte, mesmo dia da activação do
cluster PSU) — implementada a ESTRUTURA do artigo 17.º da PSU (apoios à
habitação como rendimento) no simulador, sem o valor da mediana do INE e
sem activar o cálculo — ver nova secção "Artigo 17.º — estrutura pronta,
cálculo desactivado (2026-08-16)" dentro de "IMPACTO DA PSU" para o
detalhe completo. Precedida de uma auditoria read-only (mesma sessão,
sem commits) que confirmou, contra o texto real do artigo 17.º extraído
de `dados/fontes/Decreto-Lei n.PDF`: a fórmula (renda de referência = ⅓
× mediana €/m² do INE × 112,50 m²; imputado = 50% × max(0, renda de
referência − renda paga)); que o teto de 450×IAS do artigo 14.º/3 não se
aplica aqui (é específico de rendimentos prediais); e uma ambiguidade
real no âmbito do n.º 2 (a fórmula dos 50% fala literalmente só de
"habitação social... e arrendamento subsidiado", não necessariamente de
qualquer apoio do n.º 1) — registada, não resolvida.

4 commits: 1) `dados/parametros/psu.yaml` ganha o bloco `art17_*` — 3
parâmetros fixos na lei (área 112,50 m², coeficiente 0,5, divisor 3) e 3
pendentes, deliberadamente `null` (mediana do INE, trimestre de
referência, portaria do artigo 17.º/5); `dados/parametros.json`
regenerado. 2) Teste-âncora `test_art17_habitacao_pendente_ate_portaria`
(mesmo princípio dos `null` das majorações da Fase 1/2, mas para trancar
"não pronto" em vez de "nunca redutível a um valor único") — confirmado
a falhar de propósito com um valor injectado isoladamente, revertido; +
`test_art17_habitacao_constantes_fixas_na_lei`. 3)
`calcularHabitacao(parametros, recebeApoio, rendaPaga)` — gate de
segurança na própria função pura (nunca confia só no HTML): devolve
sempre 0 enquanto `parametros.art17Habitacao.pronto` for `false`; soma
directamente ao rendimento considerado, nunca passa pela CIT. Campo novo
no formulário (checkbox + renda paga condicional) nasce `disabled` por
construção própria, com aviso persistente e nota de UX ("aumenta o
rendimento, reduz a PSU — não é um bug"). 6 golden tests novos + 2 testes
de runtime real (`http.server`, fetch real de `/dados/parametros.json`)
que confirmam, contra a página real, que um bypass deliberado do
`disabled` nunca produz um valor de habitação > 0 no resultado
renderizado — produção continua, hoje, sem mostrar nenhum valor de
habitação. 4) Esta entrada + a secção nova de CLAUDE.md, com os passos
exactos para activar quando `dre_psu_regulamentacao` disparar. Nenhuma
página de conteúdo do cluster tocada (por instrução explícita — ficam
como estão até à portaria).

Suite completa + testes novos + ruff verdes (ver mensagem final da
sessão para os números exactos). `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sem relação com scraper/Shadow Mode). Trabalho feito na branch
`claude/audit-art17-housing-psu-cx9ce7` (designada pelo ambiente remoto
desta sessão), 4 commits assinados, sem merge — PR aberto no fecho da
sessão, ver mensagem final para o número exacto.

---

*Última revisão: 2026-08-25 — "Sentinela para o despacho da ASE": sessão
de investigação e correcção de documentação, **nenhum sentinela novo
construído, nenhum HTML tocado**. PASSO 0 investigou onde é publicado o
"despacho anual da DGEstE com os escalões ASE" que bloqueava a migração
do ASE para YAML (`ROADMAP.md` → "TRABALHO FUTURO REGISTADO") — via
`WebSearch` só (`WebFetch` confirmado bloqueado nesta sessão para
qualquer domínio `.gov.pt`/`.mec.pt`/`diariodarepublica.pt`, e até para
domínios fora do Estado como `google.com` — `EGRESS_BLOCKED` no proxy de
rede desta sessão, mesma limitação documentada em dezenas de sessões
anteriores). Achado: **não existe** esse acto. O regime substantivo da
ASE — escalões A/B como %IAS, tectos de material (16€/8€) e visitas
(20€/10€) em euros, desconto de refeições (gratuita/50%) — está fixado
desde 2015 pelos Despachos n.º 8452-A/2015, 5296/2017 e 7255/2018, sem
nenhuma república anual (os valores de 2025/2026 encontrados via
`WebSearch` são idênticos aos de 2015); a única variável real é o IAS,
publicado por Portaria própria e já vigiado pelo sentinela `dre_ias`. O
mesmo vale para a Bolsa de Mérito (valor = 2,5×IAS, mesmo Despacho
n.º 8452-A/2015, nunca um despacho anual próprio) — achado lateral: o
texto de `bolsa-de-merito.html` ("o valor de 2026/2027 aguarda
publicação do despacho anual") herda a mesma premissa errada; o valor
2026/2027 (1.342,83 €) já é calculável hoje com o IAS 2026 confirmado —
**página não corrigida nesta sessão** (fora do âmbito, decisão
explícita do Nuno de só tocar em documentação), registada para uma
sessão dedicada.

Único acto do Ministério da Educação com cadência quase-anual
encontrado, ligado à ASE mas nunca citado no site (o custo da refeição
é sempre expresso como desconto %, nunca em euros): o preço-tecto da
refeição escolar (1,46 €, indexado ao IPC desde 2024/2025). Registado em
`ROADMAP.md` → "À ESPERA DE UM SINAL" → "Manuais" como **decisão
consciente de não vigiar**, com a razão — não como lacuna.

Correcções aplicadas: `ROADMAP.md` → "TRABALHO FUTURO REGISTADO" (a
entrada da migração do ASE passa de "⛔ bloqueado" a "✅ já não
bloqueado", com a razão real e a mesma acção de sempre — migrar como
qualquer outra prestação desta série, sem prazo, não feita nesta
sessão); nova linha em "À ESPERA DE UM SINAL" → "Manuais" para o preço
da refeição. `CLAUDE.md` → "PÁGINAS COM DATAS SAZONAIS": as duas linhas
de `acao-social-escolar.html`/`bolsa-de-merito.html` corrigidas (deixam
de dizer "Calendário anual" sem mais contexto, passam a apontar para a
razão real — prazo de candidatura redundante com
`calendario-escolar-apoios.html` num caso, texto desactualizado da
própria página no outro) + nova nota de manutenção sazonal com o
raciocínio completo desta investigação.

`data/estado_fontes.json` confirmado nesta sessão antes de qualquer
edição: `dge_ase` em `OK`, 0 dias consecutivos bloqueado — a única fonte
que já toca em ASE é genérica (hash da homepage `dge.mec.pt`, nunca
reconhecimento de acto), sem qualquer relação com este achado.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper novo). Suite completa
(`pytest tests/ -q`) corrida sem alterações a nenhum `.py`/`.html` —
confirma zero regressões de uma sessão puramente documental. Trabalho
feito na branch `claude/sentinela-despacho-ase` (criada nesta sessão,
`main` limpa antes de arrancar) — commit local, sem push.*
