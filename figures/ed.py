"""Extended Data da narrativa B (spec-figuras §3; D70): tabelas e análises de apoio.

ED1: tabela completa do benchmark de 2025 (CRPS, log score, Brier, ECE, PAI, hit rate);
ED2: auditoria de equivalências (módulo ômico × análogo urbano × resultado × quem vence);
ED3: comunicação exploratória (círculo emissor → receptor, pares L–R, campo do sinal) e covariáveis por domínio;
ED4: tabela multiverso da comunicação (D39/D40);
ED5: Knox entre famílias (razão observado/esperado), MISTy e Lee's L;
ED6: co-ocorrência por distância, colocation quotient e composição dos distritos;
ED7: teoria: SHAP por grupo teórico e cascata com sinal da decomposição do crime esperado (D57);
ED8: fora da amostra em detalhe: finalistas, mês a mês, acerto/erro no top 5%, habilidade por domínio,
     calibração e correlação "onde × quando";
ED9: perturbação natural: evento-estudo de aberturas e fechamentos (nulo informativo);
ED10: painel de fenótipos: contagens e cobertura, escolha do k do NMF, fator multidão por classe e
      renovação do tecido × variabilidade mensal.

(Os nomes acima são os das funções; a numeração final dos Extended Data está em ``make``. A nova
ED Fig. 10, de robustez, é ``ed_b.ed10_robustez``.)
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from common import ax_mm, check_periodo, place_labels
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S

FAM_EN = N.FAMILY_EN


# famílias como nos Methods do manuscrito (KDE é baseline; GWR e painel espacial, econometria)
FAMILIA_EN = N.MODEL_FAMILY_EN | {"kde": "Baseline", "gwr_distrito": "Econometrics", "painel_espacial": "Econometrics"}


def table(ax, header: list[str], rows: list[list[str]], col_w: list[float], fontsize: float = 5.2, zebra: bool = True):
    """Tabela simples; o texto de cada célula é quebrado em linhas para caber na largura da coluna."""
    import textwrap

    ax.axis("off")
    n = len(rows) + 1
    x = np.concatenate([[0], np.cumsum(col_w)]) / sum(col_w)
    h = 1.0 / n
    w_mm = ax.get_position().width * ax.figure.get_size_inches()[0] / S.MM
    char_mm = 0.52 * fontsize * 25.4 / 72  # largura média de um caractere (Arial/Liberation)

    def fit(t, j, bold=False):
        cap = max(int((x[j + 1] - x[j]) * w_mm / (char_mm * (1.08 if bold else 1.0))) - 1, 4)
        return "\n".join(textwrap.fill(part, cap, break_long_words=False, break_on_hyphens=False) for part in str(t).split("\n"))

    for j, t in enumerate(header):
        ax.text(x[j] + 0.005, 1 - h / 2, fit(t, j, True), fontsize=fontsize, fontweight="bold", va="center",
                transform=ax.transAxes, linespacing=1.1)
    ax.plot([0, 1], [1 - h, 1 - h], color=S.INK, lw=0.5, transform=ax.transAxes)
    for i, r in enumerate(rows):
        y = 1 - (i + 1.5) * h
        if zebra and i % 2 == 0:
            ax.add_patch(__import__("matplotlib").patches.Rectangle((0, y - h / 2), 1, h, color="#F5F5F5", transform=ax.transAxes, lw=0))
        for j, t in enumerate(r):
            ax.text(x[j] + 0.005, y, fit(t, j), fontsize=fontsize, va="center", transform=ax.transAxes, linespacing=1.1)


def ed1(periodo):
    r = json.loads((processed_dir() / "modelo" / "resultados_benchmark_dev.json").read_text())["resultados"]
    fig = S.figure(S.DOUBLE, 80)
    ax = ax_mm(fig, 2, 3, 179, 74)
    rows = []
    for m, v in sorted(r.items(), key=lambda kv: kv[1]["crps"]):
        fam = FAMILIA_EN.get(m, FAMILIA_EN.get(P.MODELO_FAMILIA.get(m, "baseline"), "Baseline"))
        rows.append([N.MODEL_EN.get(m, m), fam, f"{v['crps']:.4f}", f"{v['logscore']:.4f}", f"{v['brier']:.4f}",
                     f"{v['ece']:.3f}", f"{v['pai1']:.1f}", f"{v['hit1'] * 100:.1f}", f"{v['pai5']:.2f}", f"{v['hit5'] * 100:.1f}"])
    table(ax, ["Model", "Field of origin", "CRPS", "Log score", "Brier score", "Calibration error (ECE)", "PAI, 1% of area",
               "Captured, 1% of area (%)", "PAI, 5% of area", "Captured, 5% of area (%)"], rows,
          [2.9, 1.6, 0.75, 0.8, 0.85, 1.5, 1.1, 1.6, 1.1, 1.6], fontsize=5.0)
    return S.save(fig, "ed5_benchmark", periodo)


def ed4(periodo):
    m = pl.read_parquet(atlas_dir() / "comunicacao" / "multiverso.parquet")
    fig = S.figure(S.DOUBLE, 60)
    ax = ax_mm(fig, 2, 3, 179, 54)
    fmt = lambda v, d=2: "—" if v is None or (isinstance(v, float) and np.isnan(v)) else (f"{v:.{d}f}".replace("-", "−") if isinstance(v, float) else str(v))  # noqa: E731
    tr = {"ligante–receptor (COMMOT + NicheNet)": "Ligand–receptor (COMMOT + NicheNet)",
          "excitação cruzada (Knox, consistente com Hawkes)": "Cross-excitation (Knox, Hawkes-consistent)",
          "MISTy (visões intrínseca/justaposta/para-espacial)": "MISTy (intrinsic, juxtaposed and para-spatial views)",
          "NCEM / SLX (tipo receptor × vizinhança)": "NCEM / SLX (receiver type × neighbourhood)",
          "Lee's L bivariado (ligante × crime)": "Bivariate Lee's L (generator × phone crime)",
          "fluxos OD 2017 × gravitacional": "Origin–destination flows (2017 survey) vs gravity model", "ablação de arestas do GNN": "GNN edge ablation",
          "setor, ℓ = 250–1000 m": "tract, ℓ = 250–1,000 m", "evento, 400 m × 14 dias": "event, 400 m × 14 days", "setor": "tract",
          "setor (contiguidade)": "tract (contiguity)", "zona OD": "survey zone", "rodado": "run",
          "não rodado: base OD 2017 não disponível localmente": "not run: 2017 survey data not available",
          "não rodado: OD 2017 usada só para a população presente (P5); fluxos × gravitacional pendentes":
              "not run: 2017 survey used only for the ambient population; flows vs gravity pending",
          "não rodado nesta versão": "not run in this version"}
    words = {"melhor par": "best pair", "razão média": "mean ratio", "máx": "max", "intrinseca": "intrinsic", "justaposta": "juxtaposed",
             "para_espacial": "para-spatial", "fluxo_trilhos": "rail passengers", "fluxo_onibus": "bus passengers",
             "vida_noturna": "nightlife", "varejo": "retail", "dinheiro": "cash", "alvos_a_pe": "pedestrian targets", "→": " → "}

    def en(s):
        if s is None:
            return "—"
        s = tr.get(s, s)
        for k, v in words.items():
            s = s.replace(k, v)
        return s
    def gain(v):  # ganho < −100%: o modelo com interações diverge fora da amostra (deviance mais que dobra)
        return "< −100 (fit diverged)" if isinstance(v, float) and np.isfinite(v) and v < -100 else fmt(v)
    rows = [[en(r["abordagem"]), en(r["escala"]), en(r["estatistica"]), gain(r["ganho_fora_amostra_pct"]), fmt(r["estabilidade"]),
             fmt(r["pares_tipo_significativos"]), en(r["status"])] for r in m.iter_rows(named=True)]
    table(ax, ["Approach", "Scale", "Statistic", "Out-of-sample\ngain (%)", "Stability (ρ)", "Significant\npairs", "Status"], rows,
          [2.9, 1.7, 3.4, 1.25, 0.9, 0.95, 3.7], fontsize=5.0)
    return S.save(fig, "ed9_multiverso", periodo)


def ed5(periodo):
    kx = pl.read_parquet(atlas_dir() / "comunicacao" / "knox_familias.parquet")
    ms = pl.read_parquet(atlas_dir() / "comunicacao" / "misty.parquet")
    le = pl.read_parquet(atlas_dir() / "comunicacao" / "lee.parquet")
    fams = sorted(set(kx["a"].to_list()))
    R = np.full((len(fams), len(fams)), np.nan)
    for r in kx.iter_rows(named=True):
        R[fams.index(r["a"]), fams.index(r["b"])] = r["razao"]
    fig = S.figure(S.DOUBLE, 72)
    a = ax_mm(fig, 36, 6, 40, 40)
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
    cb = ax_mm(fig, 78, 10, 2.2, 30)
    c = fig.colorbar(im, cax=cb)
    c.set_label("Knox ratio\n(≤400 m, 1–14 days)", fontsize=5)
    c.ax.tick_params(labelsize=4.8, length=1.5)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 126, 8, 22, 36)
    d = ms.filter(pl.col("visao") != "combinada")
    names = N.MISTY_EN
    b.barh(range(d.height), d["contribuicao"].to_numpy(), color=["#264653", "#2A9D8F", "#B99BF0"], height=0.6)
    b.set_yticks(range(d.height))
    b.set_yticklabels([names[v] for v in d["visao"]])
    b.invert_yaxis()
    b.set_xlabel("MISTy view contribution")
    r2 = float(ms.filter(pl.col("visao") == "combinada")["r2_sozinha"][0])
    b.set_title(f"Combined R² = {r2:.2f}", fontsize=5.5, loc="left", color=S.MUTED)
    S.fig_label(fig, "b", 94, 3)
    c2 = ax_mm(fig, 168, 8, 13, 36)
    lr_en = N.LR_EN
    c2.barh(range(le.height), le["L_xy"].to_numpy(), color="#E8743B", height=0.6)
    c2.set_yticks(range(le.height))
    c2.set_yticklabels([lr_en.get(v, v) for v in le["ligante"]])
    c2.invert_yaxis()
    c2.axvline(0, color=S.INK, lw=0.5)
    c2.set_xlabel("Lee's L with\nphone crime rate")
    S.fig_label(fig, "c", 152, 3)
    return S.save(fig, "ed10_knox_misty_lee", periodo)


def ed6(periodo):
    co = pl.read_parquet(atlas_dir() / "coocorrencia_metacelulas_2025.parquet")
    cq = pl.read_parquet(atlas_dir() / "colocation_quotient_2025.parquet")
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    _, curto = N.class_labels(perfil)
    tipos = perfil["nome"].to_list() + ["Favela (FCU)"]
    fam = perfil["familia"].to_list() + ["favela"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0]
    cols = P.type_colors(tipos, fam, key)
    ordem = P.ordered_types(tipos, fam, key)
    fig = S.figure(S.DOUBLE, 128)
    a = ax_mm(fig, 14, 6, 60, 50)
    ref = co.filter(pl.col("a") == pl.col("b"))
    ends = []
    for t in ref["a"].unique().to_list():
        s = ref.filter(pl.col("a") == t).sort("raio_m")
        a.plot(s["raio_m"], s["razao"], color=cols.get(t, "#999999"), lw=0.9)
        ends.append((float(s["raio_m"][0]), float(s["razao"][0]), t))
    a.set_xscale("log")
    a.axhline(1, color=S.INK, lw=0.5)
    a.set_xlabel("Distance (m)")
    a.set_ylabel("Self co-occurrence ratio\nP(same type within r) / P(type)")
    top = sorted(ends, key=lambda e: -e[1])[:5]  # rótulos das cinco curvas mais altas, na menor distância
    place_labels(a, [e[0] for e in top], [e[1] for e in top], [curto.get(e[2], e[2]) for e in top], fontsize=5, point_pt=1.0)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 116, 6, 46, 46)
    order = [t for t in ordem if t in set(cq["a"].to_list())]
    Q = np.zeros((len(order), len(order)))
    for r in cq.iter_rows(named=True):
        if r["a"] in order and r["b"] in order:
            Q[order.index(r["a"]), order.index(r["b"])] = r["clq"]
    im = b.imshow(np.log2(np.clip(Q, 1 / 16, 16)), cmap=P.cmap("vik"), vmin=-4, vmax=4)
    b.set_xticks(range(len(order)))
    b.set_xticklabels([curto.get(t, t) for t in order], rotation=60, ha="right", rotation_mode="anchor", fontsize=5)
    b.set_yticks(range(len(order)))
    b.set_yticklabels([curto.get(t, t) for t in order], fontsize=5)
    b.tick_params(length=0)
    for s in b.spines.values():
        s.set_visible(False)
    cb = ax_mm(fig, 165, 10, 2.2, 30)
    c = fig.colorbar(im, cax=cb)
    c.set_label("log₂ colocation quotient", fontsize=5)
    c.ax.tick_params(labelsize=5, length=1.5)
    S.fig_label(fig, "b", 86, 3)
    from fig2 import panel_districts, types_meta

    perfil, tipos2, fam2, key2, _ = types_meta()
    cols2 = P.type_colors(tipos2, fam2, key2)
    order2 = P.ordered_types(tipos2, fam2, key2)
    c3 = ax_mm(fig, 14, 98, 166, 24)
    panel_districts(c3, {**cols2, "Favela (FCU)": P.FAMILIAS["favela"][0]}, order2 + ["Favela (FCU)"])
    S.fig_label(fig, "c", 1, 94)
    return S.save(fig, "ed1_coocorrencia_composicao", periodo)


def panel_cascata(ax):
    fl = pl.read_parquet(atlas_dir() / "sankey_celular_2025.parquet")
    agg = fl.group_by("origem").agg(pl.col("valor").sum())
    tot = agg["valor"].sum()
    order = ["identidade", "atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario"]
    vals = [float(agg.filter(pl.col("origem") == o)["valor"].sum()) / tot * 100 for o in order]
    left = 0.0
    for i, (o, v) in enumerate(zip(order, vals)):
        ax.barh(i, v, left=left if v >= 0 else left + v, color=P.GRUPOS[o], height=0.6)
        ax.text((left + v) + (1 if v >= 0 else -1), i, f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=5)
        left += v
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([N.GROUP_EN[o] for o in order])
    ax.invert_yaxis()
    ax.set_xlabel("Contribution to expected 2025 thefts (%)")
    ax.axvline(0, color=S.INK, lw=0.5)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    from ed_b import ed2, ed3, ed8, ed9, ed10, ed10_robustez

    # ordem de primeira citação no manuscrito (paper/manuscript_src.md); a figura de teoria (ed7) saiu.
    # função → saída (revisão final, 2026-10-27: renumerado pela ordem de citação; a robustez passou a ED2):
    # ed6 → ed1_coocorrencia_composicao, ed10_robustez → ed2_robustez, ed10 → ed3_painel, ed9 → ed4_perturbacao,
    # ed1 → ed5_benchmark, ed8 → ed6_fora_da_amostra, ed2 → ed7_equivalencias, ed3 → ed8_comunicacao,
    # ed4 → ed9_multiverso, ed5 → ed10_knox_misty_lee
    out = None
    for fn in (ed6, ed10_robustez, ed10, ed9, ed1, ed8, ed2, ed3, ed4, ed5):
        try:
            out = fn(periodo)
        except FileNotFoundError as e:
            print(f"{fn.__name__}: dados ausentes ({e})")
    return out
