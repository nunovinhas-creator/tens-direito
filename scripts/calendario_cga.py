#!/usr/bin/env python3
"""
Datas de pagamento das pensões da Caixa Geral de Aposentações (CGA).

Regra oficial, publicada pela própria CGA (https://www.cga.pt/pagamentos):
as pensões de aposentação, sobrevivência, preço de sangue, reforma, DFA,
invalidez, forças de segurança, subvenções vitalícias e pensões de
alimentos são pagas «no dia 19 de cada mês ou no dia útil anterior».
O 14.º mês é pago em julho e o subsídio de Natal em novembro, com a
pensão desse mês.

Ao contrário do calendário da Segurança Social (publicado mês a mês, sem
regra fixa — por isso raspado e guardado em data/calendario_pagamentos.json),
a data da CGA decorre inteiramente desta regra. É calculada aqui, nunca
guardada: dia 19, recuado para o último dia útil (segunda a sexta,
excepto feriados nacionais obrigatórios — scripts/feriados.py) quando
calha a fim de semana ou feriado.

A regra está trancada contra as 12 datas que a CGA publicou para 2026
(tests/test_calendario_cga.py). Se a CGA alguma vez se afastar da regra
num mês concreto, esse teste não o apanha — a revisão anual do calendário
publicado pela CGA (docs/FONTE-CALENDARIO.md) é o que o apanha.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feriados import util_ou_anterior  # noqa: E402

FONTE_URL = "https://www.cga.pt/pagamentos"
DIA_REFERENCIA = 19

# Âncora e nome na página do calendário (zona CAL:CORPO) e no .ics
# (calendario/pensoes-cga.ics). Nunca entra em PRESTACOES nem no JSON da
# Segurança Social: fonte, regra e validação são outras.
ANCORA = "pensoes-cga"
NOME = "Pensões da CGA (função pública)"
RESUMO_CURTO = "Pensões da CGA"
GUIA = "/caixa-geral-aposentacoes.html"

# Pagamentos extra que a CGA junta à pensão do mês (fonte: cga.pt/pagamentos).
EXTRA_POR_MES = {
    7: "inclui o 14.º mês",
    11: "inclui o subsídio de Natal",
}


def dia_pagamento(ano: int, mes: int) -> dt.date:
    """Data de pagamento das pensões da CGA no mês dado."""
    return util_ou_anterior(dt.date(ano, mes, DIA_REFERENCIA))


def proximas_datas(desde: dt.date, meses: int = 12) -> list[dt.date]:
    """Datas de pagamento de `desde` (inclusive) em diante, por ordem —
    `meses` meses a contar do mês de `desde`."""
    datas = []
    ano, mes = desde.year, desde.month
    for _ in range(meses):
        dia = dia_pagamento(ano, mes)
        if dia >= desde:
            datas.append(dia)
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return datas
