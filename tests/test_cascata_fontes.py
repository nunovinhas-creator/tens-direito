"""
Testes da Camada 2. Cobrem o cenario real visto em producao: IEFP bloqueado
por reCAPTCHA -> cascata cai para fonte legislativa -> se essa tambem falhar,
cai para o valor congelado. Nunca SEM_VALOR se houver congelado definido.

Corre standalone: python test_cascata_fontes.py
"""
from datetime import date

from classificador_resposta import FonteConfig
from cascata_fontes import (
    FontePassoConfig, RubricaConfig, ResolucaoRubrica, ResultadoTipo,
    TipoFonte, ValorCongelado, resolver_rubrica,
)

PAGINA_REAL = "<html><head><title>Pagina</title></head><body>" + \
    ("texto de conteudo real e extenso para passar o threshold. " * 20) + \
    "</body></html>"

RECAPTCHA = '<html><head><title>IEFP</title></head><body>' + \
    'g-recaptcha widget de verificacao humana. ' * 30 + '</body></html>'

LOGIN = '<html><head><title>Iniciar sessao</title></head><body>curto</body></html>'


def extrator_valor_x(corpo: str):
    if "VALOR=419.22" in corpo:
        return "419.22"
    return None


def extrator_sempre_none(corpo: str):
    return None


def fetcher_fixo(respostas: dict):
    """Devolve um fetcher que mapeia url -> (status, corpo, url_final) fixo."""
    def f(url):
        return respostas[url]
    return f


falhas = []


def check(nome, condicao, detalhe=""):
    estado = "PASS" if condicao else "FALHA"
    if not condicao:
        falhas.append(nome)
    print(f"[{estado}] {nome}{(' — ' + detalhe) if detalhe else ''}")


IEFP = FonteConfig(nome="IEFP subsidio desemprego", min_chars_uteis=500)
DRE = FonteConfig(nome="DRE - Portaria subsidio", min_chars_uteis=500)

# --- Caso 1: fonte primaria (legislativa) OK logo a primeira -> RESOLVIDO via legislativa ---
rubrica = RubricaConfig(
    nome="subsidio_desemprego_max",
    cascata=(
        FontePassoConfig(TipoFonte.LEGISLATIVA, DRE, extrator_valor_x, url="dre"),
        FontePassoConfig(TipoFonte.SERVICO, IEFP, extrator_valor_x, url="iefp"),
    ),
    congelado=ValorCongelado(valor="400.00", data_verificacao=date(2026, 1, 1)),
)
fetcher = fetcher_fixo({
    "dre": (200, PAGINA_REAL.replace("texto de conteudo", "VALOR=419.22 texto de conteudo"), "dre"),
    "iefp": (200, PAGINA_REAL, "iefp"),
})
r = resolver_rubrica(rubrica, fetcher)
check("legislativa OK -> RESOLVIDO via legislativa", r.resultado == ResultadoTipo.RESOLVIDO and r.tipo_fonte_usada == TipoFonte.LEGISLATIVA, str(r))
check("valor correto extraido", r.valor == "419.22")

# --- Caso 2: legislativa falha extracao (estrutura mudou) -> cai para servico ---
fetcher2 = fetcher_fixo({
    "dre": (200, PAGINA_REAL, "dre"),  # OK mas sem o valor (extrator devolve None)
    "iefp": (200, PAGINA_REAL.replace("texto de conteudo", "VALOR=419.22 texto de conteudo"), "iefp"),
})
r2 = resolver_rubrica(rubrica, fetcher2)
check("legislativa sem valor -> cai para servico", r2.resultado == ResultadoTipo.RESOLVIDO and r2.fonte_usada == "IEFP subsidio desemprego", str(r2))

# --- Caso 3: cenario real — IEFP bloqueado por reCAPTCHA, legislativa tambem falha -> CONGELADO ---
fetcher3 = fetcher_fixo({
    "dre": (403, "", "dre"),
    "iefp": (200, RECAPTCHA, "iefp"),
})
r3 = resolver_rubrica(rubrica, fetcher3)
check("DRE 403 + IEFP recaptcha -> CONGELADO", r3.resultado == ResultadoTipo.CONGELADO, str(r3))
check("valor congelado correto", r3.valor == "400.00")
check("nunca publica valor de fonte bloqueada", all(t[1].value != "MUDOU" for t in r3.tentativas))

# --- Caso 4: todas as fontes falham e NAO ha congelado definido -> SEM_VALOR (nunca devia acontecer em producao) ---
rubrica_sem_congelado = RubricaConfig(
    nome="teste_sem_rede",
    cascata=(FontePassoConfig(TipoFonte.SERVICO, IEFP, extrator_sempre_none, url="iefp"),),
    congelado=None,
)
fetcher4 = fetcher_fixo({"iefp": (200, RECAPTCHA, "iefp")})
r4 = resolver_rubrica(rubrica_sem_congelado, fetcher4)
check("sem congelado e tudo falha -> SEM_VALOR", r4.resultado == ResultadoTipo.SEM_VALOR)
check("SEM_VALOR -> nao publicavel", r4.publicavel is False)
check("CONGELADO -> publicavel", r3.publicavel is True)
check("RESOLVIDO -> publicavel", r.publicavel is True)

# --- Caso 5: excecao de rede no fetch tambem e tratada como bloqueio, nao crash ---
def fetcher_excecao(url):
    raise ConnectionError("timeout")

r5 = resolver_rubrica(rubrica, fetcher_excecao)
check("excecao de rede -> nao crasha, cai para congelado", r5.resultado == ResultadoTipo.CONGELADO)
check("excecao registada nas tentativas", any("excecao_fetch" in str(m) for _, _, m in r5.tentativas))

print("\n" + ("TODOS OS TESTES PASSARAM ✓" if not falhas else f"FALHAS: {falhas}"))
raise SystemExit(1 if falhas else 0)
