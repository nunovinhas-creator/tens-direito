#!/usr/bin/env python3
"""Actualiza a data de "Última revisão automática" no HISTORICO.md.

Substitui a linha existente em vez de acrescentar uma nova. A versão
anterior decidia se a linha já existia comparando o texto antes/depois de
`re.sub()`: se a substituição desse origem a um texto igual ao original,
concluía "a linha não existe, acrescenta uma nova". Isso é verdade quando
o padrão não é encontrado — mas também quando É encontrado e a data já é
a mesma (o pipeline a correr mais que uma vez no mesmo dia), caso em que
`re.sub()` também produz um texto idêntico. Resultado: uma linha nova
duplicada sempre que o pipeline corria mais do que uma vez no mesmo dia.

Escreve em `HISTORICO.md` desde a Fase 1 da separação histórico/
referência (2026-09-13) — antes escrevia directamente no CLAUDE.md, mas
o histórico de sessões ("Última revisão: ...") mudou-se todo para
`HISTORICO.md`, incluindo este carimbo automático.
"""
import re
from datetime import datetime, timezone

PADRAO = re.compile(r"Última revisão automática: \d{4}-\d{2}-\d{2}")


def actualizar_revisao(conteudo, data):
    """Devolve o novo conteúdo do HISTORICO.md com a data de revisão actualizada."""
    if PADRAO.search(conteudo):
        return PADRAO.sub(f"Última revisão automática: {data}", conteudo)
    return conteudo.rstrip() + f"\n\n---\n\n*Última revisão automática: {data}*\n"


def main():
    data = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open("HISTORICO.md", encoding="utf-8") as f:
        conteudo = f.read()

    novo = actualizar_revisao(conteudo, data)

    if novo != conteudo:
        with open("HISTORICO.md", "w", encoding="utf-8") as f:
            f.write(novo)
        print(f"HISTORICO.md actualizado: {data}")
    else:
        print("HISTORICO.md sem alterações.")


if __name__ == "__main__":
    main()
