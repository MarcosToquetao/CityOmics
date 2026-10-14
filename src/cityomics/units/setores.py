"""Setores censitários 2022 e distritos da capital (spec-dados §2).

Fonte: malha de setores com atributos do Censo 2022 (IBGE). Em São Paulo os 96 distritos
do IBGE coincidem com os distritos municipais, e cada setor já traz ``CD_DIST``, então a
hierarquia setor → distrito sai da própria malha. Tudo é reprojetado para SIRGAS 2000 /
UTM 23S (EPSG:31983), o sistema do GeoSampa.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

from cityomics import external
from cityomics.paths import processed_dir

URL_SETORES = ("https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/"
               "malha_com_atributos/setores/gpkg/UF/SP/SP_setores_CD2022.gpkg")
CD_MUN_SP = "3550308"
CRS = "EPSG:31983"

# v0001 = pessoas; v0002 = domicílios; v0007 = domicílios particulares permanentes ocupados
RENAME = {"CD_SETOR": "cd_setor", "CD_DIST": "cd_dist", "NM_DIST": "nm_dist", "SITUACAO": "situacao",
          "CD_TIPO": "cd_tipo", "AREA_KM2": "area_km2", "CD_FCU": "cd_fcu", "NM_FCU": "nm_fcu",
          "v0001": "pop_2022", "v0002": "domicilios_2022", "v0007": "dom_ocupados_2022"}


def units_dir() -> Path:
    return processed_dir() / "units"


def build_setores(log=print) -> gpd.GeoDataFrame:
    path = external.fetch(URL_SETORES, "ibge", log=log)
    gdf = gpd.read_file(path, where=f"CD_MUN = '{CD_MUN_SP}'")[list(RENAME) + ["geometry"]]
    gdf = gdf.rename(columns=RENAME).to_crs(CRS)
    gdf["favela"] = gdf["cd_fcu"].fillna(".").ne(".")
    gdf = gdf.drop(columns="cd_fcu")
    units_dir().mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(units_dir() / "setores_2022.parquet")
    return gdf


def build_distritos(setores: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    agg = {"nm_dist": "first", "area_km2": "sum", "pop_2022": "sum", "domicilios_2022": "sum"}
    dist = setores.dissolve(by="cd_dist", aggfunc=agg).reset_index()
    dist["n_setores"] = setores.groupby("cd_dist").size().reindex(dist["cd_dist"]).to_numpy()
    dist.to_parquet(units_dir() / "distritos.parquet")
    return dist


def load_setores() -> gpd.GeoDataFrame:
    return gpd.read_parquet(units_dir() / "setores_2022.parquet")


def load_distritos() -> gpd.GeoDataFrame:
    return gpd.read_parquet(units_dir() / "distritos.parquet")
