import joblib
import numpy as np
import pandas as pd
import polars as pl

from cityomics import freeze
from cityomics.models import congelar, inla_models, zoo


def _tabela(n_set=5, meses=("2024-11", "2024-12", "2025-01", "2025-02")):
    rng = np.random.default_rng(0)
    rows = [{"cd_setor": f"s{i}", "mes": m, "mes_num": int(m[-2:]), "h_int_s12": float(rng.integers(0, 30)),
             "y": float(rng.poisson(2))} for m in meses for i in range(n_set)]
    return pl.DataFrame(rows).sort("mes", "cd_setor")


def test_superficie_resumida_reproduz_inla_predict():
    t = _tabela()
    fit = t.filter(pl.col("mes") <= "2024-12")
    surf = pd.DataFrame({"cd_setor": [f"s{i}" for i in range(5)], "bym2": np.linspace(0.5, 2.5, 5)})
    s = zoo._superficie(t, fit, surf, "bym2")
    for df in (fit, t.filter(pl.col("mes") >= "2025-01")):
        np.testing.assert_allclose(zoo._predict_superficie(s, df, t), inla_models.predict(t, df, fit, surf, "bym2"))


def test_ajustado_sobrevive_a_serializacao(tmp_path):
    t = _tabela()
    m = zoo.Ajustado("media_historica", a=0.9, b=0.1)
    joblib.dump(m, tmp_path / "m.joblib")
    np.testing.assert_allclose(joblib.load(tmp_path / "m.joblib").predict(t, t), m.predict(t, t))


def test_markov_suavizado_soma_um(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path))
    from cityomics.atlas.genes_lote import atlas_dir

    pl.DataFrame({"dominio": [0, 0, 1], "de": ["a", "a", "b"], "para": ["a", "b", "b"], "n": [90, 10, 5]}).write_parquet(
        atlas_dir() / "transicoes_familia_dominio.parquet")
    rep = congelar.markov(log=lambda *_: None)
    M = pl.read_parquet(tmp_path / "models" / "frozen" / "destino" / "markov_familia_dominio.parquet")
    assert rep["familias"] == ["a", "b"] and M.height == 2 * 2 * 2
    np.testing.assert_allclose(M.group_by("dominio", "de").agg(pl.col("p").sum())["p"].to_numpy(), 1.0)
    p = M.filter((pl.col("dominio") == 0) & (pl.col("de") == "a") & (pl.col("para") == "a"))["p"][0]
    assert abs(p - 91 / 102) < 1e-12


def test_etapa_b_exige_freeze_a_e_confirmacao(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    problems = freeze.check(run_tests=False, etapa="B")
    assert any("FREEZE-A" in p for p in problems) or any("confirmação" in p for p in problems)
    assert any("pesos do Laya" in p for p in problems)


def test_emenda_datada_le_so_linhas_de_tabela_com_data():
    assert freeze.emenda_datada("A1") and freeze.emenda_datada("A10")
    assert not freeze.emenda_datada("A99")
