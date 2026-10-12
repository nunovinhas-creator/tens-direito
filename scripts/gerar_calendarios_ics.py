#!/usr/bin/env python3
"""
Calendários subscrevíveis (.ics) do calendário de pagamentos da Segurança
Social — um ficheiro por prestação da secção «Quando recebo a minha
prestação?» (`VISTA_PRESTACOES` em atualizar_calendario.py), em
`calendario/<âncora>.ics`.

A pessoa subscreve o endereço uma vez (iPhone/Mac por webcal://, Google
Calendar por ?cid=); a aplicação de calendário volta a ler o ficheiro
sozinha. Quando o workflow mensal grava as datas do mês seguinte, corre
atualizar_calendario.py, que regenera estes ficheiros — as datas novas
chegam sem a pessoa fazer nada.

Regras:
- Só datas já publicadas em data/calendario_pagamentos.json, de `hoje`
  (dia de Lisboa da geração) em diante — nunca uma data calculada.
  Excepção única: calendario/pensoes-cga.ics, cujas datas são a regra
  oficial da CGA («dia 19 ou dia útil anterior», calendario_cga.py),
  12 meses à frente.
- Os lotes «1.º/2.º pagamento» (desemprego, doença, parentalidade) entram
  os dois, com o título «(1.º ou 2.º pagamento)»: o calendário oficial não
  diz qual dos dois dias cabe a cada pessoa.
- UID estável por prestação e dia, para a regeneração actualizar em vez de
  duplicar. A data de geração fica em X-TD-GERADO-EM, para o teste
  regenerar exactamente o mesmo ficheiro.

    python scripts/gerar_calendarios_ics.py            # escreve
    python scripts/gerar_calendarios_ics.py --dry-run  # só relata
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atualizar_calendario import (  # noqa: E402
    METODOS,
    VISTA_PRESTACOES,
    _ROTULO_SLUG,
    carregar_dados,
    hoje_lisboa,
    validar_dados,
)
import calendario_cga  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "calendario"
DOMINIO = "https://tensdireito.com"
PAGINA_CALENDARIO = "/calendario-pagamentos-seguranca-social.html"
REGEX_GERADO = re.compile(r"^X-TD-GERADO-EM:(\d{4}-\d{2}-\d{2})\r?$", re.MULTILINE)


def feeds() -> list[tuple[str, str, list[str]]]:
    """(âncora, nome, slugs do JSON) de cada calendário subscrevível."""
    return [(ancora, nome, list(slugs)) for ancora, nome, slugs, _guia in VISTA_PRESTACOES]


def endereco(ancora: str) -> str:
    return f"{DOMINIO}/calendario/{ancora}.ics"


def _texto(t: str) -> str:
    return t.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _dobrar(linha: str) -> str:
    """RFC 5545: linhas com mais de 75 octetos continuam na seguinte, com um espaço."""
    partes, atual, octetos = [], "", 0
    for ch in linha:
        n = len(ch.encode("utf-8"))
        if octetos + n > (74 if partes else 75):
            partes.append(atual)
            atual, octetos = "", 0
        atual += ch
        octetos += n
    partes.append(atual)
    return "\r\n ".join(partes)


def eventos(dados: dict, slugs: list[str], hoje: dt.date) -> list[dict]:
    """Um evento por dia de pagamento de hoje em diante, por ordem."""
    por_dia: dict[dt.date, dict] = {}
    for m in dados.get("meses", []):
        for p in m.get("pagamentos", []):
            dentro = [s for s in p.get("prestacoes", []) if s in slugs]
            if not dentro:
                continue
            try:
                dia = dt.date(m["ano"], m["mes"], p["dia"])
            except (KeyError, TypeError, ValueError):
                continue
            if dia < hoje:
                continue
            ev = por_dia.setdefault(dia, {"dia": dia, "ambiguo": False, "metodos": []})
            ev["ambiguo"] = ev["ambiguo"] or any(s in _ROTULO_SLUG for s in dentro)
            for metodo in p.get("metodo", []):
                if metodo in METODOS and metodo not in ev["metodos"]:
                    ev["metodos"].append(metodo)
    return [por_dia[d] for d in sorted(por_dia)]


def render_ics(ancora: str, nome: str, slugs: list[str], dados: dict, hoje: dt.date) -> str:
    carimbo = f"{hoje:%Y%m%d}T000000Z"
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Tens Direito//Calendario de pagamentos//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + _texto(f"Pagamentos da Segurança Social: {nome}"),
        "X-WR-CALDESC:" + _texto(
            "Datas de pagamento publicadas pela Segurança Social, atualizadas todos os meses "
            f"por tensdireito.com. Calendário completo: {DOMINIO}{PAGINA_CALENDARIO}"
        ),
        "X-WR-TIMEZONE:Europe/Lisbon",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
        f"X-TD-GERADO-EM:{hoje.isoformat()}",
    ]
    for ev in eventos(dados, slugs, hoje):
        titulo = nome + (" (1.º ou 2.º pagamento)" if ev["ambiguo"] else "")
        descricao = "Data do calendário de pagamentos da Segurança Social."
        if ev["ambiguo"]:
            descricao += (" A Segurança Social paga esta prestação em dois dias do mês e não diz"
                          " qual cabe a cada pessoa: pode ser este dia ou o outro.")
        if ev["metodos"]:
            descricao += " Por " + " ou ".join(METODOS[m] for m in ev["metodos"]) + "."
        descricao += f" Confirma em {DOMINIO}{PAGINA_CALENDARIO}"
        dia = ev["dia"]
        linhas += [
            "BEGIN:VEVENT",
            f"UID:{ancora}-{dia:%Y%m%d}@tensdireito.com",
            f"DTSTAMP:{carimbo}",
            f"DTSTART;VALUE=DATE:{dia:%Y%m%d}",
            f"DTEND;VALUE=DATE:{dia + dt.timedelta(days=1):%Y%m%d}",
            "SUMMARY:" + _texto(f"Pagamento da Segurança Social: {titulo}"),
            "DESCRIPTION:" + _texto(descricao),
            "TRANSP:TRANSPARENT",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "TRIGGER:-PT12H",
            "DESCRIPTION:" + _texto(f"Amanhã a Segurança Social paga: {titulo}"),
            "END:VALARM",
            "END:VEVENT",
        ]
    linhas.append("END:VCALENDAR")
    return "\r\n".join(_dobrar(ln) for ln in linhas) + "\r\n"


def render_ics_cga(hoje: dt.date) -> str:
    """Pensões da CGA: datas da regra oficial, 12 meses a contar de hoje."""
    ancora, nome = calendario_cga.ANCORA, calendario_cga.NOME
    carimbo = f"{hoje:%Y%m%d}T000000Z"
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Tens Direito//Calendario de pagamentos//PT",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + _texto(nome),
        "X-WR-CALDESC:" + _texto(
            "Datas de pagamento das pensões da Caixa Geral de Aposentações: dia 19 de cada "
            "mês ou o dia útil anterior (regra publicada pela CGA). "
            f"Calendário completo: {DOMINIO}{PAGINA_CALENDARIO}"
        ),
        "X-WR-TIMEZONE:Europe/Lisbon",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
        f"X-TD-GERADO-EM:{hoje.isoformat()}",
    ]
    for dia in calendario_cga.proximas_datas(hoje, meses=12):
        extra = calendario_cga.EXTRA_POR_MES.get(dia.month)
        titulo = "Pagamento da pensão da CGA" + (f" ({extra})" if extra else "")
        linhas += [
            "BEGIN:VEVENT",
            f"UID:{ancora}-{dia:%Y%m%d}@tensdireito.com",
            f"DTSTAMP:{carimbo}",
            f"DTSTART;VALUE=DATE:{dia:%Y%m%d}",
            f"DTEND;VALUE=DATE:{dia + dt.timedelta(days=1):%Y%m%d}",
            "SUMMARY:" + _texto(titulo),
            "DESCRIPTION:" + _texto(
                "A CGA paga as pensões no dia 19 de cada mês ou no dia útil anterior. "
                f"Confirma em {calendario_cga.FONTE_URL}"
            ),
            "TRANSP:TRANSPARENT",
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "TRIGGER:-PT12H",
            "DESCRIPTION:" + _texto("Amanhã a CGA paga as pensões"),
            "END:VALARM",
            "END:VEVENT",
        ]
    linhas.append("END:VCALENDAR")
    return "\r\n".join(_dobrar(ln) for ln in linhas) + "\r\n"


def data_de_geracao(conteudo: str) -> dt.date | None:
    m = REGEX_GERADO.search(conteudo)
    return dt.date.fromisoformat(m.group(1)) if m else None


def atualizar_ics(dados: dict, hoje: dt.date, pasta: Path = PASTA, escrever: bool = True) -> list[str]:
    """Escreve um .ics por prestação. Devolve os nomes dos que mudaram.
    Só a data de geração a mudar (mesmos eventos) não conta como mudança —
    evita um commit por dia sem nada novo para quem subscreveu."""
    mudados = []
    if escrever:
        pasta.mkdir(parents=True, exist_ok=True)
    ficheiros = [(a, lambda a=a, n=n, s=s: render_ics(a, n, s, dados, hoje)) for a, n, s in feeds()]
    ficheiros.append((calendario_cga.ANCORA, lambda: render_ics_cga(hoje)))
    for ancora, gerar in ficheiros:
        caminho = pasta / f"{ancora}.ics"
        novo = gerar()
        antigo = caminho.read_bytes().decode("utf-8") if caminho.exists() else None
        if antigo is not None and _sem_carimbo(novo) == _sem_carimbo(antigo):
            continue
        mudados.append(caminho.name)
        if escrever:
            caminho.write_bytes(novo.encode("utf-8"))
    return mudados


def _sem_carimbo(conteudo: str) -> str:
    return re.sub(r"(?m)^(X-TD-GERADO-EM|DTSTAMP):.*$", "", conteudo)


# ── Botões 📅 da lista «Quando recebo?» (zona CAL:SUBSCREVER) ───────────
# Os botões vivem em cada linha da lista (zona CAL:CORPO, atualizar_calendario
# ._lista_prestacoes); esta zona só traz o comportamento. Por omissão (e sem
# JavaScript) o botão é a ligação webcal://, que o iPhone, o iPad e o Mac abrem
# no Calendário; nos outros aparelhos, no momento do clique, passa a ser a
# ligação de subscrição do Google Calendar. Decidido no clique (delegação),
# nunca ao carregar: a lista do mês seguinte entra mais tarde, a partir de um
# <template> (viragem de mês do lado do cliente).


def _e(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def ligacoes(ancora: str) -> tuple[str, str]:
    """(webcal, Google Calendar) para subscrever o calendário da prestação."""
    webcal = "webcal://" + endereco(ancora).split("://", 1)[1]
    return webcal, "https://calendar.google.com/calendar/render?cid=" + webcal


def render_subscrever() -> str:
    return """  <script>
    (function () {
      // iPhone, iPad (que se apresenta como Mac) e Mac abrem webcal:// no
      // Calendário; os outros aparelhos vão para o Google Calendar.
      var apple = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent);
      document.addEventListener('click', function (e) {
        var ligacao = e.target.closest && e.target.closest('a.cal-sub[data-google]');
        if (!ligacao) return;
        if (!apple) {
          ligacao.href = ligacao.dataset.google;
          ligacao.target = '_blank';
          ligacao.rel = 'noopener';
          ligacao.dataset.destino = 'google';
        }
        if (typeof gtag === 'function') {
          gtag('event', 'calendario_subscrito', { destino: ligacao.dataset.destino });
        }
      });
    })();
  </script>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="relata sem escrever")
    args = parser.parse_args(argv)
    dados = carregar_dados()
    problemas = validar_dados(dados)
    if problemas:
        for p in problemas:
            print(f"ERRO: {p}", file=sys.stderr)
        return 2
    mudados = atualizar_ics(dados, hoje_lisboa(), escrever=not args.dry_run)
    print(f"calendario/*.ics: {len(mudados)} ficheiro(s) {'a actualizar' if args.dry_run else 'actualizado(s)'}"
          + (f" ({', '.join(mudados)})" if mudados else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
