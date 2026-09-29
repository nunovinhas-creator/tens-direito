"""
cartao-europeu-estacionamento.html — condições do art. 4.º do Decreto-Lei n.º
307/2003, na redação do Decreto-Lei n.º 128/2017 (issue #263). A pergunta
frequente "Quem tem direito…" tem de dizer o mesmo no corpo e no JSON-LD
FAQPage, e nenhum sítio da página pode voltar a citar a doença oncológica
(não consta do art. 4.º; sem fonte primária no repositório).
"""
import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = (RAIZ / "cartao-europeu-estacionamento.html").read_text(encoding="utf-8")
PERGUNTA = "Quem tem direito ao cartão europeu de estacionamento?"


def _texto(fragmento: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragmento))).strip()


def _resposta_json_ld() -> str:
    for bloco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', PAGINA, re.S):
        dados = json.loads(bloco)
        if dados.get("@type") != "FAQPage":
            continue
        for q in dados["mainEntity"]:
            if q["name"] == PERGUNTA:
                return q["acceptedAnswer"]["text"]
    raise AssertionError("pergunta não encontrada no FAQPage")


def _resposta_visivel() -> str:
    i = PAGINA.index(PERGUNTA, PAGINA.index("</head>"))
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
