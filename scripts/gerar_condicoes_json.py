#!/usr/bin/env python3
"""
Consolida dados/condicoes/perguntas.yaml + dados/condicoes/<apoio>.yaml num
único dados/condicoes.json, consumido em runtime pelo motor de avaliação
(assets/js/motor-condicoes.js, PR 3) — mesmo padrão de
scripts/gerar_parametros_json.py: regra separada do valor, script falha em
vez de publicar uma referência que não existe.

Cada condição de dados/condicoes/<apoio>.yaml tem exactamente UMA fonte de
valor:
  - `parametro: <prestacao>.<nome>` — resolvido contra dados/parametros.json
    já gerado (falha se a prestação/parâmetro não existir lá);
  - `valor_literal: ...` — só aceite em condições `tipo: limiar` se vier
    acompanhado de `fonte_pagina:` (nunca um número sem proveniência), ou em
    condições `tipo: categorica` se o valor for uma das `opcoes` do campo em
    perguntas.yaml.

    python scripts/gerar_condicoes_json.py            # escreve dados/condicoes.json
    python scripts/gerar_condicoes_json.py --check     # só valida (CI), nunca escreve
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CONDICOES_DIR = RAIZ / "dados" / "condicoes"
PERGUNTAS_PATH = CONDICOES_DIR / "perguntas.yaml"
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
SAIDA_JSON = RAIZ / "dados" / "condicoes.json"
RAIZ_SITE = RAIZ  # onde procurar a página de cada `simulador:` (patchável nos testes)

TIPOS_VALIDOS = {"categorica", "numero", "data"}
TIPOS_CONDICAO_VALIDOS = {"categorica", "limiar", "formula", "limiar_faixa_incerta"}
FORMULAS_VALIDAS = {"escala_equivalencia_rsi", "psu_valor_positivo"}
OPERADORES_APOIO_VALIDOS = {"all", "any"}
OPERADORES_COMPARACAO_VALIDOS = {"eq", "neq", "gte", "lte", "gt", "lt"}
UNIDADES_IDADE = {"anos", "meses_totais"}
# PR 12: para onde leva o link de cada resultado. A página escolhe o texto
# do link por aqui ("Abrir o simulador dedicado" só para simuladores).
TIPOS_LINK_VALIDOS = {"simulador", "guia"}
PREFIXO_PAGINA_SIMULADOR = "simulador-"


class CondicaoInvalida(Exception):
    pass


def _carregar_perguntas() -> dict:
    if not PERGUNTAS_PATH.exists():
        raise CondicaoInvalida(f"{PERGUNTAS_PATH} não existe — corre o PR 1 primeiro")
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        perguntas = yaml.safe_load(f) or {}
    for campo, dados in perguntas.items():
        if dados.get("tipo") not in TIPOS_VALIDOS:
            raise CondicaoInvalida(f"perguntas.yaml: '{campo}' com tipo inválido")
        _validar_campos_do_assistente(campo, dados, perguntas)
    return perguntas


def _validar_campos_do_assistente(campo: str, dados: dict, perguntas: dict) -> None:
    """PR 11: o que simulador-universal.html precisa para mostrar a pergunta
    sem convenção não escrita — texto, rótulos de cada opção e quando a
    pergunta faz sentido. Falha com mensagem clara em vez de deixar a
    página mostrar um nome de campo cru ou uma opção sem rótulo."""
    contexto = f"perguntas.yaml: '{campo}'"
    if campo == "data_nascimento":
        raise CondicaoInvalida(
            f"{contexto}: campo genérico proibido — usar data_nascimento_requerente ou data_nascimento_crianca"
        )

    pergunta = dados.get("pergunta")
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise CondicaoInvalida(f"{contexto}: falta 'pergunta' (texto mostrado ao utilizador)")
    if "ajuda" in dados and (not isinstance(dados["ajuda"], str) or not dados["ajuda"].strip()):
        raise CondicaoInvalida(f"{contexto}: 'ajuda' tem de ser texto não vazio")

    rotulos = dados.get("rotulos")
    if dados["tipo"] == "categorica":
        opcoes = dados.get("opcoes") or []
        if not isinstance(rotulos, dict):
            raise CondicaoInvalida(f"{contexto}: pergunta categórica sem 'rotulos' (um por opção)")
        em_falta = [o for o in opcoes if o not in rotulos]
        a_mais = [r for r in rotulos if r not in opcoes]
        if em_falta or a_mais:
            raise CondicaoInvalida(
                f"{contexto}: 'rotulos' não bate com 'opcoes' — em falta {em_falta}, a mais {a_mais}"
            )
        vazios = [r for r, texto in rotulos.items() if not isinstance(texto, str) or not texto.strip()]
        if vazios:
            raise CondicaoInvalida(f"{contexto}: rótulo(s) vazio(s) para {vazios}")
    elif rotulos is not None:
        raise CondicaoInvalida(f"{contexto}: 'rotulos' só faz sentido em perguntas categóricas")

    cond = dados.get("aplicavel_se")
    if cond is None:
        return
    if not isinstance(cond, dict) or set(cond) != {"campo", "valor"}:
        raise CondicaoInvalida(f"{contexto}: 'aplicavel_se' tem de ser exactamente {{campo, valor}}")
    alvo = cond["campo"]
    if alvo == campo:
        raise CondicaoInvalida(f"{contexto}: 'aplicavel_se' não pode referenciar o próprio campo")
    if alvo not in perguntas:
        raise CondicaoInvalida(f"{contexto}: 'aplicavel_se' referencia campo inexistente '{alvo}'")
    if perguntas[alvo].get("tipo") == "categorica" and cond["valor"] not in perguntas[alvo].get("opcoes", []):
        raise CondicaoInvalida(
            f"{contexto}: 'aplicavel_se.valor' {cond['valor']!r} não é opção de '{alvo}'"
        )


def _validar_titulo_e_simulador(bruto: dict, apoio: str) -> None:
    """PR 11: cada apoio diz como se chama na página e para onde leva o
    link "simulador dedicado" — nunca um nome de ficheiro cru nem um link
    partido na página de resultados."""
    titulo = bruto.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        raise CondicaoInvalida(f"{apoio}: falta 'titulo' (nome do apoio mostrado ao utilizador)")
    simulador = bruto.get("simulador")
    if not isinstance(simulador, str) or not simulador.startswith("/") or not simulador.endswith(".html"):
        raise CondicaoInvalida(f"{apoio}: 'simulador' tem de ser um caminho do site '/<pagina>.html' ({simulador!r})")
    if not (RAIZ_SITE / simulador.lstrip("/")).is_file():
        raise CondicaoInvalida(f"{apoio}: 'simulador' aponta para página inexistente ({simulador})")
    tipo_link = bruto.get("tipo_link")
    if tipo_link not in TIPOS_LINK_VALIDOS:
        raise CondicaoInvalida(f"{apoio}: 'tipo_link' tem de ser um de {sorted(TIPOS_LINK_VALIDOS)} ({tipo_link!r})")
    e_pagina_de_simulador = simulador.lstrip("/").startswith(PREFIXO_PAGINA_SIMULADOR)
    if (tipo_link == "simulador") != e_pagina_de_simulador:
        raise CondicaoInvalida(
            f"{apoio}: 'tipo_link: {tipo_link}' não bate com o link {simulador} "
            f"(as páginas de simulador chamam-se /{PREFIXO_PAGINA_SIMULADOR}*.html)"
        )


def _carregar_parametros() -> dict:
    if not PARAMETROS_JSON.exists():
        raise CondicaoInvalida(
            f"{PARAMETROS_JSON} não existe — corre scripts/gerar_parametros_json.py primeiro"
        )
    with open(PARAMETROS_JSON, encoding="utf-8") as f:
        return json.load(f)


def _resolver_parametro(referencia: str, parametros: dict, contexto: str) -> float:
    if "." not in referencia:
        raise CondicaoInvalida(f"{contexto}: 'parametro' tem de ser '<prestacao>.<nome>', veio '{referencia}'")
    prestacao, nome = referencia.split(".", 1)
    prestacoes = parametros.get("prestacoes", {})
    if prestacao not in prestacoes:
        raise CondicaoInvalida(f"{contexto}: prestação '{prestacao}' não existe em dados/parametros.json")
    if nome not in prestacoes[prestacao]:
        raise CondicaoInvalida(
            f"{contexto}: parâmetro '{nome}' não existe em dados/parametros.json → prestacoes.{prestacao}"
        )
    return prestacoes[prestacao][nome]["valor"]


def _validar_e_resolver_formula(condicao: dict, apoio: str, perguntas: dict, parametros: dict) -> dict:
    contexto = f"{apoio}.{condicao.get('id', '<sem id>')}"

    formula = condicao.get("formula")
    if formula not in FORMULAS_VALIDAS:
        raise CondicaoInvalida(f"{contexto}: 'formula' tem de ser uma de {sorted(FORMULAS_VALIDAS)}, veio {formula!r}")

    if formula == "escala_equivalencia_rsi":
        campos_obrigatorios = ["campo_rendimento", "campo_adultos_adicionais", "campo_menores"]
        parametros_obrigatorios = ["parametro_titular", "parametro_adulto_adicional", "parametro_menor"]

        for chave in campos_obrigatorios:
            if condicao.get(chave) not in perguntas:
                raise CondicaoInvalida(
                    f"{contexto}: '{chave}' aponta para campo inexistente em perguntas.yaml ({condicao.get(chave)!r})"
                )
        for chave in parametros_obrigatorios:
            if chave not in condicao:
                raise CondicaoInvalida(f"{contexto}: falta '{chave}' para a fórmula {formula}")

        return {
            "id": condicao["id"],
            "tipo": "formula",
            "formula": formula,
            "campo_rendimento": condicao["campo_rendimento"],
            "campo_adultos_adicionais": condicao["campo_adultos_adicionais"],
            "campo_menores": condicao["campo_menores"],
            "valor_titular": _resolver_parametro(condicao["parametro_titular"], parametros, contexto),
            "valor_adulto_adicional": _resolver_parametro(condicao["parametro_adulto_adicional"], parametros, contexto),
            "valor_menor": _resolver_parametro(condicao["parametro_menor"], parametros, contexto),
            "fonte": {
                "tipo": "parametro_multiplo",
                "referencias": [
                    condicao["parametro_titular"],
                    condicao["parametro_adulto_adicional"],
                    condicao["parametro_menor"],
                ],
            },
        }

    if formula == "psu_valor_positivo":
        campos_obrigatorios = [
            "campo_rendimento_trabalho",
            "campo_outros_rendimentos",
            "campo_adultos_adicionais",
            "campo_menores",
        ]
        parametros_obrigatorios = [
            "parametro_ias",
            "parametro_valor_referencia_multiplicador",
            "parametro_ponderacao_titular",
            "parametro_ponderacao_maior",
            "parametro_ponderacao_menor",
            "parametro_cit_limiar_multiplicador",
            "parametro_cit_taxa",
            "parametro_valor_minimo",
        ]
        for chave in campos_obrigatorios:
            if condicao.get(chave) not in perguntas:
                raise CondicaoInvalida(
                    f"{contexto}: '{chave}' aponta para campo inexistente em perguntas.yaml ({condicao.get(chave)!r})"
                )
        for chave in parametros_obrigatorios:
            if chave not in condicao:
                raise CondicaoInvalida(f"{contexto}: falta '{chave}' para a fórmula {formula}")

        def resolver(chave):
            return _resolver_parametro(condicao[chave], parametros, contexto)

        ias = resolver("parametro_ias")
        return {
            "id": condicao["id"],
            "tipo": "formula",
            "formula": formula,
            "campo_rendimento_trabalho": condicao["campo_rendimento_trabalho"],
            "campo_outros_rendimentos": condicao["campo_outros_rendimentos"],
            "campo_adultos_adicionais": condicao["campo_adultos_adicionais"],
            "campo_menores": condicao["campo_menores"],
            "valor_referencia": resolver("parametro_valor_referencia_multiplicador") * ias,
            "ponderacao_titular": resolver("parametro_ponderacao_titular"),
            "ponderacao_maior": resolver("parametro_ponderacao_maior"),
            "ponderacao_menor": resolver("parametro_ponderacao_menor"),
            "cit_limiar": resolver("parametro_cit_limiar_multiplicador") * ias,
            "cit_taxa": resolver("parametro_cit_taxa"),
            "valor_minimo": resolver("parametro_valor_minimo"),
            "fonte": {
                "tipo": "parametro_multiplo",
                "referencias": [condicao[k] for k in parametros_obrigatorios],
            },
        }

    raise CondicaoInvalida(f"{contexto}: fórmula {formula!r} reconhecida mas sem implementação")


def _validar_e_resolver_condicao(condicao: dict, apoio: str, perguntas: dict, parametros: dict) -> dict:
    """Resolve a condição e, se existir, o `motivo_inelegivel` (PR 12): o
    texto que a página mostra quando é esta folha que exclui, em vez da
    frase genérica "Não cumpres uma condição de acesso…". Só em folhas —
    num grupo não se saberia qual das sub-condições falhou."""
    resolvida = _resolver_condicao(condicao, apoio, perguntas, parametros)
    if "motivo_inelegivel" in condicao:
        contexto = f"{apoio}.{condicao.get('id', '<sem id>')}"
        if "condicoes" in condicao:
            raise CondicaoInvalida(f"{contexto}: 'motivo_inelegivel' só em condições simples, não em grupos")
        motivo = condicao["motivo_inelegivel"]
        if not isinstance(motivo, str) or not motivo.strip():
            raise CondicaoInvalida(f"{contexto}: 'motivo_inelegivel' tem de ser texto não vazio")
        resolvida["motivo_inelegivel"] = motivo.strip()
    return resolvida


def _resolver_condicao(condicao: dict, apoio: str, perguntas: dict, parametros: dict) -> dict:
    contexto = f"{apoio}.{condicao.get('id', '<sem id>')}"

    if "id" not in condicao:
        raise CondicaoInvalida(f"{apoio}: condição sem 'id'")

    # Grupo aninhado (ex.: idade normal OU excepção de invalidez) — nunca
    # tem 'tipo'/'campo' próprios, só reagrupa sub-condições com o seu
    # próprio operador. Recursivo: um grupo pode conter outro grupo.
    if "condicoes" in condicao:
        if condicao.get("operador") not in OPERADORES_APOIO_VALIDOS:
            raise CondicaoInvalida(f"{contexto}: grupo sem 'operador' válido ({sorted(OPERADORES_APOIO_VALIDOS)})")
        subcondicoes = [
            _validar_e_resolver_condicao(c, apoio, perguntas, parametros) for c in condicao["condicoes"]
        ]
        if not subcondicoes:
            raise CondicaoInvalida(f"{contexto}: grupo com 'condicoes' vazio")
        return {
            "id": condicao["id"],
            "operador": condicao["operador"],
            "condicoes": subcondicoes,
        }

    if condicao.get("tipo") not in TIPOS_CONDICAO_VALIDOS:
        raise CondicaoInvalida(f"{contexto}: 'tipo' tem de ser um de {sorted(TIPOS_CONDICAO_VALIDOS)}")

    # Fórmula — não tem um único campo/operador_comparacao/valor, tem a sua
    # própria validação e formato de saída.
    if condicao["tipo"] == "formula":
        return _validar_e_resolver_formula(condicao, apoio, perguntas, parametros)

    if condicao["tipo"] == "limiar_faixa_incerta":
        return _validar_e_resolver_faixa_incerta(condicao, apoio, perguntas, parametros)

    campo = condicao.get("campo")
    if campo not in perguntas:
        raise CondicaoInvalida(f"{contexto}: campo '{campo}' não existe em perguntas.yaml")

    op = condicao.get("operador_comparacao")
    if op not in OPERADORES_COMPARACAO_VALIDOS:
        raise CondicaoInvalida(f"{contexto}: 'operador_comparacao' inválido ({op!r})")

    tem_parametro = "parametro" in condicao
    tem_literal = "valor_literal" in condicao
    if tem_parametro == tem_literal:
        raise CondicaoInvalida(f"{contexto}: tem de ter exactamente um de 'parametro' ou 'valor_literal'")

    if tem_parametro:
        valor = _resolver_parametro(condicao["parametro"], parametros, contexto)
        fonte = {"tipo": "parametro", "referencia": condicao["parametro"]}
    else:
        valor = condicao["valor_literal"]
        if condicao["tipo"] == "limiar":
            if not condicao.get("fonte_pagina"):
                raise CondicaoInvalida(
                    f"{contexto}: 'valor_literal' numa condição 'limiar' exige 'fonte_pagina' "
                    "— nunca publicar um número sem proveniência"
                )
            fonte = {"tipo": "literal_pagina", "pagina": condicao["fonte_pagina"]}
        else:  # categorica
            opcoes_campo = perguntas[campo].get("opcoes", [])
            if valor not in opcoes_campo:
                raise CondicaoInvalida(
                    f"{contexto}: valor_literal {valor!r} não é uma opção válida de '{campo}' "
                    f"({opcoes_campo})"
                )
            fonte = {"tipo": "literal_enum"}

    if condicao["tipo"] == "limiar" and perguntas[campo].get("tipo") == "data":
        _validar_limiar_de_data(condicao, valor, contexto)

    return {
        "id": condicao["id"],
        "tipo": condicao["tipo"],
        "campo": campo,
        "operador_comparacao": op,
        "valor": valor,
        "unidade_comparacao": condicao.get("unidade_comparacao"),
        "fonte": fonte,
    }


def _validar_e_resolver_faixa_incerta(condicao: dict, apoio: str, perguntas: dict, parametros: dict) -> dict:
    """PR 12: limiar com uma zona onde a norma não decide (ex.: creche "até
    aos 3 anos", sem dizer se o corte é no aniversário ou no fim do ano
    letivo). Abaixo de `parametro` cumpre; a partir de `parametro_exclusao`
    não cumpre; entre os dois, o resultado é indeterminado com o
    `motivo_indeterminado` — nunca "cumpre" nem "não cumpre" por palpite."""
    contexto = f"{apoio}.{condicao['id']}"
    campo = condicao.get("campo")
    if campo not in perguntas:
        raise CondicaoInvalida(f"{contexto}: campo '{campo}' não existe em perguntas.yaml")
    for chave in ("parametro", "parametro_exclusao"):
        if chave not in condicao:
            raise CondicaoInvalida(f"{contexto}: falta '{chave}' (limiar_faixa_incerta só aceita parâmetros)")
    if "valor_literal" in condicao or "operador_comparacao" in condicao:
        raise CondicaoInvalida(
            f"{contexto}: limiar_faixa_incerta não usa 'valor_literal' nem 'operador_comparacao' "
            "(cumpre abaixo de 'parametro', não cumpre a partir de 'parametro_exclusao')"
        )
    motivo = condicao.get("motivo_indeterminado")
    if not isinstance(motivo, str) or not motivo.strip():
        raise CondicaoInvalida(f"{contexto}: falta 'motivo_indeterminado' (texto mostrado ao utilizador)")
    unidade = condicao.get("unidade_comparacao")
    if perguntas[campo].get("tipo") == "data" and unidade not in UNIDADES_IDADE:
        raise CondicaoInvalida(
            f"{contexto}: campo de data exige 'unidade_comparacao' em {sorted(UNIDADES_IDADE)} ({unidade!r})"
        )
    valor = _resolver_parametro(condicao["parametro"], parametros, contexto)
    valor_exclusao = _resolver_parametro(condicao["parametro_exclusao"], parametros, contexto)
    for v in (valor, valor_exclusao):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise CondicaoInvalida(f"{contexto}: limiares de limiar_faixa_incerta têm de ser números ({v!r})")
    if not valor < valor_exclusao:
        raise CondicaoInvalida(
            f"{contexto}: 'parametro' ({valor}) tem de ser menor do que 'parametro_exclusao' ({valor_exclusao})"
        )
    return {
        "id": condicao["id"],
        "tipo": "limiar_faixa_incerta",
        "campo": campo,
        "valor": valor,
        "valor_exclusao": valor_exclusao,
        "unidade_comparacao": unidade,
        "motivo_indeterminado": motivo.strip(),
        "fonte": {
            "tipo": "parametro_multiplo",
            "referencias": [condicao["parametro"], condicao["parametro_exclusao"]],
        },
    }


def _validar_limiar_de_data(condicao: dict, valor, contexto: str) -> None:
    """PR 12: um limiar sobre um campo de data compara ou uma idade (com
    unidade_comparacao anos/meses_totais, contra um número) ou a própria
    data (sem unidade, contra uma data ISO). O motor compara datas ISO como
    strings — correcto só se as duas forem AAAA-MM-DD; uma data noutro
    formato, ou um número sem unidade, daria um resultado errado em
    silêncio."""
    unidade = condicao.get("unidade_comparacao")
    if unidade in UNIDADES_IDADE:
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise CondicaoInvalida(f"{contexto}: comparação em '{unidade}' exige um valor numérico ({valor!r})")
        return
    if unidade is not None:
        raise CondicaoInvalida(
            f"{contexto}: 'unidade_comparacao' tem de ser uma de {sorted(UNIDADES_IDADE)} ou omitida ({unidade!r})"
        )
    try:
        valida = isinstance(valor, str) and date.fromisoformat(valor).isoformat() == valor
    except ValueError:
        valida = False
    if not valida:
        raise CondicaoInvalida(
            f"{contexto}: limiar de data sem 'unidade_comparacao' exige uma data ISO AAAA-MM-DD ({valor!r})"
        )


def _anotar_verificado_em(condicoes: list, parametros: dict) -> list[str]:
    """Anota cada condição resolvida com o `verificado_em` do(s) parâmetro(s)
    de onde vem o seu valor (o mais recente, se forem vários) e devolve as
    datas encontradas. As condições não guardam data própria — a data de
    verificação é sempre a do parâmetro em dados/parametros.json. Condições
    `literal_enum`/`literal_pagina` não têm parâmetro, logo não têm data
    (nunca se inventa uma); o carimbo da página citada em `fonte_pagina`
    não é lido daqui, para o JSON não depender do HTML."""
    datas: list[str] = []
    for cond in condicoes:
        if "condicoes" in cond:
            datas.extend(_anotar_verificado_em(cond["condicoes"], parametros))
            continue
        fonte = cond.get("fonte", {})
        if fonte.get("tipo") == "parametro":
            referencias = [fonte["referencia"]]
        elif fonte.get("tipo") == "parametro_multiplo":
            referencias = fonte["referencias"]
        else:
            continue
        proprias = []
        for ref in referencias:
            prestacao, nome = ref.split(".", 1)
            data = parametros["prestacoes"][prestacao][nome].get("verificado_em")
            if data:
                proprias.append(data)
        if proprias:
            cond["verificado_em"] = max(proprias)
            datas.append(cond["verificado_em"])
    return datas


def _coletar_ids(condicoes: list) -> list:
    """Achata ids de condições e grupos, recursivamente, para o teste de duplicados."""
    ids = []
    for c in condicoes:
        ids.append(c["id"])
        if "condicoes" in c:
            ids.extend(_coletar_ids(c["condicoes"]))
    return ids


def consolidar() -> dict:
    perguntas = _carregar_perguntas()
    parametros = _carregar_parametros()

    apoios: dict[str, dict] = {}
    for ficheiro in sorted(CONDICOES_DIR.glob("*.yaml")):
        if ficheiro == PERGUNTAS_PATH:
            continue
        with open(ficheiro, encoding="utf-8") as f:
            bruto = yaml.safe_load(f) or {}

        apoio = bruto.get("apoio")
        if not apoio:
            raise CondicaoInvalida(f"{ficheiro.name}: falta a chave 'apoio'")
        if bruto.get("operador") not in OPERADORES_APOIO_VALIDOS:
            raise CondicaoInvalida(f"{apoio}: 'operador' tem de ser um de {sorted(OPERADORES_APOIO_VALIDOS)}")
        _validar_titulo_e_simulador(bruto, apoio)

        condicoes_resolvidas = [
            _validar_e_resolver_condicao(c, apoio, perguntas, parametros) for c in bruto.get("condicoes", [])
        ]
        if not condicoes_resolvidas:
            raise CondicaoInvalida(f"{apoio}: 'condicoes' está vazio")

        ids = _coletar_ids(condicoes_resolvidas)
        if len(ids) != len(set(ids)):
            duplicados = sorted({i for i in ids if ids.count(i) > 1})
            raise CondicaoInvalida(f"{apoio}: ids de condição duplicados ({duplicados})")

        datas_apoio = _anotar_verificado_em(condicoes_resolvidas, parametros)

        entrada = {
            "pagina": bruto.get("pagina"),
            "titulo": bruto["titulo"],
            "simulador": bruto["simulador"],
            "tipo_link": bruto["tipo_link"],
            "operador": bruto["operador"],
            "condicoes": condicoes_resolvidas,
        }
        # Data de verificação mais recente entre as condições do apoio (via
        # parâmetros) — é daqui, e nunca da data do dia, que a página tira o
        # carimbo "Verificado a".
        if datas_apoio:
            entrada["verificado_em"] = max(datas_apoio)
        # Marca opcional: este apoio é substituído por outro (ex.: RSI → PSU).
        # Não altera a elegibilidade — só informa a página de que, a partir da
        # data indicada, o apoio de substituição é que passa a valer.
        if "substituido_por" in bruto:
            entrada["substituido_por"] = bruto["substituido_por"]
            parametro_data = bruto.get("substituido_a_partir_de_parametro")
            if not parametro_data:
                raise CondicaoInvalida(f"{apoio}: 'substituido_por' exige 'substituido_a_partir_de_parametro'")
            entrada["substituido_a_partir_de"] = _resolver_parametro(parametro_data, parametros, apoio)
        apoios[apoio] = entrada

    for apoio, dados in apoios.items():
        alvo = dados.get("substituido_por")
        if alvo is not None and alvo not in apoios:
            raise CondicaoInvalida(f"{apoio}: 'substituido_por' aponta para apoio inexistente ({alvo!r})")

    datas = [a["verificado_em"] for a in apoios.values() if a.get("verificado_em")]
    return {
        "gerado_em": date.today().isoformat(),
        "verificado_em": max(datas) if datas else None,
        "perguntas": perguntas,
        "apoios": apoios,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Só valida, nunca escreve dados/condicoes.json")
    args = parser.parse_args()

    try:
        consolidado = consolidar()
    except CondicaoInvalida as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    n_apoios = len(consolidado["apoios"])
    n_condicoes = sum(len(_coletar_ids(a["condicoes"])) for a in consolidado["apoios"].values())

    if args.check:
        atual_sem_data = json.dumps(
            {k: v for k, v in consolidado.items() if k != "gerado_em"}, sort_keys=True
        )
        if SAIDA_JSON.exists():
            disco = json.loads(SAIDA_JSON.read_text(encoding="utf-8"))
            disco_sem_data = json.dumps({k: v for k, v in disco.items() if k != "gerado_em"}, sort_keys=True)
        else:
            disco_sem_data = None
        if disco_sem_data == atual_sem_data:
            print(f"dados/condicoes.json sincronizado — {n_apoios} apoio(s), {n_condicoes} condição(ões).")
            return 0
        print(
            "ERRO: dados/condicoes.json diverge do que dados/condicoes/*.yaml geraria "
            "— correr sem --check para regenerar.",
            file=sys.stderr,
        )
        return 1

    SAIDA_JSON.write_text(json.dumps(consolidado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"dados/condicoes.json escrito: {n_apoios} apoio(s), {n_condicoes} condição(ões).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
