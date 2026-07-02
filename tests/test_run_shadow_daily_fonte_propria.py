"""
Testes para a Fase 1 do robustecimento do Shadow Mode — confirmar que
`run_shadow_daily.py` gera sempre os seus próprios dados (nunca depende
de `data/alertas_datas.json` escrito por outro workflow) e que o
relatório nunca reporta "0 alertas" como "sistema estável" sem marcar
isso como anomalia quando há páginas suficientes analisadas.
"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_shadow_daily import executar_shadow_daily

_HTML_DESATUALIZADO = """<html><body>
Bolsa de mérito para o ano lectivo 2024/2025. Valor: 1.200,00 €.
Verificado a 10 de outubro de 2024.
</body></html>"""

_HTML_OK = """<html><body>
Política de privacidade. Última actualização: 24 de junho de 2026.
</body></html>"""


def _repo_com_muitas_paginas_sem_alerta(tmp_path, total=30):
    for i in range(total):
        (tmp_path / f"pagina-{i:02d}.html").write_text(_HTML_OK, encoding="utf-8")
    return tmp_path


def test_relatorio_reporta_pelo_menos_um_alerta_com_pagina_desatualizada(tmp_path):
    (tmp_path / "bolsa-de-merito.html").write_text(_HTML_DESATUALIZADO, encoding="utf-8")
    (tmp_path / "pagina-ok.html").write_text(_HTML_OK, encoding="utf-8")

    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    assert resultado["total_alertas"] >= 1
    assert "Alertas analisados: 1" in resultado["relatorio_markdown"]


def test_nao_depende_de_data_alertas_datas_json_no_checkout(tmp_path):
    # Nenhum data/alertas_datas.json existe -- e mesmo assim o alerta é
    # encontrado, porque a deteção corre em runtime sobre o HTML real,
    # nunca a partir de um ficheiro que outro workflow possa (ou não)
    # ter commitado.
    assert not (tmp_path / "data").exists()
    (tmp_path / "bolsa-de-merito.html").write_text(_HTML_DESATUALIZADO, encoding="utf-8")

    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    assert resultado["total_alertas"] == 1
    assert not (tmp_path / "data").exists()  # continua sem escrever em data/


def test_zero_alertas_com_muitas_paginas_e_marcado_como_anomalia(tmp_path):
    _repo_com_muitas_paginas_sem_alerta(tmp_path, total=30)

    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    assert resultado["total_alertas"] == 0
    assert resultado["paginas_analisadas"] == 30
    assert "ANOMALIA" in resultado["relatorio_markdown"]
    assert "sistema estável" not in resultado["relatorio_markdown"].lower() or "não interpretar" in resultado["relatorio_markdown"]


def test_zero_alertas_com_poucas_paginas_nao_e_anomalia(tmp_path):
    (tmp_path / "pagina-ok.html").write_text(_HTML_OK, encoding="utf-8")

    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1))

    assert resultado["total_alertas"] == 0
    assert resultado["paginas_analisadas"] == 1
    assert "ANOMALIA" not in resultado["relatorio_markdown"]
    assert "O sistema está estável" in resultado["relatorio_markdown"]


def test_relatorio_inclui_proveniencia_com_horas_e_paginas(tmp_path):
    _repo_com_muitas_paginas_sem_alerta(tmp_path, total=5)

    resultado = executar_shadow_daily(raiz=tmp_path, agora=datetime(2026, 7, 1, 6, 41))

    texto = resultado["relatorio_markdown"]
    assert "## Proveniência dos dados" in texto
    assert "Páginas HTML analisadas nesta execução: 5" in texto
    assert "Hora de execução (UTC): 06:41" in texto
