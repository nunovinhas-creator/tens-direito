"""Guardrail permanente contra o padrão que cegou dois sentinelas DRE
durante semanas sem ninguém reparar (Issues #147/#148, 2026-09-01).

Diagnóstico dessa sessão: `dre_habitacao_garantia` (criado 2026-07-20)
e `dre_psu_regulamentacao` (criado 2026-08-16) pesquisavam a CITAÇÃO de
um diploma por número — `'"Decreto-Lei n.º 44/2024"'` e
`'"Decreto-Lei n.º 166/2026"'` — e nunca devolveram um único resultado,
em 44 e 16 dias consecutivos respectivamente (confirmado por
`data/scraped/*_2026-*.json` reais, nunca por inferência). Os 4
sentinelas que sempre funcionaram (`dre_psu`, `dre_habitacao_paer`,
`dre_ias`, e agora `dre_psu_regulamentacao` depois da correcção)
pesquisam sempre uma frase TEMÁTICA — o nome ou o assunto da medida,
nunca a citação legal de outro diploma por número. Prova directa: no
mesmo dia (2026-09-01), com o mesmo motor, `dre_psu` (pesquisa
"prestação social única") encontrou a Portaria n.º 394/2026/1, que
`dre_psu_regulamentacao` (pesquisa "Decreto-Lei n.º 166/2026") nunca
encontrou em nenhum dos 16 dias anteriores — ver
tests/test_dre_psu_regulamentacao.py para o caso de teste completo com
dados reais.

Este ficheiro tranca esse padrão para nunca mais se repetir: qualquer
fonte DRE nova (ou existente) que use `pesquisa_interactiva` nunca pode
ter um termo com forma de citação de diploma ("n.º" + barra + ano) —
nem no `termo` pesquisado, nem na âncora de classificação
(`ancora_conteudo`, que tem sempre de ser igual ao termo).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import scraper_playwright as sp  # noqa: E402

# Forma de uma citação legal por número: "n.º"/"n.o"/"nº" seguido de um
# número de acto com barra e ano — ex.: "n.º 166/2026", "n.º 44/2024",
# "n.º 480-A/2025". Deliberadamente tolerante a variantes de escrita
# ("n.º"/"nº"/"n.o", maiúscula/minúscula, espaço opcional antes da
# barra) — o objectivo é apanhar QUALQUER forma de citação, nunca só a
# grafia exacta dos dois casos reais que já falharam.
_PADRAO_CITACAO_DIPLOMA = re.compile(r"n\.?[ºo]\s*\d+[\w-]*\s*/\s*\d{4}", re.IGNORECASE)


def _fontes_com_pesquisa_interactiva():
    return [f for f in sp.FONTES_PLAYWRIGHT if "pesquisa_interactiva" in f]


def test_ha_pelo_menos_uma_fonte_com_pesquisa_interactiva_para_testar():
    """Guarda contra o próprio guardrail ficar vazio e passar por
    omissão sem testar nada — se isto falhar, as fontes DRE mudaram de
    mecanismo e este ficheiro precisa de revisão, não só de correr."""
    assert len(_fontes_com_pesquisa_interactiva()) >= 4


def test_padrao_de_citacao_reconhece_os_dois_casos_reais_que_falharam():
    """Confirma que o regex teria apanhado os dois termos errados
    originais — sem isto, o guardrail podia estar a "passar" só por
    estar mal calibrado, nunca por o problema estar resolvido."""
    assert _PADRAO_CITACAO_DIPLOMA.search('"Decreto-Lei n.º 44/2024"')
    assert _PADRAO_CITACAO_DIPLOMA.search('"Decreto-Lei n.º 166/2026"')


def test_padrao_de_citacao_nunca_reconhece_as_frases_tematicas_reais():
    """Confirma que os termos genuinamente temáticos (os que já
    funcionaram contra o motor real) nunca disparam este guardrail por
    engano — nenhum tem "n.º"/"nº" seguido de número/ano."""
    for termo in (
        '"prestação social única"',
        '"apoio extraordinário à renda"',
        '"indexante dos apoios sociais"',
        '"Garantia Pública no crédito habitação"',
    ):
        assert not _PADRAO_CITACAO_DIPLOMA.search(termo), (
            f"falso positivo do guardrail em {termo!r} — regex demasiado permissivo"
        )


def test_nenhum_termo_de_pesquisa_interactiva_tem_forma_de_citacao_de_diploma():
    """O guardrail em si: nenhuma fonte DRE actual pode pesquisar uma
    citação de diploma por número. Se uma fonte nova precisar mesmo de
    vigiar um diploma específico, a pesquisa tem de ser pelo NOME/TEMA
    da medida (ver o comentário junto a cada entrada em
    _FONTE_CONFIGS para o padrão a seguir), nunca pela citação — que já
    provou, duas vezes, nunca devolver resultado nenhum no DRE."""
    for fonte in _fontes_com_pesquisa_interactiva():
        termo = fonte["pesquisa_interactiva"]["termo"]
        assert not _PADRAO_CITACAO_DIPLOMA.search(termo), (
            f"{fonte['slug']}: termo de pesquisa {termo!r} tem forma de citação de "
            f"diploma (\"n.º\" + barra + ano) — mesmo padrão que deixou "
            f"dre_habitacao_garantia (44 dias) e dre_psu_regulamentacao (16 dias) "
            f"cegos sem nunca devolver um resultado (Issues #147/#148); usar uma "
            f"frase temática comprovada contra o motor real, nunca a citação"
        )


def test_nenhuma_ancora_de_classificacao_tem_forma_de_citacao_de_diploma():
    """`ancora_conteudo` (usada para classificar a resposta como OK) tem
    sempre de ser igual ao termo pesquisado — o mesmo guardrail
    aplica-se aqui, com a mesma razão."""
    for fonte in _fontes_com_pesquisa_interactiva():
        config = sp._fonte_config(fonte["slug"])
        for ancora in config.ancora_conteudo:
            assert not _PADRAO_CITACAO_DIPLOMA.search(ancora), (
                f"{fonte['slug']}: ancora_conteudo {ancora!r} tem forma de citação "
                f"de diploma — mesmo guardrail de test_nenhum_termo_de_pesquisa_"
                f"interactiva_tem_forma_de_citacao_de_diploma"
            )


def test_ancora_de_classificacao_bate_sempre_com_o_termo_pesquisado():
    """Nunca uma divergência silenciosa entre o que é pesquisado e o que
    é usado para confirmar que a pesquisa correu — ambos têm de ser a
    mesma frase entre aspas, ou a classificação nunca fica OK."""
    for fonte in _fontes_com_pesquisa_interactiva():
        termo = fonte["pesquisa_interactiva"]["termo"]
        config = sp._fonte_config(fonte["slug"])
        assert config.ancora_conteudo == (termo,), (
            f"{fonte['slug']}: ancora_conteudo {config.ancora_conteudo!r} não bate "
            f"com o termo pesquisado {termo!r}"
        )
