"""
Injecção idempotente do calendário de pagamentos da Segurança Social.

Lê data/calendario_pagamentos.json (fonte de verdade — nunca datas de
memória; ver docs/FONTE-CALENDARIO.md) e reescreve APENAS as duas zonas
marcadas de calendario-pagamentos-seguranca-social.html:

  <!-- CAL:META:INICIO -->  ... <!-- CAL:META:FIM -->   (title + meta description)
  <!-- CAL:CORPO:INICIO --> ... <!-- CAL:CORPO:FIM -->  (tabelas do mês)

Invariante crítico (CALENDARIO-PAGAMENTOS-SPEC.md): a página NUNCA
mostra um mês passado como se fosse o corrente. Se o JSON não tiver o
mês corrente, a zona CAL:CORPO degrada para um bloco explícito
"consultar a fonte oficial" (com link) — nunca uma tabela velha
silenciosa. Meses passados podem ficar no JSON (histórico) mas nunca
são renderizados.

Validações duras antes de escrever (allow-list de prestações, dias
1-31, listas não vazias) — qualquer falha sai com exit != 0 sem tocar
no HTML, nunca commit parcial (padrão do guardrail existente).

Uso (sessão manual ou workflow da Fase 3):
    python scripts/atualizar_calendario.py            # aplica
    python scripts/atualizar_calendario.py --dry-run  # só relata
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "data" / "calendario_pagamentos.json"
PAGINA = RAIZ / "calendario-pagamentos-seguranca-social.html"

FONTE_OFICIAL_FALLBACK = "https://www.seg-social.pt"

# Allow-list de prestações conhecidas (slug -> nome apresentado).
# Um slug fora desta lista falha a validação — nunca é renderizado às
# cegas (mesmo padrão do guardrail de escrever_ficheiro_seguro).
PRESTACOES = {
    "doenca_profissional": "Pensões e subsídios por doença profissional",
    "apoio_renda": "Apoio extraordinário à renda",
    "pensoes": "Pensões",
    "csi": "Complemento Solidário para Idosos (CSI)",
    "reembolso_despesas_funeral": "Reembolso de despesas de funeral",
    "psi": "Prestação Social para a Inclusão (PSI)",
    "prestacoes_familiares": "Abono de família e outras prestações familiares",
    "desemprego_doenca_parentalidade_acao_social_1":
        "1.º pagamento — subsídio de desemprego, doença, parentalidade e ação social",
    "desemprego_doenca_parentalidade_acao_social_2":
        "2.º pagamento — subsídio de desemprego, doença, parentalidade e ação social",
    "fgadm": "Fundo de Garantia de Alimentos Devidos a Menores",
    "rsi": "Rendimento Social de Inserção (RSI)",
    "fgs": "Fundo de Garantia Salarial",
    "cuidador_informal": "Subsídio de apoio ao cuidador informal",
}

METODOS = {
    "transferencia_bancaria": "transferência bancária",
    "vale_de_correio": "vale de correio",
}

# Secção "Por prestação" — âncoras exigidas pela spec + guia interno.
# (anchor, nome curto, slugs que contam, rótulo por slug quando há mais
# de um, url do guia interno ou None)
_ROTULO_SLUG = {
    "desemprego_doenca_parentalidade_acao_social_1": "1.º pagamento",
    "desemprego_doenca_parentalidade_acao_social_2": "2.º pagamento",
}
VISTA_PRESTACOES = [
    ("pensoes", "Pensões", ["pensoes"], None),
    ("csi", "Complemento Solidário para Idosos (CSI)", ["csi"],
     "/complemento-solidario-idosos.html"),
    ("psi", "Prestação Social para a Inclusão (PSI)", ["psi"],
     "/prestacao-social-para-a-inclusao.html"),
    ("abono-familia", "Abono de família e prestações familiares",
     ["prestacoes_familiares"], "/abono-de-familia.html"),
    ("subsidio-desemprego", "Subsídio de desemprego",
     ["desemprego_doenca_parentalidade_acao_social_1",
      "desemprego_doenca_parentalidade_acao_social_2"],
     "/subsidio-desemprego.html"),
    ("subsidio-doenca", "Subsídio de doença (baixa médica)",
     ["desemprego_doenca_parentalidade_acao_social_1",
      "desemprego_doenca_parentalidade_acao_social_2"],
     "/baixa-medica-subsidio-doenca.html"),
    ("rsi", "Rendimento Social de Inserção (RSI)", ["rsi"], "/rsi.html"),
    ("apoio-renda", "Apoio extraordinário à renda", ["apoio_renda"],
     "/apoio-extraordinario-renda.html"),
    ("cuidador-informal", "Subsídio de apoio ao cuidador informal",
     ["cuidador_informal"], "/cuidador-informal.html"),
]

MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


# ── dados ────────────────────────────────────────────────────────────────


def carregar_dados(caminho: Path = DADOS) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def validar_dados(dados: dict) -> list[str]:
    """Lista de problemas — vazia se os dados forem publicáveis."""
    problemas: list[str] = []
    meses = dados.get("meses")
    if not isinstance(meses, list):
        return ["'meses' em falta ou não é lista"]
    if not dados.get("fonte_url", "").startswith("https://www.seg-social.pt"):
        problemas.append("'fonte_url' em falta ou fora de seg-social.pt")
    vistos = set()
    for m in meses:
        ano, mes = m.get("ano"), m.get("mes")
        if not (isinstance(ano, int) and 2020 <= ano <= 2100):
            problemas.append(f"ano inválido: {ano!r}")
            continue
        if not (isinstance(mes, int) and 1 <= mes <= 12):
            problemas.append(f"mês inválido: {mes!r}")
            continue
        if (ano, mes) in vistos:
            problemas.append(f"mês duplicado: {ano}-{mes:02d}")
        vistos.add((ano, mes))
        pagamentos = m.get("pagamentos")
        if not isinstance(pagamentos, list) or not pagamentos:
            problemas.append(f"{ano}-{mes:02d}: 'pagamentos' vazio ou em falta")
            continue
        for p in pagamentos:
            dia = p.get("dia")
            if not (isinstance(dia, int) and 1 <= dia <= 31):
                problemas.append(f"{ano}-{mes:02d}: dia inválido {dia!r}")
            prest = p.get("prestacoes")
            if not isinstance(prest, list) or not prest:
                problemas.append(f"{ano}-{mes:02d} dia {dia}: 'prestacoes' vazio")
            else:
                for s in prest:
                    if s not in PRESTACOES:
                        problemas.append(
                            f"{ano}-{mes:02d} dia {dia}: prestação desconhecida "
                            f"'{s}' (fora da allow-list PRESTACOES)"
                        )
            metodo = p.get("metodo")
            if not isinstance(metodo, list) or not metodo:
                problemas.append(f"{ano}-{mes:02d} dia {dia}: 'metodo' vazio")
            else:
                for mm in metodo:
                    if mm not in METODOS:
                        problemas.append(
                            f"{ano}-{mes:02d} dia {dia}: método desconhecido '{mm}'"
                        )
    return problemas


def hoje_lisboa() -> dt.date:
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Lisbon")).date()
    except Exception:  # zoneinfo indisponível — data local serve
        return dt.date.today()


def _encontrar_mes(dados: dict, ano: int, mes: int) -> dict | None:
    for m in dados.get("meses", []):
        if m.get("ano") == ano and m.get("mes") == mes:
            return m
    return None


def _mes_seguinte(ano: int, mes: int) -> tuple[int, int]:
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def nome_mes(ano: int, mes: int) -> str:
    return f"{MESES_PT[mes]} de {ano}"


# ── render ───────────────────────────────────────────────────────────────


def _metodo_txt(metodo: list[str]) -> str:
    nomes = [METODOS[m] for m in metodo if m in METODOS]
    if len(nomes) == 1:
        return f"Só {nomes[0]}"
    return " e ".join([", ".join(nomes[:-1])] + nomes[-1:]).capitalize()


def _tabela_mes(m: dict) -> str:
    linhas = []
    for p in sorted(m["pagamentos"], key=lambda x: x["dia"]):
        nomes = "<br>".join(html.escape(PRESTACOES[s]) for s in p["prestacoes"])
        nota = p.get("nota")
        if nota:
            nomes += (
                '<br><span class="cal-nota">'
                + html.escape(nota)
                + "</span>"
            )
        linhas.append(
            "      <tr>\n"
            f'        <td class="cal-dia">{p["dia"]}</td>\n'
            f"        <td>{nomes}</td>\n"
            f"        <td>{html.escape(_metodo_txt(p['metodo']))}</td>\n"
            "      </tr>"
        )
    corpo = "\n".join(linhas)
    return (
        '  <div class="tabela-wrap">\n'
        '    <table class="cal-tabela">\n'
        "      <thead>\n"
        "      <tr>\n"
        '        <th scope="col">Dia</th>\n'
        '        <th scope="col">Prestações pagas</th>\n'
        '        <th scope="col">Método de pagamento</th>\n'
        "      </tr>\n"
        "      </thead>\n"
        "      <tbody>\n"
        f"{corpo}\n"
        "      </tbody>\n"
        "    </table>\n"
        "  </div>"
    )


def _dias_por_slug(m: dict) -> dict[str, list[int]]:
    dias: dict[str, list[int]] = {}
    for p in m["pagamentos"]:
        for s in p["prestacoes"]:
            dias.setdefault(s, []).append(p["dia"])
    return dias


def _seccao_por_prestacao(m: dict) -> str:
    """Tabela 'Quando recebo a minha prestação?' com as âncoras da spec."""
    dias = _dias_por_slug(m)
    mes_txt = MESES_PT[m["mes"]]
    linhas = []
    for anchor, nome, slugs, url in VISTA_PRESTACOES:
        partes = []
        for s in slugs:
            for d in dias.get(s, []):
                rotulo = _ROTULO_SLUG.get(s)
                partes.append(
                    f"{d} de {mes_txt}" + (f" ({rotulo})" if rotulo else "")
                )
        if not partes:
            # Prestação sem data neste mês — nunca inventar: estado explícito.
            datas_txt = (
                "sem data no calendário deste mês — "
                '<a href="' + html.escape(FONTE_OFICIAL_FALLBACK)
                + '" target="_blank" rel="noopener">consulta a Segurança Social</a>'
            )
        else:
            datas_txt = " · ".join(html.escape(t) for t in partes)
        nome_html = html.escape(nome)
        if url:
            nome_html += (
                f'<br><a class="cal-guia" href="{html.escape(url)}">Ver o guia →</a>'
            )
        linhas.append(
            f'      <tr id="{anchor}">\n'
            f'        <th scope="row">{nome_html}</th>\n'
            f"        <td>{datas_txt}</td>\n"
            "      </tr>"
        )
    corpo = "\n".join(linhas)
    return (
        '  <h2 id="por-prestacao">Quando recebo a minha prestação?</h2>\n'
        '  <div class="tabela-wrap">\n'
        '    <table class="cal-tabela cal-tabela-prestacoes">\n'
        "      <thead>\n"
        "      <tr>\n"
        '        <th scope="col">Prestação</th>\n'
        f'        <th scope="col">Data em {html.escape(mes_txt)}</th>\n'
        "      </tr>\n"
        "      </thead>\n"
        "      <tbody>\n"
        f"{corpo}\n"
        "      </tbody>\n"
        "    </table>\n"
        "  </div>"
    )


def _bloco_degradado(dados: dict, ano: int, mes: int) -> str:
    fonte = html.escape(dados.get("fonte_url") or FONTE_OFICIAL_FALLBACK)
    return (
        '<div id="cal-corrente" data-mes="" class="cal-degradado" role="alert">\n'
        f"  <strong>⚠️ Ainda não temos o calendário verificado de {html.escape(nome_mes(ano, mes))}.</strong>\n"
        "  <p>Para não te mostrar datas erradas ou antigas, esta página só publica o calendário\n"
        "  depois de o confirmar na fonte oficial. Consulta as datas directamente na\n"
        f'  <a href="{fonte}" target="_blank" rel="noopener">Segurança Social</a>\n'
        "  ou na Segurança Social Direta (Conta-corrente → Pagamentos).</p>\n"
        "</div>"
    )


def render_corpo(dados: dict, hoje: dt.date) -> str:
    """Zona CAL:CORPO — mês corrente (ou estado degradado) + mês seguinte."""
    ano_a, mes_a = hoje.year, hoje.month
    ano_s, mes_s = _mes_seguinte(ano_a, mes_a)
    atual = _encontrar_mes(dados, ano_a, mes_a)
    seguinte = _encontrar_mes(dados, ano_s, mes_s)

    blocos: list[str] = []
    if atual:
        blocos.append(
            f'<div id="cal-corrente" data-mes="{ano_a}-{mes_a:02d}">\n'
            f'  <h2 id="mes-corrente">Calendário de {html.escape(nome_mes(ano_a, mes_a))}</h2>\n'
            f"{_tabela_mes(atual)}\n"
            f"{_seccao_por_prestacao(atual)}\n"
            "</div>"
        )
    else:
        blocos.append(_bloco_degradado(dados, ano_a, mes_a))

    if seguinte:
        blocos.append(
            f'<div id="cal-seguinte">\n'
            f'  <h2 id="mes-seguinte">Calendário de {html.escape(nome_mes(ano_s, mes_s))}</h2>\n'
            f"{_tabela_mes(seguinte)}\n"
            "</div>"
        )
    elif atual:
        blocos.append(
            '<p class="cal-proximo-mes">O calendário de '
            + html.escape(nome_mes(ano_s, mes_s))
            + " ainda não foi confirmado na fonte oficial — é publicado aqui assim que a"
            " Segurança Social o divulgar.</p>"
        )

    atualizado = html.escape(dados.get("atualizado_em", ""))
    fonte = html.escape(dados.get("fonte_url") or FONTE_OFICIAL_FALLBACK)
    blocos.append(
        '<p class="cal-fonte-inline">Fonte: <a href="'
        + fonte
        + '" target="_blank" rel="noopener">Segurança Social</a> · dados verificados a '
        + atualizado
        + "</p>"
    )
    return "\n\n".join(blocos)


def render_meta(dados: dict, hoje: dt.date) -> str:
    """Zona CAL:META — <title> + meta description com o mês corrente.

    Sem mês corrente no JSON, degrada para o ano (nunca um mês velho).
    O og:title fica FORA desta zona, estável — ver docs/FONTE-CALENDARIO.md.
    """
    atual = _encontrar_mes(dados, hoje.year, hoje.month)
    if atual:
        mes_txt = nome_mes(hoje.year, hoje.month)
        titulo = f"Calendário de Pagamentos da Segurança Social — {mes_txt}"
        descricao = (
            f"Datas de pagamento em {mes_txt}: pensões, abono de família, "
            "subsídio de desemprego e doença, RSI, CSI e PSI — por transferência "
            "bancária e vale de correio, segundo o calendário oficial."
        )
    else:
        titulo = f"Calendário de Pagamentos da Segurança Social {hoje.year}"
        descricao = (
            "Quando paga a Segurança Social as pensões, o abono de família, o "
            "subsídio de desemprego, o RSI e o CSI — calendário mensal com base "
            "na fonte oficial."
        )
    return (
        f"  <title>{html.escape(titulo)}</title>\n"
        f'  <meta name="description" content="{html.escape(descricao)}">'
    )


# ── injecção confinada ───────────────────────────────────────────────────


def injetar_zona(html_pagina: str, marcador: str, novo_conteudo: str) -> str:
    inicio = f"<!-- CAL:{marcador}:INICIO -->"
    fim = f"<!-- CAL:{marcador}:FIM -->"
    padrao = re.compile(re.escape(inicio) + r"[\s\S]*?" + re.escape(fim))
    if not padrao.search(html_pagina):
        raise ValueError(f"marcador CAL:{marcador} não encontrado na página")
    return padrao.sub(inicio + "\n" + novo_conteudo + "\n" + fim, html_pagina)


def atualizar_pagina(
    dados: dict, hoje: dt.date, caminho: Path = PAGINA, escrever: bool = True
) -> bool:
    """Regenera as duas zonas. Devolve True se o ficheiro mudou."""
    original = caminho.read_text(encoding="utf-8")
    novo = injetar_zona(original, "META", render_meta(dados, hoje))
    novo = injetar_zona(novo, "CORPO", render_corpo(dados, hoje))
    mudou = novo != original
    if mudou and escrever:
        caminho.write_text(novo, encoding="utf-8")
    return mudou


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="relata sem escrever")
    args = parser.parse_args(argv)

    dados = carregar_dados()
    problemas = validar_dados(dados)
    if problemas:
        for p in problemas:
            print(f"ERRO: {p}", file=sys.stderr)
        print("Validação falhou — nada foi escrito.", file=sys.stderr)
        return 2

    hoje = hoje_lisboa()
    try:
        mudou = atualizar_pagina(dados, hoje, escrever=not args.dry_run)
    except ValueError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 3

    atual = _encontrar_mes(dados, hoje.year, hoje.month)
    estado = (
        f"mês corrente {nome_mes(hoje.year, hoje.month)} renderizado"
        if atual
        else f"SEM dados do mês corrente ({nome_mes(hoje.year, hoje.month)}) — estado degradado"
    )
    accao = "actualizada" if mudou else "já estava sincronizada (zero alterações)"
    if args.dry_run and mudou:
        accao = "seria actualizada (--dry-run)"
    print(f"{PAGINA.name}: {estado}; página {accao}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
