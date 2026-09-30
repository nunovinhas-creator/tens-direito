"""
.github/workflows/integridade.yml — gatilho de PR (issue #266).

Sem `types:`, o `pull_request` só dispara em opened/synchronize/reopened: um PR
cuja base passa a main (edited) ou que sai de rascunho (ready_for_review) ficava
sem nenhum check (caso real: #262). E o `edited` nunca pode ser filtrado por
job: um job saltado cria um check `skipped`, que conta como passado num check
obrigatório e, pelo concurrency, cancelaria o run real em curso.
"""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
WORKFLOW = yaml.safe_load((RAIZ / ".github/workflows/integridade.yml").read_text(encoding="utf-8"))
# PyYAML (YAML 1.1) lê a chave `on` como o booleano True.
GATILHOS = WORKFLOW[True]


def test_pull_request_cobre_mudanca_de_base_e_saida_de_rascunho():
    pr = GATILHOS["pull_request"]
    assert pr["branches"] == ["main"]
    assert set(pr["types"]) == {"opened", "synchronize", "reopened", "ready_for_review", "edited"}


def test_push_continua_restrito_a_main():
    assert GATILHOS["push"]["branches"] == ["main"]


def test_nenhum_job_filtra_pela_accao_do_evento():
    for nome, job in WORKFLOW["jobs"].items():
        condicao = str(job.get("if", ""))
        assert "event.action" not in condicao and "event.changes" not in condicao, nome
