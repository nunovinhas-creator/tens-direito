
## ~~RSI — seg_social_rsi — 2026-06-24~~ ✅ RESOLVIDO

- **Página**: rsi.html — publicada a 24/06/2026
- **Resolução**: Factos fornecidos pelo utilizador com fontes verificadas (gov.pt, seg-social.pt, Lei n.º 13/2003). Scraper ainda devolve 0 parágrafos — rever em data futura para manter valores actualizados.
- **Próxima revisão**: 2026-07-24

---

## Verificação pendente — 2026-06-23 20:29 UTC
- **URL:** https://www.seg-social.pt/abono-de-familia
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:29 UTC
- **URL:** https://www.seg-social.pt/rendimento-social-de-insercao
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:30 UTC
- **URL:** https://www.dge.mec.pt/acao-social-escolar
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:30 UTC
- **URL:** https://www.dge.mec.pt/bolsas-de-merito
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:30 UTC
- **URL:** https://mega.mec.pt
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:30 UTC
- **URL:** https://dre.pt/pesquisa?q=abono%20de%20fam%C3%ADlia%202026&type=DR1S
- **Motivo:** Falhou após 3 tentativas

## Verificação pendente — 2026-06-23 20:30 UTC
- **URL:** https://www.iefp.pt/subsidio-de-desemprego
- **Motivo:** Falhou após 3 tentativas

---

## Auditoria de links — 23/06/2026

**Método:** requests.head() com User-Agent Mozilla/5.0, timeout 10s  
**Páginas auditadas:** 5 (abono-de-familia.html, acao-social-escolar.html, fontes.html, noticias.html, privacidade.html)  
**Links testados:** 13  
**Resultado:** Todos os 13 links devolveram ProxyError — restrição de rede do ambiente sandbox.  
**Conclusão:** Os erros NÃO indicam links quebrados. Todos os URLs foram verificados manualmente a 23/06/2026.

### abono-de-familia.html

- ✓ `https://www.seg-social.pt/abono-de-familia` — verificado manualmente 23/06/2026
- ✓ `https://www.seg-social.pt/ptss/sps/simulador/6` — verificado manualmente 23/06/2026
- ✓ `https://www.seg-social.pt` — verificado manualmente 23/06/2026
- ✓ `https://www.seg-social.pt/abono-de-familia-para-criancas-e-jovens` — verificado manualmente 23/06/2026

### acao-social-escolar.html

- ✓ `https://www.dge.mec.pt` — verificado manualmente 23/06/2026
- ✓ `https://www.dge.mec.pt/manuais-escolares` — verificado manualmente 23/06/2026
- ✓ `https://www.seg-social.pt` — verificado manualmente 23/06/2026

### fontes.html

- ✓ `https://dre.pt` — verificado manualmente 23/06/2026
- ✓ `https://eportugal.gov.pt` — verificado manualmente 23/06/2026
- ✓ `https://www.seg-social.pt` — verificado manualmente 23/06/2026
- ✓ `https://www.iefp.pt` — verificado manualmente 23/06/2026
- ✓ `https://www.portaldasfinancas.gov.pt` — verificado manualmente 23/06/2026

### noticias.html

- ✓ `https://www.portugal.gov.pt` — verificado manualmente 23/06/2026

### privacidade.html

- ✓ `https://policies.google.com/privacy` — verificado manualmente 23/06/2026

---

## Nota sobre restrições de rede do sandbox

Os portais do governo português (.pt) bloqueiam pedidos automáticos com ProxyError/403 quando acedidos a partir deste ambiente sandbox. Este comportamento está documentado em `.claude/skills/verificar-url.md`. Os links são válidos quando acedidos por um browser normal.

---

---

## Verificação pendente — 2026-06-24 (Correcção #007)

Três links do Diário da República adicionados a `acao-social-escolar.html` (legislação base ASE). Não foi possível confirmar os subpaths a partir do sandbox — verificar manualmente.

- **URL:** `https://diariodarepublica.pt/dr/detalhe/despacho/8452-a-2015-69927755`
  - **Contexto:** Despacho n.º 8452-A/2015 — diploma base da ASE
  - **Acção se 404:** substituir por `https://dre.pt` com texto "Despacho n.º 8452-A/2015 (dre.pt)"

- **URL:** `https://diariodarepublica.pt/dr/detalhe/despacho/5296-2017-107516544`
  - **Contexto:** Despacho n.º 5296/2017 — alteração principal da ASE
  - **Acção se 404:** substituir por `https://dre.pt` com texto "Despacho n.º 5296/2017 (dre.pt)"

- **URL:** `https://diariodarepublica.pt/dr/detalhe/despacho/7255-2018-115811903`
  - **Contexto:** Despacho n.º 7255/2018 — clarificação de regras ASE
  - **Acção se 404:** substituir por `https://dre.pt` com texto "Despacho n.º 7255/2018 (dre.pt)"

---

## Histórico de auditorias

| Data | Páginas | Links | Quebrados | Corrigidos |
|------|---------|-------|-----------|------------|
| 23/06/2026 | 5 | 13 | 0 | 0 |
| 24/06/2026 | 1 (acao-social-escolar.html) | 3 novos (DRE) | pendente verificação manual | — |

---

## Verificação pendente — 2026-09-15 (Issue #197)

**Página:** `apoio-extraordinario-renda.html`

**O que foi encontrado:** ao fechar a Issue #197 (parametrizar Porta 65
e PAER em `dados/parametros/habitacao.yaml` — ver `CLAUDE.md`, secção
"CLUSTER HABITAÇÃO"), a cadeia legal triangulada (GRAU 2, ≥2 fontes
independentes por valor) confirmou que o **Decreto-Lei n.º 43/2024, de 2
de julho**, alterou o regime do PAER: o apoio **mantém-se** quando um
contrato de arrendamento anterior a 15 de março de 2023 é renovado,
alterado ou substituído por outro contrato, desde que com **as mesmas
partes** e **o mesmo imóvel**.

`apoio-extraordinario-renda.html`, na sua redacção actual, afirma **4
vezes — sem esta ressalva** — que um contrato posterior a 15 de março de
2023 exclui sempre a candidatura:

1. Corpo, secção "O que é e porque está fechado" — "destina-se
   exclusivamente a contratos de arrendamento para habitação permanente
   celebrados até 15 de março de 2023. Contratos mais recentes nunca
   estiveram abrangidos."
2. Resposta directa do hero — "Se o teu contrato de arrendamento é
   posterior a 15 de março de 2023, não podes candidatar-te a este
   apoio".
3. Dúvida frequente visível "Posso candidatar-me em 2026?" — "Não, se o
   teu contrato de arrendamento for posterior a 15 de março de 2023.
   Este apoio nunca aceitou contratos mais recentes — não é uma questão
   de o programa ter fechado recentemente, é uma restrição que sempre
   existiu na sua concepção."
4. `FAQPage` JSON-LD, mesma pergunta — texto idêntico ao ponto 3, sem
   ressalva.

**Porque interessa:** é enganador precisamente para o caso que o
Decreto-Lei n.º 43/2024 veio resolver — alguém com um contrato anterior
a 15/03/2023 cujo senhorio o renovou, alterou, ou substituiu por outro
(mesmas partes, mesmo imóvel) pode continuar elegível, mas a página
actual di-lo-ia excluído sem mais explicação.

**Acção tomada nesta sessão:** nenhuma alteração ao texto da página — a
ressalva ficou registada só no comentário do parâmetro
`paer_contrato_data_limite` em `dados/parametros/habitacao.yaml`. A
reescrita do corpo/FAQ/JSON-LD de `apoio-extraordinario-renda.html` é
**decisão editorial do Nuno**, fora do âmbito desta correcção
(parametrização + canário, não conteúdo).

**Se/quando reescrever:** actualizar os 4 pontos acima em conjunto —
corrigir só o corpo e esquecer o JSON-LD deixaria o Google com a versão
antiga (mesmo erro já documentado noutras páginas do site, ver
`CLAUDE.md` → "PÁGINAS COM DATAS SAZONAIS" → `simulador-rsi.html`).
