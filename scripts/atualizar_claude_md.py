#!/usr/bin/env python3
"""Actualiza a data de "Última revisão automática" no CLAUDE.md.

Substitui a linha existente em vez de acrescentar uma nova. A versão
anterior decidia se a linha já existia comparando o texto antes/depois de
`re.sub()`: se a substituição desse origem a um texto igual ao original,
concluía "a linha não existe, acrescenta uma nova". Isso é verdade quando
o padrão não é encontrado — mas também quando É encontrado e a data já é
a mesma (o pipeline a correr mais que uma vez no mesmo dia), caso em que
`re.sub()` também produz um texto idêntico. Resultado: uma linha nova
duplicada sempre que o pipeline corria mais do que uma vez no mesmo dia.
"""
import re
from datetime import datetime, timezone

PADRAO = re.compile(r"Última revisão automática: \d{4}-\d{2}-\d{2}")


def actualizar_revisao(conteudo, data):
    """Devolve o novo conteúdo do CLAUDE.md com a data de revisão actualizada."""
    if PADRAO.search(conteudo):
        return PADRAO.sub(f"Última revisão automática: {data}", conteudo)
    return conteudo.rstrip() + f"\n\n---\n\n*Última revisão automática: {data}*\n"


def main():
    data = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open("CLAUDE.md", encoding="utf-8") as f:
        conteudo = f.read()

    novo = actualizar_revisao(conteudo, data)

    if novo != conteudo:
        with open("CLAUDE.md", "w", encoding="utf-8") as f:
            f.write(novo)
        print(f"CLAUDE.md actualizado: {data}")
    else:
        print("CLAUDE.md sem alterações.")


if __name__ == "__main__":
    main()
