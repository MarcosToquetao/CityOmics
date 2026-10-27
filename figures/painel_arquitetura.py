"""Painéis da arquitetura do tecido (antiga Fig. 3; narrativa B: nichos e domínios na Fig. 2, comunicação no ED3).

Fig. 3 — Arquitetura do tecido: nichos e comunicação (spec-figuras §3; D39, D40, D59).

a: enriquecimento de vizinhança tipo × tipo (nulo restrito a distrito × densidade);
b: mapa dos domínios (composição suavizada dos setores);
c: covariáveis marcadoras por domínio (d de Cohen);
d: círculo emissor → receptor (força L–R agregada, ℓ = 500 m, pares com p < 0,05);
e: bolhas dos pares L–R por par de tipos;
f: campo vetorial do sinal do par com maior atividade (estilo COMMOT).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ax_mm, check_periodo, row_swatches
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import maps as M
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S
from cityomics.viz.chord import circle
from cityomics.viz.fields import signal_field, stream, to_grid

DOM_COLORS = ["#E8743B", "#5B9BD5", "#2A9D8F", "#B99BF0", "#E3B23C", "#8C7B6B", "#D1495B", "#6A994E", "#264653",
              "#F4A261", "#9C89B8", "#7FB3EE"]
COV_EN = N.COV_EN  # nomes centralizados em viz/names.py
LR_EN = N.LR_EN


def meta():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)"]
    fam = perfil["familia"].to_list() + ["favela"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0]
    en = N.class_labels(perfil)[1]
    n = dict(zip(perfil["nome"].to_list(), perfil["n_lotes"].to_list()))
    return tipos, fam, key, en, n


def panel_nhood(ax, ne: pl.DataFrame, order: list[str], en: dict):
    order = [t for t in order if t in set(ne["a"].to_list())]
    K = len(order)
    Z = np.zeros((K, K))
    idx = {t: i for i, t in enumerate(order)}
    for r in ne.iter_rows(named=True):
        if r["a"] in idx and r["b"] in idx:
            Z[idx[r["a"]], idx[r["b"]]] = r["z"]
    np.fill_diagonal(Z, np.nan)
    vmax = np.nanpercentile(np.abs(Z), 95)
    cm = P.cmap("vik").copy()
    cm.set_bad("#E6E6E6")
    im = ax.imshow(np.clip(Z, -vmax, vmax), cmap=cm, vmin=-vmax, vmax=vmax)
    lab = [en.get(t, t) for t in order]
    ax.set_xticks(range(K))
    ax.set_xticklabels(lab, rotation=60, ha="right", rotation_mode="anchor", fontsize=5)
    ax.set_yticks(range(K))
    ax.set_yticklabels(lab, fontsize=5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def panel_domains(ax, dom: pl.DataFrame):
    vals = dict(zip(dom["cd_setor"].to_list(), (dom["dominio"] + 1).to_list()))
    arr, bounds = M.setor_raster(vals, res=40.0, fill=0)
    arr = np.nan_to_num(arr).astype(int)
    k = int(dom["dominio"].max()) + 1
    rgba = M.to_rgba(arr, {i + 1: DOM_COLORS[i % len(DOM_COLORS)] for i in range(k)}, mask=(arr > 0).astype(int), bg=S.DARK_BG)
    S.dark(ax)
    ax.set_facecolor("white")
    M.show(ax, rgba, bounds)
    M.scalebar(ax, 10_000, color="#1A1A1A", loc=(0.55, 0.03))
    ax.set_xlabel("")
    ax.set_ylabel("")


def panel_markers(ax, mk: pl.DataFrame, names: dict, ntop: int = 2):
    top = mk.sort("cohen_d", descending=True).group_by("dominio").head(ntop)["covariavel"].unique().to_list()
    doms = sorted(mk["dominio"].unique().to_list())
    covs = [c for c in COV_EN if c in top] + [c for c in top if c not in COV_EN]
    D = np.zeros((len(doms), len(covs)))
    for r in mk.filter(pl.col("covariavel").is_in(covs)).iter_rows(named=True):
        D[doms.index(r["dominio"]), covs.index(r["covariavel"])] = r["cohen_d"]
    im = ax.imshow(np.clip(D, -1.5, 1.5), cmap=P.cmap("vik"), vmin=-1.5, vmax=1.5, aspect="auto")
    ax.set_xticks(range(len(covs)))
    ax.set_xticklabels([COV_EN.get(c, c) for c in covs], rotation=60, ha="right", rotation_mode="anchor", fontsize=4.6)
    ax.set_yticks(range(len(doms)))
    dl = N.domain_labels(short=True)
    ax.set_yticklabels([dl[d] for d in doms], fontsize=4.6)
    ax.tick_params(length=0)
    row_swatches(ax, [DOM_COLORS[d % len(DOM_COLORS)] for d in doms])
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def lr_matrix(lt: pl.DataFrame, tipos: list[str], ell: int = 500, pmax: float = 0.05):
    d = lt.filter((pl.col("escala_m") == ell) & (pl.col("p") < pmax))
    agg = d.group_by("emissor", "receptor_tipo").agg(pl.col("forca").sum())
    idx = {t: i for i, t in enumerate(tipos)}
    Smat = np.zeros((len(tipos), len(tipos)))
    for r in agg.iter_rows(named=True):
        if r["emissor"] in idx and r["receptor_tipo"] in idx:
            Smat[idx[r["emissor"]], idx[r["receptor_tipo"]]] = r["forca"]
    return Smat


def panel_bubbles(ax, lt: pl.DataFrame, en: dict, ell: int = 500, ncol: int = 10):
    d = lt.filter(pl.col("escala_m") == ell).with_columns((pl.col("ligante") + "→" + pl.col("receptor")).alias("par"),
                                                          (pl.col("emissor") + " → " + pl.col("receptor_tipo")).alias("tt"))
    toptt = d.group_by("tt").agg(pl.col("forca").sum()).sort("forca", descending=True).head(ncol)["tt"].to_list()
    pares = d.select("par").unique().sort("par")["par"].to_list()
    d = d.filter(pl.col("tt").is_in(toptt))
    d = d.with_columns((pl.col("forca") / pl.col("forca").max().over("par")).alias("rel"))
    xs = [toptt.index(t) for t in d["tt"]]
    ys = [pares.index(p) for p in d["par"]]
    size = 2 + 24 * np.clip(-np.log10(d["p"].to_numpy()) / 2.0, 0, 1)
    sc = ax.scatter(xs, ys, s=size, c=d["rel"].to_numpy(), cmap=P.cmap("batlow"), vmin=0, vmax=1, edgecolor="#555555", linewidth=0.2)
    ax.set_xticks(range(len(toptt)))
    ax.set_xticklabels([" → ".join(en.get(x, x) for x in t.split(" → ")) for t in toptt], rotation=60, ha="right",
                       rotation_mode="anchor", fontsize=5)
    ax.set_yticks(range(len(pares)))
    ax.set_yticklabels([" → ".join(LR_EN.get(x, x) for x in p.split("→")) for p in pares], fontsize=5)
    ax.tick_params(length=0)
    ax.set_xlim(-0.6, len(toptt) - 0.4)
    ax.set_ylim(len(pares) - 0.5, -0.5)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(True, color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    return sc


def panel_field(ax, best: dict):
    from cityomics.atlas.communication import kernel, setor_frame

    setor, _ = setor_frame()
    s = setor.filter(pl.col("x").is_not_null())
    xy = s.select("x", "y").to_numpy()
    K = kernel(xy, float(best["escala_m"]))
    V, mag = signal_field(xy, s[best["ligante"]].to_numpy(), s[best["receptor"]].to_numpy(), K)
    _, dist = M._bounds()
    bounds = tuple(dist.total_bounds)
    gx, gy, U, W = to_grid(xy, V, bounds, n=140)
    from scipy.ndimage import gaussian_filter

    U, W = gaussian_filter(U, 2.0), gaussian_filter(W, 2.0)
    S.dark(ax)
    dist.plot(ax=ax, color="#15151B", edgecolor="#2A2A33", linewidth=0.25)
    stream(ax, gx, gy, U, W, P.cmap("lipari"), density=1.5)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xlim(bounds[0], bounds[2])
    ax.set_ylim(bounds[1], bounds[3])
    ax.set_aspect("equal")
    ax.text(0.03, 0.97, f"{LR_EN[best['ligante']]} →\n{LR_EN[best['receptor']]}", transform=ax.transAxes, color="white",
            fontsize=5.5, va="top")


