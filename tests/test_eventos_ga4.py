"""
Testes de instrumentação de conversão GA4 (sessão de medição, 2026-07-16).

Asserções sobre o FONTE dos ficheiros tocados — portáteis, sem Playwright,
correm no CI e no sandbox. Confirmam, para cada evento de conversão:
  1. o evento existe onde é suposto, com o slug/parâmetro certo;
  2. está protegido pela guarda ``typeof gtag === 'function'``;
  3. não transporta nenhum dado introduzido pelo utilizador — só o facto de
     a acção ter terminado (mais, quando aplicável, um veredicto de
     elegibilidade, que é uma conclusão do simulador, nunca um valor
     introduzido pelo utilizador).

Ver a secção "MEDIÇÃO DE CONVERSÃO — EVENTOS GA4" no CLAUDE.md.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent

# Tokens que representam valores introduzidos pelo utilizador ou leituras do
# DOM. Nenhum objecto de parâmetros de um evento de conversão pode
# referenciar qualquer um destes — é a garantia "só o facto de a acção ter
# terminado, nunca dados pessoais".
TOKENS_PROIBIDOS = [
    ".value",
    "getElementById",
    "querySelector",
    "parseFloat",
    "parseInt",
    ".toFixed",
    "rendimento",
    "salario",
    "salário",
    "remunera",
    "idade",
    "patrimonio",
    "numCriancas",
    "agregado",
    "niss",
    "morada",
    "dataNascimento",
]

# Os 6 simuladores publicados e o slug esperado em cada um. simulador-psu.html
# está deliberadamente fora (noindex, não publicado, sem calc_resultado).
SIMULADORES = {
    "simulador-abono.html": "abono",
    "simulador-ase.html": "ase",
    "simulador-csi.html": "csi",
    "simulador-subsidio-doenca.html": "subsidio_doenca",
    "simulador-rsi.html": "rsi",
    "simulador-subsidio-desemprego.html": "subsidio_desemprego",
}

# Todos os eventos de conversão introduzidos nesta sessão, por ficheiro onde
# vivem — usado no varrimento global anti-dados-pessoais.
EVENTOS_POR_FICHEIRO = {
    "assets/js/share.js": ["partilha_clique"],
    "assets/js/nav.js": ["menu_tool_click"],
    "comecar-aqui.html": ["comecar_aqui_percurso"],
    "index.html": ["cal_home_clique"],
    **{ficheiro: ["simulacao_concluida"] for ficheiro in SIMULADORES},
}


def _ler(rel):
    return (RAIZ / rel).read_text(encoding="utf-8")


def _chamadas_evento(fonte, nome):
    """(indice, corpo_do_objecto) de cada gtag('event','<nome>', {...}).

    O objecto de parâmetros é opcional (eventos sem parâmetros existem, ex.
    cal_home_clique). Assume objectos sem chavetas aninhadas — é o caso de
    todos os eventos deste site.
    """
    padrao = re.compile(
        r"gtag\(\s*['\"]event['\"]\s*,\s*['\"]"
        + re.escape(nome)
        + r"['\"]\s*(?:,\s*(\{[^}]*\}))?\s*\)"
    )
    return [(m.start(), m.group(1) or "") for m in padrao.finditer(fonte)]


def _tem_guarda_antes(fonte, indice, janela=400):
    trecho = fonte[max(0, indice - janela):indice]
    return (
        "typeof gtag === 'function'" in trecho
        or 'typeof gtag === "function"' in trecho
    )


def _sem_tokens_proibidos(corpo):
    return [t for t in TOKENS_PROIBIDOS if t in corpo]


# ── simulacao_concluida ──────────────────────────────────────────────────

@pytest.mark.parametrize("ficheiro,slug", sorted(SIMULADORES.items()))
def test_simulacao_concluida_existe_com_slug_certo(ficheiro, slug):
    fonte = _ler(ficheiro)
    chamadas = _chamadas_evento(fonte, "simulacao_concluida")
    assert chamadas, f"{ficheiro}: sem evento simulacao_concluida"
    for _, corpo in chamadas:
        assert f"'{slug}'" in corpo or f'"{slug}"' in corpo, (
            f"{ficheiro}: simulacao_concluida sem o slug '{slug}': {corpo}"
        )


@pytest.mark.parametrize("ficheiro,slug", sorted(SIMULADORES.items()))
def test_simulacao_concluida_protegida_pela_guarda(ficheiro, slug):
    fonte = _ler(ficheiro)
    for indice, _ in _chamadas_evento(fonte, "simulacao_concluida"):
        assert _tem_guarda_antes(fonte, indice), (
            f"{ficheiro}: simulacao_concluida sem guarda typeof gtag antes"
        )


@pytest.mark.parametrize("ficheiro,slug", sorted(SIMULADORES.items()))
def test_simulacao_concluida_nao_envia_dados_pessoais(ficheiro, slug):
    fonte = _ler(ficheiro)
    for _, corpo in _chamadas_evento(fonte, "simulacao_concluida"):
        maus = _sem_tokens_proibidos(corpo)
        assert not maus, (
            f"{ficheiro}: simulacao_concluida transporta dados do utilizador "
            f"({maus}): {corpo}"
        )


def test_ase_tem_verdicto_de_elegibilidade_nos_dois_caminhos():
    # A ASE é o único simulador com dois caminhos distintos (com/sem direito)
    # — o evento tem de reflectir ambos.
    fonte = _ler("simulador-ase.html")
    corpos = [corpo for _, corpo in _chamadas_evento(fonte, "simulacao_concluida")]
    assert any("elegivel: true" in c for c in corpos), "ASE sem caminho elegível"
    assert any("elegivel: false" in c for c in corpos), "ASE sem caminho não elegível"


# ── partilha_clique ──────────────────────────────────────────────────────

def test_partilha_clique_existe_guardada_e_so_com_pathname():
    fonte = _ler("assets/js/share.js")
    chamadas = _chamadas_evento(fonte, "partilha_clique")
    assert len(chamadas) == 1, "esperava exactamente uma definição do evento"
    indice, corpo = chamadas[0]
    assert _tem_guarda_antes(fonte, indice), "partilha_clique sem guarda typeof gtag"
    assert "pagina" in corpo and "window.location.pathname" in corpo, (
        f"partilha_clique deve enviar só o pathname: {corpo}"
    )
    assert not _sem_tokens_proibidos(corpo), f"partilha_clique com dados pessoais: {corpo}"
    # Nunca enviar o título da página.
    assert "titulo" not in corpo and "title" not in corpo


def test_partilha_clique_nao_e_disparada_no_fallback_manual():
    # O evento representa uma partilha bem-sucedida; a caixa manual é uma
    # falha de cópia. A função registarPartilha() não pode ser chamada de
    # dentro de mostrarCaixaManual().
    fonte = _ler("assets/js/share.js")
    inicio = fonte.index("function mostrarCaixaManual")
    fim = fonte.index("function copiarParaAreaTransferencia")
    corpo_manual = fonte[inicio:fim]
    assert "registarPartilha" not in corpo_manual


# ── comecar_aqui_percurso ────────────────────────────────────────────────

def test_comecar_aqui_percurso_inicio_e_fim_guardados():
    fonte = _ler("comecar-aqui.html")
    chamadas = _chamadas_evento(fonte, "comecar_aqui_percurso")
    assert len(chamadas) == 2, "esperava evento de início e de fim"
    for indice, _ in chamadas:
        assert _tem_guarda_antes(fonte, indice), "comecar_aqui_percurso sem guarda"
    corpos = [corpo for _, corpo in chamadas]
    assert any("'inicio'" in c for c in corpos), "sem etapa 'inicio'"
    fim = [c for c in corpos if "'fim'" in c]
    assert fim, "sem etapa 'fim'"
    assert "destino" in fim[0], "etapa final sem parâmetro destino"


def test_comecar_aqui_percurso_nao_envia_dados_pessoais():
    fonte = _ler("comecar-aqui.html")
    for _, corpo in _chamadas_evento(fonte, "comecar_aqui_percurso"):
        assert not _sem_tokens_proibidos(corpo), corpo
        # destino é um pathname recomendado, nunca as respostas do quiz.
        assert "respostas" not in corpo


# ── cal_home_clique ──────────────────────────────────────────────────────

def test_cal_home_clique_existe_e_guardado():
    fonte = _ler("index.html")
    chamadas = _chamadas_evento(fonte, "cal_home_clique")
    assert len(chamadas) == 1, "esperava exactamente uma definição do evento"
    indice, corpo = chamadas[0]
    assert _tem_guarda_antes(fonte, indice), "cal_home_clique sem guarda typeof gtag"
    assert not _sem_tokens_proibidos(corpo), corpo


# ── menu_tool_click (grelha de ferramentas do menu móvel) ────────────────

def test_menu_tool_click_existe_guardado_e_deriva_do_href():
    fonte = _ler("assets/js/nav.js")
    chamadas = _chamadas_evento(fonte, "menu_tool_click")
    assert len(chamadas) == 1, "esperava exactamente uma definição do evento"
    indice, corpo = chamadas[0]
    assert _tem_guarda_antes(fonte, indice), "menu_tool_click sem guarda typeof gtag"
    assert "tool_destino" in corpo, f"menu_tool_click sem parâmetro tool_destino: {corpo}"
    assert not _sem_tokens_proibidos(corpo), corpo
    # O destino deriva do href do próprio cartão (basename sem .html) —
    # nunca um ID/slug fixo por cartão.
    assert "getAttribute('href')" in fonte, "tool_destino deve derivar do href"


def test_nav_js_nunca_contem_measurement_id():
    # O Measurement ID vive só no atributo data-ga4 das páginas (lido pelo
    # consentimento.js); o nav.js chama gtag('event', ...) e nada mais —
    # qualquer G-XXXX hardcoded aqui contornaria essa fonte única.
    fonte = _ler("assets/js/nav.js")
    ids = re.findall(r"G-[A-Z0-9]+", fonte)
    assert not ids, f"Measurement ID hardcoded em nav.js: {ids}"


# ── o gerador de documentos NÃO instrumenta (invariante de rede-zero) ─────

def test_gerador_documentos_nunca_dispara_gtag():
    # Decisão deliberada desta sessão (confirmada com o Nuno): o gerador de
    # documentos mantém a garantia "zero pedidos de rede depois do load" —
    # não há evento documento_gerado. Ver test_gerador_documentos.py
    # (test_zero_pedidos_de_rede_ao_interagir_com_o_gerador).
    fonte = _ler("assets/js/gerador-documentos.js")
    assert "gtag(" not in fonte, (
        "o gerador de documentos não pode disparar gtag — quebraria a "
        "invariante de rede-zero"
    )


# ── varrimento global anti-dados-pessoais ────────────────────────────────

def test_nenhum_evento_de_conversao_transporta_dados_do_utilizador():
    problemas = []
    for ficheiro, eventos in EVENTOS_POR_FICHEIRO.items():
        fonte = _ler(ficheiro)
        for nome in eventos:
            for _, corpo in _chamadas_evento(fonte, nome):
                maus = _sem_tokens_proibidos(corpo)
                if maus:
                    problemas.append(f"{ficheiro}:{nome} → {maus}: {corpo}")
    assert not problemas, "\n".join(problemas)
