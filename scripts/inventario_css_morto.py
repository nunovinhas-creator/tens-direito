#!/usr/bin/env python3
"""Inventário e limpeza de CSS morto em todo o site — CSS externo + inline.

Generaliza `limpar_css_morto_nav.py` (que só cobria a família de tokens da
nav antiga) para TODO o CSS do repositório: os 6 ficheiros de
`assets/css/*.css` e o `<style>` inline de cada uma das páginas servidas
(raiz + `p/` + `documentos/`).

Modos:
  (omissão)  inventário — tabela fonte/seletor/decisão + resumo, sem tocar
             em nenhum ficheiro
  --write    remove as regras comprovadamente MORTO-CONFIRMADO
  --check    exit 2 se ainda existir alguma regra removível (CI/idempotência)
  --csv PATH grava o inventário completo (as 3 colunas) em CSV

Três camadas de uso verificadas para cada classe/id exigido por um seletor,
TODAS obrigatórias antes de declarar morto:
  1. HTML estático das páginas servidas (class=/id= reais)
  2. JavaScript (assets/js/*.js, scripts/pesquisa.js, <script> inline de
     cada página) — mutações reais (classList.add/toggle, class=/className=
     atribuído por string) E prefixos dinâmicos de template literals
     (`` `prefixo-${x}` ``)
  3. Scripts Python que escrevem HTML (scripts/*.py) — o token aparece como
     string literal no ficheiro, OU como prefixo dinâmico de f-string
     (`class="cat-{item.categoria}"` → prefixo "cat-")

Três categorias:
  USADO             — token confirmado numa das 3 camadas (estático, JS ou
                       Python, literal — nunca prova de dúvida)
  AMBIGUO           — token só explicável por um prefixo dinâmico
                       (JS/Python) — plausível mas não provado; NUNCA removido
  MORTO-CONFIRMADO  — token ausente das 3 camadas, incluindo prefixos
                       dinâmicos

Regra de remoção (idêntica em espírito a `limpar_css_morto_nav.py`): uma
regra só é removível se TODOS os seus seletores forem MORTO-CONFIRMADO. Um
seletor sem classes/ids exigidos (tag/pseudo/atributo puro, ex. `body`,
`:root`, `[data-mes]`, `a:hover`) é sempre tratado como USADO — nunca há
prova suficiente para o remover.

Estado inesperado (parse CSS falhado, chaveta desemparelhada, remoção que
não converge) => exit != 0. Nenhum erro pode parecer sucesso.
"""
from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import List, Optional, Set, Tuple

RAIZ = Path(__file__).resolve().parent.parent

EXIT_OK = 0
EXIT_ERRO_USO = 1
EXIT_ESTADO_INESPERADO = 2


class EstadoInesperado(Exception):
    pass


# ---------------------------------------------------------------------------
# Páginas servidas e ficheiros CSS externos
# ---------------------------------------------------------------------------


def paginas_servidas() -> List[Path]:
    paginas = (
        sorted(RAIZ.glob("*.html"))
        + sorted((RAIZ / "p").glob("*.html"))
        + sorted((RAIZ / "documentos").glob("*.html"))
    )
    if not paginas:
        raise EstadoInesperado("nenhuma página HTML encontrada na raiz do repositório")
    return paginas


def css_externos() -> List[Path]:
    ficheiros = sorted((RAIZ / "assets" / "css").glob("*.css"))
    if not ficheiros:
        raise EstadoInesperado("nenhum ficheiro CSS externo encontrado em assets/css/")
    return ficheiros


# ---------------------------------------------------------------------------
# Recolha de tokens HTML (classes/ids reais + scripts inline)
# ---------------------------------------------------------------------------


class _ColectorTokens(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.classes: Set[str] = set()
        self.ids: Set[str] = set()
        self.scripts_inline: List[str] = []
        self._dentro_script = False
        self._buffer_script: List[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        for nome, valor in attrs:
            if valor is None:
                continue
            if nome == "class":
                self.classes.update(valor.split())
            elif nome == "id":
                self.ids.add(valor)
        if tag == "script" and not any(n == "src" for n, _ in attrs):
            self._dentro_script = True
            self._buffer_script = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._dentro_script:
            self._dentro_script = False
            self.scripts_inline.append("".join(self._buffer_script))

    def handle_data(self, data: str) -> None:
        if self._dentro_script:
            self._buffer_script.append(data)


@dataclass
class Pagina:
    caminho: Path
    html: str
    classes: Set[str]
    ids: Set[str]
    scripts_inline: List[str]


def carregar_pagina(caminho: Path) -> Pagina:
    html = caminho.read_text(encoding="utf-8")
    colector = _ColectorTokens()
    colector.feed(html)
    return Pagina(caminho, html, colector.classes, colector.ids, colector.scripts_inline)


# ---------------------------------------------------------------------------
# Tokens que JS/Python conseguem ADICIONAR em runtime (mutações + prefixos
# dinâmicos de template literals / f-strings)
# ---------------------------------------------------------------------------

_RE_JS_CLASSLIST_MUT = re.compile(r"classList\s*\.\s*(?:add|toggle)\s*\(\s*['\"]([A-Za-z0-9_-]+)['\"]")
_RE_JS_CLASS_ATTR = re.compile(r"class\s*=\s*\\?[\"']([^\"'\\<>{}]+)")
_RE_JS_CLASSNAME = re.compile(r"\.className\s*=\s*[\"']([^\"']+)[\"']")

# prefixo dinâmico: qualquer atributo class="..." (aspas simples/duplas) cujo
# valor contenha uma interpolação ({var} de f-string Python, ou ${var} de
# template literal JS) — extrai o "pedaço" de classe antes/depois da
# interpolação (delimitado por espaço), nunca a frase toda.
_RE_CLASS_ATTR_INTERP = re.compile(
    r'class\s*=\s*["\']([^"\']*\{[^"\']*\}[^"\']*)["\']'
)


@dataclass
class PrefixoDinamico:
    prefixo: str
    sufixo: str
    origem: str


def _extrair_prefixos_dinamicos(texto: str, origem: str) -> List[PrefixoDinamico]:
    prefixos: List[PrefixoDinamico] = []
    for m in _RE_CLASS_ATTR_INTERP.finditer(texto):
        valor = m.group(1)
        # cada "palavra" do valor de class= é avaliada isoladamente
        for palavra in valor.split():
            if "{" not in palavra:
                continue
            antes, resto = palavra.split("{", 1)
            depois = resto.split("}", 1)[1] if "}" in resto else ""
            prefixos.append(PrefixoDinamico(antes, depois, origem))
    return prefixos


def tokens_que_js_pode_adicionar(paginas: List[Pagina]) -> Set[str]:
    fontes: List[Tuple[str, str]] = []
    for pagina in paginas:
        for script in pagina.scripts_inline:
            fontes.append((f"inline:{pagina.caminho.relative_to(RAIZ)}", script))
    for js in sorted((RAIZ / "assets" / "js").glob("*.js")) + [RAIZ / "scripts" / "pesquisa.js"]:
        if js.exists():
            fontes.append((str(js.relative_to(RAIZ)), js.read_text(encoding="utf-8")))
    tokens: Set[str] = set()
    for _origem, fonte in fontes:
        tokens.update(_RE_JS_CLASSLIST_MUT.findall(fonte))
        for grupo in _RE_JS_CLASS_ATTR.findall(fonte):
            tokens.update(grupo.split())
        for grupo in _RE_JS_CLASSNAME.findall(fonte):
            tokens.update(grupo.split())
    return tokens


def tokens_literais_js(paginas: List[Pagina]) -> Set[str]:
    """Qualquer identificador-tipo-classe presente no texto de todo o JS do
    site (ficheiros + <script> inline de cada página).

    Mesma permissividade deliberada de `tokens_literais_python()`: uma
    classe construída por concatenação de string ou guardada num objecto
    de dados (`cor: 'escalo-1'`, `tagCor: 'verde'`, `className:
    "gerador-form-group"`) nunca aparece como `classList.add('literal')`
    nem como `class="literal"` — só como uma string solta algures no
    ficheiro. Procurar o token no texto inteiro é a única forma fiável de
    nunca marcar isto como morto por engano.
    """
    tokens: Set[str] = set()
    for pagina in paginas:
        for script in pagina.scripts_inline:
            tokens.update(_RE_TOKEN_CSS.findall(script))
    for js in sorted((RAIZ / "assets" / "js").glob("*.js")) + [RAIZ / "scripts" / "pesquisa.js"]:
        if js.exists():
            tokens.update(_RE_TOKEN_CSS.findall(js.read_text(encoding="utf-8")))
    return tokens


def prefixos_dinamicos_js(paginas: List[Pagina]) -> List[PrefixoDinamico]:
    prefixos: List[PrefixoDinamico] = []
    for pagina in paginas:
        for script in pagina.scripts_inline:
            prefixos.extend(_extrair_prefixos_dinamicos(script, f"JS inline:{pagina.caminho.relative_to(RAIZ)}"))
    for js in sorted((RAIZ / "assets" / "js").glob("*.js")) + [RAIZ / "scripts" / "pesquisa.js"]:
        if js.exists():
            prefixos.extend(_extrair_prefixos_dinamicos(js.read_text(encoding="utf-8"), str(js.relative_to(RAIZ))))
    return prefixos


# ---------------------------------------------------------------------------
# Camada Python: tokens literais + prefixos dinâmicos de f-strings
# ---------------------------------------------------------------------------

_RE_TOKEN_CSS = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")


def tokens_literais_python() -> Set[str]:
    """Qualquer identificador-tipo-classe presente no texto de scripts/*.py.

    Deliberadamente permissivo (conta comentários e strings não-HTML
    também) — o objectivo é nunca marcar como morto algo que um gerador
    Python possa escrever; falsos positivos aqui só significam "fica",
    nunca "remove-se por engano".
    """
    tokens: Set[str] = set()
    for py in sorted((RAIZ / "scripts").glob("*.py")):
        texto = py.read_text(encoding="utf-8")
        tokens.update(_RE_TOKEN_CSS.findall(texto))
    return tokens


def prefixos_dinamicos_python() -> List[PrefixoDinamico]:
    prefixos: List[PrefixoDinamico] = []
    for py in sorted((RAIZ / "scripts").glob("*.py")):
        texto = py.read_text(encoding="utf-8")
        prefixos.extend(_extrair_prefixos_dinamicos(texto, str(py.relative_to(RAIZ))))
    return prefixos


# ---------------------------------------------------------------------------
# Parse de CSS em regras individuais (com @media aninhado) — texto puro ou
# dentro de <style> em HTML
# ---------------------------------------------------------------------------

_RE_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_RE_COMENTARIO_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass
class RegraCSS:
    seletor: str
    inicio: int
    fim: int
    media: Optional[str]


@dataclass
class BlocoMedia:
    header: str
    inicio: int
    fim: int
    corpo_inicio: int
    corpo_fim: int
    regras: List[RegraCSS] = field(default_factory=list)


def _sem_comentarios(css: str) -> str:
    return _RE_COMENTARIO_CSS.sub(lambda m: " " * len(m.group(0)), css)


def _fechar_chaveta(css: str, abre: int, fim: int) -> int:
    profundidade = 0
    for i in range(abre, fim):
        if css[i] == "{":
            profundidade += 1
        elif css[i] == "}":
            profundidade -= 1
            if profundidade == 0:
                return i
    raise EstadoInesperado(f"chaveta desemparelhada no CSS perto de: {css[abre:abre+80]!r}")


def _parse_css(css: str, base: int, regras: List[RegraCSS], medias: List[BlocoMedia],
               media_actual: Optional[str], offset: int, fim: int) -> None:
    i = offset
    while i < fim:
        ch = css[i]
        if ch.isspace():
            i += 1
            continue
        j = css.find("{", i)
        if j == -1 or j >= fim:
            resto = css[i:fim].strip()
            if resto:
                raise EstadoInesperado(f"CSS residual sem bloco: {resto[:80]!r}")
            return
        cabecalho = css[i:j].strip()
        k = _fechar_chaveta(css, j, fim)
        if cabecalho.startswith("@media"):
            bloco = BlocoMedia(cabecalho, base + i, base + k + 1, base + j + 1, base + k)
            n_antes = len(regras)
            _parse_css(css, base, regras, medias, media_actual=cabecalho, offset=j + 1, fim=k)
            bloco.regras = regras[n_antes:]
            medias.append(bloco)
        elif cabecalho.startswith("@keyframes") or cabecalho.startswith("@font-face") or cabecalho.startswith("@supports"):
            pass  # opaco — nunca tocado
        else:
            regras.append(RegraCSS(cabecalho, base + i, base + k + 1, media_actual))
        i = k + 1


def extrair_regras_de_html(html: str) -> Tuple[List[RegraCSS], List[BlocoMedia]]:
    regras: List[RegraCSS] = []
    medias: List[BlocoMedia] = []
    for m_style in _RE_STYLE.finditer(html):
        base = m_style.start(1)
        css = _sem_comentarios(m_style.group(1))
        _parse_css(css, base, regras, medias, media_actual=None, offset=0, fim=len(css))
    return regras, medias


def extrair_regras_de_css_puro(css_texto: str) -> Tuple[List[RegraCSS], List[BlocoMedia]]:
    regras: List[RegraCSS] = []
    medias: List[BlocoMedia] = []
    css = _sem_comentarios(css_texto)
    _parse_css(css, 0, regras, medias, media_actual=None, offset=0, fim=len(css))
    return regras, medias


# ---------------------------------------------------------------------------
# Análise de seletores
# ---------------------------------------------------------------------------

_RE_NOT = re.compile(r":not\([^)]*\)")
_RE_PSEUDO = re.compile(r"::?[a-zA-Z-]+(\([^)]*\))?")
_RE_ATRIBUTO = re.compile(r"\[[^\]]*\]")
_RE_CLASSE = re.compile(r"\.(-?[A-Za-z_][A-Za-z0-9_-]*)")
_RE_ID = re.compile(r"#(-?[A-Za-z_][A-Za-z0-9_-]*)")


def tokens_exigidos(seletor: str) -> Tuple[Set[str], Set[str]]:
    limpo = _RE_NOT.sub("", seletor)
    limpo = _RE_ATRIBUTO.sub("", limpo)
    limpo = _RE_PSEUDO.sub("", limpo)
    return set(_RE_CLASSE.findall(limpo)), set(_RE_ID.findall(limpo))


def dividir_seletores(lista: str) -> List[str]:
    return [s.strip() for s in lista.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Fonte CSS unificada (externo ou inline) + análise global
# ---------------------------------------------------------------------------


@dataclass
class FonteCSS:
    tipo: str  # "externo" | "inline"
    caminho: Path
    texto: str  # css puro (externo) ou html completo (inline)
    regras: List[RegraCSS]
    medias: List[BlocoMedia]


def carregar_fontes_css(paginas: List[Pagina]) -> List[FonteCSS]:
    fontes: List[FonteCSS] = []
    for css_path in css_externos():
        texto = css_path.read_text(encoding="utf-8")
        regras, medias = extrair_regras_de_css_puro(texto)
        fontes.append(FonteCSS("externo", css_path, texto, regras, medias))
    for p in paginas:
        regras, medias = extrair_regras_de_html(p.html)
        fontes.append(FonteCSS("inline", p.caminho, p.html, regras, medias))
    return fontes


@dataclass
class AnaliseSeletor:
    fonte: Path
    tipo_fonte: str
    seletor: str
    media: Optional[str]
    decisao: str  # USADO | AMBIGUO | MORTO-CONFIRMADO
    justificacao: str


def _prefixo_bate(token: str, prefixos: List[PrefixoDinamico]) -> Optional[PrefixoDinamico]:
    for pd in prefixos:
        if token.startswith(pd.prefixo) and token.endswith(pd.sufixo) and len(token) > len(pd.prefixo) + len(pd.sufixo):
            return pd
        if not pd.sufixo and pd.prefixo and token == pd.prefixo.rstrip("-"):
            continue
    return None


def classificar_token(
    token: str,
    e_id: bool,
    classes_estaticas: Set[str],
    ids_estaticos: Set[str],
    tokens_js_literal: Set[str],
    tokens_py_literal: Set[str],
    prefixos: List[PrefixoDinamico],
) -> Tuple[str, str]:
    if e_id:
        if token in ids_estaticos:
            return "USADO", "id presente em HTML real"
        return "MORTO-CONFIRMADO", "id ausente de todas as páginas servidas"
    if token in classes_estaticas:
        return "USADO", "classe presente em HTML real"
    if token in tokens_js_literal:
        return "USADO", "token literal presente em JS (mutação directa ou string de dados)"
    if token in tokens_py_literal:
        return "USADO", "token literal presente em scripts/*.py"
    pd = _prefixo_bate(token, prefixos)
    if pd is not None:
        return "AMBIGUO", f"corresponde a prefixo dinâmico {pd.prefixo!r}+{pd.sufixo!r} de {pd.origem}"
    return "MORTO-CONFIRMADO", "ausente de HTML estático, JS literal, Python literal e prefixos dinâmicos"


@dataclass
class RegraAnalisada:
    fonte: FonteCSS
    regra: RegraCSS
    seletores_analise: List[AnaliseSeletor]
    removivel: bool


def analisar_tudo(paginas: List[Pagina], fontes: List[FonteCSS]):
    classes_estaticas: Set[str] = set()
    ids_estaticos: Set[str] = set()
    for p in paginas:
        classes_estaticas.update(p.classes)
        ids_estaticos.update(p.ids)

    tokens_js_literal = tokens_que_js_pode_adicionar(paginas) | tokens_literais_js(paginas)
    tokens_py_literal = tokens_literais_python()
    prefixos = prefixos_dinamicos_js(paginas) + prefixos_dinamicos_python()

    regras_analisadas: List[RegraAnalisada] = []

    for fonte in fontes:
        for regra in fonte.regras:
            seletores = dividir_seletores(regra.seletor)
            analises_regra: List[AnaliseSeletor] = []
            for sel in seletores:
                classes, ids = tokens_exigidos(sel)
                if not classes and not ids:
                    analises_regra.append(AnaliseSeletor(
                        fonte.caminho.relative_to(RAIZ), fonte.tipo, sel, regra.media,
                        "USADO", "seletor sem classe/id exigido (tag/pseudo/atributo) — nunca provável morto",
                    ))
                    continue
                decisoes = []
                justs = []
                for c in classes:
                    d, j = classificar_token(c, False, classes_estaticas, ids_estaticos, tokens_js_literal, tokens_py_literal, prefixos)
                    decisoes.append(d)
                    justs.append(f".{c}: {j}")
                for i in ids:
                    d, j = classificar_token(i, True, classes_estaticas, ids_estaticos, tokens_js_literal, tokens_py_literal, prefixos)
                    decisoes.append(d)
                    justs.append(f"#{i}: {j}")
                if "MORTO-CONFIRMADO" in decisoes:
                    decisao_final = "MORTO-CONFIRMADO"
                elif "AMBIGUO" in decisoes:
                    decisao_final = "AMBIGUO"
                else:
                    decisao_final = "USADO"
                analises_regra.append(AnaliseSeletor(
                    fonte.caminho.relative_to(RAIZ), fonte.tipo, sel, regra.media,
                    decisao_final, "; ".join(justs),
                ))
            removivel = all(a.decisao == "MORTO-CONFIRMADO" for a in analises_regra)
            regras_analisadas.append(RegraAnalisada(fonte, regra, analises_regra, removivel))

    return regras_analisadas


# ---------------------------------------------------------------------------
# Remoção
# ---------------------------------------------------------------------------


def _colapsar_linhas_em_branco(texto: str) -> str:
    """Nunca deixa mais do que uma linha em branco seguida."""
    return re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", texto)


def remover_de_texto(texto: str, regras_removiveis: List[RegraCSS], medias: List[BlocoMedia], tipo_fonte: str) -> Tuple[str, int]:
    """Remove as regras indicadas. `tipo_fonte` distingue CSS externo (o
    texto inteiro é CSS — colapso de linhas em branco aplicado ao ficheiro
    todo) de HTML inline (colapso restrito ao interior de cada <style>,
    para nunca tocar em whitespace do corpo da página fora do CSS)."""
    if not regras_removiveis:
        return texto, 0
    spans_regras = {(r.inicio, r.fim) for r in regras_removiveis}
    spans: List[Tuple[int, int]] = list(spans_regras)
    for bloco in medias:
        if bloco.regras and all((r.inicio, r.fim) in spans_regras for r in bloco.regras):
            spans = [s for s in spans if not (s[0] >= bloco.corpo_inicio and s[1] <= bloco.fim)]
            spans.append((bloco.inicio, bloco.fim))
    spans.sort(reverse=True)
    resultado = texto
    for inicio, fim in spans:
        fim_real = fim
        while fim_real < len(resultado) and resultado[fim_real] in " \t":
            fim_real += 1
        if fim_real < len(resultado) and resultado[fim_real] == "\n":
            fim_real += 1
        inicio_real = inicio
        while inicio_real > 0 and resultado[inicio_real - 1] in " \t":
            inicio_real -= 1
        resultado = resultado[:inicio_real] + resultado[fim_real:]
    if tipo_fonte == "externo":
        resultado = _colapsar_linhas_em_branco(resultado)
    else:
        resultado = _RE_STYLE.sub(
            lambda m: m.group(0).replace(m.group(1), _colapsar_linhas_em_branco(m.group(1)))
            if re.search(r"\n[ \t]*\n[ \t]*\n", m.group(1)) else m.group(0),
            resultado,
        )
    return resultado, len(regras_removiveis)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    escrever = "--write" in argv
    verificar = "--check" in argv
    csv_path = None
    if "--csv" in argv:
        idx = argv.index("--csv")
        if idx + 1 >= len(argv):
            print("ERRO: --csv exige um caminho", file=sys.stderr)
            return EXIT_ERRO_USO
        csv_path = Path(argv[idx + 1])
    if escrever and verificar:
        print("ERRO: --write e --check são mutuamente exclusivos", file=sys.stderr)
        return EXIT_ERRO_USO

    paginas = [carregar_pagina(c) for c in paginas_servidas()]
    fontes = carregar_fontes_css(paginas)
    regras_analisadas = analisar_tudo(paginas, fontes)

    todas_analises = [a for r in regras_analisadas for a in r.seletores_analise]
    mortas = [a for a in todas_analises if a.decisao == "MORTO-CONFIRMADO"]
    ambiguas = [a for a in todas_analises if a.decisao == "AMBIGUO"]
    usadas = [a for a in todas_analises if a.decisao == "USADO"]

    regras_removiveis = [r for r in regras_analisadas if r.removivel]

    print(f"Fontes CSS: {len(fontes)} ({sum(1 for f in fontes if f.tipo=='externo')} externas, "
          f"{sum(1 for f in fontes if f.tipo=='inline')} inline)")
    print(f"Regras totais: {len(regras_analisadas)} · seletores: {len(todas_analises)}")
    print(f"  USADO: {len(usadas)}  ·  AMBIGUO: {len(ambiguas)}  ·  MORTO-CONFIRMADO: {len(mortas)}")
    print(f"Regras 100% mortas (removíveis): {len(regras_removiveis)}")
    print()

    if ambiguas:
        print("=== AMBÍGUOS (nunca removidos nesta sessão) ===")
        vistos = set()
        for a in sorted(ambiguas, key=lambda x: (str(x.fonte), x.seletor)):
            chave = (str(a.fonte), a.seletor)
            if chave in vistos:
                continue
            vistos.add(chave)
            print(f"  {a.fonte}  {a.seletor}  — {a.justificacao}")
        print()

    if mortas:
        print("=== Seletores MORTO-CONFIRMADO (por fonte) ===")
        vistos = set()
        for a in sorted(mortas, key=lambda x: (str(x.fonte), x.seletor)):
            chave = (str(a.fonte), a.seletor)
            if chave in vistos:
                continue
            vistos.add(chave)
            print(f"  {a.fonte}  {a.seletor}  — {a.justificacao}")
        print()

    if csv_path:
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["fonte", "tipo", "seletor", "media", "decisao", "justificacao"])
            for a in todas_analises:
                w.writerow([str(a.fonte), a.tipo_fonte, a.seletor, a.media or "", a.decisao, a.justificacao])
        print(f"CSV escrito em {csv_path} ({len(todas_analises)} linhas)")

    if verificar:
        if regras_removiveis:
            print(f"CHECK FALHOU: {len(regras_removiveis)} regra(s) morta(s) ainda presente(s).", file=sys.stderr)
            return EXIT_ESTADO_INESPERADO
        print("CHECK OK: nenhuma regra morta removível presente.")
        return EXIT_OK

    if not escrever:
        print("(dry-run — usar --write para aplicar; --check para verificação de CI)")
        return EXIT_OK

    # --- escrita ---------------------------------------------------------
    total_regras = 0
    total_bytes = 0
    for fonte in fontes:
        regras_desta_fonte = [r for r in regras_removiveis if r.fonte is fonte]
        if not regras_desta_fonte:
            continue
        regras_css = [r.regra for r in regras_desta_fonte]
        novo, n = remover_de_texto(fonte.texto, regras_css, fonte.medias, fonte.tipo)
        if n and novo != fonte.texto:
            bytes_removidos = len(fonte.texto.encode("utf-8")) - len(novo.encode("utf-8"))
            fonte.caminho.write_text(novo, encoding="utf-8")
            rel = fonte.caminho.relative_to(RAIZ)
            print(f"  {rel}: {n} regra(s) removida(s), {bytes_removidos} bytes")
            total_regras += n
            total_bytes += bytes_removidos
        elif n:
            raise EstadoInesperado(f"{fonte.caminho}: {n} regras marcadas para remover mas o conteúdo não mudou")

    print(f"\nTotal: {total_regras} regra(s), {total_bytes} bytes removidos")

    # convergência
    paginas2 = [carregar_pagina(c) for c in paginas_servidas()]
    fontes2 = carregar_fontes_css(paginas2)
    regras_analisadas2 = analisar_tudo(paginas2, fontes2)
    restantes = sum(1 for r in regras_analisadas2 if r.removivel)
    if restantes:
        print(f"ERRO: após a escrita restam {restantes} regra(s) removível(is) — remoção não convergiu.", file=sys.stderr)
        return EXIT_ESTADO_INESPERADO
    return EXIT_OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except EstadoInesperado as exc:
        print(f"ESTADO INESPERADO: {exc}", file=sys.stderr)
        sys.exit(EXIT_ESTADO_INESPERADO)
