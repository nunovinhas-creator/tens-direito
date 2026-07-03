"""
Testes para scripts/adicionar_autoria_artigos.py — autoria NV Labs
(author/publisher no JSON-LD FAQPage) e byline "Verificado a" a atribuir
à redação do Tens Direito.

Duas camadas: unidade (strings em memória, tmp_path) e rede de segurança
sobre os artigos REAIS do repositório — porque o que interessa aqui é
que o conteúdo publicado esteja mesmo correcto e que as duas regexes de
que a atribuição depende (`sincronizar_clusters._REGEX_VERIFICADO` e
`auto_update_engine._REGEX_VERIFICADO_A`) continuem a reconhecer o
carimbo depois de alterado — critério de aceitação explícito desta
sessão.
"""
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from adicionar_autoria_artigos import (  # noqa: E402
    ID_NVLABS,
    atualizar_byline_verificado,
    injetar_autoria_jsonld,
)
from sincronizar_clusters import _REGEX_VERIFICADO, extrair_verificado_em  # noqa: E402
from auto_update_engine import _REGEX_VERIFICADO_A  # noqa: E402

_FAQPAGE_MINIMO = """<script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {"@type": "Question", "name": "X?", "acceptedAnswer": {"@type": "Answer", "text": "Y."}}
    ]
  }
  </script>"""

_CORPO_COM_CARIMBO = """
    <div class="fonte-bloco">
      Verificado a 24 de junho de 2026 · IAS 2026: 537,13 €.
    </div>
"""


# ── injetar_autoria_jsonld — unidade ──────────────────────────────────────

def test_injeta_author_e_publisher_com_virgula_valida():
    texto, mudou = injetar_autoria_jsonld(_FAQPAGE_MINIMO)
    assert mudou is True
    assert f'"author": {{"@id": "{ID_NVLABS}"}},' in texto
    assert f'"publisher": {{"@id": "{ID_NVLABS}"}},' in texto
    # JSON ainda válido depois da inserção
    bloco = re.search(r"<script[^>]*>(.*?)</script>", texto, re.DOTALL).group(1)
    obj = json.loads(bloco)
    assert obj["author"]["@id"] == ID_NVLABS
    assert obj["publisher"]["@id"] == ID_NVLABS
    assert obj["mainEntity"]  # resto do objecto intacto


def test_injetar_autoria_e_idempotente():
    primeira, _ = injetar_autoria_jsonld(_FAQPAGE_MINIMO)
    segunda, mudou = injetar_autoria_jsonld(primeira)
    assert segunda == primeira
    assert mudou is False


def test_sem_faqpage_nao_altera_nada():
    texto, mudou = injetar_autoria_jsonld("<html><body>nada aqui</body></html>")
    assert mudou is False
    assert texto == "<html><body>nada aqui</body></html>"


# ── atualizar_byline_verificado — unidade ─────────────────────────────────

def test_acrescenta_atribuicao_apos_a_data():
    texto, mudou = atualizar_byline_verificado(_CORPO_COM_CARIMBO)
    assert mudou is True
    assert "Verificado a 24 de junho de 2026 pela redação do" in texto
    assert 'href="/sobre.html#metodo">Tens Direito</a>' in texto
    assert "IAS 2026: 537,13" in texto  # resto do texto original intacto


def test_atualizar_byline_e_idempotente():
    primeira, _ = atualizar_byline_verificado(_CORPO_COM_CARIMBO)
    segunda, mudou = atualizar_byline_verificado(primeira)
    assert segunda == primeira
    assert mudou is False


def test_sem_carimbo_nao_altera_nada():
    texto, mudou = atualizar_byline_verificado("<p>Sem carimbo nenhum.</p>")
    assert mudou is False


def test_so_a_ultima_ocorrencia_e_alterada():
    corpo = (
        '<p class="fonte-inline">Verificado a 1/06/2026</p>'
        '<p class="fonte-inline">Verificado a 2/06/2026</p>'
        '<div class="fonte-bloco">Verificado a 24 de junho de 2026</div>'
    )
    texto, mudou = atualizar_byline_verificado(corpo)
    assert mudou is True
    assert "1/06/2026 pela redação" not in texto
    assert "2/06/2026 pela redação" not in texto
    assert "24 de junho de 2026 pela redação do" in texto


# ── Compatibilidade das regexes dependentes — critério de aceitação ──────

def test_regex_sincronizar_clusters_continua_a_reconhecer_apos_atribuicao():
    texto, _ = atualizar_byline_verificado(_CORPO_COM_CARIMBO)
    m = _REGEX_VERIFICADO.search(texto)
    assert m is not None
    assert m.group("d2") == "24" and m.group("mes2") == "junho" and m.group("y2") == "2026"


def test_regex_auto_update_engine_continua_a_reconhecer_apos_atribuicao():
    texto, _ = atualizar_byline_verificado(_CORPO_COM_CARIMBO)
    m = _REGEX_VERIFICADO_A.search(texto)
    assert m is not None
    assert m.group(2) == "24 de junho de 2026"


# ── Rede de segurança sobre os artigos reais ──────────────────────────────

def _paginas_com_faqpage():
    ficheiros = sorted(RAIZ.glob("*.html")) + sorted((RAIZ / "p").glob("*.html"))
    return [f for f in ficheiros if '"@type": "FAQPage"' in f.read_text(encoding="utf-8")]


_PAGINAS = _paginas_com_faqpage()
_IDS = [str(p.relative_to(RAIZ)) for p in _PAGINAS]


def test_pelo_menos_20_paginas_reais_com_faqpage():
    assert len(_PAGINAS) >= 20


@pytest.mark.parametrize("caminho", _PAGINAS, ids=_IDS)
def test_pagina_real_tem_author_e_publisher_validos(caminho):
    html = caminho.read_text(encoding="utf-8")
    m = re.search(r'"@type":\s*"FAQPage".*?"mainEntity"', html, re.DOTALL)
    assert m, f"FAQPage sem mainEntity reconhecível em {caminho}"
    assert f'"author": {{"@id": "{ID_NVLABS}"}}' in m.group(0)
    assert f'"publisher": {{"@id": "{ID_NVLABS}"}}' in m.group(0)


@pytest.mark.parametrize("caminho", _PAGINAS, ids=_IDS)
def test_pagina_real_com_carimbo_tem_byline_atribuida_e_data_extraivel(caminho):
    html = caminho.read_text(encoding="utf-8")
    if not _REGEX_VERIFICADO.search(html):
        pytest.skip("página sem carimbo 'Verificado a' (ex.: simuladores, pillars)")

    assert 'pela redação do <a href="/sobre.html#metodo">Tens Direito</a>' in html
    # extrair_verificado_em continua a funcionar sobre o ficheiro real
    assert extrair_verificado_em(caminho) is not None
