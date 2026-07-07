#!/usr/bin/env python3
"""Limpeza de CSS morto da navegação antiga nos <style> inline das páginas.

Contexto: a Fase 4 da reorganização de navegação (ver CLAUDE.md, secção
"NAVEGAÇÃO PRINCIPAL") substituiu a nav antiga em todas as páginas, mas as
regras CSS antigas (.mobile-menu, .hamburger, .nav-mobile-sim-label, ...)
ficaram nos <style> de cada página — dívida técnica registada nessa fase.

Modos:
  (omissão)  inventário — tabela ficheiro/seletor/correspondências/decisão,
             sem tocar em nenhum ficheiro
  --write    remove as regras comprovadamente mortas (decisão global)
  --check    exit 2 se ainda existir alguma regra removível (para CI e
             para provar idempotência: depois de --write tem de passar)

Regra de remoção (deliberadamente global, nunca por página): uma regra só é
removida se TODOS os seletores da sua lista exigirem pelo menos um token
(classe/id) que (a) não existe em nenhum elemento de NENHUMA página servida
e (b) nenhum JavaScript do site consegue adicionar (classList.add/toggle,
class= em strings de JS, className=). Se um seletor ainda corresponder a
alguma coisa em qualquer página — mesmo que noutro ficheiro — a regra fica
intocada e é reportada como AMBIGUO. Nunca se remove nada por o nome
"parecer antigo".

Estado inesperado (parse CSS falhado, chavetas desemparelhadas, remoção que
não convergiu) => exit != 0 com mensagem clara — nenhum erro pode parecer
sucesso.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, Set, Tuple

RAIZ = Path(__file__).resolve().parent.parent

# Família de tokens da nav antiga — âmbito da limpeza. Só regras cujos
# seletores exigem um destes tokens são candidatas; todo o resto do CSS
# fica fora do âmbito (mesmo que também esteja morto — é reportado, nunca
# tocado por este script).
TOKENS_NAV_ANTIGA_CLASSES = {
    "mobile-menu",
    "hamburger",
    "nav-mobile-sim-label",
    "nav-mobile-sim-link",
    "nav-link",
}
TOKENS_NAV_ANTIGA_IDS = {"menu-mobile", "menuMobile"}

EXIT_OK = 0
EXIT_ERRO_USO = 1
EXIT_ESTADO_INESPERADO = 2


def paginas_servidas() -> List[Path]:
    """Todas as páginas HTML servidas: raiz + p/ + documentos/ (nunca tests/)."""
    paginas = (
        sorted(RAIZ.glob("*.html"))
        + sorted((RAIZ / "p").glob("*.html"))
        + sorted((RAIZ / "documentos").glob("*.html"))
    )
    if not paginas:
        raise EstadoInesperado("nenhuma página HTML encontrada na raiz do repositório")
    return paginas


class EstadoInesperado(Exception):
    pass


# ---------------------------------------------------------------------------
# Recolha de tokens (classes/ids) dos elementos HTML e do JavaScript
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


_RE_JS_CLASSLIST_MUT = re.compile(r"classList\s*\.\s*(?:add|toggle)\s*\(\s*['\"]([A-Za-z0-9_-]+)['\"]")
_RE_JS_CLASS_ATTR = re.compile(r"class\s*=\s*\\?[\"']([^\"'\\<>]+)")
_RE_JS_CLASSNAME = re.compile(r"\.className\s*=\s*[\"']([^\"']+)[\"']")


def tokens_que_js_pode_adicionar(paginas: List[Pagina]) -> Set[str]:
    """Classes que algum JS do site pode ADICIONAR a elementos em runtime.

    Só mutações contam (classList.add/toggle, class= em strings JS,
    className=). Leituras (querySelector('.x'), classList.remove) nunca
    criam elementos nem classes — não tornam um seletor vivo.
    """
    fontes_js: List[str] = []
    for pagina in paginas:
        fontes_js.extend(pagina.scripts_inline)
    for js in sorted((RAIZ / "assets" / "js").glob("*.js")) + [RAIZ / "scripts" / "pesquisa.js"]:
        if js.exists():
            fontes_js.append(js.read_text(encoding="utf-8"))
    tokens: Set[str] = set()
    for fonte in fontes_js:
        tokens.update(_RE_JS_CLASSLIST_MUT.findall(fonte))
        for grupo in _RE_JS_CLASS_ATTR.findall(fonte):
            tokens.update(grupo.split())
        for grupo in _RE_JS_CLASSNAME.findall(fonte):
            tokens.update(grupo.split())
    return tokens


# ---------------------------------------------------------------------------
# Parse dos blocos <style> em regras individuais (com @media aninhado)
# ---------------------------------------------------------------------------

_RE_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_RE_COMENTARIO_CSS = re.compile(r"/\*.*?\*/", re.DOTALL)


@dataclass
class RegraCSS:
    seletor: str          # texto do seletor tal como está no ficheiro
    inicio: int           # offset do início do seletor, relativo ao documento
    fim: int              # offset a seguir ao '}' que fecha a regra
    media: str | None     # header do @media envolvente, se existir


@dataclass
class BlocoMedia:
    header: str
    inicio: int           # offset do início do header
    fim: int              # offset a seguir ao '}' que fecha o bloco
    corpo_inicio: int     # offset a seguir ao '{'
    corpo_fim: int        # offset do '}' final
    regras: List[RegraCSS] = field(default_factory=list)


def _sem_comentarios(css: str) -> str:
    # substitui comentários por espaços do mesmo comprimento para preservar offsets
    return _RE_COMENTARIO_CSS.sub(lambda m: " " * len(m.group(0)), css)


def extrair_regras(html: str) -> Tuple[List[RegraCSS], List[BlocoMedia]]:
    regras: List[RegraCSS] = []
    medias: List[BlocoMedia] = []
    for m_style in _RE_STYLE.finditer(html):
        base = m_style.start(1)
        css = _sem_comentarios(m_style.group(1))
        _parse_css(css, base, regras, medias, media_actual=None, offset=0, fim=len(css))
    return regras, medias


def _parse_css(css: str, base: int, regras: List[RegraCSS], medias: List[BlocoMedia],
               media_actual: str | None, offset: int, fim: int) -> None:
    i = offset
    while i < fim:
        ch = css[i]
        if ch.isspace():
            i += 1
            continue
        # início de um seletor ou at-rule: encontrar o '{' correspondente
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


# ---------------------------------------------------------------------------
# Análise de seletores: tokens exigidos e decisão vivo/morto
# ---------------------------------------------------------------------------

_RE_NOT = re.compile(r":not\([^)]*\)")
_RE_PSEUDO = re.compile(r"::?[a-zA-Z-]+(\([^)]*\))?")
_RE_ATRIBUTO = re.compile(r"\[[^\]]*\]")
_RE_CLASSE = re.compile(r"\.(-?[A-Za-z_][A-Za-z0-9_-]*)")
_RE_ID = re.compile(r"#(-?[A-Za-z_][A-Za-z0-9_-]*)")


def tokens_exigidos(seletor: str) -> Tuple[Set[str], Set[str]]:
    """Classes e ids que TÊM de existir para o seletor corresponder a algo."""
    limpo = _RE_NOT.sub("", seletor)
    limpo = _RE_ATRIBUTO.sub("", limpo)
    limpo = _RE_PSEUDO.sub("", limpo)
    return set(_RE_CLASSE.findall(limpo)), set(_RE_ID.findall(limpo))


def dividir_seletores(lista: str) -> List[str]:
    return [s.strip() for s in lista.split(",") if s.strip()]


@dataclass
class Analise:
    pagina: Path
    seletor: str
    media: str | None
    correspondencias_pagina: int      # elementos nesta página com os tokens exigidos
    correspondencias_site: int        # idem, somado em todas as páginas
    js_pode_criar: bool
    morto_global: bool


def analisar(paginas: List[Pagina], js_tokens: Set[str]):
    """Devolve (analises, regras_por_pagina) só para regras da família nav antiga."""
    classes_por_pagina: Dict[Path, Dict[str, int]] = {}
    ids_por_pagina: Dict[Path, Set[str]] = {}
    for p in paginas:
        contagem: Dict[str, int] = {}
        colector = _ColectorTokens()
        colector.feed(p.html)
        # contagem por token: nº de elementos que têm o token
        for m in re.finditer(r'class="([^"]*)"', p.html):
            for token in m.group(1).split():
                contagem[token] = contagem.get(token, 0) + 1
        classes_por_pagina[p.caminho] = contagem
        ids_por_pagina[p.caminho] = p.ids

    def conta_pagina(pagina: Path, classes: Set[str], ids: Set[str]) -> int:
        contagem = classes_por_pagina[pagina]
        presentes_ids = ids_por_pagina[pagina]
        if any(i not in presentes_ids for i in ids):
            return 0
        if any(c not in contagem for c in classes):
            return 0
        if classes:
            return min(contagem[c] for c in classes)
        return 1 if ids else 1

    analises: List[Analise] = []
    regras_alvo: Dict[Path, List[Tuple[RegraCSS, bool]]] = {}
    medias_por_pagina: Dict[Path, List[BlocoMedia]] = {}

    for p in paginas:
        regras, medias = extrair_regras(p.html)
        medias_por_pagina[p.caminho] = medias
        for regra in regras:
            seletores = dividir_seletores(regra.seletor)
            pertence_familia = False
            todos_mortos = True
            for sel in seletores:
                classes, ids = tokens_exigidos(sel)
                if classes & TOKENS_NAV_ANTIGA_CLASSES or ids & TOKENS_NAV_ANTIGA_IDS:
                    pertence_familia = True
                else:
                    continue
                total_site = sum(conta_pagina(q.caminho, classes, ids) for q in paginas)
                # morto só se PROVADO: pelo menos um token exigido não existe
                # em nenhum elemento de nenhuma página E nenhum JS o consegue
                # adicionar; ou um id exigido não existe em nenhuma página.
                # (Um token estaticamente ausente mas adicionável por JS nunca
                # prova nada — ex.: ".mobile-menu.aberto" tem 'aberto'
                # adicionável pelo nav.js e 'mobile-menu' presente nas páginas
                # com o div órfão da nav antiga → AMBIGUO, nunca MORTO.)
                classes_site: Set[str] = set()
                for q in paginas:
                    classes_site.update(classes_por_pagina[q.caminho].keys())
                ids_site: Set[str] = set()
                for q in paginas:
                    ids_site.update(ids_por_pagina[q.caminho])
                morto = any(c not in classes_site and c not in js_tokens for c in classes) \
                    or any(i not in ids_site for i in ids)
                js_cria = (not morto) and any(c not in classes_site and c in js_tokens for c in classes)
                if not morto:
                    todos_mortos = False
                analises.append(Analise(
                    pagina=p.caminho.relative_to(RAIZ),
                    seletor=sel,
                    media=regra.media,
                    correspondencias_pagina=conta_pagina(p.caminho, classes, ids),
                    correspondencias_site=total_site,
                    js_pode_criar=js_cria,
                    morto_global=morto,
                ))
            if pertence_familia:
                # regra só é removível se TODOS os seletores da família forem
                # mortos E os restantes seletores (fora da família) não existirem
                # — uma regra partilhada com um seletor vivo fica intacta.
                fora_familia = [
                    s for s in seletores
                    if not (tokens_exigidos(s)[0] & TOKENS_NAV_ANTIGA_CLASSES
                            or tokens_exigidos(s)[1] & TOKENS_NAV_ANTIGA_IDS)
                ]
                removivel = todos_mortos and not fora_familia
                regras_alvo.setdefault(p.caminho, []).append((regra, removivel))

    return analises, regras_alvo, medias_por_pagina


# ---------------------------------------------------------------------------
# Remoção
# ---------------------------------------------------------------------------


def remover(pagina: Pagina, regras: List[Tuple[RegraCSS, bool]], medias: List[BlocoMedia]) -> Tuple[str, int]:
    """Remove as regras removíveis; devolve (novo_html, n_regras_removidas)."""
    spans: List[Tuple[int, int]] = []
    removidas = [r for r, ok in regras if ok]
    if not removidas:
        return pagina.html, 0
    spans_regras = {(r.inicio, r.fim) for r in removidas}
    for r in removidas:
        spans.append((r.inicio, r.fim))
    # @media que fica vazio depois das remoções → remover o bloco inteiro
    for bloco in medias:
        if bloco.regras and all((r.inicio, r.fim) in spans_regras for r in bloco.regras):
            spans = [s for s in spans if not (s[0] >= bloco.corpo_inicio and s[1] <= bloco.fim)]
            spans.append((bloco.inicio, bloco.fim))
    spans.sort(reverse=True)
    html = pagina.html
    for inicio, fim in spans:
        # absorve o whitespace até ao fim da linha seguinte ao '}'
        fim_real = fim
        while fim_real < len(html) and html[fim_real] in " \t":
            fim_real += 1
        if fim_real < len(html) and html[fim_real] == "\n":
            fim_real += 1
        # absorve indentação no início da linha
        inicio_real = inicio
        while inicio_real > 0 and html[inicio_real - 1] in " \t":
            inicio_real -= 1
        html = html[:inicio_real] + html[fim_real:]
    # nunca deixar mais do que uma linha em branco seguida dentro do <style>
    html = _RE_STYLE.sub(lambda m: m.group(0).replace(m.group(1), re.sub(r"\n[ \t]*\n[ \t]*\n+", "\n\n", m.group(1))) if re.search(r"\n[ \t]*\n[ \t]*\n", m.group(1)) else m.group(0), html)
    return html, len(removidas)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    escrever = "--write" in argv
    verificar = "--check" in argv
    if escrever and verificar:
        print("ERRO: --write e --check são mutuamente exclusivos", file=sys.stderr)
        return EXIT_ERRO_USO

    paginas = [carregar_pagina(c) for c in paginas_servidas()]
    js_tokens = tokens_que_js_pode_adicionar(paginas)
    analises, regras_alvo, medias_por_pagina = analisar(paginas, js_tokens)

    if not analises:
        print("Nenhuma regra da família nav antiga encontrada — nada a fazer.")
        return EXIT_OK

    # --- tabela de inventário -------------------------------------------------
    mortas = [a for a in analises if a.morto_global]
    ambiguas = [a for a in analises if not a.morto_global]

    largura_f = max(len(str(a.pagina)) for a in analises)
    largura_s = max(len(a.seletor) for a in analises)
    print(f"{'ficheiro':<{largura_f}}  {'seletor':<{largura_s}}  {'nesta pág.':>10}  {'no site':>8}  decisão")
    print("-" * (largura_f + largura_s + 45))
    for a in sorted(analises, key=lambda x: (str(x.pagina), x.seletor)):
        decisao = "MORTO (remover)" if a.morto_global else "AMBIGUO (não tocar)"
        extra = " [JS pode criar]" if a.js_pode_criar else ""
        print(f"{str(a.pagina):<{largura_f}}  {a.seletor:<{largura_s}}  {a.correspondencias_pagina:>10}  {a.correspondencias_site:>8}  {decisao}{extra}")

    n_regras_removiveis = sum(1 for lst in regras_alvo.values() for _, ok in lst if ok)
    paginas_afectadas = sorted({str(c.relative_to(RAIZ)) for c, lst in regras_alvo.items() if any(ok for _, ok in lst)})
    print()
    print(f"Seletores mortos: {len(mortas)} · ambíguos: {len(ambiguas)} · regras removíveis: {n_regras_removiveis} em {len(paginas_afectadas)} página(s)")
    if ambiguas:
        paginas_amb = sorted({str(a.pagina) for a in ambiguas if a.correspondencias_pagina > 0})
        print(f"AMBIGUO: seletores com correspondência real em: {', '.join(paginas_amb) or '(via site-wide)'}")

    if verificar:
        if n_regras_removiveis:
            print(f"CHECK FALHOU: {n_regras_removiveis} regra(s) morta(s) ainda presente(s).", file=sys.stderr)
            return EXIT_ESTADO_INESPERADO
        print("CHECK OK: nenhuma regra morta removível presente.")
        return EXIT_OK

    if not escrever:
        print("\n(dry-run — usar --write para aplicar; --check para verificação de CI)")
        return EXIT_OK

    # --- escrita ---------------------------------------------------------------
    total_regras = 0
    total_bytes = 0
    for pagina in paginas:
        regras = regras_alvo.get(pagina.caminho, [])
        if not any(ok for _, ok in regras):
            continue
        novo, n = remover(pagina, regras, medias_por_pagina[pagina.caminho])
        if n and novo != pagina.html:
            bytes_removidos = len(pagina.html.encode("utf-8")) - len(novo.encode("utf-8"))
            pagina.caminho.write_text(novo, encoding="utf-8")
            rel = pagina.caminho.relative_to(RAIZ)
            print(f"  {rel}: {n} regra(s) removida(s), {bytes_removidos} bytes")
            total_regras += n
            total_bytes += bytes_removidos
        elif n:
            raise EstadoInesperado(f"{pagina.caminho}: {n} regras marcadas para remover mas o conteúdo não mudou")

    print(f"\nTotal: {total_regras} regra(s) em {len(paginas_afectadas)} página(s), {total_bytes} bytes removidos")

    # convergência: depois de escrever, não pode restar nenhuma regra removível
    paginas2 = [carregar_pagina(c) for c in paginas_servidas()]
    _, regras_alvo2, _ = analisar(paginas2, tokens_que_js_pode_adicionar(paginas2))
    restantes = sum(1 for lst in regras_alvo2.values() for _, ok in lst if ok)
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
