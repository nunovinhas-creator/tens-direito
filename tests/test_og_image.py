"""Canário de og:image (2026-07-07).

Motivo real: partilhas no Facebook/WhatsApp/LinkedIn apareciam só com
texto — nenhuma página tinha `og:image` (reportado pelo Nuno com um
screenshot de uma partilha real de abono-de-familia.html).

Garante, sobre as páginas REAIS do repositório (nunca fixtures):
  1. toda a página servida tem `og:image` com URL absoluto para a
     imagem do site;
  2. os metadados width/height batem certo com o PNG real em disco
     (dimensões lidas do cabeçalho IHDR — o Facebook usa-os para
     renderizar a pré-visualização à primeira partilha);
  3. o ficheiro da imagem existe e tem o formato standard 1200×630;
  4. `twitter:card = summary_large_image` presente.

Se uma página nova nascer sem og:image, isto falha — correr
`python scripts/adicionar_og_image.py --write`.
"""
import re
import struct
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from adicionar_og_image import URL_IMAGEM, LARGURA, ALTURA, encontrar_paginas  # noqa: E402

IMAGEM = RAIZ / "assets" / "img" / "og-default.png"
PAGINAS = [p.relative_to(RAIZ) for p in encontrar_paginas()]


def _dimensoes_png(caminho: Path) -> tuple[int, int]:
    dados = caminho.read_bytes()
    assert dados[:8] == b"\x89PNG\r\n\x1a\n", "não é um PNG válido"
    return struct.unpack(">II", dados[16:24])


def test_imagem_existe_e_tem_1200x630():
    assert IMAGEM.exists(), "assets/img/og-default.png em falta"
    assert _dimensoes_png(IMAGEM) == (LARGURA, ALTURA)


def test_url_da_imagem_aponta_para_o_ficheiro_real():
    caminho_relativo = URL_IMAGEM.replace("https://tensdireito.com/", "")
    assert (RAIZ / caminho_relativo) == IMAGEM


@pytest.mark.parametrize("pagina", PAGINAS, ids=str)
def test_pagina_tem_og_image_completa(pagina):
    texto = (RAIZ / pagina).read_text(encoding="utf-8")
    assert f'<meta property="og:image" content="{URL_IMAGEM}">' in texto
    m_w = re.search(r'<meta property="og:image:width" content="(\d+)">', texto)
    m_h = re.search(r'<meta property="og:image:height" content="(\d+)">', texto)
    assert m_w and m_h, f"{pagina}: og:image:width/height em falta"
    # os metadados declarados têm de bater certo com o PNG real — nunca
    # um número escrito à mão a divergir da imagem em disco
    assert (int(m_w.group(1)), int(m_h.group(1))) == _dimensoes_png(IMAGEM)
    assert '<meta property="og:image:alt"' in texto
    assert '<meta name="twitter:card" content="summary_large_image">' in texto
