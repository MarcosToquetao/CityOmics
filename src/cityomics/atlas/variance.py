"""Quanto do "onde" é tecido? Decomposição da variância e comparadores (Fig. 4c; D35, D53, D55).

1. ICC de 2025: participação da variância entre setores na variância total do crime setor × mês.
2. R² fora da amostra (CV por distrito) da taxa média do setor em 2025, por quatro conjuntos de
   variáveis:
   - **tipos:** composição de tipos e exposição;
   - **genes sem tipagem:** os mesmos genes do lote agregados por setor, sem passar pelos tipos.
     É o comparador de H3 pedido pelo red-team (D55): separa o ganho da tipagem do ganho da
     informação nova do IPTU/CNPJ;
   - **tipos + domínios + ruas:** a arquitetura do tecido;
   - **tecido + covariáveis do setor:** o núcleo teórico.

   Como referência, a média histórica (2022–2024) do mesmo setor.

Usa crime: só setores fora do cofre espacial (D53).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.paths import processed_dir


def icc(year: int = REF_YEAR) -> float:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet"))
    t = t.filter(pl.col("periodo").str.starts_with(str(year)))
    t = t.filter(pl.Series(guard.explore_mask(t["cd_dist"].to_numpy())))
    y = t["n_total"].to_numpy()
    m = t.group_by("cd_setor").agg(pl.col("n_total").mean().alias("m"))
    mm = t.join(m, on="cd_setor")["m"].to_numpy()
    return float(np.var(mm) / np.var(y))


def genes_por_setor() -> pl.DataFrame:
    g = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet").filter(pl.col("tem_iptu"))
    num = [c for c in g.columns if c not in ("sql_base", "origem", "setor_fiscal", "quadra_fiscal", "condominio", "cd_setor",
                                             "cd_dist", "tem_iptu") and g[c].dtype.is_numeric()]
    w = pl.col("testada").fill_null(1.0).clip(1.0)
    agg = [((pl.col(c).fill_null(0) * w).sum() / w.sum()).alias(f"gm|{c}") for c in num if not c.startswith("cnpj_")]
    agg += [pl.col(c).fill_null(0).sum().alias(f"gs|{c}") for c in num if c.startswith("cnpj_")]
    return g.group_by("cd_setor").agg(agg + [pl.len().alias("gs|n_lotes")])


def r2_cv(X: np.ndarray, y: np.ndarray, groups: np.ndarray, folds: int = 5, seed: int = 0) -> float:
    import lightgbm as lgb
    from sklearn.model_selection import GroupKFold

    oof = np.zeros(len(y))
    for tr, te in GroupKFold(folds).split(X, y, groups):
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=40,
                              subsample=0.8, subsample_freq=1, colsample_bytree=0.8, random_state=seed, verbose=-1)
        oof[te] = m.fit(X[tr], y[tr]).predict(X[te])
    return float(1 - np.sum((y - oof) ** 2) / np.sum((y - y.mean()) ** 2))


def run(log=print) -> dict:
    from cityomics.atlas.attribution import GROUPS, crime_setor, group_scores
    from cityomics.atlas.spots import ESTACOES, RUAS

    d = atlas_dir()
    s = pl.read_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    s = s.join(crime_setor(), on="cd_setor", how="left")
    hist = pl.read_parquet(processed_dir() / "alvos" / "celular_setor_mes.parquet").filter(
        pl.col("periodo") < f"{REF_YEAR}-01").group_by("cd_setor").agg((pl.col("n_total").sum() / 3).alias("hist"))
    s = (s.join(hist, on="cd_setor", how="left").join(group_scores(), on="cd_setor", how="left")
         .join(pl.read_parquet(d / f"setor_dominio_{REF_YEAR}.parquet"), on="cd_setor", how="left")
         .join(genes_por_setor(), on="cd_setor", how="left").fill_null(0))
    s = s.filter(pl.Series(guard.explore_mask(s["cd_dist"].to_numpy())))
    area = s["area_km2"].to_numpy().clip(1e-3)
    y = np.log1p(s["y"].to_numpy() / area)
    groups = s["cd_dist"].to_numpy()
    ecols = [c for c in s.columns if c.startswith("e|")]
    E = s.select(ecols).to_numpy().astype(float)
    shares = E / np.clip(E.sum(1, keepdims=True), 1e-9, None)
    tipos = np.column_stack([shares, np.log1p(E.sum(1)), np.log(area)])
    gcols = [c for c in s.columns if c.startswith(("gm|", "gs|"))]
    genes = np.column_stack([s.select(gcols).to_numpy().astype(float), np.log(area)])
    dom = np.eye(int(s["dominio"].max()) + 1)[s["dominio"].to_numpy().astype(int)]
    tecido = np.column_stack([tipos, dom, np.log1p(s.select(RUAS + ESTACOES).to_numpy().astype(float))])
    full = np.column_stack([tecido, s.select(GROUPS).to_numpy()])
    histv = np.column_stack([np.log1p(s["hist"].to_numpy() / area)])
    res = {"icc_2025": icc(), "setores": int(s.height)}
    for nome, X in (("tipos", tipos), ("genes_sem_tipagem", genes), ("tecido", tecido), ("tecido_mais_covariaveis", full),
                    ("media_historica", histv)):
        res[f"r2_{nome}"] = r2_cv(X, y, groups)
        log(f"R² fora da amostra ({nome}): {res[f'r2_{nome}']:.3f}")
    (d / "variancia_2025.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    return res
