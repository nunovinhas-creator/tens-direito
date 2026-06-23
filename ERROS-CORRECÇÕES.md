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

## ~~Aviso de verificação pendente #001~~ — RESOLVIDO

**Data de detecção:** 23 de junho de 2026
**Data de resolução:** 23 de junho de 2026
**Página afectada:** abono-de-familia.html
**Situação inicial:** Valores da tabela calculados sem fetch confirmado (seg-social.pt devolveu HTTP 403 automaticamente). Marcados com [VERIFICAR].
**Resolução:** Valores confirmados manualmente pelo utilizador em seg-social.pt/abono-de-familia a 23/06/2026. Tabela completamente restruturada com os valores reais por faixa etária (IAS 2026 = 537,13 €). Limite do 1.º escalão corrigido: 1 IAS (537,13 €), não 2 IAS como estava. Faixas etárias alinhadas com a fonte oficial. Marcador [VERIFICAR] removido. JSON-LD FAQ atualizado com os valores correctos.

---

## Página em falta #001

**Data de detecção:** 23 de junho de 2026
**Situação:** bolsa-de-merito.html foi referenciada para revisão mas não existe no repositório.
**Acção necessária:** Criar a página com base nas regras do CLAUDE.md, fazendo fetch prévio a dge.mec.pt/bolsa-de-merito antes de redigir qualquer valor ou condição.

---

## Correcção #004

**Data de detecção:** 23 de junho de 2026
**Página afectada:** acao-social-escolar.html
**Erro encontrado:** 4 ocorrências do link `https://www.dge.mec.pt/acao-social-escolar` no HTML público. Este URL devolve 403 (restrito/requer autenticação) — nunca deve aparecer como link clicável numa página pública.
**Correcção aplicada:** Todas as ocorrências substituídas por `https://www.dge.mec.pt` com texto âncora "Direção-Geral da Educação (dge.mec.pt)". Adicionada nota "Para informação sobre ASE, consulta a secretaria da tua escola ou o portal da DGE." nos locais relevantes.
**Fonte que confirmou a correcção:** Skill `verificar-url` — regra 401/403: página existe mas é restrita, NUNCA usar no HTML público.
**Data de publicação da correcção:** 23 de junho de 2026
