#!/usr/bin/env python3
"""Verifica datas e valores potencialmente expirados em todos os HTML da raiz.

Cada correspondência de data é avaliada com o ano que ela própria capta —
não com uma verificação solta de "o ano antigo aparece algures nesta
página". Só é tratada como expirada se esse ano for anterior ao ano actual
E não estiver explicado por um contexto legítimo: referência legal/
histórica (portaria, decreto-lei, despacho, "em vigor desde"), ano de
rendimentos (sempre o ano civil anterior, por definição), comparação
"Em <ano>, ..." com o valor actual, exemplo ilustrativo de cálculo, ou
aviso explícito de conteúdo pendente ("aguarda", "previsto", "a
confirmar") cujo prazo anunciado ainda não passou.
"""

import glob
import json
import os
import re
from datetime import datetime

# Ficheiros que o pipeline gera — ignorar
AUTO_GERADOS = ["index.html", "noticias.html", "404.html"]

JANELA = 220  # caracteres de contexto para cada lado da correspondência

MESES = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

# Referência legal/histórica permanente — nunca "expira".
MARCADORES_HISTORICOS = [
    r"portaria", r"decreto-lei", r"decreto\s+lei", r"despacho", r"\bdl\s*n",
    r"lei\s+n\.?º", r"diário da república", r"dre\.pt", r"em vigor desde",
    r"já\s+benefici", r"\bdesde\b",
]

# Ano de rendimentos — é sempre o ano civil anterior ao da prestação, por definição.
MARCADORES_RENDIMENTO = [r"rendiment"]

# "Em 2025, ..." — introduz uma comparação histórica explícita com o valor actual.
MARCADORES_COMPARACAO = [r"\bem\s+20\d{2}\s*,"]

# Exemplo ilustrativo de cálculo — datas fixas usadas só para exemplificar o método.
MARCADORES_EXEMPLO = [r"exemplo", r"ilustrat", r"\bex\.\s*:"]

MARCADORES_SUPRESSAO_DIRETA = (
    MARCADORES_HISTORICOS + MARCADORES_RENDIMENTO + MARCADORES_COMPARACAO + MARCADORES_EXEMPLO
)

# Conteúdo que já assume, de forma explícita, que está pendente de confirmação.
# "confirmar" no infinitivo (pendente) — não "confirmado" (já feito).
MARCADORES_PENDENTE = [
    r"aguarda", r"previst", r"provis[oó]ri", r"\bconfirmar\b", r"estimad",
    r"deverá ser", r"após publicação",
]

PADROES = [
    {
        "regex": r"\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|"
                 r"setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})\b",
        "tipo": "data_mes_ano",
        "descricao": "Data com mês e ano",
        "ano_grupo": 2,
    },
    {
        "regex": r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        "tipo": "data_numerica",
        "descricao": "Data numérica",
        "ano_grupo": 3,
    },
    {
        "regex": r"\b(IAS|indexante)\s+de\s+[\d,\.]+\s*[€e]",
        "tipo": "valor_ias",
        "descricao": "Valor do IAS",
        "ano_grupo": None,
    },
    {
        "regex": r"\b(20\d{2})/(20\d{2})\b",
        "tipo": "ano_letivo",
        "descricao": "Ano letivo",
        "ano_grupo": None,
    },
    {
        "regex": r"\b(\d{1,2})\s+de\s+(setembro|outubro|novembro|dezembro)\s+(?:de\s+)?(\d{4})\b",
        "tipo": "prazo_outono",
        "descricao": "Prazo de outono",
        "ano_grupo": 3,
    },
]

# Meses em que cada tipo de padrão deve ser revisto
REVER_EM = {
    "data_mes_ano": [1, 7, 8, 9],
    "data_numerica": [1, 7, 8, 9],
    "valor_ias": [1, 2],
    "ano_letivo": [6, 7],
    "prazo_outono": [8, 9],
}


def _janela_contexto(conteudo, inicio, fim):
    return conteudo[max(0, inicio - JANELA):fim + JANELA]


def _tem_algum(padroes, texto):
    return any(re.search(p, texto, re.IGNORECASE) for p in padroes)


def _proxima_data_esperada(texto):
    """Devolve a data mais distante referida no texto (ex.: 'setembro de 2026')."""
    melhor = None
    for m in re.finditer(
        r"\b(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|"
        r"outubro|novembro|dezembro)\s+de\s+(\d{4})\b",
        texto, re.IGNORECASE,
    ):
        candidato = datetime(int(m.group(2)), MESES[m.group(1).lower()], 1)
        if melhor is None or candidato > melhor:
            melhor = candidato
    return melhor


def _dentro_de_link(conteudo, inicio):
    """Um token de data dentro do texto visível de um <a> é uma citação a outra
    página/recurso (ex.: link para outro artigo pelo seu próprio nome), não uma
    afirmação desta página sobre o seu próprio conteúdo."""
    antes = conteudo[max(0, inicio - 300):inicio]
    ultima_abertura = antes.rfind("<a ")
    ultimo_fecho = antes.rfind("</a>")
    return ultima_abertura != -1 and ultima_abertura > ultimo_fecho


def _esta_suprimido(conteudo, inicio, fim, ano, mes):
    if _dentro_de_link(conteudo, inicio):
        return True

    janela = _janela_contexto(conteudo, inicio, fim)

    if _tem_algum(MARCADORES_SUPRESSAO_DIRETA, janela):
        return True

    if _tem_algum(MARCADORES_PENDENTE, janela):
        data_esperada = _proxima_data_esperada(janela)
        # Sem data explícita, ou prazo anunciado ainda não decorrido: continua pendente.
        if data_esperada is None or data_esperada >= datetime(ano, mes, 1):
            return True
        return False  # o prazo anunciado já passou — deixa de estar coberto pelo aviso

    return False


def _pagina_tem_alerta(conteudo, padrao, ano, mes):
    tipo = padrao["tipo"]

    if tipo == "ano_letivo":
        # Duas passagens: primeiro identifica que pares "antigos" já têm, em
        # ALGUM ponto da página, uma explicação válida (referência legal,
        # comparação histórica ou aviso de pendência ainda dentro do prazo).
        # Uma vez explicado, o mesmo par repetido noutros pontos da página
        # (ex.: um cabeçalho FAQ e a respectiva resposta) não é sinalizado
        # em duplicado.
        ocorrencias = list(re.finditer(padrao["regex"], conteudo))
        pares_explicados = {
            m.group(0) for m in ocorrencias
            if int(m.group(1)) < ano and _esta_suprimido(conteudo, m.start(), m.end(), ano, mes)
        }
        for m in ocorrencias:
            if int(m.group(1)) >= ano:
                continue  # par actual ou futuro
            if m.group(0) in pares_explicados:
                continue
            return True
        return False

    if tipo == "valor_ias":
        for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
            janela = _janela_contexto(conteudo, m.start(), m.end())
            anos_proximos = [int(a) for a in re.findall(r"\b(20\d{2})\b", janela)]
            if not any(a < ano for a in anos_proximos):
                continue  # nenhum ano antigo anotado junto ao valor
            if _esta_suprimido(conteudo, m.start(), m.end(), ano, mes):
                continue
            return True
        return False

    for m in re.finditer(padrao["regex"], conteudo, re.IGNORECASE):
        ano_match = int(m.group(padrao["ano_grupo"]))
        if ano_match >= ano:
            continue  # data actual ou futura
        if _esta_suprimido(conteudo, m.start(), m.end(), ano, mes):
            continue
        return True
    return False


def detectar_alertas(conteudo, nome_pagina, ano, mes):
    """Devolve o alerta (dict) para `nome_pagina`, ou None se nada de expirado for encontrado."""
    for padrao in PADROES:
        if mes not in REVER_EM[padrao["tipo"]]:
            continue
        if _pagina_tem_alerta(conteudo, padrao, ano, mes):
            return {
                "pagina": nome_pagina,
                "tipo": padrao["tipo"],
                "titulo": f"📅 REVER: {nome_pagina} — {padrao['descricao']}",
                "corpo": (
                    f"A página `{nome_pagina}` contém datas ou valores que podem "
                    f"estar desactualizados para {ano}.\n\n"
                    f"**Tipo detectado:** {padrao['descricao']}\n"
                    f"**Mês actual:** {mes}/{ano}\n\n"
                    f"**Acção:** abrir a página, verificar cada data/valor com a "
                    f"fonte oficial e actualizar se necessário.\n\n"
                    f"Esta Issue foi gerada automaticamente pelo pipeline diário."
                ),
            }
    return None


def main():
    hoje = datetime.now()
    ano, mes = hoje.year, hoje.month

    alertas = []
    for html_path in sorted(glob.glob("*.html")):
        nome = os.path.basename(html_path)
        if nome in AUTO_GERADOS:
            continue
        try:
            with open(html_path, encoding="utf-8") as f:
                conteudo = f.read()
        except Exception as e:
            print(f"Erro ao ler {html_path}: {e}")
            continue

        alerta = detectar_alertas(conteudo, nome, ano, mes)
        if alerta:
            alertas.append(alerta)

    os.makedirs("data", exist_ok=True)
    with open("data/alertas_datas.json", "w", encoding="utf-8") as f:
        json.dump(alertas, f, ensure_ascii=False, indent=2)

    print(f"{len(alertas)} páginas com potencial desactualização detectadas")
    for a in alertas:
        print(f"  - {a['pagina']}: {a['tipo']}")


if __name__ == "__main__":
    main()
