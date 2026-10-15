from datetime import date

import pandas as pd

from cityomics.covariates import calendario as cal


def test_easter_known_dates():
    assert cal.easter(2024) == date(2024, 3, 31)
    assert cal.easter(2025) == date(2025, 4, 20)
    assert cal.easter(2026) == date(2026, 4, 5)


def test_holidays_and_carnaval_2026():
    h = cal.holidays(2026)
    assert h[date(2026, 4, 3)] == "nacional"       # Sexta-feira Santa
    assert h[date(2026, 6, 4)] == "municipal"      # Corpus Christi (Páscoa + 60)
    assert h[date(2026, 7, 9)] == "estadual" and h[date(2026, 11, 20)] == "nacional"
    assert date(2026, 2, 17) in cal.carnaval(2026)  # terça-feira de Carnaval
    assert cal.holidays(2023)[date(2023, 11, 20)] == "municipal"


def test_fifth_business_day_skips_weekends_and_holidays():
    # Jan/2026: 1º é feriado (qui); úteis: 2, 5, 6, 7, 8 → 5º dia útil = 8
    assert cal.fifth_business_day(2026, 1, set(cal.holidays(2026))) == date(2026, 1, 8)


def test_daily_and_monthly_are_consistent():
    d = cal.daily()
    assert d["data"].is_unique and d["data"].min() == pd.Timestamp("2015-01-01")
    m = cal.monthly(d).set_index("mes")
    assert m.loc["2026-02", "dias"] == 28 and m.loc["2026-02", "dias_carnaval"] == 5
    assert m.loc["2026-12", "tem_decimo_terceiro"]
    assert (m["dias_uteis"] + m["dias_fim_de_semana"] + m["dias_feriado"]
            - d.assign(mes=d["data"].dt.to_period("M").astype(str)).groupby("mes")
            .apply(lambda g: int((g["fim_de_semana"] & g["feriado"]).sum()), include_groups=False)
            == m["dias"]).all()
