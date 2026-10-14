"""Lotes fiscais (células do atlas) e pseudo-lotes de favela (spec-dados §2, D13).

Fontes:
- GeoSampa, camada "Lote" (Cadastro Fiscal): um GeoPackage por distrito, EPSG:31983, com
  setor fiscal, quadra, lote, condomínio e tipos de quadra e de lote;
- GeoSampa, camada de favelas (HABISP), usada como pseudo-lotes: favelas não têm lote fiscal.

Chave do lote: ``sql_base`` = setor (3) + quadra (3) + lote (4). Em condomínios, o cadastro
IPTU tem uma linha por unidade; a ligação com o lote usa o código do condomínio.
Cada lote recebe o setor censitário 2022 que contém seu centroide.
"""

from __future__ import annotations

import zipfile

import geopandas as gpd
import pandas as pd

from cityomics import external
from cityomics.units.setores import load_setores, units_dir

FAVELA_LAYER = "geoportal:habita2geosampa_habi_favela2geosampa"


def _read_gpkg_zip(path) -> gpd.GeoDataFrame:
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".gpkg"))
        target = path.parent / "_extraido" / name
        if not target.exists():
            z.extract(name, path.parent / "_extraido")
    return gpd.read_file(target)


def build_lotes(log=print) -> gpd.GeoDataFrame:
    folder = external.external_dir() / "geosampa" / "lotes"
    frames = []
    for path in sorted(folder.glob("SIRGAS_GPKG_LOTES_*.zip")):
        g = _read_gpkg_zip(path)
        g["arquivo"] = path.stem
        frames.append(g)
    lotes = gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs=frames[0].crs)
    lotes = lotes.rename(columns={"lo_setor": "setor_fiscal", "lo_quadra": "quadra_fiscal", "lo_lote": "lote",
                                  "lo_condomi": "condominio", "lo_tp_quad": "tipo_quadra", "lo_tp_lote": "tipo_lote"})
    for col, width in (("setor_fiscal", 3), ("quadra_fiscal", 3), ("lote", 4), ("condominio", 2)):
        lotes[col] = lotes[col].astype("string").str.strip().str.zfill(width)
    lotes["sql_base"] = lotes["setor_fiscal"] + lotes["quadra_fiscal"] + lotes["lote"]
    lotes["origem"] = "lote_fiscal"
    log(f"lotes fiscais: {len(lotes):,} ({lotes['sql_base'].nunique():,} chaves distintas)")

    fav = gpd.read_file(external.fetch_geosampa(FAVELA_LAYER, log=log)).to_crs(lotes.crs)
    fav = fav[["geometry"]].assign(origem="favela", sql_base=[f"FAV{i:06d}" for i in range(len(fav))])
    log(f"pseudo-lotes de favela: {len(fav):,}")

    cells = gpd.GeoDataFrame(pd.concat([lotes, fav], ignore_index=True), crs=lotes.crs)
    cells["area_m2"] = cells.area
    cent = gpd.GeoDataFrame(geometry=cells.representative_point(), crs=cells.crs)
    setores = load_setores()[["cd_setor", "cd_dist", "geometry"]]
    joined = gpd.sjoin(cent, setores, how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    cells["cd_setor"] = joined["cd_setor"]
    cells["cd_dist"] = joined["cd_dist"]
    cells.to_parquet(units_dir() / "lotes.parquet")
    log(f"células: {len(cells):,} | sem setor 2022: {cells['cd_setor'].isna().mean():.2%}")
    return cells


def load_lotes() -> gpd.GeoDataFrame:
    return gpd.read_parquet(units_dir() / "lotes.parquet")
