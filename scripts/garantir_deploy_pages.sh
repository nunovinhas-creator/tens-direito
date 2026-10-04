#!/usr/bin/env bash
# scripts/garantir_deploy_pages.sh
#
# "pages build and deployment" é um workflow dinâmico gerido
# internamente pelo GitHub Pages — sem ficheiro .yml no repositório
# (confirmado via API: path "dynamic/pages/pages-build-deployment"),
# por isso nunca podemos editar a sua lógica nem acrescentar-lhe
# retries internos (mesma limitação já documentada em CLAUDE.md
# "GATILHO CORRIGIDO" para o `workflow_run` que nunca disparava).
#
# Este script trata o problema pelo lado de fora: corre a seguir a um
# push nosso, espera que o deploy do commit publicado termine e, se falhar
# (conclusion=failure — nunca outro estado) com o erro genérico "Deployment failed, try
# again later." — falha de infraestrutura confirmada 3 vezes nesta
# sessão e nas duas anteriores, nunca relacionada com o conteúdo —
# dispara automaticamente um novo deploy via API em vez de esperar por
# intervenção manual (que até agora era sempre um humano a ver a
# notificação de email e a correr `rerun_workflow_run` à mão).
#
# Nunca é um gate rígido: se não conseguir confirmar ou recuperar o
# deploy dentro do tempo limite, sai com sucesso (exit 0) na mesma —
# o smoke test que corre a seguir é que continua a ser a verificação
# real de produção; este script só tenta reduzir a necessidade de
# intervenção manual antes disso.
#
# Requer: gh CLI + jq (ambos pré-instalados nos runners do GitHub
# Actions), GH_TOKEN no ambiente e permissions: actions: write no
# workflow que o chama (para poder disparar o rerun via API).
set -uo pipefail

# Commit a vigiar: SHA_DEPLOY quando o workflow acabou de fazer push (o
# HEAD depois do push — GITHUB_SHA é o commit que DISPAROU o run, cujo
# deploy normalmente já terminou; incidente de 2026-10-01 em
# calendario-mensal.yml, ver tests/test_garantir_deploy_pages.py).
# Sem SHA_DEPLOY (smoke-producao.yml, on: push) GITHUB_SHA é o commit
# publicado. SHA_DEPLOY definido mas vazio é um erro do workflow — nunca
# cai em silêncio para GITHUB_SHA.
if [ -n "${SHA_DEPLOY+x}" ]; then
  if [ -z "$SHA_DEPLOY" ]; then
    echo "::error::SHA_DEPLOY definido mas vazio — o step de push não exportou o SHA publicado."
    exit 1
  fi
  SHA="$SHA_DEPLOY"
else
  SHA="${GITHUB_SHA:-}"
fi
REPO="${GITHUB_REPOSITORY:-}"

if [ -z "$SHA" ] || [ -z "$REPO" ]; then
  echo "::warning::GITHUB_SHA ou GITHUB_REPOSITORY em falta — a saltar verificação do deploy (só corre dentro do GitHub Actions)."
  exit 0
fi

MAX_TENTATIVAS="${MAX_TENTATIVAS:-3}"
TIMEOUT_ESPERA_S="${TIMEOUT_ESPERA_S:-180}"
INTERVALO_POLL_S="${INTERVALO_POLL_S:-10}"
ESPERA_RERUN_S="${ESPERA_RERUN_S:-5}"

echo "A vigiar o deploy do GitHub Pages para ${SHA}..."

for tentativa in $(seq 1 "$MAX_TENTATIVAS"); do
  echo "--- Tentativa ${tentativa}/${MAX_TENTATIVAS} ---"
  decorrido=0
  run_id=""
  conclusion=""
  status=""

  while [ "$decorrido" -lt "$TIMEOUT_ESPERA_S" ]; do
    resultado=$(gh api "repos/${REPO}/actions/runs?head_sha=${SHA}&per_page=20" \
      --jq '[.workflow_runs[] | select(.name=="pages build and deployment")] | sort_by(.run_number) | last // empty' 2>/dev/null || true)

    if [ -n "$resultado" ]; then
      run_id=$(echo "$resultado" | jq -r '.id')
      status=$(echo "$resultado" | jq -r '.status')
      conclusion=$(echo "$resultado" | jq -r '.conclusion')
      echo "run ${run_id}: status=${status} conclusion=${conclusion}"
      [ "$status" = "completed" ] && break
    else
      echo "Ainda sem run de 'pages build and deployment' para este commit..."
    fi

    sleep "$INTERVALO_POLL_S"
    decorrido=$((decorrido + INTERVALO_POLL_S))
  done

  if [ "$conclusion" = "success" ]; then
    echo "Deploy confirmado com sucesso (run ${run_id})."
    exit 0
  fi

  if [ -z "$run_id" ]; then
    echo "::warning::não foi possível encontrar o run do deploy dentro do tempo limite — a continuar sem confirmar (o smoke test a seguir ainda vai apanhar uma falha real)."
    exit 0
  fi

  # Ainda a correr ao fim do tempo (status != completed, conclusion=null)
  # não é falha — relançar um deploy em curso só o atrasaria (caso real:
  # pipeline-diario.yml, run 37199982253, 2026-10-04). O smoke a seguir
  # espera pela versão servida e é o gate.
  if [ "$status" != "completed" ]; then
    echo "::notice::deploy ainda em curso (run ${run_id}, status=${status}) ao fim de ${TIMEOUT_ESPERA_S}s — sem relançar; o smoke test a seguir confirma a versão servida."
    exit 0
  fi

  # Cancelado = o Pages substituiu este deploy por um de um commit mais
  # novo. Relançá-lo publicaria a versão antiga por cima da nova.
  if [ "$conclusion" = "cancelled" ]; then
    echo "::warning::deploy de ${SHA} cancelado (substituído por um commit mais novo) — sem relançar."
    exit 0
  fi

  # Só failure é relançado; qualquer outra conclusão fica para o smoke.
  if [ "$conclusion" != "failure" ]; then
    echo "::warning::deploy terminou com conclusion=${conclusion} (run ${run_id}) — sem relançar; o smoke test a seguir decide."
    exit 0
  fi

  echo "::warning::deploy falhou (conclusion=failure) — a tentar novamente via API (run ${run_id})."
  if ! gh api --method POST "repos/${REPO}/actions/runs/${run_id}/rerun" >/dev/null 2>&1; then
    echo "::warning::pedido de rerun falhou (run já pode estar em nova tentativa, ou sem permissão) — a desistir de recuperar automaticamente."
    exit 0
  fi
  sleep "$ESPERA_RERUN_S"
done

echo "::warning::deploy continuou a falhar após ${MAX_TENTATIVAS} tentativa(s) automáticas — o smoke test a seguir vai reportar isto como falha real."
exit 0
