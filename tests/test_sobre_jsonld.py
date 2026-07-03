"""
Testes E-E-A-T (2026-07-03): a NV Labs passa a ser resolvível como
entidade — secção própria + JSON-LD em `sobre.html` — e o footer "An NV
Labs project" passa a link funcional para lá. Corre sobre os ficheiros
REAIS do repositório (não fixtures), porque o que está em risco é o
conteúdo publicado, tal como `test_breadcrumb_coerencia.py`/
`test_nav_coerencia.py`.
"""
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from atualizar_branding_nvlabs import MARCADOR_FOOTER_INICIO, MARCADOR_FOOTER_FIM  # noqa: E402

ID_NVLABS = "https://tensdireito.com/sobre.html#nvlabs"


def _jsonld_blocks(caminho: Path):
    txt = caminho.read_text(encoding="utf-8")
    blocos = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', txt, re.DOTALL):
        blocos.append(json.loads(m.group(1).strip()))
    return blocos


# ── sobre.html — JSON-LD (excepção à regra "institucionais sem JSON-LD") ──

def test_sobre_tem_aboutpage_organization_website():
    tipos = {b["@type"] for b in _jsonld_blocks(RAIZ / "sobre.html")}
    assert {"AboutPage", "Organization", "WebSite"} <= tipos


def test_sobre_organization_e_a_nv_labs_com_sameas_real():
    blocos = _jsonld_blocks(RAIZ / "sobre.html")
    org = next(b for b in blocos if b["@type"] == "Organization")
    assert org["@id"] == ID_NVLABS
    assert org["name"] == "NV Labs"
    # sameAs só com URLs reais existentes (nunca um perfil inventado)
    assert org["sameAs"] == ["https://github.com/nunovinhas-creator/tens-direito"]


def test_sobre_aboutpage_referencia_a_organization():
    blocos = _jsonld_blocks(RAIZ / "sobre.html")
    about = next(b for b in blocos if b["@type"] == "AboutPage")
    assert about["mainEntity"]["@id"] == ID_NVLABS


def test_sobre_website_publisher_referencia_a_organization():
    blocos = _jsonld_blocks(RAIZ / "sobre.html")
    website = next(b for b in blocos if b["@type"] == "WebSite")
    assert website["publisher"]["@id"] == ID_NVLABS


def test_sobre_tem_seccoes_ancoradas_nvlabs_e_metodo():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    assert 'id="nvlabs"' in html
    assert 'id="metodo"' in html


def test_sobre_liga_para_o_repositorio_github_real():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    assert 'href="https://github.com/nunovinhas-creator/tens-direito"' in html


def test_sobre_tem_marcador_contacto_email_preparado_mas_nao_activo():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    assert "<!-- CONTACTO-EMAIL:INICIO -->" in html
    assert "<!-- CONTACTO-EMAIL:FIM -->" in html
    # o endereço vive só dentro do comentário — nunca activo como mailto: real
    assert "mailto:" not in html
    assert "contacto@tens-direito.com" in html


def test_sobre_nao_inventa_pessoa_nem_credencial():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    for termo_proibido in ("equipa editorial", "Dr.", "Dra.", "jornalista", "advogad"):
        assert termo_proibido not in html


def test_sobre_mantem_disclaimer_e_ligacao_a_partir_de_nvlabs():
    html = (RAIZ / "sobre.html").read_text(encoding="utf-8")
    assert "Aviso de independência" in html
    assert 'href="#aviso-independencia"' in html


# ── Footer NV Labs — "An NV Labs project" agora é link real ──────────────

PAGINAS_COM_FOOTER_NVLABS = [
    p for p in sorted(RAIZ.glob("*.html")) + sorted((RAIZ / "p").glob("*.html"))
    if MARCADOR_FOOTER_INICIO in p.read_text(encoding="utf-8")
]

_IDS_FOOTER = [str(p.relative_to(RAIZ)) for p in PAGINAS_COM_FOOTER_NVLABS]


@pytest.mark.parametrize("caminho", PAGINAS_COM_FOOTER_NVLABS, ids=_IDS_FOOTER)
def test_footer_nvlabs_e_link_funcional_para_sobre(caminho):
    html = caminho.read_text(encoding="utf-8")
    m = re.search(
        re.escape(MARCADOR_FOOTER_INICIO) + r"(.*?)" + re.escape(MARCADOR_FOOTER_FIM),
        html, re.DOTALL,
    )
    assert m, f"marcador NVLABS:FOOTER não encontrado ou vazio em {caminho}"
    bloco = m.group(1)
    assert '<a class="footer-nvlabs" href="/sobre.html#nvlabs"' in bloco
    assert "An NV Labs project" in bloco  # texto mantém-se — decisão do Nuno
    assert "</a>" in bloco


def test_pelo_menos_uma_pagina_tem_footer_nvlabs():
    # rede de segurança contra um bug que esvaziasse a lista acima em silêncio
    assert len(PAGINAS_COM_FOOTER_NVLABS) >= 30
