# Re-review (verification round) — "Crime as a phenotype of urban tissue"

Mode: ARS v3.23.1 academic-paper-reviewer, re-review (verification). Target venue unchanged: *Nature Cities*, Article.
Date: 2026-10-20.

## 0. Run notes and provenance

- **Contract status.** This is not a contract-valid Stage 3' run. The author-adjudication sidecar, the revision-evidence bundle and the input manifest do not exist, and the round-1 manuscript was not preserved (round-1 text is known only from quotations in `eic.md`, `r1_metodologia.md`, `r2_dominio.md`, `r3_perspectiva.md`, `da.md` and `decisao_editorial.md`). The protocol was applied in spirit: every verdict below rests on the revised manuscript (`paper/manuscript.md`) and the revised figures (`figures/out/dev/fig1–6.png`, `ed1–ed9_*.png`) alone. No response letter was supplied or read. Verdicts were not adjusted for author persuasion.
- **Verdict vocabulary.** The vocabulary is the one requested: RESOLVED / PARTLY / NOT RESOLVED / DEFERRED-BY-AUTHOR. It maps to the protocol's FULLY_ADDRESSED / PARTIALLY_ADDRESSED / NOT_ADDRESSED. Every PARTLY row carries a residual class (must_fix / should_fix / consider), used in §5.
- **Binding author scope.** The binding author scope was applied as follows:
  - All text and figure items are in scope.
  - Six new analyses are in scope: geocoded-only persistence (R-97, part); the theft/robbery split of the decline (R-119); district effects (R-100); the power of the dispersion test (R-103); the excess variance expected from scale (R-104); and the model-free pre-dawn count (R-109, part).
  - All other (c) items are judged only as "deferred, disclosed or not".
  - The title is kept by author decision. It is judged under DA C1 (§2), not as a failure of R-08.
- **Single-family caveat.** The round-1 seats and this verifier share a model family. Agreement between them is not independent confirmation.

### Mechanical checks of the revised manuscript

| Constraint (Nature Cities Article) | Revised | Status |
|---|---|---|
| Title ≤ 90 characters | 36 | OK |
| Abstract ≤ 150 words, no references | 149 (whitespace count) | OK, at the limit |
| Main text ≤ 3,500 words (Intro + Results + Discussion) | ≈ 2,940 | OK |
| Methods ≤ 3,000 words | ≈ 2,450 | OK |
| ~50 main-text references | 50 main-text + 9 Methods-only (59 total) | OK |
| ED figures numbered by first citation | ED1 → ED9, cited in order | OK (R-85 resolved) |
| Fig. panels cited in order | Fig. 4 is cited a, d, b, f, c, e; Fig. 1c,d and ED Fig. 2b,d are uncited | Minor (see N-27) |

---

## 1. Traceability table — must_fix items in §4.a (text) and §4.b (figures)

There are 35 items. Anchors quote the revised manuscript (`ms` line numbers refer to `paper/manuscript.md`) or describe the revised figure.

| ID | Verdict | Evidence anchor (revised manuscript / figure) | Remaining gap (residual class) |
|---|---|---|---|
| R-01 one spine | **PARTLY** | Intro ¶3 (ms l.17): "We ask three questions: which crimes each class of cell hosts, at what hour, and what remains to be predicted once composition and history are known." Discussion ¶1 restates the same three findings. The analogy audit is in ED Figs 6–9 with one Discussion paragraph; the benchmark is one paragraph plus ED Figs 4–5. | A spine exists (R3's option: one instrument along what/when/how much, plus one bound). Two things sit outside it. (i) The subsection "Rates move within a stable tissue" (decline + event study, Fig. 5e,f, ED Fig. 3) answers none of the three stated questions, yet carries confirmatory claim C5. (ii) The paper's final sentence is a limitation with a placeholder ("the confirmatory test is pending [CONFIRMATION]"), not the claim. Fix: either add "how rates change" as a fourth question in the abstract and Intro, or move the decline to ED and drop C5. Reorder the Discussion so that it ends on the bound. (should_fix) |
| R-04 event-study claims | **PARTLY** | Results (ms l.45): "effects outside −14% to +5% of the baseline rate are excluded in every variant (Extended Data Fig. 3)". Methods (ms l.119) states the outcome, baseline/pre/effect windows, district-clustered bootstrap and "the excluded range is the union of the 95% intervals". Discussion (ms l.65): "suggests that single business openings or closures are not a lever within a year". | (i) ED Fig. 3 still prints the MDE ("effect −2.1% (MDE 6%)") and no per-variant 95% interval, so the −14%/+5% bound cannot be traced. ED Fig. 6 still reads "null; detectable effects 4–11% excluded". (ii) Repeated events per segment are not specified. "In the spirit of ref. 40" is vague, and the estimator described (treated vs mean of never-treated, same district × street class) is not Callaway–Sant'Anna. (iii) Results ¶ "did not change street crime" reads a null as no effect; write "detected no change". (iv) Bootstrap "with controls fixed" understates variance; disclose or resample. (should_fix) |
| R-06 classical lineage of additions | **RESOLVED** (text) | Discussion ¶5 (ms l.69): "Its steps have classical counterparts: Poisson ecological regression, rate–composition decomposition and time-specific crime pattern analysis. What the omics workflow added is their systematic use across all classes and crime types with a positive control, the separation of state from type and a discipline about sampling noise." | ED Fig. 6 contradicts this text: Attribution row = "Known-composition spots" vs "Ecological regression by tract", verdict "Omics (sub-tract rates)". See N-1. "Separation of state from type" and "discipline about sampling noise" have classical counterparts too (multilevel decomposition; Cochran's dispersion test, ref. 41). Consider softening. |
| R-07 criminological precursors | **RESOLVED** | Intro ¶1 (ms l.13): generators/attractors (refs 8,9), risky facilities (ref. 10), facility and land-use studies (refs 11,12), risk terrain modelling (ref. 13). Results ¶1 (ms l.27): "This is Poisson ecological regression with known exposures^18^". Limitations: one rate per class "holds for the ordering of classes but not for their absolute rates". | Minor: King and multi-land-use segment models are not engaged. Ref. 12 (Andresen, Curman & Linning 2017, crime-type trajectories) is cited as a facility/land-use study (N-21). |
| R-08 declarative title | **DEFERRED-BY-AUTHOR** | Title unchanged: "Crime as a phenotype of urban tissue". | Judged under C1 (§2): defensible only after N-23, N-24 and N-25 are fixed. |
| R-14 robbery clock as lead example | **PARTLY** | The 41% is gone. Results ¶1 (ms l.33): "For phone theft, the pre-specified test…"; "Phone robbery departed from the null in 2024 (P ≤ 0.005) but not in 2025 (P = 0.07)". Statistics: "C4, the phone-theft contrast H". | The abstract (ms l.11) chains "Classes also keep daily rhythms that replicate across years … ; low-standard housing has a pre-dawn robbery excess". Only the phone-theft rhythm met the replication test. The robbery excess is exploratory and is not labelled so in the abstract. Fix: "Phone-theft rhythms differ by class and replicate across years; an exploratory pre-dawn robbery excess appears on low-standard housing." (must_fix, one sentence) |
| R-15 dawn recommendation | **RESOLVED** | Discussion ¶3 (ms l.65): "The second pattern suggests testing measures that raise guardianship at those hours, such as street lighting^44^ and staffed bus stops, and it involves transit operators and municipal services as much as the police." The evening-patrol comparison is gone. | — |
| R-16 guardianship wording | **RESOLVED** | Results (ms l.35): "This pattern is consistent with low guardianship and with offenders converging on commuters' paths to transit^6^; darkness^35^ and offender routines remain untested alternatives." | — |
| R-20 "niche" | **RESOLVED** (text) | "Niche"/"niches" no longer appears in the text or the Fig. 1 legend. "Crime receded to its niches" is deleted. | ED Fig. 6 row "Niches" remains (N-1). |
| R-23 one ceiling term | **RESOLVED** | Results (ms l.49): "a noise ceiling, the largest R² any model could reach given Poisson noise". Methods (ms l.123) uses the same term. | — |
| R-25 validation as consistency check | **RESOLVED** (text) | Results (ms l.27): "a consistency check at finer scale rather than a test on independent data". Methods (ms l.99): "this is a consistency check between scales". Discussion ¶1 no longer lists point validation among checks on unused data. | ED Fig. 6 still says "point validation ρ 0.93" (N-1). |
| R-27 hot-spot claims | **RESOLVED** | Discussion ¶3 (ms l.65): "The results suggest where and when to look, not where to act. … micro-place hot spots remain the unit of action^43^." The comparison with hot spots is dropped. Refs 10 and 44 are weighed. | Minor: Koper and Blattman et al. are not weighed. |
| R-28 noise wording | **RESOLVED** | "Is noise" is gone everywhere. Heading: "Month-to-month variation is sparse and hard to forecast". Results (ms l.51): "rejected Poisson noise in only 4% of tracts (14% of tracts with at least one event per month…)". | New wording problem in the abstract: "real but too sparse to detect" (N-5). |
| R-31 18% in high-crime tracts | **RESOLVED** | Results (ms l.39): "in the 3,626 tracts with at least 10 expected events per year, the split was 18% against 58% (Fig. 5b)". The Fig. 5b legend shows the cross-term; Methods gives −13%. | Minor: the legend shows the cross-term but does not say what a negative value means. |
| R-32 narrowed thesis | **PARTLY** | Intro (ms l.17): "composition structures which crimes a place hosts and when, … a persistent effect of place beyond composition accounts for more of how much crime it records". Discussion ¶1 matches. The cross-term is reported (Methods l.115; Fig. 5b "cov. −13%", "+7%"). | (i) One "fix" survives: Results §Month-to-month ¶1 (ms l.49), "If composition and history fix most of where crime occurs". (ii) The cross-term appears only in Methods and in Fig. 5b. Results never says that the 42/48 shares are not additive (the cross-term is −13%). (iii) Title and glossary issues (§2, N-24). (must_fix, small) |
| R-34 "marginal changes" | **RESOLVED** | Results (ms l.45): "Single business openings and closures on street segments did not change street crime within 12 months". The claim is narrowed to the events tested. | Wording "did not change" (see R-04). |
| R-35 ref. 41 analogy | **RESOLVED** | "Limit of predictability" is gone. Ref. 41 is now Cochran 1954, the dispersion test. | — |
| R-36 validation scope | **PARTLY** | Results (ms l.29): "The finer-scale check held in the 12 crime types with at least 80% of events geocoded (median ρ = 0.85; Fig. 3c)". Fig. 3c marks phone theft, lethal violence and residential theft/robbery "not tested". | (i) Methods (ms l.99) says the statistic is computed "across parcel types", but Fig. 3c also plots hollow markers for "all cell classes". Whether stations, streets and favelas were validated is now ambiguous, and the remedy required stating that they were not (N-11). (ii) Unvalidated profiles still carry inference in Results without a mark. Examples: "phone theft at rail stations (+1.6)" (phone theft untested; stations not validated) and "lethal violence on low-standard houses, vacant land and favelas" (66% geocoded, untested). (must_fix) |
| R-37 reconciliation details | **RESOLVED** | Methods (ms l.91): "(for 2022, over the available months, and by population where none existed), giving fractional counts that sum exactly to district totals". | — |
| R-38 reconciliation-dependent signatures | **PARTLY** | The burglary sentence is removed from the Discussion. Methods (ms l.91) and Limitations (ms l.73) flag the residential and lethal-violence profiles. | Lethal violence is still a highlighted example in Results (ms l.29) with no mark at the point of use. Fix: add "(66% geocoded; reconciliation-dependent)". (should_fix) |
| R-39 identification assumptions | **RESOLVED** | Methods (ms l.99): "The model assumes one rate per class across the city, additive contributions of classes and exposure proportional to frontage, street length or station count … 'Fitted jointly' means …". | Minor: location confounding is covered only by "associational" in Limitations. |
| R-40 dispersion-test specification | **RESOLVED** | Methods (ms l.123): "at α = 0.05 … in the 16,432 exploration tracts with at least one event; we report shares of tracts without multiplicity correction because the test is used descriptively". | See N-4 on how to read 4% at α = 0.05. |
| R-41 "close to its limit" | **RESOLVED** (text) | Results (ms l.49): "Within tracts, it explained R² = 0.018 of a ceiling of 0.56: real month-to-month variation exists, but the models do not capture it." | ED Fig. 6 Forecast verdict "Small gain, at noise ceiling" contradicts this (N-1). |
| R-42 P ≤ 0.005 | **RESOLVED** (text, Fig. 4d) | Results (ms l.33) and Fig. 4d: "P ≤ 0.005". Methods: "so P ≤ 0.005 is the floor". | ED Fig. 6 still prints "theft contrast P = 0.005" (N-1). |
| R-43 rename "memory" | **RESOLVED** (text, Fig. 1a, Fig. 5) | Heading "Type and state: a persistent effect of place". Fig. 1a: "Cell state beyond type → Persistent place effect". Fig. 5b key: "Persistent effect". | ED Fig. 6 row "Memory … stable memory 48%" remains (N-1). |
| R-47 rival explanations for dawn robbery | **PARTLY** | Results (ms l.35) names commuter convergence, darkness (ref. 35, Tompson & Bowers) and offender routines, and discusses the weekend ratio of 0.4 ("when fewer residents commute"). | Target suitability and crime pattern theory are not named, and Bernasco, Ruiter & Block 2017 (ref. 15, already in the list) is not cited at this point. (should_fix) |
| R-49 Knox placement (D-3) | **NOT RESOLVED** | The Knox ratio is still in ED Fig. 9a and ED Fig. 8 ("mean ratio 1.12; max 1.68; 63 sig. pairs"). Its only Methods trace is a clause in "Exploratory analogy audit" (ms l.131). It is absent from the main text. | Neither D-3 option was taken. It was not brought into the main text with Methods, and it was not cut with the noise claim restricted (R-56). The ED evidence of short-term excitation (favela→favela 1.68) bears directly on the month-to-month claim and is never discussed (N-30). (must_fix) |
| R-53 gap statement | **PARTLY** | Intro (ms l.13): "Two gaps remain. Few studies read the full composition of a city, all its crime types and the hour together. And … a large share of police records lacks usable coordinates, most of all at homes and stations…". Sherman et al. 1989 is ref. 1. | (i) Eck & Weisburd 1995 and Steenbeek & Weisburd 2016 are not cited. (ii) "Most of all at … stations" contradicts ED Fig. 2a: public transport theft/robbery is 96% geocoded (N-12). (iii) "A large share" needs a number. Overall it is about 17% for phone crime (Methods l.91). (should_fix) |
| R-54 decline interpretation | **RESOLVED** | Results (ms l.45): "unlike the micro-place crime drops in Seattle and Boston, which came from few segments^2,38^. The two studies differ in unit, crime and period. Candidate drivers include the national phone-blocking scheme…^39^, policing and changes in reporting, none of which we test." The hub-policy corollary is gone. | C5 still encodes a hub claim that the robbery split undercuts (N-6). |
| R-55 heterogeneity vs state dependence | **RESOLVED** | Results (ms l.41): "persistent heterogeneity between places, which covariances across years cannot separate from state dependence^36^ … place management^10^ and territorial control by organized crime^37^". | — |
| R-56 scope of the noise claim | **NOT RESOLVED** | The abstract (ms l.11) does not restrict the claim to phone crime: "Month-to-month variation within tracts is real but too sparse to detect or forecast". Discussion ¶2 (ms l.63) generalises: "The noise ceiling … applies to any city that forecasts crime by small area and month." | The minimum remedy is absent. There is no restriction to phone crime at the tract-month scale in the abstract or Discussion. Nothing says how near-repeat (days–weeks, ~200 m; Johnson et al. 2007) or sub-tract dynamics would change the ceiling. Chronic vs temporary hot spots (Gorr & Lee 2015) and sparse-data concentration measurement (Bernasco & Steenbeek 2017; Haberman et al. 2017) are not engaged. (must_fix) |
| R-57 recorded-crime bias | **PARTLY** | Discussion ¶4 (ms l.67): "Victims report phone crime unevenly, which biases the map itself^46,47^; flagging by density here under-weighted the poorest tracts…; and for offences discovered by police, flags can feed back…^48^". Limitations (ms l.73): "undercount crime unevenly across places, incomes and crime types". The stigma paragraph is ms l.71. | Missing: (i) reporting propensity for phone theft vs robbery in Brazil; (ii) qualification of each dependent result (the income gradient of the flagged area; the 26% vs 7% recorded split possibly overstating richer tracts; the decline; the favela and peripheral signatures; the near-zero residential rate; dawn robbery); (iii) the statement that the finer-scale check cannot detect this bias. (must_fix) |
| R-66 sampling-noise analogy | **RESOLVED** | Results (ms l.51): "much as Poisson measurement noise masks variation in expression at low counts in single cells^26^". | — |
| R-67 "produces" and the analogy's break | **PARTLY** | "Produces" is gone from Results, Methods and the Fig. 3b legend ("share of the crime type attributed to the class"). Limitations: "Attribution is associational". Discussion ¶6: "recorded crime attributed to classes of places, not traits of their residents". | The remedy asked for the break (parcels host crime; they do not produce it) to be stated next to Fig. 1a. The Fig. 1 legend still lists "crime is a phenotype measured over the tissue" with no caveat. (consider) |
| R-87 ceiling keys | **RESOLVED** | Fig. 6b y-axis: "R² (filled: ensemble; open: noise ceiling)". Fig. 6a line: "If forecasts were exact". The legends match. | Fig. 6a legend omits two plotted lines (N-16). |

**Tally (35 must_fix):** 22 RESOLVED; 10 PARTLY (R-01, R-04, R-14, R-32, R-36, R-38, R-47, R-53, R-57, R-67); 2 NOT RESOLVED (R-49, R-56); 1 DEFERRED-BY-AUTHOR (R-08).

### 1b. must_fix items in §4.c (new analyses) — in-scope six and deferrals

| ID | Status | Evidence / disclosure | Remaining gap |
|---|---|---|---|
| R-97 geocoded-only re-runs | **PARTLY** (in scope: persistence) | Results (ms l.39): "The persistent component held with geocoded events only (40% against 46%)". Dispersion on geocoded only: "7% with geocoded events only" (ms l.51). Fig. 6a adds an "Ensemble, geocoded only" curve. | The ceiling, the persistence curve and an alternative allocation are not re-run, and the deferral is not disclosed. **Geocoded-only counts reject Poisson more often (7%) than reconciled counts (4%) despite lower counts. This is direct evidence that reconciliation damps month-to-month variance (DA-M2), and the text does not discuss it (N-3).** |
| R-100 spatially varying rates | **RESOLVED** (main part) | Results (ms l.27): "allowing a multiplicative risk level per district preserved the order of classes (Spearman ρ = 0.96), although it roughly halved the rates of central classes…"; profiles "median ρ = 0.89 …; same top class for 10 of 15 types". Methods gives the θ_d model. Limitations is updated. | Variation of λ_k by domain or income stratum (R2) is not reported. The abstract's "robust to district-level risk" overstates (N-9). |
| R-103 power | **RESOLVED** | Results (ms l.51): "simulated tracts with 0.25 events per month and a month-to-month coefficient of variation of 1 are flagged 12% of the time". Methods: "4,000 tracts per setting, gamma-distributed monthly rates". | Only one setting is reported. A minimum detectable CV at the observed tract means (0.19/month) would be more useful. |
| R-104 hub concentration vs scale | **RESOLVED** (claim withdrawn) | Results (ms l.51): "reproduces the concentration of extra-Poisson variance in the 1% of tracts with most crime (88% expected, 86% observed)". Fig. 6c annotation matches. The hub claim is replaced by "a property shared by all tracts". | The decile plot of relative dispersion and hub-only skill are not shown. Not needed now that the claim has been withdrawn. |
| R-109 robbery-clock checks | **PARTLY** (in scope: model-free count) | Results (ms l.33): "in the 313 tracts where low-standard housing dominates expected robbery, 16% … between 04:00 and 06:00 (95% interval 12–21%), against 6% in tracts dominated by commerce". Methods heaping check: "19% … fall on the full hour, against 26% overall". | Bootstrap intervals for the model hourly profile and the weekend ratios are not reported. Fig. 4a,b still display the model magnitude (≈41% at 04–06, ≈0 at 07–18), which the text disowns (N-28). |
| R-119 decline by offence | **PARTLY** (in scope) | Results (ms l.45): "robbery is 98% of phone crime on low-standard housing and 28% at stations … Phone robbery fell faster than the city's robbery on low-standard housing (relative ratio 0.56, 95% interval 0.34–0.78) …; middle-standard retail (1.15, 0.90–1.52) and rail stations (0.91, 0.69–1.19)". | The theft-specific class ratios are not reported. Fig. 5e still shows pooled phone crime only ("Fig. 5e for each offence" was required). The offence mix is given for two classes, not every class. C5 is not updated (N-6). |
| R-95 held-out validation | DEFERRED — **disclosed in effect** | Reframed as "a consistency check … rather than a test on independent data". C2 in the vault is the only independent check. | C2 criterion "ρ > 0" is too weak to serve that role (see R-108). |
| R-96 intervals for validation ρ | DEFERRED — **not disclosed** | Fig. 3c points have no intervals. | — |
| R-98 reconciled shares | DEFERRED, partly reported — **not disclosed** | Methods: 17% of 2025 phone crime reconciled; ED Fig. 2a gives the 2024–25 geocoded share by type. | Not reported by stratum or year. The Intro's station claim is unsupported (N-12). |
| R-99 recovery simulation | DEFERRED — **not disclosed** | — | Accuracy of the EM rates is unknown. |
| R-101 collinearity and boundary | DEFERRED — **not disclosed** | — | Directly relevant to the Fig. 4b profile near zero 07–18h and to the model–data gap (41% vs 16%). |
| R-102 latent month-to-month CV | DEFERRED, partly substituted — **not disclosed** | A moment estimate of the common CV ≈ 0.33 (ms l.51, l.123). | No hierarchical model, no interval. |
| R-105 geocode defaults | DEFERRED — **not disclosed** | — | — |
| R-106 ceiling intervals | DEFERRED — **not disclosed** | Fig. 6b ceilings have no intervals. | — |
| R-107 block permutation | DEFERRED — **not disclosed** | The clock P values still come from event-level permutation. C4 keeps it. | This must be settled before the vault opens. |
| R-108 confirmatory criteria / OSF | DEFERRED, partly done — **not disclosed** | Claims relabelled C1–C5 with criteria (ms l.135); C1 is now ρ ≥ 0.7. | C2 is still "ρ > 0". C4 still uses event-level permutation. OSF is still "planned". C5 is confounded by offence mix (N-6). H1 is missing from Methods (N-7). **Time-critical: this must be fixed before the vault is opened.** |
| R-110 mixed model and cross-term | DEFERRED, cross-term reported — **partly disclosed** | Cross-term −13% (Methods); Fig. 5b "cov." column. | No latent-scale variance components or intervals. The non-uniqueness of the shares is not stated in Results. |
| R-112 event-study intervals | DEFERRED, union bound reported — **not disclosed** | "−14% to +5%". | Per-variant intervals are not shown (ED Fig. 3 shows MDE). Registry dates are not validated. |
| R-113 night denominator uncertainty | DEFERRED — **not disclosed** | Results: "peaks at 03:00, at 19 times its daily mean". | The 19× is reported without an interval and drives the Discussion's "before dawn" implication. |
| R-118 tests of dawn rivals | DEFERRED — **disclosed** | "darkness^35^ and offender routines remain untested alternatives". | — |
| R-120 residual vs missing composition | DEFERRED — **partly disclosed** | Results (ms l.41): "Candidates include uses the cadastre misses…". | Untested. C1 rests on path (i) alone (§2). |
| R-121 robbery-only income audit | DEFERRED — **not disclosed** | — | The equity statements pool theft and robbery. |

Disclosure summary: of 16 deferred must_fix analyses, 2 are disclosed in the text (R-95 by reframing, R-118), 2 partly (R-110, R-120) and 12 not at all. Deferral is the author's prerogative. A deferral that leaves a reported number without its requested uncertainty, or leaves a confirmatory criterion unchanged, should be disclosed in the text (Limitations or Methods) and in the response letter.

---

## 2. DA CRITICAL C1 under the revised text

**Verdict: PARTLY RESOLVED (repairable at Minor level; no longer a D3 block on its own).**

- **Path taken.** The authors took path (i), narrowing the thesis. The narrowed claim appears consistently in four places:
  - Intro ¶3: composition "structures which crimes a place hosts and when"; a persistent place effect "accounts for more of how much crime it records".
  - Abstract.
  - Discussion ¶1.
  - Results ("Typing describes what a place is. Where crime concentrates most, its history says more.").
- **Statistics now carry the claim.** The statistics the DA cited now support the sentences rather than contradict them:
  - 42% vs 48%, and 18% vs 58% in high-crime tracts, are both in Results;
  - R² 0.25 / 0.31 vs 0.48;
  - the cross-term is reported (−13%; +7% in high-crime tracts).
- **What remains before the kept title is defensible:**
  1. **The glossary defines "tissue" as composition only.** Results ¶1 (ms l.23) says "The composition of a tract in these classes is its tissue", and the Glossary has "Tissue: the composition of a tract in cell classes". Under that definition, "Crime as a phenotype of urban tissue" attributes crime to the component that the paper shows is the minority share of how much (42%, 18% where crime concentrates). The Discussion defends the title on a broader reading: "a phenotype in the biological sense: it reflects both what a place is and the state it is in" (ms l.61). That reading needs the tissue to include state, as Fig. 1a already implies ("Cell state beyond type → Persistent place effect"). Fix: redefine tissue in the glossary and Results ¶1 as "composition plus the persistent state of its places". Alternatively, keep the definition and add one sentence saying that the title uses "tissue" in this broader sense.
  2. **Discussion ¶1, first sentence, inverts the mapping.** "São Paulo's recorded crime has a phenotype" makes crime the bearer of a phenotype, but Fig. 1a makes crime the phenotype. Fix: "São Paulo's recorded crime behaves as a phenotype of its tissue in the biological sense: it reflects both what a place is (type) and the state it is in."
  3. **One "fix" survives.** Results ms l.49 reads "If composition and history fix most of where crime occurs". Replace it with "account for most of where crime occurs".
  4. **The cross-term is not explained in Results.** Add one clause saying that the shares are not additive (cross-term −13%) and that the split is one of several possible decompositions (the R-110 mixed model is deferred).
- **Path (ii) not taken.** Showing that the residual is unmeasured composition (R-120) is deferred and only named as candidates. That is acceptable under path (i), provided the title sentence and glossary are fixed as above.
- **Conclusion.** With these four edits the title becomes a defensible framing of the paper's narrowed claim. It still states no result, which was the R-08 objection. That objection is waived here by the binding author decision, not resolved.

---

## 3. New issues introduced or exposed by the revision

Severity: **M** = major (changes a claim or a confirmatory test), **m** = minor, **s** = style/typesetting. "Regression" marks an issue introduced by the revision. "Exposed" marks one that was present before but is now visible or newly consequential.

### 3a. Claims, numbers and design

| # | Sev. | Location | Issue | Concrete fix |
|---|---|---|---|---|
| N-1 | **M** (regression by omission) | ED Fig. 6 (analogy audit table) | The table was not regenerated and contradicts the revised text in at least 11 cells: "Memory … stable memory 48%" (R-43); "Niches" (R-20); "point validation ρ 0.93" (R-25); "theft contrast P = 0.005" (R-42); "ρ = 0.75–0.86" (text: 0.75); "null; detectable effects 4–11% excluded" and "Null (tissue inertia)" (text: −14% to +5%); "GNN, Hawkes, Chronos, BYM2, Laya…" and "Laya-FT ≤ LightGBM" (internal code; R-13/R-81; R-03); "Small gain, at noise ceiling" (contradicts within-tract 0.018 of 0.56; R-41); Attribution "Known-composition spots … Omics (sub-tract rates)" against the Discussion's credit to Poisson ecological regression (R-06, R-80, R-93); "Differential expression … Omics (where the decline happened)" (R-93; the decline is now spread across the fabric). | Regenerate ED Fig. 6 from the revised text. Use plain module names, credit the classical counterpart, use "P ≤ 0.005", "persistent place effect", "finer-scale consistency check" and "−14% to +5%", drop the LLM layer, and change the Forecast verdict to "between-unit near ceiling; within-unit not captured". |
| N-2 | m | ED Fig. 3 | (i) The panels print "effect … (MDE x%)" rather than 95% intervals, so the text's −14%/+5% cannot be traced. (ii) The y-axis "Δ thefts per segment-month" disagrees with the Methods outcome "street crime (phone theft and robbery and other street theft and robbery)". (iii) "non-MEI" is an untranslated code. (iv) There is a single "a" label on a figure with no other panels. | Print the per-variant 95% interval, relabel the axis "Δ street crimes per segment-month", write "excluding individual micro-entrepreneurs", and remove the "a". |
| N-3 | **M** (exposed) | Results ms l.51; Methods l.123 | The geocoded-only dispersion test rejects Poisson in 7% of tracts against 4% with reconciled counts, although geocoded counts are smaller and the test therefore weaker. That is the signature of reconciliation smoothing month-to-month variance, the DA-M2/R-97 concern. The text lists 7% as if it were corroboration. | State it plainly: "reconciliation spreads non-geocoded events over 12-month geocoded shares and damps month-to-month variance". Report the noise ceiling and the scale comparison (88% vs 86%) on geocoded-only counts as well, or bound the effect. |
| N-4 | m | Results ms l.51 | At α = 0.05 with no multiplicity correction, 4% of tracts rejecting is fewer than expected if every tract were Poisson. The test is conservative at these means, and the share is uninformative, not low. | Say "no more than expected by chance at α = 0.05". Lead with the 14% among tracts with ≥ 1 event per month and the power result. |
| N-5 | m | Abstract (ms l.11); Discussion ¶1 (ms l.61) | "Month-to-month variation within tracts is real but too sparse to detect or forecast" contradicts itself: the variation is detected in aggregate (within-tract ceiling 0.56) and in high-count tracts. Also, counts are sparse, not variation. | "Month-to-month variation within tracts exists but is detectable only in aggregate and in the busiest tracts, and forecasts do not capture it." |
| N-6 | **M** (exposed by R-119) | Statistics ms l.135 (C5); Fig. 6g C5; Results ms l.45 | C5 ("a positive difference between the log relative ratios of hubs … and local streets") is defined on pooled phone crime. The revision shows that robbery fell 40% and theft 2%, and that robbery is 98% of phone crime on low-standard housing against 28% at stations. A pooled C5 will therefore tend to confirm through offence mix. Within robbery, hubs track the city: stations 0.91 (0.69–1.19), retail 1.15 (0.90–1.52). The definition of "hubs" also differs: the Glossary has "rail stations, bus terminals and commercial classes", C5 has "stations and middle-standard retail". | Before the vault opens, amend C5 to a within-offence contrast (phone robbery and phone theft separately, or a mix-standardized ratio), or drop it. Use one definition of hubs. |
| N-7 | m | Fig. 6g vs Results ms l.57 and Statistics ms l.135 | Fig. 6g lists six claims (C1–C5 plus H1, "Best model beats negative binomial (CRPS), Holm P < 0.05, pending (2026)") and a "Prospective window Nov 2026–Mar 2027". Results says "Five claims". Methods lists C1–C5 only and never defines H1 or the prospective window. | Add H1 and its criterion to Statistics and describe the prospective window in Methods, or remove both rows from Fig. 6g. |
| N-8 | m | Discussion ¶3 (ms l.65) | "transit hubs and middle-standard retail for evening phone theft": Results reports evening peaks only for robbery ("Robbery on retail, high-rise and service parcels peaks between 19:00 and 22:00, and at rail stations at 18:00"). Fig. 4a is phone robbery. No phone-theft peak hours are given. | Either report the phone-theft peak hours by class in Results, or change this to "evening phone robbery". |
| N-9 | m | Abstract (ms l.11) | "a distinct crime profile, robust to district-level risk": with district effects the rates of central classes roughly halve, and the top class changes for 5 of 15 crime types. | "whose ordering survives district-level risk". |
| N-10 | m | Abstract (ms l.11) | The replication claim for rhythms is attached to the robbery finding (see R-14). | As in R-14. |
| N-11 | m | Fig. 3c vs Methods ms l.99 | Fig. 3c plots "parcel types only" (filled) and "all cell classes" (hollow). Methods defines the statistic "across parcel types". The legend does not define the markers. The reported median 0.85 matches the filled markers, but readers cannot tell whether streets, stations and favelas were validated. | Define both markers in the legend and Methods, and say explicitly which classes the all-class check validates and which it does not. |
| N-12 | m | Intro ms l.13; Limitations ms l.73 | "lacks usable coordinates, most of all at homes and stations" and "suppressed more often at homes and stations": ED Fig. 2a shows public transport theft/robbery 96% geocoded. Homes (19%) are supported; stations are not shown. | Report reconciled shares by stratum (part of R-98), or drop "and stations". |
| N-13 | m | Results ms l.49 vs Fig. 6 legend | One paragraph mixes 96-district numbers (capture 53/52/52/65%; Fig. 6a) with exploration-district numbers (ceilings; Fig. 6b) without saying so. The Intro promises that "all analyses of the atlas use 77 exploration districts". | Add "(all 96 districts; development)" after the capture numbers in the text. |
| N-14 | m | Fig. 4a,b vs Results ms l.33 | Fig. 4b shows the model profile on low-standard housing (≈ 21% of weekday robbery in each of 04:00 and 05:00, near zero 07–18h). The text now says the model-free count "confirms the direction but not the size" (16%). The figure displays the size the text disowns, and that size may be a zero-boundary solution (R-101, deferred). | Overlay the model-free share (16%, 12–21%) on Fig. 4b, or add a legend note that the model magnitude is not supported. |
| N-15 | m | Results ms l.35; Discussion ms l.65 | The "19 times its daily mean" per-pedestrian peak at 03:00 is stated without uncertainty. Night-time survey support is thin (R-113, deferred and undisclosed), yet the figure drives the "before dawn" implication. | Add a Limitations clause on the night-time denominator, or pool hours 00–04. |
| N-16 | m | Fig. 6a legend | The plot shows "Chance" and "Ensemble, geocoded only" lines and a 28% annotation at 1% of area. The legend and text mention none of them (R-88 residue). | Add them to the legend, and cite the geocoded-only curve in the text or remove it. |
| N-17 | s | Fig. 6b legend | The legend says "within-tract variation", but the panel's key is "when (within unit)" and it includes district units. | Write "within-unit". |
| N-18 | m | ED Fig. 5a | Hatched bars for "2026 (sealed; no values yet)" are drawn at a fixed height (≈ 0.582), which reads as data. The numbers above the bars (0.111, 0.115, …) are unexplained (Brier?). | Remove the placeholder bars, or draw them as empty outlines with no height. Define the numbers in the legend. |
| N-19 | m | Results ms l.39; ED Fig. 2d | ED Fig. 2d (tissue turnover vs month-to-month variability, ρ = 0.13) is never cited and supports no sentence. | Cite it in the "stable tissue" sentence or cut it. |
| N-20 | m | Event study (Results ms l.45; Methods ms l.119) | "did not change street crime" reads a null as absence. The bootstrap fixes controls. The estimator is called "in the spirit of ref. 40" but is a stacked treated-vs-never-treated comparison. | "We detected no change …; effects outside −14% to +5% are excluded." Describe the estimator as such and resample controls, or disclose that they are fixed. |
| N-21 | m | Intro ms l.13 (ref. 12); ref. 35; ms l.35 (refs 32, 33) | Ref. 12 (Andresen, Curman & Linning 2017, trajectories by crime type) is cited as a facility/land-use study. Ref. 35's title is truncated ("A stab in the dark?"). Ref. 32 is cited for hourly ambient estimates (R-58 asked for it to be cited for the denominator problem). | Replace or re-describe ref. 12, and complete the ref. 35 title: Tompson, L. & Bowers, K. "A stab in the dark? A research note on temporal patterns of street robbery". |
| N-22 | s | Statistics ms l.135 | "P values are two-sided", but the clock permutation test (H above its null) is one-sided by construction. | Say so. |
| N-23 | m | Discussion ¶1 (ms l.61) | "recorded crime has a phenotype" inverts the mapping (§2). | As in §2. |
| N-24 | m | Glossary (ms l.87); Results ms l.23 | "Tissue" is defined as composition only, while the title's defence needs composition plus state (§2). | As in §2. |
| N-25 | m | Results ms l.49 | "fix most of where crime occurs" survives (R-32). | "account for". |
| N-26 | m | Methods ms l.127 | The language-model decision layer (Brier 0.1079 vs 0.1084) is still present (R-03 should_fix), and ED Fig. 6 calls it "Laya-FT". | Delete it or move it to Supplementary Information. |
| N-27 | s | Panel citation order | Fig. 4 panels are first cited a, d, b, f, c, e. Fig. 1c,d and ED Fig. 2b are uncited. | Reorder the Fig. 4 panels to a–f in citation order (or the text), and cite or cut the uncited panels. |
| N-28 | see N-14 | — | (merged into N-14) | — |
| N-29 | m | Clock section (ms l.33–35; Methods ms l.107, 111) | "Robbery" is ambiguous: Fig. 4a is phone robbery, while Fig. 4b,c and the model-free check say only "robbery". | Specify "phone robbery" (or "all street robbery") everywhere (R-62). |
| N-30 | m (exposed) | ED Fig. 8 ("Cross-excitation (Knox) … mean ratio 1.12; max 1.68; 63 sig. pairs"); ED Fig. 9a | The ED shows near-repeat excess at 400 m × 14 days, strongest favela→favela. This is short-term dependence below the tract-month scale. The main text never mentions it while generalising the month-to-month claim. | Resolve together with R-49/R-56: one sentence in Results restricting the claim to the tract-month scale, citing the Knox result. |
| N-31 | s | Fig. 2f | The x-axis says "Number of parcel types", but the selected point is 14 *clusters* before refinement (as the legend says). | Relabel it "Number of clusters". |
| N-32 | s | Methods ms l.95 | "refined by merging four clusters with less than 0.3% of parcels and by separating high-rise parcels …, giving 12 types". The arithmetic from 14 only works if the four are merged into one. | State what the four were merged into. |
| N-33 | s | Abstract | "A persistent effect of place … explains more": a residual variance component accounts for variance, it does not explain it. | "accounts for more". |
| N-34 | m | Discussion ¶2 (ms l.63) | "applies to any city that forecasts crime by small area and month" generalises a São Paulo magnitude. "The 19 held-out districts and the 2026 data test how far they replicate" is a within-city test presented as a test of travel. | "The ceiling's logic applies to any city; its size depends on counts and must be estimated locally." Say that the vault tests within-city replication only. |

### 3b. Naming and palette (R-19/R-82/R-86 residue)

- **Corner type.** It is "corner housing" (text, ms l.45), "Corner residential" (Figs 1, 3, 5e) and "corner lots" (Figs 2d, 4). Use one name and add it to the glossary.
- **Parcels without a cadastral record.** They appear as "No cadastral record" (Fig. 1), "Unrecorded" (Figs 3, 4, 5e) and "parcels without cadastral record" (glossary). Use one name.
- **Parcel family.** It is "parcel family" in the glossary and text but "Class this year / Class next year" in Fig. 5d and "% parcels changing class" in ED Fig. 2d. A *cell class* is a different glossary term. Relabel the figures "family".
- **"Sector".** ED Fig. 5f says "Correlation within sector" and "all sectors × months", a Portuguese calque of *setor censitário*. Write "tract".
- **Programs.** They are named "transport, dense-centre, peripheral-logistics and residential crime" in Results (ms l.29) but labelled by classes in Fig. 3d ("P1 · rail stations + bus terminals" …). Add the Results names to the Fig. 3d labels.
- **FCU.** "Favelas (FCU)" is still in ED Fig. 1b (R-81 residue). Fig. 1a still lists "Interstitium and vessels", which was dropped from the text (R-21).
- **Palette (R-86, consider, unresolved).** Fig. 1 reverses the residential blues and commerce oranges relative to Figs 2–5. Low-rise low-standard is dark navy in Fig. 1 but pale blue in Figs 2–5; "Low-rise mixed, wholesale" is dark red-orange in Fig. 1 but salmon in Fig. 3a. Tissue domains (Fig. 2e) reuse type-like hues. Use one type palette everywhere.
- **Method names.** Fig. 6d, ED Figs 4–5 use product and acronym names (LightGBM core/full, BYM2, SPDE/LGCP, Chronos, MaxEnt, PAI, ECE) that Methods does not use or define. ED Fig. 4 omits three baselines that Methods lists: persistence, seasonal naïve and prospective hot-spotting. Add a key in the ED Fig. 4 legend and reconcile the method list.
- **ED Fig. 8.** The last row is truncated ("not run: OD 2017 used for ambient populati…"), and "not run in this version" is development language.

### 3c. Numbers checked and found consistent

| Quantity | Value | Matches |
|---|---|---|
| Fiscal parcels | 1,651,813 / 1.65 million | Fig. 1 legend |
| Police records, 15 crime types | 0.69 million | ED Fig. 2a sum ≈ 686k |
| Geocoded phone-crime events | 121,434 and 100,347 (82.6% geocoded) | "17% reconciled" |
| Finer-scale check | median ρ 0.85 | Fig. 3c filled markers; ranges 0.93–0.95 and 0.62–0.74 match |
| Crime programs | k = 4, stability 0.96 | ED Fig. 2b |
| Clock tests | P ≤ 0.005, r = 0.93, r = 0.90, P = 0.07 | Fig. 4d |
| Per-km vs per-pedestrian ordering | ρ = 0.75 | Fig. 4f |
| Weekend ratio | 0.4 | Fig. 4e ≈ 0.37 |
| Out-of-sample R² | 0.22 / 0.26 / 0.25 / 0.31 / 0.48 | Fig. 5a |
| Variance split | 42/48/23 with cov. −13%; 18/58/16 with +7% | Fig. 5b |
| Lag-3 correlation | r = 0.63 | Fig. 5c |
| Annual permanence | 98.2% | Fig. 5d |
| Phone crime change | −20% overall, −40% robbery, −2% theft | Fig. 5f, ED Fig. 6 "ratio 0.80" |
| Capture at 5% of area | 53 / 52 / 65% | ED Fig. 4 (53.0, 51.7) and Fig. 6a |
| Ensemble R² vs noise ceiling | 0.80/0.92; 0.018/0.56; 87–99% | Fig. 6b |
| Scale-expected excess variance | 88/86% | Fig. 6c |
| Best-model CRPS gain | −0.025 (4%) | ED Fig. 4: 0.5945 vs 0.6193 |
| Flagged area vs recorded crime by income | 36/3% and 26/7%; calibration within 5% | Fig. 6f |

No numeric disagreement between the abstract, Results, Methods and the main figures was found. All the numeric disagreements are in ED Fig. 6 and ED Fig. 3 (N-1, N-2).

---

## 4. Coherence read, from title to final sentence

**Does the paper tell one story?** Mostly, yes, and much more than in round 1. The story is: *read the city as a tissue; composition structures which crime and when; a persistent state of places carries more of how much; what remains month to month is undetectable at tract scale and is not captured by forecasting.* The abstract, the Intro's three questions, the Results order (§1 tissue → §2 which → §3 when → §4 how much → §6 what remains) and Discussion ¶1 now say the same thing. The analogy audit has moved to ED with one honest Discussion paragraph, and the benchmark has shrunk to one paragraph.

**Sentences and panels that do not yet serve it:**

1. **The title.** It works as a framing only if "tissue" includes state (§2). With the current glossary, the title says the opposite of the paper's high-crime finding.
2. **Results §5 "Rates move within a stable tissue"** (ms l.45), with Fig. 5e,f, ED Fig. 3 and C5. It is the only Results subsection that answers none of the three questions the Intro poses. It now carries mostly negative or hedged content (robbery fell across the fabric; drivers untested; a null event study), and its confirmatory claim C5 is confounded (N-6). Either promote "how rates change within a stable tissue" to a stated fourth question (abstract and Intro) with C5 repaired, or move the subsection to ED and keep one sentence.
3. **Fig. 3d,e (crime programs).** No later sentence uses them (R-89 consider).
4. **Fig. 2a (UMAP) and Fig. 2c,e (tract pies, domains).** These are decorative. Domains reappear only in ED Fig. 5d and ED Fig. 7d (R-78, R-90).
5. **ED Fig. 2d and ED Fig. 7d.** Neither is cited for a claim.
6. **Methods: the language-model decision layer** (ms l.127). It is off-story (R-03).
7. **The near-repeat evidence (ED Figs 8, 9a).** It is the one piece of evidence in the paper that speaks against the generalised month-to-month claim, and the story ignores it (R-49, R-56, N-30).
8. **The final sentence** (ms l.73) is a limitation with a placeholder. Nature Discussions usually end on the claim or its bound. Consider moving the limitations paragraph before the analogy paragraph, so that the paper ends on "It is useful as an instrument that can fail its tests". Alternatively, end on the bound: forecasting adds little to a stable map.
9. **Discussion ¶3's "evening phone theft".** It is not established in Results (N-8).

---

## 5. Decision recommendation for the next round

**Recommendation: Major Revision.** It is narrow, and Minor is within reach.

**Why not Minor:**

- **Two must_fix text items are NOT RESOLVED.** R-49 (Knox placement, D-3) and R-56 (scope of the noise claim) are untouched. In the protocol's derivation, a must_fix NOT_ADDRESSED item sets a Major floor.
- **Five PARTLY items carry a must_fix residual.**
  - R-14: the abstract attaches replication to the exploratory robbery finding.
  - R-32: one "fix" survives, and the cross-term is not read in Results.
  - R-36: unvalidated profiles drive inferences, and the Fig. 3c scope is ambiguous.
  - R-57: recorded-crime bias does not yet qualify the dependent results.
  - R-01 is should_fix only.
- **Blocking issue B-1 (D1) remains open.**
  - Its acceptance criterion required R-95–R-110 to be reported, and most are deferred.
  - Only 2 of the 16 deferred analyses are disclosed in the text.
  - The revision itself surfaced new evidence for B-1's reconciliation concern: geocoded-only counts reject Poisson more often than reconciled counts (N-3).
- **The confirmatory protocol has not been amended, and that is time-critical.**
  - C2 is still ρ > 0 and C4 still uses event-level permutation (R-107/R-108).
  - OSF is still "planned".
  - C5 is now visibly confounded by offence mix (N-6).
  - H1 is undocumented (N-7).
  - These must be fixed *before* the vault is opened, or the single confirmatory test will be spent on criteria the panel has already flagged.
- **ED Fig. 6 reintroduces, in Extended Data, almost every phrase the text revision removed (N-1).**

**What has clearly improved:**

- B-2 (headline claims outrun statistics) is largely resolved: "noise", "memory", "fixes", "limit of predictability", the 41% lead and the hub-concentration claim are gone or corrected.
- B-3 (criminological reading) is resolved for guardianship, the decline, persistence, the hot spots comparison and positioning. It remains open for recorded-crime bias (R-57) and for the noise-claim scope (R-56).
- C1 is downgraded from a block to four small edits (§2).

**Shortest path to Minor or Accept in round 3** (no new analyses beyond what is already run, except where marked):

1. Fix R-49/R-56 in text: one Results sentence on the Knox result and the tract-month scope; restrict the abstract and Discussion to phone crime at the tract-month scale; cite Johnson et al. 2007, Gorr & Lee 2015 and Bernasco & Steenbeek 2017 (verify each).
2. Make the four C1 edits in §2 and the one-sentence R-14 abstract fix.
3. Mark the unvalidated, reconciliation-dependent profiles at their point of use, and define the Fig. 3c markers (R-36, R-38, N-11).
4. Qualify the dependent results for recorded-crime bias in one paragraph (R-57).
5. Regenerate ED Fig. 6 and ED Fig. 3 (N-1, N-2), and fix ED Fig. 5a (N-18).
6. Address N-3 in text. Report the noise ceiling on geocoded-only counts if possible (this extends the in-scope R-97).
7. **Before the vault opens:** amend C5 to a within-offence contrast, add H1 to Methods, tighten C2 and C4 or state why not, and register on OSF (R-108). This is the one deferral that cannot wait.
8. Add one Limitations or Methods sentence listing the deferred analyses (R-96, R-99, R-101, R-105–R-107, R-113, R-121) and what each would bound.

---

*Verifier: re-review seat (single model family; persuasion-blind; no response letter read). Files read: `paper/manuscript.md`; `paper/review/decisao_editorial.md` §§2, 4.a–4.e, 5; `figures/out/dev/fig1–fig6.png`, `ed1–ed9_*.png`. Written only to `paper/review/rereview.md`.*
