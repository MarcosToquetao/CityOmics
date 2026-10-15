import h5py
import numpy as np
import pytest

from cityomics.covariates import viirs


def test_pixel_index_for_sao_paulo_center():
    row, col = viirs.pixel_index(np.array([-23.55]), np.array([-46.63]))
    assert (row[0], col[0]) == (852, 808)    # (−20+23.55)·240 = 852 ; (−46.63+50)·240 = 808,8 → 808


def test_read_tile_masks_fill_and_bad_quality(tmp_path):
    p = tmp_path / "t.h5"
    with h5py.File(p, "w") as f:
        g = f.create_group("HDFEOS/GRIDS/VIIRS_Monthly_NTL/Data Fields")
        a = np.array([[10, 65535], [20, 30]], dtype="uint16")
        d = g.create_dataset(viirs.BANDA, data=a)
        d.attrs["scale_factor"] = [0.1]
        g.create_dataset(viirs.BANDA + "_Quality", data=np.array([[0, 0], [2, 1]], dtype="uint8"))
    out = viirs.read_tile(p)
    assert out[0, 0] == pytest.approx(1.0) and np.isnan(out[0, 1]) and np.isnan(out[1, 0]) and out[1, 1] == pytest.approx(3.0)


def test_token_required(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        viirs.token()
