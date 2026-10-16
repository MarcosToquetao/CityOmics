"""Fig. 3 — Arquitetura do tecido: nichos e comunicação (spec-figuras §3; D39, D40, D59).

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

from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import maps as M
from cityomics.viz import palette as P
from cityomics.viz import style as S
from cityomics.viz.chord import circle
from cityomics.viz.fields import signal_field, stream, to_grid

DOM_COLORS = ["#E8743B", "#5B9BD5", "#2A9D8F", "#B99BF0", "#E3B23C", "#8C7B6B", "#D1495B", "#6A994E", "#264653",
              "#F4A261", "#9C89B8", "#7FB3EE"]
COV_EN = {
    "infra_dist_estacao_trilhos_m": "Distance to rail station", "infra_dist_terminal_onibus_m": "Distance to bus terminal",
    "infra_dens_ponto_onibus_km2": "Bus-stop density", "cnpj_estoque_bar_restaurante": "Bars and restaurants",
    "cnpj_estoque_comercio_varejista": "Retail shops", "cnpj_estoque_financeiro": "Banks", "agencias_estoque": "Bank branches",
    "osm_dens_poi_bar_noturno_km2": "Nightlife density", "osm_dens_poi_banco_atm_km2": "ATM density",
    "osm_dens_poi_alimentacao_km2": "Food outlets", "osm_dens_poi_comercio_km2": "Shop density", "osm_dist_bar_noturno_m": "Distance to nightlife",
    "pop_dasi": "Resident population", "censo2022_dens_pop_km2": "Population density", "ipvs_ipvs_codigo": "Social vulnerability (IPVS)",
    "censo_interp_renda_media_resp": "Household income", "censo2022_cv_renda_resp": "Income inequality", "censo_d_renda_rel": "Income change",
    "censo_interp_frac_homens_15_29": "Young men share", "censo_interp_taxa_analfabetismo_15": "Illiteracy",
    "censo2022_frac_dom_nao_ocupados": "Vacant dwellings", "censo2022_moradores_por_dom": "Crowding", "censo_g_pop": "Population growth",
    "infra_dist_favela_m": "Distance to favela", "censo2022_frac_cortico": "Tenements (cortiços)",
    "censo2022_frac_faces_iluminacao": "Street lighting (census)", "infra_dens_iluminacao_km2": "Lamp-post density",
    "censo2022_frac_faces_calcada": "Sidewalks", "censo2022_frac_faces_pavimentadas": "Paved streets", "osm_dens_intersecoes_km2": "Intersection density",
    "osm_betweenness_media": "Street betweenness", "osm_frac_becos": "Dead ends", "sp156_iluminacao_s6": "Lighting complaints",
    "sp156_limpeza_entulho_s6": "Debris complaints", "sp156_imovel_abandonado_s12": "Abandoned-property complaints", "luz_noturna": "Night lights (VIIRS)",
    "n_transacoes_s12": "Property sales", "preco_m2_mediana_m12": "Price per m²", "frac_financiada_m12": "Mortgage share",
    "cnpj_entradas_construcao_imobiliario_s12": "New construction firms",
}
LR_EN = {"fluxo_trilhos": "Rail flow", "fluxo_onibus": "Bus flow", "vida_noturna": "Nightlife", "varejo": "Retail", "dinheiro": "Cash",
         "alvos_a_pe": "Pedestrian targets", "pouca_iluminacao": "Poor lighting", "rotas_de_fuga": "Escape routes",
         "abandono": "Disorder", "desvantagem": "Disadvantage"}


def meta():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)"]
    fam = perfil["familia"].to_list() + ["favela"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0]
    from cityomics.viz.names import SHORT

    en = dict(zip(perfil["nome"].to_list(), perfil["name_en"].to_list())) | {"Favela (FCU)": "Favelas"}
    en = {k: SHORT.get(v, v) for k, v in en.items()}
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
    from cityomics.viz.names import domain_labels

    dl = domain_labels(short=True)
    ax.set_yticklabels([dl[d] for d in doms], fontsize=4.6)
    for i, d in enumerate(doms):
        ax.add_patch(__import__("matplotlib").patches.Rectangle((-1.4, i - 0.4), 0.6, 0.8, color=DOM_COLORS[d % len(DOM_COLORS)], clip_on=False))
    ax.tick_params(length=0)
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
    ax.set_xticklabels([" → ".join(en.get(x, x) for x in t.split(" → ")) for t in toptt], rotation=60, ha="right", rotation_mode="anchor", fontsize=4.6)
    ax.set_yticks(range(len(pares)))
    ax.set_yticklabels([" → ".join(LR_EN.get(x, x) for x in p.split("→")) for p in pares], fontsize=4.6)
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
    ax.text(0.03, 0.97, f"{LR_EN[best['ligante']]} → {LR_EN[best['receptor']]}", transform=ax.transAxes, color="white",
            fontsize=5.5, va="top")


def make(periodo: str = "dev"):
    check_periodo(periodo)
    tipos, fam, key, en, n = meta()
    cols = P.type_colors(tipos, fam, key)
    order = P.ordered_types(tipos, fam, key)
    ne = pl.read_parquet(atlas_dir() / "nhood_enrichment_2025.parquet")
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet")
    mk = pl.read_parquet(atlas_dir() / "dominio_marcadores_2025.parquet")
    lt = pl.read_parquet(atlas_dir() / "comunicacao" / "lr_tipos.parquet")
    act = pl.read_parquet(atlas_dir() / "comunicacao" / "lr_atividade.parquet")
    best = act.sort("ganho_pct", descending=True).row(0, named=True)
    fig = S.figure(S.DOUBLE, 158)
    a = ax_mm(fig, 22, 4, 42, 42)
    im = panel_nhood(a, ne, order, en)
    S.fig_label(fig, "a", 1, 2)
    cb = ax_mm(fig, 66, 10, 2.2, 22)
    c1 = fig.colorbar(im, cax=cb)
    c1.set_label("Neighbourhood enrichment (z)", fontsize=5.0)
    c1.ax.tick_params(labelsize=4.8, length=1.5)
    b = ax_mm(fig, 82, 4, 44, 62)
    panel_domains(b, dom)
    S.fig_label(fig, "b", 76, 2)
    c = ax_mm(fig, 158, 4, 24, 30)
    im2 = panel_markers(c, mk, {})
    S.fig_label(fig, "c", 130, 2)
    cb2 = ax_mm(fig, 136, 64, 18, 2.0)
    c2 = fig.colorbar(im2, cax=cb2, orientation="horizontal")
    c2.set_label("Cohen's d", fontsize=5.0)
    c2.ax.tick_params(labelsize=4.8, length=1.5)
    d = ax_mm(fig, 10, 86, 56, 56)
    Smat = lr_matrix(lt, tipos)
    circle(d, tipos, np.array([n.get(t, 2000) for t in tipos], dtype=float), Smat, cols, labels=en, top=20)
    S.fig_label(fig, "d", 1, 80)
    e = ax_mm(fig, 96, 84, 36, 40)
    sc = panel_bubbles(e, lt, en)
    S.fig_label(fig, "e", 72, 80)
    cb3 = ax_mm(fig, 96, 150, 16, 2.0)
    c3 = fig.colorbar(sc, cax=cb3, orientation="horizontal")
    c3.set_label("Strength relative to pair maximum", fontsize=4.8)
    c3.ax.tick_params(labelsize=4.6, length=1.5)
    f = ax_mm(fig, 136, 78, 46, 72)
    panel_field(f, best)
    S.fig_label(fig, "f", 132, 76)
    return S.save(fig, "fig3", periodo)
