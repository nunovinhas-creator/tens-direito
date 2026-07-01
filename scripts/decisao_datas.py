"""
CAMADA 3 — Motor de decisão (TENS DIREITO, deteção de datas expiradas).

Transforma o estado devolvido por `classificar_datas.EstadoData` numa
ação. Esta camada é puramente declarativa: `decidir_acao` devolve uma
string — nenhuma função aqui escreve ficheiros, chama a API do GitHub,
faz scraping ou dispara qualquer efeito real. Não existe (ainda) nenhum
executor que consuma esta ação — essa é uma fase futura, deliberadamente
fora do âmbito deste passo.

Mapeamento obrigatório (estado -> intent):
    OK                        -> IGNORAR
    STATIC_REFERENCE          -> IGNORAR
    BLOCKED_SOURCE            -> LOG_ONLY
    OUTDATED_REVIEW_REQUIRED  -> CREATE_ISSUE
    OUTDATED_AUTOFIXABLE      -> AUTO_UPDATE

Guarda de segurança — AUTO_UPDATE:
    Ainda não existe motor de auto-update (nem é suposto existir neste
    passo). Por isso, `AUTO_UPDATE_HABILITADO = False` por omissão, e
    `decidir_acao` despromove qualquer intent AUTO_UPDATE para LOG_ONLY
    antes de o devolver. Isto garante que, mesmo que uma fase futura
    ligue o campo "acao" a um executor sem voltar a rever esta flag,
    nada é aplicado automaticamente a um ficheiro enquanto o motor de
    auto-update não for implementado e revisto à parte.

    O intent puro (sem a guarda) continua disponível via
    `decidir_intent`, para quem precisar de o inspecionar — ex.: para
    preparar, sem executar, o motor de auto-update numa fase futura.
"""
from __future__ import annotations


class Acao:
    IGNORAR = "IGNORAR"
    LOG_ONLY = "LOG_ONLY"
    CREATE_ISSUE = "CREATE_ISSUE"
    AUTO_UPDATE = "AUTO_UPDATE"


_MAPEAMENTO_ESTADO_PARA_ACAO = {
    "OK": Acao.IGNORAR,
    "STATIC_REFERENCE": Acao.IGNORAR,
    "BLOCKED_SOURCE": Acao.LOG_ONLY,
    "OUTDATED_REVIEW_REQUIRED": Acao.CREATE_ISSUE,
    "OUTDATED_AUTOFIXABLE": Acao.AUTO_UPDATE,
}

# Interruptor de segurança: NÃO ligar sem primeiro implementar e rever à
# parte um motor de auto-update real. Enquanto for False, decidir_acao
# despromove AUTO_UPDATE para LOG_ONLY.
AUTO_UPDATE_HABILITADO = False


def decidir_intent(estado: str) -> str:
    """Mapeamento puro estado -> ação, sem a guarda de segurança de
    AUTO_UPDATE. Estado desconhecido é tratado como IGNORAR (falha segura
    — nunca assume uma ação mais agressiva do que IGNORAR por defeito).

    Não usar directamente para decidir execução — usar `decidir_acao`.
    """
    return _MAPEAMENTO_ESTADO_PARA_ACAO.get(estado, Acao.IGNORAR)


def decidir_acao(estado: str, contexto: dict) -> str:
    """Decide a ação para um `estado` (de `classificar_datas.EstadoData`)
    e o `contexto` da correspondência que lhe deu origem.

    `contexto` está reservado para heurísticas futuras (ex.: excepções
    por página) — a decisão actual depende só do `estado`, conforme o
    mapeamento obrigatório. Não executa nenhum efeito real: devolve
    apenas uma string.
    """
    intent = decidir_intent(estado)
    if intent == Acao.AUTO_UPDATE and not AUTO_UPDATE_HABILITADO:
        return Acao.LOG_ONLY
    return intent


def decidir_acao_estruturada(estado: str, contexto: dict) -> dict:
    """Camada intermédia pedida: devolve `{"estado", "acao", "contexto"}`
    sem executar qualquer efeito real."""
    return {
        "estado": estado,
        "acao": decidir_acao(estado, contexto),
        "contexto": contexto,
    }
