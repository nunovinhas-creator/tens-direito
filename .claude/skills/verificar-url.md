# Skill: verificar-url

Testa se um URL existe e está acessível, e devolve a acção correcta a tomar.

## Uso

Invocar esta skill sempre que um URL vai entrar numa página HTML.
Nunca publicar um link sem primeiro passar por esta skill.

## Lógica de verificação

```python
import requests

def verificar_url(url: str, timeout: int = 10) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "pt-PT,pt;q=0.9",
    }
    try:
        resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        return {"url": url, "status": resp.status_code, "final_url": resp.url}
    except requests.Timeout:
        return {"url": url, "status": "timeout", "final_url": None}
    except requests.RequestException as e:
        return {"url": url, "status": "erro", "detalhe": str(e), "final_url": None}
```

## Tabela de decisão

| Status recebido | Significado | Acção obrigatória |
|---|---|---|
| **200** | URL válido e acessível | ✓ Usar o URL tal como está |
| **301 / 302** | Redirect permanente / temporário | Usar `final_url` (URL de destino) |
| **403** | Portal bloqueia scrapers/bots | Substituir pelo URL da página-mãe |
| **404** | Página não existe | Remover o link; texto fica sem âncora |
| **500 / 503** | Erro temporário do servidor | Marcar `[VERIFICAR — erro servidor DD/MM/AAAA]` |
| **timeout** | Inacessível (rede ou servidor lento) | Marcar `[VERIFICAR — timeout DD/MM/AAAA]` |
| **erro** | Falha de conexão (DNS, proxy) | Marcar `[VERIFICAR — inacessível DD/MM/AAAA]` |

## Regras especiais por domínio

### seg-social.pt / app.seg-social.pt
- Devolve 403 para scrapers — é comportamento esperado, não significa que o URL não existe
- URLs verificados manualmente a 23/06/2026 (ver CLAUDE.md) podem ser usados sem teste adicional
- Para URLs novos: usar URL pai `https://www.seg-social.pt` como fallback seguro

### dge.mec.pt
- Idem: 403 esperado para bots
- URLs verificados manualmente a 23/06/2026: `dge.mec.pt/acao-social-escolar`, `dge.mec.pt/manuais-escolares`, `dge.mec.pt/bolsas-de-merito`

### dre.pt
- 403 esperado para scrapers
- URL pai seguro: `https://dre.pt/pesquisa`

### URLs NOT na lista verificada do CLAUDE.md
- Testar sempre antes de publicar
- Se 403: não assumir que o URL é válido — usar URL pai
- Se 200: registar como verificado com data

## Formato de marcação no HTML

Quando um link não pode ser confirmado:

```html
<!-- VERIFICAR: [url] devolveu [status] em [DD/MM/AAAA] -->
<a href="[url-pai]">[texto do link]</a>
```

Ou, se não houver URL pai adequado, sem link:

```html
<!-- LINK REMOVIDO: [url] devolveu 404 em [DD/MM/AAAA] -->
consulta nos serviços da escola/agrupamento
```
