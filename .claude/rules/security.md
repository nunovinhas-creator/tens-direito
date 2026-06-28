# Regras de Segurança — Tens Direito

## Credenciais e Tokens

- NUNCA hardcodar tokens, API keys, passwords ou secrets no código
- NUNCA incluir credenciais em mensagens de commit, comentários ou logs
- Secrets pertencem exclusivamente ao GitHub Actions Secrets — nunca ao repositório

## URLs e Portais Oficiais

- NUNCA usar subpaths de portais do Estado sem confirmar que devolvem 200
- URLs PROIBIDAS (áreas privadas / devolvem 404 ou 403):
  - `app.seg-social.pt/ptss/ssd` — área privada
  - Qualquer `/ptss/` sem ser homepage
- Quando um subpath falha: usar a homepage do domínio
- Lista completa de URLs verificados em `CLAUDE.md` secção "FONTES VERIFICADAS"

## Ficheiros Protegidos

- NUNCA modificar ficheiros HTML manuais via pipeline automático
- Apenas estes ficheiros podem ser escritos automaticamente:
  - `index.html` — só data de verificação
  - `noticias.html` — notícia do dia via RSS
  - `CLAUDE.md` — data de revisão
  - `README.md` — estado do repositório
  - `data/scraped/*.json` — dados do scraper
- Guardrail implementado em `scripts/gerar_noticias.py` e em `pipeline-diario.yml`

## Git e Branches

- NUNCA fazer push para branch diferente de `main`
- NUNCA criar branches novas
- NUNCA usar `--no-verify` para contornar hooks
- NUNCA fazer `git push --force`

## Publicação de Factos

- NUNCA publicar valores, condições ou prazos de memória
- SEMPRE ir à fonte primária antes de redigir
- SEMPRE incluir data de verificação e link para fonte
- Se a fonte não confirmar o facto: o facto não entra no site
