"""Ruas e estações como classes de célula (D51): o "espaço intersticial e os vasos" do tecido.

Quase 80% do roubo de celular acontece na via pública e ~10% em estações e terminais, fora dos
lotes. Por isso o modelo de atribuição tem, além dos tipos de lote, três classes de rua com λ
próprio (exposição = comprimento no setor) e as estações (exposição = contagem).

- Malha viária: grafo ``drive`` do OSM já baixado (``covariates/osm.load_graph``), sem duplicar os
  dois sentidos. Classes: arterial (motorway, trunk, primary), coletora (secondary, tertiary) e
  local (o resto).
- Estações de metrô e trem (GeoSampa) e terminais de ônibus (GeoSampa).

Saídas: ``atlas/ruas.parquet`` (segmentos com classe e setor, para os mapas e a validação pontual)
e ``atlas/setor_ruas_estacoes.parquet`` (exposição por setor).
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from cityomics import external
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.units.setores import CRS

CLASSES = {
    "arterial": {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link"},
    "coletora": {"secondary", "secondary_link", "tertiary", "tertiary_link"},
}
TERMINAL_LAYER = "geoportal:terminal_onibus"


def _classe(h) -> str:
    hs = h if isinstance(h, list) else [h]
    for c, tags in CLASSES.items():
        if any(x in tags for x in hs):
            return c
    return "local"


def setor_do_ponto_medio(e: gpd.GeoDataFrame, setores: gpd.GeoDataFrame) -> np.ndarray:
    """Setor que contém o ponto médio de cada segmento, na ordem das linhas de ``e`` (qualquer índice)."""
    mid = e.geometry.interpolate(0.5, normalized=True)
    pts = gpd.GeoDataFrame({"i": np.arange(len(e))}, geometry=mid.values, crs=e.crs)
    j = gpd.sjoin(pts, setores[["cd_setor", "geometry"]], how="left", predicate="within").drop_duplicates("i")
    return j.sort_values("i")["cd_setor"].to_numpy()


def segments(setores: gpd.GeoDataFrame, log=print) -> gpd.GeoDataFrame:
    import osmnx as ox

    from cityomics.covariates.osm import load_graph

    g = load_graph(log=log)
    e = ox.graph_to_gdfs(g, nodes=False).reset_index()
    e["par"] = [tuple(sorted(x)) for x in zip(e["u"], e["v"])]
    # índice refeito depois de tirar os sentidos duplicados: o GeoDataFrame dos pontos médios alinha a
    # geometria pelo índice, e um índice com buracos trocava o setor de 99,8% dos segmentos (corrigido em
    # 2026-10-20; paper/review/parecer/C_ritmo_queda.md)
    e = e.drop_duplicates(["par", "key"]).reset_index(drop=True).to_crs(CRS)
    e["classe"] = e["highway"].map(_classe)
    e["comprimento_m"] = e.geometry.length
    e["cd_setor"] = setor_do_ponto_medio(e, setores)
    out = e[["classe", "comprimento_m", "cd_setor", "geometry"]].reset_index(drop=True)
    log(f"ruas: {len(out):,} segmentos; {out['comprimento_m'].sum() / 1e3:,.0f} km "
        f"({out.groupby('classe')['comprimento_m'].sum().div(1e3).round(0).to_dict()})")
    return out


def stations() -> gpd.GeoDataFrame:
    from cityomics.units.transit import load_stations

    st = load_stations()[["geometry"]].to_crs(CRS).assign(tipo="trilho")
    term = gpd.read_file(external.fetch_geosampa(TERMINAL_LAYER)).to_crs(CRS)
    term = gpd.GeoDataFrame({"tipo": ["terminal"] * len(term)}, geometry=term.geometry.representative_point().values, crs=CRS)
    return pd.concat([st, term], ignore_index=True)


def build(setores: gpd.GeoDataFrame, log=print) -> pd.DataFrame:
    seg = segments(setores, log=log)
    seg.to_parquet(atlas_dir() / "ruas.parquet")
    expo = seg.pivot_table(index="cd_setor", columns="classe", values="comprimento_m", aggfunc="sum", fill_value=0.0)
    expo.columns = [f"rua_{c}_m" for c in expo.columns]
    st = stations()
    sj = gpd.sjoin(st, setores[["cd_setor", "geometry"]], how="inner", predicate="within")
    cnt = sj.pivot_table(index="cd_setor", columns="tipo", values="index_right", aggfunc="count", fill_value=0)
    cnt.columns = [f"n_{c}" for c in cnt.columns]
    out = setores[["cd_setor"]].set_index("cd_setor").join(expo).join(cnt).fillna(0.0).reset_index()
    out.to_parquet(atlas_dir() / "setor_ruas_estacoes.parquet")
    log(f"estações: {int(cnt.sum().sum()):,} em setores ({cnt.sum().to_dict()})")
    return out
