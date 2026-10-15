"""Métricas operacionais de hotspot: hit rate, PAI e PEI (prereg §5.3).

Os setores são ordenados pela média prevista por km² e entram até a área acumulada alcançar a
fração-alvo da área da cidade; o hit rate é a fração das ocorrências observadas dentro deles.
PAI = hit rate / fração de área. PEI = ocorrências capturadas / ocorrências que o melhor
conjunto possível (ordenado pelo observado por km²) capturaria na mesma área.
"""

from __future__ import annotations

import numpy as np

SHARES = (0.005, 0.01, 0.02, 0.05, 0.10)


def _capture(rank_score, area, obs, share):
    order = np.argsort(-rank_score, kind="stable")
    cum_area = np.cumsum(area[order])
    k = int(np.searchsorted(cum_area, share * area.sum(), side="left")) + 1
    k = min(k, len(order))
    sel = order[:k]
    return obs[sel].sum(), area[sel].sum() / area.sum()


def hotspot_metrics(pred_mean, area, obs, shares=SHARES) -> dict[float, dict[str, float]]:
    """Métricas de um mês (ou de um bloco): vetores por setor de média prevista, área e observado."""
    pred_mean, area, obs = (np.asarray(x, dtype="float64") for x in (pred_mean, area, obs))
    total = obs.sum()
    out = {}
    for s in shares:
        hit, a = _capture(pred_mean / area, area, obs, s)
        best, _ = _capture(obs / area, area, obs, s)
        hr = hit / total if total > 0 else np.nan
        out[s] = {"hit_rate": hr, "pai": hr / a if total > 0 else np.nan,
                  "pei": hit / best if best > 0 else np.nan, "area_share": a}
    return out


def monthly_average(frames, shares=SHARES) -> dict[float, dict[str, float]]:
    """Média dos meses. ``frames``: iterável de (pred_mean, area, obs) por mês."""
    rows = [hotspot_metrics(p, a, o, shares) for p, a, o in frames]
    return {s: {m: float(np.nanmean([r[s][m] for r in rows])) for m in ("hit_rate", "pai", "pei", "area_share")}
            for s in shares}
