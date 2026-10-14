# Pacotes R do CityOmics (D9). R é usado só onde é claramente superior,
# lendo e escrevendo Parquet (via arrow) para conversar com o pacote Python.
#
# Uso: Rscript R/install.R
# Depois de instalar, congelar versões com: renv::init(); renv::snapshot()

options(repos = c(CRAN = "https://cloud.r-project.org"), Ncpus = 4, timeout = 3600)  # INLA tem ~80 MB num servidor lento

cran <- c(
  "arrow",         # interface Parquet com o Python
  "sf", "spdep",   # geometria e vizinhança
  "scoringRules",  # CRPS da binomial negativa (spec-benchmark §4)
  "surveillance",  # testes de calibração e Knox
  "ETAS",          # processos auto-excitáveis
  "renv"
)
install.packages(setdiff(cran, rownames(installed.packages())))

# R-INLA não está no CRAN (BYM2 / Knorr-Held; spec-benchmark §3.2, spec-atlas §3.2)
if (!requireNamespace("INLA", quietly = TRUE)) {
  install.packages(
    "INLA",
    repos = c(getOption("repos"), INLA = "https://inla.r-inla-download.org/R/stable"),
    dependencies = c("Depends", "Imports", "LinkingTo")
  )
}
