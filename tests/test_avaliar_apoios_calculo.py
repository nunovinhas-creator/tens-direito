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


# ── Abono real (dados/condicoes.json de produção) — 3 níveis de aninhamento,
# unidade_comparacao "anos", e os três ramos independentes da excepção
# etária (normal / estudante / deficiência) ─────────────────────────────────


RESPOSTAS_ABONO_BASE = {
    "reside_legalmente_pt": "sim",
    "rendimento_referencia_anual_agregado": 10000,
    "situacao_contributiva_regularizada": "sim",
    "patrimonio_mobiliario_agregado": 5000,
}


def test_abono_real_elegivel_crianca_pequena(pagina):
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_ABONO_BASE, "data_nascimento_crianca": "2020-01-01"}  # 6 anos em 2026
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "elegivel"


def test_abono_real_inelegivel_jovem_18_anos_sem_estudar_sem_deficiencia(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2008-01-01",  # 18 anos em 2026
        "em_estudos_ou_formacao_profissional": "nao",
        "tem_deficiencia_ou_incapacidade_reconhecida": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "inelegivel"


def test_abono_real_elegivel_jovem_18_anos_a_estudar(pagina):
    # Regressão directa do grupo `all` aninhado dentro do `any`: 18 anos
    # falha a idade_normal, mas passa em idade_estudante (≤24 + a estudar).
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2008-01-01",
        "em_estudos_ou_formacao_profissional": "sim",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "elegivel"


def test_abono_real_inelegivel_jovem_18_anos_a_estudar_mas_com_25_anos(pagina):
    # 25 anos: falha idade_normal (>16) e idade_estudante (>24), mesmo a
    # estudar — só a excepção de deficiência salvaria, e foi respondida
    # que não. Os três ramos do grupo `any` ficam resolvidos e inelegíveis.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2001-01-01",  # 25 anos em 2026
        "em_estudos_ou_formacao_profissional": "sim",
        "tem_deficiencia_ou_incapacidade_reconhecida": "nao",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "inelegivel"


def test_abono_real_indeterminado_aos_25_anos_sem_responder_a_deficiencia(pagina):
    # Os dois primeiros ramos (idade_normal, idade_estudante) já estão
    # decididos e inelegíveis, mas o terceiro (deficiência) ainda não foi
    # respondido — o grupo `any` fica indeterminado, nunca inelegível por
    # omissão.
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2001-01-01",
        "em_estudos_ou_formacao_profissional": "sim",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "indeterminado"
    assert r["abono"]["perguntasEmFalta"] == ["tem_deficiencia_ou_incapacidade_reconhecida"]


def test_abono_real_elegivel_por_deficiencia_apesar_de_25_anos(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        **RESPOSTAS_ABONO_BASE,
        "data_nascimento_crianca": "2001-01-01",
        "tem_deficiencia_ou_incapacidade_reconhecida": "sim",
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "elegivel"


def test_abono_real_inelegivel_por_patrimonio_mesmo_com_idade_ok(pagina):
    # Short-circuit do `all` de topo: uma condição de recursos inelegível
    # decide o apoio, independentemente do resultado do grupo de idade.
    condicoes = _condicoes_reais()
    respostas = {**RESPOSTAS_ABONO_BASE, "data_nascimento_crianca": "2020-01-01", "patrimonio_mobiliario_agregado": 200000}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "inelegivel"


def test_abono_real_indeterminado_quando_falta_apenas_situacao_contributiva(pagina):
    condicoes = _condicoes_reais()
    respostas = {
        "data_nascimento_crianca": "2020-01-01",
        "reside_legalmente_pt": "sim",
        "rendimento_referencia_anual_agregado": 10000,
        "patrimonio_mobiliario_agregado": 5000,
        # situacao_contributiva_regularizada em falta
    }
    r = _avaliar(pagina, condicoes, respostas)
    assert r["abono"]["estado"] == "indeterminado"
    assert r["abono"]["perguntasEmFalta"] == ["situacao_contributiva_regularizada"]


# ── ASE real (dados/condicoes.json de produção) ─────────────────────────────


def test_ase_real_elegivel_escola_publica_rendimento_baixo(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 200}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "elegivel"


def test_ase_real_elegivel_no_limite_exacto_do_escalao_b(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 537.13}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "elegivel"


def test_ase_real_inelegivel_rendimento_acima_do_escalao_b(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tipo_escola_aluno": "publica_ou_protocolo", "rendimento_per_capita_mensal_agregado": 600}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "inelegivel"


def test_ase_real_inelegivel_escola_privada_sem_protocolo_mesmo_com_rendimento_baixo(pagina):
    # Short-circuit do `all`: escola privada sem protocolo decide sozinha,
    # sem precisar de saber o rendimento.
    condicoes = _condicoes_reais()
    respostas = {"tipo_escola_aluno": "privada_sem_protocolo"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "inelegivel"


def test_ase_real_indeterminado_quando_falta_rendimento(pagina):
    condicoes = _condicoes_reais()
    respostas = {"tipo_escola_aluno": "publica_ou_protocolo"}
    r = _avaliar(pagina, condicoes, respostas)
    assert r["ase"]["estado"] == "indeterminado"
    assert r["ase"]["perguntasEmFalta"] == ["rendimento_per_capita_mensal_agregado"]


# ── RSI real (dados/condicoes.json de produção) — fórmula da escala de
# equivalência, excepção de menores, e residência em 4 ramos ────────────────


RESPOSTAS_RSI_BASE = {
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
