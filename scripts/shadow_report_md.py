"""
scripts/shadow_report_md.py

Camada de apresentação para os resultados do Shadow Mode: transforma o
dict de métricas produzido por `shadow_mode_analytics.analisar_shadow_mode`
num relatório em Markdown simples, pensado para ser lido directamente
por alguém sem conhecimentos técnicos.

Este módulo é apenas de apresentação — não decide nada, não calcula
métricas novas (usa só o que já vem em `analytics`), não executa
nenhuma acção do sistema. Não importa `shadow_mode.py`, o analytics,
nem qualquer outra camada — recebe sempre um dict já pronto e devolve
uma string. Não importa `os`, `subprocess` nem `shutil`, e não abre
nenhum ficheiro: `gerar_relatorio_markdown` nunca escreve nada, só
devolve texto — quem chamar decide se e onde guardar esse texto.

Vocabulário deliberadamente simples: o texto gerado evita termos como
"payload", "dispatcher", "pipeline", "provider" ou JSON — fala em
"fonte oficial", "risco", "estável"/"instável", números simples e
percentagens.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

NIVEIS_RISCO = ("BAIXO", "MÉDIO", "ALTO")

_ESTABILIDADE_POR_RISCO = {
    "BAIXO": "estável",
    "MÉDIO": "instável",
    "ALTO": "em risco",
}

_LIMIAR_CONFIANCA_ALTA = 0.7

_NOMES_AMIGAVEIS_FONTE = {
    "seguranca_social": "Segurança Social",
    "iefp": "IEFP",
    "dge": "DGE",
    "diario_republica": "Diário da República",
    "sem_provider": "sem fonte identificada",
}

_RELATORIO_DE_RECURSO = (
    "# 📊 Relatório do Sistema — Shadow Mode\n\n"
    "Não foi possível gerar o relatório completo a partir dos dados "
    "recebidos. Nenhuma alteração foi feita ao sistema.\n"
)


def _numero(valor: Any, default: int = 0) -> int:
    return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else default


def _percentagem(valor: Any) -> str:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        valor = 0.0
    return f"{round(valor * 100)}%"


def _avaliar_risco(total: int, erros: int, fonte_bloqueada: int, precisa_revisao: int) -> str:
    if total == 0:
        return "BAIXO"
    if erros > 0:
        return "ALTO"
    if fonte_bloqueada > 0 or precisa_revisao > 0:
        return "MÉDIO"
    return "BAIXO"


def _recomendacao(risco: str, confianca_media: float, elegiveis: int) -> str:
    if risco == "ALTO":
        return "não ativar"
    if risco == "MÉDIO":
        return "manter em observação"
    if elegiveis > 0 and confianca_media >= _LIMIAR_CONFIANCA_ALTA:
        return "ativar"
    return "manter em observação"


def _principal_risco_texto(erros: int, fonte_bloqueada: int, precisa_revisao: int) -> str:
    if erros > 0:
        return (
            f"Aconteceram {erros} erro(s) durante a análise — é preciso "
            f"perceber a causa antes de dar qualquer passo automático."
        )
    if fonte_bloqueada > 0:
        return (
            f"Há {fonte_bloqueada} caso(s) em que ainda não foi possível "
            f"confirmar a informação junto da fonte oficial — esses casos "
            f"não podem ser corrigidos sozinhos enquanto isso não for "
            f"resolvido."
        )
    if precisa_revisao > 0:
        return (
            f"Há {precisa_revisao} caso(s) que precisam de ser revistos por "
            f"uma pessoa — não é urgente, mas não deve ficar esquecido."
        )
    return "Não foi identificado nenhum risco relevante nesta análise."


def _principal_limitacao_texto(confianca_media: float) -> str:
    if confianca_media < 0.5:
        return (
            "As fontes oficiais ainda estão numa fase inicial — o sistema "
            "ainda não vai buscar valores reais a todas elas, por isso a "
            "confiança apresentada ainda é baixa."
        )
    return (
        "A maior parte das fontes já foi confirmada, mas ainda há casos "
        "por validar antes de confiar totalmente no sistema."
    )


def _erros_por_fonte_texto(erros_por_provider: Dict[str, int]) -> str:
    if not erros_por_provider:
        return "nenhum"
    partes = [
        f"{_NOMES_AMIGAVEIS_FONTE.get(nome, nome)} ({contagem})"
        for nome, contagem in sorted(erros_por_provider.items())
    ]
    return ", ".join(partes)


def gerar_relatorio_markdown(analytics: dict, *, data: Optional[str] = None) -> str:
    """Transforma um dict de métricas (output de
    `shadow_mode_analytics.analisar_shadow_mode`) num relatório em
    Markdown simples, para leitura directa por alguém sem formação
    técnica. Devolve sempre uma string — nunca lança excepção, nunca
    escreve nada, nunca faz mais do que ler o `analytics` recebido.

    `data` é opcional e só decorativo (ex.: "2026-07-01"). Sem ele, o
    relatório não inclui nenhuma referência a data/hora — o texto
    depende só do `analytics` recebido, nunca do relógio do sistema.
    """
    try:
        analytics = analytics or {}
        por_estado = analytics.get("por_estado") or {}

        total = _numero(analytics.get("total_alertas"))
        confianca_media = analytics.get("confianca_media")
        confianca_media = confianca_media if isinstance(confianca_media, (int, float)) and not isinstance(confianca_media, bool) else 0.0
        erros = _numero(analytics.get("erros"))
        elegiveis = _numero(analytics.get("auto_update_elegiveis"))
        bloqueados = _numero(analytics.get("auto_update_bloqueados"))

        ok = _numero(por_estado.get("OK")) + _numero(por_estado.get("STATIC_REFERENCE"))
        precisa_revisao = _numero(por_estado.get("OUTDATED_REVIEW_REQUIRED"))
        fonte_bloqueada = _numero(por_estado.get("BLOCKED_SOURCE"))
        auto_fixavel = _numero(por_estado.get("OUTDATED_AUTOFIXABLE"))

        risco = _avaliar_risco(total, erros, fonte_bloqueada, precisa_revisao)
        estabilidade = _ESTABILIDADE_POR_RISCO[risco]
        recomendacao = _recomendacao(risco, confianca_media, elegiveis)

        linhas = [
            "# 📊 Relatório do Sistema — Shadow Mode",
            "",
        ]
        if data:
            linhas += [f"_Gerado a: {data}_", ""]

        linhas += [
            "## Resumo geral",
            f"- Alertas analisados: {total}",
            f"- Confiança média do sistema: {_percentagem(confianca_media)}",
            f"- Risco global: {risco}",
            "",
            "---",
            "",
            "## Distribuição dos alertas",
            f"- OK: {ok}",
            f"- Precisa revisão: {precisa_revisao}",
            f"- Fonte bloqueada: {fonte_bloqueada}",
            f"- Auto-update possível (não executado): {auto_fixavel}",
            "",
            "---",
            "",
            "## Auto-update (simulado)",
            f"- Elegíveis: {elegiveis}",
            f"- Bloqueados por segurança: {bloqueados}",
            "",
            "---",
            "",
            "## Avaliação do sistema",
            f"- O sistema está {estabilidade}",
            f"- Recomendação: {recomendacao}",
            "",
            "---",
            "",
            "## Observações importantes",
            f"- {_principal_risco_texto(erros, fonte_bloqueada, precisa_revisao)}",
            f"- {_principal_limitacao_texto(confianca_media)}",
        ]

        if erros:
            linhas.append(f"- Erros por fonte: {_erros_por_fonte_texto(analytics.get('erros_por_provider') or {})}")

        linhas += [
            "",
            "---",
            "",
            "_Este relatório foi gerado em modo de simulação (Shadow Mode) "
            "— nenhuma alteração real foi feita ao sistema, a ficheiros ou "
            "a GitHub Issues._",
        ]

        return "\n".join(linhas) + "\n"

    except Exception:
        return _RELATORIO_DE_RECURSO
