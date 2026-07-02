"""
Testes para o guardrail estendido de scripts/gerar_noticias.py.

Até esta mudança, `escrever_ficheiro_seguro()` só podia escrever em
`noticias.html` (qualquer outro HTML era bloqueado por inteiro). Agora
`index.html` ganhou uma segunda excepção, mas escopada a um marcador
(`NOTICIA-HOME:INICIO/FIM`) — este ficheiro confirma que essa excepção
nunca permite escrever fora da secção marcada, nem inventar o marcador
se ele não existir.

Todos os testes isolam o sistema de ficheiros com `tmp_path` — nunca
tocam nas páginas HTML reais do repositório.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gerar_noticias import (
    escrever_ficheiro_seguro,
    atualizar_index_home,
    render_noticia_home,
)

_ENTRY = {
    "title": "PSU aprovada no Parlamento",
    "summary": "Resumo da notícia sobre a PSU.",
    "link": "https://exemplo.pt/noticia-psu",
    "published": "Wed, 01 Jul 2026 10:00:00 GMT",
}

_INDEX_COM_MARCADOR = """<!DOCTYPE html>
<html lang="pt">
<body>
  <section class="noticia-section">
    <!-- NOTICIA-HOME:INICIO -->
    <div class="noticia-card">
      <span class="badge-hoje">25 jun. 2026</span>
      <h3>Notícia antiga</h3>
      <p>Resumo antigo.</p>
      <a href="https://exemplo.pt/antiga" class="link-ler">Ler notícia completa →</a>
    </div>
    <!-- NOTICIA-HOME:FIM -->
  </section>
  <footer><p>Rodapé nunca deve mudar.</p></footer>
</body>
</html>
"""

_INDEX_SEM_MARCADOR = """<!DOCTYPE html>
<html lang="pt">
<body>
  <section class="noticia-section">
    <p>Sem marcador nenhum aqui.</p>
  </section>
</body>
</html>
"""


def _escrever(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


# ── noticias.html — escrita livre, como sempre foi ────────────────────────

def test_escreve_livremente_em_noticias_html(tmp_path):
    caminho = _escrever(tmp_path, "noticias.html", "<html>antigo</html>")
    escrever_ficheiro_seguro(caminho, "<html>novo conteúdo completo</html>")
    assert caminho.read_text(encoding="utf-8") == "<html>novo conteúdo completo</html>"


# ── qualquer outro HTML fora da lista — bloqueado por inteiro ─────────────

def test_bloqueia_escrita_noutro_html_fora_da_lista(tmp_path):
    caminho = _escrever(tmp_path, "abono-de-familia.html", "<html>original</html>")
    with pytest.raises(Exception, match="BLOQUEADO"):
        escrever_ficheiro_seguro(caminho, "<html>alterado</html>")
    assert caminho.read_text(encoding="utf-8") == "<html>original</html>"


# ── index.html — só a secção marcada pode mudar ───────────────────────────

def test_permite_escrita_em_index_dentro_do_marcador(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_COM_MARCADOR)
    novo = _INDEX_COM_MARCADOR.replace("Notícia antiga", "Notícia nova")

    escrever_ficheiro_seguro(caminho, novo)

    assert "Notícia nova" in caminho.read_text(encoding="utf-8")


def test_bloqueia_escrita_em_index_fora_do_marcador(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_COM_MARCADOR)
    novo = _INDEX_COM_MARCADOR.replace("Rodapé nunca deve mudar.", "Rodapé alterado!")

    with pytest.raises(Exception, match="BLOQUEADO"):
        escrever_ficheiro_seguro(caminho, novo)
    assert "Rodapé nunca deve mudar." in caminho.read_text(encoding="utf-8")


def test_bloqueia_escrita_em_index_sem_marcador(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_SEM_MARCADOR)

    with pytest.raises(Exception, match="BLOQUEADO"):
        escrever_ficheiro_seguro(caminho, _INDEX_SEM_MARCADOR + "<p>extra</p>")
    assert caminho.read_text(encoding="utf-8") == _INDEX_SEM_MARCADOR


# ── render_noticia_home — data real, link externo, nunca "hoje" ──────────

def test_render_noticia_home_usa_data_real_e_link_externo():
    bloco = render_noticia_home(_ENTRY)
    assert '<span class="badge-hoje">1 jul. 2026</span>' in bloco  # data real, não a palavra "hoje"
    assert ">Hoje<" not in bloco
    assert 'href="https://exemplo.pt/noticia-psu"' in bloco
    assert 'target="_blank"' in bloco
    assert "PSU aprovada no Parlamento" in bloco


# ── atualizar_index_home — integração fim-a-fim, idempotente ─────────────

def test_atualizar_index_home_injeta_bloco_e_e_idempotente(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_COM_MARCADOR)

    atualizar_index_home(_ENTRY, caminho=str(caminho))
    conteudo_apos_primeira = caminho.read_text(encoding="utf-8")
    assert "PSU aprovada no Parlamento" in conteudo_apos_primeira
    assert "Notícia antiga" not in conteudo_apos_primeira
    assert "Rodapé nunca deve mudar." in conteudo_apos_primeira

    atualizar_index_home(_ENTRY, caminho=str(caminho))
    conteudo_apos_segunda = caminho.read_text(encoding="utf-8")
    assert conteudo_apos_segunda == conteudo_apos_primeira


def test_atualizar_index_home_sem_marcador_nao_escreve(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_SEM_MARCADOR)

    atualizar_index_home(_ENTRY, caminho=str(caminho))

    assert caminho.read_text(encoding="utf-8") == _INDEX_SEM_MARCADOR
