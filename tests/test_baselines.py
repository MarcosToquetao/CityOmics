import numpy as np

from cityomics.models import baselines as B


def test_calibrate_recovers_scale_and_preserves_total():
    rng = np.random.default_rng(0)
    x = rng.gamma(0.5, 2.0, 80_000)
    mu = 1.3 * x + 0.05
    y = rng.negative_binomial(2.0, 2.0 / (2.0 + mu))
    a, b, phi = B.calibrate(x, y.astype(float))
    assert abs(a - 1.3) < 0.15 and abs(phi - 2.0) < 0.5
    assert abs((a * x + b).sum() / y.sum() - 1) < 1e-6


def test_kernel_smooth_weights_and_bands():
    d = np.array([[0.0, 100.0], [0.0, 100.0]])
    idx = np.array([[0, 1], [1, 0]])
    v = np.array([4.0, 0.0])
    g = B.kernel_smooth(v, d, idx, bandwidth=1e-6)       # sem suavização: só o próprio ponto
    assert np.allclose(g, [4.0, 0.0])
    band = B.kernel_smooth(v, d, idx, bandwidth=100.0, kind="band")   # pesos 1 e 1/2
    assert np.isclose(band[0], 4.0 / 1.5)
