"""
Diagnóstico TEMPORÁRIO (Fase 3 do calendário de pagamentos) — corre num
runner real via workflow_dispatch para responder a 3 perguntas antes de
escrever o workflow mensal definitivo:

  1. A notícia mensal do calendário é acessível de um runner (sem
     Playwright)? Com que estrutura HTML?
  2. O calendário de AGOSTO já está publicado? Em que URL/slug?
  3. O portlet antigo /pagamentos2 (com parâmetro de data) devolve
     conteúdo estruturado utilizável?

Só lê e imprime — nunca escreve ficheiros do repositório. Apagar este
script e o workflow correspondente no fim do diagnóstico (mesmo padrão
de diagnostico-dre-psu-temp / diagnostico-igefe-temp).
"""
from __future__ import annotations

import re
import sys

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "pt-PT,pt;q=0.9",
}

BASE = "https://www.seg-social.pt"
ASSET = f"{BASE}/noticias/-/asset_publisher/kBZtOMZgstp3/content"

URLS = [
    # julho — URL conhecido (do índice do Google), serve de referência de formato
    f"{ASSET}/datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-julho",
    # candidatos para agosto (slug é instável — testar variantes)
    f"{ASSET}/datas-de-pagamento-dos-subsidios-sociais-e-pensoes-em-agosto",
    f"{ASSET}/datas-de-pagamento-dos-subsidios-sociais-em-agosto",
    # listagem de notícias — para descobrir o slug real do mês corrente/seguinte
    f"{BASE}/noticias",
    # portlet antigo com parâmetro de data (potencial fonte estruturada)
    f"{BASE}/pagamentos2",
]


def examinar(url: str) -> None:
    print(f"\n{'='*78}\nURL: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
    except Exception as e:
        print(f"  ERRO DE REDE: {e}")
        return
    print(f"  status={r.status_code} final_url={r.url} bytes={len(r.text)}")
    soup = BeautifulSoup(r.text, "html.parser")
    titulo = soup.title.get_text(strip=True) if soup.title else "(sem <title>)"
    print(f"  title: {titulo}")

    if "/noticias" in url and "asset_publisher" not in url:
        # listagem: só interessa descobrir links de notícias de datas de pagamento
        links = sorted({
            a["href"] for a in soup.find_all("a", href=True)
            if "datas-de-pagamento" in a["href"]
        })
        print(f"  links 'datas-de-pagamento' encontrados ({len(links)}):")
        for li in links[:20]:
            print(f"    {li}")
        return

    # artigo/portlet: despejar o texto útil para calibrar o parser
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    texto = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))
    print(f"  texto útil ({len(texto)} chars) — primeiros 6000:")
    print("  ---")
    print(texto[:6000])
    print("  ---")

    # estrutura de tabelas, se existirem
    tabelas = soup.find_all("table")
    print(f"  tabelas no HTML: {len(tabelas)}")
    for i, t in enumerate(tabelas[:3]):
        linhas = t.find_all("tr")
        print(f"    tabela {i}: {len(linhas)} linhas; 1.as células: "
              + " | ".join(c.get_text(strip=True)[:40]
                           for c in (linhas[0].find_all(["td", "th"]) if linhas else [])))


def main() -> int:
    for url in URLS:
        examinar(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
