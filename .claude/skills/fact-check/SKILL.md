# Skill: fact-check

Aprofunda a verificação de factos legais antes de entrarem numa página —
graus de confiança, onde procurar primeiro, e os erros de leitura que já
aconteceram neste projecto. Não é política de PRs — para isso ver
`steward/SKILL.md`, que esta skill nunca substitui nem repete.

## Uso

Invocar sempre que um facto novo (valor, prazo, condição, citação de
diploma) vai entrar numa página, num YAML de `dados/parametros/`, ou numa
correcção a um já publicado — antes de escrever, nunca depois. Complementa
`verificar-url` (testa se o link existe, não se o conteúdo está certo) e a
divisão de trabalho já definida em `steward/SKILL.md` → "FONTES PRIMÁRIAS":
a verificação faz-se sempre no chat, o Code aplica.

## ESCALA DE GRAUS

O grau vai escrito junto ao facto — comentário no YAML, nota na sessão —
nunca assumido em silêncio.

- **GRAU 1** — texto legal lido na íntegra, na fonte oficial ou num PDF do
  diploma guardado em `dados/fontes/`.
- **GRAU 2** — espelho de consolidação, ou triangulação de ≥2 fontes
  independentes. Regista sempre a data da versão lida: uma consolidação de
  2023 não reflecte alterações posteriores.
- **GRAU 3** — fonte secundária única. Não sustenta publicação.

## ANTES DE PROCURAR FORA

Verifica `dados/fontes/` antes de qualquer pesquisa externa — o PDF do
diploma pode já lá estar. Foi o que aconteceu com o Decreto-Lei n.º
166/2026 (fórmula do artigo 17.º): procurado na web quando já estava
guardado no repositório. Para ler: `pdftotext -layout ficheiro.pdf -` do
lado com acesso real resolve, quando o ambiente tiver `poppler-utils`.

## ACESSOS CONHECIDOS

- `diariodarepublica.pt` e `files.dre.pt` — `EGRESS_BLOCKED` no sandbox do
  Code; as páginas de detalhe (`/dr/detalhe/...`) exigem JavaScript mesmo
  fora do sandbox.
- `dre.tretas.org` — serve o texto integral, mas bloqueia por detecção de
  bots a meio de uma sessão de leitura. Se falhar, não insistas — muda de
  espelho.
- Espelhos que já serviram texto oficial completo: PGDL (`pgdlisboa.pt`),
  portais de administrações regionais (ex. `at.madeira.gov.pt`),
  consolidações publicadas por organismos (Autoridade Tributária, Ordem
  dos Advogados).
- A verificação primária faz-se sempre no chat; o Code aplica — ver
  `steward/SKILL.md` → "FONTES PRIMÁRIAS" para a divisão de trabalho.

## PREÂMBULO NÃO É ARTICULADO

O preâmbulo declara intenção; a norma vive no articulado. Já aconteceu:
`dados/parametros/habitacao.yaml` (`paer_contrato_data_limite`) citava
"mesmas partes" — texto do preâmbulo do Decreto-Lei n.º 43/2024 — quando
o articulado (art. 3.º/2 do DL 20-B/2023, na redação do 43/2024) exige só
o **mesmo locatário**, nunca o mesmo senhorio (corrigido 2026-09-15, Issue
#198). Uma condição ou lista que só existe no preâmbulo nunca se cita
como se fosse artigo.

## NÃO ASSUMIR "ALTERAÇÃO SÓ DE FORMA"

Ver também `steward/SKILL.md` → "NUNCA RESOLVER POR SUSPEITA", que já
cobre o princípio geral. Aqui, o ponto específico: um diploma descrito
como "altera" outro pode acrescentar um direito inteiro, não só
reformular o que já existia — confirma sempre QUAL artigo mudou, nunca só
a ementa. Caso real: o artigo 46.º do Decreto-Lei n.º 91/2009 (subsídios
sociais de parentalidade) só tem seis alíneas porque a Lei n.º 65/2023
aditou a do subsídio por deslocação a unidade hospitalar fora da ilha —
uma leitura do texto original de 2009, sem confirmar a versão consolidada
mais recente, teria dado por certo que essa prestação não estava coberta
(Issue #223).

## LEI DE AUTORIZAÇÃO NÃO É O DECRETO-LEI

Uma autorização legislativa diz o que o Governo PODE fazer, nunca o que
fez — o decreto-lei que a executa pode cumprir o mesmo objectivo por um
mecanismo completamente diferente do previsto. Caso real (Issue #195,
PSU): a Lei n.º 36/2026 deixava as ponderações de "adultos equivalentes"
e a revisão do CSI "ainda por fixar"/"em 90 dias" — o Decreto-Lei n.º
166/2026 fixou os valores directamente (art. 24.º/2) e resolveu o CSI por
outra via (art. 48.º, alteração directa ao DL 232/2005), nunca pela
revisão prevista. As duas frases herdadas da autorização ficaram
desactualizadas assim que o decreto-lei saiu — só não chegaram a uma
página publicada porque alguém releu o texto final artigo a artigo antes
de confiar na intenção anunciada. Nunca presumir que o decreto-lei cumpre
a autorização à letra.

## NUNCA CHAMAR "CONFIRMADO" A UMA INFERÊNCIA

Se a conclusão vem de leitura a contrario ou de estrutura sistemática — a
norma pertence a uma categoria que o diploma não nomeia directamente, ver
`steward/SKILL.md` → "CATEGORIA vs ENUMERAÇÃO" — diz-se sempre que é
leitura nossa, com o artigo que a sustenta ao lado. Nunca "confirmado pela
lei" para uma conclusão que exigiu um raciocínio nosso para lá chegar;
quem discordar tem de conseguir verificar a partir da própria citação.

## O QUE NÃO FOI CONFIRMADO REGISTA-SE

"Não consegui ler" é um resultado válido — preferível a inferir a partir
de fonte secundária. O que fica por confirmar regista-se em
`VERIFICACAO-PENDENTE.md` (URL/diploma + motivo) ou em `ROADMAP.md` →
"TRABALHO FUTURO REGISTADO", sempre com o âmbito já reduzido ao que falta
em concreto — ex. "falta só a Portaria n.º 187/2025/1, o resto da cadeia
já está confirmado" — nunca um "confirmar diploma X" genérico que obriga
a repetir toda a investigação da próxima vez.
