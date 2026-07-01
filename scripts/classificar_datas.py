"""
CAMADA 2 — Classificação de datas (TENS DIREITO, deteção de datas expiradas).

Introduz um estado intermédio entre "correspondência de data encontrada"
(scripts/verificar_datas.py) e "Issue criada" (pipeline-diario.yml). Cada
correspondência passa a ser classificada num de 5 estados, anexado ao
alerta como metadado extra (`alerta["classificacao"]`).

Este módulo NÃO decide ainda se uma Issue é criada — essa decisão
mantém-se inteiramente em `verificar_datas.detectar_alertas`/
`_pagina_tem_alerta`. É apenas uma camada informativa, adicionada para
preparar uma futura distinção entre correcção automática, revisão
humana, referência estática e fonte bloqueada.

Heurísticas por palavras-chave do contexto envolvente, sem ML e sem
dependências novas:
- referência legal/histórica (portaria, decreto-lei, despacho, "em vigor
  desde", "desde <ano>") — nunca expira -> STATIC_REFERENCE
- aviso explícito de conteúdo pendente (aguarda, previsto, provisório,
  confirmar, estimado, "deverá ser", "após publicação") — a fonte oficial
  ainda não publicou -> BLOCKED_SOURCE
- ano mais recente encontrado (em `data` ou em `contexto`) já é actual ou
  futuro -> OK
- ano expirado associado a um valor com correspondência directa no
  scraper (IAS, indexante, salário mínimo, valor de referência) —
  substituição mecânica de um número -> OUTDATED_AUTOFIXABLE
- qualquer outro ano expirado (prazos, calendários, texto livre) —
  precisa de reescrita/verificação humana -> OUTDATED_REVIEW_REQUIRED

Os marcadores de STATIC_REFERENCE/BLOCKED_SOURCE espelham deliberadamente
os de `verificar_datas.MARCADORES_HISTORICOS`/`MARCADORES_PENDENTE`, para
que as duas camadas concordem sobre o que conta como referência
permanente ou conteúdo pendente.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class EstadoData(str, Enum):
    OK = "OK"
    OUTDATED_AUTOFIXABLE = "OUTDATED_AUTOFIXABLE"
    OUTDATED_REVIEW_REQUIRED = "OUTDATED_REVIEW_REQUIRED"
    STATIC_REFERENCE = "STATIC_REFERENCE"
    BLOCKED_SOURCE = "BLOCKED_SOURCE"


_MARCADORES_HISTORICOS = [
    r"portaria", r"decreto-lei", r"decreto\s+lei", r"despacho", r"\bdl\s*n",
    r"lei\s+n\.?º", r"diário da república", r"dre\.pt", r"em vigor desde",
    r"já\s+benefici", r"\bdesde\s+\d",
]

_MARCADORES_PENDENTE = [
    r"aguarda", r"previst", r"provis[oó]ri", r"\bconfirmar\b", r"estimad",
    r"deverá ser", r"após publicação",
]

_MARCADORES_AUTOFIXAVEL = [
    r"\bias\b", r"indexante", r"salário mínimo", r"salario minimo",
    r"valor de referência", r"valor de referencia", r"\bmontante\b",
]

_REGEX_ANO = re.compile(r"\b(?:19|20)\d{2}\b")


def _anos_encontrados(*textos: str) -> list:
    anos = []
    for texto in textos:
        anos.extend(int(m.group(0)) for m in _REGEX_ANO.finditer(texto or ""))
    return anos


def _tem_algum(padroes, texto: str) -> bool:
    return any(re.search(p, texto, re.IGNORECASE) for p in padroes)


def classificar_data(contexto: str, data: str, *, ano_atual: Optional[int] = None) -> str:
    """Classifica uma correspondência de data/valor num dos 5 estados de
    `EstadoData`, usando só heurísticas de texto — sem ML.

    `ano_atual` é opcional e usa o ano corrente por omissão; passar um
    valor fixo torna o resultado determinístico independentemente do dia
    em que os testes correm.
    """
    ano_atual = ano_atual if ano_atual is not None else datetime.now().year
    texto_completo = f"{data} {contexto}"

    if _tem_algum(_MARCADORES_HISTORICOS, texto_completo):
        return EstadoData.STATIC_REFERENCE.value

    if _tem_algum(_MARCADORES_PENDENTE, texto_completo):
        return EstadoData.BLOCKED_SOURCE.value

    anos = _anos_encontrados(data, contexto)
    if not anos or max(anos) >= ano_atual:
        return EstadoData.OK.value

    if _tem_algum(_MARCADORES_AUTOFIXAVEL, texto_completo):
        return EstadoData.OUTDATED_AUTOFIXABLE.value

    return EstadoData.OUTDATED_REVIEW_REQUIRED.value


@dataclass(frozen=True)
class ClassificacaoData:
    data: str
    estado: str
    contexto: str

    def as_dict(self) -> dict:
        return {"data": self.data, "estado": self.estado, "contexto": self.contexto}


def classificar_data_estruturada(contexto: str, data: str, *, ano_atual: Optional[int] = None) -> dict:
    """Camada intermédia pedida: devolve `{"data", "estado", "contexto"}`
    sem tomar qualquer decisão sobre criação de Issues."""
    estado = classificar_data(contexto, data, ano_atual=ano_atual)
    return ClassificacaoData(data=data, estado=estado, contexto=contexto).as_dict()
