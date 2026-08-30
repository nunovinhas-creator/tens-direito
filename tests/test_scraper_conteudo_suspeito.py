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


# ── Achado de 2026-08-30: página canónica de "zero resultados" do DRE ──────
#
# dre_psu_regulamentacao devolveu esta página TODOS OS DIAS desde a sua
# criação (2026-08-17) até hoje (12 dias, confirmado em
# data/scraped/dre_psu_regulamentacao_*.json — hash idêntico em todos) e
# nunca foi apanhado pela guarda de "conteúdo suspeito" acima: o próprio
# texto de erro do DRE ("Certifique-se de que nenhuma palavra contém erros
# ortográficos...") tem 141 caracteres, acima de MIN_CHARS_CONTEUDO=100.
# O mesmo hash já aparecia em dre_habitacao_garantia desde 2026-07-20
# ("causa por investigar sem prioridade", CLAUDE.md) — mesma causa, nunca
# antes diagnosticada.
_CONTEUDO_SEM_RESULTADOS_DRE_REAL = {
    "titulo": "",
    "paragrafos": [
        "- Certifique-se de que nenhuma palavra contém erros ortográficos. "
        "- Tente utilizar outras palavras-chave. - Tente palavras-chave mais gerais."
    ],
    "itens_lista": [],
}


def test_pagina_sem_resultados_dre_regista_bloqueio_mesmo_com_chars_suficientes(tmp_path, monkeypatch):
    """O texto real (141 chars) passa MIN_CHARS_CONTEUDO=100 — sem o
    reconhecimento directo do texto canónico do DRE, esta página nunca
    seria apanhada pela guarda de "conteúdo suspeito" (era exactamente o
    que aconteceu em produção, 12 dias seguidos, Issue #131/#132)."""
    monkeypatch.setattr(sp, "SCRAPED_DIR", tmp_path)
    monkeypatch.setattr(sp, "AVISOS_LOG", tmp_path / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", tmp_path / "bloqueios.json")

    chars = sp._conteudo_chars(_CONTEUDO_SEM_RESULTADOS_DRE_REAL)
    assert chars > sp.MIN_CHARS_CONTEUDO, (
        "pré-condição do achado: o texto de erro do DRE tem de exceder o "
        "limiar de caracteres, senão o bug não reproduz"
    )

    resultado = {
        "url": "https://diariodarepublica.pt/dr/pesquisa",
        "status": "ok",
        "conteudo_extraido": _CONTEUDO_SEM_RESULTADOS_DRE_REAL,
        "hash_conteudo": "4c2a385012799c6d133591bdeb87e1206d149f1d8a58f830be8269ba303f2ca7",
    }
    sp._guardar_resultado("dre_psu_regulamentacao", resultado)

    bloqueios = json.loads((tmp_path / "bloqueios.json").read_text(encoding="utf-8"))
    assert len(bloqueios) == 1
    assert bloqueios[0]["slug"] == "dre_psu_regulamentacao"
    assert "pesquisa DRE sem resultados" in bloqueios[0]["motivos"][0]
    # latest.json não deve ser criado/actualizado — mesma regra do ramo de
    # "conteúdo suspeito" por caracteres.
    assert not (tmp_path / "dre_psu_regulamentacao_latest.json").exists()


def test_e_pagina_sem_resultados_dre_deteta_o_texto_canonico():
    assert sp._e_pagina_sem_resultados_dre(_CONTEUDO_SEM_RESULTADOS_DRE_REAL) is True
    assert sp._e_pagina_sem_resultados_dre({"titulo": "", "paragrafos": [], "itens_lista": []}) is False


def test_pagina_com_resultados_reais_nunca_confundida_com_sem_resultados(tmp_path, monkeypatch):
    """Sanity check: uma página com resultados genuínos (mesmo formato de
    dre_ias/dre_psu em produção) nunca é confundida com "zero resultados"
    — o marcador é uma frase específica do DRE, nunca activada por
    conteúdo real."""
    monkeypatch.setattr(sp, "SCRAPED_DIR", tmp_path)
    monkeypatch.setattr(sp, "AVISOS_LOG", tmp_path / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", tmp_path / "bloqueios.json")

    conteudo_real = {
        "titulo": 'Resultados de pesquisa: "indexante dos apoios sociais"',
        "paragrafos": [
            "Portaria n.º 480-A/2025/1 - Diário da República n.º 250/2025, Suplemento, Série I de 2025-12-30",
        ],
        "itens_lista": [
            "Portaria n.º 480-A/2025/1 - Diário da República n.º 250/2025, Suplemento, Série I de 2025-12-30",
        ],
    }
    assert sp._e_pagina_sem_resultados_dre(conteudo_real) is False

    resultado = {
        "url": "https://diariodarepublica.pt/dr/pesquisa",
        "status": "ok",
        "conteudo_extraido": conteudo_real,
        "hash_conteudo": "hash-de-conteudo-real",
    }
    sp._guardar_resultado("dre_ias", resultado)
    assert not (tmp_path / "bloqueios.json").exists()
    assert (tmp_path / "dre_ias_latest.json").exists()


def test_ponta_a_ponta_dre_sem_resultados_nunca_fica_ok_e_gera_issue_ao_3o_dia(tmp_path, monkeypatch):
    """Mesmo padrão de `test_ponta_a_ponta_conteudo_vazio_nunca_fica_ok_e_gera_issue_ao_3o_dia`
    acima, mas para o novo caso — reproduz os 12 dias reais de
    dre_psu_regulamentacao (aqui só os primeiros 3, que já bastam para o
    limiar) com o conteúdo REAL de "zero resultados", nunca 0 chars."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from gerir_estado_fontes import main as gerir_estado_main, fontes_para_issue

    raiz = tmp_path
    data_dir = raiz / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sp, "SCRAPED_DIR", data_dir)
    monkeypatch.setattr(sp, "AVISOS_LOG", data_dir / "avisos.log")
    monkeypatch.setattr(sp, "BLOQUEIOS_PATH", data_dir / "bloqueios.json")

    resultado_sem_resultados = {
        "url": "https://diariodarepublica.pt/dr/pesquisa",
        "status": "ok",
        "conteudo_extraido": _CONTEUDO_SEM_RESULTADOS_DRE_REAL,
        "hash_conteudo": "4c2a385012799c6d133591bdeb87e1206d149f1d8a58f830be8269ba303f2ca7",
    }

    class _RelogioFixo:
        def __init__(self, dia: str):
            self._agora = _dt.datetime.fromisoformat(f"{dia}T09:00:00+00:00")

        def now(self, tz=None):
            return self._agora

    dias = ["2026-08-17", "2026-08-18", "2026-08-19"]
    estados_por_dia = {}
    for dia in dias:
        monkeypatch.setattr(sp, "datetime", _RelogioFixo(dia))
        sp._guardar_resultado("dre_psu_regulamentacao", dict(resultado_sem_resultados))
        estado_dia = gerir_estado_main(raiz=raiz, hoje=dia)
        estados_por_dia[dia] = estado_dia
        assert estado_dia["dre_psu_regulamentacao"]["estado"] == "BLOQUEADO", (
            f"dia {dia}: dre_psu_regulamentacao ficou OK devolvendo a página "
            "de zero resultados do DRE — o mesmo silêncio de 12 dias real"
        )

    assert estados_por_dia["2026-08-17"]["dre_psu_regulamentacao"]["dias_consecutivos_bloqueado"] == 1
    assert "dre_psu_regulamentacao" not in fontes_para_issue(estados_por_dia["2026-08-17"])
    assert estados_por_dia["2026-08-19"]["dre_psu_regulamentacao"]["dias_consecutivos_bloqueado"] == 3
    assert "dre_psu_regulamentacao" in fontes_para_issue(estados_por_dia["2026-08-19"])
