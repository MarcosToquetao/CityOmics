"""Rodada de ajuste/avaliação no período de tuning (ajusta em 2024, avalia em 2025, h=1).

O mesmo código roda depois com ``fit_year=2025`` e ``eval_year=2026`` (previsões congeladas, F7).
Escreve ``data/processed/modelo/resultados_<nome>.json`` com as métricas por modelo.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.eval import harness
from cityomics.models import baselines as B
from cityomics.paths import processed_dir

COLS = ["cd_setor", "mes", "cd_dist", "area_km2", "y", "y_geo", "h_int_l1", "h_int_l2", "h_int_l3", "h_int_s6", "h_int_s12",
        "h_int_l12", "nb_h_int_l1", "nb_h_int_s3", "nb_h_int_s12", "mes_num"]
BANDWIDTHS = (100, 200, 300, 450)


def load_table(nome: str = "tabela_celular_2022_2025.parquet", cols=None) -> pl.DataFrame:
    return pl.read_parquet(processed_dir() / "modelo" / nome, columns=cols or COLS)


def run_baselines(t: pl.DataFrame, centroids: np.ndarray, fit_year: str = "2024", eval_year: str = "2025", log=print) -> dict:
    fit = t.filter(pl.col("mes").str.starts_with(fit_year))
    ev = t.filter(pl.col("mes").str.starts_with(eval_year))
    d, idx = B.knn_kernel(centroids, k=60)
    results, params = {}, {}
    yfit = fit["y"].to_numpy()

    # larguras de banda escolhidas por log score no período de ajuste
    best = {}
    for kind in ("stkde", "hotspot_prospectivo"):
        sc = {}
        for bw in BANDWIDTHS:
            x = B.point_forecasts(fit, d, idx, bw, bw)[kind]
            a, b, phi = B.calibrate(x, yfit)
            from cityomics.eval import scores
            sc[bw] = scores.log_score(yfit, a * x + b, phi).mean()
        best[kind] = min(sc, key=sc.get)
        log(f"{kind}: largura {best[kind]} m (log score no ajuste {sc[best[kind]]:.4f})")
    bw, bwb = best["stkde"], best["hotspot_prospectivo"]
    pf_fit = B.point_forecasts(fit, d, idx, bw, bwb)
    pf_ev = B.point_forecasts(ev, d, idx, bw, bwb)
    for k in pf_fit:
        a, b, phi = B.calibrate(pf_fit[k], yfit)
        mu = np.where(np.isfinite(pf_ev[k]), a * np.nan_to_num(pf_ev[k]) + b, b)
        results[k] = harness.evaluate(ev, mu, phi)
        params[k] = {"a": a, "b": b, "phi": phi}
    # GLM de contagem
    train = t.filter(pl.col("mes") < f"{eval_year}-01").filter(pl.col("mes") >= f"{int(fit_year) - 1}-01")  # histórico completo até o fim do ajuste
    glm = B.fit_glm(train.filter(pl.col("mes") <= f"{fit_year}-12"))
    mu_fit = B.predict_glm(glm, fit)
    from cityomics.eval import scores as S
    phi = S.fit_phi(yfit, mu_fit)
    results["glm_contagem"] = harness.evaluate(ev, B.predict_glm(glm, ev), phi)
    params["glm_contagem"] = {"phi": phi}
    return {"resultados": results, "parametros": params, "bw_stkde": bw, "bw_hotspot": bwb}


def save(nome: str, obj: dict) -> None:
    d = processed_dir() / "modelo"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"resultados_{nome}.json").write_text(json.dumps(obj, indent=2))


def table_text(res: dict) -> str:
    cols = ["crps", "logscore", "brier", "ece", "pai1", "pai5", "mu_sobre_y"]
    lines = ["modelo".ljust(22) + "".join(c.rjust(11) for c in cols)]
    for k, v in sorted(res.items(), key=lambda kv: kv[1]["crps"]):
        lines.append(k.ljust(22) + "".join(f"{v[c]:11.4f}" for c in cols))
    return "\n".join(lines)
