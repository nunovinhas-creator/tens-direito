"""scripts/garantir_deploy_pages.sh — vigiar o deploy do SHA exacto do push.

Incidente real (2026-10-01, calendario-mensal.yml run 36857076880): o run
partiu de 8128964, fez push de c69d629 e o script vigiou o deploy de
8128964 (GITHUB_SHA = commit que disparou o run, nunca o que o próprio run
acabou de publicar). Esse deploy já tinha terminado na véspera, por isso o
script deu "sucesso" de imediato e o smoke test correu contra a versão
anterior do site, antes do deploy de c69d629 acabar.

Os testes correm o script real com um `gh` falso no PATH (sem rede) e com
uma guarda estática sobre os workflows que fazem push e depois smoke.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "garantir_deploy_pages.sh"
WORKFLOWS = RAIZ / ".github" / "workflows"

SHA_ANTIGO = "8128964" + "0" * 33
SHA_PUSH = "c69d629" + "0" * 33

pytestmark = pytest.mark.skipif(
    shutil.which("bash") is None or shutil.which("jq") is None,
    reason="precisa de bash e jq",
)

GH_FALSO = r"""#!/usr/bin/env bash
# gh falso: regista cada chamada e responde a partir de $GH_RUNS (JSON
# {sha: {"id":..,"status":..,"conclusion":..}}).
echo "$*" >> "$GH_LOG"
if [ "$1" = "api" ] && [ "$2" = "--method" ]; then
  exit 0
fi
url="$2"
sha="${url##*head_sha=}"; sha="${sha%%&*}"
jq -n --argjson runs "$GH_RUNS" --arg sha "$sha" '
  if $runs[$sha] then
    $runs[$sha] + {name: "pages build and deployment", run_number: 1}
  else empty end'
"""


def _correr(tmp_path, runs, env_extra):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(GH_FALSO)
    gh.chmod(0o755)
    log = tmp_path / "gh.log"
    env = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "GH_LOG": str(log),
        "GH_RUNS": json.dumps(runs),
        "GITHUB_REPOSITORY": "dono/repo",
        "GITHUB_SHA": SHA_ANTIGO,
        "TIMEOUT_ESPERA_S": "2",
        "INTERVALO_POLL_S": "1",
        "ESPERA_RERUN_S": "0",
        "MAX_TENTATIVAS": "2",
    }
    env.update(env_extra)
    res = subprocess.run(
        ["bash", str(SCRIPT)], env=env, capture_output=True, text=True, timeout=60
    )
    chamadas = log.read_text().splitlines() if log.exists() else []
    return res, chamadas


def test_vigia_o_sha_do_push_e_nao_o_github_sha(tmp_path):
    # Reproduz o incidente: o deploy do SHA antigo já está concluído, o do
    # SHA do push ainda está a correr. O script tem de esperar pelo segundo.
    runs = {
        SHA_ANTIGO: {"id": 1, "status": "completed", "conclusion": "success"},
        SHA_PUSH: {"id": 2, "status": "in_progress", "conclusion": None},
    }
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    consultas = [c for c in chamadas if "head_sha=" in c]
    assert consultas, res.stdout
    assert all(f"head_sha={SHA_PUSH}" in c for c in consultas), consultas
    assert "Deploy confirmado" not in res.stdout, (
        "deu sucesso com o deploy de outro commit:\n" + res.stdout
    )


def test_confirma_quando_o_deploy_do_sha_do_push_termina(tmp_path):
    runs = {SHA_PUSH: {"id": 2, "status": "completed", "conclusion": "success"}}
    res, _ = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    assert res.returncode == 0
    assert "Deploy confirmado com sucesso (run 2)" in res.stdout


def test_sha_deploy_definido_mas_vazio_falha_em_vez_de_cair_no_github_sha(tmp_path):
    # O output `sha` do step de push em falta nunca pode voltar a vigiar o
    # commit errado em silêncio.
    runs = {SHA_ANTIGO: {"id": 1, "status": "completed", "conclusion": "success"}}
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": ""})
    assert res.returncode != 0
    assert not [c for c in chamadas if "head_sha=" in c]


def test_sem_sha_deploy_usa_github_sha(tmp_path):
    # smoke-producao.yml (on: push) — aí GITHUB_SHA é o commit publicado.
    runs = {SHA_ANTIGO: {"id": 1, "status": "completed", "conclusion": "success"}}
    res, chamadas = _correr(tmp_path, runs, {})
    assert res.returncode == 0
    assert all(f"head_sha={SHA_ANTIGO}" in c for c in chamadas if "head_sha=" in c)


def test_deploy_falhado_e_relancado(tmp_path):
    runs = {SHA_PUSH: {"id": 7, "status": "completed", "conclusion": "failure"}}
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    assert res.returncode == 0
    assert any("actions/runs/7/rerun" in c for c in chamadas), chamadas


def test_deploy_ainda_em_curso_nao_e_falha_nem_relancado(tmp_path):
    # Caso real (pipeline-diario.yml, run 37199982253, 2026-10-04): ao fim
    # do tempo o deploy ainda corria (conclusion=null); o script registou
    # "deploy falhou" e pediu um rerun de um run em curso.
    runs = {SHA_PUSH: {"id": 7, "status": "in_progress", "conclusion": None}}
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    assert res.returncode == 0
    assert not any("rerun" in c for c in chamadas), chamadas
    assert "deploy ainda em curso" in res.stdout
    assert "falhou" not in res.stdout, res.stdout


@pytest.mark.parametrize("conclusao", ["timed_out", "startup_failure", "action_required"])
def test_so_failure_e_relancado(tmp_path, conclusao):
    runs = {SHA_PUSH: {"id": 7, "status": "completed", "conclusion": conclusao}}
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    assert res.returncode == 0
    assert not any("rerun" in c for c in chamadas), chamadas


def test_deploy_cancelado_nunca_e_relancado(tmp_path):
    # O Pages cancela o deploy de um commit quando chega outro mais novo
    # (caso real: run 36713411216, 2026-09-30). Relançá-lo publicaria a
    # versão antiga por cima da nova.
    runs = {SHA_PUSH: {"id": 7, "status": "completed", "conclusion": "cancelled"}}
    res, chamadas = _correr(tmp_path, runs, {"SHA_DEPLOY": SHA_PUSH})
    assert res.returncode == 0
    assert not any("rerun" in c for c in chamadas), chamadas


def _passos(workflow):
    dados = yaml.safe_load(workflow.read_text(encoding="utf-8"))
    for job in dados.get("jobs", {}).values():
        yield from job.get("steps", [])


WORKFLOWS_COM_PUSH_E_DEPLOY = sorted(
    w.name
    for w in WORKFLOWS.glob("*.yml")
    if any(p.get("id") == "commit_push" for p in _passos(w))
    and any("garantir_deploy_pages.sh" in str(p.get("run", "")) for p in _passos(w))
)


def test_ha_workflows_com_push_e_deploy():
    assert set(WORKFLOWS_COM_PUSH_E_DEPLOY) >= {
        "calendario-mensal.yml",
        "pipeline-diario.yml",
        "shadow-daily.yml",
    }


@pytest.mark.parametrize("nome", WORKFLOWS_COM_PUSH_E_DEPLOY)
def test_workflow_passa_o_sha_do_push_ao_script(nome):
    passos = list(_passos(WORKFLOWS / nome))
    push = next(p for p in passos if p.get("id") == "commit_push")
    linhas = [ln.strip() for ln in push["run"].splitlines()]
    i_push = max(i for i, ln in enumerate(linhas) if ln.startswith("git push"))
    assert any(
        "git rev-parse HEAD" in ln and "sha=" in ln for ln in linhas[i_push + 1 :]
    ), f"{nome}: o step commit_push tem de exportar sha=$(git rev-parse HEAD) depois do push"

    i_deploy = next(
        i for i, p in enumerate(passos) if "garantir_deploy_pages.sh" in str(p.get("run", ""))
    )
    deploy = passos[i_deploy]
    assert deploy.get("env", {}).get("SHA_DEPLOY") == "${{ steps.commit_push.outputs.sha }}"
    assert "|| true" not in deploy["run"]

    i_smoke = next(
        i for i, p in enumerate(passos) if "smoke_producao.sh" in str(p.get("run", ""))
    )
    assert i_deploy < i_smoke, f"{nome}: o smoke tem de correr depois do deploy"
