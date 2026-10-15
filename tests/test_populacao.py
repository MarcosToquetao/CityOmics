import polars as pl

from cityomics.covariates import populacao


def test_estimar_scales_by_residential_units_with_caps():
    unid = pl.DataFrame({"cd_setor": ["a", "a", "b", "b", "c", "c", "d", "d"], "ano": [2022, 2026] * 4,
                         "unid_res": [100.0, 150.0, 100.0, 1000.0, 2.0, 20.0, 100.0, 0.0]})
    pop = pl.DataFrame({"cd_setor": ["a", "b", "c", "d"], "pop": [400.0, 400.0, 6.0, 400.0]})
    out = populacao.estimar(unid, pop, anos=[2022, 2026, 2027])
    g = {(r["cd_setor"], r["ano"]): r["pop_dasi"] for r in out.iter_rows(named=True)}
    assert g[("a", 2022)] == 400 and g[("a", 2026)] == 600 and g[("a", 2027)] == 600   # 2027 usa 2026
    assert g[("b", 2026)] == 1600                                                       # razão 10 limitada a 4
    assert g[("c", 2026)] == 6                                                          # < 3 unidades em 2022: sem correção
    assert g[("d", 2026)] == 100                                                        # razão 0 limitada a 0,25
