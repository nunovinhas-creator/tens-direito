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
  qualquer biblioteca de acesso ao GitHub) — só lê ficheiros HTML/JSON
  locais (`data/pagina_fonte.json`, `data/estado_fontes.json`,
  `data/scraped/*.json` — todos escritos pelo pipeline diário, nunca por
  este script) e escreve um único ficheiro Markdown dentro de
  `shadow_history/`;
- `calcular_carimbos_elegiveis` (Fase 4) simula quais páginas SERIAM
  elegíveis para revalidação de carimbo se `decisao_datas.REVALIDACAO_CARIMBO_HABILITADA`
  estivesse ligada — nunca liga essa flag, nunca chama
  `auto_update_engine.aplicar_refresh_carimbo`, só a verificação pura de
  elegibilidade (`elegivel_refresh_carimbo`);
- a única escrita possível é dentro de `shadow_history/` — o caminho do
  ficheiro é sempre construído a partir dessa pasta, nunca de um
  caminho arbitrário vindo de fora, e é verificado antes de escrever.

Diagnóstico "0 alertas" (2026-07-02): este script já nunca dependeu de
`data/alertas_datas.json` gerado por outro workflow (só o pipeline
diário escreve esse ficheiro) — `coletar_alertas_do_dia` sempre correu
`verificar_datas.detectar_alertas` sobre o próprio checkout, em
runtime. Confirmado que os relatórios "0 alertas" de 2026-07-01/02
reflectiam o estado real: o commit `eeefa1c` (correcção de falsos
positivos em `verificar_datas.py`) tornou zero alertas genuinamente
verdadeiro para o conteúdo actual — não é um bug de leitura de dados.
Continua a não haver garantia, só por "0", de que a Camada 1 está de
facto a correr (poderia estar a falhar silenciosamente) — por isso
`executar_shadow_daily` passa agora `paginas_analisadas`/
`hora_execucao_utc` a `shadow_report_md.gerar_relatorio_markdown`, que
marca 0 alertas com muitas páginas analisadas como anomalia explícita
em vez de "sistema estável" (ver `LIMIAR_ANOMALIA_PAGINAS`).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from auto_update_engine import elegivel_refresh_carimbo
from shadow_mode import executar_shadow_mode
from shadow_mode_analytics import analisar_shadow_mode
from shadow_report_md import gerar_relatorio_markdown
from verificar_datas import AUTO_GERADOS, detectar_alertas

NOME_PASTA_HISTORICO = "shadow_history"


def calcular_raiz_repo() -> Path:
    """Raiz do repositório: um nível acima de `scripts/`."""
    return Path(__file__).resolve().parent.parent


def _paginas_elegiveis(raiz: Path) -> List[Path]:
    """Páginas HTML sujeitas a deteção de datas — as mesmas que
    `coletar_alertas_do_dia` percorre, sem os ficheiros que o pipeline
    gera (`AUTO_GERADOS`). Extraída à parte para que o total de páginas
    analisadas (usado na proveniência do relatório) venha sempre da
    mesma fonte que a própria deteção, nunca de uma contagem paralela
    que possa divergir dela. Desde 2026-07-07 cobre também `p/` e
    `documentos/` — o mesmo âmbito de `verificar_datas.main()`, que
    mudou no mesmo commit (têm de mudar sempre juntos)."""
    paginas = (sorted(raiz.glob("*.html"))
               + sorted((raiz / "p").glob("*.html"))
               + sorted((raiz / "documentos").glob("*.html")))
    return [caminho for caminho in paginas if caminho.name not in AUTO_GERADOS]


def coletar_alertas_do_dia(raiz: Path, *, ano: int, mes: int) -> List[dict]:
    """Obtém a lista de alertas de hoje reutilizando
    `verificar_datas.detectar_alertas` (a mesma função já usada e testada
    na Camada 1) sobre cada HTML servido (raiz, p/, documentos/) — só
    leitura, nunca chama `verificar_datas.main()` nem escreve nada."""
    alertas: List[dict] = []
    for caminho in _paginas_elegiveis(raiz):
        try:
            conteudo = caminho.read_text(encoding="utf-8")
        except Exception:
            continue
        alerta = detectar_alertas(conteudo, caminho.relative_to(raiz).as_posix(), ano, mes)
        if alerta:
            alertas.append(alerta)
    return alertas


def _carregar_json(caminho: Path) -> dict:
    if not caminho.exists():
        return {}
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        return conteudo if isinstance(conteudo, dict) else {}
    except Exception:
        return {}


def _hash_fonte(scraped_dir: Path, slug: str, data_str: str) -> Optional[str]:
    dados = _carregar_json(scraped_dir / f"{slug}_{data_str}.json")
    return dados.get("hash_conteudo")


def calcular_carimbos_elegiveis(raiz: Path, *, hoje: str, ontem: str) -> List[str]:
    """Simulação diária (Fase 4 -- `decisao_datas.REVALIDACAO_CARIMBO_HABILITADA`
    continua sempre False em produção; esta função nunca aplica nada, só
    reporta quais páginas SERIAM elegíveis hoje se estivesse ligada).

    Para cada página em `data/pagina_fonte.json`, todas as fontes de que
    depende têm de estar `OK` hoje em `data/estado_fontes.json` (nunca
    `OK_VIA_ARQUIVO`/`BLOQUEADO`) e o hash de cada fonte tem de estar
    inalterado face ao scrape do dia anterior -- aproximação de "a fonte
    não mudou recentemente" (não é o mesmo que "desde a última edição
    manual da página"; ver CLAUDE.md "REVALIDAÇÃO DE CARIMBO" para a
    ressalva sobre esta simplificação). Só leitura -- nunca chama
    `auto_update_engine.aplicar_refresh_carimbo`, só a verificação de
    elegibilidade."""
    pagina_fonte = _carregar_json(raiz / "data" / "pagina_fonte.json")
    estado_fontes = _carregar_json(raiz / "data" / "estado_fontes.json")
    scraped_dir = raiz / "data" / "scraped"

    elegiveis: List[str] = []
    for pagina, fontes in pagina_fonte.items():
        if not isinstance(fontes, list) or not fontes:
            continue

        todas_ok = all((estado_fontes.get(slug) or {}).get("estado") == "OK" for slug in fontes)
        if not todas_ok:
            continue

        hashes_inalterados = True
        for slug in fontes:
            hash_hoje = _hash_fonte(scraped_dir, slug, hoje)
            hash_ontem = _hash_fonte(scraped_dir, slug, ontem)
            if hash_hoje is None or hash_hoje != hash_ontem:
                hashes_inalterados = False
                break

        if elegivel_refresh_carimbo("OK", hashes_inalterados):
            elegiveis.append(pagina)

    return sorted(elegiveis)


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

    paginas_analisadas = len(_paginas_elegiveis(raiz))
    alertas = coletar_alertas_do_dia(raiz, ano=momento.year, mes=momento.month)
    relatorios = executar_shadow_mode(alertas, agora=momento.isoformat())
    analise = analisar_shadow_mode(relatorios)
    proveniencia = {
        "paginas_analisadas": paginas_analisadas,
        "hora_execucao_utc": momento.strftime("%H:%M"),
    }
    ontem_str = (momento - timedelta(days=1)).strftime("%Y-%m-%d")
    carimbos_elegiveis = calcular_carimbos_elegiveis(raiz, hoje=data_str, ontem=ontem_str)
    texto_md = gerar_relatorio_markdown(
        analise, data=data_str, proveniencia=proveniencia, carimbos_elegiveis=carimbos_elegiveis
    )

    pasta = pasta_historico or (raiz / NOME_PASTA_HISTORICO)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho_ficheiro = _caminho_historico(pasta, data_str)
    caminho_ficheiro.write_text(texto_md, encoding="utf-8")

    return {
        "relatorio_markdown": texto_md,
        "analytics": analise,
        "total_alertas": len(alertas),
        "paginas_analisadas": paginas_analisadas,
        "carimbos_elegiveis": carimbos_elegiveis,
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
