"""
Testes para scripts/source_adapter.py — Camada 6, Source Adapter.

Cobertura pedida:
- seleção correta do provider
- resposta estruturada (ResultadoFonte)
- comportamento quando não existe provider aplicável
- comportamento determinístico
- possibilidade de adicionar novos providers sem alterar código existente
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import source_adapter
from source_adapter import (
    FonteProvider,
    ResultadoFonte,
    obter_valor_oficial,
    registar_provider,
)

AGORA = "2026-07-01T00:00:00+00:00"


def _alerta(pagina="", tipo="", contexto=""):
    return {
        "pagina": pagina,
        "tipo": tipo,
        "classificacao": {"data": "x", "estado": "OUTDATED_REVIEW_REQUIRED", "contexto": contexto},
    }


@pytest.fixture(autouse=True)
def _isolar_registo_providers(monkeypatch):
    """Isola cada teste com a sua própria cópia do registo de providers,
    para que testes que chamem `registar_provider` nunca afectem outros
    testes (o registo é uma lista módulo-level mutável)."""
    monkeypatch.setattr(
        source_adapter, "_REGISTO_PROVIDERS", list(source_adapter._REGISTO_PROVIDERS)
    )
    yield


# ── Resposta estruturada ────────────────────────────────────────────────────

def test_resultado_e_dataclass_com_campos_esperados():
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert isinstance(resultado, ResultadoFonte)
    assert hasattr(resultado, "encontrado")
    assert hasattr(resultado, "valor")
    assert hasattr(resultado, "url_origem")
    assert hasattr(resultado, "data_consulta")
    assert hasattr(resultado, "confianca")
    assert hasattr(resultado, "motivo")
    assert resultado.data_consulta == AGORA


def test_placeholder_nunca_afirma_ter_encontrado_valor():
    # Nesta fase nenhum provider faz scraping real -- encontrado tem de
    # ser sempre False, nunca inventar um valor.
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert resultado.encontrado is False
    assert resultado.valor is None


def test_resultado_identifica_o_nome_do_provider_escolhido():
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert resultado.provider == "seguranca_social"


# ── Seleção correta do provider ─────────────────────────────────────────────

@pytest.mark.parametrize(
    "pagina, contexto, url_esperado",
    [
        ("abono-de-familia.html", "", "seg-social.pt"),
        ("prestacao-social-unica.html", "", "seg-social.pt"),
        ("subsidio-desemprego.html", "", "iefp.pt"),
        ("acao-social-escolar.html", "", "dge.mec.pt"),
        ("bolsa-de-merito.html", "", "dge.mec.pt"),
        ("pagina-generica.html", "Fonte: Portaria n.º 42/2026/1.", "dre.pt"),
        ("pagina-generica.html", "publicado no Diário da República.", "dre.pt"),
    ],
)
def test_selecao_correta_do_provider(pagina, contexto, url_esperado):
    resultado = obter_valor_oficial(_alerta(pagina=pagina, contexto=contexto), agora=AGORA)
    assert url_esperado in resultado.url_origem


def test_ordem_de_registo_decide_em_caso_de_ambiguidade():
    # "abono" (Seg. Social) e "portaria" (DRE) no mesmo alerta -- o
    # primeiro provider registado que se aplique é o escolhido.
    resultado = obter_valor_oficial(
        _alerta(pagina="abono-de-familia.html", contexto="Portaria n.º 60/2026/1."),
        agora=AGORA,
    )
    assert "seg-social.pt" in resultado.url_origem


# ── Sem provider aplicável ──────────────────────────────────────────────────

def test_sem_provider_aplicavel_devolve_encontrado_false_com_motivo():
    resultado = obter_valor_oficial(_alerta(pagina="passe-sub23.html"), agora=AGORA)
    assert resultado.encontrado is False
    assert resultado.url_origem is None
    assert resultado.motivo == "nenhum provider aplicável para este alerta"


def test_alerta_vazio_ou_none_nao_crasha():
    assert obter_valor_oficial({}, agora=AGORA).encontrado is False
    assert obter_valor_oficial(None, agora=AGORA).encontrado is False  # type: ignore[arg-type]


# ── Determinismo ────────────────────────────────────────────────────────────

def test_obter_valor_oficial_e_deterministico():
    alerta = _alerta(pagina="abono-de-familia.html")
    resultados = [obter_valor_oficial(alerta, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


def test_sem_provider_tambem_e_deterministico():
    alerta = _alerta(pagina="passe-sub23.html")
    resultados = [obter_valor_oficial(alerta, agora=AGORA) for _ in range(10)]
    assert all(r == resultados[0] for r in resultados)


# ── Extensibilidade: novos providers sem alterar código existente ─────────

class _ProviderTransportesDeTeste(FonteProvider):
    """Provider definido inteiramente no teste -- prova de que o
    dispatcher aceita novas fontes sem qualquer alteração a
    source_adapter.py."""

    nome = "cp_teste"

    def aplica_se(self, alerta: dict) -> bool:
        return "passe-sub23" in (alerta.get("pagina") or "")

    def obter_valor(self, alerta: dict, *, agora=None) -> ResultadoFonte:
        return ResultadoFonte(
            encontrado=True,
            valor="gratuito",
            url_origem="https://www.cp.pt",
            data_consulta=agora,
            confianca=0.9,
            motivo="provider de teste",
        )


def test_novo_provider_registado_e_escolhido_sem_alterar_source_adapter():
    # Antes de registar, não há provider para passe-sub23.html.
    antes = obter_valor_oficial(_alerta(pagina="passe-sub23.html"), agora=AGORA)
    assert antes.encontrado is False

    registar_provider(_ProviderTransportesDeTeste())

    depois = obter_valor_oficial(_alerta(pagina="passe-sub23.html"), agora=AGORA)
    assert depois.encontrado is True
    assert depois.valor == "gratuito"
    assert depois.url_origem == "https://www.cp.pt"


def test_novo_provider_com_prioridade_e_avaliado_primeiro():
    class _ProviderAbonoPrioritario(FonteProvider):
        nome = "abono_prioritario"

        def aplica_se(self, alerta: dict) -> bool:
            return "abono" in (alerta.get("pagina") or "")

        def obter_valor(self, alerta: dict, *, agora=None) -> ResultadoFonte:
            return ResultadoFonte(
                encontrado=True, valor="override", url_origem="https://exemplo.pt",
                data_consulta=agora, confianca=1.0,
            )

    registar_provider(_ProviderAbonoPrioritario(), prioridade=True)
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert resultado.valor == "override"


def test_registo_de_providers_nao_afeta_outros_testes_isolamento():
    # Confirma que a fixture de isolamento realmente protege o registo
    # global -- se este teste correr depois dos de extensibilidade acima
    # e ainda vir o comportamento por omissão, o isolamento funciona.
    resultado = obter_valor_oficial(_alerta(pagina="passe-sub23.html"), agora=AGORA)
    assert resultado.encontrado is False


# ── Falha-segura: provider mal-comportado nunca derruba o dispatcher ──────

def test_provider_cujo_aplica_se_rebenta_nao_impede_os_seguintes():
    class _ProviderRebenta(FonteProvider):
        nome = "rebenta"

        def aplica_se(self, alerta: dict) -> bool:
            raise RuntimeError("provider mal-comportado")

        def obter_valor(self, alerta: dict, *, agora=None) -> ResultadoFonte:
            raise AssertionError("nunca deveria ser chamado")

    registar_provider(_ProviderRebenta(), prioridade=True)
    # Continua a chegar ao provider seguinte (Segurança Social) sem crashar.
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert resultado.encontrado is False
    assert "seg-social.pt" in resultado.url_origem


def test_erro_inesperado_no_dispatcher_nunca_propaga_excepcao(monkeypatch):
    def _selecionar_que_rebenta(alerta):
        raise RuntimeError("falha completamente inesperada")

    monkeypatch.setattr(source_adapter, "_selecionar_provider", _selecionar_que_rebenta)
    resultado = obter_valor_oficial(_alerta(pagina="abono-de-familia.html"), agora=AGORA)
    assert resultado.encontrado is False
    assert "falha completamente inesperada" in resultado.motivo


# ── Isolamento arquitectural: não conhece as outras camadas ────────────────

def test_modulo_nao_importa_outras_camadas_do_sistema():
    proibidos = {
        "verificar_datas", "classificar_datas", "decisao_datas",
        "auto_update_engine", "orquestrador_datas",
    }
    assert not (proibidos & set(vars(source_adapter).keys()))
