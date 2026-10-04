"""
.github/workflows/canario-urls.yml — canário diário de URLs oficiais.

Estrutura (fora do push a main, fora do integridade.yml) e o JavaScript real
do step que gere a issue única `canario-urls`, corrido em Node com um
`github` falso (mesmo padrão de tests/test_canal_aviso_pagamento.py):
- falha sem issue aberta → cria, atribuída ao Nuno, com @menção;
- falha com o mesmo conjunto de URLs → só actualiza o corpo, sem comentário;
- falha com outro conjunto → actualiza e comenta com @menção;
- corrida verde com issue aberta → comenta e fecha;
- script rebentado sem relatório → nunca fecha, regista a falha.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
WF = yaml.safe_load((RAIZ / ".github" / "workflows" / "canario-urls.yml").read_text(encoding="utf-8"))
INTEGRIDADE = yaml.safe_load((RAIZ / ".github" / "workflows" / "integridade.yml").read_text(encoding="utf-8"))
TITULO = "🔗 Canário de URLs oficiais a falhar"


def test_corre_diariamente_e_a_pedido_nunca_em_push():
    gatilhos = WF[True]  # PyYAML lê `on` como True
    assert set(gatilhos) == {"schedule", "workflow_dispatch"}
    assert WF["permissions"] == {"contents": "read", "issues": "write"}


def test_saiu_do_integridade():
    assert not any("canario" in nome for nome in INTEGRIDADE["jobs"])


def test_job_fica_vermelho_quando_o_canario_falha():
    passos = WF["jobs"]["canario"]["steps"]
    canario = next(p for p in passos if p.get("id") == "canario")
    assert canario["continue-on-error"] is True
    assert "--relatorio /tmp/canario.json" in canario["run"]
    final = passos[-1]
    assert final["if"] == "steps.canario.outcome != 'success'"
    assert "exit 1" in final["run"]


def _script():
    passos = WF["jobs"]["canario"]["steps"]
    return next(p for p in passos if p.get("name", "").startswith("Abrir, actualizar ou fechar"))["with"]["script"]


def _correr(tmp_path, *, desfecho, relatorio, abertas=()):
    if shutil.which("node") is None:
        pytest.skip("node não disponível")
    script = _script()
    assert "'/tmp/canario.json'" in script and "'${{ steps.canario.outcome }}'" in script
    caminho = tmp_path / "canario.json"
    if relatorio is not None:
        caminho.write_text(json.dumps(relatorio, ensure_ascii=False), encoding="utf-8")
    script = script.replace("'/tmp/canario.json'", json.dumps(str(caminho)))
    script = script.replace("'${{ steps.canario.outcome }}'", json.dumps(desfecho))
    harness = (
        "const chamadas = [];\n"
        f"const abertas = {json.dumps(list(abertas), ensure_ascii=False)};\n"
        "const reg = (tipo) => async (a) => { chamadas.push([tipo, a]); return {data: {}}; };\n"
        "const github = {rest: {issues: {\n"
        "  listForRepo: async () => ({data: abertas}),\n"
        "  create: reg('create'), update: reg('update'), createComment: reg('comment'),\n"
        "}}};\n"
        "const context = {repo: {owner: 'o', repo: 'r'}, serverUrl: 'https://github.com', runId: 7};\n"
        "(async () => {\n" + script + "\n})().then(() => {\n"
        "  process.stdout.write('\\n@@' + JSON.stringify(chamadas));\n"
        "});\n"
    )
    res = subprocess.run(["node", "-e", harness], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.split("@@")[-1])


def _relatorio(falhas):
    return {"falhas": falhas, "corpo": "@nunovinhas-creator — tabela" if falhas else "", "resultados": []}


def _issue(falhas):
    return {"number": 5, "title": TITULO, "body": f"tabela\n\n<!-- falhas: {' '.join(falhas)} -->"}


def test_falha_sem_issue_cria_uma_atribuida_ao_nuno(tmp_path):
    [(tipo, a)] = _correr(tmp_path, desfecho="failure", relatorio=_relatorio(["https://www.sns24.gov.pt"]))
    assert tipo == "create"
    assert a["title"] == TITULO
    assert a["assignees"] == ["nunovinhas-creator"]
    assert a["labels"] == ["canario-urls", "verificar"]
    assert a["body"].startswith("@nunovinhas-creator")
    assert "<!-- falhas: https://www.sns24.gov.pt -->" in a["body"]


def test_falha_com_o_mesmo_conjunto_so_actualiza_o_corpo(tmp_path):
    falhas = ["https://www.sns24.gov.pt"]
    chamadas = _correr(tmp_path, desfecho="failure", relatorio=_relatorio(falhas), abertas=[_issue(falhas)])
    assert [t for t, _ in chamadas] == ["update"]


def test_falha_com_outro_conjunto_actualiza_e_comenta_com_mencao(tmp_path):
    chamadas = _correr(tmp_path, desfecho="failure",
                       relatorio=_relatorio(["https://www.autenticacao.gov.pt"]),
                       abertas=[_issue(["https://www.sns24.gov.pt"])])
    assert [t for t, _ in chamadas] == ["update", "comment"]
    assert chamadas[1][1]["body"].startswith("@nunovinhas-creator")
    assert "https://www.autenticacao.gov.pt" in chamadas[1][1]["body"]


def test_corrida_verde_fecha_a_issue_aberta(tmp_path):
    chamadas = _correr(tmp_path, desfecho="success", relatorio=_relatorio([]),
                       abertas=[_issue(["https://www.sns24.gov.pt"])])
    assert [t for t, _ in chamadas] == ["comment", "update"]
    assert chamadas[1][1]["state"] == "closed"


def test_corrida_verde_sem_issue_nao_faz_nada(tmp_path):
    assert _correr(tmp_path, desfecho="success", relatorio=_relatorio([])) == []


def test_script_rebentado_sem_relatorio_nunca_fecha_e_regista(tmp_path):
    chamadas = _correr(tmp_path, desfecho="failure", relatorio=None,
                       abertas=[_issue(["https://www.sns24.gov.pt"])])
    assert "update" in [t for t, _ in chamadas]
    assert not any(t == "update" and a.get("state") == "closed" for t, a in chamadas)
    assert "sem relatório" in chamadas[0][1]["body"]
