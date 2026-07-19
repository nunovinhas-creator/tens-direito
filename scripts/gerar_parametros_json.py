#!/usr/bin/env python3
"""
FASE 2 (sessão de dados abertos, 2026-07-19) — consolida
`dados/parametros/*.yaml` (padrão OpenFisca: parâmetros com vigência,
separados da lógica de cálculo — NÃO usa a biblioteca OpenFisca, só a
convenção) num único `dados/parametros.json`, consumido em runtime
pelos simuladores via `fetch()`.

Cada parâmetro tem uma lista `valores`, com `vigencia_inicio`/`valor`/
`referencia_legal`/`fonte_url`/`verificado_em` por entrada — este script
escolhe, para cada parâmetro, a entrada com a `vigencia_inicio` mais
recente que já começou (<= hoje).

PASSO 0 obrigatório, aplicado aqui como guarda dura: qualquer entrada
cuja vigência já tenha começado mas sem `verificado_em` preenchido faz
este script falhar — nunca publica um valor (`valor: 0.00` placeholder,
ou copiado sem confirmação) como se fosse dado real. Mesmo espírito de
`tests/test_valores_ancora.py`.

    python scripts/gerar_parametros_json.py            # escreve dados/parametros.json
    python scripts/gerar_parametros_json.py --check    # só valida (CI), nunca escreve
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PARAMETROS_DIR = RAIZ / "dados" / "parametros"
SAIDA_JSON = RAIZ / "dados" / "parametros.json"


class ParametroInvalido(Exception):
    pass


def _valor_vigente(nome_prestacao: str, nome_parametro: str, valores: list, hoje: date) -> dict:
    if not valores:
        raise ParametroInvalido(f"{nome_prestacao}.{nome_parametro}: 'valores' está vazio")

    candidatos = []
    for entrada in valores:
        vigencia = entrada.get("vigencia_inicio")
        if not vigencia:
            raise ParametroInvalido(f"{nome_prestacao}.{nome_parametro}: entrada sem 'vigencia_inicio'")
        try:
            vigencia_data = date.fromisoformat(str(vigencia))
        except ValueError as exc:
            raise ParametroInvalido(
                f"{nome_prestacao}.{nome_parametro}: 'vigencia_inicio' inválida ({vigencia!r}): {exc}"
            ) from exc

        # PASSO 0: qualquer entrada já em vigor tem de estar verificada por
        # humano — nunca publicar um placeholder (valor 0.00, fonte vazia)
        # como se fosse dado real só porque "está no YAML".
        if vigencia_data <= hoje and not entrada.get("verificado_em"):
            raise ParametroInvalido(
                f"{nome_prestacao}.{nome_parametro}: vigência {vigencia} já começou mas "
                "'verificado_em' está vazio — PASSO 0 não cumprido, nunca publicar sem "
                "verificação humana contra a fonte oficial."
            )
        if vigencia_data <= hoje and (not entrada.get("referencia_legal") or not entrada.get("fonte_url")):
            raise ParametroInvalido(
                f"{nome_prestacao}.{nome_parametro}: entrada com vigência {vigencia} sem "
                "'referencia_legal' ou 'fonte_url'"
            )
        if vigencia_data <= hoje:
            candidatos.append((vigencia_data, entrada))

    if not candidatos:
        raise ParametroInvalido(
            f"{nome_prestacao}.{nome_parametro}: nenhuma entrada com vigência já iniciada "
            f"(hoje={hoje.isoformat()}) — parâmetro sem valor vigente"
        )

    candidatos.sort(key=lambda par: par[0])
    return candidatos[-1][1]


def consolidar(hoje: Optional[date] = None) -> dict:
    hoje = hoje or date.today()
    prestacoes: dict[str, dict] = {}

    for ficheiro in sorted(PARAMETROS_DIR.glob("*.yaml")):
        prestacao = ficheiro.stem
        with open(ficheiro, encoding="utf-8") as f:
            bruto = yaml.safe_load(f) or {}

        parametros_prestacao = {}
        for nome_parametro, definicao in bruto.items():
            if not isinstance(definicao, dict) or "valores" not in definicao:
                raise ParametroInvalido(
                    f"{prestacao}.{nome_parametro}: formato inesperado — esperado objecto "
                    "com uma chave 'valores' (lista)"
                )
            vigente = _valor_vigente(prestacao, nome_parametro, definicao["valores"], hoje)
            parametros_prestacao[nome_parametro] = {
                "descricao": definicao.get("descricao", ""),
                "unidade": definicao.get("unidade", ""),
                "valor": vigente["valor"],
                "vigencia_inicio": str(vigente["vigencia_inicio"]),
                "referencia_legal": vigente["referencia_legal"],
                "fonte_url": vigente["fonte_url"],
                # Opcional — citação corroborante além do diploma legal
                # (ex.: um Guia Prático da Segurança Social). Nunca
                # substitui referencia_legal/fonte_url, que continuam a
                # ser sempre a fonte autoritativa.
                "fonte_url_complementar": vigente.get("fonte_url_complementar"),
                "verificado_em": str(vigente["verificado_em"]),
            }
        prestacoes[prestacao] = parametros_prestacao

    return {"gerado_em": hoje.isoformat(), "prestacoes": prestacoes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Só valida, nunca escreve dados/parametros.json")
    args = parser.parse_args()

    try:
        consolidado = consolidar()
    except ParametroInvalido as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    n_prestacoes = len(consolidado["prestacoes"])
    n_parametros = sum(len(p) for p in consolidado["prestacoes"].values())

    if args.check:
        # gerado_em varia todos os dias por desenho — comparar só o resto
        # do documento (prestacoes), nunca a data de geração.
        atual_sem_data = json.dumps({"prestacoes": consolidado["prestacoes"]}, sort_keys=True)
        if SAIDA_JSON.exists():
            disco = json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
            disco_sem_data = json.dumps({"prestacoes": disco.get("prestacoes", {})}, sort_keys=True)
        else:
            disco_sem_data = None
        if disco_sem_data == atual_sem_data:
            print(f"dados/parametros.json sincronizado — {n_prestacoes} prestação(ões), {n_parametros} parâmetro(s).")
            return 0
        print(
            "ERRO: dados/parametros.json diverge do que dados/parametros/*.yaml geraria "
            "— correr sem --check para regenerar.",
            file=sys.stderr,
        )
        return 1

    SAIDA_JSON.write_text(json.dumps(consolidado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dados/parametros.json escrito: {n_prestacoes} prestação(ões), {n_parametros} parâmetro(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
