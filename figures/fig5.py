"""Fig. 5 — Estabilidade, memória e mudança (narrativa B; D63, D66).

a: R² fora da amostra da taxa do setor: tipos, genes sem tipagem, tecido, tecido + covariáveis, média histórica;
b: decomposição da variância entre setores do log da taxa anual (2022–2025): tecido, memória estável além
   do tecido, transitória (ruído de Poisson + mudança), covariância;
c: persistência do resíduo além do tecido com a defasagem (1–3 anos);
d: estabilidade do tecido: transição anual entre famílias de lote pelo IPTU (2012–2025);
e: queda de 2022 para 2025 por classe (razão da taxa contra a razão da cidade; IC por distrito);
f: variação 2022→2025 por fenótipo.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

import painel_onde as PO
import rotulos as R
from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.viz import style as S

PARTES = [("tecido", "Composition", "#264653"), ("memoria_estavel", "Persistent effect", "#E9C46A"),
          ("transitoria", "Transient", "#BDBDBD")]


def panel_memoria(ax, mem: dict):
    rows = [("All tracts", mem["partes"]), ("High-crime tracts", mem["setores_altos"]["partes"])]
    for i, (nome, p) in enumerate(rows):
        left = 0.0
        for k, lab, c in PARTES:
            v = p[k]
            ax.barh(i, v, left=left, color=c, height=0.62, linewidth=0)
            if v > 0.08:
                ax.text(left + v / 2, i, f"{v * 100:.0f}%", ha="center", va="center", fontsize=4.8,
                        color="white" if c != "#BDBDBD" else S.INK)
            left += v
    ax.set_yticks([0, 1])
    ct = lambda v: f"{v * 100:+.0f}%".replace("-", "−")  # noqa: E731
    ax.set_yticklabels([f"{nome}\n(cross-term {ct(p['covariancia'])})" for nome, p in rows], linespacing=1.1)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.25)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    # as três partes somam mais que 100% quando o termo cruzado é negativo
    ax.axvline(1.0, color=S.INK, lw=0.5, ls=(0, (2, 2)), zorder=0)
    ax.set_xlabel("Share of between-tract variance (log rate)")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    from matplotlib.patches import Patch

    ax.legend([Patch(color=c) for _, _, c in PARTES], [lab for _, lab, _ in PARTES], loc="upper center",
              bbox_to_anchor=(0.45, -0.55), ncol=3, fontsize=4.8, handlelength=1.0, columnspacing=0.8)


def panel_persistencia(ax, mem: dict):
    L = [1, 2, 3]
    series = [("Residual beyond composition, all", mem["persistencia_residuo"], "#E9C46A", "-"),
              ("Residual, high-crime tracts", mem["setores_altos"]["persistencia_residuo"], "#B8860B", "--"),
              ("Raw log rate, all", mem["persistencia_bruta"], "#8C8C8C", ":")]
    for lab, d, c, ls in series:
        ax.plot(L, [d[str(k)] for k in L], color=c, ls=ls, marker="o", ms=2.5, lw=1.0, label=lab)
    ax.set_xticks(L)
    ax.set_xlabel("Lag (years)")
    ax.set_ylabel("Correlation across years")
    ax.set_ylim(0, 1)
    ax.legend(loc="lower left", fontsize=4.6, handlelength=1.6)
    ax.text(0.97, 0.97, f"residual r at 3 yr = {mem['persistencia_residuo']['3']:.2f}", transform=ax.transAxes, ha="right", va="top", fontsize=5)


def panel_queda_classe(ax, q: pl.DataFrame, longo: dict, cols: dict):
    # classes não identificadas (taxa colapsada a ~0 num dos anos, razão < 0,05) ficam de fora
    d = q.filter((pl.col("part_2022") >= 0.004) & pl.col("razao_rel").is_finite() & (pl.col("razao_rel") >= 0.05)).sort("razao_rel")
    y = np.arange(d.height)
    for i, r in enumerate(d.iter_rows(named=True)):
        c = cols.get(r["classe"], "#888")
        lo, hi = max(r["ic_lo"], 0.05), min(r["ic_hi"], 5)
        ax.plot([lo, hi], [i, i], color=c, lw=0.9)
        ax.scatter(r["razao_rel"], i, s=6 + 220 * r["part_2022"], color=c, edgecolor="white", linewidth=0.3, zorder=3,
                   marker="D" if r["classe"].startswith("n_") else "o")
    ax.axvline(1, color=S.INK, lw=0.5)
    ax.set_xscale("log")
    from matplotlib.ticker import FixedLocator, NullLocator

    ax.xaxis.set_major_locator(FixedLocator([0.1, 0.25, 0.5, 1, 2]))
    ax.set_xticklabels(["0.1", "0.25", "0.5", "1", "2"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_yticks(y)
    ax.set_yticklabels([longo.get(c, c) for c in d["classe"]], fontsize=5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("2025/2022 rate ratio,\nrelative to the city")
    ax.set_xlim(0.05, 4)


def panel_queda_fen(ax, qj: dict):
    f = sorted(qj["fenotipos"].items(), key=lambda kv: kv[1]["r_total"])
    v = [(r["r_total"] - 1) * 100 for _, r in f]
    y = np.arange(len(f))
    ax.barh(y, v, color=["#264653" if x < 0 else "#D1495B" for x in v], height=0.65)
    ax.axvline(0, color=S.INK, lw=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels([R.FEN_EN[k] for k, _ in f], fontsize=5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Change\n2022→2025 (%)")


def make(periodo: str = "dev"):
    check_periodo(periodo)
    fd = atlas_dir() / "fenotipo"
    mem = json.loads((fd / "memoria.json").read_text())
    q = pl.read_parquet(fd / "queda_celular.parquet")
    qj = json.loads((fd / "queda.json").read_text())
    _, _, _, longo, curto = R.classes()
    cols = R.cores()

    fig = S.figure(S.DOUBLE, 150)
    a = ax_mm(fig, 40, 8, 24, 40)
    PO.panel_variance(a)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 98, 10, 34, 14)
    panel_memoria(b, mem)
    S.fig_label(fig, "b", 74, 3)
    c = ax_mm(fig, 150, 8, 32, 36)
    panel_persistencia(c, mem)
    S.fig_label(fig, "c", 140, 3)
    d = ax_mm(fig, 26, 76, 30, 30)
    im = PO.panel_transitions(d)
    S.fig_label(fig, "d", 1, 68)
    if im is not None:
        cb = ax_mm(fig, 58, 78, 2.0, 22)
        cbar = fig.colorbar(im, cax=cb)
        cbar.set_ticks([-4, -2, 0])
        cbar.set_ticklabels(["0.01%", "1%", "100%"])
        cbar.ax.tick_params(labelsize=4.8, length=1.5)
        cbar.set_label("Annual transition rate", fontsize=5)
    e = ax_mm(fig, 108, 70, 26, 68)
    panel_queda_classe(e, q, curto, cols)
    S.fig_label(fig, "e", 70, 68)
    f = ax_mm(fig, 160, 70, 20, 60)
    panel_queda_fen(f, qj)
    S.fig_label(fig, "f", 138, 68)
    return S.save(fig, "fig5", periodo)
