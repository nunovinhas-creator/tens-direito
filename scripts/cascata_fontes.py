"""
CAMADA 2 — Cascata de fontes por valor (TENS DIREITO, scraping resiliente).

Para cada valor publicado no site (IAS, RSI, abono, subsidio desemprego...),
define-se uma lista ORDENADA de fontes por robustez decrescente:

    1. Fonte legislativa primaria (portaria/DRE consolidado) — mais estavel
    2. Fonte secundaria (pagina-servico: seg-social, iefp) — confirmacao
    3. Fallback final: valor congelado com last_verified_by_human

Regra de ouro: o resolver so aceita um valor de uma fonte classificada OK
pela Camada 1 (classificador_resposta). BLOQUEADO nunca produz um valor novo
publicavel — cai sempre para a fonte seguinte, e em ultimo caso para o
congelado. O site NUNCA mostra um valor nao verificado.

Depende de classificador_resposta.py (Camada 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Callable, Optional

from classificador_resposta import Classificacao, Estado, FonteConfig


class TipoFonte(str, Enum):
    LEGISLATIVA = "legislativa"   # portaria/DRE — mais estavel
    SERVICO = "servico"           # pagina-servico (seg-social, iefp...) — fragil
    CONGELADO = "congelado"       # last_verified_by_human — rede final


@dataclass(frozen=True)
class FontePassoConfig:
    """Um passo na cascata de uma rubrica."""
    tipo: TipoFonte
    fonte_config: FonteConfig
    # extrator(corpo_html) -> valor extraido (string/numero) ou None se nao encontrou
    extrator: Callable[[str], Optional[str]]
    url: str = ""


@dataclass
class ValorCongelado:
    valor: str
    data_verificacao: date
    verificado_por: str = "humano"


@dataclass(frozen=True)
class RubricaConfig:
    """Configuracao de cascata para UM valor publicado (ex.: 'subsidio_desemprego_montante_max')."""
    nome: str
    cascata: tuple  # tuple[FontePassoConfig, ...] em ordem de prioridade
    congelado: ValorCongelado


class ResultadoTipo(str, Enum):
    RESOLVIDO = "RESOLVIDO"       # valor obtido de fonte OK na cascata
    CONGELADO = "CONGELADO"       # todas as fontes falharam -> usou-se o valor congelado
    SEM_VALOR = "SEM_VALOR"       # nem cascata nem congelado disponiveis (nao deveria acontecer)


@dataclass
class ResolucaoRubrica:
    rubrica: str
    resultado: ResultadoTipo
    valor: Optional[str]
    fonte_usada: Optional[str]            # nome da FonteConfig que resolveu, ou "congelado"
    tipo_fonte_usada: Optional[TipoFonte]
    tentativas: list = field(default_factory=list)  # [(nome_fonte, Estado, motivos)]
    data_congelado: Optional[date] = None

    @property
    def publicavel(self) -> bool:
        # so nunca publicavel se SEM_VALOR; RESOLVIDO e CONGELADO sao ambos seguros
        return self.resultado != ResultadoTipo.SEM_VALOR


# Tipo do "fetcher": dado um url, devolve (status_code, corpo_html, url_final)
Fetcher = Callable[[str], tuple]


def resolver_rubrica(rubrica: RubricaConfig, fetcher: Fetcher) -> ResolucaoRubrica:
    """
    Percorre a cascata da rubrica por ordem. Para na primeira fonte cujo
    fetch e classificacao (Camada 1) deem OK e cujo extrator devolva um valor.
    Se nenhuma fonte resolver, cai no valor congelado (nunca SEM_VALOR se
    houver congelado definido).
    """
    tentativas = []

    for passo in rubrica.cascata:
        try:
            status_code, corpo, url_final = fetcher(passo.url)
        except Exception as e:  # falha de rede tambem conta como bloqueio, nao crash
            tentativas.append((passo.fonte_config.nome, Estado.BLOQUEADO, [f"excecao_fetch:{e}"]))
            continue

        from classificador_resposta import classificar_resposta
        c: Classificacao = classificar_resposta(
            status_code=status_code, corpo=corpo, url_final=url_final,
            config=passo.fonte_config,
        )
        tentativas.append((passo.fonte_config.nome, c.estado, c.motivos))

        if c.estado != Estado.OK:
            continue  # cai para a fonte seguinte na cascata

        valor = passo.extrator(corpo)
        if valor is None:
            # pagina real, mas o extrator nao encontrou o campo esperado.
            # Isto NAO e bloqueio (Camada 1 ja disse OK) — e possivel mudanca
            # de estrutura. Regista e cai para a fonte seguinte na mesma.
            tentativas.append((passo.fonte_config.nome, Estado.OK, ["extrator_nao_encontrou_valor"]))
            continue

        return ResolucaoRubrica(
            rubrica=rubrica.nome,
            resultado=ResultadoTipo.RESOLVIDO,
            valor=valor,
            fonte_usada=passo.fonte_config.nome,
            tipo_fonte_usada=passo.tipo,
            tentativas=tentativas,
        )

    # Cascata esgotada sem sucesso -> fallback para congelado
    if rubrica.congelado is not None:
        return ResolucaoRubrica(
            rubrica=rubrica.nome,
            resultado=ResultadoTipo.CONGELADO,
            valor=rubrica.congelado.valor,
            fonte_usada="congelado",
            tipo_fonte_usada=TipoFonte.CONGELADO,
            tentativas=tentativas,
            data_congelado=rubrica.congelado.data_verificacao,
        )

    return ResolucaoRubrica(
        rubrica=rubrica.nome,
        resultado=ResultadoTipo.SEM_VALOR,
        valor=None,
        fonte_usada=None,
        tipo_fonte_usada=None,
        tentativas=tentativas,
    )


def resumo_resolucao(r: ResolucaoRubrica) -> str:
    """Linha legivel para logs/observabilidade (Camada 4)."""
    linhas = [f"[{r.rubrica}] {r.resultado.value} via {r.fonte_usada or '—'} valor={r.valor!r}"]
    for nome, estado, motivos in r.tentativas:
        linhas.append(f"    - {nome}: {estado.value} {motivos}")
    if r.resultado == ResultadoTipo.CONGELADO:
        linhas.append(f"    -> usado valor congelado (verificado em {r.data_congelado})")
    return "\n".join(linhas)
