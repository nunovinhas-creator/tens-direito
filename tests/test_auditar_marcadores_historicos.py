"""Testes para scripts/auditar_marcadores_historicos.py — Issue #183,
passo 1: teste de regressão do corpus para MARCADORES_HISTORICOS
(scripts/verificar_datas.py).

Objectivo: capturar, para cada uma das 27 entradas de
`MARCADORES_HISTORICOS`, exactamente que ocorrências de data/valor
"antigas" (mesmo critério do padrão do tipo — ver
`scripts/verificar_datas.py::_pagina_tem_alerta`) ficam suprimidas por
essa entrada em cada página real do site, e comparar contra
`tests/marcadores_historicos_baseline.json` (baseline aprovado,
versionado, revisto linha a linha antes de cada alteração).

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

Nunca compara pelo campo `contexto` (só informativo, sensível a edições
próximas mas irrelevantes para a identidade da supressão — ver docstring
de `scripts/auditar_marcadores_historicos.py`) — a identidade é
(pagina, marcador, tipo, correspondencia, ordinal).
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from auditar_marcadores_historicos import (  # noqa: E402
    ANO_REFERENCIA,
    BASELINE_PATH,
    MARCADORES_HISTORICOS,
    auditar_corpus,
    carregar_baseline,
    identidade,
    paginas_do_corpus,
    supressoes_da_pagina,
)


def _html(corpo: str) -> str:
    return f"<html><body>{corpo}</body></html>"


# ── Unidade — a lógica de atribuição marcador↔ocorrência, isolada ──────────

def test_ocorrencia_antiga_junto_de_marcador_e_registada():
    html = _html("Despacho n.º 1/2020 fixou o valor a partir de 1 de janeiro de 2020.")
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
        "A Portaria n.º 1/2020 revoga a regra anterior; o novo regime está "
        "em vigor desde 1 de janeiro de 2020."
    )
    registos = supressoes_da_pagina(html, "sintetica.html", ano=2026)
    marcadores_de_2020 = {
        r["marcador"] for r in registos if r["correspondencia"] == "janeiro de 2020"
    }
    assert {"portaria", "em vigor desde"} <= marcadores_de_2020


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


def test_identidade_ignora_contexto():
    a = {"pagina": "x.html", "marcador": "portaria", "tipo": "data_mes_ano",
         "correspondencia": "janeiro de 2020", "ordinal": 1, "contexto": "A"}
    b = dict(a, contexto="B — texto completamente diferente")
    assert identidade(a) == identidade(b)


def test_ordinal_desambigua_duplicados_exactos_na_mesma_pagina():
    html = _html(
        "Em vigor desde 1 de janeiro de 2020 (Portaria n.º 1/2020). "
        "Repetimos: em vigor desde 1 de janeiro de 2020 (Portaria n.º 1/2020)."
    )
    registos = auditar_corpus_em_memoria(html, "sintetica.html")
    ordinais = sorted(
        r["ordinal"] for r in registos
        if r["marcador"] == "portaria" and r["correspondencia"] == "janeiro de 2020"
    )
    assert ordinais == [1, 2]


def auditar_corpus_em_memoria(conteudo: str, pagina: str, ano: int = 2026) -> list:
    """Mesma desambiguação de ordinal que `auditar_corpus()` aplica ao
    corpus real, mas sobre uma única página sintética em memória — evita
    duplicar a lógica de contagem no próprio teste."""
    from collections import Counter
    registos = supressoes_da_pagina(conteudo, pagina, ano)
    contador = Counter()
    for r in registos:
        chave = (r["pagina"], r["marcador"], r["tipo"], r["correspondencia"])
        contador[chave] += 1
        r["ordinal"] = contador[chave]
    return registos


# ── Regressão sobre o corpus real — o núcleo da Issue #183 ─────────────────

@pytest.fixture(scope="module")
def registos_atuais():
    return auditar_corpus(RAIZ, ANO_REFERENCIA)


@pytest.fixture(scope="module")
def baseline():
    return carregar_baseline(BASELINE_PATH)


def test_baseline_existe_e_nao_esta_vazio():
    assert BASELINE_PATH.exists(), (
        f"{BASELINE_PATH.relative_to(RAIZ)} não existe — gerar com "
        f"`python3 scripts/auditar_marcadores_historicos.py --write`, revisar "
        f"o diff, e só depois commitar."
    )
    assert carregar_baseline(BASELINE_PATH), "baseline vazio — nada para comparar"


def test_supressoes_do_corpus_batem_com_o_baseline_aprovado(registos_atuais, baseline):
    atuais_por_id = {identidade(r): r for r in registos_atuais}
    baseline_por_id = {identidade(r): r for r in baseline}

    novas = sorted(set(atuais_por_id) - set(baseline_por_id))
    orfas = sorted(set(baseline_por_id) - set(atuais_por_id))

    if not novas and not orfas:
        return

    linhas = []
    if novas:
        linhas.append(
            f"{len(novas)} supressão(ões) NOVA(S) — presentes no corpus mas AUSENTES do "
            f"baseline ({BASELINE_PATH.relative_to(RAIZ)}). Cada uma precisa de ser revista "
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
                f"    contexto: {r['contexto']!r}"
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
                f"    contexto (do baseline): {r['contexto']!r}"
            )
    pytest.fail("\n".join(linhas))


def test_baseline_referencia_so_marcadores_que_continuam_em_marcadores_historicos(baseline):
    """Uma entrada cujo `marcador` já não existe em MARCADORES_HISTORICOS
    nunca é reproduzida pelo corpus actual (não há regex nenhum para
    testar) — ficaria detectada como "órfã" pelo teste anterior de
    qualquer forma; esta asserção só torna a causa explícita quando for
    esse o motivo."""
    marcadores_baseline = {r["marcador"] for r in baseline}
    desconhecidos = marcadores_baseline - set(MARCADORES_HISTORICOS)
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
    chave = lambda r: (r["pagina"], r["marcador"], r["tipo"], r["correspondencia"], r["ordinal"])  # noqa: E731
    assert baseline == sorted(baseline, key=chave)


def test_auditoria_e_deterministica_entre_corridas():
    """Corre a auditoria duas vezes sobre o mesmo corpus — nunca deve
    depender da ordem do glob nem de qualquer outra fonte de não-
    determinismo (a mesma garantia que o resto do site já exige de
    `sincronizar_clusters.py`/`atualizar_calendario.py`)."""
    assert auditar_corpus(RAIZ, ANO_REFERENCIA) == auditar_corpus(RAIZ, ANO_REFERENCIA)
