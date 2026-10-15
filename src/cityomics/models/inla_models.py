"""BYM2 e SPDE/LGCP por R-INLA, convertidos em previsões mensais (spec-benchmark §3.2).

O R-INLA ajusta a superfície de risco **espacial** do período de ajuste (contagem por setor, com as
covariáveis núcleo médias do período e a vizinhança de contiguidade). A previsão mensal multiplica
essa superfície por um fator temporal as-of: o nível da cidade na janela de 12 meses disponível em
``m`` (soma de ``h_int_s12`` / 12, relativo à média do período de ajuste) e um índice sazonal por
mês do ano estimado no ajuste. Todo o gradiente temporal é da cidade; a estrutura espacial é do INLA.

Limitação declarada: não é um Knorr-Held completo (interação espaço-tempo tipo I-IV), inviável com
27 mil setores × 24 meses no INLA; é o BYM2/SPDE espacial com modulação temporal global.
"""

from __future__ import annotations

import subprocess

import numpy as np
import pandas as pd
import polars as pl

from cityomics.paths import REPO_ROOT, processed_dir


def edges(setores_gdf) -> np.ndarray:
    """Pares (i, j) de setores contíguos (i < j), índices 1-based para o R."""
    import geopandas as gpd

    g = setores_gdf[["geometry"]].reset_index(drop=True)
    j = gpd.sjoin(g, g, predicate="intersects", how="inner")
    j = j[j.index < j["index_right"]]
    return np.column_stack([j.index.to_numpy() + 1, j["index_right"].to_numpy() + 1])


def prepare(fit: pl.DataFrame, cov_cols: list[str], setores_gdf) -> tuple[pd.DataFrame, np.ndarray]:
    meses = fit["mes"].n_unique()
    agg = fit.group_by("cd_setor").agg([pl.col("y").sum().round(0).alias("y")] +
                                       [pl.col(c).mean().alias(c) for c in cov_cols]).sort("cd_setor").to_pandas()
    s = setores_gdf.sort_values("cd_setor").reset_index(drop=True)
    d = agg.copy()
    for c in cov_cols:
        v = d[c].fillna(d[c].median()).to_numpy()
        v = np.sign(v) * np.log1p(np.abs(v))
        d[c] = (v - v.mean()) / (v.std() + 1e-9)
    d["meses"] = meses
    d["area_km2"] = s["area_km2"].to_numpy()
    d["cx"], d["cy"] = s.geometry.centroid.x.to_numpy(), s.geometry.centroid.y.to_numpy()
    return d, edges(s)


def run_inla(d: pd.DataFrame, e: np.ndarray, tag: str, modo: str = "ambos", log=print) -> pd.DataFrame:
    work = processed_dir() / "modelo" / "inla"
    work.mkdir(parents=True, exist_ok=True)
    d.to_csv(work / f"{tag}_in.csv", index=False)
    pd.DataFrame(e, columns=["i", "j"]).to_csv(work / f"{tag}_edges.csv", index=False)
    r = subprocess.run(["conda", "run", "-n", "cityomics-r", "--no-capture-output", "Rscript", str(REPO_ROOT / "R" / "bym2_spde.R"),
                        str(work / f"{tag}_in.csv"), str(work / f"{tag}_edges.csv"), str(work / f"{tag}_out.csv"), modo],
                       capture_output=True, text=True)
    log(r.stdout[-2500:])
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    return pd.read_csv(work / f"{tag}_out.csv", dtype={"cd_setor": str})


def temporal_factors(table: pl.DataFrame, fit: pl.DataFrame, lam: pl.DataFrame) -> pl.DataFrame:
    """Fator ``f(m) = nível as-of(m) / nível de referência × sazonal(mês do ano)`` por mês.

    ``lam``: ``cd_setor, lam`` (média mensal do período de ajuste). Sazonal = razão média entre o total
    observado e o total previsto pelo nível, por mês do ano, dentro do período de ajuste."""
    nivel = table.group_by("mes").agg((pl.col("h_int_s12").sum() / 12).alias("nivel"), pl.col("mes_num").first())
    ref = nivel.filter(pl.col("mes").is_in(fit["mes"].unique().to_list()))["nivel"].mean()
    nivel = nivel.with_columns((pl.col("nivel") / ref).alias("f_nivel"))
    obs = fit.group_by("mes").agg(pl.col("y").sum().alias("obs"))
    tot_lam = lam["lam"].sum()
    comp = nivel.join(obs, on="mes").with_columns((pl.col("obs") / (tot_lam * pl.col("f_nivel"))).alias("r"))
    sazonal = comp.group_by("mes_num").agg(pl.col("r").mean().alias("sazonal"))
    out = nivel.join(sazonal, on="mes_num", how="left").with_columns(pl.col("sazonal").fill_null(1.0))
    return out.with_columns((pl.col("f_nivel") * pl.col("sazonal")).alias("fator")).select("mes", "fator")


def predict(table: pl.DataFrame, ev: pl.DataFrame, fit: pl.DataFrame, surface: pd.DataFrame, col: str) -> np.ndarray:
    lam = pl.from_pandas(surface[["cd_setor", col]].rename(columns={col: "lam"}))
    fac = temporal_factors(table, fit, lam)
    j = ev.select("cd_setor", "mes").join(lam, on="cd_setor", how="left").join(fac, on="mes", how="left")
    return (j["lam"] * j["fator"]).fill_null(0).to_numpy()
