"""Recalibração isotônica e comparação do Laya com o LightGBM no mesmo estado comprimido (H2).

- ``calibrate``: regressão isotônica de ``P(≥1)`` bruto do Laya sobre o evento observado, em um
  conjunto de recalibração **posterior ao treino** (2025 no protocolo final; 2024-H2 no desenvolvimento).
- ``lgbm_on_state``: LightGBM com exatamente o vetor numérico equivalente ao texto
  (``numeric_*.parquet``); é o comparador de H2.
- ``brier_compare``: Brier de P(≥1) dos dois, com bootstrap por distrito.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression

from cityomics.eval import inference


def calibrate(p_raw_recal: np.ndarray, event_recal: np.ndarray) -> IsotonicRegression:
    iso = IsotonicRegression(y_min=1e-4, y_max=1 - 1e-4, out_of_bounds="clip")
    iso.fit(p_raw_recal, event_recal)
    return iso


def lgbm_on_state(num_train: pl.DataFrame, y_train: np.ndarray, num_pred: pl.DataFrame, rounds: int = 300):
    import lightgbm as lgb

    feats = [c for c in num_train.columns if c != "state_id"]
    p = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 200, "feature_fraction": 0.8,
         "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 10, "verbose": -1, "seed": 1}
    ds = lgb.Dataset(num_train.select(feats).to_numpy().astype("float32"), (y_train >= 0.5).astype(float))
    m = lgb.train(p, ds, num_boost_round=rounds)
    return m.predict(num_pred.select(feats).to_numpy().astype("float32"))


def brier_compare(p_a: np.ndarray, p_b: np.ndarray, event: np.ndarray, clusters: np.ndarray, n_boot: int = 2000) -> dict:
    la, lb = (p_a - event) ** 2, (p_b - event) ** 2
    return {"brier_a": float(la.mean()), "brier_b": float(lb.mean()),
            **inference.cluster_bootstrap_diff(la, lb, clusters, n_boot=n_boot)}
