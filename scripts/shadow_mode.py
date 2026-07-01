"""
Shadow Mode — ferramenta de validação (TENS DIREITO, deteção de datas
expiradas).

Corre toda a cadeia de decisão já existente (classificação + decisão,
já embutidas em cada `alerta` por `verificar_datas.py`; orquestrador;
source adapter; auto-update engine em memória) para observar o que o
sistema FARIA em produção — sem produzir NENHUM efeito real.

O que este módulo NUNCA faz:
- escrever ficheiros (HTML, JSON, logs em disco, o que for);
- criar, fechar ou comentar GitHub Issues;
- fazer commits ou tocar em `git`;
- alterar workflows;
- modificar o estado do repositório de qualquer forma.

Como se garante isto:
- este módulo não importa `os`, `subprocess`, `shutil`, nem qualquer
  biblioteca de acesso ao GitHub — não há capacidade técnica de fazer
  I/O real, está estruturalmente impossível, não é só "por convenção";
- `orquestrador_datas.processar_alerta` é o único ponto do sistema
  autorizado a invocar `auto_update_engine.aplicar_auto_update`
  (Camada 5) — e esse motor já garante, por construção, que toda a
  "aplicação do patch" acontece só sobre uma string em memória, nunca
  num ficheiro real (Camada 4);
- este módulo NÃO liga a flag `decisao_datas.AUTO_UPDATE_HABILITADO` —
  observa o sistema exactamente como está configurado hoje (desligado
  por omissão). Não é propósito do Shadow Mode simular "e se a flag
  estivesse ligada" — é observar o comportamento REAL actual.

Fronteira desta camada: `source_adapter.obter_valor_oficial` é
consultado aqui apenas para fins de relatório/observabilidade (que
provider seria usado, que fonte, que confiança) — o valor que devolve
NÃO é injectado em `alerta["novo_valor"]` nem passado ao
auto_update_engine. Ligar as duas coisas é uma integração futura,
deliberadamente fora do âmbito desta ferramenta de validação.

Isolamento por alerta: qualquer erro ao processar um alerta (no source
adapter, no orquestrador, ou um alerta malformado) é apanhado e
reportado como uma entrada de relatório com estado de erro — nunca
interrompe a análise dos restantes alertas da lista.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import orquestrador_datas
import source_adapter
from decisao_datas import Acao


_MARCADOR_ERRO_FONTE = "erro ao consultar source_adapter em shadow mode"


def _agora(agora: Optional[str]) -> str:
    return agora if agora is not None else datetime.now(timezone.utc).isoformat()


def _consultar_fonte(alerta: dict, *, agora: Optional[str]) -> source_adapter.ResultadoFonte:
    try:
        return source_adapter.obter_valor_oficial(alerta, agora=agora)
    except Exception as e:  # defesa extra: source_adapter já não lança, mas nunca confiar cegamente
        return source_adapter.ResultadoFonte(
            encontrado=False,
            confianca=0.0,
            data_consulta=_agora(agora),
            motivo=f"{_MARCADOR_ERRO_FONTE}: {e}",
        )


def _consultar_orquestrador(alerta: dict, *, agora: Optional[str]) -> Dict[str, Any]:
    try:
        return orquestrador_datas.processar_alerta(alerta, agora=agora)
    except Exception as e:  # defesa extra: o orquestrador já não lança, mas nunca confiar cegamente
        return {
            "estado": "DESCONHECIDO",
            "acao_pretendida": Acao.IGNORAR,
            "acao_executada": Acao.LOG_ONLY,
            "motivo": f"erro ao consultar orquestrador em shadow mode: {e}",
            "timestamp": _agora(agora),
        }


def _relatorio_erro(alerta: Any, motivo: str, timestamp: str) -> Dict[str, Any]:
    pagina = alerta.get("pagina", "desconhecida") if isinstance(alerta, dict) else "desconhecida"
    return {
        "pagina": pagina,
        "estado": "ERRO",
        "decisao": "DESCONHECIDA",
        "acao_prevista": Acao.LOG_ONLY,
        "provider": None,
        "fonte": None,
        "confianca": 0.0,
        "motivo": motivo,
        "resultado_auto_update": None,
        "alterou_algo": False,
        "shadow_mode": True,
    }


def _processar_um_alerta(alerta: dict, *, agora: Optional[str]) -> Dict[str, Any]:
    timestamp = _agora(agora)
    alerta = alerta or {}
    classificacao = alerta.get("classificacao") or {}
    decisao = alerta.get("decisao") or {}

    pagina = alerta.get("pagina", "desconhecida")
    estado = classificacao.get("estado", "DESCONHECIDO")
    decisao_pretendida = decisao.get("acao", "DESCONHECIDA")

    resultado_fonte = _consultar_fonte(alerta, agora=timestamp)
    resultado_orquestrador = _consultar_orquestrador(alerta, agora=timestamp)

    # "motivo" é primariamente o motivo da decisão (orquestrador). Se a
    # consulta à fonte falhou de forma inesperada (não a resposta normal
    # de um placeholder), isso é informação de diagnóstico do próprio
    # shadow mode e é acrescentada para não se perder silenciosamente --
    # não há campo dedicado próprio no relatório para isto.
    motivo = resultado_orquestrador.get("motivo")
    if resultado_fonte.motivo and resultado_fonte.motivo.startswith(_MARCADOR_ERRO_FONTE):
        motivo = f"{motivo} | {resultado_fonte.motivo}"

    return {
        "pagina": pagina,
        "estado": estado,
        "decisao": decisao_pretendida,
        "acao_prevista": resultado_orquestrador.get("acao_executada"),
        "provider": resultado_fonte.provider,
        "fonte": resultado_fonte.url_origem,
        "confianca": resultado_fonte.confianca,
        "motivo": motivo,
        "resultado_auto_update": resultado_orquestrador.get("resultado_engine"),
        "alterou_algo": False,
        "shadow_mode": True,
    }


def executar_shadow_mode(alertas: List[dict], *, agora: Optional[str] = None) -> List[Dict[str, Any]]:
    """Corre a cadeia de decisão completa para cada `alerta` em modo de
    observação pura — nunca escreve nada, nunca cria/fecha Issues, nunca
    faz commits. Devolve uma lista de relatórios estruturados, um por
    alerta, sempre com `shadow_mode: True` e `alterou_algo: False`.

    Um erro ao processar um alerta nunca interrompe os restantes — é
    reportado como uma entrada de relatório com `estado: "ERRO"`.
    """
    timestamp = _agora(agora)
    relatorio = []
    for alerta in alertas or []:
        try:
            relatorio.append(_processar_um_alerta(alerta, agora=timestamp))
        except Exception as e:
            relatorio.append(_relatorio_erro(
                alerta, f"erro inesperado em shadow mode — alerta ignorado: {e}", timestamp
            ))
    return relatorio
