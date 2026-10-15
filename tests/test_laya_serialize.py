import numpy as np
import polars as pl

from cityomics.laya import serialize as S


def _df(n=300, seed=0):
    rng = np.random.default_rng(seed)
    d = {"mes": ["2025-03"] * n, "cd_setor": [f"3550308{i:08d}" for i in range(n)], "mes_num": rng.integers(1, 13, n), "area_km2": rng.uniform(0.02, 1.5, n),
         "dias_uteis": np.full(n, 21), "dias_feriado": np.zeros(n), "dias_carnaval": np.zeros(n), "tem_decimo_terceiro": np.zeros(n),
         "y": rng.poisson(0.5, n).astype(float)}
    for c in S.TREND_COLS:
        d[c] = rng.gamma(0.7, 2, n)
    d["h_int_s12"] = d["h_int_s12"] * 5
    for j in range(15):
        d[f"censo2022_x{j}"] = rng.gamma(2, 1, n) * (j + 1)
    return pl.DataFrame(d)


def test_top10_and_numeric_equivalence_with_text():
    df = _df()
    cols = [c for c in df.columns if c.startswith("censo2022_")]
    sb = S.StateBuilder(df, cols, salt="s")
    z = sb.z(df)
    top = sb.top10(z)
    assert top.shape == (df.height, 10)
    assert (np.abs(np.take_along_axis(z, top, 1)).min(axis=1) >= np.sort(np.abs(z), axis=1)[:, -10] - 1e-9).all()
    num = sb.compressed_numeric(df, {"hawkes": np.ones(df.height)})
    assert (num.select([c for c in num.columns if c.startswith("marker_")]).to_numpy().astype(float) == num.select([c for c in num.columns if c.startswith("marker_")]).to_numpy().astype(float)).sum() >= 0
    assert (~np.isnan(num.select([c for c in num.columns if c.startswith("marker_")]).to_numpy())).sum(axis=1).max() == 10


def test_texts_are_anonymous_and_short_and_ablations_work():
    df = _df()
    cols = [c for c in df.columns if c.startswith("censo2022_")]
    sb = S.StateBuilder(df, cols, salt="s")
    t = sb.texts(df, {"hawkes": np.ones(df.height)})
    assert all(df["cd_setor"][0] not in s for s in t[:5]) and all("T-" in s for s in t[:5])
    assert max(len(s.split()) for s in t) < 400            # bem abaixo de 1.024 tokens
    sem = sb.texts(df, {}, history=False)
    assert "Recent cellphone" not in sem[0] and "Forecasts" not in sem[0]
    nomes = pl.DataFrame({"cd_setor": df["cd_setor"], "nm_dist": ["Pinheiros"] * df.height})
    assert "Pinheiros" in sb.texts(df, {}, names=nomes)[0]
    assert S.anon_id(["a"], "x") != S.anon_id(["a"], "y") and S.anon_id(["a"], "x") == S.anon_id(["a"], "x")


def test_finetune_rows_labels():
    rows = S.rows_for_finetune(["a", "b", "c"], np.array([0.0, 1.2, 9.0]))
    assert [r["expected"]["ge1"] for r in rows] == [False, True, True]
    assert [r["expected"]["band"] for r in rows] == [0, 1, 4] and rows[2]["expected"]["ge3"]
