"""MaxEnt como modelo de processo pontual de Poisson (ecologia: distribuição de espécies).

O MaxEnt com saída "cloglog/raw" é, na prática, um processo pontual de Poisson com intensidade
log-linear em funções de base das covariáveis (lineares, quadráticas e dobradiças). Aqui:

- a superfície é estimada por setor sobre o período de ajuste (contagem como "presenças", área como
  exposição) com **covariáveis estruturais** e funções de base (linear, quadrática e 5 dobradiças por
  quantis), regularização L2 e alpha escolhido em validação temporal dentro do ajuste;
- a previsão mensal multiplica a superfície pelo fator temporal as-of (``inla_models.predict``).

Desvio declarado do pré-registro (§5.1, "target-group background"): não há camada de viés de esforço
de registro (outros crimes de vítima) neste ajuste; o viés de denúncia fica sem correção explícita.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl
from sklearn.linear_model import PoissonRegressor

KNOTS = (0.1, 0.3, 0.5, 0.7, 0.9)


def basis(x: np.ndarray, knots: np.ndarray | None = None):
    """Linear + quadrática + dobradiças (forward) por coluna. ``knots``: quantis (reusar na previsão)."""
    if knots is None:
        knots = np.quantile(x, KNOTS, axis=0)             # [5, p]
    cols = [x, x ** 2]
    cols += [np.maximum(0.0, x - knots[k]) for k in range(len(KNOTS))]
    return np.column_stack(cols), knots


def fit_surface(d: pd.DataFrame, cov_cols: list[str], alphas=(1e-3, 1e-2, 1e-1, 1.0), seed: int = 0) -> pd.DataFrame:
    """``d``: saída de ``inla_models.prepare`` (covariáveis padronizadas, ``y`` e ``meses``). Devolve cd_setor, maxent."""
    x = np.nan_to_num(d[cov_cols].to_numpy().astype("float64"))
    X, _ = basis(x)
    y = d["y"].to_numpy() / d["meses"].to_numpy()          # taxa mensal média
    rng = np.random.default_rng(seed)
    hold = rng.random(len(y)) < 0.2                         # validação espacial aleatória para escolher alpha
    best = (np.inf, None)
    for a in alphas:
        m = PoissonRegressor(alpha=a, max_iter=500).fit(X[~hold], y[~hold])
        mu = m.predict(X[hold])
        dev = np.mean(mu - y[hold] * np.log(mu + 1e-9))
        if dev < best[0]:
            best = (dev, a)
    m = PoissonRegressor(alpha=best[1], max_iter=800).fit(X, y)
    return pd.DataFrame({"cd_setor": d["cd_setor"], "maxent": m.predict(X)})
