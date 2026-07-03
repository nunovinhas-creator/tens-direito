"""
Testes para scripts/atualizar_branding_nvlabs.py — bootstrap idempotente
(páginas nunca processadas) + sincronização idempotente (páginas já com
os marcadores, para quando o footer voltar a mudar no futuro — e-mail,
AdSense, afiliados).

Todos os testes isolam com strings em memória — nunca tocam nas páginas
reais do repositório (ver tests/test_sobre_jsonld.py para os testes
sobre o conteúdo real já sincronizado).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from atualizar_branding_nvlabs import (
    BLOCO_FOOTER,
    BLOCO_HEADER,
    MARCADOR_FOOTER_FIM,
    MARCADOR_FOOTER_INICIO,
    MARCADOR_HEADER_INICIO,
    processar,
)

_PAGINA_NOVA = """<!DOCTYPE html>
<html>
<head></head>
<body>
  <a href="/" class="logo">Tens Direito</a>
  <footer><p>Rodapé.</p></footer>
</body>
</html>
"""

_PAGINA_SEM_LOGO_NEM_FOOTER = """<!DOCTYPE html>
<html><head></head><body><p>Página atípica.</p></body></html>
"""


# ── Bootstrap — página nunca processada ───────────────────────────────────

def test_bootstrap_insere_header_e_footer():
    texto, notas = processar(_PAGINA_NOVA)
    assert MARCADOR_HEADER_INICIO in texto
    assert MARCADOR_FOOTER_INICIO in texto
    assert '<a class="footer-nvlabs" href="/sobre.html#nvlabs"' in texto
    assert len(notas) == 3  # header + footer + branding.css


def test_bootstrap_e_idempotente_na_segunda_corrida():
    primeira, _ = processar(_PAGINA_NOVA)
    segunda, notas = processar(primeira)
    assert segunda == primeira
    assert notas == []


def test_bootstrap_nao_mexe_em_pagina_sem_logo_nem_footer():
    texto, notas = processar(_PAGINA_SEM_LOGO_NEM_FOOTER)
    assert texto == _PAGINA_SEM_LOGO_NEM_FOOTER
    assert notas == []


def test_apenas_sincronizar_nunca_faz_bootstrap():
    texto, notas = processar(_PAGINA_NOVA, apenas_sincronizar=True)
    assert texto == _PAGINA_NOVA
    assert notas == []


# ── Sincronização — página já com os marcadores ──────────────────────────

def _pagina_com_footer_antigo():
    """Simula uma página já processada por uma versão anterior do script
    (bloco footer sem link, <div> em vez de <a>) — o cenário que a
    sincronização (não o bootstrap) tem de corrigir."""
    bootstrap, _ = processar(_PAGINA_NOVA)
    antigo = bootstrap.replace(
        '<a class="footer-nvlabs" href="/sobre.html#nvlabs" aria-label="An NV Labs project — saber mais sobre a NV Labs">',
        '<div class="footer-nvlabs">',
    )
    inicio = antigo.index(MARCADOR_FOOTER_INICIO)
    fim = antigo.index(MARCADOR_FOOTER_FIM)
    bloco = antigo[inicio:fim].replace("</a>", "</div>", 1)
    return antigo[:inicio] + bloco + antigo[fim:]


def test_sincronizacao_actualiza_footer_desactualizado():
    pagina_antiga = _pagina_com_footer_antigo()
    assert '<a class="footer-nvlabs"' not in pagina_antiga

    texto, notas = processar(pagina_antiga)

    assert '<a class="footer-nvlabs" href="/sobre.html#nvlabs"' in texto
    assert any("footer" in n for n in notas)


def test_sincronizacao_e_no_op_quando_ja_canonico():
    canonico, _ = processar(_PAGINA_NOVA)
    texto, notas = processar(canonico)
    assert texto == canonico
    assert notas == []


def test_bloco_footer_canonico_contem_link_e_texto_original():
    assert '<a class="footer-nvlabs" href="/sobre.html#nvlabs"' in BLOCO_FOOTER
    assert "An NV Labs project" in BLOCO_FOOTER  # texto mantém-se, decisão do Nuno


def test_bloco_header_canonico_inalterado_no_conteudo():
    assert "NV Labs" in BLOCO_HEADER
