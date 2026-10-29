"""Fig. 3 — Fenótipo: que crime cada classe de célula expressa (narrativa B; D63–D65, D69).

a: taxa atribuída de roubo e furto de celular por classe (por km de frente ou de rua; estações por unidade),
   IC de bootstrap por distrito, nas mesmas linhas de b;
b: assinatura classe × fenótipo (15 fenótipos): tamanho = participação da classe no crime esperado do
   fenótipo; cor = log2 do enriquecimento contra a média dos fenótipos (a "matriz-assinatura");
c: validação pontual por fenótipo (Spearman entre a taxa atribuída e a observada ligando cada ponto ao
   segmento de rua e aos lotes lindeiros);
d: programas de crime (NMF, k = 4): carga de cada fenótipo;
e: uso dos programas por setor (mapas rasterizados, D60; cofre espacial em cinza);
f: Sankey grupo teórico → classe → roubo de celular (mantido por D47/D57).
"""

from __future__ import annotations

import json

import matplotlib.patches as mpatches
import numpy as np
import polars as pl

import painel_onde as PO
import rotulos as R
from common import ax_mm, check_periodo, row_swatches
from cityomics.atlas import guard
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.viz import maps as M
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S

PROG_CORES = ["#7FB3EE", "#F2A65A", "#9AD18B", "#E07A8C"]


def fen_ordem(prog: dict) -> list[str]:
    H = {p["programa"]: p["fenotipos"] for p in prog["programas"]}
    fen = list(next(iter(H.values())))
    dono = {f: max(H, key=lambda p: H[p][f]) for f in fen}
    return sorted(fen, key=lambda f: (list(H).index(dono[f]), -H[dono[f]][f]))


def panel_rates_rows(ax, lam: pl.DataFrame, rows: list[str], cols: dict):
    d = {r["classe"]: r for r in lam.iter_rows(named=True)}
    xmin = 1e-4  # abaixo disto a classe não é identificada: o intervalo vai até a borda e o ponto fica vazado
    for i, c in enumerate(rows):
        r = d.get(c)
        if r is None or r["lambda"] <= 0:
            continue
        lo, hi = max(r["lambda_ic_lo"], xmin), r["lambda_ic_hi"]
        mk = "D" if c.startswith("n_") else "o"
        cor = cols.get(c, "#888888")
        ax.plot([lo, hi], [i, i], color=cor, lw=1.0, clip_on=False)
        sub = r["lambda"] < xmin
        ax.scatter(max(r["lambda"], xmin), i, s=10, marker=mk, color="white" if sub else cor, zorder=3,
                   edgecolor=cor if sub else "white", linewidth=0.6 if sub else 0.3, clip_on=False)
    ax.set_xlim(xmin, 300)
    ax.set_xscale("log")
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("Phone crime per year,\nper km (diamonds: per station)", fontsize=5.0)
    ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)


def panel_signature(ax, m: pl.DataFrame, rows: list[str], fen: list[str]):
    d = m.filter(pl.col("classe").is_in(rows) & pl.col("fenotipo").is_in(fen))
    xi = {f: i for i, f in enumerate(fen)}
    yi = {c: i for i, c in enumerate(rows)}
    z = np.clip(d["log2_enriq"].to_numpy(), -2.5, 2.5)
    s = 1.0 + 130 * np.clip(d["participacao"].to_numpy(), 0, 0.35)
    sc = ax.scatter([xi[f] for f in d["fenotipo"]], [yi[c] for c in d["classe"]], s=s, c=z, cmap=P.cmap("vik"), vmin=-2.5, vmax=2.5,
                    edgecolors="#555555", linewidths=0.2)
    ax.set_xticks(range(len(fen)))
    ax.set_xticklabels([R.FEN_EN[f] for f in fen], rotation=55, ha="right", rotation_mode="anchor")
    ax.set_yticks([])
    ax.set_xlim(-0.6, len(fen) - 0.4)
    ax.set_ylim(len(rows) - 0.5, -0.5)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.tick_params(length=0)
    ax.grid(True, color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    return sc


def panel_row_labels(ax, rows: list[str], longo: dict, cols: dict):
    ax.set_ylim(len(rows) - 0.5, -0.5)
    ax.set_xlim(0, 1)
    ax.axis("off")
    for i, c in enumerate(rows):
        ax.add_patch(mpatches.Rectangle((0.92, i - 0.36), 0.08, 0.72, color=cols.get(c, "#888888"), clip_on=False))
        ax.text(0.88, i, longo.get(c, c), ha="right", va="center", fontsize=5.5)


def panel_validation_fen(ax, val: dict, fen: list[str]):
    y = np.arange(len(fen))
    for i, f in enumerate(fen):
        v = val.get(f, {})
        if v.get("spearman_lotes") is None:
            ax.text(0.02, i, f"coverage {v.get('cobertura', 0):.0%} (not tested)", va="center", fontsize=4.8, color=S.MUTED)
            continue
        ax.plot([v["spearman"], v["spearman_lotes"]], [i, i], color="#BDBDBD", lw=0.6, zorder=1)
        ax.scatter(v["spearman_lotes"], i, s=12, color="#264653", zorder=3)
        ax.scatter(v["spearman"], i, s=12, facecolor="white", edgecolor="#264653", linewidth=0.7, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels([R.FEN_EN[f] for f in fen])
    ax.set_ylim(len(fen) - 0.5, -0.5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Finer-scale check, Spearman ρ")
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    from matplotlib.lines import Line2D

    ax.legend([Line2D([], [], marker="o", ls="", color="#264653", ms=3), Line2D([], [], marker="o", ls="", mfc="white", mec="#264653", ms=3)],
              ["parcel types only", "all cell classes"], loc="center left", bbox_to_anchor=(0.0, 0.45), fontsize=4.8,
              handletextpad=0.2, borderaxespad=0.2)


def prog_nome(p: dict, curto: dict) -> str:
    return N.program_label(p, curto)


def panel_programs(ax, prog: dict, fen: list[str], curto: dict):
    ps = prog["programas"]
    H = np.array([[p["fenotipos"][f] for f in fen] for p in ps])
    cm = P.cmap("bilbao")
    lum = lambda c: 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]  # noqa: E731
    if lum(cm(0.0)) < lum(cm(1.0)):  # claro = zero, escuro = carga alta
        cm = cm.reversed()
    im = ax.imshow(H, cmap=cm, vmin=0, vmax=max(0.5, float(H.max())), aspect="auto")
    ax.set_yticks(range(len(ps)))
    # nome em três linhas ("Program k", classe 1, + classe 2): numa linha só invadia o painel c
    def wrap(p):
        num, rest = prog_nome(p, curto).split(" · ", 1)
        return num + "\n" + rest.replace(" + ", "\n+ ")
    ax.set_yticklabels([wrap(p) for p in ps], fontsize=5, linespacing=1.0)
    ax.set_xticks(range(len(fen)))
    ax.set_xticklabels([R.FEN_EN[f] for f in fen], rotation=55, ha="right", rotation_mode="anchor", fontsize=4.8)
    ax.tick_params(length=0)
    row_swatches(ax, [PROG_CORES[i % 4] for i in range(len(ps))], h=0.8)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    return im


def panel_program_map(ax, uso: pl.DataFrame, p: str, color: str, titulo: str):
    from matplotlib.colors import LinearSegmentedColormap

    v = dict(zip(uso["cd_setor"].to_list(), uso[p].to_list()))
    st = pl.read_parquet(atlas_dir() / f"setor_composicao_2025.parquet", columns=["cd_setor", "cd_dist"])
    cof = st.filter(pl.Series(~guard.explore_mask(st["cd_dist"].to_numpy())))["cd_setor"].to_list()
    vmax = float(np.nanpercentile(uso[p].to_numpy(), 97))
    v |= {c: -1.0 for c in cof}
    arr, bounds = M.setor_raster(v, res=60.0)
    cm = LinearSegmentedColormap.from_list("p", ["#15151B", color])
    cm.set_under("#2E2E36")
    cm.set_bad(S.DARK_BG)
    S.dark(ax)
    x0, y0, x1, y1 = bounds
    ax.imshow(np.ma.masked_invalid(arr), cmap=cm, vmin=0.0, vmax=vmax, extent=(x0, x1, y0, y1), origin="upper",
              interpolation="nearest", rasterized=True)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.text(0.03, 0.97, titulo, transform=ax.transAxes, color="white", fontsize=5.0, va="top")


def make(periodo: str = "dev"):
    check_periodo(periodo)
    fd = atlas_dir() / "fenotipo"
    m = pl.read_parquet(fd / "assinaturas.parquet")
    a_rep = json.loads((fd / "assinaturas.json").read_text())
    prog = json.loads((fd / "programas.json").read_text())
    uso = pl.read_parquet(fd / "programas_uso_setor.parquet")
    lam = pl.read_parquet(atlas_dir() / "atribuicao_celular_2025.parquet")
    fl = pl.read_parquet(atlas_dir() / "sankey_celular_2025.parquet")
    tipos, fam, key, longo, curto = R.classes()
    rows = R.ordem_linhas()
    cols = R.cores()
    fen = fen_ordem(prog)

    fig = S.figure(S.DOUBLE, 222)
    lab = ax_mm(fig, 2, 6, 40, 68)
    panel_row_labels(lab, rows, curto, cols)  # nomes curtos: os longos com qualificador não cabem
    a = ax_mm(fig, 44, 6, 26, 68)
    panel_rates_rows(a, lam, rows, cols)
    S.fig_label(fig, "a", 42, 1)
    b = ax_mm(fig, 76, 6, 104, 68)
    sc = panel_signature(b, m, rows, fen)
    S.fig_label(fig, "b", 72, 1)
    cb = ax_mm(fig, 80, 99, 22, 2.0)
    c1 = fig.colorbar(sc, cax=cb, orientation="horizontal")
    c1.set_label("log₂ enrichment vs mean crime type", fontsize=5.0)
    c1.ax.tick_params(labelsize=4.8, length=1.5)
    lg = ax_mm(fig, 112, 96, 66, 6)
    lg.axis("off")
    lg.text(0.0, 0.5, "Share of crime type", fontsize=5.0, va="center", transform=lg.transAxes)
    for i, f in enumerate((0.05, 0.15, 0.3)):
        x = 0.36 + i * 0.2
        lg.scatter([x], [0.5], s=1.0 + 130 * f, color="#BBBBBB", edgecolor="#555555", linewidth=0.2, transform=lg.transAxes, clip_on=False)
        lg.text(x + 0.04, 0.5, f"{int(f * 100)}%", fontsize=4.8, va="center", transform=lg.transAxes)

    c = ax_mm(fig, 32, 116, 38, 50)
    panel_validation_fen(c, a_rep["validacao_pontual"], fen)
    S.fig_label(fig, "c", 1, 112)
    d = ax_mm(fig, 124, 116, 58, 30)
    imd = panel_programs(d, prog, fen, curto)
    S.fig_label(fig, "d", 78, 112)
    cbd = ax_mm(fig, 84, 160, 18, 1.8)
    c2 = fig.colorbar(imd, cax=cbd, orientation="horizontal")
    c2.set_label("Program loading (d)", fontsize=5.0)
    c2.ax.tick_params(labelsize=5, length=1.5)

    for i, p in enumerate(prog["programas"]):
        ax = ax_mm(fig, 4 + i * 45, 178, 43, 40)
        panel_program_map(ax, uso, p["programa"], PROG_CORES[i % 4], N.program_title(p["programa"]))
        if i == 0:
            M.scalebar(ax, 10_000, color="white", loc=(0.55, 0.05))
    S.fig_label(fig, "e", 1, 174)
    return S.save(fig, "fig3", periodo)
