"""
Rede de segurança para fontes.html: cada diploma legal citado numa
página pública (Decreto-Lei/Portaria/Lei/Despacho "n.º NNN/AAAA") devia
ter um cartão próprio em fontes.html — a lista de fontes oficiais do
site — mas nada garantia isso até agora. Nasceu do levantamento do
cluster PSU (2026-08-30): fontes.html não tinha entrada para o
Decreto-Lei n.º 166/2026 nem para nenhuma portaria/lei da PSU, apesar de
um cluster inteiro se apoiar neles — a mesma classe de lacuna já
encontrada esta semana noutros sítios do site: uma coisa que se assume
mantida à mão e que ninguém verifica.

Como se distingue uma citação genuína de uma menção de passagem: a
regex ancora no formato oficial de citação português ("Tipo n.º
NNN/AAAA[/N]") — por construção nunca apanha frases como "consulta a
lei aplicável" (sem número) nem um número dentro de um href/slug de URL
(a regex exige o "n.º" literal antes do número, que nunca aparece numa
URL). Dado que a regra "só fontes primárias, nunca de memória" já
disciplina este site a nunca citar um diploma levianamente (ver
CLAUDE.md, "REGRAS DE CONTEÚDO"), qualquer match desta regex em texto
VISÍVEL é tratado como citação genuína.

Âmbito deliberado — só texto visível: `<script>` e `<style>` são
removidos antes da extracção. Hoje o JSON-LD de cada página espelha
sempre texto já visível (a mesma citação aparece primeiro no corpo, o
FAQPage é só a versão estruturada da mesma resposta), por isso excluir
`<script>` nunca esconde uma citação real — mas isto é uma verificação
válida HOJE, não uma garantia estrutural; se algum dia uma citação
passar a existir SÓ dentro de JSON-LD, sem equivalente em texto visível,
este teste deixa de a apanhar. Registado aqui deliberadamente, para
qualquer sessão futura que mude esse padrão saber que precisa de
alargar `_extrair_diplomas_texto_visivel`.

Levantamento inicial (2026-08-30): 46 diplomas citados e ausentes de
fontes.html — 3 do cluster PSU, corrigidos no mesmo commit deste teste
(ver fontes.html), e 43 nos restantes clusters do site, registados em
EXCECOES_DIPLOMAS_FONTES com o motivo "por acrescentar" — a allow-list
nasce POVOADA, não vazia: um teste que nasce vermelho é um teste que
alguém acaba por desligar; assim nasce verde, e a lista de excepções
passa a ser a lista de trabalho visível (ver também ROADMAP.md), nunca
uma dívida invisível. Confirmar/acrescentar o permalink do DRE em
fontes.html (nunca inventar um) e remover a entrada correspondente
daqui é o critério de "resolvido" para cada uma.

Corre sobre as páginas REAIS do repositório (mesmo padrão de
test_breadcrumb_coerencia.py/test_higiene_indexacao.py), nunca fixtures.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

RAIZ = Path(__file__).parent.parent

PADRAO_DIPLOMA = re.compile(
    r"(Decreto-Lei|Portaria|Lei|Despacho)\s+n\.?[ºo]\s*([\w\-]+/\d{4}(?:/\d+)?)",
    re.IGNORECASE,
)

_TIPO_NORMALIZADO = {
    "decreto-lei": "Decreto-Lei",
    "portaria": "Portaria",
    "lei": "Lei",
    "despacho": "Despacho",
}


def _normalizar_tipo(tipo: str) -> str:
    return _TIPO_NORMALIZADO.get(tipo.strip().lower(), tipo.title())


def _extrair_diplomas_texto_visivel(html: str) -> set[str]:
    sem_script = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    sem_script_nem_style = re.sub(r"<style\b[^>]*>.*?</style>", "", sem_script, flags=re.DOTALL | re.IGNORECASE)
    return {
        f"{_normalizar_tipo(tipo)} n.º {numero}"
        for tipo, numero in PADRAO_DIPLOMA.findall(sem_script_nem_style)
    }


# Diplomas citados nalguma página pública e ainda sem cartão em
# fontes.html, à data do levantamento — motivo idêntico para os 43
# porque a causa é a mesma para todos: nunca foram acrescentados, só
# identificados. Resolver = confirmar o permalink real do DRE (ou usar
# a homepage genérica se não confirmável — nunca inventar um subpath),
# acrescentar o cartão em fontes.html seguindo o padrão dos cartões de
# diploma já existentes, e remover a entrada daqui.
_MOTIVO_LEVANTAMENTO = "por acrescentar — levantamento de 30/08/2026"

EXCECOES_DIPLOMAS_FONTES: dict[str, str] = {
    "Decreto-Lei n.º 109/2025": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 126-A/2017": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 128/2017": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 138/2025": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 139/2025": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 15/2024": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 2/2024": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 232/2005": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 28/2004": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 29/2001": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 307/2003": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 35/2024": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 352/2007": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 4/2015": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 48-D/2024": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 55/2009": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 74-A/2017": _MOTIVO_LEVANTAMENTO,
    "Decreto-Lei n.º 8/2024": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 3026/2024": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 4472-A/2026": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 7253/2024": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 7255/2018": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 7994/2026": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 8368/2024": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 8442-A/2012": _MOTIVO_LEVANTAMENTO,
    "Despacho n.º 9989/2025": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 100/2019": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 110/2009": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 146/2005": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 22-A/2007": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 26/2016": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 4/2007": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 4/2019": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 7/2007": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 73-A/2025": _MOTIVO_LEVANTAMENTO,
    "Lei n.º 98/2009": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 106/2025/1": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 11/2024": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 151/2024/1": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 171/2025/1": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 337/2004": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 480-D/2025/1": _MOTIVO_LEVANTAMENTO,
    "Portaria n.º 58-A/2026/1": _MOTIVO_LEVANTAMENTO,
}

_FONTES_HTML = RAIZ / "fontes.html"
_DIPLOMAS_EM_FONTES = _extrair_diplomas_texto_visivel(_FONTES_HTML.read_text(encoding="utf-8"))

PAGINAS = [p for p in encontrar_paginas() if p != _FONTES_HTML]
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_diploma_citado_esta_em_fontes_ou_na_excecao(caminho):
    diplomas = _extrair_diplomas_texto_visivel(caminho.read_text(encoding="utf-8"))
    em_falta = [
        d for d in diplomas
        if d not in _DIPLOMAS_EM_FONTES and d not in EXCECOES_DIPLOMAS_FONTES
    ]
    assert not em_falta, (
        f"{caminho.relative_to(RAIZ)} cita {em_falta}, ausente(s) de fontes.html "
        "— acrescentar um cartão em fontes.html (nunca inventar permalink; "
        "usar a homepage do DRE se não for confirmável) ou registar em "
        "EXCECOES_DIPLOMAS_FONTES com o motivo"
    )


def test_excecoes_ainda_sao_citadas_e_ainda_em_falta():
    todos_os_diplomas_citados: set[str] = set()
    for caminho in PAGINAS:
        todos_os_diplomas_citados |= _extrair_diplomas_texto_visivel(caminho.read_text(encoding="utf-8"))

    for diploma in EXCECOES_DIPLOMAS_FONTES:
        assert diploma in todos_os_diplomas_citados, (
            f"EXCECOES_DIPLOMAS_FONTES tem '{diploma}', mas já não é citado "
            "em nenhuma página — remover a excepção, é uma entrada órfã"
        )
        assert diploma not in _DIPLOMAS_EM_FONTES, (
            f"EXCECOES_DIPLOMAS_FONTES tem '{diploma}', mas já tem cartão em "
            "fontes.html — remover a excepção, já está resolvida"
        )
