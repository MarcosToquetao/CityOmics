"""Hawkes/ETAS em tempo discreto com covariáveis (sismologia; spec-benchmark §3.2).

Em escala mensal e por setor, o processo autoexcitado vira

    λ[i, m] = μ[i, m] + Σ_L κ_L · y[i, m − L] + Σ_L η_L · ȳ_viz[i, m − L]

com intensidade de fundo ``μ = exp(β·x)`` (covariáveis as-of e sazonalidade) e núcleo de excitação
nos lags disponíveis (1, 2, 3, 6, 12 meses; as intensidades as-of já corrigem a cobertura). ``κ`` é a
excitação própria e ``η`` a propagação para vizinhos (contágio espacial, estilo ETAS). A
verossimilhança é Poisson com sobredispersão tratada depois por dispersão NB global. Os parâmetros
são ajustados por máxima verossimilhança com L-BFGS (PyTorch), κ e η ≥ 0 por softplus.

Limitação declarada: sem o tempo contínuo e o ponto do evento, é a versão agregada do Hawkes
(equivale a um modelo autorregressivo de contagem com núcleo parametrizado).
"""

from __future__ import annotations

import numpy as np
import polars as pl
import torch

LAGS = ("h_int_l1", "h_int_l2", "h_int_l3", "h_int_l6", "h_int_l12")
NB_LAGS = ("nb_h_int_l1", "nb_h_int_s3", "nb_h_int_s12")


class Hawkes:
    def __init__(self, bg_cols: list[str]):
        self.bg_cols = bg_cols
        self.mean = None
        self.std = None

    def _bg(self, df: pl.DataFrame) -> np.ndarray:
        x = df.select(self.bg_cols).to_numpy().astype("float64")
        x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
        x = np.sign(x) * np.log1p(np.abs(x))          # estabiliza caudas pesadas
        if self.mean is None:
            self.mean, self.std = x.mean(0), x.std(0) + 1e-6
        return (x - self.mean) / self.std

    def _hist(self, df: pl.DataFrame) -> np.ndarray:
        h = df.select(list(LAGS) + list(NB_LAGS)).to_numpy().astype("float64")
        return np.nan_to_num(h, nan=0.0)

    def fit(self, df: pl.DataFrame, iters: int = 120, seed: int = 0) -> "Hawkes":
        torch.manual_seed(seed)
        xb = torch.tensor(self._bg(df), dtype=torch.float32)
        hh = torch.tensor(self._hist(df), dtype=torch.float32)
        mes = torch.tensor(df["mes_num"].to_numpy().astype("int64") - 1)
        area = torch.tensor(np.log(df["area_km2"].to_numpy() + 1e-3), dtype=torch.float32)
        y = torch.tensor(df["y"].to_numpy(), dtype=torch.float32)
        self.beta = torch.zeros(xb.shape[1], requires_grad=True)
        self.b0 = torch.tensor(-3.0, requires_grad=True)
        self.sea = torch.zeros(12, requires_grad=True)
        self.ba = torch.tensor(0.0, requires_grad=True)
        self.kappa = torch.full((hh.shape[1],), -2.0, requires_grad=True)   # softplus^-1 do núcleo
        params = [self.beta, self.b0, self.sea, self.ba, self.kappa]
        opt = torch.optim.LBFGS(params, lr=0.5, max_iter=iters, line_search_fn="strong_wolfe")

        def nll():
            opt.zero_grad()
            lam = self._intensity(xb, hh, mes, area)
            loss = (lam - y * torch.log(lam + 1e-9)).mean() + 1e-4 * (self.beta ** 2).sum()
            loss.backward()
            return loss

        opt.step(nll)
        return self

    def _intensity(self, xb, hh, mes, area):
        bg = torch.exp(xb @ self.beta + self.b0 + self.sea[mes] + self.ba * area)
        exc = (torch.nn.functional.softplus(self.kappa) * hh).sum(dim=1)
        return bg + exc + 1e-6

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        with torch.no_grad():
            xb = torch.tensor(self._bg(df), dtype=torch.float32)
            hh = torch.tensor(self._hist(df), dtype=torch.float32)
            mes = torch.tensor(df["mes_num"].to_numpy().astype("int64") - 1)
            area = torch.tensor(np.log(df["area_km2"].to_numpy() + 1e-3), dtype=torch.float32)
            return self._intensity(xb, hh, mes, area).numpy().astype("float64")

    def kernel(self) -> dict[str, float]:
        k = torch.nn.functional.softplus(self.kappa).detach().numpy()
        return dict(zip(list(LAGS) + list(NB_LAGS), map(float, k)))
