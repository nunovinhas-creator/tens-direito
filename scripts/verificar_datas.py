#!/usr/bin/env python3
"""Verifica datas e valores potencialmente expirados em todos os HTML da raiz."""

import glob
import json
import os
import re
from datetime import datetime

HOJE = datetime.now()
ANO = HOJE.year
MES = HOJE.month

# Ficheiros que o pipeline gera — ignorar
AUTO_GERADOS = ["index.html", "noticias.html", "404.html"]

# Padrões que indicam data potencialmente expirada
PADROES = [
    {
        "regex": r"\b(janeiro|fevereiro|março|abril|maio|junho|"
                 r"julho|agosto|setembro|outubro|novembro|"
                 r"dezembro)\s+de\s+(\d{4})\b",
        "tipo": "data_mes_ano",
        "descricao": "Data com mês e ano",
    },
    {
        "regex": r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
        "tipo": "data_numerica",
        "descricao": "Data numérica",
    },
    {
        "regex": r"\b(IAS|indexante)\s+de\s+[\d,\.]+\s*[€e]",
        "tipo": "valor_ias",
        "descricao": "Valor do IAS",
    },
    {
        "regex": r"\b20\d{2}/20\d{2}\b",
        "tipo": "ano_letivo",
        "descricao": "Ano letivo",
    },
    {
        "regex": r"\b(\d{1,2})\s+de\s+(setembro|outubro|"
                 r"novembro|dezembro)\s+(de\s+)?20\d{2}\b",
        "tipo": "prazo_outono",
        "descricao": "Prazo de outono",
    },
]

# Meses em que cada tipo de data deve ser revisto
REVER_EM = {
    "data_mes_ano": [1, 7, 8, 9],
    "data_numerica": [1, 7, 8, 9],
    "valor_ias": [1, 2],
    "ano_letivo": [6, 7],
    "prazo_outono": [8, 9],
}

alertas = []

for html_path in glob.glob("*.html"):
    nome = os.path.basename(html_path)
    if nome in AUTO_GERADOS:
        continue

    try:
        with open(html_path, encoding="utf-8") as f:
            conteudo = f.read()

        for padrao in PADROES:
            if MES not in REVER_EM[padrao["tipo"]]:
                continue

            matches = re.findall(padrao["regex"], conteudo, re.IGNORECASE)
            if matches:
                tem_ano_antigo = str(ANO - 1) in conteudo
                tem_ano_letivo_antigo = (
                    f"{ANO - 1}/{ANO}" in conteudo
                    or f"{ANO}/{ANO + 1}" not in conteudo
                )

                if tem_ano_antigo or tem_ano_letivo_antigo:
                    alertas.append({
                        "pagina": nome,
                        "tipo": padrao["tipo"],
                        "titulo": f"📅 REVER: {nome} — {padrao['descricao']}",
                        "corpo": (
                            f"A página `{nome}` contém datas ou "
                            f"valores que podem estar desactualizados"
                            f" para {ANO}.\n\n"
                            f"**Tipo detectado:** {padrao['descricao']}\n"
                            f"**Mês actual:** {MES}/{ANO}\n\n"
                            f"**Acção:** abrir a página, verificar "
                            f"cada data/valor com a fonte oficial "
                            f"e actualizar se necessário.\n\n"
                            f"Esta Issue foi gerada automaticamente "
                            f"pelo pipeline diário."
                        ),
                    })
                    break  # Um alerta por página é suficiente

    except Exception as e:
        print(f"Erro ao ler {html_path}: {e}")

os.makedirs("data", exist_ok=True)
with open("data/alertas_datas.json", "w", encoding="utf-8") as f:
    json.dump(alertas, f, ensure_ascii=False, indent=2)

print(f"{len(alertas)} páginas com potencial desactualização detectadas")
for a in alertas:
    print(f"  - {a['pagina']}: {a['tipo']}")
