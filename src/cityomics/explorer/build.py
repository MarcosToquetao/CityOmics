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
    um = pl.read_parquet(atlas_dir() / "tipos_umap_2025.parquet")
    pos = pl.DataFrame({"sql_base": gi["sql_base"]}).with_row_index("i").join(um.select("sql_base", "umap1", "umap2"), on="sql_base", how="inner")
    from pynndescent import NNDescent

    ref = pos["i"].to_numpy()
    um_ref = pos.select("umap1", "umap2").to_numpy()
    index = NNDescent(Z[ref], n_neighbors=15, random_state=0, n_jobs=-1)
    U = np.empty((len(Z), 2), dtype=np.float32)
    for s in range(0, len(Z), 250_000):
        nb, _ = index.query(Z[s:s + 250_000], k=5)
        U[s:s + 250_000] = um_ref[nb].mean(axis=1)
    U[pos["i"].to_numpy()] = pos.select("umap1", "umap2").to_numpy()
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


def config(lot_path: str, setor_path: str, base_url: str, public: bool):
    from vitessce import AnnDataWrapper, VitessceConfig
    from vitessce import ViewType as vt

    vc = VitessceConfig(schema_version="1.0.16", name="CityOmics — São Paulo as a tissue" + ("" if public else " (local)"))
    lots = vc.add_dataset(name="Parcels (cells)").add_object(AnnDataWrapper(
        adata_url=f"{base_url}/{lot_path}", obs_feature_matrix_path="X", obs_set_paths=["obs/tipo", "obs/familia", "obs/dominio"],
        obs_set_names=["Parcel type", "Family", "Tissue domain"], obs_embedding_paths=["obsm/X_umap"], obs_embedding_names=["UMAP"],
        obs_points_path="obsm/spatial"))
    spots = vc.add_dataset(name="Census tracts (spots)").add_object(AnnDataWrapper(
        adata_url=f"{base_url}/{setor_path}", obs_feature_matrix_path="X", obs_set_paths=["obs/dominio"], obs_set_names=["Tissue domain"],
        obs_spots_path="obsm/spatial"))
    sp = vc.add_view(vt.SPATIAL, dataset=lots)
    um = vc.add_view(vt.SCATTERPLOT, dataset=lots, mapping="UMAP")
    sets = vc.add_view(vt.OBS_SETS, dataset=lots)
    hm = vc.add_view(vt.HEATMAP, dataset=lots)
    genes = vc.add_view(vt.FEATURE_LIST, dataset=lots)
    sp2 = vc.add_view(vt.SPATIAL, dataset=spots)
    desc = vc.add_view(vt.DESCRIPTION)
    desc.set_props(description=("Each point is a fiscal parcel (a 'cell'), coloured by its type. Census tracts are the 'spots'. "
                                "Click a type to highlight it across the map, the UMAP and the heatmap. "
                                + ("Predicted risk is shown only by district in this public version." if public else
                                   "Local version: tract-level risk and observed counts (do not share).")))
    vc.link_views([sp, um, sets, hm, genes], ["obsSetSelection", "obsColorEncoding"], [None, "cellSetSelection"])
    vc.layout((sp | (um / sp2)) / (sets | genes | hm | desc))
    return vc


def build(public: bool, port: int = 8790, log=print) -> dict:
    d = OUT / ("public" if public else "local")
    if d.exists():
        shutil.rmtree(d)
    (d / "data").mkdir(parents=True)
    lots = lots_anndata(public)
    lots.write_zarr(d / "data" / "lotes.zarr")
    spots = setores_anndata(public)
    spots.write_zarr(d / "data" / "setores.zarr")
    vc = config("data/lotes.zarr", "data/setores.zarr", f"http://localhost:{port}", public)
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
<link rel="stylesheet" href="https://unpkg.com/vitessce@3.9.7/dist/esm/index.css" onerror="this.remove()">
<style>html,body,#root{margin:0;height:100%;background:#0b0b0e;color:#ddd;font-family:Arial,Helvetica,sans-serif}</style>
</head><body><div id="root">Loading…</div>
<script type="module">
import React from "https://esm.sh/react@18.2.0";
import { createRoot } from "https://esm.sh/react-dom@18.2.0/client";
import { Vitessce } from "https://esm.sh/vitessce@3.9.7?deps=react@18.2.0,react-dom@18.2.0";
const config = await (await fetch("config.json")).json();
createRoot(document.getElementById("root")).render(
  React.createElement(Vitessce, { config, height: window.innerHeight, theme: "dark" }));
</script></body></html>
"""
