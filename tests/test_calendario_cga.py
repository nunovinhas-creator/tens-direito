"""Datas de pagamento das pensões da CGA — regra «dia 19 ou dia útil anterior»."""
import datetime as dt
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from calendario_cga import dia_pagamento, proximas_datas  # noqa: E402

D = dt.date

# Calendário de 2026 publicado pela CGA (cga.pt/pagamentos), reproduzido em
# economiafinancas.com a 09/01/2026. A regra tem de dar exactamente isto.
PUBLICADO_2026 = {
    1: 19, 2: 19, 3: 19, 4: 17, 5: 19, 6: 19,
    7: 17, 8: 19, 9: 18, 10: 19, 11: 19, 12: 18,
}


@pytest.mark.parametrize("mes,dia", sorted(PUBLICADO_2026.items()))
def test_regra_bate_com_calendario_publicado_2026(mes, dia):
    assert dia_pagamento(2026, mes) == D(2026, mes, dia)


def test_fim_de_semana_recua_para_sexta():
    # 19/04/2026 é domingo
    assert dia_pagamento(2026, 4) == D(2026, 4, 17)


def test_feriado_ao_dia_19_recua():
    # Corpo de Deus a 19/06/2025 (quinta-feira)
    assert dia_pagamento(2025, 6) == D(2025, 6, 18)
    # Sexta-Feira Santa a 19/04/2030 → quinta 18
    assert dia_pagamento(2030, 4) == D(2030, 4, 18)


def test_carnaval_nao_e_feriado():
    # Nenhum ajuste por feriados facultativos: dia 19 útil fica 19
    assert dia_pagamento(2027, 1) == D(2027, 1, 19)


def test_nunca_depois_do_dia_19():
    for ano in range(2025, 2036):
        for mes in range(1, 13):
            d = dia_pagamento(ano, mes)
            assert d.day <= 19 and d.weekday() < 5


def test_proximas_datas_exclui_o_mes_corrente_ja_pago():
    datas = proximas_datas(D(2026, 10, 20), meses=3)
    assert datas == [D(2026, 11, 19), D(2026, 12, 18)]


def test_proximas_datas_inclui_o_proprio_dia():
    assert proximas_datas(D(2026, 10, 19), meses=1) == [D(2026, 10, 19)]
