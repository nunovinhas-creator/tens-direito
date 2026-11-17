"""
tests/test_og_images_arquivo_ano.py

Issue #391: `scripts/gerar_og_images.py` tratava noticias-AAAA.html (arquivo
de notícias por ano, gerado pelo pipeline) como página com imagem própria —
renderizava assets/img/og/noticias-AAAA.jpg, punha-a no manifest e reescrevia
a og:image que o gerar_noticias.py escreve (a de noticias.html).

Corre o script real com --write sobre uma cópia temporária do repositório,
com uma página sintética noticias-2027.html (anos futuros, não só 2026), e
exige que nada do arquivo por ano mude — mas que noticias.html continue a
ter a sua imagem própria.
"""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from gerar_og_images import DOMINIO, encontrar_paginas  # noqa: E402

_IGNORAR = shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "node_modules")


def _hash(caminho: Path) -> str | None:
    return hashlib.sha256(caminho.read_bytes()).hexdigest() if caminho.exists() else None


def _imagens_arquivo(dir_og: Path) -> list[str]:
    return sorted(f.name for f in dir_og.glob("noticias-*.jpg"))


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    copia = tmp_path_factory.mktemp("repo") / "tens-direito"
    shutil.copytree(RAIZ, copia, ignore=_IGNORAR)

    origem = copia / "noticias-2026.html"
    assert origem.exists(), "noticias-2026.html em falta no repositório"
    sintetica = copia / "noticias-2027.html"
    sintetica.write_text(
        origem.read_text(encoding="utf-8").replace("Notícias de 2026", "Notícias de 2027"),
        encoding="utf-8",
    )

    dir_og = copia / "assets" / "img" / "og"
    manifest = dir_og / "manifest.json"
    antes = {
        "2026": _hash(origem),
        "2027": _hash(sintetica),
        "manifest": _hash(manifest),
        "imagens": _imagens_arquivo(dir_og),
    }
    r = subprocess.run(
        [sys.executable, str(copia / "scripts" / "gerar_og_images.py"), "--write"],
        capture_output=True, text=True, timeout=600,
    )
    depois = {
        "2026": _hash(origem),
        "2027": _hash(sintetica),
        "manifest": _hash(manifest),
        "imagens": _imagens_arquivo(dir_og),
    }
    return {"copia": copia, "antes": antes, "depois": depois, "saida": r.stdout + r.stderr,
            "codigo": r.returncode}


def test_write_nao_toca_no_arquivo_de_2026_nem_no_manifest(corrida):
    a, d, saida = corrida["antes"], corrida["depois"], corrida["saida"]
    assert d["2026"] == a["2026"], f"noticias-2026.html foi alterado:\n{saida}"
    assert d["manifest"] == a["manifest"], f"manifest.json foi alterado:\n{saida}"
    assert d["imagens"] == a["imagens"] == [], f"imagens do arquivo por ano: {d['imagens']}\n{saida}"
    assert corrida["codigo"] == 0, saida


def test_write_nao_toca_num_ano_futuro(corrida):
    a, d, saida = corrida["antes"], corrida["depois"], corrida["saida"]
    assert d["2027"] == a["2027"], f"noticias-2027.html foi alterado:\n{saida}"
    assert "noticias-2027.jpg" not in d["imagens"], saida
    manifest = json.loads((corrida["copia"] / "assets/img/og/manifest.json").read_text(encoding="utf-8"))
    assert "noticias-2027" not in manifest, saida
    assert "noticias-2027.html" not in saida, f"o script listou o ano futuro:\n{saida}"


def test_noticias_html_continua_com_imagem_propria(corrida):
    copia = corrida["copia"]
    manifest = json.loads((copia / "assets/img/og/manifest.json").read_text(encoding="utf-8"))
    assert manifest.get("noticias", {}).get("pagina") == "noticias.html", corrida["saida"]
    assert (copia / "assets/img/og/noticias.jpg").exists(), corrida["saida"]
    texto = (copia / "noticias.html").read_text(encoding="utf-8")
    assert f'<meta property="og:image" content="{DOMINIO}/assets/img/og/noticias.jpg">' in texto


def test_exclusao_so_apanha_o_arquivo_por_ano():
    nomes = {p.name for p in encontrar_paginas()}
    assert "noticias.html" in nomes
    assert not any(n.startswith("noticias-") for n in nomes), sorted(nomes)
