import numpy as np
import pandas as pd

from cityomics.models import maxent


def test_basis_shape_and_hinges_nonnegative():
    x = np.random.default_rng(0).normal(size=(500, 3))
    b, k = maxent.basis(x)
    assert b.shape == (500, 3 * (2 + len(maxent.KNOTS))) or b.shape[1] == 3 * 2 + 3 * len(maxent.KNOTS)
    assert (b[:, 6:] >= 0).all()


def test_fit_surface_recovers_monotone_response():
    rng = np.random.default_rng(1)
    n = 6000
    z = rng.normal(size=n)
    lam = np.exp(-1 + 0.8 * z)
    d = pd.DataFrame({"cd_setor": np.arange(n).astype(str), "z": z, "meses": 24,
                      "y": rng.poisson(lam * 24)})
    s = maxent.fit_surface(d, ["z"])
    assert np.corrcoef(np.log(s["maxent"]), z)[0, 1] > 0.95
