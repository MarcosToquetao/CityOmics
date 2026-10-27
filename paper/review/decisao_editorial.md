# Editorial Decision Package

- **Manuscript**: "Crime as a phenotype of urban tissue" (`paper/manuscript.md`)
- **Target venue**: Nature Cities, Article (simulated review)
- **Manuscript ID**: n/a (development draft; 77 exploration districts; confirmatory test pending by design)
- **Review round**: 1 | **Decision date**: 2026-10-19
- **Mode and contract**: `reviewer_full`, `reviewer/reviewer_full/v2` (ARS v3.23.1)
- **Inputs**: `00_painel.md`; Phase 1 cards `eic_fase1.md`, `r1_metodologia_fase1.md`, `r2_dominio_fase1.md`, `r3_perspectiva_fase1.md`, `da_fase1.md`; Phase 2 reports `eic.md`, `r1_metodologia.md`, `r2_dominio.md`, `r3_perspectiva.md`, `da.md`. The manuscript was read only to check anchors; it was not modified.

## Calibration Resolution

`calibration_status: NOT_CALIBRATED`

Current runtime boundary: this package is not upgraded from a candidate or prose-named profile. `PROFILE_MEASURED` remains unavailable until a closed profile artifact and replay validator bind the exact target fields to the completed panel's `execution_topology_sha256`. Every seat also reports `NOT_CALIBRATED`.

## Review Panel Provenance (#540/#740)

- **Typed artifact**: MISSING. No `review-panel-provenance/1.0` artifact was supplied. **Provenance artifact failure flagged.** Following the protocol, every axis is rendered `unknown`.
- **Artifact SHA-256**: unknown | **Panel ID**: unknown | **Normalized manifest SHA-256**: unknown | **Execution topology SHA-256**: unknown
- **Fresh-context scope**: `within_panel_attempt_only` (does not compare retries or prior rounds)

| Seat | Role ID | Actor type | Context ID | Peer outputs visible | Model family | Provider | Human reviewer ID |
|---|---|---|---|---|---|---|---|
| EIC (Journal-Fit) | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| R1 (methodology) | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| R2 (domain) | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| R3 (perspective) | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| DA | unknown | unknown | unknown | unknown | unknown | unknown | unknown |

| Provenance axis | Status |
|---|---|
| Role-separated | unknown |
| Within-panel invocation-context separation | unknown |
| Blind to peer outputs | unknown |
| Model-family distinct | unknown |
| Provider distinct | unknown |
| Human-reviewer distinct | unknown |

- **Binary independence claim**: Not computed. Role diversity proves at most role separation; the panel is not described as independent.
- **Correlated-error disclosure (family unknown at artifact level)**: Model-family and provider distinctness could not be verified from a typed artifact. The panel configuration declares that all five seats ran on the same model family and the same provider, so errors across seats may be correlated. Agreement between seats in this package, including CONSENSUS-4 and CONSENSUS-3 labels, is not evidence of independent confirmation.

**Declared provenance (from `00_painel.md` and the dispatching session; not artifact-verified):**
- Five subagents, each started in a fresh and separate context; per `00_painel.md` they were dispatched in parallel and no seat read another seat's report.
- Same model family and same provider for all five seats.
- Phase 1 (contract paraphrase and scoring plan, written before the paper was read) and Phase 2 (the report) ran sequentially inside each subagent, not as physically separate calls. "Plan before paper" is therefore an ordering inside one context, not an enforced separation.
- No accountable human reviewer sits behind any seat.
- This is role separation, not independence.

## Run Integrity Notes (flagged, not fixed)

1. **Criteria binding**: all five Phase 1 cards disclose `criteria_binding_unavailable`. This is an explicitly unbound run, so this package makes **no venue-alignment claim**. D6 is scored against the Journal-Fit Reviewer's own Phase 1 plan; the Nature Cities limits cited in the cards are the reviewers' descriptions, not a bound criteria digest.
2. **Phase 1 markers**: the EIC, R2 and DA cards carry `[CONTRACT-ACKNOWLEDGED]` and `[PRE-COMMITMENT-ACKNOWLEDGED]`. The R1 and R3 cards carry only `[PRE-COMMITMENT-ACKNOWLEDGED]`. All five contain the contract paraphrase and scoring plan the contract requires. The arithmetic is unaffected.
3. **Scoring-plan schema**: the EIC plan for D5 and the R3 plan for D4 omit `what_triggers_fatal`. Neither dimension is mandatory, so fatal scope does not apply to them. Flagged as a schema gap only.
4. **DA table columns**: the "Field-Norm Boundary" and "Evidence-Crossing Rationale" columns are empty for C1 and for every MAJOR row. The DA's criterion table states that no CRITICAL or MAJOR row rests on an asserted field norm.
5. **Literature verification**: R2 and R3 mark some references "verified this session" and others `[UNVERIFIED]`. The synthesizer re-verified none of them. Roadmap items carry the reviewers' flags, and authors must verify every suggested reference before citing it.
6. **Placeholders**: `[CONFIRMATION]`, `[ETHICS]`, `[OSF DOI]` and the author fields are deliberate author decisions. No seat penalised them, and neither does this package.
7. **Instruction and data boundary**: the manuscript and the reviewer cards contain no text addressed to the synthesizer. The DA's "Direct answers to the panel's weighting questions" are read as DA findings.
8. **Cross-model decision check (#518)**: `ARS_CROSS_MODEL` is unset and no consent gate was passed, so the check was not run.
9. **Machine artifacts**: the closed `revision-roadmap/1.0` JSON core and the Schema 6 package are not emitted, because the requested deliverable is this single Markdown file. Closed enums used below (obligation, cost scope, consequence codes) are those of the schema. No bound block manifest exists, so proposed targets are given as manuscript locators. Allowed operations are `replace_block`, `insert_after` and `delete_block`.
10. **Roadmap identifiers**: items use the requested `R-NN` form in place of the template's `R<n>`/`S<n>`. They are transport references, not ranks.
11. **Arbitration seat**: the Journal-Fit Reviewer seat was blind to the other cards and did not arbitrate. The SPLIT arbitrations below are the synthesizer's, made on manuscript evidence and seat expertise. Where the EIC card speaks to an issue, it is cited.
12. **Surface-form parity (#216) and confidence**: no sub-claim was down-rated for informal wording or credited for technical phrasing. Confidence values are transported as self-reported scope only and never weighted, totalled or used to resolve a dispute.

---

## 1. Mechanical Decision Derivation (D1–D6)

### 1.1 Role-scoped scoring matrix

Ineligible seats all scored `not_assessed`, so no ineligible seat voted. No eligible seat abstained, no scoring-plan dissent was recorded, and no seat declared a fatal block. Every trigger quoted in a Phase 2 score matches that seat's own Phase 1 plan.

| Dim | Name | Priority | Eligible roles | EIC | R1 | R2 | R3 | DA | Assessed n | Verdict (worst assessed) |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 | methodology_rigor | mandatory | methodology | – | **block** (repairable) | – | – | – | 1 | **block** |
| D2 | domain_accuracy | mandatory | domain | – | – | **block** (repairable) | – | – | 1 | **block** |
| D3 | argumentative_coherence | mandatory | da, methodology | – | **block** (repairable) | – | – | **block** (repairable) | 2 | **block** |
| D4 | cross_disciplinary_relevance | high | perspective | – | – | – | **warn** | – | 1 | **warn** |
| D5 | writing_and_structure | normal | eic | **warn** | – | – | – | – | 1 | **warn** |
| D6 | venue_fit_and_contribution | mandatory | eic | **warn** | – | – | – | – | 1 | **warn** |

("–" means `not_assessed` by an ineligible seat, excluded from numerator and denominator.)

### 1.2 Failure conditions

Every expression parses in the closed vocabulary, so no `[EXPRESSION-UNRECOGNISED]` marker is needed.

| ID | Sev. | Quantifier | Expression | Per-dimension evaluation | Fired |
|---|---|---|---|---|---|
| F1 | 95 | any | any mandatory dimension has a fatal block | D1, D2, D3, D6: no fatal block declared | **false** |
| F2 | 90 | any | any mandatory dimension scores 'block' | D1 true (R1); D2 true (R2); D3 true (R1, DA); D6 false (warn) | **true** |
| F3 | 70 | majority | two or more mandatory dimensions score 'warn' or worse | D1 n=1, owner R1 block → true; D2 n=1, owner R2 block → true; D3 n=2, both seats block → true; D6 n=1, owner EIC warn → true; 4 ≥ 2 | **true** |
| F4 | 60 | any | any high-priority dimension scores 'block' | D4: R3 warn → false | **false** |
| F5 | 40 | any | any dimension scores 'warn' or worse | D1–D6 all true | **true** |
| F0 | 10 | all | every dimension scores 'pass' | D1 false (and all others) | **false** |

### 1.3 Precedence and decision

The highest-severity fired condition is F2 (90), whose action is `editorial_decision=major_revision`. The action is not softened.

```
dimension_verdicts: [D1=block, D2=block, D3=block, D4=warn, D5=warn, D6=warn]
fired_conditions: [F2, F3, F5]
da_critical_adjudications: [C1=VALIDATED]
editorial_decision=major_revision
```

The decision is not `accept`, so the `[DA-CRITICAL-VS-ACCEPT]` marker does not apply.

### 1.4 Consistency check (informative only; cannot override the contract)

All four scoring seats signal **Major Revision** (EIC, R1, R2 and R3, each with confidence 4). In the no-contract recommendation matrix, Major/Major/Major/Major maps to Major Revision, which agrees with the mechanical result.

---

## 2. Devil's Advocate CRITICAL Adjudication

The DA card contains one CRITICAL item, C1.

### C1: D3 core thesis (data–conclusion mismatch). Verdict: **VALIDATED** (repairable, not fatal)

- **DA's argument.** The title and Discussion present crime as a phenotype of tissue and say composition "fixes" a place's rate. The paper's own estimates make tissue the minority component: 42% of between-tract variance against 48% for a stable non-tissue component (58% in high-crime tracts). Out of sample, tissue reaches R² = 0.25 (0.31 with covariates) against 0.48 for the tract's history, and rates move while 98.2% of parcels keep their family. The required fix is to narrow the thesis or show that the residual is unmeasured tissue, and in either case to report the tissue–memory cross-term.
- **Manuscript check (read-only).** The anchors are verbatim. Discussion ¶1 reads: "The composition of a place fixes its rate, which crimes it produces and at what hour." Results §Stable tissue ¶1 gives 42%, 48% and 58%, R² 0.25, 0.31 and 0.48, and 98.2%. The same claim recurs in Intro ¶3 ("composition sets where crime occurs, which crime and at what hour"), Results §Each cell class ¶2 ("Composition thus sets not only how much crime a place has but which crime") and Results §Month-to-month ¶1 ("If composition and memory fix where crime occurs"). Composition alone explains D² = 0.34 of the deviance (Results §Each cell class ¶1).
- **A sub-point paraphrased loosely.** "Class rates also move by up to 40%": the −40% is the citywide fall in phone robbery, and the largest class relative ratio reported is 0.76, for local streets. The manuscript itself says "Rates, however, do move" with composition fixed. The sub-point supports the time dimension of C1, but its number is not a class-rate change. The verdict rests on the variance and out-of-sample figures.
- **Corroboration by seats that did not see the DA card**:
  - EIC-W20: tissue falls to 18% in high-crime tracts, which "qualifies 'composition sets where crime occurs'".
  - EIC-W4: the abstract implies composition alone suffices, which R² 0.25 against 0.48 contradicts.
  - R1-W9: with a negative cross-term, 42% overstates what tissue explains; the implied in-sample R² is about 0.20–0.30.
  - R2-W17: the abstract credits composition with predictive value that comes from history.
  - R3-W4: the 48% residual exceeds the 42% tissue share and may be missing composition.
- **Journal-Fit Reviewer's assessment.** The EIC seat was blind and did not rule on C1. Its W4 and W20 rest on the same estimates and point the same way. This adjudication is the synthesizer's.
- **Why validated.** The anchors are exact, and the contradiction is between a sentence and the statistic offered for it, which is the D3 block trigger.
- **Why not fatal.** The DA classes its block repairable. R1's D3 block is also repairable. No seat invokes the D3 fatal trigger, and a narrower thesis is supported by the results shown (DA; R1 Detailed Comments, Title and Abstract).
- **Effect on the decision.** C1 blocks Accept and is consistent with the mechanical Major Revision.
- **Required author response.** The authors must take one of the DA's two paths and say which:
  - (i) narrow the thesis ("composition structures which crime and when, and part of how much, while place history carries more"), retitle, and replace "fixes" and "sets where" throughout; or
  - (ii) show that the persistent residual is unmeasured composition.

  Under either path, report the tissue–memory cross-term. Resolving items: R-01, R-08, R-31, R-32, R-110, R-120. If the authors disagree, they must say so explicitly in the response letter.

### Disposition of DA MAJOR rows (adjudication not required; recorded for visibility)

All eleven MAJOR rows are retained; none is rejected.

| DA row | Non-DA corroboration | Sub-claim(s) | Roadmap |
|---|---|---|---|
| M1 constant-rate assumption | R1-W3, R2-W2, R3-W1 | SC-34, SC-59, SC-60 | R-100, R-110, R-120 |
| M2 reconciliation artefact | R1-W2 | SC-38, SC-40 | R-37, R-97, R-98 |
| M3 noise as absence of evidence | EIC-W17, R1-W4/W6, R2-W6/W14, R3-W2 | SC-70–SC-77 | R-28, R-35, R-41, R-56, R-66, R-102, R-103 |
| M4 decline vs noise; citywide causes | R2-W4 (partial) | SC-64, SC-65, SC-67, SC-68 | R-54, R-74, R-119, R-123, R-132 |
| M5 validation independence | EIC-W15, R1-W1 (R3 disputes) | SC-31 | R-25, R-95 |
| M6 guardianship clock | EIC-W6, R1-W13, R2-W3/W8 | SC-50–SC-54, SC-57 | R-15, R-16, R-47, R-113, R-118 |
| M7 causal drift; null event study | R3-W3 (partial), EIC-W16, R2-W8 | SC-07, SC-08, SC-11, SC-94 | R-04, R-27, R-34, R-67, R-112 |
| M8 reporting by income and place | R2-W7, R3-W5 | SC-87, SC-88, SC-90 | R-57, R-126, R-133 |
| M9 three stories | EIC-W1, R3-W1(d) | SC-03 | R-01 |
| M10 relabelling; head-to-head | EIC-W2, R2-W2, R3-W1 | SC-21, SC-22, SC-24 | R-06, R-07, R-124 |
| M11 abstract credits tissue | EIC-W4, R2-W17 | SC-81 | R-11 |

---
## 3. Consensus and Disagreement

### 3.1 Reviewer summary matrix

| | Journal-Fit Reviewer (EIC) | R1 (Methodology) | R2 (Domain) | R3 (Perspective) | DA |
|---|---|---|---|---|---|
| Recommendation (signal) | Major Revision | Major Revision | Major Revision | Major Revision | N/A (findings only) |
| Confidence / scope | 4: urban data science and editing; no criminological or statistical detail | 4: core expertise; some concerns inferred from Methods wording | 4: criminology; no omics-side methods | 4: omics core; criminology and Brazilian policing adjacent | per finding only |
| Dimension scores | D5 warn, D6 warn | D1 block, D3 block | D2 block | D4 warn | D3 block |
| Key strengths | Analogy run as a testable instrument with losses reported; vaults and Holm family; predictability ceiling; scale; Fig. 4b; equity check | Two vaults; crime-blind typing; district block bootstrap; proper scoring; candour about losses; crowd test; positive control; noise ceiling | Concentration literature incl. Latin America; offence disaggregation; hourly denominators; falsifiable checks; equity audit; dawn-robbery pattern; candid scope | Analogy falsifiable with losses; well-chosen bridge problem; orthogonal-validation habit; crowd normalisation and non-police recommendation; bounded, audited forecasting | Strong safeguards; audit reports losses; MDE for null; positive control; ceiling split |
| Weaknesses (see 3.3) | 20 (8 major, 12 minor) | 20 (11 major, 9 minor) | 18 (8 major, 10 minor) | 12 (5 major, 7 minor) | 1 critical, 11 major, 12 minor |
| Questions | 4 | 4 | 7 | 5 | 0 |
| Minor-issue entries | 17 | 6 | 10 | 5 | n/a |

### 3.2 Counting rules applied

- Sub-claims (SC) are atomic parts of the weaknesses that reviewers actually raised. None is added by the synthesizer.
- Consensus is counted over the **four non-DA seats**. A silent seat is neither agreement nor opposition.
- Disposition precedence:
  - any `disputed` position → **SPLIT**;
  - otherwise 4 agree → **C4**; 3 agree → **C3**; 2 agree → **CORR-2**; 1 agrees → **SINGLE**;
  - the DA is tracked separately (`+DA` where it corroborates; **DA-only** where no non-DA seat raised the point).
- Severity is transported from each seat's per-finding tag. A sub-claim inherits its parent finding's tag.
  - `†` marks `[SEVERITY-SOURCE: letter-fallback]`: minor-issue lists and detailed comments, which carry no tag, are rendered minor.
  - `‡` marks `[CONFIDENCE-SOURCE: report-level]`.
  - Questions carry no severity (`Q`).
- **Operational rule for severity disputes.** A seat counts as `disputed` only when its card asks for an incompatible action or argues the point is not a problem. Severity differences that arise because seats' parent findings bundle different sub-claims are recorded per source (§3.6) but are not disputes, because no seat re-rated the sub-claim itself.
- **Cell codes** in 3.3:
  - `R` raised directly;
  - `C` corroborated indirectly;
  - `D` disputed;
  - `·` silent.

### 3.3 Sub-claim inventory (Step 1b)

| SC | Sub-claim | EIC | R1 | R2 | R3 | Disposition | DA | Items |
|---|---|---|---|---|---|---|---|---|
| SC-01 | Thesis wording ("fixes", "sets") outruns own estimates | R W20, mi | C W9 | · | · | CORR-2 | C1 | R-32 |
| SC-02 | High-crime tissue share (18%) and covariance term unreported or unexplained | R W20 | R W9, mi | · | · | CORR-2 | C1 | R-31 |
| SC-03 | No single spine; title, abstract end, Discussion and final sentence misaligned | R W1, Q3, dc | · | · | R W1(d), dc | CORR-2 | M9 | R-01 |
| SC-04 | Title states analogy, not finding | R W3 | · | · | · | SINGLE | C1, M9 | R-08 |
| SC-05 | Abstract lacks implication; undefined terms; convoluted opening | R W3, dc, W8 | · | · | · | SINGLE | – | R-09 |
| SC-06 | Transferability not argued; "megacity" generalisation | R W3 | · | · | · | SINGLE | m9 | R-10 |
| SC-07 | "Produces" language; phenotype premise | · | · | · | R W3 | SINGLE | M7, premise | R-67 |
| SC-08 | "Marginal changes … did not move crime" overgeneralises | R mi | · | · | · | SINGLE | M7 | R-34 |
| SC-09 | Benchmark paragraph overloaded | R W1 | · | · | · | SINGLE | m6 | R-02 |
| SC-10 | LLM decision layer off-story | R W1 | R W14 | · | · | CORR-2 | m5 | R-03, R-75 |
| SC-11 | Event-study placement | R W1 | R W12, W14 | · | · | CORR-2 (DA direction, D-5) | M7 | R-04 |
| SC-12 | Fig. 3f uncited, no Methods | R W1, W11 | R W14 | · | · | CORR-2 | – | R-76 |
| SC-13 | Fig. 5f uncited | R W1, W11 | · | · | · | SINGLE | – | R-77 |
| SC-14 | Fig. 2c,e uncited; domains unused | R W1, W11 | R W14 | · | · | CORR-2 | m4 | R-78 |
| SC-15 | Fig. 1a advertises failed ligand–receptor mapping | R W1 | · | · | R W9 | CORR-2 | – | R-79 |
| SC-16 | Fourth Results subsection packs four results | R W1 | · | · | · | SINGLE | – | R-05 |
| SC-17 | NMF programs add no inference | · | R W14 | · | R W10 | CORR-2 | m4 | R-89, R-129 |
| SC-18 | Marginal panels (Fig. 2a, 2d, 4e) | · | R W14, mi | · | · | SINGLE | m4 | R-90 |
| SC-19 | Displayed analyses without Methods; core replication gaps | · | R W14, W15 | · | · | SINGLE | – | R-48 |
| SC-20 | Knox analysis: cut vs bring into main text | · | R W14 (cut) | D W6 (main text) | · | **SPLIT** (D-3) | – | R-49 |
| SC-21 | Analogy "additions" include classical methods | R W2 | · | R W2 | R W1 | **C3** | M10 | R-06, R-80 |
| SC-22 | Criminological precursors not engaged | R W2 | · | R W2 | R W1, dc | **C3** | M10, alt8 | R-07 |
| SC-23 | Omics known-fraction lineage; Intro direction of deconvolution | · | · | · | R W1, W8 | SINGLE | – | R-65 |
| SC-24 | Attribution comparator from same family; no head-to-head | · | · | · | R W1(b), Q1 | SINGLE | M10, alt8 | R-124 |
| SC-25 | Gap statement misdescribes micro-place measurement | · | · | R W1 | C W1 | CORR-2 | – | R-53 |
| SC-26 | Prior biological borrowing (Chicago School) omitted | · | · | R W18 | · | SINGLE | – | R-63 |
| SC-27 | Citation descriptions (refs 11–14, 27, 32, 46) | · | · | R W10, W11, mi | · | SINGLE | – | R-58 |
| SC-28 | São Paulo crime geography and criminal governance absent | · | · | R W15 | C dc | CORR-2 | alt7 | R-61 |
| SC-29 | ED Fig. 2 label errors | · | · | · | R mi | SINGLE | – | R-93 |
| SC-30 | Kitagawa cited, composition component not reported | · | R dc | · | · | SINGLE | – | R-52 |
| SC-31 | Point validation presented as independent | R W15 | R W1 | · | D S3 | **SPLIT** (D-1) | M5 | R-25, R-95 |
| SC-32 | "Pedestrian counts" are survey estimates | R W15 | · | · | · | SINGLE | – | R-26 |
| SC-33 | Validation scope and uncertainty | · | R W1 | · | · | SINGLE | m2 | R-36, R-96 |
| SC-34 | Constant city-wide class rate untested | · | R W3 | R W2 | R W1(c) | **C3** | M1 | R-100 |
| SC-35 | Recovery accuracy, collinearity, zero boundary | · | R W3, W8, Q3 | · | · | SINGLE | – | R-99, R-101 |
| SC-36 | Assumptions unstated; "fitted jointly" undefined | · | R W3, W15 | · | · | SINGLE | – | R-39 |
| SC-37 | D² baseline ignores tract size | · | R W19 | · | · | SINGLE | m3 | R-116 |
| SC-38 | Reconciliation builds persistence, damps variance | · | R W2, Q2 | · | · | SINGLE | M2 | R-37, R-97 |
| SC-39 | Low-geocoding signatures are projections | · | R W2 | · | · | SINGLE | m2, alt3 | R-38 |
| SC-40 | Reconciled share not reported | · | R W2, Q2 | C W1 | · | CORR-2 | M2 | R-98 |
| SC-41 | Default or duplicate geocodes; geocoded share by income and year | · | R W5 | R W7, Q3 | · | CORR-2 | – | R-105 |
| SC-42 | Place-defined offences inflate signatures | · | R W18 | R W9, Q7 | · | CORR-2 | – | R-50, R-115 |
| SC-43 | Enrichment multiplicity | · | R W17 | · | · | SINGLE | – | R-114 |
| SC-44 | Signatures' sensitivity to typing resolution | · | · | · | · | DA-only | m10 | R-131 |
| SC-45 | Fig. 2f ARI refers to pre-refinement resolution | R W14 | · | · | · | SINGLE | – | R-24 |
| SC-46 | "Signature matrix" misnomer | · | · | · | R W7 | SINGLE | – | R-70, R-128 |
| SC-47 | Generator/attractor test not interpreted | · | · | R W12 | · | SINGLE | – | R-59 |
| SC-48 | Robbery clock (abstract lead) exploratory | R W6, Q4 | R W8, Q4 | · | · | CORR-2 | m1 | R-14 |
| SC-49 | 41% and hourly profile lack intervals and model-free check | · | R W8 | · | · | SINGLE | – | R-109 |
| SC-50 | Guardianship inferred, not measured | R W6 | R W13 | R W3, mi | · | **C3** | M6 | R-16 |
| SC-51 | Rival explanations for dawn robbery unaddressed | · | R W13 | R W3 | · | CORR-2 | M6, alt6 | R-47 |
| SC-52 | Tests of rival explanations | · | · | R W3, Q5 | · | SINGLE | M6 | R-118 |
| SC-53 | Crowd normalisation is a weak check | · | R W13 | · | · | SINGLE | – | R-46 |
| SC-54 | Night-time denominators near zero, no intervals | · | R W13, W8 | R W3, Q6, mi | · | CORR-2 | M6 | R-92, R-113 |
| SC-55 | Clock permutation null anti-conservative; P floor | · | R W7, mi | · | · | SINGLE | – | R-42, R-107 |
| SC-56 | "Clock" implies an oscillator | · | · | · | R W6 | SINGLE | – | R-69, R-127 |
| SC-57 | Dawn recommendation stated beyond evidence | R W6 | R W13 | R W8 | D S4 | **SPLIT** (D-4) | M6 | R-15 |
| SC-58 | "Memory" implies state dependence | · | R W9 | R W5, mi | R W4 | **C3** | – | R-43 |
| SC-59 | Variance decomposition not unique | · | R W9 | · | · | SINGLE | C1, M1 | R-110 |
| SC-60 | Residual may be missing composition | · | · | R W5 | R W4, Q4 | CORR-2 | C1, M1 | R-120 |
| SC-61 | Theory anchor for persistence; ref. 36 | · | · | R W5 | R W4 | CORR-2 | – | R-55 |
| SC-62 | Dynamic test if "memory" kept | · | R W9 | R W5 | R W4 | **C3** (conditional) | – | R-111 |
| SC-63 | Transitions vs classifier error; exclusions | · | R W20, mi | · | · | SINGLE | – | R-51, R-117 |
| SC-64 | Decline place reading may restate theft/robbery mix | · | · | R W4, Q1, mi | · | SINGLE | M4 | R-119 |
| SC-65 | Decline: crime-drop literature, drivers, causal reading | · | · | R W4, Q4 | · | SINGLE | M4, alt5 | R-54 |
| SC-66 | "Receded to its niches"; "niche" in two senses | R W8 | · | R W4, mi | R W9 | **C3** | – | R-20 |
| SC-67 | Decline vs noise tension | · | · | · | · | DA-only | M4 | R-74, R-132 |
| SC-68 | Reclassification and reporting channels 2022–2025 | · | · | R Q4 | · | SINGLE | M4 | R-123 |
| SC-69 | Event study: MDE read as exclusion; underspecified | · | R W12 | · | · | SINGLE | M7 | R-04, R-112 |
| SC-70 | Non-rejection read as Poisson "noise" (96%) | R W17 | R W4 | R W6 | R W2 | **C4** | M3 | R-28 |
| SC-71 | Power or MDE of dispersion test | · (defers, W17) | R W4 | R W6 | R W2, Q3 | **C3** | M3 | R-103 |
| SC-72 | Latent month-to-month variation (hierarchical) | · | R W4 | · | R W2 | CORR-2 | M3 | R-102 |
| SC-73 | Dispersion-test specification | · | R W4, W15 | · | · | SINGLE | – | R-40 |
| SC-74 | Noise claim beyond offence and scale; near-repeat | · | · | R W6 | · | SINGLE | M3 | R-56 |
| SC-75 | "Intrinsic noise" analogy wrong concept | · | · | · | R W2 | SINGLE | M3 | R-66 |
| SC-76 | "Close to its limit" contradicted within tracts | · | R W6 | · | R W2 | CORR-2 | M3 | R-41 |
| SC-77 | Ref. 41 mobility predictability is a different quantity | R mi | R W6 | R W14 | R W2 | **C4** | M3 | R-35 |
| SC-78 | Ceiling terminology | R W13 | R W6, W16, mi | · | · | CORR-2 | – | R-23, R-87 |
| SC-79 | Ceilings lack intervals; seasonal vs residual | · | R W6 | · | · | SINGLE | – | R-106 |
| SC-80 | Hub concentration may be a scale effect | · | R W5 | · | D W2 | **SPLIT** (D-2) | – | R-104 |
| SC-81 | Forecast comparator ("tissue map" vs history) | R W4 | · | R W17 | · | CORR-2 | M11 | R-11 |
| SC-82 | Data scope; vault exposure in benchmark | R W7, Q1 | R W11, Q1 | · | · | CORR-2 | – | R-17, R-94 |
| SC-83 | 2025 not a clean hold-out | · | R W11 | · | · | SINGLE | – | R-45 |
| SC-84 | Fig. 6e vs text on lethal violence | R W10 | R W16, W14 | · | · | CORR-2 | – | R-84 |
| SC-85 | Equity argument direction; static map flags alike | · | · | · | · | DA-only | m8 | R-73, R-130 |
| SC-86 | Feedback-loop citation mechanism | · | · | R W13 | · | SINGLE | – | R-60 |
| SC-87 | Recorded-crime bias not used to qualify results | · | · | R W7 | R W5, mi | CORR-2 | M8 | R-57 |
| SC-88 | Reporting-gradient sensitivity bound | · | · | · | R W5 | SINGLE | M8 | R-126 |
| SC-89 | Robbery-only income audit | · | · | R W7 | · | SINGLE | – | R-121 |
| SC-90 | Reporting-robust phenotype check | · | · | · | · | DA-only | M8 | R-133 |
| SC-91 | Territorial stigma; ethics beyond privacy; uses | · | · | · | R W3, Q5, dc | SINGLE | stakeholders, m11 | R-68 |
| SC-92 | Favela constructed exposure sensitivity | · | · | · | R W3(c) | SINGLE | m11 | R-125 |
| SC-93 | Lethal-violence components | · | · | R Q2 | R W12, Q2 | CORR-2 | – | R-64, R-122 |
| SC-94 | "More precisely than hot spots"; evidence not weighed | R W16 | · | R W8 | · | CORR-2 | M7 | R-27 |
| SC-95 | Policy addressed mainly to police | · | · | · | R W11, dc | SINGLE | stakeholders | R-71 |
| SC-96 | Unbounded DA alternatives (high-rise frontage; hub policing) | · | · | · | · | DA-only | alt4, alt5 | R-72 |
| SC-97 | Pseudo-vault reported as support | R W5, mi | R W10 | · | · | CORR-2 | m7 | R-12, R-75 |
| SC-98 | Pseudo-vault point-validation ρ 0.63 undiscussed | · | R W10 | · | · | SINGLE | – | R-44 |
| SC-99 | Internal codes (A11, Laya-FT, FCU) | R W5, mi | · | · | R mi | CORR-2 | – | R-13, R-81 |
| SC-100 | Confirmatory criteria weak; OSF; block version | · | R W10, W7, Q4 | · | · | SINGLE | – | R-108 |
| SC-101 | Gaps in claim numbering | R W18, Q2 | · | · | · | SINGLE | – | R-29 |
| SC-102 | "Low-income" relabel of a building-standard class | R W8 | · | · | · | SINGLE | – | R-18 |
| SC-103 | Naming drift; no glossary | R W8 | · | · | · | SINGLE | – | R-19, R-82 |
| SC-104 | Undefined terms | R W8 | · | · | R W9, mi | CORR-2 | – | R-21 |
| SC-105 | Transcriptomic jargon on axes | R W8 | · | · | · | SINGLE | – | R-82 |
| SC-106 | "Thefts" labels vs phone crime | R W9 | R W16 | · | · | CORR-2 | – | R-83 |
| SC-107 | Numbers untraceable | R W19 | R W16, W5 | · | · | CORR-2 | m12 | R-30 |
| SC-108 | ED Fig. 1 vs Methods; Portuguese labels | · | R W16, mi | · | · | SINGLE | – | R-91 |
| SC-109 | Uncited panels; ED and Fig. 6 order | R W11 | · | · | · | SINGLE | – | R-22, R-85 |
| SC-110 | Palette reversal | R W12 | · | · | · | SINGLE | – | R-86 |
| SC-111 | Legend and annotation gaps | R mi | · | · | · | SINGLE | – | R-88 |
| SC-112 | Reference style and language | R mi | · | · | · | SINGLE | – | R-33 |
| SC-113 | "Places" for areal units; theft vs robbery | · | · | R W16, mi | · | SINGLE | – | R-62 |

**Totals over 113 sub-claims:**

| Disposition | Count |
|---|---|
| C4 | 2 |
| C3 | 8 |
| SPLIT | 4 |
| CORR-2 | 33 |
| SINGLE | 61 (23 of them with DA corroboration) |
| DA-only | 5 |

### 3.4 Consensus issues (raised by two or more seats)

"Seats" counts all five seats; the label counts only the four non-DA seats.

#### CONSENSUS-4 (4/4 non-DA)

1. **SC-70. Non-rejection of a low-power test is read as "month-to-month crime is noise" (96%).** Raised by EIC-W17, R1-W4, R2-W6 and R3-W2, plus DA-M3: **5/5 seats**. → R-28, with analyses R-102 and R-103.
2. **SC-77. Ref. 41 (an entropy bound on individual mobility) does not map onto a Poisson ceiling.** The phrase "close to its limit of predictability" should be dropped or explicitly qualified. Raised by EIC minor issues (Language), R1-W6, R2-W14 and R3-W2, plus DA-M3: **5/5**. → R-35.

#### CONSENSUS-3 (3/4 non-DA; silent seat named)

1. **SC-21. Analogy "additions" include classical methods** (Kitagawa; Poisson ecological regression). Raised by EIC-W2, R2-W2 and R3-W1; R1 silent; plus DA-M10: **4/5**. → R-06, R-80.
2. **SC-22. Closest criminological precursors not engaged** (ecological regression, risky facilities, Bernasco & Block, risk terrain modelling). Raised by EIC-W2, R2-W2, R3-W1 and R3 Detailed Comments; R1 silent; plus DA-M10 and DA alt. 8: **4/5**. → R-07.
3. **SC-34. One city-wide rate per class is assumed and untested.** Raised by R1-W3, R2-W2 and R3-W1(c); EIC silent; plus DA-M1: **4/5**. → R-100.
4. **SC-50. Guardianship is inferred, not measured** ("rather than the volume of targets"). Raised by EIC-W6, R1-W13 and R2-W3 (with R2 minor issues); R3 silent (its S4 concerns the recommendation, see D-4); plus DA-M6: **4/5**. → R-16.
5. **SC-58. "Memory" implies state dependence the decomposition cannot identify.** Raised by R1-W9, R2-W5 (with R2 minor issues) and R3-W4; EIC silent: **3/5**. → R-43.
6. **SC-62. A dynamic test is needed if "memory" is kept.** Raised by R1-W9, R2-W5 and R3-W4; EIC silent: **3/5**. → R-111 (conditional).
7. **SC-66. "Crime receded to its niches"; "niche" is used in two senses.** Raised by EIC-W8, R2-W4 (with R2 minor issues) and R3-W9; R1 silent: **3/5**. → R-20.
8. **SC-71. The dispersion test needs a power or minimum-detectable-effect analysis.** Raised by R1-W4, R2-W6 and R3-W2 (with R3-Q3); EIC silent (EIC-W17 defers power to the methodology seat); plus DA-M3: **4/5**. → R-103.

#### Corroborated (2/4 non-DA)

| SC | Issue | Non-DA seats | DA | Seats | Items |
|---|---|---|---|---|---|
| SC-01 | Thesis wording outruns estimates | EIC-W20, R1-W9 | C1 | 3/5 | R-32 |
| SC-02 | 18% tissue share; covariance term | EIC-W20, R1-W9 | C1 | 3/5 | R-31 |
| SC-03 | One spine | EIC-W1, R3-W1(d) | M9 | 3/5 | R-01 |
| SC-10 | LLM decision layer | EIC-W1, R1-W14 | m5 | 3/5 | R-03, R-75 |
| SC-11 | Event-study placement | EIC-W1, R1-W12/W14 | M7 (direction) | 3/5 | R-04 |
| SC-12 | Fig. 3f | EIC-W1/W11, R1-W14 | – | 2/5 | R-76 |
| SC-14 | Fig. 2c,e | EIC-W1/W11, R1-W14 | m4 | 3/5 | R-78 |
| SC-15 | Fig. 1a ligand–receptor row | EIC-W1, R3-W9 | – | 2/5 | R-79 |
| SC-17 | NMF programs | R1-W14, R3-W10 | m4 | 3/5 | R-89 |
| SC-25 | Gap statement | R2-W1, R3-W1 | – | 2/5 | R-53 |
| SC-28 | São Paulo literature, criminal governance | R2-W15, R3 dc | alt7 | 3/5 | R-61 |
| SC-40 | Reconciled share table | R1-W2, R2-W1 | M2 | 3/5 | R-98 |
| SC-41 | Geocode defaults; geocoded share by income | R1-W5, R2-W7/Q3 | – | 2/5 | R-105 |
| SC-42 | Place-defined offences | R1-W18, R2-W9 | – | 2/5 | R-50, R-115 |
| SC-48 | Robbery clock as abstract lead | EIC-W6, R1-W8 | m1 | 3/5 | R-14 |
| SC-51 | Rival explanations for dawn robbery | R1-W13, R2-W3 | M6 | 3/5 | R-47 |
| SC-54 | Night-time denominators | R1-W13, R2-W3 | M6 | 3/5 | R-92, R-113 |
| SC-60 | Residual as missing composition | R2-W5, R3-W4 | C1, M1 | 4/5 | R-120 |
| SC-61 | Heterogeneity vs state dependence | R2-W5, R3-W4 | – | 2/5 | R-55 |
| SC-72 | Hierarchical latent variation | R1-W4, R3-W2 | M3 | 3/5 | R-102 |
| SC-76 | "Close to its limit" | R1-W6, R3-W2 | M3 | 3/5 | R-41 |
| SC-78 | Ceiling terminology | EIC-W13, R1-W6 | – | 2/5 | R-23, R-87 |
| SC-81 | Forecast comparator | EIC-W4, R2-W17 | M11 | 3/5 | R-11 |
| SC-82 | Data scope / vault exposure | EIC-W7, R1-W11 | – | 2/5 | R-17, R-94 |
| SC-84 | Fig. 6e | EIC-W10, R1-W16 | – | 2/5 | R-84 |
| SC-87 | Recorded-crime bias qualification | R2-W7, R3-W5 | M8 | 3/5 | R-57 |
| SC-93 | Lethal-violence components | R2-Q2, R3-W12 | – | 2/5 | R-64, R-122 |
| SC-94 | Hot-spot comparison | EIC-W16, R2-W8 | M7 | 3/5 | R-27 |
| SC-97 | Pseudo-vault framing | EIC-W5, R1-W10 | m7 | 3/5 | R-12, R-75 |
| SC-99 | Internal codes | EIC-W5, R3 mi | – | 2/5 | R-13, R-81 |
| SC-104 | Undefined terms | EIC-W8, R3-W9 | – | 2/5 | R-21 |
| SC-106 | "Thefts" labels | EIC-W9, R1-W16 | – | 2/5 | R-83 |
| SC-107 | Numbers untraceable | EIC-W19, R1-W16 | m12 | 3/5 | R-30 |

#### Two-seat findings: one non-DA seat plus the DA (SINGLE + DA)

| SC | Issue | Seats | Items |
|---|---|---|---|
| SC-04 | Title | EIC-W3 + DA-C1, M9 | R-08 |
| SC-06 | Transferability; "megacity" | EIC-W3 + DA-m9 | R-10 |
| SC-07 | "Produces" language; premise | R3-W3 + DA-M7, premise | R-67 |
| SC-08 | "Marginal changes" | EIC minor issues + DA-M7 | R-34 |
| SC-09 | Benchmark paragraph | EIC-W1 + DA-m6 | R-02 |
| SC-18 | Marginal panels | R1-W14 + DA-m4 | R-90 |
| SC-24 | Attribution head-to-head | R3-W1(b) + DA-M10 | R-124 |
| SC-33 | Validation scope | R1-W1 + DA-m2 | R-36, R-96 |
| SC-37 | D² baseline | R1-W19 + DA-m3 | R-116 |
| SC-38 | Reconciliation artefact | R1-W2 + DA-M2 | R-37, R-97 |
| SC-39 | Low-geocoding signatures | R1-W2 + DA-m2 | R-38 |
| SC-52 | Dawn-robbery tests | R2-W3 + DA-M6 | R-118 |
| SC-59 | Variance components; cross-term | R1-W9 + DA-C1, M1 | R-110 |
| SC-64 | Decline by offence | R2-W4 + DA-M4 | R-119 |
| SC-65 | Decline interpretation | R2-W4 + DA-M4 | R-54 |
| SC-68 | Reclassification; reporting channels | R2-Q4 + DA-M4 | R-123 |
| SC-69 | Event-study reporting | R1-W12 + DA-M7 | R-112 |
| SC-74 | Noise scope | R2-W6 + DA-M3 | R-56 |
| SC-75 | "Intrinsic noise" | R3-W2 + DA-M3 | R-66 |
| SC-88 | Reporting-gradient bound | R3-W5 + DA-M8 | R-126 |
| SC-91 | Stigma and ethics | R3-W3 + DA stakeholders, m11 | R-68 |
| SC-92 | Favela exposure | R3-W3 + DA-m11 | R-125 |
| SC-95 | Non-police policy | R3-W11 + DA stakeholders | R-71 |

### 3.5 Points of disagreement and arbitration

**D-1. SC-31: is the point validation independent of the fitted data?** (Existence disagreement; SPLIT 2 agree / 1 disputed)
- **R1-W1 and EIC-W15**: the geocoded points are the events that make up most of the fitted counts (100,347 of 121,434), and both procedures split counts by frontage. The check is cross-scale consistency, not validation on unused data. DA-M5 agrees.
- **R3 (S3 and Summary)**: "Each inference is checked against independent data"; the check transfers omics orthogonal validation.
- **R2-S4**: praises the existence of the check but does not address independence (silent).
- **Resolution: R1 upheld.**
- **Rationale**:
  - Evidence: Methods §Units and reconciliation states that geocoded events are assigned to the tract containing them and that "Attribution uses the reconciled counts".
  - Expertise: validation design is the methodology seat's remit.
  - R3's own W5 says point validation "uses the same police records".
  - R3's strength (the validation habit) stands as a design-culture merit, but the wording must change (R-25) and a held-out validation is required (R-95).

**D-2. SC-80: does the concentration of extra-Poisson variance in hubs show distinct dynamics?** (Existence; SPLIT 1/1)
- **R1-W5**: excess variance scales with μ² under constant relative overdispersion, so 88% in the top 1% is expected from scale alone. Hub geocoding defaults may add spikes.
- **R3-W2**: "Keep the strong, well-supported result: extra-Poisson variance is concentrated in hubs."
- **Resolution: R1 upheld, conditionally.**
- **Rationale**: R1 gives an analytical argument and a concrete test; R3 asserts without analysis and, in the same W2, defers formal power questions to the methodology seat. The hub claim (section heading, abstract qualifier) stays only if 88% exceeds the common-θ expectation (R-104). R3's recommendation to direct forecasting research to hubs is then conditional on that test.

**D-3. SC-20: Knox near-repeat analysis (ED Fig. 5a).** (Direction; SPLIT)
- **R1-W14**: cut it, together with the other Methods-less ED analyses.
- **R2-W6**: bring it into the main text, because near-repeat dynamics bear on the "noise" claim.
- **Resolution: author's choice between two paths, each with both constraints.** Either (i) bring Knox into the main text with full Methods, or (ii) cut it and explicitly restrict the noise claim to phone crime at tract-month scale, with the near-repeat literature acknowledged (R-56).
- **Rationale**: the seats address different criteria. Domain expertise (R2) decides that near-repeat dynamics must be addressed; methodology (R1) decides that any displayed analysis needs Methods. Both constraints can be met on either path (R-49).

**D-4. SC-57: the 04:00–06:00 guardianship recommendation.** (Perspective or existence; SPLIT 3 / 1)
- **EIC-W6, R1-W13 and R2-W8**: the recommendation rests on an exploratory clock (P = 0.07 in 2025) and an unmeasured mechanism. "Rather than extending evening patrols" rests on no reported analysis. DA-M6 agrees.
- **R3-S4**: commends the recommendation as a testable, non-police measure that serves residents of the periphery.
- **Resolution: compatible synthesis.**
  - Keep the non-police orientation (R3-S4, R3-W11), presented as hypotheses to test; the manuscript's own wording is "suggests testing".
  - Drop the evening-patrol comparison and the assertion "This last pattern is a problem of guardianship" (R-15).
- **Rationale**: evidence first, since no analysis compares patrol timing; domain expertise (R2) governs prevention evidence.

**D-5. SC-11: event-study placement** (direction; the DA is outside the count but recorded for visibility)
- **EIC-W1 and R1-W12/W14**: move it to Extended Data, with one Discussion sentence and full Methods.
- **DA-M7**: it is "the strongest test of the thesis, but it is presented as an aside".
- **Resolution: author autonomy.** DA-M7 itself offers two paths. Either (i) relocate the event study and confine the causal and targeting language to association, or (ii) keep it in the main text as an explicit test of the thesis, stating the effect the signature matrix predicts.
- **Both paths require** R1-W12's corrections: interval-based exclusion statements, the estimator, the outcome and the clustering (R-04, R-112).

**Apparent disagreements judged compatible** (no arbitration needed):
- **Benchmark**: EIC-W1 ("reduce to two sentences") and R1 Detailed Comments ("Keep and fix … the noise ceiling with the benchmark") are compatible. A reduced benchmark tied to the ceiling satisfies both, and DA-m6 concurs.
- **Equity result**: EIC-W1 ("Keep the equity sentence") and R1-W14 ("keep the fairness result as one defined sentence") agree.
- **ED Fig. 2 audit**: EIC-S1, R3-S1 and the DA praise it; R1-W14 asks for explicit verdict rules and Methods. These are compatible.
- **Weekend ratios**: R1-W14 calls them marginal; R2-W3 uses the 0.4 ratio as evidence. Keep them if used (R-90).
- **Decline**: R1 Detailed Comments ("sound as a rates-with-fixed-composition comparison") speaks to the computation, while R2-W4 and DA-M4 speak to the interpretation. These are different sub-claims.
- **"Metaphor vs instrument" sentence**: EIC-S8 commends its clarity, while R2-W18 notes a historical omission. Clarity and completeness are compatible.
- **Feedback loop**: R3-S5 commends citing it; R2-W13 corrects the mechanism and DA-m8 the direction. Keep the concern and fix both.
- **Dawn-robbery pattern**: R2-S6 calls it substantively important, while EIC-W6 and R1-W8 note its exploratory status. Importance and evidentiary status are compatible.
- **Subsection heading**: EIC-W1 suggests "Places remember", which conflicts with the CONSENSUS-3 rename of "memory" (SC-58). Resolved: the heading follows R-43.

### 3.6 Severity register (transported per source; not disputes under the §3.2 rule)

| SC | Transported severities | Basis of difference | Treatment |
|---|---|---|---|
| SC-01, SC-02 | EIC-W20 minor; R1-W9 major; DA-C1 critical | Different parent scope | Item carries all three; C1 validated |
| SC-10, SC-12, SC-14 | EIC-W1 major (bundle); R1-W14 minor | EIC bundle inheritance | Per-source listing |
| SC-11 | EIC-W1 major; R1-W12 minor; DA-M7 major | Bundle inheritance | Obligation from R1-W12, which is on R1's D1 not-met list |
| SC-15, SC-104 | EIC-W1 or W8 major; R3-W9 minor | Bundle inheritance | Per-source listing |
| SC-31 | EIC-W15 minor (wording only); R1-W1 major; DA-M5 major | Genuine difference | Methodology expertise → major retained |
| SC-50, SC-51, SC-54, SC-57 | R1-W13 minor; EIC-W6, R2-W3 and R2-W8 major | Genuine difference | Guardianship is a domain mechanism → R2's major retained |
| SC-66 | EIC-W8 and R2-W4 major; R3-W9 minor | Bundle inheritance | Per-source listing |
| SC-70 | EIC-W17 minor; R1-W4, R2-W6, R3-W2 major | EIC defers power | Methodology and domain → major |
| SC-77, SC-78 | EIC minor issues and R2-W14 minor; R1-W6 and R3-W2 major | Bundle inheritance | Per-source listing |
| SC-81 | R2-W17 minor; EIC-W4 and DA-M11 major | Genuine difference | Abstract's closing claim (venue and coherence seats) → major |
| SC-94 | EIC-W16 minor; R2-W8 major | Genuine difference | Prevention evidence is the domain seat's remit → major |
| SC-97, SC-99 | EIC-W5 major; R1-W10 major; DA-m7 minor; R3 minor issues | Bundle inheritance | Per-source listing |

### 3.7 DA findings without non-DA corroboration (retained, evaluated on manuscript evidence)

- **SC-67 (DA-M4)**: the decline is class-differentiated in the fabric the paper calls noise. The manuscript reports both the decline (Results §Stable tissue ¶2) and noise elsewhere (§Month-to-month ¶1). Retained, should_fix (R-74, R-132).
- **SC-85 (DA-m8)**: the ensemble captures 53% and the historical mean 52% (Results §Month-to-month ¶2), so the static map flags almost identically. The observed skew toward richer tracts runs opposite to the feedback concern cited in Discussion ¶3. Retained, consider (R-73, R-130).
- **SC-90 (DA-M8)**: a reporting-robust phenotype check. Retained, should_fix (R-133). R2-W7's robbery-only request (R-121) is related.
- **SC-44 (DA-m10)**: typing-resolution sensitivity. Retained, consider (R-131).
- **SC-96 (DA alternatives 4 and 5)**: high-rise frontage, and hub saturation policing or reporting convenience. These are named in DA "Ignored Alternative Explanations" without a fix line. The remedy is taken from the DA's own D3 standard (rivals "named and tested or explicitly bounded"). Retained, consider (R-72).

---
## 4. Revision Roadmap (immutable, non-ranking)

### 4.0 Conventions

- **Order.** Items are grouped into the three requested categories:
  - (a) text: rewriting, reframing or cutting prose, including legends and Methods;
  - (b) figure artwork: panels, axes, keys, palettes and panel order;
  - (c) new analyses.

  Within each category, items follow the schema's deterministic source order. An item's lowest source reference decides its position: seats in the fixed order EIC, R1, R2, R3, DA, then the finding's position in that card's document order (weaknesses, then detailed comments, questions and minor-issue lists; for the DA, document order). Severity and obligation never enter the order. IDs are stable transport references, not priorities.
- **Obligation class** (an editorial gate, not a work rank):
  - **must_fix**: the item resolves a finding that its seat names as driving a `block` on a mandatory dimension, or the validated C1. The block-driving findings are:
    - R1-W1–W9 and W12 (D1 and D3: R1's not-met list and its decision-bearing rows);
    - R2-W1–W8 (D2: R2's stated drivers and the prevention clause);
    - DA C1, M1, M2, M3, M6, M7, M9 (D3: rows the DA marks decision-bearing).
  - **should_fix**: otherwise, the item resolves a Major-severity finding (EIC-W1–W8, R1-W10/W11, R3-W1–W5, DA-M4/M5/M8/M10/M11), or a minor finding that its seat's criterion table marks decision-bearing (R2-W9, W12, W15, W18).
  - **consider**: everything else, including remedies a seat offers as optional.
- **Minimum remedy** is the least-cost option the source seat itself offers; alternatives offered by seats are noted. No remedy is added by the synthesizer.
- **Source codes**:
  - `W` weakness; `Q` question; `mi` minor-issue list; `dc` detailed comments.
  - DA `C`/`M`/`m` issue rows; DA `alt` ignored-alternative entries.
  - Severity/confidence is shown as `(maj/4)`; `†` letter-fallback severity; `‡` report-level confidence; `Q` question (no severity).
- **Cost scope and consequence codes** use the closed enums of `revision-roadmap/1.0`. Figure artwork uses `other:figure_artwork`.
- **Acceptance criterion for every item.** The minimum remedy is present in the revised manuscript. For (c) items, the analysis is reported with its result and the dependent text is revised to match. The source seat or seats judge the finding resolved at re-review.

### 4.a Items fixable by rewriting, reframing or cutting text

| ID | SC | Problem → minimum remedy | Sources (sev/conf) | Consensus | Obligation | Location (anchor) | Cost · consequence |
|---|---|---|---|---|---|---|---|
| R-01 | SC-03 | Three stories (São Paulo thesis, analogy audit, forecasting benchmark); title, abstract end, Discussion ¶1 and the final sentence state different claims. **Min:** choose one spine: if the instrument, retitle and lead with what it reveals; if the substantive thesis, move the analogy audit and cross-domain benchmark to ED. Align title, last abstract sentence, Discussion ¶1 and final sentence on one claim (DA-M9). Option (R3): one instrument along what, when and how-it-changes, plus one bound. | EIC-W1 (maj/4); EIC-Q3 (Q); EIC-dc (min†/4‡); R3-W1 (maj/4); R3-dc (min†/4‡); DA-M9 (maj/5) | CORR-2 +DA | must_fix | text: Discussion ¶4 "not as a description of what cities are"; Discussion ¶5 "The central contrast…" | section · claim_scope_unsupported (manuscript) |
| R-02 | SC-09 | Benchmark paragraph reads as a second paper. **Min:** reduce it to the ceiling, the best-model gain and the 5%-area capture; keep the equity sentence; move the rest to ED Figs 1 and 8. DA: keep only comparisons bearing on the ceiling (best model, NB GLM, historical mean, oracle). | EIC-W1 (maj/4); DA-m6 (min/4) | SINGLE +DA | should_fix | text: Results §Month-to-month ¶2 "we benchmarked 12 methods from seismology…" | section · editorial_conformance_unmet (section) |
| R-03 | SC-10 | Language-model decision layer is off-story. **Min:** delete it from this paper, or move it to Supplementary Information. Fig. 6g row H2 is handled in R-75. | EIC-W1 (maj/4); R1-W14 (min/4); DA-m5 (min/5) | CORR-2 +DA | should_fix | text: Methods §Forecasting benchmark "A pre-specified comparison of a fine-tuned language-model decision layer…" | sentence · editorial_conformance_unmet (section) |
| R-04 | SC-11, SC-69 | The MDE is read as an exclusion bound; the estimator, outcome, repeated events and clustering are unspecified; the Discussion over-reads the null. **Min:** state exclusion from each variant's 95% interval (computed in R-112), not from the MDE; specify the estimator relative to ref. 38, the outcome, repeated events and bootstrap clustering; soften "not a lever within a year". Then, per D-5, either relocate to ED with one Discussion sentence (EIC, R1), or keep it as an explicit test of the thesis (DA-M7). | EIC-W1 (maj/4); R1-W12 (min/5); R1-W14 (min/4); DA-M7 (maj/4) | CORR-2; DA direction (D-5) | must_fix | text: Results §Stable tissue ¶2 "effects larger than 4–11% of the baseline rate are excluded"; Discussion ¶2 "not a lever within a year" | section · claim_scope_unsupported (claim) |
| R-05 | SC-16 | The fourth Results subsection packs four results under a three-part heading. **Min:** split it into two subsections. The heading wording follows R-43, not "Places remember". | EIC-W1 (maj/4) | SINGLE | should_fix | text: heading "Stable tissue, places that remember and rates that move" | section · editorial_conformance_unmet (section) |
| R-06 | SC-21 | The analogy's listed "additions" include classical methods. **Min:** credit the non-omics antecedents (Kitagawa decomposition; Poisson ecological regression with exposures; time-specific crime-pattern work, refs 14–16) and remove them from the list; state precisely what only the omics workflow made possible. Candidates offered: systematic signature, program and clock analyses across all classes and crime types with an audit (EIC); use of non-randomly suppressed events, joint multi-phenotype estimation under non-negativity, and the validation culture (R3). | EIC-W2 (maj/4); R2-W2 (maj/4); R3-W1 (maj/4); DA-M10 (maj/4) | C3 +DA | must_fix | text: Discussion ¶4 "It adds attribution within the spot, phenotype signatures, a clock per class of cell and the decomposition of change." | section · claim_scope_unsupported (claim) |
| R-07 | SC-22 | The closest criminological precursors are not engaged. **Min:** add two or three sentences or a paragraph positioning attribution against ecological regression (Goodman; King, both [UNVERIFIED] per R3) and against risky facilities (Eck, Clarke & Guerette 2007), generators and attractors (Bernasco & Block 2011), risk terrain modelling (Caplan, Kennedy & Miller 2011) and multi-land-use segment models. State what attribution adds (frontage exposure, all classes at once, point validation). Discuss the context-dependence of facility effects (ref. 12), at least as a limitation. | EIC-W2 (maj/4); R2-W2 (maj/4); R3-W1 (maj/4); R3-dc (min†/4‡); DA-M10 (maj/4); DA-alt8 (†) | C3 +DA | must_fix | text: Results §Each cell class ¶1 "This inverts spot deconvolution"; Intro ¶1 | section · claim_scope_unsupported (claim) |
| R-08 | SC-04 | The title is a metaphor that states no result. **Min:** a declarative title stating the supported finding (wording is the authors'; EIC gives an example), consistent with R-32 and R-01. | EIC-W3 (maj/4); DA-C1 (crit/5); DA-M9 (maj/5) | SINGLE +DA (DA-CRITICAL) | must_fix | text: Title "Crime as a phenotype of urban tissue" | sentence · claim_scope_unsupported (claim) |
| R-09 | SC-05 | The abstract ends on a forecasting detail, has no implication sentence, and leaves "spots" and "class of cell" undefined; its first sentence is convoluted. **Min:** end with one sentence of implication; rewrite the first sentence; define or replace the two terms. Consider mentioning the confirmatory design and the audit. | EIC-W3 (maj/4); EIC-dc (min†/4‡); EIC-W8 (maj/5) | SINGLE | should_fix | text: Abstract "mapped places mix many land uses, so which component…" | sentence · reader_traceability_reduced (section) |
| R-10 | SC-06 | Generality is treated in a single limitation sentence; "a megacity's crime" generalises from one city. **Min:** add a short Discussion paragraph on what should generalise (the ceiling, a property of counts, versus the city-specific signatures) and how to test it with public cadastres; replace the phrase with "São Paulo's recorded crime". | EIC-W3 (maj/4); DA-m9 (min/5) | SINGLE +DA | should_fix | text: Discussion ¶1 "a megacity's crime behaves like a phenotype"; ¶5 "The analysis covers one city." | section · claim_scope_unsupported (claim) |
| R-11 | SC-81 | The abstract credits the "tissue map", but the benchmark comparator is history (R² 0.25 vs 0.48; 53% vs 52%). **Min:** one formulation everywhere: "beyond a static map of where crime has been (tissue plus memory)" or "beyond the historical map". Alternative (DA): add and report a tissue-only forecast. | EIC-W4 (maj/4); R2-W17 (min/4); DA-M11 (maj/5) | CORR-2 +DA | should_fix | text: Abstract "forecasts add little beyond the tissue map outside a few hubs"; Results "This ceiling bounds what forecasting can add" | sentence · claim_scope_unsupported (claim) |
| R-12 | SC-97 | An in-sample dry run is reported as support ("All five were sustained"). **Min:** describe it strictly as a code check in Methods, with no P values in the main text; move the confirmatory paragraph out of the forecasting subsection. Fig. 6g is handled in R-75. | EIC-W5 (maj/4); EIC-mi layout (min†/4‡); R1-W10 (maj/4); DA-m7 (min/5) | CORR-2 +DA | should_fix | text: Results §Month-to-month ¶3 "All five were sustained after Holm correction in a pseudo-vault…" | section · claim_scope_unsupported (claim) |
| R-13 | SC-99 | Internal codes (A11, "sealed until A11", Laya-FT) are meaningless to readers. **Min:** replace them with plain labels in the text. Figures are handled in R-81. | EIC-W5 (maj/4); EIC-mi (min†/4‡); R3-mi (min†/4‡) | CORR-2 | should_fix | text: Results §Month-to-month ¶3 "(amendment A11)" | sentence · reader_traceability_reduced (manuscript) |
| R-14 | SC-48 | The abstract's lead clock example (phone robbery, 41%) failed in 2025 (P = 0.07) and lies outside the confirmatory family (A-R7 is theft). **Min:** lead with the phone-theft clock, or label the robbery example exploratory and report the 2025 result wherever the 41% appears; state which phenotype A-R7 tests. Alternative: add the robbery clock to the confirmatory family or the 2026 hold-out before the vault opens, if the protocol allows. | EIC-W6 (maj/4); EIC-Q4 (Q); R1-W8 (maj/4); R1-Q4 (Q); DA-m1 (min/5) | CORR-2 +DA | must_fix | text: Abstract "on low-income housing, 41% of weekday phone robberies occur between 04:00 and 06:00"; Results §Clock ¶1 "P = 0.07 in 2025" | sentence · claim_scope_unsupported (claim) |
| R-15 | SC-57 | The dawn recommendation is stated beyond the evidence. **Min (per D-4):** present lighting and staffed bus stops as hypotheses to test; drop "rather than extending evening patrols"; replace "This last pattern is a problem of guardianship" with wording matching R-16; keep the non-police orientation. | EIC-W6 (maj/4); R1-W13 (min/4); R2-W8 (maj/4); DA-M6 (maj/4); R3-S4 disputed | SPLIT (D-4) | must_fix | text: Discussion ¶2 "This last pattern is a problem of guardianship … rather than extending evening patrols." | sentence · claim_scope_unsupported (claim) |
| R-16 | SC-50 | Guardianship is inferred, not measured; pedestrians are targets as well as guardians. **Min:** reword to "is consistent with low guardianship" (EIC, R1), adding "and with offenders converging on commuters' paths to transit" (R2); call pedestrian counts "guardianship potential" (R2 minor issues). Reframe as risk per pedestrian peaking before dawn, consistent with routine activity (DA). | EIC-W6 (maj/4); R1-W13 (min/4); R2-W3 (maj/4); R2-mi (min†/4‡); DA-M6 (maj/4) | C3 +DA | must_fix | text: Results §Clock ¶2 "Dawn robbery in the periphery thus tracks the absence of guardians … rather than the volume of targets." | sentence · claim_scope_unsupported (claim) |
| R-17 | SC-82 | Data scope contradicts the design: the Introduction says 77 districts, while the benchmark bootstraps 96. **Min:** add a Methods table of the districts and years used by every analysis; correct the Introduction. If vault districts entered any analysis, document which outputs were inspected and argue why that cannot inform the atlas claims (re-run option in R-94). | EIC-W7 (maj/3); EIC-Q1 (Q); R1-W11 (maj/3); R1-Q1 (Q) | CORR-2 | should_fix | text: Intro ¶3 "all crime analyses use 77 exploration districts"; Methods "2,000 bootstrap resamples of the 96 districts" | section · reporting_requirement_unmet (section) |
| R-18 | SC-102 | A building-standard class is relabelled "low-income", importing a socioeconomic claim. **Min:** call it "low-standard housing" unless income data are used. | EIC-W8 (maj/5) | SINGLE | should_fix | text: Abstract "on low-income housing"; Discussion ¶2 "low-income peripheral fabric" | sentence · interpretive_ambiguity_remains (manuscript) |
| R-19 | SC-103 | Names of types, classes, crime types and programs drift between text and figures. **Min:** add one naming key (a glossary in Methods or ED) covering types, families, classes, crime types, programs and analogy terms, and apply it to all text. Figures are handled in R-82. | EIC-W8 (maj/5) | SINGLE | should_fix | text: Results, Discussion, Methods (e.g., "medium-standard" vs "middle standard") | section · interpretive_ambiguity_remains (manuscript) |
| R-20 | SC-66 | "Niche" is used in two senses; "Crime receded to its niches" is a biological metaphor. **Min:** replace the sentence with a descriptive statement (R2: e.g., chronic hot spots), and use "niche" in one sense or drop it. | EIC-W8 (maj/5); R2-W4 (maj/4); R2-mi (min†/4‡); R3-W9 (min/4) | C3 | must_fix | text: Results §Stable tissue ¶2 "Crime receded to its niches."; Fig. 1a legend "neighbourhood composition is the niche" | sentence · interpretive_ambiguity_remains (claim) |
| R-21 | SC-104 | "Family", "hubs", "diffuse fabric", "spots" (in the abstract), "pseudo-cells" and "interstitium" are undefined. **Min:** define each at first use (pseudo-cells as a favela area entered as one unit with constructed exposure), or drop it (interstitium). | EIC-W8 (maj/5); R3-W9 (min/4); R3-mi (min†/4‡) | CORR-2 | should_fix | text: Intro ¶3 "streets and rail stations form the interstitium" | sentence · interpretive_ambiguity_remains (manuscript) |
| R-22 | SC-109 | Panels are uncited. **Min:** cite or cut Fig. 1c,d; 2c,e; 3f; 5f; and ED Figs 1, 6, 7, 8 and 10b–d. Renumbering is in R-85. | EIC-W11 (min/5) | SINGLE | consider | absence: in-text call-outs, checked from Introduction to Methods (EIC-W11) | sentence · editorial_conformance_unmet (manuscript) |
| R-23 | SC-78 | "Maximum R² without a model" is a misnomer, and the term drifts between sections. **Min:** use one term in Results, legends and Methods: "noise ceiling, the largest R² attainable by any model under Poisson noise". Reserve "expected capture if the model were true" for the 5%-area reference. Figure keys are handled in R-87. | EIC-W13 (min/4); R1-W6 (maj/5); R1-W16 (min/5); R1-mi (min†/4‡) | CORR-2 | must_fix | text: Methods "the maximum R² attainable without a model is 1 − mean/variance" | sentence · interpretive_ambiguity_remains (claim) |
| R-24 | SC-45 | The Fig. 2f ARI belongs to the pre-refinement resolution (about 14 types), not the 12 types reported. **Min:** say so in the legend and Results, or report the ARI of the final 12 types. | EIC-W14 (min/4) | SINGLE | consider | text: Fig. 2f legend "selected resolution (12 types, ARI = 0.973)" | sentence · reader_traceability_reduced (figure) |
| R-25 | SC-31 | The point validation is presented as independent. **Min (per D-1):** reword it as an internal consistency check, "checked against a finer-scale allocation of the same geocoded events" (R1), or "finer-grained or separate data" (EIC), and align the abstract. The held-out validation is R-95. | EIC-W15 (min/3); R1-W1 (maj/5); DA-M5 (maj/5); R3-S3 disputed | SPLIT (D-1) | must_fix | text: Discussion ¶1 "checked against data that the analyses did not use: geocoded points for the attribution" | sentence · claim_scope_unsupported (claim) |
| R-26 | SC-32 | "Pedestrian counts" are survey-based estimates. **Min:** write "survey-based pedestrian estimates". | EIC-W15 (min/3) | SINGLE | consider | text: Discussion ¶1 "pedestrian counts for the crowd" | sentence · interpretive_ambiguity_remains (claim) |
| R-27 | SC-94 | The untested claim of beating hot spots reverses the usual ranking; the relevant evidence is not weighed. **Min:** drop the comparison (or "could help target prevention within hot spots", EIC); say that class rates show where to look and micro-place hot spots show where to act; present implications as hypotheses. Weigh: risky-facility concentration (Eck et al. 2007), time-targeted patrol (Koper 1995 [UNVERIFIED]), the lighting RCT (Chalfin et al. 2022), Latin American displacement (Blattman et al. [year and pages to verify]). | EIC-W16 (min/4); R2-W8 (maj/4); DA-M7 (maj/4) | CORR-2 +DA | must_fix | text: Discussion ¶2 "The results locate prevention more precisely than hot spots do." | section · claim_scope_unsupported (claim) |
| R-28 | SC-70 | Non-rejection is read as noise. **Min:** replace "is noise" (abstract, Introduction, heading, Discussion, final sentence, Fig. 6 title and 6c legend) with "in most tracts, monthly counts are too small for month-to-month variation to be distinguished from Poisson noise" (R1), "indistinguishable from Poisson noise at the observed counts" (R3) or "undetectable at tract-month resolution" (DA). Use the 86% figure or qualify the 96% (EIC). | EIC-W17 (min/3); R1-W4 (maj/5); R2-W6 (maj/4); R3-W2 (maj/4); DA-M3 (maj/4) | **C4** +DA | must_fix | text: Abstract "consistent with Poisson noise in 96% of tracts"; heading "Month-to-month crime is noise outside a few hubs" | sentence · claim_scope_unsupported (claim) |
| R-29 | SC-101 | The confirmatory claims are numbered with gaps (A-R3 to A-R5 missing). **Min:** relabel them C1–C5 and state in one sentence how and when the family was fixed. | EIC-W18 (min/4); EIC-Q2 (Q) | SINGLE | consider | text: Methods "claims A-R1, A-R2, A-R6, A-R7 and A-R8" | sentence · reporting_requirement_unmet (section) |
| R-30 | SC-107 | Headline numbers cannot be traced. **Min:** use one count, with years and districts, in the abstract, Introduction and Data (1.83 million vs 0.69 million vs 121,434); state the denominator of the 39%; reconcile 34% with Fig. 6c (about 30%) and the Brier difference (0.0005 vs +0.0006); state which subset enters each analysis. | EIC-W19 (min/5); R1-W16 (min/5); R1-W5 (maj/4); DA-m12 (min/5) | CORR-2 +DA | consider | text: Abstract "1.83 million police records"; Intro ¶1 "39% of the police records analysed here" | sentence · reader_traceability_reduced (manuscript) |
| R-31 | SC-02 | The Results omit that tissue explains only 18% of variance in high-crime tracts; "high-crime" is defined only in the legend; the covariance term is unexplained. **Min:** report both shares in the Results, define high-crime tracts there (at least 10 expected events per year), and explain the covariance term in the Fig. 5b legend. | EIC-W20 (min/4); R1-W9 (maj/4); R1-mi (min†/4‡); DA-C1 (crit/5) | CORR-2 +DA | must_fix | text: Results §Stable tissue ¶1 "rising to 58% in high-crime tracts" | sentence · claim_scope_unsupported (claim) |
| R-32 | SC-01 | Thesis wording outruns the estimates (validated C1). **Min:** narrow the thesis (DA-C1: composition structures which crime and when, and part of how much, while place history carries more) and replace "fixes" and "sets where" throughout, including "fixes much" → "accounts for" (EIC). Or take C1's alternative path (R-120). In both paths report the cross-term (R-110). | EIC-W20 (min/4); EIC-mi (min†/4‡); R1-W9 (maj/4); DA-C1 (crit/5) | CORR-2 +DA (DA-CRITICAL) | must_fix | text: Discussion ¶1 "The composition of a place fixes its rate…"; Intro ¶3 "composition sets where crime occurs"; Results "Composition thus sets…"; "If composition and memory fix where crime occurs" | section · claim_scope_unsupported (claim) |
| R-33 | SC-112 | Language and reference style. **Min:** fix the dangling modifier ("Holding composition at 2025…"; use "we"); move two of the four correlations in one parenthesis to the legend; state which r is Pearson; apply Nature title case uniformly (refs 7, 10, 11, 13, 21, 23, 28, 33, 34, 36, 38, 41, 42, 44, 47); check DOI style. | EIC-mi (min†/4‡) | SINGLE | consider | text: Results §Stable tissue ¶2 "Holding composition at 2025 and estimating class rates by year…" | sentence · editorial_conformance_unmet (manuscript) |
| R-34 | SC-08 | The null event study is generalised to "tissue". **Min:** narrow the sentence to the openings and closures of the business types tested; see R-04 for the DA-M7 paths. | EIC-mi (min†/4‡); DA-M7 (maj/4) | SINGLE +DA | must_fix | text: Results §Stable tissue ¶2 "Marginal changes to the tissue did not move crime." | sentence · claim_scope_unsupported (claim) |
| R-35 | SC-77 | Ref. 41 measures an individual-mobility entropy bound, not a Poisson ceiling. **Min:** drop the analogy or make it explicit and qualified; ground the ceiling in ref. 39 (R2). | EIC-mi (min†/4‡); R1-W6 (maj/5); R2-W14 (min/3); R3-W2 (maj/4); DA-M3 (maj/4) | **C4** +DA | must_fix | text: Results §Month-to-month ¶1 "the city sits close to its limit of predictability^41^" | sentence · claim_scope_unsupported (claim) |
| R-36 | SC-33 | The text says validation "held across phenotypes", but three phenotypes are untested and so are the non-parcel classes. **Min:** restrict the claim to the phenotypes with at least 80% of events geocoded and list them; state that stations, streets and favelas are not validated; mark unvalidated signatures wherever they carry an inference (DA-m2). Intervals are in R-96. | R1-W1 (maj/5); DA-m2 (min/4) | SINGLE +DA | must_fix | text: Results §Each cell class ¶2 "Point validation held across phenotypes (median ρ = 0.85; Fig. 3c)" | sentence · claim_scope_unsupported (claim) |
| R-37 | SC-38 | The reconciliation description is incomplete. **Min:** state how 2022 events were allocated when no preceding 12 months existed (R1), and whether allocated counts are fractional (DA). | R1-W2 (maj/4); DA-M2 (maj/4) | SINGLE +DA | must_fix | text: Methods §Units and reconciliation "in proportion to the geocoded events of the same stratum over the preceding 12 months" | sentence · method_reproducibility_unresolved (section) |
| R-38 | SC-39 | The burglary (19% geocoded) and lethal-violence (66%) signatures mostly project the geocoded minority. **Min:** mark them as dependent on reconciliation, or drop them from the highlighted examples, including the Discussion's burglary sentence. | R1-W2 (maj/4); DA-m2 (min/4); DA-alt3 (†) | SINGLE +DA | must_fix | text: Results §Each cell class ¶2 "residential burglary on medium-standard houses (+3.4)" | sentence · claim_scope_unsupported (claim) |
| R-39 | SC-36 | The attribution's identification assumptions are not stated, and "fitted jointly" is undefined. **Min:** add a Methods paragraph listing the assumptions (one city-wide rate per class, additivity, exposure measures, location confounding) and define "fitted jointly". | R1-W3 (maj/4); R1-W15 (min/5) | SINGLE | must_fix | equation: Methods §Composition-aware attribution, y_s ~ Poisson(Σ_k E_sk λ_k) | section · method_reproducibility_unresolved (section) |
| R-40 | SC-73 | The dispersion test is underspecified. **Min:** state α, the multiplicity handling, which tracts enter (21,331 or 15,708) and how zero-mean tracts are treated. | R1-W4 (maj/5); R1-W15 (min/5) | SINGLE | must_fix | text: Methods §Predictability ceiling and dispersion "compares Σ_t (y_st − ȳ_s)²/ȳ_s … on 11 degrees of freedom" | sentence · method_reproducibility_unresolved (section) |
| R-41 | SC-76 | "Close to its limit" is contradicted within tracts (0.018 of 0.56). **Min:** rephrase: between tracts, forecasts approach the ceiling; within tracts, a non-Poisson component exists (ceiling 0.56) that no method captured (0.018), concentrated in high-count tracts (R1). Restrict "close to the limit" to between-unit prediction and state the roughly 3% within tracts (DA). | R1-W6 (maj/5); R3-W2 (maj/4); DA-M3 (maj/4) | CORR-2 +DA | must_fix | text: Results §Month-to-month ¶1 "Within tracts, however, it explained R² = 0.018 of a maximum of 0.56." | sentence · claim_scope_unsupported (claim) |
| R-42 | SC-55 | "P = 0.005" is the permutation floor (1/201), not an estimate. **Min:** write "P ≤ 0.005" in the text and Fig. 4d, or run more permutations (R-107). | R1-W7 (maj/4); R1-mi (min†/4‡) | SINGLE | must_fix | text: Results §Clock ¶1 "(P = 0.005 in each year)" | sentence · reporting_requirement_unmet (claim) |
| R-43 | SC-58 | "Memory" asserts state dependence. **Min:** rename it "persistent place effect beyond composition" (R1, R2) or "state beyond type" (R3) in the abstract, Introduction, headings, Results, Discussion ("why some places remember crime"), Fig. 5 and Methods, unless a dynamic test is added (R-111). | R1-W9 (maj/4); R2-W5 (maj/4); R2-mi (min†/4‡); R3-W4 (maj/3) | **C3** | must_fix | text: Abstract "Beyond composition, places carry a stable memory of crime."; Discussion ¶3 | section · claim_scope_unsupported (claim) |
| R-44 | SC-98 | The pseudo-vault point-validation ρ of 0.63, against 0.93 in exploration, goes undiscussed. **Min:** discuss the drop. | R1-W10 (maj/4) | SINGLE | should_fix | figure: Fig. 6g pseudo-vault point-validation value | sentence · interpretive_ambiguity_remains (figure) |
| R-45 | SC-83 | 2025 lies inside the exploration window, yet the benchmark is called "pre-specified" and given Holm P values. **Min:** label the 2025 benchmark as development and keep confirmatory language for 2026. | R1-W11 (maj/3) | SINGLE | should_fix | text: Results §Month-to-month ¶2 "Under a pre-specified protocol, we benchmarked…" | sentence · claim_scope_unsupported (claim) |
| R-46 | SC-53 | The crowd factor spans only 0.45–1.6, so rank survival is nearly automatic. **Min:** describe rank survival as a weak check. | R1-W13 (min/4) | SINGLE | consider | text: Results §Clock ¶2 "The ordering of classes survives division by the crowd." | sentence · claim_scope_unsupported (claim) |
| R-47 | SC-51 | Rival explanations for dawn robbery are not addressed. **Min:** name target suitability, offender routines, darkness and commuter convergence on paths to transit; name crime pattern theory (Brantingham & Brantingham 1993 [UNVERIFIED]); cite Bernasco, Ruiter & Block 2017 and Tompson & Bowers 2013; discuss the 0.4 weekend ratio on low-standard housing. Tests are in R-118. | R1-W13 (min/4); R2-W3 (maj/4); DA-M6 (maj/4); DA-alt6 (†) | CORR-2 +DA | must_fix | text: Results §Clock ¶2; Discussion ¶2 | section · claim_scope_unsupported (claim) |
| R-48 | SC-19 | Displayed analyses lack Methods (ED Figs 2–5 and 7, Fig. 3f, Laya-FT), and the core Methods have replication gaps (EM initialisation, convergence and zero boundary; aggregation of H; the per-pedestrian formula; stacking weights; tuning and refits; "calibrated within 5%" and the Fig. 6f metric; segment linking beyond 60 m). **Min:** add the details (about six sentences or a Supplementary table) and Methods for every displayed analysis kept, or cut the Methods-less analyses. If the audit stays, reduce ED Fig. 2 to a short table with explicit verdict rules. | R1-W14 (min/4); R1-W15 (min/5) | SINGLE | consider | absence: Methods, Statistics, legends, checked for the procedures listed (R1-W14, W15) | section · method_reproducibility_unresolved (section) |
| R-49 | SC-20 | Knox near-repeat placement. **Min (per D-3):** either bring the Knox results into the main text with full Methods, or cut them and address near-repeat dynamics through R-56. | R1-W14 (min/4); R2-W6 (maj/4) | SPLIT (D-3) | must_fix | figure: ED Fig. 5a, Knox ratio between parcel families | section · evidence_gap_remains (claim) |
| R-50 | SC-42 | Place-defined offences inflate signatures. **Min:** report robbery on public transport and residential burglary as positive controls rather than findings; lead with offences not defined by place (R2); state whether the cargo-robbery location marks interception or recovery (R2-Q7). Counts are in R-115. | R1-W18 (min/4); R2-W9 (min/3); R2-Q7 (Q) | CORR-2 | should_fix | text: Results §Each cell class ¶2 "Robbery on public transport is enriched at bus terminals and rail stations" | sentence · claim_scope_unsupported (claim) |
| R-51 | SC-63 | Exclusions are unexplained. **Min:** explain why 2021 pairs are excluded from the transitions, and why tracts with fewer than one expected event per year are excluded from the memory analysis. | R1-W20 (min/4); R1-mi (min†/4‡) | SINGLE | consider | text: Methods "excluding pairs with 2021"; "15,708 exploration tracts with at least one expected event per year" | sentence · method_reproducibility_unresolved (section) |
| R-52 | SC-30 | Kitagawa is cited, but the composition component is not reported. **Min:** drop the reference, or report the composition component, which R1 expects to be near zero. | R1-dc (min†/4‡) | SINGLE | consider | text: Results §Stable tissue ¶2 "a rate–composition decomposition^37^" | sentence · reader_traceability_reduced (claim) |
| R-53 | SC-25 | The gap statement misdescribes micro-place research, which counts crime directly at addresses and segments. **Min:** reframe in two parts: (i) micro-place studies rarely cover full parcel composition, all offences and the hour together; (ii) incomplete or suppressed geocoding in Brazilian police data forces inference from aggregates (shares in R-98). Cite Sherman, Gartin & Buerger 1989 and Eck & Weisburd 1995 (both [UNVERIFIED] metadata) and Steenbeek & Weisburd 2016. | R2-W1 (maj/4); R3-W1 (maj/4) | CORR-2 | must_fix | text: Intro ¶1 "Crime, however, is usually counted in areal units that mix many parcels and land uses" | section · claim_scope_unsupported (claim) |
| R-54 | SC-65 | The decline reading ignores micro-place crime-drop evidence and implies an unnamed response. **Min:** discuss the contrast with ref. 3 and Braga, Hureau & Papachristos 2011 (units, offence, context); name candidate drivers and possible reporting changes (the Celular Seguro programme from December 2023; Smart Sampa; police operations; robbery and theft reclassification); hedge or drop the causal reading and the hub-policy corollary (DA). | R2-W4 (maj/4); R2-Q4 (Q); DA-M4 (maj/4); DA-alt5 (†) | SINGLE +DA | must_fix | text: Results §Stable tissue ¶2 "It came from the diffuse fabric"; Discussion ¶2 "so hubs probably need tools of their own" | section · claim_scope_unsupported (claim) |
| R-55 | SC-61 | Persistence lacks a theoretical anchor, and ref. 36 is cross-sectional. **Min:** state the heterogeneity versus state-dependence distinction (Nagin & Paternoster 2000; Heckman [UNVERIFIED]); replace or add to ref. 36 with place-management and risky-facility work (Eck, Clarke & Guerette 2007). | R2-W5 (maj/4); R3-W4 (maj/3) | CORR-2 | must_fix | text: Results §Stable tissue ¶1 "and neighbourhood effects on violence^36^" | sentence · claim_scope_unsupported (claim) |
| R-56 | SC-74 | The noise claim goes beyond the offence and scale tested. **Min:** limit it to phone crime at the tract-month scale; say how sub-monthly or sub-tract dynamics (near-repeat risk at days to weeks and about 200 m; Johnson et al. 2007) would change the ceiling; place the result against chronic versus temporary hot spots (Gorr & Lee 2015) and sparse-data concentration measurement (Bernasco & Steenbeek 2017; Haberman, Sorg & Ratcliffe 2017). | R2-W6 (maj/4); DA-M3 (maj/4) | SINGLE +DA | must_fix | text: Intro ¶3 "and that month-to-month variation is mostly noise" | section · claim_scope_unsupported (claim) |
| R-57 | SC-87 | Recorded-crime bias is acknowledged but never used to qualify the results that depend on it. **Min:** discuss reporting propensity for phone theft versus robbery in Brazil (victimization-survey evidence; the specific survey [UNVERIFIED] per R2) and qualify the dependent results: the income gradient of the flagged area, the decline, the favela and peripheral signatures, the near-zero residential rate and dawn robbery. Say the 26% vs 7% recorded split may overstate richer tracts. State both directions of equity risk: under-protection of poorer tracts for phone crime, over-policing for violence (R3). Note that point validation cannot detect this bias (R3). Cite Akpinar et al. 2021 and Buil-Gil et al. 2022. | R2-W7 (maj/4); R3-W5 (maj/3); R3-mi (min†/4‡); DA-M8 (maj/3) | CORR-2 +DA | must_fix | text: Discussion ¶5 "Police records undercount crime unevenly across places and types of crime." | section · claim_scope_unsupported (claim) |
| R-58 | SC-27 | Cited sources are described inaccurately. **Min:** re-describe ref. 12 (vicinity effects offset by density) and ref. 13 (segments and intersections, eight crime types), or cite facility-level work; present the time-of-day evidence as mixed (ref. 14; Bernasco, Ruiter & Block 2017); let the ref. 46 claim allow for earlier hourly work (refs 33, 34); give an original source for "urban tissue" (ref. 27) [UNVERIFIED]; cite ref. 32 for the denominator problem, not hourly estimates; cite Goodman 1953 [UNVERIFIED] as the closer reference than ref. 11. | R2-W10 (min/4); R2-W11 (min/4); R2-mi (min†/4‡) | SINGLE | consider | text: Intro ¶1 "Parcel-level studies isolate single land uses^12^ or single crime types^13^" | section · claim_scope_unsupported (claim) |
| R-59 | SC-47 | The generator/attractor test is run but not interpreted. **Min:** classify cell classes by how their rank changes from per km to per pedestrian (the ranks behind Fig. 4f) and interpret the result in generator/attractor terms. | R2-W12 (min/4) | SINGLE | should_fix | text: Results §Clock ¶2 "The ordering of classes survives division by the crowd." | section · interpretive_ambiguity_remains (claim) |
| R-60 | SC-86 | Ref. 48 concerns police-discovered offences, not victim-reported phone crime. **Min:** separate discovery feedback from differential victim reporting (Akpinar et al. 2021) and cite accordingly. | R2-W13 (min/4) | SINGLE | consider | text: Discussion ¶3 "because police-recorded crime feeds back into where police look^48^" | sentence · claim_scope_unsupported (claim) |
| R-61 | SC-28 | São Paulo crime geography and criminal governance are absent. **Min:** add a short paragraph (Ceccato, Haining & Kahn 2007; Biderman et al. 2019) and use it in reading the lethal-violence and peripheral-robbery results; name the place-centred paradigm choice (R3). | R2-W15 (min/4); R3-dc (min†/4‡); DA-alt7 (†) | CORR-2 +DA | should_fix | absence: Introduction, Discussion and references, checked for São Paulo crime-and-place and criminal-governance work (R2-W15) | section · claim_scope_unsupported (claim) |
| R-62 | SC-113 | Terminology. **Min:** use "areas" or "tracts" for areal units and keep "places" for micro-places; state whether theft or robbery is meant wherever an interpretation depends on the difference. | R2-W16 (min/4); R2-mi (min†/4‡) | SINGLE | consider | text: Abstract "Crime concentrates in a few places, but mapped places mix many land uses" | sentence · interpretive_ambiguity_remains (manuscript) |
| R-63 | SC-26 | Earlier testable biological borrowing (human ecology; contagion models) is overlooked. **Min:** acknowledge it (Park, Burgess & McKenzie 1925; Shaw & McKay 1942 [UNVERIFIED]) and say how a measurement-level analogy differs. | R2-W18 (min/3) | SINGLE | should_fix | text: Intro ¶2 "but as metaphor rather than as a measurement instrument whose outputs can be tested" | sentence · claim_scope_unsupported (claim) |
| R-64 | SC-93 | The components of the lethal-violence phenotype are not stated. **Min:** list them, including whether deaths from police intervention and robbery-homicide are counted. Separate modelling is in R-122. | R2-Q2 (Q); R3-W12 (min/3); R3-Q2 (Q) | CORR-2 | consider | absence: Methods §Phenotype panel, checked for the definition of lethal violence (R3-W12) | sentence · reporting_requirement_unmet (section) |
| R-65 | SC-23 | The omics lineage is under-credited, and the Introduction blurs which side of deconvolution is known. **Min:** say in Results that attribution is a Poisson ecological regression with known exposures; credit csSAM, CIBERSORTx group mode and TCA; rewrite the Introduction sentence (deconvolution estimates composition from reference profiles; with composition known, the model run the other way estimates the profiles). | R3-W1 (maj/4); R3-W8 (min/5) | SINGLE | should_fix | text: Intro ¶2 "spots of known or estimated composition" | sentence · claim_scope_unsupported (claim) |
| R-66 | SC-75 | The "intrinsic noise" (ref. 40) analogy is the wrong concept. **Min:** use the sampling (shot) noise analogue and state what it implies: consistency with Poisson at low counts says little about rate variation. | R3-W2 (maj/4); DA-M3 (maj/4) | SINGLE +DA | must_fix | text: Results §Month-to-month ¶1 "monthly counts behave like the intrinsic noise that bounds what can be predicted about single cells^40^" | sentence · claim_scope_unsupported (claim) |
| R-67 | SC-07 | Productive and causal language, and the phenotype premise. **Min:** replace "produces" with "is attributed to" or "hosts" in Results, Methods and the Fig. 3b legend; state next to Fig. 1a where the analogy breaks (parcels host crime; they do not produce it); confine the language to association and drop targeting claims unless tested (DA-M7; see R-04, R-27). | R3-W3 (maj/3); DA-M7 (maj/4); DA premise (†) | SINGLE +DA | must_fix | text: Results §Each cell class ¶1 "the sum of what its cells produce"; Fig. 3b legend "share of the phenotype produced by the class" | section · claim_scope_unsupported (claim) |
| R-68 | SC-91 | Ethics is reduced to privacy; favela and low-income signatures carry a risk of territorial stigma. **Min:** add a paragraph on territorial stigma and on how class signatures should and should not be used, flagging the constructed favela exposure; extend the Ethics section with the intended and excluded uses of the signatures and the explorer (e.g., no use of class-level signatures to justify area-wide policing); say whether any community or stakeholder consultation took place; name the stakeholders. | R3-W3 (maj/3); R3-Q5 (Q); R3-dc (min†/4‡); DA stakeholders (†); DA-m11 (min/4) | SINGLE +DA | should_fix | text: Methods §Privacy and ethics "The study uses public administrative records…" | section · reporting_requirement_unmet (section) |
| R-69 | SC-56 | "Clock" implies an endogenous oscillator. **Min:** use "daily rhythm" or "diurnal profile", or define "clock" once as a class-specific daily profile; frame the crowd test as masking (Mrosovsky). Cosinor is optional, in R-127. | R3-W6 (min/4) | SINGLE | consider | text: heading "The tissue keeps a clock that is not the clock of crowds" | sentence · interpretive_ambiguity_remains (claim) |
| R-70 | SC-46 | The matrix is an output and is never used as a signature matrix. **Min:** call it "class-specific crime profiles (the analogue of reference signatures)"; the instrument route is in R-128. | R3-W7 (min/5) | SINGLE | consider | text: Results §Each cell class ¶2 "behaves as a signature matrix^20^" | sentence · interpretive_ambiguity_remains (claim) |
| R-71 | SC-95 | Implications are addressed mainly to the police. **Min:** rebuild the paragraph around measures outside policing and name the agencies (transit operator, municipal lighting, planning and licensing), keeping policing as one lever. | R3-W11 (min/3); R3-dc (min†/4‡); DA stakeholders (†) | SINGLE +DA | consider | text: Discussion ¶2 "Place-based policing reduces crime^45^" | section · interpretive_ambiguity_remains (section) |
| R-72 | SC-96 | Two rival explanations are unbounded: frontage understates activity on high-rise parcels, and hub stability may reflect saturation policing or reporting convenience. **Min:** name and test or explicitly bound them (the DA's D3 standard). | DA-alt4 (†); DA-alt5 (†) | DA-only | consider | text: Results §Stable tissue ¶2 "Hubs kept their rates"; Methods §Composition-aware attribution (frontage exposure) | section · claim_scope_unsupported (claim) |
| R-73 | SC-85 | The equity risk is attributed to monthly updates, but the static map flags alike (52% vs 53%), and the skew runs opposite to the cited feedback loop. **Min:** align the argument with the observed direction. The static-map profile is in R-130. | DA-m8 (min/4) | DA-only | consider | text: Discussion ¶3 "flagging by density concentrated attention in richer tracts" | sentence · claim_scope_unsupported (claim) |
| R-74 | SC-67 | A class-differentiated decline sits in the fabric the paper calls noise. **Min:** state that tract-month undetectability coexists with an aggregate trend. The test is R-132. | DA-M4 (maj/4) | DA-only | should_fix | text: Results §Stable tissue ¶2 "local streets fell faster than the city" vs §Month-to-month heading | sentence · interpretive_ambiguity_remains (claim) |

### 4.b Items requiring figure edits

| ID | SC | Problem → minimum remedy | Sources (sev/conf) | Consensus | Obligation | Location (anchor) | Cost · consequence |
|---|---|---|---|---|---|---|---|
| R-75 | SC-97, SC-10 | Fig. 6g prints pseudo-vault P values beside "Confirmation" and carries the language-model row. **Min:** make Fig. 6g a plain list of the pre-specified claims and criteria, to be filled with vault results; remove the pseudo-vault P values or label them in-sample; remove row H2. | EIC-W1 (maj/4); EIC-W5 (maj/4); R1-W10 (maj/4); R1-W14 (min/4); DA-m5 (min/5); DA-m7 (min/5) | CORR-2 +DA | should_fix | figure: Fig. 6g, status of confirmatory claims | other:figure_artwork · claim_scope_unsupported (figure) |
| R-76 | SC-12 | Fig. 3f (Shapley Sankey by theory group) is uncited and has no Methods. **Min:** delete it or merge it into ED Fig. 7 (EIC); if kept, give it full Methods (R1). | EIC-W1 (maj/4); EIC-W11 (min/5); R1-W14 (min/4) | CORR-2 | should_fix | figure: Fig. 3f | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-77 | SC-13 | Fig. 5f (change by crime type) is never cited. **Min:** delete or move it, or cite it. | EIC-W1 (maj/4); EIC-W11 (min/5) | SINGLE | should_fix | figure: Fig. 5f | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-78 | SC-14 | Fig. 2c,e (tract pies, tissue domains) are uncited and the domains are not used downstream. **Min:** delete or move them unless a Discussion sentence uses them. | EIC-W1 (maj/4); EIC-W11 (min/5); R1-W14 (min/4); DA-m4 (min/4) | CORR-2 +DA | should_fix | figure: Fig. 2c,e | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-79 | SC-15 | Fig. 1a advertises the ligand–receptor mapping that the Discussion says fails. **Min:** drop the row (move it to ED Fig. 2 as tested and failed, R3); keep only mappings used in Results; use "niche" in one sense (R-20). | EIC-W1 (maj/4); R3-W9 (min/4) | CORR-2 | should_fix | figure: Fig. 1a, row "Ligand–receptor signal → Crime generator → target" | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-80 | SC-21 | ED Fig. 2 does not credit the classical lineage of each step. **Min:** credit the classical lineage of each module. The comparator replacement is in R-124. | EIC-W2 (maj/4) | C3 (sub-claim) | should_fix | figure: ED Fig. 2, equivalence audit | other:figure_artwork · claim_scope_unsupported (figure) |
| R-81 | SC-99 | Figures carry undefined codes. **Min:** spell out "FCU" (Fig. 1); replace "Laya-FT" (Fig. 6g) and the truncated "Laya…" row (ED Fig. 2) with plain labels. | EIC-W5 (maj/4); EIC-mi (min†/4‡); R3-mi (min†/4‡) | CORR-2 | should_fix | figure: Fig. 1 legend "Favela (census FCU)"; Fig. 6g "Laya-FT" | other:figure_artwork · reader_traceability_reduced (figure) |
| R-82 | SC-103, SC-105 | Figure labels drift from the text, and the axes carry transcriptomic jargon. **Min:** apply the naming key (R-19) to every figure label (crime types in Fig. 3, "middle" vs "medium" standard, programs labelled by classes in Fig. 3d, "low-standard" per R-18); replace gene and expression wording with attribute wording (Fig. 2b "Mean expression", "Parcels expressing"; Fig. 5a "Same genes, no typing"). | EIC-W8 (maj/5) | SINGLE | should_fix | figure: Fig. 2b axes; Fig. 3 labels; Fig. 5a | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-83 | SC-106 | Axes say "thefts" where the text reports phone crime (thefts plus robberies). **Min:** relabel as "phone crime", or correct the text if the figures plot thefts only. | EIC-W9 (min/4); R1-W16 (min/5) | CORR-2 | consider | figure: Fig. 3a x-axis "Phone thefts per year, per km"; Figs 3f, 5a, 6a, 6c, 6e, 6f | other:figure_artwork · reader_traceability_reduced (figure) |
| R-84 | SC-84 | Fig. 6e shows positive skill for lethal violence, while the text says no method beat the baseline. **Min:** state the sign convention and the baseline, add intervals from the existing bootstrap, and reword to "no method significantly beat". Alternative: cut the panel as marginal (R1-W14). | EIC-W10 (min/3); R1-W16 (min/5); R1-W14 (min/4) | CORR-2 | consider | text: Results §Month-to-month ¶2 "no method beat the baseline for lethal violence (Fig. 6e)" | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-85 | SC-109 | ED figures are numbered out of citation order (ED Fig. 2 is cited first; ED Fig. 1 is never cited), and Fig. 6 panels are first cited in the order b, c, d, a. **Min:** renumber the ED figures in order of first citation and reorder the Fig. 6 panels to follow the text. | EIC-W11 (min/5) | SINGLE | consider | figure: ED Figs 1–10; Fig. 6 panel order | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-86 | SC-110 | The Fig. 1 palette reverses residential blues and commerce oranges relative to Figs 2–5, and domains reuse the type colours. **Min:** use one type palette in all figures and a separate, unconfusable palette for domains. | EIC-W12 (min/5) | SINGLE | consider | figure: Fig. 1 legend vs Fig. 2b and Fig. 3a swatches | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-87 | SC-78 | Ceiling keys are inconsistent: "maximum R² without a model" in Fig. 6b, "Noise ceiling" in Fig. 6a. **Min:** apply the single "noise ceiling" term (R-23) to Fig. 6b and rename the Fig. 6a line "expected capture if the model were true". | EIC-W13 (min/4); R1-W6 (maj/5); R1-W16 (min/5); R1-mi (min†/4‡) | CORR-2 | must_fix | text: Fig. 6 legend "maximum R² without a model (open)" | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-88 | SC-111 | Legends and annotations are incomplete. **Min:** describe the Fig. 3c hollow markers; explain "ICC = 0.84" in Fig. 5a; add the "Chance" and "Ensemble, geocoded only" lines and the 28% annotation to the Fig. 6a legend; explain the missing phone-theft markers in Fig. 4e; fix the overlapping labels in Fig. 4f; interpret the z-scores of about ±100 in Fig. 2d. | EIC-mi (min†/4‡) | SINGLE | consider | figure: Figs 2d, 3c, 4e, 4f, 5a, 6a | other:figure_artwork · reader_traceability_reduced (figure) |
| R-89 | SC-17 | The NMF programs (Fig. 3d,e) repeat the signatures and carry no later inference. **Min:** cut them, or keep them only if a Discussion sentence uses them; drop the Results sentence accordingly. The optional residual factorization is R-129. | R1-W14 (min/4); R3-W10 (min/4); DA-m4 (min/4) | CORR-2 +DA | consider | text: Results §Each cell class ¶2 "yielded four programs that were stable across seeds" | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-90 | SC-18 | Marginal panels. **Min:** drop the Fig. 2a UMAP (it supports no claim); keep Fig. 2d (neighbourhood enrichment) and Fig. 4e (weekend ratios) only if a downstream sentence uses them. Fig. 4e is used if R-47 adopts the weekend argument. | R1-W14 (min/4); R1-mi (min†/4‡); DA-m4 (min/4) | SINGLE +DA | consider | figure: Fig. 2a, 2d, 4e | other:figure_artwork · editorial_conformance_unmet (figure) |
| R-91 | SC-108 | ED Fig. 1 classes methods and baselines differently from the Methods and uses Portuguese family labels. **Min:** match the Methods (GWR and spatial panel; KDE labelled "Astronomia"; persistence, seasonal naïve and prospective hot-spotting missing) and use English labels ("Aprendizado", "Sismologia", "Fundacao"). | R1-W16 (min/5); R1-mi (min†/4‡) | SINGLE | consider | figure: ED Fig. 1 | other:figure_artwork · reader_traceability_reduced (figure) |
| R-92 | SC-54 | Fig. 4c hides how small the night-time denominator is. **Min:** show pedestrians per hour beside the per-pedestrian risk. | R2-mi (min†/4‡) | CORR-2 (sub-claim) | consider | figure: Fig. 4c, citywide robbery risk per pedestrian by hour | other:figure_artwork · interpretive_ambiguity_remains (figure) |
| R-93 | SC-29 | ED Fig. 2 labels. **Min:** name the attribution method (not "Known-composition spots", which is a setting); use one name for the decline module (Kitagawa vs "differential expression"); name the library-size row once in the crowd paragraph, or leave it out. | R3-mi (min†/4‡) | SINGLE | consider | figure: ED Fig. 2 rows for attribution, decline and library size | other:figure_artwork · interpretive_ambiguity_remains (figure) |

### 4.c Items requiring new analyses

| ID | SC | Problem → minimum remedy | Sources (sev/conf) | Consensus | Obligation | Location (anchor) | Cost · consequence |
|---|---|---|---|---|---|---|---|
| R-94 | SC-82 | Vault exposure (conditional on R-17). **Min:** if vault-district crime records entered the benchmark, dispersion test, ceiling or ED Fig. 7, re-run those analyses on the 77 exploration districts, or argue in text why the exposure cannot inform the atlas claims. | EIC-W7 (maj/3); R1-W11 (maj/3) | CORR-2 | should_fix | text: Methods "2,000 bootstrap resamples of the 96 districts" | re_analysis · evidence_gap_remains (claim) |
| R-95 | SC-31 | No genuinely held-out validation exists. **Min:** split geocoded events into halves (or alternate months), fit on tract counts built from one half plus non-geocoded events, and validate on the other half's points; or fit on 2024 and validate on 2025 points (R1). DA alternatives: the 2026 vault; a non-police source (transit-operator incident logs, locations of phone-blocking requests); a point attribution that does not use frontage. | R1-W1 (maj/5); DA-M5 (maj/5) | SPLIT (D-1) | must_fix | text: Results §Each cell class ¶1 "Linking 100,347 geocoded events … (Spearman ρ = 0.93)" | re_analysis (new_data option) · evidence_gap_remains (claim) |
| R-96 | SC-33 | Validation statistics lack uncertainty. **Min:** a bootstrap interval for every ρ, plus a reference ρ from attribution fitted to counts permuted across tracts within district. | R1-W1 (maj/5) | SINGLE | must_fix | figure: Fig. 3c, point validation per phenotype | re_analysis · reporting_requirement_unmet (figure) |
| R-97 | SC-38 | Reconciliation may manufacture persistence and Poisson-like counts. **Min:** re-run the memory decomposition, persistence curve, dispersion test and predictability ceiling (and, per DA, the benchmark) on geocoded-only counts, shown next to the current results. Add one alternative allocation: same month, or proportional to the composition model's expected counts or exposure. | R1-W2 (maj/4); R1-Q2 (Q); DA-M2 (maj/4) | SINGLE +DA | must_fix | text: Methods §Units and reconciliation "over the preceding 12 months" | re_analysis · evidence_gap_remains (claim) |
| R-98 | SC-40 | Reconciled shares are not reported. **Min:** report the non-geocoded (reconciled) share by phenotype, stratum and year in Methods; this also supports R-53. | R1-W2 (maj/4); R1-Q2 (Q); R2-W1 (maj/4); DA-M2 (maj/4) | CORR-2 +DA | must_fix | absence: Methods; only ED Fig. 10a reports geocoded shares, and not by year or stratum (R1-W2) | re_analysis · reporting_requirement_unmet (table) |
| R-99 | SC-35 | The recovery accuracy of EM attribution is unknown. **Min:** a simulation that generates tract counts from known λ with realistic heterogeneity (district multipliers, overdispersion), reporting bias and interval coverage per class. | R1-W3 (maj/4) | SINGLE | must_fix | equation: Methods §Composition-aware attribution | re_analysis · evidence_gap_remains (claim) |
| R-100 | SC-34 | The constant city-wide rate is untested. **Min:** refit with multiplicative district or tissue-domain effects, y_s ~ Poisson(θ_d Σ_k E_sk λ_k) (R1); or district random effects on λ_k (R3); or class-by-region rates (DA). Report how stable the λ ranks and enrichments remain, and whether λ_k varies across domains or income strata (R2). | R1-W3 (maj/4); R2-W2 (maj/4); R3-W1 (maj/4); DA-M1 (maj/4) | **C3** +DA | must_fix | equation: y_s ~ Poisson(Σ_k E_sk λ_k), single city-wide λ_k | re_analysis · evidence_gap_remains (claim) |
| R-101 | SC-35 | Collinearity and zero-boundary solutions are unexamined. **Min:** report exposure collinearity (condition number or pairwise correlations) and how often each λ hits zero across bootstrap draws, including the hourly λ of Fig. 4; state whether the low-standard housing profile between 07:00 and 18:00 is a boundary solution. | R1-W3 (maj/4); R1-W8 (maj/4); R1-Q3 (Q) | SINGLE | must_fix | figure: Fig. 4b, profile near zero 07:00–18:00 | re_analysis · evidence_gap_remains (claim) |
| R-102 | SC-72 | No estimate of latent month-to-month variation exists. **Min:** fit a hierarchical NB or Poisson-lognormal model to tract-month counts (overdispersion by stratum or class; DESeq2-style shrinkage, R3) and report the latent month-to-month CV with an interval. If a tract-level statement stays, use an equivalence formulation with FDR control (R1). | R1-W4 (maj/5); R3-W2 (maj/4); DA-M3 (maj/4) | CORR-2 +DA | must_fix | text: Results §Month-to-month ¶1 "median dispersion 1.01" | re_analysis · evidence_gap_remains (claim) |
| R-103 | SC-71 | The dispersion test has no power analysis. **Min:** a power simulation, or the minimum detectable extra-Poisson variation, at the observed tract means. | R1-W4 (maj/5); R2-W6 (maj/4); R3-W2 (maj/4); R3-Q3 (Q); DA-M3 (maj/4) | **C3** +DA | must_fix | text: Results §Month-to-month ¶1 "consistent with Poisson noise in 96% of tracts" | re_analysis · evidence_gap_remains (claim) |
| R-104 | SC-80 | Hub concentration may be a scale effect (per D-2). **Min:** compute the share of excess variance expected in the top 1% under a common-θ NB and compare it with 88%; plot the relative dispersion index by count decile; report forecast skill for hub tracts alone. | R1-W5 (maj/4); R3-W2 disputed | SPLIT (D-2) | must_fix | text: Results §Month-to-month ¶1 "held 34% of it and 88% of the extra-Poisson variance" | re_analysis · claim_scope_unsupported (claim) |
| R-105 | SC-41 | Default or duplicate geocodes may create spikes or bias. **Min:** check hub tracts for repeated identical coordinates and station-address or centroid geocodes; report the geocoded share and duplicate coordinates by income quintile and year. | R1-W5 (maj/4); R2-W7 (maj/4); R2-Q3 (Q) | CORR-2 | must_fix | absence: Methods §Data, checked for how coordinates are produced (R2-Q3) | re_analysis · evidence_gap_remains (dataset) |
| R-106 | SC-79 | The ceilings have no intervals, and the within-tract ceiling is not decomposed. **Min:** district-bootstrap intervals for the ceilings; split the within-tract ceiling into a seasonal-and-trend part (bounded by an in-sample seasonal-trend fit) and a residual part. | R1-W6 (maj/5) | SINGLE | must_fix | figure: Fig. 6b, ceilings without intervals | re_analysis · reporting_requirement_unmet (figure) |
| R-107 | SC-55 | The event-level permutation null is anti-conservative. **Min:** permute blocks (tract-days or tract-weeks), or use a parametric bootstrap from a district × period model with tract overdispersion; report excess H (H minus the mean null H) with an interval; compute replication on null-subtracted deviations; run more permutations. | R1-W7 (maj/4) | SINGLE | must_fix | text: Methods §Tissue clock "permuted periods among events within districts (200 permutations…)" | re_analysis · evidence_gap_remains (claim) |
| R-108 | SC-100 | The confirmatory criteria are weak, and OSF registration is only planned. **Min (protocol amendment before the vault opens):** A-R2 at ρ ≥ 0.7 using the held-out-point design; A-R7 as excess H under block permutation (pre-register the block version); A-R1 as concordance of log rates within parcel types excluding stations and streets, or a calibration slope in a stated band. State the test and P computation for each claim, and register on OSF. | R1-W7 (maj/4); R1-W10 (maj/4); R1-Q4 (Q) | SINGLE | must_fix | text: Methods §Statistics "A-R2, ρ > 0 for point validation" | re_analysis · reporting_requirement_unmet (section) |
| R-109 | SC-49 | The 41% and the hourly profile are unchecked. **Min:** bootstrap intervals for the 41% and the hourly profile (and for the weekend ratios, per R1's reporting table); the raw hourly robbery distribution in tracts dominated by low-standard housing against comparison tracts; the share of records stamped exactly 04:00 or 05:00 and the share recorded by period only. | R1-W8 (maj/4); R1-dc (min†/4‡) | SINGLE | must_fix | figure: Fig. 4b, weekday robbery vs pedestrians, four classes | re_analysis · evidence_gap_remains (claim) |
| R-110 | SC-59 | The variance decomposition is not unique, and the cross-term is unreported. **Min:** fit log μ_st = log(Σ_k E_sk λ_kt) + u_s + v_st (Poisson-lognormal or NB mixed); report σ²_u, σ²_v and the variance of the composition offset on the latent scale with district-bootstrap intervals; report the in-sample R² and the tissue–memory cross-term (DA). | R1-W9 (maj/4); DA-C1 (crit/5); DA-M1 (maj/4) | SINGLE +DA (DA-CRITICAL) | must_fix | text: Methods §Memory of place "with a cross-term absorbing their covariance" | re_analysis · claim_scope_unsupported (claim) |
| R-111 | SC-62 | A dynamic test is needed if "memory" is retained (alternative to R-43). **Min:** test whether year-t shocks predict t+1 beyond the place effect (lagged crime shocks conditional on place fixed effects). | R1-W9 (maj/4); R2-W5 (maj/4); R3-W4 (maj/3) | **C3** (conditional) | consider | text: Abstract "places carry a stable memory of crime" | re_analysis · claim_scope_unsupported (claim) |
| R-112 | SC-69 | Event-study inference. **Min:** each variant's estimate with its 95% interval, or equivalence tests; registry dates validated on a sample (required if the study stays in the main text). If kept as a test of the thesis (D-5), state the effect the signature matrix predicts for an opening, whether it lies in the excluded range, and whether openings change a parcel's class (DA-M7). | R1-W12 (min/5); DA-M7 (maj/4) | SINGLE +DA | must_fix | figure: ED Fig. 9; text "effects larger than 4–11% … are excluded" | re_analysis · claim_scope_unsupported (claim) |
| R-113 | SC-54 | Night-time denominators carry no uncertainty. **Min:** survey-bootstrap intervals for the hourly denominators and the 19-fold ratio; pool hours with little survey support (R1); report the uncertainty of night-time pedestrian estimates (DA); state whether the O-D survey applies a minimum walking distance and how that affects the dawn denominator (R2-Q6, premise [UNVERIFIED] per R2). | R1-W13 (min/4); R2-W3 (maj/4); R2-Q6 (Q); DA-M6 (maj/4) | CORR-2 +DA | must_fix | text: Results §Clock ¶2 "robbery risk per pedestrian peaks at 03:00, at 19 times its daily mean" | re_analysis · reporting_requirement_unmet (claim) |
| R-114 | SC-43 | 285 enrichment intervals are read without adjustment. **Min:** simultaneous intervals or FDR across the cells; report how many enrichments survive; label them exploratory. | R1-W17 (min/4) | SINGLE | consider | text: Methods "the bootstrap interval excluded zero enrichment" | re_analysis · reporting_requirement_unmet (claim) |
| R-115 | SC-42 | Sensitivity to place-defined offences. **Min:** report the number of distinct top classes with and without place-defined offences (R2), or show the transport-robbery signature on geocoded events only (R1). | R1-W18 (min/4); R2-W9 (min/3) | CORR-2 | should_fix | text: Results §Each cell class ¶2 "with 11 distinct classes at the top" | re_analysis · claim_scope_unsupported (claim) |
| R-116 | SC-37 | D² is measured against a constant count. **Min:** also report D² against a size-only model (one common rate times total exposure). | R1-W19 (min/5); DA-m3 (min/4) | SINGLE +DA | consider | text: Methods "relative to a constant expected count across tracts" | re_analysis · reporting_requirement_unmet (claim) |
| R-117 | SC-63 | Classifier error (6.4%) exceeds the transition rate it measures (1.8%). **Min:** estimate transitions from observed cadastral use codes, or correct the transition matrix for misclassification. | R1-W20 (min/4) | SINGLE | consider | text: Methods "93.6% accuracy on held-out parcels" | re_analysis · evidence_gap_remains (claim) |
| R-118 | SC-52 | Rival explanations for dawn robbery are untested. **Min:** test whether the 04:00–06:00 share follows sunrise across months (no daylight saving since 2019); compare weekday and weekend dawn hours directly; use distance to bus stops as a proxy for target convergence (R2). DA: test guardianship directly (lighting, open businesses, bus stops as a class) and offender-side alternatives. | R2-W3 (maj/4); R2-Q5 (Q); DA-M6 (maj/4) | SINGLE +DA | must_fix | text: Results §Clock ¶2 "thus tracks the absence of guardians" | re_analysis (new_data option) · evidence_gap_remains (claim) |
| R-119 | SC-64 | The decline by place may restate offence mix (robbery −40%, theft −2%). **Min:** run the rate–composition decomposition separately for phone theft and phone robbery; report each class's theft/robbery mix; show Fig. 5e for each offence. | R2-W4 (maj/4); R2-W7 (maj/4); R2-Q1 (Q); R2-mi (min†/4‡) | SINGLE | must_fix | text: Results §Stable tissue ¶2 "through robbery (−40%) rather than theft (−2%)" | re_analysis · claim_scope_unsupported (claim) |
| R-120 | SC-60 | The residual may be missing composition (C1's alternative path). **Min:** show how much of it tract covariates and known unmeasured generators absorb (R2); test whether it concentrates where composition is incomplete, such as many unlinked establishments, proximity to favelas or informal-commerce proxies (R3); test its correlation with class shares (DA-M1). | R2-W5 (maj/4); R3-W4 (maj/3); R3-Q4 (Q); DA-C1 (crit/5); DA-M1 (maj/4) | CORR-2 +DA (DA-CRITICAL) | must_fix | text: Discussion ¶5 "The cadastre misses informal uses outside favelas." | re_analysis · claim_scope_unsupported (claim) |
| R-121 | SC-89 | The income audit pools theft and robbery. **Min:** run the income audit of the flagged area separately for robbery. | R2-W7 (maj/4) | SINGLE | must_fix | text: Results §Month-to-month ¶2 "36% of it lay in the top income quintile and 3% in the bottom" | re_analysis · claim_scope_unsupported (claim) |
| R-122 | SC-93 | Conditional on R-64. **Min:** if deaths from police intervention are included, model them as a separate phenotype. | R2-Q2 (Q); R3-W12 (min/3) | CORR-2 | consider | text: Results "lethal violence on low-income houses, vacant land and favelas" | re_analysis · claim_scope_unsupported (claim) |
| R-123 | SC-68 | Recording changes over 2022–2025 are unexamined. **Min:** examine reclassification between robbery and theft, and changes in reporting channels (online reports; phone-loss reporting after the blocking programme). | R2-Q4 (Q); DA-M4 (maj/4) | SINGLE +DA | should_fix | text: Results §Stable tissue ¶2 "Phone crime fell by 20% between 2022 and 2025" | re_analysis · claim_scope_unsupported (claim) |
| R-124 | SC-24 | The attribution is not compared head-to-head with a standard urban specification. **Min:** in ED Fig. 2, replace the comparator with a Goodman regression on composition shares and with direct parcel-level rates from geocoded events, then state what tract-level attribution adds (R3). DA: report in the main text a head-to-head against a segment-level NB land-use regression or RTM on the same validation. | R3-W1 (maj/4); R3-Q1 (Q); DA-M10 (maj/4); DA-alt8 (†) | SINGLE +DA | should_fix | figure: ED Fig. 2, attribution vs "Ecological regression by tract" | re_analysis · claim_scope_unsupported (claim) |
| R-125 | SC-92 | Favela rates rest on a constructed exposure (7.0 m). **Min:** report the sensitivity of favela enrichment to a plausible range of frontage values, or to household-based exposure. | R3-W3 (maj/3); DA-m11 (min/4) | SINGLE +DA | should_fix | text: Methods "times the median frontage of low-income parcels (7.0 m)" | re_analysis · claim_scope_unsupported (claim) |
| R-126 | SC-88 | Reporting bias is unbounded. **Min:** compute how steep an income gradient in reporting would have to be to reverse the class ranking or the Fig. 6f gap; calibrate against victimization data where possible; state which conclusions are robust, and that location-specific detection is identifiable only at coarse scale with outside calibration. | R3-W5 (maj/3); DA-M8 (maj/3) | SINGLE +DA | should_fix | text: Discussion ¶5 "Police records undercount crime unevenly" | re_analysis (new_data option) · claim_scope_unsupported (claim) |
| R-127 | SC-56 | Optional (R3). **Min:** fit cosinor models per class; report phase and amplitude; test differential rhythmicity. | R3-W6 (min/4) | SINGLE | consider | figure: Fig. 4a, hourly profiles per class | re_analysis · interpretive_ambiguity_remains (claim) |
| R-128 | SC-46 | Optional alternative to R-70. **Min:** report the matrix's condition number and test recovery of known tract composition from the crime mix in held-out tracts; state that the matrix must not be used to infer land use or residents from crime. | R3-W7 (min/5) | SINGLE | consider | figure: Fig. 3b, signature matrix | re_analysis · interpretive_ambiguity_remains (claim) |
| R-129 | SC-17 | Optional alternative to cutting the programs (R-89). **Min:** factorize the residual matrix after removing the counts expected from composition (the activity-program analogue). | R3-W10 (min/4) | CORR-2 (sub-claim) | consider | figure: Fig. 3d,e | re_analysis · interpretive_ambiguity_remains (figure) |
| R-130 | SC-85 | **Min:** show the income profile of flagged areas for the static historical map. | DA-m8 (min/4) | DA-only | consider | text: Results "as much as the historical mean (52%)" | re_analysis · claim_scope_unsupported (claim) |
| R-131 | SC-44 | **Min:** show that the signatures replicate across neighbouring Leiden resolutions and under the k-means baseline typing. | DA-m10 (min/4) | DA-only | consider | text: Results "so typing serves attribution and interpretation rather than prediction" | re_analysis · evidence_gap_remains (claim) |
| R-132 | SC-67 | **Min:** test whether the 2022–2025 trend is detectable per class and month. | DA-M4 (maj/4) | DA-only | should_fix | text: Results §Stable tissue ¶2 "It came from the diffuse fabric" | re_analysis · interpretive_ambiguity_remains (claim) |
| R-133 | SC-90 | **Min:** show that the key class contrasts hold for nearly fully recorded phenotypes (lethal violence; arguably vehicle theft) or within income strata. | DA-M8 (maj/3) | DA-only | should_fix | text: Discussion ¶5 "Police records undercount crime unevenly" | re_analysis · claim_scope_unsupported (claim) |

### 4.d Counts

| Category | Items | must_fix | should_fix | consider |
|---|---|---|---|---|
| (a) Text: rewrite, reframe or cut | 74 (R-01–R-74) | 34 | 21 | 19 |
| (b) Figure edits | 19 (R-75–R-93) | 1 | 8 | 10 |
| (c) New analyses | 40 (R-94–R-133) | 22 | 8 | 10 |
| **Total** | **133** | **57** | **37** | **39** |

Every item traces to at least one report entry; none is synthesizer-authored. Several (c) items are conditional (R-94, R-122) or optional (R-111, R-127–R-129), as their sources state.

### 4.e Source-traceability checklist (immutable order; no work order implied)

The author records `will_address`, `wont_address` or `not_on_point` later, in the separate author-adjudication sidecar.

- **must_fix (57)**:
  - (a) R-01, R-04, R-06, R-07, R-08, R-14, R-15, R-16, R-20, R-23, R-25, R-27, R-28, R-31, R-32, R-34, R-35, R-36, R-37, R-38, R-39, R-40, R-41, R-42, R-43, R-47, R-49, R-53, R-54, R-55, R-56, R-57, R-66, R-67
  - (b) R-87
  - (c) R-95, R-96, R-97, R-98, R-99, R-100, R-101, R-102, R-103, R-104, R-105, R-106, R-107, R-108, R-109, R-110, R-112, R-113, R-118, R-119, R-120, R-121
- **should_fix (37)**:
  - (a) R-02, R-03, R-05, R-09, R-10, R-11, R-12, R-13, R-17, R-18, R-19, R-21, R-44, R-45, R-50, R-59, R-61, R-63, R-65, R-68, R-74
  - (b) R-75, R-76, R-77, R-78, R-79, R-80, R-81, R-82
  - (c) R-94, R-115, R-123, R-124, R-125, R-126, R-132, R-133
- **consider (39)**:
  - (a) R-22, R-24, R-26, R-29, R-30, R-33, R-46, R-48, R-51, R-52, R-58, R-60, R-62, R-64, R-69, R-70, R-71, R-72, R-73
  - (b) R-83, R-84, R-85, R-86, R-88, R-89, R-90, R-91, R-92, R-93
  - (c) R-111, R-114, R-116, R-117, R-122, R-127, R-128, R-129, R-130, R-131

---
## 5. Editorial Decision Letter

Dear Author(s),

Thank you for submitting your manuscript, "Crime as a phenotype of urban tissue", to *Nature Cities* (simulated review). It was reviewed by five role-separated seats: a Journal-Fit Reviewer, a methodology reviewer, a domain reviewer, a cross-disciplinary reviewer and a fixed Devil's Advocate. All five ran in separate contexts on the same model family and provider, with no accountable human behind any seat. Their agreement is therefore not independent confirmation; see the provenance section above.

### Decision: **Major Revision**

### What the reviewers valued

All five seats commend the design safeguards, which are rare in crime-and-place research:
- parcel typing fixed without crime data;
- a spatial and a temporal vault behind a pre-specified, Holm-corrected confirmatory family;
- district block bootstrap and proper scoring rules;
- a traffic-injury positive control;
- an equivalence audit that reports where the omics analogy ties or loses.

They also regard as new, and of broad interest for a Global South megacity:
- the class-resolved crime signatures;
- the class-specific daily profiles tested against a crowd denominator;
- the noise ceiling separating "where" from "when within a place";
- the income-quintile audit of forecasts.

The pending confirmatory test and the deliberate placeholders were not held against the manuscript.

### Consensus analysis

- **Unanimous among the four scoring reviewers** (and joined by the Devil's Advocate):
  - "month-to-month crime is noise" reads non-rejection of a low-power test as confirmation (SC-70);
  - the mobility "limit of predictability" (ref. 41) is a different quantity (SC-77).
- **Three of four**:
  - the analogy's listed additions include classical methods, and the closest criminological precursors are not engaged (SC-21, SC-22);
  - one city-wide rate per class is assumed but untested (SC-34);
  - guardianship is inferred rather than measured (SC-50);
  - "memory" implies a state dependence the decomposition cannot identify (SC-58, SC-62);
  - "niche" is used in two senses (SC-66);
  - the dispersion test needs a power analysis (SC-71).
- A further 33 sub-claims are corroborated by two scoring reviewers (§3.4).

### Points of disagreement and the editor's resolutions

- **Independence of the point validation.** R1 and the Journal-Fit Reviewer say the validation reuses the fitted events; R3 treats it as independent. *Resolved for R1* on the Methods text: the validation must be described as a consistency check, and a held-out validation added (R-25, R-95).
- **Hub concentration of extra-Poisson variance.** R1 says it may be a scale effect; R3 calls it well supported. *Resolved for R1, conditionally*: keep the claim only if it survives the common-θ comparison (R-104).
- **Knox near-repeat analysis.** R1 would cut it; R2 would bring it into the main text. *Your choice*: either bring it in with Methods, or cut it and restrict the noise claim (R-49, R-56).
- **The 04:00–06:00 recommendation.** R3 values its non-police orientation; the other seats find it beyond the evidence. *Combined*: keep non-police measures, but as hypotheses to test, and drop the evening-patrol comparison (R-15).
- **Event-study placement.** The Journal-Fit Reviewer and R1 would move it to Extended Data; the DA would treat it as a test of the thesis. *Your choice*, with R1's corrections in either case (R-04, R-112).

### Devil's Advocate critical issue

**C1 is VALIDATED.** The Discussion says composition "fixes" a place's rate, yet your own estimates show:
- tissue accounts for 42% of between-tract variance against 48% for the persistent residual (and 18% against 58% in high-crime tracts);
- tract history out-predicts tissue (R² 0.48 against 0.25).

The defect is repairable. Please either narrow the thesis and title, or show that the residual is unmeasured composition. In both cases, report the tissue–memory cross-term (R-08, R-32, R-110, R-120).

### Decision rationale

The decision follows mechanically from the reviewer contract:
- Three mandatory dimensions carry a repairable block from their eligible seats: D1 methodology (R1), D2 domain accuracy (R2) and D3 argumentative coherence (R1 and the Devil's Advocate). Condition F2 therefore fires and sets Major Revision. F3 and F5 also fire but rank lower.
- No seat declared a fatal block, so Reject (F1) does not fire.
- Accept is unavailable twice over: F0 fails, and the validated critical item C1 blocks it.
- The decision matches every scoring reviewer's own signal.

**Minor Revision is not available** because the repairs go beyond wording:
- **R1's block** rests on three problems. The constant class rate is untested, as is recovery accuracy. The point validation reuses most of the fitted events. And the reconciliation of non-geocoded events, by lagged geocoded counts, can manufacture persistence and Poisson-like counts. Each needs re-analysis.
- **R2's block** rests on readings that contradict or ignore established crime-and-place evidence without saying so: the guardianship mechanism, the place reading of the decline, "memory", the generalised noise claim, unqualified recording bias and the hot-spot comparison.
- **The Devil's Advocate** shows that the thesis as worded is stronger than your own decomposition and out-of-sample results.

**Reject is not warranted**:
- every seat classes its block as repairable;
- no fatal trigger is met;
- the remedies are narrower wording plus analyses your data already support.

The four arbitrated disagreements do not change the decision. The revised manuscript will return to the same seats for re-review.

### Blocking issues (0–3, immutable source order)

| Transport ref | Blocking issue | Source reviewer(s) | Evidence anchor | Resolving roadmap items |
|---|---|---|---|---|
| B-1 | D1: attribution identification, validation and inference are not yet sound. The single city-wide rate is untested; point validation reuses the fitted events; reconciliation may build persistence and damp variance; the clock null, dispersion test, hub claim and ceilings lack valid uncertainty or power. | R1 (D1 block); corroborated by R2-W2, R3-W1, DA-M1/M2/M5 | text: Methods §Units and reconciliation "events without coordinates were distributed among tracts in proportion to the geocoded events of the same stratum over the preceding 12 months" | R-25, R-36–R-40, R-42, R-95–R-110, R-112 |
| B-2 | D3: headline claims outrun the paper's own statistics. Composition "fixes" rates (C1); crime "is noise"; the city is "close to its limit of predictability"; an exploratory robbery clock leads the abstract; "memory". | R1 (D3 block), DA (D3 block, C1 validated); corroborated by EIC-W4/W6/W17/W20, R2-W5/W6, R3-W2/W4 | text: Discussion ¶1 "The composition of a place fixes its rate, which crimes it produces and at what hour." | R-01, R-08, R-14, R-28, R-31, R-32, R-35, R-41, R-43, R-66, R-67, R-102, R-103, R-110, R-120 |
| B-3 | D2: the criminological reading goes beyond or contradicts established evidence without acknowledging it. This covers the gap statement, positioning, guardianship, the decline, memory, the scope of the noise claim, recorded-crime bias and the prevention claims. | R2 (D2 block); corroborated by EIC-W2/W16, R3-W1/W5, DA-M4/M6/M8 | text: Results §Clock ¶2 "Dawn robbery in the periphery thus tracks the absence of guardians … rather than the volume of targets." | R-06, R-07, R-15, R-16, R-20, R-27, R-47, R-49, R-53–R-57, R-113, R-118–R-121 |

**Acceptance criteria**:
- **B-1** is resolved when R-95 to R-110 are reported, the dependent claims are revised to match, and R1 judges D1 and D3 no longer blocked.
- **B-2** is resolved when the title, abstract, headings and Discussion state only what the revised analyses support, and the DA and R1 judge D3 no longer blocked.
- **B-3** is resolved when each listed interpretation is reworded, cited and, where requested, tested, and R2 judges D2 no longer blocked.

### Required revisions (must_fix, roadmap order)

Each item's minimum remedy is given in §4. Its acceptance criterion is that the minimum remedy is present in the revised manuscript (for analyses: reported, with the dependent text revised to match) and that the source seat judges the finding resolved at re-review.

- **Text (a)**:
  - R-01 one spine;
  - R-04 event-study claims;
  - R-06 classical lineage of the analogy's additions;
  - R-07 criminological precursors;
  - R-08 declarative title;
  - R-14 robbery clock as lead example;
  - R-15 dawn recommendation as hypothesis;
  - R-16 guardianship wording;
  - R-20 "niche";
  - R-23 one ceiling term;
  - R-25 validation framed as a consistency check;
  - R-27 hot-spot claims;
  - R-28 noise wording;
  - R-31 18% tissue share in high-crime tracts;
  - R-32 narrowed thesis;
  - R-34 "marginal changes";
  - R-35 ref. 41 analogy;
  - R-36 validation scope;
  - R-37 reconciliation details;
  - R-38 reconciliation-dependent signatures;
  - R-39 identification assumptions;
  - R-40 dispersion-test specification;
  - R-41 "close to its limit";
  - R-42 P ≤ 0.005;
  - R-43 rename "memory";
  - R-47 rival explanations for dawn robbery;
  - R-49 Knox;
  - R-53 gap statement;
  - R-54 decline interpretation;
  - R-55 heterogeneity vs state dependence;
  - R-56 scope of the noise claim;
  - R-57 recorded-crime bias;
  - R-66 sampling-noise analogy;
  - R-67 "produces" and the analogy's break.
- **Figures (b)**: R-87 ceiling keys.
- **Analyses (c)**:
  - R-95 held-out validation;
  - R-96 validation intervals;
  - R-97 geocoded-only re-runs;
  - R-98 reconciled shares;
  - R-99 recovery simulation;
  - R-100 spatially varying rates;
  - R-101 collinearity and boundary diagnostics;
  - R-102 hierarchical month-to-month variation;
  - R-103 power;
  - R-104 hub concentration test;
  - R-105 geocode defaults;
  - R-106 ceiling intervals;
  - R-107 block-permutation clock;
  - R-108 confirmatory criteria and OSF registration;
  - R-109 robbery-clock checks;
  - R-110 variance components and cross-term;
  - R-112 event-study intervals;
  - R-113 denominator uncertainty;
  - R-118 dawn-robbery tests;
  - R-119 decline by offence;
  - R-120 residual vs missing composition;
  - R-121 robbery-only income audit.

### Suggested revisions

- **should_fix (37)** and **consider (39)** are listed in §4.e.
- Please respond to each. Where you decline an item, give a reason; declining is visible and recorded as unresolved, not forbidden.
- Several suggested references are flagged `[UNVERIFIED]` by the reviewers. Verify each before citing it.

### Journal-supplied deadline

- **Exact deadline from source letter**: NOT PROVIDED. No deadline or work estimate is inferred.

### Response letter instructions

Use the format in `templates/revision_response_template.md` and respond to every roadmap item by its R-NN identifier. Include:
1. the response and revision for each must_fix item;
2. a response to each should_fix and consider item, adopted or with the reason for declining;
3. tracked changes in the revised manuscript;
4. a table cross-referencing the new paragraph and figure locations;
5. for each disagreement D-1 to D-5 and for C1, which path you took and why.

### Closing

We encourage you to consider the reviewers' comments carefully and to submit a substantially revised manuscript. The revised manuscript will undergo another round of review by the same seats. Because the confirmatory test is pending by design, the re-review will assess the revised exploratory claims and the amended confirmatory protocol (R-108) before the vault is opened.

Sincerely,
Editorial Synthesizer (simulated panel, ARS v3.23.1)

---

## Appendix: Reviewer Report Summaries

### Journal-Fit Review Report Summary
- Recommendation: Major Revision | Confidence: 4 | D5 warn, D6 warn
- Key point: the paper fits the venue and is within every format limit. Its framing sells the analogy rather than the urban finding; secondary analyses dilute one story; and names, comparators, data scope and evidence status drift across sections.

### Reviewer 1 (Methodology) Summary
- Recommendation: Major Revision | Confidence: 4 | D1 block, D3 block (repairable)
- Key point: strong safeguards, but the validation is circular, the attribution's assumptions are untested, reconciliation contaminates the memory and noise analyses, and the 96% result is a power artefact read as confirmation. All of this is repairable with re-analysis and reframing.

### Reviewer 2 (Domain) Summary
- Recommendation: Major Revision | Confidence: 4 | D2 block (repairable)
- Key point: the empirical work is careful, but the guardianship, decline, memory and noise readings go beyond or contradict crime-and-place evidence. The gap and novelty are framed against a mischaracterised field. Recording bias is unused.

### Reviewer 3 (Perspective) Summary
- Recommendation: Major Revision | Confidence: 4 | D4 warn
- Key point: the analogy is run honestly as an instrument. Attribution, though, is ecological regression; "intrinsic noise", "memory", "clock" and "signature matrix" are loose; and ethics beyond privacy (territorial stigma, differential reporting) is missing.

### Devil's Advocate Summary
- Recommendation: N/A (findings only) | D3 block (repairable)
- Key challenge: C1, VALIDATED. The paper's own estimates make tissue the minority component of stable variation and a weaker predictor than crime history, so "composition fixes its rate" must be narrowed, or the residual shown to be unmeasured composition. Eleven MAJOR and twelve minor findings are all retained.
