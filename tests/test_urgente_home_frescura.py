"""
Canário de frescura dos cartões "⏰ Datas a não perder" da homepage
(`.urgente-banda` em `index.html`).

Esta secção é 100% MANUAL — não tem marcadores de injecção
(`<!-- X:INICIO/FIM -->`), nenhum script em `scripts/` lhe toca, e
`scripts/verificar_datas.py` exclui `index.html` por inteiro
(`AUTO_GERADOS`) da sua varredura, porque o resto do ficheiro é gerido
pelo pipeline. Isso deixa esta secção manual sem nenhum guardrail —
foi assim que "Prazo 31 de julho" ficou publicado, marcado URGENTE,
com o prazo já passado há semanas (achado real, 2026-08-23).

Este teste fecha essa fresta: qualquer cartão que anuncie uma data
absoluta (dia + mês, com ou sem ano) já passada é um estado de erro a
parecer informação válida — ver CLAUDE.md "INVARIANTE — NENHUM ESTADO
DE ERRO PODE PARECER SUCESSO". FALHAR AQUI É O COMPORTAMENTO DESEJADO
sempre que ninguém actualizar um cartão a tempo — força revisão
consciente em vez de um prazo morto ficar visível indefinidamente.

Reutiliza a mesma lógica de supressão de `verificar_datas.py`
(`MARCADORES_HISTORICOS`) para nunca confundir uma data passada citada
como facto histórico ("em vigor desde 14 de agosto") com um prazo
morto anunciado como se ainda fosse accionável.
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from verificar_datas import MARCADORES_HISTORICOS, MESES  # noqa: E402

INDEX_HTML = (RAIZ / "index.html").read_text(encoding="utf-8")
HOJE = date.today()

REGEX_DATA_DIA_MES = re.compile(
    r"\b(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|"
    r"agosto|setembro|outubro|novembro|dezembro)(?:\s+de\s+(\d{4}))?\b",
    re.IGNORECASE,
)


def _cards_urgente_banda() -> list[str]:
    """Devolve o texto bruto (HTML) de cada `.urgente-card` de index.html."""
    m = re.search(
        r'<div class="urgente-cards"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        INDEX_HTML,
        re.S,
    )
    assert m, (
        "não encontrei .urgente-cards em index.html — a secção 'Datas a não "
        "perder' foi removida ou a estrutura mudou sem actualizar este canário"
    )
    corpo = m.group(1)
    cartoes = re.findall(
        r'<div class="urgente-card"[^>]*>(.*?)</div>\s*(?=<div class="urgente-card"|\Z)',
        corpo,
        re.S,
    )
    assert len(cartoes) >= 5, f"só encontrei {len(cartoes)} cartões — estrutura mudou?"
    return cartoes


def _titulo(card_html: str) -> str:
    m = re.search(r"<h3>(.*?)</h3>", card_html, re.S)
    return m.group(1).strip() if m else "(sem título)"


def _tem_marcador_historico(texto: str) -> bool:
    return any(re.search(p, texto, re.IGNORECASE) for p in MARCADORES_HISTORICOS)


def _datas_expiradas_sem_supressao(card_html: str) -> list[str]:
    """Datas dia+mês(+ano) do cartão já passadas e não suprimidas por um
    marcador histórico (ex.: 'em vigor desde', 'já ...')."""
    expiradas = []
    for m in REGEX_DATA_DIA_MES.finditer(card_html):
        dia = int(m.group(1))
        mes = MESES[m.group(2).lower()]
        ano = int(m.group(3)) if m.group(3) else HOJE.year
        try:
            data = date(ano, mes, dia)
        except ValueError:
            continue  # data inválida (ex.: 31 de fevereiro) — não é uma data real
        if data < HOJE and not _tem_marcador_historico(card_html):
            expiradas.append(m.group(0))
    return expiradas


def test_nenhum_cartao_de_urgente_banda_anuncia_prazo_ja_passado():
    cartoes = _cards_urgente_banda()
    falhas = []
    for card in cartoes:
        expiradas = _datas_expiradas_sem_supressao(card)
        if expiradas:
            falhas.append(f"{_titulo(card)!r}: {', '.join(expiradas)}")

    assert not falhas, (
        "cartão(ões) de '⏰ Datas a não perder' (index.html) anunciam uma "
        "data já passada, sem contexto histórico que a explique — "
        "actualiza o texto (ver CLAUDE.md secção 'INVARIANTE') antes de "
        "publicar:\n  - " + "\n  - ".join(falhas)
    )


def test_badge_urgente_nunca_acompanha_prazo_ja_passado():
    """Verificação mais estrita e directa do bug real (2026-08-23): um
    badge 'URGENTE' ao lado de uma data-limite que já passou é sempre um
    erro, mesmo que a data em si esteja tecnicamente coberta por algum
    marcador (que nunca deveria aparecer junto de um badge de urgência)."""
    cartoes = _cards_urgente_banda()
    falhas = []
    for card in cartoes:
        if "URGENTE" not in card:
            continue
        for m in REGEX_DATA_DIA_MES.finditer(card):
            dia = int(m.group(1))
            mes = MESES[m.group(2).lower()]
            ano = int(m.group(3)) if m.group(3) else HOJE.year
            try:
                data = date(ano, mes, dia)
            except ValueError:
                continue
            if data < HOJE:
                falhas.append(f"{_titulo(card)!r}: badge URGENTE + {m.group(0)!r} (já passou)")

    assert not falhas, "badge URGENTE junto de um prazo já expirado:\n  - " + "\n  - ".join(falhas)
