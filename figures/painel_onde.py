"""Painéis do "onde" (antiga Fig. 4; narrativa B: taxas e Sankey na Fig. 3, variância e transições na Fig. 5, SHAP no ED7).

Fig. 4 — Onde: o tecido prevê o local do crime (spec-figuras §3; D47, D51, D55, D57, D61).

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
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import sankey
from cityomics.viz import style as S

RUA_EN = {k: v for k, v in N.FIXED_LONG.items() if k.startswith(("rua_", "n_"))}
FAM_EN = N.FAMILY_EN
GRP_EN = P.NOMES_GRUPOS_EN


def meta():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)", "Sem cadastro"]
    fam = perfil["familia"].to_list() + ["favela", "sem_cadastro"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0, 0.0]
    en = N.class_labels(perfil)[0]
    return tipos, fam, key, en


def panel_rates(ax, lam: pl.DataFrame, cols: dict, en: dict, fam_of: dict):
    d = lam.filter(~pl.col("classe").str.starts_with("n_") & (pl.col("exposicao_total") > 0) & (pl.col("lambda") > 0))
    d = d.sort("lambda")
    y = np.arange(d.height)
    for i, r in enumerate(d.iter_rows(named=True)):
        c = cols.get(r["classe"], P.RUAS.get(r["classe"], "#888888"))
        lo, hi = max(r["lambda_ic_lo"], r["lambda"] / 10, 3e-3), r["lambda_ic_hi"]
        ax.plot([lo, hi], [i, i], color=c, lw=1.0)
        ax.scatter(r["lambda"], i, s=10, color=c, zorder=3, edgecolor="white", linewidth=0.3)
    ax.set_xscale("log")
    ax.set_yticks(y)
    ax.set_yticklabels([en.get(c, RUA_EN.get(c, c)) for c in d["classe"]])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Phone crime per km of frontage or street per year")
    st = lam.filter(pl.col("classe") == "n_trilho")
    if st.height:
        tm = lam.filter(pl.col("classe") == "n_terminal")
        ax.text(0.0, -0.16, f"Rail stations: {float(st['lambda'][0]):.0f} phone crimes per station per year"
                + (f"; bus terminals: {float(tm['lambda'][0]):.0f}" if tm.height else ""),
                transform=ax.transAxes, ha="left", fontsize=5.2, color=S.MUTED)


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
    names = [("r2_tipos", "Parcel types"), ("r2_genes_sem_tipagem", "Same attributes, no typing"), ("r2_tecido", "Tissue (types, domains, streets)"),
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
    ax.set_xlabel("Out-of-sample R², tract phone crime rate 2025")
    ax.set_title(f"Between-tract variance share (ICC) = {v['icc_2025']:.2f}", fontsize=5.2, loc="right", color=S.MUTED)


def panel_sankey(ax, fl: pl.DataFrame, fam_of: dict):
    def famc(c):
        if c.startswith("rua_"):
            return "ruas"
        if c.startswith("n_"):
            return "estacoes"
        return fam_of.get(c, "sem_cadastro")
    f = fl.with_columns(pl.col("classe").map_elements(famc, return_dtype=pl.String).alias("fam"))
    f = f.group_by("fam", "origem").agg(pl.col("valor").sum())
    rep0 = json.loads((atlas_dir() / "atribuicao_celular_2025.json").read_text())
    tot = f.filter(pl.col("valor") > 0)["valor"].sum() + max(rep0.get("espacial_total", 0.0), 0.0)
    fam_order = [x for x in ["comercio", "servicos", "res_vertical_alto", "res_vertical_medio", "res_horizontal", "favela",
                             "industria", "vazio", "sem_cadastro", "ruas", "estacoes"] if x in f["fam"].to_list()]
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
    rep = json.loads((atlas_dir() / "atribuicao_celular_2025.json").read_text())
    esp = rep.get("espacial_total", 0.0) / tot * 100
    if esp > 0:
        flows.append(("Spatial (district)", "District context", esp))
        flows.append(("District context", "Phone theft", esp))
    for fm in fam_order:
        inflow = sum(v for s, d, v in flows if d == FAM_EN[fm])
        outred = sum(v for s, d, v in flows if s == FAM_EN[fm] and d == "Reduction")
        flows.append((FAM_EN[fm], "Phone theft", inflow - outred))
    fam_col = {"ruas": P.RUA_MAPA, "estacoes": "#C9C9C9"}
    mid = [(FAM_EN[fm], fam_col.get(fm, P.FAMILIAS.get(fm, ("#BBBBBB",))[0])) for fm in fam_order]
    left = [(GRP_EN[g], P.GRUPOS[g]) for g in groups]
    if esp > 0:
        mid.append(("District context", P.GRUPOS["espacial"]))
        left.append(("Spatial (district)", P.GRUPOS["espacial"]))
    sankey.draw(ax, left, mid, [("Phone theft", "#264653")], flows=[fl_ for fl_ in flows if fl_[2] > 1e-6],
                sink=("Reduction", "#9A9A9A"), xs=(0.18, 0.52, 0.86))


def panel_shap(ax):
    s = pl.read_parquet(atlas_dir() / "shap_celular_2025.parquet")
    let = json.loads((processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json").read_text())["letal"]["shap_lgbm"]
    core = json.loads((processed_dir().parents[1] / "prereg" / "core_covariates.json").read_text())["groups"]
    from cityomics.atlas.predictors import group_of

    rows = []
    for m, lab in (("completo", "Phone crime, full model"), ("sem_crime", "Phone crime, no crime history")):
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
    models = ["Phone crime, full model", "Phone crime, no crime history", "Lethal violence (district × quarter)"]
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
    if not (atlas_dir() / "transicoes_familia.parquet").exists():
        ax.text(0.5, 0.5, "transitions (pending)", ha="center", va="center", fontsize=6, color=S.MUTED, transform=ax.transAxes)
        ax.axis("off")
        return None
    T = pl.read_parquet(atlas_dir() / "transicoes_familia.parquet")
    fams = [f for f in ["res_horizontal", "res_vertical_medio", "res_vertical_alto", "comercio", "servicos", "industria", "vazio"]
            if f in T["de"].to_list()]
    M = np.zeros((len(fams), len(fams)))
    for r in T.iter_rows(named=True):
        if r["de"] in fams and r["para"] in fams:
            M[fams.index(r["de"]), fams.index(r["para"])] = r["taxa"]
    im = ax.imshow(np.log10(np.clip(M, 1e-4, 1)), cmap=P.cmap("lajolla"), vmin=-4, vmax=0)
    for i in range(len(fams)):
        ax.text(i, i, f"{M[i, i] * 100:.1f}", ha="center", va="center", fontsize=4.4, color="#1A1A1A")
    lab = [N.FAMILY_SHORT.get(f, f) for f in fams]
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


