"""
CAMADA 5 — Orquestrador (TENS DIREITO, deteção de datas expiradas).

Ponto único de controlo de execução do sistema. Recebe um `alerta` já
classificado (Camada 2, `classificar_datas.py`) e decidido (Camada 3,
`decisao_datas.py`), aplica as regras finais de segurança e devolve a
ação REALMENTE executada.

Fronteira de responsabilidade:
- Este módulo é o ÚNICO ponto do sistema autorizado a chamar
  `auto_update_engine.aplicar_auto_update`. Nenhum outro módulo o deve
  fazer — ver o teste de regressão
  `tests/test_orquestrador_datas.py::test_apenas_orquestrador_chama_auto_update_engine`,
  que varre todo o `scripts/` à procura de outras chamadas.
- Não reimplementa classificação nem decisão — usa sempre o que já vem
  em `alerta["classificacao"]` e `alerta["decisao"]` (Camadas 2 e 3).
  Não adiciona scraping, não toca em CI/CD, não escreve ficheiros.

Regras de segurança (por ordem de aplicação):
1. AUTO_UPDATE só é sequer TENTADO se TODAS forem verdade:
   - `alerta["decisao"]["acao"] == "AUTO_UPDATE"`
   - `decisao_datas.AUTO_UPDATE_HABILITADO is True` — verificado
     directamente no módulo (não uma cópia importada por valor), tal
     como já faz `auto_update_engine.py`, para nunca confiar cegamente
     em nenhuma camada anterior ter aplicado a guarda correctamente
   - `alerta["novo_valor"]` existe e não é vazio
   - `alerta["classificacao"]["estado"]` NÃO é `STATIC_REFERENCE` nem
     `BLOCKED_SOURCE` — mesmo que, por um bug futuro nas Camadas 2/3, a
     decisão tivesse chegado como `AUTO_UPDATE` para um destes estados
   Falhando qualquer uma, o AUTO_UPDATE nunca chega a ser tentado —
   `auto_update_engine.aplicar_auto_update` nem sequer é chamado.
2. Verificadas as condições, chama `auto_update_engine.aplicar_auto_update`:
   - resultado `AUTO_UPDATE_APPLIED` -> `acao_executada = AUTO_UPDATE`
   - qualquer outro resultado do engine (`SKIPPED_*`/`ABORTED_*`/
     `ROLLED_BACK`) -> fallback obrigatório: `acao_executada =
     CREATE_ISSUE` (o conteúdo continua desactualizado; precisa de
     revisão humana em vez de ficar silenciosamente por resolver).
3. Falha-segura global: qualquer excepção NÃO PREVISTA em qualquer ponto
   de `processar_alerta` (incluindo dentro do próprio engine, mesmo que
   este garanta não as lançar) é apanhada e nunca propagada para o
   chamador — o fallback é sempre `LOG_ONLY`, nunca `AUTO_UPDATE` e
   nunca um crash. Isto é deliberadamente diferente do fallback da
   regra 2: uma recusa CONTROLADA do engine implica que o conteúdo
   precisa de revisão (`CREATE_ISSUE`); um erro INESPERADO implica que
   não se sabe em que estado o sistema ficou, por isso o mais seguro é
   não fazer mais nada além de registar (`LOG_ONLY`).
4. Acções desconhecidas/inesperadas em `decisao["acao"]` (nem IGNORAR,
   nem LOG_ONLY, nem CREATE_ISSUE, nem AUTO_UPDATE) têm o mesmo default
   seguro: `LOG_ONLY` — "em caso de dúvida, LOG_ONLY".
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import auto_update_engine
import decisao_datas
from auto_update_engine import AcaoAutoUpdate
from classificar_datas import EstadoData
from decisao_datas import Acao

_ACOES_PASSAGEM_DIRETA = {Acao.IGNORAR, Acao.LOG_ONLY, Acao.CREATE_ISSUE}
_ESTADOS_NUNCA_AUTOFIXAVEIS = {
    EstadoData.STATIC_REFERENCE.value,
    EstadoData.BLOCKED_SOURCE.value,
}


def _agora(agora: Optional[str]) -> str:
    return agora if agora is not None else datetime.now(timezone.utc).isoformat()


def _resultado(estado, acao_pretendida, acao_executada, motivo, timestamp, **extra) -> dict:
    resultado = {
        "estado": estado,
        "acao_pretendida": acao_pretendida,
        "acao_executada": acao_executada,
        "motivo": motivo,
        "timestamp": timestamp,
    }
    resultado.update(extra)
    return resultado


def _verificar_elegibilidade_auto_update(alerta: dict, estado: str):
    """Devolve `(elegivel, motivo_recusa)`. As quatro condições
    obrigatórias são verificadas por ordem; a primeira que falhar já
    chega para recusar — nenhuma delas é dispensável."""
    decisao = alerta.get("decisao") or {}

    if decisao.get("acao") != Acao.AUTO_UPDATE:
        return False, "decisão não é AUTO_UPDATE"

    if decisao_datas.AUTO_UPDATE_HABILITADO is not True:
        return False, "AUTO_UPDATE_HABILITADO está desligado"

    if not alerta.get("novo_valor"):
        return False, "alerta sem novo_valor"

    if estado in _ESTADOS_NUNCA_AUTOFIXAVEIS:
        return False, f"estado {estado} nunca é elegível para auto-update"

    return True, None


def processar_alerta(alerta: dict, *, agora: Optional[str] = None) -> dict:
    """Único ponto de controlo de execução do sistema.

    Devolve sempre um dict com `estado`/`acao_pretendida`/
    `acao_executada`/`motivo`/`timestamp` — nunca lança excepção para o
    chamador, e é o único sítio do código de produção que pode invocar
    `auto_update_engine.aplicar_auto_update`.
    """
    timestamp = _agora(agora)
    estado = "DESCONHECIDO"
    acao_pretendida = Acao.IGNORAR

    try:
        alerta = alerta or {}
        decisao = alerta.get("decisao") or {}
        classificacao = alerta.get("classificacao") or {}
        estado = classificacao.get("estado") or decisao.get("estado") or "DESCONHECIDO"
        acao_pretendida = decisao.get("acao") or Acao.IGNORAR

        if acao_pretendida == Acao.AUTO_UPDATE:
            elegivel, motivo_recusa = _verificar_elegibilidade_auto_update(alerta, estado)
            if not elegivel:
                return _resultado(
                    estado, acao_pretendida, Acao.CREATE_ISSUE,
                    f"AUTO_UPDATE não elegível ({motivo_recusa}) — a criar "
                    f"Issue para revisão humana",
                    timestamp,
                )

            resultado_engine = auto_update_engine.aplicar_auto_update(alerta, agora=timestamp)
            if resultado_engine.get("acao") == AcaoAutoUpdate.AUTO_UPDATE_APPLIED:
                return _resultado(
                    estado, acao_pretendida, Acao.AUTO_UPDATE,
                    "AUTO_UPDATE aplicado com sucesso pelo auto_update_engine",
                    timestamp, resultado_engine=resultado_engine,
                )

            return _resultado(
                estado, acao_pretendida, Acao.CREATE_ISSUE,
                f"AUTO_UPDATE falhou no engine "
                f"({resultado_engine.get('acao')}) — a criar Issue para "
                f"revisão humana",
                timestamp, resultado_engine=resultado_engine,
            )

        if acao_pretendida in _ACOES_PASSAGEM_DIRETA:
            return _resultado(
                estado, acao_pretendida, acao_pretendida,
                "Ação executada conforme decisão prévia (Camada 3)",
                timestamp,
            )

        return _resultado(
            estado, acao_pretendida, Acao.LOG_ONLY,
            f"Ação pretendida desconhecida ('{acao_pretendida}') — "
            f"default seguro LOG_ONLY",
            timestamp,
        )

    except Exception as e:
        return _resultado(
            estado, acao_pretendida, Acao.LOG_ONLY,
            f"Erro inesperado no orquestrador — fail-safe para LOG_ONLY: {e}",
            timestamp,
        )
