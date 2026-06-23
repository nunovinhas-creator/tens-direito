# Tens Direito

> **Os teus direitos, com data e fonte.**
> O registo PT-PT, datado e referenciado à fonte primária, de **dinheiro + direitos + burocracia**.

Documento-mestre do projeto. É a base de verdade: define o que é, porque existe, como se posiciona, como cresce em tráfego orgânico, e as regras que o tornam credível e inatacável. Mantém este ficheiro versionado no repositório (equivalente ao `REGRAS-PADRAO` do blog).

---

## 1. O que é

Um site informativo independente em **Português de Portugal** que transforma as perguntas recorrentes de dinheiro, direitos e burocracia em respostas claras, estruturadas e **corretas para Portugal** — cada facto com data de verificação e ligação à fonte oficial.

Não é um blog de opinião nem um clone do simulador oficial. É a **camada de tradução** entre a informação oficial dispersa/ilegível e uma resposta acionável, pensada para ser:
- a fonte que os motores de IA citam (era da pesquisa conversacional);
- impossível de acusar de erro ou de aconselhamento indevido (cada frase tem data + fonte).

**Posicionamento de uma linha:** "o gov.pt encontra o Doutor Finanças" — open-source, automatizado por agentes, otimizado para SEO e para AI Overviews.

---

## 2. Porque existe — a procura validada

Três fossos reais, todos mal servidos em PT-PT, todos de alto valor comercial.

### Fosso 1 — Literacia financeira
- Apenas **~25%** dos portugueses respondem corretamente a perguntas básicas sobre inflação, juros e diversificação (Comissão Europeia).
- **63%** dizem ter conhecimentos sólidos, mas só **36%** acertam uma pergunta simples sobre inflação (estudo Santander, dez. 2025) — fosso perceção/conhecimento.
- Só **~10%** recordam ter tido educação financeira na escola.
- **6 em cada 10** não investem; a maioria fica em capital garantido a perder para a inflação.

### Fosso 2 — Direitos e apoios que existem mas ninguém encontra
- Estima-se que **~40% da população (~4 milhões)** seja elegível para algum apoio do Estado e não saiba.
- A Segurança Social tem **60+ apoios**, cada um com regras próprias; a informação "nem sempre está toda no mesmo sítio".
- O simulador oficial é limitado: só cobre o próprio + dependentes, não trata de quem trabalhou no estrangeiro, e não é vinculativo.

### Fosso 3 — O Estado digital que frustra
- A satisfação com os serviços públicos caiu **15%** em 2025 (Portal da Queixa / Consumers Trust Lab).
- IMT + AIMA concentram quase metade das reclamações da administração pública; Segurança Social, SNS e IRN recorrentes.

### Contexto que joga a nosso favor
- "O Ano em Pesquisa 2025" (Google PT): burocracia + saúde + dinheiro repetem-se ano após ano ("como renovar a carta online", "como ganhar dinheiro online").
- Google detém **~94,5%** da pesquisa em PT; há migração para **pesquisa por voz / IA / conversacional** — quem tiver a resposta estruturada e correta ganha a citação.
- Conteúdo brasileiro domina muitas SERP de "dinheiro", mas **não consegue competir** em temas presos às instituições portuguesas (Segurança Social Direta, SIGA, MEGA, escalões). Isto remove metade da concorrência por natureza do tema.

---

## 3. Marca

- **Nome:** Tens Direito
- **Domínio:** `tensdireito.pt` (confirmar `.com`)
- **Tagline:** *Os teus direitos, com data e fonte.*
- **Logótipo:** selo de verificação arredondado (não-institucional) em teal, com *checkmark* branco que funciona como a resposta afirmativa à pergunta "tens direito?". Wordmark com "Direito" a teal. Ficheiros: `tens-direito-logo.svg` (lockup) e o selo isolado como favicon/avatar.
- **Paleta:** teal de confiança `#0F766E`→`#115E59`, acento `#0D9488`, tinta `#0F172A`, texto secundário `#475569`. (Evitar o azul institucional do Estado.)
- **Tom:** próximo mas rigoroso; trata por "tu"; explica sem jargão; nunca paternalista.

**Guardrail do nome:** como "Tens Direito" afirma direito, o conteúdo **nunca** diz "tu, especificamente, tens direito a X". É sempre condicional: "tens direito **se** cumprires A e B; confirma no simulador oficial". A marca faz a promessa; o texto entrega-a como **regra**, não como veredito sobre o caso da pessoa.

---

## 4. Estratégia de tráfego orgânico

**Objetivo:** tráfego orgânico (sem redes sociais), com primeiros resultados em ~30 dias e sustentável.

### Como se ganha
Não pela autoridade (não batemos bancos/DECO nos termos-cabeça em 30 dias), mas pela **frescura + precisão + estrutura** no *long-tail datado*. Os incumbentes publicam páginas genéricas e deixam-nas envelhecer; ninguém atualiza ao minuto o valor de 2026/2027, a data de pagamento ou o passo-a-passo atual do portal.

### Cabeça-de-praia (primeiros 30 dias): cluster de setembro
Evento de calendário = procura que não precisa de promoção. Basta estar indexado quando chega.
- "escalões abono de família 2026 tabela" · "abono setembro 2026 quando paga"
- "ASE candidatura 2026/2027 prazo como pedir"
- "prova escolar abono como fazer Segurança Social Direta"
- "passe sub-23 2026/2027 como pedir"
- "bolsa de mérito secundário 2026 valor quem tem direito"

**Timing:** publicar nas próximas 2-3 semanas para as páginas terem 6-8 semanas a envelhecer antes do pico de finais de agosto / meados de setembro.

### Porque se mantém
Sazonal-recorrente: a página de "abono setembro 2026" volta a render em 2027 com os números atualizados. Por baixo, a base evergreen de burocracia ("como pedir o NISS", "renovar a carta") puxa o ano inteiro. Tráfego que **compõe**, não que decai.

### O flywheel
Notícia-âncora datada apanha o pico → liga internamente para as páginas de referência permanentes e passa-lhes autoridade → referências rankeiam o ano todo → simuladores atraem links e tempo de permanência → autoridade temática do domínio sobe → levanta as páginas mais competitivas. O agente `validador-fontes` (`/scan`) impede que envelheça a mentir — é, ao mesmo tempo, moat de SEO e escudo legal.

### Regras de execução
- **Não** alojar no blog de viagens (mistura tópica estraga os dois). Domínio próprio.
- Indexar de imediato: GSC, sitemap, *request indexing*.
- `FAQPage` / `HowTo` em JSON-LD em todas as páginas (ganha snippets e AI Overviews).
- Ligação interna forte entre notícia → referência → simulador.

---

## 5. As 10 regras de credibilidade (inatacável)

Embutidas desde o primeiro commit. São simultaneamente o diferencial de SEO (E-E-A-T) e a blindagem legal.

1. **Só fontes primárias e oficiais** como autoridade citada: Diário da República (Despacho/Portaria com número), gov.pt, seg-social.pt, valor oficial do IAS. Bancos/agregadores podem ser leitura, nunca a fonte.
2. **Carimbo de data + fonte em cada facto:** "Verificado a [data] · Fonte: [documento] (link direto)".
3. **Independência declarada:** site informativo independente, sem relação com o Estado. Nada de logótipos, cores ou nomes institucionais que confundam.
4. **Informação, não aconselhamento personalizado:** descreve-se a regra ("quem cumpre A e B tem direito a Y"), não se decide o caso da pessoa.
5. **Tudo reescrito, nada copiado:** cita-se a lei, não se copia quem a explicou. Estrutura e texto originais.
6. **Deferência ao oficial nos resultados vinculativos:** simuladores dão estimativa não vinculativa e remetem sempre para o simulador oficial.
7. **Registo público de alterações:** "Atualizado em" + histórico de revisões visível.
8. **E-E-A-T explícito:** autor identificado, páginas de Metodologia, Fontes, Contacto e política de correções.
9. **RGPD por defeito:** mínimo de dados, simuladores client-side (sem guardar inputs), política de privacidade clara.
10. **Pipeline de não-desatualizar:** o `/scan` monitoriza fontes oficiais e sinaliza páginas para revisão quando muda um valor, escalão ou data.

---

## 6. Modelo editorial — de que vive a página

Cinco camadas que se alimentam umas às outras. Princípio central: dinheiro + direitos + burocracia têm calendário previsível e repetem-se todos os anos → cada página, depois de envelhecer, volta a render só com os números atualizados.

| Camada | Função | Exemplos | Natureza |
|---|---|---|---|
| 1. Espinha | Calendário fiscal-social recorrente | IAS/escalões (jan), IRS (fev-jun), regresso às aulas (ago-set), IMI/IUC/OE (out-dez) | Sazonal, compõe anualmente |
| 2. Largura | Catálogo de apoios (1 página por prestação) | abono, RSI, subsídio desemprego, parentalidade, cuidador informal, CSI, PSI, apoio à renda | Evergreen referência |
| 3. Dor diária | "Como fazer X no portal" | renovar carta (IMT), pedir NISS, marcar no SIGA, mudar morada no CC, declaração de não dívida | Evergreen how-to |
| 4. Frescura | Notícia-âncora datada | mudança de valor, novo despacho, medidas do OE | Pico + alimenta as restantes |
| 5. Íman | Simuladores leves client-side | estimar abono, subsídio desemprego, escalão ASE, reembolso IRS | Backlinks + permanência |

### Calendário editorial (esqueleto anual)
- **Jan:** novo IAS, escalões, salário mínimo, atualização de pensões.
- **Fev–Jun:** IRS — entrega, deduções, reembolso, IRS automático, IRS Jovem (pico de maior volume).
- **Jun–Jul:** subsídio de férias, IMI, prova escolar.
- **Ago–Set:** regresso às aulas, ASE, abono a dobrar (1.º escalão, 6-16 anos), passes sub-23, bolsas de mérito (candidaturas até 30 set).
- **Out–Dez:** prestações de IMI/IUC, mudanças do Orçamento do Estado seguinte, subsídio de Natal.

### Ritmo realista (solo, mobile, com agentes a rascunhar)
2-3 páginas de referência/semana a construir o catálogo + reação aos eventos do calendário. Em 12 meses: espinha completa + 40-60 páginas evergreen.

### Dados de referência úteis (atualizar e datar sempre)
- IAS 2026 = **537,13 €**. Para escalões de quem já recebe abono em 2026, usam-se rendimentos de 2024 e IAS de 2024 (509,26 €); para novos pedidos em 2026, rendimentos de 2025 e IAS 2025 (522,50 €). *(Confirmar na fonte antes de publicar.)*

---

## 7. Arquitetura técnica

Browser-only / mobile, Python, agentes Claude, deploy estático grátis (GitHub Pages).

```
tens-direito/
├── README.md              # este documento
├── data/                  # fonte de verdade: 1 ficheiro YAML por apoio/taxa/processo
│   ├── apoios/
│   │   └── abono-familia.yml
│   ├── burocracia/
│   └── _fontes.yml        # registo central de fontes oficiais + datas de verificação
├── .claude/
│   └── agents/
│       ├── validador-fontes.md   # corre o /scan; verifica se a fonte oficial mudou
│       ├── redator-ptpt.md       # rascunha em PT-PT seguindo as 10 regras
│       └── atualizador-schema.md # gera/atualiza JSON-LD FAQPage/HowTo
├── scripts/
│   ├── scan_fontes.py     # deteta alterações nas fontes oficiais → sinaliza revisão
│   └── build_site.py      # gera HTML estático + JSON-LD a partir do data/ + content/
├── content/               # respostas geradas, revistas e versionadas (markdown)
├── templates/             # template de página que força as 10 regras
└── site/                  # output estático (GitHub Pages)
```

### Esquema de uma entrada de dados (exemplo)
```yaml
# data/apoios/abono-familia.yml
slug: abono-de-familia
titulo: "Abono de família 2026: escalões, valores e como pedir"
tipo: apoio
entidade: "Segurança Social"
atualizado: 2026-06-23
fontes:
  - nome: "Portaria n.º XXX/2026 (Diário da República)"
    url: "https://diariodarepublica.pt/..."
    verificado: 2026-06-23
  - nome: "Segurança Social — Abono de família"
    url: "https://seg-social.pt/..."
    verificado: 2026-06-23
quem_tem_direito:
  condicoes:
    - "Criança/jovem residente em Portugal, enquanto não trabalha"
    - "Agregado dentro do teto de rendimento do escalão aplicável"
  nota: "Direito condicional. Confirmar no simulador oficial."
valores:                     # sempre com ano e fonte
  ano: 2026
  ias_referencia: 537.13
  escaloes: []               # preencher a partir da fonte oficial, datado
como_pedir:
  canal: "Segurança Social Direta > Família > Abono de Família e de Pré-Natal"
  passos: []
  automatico: "Em certos casos é proposto automaticamente; confirmar a proposta no prazo."
disclaimer: "Conteúdo informativo e não vinculativo. Não substitui a consulta às entidades oficiais."
```

### Estrutura obrigatória de cada página (template)
1. Resposta direta no topo (1-2 frases) — para snippet/AI Overview.
2. "Quem tem direito" (condicional, nunca veredito pessoal).
3. "Quanto recebe" (valor + ano + fonte datada).
4. "Como pedir" (passo-a-passo do canal atual).
5. Bloco **Fontes** (oficiais, com data de verificação) + "Atualizado em".
6. Remissão para o simulador/portal oficial.
7. Disclaimer de independência e não-vinculação.
8. JSON-LD `FAQPage` e/ou `HowTo`.

---

## 8. Monetização

- **AdSense** (já aprovado noutro projeto): finanças/burocracia têm dos CPC mais altos em PT.
- **Afiliação** de produtos financeiros relevantes (contas, PPR, crédito, seguros) — claramente separada do conteúdo editorial, com divulgação.
- Regra: nunca deixar a monetização contaminar o rigor. Conteúdo patrocinado é sempre identificado.

---

## 9. Guardrails legais e RGPD (resumo operacional)

- Informação geral, não aconselhamento jurídico ou financeiro personalizado.
- Cada facto datado e ligado à fonte primária; correções públicas e rápidas.
- Independência declarada; sem imitação de entidades públicas.
- Simuladores não vinculativos, client-side, sem armazenar dados pessoais.
- Política de privacidade, página de Fontes e de Metodologia visíveis.

---

## 10. Roadmap

**Fase 0 — Base (agora):** este README; registo do domínio; logótipo; GA + GSC.
**Fase 1 — Cabeça-de-praia (próximas 2-3 semanas):** 5 páginas-pilar do cluster de setembro (abono, ASE, bolsa de mérito, manuais MEGA, passe sub-23), cada uma com versão nacional, fonte datada e JSON-LD. Indexar de imediato.
**Fase 2 — Catálogo (meses 1-6):** 2-3 páginas de referência/semana (Camada 2) + how-to (Camada 3).
**Fase 3 — Frescura + íman (contínuo):** notícias-âncora a cada mudança oficial; primeiros simuladores client-side.
**Fase 4 — Compor:** atualização anual datada de toda a espinha; expansão do catálogo.

---

### Fontes da pesquisa de base
Google "O Ano em Pesquisa 2025" (PT); estudo Santander de literacia financeira (dez. 2025); Comissão Europeia (literacia financeira ~25%); Barómetro Doutor Finanças / Univ. Católica (investimento); Portal da Queixa / Consumers Trust Lab — Relatório de Satisfação com os Serviços Públicos 2025; Segurança Social / ISS (simulador de prestações; 60+ apoios); calendário escolar e ASE 2025/2026 (Ministério da Educação, CGD Saldo Positivo, DECO, idealista). *Confirmar sempre os valores na fonte oficial antes de publicar.*
