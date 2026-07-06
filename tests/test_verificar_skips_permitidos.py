"""Testes para scripts/verificar_skips_permitidos.py — o guardrail que
substituiu o antigo LIMIAR_SKIPPED (número mágico que já deixou `main`
vermelha duas vezes, 2026-07-05 e 2026-07-06). Comparação por CONJUNTO
exacto entre os skips reais de uma corrida (relatório JUnit) e
tests/skips_permitidos.json — nunca por contagem.

Duas direcções de falha têm de estar cobertas, não só o caminho feliz:
1. um skip novo, não documentado, aparece na corrida;
2. uma entrada da allow-list deixou de saltar (ficou órfã).
"""
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from verificar_skips_permitidos import (  # noqa: E402
    ALLOW_LIST,
    _nodeid,
    extrair_skips_reais,
    verificar,
)


def _escrever_junit(tmp_path: Path, skips: dict[str, str]) -> Path:
    """Constrói um relatório JUnit mínimo, mas real (XML válido, mesma
    estrutura que o pytest --junitxml produz), com os skips indicados.
    Cada nodeid "tests/test_x.py::test_y[param]" é decomposto de volta
    para classname/name — o inverso exacto de _nodeid()."""
    testsuite = ET.Element("testsuite", name="pytest")
    for nodeid, mensagem in skips.items():
        caminho, name = nodeid.split("::", 1)
        classname = caminho[: -len(".py")].replace("/", ".")
        testcase = ET.SubElement(testsuite, "testcase", classname=classname, name=name, time="0.0")
        ET.SubElement(testcase, "skipped", type="pytest.skip", message=mensagem)
    # também um testcase que passou, para confirmar que não conta como skip
    passou = ET.SubElement(testsuite, "testcase", classname="tests.test_x", name="test_passa", time="0.0")
    del passou  # sem filho <skipped> — deliberadamente vazio

    root = ET.Element("testsuites")
    root.append(testsuite)
    caminho_xml = tmp_path / "report-testes.xml"
    ET.ElementTree(root).write(caminho_xml, encoding="utf-8", xml_declaration=True)
    return caminho_xml


# ── _nodeid() / extrair_skips_reais() ──────────────────────────────────────

def test_nodeid_reconstrucao_bate_certo_com_pytest_real():
    testcase = ET.Element(
        "testcase",
        classname="tests.test_adicionar_autoria_artigos",
        name="test_x[p/apoios-escolares.html]",
    )
    assert _nodeid(testcase) == (
        "tests/test_adicionar_autoria_artigos.py::test_x[p/apoios-escolares.html]"
    )


def test_extrair_skips_reais_le_xml_real(tmp_path):
    caminho = _escrever_junit(tmp_path, {"tests/test_a.py::test_b[x]": "motivo x"})
    skips = extrair_skips_reais(str(caminho))
    assert skips == {"tests/test_a.py::test_b[x]": "motivo x"}


# ── verificar() — as duas direcções de falha + o caminho feliz ─────────────

def test_verificar_bate_certo_devolve_lista_vazia():
    allow_list = {"tests/test_a.py::test_b[x]": {"motivo": "m", "tipo": "estrutural"}}
    skips_reais = {"tests/test_a.py::test_b[x]": "motivo real"}
    assert verificar("report-testes.xml", allow_list, skips_reais) == []


def test_skip_novo_nao_documentado_gera_erro():
    # Direcção 1: um teste salta na corrida mas não está na allow-list —
    # apanha o skip acidental de ambiente (binário/dependência em falta).
    allow_list = {}
    skips_reais = {"tests/test_a.py::test_b[x]": "binário em falta"}
    erros = verificar("report-testes.xml", allow_list, skips_reais)
    assert erros, "devia ter gerado erro"
    texto = "\n".join(erros)
    assert "tests/test_a.py::test_b[x]" in texto
    assert "binário em falta" in texto
    assert "SEM entrada" in texto


def test_entrada_allow_list_deixou_de_saltar_gera_erro():
    # Direcção 2: uma entrada da allow-list já não salta — o skip esperado
    # desapareceu silenciosamente (página corrigida ou apagada sem
    # actualizar a allow-list).
    allow_list = {"tests/test_a.py::test_b[x]": {"motivo": "m", "tipo": "estrutural"}}
    skips_reais = {}
    erros = verificar("report-testes.xml", allow_list, skips_reais)
    assert erros, "devia ter gerado erro"
    texto = "\n".join(erros)
    assert "tests/test_a.py::test_b[x]" in texto
    assert "já NÃO saltam" in texto


def test_ambas_as_direcoes_em_simultaneo_geram_os_dois_erros():
    allow_list = {
        "tests/test_a.py::test_orfa[x]": {"motivo": "m", "tipo": "estrutural"},
    }
    skips_reais = {
        "tests/test_a.py::test_novo[y]": "motivo novo",
    }
    erros = verificar("report-testes.xml", allow_list, skips_reais)
    texto = "\n".join(erros)
    assert "test_orfa" in texto
    assert "test_novo" in texto


# ── tests/skips_permitidos.json — schema e integração real ────────────────

def test_allow_list_real_e_json_valido_com_schema_correto():
    allow_list = json.loads(ALLOW_LIST.read_text(encoding="utf-8"))
    assert allow_list, "allow-list real não devia estar vazia"
    for nodeid, info in allow_list.items():
        assert "::" in nodeid, f"{nodeid!r} não parece um nodeid pytest"
        assert isinstance(info.get("motivo"), str) and info["motivo"], f"{nodeid}: motivo em falta"
        assert info.get("tipo") in ("estrutural", "ambiente"), f"{nodeid}: tipo inválido"


def test_allow_list_real_nunca_esconde_falta_de_carimbo_verificado_a():
    # Regra explícita desta allow-list: nenhuma entrada pode ser um "página
    # sem carimbo 'Verificado a'" disfarçado de estrutural — esse caso tem
    # sempre uma causa raiz corrigível (ver p/apoios-escolares.html, que
    # tinha "Verificado em junho de 2026" em vez do formato padrão, e foi
    # corrigido em vez de allow-listado).
    allow_list = json.loads(ALLOW_LIST.read_text(encoding="utf-8"))
    for nodeid, info in allow_list.items():
        assert "carimbo" not in info["motivo"].lower() or "verificado a" not in info["motivo"].lower(), (
            f"{nodeid}: parece esconder uma página sem carimbo 'Verificado a' — "
            "corrigir a página, nunca allow-listar este caso"
        )
