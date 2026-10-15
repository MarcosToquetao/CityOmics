# Amendments

Dated changes to the pre-registration, recorded before the first unsealing of the 2026 vault. Each entry also goes to OSF.

| Date | Section | Change | Reason |
|---|---|---|---|
| 2026-10-15 | 2.1 Datasets | A1. Census 2010 enters as tract aggregates converted to 2022 tracts by CNEFE-address dasymetric weights, not via the 200 m statistical grid | The grid has only population and dwellings; the tract files have age, race, literacy and income |
| 2026-10-15 | 4.1 Predictors | A2. Metrô ridership removed from the theory core; replaced by distance to rail stations. ATMs dropped (BCB branches and OSM bank POIs only) | Public Metrô data cover lines 1, 2, 3 and 15 only; no open ATM address list |
| 2026-10-15 | 2.1 Datasets | A3. Weather = ERA5 reanalysis (Open-Meteo) instead of INMET/CGE; OSM as a static 2026 snapshot (no ohsome history); lighting as a single 2026 LED snapshot; calendar without home games and events | Sources were unavailable, require registration or have no open history |
| 2026-10-15 | 2.1 Datasets | A4. SP156 used from 2015 to 2026-Q3 (2012–2014 not used). Coordinate coverage varies from ~95% (≤ 2019) to 10–63% (2020–2026); counts are divided by the monthly coverage | Source layout changed in 2020–2021 |
| 2026-10-15 | 4.1 Predictors | A5. CNPJ exits excluded from the core: mass deregistration in 2018 (361k exits vs 72k in 2017). Establishment stocks reflect final registration status and current address only | Receita publishes only the final status |
| 2026-10-15 | 2.3 / 5.3 | A6. Primary observation fixed to the reconciled real-valued count (`n_total`); CRPS computed against real-valued y; Brier event 1{n_total ≥ 0.5}; PAI ranks tracts by predicted mean per km² | The reconciled count is not an integer; the metrics needed explicit definitions |
| 2026-10-15 | 4.1 Predictors | A7. Core covariate list frozen in `prereg/core_covariates.json` before any model was fitted | D12 requires the core to be fixed before modelling |
| 2026-10-15 | 7 Timeline | A8. Freeze mechanics: `cityomics freeze commit` writes `prereg/FREEZE_MANIFEST.json` (input, lock and model hashes plus selected best-in-class identities) and the vault accepts only a `FREEZE-<sha>` whose commit contains a complete manifest | Prevents opening the vault with an arbitrary commit |
| 2026-10-15 | 4.3 | A9. Sample sizes updated to 27,301 tracts (245,700 validation tract-months) | Final tract count |
| 2026-10-15 | 4.2 Models | A10. MaxEnt runs with a uniform background over tracts (presence-only against area), not a target-group background; LGCP is approximated by the SPDE log-Gaussian model in INLA on tract centroids; Chronos-Bolt small is the zero-shot foundation model (no TimesFM) | No sampling-effort surface for a target-group background; INLA LGCP on 27k tracts × 36 months is infeasible without the approximation; Chronos is the single time-series foundation model that runs on the available hardware |
