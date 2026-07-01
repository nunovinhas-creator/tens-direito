#!/usr/bin/env python3
"""
scripts/run_shadow_daily.py

Execução diária simplificada do Shadow Mode num único comando:

    python scripts/run_shadow_daily.py

Este script é APENAS um orquestrador — liga módulos já existentes, não
decide nada, não classifica nada, não altera nenhum resultado. Toda a
lógica de deteção/classificação/decisão já existe em
`verificar_datas.detectar_alertas` (usada aqui só para obter a lista de
alertas de hoje — sem chamar `verificar_datas.main()`, que escreveria
`data/alertas_datas.json`; aqui só se lê HTML, nunca se escreve nada
fora de `shadow_history/`). A partir daí, o fluxo é sempre:

    alertas -> shadow_mode.executar_shadow_mode
            -> shadow_mode_analytics.analisar_shadow_mode
            -> shadow_report_md.gerar_relatorio_markdown
            -> guardado em shadow_history/shadow_report_AAAA-MM-DD.md

Nenhum destes três módulos é alterado por este script — são só
importados e chamados com os dados que já produzem entre si.

Segurança:
- não introduz nenhuma lógica de decisão nova;
- não liga nem toca em `decisao_datas.AUTO_UPDATE_HABILITADO` — o
  auto-update simulado dentro do Shadow Mode continua exactamente como
  está configurado hoje;
- não faz chamadas de rede nem de GitHub (não importa `requests` nem
  qualquer biblioteca de acesso ao GitHub) — só lê ficheiros HTML locais
  e escreve um único ficheiro Markdown dentro de `shadow_history/`;
- a única escrita possível é dentro de `shadow_history/` — o caminho do
  ficheiro é sempre construído a partir dessa pasta, nunca de um
  caminho arbitrário vindo de fora, e é verificado antes de escrever.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shadow_mode import executar_shadow_mode
from shadow_mode_analytics import analisar_shadow_mode
from shadow_report_md import gerar_relatorio_markdown
from verificar_datas import AUTO_GERADOS, detectar_alertas

NOME_PASTA_HISTORICO = "shadow_history"


def calcular_raiz_repo() -> Path:
    """Raiz do repositório: um nível acima de `scripts/`."""
    return Path(__file__).resolve().parent.parent


def coletar_alertas_do_dia(raiz: Path, *, ano: int, mes: int) -> List[dict]:
    """Obtém a lista de alertas de hoje reutilizando
    `verificar_datas.detectar_alertas` (a mesma função já usada e testada
    na Camada 1) sobre cada HTML da raiz do repositório — só leitura,
    nunca chama `verificar_datas.main()` nem escreve nada."""
    alertas: List[dict] = []
    for caminho in sorted(raiz.glob("*.html")):
        if caminho.name in AUTO_GERADOS:
            continue
        try:
            conteudo = caminho.read_text(encoding="utf-8")
        except Exception:
            continue
        alerta = detectar_alertas(conteudo, caminho.name, ano, mes)
        if alerta:
            alertas.append(alerta)
    return alertas


def _caminho_historico(pasta_historico: Path, data_str: str) -> Path:
    caminho = pasta_historico / f"shadow_report_{data_str}.md"
    # Garantia estrutural: o ficheiro a escrever tem mesmo de estar
    # dentro da pasta de histórico -- nunca fora dela.
    if caminho.resolve().parent != pasta_historico.resolve():
        raise ValueError("caminho de histórico calculado fora da pasta shadow_history/")
    return caminho


def executar_shadow_daily(
    *,
    raiz: Optional[Path] = None,
    agora: Optional[datetime] = None,
    pasta_historico: Optional[Path] = None,
) -> Dict[str, Any]:
    """Orquestra o fluxo completo: recolhe os alertas de hoje, corre o
    Shadow Mode, calcula as métricas, gera o relatório em Markdown e
    guarda-o em `shadow_history/`. Devolve um dict com o texto do
    relatório, a análise e o caminho do ficheiro guardado.

    `raiz`, `agora` e `pasta_historico` são parâmetros de injecção para
    permitir testar isto sem tocar no repositório real nem depender do
    relógio do sistema — por omissão usam a raiz real do repositório e
    o momento actual.
    """
    raiz = raiz or calcular_raiz_repo()
    momento = agora or datetime.now()
    data_str = momento.strftime("%Y-%m-%d")

    alertas = coletar_alertas_do_dia(raiz, ano=momento.year, mes=momento.month)
    relatorios = executar_shadow_mode(alertas, agora=momento.isoformat())
    analise = analisar_shadow_mode(relatorios)
    texto_md = gerar_relatorio_markdown(analise, data=data_str)

    pasta = pasta_historico or (raiz / NOME_PASTA_HISTORICO)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_ficheiro = _caminho_historico(pasta, data_str)
    caminho_ficheiro.write_text(texto_md, encoding="utf-8")

    return {
        "relatorio_markdown": texto_md,
        "analytics": analise,
        "total_alertas": len(alertas),
        "caminho_historico": str(caminho_ficheiro),
    }


def main() -> None:
    print("✔ A recolher alertas e a correr o Shadow Mode...", file=sys.stderr)
    resultado = executar_shadow_daily()
    print("✔ Shadow Mode executado", file=sys.stderr)
    print("✔ Analytics calculado", file=sys.stderr)
    print("✔ Relatório Markdown gerado", file=sys.stderr)
    print(f"✔ Ficheiro guardado em {resultado['caminho_historico']}", file=sys.stderr)
    print(resultado["relatorio_markdown"])


if __name__ == "__main__":
    main()
