import polars as pl

from cityomics.covariates import asof


def test_deslocar_moves_month_forward_by_one_plus_lag():
    df = pl.DataFrame({"mes": ["2024-12", "2025-01"], "x": [1, 2]})
    assert asof.deslocar(df, 0)["mes"].to_list() == ["2025-01", "2025-02"]
    assert asof.deslocar(df, 3)["mes"].to_list() == ["2025-04", "2025-05"]


def _painel(vals, lag):
    ms = asof.meses("2024-01", "2025-06")
    g = asof.grade(["a"], ms)
    src = asof.deslocar(pl.DataFrame({"mes": ms, "x": vals}), lag)
    return g.join(src, on="mes", how="left").fill_null(0).sort("mes")


def test_feature_does_not_use_months_not_yet_published():
    ms = asof.meses("2024-01", "2025-06")
    base = list(range(1, len(ms) + 1))
    alt = base.copy()
    m = ms.index("2025-03")
    for i in range(m - 1, len(ms)):          # muda o mês m−1 em diante (ainda não publicado com lag 1 para m)
        alt[i] += 1000
    a = asof.janelas(_painel(base, 1), ["x"], "cd_setor")
    b = asof.janelas(_painel(alt, 1), ["x"], "cd_setor")
    la, lb = a.filter(pl.col("mes") == "2025-03").row(0, named=True), b.filter(pl.col("mes") == "2025-03").row(0, named=True)
    assert la["x"] == lb["x"] and la["x_s3"] == lb["x_s3"] and la["x_s12"] == lb["x_s12"]
    assert a.filter(pl.col("mes") == "2025-04")["x"][0] != b.filter(pl.col("mes") == "2025-04")["x"][0]


def test_rolling_window_sums_only_past_and_yoy():
    p = asof.janelas(_painel([1] * 18, 0), ["x"], "cd_setor")
    assert p.filter(pl.col("mes") == "2024-05")["x_s3"][0] == 3
    y = asof.yoy(_painel(list(range(18)), 0), ["x"], "cd_setor")
    assert y.filter(pl.col("mes") == "2025-03")["x_yoy"][0] == 12


def test_censo_interp_endpoints(tmp_path, monkeypatch):
    cov = tmp_path / "covariaveis"
    cov.mkdir()
    cols = {"cd_setor": ["a"], "pop": [100.0], "frac_homens_15_29": [0.1], "frac_negra": [0.3],
            "taxa_analfabetismo_15": [0.02], "renda_media_resp": [1000.0]}
    pl.DataFrame(cols).write_parquet(cov / "setor_censo2010_em_2022.parquet")
    pl.DataFrame(dict(cols, pop=[400.0])).write_parquet(cov / "setor_censo2022.parquet")
    monkeypatch.setattr(asof, "processed_dir", lambda: tmp_path)
    t = asof._censo_interp(["2010-05", "2016-05", "2022-05", "2026-01"]).sort("mes")
    assert t["censo_interp_pop"].round(3).to_list() == [100.0, 200.0, 400.0, 400.0]   # t=0, 0.5 (geométrica), 1, 1
