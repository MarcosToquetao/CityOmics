"""OpenStreetMap: malha viária e pontos de interesse por setor (spec-dados §3.2).

- Malha viária (OSMnx, ``network_type="drive"``) do município: densidade de interseções e de
  vias, fração de becos sem saída, grau médio e centralidade de intermediação aproximada
  (amostra de origens), agregadas aos setores pelos nós contidos em cada um. A centralidade
  mede o quanto um lugar está "no caminho" de outros (crime pattern theory).
- Pontos de interesse (fotografia atual): contagens e densidades por categoria e distância ao
  bar mais próximo. O histórico (ohsome) fica para uma etapa seguinte.

Dados © colaboradores do OpenStreetMap (ODbL). Download pela Overpass via OSMnx, com cache.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd

from cityomics import external
from cityomics.paths import processed_dir
from cityomics.units.setores import CRS, load_setores

BETWEENNESS_K = 1000
OVERPASS = ("https://overpass-api.de/api", "https://overpass.kumi.systems/api",
            "https://maps.mail.ru/osm/tools/overpass/api")
SEED = 20261014

POI_TAGS = {
    "amenity": ["bar", "pub", "nightclub", "biergarten", "restaurant", "fast_food", "cafe", "bank", "atm",
                "pharmacy", "fuel", "school", "university", "college", "kindergarten", "place_of_worship",
                "hospital", "clinic", "police", "marketplace", "cinema", "theatre", "bus_station"],
    "shop": True,
    "tourism": ["hotel", "motel", "hostel"],
    "leisure": ["park", "pitch", "sports_centre", "stadium"],
}
CATEGORIAS = {
    "bar_noturno": ("amenity", {"bar", "pub", "nightclub", "biergarten"}),
    "alimentacao": ("amenity", {"restaurant", "fast_food", "cafe"}),
    "banco_atm": ("amenity", {"bank", "atm"}),
    "farmacia": ("amenity", {"pharmacy"}),
    "posto": ("amenity", {"fuel"}),
    "educacao": ("amenity", {"school", "university", "college", "kindergarten"}),
    "religioso": ("amenity", {"place_of_worship"}),
    "saude": ("amenity", {"hospital", "clinic"}),
    "lazer_cultura": ("amenity", {"cinema", "theatre", "marketplace"}),
    "comercio": ("shop", None),
    "hospedagem": ("tourism", {"hotel", "motel", "hostel"}),
    "esporte_parque": ("leisure", {"park", "pitch", "sports_centre", "stadium"}),
}


def osm_dir():
    d = external.external_dir() / "osm"
    d.mkdir(parents=True, exist_ok=True)
    _configure_osmnx(d)
    return d


def _configure_osmnx(d) -> None:
    """Mantém o cache de respostas da Overpass dentro de data/ (fora do git)."""
    import osmnx as ox

    ox.settings.cache_folder = str(d / "cache")


def _record(name: str, note: str) -> None:
    from cityomics.ingest.snapshot import sha256

    path = osm_dir() / name
    manifest = external.load_manifest()
    manifest[f"osm/{name}"] = {"url": f"OpenStreetMap via Overpass/OSMnx ({note})", "size": path.stat().st_size,
                               "sha256": sha256(path),
                               "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    external.manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def municipio_polygon():
    return load_setores().to_crs("EPSG:4326").union_all()


def load_graph(log=print):
    import osmnx as ox

    path = osm_dir() / "sp_drive.graphml"
    if not path.exists():
        log("OSM: baixando malha viária (drive) do município")
        g = ox.graph_from_polygon(municipio_polygon(), network_type="drive", simplify=True)
        ox.save_graphml(g, path)
        _record(path.name, "network_type=drive, simplify=True")
    return ox.load_graphml(path)


GEOFABRIK_SUDESTE = "https://download.geofabrik.de/south-america/brazil/sudeste-latest.osm.pbf"
BBOX_SP = (-46.83, -24.01, -46.36, -23.35)  # lon_min, lat_min, lon_max, lat_max


def _pois_from_pbf(log=print) -> gpd.GeoDataFrame:
    """Pontos de interesse a partir do extrato da Geofabrik (DuckDB ``ST_ReadOSM``).
    Nós com as tags de interesse e vias (polígonos de prédios, parques) representadas pelo
    centroide de seus nós. Usado quando a Overpass recusa consultas do tamanho da cidade."""
    import duckdb

    pbf = external.fetch(GEOFABRIK_SUDESTE, "osm", log=log)
    keys = list(POI_TAGS)
    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    x0, y0, x1, y1 = BBOX_SP
    tag_filter = " OR ".join(f"map_contains(tags, '{k}')" for k in keys)
    cols = ", ".join(f"tags['{k}'] AS {k}" for k in keys + ["name"])
    log("OSM: lendo o extrato .pbf (nós e vias com tags de interesse)")
    df = con.execute(f"""
        WITH osm AS (SELECT * FROM ST_ReadOSM('{pbf}')),
        nos AS (SELECT id, lat, lon FROM osm WHERE kind = 'node'
                AND lon BETWEEN {x0} AND {x1} AND lat BETWEEN {y0} AND {y1}),
        poi_nos AS (SELECT 'node' AS tipo, id, lon, lat, {cols} FROM osm
                    WHERE kind = 'node' AND lon BETWEEN {x0} AND {x1} AND lat BETWEEN {y0} AND {y1}
                    AND ({tag_filter})),
        vias AS (SELECT id, unnest(refs) AS ref, {cols} FROM osm WHERE kind = 'way' AND ({tag_filter})),
        poi_vias AS (SELECT 'way' AS tipo, v.id, avg(n.lon) AS lon, avg(n.lat) AS lat,
                            {", ".join(f"any_value(v.{k}) AS {k}" for k in keys + ["name"])}
                     FROM vias v JOIN nos n ON n.id = v.ref GROUP BY v.id)
        SELECT * FROM poi_nos UNION ALL SELECT * FROM poi_vias
    """).df()
    con.close()
    g = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["lon"], df["lat"]), crs="EPSG:4326")
    g = g[g.within(municipio_polygon())]
    for k, values in POI_TAGS.items():  # aplica o mesmo filtro de valores da consulta Overpass
        if values is not True:
            g.loc[~g[k].isin(values), k] = None
    return g[g[keys].notna().any(axis=1)].drop(columns=["lon", "lat"])


def load_pois(log=print) -> gpd.GeoDataFrame:
    import osmnx as ox

    path = osm_dir() / "sp_pois.gpkg"
    if not path.exists():
        log("OSM: baixando pontos de interesse")
        pois = None
        for url in OVERPASS:
            ox.settings.overpass_url = url
            try:
                pois = ox.features_from_polygon(municipio_polygon(), tags=POI_TAGS)
                keep = [c for c in ("amenity", "shop", "tourism", "leisure", "name") if c in pois.columns]
                pois = pois[keep + ["geometry"]].reset_index()
                note = "tags=" + ",".join(POI_TAGS) + f" via {url}"
                break
            except Exception as err:  # noqa: BLE001 — servidores públicos recusam por limite de uso
                log(f"Overpass {url} falhou ({type(err).__name__}); tentando o próximo")
        if pois is None:
            pois = _pois_from_pbf(log=log)
            note = "Geofabrik sudeste-latest.osm.pbf via DuckDB ST_ReadOSM"
        pois.to_file(path, driver="GPKG")
        _record(path.name, note)
    return gpd.read_file(path)


def street_metrics(setores: gpd.GeoDataFrame, log=print) -> pd.DataFrame:
    import osmnx as ox

    g = load_graph(log=log)
    gp = ox.project_graph(g, to_crs=CRS)
    nodes, edges = ox.graph_to_gdfs(gp)
    log(f"malha: {len(nodes):,} nós, {len(edges):,} arestas")

    und = nx.Graph(ox.convert.to_undirected(gp))
    log(f"centralidade de intermediação (k={BETWEENNESS_K} origens)")
    bc = nx.betweenness_centrality(und, k=min(BETWEENNESS_K, und.number_of_nodes()), weight="length",
                                   normalized=True, seed=SEED)
    nodes["betweenness"] = nodes.index.map(bc).astype(float)

    nj = gpd.sjoin(nodes[["street_count", "betweenness", "geometry"]], setores[["cd_setor", "geometry"]],
                   how="inner", predicate="within")
    agg = nj.groupby("cd_setor").agg(
        n_nos=("street_count", "size"),
        n_intersecoes=("street_count", lambda s: int((s >= 3).sum())),
        frac_becos=("street_count", lambda s: float((s == 1).mean())),
        grau_medio=("street_count", "mean"),
        betweenness_media=("betweenness", "mean"),
        betweenness_max=("betweenness", "max"),
    )
    # comprimento de vias dentro de cada setor (arestas recortadas pelo setor)
    edges_u = edges[["length", "geometry"]].reset_index(drop=True)
    pieces = gpd.overlay(edges_u, setores[["cd_setor", "geometry"]], how="intersection", keep_geom_type=True)
    km = pieces.assign(km=pieces.length / 1000).groupby("cd_setor")["km"].sum()

    out = setores[["cd_setor", "area_km2"]].set_index("cd_setor").join(agg).join(km.rename("km_vias"))
    out[["n_nos", "n_intersecoes", "km_vias"]] = out[["n_nos", "n_intersecoes", "km_vias"]].fillna(0)
    area = out["area_km2"].replace(0, np.nan)
    out["dens_intersecoes_km2"] = out["n_intersecoes"] / area
    out["dens_vias_km_km2"] = out["km_vias"] / area
    return out.drop(columns="area_km2").reset_index()


def poi_metrics(setores: gpd.GeoDataFrame, log=print) -> pd.DataFrame:
    pois = load_pois(log=log).to_crs(CRS)
    pois = pois.set_geometry(pois.geometry.representative_point())
    log(f"pontos de interesse: {len(pois):,}")
    for cat, (col, values) in CATEGORIAS.items():
        if col not in pois.columns:
            pois[cat] = False
            continue
        pois[cat] = pois[col].notna() if values is None else pois[col].isin(values)
    joined = gpd.sjoin(pois, setores[["cd_setor", "geometry"]], how="inner", predicate="within")
    counts = joined.groupby("cd_setor")[list(CATEGORIAS)].sum()
    out = setores[["cd_setor", "area_km2"]].set_index("cd_setor").join(counts).fillna(0)
    area = out["area_km2"].replace(0, np.nan)
    for cat in CATEGORIAS:
        out[f"n_poi_{cat}"] = out.pop(cat).astype(int)
        out[f"dens_poi_{cat}_km2"] = out[f"n_poi_{cat}"] / area
    bars = pois[pois["bar_noturno"]]
    pts = gpd.GeoDataFrame(setores[["cd_setor"]], geometry=setores.representative_point(), crs=setores.crs)
    near = gpd.sjoin_nearest(pts, bars[["geometry"]], how="left", distance_col="d")
    near = near[~near.index.duplicated(keep="first")]
    out["dist_bar_noturno_m"] = near.set_index("cd_setor")["d"].round(1)
    return out.drop(columns="area_km2").reset_index()


def build(log=print) -> pd.DataFrame:
    setores = load_setores()[["cd_setor", "area_km2", "geometry"]]
    out = street_metrics(setores, log=log).merge(poi_metrics(setores, log=log), on="cd_setor", how="outer")
    dest = processed_dir() / "covariaveis" / "setor_osm.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    return out
