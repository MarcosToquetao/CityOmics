import numpy as np
import pytest
from scipy import stats

from cityomics.eval import calibration, fairness, hotspot, inference, scores


def _crps_by_definition(y, mu, phi):
    n, p = scores.nb_scipy(mu, phi)
    k = np.arange(0, 400)
    pmf = stats.nbinom.pmf(k, n, p)
    e_abs = (pmf * np.abs(k - y)).sum()
    e_pair = (pmf[:, None] * pmf[None, :] * np.abs(k[:, None] - k[None, :])).sum()
    return e_abs - 0.5 * e_pair


@pytest.mark.parametrize("y,mu,phi", [(0, 0.3, 2.0), (3, 1.5, 0.7), (7, 2.0, 5.0), (0, 10.0, 1.0)])
def test_crps_matches_definition_for_integers(y, mu, phi):
    got = scores.crps_nb(np.array([y]), np.array([mu]), np.array([phi]))[0]
    assert got == pytest.approx(_crps_by_definition(y, mu, phi), abs=1e-6)


def test_crps_real_valued_observation_is_between_neighbors_and_nonnegative():
    mu, phi = np.array([1.2] * 3), np.array([2.0] * 3)
    c = scores.crps_nb(np.array([1.0, 1.4, 2.0]), mu, phi)
    assert (c >= 0).all() and c[1] <= max(c[0], c[2]) + 1e-9


def test_fit_phi_recovers_dispersion():
    rng = np.random.default_rng(1)
    mu = rng.uniform(0.2, 3, 40_000)
    phi = 1.5
    y = rng.negative_binomial(phi, phi / (phi + mu))
    assert scores.fit_phi(y, mu) == pytest.approx(phi, rel=0.1)


def test_brier_decomposition_adds_up():
    rng = np.random.default_rng(2)
    p = rng.uniform(0, 1, 5000)
    e = (rng.random(5000) < p).astype(float)
    d = scores.brier_decomposition(p, e)
    assert d["brier"] == pytest.approx(d["reliability"] - d["resolution"] + d["uncertainty"], abs=0.01)


def test_prob_ge1_poisson_limit():
    assert scores.prob_ge1(np.array([2.0]), np.array([1e6]))[0] == pytest.approx(1 - np.exp(-2), abs=1e-4)


def test_pit_is_uniform_under_correct_model():
    rng = np.random.default_rng(3)
    mu = rng.uniform(0.2, 4, 60_000)
    y = rng.negative_binomial(2.0, 2.0 / (2.0 + mu))
    h = calibration.pit_histogram(calibration.randomized_pit(y, mu, 2.0))
    assert np.abs(h - 0.1).max() < 0.01


def test_reliability_ece_small_when_calibrated():
    rng = np.random.default_rng(4)
    p = rng.uniform(0, 1, 20_000)
    e = (rng.random(20_000) < p).astype(float)
    assert calibration.reliability(p, e)[1] < 0.02


def test_hotspot_perfect_forecast_gives_pei_one_and_pai_above_one():
    rng = np.random.default_rng(5)
    area = rng.uniform(0.5, 1.5, 1000)
    obs = rng.poisson(rng.gamma(0.3, 3, 1000) )
    m = hotspot.hotspot_metrics(obs.astype(float), area, obs, shares=(0.05,))[0.05]   # previsão perfeita
    assert m["pei"] == pytest.approx(1.0) and m["pai"] > 1


def test_hotspot_uninformative_forecast_has_pai_near_one():
    rng = np.random.default_rng(6)
    area = np.ones(5000)
    obs = rng.poisson(1.0, 5000)
    m = hotspot.hotspot_metrics(rng.random(5000), area, obs, shares=(0.10,))[0.10]
    assert m["pai"] == pytest.approx(1.0, abs=0.15)


def test_cluster_bootstrap_detects_a_real_difference_and_not_a_null_one():
    rng = np.random.default_rng(7)
    cl = np.repeat(np.arange(60), 50)
    a = rng.normal(1.0, 1, cl.size)
    b = a + 0.3 + rng.normal(0, 0.3, cl.size)
    r = inference.cluster_bootstrap_diff(a, b, cl, n_boot=1000)
    assert r["diff"] < 0 and r["ci_high"] < 0 and r["p"] < 0.05
    null = inference.cluster_bootstrap_diff(a, a + rng.normal(0, 0.3, cl.size), cl, n_boot=1000)
    assert null["ci_low"] < 0 < null["ci_high"] and null["p"] > 0.05


def test_holm_adjustment():
    r = inference.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert r["a"]["p_adj"] == pytest.approx(0.03) and r["a"]["reject"]
    assert r["c"]["p_adj"] == pytest.approx(0.06) and not r["c"]["reject"] and not r["b"]["reject"]


def test_fairness_helpers():
    inc = np.arange(100.0)
    g = fairness.quintile_groups(inc)
    assert g.nunique() == 5
    f = fairness.flagged_share(g.to_numpy(), np.arange(100.0), np.ones(100), 0.2)
    assert f.sum() == pytest.approx(1.0) and f.idxmax() == "Q5"
