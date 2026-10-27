"""Testes do atlas e das figuras (spec-figuras §9; D51, D53, D55, D57, D60)."""

from __future__ import annotations

import json
import re

import numpy as np
import pytest

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit, shapley_flows
from cityomics.paths import REPO_ROOT


def test_em_recovers_known_rates():
    rng = np.random.default_rng(1)
    E = rng.gamma(2.0, 1.0, size=(4000, 4))
    lam = np.array([0.5, 2.0, 0.0, 5.0])
    y = rng.poisson(E @ lam)
    est = em_fit(E, y.astype(float), n_iter=3000)["lam"]
    assert np.allclose(est, lam, atol=0.25)
    assert (est >= 0).all()


def test_em_district_effect_is_normalized():
    rng = np.random.default_rng(2)
    E = rng.gamma(2.0, 1.0, size=(3000, 3))
    g = rng.integers(0, 10, 3000)
    delta = np.exp(rng.normal(0, 0.3, 10))
    y = rng.poisson(delta[g] * (E @ np.array([1.0, 3.0, 0.5])))
    out = em_fit(E, y.astype(float), groups=g, n_iter=2000)
    assert abs(np.mean(np.log(out["delta_grupo"]))) < 1e-6


def test_shapley_is_efficient():
    rng = np.random.default_rng(3)
    n, K, G = 200, 3, 4
    E = rng.gamma(2.0, 1.0, size=(n, K))
    Z = rng.normal(size=(n, G))
    B = rng.normal(scale=0.3, size=(K, G + 1))
    fl = shapley_flows(E, Z, B, np.ones(n))
    # identidade + soma das contribuições = total de cada classe (eficiência do Shapley)
    assert np.allclose(fl["identidade"] + fl["phi"].sum(1), fl["total"], rtol=1e-9)
    assert abs(fl["espacial"]) < 1e-9


def test_guard_blocks_2026_files():
    with pytest.raises(guard.SealedYearError):
        guard.pre2026("data/interim/iptu/iptu_lote_2026.parquet")
    with pytest.raises(guard.SealedYearError):
        guard.pre2026("data/external/cnpj/2026-09_Estabelecimentos0.zip")
    assert guard.pre2026("data/interim/iptu/iptu_lote_2025.parquet").name.endswith("2025.parquet")


def test_vault_is_registered_and_untampered():
    v = json.loads((REPO_ROOT / "prereg" / "atlas_vault.json").read_text())
    assert v["seed"] == 20261016 and len(v["cofre"]) == round(v["n_distritos"] * v["share"])
    assert guard.vault() == set(v["cofre"])


def test_atlas_and_figure_code_never_names_2026_inputs():
    rx = re.compile(r"_2026|2026-\d\d_|2026_")
    files = list((REPO_ROOT / "src" / "cityomics" / "atlas").glob("*.py")) + \
        list((REPO_ROOT / "src" / "cityomics" / "viz").glob("*.py")) + list((REPO_ROOT / "figures").glob("*.py"))
    bad = [f.name for f in files if f.name != "guard.py" and rx.search(f.read_text())]
    assert not bad, f"código do atlas/figuras cita arquivos de 2026: {bad}"


def test_privacy_scan_reads_zarr_metadata(tmp_path):
    from cityomics.privacy import scan_tables

    store = tmp_path / "lotes.zarr" / "obs"
    store.mkdir(parents=True)
    (store / ".zattrs").write_text(json.dumps({"column-order": ["tipo", "LATITUDE"], "encoding-type": "dataframe"}))
    found = scan_tables(tmp_path)
    assert any("LATITUDE" in f.detail for f in found)


def test_viz_style_embeds_truetype_fonts():
    import matplotlib as mpl

    from cityomics.viz import style

    style.apply()
    assert mpl.rcParams["pdf.fonttype"] == 42
    assert min(style.FONT_SIZES.values()) >= 5.0


def test_type_colors_share_family_hue():
    from cityomics.viz.palette import type_colors

    c = type_colors(["a", "b", "c"], ["res_horizontal", "res_horizontal", "comercio"], [0, 1, 0])
    assert c["a"] != c["b"] and len(set(c.values())) == 3


def test_save_enforces_minimum_font(tmp_path, monkeypatch):
    from cityomics.viz import style as S

    monkeypatch.setattr(S, "out_dir", lambda periodo: tmp_path)
    fig = S.figure(S.SINGLE, 40)
    ax = fig.add_subplot(111)
    t = ax.text(0.5, 0.5, "tiny", fontsize=3.5)
    ax.set_xlabel("x", fontsize=4.0)
    S.save(fig, "teste", png=False)
    assert t.get_fontsize() >= S.FONT_MIN and ax.xaxis.label.get_fontsize() >= S.FONT_MIN
