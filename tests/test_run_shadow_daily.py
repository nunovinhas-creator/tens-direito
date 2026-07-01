"""
Testes para scripts/run_shadow_daily.py — orquestrador único da execução
diária do Shadow Mode.

Todos os testes isolam o sistema de ficheiros com `tmp_path` — nunca
tocam na árvore real do repositório nem na pasta `shadow_history/` real,
para não deixar artefactos gerados como efeito colateral de correr a
suite de testes.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import run_shadow_daily
import shadow_mode
import shadow_mode_analytics
import shadow_report_md
from run_shadow_daily import calcular_raiz_repo, coletar_alertas_do_dia, executar_shadow_daily

_HTML_DESATUALIZADO = """<html><body>
Bolsa de mérito para o ano lectivo 2024/2025. Valor: 1.200,00 €.
Verificado a 10 de outubro de 2024.
</body></html>"""

_HTML_OK = """<html><body>
Política de privacidade. Última actualização: 24 de junho de 2026.
</body></html>"""


def _preparar_repo_falso(tmp_path, *, com_alerta=True):
    (tmp_path / "pagina-ok.html").write_text(_HTML_OK, encoding="utf-8")
    if com_alerta:
        (tmp_path / "bolsa-de-merito.html").write_text(_HTML_DESATUALIZADO, encoding="utf-8")
    (tmp_path / "index.html").write_text(_HTML_DESATUALIZADO, encoding="utf-8")  # AUTO_GERADO -- deve ser ignorado
    return tmp_path


# ── Recolha de alertas (sem chamar verificar_datas.main) ───────────────────

def test_coletar_alertas_ignora_ficheiros_auto_gerados(tmp_path):
    _preparar_repo_falso(tmp_path)
    alertas = coletar_alertas_do_dia(tmp_path, ano=2026, mes=7)
    paginas = {a["pagina"] for a in alertas}
    assert "index.html" not in paginas  # AUTO_GERADO


def test_coletar_alertas_detecta_pagina_desatualizada(tmp_path):
    _preparar_repo_falso(tmp_path)
    alertas = coletar_alertas_do_dia(tmp_path, ano=2026, mes=7)
    paginas = {a["pagina"] for a in alertas}
    assert "bolsa-de-merito.html" in paginas
    assert "pagina-ok.html" not in paginas


def test_coletar_alertas_com_pasta_vazia_devolve_lista_vazia(tmp_path):
    assert coletar_alertas_do_dia(tmp_path, ano=2026, mes=7) == []


def test_coletar_alertas_ignora_ficheiro_ilegivel_sem_crashar(tmp_path):
    _preparar_repo_falso(tmp_path)
    # bytes inválidos em UTF-8 -- read_text() lança UnicodeDecodeError,
    # que tem de ser apanhado e o ficheiro ignorado, não propagado.
    (tmp_path / "pagina-corrompida.html").write_bytes(b"\xff\xfe\x00\x01")
    alertas = coletar_alertas_do_dia(tmp_path, ano=2026, mes=7)
    assert "pagina-corrompida.html" not in {a["pagina"] for a in alertas}


def test_calcular_raiz_repo_e_um_nivel_acima_de_scripts():
    raiz = calcular_raiz_repo()
    assert raiz.name != "scripts"
    assert (raiz / "scripts" / "run_shadow_daily.py").exists()


def test_coletar_alertas_nao_escreve_nada(tmp_path):
    _preparar_repo_falso(tmp_path)
    antes = sorted(p.name for p in tmp_path.iterdir())
    coletar_alertas_do_dia(tmp_path, ano=2026, mes=7)
    depois = sorted(p.name for p in tmp_path.iterdir())
    assert antes == depois


# ── Fluxo completo isolado ───────────────────────────────────────────────

def test_executar_shadow_daily_gera_ficheiro_com_nome_esperado(tmp_path):
    _preparar_repo_falso(tmp_path)
    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    caminho_esperado = tmp_path / "shadow_history" / "shadow_report_2026-07-01.md"
    assert Path(resultado["caminho_historico"]) == caminho_esperado
    assert caminho_esperado.exists()


def test_conteudo_do_ficheiro_coincide_com_o_devolvido(tmp_path):
    _preparar_repo_falso(tmp_path)
    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    conteudo_ficheiro = Path(resultado["caminho_historico"]).read_text(encoding="utf-8")
    assert conteudo_ficheiro == resultado["relatorio_markdown"]
    assert "# 📊 Relatório do Sistema — Shadow Mode" in conteudo_ficheiro


def test_pasta_shadow_history_e_criada_se_nao_existir(tmp_path):
    _preparar_repo_falso(tmp_path)
    assert not (tmp_path / "shadow_history").exists()
    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    assert (tmp_path / "shadow_history").is_dir()


def test_nao_escreve_nada_fora_da_pasta_shadow_history(tmp_path):
    _preparar_repo_falso(tmp_path)
    antes = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    depois = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    novos_ficheiros = depois - antes
    assert novos_ficheiros == {Path("shadow_history/shadow_report_2026-07-01.md")}


def test_resultado_inclui_total_de_alertas_e_analytics(tmp_path):
    _preparar_repo_falso(tmp_path)
    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    assert resultado["total_alertas"] == 1
    assert resultado["analytics"]["total_alertas"] == 1


# ── Múltiplos dias -- histórico acumulado ──────────────────────────────────

def test_execucoes_em_dias_diferentes_criam_ficheiros_separados(tmp_path):
    _preparar_repo_falso(tmp_path)
    for dia in (29, 30):
        executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 6, dia))
    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    ficheiros = sorted(p.name for p in (tmp_path / "shadow_history").glob("*.md"))
    assert ficheiros == [
        "shadow_report_2026-06-29.md",
        "shadow_report_2026-06-30.md",
        "shadow_report_2026-07-01.md",
    ]


def test_execucao_repetida_no_mesmo_dia_sobrescreve_sem_duplicar(tmp_path):
    _preparar_repo_falso(tmp_path)
    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))
    ficheiros = list((tmp_path / "shadow_history").glob("*.md"))
    assert len(ficheiros) == 1


# ── O fluxo liga mesmo os três módulos existentes ──────────────────────────

def test_fluxo_chama_shadow_mode_analytics_e_report(tmp_path, monkeypatch):
    _preparar_repo_falso(tmp_path)
    chamadas = {"shadow_mode": 0, "analytics": 0, "report": 0}

    original_shadow_mode = shadow_mode.executar_shadow_mode
    original_analytics = shadow_mode_analytics.analisar_shadow_mode
    original_report = shadow_report_md.gerar_relatorio_markdown

    def _espiao_shadow_mode(alertas, **kwargs):
        chamadas["shadow_mode"] += 1
        return original_shadow_mode(alertas, **kwargs)

    def _espiao_analytics(relatorios):
        chamadas["analytics"] += 1
        return original_analytics(relatorios)

    def _espiao_report(analytics, **kwargs):
        chamadas["report"] += 1
        return original_report(analytics, **kwargs)

    monkeypatch.setattr(run_shadow_daily, "executar_shadow_mode", _espiao_shadow_mode)
    monkeypatch.setattr(run_shadow_daily, "analisar_shadow_mode", _espiao_analytics)
    monkeypatch.setattr(run_shadow_daily, "gerar_relatorio_markdown", _espiao_report)

    executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    assert chamadas == {"shadow_mode": 1, "analytics": 1, "report": 1}


# ── Segurança: sem rede, sem GitHub, sem auto-update real ──────────────────

def test_modulo_nao_importa_requests_nem_github_nem_subprocess():
    assert not hasattr(run_shadow_daily, "requests")
    assert not hasattr(run_shadow_daily, "github")
    assert not hasattr(run_shadow_daily, "subprocess")


def test_modulo_nao_toca_na_flag_de_auto_update():
    # A docstring do módulo menciona "AUTO_UPDATE_HABILITADO" em prosa (a
    # explicar precisamente que o script NUNCA lhe toca) -- por isso o
    # que se verifica não é a ausência da palavra em texto livre, mas sim
    # que o módulo nunca importou decisao_datas (nem, já agora, tem
    # qualquer atributo com esse nome).
    assert not hasattr(run_shadow_daily, "decisao_datas")
    assert not hasattr(run_shadow_daily, "AUTO_UPDATE_HABILITADO")


def test_caminho_historico_fora_da_pasta_e_recusado(tmp_path):
    import pytest

    pasta_historico = tmp_path / "shadow_history"
    pasta_historico.mkdir()
    with pytest.raises(ValueError):
        run_shadow_daily._caminho_historico(pasta_historico, "../fora")


# ── CLI (main) não exige input e imprime o relatório no stdout ────────────

def test_main_imprime_relatorio_no_stdout_e_nao_pede_input(tmp_path, monkeypatch, capsys):
    _preparar_repo_falso(tmp_path)
    monkeypatch.setattr(run_shadow_daily, "calcular_raiz_repo", lambda: tmp_path)

    run_shadow_daily.main()

    saida = capsys.readouterr()
    assert "# 📊 Relatório do Sistema — Shadow Mode" in saida.out
    # As mensagens de progresso vão para stderr, não poluem o stdout.
    assert "✔" not in saida.out
    assert "✔ Shadow Mode executado" in saida.err
