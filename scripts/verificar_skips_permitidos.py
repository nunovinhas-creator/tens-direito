#!/usr/bin/env python3
"""Guardrail: compara os testes "skipped" de uma corrida real do pytest
(relatório JUnit) contra tests/skips_permitidos.json por igualdade estrita
de conjuntos — nunca por contagem.

Substitui o antigo LIMIAR_SKIPPED (número mágico que já deixou `main`
vermelha duas vezes, 2026-07-05 e 2026-07-06, só por ninguém o ter
incrementado quando um skip legítimo novo aparecia). Uma contagem só vê a
direcção "subiu" — nunca detecta a direcção inversa, um skip esperado que
silenciosamente deixou de saltar (ex.: alguém corrigiu a condição que o
causava, ou apagou a página, sem que ninguém reparasse).

Duas direcções de falha, ambas reais:
1. Um nodeid saltou nesta corrida mas não está na allow-list — skip novo,
   não documentado (pode ser um binário/dependência em falta a impedir
   testes de correr, ou uma página nova sem carimbo/atribuição).
2. Um nodeid está na allow-list mas não saltou nesta corrida — o skip
   esperado deixou de acontecer (a página ganhou o que faltava, ou foi
   apagada/renomeada) e a entrada da allow-list ficou órfã.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).parent.parent
ALLOW_LIST = RAIZ / "tests" / "skips_permitidos.json"


def _nodeid(testcase: ET.Element) -> str:
    """Reconstrói o nodeid pytest (ex.: tests/test_x.py::test_y[param]) a
    partir de classname ("tests.test_x", pontos = separadores de path) e
    name (nome da função, com os parênteses rectos de parametrize já
    incluídos — nunca contêm pontos de separação de path, por isso nunca
    colidem com o replace abaixo, mesmo quando o próprio parâmetro tem
    pontos, ex.: "p/apoios-escolares.html")."""
    classname = testcase.get("classname", "")
    name = testcase.get("name", "")
    return classname.replace(".", "/") + ".py::" + name


def extrair_skips_reais(caminho_xml: str) -> dict[str, str]:
    """nodeid -> mensagem do skip, para todos os <skipped> do relatório."""
    tree = ET.parse(caminho_xml)
    skips = {}
    for testcase in tree.getroot().iter("testcase"):
        skipped = testcase.find("skipped")
        if skipped is not None:
            skips[_nodeid(testcase)] = skipped.get("message", "")
    return skips


def carregar_allow_list() -> dict:
    return json.loads(ALLOW_LIST.read_text(encoding="utf-8"))


def verificar(caminho_xml: str, allow_list: dict, skips_reais: dict) -> list[str]:
    """Devolve a lista de linhas de erro accionáveis; vazia = tudo bate certo."""
    erros = []

    nao_documentados = sorted(set(skips_reais) - set(allow_list))
    if nao_documentados:
        erros.append(
            f"{len(nao_documentados)} teste(s) saltados nesta corrida SEM entrada em "
            f"{ALLOW_LIST.relative_to(RAIZ)}:"
        )
        for nodeid in nao_documentados:
            erros.append(f"  - {nodeid!r} — motivo real: {skips_reais[nodeid]!r}")
        erros.append(
            "  Acção: investigar a causa (dependência/binário em falta a impedir o "
            "teste de correr, ou página nova sem carimbo/atribuição) antes de "
            "adicionar à allow-list. Só adicionar se for genuinamente estrutural."
        )

    deixaram_de_saltar = sorted(set(allow_list) - set(skips_reais))
    if deixaram_de_saltar:
        erros.append(
            f"{len(deixaram_de_saltar)} entrada(s) de {ALLOW_LIST.relative_to(RAIZ)} "
            f"já NÃO saltam nesta corrida:"
        )
        for nodeid in deixaram_de_saltar:
            info = allow_list[nodeid]
            erros.append(f"  - {nodeid!r} — motivo documentado: {info.get('motivo')!r}")
        erros.append(
            "  Acção: confirmar que o teste passa mesmo (não desapareceu por "
            "engano) e remover a entrada órfã da allow-list."
        )

    return erros


def main() -> int:
    caminho_xml = sys.argv[1] if len(sys.argv) > 1 else "report-testes.xml"
    allow_list = carregar_allow_list()
    skips_reais = extrair_skips_reais(caminho_xml)

    print(f"Skips reais nesta corrida: {len(skips_reais)}")
    print(f"Entradas na allow-list: {len(allow_list)}")

    erros = verificar(caminho_xml, allow_list, skips_reais)
    if erros:
        for linha in erros:
            print(f"::error::{linha}")
        return 1

    print("OK — skips reais e allow-list batem certo, conjunto por conjunto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
