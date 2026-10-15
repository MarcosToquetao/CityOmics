import numpy as np
import polars as pl

from cityomics.models.hawkes import LAGS, NB_LAGS, Hawkes


def _synthetic(n=30_000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=n)
    h1 = rng.gamma(0.7, 1.0, n)
    mu = np.exp(-1.0 + 0.5 * x) + 0.4 * h1
    y = rng.poisson(mu).astype(float)
    cols = {c: np.zeros(n) for c in list(LAGS) + list(NB_LAGS)}
    cols["h_int_l1"] = h1
    return pl.DataFrame({"x": x, "mes_num": rng.integers(1, 13, n).astype("int8"), "area_km2": np.ones(n), "y": y, **cols})


def test_hawkes_recovers_excitation_and_background_direction():
    df = _synthetic()
    m = Hawkes(["x"]).fit(df)
    k = m.kernel()
    assert 0.25 < k["h_int_l1"] < 0.6   # lags sem informação (zeros) ficam no valor inicial
    assert float(m.beta[0]) > 0.3
    mu = m.predict(df)
    assert abs(mu.sum() / df["y"].sum() - 1) < 0.05
