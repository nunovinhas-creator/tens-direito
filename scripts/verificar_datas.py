#!/usr/bin/env python3
"""Verifica datas sazonais nas páginas e gera alertas para Issues automáticas."""

from datetime import datetime
import json
import os

HOJE = datetime.now()
ANO = HOJE.year

ALERTAS = [
    {
        "pagina": "acao-social-escolar.html",
        "alerta": "Prazo ASE 30 setembro",
        "mes_rever": 8,
        "padrao": "30 de setembro",
    },
    {
        "pagina": "bolsa-de-merito.html",
        "alerta": "Prazo bolsa mérito 30 setembro",
        "mes_rever": 8,
        "padrao": "30 de setembro",
    },
    {
        "pagina": "abono-de-familia.html",
        "alerta": "Valores IAS — verificar novo IAS janeiro",
        "mes_rever": 1,
        "padrao": str(ANO - 1),
    },
    {
        "pagina": "rsi.html",
        "alerta": "Valor RSI — verificar portaria janeiro",
        "mes_rever": 1,
        "padrao": str(ANO - 1),
    },
    {
        "pagina": "subsidio-desemprego.html",
        "alerta": "Limites subsídio — verificar novo IAS",
        "mes_rever": 1,
        "padrao": str(ANO - 1),
    },
    {
        "pagina": "subsidio-parental.html",
        "alerta": "Valores parental — verificar novo IAS",
        "mes_rever": 1,
        "padrao": str(ANO - 1),
    },
    {
        "pagina": "manuais-escolares-mega.html",
        "alerta": "Datas MEGA — verificar em manuaisescolares.pt",
        "mes_rever": 7,
        "padrao": f"{ANO - 1}/{ANO}",
    },
    {
        "pagina": "passe-sub23.html",
        "alerta": "Passe sub-23 — verificar portaria vigente",
        "mes_rever": 9,
        "padrao": str(ANO - 1),
    },
]

issues_a_abrir = []
for alerta in ALERTAS:
    if HOJE.month == alerta["mes_rever"]:
        try:
            with open(alerta["pagina"], encoding="utf-8") as f:
                conteudo = f.read()
            if alerta["padrao"] in conteudo:
                issues_a_abrir.append({
                    "titulo": f"📅 REVER: {alerta['alerta']}",
                    "corpo": (
                        f"A página `{alerta['pagina']}` pode ter "
                        f"datas ou valores desactualizados.\n\n"
                        f"Padrão detectado: `{alerta['padrao']}`\n\n"
                        f"**Acção:** rever e actualizar com "
                        f"fact-checking antes de publicar."
                    ),
                })
        except FileNotFoundError:
            pass

os.makedirs("data", exist_ok=True)
with open("data/alertas_datas.json", "w", encoding="utf-8") as f:
    json.dump(issues_a_abrir, f, ensure_ascii=False, indent=2)

print(f"{len(issues_a_abrir)} alertas de datas gerados")
