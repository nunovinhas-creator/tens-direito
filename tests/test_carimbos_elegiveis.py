"""
Testes para run_shadow_daily.calcular_carimbos_elegiveis -- simulação
diária (Fase 4) de quais páginas SERIAM elegíveis para revalidação de
carimbo se decisao_datas.REVALIDACAO_CARIMBO_HABILITADA estivesse
ligada. Nunca aplica nada, nunca liga a flag -- só reporta.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_shadow_daily import calcular_carimbos_elegiveis

_HOJE = "2026-07-02"
_ONTEM = "2026-07-01"


def _escrever_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _preparar_repo(
    tmp_path,
    *,
    pagina_fonte: dict,
    estado_fontes: dict,
    hashes: dict,
):
    """`hashes` é `{slug: {"hoje": hash_ou_None, "ontem": hash_ou_None}}`."""
    _escrever_json(tmp_path / "data" / "pagina_fonte.json", pagina_fonte)
    _escrever_json(tmp_path / "data" / "estado_fontes.json", estado_fontes)
    for slug, dias in hashes.items():
        if dias.get("hoje") is not None:
            _escrever_json(
                tmp_path / "data" / "scraped" / f"{slug}_{_HOJE}.json",
                {"hash_conteudo": dias["hoje"]},
            )
        if dias.get("ontem") is not None:
            _escrever_json(
                tmp_path / "data" / "scraped" / f"{slug}_{_ONTEM}.json",
                {"hash_conteudo": dias["ontem"]},
            )
    return tmp_path


def test_elegivel_com_fonte_ok_e_hash_igual(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"rsi.html": ["seg_social_rsi"]},
        estado_fontes={"seg_social_rsi": {"estado": "OK"}},
        hashes={"seg_social_rsi": {"hoje": "abc", "ontem": "abc"}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == ["rsi.html"]


def test_nao_elegivel_com_hash_diferente(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"rsi.html": ["seg_social_rsi"]},
        estado_fontes={"seg_social_rsi": {"estado": "OK"}},
        hashes={"seg_social_rsi": {"hoje": "abc", "ontem": "xyz"}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_ok_via_arquivo_nunca_elegivel(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"manuais-escolares-mega.html": ["mega_datas"]},
        estado_fontes={"mega_datas": {"estado": "OK_VIA_ARQUIVO"}},
        hashes={"mega_datas": {"hoje": "abc", "ontem": "abc"}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_bloqueado_nunca_elegivel(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"subsidio-desemprego.html": ["iefp_desemprego"]},
        estado_fontes={"iefp_desemprego": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 3}},
        hashes={"iefp_desemprego": {"hoje": "abc", "ontem": "abc"}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_pagina_com_multiplas_fontes_precisa_de_todas_ok_e_estaveis(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"manuais-escolares-mega.html": ["dge_manuais", "mega_datas"]},
        estado_fontes={
            "dge_manuais": {"estado": "OK"},
            "mega_datas": {"estado": "OK"},
        },
        hashes={
            "dge_manuais": {"hoje": "abc", "ontem": "abc"},
            "mega_datas": {"hoje": "def", "ontem": "different"},  # mudou
        },
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_pagina_sem_scrape_de_ontem_nao_e_elegivel(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"rsi.html": ["seg_social_rsi"]},
        estado_fontes={"seg_social_rsi": {"estado": "OK"}},
        hashes={"seg_social_rsi": {"hoje": "abc", "ontem": None}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_pagina_sem_mapeamento_nunca_e_elegivel(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={},
        estado_fontes={"seg_social_rsi": {"estado": "OK"}},
        hashes={"seg_social_rsi": {"hoje": "abc", "ontem": "abc"}},
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_sem_ficheiros_nao_crasha(tmp_path):
    (tmp_path / "data").mkdir()
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == []


def test_resultado_ordenado_alfabeticamente(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={
            "rsi.html": ["seg_social_rsi"],
            "abono-de-familia.html": ["seg_social_abono"],
        },
        estado_fontes={
            "seg_social_rsi": {"estado": "OK"},
            "seg_social_abono": {"estado": "OK"},
        },
        hashes={
            "seg_social_rsi": {"hoje": "a", "ontem": "a"},
            "seg_social_abono": {"hoje": "b", "ontem": "b"},
        },
    )
    assert calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM) == [
        "abono-de-familia.html",
        "rsi.html",
    ]


def test_nunca_escreve_nada(tmp_path):
    _preparar_repo(
        tmp_path,
        pagina_fonte={"rsi.html": ["seg_social_rsi"]},
        estado_fontes={"seg_social_rsi": {"estado": "OK"}},
        hashes={"seg_social_rsi": {"hoje": "abc", "ontem": "abc"}},
    )
    antes = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    calcular_carimbos_elegiveis(tmp_path, hoje=_HOJE, ontem=_ONTEM)
    depois = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    assert antes == depois
