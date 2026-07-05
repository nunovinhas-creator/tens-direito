"""
Testes para o achado de 2026-07-05 (auditoria de infraestrutura):
"conteúdo suspeito" (status "ok", sem sinal de bloqueio, mas conteúdo
extraído insuficiente — caso real: dre_psu, 0 chars desde a criação da
fonte) tem de contar para a mesma máquina de estados de
gerir_estado_fontes.py que já trata fonte-bloqueada, em vez de ficar só
em avisos.log sem nunca gerar Issue. Isolado em tmp_path — nunca toca
em data/bloqueios.json real.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402


def test_conteudo_insuficiente_regista_bloqueio(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, "SCRAPED_DIR", tmp_path)
    monkeypatch.setattr(sp, "AVISOS_LOG", tmp_path / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", tmp_path / "bloqueios.json")

    resultado = {
        "url": "https://dre.pt/pesquisa?q=teste",
        "status": "ok",
        "conteudo_extraido": {"titulo": "", "paragrafos": [], "itens_lista": []},
        "hash_conteudo": "abc",
    }
    sp._guardar_resultado("dre_psu", resultado)

    bloqueios = json.loads((tmp_path / "bloqueios.json").read_text(encoding="utf-8"))
    assert len(bloqueios) == 1
    assert bloqueios[0]["slug"] == "dre_psu"
    assert bloqueios[0]["chars_uteis"] == 0
    assert "conteúdo suspeito" in bloqueios[0]["motivos"][0]

    # latest.json não deve ser criado/actualizado — conteúdo insuficiente
    assert not (tmp_path / "dre_psu_latest.json").exists()


def test_conteudo_suficiente_nao_regista_bloqueio(tmp_path, monkeypatch):
    monkeypatch.setattr(sp, "SCRAPED_DIR", tmp_path)
    monkeypatch.setattr(sp, "AVISOS_LOG", tmp_path / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", tmp_path / "bloqueios.json")

    resultado = {
        "url": "https://exemplo.pt",
        "status": "ok",
        "conteudo_extraido": {"titulo": "x" * 200, "paragrafos": [], "itens_lista": []},
        "hash_conteudo": "xyz",
    }
    sp._guardar_resultado("fonte_ok", resultado)

    assert not (tmp_path / "bloqueios.json").exists()
    assert (tmp_path / "fonte_ok_latest.json").exists()


def test_conteudo_insuficiente_reaproveita_maquina_de_estados_existente(tmp_path, monkeypatch):
    """Confirma que gerir_estado_fontes.py trata este bloqueio exactamente
    como um bloqueio real — 3 dias consecutivos → elegível a Issue —
    sem precisar de nenhuma lógica nova nesse script."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from gerir_estado_fontes import calcular_novo_estado, SLUGS_MONITORIZADOS

    anterior = {
        "dre_psu": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 2, "ultima_ok": "2026-06-30"},
    }
    novo = calcular_novo_estado(anterior, ["dre_psu"], SLUGS_MONITORIZADOS, hoje="2026-07-05")
    assert novo["dre_psu"]["estado"] == "BLOQUEADO"
    assert novo["dre_psu"]["dias_consecutivos_bloqueado"] == 3
