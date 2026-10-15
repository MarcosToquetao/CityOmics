"""Rodada completa do benchmark no desenvolvimento: previsões de todos os modelos, ensemble e métricas.

Janelas (ajuste → previsão), todas só com meses anteriores:
- validação do ensemble: ajuste 2023-01..2024-06 → 2024-07..2024-12;
- avaliação (tuning): ajuste 2023-01..2024-12 → 2025-01..2025-12.
Grava as previsões por modelo em ``data/processed/modelo/pred_<tag>.parquet`` e as métricas em
``resultados_benchmark_<tag>.json``. O mesmo código, com janelas deslocadas um ano, gera as
previsões congeladas de 2026 depois do congelamento (F7).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.eval import harness, scores
from cityomics.features import table as tbl
from cityomics.models import ensemble, zoo
from cityomics.models.baselines import knn_kernel
from cityomics.paths import processed_dir

MODELS = ["media_historica", "glm", "kde", "chronos", "gwr_distrito", "painel_espacial", "maxent", "bym2", "spde",
          "hawkes", "lgbm_nucleo", "lgbm_sem_crime", "lgbm_completo", "gnn"]
VAL = ("2023-01", "2024-06", "2024-07", "2024-12")
EVAL = ("2023-01", "2024-12", "2025-01", "2025-12")


def make_ctx(table: pl.DataFrame):
    from cityomics.units.setores import load_setores

    s = load_setores().sort_values("cd_setor").reset_index(drop=True)
    cent = np.column_stack([s.geometry.centroid.x, s.geometry.centroid.y])
    cx = processed_dir() / "modelo" / "chronos_x_2023_2025.parquet"
    return {"setores": s, "knn_idx": tbl.vizinhos(cent), "kde_kernel": knn_kernel(cent, k=60),
            "chronos_x": pl.read_parquet(cx) if cx.exists() else None}


def predictions(table: pl.DataFrame, win, models, ctx, log=print):
    fi, ff, pi, pf = win
    pred = table.filter((pl.col("mes") >= pi) & (pl.col("mes") <= pf)).sort("mes", "cd_setor")
    out = pred.select("cd_setor", "mes", "y", "area_km2")
    phis = {}
    for m in models:
        log(f"{m}: {fi}..{ff} -> {pi}..{pf}")
        _, mp, phi = zoo.run(m, table, fi, ff, pi, pf, ctx)
        out = out.with_columns(pl.Series(f"mu_{m}", mp))
        phis[m] = phi
    return out, phis


def run(table: pl.DataFrame, tag: str = "dev", models=MODELS, log=print) -> dict:
    ctx = make_ctx(table)
    val, phi_val = predictions(table, VAL, models, ctx, log)
    ev, phi_ev = predictions(table, EVAL, models, ctx, log)
    val.write_parquet(processed_dir() / "modelo" / f"pred_{tag}_val.parquet")
    ev.write_parquet(processed_dir() / "modelo" / f"pred_{tag}_eval.parquet")
    # ensemble: pesos na validação, aplicados em 2025
    mus_val = np.column_stack([val[f"mu_{m}"].to_numpy() for m in models])
    w = ensemble.fit_weights(val["y"].to_numpy(), mus_val)
    log("pesos do ensemble: " + ", ".join(f"{m} {x:.2f}" for m, x in zip(models, w) if x > 0.005))
    mu_ens_val = mus_val @ w
    phi_ens = scores.fit_phi(val["y"].to_numpy(), mu_ens_val)
    res = {m: harness.evaluate(ev, ev[f"mu_{m}"].to_numpy(), phi_ev[m]) for m in models}
    mus_ev = np.column_stack([ev[f"mu_{m}"].to_numpy() for m in models])
    res["ensemble"] = harness.evaluate(ev, mus_ev @ w, phi_ens)
    out = {"resultados": res, "pesos": dict(zip(models, map(float, w))), "phi_eval": phi_ev}
    (processed_dir() / "modelo" / f"resultados_benchmark_{tag}.json").write_text(json.dumps(out, indent=2))
    return out
