"""
scripts/shadow_mode_analytics.py

Ferramenta de análise e métricas dos relatórios produzidos pelo Shadow
Mode (`scripts/shadow_mode.py`). Puramente analítica: lê uma lista de
relatórios já em memória e devolve métricas agregadas — nunca escreve
ficheiros, nunca executa auto-update, nunca toca em Issues, workflows
ou em qualquer outra camada do sistema.

Isolamento deliberado: este módulo NÃO importa `shadow_mode.py` nem
qualquer outra camada (`verificar_datas`, `classificar_datas`,
`decisao_datas`, `auto_update_engine`, `orquestrador_datas`,
`source_adapter`) — opera exclusivamente sobre a estrutura de dicts já
produzida por essas camadas (o "contrato" de campos que
`shadow_mode.executar_shadow_mode` devolve), o que o mantém testável e
reutilizável de forma completamente desacoplada.

Também não importa `os`, `subprocess` nem `shutil`, e não abre nenhum
ficheiro para escrita: não ser capaz de escrever ficheiros ou executar
nada não é uma convenção aqui — é uma impossibilidade estrutural, não
existe nenhum caminho de código capaz de o fazer.

Perguntas a que esta ferramenta responde:
    - "O que o sistema faria em produção hoje?"        -> por_estado/por_acao
    - "Quantos auto-updates seriam executados?"        -> auto_update_elegiveis
    - "Quantos estão bloqueados por guardrails?"       -> auto_update_bloqueados
    - "Qual é o risco actual do sistema?"               -> erros / erros_por_provider
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

ESTADOS_CONHECIDOS = (
    "OK",
    "OUTDATED_AUTOFIXABLE",
    "OUTDATED_REVIEW_REQUIRED",
    "STATIC_REFERENCE",
    "BLOCKED_SOURCE",
)

ACOES_CONHECIDAS = ("IGNORAR", "LOG_ONLY", "CREATE_ISSUE", "AUTO_UPDATE")

_SEM_PROVIDER = "sem_provider"


def _teve_erro(relatorio: dict) -> bool:
    if relatorio.get("estado") == "ERRO":
        return True
    motivo = relatorio.get("motivo")
    return isinstance(motivo, str) and "erro" in motivo.lower()


def analisar_shadow_mode(relatorios: List[dict]) -> Dict[str, Any]:
    """Agrega os relatórios do Shadow Mode (output de
    `shadow_mode.executar_shadow_mode`) em métricas de observabilidade.

    Nunca lança excepção: entradas malformadas (não-dict) são contadas
    como erro e ignoradas para as restantes métricas, sem interromper a
    agregação do resto da lista. Função pura — o mesmo input produz
    sempre o mesmo output.
    """
    por_estado: Dict[str, int] = {estado: 0 for estado in ESTADOS_CONHECIDOS}
    por_acao: Dict[str, int] = {acao: 0 for acao in ACOES_CONHECIDAS}
    erros_por_provider: Dict[str, int] = {}

    total_alertas = 0
    auto_update_elegiveis = 0
    auto_update_bloqueados = 0
    erros = 0
    soma_confianca = 0.0
    contagem_confianca = 0

    for relatorio in relatorios or []:
        total_alertas += 1

        if not isinstance(relatorio, dict):
            erros += 1
            erros_por_provider[_SEM_PROVIDER] = erros_por_provider.get(_SEM_PROVIDER, 0) + 1
            continue

        estado = relatorio.get("estado", "DESCONHECIDO")
        por_estado[estado] = por_estado.get(estado, 0) + 1

        acao_prevista = relatorio.get("acao_prevista", "DESCONHECIDA")
        por_acao[acao_prevista] = por_acao.get(acao_prevista, 0) + 1

        if relatorio.get("decisao") == "AUTO_UPDATE":
            if acao_prevista == "AUTO_UPDATE":
                auto_update_elegiveis += 1
            else:
                auto_update_bloqueados += 1

        confianca = relatorio.get("confianca")
        if isinstance(confianca, (int, float)) and not isinstance(confianca, bool):
            soma_confianca += confianca
            contagem_confianca += 1

        if _teve_erro(relatorio):
            erros += 1
            provider = relatorio.get("provider") or _SEM_PROVIDER
            erros_por_provider[provider] = erros_por_provider.get(provider, 0) + 1

    total_tentativas_auto_update = auto_update_elegiveis + auto_update_bloqueados
    taxa_sucesso_estimada = (
        auto_update_elegiveis / total_tentativas_auto_update
        if total_tentativas_auto_update > 0
        else 0.0
    )
    confianca_media = soma_confianca / contagem_confianca if contagem_confianca > 0 else 0.0

    return {
        "total_alertas": total_alertas,
        "por_estado": por_estado,
        "por_acao": por_acao,
        "auto_update_elegiveis": auto_update_elegiveis,
        "auto_update_bloqueados": auto_update_bloqueados,
        "taxa_sucesso_estimada": taxa_sucesso_estimada,
        "erros": erros,
        "erros_por_provider": erros_por_provider,
        "confianca_media": confianca_media,
    }


def exportar_relatorio_json(analise: dict, *, indent: Optional[int] = 2) -> str:
    """Serializa uma análise (output de `analisar_shadow_mode`) para uma
    string JSON. NUNCA escreve em disco — devolve só a string; quem
    chamar decide o que fazer com ela (imprimir, anexar a um comentário,
    guardar onde e como quiser, fora deste módulo)."""
    return json.dumps(analise, ensure_ascii=False, indent=indent)


def filtrar_auto_update_candidatos(relatorios: List[dict]) -> List[dict]:
    """Devolve só os relatórios cuja decisão original (Camada 3) foi
    AUTO_UPDATE — candidatos a auto-update, tenham sido aplicados ou
    bloqueados por guardrails (ver o campo `acao_prevista` de cada um
    para saber qual dos dois casos é)."""
    return [
        relatorio
        for relatorio in (relatorios or [])
        if isinstance(relatorio, dict) and relatorio.get("decisao") == "AUTO_UPDATE"
    ]


def comparar_execucoes(atual: dict, anterior: dict) -> Dict[str, Any]:
    """Compara duas análises (outputs de `analisar_shadow_mode`) e
    devolve o delta campo a campo (`atual - anterior`) — útil para
    acompanhar a evolução do sistema entre duas execuções do Shadow
    Mode. Puramente aritmético, sem qualquer efeito lateral."""
    atual = atual or {}
    anterior = anterior or {}
    delta: Dict[str, Any] = {}

    for chave in set(atual.keys()) | set(anterior.keys()):
        v_atual = atual.get(chave)
        v_anterior = anterior.get(chave)

        if isinstance(v_atual, dict) or isinstance(v_anterior, dict):
            v_atual = v_atual or {}
            v_anterior = v_anterior or {}
            delta[chave] = {
                sub: v_atual.get(sub, 0) - v_anterior.get(sub, 0)
                for sub in set(v_atual.keys()) | set(v_anterior.keys())
            }
        elif isinstance(v_atual, (int, float)) or isinstance(v_anterior, (int, float)):
            delta[chave] = (v_atual or 0) - (v_anterior or 0)
        else:
            delta[chave] = {"atual": v_atual, "anterior": v_anterior}

    return delta
