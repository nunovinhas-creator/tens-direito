"""
Testes da mecânica de cálculo do simulador de condições de acesso à
reforma (simulador-condicoes-reforma.html), executados num browser real
(Chromium headless via Playwright) — extrai o JS inline directamente do
HTML real, nunca uma cópia à parte (mesma filosofia de
test_simulador_rsi_calculo.py/test_simulador_subsidio_desemprego_calculo.py).

Este simulador é diferente dos restantes: não calcula valores em euros,
só CONDIÇÕES DE ACESSO — responde a «já posso reformar-me, e por que
via?». Cobre a matriz de casos-limite obrigatórios do brief da sessão
(ver dados/parametros/pensoes.yaml para os limiares e a fonte legal):

1. Fronteira dos 17 anos (art. 21.º-A n.º 1 b) — início "inferior a 17",
   nunca "até 17 anos, inclusive").
2. Serviço militar decisivo (art. 48.º — só conta mediante requerimento).
3. Limite dos 60 anos na idade pessoal (art. 20.º n.º 8 — redução
   relativa + piso legal, nunca um valor absoluto).
4. Prazo de garantia não cumprido (art. 19.º — para tudo, sem vias).
5. Elegibilidade por duas vias em simultâneo (carreiras muito longas E
   flexibilização) — o simulador nunca escolhe uma só.

Se o Chromium do Playwright não estiver disponível no ambiente onde os
testes correm, o módulo inteiro é ignorado (skip) em vez de falhar.
"""
import glob
import json
import os
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
PARAMETROS_JSON = RAIZ / "dados" / "parametros.json"
SIMULADOR_HTML = (RAIZ / "simulador-condicoes-reforma.html").read_text(encoding="utf-8")


def _extrair_script_inline(texto: str, marcador: str, nome_ficheiro: str) -> str:
    for m in re.finditer(r"<script>([\s\S]*?)</script>", texto):
        if marcador in m.group(1):
            return m.group(1)
    raise AssertionError(f"Não encontrei nenhum <script> inline com '{marcador}' em {nome_ficheiro}")


CALCULO_JS = _extrair_script_inline(SIMULADOR_HTML, "function calcularCondicoesReforma", "simulador-condicoes-reforma.html")


def _localizar_chromium():
    """Mesma estratégia de localização multi-nível já usada nos outros
    simuladores — nunca assumir uma única convenção de path entre
    sandbox de desenvolvimento e CI (ver histórico em CLAUDE.md)."""
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
    """Página em branco + só o <script> de cálculo injectado — para os
    testes das funções puras (calcularCondicoesReforma/
    validarInputCondicoesReforma/calcularIdadeAnosMeses/arredondarAnos),
    sem depender de nenhum elemento de formulário."""
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=_CHROMIUM_PATH)
        page = browser.new_page()
        page.set_content("<!DOCTYPE html><html><head></head><body></body></html>")
        page.add_script_tag(content=CALCULO_JS)
        yield page
        browser.close()


def _parametros_pensoes_de_producao() -> dict:
    """Lê dados/parametros.json (a fonte real) e monta o mesmo formato
    que PARAMETROS_CONDICOES_REFORMA tem em runtime (ver
    carregarParametrosCondicoesReforma() em
    simulador-condicoes-reforma.html) — nunca valores hardcoded aqui."""
    todos = json.loads(PARAMETROS_JSON.read_text(encoding="utf-8"))
    p = todos["prestacoes"]["pensoes"]
    return {
        "prazoGarantiaVelhiceAnos": p["prazo_garantia_velhice_anos_civis"],
        "clViaAIdadeMinima": p["carreiras_longas_via_a_idade_minima"],
        "clViaAAnosMinimos": p["carreiras_longas_via_a_anos_civis_minimos"],
        "clViaBIdadeMinima": p["carreiras_longas_via_b_idade_minima"],
        "clViaBAnosMinimos": p["carreiras_longas_via_b_anos_civis_minimos"],
        "clViaBIdadeInicioLimite": p["carreiras_longas_via_b_idade_inicio_limite"],
        "flexIdadeMinima": p["flexibilizacao_idade_minima"],
        "flexAnosMinimos": p["flexibilizacao_anos_registo_minimos"],
        "idadePessoalReducaoMesesPorAno": p["idade_pessoal_reducao_meses_por_ano"],
        "idadePessoalIdadeMinima": p["idade_pessoal_idade_minima_absoluta"],
        "mesmaEmpresaAnosProibicao": p["antecipada_mesma_empresa_anos_proibicao"],
    }


PARAMS_DEFAULT = _parametros_pensoes_de_producao()

# Referência fixa de "hoje" (ano/mês) para todos os testes — determinismo
# total, nunca dependente do relógio do runner.
ANO_REF = 2026
MES_REF = 9

ENTRADA_DEFAULT = {
    "anoReferencia": ANO_REF,
    "mesReferencia": MES_REF,
    "anosCarreira": 20,
    "idadeInicioDescontos": None,
    "servicoMilitarSemDescontos": False,
    "mesesServicoMilitar": 0,
    "mesmaEmpresa": False,
}


def _nascimento_para_idade(anos_completos, meses_completos=0):
    """Devolve (anoNascimento, mesNascimento) tal que, à referência fixa
    ANO_REF/MES_REF, a idade calculada seja exactamente
    (anos_completos, meses_completos)."""
    total_meses_ref = ANO_REF * 12 + (MES_REF - 1)
    total_meses_nasc = total_meses_ref - (anos_completos * 12 + meses_completos)
    ano_nasc = total_meses_nasc // 12
    mes_nasc = total_meses_nasc % 12 + 1
    return ano_nasc, mes_nasc


def _calcular(pagina, entrada, params=None):
    entrada_completa = dict(ENTRADA_DEFAULT)
    entrada_completa.update(entrada)
    return pagina.evaluate(
        "([params, entrada]) => calcularCondicoesReforma(params, entrada)",
        [params or PARAMS_DEFAULT, entrada_completa],
    )


def _validar(pagina, bruto_parcial):
    bruto = {
        "mesNascimento": "9", "anoNascimento": "1966", "anosCarreira": "20",
        "idadeInicio": "", "servicoMilitar": False, "mesesServicoMilitar": "",
        "mesmaEmpresa": "sim", "anoReferencia": ANO_REF, "mesReferencia": MES_REF,
    }
    bruto.update(bruto_parcial)
    return pagina.evaluate("(bruto) => validarInputCondicoesReforma(bruto)", bruto)


def _idade(pagina, ano_nasc, mes_nasc, ano_ref=ANO_REF, mes_ref=MES_REF):
    return pagina.evaluate(
        "([an, mn, ar, mr]) => calcularIdadeAnosMeses(an, mn, ar, mr)",
        [ano_nasc, mes_nasc, ano_ref, mes_ref],
    )


# ── Canário: os limiares de produção batem com o brief/CLAUDE.md ──────────

def test_parametros_producao_tem_os_limiares_confirmados():
    assert PARAMS_DEFAULT["prazoGarantiaVelhiceAnos"]["valor"] == 15
    assert PARAMS_DEFAULT["clViaAIdadeMinima"]["valor"] == 60
    assert PARAMS_DEFAULT["clViaAAnosMinimos"]["valor"] == 48
    assert PARAMS_DEFAULT["clViaBIdadeMinima"]["valor"] == 60
    assert PARAMS_DEFAULT["clViaBAnosMinimos"]["valor"] == 46
    assert PARAMS_DEFAULT["clViaBIdadeInicioLimite"]["valor"] == 17
    assert PARAMS_DEFAULT["flexIdadeMinima"]["valor"] == 60
    assert PARAMS_DEFAULT["flexAnosMinimos"]["valor"] == 40
    assert PARAMS_DEFAULT["idadePessoalReducaoMesesPorAno"]["valor"] == 4
    assert PARAMS_DEFAULT["idadePessoalIdadeMinima"]["valor"] == 60
    assert PARAMS_DEFAULT["mesmaEmpresaAnosProibicao"]["valor"] == 3


# ── calcularIdadeAnosMeses ─────────────────────────────────────────────────

def test_idade_anos_completos_exactos(pagina):
    r = _idade(pagina, 1966, 9)  # nasceu no mesmo mês de referência, 60 anos antes
    assert r == {"anos": 60, "meses": 0, "totalMeses": 720}


def test_idade_com_meses_extra(pagina):
    r = _idade(pagina, 1966, 3)  # nasceu 6 meses antes do mês de referência
    assert r == {"anos": 60, "meses": 6, "totalMeses": 726}


def test_idade_ainda_nao_fez_anos_este_ano(pagina):
    # nasceu em dezembro de 1965 -> à referência de set/2026 ainda não fez 61
    r = _idade(pagina, 1965, 12)
    assert r["anos"] == 60
    assert r["meses"] == 9


# ── CASO 1: fronteira dos 17 anos ──────────────────────────────────────────

def test_caso1a_inicio_aos_16_acede_por_carreiras_muito_longas_via_b(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 46, "idadeInicioDescontos": 16,
    })
    vias_ids = [v["id"] for v in r["vias"]]
    assert "carreiras_muito_longas" in vias_ids
    cml = next(v for v in r["vias"] if v["id"] == "carreiras_muito_longas")
    assert cml["subvias"] == ["b"]
    assert cml["dependeServicoMilitar"] is False


def test_caso1b_inicio_aos_17_nao_acede_cai_na_flexibilizacao(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 46, "idadeInicioDescontos": 17,
    })
    vias_ids = [v["id"] for v in r["vias"]]
    assert "carreiras_muito_longas" not in vias_ids
    assert "flexibilizacao" in vias_ids


# ── CASO 2: serviço militar decisivo ───────────────────────────────────────

def test_caso2_servico_militar_decisivo_acusa_acesso_e_avisa(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 46,  # sem tropa, nunca chega a 48
        "servicoMilitarSemDescontos": True, "mesesServicoMilitar": 24,  # +2 anos
    })
    assert r["anosConsiderados"] == 48
    cml = next(v for v in r["vias"] if v["id"] == "carreiras_muito_longas")
    assert cml["subvias"] == ["a"]
    assert cml["dependeServicoMilitar"] is True


def test_caso2b_sem_tropa_nao_acede(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 46, "servicoMilitarSemDescontos": False,
    })
    vias_ids = [v["id"] for v in r["vias"]]
    assert "carreiras_muito_longas" not in vias_ids


def test_servico_militar_nao_decisivo_nunca_marca_dependencia(pagina):
    # já tem 48 anos SEM tropa -> mesmo reportando tropa, não depende dela
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 48,
        "servicoMilitarSemDescontos": True, "mesesServicoMilitar": 12,
    })
    cml = next(v for v in r["vias"] if v["id"] == "carreiras_muito_longas")
    assert cml["dependeServicoMilitar"] is False


# ── CASO 3: limite dos 60 anos na idade pessoal ────────────────────────────

def test_caso3_idade_pessoal_reducao_e_piso_legal(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 41,
    })
    assert r["idadePessoal"] is not None
    assert r["idadePessoal"]["anosExcedentes"] == 1
    assert r["idadePessoal"]["reducaoMeses"] == 4
    assert r["idadePessoal"]["idadeMinimaAbsoluta"] == 60


def test_idade_pessoal_ausente_com_exactamente_40_anos(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(45)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 40,
    })
    assert r["idadePessoal"] is None


def test_idade_pessoal_exemplo_do_brief_3_anos_excedentes(pagina):
    # "A sua carreira excede os 40 anos em 3 anos completos... menos 12 meses"
    ano_nasc, mes_nasc = _nascimento_para_idade(50)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 43,
    })
    assert r["idadePessoal"]["anosExcedentes"] == 3
    assert r["idadePessoal"]["reducaoMeses"] == 12


# ── CASO 4: prazo de garantia não cumprido ─────────────────────────────────

def test_caso4_prazo_garantia_nao_cumprido_para_tudo(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 14,
    })
    assert r["semAcesso"] is True
    assert r["prazoGarantiaCumprido"] is False
    assert r["anosEmFaltaPrazoGarantia"] == 1
    assert r["vias"] == []
    assert r["idadePessoal"] is None
    assert r["quantoFalta"] is None


def test_prazo_garantia_cumprido_com_servico_militar(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 13, "servicoMilitarSemDescontos": True, "mesesServicoMilitar": 24,
    })
    assert r["anosConsiderados"] == 15
    assert r["semAcesso"] is False


# ── CASO 5: elegível por duas vias em simultâneo ───────────────────────────

def test_caso5_elegivel_por_duas_vias_simultaneas(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 48,
    })
    vias_ids = sorted(v["id"] for v in r["vias"])
    assert vias_ids == ["carreiras_muito_longas", "flexibilizacao"]
    cml = next(v for v in r["vias"] if v["id"] == "carreiras_muito_longas")
    assert cml["subvias"] == ["a"]


# ── "Quanto falta" — só quando nenhuma via está disponível ────────────────

def test_quanto_falta_idade_e_carreira(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(50)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 20,
    })
    assert r["vias"] == []
    assert r["quantoFalta"] == {"idade": {"anos": 10, "meses": 0}, "anosCarreira": 20}


def test_quanto_falta_so_idade_carreira_ja_suficiente(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(55)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 42,  # já >= 40, só falta idade
    })
    assert r["vias"] == []
    assert r["quantoFalta"]["anosCarreira"] == 0
    assert r["quantoFalta"]["idade"] == {"anos": 5, "meses": 0}


def test_quanto_falta_ausente_quando_ha_via_disponivel(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 40,
    })
    assert len(r["vias"]) == 1
    assert r["quantoFalta"] is None


# ── Aviso "mesma empresa" — só relevante com via de antecipação ───────────

def test_aviso_mesma_empresa_so_com_via_disponivel(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 40, "mesmaEmpresa": True,
    })
    assert r["avisoMesmaEmpresa"] is True


def test_aviso_mesma_empresa_ausente_sem_via(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(50)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 20, "mesmaEmpresa": True,
    })
    assert r["avisoMesmaEmpresa"] is False


def test_aviso_mesma_empresa_ausente_quando_nao_reportado(pagina):
    ano_nasc, mes_nasc = _nascimento_para_idade(60)
    r = _calcular(pagina, {
        "anoNascimento": ano_nasc, "mesNascimento": mes_nasc,
        "anosCarreira": 40, "mesmaEmpresa": False,
    })
    assert r["avisoMesmaEmpresa"] is False


# ── Validação de input ──────────────────────────────────────────────────────

def test_validacao_todos_os_campos_obrigatorios_em_falta(pagina):
    r = _validar(pagina, {"mesNascimento": "", "anoNascimento": "", "anosCarreira": "", "mesmaEmpresa": ""})
    assert r["valido"] is False
    campos = {e["campo"] for e in r["erros"]}
    assert campos == {"mesNascimento", "anoNascimento", "anosCarreira", "mesmaEmpresa"}


def test_validacao_ano_nascimento_nao_numerico(pagina):
    r = _validar(pagina, {"anoNascimento": "abc"})
    assert r["valido"] is False
    assert any(e["campo"] == "anoNascimento" for e in r["erros"])


def test_validacao_ano_nascimento_no_futuro(pagina):
    r = _validar(pagina, {"anoNascimento": "2027"})
    assert r["valido"] is False
    assert any(e["campo"] == "anoNascimento" for e in r["erros"])


def test_validacao_anos_carreira_com_decimais_rejeitado(pagina):
    r = _validar(pagina, {"anosCarreira": "42.5"})
    assert r["valido"] is False
    assert any(e["campo"] == "anosCarreira" for e in r["erros"])


def test_validacao_idade_inicio_opcional_vazio_aceite(pagina):
    r = _validar(pagina, {"idadeInicio": ""})
    assert r["valido"] is True
    assert r["valoresNormalizados"]["idadeInicioDescontos"] is None


def test_validacao_idade_inicio_invalida_quando_preenchida(pagina):
    r = _validar(pagina, {"idadeInicio": "16.5"})
    assert r["valido"] is False
    assert any(e["campo"] == "idadeInicio" for e in r["erros"])


def test_validacao_servico_militar_marcado_exige_meses(pagina):
    r = _validar(pagina, {"servicoMilitar": True, "mesesServicoMilitar": ""})
    assert r["valido"] is False
    assert any(e["campo"] == "mesesServicoMilitar" for e in r["erros"])


def test_validacao_servico_militar_meses_invalidos(pagina):
    r = _validar(pagina, {"servicoMilitar": True, "mesesServicoMilitar": "-3"})
    assert r["valido"] is False
    assert any(e["campo"] == "mesesServicoMilitar" for e in r["erros"])


def test_validacao_servico_militar_nao_marcado_ignora_meses(pagina):
    r = _validar(pagina, {"servicoMilitar": False, "mesesServicoMilitar": ""})
    assert r["valido"] is True
    assert r["valoresNormalizados"]["mesesServicoMilitar"] == 0
    assert r["valoresNormalizados"]["servicoMilitarSemDescontos"] is False


def test_validacao_tudo_valido(pagina):
    r = _validar(pagina, {
        "mesNascimento": "9", "anoNascimento": "1966", "anosCarreira": "48",
        "idadeInicio": "16", "servicoMilitar": True, "mesesServicoMilitar": "24",
        "mesmaEmpresa": "nao",
    })
    assert r["valido"] is True
    assert r["valoresNormalizados"] == {
        "mesNascimento": 9, "anoNascimento": 1966, "anosCarreira": 48,
        "idadeInicioDescontos": 16, "servicoMilitarSemDescontos": True,
        "mesesServicoMilitar": 24, "mesmaEmpresa": False,
    }
