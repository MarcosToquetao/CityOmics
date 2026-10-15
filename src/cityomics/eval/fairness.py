"""Auditoria de equidade (D11): desempenho por grupo de setores (quintis de renda, composição racial)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cityomics.eval.calibration import reliability


def quintile_groups(values, labels=("Q1", "Q2", "Q3", "Q4", "Q5")) -> pd.Series:
    return pd.qcut(pd.Series(values), 5, labels=list(labels), duplicates="drop")


def by_group(groups, pred_mean, obs, prob_ge1, event) -> pd.DataFrame:
    """Média prevista vs observada (razão), Brier e ECE de P(≥1) por grupo."""
    df = pd.DataFrame({"g": np.asarray(groups), "mu": pred_mean, "y": obs, "p": prob_ge1, "e": event})
    rows = []
    for g, d in df.groupby("g", observed=True):
        _, ece = reliability(d["p"].to_numpy(), d["e"].to_numpy())
        rows.append({"grupo": g, "n": len(d), "obs_sobre_prev": d["y"].sum() / d["mu"].sum(),
                     "brier": float(((d["p"] - d["e"]) ** 2).mean()), "ece": ece})
    return pd.DataFrame(rows)


def flagged_share(groups, rank_score, area, share: float = 0.01) -> pd.Series:
    """Fração da área sinalizada (top ``share`` da cidade por score/km²) que cai em cada grupo."""
    df = pd.DataFrame({"g": np.asarray(groups), "s": np.asarray(rank_score) / np.asarray(area), "a": np.asarray(area)})
    df = df.sort_values("s", ascending=False)
    sel = df[df["a"].cumsum() <= share * df["a"].sum()]
    return sel.groupby("g", observed=True)["a"].sum() / max(sel["a"].sum(), 1e-12)
