"""
Prazos e datas do site — data/prazos.json (fonte única, curada à mão).

Alimenta duas coisas, ambas geradas por scripts/sincronizar_clusters.py:

- a etiqueta «⏳ Prazo a decorrer» nas listas de guias (PILLAR-LISTA e
  cartões de guias da homepage), para as páginas com um prazo;
- os cartões «⏰ Datas a não perder» da homepage (PRAZOS:HOME:INICIO/FIM).

O HTML gerado não depende da data de hoje (é idempotente): cada etiqueta
ou cartão com data leva `data-prazo="INICIO/FIM"` e nasce com `hidden`;
o assets/js/nav.js (iniciarPrazos) mostra só os que estão em curso pela
data de Lisboa. Sem JavaScript ficam escondidos — nunca uma data passada,
a mesma regra da barra do topo. Um prazo anual usa `--MM-DD`; o JS
completa com o ano de Lisboa.

Vigilância: `validar()` exige que a `frase` de cada entrada exista, tal e
qual, no texto visível da página, e que contenha a data de fim — se a
página mudar o prazo, tests/test_prazos.py falha até alguém actualizar
data/prazos.json.
"""
from __future__ import annotations

import calendar
import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

RAIZ = Path(__file__).resolve().parent.parent
PRAZOS_JSON = RAIZ / "data" / "prazos.json"

TIPOS = ("prazo", "data", "permanente")
MESES = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]
_RE_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_RE_ANUAL = re.compile(r"^\d{2}-\d{2}$")


@dataclass(frozen=True)
class Prazo:
    id: str
    pagina: str
    tipo: str
    icone: str
    titulo: str
    texto: str
    frase: str
    inicio: Optional[str] = None
    fim: Optional[str] = None
    recorrente: Optional[str] = None

    @property
    def anual(self) -> bool:
        return self.recorrente == "anual"

    def intervalo(self) -> str:
        """Valor de `data-prazo`: 'INICIO/FIM' (início vazio = já a decorrer);
        nas datas anuais, '--MM-DD' (o JS completa com o ano de Lisboa)."""
        def fmt(v: Optional[str]) -> str:
            if not v:
                return ""
            return f"--{v}" if self.anual else v
        return f"{fmt(self.inicio)}/{fmt(self.fim)}"


def carregar_prazos(caminho: Path = PRAZOS_JSON) -> List[Prazo]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return [Prazo(**p) for p in dados["prazos"]]


def texto_visivel(conteudo: str) -> str:
    """Texto que o leitor vê: sem <script>/<style>/comentários nem tags,
    entidades resolvidas e espaços normalizados."""
    s = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", " ", conteudo, flags=re.S | re.I)
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return " ".join(html.unescape(s).split())


def _data_fim(p: Prazo) -> Optional[date]:
    """Fim como data (num prazo anual, no ano de 2001 — só dia e mês contam)."""
    if not p.fim:
        return None
    try:
        if p.anual:
            mes, dia = (int(x) for x in p.fim.split("-"))
            return date(2001, mes, dia)
        return date.fromisoformat(p.fim)
    except ValueError:
        return None


def frase_tem_a_data(frase: str, fim: date) -> bool:
    """A frase cita a data de fim: «31 de dezembro» ou, quando o fim é o
    último dia do mês, «fim de dezembro»."""
    mes = MESES[fim.month]
    if re.search(rf"\b{fim.day}\s+de\s+{mes}\b", frase, re.I):
        return True
    ultimo = calendar.monthrange(fim.year, fim.month)[1]
    return fim.day == ultimo and re.search(rf"\bfim\s+de\s+{mes}\b", frase, re.I) is not None


def validar(prazos: List[Prazo], raiz: Path = RAIZ) -> List[str]:
    problemas: List[str] = []
    vistos = set()
    textos: Dict[str, str] = {}
    for p in prazos:
        onde = f"prazo {p.id!r}"
        if p.id in vistos:
            problemas.append(f"{onde}: id repetido")
        vistos.add(p.id)
        if p.tipo not in TIPOS:
            problemas.append(f"{onde}: tipo {p.tipo!r} desconhecido (usa {', '.join(TIPOS)})")
            continue
        for campo in ("icone", "titulo", "texto", "frase"):
            if not getattr(p, campo).strip():
                problemas.append(f"{onde}: {campo} vazio")
        caminho = raiz / p.pagina
        if not caminho.exists():
            problemas.append(f"{onde}: página {p.pagina!r} não existe")
        else:
            if p.pagina not in textos:
                textos[p.pagina] = texto_visivel(caminho.read_text(encoding="utf-8"))
            if " ".join(p.frase.split()) not in textos[p.pagina]:
                problemas.append(
                    f"{onde}: a frase {p.frase!r} já não está em {p.pagina} — a página mudou; "
                    "confirma o prazo e actualiza data/prazos.json"
                )

        if p.tipo == "permanente":
            if p.inicio or p.fim or p.recorrente:
                problemas.append(f"{onde}: um cartão permanente não tem datas")
            if re.search(r"\b(" + "|".join(MESES[1:]) + r")\b", p.texto, re.I):
                problemas.append(f"{onde}: cartão permanente com nome de mês no texto")
            continue

        if p.recorrente not in (None, "anual"):
            problemas.append(f"{onde}: recorrente {p.recorrente!r} desconhecido (só 'anual')")
            continue
        formato = _RE_ANUAL if p.anual else _RE_DATA
        for campo in ("inicio", "fim"):
            valor = getattr(p, campo)
            if valor is None and campo == "inicio":
                continue
            if not valor or not formato.match(valor):
                problemas.append(
                    f"{onde}: {campo}={valor!r} inválido "
                    f"({'MM-DD' if p.anual else 'AAAA-MM-DD'})"
                )
        fim = _data_fim(p)
        if fim is None:
            problemas.append(f"{onde}: fim {p.fim!r} não é uma data válida")
            continue
        if p.inicio and formato.match(p.inicio):
            try:
                inicio = (date(2001, *(int(x) for x in p.inicio.split("-")))
                          if p.anual else date.fromisoformat(p.inicio))
            except ValueError:
                problemas.append(f"{onde}: inicio {p.inicio!r} não é uma data válida")
            else:
                if inicio > fim:
                    problemas.append(f"{onde}: inicio depois do fim")
        if not frase_tem_a_data(p.frase, fim):
            problemas.append(f"{onde}: a frase não cita a data de fim ({fim.day} de {MESES[fim.month]})")
        if not frase_tem_a_data(p.texto, fim):
            problemas.append(f"{onde}: o texto do cartão não cita a data de fim")
        if p.anual and re.search(r"\b20\d\d\b", p.texto):
            problemas.append(f"{onde}: prazo anual com ano escrito no texto")
        if not p.anual and str(fim.year) not in p.texto:
            problemas.append(f"{onde}: data fixa sem o ano ({fim.year}) no texto do cartão")
    return problemas


def prazos_por_pagina(prazos: List[Prazo]) -> Dict[str, List[Prazo]]:
    """Só os do tipo 'prazo' — são os que ganham a etiqueta."""
    por: Dict[str, List[Prazo]] = {}
    for p in prazos:
        if p.tipo == "prazo":
            por.setdefault(p.pagina, []).append(p)
    return por


def _ordem(p: Prazo) -> tuple:
    """Permanentes no fim; os outros por fim (anuais pelo dia do ano)."""
    if p.tipo == "permanente":
        return (2, "", p.id)
    return (1, p.fim[-5:] if p.anual else p.fim, p.id)


def render_cartoes_home(prazos: List[Prazo]) -> str:
    """Interior de <!-- PRAZOS:HOME:INICIO/FIM -->: cartão do próximo
    pagamento (preenchido pelo nav.js a partir de #cal-home-dados; sem JS
    fica a ligação ao calendário, sem data), depois os prazos/datas
    (escondidos — o nav.js mostra os que estão em curso) e por fim os
    permanentes."""
    cartoes = [
        '        <div class="urgente-card" role="listitem" data-ate="permanente" data-cartao-pagamento>\n'
        '          <div class="icon">📅</div>\n'
        '          <h3>Calendário de pagamentos</h3>\n'
        '          <p>Vê em que dia a Segurança Social paga cada apoio.</p>\n'
        '          <a href="/calendario-pagamentos-seguranca-social.html">Ver calendário →</a>\n'
        '        </div>'
    ]
    for p in sorted(prazos, key=_ordem):
        if p.tipo == "permanente":
            atributos = 'data-ate="permanente"'
        else:
            atributos = f'data-ate="{p.intervalo().split("/")[1]}" data-prazo="{p.intervalo()}" hidden'
        cartoes.append(
            f'        <div class="urgente-card" role="listitem" {atributos}>\n'
            f'          <div class="icon">{p.icone}</div>\n'
            f'          <h3>{html.escape(p.titulo, quote=False)}</h3>\n'
            f'          <p>{html.escape(p.texto, quote=False)}</p>\n'
            f'          <a href="/{p.pagina}">Ver guia →</a>\n'
            f'        </div>'
        )
    return "\n\n".join(cartoes)


def etiqueta_prazo(prazos_da_pagina: List[Prazo]) -> str:
    """Etiqueta «Prazo a decorrer» (escondida; o nav.js mostra-a se algum
    dos intervalos estiver em curso). Vazia sem prazos."""
    if not prazos_da_pagina:
        return ""
    intervalos = " ".join(p.intervalo() for p in prazos_da_pagina)
    return f'<span class="etiqueta etiqueta-prazo" data-prazo="{intervalos}" hidden>⏳ Prazo a decorrer</span>'
