# Peer Review Report: Peer Reviewer 3 (Perspective)

**Manuscript**: "Crime as a phenotype of urban tissue". Nature Cities (Article), development draft
**Review date**: 2026-10-19 | **Review round**: 1
**Reviewer role**: Peer Reviewer 3 (Perspective). Dimension owned: D4 cross_disciplinary_relevance
**Reviewer identity**: computational biologist in spatial omics (deconvolution, signature matrices, cNMF programs, neighbourhood and niche analysis, circadian transcriptomics, single-cell noise), interested in urban systems and in how predictive models are used in society. I am not a criminologist, and I flag where my reading of criminology or Brazilian policing is that of an outsider.
**Review focus**: whether each biological mapping is faithful to the method it borrows; whether the analogy works as an instrument with tests or slides into decoration; whether the omics vocabulary is explained for urban readers and kept lean; whether the cross-disciplinary gain is real and honestly stated; and the practical, policy and ethical consequences of typing and predicting crime by place in a city with favelas.
**Calibration status**: `NOT_CALIBRATED`
**Placeholders**: `[CONFIRMATION: ...]`, `[ETHICS: ...]` and similar markers are deliberate author decisions and are not penalized.

contract_role: perspective

## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: warn
trigger: "analogies are broadly faithful but at least one is overstated, loose or decorative without a test; omics vocabulary is used without definitions an urban reader can follow, or more terms are imported than the analysis needs; the cross-disciplinary gain is asserted more strongly than shown, or adjacent urban-science and criminology precedents are not credited; or ethical and policy implications are acknowledged only generically rather than tied to the specific outputs"

### D5: writing_and_structure
score: not_assessed

### D6: venue_fit_and_contribution
score: not_assessed

## Review Body

### Overall Assessment

**Recommendation (perspective seat)**: Major Revision
**Confidence score**: 4. The omics side is my core expertise. Criminology, ecological inference and Brazilian policing are adjacent fields for me.

**Summary assessment.** The paper reads São Paulo as a spatial-transcriptomics sample. Parcels are cells, tracts are spots and police records are a 15-phenotype panel. It uses known-composition attribution, neighbourhood enrichment, NMF, class-specific daily profiles, a variance decomposition and a Poisson noise ceiling to ask which crime each class of place hosts, when it happens, and how much remains to be predicted. Few papers that borrow from biology use the borrowing this honestly. Every omics module is scored against an urban analogue, and the paper reports where the analogy loses. Each inference is checked against independent data. The forecasting results are bounded and audited for equity. The pre-dawn finding is turned into a guardianship test that does not rely on police. Those are real strengths. Several mappings are less faithful than the text implies, though, and in each case the faithful version would change what the paper claims. The attribution model is Goodman's ecological regression in Poisson form, so the headline "gain over urban methods" is scored against the wrong comparison. "Intrinsic noise" should be sampling noise at low count depth, and that weakens the reading of month-to-month change as noise. "Memory" asserts a mechanism that the variance decomposition cannot identify. "Clock" and "signature matrix" are looser than the cited methods. On ethics, the forecasting section is careful, but the class signatures name favelas and low-income housing as sources of lethal violence, using "produces" language and policing recommendations. There is no treatment of territorial stigma, of reporting that varies by income, or of what the lethal-violence category contains. All of this can be repaired. I recommend major revision for D4 (warn).

### Judgement Against the Phase 1 Scoring Plan (D4)

- **What I committed to look for, and what I found.** (i) *Fidelity.* The core mappings hold: spots as mixtures, attribution as the inverse of deconvolution, neighbourhood enrichment with a restricted null. The noise, clock, memory and signature-matrix mappings are loose or overstated (W2, W4, W6, W7). (ii) *Instrument versus decoration.* The analogy is used as an instrument (S1). The exception is the attribution module, whose urban comparator is mis-specified (W1), and the programs, which are close to decorative (W10). (iii) *Vocabulary.* It is mostly lean, and spots are defined for urban readers (S2). A few imported terms are unneeded or used in two senses (W8, W9). (iv) *Gain.* It is real for class-resolved rates checked against geocoded points and for class-specific daily profiles. It is overstated against ecological regression (W1). (v) *Ethics and policy.* These are tied to the outputs for forecasting (S5) but stay generic for the signatures, the favela results and reporting bias (W3, W5, W12).
- **Block not met.** The first block clause needs misdescribed load-bearing analogies *and* no demonstrated gain. Extended Data Fig. 2 shows tested gains, and the central inversion of deconvolution is described in the right direction. The second clause needs *no* treatment of feedback loops, recorded-crime bias or stigmatization. The paper does address feedback loops, undercounting and an income-quintile audit.
- **Warn met.** All four warn clauses apply, so D4 = warn. No dissent from the Phase 1 plan.

### Strengths

### S1: The analogy is run as a falsifiable instrument, with losses reported
Extended Data Fig. 2 pairs each omics module with an urban analogue and gives a verdict. Ligand–receptor communication and interaction terms lose to simpler spatial models. Niches and MISTy views tie. Parcel typing is shown to describe the tissue but to predict no better than the raw attributes. Very few papers that borrow biological vocabulary for cities do this, and it answers the usual "decorative metaphor" objection, which the Introduction itself raises against earlier urban-genome and urban-DNA work.
**Evidence Anchor**: text: Discussion ¶4 "The analogy is thus useful as an instrument that can fail its tests, not as a description of what cities are."

### S2: A well-chosen bridge problem
The paper identifies the shared problem correctly. A Visium spot mixes cells in the same way a census tract mixes land uses, and the ecological fallacy is the urban name for the mixture problem. This gives urban readers a reason for the transfer before any vocabulary arrives, and "spot" is defined in plain language at first use.
**Evidence Anchor**: text: Introduction ¶2 "Spatial transcriptomics faced the same problem."

### S3: The omics habit of orthogonal validation is transferred, not only the estimators
Spatial omics validates deconvolution against an independent modality such as imaging or smFISH. The paper does the same thing. It checks areal attribution against geocoded points, the clock against a second year, and the crowd explanation against an independent ambient-population estimate. This is arguably the most portable part of the transfer for urban science.
**Evidence Anchor**: text: Discussion ¶1 "geocoded points for the attribution, a second year for the clock and pedestrian counts for the crowd"

### S4: Normalizing by the crowd, and a practical recommendation that does not rely on police
Dividing class rates by ambient pedestrians is the urban equivalent of library-size normalization, and the clock result survives it. The pre-dawn robbery of commuters on low-income housing becomes a testable guardianship measure: lighting and staffed bus stops on routes to transit. This is the kind of implication planners and transit operators can act on, and it serves residents of the periphery rather than targeting them.
**Evidence Anchor**: text: Discussion ¶2 "such as lighting and staffed bus stops, rather than extending evening patrols"

### S5: Forecasting is bounded and audited for equity
The paper cites the feedback loop of police-recorded data. It checks calibration across income quintiles, reports that flagging by density concentrates on richer tracts, and keeps per-tract risk out of the public explorer and the data deposit. The message that most of the value of predictive policing lies in a stable map rather than in monthly updates is useful for policy.
**Evidence Anchor**: text: Results §Month-to-month ¶2 "Forecasts were calibrated within 5% across tract income quintiles, but the flagged area concentrated in richer tracts"

### Weaknesses

### W1: Attribution is ecological inference, so the claimed gain over urban methods is scored against the wrong comparator
**Problem**: The attribution model y_s ~ Poisson(Σ_k E_sk λ_k) assumes one rate per class shared across all tracts. On the urban side this is Goodman's ecological regression in Poisson form with exposures, and it carries Goodman's constancy assumption. On the omics side the closest relatives are the known-fraction methods (csSAM; CIBERSORTx group mode; TCA), which estimate cell-type-specific profiles from bulk samples whose fractions are known. "Inverts spot deconvolution" points in the right direction, but these methods are the exact analogue. Yet the Discussion lists attribution within the spot first among what the analogy adds that urban methods lack, and Extended Data Fig. 2 scores attribution as an omics win over "Ecological regression by tract". Because the two belong to the same model family, that verdict does not test the transfer. There is also a difference from Visium. In this city most events have sub-spot coordinates (100,347 of 121,434 phone-crime events in 2025), so direct parcel- or segment-level rates are the natural urban comparator. They are in effect the authors' own point validation and the parcel-level studies of ref. 12. Finally, the signatures, the clock and the decline decomposition are this same instrument applied along the phenotype, hour and year axes, and the decline decomposition is already credited to Kitagawa. The "four additions" are one instrument used three ways.
**Evidence Anchor**: text: Results §Each cell class has a crime signature ¶1 "the composition is known, and the rates are inferred"; Discussion ¶4 "It adds attribution within the spot"
**Why it matters**: Urban scientists and political methodologists will recognise Goodman and King at once, and the novelty claim will read as relabelling. That would undermine the honest audit the paper otherwise does well. The constancy assumption is exactly what makes ecological inference fragile, and the Introduction itself warns against the ecological fallacy. Stating the assumption openly strengthens the paper.
**Suggestion**: (a) Say in Results that attribution is a Poisson ecological regression with known exposures. Credit Goodman and King on the urban side and csSAM/CIBERSORTx group mode on the omics side. (b) In Extended Data Fig. 2, replace the attribution comparator with two comparators: a Goodman regression on composition shares, and direct parcel-level rates from geocoded events. Then state what tract-level attribution actually adds. Likely candidates are the use of events whose coordinates are suppressed non-randomly at homes and stations, joint multi-phenotype estimation under non-negativity, and the validation culture of S3. (c) Borrow the omics remedies for the constancy assumption, for example district-level random effects on λ_k, analogous to RCTD's platform effect or cell2location's location-level scaling, and report how far the rates move. (d) Recast the Discussion's claim as one instrument (composition-aware attribution, validated by points) applied to what, when and how it changes, plus one bound (the noise ceiling). This also serves the author's aim of a single, lean story.
**Severity**: Major
**Confidence**: 4 — core expertise in deconvolution and known-fraction methods; adjacent expertise in ecological inference

### W2: The noise analogy points to the wrong omics concept, and the faithful one qualifies the headline
**Problem**: Elowitz et al. define intrinsic noise operationally, with dual reporters: it is the part of two identical reporters in one cell that does not covary. It is a biological property of expression and is usually super-Poissonian because of bursting. A Fano factor of one is instead the signature of sampling (shot) noise, which in single-cell RNA-seq is the measurement floor at low capture depth. The paper's own ceiling, 1 − mean/variance, is the omics "variance above Poisson" used to select variable genes (Brennecke et al.; Grün et al.). Single-cell transcriptomics teaches a cautionary lesson about this ceiling: at low counts most genes look Poisson, and consistency with Poisson says little about whether the underlying rate varies (Sarkar & Stephens; Svensson). As an illustration, a ±30% seasonal swing around two events per month raises the expected dispersion index only to about 1.09, which a χ² test on 11 degrees of freedom will rarely detect. The formal power question belongs to the methodology seat. Separately, "the city sits close to its limit of predictability" cites Song et al.'s entropy bound on individual mobility, a different quantity. Within tracts the ensemble reached R² = 0.018 of an attainable 0.56, so the limit within tracts is far from reached.
**Evidence Anchor**: text: Results §Month-to-month ¶1 "monthly counts behave like the intrinsic noise that bounds what can be predicted about single cells"
**Why it matters**: The noise claim answers one of the paper's three questions, closes the abstract and carries a strong policy message (monthly updates add little). Urban readers will take "intrinsic noise" to mean "nothing there", and the faithful analogue does not support that reading.
**Suggestion**: (a) Replace the Elowitz and Song analogies with the sampling-noise analogue and state what it implies. (b) Pool tracts within a class or domain in a hierarchical negative-binomial model with shrunken dispersion, in the style of DESeq2, to estimate rate variance below the per-tract detection limit. Alternatively, report the smallest monthly rate variation detectable at each count depth. (c) Change "is noise" in headings and in the Discussion to "is indistinguishable from Poisson noise at the observed counts". Keep the strong, well-supported result: extra-Poisson variance is concentrated in hubs, where forecasts remain far below the ceiling and where forecasting research should go.
**Severity**: Major
**Confidence**: 4 — core expertise in single-cell noise models; the dispersion-test arithmetic is illustrative

### W3: The phenotype framing and the favela signatures risk territorial stigmatization, and ethics is reduced to privacy
**Problem**: The paper says what each class "produces". It reports lethal violence enriched on low-income houses, vacant land and favelas, and cargo robbery on industrial parcels and favelas. It then offers the signature matrix for targeting hot-spot components in place-based policing. The Limitations say attribution is associational. Even so, the production language and the phenotype title present crime as an intrinsic trait of place types, including favelas, which already face territorial stigma and lethal police operations in Brazil. The favela rates also rest on a constructed exposure (informal households × 7.0 m median frontage), so a modelling assumption sits under the most stigmatizing result. The "Privacy and ethics" section covers data handling only.
**Evidence Anchor**: text: Results §Each cell class has a crime signature ¶2 "lethal violence on low-income houses, vacant land and favelas"; Discussion ¶2 "the signature matrix specifies which component of a hot spot to target"
**Why it matters**: In a Nature Cities paper, a sentence saying favela tissue produces lethal violence will travel beyond its caveats, to the press and to justifications for police operations. The analogy itself shows where it breaks. In biology a phenotype is a trait of the cell, made by the cell. Here crime is an event among mobile people (offenders, victims, guardians, police) that is *recorded at* a place. Parcels host crime; they do not produce it.
**Suggestion**: (a) State this break in the analogy next to Fig. 1a, and replace "produces" with "is attributed to" or "hosts" in Results and Methods. (b) Add a paragraph on territorial stigma and on how class signatures for favelas and low-income housing should and should not be used, and flag the constructed favela exposure. (c) Report how sensitive favela enrichment is to the 7.0 m assumption, for example across a plausible range of frontage values or with household-based exposure. (d) Extend the Ethics section beyond privacy. State the intended uses and the excluded uses of the signatures and the public explorer (for example, no use of class-level signatures to justify area-wide policing), and say whether any community or stakeholder consultation took place.
**Severity**: Major
**Confidence**: 3 — adjacent expertise (societal use of predictive models); outsider to Brazilian policing

### W4: "Memory" asserts a mechanism the decomposition cannot identify, and the omics reading points to missing composition
**Problem**: The stable residual accounts for 48% of between-tract variance, more than the tissue's 42%. Calling it "memory" implies that a place's past crime shapes its future crime (state dependence). Covariance of residuals across years cannot separate state dependence from persistent unobserved heterogeneity. In deconvolution, a stable residual after fitting reference types usually means a cell type is missing from the reference or a signature is mis-specified. The manuscript names two such gaps: the cadastre misses informal uses outside favelas, and the registry links only 73.8% of establishments. Candidate "missing cell types" include street vending, informal commerce, unlicensed bars, drug-selling points and areas under criminal governance. Extended Data Fig. 2 itself labels this module "Cell state beyond type", which is the faithful version of the analogy.
**Evidence Anchor**: text: Abstract "Beyond composition, places carry a stable memory of crime."; Limitations "The cadastre misses informal uses outside favelas."
**Why it matters**: The Discussion recommends "understanding why some places remember crime", which points policy towards a mechanism the data do not identify. If the residual is partly missing composition, the finding becomes "beyond *recorded* composition", which leads to a different agenda: better land-use data rather than studying crime history.
**Suggestion**: Rename the component "persistent place effect" or "state beyond type". Test whether the residual concentrates where composition is known to be incomplete: tracts with many unlinked establishments, tracts near favelas, or proxies for informal commerce. Acknowledge the distinction between state dependence and heterogeneity (Heckman). If "memory" in the dynamic sense is wanted, it needs a dynamic panel design with tract effects, which is outside the current analysis.
**Severity**: Major
**Confidence**: 3 — core expertise on deconvolution residuals; adjacent expertise on panel econometrics and São Paulo criminal governance

### W5: Differential reporting is acknowledged only in general terms, but it bears directly on the class signatures and on the equity comparison
**Problem**: Uneven undercounting is noted in one sentence. Phone crime makes up 39% of records and drives the attribution, clock, decline and forecasting analyses, and its reporting plausibly varies with income, through insurance and device-blocking incentives and through access to online reporting. Residential burglary has similar insurance incentives. Point validation cannot detect this bias because it uses the same police records. The bias matters for the near-zero rate on low-rise residential parcels, for the pre-dawn robbery on low-income housing (true rates there may be higher still) and for the equity reading of Fig. 6f. The bottom income quintile received 3% of the flagged area against 7% of *recorded* phone crime. If its true share is higher, density-based flagging under-protects poorer tracts by more than the figure shows. The Discussion frames that result mainly as attention concentrating in richer tracts, not as under-protection of poorer ones.
**Evidence Anchor**: text: Limitations "Police records undercount crime unevenly across places and types of crime."
**Why it matters**: The signatures and the equity statement both bear on how resources are split between richer and poorer areas. The people most affected, peripheral commuters robbed before dawn, are probably the least likely to report.
**Suggestion**: Add a sensitivity analysis. Either calibrate district or class rates against external victimization data, or bound the problem by asking how steep an income gradient in reporting would have to be to reverse the class ranking or the Fig. 6f gap. In omics terms this is location-specific detection sensitivity, as in cell2location's per-location scaling. It can only be identified at a coarse scale and with outside calibration, so say so. State which conclusions are robust to plausible reporting gradients, and state both directions of the equity risk: under-protection of poorer tracts for phone crime, and over-policing for violence.
**Severity**: Major
**Confidence**: 3 — adjacent expertise; general knowledge of reporting bias, not of São Paulo reporting channels specifically

### W6: "Clock" implies an endogenous oscillator, but the measured object is an exogenously driven daily profile
**Problem**: In chronobiology a clock is an endogenous, entrainable oscillator. Tissue-specific phases, as in Zhang et al., are estimated with rhythm-detection methods that recover phase and amplitude. Here the confirmatory test uses four 6-hour periods and a χ² contrast, so it estimates no phase or amplitude, and the rhythm is driven from outside by commuting and guardianship. The crowd test is in effect a *masking* test: does the rhythm follow its direct external driver? Showing that it does not follow pedestrians points to a different external driver, as the authors' own guardianship reading says. It does not show an internal clock.
**Evidence Anchor**: text: Results heading "The tissue keeps a clock that is not the clock of crowds"
**Why it matters**: Chronobiologists reading Nature-family journals will object to the term. Urban readers may infer a self-sustaining rhythm that persists when conditions change, which the data do not test.
**Suggestion**: Use "daily rhythm" or "diurnal profile", or define "clock" once as a class-specific daily profile, not an oscillator. Optionally, fit harmonic (cosinor) models to the hourly data for each class, report phase and amplitude, and test differential rhythmicity between classes. Borrow "masking" (Mrosovsky) to frame the crowd test.
**Severity**: Minor
**Confidence**: 4 — core expertise in circadian transcriptomics analysis

### W7: The class × phenotype matrix is called a "signature matrix", but it is an output and is never used as one
**Problem**: In CIBERSORT and CIBERSORTx (ref. 20), a signature matrix is the input reference, marker genes × cell types, curated for a low condition number and used to deconvolve mixtures. Here the matrix is the output of attribution and is never used to deconvolve anything. "Behaves as a signature matrix" rests only on the fact that the top class differs across phenotypes, which is marker-like specificity.
**Evidence Anchor**: text: Results §Each cell class has a crime signature ¶2 "The matrix of classes by phenotypes behaves as a signature matrix"
**Why it matters**: As written, the term is decoration, the one place where the paper's own instrument standard (S1) slips.
**Suggestion**: Either call it "class-specific crime profiles (the analogue of reference signatures)", or turn it into an instrument. Report its condition number and test whether it recovers known tract composition from the crime mix in held-out tracts. If the second route is taken, state that the matrix should not be used to infer land use or residents from crime.
**Severity**: Minor
**Confidence**: 5 — core expertise in signature-matrix construction

### W8: The Introduction blurs which side is known in deconvolution
**Problem**: The sentence describing the omics toolkit says tools infer contributions to spots "of known or estimated composition". RCTD and cell2location estimate composition from known reference profiles. Estimation from known composition is the csSAM/CIBERSORTx group-mode problem.
**Evidence Anchor**: text: Introduction ¶2 "tools that infer what each cell type contributes to spots of known or estimated composition"
**Why it matters**: Urban readers need the direction to be clear to follow the "inverse" claim in Results.
**Suggestion**: Use one plain sentence: deconvolution estimates each spot's composition from reference profiles of cell types; when composition is known, the same model run the other way estimates the profiles.
**Severity**: Minor
**Confidence**: 5 — core expertise

### W9: The key schematic advertises a mapping that failed, and "niche" is used in two senses
**Problem**: Fig. 1a lists ligand–receptor signalling as crime generator to target, yet the Discussion reports that it loses to simpler spatial models and it does not appear in Results. In Fig. 1a, "niche" means neighbourhood composition. In Results, "Crime receded to its niches" uses it for hubs. "Interstitium" appears only in the Introduction and the schematic.
**Evidence Anchor**: figure: Fig. 1a — middle column, row "Ligand–receptor signal → Crime generator → target"
**Why it matters**: The schematic is where urban readers learn the vocabulary. Including a mapping that failed, and a term used in two senses, adds load without payoff, against the author's aim of nothing superfluous.
**Suggestion**: Keep in Fig. 1a only the mappings used in Results (cell, spot, phenotype; optionally interstitium). Move ligand–receptor to Extended Data Fig. 2 as tested and failed. Use "niche" in one sense or drop it.
**Severity**: Minor
**Confidence**: 4 — core expertise in spatial-omics vocabulary

### W10: The crime programs repeat the signatures and do not use what cNMF adds
**Problem**: Tract-level NMF of 15 phenotypes mixes composition, so the four programs (transport, dense centre, peripheral logistics, residential) are largely what tissue composition multiplied by the signatures already predicts. What cNMF adds is the separation of identity programs from activity programs, and that is not used here.
**Evidence Anchor**: text: Results §Each cell class has a crime signature ¶2 "yielded four programs that were stable across seeds"
**Why it matters**: The programs add a fourth imported concept without a test or a new result.
**Suggestion**: Either cut them, or factorize the residual matrix after removing the counts expected from composition. That would be the activity-program analogue, and it would connect directly to the persistent residual in W4.
**Severity**: Minor
**Confidence**: 4 — core expertise in cNMF

### W11: Policy translation is addressed mainly to the police, although planners and transit operators are the natural users
**Problem**: The implications paragraph opens with place-based policing. Yet the most actionable findings concern transit, namely pre-dawn commuter robbery and the hubs, along with street lighting, retail frontage, and licensing (the null event study).
**Evidence Anchor**: text: Discussion ¶2 "Place-based policing reduces crime"
**Why it matters**: The readership of Nature Cities is mostly planners, and non-police measures carry fewer of the equity risks raised in W3 and W5.
**Suggestion**: Rebuild the implications paragraph around measures outside policing and name the agencies concerned (transit operator, municipal lighting, planning and licensing). Keep policing as one lever among several.
**Severity**: Minor
**Confidence**: 3 — adjacent expertise in urban policy

### W12: The contents of the lethal-violence phenotype are not stated
**Problem**: The paper never says whether lethal violence includes deaths resulting from police intervention. Offences initiated by police are excluded from the panel, which suggests the authors are aware of the problem, but this category is not addressed.
**Evidence Anchor**: absence: Methods §Phenotype panel and signatures — expected the components of "lethal violence", including whether deaths from police intervention are counted; checked Abstract, Results, Methods §Data and §Phenotype panel and signatures, Fig. 3 legend, Extended Data Fig. 10 legend
**Why it matters**: If police killings are included, the enrichment of lethal violence on favelas would partly measure police action. That would worsen the stigmatization risk in W3. See Question 2.
**Suggestion**: List the components. If deaths from police intervention are included, model them as a separate phenotype.
**Severity**: Minor
**Confidence**: 3 — the definition depends on the SSP database, which the manuscript does not describe

### Detailed Comments

#### Assumption Audit
- **Explicit assumptions**: Class rates are constant across the city (the attribution model). Exposure is proportional to frontage, street length or station count. Parcel types fixed without crime data are a neutral description. The first is the ecological-inference constancy assumption (W1). The second is reasonable for street crime but constructed for favelas (W3).
- **Implicit assumptions**: (i) Recorded crime measures crime with a reporting rate that may vary with crime type but not with class of place (W5). (ii) A residual that is stable across years reflects something the place carries, not something the data miss (W4). (iii) Consistency with Poisson means absence of signal (W2). (iv) Places are the producers of crime (W3).
- **Paradigmatic assumptions**: The tissue frame adopts the criminology-of-place paradigm wholesale. Perspectives centred on people (offender networks, victims' commuting, criminal governance, police activity) enter only as residuals or denominators. This is a legitimate choice, but it should be named. In São Paulo, criminal governance and policing practices are prominent explanations for the geography of lethal violence, and they bear on both the "memory" and the favela signatures.

#### Cross-Disciplinary Connections
- **Parallel research**: Known-fraction profile estimation (csSAM, CIBERSORTx group mode, TCA) is the exact omics analogue of the attribution. Risk terrain modelling is the criminological precedent for attributing risk to environmental features and should be credited next to refs 9–12.
- **Borrowing opportunities**: location-level detection sensitivity (cell2location) for differential reporting (W5); missing-reference-type diagnostics for the residual (W4); masking and differential-rhythmicity tests from chronobiology (W6); identity versus activity programs from cNMF (W10); hierarchical dispersion shrinkage from bulk RNA-seq for the noise ceiling (W2).
- **A simplification the transfer suggests**: The whole paper can be told as one instrument (composition-aware attribution, validated by points) applied along three axes (what, when, how it changes), plus one bound (Poisson ceiling). Other imported terms can go to Extended Data Fig. 2.

#### Practical Impact
- **Real-world application**: The class-by-hour rates give a usable map for prevention planning. The guardianship recommendation and the finding that monthly forecasting adds little are both useful to policy.
- **Implementation feasibility**: The approach needs a parcel cadastre with frontage, a business registry and geocoded records. Many Global South cities lack a cadastre that covers informal settlements. The favela pseudo-cell device is a transferable idea worth highlighting, with its exposure assumption made explicit.
- **Stakeholders**: These include residents of favelas and of low-income periphery housing (the subjects of the most sensitive signatures), pre-dawn commuters (the victims of the most striking clock result), the transit operator, municipal planners, and the police. Only the police are named as users.

#### Broader Implications
- **Ethical dimensions**: Territorial stigma, the composition of the lethal-violence category, the constructed favela exposure, and income-dependent reporting (W3, W5, W12). Privacy handling is good.
- **Social impact**: Class-level signatures are statements about every parcel of a class, so suppressing per-tract risk in the explorer does not prevent class-level stigma.
- **Future directions**: Calibration against victimization surveys; residual diagnostics for missing land uses; tests of guardianship measures at transit stops before dawn; replication in a second city with a different informal-housing regime.

### Cross-Disciplinary Reading Recommendations
Verified in this session (PubMed citation match):
- Shen-Orr, S. S. et al. *Nat. Methods* 7, 287 (2010). csSAM, the known-fraction analogue of the attribution model (W1, W8).
- Newman, A. M. et al. *Nat. Methods* 12, 453 (2015). CIBERSORT; defines the signature matrix as a reference with a controlled condition number (W7).
- Rahmani, E. et al. *Nat. Commun.* 10, 3417 (2019). TCA, cell-type-specific signals given known fractions (W1).
- Avila Cobos, F. et al. *Nat. Commun.* 11, 5650 (2020). Deconvolution benchmarking, including the effect of missing cell types (W4).
- Brennecke, P. et al. *Nat. Methods* 10, 1093 (2013) and Grün, D. et al. *Nat. Methods* 11, 637 (2014). Variance above Poisson (technical) noise, the faithful analogue of the ceiling (W2).
- Sarkar, A. & Stephens, M. *Nat. Genet.* 53, 770 (2021) and Svensson, V. *Nat. Biotechnol.* 38, 147 (2020). Separating measurement noise from expression variability at low counts (W2).
- Swain, P. S. et al. *PNAS* 99, 12795 (2002). The operational definition of intrinsic versus extrinsic noise (W2).
- Hughes, M. E. et al. *J. Biol. Rhythms* 32, 380 (2017). Guidelines and terminology for rhythm analysis (W6).
- Mrosovsky, N. *Chronobiol. Int.* 16, 415 (1999). Masking (W6).

Search leads, not verified in this session:
- [UNVERIFIED] Goodman, L. A., ecological regressions, *Am. Sociol. Rev.* (1953); King, G., *A Solution to the Ecological Inference Problem* (Princeton UP, 1997). For W1.
- [UNVERIFIED] Heckman, J. J., heterogeneity and state dependence (1981, book chapter). For W4.
- [UNVERIFIED] Caplan, J. M., Kennedy, L. W. & Miller, J., risk terrain modelling, *Justice Q.* (2011). Criminological precedent for W1.
- [UNVERIFIED] Caldeira, T. P. R., *City of Walls* (UC Press, 2000); Feltran, G., *The Entangled City* (Manchester UP, 2020); Willis, G. D., *The Killing Consensus* (UC Press, 2015); Biderman, C. et al., "Pax Monopolista", *J. Quant. Criminol.* (2019). Crime, segregation, criminal governance and policing in São Paulo (W3, W4, W12).
- [UNVERIFIED] Wacquant, L., territorial stigmatization, *Thesis Eleven* (2007); Sampson, R. J. & Raudenbush, S. W., "Seeing disorder", *Soc. Psychol. Q.* (2004). For W3.
- [UNVERIFIED] Ensign, D. et al., runaway feedback loops in predictive policing (FAT* 2018); Akpinar, N.-J. et al., differential victim reporting and predictive policing (FAccT 2021); Richardson, R. et al., "Dirty data, bad predictions" (*NYU Law Rev. Online*, 2019). For W5 and S5.
- [UNVERIFIED] Victimization surveys for São Paulo and Brazil (for example the IBGE national household survey victimization supplement), as a source of calibration for W5.

### Questions for Authors
1. Apart from the EM fitting, is the attribution model distinguishable from a Poisson Goodman regression with exposure offsets? How does it compare with direct parcel-level rates computed from geocoded events?
2. Does the lethal-violence phenotype include deaths resulting from police intervention? If so, what share of the enrichment on favelas do they account for?
3. At the count depth of a typical tract, what monthly rate variation could the per-tract dispersion test detect, and does a hierarchical model pooling tracts within a class find rate variance below that limit?
4. Does the persistent residual ("memory") concentrate where the cadastre and registry are known to be incomplete?
5. Who should use the signature matrix and the class clocks, and which uses do the authors explicitly rule out?

### Minor Issues
- Fig. 1 legend: "Favela (census FCU)". Spell out FCU for international readers.
- "Pseudo-cells": in omics this usually means aggregates of similar cells (metacells). Define it once as a favela area entered as a single unit with constructed exposure.
- Extended Data Fig. 2: the "Omics method" for attribution reads "Known-composition spots", which is a setting rather than a method; the Forecast row is truncated ("Laya…") and "Laya-FT" is undefined. The library-size row is an apt analogy that the main text could name once in the crowd paragraph, or leave out to keep the text lean.
- Extended Data Fig. 2 calls the decline module "differential expression" while the main text credits Kitagawa. Use one name.
- Discussion ¶3: "flagging by density concentrated attention in richer tracts". Add the direction of harm for phone crime (under-protection of the bottom quintile relative to its recorded share).

### Criterion-Bound Judgements

| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| D4a Fidelity of imported concepts | Contract D4; Phase 1 what_to_look_for (fidelity) | PARTLY_MEETS | see W2, W4, W6, W7, W8 | Core mappings (spot mixtures, inverse deconvolution, neighbourhood enrichment) are faithful; noise, memory, clock and signature matrix are loose | Criminology-side fidelity judged as an outsider | yes; W2 and W4 change headline claims |
| D4b Analogy as instrument | Contract D4; Phase 1 (instrument vs decoration) | MEETS | see S1, W1, W10 | Equivalence audit with reported losses is exemplary; attribution comparator mis-specified; programs close to decorative | Extended Data Fig. 2 seen as an image only | yes, through W1 |
| D4c Vocabulary accessible and lean | Contract D4; Phase 1 (definitions, economy) | MEETS | see S2, W9 | Spots defined; most terms explained; a few unneeded or double-sense terms | none identified | no |
| D4d Gain substantiated, precedents credited | Contract D4; Phase 1 (honest gain) | PARTLY_MEETS | see W1, W4 | Gain real for class-resolved, point-validated rates and daily profiles; overstated against ecological regression; Goodman, King and risk terrain modelling not credited | Adjacent-field judgement on ecological inference | yes |
| D4e Practical, policy and ethical implications | Contract D4; Phase 1 (predictive policing, equity, stigma) | PARTLY_MEETS | see S4, S5, W3, W5, W11, W12 | Forecasting ethics tied to outputs; signature and favela ethics generic; reporting bias generic | Outsider to Brazilian policing data | yes |

These judgements are not totalled, weighted or mapped mechanically to the recommendation. The recommendation of major revision rests on W1 to W5, all of which can be repaired.
