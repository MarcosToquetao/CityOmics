"""Funções puras da análise de contexto dos gêmeos de tecido (atlas/contexto*.py)."""

import numpy as np

from cityomics.atlas import contexto as C
from cityomics.atlas import contexto_vizinhanca as V


def test_razao_encolhida_neutra_e_encolhe():
    rng = np.random.default_rng(0)
    M = rng.uniform(2, 50, 4000)
    Y = rng.poisson(M).astype(float)
    r, pri = C.razao_encolhida(Y, M)
    assert abs(r.mean()) < 0.05                      # sem excesso: razão ≈ 1
    assert np.std(r) < np.std(np.log((Y + 0.5) / (M + 0.5)))   # encolhimento reduz a dispersão


def test_mistura_sem_eventos_volta_ao_esperado():
    M = np.array([[3.0, 1.0, 1.0]])
    assert np.allclose(C.mistura(np.zeros((1, 3)), M), 0.0)


def test_hellinger_e_demean():
    P = np.array([[0.5, 0.5], [1.0, 0.0]])
    assert np.allclose(V.hellinger(P, P), 0.0)
    assert V.hellinger(P[:1], P[1:])[0] > 0.5
    g = np.array([0, 0, 1, 1])
    assert np.allclose(V.demean(np.array([1.0, 3.0, 10.0, 14.0]), g), [-1, 1, -2, 2])


def test_coef_fe_recupera_efeito():
    rng = np.random.default_rng(1)
    g = np.repeat(np.arange(40), 30)
    x = rng.normal(size=g.size)
    y = 0.5 * x + rng.normal(size=40)[g] * 3 + rng.normal(size=g.size) * 0.1
    be, ci = V.coef_fe(y, x[:, None], g, n_boot=30)
    assert abs(be[0] - 0.5) < 0.05 and ci[0, 0] < be[0] < ci[1, 0]
