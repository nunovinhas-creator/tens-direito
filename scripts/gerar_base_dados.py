#!/usr/bin/env python3
"""
FASE 3 (sessão de dados abertos, 2026-07-19) — publica os dados abertos do
Tens Direito como uma base SQLite única (`dados/tensdireito.db`), sem
servidor (o site é estático — a base é só um ficheiro binário servido tal
e qual pelo GitHub Pages, explorável no browser via Datasette Lite em
`dados.html`).

Duas tabelas:

- `parametros` — uma linha por (prestação, parâmetro, vigência), lida
  directamente de `dados/parametros/*.yaml` (TODAS as vigências, não só a
  vigente hoje — ao contrário de `dados/parametros.json`, que só resolve
  o valor actual, esta tabela é a série temporal completa).
- `historial` — uma linha por (fonte, commit) que alguma vez tocou em
  `dados/observacoes/*.json`, derivada de `git log --name-only` já
  parseado (nunca reinventado — o `git log` é a única fonte de verdade
  do historial, ver FASE 1).

Nunca inclui nenhum campo "gerado_em"/timestamp dentro das tabelas — só
assim duas corridas sobre o mesmo estado do repositório produzem o
mesmo ficheiro `.db` byte a byte (confirmado por hash em
tests/test_gerar_base_dados.py), o que permite ao pipeline só commitar
`tensdireito.db` quando o conteúdo mudar de facto, mesmo princípio de
`registar_observacao.py` na FASE 1 (nunca ruído diário).

    python scripts/gerar_base_dados.py             # escreve dados/tensdireito.db
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PARAMETROS_DIR = RAIZ / "dados" / "parametros"
OBSERVACOES_DIR = RAIZ / "dados" / "observacoes"
DESTINO_DB = RAIZ / "dados" / "tensdireito.db"


def _ler_linhas_parametros() -> List[tuple]:
    linhas = []
    for ficheiro in sorted(PARAMETROS_DIR.glob("*.yaml")):
        prestacao = ficheiro.stem
        bruto = yaml.safe_load(ficheiro.read_text(encoding="utf-8")) or {}
        for nome_parametro, definicao in sorted(bruto.items()):
            if not isinstance(definicao, dict):
                continue
            descricao = definicao.get("descricao", "")
            unidade = definicao.get("unidade", "")
            for entrada in definicao.get("valores", []):
                linhas.append((
                    prestacao,
                    nome_parametro,
                    descricao,
                    unidade,
                    entrada.get("valor"),
                    str(entrada.get("vigencia_inicio", "")),
                    entrada.get("referencia_legal", ""),
                    entrada.get("fonte_url", ""),
                    entrada.get("fonte_url_complementar"),
                    str(entrada.get("verificado_em", "")),
                ))
    # Ordem determinística: mesmo estado de ficheiros produz sempre a
    # mesma ordem de linhas na tabela (nunca depende da ordem de leitura
    # do glob entre sistemas de ficheiros diferentes).
    linhas.sort(key=lambda linha: (linha[0], linha[1], linha[5]))
    return linhas


def _git_log_observacoes(raiz: Path) -> List[tuple]:
    """Deriva o historial de `git log --name-only` sobre dados/observacoes/
    — parseado, nunca reinventado (a mesma garantia já dada por
    scripts/registar_observacao.py: um commit por fonte alterada). Numa
    checkout sem histórico git (ex.: tarball, não um clone) devolve lista
    vazia em vez de falhar — a tabela historial fica simplesmente vazia,
    nunca inventa dados."""
    # \x1e/\x1f (record/unit separator ASCII) — nunca \x00: argv não aceita
    # NUL embutido (ValueError do próprio subprocess), ao contrário de
    # outros caracteres de controlo.
    separador = "\x1e"
    campo = "\x1f"
    cmd = [
        "git", "log", f"--format={separador}%H{campo}%aI{campo}%s",
        "--name-only", "--", "dados/observacoes/",
    ]
    try:
        resultado = subprocess.run(
            cmd, cwd=raiz, capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    linhas = []
    for bloco in resultado.stdout.split(separador):
        bloco = bloco.strip("\n")
        if not bloco:
            continue
        partes = bloco.split("\n")
        cabecalho = partes[0]
        ficheiros = partes[1:]
        try:
            sha, data_iso, mensagem = cabecalho.split(campo, 2)
        except ValueError:
            continue
        for f in ficheiros:
            f = f.strip()
            if not f.startswith("dados/observacoes/") or not f.endswith(".json"):
                continue
            if f.endswith("schema.json"):
                continue
            slug = Path(f).stem
            linhas.append((slug, sha, data_iso, mensagem))

    # git log já devolve por ordem cronológica decrescente — mantida tal
    # e qual (é a ordem "historial" natural: mais recente primeiro).
    return linhas


def gerar(destino: Path = DESTINO_DB) -> dict:
    linhas_parametros = _ler_linhas_parametros()
    linhas_historial = _git_log_observacoes(RAIZ)

    if destino.exists():
        destino.unlink()
    destino.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(destino)
    try:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE parametros (
                prestacao              TEXT NOT NULL,
                parametro              TEXT NOT NULL,
                descricao              TEXT,
                unidade                TEXT,
                valor                  REAL,
                vigencia_inicio        TEXT NOT NULL,
                referencia_legal       TEXT,
                fonte_url              TEXT,
                fonte_url_complementar TEXT,
                verificado_em          TEXT
            )
            """
        )
        cur.executemany(
            "INSERT INTO parametros VALUES (?,?,?,?,?,?,?,?,?,?)", linhas_parametros
        )

        cur.execute(
            """
            CREATE TABLE historial (
                fonte        TEXT NOT NULL,
                commit_sha   TEXT NOT NULL,
                data_commit  TEXT NOT NULL,
                mensagem     TEXT
            )
            """
        )
        cur.executemany(
            "INSERT INTO historial VALUES (?,?,?,?)", linhas_historial
        )
        con.commit()
    finally:
        con.close()

    return {"parametros": len(linhas_parametros), "historial": len(linhas_historial)}


def main() -> int:
    contagens = gerar()
    print(
        f"{DESTINO_DB.relative_to(RAIZ)} escrito: "
        f"{contagens['parametros']} linha(s) em parametros, "
        f"{contagens['historial']} linha(s) em historial."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
