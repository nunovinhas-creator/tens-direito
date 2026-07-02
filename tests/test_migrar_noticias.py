"""
Testes para scripts/migrar_noticias.py — migração única de noticias.html
para data/noticias.json, com limpeza (dedup + descarte de registos
vazios/corrompidos).

Todos os testes isolam o sistema de ficheiros com `tmp_path` e HTML de
fixture — nunca tocam no noticias.html real do repositório.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from migrar_noticias import (
    deduplicar_mantendo_mais_antiga,
    extrair_itens_legado,
)

_HTML_COM_DUPLICADOS_E_LIXO = """<!DOCTYPE html>
<html>
<body>
  <!-- DESTAQUE-INICIO -->
  <article class="destaque-card" data-cat="apoios">
    <div class="destaque-meta">
      <span class="cat-badge cat-apoios"><span class="cat-dot"></span><span class="cat-label">Apoios Sociais</span></span>
      <time datetime="2026-06-29">29 jun. 2026</time>
    </div>
    <h2 class="destaque-titulo">Pensões e apoios em julho - Notícias ao Minuto</h2>
    <p class="destaque-resumo">Pensões e apoios em julho Notícias ao Minuto…</p>
    <a href="https://news.google.com/rss/articles/AAA" class="destaque-link" target="_blank" rel="noopener noreferrer">Ler notícia completa →</a>
  </article>
  <!-- DESTAQUE-FIM -->
  <div class="cards-grid" id="cards-grid">
  <!-- ARQUIVO-INICIO -->
  <article class="arquivo-card" data-cat="apoios">
    <div class="arquivo-meta">
      <span class="cat-badge cat-apoios"><span class="cat-dot"></span><span class="cat-label">Apoios Sociais</span></span>
      <time datetime="2026-06-25">25 jun. 2026</time>
    </div>
    <h3 class="arquivo-titulo">Pensões e apoios em julho - Notícias ao Minuto</h3>
    <p class="arquivo-resumo">Pensões e apoios em julho Notícias ao Minuto…</p>
    <a href="https://news.google.com/rss/articles/AAA" class="arquivo-link" target="_blank" rel="noopener noreferrer">Ler →</a>
  </article>
  <article class="arquivo-card" data-cat="apoios">
    <div class="arquivo-meta">
      <span class="cat-badge cat-apoios"><span class="cat-dot"></span><span class="cat-label">Apoios Sociais</span></span>
      <time datetime=""></time>
    </div>
    <h3 class="arquivo-titulo">Notícia anterior</h3>
    <p class="arquivo-resumo"></p>
    <a href="#" class="arquivo-link" target="_blank" rel="noopener noreferrer">Ler →</a>
  </article>
  <article class="noticia-card" data-cat="educacao">
    <div class="card-meta">
      <span class="cat-dot educacao"></span>
      <span class="cat-label educacao">Educação</span>
      <span class="card-data">23 Jun 2026</span>
    </div>
    <h3>Candidaturas à ASE 2026/2027 abrem em setembro</h3>
    <p class="card-resumo">As candidaturas à ASE abrem com o início das aulas.</p>
    <a href="https://www.dge.mec.pt" class="card-fonte" target="_blank" rel="noopener">→ Fonte: dge.mec.pt</a>
  </article>
  <article class="noticia-card" data-cat="educacao">
    <div class="card-meta">
      <span class="cat-dot educacao"></span>
      <span class="cat-label educacao">Educação</span>
      <span class="card-data">18 Jun 2026</span>
    </div>
    <h3>Bolsas de mérito 2026: candidaturas abertas</h3>
    <p class="card-resumo">Alunos do secundário podem candidatar-se à bolsa de mérito.</p>
    <a href="https://www.dge.mec.pt" class="card-fonte" target="_blank" rel="noopener">→ Fonte: dge.mec.pt</a>
  </article>
  <!-- ARQUIVO-FIM -->
  </div>
</body>
</html>
"""


def test_extrai_destaque_e_arquivo_nos_dois_formatos():
    itens, invalidos = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    titulos = {i.titulo for i in itens}
    assert "Pensões e apoios em julho" in titulos  # destaque (sem sufixo de fonte)
    assert "Candidaturas à ASE 2026/2027 abrem em setembro" in titulos  # noticia-card legado
    assert "Bolsas de mérito 2026: candidaturas abertas" in titulos


def test_descarta_placeholder_vazio():
    itens, invalidos = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    assert invalidos == 1
    assert all(i.titulo != "Notícia anterior" for i in itens)


def test_extrai_fonte_de_href_com_ordem_de_atributos_invertida():
    """href vem antes de class="card-fonte" no HTML real — regressão do
    bug encontrado na primeira tentativa de migração (0 legados extraídos)."""
    itens, _ = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    ase = next(i for i in itens if "ASE" in i.titulo)
    assert ase.url == "https://www.dge.mec.pt"
    assert ase.fonte_nome == "dge.mec.pt"


def test_deduplicar_mantem_data_mais_antiga():
    itens, _ = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    mantidos, removidos = deduplicar_mantendo_mais_antiga(itens)

    pensoes = [i for i in mantidos if "Pensões" in i.titulo]
    assert len(pensoes) == 1
    assert pensoes[0].data_iso == "2026-06-25"  # a mais antiga das duas ocorrências (25 e 29 jun)
    assert len(removidos) == 1
    assert removidos[0][1] == "2026-06-25"  # motivo aponta para a data mantida


def test_deduplicar_nao_junta_itens_com_url_generica_diferente():
    itens, _ = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    mantidos, removidos = deduplicar_mantendo_mais_antiga(itens)

    titulos_mantidos = {i.titulo for i in mantidos}
    assert "Candidaturas à ASE 2026/2027 abrem em setembro" in titulos_mantidos
    assert "Bolsas de mérito 2026: candidaturas abertas" in titulos_mantidos


def test_total_final_apos_limpeza():
    itens, invalidos = extrair_itens_legado(_HTML_COM_DUPLICADOS_E_LIXO)
    mantidos, removidos = deduplicar_mantendo_mais_antiga(itens)
    assert invalidos == 1
    assert len(itens) == 4  # destaque + 1 arquivo-card válido + 2 noticia-card (exclui o placeholder)
    assert len(removidos) == 1  # o "Pensões..." duplicado
    assert len(mantidos) == 3
