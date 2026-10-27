"""Painéis da previsão (antiga Fig. 5; narrativa B: captura, forest e contraste letal na Fig. 6; o resto no ED8 e no ED10).

Fig. 5 — Quando: quanto os métodos emprestados acrescentam (spec-figuras §3)."""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.paths import processed_dir
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S

FAMILIA_EN = N.MODEL_FAMILY_EN


def panel_forest(ax, df: pl.DataFrame) -> None:
    df = df.sort("diff", descending=True)
    y = np.arange(df.height)
    for i, r in enumerate(df.iter_rows(named=True)):
        fam = P.MODELO_FAMILIA[r["modelo"]]
        c = P.FAMILIAS_MODELO[fam]
        sig = (r["p_adj"] == r["p_adj"]) and r["p_adj"] < 0.05
        ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=c, lw=1.0, solid_capstyle="round")
        ax.scatter(r["diff"], i, s=10, color=c if sig else "white", edgecolor=c, linewidth=0.7, zorder=3)
    ax.axvline(0, color=S.INK, lw=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([N.MODEL_EN.get(m, m) for m in df["modelo"]])
    ax.set_xlabel("Difference in CRPS vs negative\nbinomial GLM (negative = better)")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-0.7, df.height - 0.3)
    xmax = float(df["ci_high"].max())
    ax.set_xlim(min(-0.04, float(df["ci_low"].min()) * 1.1), xmax * 1.05)


def panel_capture(ax, cc: pl.DataFrame) -> None:
    style = {"acaso": dict(color="#BDBDBD", lw=0.6, ls=(0, (2, 2))),
             "media_historica": dict(color="#8C8C8C", lw=0.9),
             "ensemble": dict(color="#264653", lw=1.2),
             "teto_ruido": dict(color="#264653", lw=0.8, ls=(0, (1, 1.2))),
             "oraculo": dict(color="#E9C46A", lw=1.0)}
    label = {"acaso": "Chance", "media_historica": "Historical mean", "ensemble": "Ensemble",
             "teto_ruido": "If forecasts were exact", "oraculo": "Oracle (ex post)"}
    d = cc.filter(pl.col("alvo") == "n_total")
    for k, st in style.items():
        s = d.filter(pl.col("curva") == k).sort("area")
        ax.plot(s["area"] * 100, s["captura"] * 100, **st)
    g = cc.filter((pl.col("alvo") == "n_geo") & (pl.col("curva") == "ensemble")).sort("area")
    ax.plot(g["area"] * 100, g["captura"] * 100, color="#2A9D8F", lw=0.8, ls=(0, (3, 1.5)))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 85)
    ax.set_xlabel("Area flagged (% of city)")
    ax.set_ylabel("Phone crime captured (%)")
    for x in (1, 5):
        v = float(d.filter((pl.col("curva") == "ensemble") & (pl.col("area") == x / 100))["captura"][0]) * 100
        ax.plot([x, x], [0, v], color="#D9D9D9", lw=0.5, zorder=0)
        ax.text(x + 0.15, v - 6, f"{v:.0f}%", fontsize=5.5, color="#264653")
    from matplotlib.lines import Line2D

    handles = [Line2D([], [], **style[k]) for k in ("oraculo", "ensemble", "teto_ruido", "media_historica", "acaso")]
    handles.append(Line2D([], [], color="#2A9D8F", lw=0.8, ls=(0, (3, 1.5))))
    labels = [label[k] for k in ("oraculo", "ensemble", "teto_ruido", "media_historica", "acaso")] + ["Ensemble, geocoded only"]
    ax.legend(handles, labels, loc="lower right", handlelength=1.6, borderaxespad=0.3, labelspacing=0.25, fontsize=5.2)


def panel_where_when(ax, w: pl.DataFrame) -> None:
    for r in w.iter_rows(named=True):
        fam = P.MODELO_FAMILIA[r["modelo"]]
        ax.scatter(r["r_total"], r["r_dentro"], s=14, color=P.FAMILIAS_MODELO[fam], edgecolor="white", linewidth=0.4, zorder=3)
    lab = {"gnn": (-0.012, 0.0, "right"), "ensemble": (0.0, -0.028, "center"), "media_historica": (-0.012, 0.0, "right"),
           "glm": (-0.012, 0.004, "right"), "lgbm_completo": (-0.012, -0.004, "right"), "kde": (0.012, 0.0, "left"),
           "chronos": (-0.012, 0.0, "right"), "lgbm_sem_crime": (-0.012, 0.0, "right"), "hawkes": (-0.012, 0.0, "right"),
           "maxent": (0.012, 0.0, "left")}
    for r in w.iter_rows(named=True):
        if r["modelo"] in lab:
            dx, dy, ha = lab[r["modelo"]]
            ax.text(r["r_total"] + dx, r["r_dentro"] + dy, N.MODEL_EN.get(r["modelo"], r["modelo"]), fontsize=5.0, color=S.INK,
                    ha=ha, va="center")
    ax.axhline(0, color="#BDBDBD", lw=0.5, zorder=0)
    ax.set_xlabel("Correlation across all tract-months (where)")
    ax.set_ylabel("Correlation within tracts (when)")
    ax.set_xlim(0.42, 0.9)
    ax.set_ylim(-0.2, 0.28)


def panel_calibration(ax, cal: pl.DataFrame) -> None:
    cols = {"glm": "#8C8C8C", "lgbm_completo": P.FAMILIAS_MODELO["aprendizado"], "ensemble": "#264653"}
    ax.plot([0, 1], [0, 1], color="#D9D9D9", lw=0.6)
    for m, c in cols.items():
        s = cal.filter(pl.col("modelo") == m).sort("prev")
        ax.plot(s["prev"], s["obs"], color=c, lw=0.9, marker="o", ms=1.8)
        ece = float(s["ece"][0])
        ax.text(0.98, {"glm": 0.04, "lgbm_completo": 0.12, "ensemble": 0.20}[m], f"{N.MODEL_EN[m]}: {ece:.3f}",
                fontsize=5, color=c, ha="right", va="bottom", transform=ax.transAxes)
    ax.text(0.98, 0.28, "Calibration error (ECE)", fontsize=5, color=S.INK, ha="right", va="bottom", transform=ax.transAxes)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted P(≥1 phone crime)")
    ax.set_ylabel("Observed frequency")
    ax.set_aspect("equal")


def panel_turnover(ax) -> None:
    p = processed_dir() / "atlas" / "renovacao_vs_crime.parquet"
    if not p.exists():
        ax.text(0.5, 0.5, "tissue turnover\n(pending)", ha="center", va="center", fontsize=6, color=S.MUTED, transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    rv = pl.read_parquet(p).filter(pl.col("m") > 0.5)
    x = rv["renovacao"].to_numpy() * 100
    y = rv["sobredispersao_intra"].to_numpy()
    # decis por posto (muitos setores têm renovação zero: quantis repetidos deixariam faixas vazias)
    rank = np.argsort(np.argsort(x, kind="stable"), kind="stable")
    idx = (rank * 10 // len(x)).astype(int)
    mx = [np.median(x[idx == i]) for i in range(10)]
    my = [np.median(y[idx == i]) for i in range(10)]
    lo = [np.quantile(y[idx == i], 0.25) for i in range(10)]
    hi = [np.quantile(y[idx == i], 0.75) for i in range(10)]
    ax.fill_between(mx, lo, hi, color="#B99BF0", alpha=0.35, lw=0)
    ax.plot(mx, my, color="#6A4C93", lw=1.0, marker="o", ms=2)
    rho = json.loads((processed_dir() / "atlas" / "destino.json").read_text())["spearman_renovacao_vs_variabilidade_crime"]
    ax.text(0.04, 0.92, f"Spearman ρ = {rho:.2f}", transform=ax.transAxes, fontsize=5.5)
    ax.set_xlabel("Tissue turnover (% parcels changing class per year)")
    ax.set_ylabel("Month-to-month variability\n(s.d. / √mean)")


def panel_contrast(ax, dc: pl.DataFrame) -> None:
    order = ["glm", "hawkes", "lgbm"]
    x = np.arange(len(order))
    for j, (o, c) in enumerate((("celular", "#264653"), ("letal", "#D1495B"))):
        v = [float(dc.filter((pl.col("desfecho") == o) & (pl.col("modelo") == m))["skill"][0]) * 100 for m in order]
        ax.bar(x + (j - 0.5) * 0.36, v, width=0.34, color=c, label=N.CRIME_EN[o])
    ax.axhline(0, color=S.INK, lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels([N.model_tick(m) for m in order])
    ax.set_ylabel("CRPS skill vs historical mean (%)")
    ax.set_title("District × quarter", fontsize=6, loc="left")
    ax.legend(loc="upper right", handlelength=1.0, borderaxespad=0.2)
    ax.set_ylim(-4, 10)


