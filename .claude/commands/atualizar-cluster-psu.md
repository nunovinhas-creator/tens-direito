# /atualizar-cluster-psu

Executa o plano de acção da Issue "🚨 decreto-lei PSU detectado em DRE" — só depois
de confirmação manual explícita dos valores extraídos do decreto-lei real.

## Uso

```
/atualizar-cluster-psu
```

Sem argumentos — localiza a Issue automaticamente.

## Passos de execução (obrigatórios e pela ordem indicada)

### Passo 1 — Localizar a Issue

Usar `mcp__github__list_issues` (state: open, label: `verificar`) e encontrar a
mais recente cujo título contenha `decreto-lei PSU` e `DRE`
(título real gerado pelo pipeline: `🚨 decreto-lei PSU detectado em DRE — actualizar cluster inteiro`).

Se não existir nenhuma Issue aberta com esse título: parar e informar o utilizador
— não há decreto-lei detectado, nada a fazer.

Ler o corpo da Issue. Contém:
- a fonte monitorizada (`https://dre.pt/pesquisa?q=...`) — é uma página de pesquisa, **não** o decreto-lei em si
- excertos de texto detectados pelo scraper

### Passo 2 — Encontrar o link real do decreto-lei

A Issue só aponta para a página de pesquisa. O link concreto do decreto-lei tem de
vir de `data/scraped/dre_psu_latest.json` (campo `links_uteis` ou `resultados`) —
procurar a entrada cujo texto contenha "decreto-lei" e "prestação social única".

Se não houver link directo no JSON: usar a skill `verificar-url` sobre a página de
pesquisa DRE da Issue para localizar o link do decreto-lei específico a partir dos
resultados aí listados.

Se não for possível chegar a um link concreto do decreto-lei: **parar** e reportar
ao utilizador — nunca avançar com o excerto do scraper como se fosse o texto legal.

### Passo 3 — Fetch ao texto oficial do decreto-lei

Fazer fetch ao link concreto encontrado no Passo 2 (`WebFetch`, domínio `dre.pt`).
Extrair, só do texto oficial (nunca de memória, nunca do excerto do scraper):

- número e data do decreto-lei
- data de entrada em vigor
- valor de referência da PSU
- valor máximo
- coeficiente da Componente de Incentivo ao Trabalho (CIT)
- qualquer condição de acesso alterada face à lei de autorização (ex.: trabalho
  social obrigatório vs. facultativo)

Se o fetch falhar ou o texto não confirmar algum destes pontos: marcar esse ponto
como "não confirmado" — nunca inventar o valor em falta.

### Passo 4 — Confirmação obrigatória (guardrail)

**Parar aqui.** Mostrar ao utilizador um resumo dos valores extraídos, por exemplo:

```
Decreto-lei n.º [X]/2026, de [data]
Entrada em vigor: [data]
Valor de referência PSU: [X] €
Valor máximo: [X] €
Coeficiente CIT: [X]
Condições alteradas face à lei de autorização: [sim/não — detalhe]
Fonte: [link do decreto-lei]

Confirmas estes valores? avança/não avança
```

Perguntar explicitamente com `AskUserQuestion`. **Nunca prosseguir para o Passo 5
sem resposta afirmativa explícita.** Se a resposta for "não avança" ou houver
qualquer dúvida: parar, não tocar em nenhum ficheiro.

### Passo 5 — Actualizar o cluster (só após confirmação)

1. `prestacao-social-unica.html` — substituir "a fixar por decreto-lei" pelos
   valores confirmados
2. `psu-quando-entra-em-vigor.html` — o "ainda não decidido" passa a facto
3. `psu-quem-tem-direito.html` — condições finais, se mudaram
4. `psu-lista-13-apoios.html` — se algum apoio mudou de tratamento
5. `psu-trabalho-social.html` — a secção "Por definir" (disputa PS-PSD sobre
   a obrigatoriedade) passa a facto, com a palavra exacta usada no
   decreto-lei; se o Passo 4 confirmou que a exigência ficou "obrigatória",
   documentar aqui a possibilidade de reapreciação parlamentar pelo PS
   (ver as declarações já citadas no artigo)
6. Escrever `como-pedir-psu.html` — processo real, extraído do decreto-lei
7. Escrever `calendario-pagamentos-psu.html` — datas reais
8. Avisos cruzados em `rsi.html`, `subsidio-desemprego.html`,
   `subsidio-parental.html` (secção "IMPACTO DA PSU" do CLAUDE.md)
9. `python scripts/inserir_botao_partilhar.py` — botão "Partilhar este artigo"
   nas páginas novas (idempotente; as páginas já modificadas mantêm-se)
10. **Publicar `simulador-psu.html`** (ver Passo 5a abaixo — sub-processo
    próprio, com o seu próprio guardrail)
11. `sitemap.xml` — adicionar `como-pedir-psu.html`, `calendario-pagamentos-psu.html`
    e `simulador-psu.html`
12. `scripts/pesquisa.js` — adicionar entradas para as páginas novas
    (lista manual — ver CLAUDE.md secção "FECHO DO PROJECTO")
13. `data/clusters.json` — actualizar `descricao_curta` do cluster
    `prestacao-social-unica` (deixa de dizer "ainda não em vigor"), acrescentar
    `como-pedir-psu.html`, `calendario-pagamentos-psu.html` (`tipo: "artigo"`)
    e `simulador-psu.html` (`tipo: "ferramenta"`) a `paginas[]`, e correr
    `python scripts/sincronizar_clusters.py` (`--dry-run` primeiro) para
    propagar a mudança — injecta `CLUSTER-BADGE`/`RELACIONADOS` nas páginas
    novas de tipo `artigo` e actualiza o `PILLAR-LISTA` de
    `prestacao-social-unica.html`
14. `python scripts/sincronizar_nav.py` — as páginas novas ainda não têm o
    bloco `NAV:INICIO/FIM`; o script faz o bootstrap a partir da estrutura
    `<header><nav>` do template `estrutura-pagina`
15. `CLAUDE.md` — mover as páginas novas da tabela "Cluster PSU — páginas em
    espera" para "PÁGINAS PUBLICADAS"; remover o aviso de incerteza dos
    prazos na secção "IMPACTO DA PSU"; remover a entrada `simulador-psu.html`
    de `EXCLUIDAS` (`scripts/sincronizar_clusters.py`) e de `NAO_INDEXADAS`
    (`tests/test_pesquisa_indice.py`) — deixa de ser página não-publicada

### Passo 5a — Publicar o simulador (guardrail próprio)

`simulador-psu.html` já existe, pronto, com a fórmula estruturada em
`PARAMETROS_PSU` — cada parâmetro tem `valor`, `fonte` e `verificado_em`
próprios, todos `null`/pendentes por desenho até este passo. Nunca escrever
um número solto no meio da lógica de cálculo.

1. Preencher os campos `valor`/`fonte`/`verificado_em` de `PARAMETROS_PSU`
   no `<script>` de `simulador-psu.html` com os valores confirmados no
   Passo 4 — só os que o decreto-lei realmente fixa (`valorReferencia`,
   `valorMaximo`, `coeficienteCIT.valor`, `majoracaoParentalidade`).
   `adultosEquivalentes` e `limitePatrimonio` já estavam confirmados desde a
   lei de autorização (25 jun 2026) — normalmente não mudam neste passo.
2. Mudar `const ESTADO_SIMULADOR = 'AGUARDA_DECRETO';` para `'ATIVO'`.
3. Reactivar o formulário: remover o atributo `disabled` do `<fieldset>` e
   do botão de submissão, e ligar `document.getElementById('formPSU')` a
   `calcularPSU(PARAMETROS_PSU, {...})` com os valores lidos do formulário —
   ver `calcularAbono()` em `simulador-abono.html` para o padrão de
   ligação formulário → cálculo → render do resultado a seguir.
4. Substituir o bloco `.aguarda-box` (aviso "simulação indisponível") pelo
   resultado calculado, seguindo o padrão visual de `.resultado-card` em
   `simulador-abono.html`.
5. Remover `<meta name="robots" content="noindex, nofollow">` do `<head>`
   e substituir por `<meta name="robots" content="index, follow">` — só
   agora a página fica descobrível.
6. Correr `python -m pytest tests/test_simulador_psu_calculo.py` — os
   testes existentes usam parâmetros fictícios e continuam válidos; a
   mecânica de redução gradual da CIT pode precisar de ajuste se a fórmula
   exacta do decreto-lei divergir da aproximação usada até aqui (documentado
   no próprio ficheiro de teste) — nesse caso, actualizar `calcularCIT()` e
   os testes correspondentes antes de publicar.

Cada página nova ou modificada usa a skill `estrutura-pagina` para a estrutura
obrigatória (GA4 via banner de consentimento próprio, OG, JSON-LD).

### Passo 6 — Testes de coerência

```bash
python -m pytest tests/test_breadcrumb_coerencia.py tests/test_nav_coerencia.py tests/test_sincronizar_clusters.py tests/test_pesquisa_indice.py tests/test_simulador_psu_calculo.py
```

Correm sobre as páginas reais (parametrizados) — as páginas novas entram
automaticamente assim que estiverem em `data/clusters.json`/`pesquisa.js`.
Se algum falhar: corrigir antes de avançar, nunca ignorar.

### Passo 7 — Checklist obrigatória

Antes do commit, confirmar todos os pontos da checklist do CLAUDE.md:

- [ ] `git branch` mostra `* main`
- [ ] Valores vêm do decreto-lei confirmado no Passo 4 — nunca de memória
- [ ] Links testados com a skill `verificar-url`
- [ ] GA4 `G-XP46PM8H1Q` presente
- [ ] Bloco de consentimento próprio no `<head>` (stub Consent Mode + `assets/js/consentimento.js` com `data-ga4`) — nunca gtag.js estático
- [ ] OG tags presentes
- [ ] JSON-LD FAQPage + HowTo + BreadcrumbList presentes
- [ ] "Verificado a [data]" visível
- [ ] Aviso de independência presente
- [ ] `sitemap.xml` e `scripts/pesquisa.js` actualizados
- [ ] `inserir_botao_partilhar.py`, `sincronizar_clusters.py` e `sincronizar_nav.py` corridos
- [ ] `test_breadcrumb_coerencia.py` e `test_nav_coerencia.py` a passar
- [ ] `simulador-psu.html`: `ESTADO_SIMULADOR = 'ATIVO'`, `PARAMETROS_PSU` preenchido com fonte+data por parâmetro, `robots` mudado para `index, follow`, `simulador-psu.html` removido de `EXCLUIDAS`/`NAO_INDEXADAS`, `test_simulador_psu_calculo.py` a passar

### Passo 8 — Fechar a Issue

Usar `mcp__github__issue_write` para comentar na Issue com a lista de ficheiros
alterados e o hash do commit, e fechá-la.

### Passo 9 — Commit e push

```
feat: cluster PSU actualizado — decreto-lei n.º [X]/2026 confirmado

decreto-lei: [número/data] | fonte: [link] | entrada em vigor: [data]
fecha #[numero-issue]
```

Commit directo a `main`, push, reportar o estado dos workflows ao utilizador.

## Porquê o Passo 4 é obrigatório

É o único ponto onde um erro de leitura automática do DRE (ex.: o scraper apanhar
uma retificação em vez do decreto-lei final, ou uma versão ainda não republicada)
se transformaria em factos errados publicados no site. Nunca saltar este passo.
