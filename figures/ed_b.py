"""Extended Data novos ou recompostos na narrativa B (ED2, ED3, ED7–ED10; D70). Chamados por ``ed.make``."""

from __future__ import annotations

import json

import numpy as np
import polars as pl

import painel_arquitetura as PA
import painel_onde as PO
import painel_previsao as PP
import painel_teste as PT
import rotulos as R
from common import ax_mm
from ed import panel_cascata, table
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import processed_dir
from cityomics.viz import figdata as F
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S
from cityomics.viz.chord import circle


VARIANTE_OD = "pe_bici"  # OD 2023: pessoas a pé e de bicicleta na rua (G_od2023 §4)


def _j(p):
    return json.loads(p.read_text()) if p.exists() else {}


# --- ED2: auditoria de equivalências -------------------------------------------------------------

def ed2(periodo):
    from scipy.stats import spearmanr

    a = atlas_dir()
    tip, att, var, fate = _j(a / "tipagem_2025.json"), _j(a / "atribuicao_celular_2025.json"), _j(a / "variancia_2025.json"), _j(a / "destino.json")
    ass, rel, mem = _j(a / "fenotipo" / "assinaturas.json"), _j(a / "fenotipo" / "relogio.json"), _j(a / "fenotipo" / "memoria.json")
    qd, ev = _j(a / "fenotipo" / "queda.json"), _j(a / "perturbacao" / "evento_estudo.json")
    pres = _j(a / "presenca_2023" / "presenca_2023.json").get("2023", {}).get("pe_bici", {})
    sel = _j(processed_dir().parents[1] / "prereg" / "selection_dev.json")
    bench = _j(processed_dir() / "modelo" / "resultados_benchmark_dev.json").get("resultados", {})
    cq = pl.read_parquet(a / "colocation_quotient_2025.parquet").join(pl.read_parquet(a / "nhood_enrichment_2025.parquet"), on=["a", "b"])
    rho_clq = float(spearmanr(cq["clq"], cq["z"]).statistic)
    ms = pl.read_parquet(a / "comunicacao" / "misty.parquet")
    intr = float(ms.filter(pl.col("visao") == "intrinseca")["contribuicao"][0])
    mv = pl.read_parquet(a / "comunicacao" / "multiverso.parquet")

    def ganho(prefixo):
        r = mv.filter(pl.col("abordagem").str.starts_with(prefixo))
        return float(r["ganho_fora_amostra_pct"][0]) if r.height and r["ganho_fora_amostra_pct"][0] is not None else float("nan")
    lr, ncem = ganho("ligante"), ganho("NCEM")
    ics = [(v["ic_efeito"][0] / v["base"] * 100, v["ic_efeito"][1] / v["base"] * 100) for v in ev.values()
           if isinstance(v, dict) and v.get("ic_efeito") and v.get("base")]
    lo, hi = (min(a for a, _ in ics), max(b for _, b in ics)) if ics else (0, 0)
    stab = tip.get("estabilidade", {}).get(str(tip.get("resolucao", "0.02")), tip.get("estabilidade", {}).get("0.02", {})).get("ari_medio", float("nan"))
    h1a = sel.get("h1a", {})
    pct = abs(h1a.get("diff", float("nan"))) / bench.get("glm", {}).get("crps", float("nan")) * 100
    sgn = lambda v: f"{v:+.2f}".replace("-", "−")  # noqa: E731
    rows = [
        ["Typing", "Leiden on parcel attributes", "Geodemographic k-means (OAC style)",
         f"subsample agreement (ARI) {stab:.2f}; agreement with k-means {tip.get('ari_kmeans_vs_leiden', float('nan')):.2f}; "
         f"out-of-sample R², types {var.get('r2_tipos', 0):.2f} vs attributes {var.get('r2_genes_sem_tipagem', 0):.2f}",
         "Attributes predict; types interpret"],
        ["Attribution", "Cell-type profiles from known composition (csSAM)", "Poisson ecological regression (Goodman)",
         f"deviance explained {att.get('d2_composicao', 0):.2f}; finer-scale check ρ = {att.get('spearman_validacao_pontual', 0):.2f}",
         "Same model; omics adds the workflow"],
        ["Crime-type panel", "Reference profiles; NMF programs", "Location quotient (tract only)",
         f"{len(ass.get('classes_distintas_no_topo', []))} distinct top classes; finer-scale ρ = {ass.get('gate_G1', {}).get('validacao_mediana_lotes', 0):.2f}",
         "Omics (which crime, by cell class)"],
        ["Niches", "Neighbourhood enrichment, restricted null", "Colocation quotient", f"Spearman ρ between the two = {rho_clq:.2f}",
         "Tie; restricted null is the gain"],
        ["Domains", "Smoothed composition + clustering", "Regionalization (SKATER, max-p)",
         f"out-of-sample R², tissue {var.get('r2_tecido', 0):.2f} vs types {var.get('r2_tipos', 0):.2f}", "Marginal"],
        ["Clock", "Tissue-specific daily rhythms", "Time-specific crime pattern analysis",
         f"phone-theft contrast P = {rel.get('celular_furto', {}).get('2025', {}).get('p', float('nan')):.3f}; "
         f"between-year r = {rel.get('celular_furto', {}).get('replica_r', float('nan')):.2f}", "Omics (all classes at once)"],
        ["Library size", "Normalization by sequencing depth", "Ambient population (2023 travel survey)",
         f"rank per km vs per pedestrian ρ = {pres.get('spearman_km_vs_pedestre', float('nan')):.2f} (robbery), "
         f"{pres.get('spearman_furto_km_vs_pedestre', float('nan')):.2f} (theft)", "Both (weak check)"],
        ["Change", "Rates by condition, fixed composition", "Kitagawa rate–composition decomposition",
         f"2022→2025 ratio {qd.get('celular', {}).get('r_total', float('nan')):.2f}; top-3 concentration {sgn(qd.get('celular', {}).get('concentracao_top3', float('nan')))}",
         "Same decomposition"],
        ["Persistent effect", "Cell state beyond type", "Place heterogeneity (trajectories)",
         f"persistent effect {mem.get('partes', {}).get('memoria_estavel', 0) * 100:.0f}% vs composition "
         f"{mem.get('partes', {}).get('tecido', 0) * 100:.0f}% of variance; r at 3 years {mem.get('persistencia_residuo', {}).get('3', float('nan')):.2f}",
         "Descriptive"],
        ["Perturbation", "In-situ perturbation (Perturb-map)", "Staggered difference-in-differences",
         (f"null; effects outside {lo:.0f}% to +{hi:.0f}% excluded".replace("-", "−") if ics else "—"), "Null"],
        ["Communication", "Ligand–receptor (COMMOT, NicheNet)", "Lee's L, spatial lag",
         f"best pair {sgn(lr)}% out-of-sample; all generators positive in Lee's L", "Urban analogue (simpler)"],
        ["Context", "MISTy views", "Spatial lag", f"intrinsic view {intr:.2f}", "Tie"],
        ["Interactions", "NCEM / SLX pairs", "Additive SLX",
         ("pairs make the out-of-sample fit diverge (deviance more than doubles)" if ncem < -100
          else f"pairs change out-of-sample fit by {sgn(ncem)}%"), "Urban analogue"],
        ["Fate", "Type transitions", "Transition matrix", f"permanence {fate.get('permanencia_media', 0) * 100:.1f}% per year", "Descriptive"],
        ["Forecast", "GNN, Hawkes, Chronos, BYM2", "Negative binomial GLM, historical mean",
         f"best CRPS difference {sgn(h1a.get('diff', float('nan')))} ({pct:.0f}% lower)", "Small gain over baselines"],
    ]
    fig = S.figure(S.DOUBLE, 112)
    ax = ax_mm(fig, 2, 3, 179, 106)
    table(ax, ["Module", "Omics method", "Urban analogue", "Result (development)", "Verdict"], rows, [1.5, 3.0, 2.8, 5.2, 2.6], fontsize=5.0)
    return S.save(fig, "ed7_equivalencias", periodo)


# --- ED3: comunicação exploratória ---------------------------------------------------------------

def ed3(periodo):
    tipos, fam, key, en, n = PA.meta()
    cols = P.type_colors(tipos, fam, key)
    lt = pl.read_parquet(atlas_dir() / "comunicacao" / "lr_tipos.parquet")
    act = pl.read_parquet(atlas_dir() / "comunicacao" / "lr_atividade.parquet")
    mk = pl.read_parquet(atlas_dir() / "dominio_marcadores_2025.parquet")
    best = act.sort("ganho_pct", descending=True).row(0, named=True)
    fig = S.figure(S.DOUBLE, 162)
    d = ax_mm(fig, 30, 12, 40, 40)
    circle(d, tipos, np.array([n.get(t, 2000) for t in tipos], dtype=float), PA.lr_matrix(lt, tipos), cols, labels=en, top=20)
    S.fig_label(fig, "a", 1, 3)
    e = ax_mm(fig, 122, 8, 36, 40)
    sc = PA.panel_bubbles(e, lt, en)
    S.fig_label(fig, "b", 84, 3)
    cb = ax_mm(fig, 164, 10, 2.0, 22)
    c3 = fig.colorbar(sc, cax=cb)
    c3.set_label("Strength relative\nto pair maximum", fontsize=5)
    c3.ax.tick_params(labelsize=5, length=1.5)
    f = ax_mm(fig, 8, 94, 40, 62)
    PA.panel_field(f, best)
    S.fig_label(fig, "c", 1, 90)
    g = ax_mm(fig, 108, 100, 56, 26)
    im = PA.panel_markers(g, mk, {})
    S.fig_label(fig, "d", 52, 90)
    cb2 = ax_mm(fig, 168, 102, 2.0, 20)
    c2 = fig.colorbar(im, cax=cb2)
    c2.set_label("Cohen's d", fontsize=5.0)
    c2.ax.tick_params(labelsize=5, length=1.5)
    return S.save(fig, "ed8_comunicacao", periodo)


# --- ED7: teoria ---------------------------------------------------------------------------------

def ed7(periodo):
    fig = S.figure(S.DOUBLE, 62)
    a = ax_mm(fig, 42, 6, 60, 24)
    gorder = PO.panel_shap(a)
    S.fig_label(fig, "a", 1, 3)
    lg = ax_mm(fig, 6, 44, 100, 12)
    lg.axis("off")
    gl = [g for g in gorder if g in P.GRUPOS and g not in ("tamanho", "outras")][:9]
    for i, g in enumerate(gl):
        x, y = (i % 3) * 0.34, 0.85 - (i // 3) * 0.38
        lg.add_patch(__import__("matplotlib").patches.Rectangle((x, y - 0.12), 0.02, 0.24, color=P.GRUPOS[g], transform=lg.transAxes, clip_on=False))
        lg.text(x + 0.03, y, P.NOMES_GRUPOS_EN[g], fontsize=4.8, va="center", transform=lg.transAxes)
    b = ax_mm(fig, 140, 6, 40, 40)
    panel_cascata(b)
    S.fig_label(fig, "b", 112, 3)
    return S.save(fig, "ed7_teoria", periodo)


# --- ED8: fora da amostra em detalhe -------------------------------------------------------------

def ed8(periodo):
    tag = "dev" if periodo == "dev" else periodo
    ev, mu, phi, dist, y, crps = PT._setup(tag)
    fig = S.figure(S.DOUBLE, 178)
    a = ax_mm(fig, 14, 6, 40, 36)
    PT.panel_test(a, ev, mu, phi, y, crps)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 72, 11, 48, 35)
    PT.panel_monthly(b, ev, crps)
    S.fig_label(fig, "b", 60, 3)
    c = ax_mm(fig, 134, 4, 46, 66)
    PT.panel_hitmiss(c, ev, mu)
    S.fig_label(fig, "c", 128, 2)
    d = ax_mm(fig, 40, 80, 26, 46)
    PT.panel_niche(d, ev, crps)
    S.fig_label(fig, "d", 1, 76)
    e = ax_mm(fig, 84, 82, 36, 36)
    PP.panel_calibration(e, F.calibration(tag))
    S.fig_label(fig, "e", 74, 76)
    f = ax_mm(fig, 16, 140, 40, 30)
    PP.panel_where_when(f, F.within_corr(tag))
    S.fig_label(fig, "f", 1, 135)
    g = ax_mm(fig, 128, 140, 46, 24)  # antigo Fig. 6e (R16): celular × letal na escala do órgão
    PP.panel_contrast(g, F.district_contrast())
    S.fig_label(fig, "g", 114, 135)
    return S.save(fig, "ed6_fora_da_amostra", periodo)


# --- ED9: perturbação natural --------------------------------------------------------------------

NOMES_P4 = N.EVENT_EN


def ed9(periodo):
    ev = _j(atlas_dir() / "perturbacao" / "evento_estudo.json")
    fig = S.figure(S.DOUBLE, 96)
    for i, suf in enumerate(("", "_estrito")):
        fig.text(14 / S.DOUBLE, 1 - (3.5 + i * 44) / 96, N.EVENT_ROW_EN[suf], fontsize=6, fontweight="bold", va="center")
    for j, base in enumerate(("abre_bar", "abre_varejo", "fecha_bar")):
        for i, suf in enumerate(("", "_estrito")):
            r = ev.get(base + suf)
            ax = ax_mm(fig, 14 + j * 58, 12 + i * 44, 48, 28)
            if not r:
                ax.axis("off")
                continue
            es = np.array([int(k) for k in r["caminho"]])
            v = np.array(list(r["caminho"].values()))
            if "caminho_ic" in r:
                ax.fill_between(es, r["caminho_ic"]["lo"], r["caminho_ic"]["hi"], color="#D9D9D9", lw=0, step="mid")
            ax.plot(es, v, color="#264653", lw=0.9, drawstyle="steps-mid")
            ax.axhline(0, color=S.INK, lw=0.5)
            ax.axvline(-0.5, color="#D1495B", lw=0.6, ls=(0, (2, 2)))
            ax.set_xticks([-6, -3, 0, 3, 6, 9])
            ef = f"effect {r['efeito_relativo'] * 100:+.1f}% (95% CI {r['ic_efeito'][0] / r['base'] * 100:+.1f} to {r['ic_efeito'][1] / r['base'] * 100:+.1f}%)"
            ax.set_title(f"{NOMES_P4[base]}\nn = {r['n']:,} segments; {ef.replace('-', '−')}", fontsize=5.0, loc="left", pad=2)
            if j == 0:
                ax.set_ylabel("Δ street theft and robbery\nper segment-month", fontsize=5.5)
            if i == 1:
                ax.set_xlabel("Months since event", fontsize=5.5)
    S.fig_label(fig, "a", 1, 2)
    S.fig_label(fig, "b", 1, 46)
    return S.save(fig, "ed4_perturbacao", periodo)


# --- ED10: painel de fenótipos ---------------------------------------------------------------------

def ed10(periodo):
    fd = atlas_dir() / "fenotipo"
    ass = _j(fd / "assinaturas.json")
    prog = _j(fd / "programas.json")
    od = atlas_dir() / "presenca_2023"
    pres = _j(od / "presenca_2023.json").get("2023", {}).get(VARIANTE_OD, {})
    boot = pl.read_parquet(od / "bootstrap.parquet").filter(pl.col("variante") == VARIANTE_OD) if (od / "bootstrap.parquet").exists() else None
    _, _, _, longo, curto = R.classes()
    fig = S.figure(S.DOUBLE, 128)
    a = ax_mm(fig, 36, 6, 40, 50)
    fen = sorted(ass["eventos"], key=lambda f: -ass["eventos"][f])
    y = np.arange(len(fen))
    a.barh(y, [ass["eventos"][f] / 1000 for f in fen], color="#264653", height=0.65)
    for i, f in enumerate(fen):
        cob = ass["validacao_pontual"].get(f, {}).get("cobertura")
        if cob is not None:
            a.text(ass["eventos"][f] / 1000 + 2, i, f"{cob:.0%}", va="center", fontsize=4.4, color=S.MUTED)
    a.set_yticks(y)
    a.set_yticklabels([R.FEN_EN[f] for f in fen], fontsize=5)
    a.invert_yaxis()
    a.set_xlabel("Events in exploration tracts, 2024–25 (thousands)")
    a.set_title("grey numbers: share geocoded", fontsize=5, loc="right", color=S.MUTED)
    a.tick_params(axis="y", length=0)
    S.fig_label(fig, "a", 1, 3)
    b = ax_mm(fig, 96, 8, 34, 30)
    ks = sorted(int(k) for k in prog["estabilidade"])
    b.plot(ks, [prog["estabilidade"][str(k)] for k in ks], color="#264653", marker="o", ms=2.5, lw=0.9, label="stability")
    if "erro_relativo" in prog:
        b2 = b.twinx()
        b2.plot(ks, [prog["erro_relativo"][str(k)] for k in ks], color="#D1495B", marker="s", ms=2.2, lw=0.8)
        b2.set_ylabel("Relative reconstruction error", fontsize=5, color="#D1495B")
        b2.tick_params(labelsize=4.8)
    b.axvline(prog["k"], color="#BDBDBD", lw=0.6, ls=(0, (2, 2)))
    b.set_xlabel("Number of programs (k)")
    b.set_ylabel("Stability across seeds")
    S.fig_label(fig, "b", 84, 3)
    c = ax_mm(fig, 36, 70, 40, 44)
    fm = {k: float(v) for k, v in pres.get("fator_multidao_rua", {}).items()}
    fp = {k: float(v) for k, v in pres.get("fator_multidao_presenca", {}).items()}
    cls = sorted(fm, key=lambda k: -fm[k])
    yy = np.arange(len(cls))
    if boot is not None:  # 95% do bootstrap de domicílios da OD (pedestres)
        for i, k in enumerate(cls):
            col = f"multidao_{k}"
            if col in boot.columns:
                lo, hi = np.nanpercentile(boot[col].to_numpy(), [2.5, 97.5])
                c.plot([lo, hi], [i, i], color="#264653", lw=0.7, zorder=2)
    c.scatter([fm[k] for k in cls], yy, s=10, color="#264653", label="Pedestrians (95% CI)", zorder=3)
    c.scatter([fp.get(k, np.nan) for k in cls], yy, s=10, facecolor="white", edgecolor="#264653", label="People present", zorder=3)
    c.axvline(1, color=S.INK, lw=0.5)
    c.set_yticks(yy)
    c.set_yticklabels([curto.get(k, k) for k in cls], fontsize=5)
    c.invert_yaxis()
    c.set_xlabel("Crowd factor (density of people on the\nclass relative to the city mean)")
    c.legend(loc="lower right", fontsize=5)
    c.tick_params(axis="y", length=0)
    S.fig_label(fig, "c", 1, 66)
    d = ax_mm(fig, 110, 72, 44, 34)
    PP.panel_turnover(d)
    S.fig_label(fig, "d", 96, 66)
    return S.save(fig, "ed3_painel", periodo)


# --- ED10 (nova): robustez (parecer R3, R4, R8, R12; Agentes A, B e C) ----------------------------

SIM_CEN = [("a_poisson", "o", "#264653"), ("b_risco_distrito", "s", "#E8743B"), ("c_sobredispersao", "^", "#2A9D8F"),
           ("d_permutado", "D", "#8E6CC2")]
FAV_COR = {"atual": "#1A1A1A", "area": "#E8743B", "perimetro": "#E3B23C", "raiz_domicilios": "#5B9BD5",
           "domicilios_ocupados": "#2A9D8F", "indicador_setor": "#8E6CC2"}
OCULTA = ["mar", "mnar_crime", "mnar_residencial"]


def _identificacao() -> dict:
    """``fenotipo/identificacao.json``; no desenvolvimento, CITYOMICS_IDENTIFICACAO_JSON aponta um JSON parcial."""
    import os
    from pathlib import Path

    alt = os.environ.get("CITYOMICS_IDENTIFICACAO_JSON")
    return _j(Path(alt)) if alt else _j(atlas_dir() / "fenotipo" / "identificacao.json")


def _pendente(ax, txt: str):
    ax.axis("off")
    ax.text(0.5, 0.5, txt, ha="center", va="center", fontsize=5.5, color=S.MUTED, transform=ax.transAxes)


def _media(v):
    """Valor pontual de um campo que pode ser número ou {media, p2_5, p97_5}."""
    return (v.get("media"), v.get("p2_5"), v.get("p97_5")) if isinstance(v, dict) else (v, None, None)


def ed10_painel_simulacao(a1, a2, sim: dict, rows: list[str], curto: dict):
    cel = sim.get("celular_2025", {})
    cen, cob = cel.get("cenarios", {}), cel.get("cobertura", {})
    nos_dados = [k for c, _, _ in SIM_CEN for k in cen.get(c, {}).get("celular_2025", {}).get("classes", {})]
    rows = [r for r in rows if r in nos_dados] + [r for r in dict.fromkeys(nos_dados) if r not in rows]
    off = np.linspace(-0.27, 0.27, len(SIM_CEN))
    hs = []
    for (c, mk, cor), dy in zip(SIM_CEN, off):
        cl = cen.get(c, {}).get("celular_2025", {}).get("classes", {})
        if not cl:
            continue
        for i, r in enumerate(rows):
            v = cl.get(r)
            if not v:
                continue
            b, e = v["vies_relativo_mediano"] * 100, v["erro_abs_relativo_mediano"] * 100
            a1.plot([max(b - e, -100), min(b + e, 100)], [i + dy, i + dy], color=cor, lw=0.6, alpha=0.8)
            fora = abs(b) > 100  # além de ±100%: desenhado na borda, vazado
            a1.scatter([np.clip(b, -100, 100)], [i + dy], s=6, marker=mk, color="white" if fora else cor, edgecolor=cor,
                       zorder=3, linewidth=0.6 if fora else 0)
        rho = cen[c]["celular_2025"].get("spearman_taxas_todas", [np.nan] * 3)[1]
        hs.append((a1.scatter([], [], s=8, marker=mk, color=cor), f"{N.SIM_SCENARIO_EN[c]} (ρ = {rho:.2f})"))
        cv = cob.get(c, {}).get("taxas", {})
        if cv:
            a2.scatter([cv.get(r, np.nan) * 100 for r in rows], np.arange(len(rows)) + dy, s=6, marker=mk, color=cor, linewidth=0, zorder=3)
    for ax in (a1, a2):
        ax.set_ylim(len(rows) - 0.5, -0.5)
        ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
    a1.axvline(0, color=S.INK, lw=0.5)
    a1.set_yticks(range(len(rows)))
    a1.set_yticklabels([curto.get(r, r) for r in rows], fontsize=5)
    a1.set_xlabel("Error of recovered rate (%)")
    a2.axvline(95, color=S.INK, lw=0.5, ls=(0, (2, 2)))
    a2.set_yticks([])
    a2.spines["left"].set_visible(False)
    a2.set_xlim(min(50, a2.get_xlim()[0]), 100)
    a2.set_xlabel("Coverage of\n95% intervals (%)")
    a1.legend([h for h, _ in hs], [t for _, t in hs], loc="lower left", bbox_to_anchor=(0.0, 1.01), ncol=2, fontsize=5,
              handletextpad=0.1, columnspacing=0.8, borderaxespad=0.1, title="Simulated truth (Spearman ρ, true vs recovered rates)",
              title_fontsize=5)


def ed10_painel_metades(ax, met: dict):
    alvos = [f for f in ["celular_2025"] + list(met.get("testados", [])) if isinstance(met.get(f), dict)]
    for i, f in enumerate(alvos):
        r = met[f]
        o = r.get("original", {}).get("lotes")
        m, (lo, hi) = r.get("A_para_B_lotes_media"), r.get("A_para_B_lotes_faixa", [np.nan, np.nan])
        if o is not None and m is not None:
            ax.plot([o, m], [i, i], color="#D9D9D9", lw=0.6, zorder=1)
        ax.plot([lo, hi], [i, i], color="#264653", lw=1.2, zorder=2, solid_capstyle="butt")
        ax.scatter([m], [i], s=11, color="#264653", zorder=3, label="Disjoint halves (mean; range of 5 splits)" if i == 0 else None)
        ax.scatter([o], [i], s=11, facecolor="white", edgecolor="#264653", linewidth=0.7, zorder=3,
                   label="All events, original check" if i == 0 else None)
    ax.set_yticks(range(len(alvos)))
    ax.set_yticklabels([N.CRIME_EN.get(f, f) for f in alvos], fontsize=5)
    ax.set_ylim(len(alvos) - 0.5, -0.5)
    xs = [v for f in alvos for v in (met[f].get("original", {}).get("lotes"), *met[f].get("A_para_B_lotes_faixa", [])) if v is not None]
    ax.set_xlim(min(0.0, min(xs) - 0.05) if xs else 0, 1.0)
    ax.set_xlabel("Finer-scale check across parcel types,\nSpearman ρ (rates from half A vs points of half B)")
    ax.tick_params(axis="y", length=0)
    ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=5, handletextpad=0.2, borderaxespad=0.1)


def ed10_painel_ocultacao(c1, c2, oc: dict):
    cen = [c for c in OCULTA if c in oc]
    y = np.arange(len(cen))
    for i, c in enumerate(cen):
        m, lo, hi = _media(oc[c]["razao_var_dentro_agregada"])
        if lo is not None:
            c1.plot([lo, hi], [i, i], color="#264653", lw=1.0)
        c1.scatter([m], [i], s=12, color="#264653", zorder=3)
        tv, _, _ = _media(oc[c]["teto_dentro_verdadeira"])
        rv, rlo, rhi = _media(oc[c]["teto_dentro_recuperada"])
        c2.plot([tv, rv], [i, i], color="#BDBDBD", lw=0.8, zorder=1)
        c2.scatter([tv], [i], s=12, facecolor="white", edgecolor="#D1495B", linewidth=0.8, zorder=3, label="True (geocoded)" if i == 0 else None)
        c2.scatter([rv], [i], s=12, color="#D1495B", zorder=3, label="Recovered (reconciled)" if i == 0 else None)
    c1.axvline(1, color=S.INK, lw=0.5, ls=(0, (2, 2)))
    c1.set_yticks(y)
    c1.set_yticklabels([N.HIDE_SCENARIO_EN[c] for c in cen], fontsize=5)
    c1.set_xlabel("Within-tract monthly variance,\nrecovered ÷ true")
    c1.set_xlim(min(0.5, c1.get_xlim()[0]), 1.05)
    c2.set_yticks([])
    c2.spines["left"].set_visible(False)
    c2.set_xlabel("Within-tract noise ceiling\n(maximum R²)")
    for ax in (c1, c2):
        ax.set_ylim(len(cen) - 0.5, -0.5)
        ax.tick_params(axis="y", length=0)
        ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
        ax.set_axisbelow(True)
    c2.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), fontsize=5, handletextpad=0.1, borderaxespad=0.1)
    c1.set_title("Coordinates hidden", fontsize=5.5, loc="left", pad=2)


def ed10_painel_dispersao(ax, rd: dict, cal: dict):
    versoes = [("producao", "reconciliado", "poisson_puro_medias_reconciliadas", "Reconciled"),
               ("imputacoes", "imputado", None, "Integer\nimputations"),
               ("geocodificado", "geocodificado", "poisson_puro_medias_geocodificadas", "Geocoded\nonly")]
    conj = [("todos", "rejeita_todos", "All tracts"), ("ge1", "rejeita_ge1", "≥1 event per month")]
    x, labs, k = [], [], 0
    pipe = cal.get("pipeline", {})
    for gi, (cj, chave, titulo) in enumerate(conj):
        for vi, (vo, vn, vp, nome) in enumerate(versoes):
            pos = gi * (len(versoes) + 0.8) + vi
            obs, olo, ohi = _media(rd.get(vo, {}).get(chave))
            if obs is not None:
                if olo is not None:
                    ax.plot([pos - 0.15] * 2, [olo * 100, ohi * 100], color=S.INK, lw=0.8)
                ax.scatter([pos - 0.15], [obs * 100], s=14, marker="D", color=S.INK, zorder=3, label="Observed" if k == 0 else None)
            nm, nlo, nhi = _media(pipe.get(vn, {}).get(cj, {}))
            if nm is not None:
                ax.plot([pos + 0.1] * 2, [nlo * 100, nhi * 100], color="#D1495B", lw=0.8)
                ax.scatter([pos + 0.1], [nm * 100], s=12, facecolor="white", edgecolor="#D1495B", linewidth=0.8, zorder=3,
                           label="Null through the reconciliation" if k == 0 else None)
            if vp:
                pm, plo, phi = _media(cal.get(vp, {}).get(cj, {}))
                if pm is not None:
                    ax.plot([pos + 0.3] * 2, [plo * 100, phi * 100], color="#9A9A9A", lw=0.8)
                    ax.scatter([pos + 0.3], [pm * 100], s=8, marker="s", color="#9A9A9A", zorder=3,
                               label="Pure Poisson null" if k == 0 else None)
            x.append(pos)
            labs.append(nome)
            k += 1
        ax.text(gi * (len(versoes) + 0.8) + 1, 1.0, titulo, transform=__import__("matplotlib").transforms.blended_transform_factory(
            ax.transData, ax.transAxes), ha="center", va="bottom", fontsize=5.5)
    ax.axhline(5, color=S.MUTED, lw=0.5, ls=(0, (2, 2)))
    ax.set_xticks(x)
    ax.set_xticklabels(labs, fontsize=5)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.1)
    ax.set_ylabel("Tracts rejecting Poisson\nat the 5% level (%)")
    ax.legend(loc="upper left", fontsize=5, handletextpad=0.2, borderaxespad=0.1, labelspacing=0.25)


def ed10_painel_favelas(ax, fav: dict):
    alt = fav.get("alternativas", {})
    fen = fav.get("fenotipos", [])
    if "atual" not in alt or not fen:
        return _pendente(ax, "favela exposures pending")
    base = alt["atual"]["log2_enriq_favela"]
    fen = sorted(fen, key=lambda f: -base.get(f, 0))
    nomes = [n for n in FAV_COR if n in alt] + [n for n in alt if n not in FAV_COR]
    off = np.linspace(-0.3, 0.3, len(nomes))
    m = fav.get("construcao", {}).get("fator_implicito_m_por_domicilio")
    for n, dy in zip(nomes, off):
        v = alt[n]
        cor = FAV_COR.get(n, "#888888")
        if n == "atual":
            for i, f in enumerate(fen):
                lo, hi = v["ic_log2_favela"].get(f, [np.nan, np.nan])
                ax.plot([lo, hi], [i + dy, i + dy], color=cor, lw=0.7)
        rho = v.get("contra_atual", {}).get("spearman_partes_mediana")
        lab = N.FAVELA_EXPOSURE_EN.get(n, n).format(m=f"{m:.0f}" if m else "k")
        lab += "" if n == "atual" else f" (ρ = {rho:.2f})" if rho is not None else ""
        ax.scatter([v["log2_enriq_favela"].get(f, np.nan) for f in fen], np.arange(len(fen)) + dy, s=7, color=cor,
                   marker="D" if n == "atual" else "o", linewidth=0, zorder=3, label=lab)
    ax.axvline(0, color=S.INK, lw=0.5)
    ax.set_yticks(range(len(fen)))
    ax.set_yticklabels([N.CRIME_EN.get(f, f) for f in fen], fontsize=5)
    ax.set_ylim(len(fen) - 0.5, -0.5)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Favelas: log₂ enrichment vs mean crime type")
    ax.grid(True, axis="x", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=5, handletextpad=0.1, borderaxespad=0.0,
              title="Favela exposure (median ρ of\nclass shares vs current)", title_fontsize=5, labelspacing=0.3)


def ed10_painel_blocos(ax, blocos: dict):
    from fig4 import TESTES, CRIME_COR

    nulos = [("individual", "o", "Events permuted (in the article)"), ("dia", "s", "Same-day blocks"), ("mes", "^", "Same-month blocks")]
    ys = []
    for k, (d, a) in enumerate(TESTES):
        b = blocos.get(d, {}).get(str(a), {})
        for (nome, mk, lab), dx in zip(nulos, (-0.2, 0.0, 0.2)):
            v = b.get(nome)
            if not v:
                continue
            p, n = v["p"], v.get("n_perm", 999)
            piso = p <= 1 / (n + 1) * (1 + 1e-9)
            ax.scatter([k + dx], [p], s=14, marker=mk, color=CRIME_COR[d] if not piso else "white", edgecolor=CRIME_COR[d],
                       linewidth=0.8, zorder=3)
            ys.append(p)
    ax.axhline(0.05, color=S.INK, lw=0.5, ls=(0, (2, 2)))
    ax.text(len(TESTES) - 0.45, 0.05, "P = 0.05", fontsize=5, va="bottom", ha="right", color=S.MUTED)
    ax.set_yscale("log")
    ax.set_ylim(1.2, min(ys + [1e-3]) / 2 if ys else 1e-4)
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator

    tk = [t for t in (0.001, 0.01, 0.1, 1) if t >= ax.get_ylim()[1]]
    ax.yaxis.set_major_locator(FixedLocator(tk))
    ax.yaxis.set_major_formatter(FixedFormatter([f"{t:g}" for t in tk]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.set_xticks(range(len(TESTES)))
    ax.set_xticklabels([N.clock_label(d, a, "\n") for d, a in TESTES], fontsize=5)
    for t, (d, _) in zip(ax.get_xticklabels(), TESTES):
        t.set_color(CRIME_COR[d])
    ax.set_xlim(-0.5, len(TESTES) - 0.5)
    ax.set_ylabel("Permutation P of the class contrast")
    from matplotlib.lines import Line2D

    h = [Line2D([], [], marker=mk, ls="", color=S.INK, ms=3) for _, mk, _ in nulos]
    h.append(Line2D([], [], marker="o", ls="", mfc="white", mec=S.INK, ms=3))
    ax.legend(h, [lab for _, _, lab in nulos] + ["Open: at the permutation floor"], loc="lower left", fontsize=5,
              handletextpad=0.2, borderaxespad=0.1, labelspacing=0.25)


def ed10_robustez(periodo):
    fd = atlas_dir() / "fenotipo"
    ide, rec, rq = _identificacao(), _j(fd / "reconciliacao.json"), _j(fd / "ritmo_queda.json")
    _, _, _, longo, curto = R.classes()
    fig = S.figure(S.DOUBLE, 214)
    # a — recuperação por simulação
    a1 = ax_mm(fig, 38, 18, 28, 56)
    a2 = ax_mm(fig, 69, 18, 19, 56)
    if ide.get("simulacao"):
        ed10_painel_simulacao(a1, a2, ide["simulacao"], R.ordem_linhas(), curto)
    else:
        _pendente(a1, "identificacao.json pending")
        a2.axis("off")
    S.fig_label(fig, "a", 1, 2)
    # b — metades disjuntas
    b = ax_mm(fig, 130, 10, 50, 56)
    if ide.get("metades"):
        ed10_painel_metades(b, ide["metades"])
    else:
        _pendente(b, "identificacao.json pending")
    S.fig_label(fig, "b", 94, 2)
    # c — ocultação
    c1 = ax_mm(fig, 36, 96, 26, 22)
    c2 = ax_mm(fig, 66, 96, 24, 22)
    if rec.get("ocultacao"):
        ed10_painel_ocultacao(c1, c2, rec["ocultacao"])
    else:
        _pendente(c1, "reconciliacao.json pending")
        c2.axis("off")
    S.fig_label(fig, "c", 1, 88)
    # d — teste de dispersão contra o nulo calibrado
    d = ax_mm(fig, 116, 94, 64, 30)
    if rec.get("ruido_dispersao") and rec.get("calibracao"):
        ed10_painel_dispersao(d, rec["ruido_dispersao"], rec["calibracao"])
    else:
        _pendente(d, "reconciliacao.json pending")
    S.fig_label(fig, "d", 98, 88)
    # e — favelas sob exposições alternativas
    e = ax_mm(fig, 34, 148, 42, 58)
    if ide.get("favelas"):
        ed10_painel_favelas(e, ide["favelas"])
    else:
        _pendente(e, "identificacao.json pending")
    S.fig_label(fig, "e", 1, 142)
    # f — P do relógio com nulos em blocos
    f = ax_mm(fig, 128, 150, 52, 40)
    if rq.get("relogio_blocos"):
        ed10_painel_blocos(f, rq["relogio_blocos"])
    else:
        _pendente(f, "ritmo_queda.json pending")
    S.fig_label(fig, "f", 112, 142)
    return S.save(fig, "ed2_robustez", periodo)
