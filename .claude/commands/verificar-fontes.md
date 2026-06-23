# /verificar-fontes

Audita todos os links de todas as páginas HTML publicadas e gera relatório de links quebrados.

## Uso

```
/verificar-fontes
```

Sem argumentos — verifica todas as páginas na raiz do repositório.

## Passos de execução

### Passo 1 — Listar páginas publicadas

```python
from pathlib import Path
paginas = [p for p in Path('.').glob('*.html')
           if p.name not in ('404.html',)]
```

### Passo 2 — Extrair todos os links de cada página

```python
from bs4 import BeautifulSoup

def extrair_links(ficheiro):
    soup = BeautifulSoup(ficheiro.read_text(), 'lxml')
    return [(a.get_text(strip=True), a['href'])
            for a in soup.find_all('a', href=True)
            if a['href'].startswith('http')]
```

### Passo 3 — Testar cada link com a skill `verificar-url`

Para cada link encontrado, usar a skill `verificar-url` e registar o resultado.
Timeout máximo: 10 segundos por pedido.

### Passo 4 — Classificar resultados

| Status | Acção |
|---|---|
| 200 | ✓ OK — sem acção |
| 301/302 | ⚠ Redirect — actualizar para URL final |
| 403 | ⚠ Bloqueado — substituir por URL pai se possível |
| 404 | ✗ Quebrado — remover ou corrigir |
| Timeout | ⚠ Inacessível — marcar [VERIFICAR] |

### Passo 5 — Gerar relatório

Escrever relatório em `VERIFICACAO-PENDENTE.md` com formato:

```markdown
## Auditoria de links — [data]

### [pagina.html]
- ✗ [texto do link] → [url] — STATUS: 404
- ⚠ [texto do link] → [url] — STATUS: timeout
```

### Passo 6 — Aplicar correcções automáticas

Para links com 404 confirmado: remover o `href` e o texto fica sem âncora.
Para redirects 301/302: actualizar o `href` para o URL de destino final.
Para 403 e timeouts: marcar no HTML com comentário `<!-- VERIFICAR [data] -->`.

### Passo 7 — Commit se houver correcções

```
fix: correcção de links quebrados — auditoria [data]

verificar-fontes: [N] links testados, [N] corrigidos, [N] marcados VERIFICAR
```

## Frequência recomendada

Correr semanalmente ou antes de qualquer nova publicação.
O GitHub Action `noticias-diarias.yml` pode ser extendido para incluir esta verificação.
