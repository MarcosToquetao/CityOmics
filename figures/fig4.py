"""Fig. 4 — Onde: o tecido prevê o local do crime (spec-figuras §3; D47, D51, D55, D57, D61).

a: taxa atribuída por classe de célula (tipos de lote, favelas FCU, ruas), IC de bootstrap por distrito;
b: validação pontual (taxa estimada × observada pelos eventos ligados ao segmento e aos lotes lindeiros);
c: decomposição da variância e R² fora da amostra (tipos, genes sem tipagem, tecido, + covariáveis, média histórica);
d: Sankey grupo teórico → classe → roubo de celular (massa conservada);
e: melhores preditores (SHAP por grupo teórico) para o celular e para a letal;
f: estabilidade do tecido (matriz de transição anual das famílias pelo IPTU).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import palette as P
from cityomics.viz import sankey
from cityomics.viz import style as S

RUA_EN = {"rua_arterial_m": "Arterial streets", "rua_coletora_m": "Collector streets", "rua_local_m": "Local streets",
          "n_trilho": "Rail stations", "n_terminal": "Bus terminals"}
FAM_EN = {"res_horizontal": "Low-rise residential", "res_vertical_medio": "High-rise residential",
          "res_vertical_alto": "High-standard residential", "comercio": "Commerce", "servicos": "Services",
          "industria": "Industry", "vazio": "Vacant / green", "favela": "Favelas (FCU)", "sem_cadastro": "Unrecorded",
          "ruas": "Streets", "estacoes": "Stations"}
GRP_EN = P.NOMES_GRUPOS_EN


def meta():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)", "Sem cadastro"]
    fam = perfil["familia"].to_list() + ["favela", "sem_cadastro"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0, 0.0]
    en = dict(zip(perfil["nome"].to_list(), perfil["name_en"].to_list())) | {"Favela (FCU)": "Favelas (census FCU)", "Sem cadastro": "Unrecorded"}
    return tipos, fam, key, en


def panel_rates(ax, lam: pl.DataFrame, cols: dict, en: dict, fam_of: dict):
    d = lam.filter(~pl.col("classe").str.starts_with("n_") & (pl.col("exposicao_total") > 0) & (pl.col("lambda") > 0))
    d = d.sort("lambda")
    y = np.arange(d.height)
    for i, r in enumerate(d.iter_rows(named=True)):
        c = cols.get(r["classe"], P.RUAS.get(r["classe"], "#888888"))
        lo, hi = max(r["lambda_ic_lo"], r["lambda"] / 50), r["lambda_ic_hi"]
        ax.plot([lo, hi], [i, i], color=c, lw=1.0)
        ax.scatter(r["lambda"], i, s=10, color=c, zorder=3, edgecolor="white", linewidth=0.3)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([en.get(c, RUA_EN.get(c, c)) for c in d["classe"]])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Thefts per km of frontage or street per year")
    st = lam.filter(pl.col("classe") == "n_trilho")
    if st.height:
        ax.text(0.98, 0.04, f"Rail stations: {float(st['lambda'][0]) / 1000:.0f} thefts per station per year",
                transform=ax.transAxes, ha="right", fontsize=5.2, color=S.MUTED)


def panel_validation(ax, pv: pl.DataFrame, cols: dict):
    d = pv.filter(pl.col("lambda").is_not_null() & (pl.col("taxa_observada") > 0) & ~pl.col("classe").str.starts_with("n_")
                  & (pl.col("classe") != "estacoes"))
    x = d["lambda"].to_numpy()
    y = d["taxa_observada"].to_numpy() * 1000  # eventos por metro → por km
    c = [cols.get(k, P.RUAS.get(k, "#888888")) for k in d["classe"]]
    ax.scatter(x, y, s=12, c=c, edgecolor="white", linewidth=0.3, zorder=3)
    lo, hi = min(x.min(), y.min()) / 1.5, max(x.max(), y.max()) * 1.5
    ax.plot([lo, hi], [lo, hi], color="#BDBDBD", lw=0.6, zorder=0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Attributed rate (model)")
    ax.set_ylabel("Observed rate (geocoded points)")
    rep = json.loads((atlas_dir() / "atribuicao_celular_2025.json").read_text())
    ax.text(0.04, 0.92, f"Spearman ρ = {rep['spearman_validacao_pontual']:.2f}", transform=ax.transAxes, fontsize=5.5)
    ax.set_aspect("equal")


def panel_variance(ax):
    v = json.loads((atlas_dir() / "variancia_2025.json").read_text())
    names = [("r2_tipos", "Parcel types"), ("r2_genes_sem_tipagem", "Same genes, no typing"), ("r2_tecido", "Tissue (types, niches, streets)"),
             ("r2_tecido_mais_covariaveis", "Tissue + tract covariates"), ("r2_media_historica", "Historical mean (2022–24)")]
    vals = [v[k] for k, _ in names]
    colors = ["#5B9BD5", "#BFBFBF", "#264653", "#2A9D8F", "#8C8C8C"]
    y = np.arange(len(names))[::-1]
    ax.barh(y, vals, color=colors, height=0.62)
    for yi, val in zip(y, vals):
        ax.text(val + 0.01, yi, f"{val:.2f}", va="center", fontsize=5.2)
    ax.set_yticks(y)
    ax.set_yticklabels([n for _, n in names])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Out-of-sample R², tract theft rate 2025")
    ax.set_title(f"Between-tract share of variance (ICC) = {v['icc_2025']:.2f}", fontsize=5.5, loc="left", color=S.MUTED)


def panel_sankey(ax, fl: pl.DataFrame, fam_of: dict):
    def famc(c):
        if c.startswith("rua_"):
            return "ruas"
        if c.startswith("n_"):
            return "estacoes"
        return fam_of.get(c, "sem_cadastro")
    f = fl.with_columns(pl.col("classe").map_elements(famc, return_dtype=pl.String).alias("fam"))
    f = f.group_by("fam", "origem").agg(pl.col("valor").sum())
    tot = f.filter(pl.col("valor") > 0)["valor"].sum()
    fam_order = [x for x in ["comercio", "servicos", "res_vertical_alto", "res_vertical_medio", "res_horizontal", "favela",
                             "industria", "vazio", "ruas", "estacoes"] if x in f["fam"].to_list()]
    groups = ["identidade", "atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario"]
    flows = []
    red = 0.0
    for r in f.iter_rows(named=True):
        v = r["valor"] / tot * 100
        if r["origem"] == "identidade" or v > 0:
            flows.append((GRP_EN[r["origem"]], FAM_EN[r["fam"]], abs(v)))
        else:
            flows.append((FAM_EN[r["fam"]], "Reduction", -v))
            red += -v
    for fm in fam_order:
        inflow = sum(v for s, d, v in flows if d == FAM_EN[fm])
        outred = sum(v for s, d, v in flows if s == FAM_EN[fm] and d == "Reduction")
        flows.append((FAM_EN[fm], "Phone theft", inflow - outred))
    fam_col = {"ruas": P.RUA_MAPA, "estacoes": "#C9C9C9"}
    mid = [(FAM_EN[fm], fam_col.get(fm, P.FAMILIAS.get(fm, ("#BBBBBB",))[0])) for fm in fam_order]
    left = [(GRP_EN[g], P.GRUPOS[g]) for g in groups]
    sankey.draw(ax, left, mid, [("Phone theft", "#264653")], flows=[fl_ for fl_ in flows if fl_[2] > 1e-6],
                sink=("Reduction", "#9A9A9A"), xs=(0.18, 0.52, 0.86))


def panel_shap(ax):
    s = pl.read_parquet(atlas_dir() / "shap_celular_2025.parquet")
    let = json.loads((processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json").read_text())["letal"]["shap_lgbm"]
    core = json.loads((processed_dir().parents[1] / "prereg" / "core_covariates.json").read_text())["groups"]
    from cityomics.atlas.predictors import group_of

    rows = []
    for m, lab in (("completo", "Phone theft, full model"), ("sem_crime", "Phone theft, no crime history")):
        g = s.filter(pl.col("modelo") == m).group_by("grupo").agg(pl.col("fracao").sum())
        rows += [{"modelo": lab, "grupo": r["grupo"], "frac": r["fracao"]} for r in g.iter_rows(named=True)]
    lmap = {"l1": "historico_crime", "m4": "historico_crime", "m8": "historico_crime", "l4": "historico_crime",
            "trim": "contexto_temporal", "log_pop": "tamanho"}
    totl = sum(let.values())
    agg = {}
    for k, v in let.items():
        g = lmap.get(k, k if k in core else group_of(k, core))
        agg[g] = agg.get(g, 0) + v / totl
    rows += [{"modelo": "Lethal violence (district × quarter)", "grupo": g, "frac": v} for g, v in agg.items()]
    d = pl.DataFrame(rows)
    gorder = ["historico_crime", "atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario",
              "outras_atividade", "outras_social", "outras_cpted", "contexto_temporal", "tamanho", "outras"]
    models = ["Phone theft, full model", "Phone theft, no crime history", "Lethal violence (district × quarter)"]
    for i, m in enumerate(models[::-1]):
        left = 0.0
        dm = d.filter(pl.col("modelo") == m)
        for g in gorder:
            v = float(dm.filter(pl.col("grupo") == g)["frac"].sum())
            if v <= 0:
                continue
            ax.barh(i, v, left=left, color=P.GRUPOS.get(g, "#CCCCCC"), height=0.6, linewidth=0)
            if v > 0.08:
                ax.text(left + v / 2, i, f"{v * 100:.0f}%", ha="center", va="center", fontsize=4.8, color="white")
            left += v
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models[::-1])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Share of mean |SHAP|")
    return gorder


def panel_transitions(ax):
    T = pl.read_parquet(atlas_dir() / "transicoes_familia.parquet")
    fams = [f for f in ["res_horizontal", "res_vertical_medio", "res_vertical_alto", "comercio", "servicos", "industria", "vazio"]
            if f in T["de"].to_list()]
    M = np.zeros((len(fams), len(fams)))
    for r in T.iter_rows(named=True):
        if r["de"] in fams and r["para"] in fams:
            M[fams.index(r["de"]), fams.index(r["para"])] = r["taxa"]
    im = ax.imshow(np.log10(np.clip(M, 1e-4, 1)), cmap=P.cmap("lajolla"), vmin=-4, vmax=0)
    for i in range(len(fams)):
        ax.text(i, i, f"{M[i, i] * 100:.1f}", ha="center", va="center", fontsize=4.6, color="white")
    lab = [FAM_EN[f].replace(" residential", "").replace("-standard", "") for f in fams]
    ax.set_xticks(range(len(fams)))
    ax.set_xticklabels(lab, rotation=55, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(len(fams)))
    ax.set_yticklabels(lab)
    ax.set_xlabel("Class next year")
    ax.set_ylabel("Class this year")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def make(periodo: str = "dev"):
    check_periodo(periodo)
    tipos, fam, key, en = meta()
    cols = P.type_colors(tipos, fam, key)
    fam_of = dict(zip(tipos, fam))
    lam = pl.read_parquet(atlas_dir() / "atribuicao_celular_2025.parquet")
    pv = pl.read_parquet(atlas_dir() / "validacao_pontual_2025.parquet")
    fl = pl.read_parquet(atlas_dir() / "sankey_celular_2025.parquet")
    fig = S.figure(S.DOUBLE, 150)
    a = ax_mm(fig, 40, 5, 38, 60)
    panel_rates(a, lam, cols, en, fam_of)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 94, 8, 34, 34)
    panel_validation(b, pv, cols)
    S.fig_label(fig, "b", 84, 3)
    v = ax_mm(fig, 150, 8, 31, 40)
    panel_variance(v)
    S.fig_label(fig, "c", 132, 3)
    d = ax_mm(fig, 2, 76, 92, 66)
    panel_sankey(d, fl, fam_of)
    S.fig_label(fig, "d", 1, 73)
    e = ax_mm(fig, 130, 78, 50, 22)
    gorder = panel_shap(e)
    S.fig_label(fig, "e", 98, 73)
    f = ax_mm(fig, 120, 112, 30, 30)
    im = panel_transitions(f)
    S.fig_label(fig, "f", 98, 107)
    cb = ax_mm(fig, 156, 116, 2.2, 22)
    cbar = fig.colorbar(im, cax=cb)
    cbar.set_ticks([-4, -2, 0])
    cbar.set_ticklabels(["0.01%", "1%", "100%"])
    cbar.ax.tick_params(labelsize=5, length=1.5)
    cbar.set_label("Annual transition rate", fontsize=5.2)
    lg = ax_mm(fig, 166, 104, 16, 40)
    lg.axis("off")
    yy = 1.0
    for g in [g for g in gorder if g in P.GRUPOS][:8]:
        lg.add_patch(__import__("matplotlib").patches.Rectangle((0, yy - 0.05), 0.12, 0.07, color=P.GRUPOS[g], transform=lg.transAxes, clip_on=False))
        lg.text(0.17, yy - 0.015, GRP_EN[g], fontsize=4.8, va="center", transform=lg.transAxes)
        yy -= 0.12
    return S.save(fig, "fig4", periodo)
