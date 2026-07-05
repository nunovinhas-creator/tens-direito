#!/usr/bin/env bash
# scripts/smoke_producao.sh
#
# Smoke test de produção — confirma que as páginas críticas do site
# respondem 200 depois de cada deploy do GitHub Pages, para apanhar
# falhas silenciosas como as já documentadas em CLAUDE.md
# ("##[error]Deployment failed, try again later." em
# actions/deploy-pages@v5, sem qualquer sinal de erro no resto do
# pipeline — só descoberto ao visitar a página e encontrar 404).
#
# Lê a lista de páginas de scripts/urls_criticas.txt (único sítio a
# editar — nunca hardcoded aqui nem no workflow). Para as páginas de
# simulador, confirma também que o corpo da resposta contém a string
# "Verificado a" — apanha o caso de a página responder 200 mas servir
# conteúdo errado ou desactualizado (ex.: cache do CDN com uma versão
# anterior), não só o 404.
#
# Uso: scripts/smoke_producao.sh
# Variável de ambiente DOMINIO permite apontar para outro host (usado
# nos testes locais deste script, nunca em produção real).
#
# TENTATIVAS/ESPERA_S (2026-07-05): o workflow passou de `workflow_run`
# (nunca disparava — ver smoke-producao.yml) para `push` directo a
# main, que dispara quase instantaneamente, antes de o deploy do Pages
# estar necessariamente publicado. 9 tentativas × 30s = até ~4,5 min de
# tolerância à propagação do Pages, sem penalizar o caso comum (sai do
# ciclo assim que um 200 é confirmado — o deploy real observado demora
# tipicamente segundos, não minutos).
set -uo pipefail

DOMINIO="${DOMINIO:-https://tensdireito.com}"
LISTA="$(dirname "$0")/urls_criticas.txt"
USER_AGENT="TensDireito-SmokeTest/1.0 (+https://tensdireito.com/sobre.html)"
TENTATIVAS=9
ESPERA_S=30

# Páginas de simulador — a verificação extra de conteúdo só se aplica
# a estas (as restantes só precisam do 200). Acrescentar aqui se um
# simulador novo for publicado.
SIMULADORES=("/simulador-abono.html" "/simulador-ase.html" "/simulador-csi.html")

falhas=0

e_simulador() {
  local caminho="$1"
  local s
  for s in "${SIMULADORES[@]}"; do
    [ "$caminho" = "$s" ] && return 0
  done
  return 1
}

verificar_url() {
  local caminho="$1"
  local url="${DOMINIO}${caminho}"
  local corpo_ficheiro
  corpo_ficheiro="$(mktemp)"
  local tentativa http_code

  for tentativa in $(seq 1 "$TENTATIVAS"); do
    http_code=$(curl -sS -A "$USER_AGENT" -o "$corpo_ficheiro" -w "%{http_code}" "$url" 2>/tmp/smoke_curl_err.log)
    if [ "$http_code" = "200" ]; then
      break
    fi
    echo "::warning::${url} devolveu ${http_code:-erro de rede} (tentativa ${tentativa}/${TENTATIVAS})"
    if [ "$tentativa" -lt "$TENTATIVAS" ]; then
      sleep "$ESPERA_S"
    fi
  done

  if [ "$http_code" != "200" ]; then
    echo "::error::${url} falhou após ${TENTATIVAS} tentativas (último código: ${http_code:-erro de rede})"
    rm -f "$corpo_ficheiro"
    return 1
  fi

  if e_simulador "$caminho" && ! grep -q "Verificado a" "$corpo_ficheiro"; then
    echo "::error::${url} devolveu 200 mas o corpo não contém 'Verificado a' — pode estar a servir conteúdo errado ou desactualizado"
    rm -f "$corpo_ficheiro"
    return 1
  fi

  echo "OK  ${url} (${http_code})"
  rm -f "$corpo_ficheiro"
  return 0
}

if [ ! -f "$LISTA" ]; then
  echo "::error::Lista de URLs não encontrada: ${LISTA}"
  exit 1
fi

while IFS= read -r linha || [ -n "$linha" ]; do
  linha="$(echo "$linha" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  [ -z "$linha" ] && continue
  case "$linha" in
    \#*) continue ;;
  esac

  if ! verificar_url "$linha"; then
    falhas=$((falhas + 1))
  fi
done < "$LISTA"

if [ "$falhas" -gt 0 ]; then
  echo "=== ${falhas} página(s) falharam o smoke test ==="
  exit 1
fi

echo "=== Todas as páginas críticas responderam correctamente ==="
