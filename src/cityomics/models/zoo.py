"""Zoológico de modelos com interface única, para ensemble e ablações (F5).

``run(nome, table, fit_ini, fit_fim, pred_ini, pred_fim)`` ajusta ``nome`` nos meses
``[fit_ini, fit_fim]`` e devolve ``(mu_ajuste, mu_previsão, phi)`` para os meses de ajuste e de
previsão. Todos usam só features as-of da tabela. Assim o mesmo código serve para (a) validar o
ensemble (ajuste 2023–2024H1, previsão 2024H2), (b) avaliar 2025 (ajuste 2023–2024) e (c) as
previsões congeladas de 2026 (ajuste 2023–2025), depois de congelar.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.eval import scores
from cityomics.models import baselines as B
from cityomics.models import chronos_zs, gnn, hawkes, inla_models, lgbm, local, maxent

LGBM_PARAMS = {"num_leaves": 63, "min_data_in_leaf": 200, "learning_rate": 0.05}


def _split(table: pl.DataFrame, a: str, b: str, c: str, d: str):
    return (table.filter((pl.col("mes") >= a) & (pl.col("mes") <= b)).sort("mes", "cd_setor"),
            table.filter((pl.col("mes") >= c) & (pl.col("mes") <= d)).sort("mes", "cd_setor"))


def cov_cols(columns: list[str]) -> list[str]:
    core = lgbm.feature_sets(columns)["nucleo"]
    return [c for c in core if not c.startswith(("h_", "nb_h_", "nr_w")) and c not in ("mes_num", "area_km2")]


STRUCT_EXCL = ("sp156_", "n_transacoes", "preco", "frac_fin", "cnpj_entr", "dias_", "chuva", "temp", "tem_dec",
               "n_sex", "n_sab", "censo_d_", "censo_g_")


def run(nome: str, table: pl.DataFrame, fit_ini: str, fit_fim: str, pred_ini: str, pred_fim: str, ctx: dict | None = None):
    ctx = ctx or {}
    fit, pred = _split(table, fit_ini, fit_fim, pred_ini, pred_fim)
    yfit = fit["y"].to_numpy()
    cols = table.columns
    if nome == "glm":
        m = B.fit_glm(fit)
        mf, mp = B.predict_glm(m, fit), B.predict_glm(m, pred)
    elif nome == "media_historica":
        xf, xp = fit["h_int_s12"].to_numpy() / 12, pred["h_int_s12"].to_numpy() / 12
        a, b, _ = B.calibrate(np.nan_to_num(xf), yfit)
        mf, mp = a * np.nan_to_num(xf) + b, a * np.nan_to_num(xp) + b
    elif nome == "hawkes":
        m = hawkes.Hawkes(cov_cols(cols)).fit(fit)
        mf, mp = m.predict(fit), m.predict(pred)
    elif nome in ("lgbm_completo", "lgbm_nucleo", "lgbm_sem_crime"):
        fs = lgbm.feature_sets(cols)[{"lgbm_completo": "completo", "lgbm_nucleo": "nucleo", "lgbm_sem_crime": "sem_crime"}[nome]]
        m = lgbm.fit(fit, fs, LGBM_PARAMS, rounds=350 if nome != "lgbm_sem_crime" else 800)
        mf, mp = lgbm.predict(m, fit, fs), lgbm.predict(m, pred, fs)
    elif nome == "gnn":
        fs = [c for c in lgbm.feature_sets(cols)["nucleo"] if c != "mes_num"] + ["mes_num"]
        m = gnn.GNN(fs, ctx["knn_idx"]).fit(fit, log=lambda *_: None)
        mf, mp = m.predict(fit), m.predict(pred)
    elif nome in ("bym2", "spde", "maxent"):
        cv = [c for c in cov_cols(cols) if not c.startswith(STRUCT_EXCL)]
        d, e = inla_models.prepare(fit, cv, ctx["setores"])
        if nome == "maxent":
            surf = maxent.fit_surface(d, cv)
        else:
            surf = inla_models.run_inla(d, e, f"{fit_ini}_{fit_fim}", modo=nome, log=lambda *_: None)
        mf = inla_models.predict(table, fit, fit, surf, nome)
        mp = inla_models.predict(table, pred, fit, surf, nome)
    elif nome == "gwr_distrito":
        m = local.GWRDistrict(cov_cols(cols)).fit(fit)
        mf, mp = m.predict(fit), m.predict(pred)
    elif nome == "painel_espacial":
        m = local.PainelEspacial(cov_cols(cols)).fit(fit)
        mf, mp = m.predict(fit), m.predict(pred)
    elif nome == "kde":
        d, idx = ctx["kde_kernel"]
        xf = B.point_forecasts(fit, d, idx, 300, 300)["stkde"]
        xp = B.point_forecasts(pred, d, idx, 300, 300)["stkde"]
        a, b, _ = B.calibrate(xf, yfit)
        mf, mp = a * xf + b, a * xp + b
    elif nome == "chronos":
        xs = ctx["chronos_x"]            # DataFrame (cd_setor, mes, x) com previsões zero-shot para todos os meses
        xf = fit.select("cd_setor", "mes").join(xs, on=["cd_setor", "mes"], how="left")["x"].to_numpy()
        xp = pred.select("cd_setor", "mes").join(xs, on=["cd_setor", "mes"], how="left")["x"].to_numpy()
        a, b, _ = B.calibrate(np.nan_to_num(xf), yfit)
        mf, mp = a * np.nan_to_num(xf) + b, a * np.nan_to_num(xp) + b
    else:
        raise KeyError(nome)
    phi = scores.fit_phi(yfit, mf)
    return mf, mp, phi
