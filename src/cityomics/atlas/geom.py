"""Geometria auxiliar do atlas: centróides dos lotes (cache local) e leitura das camadas."""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir


def lot_points(refresh: bool = False) -> pl.DataFrame:
    """sql_base, origem, x, y (ponto representativo, EPSG:31983), área e chaves de quadra/setor."""
    path = atlas_dir() / "lote_pontos.parquet"
    if path.exists() and not refresh:
        return pl.read_parquet(path)
    import geopandas as gpd

    g = gpd.read_parquet(processed_dir() / "units" / "lotes.parquet",
                         columns=["sql_base", "origem", "setor_fiscal", "quadra_fiscal", "cd_setor", "cd_dist", "area_m2", "geometry"])
    rp = g.geometry.representative_point()
    out = pl.DataFrame({
        "sql_base": g["sql_base"].astype(str).to_numpy(), "origem": g["origem"].astype(str).to_numpy(),
        "setor_fiscal": g["setor_fiscal"].astype(str).to_numpy(), "quadra_fiscal": g["quadra_fiscal"].astype(str).to_numpy(),
        "cd_setor": g["cd_setor"].astype(str).to_numpy(), "cd_dist": g["cd_dist"].astype(str).to_numpy(),
        "area_m2": g["area_m2"].to_numpy().astype(float),
        "x": rp.x.to_numpy().astype(np.float64), "y": rp.y.to_numpy().astype(np.float64),
    })
    out = out.unique("sql_base", keep="first", maintain_order=True)  # uma célula por chave (polígonos repetidos)
    out.write_parquet(path)
    return out
