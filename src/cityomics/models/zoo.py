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


class Ajustado:
    """Modelo ajustado, serializável, que prevê qualquer mês com features as-of (F4: congelamento).

    ``predict(df, table, ctx)``: ``df`` ordenado por (mes, cd_setor); ``table`` é a tabela as-of que contém
    os meses de ``df`` (os modelos INLA tiram dela o nível do histórico); ``ctx`` como em ``benchmark_run``.
    """

    def __init__(self, nome: str, obj=None, a: float = 1.0, b: float = 0.0, extra: dict | None = None):
        self.nome, self.obj, self.a, self.b, self.extra = nome, obj, a, b, extra or {}
        self.phi = None

    def predict(self, df: pl.DataFrame, table: pl.DataFrame | None = None, ctx: dict | None = None) -> np.ndarray:
        ctx, n = ctx or {}, self.nome
        if n == "glm":
            return B.predict_glm(self.obj, df)
        if n == "media_historica":
            return self.a * np.nan_to_num(df["h_int_s12"].to_numpy() / 12) + self.b
        if n in ("hawkes", "gnn", "gwr_distrito", "painel_espacial"):
            return self.obj.predict(df)
        if n in ("lgbm_completo", "lgbm_nucleo", "lgbm_sem_crime"):
            return lgbm.predict(self.obj, df, self.extra["feats"])
        if n in ("bym2", "spde", "maxent"):
            return _predict_superficie(self.extra, df, table)
        if n == "kde":
            d, idx = ctx["kde_kernel"]
            return self.a * B.point_forecasts(df, d, idx, 300, 300)["stkde"] + self.b
        if n == "chronos":
            x = df.select("cd_setor", "mes").join(ctx["chronos_x"], on=["cd_setor", "mes"], how="left")["x"].to_numpy()
            return self.a * np.nan_to_num(x) + self.b
        raise KeyError(n)


def _superficie(table: pl.DataFrame, fit: pl.DataFrame, surf, col: str) -> dict:
    """O que ``inla_models.predict`` usa do período de ajuste, resumido: λ por setor, nível de referência e
    sazonalidade (``inla_models.temporal_factors``), para prever meses novos sem guardar a tabela de ajuste."""
    lam = pl.from_pandas(surf[["cd_setor", col]].rename(columns={col: "lam"}))
    nivel = table.group_by("mes").agg((pl.col("h_int_s12").sum() / 12).alias("nivel"), pl.col("mes_num").first())
    ref = float(nivel.filter(pl.col("mes").is_in(fit["mes"].unique().to_list()))["nivel"].mean())
    obs = fit.group_by("mes").agg(pl.col("y").sum().alias("obs"))
    comp = nivel.with_columns((pl.col("nivel") / ref).alias("f_nivel")).join(obs, on="mes").with_columns(
        (pl.col("obs") / (lam["lam"].sum() * pl.col("f_nivel"))).alias("r"))
    sazonal = comp.group_by("mes_num").agg(pl.col("r").mean().alias("sazonal"))
    return {"lam": lam, "ref": ref, "sazonal": sazonal}


def _predict_superficie(s: dict, df: pl.DataFrame, table: pl.DataFrame) -> np.ndarray:
    nivel = table.group_by("mes").agg((pl.col("h_int_s12").sum() / 12).alias("nivel"), pl.col("mes_num").first())
    fac = (nivel.join(s["sazonal"], on="mes_num", how="left").with_columns(pl.col("sazonal").fill_null(1.0))
           .with_columns((pl.col("nivel") / s["ref"] * pl.col("sazonal")).alias("fator")).select("mes", "fator"))
    j = df.select("cd_setor", "mes").join(s["lam"], on="cd_setor", how="left").join(fac, on="mes", how="left")
    return (j["lam"] * j["fator"]).fill_null(0).to_numpy()


def fit(nome: str, table: pl.DataFrame, fit_ini: str, fit_fim: str, ctx: dict | None = None) -> Ajustado:
    """Ajusta ``nome`` nos meses ``[fit_ini, fit_fim]``; ``phi`` (NB2) é ajustado nesses meses, como em ``run``."""
    ctx = ctx or {}
    fit_df = table.filter((pl.col("mes") >= fit_ini) & (pl.col("mes") <= fit_fim)).sort("mes", "cd_setor")
    yfit = fit_df["y"].to_numpy()
    cols = table.columns
    if nome == "glm":
        m = Ajustado(nome, B.fit_glm(fit_df))
    elif nome == "media_historica":
        a, b, _ = B.calibrate(np.nan_to_num(fit_df["h_int_s12"].to_numpy() / 12), yfit)
        m = Ajustado(nome, a=a, b=b)
    elif nome == "hawkes":
        m = Ajustado(nome, hawkes.Hawkes(cov_cols(cols)).fit(fit_df))
    elif nome in ("lgbm_completo", "lgbm_nucleo", "lgbm_sem_crime"):
        fs = lgbm.feature_sets(cols)[{"lgbm_completo": "completo", "lgbm_nucleo": "nucleo", "lgbm_sem_crime": "sem_crime"}[nome]]
        m = Ajustado(nome, lgbm.fit(fit_df, fs, LGBM_PARAMS, rounds=350 if nome != "lgbm_sem_crime" else 800), extra={"feats": fs})
    elif nome == "gnn":
        fs = [c for c in lgbm.feature_sets(cols)["nucleo"] if c != "mes_num"] + ["mes_num"]
        m = Ajustado(nome, gnn.GNN(fs, ctx["knn_idx"]).fit(fit_df, log=lambda *_: None))
    elif nome in ("bym2", "spde", "maxent"):
        cv = [c for c in cov_cols(cols) if not c.startswith(STRUCT_EXCL)]
        d, e = inla_models.prepare(fit_df, cv, ctx["setores"])
        if nome == "maxent":
            surf = maxent.fit_surface(d, cv)
        else:
            surf = inla_models.run_inla(d, e, f"{fit_ini}_{fit_fim}", modo=nome, log=lambda *_: None)
        m = Ajustado(nome, extra=_superficie(table, fit_df, surf, nome))
    elif nome == "gwr_distrito":
        m = Ajustado(nome, local.GWRDistrict(cov_cols(cols)).fit(fit_df))
    elif nome == "painel_espacial":
        m = Ajustado(nome, local.PainelEspacial(cov_cols(cols)).fit(fit_df))
    elif nome == "kde":
        d, idx = ctx["kde_kernel"]
        a, b, _ = B.calibrate(B.point_forecasts(fit_df, d, idx, 300, 300)["stkde"], yfit)
        m = Ajustado(nome, a=a, b=b)
    elif nome == "chronos":
        xf = fit_df.select("cd_setor", "mes").join(ctx["chronos_x"], on=["cd_setor", "mes"], how="left")["x"].to_numpy()
        a, b, _ = B.calibrate(np.nan_to_num(xf), yfit)
        m = Ajustado(nome, a=a, b=b)
    else:
        raise KeyError(nome)
    m.phi = scores.fit_phi(yfit, m.predict(fit_df, table, ctx))
    return m


def run(nome: str, table: pl.DataFrame, fit_ini: str, fit_fim: str, pred_ini: str, pred_fim: str, ctx: dict | None = None):
    m = fit(nome, table, fit_ini, fit_fim, ctx)
    fit_df, pred = _split(table, fit_ini, fit_fim, pred_ini, pred_fim)
    return m.predict(fit_df, table, ctx), m.predict(pred, table, ctx), m.phi
