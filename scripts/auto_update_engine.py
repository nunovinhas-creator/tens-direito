"""
CAMADA 4 — Motor de auto-update (TENS DIREITO, deteção de datas expiradas).

Consome directamente o output de `decisao_datas.py` (um `alerta` com a
chave `"decisao"`) e, SE E SÓ SE a decisão for `AUTO_UPDATE` **e** a
feature flag `decisao_datas.AUTO_UPDATE_HABILITADO` estiver
explicitamente a `True`, simula um patch seguro sobre o conteúdo em
memória do alerta. Fora disso, devolve sempre `SKIPPED_SAFE_MODE` sem
tocar em nada.

Nota de auditoria (ler antes de tocar neste ficheiro):
Este módulo NUNCA importa `os`, `subprocess` ou `shutil`, e não abre
nenhum ficheiro. Isto não é um esquecimento — é a garantia de que não
há, nesta fase, NENHUM caminho de código capaz de escrever num ficheiro
real, apagar algo ou lançar um processo externo. Toda a "aplicação do
patch" acontece sobre uma string em memória (`conteudo`, tipicamente
`alerta["classificacao"]["contexto"]`) e é devolvida ao chamador —
nunca persistida aqui. Ligar isto a ficheiros reais do repositório é
uma fase futura, deliberadamente fora do âmbito deste passo, e exige o
seu próprio ponto de escrita explícito, revisto à parte (não este).

A auto-update engine também NUNCA é chamada a partir de
`verificar_datas.py` ou do pipeline diário — é invocada directamente
por quem a testar/usar, não automaticamente. Isso mantém-se assim até
uma decisão explícita de activação global.

Reutiliza `decisao_datas.AUTO_UPDATE_HABILITADO` como única fonte de
verdade da feature flag (em vez de manter uma cópia própria) para que
nunca possa divergir da Camada 3. A verificação é feita através do
módulo (`decisao_datas.AUTO_UPDATE_HABILITADO`), não de um valor
importado à parte, para que um `monkeypatch`/alteração em runtime seja
sempre respeitado e para nunca confiar cegamente em `decisao_datas` ter
aplicado a guarda correctamente — dupla verificação, não confiança.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Callable, Optional

import decisao_datas
from decisao_datas import Acao


class AcaoAutoUpdate:
    SKIPPED_SAFE_MODE = "SKIPPED_SAFE_MODE"
    SKIPPED_SEM_NOVO_VALOR = "SKIPPED_SEM_NOVO_VALOR"
    ABORTED_VALOR_NAO_ENCONTRADO = "ABORTED_VALOR_NAO_ENCONTRADO"
    ABORTED_DIFERENCA_ANOMALA = "ABORTED_DIFERENCA_ANOMALA"
    AUTO_UPDATE_APPLIED = "AUTO_UPDATE_APPLIED"
    ROLLED_BACK = "ROLLED_BACK"


# Acima destes limites, a diferença entre o valor antigo e o novo é
# tratada como anómala e o update é abortado (nunca aplicado).
LIMITE_DIFERENCA_RELATIVA = 0.5  # valores numéricos: 50% de variação
LIMITE_RATIO_TAMANHO = (0.3, 3.0)  # valores não numéricos: rácio de comprimento

_MOTIVO_SAFE_MODE = "AUTO_UPDATE desativado ou não elegível"

_REGEX_NUMERO = re.compile(r"\d+(?:\.\d{3})*(?:,\d+)?")


def _extrair_numero(texto) -> Optional[float]:
    if not isinstance(texto, str) or not texto:
        return None
    m = _REGEX_NUMERO.search(texto)
    if not m:
        return None
    bruto = m.group(0).replace(".", "").replace(",", ".")
    try:
        return float(bruto)
    except ValueError:
        return None


def _diferenca_aceitavel(valor_antigo, valor_novo) -> bool:
    """Compara valor_antigo vs valor_novo. Números: variação relativa
    dentro do limite. Texto sem números (ex.: datas por extenso): usa o
    rácio de comprimento como aproximação para apanhar substituições
    disparatadas, já que não há uma grandeza numérica para comparar."""
    antigo_num = _extrair_numero(valor_antigo)
    novo_num = _extrair_numero(valor_novo)
    if antigo_num is not None and novo_num is not None:
        base = max(abs(antigo_num), 1e-9)
        return abs(novo_num - antigo_num) / base <= LIMITE_DIFERENCA_RELATIVA

    minimo, maximo = LIMITE_RATIO_TAMANHO
    len_antigo = max(len(valor_antigo or ""), 1)
    ratio = len(valor_novo or "") / len_antigo
    return minimo <= ratio <= maximo


def buscar_novo_valor_mock(alerta: dict) -> Optional[str]:
    """Placeholder deliberadamente burro: NUNCA inventa um valor. Só
    devolve o que o próprio chamador já colocou em `alerta["novo_valor"]`
    — tipicamente lido de `data/scraped/*.json` por um passo anterior
    (fora deste módulo). Sem esse valor explícito, devolve `None` (nada
    para actualizar), nunca um número inventado."""
    return alerta.get("novo_valor")


def _autorizado(alerta: dict) -> bool:
    acao_decidida = (alerta.get("decisao") or {}).get("acao")
    return (
        acao_decidida == Acao.AUTO_UPDATE
        and decisao_datas.AUTO_UPDATE_HABILITADO is True
    )


def aplicar_auto_update(
    alerta: dict,
    *,
    buscar_novo_valor: Optional[Callable[[dict], Optional[str]]] = None,
    agora: Optional[str] = None,
) -> dict:
    """Processa um `alerta` (output combinado de `verificar_datas` +
    `classificar_datas` + `decisao_datas`) e devolve um dict descrevendo
    o resultado. Nunca lança excepção para o chamador — qualquer erro
    interno é apanhado e convertido em `ROLLED_BACK`, preservando sempre
    o conteúdo original (snapshot).

    Se não autorizado (decisão != AUTO_UPDATE ou flag desligada), devolve
    exactamente `{"acao": "SKIPPED_SAFE_MODE", "motivo": "..."}` — nada
    mais é sequer inspeccionado.
    """
    if not _autorizado(alerta):
        return {"acao": AcaoAutoUpdate.SKIPPED_SAFE_MODE, "motivo": _MOTIVO_SAFE_MODE}

    buscar_novo_valor = buscar_novo_valor or buscar_novo_valor_mock
    classificacao = alerta.get("classificacao") or {}
    valor_antigo = classificacao.get("data")
    conteudo_antigo = alerta.get("conteudo", classificacao.get("contexto"))

    # Snapshot guardado ANTES de qualquer tentativa de alteração — é o
    # que se devolve (rollback lógico) se algo a seguir falhar.
    snapshot = conteudo_antigo

    try:
        valor_novo = buscar_novo_valor(alerta)
        if not valor_novo:
            return {
                "acao": AcaoAutoUpdate.SKIPPED_SEM_NOVO_VALOR,
                "motivo": "Nenhum novo valor disponível para aplicar",
                "snapshot": snapshot,
            }

        if (
            not isinstance(valor_antigo, str)
            or not isinstance(conteudo_antigo, str)
            or valor_antigo not in conteudo_antigo
        ):
            return {
                "acao": AcaoAutoUpdate.ABORTED_VALOR_NAO_ENCONTRADO,
                "motivo": "Valor antigo não encontrado no conteúdo-alvo — update abortado",
                "snapshot": snapshot,
            }

        if not _diferenca_aceitavel(valor_antigo, valor_novo):
            return {
                "acao": AcaoAutoUpdate.ABORTED_DIFERENCA_ANOMALA,
                "motivo": (
                    f"Diferença entre '{valor_antigo}' e '{valor_novo}' "
                    f"excede o limite de segurança — update abortado"
                ),
                "snapshot": snapshot,
            }

        # Substituição única e explícita do valor exacto encontrado — o
        # "target" é sempre esta string em memória, nunca um ficheiro.
        conteudo_novo = conteudo_antigo.replace(valor_antigo, valor_novo, 1)

        if conteudo_novo == conteudo_antigo:
            raise ValueError("patch não teve qualquer efeito no conteúdo")

        log = {
            "pagina": alerta.get("pagina"),
            "tipo": alerta.get("tipo"),
            "estado": classificacao.get("estado"),
            "valor_antigo": valor_antigo,
            "valor_novo": valor_novo,
            "aplicado_em": agora or datetime.now(timezone.utc).isoformat(),
        }

        return {
            "acao": AcaoAutoUpdate.AUTO_UPDATE_APPLIED,
            "snapshot": snapshot,
            "conteudo_novo": conteudo_novo,
            "log": log,
        }

    except Exception as e:
        # Rollback lógico: nada foi persistido em lado nenhum, por isso
        # "reverter" é simplesmente devolver o snapshot intacto.
        return {
            "acao": AcaoAutoUpdate.ROLLED_BACK,
            "motivo": f"Erro durante a aplicação do update — revertido: {e}",
            "snapshot": snapshot,
            "conteudo": snapshot,
        }
