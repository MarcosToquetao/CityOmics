"""Histórico de crime as-of por setor × mês (spec-dados §3.3, D6, D25).

Regra as-of exata: o lag ``L`` do mês ``m`` conta os eventos de fato em ``m − L`` que **já estavam
registrados** antes do início de ``m``, isto é, com mês de registro ≤ ``m − 1``. Como 7% dos BOs são
registrados no mês seguinte ao fato, usar a contagem final do mês anterior vazaria informação.

Eventos sem coordenada (via ``bairro`` ou ``dp``) só têm distrito. O histórico por setor usa só os
eventos geocodificados (via ``coord``) e corrige a cobertura dividindo pela fração geocodificada do
distrito no mesmo mês de fato (também as-of): ``intensidade = n_geo_setor / cobertura_distrito``.
Isso evita que a alta de cobertura de 80% para 90% (abr/2026) pareça aumento de crime.

Todas as features são contagens ou somas ponderadas do passado; nenhuma usa o mês ``m`` nem depois.
"""

from __future__ import annotations

import numpy as np
import polars as pl

LAGS = (1, 2, 3, 6, 12)
JANELAS = (3, 6, 12)
KMAX = 12     # registros com mais de 11 meses de atraso só entram a partir do lag 12


def _midx(col: str) -> pl.Expr:
    return pl.col(col).dt.year() * 12 + pl.col(col).dt.month() - 1


def _cum_counts(keys: np.ndarray, n_keys: int, f_idx: np.ndarray, k: np.ndarray, n_f: int) -> np.ndarray:
    """Tensor [chave, mês de fato, L−1]: eventos com atraso de registro ≤ L−1 meses."""
    c = np.zeros((n_keys, n_f, KMAX), dtype="float32")
    kk = np.minimum(k, KMAX - 1)
    np.add.at(c, (keys, f_idx, kk), 1.0)
    return np.cumsum(c, axis=2)


def _lag_value(cum: np.ndarray, m_idx: int, f0: int, lag: int) -> np.ndarray:
    f = m_idx - lag - f0
    if f < 0 or f >= cum.shape[1]:
        return np.full(cum.shape[0], np.nan, dtype="float32")
    return cum[:, f, min(lag, KMAX) - 1]


def build(events: pl.DataFrame, setores: list[str], distritos: dict[str, str], meses: list[str],
          inicio: str = "2022-01") -> pl.DataFrame:
    """Features de histórico para cada (setor, mês) de ``meses``.

    ``events``: colunas ``cd_setor``, ``cd_dist``, ``data_fato``, ``data_registro``, ``via``.
    ``distritos``: mapa setor → distrito. ``meses``: 'AAAA-MM' dos meses-alvo. ``inicio``: primeiro mês de
    fato com cobertura completa (a SSP só serve 2022+); lags que chegam antes dele ficam ausentes (NaN),
    e janelas incompletas também.
    """
    ev = events.filter(pl.col("data_fato").is_not_null() & pl.col("cd_dist").is_not_null())
    ev = ev.with_columns(
        _midx("data_fato").alias("f"),
        pl.when(pl.col("data_registro").is_null()).then(_midx("data_fato"))
        .otherwise(pl.max_horizontal(_midx("data_registro"), _midx("data_fato"))).alias("r"))
    ev = ev.with_columns((pl.col("r") - pl.col("f")).alias("k"))
    ymd = lambda s: int(s[:4]) * 12 + int(s[5:7]) - 1  # noqa: E731
    m_idx = [ymd(m) for m in meses]
    f0 = ymd(inicio)
    ev = ev.filter(pl.col("f") >= f0)
    n_f = max(int(ev["f"].max()), max(m_idx)) - f0 + 1

    sid = {s: i for i, s in enumerate(setores)}
    dist_list = sorted(set(distritos.values()))
    did = {d: i for i, d in enumerate(dist_list)}
    geo = ev.filter((pl.col("via") == "coord") & pl.col("cd_setor").is_in(setores))
    cum_s = _cum_counts(np.array([sid[s] for s in geo["cd_setor"]]), len(setores),
                        (geo["f"] - f0).to_numpy(), geo["k"].to_numpy(), n_f)
    ev_d = ev.filter(pl.col("cd_dist").is_in(dist_list))
    cum_d = _cum_counts(np.array([did[d] for d in ev_d["cd_dist"]]), len(dist_list),
                        (ev_d["f"] - f0).to_numpy(), ev_d["k"].to_numpy(), n_f)
    geo_d = ev_d.filter((pl.col("via") == "coord") & pl.col("cd_setor").is_not_null())
    cum_dg = _cum_counts(np.array([did[d] for d in geo_d["cd_dist"]]), len(dist_list),
                         (geo_d["f"] - f0).to_numpy(), geo_d["k"].to_numpy(), n_f)
    sd = np.array([did[distritos[s]] for s in setores])

    # cobertura geocodificada do distrito em cada mês de fato, as-of por lag (suavizada: +1 / +1,25 evita 0/0)
    frames = []
    for m, mi in zip(meses, m_idx):
        cols = {"cd_setor": setores, "mes": [m] * len(setores)}
        est = {}
        for lag in range(1, 13):
            g = _lag_value(cum_s, mi, f0, lag)
            dt = _lag_value(cum_d, mi, f0, lag)[sd]
            dg = _lag_value(cum_dg, mi, f0, lag)[sd]
            cov = (dg + 1.0) / (dt + 1.25)
            est[lag] = (g / cov).astype("float32")
            cols[f"h_int_l{lag}"] = est[lag]          # série as-of completa (Chronos usa os 12 lags)
            if lag in LAGS:
                cols[f"h_geo_l{lag}"] = g
                cols[f"h_dist_l{lag}"] = dt
        for w in JANELAS:
            cols[f"h_int_s{w}"] = np.sum([est[l] for l in range(1, w + 1)], axis=0)
        frames.append(pl.DataFrame(cols))
    return pl.concat(frames)
