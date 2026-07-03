"""
Testes para scripts/gerir_estado_feeds.py — máquina de estados de saúde
dos feeds de notícias (Fase 3 do robustecimento de 2026-07-04, mesmo
padrão de gerir_estado_fontes.py para fontes bloqueadas do scraper).

Sem chamadas reais ao GitHub -- este módulo só calcula e persiste
`data/estado_feeds.json`; a criação/fecho de Issues fica a cargo do
passo GitHub Actions que consome o resultado.

Diferença deliberada face a gerir_estado_fontes.py: não há uma lista
fixa de feeds monitorizados neste módulo — os nomes vêm sempre de
`data/feeds_saude_hoje.json` (escrito por gerar_noticias.py a partir do
`FEEDS` real), para nunca haver 2 listas que possam divergir.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gerir_estado_feeds import (
    LIMIAR_DIAS_PARA_ISSUE,
    calcular_novo_estado,
    carregar_estado,
    feeds_para_issue,
    feeds_recuperados,
    guardar_estado,
    main,
)

_FEEDS = ["abono_familia", "dre"]


# ── calcular_novo_estado ────────────────────────────────────────────────────

def test_feed_sem_estado_anterior_e_morto_hoje_comeca_em_1_dia():
    novo = calcular_novo_estado({}, ["dre"], _FEEDS, hoje="2026-07-01")
    assert novo["dre"]["estado"] == "MORTO"
    assert novo["dre"]["dias_consecutivos_morto"] == 1


def test_feed_morto_ontem_e_hoje_acumula_dias():
    anterior = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 2, "ultima_ok": "2026-06-28"}}
    novo = calcular_novo_estado(anterior, ["dre"], _FEEDS, hoje="2026-07-01")
    assert novo["dre"]["dias_consecutivos_morto"] == 3
    assert novo["dre"]["ultima_ok"] == "2026-06-28"  # não muda enquanto morto


def test_feed_nao_morto_hoje_e_ok_e_reinicia_contador():
    anterior = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 5, "ultima_ok": "2026-06-20"}}
    novo = calcular_novo_estado(anterior, [], _FEEDS, hoje="2026-07-01")
    assert novo["dre"]["estado"] == "OK"
    assert novo["dre"]["dias_consecutivos_morto"] == 0
    assert novo["dre"]["ultima_ok"] == "2026-07-01"


def test_feed_sem_historico_e_ok_hoje():
    novo = calcular_novo_estado({}, [], _FEEDS, hoje="2026-07-01")
    assert novo["abono_familia"]["estado"] == "OK"
    assert novo["abono_familia"]["ultima_ok"] == "2026-07-01"


def test_todos_os_feeds_aparecem_no_estado_mesmo_sem_morte():
    novo = calcular_novo_estado({}, [], _FEEDS, hoje="2026-07-01")
    assert set(novo.keys()) == set(_FEEDS)


# ── feeds_para_issue: limiar de 3 dias ──────────────────────────────────────

def test_um_dia_morto_nao_gera_issue():
    estado = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 1}}
    assert feeds_para_issue(estado) == []


def test_dois_dias_morto_nao_gera_issue():
    estado = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 2}}
    assert feeds_para_issue(estado) == []


def test_tres_dias_morto_gera_issue():
    estado = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 3}}
    assert feeds_para_issue(estado) == ["dre"]


def test_mais_de_tres_dias_continua_a_aparecer_para_comentario():
    estado = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 10}}
    assert feeds_para_issue(estado) == ["dre"]


def test_feed_ok_nunca_aparece_para_issue():
    estado = {"dre": {"estado": "OK", "dias_consecutivos_morto": 0}}
    assert feeds_para_issue(estado) == []


def test_limiar_configuravel():
    estado = {"x": {"estado": "MORTO", "dias_consecutivos_morto": 1}}
    assert feeds_para_issue(estado, limiar=1) == ["x"]


def test_limiar_por_omissao_e_tres():
    assert LIMIAR_DIAS_PARA_ISSUE == 3


# ── feeds_recuperados: transição MORTO -> OK ────────────────────────────────

def test_transicao_morto_para_ok_e_reportada():
    anterior = {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 4}}
    novo = {"dre": {"estado": "OK", "dias_consecutivos_morto": 0, "ultima_ok": "2026-07-01"}}
    assert feeds_recuperados(anterior, novo) == ["dre"]


def test_continua_morto_nao_e_recuperado():
    anterior = {"dre": {"estado": "MORTO"}}
    novo = {"dre": {"estado": "MORTO"}}
    assert feeds_recuperados(anterior, novo) == []


def test_ja_estava_ok_nao_e_recuperado_de_novo():
    anterior = {"dre": {"estado": "OK"}}
    novo = {"dre": {"estado": "OK"}}
    assert feeds_recuperados(anterior, novo) == []


def test_sem_estado_anterior_nao_e_recuperado():
    novo = {"dre": {"estado": "OK"}}
    assert feeds_recuperados({}, novo) == []


# ── Persistência (carregar_estado / guardar_estado) ─────────────────────────

def test_guardar_e_carregar_estado_ida_e_volta(tmp_path):
    caminho = tmp_path / "data" / "estado_feeds.json"
    estado = {"dre": {"estado": "OK", "dias_consecutivos_morto": 0, "ultima_ok": "2026-07-01"}}
    guardar_estado(caminho, estado)
    assert carregar_estado(caminho) == estado


def test_carregar_estado_sem_ficheiro_devolve_vazio(tmp_path):
    assert carregar_estado(tmp_path / "nao-existe.json") == {}


def test_carregar_estado_com_json_invalido_devolve_vazio(tmp_path):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{ isto nao e json", encoding="utf-8")
    assert carregar_estado(caminho) == {}


# ── main(): fluxo completo isolado num tmp_path ─────────────────────────────

def _preparar_repo_falso(tmp_path, *, saude_hoje=None, estado_anterior=None):
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    if saude_hoje is not None:
        (tmp_path / "data" / "feeds_saude_hoje.json").write_text(
            json.dumps(saude_hoje, ensure_ascii=False), encoding="utf-8"
        )
    if estado_anterior is not None:
        (tmp_path / "data" / "estado_feeds.json").write_text(
            json.dumps(estado_anterior, ensure_ascii=False), encoding="utf-8"
        )


def test_main_atinge_limiar_ao_terceiro_dia_consecutivo(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        saude_hoje=[
            {"nome": "dre", "url": "https://dre.pt/rss/dr1s.rss", "estado": "MORTO", "motivo": "erro_parsing_xml", "n_entradas": 0, "data": "2026-07-01"},
            {"nome": "abono_familia", "url": "https://x", "estado": "OK", "motivo": "", "n_entradas": 10, "data": "2026-07-01"},
        ],
        estado_anterior={"dre": {"estado": "MORTO", "dias_consecutivos_morto": 2, "ultima_ok": "2026-06-28"}},
    )

    estado = main(raiz=tmp_path, hoje="2026-07-01")

    assert estado["dre"]["dias_consecutivos_morto"] == 3
    assert feeds_para_issue(estado) == ["dre"]

    persistido = carregar_estado(tmp_path / "data" / "estado_feeds.json")
    assert persistido == estado


def test_main_todos_os_feeds_do_snapshot_ficam_no_ficheiro_persistido(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        saude_hoje=[
            {"nome": "abono_familia", "url": "https://x", "estado": "OK", "motivo": "", "n_entradas": 10, "data": "2026-07-01"},
            {"nome": "rsi", "url": "https://y", "estado": "OK", "motivo": "", "n_entradas": 5, "data": "2026-07-01"},
        ],
    )

    estado = main(raiz=tmp_path, hoje="2026-07-01")

    assert set(estado.keys()) == {"abono_familia", "rsi"}


def test_main_sem_feeds_saude_hoje_json_mantem_estado_anterior(tmp_path):
    """Sem dados de saúde desta corrida (ex.: gerar_noticias.py falhou
    antes de escrever) — nunca inventa 'tudo OK' nem 'tudo morto'; mantém
    o último estado real conhecido."""
    _preparar_repo_falso(
        tmp_path,
        estado_anterior={"dre": {"estado": "MORTO", "dias_consecutivos_morto": 5, "ultima_ok": "2026-06-01"}},
    )
    estado = main(raiz=tmp_path, hoje="2026-07-01")
    assert estado == {"dre": {"estado": "MORTO", "dias_consecutivos_morto": 5, "ultima_ok": "2026-06-01"}}


def test_main_nao_escreve_fora_de_data(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        saude_hoje=[{"nome": "abono_familia", "url": "https://x", "estado": "OK", "motivo": "", "n_entradas": 10, "data": "2026-07-01"}],
    )
    antes = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    main(raiz=tmp_path, hoje="2026-07-01")
    depois = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    novos = depois - antes
    assert all(str(p).startswith("data/") for p in novos)
