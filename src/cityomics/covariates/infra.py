"""Infraestrutura e equipamentos por setor (GeoSampa, WFS) — covariáveis estáticas.

Para cada setor 2022, a partir do ponto representativo do setor:
- distância à feição mais próxima (estações de metrô e trem, terminais e corredores de ônibus,
  delegacias e bases da PM e da GCM, favelas, cortiços, parques, praças, UBS, feiras);
- contagem e densidade por km² de pontos de ônibus e de pontos de iluminação pública.

Todas as camadas são fotografias atuais (2026): não têm histórico. A iluminação pública já
está 100% em LED (carga de 2026-07-14), então só a densidade varia entre setores.
Equipamentos de segurança são endógenos ao crime (instalados onde há crime); entram como
contexto e são marcados para análise de sensibilidade.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from cityomics import external
from cityomics.paths import processed_dir
from cityomics.units.setores import load_setores

DISTANCIAS = {
    "estacao_metro": "geoportal:estacao_metro",
    "estacao_trem": "geoportal:estacao_trem",
    "terminal_onibus": "geoportal:terminal_onibus",
    "corredor_onibus": "geoportal:corredor_onibus",
    "delegacia": "geoportal:equipamento_policia_civil",
    "base_pm": "geoportal:equipamento_policia_militar",
    "base_gcm": "geoportal:equipamento_guarda_civil_metropolitana",
    "favela": "geoportal:habita2geosampa_habi_favela2geosampa",
    "cortico": "geoportal:habita2geosampa_habi_cortico2geosampa",
    "parque": "geoportal:pde_parque_municipal",
    "praca": "geoportal:GEOSAMPA_v_praca_largo",
    "ubs": "geoportal:equipamento_saude_ubs_posto_centro",
    "feira": "geoportal:equipamento_feira_livre",
}
CONTAGENS = {
    "ponto_onibus": "geoportal:ponto_onibus",
    "iluminacao": "geoportal:iluminacao_publica",
}
ENDOGENAS = ("delegacia", "base_pm", "base_gcm")


def _layer(layer: str, log=print) -> gpd.GeoDataFrame:
    g = gpd.read_file(external.fetch_geosampa(layer, log=log))
    return g.set_crs("EPSG:31983", allow_override=True)[["geometry"]]


def build(log=print) -> pd.DataFrame:
    setores = load_setores()[["cd_setor", "area_km2", "geometry"]]
    pts = gpd.GeoDataFrame(setores[["cd_setor"]], geometry=setores.representative_point(), crs=setores.crs)
    out = setores[["cd_setor", "area_km2"]].copy()

    for name, layer in DISTANCIAS.items():
        feats = _layer(layer, log=log)
        near = gpd.sjoin_nearest(pts, feats, how="left", distance_col="d")
        near = near[~near.index.duplicated(keep="first")]
        out[f"dist_{name}_m"] = near["d"].round(1).to_numpy()
        log(f"distância a {name}: mediana {np.nanmedian(out[f'dist_{name}_m']):,.0f} m")
    out["dist_estacao_trilhos_m"] = out[["dist_estacao_metro_m", "dist_estacao_trem_m"]].min(axis=1)

    for name, layer in CONTAGENS.items():
        feats = gpd.GeoDataFrame(geometry=_layer(layer, log=log).geometry.representative_point(), crs="EPSG:31983")
        hits = gpd.sjoin(feats, setores[["cd_setor", "geometry"]], how="inner", predicate="within")
        counts = hits.groupby("cd_setor").size()
        out[f"n_{name}"] = out["cd_setor"].map(counts).fillna(0).astype(int)
        out[f"dens_{name}_km2"] = out[f"n_{name}"] / out["area_km2"].replace(0, np.nan)
        log(f"{name}: {int(counts.sum()):,} feições em setores")

    out = out.drop(columns="area_km2")
    dest = processed_dir() / "covariaveis" / "setor_infra.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    return out
