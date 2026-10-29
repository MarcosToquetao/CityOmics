# CityOmics

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23778357.svg)](https://doi.org/10.5281/zenodo.23778357)

Code for the article "Crime as a phenotype of urban tissue" (Toquetão & Nakaya, in review).

The study reads São Paulo with the tools of spatial transcriptomics. Fiscal parcels play the role of cells, census tracts are spots of known composition, and police records of 15 crime types are the phenotype. From areal counts, the pipeline estimates which crimes each class of parcel hosts and at what hour, how much of a tract's crime persists beyond its composition, and how well month-to-month counts can be forecast.

- Article: [DOI after publication]
- Code archive: Zenodo, https://doi.org/10.5281/zenodo.23778357 (all versions; v1.0.1, the version cited in the article: https://doi.org/10.5281/zenodo.23779225)
- Aggregated data and frozen models: Zenodo, https://doi.org/10.5281/zenodo.23778485
- Preregistration, amendments and freeze manifests: `prereg/`, archived with the code at Zenodo

## Repository layout

```
src/cityomics/   Python package and the `cityomics` command-line tool
  ingest/          police-report microdata from the São Paulo Secretariat of Public Security (SSP)
  units/           census tracts, districts, parcels and assignment of events
  covariates/      cadastre, business registry, census and other covariates
  features/        modelling table for the forecasting benchmark
  models/          forecasting models, benchmark, selection and frozen models
  atlas/           parcel types, niches, attribution, rhythms, persistent effects
  eval/            scores, calibration, hotspot and fairness metrics
  sealed.py        vault that locks records dated 2026
  privacy.py       scan for secrets and identifying columns
R/               R-INLA models (BYM2, SPDE), exchanging files with Python
notebooks/colab/ thin notebooks for the GPU steps
figures/         one script per figure
prereg/          analysis plan, amendments, selections and freeze manifests
data_manifest/   URL, access date and SHA-256 of every input file
tests/           test suite
docs/            design notes for each stage (in Portuguese)
```

Code comments and the design notes in `docs/` are written in Portuguese.

## Installation

Tested on Linux (x86-64) with conda-forge. The Python environment:

```bash
mamba env create -f environment.yml
conda activate cityomics
```

The environment installs the package in editable mode.

To reproduce the exact versions used in the article, build it from the lock files instead:

```bash
mamba create -n cityomics --file conda-linux-64.lock
conda activate cityomics
pip install -r requirements-pip.lock
pip install -e .
```

The R environment, used for the INLA models:

```bash
mamba env create -f environment-r.yml
mamba run -n cityomics-r Rscript R/install.R
```

Check the installation:

```bash
cityomics info
pytest
```

## Data

The inputs are public, but the repository does not ship them. [DATA.md](DATA.md) lists each source with its provider and terms of use. The files in `data_manifest/` give the URL, access date and SHA-256 checksum of every file, so a fresh download can be checked against the version used in the article.

Police-report microdata contain report numbers and addresses. They are processed on a local machine and never leave it; only aggregates are published. The aggregated outputs, the tables behind Figs. 2 and 5 and the frozen models are on Zenodo (https://doi.org/10.5281/zenodo.23778485).

The inputs take about 31 GB of disk once downloaded and processed.

## Reproducing the analysis

Run the stages in order. Each one reads the outputs of the previous one from `data/`.

| Stage | Command | Notes |
|---|---|---|
| 1. Ingest police reports | `cityomics ingest snapshot`, then `cityomics ingest parse`, then `cityomics ingest check` | `snapshot --verify` compares the downloaded files with the recorded checksums; `check` compares annual totals with the official SSP tables |
| 2. Units | `cityomics units build`, then `cityomics units lotes --download` | Tracts, districts and assignment of events; then fiscal parcels and favela pseudo-parcels |
| 3. Covariates | `cityomics covariates iptu --download` | Property-tax cadastre, one file per year |
| 4. Forecasting benchmark | See `docs/F5_benchmark.md` | Runs through the Python API (`cityomics.models.benchmark_run`, `select_run`, `letal_run`); no command-line entry yet |
| 5. Atlas | `cityomics atlas run` | Steps in order: genes, ruas, tipagem, spots, nichos, atribuicao, variancia, preditores, comunicacao, destino, letal |
| 6. Freeze | `cityomics freeze check`, then `cityomics freeze models` | Writes the frozen models to `data/models/frozen/`; the fine-tuned weights trained in Colab are identified by their SHA-256 |
| 7. Figures | `cityomics figures --periodo dev` | Writes vector PDF and 450 dpi PNG to `figures/out/dev/` |

Steps that need a GPU run in Google Colab through the notebooks in `notebooks/colab/`, whose README lists them. Only aggregated, anonymous tables are uploaded there.

The article was produced on a workstation with 12 CPU cores and 30 GB of RAM, with the GPU steps in Colab.

### Figures

| Figure | Script | Command |
|---|---|---|
| Fig. 1 | `figures/fig1.py` | `cityomics figures --only fig1` |
| Fig. 2 | `figures/fig2.py` | `cityomics figures --only fig2` |
| Fig. 3 | `figures/fig3.py` | `cityomics figures --only fig3` |
| Fig. 4 | `figures/fig4.py` | `cityomics figures --only fig4` |
| Fig. 5 | `figures/fig5.py` | `cityomics figures --only fig5` |
| Fig. 6 | `figures/fig6.py` | `cityomics figures --only fig6` |
| Extended Data Figs. 1–10 | `figures/ed.py`, `figures/ed_b.py` | `cityomics figures --only ed` |

## Preregistration and the 2026 vault

The analysis plan, its dated amendments and the hashes of frozen inputs and models are in `prereg/`. Records dated 2026 were sealed at ingestion. Reading them needs two keys: the file `prereg/UNSEAL_KEY`, which holds the hash of the commit that froze the models (`FREEZE-CDE1BDA`), and an environment variable with the same value. Every opening is logged. The vault had not been opened when the article was submitted; the log will be added to this repository once it is (amendment A14 in `prereg/AMENDMENTS.md`).

Because the key is a commit hash, the history of this repository is part of the record. Commit `cde1bda` shows what was frozen and when; the git history has not been rewritten.

## Privacy

Report numbers, addresses and coordinates stay on the local machine. Public outputs are aggregated to tracts, districts or classes of place, tract-level crime maps are rasterized, and no per-tract crime risk is published. Before each upload or commit, `cityomics privacy-scan` looks for secrets in the repository and for identifying columns in `data/processed/`.

The class profiles describe where crimes are recorded. They are not meant for area-wide policing or for drawing conclusions about the people who live in a place.

## Use of AI assistance

The analysis code, tests and figure scripts were written with Claude (Anthropic) under the authors' direction. The Methods section of the article ("Use of large language models") describes this use in full.

## Citation

If you use this code, please cite the article and the archived version of the code. GitHub shows both under "Cite this repository", from [CITATION.cff](CITATION.cff).

## Licence

Code: MIT ([LICENSE](LICENSE)). Text, figures and derived data: CC BY 4.0. The input data keep the terms of their providers ([DATA.md](DATA.md)).

## Contact

Marcos Lemes Toquetão, Innovation Center, University of São Paulo (InovaUSP). Please open a GitHub issue for questions about the code.
