# Histórico de Sessões — Tens Direito

Registo cronológico de sessões de trabalho anteriores, movido para aqui
do `CLAUDE.md` (Fase 1 da separação histórico/referência). `CLAUDE.md`
continua a ser a documentação de referência do estado actual do
projecto; este ficheiro é só o diário de sessões — nunca reescrever uma
entrada antiga: cada uma descreve o estado e as decisões da altura em
que foi escrita, não necessariamente o estado actual do repositório
(esse está sempre em `CLAUDE.md`).

Nunca servido, nunca linkado, fora do sitemap/pesquisa.js — mesma
categoria de `ROADMAP.md`.

Uma sessão nova acrescenta sempre uma entrada nova `*Última revisão:
AAAA-MM-DD — ...*` ao **fim** deste ficheiro, nunca ao `CLAUDE.md`.

---

*Última revisão: 2026-06-28 — CSI e PSU publicadas; fact-checking completo; GSTACK adicionado; PSU destaque; datas sazonais; simulador abono (fix múltiplas crianças); simulador ASE completo; plano impacto PSU documentado*

---

*Última revisão: 2026-07-01 — corrigido bug de dedup em `pipeline-diario.yml` que gerava Issues duplicadas (data-expirada, fonte-bloqueada, fonte-alterada, divergências de valores); 8 Issues duplicadas fechadas*

---

*Última revisão: 2026-07-02 — investigado um `<system-reminder>` suspeito recebido numa sessão anterior; busca exaustiva ao repositório (186 ficheiros trackeados, `data/scraped/`, `shadow_history/`, log do scraper) não encontrou nenhum vestígio de prompt injection — conclusão: artefacto do harness, não conteúdo importado; adicionado guardrail permanente `scripts/verificar_injecao.py` (procura padrões de injection em `data/` e `shadow_history/`, só leitura, nunca executa o que encontra) + novo job em `integridade.yml`; nova secção "SEGURANÇA — PROMPT INJECTION EM DADOS IMPORTADOS"; 9 testes novos em `tests/test_verificar_injecao.py`, 409 testes a passar*

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
completo. As 8 fontes monitorizadas já tinham `_latest.json` reais em
produção, por isso `dados/observacoes/*.json` nasceu com conteúdo real
(nunca vazio) — confirmada a idempotência (2.ª corrida sem alterações),
que um SHA forçado a divergir produz observação nova, e que o guard "sem
`_latest.json` ainda" nunca lança excepção para uma fonte nova. Efeito
lateral encontrado e corrigido no mesmo commit, sem relação com dados
abertos: o bloco `ATUALIZACOES:HOME` de `index.html` estava
desactualizado de uma sessão anterior (2 cartões a apontar para páginas
já fora das 4 mais recentemente verificadas) — corrigido pela própria
`sincronizar_clusters.py`. Suite local completa: **2702 passed, 4 skipped, 0 failed**
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

---

*Última revisão: 2026-08-31 — preparação automática de rascunhos para o
canal de WhatsApp. Passo 0 (obrigatório antes de construir): medidos os
três gatilhos propostos contra dados reais de agosto de 2026 — o
gatilho de "notícia relevante" (critério já usado por
`gerar_noticias.py`) teria dado ~20 dias/31 com pelo menos uma
vencedora, muito acima do limite de 10/mês; um filtro mais apertado
(sinal legal directo no título) reduzia para 2 dias, mas ambos já
coincidiam com o gatilho de alteração legal — decisão do Nuno de não
construir este gatilho agora (ver ROADMAP.md → "À espera de um sinal"
→ "Canal de WhatsApp" para os números completos e a razão).

Construídos só os gatilhos 1 (alteração legal confirmada) e 3
(calendário mensal de pagamentos) — nova secção "Mecanismo" dentro de
"CANAL DE WHATSAPP — GATILHO EDITORIAL DE PUBLICAÇÃO" com o detalhe
completo. Novo `scripts/preparar_canal.py`: gatilho 1 lê e consome
`data/canal_pendente.json` (fila preenchida à mão por sessões
editoriais, nunca pela automação — o script só formata o texto que um
humano já escreveu); gatilho 3 gera o rascunho automaticamente a partir
de `data/calendario_pagamentos.json` (fonte já verificada, sem
julgamento humano necessário), uma vez por mês, no primeiro dia útil
(seg-sex, sem calendário de feriados — limitação conhecida,
documentada). Prioridade 1 > 3 em caso de colisão no mesmo dia; o
calendário nunca é perdido, só adiado para o próximo dia sem alteração
legal pendente. Máximo 1 rascunho/dia.

Novo passo em `pipeline-diario.yml` (antes do push diário) corre o
script e escreve `/tmp/canal_rascunho_hoje.json` (efémero, nunca
commitado); um step novo mais abaixo cria uma Issue `📱 Canal — <título>
(<data>)` com o texto pronto a copiar num bloco de código, label
`canal-rascunho` nova, e a nota explícita de que a decisão de publicar
é sempre manual — sem nada a publicar, nenhuma Issue é criada. Os 5
blocos de Issue dos sentinelas dirigidos (Step 8) tiveram o antigo
passo "considerar publicação" substituído por uma instrução accionável:
acrescentar uma entrada a `data/canal_pendente.json` no mesmo commit da
correcção.

21 testes novos em `tests/test_preparar_canal.py` (os dois gatilhos
isolados, prioridade/colisão, limite de 1/mês, entradas malformadas na
fila nunca bloqueiam as seguintes, silêncio quando não há nada, `_nota`
explicativa sobrevive ao consumo da fila — testado também sobre o
ficheiro real do repositório, não só sobre cópias em `tmp_path`) —
`main()` aceita `raiz`/`hoje`/`saida` explícitos, mesmo padrão de
`gerir_estado_fontes.main()`, sem monkeypatch de constantes de módulo.

**`data/canal_pendente.json` ganhou `_nota` explicativa no próprio
ficheiro** (revisão pedida pelo Nuno, antes do push): mesmo padrão já
usado em `data/destaque_evento.json` — decisão tomada depois de uma
lição real, documentada nesse ficheiro, de instruções que passaram 12
dias sem ninguém as ler por não estarem visíveis no próprio JSON.
Schema passou de array solto para `{"_nota": "...", "entradas": [...]}`;
`preparar_canal.py` preserva `_nota` em toda e qualquer escrita (só
`entradas` muda), nunca reescreve o documento a partir do zero. As 5
checklists de Issue dos sentinelas dirigidos já apontavam para
`data/canal_pendente.json` como o passo onde a decisão "confirmada uma
alteração real" é tomada — confirmado, não precisou de correcção.

Suite completa reconfirmada sem regressões: **3634 passed, 4 skipped**
(mesma allow-list de sempre, confirmada elemento a elemento por
`scripts/verificar_skips_permitidos.py`); `ruff check scripts/ tests/
--select E,F,W --ignore E501 .` limpo; `data/canal_pendente.json`/
`data/canal_estado.json` confirmados sem prompt injection
(`scripts/verificar_injecao.py`); YAML do workflow validado. Dry-runs
manuais contra dados reais (calendário de setembro de 2026, um caso de
alteração legal fictício, e o schema real com `_nota`), sempre isolados
em `tmp_path`/`/tmp` — nunca contra o checkout real, depois de uma 1.ª
tentativa ter mutado por engano `data/canal_estado.json` local
(revertido de imediato, sem consequência).

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/canal-rascunhos-automaticos-23gm2t` (designada pelo ambiente
remoto desta sessão), 1 commit — **PR aberto contra `main`, NÃO
integrado** (instrução explícita: sem merge; ver o PR para o número
exacto).*

---

*Última revisão: 2026-08-31 (sessão seguinte) — caminho automático para
o gatilho 1 do canal de WhatsApp, sem passo manual. Até agora o gatilho
1 (alteração legal) só produzia rascunho depois de uma sessão editorial
preencher `data/canal_pendente.json` à mão — o disparo de um dos 5
sentinelas dirigidos (`dre_psu`, `dre_psu_regulamentacao`,
`dre_habitacao_paer`, `dre_habitacao_garantia`, `dre_ias`) ficava só
registado na sua própria Issue `verificar`, sem nunca chegar ao canal
enquanto ninguém confirmasse manualmente. Nova secção "Gatilho 1b" em
"Mecanismo" (`CLAUDE.md`) com o detalhe completo — resumo: quando
qualquer um dos 5 escreve a sua chave de aviso em
`data/scraped/avisos.log` no dia de hoje,
`scripts/preparar_canal.py::obter_deteccao_sentinela()` prepara logo um
rascunho `confirmado: false`, sem esperar pela fila manual.

**O aviso é obrigatório e vem sempre antes do texto** — exigência
central desta sessão, motivada por os sentinelas já terem produzido
ruído confirmado (Regulamento da Série II na Issue #114, o próprio
DL 166/2026 já conhecido a reaparecer na Issue #132): um rascunho
`confirmado: false` nunca pode parecer pronto a publicar. Implementado
em dois sítios que têm de concordar — o texto do próprio rascunho
(`formatar_rascunho_sentinela()`, sempre `[POR CONFIRMAR — ...]`) e,
mais importante, o corpo da Issue criada pelo Step 7h de
`pipeline-diario.yml`: o bloco `> ⚠️ NÃO PUBLICAR AINDA...` é inserido
logo a seguir ao título `## Rascunho para o canal de WhatsApp`, antes
de "Gatilho"/"Data" e muito antes do bloco de código com o texto —
nunca como nota de rodapé. Título da Issue com prefixo distinto
(`⚠️ Canal (por confirmar)` em vez de `📱 Canal`) e label extra
`verificar`, para nunca se confundir na lista de Issues com um
rascunho já confirmado.

**Deduplicação por ocorrência, não por dia** — o requisito mais
delicado desta sessão, porque já aconteceu na prática: antes do corte
de recência da Issue #132 ser corrigido, `dre_psu` re-detectou o mesmo
DL 166/2026 vários dias seguidos, escrevendo uma linha nova em
`avisos.log` a cada corrida. Um mecanismo que disparasse "um rascunho
por dia em que o sentinela dispara" teria criado uma Issue nova todos
os dias para a mesma causa. Corrigido guardando, em
`data/canal_estado.json["sentinelas_rascunhadas"]`
(`{chave_aviso: excerto}`), o último excerto para o qual **já foi
produzido** um rascunho por sentinela — só volta a disparar quando o
excerto detectado hoje for genuinamente diferente do último rascunhado
(nunca "já visto"; a chave só é gravada quando um rascunho é de facto
entregue, para um sinal que perdeu o slot diário para a fila manual
nunca ficar perdido, só adiado).

Duas origens, dois estados, nunca misturados: `confirmado: true`
(fila manual 1a, ou calendário 3 — já verificado, sem julgamento por
fazer) vs. `confirmado: false` (sentinela 1b, sempre por confirmar).
Prioridade fixa 1a > 1b > 3, no máximo 1 rascunho/dia como sempre — uma
origem de prioridade mais baixa nunca é descartada por uma colisão, só
adiada para a corrida seguinte.

**O que não mudou, conforme pedido**: máximo continua 1 mensagem/dia; a
publicação continua inteiramente manual (o rascunho automático é ainda
mais explicitamente "não publiques isto" do que o confirmado); o
gatilho de "notícia relevante" continua por construir. As checklists
das Issues dos 5 sentinelas dirigidos (Step 8) não foram tocadas — 1a
continua a ser o caminho preferido para um rascunho já confirmado e
pronto a copiar; 1b é só a rede de segurança para quando ninguém a
preencheu ainda.

`tests/test_preparar_canal.py` ganhou 15 testes novos (36 no total):
unitários para `avisos_de_hoje()`/`obter_deteccao_sentinela()`/
`formatar_rascunho_sentinela()` (extracção do excerto, reconhecimento
das 5 chaves exactas, ocorrência já rascunhada nunca repete, excerto
diferente conta como ocorrência nova) e de integração via `main()`
(rascunho por confirmar produzido e persistido correctamente; sem
sinal de hoje nunca produz nada; fila manual ganha ao sentinela no
mesmo dia sem gastar o sinal; sentinela ganha ao calendário no mesmo
dia; a mesma ocorrência ao longo de 3 dias consecutivos — cenário real
da Issue #132, reproduzido com fixtures — nunca gera mais do que 1
rascunho; um excerto novo volta a gerar rascunho; os dois gatilhos
pré-existentes continuam sempre `confirmado: true`). Sintaxe do
JavaScript novo do Step 7h validada com `node --check` e exercitada com
stubs da API do GitHub (`github.rest.issues.create`) nos dois caminhos
(confirmado/por confirmar) antes do commit — confirmado que o aviso
aparece mesmo antes do bloco de código e que o título/labels variam
como esperado.

Suite completa (`pytest tests/ -q`, ambiente local com
`playwright`/`feedparser`/`beautifulsoup4`/`lxml`/`jsonschema`
instalados manualmente — mesmo workaround do `sgmllib3k` já documentado
em sessões anteriores para o `feedparser`, e o mesmo Chromium
pré-instalado em `/opt/pw-browsers`): **3649 passed, 4 skipped, 1
warning em 632s** — os 4 skips continuam exactamente os mesmos 4 da
allow-list (`tests/skips_permitidos.json`), nenhum skip novo. `ruff
check scripts/ tests/ --select E,F,W --ignore E501 .` limpo. YAML de
`pipeline-diario.yml` validado com `yaml.safe_load`.
`scripts/verificar_injecao.py` reconfirmado limpo (não tocado por esta
sessão, corrido só como verificação). `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` — sessão sem
scraper. Trabalho feito na branch `claude/automatic-legal-trigger-path-tqweh9`
(designada pelo ambiente remoto desta sessão) — commit local, **sem
push** (instrução explícita desta sessão).*

---

*Última revisão: 2026-09-01 — corrigidos os termos de pesquisa de
`dre_psu_regulamentacao` (Issue #148) e `dre_habitacao_garantia` (Issue
#147), os dois sentinelas DRE que nunca devolveram um único resultado
desde a criação (16 e 44 dias consecutivos, respectivamente —
confirmado por `data/scraped/*_2026-*.json` reais, sessão de
diagnóstico anterior no mesmo dia). Causa: ambos pesquisavam a
**citação** de um diploma por número (`"Decreto-Lei n.º 166/2026"`/
`"Decreto-Lei n.º 44/2024"`) — os 4 sentinelas DRE que sempre
funcionaram (`dre_psu`, `dre_habitacao_paer`, `dre_ias`, e agora este)
pesquisam sempre uma frase temática. Prova directa, não inferida:
`dre_psu` (pesquisa `"prestação social única"`) já tinha, no
`itens_lista` real de 2026-09-01, exactamente o caso de teste concreto
pedido — "Portaria n.º 394/2026/1", que `dre_psu_regulamentacao` nunca
encontrara em 16 dias com a citação por número.

`dre_psu_regulamentacao` corrigido para o MESMO termo de `dre_psu`
(`"prestação social única"`) — deliberado, nunca redundância: os
filtros são opostos (`detectar_decreto_lei_psu` só conta Decreto-Lei;
`detectar_portaria` só conta Portaria), documentado em comentário
cruzado nos dois sítios em `scripts/scraper_playwright.py` e em
CLAUDE.md "IMPACTO DA PSU". Corte de recência (`desde`) subido de
"2026-08-16" para **"2026-08-28"** — achado ao validar contra o dado
real: sem isto, a própria Portaria n.º 394/2026/1 (já tratada no commit
`d0f082a`) seria sinalizada como "nova" todos os dias, para sempre
(mesmo padrão do `numero_conhecido` do `dre_psu`, Issue #132, aqui
resolvido só com a data porque `_detectar_portaria_generico` não aceita
`numero_conhecido`). `dre_habitacao_garantia` corrigido para
`"Garantia Pública no crédito habitação"` — a designação temática do
apoio já usada como rótulo humano em `scripts/preparar_canal.py`;
**ainda por confirmar contra um scrape real** (rede bloqueada para
diariodarepublica.pt nesta sessão, mesma limitação de sempre — sem dado
real equivalente ao de `dre_psu` disponível para este caso), com o
mesmo aviso deixado em comentário para a 1.ª corrida real do pipeline
confirmar (e, se necessário, subir o `desde` de `detectar_decreto_lei`
da mesma forma).

Novo guardrail permanente, `tests/test_dre_termos_pesquisa.py`: falha
se qualquer fonte DRE (actual ou futura) com `pesquisa_interactiva`
tiver um termo — ou uma `ancora_conteudo` — com forma de citação de
diploma ("n.º" + barra + ano), confirmado a reconhecer os dois casos
reais que falharam e a nunca disparar por engano com as 4 frases
temáticas já comprovadas. `tests/test_dre_psu_regulamentacao.py`
ganhou uma secção de validação contra o `itens_lista` REAL de
`data/scraped/dre_psu_2026-09-01.json` (nunca reescrito à mão): confirma
que a Portaria n.º 394/2026/1 é isolada correctamente dos outros 8 itens
reais (Lei, Decreto-Lei, Despachos), que o corte de recência novo a
suprime, e que uma Portaria futura hipotética, misturada com os mesmos
dados reais, ainda dispara. Achado e corrigido antes do commit: uma 1.ª
versão desse teste não isolava `_registar_aviso` via `monkeypatch` e
escrevia mesmo em `data/scraped/avisos.log` real ao correr — revertido
o ficheiro de dados e corrigido o teste antes de qualquer commit.

Fechadas as Issues #147 e #148 com o diagnóstico: verdadeiro positivo
quanto ao sintoma quotidiano (o scraper estava mesmo cego, todos os
dias), mas a causa nunca foi um bloqueio do DRE — era a expressão de
pesquisa, errada desde a criação de cada sentinela, nunca calibrada
contra o motor real antes de hoje.

Suite completa: **3660 passed, 4 skipped** (allow-list de skips
confirmada elemento a elemento, sem alteração); `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper novo, só correcção de termos de pesquisa já
existentes). Trabalho feito na branch `claude/corrigir-termos-sentinelas`
(criada nesta sessão a partir de `main`) — commit local, **sem push**
(instrução explícita desta sessão).*

---

*Última revisão: 2026-09-02 — sessão de triagem de duas Issues (#150,
#151) sobre os sentinelas DRE do cluster PSU/Habitação, com o termo de
`dre_habitacao_garantia` finalmente calibrado contra o motor real.

**Issue #150 (`dre_psu_regulamentacao`, 1.ª mudança detectada desde a
correcção de termo da sessão anterior, commit `e3b67d7`)**: confirmado
que é o mecanismo genérico de "mudança de conteúdo" (`data/mudancas.json`,
0→9 itens face a 2026-09-01, que ainda devolvia a página canónica de
"zero resultados") — nunca a Issue específica de "Portaria de
regulamentação detectada" (`dre_psu_regulamentacao_portaria_detectada`).
Confirmado ao correr `_detectar_portaria_generico()` directamente contra
o `itens_lista` real de hoje (`data/scraped/dre_psu_regulamentacao_2026-09-02.json`):
dos 9 itens, só um é Portaria (n.º 394/2026/1, já conhecida e tratada —
data completa 2026-08-27, anterior ao corte de recência de
"2026-08-28") — correctamente suprimida; nenhuma outra Portaria na
lista. **Resposta directa à pergunta do Nuno: não há nenhuma Portaria
nova a regulamentar a PSU além da 394/2026/1.** (Achado incidental
corrigido no mesmo teste manual: uma chamada de verificação sem
`data_minima` escreveu, sem querer, uma linha real em
`data/scraped/avisos.log` — revertida com `git checkout` antes de
continuar, nunca chegou a ficheiro nenhum commitado.)

**Issue #151 (`dre_habitacao_garantia`, 4.º dia consecutivo cego, mesmo
depois da correcção de termo da sessão anterior)**: calibrado contra o
motor real pela primeira vez, via 4 corridas sucessivas de um workflow
de diagnóstico temporário (`.github/workflows/diagnostico-garantia-
termo-temp.yml` + `scripts/_diag_garantia_termo.py`, numa branch
própria `claude/diag-garantia-termo-temp` — nunca em `main`, apagados
os dois no fim, mesmo padrão já documentado nesta secção para
diagnósticos anteriores).

Achado metodológico incidental, mas real e relevante para qualquer
diagnóstico DRE futuro: a 1.ª corrida (mesma `page`/`context`
reutilizada entre termos, sem pausa) mostrou `"apoio extraordinário à
renda"` — termo que já se sabe fiável, 19 itens/dia em produção — a
devolver **0 itens**. Investigado antes de confiar no resultado:
`dre_psu`, `dre_habitacao_paer`, `dre_habitacao_garantia`, `dre_ias` e
`dre_psu_regulamentacao` partilham TODOS o mesmo `PerfilBrowser`
(`stealth=False, headers_custom=False`) em `_PERFIL_POR_SLUG` — como
`PerfilBrowser` é um `dataclass(frozen=True)`, instâncias com os mesmos
valores são iguais e colidem na mesma chave de `grupos` em `main()`,
logo as 5 fontes partilham o mesmo `context`/`page` em produção,
processadas sequencialmente. Uma 2.ª pesquisa na mesma página, sem
pausa, cai na página canónica de "zero resultados" do DRE mesmo com um
termo correcto — mas a produção sobrevive a isto porque
`scrape_playwright()` tenta até 3 vezes com 30-120s de espera entre
tentativas quando a classificação falha (`TENTATIVAS_BLOQUEIO`), o que
o diagnóstico inicial não replicava. Corrigido nas corridas seguintes
abrindo um `context` novo (cookies limpos) por termo testado, com até 2
tentativas e uma pausa curta — isolamento que devolveu resultados
limpos e reprodutíveis.

Com isolamento correcto: `"Garantia Pública no crédito habitação"`
(termo actual) confirmado a devolver 0 resultados, 2 tentativas,
contexto limpo — genuinamente morto, não um artefacto de sessão.
`"garantia pública"` sozinho devolve 29 resultados, mas nenhum
relacionado com o DL 44/2024 (são Resoluções da AR/CM sobre linhas de
garantia pública completamente distintas — crédito a empresas, fundos
europeus) — termo genérico demais, teria sido um novo falso-positivo à
espera de acontecer. `"garantia do Estado"`, `"crédito à habitação de
jovens"` e a citação do H1 da página de detalhe (`"Decreto-Lei n.º
44/2024, de 10 de julho"`) devolvem todos 0.

Em vez de continuar a adivinhar candidatos, extraído o texto completo
da própria página de detalhe do DL 44/2024 em dre.pt (URL já conhecida
de `dados/parametros/habitacao.yaml`) — a ementa e o corpo do diploma
usam, repetidamente, a expressão legal exacta **"garantia pessoal do
Estado"** (nunca "garantia pública"): *"Estabelece as condições em que
o Estado pode prestar garantia pessoal a instituições de crédito..."*,
*"A garantia pessoal do Estado, referida no artigo anterior, pode ser
concedida..."*, *"A garantia pessoal do Estado não ultrapasse 15% do
valor da transação..."*. Testado contra o motor real:
`'"garantia pessoal do Estado"'` devolve **24 resultados à 1.ª
tentativa**, incluindo a **Portaria n.º 236-A/2024/1** — a que
regulamenta exactamente este DL 44/2024 (confirmada em
`dados/parametros/habitacao.yaml`) — prova directa e não-inferida de
que a frase está correcta. O próprio DL 44/2024 não aparece nos 24
itens (é de 2024, tal como a Portaria 236-A/2024/1 seria também
suprimida pelo corte de recência `desde: "2026-07-20"` já existente —
o sentinela existe para apanhar uma ALTERAÇÃO futura, nunca para
redescobrir o diploma já conhecido).

Corrigido `dre_habitacao_garantia` em `scripts/scraper_playwright.py`
(`_FONTE_CONFIGS` e `FONTES_PLAYWRIGHT`, `termo`/`ancora_conteudo` de
`'"Garantia Pública no crédito habitação"'` para `'"garantia pessoal do
Estado"'`, com o raciocínio completo em comentário) — `data_minima`
("2026-07-20") mantida sem alteração, já cobre correctamente os itens
históricos que este termo mais amplo devolve. `tests/test_dre_habitacao_
watchlist.py::test_dre_habitacao_garantia_pesquisa_a_frase_tematica_
nao_a_citacao` e `tests/test_dre_termos_pesquisa.py` (lista de frases
temáticas comprovadas) actualizados para o termo novo. Não é o mesmo
padrão do IAS/PSU/PAER (citação de diploma por número) — é o mesmo
padrão já corrigido nas sessões anteriores (Issues #147/#148): um termo
nunca confirmado contra o motor real antes de ser publicado. **Lição
reforçada**: mesmo uma correcção que já não tem "forma de citação"
(passa o guardrail `test_dre_termos_pesquisa.py`) ainda precisa de
confirmação directa contra o motor real antes de ser dada como
resolvida — o guardrail apanha a forma errada, nunca a semântica
errada.

Suite completa: **3660 passed, 4 skipped** (allow-list de skips
confirmada elemento a elemento, sem alteração); `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper novo). A 1.ª corrida real do pipeline com o termo
novo confirma se `dre_habitacao_garantia` sai do estado `BLOQUEADO`;
Issue #151 fecha-se sozinha ao recuperar (mesma máquina de estados de
sempre). Trabalho feito na branch `claude/garantia-termo-e-triagem-150`
(designada pelo ambiente remoto desta sessão) — commit local, **sem
push** (instrução explícita desta sessão).*

---

*Última revisão: 2026-09-02 — nova página `garantia-para-a-infancia.html`,
8.ª página do cluster `familia`. Sessão notável por ser um dos raros casos
deste projecto com **leitura directa** de diplomas primários (Decreto
Regulamentar n.º 3/2022, arts. 3.º/4.º/5.º/6.º/8.º/9.º/10.º; Portaria n.º
60/2026/1, art. 5.º) em vez de triangulação — mas a página distingue
explicitamente, no seu próprio bloco de fontes, o que veio dessa leitura
directa do que veio de fontes secundárias, exactamente como pedido.

**Verificação do limiar de rendimento (art. 4.º) — achado real, não
corrigido**: o artigo 4.º remete o limite de Rendimento de Referência
para portaria própria; essa portaria nunca foi identificada (`WebFetch`
confirmado bloqueado nesta sessão para TODOS os domínios testados —
`diariodarepublica.pt`, `files.dre.pt`, `homepagejuridica.pt`,
`dre.tretas.org`, até `en.wikipedia.org` — não é bloqueio específico ao
Estado). `dados/parametros/abono.yaml` confirma que o valor hoje
publicado (2.495,37 €/ano) nunca esteve ligado a uma portaria concreta —
`referencia_legal` cita só o Guia Prático 4001 do ISS, I.P. (documento
interpretativo, não diploma) e `fonte_url` é a homepage genérica
`dre.pt`. Triangulação nova por 3 fontes financeiras independentes,
aritmeticamente consistentes com os IAS reais de cada ano, revelou uma
estrutura não documentada até agora: o limiar da Garantia pode seguir os
MESMOS 3 cenários já parametrizados para os limites de escalão do abono
(`escalao1-4_limite_cenario_*`) — manutenção/rendimentos 2024 → 2.495,37 €
(IAS 509,26 €); pedidos novos/rendimentos 2025 → 2.560,25 € (IAS 522,50 €);
reavaliação/rendimentos 2026 → 2.631,94 € (IAS 537,13 €). Verificado no
código: `simulador-abono.html` declara em comentário (linha ~444) aplicar
sempre o cenário "pedidos novos" para os escalões, mas usa
`garantia_infancia_limite_rr_anual` (o valor do cenário "manutenção") para
a Garantia — uma inconsistência interna real. A correcção de 19/07/2026
trocou o valor antigo (2.631,94 €, cenário de reavaliação) por 2.495,37 €
(cenário de manutenção), nunca pelo valor coerente com o resto do
simulador (2.560,25 €).

**Decisão do Nuno, seguida à letra**: não corrigir — triangulação sem
fonte primária "trocaria uma suposição por outra". `abono-de-familia.html`,
`simulador-abono.html` e `dados/parametros/abono.yaml` **não foram
tocados nesta sessão** (incluindo o efeito colateral mecânico de
`scripts/sincronizar_clusters.py`, que reescreveria o `RELACIONADOS` de
`abono-de-familia.html` ao adicionar a página nova ao cluster — corrido
normalmente sobre o repositório inteiro e depois revertido `git checkout
-- abono-de-familia.html` só nesse ficheiro, mantendo as restantes
actualizações mecânicas de `index.html`/`p/familia.html`/
`subsidio-parental.html`/`assistencia-familia-filhos.html`, nenhuma
delas relacionada com a controvérsia). A página nova publica o valor
2.495,37 € citando a mesma fonte (Guia Prático) mas com uma frase
explícita — "não está confirmado numa fonte primária" — trancada por
`tests/test_valores_ancora.py::test_garantia_infancia_limiar_nunca_afirmado_como_confirmado`.
Investigação completa (a tabela dos 3 cenários, a inconsistência do
simulador, os passos para a sessão dedicada) registada em `ROADMAP.md` →
"TRABALHO FUTURO REGISTADO".

**Verificação da relação com a PSU — resolvida com fonte primária, não
inferência**: o repositório já tinha `dados/fontes/Decreto-Lei n.PDF`
(o texto integral do DL n.º 166/2026, usado na sessão do art. 17.º de
16/08/2026) — extraído com `pymupdf` (`pypdf` falhou por um conflito
`cryptography`/`cffi` neste sandbox) e pesquisado directamente. Confirmado
por leitura da "Norma revogatória" (art. 62.º, alíneas a) a p)) e da lista
de diplomas alterados (art. 1.º, n.º 2, alíneas a) a k)): **nenhuma
menciona o Decreto Regulamentar n.º 3/2022 nem a Garantia para a
Infância** — confirmado também por `grep -i "infância"` ao texto inteiro
(75.490 caracteres, zero ocorrências). A página afirma isto com
certeza — nunca "segue a mesma lógica do abono", a inferência
inicialmente proposta e explicitamente rejeitada pelo Nuno nesta sessão
a favor da verificação real (trancado por
`tests/test_garantia_infancia_psu_por_leitura_directa_nunca_por_inferencia`).

**Conteúdo da página**: `.resposta-rapida` (56 palavras) abre pelo facto
de ser automática (art. 10.º, reconhecimento oficioso); aviso dedicado
sobre as majorações nunca contarem para o diferencial (art. 6.º, n.º 1 —
"é aqui que mais se erra a fazer as contas à mão"); exemplo idêntico ao
já publicado em `abono-de-familia.html` (criança de 8 anos, 1.º escalão,
75,13 € + 52,20 € = 127,33 €), trancado por canário cruzado entre as duas
páginas; FAQ de 8 perguntas com paridade 1:1 `<details>`↔JSON-LD;
checklist final de 5 itens (adaptada à natureza automática da prestação —
"confirmar", não "pedir"). `<title>`/meta description usam só valores
directamente confirmados (127,33 €/mês, 52,20 €/mês) — o limiar por
confirmar nunca entra em metadados, só no corpo, com a ressalva.

**Integração**: `data/clusters.json` (8.ª página do cluster `familia`,
inserida a seguir a `abono-de-familia.html`, edição cirúrgica de texto —
nunca `json.dump()` do ficheiro inteiro, lição já registada numa sessão
anterior sobre reformatação acidental). `scripts/sincronizar_clusters.py`
corrido sobre o repositório inteiro — actualizou correctamente
`index.html` (`ATUALIZACOES:HOME`), `p/familia.html` (`PILLAR-LISTA` +
`PILLAR-JSONLD`, 4→5 itens), `subsidio-parental.html` e
`assistencia-familia-filhos.html` (RELACIONADOS com a página nova,
perdendo o cross-link para a PSU que já esgotava o máximo de 4 — mesmo
efeito automático já documentado nesta secção para outras sessões);
`abono-de-familia.html` foi revertido a seguir (`git checkout --`), por
decisão do Nuno. A própria página nova já nasceu com `CLUSTER-BADGE`/
`RELACIONADOS` correctos escritos à mão — confirmado por **zero
alterações** a ela própria na corrida do script. `scripts/
sincronizar_nav.py`, `adicionar_canonicas.py`, `adicionar_autoria_artigos.py`
e `adicionar_article_jsonld.py` confirmados a **zero alterações** (nav,
canónica, autoria e `Article` JSON-LD já correctos à partida — incluindo
o cuidado já documentado de pôr `author`/`publisher` directamente no
`FAQPage` à mão, porque o `@id` da NV Labs já presente no `Article` faz
`adicionar_autoria_artigos.py` saltar essa inserção). `scripts/
gerar_og_images.py --write` gerou só a imagem nova (1200×630, confirmado
pelo cabeçalho JPEG real). `fontes.html` ganhou um cartão novo para o
Decreto Regulamentar n.º 3/2022 (a citação nem sequer é apanhada pela
regex de `tests/test_fontes_coerencia.py`, que só reconhece
"Decreto-Lei"/"Portaria"/"Lei"/"Despacho" — acrescentado por convenção do
site, não por exigência do teste). `sitemap.xml` e `scripts/pesquisa.js`
actualizados manualmente.

**Efeito lateral incidental, sem relação com esta sessão**: `scripts/
inserir_botao_partilhar.py`, corrido sobre o repositório inteiro,
encontrou e corrigiu uma lacuna pré-existente em `verificador-apoios.html`
(nunca tinha o botão "Partilhar este artigo") — mantido, por ser
exactamente o comportamento idempotente esperado do script, mesmo padrão
de divulgação transparente já usado noutras sessões para efeitos
colaterais deste tipo.

**Ambiente de sandbox desta sessão**: `playwright`, `beautifulsoup4`,
`lxml`, `jsonschema`, `pytest` e `pymupdf` não estavam instalados —
instalados nesta sessão (`PyYAML`/`feedparser` excluídos do
`requirements.txt` na instalação em lote por conflitos — `PyYAML` já
estava presente via pacote do sistema; `feedparser` corrigido com o
mesmo workaround já documentado em várias sessões anteriores para o bug
`install_layout`/`setuptools` do `sgmllib3k`: baixado o tarball via `pip
download --no-binary` e extraído `sgmllib.py` para `site-packages` à
mão). Browsers Chromium reaproveitados de `/opt/pw-browsers` (revisão
1194) via `PLAYWRIGHT_BROWSERS_PATH` e os `_localizar_chromium()`
já existentes por ficheiro de teste.

Suite completa (`pytest tests/ -q`): **3673 passed, 4 skipped** (13
testes novos: 5 em `test_valores_ancora.py`; a allow-list de skips
confirmada elemento a elemento, sem alteração); `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Trabalho feito na branch
`claude/garantia-para-a-infancia-d6gni5` (designada pelo ambiente remoto
desta sessão) — commit local, **sem push** (instrução explícita desta
sessão).*

---

*Última revisão: 2026-09-02 (sessão "Limiar da garantia — cenários",
seguimento directo à sessão anterior) — investigada a fonte do limiar de
elegibilidade da Garantia para a Infância (`garantia_infancia_limite_rr_
anual`), registada em `ROADMAP.md` como "por confirmar em fonte
primária". **Encontrada a fonte primária da OBRIGAÇÃO legal, mas não o
seu texto**: o art. 4.º c) do Decreto Regulamentar n.º 3/2022 remete este
limiar para portaria própria dos membros do Governo das finanças e da
segurança social — confirmada como a **Portaria n.º 223/2022, de 6 de
setembro** (via listagem oficial em sgeconomia.gov.pt, achado novo desta
sessão). Confirmado também que a Portaria n.º 60/2026/1 (já lida numa
sessão anterior) não fixa este limiar — só o valor de referência mensal
(art. 5.º/2 DR 3/2022, 1.528€/ano). E que o art. 9.º do DL n.º 176/2003,
para onde o art. 4.º c) remete o CÁLCULO do Rendimento de Referência
(não o limiar em si), usa a mesma lógica de 3 cenários já parametrizada
para os limites de escalão do abono — reforça, sem confirmar, a hipótese
de que o limiar também varia por cenário.

**WebFetch confirmado 100% bloqueado nesta sessão** para todos os
domínios testados — não só `.gov.pt`/`diariodarepublica.pt` (já
documentado em dezenas de sessões anteriores), mas também
`dre.tretas.org`, `pgdlisboa.pt`, `lexlink.eu` e até páginas de bancos
(`santander.pt`, `cgd.pt`) — por isso nunca foi possível ler o texto da
Portaria n.º 223/2022 nem de uma eventual actualização anual. Uma
triangulação nova via `WebSearch` (Doutor Finanças/Montepio/Santander/
e-konomista/CGD) devolveu, pela 1.ª vez numa única síntese coerente, os
3 valores em simultâneo — manutenção 2.495,37€/pedidos novos
2.560,25€/reavaliação 2.631,94€, com a mesma terminologia já usada no
site — mas continua a ser triangulação de fontes secundárias, não uma
fonte primária lida, pelos padrões deste repositório (`REGRA DE OURO`/
"REGRAS DE CONTEÚDO": nunca publicar de triangulação quando a fonte
primária existe mas não foi lida). **Nenhum valor foi alterado**:
`dados/parametros/abono.yaml` ganhou só um comentário novo (Portaria n.º
223/2022 + o cruzamento com o DL 176/2003, sem tocar em nenhum
`valor:`), confirmado sincronizado com `dados/parametros.json`
(`gerar_parametros_json.py --check`).

**Incoerência interna corrigida** (independente da Parte 1, verificável
só pelo código): `simulador-abono.html` declarava em comentário aplicar
sempre o cenário (b) — pedidos novos — "a este simulador" em bloco,
quando isso só é verdade para os limites de escalão
(`escalao1-4_limite_cenario_pedidos_novos_2026`); a Garantia usa
`garantia_infancia_limite_rr_anual`, um valor único sem variante por
cenário, com origem documentada como cenário (a) manutenção. Corrigido o
comentário (nunca o valor nem o comportamento) para escopar a afirmação
"cenário (b)" aos limites de escalão e sinalizar explicitamente a
incoerência, com o raciocínio completo e a fórmula candidata
(2.560,25€ = 0,35 × IAS 2025 × 14) para quando a fonte primária existir.
`ROADMAP.md` actualizado com o mesmo achado, substituindo a entrada da
sessão anterior em vez de a duplicar.

`pytest tests/ -q` reconfirmado sem regressões (nenhum valor tocado,
`tests/test_valores_ancora.py::test_garantia_infancia_limiar_nunca_
afirmado_como_confirmado` continua a passar sem alteração).
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/limiar-garantia-cenarios-2txc4c` (designada pelo ambiente remoto
desta sessão) — commit local, **SEM PR — branch não integrada em
`main`** (instrução explícita desta sessão: "Não fazer push").*

---

*Última revisão: 2026-09-02 (sessão "Limiar da garantia — cenários",
2.ª ronda "CORRIGIR O QUE ESTÁ CONFIRMADO", seguimento directo à sessão
anterior) — o Nuno leu directamente o texto da **Portaria n.º 223/2022,
de 6 de setembro, art. 2.º** (WebFetch continua bloqueado nesta sessão
para todos os domínios testados, incluindo um PDF fora de `.gov.pt`
hospedado em `exercito.pt`) e confirmou o que a ronda anterior só tinha
levantado por triangulação: o limite da Garantia para a Infância é
fixado em 0,35 do IAS "em vigor à data a que se reportam os rendimentos
apurados" — redacção IDÊNTICA à do art. 14.º n.º 2 do DL n.º 176/2003
(mecânica dos limites de escalão do abono). Por isso o limiar segue a
MESMA lógica de 3 cenários já parametrizada para os escalões.

`dados/parametros/abono.yaml`: `garantia_infancia_limite_rr_anual`
(valor único, cenário de manutenção) substituído por 3 parâmetros —
`garantia_infancia_limite_rr_anual_cenario_manutencao_2025` (2.495,37 €),
`..._pedidos_novos_2026` (2.560,25 €), `..._reavaliacao_2026`
(2.631,94 €) — todos com `referencia_legal` a citar a Portaria n.º
223/2022 em vez do Guia Prático 4001 (interpretativo). `simulador-
abono.html`: `limiteGarantia` passa a ler o parâmetro do cenário (b)
pedidos novos (2.560,25 €) — o mesmo cenário já usado para os limites
de escalão, resolvendo a incoerência interna sinalizada na ronda
anterior (o simulador declarava em comentário aplicar sempre o cenário
(b), mas usava o valor do cenário (a) para a Garantia); comentário JS
reescrito para reflectir a resolução. `abono-de-familia.html` e
`garantia-para-a-infancia.html` ganharam a tabela dos 3 cenários (mesmo
formato já usado para os escalões) e a citação da portaria, substituindo
o texto "não está confirmado numa fonte primária". `fontes.html` ganhou
cartão para a Portaria n.º 223/2022.

**O que fica por confirmar, registado em comentário no YAML e em
ROADMAP.md**: o multiplicador ×14 usado para anualizar o IAS. Pesquisa
dedicada via `WebSearch` (WebFetch continua bloqueado) não encontrou
nenhuma norma que anualize o IAS desta forma — nem a Portaria n.º
223/2022 nem o art. 9.º do DL n.º 176/2003 têm essa cláusula expressa; o
art. 14.º n.º 3 do DL 176/2003 anualiza incluindo férias/Natal mas está
circunscrito à RMMG, nunca ao IAS. As sínteses do WebSearch eram
inconsistentes entre si (uma chegou a devolver um valor "2.354,11 €" sem
qualquer base) e nenhuma citou um artigo concreto. Mantido o ×14 — é o
valor que o Guia Prático 4001 do ISS, I.P. publica e que a Segurança
Social aplica na prática — mas por analogia com o regime dos escalões,
nunca por norma expressa confirmada; o caso **não fecha por completo**
nesta sessão.

**Efeito prático da correcção**: uma banda de 64,88 €/ano de RR
(2.495,37 € a 2.560,25 €) que antes ficava de fora da Garantia (por o
simulador usar, por engano, o limiar mais baixo do cenário de
manutenção) passa a ter direito — o novo limiar é sempre mais generoso,
nunca o inverso. Trancado em 2 testes novos de fronteira: RR = 2.530 €
(1 criança, rendimento anual 5.060 €) passa de `garantiaAplicada=False`
para `garantiaAplicada=True`; RR = 2.600 € confirma que o simulador
nunca usa por engano o limiar ainda mais generoso do cenário (c),
2.631,94 €.

Testes: `tests/test_valores_ancora.py` (3 testes novos — citação da
portaria + os 3 valores no corpo, aviso do ×14 mantido, os 3 parâmetros
YAML) substituem `test_garantia_infancia_limiar_nunca_afirmado_como_confirmado`;
`tests/test_simulador_abono_calculo.py` (2 testes novos de fronteira
substituem `test_limite_garantia_infancia_corrigido_2495_37_nunca_2631_94`,
mais `test_parametros_producao_tem_todos_os_valores_confirmados` e
`test_coerencia_artigo_simulador_garantia_infancia` reescritos para a
mecânica de 3 cenários). `pytest tests/ -q` a passar sem regressões
(ver resultado exacto no commit desta sessão). `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo (nenhum `.py` fora de
`tests/` alterado). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_
HABILITADA` reconfirmados `False` (inalterados — sessão sem scraper).
Trabalho feito na branch `claude/limiar-garantia-cenarios-2txc4c`
(designada pelo ambiente remoto desta sessão, continuação directa da
ronda anterior) — commit local, **SEM PR — branch não integrada em
`main`** (instrução explícita desta sessão: "Não fazer push").*

---

*Última revisão: 2026-09-03 — triagem da Issue #158 (`dre_habitacao_garantia`),
pedida com 3 opções à escolha ("filtro a jusante já isola o que interessa",
"termo precisa de ser mais específico", "termo está certo, falta corte de
recência"). PASSO 0 confirmou, contra os dados reais do dia
(`data/scraped/dre_habitacao_garantia_2026-09-03.json`): dos 24 itens
devolvidos pela pesquisa `"garantia pessoal do Estado"`, 22 eram
"Resolução do Conselho de Ministros" de 1997-2021 sem relação nenhuma com
o DL 44/2024 (confirmado por `WebSearch`: a RCM n.º 30/2021 autoriza uma
garantia do Estado no âmbito de uma convenção Portugal-Angola) e só 2
eram Portarias genuinamente ligadas ao regime — a já conhecida n.º
236-A/2024/1, e a sua **1.ª alteração, a Portaria n.º 187/2025/1** (achado
real, nunca antes citada em `dados/parametros/habitacao.yaml`, confirmada
via `WebSearch` — WebFetch continua completamente bloqueado nesta sessão
para todos os domínios testados, incluindo mirrors fora de `.gov.pt`:
`files.diariodarepublica.pt`, `dre.tretas.org`, `bportugal.pt`,
`apcmc.pt`).

**Nenhuma das 3 opções propostas batia certo por inteiro** — a
investigação revelou duas mecanismos distintos, não um só: (1) o detector
DEDICADO (`detectar_decreto_lei`, chave `..._decreto_detectado`) já filtra
correctamente por tipo (só Decreto-Lei) + corte de recência
(`desde: "2026-07-20"`) — nenhum dos 24 itens é Decreto-Lei, por isso
nunca disparou por engano; isto confirma a opção (a) para ESSE mecanismo,
sem precisar de mudar o termo nem o corte. (2) A Issue #158 real veio de
um mecanismo diferente e sem filtro nenhum: o diff GENÉRICO "Detectar
mudanças e registar" de `pipeline-diario.yml` (o que escreve
`data/mudancas.json` e cria Issues `fonte-alterada`), que compara
`conteudo_extraido.itens_lista` em bruto para TODAS as fontes monitorizadas,
sem nunca filtrar por tipo de acto legal — confirmado com
`data/mudancas.json` real do dia: os 10 primeiros "itens novos" listados
na Issue eram todos RCM. Este mecanismo nunca teve corte de recência nem
filtro de tipo, ao contrário do que a opção (c) assumia ("falta corte de
recência PARA ESTA FONTE" — na verdade falta para o mecanismo GENÉRICO,
partilhado por todas as fontes DRE). A opção (b) foi descartada por
impossibilidade prática: qualquer termo novo teria de ser confirmado
contra o motor real do DRE antes de ser aceite (lição já custada em duas
rondas — Issues #147/#148/#151) e esta sessão não tem acesso a browser
interactivo real para o DRE (`WebFetch`/mirrors todos bloqueados);
inventar um termo "mais específico" sem essa confirmação teria repetido
o erro já documentado.

**Correcção aplicada**: `.github/workflows/pipeline-diario.yml`, step
"Detectar mudanças e registar" — nova allow-list `DRE_SLUGS_PESQUISA`
(um `Set`, hoje só com `'dre_habitacao_garantia'`) + `ACTO_LEGAL_REGEX`
(`/^(Decreto-Lei|Lei|Portaria|Despacho)\s/i`) + `extrairAtosLegais()`,
que filtra `itens_lista` (nunca `paragrafos` — achado lateral: um
"Decreto-Lei n.º 7/2002", sem relação nenhuma com o DL 44/2024, aparecia
em `paragrafos` mas nunca em `itens_lista`; `paragrafos` é um recorte
truncado dos primeiros resultados renderizados, `span[data-expression]`,
instável por desenho, ao contrário de `itens_lista`, o resultado completo
via `a[href*='/dr/detalhe/']`). Quando o diff filtrado fica vazio dos
dois lados, nenhuma "mudança" é registada — nunca uma Issue "mudou algo"
sem nada de accionável. Fontes fora da allow-list mantêm o comportamento
anterior, sem qualquer alteração.

**Deliberadamente NÃO generalizado às outras 4 fontes DRE de pesquisa
interactiva** (`dre_psu`, `dre_psu_regulamentacao`, `dre_habitacao_paer`,
`dre_ias`) — verificado antes de decidir, não por precaução vazia:
`dre_habitacao_paer` tem um caso real e já testado
(`tests/test_diff_mudancas_issue.py`, Issue #114) em que o sinal
relevante era um "Regulamento" da Série II, um tipo FORA desta allow-list
— aplicar o mesmo filtro ali sem confirmar primeiro o perfil de ruído
real dessa fonte teria regredido silenciosamente uma detecção já
validada (confirmado explicitamente: com o filtro aplicado ao par real
`dre_habitacao_paer_2026-08-{19,20}.json`, o diff filtrado fica vazio,
apagando o sinal). `dre_psu`/`dre_psu_regulamentacao` foram verificadas
de passagem (o par real usado na Issue #150, `dre_psu_regulamentacao_
2026-09-0{1,2}.json`, tem os 9 itens TODOS dentro da allow-list — o
filtro aqui seria um no-op, mas nunca activado nesta sessão por
disciplina de escopo) e `dre_ias` nunca foi examinada. Generalizar por
analogia sem confirmar contra dados reais é exactamente o erro que já
custou duas rondas a este sentinela — registado em `ROADMAP.md` →
"TRABALHO FUTURO REGISTADO" para uma sessão dedicada, fonte a fonte.

**Testes**: novo `tests/test_diff_mudancas_allow_list_dre.py` (9 testes)
— estáticos sobre o script real do workflow (allow-list existe, scoped
só a `dre_habitacao_garantia`, extracção só de `itens_lista`, supressão
quando filtrado fica vazio) e comportamentais sobre dados REAIS desta
sessão (`data/scraped/dre_habitacao_garantia_2026-09-0{2,3}.json`): o
diff em bruto é dominado por RCM (10/10 dos itens capados são RCM), o
diff filtrado isola só as 2 Portarias relevantes, a Portaria 187/2025/1
ainda não está no YAML (canário para a sessão de fact-check futura), e
uma regressão directa confirmando que `dre_habitacao_paer` continua com
o comportamento antigo intacto. Sintaxe e lógica do JS novo validadas
com `node --check` e execução real (`node`) contra os dados reais do
dia — não só lidas, confirmadas a produzir exactamente o `data/mudancas.json`
esperado (2 Portarias, zero RCM) antes do commit. `tests/test_diff_mudancas_issue.py`
(13 testes pré-existentes) reconfirmado sem alterações.

Issue #158 fechada com o desfecho completo (termo correcto, detector
dedicado correcto, ruído era do diff genérico sem filtro — corrigido
scoped a esta fonte, achado lateral da Portaria 187/2025/1 registado
para fact-check). `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados — sessão sem scraper novo, só
correcção ao diff genérico de mudanças). Trabalho feito na branch
`claude/triagem-158-garantia-ty23uz` (designada pelo ambiente remoto
desta sessão) — commit local, sem push (instrução explícita desta
sessão).*

---

*Última revisão: 2026-09-05 — Anel 3, parte A: invalidez e acumulação com
trabalho, cluster `/p/reformas.html`. Três páginas novas —
`invalidez-relativa-ou-absoluta.html`, `pensao-e-trabalho.html`,
`quando-a-invalidez-vira-velhice.html` — todas dependentes exclusivamente
do Decreto-Lei n.º 187/2007 (versão consolidada, DRE), já verificado por
inteiro numa sessão anterior (Anel 1+2, 4 set. 2026) — nenhum fact-check
novo necessário, o brief já trazia os artigos exactos citados. Mesma
anatomia obrigatória dos Anéis 1/2: resposta-rápida (≤60 palavras,
confirmado por contagem programática nas 3 — 48/43/45 palavras) → tabela/
regra → exemplo → checklist, sempre em múltiplos do IAS/RR ou por remissão,
nunca valores anuais em euros — única excepção deliberada: as coimas do
art. 92.º (50 a 350 €), citadas com nota explícita de que são montantes
fixados directamente pelo diploma, não por portaria anual, e nunca
colocadas em `<title>`/meta description (por isso sem entrada nova em
`tests/test_valores_ancora.py`).

**Regra de contenção respeitada**: nenhuma das 3 páginas fala de pensão de
sobrevivência, complementos autónomos ou regimes paralelos — o único
`complemento social` citado é a exclusão de base de cálculo do art. 59.º,
n.º 3, já mencionada explicitamente no próprio brief.

**Decisão de datação**: o brief citava a fonte como "verificada em
2026-09-04" (data da sessão anterior que fez o fact-check completo do
DL 187/2007 para os Anéis 1/2) — inicialmente usada como "Verificado a"
das 3 páginas novas, por analogia directa com essa frase. Corrigido antes
do commit: **todo o histórico deste ficheiro usa sempre a data da própria
sessão/commit para "Verificado a"/`datePublished`/`dateModified`, nunca a
data de uma verificação anterior herdada** (confirmado por grep a
`renovar-cartao-cidadao.html`/`garantia-para-a-infancia.html` antes de
decidir) — as 3 páginas novas, `p/reformas.html` (só `dateModified`, pelo
Anel 3 ter passado a ter conteúdo real) e a entrada nova da tabela
"PÁGINAS PUBLICADAS" usam **5 set. 2026** (data real desta sessão), nunca
4 set. `index.html` (`ATUALIZACOES:HOME`) resincronizado a seguir — as 3
páginas novas + `majoracao-subsidio-desemprego.html` (também com
"Verificado a 5 set. 2026", de fora do âmbito desta sessão) passam a
ocupar as 4 posições, por serem hoje as mais recentemente verificadas do
site inteiro.

**`p/reformas.html`**: card "Anel 3" deixou de estar `Em preparação` — 3
mini-cards para as páginas novas + `aviso-info` explícito de que a pensão
de sobrevivência continua em levantamento (DL 187/2007 não a regula,
nada publicado sem fonte primária). `PILLAR-LISTA`/`PILLAR-JSONLD`
(`numberOfItems` 7→10) regenerados por `scripts/sincronizar_clusters.py`.

**Achado lateral, corrigido no mesmo commit — drift pré-existente, sem
relação com esta sessão**: `sincronizar_clusters.py --dry-run` já
reportava, antes de qualquer alteração minha (confirmado por `git stash`),
que `majoracao-subsidio-desemprego.html` (editado por outra sessão/
pipeline, "Verificado a 5 set. 2026") tinha o bloco `RELACIONADOS`
desactualizado (ainda apontava a `/simulador-subsidio-desemprego.html`,
inexistente hoje) — corrigido como efeito mecânico e seguro do próprio
script, mesmo padrão já documentado várias vezes neste ficheiro para
"efeito lateral, sem relação com [o tema desta sessão]".

**Achado de acessibilidade, corrigido antes do commit**: as duas tabelas
comparativas (`invalidez-relativa-ou-absoluta.html`,
`quando-a-invalidez-vira-velhice.html`) tinham `<th></th>` vazio na
1.ª coluna — apanhado por `tests/test_acessibilidade.py`
(`empty-table-header`, minor, acima do limiar de 0) — corrigido com texto
descritivo ("Regra"/"Aspecto"), mesmo precedente de `porta-65.html`.

**Redundância removida antes do commit**: a 1.ª versão de
`pensao-e-trabalho.html` repetia a frase "os limites calculam-se sobre a
pensão sem extras" duas vezes, byte a byte — uma vez como `aviso-info`
isolado, outra como item 4 de "Quatro coisas que quase ninguém sabe" (o
item pedido pelo brief). Removido o `aviso-info` duplicado, mantido só o
item da lista.

**Ligações internas obrigatórias** (exigidas explicitamente para
`quando-a-invalidez-vira-velhice.html`) confirmadas presentes:
`idade-normal.html` (3×), `pensao-e-trabalho.html` (2×),
`invalidez-relativa-ou-absoluta.html` (1×). `pensao-e-trabalho.html`
ganhou também um cross-link de corpo para `invalidez-relativa-ou-absoluta.html`
(não exigido pelo brief, mas necessário — a página usa os termos "invalidez
relativa/absoluta" sem os definir). O bloco `RELACIONADOS` automático das
3 páginas novas mostra sempre os 4 primeiros irmãos do cluster (Anel 1) —
comportamento mecânico já documentado noutras entradas deste ficheiro,
nunca uma regressão desta sessão.

Integração completa: `data/clusters.json` (edição cirúrgica de texto, não
`json.dump()` do ficheiro inteiro — lição já registada numa sessão
anterior sobre reformatação acidental), `sitemap.xml`,
`scripts/pesquisa.js`, `scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO`). `scripts/sincronizar_nav.py`,
`scripts/inserir_botao_partilhar.py`, `scripts/adicionar_canonicas.py`,
`scripts/adicionar_autoria_artigos.py` e `scripts/adicionar_article_jsonld.py`
confirmados todos a **zero alterações** às 3 páginas novas — nav, botão de
partilha, canónica, autoria e `Article` JSON-LD já nasceram correctos.
`scripts/gerar_og_images.py --write` gerou as 3 imagens (1200×630,
confirmado pelo cabeçalho JPEG real, chip "Reformas e Pensões" herdado de
`data/clusters.json`).

**Ambiente de sandbox desta sessão**: `beautifulsoup4`/`lxml`/`playwright`/
`playwright-stealth`/`jsonschema`/`requests`/`pytest` não estavam
instalados — instalados nesta sessão; `feedparser` corrigido com o mesmo
workaround já documentado em dezenas de sessões anteriores para o bug
`install_layout`/`setuptools` do `sgmllib3k` (tarball extraído à mão para
`site-packages`). Achado novo desta sessão: `pytest`/`ruff` no `PATH`
resolviam para binários `uv tool` isolados (`/root/.local/share/uv/tools/`),
com o seu próprio ambiente Python separado do `python3` do sistema onde os
pacotes acima foram instalados — `python3 -m pytest tests/test_valores_ancora.py`
falhava com `ModuleNotFoundError: No module named 'yaml'` mesmo com
`python3 -c "import yaml"` a funcionar directamente, porque o `pytest` do
PATH usava outro interpretador. Corrigido instalando `pytest` também no
`python3` do sistema e usando sempre `python3 -m pytest` daí em diante —
registado aqui para a próxima sessão neste sandbox não repetir o mesmo
diagnóstico.

Verificado nesta sessão: os 3 blocos JSON-LD de cada página válidos
(`json.loads`), paridade 1:1 FAQ visível↔JSON-LD (7/7, 7/7, 5/5),
`verificar_datas.detectar_alertas()` sem falsos positivos em nenhum mês
de 2026/2027, zero overflow horizontal a 375px e zero erros de consola
com Chromium real (só o aviso esperado de rede bloqueada do GA4/sandbox),
checklist a actualizar o contador e a nunca persistir em `localStorage`
entre reloads (confirmado com Chromium real, não só por ausência da
string no código), `tests/test_acessibilidade.py` a 0 violações
critical/serious/moderate/minor nas 5 páginas tocadas
(`invalidez-relativa-ou-absoluta.html`, `pensao-e-trabalho.html`,
`quando-a-invalidez-vira-velhice.html`, `p/reformas.html`, `index.html`).
Suite completa (`pytest tests/ -q`) e `ruff check scripts/ tests/ --select
E,F,W --ignore E501 .` corridos antes do commit — ver o resultado exacto
no commit desta sessão. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Trabalho feito na branch designada pelo ambiente
remoto desta sessão, `claude/anel-3-invalidez-acumulacao-es1ruo` — ver o
resumo final da sessão para o estado exacto de integração (PR aberto,
merged, ou sem PR).*

---

*Última revisão: 2026-09-06 — Anel 3, parte B: sobrevivência e subsídio por
morte, cluster `/p/reformas.html`. Três páginas novas —
`pensao-de-sobrevivencia.html`, `subsidio-por-morte.html`,
`quem-tem-direito-por-parentesco.html` — dependentes do Decreto-Lei n.º
322/90, de 18 de outubro, na redação em vigor (última alteração
conhecida: Decreto-Lei n.º 40/2025). Regra metodológica do brief seguida
à letra: a consolidação do DRE é a fonte de decisão sobre o que está em
vigor hoje, os diplomas alteradores servem só para reconstruir a
cronologia — nunca para determinar isoladamente a redação actual.
`WebFetch`/`curl` continuam completamente bloqueados nesta sessão para
`diariodarepublica.pt` (mesma limitação documentada em dezenas de
sessões anteriores), por isso o texto integral do diploma não foi lido
directamente; todo o conteúdo foi triangulado por múltiplas fontes
independentes via `WebSearch` (Santander, CGD, DECO PROteste, Montepio,
Doutor Finanças, CA Vida, entre outras), incluindo confirmação directa
das percentagens, prazos e datas de vigência dadas pelo brief — nenhuma
divergência encontrada.

**pensao-de-sobrevivencia.html**: prazo de garantia de 36 meses (72 no
seguro social voluntário, art. 16.º); pensão de base a partir da pensão
de invalidez/velhice do falecido, com fórmula proporcional (R/60) para
carreiras <60 meses (art. 24.º, n.º 3); tabela completa das 11
percentagens por grupo de titulares (arts. 25.º a 27.º), com a simetria
"sem cônjuge, a percentagem dos descendentes duplica" destacada; sem
prazo de caducidade desde o DL 133/2012 (art. 48.º, n.º 1); cessação por
casamento/união de facto (art. 41.º, alínea a), com a cronologia
DL133/2012→Lei82-B/2014 explicitada, nunca atribuída só ao primeiro
diploma. O limite da pensão do ex-cônjuge (art. 29.º, n.º 5) — a "Falha
1" registada no brief — é tratado com o mesmo cuidado: existência
confirmada (aditado pelo DL 133/2012), redação exacta em vigor marcada
como "por confirmar directamente na consolidação", sem desenvolvimento
nem link para as páginas de cônjuge/união de facto (ainda bloqueadas,
sem fonte — Decreto Regulamentar n.º 1/94 e Lei n.º 7/2001 — por
instruir).

**subsidio-por-morte.html**: prestação única, 3 × IAS (art. 32.º),
prazo de 180 dias (art. 48.º, n.º 2). Secção dedicada à cronologia do
valor — a "Falha 2" do brief — corrige de propósito a atribuição comum
do valor actual ao DL 133/2012: esse diploma introduziu uma fórmula
transitória (6 × RR, máx. 6 × IAS), em vigor só 7 meses (01-07-2012 a
31-01-2013); o valor fixo de 3 × IAS é do DL 13/2013, desde 01-02-2013.
Tabela de desambiguação das 4 prestações por morte (pensão de
sobrevivência/DL322-90, subsídio por morte/DL322-90 art.32, reembolso
de despesas de funeral/DL322-90 art.54 n.2, subsídio de funeral/DL
176/2003 art.16) — nunca fundidas. Nota sobre o DL 104/2026 (remissão
normativa do subsídio de funeral para o limite do art. 54.º, n.º 2, sem
alterar o DL 322/90 em si) — "citar um artigo noutro diploma não
transforma a citação em alteração".

**quem-tem-direito-por-parentesco.html**: hierarquia de 3 grupos
(cônjuge/ex-cônjuge → descendentes → ascendentes, nunca acumulando o 3.º
com os dois primeiros); idade dos descendentes (art. 12.º, na redação do
DL 53/2023, de 5 de julho — a última alteração conhecida a este artigo,
confirmada por triangulação): sem condição até aos 18, dos 18 aos 25 se
estudante, dos 25 aos 27 em pós-graduação/mestrado/doutoramento/estágio
obrigatório, sem limite com deficiência.

**Detecção 3 do brief (art. 41.º) replicada nesta sessão**: a hipótese
inicial de que a cessação por casamento/união de facto seria só redação
do DL 133/2012 foi corrigida ao confirmar, por `WebSearch`, uma segunda
alteração pela Lei n.º 82-B/2014 — a página cita as duas, nunca só a
primeira.

Integração: `data/clusters.json` (3 páginas novas no cluster
`reformas`), `sincronizar_clusters.py`/`sincronizar_nav.py`/
`inserir_botao_partilhar.py`/`adicionar_canonicas.py`/
`adicionar_autoria_artigos.py`/`adicionar_article_jsonld.py`/
`gerar_og_images.py --write` corridos — as 3 páginas já nasceram com nav,
canónica, autoria, `Article` JSON-LD, botão de partilha e imagem OG
correctos (zero alterações desses scripts às páginas novas);
`sincronizar_clusters.py` regenerou `index.html` (`ATUALIZACOES:HOME`) e
`p/reformas.html` (`PILLAR-LISTA`/`PILLAR-JSONLD`, 10→13 itens). `p/
reformas.html` reorganizado: "Anel 3" renomeado para "Anel 3A" (invalidez
e trabalho, DL 187/2007), novo card "Anel 3B" (sobrevivência e subsídio
por morte, DL 322/90) com aviso explícito sobre as 3 páginas ainda
bloqueadas (cônjuge, união de facto, duração — DR 1/94 e Lei 7/2001 por
instruir); FAQ do pillar (visível + JSON-LD, paridade confirmada)
corrigida para deixar de afirmar "sempre com o artigo do DL 187/2007
citado" como se fosse o único diploma do guia — passa a citar os dois,
consoante o tema. `fontes.html` ganhou 7 cartões novos (DL 322/90,
DL 133/2012, DL 13/2013, Lei 82-B/2014, DL 53/2023, DL 104/2026, Lei
7/2001) — `tests/test_fontes_coerencia.py` confirmou e exigiu cada um
(nenhum diploma citado ficou de fora nem foi parar à allow-list de
excepções). `sitemap.xml`, `scripts/pesquisa.js` actualizados.

Novo canário em `tests/test_valores_ancora.py`
(`test_pensao_sobrevivencia_meta_description_percentagens_batem_com_a_tabela`
+ variante `og:description`) — as percentagens 20%/80% citadas no
`<meta name="description">`/`og:description` de
`pensao-de-sobrevivencia.html` não derivam do IAS (vêm directamente da
lei, sem fórmula), por isso o canário é de consistência com a tabela do
corpo — confirmado a falhar de propósito (valor adulterado para "99%")
e revertido.


---

*Correcção (2026-09-06, mesmo dia) — três correcções a `subsidio-por-morte.html`,
verificadas pelo Nuno na leitura integral da consolidação do DL 322/90
no DRE (`WebFetch` continua bloqueado nesta sessão para
`diariodarepublica.pt`, mesma limitação de sempre — a leitura foi feita
pelo Nuno, não por esta sessão). Todas as três decorrem do
**Decreto-Lei n.º 79/2019**, o alterador mais extenso do diploma depois
do DL 133/2012, que a triangulação por `WebSearch` da sessão anterior
nunca tinha detectado — confirma, mais uma vez, a regra metodológica do
brief: um diploma alterador nunca é fonte de decisão sobre o texto
vigente, só a consolidação.

1. **Termo inicial dos prazos** (arts. 48.º, n.º 2, e 54.º, n.º 3): os
   180 dias do subsídio por morte e os 90 dias do reembolso de despesas
   de funeral contam-se da **data do registo do óbito**, não da data do
   falecimento — datas que podem divergir por vários dias. Corrigido em
   7 sítios (FAQ visível + JSON-LD, resumo rápido, resposta rápida,
   checklist, dois parágrafos de corpo), com a atribuição da redacção
   trocada de "Decreto-Lei n.º 133/2012" para "Decreto-Lei n.º 79/2019"
   onde aplicável.
2. **Art. 34.º está revogado** pelo DL 79/2019 — o piso de 1 × IAS na
   remuneração de referência, usado como explicação do "porquê" da
   fórmula transitória de 2012 colapsar sempre no mesmo valor, já não
   existe. Parágrafo inteiro removido (não substituído — a explicação
   aritmética deixou de ter base legal; a cronologia do art. 32.º em si
   mantém-se válida e intocada).
3. **Art. 54.º, n.º 4 mudou de sentido**: a redacção de 2012 mandava
   *deduzir* ao subsídio por morte o valor limite do reembolso, na
   falta de comprovativo das despesas de funeral. A redacção em vigor
   (DL 79/2019) é diferimento, não dedução: sem esse comprovativo, o
   subsídio só é pago depois de terminar o prazo de 90 dias do
   reembolso, sem que este tenha sido requerido — nunca um valor
   reduzido. Corrigido nos 3 sítios onde aparecia (FAQ visível +
   JSON-LD, parágrafo de corpo).

`fontes.html` — cartão do Decreto-Lei n.º 79/2019 expandido para
reflectir também a sua relação com o DL 322/90 (antes só mencionava o
Decreto-Lei n.º 187/2007). Nenhuma outra página do site continha estes
três erros — confirmado por grep antes de fechar (só
`subsidio-por-morte.html` cita os arts. 34.º/48.º/54.º/n.º 4 do
DL 322/90).

Verificado antes do commit: os 3 blocos JSON-LD continuam válidos,
paridade 1:1 FAQ visível↔JSON-LD confirmada, `.resposta-rapida` com 55
palavras (dentro do limite de 60), `verificar_datas.detectar_alertas()`
sem alertas em nenhum mês de 2026, 0px de overflow a 375px, zero erros
de consola (Chromium real). Suite completa + `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` — ver o resultado exacto no
commit desta correcção. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Trabalho feito na branch
`claude/anel-3b-sobrevivencia-subsidio-uy2dbl` — sem PR, por instrução
explícita.

---

*Última revisão: 2026-09-06 (continuação, "Anel 3, parte C") — fecho do
Anel 3 do cluster Reformas e Pensões: 3 páginas novas —
`duracao-da-pensao-de-sobrevivencia.html`,
`pensao-sobrevivencia-conjuge.html`,
`pensao-sobrevivencia-uniao-de-facto.html` — que completam o que o Anel
3B (publicado no mesmo dia, sessão anterior) tinha deixado
deliberadamente por fazer: a duração exacta da pensão de sobrevivência,
as condições próprias do cônjuge/ex-cônjuge, e a união de facto.

**Fontes**: DL 322/90 (arts. 38.º-42.º, duração/cessação/momento/
suspensão; arts. 9.º, 10.º, 11.º, 25.º, 28.º e 29.º, n.º 5, cônjuge) e
Decreto Regulamentar n.º 1/94 (arts. 2.º, 3.º, 4.º, 6.º, união de
facto) — ambos verificados directamente na consolidação do DRE, per o
brief. **Lei n.º 7/2001** (impedimentos, prova, arts. 1.º, n.º 2, 2.º,
2.º-A e 6.º) veio de fonte secundária — `WebFetch` confirmado
completamente bloqueado nesta sessão para **todos** os domínios
testados, não só `diariodarepublica.pt` (testado também
`www.pgdlisboa.pt`, `informador.pt`, `www.tribunalconstitucional.pt`,
`www.dgsi.pt`, `faolex.fao.org` e `en.wikipedia.org` — todos
`EGRESS_BLOCKED`), triangulada por múltiplas queries `WebSearch`
independentes e concordantes. Nota de estatuto de fonte publicada de
forma visível na página, distinguindo os dois diplomas verificados
directamente do terceiro triangulado, com pedido explícito de correcção
se alguém encontrar divergência.

**Página 1 (`duracao-da-pensao-de-sobrevivencia.html`)**: tabela do
art. 38.º (5 anos se <35 anos à data da morte, sem limite se ≥35 ou ao
completá-los ainda com direito, ou com incapacidade total e
permanente), prorrogação com descendentes (n.º 3), e uma secção
dedicada a nunca confundir duração (art. 38.º) com cessação (art. 41.º),
momento (art. 42.º) e suspensão (art. 40.º) — quatro conceitos
diferentes que o diploma trata em artigos separados. Esclarece também
que a duração dos descendentes não está aqui — o art. 39.º só trata de
situações escolares, os limites de idade estão no art. 12.º, remetido
para `quem-tem-direito-por-parentesco.html`.

**Página 2 (`pensao-sobrevivencia-conjuge.html`)**: as 4 condições de
acesso (cônjuge sem filhos — 1 ano de casamento salvo acidente/doença
posterior; separado judicialmente/divorciado — pensão de alimentos
reconhecida; casamento nulo/anulado — boa fé + pensão de alimentos;
exclusões por indignidade/deserdação), e as duas regras que se somam no
montante — percentagem (60%/70%, arts. 25.º/28.º) e o tecto do
ex-cônjuge (nunca excede a pensão de alimentos que recebia, art. 29.º,
n.º 5) — com a distinção explícita entre "SE tens direito" (art. 11.º)
e "QUANTO recebes" (art. 29.º, n.º 5), a mesma pensão de alimentos a
decidir as duas coisas por razões diferentes.

**Página 3 (`pensao-sobrevivencia-uniao-de-facto.html`)**: o valor
prático mais alto do Anel 3 — desfaz a ideia generalizada de que é
preciso ir a tribunal. Requisito (>2 anos, beneficiário não casado ou
separado judicialmente), os 5 impedimentos do art. 2.º da Lei n.º
7/2001, e a secção central sobre como se prova: desde a Lei n.º
23/2010, o direito existe independentemente da necessidade de
alimentos (art. 6.º, n.º 1) — a prova passou a ser administrativa
(declaração da junta de freguesia + declaração sob compromisso de
honra + certidões, art. 2.º-A, n.º 4), nunca sentença judicial. A
tensão entre o art. 3.º, n.º 1, do Decreto Regulamentar n.º 1/94 (ainda
exige sentença) e o art. 6.º, n.º 1, da Lei n.º 7/2001 na redacção da
Lei n.º 23/2010 (dispensa) é tratada com a gradação de 3 níveis exigida
pelo brief: 1) letra da lei (art. 6.º DR 1/94, trânsito em julgado); 2)
interpretação sistemática com apoio jurisprudencial (regra geral do
art. 36.º, n.º 1, DL 322/90 — "há jurisprudência do STJ que... reconduziu",
nunca "a jurisprudência entende", e sem número de acórdão específico,
por não ter sido possível confirmar uma fonte de publicação fiável
nesta sessão); 3) o que não se pode dizer — que o legislador resolveu
expressamente a incompatibilidade (não resolveu). Conselho prático
final: requerer dentro de 6 meses da morte torna a discussão jurídica
irrelevante para o caso concreto do leitor.

**Achado da auditoria (2.ª ronda, revisão cruzada)**: nenhum encontrado
nesta sessão — os 3 blocos JSON-LD nasceram válidos, a paridade 1:1
FAQ visível↔JSON-LD foi confirmada programaticamente nas 3 páginas
(7/7, 7/7, 8/8) antes do commit, e `verificar_datas.detectar_alertas()`
confirmou 0 alertas nas 5 páginas tocadas (as 3 novas +
`pensao-de-sobrevivencia.html` + `p/reformas.html`) em todos os meses
de revisão (1/7/8/9).

Integração: `data/clusters.json` (edição cirúrgica de texto — nunca
`json.dump()` do ficheiro inteiro, lição já registada em sessões
anteriores), `p/reformas.html` (novo card "Anel 3C", "Anel 3B" perdeu o
aviso "ainda em levantamento"), `fontes.html` (novo cartão para
Decreto Regulamentar n.º 1/94 e Lei n.º 23/2010; cartão da Lei n.º
7/2001 actualizado — deixa de dizer "página bloqueada"), `sitemap.xml`,
`scripts/pesquisa.js`, `scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO`). `scripts/sincronizar_clusters.py`,
`sincronizar_nav.py`, `inserir_botao_partilhar.py`,
`adicionar_canonicas.py`, `adicionar_autoria_artigos.py` e
`adicionar_article_jsonld.py` corridos sobre o repositório inteiro —
**zero alterações** às 3 páginas novas (nasceram já correctas,
seguindo o padrão exacto dos scripts); `sincronizar_clusters.py`
regenerou automaticamente `index.html` (`ATUALIZACOES:HOME`) e
`p/reformas.html` (`PILLAR-LISTA`+`PILLAR-JSONLD`, 13→16 itens) — as
`RELACIONADOS` dos artigos existentes do cluster não mudaram (a regra
determinística mostra sempre os 4 primeiros irmãos da lista, e as
páginas novas entraram no fim). `scripts/gerar_og_images.py --write`
gerou as 3 imagens (1200×630, confirmado pelo cabeçalho JPEG real).
`pensao-de-sobrevivencia.html` actualizada (FAQ visível + JSON-LD do
ex-cônjuge, e o card "O que quase ninguém sabe") para linkar às 3
páginas novas em vez de dizer "ainda por instruir"/"será desenvolvida".

Canário novo em `tests/test_valores_ancora.py`
(`test_pensao_sobrevivencia_conjuge_meta_description_percentagens_batem_com_o_corpo`
— 60%/70% nunca derivam do IAS, canário de consistência com o corpo,
mesmo padrão já usado para a página-mãe); nova excepção em
`tests/test_anos_metadados.py` (`("pensao-sobrevivencia-uniao-de-facto.html",
2001)` — "Lei n.º 7/2001" na meta description é número de diploma, não
data de vigência).

Ambiente de sandbox desta sessão: `pytest`/`ruff` resolviam para
binários `uv tool` isolados, separados do `python3` do sistema (mesmo
padrão documentado em sessões anteriores) — `beautifulsoup4`, `lxml`,
`jsonschema`, `requests`, `pyyaml`, `playwright` e `feedparser`
instalados para `python3`, browsers Chromium reaproveitados de
`/opt/pw-browsers`; usado sempre `python3 -m pytest`. Suite completa
não foi corrida até ao fim nesta sessão por limite de tempo (a suite
Playwright sobre as 100+ páginas do repositório excede o orçamento
desta sessão) — verificação feita com os ficheiros de teste
directamente relevantes (`test_fontes_coerencia.py`,
`test_anos_metadados.py`, `test_higiene_indexacao.py`,
`test_breadcrumb_coerencia.py`, `test_nav_coerencia.py`,
`test_valores_ancora.py`, `test_sincronizar_clusters.py`,
`test_og_image.py` — 1953 passed), mais `ruff check scripts/ tests/
--select E,F,W --ignore E501 .` limpo, validação directa de JSON-LD
(5 páginas, 15 blocos, todos válidos), paridade FAQ 1:1 e contagem de
palavras da resposta rápida (todas ≤60), tudo confirmado por scripts
Python dedicados em vez da suite completa. Registado honestamente como
verificação parcial, não como suite completa — a suite completa fica
para o CI real (`integridade.yml`) confirmar. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper).

Dois loose ends registados em `ROADMAP.md` → "TRABALHO FUTURO
REGISTADO", sem prazo, não bloqueantes: confirmação directa na
consolidação do DRE dos arts. 2.º/2.º-A/6.º da Lei n.º 7/2001; citação
exacta (número/data/fonte) do acórdão do STJ que reconduziu o início do
pagamento ao art. 36.º do DL 322/90.

Trabalho feito na branch `claude/anel-3c-sobrevivencia-4p9bbm`
(designada pelo ambiente remoto desta sessão) — **SEM PR — branch não
integrada em `main`** (protocolo de fim de sessão desta secção "REGRA
ABSOLUTA — GIT").

---

*Última revisão: 2026-09-06 — Anel 4: regimes complementares, cluster
`/p/reformas.html`. Três regimes juridicamente independentes do
Decreto-Lei n.º 187/2007, cada um instruído pelo princípio transversal
do brief — "âmbito antes da regra": nunca aplicar uma norma antes de
confirmar quem ela abrange. `WebFetch` confirmado bloqueado nesta
sessão para TODOS os domínios testados, sem excepção — não só
`diariodarepublica.pt`/`.gov.pt` (limitação de sempre), mas também
`eur-lex.europa.eu`, `europa.eu`, mirrors de terceiros
(`dre.tretas.org`, `pgdlisboa.pt`, `files.dre.pt`) e até domínios sem
relação nenhuma com o Estado (`en.wikipedia.org`) — a expectativa do
brief de que "o EUR-Lex serve páginas legíveis, ao contrário do DRE"
não se confirmou nesta sessão: o bloqueio é de rede (proxy), não do
portal. Todo o conteúdo assenta em triangulação por `WebSearch` — várias
pesquisas independentes por facto, nunca uma fonte só —, mesmo padrão já
usado em dezenas de sessões anteriores perante o mesmo bloqueio.

**Linha 1 — carreiras contributivas no estrangeiro** (prioridade 1, 2
páginas). `carreiras-contributivas-estrangeiro.html` cobre só UE (27
Estados-membros), EEE (Islândia, Liechtenstein, Noruega) e Suíça —
mesma coordenação (Regulamento (CE) n.º 883/2004 + Regulamento (CE) n.º
987/2009), três instrumentos jurídicos distintos por grupo (directo na
UE; Acordo EEE; Acordo UE-Suíça de livre circulação). Exclusão
deliberada e destacada (nunca só uma nota de rodapé) dos acordos
bilaterais com países terceiros (Brasil, EUA, Canadá, Cabo Verde) —
"ainda por documentar", nunca fingido como coberto. Totalização (art.
11.º, DL 187/2007) distinguida explicitamente de cálculo proporcional
(art. 39.º) — a distinção estruturante "aquisição do direito vs.
cálculo do montante" exigida pelo brief, com exemplo numérico (12 anos
PT / 18 estrangeiros / 30 totais → Portugal paga 12/30 do valor
teórico). `reforma-reino-unido-brexit.html`, tratamento autónomo do
Reino Unido conforme instruído: Acordo de Saída (situações
transfronteiriças anteriores a 31/12/2020, fim do período de transição)
vs. Protocolo de Coordenação da Segurança Social do Acordo de Comércio
e Cooperação (situações desde 1/1/2021) — dois instrumentos, nunca
tratados como equivalentes. Um ponto sinalizado com cautela reforçada,
não apagado nem apresentado com falsa certeza: a regra de dispensa do
cálculo proporcional do Protocolo TCA (21+ anos totais, ≤20 anos
portugueses) tem origem numa síntese de terceiros sobre uma orientação
técnica da DGSS, nunca confirmada por leitura directa do texto do
Protocolo — marcada como tal na própria página (`aviso-atencao`) e no
ROADMAP.md, para revisão quando houver acesso real ao texto.

**Linha 2 — pensão unificada** (prioridade 2, 1 página). Achado
central da sessão: o art. 63.º, n.º 2, do DL 187/2007 remete a
atribuição da pensão unificada para "lei própria" sem a identificar —
investigação confirmou que é o **Decreto-Lei n.º 361/98, de 18 de
novembro** (regime da pensão unificada, anterior ao DL 187/2007 e já
em vigor quando este saiu — por isso nunca precisou de ser citado),
alterado pelo Decreto-Lei n.º 437/99 e pela Lei n.º 83-C/2013 (OE2014).
A pista fraca do brief — Portaria n.º 642/83, citada no art. 28.º da
Portaria 480-B/2025/1 — resolvida com a mesma triangulação: o DL 361/98
revogou expressamente o DL 159/92 e a Portaria n.º 2/93, **nunca** a
Portaria 642/83, que sobrevive só como categoria de indexação de
pensões unificadas atribuídas ao abrigo do regime anterior a 1998 —
nunca regula atribuições novas. Cronologia importante documentada como
tal (antes/depois de 2014, Lei n.º 83-C/2013): a fórmula de cálculo
passou de "pensão inteira pelas regras do último regime" para "cada
parte pelas regras do seu regime, depois somadas" — nunca apresentada
como se tivesse sido sempre assim.

**Linha 3 — Caixa Geral de Aposentações** (prioridade 3, 1 página,
`caixa-geral-aposentacoes.html`). Fronteira temporal confirmada com a
norma exacta: **Lei n.º 60/2005, de 29 de dezembro, art. 2.º, n.º 1** —
fecho a novas inscrições desde 1 de janeiro de 2006 (não "2006" por
conhecimento geral, como o brief avisava para não assumir — a data e a
norma foram confirmadas por triangulação antes de qualquer redacção).
Estrutura obrigatória do brief seguida à letra, com 4 blocos separados
na página: quem está abrangido (fronteira de 2006, primeiro que
qualquer regra) → lei aplicável (Estatuto da Aposentação + Lei n.º
60/2005 + Lei n.º 52/2007, por ordem cronológica) → regra de cálculo
(divisão interna por datas — 1 de setembro de 1993 e 1 de janeiro de
2006 decidem qual fórmula se aplica a cada parte da carreira, nunca uma
fórmula única por pessoa; idade de acesso unificada com o regime geral
desde 7 de março de 2014, Lei n.º 83-C/2013) → regras transitórias
(regimes especiais com renúncia obrigatória; escalões de pensão mínima
próprios da CGA, Portaria 480-B/2025/1 art. 5.º, sem valores em euros
publicados, mesma regra do resto do cluster). Questão em aberto
sinalizada, não escondida: a reinscrição na CGA de quem saiu da função
pública depois de 2006 e regressou — a Lei n.º 45/2024 tentou
restringi-la com efeitos retroactivos a 2006, e o Tribunal
Constitucional já a declarou inconstitucional duas vezes (Acórdãos n.os
689/2025 e 325/2026, princípio da protecção da confiança) — matéria
ainda em evolução jurisprudencial, tratada como tal. Decisão sobre
"anel autónomo" (pedida explicitamente pelo brief): CGA publicada como
1 página dentro do Anel 4, proporcional ao universo decrescente de
subscritores — registada em ROADMAP.md a condição para reabrir essa
decisão (regimes especiais ou o litígio da reinscrição aprofundados
numa sessão futura).

**Achado lateral, corrigido antes do commit — dois falsos positivos
reais do canário de datas expiradas** (`scripts/verificar_datas.py`):
`reforma-reino-unido-brexit.html` ("31 de dezembro de 2020", fim do
período de transição) e `caixa-geral-aposentacoes.html` ("1 de janeiro
de 2006", fecho da CGA) disparariam `data_mes_ano` no pipeline real —
confirmado directamente com `detectar_alertas()`, não assumido.
Corrigido em duas frentes: reescritas as ocorrências que usavam "antes
de"/"até"/"relativamente a" para usar "anterior a"/"posterior a"
(marcadores já existentes e seguros), e acrescentados 4 marcadores
novos a `MARCADORES_HISTORICOS` — `período de transição` (Brexit,
evento histórico único, confirmado sem colisão site-wide excepto
`psu-vs-abono-familia.html`, sem data próxima nessa página), `novas
inscrições`/`se inscreveu`/`inscritos a partir de` (fecho da CGA, sem
colisão fora das páginas deste tema), e `regulamento\s*\((?:ce|ue)\)\s*
n\.?[ºo]` — citação de Regulamento europeu pelo formato oficial,
categoria nunca antes citada neste site; confirmado que NÃO colide com
a citação de `renovar-cartao-cidadao.html` ("Regulamento (UE)
2025/1208", sem "n.º" — formato diferente, verificado por grep antes
de aplicar). `detectar_alertas()` reconfirmado a devolver `None` nas 4
páginas novas depois da correcção; `tests/test_verificar_datas.py` (46
testes) sem regressões.

**Achado lateral 2, também corrigido — canário de pesquisa interna**
(2.ª ocorrência do mesmo padrão, já documentado 2× no histórico deste
ficheiro): `tests/test_pesquisa_ranking.py::
test_match_fora_do_titulo_mostra_excerto_destacado` usava "segurança
social" como termo robusto (trocado de "sub" a 2026-09-04) — atingiu o
próprio limite de 8 títulos com a publicação de `pensao-unificada.html`
("Pensão Unificada: CGA e Segurança Social numa só pensão"), o 8.º
título a conter o termo, saturando `MAX_RESULTADOS` só com camada 1.
Trocado para "requerimento" (1 título hoje, 13 descrições/keywords —
margem bem maior), com o histórico completo documentado no comentário
do teste; mesma ressalva já registada nas trocas anteriores: um termo
fixo continua vulnerável ao mesmo crescimento no futuro.

Integração completa das 4 páginas: `data/clusters.json` (edição
cirúrgica de texto, nunca `json.dump()` do ficheiro inteiro — lição já
registada em sessões anteriores sobre reformatação acidental),
`scripts/sincronizar_clusters.py` (regenerou `index.html`
`ATUALIZACOES:HOME`, `p/reformas.html` `PILLAR-LISTA`/`PILLAR-JSONLD`
13→17 itens, `CLUSTER-BADGE`/`RELACIONADOS` das 4 páginas novas — as
já escritas à mão confirmadas idênticas ao que o script geraria antes
da corrida real), `scripts/sincronizar_nav.py`/
`scripts/inserir_botao_partilhar.py`/`scripts/adicionar_canonicas.py`/
`scripts/adicionar_autoria_artigos.py`/`scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO` actualizado; zero alterações às 4 páginas — nav,
canónica, autoria e `Article` JSON-LD já correctos à partida),
`scripts/gerar_og_images.py --write` (4 imagens novas, 1200×630
confirmado pelo cabeçalho JPEG real), `sitemap.xml`,
`scripts/pesquisa.js`. `p/reformas.html`: card "Anel 4" deixou de estar
`Em preparação`, FAQ (visível + JSON-LD) actualizada para deixar de
apontar para "regras ainda por documentar". `fontes.html` ganhou 12
cartões novos (2 Regulamentos europeus, Acordo de Saída, Protocolo TCA,
DL 361/98, DL 437/99, Lei 83-C/2013, Estatuto da Aposentação, Lei
60/2005, Lei 52/2007, DL 286/93, Lei 45/2024, Portaria 480-B/2025/1) —
`tests/test_fontes_coerencia.py` (104 testes) confirmou e exigiu cada
um dos que batem no formato de citação PT (Lei/Decreto-Lei/Portaria);
os Regulamentos europeus e os Acordos internacionais ficam fora dessa
regex por desenho (só reconhece diplomas portugueses), acrescentados
por convenção editorial do site, não por exigência do teste.

Nenhum valor em euros publicado em nenhuma das 4 páginas (regra do
cluster, "nunca um valor que muda todos os anos") — os escalões de
pensão mínima da CGA são descritos estruturalmente (5 escalões por
tempo de serviço, Portaria 480-B/2025/1 art. 5.º), nunca com os
montantes. `tests/test_valores_ancora.py` confirmado sem necessidade de
nova entrada (nenhum €/% em `<title>`/meta description). 4 excepções
novas registadas em `EXCECOES_ANOS_HISTORICOS`
(`tests/test_anos_metadados.py`) para os anos de diplomas/datas
históricas fixas citados em metadados (2004, 2005, 2006, 2020) —
confirmadas a bater certo com o texto real das páginas.
`tests/test_acessibilidade.py` — 0 violações críticas/sérias nas 5
páginas tocadas (as 4 novas + `p/reformas.html`). Suite completa: 4275
passed, 4 skipped antes da correcção dos dois achados laterais;
reconfirmada sem regressões depois (`test_verificar_datas.py`: 46
passed; `test_pesquisa_ranking.py`: 13 passed). `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
designada pelo ambiente remoto desta sessão,
`claude/anel-4-regimes-complementares-5gssae`.

---

*Última revisão: 2026-09-07 — reescrita estrutural correctiva do Anel 4
("regimes complementares", cluster Reformas e Pensões), na sequência de
uma auditoria à entrada de 2026-09-06 acima (preservada tal como foi
escrita, nunca reescrita — a correcção vive só nesta entrada nova,
mesma disciplina do resto do histórico deste ficheiro). A auditoria
encontrou **7 erros estruturais**, não pontuais, em 4 páginas — a
instrução foi reescrever de raiz a partir das fontes primárias, nunca
corrigir frase a frase:

1. **"A totalização nunca aumenta o valor pago por Portugal"** — falso.
   O art. 52.º, n.º 3, do Regulamento (CE) n.º 883/2004 obriga ao
   **mais alto** entre a prestação independente (só lei nacional) e a
   pro rata (totalização); a totalização pode aumentar o que Portugal
   paga, nunca só reduzir.
2. **"Portugal paga sempre a fracção dos anos cá descontados"** —
   mesmo erro, a fórmula pro rata é só um dos dois cálculos possíveis
   (art. 52.º, n.º 1, alíneas a) e b)), nunca automaticamente aplicada.
3. **Cronologia da pensão unificada invertida** — a titularidade
   (a quem/quando é atribuída, incapacidade) sempre seguiu o último
   regime (art. 4.º, n.os 4-5, DL 361/98, nunca alterado); é só o
   **cálculo do valor** que mudou — art. 7.º (regime único pelas regras
   do último regime) foi revogado pela Lei n.º 83-C/2013, o art. 9.º,
   n.º 1, em vigor manda somar as parcelas calculadas separadamente por
   cada regime.
4. **"Metade do excedente"** na pensão unificada — não existe no
   diploma, removido por inteiro, sem inventar garantia de substituição.
5. **"60 meses em cada regime"** — errado; são 60 meses no regime que
   efectivamente atribui a pensão (art. 5.º, n.º 1), nunca
   simultaneamente nos dois.
6. **Taxonomia de "três grupos" de subscritores da CGA** — errado; são
   **duas** categorias, com fronteira a 1 de setembro de 1993 (art. 5.º,
   Lei n.º 60/2005): inscritos até essa data têm pensão em duas
   parcelas (regime CGA até 31/12/2005 + regime geral desde 1/1/2006);
   inscritos a partir de 1/9/1993 têm a pensão inteira pelas regras do
   regime geral, nunca em duas parcelas.
7. **Regra de dispensa "21/20 anos"** atribuída ao Protocolo pós-Brexit
   — errado; pertence ao Anexo VIII do Regulamento (CE) n.º 883/2004
   (UE/EEE/Suíça), movida para `carreiras-contributivas-estrangeiro.html`
   e removida por completo de `reforma-reino-unido-brexit.html`
   (confirmado por grep, zero ocorrências de "21 anos"/"20 anos" nessa
   página).

**Metodologia GRAU 1/2/3, visível no corpo de cada página, nunca só no
ROADMAP**: GRAU 1 = lido directamente na fonte primária (DRE/EUR-Lex);
GRAU 2 = reformulado de fontes secundárias, afirmado como facto mas sem
ser leitura literal do texto oficial; GRAU 3 = questão genuinamente por
confirmar, sinalizada explicitamente, **nunca preenchida por analogia**.
Qualquer hedge de GRAU 2/3 tem de repetir-se em todos os sítios onde o
facto reaparece (FAQ, checklist, resumo) — uma reafirmação sem o hedge
noutro sítio é, por si só, um bug (exactamente o que aconteceu com a
regra 21/20 mal atribuída no rascunho original).

**`carreiras-contributivas-estrangeiro.html`** — reescrita integral:
Regulamento (CE) n.º 883/2004 (art. 2.º âmbito pessoal, art. 3.º/1
âmbito material, art. 52.º os dois cálculos + o mais alto, Anexo VIII
dispensa do cálculo duplo com a excepção 21/20 anos citada ao pormenor
e correctamente atribuída, art. 57.º períodos <1 ano, art. 58.º
complemento até à pensão mínima, Anexos VI/VII); Regulamento (CE) n.º
987/2009 (art. 45.º pedido único, art. 47.º instituição de contacto,
art. 48.º resumo consolidado + direito de revisão, art. 50.º prestação
autónoma sem esperar por outros países); GRAU 2 — extensão a
EEE (Anexo VI do Acordo EEE) e Suíça (Anexo II do Acordo de Livre
Circulação), extensão confirmada como facto, texto exacto da adaptação
não lido.

**`reforma-reino-unido-brexit.html`** — reescrita integral: Acordo de
Saída (art. 30.º critério fixo no fim do período de transição, 31 de
dezembro de 2020, nunca uma história; art. 31.º os Regulamentos
883/2004 e 987/2009 continuam a aplicar-se, os mesmos, não "similares");
Protocolo TCA (arts. 488.º-490.º âmbito, art. 779.º sobrevive à
denúncia geral do Acordo). Card GRAU 3 explícito: por confirmar se o
Protocolo tem equivalente ao art. 52.º, n.º 3 (direito ao valor mais
alto) ou ao Anexo VIII (dispensa do cálculo duplo) do Regulamento
883/2004 — nunca preenchido por analogia.

**`pensao-unificada.html`** — reescrita integral: DL 361/98 (arts. 1.º/
2.º âmbito, art. 4.º totalização + titularidade sempre pelo último
regime, art. 5.º mínimo de 60 meses no regime que atribui, art. 6.º
pedido nunca automático, arts. 7.º/9.º história do cálculo do valor,
art. 18.º recurso ao primeiro regime se não houver direito à unificada,
art. 30.º revoga DL 159/92 e Portaria 2/93, nunca a Portaria 642/83).

**`caixa-geral-aposentacoes.html`** — reescrita integral: Lei n.º
60/2005 (art. 2.º fecho a novas inscrições desde 1/1/2006, art. 5.º as
duas categorias com fronteira em 1/9/1993 e as duas fórmulas, art. 3.º
+ Anexo I idade de acesso progressiva, art. 4.º + Anexo II tempo de
serviço progressivo, art. 7.º salvaguarda 36 anos+60 anos a 31/12/2005
independente de quando a aposentação é requerida, art. 6.º
sobrevivência, art. 8.º corte de 4,5%/ano na aposentação compulsiva).
Card "O que não foi lido" — o Estatuto da Aposentação nunca foi lido
por inteiro, só o que a Lei n.º 60/2005 cita directamente pode ser
afirmado; removida por completo a alegação sem fonte "5 anos de
serviço, ou 3 anos em incapacidade" (não encontrada na Lei n.º 60/2005).

**Falsos positivos do canário de datas expiradas, corrigidos de novo**
(a reescrita integral introduziu texto novo, por isso precisou de nova
verificação — não é o mesmo trabalho já documentado na entrada
anterior, que cobria o rascunho original): confirmado com
`detectar_alertas()` real, executado directamente (nunca só inspecção
visual), contra as 4 páginas nos 4 meses de revisão (1/7/8/9) e nos
anos 2026/2027 — 11 ocorrências corrigidas ao todo (6 em
`reforma-reino-unido-brexit.html`, 5 em
`caixa-geral-aposentacoes.html`), sempre reescrevendo a prosa em torno
para trazer um marcador já existente (`período de transição`, `novas
inscrições`, `lei n.º`) para dentro da janela de 220 caracteres —
nunca inventando marcadores novos em `scripts/verificar_datas.py`.
Confirmado depois: zero alertas inesperados; o único disparo
remanescente é o desejado (carimbo "Verificado a 7 de setembro de
2026" a envelhecer para 2027).

Integração completa: `data/clusters.json` (edição cirúrgica de texto),
`scripts/sincronizar_clusters.py` (regenerou `index.html`
`ATUALIZACOES:HOME` e `p/reformas.html` `PILLAR-LISTA`/`PILLAR-JSONLD`
— idempotência confirmada, zero alterações às 4 páginas em qualquer
corrida dos scripts de sincronização), `scripts/sincronizar_nav.py`/
`scripts/inserir_botao_partilhar.py`/`scripts/adicionar_canonicas.py`/
`scripts/adicionar_autoria_artigos.py`/`scripts/adicionar_article_jsonld.py`
(`DATAS_PUBLICACAO` = 2026-09-07), `scripts/gerar_og_images.py --write`
(2 imagens regeneradas — só as páginas cujo título mudou), `sitemap.xml`,
`scripts/pesquisa.js` (keywords reescritas para reflectir o conteúdo
corrigido: "pro rata", "21 20", "regulamento 883/2004", "montante mais
alto", "soma das parcelas", "1993"). `p/reformas.html` — as 3
mini-descrições do card "Anel 4" (hand-authored, fora do
`PILLAR-LISTA` automático) reescritas para deixar de repetir os erros
#1/#3/#6. `fontes.html` — 12 cartões revistos com as descrições
correctas, mais um cartão novo para o Decreto-Lei n.º 35/2002 (citado
pela primeira vez nesta reescrita). 5 excepções novas/mantidas em
`tests/test_anos_metadados.py::EXCECOES_ANOS_HISTORICOS` (2004, 2005,
2006, 1993, 2020 — todas número de diploma ou data histórica fixa,
nunca uma data de vigência a esquecer), confirmadas contra o texto real
das páginas.

Nenhum valor em euros em nenhuma das 4 páginas (regra do cluster) —
todos os valores expressos em múltiplos do IAS ou por remissão à
Segurança Social Direta. Registado em `ROADMAP.md` → "TRABALHO FUTURO
REGISTADO": Estatuto da Aposentação (nunca lido por inteiro), texto
oficial do Protocolo SSC do TCA (nunca lido), Anexo VI do Acordo EEE/
Anexo II do Acordo Suíça (nunca lidos em fonte oficial) — os 3 pontos
GRAU 2/3 desta sessão, cada um com a justificação completa.

**Suite completa**: `python3 -m pytest tests/ -q` — **4363 passed, 4
skipped** em 608,47s (10m08s), zero falhas; os 4 skips confirmados os
mesmos 4 estruturais de sempre. `ruff check scripts/ tests/ --select
E,F,W --ignore E501 .` limpo. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Trabalho feito na branch
`claude/anel-4-regimes-complementares-5gssae` (a mesma da entrada
anterior, nomeada explicitamente pelo pedido desta sessão) — **SEM
PR — branch não integrada em `main`** (instrução explícita desta
sessão: não abrir PR).

---

*Última revisão: 2026-09-07 — novo `simulador-condicoes-reforma.html`,
8.º simulador do site e 1.ª ferramenta do cluster `reformas` (fecha-o,
per o brief da sessão). Recebidos nesta sessão dois ficheiros já
pré-verificados pelo Nuno: `pensoes-lei.yml` (parâmetros estruturais do
regime de invalidez/velhice, DL 187/2007, com citação de artigo e
metadados de verificação directa no DRE a 2026-09-04) e um brief
completo do simulador. Nenhum WebSearch/WebFetch foi necessário — os
valores vieram directamente da fonte já verificada fornecida à sessão,
mesmo padrão de outras sessões que receberam pacotes pré-fact-checked
do Nuno.

**Diferença de género face aos 8 simuladores anteriores**: este não
calcula nenhum valor em euros — responde só a «já posso reformar-me, e
por que via?» (condições de acesso). Nunca pede a idade normal de
reforma nem o factor de sustentabilidade como input — nenhum dos dois
é condição de acesso (a idade normal muda todos os anos por portaria e
não é modelada; o factor de sustentabilidade só entra no output, como
informação qualitativa por via, nunca como cálculo) — por isso o
simulador continua exacto sem edição, em qualquer ano.

`dados/parametros/pensoes.yaml` — novo, 11 parâmetros, âmbito
deliberadamente restrito ao que o simulador consome (prazo de garantia
de 15 anos, as duas vias de carreiras muito longas — 60+48 e 60+46 com
início antes dos 17 —, flexibilização 60+40, redução de 4 meses/ano da
idade pessoal com piso de 60 anos, e o prazo de 3 anos de proibição de
regresso à mesma empresa) — nunca a idade normal nem o factor de
sustentabilidade, que não são limiares fixados no diploma. Todos os 11
parâmetros com `referencia_legal`/`fonte_url` (a versão consolidada do
DRE já citada em `p/reformas.html`) e `verificado_em: "2026-09-04"` (a
data real da verificação no ficheiro fornecido, não a data desta
sessão) — `vigencia_inicio: "2021-02-25"` uniforme (a data da
republicação onde a redacção actual foi confirmada), já que são
limiares absolutos, nunca revistos por portaria.

**Lógica implementada exactamente como desenhada no brief** — avaliação
em cascata (prazo de garantia → carreiras muito longas → flexibilização
→ idade pessoal informativa → "quanto falta" só quando nada se aplica),
**mostrando sempre todas as vias em que a pessoa cabe**, nunca só a
primeira. O serviço militar (art. 48.º) é tratado como o brief exigia —
nunca a pergunta «fez tropa?», mas «cumpriste serviço militar em
período sem descontos?», com um campo condicional de duração em meses;
o simulador compara o resultado com e sem esse tempo e assinala
`dependeServicoMilitar` quando ele é decisivo, avisando que só conta
mediante requerimento próprio. Os 5 casos-limite obrigatórios do brief
(fronteira dos 17 anos — `< 17`, nunca `<= 17`; serviço militar
decisivo; piso dos 60 anos na idade pessoal, com as duas informações
sempre juntas; prazo de garantia não cumprido; elegibilidade
simultânea por carreiras muito longas e flexibilização) foram escritos
como testes ANTES de qualquer ajuste ao código e **passaram à primeira
tentativa** — nenhuma correcção de lógica foi necessária depois de
escritos.

Estrutura da página: card de âmbito ("vai buscar os teus anos à SSD,
não os estimes"), formulário (mês+ano de nascimento — nunca o dia, "o
dia não é preciso" — anos de carreira, idade de início opcional,
serviço militar, mesma empresa), resultado com um `via-card` por via
disponível (tabela de consequências: factor de sustentabilidade/factor
de redução/mínimo garantido), bloco informativo de idade pessoal
(redução relativa + piso, nunca um valor absoluto), bloco "quanto
falta" quando não há nenhuma via ainda, e um card fixo e sempre visível
sobre as antecipações NÃO cobertas (desemprego de longa duração — art.
24.º — e profissão desgastante — art. 22.º — nenhuma das duas isenta
do factor de sustentabilidade, ao contrário das vias que este
simulador cobre). Mesmo padrão arquitectural dos simuladores recentes:
`fetch('/dados/parametros.json')` em runtime, botão nasce `disabled`
até carregar com sucesso, `validarInputCondicoesReforma()` nunca
converte vazio/inválido em 0 silenciosamente, função pura
`calcularCondicoesReforma()` nunca toca no DOM.

Integração: `data/clusters.json` (`simulador-condicoes-reforma.html`,
tipo `ferramenta`, cluster `reformas`); `scripts/sincronizar_clusters.py`
corrido com sucesso — actualizou `index.html` (`ATUALIZACOES:HOME`) e
`p/reformas.html` (`PILLAR-LISTA`/`PILLAR-JSONLD`, 20→21 itens, badge
"Ferramenta"); `sincronizar_nav.py`/`inserir_botao_partilhar.py`/
`adicionar_canonicas.py`/`adicionar_autoria_artigos.py`/
`adicionar_article_jsonld.py` confirmados a **zero alterações** — a
página já nasceu com nav, botão de partilha, canónica, autoria e
`Article` JSON-LD correctos. `scripts/gerar_og_images.py --write` gerou
a imagem própria. `p/reformas.html` ganhou também um 5.º mini-card
manual no Anel 1 (fora do `PILLAR-LISTA` automático, mesmo padrão já
usado nos outros clusters para dar visibilidade extra a um simulador
dentro do "guia" mais relevante). `simuladores.html` (hub — 9.º card,
`hasPart` JSON-LD, "Oito"→"Nove" no `<h1>`/description/og/parágrafo de
fecho) e a secção "Simuladores e Calculadoras" do `index.html` (9.º
cartão) actualizados. `sitemap.xml` e `scripts/pesquisa.js`
actualizados. `scripts/gerar_base_dados.py` corrido para reflectir os
11 parâmetros novos em `dados/tensdireito.db` (Dados Abertos).

Testes: `tests/test_simulador_condicoes_reforma_calculo.py`, novo, 31
casos — os 5 casos-limite obrigatórios do brief, canário dos 11
limiares de produção contra `dados/parametros.json`, cálculo de idade
em anos/meses completos (nunca o dia), "quanto falta", aviso "mesma
empresa" (só com via disponível), e validação de input completa
(obrigatórios, formatos, decimais rejeitados, campo condicional do
serviço militar). Nenhuma entrada nova necessária em
`tests/test_valores_ancora.py`/`tests/test_anos_metadados.py` — a
página não usa nenhum valor em €/% nem ano civil anterior ao corrente
em `<title>`/meta description (confirmado a passar sem excepção).
`tests/test_acessibilidade.py` — 0 violações críticas/sérias nas 4
páginas tocadas (`simulador-condicoes-reforma.html`, `p/reformas.html`,
`simuladores.html`, `index.html`). `tests/test_eventos_ga4.py`
reconfirmado sem regressões (evento `simulacao_concluida` com
`elegivel` = prazo de garantia cumprido).

Suite completa: `python3 -m pytest tests/ -q` — **4422 passed, 4
skipped** em 646,96s (10m46s), zero falhas; guardrail de skips
(`scripts/verificar_skips_permitidos.py`) confirma os 4 skips reais a
bater certo, elemento a elemento, com a allow-list — nenhum skip novo.
`ruff check scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/new-session-t59zm0` (designada pelo ambiente remoto desta
sessão).

---

*Última revisão: 2026-09-07 (issue #170) — falso positivo do canário de
datas expiradas em `fontes.html` ("Data com mês e ano", mês 9/2026).
Investigação: listadas as 14 ocorrências reais de "mês de ano" da página
mais as ~90 ocorrências de ano isolado — todas são citações de diploma
(data de publicação, número de lei/decreto-lei/portaria) ou datas-limite
substantivas fixadas pela própria lei; `fontes.html` não tem nenhum
carimbo "Verificado a"/data de última consulta (confirmado por grep —
é uma página institucional de lista de fontes, sem esse campo), por
isso **nenhuma** categoria (a) existe nesta página para actualizar.

O match concreto a disparar era "31 de dezembro de 2005" no card da
Lei n.º 60/2005 — "a salvaguarda de 36 anos de serviço + 60 de idade a
31 de dezembro de 2005 (art. 7.º)", uma data-limite de uma cláusula de
salvaguarda transitória da Caixa Geral de Aposentações. Confirmado como
falso positivo genuíno, mesma família das fronteiras da CGA já cobertas
por `MARCADORES_HISTORICOS` ("novas inscrições"/"se inscreveu"/"inscritos
a partir de", 2026-09-06) — o mesmo facto já estava correctamente
suprimido em `caixa-geral-aposentacoes.html` (onde "Lei n.º 60/2005"/"se
inscreveu" caem dentro da janela de 220 caracteres), mas o parágrafo de
`fontes.html` é longo o suficiente para o H2 "Lei n.º 60/2005" ficar fora
da janela desta ocorrência específica. Uma cláusula de salvaguarda é, por
definição, um requisito fixado a uma data histórica que nunca volta a
mudar — nunca "expira".

Corrigido no detector, nunca no conteúdo: novo marcador `\bsalvaguarda\b`
em `MARCADORES_HISTORICOS` (`scripts/verificar_datas.py`) — confirmado
por grep ao repositório inteiro antes de aplicar (só 2 ficheiros usam a
palavra: `caixa-geral-aposentacoes.html`, já suprimida por outros
marcadores, e `reforma-reino-unido-brexit.html`, sem nenhuma data de
mês+ano nas proximidades — zero risco de mascarar um prazo real). 3
testes novos em `tests/test_verificar_datas.py`: `fontes.html` real sem
alerta nos 4 meses de revisão (1/7/8/9), o marcador a suprimir
correctamente uma citação sintética da mesma cláusula, e uma guarda
anti-sobre-supressão (uma data antiga genuína sem a palavra "salvaguarda"
por perto continua a alertar normalmente).

**Nenhum conteúdo de `fontes.html` foi alterado** — todas as ~30
citações de diploma/portaria da página (datas de publicação, valores
substantivos como o limite de 0,35×IAS da Garantia para a Infância, os
limiares do IMT Jovem, os artigos do DL n.º 322/90/187/2007/361/98,
etc.) são categoria (b) e ficam por confirmar directamente no DRE numa
sessão dedicada — nenhuma delas apresentava indício de estar
substantivamente errada, só a data-limite histórica que disparou o
detector. Suite completa: `python3 -m pytest tests/ -q` — **4425
passed, 4 skipped** (671s), zero falhas, os mesmos 4 skips estruturais
de sempre (3 testes novos face à baseline anterior de 4422); `ruff
check scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados). Trabalho feito na branch
`claude/issue-170-fontes-datas-txy53c` (designada pelo ambiente remoto
desta sessão) — PR aberto, referenciando "Closes #170", sem merge para
`main`.

---

*Última revisão: 2026-09-07 (continuação) — sessão de correcção pontual a
`fontes.html`, começando exactamente onde a entrada anterior tinha
parado: 6 cartões corrigidos/completados no cluster Reformas e no
cluster Habitação. `WebFetch`/`curl` confirmados bloqueados nesta sessão
para todos os domínios testados (`diariodarepublica.pt`, `www.cga.pt`) —
mesma limitação de sempre; as duas confirmações pedidas explicitamente
antes de publicar foram feitas por triangulação `WebSearch` (nunca
leitura directa no DRE):

1) **Decreto-Lei n.º 79/2019, de 14 de junho** — confirmado por 4 fontes
independentes (dre.pt indexado, cga.pt, SPGL, homepagejuridica.pt),
Diário da República n.º 113/2019, Série I. 2) **Lei n.º 73-A/2025 =
OE2026 com actualização de 2% dos escalões de IMT** — confirmado por 8
fontes profissionais/financeiras independentes (OCC, EY, Doutor
Finanças, PwC, Crowe, Apcmc, Macedo Vitorino, RFF Lawyers), valores
330.539€/660.982€ batem certo com os já publicados em `imt-jovem.html`.

Correcções aplicadas: **DL 18/2023** ganhou a data (3 de março, DR n.º
45/2023, Série I, pp. 40-43 — confirmado pelo próprio nome do ficheiro
PDF em files.dre.pt, "0004000043" = páginas 40-43) e a frase errada
"condições reguladas por diploma próprio ainda não verificado" foi
substituída pela relação real: o regime foi criado pela **Lei n.º
5/2022, de 7 de janeiro** (novo cartão, idade ≥60 anos/incapacidade
≥80%/15 anos de carreira), e o DL 18/2023 é a sua regulamentação, mais
de um ano depois. **DL 79/2019** ganhou a data confirmada. **DL 97/2026**
— a nota "com efeitos desde 1 de setembro de 2026" estava mal atribuída
a tudo; reescrita para distinguir as três datas reais (dedução de rendas
aos rendimentos de 2026; IVA a 6% desde 1 de julho de 2026; regimes CIA
— Contratos de Investimento para Arrendamento, facto novo, nunca antes
citado no site — e RSAA desde 1 de setembro de 2026); acrescentada a lei
de autorização, **Lei n.º 9-A/2026, de 6 de março** (novo cartão, link
para o PDF real em files.diariodarepublica.pt). **DL 44/2024** (garantia
pública) ganhou a nota do prazo-limite (contratos celebrados até 31 de
dezembro de 2026, com possibilidade de prorrogação) — facto já publicado
e verificado em `garantia-publica-credito-habitacao.html`, só importado
para fontes.html; a data foi registada em `ROADMAP.md` → "DATAS FIXAS"
(vigilância explícita, cruzada com o sentinela `dre_habitacao_garantia`).
**DL 48-A/2024** (IMT Jovem) corrigido — os valores de 2026 (330.539€/
660.982€) vêm da Lei n.º 73-A/2025, nunca deste diploma; **novo cartão
para a Lei n.º 73-A/2025** (resolve, de caminho, uma excepção já aberta
em `EXCECOES_DIPLOMAS_FONTES` desde o levantamento de 30/08/2026 —
removida de `tests/test_fontes_coerencia.py`, critério de "resolvido"
cumprido). Ressalva Açores/Madeira acrescentada com nota de estatuto de
fonte ("sujeita a confirmação directa no DRE") — usado o valor **826.228€**
já publicado e investigado em `imt-jovem.html` (arredondamento das
tabelas práticas da AT), não os "826.227€" do pedido original, que
correspondem à divergência de arredondamento já resolvida numa sessão
anterior (2026-07-20); reportado aqui para nunca se repetir a confusão.

**Falso positivo apanhado antes do commit, não depois**: o texto
"contratos de crédito formalizados até 31 de dezembro de 2026" (1.ª
versão da correcção do DL 44/2024) disparava `data_mes_ano` em
`verificar_datas.py` a partir de janeiro de 2027 — "formalizados até"
não bate com nenhum marcador de `MARCADORES_HISTORICOS`. Corrigido
reescrevendo para "celebrados até", reutilizando o marcador já existente
`celebrados?\s+at[ée]\b` (mesma família das Issues #51/#52) — nunca
inventado marcador novo para um caso que a vocabulário já cobre.
Confirmado com `detectar_alertas()` real sobre os 12 meses × 2026-2028:
zero alertas depois da correcção.

Regra aplicada uniformemente: qualquer facto novo/corrigido nesta sessão
que não foi lido directamente no DRE (bloqueado) ganhou a nota "Triangulado
por fontes secundárias independentes — acesso directo a
diariodarepublica.pt bloqueado nesta sessão", mesmo padrão já usado nos
cartões da Lei n.º 7/2001 e do Estatuto da Aposentação.

**Fora do âmbito desta sessão, sinalizado e não corrigido**: a nova
redacção do cartão do DL 18/2023 em `fontes.html` diverge agora de
`outras-antecipacoes.html`, que continua a descrever a via de
antecipação por deficiência como dependente de "regulamentação própria,
que ainda não verificámos" (JSON-LD e texto visível, 3 ocorrências) — a
tarefa desta sessão foi explicitamente scoped a `fontes.html`; corrigir
esse artigo fica registado para uma sessão dedicada.

Suite completa: `python3 -m pytest tests/ -q` — **4427 passed, 4
skipped** (601s), zero falhas, os mesmos 4 skips estruturais de sempre
(confirmados elemento a elemento contra `tests/skips_permitidos.json`);
`ruff check scripts/ tests/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados). Trabalho feito na branch
`claude/corrigir-fontes-html-otwjr9` (designada pelo ambiente remoto
desta sessão) — PR aberto contra `main`, sem merge.

---

*Última revisão: 2026-09-08 (continuação, mesmo PR #174) — corrigida uma
inconsistência real face à "regra aplicada uniformemente" da entrada
anterior: o cartão da **Lei n.º 73-A/2025** em `fontes.html`, apesar de
confirmado só por triangulação (nunca leitura directa no DRE, exactamente
como o DL 79/2019), tinha ficado sem a nota de estatuto de fonte —
corrigido, acrescentada a mesma frase já usada no cartão do DL 79/2019
("Triangulado por fontes secundárias independentes — acesso directo a
diariodarepublica.pt bloqueado nesta sessão."). Citação do DL 79/2019
também upgradada de "Publicado no Diário da República n.º 113/2019,
Série I." para a coordenada completa "..., de 2019-06-14" — confirmado
por `verificar_datas.detectar_alertas()` (2026-2028, todos os meses) que
o novo formato ISO não introduz nenhum falso positivo (o padrão
`data_numerica` exige barras `DD/MM/AAAA`, nunca hífens).

**Novo achado, registado em CLAUDE.md → "FONTES VERIFICADAS E APROVADAS"**:
as páginas `diariodarepublica.pt/dr/detalhe/...` são uma SPA que exige
JavaScript para renderizar o texto do diploma — nunca legíveis por um
fetch simples, mesmo quando o domínio não está bloqueado. `files.dre.pt`
(PDF estático da própria série do DR, já usado nalguns cartões deste
ficheiro) é o canal a preferir daqui para a frente. **Honestidade sobre
o que esta sessão confirmou**: tentado `WebFetch` real a um URL
`files.dre.pt` já em uso no site e a um URL `dr/detalhe/` (DL 79/2019) —
os dois devolveram `EGRESS_BLOCKED` desta sessão, o mesmo bloqueio total
de rede já documentado para dezenas de domínios — por isso esta sessão
não confirmou por si própria a diferença de acessibilidade entre os
dois; a recomendação fica registada para ser testada num ambiente com
rede real (ex.: runner do GitHub Actions) antes de se assumir resolvida
por completo.

**Issue separada aberta, fora do âmbito deste PR** — [#175](https://github.com/nunovinhas-creator/tens-direito/issues/175):
`imt-jovem.html` afirma o mesmo facto da Lei n.º 73-A/2025 (+2% nos
escalões de IMT, limiares 330.539€/660.982€) desde 2026-07-20, também
só por triangulação, mas sem nenhuma nota de estatuto de fonte — nunca
corrigido nesta sessão, por estar fora do âmbito ("corrigir
`fontes.html`"); fica registado para uma sessão dedicada, que deve
também confirmar `dados/parametros/habitacao.yaml`.

`tests/test_fontes_coerencia.py` (108 passed) e
`tests/test_verificar_datas.py` (51 passed) reconfirmados sem
regressões; suite completa + `ruff` corridos de novo antes do commit
final. `AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA`
reconfirmados `False` (inalterados). Mesma branch
`claude/corrigir-fontes-html-otwjr9`, mesmo PR #174, sem merge.

---

*Última revisão: 2026-09-08 (continuação, mesmo PR #174) — corrigida a
ressalva desta entrada sobre `files.dre.pt`, com uma verificação primária
feita fora desta sessão: o PDF integral do Decreto-Lei n.º 18/2023 foi
lido por inteiro em fonte primária. `files.dre.pt` está confirmado
acessível — o `EGRESS_BLOCKED` que as tentativas de `WebFetch`/`curl`
desta e de outras sessões continuam a devolver é uma limitação da rede
do sandbox onde o Code corre, nunca prova de que o domínio ou o método
(PDF estático vs. SPA) estão indisponíveis; corrigido em
"FONTES VERIFICADAS E APROVADAS" → "Verificação directa de diplomas",
substituindo a ressalva "esta sessão não confirmou... antes de se
assumir como garantidamente resolvido" pelo facto confirmado e por uma
**regra permanente, nova**: a verificação primária de um diploma no DRE
nunca é feita pelo Code a partir desta sessão — é sempre feita fora
(pelo Nuno, ou por outro processo com acesso real à rede) e entregue ao
Code já como facto confirmado, com o artigo citado ao pormenor; o Code
nunca reconstrói nem infere o que já lhe foi entregue verificado, só o
transcreve fielmente, com a atribuição GRAU 1 correcta.

Cartão do Decreto-Lei n.º 18/2023 em `fontes.html` actualizado com os
factos que essa leitura primária deu, nenhum deles disponível antes: é a
**11.ª alteração** ao Decreto-Lei n.º 187/2007 e a **50.ª** ao Estatuto
da Aposentação (art. 40.º do Decreto-Lei n.º 498/72); o **artigo 5.º**
afasta desta via a redução por penalizações de antecipação e o factor de
sustentabilidade; o **artigo 6.º** proíbe a acumulação com actividade
profissional a qualquer título, com perda do direito enquanto essa
acumulação durar; e o **artigo 1.º** confirma directamente que o diploma
regulamenta a Lei n.º 5/2022 — removido o resto da frase "condições
reguladas por diploma próprio ainda não verificado", que já tinha sido
corrigida na entrada anterior deste PR mas cuja causa (a relação exacta
entre os dois diplomas) só ficou confirmada por leitura directa agora. A
nota "Triangulado por fontes secundárias independentes" deu lugar a
"Lido por inteiro em fonte primária (PDF, files.dre.pt)" — cartão passa
de GRAU 2 a GRAU 1. A data (3 de março, DR n.º 45/2023) e o link para
`diariodarepublica.pt/dr/detalhe/...` já estavam correctos desde a
entrada anterior deste PR — nenhum dos dois foi tocado.

**Continua fora do âmbito, sinalizado de novo**: `outras-antecipacoes.html`
mantém-se sem alteração (a tarefa desta sessão foi explicitamente scoped
a `fontes.html`) — a divergência já registada na entrada anterior deste
PR fica agora mais acentuada: essa página descreve a via de antecipação
por deficiência com o badge "Por verificar"/GRAU 3 ("regulamentação
própria, que ainda não verificámos", JSON-LD e texto visível, 3
ocorrências), enquanto `fontes.html` já está em GRAU 1 para o mesmo
diploma. Corrigir esse artigo continua registado para uma sessão
dedicada.

Suite completa: `python3 -m pytest tests/ -q --junitxml=...` — **4427
passed, 4 skipped** (672,85s/11m13s), zero falhas; guardrail de skips
(`scripts/verificar_skips_permitidos.py`) confirmado a bater certo,
elemento a elemento, com os mesmos 4 skips estruturais da allow-list
(`tests/skips_permitidos.json`, inalterada); `ruff check scripts/
tests/ --select E,F,W --ignore E501 .` limpo; `tests/test_fontes_
coerencia.py`/`test_verificar_datas.py`/`test_anos_metadados.py`/
`test_valores_ancora.py` (377 testes) reconfirmados sem regressões
antes da suite completa. `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Mesma branch `claude/corrigir-fontes-html-otwjr9`,
mesmo PR #174, sem merge.

---

*Última revisão: 2026-09-08 (continuação, mesmo PR #174) — resultado da
verificação primária da **Lei n.º 73-A/2025** (a única, das duas
confirmações pedidas na sessão anterior deste PR, que voltou a ser
posta à prova): fecho **parcial**, não total — o diploma confirma-se em
GRAU 1, os valores que ele fixaria continuam GRAU 2 (Issue #175 mantida
aberta com essa distinção, ver abaixo).

Cartão em `fontes.html` reescrito para separar as duas coisas, nunca
misturadas como estavam: **confirmado** — é mesmo a Lei do Orçamento do
Estado para 2026, publicada no Diário da República n.º 250, Suplemento,
1.ª série, lida em fonte primária (PDF, files.diariodarepublica.pt);
**por confirmar** — os limiares concretos do IMT Jovem para 2026
(330.539€/660.982€, face a 324.058€/648.022€ em 2025) atribuídos à
actualização de 2% dos escalões gerais de IMT por esta lei mantêm-se
triangulados por fontes secundárias independentes, com a mesma nota de
estatuto de fonte de sempre — a leitura primária confirmou a
identidade do diploma, não o articulado que fixa esses números.
`Decreto-Lei n.º 79/2019` **intocado** nesta correcção — mantém a
coordenada (DR n.º 113/2019, Série I) e a nota de triangulação, por não
ter sido posto à prova.

**Issue #175 actualizada, não fechada**: o comentário registado deixa
explícito que a lacuna original ("`imt-jovem.html` cita a Lei n.º
73-A/2025 sem nota de estatuto de fonte") **não está resolvida** por
esta verificação — só o diploma em `fontes.html` mudou de GRAU; os
valores continuam por confirmar directamente no articulado, tanto em
`fontes.html` como em `imt-jovem.html`/`dados/parametros/habitacao.yaml`
(os dois pontos que a Issue já listava). Fechar a Issue por completo
continua a exigir ler o articulado da lei (não só a 1.ª página/ementa)
e confirmar os valores concretos dos escalões de IMT — trabalho ainda
não feito.

Verificado antes do commit: `tests/test_fontes_coerencia.py`/
`test_verificar_datas.py`/`test_anos_metadados.py`/
`test_valores_ancora.py` (377 testes) sem regressões; `ruff check
scripts/ tests/ --select E,F,W --ignore E501 .` limpo; suite completa —
**4427 passed, 4 skipped** (689s/11m28s), zero falhas, guardrail de
skips confirmado a bater certo, elemento a elemento, com a allow-list.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados). Mesma branch `claude/corrigir-fontes-html-otwjr9`,
mesmo PR #174, sem merge.

---

*Última revisão: 2026-09-08 (sessão separada, branch própria) — precisão
ao cartão da Garantia Pública em `fontes.html`, sobre o prazo-limite já
conhecido (31 de dezembro de 2026). As duas correcções foram aplicadas
ao cartão da **Portaria n.º 236-A/2024/1** — a fonte concreta desta
cláusula, não o Decreto-Lei n.º 44/2024 em si (esse cartão, que já
mencionava o prazo de forma mais genérica, ficou intocado): 1) citação
literal da cláusula de vigência do protocolo — "até 31 de dezembro de
2026, 'ou outra data que posteriormente corresponder ao termo de uma
eventual prorrogação'" — em vez da formulação vaga já existente ("a lei
prevê a possibilidade de prorrogação"); 2) precisão nova, nunca antes
publicada no site: o que conta para este prazo é sempre a data da
escritura e do contrato de crédito, nunca a do CPCV nem a do início do
processo de compra.

**Achado durante a verificação, corrigido antes do commit**: a 1.ª
versão da frase introduzia um falso positivo real no canário de datas
expiradas — confirmado com `verificar_datas.detectar_alertas()`, nunca
assumido. O h2 "Portaria n.º 236-A/2024/1" ficava a 256 caracteres da
nova ocorrência "dezembro de 2026", fora da janela de 220 caracteres de
`_esta_suprimido()` — disparava `data_mes_ano` a partir de 2027, mesma
classe de bug já documentada para a Issue #170 (parágrafos longos
empurram o marcador de supressão para fora da janela). Corrigido
reformulando a frase para trazer "celebrados até" (marcador já existente
em `MARCADORES_HISTORICOS`, `celebrados?\s+at[ée]\b`) para junto da
própria data — nunca um marcador novo, reaproveitando o vocabulário já
coberto (mesma disciplina já registada nesta secção para casos
análogos). Confirmado depois: zero alertas nos 3 anos testados
(2026/2027/2028), nos 4 meses de revisão (1/7/8/9).

`ROADMAP.md` → "DATAS FIXAS" (a entrada de 31 de dezembro de 2026 já
existia desde 2026-07-20) actualizada com a mesma precisão — base legal
correcta (Portaria n.º 236-A/2024/1, não só "a lei"), a distinção
escritura/contrato vs. CPCV/início do processo, e uma nota nova: a
decisão sobre prorrogação só deve surgir com a proposta de Orçamento do
Estado para 2027, esperada em outubro de 2026 — nunca antes disso, para
não gerar expectativa de novidade prematura numa próxima sessão que
reveja este gatilho.

Nenhuma outra página tocada — `garantia-publica-credito-habitacao.html`
e `dados/parametros/habitacao.yaml` ficam fora do âmbito desta sessão
(tarefa explicitamente scoped a "cartão da garantia pública em
fontes.html").

**Issue separada aberta, por instrução explícita — nunca implementada**:
indício, de fonte secundária e por confirmar, de novas regras de taxa de
esforço/prazos máximos no crédito à habitação desde 1 de agosto de 2026,
também aplicáveis a jovens até 35 anos — se confirmado, afecta todo o
cluster Habitação sobre crédito (Garantia Pública, IMT Jovem), não só a
Garantia Pública. [Issue #178](https://github.com/nunovinhas-creator/tens-direito/issues/178)
(label `verificar`, prioridade alta assinalada no título) — nada
implementado, nenhuma página tocada por esse indício.

Suite completa: **4431 passed, 4 skipped** (629,83s/10m30s), zero
falhas; guardrail de skips (`scripts/verificar_skips_permitidos.py`)
confirmado a bater certo, elemento a elemento, com os mesmos 4 skips
estruturais da allow-list (`tests/skips_permitidos.json`, inalterada);
`ruff check scripts/ tests/ --select E,F,W --ignore E501 .` limpo
(nenhum `.py` alterado nesta sessão). `AUTO_UPDATE_HABILITADO`/
`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados `False` (inalterados —
sessão sem scraper). Trabalho feito na branch
`claude/garantia-publica-data-limite-8rgwds` (designada pelo ambiente
remoto desta sessão) — PR novo, sem merge.

---

*Última revisão: 2026-09-08 (fecho da Issue #177) — corrigida a
justificação, desactualizada desde o PR #176, de `simulador-imt-jovem.html`
continuar limitado ao Continente. **Decisão: mantém-se assim** — mas por
opção deliberada de âmbito, nunca por falta de dados. A razão original
citada nos 4 sítios do simulador ("as parcelas a abater da tabela geral
RA não foram confirmadas de forma conclusiva") deixou de ser verdadeira
com o PR #176 (2026-09-08, mesmo dia): `dados/parametros/habitacao.yaml`
tem hoje a tabela geral de IMT (HPP) das Regiões Autónomas por inteiro
(`imt_geral_hpp_ra_*`, 8 parâmetros), verificada contra o folheto
oficial da AT "Os meus direitos e deveres na aquisição de um prédio"
(janeiro 2026, Ofício Circulado n.º 40129/2026), com testes-canário
próprios em `tests/test_valores_ancora.py` — a lacuna de dados que
justificava a exclusão já não existe.

Reescritos os 4 sítios listados na Issue #177 — `#avisoRegiao` (aviso
visível no formulário), FAQ "Este simulador serve para os Açores e a
Madeira?" (visível + `FAQPage` JSON-LD), o comentário JS que documenta
`PARAMETROS_IMT_JOVEM`, e a nota da lista de limitações ("Não inclui...")
— para deixar claro que (1) é uma decisão deliberada de âmbito, para
manter o formulário simples com um único conjunto de escalões, sem
selector de região; (2) o resultado do simulador **não se aplica** ao
caso de quem compra nos Açores ou na Madeira (os limites lá são 25%
mais altos); e (3) para onde ir em vez disso — a nota sobre as Regiões
Autónomas no guia do IMT Jovem, a tabela completa nos Dados Abertos do
site (onde a tabela RA já vive, verificada), ou confirmar o valor exacto
na Autoridade Tributária. Docstring de
`tests/test_simulador_imt_jovem_calculo.py` actualizada a par, com a
mesma correcção (Issue #177/PR #176 citados directamente, em vez da
alegação "parcelas não confirmadas"). Nota nova em CLAUDE.md → "CLUSTER
HABITAÇÃO" regista a mesma decisão, para nunca se voltar a assumir que a
exclusão é por falta de dados: os parâmetros RA existem e estão
verificados; a não utilização no simulador é deliberada — estender o
simulador às RA fica registado como possível trabalho futuro (parâmetros
já prontos), sem prazo, não decidido nesta sessão.

Nenhum valor de cálculo do simulador foi tocado — só texto explicativo e
comentários; `imt-jovem.html` (o guia) também não foi tocado, fora do
âmbito desta Issue. Suite completa (`pytest tests/ -q`, ambiente local
com `playwright`/`beautifulsoup4`/`lxml`/`jsonschema`/`feedparser`/
`pytest` instalados nesta sessão, Chromium reaproveitado de
`/opt/pw-browsers`) e `ruff check scripts/ tests/ --select E,F,W
--ignore E501 .` corridos antes do commit — ver o resultado exacto no
commit desta sessão. Os 27 testes de
`tests/test_simulador_imt_jovem_calculo.py` e os testes de acessibilidade/
higiene/canários/breadcrumb/nav/pesquisa/og-image das páginas tocadas
reconfirmados sem regressões antes da suite completa.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Issue #177 fechada com
comentário a registar a decisão e a razão. Trabalho feito na branch
`claude/imt-jovem-scope-limitation-0j8gzy` (designada pelo ambiente
remoto desta sessão) — PR novo, sem merge.

---

*Última revisão: 2026-09-09 — Issue #183, passo 2: portão de confirmação
em `scripts/verificar_datas.py`, para `MARCADORES_HISTORICOS` deixar de
tratar como permanente qualquer data protegida por um marcador de
citação de diploma ou de fronteira (`portaria`/`decreto-lei`/`lei n.º`/
`despacho`/`celebrados? at[ée]`/`posterior a`/`anterior(es) a`/etc.),
independentemente de a data em causa já estar resolvida ou ser um
compromisso ainda em aberto.

**Correcção ao diagnóstico original da Issue #183** (investigado, nunca
assumido, antes de implementar): o texto da Issue atribuía o
silenciamento do prazo de 31/12/2026 da Garantia Pública em
`fontes.html` aos marcadores `Portaria`/`Decreto-Lei`. Testado
directamente contra `_esta_suprimido()` antes de qualquer código: nos
dois cartões desse tema, o `<h2>` com o diploma fica a mais de 220
caracteres da data (parágrafo longo) — o marcador que dispara de facto
é `celebrados?\s+at[ée]\b`, o mesmo que já fecha correctamente o PAER
(prazo definitivamente ultrapassado e fechado, `apoio-extraordinario-
renda.html`). A mesma frase serve dois factos semanticamente opostos —
um limite já encerrado para sempre vs. um prazo em vigor que a lei
ainda pode prorrogar — e nenhuma regex distingue isto pela redacção
sozinha.

**Mecanismo**: um marcador de `MARCADORES_HISTORICOS` só suprime
PERMANENTEMENTE uma ocorrência (`data_mes_ano`/`data_numerica`/
`prazo_outono` — os 3 únicos tipos com data própria sem ambiguidade)
se essa data for anterior (ou igual) ao carimbo "Verificado a" da
própria página, extraído por uma nova `sincronizar_clusters.
verificado_em_do_texto()` (núcleo de `extrair_verificado_em()`,
separado para operar sobre conteúdo já em memória, sem reabrir
ficheiro — usado por `verificar_datas.py`, que importa a função em vez
de reimplementar o parser de 3 formatos). Uma data posterior ao
carimbo é um compromisso ainda por cumprir à última verificação —
comporta-se então como `MARCADORES_PENDENTE`: suprimido só até a data
passar, depois exposto. Sem carimbo (fail-safe), preserva-se o
comportamento anterior — permanente — nunca "sem carimbo = expõe
tudo": testado directamente contra o corpus real antes de decidir isto
por segurança, não por conveniência — `fontes.html` tem 39 citações
permanentes genuínas (Decreto-Lei/Lei/Regulamento (CE) de 1993 a 2023)
que ficariam todas expostas por engano se a omissão de carimbo
significasse "duvidar de tudo".

**`fontes.html` ganha o seu primeiro carimbo `Verificado a`** —
pré-condição do mecanismo (é a única página do corpus com citações de
diploma sem nenhum carimbo próprio), nunca uma auditoria de conteúdo.
Nota importante para não confundir no futuro: `<p class="updated">
Verificado a 9 de setembro de 2026</p>`, acrescentado depois do
disclaimer, **não afirma que as dezenas de cartões da página foram
revistos contra as fontes oficiais nesta data** — afirma só que a
página passou a ter um ponto de referência para o portão de
confirmação funcionar. Os factos de cada cartão continuam a ter a
proveniência que já tinham (verificados nas sessões que os
acrescentaram, documentadas nas entradas de revisão deste ficheiro).
Colocado deliberadamente longe de qualquer citação de diploma (testado
com `_janela_contexto` real antes de decidir a posição) — o topo de
`<main>` e o hero foram testados primeiro e rejeitados por caírem
dentro do alcance de "Diário da República"/"Portaria"/`.hero`
respectivamente (o segundo por motivo de contraste, não de marcador).

**Achado colateral, não corrigido nesta sessão**: o mesmo `grep` que
confirmou a posição segura de `fontes.html` revelou que **53 páginas
do site já têm o seu próprio carimbo "Verificado a" dentro do alcance
de um marcador histórico** (ex.: `caixa-geral-aposentacoes.html`,
`carreiras-contributivas-estrangeiro.html`) — um facto pré-existente,
não introduzido por este portão: confirmado com o código de ANTES desta
sessão que essas duas páginas já não geravam nenhum alerta nem em 2028,
porque o próprio carimbo de revisão anual fica mascarado por "Lei n.º"/
"Regulamento (CE)" perto. O portão novo não piora isto (não muda o
resultado para essas 53 páginas, confirmado por diff completo do corpus
antes/depois) mas também não o resolve — fica registado para decisão
futura, fora do âmbito desta Issue.

**Âmbito deliberado, sem data prevista de expansão**: só os 3 tipos com
data própria e sem ambiguidade (`data_mes_ano`, `data_numerica`,
`prazo_outono`). `ano_letivo` (par de anos, ex. "2025/2026", sem dia
próprio) e `valor_ias` (ano solto na janela, sem grupo de regex
dedicado) ficam fora desta iteração — nenhum caso concreto da Issue os
exige, e derivar uma data única e sem ambiguidade a partir de qualquer
um dos dois exigiria uma decisão de desenho à parte (ex.: que dia do
ano lectivo representa o par "2025/2026"?), nunca uma extensão mecânica
do portão actual.

**Resultado do baseline — diff vazio, não as 39 entradas antecipadas na
proposta**: a proposta original estimava "39 entradas mudariam", mas
essa simulação testava um desenho REJEITADO (sem carimbo em
`fontes.html`, com o fail-safe a tratar "sem carimbo" como "expõe
tudo"). Com o desenho efectivamente implementado — carimbo acrescentado
+ fail-safe que preserva o comportamento anterior — as 39 citações de
`fontes.html` já estavam no baseline aprovado desde o PR #184 e
continuam correctamente permanentes (todas anteriores a
9 de setembro de 2026). `scripts/auditar_marcadores_historicos.py`
ganhou o mesmo portão espelhado (`_fica_exposta_ao_portao()`, com o
mesmo `verificado_em_do_texto()` e a mesma `_data_da_ocorrencia()`
importada de `verificar_datas.py` — nunca reimplementada) para o
baseline nunca mentir sobre o que `_esta_suprimido()` faz de facto;
como este script fixa `ANO_REFERENCIA=2026` por desenho (nunca
`datetime.now()`, ver docstring do próprio módulo), o portão nunca
altera nenhuma das 295 supressões desse ano fixo — confirmado por
`auditar_corpus()` a devolver exactamente as mesmas 295 entradas antes
e depois, 0 novas, 0 órfãs.

**Verificado directamente contra o calendário real (2027-2028), fora do
baseline fixo**: a correcção funciona — `garantia-publica-credito-
habitacao.html` passa a alertar de forma consistente a partir de 2027
(hoje continua correctamente silenciado, a data ainda não chegou);
`apoio-extraordinario-renda.html` (PAER, prazo genuinamente fechado)
nunca começa a alertar por causa do portão — o alerta que já tinha a
partir de 2027 vem de outra causa, pré-existente, confirmada idêntica
antes e depois desta sessão (o próprio carimbo da página a envelhecer,
mecanismo normal e desejado). Diff completo do corpus (945 combinações
página×ano×mês) confirma só 35 diferenças, todas explicadas: 5 são o
alvo desta correcção (`fontes.html`); 20 (4 páginas × 5 combinações)
são a mesma classe de correcção a alcançar, correctamente, outro prazo
real e ainda em aberto — a produção de efeitos do Decreto-Lei n.º
166/2026 a 31/12/2026 (artigo 63.º), citado em `psu-quem-tem-
direito.html`, `psu-vs-abono-familia.html`, `simulador-psu.html` e
`simulador-rsi.html` — registado na Issue #186, não corrigido aqui; as
restantes 10 são reclassificações cosméticas em
páginas que já alertavam de qualquer forma antes desta sessão
(`bolsa-de-merito.html`, `renovar-cartao-cidadao.html`), sem nenhuma
mudança na decisão final de alertar ou não.

Suite completa + `ruff check scripts/ tests/ --select E,F,W --ignore
E501 .` — ver o resultado exacto no commit desta sessão.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/prazo-verificacao-issue183-passo2` (designada pelo ambiente
remoto desta sessão) — PR novo, sem merge.

---

*Última revisão: 2026-09-15 — Issue #192: fronteira de palavra sistemática
em `_contem_keyword()` (`scripts/gerar_noticias.py`), a substituir a cadeia
reactiva de `if kw == "ias"/"ase"/"reforma"` (cada uma só corrigida depois
de um falso positivo já publicado — "dias"/"famílias" para "ias",
"quase"/"baseadas" para "ase", 2026-09-09/#190) por uma única regra
aplicada a TODAS as keywords de `CAT_KEYWORDS`/`CLUSTER_KEYWORDS`: `\b` só
à ESQUERDA da keyword, nunca à direita (o sufixo é flexão portuguesa
normal — "abono"→"abonos", "reforma"→"reformados" — e nunca produziu falso
positivo; foi a fronteira à direita em `\breforma\b` que tinha obrigado a
inventar a keyword "reformado" à mão, remendo agora desnecessário).
Regexes compiladas cacheadas com `functools.lru_cache`.

**Medição obrigatória antes de aplicar** (script descartável, comparando a
função antiga com a nova sobre os 120 itens reais de `data/noticias.json`):
exactamente 1 diferença, como previsto — "rsi" substring de
"unive[rsi]tária" no item "Renda universitária: apoios que podes pedir em
Portugal", gravado `categoria=apoios`/`cluster_id=trabalho-rendimento`,
nunca antes detectado por não passar por nenhum dos 3 casos especiais
antigos. Corrigido: `--recalcular-clusters` (`trabalho-rendimento` → `null`,
seguro em massa) + correcção manual da `categoria` (`apoios` → `habitacao`,
único item tocado) + `--sync`.

**Simetria corrigida**: `detectar_categoria(titulo, resumo)` extraída como
função real (mesma assinatura de `detectar_cluster()`); `detect_category(entry)`
passa a ser só o adaptador que extrai `title`/`summary` da entrada bruta do
feed e delega. `recalcular_categorias(itens)` acrescentada como gémeo
exacto de `recalcular_cluster_ids()` (devolve mudanças, nunca altera em
memória), com a flag `--recalcular-categorias [--dry-run]`.

**Achado lateral, não corrigido — assimetria de entrada, documentada em
`ROADMAP.md` → "TRABALHO FUTURO REGISTADO"**: ao contrário de
`cluster_id`, correr `--recalcular-categorias` em massa não é seguro hoje
— a `categoria` gravada de itens antigos foi calculada na ingestão a
partir do título BRUTO e do resumo INTEGRAL do feed (nunca gravados);
recalcular a partir dos campos já gravados dá 6 diferenças (`--dry-run`),
das quais só 1 é desta issue — as outras 5 incluem pelo menos uma
regressão real ("Candidaturas à ASE 2026/2027" iria de `educacao` para
`apoios`, porque "abono" está no resumo gravado e "apoios" vem antes de
"educacao" na ordem de inserção de `CAT_KEYWORDS`). Falta decidir a
precedência entre categorias antes de generalizar a correcção em massa —
por isso só o item desta issue foi corrigido à mão, os outros 5 ficaram
como estavam.

**Testes** (`tests/test_gerar_noticias.py`, `import pytest` acrescentado ao
topo, antes em falta): invariante parametrizado sobre TODAS as keywords de
`CAT_KEYWORDS`+`CLUSTER_KEYWORDS` (`not _contem_keyword(kw, "xpto"+kw)` e o
lado do sufixo, `_contem_keyword(kw, "... "+kw+"s ...")` — aplicam-se
sozinhos a qualquer keyword futura); tabela de armadilhas reais
(`ias`/`dias`, `ias`/`famílias`, `ase`/`quase`, `ase`/`baseadas`,
`rsi`/`universitária`); caso real da "Renda universitária"; simetria
`detect_category(entry) == detectar_categoria(titulo, resumo)`; e os dois
testes de `recalcular_categorias()` (só o que muda, nunca altera em
memória). Comentários antigos junto a `CLUSTER_KEYWORDS`/nos testes de
2026-09-09 actualizados para reflectir a regra sistemática, sem reescrever
o que já estava certo (o comportamento observável de "ase"/"reforma" não
mudou, só deixou de depender de um caso especial). Secção de notícias do
`CLAUDE.md` reescrita («`_contem_keyword()` — fronteira de palavra
sistemática») — a frase antiga ("hoje: ias, ase, reforma") já não
descrevia o código.

Suite completa (249 testes em `test_gerar_noticias.py`, todos a passar) +
`ruff check scripts/ --select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/192-fronteira-keyword-sistematica-8azmrn` (designada pelo ambiente
remoto desta sessão) — PR novo, sem merge, "Closes #192".

---

*Última revisão: 2026-09-15 — corrige `apoio-extraordinario-renda.html`
para reflectir a ressalva do n.º 2 do artigo 3.º do Decreto-Lei
n.º 20-B/2023, na redação do Decreto-Lei n.º 43/2024, de 2 de julho
(pendência registada em `VERIFICACAO-PENDENTE.md` ao fechar a Issue #197):
o apoio mantém-se, excecional e temporariamente, num contrato posterior a
15 de março de 2023 quando, cumulativamente, o contrato anterior cessou
comprovadamente por iniciativa do senhorio (nunca do locatário), o
contrato em vigor é para o mesmo locatário e o mesmo imóvel, corresponde a
habitação permanente e domicílio fiscal, e isso é comprovado pela
Autoridade Tributária a partir da comunicação obrigatória dos contratos.
Texto legal confirmado GRAU 1 por dois espelhos independentes com texto
idêntico (PGDL — pgdlisboa.pt — e o PDF da AT-Madeira,
at.madeira.gov.pt) — dre.pt continua bloqueado nesta sessão.

**Duas precisões que o registo anterior (Issue #197) tinha ao lado**:
1) o preâmbulo do diploma fala em "mesmas partes", mas o articulado exige
só o **mesmo locatário** — nunca o mesmo senhorio; 2) não é "contrato
renovado" em geral — é cessação por **iniciativa do senhorio**; quem mudou
de contrato por iniciativa própria não está abrangido. Corrigido em
`dados/parametros/habitacao.yaml` (`paer_contrato_data_limite`,
`descricao`/`referencia_legal`) e `dados/parametros.json` regenerado.

As 4 ocorrências absolutas da página tratadas em dois níveis: corpo
(novo bloco `.aviso-info`) e FAQ visível ganharam a ressalva completa,
com as 4 condições cumulativas; resposta directa do hero e `FAQPage`
JSON-LD ganharam a versão curta ("salvo se o contrato anterior cessou
por iniciativa do senhorio e continuas no mesmo imóvel") — nunca o
JSON-LD a prometer ao Google a versão antiga enquanto o corpo já diz
outra coisa. Página passou a citar `Decreto-Lei n.º 43/2024` em texto
visível — ganhou cartão próprio em `fontes.html` (mesmo GRAU 1, dois
espelhos), o que passou `apoio-extraordinario-renda.html` a ser coberto
por `tests/test_fontes_coerencia.py` pela primeira vez (antes passava só
por nunca citar nenhum diploma). "Verificado a"/`dateModified` avançados
para 15/09/2026 nas duas páginas tocadas.

**Canário novo**, `tests/test_valores_ancora.py::
test_paer_ressalva_dl_43_2024_acompanha_toda_afirmacao_da_data_limite`
— exige a ressalva ("senhorio") num raio de 700 caracteres de CADA
afirmação de "15 de março de 2023" na página (não só presença algures),
para que uma reescrita futura de uma das 4 ocorrências sem trazer a
ressalva para perto continue a fazer o teste falhar. Confirmado a falhar
de propósito (JSON-LD sem a ressalva) e revertido antes do commit.

`tests/marcadores_historicos_baseline.json` regenerado
(`scripts/auditar_marcadores_historicos.py --write`) — 18 supressões
novas + 1 órfã, todas revistas: mesma data-limite permanente do PAER
("15 de março de 2023"), agora perto de mais texto legal
("decreto-lei"/"lei n.º") em `apoio-extraordinario-renda.html` e no
cartão novo de `fontes.html`; a órfã é a mesma ocorrência, cujo texto à
volta mudou de "Contratos mais recentes nunca estiveram abrangidos"
para a frase que remete para a ressalva — nenhuma esconde uma data
genuinamente desactualizada. Entrada de `VERIFICACAO-PENDENTE.md`
removida.

Suite completa (4313 passed, 538 skipped) + `ruff check scripts/
--select E,F,W --ignore E501 .` limpo.
`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` reconfirmados
`False` (inalterados — sessão sem scraper). Trabalho feito na branch
`claude/paer-ressalva-dl-43-2024-tkg05z` (designada pelo ambiente remoto
desta sessão) — PR novo, sem merge, sem "Closes" (sem issue associada).

---

*Última revisão: 2026-09-15 — corrige a Issue #223
(`psu-quem-tem-direito.html`, `prestacao-social-unica.html`,
`psu-lista-13-apoios.html`): o artigo 61.º/2 do Decreto-Lei
n.º 166/2026 não nomeia nenhuma prestação — usa só a expressão
categorial "subsídios sociais de parentalidade e de desemprego". A
issue (e as 3 páginas) tratavam #12 (deslocação a unidade hospitalar
fora da ilha) e #13 (riscos específicos) como caso à parte por "não
estarem nomeados", enquanto atribuíam ao mesmo artigo uma lista de
cinco prestações "nomeadas" que também não estavam — era interpretação
nossa, não o texto da lei, e a exclusão de #12/#13 dessa interpretação
nunca teve critério declarado.

Fechado com leitura do Decreto-Lei n.º 91/2009 (consolidação do DRE,
versão de 20/11/2023, com a Lei n.º 65/2023 já incorporada — GRAU 2,
`diariodarepublica.pt` continua bloqueado nesta sessão): o artigo 46.º
(Capítulo III, subsídios sociais de parentalidade) lista seis
subsídios, incluindo riscos específicos (#13) e deslocação a unidade
hospitalar fora da ilha (#12, alínea aditada pela Lei n.º 65/2023, em
vigor desde 21/11/2023). O artigo 62.º/k do DL 166/2026 revoga esse
Capítulo III por inteiro — é o mesmo conjunto que o artigo 61.º/2
protege pela categoria. #12 e #13 entram na continuidade transitória
como os outros quatro, sem distinção entre si.

Corrigido: as 3 páginas (removida a nota "não é possível confirmar
aqui qual dos dois mecanismos se aplica"; #12/#13 juntam-se ao grupo
do artigo 61.º nos parágrafos "Continuidade sem conversão" e no
`FAQPage` JSON-LD correspondente, corpo e JSON-LD mantidos em
paridade), `fontes.html` (cartão do Decreto-Lei n.º 91/2009 alargado
ao Capítulo III + novo cartão para a Lei n.º 65/2023) e `CLAUDE.md`
("IMPACTO DA PSU" — nova subsecção "PENDÊNCIA #12/#13 vs PSU —
FECHADA", com a lição geral: perante uma categoria jurídica em vez de
uma enumeração, a pergunta é "pertence à categoria?", nunca "está
nomeado?", e a resposta vive no diploma que define a categoria, nunca
no que só a invoca). Issue #223 fechada com a transcrição literal do
artigo 46.º e o mesmo raciocínio.

Correcção adicional ao cartão da Lei n.º 65/2023: "alínea f) ao n.º 1
do artigo 46.º" corrigido para "alínea f) ao artigo 46.º" — o artigo
46.º do DL 91/2009 não tem números, é corpo único com alíneas a) a f).

`pytest`/`PyYAML`/`feedparser`/`jsonschema`/`beautifulsoup4`/`lxml`
instalados no sandbox desta sessão (não estavam disponíveis nas
sessões anteriores documentadas neste ficheiro). Suite completa
corrida: **4331 passed, 538 skipped** — os skips são todos de testes
que dependem de Playwright/browser real, não instalado neste sandbox
(mesma limitação estrutural já documentada, nunca ligada a esta
sessão). `tests/test_fontes_coerencia.py` e
`tests/test_higiene_indexacao.py` (pedidos explicitamente) incluídos
nessa corrida, sem falhas.

`tests/test_auditar_marcadores_historicos.py` falhou numa 1.ª
corrida — 10 supressões novas, todas em `fontes.html`, à volta de duas
datas históricas permanentes introduzidas pelos cartões novos ("em
vigor desde 21 de novembro de 2023", a data de entrada em vigor da
Lei n.º 65/2023; "versão de 20 de novembro de 2023", a data do
espelho de consolidação do DRE lido). Revistas uma a uma antes de
aprovar — nenhuma esconde uma data a expirar, ambas são citações
permanentes de diploma/proveniência. Baseline regenerado
(`python3 scripts/auditar_marcadores_historicos.py --write`); suite
reconfirmada a passar por inteiro depois da regeneração.

`AUTO_UPDATE_HABILITADO`/`REVALIDACAO_CARIMBO_HABILITADA` não tocados.
Trabalho feito na branch `claude/223-correccao-metodologica`, pedida
explicitamente pelo utilizador nesta sessão, a substituir a branch
designada pelo ambiente remoto (`claude/issue-223-verification-
ilt0fi`).

---

*Última revisão automática: 2026-09-20*
