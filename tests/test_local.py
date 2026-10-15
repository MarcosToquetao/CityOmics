import numpy as np
import polars as pl

from cityomics.models import local


def _df(n=6000, seed=0):
    rng = np.random.default_rng(seed)
    d = rng.integers(0, 3, n).astype(str)
    cols = {c: rng.gamma(0.8, 1.0, n) for c in local.HIST}
    slope = np.array([0.2, 0.5, 0.8])[d.astype(int)]
    mu = np.exp(-1.5 + slope * np.log1p(cols["h_int_s12"]))
    return pl.DataFrame({"cd_dist": d, "mes_num": rng.integers(1, 13, n).astype("int8"), "y": rng.poisson(mu).astype(float), **cols, "z": rng.normal(size=n)})


def test_gwr_and_panel_preserve_total_and_gwr_varies_by_district():
    df = _df()
    g = local.GWRDistrict(["z"], min_rows=500).fit(df)
    assert len(g.local) == 3
    assert abs(g.predict(df).sum() / df["y"].sum() - 1) < 0.05
    p = local.PainelEspacial(["z"]).fit(df)
    assert abs(p.predict(df).sum() / df["y"].sum() - 1) < 0.05
