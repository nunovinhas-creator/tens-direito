# Skill: babysit

A mecânica de tomar conta de um PR aberto — o que verificar a cada evento,
o que corrigir sozinho e o que escalar. O critério do que é escalável é
sempre o de `steward` (ver essa skill, que tem precedência quando os dois
existirem) — esta descreve só o "como", não o "quando".

## Uso

Lida antes de agir sobre eventos de CI ou de revisão num PR que se esteja
a vigiar ou a conduzir, a par de `steward`.

## O QUE VERIFICAR

Estado do CI, `mergeable_state`, comentários de revisão novos.

## CORRIGE SOZINHO

Lint, typos, conflitos de merge mecânicos, e falhas de CI cuja causa seja
ambiente (ver `steward`).

## REPORTA E ESPERA

Tudo o que a `steward` lista como escalável. Se o CI falhar, diz a causa
antes de mexeres.

## QUANDO DESISTE

CI verde e mergeable significa que o trabalho acabou — o merge é do Nuno.
Não insistas nem ofereças mais.

## NUNCA

Commitar depois de teres dito que esperavas confirmação. Se o hook
assinalar alterações por commitar, diz, não commites.

## VERIFICAÇÃO FINAL

Suite + `ruff`. PR sem "Closes".
