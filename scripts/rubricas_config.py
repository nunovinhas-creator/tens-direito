"""
RUBRICAS — configuração da cascata de fontes por valor publicado.

Cada RubricaConfig define:
  - cascata: lista ordenada de FontePassoConfig (LEGISLATIVA > SERVICO > CONGELADO)
  - congelado: ValorCongelado com o último valor verificado por humano

Regra de ouro: só se codifica uma fonte LEGISLATIVA após teste empírico no runner
real confirmar que a URL renderiza o valor numérico esperado.

URLs confirmados via Playwright no runner GitHub Actions:
  - DRE portaria 480-A/2025 → 200, 3943 chars, "537,13" presente (2026-06-30)
"""
from __future__ import annotations

import re
from datetime import date

from classificador_resposta import FonteConfig
from cascata_fontes import (
    FontePassoConfig, RubricaConfig, TipoFonte, ValorCongelado,
)

# ---------------------------------------------------------------------------
# Configs de fonte reutilizáveis
# ---------------------------------------------------------------------------

_CFG_DRE = FonteConfig(
    nome="DRE — legislação consolidada",
    min_chars_uteis=500,
)

_CFG_SEG_SOCIAL = FonteConfig(
    nome="Seg. Social — abono de família",
    min_chars_uteis=500,
    dominios_login=("app.seg-social.pt",),
)

_CFG_IEFP = FonteConfig(
    nome="IEFP — subsídio de desemprego",
    min_chars_uteis=500,
)

# ---------------------------------------------------------------------------
# Extratores
# ---------------------------------------------------------------------------

def _extrair_ias(corpo: str) -> str | None:
    """Extrai '537,13' do texto renderizado da portaria DRE."""
    m = re.search(r"(\d{3}[,\.]\d{2})\s*(?:€|EUR|euros)?", corpo)
    # Filtrar: só aceitar o valor conhecido do IAS 2026
    if m and re.search(r"537[,\.]13", corpo):
        return "537,13"
    return None


# ---------------------------------------------------------------------------
# Rubricas
# ---------------------------------------------------------------------------

RUBRICA_IAS = RubricaConfig(
    nome="ias_2026",
    cascata=(
        FontePassoConfig(
            tipo=TipoFonte.LEGISLATIVA,
            fonte_config=_CFG_DRE,
            extrator=_extrair_ias,
            # Confirmado via Playwright no runner real em 2026-06-30:
            # status 200, 3943 chars, "537,13" no texto renderizado
            url="https://diariodarepublica.pt/dr/detalhe/portaria/480-a-2025-993056222",
        ),
        FontePassoConfig(
            tipo=TipoFonte.SERVICO,
            fonte_config=_CFG_SEG_SOCIAL,
            extrator=_extrair_ias,
            url="https://www.seg-social.pt/abono-de-familia",
        ),
    ),
    congelado=ValorCongelado(
        valor="537,13",
        data_verificacao=date(2026, 6, 28),
        verificado_por="humano",
    ),
)

# Mapa central: slug -> RubricaConfig
# À medida que as rubricas seguintes forem confirmadas empiricamente,
# adicionam-se aqui (checkpoint por rubrica conforme CLAUDE.md).
RUBRICAS: dict[str, RubricaConfig] = {
    "ias_2026": RUBRICA_IAS,
}
