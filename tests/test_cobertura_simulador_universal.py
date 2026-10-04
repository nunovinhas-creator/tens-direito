"""
Cobertura do simulador universal (PR 13 da série "simulador universal").

Cada página `tipo: "artigo"` de `data/clusters.json` tem de estar numa de
duas situações: é a `pagina` de um apoio em `dados/condicoes.json`, ou
está em `FORA_DO_SIMULADOR_UNIVERSAL` com categoria e motivo. Falha nos
dois sentidos: página nova sem classificação, ou entrada órfã (página que
saiu de `clusters.json` ou que entretanto passou a estar coberta).

As páginas `por_implementar` são o trabalho pendente do simulador
universal (ver ROADMAP.md → "TRABALHO FUTURO REGISTADO").
"""
from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

CATEGORIAS = {
    # Subpágina de outro apoio; o 3.º campo é a página desse apoio.
    "complementar",
    # Como pedir, documentos, calendários: não é um apoio com condições.
    "processo",
    # Regras de reforma: têm simulador próprio (simulador-condicoes-reforma.html).
    "reforma",
    # Apoio fechado a novos pedidos.
    "encerrado",
    # Apoio real com condições de acesso, ainda sem entrada em dados/condicoes.
    "por_implementar",
}

_PSU = "prestacao-social-unica.html"
_SOBREVIVENCIA = "pensao-de-sobrevivencia.html"
_COMO_PEDIR = "guia de como pedir um documento ou serviço, não é um apoio"
_REFORMA = "regra de reforma — coberta pelo simulador de condições de acesso à reforma"
_POR_IMPLEMENTAR = "apoio com condições de acesso, ainda sem entrada em dados/condicoes"

# (categoria, motivo, página do apoio de que é complementar — só em "complementar")
FORA_DO_SIMULADOR_UNIVERSAL: dict[str, tuple[str, str, str | None]] = {
    # ── complementar ──
    "psu-quando-entra-em-vigor.html": ("complementar", "cronologia da PSU", _PSU),
    "psu-quem-tem-direito.html": ("complementar", "detalhe das condições da PSU", _PSU),
    "psu-vs-abono-familia.html": ("complementar", "comparação PSU/abono", _PSU),
    "psu-lista-13-apoios.html": ("complementar", "prestações substituídas pela PSU", _PSU),
    "psu-trabalho-social.html": ("complementar", "actividades de solidariedade da PSU", _PSU),
    "como-pedir-psu.html": ("complementar", "como pedir a PSU", _PSU),
    "calendario-pagamentos-psu.html": ("complementar", "duração e pagamento da PSU", _PSU),
    "majoracao-subsidio-desemprego.html": (
        "complementar", "majoração do subsídio de desemprego", "subsidio-desemprego.html"),
    "quem-tem-direito-por-parentesco.html": (
        "complementar", "beneficiários da pensão de sobrevivência", _SOBREVIVENCIA),
    "duracao-da-pensao-de-sobrevivencia.html": (
        "complementar", "duração da pensão de sobrevivência", _SOBREVIVENCIA),
    "pensao-sobrevivencia-conjuge.html": (
        "complementar", "pensão de sobrevivência do cônjuge", _SOBREVIVENCIA),
    "pensao-sobrevivencia-uniao-de-facto.html": (
        "complementar", "pensão de sobrevivência na união de facto", _SOBREVIVENCIA),
    # ── processo ──
    "senha-seguranca-social-direta.html": ("processo", _COMO_PEDIR, None),
    "iban-seguranca-social.html": ("processo", _COMO_PEDIR, None),
    "chave-movel-digital.html": ("processo", _COMO_PEDIR, None),
    "como-pedir-niss.html": ("processo", _COMO_PEDIR, None),
    "declaracao-situacao-contributiva.html": ("processo", _COMO_PEDIR, None),
    "alterar-morada.html": ("processo", _COMO_PEDIR, None),
    "renovar-cartao-cidadao.html": ("processo", _COMO_PEDIR, None),
    "numero-utente-sns.html": ("processo", _COMO_PEDIR, None),
    "registo-criminal-online.html": ("processo", _COMO_PEDIR, None),
    "certidao-situacao-tributaria.html": ("processo", _COMO_PEDIR, None),
    "marcar-atendimento-seguranca-social.html": ("processo", _COMO_PEDIR, None),
    "prova-escolar.html": ("processo", "prova anual para manter o abono, não é um apoio", None),
    "calendario-escolar-apoios.html": ("processo", "calendário de prazos de vários apoios", None),
    "amim.html": ("processo", "atestado que prova a incapacidade, não é um apoio", None),
    # ── reforma ──
    "idade-normal.html": ("reforma", _REFORMA, None),
    "idade-pessoal.html": ("reforma", _REFORMA, None),
    "carreiras-muito-longas.html": ("reforma", _REFORMA, None),
    "outras-antecipacoes.html": ("reforma", _REFORMA, None),
    "como-e-calculada.html": ("reforma", _REFORMA, None),
    "que-anos-contam.html": ("reforma", _REFORMA, None),
    "mais-cedo-ou-mais-tarde.html": ("reforma", _REFORMA, None),
    "invalidez-relativa-ou-absoluta.html": ("reforma", _REFORMA, None),
    "pensao-e-trabalho.html": ("reforma", _REFORMA, None),
    "quando-a-invalidez-vira-velhice.html": ("reforma", _REFORMA, None),
    "carreiras-contributivas-estrangeiro.html": ("reforma", _REFORMA, None),
    "reforma-reino-unido-brexit.html": ("reforma", _REFORMA, None),
    "pensao-unificada.html": ("reforma", _REFORMA, None),
    "caixa-geral-aposentacoes.html": ("reforma", _REFORMA, None),
    # ── encerrado ──
    "apoio-extraordinario-renda.html": (
        "encerrado", "PAER fechado a novos beneficiários (contratos até 15/03/2023)", None),
    # ── por_implementar ──
    "bolsa-de-merito.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "manuais-escolares-mega.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "passe-sub23.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "bolsa-de-estudo-ensino-superior.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "garantia-para-a-infancia.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "subsidio-parental.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "assistencia-familia-filhos.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "cuidador-informal.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "prestacao-social-para-a-inclusao.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "amim-beneficios-fiscais.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "porta-65.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "deducao-rendas-irs.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "garantia-publica-credito-habitacao.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    "primeiro-direito.html": ("por_implementar", _POR_IMPLEMENTAR, None),
    _SOBREVIVENCIA: ("por_implementar", _POR_IMPLEMENTAR, None),
    "subsidio-por-morte.html": ("por_implementar", _POR_IMPLEMENTAR, None),
}


def _artigos(clusters: dict) -> set[str]:
    return {
        p["slug"].lstrip("/")
        for c in clusters["clusters"]
        for p in c["paginas"]
        if p.get("tipo") == "artigo"
    }


def _cobertas(condicoes: dict) -> set[str]:
    return {a["pagina"] for a in condicoes["apoios"].values()}


def erros_de_cobertura(clusters: dict, condicoes: dict, fora: dict) -> list[str]:
    artigos, cobertas = _artigos(clusters), _cobertas(condicoes)
    erros = []
    for pagina in sorted(artigos - cobertas - set(fora)):
        erros.append(f"{pagina}: sem entrada em dados/condicoes nem em FORA_DO_SIMULADOR_UNIVERSAL")
    for pagina, (categoria, motivo, alvo) in sorted(fora.items()):
        if pagina not in artigos:
            erros.append(f"{pagina}: órfã — já não é artigo em data/clusters.json")
        if pagina in cobertas:
            erros.append(f"{pagina}: órfã — já está coberta por dados/condicoes")
        if categoria not in CATEGORIAS:
            erros.append(f"{pagina}: categoria desconhecida {categoria!r}")
        if not motivo:
            erros.append(f"{pagina}: sem motivo")
        if categoria == "complementar":
            alvo_valido = alvo in cobertas or fora.get(alvo, ("",))[0] == "por_implementar"
            if not alvo_valido:
                erros.append(f"{pagina}: complementar de {alvo!r}, que não é apoio coberto nem por implementar")
        elif alvo is not None:
            erros.append(f"{pagina}: só a categoria complementar indica o apoio de que depende")
    return erros


def _json(caminho: str) -> dict:
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


CLUSTERS = _json("data/clusters.json")
CONDICOES = _json("dados/condicoes.json")


def test_todas_as_paginas_de_apoio_estao_cobertas_ou_classificadas():
    assert erros_de_cobertura(CLUSTERS, CONDICOES, FORA_DO_SIMULADOR_UNIVERSAL) == []


def test_pagina_sem_classificacao_falha():
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL)
    del fora["porta-65.html"]
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        "porta-65.html: sem entrada em dados/condicoes nem em FORA_DO_SIMULADOR_UNIVERSAL"
    ]


def test_entrada_de_pagina_que_ja_nao_existe_falha():
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL, **{"pagina-apagada.html": ("processo", "x", None)})
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        "pagina-apagada.html: órfã — já não é artigo em data/clusters.json"
    ]


def test_entrada_de_pagina_ja_coberta_falha():
    coberta = CONDICOES["apoios"]["rsi"]["pagina"]
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL, **{coberta: ("por_implementar", "x", None)})
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        f"{coberta}: órfã — já está coberta por dados/condicoes"
    ]


def test_categoria_desconhecida_falha():
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL, **{"porta-65.html": ("adiado", "x", None)})
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        "porta-65.html: categoria desconhecida 'adiado'"
    ]


def test_complementar_de_pagina_que_nao_e_apoio_falha():
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL,
                **{"como-pedir-psu.html": ("complementar", "x", "como-pedir-niss.html")})
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        "como-pedir-psu.html: complementar de 'como-pedir-niss.html', "
        "que não é apoio coberto nem por implementar"
    ]


def test_alvo_fora_de_complementar_falha():
    fora = dict(FORA_DO_SIMULADOR_UNIVERSAL, **{"porta-65.html": ("por_implementar", "x", _PSU)})
    assert erros_de_cobertura(CLUSTERS, CONDICOES, fora) == [
        "porta-65.html: só a categoria complementar indica o apoio de que depende"
    ]

