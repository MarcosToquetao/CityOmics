"""Atribuição dos eventos às unidades (spec-dados §2).

- Com coordenada válida: ponto → setor 2022 (point-in-polygon) e, pelo setor, distrito.
- Sem coordenada: distrito pelo bairro (distrito mais frequente entre os registros
  geocodificados daquele bairro) e, se o bairro for ambíguo ou desconhecido, pela delegacia
  da circunscrição. O setor fica vazio e é tratado pela reconciliação.

As tabelas de consulta bairro → distrito e delegacia → distrito são construídas só com
registros fora do cofre (2022–2025), de todas as naturezas.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd

from cityomics.ingest.schema import norm_text
from cityomics.paths import interim_dir, raw_dir
from cityomics.units.setores import CRS, load_setores

MIN_N = 5          # registros geocodificados mínimos para confiar no bairro
MIN_SHARE = 0.6    # fração mínima do distrito modal

# Estratos de tipo de local (D27), por palavra-chave no subtipo normalizado. A ordem importa.
STRATA = [
    ("residencia", ("CASA", "APARTAMENTO", "RESIDENCIA", "GARAGEM", "CONDOMINIO", "HOTEL", "PENSAO",
                    "HOSPEDA", "ALBERGUE", "MOTEL", "CORTICO", "FAVELA")),
    ("trilhos", ("METROV", "FERROV", "TERMINAL", "ESTACAO", "TREM", "METRO")),
    ("onibus", ("ONIBUS", "TRANSPORTE COLETIVO", "RODOVIARIO", "LOTACAO", "TROLEBUS")),
    ("via_publica", ("VIA PUBLICA", "TRANSEUNTE", "PRACA", "VEICULO", "VIELA", "CALCADA", "VIADUTO")),
    ("comercio", ("LOJA", "BAR", "MERCADO", "RESTAURANTE", "FARMACIA", "DROGARIA", "POSTO", "SHOPPING",
                  "COMERCI", "LANCHONETE", "PADARIA", "ESTACIONAMENTO", "BANCO", "SUPERMERCADO", "SHOW")),
]


def stratum(subtipolocal: pd.Series) -> pd.Series:
    text = subtipolocal.map(norm_text)
    out = pd.Series("outros", index=text.index, dtype="object")
    assigned = pd.Series(False, index=text.index)
    for name, keys in STRATA:
        hit = text.str.contains("|".join(keys), regex=True) & ~assigned
        out[hit] = name
        assigned |= hit
    return out


def points_to_setores(df: pd.DataFrame, setores: gpd.GeoDataFrame) -> pd.DataFrame:
    """Devolve ``cd_setor`` e ``cd_dist`` para as linhas com coordenada válida."""
    pts = df[df["coord_valida"]]
    gpts = gpd.GeoDataFrame(index=pts.index, geometry=gpd.points_from_xy(pts["longitude"], pts["latitude"]),
                            crs="EPSG:4674").to_crs(CRS)
    joined = gpd.sjoin(gpts, setores[["cd_setor", "cd_dist", "geometry"]], how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    return joined[["cd_setor", "cd_dist"]]


def _modal_lookup(keys: pd.Series, dist: pd.Series) -> pd.DataFrame:
    t = pd.DataFrame({"k": keys, "d": dist}).dropna()
    counts = t.groupby(["k", "d"]).size().rename("n").reset_index()
    tot = counts.groupby("k")["n"].transform("sum")
    counts["share"] = counts["n"] / tot
    counts["total"] = tot
    best = counts.sort_values(["k", "n"], ascending=[True, False]).drop_duplicates("k")
    return best[(best["total"] >= MIN_N) & (best["share"] >= MIN_SHARE)].set_index("k")[["d", "share", "total"]]


def build_lookups(years=(2022, 2023, 2024, 2025), log=print) -> dict[str, pd.DataFrame]:
    setores = load_setores()
    frames = []
    for year in years:
        for fonte in ("ssp", "celular"):
            path = raw_dir() / "bo" / f"{fonte}_{year}.parquet"
            if path.exists():
                frames.append(pd.read_parquet(path, columns=["bairro", "dp_fato", "latitude", "longitude",
                                                             "coord_valida"]))
    df = pd.concat(frames, ignore_index=True)
    geo = points_to_setores(df, setores)
    df["cd_dist"] = geo["cd_dist"]
    lookups = {"bairro": _modal_lookup(df["bairro"].map(norm_text), df["cd_dist"]),
               "dp": _modal_lookup(df["dp_fato"].map(norm_text), df["cd_dist"])}
    for name, lk in lookups.items():
        lk.reset_index().to_parquet(interim_dir() / f"lookup_{name}_distrito.parquet", index=False)
        log(f"lookup {name} → distrito: {len(lk):,} chaves confiáveis")
    return lookups


def load_lookups() -> dict[str, pd.DataFrame]:
    return {n: pd.read_parquet(interim_dir() / f"lookup_{n}_distrito.parquet").set_index("k")
            for n in ("bairro", "dp")}


def assign_events(ev: pd.DataFrame, setores: gpd.GeoDataFrame, lookups: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ev = ev.copy()
    geo = points_to_setores(ev, setores)
    ev["cd_setor"] = geo["cd_setor"]
    ev["cd_dist"] = geo["cd_dist"]
    ev["via"] = np.where(ev["cd_dist"].notna(), "coord", None)

    for name, col in (("bairro", "bairro"), ("dp", "dp_fato")):
        todo = ev["cd_dist"].isna()
        mapped = ev.loc[todo, col].map(norm_text).map(lookups[name]["d"])
        ev.loc[mapped.dropna().index, "cd_dist"] = mapped.dropna()
        ev.loc[mapped.dropna().index, "via"] = name
    ev["via"] = ev["via"].fillna("nenhum")
    ev["estrato"] = stratum(ev["subtipolocal"])
    return ev
