"""Fig. 6 — A variação mês a mês é concentrada e mal prevista (narrativa B; D63, D67, D68; parecer R16).

a: captura ao sinalizar os setores de maior risco (acaso, média histórica, ensemble, teto de ruído, oráculo);
b: previsibilidade por escala: R² alcançado e R² máximo sem modelo (variância acima do ruído de Poisson),
   entre e dentro das unidades e só dentro (mês a mês);
c: onde mora a dinâmica mensal: parte do crime e do excesso de variância sobre o Poisson acumulada nos
   setores de maior contagem;
d: ΔCRPS de cada método contra o NB-GLM (bootstrap por distrito; Holm de ``prereg/selection_dev.json``, CRPS corrigido);
e: equidade: área sinalizada e crime registrado por quintil de renda do setor.

Saíram (R16): o contraste celular × letal (agora Extended Data Fig. 5g) e o quadro de confirmação (Tabela 1).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

import painel_previsao as PP
import painel_teste as PT
from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.viz import figdata as F
from cityomics.viz import style as S

ESCALAS = [("setor", "mes", "Tract ×\nmonth"), ("setor", "trimestre", "Tract ×\nquarter"), ("setor", "ano", "Tract ×\nyear"),
           ("distrito", "mes", "District ×\nmonth"), ("distrito", "trimestre", "District ×\nquarter"), ("distrito", "ano", "District ×\nyear")]


def panel_escala(ax, t: pl.DataFrame):
    x = np.arange(len(ESCALAS))
    for med, c, dx, lab in (("onde_e_quando", "#264653", -0.12, "Between and within units"),
                             ("quando", "#D1495B", 0.12, "Within units (month to month)")):
        mx, ob = [], []
        for e, tp, _ in ESCALAS:
            r = t.filter((pl.col("espaco") == e) & (pl.col("tempo") == tp) & (pl.col("medida") == med))
            mx.append(float(r["r2_max_sem_modelo"][0]) if r.height else np.nan)
            ob.append(float(r["r2_observado"][0]) if r.height else np.nan)
        for i in range(len(x)):
            if not np.isnan(mx[i]):
                ax.plot([x[i] + dx] * 2, [ob[i], mx[i]], color=c, lw=0.7, alpha=0.6)
        ax.scatter(x + dx, mx, s=14, facecolor="white", edgecolor=c, linewidth=0.8, zorder=3)
        ax.scatter(x + dx, ob, s=14, color=c, zorder=3, label=lab)
    ax.set_xticks(x)
    ax.set_xticklabels([lab for _, _, lab in ESCALAS], fontsize=4.6)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("R² (filled: ensemble; open: noise ceiling)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=5, handletextpad=0.1, borderaxespad=0.2,
              columnspacing=1.0)


def panel_concentracao(ax, d: pl.DataFrame, rep: dict):
    d = d.filter(pl.col("media_mensal") > 0).sort("media_mensal", descending=True)
    n = d.height
    xs = np.arange(1, n + 1) / n * 100
    crime = np.cumsum(d["media_mensal"].to_numpy()) / d["media_mensal"].sum() * 100
    exc = np.cumsum(d["excesso"].to_numpy()) / max(d["excesso"].sum(), 1e-12) * 100
    ax.plot(xs, exc, color="#D1495B", lw=1.1, label="Extra-Poisson monthly variance")
    ax.plot(xs, crime, color="#264653", lw=1.1, label="Phone crime")
    ax.plot(xs, xs, color="#D9D9D9", lw=0.6, label="Equal shares (no concentration)")
    ax.set_xscale("log")
    ax.set_xlim(0.05, 100)
    ax.set_ylim(0, 102)
    ax.axvline(1, color="#BDBDBD", lw=0.5, ls=(0, (2, 2)))
    ax.set_xlabel("Tracts, ranked by phone crime (cumulative %)")
    ax.set_ylabel("Cumulative share (%)")
    from matplotlib.ticker import FixedLocator, NullLocator

    ax.xaxis.set_major_locator(FixedLocator([0.1, 1, 10, 100]))
    ax.set_xticklabels(["0.1", "1", "10", "100"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.legend(loc="lower right", fontsize=4.6, handlelength=1.4)
    rob = json.loads((atlas_dir() / "fenotipo" / "robustez.json").read_text())["escala_do_excesso"]
    ax.set_title(f"Top 1% of tracts: {rob['parte_excesso_top1_observada'] * 100:.0f}% of extra-Poisson variance\n"
                 f"({rob['parte_excesso_top1_esperada_theta_comum'] * 100:.0f}% expected from scale alone)",
                 fontsize=4.8, loc="left", color=S.MUTED)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    tag = "dev" if periodo == "dev" else periodo
    fd = atlas_dir() / "fenotipo"
    t = pl.read_parquet(fd / "previsibilidade_escala.parquet")
    disp = pl.read_parquet(fd / "dispersao_setor.parquet")
    prev = json.loads((fd / "previsibilidade.json").read_text())

    fig = S.figure(S.DOUBLE, 140)
    a = ax_mm(fig, 14, 6, 40, 42)
    PP.panel_capture(a, F.capture_curves(tag))
    S.fig_label(fig, "a", 1, 2)
    b = ax_mm(fig, 72, 11, 54, 34)
    panel_escala(b, t)
    S.fig_label(fig, "b", 62, 2)
    c = ax_mm(fig, 142, 9, 36, 39)
    panel_concentracao(c, disp, prev)
    S.fig_label(fig, "c", 132, 2)
    d = ax_mm(fig, 40, 68, 40, 56)
    PP.panel_forest(d, F.forest(tag))
    S.fig_label(fig, "d", 1, 64)
    ev, mu, phi, dist = F.load_eval(tag)
    e = ax_mm(fig, 118, 70, 60, 40)
    PT.panel_equity(e, ev, mu)
    S.fig_label(fig, "e", 104, 64)
    return S.save(fig, "fig6", periodo)
