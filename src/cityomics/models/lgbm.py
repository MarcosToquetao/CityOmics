"""LightGBM (Poisson/Tweedie) com lags espaciais e temporais (spec-benchmark §3.2).

Duas configurações, mesma interface:

- ``completo``: histórico as-of + vizinhança + todas as covariáveis numéricas do painel;
- ``nucleo``: histórico + núcleo teórico pré-especificado (``prereg/core_covariates.json``);
- ``sem_crime``: covariáveis sem nenhum histórico de crime (ablação D6).

O alvo é a contagem reconciliada (real); a perda Poisson aceita alvos reais. A distribuição NB vem
de uma dispersão global ajustada por máxima verossimilhança no período de ajuste (prereg §5.3).
Os hiperparâmetros são escolhidos por CV com **blocos de tempo** dentro do ajuste e sem olhar o
período de avaliação.
"""

from __future__ import annotations

import json

import lightgbm as lgb
import numpy as np
import polars as pl

from cityomics.eval import scores
from cityomics.paths import REPO_ROOT

ID_COLS = {"cd_setor", "mes", "cd_dist", "y", "y_geo"}
HIST_PREFIXES = ("h_", "nb_h_", "nr_w")      # tudo que vem do histórico de crime (ablação D6)


def feature_sets(columns: list[str]) -> dict[str, list[str]]:
    core = json.loads((REPO_ROOT / "prereg" / "core_covariates.json").read_text())
    core_cols = [c for g in core["groups"].values() for c in g if c in columns]
    hist = [c for c in columns if c.startswith(HIST_PREFIXES)]
    todas = [c for c in columns if c not in ID_COLS and c != "area_km2"]
    cov = [c for c in todas if c not in hist]
    return {"completo": ["area_km2"] + todas, "nucleo": ["area_km2"] + hist + core_cols + ["mes_num"],
            "sem_crime": ["area_km2"] + cov, "so_historico": ["area_km2"] + hist + ["mes_num"]}


DEFAULT_PARAMS = {"objective": "poisson", "learning_rate": 0.05, "num_leaves": 63, "min_data_in_leaf": 200,
                  "feature_fraction": 0.7, "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 10.0,
                  "verbose": -1, "num_threads": 0, "seed": 1}


def _xy(df: pl.DataFrame, feats: list[str]):
    return df.select(feats).to_numpy().astype("float32"), df["y"].to_numpy().astype("float64")


def fit(train: pl.DataFrame, feats: list[str], params: dict | None = None, rounds: int = 400, valid: pl.DataFrame | None = None):
    p = {**DEFAULT_PARAMS, **(params or {})}
    x, y = _xy(train, feats)
    dtrain = lgb.Dataset(x, y, feature_name=feats, free_raw_data=False)
    sets, cb = [], []
    if valid is not None:
        xv, yv = _xy(valid, feats)
        sets = [lgb.Dataset(xv, yv, reference=dtrain)]
        cb = [lgb.early_stopping(40, verbose=False)]
    return lgb.train(p, dtrain, num_boost_round=rounds, valid_sets=sets, callbacks=cb)


def predict(model, df: pl.DataFrame, feats: list[str]) -> np.ndarray:
    return model.predict(df.select(feats).to_numpy().astype("float32"))


def tune(train: pl.DataFrame, feats: list[str], grid: list[dict], log=print) -> tuple[dict, int]:
    """Escolhe hiperparâmetros por validação temporal dentro do ajuste: treina nos meses antes do último
    semestre do ajuste e valida no último semestre (Poisson deviance); devolve (params, nº de rodadas)."""
    meses = sorted(train["mes"].unique().to_list())
    corte = meses[-6]
    a, b = train.filter(pl.col("mes") < corte), train.filter(pl.col("mes") >= corte)
    best = (np.inf, None, 0)
    for g in grid:
        m = fit(a, feats, g, rounds=800, valid=b)
        score = m.best_score["valid_0"]["poisson"]
        log(f"  {g} -> poisson {score:.5f} em {m.best_iteration} rodadas")
        if score < best[0]:
            best = (score, g, m.best_iteration)
    return best[1], max(best[2], 50)


def evaluate_models(t: pl.DataFrame, fit_year: str, eval_year: str, sets: dict[str, list[str]], grid: list[dict], log=print) -> dict:
    from cityomics.eval import harness

    first_ok = f"{int(fit_year) - 1}-01"      # lags de 12 meses só existem a partir de 2023-01
    train = t.filter((pl.col("mes") <= f"{fit_year}-12") & (pl.col("mes") >= "2023-01") if int(fit_year) >= 2024 else pl.col("mes") <= f"{fit_year}-12")
    ev = t.filter(pl.col("mes").str.starts_with(eval_year))
    out = {}
    for nome, feats in sets.items():
        log(f"{nome}: {len(feats)} features")
        params, rounds = tune(train, feats, grid, log=log)
        m = fit(train, feats, params, rounds=rounds)
        mu_fit = predict(m, train, feats)
        phi = scores.fit_phi(train["y"].to_numpy(), mu_fit)
        mu = predict(m, ev, feats)
        out[nome] = {"metrics": harness.evaluate(ev, mu, phi), "params": params, "rounds": rounds,
                     "importance": dict(sorted(zip(feats, m.feature_importance("gain").tolist()), key=lambda kv: -kv[1])[:25])}
    return out
