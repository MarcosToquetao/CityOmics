"""Painéis fora da amostra (antiga Fig. 6; narrativa B: equidade na Fig. 6; o resto no ED8).

Fig. 6 — Fora da amostra e equidade (parametrizada: 2025 em dev; 2026 depois do FREEZE, D52).

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
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S

FINAL = ["glm", "hawkes", "lgbm_completo", "gnn", "ensemble"]
COR = {"glm": "#9E9E9E", "hawkes": "#D1495B", "lgbm_completo": "#E9C46A", "gnn": "#F4A261", "ensemble": "#264653"}


def _setup(tag):
    ev, mu, phi, dist = F.load_eval(tag)
    y = ev["y"].to_numpy().astype(float)
    crps = {m: scores.crps_nb(y, mu[m], phi[m]) for m in FINAL}
    return ev, mu, phi, dist, y, crps


def panel_test(ax, ev, mu, phi, y, crps):
    """CRPS dos finalistas em 2025 (pontos; o eixo não começa em zero, por isso não são barras). 2026 segue selado."""
    br = {m: float(np.mean((scores.prob_ge1(mu[m], phi[m]) - (y >= 0.5)) ** 2)) for m in FINAL}
    x = np.arange(len(FINAL))
    v = [float(np.mean(crps[m])) for m in FINAL]
    ax.scatter(x, v, s=22, color=[COR[m] for m in FINAL], zorder=3, edgecolor="white", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([N.MODEL_EN.get(m, m) for m in FINAL], rotation=35, ha="right", rotation_mode="anchor", fontsize=5)
    span = max(v) - min(v)
    ax.set_ylim(min(v) - 0.25 * span, max(v) + 0.35 * span)
    ax.set_xlim(-0.6, len(FINAL) - 0.4)
    ax.set_ylabel("CRPS, 2025 (lower is better)")
    for i, m in enumerate(FINAL):
        ax.text(i, v[i] + 0.08 * span, f"Brier\n{br[m]:.3f}", ha="center", va="bottom", fontsize=5, color=S.MUTED, linespacing=1.0)
    ax.grid(True, axis="y", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)


def panel_monthly(ax, ev, crps):
    mes = ev["mes"].to_numpy()
    months = sorted(np.unique(mes))
    for m in FINAL[1:]:
        sk = [1 - np.mean(crps[m][mes == k]) / np.mean(crps["glm"][mes == k]) for k in months]
        ax.plot(range(len(months)), np.array(sk) * 100, color=COR[m], lw=1.1 if m == "ensemble" else 0.8, marker="o", ms=1.6,
                label=N.MODEL_EN[m])
    ax.axhline(0, color=S.INK, lw=0.5)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([k[5:] for k in months])
    ax.set_xlabel("Month of 2025")
    ax.set_ylabel("CRPS skill vs negative\nbinomial GLM (%)")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2, fontsize=5, handlelength=1.2, columnspacing=0.8,
              borderaxespad=0.2)


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
    ax.set_xlabel("")
    ax.set_ylabel("")
    hit = (flag & real).sum() / max(real.sum(), 1)
    for i, (c, t) in enumerate((("#F5C451", "Flagged and in observed top 5%"), ("#5B9BD5", "Flagged only"), ("#D1495B", "Missed (observed top 5%)"))):
        ax.add_patch(__import__("matplotlib").patches.Rectangle((0.02, -0.06 - i * 0.05), 0.05, 0.03, color=c, transform=ax.transAxes, clip_on=False))
        ax.text(0.09, -0.045 - i * 0.05, t, transform=ax.transAxes, fontsize=4.8, va="center", color=S.INK)
    ax.text(0.02, -0.22, f"{hit * 100:.0f}% of observed top-5% tracts flagged (annual 2025)", transform=ax.transAxes, fontsize=4.8, color=S.INK)


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
    from painel_arquitetura import DOM_COLORS

    y = np.arange(len(rows))
    ax.barh(y, [r[1] * 100 for r in rows], color=[DOM_COLORS[r[0] % len(DOM_COLORS)] for r in rows], height=0.65)
    ax.set_yticks(y)
    dl = N.domain_labels(short=True)
    ax.set_yticklabels([dl[r[0]].replace(" + ", "\n+ ") for r in rows], fontsize=5, linespacing=1.0)
    ax.axvline(0, color=S.INK, lw=0.5)
    ax.set_xlabel("Ensemble CRPS skill vs\nnegative binomial GLM (%)")
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
    ax.bar(x + 0.18, share_crime, 0.34, color="#BDBDBD", label="Recorded phone crime")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{g}\n×{c:.2f}" for g, c in zip(qs, calib)])
    ax.set_ylabel("Share (%)")
    ax.set_xlabel("Tract income quintile (Q1, lowest)\n× predicted ÷ recorded phone crime")
    ax.legend(loc="upper left", fontsize=4.8, handlelength=1.0)


def panel_prospective(ax):
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 1)
    for i, m in enumerate(["Nov 26", "Dec 26", "Jan 27", "Feb 27", "Mar 27"]):
        ax.add_patch(__import__("matplotlib").patches.Rectangle((i + 0.1, 0.25), 0.8, 0.5, fill=False, edgecolor="#BDBDBD", hatch="//////", lw=0.4))
        ax.text(i + 0.5, 0.15, m, ha="center", fontsize=4.8, color=S.MUTED)
    ax.text(2.5, 0.85, "Prospective window: forecasts frozen, outcomes pending", ha="center", fontsize=5, color=S.MUTED)
    ax.axis("off")


