# Data

All inputs are public. None of them is stored in this repository: the code downloads them, or reads copies placed in `data/external/` and `data/raw/`. The two files in `data_manifest/` record, for each file, the URL it came from, when it was downloaded, its size and its SHA-256 checksum:

- `data_manifest/ssp_snapshot.json`: the police-report spreadsheets;
- `data_manifest/external_manifest.json`: every other input (265 files).

Providers update and republish some of these files. The checksums tell whether a new download matches the version used in the article; they cannot recover an older version once a provider replaces it.

## Sources used in the article

| Data | Provider | Years | Used for |
|---|---|---|---|
| Police-report microdata: main base, mobile-phone thefts and robberies, lethal violence | São Paulo State Secretariat of Public Security (SSP), transparency portal | 2022–2026 | Crime counts, the phenotype |
| Fiscal parcels, property-tax cadastre (IPTU), streets, rail and bus stations, favelas | São Paulo City Hall, GeoSampa geoportal | Cadastre 2012–2025 | Cells, parcel attributes, street and station classes |
| Business establishments (CNPJ) | Federal Revenue Service of Brazil | Snapshot of December 2025 | Business activity of each parcel |
| Census tracts and tract aggregates | Brazilian Institute of Geography and Statistics (IBGE), 2022 Census | 2022 | Spots and tract covariates |
| Origin–Destination survey | Metrô de São Paulo | 2023, with 2017 as a sensitivity check | Ambient population |

## Sources used only in the forecasting benchmark or in exploratory analyses

| Data | Provider |
|---|---|
| Property transfer tax records (ITBI) | São Paulo City Hall, Department of Finance |
| SP156 service requests | São Paulo City Hall, open data portal |
| Social vulnerability index (IPVS) | Fundação SEADE |
| 2010 Census tract aggregates and CNEFE address register | IBGE |
| Bank branches | Central Bank of Brazil |
| Road network and points of interest | OpenStreetMap contributors, via Geofabrik and Overpass |
| Night-time lights (VIIRS Black Marble, VNP46A3) | NASA |
| Daily weather (ERA5 reanalysis) | Copernicus Climate Change Service, via Open-Meteo |

Exact URLs are in `data_manifest/`. OpenStreetMap data are licensed under the Open Database Licence (ODbL), which requires attribution and asks that derived databases be shared under the same licence. Brazilian public-sector data are published under the Access to Information Law (Law 12.527/2011). [Check the terms of each remaining source before deposit.]

## What is not redistributed, and why

Police-report microdata hold report numbers, street addresses and coordinates. They are public, but placing them in a second repository would make individual events easier to find and link. They are processed on a local machine and only aggregates leave it.

To rebuild the analysis, download the spreadsheets from the SSP transparency portal and check them:

```bash
cityomics ingest snapshot
cityomics ingest snapshot --verify
```

## The 2026 vault

Records dated 2026 are split off at ingestion and stored in `data/sealed_2026/`. The code refuses to read them unless both keys match (see the README). The access log of the vault is registered on OSF [OSF DOI].

## Deposited outputs (Zenodo, https://doi.org/10.5281/zenodo.23778485)

| Content | Level |
|---|---|
| Composition of each census tract in the 23 cell classes | Tract |
| Attributes and marker variables of the 16 parcel types | Type |
| Crime profile, daily rhythm and risk per pedestrian of each cell class | Class |
| Summary results of the atlas analyses and of the confirmatory test | Summary statistics |
| Tables plotted in Figs. 2 and 5 | As plotted |
| Benchmark scores | Model |
| Frozen forecasting models, with their manifest and checksums | Model |

The deposit holds only what the study produced. Crime counts and other figures that the public bodies already publish are not copied; they can be rebuilt from the sources above. Per-tract crime risk is not published, in line with the article.

Licence of the deposited outputs: CC BY 4.0.
