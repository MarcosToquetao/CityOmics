import numpy as np

from cityomics.features import table


def test_knn_neighbors_exclude_self_and_are_closest():
    pts = np.array([[0, 0], [1, 0], [2, 0], [10, 0]], dtype=float)
    idx = table.vizinhos(pts, k=2)
    assert 0 not in idx[0] and set(idx[0]) == {1, 2} and set(idx[3]) == {2, 1}


def test_spatial_lag_is_neighbor_mean_ignoring_nan():
    v = np.array([1.0, 3.0, np.nan, 5.0])
    idx = np.array([[1, 2], [0, 2], [0, 1], [0, 1]])
    out = table.spatial_lag(v, idx)
    assert out[0] == 3.0 and out[1] == 1.0 and out[2] == 2.0 and out[3] == 2.0
