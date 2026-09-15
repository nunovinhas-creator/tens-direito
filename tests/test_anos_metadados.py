"""
Canário de anos em metadados — title/meta description (2026-07-06).

As queries reais do GSC mostram que os utilizadores pesquisam com o ano
("cuidador informal 2026", "rsi 2026", "prova escolar 2026"). Ter um ano
civil desactualizado num <title> ou <meta name="description"> é o mesmo
problema já resolvido para valores legais em tests/test_valores_ancora.py
— uma promessa visível no Google que fica errada em silêncio.

Este teste falha sempre que um <title>/description contenha um ano civil
inferior ao ano corrente (calculado via `datetime.now().year`, nunca uma
constante fixa — o ponto é o teste ficar vermelho sozinho em janeiro, sem
precisar de ninguém "lembrar" de o actualizar), excepto para referências
históricas legítimas — citações de diplomas legais (ex.: "DL 138/2025") ou
factos permanentes com data no passado (ex.: "fechado desde 2023") — que
vivem em EXCECOES_ANOS_HISTORICOS, cada uma com o motivo registado.

Corre sobre as páginas reais (mesmo padrão de test_higiene_indexacao.py/
test_acessibilidade.py), nunca uma cópia.

Issue #208 (2026-09-15) — EXCECOES_ANOS_HISTORICOS era a mais fraca das 3
listas de supressão do repositório (comparar com
tests/marcadores_historicos_baseline.json/test_auditar_marcadores_historicos.py
e EXCECOES_DIPLOMAS_FONTES/test_fontes_coerencia.py): tinha um único braço
de auto-auditoria (órfã), e mesmo esse por substring solta
(`str(ano) in texto`), não pelo mesmo critério REGEX_ANO usado pela
supressão. Corrigido com os 3 braços descritos junto de cada teste abaixo
— ver CLAUDE.md, secção "CANÁRIO DE ANOS EM METADADOS" → "Excepções a anos
históricos".
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

ANO_ATUAL = datetime.now().year

PAGINAS = sorted(encontrar_paginas(RAIZ), key=lambda p: str(p))
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]

REGEX_ANO = re.compile(r"\b(19|20)\d{2}\b")

# Raio do recorte de contexto usado pelo braço "baseline" (ver
# _recorte/_contextos_do_ano) — ±35 caracteres à volta do match, sempre
# encostado a fronteiras de palavra (nunca corta uma palavra a meio).
RAIO_CONTEXTO = 35


def _title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1) if m else ""


def _meta_description(html: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else ""


def _anos_antigos(texto: str) -> set[int]:
    """Mesmo cálculo usado pela asserção principal (REGEX_ANO + corte
    < ANO_ATUAL) — extraído para ser reutilizado pelo braço "já resolvida"
    de EXCECOES_ANOS_HISTORICOS (issue #208), para nunca divergir do
    critério real que decide se um ano é "antigo"."""
    return {int(m.group(0)) for m in REGEX_ANO.finditer(texto) if int(m.group(0)) < ANO_ATUAL}


def _recorte(texto: str, inicio: int, fim: int, raio: int = RAIO_CONTEXTO) -> str:
    """Recorte de contexto à volta de um match: ±`raio` caracteres a partir
    de `inicio`/`fim`, encostado a fronteiras de palavra (nunca corta uma
    palavra a meio — expande até ao espaço/pontuação mais próximo dos dois
    lados) e com espaços normalizados (sequências de whitespace colapsadas
    a um único espaço, sem espaço nas pontas)."""
    ini = max(0, inicio - raio)
    fimm = min(len(texto), fim + raio)
    while ini > 0 and texto[ini - 1].isalnum() and texto[ini].isalnum():
        ini -= 1
    while fimm < len(texto) and texto[fimm - 1].isalnum() and texto[fimm].isalnum():
        fimm += 1
    return re.sub(r"\s+", " ", texto[ini:fimm]).strip()


def _contextos_do_ano(texto: str, ano: int, raio: int = RAIO_CONTEXTO) -> tuple[str, ...]:
    """Um recorte (`_recorte`) por CADA ocorrência de `ano` em `texto`
    (REGEX_ANO, nunca substring solta), na ordem em que aparecem — é o
    valor comparado contra o baseline registado em
    EXCECOES_ANOS_HISTORICOS pelo braço 3 (ver
    test_excecoes_contexto_bate_com_o_registado)."""
    return tuple(
        _recorte(texto, m.start(), m.end(), raio)
        for m in REGEX_ANO.finditer(texto)
        if int(m.group(0)) == ano
    )


# (página, ano) → (motivo, contextos). Só anos que são citação de diploma
# legal (número do DL/Lei/Portaria/Regulamento) ou facto histórico
# permanente — nunca "esquecimento de actualizar".
#
# `contextos` é um tuplo com um recorte (_recorte, ±RAIO_CONTEXTO
# caracteres) por CADA ocorrência do ano no title+description da página, na
# ordem em que aparecem — gerado por script (scripts auxiliares
# descartáveis, nunca à mão) a partir das páginas reais, nunca inventado.
# Razão (issue #208): a chave (página, ano) autoriza o ANO, não o facto —
# sem este baseline por ocorrência, acrescentar uma 2.ª menção ao mesmo ano
# por um motivo diferente e nunca revisto (ex.: "valores de 2007
# desactualizados" ao lado de "DL 187/2007") ficaria suprimida em silêncio
# pela mesma entrada. Cada entrada é validada em 3 frentes — ver
# test_excecoes_sao_orfas_ou_ja_resolvidas (órfã / já resolvida) e
# test_excecoes_contexto_bate_com_o_registado (baseline por ocorrência,
# comparação exacta) — mais a guarda de
# test_excecoes_contexto_registado_contem_o_proprio_ano.
EXCECOES_ANOS_HISTORICOS: dict[tuple[str, int], tuple[str, tuple[str, ...]]] = {
    ("apoio-extraordinario-renda.html", 2023): (
        "PAER fechado a novos candidatos desde 15/03/2023 — facto histórico permanente, o apoio não voltou a abrir",
        ("fechado a novos candidatos desde 15-03-2023 e o Governo anunciou a sua revogação",),
    ),
    ("complemento-solidario-idosos.html", 2024): (
        "Regra de rendimentos dos filhos deixou de contar desde 2024 — facto histórico permanente",
        ("podem receber até 670€/mês. Desde 2024, os rendimentos dos filhos deixaram",),
    ),
    ("cuidador-informal.html", 2025): (
        "Decreto-Lei n.º 138/2025 — número do diploma, não uma data de vigência",
        ("Social. Verificado com base no DL 138/2025.",),
    ),
    ("documentos/pedido-acesso-documentos-administrativos.html", 2016): (
        "Lei n.º 26/2016 (LADA) — número do diploma, não uma data de vigência",
        ("administrativos, ao abrigo da Lei n.º 26/2016 (LADA). Tudo no teu browser.",),
    ),
    # Cluster reformas (2026-09-04) — DL 187/2007 é o diploma-base do regime
    # geral de invalidez e velhice, citado no title/description das 7 páginas
    # do cluster + pillar. "2007" é o número do diploma, não uma data de
    # vigência — o diploma continua em vigor (versão consolidada) e é
    # exactamente o tipo de facto estrutural que este cluster se propõe a
    # nunca deixar caducar.
    ("p/reformas.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("As regras do regime geral (DL 187/2007), sempre em vigor — sem valores que",),
    ),
    ("idade-normal.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("esperança média de vida (art. 20.º, DL 187/2007). A idade do teu ano é fixada por",),
    ),
    ("idade-pessoal.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("60 anos (art. 20.º, n.º 8, DL 187/2007).",),
    ),
    ("carreiras-muito-longas.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("sustentabilidade (art. 21.º-A, DL 187/2007).",),
    ),
    ("como-e-calculada.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("o factor entra (art. 26.º, DL 187/2007).",),
    ),
    ("que-anos-contam.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("33.º pela data de inscrição (DL 187/2007).",),
    ),
    ("mais-cedo-ou-mais-tarde.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("longas não têm corte nenhum (DL 187/2007).",),
    ),
    # Anel 3, parte A (2026-09-05) — mesmas 3 novas páginas do cluster,
    # mesmo motivo das 7 anteriores.
    ("invalidez-relativa-ou-absoluta.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("avaliada (arts. 13.º a 17.º, DL 187/2007).",),
    ),
    ("pensao-e-trabalho.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("trabalhar (arts. 58.º a 62.º, DL 187/2007).",),
    ),
    ("quando-a-invalidez-vira-velhice.html", 2007): (
        "Decreto-Lei n.º 187/2007 — número do diploma, não uma data de vigência",
        ("o que se mantém (art. 52.º, DL 187/2007).",),
    ),
    # Anel 3, parte C (2026-09-06) — "Lei n.º 7/2001" citada na meta
    # description (diploma que rege a prova da união de facto), não uma
    # data de vigência.
    ("pensao-sobrevivencia-uniao-de-facto.html", 2001): (
        "Lei n.º 7/2001 — número do diploma, não uma data de vigência",
        ("Impedimentos e como requerer (Lei n.º 7/2001, Decreto Regulamentar n.º 1/94).",),
    ),
    # Anel 4 — regimes complementares (2026-09-07, reescrita estrutural).
    ("caixa-geral-aposentacoes.html", 2005): (
        "Lei n.º 60/2005 — número do diploma, não uma data de vigência",
        ("2006 e, antes dela, 1993 (Lei n.º 60/2005).",),
    ),
    ("caixa-geral-aposentacoes.html", 2006): (
        "1 de janeiro de 2006 — data histórica fixa do fecho da CGA a novas inscrições, nunca se repete nem muda",
        (
            "novas inscrições em 1 de janeiro de 2006. Quem já era subscritor mantém regras",
            "regras próprias, com duas fronteiras — 2006 e, antes dela, 1993 (Lei n.º 60/2005",
        ),
    ),
    ("caixa-geral-aposentacoes.html", 1993): (
        "1 de setembro de 1993 — data histórica fixa da segunda fronteira interna da CGA (art. 5.º, Lei n.º 60/2005), nunca se repete nem muda",
        ("duas fronteiras — 2006 e, antes dela, 1993 (Lei n.º 60/2005).",),
    ),
    ("carreiras-contributivas-estrangeiro.html", 2004): (
        "Regulamento (CE) n.º 883/2004 — ano do regulamento, não uma data de vigência",
        ("totalizam os períodos (Regulamento 883/2004), como se calcula a pensão pro rata",),
    ),
    ("reforma-reino-unido-brexit.html", 2020): (
        "31 de dezembro de 2020 — data histórica fixa do fim do período de transição do Brexit, nunca se repete nem muda",
        ("fim do período de transição (31/12/2020) mantém-se coberto pelo Regulamento",),
    ),
}


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_sem_ano_civil_desactualizado_em_title_ou_description(caminho):
    pagina = str(caminho.relative_to(RAIZ))
    html = caminho.read_text(encoding="utf-8")
    texto = _title(html) + " " + _meta_description(html)

    anos_antigos = sorted(_anos_antigos(texto))
    nao_excecionados = [a for a in anos_antigos if (pagina, a) not in EXCECOES_ANOS_HISTORICOS]

    assert not nao_excecionados, (
        f"{pagina}: <title>/description menciona ano(s) {nao_excecionados} "
        f"anterior(es) ao ano corrente ({ANO_ATUAL}), sem excepção registada em "
        f"EXCECOES_ANOS_HISTORICOS — reveja se é um esquecimento de actualização "
        f"ou uma citação legítima a acrescentar às excepções"
    )


def test_excecoes_sao_orfas_ou_ja_resolvidas():
    """Duas direcções de falha por excepção (issue #208), mesmo espírito de
    test_excecoes_ainda_sao_citadas_e_ainda_em_falta
    (tests/test_fontes_coerencia.py):

    1. **órfã** — o ano já não corresponde a NENHUMA ocorrência real de
       REGEX_ANO no title/description da página. Mesmo critério da
       supressão (REGEX_ANO com fronteira de palavra), nunca
       `str(ano) in texto` — essa substring solta também aceitaria, por
       exemplo, "2007" dentro de "12007" ou de um valor monetário sem
       relação nenhuma com o diploma citado.
    2. **já resolvida** — o ano já não é "antigo" pelo MESMO cálculo da
       asserção principal (`_anos_antigos`: REGEX_ANO + corte
       < ANO_ATUAL). Sem este braço, uma excepção cujo ano deixasse de
       ser considerado antigo continuaria a "proteger" um alerta que a
       asserção principal nunca chegaria a levantar — peso morto, nunca
       detectado antes desta correcção.
    """
    for (pagina, ano), (motivo, _contextos) in EXCECOES_ANOS_HISTORICOS.items():
        html = (RAIZ / pagina).read_text(encoding="utf-8")
        texto = _title(html) + " " + _meta_description(html)

        assert _contextos_do_ano(texto, ano), (
            f"Excepção órfã: ({pagina}, {ano}) — {motivo!r} — {ano} já não "
            f"corresponde a nenhuma ocorrência de REGEX_ANO em title/description "
            f"de {pagina}. Remover a excepção."
        )
        assert ano in _anos_antigos(texto), (
            f"Excepção já resolvida: ({pagina}, {ano}) — {motivo!r} — {ano} já não "
            f"é considerado antigo por _anos_antigos() (REGEX_ANO + < ANO_ATUAL="
            f"{ANO_ATUAL}), o mesmo cálculo da asserção principal — a excepção não "
            f"suprime nada, remover."
        )


def test_excecoes_contexto_bate_com_o_registado():
    """Braço 3 — baseline por ocorrência (issue #208). A chave (página,
    ano) autoriza o ANO, não o facto: sem comparar o contexto literal de
    cada ocorrência, uma segunda ocorrência do mesmo ano por um motivo
    diferente e nunca revisto (ex.: "valores de 2007 desactualizados" ao
    lado de "DL 187/2007") ficaria suprimida em silêncio pela mesma
    entrada. Comparação exacta contra o tuplo `contextos` registado —
    gerado por script, nunca à mão; regenerar exige rever a ocorrência
    concreta, nunca aceitar em bloco (ver CLAUDE.md, "Excepções a anos
    históricos")."""
    for (pagina, ano), (motivo, contextos_registados) in EXCECOES_ANOS_HISTORICOS.items():
        html = (RAIZ / pagina).read_text(encoding="utf-8")
        texto = _title(html) + " " + _meta_description(html)
        contextos_atuais = _contextos_do_ano(texto, ano)
        assert contextos_atuais == contextos_registados, (
            f"({pagina}, {ano}) — {motivo!r} — contexto(s) real(is) diverge(m) do "
            f"baseline registado em EXCECOES_ANOS_HISTORICOS.\n"
            f"  registado: {contextos_registados!r}\n"
            f"  actual:    {contextos_atuais!r}\n"
            f"Reveja a ocorrência concreta antes de aprovar um novo contexto — nunca "
            f"copiar o actual para o registado sem olhar para ele."
        )


def test_excecoes_contexto_registado_contem_o_proprio_ano():
    """Guarda extra (issue #208, ponto 4): um contexto registado que não
    contém o próprio ano é sinal de um baseline aprovado por reflexo, sem
    olhar para a ocorrência real — nunca deve acontecer, independentemente
    de bater ou não com a página actual (essa comparação é feita à parte,
    em test_excecoes_contexto_bate_com_o_registado)."""
    for (pagina, ano), (motivo, contextos) in EXCECOES_ANOS_HISTORICOS.items():
        for contexto in contextos:
            assert str(ano) in contexto, (
                f"({pagina}, {ano}) — {motivo!r} — o contexto registado "
                f"{contexto!r} não contém o próprio ano {ano}. Baseline suspeito de "
                f"ter sido aprovado sem olhar para a ocorrência real."
            )
