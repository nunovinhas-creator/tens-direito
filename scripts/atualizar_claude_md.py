#!/usr/bin/env python3
"""Actualiza a data de "Última revisão automática" no HISTORICO.md.

Move sempre o carimbo para o FIM do ficheiro — nunca o actualiza no lugar
onde estiver. A versão anterior fazia `PADRAO.sub()` sobre o ficheiro
inteiro: se o carimbo já existisse (em qualquer posição), só lhe trocava a
data ali mesmo. Isso enterrou o carimbo a meio da cadeia de sessões: a
migração da Fase 1 (separação histórico/referência, 2026-09-13) trouxe
para `HISTORICO.md` uma ocorrência do carimbo que já estava mal colocada
no `CLAUDE.md` antigo (perto do início, não no fim) e cada corrida
seguinte do pipeline só lhe actualizava a data sem nunca a mover — o
carimbo ficava cada vez mais "enterrado" à medida que sessões novas
acrescentavam entradas reais ao fim do ficheiro.

Antes disso, uma versão ainda mais antiga decidia se o carimbo já existia
comparando o texto antes/depois de `re.sub()`: se a substituição desse
origem a um texto igual ao original, concluía "a linha não existe,
acrescenta uma nova" — verdade quando o padrão não é encontrado, mas
também quando É encontrado e a data já é a mesma (pipeline a correr mais
que uma vez no mesmo dia), o que duplicava a linha.

Escreve em `HISTORICO.md` desde a Fase 1 da separação histórico/
referência (2026-09-13) — antes escrevia directamente no CLAUDE.md, mas
o histórico de sessões ("Última revisão: ...") mudou-se todo para
`HISTORICO.md`, incluindo este carimbo automático.
"""
import re
from datetime import datetime, timezone

PADRAO_CARIMBO = r"\*Última revisão automática: \d{4}-\d{2}-\d{2}\*"
# Remove o carimbo antigo esteja onde estiver: bracketed por "---" dos dois
# lados (caso do meio da cadeia) ou só à esquerda (caso já esteja no fim,
# sem mais nenhuma entrada depois) — os dois casos colapsam para o mesmo
# separador único que já lá estava antes do carimbo ter sido inserido.
_BLOCO_MEIO = re.compile(PADRAO_CARIMBO + r"\n\n---\n\n")
_BLOCO_FIM = re.compile(r"\n\n---\n\n" + PADRAO_CARIMBO + r"\n*$")


def actualizar_revisao(conteudo, data):
    """Devolve o novo conteúdo do HISTORICO.md com o carimbo "Última revisão
    automática" movido para o fim do ficheiro — nunca actualizado no lugar
    onde já estiver, para nunca ficar enterrado a meio da cadeia de sessões."""
    sem_carimbo = _BLOCO_MEIO.sub("", conteudo)
    sem_carimbo = _BLOCO_FIM.sub("", sem_carimbo)

    novo = sem_carimbo.rstrip("\n") + f"\n\n---\n\n*Última revisão automática: {data}*\n"

    if novo == conteudo:
        return conteudo
    return novo


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
