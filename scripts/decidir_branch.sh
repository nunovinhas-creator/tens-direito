#!/usr/bin/env bash
# scripts/decidir_branch.sh <branch>
#
# Decide se uma branch remota já está integrada em main e pode ser apagada
# por limpar-branches.yml (issue #276). Escreve uma linha em stdout:
#   APAGAR <motivo>
#   MANTER <commits_unicos> <motivo>
# Nunca apaga nada — só decide; o workflow é que apaga.
#
# Integrada = (a) 0 commits únicos face a origin/main (merge commit /
# fast-forward), OU (b) squash: existe um PR merged dessa branch para main
# cuja cabeça (head.sha) é a cabeça actual da branch, e nenhum PR aberto
# dessa branch. Num squash os commits da branch nunca entram no histórico de
# main, por isso (a) nunca chega a 0. Um push depois do merge muda a cabeça
# e a branch fica (trabalho por integrar).
#
# Exit 1 se a API falhar (nunca devolve APAGAR sem resposta da API); exit 2
# se lhe pedirem para decidir sobre main.
#
# Requer: git com origin/main e origin/<branch> já obtidos, gh + jq,
# GH_TOKEN e REPO (owner/repo) no ambiente.
set -uo pipefail

b="${1:?uso: decidir_branch.sh <branch>}"
if [ "$b" = "main" ]; then
  echo "::error::GUARDRAIL violado — tentativa de decidir sobre 'main'." >&2
  exit 2
fi
REPO="${REPO:?REPO (owner/repo) em falta}"
OWNER="${REPO%%/*}"

if ! cabeca="$(git rev-parse -q --verify "refs/remotes/origin/${b}^{commit}")"; then
  echo "::error::origin/${b} não existe no checkout." >&2
  exit 1
fi
unicos="$(git rev-list --count "origin/main..${cabeca}")"

if [ "$unicos" -eq 0 ]; then
  echo "APAGAR totalmente integrada em main (0 commits únicos)"
  exit 0
fi

if ! prs="$(gh api -X GET "repos/${REPO}/pulls" -f head="${OWNER}:${b}" -f state=all -f per_page=100 2>/tmp/decidir_branch_erro)"; then
  echo "::error::API falhou ao listar os PRs de '${b}': $(cat /tmp/decidir_branch_erro)" >&2
  exit 1
fi
if ! jq -e 'type == "array"' >/dev/null 2>&1 <<< "$prs"; then
  echo "::error::resposta inesperada da API para '${b}': ${prs:0:200}" >&2
  exit 1
fi

aberto="$(jq -r '[.[] | select(.state == "open")][0].number // empty' <<< "$prs")"
if [ -n "$aberto" ]; then
  echo "MANTER ${unicos} PR #${aberto} aberto"
  exit 0
fi

squash="$(jq -r --arg h "$cabeca" \
  '[.[] | select(.merged_at != null and .base.ref == "main" and .head.sha == $h)][0].number // empty' \
  <<< "$prs")"
if [ -n "$squash" ]; then
  echo "APAGAR integrada por squash no PR #${squash} (cabeça ${cabeca:0:7} = cabeça do PR)"
  exit 0
fi

if jq -e '[.[] | select(.merged_at != null and .base.ref == "main")] | length > 0' >/dev/null <<< "$prs"; then
  echo "MANTER ${unicos} PR merged, mas a cabeça mudou depois do merge"
else
  echo "MANTER ${unicos} sem PR merged para main"
fi
