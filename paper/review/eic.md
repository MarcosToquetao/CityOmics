# Peer Review Report: Journal-Fit Reviewer

**Title**: Crime as a phenotype of urban tissue
**Manuscript ID**: n/a (development draft, 77 exploration districts)
**Review date**: 2026-10-19
**Review round**: Round 1
**Reviewer role**: Journal-Fit Reviewer (`eic`)
**Reviewer identity**: Handling editor at *Nature Cities* with a background in computational urban science
**Review focus**: Whether the paper interests a broad Nature Cities readership, whether it tells one clear and economical story, whether its contribution is original, and whether it meets the Article format and stays consistent from abstract to legends (contract D5, D6).
**Calibration status**: `NOT_CALIBRATED`
**Overall confidence**: 4 (core competence in urban data science and journal editing; I do not judge criminological or statistical detail).

contract_role: eic
## Dimension Scores

### D1: methodology_rigor
score: not_assessed

### D2: domain_accuracy
score: not_assessed

### D3: argumentative_coherence
score: not_assessed

### D4: cross_disciplinary_relevance
score: not_assessed

### D5: writing_and_structure
score: warn
trigger: "there are passages, numbers or figure panels that do not serve the thesis, small inconsistencies in numbers or terms between sections and legends, undefined borrowed vocabulary"

### D6: venue_fit_and_contribution
score: warn
trigger: "significance for non-specialist readers is under-articulated, positioning against the closest prior work is thin, generalisation beyond the study city or policy relevance is asserted rather than argued"

## Review Body

### Overall Recommendation (signal only)
**Major Revision.** The paper belongs in Nature Cities and its core results are new and of broad interest. The case for sending it out is weakened by framing, narrative economy and internal consistency, not by missing data. None of the fixes needs new analysis apart from the confirmatory test that is already planned. The final editorial decision belongs to the synthesizer.

### Summary Assessment
The manuscript reads São Paulo with the toolkit of spatial transcriptomics: 1.65 million parcels are cells, census tracts are spots and 15 crime types are phenotypes. From this it derives four results: a class-by-crime signature matrix, class-specific daily clocks that do not follow pedestrian volume, a stable "memory" of place beyond composition, and a predictability ceiling showing that month-to-month counts are close to Poisson noise outside a few hubs. The design is unusually careful for the field: crime-blind typing, spatial and temporal vaults, a pre-specified confirmatory family and an audit that scores each omics method against an urban analogue and reports where the analogy loses. It fits the venue well, in a Global South megacity with clear stakes for policing and planning. The format is within every limit. Three things hold it back. (1) The title and abstract sell the analogy rather than the urban finding, and what the analogy uniquely adds is overstated. (2) The text carries secondary analyses and figure panels that do not serve the thesis. (3) Names, comparators, data scope and evidence status drift between abstract, Results, Discussion, Methods and figures. Most notably, the abstract's lead clock example and the main policy recommendation rest on an analysis outside the confirmatory family whose 2025 test was not significant, and an in-sample dry run is reported as if it supported the confirmatory claims. These are repairable in one careful rewrite, so my signal is Major Revision.

### Criterion-Bound Judgements
| Dimension / criterion | Criterion source | Judgement | Evidence anchors | Rationale | Uncertainty or scope limit | Decision bearing? |
|---|---|---|---|---|---|---|
| Scope fit for Nature Cities | Contract D6; Nature Cities aims (urban science, policy-relevant) | MEETS | see S4, S7 | City-wide, parcel-scale crime analysis in a Global South megacity, with implications for policing and equity | none identified | yes: fit is not in question |
| Originality | Contract D6 | PARTLY_MEETS | see W2 | The substantive results (signature matrix, clocks per class, predictability ceiling) are new; what the analogy itself adds is overstated and the closest prior work is not engaged | Domain seat should confirm the closest prior work | yes: affects the framing of the contribution |
| Significance for a broad readership | Contract D6 | PARTLY_MEETS | see W3, W4 | No take-home for cities in the title or abstract; transferability beyond one city is not argued | none identified | yes |
| Claims proportionate to evidence stage | Contract D6; caller note on pending confirmation | PARTLY_MEETS | see W5, W6 | The dry run is reported as support; the lead example sits outside the confirmatory family | The confirmatory test is pending by design | yes |
| Article format compliance | Contract D5; Nature Cities Article limits | MEETS | see S6 | All length, reference and display-item limits are met | Reference house style not fully verified | no |
| One story, narrative economy | Contract D5 | PARTLY_MEETS | see W1, W11 | Four or five secondary analyses and about six figure panels do not serve the thesis | none identified | yes |
| Consistency across sections, figures and legends | Contract D5 | PARTLY_MEETS | see W7–W10, W12, W14, W19, W20 | Drift in data scope, terms, labels and numbers | Figures judged from development PNGs | yes |
| Clarity of exposition | Contract D5 | PARTLY_MEETS | see W8, W13 | Plain prose overall, but borrowed jargon is left undefined and key quantities are worded confusingly | none identified | no |
| Methodological rigor, domain accuracy, literature integration | Other seats (D1, D2, D4) | NOT_ASSESSED | — | Outside my remit | — | — |

### S1: The analogy is treated as a testable instrument, including its failures
The Discussion reports where the omics lens wins, ties and loses: it loses on ligand–receptor-style communication, and parcel typing does not predict better than the raw attributes. Extended Data Fig. 2 scores each module against an urban analogue. This candour is rare in papers that borrow from biology and will persuade sceptical readers.
**Evidence Anchor**: text: Discussion ¶4 "The analogy is thus useful as an instrument that can fail its tests, not as a description of what cities are."

### S2: Confirmatory safeguards that the field rarely uses
Parcel types were fixed without crime data, and spatial and temporal vaults, a pre-specified confirmatory family with Holm correction and planned OSF registration give the final paper a credibility advantage over most crime-and-place studies.
**Evidence Anchor**: text: Methods, Study design "Two vaults protect confirmatory tests."

### S3: The predictability ceiling is a general and policy-relevant result
Comparing model R² with the maximum R² that Poisson noise allows, at six space–time scales, separates "where" (near ceiling) from "when within a place" (far below a low ceiling). This is the most portable idea in the paper and speaks directly to the predictive-policing debate.
**Evidence Anchor**: figure: Fig. 6b — ensemble R² against the noise ceiling at six space–time scales

### S4: Scale and resolution in an under-studied megacity
The study covers a full city at parcel resolution, with 19 cell classes and 15 crime types. Studies at this scale in the Global South are scarce, and the data are public.
**Evidence Anchor**: text: Results ¶1 "We described each of 1,651,813 fiscal parcels by 30 attributes"

### S5: Fig. 4b makes the clock-versus-crowd argument at a glance
Overlaying robbery and pedestrian profiles for four classes shows the dawn mismatch at once. It is the kind of panel Nature Cities readers remember.
**Evidence Anchor**: figure: Fig. 4b — weekday robbery against pedestrians on the street in four classes

### S6: Full compliance with the Article format
Title, abstract, main text, Methods, reference count and display items are all within limits. The introduction is untitled and is followed by Results and Discussion, as the format requires.
**Evidence Anchor**: dataset: manuscript.md — section lengths (title 36 characters; abstract 149 words; main text about 2,590 words; Methods about 1,870 words; 54 references; 6 figures and 10 Extended Data figures)

### S7: An equity check on forecasting is built in
Reporting where flagged area falls by income quintile gives the forecasting half a concrete stake for urban policy.
**Evidence Anchor**: text: Results ¶ benchmark "Forecasts were calibrated within 5% across tract income quintiles, but the flagged area concentrated in richer tracts"

### S8: The gap in prior borrowing is stated cleanly
The introduction draws a clear line between earlier biological metaphors in urban research and the paper's instrumental use of the toolkit.
**Evidence Anchor**: text: Introduction ¶2 "but as metaphor rather than as a measurement instrument whose outputs can be tested"

### W1: Secondary analyses and panels dilute the single story
**Problem**: The thesis is that composition and memory make a stable map, while month-to-month variation is mostly noise. Around it, the text and figures carry material that does not advance this thesis:
- the full 12-method benchmark: Holm-adjusted CRPS, PAI at 1%, district-level lethal violence, all packed into one paragraph;
- a fine-tuned language-model decision layer, which appears only in Methods and as row H2 of Fig. 6g;
- the business-opening event study, placed inside the decline paragraph;
- Fig. 3f, a Shapley Sankey by criminological theory group (CPTED, social disorganization) that the text never mentions;
- Fig. 5f, change by crime type, which is never cited;
- Fig. 2c,e, tract pies and tissue domains, which are never cited;
- the "Ligand–receptor signal" row in Fig. 1a, which advertises a module the Discussion says fails.

The fourth Results subsection also packs four results under a three-part heading.
**Evidence Anchor**: text: Results ¶ benchmark "we benchmarked 12 methods from seismology, epidemiology, ecology, econometrics and machine learning"
**Why it matters**: Nature Cities readers judge a paper by whether they can state its one idea. Each side analysis costs words and attention, and the forecasting benchmark reads as a second paper.
**Suggestion**:
- Reduce the benchmark to two sentences: the ceiling, the best-model gain and the 5%-area capture. Keep the equity sentence. Move everything else to Extended Data Figs 1 and 8.
- Delete the language-model comparison from this paper.
- Move the event study to Extended Data and give it one sentence in the Discussion.
- Delete Fig. 3f or merge it into Extended Data Fig. 7. Delete or move Fig. 5f and Fig. 2c,e.
- Drop the ligand–receptor row from Fig. 1a.
- Split the fourth subsection into "Places remember" and "The decline spared the hubs".
**Severity**: Major
**Confidence**: 4 — core editorial competence in narrative structure

### W2: What the analogy uniquely contributes is overstated, and the closest prior work is not engaged
**Problem**: The Discussion credits the omics lens with four gains. One of them, "the decomposition of change", is Kitagawa's demographic rate–composition decomposition (ref. 37). Composition-aware attribution is a Poisson model on known exposures, which is close to ecological regression. The introduction positions the work only against the ecological fallacy and single-land-use or single-crime studies. It does not position it against the nearest composition-based approaches in environmental criminology, such as risk-terrain-style or multi-land-use street-segment models (the domain seat should confirm the exact set). The novelty claim, "read the full composition of a city, its crime types and its daily rhythm together", is a claim of integration.
**Evidence Anchor**: text: Discussion ¶4 "It adds attribution within the spot, phenotype signatures, a clock per class of cell and the decomposition of change."
**Why it matters**: The title makes the analogy the contribution. If referees can reclassify the wins as classical urban or demographic methods, they will read the paper as relabelling, which is the most damaging objection to this kind of work at a Nature-family journal.
**Suggestion**: State precisely what the omics workflow made possible that a criminologist would not have done: running signature, program and clock analyses systematically across all classes and crime types at once, with an audit. Credit the classical lineage of each step in Extended Data Fig. 2. Add two or three sentences to the introduction naming the closest composition-based crime models and saying what they cannot do.
**Severity**: Major
**Confidence**: 4 — core competence in computational urban science; exact prior-work set deferred to domain seat

### W3: The title and abstract convey an analogy, not an urban finding, and transferability is not argued
**Problem**: The title is a metaphor that states no result. The abstract ends on a forecasting detail and has no sentence on what cities or police should do differently. The policy content in Discussion ¶2–3 (where and when to target, the limited value of monthly forecast updates, equity) is absent from the abstract. The only treatment of generality is a single limitation sentence. The Discussion does not say which results should transfer to other cities: the predictability ceiling is a property of counts, while the signatures are city-specific.
**Evidence Anchor**: text: Title "Crime as a phenotype of urban tissue" and Limitations "The analysis covers one city."
**Why it matters**: Editors decide on send-out from the title, the abstract and the first paragraph. Without an urban take-home and a transferability argument, a single-city study risks being judged of local interest.
**Suggestion**:
- Use a declarative title that carries the finding, for example a variant of "A stable map and a noisy month: crime structure and its predictability in São Paulo" (the authors' wording to decide).
- End the abstract with one sentence of implication, such as "prevention can be targeted by place type and hour, and monthly forecasts add little to a static map".
- Add a short Discussion paragraph on what should generalise and how to test it elsewhere with public cadastres.
**Severity**: Major
**Confidence**: 4 — core editorial competence in venue fit

### W4: The forecasting conclusion names different comparators in the abstract, Results and Discussion
**Problem**: The abstract says forecasts add little beyond "the tissue map", meaning composition. The Results benchmark forecasts against the historical mean and a negative binomial model, and Fig. 5a shows that the tissue alone is much weaker than history (R² 0.25 against 0.48). The Discussion says "a stable map of tissue and memory". The abstract therefore implies that composition alone suffices, which the paper's own data contradict.
**Evidence Anchor**: text: Abstract "forecasts add little beyond the tissue map outside a few hubs" against Discussion ¶3 "Monthly forecasts add little to a stable map of tissue and memory"
**Why it matters**: This is the closing claim of the abstract and the take-home of half the paper. Inconsistent comparators undermine the synthesis of "stable map, noisy month".
**Suggestion**: Use one formulation everywhere, for example "forecasts add little beyond a static map of where crime has been (tissue plus memory)". Make sure the Results sentence "This ceiling bounds what forecasting can add" names the same comparator.
**Severity**: Major
**Confidence**: 4 — direct reading of text and Fig. 5a

### W5: An in-sample dry run is reported as support for the confirmatory claims
**Problem**: The Results say all five confirmatory claims "were sustained" in a pseudo-vault drawn from the exploration districts. Fig. 6g prints P values for it beside a "Confirmation" column. Methods describe the same exercise as a code check. Internal codes ("A11", "sealed until A11", "Laya-FT") are meaningless to readers.
**Evidence Anchor**: text: Results ¶ confirmatory "All five were sustained after Holm correction in a pseudo-vault of 19 exploration districts drawn at random"
**Why it matters**: Readers and press will take "sustained" as independent support before the real test exists. That misrepresents the evidence stage, which is the point the preregistration is meant to protect.
**Suggestion**: Move the dry run to Methods as a code check, with no P values in the main text. Make Fig. 6g a plain list of the pre-specified claims and their criteria, to be filled with vault results. Replace internal codes with plain labels.
**Severity**: Major
**Confidence**: 4 — editorial judgement on framing; facts taken from the manuscript's own Methods

### W6: The abstract's lead clock example and the main policy recommendation rest on an exploratory result
**Problem**: The abstract illustrates the clocks with phone robbery at dawn (41% of robberies against 3% of pedestrians), and Discussion ¶2 builds its main recommendation on it (guardianship between 04:00 and 06:00). But the robbery clock failed the 2025 permutation test (P = 0.07), and the confirmatory claim A-R7 concerns phone theft (Fig. 6g). The Results then infer that dawn robbery "tracks the absence of guardians … rather than the volume of targets". Pedestrians are both targets and guardians, so a low pedestrian count cannot separate the two.
**Evidence Anchor**: text: Results, clock ¶1 "for phone robbery in 2024 (P = 0.005; P = 0.07 in 2025)"
**Why it matters**: Once the confirmatory results are in, the most quotable number in the paper will be one that was never put to the test, and its interpretation is not tested either.
**Suggestion**: Lead the abstract with the phone-theft clock, which is in the confirmatory family. Alternatively, keep the robbery example but label it exploratory and add it to the 2026 hold-out if the protocol allows. Report the 2025 non-significance wherever the 41% appears. Soften "thus tracks the absence of guardians" to "is consistent with low guardianship".
**Severity**: Major
**Confidence**: 4 — reading of Results, Fig. 4d and Fig. 6g

### W7: The districts used by the forecasting analyses contradict the stated design
**Problem**: The introduction says every crime analysis uses the 77 exploration districts. Methods describe the vault as protecting the atlas only, and resample all 96 districts for the forecasting benchmark. Neither Fig. 6 nor its legend says which districts or tracts the dispersion test and benchmark used.
**Evidence Anchor**: text: Introduction ¶3 "all crime analyses use 77 exploration districts" against Methods, Forecasting benchmark "Differences used 2,000 bootstrap resamples of the 96 districts"
**Why it matters**: If crime records from the vault districts entered any analysis, readers will ask whether the spatial vault is still blind. Even if it is, the contradiction erodes trust in the paper's central safeguard.
**Suggestion**: State the data scope of every analysis in a single table in Methods. Correct the introduction sentence. If the benchmark used vault districts, explain why that does not compromise the atlas claims.
**Severity**: Major
**Confidence**: 3 — inconsistency is clear; its consequence depends on pipeline details I cannot see

### W8: Names of classes, groupings and borrowed terms drift between text, figures and legends
**Problem**: The cadastral type "Low-rise residential, low standard" (a building standard) becomes "low-income housing", "low-income houses" and "low-income peripheral fabric" in the abstract, Results and Discussion. The paper separately analyses tract income, so the relabel imports a socioeconomic claim. Other mismatches:
- "medium-standard" in the text against "middle standard" in the figures;
- "high-rise mixed parcels" against "Mid/high-rise, residential and mixed";
- "residential burglary", "cargo robbery", "street theft" and "assault outside the home" in the text against "Dwelling burglary", "Cargo theft/robbery", "Theft from person" and "Assault (non-domestic)" in Fig. 3;
- the programs named "transport, dense-centre, peripheral-logistics and residential" in the text but labelled by classes in Fig. 3d.

Fig. 1a defines "niche" as neighbourhood composition. The text then uses it in an ecological sense ("Crime receded to its niches"), and Fig. 5a uses it for undefined tissue features. "Family", a third grouping between the 12 types and 19 classes, is never defined, and neither are "hubs" or "diffuse fabric". Fig. 2b ("Mean expression", "Parcels expressing") and Fig. 5a ("Same genes, no typing") put transcriptomic jargon on axes, and the abstract uses "spots" without defining it.
**Evidence Anchor**: text: Abstract "on low-income housing, 41% of weekday phone robberies occur between 04:00 and 06:00"
**Why it matters**: A broad readership cannot follow a story whose units change names between panels. The "low-income" relabel also shapes the equity reading of the policy paragraph.
**Suggestion**:
- Add one naming key: a glossary table in Methods or Extended Data covering types, families, classes, crime types, programs and analogy terms. Apply it to all text and figures.
- Call the class "low-standard housing" unless income data are used.
- Replace gene and expression wording on figure axes with "attribute" wording.
**Severity**: Major
**Confidence**: 5 — direct cross-check of text and all six figures

### W9: Figure labels say "thefts" where the text reports phone crime
**Problem**: Several figures label the outcome as thefts. The text defines phone crime as thefts plus robberies and quotes values (71 per km, 87 per station, 53% captured) that match these figures.
**Evidence Anchor**: figure: Fig. 3a — x-axis "Phone thefts per year, per km" (likewise Fig. 3f sink, Fig. 5a, Fig. 6a, 6c, 6e, 6f)
**Why it matters**: Readers cannot tell which outcome is plotted.
**Suggestion**: Relabel these figures "phone crime" throughout, or correct the text if they do plot thefts only.
**Severity**: Minor
**Confidence**: 4 — values read from figures match the text

### W10: Fig. 6e appears to contradict the text on lethal violence
**Problem**: The text says no method beat the baseline for lethal violence at district scale. Fig. 6e shows positive CRPS skill against the historical mean for lethal violence for all three methods (about +2% to +6%). It gives no sign convention and no intervals.
**Evidence Anchor**: text: Results ¶ benchmark "At the scale of districts, no method beat the baseline for lethal violence"
**Why it matters**: A visible contradiction between a text claim and its figure undermines trust in the rest of the figure.
**Suggestion**: State the sign convention and add intervals, then reword, for example "no method significantly beat".
**Severity**: Minor
**Confidence**: 3 — depends on an unstated sign convention

### W11: Uncited panels and Extended Data numbering out of citation order
**Problem**: Nature requires every panel to be cited and Extended Data figures to be numbered in order of first citation. Here, Extended Data Fig. 2 is cited first and Extended Data Fig. 1 never. Extended Data Figs 3–5 are cited only as a range. Fig. 6 panels are first cited in the order b, c, d, a.
**Evidence Anchor**: absence: Results, Discussion and Methods call-outs — expected in-text citations of Fig. 1c,d, Fig. 2c,e, Fig. 3f, Fig. 5f and Extended Data Figs 1, 6, 7, 8 and 10b–d; checked every figure call-out from the introduction to the Methods
**Why it matters**: This is a format compliance issue, and it also signals panels that may not belong (see W1).
**Suggestion**: Cite or cut each panel, renumber Extended Data in order of citation, and reorder the Fig. 6 panels to follow the text.
**Severity**: Minor
**Confidence**: 5 — mechanical check

### W12: The parcel-type palette in Fig. 1 is reversed relative to Figs 2–5
**Problem**: In the Fig. 1 legend, "Low-rise residential, low standard" is dark navy and "high standard" is pale blue. Figs 2b and 3a use the opposite. Commerce shades are likewise inverted ("Low-rise mixed, wholesale" is dark in Fig. 1 and pale in Fig. 2b). The tissue-domain palette in Fig. 2e reuses type colours.
**Evidence Anchor**: figure: Fig. 1 legend against Fig. 2b and Fig. 3a swatches — residential blues and commerce oranges inverted
**Why it matters**: The Fig. 1 map is the reader's first key to the types. Reversed colours mislead in every later figure.
**Suggestion**: Use one palette for all figures, and give domains a palette that cannot be confused with the types.
**Severity**: Minor
**Confidence**: 5 — visual check of the development figures

### W13: The quantities behind the predictability ceiling are worded confusingly
**Problem**: The ceiling is described as the "maximum R² without a model", which reads as what one gets without modelling. It is in fact the largest R² any model could reach given Poisson noise. The 5%-area benchmark is called "the share expected if the model were true" in the text but "Noise ceiling" in Fig. 6a.
**Evidence Anchor**: text: Fig. 6 legend "maximum R² without a model (open)"
**Why it matters**: The ceiling is the paper's most portable idea (S3), so it must be unambiguous.
**Suggestion**: Use a single term, such as "noise ceiling: the largest R² attainable by any model under Poisson noise", in the Results, legends, figure keys and Methods.
**Severity**: Minor
**Confidence**: 4 — clarity judgement

### W14: Fig. 2f plots the selected resolution at about 14 types, but the legend says 12
**Problem**: Methods explain that the chosen clustering was then refined by merging small types and splitting out high-rise parcels. The ARI of 0.973 therefore refers to a different number of types from the 12 reported.
**Evidence Anchor**: figure: Fig. 2f — orange point at about 14 types against legend "selected resolution (12 types, ARI = 0.973)"
**Why it matters**: This is a small but visible number mismatch on the typing that underpins the rest of the paper.
**Suggestion**: State in the legend and in the Results that the ARI is for the resolution before refinement, or report the ARI of the final 12 types.
**Severity**: Minor
**Confidence**: 4 — figure read against Methods

### W15: The Discussion overstates the independence of its validation data
**Problem**: The Discussion says the main statements were checked against unused data. But geocoded events also feed the reconciled counts used for attribution, and the "pedestrian counts" are modelled estimates from a 2017 travel survey, not counts.
**Evidence Anchor**: text: Discussion ¶1 "The main statements were checked against data that the analyses did not use"
**Why it matters**: This sentence frames the credibility of the whole paper, and a referee will catch it.
**Suggestion**: Say "checked against finer-grained or separate data", and "survey-based pedestrian estimates".
**Severity**: Minor
**Confidence**: 3 — independence questions are for the methodology seat; here only the wording is judged

### W16: An untested comparative policy claim
**Problem**: The Discussion claims the results locate prevention more precisely than hot spots, but no comparison with hot-spot targeting is made. The attribution is associational, as the limitations acknowledge.
**Evidence Anchor**: text: Discussion ¶2 "The results locate prevention more precisely than hot spots do."
**Why it matters**: Policy readers will act on the strongest sentence in the implications.
**Suggestion**: Change it to "could help target prevention within hot spots", or add the comparison.
**Severity**: Minor
**Confidence**: 4 — editorial judgement on proportionality

### W17: The abstract's "96% of tracts" leans on low-count tracts
**Problem**: The Results give 86% for tracts with at least one event per month. The higher figure includes tracts where a dispersion test has little power to detect anything but Poisson noise.
**Evidence Anchor**: text: Abstract "are consistent with Poisson noise in 96% of tracts"
**Why it matters**: The headline number should be the defensible one.
**Suggestion**: Use the 86% figure in the abstract, or qualify the 96%. The methodology seat may wish to address power.
**Severity**: Minor
**Confidence**: 3 — framing judgement; power analysis is outside my remit

### W18: Gaps in the numbering of the confirmatory claims invite questions about selective reporting
**Problem**: The confirmatory family is numbered A-R1, A-R2, A-R6, A-R7 and A-R8, and the paper never says what became of A-R3 to A-R5.
**Evidence Anchor**: text: Methods, Study design "claims A-R1, A-R2, A-R6, A-R7 and A-R8, below"
**Why it matters**: In a preregistered design, unexplained gaps look like dropped hypotheses.
**Suggestion**: Relabel the claims C1–C5 and state in one sentence how the family was fixed and when.
**Severity**: Minor
**Confidence**: 4 — transparency convention

### W19: A headline count in the abstract cannot be traced in the body
**Problem**: The body reports 0.69 million events (15 crime types, 2024–2025) and 121,434 (phone crime, 2025), but never 1.83 million. The denominator of "39% of the police records analysed here" is also unclear.
**Evidence Anchor**: text: Abstract "1.83 million police records form a panel of 15 crime phenotypes"
**Why it matters**: Every number in the abstract should be traceable to the body.
**Suggestion**: Use one count, with years and districts, in the abstract, introduction and Data section.
**Severity**: Minor
**Confidence**: 5 — text search

### W20: The Results omit that tissue explains only 18% of variance in high-crime tracts
**Problem**: The Results report only that memory rises to 58% in high-crime tracts. Fig. 5b also shows the tissue share falling from 42% to 18% there. "High-crime tracts" is defined only in the legend, and the shares sum to more than 100% with a negative covariance term, which readers will not follow without help.
**Evidence Anchor**: figure: Fig. 5b — high-crime tracts bar 18% tissue, 58% memory, 16% transient; all-tracts bar 42%, 48%, 23%, covariance −13%
**Why it matters**: In the places policy cares about most, composition explains least. This qualifies "composition sets where crime occurs" and belongs in the text.
**Suggestion**: Report both shares, define high-crime tracts in the Results, and explain the covariance term in the legend.
**Severity**: Minor
**Confidence**: 4 — figure read against text

### Detailed Comments

#### Journal Fit
Squarely in scope. The paper addresses crime, a first-order urban outcome, at parcel scale in a megacity of 11.5 million people, with implications for policing, planning and the equity of algorithmic targeting. Its methodological cross-over is the kind Nature Cities seeks. The policy implications should be in the abstract (W3).

#### Originality
New: the class-by-crime signature matrix with point validation, clocks per class tested against a crowd denominator, the tissue–memory–transient decomposition, and the predictability ceiling. The equivalence audit is itself original. The originality of the analogy as a method is overstated (W2).

#### Significance
Potentially high, especially the "stable map, noisy month" result for predictive policing (S3). Significance beyond São Paulo needs an explicit argument (W3).

#### Structural Coherence
The introduction poses three questions (which crime, when, what remains) and the Results answer them in order. That backbone is good. Coherence is lost in the drift of comparators (W4), data scope (W7), terms (W8) and evidence status (W5, W6), and in side analyses (W1).

#### Title & Abstract
The title is under the length limit but states no finding. The abstract has 149 words, no references and a clear "Here we" turn. Its first sentence is convoluted ("mapped places mix many land uses, so which component of a place produces which crime, and when, is inferred from aggregates"). It uses "spots" and "class of cell" without definition. It omits the confirmatory design and the audit, both of which are selling points, and it ends without an implication.

#### Conclusion
The Discussion opens with a crisp summary and ends with limitations and the pending test, which is appropriate at this stage. Once confirmation is in, end on one sentence of what cities should do with a stable map and a noisy month.

### Questions for Authors
1. Did any analysis, including the forecasting benchmark and the dispersion test, read crime records from the 19 vault districts? If so, how does the spatial vault stay blind for the atlas claims?
2. What were claims A-R3 to A-R5, and were they removed before or after exploration results were seen?
3. If a planner reads only one sentence, should it be about the analogy as an instrument or about the stable map and the noisy month? The title and abstract should follow that choice.
4. Will the phone-robbery dawn pattern be tested in the 2026 hold-out? If not, why does it lead the abstract?

### Minor Issues

#### Language
- Results, decline ¶: dangling modifier in "Holding composition at 2025 and estimating class rates by year, a rate–composition decomposition, the fall was uneven". Rewrite with "we" as the subject.
- Results: "Marginal changes to the tissue did not move crime" generalises from openings and closures of specific business types; narrow it.
- Results: "the city sits close to its limit of predictability" borrows a concept from individual mobility (ref. 41) that does not map onto Poisson ceilings; drop it or explain it.
- Discussion ¶1: "fixes much of what composition leaves unexplained" should be "accounts for".
- Results, clock ¶2: one parenthesis carries four correlations; move two to the legend.
- Correlation notation mixes r and ρ; state which r is Pearson.

#### Citation Format
- Article-title capitalisation is inconsistent: Title Case in refs 7, 10, 11, 13, 21, 23, 28, 33, 34, 36, 38, 41, 42, 44, 47 and sentence case elsewhere. Apply Nature house style uniformly.
- Check whether Nature Cities prints DOIs as full URLs in the reference list.

#### Figures and Tables
- Fig. 3c: the hollow markers ("all cell classes") are not described in the legend.
- Fig. 5a: the annotation "ICC = 0.84" is not explained.
- Fig. 6a: the "Chance" and "Ensemble, geocoded only" lines and the 28% annotation are not in the legend.
- Fig. 4e: phone-theft markers are missing for several classes without explanation.
- Fig. 4f: labels overlap points ("retail (mid)").
- Fig. 1: "FCU" is not defined.
- Fig. 6g: "Laya-FT" is undefined.
- Fig. 2d: colour-bar z-scores of about ±100 need a sentence of interpretation.

#### Layout
- The confirmatory paragraph sits inside the forecasting subsection although it covers claims from Figs 3–5. Move it to a short closing subsection or to Methods (see W5).
