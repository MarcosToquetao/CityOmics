"""Testes da identificação da atribuição (parecer de 2026-10-20, Agente B; ``atlas/identificacao.py``).

Só dados sintéticos: o EM vetorizado é o de ``em_fit``, recupera λ com E bem condicionada, o bootstrap por
pesos é o bootstrap por distrito, reescalar uma coluna de E não muda as partes e a validação pontual
pré-computada soma eventos como a original.
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import csr_matrix

from cityomics.atlas import guard, identificacao as I
from cityomics.atlas.attribution import bootstrap, em_fit, em_fit_multi
from cityomics.atlas.fenotipo import _log2_enriq, _participacao


def _sintetico(seed: int = 0, n: int = 4000):
    rng = np.random.default_rng(seed)
    E = rng.gamma(2.0, 1.0, size=(n, 4)) * (rng.random((n, 4)) < 0.7)
    lam = np.array([0.5, 2.0, 0.05, 5.0])
    y = rng.poisson(E @ lam).astype(float)
    return rng, E, lam, y


def test_kernel_matches_em_fit():
    _, E, _, y = _sintetico(1)
    L, it = I.em(E, y)
    assert np.allclose(L[:, 0], em_fit(E, y)["lam"], rtol=1e-10, atol=1e-12)
    assert it[0] >= 2


def test_em_recovers_rates_with_well_conditioned_exposure():
    rng, E, lam, _ = _sintetico(2, n=20000)
    assert I._belsley(E, list("abcd"))["numero_condicao"] < 10
    Y = rng.poisson(np.repeat((E @ lam)[:, None], 20, axis=1)).astype(float)
    L, _ = I.em(E, Y, n_iter=5000, tol=1e-12)
    assert np.allclose(L.mean(axis=1), lam, rtol=0.05, atol=0.01)
    assert (L >= 0).all()


def test_weighted_bootstrap_equals_district_resampling():
    _, E, _, y = _sintetico(3, n=1500)
    dist = np.repeat(np.arange(30), 50).astype(str)
    codes, mult = I.multiplicidades(dist, 10, seed=0)
    B, _ = I.em(E, y, ycol=np.zeros(10, int), dist=codes, mult=mult)
    B0 = bootstrap(E, y, dist, n_boot=10, seed=0)
    assert np.allclose(B.T, B0, rtol=1e-8, atol=1e-10)


def test_rescaling_a_column_keeps_shares_and_enrichment():
    rng, E, lam, _ = _sintetico(4)
    Lam = np.column_stack([lam, lam[::-1], np.array([1.0, 0.1, 3.0, 0.2])])
    Y = rng.poisson(E @ Lam).astype(float)
    L0 = em_fit_multi(E, Y, n_iter=50000, tol=1e-14)
    Ec = E.copy()
    Ec[:, 2] *= 7.0
    L1 = em_fit_multi(Ec, Y, n_iter=50000, tol=1e-14)
    S0, S1 = _participacao(L0, E), _participacao(L1, Ec)
    assert np.allclose(S0, S1, atol=1e-6)
    assert np.allclose(_log2_enriq(S0), _log2_enriq(S1), atol=1e-3)
    assert np.allclose(L1[2] * 7.0, L0[2], rtol=1e-4)


def test_point_rates_sum_events_over_segments_and_stations():
    # dois segmentos (arterial e local), duas classes de lote; o segmento 0 reparte 3:1 entre as classes
    M = csr_matrix(np.array([[0.75, 0.25], [0.0, 1.0]]))
    lig = {"st": np.array([False, False, False, True]), "seg": np.array([0, 0, 1, -1]), "M": M,
           "seg_cls": np.array([0, 2]), "classes": ["a", "b", "rua_arterial_m", "rua_coletora_m", "rua_local_m", "estacoes"],
           "exposicao": np.array([1.0, 2.0, 1.0, 1.0, 1.0, 1.0])}
    tx = I.taxas_pontuais(lig, np.ones(4, bool))
    assert np.isclose(tx["a"], 1.5) and np.isclose(tx["b"], 0.75)
    assert tx["rua_arterial_m"] == 2 and tx["rua_local_m"] == 1 and tx["rua_coletora_m"] == 0 and tx["estacoes"] == 1
    tx1 = I.taxas_pontuais(lig, np.array([False, False, True, False]))
    assert tx1["a"] == 0 and np.isclose(tx1["b"], 0.5)


def test_small_clusters_are_merged_into_nearest_large_one():
    rng = np.random.default_rng(5)
    P = np.concatenate([rng.normal(0, 0.1, (500, 2)), rng.normal(5, 0.1, (500, 2)), rng.normal(4.8, 0.1, (1, 2))])
    lab = np.array([0] * 500 + [1] * 500 + [2])
    out, n = I._funde(P, lab, min_share=0.003)
    assert n == 1 and len(np.unique(out)) == 2 and out[-1] == out[500]


def test_scope_stays_before_2026():
    assert max(I.ANOS) <= guard.YEAR_MAX


def test_quick_run_never_writes_the_official_json():
    import pytest

    with pytest.raises(ValueError):
        I.run(rapido=True, saida=None)


def test_vertical_rule_applies_to_every_type():
    lab = np.array([0, 0, 1, 1, 2])
    alto = np.array([False, True, False, True, False])
    out = I._vertical(lab, alto)
    assert out.tolist() == [0, 3, 1, 3, 2]
