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
LISTA="${LISTA_URLS:-$(dirname "$0")/urls_criticas.txt}"
USER_AGENT="TensDireito-SmokeTest/1.0 (+https://tensdireito.com/sobre.html)"
TENTATIVAS="${TENTATIVAS:-9}"
ESPERA_S="${ESPERA_S:-30}"

# Versão servida (issue #281): até ~10 min (20 × 30 s) para o site servir
# o commit publicado — o CDN do Pages guarda páginas até 10 min.
TENTATIVAS_VERSAO="${TENTATIVAS_VERSAO:-20}"
ESPERA_VERSAO_S="${ESPERA_VERSAO_S:-30}"

# Páginas de simulador — a verificação extra de conteúdo só se aplica
# a estas (as restantes só precisam do 200). Acrescentar aqui se um
# simulador novo for publicado.
SIMULADORES=("/simulador-abono.html" "/simulador-ase.html" "/simulador-csi.html" "/simulador-imt-jovem.html" "/simulador-universal.html")

# FASE 3 (sessão de dados abertos, 2026-07-19): além do 200, o JSON
# consolidado tem mesmo de parsear como JSON válido — um 200 com corpo
# truncado/corrompido (ex.: cache de CDN a meio de um deploy) nunca deve
# passar despercebido só porque o status code estava certo.
JSON_A_VALIDAR=("/dados/parametros.json")

falhas=0

e_simulador() {
  local caminho="$1"
  local s
  for s in "${SIMULADORES[@]}"; do
    [ "$caminho" = "$s" ] && return 0
  done
  return 1
}

e_json_a_validar() {
  local caminho="$1"
  local j
  for j in "${JSON_A_VALIDAR[@]}"; do
    [ "$caminho" = "$j" ] && return 0
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

  if e_json_a_validar "$caminho" && ! python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$corpo_ficheiro" 2>/dev/null; then
    echo "::error::${url} devolveu 200 mas o corpo não parseia como JSON válido"
    rm -f "$corpo_ficheiro"
    return 1
  fi

  # dados/tensdireito.db (FASE 3): confirma que o GitHub Pages serve o
  # ficheiro com CORS aberto, condição necessária para o Datasette Lite o
  # conseguir ler directamente no browser de outro domínio. Nunca falha o
  # smoke test por isto — só ::warning:: — porque isto é uma confirmação
  # de comportamento da plataforma, não do nosso código, e um cabeçalho
  # ausente não significa que a página em si esteja quebrada.
  if [ "$caminho" = "/dados/tensdireito.db" ]; then
    if ! curl -sS -A "$USER_AGENT" -I "$url" 2>/dev/null | grep -qi "^access-control-allow-origin:"; then
      echo "::warning::${url} não devolveu Access-Control-Allow-Origin — confirmar manualmente se o Datasette Lite consegue mesmo ler o ficheiro"
    fi
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

# ── Versão servida (issue #281) ─────────────────────────────────────────────
# 200 + "Verificado a" não prova a versão: a 2026-10-01
# (calendario-mensal.yml, run 36857076880) o smoke deu verde contra o site
# anterior. Aqui, cada HTML publicado que o commit vigiado alterou (ou a
# homepage, se não alterou nenhum) tem de ser servido byte a byte como está
# nesse commit — ou como está num commit mais novo de main (outro push pode
# ter chegado entretanto). Pedido com ?v=<sha> para não ler a cache do CDN.
# Gate rígido: sem coincidência no fim do orçamento, o smoke falha.

# Commit vigiado: SHA_DEPLOY quando o workflow acabou de fazer push;
# senão GITHUB_SHA (smoke-producao.yml). SHA_DEPLOY vazio é um erro.
sha_vigiado() {
  if [ -n "${SHA_DEPLOY+x}" ]; then
    if [ -z "$SHA_DEPLOY" ]; then
      echo "::error::SHA_DEPLOY definido mas vazio — o step de push não exportou o SHA publicado." >&2
      return 1
    fi
    echo "$SHA_DEPLOY"
  else
    echo "${GITHUB_SHA:-}"
  fi
}

# Caminho no repositório → caminho servido. Só as páginas do site
# (raiz, p/, documentos/), as mesmas de encontrar_paginas().
e_html_publicado() {
  case "$1" in
    */*/*) return 1 ;;
    p/*.html|documentos/*.html) return 0 ;;
    */*) return 1 ;;
    *.html) return 0 ;;
  esac
  return 1
}

caminho_servido() {
  if [ "$1" = "index.html" ]; then echo "/"; else echo "/$1"; fi
}

# Blobs aceites para um ficheiro: o do commit vigiado e os de cada commit
# mais novo até ao topo de main que o alterou.
blobs_aceites() {
  local ficheiro="$1" topo="$2" c
  git rev-parse "${SHA}:${ficheiro}" 2>/dev/null
  if [ -n "$topo" ]; then
    for c in $(git log --format=%H "${SHA}..${topo}" -- "$ficheiro" 2>/dev/null); do
      git rev-parse "${c}:${ficheiro}" 2>/dev/null
    done
  fi
}

verificar_versao_servida() {
  if ! SHA="$(sha_vigiado)"; then
    return 1
  fi
  if [ -z "$SHA" ]; then
    echo "::warning::sem SHA_DEPLOY nem GITHUB_SHA — verificação da versão servida saltada (só corre dentro do GitHub Actions)."
    return 0
  fi
  if ! git cat-file -e "${SHA}^{commit}" 2>/dev/null; then
    echo "::error::commit vigiado ${SHA} não existe no checkout — sem ele não há como provar a versão servida."
    return 1
  fi
  if ! git cat-file -e "${SHA}^1^{commit}" 2>/dev/null; then
    echo "::error::o commit-pai de ${SHA} não está no checkout (fetch-depth insuficiente) — não é possível saber que ficheiros o push alterou."
    return 1
  fi

  local topo="${REF_TOPO:-}"
  if [ -z "$topo" ]; then
    git fetch -q origin main 2>/dev/null || true
    if git rev-parse -q --verify origin/main >/dev/null; then topo="origin/main"; else topo="HEAD"; fi
  fi
  if ! git merge-base --is-ancestor "$SHA" "$topo" 2>/dev/null; then
    topo=""
  fi

  local ficheiros=() f
  while IFS= read -r f; do
    [ -n "$f" ] && e_html_publicado "$f" && ficheiros+=("$f")
  done < <(git diff --name-only --no-renames --diff-filter=d "${SHA}^1" "$SHA")
  if [ "${#ficheiros[@]}" -eq 0 ]; then
    echo "O commit ${SHA:0:7} não alterou HTML publicado — a comparar a homepage."
    ficheiros=("index.html")
  fi

  local corpo pendentes=("${ficheiros[@]}") tentativa url servido proximos
  corpo="$(mktemp)"
  for tentativa in $(seq 1 "$TENTATIVAS_VERSAO"); do
    proximos=()
    for f in "${pendentes[@]}"; do
      url="${DOMINIO}$(caminho_servido "$f")?v=${SHA}"
      if curl -sS -f -A "$USER_AGENT" -H "Cache-Control: no-cache" -o "$corpo" "$url" 2>/dev/null \
         && servido="$(git hash-object "$corpo")" \
         && blobs_aceites "$f" "$topo" | grep -qx "$servido"; then
        echo "OK  versão servida de /${f} = ${SHA:0:7} ou mais nova"
      else
        proximos+=("$f")
      fi
    done
    pendentes=("${proximos[@]}")
    [ "${#pendentes[@]}" -eq 0 ] && break
    echo "::warning::${#pendentes[@]} ficheiro(s) ainda não servem ${SHA:0:7} (tentativa ${tentativa}/${TENTATIVAS_VERSAO}): ${pendentes[*]}"
    [ "$tentativa" -lt "$TENTATIVAS_VERSAO" ] && sleep "$ESPERA_VERSAO_S"
  done
  rm -f "$corpo"

  if [ "${#pendentes[@]}" -gt 0 ]; then
    for f in "${pendentes[@]}"; do
      echo "::error::/${f} não serve a versão de ${SHA:0:7} (nem uma mais nova) ao fim de ${TENTATIVAS_VERSAO} tentativas — o deploy não chegou ou o site serve uma versão antiga."
    done
    return 1
  fi
  return 0
}

if ! verificar_versao_servida; then
  falhas=$((falhas + 1))
fi

if [ "$falhas" -gt 0 ]; then
  echo "=== ${falhas} página(s) falharam o smoke test ==="
  exit 1
fi

echo "=== Todas as páginas críticas responderam correctamente ==="
