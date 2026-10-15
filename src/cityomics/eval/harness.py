"""Avaliação de previsões h=1 de setor × mês: todas as métricas do pré-registro §5.3 de uma vez."""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.eval import calibration, hotspot, scores


def per_row_scores(y, mu, phi) -> dict[str, np.ndarray]:
    ev = (np.asarray(y) >= 0.5).astype("float64")
    p1 = scores.prob_ge1(mu, phi)
    return {"crps": scores.crps_nb(y, mu, phi), "logscore": scores.log_score(y, mu, phi),
            "brier": scores.brier(p1, ev), "p1": p1, "event": ev}


def evaluate(df: pl.DataFrame, mu: np.ndarray, phi: float, shares=(0.01, 0.05)) -> dict:
    """``df``: colunas ``y``, ``mes``, ``area_km2``. ``mu``: média prevista por linha."""
    y = df["y"].to_numpy().astype("float64")
    s = per_row_scores(y, mu, phi)
    nz = y >= 0.5
    mes = df["mes"].to_numpy()
    area = df["area_km2"].to_numpy()
    frames = [(mu[mes == m], area[mes == m], y[mes == m]) for m in np.unique(mes)]
    hs = hotspot.monthly_average(frames, shares)
    rows, ece = calibration.reliability(s["p1"], s["event"])
    out = {"crps": float(s["crps"].mean()), "crps_nz": float(s["crps"][nz].mean()), "logscore": float(s["logscore"].mean()),
           "brier": float(s["brier"].mean()), "ece": ece, "mu_sobre_y": float(mu.sum() / y.sum()), "phi": float(phi)}
    for sh in shares:
        out[f"pai{int(sh * 100)}"] = hs[sh]["pai"]
        out[f"hit{int(sh * 100)}"] = hs[sh]["hit_rate"]
    return out
