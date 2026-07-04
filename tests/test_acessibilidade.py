"""
Auditoria WCAG 2.1 AA permanente (2026-07-04) — axe-core vendorizado
(`tests/vendor/axe-core/axe.min.js`, MPL-2.0, sem CDN em runtime) corrido
via Playwright sobre as 36 páginas reais do repositório
(`encontrar_paginas()`, mesmo padrão de `test_nav_coerencia.py`/
`test_higiene_indexacao.py`).

Serve as páginas por um `http.server` local enraizado na raiz do
repositório — nunca `file://`, que quebra `<link>`/`<script>` de
caminho absoluto (ex. `/assets/css/nav.css`) e invalidaria a auditoria
(achado real da sessão que criou este ficheiro: a 1.ª tentativa via
`file://` reportava 34/36 páginas com `color-contrast`, a maioria falsos
positivos por CSS/JS partilhado nunca ter carregado).

Threshold documentado (mesmo espírito do guardrail de skips de
`integridade.yml`): `critical`/`serious` nunca são tolerados — falha
sempre que exista um. `moderate`/`minor` têm um limiar explícito
(`LIMIAR_MODERADO_MINOR`, hoje 0, confirmado pela auditoria de
2026-07-04 depois de corrigidas todas as violações encontradas) — subir
este número exige decisão consciente, nunca uma regressão silenciosa.

Se o Chromium do Playwright não estiver disponível, o módulo inteiro é
ignorado (skip) em vez de falhar — mesmo padrão de
`test_pesquisa_hero.py`/`test_simulador_psu_calculo.py`.
"""
from __future__ import annotations

import glob
import http.server
import os
import socket
import sys
import threading
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from sincronizar_clusters import encontrar_paginas  # noqa: E402

AXE_JS = (RAIZ / "tests" / "vendor" / "axe-core" / "axe.min.js").read_text(encoding="utf-8")

PAGINAS = sorted(encontrar_paginas(RAIZ), key=lambda p: str(p))
IDS = [str(p.relative_to(RAIZ)) for p in PAGINAS]

# Limiar documentado para violações moderate/minor (best-practice do axe,
# não são critérios formais WCAG) — 0 hoje, confirmado pela auditoria de
# 2026-07-04. critical/serious nunca têm limiar: qualquer ocorrência falha.
LIMIAR_MODERADO_MINOR = 0


def _localizar_chromium():
    bases = [os.environ.get("PLAYWRIGHT_BROWSERS_PATH")]
    bases += ["/opt/pw-browsers", os.path.expanduser("~/.cache/ms-playwright")]
    for base in bases:
        if not base:
            continue
        candidatos = sorted(glob.glob(os.path.join(base, "chromium-*", "chrome-linux*", "chrome")))
        if candidatos:
            return candidatos[-1]
    return None


try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    _PLAYWRIGHT_DISPONIVEL = False

_CHROMIUM_PATH = _localizar_chromium() if _PLAYWRIGHT_DISPONIVEL else None

pytestmark = pytest.mark.skipif(
    not (_PLAYWRIGHT_DISPONIVEL and _CHROMIUM_PATH),
    reason="Playwright/Chromium não disponível neste ambiente",
)


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor():
    porta = _porta_livre()
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(RAIZ), **kw)  # noqa: E731
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", porta), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{porta}"
    httpd.shutdown()
    thread.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        yield b
        b.close()


def _auditar_pagina(browser, base_url, rel):
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.route("https://cdn-cookieyes.com/**", lambda route: route.abort())
    page.route("https://www.googletagmanager.com/**", lambda route: route.abort())
    try:
        page.goto(f"{base_url}/{rel}", wait_until="networkidle", timeout=30000)
        page.add_script_tag(content=AXE_JS)
        resultado = page.evaluate(
            """
            async () => {
                return await axe.run(document, {
                    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'best-practice'] }
                });
            }
            """
        )
        return resultado.get("violations", [])
    finally:
        page.close()


@pytest.mark.parametrize("caminho", PAGINAS, ids=IDS)
def test_sem_violacoes_criticas_ou_serias(servidor, browser, caminho):
    rel = str(caminho.relative_to(RAIZ))
    violacoes = _auditar_pagina(browser, servidor, rel)

    graves = [v for v in violacoes if v.get("impact") in ("critical", "serious")]
    assert not graves, (
        f"{rel}: {len(graves)} violação(ões) critical/serious — "
        + "; ".join(f"{v['id']} ({v['impact']}, {len(v['nodes'])} elemento(s))" for v in graves)
    )

    moderadas_menores = [v for v in violacoes if v.get("impact") in ("moderate", "minor")]
    total_nodes = sum(len(v["nodes"]) for v in moderadas_menores)
    assert total_nodes <= LIMIAR_MODERADO_MINOR, (
        f"{rel}: {total_nodes} ocorrência(s) moderate/minor, acima do limiar documentado de "
        f"{LIMIAR_MODERADO_MINOR} — "
        + "; ".join(f"{v['id']} ({v['impact']}, {len(v['nodes'])} elemento(s))" for v in moderadas_menores)
    )
