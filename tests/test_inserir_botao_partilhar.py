"""
Testes para scripts/inserir_botao_partilhar.py — inserção automática e
idempotente do botão "Partilhar este artigo".

Todos os testes isolam o sistema de ficheiros com `tmp_path` — nunca
tocam nas páginas HTML reais do repositório.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import inserir_botao_partilhar as ibp
from inserir_botao_partilhar import (
    encontrar_paginas_alvo,
    processar_pagina,
)

_PAGINA_COM_H1 = """<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <title>Página de teste</title>
</head>
<body>
  <section class="hero">
    <div class="hero-inner">
      <h1>Título do artigo de teste</h1>
      <div class="resposta-direta">Resumo rápido.</div>
    </div>
  </section>
  <main>
    <p>Conteúdo do artigo.</p>
  </main>
</body>
</html>
"""

_PAGINA_SEM_H1_COM_MAIN = """<!DOCTYPE html>
<html lang="pt">
<head><title>Sem h1</title></head>
<body>
  <main>
    <p>Só tem main, sem h1.</p>
  </main>
</body>
</html>
"""

_PAGINA_SEM_H1_SEM_MAIN = """<!DOCTYPE html>
<html lang="pt">
<head><title>Nada</title></head>
<body>
  <p>Nem h1 nem main.</p>
</body>
</html>
"""

_PAGINA_JA_COM_BOTAO = """<!DOCTYPE html>
<html lang="pt">
<head>
  <link rel="stylesheet" href="/assets/css/share.css">
  <script src="/assets/js/share.js" defer></script>
</head>
<body>
  <h1>Já tratada</h1>
  <div class="partilhar-artigo">
    <button type="button" class="botao-partilhar" aria-label="Partilhar este artigo">📤 Partilhar este artigo</button>
  </div>
  <main><p>Conteúdo.</p></main>
</body>
</html>
"""


def _escrever(tmp_path, nome, conteudo):
    caminho = tmp_path / nome
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


# ── Inserção em páginas com <h1> ────────────────────────────────────────────

def test_insere_botao_imediatamente_apos_h1(tmp_path):
    caminho = _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)
    resultado = processar_pagina(caminho, raiz=tmp_path)

    assert resultado.alterada is True
    assert "após <h1>" in resultado.motivo

    conteudo = caminho.read_text(encoding="utf-8")
    pos_h1 = conteudo.index("</h1>")
    pos_botao = conteudo.index("botao-partilhar")
    pos_resposta_direta = conteudo.index("resposta-direta")
    # O botão fica entre o fecho do h1 e o resto do conteúdo que já lá estava.
    assert pos_h1 < pos_botao < pos_resposta_direta


def test_insere_referencias_css_e_js_antes_de_head(tmp_path):
    caminho = _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)
    processar_pagina(caminho, raiz=tmp_path)
    conteudo = caminho.read_text(encoding="utf-8")

    assert '<link rel="stylesheet" href="/assets/css/share.css">' in conteudo
    assert '<script src="/assets/js/share.js" defer></script>' in conteudo
    assert conteudo.index("share.css") < conteudo.index("</head>")
    assert conteudo.index("share.js") < conteudo.index("</head>")


def test_texto_e_aria_label_do_botao():
    # Verifica directamente o bloco inserido, sem depender de nenhuma página.
    assert "aria-label=\"Partilhar este artigo\"" in ibp.BLOCO_BOTAO
    assert "📤 Partilhar este artigo" in ibp.BLOCO_BOTAO
    assert "<button type=\"button\"" in ibp.BLOCO_BOTAO  # elemento nativo -- acessível por teclado


# ── Fallback: sem <h1>, com <main> ──────────────────────────────────────────

def test_insere_antes_de_fecho_main_quando_nao_ha_h1(tmp_path):
    caminho = _escrever(tmp_path, "sem-h1.html", _PAGINA_SEM_H1_COM_MAIN)
    resultado = processar_pagina(caminho, raiz=tmp_path)

    assert resultado.alterada is True
    assert "</main>" in resultado.motivo

    conteudo = caminho.read_text(encoding="utf-8")
    pos_botao = conteudo.index("botao-partilhar")
    pos_fecho_main = conteudo.index("</main>")
    assert pos_botao < pos_fecho_main


# ── Sem h1 nem main: não alterável ──────────────────────────────────────────

def test_pagina_sem_h1_nem_main_nao_e_alterada(tmp_path):
    caminho = _escrever(tmp_path, "vazia.html", _PAGINA_SEM_H1_SEM_MAIN)
    conteudo_antes = caminho.read_text(encoding="utf-8")

    resultado = processar_pagina(caminho, raiz=tmp_path)

    assert resultado.alterada is False
    assert "sem ponto de inserção" in resultado.motivo
    assert caminho.read_text(encoding="utf-8") == conteudo_antes


# ── Idempotência (obrigatória) ──────────────────────────────────────────────

def test_pagina_ja_com_botao_nao_e_alterada(tmp_path):
    caminho = _escrever(tmp_path, "ja-tratada.html", _PAGINA_JA_COM_BOTAO)
    conteudo_antes = caminho.read_text(encoding="utf-8")

    resultado = processar_pagina(caminho, raiz=tmp_path)

    assert resultado.alterada is False
    assert "já tem" in resultado.motivo
    assert caminho.read_text(encoding="utf-8") == conteudo_antes


def test_correr_duas_vezes_nao_duplica_nem_altera(tmp_path):
    caminho = _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)

    r1 = processar_pagina(caminho, raiz=tmp_path)
    conteudo_apos_primeira = caminho.read_text(encoding="utf-8")

    r2 = processar_pagina(caminho, raiz=tmp_path)
    conteudo_apos_segunda = caminho.read_text(encoding="utf-8")

    assert r1.alterada is True
    assert r2.alterada is False
    assert conteudo_apos_primeira == conteudo_apos_segunda
    # Só um botão -- não duplicado.
    assert conteudo_apos_segunda.count("botao-partilhar") == 1
    assert conteudo_apos_segunda.count("share.js") == 1
    assert conteudo_apos_segunda.count("share.css") == 1


def test_correr_tres_vezes_seguidas_e_estavel(tmp_path):
    caminho = _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)
    for _ in range(3):
        processar_pagina(caminho, raiz=tmp_path)
    conteudo = caminho.read_text(encoding="utf-8")
    assert conteudo.count("botao-partilhar") == 1


# ── Não corrompe título / meta description / JSON-LD / URLs ───────────────

def test_nao_altera_title_nem_meta_nem_resto_do_conteudo(tmp_path):
    pagina = _PAGINA_COM_H1.replace(
        "<title>Página de teste</title>",
        '<title>Página de teste</title>\n  <meta name="description" content="Descrição original.">',
    )
    caminho = _escrever(tmp_path, "artigo.html", pagina)
    processar_pagina(caminho, raiz=tmp_path)
    conteudo = caminho.read_text(encoding="utf-8")

    assert "<title>Página de teste</title>" in conteudo
    assert 'content="Descrição original."' in conteudo
    assert "<p>Conteúdo do artigo.</p>" in conteudo
    assert "Título do artigo de teste" in conteudo


# ── Descoberta de páginas-alvo (exclui AUTO_GERADOS) ────────────────────────

def test_encontrar_paginas_alvo_ignora_auto_gerados(tmp_path):
    _escrever(tmp_path, "index.html", _PAGINA_COM_H1)
    _escrever(tmp_path, "noticias.html", _PAGINA_COM_H1)
    _escrever(tmp_path, "404.html", _PAGINA_COM_H1)
    _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)

    nomes = {p.name for p in encontrar_paginas_alvo(tmp_path)}
    assert nomes == {"artigo.html"}


def test_encontrar_paginas_alvo_inclui_subpasta_p(tmp_path):
    (tmp_path / "p").mkdir()
    _escrever(tmp_path, "artigo.html", _PAGINA_COM_H1)
    (tmp_path / "p" / "pilar.html").write_text(_PAGINA_COM_H1, encoding="utf-8")

    nomes = {str(p.relative_to(tmp_path)) for p in encontrar_paginas_alvo(tmp_path)}
    assert nomes == {"artigo.html", "p/pilar.html"}


# ── Robustez ─────────────────────────────────────────────────────────────

def test_ficheiro_inexistente_nao_crasha(tmp_path):
    resultado = processar_pagina(tmp_path / "nao-existe.html", raiz=tmp_path)
    assert resultado.alterada is False
    assert "erro ao ler" in resultado.motivo
