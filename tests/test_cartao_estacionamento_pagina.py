"""
cartao-europeu-estacionamento.html — condições do art. 4.º do Decreto-Lei n.º
307/2003, na redação do Decreto-Lei n.º 128/2017 (issue #263). A pergunta
frequente "Quem tem direito…" tem de dizer o mesmo no corpo e no JSON-LD
FAQPage, e nenhum sítio da página pode voltar a citar a doença oncológica
(não consta do art. 4.º; sem fonte primária no repositório).

Issue #269: nas Forças Armadas a prova da incapacidade não é o AMIM, é o
cartão de pessoa deficiente das Forças Armadas (art. 6.º, n.º 3). O passo 2
do HowTo e a pergunta "Como e onde peço o cartão?" têm de o dizer.
"""
import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = (RAIZ / "cartao-europeu-estacionamento.html").read_text(encoding="utf-8")
PERGUNTA = "Quem tem direito ao cartão europeu de estacionamento?"
PERGUNTA_PEDIDO = "Como e onde peço o cartão?"
EXCECAO_FA = ("cartão de pessoa deficiente das Forças Armadas", "Ministério da Defesa Nacional")


def _texto(fragmento: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragmento))).strip()


def _json_ld(tipo: str) -> dict:
    for bloco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', PAGINA, re.S):
        dados = json.loads(bloco)
        if dados.get("@type") == tipo:
            return dados
    raise AssertionError(f"{tipo} não encontrado")


def _resposta_json_ld(pergunta: str = PERGUNTA) -> str:
    for q in _json_ld("FAQPage")["mainEntity"]:
        if q["name"] == pergunta:
            return q["acceptedAnswer"]["text"]
    raise AssertionError("pergunta não encontrada no FAQPage")


def _resposta_visivel(pergunta: str = PERGUNTA) -> str:
    i = PAGINA.index(pergunta, PAGINA.index("</head>"))
    m = re.search(r'<div class="resposta">(.*?)</div>', PAGINA[i:], re.S)
    assert m, "resposta visível não encontrada"
    return _texto(m.group(1))


def test_quem_tem_direito_igual_no_corpo_e_no_json_ld():
    assert _resposta_visivel() == _resposta_json_ld()


def test_quem_tem_direito_segue_o_art_4():
    resposta = _resposta_json_ld()
    for trecho in ("usar os transportes públicos",          # al. a): locomoção OU transportes
                   "limitação permanente de 60% ou mais",   # al. a): "permanente" na limitação
                   "alteração permanente da visão de 95% ou mais",  # al. c)
                   "Forças Armadas, ou equiparado, com incapacidade motora de 60% ou mais"):  # n.º 2
        assert trecho in resposta, trecho


def test_doenca_oncologica_nao_aparece_em_lado_nenhum():
    assert "oncol" not in PAGINA.lower()


def test_como_peco_igual_no_corpo_e_no_json_ld():
    assert _resposta_visivel(PERGUNTA_PEDIDO) == _resposta_json_ld(PERGUNTA_PEDIDO)


def test_como_peco_tem_a_excecao_das_forcas_armadas():
    resposta = _resposta_json_ld(PERGUNTA_PEDIDO)
    for trecho in EXCECAO_FA:
        assert trecho in resposta, trecho


def test_howto_passo_2_tem_a_excecao_das_forcas_armadas():
    passo = next(p for p in _json_ld("HowTo")["step"] if p["position"] == 2)
    for trecho in EXCECAO_FA:
        assert trecho in passo["text"], trecho


def test_resumo_e_checklist_tem_a_excecao_das_forcas_armadas():
    corpo = PAGINA[PAGINA.index("</head>"):]
    resumo = re.search(r"<li>Documento essencial:(.*?)</li>", corpo, re.S)
    checklist = re.search(r'<section class="checklist-final".*?</section>', corpo, re.S)
    assert resumo and checklist
    item_amim = next(_texto(li) for li in re.findall(r"<li>(.*?)</li>", checklist.group(0), re.S)
                     if "AMIM" in li)
    for sitio in (_texto(resumo.group(1)), item_amim):
        assert "ou, nas Forças Armadas, o cartão de pessoa deficiente das Forças Armadas" in sitio, sitio
