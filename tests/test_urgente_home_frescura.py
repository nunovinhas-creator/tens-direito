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

Desde a issue #283 cada cartão declara a sua data de fim num atributo
`data-ate="AAAA-MM-DD"` (ou `data-ate="permanente"`), e o teste verifica:

1. todos os cartões têm `data-ate` válido;
2. `data-ate` ainda não passou — a regra principal, sem depender de ler
   o texto;
3. `permanente` só num cartão sem nenhum nome de mês no texto;
4. coerência texto ↔ `data-ate`: `data-ate` nunca é posterior à data
   não histórica mais tardia do texto (impede `2030-12-31` num cartão que
   diz "até 30 de setembro").

O detector de datas no texto reconhece dia + mês ("30 de setembro"), mês
sem dia ("setembro" → último dia do mês) e sequências de meses
("julho/agosto", "julho e agosto", "julho a agosto" → último dia do
último mês). Só nomes de meses concretos contam — "todos os meses" nunca
dispara. Uma data sem ano usa o ano do `data-ate` (quem escreve o cartão
declara o ano uma vez), nunca o ano corrente — "janeiro" escrito em
dezembro para o ano seguinte não é um falso positivo, e "até 31 de
dezembro" deixa de passar a ser lido como o 31 de dezembro seguinte em
janeiro. A supressão histórica (`MARCADORES_HISTORICOS` de
`verificar_datas.py`) é por ocorrência, olhando só para a frase em que a
data está — nunca por cartão (antes, "em vigor desde 14 de agosto"
suprimia também o "31 de dezembro" do mesmo cartão da PSU).

FALHAR AQUI É O COMPORTAMENTO DESEJADO sempre que ninguém actualizar um
cartão a tempo — ver CLAUDE.md "INVARIANTE — NENHUM ESTADO DE ERRO PODE
PARECER SUCESSO".
"""
from __future__ import annotations

import calendar
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from verificar_datas import MARCADORES_HISTORICOS, MESES  # noqa: E402

INDEX_HTML = (RAIZ / "index.html").read_text(encoding="utf-8")
FIXTURE_PRE_282 = (RAIZ / "tests" / "fixtures" / "urgente_cards_pre_282.html").read_text(
    encoding="utf-8"
)

_MES = (
    r"(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|"
    r"outubro|novembro|dezembro)"
)
REGEX_DIA_MES = re.compile(
    rf"\b(\d{{1,2}})\s+de\s+({_MES})(?:\s+de\s+(\d{{4}}))?\b", re.IGNORECASE
)
# Um mês ou uma sequência de meses ("julho/agosto", "julho e agosto",
# "julho a agosto", "julho, agosto"), com ano opcional no fim.
REGEX_MESES = re.compile(
    rf"\b({_MES}(?:\s*(?:/|,|\be\b|\ba\b)\s*{_MES})*)(?:\s+de\s+(\d{{4}}))?\b",
    re.IGNORECASE,
)
REGEX_NOME_MES = re.compile(rf"\b{_MES}\b", re.IGNORECASE)
# Início da frase em que uma data está — a janela da supressão histórica.
REGEX_FRONTEIRA = re.compile(r"[.;!?—]")


@dataclass(frozen=True)
class Cartao:
    titulo: str
    data_ate: str | None  # valor bruto do atributo, None se ausente
    texto: str  # texto visível, sem tags


@dataclass(frozen=True)
class Ocorrencia:
    texto: str
    data: date  # data-limite (último dia do mês para um mês sem dia)
    historica: bool
    ano_implicito: bool  # sem ano no texto — usou o ano do data-ate


def _cartoes(html: str) -> list[Cartao]:
    """Divide pela tag de abertura de cada cartão, em vez de procurar o
    `</div>` de fecho: um cartão pode ter `<div>` aninhados (ex.: o badge
    "Em vigor" da PSU), e um `.*?</div>` cortava-o a meio."""
    partes = re.split(r'(<div class="urgente-card"[^>]*>)', html)
    cartoes = []
    for abertura, corpo in zip(partes[1::2], partes[2::2]):
        m_ate = re.search(r'\bdata-ate="([^"]*)"', abertura)
        m_tit = re.search(r"<h3>(.*?)</h3>", corpo, re.S)
        texto = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", corpo)).strip()
        cartoes.append(
            Cartao(
                titulo=m_tit.group(1).strip() if m_tit else "(sem título)",
                data_ate=m_ate.group(1) if m_ate else None,
                texto=texto,
            )
        )
    assert len(cartoes) == html.count('class="urgente-card"'), (
        "contagem de cartões não bate com as aberturas .urgente-card — estrutura mudou?"
    )
    return cartoes


def _cards_urgente_banda() -> list[Cartao]:
    """Cartões reais de index.html. Sem a secção (escondida por ficar
    vazia), devolve `[]`."""
    if 'class="urgente-banda"' not in INDEX_HTML:
        return []
    m = re.search(
        r'<div class="urgente-cards"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        INDEX_HTML,
        re.S,
    )
    assert m, (
        "não encontrei .urgente-cards em index.html — a estrutura da secção "
        "'Datas a não perder' mudou sem actualizar este canário"
    )
    return _cartoes(m.group(1))


def _data_ate(cartao: Cartao) -> date | None:
    """`data-ate` como data, ou None para `permanente`/ausente/inválido."""
    if cartao.data_ate is None or cartao.data_ate == "permanente":
        return None
    try:
        return date.fromisoformat(cartao.data_ate)
    except ValueError:
        return None


def _e_historica(texto: str, inicio: int, fim: int) -> bool:
    fronteiras = [m.end() for m in REGEX_FRONTEIRA.finditer(texto, 0, inicio)]
    janela = texto[fronteiras[-1] if fronteiras else 0:fim]
    return any(re.search(p, janela, re.IGNORECASE) for p in MARCADORES_HISTORICOS)


def detectar_datas(texto: str, ano_ref: int) -> list[Ocorrencia]:
    """Datas do texto, com o ano implícito `ano_ref` quando não há ano."""
    ocorrencias = []
    mascarado = texto
    for m in REGEX_DIA_MES.finditer(texto):
        ano = int(m.group(3)) if m.group(3) else ano_ref
        try:
            data = date(ano, MESES[m.group(2).lower()], int(m.group(1)))
        except ValueError:
            continue  # data inválida (ex.: 31 de fevereiro) — não é uma data real
        ocorrencias.append(
            Ocorrencia(m.group(0), data, _e_historica(texto, m.start(), m.end()), not m.group(3))
        )
        # Tira o mês já lido, para não ser contado de novo como mês sem dia.
        mascarado = mascarado[: m.start()] + " " * (m.end() - m.start()) + mascarado[m.end():]
    for m in REGEX_MESES.finditer(mascarado):
        ultimo = REGEX_NOME_MES.findall(m.group(1))[-1]
        ano = int(m.group(2)) if m.group(2) else ano_ref
        mes = MESES[ultimo.lower()]
        data = date(ano, mes, calendar.monthrange(ano, mes)[1])
        ocorrencias.append(
            Ocorrencia(m.group(0), data, _e_historica(texto, m.start(), m.end()), not m.group(2))
        )
    return ocorrencias


def _mais_um_ano(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # 29 de fevereiro
        return d.replace(year=d.year + 1, day=28)


def falhas_cartao(cartao: Cartao, hoje: date) -> list[str]:
    """As quatro regras da issue #283 (mais o limite de 12 meses para datas
    sem ano, que fecha a coerência). Lista vazia = cartão válido."""
    if cartao.data_ate is None:
        return ['sem atributo data-ate (usa "AAAA-MM-DD" ou "permanente")']
    if cartao.data_ate == "permanente":
        meses = REGEX_NOME_MES.findall(cartao.texto)
        if meses:
            return [f'data-ate="permanente" com nome de mês no texto: {", ".join(meses)}']
        return []
    ate = _data_ate(cartao)
    if ate is None:
        return [f'data-ate={cartao.data_ate!r} não é uma data AAAA-MM-DD válida nem "permanente"']
    falhas = []
    if ate < hoje:
        falhas.append(f"data-ate {ate.isoformat()} já passou")
    ocorrencias = detectar_datas(cartao.texto, ate.year)
    if any(o.ano_implicito for o in ocorrencias) and ate >= _mais_um_ano(hoje):
        # Uma data sem ano só identifica um dia dentro dos próximos 12 meses;
        # sem este limite, data-ate="2030-12-31" tornava "até 31 de dezembro"
        # coerente por arrastar o ano implícito para 2030.
        falhas.append(
            f"data-ate {ate.isoformat()} está a 12 meses ou mais de hoje e o texto tem "
            "datas sem ano — escreve o ano no texto"
        )
    prazos = [o for o in ocorrencias if not o.historica]
    if prazos:
        mais_tardia = max(prazos, key=lambda o: o.data)
        if ate > mais_tardia.data:
            falhas.append(
                f"data-ate {ate.isoformat()} é posterior à data mais tardia do texto "
                f"({mais_tardia.texto!r} → {mais_tardia.data.isoformat()})"
            )
    return falhas


def _cartao(texto: str, data_ate: str | None, titulo: str = "Teste") -> Cartao:
    return Cartao(titulo=titulo, data_ate=data_ate, texto=texto)


def _cartao_pre_282(titulo: str) -> Cartao:
    for c in _cartoes(FIXTURE_PRE_282):
        if c.titulo == titulo:
            return c
    raise AssertionError(f"cartão {titulo!r} não está na fixture pre-#282")


# --- Cartões reais de index.html -------------------------------------------


def test_seccao_datas_a_nao_perder_nunca_fica_vazia():
    """Decisão de 2026-10-01: se todos os cartões saírem, a secção
    esconde-se (sai de index.html) — nunca o título sozinho, sem cartões."""
    if 'class="urgente-banda"' not in INDEX_HTML:
        return
    assert _cards_urgente_banda(), (
        "'⏰ Datas a não perder' está em index.html sem nenhum cartão — "
        "retira a secção inteira em vez de deixar o título vazio"
    )


def test_nenhum_cartao_de_urgente_banda_tem_data_ate_invalida_passada_ou_incoerente():
    falhas = []
    for c in _cards_urgente_banda():
        for f in falhas_cartao(c, date.today()):
            falhas.append(f"{c.titulo!r}: {f}")
    assert not falhas, (
        "cartão(ões) de '⏰ Datas a não perder' (index.html) com data de fim "
        "em falta, já passada ou incoerente com o texto — actualiza o cartão "
        "(ver CLAUDE.md secção 'INVARIANTE') antes de publicar:\n  - "
        + "\n  - ".join(falhas)
    )


def test_badge_urgente_nunca_acompanha_prazo_ja_passado():
    """Verificação mais estrita e directa do bug real (2026-08-23): um
    badge 'URGENTE' ao lado de uma data que já passou é sempre um erro,
    mesmo que a data esteja coberta por um marcador histórico."""
    hoje = date.today()
    falhas = []
    for c in _cards_urgente_banda():
        if "URGENTE" not in c.texto:
            continue
        ate = _data_ate(c)
        for o in detectar_datas(c.texto, ate.year if ate else hoje.year):
            if o.data < hoje:
                falhas.append(f"{c.titulo!r}: badge URGENTE + {o.texto!r} (já passou)")
    assert not falhas, "badge URGENTE junto de um prazo já expirado:\n  - " + "\n  - ".join(falhas)


# --- Detector ---------------------------------------------------------------


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Vales MEGA disponíveis em julho/agosto.", [date(2026, 8, 31)]),
        ("Pagos em julho e agosto.", [date(2026, 8, 31)]),
        ("Inscrições de julho a agosto.", [date(2026, 8, 31)]),
        ("1.º escalão: duplica em setembro.", [date(2026, 9, 30)]),
        ("Candidaturas em fevereiro.", [date(2026, 2, 28)]),
        ("Pede até 30 de setembro.", [date(2026, 9, 30)]),
        ("Até 31 de dezembro de 2027.", [date(2027, 12, 31)]),
        ("Abre em março de 2027.", [date(2027, 3, 31)]),
        ("Gratuito dos 4 aos 23 anos. Carrega todos os meses.", []),
        ("Recebes por mês, ao longo do mês.", []),
    ],
)
def test_detector_reconhece_dia_mes_mes_isolado_e_pares(texto, esperado):
    assert [o.data for o in detectar_datas(texto, 2026)] == esperado


def test_supressao_historica_e_por_ocorrencia_nao_por_cartao():
    """No cartão real da PSU, "desde 14 de agosto" é histórico, mas o
    "31 de dezembro" da frase seguinte nunca pode ficar suprimido por isso."""
    psu = _cartao_pre_282("Prestação Social Única")
    ocorrencias = {o.texto: o.historica for o in detectar_datas(psu.texto, 2026)}
    assert ocorrencias == {"14 de agosto": True, "31 de dezembro": False}


# --- Casos que nunca podem disparar ------------------------------------------


def test_janeiro_escrito_em_dezembro_para_o_ano_seguinte_nao_dispara():
    cartao = _cartao("Candidaturas abertas em janeiro.", "2027-01-31")
    assert falhas_cartao(cartao, date(2026, 12, 15)) == []


def test_carrega_todos_os_meses_permanente_nao_dispara():
    passe = _cartao_pre_282("Passe sub-23")
    assert passe.texto.find("todos os meses") >= 0
    assert falhas_cartao(_cartao(passe.texto, "permanente"), date(2026, 10, 1)) == []


# --- Regras 1-4 ---------------------------------------------------------------


def test_cartao_sem_data_ate_falha():
    assert falhas_cartao(_cartao("Pede até 30 de setembro.", None), date(2026, 9, 1))


def test_data_ate_invalida_falha():
    assert falhas_cartao(_cartao("Pede até 30 de setembro.", "30/09/2026"), date(2026, 9, 1))


def test_permanente_com_nome_de_mes_falha():
    assert falhas_cartao(_cartao("Duplica em setembro.", "permanente"), date(2026, 9, 1))


def test_data_ate_posterior_ao_prazo_do_texto_falha():
    falhas = falhas_cartao(_cartao("Pede até 30 de setembro.", "2030-12-31"), date(2026, 9, 1))
    assert any("posterior" in f for f in falhas)


def test_data_ate_a_anos_de_distancia_com_data_sem_ano_falha():
    """Mutação real: data-ate="2030-12-31" no cartão da Prova Escolar
    passava, porque "31 de dezembro" herdava o ano 2030."""
    prova = _cartao_pre_282("Prova Escolar")
    falhas = falhas_cartao(_cartao(prova.texto, "2030-12-31"), date(2026, 10, 4))
    assert any("12 meses" in f for f in falhas)


def test_data_ate_a_anos_de_distancia_com_ano_escrito_no_texto_passa():
    cartao = _cartao("Regime transitório até 31 de dezembro de 2030.", "2030-12-31")
    assert falhas_cartao(cartao, date(2026, 10, 4)) == []


def test_prova_escolar_em_janeiro_ja_nao_passa_como_dezembro_seguinte():
    """Antes, "até 31 de dezembro" sem ano era lido no ano corrente: a 2 de
    janeiro de 2027 virava 31/12/2027 e não dava alerta."""
    prova = _cartao_pre_282("Prova Escolar")
    assert falhas_cartao(_cartao(prova.texto, "2026-12-31"), date(2026, 12, 31)) == []
    assert falhas_cartao(_cartao(prova.texto, "2026-12-31"), date(2027, 1, 2))


# --- Provas com os cartões reais retirados no #282 -------------------------


@pytest.mark.parametrize(
    "titulo, data_ate",
    [
        ("Manuais gratuitos", "2026-08-31"),
        ("Abono a dobrar", "2026-09-30"),
        ("ASE — candidatura", "2026-09-30"),
        ("Bolsas de mérito", "2026-09-30"),
    ],
)
def test_cartoes_retirados_no_282_falham_a_1_de_outubro(titulo, data_ate):
    original = _cartao_pre_282(titulo)
    hoje = date(2026, 10, 1)
    # Como estavam (sem data-ate): falham pela regra 1.
    assert falhas_cartao(original, hoje)
    # Com a data de fim honesta: falham porque já passou.
    honesto = _cartao(original.texto, data_ate, titulo)
    assert any("já passou" in f for f in falhas_cartao(honesto, hoje))
    # Com uma data de fim inventada para os manter: falham pela coerência.
    inventado = _cartao(original.texto, "2026-12-31", titulo)
    assert any("posterior" in f for f in falhas_cartao(inventado, hoje))


def test_manuais_falham_logo_a_1_de_setembro():
    """"julho/agosto" passa a contar como 31 de agosto — o cartão teria sido
    apanhado um mês antes da revisão manual do #282."""
    manuais = _cartao_pre_282("Manuais gratuitos")
    assert falhas_cartao(_cartao(manuais.texto, "2026-08-31"), date(2026, 8, 31)) == []
    assert falhas_cartao(_cartao(manuais.texto, "2026-08-31"), date(2026, 9, 1))


def test_detector_antigo_nao_via_manuais_nem_abono():
    """Prova da lacuna da issue #283: o detector antigo (só dia + mês)
    não encontrava nenhuma data nestes dois cartões; o novo encontra."""
    for titulo in ("Manuais gratuitos", "Abono a dobrar"):
        texto = _cartao_pre_282(titulo).texto
        assert not REGEX_DIA_MES.search(texto)
        assert detectar_datas(texto, 2026)
