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

### Canal de WhatsApp — critério editorial de publicação

Ver CLAUDE.md → **"CANAL DE WHATSAPP — GATILHO EDITORIAL DE PUBLICAÇÃO"**
para o detalhe completo. Resumo: publica-se quando (1) um sentinela
dirigido (`dre_psu`, `dre_psu_regulamentacao`, `dre_habitacao_paer`,
`dre_habitacao_garantia`, `dre_ias`) dispara **e** a verificação manual
confirma alteração real a um apoio, (2) uma página é corrigida por
mudança de facto legal com avanço da data "Verificado a" — nunca por
reorganização/trabalho interno —, ou (3) uma vez por mês, no primeiro
dia útil, o calendário de pagamentos do mês inteiro. Sem nada a
publicar: silêncio, nunca um lembrete periódico.

**Preparação automática do rascunho — implementada (2026-08-31), com
um caminho automático novo para o gatilho 1 (1b — sem esperar pela
fila manual)**:
`scripts/preparar_canal.py` (corrido em `pipeline-diario.yml`) cobre o
gatilho 1 em duas variantes e o gatilho 3 — 1a via fila manual
`data/canal_pendente.json` (uma sessão editorial escreve o resumo no
mesmo commit da correcção, `confirmado: true`; o script só formata e
entrega, nunca decide), 1b automático a partir de qualquer um dos 5
sentinelas dirigidos escrevendo em `data/scraped/avisos.log`
(`confirmado: false`, deduplicado por ocorrência — o mesmo excerto em
dias seguidos nunca gera dois rascunhos), 3 gerado automaticamente de
`data/calendario_pagamentos.json`. Um rascunho `confirmado: false`
nasce sempre com o aviso "NÃO PUBLICAR AINDA" antes do texto na Issue —
nunca é tratado como pronto a copiar. Sem nada a publicar, nenhuma
Issue `canal-rascunho` é criada. Decisão e publicação continuam sempre
manuais — ver CLAUDE.md → "Mecanismo" para o detalhe.

**Gatilho de "notícia relevante" — deliberadamente NÃO construído.**
Passo 0 desta sessão mediu os três gatilhos propostos contra os dados
reais de agosto de 2026 antes de escrever qualquer código: o critério
de selecção já usado por `gerar_noticias.py` (um vencedor/dia, até 3
categorias) teria dado **~20 dias em 31 com pelo menos uma notícia
vencedora** — muito acima do limite de 10/mês combinado com os outros
gatilhos. Um filtro mais apertado (só título com sinal legal directo —
"decreto-lei"/"portaria"/"promulga"/"entra em vigor"/"Diário da
República") reduzia para **2 dias**, mas ambos coincidiam com dias já
cobertos pelo gatilho 1 (a publicação do DL 166/2026 da PSU) — ou seja,
não acrescentava nenhuma mensagem que o gatilho legal não desse já,
só código extra a manter. Decisão do Nuno: não construir este gatilho
agora. Reabrir só com dados novos que mostrem o contrário (ex.: um
filtro que capture notícias genuinamente novas sem sobrepor o gatilho
1) — nunca por rotina.

### Manuais (só o Nuno vê o sinal — o sistema não avisa)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Autobaixa** (`autobaixa.html`) | Nuno confirma no Google Search Console que `baixa-medica-subsidio-doenca.html` acumula impressões relevantes para "autobaixa"/"autodeclaração de doença" — **sem limiar numérico fixado**, é julgamento do Nuno | Google Search Console (Code não tem acesso) | Criar `autobaixa.html` (6 passos: reaproveitar secção 8, pilar mantém versão resumida, evitar canibalização SEO, cross-links, cluster `trabalho-rendimento`, checklist completa) — ver CLAUDE.md **"GATILHO AUTOBAIXA"** |
| **Auto-update do carimbo "Verificado a"** (`REVALIDACAO_CARIMBO_HABILITADA`) | ≥14 relatórios shadow consecutivos com simulações correctas (zero falsos elegíveis) **e** fontes correspondentes maioritariamente `OK` — decisão do Nuno, nunca do Claude Code | `shadow_history/*.md` + **`python scripts/validar_carimbos_elegiveis.py`** (sessão manual, só leitura — valida o dia: exit 0 = conta para a contagem; contagem iniciada a **2026-07-11, dia 1 validado**, com 9 avisos todos classificados como artefactos das correcções do scraper de 03/07 e 07/07) | Ligar a flag numa sessão manual dedicada, nunca de ânimo leve — ver CLAUDE.md **"REVALIDAÇÃO DE CARIMBO"** |
| **Densidade da PSU na homepage** | "Quando o tema arrefecer" (sem data fixada) — julgamento do Nuno | Olhar à homepage / tráfego | Remover banner do topo + cartão de prazos (dos 6 pontos actuais que a PSU ocupa) — ver CLAUDE.md **"FECHO DO PROJECTO"** → "Registado para o futuro", ponto 1 |
| **Nova tabela de rendas máximas de referência do Porta 65** | Publicação anual, tipicamente no fim do ano, de um novo PDF `RendasMaximas_AAAA.pdf` no Portal da Habitação — não é um decreto-lei, por isso fora do alcance da watchlist DRE (`dre_habitacao_paer`/`dre_habitacao_garantia`) | portaldahabitacao.pt (verificação manual — sem scraper dedicado) | Confirmar a tabela do ano novo e actualizar `porta-65.html` se algum valor citado no corpo mudar — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
| **Excepção de idade do casal no Porta 65 Jovem — diploma que a fixa por confirmar** (`porta-65.html`) | A regra em si ("num casal um dos elementos pode ter até 36 anos, desde que o outro tenha no máximo 35") está atribuída ao Portal da Habitação e ao Portal gov.pt (2026-08-30, correcção de uma formulação vaga anterior) — mas o articulado consolidado (diploma que fixa esta excepção) nunca foi lido directamente: dre.pt continua bloqueado no ambiente desta sessão (mesma limitação de sempre) | dre.pt (sem scraper dedicado — `WebSearch`/acesso directo quando disponível) | Confirmar o diploma exacto e, se a redacção em vigor divergir da regra já publicada, corrigir `porta-65.html` (bullet da secção de elegibilidade) — nunca citar um número de diploma sem essa confirmação directa |
| **Novo sistema de ação social no ensino superior — publicação em DR ainda por confirmar** (`bolsa-de-estudo-ensino-superior.html`) | **Estado a 2026-07-14** (não fechado): o diploma foi promulgado pelo PR a 7/07/2026 (confirmado por 6+ fontes jornalísticas independentes) — mas esta sessão **não confirmou** a publicação em Diário da República nem a citação exacta (número/data) do decreto-lei; acesso directo a dre.pt bloqueado em 2 sessões seguidas. A página já reflecte os valores comunicados pelo Governo/DGES-IES (mínima ≈872€, média ≈2.660€, apoio residência 160€/mês, Bolsa de Incentivo 1.045€) com nota explícita dessa lacuna — **nunca afirmar que "já é lei" sem essa confirmação** | dre.pt (Code não tem scraper dedicado; tentar `WebSearch` por "Decreto-Lei n.º" + "ação social" + "ensino superior" + o ano, ou pedir ao Nuno para confirmar directamente) | 1) Confirmar a citação exacta do decreto-lei publicado; 2) verificar os valores já publicados na página contra o texto real do diploma (não assumir que o comunicado do Governo bate certo com o texto final); 3) citar o número do decreto-lei na página (`fonte-bloco` + JSON-LD se aplicável); 4) só depois disso — nunca antes — cobrir os valores (872€/2.660€/160€/1.045€) em `tests/test_valores_ancora.py`, como canário de consistência (não há fórmula IAS-derivada, mesma categoria do abono/PSI) |
| **Preço-tecto da refeição escolar** — decisão consciente de **não vigiar**, não uma lacuna (investigação de 2026-08-25, "Sentinela para o despacho da ASE") | Único acto do Ministério da Educação com cadência quase-anual encontrado na investigação do despacho da ASE (indexado ao IPC desde o ano lectivo 2024/2025, 1,46€ desde então, sem alteração confirmada para 2026/2027) — mas o site nunca cita este valor: `acao-social-escolar.html`/`simulador-ase.html` expressam o custo da refeição só como desconto percentual (gratuita no A, 50% no B, fixo desde o Despacho n.º 8452-A/2015), nunca o preço em euros. Por isso este acto nunca afecta um valor publicado no site | dge.mec.pt/refeitorios-escolares (sem scraper dedicado; `WebFetch` bloqueado nesta sessão para qualquer domínio `.gov.pt`/`.mec.pt`/`diariodarepublica.pt`, confirmado de novo — mesma limitação de sempre) | Nada a fazer, salvo decisão editorial futura de passar a citar o preço da refeição em euros — nesse caso, construir um sentinela dedicado (pesquisa de frase exacta, mesmo padrão de `dre_ias`) antes de publicar o valor — ver CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** |
| **Majoração da PSI — 3.ª componente ainda sem regulamentação própria** (`prestacao-social-para-a-inclusao.html`) | Publicação de portaria/diploma que regulamente a majoração prevista no Decreto-Lei n.º 126-A/2017 (distinta da "Nova portaria de actualização da PSI" já rastreada nesta tabela — essa reajusta os valores da base/complemento já em vigor; a majoração nunca chegou a ter regulamento próprio). **Sem sentinela automático** — `dre_psu_regulamentacao` só vigia Portarias que citem "Decreto-Lei n.º 166/2026" (a PSU), nunca "Decreto-Lei n.º 126-A/2017" (a PSI); confirmado por grep a `scripts/scraper_playwright.py` que não existe sentinela para este diploma. **Confirmado ainda pendente via `WebSearch` a 2026-08-26** (`WebFetch`/dre.pt bloqueados nesta sessão, mesma limitação de sempre) — nenhuma fonte encontrada menciona uma portaria publicada | dre.pt (sem scraper dedicado — `WebSearch` por "majoração" + "prestação social para a inclusão" + "portaria" + o ano) | Confirmar o texto da portaria/diploma; actualizar as várias ocorrências de "ainda não em vigor"/"aguarda regulamentação própria" (corpo + `FAQPage` JSON-LD visível e estruturado) com o valor/condições reais; considerar sentinela dedicado se o site passar a depender disto com frequência — ver CLAUDE.md, linha `prestacao-social-para-a-inclusao.html` em "PÁGINAS COM DATAS SAZONAIS" |

### Automáticos (o sistema já avisa via Issue)

| Item | Gatilho exacto | Onde verifico | Acção quando disparar |
|---|---|---|---|
| **Portaria(s) de regulamentação da PSU — art. 17.º (renda de referência) e arts. 32.º/59.º (procedimentos e meios de prova)** | Publicação em dre.pt de uma Portaria que regulamenta o Decreto-Lei n.º 166/2026 (já publicado e em vigor — o gatilho anterior "decreto-lei da PSU publicado" fechou a 2026-08-13, ver "CONCLUÍDO RECENTEMENTE"). Dois pontos concretos deixados por regulamentar pelo próprio diploma (confirmados directamente pelo Nuno na leitura do texto real) | `dre_psu_regulamentacao` — novo sentinela (2026-08-16, Fase 2 Commit 5/5): pesquisa de frase exacta pelo número do decreto-lei (`"Decreto-Lei n.º 166/2026"`), filtrando só resultados do tipo Portaria (`detectar_portaria`, mesmo mecanismo do `dre_ias`); corte de recência `"desde": "2026-08-16"`. Nunca calibrado contra um runner real nesta sessão — a 1.ª corrida real do pipeline confirma `min_chars_uteis`. `dre_psu` (o sentinela original do decreto-lei) mantém-se activo em paralelo, com um corte de recência novo (`data_minima="2026-08-16"` dentro de `_detectar_decreto_psu()`) para nunca voltar a disparar sobre o próprio DL 166/2026 já conhecido — só um decreto-lei FUTURO sobre a PSU continua a disparar essa Issue | Confirmar em dre.pt qual dos 2 pontos a Portaria regulamenta; se for o art. 17.º, actualizar `psu-quando-entra-em-vigor.html`/`simulador-psu.html` com o valor real (considerar acrescentar a `dados/parametros/psu.yaml`); se for os arts. 32.º/59.º, actualizar `como-pedir-psu.html` — ver CLAUDE.md **"IMPACTO DA PSU"** → nota do sentinela |
| **Data/valor expirado numa página** | `verificar_datas.py` (Shadow Mode + pipeline) detecta um padrão não suprimido | Issues `data-expirada` (fecho automático se corrigido) | Rever a página assinalada — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** |
| **Fonte do scraper bloqueada 3 dias seguidos** | `data/estado_fontes.json` regista o 3.º dia consecutivo `BLOQUEADO` (inclui `dre_psu` desde 2026-07-05, agora que "conteúdo suspeito" conta como bloqueio) | Issues `fonte-bloqueada` (fecho automático ao recuperar) | Investigar/corrigir o scraper para essa fonte — ver CLAUDE.md **"MÁQUINA DE ESTADOS DE FONTES BLOQUEADAS E ISSUES ÓRFÃS"** e **"AUDITORIA DE INFRAESTRUTURA"** achado 1 |
| **Revogação do PAER / reforma "produto único" do arrendamento — watchlist calibrada contra um runner real (2026-07-20)** | `dre_habitacao_paer` — pesquisa de frase exacta `"apoio extraordinário à renda"` no diariodarepublica.pt, mesmo mecanismo do `dre_psu`; dispara quando um Decreto-Lei **datado a partir de 2026-07-20** aparecer nos resultados. **1.ª corrida real (workflow_dispatch) confirmou um falso positivo genuíno**: a pesquisa devolveu correctamente o DL n.º 20-B/2023 (diploma fundador do PAER) e as suas alterações já conhecidas — sem corte de recência, dispararia esta Issue todos os dias. Corrigido com `data_minima`/`"desde": "2026-07-20"` em `_detectar_decreto_lei_generico` (`scripts/scraper_playwright.py`); Issue #73 fechada com explicação; 6 testes de regressão novos (incl. fixture real desta corrida) em `tests/test_dre_habitacao_watchlist.py`; `dre_psu` confirmado 100% inalterado. **2.ª corrida real (após a correcção) confirmou a correcção Python a funcionar** (`achou=False`, nenhuma linha nova em `avisos.log`) — mas recriou a Issue (#74) na mesma, por um bug **diferente e separado**: o passo JS "Abrir Issues" filtra `avisos.log` por dia calendário (`l.startsWith(hoje)`), não por corrida — como as 2 corridas de teste aconteceram no mesmo dia UTC, a linha antiga da 1.ª corrida (anterior à correcção) foi "reencontrada". **Nunca acontece no cron diário normal** (uma corrida/dia) — só se manifesta com múltiplos `workflow_dispatch` manuais no mesmo dia, exactamente esta calibração. Issue #74 fechada com a mesma explicação. Gap registado, não corrigido (baixa prioridade, mesma categoria do gap MUDOU do MEGA) — corrigir exigiria filtrar por timestamp de início da corrida em vez de por dia, na lógica de Issues partilhada por várias watchlists (MEGA, PSU, Garantia Pública) | Issue `🏠 Decreto-lei sobre o PAER detectado em DRE` (label `verificar`, dedup automático) | Confirmar se revoga/substitui o PAER isoladamente ou é a fusão "produto único" (Porta 65/Porta 65+/PAER/Arrendar para Subarrendar); actualizar `apoio-extraordinario-renda.html` sempre, `porta-65.html`/`primeiro-direito.html`/`p/habitacao.html` se for a fusão — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
| **Alteração/prorrogação da Garantia Pública (DL 44/2024) — watchlist calibrada contra um runner real (2026-07-20)** | `dre_habitacao_garantia` — pesquisa de frase exacta `"Decreto-Lei n.º 44/2024"`, mesmo mecanismo, mesmo corte de recência (`"desde": "2026-07-20"`); crítico perto do prazo actual, 31/12/2026. **1.ª corrida real devolveu zero resultados** (a pesquisa por esta frase com "n.º" não encontrou nenhum diploma — nem sequer o próprio DL 44/2024; comportamento seguro por desenho, mas a causa raiz — se é a pontuação "n.º"/período a quebrar a tokenização do Elasticsearch do DRE — fica por investigar, sem prioridade enquanto continuar a falhar em segurança, nunca em silêncio como sucesso) | Issue `🔑 Decreto-lei que cita o DL 44/2024 (Garantia Pública) detectado em DRE` (label `verificar`, dedup automático) | Confirmar o que muda (prazo, percentagem, valor do imóvel); se for o prazo, actualizar `garantia_prazo_contrato_limite` em `dados/parametros/habitacao.yaml` + `garantia-publica-credito-habitacao.html` — ver CLAUDE.md **"CLUSTER HABITAÇÃO"** |
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
  YAML + auditoria factual", 2026-07-19)** — ✅ **já não bloqueado**.
  Investigação de 2026-08-25 ("Sentinela para o despacho da ASE", ver
  CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** → nota
  `acao-social-escolar.html`/`bolsa-de-merito.html`) confirmou que a
  razão do bloqueio anterior — "exige o despacho anual da DGEstE com os
  escalões ASE do ano lectivo 2026/2027" — não corresponde a nenhum acto
  real: o regime está fixado desde 2015 pelos Despachos n.º 8452-A/2015,
  5296/2017 e 7255/2018 (escalões em %IAS, tectos de material/visitas em
  euros, desconto de refeições), sem nenhuma república anual; a única
  variável é o IAS, já publicado por Portaria própria e já vigiado pelo
  `dre_ias`. Pronto para migrar como qualquer outra prestação:
  `dados/parametros/ase.yaml` deve **referenciar os escalões do abono**
  (A↔1.º, B↔2.º) em vez de duplicar limiares — dependência explícita
  para que uma actualização do abono nunca deixe o ASE inconsistente —
  mais auditoria de `simulador-ase.html` e `acao-social-escolar.html`
  contra os 3 despachos-base (nunca assumir que os valores hoje no site
  já batem certo, mesma disciplina dos outros commits desta série).
  Commits 1 (subsídio de doença) e 2 (abono de família) desta sessão
  concluídos — ver CLAUDE.md **"DADOS ABERTOS"** e a entrada de revisão
  "Última revisão: 2026-07-19" (sessão "Parâmetros YAML + auditoria
  factual") para o detalhe completo, incluindo as 2 correcções factuais
  reais encontradas (piso do subsídio de doença RMMG-não-IAS; limite da
  Garantia para a Infância IAS-2024). Sem prazo, não feito ainda —
  fica como candidato ao próximo commit desta série, não como sessão de
  documentação.
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
- **Refactor de `artigos_relacionados()`** (`scripts/sincronizar_clusters.py:395`,
  `MAX_RELACIONADOS = 4`) — percorre `cluster.paginas` sempre pela mesma
  ordem, por isso qualquer página na posição ≥5 do seu cluster nunca
  aparece no bloco `RELACIONADOS` de nenhum irmão. Achado na auditoria de
  ligação interna de 2026-07-28 (Search Console: 11 páginas "Detetada —
  não indexada"): `calendario-escolar-apoios.html` (posição 7/8),
  `registo-criminal-online.html` (9/11) e `primeiro-direito.html` (6/7)
  ficavam sem nenhum link de corpo vindo de irmãos, por esta causa
  estrutural — corrigido nessa sessão só com links editoriais pontuais,
  não com este refactor. Candidato: rotação determinística (ex.: por
  posição do artigo de origem, não sempre os 4 primeiros) para que
  clusters com 5+ páginas deixem de ter uma "cauda" invisível. Sem
  prazo — só afecta clusters grandes (`como-pedir`, `habitacao`,
  `apoios-escolares`, `trabalho-rendimento`), não o resto do site.
- **43 diplomas citados em páginas mas ausentes de `fontes.html`**
  (levantamento de 2026-08-30, sessão "FONTES.HTML — LACUNA DO CLUSTER
  PSU") — a lista de trabalho é a própria `EXCECOES_DIPLOMAS_FONTES` em
  `tests/test_fontes_coerencia.py` (nova rede de segurança criada nesta
  sessão: falha se um diploma citado numa página não tiver cartão em
  `fontes.html` nem constar dessa lista). Os 3 diplomas do cluster PSU
  (Lei n.º 36/2026, Decreto-Lei n.º 166/2026, Portaria n.º 394/2026/1)
  já foram acrescentados a `fontes.html` nesta mesma sessão — ficam de
  fora da lista de trabalho. Resolver cada um dos 43 = confirmar o
  permalink real do DRE (nunca inventar um subpath — usar a homepage
  genérica `https://diariodarepublica.pt` quando não confirmável, mesma
  regra de sempre) e acrescentar o cartão em `fontes.html`, seguindo o
  padrão dos cartões de diploma já existentes (`.tag`="Legislação",
  `<h2>`=citação completa, `<p>`=descrição de uma frase). **Principal
  obstáculo**: confirmar os permalinks exige aceder a `dre.pt`, hoje
  bloqueado no ambiente de desenvolvimento (mesma limitação documentada
  em dezenas de sessões — `WebFetch`/`curl` devolvem 403 via proxy para
  domínios externos); sem isso, cada entrada teria de usar a homepage
  genérica, o que é válido mas perde a especificidade dos cartões mais
  recentes do site. Sem prazo — nenhum destes 43 é urgente por si só,
  mas o teste novo garante que a lista nunca mais cresce em silêncio: um
  diploma citado numa página nova, sem cartão nem excepção registada,
  faz o CI falhar.
- **Limiar de rendimento da Garantia para a Infância — fonte
  identificada, formula por cenário ainda por confirmar em fonte
  primária lida** (achado em 2026-09-02, sessão "Garantia para a
  Infância"; reinvestigado na sessão "Limiar da garantia — cenários",
  mesma data — ver CLAUDE.md, entradas de revisão dessa data, para o
  detalhe completo): `dados/parametros/abono.yaml`
  (`garantia_infancia_limite_rr_anual` = 2.495,37 €/ano) continua sem
  citar uma portaria concreta no campo `referencia_legal` — só o Guia
  Prático 4001 do ISS, I.P. (interpretativo, não diploma). **Fonte
  primária da OBRIGAÇÃO legal identificada nesta sessão**: o art. 4.º
  c) do Decreto Regulamentar n.º 3/2022 remete este limiar para
  portaria própria — confirmada como a **Portaria n.º 223/2022, de 6
  de setembro** (via listagem oficial em sgeconomia.gov.pt); o art. 9.º
  do DL n.º 176/2003, para onde esse artigo remete o CÁLCULO do
  Rendimento de Referência, usa a mesma lógica de 3 cenários já
  parametrizada para os limites de escalão do abono — reforça, mas não
  confirma, que o limiar em si também varia por cenário. Triangulação
  de fontes financeiras (Doutor Finanças/Montepio/Santander/
  e-konomista/CGD), mais forte do que a da sessão de 2 de setembro
  (desta vez com os 3 valores devolvidos em conjunto, de forma
  internamente coerente, na mesma síntese): (a) manutenção/rendimentos
  2024, IAS 509,26 € → 2.495,37 €; (b) pedidos novos/rendimentos 2025,
  IAS 522,50 € → 2.560,25 €; (c) reavaliação/rendimentos 2026, IAS
  537,13 € → 2.631,94 €. `simulador-abono.html` declara em comentário
  aplicar sempre o cenário (b) para os escalões, mas usa o valor do
  cenário (a) para a Garantia — inconsistência interna real,
  **documentada mas ainda não corrigida**: a correcção de 19/07/2026
  trocou o valor antigo (2.631,94 €, cenário c) por 2.495,37 € (cenário
  a), nunca por 2.560,25 € (cenário b, o coerente com o resto do
  simulador). **Continua sem correcção de valor, deliberadamente** —
  nem a Portaria n.º 223/2022 nem uma eventual actualização anual para
  2026 foram lidas (WebFetch confirmado bloqueado nesta 2.ª sessão para
  todos os domínios testados: `dre.pt`/`files.dre.pt`/`dre.tretas.org`/
  `pgdlisboa.pt`/`lexlink.eu`/bancos — não só os `.gov.pt` já
  documentados noutras sessões); a triangulação de fontes financeiras
  continua a não valer como fonte primária pelos padrões deste
  repositório. `abono-de-familia.html`, `simulador-abono.html`
  (parâmetros) e `abono.yaml` (valores) continuam intocados — só os
  comentários de ambos os ficheiros foram actualizados com o achado da
  Portaria n.º 223/2022, para a próxima sessão não repetir esta
  investigação do zero. `garantia-para-a-infancia.html` continua a
  publicar o valor actual com a nota de que não está confirmado em
  fonte primária. **Sessão dedicada deve começar por**: ler o texto da
  Portaria n.º 223/2022 e de uma eventual actualização anual (pedir
  confirmação directa ao Nuno, ou repetir o acesso a `dre.pt` num
  ambiente sem o bloqueio de rede destas duas sessões — mesmo padrão já
  usado para a Lei n.º 36/2026/DL n.º 166/2026). Só depois, se
  confirmada a estrutura de 3 cenários, actualizar `abono.yaml` (3
  parâmetros novos, mesmo padrão dos limites de escalão),
  `simulador-abono.html` (usar o valor do cenário correcto) e
  `abono-de-familia.html`/`garantia-para-a-infancia.html` (texto).
- **Inbound dos hubs (`p/familia.html`, `p/trabalho-rendimento.html`,
  `p/idosos-incapacidade-cuidadores.html`) continua fraco** — a sessão de
  2026-07-28 corrigiu o que cada hub linka PARA FORA (filhos em falta no
  corpo) mas não resolveu o inbound contextual DOS hubs (hoje: nav
  boilerplate + breadcrumbs dos filhos + 1 card na homepage, zero prosa
  editorial de fora do próprio cluster). Se, ao fim de ~2 semanas, estes 3
  hubs continuarem em "Detetada — não indexada" no Search Console, o
  próximo lever é um link contextual de subida — do artigo-filho com mais
  tráfego de cada cluster para o respectivo hub, com âncora descritiva
  (ex.: "guia completo de Família e Crianças"), não mais um card
  genérico.
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
| **13 de agosto de 2026** (cumprido) | Publicação do Decreto-Lei n.º 166/2026 (dentro do prazo PRR de 31 ago 2026) — gatilho fechado, ver "CONCLUÍDO RECENTEMENTE" | Cluster PSU inteiro (8 páginas) — activado na Fase 2 |
| **3 de agosto de 2031** (nota de verificação, sem gatilho de acção) | Prazo-limite real remanescente para os Cartões de Cidadão com MRZ mas sem chip de contacto (emitidos até 10/06/2024). O prazo de 2026 **não** se aplica ao CC normal — corrigido a 2026-07-18 após esclarecimento oficial do IRN (30/12/2025); só afecta o CC do Tratado de Porto Seguro e o BI vitalício | `renovar-cartao-cidadao.html` — ver CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** |
| **Setembro** | Prazos ASE / Bolsa de Mérito | `acao-social-escolar.html`, `bolsa-de-merito.html` — calendário anual |
| **31 de dezembro de 2026** | Produção de efeitos da PSU para beneficiários (artigo 63.º, DL 166/2026 — confirmado, corrige o "1 de janeiro de 2027" citado antes do decreto-lei sair). Conversão oficiosa dos beneficiários actuais das 13 prestações extintas; 1.º mês em que a PSU é paga de facto. Verificar nessa altura que o banner de vigência do simulador (`aplicarBannerVigencia()`, já ligado a `data_producao_efeitos`) muda automaticamente de estado, sem intervenção manual. Retirar também o `<span class="badge-novo">NOVO</span>` do cartão do Simulador da PSU na grelha `#simuladores-home` do `index.html` (destaque acrescentado a 2026-08-19, quando a PSU era o único simulador do cluster ainda sem resultado real) — a partir desta data deixa de ser novidade e passa a ser o simulador principal | Todo o cluster PSU, `simulador-psu.html`, `index.html` |

Detalhe completo: CLAUDE.md **"PÁGINAS COM DATAS SAZONAIS"** e **"IMPACTO DA
PSU"**.

---

## ✅ CONCLUÍDO RECENTEMENTE

- **Cluster PSU — activação completa (Fase 2, Commits 1-5)** — 2026-08-16.
  Decreto-Lei n.º 166/2026, de 13 de agosto, publicado (Diário da
  República n.º 156/2026, Série I), em vigor desde 14/08/2026, produção
  de efeitos a **31/12/2026** (artigo 63.º — corrige o "1 de janeiro de
  2027" citado antes do decreto-lei sair, ver CLAUDE.md "IMPACTO DA PSU").
  5 commits, cada um revisto e verificado a passar a suite completa antes
  do seguinte:
  - **Commit 1** — as 6 páginas existentes do cluster actualizadas com
    valores reais do decreto-lei.
  - **Commit 2** — 2 páginas novas: `como-pedir-psu.html`,
    `calendario-pagamentos-psu.html`.
  - **Commit 3** — `simulador-psu.html` activado: `robots` de
    `noindex,nofollow` para `index,follow`, fórmula real implementada e
    testada (18 golden tests), banner de vigência ligado a
    `data_producao_efeitos` do YAML, artigo 17.º (habitação) marcado
    explicitamente "não considerado" — nunca inventado.
  - **Commit 4** — cross-links das 13 prestações extintas nas 3 páginas
    com página própria (`rsi.html`, `subsidio-desemprego.html`,
    `subsidio-parental.html` — 7 das 13 sem página própria, sem cross-link
    por desenho); teste fail-safe da majoração (valor não reconhecido →
    zero, nunca as duas em simultâneo); `sincronizar_nav.py` confirmado
    sem duplicados; banner sazonal da homepage actualizado; 2 entradas
    obsoletas em `data/clusters.json` corrigidas e propagadas a 12
    páginas via `sincronizar_clusters.py`.
  - **Commit 5** — esta entrada + fecho/reconfiguração do sentinela
    `dre_psu` (ver abaixo) + correcção do "1 jan 2027" em `CLAUDE.md`.

  **Sentinela `dre_psu`**: achado real nesta sessão — sem corte de
  recência, `_detectar_decreto_psu()` re-dispararia todos os dias sobre o
  próprio DL 166/2026 já conhecido (mesma classe de falso positivo do
  PAER, Issue #73). Corrigido com `data_minima="2026-08-16"` hardcoded
  dentro da função (nunca no dict de `FONTES_PLAYWRIGHT`, que
  `tests/test_dre_habitacao_watchlist.py::test_dre_psu_continua_a_usar_o_mecanismo_antigo_intocado`
  tranca à forma exacta de antes) — a fonte mantém-se activa como rede de
  segurança para um decreto-lei futuro sobre a PSU. Novo sentinela irmão,
  `dre_psu_regulamentacao`: pesquisa pelo número do decreto-lei
  (`"Decreto-Lei n.º 166/2026"`), filtrando só Portarias
  (`detectar_portaria`, mesmo mecanismo do `dre_ias`) — cobre os 2 pontos
  que o próprio diploma deixa por regulamentar (art. 17.º renda de
  referência; arts. 32.º/59.º procedimentos e meios de prova),
  confirmados directamente pelo Nuno. Nunca calibrado contra um runner
  real nesta sessão. 15 testes novos em
  `tests/test_dre_psu_regulamentacao.py`.

  Suite completa + coerência do cluster (breadcrumb/nav/datas/anos) +
  guardrail de skips + `ruff` + `verificar_datas.py` (0 alertas), todos
  verdes antes de cada commit. Sem merge — PR aberto contra `main`
  aguarda revisão final do Nuno, commit-a-commit. Ver CLAUDE.md
  "IMPACTO DA PSU" para o detalhe completo de cada commit.

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
