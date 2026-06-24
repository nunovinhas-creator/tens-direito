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

## Correcção #010 — 2026-06-24

**`subsidio-desemprego.html` — 11 erros críticos corrigidos**

Fonte: DL n.º 220/2006 + Instituto da Segurança Social + IAS 2026 (537,13 €) · verificado 24/06/2026.

- **Correcção 1 — Prazo de garantia:** Corrigido para 360 dias de trabalho com registo nos 24 meses imediatamente anteriores à data de desemprego.
- **Correcção 2 — Prazo do pedido:** Corrigido para 90 dias consecutivos a contar do registo no IEFP. Pedido fora do prazo não perde o direito na totalidade — o período de concessão é reduzido pelo número de dias de atraso.
- **Correcção 3 — Fórmula de cálculo:** Corrigida para soma dos primeiros 12 meses dos últimos 14 meses anteriores ao desemprego ÷ 360 = Remuneração de Referência diária. Subsídio diário = RR × 65%.
- **Correcção 4 — Limites 2026:** Adicionados todos os limites: mínimo 537,13 € (100% IAS); mínimo absoluto 349,13 € (65% IAS, quando RR líquida < IAS); máximo 1.342,83 € (2,5×IAS); máximo majorado 1.477,11 € (+10% quando ambos os cônjuges estão desempregados com dependentes).
- **Correcção 5 — Subsídio Social de Desemprego:** Adicionadas condições de recursos: rendimento per capita máximo 80% IAS (429,70 €/mês); duração 180 dias/12 meses; limite de património mobiliário 240×IAS = 128.911,20 €.
- **Correcção 6 — Justa causa:** Distinguidas as duas situações: despedimento disciplinar pelo empregador = voluntário = SEM direito; resolução pelo trabalhador com justa causa = involuntário = COM direito + indemnização 15–45 dias/ano.
- **Correcção 7 — Mútuo acordo:** Adicionadas as condições legais: apenas em reestruturações económicas; PME: máximo 3 trabalhadores ou 25% do efectivo; grandes empresas: máximo 62 ou 20%, absoluto 80/triénio.
- **Correcção 8 — Mobilidade UE:** Adicionado procedimento completo: comunicar ao IEFP 4 semanas antes da saída; obter Documento Portátil U2; registar no serviço de emprego do país de destino em 7 dias; portabilidade máxima 3 meses, extensível mais 3 meses (pedir 30 dias antes do término).
- **Correcção 9 — Deveres do beneficiário:** Adicionada regra: comunicar qualquer facto relevante em 5 dias úteis; baixa médica com CIT ou auto-declaração SNS (máx. 3 dias, máx. 2×/ano); incumprimento → 90 dias sem re-inscrição.
- **Correcção 10 — Trabalhadores independentes:** Adicionadas duas modalidades distintas: economicamente dependentes (≥50% receitas de um cliente) → 360 dias/24 meses; cessação de actividade involuntária → 720 dias/48 meses, taxa 25,2%.
- **Correcção 11 — Declaração do empregador:** Adicionado Modelo RP5044-DGSS como documento obrigatório; se empregador recusar emitir, ACT emite em 30 dias.

## Correcção #011 — 2026-06-24

**`rsi.html` — 7 erros corrigidos**

Fontes: Portaria n.º 71/2026/1, de 13 de fevereiro · Lei n.º 13/2003, de 21 de maio · verificado 24/06/2026.

- **Correcção 1 — Formulário RSI 1 (crítico):** Todas as referências a "formulário RSI 28" substituídas por "formulário RSI 1" (Requerimento inicial). RSI 28 é a Declaração de Alterações, usada após aprovação. RSI 1 é o formulário para o pedido inicial. Corrigido no HTML visível, no passo a passo, no bloco de documentos e no JSON-LD HowTo.
- **Correcção 2 — Prazo de 45 dias:** Substituída a indicação errada "a Segurança Social tem 45 dias para decidir" pela regra correcta: "após a aprovação, o Contrato de Inserção deve ser formalizado com o Núcleo Local de Inserção (NLI) no prazo de 45 dias seguidos". Corrigido no HTML e no JSON-LD HowTo.
- **Correcção 3 — Valores oficiais 2026 confirmados:** Removido o aviso de dúvida sobre valores. A Portaria n.º 71/2026/1, de 13 de fevereiro, confirmou o RSI base em 247,56 € (46,09% do IAS 537,13 €): titular 247,56 €; adulto adicional 173,29 € (70%); menor 123,78 € (50%).
- **Correcção 4 — Limite de património confirmado:** Removido aviso de dúvida. O limite de 32.227,80 € (60 × IAS 537,13 €) está confirmado para 2026.
- **Correcção 5 — Exemplo prático actualizado 2026:** Substituído exemplo com valores 2025 (654,03 €) por valores 2026 confirmados: 2 adultos + 2 crianças = 668,41 €; rendimentos 450,50 €; RSI = 217,91 €/mês. Adicionada nota sobre rendimentos de trabalho (80% após contribuições).
- **Correcção 6 — FAQ acumulação com subsídio de desemprego:** Actualizado o item da tabela de acumulação com regra explícita: subsídio conta 100% nos rendimentos; se exceder valor máximo RSI, RSI = 0; acumulação útil em agregados grandes com subsídios baixos. Adicionado novo bloco FAQ com exemplo ilustrativo.
- **Correcção 7 — FAQ menores de 18 anos:** Actualizada a condição de elegibilidade: "rendimentos próprios superiores a 70% do RSI base = 173,29 €/mês em 2026 (Portaria n.º 71/2026/1)" — valor concreto explicitado. Adicionados ao JSON-LD FAQPage: formulário RSI 1, prazo 45 dias (contrato inserção), valor RSI 2026. Fonte adicionada: Portaria n.º 71/2026/1, de 13 de fevereiro (diariodarepublica.pt).

## Fact-checking MEGA — 2026-06-24

**`manuais-escolares-mega.html` — sem erros críticos; 5 nuances adicionadas**

Fonte: IGeFE / Ministério da Educação · verificado 24/06/2026.

- **Nuance 1 — Senha Portal das Finanças:** Adicionada nota no passo de registo: "Tens de ter à mão a senha de acesso ao Portal das Finanças do Encarregado de Educação para fazer esta ligação no primeiro acesso."
- **Nuance 2 — Vales dependem do fecho de turmas:** Adicionada nota na secção de calendário: os vales só aparecem depois de a escola ter inserido e fechado oficialmente as turmas do ano letivo; se a data indicativa já passou sem vales, aguardar que a escola finalize os dados.
- **Nuance 3 — 1.º ciclo sempre manuais novos desde 2024:** Confirmada e reforçada a regra com data explícita: "desde 2024, alunos do 1.º ciclo têm sempre manuais novos e não precisam de devolver".
- **Nuance 4 — Voucher indica novo vs reutilizado:** Adicionado bloco informativo: o próprio vale especifica "Livraria" (manual novo) ou "Escola" (manual reutilizado); atribuição aleatória pelo sistema para 5.º ao 12.º ano.
- **Nuance 5 — Bloqueio automático por NIF do educando:** Reforçada a secção de devolução: bloqueio é automático (sistema cruza com escolas) e afecta o NIF do educando, não o do encarregado. JSON-LD actualizado com as nuances 1, 3, 4 e 5.

## Fact-checking Bolsa de Mérito — 2026-06-24

**`bolsa-de-merito.html` — sem erros críticos; 1 nuance adicionada**

Fonte: Despacho n.º 8452-A/2015, art. 14.º · verificado 24/06/2026.

- **Nuance 1 — Arredondamento da média:** Adicionada nota após a linha da média ≥ 14 valores para o 10.º/11.º ano: "A média é arredondada às unidades para efeitos de elegibilidade. Um aluno com 13,5 de média vê a nota arredondada para 14 e torna-se elegível." Com referência ao Despacho n.º 8452-A/2015, art. 14.º.

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

