"""
Testes da mecânica de avaliação do motor de apoios (avaliarApoios,
assets/js/calc-apoios.js), executados num browser real (Chromium headless
via Playwright) — mesma filosofia de test_simulador_csi_calculo.py /
test_simulador_abono_calculo.py: o JS real, nunca uma cópia à parte.

PR 3 da série "simulador universal". Os casos-âncora usam o CSI real
(dados/condicoes/csi.yaml compilado em dados/condicoes.json pelo PR 2) —
não uma fixture sintética — para que uma regressão no schema real do CSI
apareça aqui, não só no gerar_condicoes_json.py. O caso do grupo `any`
aninhado (idade normal OU excepção de invalidez) e o de perguntas em
falta usam fixtures sintéticas próprias, para não depender de o CSI
continuar a ter exactamente essa forma no futuro.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import json
import os
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
CALC_APOIOS_JS = (RAIZ / "assets" / "js" / "calc-apoios.js").read_text(encoding="utf-8")
CONDICOES_JSON = RAIZ / "dados" / "condicoes.json"


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


@pytest.fixture()
def pagina():
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALC_APOIOS_JS)
        yield page
        browser.close()


def _avaliar(pagina, condicoes_json, respostas, hoje="2026-09-27"):
    return pagina.evaluate(
        "([condicoesJson, respostas, hoje]) => avaliarApoios(condicoesJson, respostas, hoje)",
        [condicoes_json, respostas, hoje],
    )


# ── CSI real (dados/condicoes.json de produção) ─────────────────────────────


def _condicoes_reais() -> dict:
    if not CONDICOES_JSON.exists():
        pytest.skip("dados/condicoes.json não gerado neste checkout — correr gerar_condicoes_json.py primeiro")
    return json.loads(CONDICOES_JSON.read_text(encoding="utf-8"))


def test_csi_real_elegivel_por_idade_normal(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento_requerente": "1955-01-01",  # bem acima do mínimo em 2026
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "elegivel"


def test_csi_real_inelegivel_por_idade_sem_excepcao(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento_requerente": "2000-01-01",  # jovem, sem excepção de invalidez
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
        "tem_pensao_invalidez_sem_reavaliacao": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "inelegivel"


def test_csi_real_elegivel_por_excepcao_de_invalidez_apesar_da_idade(pagina):
    # Regressão directa da correcção do PR 2: idade normal falha, mas a
    # excepção (grupo `any`) torna o apoio elegível na mesma.
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento_requerente": "2000-01-01",
        "tem_pensao_invalidez_sem_reavaliacao": "sim",
        "reside_legalmente_pt": "sim",
        "anos_residencia_pt": 10,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "elegivel"


def test_csi_real_indeterminado_quando_falta_residencia(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento_requerente": "1955-01-01",
        "reside_legalmente_pt": "sim",
        # anos_residencia_pt em falta — o grupo idade_minima já resolveu
        # (elegivel por idade normal), mas o apoio como um todo ainda não.
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "indeterminado"
    assert "anos_residencia_pt" in r["csi"]["perguntasEmFalta"]


def test_csi_real_inelegivel_por_residencia_mesmo_sem_saber_a_idade(pagina):
    # Short-circuit do operador `all`: uma condição já inelegível decide
    # o apoio, mesmo que a idade nunca tenha sido perguntada — é isto que
    # evita perguntar tudo antes de poder dizer "sem direito".
    condicoes = _condicoes_reais()
    respostas = {"reside_legalmente_pt": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["csi"]["estado"] == "inelegivel"


# ── Fixtures sintéticas — grupo `any` isolado e agregação de perguntas em falta ──


CONDICOES_SINTETICAS_ANY = {
    "apoios": {
        "teste": {
            "operador": "all",
            "condicoes": [
                {
                    "id": "grupo",
                    "operador": "any",
                    "condicoes": [
                        {
                            "id": "a",
                            "tipo": "categorica",
                            "campo": "campo_a",
                            "operador_comparacao": "eq",
                            "valor": "sim",
                        },
                        {
                            "id": "b",
                            "tipo": "categorica",
                            "campo": "campo_b",
                            "operador_comparacao": "eq",
                            "valor": "sim",
                        },
                    ],
                }
            ],
        }
    }
}


def test_grupo_any_elegivel_quando_uma_folha_cumpre_mesmo_com_a_outra_em_falta(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "sim"})
    assert r["teste"]["estado"] == "elegivel"


def test_grupo_any_indeterminado_quando_nenhuma_folha_cumpre_mas_falta_uma(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "nao"})
    assert r["teste"]["estado"] == "indeterminado"
    assert r["teste"]["perguntasEmFalta"] == ["campo_b"]


def test_grupo_any_inelegivel_quando_todas_as_folhas_respondidas_falham(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {"campo_a": "nao", "campo_b": "nao"})
    assert r["teste"]["estado"] == "inelegivel"


def test_apoio_totalmente_indeterminado_sem_nenhuma_resposta(pagina):
    r = _avaliar(pagina, CONDICOES_SINTETICAS_ANY, {})
    assert r["teste"]["estado"] == "indeterminado"
    assert set(r["teste"]["perguntasEmFalta"]) == {"campo_a", "campo_b"}


# ── Vários apoios em simultâneo ──────────────────────────────────────────────


def test_avalia_varios_apoios_independentemente(pagina):
    condicoes = {
        "apoios": {
            "x": {
                "operador": "all",
                "condicoes": [
                    {"id": "c1", "tipo": "categorica", "campo": "f1", "operador_comparacao": "eq", "valor": "sim"}
                ],
            },
            "y": {
                "operador": "all",
                "condicoes": [
                    {"id": "c2", "tipo": "categorica", "campo": "f2", "operador_comparacao": "eq", "valor": "sim"}
                ],
            },
        }
    }
    r = _avaliar(pagina, condicoes, {"f1": "sim", "f2": "nao"})
    assert r["x"]["estado"] == "elegivel"
    assert r["y"]["estado"] == "inelegivel"


# ── Abono real (dados/condicoes.json de produção) — escada etária por nível
# de ensino (art. 11.º n.º 2 do DL 176/2003), 3 níveis de aninhamento e
# unidade_comparacao "anos" ────────────────────────────────────────────────


RESPOSTAS_ABONO_BASE = {
    "tem_filhos_a_cargo": "sim",  # portão do PR 11
    "reside_legalmente_pt": "sim",
    "rendimento_referencia_anual_agregado": 10000,
    "situacao_contributiva_regularizada": "sim",
    "patrimonio_mobiliario_agregado": 5000,
}


def _abono(pagina, nascimento, nivel, deficiencia="nao"):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": nascimento,
        "nivel_ensino_frequentado": nivel,
        "tem_deficiencia_ou_incapacidade_reconhecida": deficiencia,
    }
    return _avaliar(pagina, condicoes, respostas)["abono"]


def test_abono_real_elegivel_crianca_pequena(pagina):
    assert _abono(pagina, "2020-01-01", "nao_estuda")["estado"] == "elegivel"  # 6 anos


def test_abono_real_elegivel_17_anos_no_ensino_basico(pagina):
    assert _abono(pagina, "2009-01-01", "basico_ou_equivalente")["estado"] == "elegivel"  # 17 anos


def test_abono_real_inelegivel_17_anos_sem_estudar(pagina):
    assert _abono(pagina, "2009-01-01", "nao_estuda")["estado"] == "inelegivel"


def test_abono_real_inelegivel_19_anos_no_ensino_basico(pagina):
    # Passou o degrau dos 18 e não frequenta secundário nem superior.
    assert _abono(pagina, "2007-01-01", "basico_ou_equivalente")["estado"] == "inelegivel"  # 19 anos


def test_abono_real_elegivel_17_anos_no_secundario(pagina):
    # Degrau "idade máxima por nível": 17 ≤ 21 e frequenta secundário.
    assert _abono(pagina, "2009-01-01", "secundario_ou_equivalente")["estado"] == "elegivel"


def test_abono_real_elegivel_20_anos_no_secundario(pagina):
    assert _abono(pagina, "2006-01-01", "secundario_ou_equivalente")["estado"] == "elegivel"  # 20 anos


def test_abono_real_inelegivel_22_anos_no_secundario(pagina):
    assert _abono(pagina, "2004-01-01", "secundario_ou_equivalente")["estado"] == "inelegivel"  # 22 anos


def test_abono_real_elegivel_23_anos_no_superior(pagina):
    assert _abono(pagina, "2003-01-01", "superior_ou_equivalente")["estado"] == "elegivel"  # 23 anos


def test_abono_real_inelegivel_25_anos_no_superior(pagina):
    assert _abono(pagina, "2001-01-01", "superior_ou_equivalente")["estado"] == "inelegivel"  # 25 anos


def test_abono_real_elegivel_por_deficiencia_apesar_de_25_anos(pagina):
    assert _abono(pagina, "2001-01-01", "nao_estuda", deficiencia="sim")["estado"] == "elegivel"


def test_abono_real_indeterminado_aos_25_anos_sem_responder_a_deficiencia(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2001-01-01",
        "nivel_ensino_frequentado": "superior_ou_equivalente",
    }
    r = _avaliar(pagina, condicoes, respostas)["abono"]
    assert r["estado"] == "indeterminado"
    assert r["perguntasEmFalta"] == ["tem_deficiencia_ou_incapacidade_reconhecida"]


def test_abono_real_inelegivel_por_patrimonio_mesmo_com_idade_ok(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2020-01-01",
        "patrimonio_mobiliario_agregado": 200000,
    }
    assert _avaliar(pagina, condicoes, respostas)["abono"]["estado"] == "inelegivel"


def test_abono_real_indeterminado_quando_falta_apenas_situacao_contributiva(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "tem_filhos_a_cargo": "sim",
        "data_nascimento_crianca": "2020-01-01",
        "reside_legalmente_pt": "sim",
        "rendimento_referencia_anual_agregado": 10000,
        "patrimonio_mobiliario_agregado": 5000,
    }
    r = _avaliar(pagina, condicoes, respostas)["abono"]
    assert r["estado"] == "indeterminado"
    assert r["perguntasEmFalta"] == ["situacao_contributiva_regularizada"]


# ── ASE real (dados/condicoes.json de produção) ─────────────────────────────


def test_ase_real_elegivel_escola_publica_rendimento_baixo(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 200}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "elegivel"


def test_ase_real_elegivel_no_limite_exacto_do_escalao_b(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 537.13}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "elegivel"


def test_ase_real_inelegivel_rendimento_acima_do_escalao_b(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 600}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "inelegivel"


def test_ase_real_inelegivel_escola_privada_sem_protocolo_mesmo_com_rendimento_baixo(pagina):
    # Short-circuit do `all`: escola privada sem protocolo decide sozinha,
    # sem precisar de saber o rendimento.
    condicoes = _condicoes_reais()
    respostas = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "privada_sem_protocolo"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "inelegivel"


def test_ase_real_indeterminado_quando_falta_rendimento(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "publica_ou_protocolo"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "indeterminado"
    assert r["ase"]["perguntasEmFalta"] == ["rendimento_per_capita_mensal_agregado"]


# ── RSI real (dados/condicoes.json de produção) — fórmula da escala de
# equivalência, excepção de menores, e residência em 4 ramos ────────────────


RESPOSTAS_RSI_BASE = {
    "reside_legalmente_pt": "sim",  # portão do PR 11
    "data_nascimento_requerente": "1990-01-01",  # 36 anos, sem excepção de menor
    "estatuto_residencia": "nacional_pt",
    "rendimento_mensal_agregado": 200,
    "numero_adultos_adicionais_agregado": 0,
    "numero_menores_agregado": 0,
    "patrimonio_mobiliario_pessoal": 1000,
    "situacao_profissional": "empregado",
    "esta_em_estabelecimento_prisional_ou_institucionalizado": "nao",
}


def test_rsi_real_elegivel_caso_simples(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_RSI_BASE)
    assert r["rsi"]["estado"] == "elegivel"


def test_rsi_real_formula_soma_agregado_2_adultos_1_crianca(pagina):
    # Exemplo publicado em rsi.html: 2 adultos + 1 criança → limite = 247,56
    # + 173,29 + 123,78 = 544,63€. Um cêntimo acima já é inelegível.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "numero_adultos_adicionais_agregado": 1,
        "numero_menores_agregado": 1,
        "rendimento_mensal_agregado": 544.63,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "elegivel"

    respostas["rendimento_mensal_agregado"] = 544.64
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_indeterminado_quando_falta_um_dos_tres_campos_da_formula(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_RSI_BASE)
    del respostas["numero_menores_agregado"]
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "indeterminado"
    assert "numero_menores_agregado" in r["rsi"]["perguntasEmFalta"]


def test_rsi_real_inelegivel_por_patrimonio_mesmo_com_rendimento_baixo(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_RSI_BASE, "patrimonio_mobiliario_pessoal": 40000}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_inelegivel_desempregado_nao_inscrito(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "situacao_profissional": "desempregado",
        "inscrito_centro_emprego_e_disponivel": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_elegivel_desempregado_inscrito_e_disponivel(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "situacao_profissional": "desempregado",
        "inscrito_centro_emprego_e_disponivel": "sim",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "elegivel"


def test_rsi_real_indeterminado_desempregado_sem_responder_inscricao(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_RSI_BASE, "situacao_profissional": "desempregado"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "indeterminado"
    assert r["rsi"]["perguntasEmFalta"] == ["inscrito_centro_emprego_e_disponivel"]


def test_rsi_real_inelegivel_institucionalizado(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_RSI_BASE, "esta_em_estabelecimento_prisional_ou_institucionalizado": "sim"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_pais_terceiro_com_menos_de_1_ano_inelegivel(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "estatuto_residencia": "titulo_residencia_valido",
        "anos_residencia_pt": 0,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_pais_terceiro_com_1_ano_elegivel(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "estatuto_residencia": "titulo_residencia_valido",
        "anos_residencia_pt": 1,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "elegivel"


def test_rsi_real_refugiado_elegivel_sem_prazo_de_residencia(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_RSI_BASE, "estatuto_residencia": "refugiado"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "elegivel"


def test_rsi_real_menor_inelegivel_sem_excepcao(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "data_nascimento_requerente": "2015-01-01",  # 11 anos
        "rendimento_mensal_proprio_menor": 0,
        "esta_gravida": "nao",
        "casado_ou_uniao_facto_mais_de_2_anos": "nao",
        "tem_menores_ou_pessoas_deficiencia_a_cargo": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


def test_rsi_real_menor_elegivel_por_excepcao_rendimentos_e_gravidez(pagina):
    # Regressão directa da excepção de menores: rendimentos próprios acima
    # do limite (173,29€) E grávida — os dois ramos exigidos pelo `all`.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "data_nascimento_requerente": "2015-01-01",
        "rendimento_mensal_proprio_menor": 200,
        "esta_gravida": "sim",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "elegivel"


def test_rsi_real_menor_inelegivel_rendimentos_altos_mas_sem_situacao_pessoal(pagina):
    # Rendimentos próprios acima do limite não chega sozinho — falta uma
    # das três situações pessoais (grávida/casada/dependentes a cargo).
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_RSI_BASE,
        "data_nascimento_requerente": "2015-01-01",
        "rendimento_mensal_proprio_menor": 200,
        "esta_gravida": "nao",
        "casado_ou_uniao_facto_mais_de_2_anos": "nao",
        "tem_menores_ou_pessoas_deficiencia_a_cargo": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["rsi"]["estado"] == "inelegivel"


# ── Subsídio de Desemprego real (dados/condicoes.json de produção) ──────────


RESPOSTAS_DESEMPREGO_BASE = {
    "situacao_profissional": "desempregado",
    "desemprego_involuntario": "sim",
    "dias_registo_remuneracoes_24_meses": 400,
    "inscrito_centro_emprego_e_disponivel": "sim",
    "situacao_contributiva_regularizada": "sim",
}


def test_desemprego_real_elegivel_caso_simples(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_DESEMPREGO_BASE)
    assert r["desemprego"]["estado"] == "elegivel"


def test_desemprego_real_inelegivel_se_nao_desempregado(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "situacao_profissional": "empregado"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "inelegivel"


def test_desemprego_real_inelegivel_se_voluntario(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "desemprego_involuntario": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "inelegivel"


def test_desemprego_real_inelegivel_sem_prazo_de_garantia(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "dias_registo_remuneracoes_24_meses": 300}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "inelegivel"


def test_desemprego_real_elegivel_no_limite_exacto_do_prazo_de_garantia(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "dias_registo_remuneracoes_24_meses": 360}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "elegivel"


def test_desemprego_real_inelegivel_sem_inscricao_iefp(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "inscrito_centro_emprego_e_disponivel": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "inelegivel"


def test_desemprego_real_inelegivel_situacao_contributiva_irregular(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DESEMPREGO_BASE, "situacao_contributiva_regularizada": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "inelegivel"


def test_desemprego_real_indeterminado_quando_falta_prazo_de_garantia(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_DESEMPREGO_BASE)
    del respostas["dias_registo_remuneracoes_24_meses"]
    r = _avaliar(pagina, condicoes, respostas)
    assert r["desemprego"]["estado"] == "indeterminado"
    assert r["desemprego"]["perguntasEmFalta"] == ["dias_registo_remuneracoes_24_meses"]


def test_desemprego_real_inelegivel_sem_saber_prazo_de_garantia_se_ja_empregado(pagina):
    # Short-circuit: já sabemos que não está desempregado, decide sozinho.
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, {"situacao_profissional": "empregado"})
    assert r["desemprego"]["estado"] == "inelegivel"


# ── Subsídio de Doença real (dados/condicoes.json de produção) — grupos
# `any` por regime (profissionalidade só conta de outrem, situação
# contributiva só independentes) ────────────────────────────────────────────


RESPOSTAS_DOENCA_BASE = {
    "tem_cit_valido": "sim",
    "tipo_trabalhador": "conta_outrem",
    "meses_civis_com_registo_remuneracoes": 12,
    "dias_registo_remuneracoes_indice_profissionalidade": 15,
    "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
    "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
}


def test_doenca_real_elegivel_conta_de_outrem(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_DOENCA_BASE)
    assert r["subsidio-doenca"]["estado"] == "elegivel"


def test_doenca_real_inelegivel_sem_cit(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DOENCA_BASE, "tem_cit_valido": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_inelegivel_sem_prazo_de_garantia(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DOENCA_BASE, "meses_civis_com_registo_remuneracoes": 5}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_elegivel_no_limite_exacto_de_6_meses_e_12_dias(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_DOENCA_BASE,
        "meses_civis_com_registo_remuneracoes": 6,
        "dias_registo_remuneracoes_indice_profissionalidade": 12,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "elegivel"


def test_doenca_real_conta_de_outrem_inelegivel_sem_profissionalidade(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DOENCA_BASE, "dias_registo_remuneracoes_indice_profissionalidade": 11}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_independente_nao_precisa_de_profissionalidade(pagina):
    # Art. 12.º n.º 2: independentes estão isentos — o grupo `any` resolve
    # pelo ramo "isento_independente", sem perguntar os dias.
    condicoes = _condicoes_reais()
    respostas = {
        "tem_cit_valido": "sim",
        "tipo_trabalhador": "independente",
        "meses_civis_com_registo_remuneracoes": 12,
        "situacao_contributiva_regularizada": "sim",
        "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
        "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "elegivel"


def test_doenca_real_independente_inelegivel_com_contributiva_irregular(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "tem_cit_valido": "sim",
        "tipo_trabalhador": "independente",
        "meses_civis_com_registo_remuneracoes": 12,
        "situacao_contributiva_regularizada": "nao",
        "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
        "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_conta_de_outrem_nao_precisa_de_situacao_contributiva(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_DOENCA_BASE)  # sem situacao_contributiva_regularizada
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "elegivel"


def test_doenca_real_inelegivel_acumulacao_pensao_invalidez_relativa(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DOENCA_BASE, "acumula_pensao_invalidez_relativa_com_trabalho": "sim"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_inelegivel_indemnizacao_igual_ou_superior(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_DOENCA_BASE, "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "sim"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_indeterminado_conta_de_outrem_sem_dias_de_profissionalidade(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_DOENCA_BASE)
    del respostas["dias_registo_remuneracoes_indice_profissionalidade"]
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "indeterminado"
    assert r["subsidio-doenca"]["perguntasEmFalta"] == ["dias_registo_remuneracoes_indice_profissionalidade"]


def test_doenca_real_ssv_nao_maritimo_tem_de_cumprir_profissionalidade(pagina):
    # Só independentes e marítimos SSV estão isentos: o SSV comum cumpre o
    # índice como a regra geral.
    condicoes = _condicoes_reais()
    respostas = {
        "tem_cit_valido": "sim",
        "tipo_trabalhador": "seguro_social_voluntario",
        "meses_civis_com_registo_remuneracoes": 12,
        "dias_registo_remuneracoes_indice_profissionalidade": 5,
        "situacao_contributiva_regularizada": "sim",
        "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
        "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


def test_doenca_real_ssv_maritimo_isento_de_profissionalidade(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "tem_cit_valido": "sim",
        "tipo_trabalhador": "seguro_social_voluntario_maritimo",
        "meses_civis_com_registo_remuneracoes": 12,
        "situacao_contributiva_regularizada": "sim",
        "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
        "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "elegivel"


def test_doenca_real_ssv_inelegivel_com_situacao_contributiva_irregular(pagina):
    # A situação contributiva aplica-se a independentes E a todo o SSV.
    condicoes = _condicoes_reais()
    respostas = {
        "tem_cit_valido": "sim",
        "tipo_trabalhador": "seguro_social_voluntario_maritimo",
        "meses_civis_com_registo_remuneracoes": 12,
        "situacao_contributiva_regularizada": "nao",
        "acumula_pensao_invalidez_relativa_com_trabalho": "nao",
        "recebe_indemnizacao_acidente_trabalho_maior_subsidio": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["subsidio-doenca"]["estado"] == "inelegivel"


# ── IMT Jovem real (dados/condicoes.json de produção) ───────────────────────


RESPOSTAS_IMT_BASE = {
    "data_nascimento_requerente": "1996-01-01",  # 30 anos em 2026
    "e_dependente_irs": "nao",
    "titular_imovel_habitacional_ultimos_3_anos": "nao",
    "destino_habitacao_propria_permanente": "sim",
}


def test_imt_jovem_real_elegivel_caso_simples(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_IMT_BASE)
    assert r["imt-jovem"]["estado"] == "elegivel"


def test_imt_jovem_real_elegivel_aos_35_anos_inclusive(pagina):
    condicoes = _condicoes_reais()
    # Nasceu a 1991-01-01: a 2026-09-27 tem 35 anos completos.
    respostas = {**RESPOSTAS_IMT_BASE, "data_nascimento_requerente": "1991-01-01"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "elegivel"


def test_imt_jovem_real_inelegivel_aos_36_anos(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_IMT_BASE, "data_nascimento_requerente": "1990-01-01"}  # 36 anos
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "inelegivel"


def test_imt_jovem_real_inelegivel_se_dependente_irs(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_IMT_BASE, "e_dependente_irs": "sim"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "inelegivel"


def test_imt_jovem_real_inelegivel_com_imovel_habitacional_recente(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_IMT_BASE, "titular_imovel_habitacional_ultimos_3_anos": "sim"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "inelegivel"


def test_imt_jovem_real_inelegivel_se_nao_for_habitacao_propria_permanente(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_IMT_BASE, "destino_habitacao_propria_permanente": "nao"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "inelegivel"


def test_imt_jovem_real_indeterminado_quando_falta_uma_resposta(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_IMT_BASE)
    del respostas["e_dependente_irs"]
    r = _avaliar(pagina, condicoes, respostas)
    assert r["imt-jovem"]["estado"] == "indeterminado"
    assert r["imt-jovem"]["perguntasEmFalta"] == ["e_dependente_irs"]


def test_imt_jovem_real_inelegivel_sem_saber_o_resto_se_ja_passou_a_idade(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, {"data_nascimento_requerente": "1980-01-01"})
    assert r["imt-jovem"]["estado"] == "inelegivel"


# ── PSU real (dados/condicoes.json de produção) — fórmula psu_valor_positivo
# (PSUbase + CIT − rendimentos, com mínimo) e marca de substituição do RSI ──


RESPOSTAS_PSU_BASE = {
    "data_nascimento_requerente": "1990-01-01",  # 36 anos
    "reside_legalmente_pt": "sim",
    "estatuto_residencia": "nacional_pt",
    "rendimento_trabalho_mensal_agregado": 0,
    "outros_rendimentos_mensais_agregado": 100,
    "numero_adultos_adicionais_agregado": 0,
    "numero_menores_agregado": 0,
    "patrimonio_mobiliario_pessoal": 1000,
}


def test_psu_real_elegivel_caso_simples(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_PSU_BASE)
    assert r["psu"]["estado"] == "elegivel"


def test_psu_real_inelegivel_menor_de_18_anos(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_PSU_BASE, "data_nascimento_requerente": "2010-01-01"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "inelegivel"


def test_psu_real_cit_permite_rendimento_de_trabalho_acima_do_psubase(pagina):
    # 300€ de trabalho > PSUbase (268,57€), mas a CIT (203,71€) mantém o
    # valor da prestação positivo (172,28€). Um limiar simples "rendimento ≤
    # PSUbase" diria "sem direito" — e estaria errado.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_PSU_BASE,
        "rendimento_trabalho_mensal_agregado": 300,
        "outros_rendimentos_mensais_agregado": 0,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "elegivel"


def test_psu_real_inelegivel_com_rendimento_de_trabalho_muito_alto(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_PSU_BASE,
        "rendimento_trabalho_mensal_agregado": 1500,
        "outros_rendimentos_mensais_agregado": 0,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "inelegivel"


def test_psu_real_outros_rendimentos_nao_beneficiam_da_cit(pagina):
    # O mesmo valor, mas de rendimentos que não são de trabalho: sem CIT,
    # 300€ ultrapassam o PSUbase e o agregado deixa de ter direito.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_PSU_BASE,
        "rendimento_trabalho_mensal_agregado": 0,
        "outros_rendimentos_mensais_agregado": 300,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "inelegivel"


def test_psu_real_agregado_maior_aumenta_o_limite(pagina):
    # 2 adultos + 1 menor: 268,565 × (1 + 0,7 + 0,5) = 590,84€.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_PSU_BASE,
        "numero_adultos_adicionais_agregado": 1,
        "numero_menores_agregado": 1,
        "outros_rendimentos_mensais_agregado": 500,
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "elegivel"


def test_psu_real_indeterminado_quando_falta_rendimento(pagina):
    condicoes = _condicoes_reais()
    respostas = dict(RESPOSTAS_PSU_BASE)
    del respostas["outros_rendimentos_mensais_agregado"]
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "indeterminado"
    assert r["psu"]["perguntasEmFalta"] == ["outros_rendimentos_mensais_agregado"]


def test_psu_real_estrangeiro_sem_1_ano_inelegivel(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_PSU_BASE, "estatuto_residencia": "titulo_residencia_valido", "anos_residencia_pt": 0}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "inelegivel"


def test_psu_real_estrangeiro_com_1_ano_elegivel(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_PSU_BASE, "estatuto_residencia": "titulo_residencia_valido", "anos_residencia_pt": 1}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "elegivel"


def test_psu_real_inelegivel_por_patrimonio(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_PSU_BASE, "patrimonio_mobiliario_pessoal": 40000}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["psu"]["estado"] == "inelegivel"


def test_rsi_real_marcado_como_substituido_pela_psu(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_RSI_BASE)
    assert r["rsi"]["substituidoPor"] == "psu"
    assert r["rsi"]["substituidoAPartirDe"] == "2026-12-31"
    # A marca não altera a elegibilidade do RSI até à data de substituição.
    assert r["rsi"]["estado"] == "elegivel"


def test_apoios_sem_substituicao_nao_tem_a_marca(pagina):
    condicoes = _condicoes_reais()
    r = _avaliar(pagina, condicoes, RESPOSTAS_PSU_BASE)
    assert "substituidoPor" not in r["psu"]
    assert "substituidoPor" not in r["csi"]


# ── PR 11: proximaPergunta (escolha dinâmica da próxima pergunta) ───────────


def _proxima(pagina, condicoes_json, respostas, hoje="2026-09-27"):
    return pagina.evaluate(
        "([c, r, h]) => proximaPergunta(c, r, h)",
        [condicoes_json, respostas, hoje],
    )


def _folha(id_, campo):
    return {"id": id_, "tipo": "categorica", "campo": campo, "operador_comparacao": "eq", "valor": "sim"}


def _sintetico(perguntas_ordem, apoios, monetarios=(), filhos=()):
    """perguntas_ordem: lista de campos (a ordem é o desempate). apoios: {id: [campos]} (all de folhas eq sim)."""
    perguntas = {}
    for campo in perguntas_ordem:
        if campo in monetarios:
            perguntas[campo] = {"tipo": "numero", "unidade": "EUR/mês"}
        else:
            perguntas[campo] = {"tipo": "categorica", "opcoes": ["sim", "nao"]}
        if campo in filhos:
            perguntas[campo]["aplicavel_se"] = {"campo": "tem_filhos_a_cargo", "valor": "sim"}
    return {
        "perguntas": perguntas,
        "apoios": {
            a: {"operador": "all", "condicoes": [
                ({"id": f"{a}_{c}", "tipo": "limiar", "campo": c, "operador_comparacao": "lte", "valor": 100}
                 if c in monetarios else _folha(f"{a}_{c}", c))
                for c in campos]}
            for a, campos in apoios.items()
        },
    }


def test_proxima_pergunta_primeira_e_a_que_aparece_em_mais_apoios(pagina):
    c = _sintetico(["f3", "f2", "f1"], {"a": ["f1", "f2"], "b": ["f1"], "c": ["f1", "f3"]})
    assert _proxima(pagina, c, {}) == "f1"  # 3 apoios, apesar de ser o último em perguntas.yaml


def test_proxima_pergunta_rendimentos_ficam_sempre_no_fim(pagina):
    c = _sintetico(["renda", "f1"], {"a": ["renda", "f1"], "b": ["renda"], "c": ["renda"]}, monetarios={"renda"})
    assert _proxima(pagina, c, {}) == "f1"  # apesar de "renda" estar em 3 apoios e aparecer primeiro
    assert _proxima(pagina, c, {"f1": "sim"}) == "renda"


def test_proxima_pergunta_da_crianca_so_com_filhos_e_depois_do_requerente(pagina):
    condicoes = _condicoes_reais()
    perguntas = condicoes["perguntas"]
    filhos = {c for c, d in perguntas.items() if (d.get("aplicavel_se") or {}).get("campo") == "tem_filhos_a_cargo"}
    assert filhos, "esperava perguntas da criança com aplicavel_se em tem_filhos_a_cargo"

    def percorrer(tem_filhos):
        respostas, ordem = {}, []
        for _ in range(80):
            campo = _proxima(pagina, condicoes, respostas)
            if campo is None:
                return ordem, respostas
            ordem.append(campo)
            d = perguntas[campo]
            if campo == "tem_filhos_a_cargo":
                respostas[campo] = tem_filhos
            elif d["tipo"] == "categorica":
                respostas[campo] = d["opcoes"][0]
            elif d["tipo"] == "data":
                respostas[campo] = "2018-06-01"
            else:
                respostas[campo] = 1
        raise AssertionError("proximaPergunta não terminou")

    ordem_sem, _ = percorrer("nao")
    assert not filhos & set(ordem_sem), "perguntou pela criança a quem disse que não tem filhos"

    ordem_com, _ = percorrer("sim")
    perguntas_crianca = [c for c in ordem_com if c in filhos]
    assert perguntas_crianca, "com filhos, as perguntas da criança têm de aparecer"
    primeira_crianca = ordem_com.index(perguntas_crianca[0])
    assert ordem_com.index("tem_filhos_a_cargo") < primeira_crianca
    nao_monetarias_requerente = [
        c for c in ordem_com
        if c not in filhos and "EUR" not in str(perguntas[c].get("unidade", ""))
    ]
    assert all(ordem_com.index(c) < primeira_crianca for c in nao_monetarias_requerente), (
        "perguntas do requerente têm de vir antes das da criança"
    )


def test_proxima_pergunta_devolve_null_no_fim_e_nada_fica_por_decidir(pagina):
    c = _sintetico(["f1", "f2"], {"a": ["f1", "f2"]})
    assert _proxima(pagina, c, {"f1": "sim", "f2": "nao"}) is None

    condicoes = _condicoes_reais()
    respostas = {}
    for _ in range(80):
        campo = _proxima(pagina, condicoes, respostas)
        if campo is None:
            break
        d = condicoes["perguntas"][campo]
        respostas[campo] = d["opcoes"][-1] if d["tipo"] == "categorica" else ("1980-01-01" if d["tipo"] == "data" else 0)
    else:
        raise AssertionError("proximaPergunta não terminou")
    estados = {a: r["estado"] for a, r in _avaliar(pagina, condicoes, respostas).items()}
    assert "indeterminado" not in estados.values(), estados


def test_proxima_pergunta_ignora_apoios_ja_decididos(pagina):
    c = _sintetico(["f1", "f2", "f3"], {"a": ["f1", "f2"], "b": ["f2", "f3"], "c": ["f3"]})
    assert _proxima(pagina, c, {}) == "f2"  # empate f2/f3 (2 apoios) → ordem de perguntas.yaml
    # "a" fica inelegível com f1 = nao: f2 passa a contar só para "b", f3 continua em "b" e "c".
    assert _proxima(pagina, c, {"f1": "nao"}) == "f3"


def test_proxima_pergunta_desempate_estavel_pela_ordem_de_perguntas(pagina):
    c1 = _sintetico(["x", "y"], {"a": ["y"], "b": ["x"]})
    c2 = _sintetico(["y", "x"], {"a": ["y"], "b": ["x"]})
    assert _proxima(pagina, c1, {}) == "x"
    assert _proxima(pagina, c2, {}) == "y"
    # determinístico: nem a ordem das respostas nem chamadas repetidas mudam nada
    c3 = _sintetico(["x", "y", "z"], {"a": ["z", "y"], "b": ["z", "x"]})
    assert _proxima(pagina, c3, {"z": "sim"}) == _proxima(pagina, c3, {"z": "sim"}) == "x"


# ── PR 11: portões (quem responde "não" sai logo de "falta saber") ──────────


def test_abono_e_ase_reais_inelegiveis_sem_filhos_a_cargo(pagina):
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "nao"})
    assert r["abono"]["estado"] == "inelegivel"
    assert r["ase"]["estado"] == "inelegivel"


def test_rsi_csi_psu_reais_inelegiveis_sem_residencia_legal(pagina):
    r = _avaliar(pagina, _condicoes_reais(), {"reside_legalmente_pt": "nao"})
    for apoio in ("rsi", "csi", "psu"):
        assert r[apoio]["estado"] == "inelegivel", apoio


def test_ase_e_psu_nunca_elegiveis_sem_a_pergunta_de_rendimento(pagina):
    # Tudo o resto respondido a favor; só falta o rendimento → nunca "elegivel".
    condicoes = _condicoes_reais()
    ase = {"tem_filhos_a_cargo": "sim", "tipo_escola_aluno": "publica_ou_protocolo"}
    assert _avaliar(pagina, condicoes, ase)["ase"]["estado"] == "indeterminado"
    assert _avaliar(pagina, condicoes, {**ase, "rendimento_per_capita_mensal_agregado": 0})["ase"]["estado"] == "elegivel"

    psu = {k: v for k, v in RESPOSTAS_PSU_BASE.items()
           if k not in ("rendimento_trabalho_mensal_agregado", "outros_rendimentos_mensais_agregado")}
    for so_um in ({"rendimento_trabalho_mensal_agregado": 0}, {"outros_rendimentos_mensais_agregado": 0}, {}):
        assert _avaliar(pagina, condicoes, {**psu, **so_um})["psu"]["estado"] == "indeterminado", so_um
    assert _avaliar(pagina, condicoes, {**psu, "rendimento_trabalho_mensal_agregado": 0,
                                        "outros_rendimentos_mensais_agregado": 0})["psu"]["estado"] == "elegivel"


# ── PR 12: creche gratuita real (dados/condicoes.json de produção) ──────────
# Única condição de acesso própria: nascida a partir de 1/9/2021, inclusive
# (Portaria n.º 305/2022, art. 5.º/1/a) e art. 2.º, redação da Portaria n.º
# 158/2024/1). Comparação de datas ISO, sem conversão para idade.


def _data_creche(condicoes):
    cond = {c["id"]: c for c in condicoes["apoios"]["creche"]["condicoes"]}
    return cond["nascida_a_partir_da_data_elegivel"]["valor"]


def test_creche_real_elegivel_crianca_pequena(pagina):
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": "2025-03-10"})
    assert r["creche"]["estado"] == "elegivel"


# Os testes da data-limite avaliam "hoje" a 2022-09-01 (efeitos da Portaria
# n.º 304/2022): a criança tem 1 ano, a condição de idade cumpre-se e só a
# de data decide. A 2026 uma criança de 2021 já não passa na idade.
HOJE_DATA_LIMITE = "2022-09-01"


def test_creche_real_elegivel_no_dia_exacto_da_data_limite(pagina):
    condicoes = _condicoes_reais()
    limite = _data_creche(condicoes)
    r = _avaliar(pagina, condicoes, {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": limite},
                 hoje=HOJE_DATA_LIMITE)
    assert r["creche"]["estado"] == "elegivel"


def test_creche_real_inelegivel_na_vespera_da_data_limite(pagina):
    from datetime import date, timedelta
    condicoes = _condicoes_reais()
    vespera = (date.fromisoformat(_data_creche(condicoes)) - timedelta(days=1)).isoformat()
    r = _avaliar(pagina, condicoes, {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": vespera},
                 hoje=HOJE_DATA_LIMITE)
    assert r["creche"]["estado"] == "inelegivel"


def test_creche_real_comparacao_por_data_nao_por_string_de_mes(pagina):
    # 2021-10-01 > 2021-09-01: garante que a comparação é cronológica
    # (mês de dois dígitos), não uma coincidência de prefixo.
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": "2021-10-01"},
                 hoje=HOJE_DATA_LIMITE)
    assert r["creche"]["estado"] == "elegivel"


def test_creche_real_portao_sem_filhos_decide_sozinho(pagina):
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "nao"})
    assert r["creche"]["estado"] == "inelegivel"


def test_creche_real_indeterminado_quando_falta_a_data_de_nascimento(pagina):
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "sim"})
    assert r["creche"]["estado"] == "indeterminado"
    assert r["creche"]["perguntasEmFalta"] == ["data_nascimento_crianca"]


def test_creche_real_sem_respostas_pergunta_primeiro_pelos_filhos(pagina):
    condicoes = {**_condicoes_reais()}
    condicoes["apoios"] = {"creche": condicoes["apoios"]["creche"]}
    assert _proxima(pagina, condicoes, {}) == "tem_filhos_a_cargo"
    assert _proxima(pagina, condicoes, {"tem_filhos_a_cargo": "nao"}) is None
    assert _proxima(pagina, condicoes, {"tem_filhos_a_cargo": "sim"}) == "data_nascimento_crianca"



# ── PR 12 (revisão): idade máxima da creche — "até aos 3 anos" ──────────────
# Portaria n.º 198/2022, art. 9.º, n.º 4 (redação da Portaria n.º 304/2022),
# aplicável às aderentes pelo art. 9.º da Portaria n.º 305/2022. Idade em
# anos completos à data da avaliação ("hoje" dos testes: 2026-09-27):
# < 3 provável; 3 (até antes dos 4) indeterminado, com motivo; ≥ 4 inelegível.

MOTIVO_CRECHE = "a regra diz «até aos 3 anos» mas não fixa se é no aniversário ou no fim do ano letivo"


def _creche(pagina, nascimento, hoje="2026-09-27"):
    return _avaliar(pagina, _condicoes_reais(),
                    {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": nascimento}, hoje)["creche"]


def test_creche_idade_vespera_do_3_aniversario_ainda_provavel(pagina):
    assert _creche(pagina, "2023-09-28")["estado"] == "elegivel"  # 2 anos, faz 3 amanhã


def test_creche_idade_dia_exacto_do_3_aniversario_indeterminado_com_motivo(pagina):
    r = _creche(pagina, "2023-09-27")  # faz 3 anos hoje
    assert r["estado"] == "indeterminado"
    assert r["perguntasEmFalta"] == []
    assert r["motivos"] == [MOTIVO_CRECHE]


def test_creche_idade_vespera_do_4_aniversario_ainda_indeterminado(pagina):
    r = _creche(pagina, "2022-09-28")  # 3 anos, faz 4 amanhã
    assert r["estado"] == "indeterminado"
    assert r["motivos"] == [MOTIVO_CRECHE]


def test_creche_idade_dia_exacto_do_4_aniversario_inelegivel(pagina):
    assert _creche(pagina, "2022-09-27")["estado"] == "inelegivel"  # faz 4 anos hoje


@pytest.mark.parametrize("nascimento", ["2021-09-01", "2021-12-31", "2022-06-15", "2023-01-01", "2023-09-27"])
def test_creche_criancas_nascidas_2021_2023_ja_nao_sao_provaveis(pagina, nascimento):
    # Todas cumprem a data de 1/9/2021 — é a idade que as tira de "provável".
    assert _creche(pagina, nascimento)["estado"] != "elegivel"


def test_creche_motivo_so_aparece_quando_a_idade_e_que_decide(pagina):
    # Sem filhos a cargo, o portão decide — nenhum motivo de idade herdado.
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "nao"})["creche"]
    assert r["estado"] == "inelegivel" and "motivos" not in r
    # Criança em idade de dúvida mas ainda sem data respondida: só falta a data.
    r = _avaliar(pagina, _condicoes_reais(), {"tem_filhos_a_cargo": "sim"})["creche"]
    assert r["perguntasEmFalta"] == ["data_nascimento_crianca"] and "motivos" not in r


def test_faixa_incerta_sintetica_propaga_motivo_por_grupo_all_e_any(pagina):
    folha = {"id": "f", "tipo": "limiar_faixa_incerta", "campo": "n", "valor": 3, "valor_exclusao": 4,
             "unidade_comparacao": None, "motivo_indeterminado": "m"}
    outra = {"id": "o", "tipo": "categorica", "campo": "c", "operador_comparacao": "eq", "valor": "sim"}
    base = {"perguntas": {}, "apoios": {
        "all": {"operador": "all", "condicoes": [folha, outra]},
        "any": {"operador": "any", "condicoes": [folha, outra]},
    }}
    r = _avaliar(pagina, base, {"n": 3, "c": "nao"})
    assert r["all"]["estado"] == "inelegivel"            # uma falha decide o "all"
    assert r["any"] == {"estado": "indeterminado", "perguntasEmFalta": [], "motivos": ["m"]}
    r = _avaliar(pagina, base, {"n": 3, "c": "sim"})
    assert r["all"] == {"estado": "indeterminado", "perguntasEmFalta": [], "motivos": ["m"]}
    assert r["any"]["estado"] == "elegivel"              # uma alternativa cumpre o "any"
    assert _avaliar(pagina, base, {"n": 2.9, "c": "sim"})["all"]["estado"] == "elegivel"
    assert _avaliar(pagina, base, {"n": 4, "c": "sim"})["all"]["estado"] == "inelegivel"



# ── PR 12 (revisão 2): texto próprio quando a idade exclui (4+ anos) ─────────

MOTIVO_CRECHE_4_ANOS = ("A creche gratuita aplica-se a crianças até aos 3 anos. Pela data indicada, o teu filho "
                        "mais novo terá ultrapassado essa idade. Confirma no guia completo.")


def _motivos_exclusao(pagina, respostas, hoje="2026-09-27"):
    return pagina.evaluate(
        "([c, r, h]) => motivosQueExcluem(c.apoios.creche, r, h)", [_condicoes_reais(), respostas, hoje])


def test_creche_4_anos_tem_motivo_proprio(pagina):
    r = {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": "2022-09-27"}  # faz 4 hoje
    assert _motivos_exclusao(pagina, r) == [MOTIVO_CRECHE_4_ANOS]


def test_creche_motivo_de_4_anos_nunca_aparece_fora_dessa_zona(pagina):
    for nascimento in ("2023-09-27", "2022-09-28", "2024-09-27"):  # 3, 3, 2 anos
        assert _motivos_exclusao(pagina, {"tem_filhos_a_cargo": "sim", "data_nascimento_crianca": nascimento}) == []
    # Sem filhos: é o portão que exclui, e esse não tem texto próprio.
    assert _motivos_exclusao(pagina, {"tem_filhos_a_cargo": "nao"}) == []
