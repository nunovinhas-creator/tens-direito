# CLAUDE.md — Tens Direito

Instruções globais para o Claude Code neste repositório.
Ler sempre antes de qualquer tarefa.

## REGRA ABSOLUTA — GIT

NUNCA criar branches. SEMPRE trabalhar em main.

Workflow obrigatório em TODOS os commits:
  git add .
  git commit -m "mensagem"
  git push origin main

PROIBIDO:
  git checkout -b [qualquer nome]
  git switch -c [qualquer nome]
  Criar Pull Requests
  Trabalhar em qualquer branch que não seja main

Se o Claude Code sugerir criar uma branch: RECUSAR.
Se estiver numa branch diferente de main: fazer
merge imediato para main antes de qualquer trabalho.

Verificação obrigatória antes de cada push:
  git branch  → deve mostrar * main
  Se não mostrar: git checkout main primeiro

## CHECKLIST OBRIGATÓRIA ANTES DE COMMIT

Antes de qualquer `git commit`, verificar cada ponto:

- [ ] `git branch` mostra `* main`
- [ ] Página tem GA4 snippet `G-XP46PM8H1Q`
- [ ] Página tem `og:title` e `og:description`
- [ ] Página tem JSON-LD (`FAQPage` ou `HowTo` + `BreadcrumbList`)
- [ ] Página tem `"Verificado a [data]"` visível no corpo
- [ ] Página tem disclaimer de independência (`Aviso de independência`)
- [ ] Links testados — nenhum inventado (ver regra de links no CLAUDE.md)
- [ ] `sitemap.xml` actualizado se nova página
- [ ] Commit vai directamente para `main` (não para branch)

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

**Commands** (`.claude/commands/`):
- `/publicar-pagina` — pipeline completo: scrape → validar → gerar HTML → auditar links → commit
- `/verificar-fontes` — audita todos os links de todas as páginas publicadas
- `/nova-noticia` — lê RSS, selecciona notícia relevante, actualiza noticias.html

**Skills** (`.claude/skills/`):
- `verificar-url` — testa se um URL existe e devolve acção correcta (200/403/404/timeout)
- `estrutura-pagina` — template HTML com as 10 secções obrigatórias e JSON-LD pronto a preencher

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
- URL canónico DGE: https://www.dge.mec.pt ← USAR ESTE
- RESTRITO (não usar no HTML público): https://www.dge.mec.pt/acao-social-escolar (devolve 403)
- Fonte primária para diplomas: https://dre.pt/pesquisa?q=acao+social+escolar
- Scraper usa: homepage DGE + DRE como fallback (ver data/scraped/_fontes_config.json)
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
- URL canónico DGE: RESTRITO — https://www.dge.mec.pt/bolsas-de-merito devolve 403
- Fonte primária: https://dre.pt/pesquisa?q=bolsa+merito+ensino+basico ← USAR ESTE
- Alternativo DRE: https://dre.pt/pesquisa?q=bolsa+de+merito
- Candidatura: presencial na secretaria da escola
- Despacho anual (pesquisar DRE pelo título "bolsa de mérito")
- Verificar: média mínima, condição de ASE, valor exato
- Nota: não existe portal público DGE para esta prestação — DRE é a única fonte fiável

### Passe sub-23
- Portal cidadão: https://www.gov.pt
- Verificar: condições actuais, como pedir, o que muda aos 23

### Segurança Social (geral)
- Informação geral: https://www.seg-social.pt
- Segurança Social Direta: https://app.seg-social.pt/ptss/ssd
- Legislação: https://dre.pt (pesquisar pelo nome da prestação)

### IEFP — Subsídio de Desemprego
- URL correcto: https://www.iefp.pt/subsidio-desemprego ← SEM hífen antes de desemprego
- URL antigo (incorrecto): https://www.iefp.pt/subsidio-de-desemprego — NÃO usar
- Fallback (entidade pagadora): https://www.seg-social.pt/subsidio-de-desemprego
- ATENÇÃO: IEFP só recebe o pedido. Decisão e pagamento são da Segurança Social.

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

## STACK DE AUTOMAÇÃO (100% gratuito, sem serviços externos)

```
GitHub Actions pipeline-diario  →  scrape + detectar + notícias + validar + push  (06:00 UTC)
GitHub Actions lychee            →  verificação links  (semanal segunda 07:00 UTC)
GitHub Actions validar-conteudo  →  valida HTML em cada push (sem push)
Claude Code (local)              →  lê JSONs → gera HTML
GitHub Pages                     →  publica tensdireito.com
```

### ARQUITECTURA DE DADOS — PRINCÍPIO PUSH ÚNICO

**Apenas `pipeline-diario.yml` faz `git push`.** Os outros dois workflows
só lêem — nunca escrevem no repositório.

Isto elimina race conditions entre workflows concorrentes.

### Workflows

| Ficheiro | Cron / Trigger | Função | `git push`? |
|---|---|---|---|
| `pipeline-diario.yml` | `0 6 * * *` (diário 06:00 UTC) | Scrape + detectar mudanças + notícias + validar valores + README + push único | ✅ sim |
| `verificar-links.yml` | `0 7 * * 1` (segunda 07:00 UTC) | lychee testa todos os links HTML + Issue se 404 | ❌ não |
| `validar-conteudo.yml` | push para main (`**.html`) | Valida GA4, OG tags, JSON-LD, disclaimer, data verificação + HTML5 validator | ❌ não |

### Labels de Issues automáticas
- `fonte-alterada` — conteúdo de uma fonte mudou, verificar e actualizar HTML
- `link-quebrado` — link com 404 confirmado, remover ou corrigir
- `verificar` — marcador genérico de revisão pendente

## FLUXO DE PUBLICAÇÃO

→ Ver `.claude/commands/publicar-pagina.md` para o pipeline completo (6 passos).
→ Ver `.claude/skills/estrutura-pagina.md` para o template HTML obrigatório.
→ Ver `.claude/skills/verificar-url.md` para a lógica de validação de links.

### Regra absoluta
NUNCA gerar HTML de conteúdo sem dados do scraper.
Sem scrape confirmado = sem página. Sem excepções.

### Checklist antes de cada commit
- [ ] `data/scraped/[fonte]_[data].json` existe com `status: "ok"`
- [ ] Todos os links testados com `verificar-url` — nenhum com 404
- [ ] JSON-LD FAQPage e HowTo presentes (ver `estrutura-pagina`)
- [ ] Disclaimer de independência presente
- [ ] Data de verificação visível na página
- [ ] `sitemap.xml` actualizado

---

## Não fazer

- Não usar Jekyll ou qualquer SSG (`.nojekyll` garante HTML puro)
- Não apagar `CNAME` nem `.nojekyll`
- Não publicar sem fonte datada
- Não dar veredictos pessoais ("tu tens direito a X")
- Não misturar conteúdo com o blog de viagens
