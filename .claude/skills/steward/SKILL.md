# Skill: steward

A política de manutenção de PRs neste repositório — quando um sinal conta
como real e o que fica reservado para o Nuno decidir, em vez de resolvido
sozinho.

## Uso

Lida antes de agir sobre eventos de CI ou de revisão num PR aberto pelo
Code ou conduzido em nome do seu autor — tem precedência sobre as
convenções por omissão de babysitting em tudo o que seja critério e
proactividade. Prevalece sobre `babysit/` sempre que os dois existirem.

## FALHAS DE AMBIENTE vs FALHAS DO DIFF

A autoridade é sempre o CI pinado, nunca a corrida local. Casos já vistos
neste repositório, todos sem relação com o código:

- Playwright instalado ad-hoc: rebenta no launch com "timeout: expected
  float, got undefined". Chegou a produzir 343 erros.
- lxml em falta: faz falhar um ficheiro inteiro de testes.
- Chromium ausente: produz skips, que batem com a allow-list.
- Rede bloqueada (www.google.com): testes com browser real.
- pytest não instalado: instalar com
  `pip install pytest PyYAML --break-system-packages`

Regra: reporta a causa, não escondas, e não alteres o diff para contornar.
Se a falha tocar ficheiros que o diff não tocou, presume ambiente e
confirma antes de mexer.

## FONTES PRIMÁRIAS — DIVISÃO DE TRABALHO

`diariodarepublica.pt` e `files.dre.pt` dão `EGRESS_BLOCKED` no sandbox, e
as páginas de detalhe exigem JavaScript. A verificação primária faz-se no
chat; o Code aplica. Quando não conseguires ler um texto legal, diz que
não conseguiste e pára — nunca infiras a partir de fontes secundárias sem
marcar o grau. Espelhos de consolidação são GRAU 2, com a data da versão
registada.

Antes de procurar fora, verifica `dados/fontes/` — o PDF do diploma pode
já lá estar.

## MEDIR ANTES DE APLICAR

Alteração a critério de classificação, a keyword, a filtro ou a regex
exige medição sobre os dados reais antes de ser aplicada, com o número
esperado declarado. Se o número não bater, pára e reporta.

## PROVAR O GUARDRAIL A FALHAR

Teste ou guardrail novo só conta depois de o veres falhar de propósito:
partes a condição, confirmas a falha, repões. Vale também para canários
ligados ao YAML.

## NUNCA RESOLVER POR SUSPEITA

Limite conhecido e medido regista-se, não se corrige. "Não encontrei X"
não é "X não existe". E nunca afirmes que uma alteração legislativa é "só
de forma" sem teres lido o texto.

## CATEGORIA vs ENUMERAÇÃO

Quando uma norma usa uma categoria jurídica em vez de uma lista, a
pergunta não é "está nomeado?" mas "pertence à categoria?" — e a resposta
está no diploma que DEFINE a categoria, nunca no que a invoca. Tratar "não
nomeado" como "não abrangido" já produziu uma lacuna inexistente
(issue #223).

## TEXTO VISÍVEL AO UTILIZADOR

Qualquer alteração que mude o sentido do que uma pessoa lê passa pelo
Nuno antes do commit, em prosa simples aos 55 caracteres, sem blocos de
código. Corpo e JSON-LD alinhados sempre — mudar só um deixa o outro a
prometer ao Google o texto antigo.

## O QUE SE ESCALA, EM VEZ DE RESOLVER

- relaxar qualquer lista de supressão, baseline ou excepção
- alterar filtro, termo ou corte de recência de um sentinela
- redacção de texto visível
- fechar uma issue que só ficou resolvida em parte

Nestes casos: reporta e espera, mesmo que a sugestão venha de um revisor
e pareça razoável.

## CONVENÇÕES DE PR

- `git checkout main && git pull` antes de criar branch. O trabalho
  dispersa-se por sessões; já houve commits duplicados evitados por
  verificar o estado real primeiro.
- "Closes #N" só quando a issue fica resolvida por inteiro.
- Achado de substância encontrado pelo caminho: issue própria, nunca
  enterrado no diff.
- `ruff check scripts/ --select E,F,W --ignore E501 .`
