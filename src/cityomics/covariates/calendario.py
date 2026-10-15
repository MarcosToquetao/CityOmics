"""Calendário: feriados, dias de pagamento, Carnaval e fins de semana (spec-dados §3.2).

Tudo é calculado por regra, sem download, para os dias de 2015 a 2027 (a janela
prospectiva vai até mar/2027). Resolução diária; ``monthly`` agrega por mês.

Feriados: nacionais (inclui Consciência Negra, nacional desde 2024), estaduais de SP (9 de
julho) e municipais de São Paulo (25 de janeiro e Corpus Christi). Carnaval e Corpus Christi
dependem da Páscoa. Dia de pagamento: 5º dia útil de cada mês, o dia 20 (adiantamento) e o
13º salário (30/nov e 20/dez). Sábados e domingos ficam em ``fim_de_semana``.

Não incluídos, por falta de fonte aberta e completa: jogos em casa dos clubes, grandes
eventos e blocos de rua (listados só em Diário Oficial).
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from cityomics.paths import processed_dir

YEARS = range(2015, 2028)


def easter(year: int) -> date:
    """Domingo de Páscoa (algoritmo de Meeus/Jones/Butcher)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)


def holidays(year: int) -> dict[date, str]:
    p = easter(year)
    out = {
        date(year, 1, 1): "nacional", date(year, 4, 21): "nacional", date(year, 5, 1): "nacional",
        date(year, 9, 7): "nacional", date(year, 10, 12): "nacional", date(year, 11, 2): "nacional",
        date(year, 11, 15): "nacional", date(year, 12, 25): "nacional",
        p - timedelta(days=2): "nacional",          # Sexta-feira Santa
        date(year, 7, 9): "estadual",               # Revolução Constitucionalista
        date(year, 1, 25): "municipal",             # aniversário da cidade
        p + timedelta(days=60): "municipal",        # Corpus Christi
    }
    if year >= 2024:
        out[date(year, 11, 20)] = "nacional"        # Consciência Negra
    elif year >= 2004:
        out[date(year, 11, 20)] = "municipal"       # municipal em SP desde 2004
    return out


def carnaval(year: int) -> set[date]:
    p = easter(year)
    return {p - timedelta(days=d) for d in (51, 50, 49, 48, 47)}  # sábado a quarta de cinzas


def fifth_business_day(year: int, month: int, feriados: set[date]) -> date:
    d, n = date(year, month, 1), 0
    while True:
        if d.weekday() < 5 and d not in feriados:
            n += 1
            if n == 5:
                return d
        d += timedelta(days=1)


def daily() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        hol = holidays(year)
        feriados = set(hol)
        car = carnaval(year)
        pay5 = {fifth_business_day(year, m, feriados) for m in range(1, 13)}
        pay20 = {date(year, m, 20) for m in range(1, 13)}
        decimo = {date(year, 11, 30), date(year, 12, 20)}
        d = date(year, 1, 1)
        while d.year == year:
            rows.append({
                "data": pd.Timestamp(d), "dia_semana": d.weekday(),
                "fim_de_semana": d.weekday() >= 5,
                "feriado": d in hol, "feriado_tipo": hol.get(d),
                "vespera_feriado": (d + timedelta(days=1)) in hol,
                "carnaval": d in car,
                "pagamento_5du": d in pay5, "pagamento_dia20": d in pay20, "decimo_terceiro": d in decimo,
            })
            d += timedelta(days=1)
    df = pd.DataFrame(rows)
    df["dia_nao_util"] = df["fim_de_semana"] | df["feriado"]
    return df


def monthly(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = daily() if df is None else df
    df = df.assign(mes=df["data"].dt.to_period("M").astype(str))
    g = df.groupby("mes")
    out = pd.DataFrame({
        "dias": g.size(),
        "dias_fim_de_semana": g["fim_de_semana"].sum(),
        "dias_feriado": g["feriado"].sum(),
        "dias_uteis": g["dia_nao_util"].apply(lambda s: int((~s).sum())),
        "dias_carnaval": g["carnaval"].sum(),
        "n_sextas": g["dia_semana"].apply(lambda s: int((s == 4).sum())),
        "n_sabados": g["dia_semana"].apply(lambda s: int((s == 5).sum())),
        "tem_decimo_terceiro": g["decimo_terceiro"].any(),
    }).reset_index()
    for c in ("dias_fim_de_semana", "dias_feriado", "dias_carnaval"):
        out[c] = out[c].astype(int)
    out["frac_fim_de_semana"] = out["dias_fim_de_semana"] / out["dias"]
    return out


def build() -> dict[str, pd.DataFrame]:
    d = daily()
    m = monthly(d)
    dest = processed_dir() / "covariaveis"
    dest.mkdir(parents=True, exist_ok=True)
    d.to_parquet(dest / "calendario_dia.parquet", index=False)
    m.to_parquet(dest / "calendario_mes.parquet", index=False)
    return {"dia": d, "mes": m}
