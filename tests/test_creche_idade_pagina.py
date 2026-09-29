"""
creche-gratuita.html — regra da idade (PR 12): a página explica que a creche
e a gratuitidade vão até aos 3 anos (Portaria n.º 262/2011, art. 3.º;
Portaria n.º 198/2022, art. 9.º, n.º 4) e que nenhum diploma fixa se o corte
é no aniversário ou no fim do ano letivo. A pergunta frequente tem de dizer o
mesmo no texto visível e no JSON-LD FAQPage — mudar só um deixava o outro a
prometer ao Google o texto antigo.
"""
import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINA = (RAIZ / "creche-gratuita.html").read_text(encoding="utf-8")
PERGUNTA = "A minha filha ou filho tem direito à creche gratuita?"
FRASE_IDADE = ("A creche e a gratuitidade vão até aos 3 anos de idade, mas nenhum diploma fixa se o corte é "
               "no aniversário ou no fim do ano letivo.")


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
    m = re.search(r"<summary><h3>" + re.escape(PERGUNTA) + r"</h3></summary>\s*<div class=\"resposta\">\s*<p>(.*?)</p>",
                  PAGINA, re.S)
    assert m, "pergunta não encontrada no corpo"
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def test_faq_da_idade_igual_no_corpo_e_no_json_ld():
    visivel, json_ld = _resposta_visivel(), _resposta_json_ld()
    assert visivel.endswith(FRASE_IDADE), visivel
    assert json_ld.endswith(FRASE_IDADE), json_ld


def test_paragrafo_da_idade_cita_os_dois_diplomas_e_a_ambiguidade():
    card = PAGINA[PAGINA.index("<h2>A criança tem direito?</h2>"):]
    card = card[:card.index("</div>")]
    texto = html.unescape(re.sub(r"<[^>]+>", "", card))
    for trecho in ("A creche acolhe crianças até aos 3 anos de idade (Portaria n.º 262/2011, artigo 3.º)",
                   "até aos 3 anos (Portaria n.º 198/2022, artigo 9.º, n.º 4)",
                   "Nenhum diploma diz se a criança deixa de estar abrangida no dia em que faz 3 anos ou só no "
                   "fim desse ano letivo"):
        assert trecho in texto, trecho
