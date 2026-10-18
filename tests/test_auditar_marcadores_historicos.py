"""Testes para scripts/auditar_marcadores_historicos.py — Issue #183,
passo 1: teste de regressão do corpus para MARCADORES_HISTORICOS
(scripts/verificar_datas.py).

Objectivo: capturar, para cada uma das 27 entradas de
`MARCADORES_HISTORICOS`, exactamente que ocorrências de data/valor
"antigas" (mesmo critério do padrão do tipo — ver
`scripts/verificar_datas.py::_pagina_tem_alerta`) ficam suprimidas por
essa entrada em cada página real do site, e comparar contra
`tests/marcadores_historicos_baseline_<ano>.json` (baseline aprovado,
versionado, revisto linha a linha antes de cada alteração) — um para o
ano corrente e outro para o ano seguinte (issue #332, PR C): no dia 1 de
janeiro, a regressão fica vermelha sozinha até se gravar o baseline do
novo ano seguinte, para as supressões desse ano serem revistas com um ano
de antecedência.

Duas direcções de falha, mesmo princípio já usado em
`tests/test_verificar_skips_permitidos.py` para
`tests/skips_permitidos.json` — comparação por conjunto exacto, nunca por
contagem:
1. Uma supressão nova, presente no corpus mas ausente do baseline — o
   caso central da Issue #183: alguém editou `MARCADORES_HISTORICOS`
   (regex novo ou alterado) ou uma página passou a conter conteúdo que um
   marcador já existente agora suprime, sem ninguém ter revisto a linha
   concreta.
2. Uma entrada do baseline que já não é reproduzida — o marcador foi
   removido/estreitado ou o conteúdo da página mudou, e a entrada ficou
   órfã; o baseline tem de ser podado, nunca deixado a apontar para algo
   que já não existe.

A identidade é (pagina, marcador, tipo, correspondencia, frase, ordinal)
— a frase envolvente identifica a supressão e o ordinal só desempata a
mesma frase repetida (issue #264; ver docstring de
`scripts/auditar_marcadores_historicos.py`).
"""
import re
import sys
import unicodedata
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from verificar_datas import MARCADOR_DESDE  # noqa: E402

from auditar_marcadores_historicos import (  # noqa: E402
    MARCADOR_DATAS_PERMANENTES,
    MARCADORES_HISTORICOS,
    PASTA_BASELINES,
    ano_de_execucao,
    anos_auditados,
    auditar_corpus,
    caminho_baseline,
    carregar_baseline,
    comparar,
    gravar_baseline,
    relatorio_por_marcador,
    frase_envolvente,
    identidade,
    paginas_do_corpus,
    supressoes_da_pagina,
)


def _html(corpo: str) -> str:
    return f"<html><body>{corpo}</body></html>"


# ── Unidade — a lógica de atribuição marcador↔ocorrência, isolada ──────────

def test_ocorrencia_antiga_junto_de_marcador_e_registada():
    html = _html("Despacho n.º 1/2020, de 1 de janeiro de 2020, fixou o valor.")
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    marcadores = {r["marcador"] for r in registos if r["correspondencia"] == "janeiro de 2020"}
    assert "despacho" in marcadores


def test_data_futura_nunca_e_registada_mesmo_junto_de_marcador():
    """Uma data igual/posterior ao ano de referência nunca passa pelo
    filtro de "antiga" — não há nada para um marcador suprimir."""
    html = _html("Portaria n.º 1/2026, em vigor desde 1 de janeiro de 2026.")
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    assert registos == []


def test_ocorrencia_antiga_sem_marcador_nenhum_nao_e_registada():
    """Uma data antiga sem nenhum termo de MARCADORES_HISTORICOS na janela
    de contexto não gera nenhum registo — não há supressão para atribuir."""
    html = _html("O valor era 480,43€ em janeiro de 2020, sem mais contexto nenhum.")
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    assert registos == []


def test_mesma_ocorrencia_pode_ser_atribuida_a_mais_do_que_um_marcador():
    html = _html(
        "O novo regime está em vigor desde 1 de março de 2020, "
        "que revoga a regra anterior."
    )
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    marcadores_de_2020 = {
        r["marcador"] for r in registos if r["correspondencia"] == "março de 2020"
    }
    assert {MARCADOR_DESDE, "em vigor desde"} <= marcadores_de_2020


def test_ano_letivo_par_antigo_e_registado_como_par_completo():
    html = _html('Desde 2016/2017, esta regra aplica-se pela Portaria n.º 1/2016.')
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    pares = {r["correspondencia"] for r in registos if r["tipo"] == "ano_letivo"}
    assert "2016/2017" in pares


def test_valor_ias_so_e_antigo_com_ano_antigo_anotado_na_janela():
    """`valor_ias` não tem ano_grupo próprio — a idade vem de um ano solto
    na janela; sem esse ano antigo, o marcador nunca é chamado a suprimir
    nada (não há candidato)."""
    html_sem_ano_antigo = _html("Portaria n.º 1/2026 — IAS de 537,13€.")
    assert supressoes_da_pagina(html_sem_ano_antigo, "sintetica.html", ano=2026) == []

    html_com_ano_antigo = _html("Em 2019, a Portaria n.º 1/2019 fixava o IAS de 428,90€.")
    registos = supressoes_da_pagina(html_com_ano_antigo, "sintetica.html", ano=2026)
    assert any(r["tipo"] == "valor_ias" and r["marcador"] == "portaria" for r in registos)


def test_identidade_inclui_a_frase():
    a = {"pagina": "x.html", "marcador": "portaria", "tipo": "data_mes_ano",
         "correspondencia": "janeiro de 2020", "frase": "A", "ordinal": 1}
    b = dict(a, frase="B — outra frase")
    assert identidade(a) != identidade(b)


def _ids(raiz: Path, nome: str, corpo: str) -> set:
    """Identidades de uma página sintética, pela mesma via que o corpus
    real (`auditar_corpus`), numa pasta própria."""
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / nome).write_text(_html(corpo), encoding="utf-8")
    return {identidade(r) for r in auditar_corpus(raiz, 2026)}


def _registos(raiz: Path, nome: str, corpo: str) -> list:
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / nome).write_text(_html(corpo), encoding="utf-8")
    return auditar_corpus(raiz, 2026)


def test_ordinal_desambigua_a_mesma_frase_repetida_na_mesma_pagina(tmp_path):
    frase = "Em vigor desde 1 de março de 2020 (Portaria n.º 1/2020)."
    registos = _registos(tmp_path, "sintetica.html", f"<p>{frase}</p><p>{frase}</p>")
    ordinais = sorted(
        r["ordinal"] for r in registos
        if r["marcador"] == "em vigor desde" and r["correspondencia"] == "março de 2020"
    )
    assert ordinais == [1, 2]


# ── Issue #264 — identidade pela frase envolvente, nunca pela posição ──────

FONTES = (RAIZ / "fontes.html").read_text(encoding="utf-8")


def _cartao(titulo: str) -> str:
    """Cartão real de `fontes.html` (nunca reescrito à mão)."""
    m = re.search(
        r'<div class="card">\s*<span class="tag">[^<]*</span>\s*<h2>'
        + re.escape(titulo) + r".*?</div>",
        FONTES, re.S,
    )
    assert m, f"cartão {titulo!r} não encontrado em fontes.html"
    return m.group(0)


CARTAO_198 = _cartao("Portaria n.º 198/2022")
# Desde a issue #332 os marcadores de diploma só suprimem a data da própria
# citação, e o cartão da Portaria n.º 158/2024/1 (o do caso real #260) ficou
# sem supressões. O mecanismo testado é o mesmo com qualquer cartão real que
# as tenha: este, com as fronteiras de inscrição na CGA.
CARTAO_286 = _cartao("Decreto-Lei n.º 286/93")
# Mais de 220 caracteres sem datas nem marcadores: afasta as janelas de
# contexto de dois blocos, para cada ocorrência ter os mesmos marcadores
# sozinha e acompanhada.
SEPARADOR = "<p>" + "Texto neutro de separação sem mais nada. " * 8 + "</p>"


def test_inserir_cartao_antes_nao_desloca_entradas_antigas_260(tmp_path):
    """Caso real do #260: o cartão da Portaria n.º 198/2022 entrou ANTES do
    da n.º 158/2024/1, e as duas supressões da frase inalterada da
    158/2024/1 passaram de ordinal 1 a 2 — «novas» sem terem mudado. Com a
    identidade pela frase, a página com os dois cartões tem exactamente as
    entradas de cada cartão sozinho, nem mais nem menos."""
    so_286 = _ids(tmp_path / "a", "fontes.html", CARTAO_286)
    so_198 = _ids(tmp_path / "b", "fontes.html", CARTAO_198)
    os_dois = _ids(tmp_path / "c", "fontes.html", CARTAO_198 + SEPARADOR + CARTAO_286)
    assert so_286 and so_198
    assert os_dois == so_286 | so_198


def test_alterar_a_frase_da_supressao_gera_uma_orfa_e_uma_nova(tmp_path):
    """Sentido inverso: mudar uma palavra da frase suprimida tem de
    aparecer, para cada (marcador, tipo, correspondencia) afectado,
    como exactamente uma entrada órfã e uma nova."""
    assert "fórmula de cálculo" in CARTAO_286
    alterado = CARTAO_286.replace("fórmula de cálculo", "fórmula do cálculo")
    antes = _ids(tmp_path / "a", "fontes.html", CARTAO_198 + SEPARADOR + CARTAO_286)
    depois = _ids(tmp_path / "b", "fontes.html", CARTAO_198 + SEPARADOR + alterado)
    orfas, novas = antes - depois, depois - antes
    assert orfas and novas
    grupo = lambda ids: sorted(i[1:4] for i in ids)  # noqa: E731 — (marcador, tipo, correspondencia)
    assert grupo(orfas) == grupo(novas)
    assert len(set(grupo(orfas))) == len(orfas)


def test_faq_repetida_no_corpo_e_no_json_ld_fica_estavel_com_texto_inserido_antes(tmp_path):
    frase = "Em vigor desde 1 de março de 2020, pela Portaria n.º 1/2020."
    faq = (
        '<script type="application/ld+json">{"@type": "Answer", "text": "' + frase + '"}</script>'
        + SEPARADOR + f"<p>{frase}</p>"
    )
    inserido = "<p>A Portaria n.º 9/2020 mudou a regra em janeiro de 2020.</p>" + SEPARADOR
    registos = _registos(tmp_path / "a", "faq.html", faq)
    ordinais = sorted(
        r["ordinal"] for r in registos
        if r["marcador"] == "em vigor desde" and r["correspondencia"] == "março de 2020"
    )
    assert ordinais == [1, 2]
    so_faq = {identidade(r) for r in registos}
    so_inserido = _ids(tmp_path / "b", "faq.html", inserido)
    com_inserido = _ids(tmp_path / "c", "faq.html", inserido + faq)
    assert com_inserido == so_faq | so_inserido


def _frases(raiz: Path, corpo: str) -> set:
    return {r["frase"] for r in _registos(raiz, "sintetica.html", corpo)}


def test_tags_inline_na_frase_nao_mudam_a_identidade(tmp_path):
    simples = "<p>Em vigor desde 1 de março de 2020, pela Portaria n.º 1/2020.</p>"
    # Tags fora dos marcadores: uma tag que parta um marcador (ex.: entre
    # "desde" e "1") muda a própria supressão, que é avaliada sobre o HTML
    # bruto como na produção — aí é certo aparecer como entrada diferente.
    marcada = ('<p>Em vigor desde 1 de março de 2020, <em>pela</em> '
               '<a href="/x.html"><strong>Portaria n.º 1/2020</strong></a>.</p>')
    assert _frases(tmp_path / "a", simples) == {
        "Em vigor desde 1 de março de 2020, pela Portaria n.º 1/2020."
    }
    assert _ids(tmp_path / "b", "s.html", simples) == _ids(tmp_path / "c", "s.html", marcada)


def test_data_num_atributo_tem_como_frase_o_valor_do_atributo(tmp_path):
    valor = "Portaria n.º 1/2020, em vigor desde janeiro de 2020 para todos."
    corpo = f'<meta name="description" content="{valor}"><p>Sem mais nada aqui.</p>'
    assert _frases(tmp_path, corpo) == {valor}


def test_nbsp_e_composicao_unicode_nao_mudam_a_identidade(tmp_path):
    normal = "<p>Em vigor desde 1 de maio de 2020, pela Portaria n.º 1/2020, até à revisão.</p>"
    variante = unicodedata.normalize("NFD", normal).replace("de 2020, pela", "de\u00a02020,\u202fpela")
    assert variante != normal
    assert _frases(tmp_path / "a", normal)
    assert _frases(tmp_path / "a", normal) == _frases(tmp_path / "b", variante)
    assert _ids(tmp_path / "c", "s.html", normal) == _ids(tmp_path / "d", "s.html", variante)


def test_nenhuma_frase_vazia_no_corpus_real():
    vazias = [r for a in anos_auditados() for r in auditar_corpus(RAIZ, a) if not r["frase"]]
    assert not vazias, [(r["pagina"], r["tipo"], r["correspondencia"]) for r in vazias]


def test_frase_envolvente_corta_na_frase_e_nao_em_abreviaturas():
    conteudo = _html("<p>Antes. O art. 4.º, n.º 1, vale desde janeiro de 2020 por lei. Depois.</p>")
    i = conteudo.index("janeiro de 2020")
    assert frase_envolvente(conteudo, i, i + len("janeiro de 2020")) == (
        "O art. 4.º, n.º 1, vale desde janeiro de 2020 por lei."
    )


# ── Regressão sobre o corpus real — o núcleo da Issue #183 ─────────────────

ANOS = anos_auditados()


@pytest.fixture(scope="module", params=ANOS, ids=lambda a: str(a))
def ano(request):
    return request.param


@pytest.fixture(scope="module")
def registos_atuais(ano):
    return auditar_corpus(RAIZ, ano)


@pytest.fixture(scope="module")
def baseline(ano):
    return carregar_baseline(caminho_baseline(ano))


@pytest.mark.parametrize("ano_baseline", ANOS, ids=str)
def test_baseline_existe_e_nao_esta_vazio(ano_baseline):
    caminho = caminho_baseline(ano_baseline)
    assert caminho.exists(), (
        f"{caminho.relative_to(RAIZ)} não existe — gerar com "
        f"`python3 scripts/auditar_marcadores_historicos.py --write`, revisar "
        f"as entradas novas (`--novas` lista-as por marcador) e só depois commitar."
    )
    assert carregar_baseline(caminho), "baseline vazio — nada para comparar"


def test_so_existem_baselines_do_ano_corrente_e_do_seguinte():
    """Um baseline de um ano que já acabou não é auditado por ninguém —
    apagá-lo quando o ano muda, nunca deixá-lo a parecer vigiado."""
    anos = sorted(int(p.stem.rsplit("_", 1)[1])
                  for p in PASTA_BASELINES.glob("marcadores_historicos_baseline_*.json"))
    assert anos == list(ANOS), (
        f"Baselines encontrados para {anos}, esperados {list(ANOS)} (ano corrente e "
        f"seguinte). Apagar os de anos fora deste par; gerar os em falta com "
        f"`python3 scripts/auditar_marcadores_historicos.py --write`."
    )


def test_supressoes_do_corpus_batem_com_o_baseline_aprovado(ano, registos_atuais, baseline):
    atuais_por_id = {identidade(r): r for r in registos_atuais}
    baseline_por_id = {identidade(r): r for r in baseline}
    caminho = caminho_baseline(ano).relative_to(RAIZ)
    novas = sorted(set(atuais_por_id) - set(baseline_por_id))
    orfas = sorted(set(baseline_por_id) - set(atuais_por_id))

    if not novas and not orfas:
        return

    linhas = []
    # Uma órfã e uma nova do mesmo (pagina, marcador, tipo, correspondencia)
    # são, quase sempre, a mesma supressão com a frase editada: mostrar lado
    # a lado, para a revisão olhar para o antes e o depois.
    grupos_novas = {chave[:4] for chave in novas}
    alteradas = sorted(grupos_novas & {chave[:4] for chave in orfas})
    for grupo in alteradas:
        antes = [baseline_por_id[c]["frase"] for c in orfas if c[:4] == grupo]
        depois = [atuais_por_id[c]["frase"] for c in novas if c[:4] == grupo]
        linhas.append(
            f"FRASE ALTERADA — pagina={grupo[0]!r} marcador={grupo[1]!r} "
            f"tipo={grupo[2]!r} correspondencia={grupo[3]!r}\n"
            f"    antes:  {antes!r}\n    depois: {depois!r}"
        )
    if novas:
        linhas.append(
            f"{len(novas)} supressão(ões) NOVA(S) — presentes no corpus mas AUSENTES do "
            f"baseline ({caminho}). Cada uma precisa de ser revista "
            f"e, se legítima, aprovada regenerando o baseline com "
            f"`python3 scripts/auditar_marcadores_historicos.py --write` e commitando o "
            f"diff (nunca em bloco sem olhar para a linha concreta):"
        )
        for chave in novas:
            r = atuais_por_id[chave]
            linhas.append(
                f"  - pagina={r['pagina']!r} marcador={r['marcador']!r} "
                f"tipo={r['tipo']!r} correspondencia={r['correspondencia']!r} "
                f"ordinal={r['ordinal']}\n"
                f"    frase: {r['frase']!r}"
            )
    if orfas:
        linhas.append(
            f"{len(orfas)} entrada(s) do baseline já NÃO são reproduzidas pelo corpus "
            f"actual — órfãs, a podar do baseline (confirmar que o conteúdo/marcador "
            f"mudou de facto, nunca apagar sem entender porquê):"
        )
        for chave in orfas:
            r = baseline_por_id[chave]
            linhas.append(
                f"  - pagina={r['pagina']!r} marcador={r['marcador']!r} "
                f"tipo={r['tipo']!r} correspondencia={r['correspondencia']!r} "
                f"ordinal={r['ordinal']}\n"
                f"    frase (do baseline): {r['frase']!r}"
            )
    pytest.fail("\n".join(linhas))


def test_baseline_referencia_so_marcadores_que_continuam_em_marcadores_historicos(baseline):
    """Uma entrada cujo `marcador` já não existe em MARCADORES_HISTORICOS
    nunca é reproduzida pelo corpus actual (não há regex nenhum para
    testar) — ficaria detectada como "órfã" pelo teste anterior de
    qualquer forma; esta asserção só torna a causa explícita quando for
    esse o motivo."""
    marcadores_baseline = {r["marcador"] for r in baseline}
    desconhecidos = marcadores_baseline - set(MARCADORES_HISTORICOS) - {MARCADOR_DATAS_PERMANENTES}
    assert not desconhecidos, (
        f"Entradas do baseline referenciam marcador(es) que já não existem em "
        f"MARCADORES_HISTORICOS: {sorted(desconhecidos)!r} — o teste de regressão "
        f"principal já as reportaria como órfãs; poda-las do baseline."
    )


def test_baseline_referencia_so_paginas_reais_do_corpus(baseline):
    paginas_reais = {str(p.relative_to(RAIZ)) for p in paginas_do_corpus(RAIZ)}
    referenciadas = {r["pagina"] for r in baseline}
    fantasmas = referenciadas - paginas_reais
    assert not fantasmas, (
        f"Entradas do baseline referenciam página(s) que já não fazem parte do "
        f"corpus (apagadas, renomeadas, ou movidas para fora de raiz/p//documentos/): "
        f"{sorted(fantasmas)!r}"
    )


def test_baseline_esta_ordenado_deterministicamente(baseline):
    """Mesma ordenação de `auditar_corpus()` — nunca a ordem de geração
    de uma corrida específica, para uma regeneração sem alterações reais
    nunca produzir um diff de puro reordenamento."""
    assert baseline == sorted(baseline, key=identidade)


def test_auditoria_e_deterministica_entre_corridas():
    """Corre a auditoria duas vezes sobre o mesmo corpus — nunca deve
    depender da ordem do glob nem de qualquer outra fonte de não-
    determinismo (a mesma garantia que o resto do site já exige de
    `sincronizar_clusters.py`/`atualizar_calendario.py`)."""
    ano = ano_de_execucao()
    assert auditar_corpus(RAIZ, ano) == auditar_corpus(RAIZ, ano)


# ── Ano de execução e ferramentas de revisão (issue #332, PR C) ────────────

def test_anos_auditados_sao_o_ano_corrente_e_o_seguinte():
    from datetime import date
    assert anos_auditados() == (date.today().year, date.today().year + 1)
    assert anos_auditados(2030) == (2030, 2031)


def test_auditar_corpus_sem_ano_usa_o_ano_de_execucao(tmp_path):
    (tmp_path / "s.html").write_text(_html(
        "<p>Prazo desde 3 de março de %d.</p>" % ano_de_execucao()), encoding="utf-8")
    assert auditar_corpus(tmp_path) == auditar_corpus(tmp_path, ano_de_execucao())


def test_data_do_ano_corrente_so_entra_no_baseline_do_ano_seguinte(tmp_path):
    """O caso da issue #332: uma data do próprio ano, suprimida por um
    marcador, nunca aparecia em nenhum baseline. Agora aparece no do ano
    seguinte — é aí que passa a ter efeito."""
    (tmp_path / "s.html").write_text(_html(
        "<p>Obrigatório desde 16 de maio de 2026.</p>"), encoding="utf-8")
    assert auditar_corpus(tmp_path, 2026) == []
    registos = auditar_corpus(tmp_path, 2027)
    assert registos and {r["correspondencia"] for r in registos} == {"maio de 2026"}
    novas, orfas = comparar(registos, auditar_corpus(tmp_path, 2026))
    assert novas == registos and orfas == []


def test_linha_vem_no_relatorio_mas_nunca_no_baseline_gravado(tmp_path):
    (tmp_path / "s.html").write_text(
        "<html><body>\n\n<p>Obrigatório desde 16 de maio de 2026.</p></body></html>",
        encoding="utf-8")
    registos = auditar_corpus(tmp_path, 2027)
    assert {r["linha"] for r in registos} == {3}
    destino = tmp_path / "b.json"
    gravar_baseline(registos, destino)
    gravados = carregar_baseline(destino)
    assert all("linha" not in r for r in gravados)
    assert [identidade(r) for r in gravados] == [identidade(r) for r in registos]
    relatorio = relatorio_por_marcador(registos)
    assert "| s.html | 3 | maio de 2026 |" in relatorio

