"""
Testes para o guardrail de scripts/gerar_noticias.py — allow-list estrita
em `escrever_ficheiro_seguro()`.

`noticias.html`, `noticias.json`, `feeds_saude_hoje.json` e
`noticias_candidatos.json` (os 2 últimos, Fase 3 do robustecimento de
2026-07-04) têm escrita livre; `index.html` só pode ser escrito dentro do
marcador `NOTICIA-HOME:INICIO/FIM`; qualquer outro nome é sempre bloqueado,
mesmo que nunca tenha sido pensado explicitamente (a função rejeita por
omissão, nunca escreve por omissão).

Todos os testes isolam o sistema de ficheiros com `tmp_path` — nunca
tocam nas páginas HTML reais do repositório.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gerar_noticias import (
    ItemNoticia,
    escrever_ficheiro_seguro,
    atualizar_index_home,
    ordenar_itens,
    render_noticia_home,
)

_ITEM = ItemNoticia(
    data_iso="2026-07-01",
    titulo="PSU aprovada no Parlamento",
    fonte_nome="Exemplo Notícias",
    url="https://exemplo.pt/noticia-psu",
    resumo="Resumo da notícia sobre a PSU.",
    categoria="apoios",
    cluster_id="prestacao-social-unica",
)

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


# ── noticias.html / noticias.json — escrita livre ─────────────────────────

def test_escreve_livremente_em_noticias_html(tmp_path):
    caminho = _escrever(tmp_path, "noticias.html", "<html>antigo</html>")
    escrever_ficheiro_seguro(caminho, "<html>novo conteúdo completo</html>")
    assert caminho.read_text(encoding="utf-8") == "<html>novo conteúdo completo</html>"


def test_escreve_livremente_em_noticias_json(tmp_path):
    caminho = _escrever(tmp_path, "noticias.json", '{"itens": []}')
    escrever_ficheiro_seguro(caminho, '{"itens": [{"titulo": "x"}]}')
    assert "titulo" in caminho.read_text(encoding="utf-8")


def test_escreve_livremente_em_feeds_saude_hoje_json(tmp_path):
    caminho = _escrever(tmp_path, "feeds_saude_hoje.json", "[]")
    escrever_ficheiro_seguro(caminho, '[{"nome": "abono_familia", "estado": "OK"}]')
    assert "abono_familia" in caminho.read_text(encoding="utf-8")


def test_escreve_livremente_em_noticias_candidatos_json(tmp_path):
    caminho = _escrever(tmp_path, "noticias_candidatos.json", "[]")
    escrever_ficheiro_seguro(caminho, '[{"data": "2026-07-04", "vencedor": null}]')
    assert "2026-07-04" in caminho.read_text(encoding="utf-8")


# ── qualquer outro ficheiro fora da allow-list — sempre bloqueado ─────────

def test_bloqueia_escrita_noutro_html_fora_da_lista(tmp_path):
    caminho = _escrever(tmp_path, "abono-de-familia.html", "<html>original</html>")
    with pytest.raises(Exception, match="BLOQUEADO"):
        escrever_ficheiro_seguro(caminho, "<html>alterado</html>")
    assert caminho.read_text(encoding="utf-8") == "<html>original</html>"


def test_bloqueia_escrita_em_ficheiro_nao_html_desconhecido(tmp_path):
    """A allow-list é estrita nos dois sentidos: um ficheiro que não seja
    .html e não conste em FICHEIROS_AUTO_GERADOS também é bloqueado —
    nunca há um "senão escreve" implícito."""
    caminho = _escrever(tmp_path, "qualquer-coisa.json", "{}")
    with pytest.raises(Exception, match="BLOQUEADO"):
        escrever_ficheiro_seguro(caminho, '{"x": 1}')
    assert caminho.read_text(encoding="utf-8") == "{}"


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
    bloco = render_noticia_home([_ITEM])
    assert '<span class="badge-hoje">1 jul. 2026</span>' in bloco  # data real, não a palavra "hoje"
    assert ">Hoje<" not in bloco
    assert 'href="https://exemplo.pt/noticia-psu"' in bloco
    assert 'target="_blank"' in bloco
    assert "PSU aprovada no Parlamento" in bloco


def test_render_noticia_home_respeita_limite():
    """render_noticia_home() espera a lista já ordenada (data desc) — a
    ordenação é responsabilidade explícita de ordenar_itens(), chamada
    pelo produtor real (atualizar_index_home)."""
    itens = ordenar_itens([
        ItemNoticia(data_iso=f"2026-06-{d:02d}", titulo=f"Item {d}", fonte_nome="X", url="https://x.pt", resumo="r", categoria="apoios")
        for d in (10, 15, 20, 25, 29)
    ])
    bloco = render_noticia_home(itens, limite=3)
    assert bloco.count('class="noticia-card"') == 3
    assert "Item 29" in bloco and "Item 25" in bloco and "Item 20" in bloco
    assert "Item 15" not in bloco and "Item 10" not in bloco


# ── atualizar_index_home — integração fim-a-fim, idempotente ─────────────

def test_atualizar_index_home_injeta_bloco_e_e_idempotente(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_COM_MARCADOR)

    atualizar_index_home([_ITEM], caminho=str(caminho))
    conteudo_apos_primeira = caminho.read_text(encoding="utf-8")
    assert "PSU aprovada no Parlamento" in conteudo_apos_primeira
    assert "Notícia antiga" not in conteudo_apos_primeira
    assert "Rodapé nunca deve mudar." in conteudo_apos_primeira

    atualizar_index_home([_ITEM], caminho=str(caminho))
    conteudo_apos_segunda = caminho.read_text(encoding="utf-8")
    assert conteudo_apos_segunda == conteudo_apos_primeira


def test_atualizar_index_home_sem_marcador_nao_escreve(tmp_path):
    caminho = _escrever(tmp_path, "index.html", _INDEX_SEM_MARCADOR)

    atualizar_index_home([_ITEM], caminho=str(caminho))

    assert caminho.read_text(encoding="utf-8") == _INDEX_SEM_MARCADOR
