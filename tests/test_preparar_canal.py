"""
Testes para scripts/preparar_canal.py — rascunho diário do canal de
WhatsApp (nunca publica, só prepara texto pronto a copiar).

Cobre os dois gatilhos construídos (alteração legal confirmada,
calendário mensal), a prioridade entre eles, o limite de 1
rascunho/dia, e os caminhos de silêncio (nada a publicar). O gatilho de
"notícia relevante" foi deliberadamente NÃO construído — ver
ROADMAP.md/CLAUDE.md — por isso não tem testes aqui.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from preparar_canal import (  # noqa: E402
    calendario_devido,
    formatar_rascunho_calendario,
    formatar_rascunho_legal,
    main,
    obter_pendente_legal,
)


def _escrever(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _preparar_repo_falso(
    tmp_path: Path,
    *,
    pendente=None,
    estado=None,
    calendario=None,
    nota_pendente="Fila preenchida à mão — ver CLAUDE.md.",
) -> Path:
    """
    `pendente`, quando passado, é a lista de entradas (não o documento
    inteiro) — o helper embrulha-a em {"_nota": ..., "entradas": [...]}
    para poupar cada teste de repetir a forma real do ficheiro.
    """
    dados_dir = tmp_path / "data"
    dados_dir.mkdir(parents=True, exist_ok=True)
    if pendente is not None:
        _escrever(
            dados_dir / "canal_pendente.json",
            {"_nota": nota_pendente, "entradas": pendente},
        )
    if estado is not None:
        _escrever(dados_dir / "canal_estado.json", estado)
    if calendario is not None:
        _escrever(dados_dir / "calendario_pagamentos.json", calendario)
    return tmp_path


_CALENDARIO_AGOSTO = {
    "meses": [
        {
            "ano": 2026,
            "mes": 8,
            "pagamentos": [
                {"dia": 8, "prestacoes": ["pensoes", "csi"]},
                {"dia": 16, "prestacoes": ["prestacoes_familiares"]},
                {"dia": 3, "prestacoes": ["doenca_profissional"]},
            ],
        }
    ]
}


# ── obter_pendente_legal ─────────────────────────────────────────────────


def test_fila_vazia_devolve_none():
    entrada, resto = obter_pendente_legal([])
    assert entrada is None
    assert resto == []


def test_devolve_a_entrada_mais_antiga_primeiro():
    fila = [
        {"titulo": "A", "resumo": "primeiro"},
        {"titulo": "B", "resumo": "segundo"},
    ]
    entrada, resto = obter_pendente_legal(fila)
    assert entrada["titulo"] == "A"
    assert resto == [{"titulo": "B", "resumo": "segundo"}]


def test_entrada_malformada_e_descartada_sem_bloquear_a_seguinte():
    fila = [
        {"titulo": "sem resumo"},
        "nao e um dict",
        {"titulo": "B", "resumo": "   "},
        {"titulo": "C", "resumo": "válida"},
    ]
    entrada, resto = obter_pendente_legal(fila)
    assert entrada["titulo"] == "C"
    assert resto == []


def test_fila_so_com_entradas_malformadas_devolve_none():
    fila = [{"titulo": "sem resumo"}, {"resumo": ""}]
    entrada, resto = obter_pendente_legal(fila)
    assert entrada is None
    assert resto == []


# ── calendario_devido ────────────────────────────────────────────────────


def test_calendario_nao_devido_antes_do_mes_chegar():
    import datetime as dt

    # calendário só tem agosto; hoje ainda é julho
    devido = calendario_devido(dt.date(2026, 7, 25), {}, _CALENDARIO_AGOSTO)
    assert devido is None


def test_calendario_devido_no_primeiro_dia_util_do_mes():
    import datetime as dt

    # 2026-08-01 é sábado — não conta
    assert calendario_devido(dt.date(2026, 8, 1), {}, _CALENDARIO_AGOSTO) is None
    # 2026-08-02 é domingo — não conta
    assert calendario_devido(dt.date(2026, 8, 2), {}, _CALENDARIO_AGOSTO) is None
    # 2026-08-03 é segunda — primeiro dia útil
    devido = calendario_devido(dt.date(2026, 8, 3), {}, _CALENDARIO_AGOSTO)
    assert devido is not None
    assert devido["mes"] == 8


def test_calendario_ja_entregue_este_mes_nao_volta_a_disparar():
    import datetime as dt

    estado = {"ultimo_calendario_publicado": "2026-08"}
    devido = calendario_devido(dt.date(2026, 8, 10), estado, _CALENDARIO_AGOSTO)
    assert devido is None


def test_calendario_sem_dados_do_mes_corrente_nunca_inventa():
    import datetime as dt

    devido = calendario_devido(dt.date(2026, 9, 3), {}, _CALENDARIO_AGOSTO)
    assert devido is None


# ── formatar_rascunho_* ──────────────────────────────────────────────────


def test_formatar_rascunho_legal_inclui_links_das_paginas():
    texto = formatar_rascunho_legal(
        {"resumo": "A Portaria X fecha as normas.", "paginas": ["a.html", "b.html"]}
    )
    assert "A Portaria X fecha as normas." in texto
    assert "https://tensdireito.com/a.html" in texto
    assert "https://tensdireito.com/b.html" in texto


def test_formatar_rascunho_legal_sem_paginas_nunca_deixa_linha_vazia_a_mais():
    texto = formatar_rascunho_legal({"resumo": "Só o resumo."})
    assert texto == "Só o resumo."


def test_formatar_rascunho_calendario_lista_dias_por_ordem_e_nomes_legiveis():
    mes = _CALENDARIO_AGOSTO["meses"][0]
    texto = formatar_rascunho_calendario(mes)
    # ordem: dia 3 antes de dia 8 antes de dia 16, mesmo a fonte não estando ordenada
    idx3 = texto.index("dia 3:")
    idx8 = texto.index("dia 8:")
    idx16 = texto.index("dia 16:")
    assert idx3 < idx8 < idx16
    assert "Pensões" in texto
    assert "Complemento Solidário para Idosos" in texto
    assert "calendario-pagamentos-seguranca-social.html" in texto


def test_formatar_rascunho_calendario_slug_desconhecido_nunca_crasha():
    mes = {"mes": 8, "ano": 2026, "pagamentos": [{"dia": 5, "prestacoes": ["algo_novo"]}]}
    texto = formatar_rascunho_calendario(mes)
    assert "algo_novo" in texto


# ── main() — integração isolada em tmp_path ──────────────────────────────


def test_main_sem_nada_pendente_e_sem_calendario_devido_nao_escreve_saida(tmp_path):
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario={"meses": []})
    saida = tmp_path / "saida.json"
    resultado = main(raiz=tmp_path, hoje="2026-07-15", saida=saida)
    assert resultado is None
    assert not saida.exists()


def test_main_entrega_alteracao_legal_e_consome_a_fila(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Portaria X", "resumo": "Texto pronto.", "paginas": ["x.html"]}],
        estado={},
        calendario={"meses": []},
    )
    saida = tmp_path / "saida.json"
    resultado = main(raiz=tmp_path, hoje="2026-08-30", saida=saida)

    assert resultado["gatilho"] == "alteracao_legal"
    assert resultado["titulo"] == "Portaria X"
    assert "Texto pronto." in resultado["texto"]
    assert saida.exists()

    documento_persistido = json.loads((tmp_path / "data" / "canal_pendente.json").read_text())
    assert documento_persistido["entradas"] == []

    estado_persistido = json.loads((tmp_path / "data" / "canal_estado.json").read_text())
    assert estado_persistido["ultima_entrega_canal"] == "2026-08-30"


def test_main_alteracao_legal_ganha_sobre_calendario_no_mesmo_dia(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Facto legal", "resumo": "Resumo pronto."}],
        estado={},
        calendario=_CALENDARIO_AGOSTO,
    )
    saida = tmp_path / "saida.json"
    # 2026-08-03 é o primeiro dia útil de agosto — o calendário estaria
    # devido, mas a fila legal tem prioridade
    resultado = main(raiz=tmp_path, hoje="2026-08-03", saida=saida)

    assert resultado["gatilho"] == "alteracao_legal"
    # o calendário NUNCA foi marcado como entregue — fica para o próximo dia
    estado_persistido = json.loads((tmp_path / "data" / "canal_estado.json").read_text())
    assert "ultimo_calendario_publicado" not in estado_persistido


def test_main_calendario_entregue_no_dia_seguinte_apos_colisao(tmp_path):
    # dia 1: fila legal consome o slot do dia
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Facto legal", "resumo": "Resumo pronto."}],
        estado={},
        calendario=_CALENDARIO_AGOSTO,
    )
    saida1 = tmp_path / "saida1.json"
    main(raiz=tmp_path, hoje="2026-08-03", saida=saida1)

    # dia seguinte: fila já vazia, calendário continua devido
    saida2 = tmp_path / "saida2.json"
    resultado = main(raiz=tmp_path, hoje="2026-08-04", saida=saida2)

    assert resultado["gatilho"] == "calendario"
    assert saida2.exists()


def test_main_calendario_entregue_uma_so_vez_por_mes(tmp_path):
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario=_CALENDARIO_AGOSTO)
    saida1 = tmp_path / "saida1.json"
    r1 = main(raiz=tmp_path, hoje="2026-08-03", saida=saida1)
    assert r1["gatilho"] == "calendario"

    saida2 = tmp_path / "saida2.json"
    r2 = main(raiz=tmp_path, hoje="2026-08-17", saida=saida2)
    assert r2 is None
    assert not saida2.exists()


def test_main_nao_crasha_sem_nenhum_ficheiro_de_dados(tmp_path):
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    resultado = main(raiz=tmp_path, hoje="2026-08-03", saida=tmp_path / "saida.json")
    assert resultado is None


def test_main_pendente_malformado_nao_crasha_e_segue_para_calendario(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "sem resumo"}],
        estado={},
        calendario=_CALENDARIO_AGOSTO,
    )
    saida = tmp_path / "saida.json"
    resultado = main(raiz=tmp_path, hoje="2026-08-03", saida=saida)
    assert resultado["gatilho"] == "calendario"
    documento_persistido = json.loads((tmp_path / "data" / "canal_pendente.json").read_text())
    assert documento_persistido["entradas"] == []


def test_nota_explicativa_sobrevive_ao_consumo_da_fila(tmp_path):
    # Lição de data/destaque_evento.json: uma nota explicativa que
    # desaparece numa reescrita automática fica esquecida em silêncio.
    # Confirma que _guardar a fila depois de consumir uma entrada nunca
    # apaga "_nota" (nem qualquer outra chave que viva ao lado de
    # "entradas").
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Facto legal", "resumo": "Resumo pronto."}],
        estado={},
        calendario={"meses": []},
        nota_pendente="PREENCHIDA À MÃO — nunca apagar esta nota.",
    )
    main(raiz=tmp_path, hoje="2026-08-30", saida=tmp_path / "saida.json")

    documento_persistido = json.loads((tmp_path / "data" / "canal_pendente.json").read_text())
    assert documento_persistido["_nota"] == "PREENCHIDA À MÃO — nunca apagar esta nota."
    assert documento_persistido["entradas"] == []


def test_ficheiro_real_de_producao_tem_nota_explicativa():
    # data/canal_pendente.json é preenchido à mão por sessões editoriais
    # — sem uma nota explicativa visível no próprio ficheiro, fica
    # esquecido (mesma lição de data/destaque_evento.json, cujas
    # instruções passaram 12 dias sem ninguém as ler). Este teste corre
    # sobre o ficheiro REAL do repositório, não uma cópia.
    caminho = Path(__file__).parent.parent / "data" / "canal_pendente.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    assert isinstance(dados, dict)
    assert "entradas" in dados
    nota = dados.get("_nota", "")
    assert len(nota) > 40, "nota explicativa em falta ou demasiado curta"
    assert "mão" in nota.lower() or "manual" in nota.lower()
    assert "CLAUDE.md" in nota
