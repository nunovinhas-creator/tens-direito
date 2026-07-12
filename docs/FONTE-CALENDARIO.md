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

## ⚠️ ACHADO DECISIVO (diagnóstico de 2026-07-12, 4 rondas num runner real)

**A fonte oficial pública deixou de existir com a migração do portal.**
Provado com fetch/Playwright reais (runs do workflow temporário
`diagnostico-calendario-temp.yml`, apagado no fim):

1. **Portal antigo morto**: a notícia mensal, `/noticias` e
   `/pagamentos2` redireccionam TODOS para o gateway da SSD
   (`/ptss/pssd/home?r=...`) — com `requests` devolvem só a shell de
   cookies (213 chars); com Playwright a SPA carrega a home e **não
   restaura o recurso pedido** (o parâmetro `r=` é ignorado).
2. **Portal novo sem calendário público**: a listagem
   `/ptss/pssd/noticias` renderiza (13 notícias, sem paginação) mas
   **nenhuma** é de datas de pagamento; slugs candidatos dão 404 real
   (`/ptss/fraw/errors/404`); a página "Calendário" de
   `pagamentos-dividas/valores-a-receber` é uma funcionalidade com
   login ("os seus próximos pagamentos"), não uma publicação mensal.
3. A notícia de julho existia no portal antigo (indexada pelo Google)
   — morreu com a migração, dias depois de publicada.

**Consequência**: scraping automático da fonte oficial é hoje
IMPOSSÍVEL, não apenas frágil. O fluxo mensal é o fallback
semiautomático que a spec previa, com uma sonda que detecta se a
publicação oficial reaparecer.

## Fase 3 — IMPLEMENTADA (2026-07-12): fluxo semiautomático

`.github/workflows/calendario-mensal.yml` + `scripts/verificar_calendario_mensal.py`:

1. **Dia 25 (06:00 UTC) + retry dia 28**: alvo = mês seguinte. Se
   `data/calendario_pagamentos.json` já o tem (posto por sessão manual
   verificada) → injecção idempotente + testes + commit confinado.
   Se não tem → sonda `/ptss/pssd/noticias` (Playwright) à procura de
   uma notícia de datas de pagamento reaparecida, e abre/actualiza a
   Issue `calendario-manual` (título com o mês alvo — dedup por
   título; corpo com o relatório da sonda + prompt pronto a colar).
   **Nunca commit parcial, nunca dados inventados.**
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
