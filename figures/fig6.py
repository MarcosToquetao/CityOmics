"""Fig. 6 — Fora da amostra e equidade (parametrizada: 2025 em dev; 2026 depois do FREEZE, D52).

a: desempenho dos finalistas (CRPS, Brier) no teste; em dev, 2025 com o espaço de 2026 lacrado;
b: habilidade mês a mês contra o NB-GLM;
c: mapa de acerto/erro no top 5% da área (rasterizado, D60);
d: habilidade por domínio do tecido (fora do cofre espacial, D53);
e: auditoria por quintil de renda: área sinalizada, crime capturado e calibração;
f: janela prospectiva (vazia até existir).
"""

from __future__ import annotations

import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.atlas import guard
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.eval import scores
from cityomics.paths import processed_dir
from cityomics.viz import figdata as F
from cityomics.viz import maps as M
from cityomics.viz import palette as P
from cityomics.viz import style as S

FINAL = ["glm", "hawkes", "lgbm_completo", "gnn", "ensemble"]


def _setup(tag):
    ev, mu, phi, dist = F.load_eval(tag)
    y = ev["y"].to_numpy().astype(float)
    crps = {m: scores.crps_nb(y, mu[m], phi[m]) for m in FINAL}
    return ev, mu, phi, dist, y, crps


def panel_test(ax, ev, mu, phi, y, crps):
    br = {m: float(np.mean((scores.prob_ge1(mu[m], phi[m]) - (y >= 0.5)) ** 2)) for m in FINAL}
    x = np.arange(len(FINAL))
    ax.bar(x - 0.18, [float(np.mean(crps[m])) for m in FINAL], 0.34, color=[P.FAMILIAS_MODELO[P.MODELO_FAMILIA[m]] for m in FINAL], label="2025 (development)")
    ax.bar(x + 0.18, [float(np.mean(crps[m])) for m in FINAL], 0.34, color="none", edgecolor="#BDBDBD", hatch="//////", lw=0.4, label="2026 (sealed)")
    ax.set_xticks(x)
    ax.set_xticklabels([F.NOMES_MODELO[m].replace("Graph neural network", "GNN") for m in FINAL], rotation=30, ha="right", rotation_mode="anchor")
    lo = min(float(np.mean(crps[m])) for m in FINAL)
    ax.set_ylim(lo * 0.95, max(float(np.mean(crps[m])) for m in FINAL) * 1.02)
    ax.set_ylabel("CRPS (lower is better)")
    ax.legend(loc="upper right", handlelength=1.2, fontsize=5)
    for i, m in enumerate(FINAL):
        ax.text(i - 0.18, float(np.mean(crps[m])) * 1.002, f"{br[m]:.3f}", ha="center", va="bottom", fontsize=4.4, rotation=90, color=S.MUTED)


def panel_monthly(ax, ev, crps):
    mes = ev["mes"].to_numpy()
    months = sorted(np.unique(mes))
    for m in FINAL[1:]:
        sk = [1 - np.mean(crps[m][mes == k]) / np.mean(crps["glm"][mes == k]) for k in months]
        ax.plot(range(len(months)), np.array(sk) * 100, color=P.FAMILIAS_MODELO[P.MODELO_FAMILIA[m]], lw=0.9, marker="o", ms=1.6,
                label=F.NOMES_MODELO[m].replace("Graph neural network", "GNN"))
    ax.axhline(0, color=S.INK, lw=0.5)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([k[5:] for k in months])
    ax.set_xlabel("Month of 2025")
    ax.set_ylabel("CRPS skill vs NB-GLM (%)")
    ax.legend(loc="lower left", ncol=2, fontsize=4.8, handlelength=1.2, columnspacing=0.8)


def panel_hitmiss(ax, ev, mu, share=0.05):
    an = ev.with_columns(pl.Series("mu", mu["ensemble"])).group_by("cd_setor").agg(
        pl.col("mu").sum(), pl.col("y").sum(), pl.col("area_km2").first())
    a = an["area_km2"].to_numpy()
    def top(score):
        o = np.argsort(-score)
        k = np.searchsorted(np.cumsum(a[o]), share * a.sum()) + 1
        sel = np.zeros(len(a), bool)
        sel[o[:k]] = True
        return sel
    flag = top(an["mu"].to_numpy() / a)
    real = top(an["y"].to_numpy() / a)
    cls = np.where(flag & real, 1, np.where(flag & ~real, 2, np.where(~flag & real, 3, 4)))
    arr, bounds = M.setor_raster(dict(zip(an["cd_setor"].to_list(), cls.tolist())), res=40.0, fill=0)
    arr = np.nan_to_num(arr).astype(int)
    rgba = M.to_rgba(arr, {1: "#F5C451", 2: "#5B9BD5", 3: "#D1495B", 4: "#26262E"}, mask=(arr > 0).astype(int), bg=S.DARK_BG)
    S.dark(ax)
    ax.set_facecolor("white")
    M.show(ax, rgba, bounds)
    hit = (flag & real).sum() / max(real.sum(), 1)
    for i, (c, t) in enumerate((("#F5C451", "Flagged and top-5%"), ("#5B9BD5", "Flagged only"), ("#D1495B", "Missed top-5%"))):
        ax.add_patch(__import__("matplotlib").patches.Rectangle((0.03, 0.95 - i * 0.055), 0.04, 0.03, color=c, transform=ax.transAxes))
        ax.text(0.09, 0.965 - i * 0.055, t, transform=ax.transAxes, fontsize=4.8, va="center", color=S.INK)
    ax.text(0.03, 0.75, f"{hit * 100:.0f}% of top tracts flagged", transform=ax.transAxes, fontsize=4.8, color=S.INK)


def panel_niche(ax, ev, crps):
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet")
    d = ev.select("cd_setor").join(dom, on="cd_setor", how="left")
    setd = pl.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "cd_dist"]).with_columns(
        pl.col("cd_setor").cast(pl.String), pl.col("cd_dist").cast(pl.String))
    keep = guard.explore_mask(ev.select("cd_setor").join(setd, on="cd_setor", how="left")["cd_dist"].to_numpy())
    lab = d["dominio"].fill_null(-1).to_numpy()
    rows = []
    for k in sorted(set(lab[lab >= 0])):
        i = (lab == k) & keep
        rows.append((k, 1 - np.mean(crps["ensemble"][i]) / np.mean(crps["glm"][i]), i.sum()))
    rows.sort(key=lambda r: r[1])
    from figures_fig3_colors import DOM_COLORS

    y = np.arange(len(rows))
    ax.barh(y, [r[1] * 100 for r in rows], color=[DOM_COLORS[r[0] % len(DOM_COLORS)] for r in rows], height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels([f"N{r[0] + 1}" for r in rows])
    ax.axvline(0, color=S.INK, lw=0.5)
    ax.set_xlabel("Ensemble CRPS skill vs NB-GLM (%)")
    ax.tick_params(axis="y", length=0)


def panel_equity(ax, ev, mu):
    renda = pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet")
    col = next((c for c in renda.columns if "renda" in c and "media" in c), None)
    r = renda.select(pl.col("cd_setor").cast(pl.String), pl.col(col).alias("renda"))
    an = ev.with_columns(pl.Series("mu", mu["ensemble"])).group_by("cd_setor").agg(
        pl.col("mu").sum(), pl.col("y").sum(), pl.col("area_km2").first()).join(r, on="cd_setor", how="left")
    an = an.filter(pl.col("renda").is_not_null())
    q = an["renda"].qcut(5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"]).cast(pl.String).to_numpy()
    a = an["area_km2"].to_numpy()
    o = np.argsort(-(an["mu"].to_numpy() / a))
    k = np.searchsorted(np.cumsum(a[o]), 0.05 * a.sum()) + 1
    flag = np.zeros(len(a), bool)
    flag[o[:k]] = True
    yv, mv = an["y"].to_numpy(), an["mu"].to_numpy()
    qs = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    share_area = [a[(q == g) & flag].sum() / a[flag].sum() * 100 for g in qs]
    share_crime = [yv[q == g].sum() / yv.sum() * 100 for g in qs]
    calib = [mv[q == g].sum() / max(yv[q == g].sum(), 1) for g in qs]
    x = np.arange(5)
    ax.bar(x - 0.18, share_area, 0.34, color="#264653", label="Flagged area (top 5%)")
    ax.bar(x + 0.18, share_crime, 0.34, color="#BDBDBD", label="Observed thefts")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{g}\n×{c:.2f}" for g, c in zip(qs, calib)])
    ax.set_ylabel("Share (%)")
    ax.set_xlabel("Tract income quintile (predicted/observed)")
    ax.legend(loc="upper left", fontsize=4.8, handlelength=1.0)


def panel_prospective(ax):
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 1)
    for i, m in enumerate(["Nov 26", "Dec 26", "Jan 27", "Feb 27", "Mar 27"]):
        ax.add_patch(__import__("matplotlib").patches.Rectangle((i + 0.1, 0.25), 0.8, 0.5, fill=False, edgecolor="#BDBDBD", hatch="//////", lw=0.4))
        ax.text(i + 0.5, 0.15, m, ha="center", fontsize=4.8, color=S.MUTED)
    ax.text(2.5, 0.85, "Prospective window: forecasts frozen, outcomes pending", ha="center", fontsize=5, color=S.MUTED)
    ax.axis("off")


def make(periodo: str = "dev"):
    check_periodo(periodo)
    import sys
    import types

    m3 = types.ModuleType("figures_fig3_colors")
    m3.DOM_COLORS = ["#E8743B", "#5B9BD5", "#2A9D8F", "#B99BF0", "#E3B23C", "#8C7B6B", "#D1495B", "#6A994E", "#264653",
                     "#F4A261", "#9C89B8", "#7FB3EE"]
    sys.modules["figures_fig3_colors"] = m3
    tag = "dev" if periodo == "dev" else periodo
    ev, mu, phi, dist, y, crps = _setup(tag)
    fig = S.figure(S.DOUBLE, 130)
    a = ax_mm(fig, 12, 6, 44, 40)
    panel_test(a, ev, mu, phi, y, crps)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 72, 6, 50, 40)
    panel_monthly(b, ev, crps)
    S.fig_label(fig, "b", 62, 3)
    c = ax_mm(fig, 132, 4, 50, 72)
    panel_hitmiss(c, ev, mu)
    S.fig_label(fig, "c", 128, 2)
    d = ax_mm(fig, 12, 70, 30, 46)
    panel_niche(d, ev, crps)
    S.fig_label(fig, "d", 1, 66)
    e = ax_mm(fig, 56, 70, 50, 38)
    panel_equity(e, ev, mu)
    S.fig_label(fig, "e", 48, 66)
    f = ax_mm(fig, 112, 96, 70, 22)
    panel_prospective(f)
    S.fig_label(fig, "f", 110, 90)
    return S.save(fig, "fig6", periodo)
