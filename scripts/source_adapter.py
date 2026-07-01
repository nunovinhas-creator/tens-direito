"""
CAMADA 6 — Source Adapter (TENS DIREITO, deteção de datas expiradas).

Responsabilidade única: responder "qual é o valor oficial desta
informação?" a partir de um `alerta`. Nada mais.

Isolamento deliberado: este módulo NÃO importa (nem sabe nada sobre)
GitHub Issues, CI/CD, workflows, `auto_update_engine` ou
`verificar_datas`. Nenhum desses módulos importa este ficheiro — é uma
camada preparatória, construída e testada isoladamente, ainda sem
nenhum ponto de chamada em produção. O objetivo é que, no futuro, o
orquestrador (Camada 5) possa simplesmente fazer

    resultado = obter_valor_oficial(alerta)

sem conhecer de onde vem o valor — mas essa ligação não é feita aqui.

Nesta fase NÃO há scraping real: todos os providers são placeholders
que devolvem uma resposta controlada (`encontrado=False`, com motivo
explícito). Não há pedidos de rede, não há ficheiros escritos, não há
efeitos colaterais de qualquer tipo — `obter_valor_oficial` é uma
função pura do ponto de vista do sistema de ficheiros e da rede.

Arquitectura (Strategy / Plugin):
    - `FonteProvider` é a interface comum (classe abstracta) que
      qualquer provider tem de implementar: `aplica_se(alerta)` decide
      se é responsável por aquele alerta; `obter_valor(alerta)` devolve
      o `ResultadoFonte`.
    - `registar_provider(provider)` adiciona um novo provider ao
      registo em runtime — permite estender o sistema com novas fontes
      sem alterar nenhum código existente neste ficheiro (princípio
      aberto/fechado).
    - `obter_valor_oficial(alerta)` é o único ponto de entrada público:
      escolhe automaticamente o provider aplicável (o primeiro
      registado cujo `aplica_se` seja verdadeiro) e delega nele. Sem
      provider aplicável, devolve `ResultadoFonte(encontrado=False, ...)`
      — nunca lança excepção.
"""
from __future__ import annotations

import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


@dataclass(frozen=True)
class ResultadoFonte:
    """Resposta estruturada e uniforme de qualquer provider."""

    encontrado: bool
    valor: Optional[str] = None
    url_origem: Optional[str] = None
    data_consulta: Optional[str] = None
    confianca: float = 0.0
    motivo: Optional[str] = None
    provider: Optional[str] = None


def _agora(agora: Optional[str]) -> str:
    return agora if agora is not None else datetime.now(timezone.utc).isoformat()


def _normalizar(texto: str) -> str:
    texto = (texto or "").lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def _texto_alerta(alerta: dict) -> str:
    """Concatena os campos textuais do alerta que ajudam a identificar a
    fonte oficial responsável (nome da página, tipo, e o texto de
    contexto já extraído pela Camada 2)."""
    alerta = alerta or {}
    classificacao = alerta.get("classificacao") or {}
    partes = [
        str(alerta.get("pagina", "")),
        str(alerta.get("tipo", "")),
        str(classificacao.get("contexto", "")),
    ]
    return _normalizar(" ".join(partes))


class FonteProvider(ABC):
    """Interface comum a qualquer provider de fonte oficial."""

    nome: str = "generico"

    @abstractmethod
    def aplica_se(self, alerta: dict) -> bool:
        """Devolve True se este provider é responsável pela fonte
        oficial deste alerta."""

    @abstractmethod
    def obter_valor(self, alerta: dict, *, agora: Optional[str] = None) -> ResultadoFonte:
        """Devolve o ResultadoFonte para este alerta. Nunca deve lançar
        excepção — erros são reportados via `ResultadoFonte(encontrado=False, motivo=...)`."""


class _ProviderPlaceholder(FonteProvider):
    """Base comum aos providers desta fase: nenhum faz scraping real —
    todos devolvem uma resposta controlada e auditável, identificando
    claramente que ainda são um placeholder à espera de implementação."""

    url_base: str = ""
    palavras_chave: tuple = ()

    def aplica_se(self, alerta: dict) -> bool:
        texto = _texto_alerta(alerta)
        return any(p in texto for p in self.palavras_chave)

    def obter_valor(self, alerta: dict, *, agora: Optional[str] = None) -> ResultadoFonte:
        return ResultadoFonte(
            encontrado=False,
            valor=None,
            url_origem=self.url_base,
            data_consulta=_agora(agora),
            confianca=0.0,
            motivo=(
                f"provider '{self.nome}' é um placeholder — obtenção real "
                f"de valores ainda não implementada"
            ),
            provider=self.nome,
        )


# ── Providers placeholder (fontes já confirmadas em CLAUDE.md) ─────────────
# As URLs usadas são exactamente as já auditadas e aprovadas na secção
# "FONTES VERIFICADAS E APROVADAS" do CLAUDE.md — nenhum URL novo ou por
# confirmar é introduzido aqui.

class ProviderSegurancaSocial(_ProviderPlaceholder):
    nome = "seguranca_social"
    url_base = "https://www.seg-social.pt"
    palavras_chave = (
        "abono", "seg-social", "seguranca social", "rsi", "csi",
        "prestacao-social", "prestacao social unica", "psu",
        "complemento solidario", "subsidio parental",
    )


class ProviderIEFP(_ProviderPlaceholder):
    nome = "iefp"
    url_base = "https://www.iefp.pt/subsidio-desemprego"
    palavras_chave = ("iefp", "subsidio-desemprego", "subsidio de desemprego")


class ProviderDGE(_ProviderPlaceholder):
    nome = "dge"
    url_base = "https://www.dge.mec.pt"
    palavras_chave = (
        "dge", "acao-social-escolar", "ase", "bolsa-de-merito",
        "bolsa de merito", "manuais-escolares", "manuais escolares",
    )


class ProviderDiarioRepublica(_ProviderPlaceholder):
    nome = "diario_republica"
    url_base = "https://dre.pt"
    palavras_chave = (
        "portaria", "decreto-lei", "decreto lei", "despacho",
        "diario da republica", "dre.pt",
    )


# ── Registo/dispatcher ──────────────────────────────────────────────────────
# Ordem de avaliação: o primeiro provider registado cujo `aplica_se`
# devolva True é o escolhido. Novos providers podem ser adicionados via
# `registar_provider` sem alterar nenhuma linha deste ficheiro.

_REGISTO_PROVIDERS: List[FonteProvider] = [
    ProviderSegurancaSocial(),
    ProviderIEFP(),
    ProviderDGE(),
    ProviderDiarioRepublica(),
]


def registar_provider(provider: FonteProvider, *, prioridade: bool = False) -> None:
    """Adiciona um novo provider ao registo em runtime — o mecanismo de
    extensão pretendido: novas fontes oficiais entram por aqui, sem
    tocar em `_REGISTO_PROVIDERS`, no dispatcher ou em qualquer provider
    já existente.

    `prioridade=True` insere-o à cabeça da lista (avaliado antes dos
    restantes); por omissão é acrescentado ao fim.
    """
    if prioridade:
        _REGISTO_PROVIDERS.insert(0, provider)
    else:
        _REGISTO_PROVIDERS.append(provider)


def _selecionar_provider(alerta: dict) -> Optional[FonteProvider]:
    for provider in _REGISTO_PROVIDERS:
        try:
            if provider.aplica_se(alerta):
                return provider
        except Exception:
            # Um provider mal-comportado não pode impedir a avaliação
            # dos restantes nem derrubar o dispatcher.
            continue
    return None


def obter_valor_oficial(alerta: dict, *, agora: Optional[str] = None) -> ResultadoFonte:
    """Ponto de entrada público único desta camada: "qual é o valor
    oficial desta informação?"

    Nunca lança excepção para o chamador — sem provider aplicável, ou em
    caso de erro interno inesperado, devolve sempre um `ResultadoFonte`
    com `encontrado=False` e `motivo` explicativo.
    """
    try:
        alerta = alerta or {}
        provider = _selecionar_provider(alerta)
        if provider is None:
            return ResultadoFonte(
                encontrado=False,
                confianca=0.0,
                data_consulta=_agora(agora),
                motivo="nenhum provider aplicável para este alerta",
            )
        return provider.obter_valor(alerta, agora=agora)
    except Exception as e:
        return ResultadoFonte(
            encontrado=False,
            confianca=0.0,
            data_consulta=_agora(agora),
            motivo=f"erro inesperado no source_adapter: {e}",
        )
