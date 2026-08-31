"""
Testes para scripts/preparar_canal.py — rascunho diário do canal de
WhatsApp (nunca publica, só prepara texto pronto a copiar).

Cobre os gatilhos construídos — alteração legal confirmada (fila
manual), alteração legal por confirmar (caminho automático via
sentinela dirigido), calendário mensal — a prioridade entre eles, o
limite de 1 rascunho/dia, a deduplicação por ocorrência do caminho
automático, e os caminhos de silêncio (nada a publicar). O gatilho de
"notícia relevante" foi deliberadamente NÃO construído — ver
ROADMAP.md/CLAUDE.md — por isso não tem testes aqui.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from preparar_canal import (  # noqa: E402
    SENTINELAS_DIRIGIDOS,
    avisos_de_hoje,
    calendario_devido,
    formatar_rascunho_calendario,
    formatar_rascunho_legal,
    formatar_rascunho_sentinela,
    main,
    obter_deteccao_sentinela,
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


def _escrever_linha_avisos_log(tmp_path: Path, data_iso: str, chave_aviso: str, excerto: str) -> None:
    """
    Acrescenta uma linha a data/scraped/avisos.log no formato real
    escrito por `scripts/scraper_playwright.py::_registar_aviso`
    (timestamp ISO no início da linha + "AVISO slug=... motivo=chave:excerto").
    Cumulativo por desenho (`mode="a"`) — mesmo comportamento do ficheiro
    real, necessário para os testes de deduplicação por ocorrência (uma
    linha por dia, mesmo excerto).
    """
    caminho = tmp_path / "data" / "scraped" / "avisos.log"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    linha = f"{data_iso}T09:00:00.000000+00:00 AVISO slug=dre_x motivo={chave_aviso}:{excerto}\n"
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(linha)


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


# ── avisos_de_hoje / obter_deteccao_sentinela ───────────────────────────


def test_avisos_de_hoje_filtra_pelo_prefixo_da_data(tmp_path):
    caminho = tmp_path / "avisos.log"
    caminho.write_text(
        "2026-08-29T09:00:00+00:00 AVISO slug=x motivo=antigo:x\n"
        "2026-08-31T09:00:00+00:00 AVISO slug=x motivo=hoje:y\n",
        encoding="utf-8",
    )
    linhas = avisos_de_hoje(caminho, "2026-08-31")
    assert len(linhas) == 1
    assert "hoje:y" in linhas[0]


def test_avisos_de_hoje_ficheiro_inexistente_devolve_lista_vazia(tmp_path):
    assert avisos_de_hoje(tmp_path / "nao_existe.log", "2026-08-31") == []


def test_obter_deteccao_sentinela_reconhece_as_5_chaves_dirigidas():
    # As 5 chaves têm de bater exactamente com as que
    # scripts/scraper_playwright.py escreve (_registar_aviso) — nunca um
    # nome inventado que nunca dispararia na prática.
    assert set(SENTINELAS_DIRIGIDOS) == {
        "dre_psu_decreto_detectado",
        "dre_psu_regulamentacao_portaria_detectada",
        "dre_habitacao_paer_decreto_detectado",
        "dre_habitacao_garantia_decreto_detectado",
        "dre_ias_portaria_detectada",
    }


def test_obter_deteccao_sentinela_extrai_chave_e_excerto():
    avisos_hoje = [
        "2026-08-31T09:00:00+00:00 AVISO slug=dre_psu "
        "motivo=dre_psu_decreto_detectado:- Decreto-Lei n.º 200/2026 - Série I de 2026-08-31"
    ]
    deteccao = obter_deteccao_sentinela(avisos_hoje, {})
    assert deteccao is not None
    chave_aviso, excerto = deteccao
    assert chave_aviso == "dre_psu_decreto_detectado"
    assert "Decreto-Lei n.º 200/2026" in excerto


def test_obter_deteccao_sentinela_sem_sinal_hoje_devolve_none():
    assert obter_deteccao_sentinela([], {}) is None
    assert obter_deteccao_sentinela(["linha sem nenhuma chave dirigida"], {}) is None


def test_obter_deteccao_sentinela_ocorrencia_ja_rascunhada_nunca_repete():
    avisos_hoje = [
        "2026-08-31T09:00:00+00:00 AVISO slug=dre_psu "
        "motivo=dre_psu_decreto_detectado:- Decreto-Lei n.º 166/2026"
    ]
    ja_rascunhados = {"dre_psu_decreto_detectado": "- Decreto-Lei n.º 166/2026"}
    assert obter_deteccao_sentinela(avisos_hoje, ja_rascunhados) is None


def test_obter_deteccao_sentinela_excerto_diferente_conta_como_ocorrencia_nova():
    avisos_hoje = [
        "2026-09-01T09:00:00+00:00 AVISO slug=dre_psu "
        "motivo=dre_psu_decreto_detectado:- Decreto-Lei n.º 999/2026 - Série I de 2026-09-01"
    ]
    ja_rascunhados = {"dre_psu_decreto_detectado": "- Decreto-Lei n.º 166/2026"}
    deteccao = obter_deteccao_sentinela(avisos_hoje, ja_rascunhados)
    assert deteccao is not None
    assert "999/2026" in deteccao[1]


def test_formatar_rascunho_sentinela_avisa_para_nao_publicar_sem_confirmar():
    texto = formatar_rascunho_sentinela(
        "dre_ias_portaria_detectada", "- Portaria n.º 1/2027 - Série I de 2027-01-05"
    )
    assert "POR CONFIRMAR" in texto
    assert "Indexante dos Apoios Sociais" in texto
    assert "Portaria n.º 1/2027" in texto
    assert "Confirma o facto na fonte oficial" in texto


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


# ── main() — caminho automático (sentinela, "por confirmar") ────────────


def test_main_sentinela_prepara_rascunho_por_confirmar(tmp_path):
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario={"meses": []})
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-31", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 200/2026"
    )
    saida = tmp_path / "saida.json"
    resultado = main(raiz=tmp_path, hoje="2026-08-31", saida=saida)

    assert resultado is not None
    assert resultado["confirmado"] is False
    assert resultado["origem"] == "sentinela"
    assert resultado["sentinela"] == "dre_psu_decreto_detectado"
    assert "POR CONFIRMAR" in resultado["texto"]
    assert saida.exists()

    estado_persistido = json.loads((tmp_path / "data" / "canal_estado.json").read_text())
    assert estado_persistido["sentinelas_rascunhadas"] == {
        "dre_psu_decreto_detectado": "- Decreto-Lei n.º 200/2026"
    }
    assert estado_persistido["ultima_entrega_canal"] == "2026-08-31"


def test_main_sem_sinal_de_sentinela_hoje_nunca_produz_rascunho_por_confirmar(tmp_path):
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario={"meses": []})
    # sinal de ONTEM, nunca de hoje — avisos_de_hoje() tem de o excluir
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-30", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 200/2026"
    )
    resultado = main(raiz=tmp_path, hoje="2026-08-31", saida=tmp_path / "saida.json")
    assert resultado is None


def test_main_fila_manual_confirmada_ganha_sobre_sentinela_no_mesmo_dia(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Facto legal", "resumo": "Resumo pronto."}],
        estado={},
        calendario={"meses": []},
    )
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-31", "dre_ias_portaria_detectada", "- Portaria n.º 1/2027"
    )
    resultado = main(raiz=tmp_path, hoje="2026-08-31", saida=tmp_path / "saida.json")

    assert resultado["confirmado"] is True
    assert resultado["origem"] == "fila_manual"
    # o sinal do sentinela nunca foi "gasto" — fica elegível para o dia
    # seguinte, exactamente como o calendário fica em espera na colisão
    # já testada acima
    estado_persistido = json.loads((tmp_path / "data" / "canal_estado.json").read_text())
    assert "sentinelas_rascunhadas" not in estado_persistido


def test_main_sentinela_ganha_sobre_calendario_no_mesmo_dia(tmp_path):
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario=_CALENDARIO_AGOSTO)
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-03", "dre_habitacao_paer_decreto_detectado", "- Decreto-Lei n.º 5/2026"
    )
    # 2026-08-03 é o primeiro dia útil de agosto — o calendário estaria
    # devido, mas a detecção do sentinela (alteração legal) tem prioridade
    resultado = main(raiz=tmp_path, hoje="2026-08-03", saida=tmp_path / "saida.json")

    assert resultado["confirmado"] is False
    assert resultado["gatilho"] == "alteracao_legal"
    estado_persistido = json.loads((tmp_path / "data" / "canal_estado.json").read_text())
    assert "ultimo_calendario_publicado" not in estado_persistido


def test_main_mesma_ocorrencia_de_sentinela_nunca_gera_dois_rascunhos(tmp_path):
    # Cenário real (ver Issue #132 em CLAUDE.md): o mesmo sentinela
    # continua a devolver o MESMO excerto em dias seguidos, sem que
    # tenha havido nenhuma alteração legal nova.
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario={"meses": []})
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-27", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 166/2026"
    )
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-28", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 166/2026"
    )
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-29", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 166/2026"
    )

    r1 = main(raiz=tmp_path, hoje="2026-08-27", saida=tmp_path / "s1.json")
    assert r1 is not None
    assert r1["confirmado"] is False

    r2 = main(raiz=tmp_path, hoje="2026-08-28", saida=tmp_path / "s2.json")
    assert r2 is None

    r3 = main(raiz=tmp_path, hoje="2026-08-29", saida=tmp_path / "s3.json")
    assert r3 is None


def test_main_sentinela_com_excerto_novo_volta_a_gerar_rascunho(tmp_path):
    # A ocorrência muda de facto (um acto diferente) — nunca fica presa
    # ao "já rascunhado" de uma ocorrência anterior.
    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario={"meses": []})
    _escrever_linha_avisos_log(
        tmp_path, "2026-08-27", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 166/2026"
    )
    _escrever_linha_avisos_log(
        tmp_path, "2026-09-10", "dre_psu_decreto_detectado", "- Decreto-Lei n.º 999/2026"
    )

    r1 = main(raiz=tmp_path, hoje="2026-08-27", saida=tmp_path / "s1.json")
    assert r1["confirmado"] is False

    r2 = main(raiz=tmp_path, hoje="2026-09-10", saida=tmp_path / "s2.json")
    assert r2 is not None
    assert r2["confirmado"] is False
    assert "999/2026" in r2["texto"]


def test_main_calendario_e_fila_manual_continuam_confirmados(tmp_path):
    # Reconfirma que só o caminho do sentinela nasce "por confirmar" —
    # nenhuma regressão nos dois gatilhos já existentes.
    _preparar_repo_falso(
        tmp_path,
        pendente=[{"titulo": "Facto legal", "resumo": "Resumo pronto."}],
        estado={},
        calendario={"meses": []},
    )
    r1 = main(raiz=tmp_path, hoje="2026-08-30", saida=tmp_path / "s1.json")
    assert r1["confirmado"] is True

    _preparar_repo_falso(tmp_path, pendente=[], estado={}, calendario=_CALENDARIO_AGOSTO)
    r2 = main(raiz=tmp_path, hoje="2026-08-03", saida=tmp_path / "s2.json")
    assert r2["confirmado"] is True


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
