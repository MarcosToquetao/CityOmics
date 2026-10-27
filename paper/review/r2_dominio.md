# Peer Review Report: Peer Reviewer 2 (Domain)

- **Title**: Crime as a phenotype of urban tissue
- **Venue**: Nature Cities (Article)
- **Review Date**: 2026-10-19
- **Review Round**: Round 1 (development-stage manuscript; 77 exploration districts; confirmatory placeholders deliberately left open and not penalized)
- **Phase 1 commitment**: `paper/review/r2_dominio_fase1.md` (no dissent from that plan)

contract_role: domain

## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: block
trigger: "A core claim (headline finding, stated mechanism, or stated novelty) misrepresents or contradicts established crime-and-place evidence without acknowledging it"
block_class: repairable

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

### Reviewer Information

**Reviewer Role**: Peer Reviewer 2 (Domain).

**Reviewer Identity**: Crime-and-place scholar (environmental criminology) with research experience in Latin American cities. Expertise covers the law of crime concentration, routine activity and crime pattern theory, crime generators and attractors, ambient population and guardianship, temporal patterns of crime, robbery and mobile-phone theft, and the biases of police-recorded data.

**Review Focus**: Whether the criminology is right. I checked that the theory is used as the field defines it, that citations support their sentences, that the contribution is placed correctly against crime-and-place research, that results are read soundly in the São Paulo context, and that the prevention implications follow from the evidence.

### Recommendation and Confidence

**Recommendation**: Major Revision.

**Confidence Score**: 4. Core expertise covers the criminological claims. I do not judge the omics-side methods.

**Calibration Status**: `NOT_CALIBRATED`

### Summary Assessment

The manuscript reads São Paulo as a "tissue". Fiscal parcels are cells and census tracts are spots. It attributes 15 police-recorded crime types to 19 cell classes, describes a daily clock for each class and normalizes it by an ambient-population estimate. It then splits between-tract variance into composition, a persistent residual it calls "memory" and noise, and bounds monthly forecasting with a Poisson ceiling. The empirical work is large, careful and unusually self-critical for this literature: the held-out design, the positive control and the equity audit stand out. The weak point is the criminological reading of the results.

Four headline interpretations go beyond the evidence or contradict established findings without saying so:
- Dawn robbery "tracks the absence of guardians … rather than the volume of targets". This is asserted, not tested, and the paper's own weekday–weekend contrast cuts against it.
- The 2022–2025 decline "came from the diffuse fabric". This mixes up place class with the robbery-versus-theft mix, and it runs against micro-place crime-drop evidence that the paper does not discuss.
- "Memory" mixes up persistent unobserved differences between places with true state dependence.
- "Month-to-month variation is mostly noise". This generalizes from phone crime at the tract-month scale and ignores the near-repeat literature.

The gap statement also misdescribes how micro-place criminology measures crime. The attribution is positioned against omics rather than against its criminological precursors. And recorded-crime bias in the Brazilian setting is acknowledged but never used to qualify the results that depend on it.

All of this can be fixed by reframing, adding literature and running a few targeted analyses. The core descriptive contribution survives, so I recommend Major Revision.

### S1: Sound anchoring in the concentration literature, including Latin America
The introduction places the study within the law of crime concentration and its long-run stability, and cites Latin American and Brazilian replications. Few urban-science papers do this. It also flags mobile-phone crime as a crime of global concern, which justifies the focus on phone crime.
**Evidence Anchor**: text: Introduction ¶1 "The pattern holds in Latin American cities"

### S2: Offence disaggregation that limits enforcement-driven recording
The paper uses 15 offence-specific outcomes rather than total crime. It deduplicates the phone base against the main base, and it excludes police-initiated offences, domestic violence and sexual violence. Excluding police-initiated offences removes the part of police data most driven by enforcement and least by victimization. This is good practice for crime-and-place work.
**Evidence Anchor**: text: Methods, Phenotype panel "Offences initiated by police, domestic violence and sexual violence were excluded."

### S3: Hourly denominators that separate people present from people on the street
The population at risk is a long-standing problem for spatial crime rates (refs 32–34). The authors build hourly ambient-population estimates and separate people present from people walking on the street. Hourly, street-specific denominators are what the generator/attractor and guardianship questions actually need.
**Evidence Anchor**: text: Results, clock section "separating people present from people walking on the street"

### S4: Falsifiable checks that a criminologist would want
Two checks guard against an artefact of the areal model: point validation against geocoded events and a positive control. Traffic injuries peak on arterial streets, as expected from exposure to traffic.
**Evidence Anchor**: text: Results, signature section "As a positive control, traffic injuries had their highest rate per km among street classes on arterial streets"

### S5: An equity audit of forecasting
The authors report calibration by income quintile and where the flagged area falls. This engages directly with the predictive-policing critique, and venue readers will expect it.
**Evidence Anchor**: text: Results, forecasting section "but the flagged area concentrated in richer tracts"

### S6: A substantively important pattern for Latin American megacities
On low-income housing, phone robbery is concentrated before dawn on weekdays. To my knowledge this has not been quantified at this resolution for a Latin American city. It fits the long early-morning commutes from the urban periphery and is directly relevant to policy.
**Evidence Anchor**: figure: Fig. 4b — weekday robbery against pedestrians on low-rise low-income housing

### S7: Candid scope statements
The paper says plainly that attribution is associational and that the analogy loses to simpler urban methods in some modules. This candour is welcome and makes the work easier to trust.
**Evidence Anchor**: text: Discussion, limitations "Attribution is associational, and only the event study approaches a causal design."

### W1: The gap statement misrepresents how crime-and-place research measures crime
**Problem**: The introduction says crime "is usually counted in areal units". It then frames the field's limitation as having to infer components from aggregates. Since the hot-spots work of the late 1980s and the Seattle street-segment studies (ref 3, which the paper cites), crime-and-place research has mostly counted crime directly at addresses, street segments and intersections, precisely to avoid aggregation. Variance-partitioning work shows that most of the variability lies at the segment level, not at the neighbourhood level (Steenbeek & Weisburd, J. Quant. Criminol., 2016; verified this session). So the field already measures components directly. The real reason this paper needs composition-aware attribution is specific to its data. Coordinates in the São Paulo police records are missing or suppressed for part of the events, especially at homes and stations, as the limitations themselves say.
**Evidence Anchor**: text: Introduction ¶1 "Crime, however, is usually counted in areal units that mix many parcels and land uses"
**Why it matters**: Criminology referees will read the motivating gap as a straw man. The stronger and honest justification is incomplete geocoding plus the lack of a city-wide parcel inventory. That justification makes the method necessary here and transferable to other Global South police datasets.
**Suggestion**: Reframe the gap in two parts: (i) micro-place studies exist but rarely cover the full parcel composition, all offence types and the hour together; (ii) incomplete or imprecise geocoding in Brazilian police data (with the share of non-geocoded events by stratum) forces inference from aggregates. Cite foundational micro-place work (Sherman, Gartin & Buerger, Criminology 1989 [UNVERIFIED metadata]; Eck & Weisburd, Crime Prev. Stud. 1995 [UNVERIFIED metadata]) and Steenbeek & Weisburd 2016.
**Severity**: Major
**Confidence**: 4 — core expertise: micro-place criminology

### W2: The novelty of the attribution is set against omics, not against its criminological precursors
**Problem**: The attribution model, an expected count Σ_k E_sk λ_k with class rates constant across tracts, is presented as inverting spot deconvolution. In the social sciences this is Goodman-style ecological regression. In criminology, rates per type of facility or land use are an established object of study:
- the risky-facilities literature (Eck, Clarke & Guerette, Crime Prev. Stud. 21, 2007; verified);
- block-level models of crime generators, crime attractors and offender anchor points (Bernasco & Block, J. Res. Crime Delinq. 48, 2011; verified);
- risk terrain modeling, which assigns relative risk to environmental features (Caplan, Kennedy & Miller, Justice Q. 28, 2011; verified).

Studies crossing facility types with time of day also already exist (refs 15, 16). The constant-rate assumption also cuts against evidence that facility effects depend on context: in ref 12, the effect of commercial use is offset by density.
**Evidence Anchor**: text: Results, attribution section "This inverts spot deconvolution" and "the composition is known, and the rates are inferred"
**Why it matters**: The contribution claim reaches a criminology audience without the comparison that audience will make first. The genuine advances are real but they need stating: a wall-to-wall parcel typology, joint signatures across 15 offences, per-class clocks with hourly denominators, a predictability ceiling and held-out confirmation in a Global South megacity.
**Suggestion**: Add a paragraph that places attribution against ecological regression and the facility-risk, generator/attractor and RTM literatures. State what the composition-aware approach adds (exposure in metres of frontage, all classes at once, point validation). Report whether λ_k varies across tissue domains or income strata. At minimum, discuss context-dependence as a limitation.
**Severity**: Major
**Confidence**: 4 — core expertise: facility and land-use criminology

### W3: Guardianship is asserted as the mechanism for dawn robbery, not tested, and the paper's own data argue against it
**Problem**: The text concludes that dawn robbery tracks the absence of guardians rather than the volume of targets. Under routine activity theory, the ambient pedestrian population is at the same time a pool of targets, potential guardians and offenders; ref 34, cited by the authors, frames it that way. A high ratio of robberies to pedestrians fits low guardianship. It equally fits other explanations:
- high target suitability: commuters carrying phones on predictable paths to transit;
- offenders' own routines;
- darkness. Moving from daylight to darkness raised predicted street robbery 2.6-fold in London (Tompson & Bowers, J. Res. Crime Delinq. 50, 2013; verified).

Three further problems:
- The paper's own weekend ratio for low-income housing is 0.4. Guardianship at dawn is no higher on weekends, yet robbery falls. That pattern points to the convergence of offenders with weekday commuters, which is the target side of the triangle.
- Tract-level pedestrian density averages away the concentration of commuters at bus stops and along routes to transit. So the relevant "volume of targets" is not measured.
- At 03:00 the survey-based denominator is tiny and leaves out non-resident and leisure populations. This inflates the per-pedestrian peak (19 times the daily mean).

Finally, robbers' location choices in Chicago were largely invariant across hours of the day (Bernasco, Ruiter & Block, J. Res. Crime Delinq. 54, 2017; verified). That result bears directly on "a clock that is not the clock of crowds" and is not discussed. Crime pattern theory, with its activity nodes and the paths between home, work and transit, is the natural frame for a journey-to-work pattern, and it is never named.
**Evidence Anchor**: text: Results, clock section "Dawn robbery in the periphery thus tracks the absence of guardians, as routine-activity theory predicts" and "rather than the volume of targets"
**Why it matters**: This sentence turns a descriptive finding into a mechanism and then into a prevention prescription (W8). Without a test, the mechanism claim does not hold.
**Suggestion**: Reword to "consistent with low guardianship and with offenders converging on commuters' paths to transit". Add a darkness-versus-guardianship test. São Paulo has had no daylight saving time since 2019, so sunrise time moves by more than an hour across the year. If the 04:00–06:00 share follows sunrise across months, visibility matters, as in the darkness literature. Compare weekday and weekend dawn hours directly, and use distance to bus stops as a target-convergence proxy. Cite Bernasco, Ruiter & Block 2017 and Tompson & Bowers 2013, and name crime pattern theory (Brantingham & Brantingham 1993 [UNVERIFIED metadata]).
**Severity**: Major
**Confidence**: 4 — core expertise: robbery timing and guardianship

### W4: The decline is attributed to "the diffuse fabric", which mixes up place class with offence mix and contradicts micro-place crime-drop evidence without saying so
**Problem**: The paper itself says phone crime fell through robbery (−40%) rather than theft (−2%). Rail stations and medium-standard retail are plausibly theft-dominated (pickpocketing in crowds), and local streets and low-income housing robbery-dominated. If so, "hubs kept their rates while the diffuse fabric responded" may simply restate the robbery–theft divergence in terms of place. The opposite pattern is also on record: in Seattle the crime drop was produced by a small group of street segments with steeply declining trajectories (ref 3; verified this session), and Boston's citywide robbery trends were driven by a small number of segments and intersections (Braga, Hureau & Papachristos, J. Res. Crime Delinq. 48, 2011; verified). The manuscript does not engage with either.

The paper also implies that the diffuse fabric "responded" without naming what it responded to. Two São Paulo-specific candidates fall within the window:
- the federal Celular Seguro device- and bank-blocking programme, launched in December 2023 (verified this session). It could change both offender payoffs (the security hypothesis; ref 6) and victims' reporting behaviour;
- the municipal Smart Sampa camera expansion, from 2023–2025 (verified that it exists; its spatial rollout is not verified).
**Evidence Anchor**: text: Results, decline section "It came from the diffuse fabric: local streets fell faster than the city"
**Why it matters**: The decline is one of the five confirmatory claims (A-R8) and supports the prevention advice that "hubs probably need tools of their own". If it reflects offence mix, the inference about places is wrong.
**Suggestion**: Run the rate–composition decomposition separately for phone theft and phone robbery, and report the theft/robbery mix of each class. Discuss the contrast with refs 3 and Braga et al. 2011: units (tracts versus segments), offence and context. Name candidate drivers and possible reporting changes in the period. Replace "crime receded to its niches" with a descriptive statement.
**Severity**: Major
**Confidence**: 4 — core expertise: crime trends at places; São Paulo context partly verified

### W5: "Memory" mixes up persistent unobserved heterogeneity with state dependence
**Problem**: The "stable memory" is the covariance of residuals across years after removing parcel composition. That quantity picks up any time-invariant feature the cadastre misses, including several the paper itself names as missing:
- informal street commerce outside favelas;
- bus stops, nightlife and drug markets;
- offender anchor points;
- the socioeconomic make-up of residents (tract covariates are left out of the tissue term);
- stable artefacts of geocoding or reporting.

None of these is memory in the sense of past crime causing future crime. Criminology draws this distinction explicitly between population heterogeneity and state dependence (Nagin & Paternoster, J. Quant. Criminol. 16, 2000; verified). The supporting citation (ref 36, collective efficacy and violence) is cross-sectional, about violence among residents, and does not speak to persistence. Phone crime, committed largely by non-residents in commercial and transit places, fits place management and risky facilities better.
**Evidence Anchor**: text: Abstract "Beyond composition, places carry a stable memory of crime."
**Why it matters**: This is a headline claim in the abstract and Discussion, which call for research on why places "remember". The term implies a dynamic mechanism the analysis cannot identify.
**Suggestion**: Rename it, for example "persistent place effect beyond composition". Show how much of it tract covariates and known unmeasured generators absorb. Use "memory" only if a dynamic test is added (for example, lagged crime shocks predicting later crime, conditional on place fixed effects). Replace or add to ref 36 with place-management and risky-facility work (Eck, Clarke & Guerette 2007).
**Severity**: Major
**Confidence**: 4 — core expertise: trajectories and stability of crime at places

### W6: "Month-to-month variation is mostly noise" goes beyond the offence and scale tested
**Problem**: The dispersion result concerns phone crime in tract-months in 2025. With low monthly means, a χ² test on 11 degrees of freedom has limited power. "Consistent with Poisson" is not the same as "is noise". When crimes are sparse relative to places and time windows, much apparent concentration and variation is expected by chance. The concentration-measurement literature formalizes this (Bernasco & Steenbeek, J. Quant. Criminol. 33, 2017; verified). Concentration also differs across temporal scales (Haberman, Sorg & Ratcliffe, J. Quant. Criminol. 33, 2017; verified).

Repeat and near-repeat risk works at days to weeks and within about 200 m (Johnson et al., J. Quant. Criminol. 23, 2007; verified), which tract-month aggregation cannot see. The Knox analysis exists in Extended Data but is not brought into this argument. The forecasting literature also already separates chronic from short-lived hot spots (Gorr & Lee, J. Quant. Criminol. 31, 2015; verified). The ceiling is a useful formal statement of that distinction rather than a new phenomenon.
**Evidence Anchor**: text: Introduction, final ¶ "and that month-to-month variation is mostly noise."
**Why it matters**: This is one of the three headline findings and the basis for the forecasting implications. Stated generally, it contradicts well-replicated short-term contagion results for burglary and robbery.
**Suggestion**: Limit the claim to phone crime at the tract-month scale. Report the power of the dispersion test at typical tract means. Bring the near-repeat (Knox) results into the main text, and say how sub-monthly or sub-tract dynamics would change the ceiling. Place the result relative to chronic and temporary hot-spot work.
**Severity**: Major
**Confidence**: 4 — core expertise: near-repeat and forecasting literature

### W7: Recorded-crime bias in the Brazilian context is acknowledged but not used to qualify the results that depend on it
**Problem**: The limitations note that police records undercount crime unevenly, with no source and no consequence for any interpretation. Three results are plausibly affected by uneven reporting:
- **The income gradient of the flagged area.** In Brazil, whether a phone theft is reported likely depends on insurance, device and line blocking, and access to online reporting, all of which vary with income. Differential victim reporting moves predicted hot spots toward high-reporting areas even when models are trained on victim reports, in a simulation calibrated to Bogotá (Akpinar, De-Arteaga & Chouldechova, FAccT 2021; verified).
- **The 2022–2025 decline** (see W4).
- **The favela and peripheral signatures.** There, police access, trust and criminal governance shape both offending and reporting.

The divergence between recorded and true crime is also larger at small geographies (Buil-Gil, Moretti & Langton, J. Exp. Criminol. 18, 2022; verified). The reconciliation step adds a further assumption: non-geocoded events are spread like geocoded events of the same stratum, so it inherits any spatial bias in geocoding.
**Evidence Anchor**: text: Discussion, limitations "Police records undercount crime unevenly across places and types of crime."
**Why it matters**: The equity conclusion and the decline claim both depend on recorded crime tracking victimization similarly across income levels and over time. The paper never examines whether it does.
**Suggestion**: Discuss reporting propensity for phone theft versus robbery in Brazil, citing national or São Paulo victimization-survey evidence (for example, the 2013 national victimization survey [UNVERIFIED as to authorship and figures]). Run the income audit and the decline separately for robbery, which is likely better reported than theft. Report the share of geocoded events by income quintile and by year. Say that the 26% versus 7% recorded split may itself overstate the share of richer tracts.
**Severity**: Major
**Confidence**: 4 — core expertise: police-data bias; Brazil-specific reporting rates not verified

### W8: Prevention implications are overstated against hot-spot practice and the evidence
**Problem**: "More precisely than hot spots" reverses the usual ranking. Hot spots are micro places such as addresses and segments. The signature matrix gives class-average rates inferred from tracts. Because crime concentrates within types of facility (risky facilities: a few members of any facility type account for most of its crime; Eck, Clarke & Guerette 2007, verified), a class average does not say which retail parcels or stations to target. Time-specific targeting is already standard in hot-spots practice (for example, Koper, Justice Q. 1995 [UNVERIFIED metadata]).

The specific advice to improve lighting and staff bus stops between 04:00 and 06:00 has supporting evidence the paper does not cite. Street lighting led to at least a 36% reduction in night-time outdoor index crimes in a New York City randomized trial (Chalfin, Hansen, Lerner & Parker, J. Quant. Criminol. 38, 2022; verified). But "rather than extending evening patrols" has no basis in any analysis reported. Latin American evidence on place-based policing also shows displacement of property crime to nearby streets (Blattman, Green, Ortega & Tobón, J. Eur. Econ. Assoc. [year and pages to verify]). Readers at the venue would expect that evidence to be weighed.
**Evidence Anchor**: text: Discussion, prevention ¶ "The results locate prevention more precisely than hot spots do."
**Why it matters**: Practitioners will read prescriptions in a Nature-family journal as evidence-based. Here they come from descriptive, ecological evidence.
**Suggestion**: Present the implications as hypotheses to test. Cite the lighting and hot-spot evidence, including Latin American trials. Drop the comparison with hot spots and the comparison with evening patrols. Say that class rates show where to look and that micro-place hot spots show where to act.
**Severity**: Major
**Confidence**: 4 — core expertise: place-based prevention evidence

### W9: Several headline signature enrichments are partly definitional
**Problem**: Some offences are defined by the place type recorded in the police report: "robbery on public transport" and "residential burglary". Reconciliation spreads non-geocoded events by those same place-type strata, and rail-stratum events go only to tracts near stations. Their enrichment at stations, terminals and houses is therefore expected by construction. Which type of house or transport class wins remains informative, but these cases work as positive controls rather than discoveries. Cargo robbery in favelas may also reflect where cargo is unloaded or recovered rather than where the robbery happened. That is my field knowledge and is not verified for these records.
**Evidence Anchor**: text: Results, signature section "Robbery on public transport is enriched at bus terminals and rail stations"
**Why it matters**: The "11 distinct classes at the top" claim, part of confirmatory claim A-R6, is partly inflated by definitional cases.
**Suggestion**: Label place-defined offences as controls. Report the count of distinct top classes with and without them. Lead with the offences that are not defined by place: phone and street robbery, wire theft, lethal violence.
**Severity**: Minor
**Confidence**: 3 — core expertise on offence coding; how SSP records specific location fields not verified

### W10: Introduction citations describe their sources inaccurately
**Problem**: Ref 12 (Twinam 2017) estimates the effect of commercial and mixed uses on crime in their vicinity in Chicago, offset by density. It is not a parcel-level study of a single land use. Ref 13 (Andresen, Curman & Linning 2017; verified this session) studies street segments and intersections in Vancouver across eight crime types, not single crime types at parcels.
**Evidence Anchor**: text: Introduction ¶1 "Parcel-level studies isolate single land uses"
**Why it matters**: Correcting the descriptions would not change the core argument, but the gap claim should rest on accurately described prior work.
**Suggestion**: Re-describe both studies, or cite genuinely facility-level work (for example, risky facilities) for this sentence.
**Severity**: Minor
**Confidence**: 4 — verified at abstract level

### W11: The time-of-day evidence is presented one-sidedly
**Problem**: Ref 14 proposes summary indicators of when crime occurs. It does not show that place effects vary by hour. The sentence also leaves out direct counter-evidence. Bernasco, Ruiter & Block (2017; verified) found that the attraction of block attributes for street robbers barely varied by hour or weekday, except near high schools.
**Evidence Anchor**: text: Introduction ¶1 "time-of-day studies show that the criminogenic effect of a place changes with the hour"
**Why it matters**: The evidence on time-varying place effects is mixed. Presenting it as settled weakens the paper's position in the debate its clock results actually contribute to.
**Suggestion**: Present the debate as mixed and place the class clocks within it.
**Severity**: Minor
**Confidence**: 4 — verified at abstract level

### W12: The generator/attractor distinction is cited but not used where the analysis tests it
**Problem**: In the crime-and-place literature, comparing crime per unit of space with crime per person present is the standard operational test of generators versus attractors (refs 9, 10; Bernasco & Block 2011). The paper runs exactly this comparison but reads it only as "the ordering survives".
**Evidence Anchor**: text: Results, clock section "The ordering of classes survives division by the crowd."
**Why it matters**: This is a missed chance to give back to theory: which classes behave as generators and which as attractors or low-guardianship settings.
**Suggestion**: Classify the cell classes by how their rank changes from per km to per pedestrian, and interpret the result in generator/attractor terms.
**Severity**: Minor
**Confidence**: 4 — core expertise

### W13: The feedback-loop citation fits police-discovered crime, not victim-reported phone crime
**Problem**: Ref 48 shows the feedback loop for police-discovered drug offences. Phone crime enters the data mostly through victim reports, and the paper excludes police-initiated offences. The relevant mechanism for these data is differential victim reporting (Akpinar et al. 2021; verified).
**Evidence Anchor**: text: Discussion, forecasting ¶ "because police-recorded crime feeds back into where police look"
**Why it matters**: The risk is real, but its stated mechanism is the wrong one for the crime analysed.
**Suggestion**: Separate discovery feedback from reporting bias and cite accordingly.
**Severity**: Minor
**Confidence**: 4 — core expertise

### W14: The "limit of predictability" citation measures a different quantity
**Problem**: Ref 41 estimates an entropy-based upper bound on predicting an individual's location sequence. The paper's ceiling is a Poisson-variance bound on aggregate counts. Citing ref 41 suggests the two are the same.
**Evidence Anchor**: text: Results, noise section "the city sits close to its limit of predictability"
**Why it matters**: The citation does not support the claim it is attached to.
**Suggestion**: Use it as an explicit analogy or drop it. Ground the ceiling in the dispersion literature already cited (ref 39).
**Severity**: Minor
**Confidence**: 3 — adjacent field

### W15: São Paulo and Brazilian crime-geography literature is missing
**Problem**: Apart from one study of a Brazilian city (ref 5), the paper cites no work on crime in São Paulo. This matters for interpretation:
- Homicide in São Paulo has been tied to poverty, land use, drug markets and firearms (Ceccato, Haining & Kahn, Environ. Plan. A 39, 2007; verified).
- The entry of the Primeiro Comando da Capital into favelas was associated with an 11% fall in violent crime and no change in property crime (Biderman, De Mello, De Lima & Schneider, J. Quant. Criminol. 35, 2019; verified). This bears on the favela and peripheral signatures and on lethal violence.
**Evidence Anchor**: absence: Introduction, Discussion and reference list — expected engagement with São Paulo crime-and-place and criminal-governance research; checked Introduction, Results, Discussion, Methods, Data, reference list
**Why it matters**: Without local context, the signatures for favelas, low-income housing and lethal violence are read only through Global North theory. Criminal governance in São Paulo's periphery is a well-documented rival explanation.
**Suggestion**: Add a short paragraph on São Paulo's crime geography and criminal governance, and use it in reading the lethal-violence and peripheral-robbery results.
**Severity**: Minor
**Confidence**: 4 — regional expertise; two key works verified this session

### W16: "Places" is used for areal units, against field usage
**Problem**: In criminology, "places" means micro units such as addresses, facilities and street segments. The abstract applies "places" to areal units that mix land uses. It later says that "places carry a stable memory" when the unit is the census tract.
**Evidence Anchor**: text: Abstract "Crime concentrates in a few places, but mapped places mix many land uses"
**Why it matters**: Criminology readers will read "places" as micro-places, which confuses the scale of the claims.
**Suggestion**: Use "areas" or "tracts" for areal units, and keep "places" for micro-places.
**Severity**: Minor
**Confidence**: 4 — field terminology

### W17: The abstract compares forecasts with the "tissue map", but the benchmark baseline is history
**Problem**: The benchmark compares forecasts with the historical mean and a negative binomial model. Out of sample, the historical mean (R² = 0.48) beats tissue features (0.25). The practical claim is that monthly forecasts add little beyond a stable historical map, which is the map hot-spot practice already uses. It is not a claim about the tissue map.
**Evidence Anchor**: text: Abstract "forecasts add little beyond the tissue map outside a few hubs"
**Why it matters**: The wording credits composition with predictive value that comes from crime history.
**Suggestion**: Say "beyond a stable map of past crime", in line with the Discussion's "tissue and memory".
**Severity**: Minor
**Confidence**: 4 — reading of the reported results

### W18: The claim about earlier borrowing of biological vocabulary overlooks the Chicago School
**Problem**: Urban sociology and criminology adopted plant and human ecology (invasion, succession, natural areas) as an empirical research programme. Social disorganization theory grew from it. Criminology has also used epidemic and contagion models of violence as testable instruments, and the paper benchmarks one such import from seismology (ref 42).
**Evidence Anchor**: text: Introduction ¶2 "but as metaphor rather than as a measurement instrument whose outputs can be tested"
**Why it matters**: The novelty claim for the analogy is overstated against the field's own history.
**Suggestion**: Acknowledge the human-ecology tradition (Park, Burgess & McKenzie 1925; Shaw & McKay 1942 [UNVERIFIED metadata]) and say how a testable, measurement-level analogy differs from it.
**Severity**: Minor
**Confidence**: 3 — history of the discipline

### Criterion-Bound Judgements

Calibration status: `NOT_CALIBRATED`

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| D2: citations support their sentences | contract D2; domain reviewer Step 3a | PARTLY_MEETS | see W10, W11, W13, W14 | Most citations are accurate and canonical; several framing sentences rest on partial mismatches | Some checks at abstract level only; ref 46's content not verified (DOI resolves to an Elsevier record) | no, individually minor |
| D2: theory applied as the field defines it | domain reviewer Step 2 | PARTLY_MEETS | see W3, W5, W12 | Routine activity and generator/attractor theory are defined correctly but used to assert mechanisms not tested; crime pattern theory is never named | none identified | yes, guardianship and memory are headline claims |
| D2: literature coverage | domain reviewer Step 1 | PARTLY_MEETS | see W2, W6, W15 | Concentration literature well covered; precursors of attribution, near-repeat, concentration-measurement and São Paulo literatures missing | none identified | yes, through positioning |
| D2: contribution stated without overclaiming | domain reviewer Step 4 | PARTLY_MEETS | see W1, W2, W18 | Real advances exist but are framed against a mischaracterized field and against omics | none identified | yes |
| D2: domain reading of results | domain reviewer Step 3b | DOES_NOT_MEET | see W3, W4, W6, W7, W9 | Decline, dawn-robbery mechanism and "noise" readings go beyond, or contradict, established evidence without saying so | Exploration-stage results; confirmatory test pending | yes, triggers the D2 block (repairable) |
| D2: prevention implications warranted | domain reviewer Step 4; Public Policy anchors | PARTLY_MEETS | see W8 | Prescriptions stated more firmly than descriptive evidence allows; supporting and counter evidence not cited | none identified | yes |

These judgements are not totalled or mapped mechanically to the recommendation. What drives the decision is the set of repairable but substantive interpretive defects in W3–W7, together with the positioning problems in W1–W2.

### Detailed Comments

#### Literature Review
- **Coverage**: The concentration and stability literature (refs 1–5), routine activity theory (7, 8), generators and attractors (9, 10) and ambient population (32–34) are well chosen. Missing: the precursors of exposure-based facility rates (risky facilities, Bernasco & Block, risk terrain modeling); repeat and near-repeat victimization; concentration measurement with sparse data; time-of-day counter-evidence; lighting and Latin American place-based policing trials; police-data bias at small scales; and São Paulo crime geography.
- **Integration quality**: Literature is cited mostly to back individual sentences, not set against the findings. The decline and dawn-robbery results, for example, are never placed against the studies they confirm or contradict.
- **Research gap argument**: Not persuasive as written (W1). It becomes persuasive once restated around incomplete geocoding and the lack of a city-wide parcel inventory.

#### Theoretical Framework
- **Appropriateness**: Routine activity theory and crime pattern theory are the right frameworks. Crime pattern theory, the more apt one for journey-to-work robbery and for activity nodes such as stations, is never named.
- **Application depth**: Theory enters at two points: the motivating sentence and the guardianship conclusion. The generator/attractor test is run but not interpreted as one (W12). "Memory" has no theoretical anchor (W5).
- **Alternative frameworks**: Place management and risky facilities for the persistent residual. Criminal governance for the periphery and favelas. Darkness and visibility for the dawn peak.

#### Academic Argument Quality
- **Factual accuracy**: No outright factual errors about the cited works, apart from the misdescriptions in W10, W11, W13 and W14. The contrast with micro-place crime-drop findings (W4) is a factual omission, not an error.
- **Argument logic**: The step from "risk per pedestrian is high" to "absence of guardians rather than targets" is a non sequitur under routine activity theory (W3). The step from "Poisson-consistent tract-months" to "crime is noise" generalizes beyond the evidence (W6).
- **Terminology precision**: "Places" for tracts (W16). "Memory" for persistent heterogeneity (W5). "Responded" and "receded to its niches" for an unexplained decline (W4).

#### Contribution to the Field
- **Incremental contribution**: A large, wall-to-wall, multi-offence, time-resolved description of how urban composition relates to recorded crime in a Global South megacity. It includes a formal predictability ceiling for monthly forecasting and a confirmatory hold-out design that is rare in criminology. The dawn-robbery pattern and the equity audit are of direct policy interest.
- **Positioning**: Against omics rather than against environmental criminology (W2).
- **Overclaiming**: Prevention precision (W8), mechanism (W3), memory (W5), noise (W6) and the earlier use of biological vocabulary (W18).

#### Missing Key References
Verified this session (existence and main finding at abstract level):
- Bernasco, W., Ruiter, S. & Block, R. Do street robbery location choices vary over time of day or day of week? A test in Chicago. *J. Res. Crime Delinq.* **54**, 244–275 (2017). Direct counter-evidence for, and context to, the clock results.
- Tompson, L. & Bowers, K. A stab in the dark? A research note on temporal patterns of street robbery. *J. Res. Crime Delinq.* **50**, 616–631 (2013). The darkness alternative for the dawn peak.
- Braga, A. A., Hureau, D. M. & Papachristos, A. V. The relevance of micro places to citywide robbery trends. *J. Res. Crime Delinq.* **48**, 7–32 (2011). Crime-drop concentration, to set against the decline result.
- Bernasco, W. & Block, R. Robberies in Chicago: a block-level analysis of the influence of crime generators, crime attractors, and offender anchor points. *J. Res. Crime Delinq.* **48**, 33–57 (2011). The closest criminological precursor of the attribution.
- Eck, J. E., Clarke, R. V. & Guerette, R. T. Risky facilities: crime concentration in homogeneous sets of establishments and facilities. *Crime Prev. Stud.* **21**, 225–264 (2007). Concentration within facility type; implications for class-level targeting.
- Caplan, J. M., Kennedy, L. W. & Miller, J. Risk terrain modeling: brokering criminological theory and GIS methods for crime forecasting. *Justice Q.* **28**, 360–381 (2011).
- Nagin, D. S. & Paternoster, R. Population heterogeneity and state dependence: state of the evidence and directions for future research. *J. Quant. Criminol.* **16**, 117–144 (2000).
- Bernasco, W. & Steenbeek, W. More places than crimes: implications for evaluating the law of crime concentration at place. *J. Quant. Criminol.* **33**, 451–467 (2017).
- Haberman, C. P., Sorg, E. T. & Ratcliffe, J. H. Assessing the validity of the law of crime concentration across different temporal scales. *J. Quant. Criminol.* **33**, 547–567 (2017).
- Johnson, S. D. et al. Space–time patterns of risk: a cross national assessment of residential burglary victimization. *J. Quant. Criminol.* **23**, 201–219 (2007).
- Gorr, W. L. & Lee, Y. Early warning system for temporary crime hot spots. *J. Quant. Criminol.* **31**, 25–47 (2015).
- Steenbeek, W. & Weisburd, D. Where the action is in crime? An examination of variability of crime across different spatial units in The Hague, 2001–2009. *J. Quant. Criminol.* (2016) [volume and pages to verify].
- Akpinar, N.-J., De-Arteaga, M. & Chouldechova, A. The effect of differential victim crime reporting on predictive policing systems. *Proc. ACM FAccT* (2021).
- Buil-Gil, D., Moretti, A. & Langton, S. H. The accuracy of crime statistics: assessing the impact of police data bias on geographic crime analysis. *J. Exp. Criminol.* **18**, 515–541 (2022).
- Chalfin, A., Hansen, B., Lerner, J. & Parker, L. Reducing crime through environmental design: evidence from a randomized experiment of street lighting in New York City. *J. Quant. Criminol.* **38**, 127–157 (2022).
- Blattman, C., Green, D. P., Ortega, D. & Tobón, S. Place-based interventions at scale: the direct and spillover effects of policing and city services on crime. *J. Eur. Econ. Assoc.* [year and pages to verify].
- Ceccato, V., Haining, R. & Kahn, T. The geography of homicide in São Paulo, Brazil. *Environ. Plan. A* **39**, 1632–1653 (2007).
- Biderman, C., De Mello, J. M. P., De Lima, R. S. & Schneider, A. Pax monopolista and crime: the case of the emergence of the Primeiro Comando da Capital in São Paulo. *J. Quant. Criminol.* **35**, 573–605 (2019).

Search leads, not checked in this session [UNVERIFIED]:
- Foundational micro-place work: Sherman, Gartin & Buerger on hot spots of predatory crime (Criminology, 1989); Eck & Weisburd on crime places in crime theory (Crime Prevention Studies, 1995).
- Crime pattern theory: Brantingham & Brantingham, "Environment, routine and situation" (1993).
- Hot products and phone theft: Clarke's Home Office report on hot products (1999); the security hypothesis for the crime drop (Farrell, Tseloni, Mailley & Tilley, 2011).
- Ambient population as denominator: Malleson & Andresen on London hot spots (J. Crim. Justice, 2016).
- Prospective hot-spotting and hit-rate/PAI metrics: Bowers, Johnson & Pease (2004); Chainey, Tompson & Uhlig (2008).
- Lighting meta-analysis: Welsh & Farrington, Campbell review (2008). Time-targeted patrol: Koper (1995).
- Brazilian victimization surveys on reporting propensity for theft and robbery.
- Ethnography of criminal governance in São Paulo's periphery (for example, work by Gabriel Feltran).

### Questions for Authors
1. What share of phone crime is theft and what share robbery in each cell class, especially stations, medium-standard retail and local streets? Does the 2022–2025 decline by class survive when theft and robbery are decomposed separately?
2. Does "lethal violence" include deaths from police intervention, and robbery-homicide? In São Paulo, police killings are concentrated in the periphery and would change the reading of the favela and low-income signatures.
3. How are coordinates produced in the SSP microdata (address geocoding, or defaults to street or police-station centroids)? How do the geocoded share and duplicate coordinates vary by income quintile and by year?
4. Did the share of online reports, or phone-loss reporting behaviour, change after the federal blocking programme launched in December 2023?
5. Does the 04:00–06:00 share of weekday robbery on low-income housing vary with sunrise time across months?
6. Does the 2017 Origin–Destination survey apply a minimum distance for recording walking trips? I believe it may [UNVERIFIED]. If so, how does that affect the pedestrian denominator at dawn?
7. In the cargo-robbery signature, does the recorded location mark the interception or where the cargo was recovered?

### Minor Issues

#### Citation Format
- Ref 46 (Hipp & de Leon 2026): the DOI resolves to an Elsevier record, but I could not check its content. The claim that hourly guardianship potential "has only recently been examined directly" should allow for earlier hourly work the authors already cite (refs 33, 34).
- Ref 27 is a recent secondary source for "urban tissue" in morphology. The concept predates it (Italian typo-morphological school; Conzen). Consider citing an original source [UNVERIFIED specific works].
- Ref 32 uses a 24-hour average ambient population (LandScan), not an hourly one. Cite it for the denominator problem, not for hourly estimates.
- Ref 11 (Robinson) is about individual-level inference. The paper's case is a cross-level inference from tracts to parcel classes; Goodman's ecological regression (1953) [UNVERIFIED metadata] is the closer reference.
- Ref 29 (Urban genome, npj Urban Sustain. 2025) exists, verified this session.

#### Language and Terminology
- "Capable guardians": pedestrians are at most potential guardians. Guardianship in routine activity theory also requires the capacity and willingness to intervene (ref 8). Say "guardianship potential" when referring to pedestrian counts.
- "Crime receded to its niches" and "places that remember" are biological metaphors that criminology readers will take literally. Consider "chronic hot spots" and "persistent place effects".
- "Phone crime" combines theft and robbery, offences with different mechanisms and reporting rates. State which is meant wherever an interpretation depends on the difference.

#### Figures and Tables
- Fig. 5e: show the decline per class for theft and robbery separately (see W4).
- Fig. 4c: show the denominator (pedestrians per hour) beside the per-pedestrian risk, so readers can see how small the night-time base is.
