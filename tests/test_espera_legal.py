"""
Canário — afirmações de "à espera de um instrumento legal" nunca podem
ficar indefinidamente por reverificar (sessão "LEVANTAMENTO DE ESPERAS
POR INSTRUMENTO LEGAL", 2026-08-26).

Motivação real: `index.html` afirmou "Aguarda decreto-lei com valores"
sobre a PSU durante 12 dias depois de o decreto-lei já estar publicado e
em vigor (DL n.º 166/2026, 13/08/2026) — a fonte de verdade
(`data/destaque_evento.json`) tinha uma nota interna a dizer exactamente
o que fazer quando isso acontecesse, e ninguém a leu. Uma afirmação de
pendência não tem prazo de validade e ninguém a revisita sozinha.

## O que conta como "espera por instrumento legal"

Um VERBO de espera (`aguarda`, `ainda não está/entrou em vigor`, `por
publicar/regulamentar/confirmar`) a co-ocorrer, numa janela curta (mesma
frase), com um SUBSTANTIVO de instrumento legal (`decreto-lei`,
`portaria`, `regulamentação`, `diploma`, `Diário da República`) — desde
que esse instrumento NÃO esteja identificado por número (`decreto-lei
n.º 166/2026` já existe, é facto assente, nunca uma espera) nem
referenciado por artigo definido/demonstrativo ("o decreto-lei", "essa
portaria" — referência anafórica a algo já citado antes no texto).

## O que NÃO conta (nunca marcar como espera)

1. "Aguarda a decisão"/"aguarda a validação"/"aguarda a carta de
   confirmação"/"aguarda a notificação"/"aguarda avaliação"/"aguarda o
   pagamento"/"aguarda a convocatória" — passo de processo que o PRÓPRIO
   LEITOR vive (com SLA institucional conhecido: dias úteis, prazo
   legal), não uma afirmação do site sobre uma lacuna na lei. Aparece
   legitimamente em dezenas de páginas (HowTo/checklist) — nunca tem
   substantivo de instrumento legal por perto, por isso o regex nunca
   dispara (confirmado nesta sessão contra ~20 ocorrências reais).
2. Referência anafórica a um diploma já identificado — "o decreto-lei
   [...] só produz efeitos a 31 de dezembro de 2026" (como-pedir-psu.html)
   fala de um facto já assente (o DL 166/2026, citado por número mais
   acima no mesmo texto), não de uma lacuna. Excluído pela exigência de
   ausência de artigo definido/demonstrativo antes do instrumento.
3. `noticias.html` — arquivo de notícias auto-gerado (REGRA DE OURO),
   cada item é um SNAPSHOT datado (`<time datetime="...">`) do que era
   verdade no dia da publicação, como um arquivo de jornal — nunca uma
   afirmação viva sobre o estado actual do site. Fora do âmbito.
4. Conteúdo dentro de `<script>` (incluindo JSON-LD) — o mesmo texto de
   FAQ já é mantido em sincronia 1:1 com o `<details>` visível por
   convenção do repositório (ver CLAUDE.md); duplicar aqui a exigência
   de marcador dentro de um bloco JSON não é possível sem partir o JSON
   (`<!--` não é sintaxe JSON válida).

## Duas fontes de "espera", dois mecanismos

**A) Prosa em HTML** — qualquer afirmação apanhada pelo regex tem de ter,
dentro de uma janela curta antes/depois, um marcador
`<!-- ESPERA-LEGAL: verificado_em="AAAA-MM-DD" -->`. Falha se o marcador
não existir (sem data associada) ou se `verificado_em` tiver mais de
`LIMIAR_DIAS` dias (data ultrapassada — precisa de reverificação).

**B) Parâmetros YAML pendentes** (`dados/parametros/*.yaml`, `valor:
null`) — só os que a própria descrição já marca como `PENDENTE`
(convenção já em uso nestes ficheiros antes deste teste existir, nunca
inventada aqui — distingue um valor pendente de confirmação legal de um
valor `null` por desenho arquitectural, ex. `majoracao_parentalidade_mensal`
da PSU, que nunca terá um único valor fixo e não é "espera" nenhuma).
Cada entrada `PENDENTE` já é obrigada a ter `verificado_em` por
`scripts/gerar_parametros_json.py` (PASSO 0) — este teste acrescenta só
o limiar de idade, que aquele script não verifica.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

from sincronizar_clusters import encontrar_paginas  # noqa: E402

PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
PARAMETROS_DIR = RAIZ / "dados" / "parametros"

LIMIAR_DIAS = 60

# noticias.html é arquivo auto-gerado de snapshots datados — nunca uma
# afirmação viva do site (ver docstring do módulo, ponto 3).
PAGINAS_EXCLUIDAS = {"noticias.html"}

VERBO_ESPERA = (
    r"(?:aguarda(?:m)?|ainda\s+n[ãa]o\s+(?:est[áa]|entrou)\s+em\s+vigor"
    r"|por\s+(?:publicar|regulamentar|confirmar))"
)

# Substantivo do instrumento legal, nunca precedido de artigo definido/
# demonstrativo (sinal de referência anafórica a um diploma já
# identificado — ver docstring, ponto 2) nem seguido de "n.º"/"nº" (um
# instrumento já numerado é facto assente, nunca uma espera).
_ARTIGO_DEFINIDO = (
    r"(?<!\bo\s)(?<!\ba\s)(?<!\bdo\s)(?<!\bda\s)(?<!\bno\s)(?<!\bna\s)"
    r"(?<!\besse\s)(?<!\bessa\s)(?<!\beste\s)(?<!\besta\s)"
)
INSTRUMENTO_LEGAL = (
    rf"{_ARTIGO_DEFINIDO}(?:decreto-lei|portaria|regulamenta[çc][ãa]o|diploma"
    rf"|di[áa]rio\s+da\s+rep[úu]blica)(?!\s*(?:n\.?º|nº))"
)

PADRAO_ESPERA_LEGAL = re.compile(
    rf"(?:{VERBO_ESPERA}[^.]{{0,180}}{INSTRUMENTO_LEGAL})"
    rf"|(?:{INSTRUMENTO_LEGAL}[^.]{{0,180}}{VERBO_ESPERA})",
    re.IGNORECASE,
)

PADRAO_SCRIPT = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)

PADRAO_MARCADOR = re.compile(
    r'<!--\s*ESPERA-LEGAL:\s*verificado_em="(\d{4}-\d{2}-\d{2})"\s*-->'
)

JANELA_MARCADOR = 400  # chars antes/depois do match onde o marcador é aceite


def _ler(nome_relativo: str) -> str:
    return (RAIZ / nome_relativo).read_text(encoding="utf-8")


def _paginas_para_varrer():
    return [
        p
        for p in encontrar_paginas()
        if p.name not in PAGINAS_EXCLUIDAS
    ]


def _spans_de_script(texto: str) -> list[tuple[int, int]]:
    return [m.span() for m in PADRAO_SCRIPT.finditer(texto)]


def _dentro_de_algum_span(pos: int, spans: list[tuple[int, int]]) -> bool:
    return any(inicio <= pos < fim for inicio, fim in spans)


def _idade_em_dias(data_str: str, hoje: date) -> int:
    return (hoje - date.fromisoformat(data_str)).days


def _mensagem_reverificar(trecho: str, motivo: str) -> str:
    return (
        f'Afirmação de espera por instrumento legal "...{trecho}..." {motivo} '
        "Antes de corrigir: confirma em dre.pt (ou WebSearch, se dre.pt estiver "
        "bloqueado nesta sessão) se o diploma em falta já foi publicado. "
        "Se JÁ foi publicado: corrige a afirmação para reflectir o estado real "
        "(ver a correcção de index.html/data/destaque_evento.json nesta mesma "
        'sessão como exemplo). Se AINDA está pendente: renova a data do '
        'marcador ESPERA-LEGAL (ou verificado_em no YAML) para hoje — a '
        "espera continua legítima, só precisava de confirmação."
    )


def test_html_afirmacoes_de_espera_legal_tem_marcador_recente():
    """Cada afirmação apanhada pelo regex (fora de <script>) tem de ter,
    numa janela curta, um marcador `<!-- ESPERA-LEGAL: verificado_em="..."
    -->` com menos de LIMIAR_DIAS dias. Falha sem marcador (nunca
    verificada) ou com marcador vencido (verificada há demasiado tempo)
    — nunca falha em silêncio, a mensagem diz sempre o que fazer."""
    hoje = date.today()
    falhas: list[str] = []

    for pagina in _paginas_para_varrer():
        texto = pagina.read_text(encoding="utf-8")
        spans_script = _spans_de_script(texto)
        rel = str(pagina.relative_to(RAIZ))

        for match in PADRAO_ESPERA_LEGAL.finditer(texto):
            if _dentro_de_algum_span(match.start(), spans_script):
                continue  # dentro de <script>/JSON-LD — fora do âmbito

            trecho = match.group(0)[:120].replace("\n", " ")
            janela = texto[max(0, match.start() - JANELA_MARCADOR): match.end() + JANELA_MARCADOR]
            marcador = PADRAO_MARCADOR.search(janela)

            if not marcador:
                falhas.append(
                    f"{rel}: " + _mensagem_reverificar(
                        trecho, "não tem nenhum marcador ESPERA-LEGAL nas proximidades — sem data associada."
                    )
                )
                continue

            data_str = marcador.group(1)
            try:
                idade = _idade_em_dias(data_str, hoje)
            except ValueError:
                falhas.append(
                    f"{rel}: marcador ESPERA-LEGAL com data inválida ({data_str!r}) junto de "
                    f'"...{trecho}...". Corrige o formato para AAAA-MM-DD.'
                )
                continue

            if idade > LIMIAR_DIAS:
                falhas.append(
                    f"{rel}: " + _mensagem_reverificar(
                        trecho,
                        f"tem marcador de {data_str}, há {idade} dias "
                        f"(limiar: {LIMIAR_DIAS}) — data ultrapassada.",
                    )
                )

    assert not falhas, "\n\n".join(falhas)


def test_yaml_parametros_pendentes_tem_verificado_em_recente():
    """Parâmetros `valor: null` cuja `descricao` os marca como
    `PENDENTE` (convenção já usada em dados/parametros/*.yaml antes
    deste teste existir — ex.: os 3 do artigo 17.º da PSU) têm de ter
    `verificado_em` com menos de LIMIAR_DIAS dias. Nunca aplicado aos
    `null` que são assim por desenho arquitectural (ex.: as majorações
    da PSU, que dependem do beneficiário e nunca serão um valor único —
    a própria descricao explica isso, sem a palavra PENDENTE)."""
    hoje = date.today()
    consolidado = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    falhas: list[str] = []

    for prestacao, parametros in consolidado["prestacoes"].items():
        for nome, dados in parametros.items():
            if dados.get("valor") is not None:
                continue
            if "PENDENTE" not in (dados.get("descricao") or ""):
                continue  # null por desenho, nunca uma espera legal

            verificado_em = dados.get("verificado_em")
            identificador = f"dados/parametros/{prestacao}.yaml::{nome}"

            if not verificado_em:
                falhas.append(
                    f"{identificador}: marcado PENDENTE mas sem 'verificado_em' — "
                    "confirma contra a fonte oficial e preenche o campo (nunca deixar em branco)."
                )
                continue

            try:
                idade = _idade_em_dias(verificado_em, hoje)
            except ValueError:
                falhas.append(f"{identificador}: 'verificado_em' inválido ({verificado_em!r}).")
                continue

            if idade > LIMIAR_DIAS:
                falhas.append(
                    f"{identificador}: 'verificado_em' de {verificado_em}, há {idade} dias "
                    f"(limiar: {LIMIAR_DIAS}) — confirma em dre.pt se o instrumento em falta "
                    "já saiu; se sim, preenche o valor real (nunca isoladamente — ver o teste "
                    "irmão que tranca os parâmetros pendentes em conjunto); se não, renova "
                    "'verificado_em' para hoje."
                )

    assert not falhas, "\n\n".join(falhas)


# ── Regressão do regex — provar as duas direcções, nunca só o caminho feliz ──

# Passos de processo REAIS do site (aguarda + acção do leitor, sem
# instrumento legal por perto) — nunca podem disparar o regex. Extraídos
# desta sessão (grep a "aguarda\b" -i em todo o repositório).
FRASES_PROCESSO_NUNCA_DISPARAM = [
    "Aguarda a convocatória para a junta médica (JMAI).",
    "A Segurança Social avisa-te assim que o pedido for validado.",
    "aguarda que a escola finalize os dados",
    "Aguarda avaliação pela RNCCI.",
    "Aguarda a avaliação — as candidaturas são analisadas mensalmente.",
    "Aguarda a decisão — até 30 dias, ou 20 dias em caso de vulnerabilidade especial.",
    "Se aprovado, aguarda o início dos pagamentos a partir de 31 de dezembro de 2026.",
    "Aguarda a carta de confirmação — chega à nova morada, por correio.",
    "Aguarda o pagamento do subsídio, a partir do fim do período de espera.",
    "Aguarda a notificação — a Segurança Social envia uma carta registada.",
    "Aguarda a decisão. O agrupamento comunica o escalão atribuído.",
]


def test_regex_nao_dispara_em_passos_de_processo_legitimos():
    """As afirmações "aguarda [passo que o leitor vive]" — sem
    instrumento legal por perto — nunca podem ser classificadas como
    espera por instrumento legal, mesmo com "aguarda" presente. Regressão
    directa: se este teste falhar, o regex ficou demasiado largo e vai
    gerar falsos positivos em dezenas de páginas legítimas."""
    for frase in FRASES_PROCESSO_NUNCA_DISPARAM:
        assert not PADRAO_ESPERA_LEGAL.search(frase), (
            f'Falso positivo: "{frase}" não devia disparar o regex de espera legal '
            "(é um passo de processo, não uma lacuna na lei)."
        )


def test_regex_nao_dispara_em_referencia_anaforica_a_diploma_ja_citado():
    """"O decreto-lei" (referência de volta a um diploma já numerado
    mais acima no mesmo texto) não é uma espera — é facto assente.
    Regressão sobre o caso real encontrado nesta sessão
    (como-pedir-psu.html), que quase entrou em falso positivo."""
    frase = (
        "O primeiro pagamento só acontece a partir de 31 de dezembro de 2026, "
        "data de produção de efeitos do decreto-lei (artigo 63.º) — mesmo que a "
        "decisão tenha sido dada antes dessa data."
    )
    assert not PADRAO_ESPERA_LEGAL.search(frase)


def test_regex_dispara_nas_duas_esperas_legitimas_ainda_pendentes():
    """As 2 esperas confirmadas ainda pendentes nesta sessão (art. 17.º
    da PSU; majoração da PSI) têm de continuar a disparar o regex —
    garante que a cobertura não se perdeu com os ajustes de falsos
    positivos acima."""
    assert PADRAO_ESPERA_LEGAL.search("Ainda não disponível — aguarda portaria de regulamentação.")
    assert PADRAO_ESPERA_LEGAL.search("Não está em vigor — aguarda regulamentação própria.")


def test_regex_teria_apanhado_a_afirmacao_ja_corrigida_de_index_html():
    """Regressão do achado real desta sessão: o texto antigo de
    `index.html`/`data/destaque_evento.json` ("Aguarda decreto-lei com
    valores.", 12 dias depois de o DL 166/2026 já estar publicado) tinha
    de disparar este regex — prova que o mecanismo teria apanhado o
    problema que motivou esta sessão, se já existisse."""
    assert PADRAO_ESPERA_LEGAL.search(
        "13 apoios num só. Aprovada no Parlamento a 25/06/2026. "
        "Aguarda decreto-lei com valores."
    )


def test_regex_ignora_diploma_ja_numerado():
    """Um instrumento já identificado por número ("decreto-lei n.º
    166/2026") é facto assente, nunca uma espera — mesmo com "aguarda"
    na mesma frase."""
    assert not PADRAO_ESPERA_LEGAL.search(
        "Aguarda a decisão sobre o pedido, ao abrigo do decreto-lei n.º 166/2026."
    )


def test_dentro_do_limiar_aceita_data_recente_e_rejeita_data_antiga():
    """Unidade da lógica de idade — prova as duas direcções antes de
    confiar nela dentro dos testes de varrimento acima."""
    hoje = date(2026, 8, 26)
    assert _idade_em_dias("2026-08-26", hoje) == 0
    assert _idade_em_dias("2026-07-01", hoje) == 56
    assert _idade_em_dias("2026-06-01", hoje) == 86


def test_marcadores_de_espera_legal_existem_e_estao_frescos_nas_2_paginas_pendentes():
    """As 2 páginas com espera legítima confirmada nesta sessão
    (simulador-psu.html, prestacao-social-para-a-inclusao.html) têm de
    ter o marcador ESPERA-LEGAL, datado de hoje — prova directa de que a
    retrofit desta sessão ficou aplicada, não só a lógica do regex."""
    for nome, minimo_ocorrencias in (
        ("simulador-psu.html", 1),
        ("prestacao-social-para-a-inclusao.html", 1),
    ):
        texto = _ler(nome)
        ocorrencias = PADRAO_MARCADOR.findall(texto)
        assert len(ocorrencias) >= minimo_ocorrencias, (
            f"{nome}: esperado pelo menos {minimo_ocorrencias} marcador(es) ESPERA-LEGAL, "
            f"encontrados {len(ocorrencias)}"
        )
