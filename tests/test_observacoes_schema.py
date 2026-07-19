"""FASE 1 (sessão de dados abertos, 2026-07-19) — dados/observacoes/*.json.

Valida cada ficheiro contra dados/observacoes/schema.json. JSON malformado
ou fora do schema = teste vermelho, nunca um sucesso silencioso (ver
CLAUDE.md "INVARIANTE — NENHUM ESTADO DE ERRO PODE PARECER SUCESSO").
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

RAIZ = Path(__file__).resolve().parent.parent
OBS_DIR = RAIZ / "dados" / "observacoes"
SCHEMA_PATH = OBS_DIR / "schema.json"


def _ficheiros_observacoes():
    """Só descobre os caminhos — nunca faz json.loads() aqui: um ficheiro
    malformado tem de aparecer como UM teste vermelho (o dele), nunca
    rebentar a colheita de testes inteira."""
    if not OBS_DIR.exists():
        return []
    return sorted(p for p in OBS_DIR.glob("*.json") if p.name != "schema.json")


def test_schema_existe_e_e_json_schema_valido():
    assert SCHEMA_PATH.exists(), "dados/observacoes/schema.json em falta"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator.check_schema(schema)


@pytest.mark.parametrize("caminho", _ficheiros_observacoes(), ids=lambda p: p.name)
def test_observacao_bate_com_schema(caminho: Path):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    jsonschema.validate(instance=dados, schema=schema)


def test_slug_bate_com_nome_do_ficheiro():
    for caminho in _ficheiros_observacoes():
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados["fonte"] == caminho.stem, (
            f"{caminho.name}: campo 'fonte' ({dados['fonte']!r}) tem de bater "
            f"com o nome do ficheiro ({caminho.stem!r})"
        )


def test_estado_nao_ok_nunca_tem_valores_extraidos():
    """Um bloqueio (ou qualquer estado != OK) nunca pode gravar
    valores_extraidos como se fosse sucesso — reforça em CI a garantia
    arquitectural de scripts/registar_observacao.py."""
    for caminho in _ficheiros_observacoes():
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if dados["estado"] != "OK":
            assert dados["valores_extraidos"] is None, (
                f"{caminho.name}: estado={dados['estado']} mas valores_extraidos "
                "não é null"
            )
            assert dados.get("motivo"), f"{caminho.name}: estado != OK sem 'motivo'"


def test_pelo_menos_uma_fonte_monitorizada_tem_observacao():
    """Rede de segurança mínima: se dados/observacoes/ existir mas estiver
    vazio (ex.: script nunca correu com sucesso), isso é uma anomalia —
    nunca um estado vazio silencioso."""
    ficheiros = _ficheiros_observacoes()
    if OBS_DIR.exists():
        assert ficheiros, "dados/observacoes/ existe mas está vazio de observações"
