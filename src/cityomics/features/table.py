"""Tabela de modelagem do celular: setor × mês com alvo, histórico as-of e covariáveis (F5).

Cada linha é um setor em um mês-alvo ``m``. As colunas são:

- ``y`` (contagem reconciliada ``n_total``, real), ``y_geo`` (só geocodificados), ``cd_dist``, ``area_km2``;
- histórico de crime as-of (``features.history``) e sua média nos 8 vizinhos mais próximos
  (``nb_*``, vizinhança por centroides: determinística e sem polígonos);
- covariáveis do painel as-of (``covariates.asof``), numéricas em float32;
- ``mes_num`` (1–12) para sazonalidade.

Para 2026, o alvo vem do cofre (F7) e as features são montadas com o mesmo código a partir dos
eventos registrados antes de cada mês; aqui só se monta 2022–2025.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy.spatial import cKDTree

from cityomics.features import history
from cityomics.paths import interim_dir, processed_dir

K_VIZ = 8
VIZ_COLS = ("h_int_l1", "h_int_s3", "h_int_s12")


def vizinhos(centroides: np.ndarray, k: int = K_VIZ) -> np.ndarray:
    """Índices dos ``k`` vizinhos mais próximos (sem o próprio setor)."""
    _, idx = cKDTree(centroides).query(centroides, k=k + 1)
    return idx[:, 1:]


def spatial_lag(valores: np.ndarray, idx: np.ndarray) -> np.ndarray:
    return np.nanmean(valores[idx], axis=1)


def build(meses: list[str], log=print) -> pl.DataFrame:
    import geopandas as gpd

    from cityomics.units.setores import load_setores

    s = load_setores()
    s = s.assign(cx=s.geometry.centroid.x, cy=s.geometry.centroid.y)
    s = s.sort_values("cd_setor").reset_index(drop=True)
    setores = s["cd_setor"].astype(str).tolist()
    dist = dict(zip(setores, s["cd_dist"].astype(str)))
    idx = vizinhos(s[["cx", "cy"]].to_numpy())

    ev = pl.read_parquet(interim_dir() / "eventos_celular_atribuidos.parquet",
                         columns=["cd_setor", "cd_dist", "data_fato", "data_registro", "via"])
    # histórico precisa de meses anteriores: calcula para os meses pedidos usando todos os eventos disponíveis
    h = history.build(ev, setores, dist, meses)
    log(f"histórico: {h.height:,} linhas, {h.width} colunas")

    # defasagem espacial por mês
    nb = []
    pos = {m: i for i, m in enumerate(meses)}
    for m in meses:
        d = h.filter(pl.col("mes") == m).sort("cd_setor")
        cols = {"cd_setor": d["cd_setor"], "mes": d["mes"]}
        for c in VIZ_COLS:
            cols[f"nb_{c}"] = spatial_lag(d[c].to_numpy().astype("float64"), idx).astype("float32")
        nb.append(pl.DataFrame(cols))
    h = h.join(pl.concat(nb), on=["cd_setor", "mes"])

    alvo = pl.read_parquet(processed_dir() / "alvos" / "celular_setor_mes.parquet").rename(
        {"periodo": "mes", "n_total": "y", "n_geo": "y_geo"}).select("cd_setor", "mes", "y", "y_geo")
    base = pl.DataFrame({"cd_setor": setores, "cd_dist": s["cd_dist"].astype(str).tolist(), "area_km2": s["area_km2"].to_numpy()})
    t = h.join(alvo, on=["cd_setor", "mes"], how="left").join(base, on="cd_setor")

    panel = pl.scan_parquet(processed_dir() / "covariaveis" / "painel_setor_mes.parquet")
    num = [c for c, d in panel.collect_schema().items() if d.is_numeric() or d == pl.Boolean]
    p = panel.filter(pl.col("mes").is_in(meses)).select(["cd_setor", "mes"] + num).collect()
    p = p.with_columns([pl.col(c).cast(pl.Float32) for c in num])
    t = t.join(p, on=["cd_setor", "mes"], how="left").with_columns(
        pl.col("mes").str.slice(5, 2).cast(pl.Int8).alias("mes_num"))
    return t.sort("mes", "cd_setor")


def write(meses: list[str], nome: str, log=print) -> pl.DataFrame:
    t = build(meses, log=log)
    dest = processed_dir() / "modelo"
    dest.mkdir(parents=True, exist_ok=True)
    t.write_parquet(dest / nome)
    log(f"{nome}: {t.height:,} linhas × {t.width} colunas")
    return t
