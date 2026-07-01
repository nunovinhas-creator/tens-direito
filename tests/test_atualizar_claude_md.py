"""
Testes para scripts/atualizar_claude_md.py — regressão ao bug que gerava
linhas "Última revisão automática" duplicadas no CLAUDE.md sempre que o
pipeline corria mais do que uma vez no mesmo dia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from atualizar_claude_md import actualizar_revisao


def test_substitui_linha_existente_por_nova_data():
    conteudo = "texto\n\n---\n\n*Última revisão automática: 2026-06-30*\n"
    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert "Última revisão automática: 2026-07-01" in novo
    assert "2026-06-30" not in novo
    assert novo.count("Última revisão automática") == 1


def test_adiciona_linha_quando_nao_existe():
    conteudo = "texto sem linha de revisão\n"
    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert "Última revisão automática: 2026-07-01" in novo
    assert novo.count("Última revisão automática") == 1


def test_correr_duas_vezes_no_mesmo_dia_nao_duplica_linha():
    # Regressão directa do bug relatado: chamar a função outra vez com a
    # MESMA data (pipeline a correr uma segunda/terceira vez no mesmo dia)
    # não deve acrescentar uma segunda linha.
    conteudo = "texto\n\n---\n\n*Última revisão automática: 2026-07-01*\n"

    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert novo == conteudo  # nada muda — já está actualizado
    assert novo.count("Última revisão automática") == 1

    novo2 = actualizar_revisao(novo, "2026-07-01")
    assert novo2.count("Última revisão automática") == 1

    novo3 = actualizar_revisao(novo2, "2026-07-01")
    assert novo3.count("Última revisão automática") == 1


def test_so_substitui_a_data_preserva_resto_do_texto():
    conteudo = (
        "# CLAUDE.md\n\nconteúdo antes\n\n---\n\n"
        "*Última revisão automática: 2026-01-01*\n\n---\n\nconteúdo depois\n"
    )
    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert "conteúdo antes" in novo
    assert "conteúdo depois" in novo
    assert "Última revisão automática: 2026-07-01" in novo
    assert novo.count("Última revisão automática") == 1
