import numpy as np
import polars as pl

from cityomics.models import gnn


def test_norm_adj_rows_sum_to_one_and_gnn_learns_signal():
    rng = np.random.default_rng(0)
    n, k, T = 300, 4, 10
    idx = np.stack([rng.choice(np.delete(np.arange(n), i), k, replace=False) for i in range(n)])
    a = gnn.norm_adj(idx, n).to_dense()
    assert np.allclose(a.sum(1).numpy(), 1.0, atol=1e-5)
    rows = []
    for t in range(T):
        x = rng.normal(size=n)
        y = rng.poisson(np.exp(-0.5 + 0.8 * x)).astype(float)
        rows.append(pl.DataFrame({"cd_setor": [f"{i:04d}" for i in range(n)], "mes": f"2024-{t + 1:02d}", "f": x, "y": y}))
    df = pl.concat(rows)
    m = gnn.GNN(["f"], idx, device="cpu").fit(df, epochs=60, log=lambda *_: None)
    mu = m.predict(df.sort("mes", "cd_setor"))
    assert np.corrcoef(np.log(mu), df.sort("mes", "cd_setor")["f"].to_numpy())[0, 1] > 0.3
    assert abs(mu.sum() / df["y"].sum() - 1) < 0.15
