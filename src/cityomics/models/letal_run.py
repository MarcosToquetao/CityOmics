"""Benchmark reduzido por distrito × trimestre: violência letal e, pareado, o celular (D41, D61).

Mesma escala para os dois desfechos, para que o contraste "tecido fino × órgão" não confunda o
desfecho com a agregação (D61). Ajuste em 2022Q1–2024Q4, avaliação em 2025Q1–Q4 (96 distritos).

Modelos:
- ``media_historica``: média dos 4 trimestres anteriores;
- ``glm``: Poisson com lags (t−1, média de 4) e log da população como offset;
- ``eb_espacial``: Poisson-gama bayesiano empírico com encolhimento para a média dos vizinhos (é o
  BYM2 aproximado: o BYM2 completo no INLA fica para o F7, por custo);
- ``hawkes``: μ_d + α Σ_k e^{−β k} y_{d,t−k} (autoexcitação discreta por distrito);
- ``lgbm``: LightGBM Poisson com lags, sazonalidade e os 4 escores teóricos médios do distrito.

Métricas: CRPS, log score (NB com dispersão ajustada no período de ajuste) e Brier de P(≥1);
bootstrap por distrito e Holm contra o GLM. O SHAP do LightGBM da letal vai para a Fig. 4e.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.eval import inference, scores
from cityomics.paths import processed_dir

FIT = ("2022Q1", "2024Q4")
EVAL = ("2025Q1", "2025Q4")


def panel(outcome: str) -> pl.DataFrame:
    if outcome == "letal":
        t = pl.read_parquet(processed_dir() / "alvos" / "letal_distrito_trimestre.parquet").rename({"composto": "y"}).drop("estrito")
    else:
        c = pl.read_parquet(processed_dir() / "alvos" / "celular_setor_mes.parquet")
        c = c.with_columns((pl.col("periodo").str.slice(0, 4) + "Q" + ((pl.col("periodo").str.slice(5, 2).cast(pl.Int32) - 1) // 3 + 1).cast(pl.String)).alias("q"))
        t = c.group_by("cd_dist", "q").agg(pl.col("n_total").sum().alias("y")).rename({"q": "periodo"})
    t = t.with_columns(pl.col("y").cast(pl.Float64)).sort("cd_dist", "periodo")
    dist = pl.read_parquet(processed_dir() / "units" / "distritos.parquet", columns=["cd_dist", "pop_2022"]).with_columns(pl.col("cd_dist").cast(pl.String))
    t = t.with_columns(pl.col("cd_dist").cast(pl.String)).join(dist, on="cd_dist", how="left")
    t = t.with_columns(
        pl.col("y").shift(1).over("cd_dist").alias("l1"),
        pl.col("y").shift(4).over("cd_dist").alias("l4"),
        pl.col("y").shift(1).rolling_mean(4).over("cd_dist").alias("m4"),
        pl.col("y").shift(1).rolling_mean(8, min_samples=4).over("cd_dist").alias("m8"),
        pl.col("periodo").str.slice(5, 1).cast(pl.Int32).alias("trim"),
    )
    return t


def _nb(y, mu):
    phi = scores.fit_phi(y, mu)
    return phi


def _hawkes_fit(Y: np.ndarray, kmax: int = 4):
    """Y: (distritos, tempo). μ_d por distrito + α, β comuns; máxima verossimilhança Poisson."""
    from scipy.optimize import minimize

    D, T = Y.shape

    def pred(theta, Y):
        mu = np.exp(theta[:D])
        a, b = np.exp(theta[D]), np.exp(theta[D + 1])
        lam = np.tile(mu[:, None], (1, Y.shape[1]))
        for k in range(1, kmax + 1):
            lam[:, k:] += a * np.exp(-b * (k - 1)) * Y[:, :-k]
        return lam

    def nll(theta):
        lam = pred(theta, Y)[:, kmax:]
        yy = Y[:, kmax:]
        return float(np.sum(lam - yy * np.log(np.clip(lam, 1e-9, None))))

    th0 = np.concatenate([np.log(Y.mean(1) + 0.1), [np.log(0.1), np.log(0.5)]])
    r = minimize(nll, th0, method="L-BFGS-B")
    return r.x, pred


def run_outcome(outcome: str, log=print) -> dict:
    import lightgbm as lgb
    from sklearn.linear_model import PoissonRegressor

    from cityomics.atlas.attribution import GROUPS, group_scores

    t = panel(outcome)
    z = group_scores().join(pl.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "cd_dist", "pop_2022"])
                            .with_columns(pl.col("cd_setor").cast(pl.String), pl.col("cd_dist").cast(pl.String)), on="cd_setor")
    zd = z.group_by("cd_dist").agg([((pl.col(g) * pl.col("pop_2022")).sum() / pl.col("pop_2022").sum()).alias(g) for g in GROUPS])
    t = t.join(zd, on="cd_dist", how="left")
    fit = t.filter((pl.col("periodo") >= FIT[0]) & (pl.col("periodo") <= FIT[1]) & pl.col("m4").is_not_null())
    ev = t.filter((pl.col("periodo") >= EVAL[0]) & (pl.col("periodo") <= EVAL[1]))
    y_f, y_e = fit["y"].to_numpy(), ev["y"].to_numpy()
    preds_f, preds_e = {}, {}
    preds_f["media_historica"], preds_e["media_historica"] = fit["m4"].to_numpy(), ev["m4"].to_numpy()
    feats = ["l1", "m4", "m8"]
    Xf = np.log1p(fit.select(feats).fill_null(0).to_numpy())
    Xe = np.log1p(ev.select(feats).fill_null(0).to_numpy())
    off_f, off_e = np.log(fit["pop_2022"].to_numpy()), np.log(ev["pop_2022"].to_numpy())
    glm = PoissonRegressor(alpha=1e-6, max_iter=1000).fit(np.column_stack([Xf, off_f]), y_f)
    preds_f["glm"], preds_e["glm"] = glm.predict(np.column_stack([Xf, off_f])), glm.predict(np.column_stack([Xe, off_e]))
    # bayesiano empírico espacial: taxa do distrito encolhida para a dos vizinhos (contiguidade de distritos)
    from cityomics.atlas.niches import queen_neighbors

    nb = queen_neighbors()
    sd = pl.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "cd_dist"]).with_columns(pl.col("cd_setor").cast(pl.String), pl.col("cd_dist").cast(pl.String))
    dd = (nb.join(sd, on="cd_setor").join(sd.rename({"cd_setor": "vizinho", "cd_dist": "dv"}), on="vizinho")
          .filter(pl.col("cd_dist") != pl.col("dv")).select("cd_dist", "dv").unique())
    rate = fit.group_by("cd_dist").agg((pl.col("y").sum() / pl.len()).alias("r"))
    nbr = dd.join(rate.rename({"cd_dist": "dv", "r": "rv"}), on="dv").group_by("cd_dist").agg(pl.col("rv").mean())
    eb = rate.join(nbr, on="cd_dist", how="left").with_columns(pl.col("rv").fill_null(pl.col("r").mean()))
    nq = fit.group_by("cd_dist").len().rename({"len": "nq"})
    eb = eb.join(nq, on="cd_dist").with_columns(((pl.col("r") * pl.col("nq") + 2.0 * pl.col("rv")) / (pl.col("nq") + 2.0)).alias("eb"))
    preds_f["eb_espacial"] = fit.join(eb.select("cd_dist", "eb"), on="cd_dist", how="left")["eb"].to_numpy()
    preds_e["eb_espacial"] = ev.join(eb.select("cd_dist", "eb"), on="cd_dist", how="left")["eb"].to_numpy()
    # Hawkes discreto por distrito
    wide = t.pivot(on="periodo", index="cd_dist", values="y").sort("cd_dist")
    cols = sorted([c for c in wide.columns if c != "cd_dist"])
    Y = wide.select(cols).to_numpy().astype(float)
    nfit = cols.index(FIT[1]) + 1
    theta, pred = _hawkes_fit(Y[:, :nfit])
    lam = pred(theta, Y)
    hk = pl.DataFrame({"cd_dist": np.repeat(wide["cd_dist"].to_numpy(), len(cols)), "periodo": np.tile(cols, len(wide)),
                       "hk": lam.ravel()})
    preds_f["hawkes"] = fit.join(hk, on=["cd_dist", "periodo"], how="left")["hk"].to_numpy()
    preds_e["hawkes"] = ev.join(hk, on=["cd_dist", "periodo"], how="left")["hk"].to_numpy()
    lf = feats + ["l4", "trim"] + GROUPS
    Lf = fit.select(lf).fill_null(0).to_numpy()
    Le = ev.select(lf).fill_null(0).to_numpy()
    ds = lgb.Dataset(np.column_stack([Lf, off_f]), y_f, feature_name=lf + ["log_pop"])
    m = lgb.train({"objective": "poisson", "learning_rate": 0.03, "num_leaves": 7, "min_data_in_leaf": 20, "verbose": -1,
                   "seed": 1, "lambda_l2": 5.0}, ds, num_boost_round=300)
    preds_f["lgbm"], preds_e["lgbm"] = m.predict(np.column_stack([Lf, off_f])), m.predict(np.column_stack([Le, off_e]))
    contrib = m.predict(np.column_stack([Le, off_e]), pred_contrib=True)[:, :-1]
    shap = {f: float(v) for f, v in zip(lf + ["log_pop"], np.abs(contrib).mean(0))}
    res, losses = {}, {}
    for k in preds_e:
        mu_f = np.clip(np.nan_to_num(preds_f[k], nan=y_f.mean()), 1e-6, None)
        mu_e = np.clip(np.nan_to_num(preds_e[k], nan=y_f.mean()), 1e-6, None)
        phi = _nb(y_f, mu_f)
        crps = scores.crps_nb(y_e, mu_e, phi)
        ls = scores.log_score(y_e, mu_e, phi)
        br = (scores.prob_ge1(mu_e, phi) - (y_e >= 1)) ** 2
        losses[k] = crps
        res[k] = {"crps": float(np.mean(crps)), "log_score": float(np.mean(ls)), "brier": float(np.mean(br)), "phi": float(phi)}
    clusters = ev["cd_dist"].to_numpy()
    tests = {k: inference.cluster_bootstrap_diff(losses[k], losses["glm"], clusters, n_boot=2000) for k in losses if k != "glm"}
    hol = inference.holm({k: v["p"] for k, v in tests.items()})
    out = {"desfecho": outcome, "media_y_2025": float(y_e.mean()), "modelos": res,
           "contra_glm": {k: tests[k] | hol[k] for k in tests}, "shap_lgbm": shap}
    log(f"{outcome} distrito × trimestre: CRPS " + ", ".join(f"{k} {v['crps']:.3f}" for k, v in res.items()))
    return out


def run(log=print) -> dict:
    out = {o: run_outcome(o, log=log) for o in ("letal", "celular")}
    (processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return out
