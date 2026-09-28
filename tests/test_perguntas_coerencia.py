"""
Coerência de dados/condicoes/perguntas.yaml (PR 1 da série "condições de
acesso" — base do simulador universal). Nunca valida factos, só a forma:
cada pergunta tem o que o motor precisa para a gerar e validar sem
depender de convenção não escrita.
"""
import copy
from pathlib import Path

import yaml

RAIZ = Path(__file__).parent.parent
CONDICOES_DIR = RAIZ / "dados" / "condicoes"
PERGUNTAS_PATH = CONDICOES_DIR / "perguntas.yaml"

TIPOS_VALIDOS = {"categorica", "numero", "data"}


def _carregar():
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _carregar_apoios() -> dict:
    apoios = {}
    for ficheiro in sorted(CONDICOES_DIR.glob("*.yaml")):
        if ficheiro == PERGUNTAS_PATH:
            continue
        with open(ficheiro, encoding="utf-8") as f:
            bruto = yaml.safe_load(f)
        apoios[bruto["apoio"]] = bruto
    return apoios


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


# ── PR 11: o que simulador-universal.html precisa para mostrar cada pergunta ──


def test_toda_pergunta_tem_texto_para_o_utilizador():
    perguntas = _carregar()
    for campo, dados in perguntas.items():
        texto = dados.get("pergunta")
        assert isinstance(texto, str) and texto.strip(), f"{campo}: falta 'pergunta'"
        assert texto.strip().endswith("?"), f"{campo}: 'pergunta' deve ser uma pergunta ({texto!r})"
    assert "data_nascimento" not in perguntas, "campo genérico proibido — um por papel (requerente/criança)"
    assert {"data_nascimento_requerente", "data_nascimento_crianca"} <= set(perguntas)


# Guardrail 1 — rótulos: cada opção de uma pergunta categórica tem exactamente
# um rótulo não vazio (nem opção sem rótulo, que a página mostraria como nome
# de código cru, nem rótulo sem opção, que seria uma opção fantasma).
def _erros_rotulos(perguntas: dict) -> list[str]:
    erros = []
    for campo, dados in perguntas.items():
        rotulos = dados.get("rotulos")
        if dados.get("tipo") != "categorica":
            if rotulos is not None:
                erros.append(f"{campo}: 'rotulos' numa pergunta não categórica")
            continue
        if not isinstance(rotulos, dict):
            erros.append(f"{campo}: sem 'rotulos'")
            continue
        opcoes = dados.get("opcoes") or []
        if set(rotulos) != set(opcoes):
            erros.append(f"{campo}: rótulos {sorted(rotulos)} ≠ opções {sorted(opcoes)}")
        erros.extend(f"{campo}: rótulo vazio para {o!r}" for o, txt in rotulos.items() if not str(txt or "").strip())
    return erros


def test_guardrail_rotulos_batem_com_opcoes():
    assert _erros_rotulos(_carregar()) == []


def test_guardrail_rotulos_falha_quando_estragado():
    perguntas = copy.deepcopy(_carregar())
    categoricas = [c for c, d in perguntas.items() if d["tipo"] == "categorica"]
    del perguntas[categoricas[0]]["rotulos"][perguntas[categoricas[0]]["opcoes"][0]]  # opção sem rótulo
    perguntas[categoricas[1]]["rotulos"]["opcao_fantasma"] = "Fantasma"               # rótulo sem opção
    perguntas[categoricas[2]]["rotulos"][perguntas[categoricas[2]]["opcoes"][0]] = " "  # rótulo vazio
    numerica = next(c for c, d in perguntas.items() if d["tipo"] == "numero")
    perguntas[numerica]["rotulos"] = {"1": "um"}                                      # rótulos em número
    erros = _erros_rotulos(perguntas)
    assert len(erros) == 4, erros


# Guardrail 2 — portões: um apoio que use um campo com `aplicavel_se`
# {campo: X, valor: v} tem de ficar decidido quando X != v, senão a pergunta
# nunca é feita e o apoio fica eternamente em "falta saber" (foi o que
# motivou tem_filhos_a_cargo no abono/ASE e reside_legalmente_pt no RSI).
# O portão pode ser uma condição de topo `X eq v` (o apoio fica logo
# inelegível) ou, dentro do grupo `any` que contém o campo, uma alternativa
# `X neq v` (o grupo fica logo elegível).
def _eh_portao(cond: dict, campo: str, valor, operador: str) -> bool:
    return (
        "condicoes" not in cond
        and cond.get("campo") == campo
        and cond.get("operador_comparacao") == operador
        and cond.get("valor_literal") == valor
    )


def _campos_da_folha(cond: dict) -> list[str]:
    if cond.get("tipo") == "formula":
        return [v for k, v in cond.items() if k.startswith("campo_")]
    return [cond["campo"]]


def _erros_portoes(perguntas: dict, apoios: dict) -> list[str]:
    erros = []

    def visitar(cond, apoio, topo, grupo_any):
        if "condicoes" in cond:
            novo_any = cond["condicoes"] if cond["operador"] == "any" else grupo_any
            for sub in cond["condicoes"]:
                visitar(sub, apoio, topo, novo_any)
            return
        for campo in _campos_da_folha(cond):
            regra = perguntas.get(campo, {}).get("aplicavel_se")
            if not regra:
                continue
            x, v = regra["campo"], regra["valor"]
            no_topo = apoio["operador"] == "all" and any(_eh_portao(c, x, v, "eq") for c in topo)
            no_grupo = grupo_any is not None and any(_eh_portao(c, x, v, "neq") for c in grupo_any)
            if not (no_topo or no_grupo):
                erros.append(f"{apoio['apoio']}: usa '{campo}' (aplicavel_se {x} == {v}) sem portão em '{x}'")

    for apoio in apoios.values():
        for cond in apoio["condicoes"]:
            visitar(cond, apoio, apoio["condicoes"], None)
    return sorted(set(erros))


def test_guardrail_todo_apoio_tem_portao_para_campos_condicionais():
    assert _erros_portoes(_carregar(), _carregar_apoios()) == []


def test_guardrail_portoes_falha_quando_estragado():
    perguntas = _carregar()
    apoios = copy.deepcopy(_carregar_apoios())
    # Tirar o portão tem_filhos_a_cargo ao abono e o portão de residência ao RSI.
    apoios["abono"]["condicoes"] = [c for c in apoios["abono"]["condicoes"] if c["id"] != "tem_filhos_a_cargo"]
    apoios["rsi"]["condicoes"] = [c for c in apoios["rsi"]["condicoes"] if c["id"] != "reside_legalmente"]
    erros = _erros_portoes(perguntas, apoios)
    assert any(e.startswith("abono:") and "tem_filhos_a_cargo" in e for e in erros), erros
    assert any(e.startswith("rsi:") and "reside_legalmente_pt" in e for e in erros), erros
    # E a alternativa `neq` num grupo any também conta: sem ela, o RSI deixa de
    # ter portão para inscrito_centro_emprego_e_disponivel.
    apoios = copy.deepcopy(_carregar_apoios())
    grupo = next(c for c in apoios["rsi"]["condicoes"] if c["id"] == "disponibilidade_se_desempregado")
    grupo["condicoes"] = [c for c in grupo["condicoes"] if c["id"] != "nao_desempregado"]
    assert any("inscrito_centro_emprego_e_disponivel" in e for e in _erros_portoes(perguntas, apoios))
