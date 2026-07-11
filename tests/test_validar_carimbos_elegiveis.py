"""
Testes de scripts/validar_carimbos_elegiveis.py — o passo humano do
critério de activação da revalidação de carimbo (ver ROADMAP.md e
CLAUDE.md "REVALIDAÇÃO DE CARIMBO").

Mesma disciplina do invariante "nenhum estado de erro pode parecer
sucesso": cada caminho de FALHA é provado explicitamente (falso elegível
por hash mudado, fonte não-OK, ok_via_arquivo, conteúdo vazio, scrape em
falta), não só o caminho feliz. Tudo isolado em tmp_path — nunca toca
nos dados reais do repositório.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validar_carimbos_elegiveis import (  # noqa: E402
    elegiveis_do_relatorio,
    historico_hashes,
    verificar_pagina,
)

HOJE = "2026-07-11"
ONTEM = "2026-07-10"

CONTEUDO_REAL = {"titulo": "Página real", "paragrafos": ["x" * 300]}


def _montar_raiz(tmp_path: Path) -> Path:
    (tmp_path / "data" / "scraped").mkdir(parents=True)
    (tmp_path / "shadow_history").mkdir()
    (tmp_path / "pagina.html").write_text(
        "<html><body><p>Verificado a 01/07/2026</p></body></html>", encoding="utf-8"
    )
    return tmp_path


def _escrever_scrape(raiz: Path, slug: str, dia: str, *, hash_="abc123",
                     status="ok", conteudo=None, url="https://exemplo.gov.pt/a"):
    (raiz / "data" / "scraped" / f"{slug}_{dia}.json").write_text(
        json.dumps({
            "url": url,
            "status": status,
            "hash_conteudo": hash_,
            "conteudo_extraido": CONTEUDO_REAL if conteudo is None else conteudo,
        }),
        encoding="utf-8",
    )


ESTADO_OK = {"fonte_x": {"estado": "OK", "dias_consecutivos_bloqueado": 0, "ultima_ok": HOJE}}


def test_pagina_saudavel_sem_problemas(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", ONTEM)
    _escrever_scrape(raiz, "fonte_x", HOJE)
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert r.problemas == []
    assert r.avisos == []
    assert r.carimbo == "2026-07-01"


def test_hash_mudado_hoje_e_falso_elegivel(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", ONTEM, hash_="antigo")
    _escrever_scrape(raiz, "fonte_x", HOJE, hash_="novo")
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert any("hash de hoje ≠ ontem" in p for p in r.problemas)


def test_fonte_nao_ok_e_problema(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", ONTEM)
    _escrever_scrape(raiz, "fonte_x", HOJE)
    estado = {"fonte_x": {"estado": "BLOQUEADO"}}
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], estado, HOJE, ONTEM)
    assert any("BLOQUEADO" in p for p in r.problemas)


def test_ok_via_arquivo_nunca_valida(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", ONTEM)
    _escrever_scrape(raiz, "fonte_x", HOJE, status="ok_via_arquivo")
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert any("ok_via_arquivo" in p or "status" in p for p in r.problemas)


def test_conteudo_vazio_e_problema(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", ONTEM)
    _escrever_scrape(raiz, "fonte_x", HOJE, conteudo={})
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert any("conteúdo suspeito" in p for p in r.problemas)


def test_scrape_em_falta_e_problema(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", HOJE)  # falta o de ontem
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert any("scrape de ontem em falta" in p for p in r.problemas)


def test_mudanca_pos_carimbo_mesma_url_e_aviso_nao_problema(tmp_path):
    raiz = _montar_raiz(tmp_path)  # carimbo 2026-07-01
    _escrever_scrape(raiz, "fonte_x", "2026-07-05", hash_="v1")
    _escrever_scrape(raiz, "fonte_x", "2026-07-06", hash_="v2")  # mesma URL
    _escrever_scrape(raiz, "fonte_x", ONTEM, hash_="v2")
    _escrever_scrape(raiz, "fonte_x", HOJE, hash_="v2")
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert r.problemas == []
    assert any("MESMA URL" in a for a in r.avisos)


def test_mudanca_pos_carimbo_com_url_diferente_e_artefacto(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", "2026-07-05", hash_="v1", url="https://exemplo.gov.pt/antiga")
    _escrever_scrape(raiz, "fonte_x", "2026-07-06", hash_="v2", url="https://exemplo.gov.pt/nova")
    _escrever_scrape(raiz, "fonte_x", ONTEM, hash_="v2", url="https://exemplo.gov.pt/nova")
    _escrever_scrape(raiz, "fonte_x", HOJE, hash_="v2", url="https://exemplo.gov.pt/nova")
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert r.problemas == []
    assert any("artefacto" in a for a in r.avisos)
    assert not any("MESMA URL" in a for a in r.avisos)


def test_mudanca_anterior_ao_carimbo_nao_gera_aviso(tmp_path):
    raiz = _montar_raiz(tmp_path)  # carimbo 2026-07-01
    _escrever_scrape(raiz, "fonte_x", "2026-06-20", hash_="v0")
    _escrever_scrape(raiz, "fonte_x", "2026-06-25", hash_="v1")  # antes do carimbo
    _escrever_scrape(raiz, "fonte_x", ONTEM, hash_="v1")
    _escrever_scrape(raiz, "fonte_x", HOJE, hash_="v1")
    r = verificar_pagina(raiz, "pagina.html", ["fonte_x"], ESTADO_OK, HOJE, ONTEM)
    assert r.problemas == [] and r.avisos == []


def test_historico_hashes_ordenado(tmp_path):
    raiz = _montar_raiz(tmp_path)
    _escrever_scrape(raiz, "fonte_x", "2026-07-02", hash_="b")
    _escrever_scrape(raiz, "fonte_x", "2026-07-01", hash_="a")
    regs = historico_hashes(raiz, "fonte_x")
    assert [r[0] for r in regs] == ["2026-07-01", "2026-07-02"]


def test_elegiveis_do_relatorio_lista_e_nenhuma(tmp_path):
    raiz = _montar_raiz(tmp_path)
    (raiz / "shadow_history" / f"shadow_report_{HOJE}.md").write_text(
        "## Carimbos elegíveis para revalidação (simulado)\n"
        "- 2 página(s) seriam elegíveis hoje: `b.html`, `a.html`\n",
        encoding="utf-8",
    )
    assert elegiveis_do_relatorio(raiz, HOJE) == ["a.html", "b.html"]

    (raiz / "shadow_history" / "shadow_report_2026-07-12.md").write_text(
        "- Nenhuma página elegível hoje\n", encoding="utf-8"
    )
    assert elegiveis_do_relatorio(raiz, "2026-07-12") == []
    assert elegiveis_do_relatorio(raiz, "2026-07-13") is None
