# Registo de Erros e Correcções — Tens Direito

---

## Correcção #001

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** A secção "O que cobre" listava "Manuais escolares em regime de empréstimo gratuito" como benefício exclusivo do Escalão A, e "Manuais escolares em regime de empréstimo (parcial)" para o Escalão B. Esta informação estava errada.
**Correcção aplicada:** Os manuais escolares são gratuitos para TODOS os alunos do ensino público via programa MEGA (Manuais Escolares Gratuitos), independentemente do escalão ASE. A secção foi corrigida e foi adicionado bloco informativo sobre o MEGA com link para mega.mec.pt.
**Fonte que confirmou a correcção:** CLAUDE.md do repositório — "ATENÇÃO CONFIRMADA: manuais gratuitos para TODOS os alunos do ensino público, independentemente de escalão ASE"
**Data de publicação da correcção:** 23 de junho de 2026

---

## Correcção #002

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** O passo 1 do "Como candidatar" indicava que os encarregados de educação devem juntar "declaração de IRS ou última declaração de rendimentos". O mesmo erro estava no JSON-LD HowTo (passo 1).
**Correcção aplicada:** A declaração exigida na candidatura à ASE é emitida pela Segurança Social (não é a declaração de IRS). O texto foi corrigido em ambos os locais (HTML visível e JSON-LD) para "declaração de rendimentos emitida pela Segurança Social (pedida em seg-social.pt ou num balcão da SS)".
**Fonte que confirmou a correcção:** CLAUDE.md do repositório — "ATENÇÃO: a declaração que os EE entregam é emitida pela Segurança Social, não é declaração de rendimentos própria"
**Data de publicação da correcção:** 23 de junho de 2026

---

## ~~Aviso de verificação pendente #001~~ — RESOLVIDO

**Data de detecção:** 23 de junho de 2026
**Data de resolução:** 23 de junho de 2026
**Página afectada:** abono-de-familia.html
**Situação inicial:** Valores da tabela calculados sem fetch confirmado (seg-social.pt devolveu HTTP 403 automaticamente). Marcados com [VERIFICAR].
**Resolução:** Valores confirmados manualmente pelo utilizador em seg-social.pt/abono-de-familia a 23/06/2026. Tabela completamente restruturada com os valores reais por faixa etária (IAS 2026 = 537,13 €). Limite do 1.º escalão corrigido: 1 IAS (537,13 €), não 2 IAS como estava. Faixas etárias alinhadas com a fonte oficial. Marcador [VERIFICAR] removido. JSON-LD FAQ atualizado com os valores correctos.

---

## Página em falta #001

**Data de detecção:** 23 de junho de 2026
**Situação:** bolsa-de-merito.html foi referenciada para revisão mas não existe no repositório.
**Acção necessária:** Criar a página com base nas regras do CLAUDE.md, fazendo fetch prévio a dge.mec.pt/bolsa-de-merito antes de redigir qualquer valor ou condição.

---

## Correcção #004

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** 4 ocorrências do link `https://www.dge.mec.pt/acao-social-escolar` no HTML público. Este URL devolve 403 (restrito/requer autenticação) — nunca deve aparecer como link clicável numa página pública.
**Correcção aplicada:** Todas as ocorrências substituídas por `https://www.dge.mec.pt` com texto âncora "Direção-Geral da Educação (dge.mec.pt)". Adicionada nota "Para informação sobre ASE, consulta a secretaria da tua escola ou o portal da DGE." nos locais relevantes.
**Fonte que confirmou a correcção:** Skill `verificar-url` — regra 401/403: página existe mas é restrita, NUNCA usar no HTML público.
**Data de publicação da correcção:** 23 de junho de 2026

## Correcção #005 — 2026-06-24

**Links DRE e CP corrigidos para homepage**

- `bolsa-de-merito.html`: subpath `dre.pt/pesquisa?q=bolsa+merito+ensino+basico` → `https://dre.pt`
- `passe-sub23.html`: subpath `cp.pt/passageiros/pt/consultar-horarios/precos/passes-sub18-e-sub23` → `https://www.cp.pt`

Regra aplicada: quando um subpath de portal oficial devolve erro, usar a homepage do domínio.

## Correcção #006 — 2026-06-24

**`app.seg-social.pt/ptss/ssd` substituído por `seg-social.pt` em todas as páginas**

- **Erro:** O URL `https://app.seg-social.pt/ptss/ssd` (Segurança Social Direta) foi usado como link público em `rsi.html` e `subsidio-desemprego.html`. Este URL devolve 404 para utilizadores não autenticados — é uma área privada que exige login prévio.
- **Páginas corrigidas:** `rsi.html` (3 ocorrências), `subsidio-desemprego.html` (7 ocorrências)
- **Substituição aplicada:** `https://app.seg-social.pt/ptss/ssd` → `https://www.seg-social.pt`
- **Texto âncora actualizado:** "Segurança Social Direta" → "Segurança Social Direta (seg-social.pt)"
- **Regra adicionada ao CLAUDE.md:** tabela de URLs PROIBIDOS com `app.seg-social.pt/ptss/ssd` marcado como área privada.

## Correcção #007 — 2026-06-24

**`acao-social-escolar.html` — NEE removido, visitas e material corrigidos, legislação completa**

- **Correcção 1 — NEE removida:** A frase "Alunos com necessidades educativas especiais (NEE) poderão ter acesso independentemente do escalão de rendimento — confirmar junto do agrupamento" foi removida. Informação não confirmada na legislação base (Despacho n.º 8452-A/2015 e alterações).
- **Correcção 2 — Visitas de estudo:** Substituída menção genérica a "isenção ou redução de custos" pela regra real: os encarregados pagam sempre; os alunos com escalão são ressarcidos posteriormente até ao limite anual (Escalão A: 20 €/ano letivo; Escalão B: 10 €/ano letivo).
- **Correcção 3 — Material escolar:** Actualizados os valores do apoio de material de desgaste (cadernos, lápis, mochilas — NÃO livros): Escalão A 16 €/ano letivo; Escalão B 8 €/ano letivo.
- **Correcção 4 — Nota MEGA:** Reforçado o bloco MEGA com explicação de que o programa abrange todos os alunos do ensino público desde 2016/2017 e que o apoio de "material escolar" da ASE é exclusivamente para material de desgaste.
- **Correcção 5 — Legislação:** Substituídas fontes genéricas pela legislação base completa: Despacho n.º 8452-A/2015, Despacho n.º 5296/2017, Despacho n.º 7255/2018, com links para diariodarepublica.pt.
- **Correcção 6 — JSON-LD:** FAQ sobre manuais actualizada com distinção MEGA vs. material de desgaste e valores; adicionada pergunta/resposta sobre visitas de estudo com regra de ressarcimento posterior.

## Correcção #008 — 2026-06-24

**`subsidio-parental.html` — 9 erros críticos corrigidos após fact-checking externo**

Fonte das correcções: relatório de fact-checking externo, verificado a 24/06/2026.

- **Correcção 1 — Dias do pai (tipo):** "28 dias úteis" corrigido para "28 dias de calendário (incluindo fins de semana e feriados)".
- **Correcção 2 — Distribuição dos 28 dias:** Substituída a divisão errada "20 dias imediatos + 8 dias nos primeiros 30 dias" pela divisão correcta: 7 dias seguidos imediatamente após o nascimento + 21 dias seguidos ou interpolados (blocos mínimos de 7 dias) nos primeiros 42 dias.
- **Correcção 3 — 7 dias facultativos do pai:** Adicionado o direito a 7 dias facultativos adicionais, gozados em simultâneo com a licença da mãe nas primeiras 6 semanas após o parto, pagos a 100%. Total máximo licença exclusiva do pai: 35 dias (28+7).
- **Correcção 4 — Fórmula RR:** Fórmula corrigida para "soma dos salários brutos dos 6 meses mais antigos dos 8 meses anteriores ao mês de início da licença ÷ 180". Adicionado método alternativo para trabalhadores com menos de 6 meses de contribuições.
- **Correcção 5 — Tabela de modalidades:** Reformulação das descrições para reflectir o critério correcto de partilha (pai goza ≥30 dias seguidos ou 2×15; ou ≥60 dias seguidos ou 2×30). Adicionada nota obrigatória: na modalidade de 180 dias a 90%, os 60 dias do pai estão incluídos nos 180 dias totais.
- **Correcção 6 — Pedido online:** Substituída referência ao formulário RP 5049-DGSS como canal online pelo formulário electrónico dinâmico da SS Direta (seg-social.pt). RP 5049-DGSS mantido como referência para canal presencial/correio.
- **Correcção 7 — Acompanhamento legislativo:** Substituído link para dre.pt (publica apenas diplomas promulgados) pelo link correcto: parlamento.pt. Aviso actualizado com estado actual da proposta.
- **Correcção 8 — Subsídio Social Parental:** Adicionadas condições de recursos obrigatórias: rendimento per capita máximo 80% IAS (429,70 €/mês em 2026); património mobiliário máximo 240 × IAS (128.911,20 € em 2026).
- **Correcção 9 — Estado da proposta legislativa:** Aviso actualizado com estado actual: aprovado generalidade 23 jan 2026, em discussão especialidade na Comissão de Trabalho (10.ª), audição ISS realizada 26 jun 2026, NÃO em vigor.

## Correcção #009 — 2026-06-24

**`abono-de-familia.html` — 12 erros corrigidos, valores actualizados Portaria n.º 60/2026/1**

Fontes: Portaria n.º 60/2026/1, de 5 de fevereiro · Instituto da Segurança Social · verificado 24/06/2026.

- **Correcção 1 — Estrutura etária:** Substituída a segmentação obsoleta (até 12 meses / 1–3 anos / 3–6 anos / 6–24 anos) pela estrutura oficial com 3 grupos: ≤ 36 meses / > 36 a ≤ 72 meses / > 72 meses.
- **Correcção 2 — Valores mensais:** Substituída toda a tabela de valores pelos dados da Portaria n.º 60/2026/1: 1.º escalão ≤36m 190,98 €; 2.º escalão ≤36m 161,65 €; 3.º escalão ≤36m 132,07 €; 4.º escalão ≤36m 88,43 €; valores completos por escalão e grupo etário.
- **Correcção 3 — Metodologia escalões:** Substituída a indicação errada de "rendimento mensal per capita ÷ IAS" pela fórmula do Rendimento de Referência anual: RR = rendimento bruto anual ÷ (n.º crianças + 1). Adicionados limites anuais para novos pedidos 2026 (IAS 2025=522,50€), pedidos activos (IAS 2024=509,26€) e reavaliações (IAS 2026=537,13€).
- **Correcção 4 — 4.º escalão perde direito aos 72 meses:** Adicionada nota obrigatória: crianças no 4.º escalão perdem o direito ao abono quando completam 72 meses (6 anos).
- **Correcção 5 — Majorações:** Adicionada secção de majorações: família monoparental +50%; famílias numerosas 2+ crianças ≤36m (+64,96 € a +39,28 € conforme escalão); 3+ crianças ≤36m 1.º escalão +106,96 €.
- **Correcção 6 — Garantia para a Infância:** Adicionada nova secção: crianças 1.º escalão com RR < 2.631,94 €/ano têm garantido 127,33 €/mês; complemento pago automaticamente pela SS sem necessidade de pedido.
- **Correcção 7 — Atribuição automática:** Adicionada informação sobre atribuição automática para recém-nascidos (proposta enviada à SS Direta após registo civil e CC; pais aceitam expressamente).
- **Correcção 8 — Prazo:** Actualizado para 6 meses a contar do 1.º dia do mês seguinte ao nascimento; esclarecido que pedido fora do prazo perde retroactivos.
- **Correcção 9 — Data de pagamento:** Adicionado que o pagamento é tipicamente no dia 16 de cada mês.
- **Correcção 10 — Limite de património:** Adicionada condição de acesso: património mobiliário máximo 240 × IAS = 128.911,20 € em 2026.
- **Correcção 11 — Trabalhadores independentes:** Adicionada regra: dívida à SS não regularizada em 3 meses após suspensão → direito perde-se definitivamente.
- **Correcção 12 — Formulário reavaliação:** Adicionada referência ao Modelo GF58-DGSS para pedidos de reavaliação de escalão a meio do ano.

