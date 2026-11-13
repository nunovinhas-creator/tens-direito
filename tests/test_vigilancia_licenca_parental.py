"""Licença parental — estado legislativo e vigilância (issues #330/#331).

O alargamento (Projeto de Lei n.º 176/XVII/1.ª) foi aprovado em votação final
global a 16/10/2026 e, à data da verificação, não estava promulgado nem
publicado. Estes testes trancam o que a página pode e não pode dizer até a lei
ser publicada, e provam que a revisão marcada (`data-rever-ate`) dá alerta
quando o prazo passa — o mecanismo antigo (frase "voltamos a confirmar até
15 de novembro de 2026") não dava alerta nenhum em 2026.

Estado legislativo declarado no `.aviso-lei` (`data-estado-legislativo`):
- `aprovado-por-publicar` — a página tem de dizer que a lei ainda não está em
  vigor e nunca a pode apresentar como em vigor;
- `publicado` — passagem legítima a regras em vigor: exige o diploma citado
  por número (Lei n.º N/AAAA), a entrada em vigor e as condições de
  aplicação, e deixa de exigir «ainda não está em vigor».
Qualquer outro valor (ou nenhum) falha — a página tem de declarar o estado.
Factos das tabelas: projeto de decreto da AR (arts. 40.º e 43.º do Código do
Trabalho e art. 30.º do DL 91/2009, na redação aprovada), entregues pelo Nuno
a 11/11/2026 com o artigo citado.
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ_REPO = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ_REPO / "scripts"))

import verificar_datas as v  # noqa: E402
from sincronizar_clusters import verificado_em_do_texto  # noqa: E402

PAGINA = RAIZ_REPO / "subsidio-parental.html"


def _html():
    return PAGINA.read_text(encoding="utf-8")


def _texto():
    """Texto visível aproximado: sem tags, espaços normalizados."""
    t = re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", _html(), flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


def _celulas():
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
            for c in re.findall(r"<tr>(.*?)</tr>", _html(), flags=re.S)]


ESTADOS = {"aprovado-por-publicar", "publicado"}


def _estado():
    m = re.search(r'class="aviso-lei"[^>]*data-estado-legislativo="([^"]*)"', _html())
    return m.group(1) if m else None


def _pendente():
    return _estado() == "aprovado-por-publicar"


# --- estado legislativo -----------------------------------------------------

def test_estado_legislativo_declarado():
    assert _estado() in ESTADOS, f"data-estado-legislativo inválido ou em falta: {_estado()!r}"


def test_estado_publicado_exige_diploma_vigencia_e_condicoes():
    if _estado() != "publicado":
        return
    t = _texto()
    assert re.search(r"Lei n\.º \d+/20\d\d", t), "falta o número do diploma publicado"
    assert re.search(r"entra(m)? em vigor|em vigor desde|produz efeitos", t, re.IGNORECASE)
    assert re.search(r"licenças? (que comecem|iniciadas)", t, re.IGNORECASE), "faltam as condições de aplicação"

def test_regista_a_votacao_final_global_de_16_de_outubro():
    t = _texto()
    assert "16 de outubro de 2026" in t
    assert "votação final global" in t
    assert "176/XVII" in t


def test_nunca_volta_a_dizer_que_falta_a_votacao_final_global():
    t = _texto()
    proibido = re.compile(
        r"(ainda tem de ser|falta|aguarda|antes d[ao]|até à)[^.]{0,120}votação final global",
        re.IGNORECASE,
    )
    assert not proibido.search(t), proibido.search(t).group(0)


def test_nunca_apresenta_a_lei_aprovada_como_em_vigor():
    if not _pendente():
        return
    t = _texto()
    proibidos = [
        r"(já|agora) (está|estão) em vigor(?!\?)",
        r"entra(m)? (automaticamente )?em vigor (a|em) 1 de janeiro de 2027",
        r"em vigor desde 1 de janeiro de 2027",
        r"publicad[ao] em Diário da República (a|em) \d",
    ]
    for p in proibidos:
        m = re.search(p, t, re.IGNORECASE)
        assert not m, f"afirmação de vigência sem publicação confirmada: {m.group(0)!r}"
    assert re.search(r"ainda não está em vigor", t, re.IGNORECASE)
    assert re.search(r"Orçamento do Estado seguinte à publicação", t)


def test_data_de_2027_nunca_aparece_como_certa():
    if not _pendente():
        return
    t = _texto()
    for m in re.finditer(r"1 de janeiro de 2027", t):
        janela = t[max(0, m.start() - 250):m.end() + 250]
        assert re.search(r"só se|ainda não é certo|depende|ligada ao Orçamento", janela), (
            f"1/1/2027 sem a condição da entrada em vigor: …{janela}…"
        )


# --- regras em vigor vs. texto aprovado ------------------------------------

def test_tabela_das_regras_em_vigor_preservada():
    linhas = _celulas()
    esperadas = [
        ("120 dias", "100%"), ("150 dias", "80%"), ("150 dias", "100%"),
        ("180 dias", "83%"), ("180 dias", "90%"),
    ]
    tabela_vigor = [linha for linha in linhas if linha.startswith(("Gozo exclusivo", "Partilhada"))]
    for dias, pct in esperadas:
        assert any(dias in linha and linha.endswith(pct) for linha in tabela_vigor), (dias, pct)


def test_tabela_do_texto_aprovado():
    linhas = _celulas()

    def linha(prefixo):
        achadas = [x for x in linhas if x.startswith(prefixo)]
        assert len(achadas) == 1, (prefixo, achadas)
        return achadas[0]

    assert linha("150 dias sem partilha").endswith("100%")
    assert linha("180 dias sem partilha").endswith("83%")
    l180 = linha("180 dias com partilha")
    assert l180.endswith("100%") and "2×15" in l180
    l86 = linha("210 dias com partilha")
    assert l86.endswith("86%") and "30 dias seguidos" in l86 and "2×15 dias seguidos" in l86
    l90 = linha("210 dias com o pai")
    assert l90.endswith("90%") and "60 dias seguidos" in l90 and "2×30 dias seguidos" in l90
    assert linha("120 dias a 100%").endswith("Deixa de existir")
    pai_obr = linha("Pai — dias obrigatórios")
    assert "7 seguidos" in pai_obr and "14 seguidos" in pai_obr
    pai_fac = linha("Pai — dias facultativos")
    assert pai_fac.startswith("Pai — dias facultativos 7 dias") and "14 dias" in pai_fac
    assert "42 dias após o parto" in linha("Mãe — dias obrigatórios")


def test_jornada_continua_nao_e_apresentada_como_automatica():
    t = _texto()
    assert "56.º-A" in t
    assert re.search(r"Não é automática", t)
    assert re.search(r"convenção coletiva", t) and re.search(r"acordo com o empregador", t)


def test_situacoes_especiais_com_condicoes_e_nunca_automaticas():
    t = _texto()
    assert "n.os 17 a 21" in t
    assert re.search(r"Famílias monoparentais:", t)
    assert re.search(r"Outros familiares:.{0,200}não é uma possibilidade aberta a todas", t)
    vd = re.search(r"Vítimas de violência doméstica:(.{0,500})", t).group(1)
    for condicao in ("todas", "queixa-crime", "medida de coação", "proibição de contacto",
                     "casa de morada de família", "Não é automático"):
        assert condicao in vd, condicao


def test_percentagens_nao_sao_aplicadas_a_psu():
    t = _texto()
    assert re.search(r"não se aplicam automaticamente à PSU", t)


# --- vigilância -------------------------------------------------------------

def test_pagina_tem_revisao_marcada_coerente_com_o_carimbo():
    html = _html()
    revs = v.revisoes_marcadas(html)
    assert len(revs) == 1, revs
    _, d = revs[0]
    verificado = verificado_em_do_texto(html)
    assert d is not None and verificado is not None
    assert verificado <= d <= verificado + timedelta(days=60)


def test_sem_alerta_no_dia_da_verificacao():
    html = _html()
    verificado = verificado_em_do_texto(html)
    assert v.detectar_alertas(html, PAGINA.name, verificado.year, verificado.month,
                              dia=verificado.day) is None


def test_alerta_no_dia_seguinte_ao_prazo_da_revisao():
    html = _html()
    _, d = v.revisoes_marcadas(html)[0]
    no_prazo = v.detectar_alertas(html, PAGINA.name, d.year, d.month, dia=d.day)
    assert no_prazo is None
    dia_seguinte = d + timedelta(days=1)
    alerta = v.detectar_alertas(html, PAGINA.name, dia_seguinte.year, dia_seguinte.month,
                                dia=dia_seguinte.day)
    assert alerta is not None and alerta["tipo"] == "revisao_marcada"
    assert d.isoformat() in alerta["corpo"]


def test_alerta_continua_nos_meses_fora_de_rever_em():
    """Ao contrário dos PADROES, a revisão marcada não espera por jan/jul/ago/set."""
    html = _html()
    _, d = v.revisoes_marcadas(html)[0]
    seguinte = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    alerta = v.detectar_alertas(html, PAGINA.name, seguinte.year, seguinte.month)
    assert alerta is not None and alerta["tipo"] == "revisao_marcada"
