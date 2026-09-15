# Skill: estrutura-pagina

Template HTML obrigatório para todas as páginas de conteúdo do Tens Direito.
Inclui as 10 secções obrigatórias e os blocos JSON-LD prontos a preencher.

## Uso

Usar este template sempre que se gera uma nova página de conteúdo.
Nunca criar HTML de raiz sem partir deste template.

## Template base

```html
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <link rel="shortcut icon" href="/favicon.svg">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="index, follow">
  <link rel="sitemap" type="application/xml" href="/sitemap.xml">
  <title>[TÍTULO SEO — máx. 60 caracteres]</title>
  <meta name="description" content="[META DESCRIPTION — máx. 155 caracteres]">

  <!-- [SECÇÃO 1: CSS — copiar de abono-de-familia.html sem alterações] -->
  <style>
    /* usar o CSS de abono-de-familia.html como base */
  </style>

  <!-- [SECÇÃO 2: JSON-LD FAQPage — 5 perguntas obrigatórias] -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "[Pergunta 1 — o que é X?]",
        "acceptedAnswer": { "@type": "Answer", "text": "[Resposta em condicional]" }
      },
      {
        "@type": "Question",
        "name": "[Pergunta 2 — quem tem direito?]",
        "acceptedAnswer": { "@type": "Answer", "text": "[Resposta em condicional]" }
      },
      {
        "@type": "Question",
        "name": "[Pergunta 3 — qual o valor?]",
        "acceptedAnswer": { "@type": "Answer", "text": "[Resposta com fonte e data]" }
      },
      {
        "@type": "Question",
        "name": "[Pergunta 4 — como pedir?]",
        "acceptedAnswer": { "@type": "Answer", "text": "[Resposta passo-a-passo]" }
      },
      {
        "@type": "Question",
        "name": "[Pergunta 5 — prazo/pagamento?]",
        "acceptedAnswer": { "@type": "Answer", "text": "[Resposta em condicional]" }
      }
    ]
  }
  </script>

  <!-- [SECÇÃO 3: JSON-LD HowTo — passos para pedir] -->
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "HowTo",
    "name": "Como pedir [NOME DO APOIO]",
    "description": "[Descrição do processo em 1 frase]",
    "step": [
      { "@type": "HowToStep", "position": 1, "name": "[Passo 1]", "text": "[Instrução]" },
      { "@type": "HowToStep", "position": 2, "name": "[Passo 2]", "text": "[Instrução]" },
      { "@type": "HowToStep", "position": 3, "name": "[Passo 3]", "text": "[Instrução]" },
      { "@type": "HowToStep", "position": 4, "name": "[Passo 4]", "text": "[Instrução]" },
      { "@type": "HowToStep", "position": 5, "name": "[Passo 5]", "text": "[Instrução]" }
    ]
  }
  </script>
</head>
<body>

  <!-- [SECÇÃO 4: NAV — idêntico em todas as páginas] -->
  <header>
    <nav>
      <a href="/" class="logo">
        <svg width="36" height="36" viewBox="0 0 36 36" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <rect width="36" height="36" rx="9" fill="#0F766E"/>
          <path d="M9 18 L16 25 L27 11" fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="logo-text"><span class="tens">Tens </span><span class="direito">Direito</span></div>
      </a>
      <a href="/noticias.html" class="nav-link">Notícias</a>
      <a href="/sobre.html" class="nav-link">Sobre</a>
    </nav>
  </header>

  <!-- [SECÇÃO 5: HERO com resposta directa] -->
  <section class="hero">
    <div class="hero-inner">
      <h1>[TÍTULO DA PÁGINA]</h1>
      <div class="resposta-direta">
        [RESPOSTA DIRECTA em 1-2 frases: o que é, para quem serve, valor/condição chave]
      </div>
    </div>
  </section>

  <main>

    <!-- [SECÇÃO 6: QUEM TEM DIREITO — em condicional] -->
    <div class="card">
      <span class="badge">Elegibilidade</span>
      <h2>Quem poderá ter direito</h2>
      <!-- FONTE: [url] | scraped: [data_acesso] -->
      <p>Poderão ter direito... [condições em condicional]</p>
      <ul>
        <li>[Condição 1]</li>
        <li>[Condição 2]</li>
      </ul>
    </div>

    <!-- [SECÇÃO 7: VALORES/TABELA — com fonte datada] -->
    <div class="card">
      <span class="badge">Valores [ANO]</span>
      <h2>[Escalões / Valores / Condições]</h2>
      <!-- FONTE: [url] | scraped: [data_acesso] -->
      <div class="tabela-wrap">
        <table>
          <thead><tr><th>[Col 1]</th><th>[Col 2]</th></tr></thead>
          <tbody>
            <tr><td>[dado]</td><td>[dado]</td></tr>
          </tbody>
        </table>
      </div>
      <p class="nota-tabela">Verificado a [DD/MM/AAAA] · <a href="[URL VERIFICADO]">Fonte: [nome]</a></p>
    </div>

    <!-- [SECÇÃO 8: COMO PEDIR — passo-a-passo] -->
    <div class="card passos">
      <span class="badge">Passo a passo</span>
      <h2>Como pedir</h2>
      <!-- FONTE: [url] | scraped: [data_acesso] -->
      <ol>
        <li><span>[Passo 1]</span></li>
        <li><span>[Passo 2]</span></li>
        <li><span>[Passo 3]</span></li>
        <li><span>[Passo 4]</span></li>
        <li><span>[Passo 5]</span></li>
      </ol>
    </div>

    <!-- [SECÇÃO 9: FONTES DATADAS — obrigatório] -->
    <div class="fonte-bloco">
      <strong>Fontes e verificação:</strong><br>
      <a href="[URL VERIFICADO]" target="_blank" rel="noopener">[Fonte 1]</a> ·
      <a href="[URL VERIFICADO]" target="_blank" rel="noopener">[Fonte 2]</a><br>
      Verificado a [DD de mês de AAAA] · [Diploma legal se aplicável]
    </div>

    <!-- [SECÇÃO 10: DISCLAIMER — obrigatório em todas as páginas] -->
    <div class="disclaimer">
      <strong>Aviso de independência:</strong> O Tens Direito é um site informativo
      independente, sem qualquer relação com o Estado ou qualquer entidade pública.
      A informação aqui publicada é de carácter geral e pode não refletir o teu caso
      concreto. Para confirmação oficial, consulta directamente
      <a href="[URL VERIFICADO DA FONTE OFICIAL]" target="_blank" rel="noopener"
         style="color:#856404;">[nome da entidade oficial]</a>.
    </div>

  </main>

  <!-- FOOTER — idêntico em todas as páginas -->
  <footer>
    <p>tensdireito.com — Informação verificada para cidadãos portugueses</p>
    <p style="margin-top:0.5rem;">
      <a href="/sobre.html">Sobre</a> · <a href="/fontes.html">Fontes</a> · <a href="/privacidade.html">Privacidade</a>
    </p>
  </footer>

</body>
</html>
```

## Regras de preenchimento

1. **Secção 5 (Hero):** resposta directa obrigatória — o leitor entende o essencial sem rolar a página
2. **Secções 6, 7, 8:** cada uma começa com comentário `<!-- FONTE: url | scraped: data -->`
3. **Secção 7 (Valores):** só entram valores confirmados pelo scraper ou verificação manual — nunca de memória
4. **Secção 9 (Fontes):** só URLs da lista verificada no CLAUDE.md ou testados com `verificar-url`
5. **Secção 10 (Disclaimer):** texto fixo, nunca encurtar ou remover

## Cores e identidade

| Elemento | Valor |
|---|---|
| Cor principal (teal) | `#0F766E` |
| Cor secundária (teal claro) | `#0D9488` |
| Texto escuro | `#0F172A` |
| Texto corpo | `#495057` |
| Fundo página | `#f8f9fa` |
| Fundo hero | `#0F766E` (branco sobre fundo teal) |
| Badge cor fundo | `#e6f4f1` |
| Aviso amarelo (disclaimer) | `#fff3cd` com border `#ffc107` |
