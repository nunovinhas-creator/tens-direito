"""
Testes para scripts/gerir_estado_fontes.py — máquina de estados de
fontes bloqueadas (Fase 2 do robustecimento do Shadow Mode / higiene
de Issues).

Sem chamadas reais ao GitHub -- este módulo só calcula e persiste
`data/estado_fontes.json`; a criação/fecho de Issues fica a cargo do
passo GitHub Actions que consome o resultado.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from gerir_estado_fontes import (
    LIMIAR_DIAS_PARA_ISSUE,
    SLUGS_MONITORIZADOS,
    calcular_novo_estado,
    carregar_estado,
    fontes_para_issue,
    fontes_recuperadas,
    guardar_estado,
    main,
)

_SLUGS = ["seg_social_abono", "iefp_desemprego"]


# ── calcular_novo_estado ────────────────────────────────────────────────────

def test_fonte_sem_estado_anterior_e_bloqueada_hoje_comeca_em_1_dia():
    novo = calcular_novo_estado({}, ["seg_social_abono"], _SLUGS, hoje="2026-07-01")
    assert novo["seg_social_abono"]["estado"] == "BLOQUEADO"
    assert novo["seg_social_abono"]["dias_consecutivos_bloqueado"] == 1


def test_fonte_bloqueada_ontem_e_hoje_acumula_dias():
    anterior = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 2, "ultima_ok": "2026-06-28"}}
    novo = calcular_novo_estado(anterior, ["seg_social_abono"], _SLUGS, hoje="2026-07-01")
    assert novo["seg_social_abono"]["dias_consecutivos_bloqueado"] == 3
    assert novo["seg_social_abono"]["ultima_ok"] == "2026-06-28"  # não muda enquanto bloqueado


def test_fonte_nao_bloqueada_hoje_e_ok_e_reinicia_contador():
    anterior = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 5, "ultima_ok": "2026-06-20"}}
    novo = calcular_novo_estado(anterior, [], _SLUGS, hoje="2026-07-01")
    assert novo["seg_social_abono"]["estado"] == "OK"
    assert novo["seg_social_abono"]["dias_consecutivos_bloqueado"] == 0
    assert novo["seg_social_abono"]["ultima_ok"] == "2026-07-01"


def test_fonte_sem_historico_e_ok_hoje():
    novo = calcular_novo_estado({}, [], _SLUGS, hoje="2026-07-01")
    assert novo["iefp_desemprego"]["estado"] == "OK"
    assert novo["iefp_desemprego"]["ultima_ok"] == "2026-07-01"


def test_todas_as_fontes_monitorizadas_aparecem_no_estado_mesmo_sem_bloqueio():
    novo = calcular_novo_estado({}, [], _SLUGS, hoje="2026-07-01")
    assert set(novo.keys()) == set(_SLUGS)


# ── fontes_para_issue: limiar de 3 dias ─────────────────────────────────────

def test_um_dia_bloqueado_nao_gera_issue():
    estado = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 1}}
    assert fontes_para_issue(estado) == []


def test_dois_dias_bloqueado_nao_gera_issue():
    estado = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 2}}
    assert fontes_para_issue(estado) == []


def test_tres_dias_bloqueado_gera_issue():
    estado = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 3}}
    assert fontes_para_issue(estado) == ["seg_social_abono"]


def test_mais_de_tres_dias_continua_a_aparecer_para_comentario():
    estado = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 10}}
    assert fontes_para_issue(estado) == ["seg_social_abono"]


def test_fonte_ok_nunca_aparece_para_issue():
    estado = {"seg_social_abono": {"estado": "OK", "dias_consecutivos_bloqueado": 0}}
    assert fontes_para_issue(estado) == []


def test_limiar_configuravel():
    estado = {"x": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 1}}
    assert fontes_para_issue(estado, limiar=1) == ["x"]


def test_limiar_por_omissao_e_tres():
    assert LIMIAR_DIAS_PARA_ISSUE == 3


# ── fontes_recuperadas: transição BLOQUEADO -> OK ───────────────────────────

def test_transicao_bloqueado_para_ok_e_reportada():
    anterior = {"seg_social_abono": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 4}}
    novo = {"seg_social_abono": {"estado": "OK", "dias_consecutivos_bloqueado": 0, "ultima_ok": "2026-07-01"}}
    assert fontes_recuperadas(anterior, novo) == ["seg_social_abono"]


def test_continua_bloqueado_nao_e_recuperada():
    anterior = {"seg_social_abono": {"estado": "BLOQUEADO"}}
    novo = {"seg_social_abono": {"estado": "BLOQUEADO"}}
    assert fontes_recuperadas(anterior, novo) == []


def test_ja_estava_ok_nao_e_recuperada_de_novo():
    anterior = {"seg_social_abono": {"estado": "OK"}}
    novo = {"seg_social_abono": {"estado": "OK"}}
    assert fontes_recuperadas(anterior, novo) == []


def test_sem_estado_anterior_nao_e_recuperada():
    novo = {"seg_social_abono": {"estado": "OK"}}
    assert fontes_recuperadas({}, novo) == []


# ── Persistência (carregar_estado / guardar_estado) ─────────────────────────

def test_guardar_e_carregar_estado_ida_e_volta(tmp_path):
    caminho = tmp_path / "data" / "estado_fontes.json"
    estado = {"seg_social_abono": {"estado": "OK", "dias_consecutivos_bloqueado": 0, "ultima_ok": "2026-07-01"}}
    guardar_estado(caminho, estado)
    assert carregar_estado(caminho) == estado


def test_carregar_estado_sem_ficheiro_devolve_vazio(tmp_path):
    assert carregar_estado(tmp_path / "nao-existe.json") == {}


def test_carregar_estado_com_json_invalido_devolve_vazio(tmp_path):
    caminho = tmp_path / "estado.json"
    caminho.write_text("{ isto nao e json", encoding="utf-8")
    assert carregar_estado(caminho) == {}


# ── main(): fluxo completo isolado num tmp_path ─────────────────────────────

def _preparar_repo_falso(tmp_path, *, bloqueios=None, estado_anterior=None):
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    if bloqueios is not None:
        (tmp_path / "data" / "bloqueios.json").write_text(
            json.dumps(bloqueios, ensure_ascii=False), encoding="utf-8"
        )
    if estado_anterior is not None:
        (tmp_path / "data" / "estado_fontes.json").write_text(
            json.dumps(estado_anterior, ensure_ascii=False), encoding="utf-8"
        )


def test_main_atinge_limiar_ao_terceiro_dia_consecutivo(tmp_path):
    _preparar_repo_falso(
        tmp_path,
        bloqueios=[
            {"slug": "iefp_desemprego", "url": "https://www.iefp.pt/subsidio-desemprego", "data": "2026-07-01T09:00:00+00:00", "motivos": ["desafio:recaptcha"], "chars_uteis": 100},
        ],
        estado_anterior={"iefp_desemprego": {"estado": "BLOQUEADO", "dias_consecutivos_bloqueado": 2, "ultima_ok": "2026-06-28"}},
    )

    estado = main(raiz=tmp_path, hoje="2026-07-01")

    assert estado["iefp_desemprego"]["dias_consecutivos_bloqueado"] == 3
    assert fontes_para_issue(estado) == ["iefp_desemprego"]

    persistido = carregar_estado(tmp_path / "data" / "estado_fontes.json")
    assert persistido == estado


def test_main_todas_as_fontes_monitorizadas_ficam_no_ficheiro_persistido(tmp_path):
    _preparar_repo_falso(tmp_path, bloqueios=[])

    estado = main(raiz=tmp_path, hoje="2026-07-01")

    assert set(estado.keys()) == set(SLUGS_MONITORIZADOS)


def test_main_sem_bloqueios_json_nao_crasha(tmp_path):
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    estado = main(raiz=tmp_path, hoje="2026-07-01")
    assert all(info["estado"] == "OK" for info in estado.values())


def test_main_nao_escreve_fora_de_data(tmp_path):
    _preparar_repo_falso(tmp_path, bloqueios=[])
    antes = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    main(raiz=tmp_path, hoje="2026-07-01")
    depois = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    novos = depois - antes
    assert all(str(p).startswith("data/") for p in novos)
