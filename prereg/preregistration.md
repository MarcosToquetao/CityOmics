# Pre-registration — Borrowed-science forecasting of urban crime in São Paulo, and a spatial-omics atlas of the city

**Template:** OSF *Preregistration for secondary data analysis* (van den Akker et al., 2021), adapted.
**Status:** DRAFT v0.1 (2026-10-14). To be registered on OSF by **2026-10-31**, before the prospective window opens (D32).
**Authors:** [fill in: name(s), affiliation, supervisor]
**Project repository:** https://github.com/MarcosToquetao/CityOmics (private until publication). Design documents: `spec-overview.md`, `spec-dados.md`, `spec-benchmark.md`, `spec-atlas.md`. Decision IDs (Dn) refer to the Decisions Log in `spec-overview.md`.

---

## 1. Study information

### 1.1 Title
Borrowed-science forecasting of urban crime in São Paulo: a pre-registered benchmark and a spatial-omics atlas of the city.

### 1.2 Research questions
- **RQ1.** Do forecasting methods developed in other sciences outperform strong crime-forecasting baselines in out-of-sample spatio-temporal prediction of victim-reported crime in São Paulo? The fields are seismology (ETAS/Hawkes), epidemiology (Bayesian disease mapping), ecology (maximum-entropy species distribution models), physics/astronomy (log-Gaussian Cox processes, correlation functions), econometrics (spatial panels/GWR) and machine learning.
- **RQ2.** Does a compact, calibrated typed-decision model (Laya), fed with serialized representations from those methods, produce better probabilistic forecasts than a gradient-boosting model fed with exactly the same information?
- **RQ3.** Do representations built with spatial-transcriptomics methods improve 2026 forecasts beyond the best benchmark model? Here urban lots are treated as cells, census tracts as spots, and representations include lot types, niche composition and spatial domains, all fitted on data up to 2025.
- **RQ4.** Can the semester-to-semester transitions of urban lot types ("cell fate") be predicted better by the decision model than by a Markov transition baseline?

### 1.3 Hypotheses (confirmatory)

| ID | Hypothesis | Outcome / unit | Primary metric | Direction |
|---|---|---|---|---|
| H1a | The best cross-domain model beats the best baseline | Cellphone robbery/theft, census tract × month, h = 1 | Mean CRPS (negative binomial) | Cross-domain lower |
| H1b | Same comparison as H1a | Same | PAI at 1% of city area | Cross-domain higher |
| H2 | Laya-FT on the compressed state beats LightGBM on the identical compressed state | Same | Brier score for P(count ≥ 1) | Laya-FT lower (two-sided test) |
| H3 | Adding atlas features (fitted ≤ 2025) to the best benchmark model improves it | Same | Mean CRPS | With atlas lower |
| H4 | Laya-FT predicts lot-type transitions better than a Markov baseline (type × niche) | Lot, 2025-S2 → 2026-S1, among lots that change type | Multiclass log-loss | Laya-FT lower |

"Best cross-domain model" and "best baseline" are each the single model with the lowest CRPS (H1a) or highest PAI@1% (H1b) on the 2025 tuning period, chosen within its class before 2026 is unsealed (§5.2). The selected model identities will be recorded as a timestamped amendment before unsealing.

### 1.4 Secondary and exploratory analyses (not confirmatory)
- Lethal violence (composite and strict CVLI), district × quarter, **power-limited** (§4.4).
- Horizons h = 3 and h = 6 months.
- PAI/PEI curves at 0.5–10% of area; log score; calibration (randomized PIT, reliability, ECE).
- Ablations: each cross-domain family removed; crime history removed (D6); real place names added to the Laya state (prior-knowledge probe, D24); theory-driven vs data-driven covariate sets (D12).
- Equity audit: hit rate, calibration and flagged area by tract income quintile and racial composition (Census 2022).
- Atlas modules (typing vs k-means/OAC, attribution by lot type with point-level validation, niches/domains vs colocation quotient/SKATER/max-p, spatially variable features vs Moran's I) are **descriptive**, with pre-specified baselines (spec-atlas §3).

---

## 2. Data description

### 2.1 Datasets
| Dataset | Content | Period used |
|---|---|---|
| SSP-SP *SPDadosCriminais* | Police occurrence records (BO × offence), state of São Paulo, filtered to the capital by place of occurrence | 2022–2026 |
| SSP-SP *CelularesSubtraidos* | Cellphone robbery/theft records (object × BO) | 2022–2026 |
| SPSafe (doi:10.5753/dsw.2023.233945); CEM-USP police-district series | Historical lethal violence | 2003–2022 / 2000–2020 |
| IBGE Census 2010/2022 (tract aggregates, 200 m grid, CNEFE, FCU), IPVS, GeoSampa (lots, IPTU/TPCL cadastre), ITBI transactions, CNPJ establishments, VIIRS Black Marble C2, Metrô ridership, OpenStreetMap/ohsome, SP156 complaints, BCB branches/ATMs, INMET/CGE weather, calendar | Covariates ("genes") | Per source (spec-dados §3) |

Download dates and SHA-256 checksums of every raw file will be frozen in `data/snapshot.json` (D18). Its hash will be reported in an amendment.

### 2.2 Units of analysis (D13)
- **Lot** (fiscal lot, IPTU; favelas as FCU pseudo-lots): atlas "cell", fate target.
- **Census tract 2022** (~27k): cellphone outcome, atlas "spot".
- **District** (96): lethal-violence outcome.

### 2.3 Outcomes
- **Cellphone:** consummated robbery or theft of cellphones in the capital, deduplicated by BO (key: police station, BO year, BO number, highest version). Counted by date of occurrence and assigned to tracts. Non-geocoded records are allocated by place-type-stratified hierarchical reconciliation (D16, D27).
- **Lethal violence (composite, D20):** intentional homicide + attempted homicide + robbery-homicide (latrocínio) + bodily injury followed by death. Traffic-related categories are excluded. **Strict CVLI** omits attempts.
- **Lot type at semester s:** Leiden cluster of native lot features. These are stocks of active establishments by economic activity, last ITBI price per m² carried forward, time since last transaction, SP156 complaints nearby, and the previous year's IPTU attributes as lagged context (D23). Clusters are fitted on semesters up to 2025-S2 and projected onto 2026-S1.

### 2.4 Excluded data
- SSP domestic-violence base (D14).
- Police-initiated offences (drug trafficking, weapon possession), because they measure enforcement rather than victimization.
- Occurrence dates before 2003 or invalid.

---

## 3. Knowledge of the data (prior exposure)

We declare the following exposure honestly. It is the reason for the prospective confirmation window (D26).

1. **2026 crime data have been seen in aggregate form.** The first author maintains a public website (MapaSegurancaSP) that displays 2026 crime counts by district and month. During project design (2026-10-14), an automated audit of the local data reported monthly 2026 counts (Jan–Jul) and January–July 2026 vs 2025 changes. Robbery fell about 14%, vehicle robbery about 34%, and intentional bodily injury rose about 11%. It also showed that geocoding coverage rose from ~80% to ~90% from April 2026.
2. **No model has been fitted, tuned or evaluated on 2026 data.** No tract-level or lot-level 2026 outcome has been computed.
3. **2022–2025 data have been explored** for data-quality auditing (schema changes, duplication, geocoding coverage, reporting lags) and for the power analysis (§4.4).
4. **No 2026 covariate-derived target** (lot types in 2026-S1) has been computed.

**Safeguards.**
- From F1 onward, all 2026 outcome records go to a software-enforced vault (`cityomics.sealed`). Reading it requires the OSF DOI in a versioned file plus an explicit session flag, and every access is logged with timestamp, purpose and git commit.
- The prospective window (§5.5) consists of data that do not exist at registration time.

---

## 4. Variables and sample

### 4.1 Predictors
- **Covariate pool T1 + T2:** ~150–300 variables (spec-dados §3).
- **Pre-specified theory-driven core (D12):**
  - routine activity: Metrô ridership potential, commercial and bar establishments (CNPJ), OSM POIs;
  - social disorganization: IPVS, head-of-household income, Census Δ2010→2022;
  - CPTED: street lighting in the census surroundings module, VIIRS radiance, sidewalks;
  - land market: ITBI volume and price.
- **Data-driven selection:** SHAP/permutation importance and stability selection, run on 2022–2025 only with spatially and temporally blocked CV.
- **All availability-dated (as-of):** a record or covariate feeds month m only if it was available before the start of m, using the registration date for BOs and the publication lag for covariates.

### 4.2 Temporal split
- **Training:** 2022–2024; lethal violence extended back via SPSafe/CEM (D15).
- **Tuning:** 2025, with rolling-origin, expanding windows.
- **Final fit:** 2022–2025, after which all parameters are **frozen**.
- **Validation (primary test):** January–September 2026.
- **Prospective confirmation:** November 2026–March 2027.
- **Forecast protocol (D25):** parameters stay frozen through 2026. Model inputs (lags, rolling covariates) are updated each month with data available before that month. No refitting.

### 4.3 Sample sizes
- **Cellphone:** ~27,000 tracts × 9 months ≈ 243,000 tract-months (validation) and ≈ 135,000 (prospective, 5 months). Around 160,000 BOs per year.
- **Lethal violence:** 96 districts × 3 quarters = 288 district-quarters (validation). Composite ~1,180–1,320 events per year in 2022–2025.
- **Lot fate:** all fiscal lots (~1.5 million, to be confirmed) for baselines. For Laya, all lots that change type plus an equal-size stratified sample of non-changers, with inverse-probability weights.

### 4.4 Power analysis (lethal violence)
- **Method:** pseudo-out-of-sample, 2022–2025 data only.
- **Proxy unit:** police-station areas (94), similar in size to the 96 districts.
- **Analog test window:** January–September 2025, h = 1 (282 cells).
- **Comparison:** an 8-quarter mean model vs persistence, both negative binomial with dispersion estimated on history. The standard error of the mean score difference comes from a cluster bootstrap over units (2,000 replicates).
- **Minimum detectable difference** (α = 0.05 two-sided, power 0.80):

| Outcome | Mean events per cell | MDE, log score (3 quarters) | MDE, CRPS (3 quarters) | MDE, CRPS (prospective quarter only) |
|---|---|---|---|---|
| Composite | 3.59 | 11.5% of baseline | 20.7% | 35.8% |
| Strict CVLI | 1.53 | 12.7% | 20.8% | 36.0% |

- **Implication:** comparisons among competitive models for lethal violence can only detect large differences. Lethal violence is therefore **secondary**, and its prospective window is **descriptive only**.
- **Caveat:** the MDE uses the dispersion of differences between two quite different models. Differences between closer models are usually less variable, so these MDEs are conservative. Code and output: `prereg/analysis/`.

The cellphone outcome has two to three orders of magnitude more cells, so no power limitation is anticipated for H1–H3.

---

## 5. Analysis plan

### 5.1 Models

**Baselines:**
- persistence (t−1);
- seasonal naive (same month last year);
- historical mean;
- space-time kernel density;
- prospective hotspotting;
- negative-binomial GLM with temporal and spatial lags.

**Cross-domain families:**
- ETAS/Hawkes with covariates;
- BYM2 / Knorr-Held space-time models (R-INLA);
- near-repeat (Knox) features;
- MaxEnt with target-group background;
- log-Gaussian Cox process (SPDE);
- spatial panel / GWR;
- LightGBM (Poisson/Tweedie) with spatial and temporal lags;
- Chronos/TimesFM zero-shot;
- spatio-temporal GNN;
- stacked ensemble.

**Decision layer (D24):**
- **Laya-FT:** `laya-typed-decisions` (ModernBERT-large, 421M parameters, 1,024-token context), weights pinned by hash. Fully fine-tuned with RLCD on 2022–2024 and isotonic-recalibrated on 2025. This is the primary arm.
- **Laya-ZS:** zero-shot plus the same recalibration, as reference.
- **Input:** a serialized English state with anonymized unit IDs. It contains atlas type/domain, top-10 marker z-scores, niche composition, 3/6/12-month crime trends, cross-domain scores and calendar.
- **Comparator:** LightGBM receives the full features and, separately, the identical compressed state (the H2 comparator).

**Fate models (H4):**
- Markov by type × niche (baseline);
- CellRank fate probabilities;
- multiclass LightGBM;
- Laya-FT/ZS (`choice` over K ≤ ~20 types).

### 5.2 Model selection before unsealing
- All hyperparameters, feature sets, ensemble weights and the "best in class" models for H1 are chosen on 2025.
- The frozen model files are hashed, and the hashes plus selected identities are posted as a timestamped amendment.
- Only then is the vault opened.

### 5.3 Metrics
- **Probabilistic:** CRPS (NB closed form), log score, Brier for P(≥ 1) with decomposition. Scores are also reported on non-zero cells only.
- **Operational:** hit rate, PAI and PEI at 0.5/1/2/5/10% of area.
- **Calibration:** randomized PIT histograms, reliability diagrams, ECE (overall and by group).
- **Fate:** P(change) Brier/AUC; among changers, log-loss and macro-F1. Reported separately for activity-driven and cadastre-driven transitions (D23).

### 5.4 Inference
- **Tests:** paired differences (Diebold–Mariano style) with a **cluster bootstrap by district** (2,000 replicates). Districts are resampled with all their cells and months, which preserves spatial and temporal dependence. For H4, the bootstrap clusters are tracts.
- **Multiplicity:** **Holm** correction across the five confirmatory tests (H1a, H1b, H2, H3, H4) at family-wise α = 0.05.
- **Support criterion:** a hypothesis is supported if the Holm-adjusted p < 0.05 in the stated direction. For H2 the test is two-sided, and either direction is reported.
- **Effect sizes:** mean differences with 95% bootstrap CIs, also reported month by month for 2026.

### 5.5 Prospective confirmation
- **What is re-tested:** H1a, H1b and H3, using cellphone data from November 2026 to March 2027 with the frozen models.
- **When:** after SSP publication plus a 60-day settling period for late reports (expected around June 2027).
- **Confirmation criterion:** the 95% CI of the difference excludes zero in the same direction as in the validation test.
- **Lethal violence:** prospective results are descriptive only (§4.4).

### 5.6 Missing data and data quality
- **Non-geocoded records** are handled by stratified reconciliation (D27); ranking metrics are also reported without reconciliation.
- **Covariates missing for a unit** (e.g., suppressed Census cells) are imputed using training-period values only, and a missingness indicator is added.
- **Reporting lag:** under the as-of rule, the most recent month is never used as fully observed input.

### 5.7 Deviations
- Before unsealing, changes are recorded as dated amendments in `prereg/AMENDMENTS.md` and on OSF.
- After unsealing, any change is reported as a deviation, alongside the pre-registered result.
- If Laya fine-tuning proves infeasible, H2/H4 use Laya-ZS with recalibration, reported as a deviation.

---

## 6. Ethics and data protection
- **Framing:** prevention, urban planning and victim services; no patrol-dispatch tool and no individual-level prediction (D11).
- **Data custody:**
  - BO numbers, addresses and coordinates stay on the authors' local machine;
  - only aggregated or anonymized matrices are uploaded to cloud GPU (Google Colab);
  - no data are sent to hosted language-model APIs (D7, D24, D30).
- **Publication:** public outputs are aggregated, and lethal violence is mapped only as smoothed rates.
- **Retention:** raw microdata are deleted five years after the last publication (D14).
- **Ethics review:** [fill in: institutional ethics committee decision or exemption, since the source data are public administrative records].

---

## 7. Timeline
| Date | Milestone |
|---|---|
| 2026-10-31 | Registration on OSF (this document) |
| Nov 2026 – Feb 2027 | Pipeline, tuning on 2025, atlas; amendments recorded |
| before unsealing | Amendment with snapshot hash, frozen model hashes and selected best-in-class models |
| ~Mar 2027 | Single unsealing of 2026; validation results |
| ~Jun 2027 | Prospective data settled; confirmation results |
