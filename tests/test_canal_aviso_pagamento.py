"""
Testes do aviso de pagamento na véspera (gatilho 4 de
scripts/preparar_canal.py) e do step "Criar Issue do rascunho do canal"
de pipeline-diario.yml (assignee, menção, blocos separados).

O step do workflow é testado correndo o JavaScript REAL extraído do
YAML em Node, com `github`/`context` simulados — nunca uma cópia.
"""
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from atualizar_calendario import VISTA_PRESTACOES  # noqa: E402
from atualizar_calendario import PRESTACOES  # noqa: E402
from preparar_canal import (  # noqa: E402
    EXCLUSOES_DESCRICAO,
    URL_CALENDARIO,
    aviso_pagamento_devido,
    calendario_devido,
    descricao_da_pagina,
    e_dia_util,
    feriados_nacionais,
    formatar_aviso_pagamento,
    main,
    pagamentos_por_data,
    vespera_util,
)

D = dt.date


def _escrever(caminho: Path, dados) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


def _calendario(ano, mes, pagamentos):
    return {"meses": [{"ano": ano, "mes": mes, "pagamentos": pagamentos}]}


def _repo(tmp_path, *, calendario, estado=None, pendente=None, paginas=None):
    _escrever(tmp_path / "data" / "calendario_pagamentos.json", calendario)
    # Por omissão o mensal de setembro já foi entregue — isola o aviso de
    # véspera; o teste do mensal passa `estado={}` de propósito.
    if estado is None:
        estado = {"ultimo_calendario_publicado": "2026-09"}
    _escrever(tmp_path / "data" / "canal_estado.json", estado)
    _escrever(
        tmp_path / "data" / "canal_pendente.json",
        {"_nota": "Fila preenchida à mão.", "entradas": pendente or []},
    )
    for nome, conteudo in (paginas or {}).items():
        (tmp_path / nome).write_text(conteudo, encoding="utf-8")
    return tmp_path


def _estado(tmp_path):
    return json.loads((tmp_path / "data" / "canal_estado.json").read_text())


# ── Feriados e dia útil ──────────────────────────────────────────────────


def test_feriados_2026_batem_com_o_artigo_234_do_codigo_do_trabalho():
    # Páscoa de 2026 = 5 de abril → Sexta-Feira Santa 3/4, Corpo de Deus 4/6.
    esperado = {
        D(2026, 1, 1), D(2026, 4, 3), D(2026, 4, 5), D(2026, 4, 25),
        D(2026, 5, 1), D(2026, 6, 4), D(2026, 6, 10), D(2026, 8, 15),
        D(2026, 10, 5), D(2026, 11, 1), D(2026, 12, 1), D(2026, 12, 8),
        D(2026, 12, 25),
    }
    assert feriados_nacionais(2026) == esperado


def test_pascoa_de_outros_anos_bate_com_o_calendario():
    # Sexta-Feira Santa conhecida: 2025-04-18, 2027-03-26, 2028-04-14.
    assert D(2025, 4, 18) in feriados_nacionais(2025)
    assert D(2027, 3, 26) in feriados_nacionais(2027)
    assert D(2028, 4, 14) in feriados_nacionais(2028)


def test_carnaval_nao_e_feriado_obrigatorio():
    assert e_dia_util(D(2026, 2, 17))  # Terça-feira de Carnaval


def test_fim_de_semana_nunca_e_dia_util():
    assert not e_dia_util(D(2026, 9, 26))
    assert not e_dia_util(D(2026, 9, 27))


# ── Véspera útil ─────────────────────────────────────────────────────────


def test_vespera_de_dia_de_semana_e_o_dia_anterior():
    assert vespera_util(D(2026, 9, 8)) == D(2026, 9, 7)


def test_pagamento_a_segunda_tem_vespera_na_sexta():
    assert vespera_util(D(2026, 9, 7)) == D(2026, 9, 4)


def test_vespera_salta_feriado_de_5_de_outubro():
    # 5/10/2026 é segunda-feira e feriado → pagamento de terça avisado na sexta.
    assert vespera_util(D(2026, 10, 6)) == D(2026, 10, 2)


def test_vespera_salta_sexta_feira_santa_e_fim_de_semana():
    assert vespera_util(D(2026, 4, 6)) == D(2026, 4, 2)


def test_vespera_salta_natal():
    assert vespera_util(D(2026, 12, 28)) == D(2026, 12, 24)


# ── Quando o aviso é devido ──────────────────────────────────────────────

_CAL_SET = _calendario(2026, 9, [
    {"dia": 7, "prestacoes": ["apoio_renda"]},
    {"dia": 8, "prestacoes": ["psi", "csi"]},
    {"dia": 8, "prestacoes": ["csi", "pensoes"], "metodo": ["vale_de_correio"]},
])


def test_aviso_devido_na_vespera_util():
    assert aviso_pagamento_devido(D(2026, 9, 4), {}, _CAL_SET) == (D(2026, 9, 7), ["apoio_renda"])


def test_aviso_nunca_antes_da_vespera():
    assert aviso_pagamento_devido(D(2026, 9, 3), {}, _CAL_SET) is None


def test_aviso_nunca_no_proprio_dia_do_pagamento():
    # 8/9 é o próprio dia do pagamento de 8 e não é véspera de nada.
    assert aviso_pagamento_devido(D(2026, 9, 8), {"avisos_pagamento_entregues": []},
                                  _calendario(2026, 9, [{"dia": 8, "prestacoes": ["psi"]}])) is None


def test_corrida_da_vespera_falhada_e_recuperada_ao_sabado():
    assert aviso_pagamento_devido(D(2026, 9, 5), {}, _CAL_SET) == (D(2026, 9, 7), ["apoio_renda"])


def test_dia_ja_avisado_nunca_repete():
    estado = {"avisos_pagamento_entregues": ["2026-09-07"]}
    assert aviso_pagamento_devido(D(2026, 9, 4), estado, _CAL_SET) is None


def test_pagamento_no_inicio_do_mes_seguinte_usa_dados_do_proximo_mes():
    cal = {"meses": [
        {"ano": 2026, "mes": 9, "pagamentos": [{"dia": 28, "prestacoes": ["rsi"]}]},
        {"ano": 2026, "mes": 10, "pagamentos": [{"dia": 1, "prestacoes": ["pensoes"]}]},
    ]}
    assert aviso_pagamento_devido(D(2026, 9, 30), {}, cal) == (D(2026, 10, 1), ["pensoes"])


# ── Agrupamento ──────────────────────────────────────────────────────────


def test_varias_entradas_do_mesmo_dia_fundidas_sem_repetidos():
    assert pagamentos_por_data(_CAL_SET)[D(2026, 9, 8)] == ["psi", "csi", "pensoes"]


def test_mesmo_dia_gera_uma_so_mensagem_com_todas_as_prestacoes(tmp_path):
    texto = formatar_aviso_pagamento(tmp_path, D(2026, 9, 7), D(2026, 9, 8), ["psi", "csi", "pensoes"])
    assert texto.startswith("Amanhã (dia 8), a Segurança Social paga:")
    assert texto.count("Amanhã") == 1
    for nome in ("Prestação Social para a Inclusão (PSI)",
                 "Complemento Solidário para Idosos (CSI)", "• Pensões"):
        assert nome in texto


def test_pagamento_a_segunda_avisado_na_sexta_nunca_diz_amanha(tmp_path):
    texto = formatar_aviso_pagamento(tmp_path, D(2026, 9, 4), D(2026, 9, 7), ["apoio_renda"])
    assert texto.startswith("Segunda-feira (dia 7), a Segurança Social paga:")
    assert "Amanhã" not in texto


# ── Descrições vindas do site ────────────────────────────────────────────

_PAGINA_RAPIDA = """<html><div class="resposta-direta resposta-rapida">
<span class="resposta-rapida-label">⚡ Resposta rápida</span>
<p class="resposta-rapida-texto">O CSI paga a diferen&ccedil;a ao abrigo do <strong>n.º 2</strong> — até 1.º escalão. Segunda frase.</p>
</div></html>"""
_PAGINA_DIRECTA = """<html><div class="resposta-direta">
  Pago pela Segurança Social durante a licença. Outra frase.
</div></html>"""


def test_descricao_usa_a_primeira_frase_da_resposta_rapida(tmp_path):
    (tmp_path / "x.html").write_text(_PAGINA_RAPIDA, encoding="utf-8")
    assert descricao_da_pagina(tmp_path, "/x.html") == (
        "O CSI paga a diferença ao abrigo do n.º 2 — até 1.º escalão."
    )


def test_descricao_sem_resposta_rapida_usa_resposta_directa(tmp_path):
    (tmp_path / "x.html").write_text(_PAGINA_DIRECTA, encoding="utf-8")
    assert descricao_da_pagina(tmp_path, "/x.html") == "Pago pela Segurança Social durante a licença."


def test_descricao_de_pagina_inexistente_e_none(tmp_path):
    assert descricao_da_pagina(tmp_path, "/nao-existe.html") is None


def test_prestacao_sem_pagina_fica_so_com_nome_e_link_do_calendario(tmp_path):
    texto = formatar_aviso_pagamento(tmp_path, D(2026, 9, 22), D(2026, 9, 23), ["fgs"])
    linhas = texto.splitlines()
    i = linhas.index("• Fundo de Garantia Salarial")
    assert linhas[i + 1] == ""  # nenhuma descrição, nenhum link próprio
    assert texto.rstrip().endswith(URL_CALENDARIO)
    assert texto.count("https://") == 1


def test_prestacao_com_pagina_leva_descricao_e_link(tmp_path):
    (tmp_path / "rsi.html").write_text(_PAGINA_DIRECTA, encoding="utf-8")
    texto = formatar_aviso_pagamento(tmp_path, D(2026, 9, 22), D(2026, 9, 23), ["rsi"])
    assert "  Pago pela Segurança Social durante a licença.\n  https://tensdireito.com/rsi.html" in texto


def test_apoio_a_renda_fica_so_com_o_nome_por_exclusao_explicita(tmp_path):
    (tmp_path / "apoio-extraordinario-renda.html").write_text(_PAGINA_DIRECTA, encoding="utf-8")
    texto = formatar_aviso_pagamento(tmp_path, D(2026, 9, 4), D(2026, 9, 7), ["apoio_renda"])
    linhas = texto.splitlines()
    i = linhas.index("• Apoio extraordinário à renda")
    assert linhas[i + 1] == ""
    assert "Pago pela" not in texto and "apoio-extraordinario-renda.html" not in texto
    assert texto.count("https://") == 1


@pytest.mark.parametrize("slug", sorted(EXCLUSOES_DESCRICAO))
def test_exclusao_de_descricao_nunca_orfa(slug):
    # Órfã = prestação que já não existe, ou que já não tem página (a
    # exclusão deixaria de fazer alguma coisa).
    assert slug in PRESTACOES
    assert any(slug in slugs and url for _a, _n, slugs, url in VISTA_PRESTACOES)
    assert EXCLUSOES_DESCRICAO[slug].strip()


@pytest.mark.parametrize("url", sorted({u for *_x, u in VISTA_PRESTACOES if u}))
def test_todas_as_paginas_reais_do_calendario_tem_descricao(url):
    # Guarda contra uma reestruturação de página que deixe o aviso sem
    # descrição em silêncio — corre sobre as páginas REAIS.
    descricao = descricao_da_pagina(RAIZ, url)
    assert descricao and len(descricao) > 20 and descricao.endswith((".", "!", "?"))


# ── main(): estado e colisões ────────────────────────────────────────────


def test_main_aviso_sozinho_e_regista_o_dia(tmp_path):
    _repo(tmp_path, calendario=_CAL_SET)
    r = main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s.json")
    assert [b["gatilho"] for b in r["blocos"]] == ["pagamento"]
    assert r["blocos"][0]["data_pagamento"] == "2026-09-07"
    assert _estado(tmp_path)["avisos_pagamento_entregues"] == ["2026-09-07"]


def test_main_nunca_repete_o_mesmo_dia_de_pagamento(tmp_path):
    _repo(tmp_path, calendario=_CAL_SET)
    assert main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s1.json") is not None
    # Mesmo dia outra vez (workflow_dispatch) e sábado a seguir: nada.
    assert main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s2.json") is None
    assert main(raiz=tmp_path, hoje="2026-09-05", saida=tmp_path / "s3.json") is None
    # Segunda: véspera do dia 8 — esse sim.
    r = main(raiz=tmp_path, hoje="2026-09-07", saida=tmp_path / "s4.json")
    assert r["blocos"][0]["data_pagamento"] == "2026-09-08"


def test_main_retencao_limpa_datas_antigas(tmp_path):
    _repo(tmp_path, calendario=_CAL_SET, estado={
        "ultimo_calendario_publicado": "2026-09", "avisos_pagamento_entregues": ["2026-01-05"]})
    main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s.json")
    assert _estado(tmp_path)["avisos_pagamento_entregues"] == ["2026-09-07"]


def test_main_colisao_com_alteracao_legal_vai_na_mesma_issue_sem_adiar(tmp_path):
    _repo(tmp_path, calendario=_CAL_SET,
          pendente=[{"titulo": "Portaria X", "resumo": "Texto pronto."}])
    r = main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s.json")
    assert [b["gatilho"] for b in r["blocos"]] == ["alteracao_legal", "pagamento"]
    assert r["titulo"] == "Portaria X + Pagamentos de 7 de setembro"
    assert r["confirmado"] is True
    estado = _estado(tmp_path)
    assert estado["avisos_pagamento_entregues"] == ["2026-09-07"]
    assert json.loads((tmp_path / "data" / "canal_pendente.json").read_text())["entradas"] == []


def test_main_colisao_com_sentinela_por_confirmar_marca_issue_por_confirmar(tmp_path):
    _repo(tmp_path, calendario=_CAL_SET)
    log = tmp_path / "data" / "scraped" / "avisos.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("2026-09-04T09:00:00+00:00 AVISO slug=x motivo=dre_ias_portaria_detectada:- Portaria n.º 9/2026\n",
                   encoding="utf-8")
    r = main(raiz=tmp_path, hoje="2026-09-04", saida=tmp_path / "s.json")
    assert [b["confirmado"] for b in r["blocos"]] == [False, True]
    assert r["confirmado"] is False


def test_main_calendario_mensal_mantem_se_e_convive_com_o_aviso(tmp_path):
    # 2/9/2026 (quarta) é véspera do pagamento de 3/9; o mensal de
    # setembro ainda não foi entregue.
    cal = _calendario(2026, 9, [{"dia": 3, "prestacoes": ["doenca_profissional"]}])
    _repo(tmp_path, calendario=cal, estado={})
    r = main(raiz=tmp_path, hoje="2026-09-02", saida=tmp_path / "s.json")
    assert [b["gatilho"] for b in r["blocos"]] == ["calendario", "pagamento"]


def test_calendario_mensal_nunca_em_feriado():
    cal = _calendario(2026, 12, [{"dia": 8, "prestacoes": ["pensoes"]}])
    assert calendario_devido(D(2026, 12, 1), {}, cal) is None  # feriado
    assert calendario_devido(D(2026, 12, 2), {}, cal) is not None


# ── Step do workflow: assignee, menção, blocos ───────────────────────────


def _script_do_step():
    wf = yaml.safe_load((RAIZ / ".github" / "workflows" / "pipeline-diario.yml").read_text())
    passos = wf["jobs"]["pipeline"]["steps"]
    passo = next(p for p in passos if p.get("name", "").startswith("Criar Issue do rascunho do canal"))
    return passo["with"]["script"]


def _correr_step(tmp_path, rascunho):
    if shutil.which("node") is None:
        pytest.skip("node não disponível")
    ficheiro = tmp_path / "rascunho.json"
    ficheiro.write_text(json.dumps(rascunho, ensure_ascii=False), encoding="utf-8")
    script = _script_do_step()
    assert "'/tmp/canal_rascunho_hoje.json'" in script
    script = script.replace("'/tmp/canal_rascunho_hoje.json'", json.dumps(str(ficheiro)))
    harness = (
        "const criadas = [];\n"
        "const github = {rest: {issues: {\n"
        "  listForRepo: async () => ({data: []}),\n"
        "  create: async (a) => { criadas.push(a); },\n"
        "}}};\n"
        "const context = {repo: {owner: 'o', repo: 'r'}};\n"
        "(async () => {\n" + script + "\n})().then(() => {\n"
        "  process.stdout.write('\\n@@' + JSON.stringify(criadas));\n"
        "});\n"
    )
    res = subprocess.run(["node", "-e", harness], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.split("@@")[-1])


def _bloco(gatilho, titulo, texto, confirmado=True, **extra):
    return {"gatilho": gatilho, "titulo": titulo, "texto": texto, "confirmado": confirmado, **extra}


def test_issue_atribuida_ao_nuno_e_mencionado_na_primeira_linha(tmp_path):
    b = _bloco("calendario", "Calendário de pagamentos — outubro de 2026", "📅 texto")
    [issue] = _correr_step(tmp_path, {**b, "data": "2026-10-01", "blocos": [b]})
    assert issue["assignees"] == ["nunovinhas-creator"]
    assert issue["body"].splitlines()[0].startswith("@nunovinhas-creator")
    assert issue["labels"] == ["canal-rascunho"]


def test_issue_de_forma_antiga_sem_blocos_tambem_leva_assignee(tmp_path):
    b = _bloco("alteracao_legal", "Portaria X", "Texto pronto.")
    [issue] = _correr_step(tmp_path, {**b, "data": "2026-10-01"})
    assert issue["assignees"] == ["nunovinhas-creator"]
    assert "Texto pronto." in issue["body"]


def test_colisao_gera_uma_issue_com_os_dois_blocos_separados(tmp_path):
    legal = _bloco("alteracao_legal", "Portaria X", "TEXTO-LEGAL")
    pag = _bloco("pagamento", "Pagamentos de 7 de setembro", "TEXTO-PAGAMENTO",
                 data_pagamento="2026-09-07")
    criadas = _correr_step(tmp_path, {"data": "2026-09-04", "blocos": [legal, pag]})
    assert len(criadas) == 1
    corpo = criadas[0]["body"]
    assert criadas[0]["title"] == "📱 Canal — Portaria X + Pagamentos de 7 de setembro (2026-09-04)"
    assert "Rascunho 1 de 2 — Portaria X" in corpo and "Rascunho 2 de 2 — Pagamentos de 7 de setembro" in corpo
    assert corpo.index("TEXTO-LEGAL") < corpo.index("Rascunho 2 de 2") < corpo.index("TEXTO-PAGAMENTO")
    assert corpo.count("```") == 4


def test_bloco_por_confirmar_poe_aviso_antes_de_qualquer_texto(tmp_path):
    sent = _bloco("alteracao_legal", "Portaria do IAS", "TEXTO-BRUTO", confirmado=False,
                  sentinela="dre_ias_portaria_detectada")
    pag = _bloco("pagamento", "Pagamentos de 7 de setembro", "TEXTO-PAGAMENTO")
    [issue] = _correr_step(tmp_path, {"data": "2026-09-04", "blocos": [pag, sent]})
    corpo = issue["body"]
    assert issue["title"].startswith("⚠️ Canal (por confirmar)")
    assert issue["labels"] == ["canal-rascunho", "verificar"]
    assert corpo.index("NÃO PUBLICAR AINDA") < corpo.index("TEXTO-PAGAMENTO")
    assert corpo.index("NÃO PUBLICAR AINDA") < corpo.index("TEXTO-BRUTO")
