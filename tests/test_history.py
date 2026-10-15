from datetime import datetime

import polars as pl

from cityomics.features import history

SETORES = ["s1", "s2"]
DIST = {"s1": "d1", "s2": "d1"}


def _ev(rows):
    return pl.DataFrame(rows, schema={"cd_setor": pl.String, "cd_dist": pl.String, "data_fato": pl.Datetime,
                                      "data_registro": pl.Datetime, "via": pl.String}, orient="row")


def _row(setor, fato, reg, via="coord"):
    return (setor, "d1", datetime.fromisoformat(fato), datetime.fromisoformat(reg), via)


def test_lag1_counts_only_events_registered_before_month_start():
    ev = _ev([_row("s1", "2024-05-10", "2024-05-12"),     # registrado no mesmo mês: conta no lag 1 de junho
              _row("s1", "2024-05-28", "2024-06-02"),     # registrado em junho: NÃO conta para junho
              _row("s1", "2024-04-03", "2024-04-03")])
    h = history.build(ev, SETORES, DIST, ["2024-06", "2024-07"]).filter(pl.col("cd_setor") == "s1").sort("mes")
    assert h["h_geo_l1"].to_list()[0] == 1.0        # junho vê só o evento de maio registrado em maio
    assert h["h_geo_l2"].to_list()[1] == 2.0        # julho (lag 2 = maio) já vê o evento registrado em junho
    assert h["h_geo_l2"].to_list()[0] == 1.0        # abril visto de junho


def test_features_unchanged_when_late_events_are_removed():
    base = [_row("s1", "2024-05-10", "2024-05-12"), _row("s2", "2024-05-11", "2024-05-11"),
            _row("s1", "2024-04-02", "2024-04-05")]
    late = _row("s1", "2024-05-30", "2024-06-15")          # registrado depois do início de junho
    a = history.build(_ev(base), SETORES, DIST, ["2024-06"]).sort("cd_setor")
    b = history.build(_ev(base + [late]), SETORES, DIST, ["2024-06"]).sort("cd_setor")
    assert a.equals(b)


def test_coverage_correction_scales_intensity():
    ev = _ev([_row("s1", "2024-05-10", "2024-05-10"), _row("s1", "2024-05-11", "2024-05-11"),
              _row("s2", "2024-05-12", "2024-05-12", via="bairro"), _row("s2", "2024-05-13", "2024-05-13", via="bairro")])
    h = history.build(ev, SETORES, DIST, ["2024-06"]).sort("cd_setor")
    # distrito: 4 eventos, 2 geocodificados → cobertura (2+1)/(4+1,25) ≈ 0,571 → intensidade s1 ≈ 2/0,571
    assert abs(h["h_int_l1"][0] - 2 / (3 / 5.25)) < 1e-4 and h["h_dist_l1"][0] == 4
