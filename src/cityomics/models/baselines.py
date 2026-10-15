"""Baselines do benchmark (spec-benchmark §3.1; prereg §5.1).

Cada baseline produz uma previsão pontual ``x`` por setor × mês a partir só do histórico as-of.
Para virar distribuição, todos passam pela mesma calibração: ``mu = a·x + b`` com ``(a, b, phi)``
ajustados por máxima verossimilhança NB no período de ajuste (2024 para avaliar 2025; 2025 para
as previsões congeladas de 2026). Assim a comparação é entre as informações dos baselines, não
entre calibrações mais ou menos felizes.

- persistência: intensidade do mês anterior (``h_int_l1``);
- sazonal ingênuo: mesmo mês do ano anterior (``h_int_l12``);
- média histórica: média dos 12 meses anteriores (``h_int_s12 / 12``);
- STKDE: média dos últimos 6 meses suavizada por kernel gaussiano no espaço (largura escolhida no ajuste);
- hotspotting prospectivo: pesos por faixas de distância (Bowers e Johnson) sobre a mesma janela;
- GLM de contagem com lags temporais e espaciais (média Poisson por quase-verossimilhança + dispersão NB).
"""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy import optimize, special
from scipy.spatial import cKDTree
from sklearn.linear_model import PoissonRegressor

from cityomics.eval import scores


def calibrate(x: np.ndarray, y: np.ndarray, max_rows: int = 400_000, seed: int = 0) -> tuple[float, float, float]:
    """(a, b, phi) de ``mu = a·x + b`` por máxima verossimilhança NB sobre ``y`` (arredondado)."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], np.rint(y[ok])
    if len(x) > max_rows:
        i = np.random.default_rng(seed).choice(len(x), max_rows, replace=False)
        x, y = x[i], y[i]

    def nll(t):
        a, b, phi = np.exp(t)
        mu = a * x + b
        ll = (special.gammaln(y + phi) - special.gammaln(phi) - special.gammaln(y + 1)
              + phi * np.log(phi / (phi + mu)) + y * np.log(mu / (phi + mu)))
        return -ll.sum()

    r = optimize.minimize(nll, np.log([1.0, 0.01, 1.0]), method="L-BFGS-B", bounds=[(-6, 3), (-9, 1), (-4, 8)])
    a, b, _ = np.exp(r.x)
    # preserva o total do período de ajuste (a máxima verossimilhança com modelo mal especificado desvia o nível)
    k = y.sum() / (a * x + b).sum()
    a, b = a * k, b * k
    phi = scores.fit_phi(y, a * x + b)
    return float(a), float(b), float(phi)


def knn_kernel(centroids: np.ndarray, k: int = 60):
    tree = cKDTree(centroids)
    d, idx = tree.query(centroids, k=k + 1)
    return d, idx


def kernel_smooth(values: np.ndarray, d: np.ndarray, idx: np.ndarray, bandwidth: float, kind: str = "gauss") -> np.ndarray:
    """Média ponderada dos vizinhos (inclui o próprio setor) com pesos por distância."""
    if kind == "gauss":
        w = np.exp(-0.5 * (d / bandwidth) ** 2)
    else:   # faixas de Bowers e Johnson: peso 1/(1 + faixa), faixa = parte inteira de d/bandwidth
        w = 1.0 / (1.0 + np.floor(d / bandwidth))
    v = np.where(np.isfinite(values[idx]), values[idx], 0.0)
    return (w * v).sum(axis=1) / w.sum(axis=1)


def _by_month(df: pl.DataFrame, col: str, fn) -> np.ndarray:
    """Aplica ``fn(vetor do mês)`` mês a mês; a tabela precisa ter todos os setores na mesma ordem em cada mês."""
    out = np.empty(df.height)
    mes = df["mes"].to_numpy()
    vals = df[col].to_numpy().astype("float64")
    for m in np.unique(mes):
        i = np.where(mes == m)[0]
        out[i] = fn(vals[i])
    return out


def point_forecasts(df: pl.DataFrame, kernel_d: np.ndarray, kernel_idx: np.ndarray, bw: float, bw_band: float) -> dict[str, np.ndarray]:
    """Previsões pontuais dos baselines sem modelo estatístico (todas as-of)."""
    base = df["h_int_s6"].to_numpy().astype("float64") / 6
    return {
        "persistencia": df["h_int_l1"].to_numpy().astype("float64"),
        "sazonal": df["h_int_l12"].to_numpy().astype("float64"),
        "media_historica": df["h_int_s12"].to_numpy().astype("float64") / 12,
        "stkde": _by_month(df.with_columns(pl.Series("v", base)), "v", lambda v: kernel_smooth(v, kernel_d, kernel_idx, bw)),
        "hotspot_prospectivo": _by_month(df.with_columns(pl.Series("v", base)), "v",
                                         lambda v: kernel_smooth(v, kernel_d, kernel_idx, bw_band, kind="band")),
    }


GLM_FEATURES = ["h_int_l1", "h_int_l2", "h_int_l3", "h_int_s6", "h_int_s12", "nb_h_int_l1", "nb_h_int_s3", "nb_h_int_s12"]


def _glm_matrix(df: pl.DataFrame) -> np.ndarray:
    x = np.column_stack([np.log1p(df[c].to_numpy().astype("float64")) for c in GLM_FEATURES])
    mes = df["mes_num"].to_numpy()
    sazonal = np.column_stack([(mes == k).astype("float64") for k in range(2, 13)])
    return np.column_stack([x, sazonal, np.log(df["area_km2"].to_numpy() + 1e-3)])


def fit_glm(train: pl.DataFrame) -> PoissonRegressor:
    train = train.drop_nulls(GLM_FEATURES)
    m = PoissonRegressor(alpha=1e-4, max_iter=500)
    m.fit(_glm_matrix(train), train["y"].to_numpy())
    return m


def predict_glm(m: PoissonRegressor, df: pl.DataFrame) -> np.ndarray:
    d = df.with_columns([pl.col(c).fill_null(0.0).fill_nan(0.0) for c in GLM_FEATURES])
    return m.predict(_glm_matrix(d))
