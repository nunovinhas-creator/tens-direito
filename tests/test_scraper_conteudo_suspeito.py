"""
Testes para o achado de 2026-07-05 (auditoria de infraestrutura):
"conteúdo suspeito" (status "ok", sem sinal de bloqueio, mas conteúdo
extraído insuficiente — caso real: dre_psu, 0 chars desde a criação da
fonte) tem de contar para a mesma máquina de estados de
gerir_estado_fontes.py que já trata fonte-bloqueada, em vez de ficar só
em avisos.log sem nunca gerar Issue. Isolado em tmp_path — nunca toca
em data/bloqueios.json real.
"""
import datetime as _dt
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


def test_ponta_a_ponta_conteudo_vazio_nunca_fica_ok_e_gera_issue_ao_3o_dia(tmp_path, monkeypatch):
    """Prova de ponta-a-ponta pedida na auditoria de 2026-07-05 (Passo 2c):
    liga _guardar_resultado() (lado do scraper, escreve data/bloqueios.json)
    directamente a gerir_estado_fontes.main() (lê esse mesmo ficheiro, sem
    nenhum import cruzado entre os dois módulos) ao longo de 3 dias
    simulados — nunca um teste isolado de cada lado, para garantir que a
    integração real (não só cada peça em separado) fecha o silêncio
    original: uma extração de 0 caracteres NUNCA produz estado OK, e
    fica elegível a Issue exactamente no 3.º dia consecutivo, nem antes
    nem depois."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from gerir_estado_fontes import main as gerir_estado_main, fontes_para_issue

    raiz = tmp_path
    data_dir = raiz / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sp, "SCRAPED_DIR", data_dir)
    monkeypatch.setattr(sp, "AVISOS_LOG", data_dir / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", data_dir / "bloqueios.json")

    resultado_vazio = {
        "url": "https://dre.pt/pesquisa?q=presta%C3%A7%C3%A3o+social+%C3%BAnica",
        "status": "ok",
        "conteudo_extraido": {"titulo": "", "paragrafos": [], "itens_lista": []},
        "hash_conteudo": "mesmo-hash-todos-os-dias",
    }

    class _RelogioFixo:
        """Substitui sp.datetime por um relógio parado num dia — permite
        simular 3 corridas diárias sucessivas do scraper sem depender do
        relógio real do sistema. Só implementa o que _guardar_resultado
        usa (datetime.now(tz).strftime/.isoformat())."""
        def __init__(self, dia: str):
            self._agora = _dt.datetime.fromisoformat(f"{dia}T09:00:00+00:00")

        def now(self, tz=None):
            return self._agora

    dias = ["2026-07-01", "2026-07-02", "2026-07-03"]
    estados_por_dia = {}
    for dia in dias:
        monkeypatch.setattr(sp, "datetime", _RelogioFixo(dia))
        sp._guardar_resultado("dre_psu", dict(resultado_vazio))
        estado_dia = gerir_estado_main(raiz=raiz, hoje=dia)
        estados_por_dia[dia] = estado_dia

        # Nunca OK, em nenhum dos 3 dias — é exactamente o silêncio original.
        assert estado_dia["dre_psu"]["estado"] == "BLOQUEADO", (
            f"dia {dia}: dre_psu ficou OK com conteúdo vazio — silêncio reproduzido"
        )

    # Dias 1 e 2: registado, mas ainda sem Issue (ruído controlado).
    assert estados_por_dia["2026-07-01"]["dre_psu"]["dias_consecutivos_bloqueado"] == 1
    assert "dre_psu" not in fontes_para_issue(estados_por_dia["2026-07-01"])
    assert estados_por_dia["2026-07-02"]["dre_psu"]["dias_consecutivos_bloqueado"] == 2
    assert "dre_psu" not in fontes_para_issue(estados_por_dia["2026-07-02"])

    # Dia 3: elegível a Issue — o alerta visível que nunca existiu antes desta correcção.
    assert estados_por_dia["2026-07-03"]["dre_psu"]["dias_consecutivos_bloqueado"] == 3
    assert "dre_psu" in fontes_para_issue(estados_por_dia["2026-07-03"])
