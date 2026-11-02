"""
Issue #367 (2026-11-02): dge.mec.pt ficou inacessível a partir de 23/10
(timeout / ligação recusada). `scrape_playwright()` e `scrape_http()`
devolviam None sem registar nada em data/bloqueios.json — por isso
gerir_estado_fontes.py marcava `dge_manuais` e `mega_datas` como OK, com
`ultima_ok` de hoje, sem um único ficheiro diário desde 22/10. Uma falha
de rede em todas as tentativas é cegueira e conta para a mesma máquina de
estados (3 dias consecutivos → issue fonte-bloqueada).

Isolado em tmp_path — nunca toca em data/bloqueios.json real.
"""
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402
from gerir_estado_fontes import SLUGS_MONITORIZADOS, calcular_novo_estado  # noqa: E402


def _isolar(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, "SCRAPED_DIR", tmp_path)
    monkeypatch.setattr(sp, "AVISOS_LOG", tmp_path / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", tmp_path / "bloqueios.json")


def _fonte(slug):
    return next(f for f in sp.FONTES_PLAYWRIGHT if f["slug"] == slug)


def test_playwright_falha_de_rede_regista_bloqueio(tmp_path, monkeypatch):
    _isolar(tmp_path, monkeypatch)
    monkeypatch.setattr(sp, "_obter_html", lambda *a, **k: None)

    fonte = _fonte("seg_social_abono")
    assert sp.scrape_playwright(page=None, fonte=fonte) is None

    bloqueios = json.loads((tmp_path / "bloqueios.json").read_text(encoding="utf-8"))
    assert [b["slug"] for b in bloqueios] == ["seg_social_abono"]
    assert bloqueios[0]["url"] == fonte["url"]
    assert bloqueios[0]["motivos"] == ["falha de rede em todas as tentativas"]
    assert not list(tmp_path.glob("seg_social_abono_*.json"))


def test_http_falha_de_rede_regista_bloqueio(tmp_path, monkeypatch):
    _isolar(tmp_path, monkeypatch)

    def _sem_rede(*a, **k):
        raise requests.ConnectionError("ligação recusada")

    monkeypatch.setattr(sp.requests, "get", _sem_rede)
    monkeypatch.setattr(sp.time, "sleep", lambda s: None)

    assert sp.scrape_http(_fonte("iefp_desemprego")) is None

    bloqueios = json.loads((tmp_path / "bloqueios.json").read_text(encoding="utf-8"))
    assert [b["slug"] for b in bloqueios] == ["iefp_desemprego"]
    assert bloqueios[0]["motivos"] == ["falha de rede em todas as tentativas"]


def test_falha_de_rede_conta_para_a_maquina_de_estados():
    """Com a entrada em bloqueios.json, a fonte deixa de ficar OK: o
    contador sobe e, ao 3.º dia, é elegível para issue."""
    anterior = {"igefe_mega": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 2,
                               "ultima_ok": "2026-10-22"}}
    novo = calcular_novo_estado(anterior, ["igefe_mega"], SLUGS_MONITORIZADOS, hoje="2026-11-02")
    assert novo["igefe_mega"] == {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 3,
                                   "ultima_ok": "2026-10-22"}


def test_fontes_dge_retiradas():
    """dge.mec.pt deixou de responder (issue #367): nenhuma fonte vigiada
    nem monitorizada aponta para lá."""
    assert not [f["slug"] for f in sp.FONTES_PLAYWRIGHT if "dge.mec.pt" in f["url"]]
    for slug in ("dge_ase", "dge_manuais", "mega_datas"):
        assert slug not in SLUGS_MONITORIZADOS
