"""Calibração: PIT randomizado, diagrama de confiabilidade e ECE (prereg §5.3)."""

from __future__ import annotations

import numpy as np

from cityomics.eval.scores import nb_scipy
from scipy import stats


def randomized_pit(y, mu, phi, seed: int = 0):
    """PIT randomizado para contagens: u ~ U[F(y−1), F(y)] (y arredondado)."""
    rng = np.random.default_rng(seed)
    y = np.rint(np.asarray(y, dtype="float64"))
    n, p = nb_scipy(mu, phi)
    hi = stats.nbinom.cdf(y, n, p)
    lo = np.where(y > 0, stats.nbinom.cdf(y - 1, n, p), 0.0)
    return lo + rng.random(y.shape) * (hi - lo)


def pit_histogram(pit, bins: int = 10) -> np.ndarray:
    """Frequências relativas por faixa (uniforme = 1/bins)."""
    h, _ = np.histogram(pit, bins=bins, range=(0, 1))
    return h / h.sum()


def reliability(prob, event, bins: int = 10):
    """Tabela (prob. média prevista, frequência observada, n) por faixa de quantis e o ECE."""
    prob, event = np.asarray(prob, dtype="float64"), np.asarray(event, dtype="float64")
    edges = np.unique(np.quantile(prob, np.linspace(0, 1, bins + 1)))
    b = np.clip(np.searchsorted(edges, prob, side="right") - 1, 0, len(edges) - 2)
    rows = [(prob[b == j].mean(), event[b == j].mean(), int((b == j).sum())) for j in range(len(edges) - 1) if (b == j).any()]
    n = len(prob)
    ece = sum(c / n * abs(p - o) for p, o, c in rows)
    return rows, float(ece)
