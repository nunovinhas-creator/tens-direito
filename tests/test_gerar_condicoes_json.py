"""
Testes de scripts/gerar_condicoes_json.py (PR 2 da série "simulador
universal"). Mesmo espírito de test_gerar_parametros_json — mas isolado em
fixtures temporárias (tmp_path), nunca contra dados/condicoes/*.yaml real,
para não depender do conteúdo que outros PRs desta série forem
acrescentando. O teste de integração com o CSI real fica à parte, no fim
do ficheiro.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import gerar_condicoes_json  # noqa: E402


def _preparar(tmp_path, monkeypatch, perguntas: dict, parametros: dict, apoios_yaml: dict):
    condicoes_dir = tmp_path / "condicoes"
    condicoes_dir.mkdir()
    perguntas_path = condicoes_dir / "perguntas.yaml"
    perguntas_path.write_text(yaml.dump(perguntas, allow_unicode=True), encoding="utf-8")

    parametros_path = tmp_path / "parametros.json"
    parametros_path.write_text(json.dumps(parametros), encoding="utf-8")

    for nome, conteudo in apoios_yaml.items():
        (condicoes_dir / f"{nome}.yaml").write_text(yaml.dump(conteudo, allow_unicode=True), encoding="utf-8")

    monkeypatch.setattr(gerar_condicoes_json, "CONDICOES_DIR", condicoes_dir)
    monkeypatch.setattr(gerar_condicoes_json, "PERGUNTAS_PATH", perguntas_path)
    monkeypatch.setattr(gerar_condicoes_json, "PARAMETROS_JSON", parametros_path)


PERGUNTAS_BASE = {
    "idade_meses_totais": {"descricao": "idade em meses", "tipo": "numero", "unidade": "meses"},
    "reside_legalmente_pt": {"descricao": "reside legalmente", "tipo": "categorica", "opcoes": ["sim", "nao"]},
    "anos_residencia_pt": {"descricao": "anos de residência", "tipo": "numero", "unidade": "anos"},
}

PARAMETROS_BASE = {"prestacoes": {"csi": {"idade_minima_meses_totais": {"valor": 801}}}}


def test_golden_path_resolve_parametro_e_valor_literal(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "pagina": "complemento-solidario-idosos.html",
        "operador": "all",
        "condicoes": [
            {
                "id": "idade_minima",
                "tipo": "limiar",
                "campo": "idade_meses_totais",
                "operador_comparacao": "gte",
                "parametro": "csi.idade_minima_meses_totais",
            },
            {
                "id": "reside_legalmente",
                "tipo": "categorica",
                "campo": "reside_legalmente_pt",
                "operador_comparacao": "eq",
                "valor_literal": "sim",
            },
            {
                "id": "anos_residencia_minima",
                "tipo": "limiar",
                "campo": "anos_residencia_pt",
                "operador_comparacao": "gte",
                "valor_literal": 6,
                "fonte_pagina": "complemento-solidario-idosos.html",
            },
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})

    consolidado = gerar_condicoes_json.consolidar()

    assert consolidado["apoios"]["csi"]["operador"] == "all"
    condicoes = {c["id"]: c for c in consolidado["apoios"]["csi"]["condicoes"]}
    assert condicoes["idade_minima"]["valor"] == 801
    assert condicoes["idade_minima"]["fonte"] == {"tipo": "parametro", "referencia": "csi.idade_minima_meses_totais"}
    assert condicoes["reside_legalmente"]["fonte"] == {"tipo": "literal_enum"}
    assert condicoes["anos_residencia_minima"]["fonte"] == {
        "tipo": "literal_pagina",
        "pagina": "complemento-solidario-idosos.html",
    }


def test_parametro_inexistente_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "x",
                "tipo": "limiar",
                "campo": "idade_meses_totais",
                "operador_comparacao": "gte",
                "parametro": "csi.parametro_que_nao_existe",
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="não existe"):
        gerar_condicoes_json.consolidar()


def test_valor_literal_limiar_sem_fonte_pagina_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "x",
                "tipo": "limiar",
                "campo": "anos_residencia_pt",
                "operador_comparacao": "gte",
                "valor_literal": 6,
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="fonte_pagina"):
        gerar_condicoes_json.consolidar()


def test_valor_literal_categorica_fora_das_opcoes_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "x",
                "tipo": "categorica",
                "campo": "reside_legalmente_pt",
                "operador_comparacao": "eq",
                "valor_literal": "talvez",
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="opção válida"):
        gerar_condicoes_json.consolidar()


def test_parametro_e_valor_literal_em_simultaneo_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "x",
                "tipo": "limiar",
                "campo": "idade_meses_totais",
                "operador_comparacao": "gte",
                "parametro": "csi.idade_minima_meses_totais",
                "valor_literal": 801,
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="exactamente um"):
        gerar_condicoes_json.consolidar()


def test_nenhum_de_parametro_ou_valor_literal_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {"id": "x", "tipo": "limiar", "campo": "idade_meses_totais", "operador_comparacao": "gte"}
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="exactamente um"):
        gerar_condicoes_json.consolidar()


def test_campo_inexistente_em_perguntas_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "x",
                "tipo": "limiar",
                "campo": "campo_fantasma",
                "operador_comparacao": "gte",
                "valor_literal": 1,
                "fonte_pagina": "x.html",
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="não existe em perguntas.yaml"):
        gerar_condicoes_json.consolidar()


def test_ids_duplicados_falha(tmp_path, monkeypatch):
    condicao = {
        "id": "repetido",
        "tipo": "categorica",
        "campo": "reside_legalmente_pt",
        "operador_comparacao": "eq",
        "valor_literal": "sim",
    }
    apoio_yaml = {"apoio": "csi", "operador": "all", "condicoes": [condicao, dict(condicao)]}
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="duplicados"):
        gerar_condicoes_json.consolidar()


def test_grupo_aninhado_any_resolve_ambas_as_folhas(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "idade_minima",
                "operador": "any",
                "condicoes": [
                    {
                        "id": "idade_normal",
                        "tipo": "limiar",
                        "campo": "idade_meses_totais",
                        "operador_comparacao": "gte",
                        "parametro": "csi.idade_minima_meses_totais",
                    },
                    {
                        "id": "excepcao",
                        "tipo": "categorica",
                        "campo": "reside_legalmente_pt",
                        "operador_comparacao": "eq",
                        "valor_literal": "sim",
                    },
                ],
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})

    consolidado = gerar_condicoes_json.consolidar()

    grupo = consolidado["apoios"]["csi"]["condicoes"][0]
    assert grupo["id"] == "idade_minima"
    assert grupo["operador"] == "any"
    ids_filhos = {c["id"] for c in grupo["condicoes"]}
    assert ids_filhos == {"idade_normal", "excepcao"}


def test_grupo_aninhado_sem_operador_valido_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [
            {
                "id": "grupo",
                "operador": "xor",
                "condicoes": [
                    {
                        "id": "x",
                        "tipo": "categorica",
                        "campo": "reside_legalmente_pt",
                        "operador_comparacao": "eq",
                        "valor_literal": "sim",
                    }
                ],
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="grupo sem 'operador'"):
        gerar_condicoes_json.consolidar()


def test_id_duplicado_dentro_de_grupo_falha(tmp_path, monkeypatch):
    folha = {
        "id": "repetido",
        "tipo": "categorica",
        "campo": "reside_legalmente_pt",
        "operador_comparacao": "eq",
        "valor_literal": "sim",
    }
    apoio_yaml = {
        "apoio": "csi",
        "operador": "all",
        "condicoes": [{"id": "grupo", "operador": "any", "condicoes": [folha, dict(folha)]}],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="duplicados"):
        gerar_condicoes_json.consolidar()


def test_operador_apoio_invalido_falha(tmp_path, monkeypatch):
    apoio_yaml = {
        "apoio": "csi",
        "operador": "xor",
        "condicoes": [
            {
                "id": "x",
                "tipo": "categorica",
                "campo": "reside_legalmente_pt",
                "operador_comparacao": "eq",
                "valor_literal": "sim",
            }
        ],
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_BASE, PARAMETROS_BASE, {"csi": apoio_yaml})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="'operador'"):
        gerar_condicoes_json.consolidar()


# ── Integração com o CSI real (dados/condicoes/csi.yaml + dados/parametros.json do repo) ──


def test_integracao_csi_real_gera_sem_erro():
    if not gerar_condicoes_json.PARAMETROS_JSON.exists():
        pytest.skip("dados/parametros.json não gerado neste checkout — correr gerar_parametros_json.py primeiro")
    if not (gerar_condicoes_json.CONDICOES_DIR / "csi.yaml").exists():
        pytest.skip("dados/condicoes/csi.yaml ainda não existe neste checkout")

    consolidado = gerar_condicoes_json.consolidar()

    assert "csi" in consolidado["apoios"]
    ids = set(gerar_condicoes_json._coletar_ids(consolidado["apoios"]["csi"]["condicoes"]))
    assert {
        "idade_minima",
        "idade_normal",
        "excepcao_invalidez_sem_reavaliacao",
        "reside_legalmente",
        "anos_residencia_minima",
    } <= ids


# ── PR 10: fórmula psu_valor_positivo e marca de substituição entre apoios ──


PARAMETROS_PSU_FIXTURE = {
    "prestacoes": {
        "psu": {
            "ias_2026": {"valor": 500},
            "valor_referencia_multiplicador_ias": {"valor": 0.5},
            "ponderacao_titular": {"valor": 1},
            "ponderacao_maior": {"valor": 0.7},
            "ponderacao_menor": {"valor": 0.5},
            "cit_limiar_multiplicador_ias": {"valor": 0.2},
            "cit_taxa_acima_limiar": {"valor": 0.5},
            "valor_minimo_euros": {"valor": 10},
            "data_producao_efeitos": {"valor": "2026-12-31"},
        }
    }
}

PERGUNTAS_PSU_FIXTURE = {
    "trabalho": {"descricao": "t", "tipo": "numero", "unidade": "EUR"},
    "outros": {"descricao": "o", "tipo": "numero", "unidade": "EUR"},
    "adultos": {"descricao": "a", "tipo": "numero", "unidade": "pessoas"},
    "menores": {"descricao": "m", "tipo": "numero", "unidade": "pessoas"},
}


def _formula_psu(**alteracoes):
    base = {
        "id": "f",
        "tipo": "formula",
        "formula": "psu_valor_positivo",
        "campo_rendimento_trabalho": "trabalho",
        "campo_outros_rendimentos": "outros",
        "campo_adultos_adicionais": "adultos",
        "campo_menores": "menores",
        "parametro_ias": "psu.ias_2026",
        "parametro_valor_referencia_multiplicador": "psu.valor_referencia_multiplicador_ias",
        "parametro_ponderacao_titular": "psu.ponderacao_titular",
        "parametro_ponderacao_maior": "psu.ponderacao_maior",
        "parametro_ponderacao_menor": "psu.ponderacao_menor",
        "parametro_cit_limiar_multiplicador": "psu.cit_limiar_multiplicador_ias",
        "parametro_cit_taxa": "psu.cit_taxa_acima_limiar",
        "parametro_valor_minimo": "psu.valor_minimo_euros",
    }
    base.update(alteracoes)
    return base


def test_formula_psu_resolve_multiplicadores_contra_o_ias(tmp_path, monkeypatch):
    apoio = {"apoio": "psu", "operador": "all", "condicoes": [_formula_psu()]}
    _preparar(tmp_path, monkeypatch, PERGUNTAS_PSU_FIXTURE, PARAMETROS_PSU_FIXTURE, {"psu": apoio})
    f = gerar_condicoes_json.consolidar()["apoios"]["psu"]["condicoes"][0]
    assert f["valor_referencia"] == 250  # 0,5 × IAS 500
    assert f["cit_limiar"] == 100  # 0,2 × IAS 500
    assert f["ponderacao_maior"] == 0.7
    assert f["valor_minimo"] == 10


def test_formula_psu_sem_parametro_obrigatorio_falha(tmp_path, monkeypatch):
    formula = _formula_psu()
    del formula["parametro_cit_taxa"]
    apoio = {"apoio": "psu", "operador": "all", "condicoes": [formula]}
    _preparar(tmp_path, monkeypatch, PERGUNTAS_PSU_FIXTURE, PARAMETROS_PSU_FIXTURE, {"psu": apoio})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="parametro_cit_taxa"):
        gerar_condicoes_json.consolidar()


def test_formula_psu_com_campo_inexistente_falha(tmp_path, monkeypatch):
    apoio = {"apoio": "psu", "operador": "all", "condicoes": [_formula_psu(campo_menores="fantasma")]}
    _preparar(tmp_path, monkeypatch, PERGUNTAS_PSU_FIXTURE, PARAMETROS_PSU_FIXTURE, {"psu": apoio})
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="campo inexistente"):
        gerar_condicoes_json.consolidar()


def _apoio_simples(nome, **extra):
    return {
        "apoio": nome,
        "operador": "all",
        "condicoes": [
            {"id": "c", "tipo": "categorica", "campo": "reside", "operador_comparacao": "eq", "valor_literal": "sim"}
        ],
        **extra,
    }


PERGUNTAS_SUBSTITUICAO = {"reside": {"descricao": "r", "tipo": "categorica", "opcoes": ["sim", "nao"]}}


def test_substituido_por_resolve_data_a_partir_de_parametro(tmp_path, monkeypatch):
    apoios = {
        "antigo": _apoio_simples(
            "antigo", substituido_por="novo", substituido_a_partir_de_parametro="psu.data_producao_efeitos"
        ),
        "novo": _apoio_simples("novo"),
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_SUBSTITUICAO, PARAMETROS_PSU_FIXTURE, apoios)
    consolidado = gerar_condicoes_json.consolidar()["apoios"]
    assert consolidado["antigo"]["substituido_por"] == "novo"
    assert consolidado["antigo"]["substituido_a_partir_de"] == "2026-12-31"
    assert "substituido_por" not in consolidado["novo"]


def test_substituido_por_apoio_inexistente_falha(tmp_path, monkeypatch):
    apoios = {
        "antigo": _apoio_simples(
            "antigo", substituido_por="fantasma", substituido_a_partir_de_parametro="psu.data_producao_efeitos"
        ),
    }
    _preparar(tmp_path, monkeypatch, PERGUNTAS_SUBSTITUICAO, PARAMETROS_PSU_FIXTURE, apoios)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="apoio inexistente"):
        gerar_condicoes_json.consolidar()


def test_substituido_por_sem_data_falha(tmp_path, monkeypatch):
    apoios = {"antigo": _apoio_simples("antigo", substituido_por="novo"), "novo": _apoio_simples("novo")}
    _preparar(tmp_path, monkeypatch, PERGUNTAS_SUBSTITUICAO, PARAMETROS_PSU_FIXTURE, apoios)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="substituido_a_partir_de_parametro"):
        gerar_condicoes_json.consolidar()
