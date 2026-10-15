import numpy as np

from cityomics.models import ensemble


def test_weights_pick_the_informative_model_and_sum_to_one():
    rng = np.random.default_rng(0)
    truth = rng.gamma(0.8, 1.0, 20_000)
    y = rng.poisson(truth).astype(float)
    good = truth * 1.02
    bad = rng.gamma(0.8, 1.0, 20_000)
    w = ensemble.fit_weights(y, np.column_stack([good, bad]))
    assert abs(w.sum() - 1) < 1e-9 and w[0] > 0.9
