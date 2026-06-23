# CLAUDE.md — Tens Direito

Instruções globais para o Claude Code neste repositório.
Ler sempre antes de qualquer tarefa.

## O que é este projeto

Site informativo PT-PT sobre apoios sociais, direitos e burocracia em Portugal.
Cada facto tem data de verificação e ligação à fonte oficial.
Domínio: tensdireito.com | GitHub Pages (estático)

## Regras absolutas

1. **Português de Portugal** em todo o conteúdo (nunca PT-BR).
2. **Só fontes primárias**: DR, gov.pt, seg-social.pt, iefp.pt, ias oficial.
3. **Nunca assertivo** sobre o caso pessoal do leitor: condicional sempre.
4. **Nunca copiar** texto de bancos, jornais ou agregadores — reescrever sempre.
5. **Data em cada facto**: "Verificado a [data] · Fonte: [link]".
6. **Disclaimer** de não-vinculação em todas as páginas.
7. **JSON-LD** FAQPage/HowTo em todas as páginas de conteúdo.
8. **Independência declarada**: sem imitar o Estado.

## Estrutura de ficheiros

```
data/apoios/        → YAML de cada apoio (fonte de verdade)
data/burocracia/    → YAML de cada processo burocrático
site/               → HTML estático publicado (GitHub Pages serve daqui)
content/            → rascunhos em Markdown antes de converter para HTML
templates/          → templates reutilizáveis
.claude/agents/     → agentes especializados
scripts/            → automação Python
CNAME               → tensdireito.com (não apagar)
.nojekyll           → serve HTML estático (não apagar)
```

## Agentes disponíveis

- `validador-fontes` — comando `/scan` para verificar se as fontes mudaram
- `redator-ptpt` — redigir/rever conteúdo seguindo as 10 regras
- `atualizador-schema` — gerar/atualizar JSON-LD

## FONTES OBRIGATÓRIAS POR TEMA

### Regra absoluta
NUNCA escrever valores, condições ou prazos de memória.
Sempre ir à fonte primária ANTES de redigir.
Se a fonte não confirmar o facto, o facto não entra no site.

### Manuais escolares / MEGA
- Fonte primária: https://mega.mec.pt
- Legislação: Portaria que regulamenta o MEGA (pesquisar no DRE)
- Verificar: quem tem direito, como levantar, calendário
- ATENÇÃO CONFIRMADA: manuais gratuitos para TODOS os alunos
  do ensino público, independentemente de escalão ASE

### ASE — Ação Social Escolar
- Fonte primária: https://www.dge.mec.pt/acao-social-escolar
- Despacho anual que fixa escalões e valores (pesquisar DRE)
- Verificar: escalões A e B, o que cobre cada um, prazos
- ATENÇÃO: a declaração que os EE entregam é emitida
  pela Segurança Social, não é declaração de rendimentos própria

### Abono de família
- Fonte primária: https://www.seg-social.pt/abono-de-familia
- IAS 2026: 537,13€ (Portaria n.º XX/2026)
- Verificar escalões e valores no portal antes de publicar

### Bolsa de mérito
- Fonte primária: https://www.dge.mec.pt/bolsa-de-merito
- Despacho anual (pesquisar DRE pelo título "bolsa de mérito")
- Verificar: média mínima, condição de ASE, valor exato

### Passe sub-23
- Fonte primária: https://www.imtt.pt ou https://www.gov.pt
- Verificar: condições actuais, como pedir, o que muda aos 23

### Segurança Social (geral)
- Simulador oficial: https://simulador.seg-social.pt
- Portal de prestações: https://www.seg-social.pt/prestacoes-pecuniarias
- Legislação: https://dre.pt (pesquisar pelo nome da prestação)

### Diário da República (todas as áreas)
- https://dre.pt/pesquisa — pesquisar pelo nome da medida + ano
- Usar sempre o número da Portaria/Despacho como referência

---

## FLUXO OBRIGATÓRIO ANTES DE PUBLICAR QUALQUER PÁGINA

Passo 1 — FETCH da fonte primária
  Antes de escrever qualquer facto, fazer web_fetch ao URL
  da fonte oficial e ler o conteúdo actual.

Passo 2 — VERIFICAR no DRE
  Para valores e condições de acesso, confirmar com o
  Despacho/Portaria mais recente em dre.pt.

Passo 3 — REGISTAR a fonte
  Anotar: URL exacto + data de acesso + número do diploma legal.

Passo 4 — SÓ ENTÃO redigir
  Escrever apenas o que foi confirmado na fonte.
  Se um facto não foi confirmado, não entra — nunca inventar.

Passo 5 — ASSINALAR o que falta confirmar
  Se uma fonte estava inacessível, marcar com
  [VERIFICAR — fonte inacessível em DD/MM/AAAA].

---

## CHECKLIST DE PUBLICAÇÃO (obrigatória em cada página)

Antes de fazer commit, confirmar:
[ ] Fui à fonte primária e li o conteúdo actual
[ ] Cada valor tem número de diploma legal ou URL de fonte datada
[ ] Não há factos de memória — tudo confirmado na fonte
[ ] Links testados e funcionais
[ ] Disclaimer de não-vinculação presente
[ ] Data de verificação visível

## Workflow de publicação

1. Verificar/criar o `.yml` em `data/apoios/`
2. Redigir HTML em `site/[slug].html` com o agente `redator-ptpt`
3. Adicionar JSON-LD com o agente `atualizador-schema`
4. Confirmar fontes com `/scan`
5. Commit + push → GitHub Pages publica automaticamente

## Não fazer

- Não usar Jekyll ou qualquer SSG (`.nojekyll` garante HTML puro)
- Não apagar `CNAME` nem `.nojekyll`
- Não publicar sem fonte datada
- Não dar veredictos pessoais ("tu tens direito a X")
- Não misturar conteúdo com o blog de viagens
