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

### Abono de Família
- URL canónico: https://www.seg-social.pt/abono-de-familia-para-criancas-e-jovens
- Simulador oficial: https://www.seg-social.pt/ptss/sps/simulador/6
- Segurança Social Direta: https://app.seg-social.pt/ptss/ssd
- Prova escolar / menu Família: https://app.seg-social.pt/ptss/ssd (menu Família)
- IAS 2026: 537,13 € (Portaria em vigor)
- Verificar escalões e valores no portal antes de publicar

### ASE — Ação Social Escolar
- URL canónico DGE: https://www.dge.mec.pt/acao-social-escolar
- Despacho anual que fixa escalões e valores (pesquisar DRE)
- Verificar: escalões A e B, o que cobre cada um, prazos
- ATENÇÃO: não existe portal público para EE — candidatura é
  presencial nos serviços administrativos da escola/agrupamento.
  Não linkar para SIGE — é sistema interno das escolas.
- ATENÇÃO: a declaração que os EE entregam é emitida
  pela Segurança Social, não é declaração de rendimentos própria

### MEGA — Manuais Escolares Gratuitos
- URL canónico DGE: https://www.dge.mec.pt/manuais-escolares
- Gestão interna (só escolas): https://www.igefe.mec.pt
- ATENÇÃO: mega.mec.pt NÃO é URL público válido — não usar.
  O portal público é dge.mec.pt/manuais-escolares
- ATENÇÃO CONFIRMADA: manuais gratuitos para TODOS os alunos
  do ensino público, independentemente de escalão ASE

### Bolsa de Mérito
- URL canónico DGE: https://www.dge.mec.pt/bolsas-de-merito
- Candidatura: presencial na secretaria da escola
- Despacho anual (pesquisar DRE pelo título "bolsa de mérito")
- Verificar: média mínima, condição de ASE, valor exato

### Passe sub-23
- Portal cidadão: https://www.gov.pt
- Verificar: condições actuais, como pedir, o que muda aos 23

### Segurança Social (geral)
- Informação geral: https://www.seg-social.pt
- Segurança Social Direta: https://app.seg-social.pt/ptss/ssd
- Legislação: https://dre.pt (pesquisar pelo nome da prestação)

### IEFP — Subsídio de Desemprego
- URL: https://www.iefp.pt/subsidio-de-desemprego

### Diário da República (todas as áreas)
- Pesquisa: https://dre.pt/pesquisa
- Série I (diplomas principais): https://dre.pt/dre/legislacao-consolidada
- Usar sempre o número da Portaria/Despacho como referência

### Gov.pt — Portal do Cidadão
- Portal cidadão: https://www.gov.pt

---

## REGRA DE LINKS (obrigatória)

Antes de qualquer link entrar numa página HTML:
1. O URL tem de estar na lista de URLs verificados acima, OU
2. Ter sido testado com requests.get() com status 200, OU
3. Ser um URL do tipo https://www.[dominio-oficial].pt/[path]
   confirmado na pesquisa Google com site:[dominio]

NUNCA inventar subpaths de portais oficiais.
Se não houver URL confirmado: linkar para a página-mãe
ou escrever "consulta nos serviços da escola/agrupamento"
sem link nenhum.

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
