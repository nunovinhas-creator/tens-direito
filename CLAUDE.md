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
- `HISTORICO.md` — data de revisão automática
- `README.md` — estado do repositório
- `data/scraped/*.json` — dados do scraper
- `data/estado_fontes.json` — máquina de estados de fontes bloqueadas (ver secção "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS")
- `data/feeds_saude_hoje.json` — snapshot diário da saúde de cada feed de notícias (Fase 3, ver secção "FRESCURA DA HOMEPAGE")
- `data/estado_feeds.json` — máquina de estados de feeds mortos, escrito por `gerir_estado_feeds.py` (mesmo padrão de `estado_fontes.json`)
- `data/noticias_candidatos.json` — log auditável de candidatos/decisões de cada corrida de notícias (últimos 14 dias)
- `dados/observacoes/<slug>.json` — historial auditável de observações do scraper, um ficheiro por fonte monitorizada, escrito por `scripts/registar_observacao.py` (Fase 1 de "DADOS ABERTOS", só quando `sha256_conteudo` mudar — ver essa secção)
- `dados/parametros.json` — consolidado dos parâmetros legais (Fase 2 de "DADOS ABERTOS"), gerado por `scripts/gerar_parametros_json.py` a partir de `dados/parametros/*.yaml` (esses YAML continuam curados manualmente, nunca escritos pelo pipeline)
- `dados/tensdireito.db` — base SQLite pública (Fase 3 de "DADOS ABERTOS"), gerada por `scripts/gerar_base_dados.py`
- `data/canal_pendente.json` — fila de rascunhos por entregar ao canal de WhatsApp (gatilho de alteração legal); o pipeline só CONSOME (remove a entrada mais antiga entregue) — quem a preenche é sempre uma sessão editorial manual, nunca o pipeline (ver secção "CANAL DE WHATSAPP")
- `data/canal_estado.json` — estado do mecanismo do canal (último rascunho entregue, último mês do calendário publicado), escrito por `scripts/preparar_canal.py` (ver secção "CANAL DE WHATSAPP")

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
- Se o `ROADMAP.md` (ou a última entrada de revisão do `HISTORICO.md` —
  desde o #194, é lá que o diário de sessões vive, nunca no fim do
  `CLAUDE.md`) indicar uma branch "SEM PR — branch não integrada" que ainda não
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
de `HISTORICO.md`: `diagnostico-dre-psu-temp.yml`,
`diagnostico-fontes-temp.yml`, `diagnostico-igefe-temp.yml`,
`diagnostico-calendario-temp.yml`, `diagnostico-logo-temp.yml` — todos
committed directamente em `main` e apagados no fim); essas entradas ficam
como estavam escritas nessa altura, sem reescrever o passado, mas o padrão
delas já não é o que se segue daqui para a frente.

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
Issue única aberta com a contagem certa. Ver a entrada de 2026-07-06 em
`HISTORICO.md` para os run_ids reais.

Estado do repositório confirmado nesta sessão, antes de qualquer teste
(via API `list_branches` + `git ls-remote --heads origin`, não por
suposição): as duas branches órfãs documentadas em revisões anteriores
(`claude/infrastructure-audit-robustness-10k2wc`,
`claude/melhorias-spec-phase-1-anlctz`) **já não existiam** — foram
apagadas manualmente entretanto (fora desta sessão). Só `main`
existia no remoto antes deste workflow correr pela primeira vez.

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
| Pesquisa interna | `scripts/pesquisa.js` (JS puro, indexa as páginas listadas no próprio ficheiro — todas excepto `index.html` e `404.html`; ranking em camadas + excerto + badge de cluster — ver nota de manutenção abaixo) |
| Scraper | Playwright + BeautifulSoup (`scripts/scraper_playwright.py`), com `playwright-stealth`, retries com jitter e fallback Wayback (`OK_VIA_ARQUIVO`) — ver secção "SCRAPER — ROBUSTEZ CONTRA BLOQUEIOS" |
| Extracção valores | `scripts/extrair_valores.py` → `data/divergencias.json` |
| Notícias | `data/noticias.json` (fonte de verdade) + `scripts/gerar_noticias.py` (um feed RSS por tema do site — ver constante `FEEDS` — + corte de recência de 7 dias) → `noticias.html` (arquivo por mês) + 2-3 cards em `index.html` (`NOTICIA-HOME`) — ver secção "FRESCURA DA HOMEPAGE" |
| Partilha social | `assets/js/share.js` + `assets/css/share.css`, inserido em cada página via `scripts/inserir_botao_partilhar.py` (idempotente, sem bibliotecas externas) |
| Clusters/navegação | `data/clusters.json` (fonte única) + `scripts/sincronizar_clusters.py` (idempotente, injecta entre marcadores — ver secção "SISTEMA DE CLUSTERS") |
| Checklist final | `assets/js/checklist.js` + `assets/css/checklist.css` — bloco `.checklist-final` (ver secção "RESPOSTA RÁPIDA + CHECKLIST FINAL"), sem localStorage |
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

### Workflows (ver `.github/workflows/` — a tabela abaixo lista todos, com o que cada um escreve)

| Ficheiro | Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | cron `0 6 * * *` | Scrape → detectar mudanças → notícias → validar valores → README → push único | ✅ sim (`data/`, `index.html`, `noticias.html`, `README.md`, `HISTORICO.md`) |
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
outros workflows (ver tabela "Workflows" acima) verifica a produção
real — todos correm sobre o checkout local do repositório.

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
   ignoradas. A lista de páginas cobertas vive só no próprio
   ficheiro — nunca fixada aqui. Adicionar uma página nova importante
   é só acrescentar uma linha aqui.

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
| `garantia-para-a-infancia.html` | Garantia para a Infância 2026: 127,33€/mês, sem pedido | 2 set. 2026 |
| `p/reformas.html` | Reformas e Pensões — Guia Completo das Regras 2026 | 4 set. 2026 |
| `idade-normal.html` | Idade Normal de Reforma: porque sobe todos os anos | 4 set. 2026 |
| `idade-pessoal.html` | Idade Pessoal de Reforma: carreira longa reduz a idade | 4 set. 2026 |
| `carreiras-muito-longas.html` | Carreiras Muito Longas: reforma aos 60 anos sem cortes | 4 set. 2026 |
| `outras-antecipacoes.html` | Outras Antecipações da Reforma: desemprego, deficiência e mais | 4 set. 2026 |
| `como-e-calculada.html` | Como é Calculada a Pensão: as três peças da fórmula | 4 set. 2026 |
| `que-anos-contam.html` | Que Anos Contam para a Pensão: densidade e melhores 40 anos | 4 set. 2026 |
| `mais-cedo-ou-mais-tarde.html` | Reformar Mais Cedo ou Mais Tarde: o corte e a bonificação | 4 set. 2026 |
| `invalidez-relativa-ou-absoluta.html` | Invalidez Relativa ou Absoluta: a diferença e o que muda | 5 set. 2026 |
| `pensao-e-trabalho.html` | Pensão e Trabalho: o que podes (e não podes) acumular | 5 set. 2026 |
| `quando-a-invalidez-vira-velhice.html` | Quando a Invalidez Vira Velhice: a conversão automática | 5 set. 2026 |
| `pensao-de-sobrevivencia.html` | Pensão de Sobrevivência: quem tem direito e como se calcula | 6 set. 2026 |
| `subsidio-por-morte.html` | Subsídio por Morte: quem recebe, quanto e como pedir | 6 set. 2026 |
| `quem-tem-direito-por-parentesco.html` | Quem Tem Direito por Parentesco: descendentes e ascendentes | 6 set. 2026 |
| `duracao-da-pensao-de-sobrevivencia.html` | Duração da Pensão de Sobrevivência: quanto tempo dura | 6 set. 2026 |
| `pensao-sobrevivencia-conjuge.html` | Pensão de Sobrevivência do Cônjuge: condições e o limite do ex-cônjuge | 6 set. 2026 |
| `pensao-sobrevivencia-uniao-de-facto.html` | União de Facto e Pensão de Sobrevivência: como comprovar | 6 set. 2026 |
| `carreiras-contributivas-estrangeiro.html` | Carreira Contributiva no Estrangeiro: totalização de períodos na UE | 7 set. 2026 |
| `reforma-reino-unido-brexit.html` | Reforma e o Reino Unido: o Protocolo pós-Brexit | 7 set. 2026 |
| `pensao-unificada.html` | Pensão Unificada: CGA e Segurança Social numa só pensão | 7 set. 2026 |
| `caixa-geral-aposentacoes.html` | Caixa Geral de Aposentações: quem está abrangido e como funciona | 7 set. 2026 |
| `simulador-condicoes-reforma.html` | Simulador de Condições de Acesso à Reforma | 7 set. 2026 |
| `simulador-psu.html` | Simulador da PSU 2026: calcula o teu valor (Decreto-Lei n.º 166/2026) | 3 jul. 2026 |
| `simulador-subsidio-doenca.html` | Simulador de Subsídio de Doença 2026 | 5 jul. 2026 |
| `simulador-subsidio-desemprego.html` | Simulador do Subsídio de Desemprego 2026 | 13 jul. 2026 |
| `numero-utente-sns.html` | Número de utente do SNS: como pedir em 2026 | 18 jul. 2026 |
| `certidao-situacao-tributaria.html` | Certidão de Situação Tributária 2026: a certidão de não dívida às Finanças | 19 jul. 2026 |
| `marcar-atendimento-seguranca-social.html` | Marcar Atendimento na Segurança Social 2026: SIGA, telefone e presencial | 19 jul. 2026 |
| `registo-criminal-online.html` | Certificado do Registo Criminal Online 2026: preço, prazo e como pedir | 19 jul. 2026 |
| `calendario-pagamentos-psu.html` | Duração e pagamento da PSU 2026: 12 meses renováveis (DL 166/2026) | 13 ago. 2026 |
| `como-pedir-psu.html` | Como pedir a PSU 2026: requerimento, prazos e documentos (DL 166/2026) | 13 ago. 2026 |
| `amim-beneficios-fiscais.html` | Benefícios Fiscais do AMIM 2026: IRS, ISV e IUC | 19 ago. 2026 |
| `cartao-europeu-estacionamento.html` | Cartão Europeu de Estacionamento 2026: Quem Tem Direito | 19 ago. 2026 |
| `majoracao-subsidio-desemprego.html` | Majoração de 10% do subsídio de desemprego 2026 | 4 set. 2026 |
| `noticias.html` | Notícias | jun. 2026 |
| `sobre.html` | Sobre o Tens Direito | jun. 2026 |
| `fontes.html` | Fontes Oficiais | jun. 2026 |
| `privacidade.html` | Política de Privacidade | jun. 2026 |
| `acessibilidade.html` | Acessibilidade | 4 jul. 2026 |
| `dados.html` | Dados Abertos | 19 jul. 2026 |
| `404.html` | Página não encontrada | jun. 2026 |

*Tabela corrigida a 2026-07-02 — faltavam 7 páginas já publicadas (rsi, subsidio-desemprego,
subsidio-parental, cuidador-informal, comecar-aqui, simulador-abono, simulador-ase).*

*Tabela corrigida a 2026-09-14 — faltavam 12 páginas já publicadas, encontradas por
comparação directa com os ficheiros reais do repositório. Duas ficam deliberadamente fora
da tabela, nunca por esquecimento — razão de cada uma em
`tests/test_higiene_indexacao.py::EXCLUSOES_TABELA_PAGINAS`: `simulador-rsi.html` (factos
por confirmar, Issue #209) e `verificador-apoios.html` (página-fantasma de
redirecionamento). Guardrail novo no mesmo ficheiro falha sozinho se a tabela voltar a
divergir, nas duas direcções — mesmo padrão de `EXCLUSOES_SITEMAP`.*

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
- [ ] Novo artigo de conteúdo? Inclui obrigatoriamente os dois blocos — ver secção "RESPOSTA RÁPIDA + CHECKLIST FINAL": `.resposta-rapida` (rótulo "⚡ Resposta rápida" + tempo de leitura, dentro do `.resposta-direta` já existente no hero, ≤60 palavras) e `.checklist-final` (checklist accionável antes do FAQ, liga `assets/css/checklist.css` + `assets/js/checklist.js`)
- [ ] Editou `<title>` ou `<meta name="description">` com um valor legal em € ou %? Tem de estar coberto por `tests/test_valores_ancora.py` — ver secção "CANÁRIO DE VALORES-ÂNCORA — TITLE/META DESCRIPTION"
- [ ] Página nova de prestação com valores anuais? `<title>`/description devem incluir o ano corrente; qualquer ano civil anterior citado tem de ter excepção explícita em `tests/test_anos_metadados.py` — ver secção "CANÁRIO DE ANOS EM METADADOS"
- [ ] Alterado algum `.py`? Correr `ruff check scripts/ --select E,F,W --ignore E501 .` — mesmo comando do job "Qualidade Python (Ruff)" em `integridade.yml` (nota: a `ruff-action` acrescenta a raiz do repo aos alvos, por isso `tests/` também é verificado, apesar do `scripts/` explícito no comando)
- [ ] Commit e push directamente para `main`
- [ ] Se o ambiente desta sessão impôs uma branch designada (`claude/<nome>`, imposta de fora do repositório — ver "REGRA ABSOLUTA — GIT" → "Protocolo de fim de sessão"), este último passo é substituído pelo protocolo de reporte de lá: terminar com o estado de integração explícito ("PR: #nn (aberto|merged)" ou "SEM PR — branch não integrada"), nunca com um commit/push directo a `main` que não é possível fazer. É uma imposição externa do harness, nunca uma flexibilização desta regra — a checklist não foi violada, só a via de chegada a `main` é diferente

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
│   └── css/checklist.css     ← estilo do bloco .checklist-final
├── scripts/
│   ├── scraper_playwright.py ← Playwright + BS4, fontes em FONTES_PLAYWRIGHT/SLUGS_MONITORIZADOS (no próprio ficheiro)
│   ├── extrair_valores.py    ← compara valores scraped vs HTML publicado
│   ├── gerar_noticias.py     ← RSS por tema + data/noticias.json → noticias.html + cards em index.html (NOTICIA-HOME)
│   ├── gerir_estado_feeds.py ← máquina de estados de feeds de notícias mortos (Step 3a do pipeline)
│   ├── migrar_noticias.py    ← migração única do noticias.html legado para data/noticias.json (não corre no pipeline)
│   ├── gerar_pagina.py       ← utilitário de geração HTML
│   ├── inserir_botao_partilhar.py ← insere assets/js/share.js + assets/css/share.css (idempotente)
│   ├── adicionar_canonicas.py ← insere <link rel="canonical"> auto-referente nas páginas do site (idempotente)
│   ├── adicionar_og_image.py ← bootstrap: insere o bloco og:image em páginas novas (idempotente)
│   ├── gerar_og_images.py    ← gera assets/img/og/<slug>.jpg por página (Chromium real, manifest, idempotente)
│   ├── adicionar_article_jsonld.py ← insere JSON-LD Article (author/publisher/datas) nas páginas de conteúdo com FAQPage (idempotente)
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

### Verificação directa de diplomas — `files.dre.pt` em vez de `dr/detalhe/`

Correcção ao método de verificação primária (2026-09-08): as páginas
`diariodarepublica.pt/dr/detalhe/...` são uma SPA que exige JavaScript
para renderizar o texto do diploma — um `WebFetch`/`curl` simples a essas
páginas nunca devolve o conteúdo real (mesmo quando o domínio não está
bloqueado pela rede da sessão), só a shell vazia. **`files.dre.pt`** (e o
espelho `files.diariodarepublica.pt`) serve o PDF estático da própria
série do Diário da República — um ficheiro binário, sem JS nenhum a
renderizar, fetchável directamente. É o canal a preferir para confirmar
o texto de um diploma, não `dr/detalhe/`. Padrão do URL, já usado em
vários cartões de `fontes.html` (ex.: DL 119/2021, DL 18/2023):
`https://files.dre.pt/1s/AAAA/MM/NNNNN/PPPPPPQQQQQQ.pdf` — série (`1s`
= Série I), ano, mês, número do DR com padding, e o intervalo de
páginas do diploma dentro desse DR (`PPPPPP`-`QQQQQQ`, 6 dígitos cada).

**Confirmado (2026-09-08, continuação do mesmo PR #174)**: `files.dre.pt`
está acessível — o PDF integral do Decreto-Lei n.º 18/2023 foi lido por
inteiro em fonte primária, fora do sandbox (ver o cartão actualizado
deste diploma em `fontes.html`, com os factos que só uma leitura
completa dá — número de ordem das alterações ao Decreto-Lei n.º 187/2007
e ao Estatuto da Aposentação, e o conteúdo dos arts. 5.º/6.º).
**Correcção à leitura da entrada anterior**: `EGRESS_BLOCKED` nas
tentativas de `WebFetch`/`curl` desta e de outras sessões — a
`files.dre.pt` e a dezenas de outros domínios, documentado em toda a
extensão deste ficheiro — é uma limitação da rede do sandbox onde o
Code corre, nunca prova de que o domínio, o diploma ou o método (PDF
estático em vez de SPA) estão indisponíveis. O método continua válido;
só não é executável a partir desta sessão.

**Regra permanente**: a verificação primária de um diploma no DRE (ou
em qualquer fonte oficial atrás de `EGRESS_BLOCKED`) nunca é feita pelo
Code a partir desta sessão — é feita fora dela (pelo Nuno, ou por outro
processo com acesso real à rede) e entregue ao Code já como facto
confirmado, com o artigo/diploma citado ao pormenor. O Code nunca
reconstrói, infere ou triangula um facto que já lhe foi entregue como
verificado — só o transcreve fielmente na página, com a atribuição
correcta ("Lido por inteiro em fonte primária", GRAU 1 na metodologia
descrita na secção "Anel 4" mais abaixo). Sem essa entrega externa, e
com o sandbox bloqueado, o site continua a seguir a regra normal:
triangulação por `WebSearch` (GRAU 2, sempre identificada como tal) ou
a questão fica marcada por confirmar (GRAU 3) — nunca preenchida por
analogia, e nunca apresentada como "lida directamente" sem o ter sido
de facto.

**`bportugal.pt` (Banco de Portugal) bloqueia acesso automatizado por
detecção de bots — mesma natureza da limitação acima, incluindo os
PDFs**: um comunicado oficial do Banco de Portugal costuma aparecer
indexado em resultados de `WebSearch` (o título/excerto é legível), mas
o PDF em si não é legível a partir de nenhuma sessão — mesmo tratamento
que `dr/detalhe/`: sem acesso directo ao ficheiro, o facto nunca passa
de GRAU 2 (triangulado) ou fica GRAU 3 (por confirmar), nunca GRAU 1,
mesmo que o comunicado apareça citado por múltiplas fontes secundárias.

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
13. **O próprio site nunca é fonte**: uma afirmação já publicada noutra página deste site nunca conta como confirmação de um facto novo — se essa página afirmou algo sem fonte primária, repeti-lo aqui não o confirma, só duplica a mesma incerteza. Cada afirmação remete sempre para a fonte primária (ou para uma triangulação identificada como tal, GRAU 2/3 — ver "FONTES VERIFICADAS E APROVADAS"), nunca para outra página do próprio site como prova.

### Não fazer
- Não usar Jekyll ou qualquer SSG
- Não apagar `CNAME` nem `.nojekyll`
- Não publicar sem fonte datada
- Não dar veredictos pessoais ("tu tens direito a X")
- Contacto oficial = **contacto@tensdireito.com** (forwarding ImprovMX → caixa pessoal, activo desde 2026-07-03), sempre ofuscado via JavaScript (`.email-ofuscado`, `sobre.html`), nunca literal em HTML público
- Não usar subpaths de portais sem confirmar que devolvem 200
- **Páginas públicas nunca mencionam GitHub, repositório, código aberto, IA/inteligência artificial ou automação de redação** (decisão do Nuno, 2026-07-03) — vocabulário público é "a redação", "monitorização diária", "verificação contra fontes oficiais"; menções a GitHub/infra continuam permitidas em `scripts/`, workflows, `CLAUDE.md` e docs internos

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

O inventário completo (página, ano, motivo) vive só no dict
`EXCECOES_ANOS_HISTORICOS`, no topo de `tests/test_anos_metadados.py`
— nunca duplicado aqui. Mesma regra permanente já aplicada ao resto
deste ficheiro (ver "AUTO-ACTUALIZAÇÃO DESTE FICHEIRO"): uma contagem
ou lista solta na prosa diverge do código mais cedo ou mais tarde sem
ninguém dar por isso — esta tabela chegou a citar 4 excepções (uma
delas, `subsidio-desemprego.html`/2006, já nem existe no dict) quando o
código real já tinha muitas mais. Quem precisar de saber quantas
excepções existem, ou quais, lê o dict.

Cada entrada só existe por um de dois motivos, sempre registados ao
lado da própria entrada — nunca "esquecimento de actualizar":
- **citação de diploma legal** — o ano faz parte do número do DL/Lei/
  Portaria/Regulamento, não é uma data de vigência (ex.: "Decreto-Lei
  n.º 138/2025");
- **facto histórico permanente** — uma data fixa no passado que nunca
  se repete nem muda (ex.: "PAER fechado a novos candidatos desde
  15/03/2023").

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
4. **Clusters actuais** — lista e contagem completas vivem sempre em
   `data/clusters.json` (fonte única, ponto 1 acima) — nunca fixar aqui
   um número de clusters/pillars, mesmo princípio já aplicado em
   "SCHEMA.ORG — GRAFO DO SITE" → "CollectionPage + ItemList nas pillar
   pages". Notas por cluster que vale a pena reter (não é a lista
   completa — essa é sempre o próprio JSON):

   | Cluster | Pillar | Nota |
   |---|---|---|
   | Idosos, Incapacidade e Cuidadores | `p/idosos-incapacidade-cuidadores.html` | inclui `amim.html` |
   | Habitação | `p/habitacao.html` | criado 3 jul 2026 — Porta 65 Jovem/+ e Apoio Extraordinário à Renda |

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
todos os pillars de `data/clusters.json` existem com a lista de artigos sincronizada (com badge
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

Nav única em todas as páginas do site, gerada a partir de `data/clusters.json`
e injectada entre `<!-- NAV:INICIO -->` / `<!-- NAV:FIM -->` por
`scripts/sincronizar_nav.py`. Estrutura: **Logo | Apoios ▾ (um item por
cluster de `data/clusters.json`, pelos pillars) | Começa aqui | Notícias
| Pesquisa**. "Guias" saiu
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
7. **Testes**: `tests/test_nav_coerencia.py` corre sobre as páginas
   reais do site (parametrizado — cobre página nova automaticamente) e
   confirma: exactamente 1 bloco `NAV` por página,
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
excepção deliberada à regra "institucionais sem JSON-LD" desta secção:
`AboutPage` (mainEntity → Organization), `Organization`
(`@id=".../sobre.html#nvlabs"`, sem `sameAs` — o único que existia
apontava para o repositório GitHub, removido nesta revisão) e
`WebSite` (publisher → Organization). Válido porque `FAQPage`/`WebPage`
herdam `author`/`publisher` de `CreativeWork` — confirmado por
`tests/test_sobre_jsonld.py`, que carrega e valida os 3 blocos como
JSON real, nunca uma cópia.

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
só passou a ser clicável. Corre com `--apenas-sincronizar --write` em
qualquer página que já tenha o bloco (contagem real é sempre
`grep -rl "sobre.html#nvlabs" --include="*.html"`, nunca fixada aqui);
idempotência confirmada.
`assets/css/branding.css` ajustado (`.footer-nvlabs` de `<div>` para
`<a>`, com `:focus-visible`).

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

Duas fontes de frescura na homepage, ambas automáticas e nenhuma inventa
datas: A) "Últimas notícias", de `data/noticias.json`; B) "Atualizado
recentemente", do carimbo real de cada artigo. Diagnóstico e narrativa da
reformulação original (2026-07-02) e das correcções seguintes de feeds/
selecção (2026-07-04) vivem em `HISTORICO.md`, não aqui.

### A) "Últimas notícias" — `data/noticias.json` + `gerar_noticias.py` + `NOTICIA-HOME:INICIO/FIM`

`data/noticias.json` é a fonte de verdade — `noticias.html` (destaque +
arquivo por mês, ordenado por data real desc) e o bloco `NOTICIA-HOME` de
`index.html` (2-3 itens mais recentes) são sempre **gerados** a partir dele,
nunca editados directamente. `sincronizar_saidas()` é o único ponto que
regenera as duas saídas a partir do JSON em disco — idempotente, chamado
sempre no fim de `main()` (com ou sem vencedor novo no dia, para nunca
ficarem presas a conteúdo antigo se o JSON mudar por outra via); disponível
como passo manual isolado via `python scripts/gerar_noticias.py --sync`.

Cada item: `data_iso`, `titulo` (sem sufixo "- Fonte"), `fonte_nome`, `url`,
`resumo`, `categoria` (filtros de `noticias.html`) e `cluster_id`
(classificação best-effort — ver bloco próprio abaixo).

**Selecção** (`selecionar_vencedores()`): até `MAX_VENCEDORES_POR_DIA` (3)
vencedores por corrida, no máximo 1 por categoria — slots são sempre
oportunistas, nunca quota: uma categoria sem candidato com score positivo,
dentro da janela de recência (`JANELA_RECENCIA_DIAS`, 7 dias) e não
duplicado fica simplesmente vazia, nunca se publica algo fraco só para
preencher diversidade. Dedup (`encontrar_duplicado()`) por título
normalizado (`difflib`, limiar 0.90) e por URL canónico exacto — mas só
quando o URL não é a homepage genérica de um domínio
(`_url_e_especifica()`), para não confundir duas fontes distintas que citam
o mesmo domínio. `FEEDS` tem um feed por tema do site — ver essa constante
em `gerar_noticias.py` para a lista actual, nunca fixar aqui a contagem (já
divergiu uma vez sem ninguém dar por isso). `LIMITE_ENTRADAS_POR_FEED` (15)
é quantas entradas de cada feed são examinadas por corrida.

**`cluster_id`**: `detectar_cluster()` percorre `CLUSTER_KEYWORDS` e passa
cada keyword por `_contem_keyword()` — a maioria é substring simples, mas
qualquer keyword que colida com palavras comuns (hoje: "ias", "ase",
"reforma") exige fronteira de palavra (`\bkw\b`) para não apanhar
"baseadas"/"quase"/"reformados" por engano. **Regra para qualquer keyword
nova**: se puder ser substring de uma palavra comum não relacionada,
precisa da mesma fronteira — foi a falta dela que classificou 2 notícias de
desemprego/IRS como apoios-escolares só por "ase" ser substring de "quase"/
"baseadas" (corrigido 2026-09-09, #190). Desde #189 (mesma data),
`cluster_id` é renderizado nos cards de `noticias.html` — bloco "Relacionado
com o guia X" (`.pertence-guia`, sourced de `data/clusters.json` via
`carregar_clusters()`, nunca uma URL construída à mão); sem `cluster_id` ou
com um id removido de `clusters.json`, o card não mostra nada. `python
scripts/gerar_noticias.py --recalcular-clusters [--dry-run]` recalcula o
`cluster_id` de itens já gravados sem esperar por notícia nova.

**Guardrail**: `escrever_ficheiro_seguro()` é uma allow-list estrita — ver
"REGRA DE OURO — FICHEIROS AUTO-GERADOS vs MANUAIS" no topo deste ficheiro
para a lista exacta de ficheiros de escrita livre e a secção confinada de
`index.html`; qualquer nome fora dessas duas listas é sempre bloqueado.

**Observabilidade**: cada corrida regista no log candidatos por feed,
rejeições com motivo (score, duplicado, fora da janela de recência) e os
vencedores finais. `data/feeds_saude_hoje.json` — snapshot diário por feed
(`OK`/`MORTO`; XML malformado conta sempre como `MORTO`, mesmo com HTTP
200) — consumido por `gerir_estado_feeds.py` (máquina de estados,
`data/estado_feeds.json`, Issue `feed-morto` só ao 3.º dia consecutivo,
fecho automático ao recuperar). `data/noticias_candidatos.json` — log
auditável dos últimos 14 dias corridos, classifica **todos** os candidatos
dentro da janela de recência (`vencedor`/`rejeitado_score`/
`rejeitado_duplicado`/`nao_escolhido`) — para "o sistema viu a notícia X?"
ter sempre resposta.

### B) "Atualizado recentemente" — `sincronizar_clusters.py` + `ATUALIZACOES:HOME:INICIO/FIM`

3-4 artigos com o "Verificado a ..." mais recente (extraído do corpo real de
cada página `tipo: "artigo"`, nunca do RSS, nunca inventado) — sempre
verdadeiro por construção, porque reflecte edições reais do site.
`extrair_verificado_em()` aceita os 3 formatos usados nos artigos publicados
(`DD/MM/AAAA`, "D de mês de AAAA", "D mês AAAA") e usa sempre a **última**
ocorrência no ficheiro (a mais próxima do bloco de fontes no fim do corpo —
as anteriores são notas por secção). Ordem determinística: data
decrescente, slug como desempate — nunca aleatória, para a saída ser
idempotente. Escrito por `scripts/sincronizar_clusters.py` (script de
**sessão manual**, não do pipeline automático — ver "REGRA DE OURO").

**Posição na homepage**: logo a seguir a "Guias principais"
(`DESTAQUES:HOME`) e antes de "Como funciona".

### Regra de honestidade

Nenhum dos dois blocos mostra alguma vez "hoje" ou uma data inventada. Se
uma fonte falhar (RSS sem itens relevantes, ou um artigo sem "Verificado a"
reconhecível), o bloco correspondente simplesmente não é actualizado nessa
corrida — mantém o último conteúdo real. A) liga sempre directamente à
fonte externa, nunca um link interno inventado; sem vencedor no dia,
`data/noticias.json` não é tocado. Zero factos de memória, mesma regra do
resto do site.

---

## RESPOSTA RÁPIDA + CHECKLIST FINAL

Dois componentes reutilizáveis — padrão obrigatório em qualquer artigo
novo de conteúdo, não um retrofit pontual (ver "CHECKLIST OBRIGATÓRIA
ANTES DE QUALQUER COMMIT" para a obrigação; quais páginas já os têm é
sempre `PAGINAS_ALVO` em `tests/test_resposta_rapida_checklist.py`,
nunca uma contagem fixa aqui — ver "AUTO-ACTUALIZAÇÃO DESTE FICHEIRO").

### `.resposta-rapida` — reaproveita `.resposta-direta`, não duplica

A mesma `.resposta-direta` já existente no hero ganha a classe extra
`resposta-rapida` mais dois elementos, nunca uma caixa duplicada:

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
recalculado em runtime.

### `.checklist-final` — `assets/css/checklist.css` + `assets/js/checklist.js`

Mesmo padrão de `share.js`/`share.css` (ficheiro partilhado em
`assets/`, ligado via `<link>`/`<script>` no `<head>`, nunca duplicado
inline por página). **Estado só em memória** — `checklist.js` nunca
chama `localStorage`/`sessionStorage`; recarregar a página repõe todas
as checkboxes por marcar, por desenho.

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

Posicionado antes da secção "Dúvidas frequentes"; numa página sem FAQ
visível dedicada, antes de `RELACIONADOS`, ainda assim no fim do corpo
do artigo — nunca inventar uma secção que a página não tem.

### Testes

`tests/test_resposta_rapida_checklist.py` — cobertura real sempre em
`PAGINAS_ALVO`, nesse ficheiro; nunca fixar aqui a lista de páginas nem
o número de casos.

---

## GERADOR DE DOCUMENTOS

Minutas de requerimentos, reclamações e cartas dirigidas à Segurança
Social, geradas 100% no browser (`PROMPTGERADORDOCUMENTOSv1.md`, documento
externo, nunca commitado). Ver `ROADMAP.md` → "GERADOR DE DOCUMENTOS —
ESTADO" para o índice rápido do que falta.

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
via `gtag`) — um evento GA4 é uma chamada de rede real, e a mensagem "os
dados que preenches nunca saem do teu dispositivo" tem de ser verdade a
sério, não só quanto ao conteúdo do formulário. Zero
`localStorage`/`sessionStorage` — estado só em memória (mesmo padrão de
`checklist.js`).

### Integração no sistema de clusters

`cluster_da_pagina()`/`processar_pagina()` em `sincronizar_clusters.py`
comparam `Pagina.slug` só contra `caminho.name` (basename) — desenhado
para páginas na raiz, nunca preparado para sub-caminhos como
`documentos/...` (ao contrário do `pillar`, que já tem uma função
própria, `cluster_do_pillar()`, para caminhos com `/`). Por isso as
páginas do gerador (`documentos.html` + cada minuta) ficam em
`EXCLUIDAS` — mesma categoria de `comecar-aqui.html`/`simuladores.html`
— e a integração é feita inteiramente por fora do sistema de clusters:
nav (link "📄 Documentos" em `scripts/sincronizar_nav.py`, mesmo padrão
do link "🧮 Simuladores"), `sitemap.xml`, `scripts/pesquisa.js`, cards no
hub `/documentos.html`, e cross-links manuais a partir das páginas de
prestações relevantes — ver `ROADMAP.md` para o trabalho futuro
registado de generalizar `Pagina.slug`.

### Regras do portão de verificação — activas para qualquer minuta futura

- **Nunca apresentar uma minuta como substituto de um Mod. oficial** —
  quando existe um formulário próprio (Mod. numerado) para o mesmo
  pedido, a minuta é sempre uma carta de acompanhamento desse Mod.,
  nunca uma alternativa a ele. É o critério que decide se uma candidata
  precisa de "pivot" (ver os resultados por candidata mais abaixo).
- **O recurso ao SVI nunca é cross-linkado com `amim.html`, deliberadamente**
  — são dois sistemas de junta médica diferentes (SVI é da Segurança
  Social, para prestações contributivas; AMIM é da Saúde, atestado
  multiuso); cruzá-los confundiria o leitor sobre qual processo seguir.

### Minutas publicadas — estado do portão de verificação

12 minutas publicadas em `documentos/`, nenhuma rejeitada. 7 sem pivot
(nenhum Mod. oficial equivalente):

| Minuta | Base legal / canal |
|---|---|
| `reclamacao-decisao-seguranca-social.html` | CPA art. 191.º-192.º (DL 4/2015) — regime geral, sem Mod. próprio, prazo 15 dias úteis |
| `recurso-hierarquico-seguranca-social.html` | CPA art. 193.º-198.º |
| `exposicao-atraso-processamento.html` | CPA art. 128.º-129.º (prazo geral de 90 dias) |
| `requerimento-reavaliacao-escalao-ase.html` | processo descentralizado por agrupamento de escolas, sem Mod. nacional da DGE |
| `pedido-acesso-documentos-administrativos.html` | Lei n.º 26/2016 (LADA), art. 12.º/15.º, prazo 10 dias úteis |
| `requerimento-generico-seguranca-social.html` | catch-all, direito de petição (art. 52.º CRP) — nunca substitui um Mod. existente nem contesta uma decisão já tomada |
| `pedido-declaracao-comprovativo-prestacoes.html` | sem Mod. numerado — página recomenda a Segurança Social Direta como canal mais rápido, esta minuta como alternativa em papel |

5 com pivot para carta de acompanhamento de um Mod. oficial (regra do
portão acima):

| Minuta | Mod. oficial que acompanha |
|---|---|
| `carta-acompanhamento-reavaliacao-abono.html` | Modelo GF58-DGSS (`abono-de-familia.html`) |
| `carta-acompanhamento-csi.html` | Modelos CSI 1/CSI 1.1/CSI 1.2 (`complemento-solidario-idosos.html`) |
| `carta-acompanhamento-divida-prestacoes.html` | Mod. IMP.PN.01.01 |
| `carta-acompanhamento-comunicacao-alteracao.html` | Mod. GF 37-DGSS/GF 54-DGSS (ou "Declaração de Situação Familiar" na SS Direta) |
| `carta-acompanhamento-svi-recurso.html` | Mod. SVI 55-DGSS, prazo de 10 dias (mais curto que os 15 dias do regime geral) |

**Excluída à partida, nunca avaliada**: procurações e qualquer documento
com efeitos de representação legal.

Cross-links a partir das páginas de prestação relevantes (abono,
CSI, RSI, subsídio de desemprego, baixa médica, PSI, ASE) apontam para
a minuta correspondente; o hub `/documentos.html` lista as 12.

### Disclaimer obrigatório

Presente em texto idêntico em todas as páginas do gerador (`documentos/*.html`,
listadas no hub `/documentos.html`) E no texto gerado de cada minuta
(verificado por `tests/test_gerador_documentos.py::test_disclaimer_presente_na_pagina_e_no_texto_gerado`):
> "Este documento é um modelo informativo e não substitui aconselhamento
> jurídico. Confirme sempre os requisitos junto da Segurança Social ou de
> um advogado/solicitador."

### Testes

`tests/test_gerador_documentos.py` — Chromium real via Playwright, mesmo
padrão de `test_acessibilidade.py`, nunca `file://`: formulário
preenchido gera texto com todos os campos, campo obrigatório vazio
bloqueia + mostra erro, NISS inválido bloqueia com mensagem de padrão,
disclaimer presente na página e no texto gerado, botão Copiar existe e
fica activo após gerar, consistência do hub (cada card aponta para
ficheiro real, cada minuta linka de volta), e zero pedidos de rede ao
interagir com o gerador. Genérico sobre todas as páginas via
`page.evaluate("CONFIG_DOCUMENTO")` — nunca hardcoded por minuta, mesma
filosofia de `test_simulador_csi_calculo.py`. `test_nav_tem_link_documentos`
em `tests/test_nav_coerencia.py` (mesmo padrão de
`test_nav_tem_link_simuladores`) confirma o link na nav.

---

## CALENDÁRIO DE PAGAMENTOS DA SEGURANÇA SOCIAL

Página evergreen `calendario-pagamentos-seguranca-social.html` — URL
única que acumula autoridade; o conteúdo do mês é sempre injectado,
nunca reescrito à mão. Narrativa completa (triangulação inicial de
julho 2026, diagnóstico que corrigiu a data-alvo do scraping, histórico
do scraper) vive em `HISTORICO.md`, não aqui.

**Invariante crítico**: a página nunca mostra um mês passado como
corrente, e nenhuma data vem de memória — só da fonte oficial pública
`https://www.seg-social.pt/ptss/pssd/pagamentos` (ver
`docs/FONTE-CALENDARIO.md`). Sem dados do mês corrente, degrada para um
bloco explícito "consultar fonte oficial" — nunca uma tabela velha
silenciosa.

### Arquitectura

- **`data/calendario_pagamentos.json`** — fonte de verdade
  (`atualizado_em`, `fonte_url`, `meses[].pagamentos[]` com
  dia/prestações/método/nota).
- **`scripts/atualizar_calendario.py`** — injecção idempotente
  (`--dry-run` disponível), confinada a `CAL:META:INICIO/FIM` (title +
  meta description com o mês corrente) e `CAL:CORPO:INICIO/FIM` (tabela
  do mês; secção "Quando recebo a minha prestação?" com 10 âncoras —
  `#pensoes`/`#csi`/`#psi`/`#abono-familia`/`#subsidio-desemprego`/
  `#subsidio-doenca`/`#parentalidade-social`/`#rsi`/`#apoio-renda`/
  `#cuidador-informal`, `VISTA_PRESTACOES` — e o mês seguinte quando
  disponível). Validação dura antes de escrever (allow-list
  `PRESTACOES`, dias 1-31, listas não vazias, `fonte_url` só de
  seg-social.pt, mês duplicado) — falha sem tocar no HTML. Meses
  passados nunca são renderizados, mesmo presentes no JSON.
- **`og:title` estável, sem mês** (decisão deliberada): o manifest das
  imagens og (`tests/test_og_image.py`) exige `og:title == manifest` —
  um título mensal obrigaria a regenerar a imagem todos os meses. Só
  `<title>`/description variam com o mês.
- **Destaque "Próximo pagamento"** no topo, antes da tabela: camada
  estática (sempre visível mesmo sem JS, com todas as datas do mês) +
  `#cal-dados` (JSON `dia`+`resumo` curto por pagamento) que um script
  de runtime lê para promover a próxima data a contar de hoje — só
  quando o mês renderizado é o mês corrente do visitante; num mês velho
  (aviso de desatualização activo) ou em estado degradado nunca inventa
  um "próximo", e a camada estática mantém-se.
- **Guarda JS em runtime** (progressive enhancement, zero rede): compara
  `#cal-corrente[data-mes]` com a data do visitante e mostra
  `#cal-aviso-desatualizado` se a página tiver ficado velha.
- **`tests/test_calendario_frescura.py`** — canário de frescura (falha
  se o mês renderizado for anterior ao mês real), sincronização
  página↔script↔JSON, estado degradado (JSON vazio ou só com meses
  passados nunca rende tabela), caminhos de falha da validação, e
  Playwright mobile (375px sem overflow, âncoras, guarda JS).
- Integração: `EXCLUIDAS` em `sincronizar_clusters.py` (página
  utilitária cross-cluster, mesma categoria de `simuladores.html`),
  nav/sitemap/pesquisa.js/og-image próprios, cross-links nos dois
  sentidos com as páginas de prestações (parágrafo "📅 Em que dia do mês
  é pago?", com âncora directa) + botão em `comecar-aqui.html` (link sem
  âncora — o grafo de órfãs de `test_higiene_indexacao.py` não segue
  hrefs com `#fragmento`).

### Scraping automático

Fonte pública real: `https://www.seg-social.pt/ptss/pssd/pagamentos` —
SPA com um separador por mês, sem gateway de login; o fluxo manual
(sonda + Issue) é só o *fallback*.

- **`scripts/scraper_calendario.py`** — `parse_innertext()` (texto do
  painel do mês → schema do JSON) + `raspar_mes()` (Playwright: clica no
  separador, espera pelo cabeçalho do mês e por uma linha de método).
  Mapeamento estrito `NOME_PARA_SLUG`; prestação fora da allow-list, mês
  vazio ou método órfão fazem **falhar** (`ScraperError`) — nunca
  descarta em silêncio.
- **`.github/workflows/calendario-mensal.yml`** — dia 25 + retry 28
  (alvo: mês seguinte) e dia 1 às 05:30 (alvo: mês corrente — vira a
  página quando o JSON já tem o mês novo); `workflow_dispatch` com
  `forcar_seguinte`. Se o JSON tem o mês alvo → injecção idempotente +
  `pytest tests/test_calendario_frescura.py` + guardrail (falha se
  qualquer ficheiro fora do JSON + página aparecer modificado) +
  commit/push + `garantir_deploy_pages.sh` + smoke inline; fecha
  automaticamente a Issue `calendario-manual` do mês. Se não tem →
  tenta o scraper; sucesso grava o mês no JSON. Só se o scraper falhar
  → **nunca commit parcial**: sonda as rotas oficiais e abre/actualiza
  (dedup por título) a Issue `calendario-manual` com o erro do scraper
  + sonda + prompt pronto. `concurrency: main-writes`.
- **`scripts/verificar_calendario_mensal.py`** — decide o mês alvo (dia
  ≥ 20 → mês seguinte); se o JSON não o tem, chama
  `tentar_scraper_e_gravar()` (grava só dados que passem a validação);
  fallback = sonda `/ptss/pssd/noticias` + Issue. Emite `estado`/
  `mes_alvo` via `GITHUB_OUTPUT`.

Para o `pipeline-diario.yml`, esta página continua a ser HTML manual
protegido como qualquer outra. `pagamento-apos-deferimento.html`
("Pedido deferido: quando cai o primeiro pagamento") é a página irmã
evergreen — tabela por prestação (desemprego/doença/parental/abono/
RSI/pensão/CSI) e cross-links nos dois sentidos com o calendário.

**Cross-link PSU**: nas 4 linhas cujo regime **não-contributivo** consta
da lista dos 13 apoios (pensão social de velhice/invalidez, subsídio
social de desemprego, subsídios sociais de parentalidade, RSI), uma
nota aponta para `/prestacao-social-unica.html` confirmando a conversão
oficiosa a partir de 31 de dezembro de 2026 (artigo 57.º do Decreto-Lei
n.º 166/2026, hoje já publicado e em vigor — ver "IMPACTO DA PSU" para o
estado do diploma). CSI e PSI ficam de fora das 4 linhas — ver
"PENDÊNCIA PSI vs PSU — FECHADA" na mesma secção para a distinção entre
exclusão explícita (CSI) e exclusão por omissão (PSI). Implementado
dentro do próprio gerador (`PSU_NOTAS` em `atualizar_calendario.py`,
aplicado em `_seccao_por_prestacao()`) — sobrevive a qualquer
regeneração mensal do `calendario-mensal.yml`, nunca um add-on manual
que a próxima corrida apagaria.

---

## MEDIÇÃO DE CONVERSÃO — EVENTOS GA4

Instrumentação de conversão, sem qualquer alteração de layout/conteúdo/
Schema. Cada evento vive no JS já existente da funcionalidade respectiva
— nunca um `eventos.js` global partilhado.

**Padrão obrigatório de qualquer evento novo**: guarda `typeof gtag ===
'function'` antes de chamar (o gtag.js carrega sempre com Consent Mode v2
avançado; em `denied` os eventos seguem como pings sem cookies — comportamento
correcto, nunca contornar). **Nenhum parâmetro transporta dados introduzidos
pelo utilizador** — só o facto de a acção ter terminado (mais, quando o
simulador o determina, um veredicto de elegibilidade, que é uma conclusão do
simulador, nunca um valor introduzido).

| Evento | Onde | Parâmetros | Notas |
|---|---|---|---|
| `simulacao_concluida` | inline nos simuladores publicados que disparam este evento (grep `simulacao_concluida` em `simulador-*.html`; hoje: abono, ase, csi, subsidio_doenca, rsi, subsidio_desemprego, imt_jovem, psu, condicoes_reforma), a par do `calc_resultado` já existente | `simulador` (slug), `elegivel` (só onde há veredicto binário) | `elegivel` presente em abono (`escalão ≠ 5`), ase (com/sem direito), csi (`temDireito`), subsidio_desemprego (prazo de garantia), imt_jovem e condicoes_reforma; **omitido** em subsidio_doenca, rsi e psu — sem veredicto binário limpo (rsi é multi-factor e auto-declara-se incompleto). |
| `menu_tool_click` | `assets/js/nav.js`, clique nos cartões da grelha de ferramentas do menu móvel e no link "Começa aqui" (`.nav-mobile-card`/`.nav-mobile-destaque`) | `tool_destino` (basename do próprio `href`, nunca um ID fixo por cartão) | Só no menu móvel, não no desktop. |
| `partilha_clique` | `assets/js/share.js`, nos dois pontos de sucesso (Web Share API e cópia para a área de transferência) | `pagina` (pathname) | Nunca no fallback da caixa manual (falha de cópia) nem em cancelamento (AbortError). Nunca envia o título. |
| `comecar_aqui_percurso` | `comecar-aqui.html` | evento de início (`etapa: 'inicio'`, primeira escolha) e evento final (`etapa: 'fim'`, `destino` = pathname recomendado) | Mede a taxa de conclusão do funil. `destino` é o apoio recomendado (primeiro card) ou `/#guias-de-apoios`, nunca as respostas do quiz. |
| `cal_home_clique` | `index.html`, clique na barra fixa `.cal-topo` (é um `<a>`, é clicável) | — | GA4 usa `sendBeacon` por omissão, por isso o evento sobrevive à navegação. |

**`documento_gerado` — deliberadamente NÃO implementado**: o gerador de
documentos tem a invariante dura, documentada e testada, de **zero pedidos
de rede depois do load**
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
`tests/test_share_js.py` (testes funcionais Chromium para `partilha_clique`:
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
(hoje não existe, ver acima). `menu_tool_click`, `partilha_clique` e
`cal_home_clique` são úteis como micro-conversões, opcional marcá-los.

---

## SCHEMA.ORG — GRAFO DO SITE (WebSite + CollectionPage)

JSON-LD ao nível do site (grafo entre páginas) — o JSON-LD de cada artigo
(`FAQPage`/`HowTo`/`BreadcrumbList`/`Article`) é assunto à parte, correcto
e não relacionado com esta secção.

### WebSite único, na homepage

- O bloco `WebSite` vive **só** em `index.html`, com `@id`
  `https://tensdireito.com/#website`, `publisher` a referenciar a
  `Organization` da NV Labs por `@id`
  (`https://tensdireito.com/sobre.html#nvlabs`, definida em `sobre.html`).
  Nunca dois `WebSite` com `@id` diferentes — `sobre.html` mantém só
  `AboutPage` + `Organization` (a entidade NV Labs continua resolvível
  lá).
- **Sem `potentialAction` (`SearchAction`)** — existiu entre 2026-07-16 e
  2026-07-18, removido depois de o GSC reportar
  `https://tensdireito.com/?pesquisa={search_term_string}` como "Rastreada
  — atualmente não indexada": a Google descontinuou a sitelinks search box
  em outubro de 2024, o markup deixou de ter função. A funcionalidade de
  pesquisa em si (`?pesquisa=`, `pesquisa.js`) nunca foi tocada — só o
  `potentialAction` estruturado saiu; o `canonical` da homepage (sem query
  params) absorve qualquer variante `?pesquisa=...` que o Google tenha
  rastreado. Nenhum script gera este bloco (é escrito à mão em
  `index.html`).
- Cuidado de manutenção: o `pipeline-diario.yml` (Step 6, `sed`)
  actualiza o campo `"dateModified"` deste bloco `WebSite` em `index.html`
  — não mexer na linha sem confirmar que o `sed` continua a apanhá-la.

### CollectionPage + ItemList nas pillar pages

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
  o `PILLAR-LISTA`. Aplica-se a **todos** os pillars de
  `data/clusters.json` (fonte única — nunca fixar aqui a contagem de
  clusters, ver "SISTEMA DE CLUSTERS"). Cada pillar fica com `Article` +
  `FAQPage` + `BreadcrumbList` + `CollectionPage` — sem duplicar tipos.
- Testes: `tests/test_sincronizar_clusters.py` estendido — injecção,
  idempotência do bloco, 1:1 `ItemList`↔`clusters.json` (unidade em
  `tmp_path` **e** guarda sobre os pillars reais), e pillar com
  `PILLAR-LISTA` mas sem `PILLAR-JSONLD` é reportada sem escrever (a
  presença dos dois marcadores é obrigatória numa pillar).
  `test_breadcrumb_coerencia.py` reconfirmado sem regressão.

### E-E-A-T — NV Labs como entidade resolvível

Sem autor pessoal público (decisão do Nuno, mantida), o E-E-A-T do
site joga-se a nível de entidade + método. A **NV Labs** — estúdio
independente português, responsável editorial do Tens Direito — é
**resolvível**: "An NV Labs project" no footer liga a
`sobre.html#nvlabs`, que tem secção própria (ver "PÁGINAS
INSTITUCIONAIS") e JSON-LD `Organization` próprio. **Sem `sameAs`** —
o único que chegou a existir apontava para o repositório GitHub,
removido pela regra de zero menções a GitHub em página pública (ver
"REGRAS DE CONTEÚDO" → "Não fazer"). Regra permanente: nunca inventar
um perfil para preencher esse campo — sem um perfil público real da
NV Labs, o `sameAs` fica ausente.

### Autoria nos artigos — `scripts/adicionar_autoria_artigos.py`

Novo script, âmbito automático (todas as páginas com `"@type":
"FAQPage"` em `*.html`/`p/*.html` — contagem real é sempre
`grep -rl '"@type": "FAQPage"' --include="*.html"`, nunca fixada aqui;
`simulador-psu.html` fica fora por não ter JSON-LD nenhum,
deliberadamente não publicado):

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

### PASSO MANUAL PARA O NUNO — validar depois do deploy

Depois do deploy, validar no **Rich Results Test**
(search.google.com/test/rich-results) e/ou no **Search Console** (relatório
de dados estruturados): a homepage (`WebSite`, sem `SearchAction`) e uma ou
duas pillar pages (`CollectionPage` + `ItemList`). Não é possível validar
por código contra a Google — a validação local é estrutural (JSON real,
`@id` coerentes, `position` sequencial, URLs absolutos).

---

## AUTO-ACTUALIZAÇÃO DESTE FICHEIRO

Sempre que houver mudança significativa, actualizar a secção relevante do
CLAUDE.md no mesmo commit — nunca acrescentando uma entrada nova no fim
deste ficheiro. O registo cronológico de sessões ("Última revisão:
AAAA-MM-DD — ...") vive em `HISTORICO.md`; é lá, sempre ao fim desse
ficheiro, que uma sessão regista o resumo do que fez — nunca aqui.

Triggers obrigatórios de actualização (de CLAUDE.md e/ou HISTORICO.md):
- Alteração a `.github/workflows/`
- Alteração a `scripts/`
- Adição ou remoção de página HTML publicada
- Mudança nas regras de conteúdo ou de links
- Mudança na stack (novos serviços, remoção de dependências)

**Regra permanente — nunca afirmar uma contagem que o repositório já sabe
contar**: nenhuma secção deste ficheiro fixa o número de páginas, feeds,
workflows, clusters, sentinelas, fontes scraped ou qualquer outra coisa
que já vive, contável, num ficheiro/constante/directório do repositório.
Aponta sempre para essa fonte — "as páginas listadas em
`scripts/pesquisa.js`", "os feeds em `FEEDS` (`scripts/gerar_noticias.py`)",
"os workflows em `.github/workflows/`" — nunca "27 páginas"/"13
feeds"/"8 workflows". Um número certo hoje não prova nada: é só um
número que ainda não divergiu, e diverge sempre que o ficheiro/constante
muda sem alguém lembrar de actualizar a prosa (já aconteceu mais do que
uma vez nesta secção do ficheiro — contagem de pillars, de feeds, de
fontes do scraper). Onde um número for mesmo necessário para a frase
fazer sentido — um limiar, uma janela de dias, uma constante de negócio
como `MAX_VENCEDORES_POR_DIA` — mantém-se, mas sempre com a fonte ao
lado, nunca como facto solto, e justificado caso a caso.

---

---

## PÁGINAS COM DATAS SAZONAIS

Páginas que têm datas que expiram e precisam de revisão manual anual:

| Página | Data a rever | Trigger |
|---|---|---|
| `manuais-escolares-mega.html` | **Datas de emissão 2026/2027 já publicadas (13/07/2026): 3 ago (1.º–4.º), 10 ago (5.º–9.º), 13 ago (10.º–12.º)** — próxima revisão jun. 2027 | Issue automática do scraper (`dge.mec.pt` **e** `igefe.mec.pt`, desde 2026-07-06) — ver nota abaixo |
| `acao-social-escolar.html` | Setembro — prazo de candidatura ("até 30 de setembro"), **nunca** escalões (ver nota abaixo) | Redundante com `calendario-escolar-apoios.html`, mantida por cautela |
| `bolsa-de-merito.html` | Setembro — valor do ano lectivo (2,5×IAS em vigor), **nunca** um despacho próprio (ver nota abaixo) | Calendário anual — corrigida a 25/08/2026, ver nota |
| `abono-de-familia.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `rsi.html` | Janeiro (novo IAS/RSI) | Issue automática do scraper |
| `complemento-solidario-idosos.html` | Janeiro (novo valor CSI) | Issue automática do scraper |
| `prestacao-social-unica.html` | Ago 2026 (decreto-lei publicado, já em vigor) + **31 de dezembro de 2026** (produção de efeitos, art. 63.º DL 166/2026) | Ver "IMPACTO DA PSU" |
| `psu-quando-entra-em-vigor.html` | Idem | Ver "IMPACTO DA PSU" |
| `psu-quem-tem-direito.html` | Idem | Ver "IMPACTO DA PSU" |
| `psu-vs-abono-familia.html` | Idem — `verificar_datas.py` passa a expor sozinho a partir de 2027 (Issue #186) | Ver "IMPACTO DA PSU" |
| `simulador-psu.html` | Idem — banner de vigência já ligado a `data_producao_efeitos` | Ver "IMPACTO DA PSU" |
| `subsidio-desemprego.html` | Janeiro (novos limites) | Issue automática do scraper |
| `majoracao-subsidio-desemprego.html` | **31 de dezembro de 2026** — o Decreto-Lei n.º 166/2026 (art. 49.º) altera a redação do n.º 5 do art. 28.º-A do DL 220/2006 nesta data (a majoração passa a manter-se quando o cônjuge transita para a PSU, em vez de "subsídio social de desemprego subsequente") — rever a secção "Se a situação mudar" e a FAQ correspondente, confirmando que o texto passa de "vai mudar a partir de" para o estado já em vigor | A partir de 2027, `verificar_datas.py` expõe isto sozinho (portão de confirmação de `MARCADORES_HISTORICOS`, #187); até lá, verificação manual, mesma data já vigiada pelo `pipeline-diario.yml` para o resto do cluster PSU |
| `garantia-publica-credito-habitacao.html` | **31 de dezembro de 2026** — prazo-limite dos contratos abrangidos pela Garantia Pública (Portaria n.º 236-A/2024/1), sem prorrogação confirmada | `dre_habitacao_garantia` (watchlist DRE) — ver "CLUSTER HABITAÇÃO" |
| `fontes.html` | Idem — cartão da Portaria n.º 236-A/2024/1 cita a mesma cláusula de vigência | Idem — ver "CLUSTER HABITAÇÃO" |
| `subsidio-parental.html` | Janeiro (novo IAS) | Issue automática do scraper |
| `amim.html` | Janeiro (novo IAS: afeta IRS 4×/2,5×IAS e valor PSI) | Issue automática do scraper |
| `prestacao-social-para-a-inclusao.html` | Janeiro/Fevereiro (nova portaria de actualização da PSI) | Verificação manual/news dre.pt |
| `prova-escolar.html` | Junho (ano letivo seguinte) | Calendário anual — ver nota abaixo |
| `bolsa-de-estudo-ensino-superior.html` | Verão (Despacho anual de prazos, ex.: Despacho n.º 7994/2026 para 2026/2027 — a data muda de ano para ano) | Verificação manual/news dges.gov.pt |
| `calendario-escolar-apoios.html` | Junho/Julho (antes do início do próximo ciclo de prazos) — `verificar_datas.py` confirmado a **não** disparar em jul. 2026 (mês de publicação) mas a disparar em 2027 nos meses 1/7/8/9 (padrão `data_mes_ano`, "setembro de 2026" na FAQ do início das aulas) — comportamento desejado, mesma lógica de `prova-escolar.html` | Calendário anual — agrega os prazos das páginas do cluster escolar ligadas a partir do próprio artigo (nunca fixadas aqui), revisão obrigatória sempre que qualquer um desses prazos mudar |
| `renovar-cartao-cidadao.html` | Nota de verificação para **3 de agosto de 2031** — prazo-limite real remanescente (cartões com MRZ mas sem chip de contacto, emitidos até 10/06/2024; Regulamento (UE) 2025/1208). Corrigido a 2026-07-18: o prazo de 3/08/2026 **não** se aplica ao Cartão de Cidadão normal (tem MRZ desde 2007) — só afecta duas excepções raras (CC do Tratado de Porto Seguro, BI vitalício), conforme esclarecimento oficial do IRN de 30/12/2025. `verificar_datas.py` continua a disparar em 2027 nos meses 1/7/8/9 (o texto ainda cita "2026") — sem acção obrigatória nessa altura, só confirmar que a secção "Preciso de renovar antes do prazo?" continua correcta | Sem gatilho de acção — nota de contexto, a rever se saírem novos esclarecimentos oficiais do IRN antes de 2031 |

**Nota — `simulador-rsi.html` fica de fora desta tabela, deliberadamente**:
a página existe, está publicada e integrada (nav, sitemap, `data/clusters.json`,
`pesquisa.js`), e provavelmente cita a mesma data de 31/12/2026 (produção
de efeitos do DL 166/2026) que as 5 páginas PSU/Garantia Pública acima —
mas nunca foi confirmado directamente, porque `simulador-rsi.html` nunca
chegou a entrar em `CLAUDE.md` (nem na tabela "PÁGINAS PUBLICADAS"). Em
vez de inventar uma linha com um dado não verificado, ver
[Issue #209](https://github.com/nunovinhas-creator/tens-direito/issues/209).

**`manuais-escolares-mega.html` — mecanismo de vigilância sazonal**: duas
fontes independentes, mesma chave de aviso. `mega_datas` vigia
`dge.mec.pt`; `igefe_mega` (`scripts/scraper_playwright.py`,
`metodo="http"`) vigia directamente
`https://www.igefe.mec.pt/Page/Index/199` — a entidade que emite de
facto os vouchers aos encarregados de educação é a IGeFE, I.P., não a
DGE. Selectores específicos a esta fonte (`paragrafos:
".ig-publicsite-paragraph"`, não o `"p"` genérico das outras fontes),
`min_chars_uteis=300`, `ancora_conteudo=("voucher",)`. Ambas partilham
`_detectar_datas_mega()` e a chave `mega_2026_2027_publicadas` (via
`MEGA_SLUGS_DATAS_RICAS`) — a Issue automática "📅 MEGA 2026/2027 —
datas de emissão detectadas" dispara com qualquer uma das duas,
independentemente de qual publicar primeiro. Histórico da investigação
e dos falsos positivos corrigidos: ver `HISTORICO.md`, entrada de
2026-07-06.

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

**`acao-social-escolar.html`/`bolsa-de-merito.html` — regime substantivo
sem república anual**: escalões A/B como % do IAS, tectos de material
escolar (16€/8€) e visitas de estudo (20€/10€) em euros, desconto nas
refeições (gratuita no A, 50% no B) estão fixados desde 2015 pelos
Despachos n.º 8452-A/2015, 5296/2017 e 7255/2018 — **sem nenhuma
república anual**. A única variável real é o IAS, publicado por
Portaria própria (tipicamente dezembro/janeiro) — **já vigiado pelo
sentinela `dre_ias`** (Issue automática de janeiro, ver "PÁGINAS COM
DATAS SAZONAIS" acima). O mesmo se aplica à Bolsa de Mérito: o valor é
sempre 2,5×IAS, calculado a partir do mesmo Despacho n.º 8452-A/2015 —
**nunca** um despacho anual próprio. `bolsa-de-merito.html` reflecte
isto correctamente (1.342,83 € = 2,5 × IAS 2026, "Verificado a
25/08/2026") — investigação da premissa errada original e correcção
documentadas em `HISTORICO.md`, entrada de 2026-08-25.

O prazo de "30 de setembro" em `acao-social-escolar.html` é uma regra
fixa do regime-base (não republicada ano a ano); a única coisa que o
podia genuinamente deslocar é um despacho de calendário escolar/
matrículas novo — já agregado por `calendario-escolar-apoios.html`
(ver a entrada dessa página nesta tabela). A revisão de setembro deste
artigo fica por isso redundante com essa página, mantida por cautela.

**Preço-tecto da refeição escolar**: decisão consciente de **não
vigiar** — o site expressa sempre o custo da refeição como desconto
percentual (gratuita/50%), nunca o valor em euros. Razão completa e
decisão: ver `ROADMAP.md` → "À ESPERA DE UM SINAL" → "Manuais".

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
pormenor, o que o site já documentava e acrescenta factos novos — ver a
entrada de 2026-07-28 em `HISTORICO.md` para o detalhe completo.
**Por reconciliar com o Decreto-Lei n.º 166/2026 (Issue #195)**: os 6
factos abaixo foram confirmados pela Lei n.º 36/2026, uma autorização
legislativa intermédia — ninguém confirmou ainda, afirmação a afirmação,
quais o decreto-lei manteve tal e qual, quais refinou, e quais deixaram
de ser relevantes (ex.: o ponto das ponderações de "adultos
equivalentes", abaixo marcado "ainda por fixar", pode já estar fixado em
`dados/parametros/psu.yaml`). Resumo: a lista dos 13 apoios (artigo 1.º/2) bate certo com a
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
2026-08-13/16 com os valores reais do decreto-lei (Fase 2) — ver as
entradas correspondentes a essas datas em `HISTORICO.md`. **Mais 3 páginas novas
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
pesquisa de frase exacta, a filtrar só resultados do tipo **Portaria**
(`detectar_portaria`, mesmo mecanismo do `dre_ias`) — nunca Decreto-Lei,
que já não interessa a este sentinela (é trabalho do `dre_psu`). Cobre
os dois pontos em aberto (art. 17.º; arts. 32.º/59.º) com um único
sentinela — quando disparar, a Issue automática pede para confirmar qual
dos dois é.

**Nasceu cego, corrigido a 2026-09-01 (Issues #147/#148)** — o termo
original pesquisava a **citação** do decreto-lei por número
(`'"Decreto-Lei n.º 166/2026"'`, mesmo padrão que `dre_habitacao_garantia`
usava para o DL 44/2024, na suposição de que "qualquer Portaria que o
regulamente tem de o citar na ementa"). Nunca devolveu um único
resultado em 16 dias consecutivos (2026-08-16 a 2026-08-31, confirmado
por `data/scraped/dre_psu_regulamentacao_*.json` reais) — nem no
próprio dia em que a **Portaria n.º 394/2026/1** (27/08/2026, ver
secção anterior) foi publicada, nem em nenhum dos dias seguintes. Prova
directa de que a expressão estava errada, não a fonte: `dre_psu` —
pesquisa temática `'"prestação social única"'`, mesmo motor, mesmo dia
— **já tinha essa Portaria** no seu `itens_lista` de 2026-09-01. A
pesquisa de frase exacta do DRE parece corresponder por tema/
classificação do acto, nunca por citação literal de outro diploma pelo
número — nenhum dos 4 sentinelas que sempre funcionaram
(`dre_psu`/`dre_habitacao_paer`/`dre_ias`/agora este) usa uma citação;
só os 2 que nasceram cegos usavam.

**Corrigido trocando o termo para o MESMO de `dre_psu` — deliberado,
nunca redundância**: os dois sentinelas passam a ver os mesmos
resultados brutos do DRE, mas reagem a metades opostas —
`detectar_decreto_lei_psu` (`dre_psu`) só conta Decreto-Lei;
`detectar_portaria` (este sentinela) só conta Portaria. **Nunca apagar
um dos dois por parecer duplicado** — `tests/test_dre_psu_regulamentacao.py::test_dre_psu_regulamentacao_termo_e_identico_ao_dre_psu_mas_filtros_opostos`
tranca exactamente essa distinção. Corte de recência subido de
`"2026-08-16"` para **`"2026-08-28"`**: com o termo novo, a pesquisa já
devolve a própria Portaria n.º 394/2026/1 (data completa
"Série I de 2026-08-27" no item) — sem o corte pós-27/08, ela seria
sinalizada como "nova" todos os dias, para sempre (mesmo pesadelo do
`numero_conhecido` do `dre_psu`, Issue #132, só que aqui resolvido só
com a data, porque o item real já vinha com data completa —
`_detectar_portaria_generico` nem sequer aceita `numero_conhecido`
hoje). Uma Portaria genuinamente nova (ex.: a que falta para o art.
17.º) continua a disparar normalmente. Ainda não confirmado contra um
scrape real desta sessão pós-correcção — rede bloqueada para
diariodarepublica.pt (mesma limitação de sempre); a validação disponível
é a mais próxima possível sem inventar dados: o mesmo termo, o mesmo
motor, o mesmo dia, já devolveu a Portaria via `dre_psu` — a 1.ª corrida
real do pipeline com o termo novo confirma de vez.

Novo guardrail permanente: `tests/test_dre_termos_pesquisa.py` — falha
se qualquer fonte DRE (actual ou futura) com `pesquisa_interactiva`
tiver um termo com forma de citação de diploma ("n.º" + barra + ano),
o mesmo padrão que deixou `dre_habitacao_garantia` (44 dias) e este
sentinela (16 dias) cegos sem nunca devolver um resultado.

Testes: `tests/test_dre_psu_regulamentacao.py` (30+ casos) — confirma que
`dre_psu` mantém config/perfil/forma 100% inalterados, que o próprio DL
166/2026 já não dispara `dre_psu` (regressão do achado real desta
sessão), que um decreto-lei futuro sobre a PSU ainda dispara `dre_psu`,
e cobre `dre_psu_regulamentacao` (config, presença em
`FONTES_PLAYWRIGHT`, corte de recência novo, detecção por item — Portaria
dispara, Decreto-Lei nunca dispara este sentinela específico, conteúdo
vazio nunca dispara) — mais uma secção nova de validação contra o
`itens_lista` REAL de `data/scraped/dre_psu_2026-09-01.json` (nunca
reescrito à mão): confirma que a Portaria n.º 394/2026/1 é encontrada e
isolada correctamente do resto dos resultados reais (Lei, Decreto-Lei,
Despachos), que o corte de recência novo a suprime (já tratada, commit
`d0f082a`), e que uma Portaria futura hipotética, misturada com os
mesmos dados reais, ainda dispara.

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
(ver o antigo item 9 do "Plano de acção" abaixo, e a entrada de 2026-07-04
"nova página `prestacao-social-para-a-inclusao.html`" em `HISTORICO.md`).
Facto novo, verificado pelo Nuno a
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

Gatilho documentado para uma página futura — `autobaixa.html` continua
por criar; mesmo padrão do "Cluster PSU — páginas em espera".

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
6. Checklist obrigatória completa de qualquer página nova de conteúdo —
   ver "CHECKLIST OBRIGATÓRIA ANTES DE QUALQUER COMMIT".

**Ponto ⚠️ a re-verificar nesse momento**: comunicação da autodeclaração
ao empregador — na última verificação de `baixa-medica-subsidio-doenca.html`
continuava não automática (código por SMS/e-mail que o trabalhador
tem de facultar); confirmar se entretanto passou a automática antes de
reafirmar na landing.

O anteprojecto de reforma laboral ("Trabalho XXI") sobre autodeclaração
fraudulenta como justa causa de despedimento foi removido da página
(Proposta de Lei n.º 77/XVII/1.ª chumbada na Assembleia da República) —
não reintroduzir sem um facto novo e confirmado.

---

## CLUSTER HABITAÇÃO

Pillar `p/habitacao.html` + páginas-filho — lista completa e contagem
sempre em `data/clusters.json`, cluster `habitacao` (hoje:
`porta-65.html`, `apoio-extraordinario-renda.html`, `imt-jovem.html`,
`garantia-publica-credito-habitacao.html`, `deducao-rendas-irs.html`,
`primeiro-direito.html`, `simulador-imt-jovem.html`), hub reorganizado
em três secções: 🏠 Arrendar / 🔑 Comprar / 🏚️ Situações de carência.
Fact-check prévio obrigatório (bloqueante, ver "REGRAS DE CONTEÚDO") —
com uma distinção que importa manter separada, nunca os três casos ao
mesmo nível.

**Ilegíveis por fetch simples, de qualquer lado, sessão ou não**:
`diariodarepublica.pt/dr/detalhe/...` é uma SPA que exige JavaScript a
renderizar (um `fetch`/`curl` devolve só a shell vazia, mesmo fora do
sandbox); `bportugal.pt` bloqueia acesso automatizado por detecção de
bots, incluindo os PDFs. Nos dois casos o obstáculo é do próprio site,
não da rede do Code — nenhum acesso automatizado, de lado nenhum,
resolve isto.

**Ilegível só a partir desta sessão**: `files.dre.pt` **funciona** —
serve o PDF estático da própria série do Diário da República, sem JS
nenhum a renderizar, e é hoje a única via de leitura primária de um
diploma que existe de facto (já confirmado a devolver o texto integral
de um diploma quando lido fora do sandbox — ver "FONTES VERIFICADAS E
APROVADAS" → "Verificação directa de diplomas"). O que bloqueia o
acesso a partir daqui é só a configuração de rede do sandbox onde o
Code corre (`EGRESS_BLOCKED`, observado como `403` em jul 2026 —
confirmado até para domínios sem relação nenhuma com o Estado, ex.:
`en.wikipedia.org`), nunca uma recusa do domínio em si. **Nunca tratar
`files.dre.pt` como morto** — está bloqueado a partir desta sessão, não
inacessível.

A regra é a mesma de "FONTES VERIFICADAS": a leitura primária de um
diploma via `files.dre.pt` faz-se sempre fora do Code — pelo Nuno, ou
por outro processo com acesso real à rede — e é entregue já como facto
confirmado (GRAU 1). Sem essa entrega, o fact-check destas páginas é
feito por triangulação `WebSearch` (GRAU 2, sempre identificada como
tal) ou fica marcado por confirmar (GRAU 3) — nunca por analogia. As
páginas citam sempre a URL oficial como fonte, mesmo sem acesso
directo — mesmo padrão já usado no site para fontes que devolvem 403 a
bots.

**Regra de dados**: qualquer valor
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

**Excepção conhecida, rastreada (Issue #197)**: os 2 primeiros bullets
de "Estado real verificado" abaixo — Porta 65 Jovem/Porta 65+ e o Apoio
Extraordinário à Renda (PAER) — não seguem esta regra. Os factos que
citam (datas de candidatura contínua, condições de acesso, data de
fecho a novos beneficiários) vivem só em prosa, sem entrada em
`dados/parametros/habitacao.yaml` nem canário em
`tests/test_valores_ancora.py`, ao contrário dos outros 4 bullets (IMT
Jovem, Garantia Pública, Dedução de rendas no IRS, 1.º Direito). Nada
os impede hoje de ficar desactualizados em silêncio.

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
  à data de verificação**. Por
  isso `apoio-extraordinario-renda.html` não é um guia de candidatura —
  é uma página "estado actual + alternativas", apontando para o Porta 65.
  **Reforma "produto único"**: o Governo
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
  20 jul 2026): Decreto-Lei n.º 97/2026, de 20 de maio —
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
- **1.º Direito** (`primeiro-direito.html`, publicada 20 jul 2026):
  DL n.º 37/2018 alterado por DL n.º 44/2025 (27 mar 2025,
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

**Simulador de IMT Jovem — âmbito Continente-só é decisão deliberada, não
falta de dados (2026-09-08, Issue #177)**: `dados/parametros/habitacao.yaml`
tem, desde o PR #176, a tabela geral de IMT (HPP) das Regiões Autónomas
por inteiro (`imt_geral_hpp_ra_*`, 8 parâmetros), verificada contra o
folheto oficial da AT "Os meus direitos e deveres na aquisição de um
prédio" (janeiro 2026, Ofício Circulado n.º 40129/2026) — com
testes-canário próprios em `tests/test_valores_ancora.py`. Apesar
disso, `simulador-imt-jovem.html` continua a calcular só para o
Continente: a razão original (parcelas a abater RA por confirmar) já
não existe desde o PR #176, mas a limitação em si mantém-se, agora por
opção deliberada de âmbito — manter o formulário simples, com um único
conjunto de escalões, sem selector de região. Os 4 sítios que
explicavam a limitação (`#avisoRegiao`, FAQ visível + JSON-LD,
comentário JS, lista de limitações) foram reescritos para reflectir a
razão real, deixam claro ao utilizador dos Açores/Madeira que o
resultado não se aplica ao seu caso, e apontam para o guia do IMT
Jovem, para os Dados Abertos (onde a tabela RA já vive, verificada) e
para a Autoridade Tributária. Se um dia se quiser estender o simulador
às Regiões Autónomas, os parâmetros já existem — falta só ligar a
coluna "sem isenção" a um selector de região.

### Watchlist automática DRE

`dre_habitacao_paer` (revogação do PAER/reforma "produto único") e
`dre_habitacao_garantia` (alteração/prorrogação do DL n.º 44/2024) —
mesmo mecanismo `pesquisa_interactiva` do `dre_psu` (ver "IMPACTO DA
PSU"), com corte de recência `data_minima`/`"desde": "2026-07-20"` em
`_detectar_decreto_lei_generico` (`scripts/scraper_playwright.py`) — só
conta "novo" um item datado a partir da activação da watchlist.
`dre_habitacao_garantia` pesquisa a frase legal exacta **"garantia
pessoal do Estado"** (nunca "garantia pública", termo genérico demais,
nem a citação por número do diploma) — confirmada contra o motor real:
devolve a Portaria n.º 236-A/2024/1, que regulamenta o DL 44/2024.
`tests/test_dre_termos_pesquisa.py` é guardrail permanente: nenhuma
fonte DRE (actual ou futura) com `pesquisa_interactiva` pode usar um
termo em forma de citação de diploma ("n.º" + barra + ano) — foi essa
forma, não um bloqueio real do DRE, que deixou este sentinela e
`dre_psu_regulamentacao` cegos durante semanas.

O diff genérico "Detectar mudanças e registar" (`pipeline-diario.yml`)
compara `itens_lista` em bruto para todas as fontes DRE sem filtrar por
tipo de acto legal — dominado por ruído (ex.: Resoluções do Conselho de
Ministros sem relação com o diploma vigiado). `dre_habitacao_garantia`
tem uma allow-list scoped (`DRE_SLUGS_PESQUISA` + `ACTO_LEGAL_REGEX`, só
Decreto-Lei/Lei/Portaria/Despacho) que filtra esse ruído antes do diff
— **deliberadamente não generalizada** às outras 4 fontes DRE sem
confirmar primeiro o perfil de ruído de cada uma (`dre_habitacao_paer`
tem um caso real, um "Regulamento" da Série II, fora desta allow-list,
que o mesmo filtro apagaria por engano — ver `tests/test_diff_mudancas_issue.py`).

**Gap aberto (Issue #198)**: a Portaria n.º 187/2025/1 (1.ª alteração à
236-A/2024/1, achada pela allow-list acima) continua por fact-checar e
por acrescentar a `dados/parametros/habitacao.yaml` — confirmada só por
`WebSearch`, nunca o texto legal directo. Antes de acrescentar
`fonte_url_complementar` (mesmo padrão do CSI): confirmar se altera
algum dos 6 valores já publicados da Garantia Pública (idade 18-35,
tecto 450.000€, 15%, 10 anos, prazo 31/12/2026, 8.º escalão de IRS) —
nunca assumir que é só alteração de forma.

**Registado para o futuro, sem prazo**: nova tabela de rendas máximas de
referência do Porta 65 (publicação anual, fora do alcance da watchlist
DRE — é um PDF administrativo, não um decreto-lei; ver `ROADMAP.md` →
"À espera de um sinal").

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

## CANAL DE WHATSAPP — GATILHO EDITORIAL DE PUBLICAÇÃO

O convite ao canal (bloco `<!-- CANAL WHATSAPP -->` em `index.html` +
nos artigos de maior tráfego — contagem real é sempre `grep -l
"Avisamos só quando uma regra muda a sério" *.html` menos `index.html`,
nunca fixada aqui; PR #140, 2026-08-30, acrescentou os primeiros)
promete ao leitor: **"Avisamos só quando uma regra muda a sério — sem
grupo, sem responderes a nada."** A partir do 1.º seguidor essa frase é
uma obrigação editorial, não só copy — sem um critério explícito do que
justifica um post, o canal morre por omissão, o mesmo padrão de páginas
que ficaram indefinidamente "à espera de um despacho" sem ninguém a
decidir quando agir (ver "🔔 À ESPERA DE UM SINAL" no `ROADMAP.md`). Esta
secção define esse critério; o `ROADMAP.md` só aponta para aqui.

**Nenhuma automação publica no canal.** Zero integração com a API do
WhatsApp/Meta Business, zero gateway, zero token novo no repositório —
decisão e texto são sempre do Nuno, publicados manualmente. O que existe
é o gatilho que diz **quando vale a pena olhar para o canal**, mais
(desde 2026-08-31, ver "Mecanismo" abaixo) um **rascunho pronto a
copiar** — para o gatilho 1, o texto que um humano já escreveu no
momento da correcção, só formatado e entregue; para o gatilho 3, um
texto gerado de dados já verificados, sem julgamento novo nenhum. Nunca
um texto inventado pela automação, nunca publicado sozinho.

### Publica-se quando (qualquer um dos três — nunca por omissão de nenhum)

1. **Um sentinela dirigido dispara E a verificação manual confirma
   alteração real** a um apoio coberto pelo site. "Dirigido" = reconhece
   um **acto legal concreto** (Decreto-Lei ou Portaria publicados em
   dre.pt, por pesquisa de frase exacta) — nunca uma mudança de hash
   genérica. Os 5 sentinelas dirigidos hoje activos:

   | Sentinela | O que reconhece |
   |---|---|
   | `dre_psu` | Decreto-Lei sobre a PSU |
   | `dre_psu_regulamentacao` | Portaria que regulamenta o DL n.º 166/2026 (PSU) |
   | `dre_habitacao_paer` | Decreto-Lei sobre o Apoio Extraordinário à Renda |
   | `dre_habitacao_garantia` | Decreto-Lei que cita o DL n.º 44/2024 (Garantia Pública) |
   | `dre_ias` | Portaria do IAS |

   O disparo do sentinela **nunca chega sozinho** — é só o início da
   verificação humana já exigida pela Issue automática (ver "CLASSIFICADOR
   — VERIFICAÇÃO POSITIVA" e "IMPACTO DA PSU"/"CLUSTER HABITAÇÃO" para o
   detalhe de cada um). Vários destes sentinelas já produziram falsos
   positivos confirmados e fechados sem qualquer alteração ao site (Issues
   #55-#58 do MEGA, #73/#74 do PAER, #114 de `dre_habitacao_paer` — ver
   "MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS" e "CLUSTER
   HABITAÇÃO") — um disparo fechado como falso positivo nunca é publicável,
   por definição não houve mudança nenhuma.
2. **Uma página é corrigida por mudança de facto legal**, com avanço da
   data "Verificado a"/`dateModified` — nunca por reorganização,
   refactor, limpeza técnica ou melhoria de texto sem facto novo por
   trás. Cobre tanto correcções vindas de um sentinela automático (ponto
   1) como as encontradas manualmente numa sessão de fact-check
   (`WebSearch`) sem qualquer sentinela a disparar — ex.: a correcção dos
   limites de IMT Jovem nas Regiões Autónomas, o piso do subsídio de
   doença (RMMG, não IAS), ou os 13 apoios da PSU confirmados pela Lei
   n.º 36/2026 — todas já documentadas nas respectivas entradas de
   revisão em `HISTORICO.md`.
3. **Calendário de pagamentos da Segurança Social, uma vez por mês** —
   no primeiro dia útil do mês (simplificado a segunda-sexta, sem
   calendário de feriados portugueses — limitação conhecida, ver
   "Mecanismo"), com as datas confirmadas do **mês inteiro**, nunca um
   aviso por cada dia de pagamento. Categoria diferente dos pontos 1-2:
   não depende de um veredicto humano sobre "isto é uma alteração
   real?" — é a mesma informação já verificada de
   `calendario-pagamentos-seguranca-social.html`/
   `data/calendario_pagamentos.json`, que o leitor precisa todos os
   meses e não tem forma prática de saber sem visitar o site. Só
   dispara quando o mês corrente já está confirmado nos dados (nunca
   inventa um mês por publicar) e nunca duas vezes no mesmo mês.

### Não se publica

- Por **ruído já classificado como tal** — `MUDOU`/"conteúdo suspeito"
  sem alteração real, ou qualquer Issue de sentinela dirigido fechada
  como falso positivo (mesma lista do ponto 1 acima).
- Por **trabalho interno** — testes, refactor, reestruturação de
  conteúdo/navegação, infra-estrutura, acessibilidade, limpeza de CSS,
  SEO técnico (canónicas, JSON-LD, sitemap) — mesmo numa sessão grande
  e com muitos commits, nada disto é "uma regra que mudou" para quem
  segue o canal.
- Por **cadência** — nunca publicar um lembrete só porque passou tempo
  desde a última mensagem (ex.: um "ainda aqui!" mensal). O canal não
  promete cadência nenhuma; inventar uma quebraria a promessa "avisamos
  só quando", não a cumpriria. **Não confundir com o ponto 3 de "Publica-
  se quando" (calendário de pagamentos)**: a distinção é sobre o
  conteúdo, não sobre ter periodicidade — o calendário de pagamentos é
  informação nova e verificada todos os meses (datas reais, nunca um
  "continuamos aqui"), a única excepção deliberada a "sem cadência
  prometida" nesta secção.

### Quando não há nada para publicar: nada

Silêncio é o comportamento correcto sempre que nenhuma das condições
acima se verificar — é exactamente o que o convite promete ao leitor.
Nunca um lembrete periódico, nunca uma mensagem de "continuamos aqui" só
para manter presença. O mesmo princípio de honestidade já aplicado ao
resto do site (ver "FRESCURA DA HOMEPAGE" → "Regra de honestidade": nenhum
bloco mostra uma data inventada só para parecer actual) aplica-se ao
canal.

### Mecanismo — `preparar_canal.py`, Issue `canal-rascunho` (2026-08-31)

Substitui o mecanismo anterior (só texto na checklist das Issues dos
sentinelas, nunca um rascunho de facto) por uma preparação real, mas
sempre parada um passo antes de publicar. Cobre o gatilho 1 (alteração
legal — em duas variantes, 1a/1b, ver abaixo) e o gatilho 3
(calendário) da secção anterior — o gatilho de "notícia relevante"
ficou deliberadamente por construir (ver `ROADMAP.md` → "À espera de um
sinal" → "Canal de WhatsApp" para a medição real de agosto de 2026 e a
razão).

**Gatilho 1a — fila manual `data/canal_pendente.json`, `confirmado: true`**
(`{"_nota": "...", "entradas": [{titulo, resumo, paginas[]}]}`):
preenchida à MÃO por uma sessão editorial, **no mesmo commit** em que
corrige uma página por causa de uma alteração legal confirmada — nunca
por nenhuma automação. O campo `_nota` explica o mecanismo directamente
no ficheiro (mesmo padrão de `data/destaque_evento.json`; razão da
`_nota` — lição de uma sessão anterior sobre instruções invisíveis no
próprio JSON — documentada em `HISTORICO.md`, 2026-08-31).
`preparar_canal.py` preserva `_nota` em toda e qualquer escrita (só o
campo `entradas` muda) — nunca reescreve o documento a partir do zero,
o que a apagaria em silêncio; trancado por
`test_nota_explicativa_sobrevive_ao_consumo_da_fila` e por
`test_ficheiro_real_de_producao_tem_nota_explicativa` (este último corre
sobre o ficheiro real, não uma cópia). `resumo` é o texto pronto a
copiar (PT-PT simples, mesma régua de "LINGUAGEM PARA O UTILIZADOR"),
escrito no momento de maior contexto, não recriado a posteriori a
partir de um diff. `scripts/preparar_canal.py` nunca decide se algo é
"uma alteração real" — só consome a entrada mais antiga de `entradas`
e formata. Isto substitui o antigo passo "considerar publicação" nas
checklists de Issue dos sentinelas dirigidos listados em "Publica-se
quando" (`pipeline-diario.yml`, Step 8) — cada um aponta para
`data/canal_pendente.json` (**é aí que a decisão "confirmada uma
alteração real" é tomada**) em vez de só "considerar".

**Gatilho 1b — caminho automático, sem fila manual, `confirmado: false`
(2026-08-31)**: quando um dos sentinelas dirigidos listados em
"Publica-se quando" escreve a sua chave de aviso em
`data/scraped/avisos.log` no dia de hoje (mesmas chaves que já geram
Issue própria no Step 8 — `dre_psu_decreto_detectado`,
`dre_psu_regulamentacao_portaria_detectada`,
`dre_habitacao_paer_decreto_detectado`,
`dre_habitacao_garantia_decreto_detectado`, `dre_ias_portaria_detectada`),
`scripts/preparar_canal.py::obter_deteccao_sentinela()` prepara logo um
rascunho — sem esperar que uma sessão editorial preencha 1a primeiro.
Nunca confunde-se com 1a: nasce `confirmado: false`, com `sentinela`
(a chave de aviso) e um texto que é só o excerto bruto detectado em
dre.pt, nunca pronto a copiar. **O aviso "NÃO PUBLICAR AINDA" é
obrigatório e vem sempre ANTES do texto** no corpo da Issue (Step 7h do
workflow, ver abaixo): um rascunho automático nunca pode ser tratado
como pronto a publicar, mas também não faz sentido perder o sinal só
porque ninguém preencheu 1a ainda (motivo — ruído real já confirmado
nas Issues #114/#132 — documentado em `HISTORICO.md`, 2026-08-31).

Deduplicado por **ocorrência**, não por dia: `data/canal_estado.json`
guarda, em `sentinelas_rascunhadas` (`{chave_aviso: excerto}`), o
último excerto para o qual este script já produziu um rascunho por
sentinela — só volta a disparar quando o excerto detectado hoje for
diferente do último rascunhado (um acto genuinamente novo, não o mesmo
decreto-lei/portaria a persistir na pesquisa dia após dia — caso real
documentado em `HISTORICO.md`, Issue #132). A chave só é registada
quando um rascunho é de facto
produzido — se o sinal aparecer num dia em que 1a já ocupou o único
slot diário, fica por rascunhar e continua elegível no dia seguinte
(nunca perdido em silêncio).

**Gatilho 3 — `data/calendario_pagamentos.json`, `confirmado: true`**:
sem fila manual, gerado directamente (já é fonte verificada).
`calendario_devido()` só dispara quando (a) o mês corrente já está no
JSON, (b) hoje é dia útil (seg-sex — sem calendário de feriados,
limitação conhecida, nunca escondida) e (c) o mês ainda não foi
entregue este mês (`data/canal_estado.json["ultimo_calendario_publicado"]`).

**Prioridade e volume**: `scripts/preparar_canal.py::main()` tenta
sempre 1a primeiro; só se a fila estiver vazia tenta 1b (sentinela);
só se nenhum sentinela tiver sinal novo tenta 3 (calendário). Nunca
mais de 1 rascunho/dia, qualquer que seja a origem. Numa colisão
(mais do que uma origem pendente no mesmo dia), a(s) de prioridade mais
baixa não são descartadas — `calendario_devido()` continua a devolver o
mês enquanto não for marcado como entregue, e um sentinela por
confirmar continua a re-detectar o mesmo excerto todos os dias até ser
rascunhado — por isso a corrida seguinte sem nada de prioridade mais
alta entrega-as (só adiadas, nunca perdidas).

**Passo em `pipeline-diario.yml`** (entre "Actualizar CLAUDE.md" e o
guardrail de ficheiros protegidos, antes do push diário, portanto
depois do scrape — `data/scraped/avisos.log` já tem os avisos de hoje
quando este step corre): corre `scripts/preparar_canal.py`, que escreve
`/tmp/canal_rascunho_hoje.json` (efémero, fora do repositório, nunca
commitado) quando há algo a publicar, e actualiza
`data/canal_pendente.json`/`data/canal_estado.json` (commitados como
qualquer outro ficheiro em `data/`). Um step mais abaixo ("Criar Issue
do rascunho do canal") lê esse ficheiro e, se existir, cria uma Issue
com o texto num bloco de código, label `canal-rascunho`, e a nota
explícita "o texto final e a decisão de publicar são sempre tuas".
Título e corpo variam com `rascunho.confirmado`: `true` → `📱 Canal —
<título> (<data>)`, corpo directo ao texto; `false` → `⚠️ Canal (por
confirmar) — <título> (<data>)`, label extra `verificar`, e o bloco de
aviso "NÃO PUBLICAR AINDA" logo a seguir ao título da Issue, antes de
qualquer outra coisa (nunca depois do texto nem só como nota de
rodapé) — a checklist final também ganha um item extra ("Confirmado na
fonte oficial") antes dos passos de publicação/decisão. **Sem nada a
publicar, nenhuma Issue é criada** — silêncio é o comportamento
correcto, mesma regra do resto desta secção. Fecho é sempre manual (o
Nuno fecha depois de publicar, de decidir não publicar, ou de confirmar
que um rascunho "por confirmar" não correspondia a nada real).

**Risco residual aceite, documentado no próprio script**: se a criação
da Issue falhar por um motivo transitório depois de a fila já ter sido
consumida/o mês marcado como entregue/o excerto do sentinela já
registado, essa mensagem específica fica sem retry automático (o estado
já foi commitado). Considerado aceitável para uma ferramenta de
sugestão, não um sistema crítico — nunca escondido.

`scripts/preparar_canal.py` testado em `tests/test_preparar_canal.py`
(os três gatilhos isoladamente, prioridade/colisão entre os três,
limite de 1/mês do calendário, deduplicação por ocorrência do gatilho
1b — mesmo excerto em dias seguidos nunca gera dois rascunhos, um
excerto novo gera um rascunho novo —, entradas malformadas na fila
nunca bloqueiam as seguintes, silêncio quando não há nada). Nenhuma
chamada de rede — os testes correm inteiramente em `tmp_path`, `main()`
aceita `raiz`/`hoje`/`saida` explícitos (mesmo padrão de
`gerir_estado_fontes.main()`), sem monkeypatch de constantes de módulo.

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

Implementa a melhoria já registada numa sessão anterior (achado por
varrimento real das 27 páginas de conteúdo, ver `HISTORICO.md`, entrada
de 2026-07-03 "fecho da sessão E-E-A-T"): as 27 páginas de conteúdo (as
que têm `FAQPage`) só tinham
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

Três camadas, cada uma útil por si só: historial auditável em
`dados/observacoes/`, parâmetros legais versionados em YAML, e publicação
consolidada (JSON + SQLite). Nenhum valor legal fica hardcoded fora da
fonte canónica destas camadas; nenhum estado de erro pode parecer sucesso
(ver "INVARIANTE"); `escrever_ficheiro_seguro()`/allow-lists próprias
continuam a ser a única via de escrita automática.

### Fase 1 — Git scraping: historial auditável (`dados/observacoes/`)

O pipeline diário commita os dados extraídos das fontes oficiais, criando
um historial público (`git log -- dados/observacoes/<slug>.json`) de
quando cada valor mudou — um ficheiro por fonte monitorizada
(`SLUGS_MONITORIZADOS`, a mesma lista de `gerir_estado_fontes.py`),
sobrescrito no lugar; **o historial vive no `git log`, nunca num array a
crescer dentro do próprio JSON**.

- `scripts/registar_observacao.py` — lê `data/scraped/<slug>_latest.json`
  e grava/actualiza `dados/observacoes/<slug>.json` só quando
  `sha256_conteudo` mudar face ao já registado. `hash_conteudo` é
  calculado por `scraper_playwright.py` só sobre `conteudo_extraido`
  (título/parágrafos/itens já limpos de tags/scripts), nunca sobre
  `data_acesso`/URL/outros campos dinâmicos — sem normalização própria
  neste script. **Um bloqueio nunca aparece como sucesso**:
  `data/scraped/<slug>_latest.json` só é escrito pelo scraper para
  OK/OK_VIA_ARQUIVO (nunca BLOQUEADO — ver
  `scraper_playwright._guardar_resultado`/`_tratar_nao_ok`);
  `registar_observacao.py` confirma isso de novo a partir do campo
  `status`, nunca assume `OK` por omissão — um estado inesperado fica
  `DESCONHECIDO`, com `valores_extraidos: null` + `motivo`.
- `dados/observacoes/schema.json` — JSON Schema (Draft 7) de cada
  observação; validado por `tests/test_observacoes_schema.py`
  (`jsonschema`) — JSON malformado ou fora do schema é um teste
  vermelho, coberto pela suite normal do job "Suite de Testes (pytest)"
  em `integridade.yml`.
- `pipeline-diario.yml`, Step 1c ("Git scraping — registar observações
  auditáveis"), logo a seguir ao scrape: corre o script e, para cada
  ficheiro de `dados/observacoes/` que mudou, faz **um commit por
  fonte** (`dados: atualização <slug> <data>`, autor
  `github-actions[bot]`) — nunca um commit a misturar várias fontes, é
  essa granularidade que torna o `git log` de cada ficheiro legível como
  historial real. `scripts/verificar_injecao.py` (guardrail de prompt
  injection) cobre `dados/` na mesma categoria de conteúdo externo de
  `data/scraped/`.

### Fase 2 — Padrão OpenFisca: parâmetros legais em YAML versionado

Convenção OpenFisca (parâmetros com vigência, separados da lógica de
cálculo) — sem instalar a biblioteca OpenFisca, só o padrão.
`dados/parametros/<prestacao>.yaml`, um ficheiro por prestação; cada
parâmetro tem uma lista `valores` com `vigencia_inicio`/`valor`/
`referencia_legal`/`fonte_url`/`verificado_em` por entrada — permite
série temporal completa (valores de anos anteriores nunca são
apagados, só deixam de ser o "vigente").

- **PASSO 0, guarda dura**: `scripts/gerar_parametros_json.py` **falha**
  (`exit 1`, nunca escreve) se qualquer entrada cuja vigência já tenha
  começado (`vigencia_inicio <= hoje`) não tiver `verificado_em`,
  `referencia_legal` ou `fonte_url` preenchidos — nunca publica um
  placeholder como se fosse dado real.
- **Nada derivável de outro parâmetro é guardado como parâmetro**: um
  valor calculável a partir de um parâmetro já existente (ex.: um tecto
  que é sempre `multiplicador × IAS`) nunca ganha entrada própria em
  `dados/parametros/*.yaml` — a relação fica trancada por um teste
  (`tests/test_valores_ancora.py`, que recalcula e compara), nunca por
  um segundo valor a manter sincronizado à mão. Só o `multiplicador`
  (ou a constante fixa na lei) é parâmetro; o resultado é sempre
  derivado em runtime ou no teste, nunca duplicado no YAML.
- **Um parâmetro só existe se houver código que o consuma**: uma
  entrada em `dados/parametros/*.yaml` exige um consumidor real — um
  simulador/página via `dados/parametros.json`, um teste-âncora, ou, no
  mínimo, os exportadores de Dados Abertos (`gerar_parametros_json.py`/
  `gerar_base_dados.py`, que publicam qualquer YAML por desenho, mesmo
  antes de um simulador o usar — caso de `imt_geral_hpp_ra_*` em
  `habitacao.yaml`). Nunca um valor especulativo sem nenhum consumidor,
  real ou de exportação (mesmo problema documentado para
  `source_adapter.py`, secção "IDEIAS RECUPERADAS — cascata de
  fontes").
- `scripts/gerar_parametros_json.py` consolida `dados/parametros/*.yaml`
  num único `dados/parametros.json` (um valor **vigente** por
  parâmetro — a entrada com `vigencia_inicio` mais recente já iniciada);
  `--check` valida sem escrever (usado como rede de segurança em
  `tests/test_valores_ancora.py::test_dados_parametros_json_sincronizado_com_os_yaml`
  — esquecer de regenerar depois de editar um YAML fica vermelho).
- **Simuladores migrados para `fetch('/dados/parametros.json')`**
  (padrão comum aos três: `let PARAMETROS_X = null`, populado em
  `DOMContentLoaded`; o botão de cálculo nasce `disabled`, só activado
  depois do fetch ter sucesso; se falhar, um aviso próprio fica visível
  e o botão mantém-se desactivado; a função pura de cálculo nunca é
  tocada — continua testável sem rede): `simulador-csi.html`,
  `simulador-abono.html`, `simulador-subsidio-doenca.html`. Só
  `simulador-ase.html` continua com valores inline (`CONFIG`, nunca
  `PARAMETROS_*`) — ver `ROADMAP.md` para o estado da migração.
- Golden tests de cada simulador migrado constroem `params` directamente
  de `dados/parametros.json` (nunca de um objecto global da página),
  mais 2 testes de runtime real por simulador (`http.server`, mesmo
  padrão de `test_acessibilidade.py`, nunca `file://`): sucesso do
  fetch activa o botão e calcula correctamente; falha do fetch
  (`page.route(...).abort()`) mantém o botão bloqueado e o formulário
  nunca produz resultado, mesmo tentando contornar o `disabled` via JS.
- `tests/test_valores_ancora.py` cobre a mesma fonte: os valores de
  cada prestação em `dados/parametros.json` continuam a bater com a
  respectiva página publicada; `dados/parametros.json` está
  sincronizado com os YAML (`--check`); nenhum parâmetro vigente fica
  sem `verificado_em` (réplica visível da guarda dura do PASSO 0).

### Fase 3 — Publicação: `dados.html` + SQLite + Datasette Lite

`scripts/gerar_base_dados.py` consolida `dados/parametros/*.yaml` (TODAS
as vigências, não só a vigente — série temporal completa, diferente de
`dados/parametros.json`) e o historial de `dados/observacoes/` numa base
SQLite única, sem servidor (ficheiro binário estático, servido tal e
qual pelo GitHub Pages):

- Tabela `parametros` (prestacao/parametro/descricao/unidade/valor/
  vigencia_inicio/referencia_legal/fonte_url/verificado_em) — uma linha
  por (prestação, parâmetro, vigência).
- Tabela `historial` (fonte/commit_sha/data_commit/mensagem) — derivada
  de `git log --format=... --name-only -- dados/observacoes/`, parseada
  com um separador de campos `\x1e`/`\x1f` (nunca `\x00` —
  `subprocess`/argv não aceita NUL embutido).
- **Determinismo deliberado**: nenhuma tabela guarda um campo tipo
  `gerado_em`/timestamp de geração — por isso duas corridas sobre o
  mesmo estado do repositório produzem `dados/tensdireito.db`
  **byte-idêntico** (`tests/test_gerar_base_dados.py::test_gerar_e_deterministico`),
  a mesma condição que já vale para `registar_observacao.py`: o
  pipeline só precisa de commitar quando o conteúdo mudar de facto,
  nunca ruído diário.
- `pipeline-diario.yml`, Step 1d ("Publicar base de dados aberta"),
  logo a seguir ao Step 1c: corre `gerar_parametros_json.py` +
  `gerar_base_dados.py` e commita `dados/parametros.json`/
  `dados/tensdireito.db` só se algo mudou — corre depois do Step 1c de
  propósito, para a tabela `historial` do SQLite já reflectir o commit
  de observações do próprio dia.
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
  Abertos", junto de "Fontes"/"Privacidade") — sem isso ficaria órfã,
  apanhado por `tests/test_higiene_indexacao.py`.
- `scripts/smoke_producao.sh`: `/dados.html`, `/dados/parametros.json`
  e `/dados/tensdireito.db` em `scripts/urls_criticas.txt`;
  `parametros.json` tem uma verificação extra — o corpo tem de parsear
  como JSON válido, não só devolver 200 (apanha um 200 com corpo
  truncado/corrompido, ex.: cache de CDN a meio de um deploy);
  `tensdireito.db` tem uma verificação de `Access-Control-Allow-Origin`
  — nunca falha o smoke test por isto (só `::warning::`), porque
  confirma comportamento da plataforma (GitHub Pages), não do nosso
  código.

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

Testes: `tests/test_scraper_fallback.py` (mocks — sem rede real; contagem
real é sempre a do próprio ficheiro, nunca fixada aqui), cobre snapshot
recente/antigo/inexistente, falha de rede na consulta Wayback, e a
garantia de que a decisão nunca devolve `"estado": "OK"` directamente
(só `OK_VIA_ARQUIVO` ou `BLOQUEADO`).

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

*O histórico cronológico de sessões de trabalho ("Última revisão:
AAAA-MM-DD — ...") vive em `HISTORICO.md`, não neste ficheiro — nunca
acrescentar uma entrada nova aqui; acrescentar sempre ao fim de
`HISTORICO.md`.*
