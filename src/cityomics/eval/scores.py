"""Escores probabilísticos para contagens com distribuição binomial negativa (NB2).

A NB2 tem média ``mu`` e dispersão ``phi`` (variância ``mu + mu²/phi``). Para o pré-registro
(§5.3, emenda A6) a observação é real (contagem reconciliada), e o CRPS é

    CRPS(F, y) = ∫ (F(x) − 1{x ≥ y})² dx.

Como ``F`` é constante em cada [k, k + 1), para ``y`` em [j, j + 1) a integral vale
Σ_{k≠j} (F(k) − 1{k ≥ y})² + (y − j)·F(j)² + (j + 1 − y)·(F(j) − 1)², a interpolação linear entre o
CRPS de ⌊y⌋ e o de ⌈y⌉. Para ``y`` inteiro coincide com ``E|X − y| − ½ E|X − X'|`` (testes).

Correção de 2026-10-20 (parecer crítico; paper/review/parecer/A_reconciliacao.md): a versão anterior
usava Σₖ (F(k) − 1{k ≥ y})², a fórmula escrita no §5.3, que com ``y`` fracionário dá o CRPS de ⌈y⌉
(trata uma contagem de 0,03 como um evento). ``crps_nb_registrado`` mantém essa fórmula para
reproduzir os números anteriores; a emenda que registra a correção está em ``prereg/A12_DRAFT.md``.
"""

from __future__ import annotations

import numpy as np
from scipy import optimize, special, stats


def nb_scipy(mu, phi):
    """Parâmetros (n, p) do ``scipy.stats.nbinom`` para média ``mu`` e dispersão ``phi``."""
    mu = np.asarray(mu, dtype="float64")
    phi = np.broadcast_to(np.asarray(phi, dtype="float64"), mu.shape)
    return phi, phi / (phi + np.maximum(mu, 1e-12))


def nb_logpmf(y, mu, phi):
    n, p = nb_scipy(mu, phi)
    return stats.nbinom.logpmf(np.asarray(y), n, p)


def log_score(y, mu, phi):
    """Escore logarítmico (menor é melhor) sobre a contagem arredondada."""
    return -nb_logpmf(np.rint(y), mu, phi)


def crps_nb(y, mu, phi, chunk: int = 50_000):
    """CRPS da NB2 contra ``y`` real ou inteiro: o da fórmula registrada em ⌈y⌉ menos
    (⌈y⌉ − y)·(2F(⌊y⌋) − 1), que é a integral exata no intervalo [⌊y⌋, ⌈y⌉)."""
    y = np.asarray(y, dtype="float64")
    mu = np.broadcast_to(np.asarray(mu, dtype="float64"), y.shape)
    phi = np.broadcast_to(np.asarray(phi, dtype="float64"), y.shape)
    teto = np.ceil(y)
    out = crps_nb_registrado(teto, mu, phi, chunk)
    frac = teto > y
    if frac.any():
        n, p = nb_scipy(mu[frac], phi[frac])
        out[frac] -= (teto[frac] - y[frac]) * (2.0 * stats.nbinom.cdf(np.floor(y[frac]), n, p) - 1.0)
    return out


def crps_nb_registrado(y, mu, phi, chunk: int = 50_000):
    """Σₖ (F(k) − 1{k ≥ y})², a fórmula do §5.3: o CRPS para ``y`` inteiro e o CRPS de ⌈y⌉ para ``y``
    fracionário. Só para reproduzir os números anteriores à correção; use ``crps_nb``."""
    y = np.asarray(y, dtype="float64")
    mu = np.broadcast_to(np.asarray(mu, dtype="float64"), y.shape)
    phi = np.broadcast_to(np.asarray(phi, dtype="float64"), y.shape)
    out = np.empty(y.shape, dtype="float64")
    order = np.argsort(mu, kind="stable")
    for i in range(0, len(order), chunk):
        idx = order[i:i + chunk]
        n, p = nb_scipy(mu[idx], phi[idx])
        kmax = int(max(np.ceil(y[idx].max()), stats.nbinom.ppf(0.99999, n, p).max())) + 1
        k = np.arange(kmax + 1)
        cdf = stats.nbinom.cdf(k[None, :], n[:, None], p[:, None])
        ind = (k[None, :] >= y[idx][:, None]).astype("float64")
        out[idx] = ((cdf - ind) ** 2).sum(axis=1)
    return out


def prob_ge1(mu, phi):
    n, p = nb_scipy(mu, phi)
    return 1.0 - stats.nbinom.pmf(0, n, p)


def prob_ge(mu, phi, k):
    n, p = nb_scipy(mu, phi)
    return 1.0 - stats.nbinom.cdf(k - 1, n, p)


def brier(prob, event):
    prob, event = np.asarray(prob, dtype="float64"), np.asarray(event, dtype="float64")
    return (prob - event) ** 2


def brier_decomposition(prob, event, bins: int = 10) -> dict[str, float]:
    """Brier = confiabilidade − resolução + incerteza (Murphy, bins de probabilidade iguais)."""
    prob, event = np.asarray(prob, dtype="float64"), np.asarray(event, dtype="float64")
    obar = event.mean()
    edges = np.quantile(prob, np.linspace(0, 1, bins + 1))
    b = np.clip(np.searchsorted(edges, prob, side="right") - 1, 0, bins - 1)
    rel = res = 0.0
    for j in range(bins):
        m = b == j
        if not m.any():
            continue
        w, pj, oj = m.mean(), prob[m].mean(), event[m].mean()
        rel += w * (pj - oj) ** 2
        res += w * (oj - obar) ** 2
    return {"brier": float(((prob - event) ** 2).mean()), "reliability": float(rel), "resolution": float(res),
            "uncertainty": float(obar * (1 - obar))}


def fit_phi(y, mu, lo: float = 1e-2, hi: float = 1e4) -> float:
    """Dispersão NB2 global por máxima verossimilhança dado ``mu`` (pré-registro §5.3, só período de tuning)."""
    y = np.rint(np.asarray(y, dtype="float64"))
    mu = np.maximum(np.asarray(mu, dtype="float64"), 1e-9)

    def nll(logphi: float) -> float:
        phi = np.exp(logphi)
        ll = (special.gammaln(y + phi) - special.gammaln(phi) - special.gammaln(y + 1)
              + phi * np.log(phi / (phi + mu)) + y * np.log(mu / (phi + mu)))
        return -ll.sum()

    r = optimize.minimize_scalar(nll, bounds=(np.log(lo), np.log(hi)), method="bounded")
    return float(np.exp(r.x))
