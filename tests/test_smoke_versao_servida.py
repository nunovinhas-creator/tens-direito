"""
Smoke de produção confirma a versão servida (issue #281).

Antes, `scripts/smoke_producao.sh` só verificava 200, "Verificado a" nos
simuladores e JSON válido — um site ainda na versão anterior passava. Foi o
que aconteceu a 2026-10-01 (calendario-mensal.yml, run 36857076880): o deploy
do commit anterior já tinha terminado e o smoke deu verde contra ele.

Estes testes correm o script real contra um servidor HTTP local e um
repositório git temporário: cada HTML publicado que o commit vigiado alterou
(ou a homepage, se não alterou nenhum) tem de ser servido como está nesse
commit ou num commit mais novo; pedidos com ?v=<sha>. Mais uma guarda
estática sobre os workflows: smoke no fim do job, com SHA_DEPLOY, sem nada
que engula a falha.
"""
from __future__ import annotations

import http.server
import os
import subprocess
import threading
from functools import partial
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).parent.parent
SCRIPT = RAIZ / "scripts" / "smoke_producao.sh"
WORKFLOWS = RAIZ / ".github" / "workflows"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(repo: Path, ficheiros: dict[str, str | None], msg: str) -> str:
    for nome, conteudo in ficheiros.items():
        caminho = repo / nome
        if conteudo is None:
            caminho.unlink()
            continue
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(conteudo, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    _commit(r, {"index.html": "<p>v0</p>\n", "p/guia.html": "<p>guia v0</p>\n"}, "base")
    return r


class _Servidor:
    """Serve o directório `site/`; regista os caminhos pedidos (com query)."""

    def __init__(self, raiz: Path):
        self.raiz = raiz
        self.pedidos: list[str] = []
        servidor = self

        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):  # noqa: N802
                servidor.pedidos.append(self.path)
                super().do_GET()

            def log_message(self, *a):
                pass

        self.httpd = http.server.ThreadingHTTPServer(
            ("127.0.0.1", 0), partial(Handler, directory=str(raiz))
        )
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def servir(self, ficheiros: dict[str, str]):
        for nome, conteudo in ficheiros.items():
            caminho = self.raiz / nome
            caminho.parent.mkdir(parents=True, exist_ok=True)
            caminho.write_text(conteudo, encoding="utf-8")


@pytest.fixture
def site(tmp_path):
    raiz = tmp_path / "site"
    raiz.mkdir()
    s = _Servidor(raiz)
    yield s
    s.httpd.shutdown()


def _correr(repo: Path, site: _Servidor, tmp_path: Path, extra: dict[str, str]):
    lista = tmp_path / "urls.txt"
    lista.write_text("/\n", encoding="utf-8")
    env = {
        k: v for k, v in os.environ.items() if k not in ("GITHUB_SHA", "SHA_DEPLOY")
    }
    env.update(
        {
            "DOMINIO": site.url,
            "LISTA_URLS": str(lista),
            "TENTATIVAS": "1",
            "ESPERA_S": "0",
            "TENTATIVAS_VERSAO": "2",
            "ESPERA_VERSAO_S": "0",
            "REF_TOPO": "HEAD",
        }
    )
    env.update(extra)
    return subprocess.run(
        ["bash", str(SCRIPT)], cwd=repo, env=env, capture_output=True, text=True, timeout=60
    )


def test_incidente_deploy_do_commit_anterior_ja_concluido_falha(repo, site, tmp_path):
    """Caso de 2026-10-01: o site serve o commit anterior, tudo responde 200."""
    sha = _commit(repo, {"index.html": "<p>v1</p>\n"}, "push do workflow")
    site.servir({"index.html": "<p>v0</p>\n", "p/guia.html": "<p>guia v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 1, res.stdout + res.stderr
    assert "não serve a versão" in res.stdout


def test_versao_publicada_servida_passa(repo, site, tmp_path):
    sha = _commit(repo, {"index.html": "<p>v1</p>\n"}, "push")
    site.servir({"index.html": "<p>v1</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr


def test_compara_todos_os_html_alterados_e_nao_so_a_homepage(repo, site, tmp_path):
    sha = _commit(
        repo, {"index.html": "<p>v1</p>\n", "p/guia.html": "<p>guia v1</p>\n"}, "push"
    )
    site.servir({"index.html": "<p>v1</p>\n", "p/guia.html": "<p>guia v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 1
    assert "/p/guia.html não serve" in res.stdout
    assert "/index.html não serve" not in res.stdout


def test_push_sem_html_compara_a_homepage(repo, site, tmp_path):
    sha = _commit(repo, {"shadow/relatorio.md": "x\n"}, "push sem html")
    site.servir({"index.html": "<p>v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr
    assert "a comparar a homepage" in res.stdout

    site.servir({"index.html": "<p>outra coisa</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 1


def test_html_fora_das_paginas_do_site_nao_conta(repo, site, tmp_path):
    sha = _commit(repo, {"tests/fixtures/x.html": "<p>fixture</p>\n"}, "fixture")
    site.servir({"index.html": "<p>v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr
    assert "a comparar a homepage" in res.stdout


def test_versao_mais_nova_de_main_e_aceite(repo, site, tmp_path):
    sha = _commit(repo, {"index.html": "<p>v1</p>\n"}, "push vigiado")
    _commit(repo, {"index.html": "<p>v2</p>\n"}, "push seguinte")
    site.servir({"index.html": "<p>v2</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr


def test_ficheiro_apagado_no_commit_nao_e_pedido(repo, site, tmp_path):
    sha = _commit(repo, {"p/guia.html": None, "index.html": "<p>v1</p>\n"}, "apaga")
    site.servir({"index.html": "<p>v1</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr


def test_pedidos_levam_parametro_anti_cache_com_o_sha(repo, site, tmp_path):
    sha = _commit(repo, {"p/guia.html": "<p>guia v1</p>\n"}, "push")
    site.servir({"index.html": "<p>v0</p>\n", "p/guia.html": "<p>guia v1</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 0, res.stdout + res.stderr
    assert f"/p/guia.html?v={sha}" in site.pedidos


def test_sha_deploy_vazio_falha(repo, site, tmp_path):
    site.servir({"index.html": "<p>v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"SHA_DEPLOY": ""})
    assert res.returncode == 1
    assert "SHA_DEPLOY definido mas vazio" in res.stdout + res.stderr


def test_sem_sha_deploy_usa_github_sha(repo, site, tmp_path):
    sha = _commit(repo, {"index.html": "<p>v1</p>\n"}, "push")
    site.servir({"index.html": "<p>v0</p>\n"})
    res = _correr(repo, site, tmp_path, {"GITHUB_SHA": sha})
    assert res.returncode == 1


def test_commit_pai_ausente_falha(tmp_path, site):
    r = tmp_path / "raso"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    sha = _commit(r, {"index.html": "<p>v0</p>\n"}, "único")
    site.servir({"index.html": "<p>v0</p>\n"})
    res = _correr(r, site, tmp_path, {"SHA_DEPLOY": sha})
    assert res.returncode == 1
    assert "commit-pai" in res.stdout


# ── Guarda estática sobre os workflows ─────────────────────────────────────


def _passos(nome: str) -> list[dict]:
    dados = yaml.safe_load((WORKFLOWS / nome).read_text(encoding="utf-8"))
    (job,) = dados["jobs"].values()
    return job["steps"]


def _i(passos, texto):
    return next(i for i, p in enumerate(passos) if texto in str(p.get("run", "")))


@pytest.mark.parametrize("nome", ["pipeline-diario.yml", "calendario-mensal.yml"])
def test_smoke_e_o_ultimo_passo_e_corre_mesmo_depois_de_um_passo_de_issue_falhar(nome):
    passos = _passos(nome)
    i_smoke = _i(passos, "smoke_producao.sh")
    i_deploy = _i(passos, "garantir_deploy_pages.sh")
    assert i_smoke == len(passos) - 1, f"{nome}: o smoke tem de ser o último passo"
    assert i_deploy == i_smoke - 1, f"{nome}: o garantir_deploy vem logo antes do smoke"
    for i in (i_deploy, i_smoke):
        cond = passos[i].get("if", "")
        assert "!cancelled()" in cond and "steps.commit_push.outputs.pushed == 'true'" in cond


@pytest.mark.parametrize(
    "nome", ["pipeline-diario.yml", "calendario-mensal.yml", "shadow-daily.yml"]
)
def test_smoke_recebe_o_sha_do_push_e_a_falha_nao_e_engolida(nome):
    passos = _passos(nome)
    smoke = passos[_i(passos, "smoke_producao.sh")]
    assert smoke.get("env", {}).get("SHA_DEPLOY") == "${{ steps.commit_push.outputs.sha }}"
    assert not smoke.get("continue-on-error")
    assert "|| true" not in smoke["run"]


@pytest.mark.parametrize(
    "nome",
    ["pipeline-diario.yml", "calendario-mensal.yml", "shadow-daily.yml", "smoke-producao.yml"],
)
def test_checkout_traz_o_commit_pai(nome):
    checkout = next(p for p in _passos(nome) if "actions/checkout" in str(p.get("uses", "")))
    profundidade = (checkout.get("with") or {}).get("fetch-depth")
    assert profundidade is not None and (profundidade == 0 or profundidade >= 2), (
        f"{nome}: o smoke precisa do commit-pai para saber que ficheiros o push alterou"
    )
