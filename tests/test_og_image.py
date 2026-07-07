"""Canário de og:image por página (2026-07-07).

Motivo real: partilhas no Facebook/WhatsApp/LinkedIn apareciam só com
texto — nenhuma página tinha `og:image` (reportado pelo Nuno com um
screenshot de uma partilha real). Primeiro corrigido com uma imagem
única do site; no mesmo dia evoluiu para uma imagem POR PÁGINA com o
título real do artigo (`scripts/gerar_og_images.py`, estilo jornal).

Garante, sobre as páginas REAIS do repositório (nunca fixtures):
  1. toda a página servida tem `og:image` a apontar para a SUA imagem
     (`assets/img/og/<slug>.jpg`), com URL absoluto;
  2. o ficheiro da imagem existe e é um JPEG 1200×630 real — os
     metadados width/height declarados batem com as dimensões lidas do
     próprio ficheiro, nunca números soltos;
  3. `og:image:alt` = título do cartão e `twitter:card =
     summary_large_image` presentes;
  4. o manifest do gerador está sincronizado com o og:title actual de
     cada página — mudar um título sem regenerar a imagem falha aqui
     (a imagem mostraria o título antigo em silêncio);
  5. não há imagens órfãs em assets/img/og/ sem página correspondente.

Página nova sem imagem própria, ou título alterado sem regenerar:
correr `python scripts/gerar_og_images.py --write`.
"""
import json
import re
import struct
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from gerar_og_images import (  # noqa: E402
    DIR_OG,
    DOMINIO,
    LARGURA,
    ALTURA,
    MANIFEST,
    encontrar_paginas,
    slug_imagem,
    titulo_para_cartao,
)

PAGINAS = [str(p.relative_to(RAIZ)) for p in encontrar_paginas()]
_RE_OG_TITLE = re.compile(r'<meta property="og:title" content="([^"]*)">')


def _dimensoes_jpeg(caminho: Path) -> tuple[int, int]:
    """Lê largura×altura do cabeçalho JPEG (segmentos SOF), sem PIL."""
    dados = caminho.read_bytes()
    assert dados[:2] == b"\xff\xd8", f"{caminho.name}: não é um JPEG"
    i = 2
    while i < len(dados) - 9:
        assert dados[i] == 0xFF, f"{caminho.name}: segmento JPEG malformado"
        marcador = dados[i + 1]
        if 0xC0 <= marcador <= 0xCF and marcador not in (0xC4, 0xC8, 0xCC):
            altura, largura = struct.unpack(">HH", dados[i + 5:i + 9])
            return largura, altura
        i += 2 + struct.unpack(">H", dados[i + 2:i + 4])[0]
    raise AssertionError(f"{caminho.name}: sem segmento SOF")


def test_manifest_existe():
    assert MANIFEST.exists(), "assets/img/og/manifest.json em falta — correr gerar_og_images.py --write"


@pytest.mark.parametrize("pagina", PAGINAS, ids=str)
def test_pagina_tem_a_sua_og_image(pagina):
    texto = (RAIZ / pagina).read_text(encoding="utf-8")
    slug = slug_imagem(pagina)
    url_esperado = f"{DOMINIO}/assets/img/og/{slug}.jpg"
    assert f'<meta property="og:image" content="{url_esperado}">' in texto, (
        f"{pagina}: og:image não aponta para a imagem própria — "
        "correr gerar_og_images.py --write")

    imagem = DIR_OG / f"{slug}.jpg"
    assert imagem.exists(), f"{imagem} em falta"
    dim = _dimensoes_jpeg(imagem)
    assert dim == (LARGURA, ALTURA), f"{imagem.name}: {dim}, esperado {LARGURA}x{ALTURA}"

    m_w = re.search(r'<meta property="og:image:width" content="(\d+)">', texto)
    m_h = re.search(r'<meta property="og:image:height" content="(\d+)">', texto)
    assert m_w and m_h and (int(m_w.group(1)), int(m_h.group(1))) == dim
    assert '<meta property="og:image:alt"' in texto
    assert '<meta name="twitter:card" content="summary_large_image">' in texto


@pytest.mark.parametrize("pagina", PAGINAS, ids=str)
def test_manifest_sincronizado_com_titulo_actual(pagina):
    """Editar og:title sem regenerar a imagem deixaria o título antigo
    dentro do cartão, em silêncio — este teste força a regeneração."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    texto = (RAIZ / pagina).read_text(encoding="utf-8")
    m = _RE_OG_TITLE.search(texto)
    assert m, f"{pagina}: sem og:title"
    import html as _html
    titulo_actual = titulo_para_cartao(_html.unescape(m.group(1)))
    entrada = manifest.get(slug_imagem(pagina))
    assert entrada, f"{pagina}: sem entrada no manifest — correr gerar_og_images.py --write"
    assert entrada["titulo"] == titulo_actual, (
        f"{pagina}: og:title mudou ({entrada['titulo']!r} → {titulo_actual!r}) "
        "sem regenerar a imagem — correr gerar_og_images.py --write")


def test_sem_imagens_orfas():
    slugs_validos = {slug_imagem(p) for p in PAGINAS}
    orfas = [f.name for f in DIR_OG.glob("*.jpg") if f.stem not in slugs_validos]
    assert orfas == [], f"imagens sem página correspondente: {orfas}"
