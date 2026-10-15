import numpy as np

from cityomics.laya import evaluate as E


def test_isotonic_recalibration_fixes_overconfidence_and_is_monotone():
    rng = np.random.default_rng(0)
    p_true = rng.uniform(0.05, 0.6, 20_000)
    event = (rng.random(20_000) < p_true).astype(float)
    p_raw = np.clip(p_true * 1.0 + (p_true - 0.3) * 1.5, 0.01, 0.99)       # superconfiante
    iso = E.calibrate(p_raw, event)
    cal = iso.predict(p_raw)
    assert ((cal - event) ** 2).mean() < ((p_raw - event) ** 2).mean()
    o = np.argsort(p_raw)
    assert (np.diff(cal[o]) >= -1e-12).all()


def test_brier_compare_prefers_the_sharper_forecast():
    rng = np.random.default_rng(1)
    n = 30_000
    p = rng.uniform(0.02, 0.7, n)
    ev = (rng.random(n) < p).astype(float)
    r = E.brier_compare(p, np.full(n, ev.mean()), ev, rng.integers(0, 50, n), n_boot=500)
    assert r["brier_a"] < r["brier_b"] and r["diff"] < 0 and r["p"] < 0.05
