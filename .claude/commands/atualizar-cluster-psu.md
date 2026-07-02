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
5. Escrever `como-pedir-psu.html` — processo real, extraído do decreto-lei
6. Escrever `calendario-pagamentos-psu.html` — datas reais
7. Avisos cruzados em `rsi.html`, `subsidio-desemprego.html`,
   `subsidio-parental.html` (secção "IMPACTO DA PSU" do CLAUDE.md)
8. `sitemap.xml` — adicionar `como-pedir-psu.html` e `calendario-pagamentos-psu.html`
9. `scripts/pesquisa.js` — adicionar entradas para as 2 páginas novas
10. `data/clusters.json` — actualizar `descricao_curta` do cluster
    `prestacao-social-unica` (deixa de dizer "ainda não em vigor"), acrescentar
    `como-pedir-psu.html` e `calendario-pagamentos-psu.html` a `paginas[]`, e
    correr `python scripts/sincronizar_clusters.py` para propagar a mudança
11. `CLAUDE.md` — mover as 2 páginas da tabela "Cluster PSU — páginas em espera"
    para "PÁGINAS PUBLICADAS"; remover o aviso de incerteza dos prazos na secção
    "IMPACTO DA PSU"

Cada página nova ou modificada usa a skill `estrutura-pagina` para a estrutura
obrigatória (GA4, CookieYes, OG, JSON-LD).

### Passo 6 — Checklist obrigatória

Antes do commit, confirmar todos os pontos da checklist do CLAUDE.md:

- [ ] `git branch` mostra `* main`
- [ ] Valores vêm do decreto-lei confirmado no Passo 4 — nunca de memória
- [ ] Links testados com a skill `verificar-url`
- [ ] GA4 `G-XP46PM8H1Q` presente
- [ ] CookieYes antes do GA4 no `<head>`
- [ ] OG tags presentes
- [ ] JSON-LD FAQPage + HowTo + BreadcrumbList presentes
- [ ] "Verificado a [data]" visível
- [ ] Aviso de independência presente
- [ ] `sitemap.xml` e `scripts/pesquisa.js` actualizados

### Passo 7 — Fechar a Issue

Usar `mcp__github__issue_write` para comentar na Issue com a lista de ficheiros
alterados e o hash do commit, e fechá-la.

### Passo 8 — Commit e push

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
