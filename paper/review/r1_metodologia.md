# Peer Review Report: Reviewer 1 (Methodology)

- **Title**: Crime as a phenotype of urban tissue
- **Venue**: Nature Cities (Article)
- **Review date**: 2026-10-19
- **Review round**: Round 1 (development-stage manuscript, 77 exploration districts; confirmation pending)
- **Phase 1 commitment**: `paper/review/r1_metodologia_fase1.md`

contract_role: methodology

## Dimension Scores

### D1: methodology_rigor
score: block
trigger: "At least one headline result rests on an analysis whose key identification assumption is unstated or untested in a way that could plausibly reverse or substantially change the claim, or on a validation that reuses the information it is meant to test"
block_class: repairable

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: block
trigger: "A load-bearing claim in the abstract or main conclusions is not supported by, or is contradicted by, the statistic offered for it, or the argument depends on a reasoning step such as circular validation or reading non-significance as confirmation"
block_class: repairable

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

### Reviewer Information

**Role**: Peer Reviewer 1 (Methodology).
**Identity**: Spatial statistician and quantitative criminologist working on count models, ecological inference, permutation tests, staggered difference-in-differences and forecast evaluation (proper scoring rules, cluster bootstrap, multiple testing, preregistration).
**Focus**: Whether each statistic supports the sentence that uses it, whether the identification assumptions behind the attribution, clock, memory and predictability analyses hold, and whether the Methods are enough to replicate every Result. I also flag methods that are missing and methods that the story does not need.

### Overall Assessment

**Recommendation**: Major Revision.
**Confidence score**: 4. The work falls within my core expertise. I hold back from 5 because some of my concerns are inferred from Methods wording that the authors can clarify.
**Calibration status**: `NOT_CALIBRATED`

**Summary assessment.** The manuscript models tract-level police counts in São Paulo as Poisson sums of class-specific rates over 19 parcel and street classes. From this it derives crime signatures across 15 phenotypes, period-of-day clocks normalised by survey-based ambient population, a variance decomposition into tissue, persistent residual and transient parts, a staggered event study, and a Poisson-based predictability ceiling with a 12-method forecasting benchmark. The design has real safeguards: parcel types are fixed without crime data, there is a spatial and a temporal vault, intervals use a district block bootstrap, scoring rules are proper, and null results are reported honestly. Several headline claims, however, rest on steps that are not yet sound. The point validation reuses the geocoded events that make up most of the fitted counts. Non-geocoded events are allocated using each tract's previous-year geocoded pattern, which builds persistence and smoothness into the series used for the memory and noise claims. The attribution's assumption of one homogeneous rate per class across the city is never tested. The 96% Poisson result is mostly a power artefact read as confirmation. The concentration of variance in hubs is what scale alone predicts. The text says the city is close to its limit of predictability, but the within-tract ceiling shows the opposite. The robbery clock that leads the abstract is the weakest result and is not part of the confirmatory family. Every one of these can be repaired with re-analysis and reframing, and none is fatal. Together they warrant blocks on D1 and D3 until they are addressed.

### Judgements against the Phase 1 scoring plan

**D1 methodology_rigor: block (repairable).** Among the Phase 1 look-for items, the following are met: typing blind to crime, block bootstrap by district, cross-validation blocked by district, proper scoring rules with Holm correction, an MDE reported for the event study, and a vault design. The following are not met: identification assumptions of the attribution stated and probed (W3); validation independent of the fitted attribution (W1); a permutation unit that matches the dependence structure (W7); non-rejection backed by power or equivalence reasoning (W4); a variance decomposition with a unique estimand and intervals (W9); handling of non-geocoded events that does not contaminate downstream analyses (W2); and an MDE interpreted correctly (W12). The block trigger is met because several headline results rest on untested assumptions, and in one case on a validation that reuses its input. The fatal trigger is not met: the target quantities are identifiable from these data and every defect can be repaired within a revision.

**D3 argumentative_coherence: block (repairable).** The block trigger is met by four statements. The Discussion presents the point validation as using data the analyses did not use (W1). The abstract and a section title read 96% non-rejection as Poisson noise (W4). The predictability conclusion is contradicted by its own within-tract ceiling (W6). The abstract's headline clock example comes from a non-confirmatory result that failed in one of two years (W8). The fatal trigger is not met: the central thread (composition, then persistence, then limited monthly forecastability) is internally consistent and can be repaired by reframing plus the analyses below.

### Strengths

### S1: A two-vault confirmatory design with pre-specified Holm-corrected claims
A spatial vault of 19 districts and a temporal vault for 2026 are sealed behind a software key, frozen models carry commit hashes, and the confirmatory family is fixed in advance. This is rare in urban crime research and directly limits the analytic flexibility that weakens most atlas-style studies.
**Evidence Anchor**: text: Methods, Study design and safeguards "Two vaults protect confirmatory tests."

### S2: The typology is built without outcome data
Parcel types are derived from cadastral and registry attributes alone, which removes the most common circularity in place-based crime typologies (clusters tuned to separate crime). The stability selection by ARI across subsamples is a sound way to choose the resolution.
**Evidence Anchor**: text: Methods, Study design and safeguards "Parcel types were fixed without crime data before attribution."

### S3: Uncertainty and validation respect spatial dependence
Intervals come from a district block bootstrap and out-of-sample R² uses cross-validation blocked by district. Both are appropriate for spatially autocorrelated counts and avoid the inflated precision that tract-level resampling would give.
**Evidence Anchor**: text: Methods, Composition-aware attribution "Intervals come from 500 bootstrap resamples of districts."

### S4: Forecasts are evaluated with proper scoring rules against strong baselines
Every model issues a full predictive distribution scored by CRPS, log score and Brier score. Hit rates at 1% and 5% of area are reported, a negative binomial GLM and the historical mean serve as baselines, and comparisons use Holm correction. This is the correct way to evaluate probabilistic crime forecasts.
**Evidence Anchor**: text: Methods, Forecasting benchmark "All forecasts were negative binomial and scored by the continuous ranked probability score"

### S5: Unfavourable results are reported
The paper states plainly that typing does not beat raw attributes, that the best model does not improve capture at 1% of area, and that ligand–receptor-style and interaction models lose to simpler spatial models. This candour makes the positive results more credible.
**Evidence Anchor**: text: Results, Stable tissue "Parcel types (R² = 0.22) did not outperform the same attributes without typing (0.26)"

### S6: A rival explanation for the clock is tested explicitly
Normalising by survey-based ambient population, with people present and pedestrians on the street kept separate, directly addresses the obvious objection that class clocks just track crowds.
**Evidence Anchor**: text: Results, The tissue keeps a clock "A clock of this kind could simply track the number of potential victims."

### S7: A positive control is included
Traffic injuries peaking on arterial streets show that the attribution can recover a known spatial pattern.
**Evidence Anchor**: text: Results, Each cell class has a crime signature "As a positive control, traffic injuries had their highest rate per km among street classes on arterial streets"

### S8: Forecast skill is anchored to a principled noise ceiling
Comparing achieved R² with the share of variance above Poisson noise is a good idea. It turns "the models are weak" into a question about what is attainable. My concerns (W4–W6) are about interpretation, not the idea.
**Evidence Anchor**: text: Methods, Predictability ceiling and dispersion "because Poisson noise has variance equal to the mean"

### Weaknesses

### W1: Point validation is a cross-scale consistency check, not validation on unused data
**Problem**: The attribution is fitted to reconciled tract counts in which every geocoded event sits in the tract that contains it. The point validation re-allocates those same geocoded events to street segments and abutting parcels. For phone crime in 2025, 100,347 of the 121,434 fitted events (83%) are the validation points themselves, and the remaining 17% were allocated within districts in proportion to geocoded events (W2). Both procedures also share the frontage-proportional assumption: the segment count is split "in proportion to frontage among the parcels within 40 m". Agreement therefore shows that two allocations of one dataset at two scales agree. It does not test the attribution against independent data. The Discussion nevertheless states that the attribution was checked against data the analyses did not use. There are further gaps. Each ρ is computed across about 12 parcel types and reported without an interval. The non-parcel classes that carry several headline signatures (stations, streets, favelas) are not validated. Three phenotypes are untested (phone theft at 78% geocoded, lethal violence 66%, residential burglary 19%; Fig. 3c), yet the Results say validation "held across phenotypes".
**Evidence Anchor**: text: Discussion, first paragraph "The main statements were checked against data that the analyses did not use: geocoded points for the attribution"
**Why it matters**: The abstract offers "which geocoded events reproduce (median Spearman ρ = 0.85)" as the main external support for the attribution. As written, it claims more independence than the design provides.
**Suggestion**: (i) Rewrite the Discussion sentence along the lines of "checked against a finer-scale allocation of the same geocoded events". (ii) Add a genuinely held-out validation. One option: randomly split geocoded events into halves A and B (or alternate months), fit the attribution on tract counts built from A plus non-geocoded events, and validate on B's points. Another: fit on 2024 tract counts and validate on 2025 points. (iii) Report a bootstrap interval for every ρ, together with a reference ρ from attribution fitted to counts permuted across tracts within district. (iv) Restrict the claim to "the 12 phenotypes with at least 80% of events geocoded".
**Severity**: Major
**Confidence**: 5 — core expertise: ecological inference and validation design

### W2: Reconciliation of non-geocoded events builds persistence and smoothness into tract counts
**Problem**: Events without coordinates are allocated to tracts using the previous 12 months of geocoded events in the same stratum. This has three consequences. (a) The allocated part of a tract's count in year t is a deterministic function of its geocoded counts in year t−1, which adds correlation between years. That inflates the "stable memory", the persistence curve (Fig. 5c) and the skill of the historical-mean forecaster. (b) Within a district-month, the allocated part of tract s varies only with the district total N. Its month-to-month variance is about p_s²·Var(N) rather than p_s·N, so it is under-dispersed relative to Poisson and pulls tract dispersion indices towards (or below) 1, which favours the 96% result (W4). (c) For phenotypes with low geocoding (residential burglary 19%, lethal violence 66%; Extended Data Fig. 10a), the signatures are mostly a projection of the geocoded minority. The manuscript itself notes that coordinates are suppressed more often at homes, which is exactly where the burglary signature (+3.4 on medium-standard houses) is reported. The only geocoded-only sensitivity shown is the capture curve in Fig. 6a.
**Evidence Anchor**: text: Methods, Units and reconciliation "events without coordinates were distributed among tracts in proportion to the geocoded events of the same stratum over the preceding 12 months"
**Why it matters**: Three headline results (persistent memory, Poisson-like monthly counts, and the burglary and lethal-violence signatures) could be partly produced by pre-processing.
**Suggestion**: Re-run the memory decomposition, the persistence curve, the dispersion test and the predictability ceiling on geocoded-only counts, and show them next to the current results. Add one alternative allocation as a sensitivity check: the same month, or proportional to the composition model's expected counts. Report the reconciled share by phenotype and year in Methods. State how 2022 events were allocated when no preceding 12 months existed. Mark the burglary and lethal-violence signatures as dependent on reconciliation, or drop them from the list of highlighted examples.
**Severity**: Major
**Confidence**: 4 — core expertise: the direction of bias follows analytically; its size needs the re-analysis

### W3: The attribution model's identification assumptions are not stated or tested
**Problem**: The model assumes one rate per class that applies everywhere in the city, additive contributions, and frontage, street length or station counts as correct exposure measures. Several consequences are never examined. Rates are spatially heterogeneous within classes (retail in the centre versus the periphery). Class rates are confounded by location: stations and high-rise parcels sit in central districts with high baseline risk, so their λ absorbs district-level risk. The 19 exposures are collinear, multiplicative EM can push rates to zero when collinear classes compete, and recovery accuracy is unknown. The manuscript's own numbers show the assumptions are strained: composition explains a third of the deviance, and the stable residual beyond the tissue is 48% of between-tract variance. In other words, rates vary across tracts in ways the model either assigns to classes or treats as noise. Finally, "fitted jointly" for 15 phenotypes is undefined. Unless the phenotypes share structure, the Poisson likelihood factorises and a joint fit is identical to separate fits.
**Evidence Anchor**: equation: Methods, Composition-aware attribution, y_s ~ Poisson(Σ_k E_sk λ_k) with a single city-wide λ_k per class
**Why it matters**: The rates (Fig. 3a), signatures (Fig. 3b), clocks (Fig. 4) and decline ratios (Fig. 5e) are all functions of the λ estimates. If a class's λ partly reflects where that class is located, the ecological fallacy has only moved from tracts to classes.
**Suggestion**: (i) Run a simulation recovery study: generate tract counts from known λ with realistic heterogeneity (district multipliers, overdispersion) and report bias and interval coverage per class. (ii) Refit with multiplicative district or tissue-domain effects, y_s ~ Poisson(θ_d Σ_k E_sk λ_k), and report how stable the λ ranks and enrichments remain. (iii) Report exposure collinearity (condition number or pairwise correlations) and how often each λ hits the zero boundary across bootstrap draws, including the hourly λ used in Fig. 4. (iv) Add one Methods paragraph listing the assumptions. (v) Define "fitted jointly".
**Severity**: Major
**Confidence**: 4 — core expertise: Poisson deconvolution and ecological inference

### W4: "Consistent with Poisson in 96% of tracts" is mostly a power artefact read as confirmation
**Problem**: Each tract is tested on 12 monthly counts with a χ² test on 11 degrees of freedom, and most tracts average about one event a month or fewer. At such means, even large variation in the latent rate gives a small dispersion index, because var/mean = 1 + μ·CV². With μ = 1 per month and a latent month-to-month CV of 0.7, the index is about 1.5, and the test rejects at α = 0.05 only about 30% of the time. At μ = 0.3 power is about 10%. Under a true global Poisson null, about 5% of tracts would reject at α = 0.05. The observed 4% is at or below that level, so the test says almost nothing about most tracts. Rejection rises to 14% among tracts with at least one event per month, which is the gradient expected from constant relative overdispersion as power increases. Neither α nor any multiplicity handling is stated.
**Evidence Anchor**: text: Results, Month-to-month crime is noise "Month-to-month counts were consistent with Poisson noise in 96% of tracts"
**Why it matters**: The abstract, a section title and the Discussion ("what remains from month to month is mostly noise") all rest on this statistic.
**Suggestion**: Replace the count of non-rejections with an estimate. Fit a hierarchical negative binomial or Poisson-lognormal model to tract-month counts (overdispersion may vary by count stratum or class) and report the latent month-to-month CV with an interval. Add a power simulation at the observed means. If a tract-level statement stays, use an equivalence formulation (the share of tracts whose upper 95% bound on the dispersion index falls below a stated margin) with FDR control. Reword the claim, for example: "in most tracts, monthly counts are too small for month-to-month variation to be distinguished from Poisson noise".
**Severity**: Major
**Confidence**: 5 — core expertise: count-model dispersion and power

### W5: Concentration of extra-Poisson variance in hubs is what scale alone predicts
**Problem**: Excess variance, Σ_t(y_st − ȳ_s)² − 11ȳ_s, grows with μ² whenever relative overdispersion is constant (negative binomial: var = μ + μ²/θ). If 1% of tracts hold 34% of crime (the curve in Fig. 6c looks closer to 30%; please check), the same tracts hold a much larger share of Σμ², and therefore of excess variance, even if every tract had the same relative overdispersion. The 88% figure therefore does not show that hubs have different dynamics. Hub tracts may also contain default geocoding points (police-station addresses, neighbourhood centroids) that create artificial monthly spikes.
**Evidence Anchor**: text: Results, Month-to-month crime is noise "the 1% of tracts with most phone crime held 34% of it and 88% of the extra-Poisson variance"
**Why it matters**: "The predictable monthly dynamics live in a few hubs" carries the section title and the abstract's qualifier "outside a few hubs".
**Suggestion**: Compute the share of excess variance expected in the top 1% under a common-θ negative binomial fitted to all tracts, and compare it with 88%. Plot the relative dispersion index, not absolute excess, by count decile. Check hub tracts for repeated identical coordinates and station-address geocodes. Report forecast skill for hub tracts on their own. Pooled within-tract R² is 0.018 and is dominated by hubs, so at present there is no evidence that forecasts add anything at hubs either.
**Severity**: Major
**Confidence**: 4 — core expertise: overdispersion scaling

### W6: The predictability ceiling contradicts "close to its limit of predictability"
**Problem**: Within tracts, the ensemble reaches R² = 0.018 against a ceiling of 0.56, about 3% of the attainable signal. The 87–99% figures refer to "where and when", which is dominated by between-tract variance that the historical map already captures. The text nevertheless concludes that the city is near its limit, and the abstract says forecasts "add little beyond the tissue map outside a few hubs". For the temporal component the ceiling says the opposite: there is a sizeable within-tract signal above Poisson noise that no method captures. The ceiling also carries no interval. It assumes counts are Poisson given the rate, so multi-victim incidents or duplicate reports would raise the noise floor. And "maximum R² attainable without a model" is a misnomer: it is the maximum attainable by any model, estimated from data.
**Evidence Anchor**: text: Results, Month-to-month crime is noise "Within tracts, however, it explained R² = 0.018 of a maximum of 0.56." and "the city sits close to its limit of predictability"
**Why it matters**: This misstates the paper's answer to its third question, what remains to be predicted.
**Suggestion**: Rephrase, for example: "between tracts, forecasts approach the ceiling; within tracts, a non-Poisson component exists (ceiling 0.56) that no method captured (0.018), concentrated in high-count tracts". Add district-bootstrap intervals to the ceilings. Split the within-tract ceiling into a systematic seasonal-and-trend part (bounded by an in-sample seasonal-trend fit) and a residual part. Drop "close to its limit" and the analogy to limits of predictability in human mobility unless the within-tract gap is explained.
**Severity**: Major
**Confidence**: 5 — core expertise: forecast evaluation

### W7: The clock's permutation null treats events as exchangeable
**Problem**: Permuting periods among individual events within districts assumes events are independent given the district. In practice they cluster: repeat and near-repeat offences, multi-victim incidents, the same offenders working the same tract at the same hour, and reports filed in batches. Event-level permutation therefore understates the null variance of H and is anti-conservative. With 200 permutations, the smallest attainable P is 1/201 ≈ 0.005, so "P = 0.005" is a floor, not an estimate. The null distribution of H sits far from zero (Fig. 4d: roughly 2.5 for theft and 5.5 for robbery, ×100), so raw H overstates the class-specific signal. For robbery in 2025 the observed H (about 5.8) lies inside the null distribution. The year-to-year replication (r = 0.93 and 0.90) is computed on deviations that still contain the district-rhythm component the null preserves, so it does not isolate class-specific structure.
**Evidence Anchor**: text: Methods, Tissue clock "The null distribution permuted periods among events within districts (200 permutations for exploration and 999 for confirmation)."
**Why it matters**: A-R7 is a confirmatory claim, and its test must be valid at the level at which events cluster.
**Suggestion**: Permute blocks (tract-days or tract-weeks), or use a parametric bootstrap from a district × period model with tract-level overdispersion. Report excess contrast (H minus the mean null H) with an interval. Compute replication on null-subtracted deviations. Write "P ≤ 0.005", or run more permutations. Pre-register the block version for the vault.
**Severity**: Major
**Confidence**: 4 — core expertise: permutation inference under clustering

### W8: The abstract's headline clock example rests on the weakest, non-confirmatory and unvalidated result
**Problem**: The abstract leads with the robbery clock on low-income housing, which has four problems. (a) The class-specific departure for robbery failed in 2025 (P = 0.07), and the confirmatory claim A-R7 covers phone theft only (Fig. 6g), so the robbery clock sits outside the confirmatory family. (b) The 41% is a ratio of hourly class rates estimated by EM, a model output reported without an interval. In Fig. 4b the low-income profile is near zero from 07:00 to 18:00 and above 20% at both 04:00 and 05:00, a shape that fits boundary solutions when collinear classes compete hour by hour (W3). (c) There is no model-free check (the raw hourly distribution in tracts dominated by low-income housing) and no check for hour heaping (default hours, or time of report recorded instead of time of event). (d) The "3% of pedestrians" comes from a 2017 weekday survey.
**Evidence Anchor**: text: Abstract "on low-income housing, 41% of weekday phone robberies occur between 04:00 and 06:00"
**Why it matters**: The paper's most quotable number is presented as established but may not survive confirmation.
**Suggestion**: Either lead the abstract with the confirmatory phone-theft clock, or add the robbery clock to the confirmatory family before the vault is opened. Report bootstrap intervals for the 41% and for the hourly profile. Show the raw hourly distribution of robbery in tracts where low-rise low-income housing makes up most of the exposure, alongside comparison tracts. Report the share of robbery records stamped exactly at 04:00 or 05:00 and the share recorded by period only.
**Severity**: Major
**Confidence**: 4 — core expertise: deconvolution identifiability and police-record timing

### W9: The memory decomposition is not unique and confuses persistent heterogeneity with memory
**Problem**: The decomposition expresses var(m), the mean between-year residual covariance and a remainder as fractions of var(ℓ), with a cross-term absorbing their covariance. Fig. 5b shows that cross-term at −13% for all tracts and +7% for high-crime tracts. With a negative cross-term, var(m)/var(ℓ) overstates what the tissue explains. The implied in-sample R² of ℓ on m is about 0.20–0.30 (depending on whether the cross-term is Cov or 2Cov), close to the out-of-sample 0.25 and well below 42%. In high-crime tracts the tissue share drops to 18%, which the text does not report. Using ℓ = log(count + 0.5) adds count-dependent sampling noise to the transient part. More fundamentally, the "stable memory" is the time-invariant part of the tract effect. That is persistent unobserved heterogeneity (place characteristics, local recording practice, mismeasured exposure, reconciliation as in W2), not memory in the sense of state dependence, where past crime raises future crime. Residual autocorrelation falling only from about 0.70 to 0.63 over one to three years is the signature of a permanent component, not of dynamics.
**Evidence Anchor**: text: Results, Stable tissue "the tissue accounted for 42% and a stable component beyond the tissue, the covariance of residuals across years, for 48%"
**Why it matters**: "Beyond composition, places carry a stable memory of crime" is the abstract's second claim, and "memory" suggests a dynamic mechanism the analysis does not test.
**Suggestion**: Fit a Poisson-lognormal or negative binomial mixed model, log μ_st = log(Σ_k E_sk λ_kt) + u_s + v_st, and report σ²_u, σ²_v and the variance of the composition offset on the same latent scale with district-bootstrap intervals. Report the in-sample R² next to the variance shares. To claim memory, add a dynamic test (do year-t shocks predict t+1 beyond u_s?). Otherwise, call it "a persistent place effect beyond composition" in the abstract, Results and Discussion.
**Severity**: Major
**Confidence**: 4 — core expertise: variance components and panel models

### W10: Confirmatory criteria are weak, and the pseudo-vault is presented as evidence
**Problem**: A-R2 passes if ρ > 0, and A-R7 passes if H exceeds an event-level permutation null (W7). A-R1 and A-R6 require ρ ≥ 0.7 on class rates that span about four orders of magnitude (Fig. 3a), which the structural extremes (stations versus residential) almost guarantee. How P is computed for threshold criteria is not stated. The pseudo-vault is made of exploration districts already used in development, yet the Results present it as evidence ("All five were sustained after Holm correction"). Its point-validation ρ of 0.63, against 0.93 in exploration, is informative and goes undiscussed. OSF registration is "planned" and not yet timestamped.
**Evidence Anchor**: text: Methods, Statistics "A-R2, ρ > 0 for point validation"
**Why it matters**: The paper presents the analogy as "an instrument that can fail its tests". The pre-specified tests need a realistic chance of failing.
**Suggestion**: Before opening the vault, tighten the criteria: A-R2 at ρ ≥ 0.7 using the held-out-point design from W1; A-R7 as excess H under a block permutation; A-R1 as concordance of log rates within parcel types excluding stations and streets, or a calibration slope inside a stated band. State the test and how P is computed for each, and register on OSF. In the Results, describe the pseudo-vault strictly as a code check and either remove its P values from Fig. 6g or label them in-sample.
**Severity**: Major
**Confidence**: 4 — core expertise: preregistration and confirmatory design

### W11: The forecasting benchmark appears to use the held-out districts
**Problem**: The benchmark bootstraps "the 96 districts", while the spatial vault "holds out 19 of the 96 districts from every crime analysis of the atlas". If the benchmark used crime data from the 19 vault districts, the authors have already seen tissue–crime associations there. That covers the models with tissue features, the SHAP theory groups in Extended Data Fig. 7, and possibly the ceiling and dispersion analyses in Fig. 6, and it weakens the blindness of the spatial confirmatory test. Separately, the 2025 evaluation year falls inside the 2022–2025 exploration window and was visible during development, so only 2026 is a clean hold-out. Yet the 2025 results are described as run "under a pre-specified protocol" and reported with Holm-adjusted P values.
**Evidence Anchor**: text: Methods, Forecasting benchmark "Differences used 2,000 bootstrap resamples of the 96 districts and Holm correction."
**Why it matters**: The integrity of the vaults is the paper's main protection against analytic flexibility.
**Suggestion**: Add a table listing, for each analysis, the districts and years used. If vault districts entered the benchmark, document which outputs were inspected, and either re-run the benchmark on the 77 exploration districts or argue why that exposure cannot inform the atlas claims. Label the 2025 benchmark as development and keep confirmatory language for 2026.
**Severity**: Major
**Confidence**: 3 — inferred from Methods wording; the authors may have restricted what they inspected

### W12: The event study reads its MDE as an exclusion bound and is underspecified
**Problem**: An MDE of 2.8 SE is the effect detectable with 80% power at α = 0.05. It is not a range the data exclude; exclusion comes from the confidence interval around the estimate. In Extended Data Fig. 9, bar and restaurant closures on commercial parcels give −3.9% with an MDE of 11%. That implies SE ≈ 3.9% and a 95% interval of roughly −11.6% to +3.8%, so a reduction of about 11% is not excluded. The Methods also leave out the outcome (the axis says "thefts": phone theft or all theft?), how the estimator relates to the cited Callaway–Sant'Anna method (what is described is a binned treated versus never-treated comparison with a baseline at months −12 to −7), how repeated events on a segment are handled, the clustering used in the bootstrap, and whether registry dates are valid. Registration and deregistration dates can lag real openings and closures by months, which attenuates and blurs effects. Six variants are tested.
**Evidence Anchor**: text: Results, Stable tissue "effects larger than 4–11% of the baseline rate are excluded"
**Why it matters**: The Discussion's policy statement ("not a lever within a year") relies on this result. It is secondary to the three questions, however.
**Suggestion**: Report each variant's estimate with its 95% interval and write "effects outside [L, U] are excluded", or use equivalence tests. Specify the estimator and the outcome. Validate registry dates on a sample. Otherwise, move the event study to Extended Data with full Methods and soften the Discussion sentence.
**Severity**: Minor
**Confidence**: 5 — core expertise: staggered difference-in-differences

### W13: Crowd normalisation is a weak test, and guardianship is inferred rather than measured
**Problem**: (a) The class "crowd factor" spans only about 0.45–1.6 (Extended Data Fig. 10c), because pedestrian density is smoothed with σ = 300 m and mapped to classes through tract exposure. Dividing rates that span about four orders of magnitude by such a factor can hardly change ranks, so "the ordering survives" (ρ = 0.75) is close to automatic. (b) The 19-fold risk per pedestrian at 03:00 divides by a near-zero night-time denominator taken from a 2017 weekday household survey, with no interval. (c) Guardianship is not measured. The same pattern fits target suitability (lone commuters carrying phones in the dark) or offender routines, and pedestrians are both targets and guardians.
**Evidence Anchor**: text: Results, The tissue keeps a clock "Dawn robbery in the periphery thus tracks the absence of guardians"
**Why it matters**: The Discussion's policy recommendation for 04:00–06:00 rests on this interpretation.
**Suggestion**: Add survey-bootstrap intervals to the hourly denominators and to the 19-fold ratio, and pool hours where the survey has little support. Describe rank survival as a weak check. Write "is consistent with low guardianship, as routine-activity theory predicts" and soften the policy sentence to match.
**Severity**: Minor
**Confidence**: 4 — core expertise: ambient-population denominators

### W14: Displayed analyses have no Methods, and they are not needed for the story
**Problem**: Several displayed analyses have no Methods at all: the equivalence-audit verdicts (Extended Data Fig. 2), the communication, multiverse, Knox, MISTy and Lee's L analyses (Extended Data Figs 3–5), and the Shapley and SHAP theory-group decompositions (Fig. 3f, Extended Data Fig. 7, the former not cited in the text). The language-model decision layer ("Laya-FT", Fig. 6g) gets one Methods sentence and no Results. None of these answers the three stated questions. Also marginal to the story: NMF programs (Fig. 3d,e), neighbourhood enrichment and tissue domains (Fig. 2d,e, with 2c and 2e not cited), weekend ratios (Fig. 4e), the district × quarter lethal-violence comparison (Fig. 6e) and the income-quintile flagging analysis (Fig. 6f, with no metric definition).
**Evidence Anchor**: absence: Methods section — expected procedures and decision rules for Extended Data Figs 2–5 and 7, Fig. 3f and the Laya-FT comparison; checked all Methods subsections, Statistics, Data availability and every figure legend
**Why it matters**: As presented these analyses cannot be replicated, and they thin out a story the authors want to keep to one thread.
**Suggestion**: Cut Extended Data Figs 3–5, Extended Data Fig. 7, Fig. 3f and the H2 language-model comparison, or move them to a Supplementary note with full Methods. If the analogy audit stays, reduce Extended Data Fig. 2 to a short table with explicit verdict rules. Keep NMF programs and neighbourhood enrichment only if a Discussion sentence uses them, and keep the fairness result as one defined sentence.
**Severity**: Minor
**Confidence**: 4 — reproducibility standards; the call on story economy is shared with the editor

### W15: Core Methods have replication gaps
**Problem**: Several details needed to rerun the core analyses are missing: EM initialisation, convergence tolerance and handling of the zero boundary; what "fitted jointly" means; how the contrast H is aggregated over classes into one value per phenotype-year; the exact formula for "rates per pedestrian"; which tracts enter the dispersion test (all 21,331 exploration tracts, or the 15,708 used for memory?), its α and its handling of tracts with zero mean; the ensemble's stacking weights and the data they were fitted on; hyperparameter tuning and refitting schedule per model; the definition of "calibrated within 5%"; and the segment-linking rule for events beyond 60 m.
**Evidence Anchor**: absence: Methods, attribution, clock, dispersion and benchmark subsections — expected the estimation, aggregation and tuning details listed above; checked Methods, Statistics and all figure legends
**Why it matters**: An independent team with the same data could not reproduce Figs 3a, 4d, 6b–c or 6d from the text alone.
**Suggestion**: Add these details in about six sentences, or in a Supplementary methods table. Code availability helps but does not replace them.
**Severity**: Minor
**Confidence**: 5 — reproducibility standards

### W16: Numbers and labels disagree across abstract, text and figures
**Problem**: The abstract's 1.83 million records appear nowhere else; the Results use 0.69 million (2024–2025) and 121,434 (2025 phone crime). The text says "phone crime" (thefts plus robberies), but the axes of Fig. 3a ("Phone thefts per year"), Fig. 5a ("tract theft rate"), Fig. 6a ("Thefts captured") and Fig. 6c ("Thefts") suggest theft only. The text gives 34% for the top 1% of tracts, where Fig. 6c looks like about 30%. The Brier difference is 0.0005 in Methods (0.1079 against 0.1084) and +0.0006 in Fig. 6g. Methods say 12 methods and six baselines, but Extended Data Fig. 1 classes GWR and spatial panel as baselines, labels KDE "Astronomia" (a baseline in Methods), leaves out persistence, seasonal naïve and prospective hot-spotting, and uses Portuguese family labels. The Fig. 6a legend says "Noise ceiling" where the text says "expected if the model were true", and the ensemble (53%) beats it. "No method beat the baseline for lethal violence" is ambiguous: against the historical mean, all three methods in Fig. 6e show positive skill.
**Evidence Anchor**: text: Abstract "1.83 million police records form a panel of 15 crime phenotypes"
**Why it matters**: Readers cannot tell which outcome each figure shows.
**Suggestion**: Reconcile every number and label, use one outcome name per figure, and state the baseline in Fig. 6e.
**Severity**: Minor
**Confidence**: 5 — direct comparison of surfaces

### W17: Exploratory enrichment calls are made without multiplicity control
**Problem**: Enrichment is declared whenever a bootstrap interval excludes zero, across 19 classes × 15 phenotypes = 285 intervals with no adjustment. The neighbourhood-enrichment z-scores rest on 100 permutations across all type pairs. The specific enrichments quoted in the Results (for example +1.5 for vacant land in lethal violence) carry no multiplicity-adjusted uncertainty.
**Evidence Anchor**: text: Methods, Phenotype panel and signatures "Enriched classes were reported when they held at least 2% of the phenotype and the bootstrap interval excluded zero enrichment."
**Why it matters**: Some of the highlighted enrichments are expected to be false positives.
**Suggestion**: Use simultaneous intervals or FDR across the 285 cells, report the number of enrichments that survive, and say explicitly that these are exploratory.
**Severity**: Minor
**Confidence**: 4 — multiple testing

### W18: Some signatures are partly built in by the data definitions
**Problem**: "Robbery on public transport" is defined by place of occurrence, and rail-stratum events without coordinates are allocated only to tracts within 250 m of a station. Its enrichment at stations and terminals (+2.5 and +2.3) is therefore partly built in, much like the traffic-injury positive control.
**Evidence Anchor**: text: Methods, Units and reconciliation "Rail-stratum events were distributed only among tracts within 250 m of a station."
**Why it matters**: Presenting a built-in pattern as a discovered signature inflates the apparent discriminating power of the method.
**Suggestion**: Report it as a second positive control rather than a finding, or show it on geocoded events only.
**Severity**: Minor
**Confidence**: 4 — data-construction logic

### W19: The D² baseline ignores tract size
**Problem**: D² is computed against a constant expected count per tract, so part of the "third of the deviance" reflects differences in tract size and total exposure rather than composition.
**Evidence Anchor**: text: Methods, Composition-aware attribution "D² is the deviance explained relative to a constant expected count across tracts."
**Why it matters**: "Composition alone explained a third of the deviance" overstates what composition adds.
**Suggestion**: Also report D² against a size-only model (one common rate times total exposure), so the composition increment is visible.
**Severity**: Minor
**Confidence**: 5 — deviance-based fit measures

### W20: Classifier error exceeds the transition rate it is used to measure
**Problem**: Family transitions are inferred from a classifier with 93.6% accuracy, an error rate of about 6.4%, larger than the 1.8% annual transition rate it reports. The 98.2% permanence therefore reflects stable cadastral attributes and correlated classifier errors as much as stable land use. Pairs involving 2021 are excluded without explanation.
**Evidence Anchor**: text: Methods, Parcel types and tissue architecture "93.6% accuracy on held-out parcels"
**Why it matters**: "The tissue itself barely changes" supports reading composition as a slow variable.
**Suggestion**: Estimate transitions from observed cadastral use codes where they exist, or correct the transition matrix for misclassification. Explain the 2021 exclusion.
**Severity**: Minor
**Confidence**: 4 — misclassification in transition estimation

### Detailed Comments

**Title and Abstract.** The abstract should match the confirmatory status of each claim. Its three claims map onto W1 (validation framing), W8 (robbery clock), W9 ("memory") and W4–W6 ("Poisson noise in 96%", "outside a few hubs"). A version that holds up under the current evidence would say: composition-aware attribution assigns class-specific rates and signatures that a finer-scale allocation of geocoded events reproduces; phone-theft clocks differ by class and replicate across years; a large persistent place effect remains beyond composition; and month-to-month counts in most tracts are too sparse to be told apart from Poisson noise, so monthly forecasts add little to a stable map.

**Methods.** The Methods are compact and mostly well written, but the core models need about six more sentences (W15) and the analyses in W14 need either Methods or removal. The confirmatory section should list, for each claim, the statistic, the test, how P is computed and the decision threshold. Add the table of districts and years per analysis (W11).

**Results.**
- *Attribution.* Add the identification paragraph, a recovery simulation and the held-out validation (W1, W3).
- *Clock.* Report excess H, use a block-permutation null, give intervals on hourly profiles, and add a model-free check of the 04:00–06:00 spike (W7, W8).
- *Memory.* Fit a variance-components model and rename the component (W9).
- *Decline.* This is sound as a rates-with-fixed-composition comparison. Because Kitagawa is cited, either report the composition component (near zero, given 98.2% permanence) or drop the reference.
- *Noise and forecasting.* Rewrite around W4–W6, and label 2025 as development (W11).

**Discussion.** Rewrite the "checked against data that the analyses did not use" sentence (W1), soften the guardianship policy inference (W13) and the event-study inference (W12), and replace "remember crime" with "persistent place effects" unless a dynamic test is added (W9).

**Statistical reporting adequacy** (criterion: the Nature Portfolio reporting summary plus `statistical_reporting_standards.md` §6):

| Item | State | Note |
|---|---|---|
| Effect sizes | COMPLETE | Rates, ratios, ρ, ΔCRPS reported |
| Uncertainty intervals | PARTLY_COMPLETE | Missing for validation ρ, the 41% figure, ceilings, variance shares, excess H, weekend ratios, per-pedestrian risk |
| Assumption checks | MISSING | Attribution homogeneity, additivity, collinearity, boundary (W3) |
| Power or precision | PARTLY_COMPLETE | MDE given for the event study but misread (W12); none for the dispersion test (W4) |
| Missing-data handling | PARTLY_COMPLETE | Reconciliation described; downstream consequences unexamined (W2) |
| Multiplicity | PARTLY_COMPLETE | Holm for benchmark and confirmatory family; none for exploratory enrichment (W17) |
| Preregistration | PARTLY_COMPLETE | Version-controlled plan; OSF pending; criteria weak (W10) |

**Methodological fallacies detected.**
- Circular validation (W1).
- Ecological inference moved from tracts to classes (W3).
- Non-rejection read as confirmation (W4).
- A scale effect read as a mechanism (W5).
- Persistent heterogeneity read as state dependence (W9).
- Causal language from an associational ratio (W13).

**Keep, fix or cut, for one story.** Keep and fix: attribution with signatures (W1–W3), the phone-theft clock with crowd normalisation (W7, W13), the persistent place effect (W9), the decline under fixed composition, and the noise ceiling with the benchmark (W4–W6). Move to Extended Data with full Methods, or cut: the event study (W12) and the fairness analysis. Cut: communication, multiverse, MISTy, Knox, Lee's L, SHAP theory groups, Fig. 3f and the language-model layer (W14).

### Questions for Authors

1. Which districts and years entered each analysis? In particular, did the forecasting benchmark, Fig. 6b–c and Extended Data Fig. 7 use crime data from the 19 vault districts, and which of those outputs were inspected?
2. For each phenotype and year, what share of events was reconciled rather than geocoded, and do the memory decomposition, the persistence curve and the dispersion test hold on geocoded-only counts?
3. How many class rates (annual and hourly) sit at or within numerical tolerance of zero, and how often does this happen across bootstrap resamples? Is the low-income profile between 07:00 and 18:00 a boundary solution?
4. Will the confirmatory criteria be tightened, and the robbery clock added, before OSF registration and opening of the vault?

### Minor Issues

- Write "P ≤ 0.005" wherever the permutation floor is reached (Fig. 4d, Results).
- Extended Data Fig. 1 family labels are in Portuguese ("Aprendizado", "Sismologia", "Fundacao").
- Rename "Noise ceiling" in Fig. 6a to "expected capture if the model were true".
- Fig. 5b's "high-crime tracts" are defined only in the legend (at least 10 expected events per year); state this in the text.
- Methods: say why tracts with fewer than one expected event per year (21,331 minus 15,708) are excluded from the memory analysis.
- The Fig. 2a UMAP of 150,000 parcels is not needed for any claim.

### Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension | Criterion source | Judgement | Evidence anchor(s) | Rationale | Uncertainty / scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Originality | quality_rubrics (not my remit) | NOT_ASSESSED | — | Outside the methodology seat | — | no |
| Methodological Rigor | Contract D1; Phase 1 scoring plan | PARTLY_MEETS | W1, W2, W3, W7, W9 | Strong safeguards (vaults, blind typing, block bootstrap, proper scores), but the key identification and validation steps are untested or circular | Some concerns rest on Methods wording (W11) | yes: repairable block |
| Evidence Sufficiency | Contract D1; statistical reporting standards §6 | PARTLY_MEETS | W4, W5, W6, W8 | Headline statistics lack intervals, power or model-free checks | The confirmatory test is pending by design | yes |
| Argument Coherence | Contract D3; Phase 1 scoring plan | PARTLY_MEETS | W1, W4, W6, W8, W9 | The thread is coherent, but four abstract or Discussion statements outrun their statistics | Repairable by reframing | yes: repairable block |
| Writing Quality | quality_rubrics (journal-fit seat) | NOT_ASSESSED | — | Outside remit; story-economy points raised in W14 only | — | no |
| Literature Integration | quality_rubrics (domain seat) | NOT_ASSESSED | — | Outside remit | — | no |
| Significance and Impact | quality_rubrics (journal-fit seat) | NOT_ASSESSED | — | Outside remit | — | no |

The recommendation follows from the decision-bearing criteria still open: methodological rigor (W1–W3, W7, W9) and argument coherence (W1, W4, W6, W8). All are repairable with the analyses and rewording listed above. The strengths in design do not offset these gaps.

## Arithmetic Receipts

no_recomputable_statistics: The manuscript reports no t, z, F or chi-square statistic paired with its df and P value, no discrete-scale mean or SD with an analytic N, and no df to invert; all reported P values are permutation, bootstrap or Holm-adjusted (nonstandard procedures) and the dispersion test is summarised only as shares of tracts, so none of the four bounded procedures applies; consistency arithmetic (geocoded share 100,347/121,434, Brier difference, implied in-sample R2 from Fig. 5b, event-study intervals from MDE) is reported as prose in W1, W9, W12 and W16.
