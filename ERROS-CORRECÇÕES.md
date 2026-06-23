# Registo de Erros e Correcções — Tens Direito

---

## Correcção #001

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** A secção "O que cobre" listava "Manuais escolares em regime de empréstimo gratuito" como benefício exclusivo do Escalão A, e "Manuais escolares em regime de empréstimo (parcial)" para o Escalão B. Esta informação estava errada.
**Correcção aplicada:** Os manuais escolares são gratuitos para TODOS os alunos do ensino público via programa MEGA (Manuais Escolares Gratuitos), independentemente do escalão ASE. A secção foi corrigida e foi adicionado bloco informativo sobre o MEGA com link para mega.mec.pt.
**Fonte que confirmou a correcção:** CLAUDE.md do repositório — "ATENÇÃO CONFIRMADA: manuais gratuitos para TODOS os alunos do ensino público, independentemente de escalão ASE"
**Data de publicação da correcção:** 23 de junho de 2026

---

## Correcção #002

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** O passo 1 do "Como candidatar" indicava que os encarregados de educação devem juntar "declaração de IRS ou última declaração de rendimentos". O mesmo erro estava no JSON-LD HowTo (passo 1).
**Correcção aplicada:** A declaração exigida na candidatura à ASE é emitida pela Segurança Social (não é a declaração de IRS). O texto foi corrigido em ambos os locais (HTML visível e JSON-LD) para "declaração de rendimentos emitida pela Segurança Social (pedida em seg-social.pt ou num balcão da SS)".
**Fonte que confirmou a correcção:** CLAUDE.md do repositório — "ATENÇÃO: a declaração que os EE entregam é emitida pela Segurança Social, não é declaração de rendimentos própria"
**Data de publicação da correcção:** 23 de junho de 2026

---

## Aviso de verificação pendente #001

**Data de detecção:** 23 de junho de 2026
**Página afectada:** abono-de-familia.html
**Situação:** Os valores da tabela de escalões (ex.: 68,19 € para 1.º escalão até 36 meses) foram calculados com base em IAS 537,13 € e percentagens históricas do abono de família, sem fetch confirmado à fonte primária (seg-social.pt devolveu HTTP 403 em 23/06/2026).
**Estado:** Marcado com [VERIFICAR] na nota da tabela. Valores não removidos porque a metodologia de cálculo é conhecida, mas carecem de confirmação oficial.
**Acção necessária:** Quando seg-social.pt estiver acessível, confirmar os valores exactos e remover o aviso [VERIFICAR].
**Prazo:** Próxima sessão de revisão mensal.

---

## Página em falta #001

**Data de detecção:** 23 de junho de 2026
**Situação:** bolsa-de-merito.html foi referenciada para revisão mas não existe no repositório.
**Acção necessária:** Criar a página com base nas regras do CLAUDE.md, fazendo fetch prévio a dge.mec.pt/bolsa-de-merito antes de redigir qualquer valor ou condição.
