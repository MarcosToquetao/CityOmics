"""Extended Data (spec-figuras §3): tabelas e análises de apoio.

ED1: tabela completa do benchmark de 2025 (CRPS, log score, Brier, ECE, PAI, hit rate);
ED2: tabela multiverso da comunicação (D39/D40);
ED3: Knox entre famílias (razão observado/esperado), MISTy e Lee's L;
ED4: co-ocorrência por distância (metacélulas) e colocation quotient (baseline urbano);
ED5: cascata com sinal da decomposição do crime esperado (versão analítica do Sankey, D57).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import figdata as F
from cityomics.viz import palette as P
from cityomics.viz import style as S

FAM_EN = {"res_horizontal": "Low-rise res.", "res_vertical_medio": "High-rise res.", "res_vertical_alto": "High-standard res.",
          "comercio": "Commerce", "servicos": "Services", "industria": "Industry", "vazio": "Vacant", "favela": "Favela",
          "sem_cadastro": "Unrecorded"}


def table(ax, header: list[str], rows: list[list[str]], col_w: list[float], fontsize: float = 5.2, zebra: bool = True):
    ax.axis("off")
    n = len(rows) + 1
    x = np.concatenate([[0], np.cumsum(col_w)]) / sum(col_w)
    h = 1.0 / n
    for j, t in enumerate(header):
        ax.text(x[j] + 0.005, 1 - h / 2, t, fontsize=fontsize, fontweight="bold", va="center", transform=ax.transAxes)
    ax.plot([0, 1], [1 - h, 1 - h], color=S.INK, lw=0.5, transform=ax.transAxes)
    for i, r in enumerate(rows):
        y = 1 - (i + 1.5) * h
        if zebra and i % 2 == 0:
            ax.add_patch(__import__("matplotlib").patches.Rectangle((0, y - h / 2), 1, h, color="#F5F5F5", transform=ax.transAxes, lw=0))
        for j, t in enumerate(r):
            ax.text(x[j] + 0.005, y, t, fontsize=fontsize, va="center", transform=ax.transAxes)


def ed1(periodo):
    r = json.loads((processed_dir() / "modelo" / "resultados_benchmark_dev.json").read_text())["resultados"]
    fig = S.figure(S.DOUBLE, 80)
    ax = ax_mm(fig, 2, 3, 179, 74)
    rows = []
    for m, v in sorted(r.items(), key=lambda kv: kv[1]["crps"]):
        fam = P.MODELO_FAMILIA.get(m, "baseline")
        rows.append([F.NOMES_MODELO[m], fam.capitalize(), f"{v['crps']:.4f}", f"{v['logscore']:.4f}", f"{v['brier']:.4f}",
                     f"{v['ece']:.3f}", f"{v['pai1']:.1f}", f"{v['hit1'] * 100:.1f}", f"{v['pai5']:.2f}", f"{v['hit5'] * 100:.1f}"])
    table(ax, ["Model", "Family", "CRPS", "Log score", "Brier", "ECE", "PAI 1%", "Hit 1% (%)", "PAI 5%", "Hit 5% (%)"], rows,
          [3.2, 1.8, 1, 1, 1, 0.8, 0.9, 1, 0.9, 1])
    return S.save(fig, "ed1_benchmark", periodo)


def ed2(periodo):
    m = pl.read_parquet(atlas_dir() / "comunicacao" / "multiverso.parquet")
    fig = S.figure(S.DOUBLE, 60)
    ax = ax_mm(fig, 2, 3, 179, 54)
    fmt = lambda v, d=2: "—" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:.{d}f}" if isinstance(v, float) else str(v))  # noqa: E731
    rows = [[r["abordagem"], r["escala"], fmt(r["estatistica"]), fmt(r["ganho_fora_amostra_pct"]), fmt(r["estabilidade"]),
             fmt(r["pares_tipo_significativos"]), r["status"]] for r in m.iter_rows(named=True)]
    table(ax, ["Approach", "Scale", "Statistic", "Out-of-sample gain (%)", "Stability (ρ)", "Significant pairs", "Status"], rows,
          [3.2, 2.0, 3.2, 1.3, 1.0, 1.0, 2.4], fontsize=4.6)
    return S.save(fig, "ed2_multiverso", periodo)


def ed3(periodo):
    kx = pl.read_parquet(atlas_dir() / "comunicacao" / "knox_familias.parquet")
    ms = pl.read_parquet(atlas_dir() / "comunicacao" / "misty.parquet")
    le = pl.read_parquet(atlas_dir() / "comunicacao" / "lee.parquet")
    fams = sorted(set(kx["a"].to_list()))
    R = np.full((len(fams), len(fams)), np.nan)
    for r in kx.iter_rows(named=True):
        R[fams.index(r["a"]), fams.index(r["b"])] = r["razao"]
    fig = S.figure(S.DOUBLE, 64)
    a = ax_mm(fig, 22, 6, 46, 46)
    im = a.imshow(R, cmap=P.cmap("lajolla"), vmin=1.0, vmax=np.nanmax(R))
    a.set_xticks(range(len(fams)))
    a.set_xticklabels([FAM_EN.get(f, f) for f in fams], rotation=55, ha="right", rotation_mode="anchor", fontsize=4.8)
    a.set_yticks(range(len(fams)))
    a.set_yticklabels([FAM_EN.get(f, f) for f in fams], fontsize=4.8)
    a.set_xlabel("Later event near (B)")
    a.set_ylabel("Earlier event near (A)")
    for s in a.spines.values():
        s.set_visible(False)
    a.tick_params(length=0)
    cb = ax_mm(fig, 70, 10, 2.2, 30)
    c = fig.colorbar(im, cax=cb)
    c.set_label("Knox ratio (≤400 m, 1–14 days)", fontsize=5)
    c.ax.tick_params(labelsize=4.8, length=1.5)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 96, 8, 36, 36)
    d = ms.filter(pl.col("visao") != "combinada")
    names = {"intrinseca": "Intrinsic (own tract)", "justaposta": "Juxtaview (neighbours)", "para_espacial": "Paraview (1 km)"}
    b.barh(range(d.height), d["contribuicao"].to_numpy(), color=["#264653", "#2A9D8F", "#B99BF0"], height=0.6)
    b.set_yticks(range(d.height))
    b.set_yticklabels([names[v] for v in d["visao"]])
    b.invert_yaxis()
    b.set_xlabel("MISTy view contribution")
    r2 = float(ms.filter(pl.col("visao") == "combinada")["r2_sozinha"][0])
    b.set_title(f"Combined out-of-sample R² = {r2:.2f}", fontsize=5.5, loc="left", color=S.MUTED)
    S.fig_label(fig, "b", 76, 3)
    c2 = ax_mm(fig, 150, 8, 30, 36)
    lr_en = {"fluxo_trilhos": "Rail flow", "fluxo_onibus": "Bus flow", "vida_noturna": "Nightlife", "varejo": "Retail", "dinheiro": "Cash"}
    c2.barh(range(le.height), le["L_xy"].to_numpy(), color="#E8743B", height=0.6)
    c2.set_yticks(range(le.height))
    c2.set_yticklabels([lr_en.get(v, v) for v in le["ligante"]])
    c2.invert_yaxis()
    c2.axvline(0, color=S.INK, lw=0.5)
    c2.set_xlabel("Lee's L (ligand × theft rate)")
    S.fig_label(fig, "c", 136, 3)
    return S.save(fig, "ed3_knox_misty_lee", periodo)


def ed4(periodo):
    co = pl.read_parquet(atlas_dir() / "coocorrencia_metacelulas_2025.parquet")
    cq = pl.read_parquet(atlas_dir() / "colocation_quotient_2025.parquet")
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    en = dict(zip(perfil["nome"].to_list(), perfil["name_en"].to_list())) | {"Favela (FCU)": "Favelas (FCU)"}
    fam = dict(zip(perfil["nome"].to_list(), perfil["familia"].to_list())) | {"Favela (FCU)": "favela"}
    tipos = list(en)
    cols = P.type_colors(tipos, [fam[t] for t in tipos], [0.0] * len(tipos))
    fig = S.figure(S.DOUBLE, 70)
    a = ax_mm(fig, 14, 6, 60, 50)
    ref = co.filter(pl.col("a") == pl.col("b"))
    for t in ref["a"].unique().to_list():
        s = ref.filter(pl.col("a") == t).sort("raio_m")
        a.plot(s["raio_m"], s["razao"], color=cols.get(t, "#999999"), lw=0.9)
    a.set_xscale("log")
    a.axhline(1, color=S.INK, lw=0.5)
    a.set_xlabel("Distance (m)")
    a.set_ylabel("Self co-occurrence ratio\nP(same type within r) / P(type)")
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 100, 6, 50, 50)
    order = [t for t in tipos if t in set(cq["a"].to_list())]
    Q = np.zeros((len(order), len(order)))
    for r in cq.iter_rows(named=True):
        if r["a"] in order and r["b"] in order:
            Q[order.index(r["a"]), order.index(r["b"])] = r["clq"]
    im = b.imshow(np.log2(np.clip(Q, 1 / 16, 16)), cmap=P.cmap("vik"), vmin=-4, vmax=4)
    b.set_xticks(range(len(order)))
    b.set_xticklabels([en[t] for t in order], rotation=60, ha="right", rotation_mode="anchor", fontsize=4.4)
    b.set_yticks(range(len(order)))
    b.set_yticklabels([en[t] for t in order], fontsize=4.4)
    b.tick_params(length=0)
    for s in b.spines.values():
        s.set_visible(False)
    cb = ax_mm(fig, 152, 12, 2.2, 30)
    c = fig.colorbar(im, cax=cb)
    c.set_label("log₂ colocation quotient", fontsize=5)
    c.ax.tick_params(labelsize=4.8, length=1.5)
    S.fig_label(fig, "b", 84, 3)
    return S.save(fig, "ed4_coocorrencia_clq", periodo)


def ed5(periodo):
    fl = pl.read_parquet(atlas_dir() / "sankey_celular_2025.parquet")
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    fam = dict(zip(perfil["nome"].to_list(), perfil["familia"].to_list())) | {"Favela (FCU)": "favela", "Sem cadastro": "sem_cadastro"}
    f = fl.with_columns(pl.col("classe").map_elements(lambda c: "Streets" if c.startswith("rua_") else ("Stations" if c.startswith("n_")
                                                       else FAM_EN.get(fam.get(c, "sem_cadastro"), c)), return_dtype=pl.String).alias("g"))
    agg = f.group_by("origem").agg(pl.col("valor").sum())
    tot = agg["valor"].sum()
    order = ["identidade", "atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario"]
    vals = [float(agg.filter(pl.col("origem") == o)["valor"].sum()) / tot * 100 for o in order]
    fig = S.figure(S.SINGLE, 60)
    ax = ax_mm(fig, 30, 6, 52, 46)
    left = 0.0
    for i, (o, v) in enumerate(zip(order, vals)):
        ax.barh(i, v, left=left if v >= 0 else left + v, color=P.GRUPOS[o], height=0.6)
        ax.text((left + v) + (1 if v >= 0 else -1), i, f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=5)
        left += v
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([P.NOMES_GRUPOS_EN[o] for o in order])
    ax.invert_yaxis()
    ax.set_xlabel("Contribution to expected 2025 thefts (%)")
    ax.axvline(0, color=S.INK, lw=0.5)
    return S.save(fig, "ed5_cascata", periodo)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    out = None
    for fn in (ed1, ed2, ed3, ed4, ed5):
        try:
            out = fn(periodo)
        except FileNotFoundError as e:
            print(f"{fn.__name__}: dados ausentes ({e})")
    return out
