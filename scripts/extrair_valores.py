#!/usr/bin/env python3
"""
Extrai valores estruturados dos JSONs scraped e compara com os valores
publicados nos HTMLs do site. Regista divergências em data/divergencias.json.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRAPED_DIR = BASE_DIR / "data" / "scraped"
DIVERGENCIAS_PATH = BASE_DIR / "data" / "divergencias.json"

# Campos a monitorizar: {slug_fonte: {nome_campo: {patron_regex, campo_html, tipo}}}
CAMPOS = {
    "seg_social_abono": {
        "ias_2026": {
            "exemplo": "537,13",
            "tipo": "euro",
            "regex": r"537[,.]13",
            "html_file": "abono-de-familia.html",
            "descricao": "IAS 2026",
        },
        "escalao_1_valor_6_16": {
            "exemplo": "42,84",
            "tipo": "euro",
            "regex": r"42[,.]84",
            "html_file": "abono-de-familia.html",
            "descricao": "Escalão 1 — 6 a 16 anos",
        },
    },
    "iefp_desemprego": {
        "prazo_pedido_dias": {
            "exemplo": "90 dias",
            "tipo": "texto",
            "regex": r"90\s*dias",
            "html_file": None,
            "descricao": "Prazo para pedir subsídio de desemprego",
        },
    },
    "dre_ias": {
        "ias_valor": {
            "exemplo": "537,13",
            "tipo": "euro",
            "regex": r"537[,.]13",
            "html_file": "abono-de-familia.html",
            "descricao": "IAS no Diário da República",
        },
    },
}


def _extrair_de_json(slug: str, campo: str, regex: str) -> str | None:
    latest = SCRAPED_DIR / f"{slug}_latest.json"
    if not latest.exists():
        return None
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except Exception:
        return None

    # Procurar o padrão em todos os valores de texto do JSON
    texto = json.dumps(data, ensure_ascii=False)
    m = re.search(regex, texto)
    return m.group(0) if m else None


def _extrair_de_html(html_file: str, regex: str) -> str | None:
    path = BASE_DIR / html_file
    if not path.exists():
        return None
    texto = path.read_text(encoding="utf-8")
    m = re.search(regex, texto)
    return m.group(0) if m else None


def main() -> list[dict]:
    divergencias = []
    hoje = datetime.now(timezone.utc).isoformat()

    for slug, campos in CAMPOS.items():
        for nome_campo, cfg in campos.items():
            regex = cfg["regex"]
            html_file = cfg.get("html_file")

            valor_fonte = _extrair_de_json(slug, nome_campo, regex)
            valor_publicado = _extrair_de_html(html_file, regex) if html_file else None

            # Só reportar divergência se a fonte TEM o valor mas o HTML NÃO
            if valor_fonte and html_file and not valor_publicado:
                divergencias.append({
                    "campo": nome_campo,
                    "descricao": cfg["descricao"],
                    "slug_fonte": slug,
                    "html_file": html_file,
                    "valor_fonte": valor_fonte,
                    "valor_publicado": valor_publicado,
                    "data": hoje,
                })
                print(f"⚠ DIVERGÊNCIA: {nome_campo} — fonte: {valor_fonte!r} | html: {valor_publicado!r}")
            else:
                status = "OK" if valor_fonte else "não encontrado na fonte"
                print(f"  {slug}/{nome_campo}: {status}")

    DIVERGENCIAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DIVERGENCIAS_PATH, "w", encoding="utf-8") as f:
        json.dump(divergencias, f, ensure_ascii=False, indent=2)

    print(f"\n{len(divergencias)} divergência(s) registada(s) em {DIVERGENCIAS_PATH}")
    return divergencias


if __name__ == "__main__":
    main()
