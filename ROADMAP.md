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
| **Backlog Habitação** (garantia crédito jovem, isenção IMT jovem, RSAA, 1.º Direito) | Nenhum — só quando houver prioridade dedicada | — | Fact-check + página nova, um apoio de cada vez — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** → Backlog |
| **Novo sistema de ação social no ensino superior — publicação em DR ainda por confirmar** (`bolsa-de-estudo-ensino-superior.html`) | **Estado a 2026-07-14** (não fechado): o diploma foi promulgado pelo PR a 7/07/2026 (confirmado por 6+ fontes jornalísticas independentes) — mas esta sessão **não confirmou** a publicação em Diário da República nem a citação exacta (número/data) do decreto-lei; acesso directo a dre.pt bloqueado em 2 sessões seguidas. A página já reflecte os valores comunicados pelo Governo/DGES-IES (mínima ≈872€, média ≈2.660€, apoio residência 160€/mês, Bolsa de Incentivo 1.045€) com nota explícita dessa lacuna — **nunca afirmar que "já é lei" sem essa confirmação** | dre.pt (Code não tem scraper dedicado; tentar `WebSearch` por "Decreto-Lei n.º" + "ação social" + "ensino superior" + o ano, ou pedir ao Nuno para confirmar directamente) | 1) Confirmar a citação exacta do decreto-lei publicado; 2) verificar os valores já publicados na página contra o texto real do diploma (não assumir que o comunicado do Governo bate certo com o texto final); 3) citar o número do decreto-lei na página (`fonte-bloco` + JSON-LD se aplicável); 4) só depois disso — nunca antes — cobrir os valores (872€/2.660€/160€/1.045€) em `tests/test_valores_ancora.py`, como canário de consistência (não há fórmula IAS-derivada, mesma categoria do abono/PSI) |

### Automáticos (o sistema já avisa via Issue)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Decreto-lei da PSU publicado — ALTA PRIORIDADE, gatilho aproximando-se** | Publicação em dre.pt do decreto-lei da PSU (prazo PRR: 31 ago 2026). **Milestone intermédia já cumprida a 2026-07-17**: o PR promulgou a autorização legislativa que permite ao Governo aprovar o decreto-lei — válida só 120 dias (janela ~ago-nov 2026) — e o diploma final terá de fixar valores e condições directamente (já não por portaria), ficando sujeito a nova promulgação do PR e possível apreciação parlamentar. Isto reduz a margem de tempo real até ao gatilho seguinte | `dre_psu` — **corrigido a 2026-07-07** (Issue #54): pesquisa interactiva de frase exacta no diariodarepublica.pt, com âncora que prova filtragem real; Issue automática ao detectar um Decreto-Lei nos resultados (ver CLAUDE.md "IMPACTO DA PSU" → nota do sentinela). Confirmado `OK` e monitorizado diariamente (`data/estado_fontes.json`, `ultima_ok: 2026-07-18`) — cron diário sem data-limite, cobre a janela ago-nov sozinho | Correr `/atualizar-cluster-psu` — sessão imediata de valores + activação do simulador PSU assim que a Issue disparar (9 passos: actualizar as 5 páginas do cluster, criar `como-pedir-psu.html` + `calendario-pagamentos-psu.html`, publicar `simulador-psu.html`, transformar `rsi.html`, actualizar avisos em subsídio desemprego/parental, nunca apagar páginas antigas, reduzir densidade da PSU depois, actualizar `data/clusters.json`, revalidar a lista dos 13 apoios em `prestacao-social-para-a-inclusao.html`) — ver CLAUDE.md **"IMPACTO DA PSU"** → "Plano de acção" |
| **Data/valor expirado numa página** | `verificar_datas.py` (Shadow Mode + pipeline) detecta um padrão não suprimido | Issues `data-expirada` (fecho automático se corrigido) | Rever a página assinalada — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** |
| **Fonte do scraper bloqueada 3 dias seguidos** | `data/estado_fontes.json` regista o 3.º dia consecutivo `BLOQUEADO` (inclui `dre_psu` desde 2026-07-05, agora que "conteúdo suspeito" conta como bloqueio) | Issues `fonte-bloqueada` (fecho automático ao recuperar) | Investigar/corrigir o scraper para essa fonte — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** e **"AUDITORIA DE INFRAESTRUTURA"** achado 1 |
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
