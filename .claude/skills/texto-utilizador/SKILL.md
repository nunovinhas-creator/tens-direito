# Skill: texto-utilizador

O que uma pessoa LÊ nas páginas do site — precisão, consistência e prazo
de validade do texto visível. Nunca a política de PRs (`steward/SKILL.md`)
nem o grau de confiança de um facto legal (`fact-check/SKILL.md`): um
facto pode estar em GRAU 1, correctamente confirmado, e o texto que o
comunica continuar errado — é esse erro, sempre de redacção e nunca de
fonte, que esta skill cobre.

## Uso

Invocar sempre que um texto visível ao utilizador é escrito ou editado —
corpo do artigo, FAQ visível, resposta rápida, checklist final, JSON-LD,
ou qualquer string composta em runtime por JavaScript. `fact-check`
decide se o facto está confirmado e em que grau; esta skill decide como
esse facto já confirmado é fraseado para quem lê.

## CORPO E JSON-LD DIZEM SEMPRE O MESMO

Mudar só um deixa o outro a prometer ao Google o texto antigo — já
aconteceu um título divergente entre corpo e JSON-LD na mesma FAQ
("pensão social" vs "pensão social de velhice"), duas prestações
diferentes escondidas atrás do mesmo texto visível. Antes de fechar
qualquer alteração a um facto, percorre todos os pares onde ele aparece:
resposta rápida, corpo, FAQ visível, `FAQPage`/`HowTo` JSON-LD,
`title`/meta description, `og:title`. A maioria destes pares não tem
canário nenhum a apanhar a divergência (ao contrário dos valores em €/%
e dos anos civis, cobertos por `tests/test_valores_ancora.py`/
`tests/test_anos_metadados.py`) — depende só de quem edita verificar
todos, não de um teste automático.

## FACTO LEGAL vs FACTO OPERACIONAL

Uma data fixada por lei é certa desde que publicada. Que a conversão foi
feita, que o pagamento já começou, que o processo do leitor foi tratado
— nada disso decorre da data em si, é facto operacional, e só se afirma
quando confirmado à parte. Nunca escrever texto que troque de afirmação
sozinho conforme a data corrente: um banner em JavaScript de
`simulador-psu.html` passava a dizer "a PSU já está a ser paga" assim
que o relógio do visitante cruzasse 31/12/2026, sem qualquer
confirmação — e ficava invisível a `verificar_datas.py` por a frase ser
composta em runtime, nunca escrita no HTML estático. Afirma o legal,
cita o artigo, e remete para a Segurança Social Direta para o caso
concreto do leitor.

## VOZ IMPERATIVA CADUCA

"Fecha o contrato até [data]" e uma checkbox de prazo continuam a
parecer accionáveis depois de a janela fechar — pior do que uma data
errada, porque instrui para uma acção já impossível sem avisar disso. Ao
escrever um passo de `HowTo`, uma checkbox de `.checklist-final` ou uma
resposta rápida com prazo, pensa em como lê no dia seguinte ao prazo:
ver `CLAUDE.md` → "CLUSTER HABITAÇÃO" → o esqueleto de redacção já
preparado para `garantia-publica-credito-habitacao.html`, para o dia em
que o prazo de 31/12/2026 passar sem prorrogação confirmada — o passo do
`HowTo` deixa de ser instrução accionável e passa a nota de estado,
nunca continua na voz imperativa a fingir que o prazo ainda decorre.

## NOMEAR, NUNCA "DEPENDE"

Se um regime trata casos de forma diferente, nomeia as prestações de
cada grupo — "depende do apoio" sem dizer quais é tão inútil como
generalizar; a pessoa tem de conseguir identificar em que grupo está a
partir do próprio texto. Quando a mesma prestação cai em dois grupos
conforme uma condição — a pensão de orfandade, conforme o órfão integre
ou não o agregado do pensionista de sobrevivência — aparece nos dois,
com o critério explicado ao lado, nunca só num a assumir que quem
procura já sabe em que condição está.

## NÃO SUAVIZAR O QUE MAIS IMPORTA

A informação com consequência vai no corpo do parágrafo, em texto
normal — nunca em nota de rodapé, letra pequena, ou dentro de um
`<details>`/`.zona-cinzenta` quando não é uma dúvida frequente mas sim
uma condição central. "Ao fim do período não há conversão automática e
tens de pedir de novo" é o tipo de frase que não pode ficar escondida
atrás de um clique.

## RESSALVA ESTREITA, DITA COM PRECISÃO

Quando existe uma excepção, escreve-a pelo articulado, nunca pelo
preâmbulo — ver `fact-check/SKILL.md` → "PREÂMBULO NÃO É ARTICULADO" para
a mesma distinção do lado da apuração do facto — e com as palavras
exactas do critério legal, nunca uma paráfrase que alarga ou estreita o
alcance sem querer. "Renovado" quando a lei diz "cessado por iniciativa
do senhorio" alarga a excepção do PAER a quem a lei não cobre — e era
tecnicamente o inverso do previsto (ver `CLAUDE.md` → "CLUSTER
HABITAÇÃO", Decreto-Lei n.º 43/2024). Formula de modo a que quem NÃO
está no caso da excepção perceba isso de imediato, sem ter de decifrar a
negativa.

## ONDE A RESSALVA VAI, POR NÍVEL

Corpo e FAQ visível levam as condições completas, todas as cumulativas
listadas. Resposta rápida e JSON-LD (`FAQPage`, `HowTo`) levam a versão
curta — mas essa versão curta sinaliza sempre que há mais condições e
remete para o corpo, nunca afirma o caso geral como se fosse absoluto.
O absoluto sozinho, sem essa ressalva, nunca aparece em nenhum dos
quatro níveis.

## TEXTO VISÍVEL PASSA PELO NUNO

Processo de aprovação — quem decide, formato, quando escalar — vive em
`steward/SKILL.md` → "TEXTO VISÍVEL AO UTILIZADOR" e → "O QUE SE ESCALA,
EM VEZ DE RESOLVER"; esta skill nunca duplica isso, só decide o quê
escrever antes de chegar lá. Em prosa simples, aos 55 caracteres, sem
blocos de código, sempre antes do commit.

## VER TAMBÉM

`CLAUDE.md` → "LINGUAGEM PARA O UTILIZADOR" cobre clareza para baixa
literacia digital (PT-PT simples, anglicismos, siglas explicadas,
consistência terminológica) — preocupação diferente da desta skill, que
é precisão e prazo de validade do que já está claro. As duas aplicam-se
em conjunto a qualquer texto novo.

## VERIFICAÇÃO FINAL

Suite + `ruff check scripts/ --select E,F,W --ignore E501 .`. PR sem
"Closes".
