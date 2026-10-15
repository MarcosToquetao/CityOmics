from datetime import datetime

import numpy as np
import polars as pl
from pyproj import Transformer

from cityomics.features import nearrepeat


def _events(rows):
    return pl.DataFrame(rows, schema={"latitude": pl.Float64, "longitude": pl.Float64, "coord_valida": pl.Boolean,
                                      "data_fato": pl.Datetime, "data_registro": pl.Datetime, "cd_dist": pl.String}, orient="row")


def test_counts_within_radius_and_window_and_registration_asof():
    to_ll = Transformer.from_crs(31983, 4674, always_xy=True)
    x0, y0 = 333000.0, 7395000.0
    near = to_ll.transform(x0 + 100, y0)
    far = to_ll.transform(x0 + 900, y0)
    d = lambda s: datetime.fromisoformat(s)  # noqa: E731
    ev = _events([
        (near[1], near[0], True, d("2024-05-20"), d("2024-05-21"), "d1"),    # dentro: 100 m, 12 dias antes
        (far[1], far[0], True, d("2024-05-20"), d("2024-05-21"), "d1"),      # longe: 900 m
        (near[1], near[0], True, d("2024-03-01"), d("2024-03-02"), "d1"),    # fora da janela de 30 dias
        (near[1], near[0], True, d("2024-05-30"), d("2024-06-03"), "d1"),    # registrado depois de 1/jun: fora (as-of)
        (None, None, False, d("2024-05-25"), d("2024-05-26"), "d1"),         # sem coordenada: entra só na fração
    ])
    out = nearrepeat.build(ev, np.array([[x0, y0]]), ["s1"], ["2024-06"], configs=((30, 250),))
    # janela: 3 eventos registrados, 2 geocodificados (near+far...), dentro de 250 m só 1; fração geocodificada = 2/3 (+ far)
    share = 2 / 3
    assert abs(out["nr_w30_r250"][0] - 1 / max(share, 0.05)) < 1e-4
