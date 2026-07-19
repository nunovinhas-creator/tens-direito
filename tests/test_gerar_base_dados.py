"""FASE 3 (sessão de dados abertos, 2026-07-19) — scripts/gerar_base_dados.py.

Cobre: determinismo (duas corridas sobre o mesmo estado = ficheiro .db
byte-idêntico, condição necessária para o pipeline só commitar quando o
conteúdo mudar de facto — mesmo princípio de test_registar_observacao),
schema das duas tabelas, contagem de linhas de `parametros` a bater com
`dados/parametros/*.yaml` real, e o parser de `git log --name-only`
isolado num repositório git temporário (nunca contra o histórico real do
próprio projecto — determinístico, sem depender de quantos commits
`dados/observacoes/` já tem neste checkout).
"""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest
import yaml

import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_base_dados  # noqa: E402


def test_gerar_e_deterministico(tmp_path):
    destino1 = tmp_path / "a.db"
    destino2 = tmp_path / "b.db"
    gerar_base_dados.gerar(destino1)
    gerar_base_dados.gerar(destino2)
    assert destino1.read_bytes() == destino2.read_bytes()


def test_schema_tem_as_duas_tabelas(tmp_path):
    destino = tmp_path / "t.db"
    gerar_base_dados.gerar(destino)
    con = sqlite3.connect(destino)
    try:
        nomes = {
            linha[0]
            for linha in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {"parametros", "historial"} <= nomes
        colunas_parametros = {c[1] for c in con.execute("PRAGMA table_info(parametros)")}
        assert colunas_parametros == {
            "prestacao", "parametro", "descricao", "unidade", "valor",
            "vigencia_inicio", "referencia_legal", "fonte_url",
            "fonte_url_complementar", "verificado_em",
        }
        colunas_historial = {c[1] for c in con.execute("PRAGMA table_info(historial)")}
        assert colunas_historial == {"fonte", "commit_sha", "data_commit", "mensagem"}
    finally:
        con.close()


def test_contagem_de_parametros_bate_com_os_yaml_reais(tmp_path):
    destino = tmp_path / "t.db"
    contagens = gerar_base_dados.gerar(destino)

    total_esperado = 0
    for ficheiro in gerar_base_dados.PARAMETROS_DIR.glob("*.yaml"):
        bruto = yaml.safe_load(ficheiro.read_text(encoding="utf-8")) or {}
        for definicao in bruto.values():
            total_esperado += len(definicao.get("valores", []))

    assert contagens["parametros"] == total_esperado
    con = sqlite3.connect(destino)
    try:
        (n,) = con.execute("SELECT COUNT(*) FROM parametros").fetchone()
        assert n == total_esperado
    finally:
        con.close()


def test_csi_valor_referencia_individual_esta_na_tabela(tmp_path):
    destino = tmp_path / "t.db"
    gerar_base_dados.gerar(destino)
    con = sqlite3.connect(destino)
    try:
        linha = con.execute(
            "SELECT valor, referencia_legal, fonte_url, verificado_em "
            "FROM parametros WHERE prestacao='csi' AND parametro='valor_referencia_individual_anual'"
        ).fetchone()
    finally:
        con.close()
    assert linha is not None, "csi.valor_referencia_individual_anual em falta na tabela"
    valor, referencia_legal, fonte_url, verificado_em = linha
    assert valor == 8040
    assert referencia_legal
    assert fonte_url
    assert verificado_em


# ── Parser de git log — isolado num repositório git temporário ─────────────
def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def repo_git_temporario(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "teste@example.com")
    _git(tmp_path, "config", "user.name", "Teste")

    obs_dir = tmp_path / "dados" / "observacoes"
    obs_dir.mkdir(parents=True)

    (obs_dir / "fonte_a.json").write_text('{"fonte": "fonte_a"}\n', encoding="utf-8")
    _git(tmp_path, "add", "dados/observacoes/fonte_a.json")
    _git(tmp_path, "commit", "-q", "-m", "dados: atualização fonte_a 2026-07-19")

    (obs_dir / "fonte_b.json").write_text('{"fonte": "fonte_b"}\n', encoding="utf-8")
    _git(tmp_path, "add", "dados/observacoes/fonte_b.json")
    _git(tmp_path, "commit", "-q", "-m", "dados: atualização fonte_b 2026-07-19")

    (obs_dir / "fonte_a.json").write_text('{"fonte": "fonte_a", "sha256_conteudo": "novo"}\n', encoding="utf-8")
    _git(tmp_path, "add", "dados/observacoes/fonte_a.json")
    _git(tmp_path, "commit", "-q", "-m", "dados: atualização fonte_a 2026-07-20")

    return tmp_path


def test_git_log_observacoes_parseia_um_commit_por_fonte_alterada(repo_git_temporario):
    linhas = gerar_base_dados._git_log_observacoes(repo_git_temporario)
    assert len(linhas) == 3

    por_fonte = {}
    for fonte, sha, data_commit, mensagem in linhas:
        por_fonte.setdefault(fonte, []).append((sha, data_commit, mensagem))

    assert len(por_fonte["fonte_a"]) == 2  # 2 commits tocaram em fonte_a.json
    assert len(por_fonte["fonte_b"]) == 1
    for _, _sha, data_commit, mensagem in linhas:
        assert data_commit  # ISO 8601, nunca vazio
        assert mensagem.startswith("dados: atualização")


def test_git_log_observacoes_nunca_inclui_o_schema(repo_git_temporario):
    schema = repo_git_temporario / "dados" / "observacoes" / "schema.json"
    schema.write_text("{}\n", encoding="utf-8")
    _git(repo_git_temporario, "add", "dados/observacoes/schema.json")
    _git(repo_git_temporario, "commit", "-q", "-m", "dados: schema")

    linhas = gerar_base_dados._git_log_observacoes(repo_git_temporario)
    fontes = {fonte for fonte, *_ in linhas}
    assert "schema" not in fontes


def test_git_log_observacoes_sem_git_devolve_lista_vazia(tmp_path):
    """Nunca falha nem inventa historial numa checkout sem git (ex.:
    tarball) — devolve lista vazia."""
    linhas = gerar_base_dados._git_log_observacoes(tmp_path)
    assert linhas == []
