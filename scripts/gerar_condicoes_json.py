#!/usr/bin/env python3
"""
Consolida dados/condicoes/perguntas.yaml + dados/condicoes/<apoio>.yaml num
único dados/condicoes.json, consumido em runtime pelo motor de avaliação
(assets/js/motor-condicoes.js, PR 3) — mesmo padrão de
scripts/gerar_parametros_json.py: regra separada do valor, script falha em
vez de publicar uma referência que não existe.

Cada condição de dados/condicoes/<apoio>.yaml tem exactamente UMA fonte de
valor:
  - `parametro: <prestacao>.<nome>` — resolvido contra dados/parametros.json
    já gerado (falha se a prestação/parâmetro não existir lá);
  - `valor_literal: ...` — só aceite em condições `tipo: limiar` se vier
    acompanhado de `fonte_pagina:` (nunca um número sem proveniência), ou em
    condições `tipo: categorica` se o valor for uma das `opcoes` do campo em
    perguntas.yaml.

    python scripts/gerar_condicoes_json.py            # escreve dados/condicoes.json
    python scripts/gerar_condicoes_json.py --check     # só valida (CI), nunca escreve
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONDICOES_DIR = RAIZ / "dados" / "condicoes"
PERGUNTAS_PATH = CONDICOES_DIR / "perguntas.yaml"
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
SAIDA_JSON = RAIZ / "dados" / "condicoes.json"

TIPOS_VALIDOS = {"categorica", "numero", "data"}
TIPOS_CONDICAO_VALIDOS = {"categorica", "limiar"}
OPERADORES_APOIO_VALIDOS = {"all", "any"}
OPERADORES_COMPARACAO_VALIDOS = {"eq", "neq", "gte", "lte", "gt", "lt"}


class CondicaoInvalida(Exception):
    pass


def _carregar_perguntas() -> dict:
    if not PERGUNTAS_PATH.exists():
        raise CondicaoInvalida(f"{PERGUNTAS_PATH} não existe — corre o PR 1 primeiro")
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        perguntas = yaml.safe_load(f) or {}
    for campo, dados in perguntas.items():
        if dados.get("tipo") not in TIPOS_VALIDOS:
            raise CondicaoInvalida(f"perguntas.yaml: '{campo}' com tipo inválido")
    return perguntas


def _carregar_parametros() -> dict:
    if not PARAMETROS_JSON.exists():
        raise CondicaoInvalida(
            f"{PARAMETROS_JSON} não existe — corre scripts/gerar_parametros_json.py primeiro"
        )
    with open(PARAMETROS_JSON, encoding="utf-8") as f:
        return json.load(f)


def _resolver_parametro(referencia: str, parametros: dict, contexto: str) -> float:
    if "." not in referencia:
        raise CondicaoInvalida(f"{contexto}: 'parametro' tem de ser '<prestacao>.<nome>', veio '{referencia}'")
    prestacao, nome = referencia.split(".", 1)
    prestacoes = parametros.get("prestacoes", {})
    if prestacao not in prestacoes:
        raise CondicaoInvalida(f"{contexto}: prestação '{prestacao}' não existe em dados/parametros.json")
    if nome not in prestacoes[prestacao]:
        raise CondicaoInvalida(
            f"{contexto}: parâmetro '{nome}' não existe em dados/parametros.json → prestacoes.{prestacao}"
        )
    return prestacoes[prestacao][nome]["valor"]


def _validar_e_resolver_condicao(condicao: dict, apoio: str, perguntas: dict, parametros: dict) -> dict:
    contexto = f"{apoio}.{condicao.get('id', '<sem id>')}"

    if "id" not in condicao:
        raise CondicaoInvalida(f"{apoio}: condição sem 'id'")
    if condicao.get("tipo") not in TIPOS_CONDICAO_VALIDOS:
        raise CondicaoInvalida(f"{contexto}: 'tipo' tem de ser um de {sorted(TIPOS_CONDICAO_VALIDOS)}")

    campo = condicao.get("campo")
    if campo not in perguntas:
        raise CondicaoInvalida(f"{contexto}: campo '{campo}' não existe em perguntas.yaml")

    op = condicao.get("operador_comparacao")
    if op not in OPERADORES_COMPARACAO_VALIDOS:
        raise CondicaoInvalida(f"{contexto}: 'operador_comparacao' inválido ({op!r})")

    tem_parametro = "parametro" in condicao
    tem_literal = "valor_literal" in condicao
    if tem_parametro == tem_literal:
        raise CondicaoInvalida(f"{contexto}: tem de ter exactamente um de 'parametro' ou 'valor_literal'")

    if tem_parametro:
        valor = _resolver_parametro(condicao["parametro"], parametros, contexto)
        fonte = {"tipo": "parametro", "referencia": condicao["parametro"]}
    else:
        valor = condicao["valor_literal"]
        if condicao["tipo"] == "limiar":
            if not condicao.get("fonte_pagina"):
                raise CondicaoInvalida(
                    f"{contexto}: 'valor_literal' numa condição 'limiar' exige 'fonte_pagina' "
                    "— nunca publicar um número sem proveniência"
                )
            fonte = {"tipo": "literal_pagina", "pagina": condicao["fonte_pagina"]}
        else:  # categorica
            opcoes_campo = perguntas[campo].get("opcoes", [])
            if valor not in opcoes_campo:
                raise CondicaoInvalida(
                    f"{contexto}: valor_literal {valor!r} não é uma opção válida de '{campo}' "
                    f"({opcoes_campo})"
                )
            fonte = {"tipo": "literal_enum"}

    return {
        "id": condicao["id"],
        "tipo": condicao["tipo"],
        "campo": campo,
        "operador_comparacao": op,
        "valor": valor,
        "unidade_comparacao": condicao.get("unidade_comparacao"),
        "fonte": fonte,
    }


def consolidar() -> dict:
    perguntas = _carregar_perguntas()
    parametros = _carregar_parametros()

    apoios: dict[str, dict] = {}
    for ficheiro in sorted(CONDICOES_DIR.glob("*.yaml")):
        if ficheiro == PERGUNTAS_PATH:
            continue
        with open(ficheiro, encoding="utf-8") as f:
            bruto = yaml.safe_load(f) or {}

        apoio = bruto.get("apoio")
        if not apoio:
            raise CondicaoInvalida(f"{ficheiro.name}: falta a chave 'apoio'")
        if bruto.get("operador") not in OPERADORES_APOIO_VALIDOS:
            raise CondicaoInvalida(f"{apoio}: 'operador' tem de ser um de {sorted(OPERADORES_APOIO_VALIDOS)}")

        condicoes_resolvidas = [
            _validar_e_resolver_condicao(c, apoio, perguntas, parametros) for c in bruto.get("condicoes", [])
        ]
        if not condicoes_resolvidas:
            raise CondicaoInvalida(f"{apoio}: 'condicoes' está vazio")

        ids = [c["id"] for c in condicoes_resolvidas]
        if len(ids) != len(set(ids)):
            raise CondicaoInvalida(f"{apoio}: ids de condição duplicados ({ids})")

        apoios[apoio] = {
            "pagina": bruto.get("pagina"),
            "operador": bruto["operador"],
            "condicoes": condicoes_resolvidas,
        }

    return {"gerado_em": date.today().isoformat(), "perguntas": perguntas, "apoios": apoios}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Só valida, nunca escreve dados/condicoes.json")
    args = parser.parse_args()

    try:
        consolidado = consolidar()
    except CondicaoInvalida as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    n_apoios = len(consolidado["apoios"])
    n_condicoes = sum(len(a["condicoes"]) for a in consolidado["apoios"].values())

    if args.check:
        atual_sem_data = json.dumps(
            {"perguntas": consolidado["perguntas"], "apoios": consolidado["apoios"]}, sort_keys=True
        )
        if SAIDA_JSON.exists():
            disco = json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
            disco_sem_data = json.dumps(
                {"perguntas": disco.get("perguntas", {}), "apoios": disco.get("apoios", {})}, sort_keys=True
            )
        else:
            disco_sem_data = None
        if disco_sem_data == atual_sem_data:
            print(f"dados/condicoes.json sincronizado — {n_apoios} apoio(s), {n_condicoes} condição(ões).")
            return 0
        print(
            "ERRO: dados/condicoes.json diverge do que dados/condicoes/*.yaml geraria "
            "— correr sem --check para regenerar.",
            file=sys.stderr,
        )
        return 1

    SAIDA_JSON.write_text(json.dumps(consolidado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dados/condicoes.json escrito: {n_apoios} apoio(s), {n_condicoes} condição(ões).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
