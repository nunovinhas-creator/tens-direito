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

## Valores de referência (atualizar anualmente)

| Indicador | 2026 | Fonte |
|---|---|---|
| IAS | 537,13 € | Portaria n.º XX/2026 |
| Salário Mínimo | confirmar | DR |
| Escalão ASE-A (rendimento máx.) | confirmar | Ministério Educação |

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
