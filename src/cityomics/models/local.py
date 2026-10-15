"""Regressão local e painel espacial (econometria; spec-benchmark §3.2).

- **GWR por distrito:** um GLM de Poisson regularizado por distrito (96 ajustes), com os mesmos
  regressores de todos; os coeficientes variam no espaço entre distritos (aproximação do GWR/MGWR
  exato, inviável com 27 mil setores × 24 meses por ajuste). Distritos com poucos dados herdam o
  ajuste global por encolhimento (ridge em direção ao global).
- **Painel espacial:** Poisson global com efeitos fixos de distrito e de mês do ano e defasagens
  espaciais das variáveis (Wx: ``nb_*``), a versão SLX de um painel espacial.

Em ambos, a média é Poisson por quase-verossimilhança e a distribuição NB vem da dispersão global.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.linear_model import PoissonRegressor

HIST = ["h_int_l1", "h_int_l2", "h_int_l3", "h_int_s6", "h_int_s12", "nb_h_int_l1", "nb_h_int_s3", "nb_h_int_s12"]


def _x(df: pl.DataFrame, cols: list[str], mu: np.ndarray | None = None, sd: np.ndarray | None = None):
    x = df.select(cols).to_numpy().astype("float64")
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = np.sign(x) * np.log1p(np.abs(x))
    if mu is None:
        mu, sd = x.mean(0), x.std(0) + 1e-6
    return (x - mu) / sd, mu, sd


class GWRDistrict:
    def __init__(self, cols: list[str], alpha_local: float = 1e-2, alpha_global: float = 1e-4, min_rows: int = 800):
        self.cols, self.al, self.ag, self.min_rows = cols + HIST, alpha_local, alpha_global, min_rows

    def fit(self, df: pl.DataFrame):
        x, self.mu, self.sd = _x(df, self.cols)
        y = df["y"].to_numpy()
        sea = np.column_stack([(df["mes_num"].to_numpy() == k).astype("float64") for k in range(2, 13)])
        X = np.column_stack([x, sea])
        self.glob = PoissonRegressor(alpha=self.ag, max_iter=400).fit(X, y)
        self.local = {}
        d = df["cd_dist"].to_numpy()
        for dist in np.unique(d):
            i = d == dist
            if i.sum() >= self.min_rows:
                # encolhimento: o ajuste local parte da previsão global como offset aproximado (log do global)
                off = np.log(self.glob.predict(X[i]) + 1e-6)
                m = PoissonRegressor(alpha=self.al, max_iter=300).fit(np.column_stack([X[i], off]), y[i])
                self.local[dist] = m
        return self

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        x, _, _ = _x(df, self.cols, self.mu, self.sd)
        sea = np.column_stack([(df["mes_num"].to_numpy() == k).astype("float64") for k in range(2, 13)])
        X = np.column_stack([x, sea])
        mu = self.glob.predict(X)
        d = df["cd_dist"].to_numpy()
        for dist, m in self.local.items():
            i = d == dist
            if i.any():
                mu[i] = m.predict(np.column_stack([X[i], np.log(mu[i] + 1e-6)]))
        return mu


class PainelEspacial:
    """Poisson com efeitos fixos de distrito e mês do ano mais defasagens espaciais (SLX)."""

    def __init__(self, cols: list[str]):
        self.cols = cols + HIST

    def _X(self, df: pl.DataFrame, fit: bool):
        x, mu, sd = _x(df, self.cols, None if fit else self.mu, None if fit else self.sd)
        if fit:
            self.mu, self.sd = mu, sd
            self.dists = sorted(df["cd_dist"].unique().to_list())
        dd = df["cd_dist"].to_numpy()
        fe = np.column_stack([(dd == k).astype("float64") for k in self.dists[1:]])
        sea = np.column_stack([(df["mes_num"].to_numpy() == k).astype("float64") for k in range(2, 13)])
        return np.column_stack([x, fe, sea])

    def fit(self, df: pl.DataFrame):
        self.m = PoissonRegressor(alpha=1e-4, max_iter=500).fit(self._X(df, True), df["y"].to_numpy())
        return self

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        return self.m.predict(self._X(df, False))
