"""
`scripts/decidir_branch.sh` (issue #276): limpar-branches.yml só apagava
branches com 0 commits únicos face a main — num merge por squash isso nunca
acontece, e a branch ficava na Issue "Branches órfãs" como se tivesse
trabalho por integrar (caso real: #271).

Corre o script real contra um repositório git temporário (refs
origin/main e origin/<b>) e um `gh` falso que devolve a lista de PRs.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).parent.parent
SCRIPT = RAIZ / "scripts" / "decidir_branch.sh"
WORKFLOW = RAIZ / ".github" / "workflows" / "limpar-branches.yml"
REPO = "dono/repo"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "trabalho")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    (r / "a.txt").write_text("base\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    base = _git(r, "rev-parse", "HEAD")
    (r / "a.txt").write_text("trabalho\n")
    _git(r, "commit", "-q", "-am", "trabalho na branch")
    cabeca = _git(r, "rev-parse", "HEAD")
    # main recebe o mesmo conteúdo num commit novo (squash).
    _git(r, "checkout", "-q", "-b", "main", base)
    (r / "a.txt").write_text("trabalho\n")
    _git(r, "commit", "-q", "-am", "squash (#1)")
    _git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(r, "update-ref", "refs/remotes/origin/feat", cabeca)
    return r, cabeca


def _gh_falso(tmp_path: Path, resposta, falhar: bool = False) -> Path:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    (tmp_path / "resposta.json").write_text(json.dumps(resposta))
    gh = bindir / "gh"
    gh.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$*" >> "{tmp_path}/chamadas.log"\n'
        + ('echo "HTTP 502" >&2; exit 1\n' if falhar else f'cat "{tmp_path}/resposta.json"\n')
    )
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    return bindir


def _correr(repo: Path, tmp_path: Path, branch: str, resposta=(), falhar=False):
    bindir = _gh_falso(tmp_path, list(resposta), falhar)
    env = dict(os.environ, PATH=f"{bindir}:{os.environ['PATH']}", REPO=REPO, GH_TOKEN="x")
    return subprocess.run(
        ["bash", str(SCRIPT), branch], cwd=repo, env=env, capture_output=True, text=True
    )


def _pr(numero, cabeca, *, merged=True, base="main", estado="closed"):
    return {
        "number": numero,
        "state": estado,
        "merged_at": "2026-10-04T09:39:22Z" if merged else None,
        "base": {"ref": base},
        "head": {"sha": cabeca, "ref": "feat"},
    }


def test_1_squash_merged_com_a_mesma_cabeca_apaga(repo, tmp_path):
    r, cabeca = repo
    res = _correr(r, tmp_path, "feat", [_pr(271, cabeca)])
    assert res.returncode == 0, res.stderr
    assert res.stdout.startswith("APAGAR"), res.stdout
    assert "#271" in res.stdout
    chamadas = (tmp_path / "chamadas.log").read_text()
    assert "head=dono:feat" in chamadas and "state=all" in chamadas


def test_2_push_depois_do_merge_mantem(repo, tmp_path):
    r, cabeca = repo
    _git(r, "checkout", "-q", cabeca)
    (r / "b.txt").write_text("depois do merge\n")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "push depois do merge")
    _git(r, "update-ref", "refs/remotes/origin/feat", "HEAD")
    res = _correr(r, tmp_path, "feat", [_pr(271, cabeca)])
    assert res.returncode == 0, res.stderr
    assert res.stdout.startswith("MANTER 2 "), res.stdout


def test_3_pr_merged_para_outra_base_mantem(repo, tmp_path):
    r, cabeca = repo
    res = _correr(r, tmp_path, "feat", [_pr(5, cabeca, base="outra")])
    assert res.stdout.startswith("MANTER"), res.stdout


def test_4_pr_aberto_mantem(repo, tmp_path):
    r, cabeca = repo
    res = _correr(
        r, tmp_path, "feat", [_pr(9, cabeca, merged=False, estado="open"), _pr(8, cabeca)]
    )
    assert res.stdout.startswith("MANTER"), res.stdout
    assert "#9 aberto" in res.stdout


def test_5_sem_pr_mantem(repo, tmp_path):
    r, _ = repo
    res = _correr(r, tmp_path, "feat", [])
    assert res.returncode == 0
    assert res.stdout.startswith("MANTER 1 "), res.stdout


def test_6_pr_fechado_sem_merge_mantem(repo, tmp_path):
    r, cabeca = repo
    res = _correr(r, tmp_path, "feat", [_pr(7, cabeca, merged=False)])
    assert res.stdout.startswith("MANTER"), res.stdout


def test_7_varios_prs_so_o_ultimo_coincide_apaga(repo, tmp_path):
    """Caso real de claude/calendario-mensal-pr-279-qy99bo: #286 e #288."""
    r, cabeca = repo
    res = _correr(r, tmp_path, "feat", [_pr(288, cabeca), _pr(286, "5d2c446" + "0" * 33)])
    assert res.stdout.startswith("APAGAR"), res.stdout
    assert "#288" in res.stdout


def test_8_falha_da_api_nunca_apaga(repo, tmp_path):
    r, _ = repo
    res = _correr(r, tmp_path, "feat", falhar=True)
    assert res.returncode == 1
    assert "APAGAR" not in res.stdout
    assert "API falhou" in res.stderr


def test_9_main_nunca_e_processada(repo, tmp_path):
    r, _ = repo
    res = _correr(r, tmp_path, "main", [])
    assert res.returncode == 2
    assert "APAGAR" not in res.stdout
    assert not (tmp_path / "chamadas.log").exists()


def test_zero_commits_unicos_apaga_sem_consultar_a_api(repo, tmp_path):
    r, _ = repo
    _git(r, "update-ref", "refs/remotes/origin/integrada", "refs/remotes/origin/main")
    res = _correr(r, tmp_path, "integrada", falhar=True)
    assert res.returncode == 0
    assert res.stdout.startswith("APAGAR"), res.stdout
    assert not (tmp_path / "chamadas.log").exists()


# ── Workflow ────────────────────────────────────────────────────────────────


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def test_workflow_usa_o_script_e_pode_ler_prs():
    w = _workflow()
    assert w["permissions"].get("pull-requests") == "read"
    (job,) = w["jobs"].values()
    processar = next(p for p in job["steps"] if p.get("id") == "processar")
    assert "scripts/decidir_branch.sh" in processar["run"]
    assert "rev-list --count" not in processar["run"], "a decisão vive só no script"


def test_workflow_tem_modo_simular_que_nao_apaga_nem_mexe_na_issue():
    w = _workflow()
    gatilhos = w.get("on") or w.get(True)
    entrada = gatilhos["workflow_dispatch"]["inputs"]["simular"]
    assert entrada["type"] == "boolean" and entrada["default"] is False
    (job,) = w["jobs"].values()
    processar = next(p for p in job["steps"] if p.get("id") == "processar")
    assert processar["env"].get("SIMULAR") == "${{ inputs.simular == true }}"
    run = processar["run"]
    i_sim = run.index('if [ "$SIMULAR" = "true" ]')
    i_del = run.index("gh api -X DELETE")
    assert i_sim < i_del, "o DELETE tem de estar no ramo não-simulado"
    issue = next(p for p in job["steps"] if "Issue" in p.get("name", ""))
    assert "inputs.simular != true" in issue["if"]
