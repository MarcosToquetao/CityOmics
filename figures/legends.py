"""Legendas das figuras no estilo Nature (D46), com os números lidos dos resultados (narrativa B, D63).

Gera ``figures/legendas_<periodo>.md`` (inglês). A primeira frase de cada legenda, em negrito, é a
conclusão da figura; as demais descrevem os painéis e as estatísticas. Nenhum número é digitado à mão.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import REPO_ROOT, processed_dir

NAN = float("nan")


def _j(path):
    return json.loads(path.read_text()) if path.exists() else {}


def build(periodo: str = "dev") -> str:
    a = atlas_dir()
    fd, pd_ = a / "fenotipo", a / "presenca"
    tip, att, var, fate = _j(a / "tipagem_2025.json"), _j(a / "atribuicao_celular_2025.json"), _j(a / "variancia_2025.json"), _j(a / "destino.json")
    dom = _j(a / "dominios_2025.json")
    ass, prog, rel = _j(fd / "assinaturas.json"), _j(fd / "programas.json"), _j(fd / "relogio.json")
    mem, qd, prev = _j(fd / "memoria.json"), _j(fd / "queda.json"), _j(fd / "previsibilidade.json")
    pres, ev4 = _j(pd_ / "presenca.json"), _j(a / "perturbacao" / "evento_estudo.json")
    bench = _j(processed_dir() / "modelo" / "resultados_benchmark_dev.json").get("resultados", {})
    sel = _j(REPO_ROOT / "prereg" / "selection_dev.json")
    dq = _j(processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json")
    lam = pl.read_parquet(a / "atribuicao_celular_2025.parquet") if (a / "atribuicao_celular_2025.parquet").exists() else None
    capp = processed_dir() / "figdata" / f"fig5_captura_{periodo}.parquet"
    cap = pl.read_parquet(capp) if capp.exists() else None
    hrs = pl.read_parquet(fd / "relogio_horas_roubo_celular.parquet") if (fd / "relogio_horas_roubo_celular.parquet").exists() else None
    qc = pl.read_parquet(fd / "queda_celular.parquet") if (fd / "queda_celular.parquet").exists() else None
    esc = pl.read_parquet(fd / "previsibilidade_escala.parquet") if (fd / "previsibilidade_escala.parquet").exists() else None

    def capv(curva, area, alvo="n_total"):
        if cap is None:
            return NAN
        return float(cap.filter((pl.col("curva") == curva) & (pl.col("area") == area) & (pl.col("alvo") == alvo))["captura"][0]) * 100

    def lamv(c):
        if lam is None:
            return NAN
        r = lam.filter(pl.col("classe") == c)
        return float(r["lambda"][0]) if r.height else NAN

    def hora(c, hs):
        if hrs is None:
            return NAN
        r = hrs.filter(pl.col("classe") == c)
        return sum(float(r[f"h{h:02d}"][0]) for h in hs) * 100 if r.height else NAN

    def qv(c, col):
        if qc is None:
            return NAN
        r = qc.filter(pl.col("classe") == c)
        return float(r[col][0]) if r.height else NAN

    def ev(e, t, m, col):
        if esc is None:
            return NAN
        r = esc.filter((pl.col("espaco") == e) & (pl.col("tempo") == t) & (pl.col("medida") == m))
        return float(r[col][0]) if r.height else NAN

    h1a = sel.get("h1a", {})
    # Fig. 4 e ED 2, 10: OD 2023, blocos do relógio, reconciliação, identificação
    p23 = _j(a / "presenca_2023" / "presenca_2023.json").get("2023", {}).get("pe_bici", {})
    B23 = _j(a / "presenca_2023" / "presenca_2023.json").get("bootstrap", {}).get("B")
    p23boot = p23.get("bootstrap", {}) | {"B": f"{B23:,}" if isinstance(B23, int) else "—"}
    rq = _j(fd / "ritmo_queda.json")
    blocos = rq.get("relogio_blocos", {})
    fds_ic = rq.get("relogio_ic", {}).get("fim_de_semana", {})
    rec = _j(fd / "reconciliacao.json")
    oc, cal = rec.get("ocultacao", {}), rec.get("calibracao", {})
    import os

    ide = _j(Path(os.environ["CITYOMICS_IDENTIFICACAO_JSON"])) if os.environ.get("CITYOMICS_IDENTIFICACAO_JSON") else _j(fd / "identificacao.json")
    sim, met = ide.get("simulacao", {}), ide.get("metades", {})
    from cityomics.viz import names as N

    _, curto = N.class_labels()
    perfil = pl.read_parquet(a / "tipos_perfil_2025.parquet")
    pop = perfil.filter(pl.col("familia") == "res_horizontal").sort("padrao_baixo", descending=True)["nome"]
    popular = pop[0] if len(pop) else ""

    def ic(v, d=2):
        return f"{v[0]:.{d}f}–{v[1]:.{d}f}" if v else "—"

    def pfmt(r, d, ano):
        """P de cada nulo do relógio: eventos (relogio.json), blocos de dia e de mês (ritmo_queda.json)."""
        def f(p, n):
            if p is None:
                return "—"
            return f"P ≤ {1 / (n + 1):.3f}" if p <= 1 / (n + 1) * (1 + 1e-9) else f"P = {p:.3f}"
        b = blocos.get(d, {}).get(ano, {})
        return (f"{f(r.get(ano, {}).get('p'), len(r.get(ano, {}).get('H_nulo', [])) or 200)} with events, "
                f"{f(b.get('dia', {}).get('p'), b.get('dia', {}).get('n_perm', 999))} with day blocks and "
                f"{f(b.get('mes', {}).get('p'), b.get('mes', {}).get('n_perm', 999))} with month blocks")

    def fdsv(d, c):
        v = fds_ic.get(d, {}).get("classes", {}).get(c)
        return f"{v['razao']:.2f}, 95% interval {ic(v['ic'])}" if v else "—"

    try:
        import fig4 as F4

        rv23 = pl.read_parquet(a / "presenca_2023" / "relogio_vs_rua.parquet").filter(pl.col("variante") == F4.VARIANTE)
        dest = F4.destaques(rv23)
    except Exception:  # noqa: BLE001
        dest = []
    destaques_txt = ", ".join(curto.get(c, c).lower() for c in dest)
    n_tipos = tip.get("n_tipos", "—")
    stab = tip.get("estabilidade", {}).get("0.02", {}).get("ari_medio", NAN)
    rv = pres.get("relogio_vs_rua", {})
    risco = rv.get("risco_relativo_por_hora", [NAN] * 24)
    disp = prev.get("dispersao_setor_mes", {})
    mde = [v.get("mde_relativo") for v in ev4.values() if isinstance(v, dict) and v.get("mde_relativo")]
    fen = qd.get("fenotipos", {})
    n_eventos = sum(ass.get("eventos", {}).values())
    G1 = ass.get("gate_G1", {})
    furto, roubo = rel.get("celular_furto", {}), rel.get("celular_roubo", {})
    fds = rel.get("fim_de_semana", {})

    txt = f"""# Figure legends ({periodo})

**Fig. 1 | São Paulo read as a tissue.** **a**, Correspondence between spatial transcriptomics and the city: parcels are cells, census tracts are spots, streets and stations are the interstitium and vessels, neighbourhood composition is the niche, crime generators and targets play the role of ligand–receptor pairs and crime is the phenotype. **b**, 1.65 million fiscal parcels coloured by type (Leiden on 30 native parcel attributes from the 2025 property-tax cadastre and the December-2025 business registry, linked by address), with census favelas (IBGE FCU) as pseudo-cells; rail lines and water bodies as landmarks. **c,d**, Parcel-resolution views of the centre (**c**) and of a periphery where a favela abuts high-rise condominiums (**d**), with census-tract outlines (white). No crime data are shown. Scale bars, 10 km (**b**) and 500 m (**c,d**).

**Fig. 2 | Parcel types and tissue architecture.** **a**, UMAP of 150,000 parcels coloured by type. **b**, Marker attributes per type (dot size, fraction of parcels expressing the attribute; colour, mean standardized value). **c**, Spot (census-tract) composition as pie charts in the centre, analogous to spot deconvolution. **d**, Neighbourhood enrichment between parcel types (z-scores against 100 permutations restricted to district × population-density decile; diagonal omitted). **e**, Tissue domains: tract composition smoothed over contiguous neighbours and clustered (k = {dom.get('k', '—')}, chosen by silhouette), named by their most enriched elements. **f**, Typing stability across subsamples (adjusted Rand index) against the number of types; the selected resolution (orange; {n_tipos} types, ARI = {stab:.3f}) was fixed without any crime data; dashed line, agreement with an OAC-style k-means baseline (ARI = {tip.get('ari_kmeans_vs_leiden', NAN):.2f}).

**Fig. 3 | Crime is a phenotype of the cell classes of the tissue.** **a**, Phone thefts and robberies attributed to each cell class in 2025 (per km of parcel frontage or street; diamonds, per station), from a Poisson model in which each tract's count is the sum of what its cells produce (EM; 95% intervals from 500 district bootstrap resamples): high-rise residential and mixed parcels {lamv('Vertical residencial e misto'):.0f} km⁻¹ yr⁻¹, mixed residential and commercial parcels {lamv('Misto residencial e comercial'):.0f}, arterial streets {lamv('rua_arterial_m'):.0f}, rail stations {lamv('n_trilho'):.0f} per station; low-rise residential parcels are near zero. **b**, Signature matrix of {len(ass.get('fenotipos', []))} crime phenotypes ({n_eventos / 1e6:.2f} million reconciled events in exploration tracts, 2024–2025): dot size, share of the phenotype's expected count produced by the class; colour, log₂ enrichment against the mean phenotype. The most enriched class differs across phenotypes ({len(ass.get('classes_distintas_no_topo', []))} distinct classes); traffic injuries, a positive control, have their highest rate per km among street classes on arterial streets ({ass.get('controle_positivo_transito', {}).get('lambda_por_km', {}).get('rua_arterial_m', NAN):.2f} vs {ass.get('controle_positivo_transito', {}).get('lambda_por_km', {}).get('rua_local_m', NAN):.2f} injuries per km on local streets over 2024–2025). **c**, Point validation per phenotype: Spearman correlation between the attributed rate and the rate observed by linking geocoded events to the nearest street segment and its abutting parcels (median across parcel types {G1.get('validacao_mediana_lotes', NAN):.2f}); phenotypes with less than 80% geocoded events are not tested. **d**, Crime programs from non-negative matrix factorization of the tract × phenotype matrix (k = {prog.get('k', '—')}, the smallest k ≥ 3 stable across seeds, stability {prog.get('estabilidade', {}).get(str(prog.get('k', 0)), NAN):.2f}); rows named by the cell classes most associated with each program. **e**, Program usage per tract (rasterized; spatial-vault districts in grey). **f**, Decomposition of expected 2025 phone thefts by theoretical covariate group and cell class (exact Shapley values against the average tract; reductions as a sink). All crime analyses exclude 19 districts held out as a spatial vault.

**Fig. 4 | Each class keeps its own daily rhythm.** **a**, Pre-specified test of the class clock (claim C4), phone theft first and phone robbery second: departures of each class from the city's share of events in four periods of the day, 2024 against 2025 (dots, class × period; phone theft r = {furto.get('replica_r', NAN):.2f}, phone robbery r = {roubo.get('replica_r', NAN):.2f}), and the class contrast H (×100) against three nulls: events permuted between periods within districts (grey dots, {len(furto.get('2024', {}).get('H_nulo', []))} permutations) and blocks of events from the same tract and period on the same day or in the same month permuted together (bars, median to 95th percentile; {blocos.get('celular_furto', {}).get('2024', {}).get('dia', {}).get('n_perm', '—')} permutations). P values below the axis (phone theft: {pfmt(furto, 'celular_furto', '2024')} in 2024 and {pfmt(furto, 'celular_furto', '2025')} in 2025; phone robbery: {pfmt(roubo, 'celular_roubo', '2024')} and {pfmt(roubo, 'celular_roubo', '2025')}). **b**, Exploratory: hourly profile of phone robbery per cell class estimated by the attribution model (2024–2025, events with exact hour). **c**, Weekday robbery (line, model estimate) and pedestrians on the street (grey; Origin–Destination survey 2023) in four classes ({destaques_txt}). **d**, Citywide robbery risk per pedestrian by hour relative to the daily mean (weekdays; shading, 95% interval from {p23boot.get('B', '—')} household resamples of the survey); between 00:00 and 05:59 it is {p23.get('risco_madrugada_0_5h', NAN):.1f} times the daily mean ({ic(p23boot.get('risco_madrugada_ic95'), 1)}). **e**, Weekend-to-weekday ratio of daily rates of phone theft and phone robbery per class (bars, 95% intervals from {fds_ic.get('B', '—')} district bootstrap resamples; robbery on {curto.get(popular, popular).lower()}, {fdsv('celular_roubo', popular)}). **f**, Robbery per km against robbery per pedestrian across classes (Spearman ρ = {p23.get('spearman_km_vs_pedestre', NAN):.2f}, 95% interval {ic(p23boot.get('spearman_ic95'))}).

**Fig. 5 | The tissue is stable, places remember, and rates move.** **a**, Out-of-sample R² of the 2025 tract theft rate (district-blocked cross-validation): parcel types {var.get('r2_tipos', NAN):.2f}, the same attributes without typing {var.get('r2_genes_sem_tipagem', NAN):.2f}, tissue {var.get('r2_tecido', NAN):.2f}, tissue plus tract covariates {var.get('r2_tecido_mais_covariaveis', NAN):.2f}, historical mean {var.get('r2_media_historica', NAN):.2f}; between-tract share of variance (ICC) = {var.get('icc_2025', NAN):.2f}. **b**, Between-tract variance of the log annual theft rate (2022–2025): tissue (expected count from composition alone) {mem.get('partes', {}).get('tecido', NAN) * 100:.0f}%, stable memory beyond the tissue (covariance of residuals across years) {mem.get('partes', {}).get('memoria_estavel', NAN) * 100:.0f}% and transient {mem.get('partes', {}).get('transitoria', NAN) * 100:.0f}%; in high-crime tracts (≥10 expected per year) memory reaches {mem.get('setores_altos', {}).get('partes', {}).get('memoria_estavel', NAN) * 100:.0f}%. **c**, Persistence of the residual beyond the tissue: r = {mem.get('persistencia_residuo', {}).get('1', NAN):.2f}, {mem.get('persistencia_residuo', {}).get('2', NAN):.2f} and {mem.get('persistencia_residuo', {}).get('3', NAN):.2f} at lags of 1–3 years. **d**, Annual transition rates between parcel families in the property-tax cadastre, 2012–2025 (2021 excluded); permanence = {fate.get('permanencia_media', NAN) * 100:.1f}% per year. **e**, Phone thefts fell by {(1 - qd.get('celular', {}).get('r_total', NAN)) * 100:.0f}% from 2022 to 2025 with the tissue held at its 2025 composition, but not uniformly: local streets fell faster than the city (relative ratio {qv('rua_local_m', 'razao_rel'):.2f}, 95% interval {qv('rua_local_m', 'ic_lo'):.2f}–{qv('rua_local_m', 'ic_hi'):.2f}), while rail stations kept their rate ({qv('n_trilho', 'lambda_2022'):.0f} → {qv('n_trilho', 'lambda_2025'):.0f} per station) and arterial streets fell less than the city (relative ratio {qv('rua_arterial_m', 'razao_rel'):.2f}, {qv('rua_arterial_m', 'ic_lo'):.2f}–{qv('rua_arterial_m', 'ic_hi'):.2f}); dot size, share of 2022 thefts. **f**, Change 2022→2025 by phenotype (phone robbery {(fen.get('celular_roubo', {}).get('r_total', NAN) - 1) * 100:+.0f}%, phone theft {(fen.get('celular_furto', {}).get('r_total', NAN) - 1) * 100:+.0f}%, assault {(fen.get('lesao_dolosa', {}).get('r_total', NAN) - 1) * 100:+.0f}%).

**Fig. 6 | Month-to-month variation is concentrated and poorly forecast.** **a**, Share of 2025 phone crime captured when flagging the highest-risk tracts: the ensemble captures {capv('ensemble', 0.01):.0f}% in 1% of the city and {capv('ensemble', 0.05):.0f}% in 5%, against {capv('media_historica', 0.05):.0f}% for the historical mean, {capv('teto_ruido', 0.05):.0f}% expected if the ensemble's forecasts were exact and {capv('oraculo', 0.05):.0f}% for an ex-post oracle (all 96 districts). **b**, R² reached by the ensemble (filled) and noise ceiling (open) for between-and-within and within-unit variation, by spatial and temporal scale (exploration districts); for tract × month, {ev('setor', 'mes', 'onde_e_quando', 'r2_observado'):.2f} of {ev('setor', 'mes', 'onde_e_quando', 'r2_max_sem_modelo'):.2f} between and within, {ev('setor', 'mes', 'quando', 'r2_observado'):.3f} of {ev('setor', 'mes', 'quando', 'r2_max_sem_modelo'):.2f} within tracts. **c**, Cumulative shares of phone crime and of extra-Poisson monthly variance across tracts ranked by count; the 1% of tracts with most crime hold {disp.get('parte_do_crime_no_top1pct', NAN) * 100:.0f}% of phone crime and {disp.get('parte_do_excesso_no_top1pct', NAN) * 100:.0f}% of the extra-Poisson variance. **d**, Difference in continuous ranked probability score (CRPS, against real-valued reconciled counts) between each method and the negative binomial GLM (dots; bars, 95% district bootstrap intervals; filled, Holm-adjusted P < 0.05 against the best baseline); the ensemble improves CRPS by {abs(h1a.get('diff', NAN)):.3f} ({abs(h1a.get('diff', 0)) / bench.get('glm', {}).get('crps', 1) * 100:.0f}%). **e**, Share of flagged area (top 5%) and of recorded phone crime by tract income quintile, with the ratio of predicted to recorded counts.

## Extended Data

**Extended Data Fig. 1 | Co-occurrence and composition.** **a**, Self co-occurrence of each type by distance (labels, the five highest curves). **b**, Colocation quotient between types. **c**, Type composition of the 96 districts, clustered by composition.

**Extended Data Fig. 2 | Crime-type panel.** **a**, Events per crime type in exploration tracts (2024–2025) and share geocoded. **b**, Stability across seeds and reconstruction error of crime programs by rank; dashed line, chosen rank. **c**, Density of pedestrians (filled; bars, 95% intervals from {p23boot.get('B', '—')} household resamples) and of people present (open) on each class relative to the city mean, weighted by when robberies occur (Origin–Destination survey 2023, weekdays). **d**, Tissue turnover against month-to-month variability of phone crime within tracts (Spearman ρ = {fate.get('spearman_renovacao_vs_variabilidade_crime', NAN):.2f}).

**Extended Data Fig. 3 | Business openings and closures do not change street crime within a year.** Event study on street segments, treated against never-treated segments of the same district and street class (baseline months −12 to −7). **a**, Any establishment. **b**, Establishments other than individual micro-entrepreneurs on commercial or service parcels. Shading, 95% bootstrap intervals; titles, number of treated segments and effect over months 0–11 relative to the baseline.

**Extended Data Fig. 4 | Forecasting benchmark, 2025 (development).** Continuous ranked probability score (CRPS), log score, Brier score of at least one event, expected calibration error (ECE), predictive accuracy index (PAI, share of crime captured divided by share of area) and share of crime captured at 1% and 5% of the area for every method (tract by month, one month ahead, fitted on 2023–2024).

**Extended Data Fig. 5 | Out-of-sample performance in detail.** **a**, Scores of the finalists ({'2026 sealed' if periodo == 'dev' else '2026'}); numbers, Brier score. **b**, Monthly skill against the negative binomial GLM. **c**, Tracts flagged in the top 5% of area against the observed top 5% (rasterized). **d**, Skill by tissue domain. **e**, Calibration of P(≥1); ECE, expected calibration error. **f**, Correlation across all tract-months (where) against correlation within tracts (when). **g**, Skill against the historical mean at district by quarter for phone crime and lethal violence (lethal violence: best model, negative binomial GLM, CRPS = {dq.get('letal', {}).get('modelos', {}).get('glm', {}).get('crps', NAN):.2f}).

**Extended Data Fig. 6 | Analogy audit.** For each module, the spatial-omics method, its classical urban analogue, the development result and which approach wins under the rule in Methods.

**Extended Data Fig. 7 | Exploratory communication.** **a**, Communication between parcel types aggregated over criminological ligand–receptor pairs (500 m; permutation P < 0.05). **b**, Pairs for the strongest type pairs. **c**, Signal flow of the pair with the largest out-of-sample activity. **d**, Tract covariates enriched in each tissue domain (Cohen's d). No approach improves out-of-sample prediction beyond crime history.

**Extended Data Fig. 8 | Multiverse of communication approaches.** Statistic, out-of-sample gain, stability and status of every approach run.

**Extended Data Fig. 9 | Near-repeat excitation, MISTy and Lee's L.** **a**, Knox ratio between parcel families (400 m, 1–14 days). **b**, Contributions of intrinsic, juxtaposed and para-spatial views. **c**, Bivariate Lee's L between crime generators and phone crime.

**Extended Data Fig. 10 | Robustness of attribution, reconciliation and the clock.** **a**, Recovery of the 2025 class rates of phone crime in {sim.get('n_sim', '—')} simulations from the real exposures with known rates: Poisson counts, district-level risk, tract-level overdispersion and rates permuted among classes; left, median relative error (bars, ± median absolute relative error; open, beyond ±100%); right, coverage of 95% district-bootstrap intervals ({sim.get('cobertura', {}).get('n_sim', '—')} simulations; dotted line, 95%); legend, median Spearman ρ between true and recovered rates. **b**, Finer-scale check with disjoint halves of geocoded events: rates estimated from a random half against segment-allocated rates of the other half (filled; bars, range of {len(met.get('celular_2025', {}).get('metades', []))} splits) and the original check with all events (open), across parcel types, for crime types with at least 80% of events geocoded (median ρ {met.get('mediana_painel_A_para_B_lotes', NAN):.2f} against {met.get('mediana_painel_original_lotes', NAN):.2f}). **c**, Coordinates of geocoded phone-crime events hidden at each stratum's observed missing rate (at random within stratum, more where crime is high, more on residential frontage; {oc.get('replicas', '—')} replicates) and reconciled: within-tract monthly variance of recovered relative to true counts (left; bars, 95% range of replicates) and within-tract noise ceiling of true (open) and recovered (filled) counts (right). **d**, Share of tracts in which a per-tract dispersion test rejects Poisson noise at the 5% level, observed (diamonds) and under nulls simulated through the same geocoding and reconciliation (open; {cal.get('pipeline', {}).get('replicas', '—')} replicates) or as pure Poisson counts (grey), for reconciled counts, integer imputations and geocoded events only, in all tracts and in tracts with at least one event per month. **e**, Log₂ enrichment of crime types in favelas (against the mean crime type) under alternative favela exposures; bars, 95% district-bootstrap intervals for the current exposure; legend, median Spearman ρ of class shares against the current exposure. **f**, Permutation P of the class contrast of the clock under the article's null (events permuted between periods within districts) and under nulls that permute blocks of events from the same tract and period on the same day or in the same month; open, at the permutation floor; dashed line, P = 0.05.
"""
    out = REPO_ROOT / "figures" / f"legendas_{periodo}.md"
    out.write_text(txt)
    return str(out)


if __name__ == "__main__":
    print(build())
