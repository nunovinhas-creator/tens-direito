"""
Canário de anos em metadados — title/meta description (2026-07-06).

As queries reais do GSC mostram que os utilizadores pesquisam com o ano
("cuidador informal 2026", "rsi 2026", "prova escolar 2026"). Ter um ano
civil desactualizado num <title> ou <meta name="description"> é o mesmo
problema já resolvido para valores legais em tests/test_valores_ancora.py
— uma promessa visível no Google que fica errada em silêncio.

Este teste falha sempre que um <title>/description contenha um ano civil
inferior ao ano corrente (calculado via `datetime.now().year`, nunca uma
constante fixa — o ponto é o teste ficar vermelho sozinho em janeiro, sem
precisar de ninguém "lembrar" de o actualizar), excepto para referências
históricas legítimas — citações de diplomas legais (ex.: "DL 138/2025") ou
factos permanentes com data no passado (ex.: "fechado desde 2023") — que
vivem em EXCECOES_ANOS_HISTORICOS, cada uma com o motivo registado.

Corre sobre as páginas reais (mesmo padrão de test_higiene_indexacao.py/
test_acessibilidade.py), nunca uma cópia.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

ANO_ATUAL = datetime.now().year

PAGINAS = sorted(encontrar_paginas(RAIZ), key=lambda p: str(p))
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]

REGEX_ANO = re.compile(r"\b(19|20)\d{2}\b")

# (página, ano) → motivo. Só anos que são citação de diploma legal (número
# do DL/Portaria) ou facto histórico permanente — nunca "esquecimento de
# actualizar". Cada entrada tem de continuar a aparecer na página real
# (ver test_excecoes_continuam_a_existir_na_pagina) — uma excepção órfã
# (a página já não tem esse ano) é uma excepção a remover, não a manter.
EXCECOES_ANOS_HISTORICOS = {
    ("apoio-extraordinario-renda.html", 2023): "PAER fechado a novos candidatos desde 15/03/2023 — facto histórico permanente, o apoio não voltou a abrir",
    ("complemento-solidario-idosos.html", 2024): "Regra de rendimentos dos filhos deixou de contar desde 2024 — facto histórico permanente",
    ("cuidador-informal.html", 2025): "Decreto-Lei n.º 138/2025 — número do diploma, não uma data de vigência",
    ("documentos/pedido-acesso-documentos-administrativos.html", 2016): "Lei n.º 26/2016 (LADA) — número do diploma, não uma data de vigência",
}


def _title(html: str) -> str:
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1) if m else ""


def _meta_description(html: str) -> str:
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else ""


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_sem_ano_civil_desactualizado_em_title_ou_description(caminho):
    pagina = str(caminho.relative_to(RAIZ))
    html = caminho.read_text(encoding="utf-8")
    texto = _title(html) + " " + _meta_description(html)

    anos_antigos = sorted({int(m.group(0)) for m in REGEX_ANO.finditer(texto) if int(m.group(0)) < ANO_ATUAL})
    nao_excecionados = [a for a in anos_antigos if (pagina, a) not in EXCECOES_ANOS_HISTORICOS]

    assert not nao_excecionados, (
        f"{pagina}: <title>/description menciona ano(s) {nao_excecionados} "
        f"anterior(es) ao ano corrente ({ANO_ATUAL}), sem excepção registada em "
        f"EXCECOES_ANOS_HISTORICOS — reveja se é um esquecimento de actualização "
        f"ou uma citação legítima a acrescentar às excepções"
    )


def test_excecoes_continuam_a_existir_na_pagina():
    """Uma excepção cujo ano já não aparece na página é lixo a remover daqui
    — nunca um esquecimento inofensivo. Evita que a lista de excepções
    cresça sem controlo e deixe de reflectir a realidade do site."""
    for (pagina, ano), motivo in EXCECOES_ANOS_HISTORICOS.items():
        html = (RAIZ / pagina).read_text(encoding="utf-8")
        texto = _title(html) + " " + _meta_description(html)
        assert str(ano) in texto, (
            f"Excepção órfã: ({pagina}, {ano}) — {motivo!r} — mas {ano} já não "
            f"aparece no title/description de {pagina}. Remover a excepção."
        )
