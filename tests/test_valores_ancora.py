"""
Canário de valores-âncora — 2026.

Este teste NÃO verifica lógica de cálculo (isso já é feito por
tests/test_simulador_*_calculo.py). Afirma explicitamente, com fonte e
data, os valores-base de 2026 que atravessam vários simuladores e
páginas do site. Extrai os valores reais dos ficheiros HTML publicados
(nunca uma cópia) — o mesmo princípio de test_pesquisa_indice.py.

Quando a lei mudar (tipicamente em janeiro, com a nova Portaria do
IAS), ESTE TESTE TEM DE FALHAR — é o comportamento desejado. Falhar
aqui força uma revisão consciente de todos os simuladores/páginas
afectados, em vez de uma alteração de um valor passar despercebida
sem que nenhuma "data de validade" de página a apanhe. Ao subir os
valores para o ano seguinte, actualizar também os `verificado_em` e a
fonte de cada simulador — nunca só este ficheiro.

Fonte: Portaria n.º 480-A/2025/1, de 30 de dezembro (IAS 2026) e
Decreto-Lei n.º 28/2004, na redação atual (subsídio de doença) — ver
CLAUDE.md secção "FONTES VERIFICADAS E APROVADAS".
"""
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

IAS_2026 = 537.13


def _ler(nome: str) -> str:
    return (BASE_DIR / nome).read_text(encoding="utf-8")


def _valor_js(html: str, chave: str) -> float:
    """Extrai `<chave>: { valor: N, ...}` ou `<chave>: N,` de um objecto
    JS embutido no HTML — falha com uma mensagem clara se a chave não
    existir mais (renomeada ou removida), em vez de um KeyError mudo."""
    m = re.search(rf"\b{re.escape(chave)}\s*:\s*\{{\s*valor\s*:\s*([\d.]+)", html)
    if not m:
        m = re.search(rf"\b{re.escape(chave)}\s*:\s*([\d.]+)", html)
    assert m, f"chave {chave!r} não encontrada — renomeada ou removida?"
    return float(m.group(1))


# ── IAS 2026 ─────────────────────────────────────────────────────────────────

def test_ias_2026_simulador_abono():
    assert _valor_js(_ler("simulador-abono.html"), "ias2026") == IAS_2026


def test_ias_2026_simulador_ase():
    assert _valor_js(_ler("simulador-ase.html"), "ias2026") == IAS_2026


def test_ias_2026_visivel_no_texto():
    for pagina in ("simulador-abono.html", "simulador-ase.html", "simulador-subsidio-doenca.html"):
        assert "537,13" in _ler(pagina), f"{pagina}: IAS 2026 (537,13€) não visível no texto"


# ── Subsídio de doença — percentagens por escalão ───────────────────────────

def test_percentagens_escalao_subsidio_doenca():
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "taxaEscalao1") == 0.55
    assert _valor_js(html, "taxaEscalao2") == 0.60
    assert _valor_js(html, "taxaEscalao3") == 0.70
    assert _valor_js(html, "taxaEscalao4") == 0.75


def test_percentagens_tuberculose():
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "taxaTuberculoseAte2Familiares") == 0.80
    assert _valor_js(html, "taxaTuberculoseMais2Familiares") == 1.00


# ── Subsídio de doença — pisos mínimos ───────────────────────────────────────

def test_piso_diario_universal():
    assert _valor_js(_ler("simulador-subsidio-doenca.html"), "pisoDiarioUniversal") == 5.37


def test_pisos_proporcionais_300_325():
    html = _ler("simulador-subsidio-doenca.html")
    # 300€/mês ÷ 30 e 325€/mês ÷ 30 — ver CLAUDE.md "GATILHO AUTOBAIXA" (⚠️B)
    assert abs(_valor_js(html, "pisoDiarioProporcionalTaxa55") - 300 / 30) < 1e-9
    assert abs(_valor_js(html, "pisoDiarioProporcionalTaxa60") - 325 / 30) < 1e-9


# ── Subsídio de doença — dias de espera ──────────────────────────────────────

def test_dias_de_espera_por_vinculo():
    html = _ler("simulador-subsidio-doenca.html")
    assert _valor_js(html, "diasEsperaContaOutrem") == 3
    assert _valor_js(html, "diasEsperaIndependente") == 10
    assert _valor_js(html, "diasEsperaSeguroSocialVoluntario") == 30
