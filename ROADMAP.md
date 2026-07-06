# ROADMAP.md — Gatilhos e Próximos Passos (uso interno)

Ficheiro **privado**, nunca servido publicamente: é `.md`, não `.html` — não
entra no pipeline, no `sitemap.xml`, no `scripts/pesquisa.js` nem em nenhum
link de nenhuma página. Nada aqui é conteúdo do site.

**Regra deste ficheiro**: é um índice/apontador, nunca uma cópia. O detalhe
completo de cada item vive sempre em `CLAUDE.md` — aqui só a referência à
secção certa, para nunca divergirem. Actualizar aqui quando um gatilho
dispara, muda de estado, ou é criado/fechado — mas escrever o raciocínio
completo sempre em `CLAUDE.md`, nunca aqui.

---

## 🔔 À ESPERA DE UM SINAL

### Manuais (só o Nuno vê o sinal — o sistema não avisa)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Autobaixa** (`autobaixa.html`) | Nuno confirma no Google Search Console que `baixa-medica-subsidio-doenca.html` acumula impressões relevantes para "autobaixa"/"autodeclaração de doença" — **sem limiar numérico fixado**, é julgamento do Nuno | Google Search Console (Code não tem acesso) | Criar `autobaixa.html` (6 passos: reaproveitar secção 8, pilar mantém versão resumida, evitar canibalização SEO, cross-links, cluster `trabalho-rendimento`, checklist completa) — ver CLAUDE.md **"GATILHO AUTOBAIXA"** |
| **Auto-update do carimbo "Verificado a"** (`REVALIDACAO_CARIMBO_HABILITADA`) | ≥14 relatórios shadow consecutivos com simulações correctas (zero falsos elegíveis) **e** fontes correspondentes maioritariamente `OK` — decisão do Nuno, nunca do Claude Code | `shadow_history/*.md`, secção "Carimbos elegíveis para revalidação (simulado)" de cada relatório | Ligar a flag numa sessão manual dedicada, nunca de ânimo leve — ver CLAUDE.md **"REVALIDAÇÃO DE CARIMBO"** |
| **Densidade da PSU na homepage** | "Quando o tema arrefecer" (sem data fixada) — julgamento do Nuno | Olhar à homepage / tráfego | Remover banner do topo + cartão de prazos (dos 6 pontos actuais que a PSU ocupa) — ver CLAUDE.md **"FECHO DO PROJECTO"** → "Registado para o futuro", ponto 1 |
| **Backlog Habitação** (garantia crédito jovem, isenção IMT jovem, RSAA, 1.º Direito) | Nenhum — só quando houver prioridade dedicada | — | Fact-check + página nova, um apoio de cada vez — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** → Backlog |
| **Novo sistema de ação social no ensino superior** (`bolsa-de-estudo-ensino-superior.html`) | Publicação em dre.pt do decreto-lei aprovado em Conselho de Ministros a 21/05/2026 (aplicável a partir de 2026/2027) — nenhuma fonte automática vigia isto, verificação manual/`WebSearch` em `dges.gov.pt`/dre.pt | dre.pt, dges.gov.pt (Code não tem scraper dedicado) | Reescrever a secção "O que muda a partir de 2026/2027" com os valores/fórmula reais do diploma publicado; actualizar `<title>`/description se um valor máximo concreto passar a existir (e nesse caso, cobrir em `tests/test_valores_ancora.py`) |

### Automáticos (o sistema já avisa via Issue)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Decreto-lei da PSU publicado** | Publicação em dre.pt do decreto-lei da PSU (prazo PRR: 31 ago 2026) | ⚠️ **`dre_psu` está quebrado** — nunca extraiu conteúdo real desde a criação (URL de pesquisa do DRE devolve o índice inteiro, não filtrado); até corrigir, só verificação manual/news serve de facto | Correr `/atualizar-cluster-psu` (9 passos: actualizar 4 páginas do cluster, criar `como-pedir-psu.html` + `calendario-pagamentos-psu.html`, publicar `simulador-psu.html`, transformar `rsi.html`, actualizar avisos em subsídio desemprego/parental, nunca apagar páginas antigas, reduzir densidade da PSU depois, actualizar `data/clusters.json`, revalidar a lista dos 13 apoios em `prestacao-social-para-a-inclusao.html`) — ver CLAUDE.md **"IMPACTO DA PSU"** → "Plano de acção" |
| **Data/valor expirado numa página** | `verificar_datas.py` (Shadow Mode + pipeline) detecta um padrão não suprimido | Issues `data-expirada` (fecho automático se corrigido) | Rever a página assinalada — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** |
| **Fonte do scraper bloqueada 3 dias seguidos** | `data/estado_fontes.json` regista o 3.º dia consecutivo `BLOQUEADO` (inclui `dre_psu` desde 2026-07-05, agora que "conteúdo suspeito" conta como bloqueio) | Issues `fonte-bloqueada` (fecho automático ao recuperar) | Investigar/corrigir o scraper para essa fonte — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** e **"AUDITORIA DE INFRAESTRUTURA"** achado 1 |
| **Feed de notícias morto 3 dias seguidos** | `data/estado_feeds.json` regista o 3.º dia consecutivo `MORTO` | Issues `feed-morto` (fecho automático ao recuperar) | Substituir/reparar o feed — ver CLAUDE.md **"FRESCURA DA HOMEPAGE"** → "Fontes RSS" |
| **Branch remota com commits únicos** | `limpar-branches.yml` (push a main, cron diário `0 5 * * *`, manual) encontra uma branch != `main` não totalmente integrada | Issue única `🌿 Branches órfãs por integrar` (fecho automático quando a lista fica vazia) | Trazer o trabalho para `main` (commit directo, nunca PR) ou apagar a branch manualmente — ver CLAUDE.md **"LIMPEZA AUTOMÁTICA DE BRANCHES"** |

---

## 🔧 TRABALHO FUTURO REGISTADO

Correcções/decisões adiadas, já documentadas — sem prazo, sem decisão de
"quando" tomada:

- **URL de pesquisa do `dre_psu` quebrada** — trocar exige primeiro confirmar
  o mecanismo real de disparo da pesquisa da SPA do DRE (não é só trocar
  `q=` por `termo=`); sessão com browser interactivo real necessária — ver
  CLAUDE.md **"IMPACTO DA PSU"** (nota do sentinela) e **"AUDITORIA DE
  INFRAESTRUTURA"** achado 1.
- **`MUDOU` nunca cria Issue** — só fica em `avisos.log`
  (`mudanca_estrutural:`); não existe hoje um tipo de Issue nem consumidor
  para esse padrão — ver CLAUDE.md **"SEG-SOCIAL — ESTRATÉGIA DE FETCH"**
  (Gap conhecido).
- **Ranking da pesquisa interna por relevância real** — hoje corta a 8
  resultados por saturação (`MAX_RESULTADOS`), não por relevância; decisão de
  UX, não bug — ver CLAUDE.md **"AUDITORIA DE INFRAESTRUTURA"** achado 6.
- **`LIMIAR_ANOMALIA_PAGINAS=25` nunca dispara** — `_paginas_elegiveis()` só
  conta as 22 páginas da raiz (`*.html`, não recursivo), as pillar pages em
  `p/*.html` nunca entram — ver CLAUDE.md **"SHADOW MODE — SISTEMA DE
  OBSERVAÇÃO"**.
- **Scan de segredos ao histórico completo** — `gitleaks` CLI indisponível
  no sandbox de desenvolvimento; recomendado ao Nuno correr
  `gitleaks detect --source . --log-opts="--all"` localmente antes de tornar
  o repositório privado — ver CLAUDE.md **"AUDITORIA DE INFRAESTRUTURA"**
  achado 5.
- **Variante clara de `clusters.css`** — se um dia se quiser dar
  breadcrumb/relacionados também aos simuladores, sem forçar hero escuro —
  ver CLAUDE.md **"FECHO DO PROJECTO"** → "Registado para o futuro", ponto 2.
- **CSS morto da nav antiga** — limpeza cosmética nos `<style>` de cada
  página, sem risco (nada o usa) — ver CLAUDE.md **"FECHO DO PROJECTO"** →
  "Registado para o futuro", ponto 3.
- **Branch de teste `teste-janitor-nao-integrada`** — criada de propósito
  para provar em CI real que `limpar-branches.yml` nunca apaga uma branch
  com commits únicos (1 commit, marcador `.janitor-test-marker.txt`, nunca
  chega a `main`); a sessão não conseguiu apagá-la (`git push --delete` deu
  403, mesma limitação de sempre) — apagar manualmente no GitHub. Depois de
  apagada, a Issue #59 ("🌿 Branches órfãs por integrar") fecha-se sozinha
  na próxima corrida do workflow (push a main, cron `0 5 * * *`, ou
  `workflow_dispatch` manual) — **esse fecho automático ainda não foi
  confirmado em CI real** (só o caminho "cria/actualiza a Issue" foi
  verificado nesta sessão) — ver CLAUDE.md **"LIMPEZA AUTOMÁTICA DE
  BRANCHES"**.
- **2 páginas novas propostas para o cluster escolar** (decisão do Nuno,
  nada implementado) — `calendario-escolar-apoios.html` (calendário único
  de prazos ASE/bolsa mérito/MEGA/prova escolar) e
  `bolsa-de-estudo-ensino-superior.html` (lacuna já admitida pelo próprio
  `p/apoios-escolares.html` — bolsas DGES nunca cobertas) — ver
  `ANALISE-CLUSTER-ESCOLAR.md` para o inventário completo e o raciocínio.

---

## 📅 DATAS FIXAS

| Quando | O quê | Páginas |
|---|---|---|
| **Janeiro** | Novo IAS (e valores derivados) | `abono-de-familia.html`, `rsi.html`, `complemento-solidario-idosos.html`, `subsidio-desemprego.html`, `subsidio-parental.html`, `amim.html` — Issue automática do scraper |
| **Janeiro/Fevereiro** | Nova portaria de actualização da PSI | `prestacao-social-para-a-inclusao.html` — verificação manual/news dre.pt |
| **Junho** (antes do prazo 31 jul) | Rever ano lectivo/prazo — não deve disparar antes de **junho de 2027** | `prova-escolar.html` — calendário anual |
| **Julho, até publicação** | Datas do MEGA 2026/2027 (manuais escolares) — confirmado a 06/07/2026 que ainda não há anúncio (gov.pt, manuaisescolares.pt, IGeFE); vigilância automática alargada a `igefe.mec.pt` nesse mesmo dia (nova fonte `igefe_mega`, ver CLAUDE.md) | `manuais-escolares-mega.html` — Issue automática do scraper, agora com 2 fontes independentes (`dge.mec.pt` **e** `igefe.mec.pt`) sob a mesma chave de aviso — ver CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** |
| **Agosto 2026** | Prazo PRR do decreto-lei da PSU | `prestacao-social-unica.html`, `psu-quando-entra-em-vigor.html`, `psu-quem-tem-direito.html` — verificação manual/news dre.pt |
| **Setembro** | Prazos ASE / Bolsa de Mérito | `acao-social-escolar.html`, `bolsa-de-merito.html` — calendário anual |
| **Janeiro 2027** | Entrada em vigor da PSU para beneficiários (texto inicial, ainda não confirmado pelo decreto-lei) | Todo o cluster PSU |

Detalhe completo: CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** e **"IMPACTO DA
PSU"**.

---

## ✅ CONCLUÍDO RECENTEMENTE

- **`limpar-branches.yml`** — 2026-07-06, apaga sozinho branches remotas
  totalmente integradas (via GITHUB_TOKEN do Actions, nunca depende de
  sessão logada) e regista as que têm commits únicos numa Issue única —
  fecha a lacuna que já tinha deixado 2 branches órfãs por apagar
  manualmente em sessões anteriores.
- **Vigilância automática das datas MEGA alargada a `igefe.mec.pt`** (nova
  fonte `igefe_mega`) — 2026-07-06, fecha o furo em que só `dge.mec.pt` era
  vigiado.
- **Página `bolsa-de-estudo-ensino-superior.html`** — publicada 2026-07-06,
  6.ª página do cluster `apoios-escolares`, fecha a lacuna já admitida pelo
  próprio `p/apoios-escolares.html`.
- **Simulador de subsídio de doença** (`simulador-subsidio-doenca.html`) —
  publicado 2026-07-05, 4.ª calculadora do site.
- **Página `baixa-medica-subsidio-doenca.html`** — publicada 2026-07-05.
- **Auditoria de infraestrutura e robustez** (dre_psu, concurrency,
  smoke inline, gitleaks) — fechada 2026-07-05.
- **Recuperação automática do deploy do GitHub Pages** — 2026-07-05.
- **Smoke test de produção** (`smoke-producao.yml`) — 2026-07-04/05.
- **Acessibilidade WCAG 2.1 AA** — 0 violações em 36/36 páginas — 2026-07-04.
- **Hub de simuladores** (`simuladores.html`) — 2026-07-04.
- **Simulador CSI** (`simulador-csi.html`) — 2026-07-04.
- **Auditoria de indexação e higiene SEO técnica** (canónicas, `Article`
  JSON-LD, sitemap) — 2026-07-04.
- **Página PSI** (`prestacao-social-para-a-inclusao.html`) — 2026-07-04.
- **E-E-A-T / NV Labs como entidade resolvível** (`sobre.html`, autoria nos
  artigos) — 2026-07-03.
- **Cluster Habitação** (`p/habitacao.html`, `porta-65.html`,
  `apoio-extraordinario-renda.html`) — 2026-07-03.

Detalhe completo de cada um: ver a respectiva secção em CLAUDE.md ou a
entrada de "Última revisão" com a data correspondente.
