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

## Decisão Fase 3 (registada, a executar na próxima sessão)

**Fluxo semiautomático com fallback obrigatório** (lição do `dre_psu`:
nunca scraper frágil sem fallback):

1. Workflow agendado (dia 25, 06:00 UTC + retry dia 28) tenta obter o
   calendário do mês seguinte num runner real — 1.ª tentativa à notícia
   mensal (HTML simples), 2.ª à página SPA (Playwright + âncora).
2. Validação dura antes de qualquer commit: mês/ano == mês seguinte
   esperado (extraído do CONTEÚDO, nunca do URL — ver fragilidade do
   slug acima); dias 1-31; prestações não vazias; slugs todos na
   allow-list `PRESTACOES` de `scripts/atualizar_calendario.py`.
3. Falha em qualquer passo → Issue `calendario-manual` com prompt
   pronto a colar (padrão do fluxo PSU), **nunca commit parcial**.
4. O workflow novo escreve APENAS `data/calendario_pagamentos.json` +
   `calendario-pagamentos-seguranca-social.html` (só entre marcadores
   `CAL:META`/`CAL:CORPO`) — âmbito disjunto dos outros workflows com
   push, guardrail próprio no workflow (mesmo padrão de
   `shadow-daily.yml`). Nota: a página é HTML "manual" aos olhos do
   guardrail do `pipeline-diario.yml` — o workflow novo é separado e
   tem de declarar o seu próprio âmbito.

## Decisão og:title estável (tomada nesta sessão)

O `<title>`/meta description da página incluem o mês corrente (spec),
mas o `og:title` é **estável, sem mês** ("Calendário de Pagamentos da
Segurança Social") — `tests/test_og_image.py` exige que o manifest das
imagens og bata com o `og:title`; um og:title mensal obrigaria a
regenerar a imagem og (Chromium) todos os meses no workflow. Com
og:title estável, a atualização mensal toca só em texto.
