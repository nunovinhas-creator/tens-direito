# FONTE — Calendário de Pagamentos da Segurança Social

Documento da Fase 0 de `CALENDARIO-PAGAMENTOS-SPEC.md` (2026-07-12).
Privado, nunca servido (é `.md`, fora do sitemap/pesquisa — mesma
categoria de `ROADMAP.md`).

## Fonte oficial identificada

A Segurança Social publica o calendário mensal de pagamentos em **dois
locais oficiais**:

### 1. Notícia mensal no portal antigo (Liferay) — fonte primária recomendada

- **Padrão de URL**:
  `https://www.seg-social.pt/noticias/-/asset_publisher/kBZtOMZgstp3/content/datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-<mês>`
- **Formato**: HTML (artigo de notícia com a lista de datas por prestação
  e por método — transferência bancária / vale de correio).
- **Cadência**: publicada tipicamente nos últimos dias do mês anterior ou
  nos primeiros dias do próprio mês (evidência: a imprensa que reproduz o
  calendário publica nessa janela, citando sempre "a Segurança Social
  publicou").
- **⚠️ Fragilidade conhecida do URL**: o slug da notícia nem sempre é
  consistente — encontrados no índice do Google casos como
  `...-em-julho` a servir o artigo de **agosto** (slug reciclado:
  `datas-de-pagamento-dos-subsidios-sociais-em-julho` com título
  "…em Agosto") e sufixos numéricos (`...-em-setembro-2`). **Nunca
  assumir que o slug corresponde ao mês** — validar sempre o mês/ano no
  conteúdo, nunca no URL.

### 2. Página "Calendário" do portal novo (SPA OutSystems/`/ptss/pssd/`)

- **URL**: `https://www.seg-social.pt/ptss/pssd/menu/pagamentos-dividas/valores-a-receber/calendario`
- **Formato**: SPA — mesma família dos deep-links `/ptss/pssd/menu/...`
  já usados por `seg_social_abono`/`seg_social_rsi` no scraper
  (funcionam num runner real via Playwright com espera explícita pela
  âncora e perfil `headers_custom=False` — ver CLAUDE.md
  "SEG-SOCIAL — ESTRATÉGIA DE FETCH").
- Existe também `https://www.seg-social.pt/pagamentos2` (portlet antigo
  com parâmetro de data `..._datapagsub=MM-AAAA`) — potencial fonte
  estruturada, por confirmar num runner real.

## Acessibilidade por ambiente

- **Sessão de desenvolvimento**: `seg-social.pt` está **bloqueado**
  (403 da política de rede, `WebFetch` e `curl` — mesma limitação
  documentada no CLAUDE.md para todas as sessões). Só `WebSearch`
  funciona.
- **Runner GitHub Actions**: os deep-links `/ptss/pssd/` do mesmo
  domínio já são scrapados com sucesso todos os dias pelo
  `pipeline-diario.yml` — é expectável que a notícia mensal e a página
  Calendário sejam acessíveis de um runner. **Por confirmar com fetch
  real na sessão da Fase 3** antes de decidir o mecanismo definitivo.

## Verificação dos dados desta sessão (julho 2026)

Sem acesso directo à fonte nesta sessão, as datas de julho de 2026
foram trianguladas por **≥5 fontes independentes** que reproduzem
explicitamente o calendário oficial da Segurança Social (mesmo padrão
já usado no site para fontes que devolvem 403 a bots — a página cita
sempre o URL oficial como fonte):

- economiafinancas.com — "Datas de Pagamento das Prestações Sociais de
  Julho de 2026"
- executivedigest.sapo.pt — "Recebe apoios da Segurança Social? Veja o
  calendário de pagamentos do mês de julho"
- aciab.pt — "Datas de Pagamento da Segurança Social em julho de 2026"
- noticiasaominuto.com / postal.pt / pplware.sapo.pt — artigos do mesmo
  calendário
- e-konomista.pt — confirma o subsídio de férias dos pensionistas pago
  com a pensão de julho, na mesma data

Todas coerentes entre si: 3, 7, 8, 16, 21, 23 e 28 de julho (detalhe em
`data/calendario_pagamentos.json`). Método: tudo pago por transferência
bancária e vale de correio, excepto o apoio à renda (só transferência).

**Agosto de 2026 deliberadamente NÃO incluído**: as únicas fontes
encontradas (2 blogs de promoções) tanto podem reproduzir o calendário
oficial como tê-lo *previsto* pelas regras de dias fixos + antecipação
de fim-de-semana — indistinguível sem a fonte oficial. Fica para a
sessão da Fase 3 (workflow do dia 25) ou para a corrida manual seguinte.

## Regras estruturais confirmadas (para validação futura)

- Dias fixos de referência: pensões/CSI/PSI/reembolso funeral dia 8;
  prestações familiares + 1.º pagamento desemprego/doença/parentalidade/
  ação social dia 16; FGADM dia 21; RSI + FGS dia 23; 2.º pagamento +
  cuidador informal dia 28 (aprox. — os dias exactos variam com o mês).
- Data ao fim-de-semana/feriado → antecipada para o dia útil anterior.
- Vale de correio: entrega é responsabilidade dos CTT, pode demorar
  mais alguns dias do que a data indicada.
- Apoio à renda: pago exclusivamente por transferência bancária.

Estas regras servem só para **validação de plausibilidade** na Fase 3
(um valor fora deste padrão exige confirmação extra) — nunca para
*gerar* datas. Datas geram-se apenas a partir da fonte oficial.

## ✅ FONTE PÚBLICA REAL ENCONTRADA (2026-07-12, pista do Nuno) — scraping automático

**`https://www.seg-social.pt/ptss/pssd/pagamentos`** — página PÚBLICA
oficial, sem login, provada num runner real (workflow temporário,
apagado no fim):

- `requests` (GET simples): **HTTP 200, NÃO redirecciona para o gateway
  de login** (`redirecciona p/ gateway SSD: False`) — ao contrário de
  `/pagamentos2` e do "Calendário" de valores-a-receber.
- SPA OutSystems com um **separador por mês** ("junho 2026",
  "julho 2026", "agosto 2026", …). Ao clicar num separador, mostra a
  tabela oficial desse mês: por cada dia, as prestações pagas e o método
  (transferência bancária / vale de correio).
- As datas são publicadas **antes do início do mês** (agosto já lá
  estava a meio de julho, com as antecipações de fim-de-semana já
  aplicadas — ex.: pensões antecipadas de 8 para 7 ago porque 8 é
  sábado).
- Nota estrutural: a tabela **não** é um `<table>` (`tabelas no DOM: 0`)
  — é uma lista de blocos por dia. O cabeçalho do dia aparece antes das
  linhas de prestação renderizarem, por isso `raspar_mes` espera pelo
  cabeçalho do mês **E** por uma linha de método, mais um settle, antes
  de ler (ver `scripts/scraper_calendario.py`).

### Correcção à conclusão anterior (mesmo dia, mais cedo)

A ronda de diagnóstico anterior concluiu, erradamente, que "a fonte
pública deixou de existir / scraping é impossível" — porque testou
`/pagamentos2`, `/noticias` e o "Calendário" de valores-a-receber (que
de facto redireccionam para login ou não têm a tabela), mas **não**
testou `/ptss/pssd/pagamentos`. O Nuno apontou esse URL; um novo
diagnóstico confirmou-o como fonte pública real. **Scraping automático
é possível** — implementado em `scripts/scraper_calendario.py`, com o
fluxo manual (Issue + prompt) a ficar apenas como *fallback* se o
scraper falhar (mês ainda não publicado, prestação nova fora da
allow-list, layout mudado). Provado ponta-a-ponta: agosto de 2026 foi
raspado ao vivo, validado, injectado e commitado automaticamente pelo
`calendario-mensal.yml` (run 29201776013).

## Fase 3 — IMPLEMENTADA (2026-07-12): fluxo semiautomático

`.github/workflows/calendario-mensal.yml` + `scripts/verificar_calendario_mensal.py`:

1. **Dia 25 (06:00 UTC) + retry dia 28**: alvo = mês seguinte. Se
   `data/calendario_pagamentos.json` já o tem → injecção idempotente +
   testes + commit confinado. Se não tem → **tenta o scraper automático**
   (`scripts/scraper_calendario.py` sobre `/ptss/pssd/pagamentos`); se
   obtiver o mês, grava-o no JSON e segue o caminho `dados_ok`. Só se o
   scraper falhar (mês ainda não publicado, prestação nova fora da
   allow-list `NOME_PARA_SLUG`, layout mudado) é que cai para o
   *fallback* manual: sonda `/ptss/pssd/noticias` + abre/actualiza a
   Issue `calendario-manual` (dedup por título; corpo com o erro do
   scraper + sonda + prompt pronto). **Nunca commit parcial, nunca
   dados inventados, nunca uma prestação descartada em silêncio.**
2. **Dia 1 (05:30 UTC)**: alvo = mês corrente. Quando o JSON já tem o
   mês novo, a injecção vira a página automaticamente e o commit segue
   — sem este disparo, a página ficava no mês velho até alguém correr
   o script (com o canário do CI vermelho a exigi-lo).
3. **Guardrail próprio**: falha o job se qualquer ficheiro fora de
   `data/calendario_pagamentos.json` + a página aparecer modificado
   antes do commit (âmbito disjunto de todos os outros workflows com
   push, mesmo padrão de `shadow-daily.yml`). `concurrency:
   main-writes` partilhado com os outros workflows de push.
4. Ao ficar `dados_ok`, fecha automaticamente a Issue
   `calendario-manual` do mês (mesmo padrão de fecho automático de
   `fonte-bloqueada`).
5. Pós-push: `garantir_deploy_pages.sh` + smoke test inline (mesmo
   padrão do pipeline diário — pushes de GITHUB_TOKEN não disparam
   workflows `on: push`).

## Decisão og:title estável (tomada nesta sessão)

O `<title>`/meta description da página incluem o mês corrente (spec),
mas o `og:title` é **estável, sem mês** ("Calendário de Pagamentos da
Segurança Social") — `tests/test_og_image.py` exige que o manifest das
imagens og bata com o `og:title`; um og:title mensal obrigaria a
regenerar a imagem og (Chromium) todos os meses no workflow. Com
og:title estável, a atualização mensal toca só em texto.
