# Análise do Cluster Escolar — Tens Direito

Documento de análise, 2026-07-06. **Só análise — nenhuma página foi criada
nesta sessão.** Ficheiro privado, uso interno (mesma categoria de
`ROADMAP.md` — nunca servido, fora do sitemap/pesquisa.js).

Contexto: os temas escolares (MEGA, ASE, bolsa de mérito, prova escolar)
têm os melhores CTRs do site, em plena época de preparação do ano lectivo
2026/2027. Esta análise mapeia o que já existe, onde há lacunas reais, e
propõe no máximo 2 páginas novas — a decisão de implementar fica para o
Nuno.

---

## 1. Inventário do cluster `apoios-escolares`

Fonte única: `data/clusters.json` → cluster `apoios-escolares`, pillar
`p/apoios-escolares.html`.

| Página | Tipo | Nível de ensino | Destaque |
|---|---|---|---|
| `acao-social-escolar.html` | artigo | Todos os níveis (pré-escolar ao secundário) | ✅ destaque do cluster |
| `bolsa-de-merito.html` | artigo | Secundário (10.º-12.º ano) | — |
| `manuais-escolares-mega.html` | artigo | 1.º ao 12.º ano | — |
| `passe-sub23.html` | artigo | Todos (transportes, 4-23 anos) | — |
| `prova-escolar.html` | artigo | Beneficiários de abono/pensão de sobrevivência em idade escolar | — |
| `simulador-ase.html` | ferramenta | Todos os níveis | — |
| `p/apoios-escolares.html` | pillar | — | agrega os 6 acima |

### Interligação actual (links internos)

Confirmado por scan directo aos `href` de cada página: **o cluster está
100% interligado**. Os 5 artigos têm todos um link para os outros 4 (via
`RELACIONADOS`, gerado automaticamente por `sincronizar_clusters.py`) e
para o pillar; o simulador ASE liga ao artigo ASE e ao pillar; o pillar
liga aos 6. Não há nenhuma página órfã nem nenhum link em falta dentro do
cluster — o trabalho de interligação já está feito, esta análise não
encontrou lacunas de navegação.

Cross-links **manuais** (para além do `RELACIONADOS` automático) já
existentes e relevantes:
- `manuais-escolares-mega.html` → `acao-social-escolar.html` ("o apoio a
  material escolar adicional... poderá estar disponível através da Ação
  Social Escolar").
- `prova-escolar.html` explica a ligação entre a prova escolar e a
  suspensão de abono/bolsa de mérito/pensão de sobrevivência — é a página
  que mais depende de conceitos outras páginas do cluster (e do cluster
  "Família e Crianças", pelo abono).

---

## 2. Lacunas identificadas

### 2.1. Sem página dedicada: calendário único de prazos do ciclo escolar

Cada página do cluster já menciona o seu próprio prazo, mas **espalhado**:

| Prazo | Onde está mencionado hoje |
|---|---|
| Vales MEGA — final de julho a meados de agosto (2026/2027 por confirmar) | `manuais-escolares-mega.html` |
| Prova Escolar — até 31 de julho | `prova-escolar.html` |
| ASE — candidaturas até 30 de setembro | `acao-social-escolar.html` |
| Bolsa de mérito — candidaturas em setembro | `bolsa-de-merito.html` |

Não existe **nenhuma página** que responda a uma pesquisa do tipo "prazos
apoios escolares setembro 2026" ou "calendário candidaturas escola
2026/2027" com os 4 prazos juntos, por mês, num único sítio. É
precisamente o tipo de página que capta tráfego de quem já sabe que tem
"coisas da escola para tratar" mas não sabe exactamente quais nem quando
— um ângulo de busca genuinamente diferente dos 4 artigos existentes
(cada um responde "tenho direito a X?", nenhum responde "o que tenho de
fazer este mês?").

### 2.2. Sem página dedicada: apoios ao ensino superior (DGES)

**Achado mais forte desta análise**: o próprio pillar
(`p/apoios-escolares.html`) já admite esta lacuna, duas vezes, no próprio
texto publicado:

> "Para o ensino superior existem outros apoios — bolsas de ação social
> da DGES — que não estão cobertos neste guia."

A "bolsa de mérito" (`bolsa-de-merito.html`) é estritamente para o
secundário (10.º-12.º ano, requer escalão ASE + média mínima) — não cobre
nem substitui a **Bolsa de Ação Social do Ensino Superior** (DGES/SASE),
que é means-tested (não por mérito académico) e serve estudantes do
ensino superior. É uma prestação distinta, dentro do mesmo nicho
(apoios sociais, condição de recursos, procedimento burocrático), para um
público adjacente (jovens que acabam de sair do secundário — precisamente
os leitores de `bolsa-de-merito.html` e `acao-social-escolar.html` no ano
seguinte). Confirmado que nenhuma página do site actual menciona "DGES"
ou "bolsa de estudo do ensino superior" com informação substantiva (as 2
ocorrências fora do pillar são menções de passagem em `prova-escolar.html`
e `amim.html`, nunca um guia).

### 2.3. Gaps considerados e descartados (sem prioridade)

- **Seguro escolar obrigatório** — baixo volume de busca provável,
  fronteira difusa com "direito", não claramente um "apoio social".
- **Calendário escolar geral** (início/fim de período, feriados) —
  fora do nicho "prestações sociais e burocracia": é informação
  administrativa geral, mais território de portais de educação do que
  de um site de apoios sociais. Descartado por âmbito.
- **Transporte escolar municipal** (distinto do passe sub-23 nacional) —
  gerido caso a caso por cada câmara municipal, sem uma fonte oficial
  nacional única para citar; um artigo teria de ser genérico ao ponto de
  ter pouco valor prático. Descartado por falta de fonte primária única.

---

## 3. Recomendação — máximo 2 páginas novas

**Nenhuma página foi criada.** Ambas as propostas abaixo precisam de
fact-checking completo (fonte primária, nunca de memória) antes de
qualquer conteúdo ser escrito — esta análise não substitui esse passo.

### Proposta 1 — `calendario-escolar-apoios.html`

- **Query-alvo**: "prazos apoios escolares 2026/2027", "calendário
  candidaturas escola setembro", "quando pedir ASE bolsa manuais".
- **Ângulo**: página de referência rápida, organizada por mês (julho →
  outubro), cada prazo com 1-2 frases e link para o artigo completo
  correspondente — nunca duplica o conteúdo detalhado, só agrega e
  aponta.
- **Risco de canibalização**: baixo — os 4 artigos respondem "tenho
  direito e como peço", esta responde "quando", ângulo suficientemente
  distinto (mesmo padrão já usado para `autobaixa.html` vs.
  `baixa-medica-subsidio-doenca.html`, ver CLAUDE.md "GATILHO
  AUTOBAIXA").
- **Ligação ao cluster**: entra em `data/clusters.json` como `tipo:
  "artigo"` no cluster `apoios-escolares` — herda automaticamente
  `RELACIONADOS`/`PILLAR-LISTA` via `sincronizar_clusters.py`, sem
  trabalho manual de interligação.
- **Manutenção**: precisa de revisão sazonal todos os anos (mesma
  categoria de `prova-escolar.html` — ver CLAUDE.md "PÁGINAS COM DATAS
  SAZONAIS") — não decidir sem aceitar esse custo recorrente.

### Proposta 2 — `bolsa-de-estudo-ensino-superior.html`

- **Query-alvo**: "bolsa de estudo ensino superior 2026/2027", "bolsa
  DGES como pedir", "tenho direito a bolsa de estudo faculdade".
- **Ângulo**: guia completo da Bolsa de Ação Social do Ensino Superior
  (condições de recursos, cálculo do rendimento relevante, prazos,
  procedimento na plataforma da DGES/SASE) — mesma profundidade dos
  artigos já publicados (FAQ, HowTo, checklist, resposta rápida).
- **Risco de canibalização**: nenhum — público e prestação distintos de
  `bolsa-de-merito.html` (secundário, mérito) confirmado na secção 2.2.
- **Ligação ao cluster**: candidata a **6.ª página** do cluster
  `apoios-escolares`, ou a um cluster novo "Ensino Superior" se a
  extensão justificar mais páginas no futuro (decisão fora do âmbito
  desta análise) — no mínimo, cross-link nos dois sentidos com
  `bolsa-de-merito.html` ("acabaste o secundário? vê a bolsa do ensino
  superior") e `acao-social-escolar.html`.
- **Vantagem adicional**: fecha uma lacuna que o próprio site já assinala
  publicamente ao leitor (o texto do pillar) — publicar esta página
  permite trocar essa frase por um link real.

### Ordem sugerida (não vinculativa)

Proposta 2 (DGES) tem o caso mais forte — preenche uma lacuna já admitida
publicamente pelo próprio site, prestação claramente distinta, zero risco
de canibalização. Proposta 1 (calendário) tem valor mas depende de os 4
prazos de origem estarem correctos e actualizados primeiro (em especial
os vales MEGA 2026/2027, ainda por publicar — ver CLAUDE.md "PÁGINAS COM
DATAS SAZONAIS") — publicá-la antes disso arrisca um calendário
incompleto no lançamento.
