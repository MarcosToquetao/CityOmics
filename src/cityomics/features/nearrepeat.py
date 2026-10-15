"""Features de near-repeat (Knox) por setor × mês (ecologia/epidemiologia do crime; spec-benchmark §3.2).

Para o mês ``m``, conta os eventos geocodificados dentro de um raio ``r`` do centroide do setor e
dentro de uma janela de ``w`` dias antes do início de ``m``, usando só BOs já registrados antes de
``m`` (regra as-of). A contagem é dividida pela fração geocodificada dos eventos da janela, para
que a alta de cobertura de 2026 não pareça alta de risco. As janelas terminam no início de ``m``:
é o contágio de curto prazo que a contagem mensal não enxerga.

Os microdados (coordenadas) ficam só na memória; a saída é agregada por setor.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from pyproj import Transformer
from scipy.spatial import cKDTree

CONFIGS = ((30, 250), (30, 500), (90, 500), (14, 250))   # (janela em dias, raio em metros)


def build(events: pl.DataFrame, centroids: np.ndarray, setores: list[str], meses: list[str], configs=CONFIGS) -> pl.DataFrame:
    """``events``: ``latitude``, ``longitude``, ``coord_valida``, ``data_fato``, ``data_registro``, ``cd_dist``.
    ``centroids``: coordenadas (x, y) em EPSG:31983 na ordem de ``setores``."""
    ev = events.filter(pl.col("data_fato").is_not_null() & pl.col("cd_dist").is_not_null())
    ev = ev.with_columns(pl.col("data_registro").fill_null(pl.col("data_fato")))
    geo = ev.filter(pl.col("coord_valida") & pl.col("latitude").is_not_null())
    tr = Transformer.from_crs(4674, 31983, always_xy=True)
    gx, gy = tr.transform(geo["longitude"].to_numpy(), geo["latitude"].to_numpy())
    pts = np.column_stack([gx, gy])
    f_geo = geo["data_fato"].to_numpy().astype("datetime64[D]")
    r_geo = geo["data_registro"].to_numpy().astype("datetime64[D]")
    f_all = ev["data_fato"].to_numpy().astype("datetime64[D]")
    r_all = ev["data_registro"].to_numpy().astype("datetime64[D]")
    frames = []
    for m in meses:
        t0 = np.datetime64(f"{m}-01", "D")
        cols = {"cd_setor": setores, "mes": [m] * len(setores)}
        for w, r in configs:
            lo = t0 - np.timedelta64(w, "D")
            sel = (f_geo >= lo) & (f_geo < t0) & (r_geo < t0)
            tot = ((f_all >= lo) & (f_all < t0) & (r_all < t0)).sum()
            share = max(sel.sum() / tot, 0.05) if tot > 0 else np.nan
            if sel.sum() == 0:
                cnt = np.zeros(len(setores))
            else:
                cnt = cKDTree(pts[sel]).query_ball_point(centroids, r, return_length=True).astype("float64")
            cols[f"nr_w{w}_r{r}"] = (cnt / share).astype("float32") if np.isfinite(share) else np.full(len(setores), np.nan, "float32")
        frames.append(pl.DataFrame(cols))
    return pl.concat(frames)
