"""Explorador Vitessce do CityOmics (spec-explorer.md; D48, D49, D60).

Duas versões, ambas fora do git:
- ``explorer/local/``: lotes + setores com o risco previsto e a incerteza por setor (uso interno);
- ``explorer/public/``: montada por **lista branca**; risco só por distrito; sem MEI por lote, sem
  nomes de favela ou bairro, sem crime por lote nem por setor (D49, D60). ``check_public`` falha se
  algo fora da lista aparecer.

Os lotes são pontos (o Vitessce ainda não lê polígonos do AnnData). Os lotes fora da subamostra do
UMAP herdam a média das coordenadas dos 5 vizinhos mais próximos no espaço dos genes padronizados.
"""

from __future__ import annotations

import json
import shutil

import numpy as np
import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import REPO_ROOT, processed_dir

OUT = REPO_ROOT / "explorer"
PUBLIC_OBS = {"tipo", "familia", "dominio", "distrito"}
PUBLIC_SETOR_OBS = {"dominio", "distrito"}
FORBIDDEN_PUBLIC = ("risco", "crime", "mu_", "pred", "n_total", "y_", "mei", "nm_fcu", "bairro", "incerteza")


def lots_anndata(public: bool):
    import anndata as ad
    from cityomics.atlas import typing as T
    from cityomics.viz.figdata import GENE_EN

    g = pl.read_parquet(atlas_dir() / "lote_genes_2025.parquet")
    Z, names, mask, raw = T.prepare(g)
    gi = g.filter(pl.col("tem_iptu")).select("sql_base", "cd_setor", "cd_dist")
    tipos = pl.read_parquet(atlas_dir() / "lote_tipos_2025.parquet").select("sql_base", "tipo", "familia")
    pts = pl.read_parquet(atlas_dir() / "lote_pontos.parquet").select("sql_base", "x", "y")
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet").select("cd_setor", "dominio_nome")
    obs = (gi.with_row_index("i").join(tipos, on="sql_base", how="left").join(pts, on="sql_base", how="left")
           .join(dom, on="cd_setor", how="left").sort("i"))
    # o explorador usa a subamostra aleatória do UMAP (150 mil lotes, coordenadas exatas): 1,6 milhão de pontos
    # mais um heatmap de 1,6 milhão de colunas travam o navegador; o mapa completo está na Fig. 1
    um = pl.read_parquet(atlas_dir() / "tipos_umap_2025.parquet").select("sql_base", "umap1", "umap2")
    sel = pl.DataFrame({"sql_base": gi["sql_base"]}).with_row_index("i").join(um, on="sql_base", how="inner").sort("i")
    rows = sel["i"].to_numpy()
    Z = Z[rows]
    obs = obs.join(sel.select("i"), on="i", how="inner").sort("i")
    U = sel.select("umap1", "umap2").to_numpy().astype(np.float32)
    keep = [i for i, n in enumerate(names) if not (public and n == "cnpj_mei")]
    X = Z[:, keep].astype(np.float32)
    var = [GENE_EN.get(names[i], names[i]) for i in keep]
    xy = obs.select("x", "y").to_numpy().astype(np.float32)
    xy = np.nan_to_num(xy - np.nanmin(xy, axis=0)) / 1000.0  # km a partir do canto da cidade
    import pandas as pd

    o = pd.DataFrame({"tipo": obs["tipo"].fill_null("Sem cadastro").to_numpy(), "familia": obs["familia"].fill_null("sem_cadastro").to_numpy(),
                      "dominio": obs["dominio_nome"].fill_null("—").to_numpy(), "distrito": obs["cd_dist"].cast(pl.String).fill_null("—").to_numpy()},
                     index=obs["sql_base"].to_numpy())
    for c in o.columns:
        o[c] = o[c].astype("category")
    a = ad.AnnData(X=X, obs=o, var=pd.DataFrame(index=var))
    a.obsm["spatial"] = xy
    a.obsm["X_umap"] = U
    return a


def setores_anndata(public: bool):
    import anndata as ad
    import geopandas as gpd
    import pandas as pd

    comp = pl.read_parquet(atlas_dir() / "setor_composicao_2025.parquet")
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet").select("cd_setor", "dominio_nome")
    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    cen = g.geometry.representative_point()
    xy = pl.DataFrame({"cd_setor": g["cd_setor"].astype(str).to_numpy(), "x": cen.x.to_numpy(), "y": cen.y.to_numpy()})
    s = comp.select("cd_setor", "cd_dist", *[c for c in comp.columns if c.startswith("e|")]).join(dom, on="cd_setor", how="left").join(xy, on="cd_setor", how="left")
    ecols = [c for c in s.columns if c.startswith("e|")]
    E = s.select(ecols).to_numpy().astype(np.float32)
    E = E / np.clip(E.sum(1, keepdims=True), 1e-9, None)
    var = [f"share: {c[2:]}" for c in ecols]
    o = pd.DataFrame({"dominio": s["dominio_nome"].fill_null("—").to_numpy(), "distrito": s["cd_dist"].cast(pl.String).to_numpy()},
                     index=s["cd_setor"].to_numpy())
    if not public:
        from cityomics.viz.figdata import load_eval
        from cityomics.eval import scores

        ev, mu, phi, _ = load_eval("dev")
        an = ev.with_columns(pl.Series("mu", mu["ensemble"]), pl.Series("p1", scores.prob_ge1(mu["ensemble"], phi["ensemble"]))).group_by("cd_setor").agg(
            pl.col("mu").sum().alias("risco_previsto_2025"), pl.col("y").sum().alias("crime_observado_2025"), pl.col("p1").mean().alias("p_ge1_medio"))
        r = pl.DataFrame({"cd_setor": s["cd_setor"]}).join(an, on="cd_setor", how="left").fill_null(0)
        extra = r.select("risco_previsto_2025", "crime_observado_2025", "p_ge1_medio").to_numpy().astype(np.float32)
        E = np.hstack([E, np.log1p(extra[:, :2]), extra[:, 2:]])
        var += ["log risk 2025 (local)", "log observed 2025 (local)", "mean P(≥1) (local)"]
    for c in o.columns:
        o[c] = o[c].astype("category")
    a = ad.AnnData(X=E, obs=o, var=pd.DataFrame(index=var))
    a.obsm["spatial"] = (np.nan_to_num(s.select("x", "y").to_numpy() - np.nanmin(s.select("x", "y").to_numpy(), axis=0)) / 1000.0).astype(np.float32)
    return a


def config(lot_path: str, setor_path: str, base_url: str, public: bool, tipos: list[str] | None = None):
    from vitessce import AnnDataWrapper, VitessceConfig
    from vitessce import ViewType as vt

    vc = VitessceConfig(schema_version="1.0.16", name="CityOmics — São Paulo as a tissue" + ("" if public else " (local)"))
    lots = vc.add_dataset(name="Parcels (cells)").add_object(AnnDataWrapper(
        adata_url=f"{base_url}/{lot_path}", obs_feature_matrix_path="X", obs_set_paths=["obs/tipo", "obs/familia", "obs/dominio"],
        obs_set_names=["Parcel type", "Family", "Tissue domain"], obs_embedding_paths=["obsm/spatial", "obsm/X_umap"],
        obs_embedding_names=["Map", "UMAP"]))
    spots = vc.add_dataset(name="Census tracts (spots)").add_object(AnnDataWrapper(
        adata_url=f"{base_url}/{setor_path}", obs_feature_matrix_path="X", obs_set_paths=["obs/dominio"], obs_set_names=["Tissue domain"],
        obs_embedding_paths=["obsm/spatial"], obs_embedding_names=["Map"]))
    # o mapa é uma "imersão" com as coordenadas (km): a visão de dispersão colore milhões de pontos por tipo
    mp = vc.add_view(vt.SCATTERPLOT, dataset=lots, mapping="Map")
    um = vc.add_view(vt.SCATTERPLOT, dataset=lots, mapping="UMAP")
    sets = vc.add_view(vt.OBS_SETS, dataset=lots)
    hm = vc.add_view(vt.HEATMAP, dataset=lots)
    genes = vc.add_view(vt.FEATURE_LIST, dataset=lots)
    sp2 = vc.add_view(vt.SCATTERPLOT, dataset=spots, mapping="Map")
    desc = vc.add_view(vt.DESCRIPTION, dataset=lots)
    desc.set_props(description=("Each point is a fiscal parcel (a 'cell'), coloured by its type. Census tracts are the 'spots' (lower right). "
                                "Click a type to highlight it across the map, the UMAP and the heatmap; pick an attribute ('gene') to colour by it. "
                                + ("Predicted risk is shown only by district in this public version." if public else
                                   "Local version: tract-level predicted risk and observed counts are tract features (do not share).")))
    sel0 = [["Parcel type", x] for x in (tipos or [])] or None
    colors = None
    if tipos:
        from cityomics.viz.palette import type_colors

        perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
        fam = dict(zip(perfil["nome"].to_list(), perfil["familia"].to_list())) | {"Sem cadastro": "sem_cadastro", "Favela (FCU)": "favela"}
        hexes = type_colors(tipos, [fam.get(x, "sem_cadastro") for x in tipos], [0.0] * len(tipos), dark=True)
        colors = [{"path": ["Parcel type", x], "color": [int(hexes[x][i:i + 2], 16) for i in (1, 3, 5)]} for x in tipos]
    vc.link_views([mp, um, sets, hm, genes], ["obsSetSelection", "obsColorEncoding", "featureSelection", "obsSetColor"],
                  [sel0, "cellSetSelection", None, colors])
    vc.layout((mp | (um / sp2)) / (sets | genes | hm | desc))
    return vc


def build(public: bool, port: int = 8790, reuse: bool = False, log=print) -> dict:
    """``reuse=True`` mantém os zarr já gravados e só refaz a configuração e a página."""
    import anndata as ad

    ad.settings.zarr_write_format = 2  # o Vitessce 3.9 lê zarr v2 (.zarray/.zgroup)
    d = OUT / ("public" if public else "local")
    if reuse and (d / "data" / "lotes.zarr").exists() and (d / "data" / "setores.zarr").exists():
        lots, spots = ad.read_zarr(d / "data" / "lotes.zarr"), ad.read_zarr(d / "data" / "setores.zarr")
    else:
        if d.exists():
            shutil.rmtree(d)
        (d / "data").mkdir(parents=True)
        import numcodecs

        comp = numcodecs.Blosc(cname="lz4", clevel=5, shuffle=numcodecs.Blosc.SHUFFLE)  # o zstd do anndata não abre no Vitessce
        lots = lots_anndata(public)
        ad.io.write_zarr(d / "data" / "lotes.zarr", lots, compressor=comp)
        spots = setores_anndata(public)
        ad.io.write_zarr(d / "data" / "setores.zarr", spots, compressor=comp)
    vc = config("data/lotes.zarr", "data/setores.zarr", f"http://localhost:{port}", public,
                tipos=sorted(lots.obs["tipo"].astype(str).unique().tolist()))
    cfg = vc.to_dict(base_url=f"http://localhost:{port}")
    (d / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1))
    (d / "index.html").write_text(INDEX_HTML.replace("__TITLE__", cfg.get("name", "CityOmics")))
    if public:
        check_public(d)
    log(f"explorador {'público' if public else 'local'}: {lots.n_obs:,} lotes, {spots.n_obs:,} setores → {d}")
    return {"dir": str(d), "lotes": int(lots.n_obs), "setores": int(spots.n_obs)}


def check_public(d) -> None:
    """Falha se o objeto público tiver colunas ou genes fora da lista branca (D49, D60)."""
    import anndata as ad

    lots = ad.read_zarr(d / "data" / "lotes.zarr")
    spots = ad.read_zarr(d / "data" / "setores.zarr")
    bad = [c for c in list(lots.obs.columns) if c not in PUBLIC_OBS] + [c for c in list(spots.obs.columns) if c not in PUBLIC_SETOR_OBS]
    names = [str(v).lower() for v in list(lots.var_names) + list(spots.var_names)]
    bad += [n for n in names if any(f in n for f in FORBIDDEN_PUBLIC)]
    if bad:
        raise RuntimeError(f"objeto público fora da lista branca: {bad}")


INDEX_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>html,body,#root{margin:0;height:100%;background:#0b0b0e;color:#ddd;font-family:Arial,Helvetica,sans-serif}</style>
<script type="importmap">{"imports": {
  "react": "https://esm.sh/react@18.2.0",
  "react-dom": "https://esm.sh/react-dom@18.2.0",
  "react-dom/client": "https://esm.sh/react-dom@18.2.0/client",
  "react/jsx-runtime": "https://esm.sh/react@18.2.0/jsx-runtime"}}</script>
</head><body><div id="root">Loading the CityOmics explorer…</div>
<script type="module">
import React from "react";
import { createRoot } from "react-dom/client";
import { Vitessce } from "https://cdn.jsdelivr.net/npm/vitessce@3.9.7/dist/index.min.js";
const config = await (await fetch("config.json")).json();
createRoot(document.getElementById("root")).render(
  React.createElement(Vitessce, { config, height: window.innerHeight, theme: "dark" }));
</script></body></html>
"""
