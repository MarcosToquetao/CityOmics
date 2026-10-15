"""Inferência: bootstrap por cluster (distrito) e correção de Holm (prereg §5.4)."""

from __future__ import annotations

import numpy as np


def cluster_bootstrap_diff(loss_a, loss_b, clusters, n_boot: int = 2000, seed: int = 0) -> dict[str, float]:
    """Diferença média pareada ``loss_a − loss_b`` com bootstrap de clusters inteiros.

    Reamostra distritos com todas as suas células e meses, o que preserva a dependência espacial e
    temporal. Negativo = ``a`` melhor (perda menor). ``p`` é bilateral, pela distribuição bootstrap
    centrada na hipótese nula.
    """
    d = np.asarray(loss_a, dtype="float64") - np.asarray(loss_b, dtype="float64")
    _, inv = np.unique(np.asarray(clusters), return_inverse=True)
    k = inv.max() + 1
    sums = np.bincount(inv, weights=d, minlength=k)
    cnt = np.bincount(inv, minlength=k).astype("float64")
    rng = np.random.default_rng(seed)
    w = rng.multinomial(k, np.full(k, 1 / k), size=n_boot).astype("float64")
    boot = (w @ sums) / (w @ cnt)
    est = sums.sum() / cnt.sum()
    lo, hi = np.quantile(boot, [0.025, 0.975])
    centered = boot - boot.mean()
    p = float((np.abs(centered) >= abs(est)).mean())
    return {"diff": float(est), "ci_low": float(lo), "ci_high": float(hi), "p": max(p, 1 / n_boot), "n_clusters": int(k)}


def holm(pvalues: dict[str, float], alpha: float = 0.05) -> dict[str, dict[str, float | bool]]:
    """Ajuste de Holm-Bonferroni (controle do erro familiar)."""
    names = sorted(pvalues, key=pvalues.get)
    m = len(names)
    out, running = {}, 0.0
    for i, nme in enumerate(names):
        adj = min(1.0, (m - i) * pvalues[nme])
        running = max(running, adj)
        out[nme] = {"p": pvalues[nme], "p_adj": running, "reject": running < alpha}
    return out


def cluster_bootstrap_ratio_diff(num_a, num_b, den, clusters, n_boot: int = 2000, seed: int = 0) -> dict[str, float]:
    """Diferença ``Σnum_a/Σden − Σnum_b/Σden`` com bootstrap de clusters (razão de somas).

    Serve para o hit rate: ``num`` = ocorrências dentro do hotspot, ``den`` = ocorrências totais.
    Positivo = ``a`` captura mais. A razão é reagregada em cada reamostra.
    """
    d = np.asarray(num_a, dtype="float64") - np.asarray(num_b, dtype="float64")
    _, inv = np.unique(np.asarray(clusters), return_inverse=True)
    k = inv.max() + 1
    sd = np.bincount(inv, weights=d, minlength=k)
    sn = np.bincount(inv, weights=np.asarray(den, dtype="float64"), minlength=k)
    rng = np.random.default_rng(seed)
    w = rng.multinomial(k, np.full(k, 1 / k), size=n_boot).astype("float64")
    boot = (w @ sd) / (w @ sn)
    est = sd.sum() / sn.sum()
    lo, hi = np.quantile(boot, [0.025, 0.975])
    p = float((np.abs(boot - boot.mean()) >= abs(est)).mean())
    return {"diff": float(est), "ci_low": float(lo), "ci_high": float(hi), "p": max(p, 1 / n_boot), "n_clusters": int(k)}
