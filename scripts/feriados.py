#!/usr/bin/env python3
"""
Feriados nacionais obrigatórios e dias úteis — partilhado.

Usado pelo aviso de véspera do canal (scripts/preparar_canal.py) e pelas
datas de pagamento da CGA (scripts/calendario_cga.py). Vive num módulo
próprio para nenhum dos dois ter de importar o outro: preparar_canal.py já
importa atualizar_calendario.py, que por sua vez precisa da CGA.

"Dia útil" = segunda a sexta, excepto os feriados obrigatórios do artigo
234.º, n.º 1, do Código do Trabalho. Os feriados municipais e a
Terça-feira de Carnaval (facultativos) não contam.
"""
from __future__ import annotations

import datetime as dt


def _domingo_de_pascoa(ano: int) -> dt.date:
    # Algoritmo anónimo gregoriano (Meeus/Jones/Butcher).
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    ll = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ll) // 451
    mes, dia = divmod(h + ll - 7 * m + 114, 31)
    return dt.date(ano, mes, dia + 1)


def feriados_nacionais(ano: int) -> set[dt.date]:
    """Feriados obrigatórios — artigo 234.º, n.º 1, do Código do Trabalho."""
    pascoa = _domingo_de_pascoa(ano)
    fixos = [(1, 1), (4, 25), (5, 1), (6, 10), (8, 15), (10, 5), (11, 1),
             (12, 1), (12, 8), (12, 25)]
    return {dt.date(ano, m, d) for m, d in fixos} | {
        pascoa - dt.timedelta(days=2),   # Sexta-Feira Santa
        pascoa,                          # Domingo de Páscoa
        pascoa + dt.timedelta(days=60),  # Corpo de Deus
    }


def e_dia_util(dia: dt.date) -> bool:
    return dia.weekday() < 5 and dia not in feriados_nacionais(dia.year)


def vespera_util(dia: dt.date) -> dt.date:
    """Último dia útil estritamente anterior a `dia`."""
    anterior = dia - dt.timedelta(days=1)
    while not e_dia_util(anterior):
        anterior -= dt.timedelta(days=1)
    return anterior


def util_ou_anterior(dia: dt.date) -> dt.date:
    """`dia` se for útil; senão, o último dia útil antes dele."""
    return dia if e_dia_util(dia) else vespera_util(dia)
