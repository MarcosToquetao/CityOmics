"""Ensemble empilhado (spec-benchmark §3.2; prereg §5.1).

Os pesos são ajustados em uma **janela de validação** posterior ao ajuste dos modelos-base (previsões
fora da amostra), minimizando a deviance de Poisson da mistura de médias sob a restrição de simplex
(pesos ≥ 0, soma 1). A mistura é de médias; a dispersão NB vem da validação. Depois os modelos-base
são reajustados com todo o período e os pesos congelados são aplicados.
"""

from __future__ import annotations

import numpy as np
from scipy import optimize


def poisson_deviance(y, mu):
    mu = np.maximum(mu, 1e-9)
    return float(np.mean(mu - y * np.log(mu)))


def fit_weights(y: np.ndarray, mus: np.ndarray) -> np.ndarray:
    """``mus``: [n, k] médias previstas fora da amostra. Devolve pesos no simplex."""
    k = mus.shape[1]
    f = lambda w: poisson_deviance(y, mus @ w)  # noqa: E731
    r = optimize.minimize(f, np.full(k, 1 / k), method="SLSQP", bounds=[(0, 1)] * k,
                          constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}], options={"maxiter": 300})
    w = np.clip(r.x, 0, None)
    return w / w.sum()
