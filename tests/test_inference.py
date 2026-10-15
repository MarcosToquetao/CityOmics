

def test_ratio_bootstrap_detects_difference_and_null():
    import numpy as np

    from cityomics.eval.inference import cluster_bootstrap_ratio_diff

    rng = np.random.default_rng(1)
    cl = np.repeat(np.arange(40), 50)
    y = rng.poisson(0.5, cl.size).astype(float)
    hit_a = y * (rng.random(cl.size) < 0.6)
    hit_b = y * (rng.random(cl.size) < 0.2)
    t = cluster_bootstrap_ratio_diff(hit_a, hit_b, y, cl, n_boot=500)
    assert t["diff"] > 0.25 and t["ci_low"] > 0 and t["p"] < 0.05
    same = cluster_bootstrap_ratio_diff(hit_a, hit_a, y, cl, n_boot=500)
    assert same["diff"] == 0.0
