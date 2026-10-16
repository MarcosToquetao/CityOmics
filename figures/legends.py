"""Legendas das figuras no estilo Nature (D46), com os números lidos dos resultados.

Gera ``figures/legendas_<periodo>.md`` (inglês). A primeira frase de cada legenda, em negrito, é a
conclusão da figura; as demais descrevem os painéis e as estatísticas.
"""

from __future__ import annotations

import json

import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import REPO_ROOT, processed_dir


def _j(path):
    return json.loads(path.read_text()) if path.exists() else {}


def build(periodo: str = "dev") -> str:
    a = atlas_dir()
    tip = _j(a / "tipagem_2025.json")
    att = _j(a / "atribuicao_celular_2025.json")
    var = _j(a / "variancia_2025.json")
    fate = _j(a / "destino.json")
    dom = _j(a / "dominios_2025.json")
    bench = _j(processed_dir() / "modelo" / "resultados_benchmark_dev.json").get("resultados", {})
    sel = _j(REPO_ROOT / "prereg" / "selection_dev.json")
    dq = _j(processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json")
    lam = pl.read_parquet(a / "atribuicao_celular_2025.parquet") if (a / "atribuicao_celular_2025.parquet").exists() else None
    cap = pl.read_parquet(processed_dir() / "figdata" / f"fig5_captura_{periodo}.parquet") if (processed_dir() / "figdata" / f"fig5_captura_{periodo}.parquet").exists() else None

    def capv(curva, area, alvo="n_total"):
        if cap is None:
            return float("nan")
        return float(cap.filter((pl.col("curva") == curva) & (pl.col("area") == area) & (pl.col("alvo") == alvo))["captura"][0]) * 100

    def lamv(c):
        if lam is None:
            return float("nan")
        r = lam.filter(pl.col("classe") == c)
        return float(r["lambda"][0]) if r.height else float("nan")

    h1a = sel.get("h1a", {})
    n_tipos = tip.get("n_tipos", "—")
    stab = tip.get("estabilidade", {}).get("0.02", {}).get("ari_medio", float("nan"))
    txt = f"""# Figure legends ({periodo})

**Fig. 1 | São Paulo read as a tissue.** **a**, Correspondence between spatial transcriptomics and the city: parcels are cells, census tracts are spots, streets and stations are the interstitium and vessels, neighbourhood composition is the niche, crime generators and targets play the role of ligand–receptor pairs and crime is the phenotype. **b**, 1.65 million fiscal parcels coloured by type (Leiden on 30 native parcel attributes from the 2025 property-tax cadastre and the December-2025 business registry, linked by address), with census favelas (IBGE FCU) as pseudo-cells; rail lines and water bodies as landmarks. **c,d**, Parcel-resolution views of the centre (**c**) and of a periphery where a favela abuts high-rise condominiums (**d**), with census-tract outlines (white). No crime data are shown. Scale bars, 10 km (**b**) and 500 m (**c,d**).

**Fig. 2 | Parcel types and their marker attributes.** **a**, UMAP of 150,000 parcels coloured by type. **b**, Marker attributes per type (dot size, fraction of parcels expressing the attribute; colour, mean standardized value). **c**, Spot (census-tract) composition as pie charts in the centre, analogous to spot deconvolution. **d**, Type composition of the 96 districts, clustered by composition. **e**, Typing stability across subsamples (adjusted Rand index) as a function of the number of types; the selected resolution (orange; {n_tipos} types, ARI = {stab:.3f}) was fixed without any crime data; dashed line, agreement with an OAC-style k-means baseline (ARI = {tip.get('ari_kmeans_vs_leiden', float('nan')):.2f}).

**Fig. 3 | Tissue architecture: niches and communication.** **a**, Neighbourhood enrichment between parcel types (z-scores against 100 permutations restricted to district × population-density decile). **b**, Tissue domains: tract composition smoothed over contiguous neighbours and clustered (k = {dom.get('k', '—')}, chosen by silhouette). **c**, Tract covariates enriched in each domain (Cohen's d). **d**, Sender → receiver communication between types (CellChat-style), aggregating criminological ligand–receptor pairs (generator in the sender tract, vulnerability in the receiver tract; exponential kernel, ℓ = 500 m; pairs with permutation P < 0.05). **e**, Ligand–receptor pairs for the strongest type pairs (size, −log10 P; colour, strength). **f**, Signal flow of the pair with the largest out-of-sample activity (COMMOT-style streamlines). Exploratory analyses; the full multiverse of approaches is in Extended Data Fig. 2.

**Fig. 4 | The tissue predicts where crime occurs.** **a**, Phone-theft rates attributed to each cell class (parcel types per km of street frontage, street classes per km, 2025), from a Poisson model in which each tract's count is the sum of what its cells produce (EM estimation; 95% intervals from 500 district bootstrap resamples); medium-standard street retail ({lamv('Comércio de rua médio'):.0f} thefts km⁻¹ yr⁻¹) and high-rise mixed parcels ({lamv('Vertical residencial e misto'):.0f}) dominate, low-rise residential parcels are near zero; each rail station adds {lamv('n_trilho'):.0f} thefts per year. **b**, Point validation: attributed rate against the rate observed by linking geocoded thefts to the nearest street segment and its abutting parcels (Spearman ρ = {att.get('spearman_validacao_pontual', float('nan')):.2f}). **c**, Out-of-sample R² of the 2025 tract theft rate (district-blocked cross-validation): parcel types {var.get('r2_tipos', float('nan')):.2f}, the same parcel attributes without typing {var.get('r2_genes_sem_tipagem', float('nan')):.2f}, tissue (types, domains, streets) {var.get('r2_tecido', float('nan')):.2f}, tissue plus tract covariates {var.get('r2_tecido_mais_covariaveis', float('nan')):.2f}, historical mean {var.get('r2_media_historica', float('nan')):.2f}; between-tract share of variance (ICC) = {var.get('icc_2025', float('nan')):.2f}. **d**, Decomposition of expected 2025 thefts by theoretical covariate group and cell class (exact Shapley values against the average tract; reductions shown as a hatched sink). **e**, Mean |SHAP| of the gradient-boosting predictors grouped by theory. **f**, Annual transition rates between parcel families from the property-tax cadastre, 2012–2025 (2021 excluded); permanence = {fate.get('permanencia_media', float('nan')) * 100:.1f}% per year. All crime analyses exclude 19 districts held out as a spatial vault.

**Fig. 5 | When: how much do methods borrowed from other sciences add?** **a**, Difference in CRPS against the NB-GLM baseline for each method in 2025 (dots, mean; lines, 95% district-cluster bootstrap intervals; filled, Holm-adjusted P < 0.05). The best cross-domain model (graph neural network) improves CRPS by {abs(h1a.get('diff', float('nan'))):.3f} ({abs(h1a.get('diff', 0)) / bench.get('glm', {}).get('crps', 1) * 100:.0f}%). **b**, Share of thefts captured when flagging the highest-risk tracts: the ensemble captures {capv('ensemble', 0.01):.0f}% in 1% of the city and {capv('ensemble', 0.05):.0f}% in 5%, against {capv('media_historica', 0.05):.0f}% for the historical mean, {capv('teto_ruido', 0.05):.0f}% expected if the model were the truth (noise ceiling) and {capv('oraculo', 0.05):.0f}% for an ex-post oracle. **c**, Correlation across all tract-months (where) against within-tract correlation (when). **d**, Calibration of P(≥1 theft). **e**, Tissue turnover against month-to-month variability of thefts within tracts (Spearman ρ = {fate.get('spearman_renovacao_vs_variabilidade_crime', float('nan')):.2f}). **f**, CRPS skill against the historical mean at district × quarter for phone theft and lethal violence (lethal: best model NB-GLM, CRPS = {dq.get('letal', {}).get('modelos', {}).get('glm', {}).get('crps', float('nan')):.2f}; no model beats it).

**Fig. 6 | Out-of-sample performance and equity.** **a**, CRPS of the finalists ({'2025 development; 2026 sealed until the freeze' if periodo == 'dev' else '2026 test'}); numbers above bars, Brier score of P(≥1). **b**, Monthly CRPS skill against the NB-GLM. **c**, Tracts flagged by the ensemble in the top 5% of the city's area against the observed top 5% (annual; rasterized). **d**, Ensemble skill by tissue domain (vault districts excluded). **e**, Share of flagged area and of observed thefts by tract income quintile, with the ratio of predicted to observed thefts. **f**, Prospective window (November 2026–March 2027), forecasts frozen before outcomes exist.
"""
    out = REPO_ROOT / "figures" / f"legendas_{periodo}.md"
    out.write_text(txt)
    return str(out)


if __name__ == "__main__":
    print(build())
