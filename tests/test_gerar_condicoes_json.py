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


def _completar_campos_do_assistente(perguntas: dict, apoios_yaml: dict) -> tuple[dict, dict]:
    """PR 11: o compilador passou a exigir `pergunta`/`rotulos` em cada
    pergunta e `titulo`/`simulador` em cada apoio. As fixtures dos testes
    anteriores ao PR 11 não são sobre isso — preenche o mínimo válido, sem
    nunca sobrepor o que um teste tenha definido de propósito."""
    perguntas = {c: dict(d) for c, d in perguntas.items()}
    for campo, dados in perguntas.items():
        dados.setdefault("pergunta", f"Pergunta sobre {campo}?")
        if dados.get("tipo") == "categorica":
            dados.setdefault("rotulos", {o: str(o) for o in dados.get("opcoes", [])})
    apoios_yaml = {n: dict(c) for n, c in apoios_yaml.items()}
    for conteudo in apoios_yaml.values():
        conteudo.setdefault("titulo", f"Apoio {conteudo.get('apoio')}")
        conteudo.setdefault("simulador", "/simuladores.html")
        conteudo.setdefault("tipo_link", "guia")
    return perguntas, apoios_yaml


def _preparar(tmp_path, monkeypatch, perguntas: dict, parametros: dict, apoios_yaml: dict, completar: bool = True):
    if completar:
        perguntas, apoios_yaml = _completar_campos_do_assistente(perguntas, apoios_yaml)
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


# ── PR 11: campos do assistente (pergunta, rotulos, aplicavel_se, titulo, simulador) ──


def _apoio_min(**extra):
    base = {
        "apoio": "x",
        "operador": "all",
        "titulo": "Apoio X",
        "simulador": "/simuladores.html",
        "tipo_link": "guia",
        "condicoes": [
            {"id": "c", "tipo": "categorica", "campo": "reside", "operador_comparacao": "eq", "valor_literal": "sim"}
        ],
    }
    base.update(extra)
    return base


def _pergunta_reside(**extra):
    base = {"descricao": "r", "tipo": "categorica", "opcoes": ["sim", "nao"], "pergunta": "Resides?",
            "rotulos": {"sim": "Sim", "nao": "Não"}}
    base.update(extra)
    return base


def test_titulo_e_simulador_passam_para_o_json(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}}, {"x": _apoio_min()},
              completar=False)
    apoio = gerar_condicoes_json.consolidar()["apoios"]["x"]
    assert apoio["titulo"] == "Apoio X"
    assert apoio["simulador"] == "/simuladores.html"


@pytest.mark.parametrize("alteracao,erro", [
    ({"titulo": ""}, "titulo"),
    ({"simulador": "simuladores.html"}, "simulador"),
    ({"simulador": "/nao-existe-de-todo.html"}, "página inexistente"),
])
def test_titulo_ou_simulador_invalido_falha(tmp_path, monkeypatch, alteracao, erro):
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}},
              {"x": _apoio_min(**alteracao)}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()


def test_apoio_sem_titulo_falha(tmp_path, monkeypatch):
    apoio = _apoio_min()
    del apoio["titulo"]
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}}, {"x": apoio}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="titulo"):
        gerar_condicoes_json.consolidar()


@pytest.mark.parametrize("pergunta,erro", [
    ({"pergunta": ""}, "pergunta"),
    ({"rotulos": {"sim": "Sim"}}, "em falta"),
    ({"rotulos": {"sim": "Sim", "nao": "Não", "talvez": "Talvez"}}, "a mais"),
    ({"rotulos": {"sim": "Sim", "nao": " "}}, "vazio"),
    ({"aplicavel_se": {"campo": "reside", "valor": "sim"}}, "próprio campo"),
    ({"aplicavel_se": {"campo": "fantasma", "valor": "sim"}}, "inexistente"),
])
def test_pergunta_invalida_falha(tmp_path, monkeypatch, pergunta, erro):
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside(**pergunta)}, {"prestacoes": {}},
              {"x": _apoio_min()}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()


def test_rotulos_em_pergunta_numerica_falha(tmp_path, monkeypatch):
    perguntas = {
        "reside": _pergunta_reside(),
        "anos": {"descricao": "a", "tipo": "numero", "unidade": "anos", "pergunta": "Quantos?",
                 "rotulos": {"1": "um"}},
    }
    _preparar(tmp_path, monkeypatch, perguntas, {"prestacoes": {}}, {"x": _apoio_min()}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="só faz sentido"):
        gerar_condicoes_json.consolidar()


def test_aplicavel_se_com_valor_fora_das_opcoes_falha(tmp_path, monkeypatch):
    perguntas = {
        "reside": _pergunta_reside(),
        "anos": {"descricao": "a", "tipo": "numero", "unidade": "anos", "pergunta": "Quantos?",
                 "aplicavel_se": {"campo": "reside", "valor": "talvez"}},
    }
    _preparar(tmp_path, monkeypatch, perguntas, {"prestacoes": {}}, {"x": _apoio_min()}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="não é opção"):
        gerar_condicoes_json.consolidar()


def test_campo_generico_data_nascimento_proibido(tmp_path, monkeypatch):
    perguntas = {"reside": _pergunta_reside(),
                 "data_nascimento": {"descricao": "d", "tipo": "data", "pergunta": "Quando nasceste?"}}
    _preparar(tmp_path, monkeypatch, perguntas, {"prestacoes": {}}, {"x": _apoio_min()}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match="genérico"):
        gerar_condicoes_json.consolidar()


def test_verificado_em_e_o_mais_recente_dos_parametros_das_condicoes(tmp_path, monkeypatch):
    # O carimbo da página vem daqui: a data mais recente dos parâmetros que as
    # condições usam — nunca a data do dia. Literais não têm data (nunca se inventa).
    parametros = {"prestacoes": {"p": {
        "a": {"valor": 1, "verificado_em": "2026-03-01"},
        "b": {"valor": 2, "verificado_em": "2026-05-20"},
    }}}
    perguntas = {"reside": _pergunta_reside(),
                 "n": {"descricao": "n", "tipo": "numero", "unidade": "anos", "pergunta": "Quantos?"}}

    def limiar(id_, ref):
        return {"id": id_, "tipo": "limiar", "campo": "n", "operador_comparacao": "gte", "parametro": ref}

    apoios = {
        "x": _apoio_min(condicoes=[limiar("ca", "p.a"), limiar("cb", "p.b")]),
        "y": _apoio_min(apoio="y", condicoes=[limiar("ca", "p.a")]),
        "z": _apoio_min(apoio="z"),  # só literal: sem data
    }
    _preparar(tmp_path, monkeypatch, perguntas, parametros, apoios, completar=False)
    c = gerar_condicoes_json.consolidar()
    assert c["apoios"]["x"]["verificado_em"] == "2026-05-20"
    assert c["apoios"]["y"]["verificado_em"] == "2026-03-01"
    assert "verificado_em" not in c["apoios"]["z"]
    assert c["verificado_em"] == "2026-05-20"
    assert c["apoios"]["x"]["condicoes"][0]["verificado_em"] == "2026-03-01"


# ── PR 12: limiar sobre campo de data ───────────────────────────────────────
# O motor compara datas ISO como strings (a ordem lexicográfica de AAAA-MM-DD
# é a cronológica). Um valor noutro formato, ou um número sem unidade, daria
# um resultado errado em silêncio — o compilador recusa-os.


def _perguntas_data():
    return {"reside": _pergunta_reside(),
            "nasc": {"descricao": "d", "tipo": "data", "pergunta": "Quando nasceu?"}}


def _limiar_data(**extra):
    base = {"id": "d", "tipo": "limiar", "campo": "nasc", "operador_comparacao": "gte", "parametro": "p.v"}
    base.update(extra)
    return base


def test_limiar_de_data_sem_unidade_aceita_data_iso(tmp_path, monkeypatch):
    parametros = {"prestacoes": {"p": {"v": {"valor": "2021-09-01"}}}}
    _preparar(tmp_path, monkeypatch, _perguntas_data(), parametros,
              {"x": _apoio_min(condicoes=[_limiar_data()])}, completar=False)
    cond = gerar_condicoes_json.consolidar()["apoios"]["x"]["condicoes"][0]
    assert cond["valor"] == "2021-09-01"
    assert cond["unidade_comparacao"] is None


@pytest.mark.parametrize("valor,unidade,erro", [
    ("01/09/2021", None, "data ISO"),       # formato português: a comparação por string erraria
    ("2021-9-1", None, "data ISO"),         # sem zeros: "2021-10-01" < "2021-9-1" como string
    ("2021-02-30", None, "data ISO"),       # data inexistente
    (16, None, "data ISO"),                 # idade sem unidade_comparacao
    ("2021-09-01", "anos", "valor numérico"),
    (16, "dias", "unidade_comparacao"),
])
def test_limiar_de_data_invalido_falha(tmp_path, monkeypatch, valor, unidade, erro):
    parametros = {"prestacoes": {"p": {"v": {"valor": valor}}}}
    extra = {"unidade_comparacao": unidade} if unidade else {}
    _preparar(tmp_path, monkeypatch, _perguntas_data(), parametros,
              {"x": _apoio_min(condicoes=[_limiar_data(**extra)])}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()


def test_limiar_de_idade_em_anos_continua_aceite(tmp_path, monkeypatch):
    parametros = {"prestacoes": {"p": {"v": {"valor": 16}}}}
    _preparar(tmp_path, monkeypatch, _perguntas_data(), parametros,
              {"x": _apoio_min(condicoes=[_limiar_data(operador_comparacao="lte", unidade_comparacao="anos")])},
              completar=False)
    assert gerar_condicoes_json.consolidar()["apoios"]["x"]["condicoes"][0]["valor"] == 16


def test_creche_real_compila_com_data_do_parametro():
    parametros = json.loads((RAIZ / "dados" / "parametros.json").read_text(encoding="utf-8"))
    c = gerar_condicoes_json.consolidar()
    creche = c["apoios"]["creche"]
    assert creche["simulador"] == "/creche-gratuita.html"
    cond = {x["id"]: x for x in creche["condicoes"]}["nascida_a_partir_da_data_elegivel"]
    assert cond["fonte"] == {"tipo": "parametro", "referencia": "creche.creche_elegivel_nascidos_apos"}
    assert cond["valor"] == parametros["prestacoes"]["creche"]["creche_elegivel_nascidos_apos"]["valor"]
    assert cond["operador_comparacao"] == "gte"


# ── PR 12: proveniência dos parâmetros usados pelas condições ───────────────

CAMPOS_FONTE = ("vigencia_inicio", "referencia_legal", "fonte_url", "verificado_em")
# Apoios cujos parâmetros têm de citar o artigo (regra a partir do PR 12;
# os anteriores ficam como estão — ver "Por confirmar" do PR 12).
APOIOS_COM_ARTIGO_OBRIGATORIO = ("creche",)


def _referencias(condicoes: list) -> set[str]:
    refs: set[str] = set()
    for c in condicoes:
        if "condicoes" in c:
            refs |= _referencias(c["condicoes"])
            continue
        fonte = c.get("fonte", {})
        if fonte.get("tipo") == "parametro":
            refs.add(fonte["referencia"])
        elif fonte.get("tipo") == "parametro_multiplo":
            refs.update(fonte["referencias"])
    return refs


def _erros_de_proveniencia(condicoes_json: dict, parametros_json: dict) -> list[str]:
    import re
    erros = []
    prestacoes = parametros_json["prestacoes"]
    for apoio, dados in condicoes_json["apoios"].items():
        for ref in sorted(_referencias(dados["condicoes"])):
            prestacao, nome = ref.split(".", 1)
            p = prestacoes[prestacao][nome]
            falta = [k for k in CAMPOS_FONTE if not p.get(k)]
            if falta:
                erros.append(f"{apoio}: {ref} sem {falta}")
            if apoio in APOIOS_COM_ARTIGO_OBRIGATORIO and not re.search(r"\bart(\.|igo)", p.get("referencia_legal") or "", re.I):
                erros.append(f"{apoio}: {ref} sem artigo na referencia_legal")
    return erros


def _json_real(nome):
    return json.loads((RAIZ / "dados" / nome).read_text(encoding="utf-8"))


def test_parametros_das_condicoes_tem_os_quatro_campos_de_fonte():
    assert _erros_de_proveniencia(_json_real("condicoes.json"), _json_real("parametros.json")) == []


@pytest.mark.parametrize("campo", CAMPOS_FONTE)
def test_guardrail_proveniencia_falha_quando_estragado(campo):
    parametros = _json_real("parametros.json")
    parametros["prestacoes"]["creche"]["creche_elegivel_nascidos_apos"][campo] = None
    erros = _erros_de_proveniencia(_json_real("condicoes.json"), parametros)
    assert any("creche.creche_elegivel_nascidos_apos" in e and campo in e for e in erros), erros


def test_guardrail_artigo_falha_quando_estragado():
    parametros = _json_real("parametros.json")
    parametros["prestacoes"]["creche"]["creche_elegivel_nascidos_apos"]["referencia_legal"] = "Portaria n.º 305/2022"
    erros = _erros_de_proveniencia(_json_real("condicoes.json"), parametros)
    assert erros == ["creche: creche.creche_elegivel_nascidos_apos sem artigo na referencia_legal"]


# ── PR 12: tipo_link (simulador ou guia) ────────────────────────────────────


def test_tipo_link_passa_para_o_json(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}},
              {"x": _apoio_min(simulador="/simulador-abono.html", tipo_link="simulador")}, completar=False)
    assert gerar_condicoes_json.consolidar()["apoios"]["x"]["tipo_link"] == "simulador"


@pytest.mark.parametrize("alteracao,erro", [
    ({"tipo_link": None}, "tipo_link"),
    ({"tipo_link": "pagina"}, "tipo_link"),
    # guia a apontar para um simulador, e simulador a apontar para um guia
    ({"simulador": "/simulador-abono.html", "tipo_link": "guia"}, "não bate"),
    ({"simulador": "/creche-gratuita.html", "tipo_link": "simulador"}, "não bate"),
])
def test_tipo_link_invalido_falha(tmp_path, monkeypatch, alteracao, erro):
    apoio = _apoio_min(**alteracao)
    if apoio["tipo_link"] is None:
        del apoio["tipo_link"]
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}}, {"x": apoio},
              completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()


def test_creche_real_e_guia_e_os_restantes_sao_simuladores():
    apoios = gerar_condicoes_json.consolidar()["apoios"]
    assert apoios["creche"]["tipo_link"] == "guia"
    assert {a["tipo_link"] for n, a in apoios.items() if n != "creche"} == {"simulador"}



# ── PR 12 (revisão): limiar_faixa_incerta ───────────────────────────────────


def _faixa(**extra):
    base = {"id": "f", "tipo": "limiar_faixa_incerta", "campo": "nasc", "unidade_comparacao": "anos",
            "parametro": "p.lim", "parametro_exclusao": "p.exc", "motivo_indeterminado": "a norma não decide"}
    base.update(extra)
    return {k: v for k, v in base.items() if v is not None}


PARAMETROS_FAIXA = {"prestacoes": {"p": {"lim": {"valor": 3, "verificado_em": "2026-01-01"},
                                         "exc": {"valor": 4, "verificado_em": "2026-02-01"}}}}


def test_faixa_incerta_resolve_os_dois_parametros_e_o_motivo(tmp_path, monkeypatch):
    _preparar(tmp_path, monkeypatch, _perguntas_data(), PARAMETROS_FAIXA,
              {"x": _apoio_min(condicoes=[_faixa()])}, completar=False)
    cond = gerar_condicoes_json.consolidar()["apoios"]["x"]["condicoes"][0]
    assert (cond["valor"], cond["valor_exclusao"]) == (3, 4)
    assert cond["motivo_indeterminado"] == "a norma não decide"
    assert cond["fonte"] == {"tipo": "parametro_multiplo", "referencias": ["p.lim", "p.exc"]}
    assert cond["verificado_em"] == "2026-02-01"


@pytest.mark.parametrize("alteracao,parametros,erro", [
    ({"motivo_indeterminado": None}, None, "motivo_indeterminado"),
    ({"motivo_indeterminado": "  "}, None, "motivo_indeterminado"),
    ({"parametro_exclusao": None}, None, "parametro_exclusao"),
    ({"valor_literal": 3}, None, "não usa"),
    ({"operador_comparacao": "lt"}, None, "não usa"),
    ({"unidade_comparacao": None}, None, "unidade_comparacao"),
    ({}, {"prestacoes": {"p": {"lim": {"valor": 4}, "exc": {"valor": 4}}}}, "menor"),
    ({}, {"prestacoes": {"p": {"lim": {"valor": 5}, "exc": {"valor": 4}}}}, "menor"),
    ({}, {"prestacoes": {"p": {"lim": {"valor": "3"}, "exc": {"valor": 4}}}}, "números"),
])
def test_faixa_incerta_invalida_falha(tmp_path, monkeypatch, alteracao, parametros, erro):
    _preparar(tmp_path, monkeypatch, _perguntas_data(), parametros or PARAMETROS_FAIXA,
              {"x": _apoio_min(condicoes=[_faixa(**alteracao)])}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()


def test_creche_real_idade_vem_dos_dois_parametros_da_portaria_198():
    parametros = json.loads((RAIZ / "dados" / "parametros.json").read_text(encoding="utf-8"))["prestacoes"]["creche"]
    cond = {c["id"]: c for c in gerar_condicoes_json.consolidar()["apoios"]["creche"]["condicoes"]}["idade_ate_aos_3_anos"]
    assert cond["fonte"]["referencias"] == ["creche.creche_idade_limite_anos", "creche.creche_idade_fim_incerteza_anos"]
    assert (cond["valor"], cond["valor_exclusao"]) == (3, 4)
    limite = parametros["creche_idade_limite_anos"]
    assert "art. 9.º, n.º 4" in limite["referencia_legal"] and "Portaria n.º 198/2022" in limite["referencia_legal"]
    assert limite["vigencia_inicio"] == "2022-09-01"
    derivado = parametros["creche_idade_fim_incerteza_anos"]["referencia_legal"]
    assert derivado.startswith("Derivado de:")
    for citacao in ("Portaria n.º 262/2011, art. 3.º", "anexo, ponto 4", "Portaria n.º 198/2022, art. 2.º, n.º 1",
                    "art. 9.º, n.º 4", "Nenhum diploma fixa os 4 anos como limite"):
        assert citacao in derivado, citacao


def test_fontes_da_creche_guardadas_em_dados_fontes():
    fontes = RAIZ / "dados" / "fontes"
    for nome in ("Lei-2-2022.pdf", "Portaria-198-2022-consolidada-2023-03-10.pdf",
                 "Portaria-305-2022-consolidada-2024-06-06.pdf", "Portaria-262-2011-consolidada-2023-12-11.pdf"):
        caminho = fontes / nome
        assert caminho.is_file() and caminho.read_bytes()[:5] == b"%PDF-", nome



# ── PR 12 (revisão 2): motivo_inelegivel ────────────────────────────────────


def test_motivo_inelegivel_passa_para_o_json(tmp_path, monkeypatch):
    cond = {"id": "c", "tipo": "categorica", "campo": "reside", "operador_comparacao": "eq",
            "valor_literal": "sim", "motivo_inelegivel": "  Texto próprio.  "}
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}},
              {"x": _apoio_min(condicoes=[cond])}, completar=False)
    assert gerar_condicoes_json.consolidar()["apoios"]["x"]["condicoes"][0]["motivo_inelegivel"] == "Texto próprio."


@pytest.mark.parametrize("motivo,em_grupo,erro", [
    ("", False, "texto não vazio"),
    (7, False, "texto não vazio"),
    ("Texto.", True, "não em grupos"),
])
def test_motivo_inelegivel_invalido_falha(tmp_path, monkeypatch, motivo, em_grupo, erro):
    folha = {"id": "c", "tipo": "categorica", "campo": "reside", "operador_comparacao": "eq", "valor_literal": "sim"}
    if em_grupo:
        cond = {"id": "g", "operador": "all", "condicoes": [folha], "motivo_inelegivel": motivo}
    else:
        cond = {**folha, "motivo_inelegivel": motivo}
    _preparar(tmp_path, monkeypatch, {"reside": _pergunta_reside()}, {"prestacoes": {}},
              {"x": _apoio_min(condicoes=[cond])}, completar=False)
    with pytest.raises(gerar_condicoes_json.CondicaoInvalida, match=erro):
        gerar_condicoes_json.consolidar()
