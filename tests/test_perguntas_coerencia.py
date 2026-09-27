"""
Coerência de dados/condicoes/perguntas.yaml (PR 1 da série "condições de
acesso" — base do simulador universal). Nunca valida factos, só a forma:
cada pergunta tem o que o motor precisa para a gerar e validar sem
depender de convenção não escrita.
"""
from pathlib import Path

import yaml

RAIZ = Path(__file__).parent.parent
PERGUNTAS_PATH = RAIZ / "dados" / "condicoes" / "perguntas.yaml"

TIPOS_VALIDOS = {"categorica", "numero", "data"}


def _carregar():
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_ficheiro_existe_e_nao_esta_vazio():
    assert PERGUNTAS_PATH.exists()
    perguntas = _carregar()
    assert perguntas, "perguntas.yaml não pode ficar vazio"


def test_toda_pergunta_tem_descricao_e_tipo_valido():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        assert "descricao" in dados, f"{campo}: falta 'descricao'"
        assert dados.get("tipo") in TIPOS_VALIDOS, (
            f"{campo}: tipo '{dados.get('tipo')}' inválido — "
            f"tem de ser um de {sorted(TIPOS_VALIDOS)}"
        )


def test_categorica_tem_opcoes_nao_vazias():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        if dados["tipo"] == "categorica":
            opcoes = dados.get("opcoes")
            assert opcoes, f"{campo}: tipo 'categorica' sem 'opcoes'"
            assert len(opcoes) == len(set(opcoes)), f"{campo}: 'opcoes' com duplicados"


def test_numero_tem_unidade():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        if dados["tipo"] == "numero":
            assert dados.get("unidade"), f"{campo}: tipo 'numero' sem 'unidade'"


def test_aplicavel_se_aponta_para_campo_existente_e_valor_valido():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        cond = dados.get("aplicavel_se")
        if cond is None:
            continue
        campo_referenciado = cond.get("campo")
        assert campo_referenciado in perguntas, (
            f"{campo}: 'aplicavel_se' referencia campo inexistente '{campo_referenciado}'"
        )
        pergunta_referenciada = perguntas[campo_referenciado]
        if pergunta_referenciada["tipo"] == "categorica":
            assert cond.get("valor") in pergunta_referenciada["opcoes"], (
                f"{campo}: 'aplicavel_se.valor' ({cond.get('valor')!r}) não é uma opção "
                f"válida de '{campo_referenciado}'"
            )


def test_nenhum_campo_referencia_a_si_proprio_em_aplicavel_se():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        cond = dados.get("aplicavel_se")
        if cond is not None:
            assert cond.get("campo") != campo, f"{campo}: 'aplicavel_se' não pode referenciar-se a si próprio"
