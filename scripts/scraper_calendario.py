"""
Scraper do calendário oficial de pagamentos da Segurança Social.

Fonte (confirmada num runner real a 2026-07-12, ver docs/FONTE-CALENDARIO.md):
    https://www.seg-social.pt/ptss/pssd/pagamentos
— página PÚBLICA (não redirecciona para o gateway de login), SPA
OutSystems com um separador por mês ("junho 2026", "julho 2026",
"agosto 2026", …). Ao clicar num separador, a página mostra a tabela
desse mês: por cada dia, as prestações pagas e o método (transferência
bancária / vale de correio). As datas são publicadas antes do início do
mês (agosto já estava lá a meio de julho).

Estrutura de saída (schema de data/calendario_pagamentos.json):
    {"ano": 2026, "mes": 8, "pagamentos": [
        {"dia": 3, "prestacoes": ["doenca_profissional"],
         "metodo": ["transferencia_bancaria", "vale_de_correio"]}, ...]}

INVARIANTE (ver CLAUDE.md "NENHUM ESTADO DE ERRO PODE PARECER SUCESSO"):
uma prestação cujo nome não esteja no mapa `NOME_PARA_SLUG` faz o scraper
FALHAR (`ScraperError`), nunca é descartada em silêncio nem adivinhada —
o fluxo mensal cai então para a Issue manual, com o nome desconhecido no
relatório. O mesmo para um mês sem dias, ou um dia sem prestações.

O parsing (`parse_innertext`) é uma função PURA sobre o texto visível do
painel do mês — testável sem rede (tests/test_scraper_calendario.py usa
o texto real capturado no diagnóstico). Só `raspar_mes` toca na rede.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata

BASE = "https://www.seg-social.pt"
URL = f"{BASE}/ptss/pssd/pagamentos"

MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
# Abreviatura de 3 letras que a página usa no cabeçalho de cada dia (ex.: "03 AGO").
ABREV_MES = [
    "", "JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
    "JUL", "AGO", "SET", "OUT", "NOV", "DEZ",
]


class ScraperError(RuntimeError):
    """Falha explícita — nunca engolida. O fluxo mensal cai para a Issue manual."""


def _norm(s: str) -> str:
    """minúsculas, sem acentos, espaços colapsados, sem pontuação de fim —
    para o mapa de nomes ser robusto a variações triviais do portal."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("º", "").replace("ª", "")
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


# Nome no portal (normalizado) → slug da allow-list PRESTACOES de
# atualizar_calendario.py. Curado a partir do conteúdo real do diagnóstico.
NOME_PARA_SLUG = {
    _norm("Doença Profissional: pensões e subsídios"): "doenca_profissional",
    _norm("Rendas"): "apoio_renda",
    _norm("Pensões"): "pensoes",
    _norm("Complemento Solidário para Idosos"): "csi",
    _norm("Reembolso de Despesas de Funeral"): "reembolso_despesas_funeral",
    _norm("Prestação Social para a Inclusão"): "psi",
    _norm("Prestações familiares"): "prestacoes_familiares",
    _norm("1º pagamento desemprego / doença / parentalidade / ação social"):
        "desemprego_doenca_parentalidade_acao_social_1",
    _norm("2º pagamento desemprego / doença / parentalidade / ação social"):
        "desemprego_doenca_parentalidade_acao_social_2",
    _norm("Subsídio por Suspensão da Atividade Cultural"):
        "subsidio_suspensao_atividade_cultural",
    _norm("Fundo de Garantia de Alimentos Devidos a Menores"): "fgadm",
    _norm("Fundo de Garantia Salarial"): "fgs",
    _norm("Rendimento Social de Inserção"): "rsi",
    _norm("Subsídio de Apoio ao Cuidador Informal"): "cuidador_informal",
}

_RE_DIA_CABECALHO = re.compile(r"^(\d{1,2})\s+([A-Z]{3})$")
_RE_FRAGMENTO = re.compile(r"^(\d{1,2}|[A-Z]{3})$")  # os "03"/"AGO" partidos
_SENTINELA_FIM = "a sua opiniao e importante"


def _mapear_metodo(linha: str) -> list[str]:
    tem_transf = "transferencia" in _norm(linha)
    tem_vale = "vale de correio" in _norm(linha)
    metodo = []
    if tem_transf:
        metodo.append("transferencia_bancaria")
    if tem_vale:
        metodo.append("vale_de_correio")
    return metodo


def _e_metodo(linha: str) -> bool:
    return bool(_mapear_metodo(linha))


def parse_innertext(texto: str, ano: int, mes: int) -> dict:
    """Converte o texto visível do painel do mês na estrutura do JSON.

    Função pura (sem rede) — o coração testável do scraper. Levanta
    ScraperError em qualquer situação ambígua ou incompleta.
    """
    if not (1 <= mes <= 12):
        raise ScraperError(f"mês inválido: {mes}")
    abbr = ABREV_MES[mes]
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]

    pagamentos: dict[int, list[dict]] = {}
    dia_atual: int | None = None
    prestacao_pendente: str | None = None
    nomes_desconhecidos: list[str] = []
    viu_cabecalho = False

    for linha in linhas:
        if _norm(linha) == _SENTINELA_FIM:
            break

        m = _RE_DIA_CABECALHO.match(linha)
        if m:
            # cabeçalho de dia — só conta se for do mês alvo (nunca mistura meses)
            if m.group(2).upper() == abbr:
                dia_atual = int(m.group(1))
                pagamentos.setdefault(dia_atual, [])
                prestacao_pendente = None
                viu_cabecalho = True
            else:
                dia_atual = None  # dia de outro mês (não devia aparecer no painel activo)
            continue

        if dia_atual is None or not viu_cabecalho:
            continue  # ainda na navegação/separadores, antes do 1.º dia

        if _RE_FRAGMENTO.match(linha):
            continue  # os "03"/"AGO" partidos do cabeçalho visual

        if _e_metodo(linha):
            if prestacao_pendente is None:
                # método sem prestação antes — layout inesperado, falha alto
                raise ScraperError(
                    f"método '{linha}' sem prestação associada no dia {dia_atual}"
                )
            slug = NOME_PARA_SLUG.get(_norm(prestacao_pendente))
            if slug is None:
                nomes_desconhecidos.append(prestacao_pendente)
            else:
                pagamentos[dia_atual].append({"slug": slug, "metodo": _mapear_metodo(linha)})
            prestacao_pendente = None
        else:
            prestacao_pendente = linha

    if nomes_desconhecidos:
        raise ScraperError(
            "prestação(ões) fora da allow-list NOME_PARA_SLUG (nunca descartar "
            "em silêncio — acrescentar o mapeamento ou tratar manualmente): "
            + "; ".join(sorted(set(nomes_desconhecidos)))
        )
    if not pagamentos:
        raise ScraperError(
            f"nenhum dia de pagamento extraído para {MESES_PT[mes]} de {ano} — "
            "o separador do mês pode não ter carregado ou o layout mudou"
        )

    # agrupar por dia, deduplicar slugs preservando ordem, validar
    lista = []
    for dia in sorted(pagamentos):
        itens = pagamentos[dia]
        if not itens:
            raise ScraperError(f"dia {dia} sem prestações extraídas")
        slugs, metodos_por_slug = [], {}
        for it in itens:
            if it["slug"] not in metodos_por_slug:
                slugs.append(it["slug"])
                metodos_por_slug[it["slug"]] = it["metodo"]
        # método do dia = união dos métodos das suas prestações, ordem canónica
        metodo_dia = []
        for mm in ("transferencia_bancaria", "vale_de_correio"):
            if any(mm in metodos_por_slug[s] for s in slugs):
                metodo_dia.append(mm)
        lista.append({"dia": dia, "prestacoes": slugs, "metodo": metodo_dia})

    return {"ano": ano, "mes": mes, "pagamentos": lista}


def raspar_mes(ano: int, mes: int, timeout_ms: int = 45000) -> dict:
    """Abre a página, clica no separador do mês alvo e devolve a estrutura
    do JSON. Só aqui há rede. Levanta ScraperError se o mês não existir na
    página ou o conteúdo não carregar."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # pragma: no cover
        raise ScraperError(f"Playwright indisponível: {e}") from e

    rotulo = f"{MESES_PT[mes]} {ano}"
    abbr = ABREV_MES[mes]
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        try:
            page = browser.new_context(
                locale="pt-PT", timezone_id="Europe/Lisbon"
            ).new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=timeout_ms)
            # esperar pelos separadores de mês
            try:
                page.wait_for_function(
                    "r => new RegExp(r, 'i').test(document.body.innerText)",
                    arg=rf"{MESES_PT[mes]}\s+{ano}", timeout=20000,
                )
            except Exception as e:
                raise ScraperError(
                    f"separador '{rotulo}' não apareceu na página — o mês pode "
                    f"ainda não estar publicado pela Segurança Social"
                ) from e
            # clicar no separador do mês
            try:
                page.get_by_text(
                    re.compile(rf"^\s*{MESES_PT[mes]}\s+{ano}\s*$", re.I)
                ).first.click(timeout=10000)
            except Exception as e:
                raise ScraperError(f"não consegui clicar no separador '{rotulo}': {e}") from e
            # esperar que apareça pelo menos um cabeçalho de dia do mês
            try:
                page.wait_for_function(
                    "r => new RegExp(r).test(document.body.innerText)",
                    arg=rf"\b\d{{1,2}}\s+{abbr}\b", timeout=15000,
                )
            except Exception as e:
                raise ScraperError(
                    f"a tabela de {rotulo} não carregou após clicar no separador"
                ) from e
            texto = page.evaluate("document.body ? document.body.innerText : ''")
        finally:
            browser.close()
    return parse_innertext(texto, ano, mes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ano", type=int, required=True)
    parser.add_argument("--mes", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        mes = raspar_mes(args.ano, args.mes)
    except ScraperError as e:
        print(f"ScraperError: {e}", file=sys.stderr)
        return 2
    print(json.dumps(mes, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
