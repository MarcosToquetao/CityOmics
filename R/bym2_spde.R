# BYM2 (epidemiologia: mapeamento de doenças) e SPDE/Matérn (LGCP em grade de setores) com R-INLA.
# Lê um CSV agregado por setor (contagem no período de ajuste, covariáveis padronizadas, centroides)
# e uma lista de arestas (vizinhança de contiguidade); escreve a média ajustada por setor.
# Uso: Rscript R/bym2_spde.R <entrada.csv> <arestas.csv> <saida.csv> [bym2|spde|ambos]
suppressMessages({library(INLA); library(data.table)})
args <- commandArgs(trailingOnly = TRUE)
d <- fread(args[1]); e <- fread(args[2]); modo <- ifelse(length(args) >= 4, args[4], "ambos")
inla.setOption(num.threads = "8:1")
covs <- setdiff(names(d), c("cd_setor", "y", "meses", "cx", "cy", "id", "area_km2"))
d[, id := .I]
form_cov <- paste(covs, collapse = " + ")
out <- data.table(cd_setor = d$cd_setor)

if (modo %in% c("bym2", "ambos")) {
  n <- nrow(d)
  g <- sparseMatrix(i = e$i, j = e$j, x = 1, dims = c(n, n)); g <- g + t(g); g[g > 1] <- 1
  f <- as.formula(paste("y ~", form_cov, "+ f(id, model='bym2', graph=g, scale.model=TRUE, constr=TRUE,",
                        "hyper=list(prec=list(prior='pc.prec', param=c(1, 0.01)), phi=list(prior='pc', param=c(0.5, 0.5))))"))
  m <- inla(f, family = "poisson", data = d, E = d$meses * d$area_km2^0, control.predictor = list(compute = TRUE),
            control.compute = list(config = FALSE), control.inla = list(strategy = "gaussian", int.strategy = "eb"), verbose = FALSE)
  out[, bym2 := m$summary.fitted.values$mean / d$meses]
  cat("BYM2 hiperparâmetros:\n"); print(m$summary.hyperpar[, c("mean", "0.025quant", "0.975quant")])
}
if (modo %in% c("spde", "ambos")) {
  loc <- as.matrix(d[, .(cx, cy)])
  mesh <- inla.mesh.2d(loc = loc, cutoff = 250, max.edge = c(900, 4000), offset = c(2000, 8000))
  cat("malha SPDE:", mesh$n, "nós\n")
  spde <- inla.spde2.pcmatern(mesh, prior.range = c(2000, 0.5), prior.sigma = c(1, 0.01))
  A <- inla.spde.make.A(mesh, loc)
  idx <- inla.spde.make.index("s", spde$n.spde)
  X <- as.data.frame(d[, ..covs])
  stk <- inla.stack(data = list(y = d$y), A = list(A, 1), effects = list(idx, c(list(Intercept = 1), X)), tag = "est")
  f2 <- as.formula(paste("y ~ -1 + Intercept +", form_cov, "+ f(s, model = spde)"))
  m2 <- inla(f2, family = "poisson", data = inla.stack.data(stk), E = rep(d$meses, 1),
             control.predictor = list(A = inla.stack.A(stk), compute = TRUE), control.compute = list(config = FALSE),
             control.inla = list(strategy = "gaussian", int.strategy = "eb"), verbose = FALSE)
  ix <- inla.stack.index(stk, "est")$data
  out[, spde := m2$summary.fitted.values$mean[ix] / d$meses]
  cat("SPDE hiperparâmetros:\n"); print(m2$summary.hyperpar[, c("mean", "0.025quant", "0.975quant")])
}
fwrite(out, args[3])
