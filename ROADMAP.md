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

## 📄 GERADOR DE DOCUMENTOS — ESTADO (Sessões 1 e 2 concluídas, 2026-07-06)

Ver CLAUDE.md → **"GERADOR DE DOCUMENTOS"** para o detalhe completo
(arquitectura, portão de verificação, testes). Projecto concluído — as
12 minutas candidatas do prompt original foram todas verificadas e
publicadas (nenhuma rejeitada).

**Motor** (`assets/js/gerador-documentos.js`) + CSS partilhado + hub
`/documentos.html` (12 cards) + 12 páginas em `documentos/`:

| # | Minuta | Resultado do portão |
|---|---|---|
| 1 | `reclamacao-decisao-seguranca-social.html` | Sem pivot — CPA arts. 191.º-192.º |
| 2 | `carta-acompanhamento-reavaliacao-abono.html` | **Pivot** — Modelo GF58-DGSS |
| 3 | `carta-acompanhamento-csi.html` | **Pivot** — Mod. CSI 1/1.1/1.2 |
| 4 | `recurso-hierarquico-seguranca-social.html` | Sem pivot — CPA arts. 193.º-198.º |
| 5 | `carta-acompanhamento-divida-prestacoes.html` | **Pivot** — Mod. IMP.PN.01.01 |
| 6 | `carta-acompanhamento-comunicacao-alteracao.html` | **Pivot** — Mod. GF 37/GF 54-DGSS (contextos específicos) |
| 7 | `exposicao-atraso-processamento.html` | Sem pivot — CPA arts. 128.º-129.º |
| 8 | `carta-acompanhamento-svi-recurso.html` | **Pivot** — Mod. SVI 55-DGSS, prazo 10 dias |
| 9 | `requerimento-reavaliacao-escalao-ase.html` | Sem pivot — processo descentralizado por escola |
| 10 | `pedido-acesso-documentos-administrativos.html` | Sem pivot — Lei n.º 26/2016 (LADA) |
| 11 | `requerimento-generico-seguranca-social.html` | Sem pivot — template catch-all |
| 12 | `pedido-declaracao-comprovativo-prestacoes.html` | Sem pivot forte — SS Direta é auto-serviço |

**Excluída à partida** (decisão do prompt original, nunca avaliada):
procurações e qualquer documento com efeitos de representação legal.

Integração completa: nav, `sitemap.xml`, `scripts/pesquisa.js`,
cross-links a partir de `abono-de-familia.html`,
`complemento-solidario-idosos.html`, `acao-social-escolar.html`,
`reclamacao-decisao-seguranca-social.html`, e de
`rsi.html`/`subsidio-desemprego.html`/`baixa-medica-subsidio-doenca.html`/
`prestacao-social-para-a-inclusao.html` para a reclamação. Meta
descriptions das 3 páginas da Sessão 1 revistas para CTR nesta sessão;
título da carta de CSI encurtado (risco de corte no Google).

62 golden tests (`tests/test_gerador_documentos.py`, genérico sobre as
12 páginas via `page.evaluate("CONFIG_DOCUMENTO")` — nunca hardcoded
por minuta) + teste de rede. Suite completa: **1738 passed, 4
skipped**. Trabalho directo em `main`.

**Registado para o futuro, sem prazo**: generalizar `Pagina.slug` em
`sincronizar_clusters.py` para suportar sub-caminhos (`documentos/...`)
e dar cluster membership a sério às minutas (badge "Ferramenta",
contagem no cartão da homepage) — só as 12 páginas ficarem em
`EXCLUIDAS` funciona bem hoje, o refactor só se justifica se o número
de minutas crescer muito mais. SVI (`carta-acompanhamento-svi-recurso.html`)
e AMIM (`amim.html`) deliberadamente **nunca** cross-linkados entre si
— são processos de junta médica distintos (Segurança Social vs.
Ministério da Saúde) — não reverter essa decisão sem confirmar de novo
que são de facto o mesmo sistema.

---

## 🪪 CAMADA 3 — "COMO FAZER X NO PORTAL" — ESTADO (arrancou 2026-07-14)

Ver CLAUDE.md → entrada "Última revisão: 2026-07-14" (sessão
`como-pedir-niss.html`) e a entrada seguinte (sessão
`declaracao-situacao-contributiva`) para o detalhe completo de cada
página (fact-check, estrutura, integração).

**Publicadas (2 de N):**

| Página | Publicada | Nota |
|---|---|---|
| `como-pedir-niss.html` | 14 jul. 2026 | Guia evergreen sobre como pedir o Número de Identificação da Segurança Social — o passo mais a montante de qualquer apoio do site (sem NISS não há Segurança Social Direta nem simuladores) |
| `declaracao-situacao-contributiva.html` | 14 jul. 2026 | "Certidão de não dívida à Segurança Social" — nuance diferenciadora: quem nunca trabalhou não consegue pedi-la online, só ao balcão; desambiguada da certidão equivalente das Finanças |

**Candidatos seguintes, registados sem prioridade nem prazo** (mesmo
padrão de outras listas de backlog neste ficheiro — nenhum tem
fact-check feito ainda):

| Página candidata | Porquê |
|---|---|
| `primeiro-acesso-seguranca-social-direta.html` | Registo/activação da conta SSD (password, Chave Móvel Digital, cartão de cidadão + leitor) — pré-requisito prático de quase todos os guias do site |
| `como-mudar-morada-cartao-cidadao.html` | Actualização de morada no CC/SSD — afecta elegibilidade a vários apoios (ex.: abono, RSI) e é uma dúvida recorrente nos artigos já publicados |

---

## 🔔 À ESPERA DE UM SINAL

### Manuais (só o Nuno vê o sinal — o sistema não avisa)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Autobaixa** (`autobaixa.html`) | Nuno confirma no Google Search Console que `baixa-medica-subsidio-doenca.html` acumula impressões relevantes para "autobaixa"/"autodeclaração de doença" — **sem limiar numérico fixado**, é julgamento do Nuno | Google Search Console (Code não tem acesso) | Criar `autobaixa.html` (6 passos: reaproveitar secção 8, pilar mantém versão resumida, evitar canibalização SEO, cross-links, cluster `trabalho-rendimento`, checklist completa) — ver CLAUDE.md **"GATILHO AUTOBAIXA"** |
| **Auto-update do carimbo "Verificado a"** (`REVALIDACAO_CARIMBO_HABILITADA`) | ≥14 relatórios shadow consecutivos com simulações correctas (zero falsos elegíveis) **e** fontes correspondentes maioritariamente `OK` — decisão do Nuno, nunca do Claude Code | `shadow_history/*.md` + **`python scripts/validar_carimbos_elegiveis.py`** (sessão manual, só leitura — valida o dia: exit 0 = conta para a contagem; contagem iniciada a **2026-07-11, dia 1 validado**, com 9 avisos todos classificados como artefactos das correcções do scraper de 03/07 e 07/07) | Ligar a flag numa sessão manual dedicada, nunca de ânimo leve — ver CLAUDE.md **"REVALIDAÇÃO DE CARIMBO"** |
| **Densidade da PSU na homepage** | "Quando o tema arrefecer" (sem data fixada) — julgamento do Nuno | Olhar à homepage / tráfego | Remover banner do topo + cartão de prazos (dos 6 pontos actuais que a PSU ocupa) — ver CLAUDE.md **"FECHO DO PROJECTO"** → "Registado para o futuro", ponto 1 |
| **Nova tabela de rendas máximas de referência do Porta 65** | Publicação anual, tipicamente no fim do ano, de um novo PDF `RendasMaximas_AAAA.pdf` no Portal da Habitação — não é um decreto-lei, por isso fora do alcance da watchlist DRE (`dre_habitacao_paer`/`dre_habitacao_garantia`) | portaldahabitacao.pt (verificação manual — sem scraper dedicado) | Confirmar a tabela do ano novo e actualizar `porta-65.html` se algum valor citado no corpo mudar — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
| **Novo sistema de ação social no ensino superior — publicação em DR ainda por confirmar** (`bolsa-de-estudo-ensino-superior.html`) | **Estado a 2026-07-14** (não fechado): o diploma foi promulgado pelo PR a 7/07/2026 (confirmado por 6+ fontes jornalísticas independentes) — mas esta sessão **não confirmou** a publicação em Diário da República nem a citação exacta (número/data) do decreto-lei; acesso directo a dre.pt bloqueado em 2 sessões seguidas. A página já reflecte os valores comunicados pelo Governo/DGES-IES (mínima ≈872€, média ≈2.660€, apoio residência 160€/mês, Bolsa de Incentivo 1.045€) com nota explícita dessa lacuna — **nunca afirmar que "já é lei" sem essa confirmação** | dre.pt (Code não tem scraper dedicado; tentar `WebSearch` por "Decreto-Lei n.º" + "ação social" + "ensino superior" + o ano, ou pedir ao Nuno para confirmar directamente) | 1) Confirmar a citação exacta do decreto-lei publicado; 2) verificar os valores já publicados na página contra o texto real do diploma (não assumir que o comunicado do Governo bate certo com o texto final); 3) citar o número do decreto-lei na página (`fonte-bloco` + JSON-LD se aplicável); 4) só depois disso — nunca antes — cobrir os valores (872€/2.660€/160€/1.045€) em `tests/test_valores_ancora.py`, como canário de consistência (não há fórmula IAS-derivada, mesma categoria do abono/PSI) |

### Automáticos (o sistema já avisa via Issue)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Decreto-lei da PSU publicado — ALTA PRIORIDADE, gatilho aproximando-se** | Publicação em dre.pt do decreto-lei da PSU (prazo PRR: 31 ago 2026). **Milestone intermédia já cumprida a 2026-07-17**: o PR promulgou a autorização legislativa que permite ao Governo aprovar o decreto-lei — válida só 120 dias (janela ~ago-nov 2026) — e o diploma final terá de fixar valores e condições directamente (já não por portaria), ficando sujeito a nova promulgação do PR e possível apreciação parlamentar. Isto reduz a margem de tempo real até ao gatilho seguinte | `dre_psu` — **corrigido a 2026-07-07** (Issue #54): pesquisa interactiva de frase exacta no diariodarepublica.pt, com âncora que prova filtragem real; Issue automática ao detectar um Decreto-Lei nos resultados (ver CLAUDE.md "IMPACTO DA PSU" → nota do sentinela). Confirmado `OK` e monitorizado diariamente (`data/estado_fontes.json`, `ultima_ok: 2026-07-18`) — cron diário sem data-limite, cobre a janela ago-nov sozinho | Correr `/atualizar-cluster-psu` — sessão imediata de valores + activação do simulador PSU assim que a Issue disparar (9 passos: actualizar as 5 páginas do cluster, criar `como-pedir-psu.html` + `calendario-pagamentos-psu.html`, publicar `simulador-psu.html`, transformar `rsi.html`, actualizar avisos em subsídio desemprego/parental, nunca apagar páginas antigas, reduzir densidade da PSU depois, actualizar `data/clusters.json`, revalidar a lista dos 13 apoios em `prestacao-social-para-a-inclusao.html`) — ver CLAUDE.md **"IMPACTO DA PSU"** → "Plano de acção" |
| **Data/valor expirado numa página** | `verificar_datas.py` (Shadow Mode + pipeline) detecta um padrão não suprimido | Issues `data-expirada` (fecho automático se corrigido) | Rever a página assinalada — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** |
| **Fonte do scraper bloqueada 3 dias seguidos** | `data/estado_fontes.json` regista o 3.º dia consecutivo `BLOQUEADO` (inclui `dre_psu` desde 2026-07-05, agora que "conteúdo suspeito" conta como bloqueio) | Issues `fonte-bloqueada` (fecho automático ao recuperar) | Investigar/corrigir o scraper para essa fonte — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** e **"AUDITORIA DE INFRAESTRUTURA"** achado 1 |
| **Revogação do PAER / reforma "produto único" do arrendamento — watchlist nova (Sessão 3, 2026-07-20)** | `dre_habitacao_paer` — pesquisa de frase exacta `"apoio extraordinário à renda"` no diariodarepublica.pt, mesmo mecanismo do `dre_psu`; dispara quando um Decreto-Lei aparecer nos resultados. **Nunca calibrado contra um runner real nesta sessão** (WebFetch/curl bloqueados) — a 1.ª corrida real do pipeline confirma o `min_chars_uteis` | Issue `🏠 Decreto-lei sobre o PAER detectado em DRE` (label `verificar`, dedup automático) | Confirmar se revoga/substitui o PAER isoladamente ou é a fusão "produto único" (Porta 65/Porta 65+/PAER/Arrendar para Subarrendar); actualizar `apoio-extraordinario-renda.html` sempre, `porta-65.html`/`primeiro-direito.html`/`p/habitacao.html` se for a fusão — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
| **Alteração/prorrogação da Garantia Pública (DL 44/2024) — watchlist nova (Sessão 3, 2026-07-20)** | `dre_habitacao_garantia` — pesquisa de frase exacta `"Decreto-Lei n.º 44/2024"`, mesmo mecanismo; crítico perto do prazo actual, 31/12/2026. **Nunca calibrado contra um runner real nesta sessão** | Issue `🔑 Decreto-lei que cita o DL 44/2024 (Garantia Pública) detectado em DRE` (label `verificar`, dedup automático) | Confirmar o que muda (prazo, percentagem, valor do imóvel); se for o prazo, actualizar `garantia_prazo_contrato_limite` em `dados/parametros/habitacao.yaml` + `garantia-publica-credito-habitacao.html` — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
| **Feed de notícias morto 3 dias seguidos** | `data/estado_feeds.json` regista o 3.º dia consecutivo `MORTO` | Issues `feed-morto` (fecho automático ao recuperar) | Substituir/reparar o feed — ver CLAUDE.md **"FRESCURA DA HOMEPAGE"** → "Fontes RSS" |
| **Branch remota com commits únicos** | `limpar-branches.yml` (push a main, cron diário `0 5 * * *`, manual) encontra uma branch != `main` não totalmente integrada | Issue única `🌿 Branches órfãs por integrar` (fecho automático quando a lista fica vazia) | Trazer o trabalho para `main` (commit directo, nunca PR) ou apagar a branch manualmente — ver CLAUDE.md **"LIMPEZA AUTOMÁTICA DE BRANCHES"** |

---

## 🔧 TRABALHO FUTURO REGISTADO

Correcções/decisões adiadas, já documentadas — sem prazo, sem decisão de
"quando" tomada:

- **`MUDOU` nunca cria Issue** — só fica em `avisos.log`
  (`mudanca_estrutural:`); não existe hoje um tipo de Issue nem consumidor
  para esse padrão — ver CLAUDE.md **"SEG-SOCIAL — ESTRATÉGIA DE FETCH"**
  (Gap conhecido).
- **Ranking da pesquisa interna por relevância real** — hoje corta a 8
  resultados por saturação (`MAX_RESULTADOS`), não por relevância; decisão de
  UX, não bug — ver CLAUDE.md **"AUDITORIA DE INFRAESTRUTURA"** achado 6.
- **Scan de segredos ao histórico completo** — `gitleaks` CLI indisponível
  no sandbox de desenvolvimento; recomendado ao Nuno correr
  `gitleaks detect --source . --log-opts="--all"` localmente antes de tornar
  o repositório privado — ver CLAUDE.md **"AUDITORIA DE INFRAESTRUTURA"**
  achado 5.
- **Variante clara de `clusters.css`** — se um dia se quiser dar
  breadcrumb/relacionados também aos simuladores, sem forçar hero escuro —
  ver CLAUDE.md **"FECHO DO PROJECTO"** → "Registado para o futuro", ponto 2.
- **Migração do ASE para parâmetros YAML (Commit 3 da sessão "Parâmetros
  YAML + auditoria factual", 2026-07-19)** — ⛔ **bloqueado**: exige o
  despacho anual da DGEstE (Ministério da Educação) com os escalões ASE
  do ano lectivo 2026/2027, ainda não fornecido/verificado pelo Nuno.
  Quando disponível: `dados/parametros/ase.yaml` deve **referenciar os
  escalões do abono** (A↔1.º, B↔2.º) em vez de duplicar limiares —
  dependência explícita para que uma actualização do abono nunca deixe o
  ASE inconsistente — mais auditoria de `simulador-ase.html` e
  `acao-social-escolar.html` contra o despacho. Commits 1 (subsídio de
  doença) e 2 (abono de família) desta sessão concluídos — ver CLAUDE.md
  **"DADOS ABERTOS"** e a entrada de revisão "Última revisão: 2026-07-19"
  (sessão "Parâmetros YAML + auditoria factual") para o detalhe completo,
  incluindo as 2 correcções factuais reais encontradas (piso do subsídio
  de doença RMMG-não-IAS; limite da Garantia para a Infância IAS-2024).
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
---

## 📅 DATAS FIXAS

| Quando | O quê | Páginas |
|---|---|---|
| **Janeiro** | Novo IAS (e valores derivados) | `abono-de-familia.html`, `rsi.html`, `complemento-solidario-idosos.html`, `subsidio-desemprego.html`, `subsidio-parental.html`, `amim.html` — Issue automática do scraper |
| **Janeiro/Fevereiro** | Nova portaria de actualização da PSI | `prestacao-social-para-a-inclusao.html` — verificação manual/news dre.pt |
| **Junho** (antes do prazo 31 jul) | Rever ano lectivo/prazo — não deve disparar antes de **junho de 2027** | `prova-escolar.html` — calendário anual |
| **Junho/Julho 2027** | Revisão anual do calendário e dos 2 despachos de prazo que mudam de ano para ano (vales MEGA, bolsa de estudo do ensino superior) | `calendario-escolar-apoios.html`, `manuais-escolares-mega.html`, `bolsa-de-estudo-ensino-superior.html` — `verificar_datas.py` confirmado a disparar sozinho em 2027 (padrão `data_mes_ano`/`ano_letivo`) |
| **Junho 2027** | Próxima revisão sazonal do MEGA (datas de emissão 2026/2027 já publicadas e confirmadas a 13/07/2026: 3/10/13 ago) | `manuais-escolares-mega.html` — ver CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** |
| **Mensal (automático)** | Calendário de pagamentos — `calendario-mensal.yml` **raspa a fonte pública oficial** (`/ptss/pssd/pagamentos`) e publica o mês seguinte sozinho (dia 25/28) + vira a página no dia 1; agosto 2026 já foi obtido e publicado automaticamente (12/07). Só precisa de sessão manual se o scraper falhar (Issue `calendario-manual` com o erro) — ex.: prestação nova fora da allow-list `NOME_PARA_SLUG` | `calendario-pagamentos-seguranca-social.html` + `data/calendario_pagamentos.json` — ver CLAUDE.md **"CALENDÁRIO DE PAGAMENTOS"** e `docs/FONTE-CALENDARIO.md` |
| **Agosto 2026** | Prazo PRR do decreto-lei da PSU (autorização legislativa promulgada a 17/07/2026, válida 120 dias) | `prestacao-social-unica.html`, `psu-quando-entra-em-vigor.html`, `psu-quem-tem-direito.html`, `psu-lista-13-apoios.html`, `psu-trabalho-social.html`, `psu-vs-abono-familia.html` — verificação manual/news dre.pt + sentinela `dre_psu` |
| **3 de agosto de 2031** (nota de verificação, sem gatilho de acção) | Prazo-limite real remanescente para os Cartões de Cidadão com MRZ mas sem chip de contacto (emitidos até 10/06/2024). O prazo de 2026 **não** se aplica ao CC normal — corrigido a 2026-07-18 após esclarecimento oficial do IRN (30/12/2025); só afecta o CC do Tratado de Porto Seguro e o BI vitalício | `renovar-cartao-cidadao.html` — ver CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** |
| **Setembro** | Prazos ASE / Bolsa de Mérito | `acao-social-escolar.html`, `bolsa-de-merito.html` — calendário anual |
| **Janeiro 2027** | Entrada em vigor da PSU para beneficiários (texto inicial, ainda não confirmado pelo decreto-lei) | Todo o cluster PSU |

Detalhe completo: CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** e **"IMPACTO DA
PSU"**.

---

## ✅ CONCLUÍDO RECENTEMENTE

- **Cluster Habitação — Sessão 3 (fecho: dedução de rendas, 1.º Direito,
  auditoria Porta 65, watchlist DRE)** — 2026-07-20. Fecha o "Backlog
  Habitação". PASSO 0 confirmou por `WebSearch` (`WebFetch`/`curl`
  continuam bloqueados nesta sessão): o Decreto-Lei n.º 97/2026, de 20
  de maio, já está **publicado** (não pendente, ao contrário do que o
  prompt admitia como hipótese) — sobe a dedução de rendas no IRS para
  900€/2026 e 1.000€/2027 (a declaração entregue em 2026, sobre
  rendimentos de 2025, usa ainda 700€) e cria o RSAA, com efeitos desde
  1 set. 2026; o PAER continua em vigor, revogação **não** publicada; o
  1.º Direito (DL 37/2018 + DL 44/2025) confirmado com candidatura
  sempre via município (Estratégia Local de Habitação); a reforma
  "produto único" (fusão Porta 65/Porta 65+/PAER/Arrendar para
  Subarrendar) é só uma intenção anunciada, sem projecto de lei
  publicado — distinta do Fundo de Emergência para a Habitação (FEH,
  aprovado em Conselho de Ministros a 9/07/2026, não confirmado
  publicado em DRE), que também não é apresentado como recurso já
  disponível.

  2 páginas novas (`deducao-rendas-irs.html`, `primeiro-direito.html`),
  ambas com FAQPage+HowTo+BreadcrumbList+Article,
  `.resposta-rapida`+`.checklist-final`; `dados/parametros/habitacao.yaml`
  ganhou `deducao_rendas_irs_limite_eur` (3 vigências: 700/2023,
  900/2026, 1000/2027) com 4 golden tests novos (incl. um que tranca a
  cronologia nunca poder ler-se como "900€ já em vigor na declaração de
  2026"); os limiares do 1.º Direito (4×IAS/60×IAS) validados contra o
  `IAS_2026` já afirmado no canário, sem YAML próprio (não aparecem em
  title/meta). `porta-65.html` auditado: aviso de transição para quem
  vai comprar casa (cancelar o Porta 65), confirmação da tabela de
  rendas máximas 2026, e nota de watchlist não-alarmista sobre o
  "produto único" — 2 FAQs novas, paridade visível↔JSON-LD mantida.
  `p/habitacao.html` reorganizado em 3 secções (🏠 Arrendar / 🔑 Comprar
  / 🏚️ Situações de carência), `fontes.html` +3 diplomas
  (DL 37/2018, DL 44/2025, DL 97/2026). `data/clusters.json` actualizado
  (7 páginas + hub + simulador) — `sincronizar_clusters.py`,
  `sincronizar_nav.py`, `adicionar_canonicas.py`,
  `adicionar_autoria_artigos.py`, `adicionar_article_jsonld.py`,
  `inserir_botao_partilhar.py` confirmados idempotentes (0 alterações,
  páginas já nasceram correctas), `gerar_og_images.py --write` gerou as
  2 imagens novas.

  Watchlist DRE nova (`scripts/scraper_playwright.py`): duas fontes
  Playwright (`dre_habitacao_paer`, `dre_habitacao_garantia`), mesmo
  mecanismo `pesquisa_interactiva` já provado do `dre_psu` — lógica de
  detecção generalizada em `_detectar_decreto_lei_generico`
  (`_detectar_decreto_psu` mantido intocado como wrapper fino, por
  compatibilidade com `tests/test_dre_psu_pesquisa.py`). Ambas
  monitorizadas em `SLUGS_MONITORIZADOS` (máquina de estados
  fonte-bloqueada) e com blocos de Issue dedicados em
  `pipeline-diario.yml` (dedup por título, mesmo padrão MEGA/PSU — só
  linhas de `avisos.log` de hoje, corrigindo de origem o bug de linha
  antiga reencontrada já documentado para as Issues #55-#58). **Nunca
  calibrado contra um runner real nesta sessão** — ver as duas linhas
  novas em "Automáticos" acima; a 1.ª corrida real do pipeline confirma
  os `min_chars_uteis`. 12 testes novos em
  `tests/test_dre_habitacao_watchlist.py`.

  `scripts/urls_criticas.txt` ganhou as 2 páginas novas (smoke test de
  produção). Nenhum canário de URLs dedicado (mesmo padrão de
  `data/urls_como_pedir.json`) foi criado — decisão já registada na
  Sessão 1, reconfirmada: infra-estrutura específica ao cluster
  `como-pedir`, sem equivalente genérico no repositório.

  **Integrada em `main` a 2026-07-20** (sessão de handoff/integração
  separada, protocolo da secção "REGRA ABSOLUTA — GIT" do CLAUDE.md):
  fast-forward directo de `claude/habitacao-rendas-primeiro-direito-bwvyvx`
  (`3c85832`→`64e51bd`) para `main`, sem PR, sem conflitos (main não tinha
  avançado desde a base). CI local reconfirmada no estado final antes do
  merge (suite completa, ruff, `verificar_datas`,
  `verificar_skips_permitidos.py`, `gerar_parametros_json.py --check`).
  Push a `main` disparou os 4 workflows — todos confirmados `success` via
  API (por `head_sha` exacto, nunca assumido pelo "run mais recente"):
  **Integridade do Código** (7 jobs, incl. "Suite de Testes (pytest)"),
  **Validar Conteúdo HTML**, **Verificação de Produção (Smoke Test)** —
  confirma as 2 páginas novas + `imt-jovem.html`/`garantia-publica-
  credito-habitacao.html` a servir conteúdo real em produção — e
  **Limpar Branches Órfãs**. Branch local apagada; a remota cai sozinha
  no próximo push via `limpar-branches.yml`.

- **Cluster Habitação — Sessão 2 (correcção IMT Jovem + simulador)** —
  2026-07-20. (1) Correcção factual de `imt-jovem.html`: limites das
  Regiões Autónomas (25% acima do Continente — isenção total até
  413.174€, parcial até 826.228€ em 2026; Lei n.º 21/90 + Ofício
  Circulado n.º 40129/2026) em nota junto à tabela + FAQ nova, e a
  exclusão de terrenos para construção (informação vinculativa da AT,
  out. 2025) como erro comum novo — ambos parametrizados em
  `dados/parametros/habitacao.yaml`, com canário RA = Continente×1,25.
  (2) `simulador-imt-jovem.html` (7.º simulador): tabela geral de IMT
  2026 (HPP, Continente) parametrizada no YAML (15 parâmetros, incl. IS
  0,8%), fetch de `/dados/parametros.json` em runtime (padrão CSI),
  checklist de elegibilidade (inelegível nunca vê poupança), VPT, 27
  testes novos. Tabela RA deliberadamente fora do simulador (parcelas a
  abater RA não confirmadas de forma conclusiva) — só Continente, com
  aviso. `/simulador-imt-jovem.html` no smoke test (urls_criticas +
  array SIMULADORES). Sessão 3 (RSAA, 1.º Direito, dedução de rendas,
  watchlist DRE) continua por fazer — ver "Backlog Habitação".
  **Sessão 2 integrada em `main` a 2026-07-20** — fast-forward directo
  (`aca7e50..edc6191`, sem PR, branch `claude/imt-jovem-correcao-
  simulador-73xpd7` apagada localmente após o merge; a remota cai via
  `limpar-branches.yml` no próximo push, mesmo padrão da Sessão 1).
  CI local completa reconfirmada no estado final da branch antes do
  merge (suite 2917 passed/4 skipped, ruff, `verificar_datas.py` sem
  falsos positivos nas páginas tocadas, `verificar_skips_permitidos.py`
  4/4, `gerar_parametros_json.py --check` sincronizado). Push a `main`
  disparou os 4 workflows — os 4 confirmados `success` no commit
  `edc6191`: **Integridade do Código**, **Validar Conteúdo HTML**,
  **Verificação de Produção (Smoke Test)** — log real confirmado com
  `OK https://tensdireito.com/simulador-imt-jovem.html (200)` dentro do
  array `SIMULADORES`, que exige também `"Verificado a"` no corpo, não
  só o status — e **Limpar Branches Órfãs**.

- **Cluster Habitação — Sessão 1 (`imt-jovem.html` +
  `garantia-publica-credito-habitacao.html`)** — 2026-07-20. Fecha a
  1.ª metade do "Backlog Habitação" (linha abaixo): novo
  `dados/parametros/habitacao.yaml` (padrão OpenFisca, PASSO 0 via
  `WebSearch` — `WebFetch` continua bloqueado nesta sessão) com os
  limiares de IMT Jovem (330.539€/660.982€/8%, Lei n.º 73-A/2025 + DL
  n.º 48-A/2024) e da Garantia Pública (15%/450.000€/10 anos/18-35
  anos/86.634€, DL n.º 44/2024 + Portaria n.º 236-A/2024/1); 2 páginas
  novas completas (FAQPage+HowTo+BreadcrumbList+Article, resposta-
  rápida, checklist-final); `p/habitacao.html` reorganizado em duas
  secções (🏠 Arrendar / 🔑 Comprar); `fontes.html` com os 4 diplomas
  novos; 8 golden tests novos em `test_valores_ancora.py`. Sessões 2
  (simulador de IMT Jovem) e 3 (RSAA, 1.º Direito, dedução de rendas em
  IRS, watchlist automática) do mesmo plano ficam para sessões
  seguintes — ver linha "Backlog Habitação" abaixo.
  **Sessão 1 integrada em `main` a 2026-07-20** — fast-forward directo
  (`d7abbbb..5e1ab7a`, sem PR, branch `claude/new-session-vbrhmd`
  apagada automaticamente pelo `limpar-branches.yml` no mesmo push).
  Confirmado no push real a `main`, os 4 workflows: `Integridade do
  Código` (suite completa + ruff + gitleaks + pip-audit), `Validar
  Conteúdo HTML`, `pages build and deployment` e `Verificação de
  Produção (Smoke Test)` — todos `success`. `/imt-jovem.html` e
  `/garantia-publica-credito-habitacao.html` não foram confirmadas por
  pedido HTTP directo (`curl`/`WebFetch` a `tensdireito.com` bloqueados
  nesta sessão, 403 via proxy — mesma limitação documentada em várias
  sessões anteriores) — confiança assente no `pages build and
  deployment` bem-sucedido (publicou exactamente a árvore do commit
  `5e1ab7a`, que contém os dois ficheiros estáticos) e no smoke test
  às páginas críticas também verde.
  **Verificação pós-deploy (mesmo dia, sessão seguinte)** — o Nuno
  reportou o hub (`p/habitacao.html`) em produção a parecer a versão
  antiga (sem "Comprar"/IMT Jovem/Garantia Pública). Confirmado por
  esta sessão, directamente contra o repositório (não assumido): `git
  log` mostra `5e1ab7a` (e `a026d4a`, o commit seguinte) em `main`;
  `git show main:p/habitacao.html` já tem a secção "🔑 Comprar" e os
  links para as 2 páginas novas; `imt-jovem.html`,
  `garantia-publica-credito-habitacao.html` e
  `dados/parametros/habitacao.yaml` confirmados no `git ls-tree` de
  `main`. **`main` e o deploy publicado estão correctos** — não é um
  problema de merge nem de conteúdo. Causa mais provável: cache do CDN
  do GitHub Pages a servir uma cópia antiga da página (`p/habitacao.html`
  não está em `scripts/urls_criticas.txt`, por isso o smoke test que
  correu no push nunca a verificou directamente — só confirmou que o
  deploy em si teve sucesso, via outras páginas). **Aguardar
  propagação e reverificar em 24h** (pedir ao Nuno para recarregar
  `p/habitacao.html` sem cache, ou verificar de novo nesta janela) —
  nenhuma acção de código necessária enquanto isso não for confirmado.
  **Lacuna do canary fechada no mesmo dia**: `/p/habitacao.html`,
  `/imt-jovem.html` e `/garantia-publica-credito-habitacao.html`
  acrescentadas a `scripts/urls_criticas.txt` — é exactamente esta
  ausência que explicava o smoke test do push de integração nunca ter
  apanhado o hub directamente. Verificado localmente (`curl` real a
  `tensdireito.com` bloqueado nesta sessão — mesma limitação de proxy
  já documentada — substituído por `http.server` local a servir os
  ficheiros reais do repositório, mesmo padrão já usado nas sessões que
  criaram este script): as 3 URLs novas respondem 200.
  **Sem verificação de conteúdo necessária nas 3** —
  `scripts/smoke_producao.sh` só faz verificação de conteúdo extra para
  `SIMULADORES`/`JSON_A_VALIDAR` (arrays explícitos no script);
  `p/habitacao.html` cai fora de ambos, por isso o smoke test nunca
  vai reprovar por a secção "Comprar" ainda não ter propagado no CDN —
  só confirma 200. Não foi preciso nenhum commit em duas fases nem
  lógica nova no script; só a lista de URLs mudou.
  **Reverificação — FECHADA (sessão de arranque/handoff, mesmo dia,
  16:48 UTC)**: as 3 URLs entraram em `scripts/urls_criticas.txt`
  (ponto anterior), por isso os pushes seguintes já as verificam em
  produção real via `smoke-producao.yml`, correndo no runner do GitHub
  Actions — sem o bloqueio de rede desta sessão. Confirmados **3
  deploys/checks consecutivos verdes** desde o relato do Nuno, o mais
  recente a 16:48 UTC (push `ac39990`): `OK
  https://tensdireito.com/p/habitacao.html (200)`, `OK .../imt-
  jovem.html (200)`, `OK .../garantia-publica-credito-habitacao.html
  (200)` (runs `29759483198`/`29760617739`/`29761133949`, logs reais
  via `get_job_logs`, nunca assumidos). Tempo decorrido desde o
  primeiro push (`5e1ab7a`, manhã do mesmo dia) já excede as 24h
  pedidas. Verificação de conteúdo ("Comprar" no HTML servido)
  continua fora do alcance desta sessão — `curl`/`WebFetch` a
  `tensdireito.com` bloqueados (403 via proxy) — mas a combinação de
  árvore correcta em `main` + 3 checks 200 sucessivos ao longo de horas
  é suficiente para fechar a nota de cache: **nunca mais foi visto um
  200 com conteúdo antigo nas 3 URLs desde então.** Nenhuma acção
  adicional pendente.
- **`declaracao-situacao-contributiva.html`** — 2026-07-14, 2.ª página da
  Camada 3 editorial, cluster `trabalho-rendimento`. "Certidão de não
  dívida à Segurança Social" — ver secção "🪪 CAMADA 3" acima e CLAUDE.md
  para o detalhe completo.
- **`calendario-escolar-apoios.html`** — 2026-07-14, 7.ª página do cluster
  `apoios-escolares` (proposta em `ANALISE-CLUSTER-ESCOLAR.md`), calendário
  único de prazos julho-outubro (Prova Escolar, MEGA, ASE, bolsa de mérito,
  bolsa de estudo do ensino superior, passe sub-23). No mesmo commit:
  `bolsa-de-estudo-ensino-superior.html` actualizada com o novo sistema de
  ação social (promulgado 7/07/2026) e o prazo 2026/2027 (14 ago-2 out, mais
  tarde que em anos anteriores). Ver CLAUDE.md — entrada "Última revisão:
  2026-07-14" (sessão `calendario-escolar-apoios`).
- **Datas de emissão dos vales MEGA 2026/2027 confirmadas** — 2026-07-13
  (3/10/13 ago), sentinela `mega_datas`/`igefe_mega`/`dge_manuais` a
  confirmar `OK` desde então, zero Issues abertas — gatilho fechado.
- **`como-pedir-niss.html`** — 2026-07-14, 1.ª página da Camada 3
  editorial ("Como fazer X no portal"), cluster `trabalho-rendimento`.
  Ver secção "🪪 CAMADA 3" acima e CLAUDE.md para o detalhe completo.
- **Auditoria completa (Fase 2) de `simulador-subsidio-doenca.html`** —
  2026-07-06. Valores reconfirmados sem divergências (zero correcções de
  código); 8 golden tests novos (fronteiras 30/31 e 365/366, piso
  universal a morder de facto, majoração via checkbox, seguro social
  voluntário, teto exacto); FAQ nova a esclarecer que gravidez de risco
  é prestação distinta (lacuna de UX real, não coberta antes); carimbo
  actualizado. Ponto ⚠️A (retroactividade dos dias de espera) **fechado
  na mesma sessão** — o Nuno confirmou directamente que não há
  retroactividade; ⚠️B (piso 300€/325€ em períodos parciais) continua em
  aberto — ver CLAUDE.md **"Última revisão: 2026-07-06"** (as duas
  entradas da auditoria) para o
  detalhe completo.
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
- **Detecção de datas expiradas tornada recursiva** (`p/` + `documentos/`,
  52 páginas; marcador "anterior a" para o falso positivo do PAER no pillar
  de Habitação) — 2026-07-07; ver CLAUDE.md "SHADOW MODE" ponto 8.
- **Sentinela `dre_psu` corrigido de vez** (Issue #54) — 2026-07-07: pesquisa
  interactiva de frase exacta no diariodarepublica.pt (nenhum parâmetro de
  URL filtra — confirmado num runner com browser real); ver CLAUDE.md
  "IMPACTO DA PSU" → nota do sentinela.
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
