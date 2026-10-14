"""Estações de metrô e trem (GeoSampa) e os setores que as contêm (D27).

Os eventos do estrato "trilhos" sem coordenada são distribuídos só entre setores a até
``BUFFER_M`` metros de uma estação: a estação fica no viário, e o setor do lado oposto
da rua também recebe parte dos casos.
"""

from __future__ import annotations

import geopandas as gpd

from cityomics import external

BUFFER_M = 250
LAYERS = ("geoportal:estacao_metro", "geoportal:estacao_trem")


def load_stations(log=print) -> gpd.GeoDataFrame:
    frames = [gpd.read_file(external.fetch_geosampa(layer, log=log)) for layer in LAYERS]
    st = gpd.GeoDataFrame(gpd.pd.concat(frames, ignore_index=True), crs="EPSG:31983")
    return st[["nm_estacao_metro_trem", "nm_linha_metro_trem", "nm_empresa_metro_trem", "geometry"]]


def station_setores(setores: gpd.GeoDataFrame, stations: gpd.GeoDataFrame, buffer_m: float = BUFFER_M) -> set[str]:
    zones = stations.buffer(buffer_m)
    hits = gpd.sjoin(setores[["cd_setor", "geometry"]], gpd.GeoDataFrame(geometry=zones, crs=stations.crs),
                     how="inner", predicate="intersects")
    return set(hits["cd_setor"])
