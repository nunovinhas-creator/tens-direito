"""
Testes para scripts/atualizar_claude_md.py.

Duas gerações de bug regressadas aqui:
1) linhas "Última revisão automática" duplicadas no HISTORICO.md sempre
   que o pipeline corria mais do que uma vez no mesmo dia (o script
   escrevia no CLAUDE.md até à Fase 1 da separação histórico/referência,
   2026-09-13).
2) o carimbo actualizado NO LUGAR onde já estivesse, em vez de movido
   para o fim — a Fase 1 migrou para `HISTORICO.md` uma ocorrência do
   carimbo já mal colocada (perto do início do ficheiro, não no fim) e
   cada corrida seguinte só lhe trocava a data, enterrando-o cada vez
   mais fundo à medida que sessões novas acrescentavam entradas reais ao
   fim do ficheiro real.
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


def test_carimbo_a_meio_do_ficheiro_e_movido_para_o_fim():
    # Regressão do bug real: o carimbo tinha ficado bracketed por "---"
    # dos dois lados A MEIO da cadeia de sessões (não era a última
    # entrada) — a versão antiga só lhe trocava a data ali mesmo,
    # enterrando-o cada vez mais fundo. A versão corrigida remove-o de
    # onde estiver e acrescenta-o de novo no fim real do ficheiro.
    conteudo = (
        "# Histórico\n\n---\n\n"
        "*Última revisão: 2026-06-28 — sessão antiga*\n\n---\n\n"
        "*Última revisão automática: 2026-09-13*\n\n---\n\n"
        "*Última revisão: 2026-07-05 — sessão mais recente*\n"
    )
    novo = actualizar_revisao(conteudo, "2026-09-14")

    assert novo.count("Última revisão automática") == 1
    assert "Última revisão automática: 2026-09-14" in novo
    # o carimbo é sempre a última coisa no ficheiro, depois da última
    # sessão real — nunca a meio
    assert novo.rstrip("\n").endswith("*Última revisão automática: 2026-09-14*")
    # nenhum separador "---" a dobrar (o que sobrava dos dois lados do
    # carimbo antigo tem de colapsar num só)
    assert "---\n\n---" not in novo
    # o conteúdo à volta do carimbo antigo mantém-se intacto e na mesma
    # ordem relativa
    assert novo.index("sessão antiga") < novo.index("sessão mais recente")
    assert novo.index("sessão mais recente") < novo.index("Última revisão automática: 2026-09-14")


def test_carimbo_ja_no_fim_e_so_tem_a_data_trocada():
    conteudo = (
        "# CLAUDE.md\n\nconteúdo antes\n\n---\n\n"
        "*Última revisão automática: 2026-01-01*\n"
    )
    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert "conteúdo antes" in novo
    assert "Última revisão automática: 2026-07-01" in novo
    assert novo.count("Última revisão automática") == 1
    assert novo.rstrip("\n").endswith("*Última revisão automática: 2026-07-01*")


def test_conteudo_depois_do_carimbo_antigo_passa_a_ficar_antes_dele():
    # Antes da correcção, um "conteúdo depois" que ficasse fisicamente a
    # seguir ao carimbo mal colocado mantinha-se ali (o bug: o carimbo
    # nunca se movia). Depois da correcção, esse conteúdo real passa a
    # ficar sempre ANTES do carimbo, porque o carimbo vai sempre para o
    # fim verdadeiro do ficheiro.
    conteudo = (
        "# CLAUDE.md\n\nconteúdo antes\n\n---\n\n"
        "*Última revisão automática: 2026-01-01*\n\n---\n\nconteúdo depois\n"
    )
    novo = actualizar_revisao(conteudo, "2026-07-01")
    assert "conteúdo antes" in novo
    assert "conteúdo depois" in novo
    assert novo.count("Última revisão automática") == 1
    assert novo.index("conteúdo depois") < novo.index("Última revisão automática: 2026-07-01")
    assert novo.rstrip("\n").endswith("*Última revisão automática: 2026-07-01*")
