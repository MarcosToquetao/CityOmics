"""Fig. 2 — Tipos de lote e arquitetura do tecido (narrativa B, spec-figuras §3; D63, D64).

a: UMAP de 150 mil lotes, colorido por tipo;
b: dotplot marcador × tipo;
c: composição dos spots (pizzas por setor) num recorte do centro, como na deconvolução;
d: enriquecimento de vizinhança tipo × tipo (nulo restrito a distrito × densidade);
e: domínios do tecido (composição suavizada dos setores);
f: estabilidade da tipagem (ARI por resolução) e concordância com o k-means.
A composição por distrito (antiga 2d) e as covariáveis por domínio (antiga 3c) vão para o ED6 e o ED3.
"""

from __future__ import annotations

import json

import matplotlib.patches as mpatches
import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import figdata as F
from cityomics.viz import palette as P
from cityomics.viz import names as N
from cityomics.viz import style as S


def types_meta():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list()
    fam = perfil["familia"].to_list()
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list()
    en = N.class_labels(perfil)[1]  # nomes curtos, os mesmos do texto e das Figs. 1 e 3–6
    return perfil, tipos, fam, key, en


def panel_umap(ax, cols_by_cluster):
    u = pl.read_parquet(atlas_dir() / "tipos_umap_2025.parquet")
    rng = np.random.default_rng(0)
    idx = rng.permutation(u.height)
    c = [cols_by_cluster.get(k, "#BBBBBB") for k in u["cluster"].to_numpy()[idx]]
    ax.scatter(u["umap1"].to_numpy()[idx], u["umap2"].to_numpy()[idx], s=0.15, c=c, linewidths=0, rasterized=True)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ("left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_aspect("equal", adjustable="datalim")
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    L = 0.12 * (x1 - x0)
    ax.annotate("", xy=(x0 + L, y0), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.5, color=S.INK, mutation_scale=4))
    ax.annotate("", xy=(x0, y0 + L), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=0.5, color=S.INK, mutation_scale=4))
    ax.text(x0 + L / 2, y0 - 0.03 * (y1 - y0), "UMAP 1", ha="center", va="top", fontsize=5)
    ax.text(x0 - 0.03 * (x1 - x0), y0 + L / 2, "UMAP 2", ha="right", va="center", fontsize=5, rotation=90)


def panel_dotplot(ax, dp: pl.DataFrame, order: list[str], en: dict, cols: dict, genes: list[str]):
    dp = dp.filter(pl.col("gene").is_in(genes) & pl.col("tipo").is_in(order))
    gi = {g: i for i, g in enumerate(genes)}
    ti = {t: i for i, t in enumerate(order)}
    cm = P.cmap("vik")
    z = np.clip(dp["z"].to_numpy(), -2, 2)
    sc = ax.scatter([gi[g] for g in dp["gene"]], [ti[t] for t in dp["tipo"]], s=0.5 + 18 * dp["frac"].to_numpy(),
                    c=z, cmap=cm, vmin=-2, vmax=2, linewidths=0.2, edgecolors="#555555")
    ax.set_xticks(range(len(genes)))
    ax.set_xticklabels([N.ATTR_EN.get(g, g) for g in genes], rotation=55, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([en.get(t, t) for t in order])
    for tl, t in zip(ax.get_yticklabels(), order):
        tl.set_color(S.INK)
    for i, t in enumerate(order):
        ax.add_patch(mpatches.Rectangle((-1.05, i - 0.38), 0.45, 0.76, color=cols[t], clip_on=False))
    ax.set_xlim(-0.6, len(genes) - 0.4)
    ax.set_ylim(len(order) - 0.5, -0.5)
    ax.tick_params(axis="both", length=0)
    ax.tick_params(axis="y", pad=11)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(True, color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    return sc


def panel_pies(ax, cols_dark: dict, tipos_all: list[str]):
    import geopandas as gpd

    from figures_fig1_helpers import roi_center_se

    cx, cy = roi_center_se()
    half = 1000.0
    bbox = (cx - half, cy - half, cx + half, cy + half)
    from cityomics.viz.maps import layer

    s = layer("setores").cx[bbox[0]:bbox[2], bbox[1]:bbox[3]][["cd_setor", "geometry"]].copy()
    comp = pl.read_parquet(atlas_dir() / "setor_composicao_2025.parquet")
    ecols = [c for c in comp.columns if c.startswith("e|") and c[2:] in tipos_all]
    s["cd_setor"] = s["cd_setor"].astype(str)
    cm = comp.filter(pl.col("cd_setor").is_in(s["cd_setor"].tolist())).select("cd_setor", *ecols)
    S.dark(ax)
    s.boundary.plot(ax=ax, color="#3A3A44", linewidth=0.25)
    cen = s.set_index("cd_setor").geometry.representative_point()
    area = s.set_index("cd_setor").geometry.area
    for row in cm.iter_rows(named=True):
        v = np.array([row[c] for c in ecols], dtype=float)
        if v.sum() <= 0 or row["cd_setor"] not in cen.index:
            continue
        p = cen[row["cd_setor"]]
        if not (bbox[0] < p.x < bbox[2] and bbox[1] < p.y < bbox[3]):
            continue
        frac = v / v.sum()
        r = float(np.clip(0.42 * np.sqrt(area[row["cd_setor"]] / np.pi), 18, 60))
        ang = 90.0
        for c, f in zip(ecols, frac):
            if f <= 0:
                continue
            ax.add_patch(mpatches.Wedge((p.x, p.y), r, ang, ang + 360 * f, facecolor=cols_dark[c[2:]], edgecolor="none"))
            ang += 360 * f
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    ax.set_aspect("equal")
    ax.set_xlabel("")
    ax.set_ylabel("")
    from cityomics.viz.maps import scalebar

    scalebar(ax, 500, color="white", loc=(0.06, 0.05))


def panel_districts(ax, cols: dict, order: list[str]):
    d = pl.read_parquet(atlas_dir() / "distrito_composicao_2025.parquet")
    ncols = [f"n|{t}" for t in order if f"n|{t}" in d.columns]
    M = d.select(ncols).to_numpy().astype(float)
    M = M / np.clip(M.sum(1, keepdims=True), 1, None)
    from scipy.cluster.hierarchy import leaves_list, linkage

    o = leaves_list(linkage(np.sqrt(M), "average"))
    M = M[o]
    bottom = np.zeros(len(M))
    for j, c in enumerate(ncols):
        ax.bar(np.arange(len(M)), M[:, j], bottom=bottom, width=1.0, color=cols[c[2:]], linewidth=0)
        bottom += M[:, j]
    ax.set_xlim(-0.5, len(M) - 0.5)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_ylabel("Share of parcels")
    ax.set_xlabel("Districts (n = 96), clustered by composition")
    ax.spines["bottom"].set_visible(False)


def panel_stability(ax):
    rep = json.loads((atlas_dir() / "tipagem_2025.json").read_text())
    st = rep["estabilidade"]
    rs = sorted(float(r) for r in st)
    ari = [st[str(r) if str(r) in st else repr(r)]["ari_medio"] for r in rs]
    k = [st[str(r) if str(r) in st else repr(r)]["n_tipos_mediano"] for r in rs]
    ax.plot(k, ari, color="#264653", marker="o", ms=2.2, lw=0.9)
    chosen = float(rep["resolucao"])
    kc = st[str(chosen) if str(chosen) in st else repr(chosen)]["n_tipos_mediano"]
    ac = st[str(chosen) if str(chosen) in st else repr(chosen)]["ari_medio"]
    ax.scatter([kc], [ac], s=22, facecolor="none", edgecolor="#E8743B", linewidth=0.9, zorder=3)
    ax.axhline(rep["ari_kmeans_vs_leiden"], color="#8C8C8C", lw=0.6, ls=(0, (2, 2)))
    ax.text(max(k), rep["ari_kmeans_vs_leiden"] + 0.015, "k-means vs Leiden", fontsize=5, color="#8C8C8C", ha="right")
    ax.set_xlabel("Number of parcel types")
    ax.set_ylabel("Agreement between subsamples (ARI)")
    ax.set_ylim(0, 1)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    import sys

    sys.modules.setdefault("figures_fig1_helpers", _helpers())
    perfil, tipos, fam, key, en = types_meta()
    cols = P.type_colors(tipos, fam, key)
    cols_dark = P.type_colors(tipos + ["Favela (FCU)"], fam + ["favela"], key + [0.0], dark=True)
    order = P.ordered_types(tipos, fam, key)
    cols_by_cluster = dict(zip(perfil["cluster"].to_list(), [cols[t] for t in tipos]))
    dp = F.dotplot()
    mk = pl.read_parquet(atlas_dir() / "tipos_marcadores_2025.parquet")
    top = (mk.filter(pl.col("logfc") > 0).sort("score", descending=True).group_by("cluster").head(3)["gene"].unique().to_list())
    pref = list(N.ATTR_EN)
    genes = [g for g in pref if g in top] + [g for g in top if g not in pref]
    # três fileiras: (a, b) tipos; (c, e + legenda dos domínios) tecido; (f, d) estabilidade e vizinhança
    fig = S.figure(S.DOUBLE, 240)
    a = ax_mm(fig, 6, 6, 44, 44)
    panel_umap(a, cols_by_cluster)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 100, 6, 81, 60)
    sc = panel_dotplot(b, dp, order, en, cols, genes)
    S.fig_label(fig, "b", 55, 3)
    cb = ax_mm(fig, 8, 62, 26, 2.2)
    cbar = fig.colorbar(sc, cax=cb, orientation="horizontal")
    cbar.set_label("Mean standardized value (b)", fontsize=5.2)
    cbar.ax.tick_params(labelsize=5, length=1.5)
    lg = ax_mm(fig, 8, 76, 40, 6)
    lg.axis("off")
    for i, f in enumerate((0.1, 0.5, 1.0)):
        lg.scatter([0.05 + i * 0.3], [0.4], s=0.5 + 18 * f, color="#BBBBBB", edgecolor="#555555", linewidth=0.2, transform=lg.transAxes, clip_on=False)
        lg.text(0.05 + i * 0.3 + 0.07, 0.4, f"{int(f * 100)}%", fontsize=5, va="center", transform=lg.transAxes)
    lg.text(0.0, 1.05, "Parcels with the attribute (b)", fontsize=5.2, transform=lg.transAxes)
    y2 = 100
    c = ax_mm(fig, 6, y2, 52, 52)
    panel_pies(c, cols_dark, tipos + ["Favela (FCU)"])
    S.fig_label(fig, "c", 1, y2 - 3)
    import painel_arquitetura as PA

    tipos_a, fam_a, key_a, en_a, _ = PA.meta()
    order_a = P.ordered_types(tipos_a, fam_a, key_a)
    ne = pl.read_parquet(atlas_dir() / "nhood_enrichment_2025.parquet")
    d = ax_mm(fig, 104, y2, 44, 44)
    im = PA.panel_nhood(d, ne, order_a, en_a)
    S.fig_label(fig, "d", 64, y2 - 3)
    cbd = ax_mm(fig, 152, y2 + 4, 2.0, 24)
    c1 = fig.colorbar(im, cax=cbd)
    c1.set_label("Enrichment (z)", fontsize=5.0)
    c1.ax.tick_params(labelsize=5, length=1.5)
    y3 = 176
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet")
    e = ax_mm(fig, 6, y3, 40, 56)
    PA.panel_domains(e, dom)
    S.fig_label(fig, "e", 1, y3 - 3)
    dl = N.domain_labels(short=True)
    lgd = ax_mm(fig, 50, y3 + 6, 76, 40)
    lgd.axis("off")
    lgd.text(0.0, 1.0, "Tissue domains (e), named by their most enriched cell classes", fontsize=5.2,
             transform=lgd.transAxes, va="bottom")
    step = 0.92 / max(len(dl), 1)
    for i, k in enumerate(sorted(dl)):
        y = 0.90 - i * step
        lgd.add_patch(mpatches.Rectangle((0.0, y - 0.035), 0.03, 0.07, color=PA.DOM_COLORS[k % len(PA.DOM_COLORS)],
                                         transform=lgd.transAxes, clip_on=False))
        lgd.text(0.045, y, dl[k], fontsize=5.0, va="center", transform=lgd.transAxes)
    f_ = ax_mm(fig, 144, y3 + 4, 36, 30)
    panel_stability(f_)
    S.fig_label(fig, "f", 130, y3 - 3)
    return S.save(fig, "fig2", periodo)


def _helpers():
    import types

    mod = types.ModuleType("figures_fig1_helpers")

    def roi_center_se():
        import geopandas as gpd

        d = gpd.read_parquet(processed_dir() / "units" / "distritos.parquet", columns=["nm_dist", "geometry"])
        se = d[d["nm_dist"].str.upper().str.contains("^SE$|^SÉ$", regex=True)].geometry.centroid.iloc[0]
        return se.x, se.y

    mod.roi_center_se = roi_center_se
    return mod
