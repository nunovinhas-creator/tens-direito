# Levantamento — Dados Abertos (Fase 0)

Documento privado, mesma categoria de `ROADMAP.md`/`ANALISE-CLUSTER-ESCOLAR.md`
— raiz do repositório, nunca servido (`.md`, fora do sitemap/nav/pesquisa.js).
Não altera nenhum ficheiro existente. Objectivo: medir a distância real entre
o que já existe e uma base de dados publicável, antes de comprometer trabalho
de implementação.

Metodologia: inspecção directa dos ficheiros reais (`dados/parametros/*.yaml`,
`dados/parametros.json`, `dados/observacoes/*.json`, `tests/test_valores_ancora.py`)
e arqueologia de `git log` sobre o histórico completo do repositório (o clone
estava raso — só desde 2026-08-15 — corrigido com `git fetch --unshallow`
antes de qualquer conclusão sobre o ponto 3, para não avaliar "histórico
recuperável" a partir de uma janela de 9 dias por engano).

---

## 1. Inventário — o que já está estruturado

Padrão OpenFisca (`dados/parametros/<prestacao>.yaml`, consolidado em
`dados/parametros.json` por `scripts/gerar_parametros_json.py`, publicado em
`dados/tensdireito.db` por `scripts/gerar_base_dados.py`, servido em
`dados.html`). Cada parâmetro tem `descricao`/`unidade`/`valor`/
`vigencia_inicio`/`referencia_legal`/`fonte_url`/`verificado_em` (mais
`fonte_url_complementar`, opcional).

**5 ficheiros YAML, 5 prestações, 97 parâmetros no total:**

| Prestação | Ficheiro | N.º parâmetros | `valor: null` | Diploma associado | Data de verificação |
|---|---|---|---|---|---|
| Abono de Família | `abono.yaml` | 28 | 0 | Portaria n.º 60/2026/1 | 2026-07-19 |
| CSI | `csi.yaml` | 3 | 0 | Decreto-Lei n.º 232/2005 + Portaria n.º 480-D/2025/1 + Portaria n.º 358/2024/1 | 2026-07-19 |
| Habitação (IMT Jovem, Garantia Pública, dedução de rendas IRS) | `habitacao.yaml` | 32 | 0 | Lei n.º 73-A/2025, DL n.º 44/2024, DL n.º 97/2026, entre outros | 2026-07-19 a 2026-07-20 |
| PSU | `psu.yaml` | 19 | 5 | Decreto-Lei n.º 166/2026 | 2026-08-16 |
| Subsídio de Doença | `subsidio-doenca.yaml` | 15 | 0 | Guia Prático 5001 do ISS + DL vários | 2026-07-19 |
| **Total** | | **97** | **5** | | |

Todos os 97 parâmetros — mesmo os `null` — têm `referencia_legal`/`fonte_url`
preenchidos (0 em falta); os 5 `null` são deliberados (PSU: 3 do artigo 17.º —
mediana de renda do INE, trimestre de referência e portaria de
regulamentação, todos pendentes de uma Portaria ainda não publicada — mais
2 majorações, parentalidade e desemprego, também pendentes de regulamentação).
Guarda dura confirmada em `scripts/gerar_parametros_json.py`: qualquer entrada
já vigente sem `verificado_em`/`referencia_legal`/`fonte_url` faz o script
falhar (`exit 1`), nunca publica um placeholder como dado real.

**Simuladores já migrados para `fetch('/dados/parametros.json')` em runtime**
(nunca calculam com valores em falta — botão nasce `disabled` até o fetch
suceder): Abono, CSI, IMT Jovem, PSU, Subsídio de Doença — 5 dos 8
simuladores publicados.

**Publicação (Fase 3)**: `dados/tensdireito.db` (SQLite, determinístico —
duas corridas sobre o mesmo estado do repositório dão o mesmo ficheiro
byte-a-byte) com 2 tabelas — `parametros` (uma linha por prestação/parâmetro/
vigência, incluindo vigências passadas) e `historial` (derivada de
`git log` sobre `dados/observacoes/`) — servido via Datasette Lite, licença
CC BY 4.0, em `dados.html`.

---

## 2. Lacunas — valores que vivem só em HTML

**3 dos 8 simuladores nunca foram migrados** — continuam com um objecto JS
inline (`PARAMETROS_*`/`CONFIG`), cada valor já citando `fonte`/
`verificado_em` no próprio objecto, mas nunca reflectido em
`dados/parametros/*.yaml` nem em `dados/parametros.json`:

| Simulador | Parâmetros escalares no objecto JS | Extra | Estado |
|---|---|---|---|
| `simulador-rsi.html` | 12 (`PARAMETROS_RSI`) | — | Nenhum registo em `ROADMAP.md` a apontar para esta migração — nem sequer está na fila |
| `simulador-subsidio-desemprego.html` | 16 (`PARAMETROS_SUBSIDIO_DESEMPREGO` — contado mal como "17" na 1.ª versão deste levantamento, corrigido a 2026-08-24 no PASSO 0 da migração) | + tabela `TABELA_DURACAO_BASE` (12 linhas × dias) | Idem — sem registo em `ROADMAP.md` |
| `simulador-ase.html` | 2 (`limiteEscalaoA`/`limiteEscalaoB`) + 4 valores monetários em `cobertura` (texto, sem `fonte`/`verificado_em` por campo) | — | **Bloqueado por desenho** — `ROADMAP.md` já regista a razão (despacho anual da DGEstE 2026/2027 ainda não fornecido) e a dependência desejada (`ase.yaml` deve referenciar os escalões do abono, nunca duplicar) |

Ou seja: RSI e Subsídio de Desemprego não têm sequer o estatuto de "bloqueado,
à espera de fonte" que o ASE tem — são simplesmente trabalho por começar, sem
nenhum registo formal.

**Páginas de conteúdo puro (sem simulador nenhum) com valores legais só em
prosa**, nunca capturados em nenhum ficheiro estruturado. Amostra de duas,
contadas por valor distinto (não por menção repetida):

- `subsidio-parental.html` — 15 valores distintos em €/% (537,13€, 429,70€,
  128.911,20€, 14,32€, 1.200€, 4.800€, 7.200€, 40€, 30%, 40%, 50%, 80%, 83%,
  90%, 100%).
- `prestacao-social-para-a-inclusao.html` — 16 valores distintos (333,64€,
  4.003,68€, 8.040€, 670€, 12.880€, 50%, 55%, 60%, 65%, 80%, 95%, 8%, 100%).

Outras páginas na mesma situação, sem simulador nem YAML, com densidade de €
comparável (contagem bruta de ocorrências do símbolo €, inclui repetições —
proxy do volume de prosa financeira, não do número de parâmetros distintos):
`acao-social-escolar.html` (50), `cuidador-informal.html` (34),
`complemento-solidario-idosos.html` (37 — o artigo, distinto do simulador já
migrado), `bolsa-de-merito.html` (30), `bolsa-de-estudo-ensino-superior.html`
(30), `baixa-medica-subsidio-doenca.html` (22 — idem, artigo distinto do
simulador migrado), `amim-beneficios-fiscais.html`/`amim.html`, `porta-65.html`.

**Estimativa**: entre os 3 simuladores por migrar (≈47 valores escalares +
uma tabela de 12 linhas) e as páginas de conteúdo puro sem qualquer
retaguarda estruturada (RSI/subsídio de desemprego têm pelo menos os seus
próprios artigos também sem YAML, mais subsídio parental, PSI, cuidador
informal, AMIM, bolsa de mérito, bolsa de estudo, ASE artigo), a ordem de
grandeza é **60 a 90+ valores legais distintos** ainda só em HTML — mais do
que o dobro dos 97 já estruturados. Nota de honestidade: isto é uma
estimativa por amostragem (2 páginas contadas ao pormenor + contagem bruta
de € nas restantes), não uma contagem exaustiva linha a linha de todas as
~55 páginas servidas.

**Nota à parte — calendário de pagamentos**: `data/calendario_pagamentos.json`
já é estruturado, mas é um sistema deliberadamente separado (datas de
pagamento por mês, gerado por scraping automático, não "parâmetros legais"
no sentido OpenFisca) — não conta nem para o inventário nem para a lacuna.

---

## 3. Histórico — o que existe, o que é recuperável

**O padrão OpenFisca já suporta série temporal** (`valores: [...]`, uma
entrada por `vigencia_inicio`) — mas, na prática, só **3 dos 97 parâmetros**
têm mais do que uma vigência registada:

| Parâmetro | Vigências | Ficheiro |
|---|---|---|
| `imt_isencao_total_limite_eur` | 2024-08-01, 2026-01-01 | `habitacao.yaml` |
| `imt_isencao_parcial_limite_eur` | 2024-08-01, 2026-01-01 | `habitacao.yaml` |
| `deducao_rendas_irs_limite_eur` | 2023-01-01, 2026-01-01, 2027-01-01 | `habitacao.yaml` |

Os restantes 94 têm sempre uma única vigência (o valor de 2026) — foram
escritos assim desde o início, nunca acumularam histórico via edições
sucessivas.

**O `git log` dos próprios ficheiros estruturados dá muito pouco**: os 5
`.yaml` têm 1-2 commits cada desde que nasceram (2026-07-19/20); o
`dados/parametros.json` tem 11 commits, mas **8 deles só mudam o campo
`gerado_em`** (regeneração diária, conteúdo idêntico) — só 2 commits (a
criação, 2026-08-15, e a adição do bloco `art17_*` da PSU, 2026-08-16)
alteraram valores de facto. Ou seja: **o sistema estruturado, por si só, não
tem histórico nenhum anterior a 2026** — nunca vigorou durante uma transição
de ano legal, por isso nunca precisou de guardar um valor anterior a não ser
os 3 casos acima (que já nasceram com a série completa escrita à mão, não
acumulada organicamente).

**O histórico real do site vive no `git log` das próprias páginas HTML**, e
esse sim é profundo — o repositório tem histórico completo desde 2026-06-23
(669 commits; o clone local estava truncado a 9 dias antes de
`git fetch --unshallow`). Mas esse histórico:

1. **Não documenta transições de valores legais entre anos civis** — o site
   nasceu já em 2026, a citar sempre os valores de 2026 (confirmado em
   `abono-de-familia.html`: a 1.ª versão publicada, 2026-06-23, já dizia
   "IAS 2026 de 537,13€"; o valor de 2025 — 522,50€ — só aparece como
   referência de contexto dentro da prosa, nunca como "o valor vigente"
   numa versão anterior da página).
2. **Documenta correcções factuais reais**, mas de forma não estruturada —
   por exemplo, a correcção do piso diário do subsídio de doença (de uma
   base IAS errada para a base RMMG correcta, 2026-07-19) ou a remoção da
   redução de 80% nos rendimentos de trabalho do CSI (2026-07-19) estão
   nos commits e narradas em prosa nas entradas de revisão de `CLAUDE.md`,
   mas não são recuperáveis por uma query — exigem `git log -S<valor>` por
   ficheiro, ou ler as entradas de revisão relevantes de `CLAUDE.md` à mão.

**`dados/observacoes/*.json` (Fase 1, git scraping) não é histórico de
valores** — é um log de conteúdo extraído por fonte monitorizada (DRE,
IEFP, IGeFE, etc.), sobrescrito quando o SHA-256 do conteúdo muda,
com o histórico real a viver no `git log` de cada ficheiro. É jovem
(nasceu 2026-07-19) e fino: os 3 ficheiros verificados têm 1, 1 e 4 commits
respectivamente — a maioria das fontes monitorizadas ainda não mudou de
conteúdo desde que este sistema arrancou. E mesmo quando muda, guarda
**texto extraído da página** (títulos/parágrafos de resultados de pesquisa),
não um valor parseado — nunca substitui a leitura humana para transformar
"a fonte mudou" em "o parâmetro X passou de A para B".

**Conclusão do ponto 3**: não há hoje nenhum histórico de valores legais
anteriores a 2026 recuperável de forma estruturada. O que existe é (a) 3
séries temporais completas escritas à mão no habitacao.yaml, e (b) um
histórico de correcções recente (desde jul/ago 2026) espalhado por commits
Git e pela narrativa de `CLAUDE.md`, arqueologicamente recuperável mas não
consultável como dado.

---

## 4. Canários — valores já trancados por testes

`tests/test_valores_ancora.py` (973 linhas, **62 funções de teste**) é o
mecanismo real de consistência entre páginas — falha sozinho quando duas
páginas (ou uma página e o `dados/parametros.json`) divergem sobre o mesmo
valor legal, ou quando o IAS mudar e um `<title>`/meta description citando
um múltiplo do IAS não for actualizado.

Cobertura por prestação (contagem de funções cujo nome/corpo referencia a
prestação):

| Prestação | N.º de testes | Cobre YAML↔HTML, ou só HTML↔HTML? |
|---|---|---|
| PSU | 12 | YAML↔HTML (`dados/parametros.json` como fonte) |
| Habitação (IMT Jovem/Garantia Pública/dedução rendas) | 12 | YAML↔HTML |
| Subsídio de Doença | 6 | YAML↔HTML |
| Renovação Cartão de Cidadão | 3 | Só HTML↔HTML (sem YAML — fora do âmbito OpenFisca, são taxas administrativas) |
| CSI | 3 | YAML↔HTML + guarda anti-reintrodução dos 80% |
| AMIM / PSI / Cartão de Estacionamento | 6 | Só HTML↔HTML |
| Subsídio de Desemprego (artigo, não simulador) | 4 | Só HTML↔HTML — nenhum contra o YAML, porque não há YAML |
| Assistência a Família e Filhos | 3 | Só HTML↔HTML |
| Abono | 2 | Só HTML↔HTML |
| ASE / Cuidador Informal | 2 | Só HTML↔HTML |
| 1.º Direito | 1 | Só HTML↔HTML (deriva do IAS) |
| **RSI** | **0** | **Nenhuma cobertura** — nem HTML↔HTML entre `rsi.html` e `simulador-rsi.html` |
| Sincronização geral YAML→JSON | 2 | `test_dados_parametros_json_sincronizado_com_os_yaml` (`--check`), `test_nenhum_parametro_vigente_fica_sem_verificado_em` |

**RSI é o único apoio com página + simulador publicados e zero canário** —
nada impede hoje que `rsi.html` e `simulador-rsi.html` divirjam sobre o
valor-base de 247,56€ sem que nenhum teste dê sinal.

Existe também `tests/test_anos_metadados.py` — canário irmão, mas para anos
civis em metadados (não valores), fora do âmbito directo deste levantamento.

---

## 5. Distância até uma base de dados publicável — síntese

| Dimensão | Estado |
|---|---|
| Infraestrutura de publicação (YAML → JSON → SQLite → Datasette Lite) | **Pronta e em produção**, determinística, com guarda dura contra placeholders |
| Cobertura de prestações | **5 de ~15+ prestações com página própria** (abono, CSI, habitação/IMT/garantia/dedução rendas, PSU, subsídio de doença) |
| Cobertura de simuladores | **5 de 8** migrados; RSI e Subsídio de Desemprego nem sequer registados como pendência no `ROADMAP.md` (ASE está, e correctamente bloqueado) |
| Valores só em HTML, sem retaguarda nenhuma | Estimativa 60-90+, predominantemente em páginas de conteúdo puro sem simulador (subsídio parental, PSI, cuidador informal, AMIM, bolsa de mérito, bolsa de estudo) |
| Histórico multi-ano | Só 3 parâmetros (de 97) têm série temporal real; o resto nasceu já só com o valor de 2026 |
| Rede de segurança (canários) | 62 testes, mas com lacunas claras — RSI sem nenhuma, subsídio de desemprego só ao nível do artigo |

**Leitura directa**: a base de dados publicada hoje é honesta (nunca finge
cobrir o que não cobre) e tecnicamente sólida, mas cobre uma fatia
minoritária do site — a maior parte do "direito social" publicado no
Tens Direito ainda não tem retaguarda de dados estruturados. Alargar a
cobertura é essencialmente repetir, prestação a prestação, o mesmo padrão de
3 passos já provado no CSI/subsídio de doença/abono (auditoria da fonte
primária → YAML com `referencia_legal`/`fonte_url`/`verificado_em` →
migração do simulador/artigo para consumir `dados/parametros.json` +
canário em `test_valores_ancora.py`) — nenhuma decisão de arquitectura nova
é necessária, só volume de trabalho.

---

*Nenhum ficheiro existente foi alterado por este levantamento. Este
documento não foi commitado nem publicado — fica no working tree da branch
`claude/dados-abertos-levantamento-g78v7q` para revisão antes de qualquer
decisão sobre o que publicar a seguir.*
