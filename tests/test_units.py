import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from cityomics.units import assign, reconcile


def test_stratum_keywords():
    s = pd.Series(["Via Pública", "Metroviário e Ferroviário Metropolitano", "Casa", "Ônibus/Lotação/Trolebus",
                   "Bar/Botequim", "Outros", None, "Garagem coletiva de prédio"])
    assert assign.stratum(s).tolist() == ["via_publica", "trilhos", "residencia", "onibus", "comercio",
                                          "outros", "outros", "residencia"]


def setores_fixture():
    return gpd.GeoDataFrame({"cd_setor": ["A", "B", "C"], "cd_dist": ["D1", "D1", "D2"],
                             "pop_2022": [100, 300, 50]},
                            geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 0, 3, 1)], crs="EPSG:31983")


def events(rows):
    return pd.DataFrame(rows, columns=["cd_setor", "cd_dist", "estrato", "data_fato"]).assign(
        data_fato=lambda d: pd.to_datetime(d["data_fato"]))


def test_reconcile_conserves_district_totals_and_uses_stratum_history():
    rows = []
    # janeiro–dezembro: estações (trilhos) geocodificadas só no setor B; via pública só no A
    for m in range(1, 13):
        rows += [("B", "D1", "trilhos", f"2022-{m:02d}-05"), ("A", "D1", "via_publica", f"2022-{m:02d}-06")]
    # janeiro/2023: 10 eventos de trilhos sem coordenada no distrito D1 e 1 sem setor no D2
    rows += [(None, "D1", "trilhos", "2023-01-10")] * 10 + [(None, "D2", "outros", "2023-01-11")]
    rows += [("A", "D1", "via_publica", "2023-01-02")]
    out = reconcile.reconcile(events(rows), setores_fixture(), freq="M")

    jan = out[out["periodo"] == pd.Period("2023-01", "M")].set_index("cd_setor")
    # invariante: soma do distrito = total atribuído ao distrito
    assert np.isclose(jan.loc[["A", "B"], "n_total"].sum(), 11)
    assert np.isclose(jan.loc["C", "n_total"], 1)
    # a fração de trilhos segue o histórico do estrato: quase tudo vai para B
    assert jan.loc["B", "n_alocado"] > 9 * jan.loc["A", "n_alocado"]


def test_reconcile_falls_back_to_population_without_history():
    rows = [(None, "D1", "outros", "2022-01-10")] * 4
    out = reconcile.reconcile(events(rows), setores_fixture(), freq="M").set_index("cd_setor")
    assert np.isclose(out.loc["A", "n_alocado"], 1.0) and np.isclose(out.loc["B", "n_alocado"], 3.0)


def test_points_to_setores_assigns_by_location():
    st = setores_fixture()
    pts = gpd.GeoSeries(gpd.points_from_xy([0.5, 1.5, 9.0], [0.5, 0.5, 9.0]), crs="EPSG:31983").to_crs("EPSG:4674")
    df = pd.DataFrame({"longitude": pts.x, "latitude": pts.y, "coord_valida": [True, True, True]})
    out = assign.points_to_setores(df, st)
    assert out["cd_setor"].tolist()[:2] == ["A", "B"] and pd.isna(out["cd_setor"].iloc[2])


def test_reconcile_restricts_stratum_to_eligible_setores():
    rows = [("A", "D1", "via_publica", "2022-01-05")] * 5 + [(None, "D1", "trilhos", "2022-02-10")] * 6
    out = reconcile.reconcile(events(rows), setores_fixture(), freq="M", eligible={"trilhos": {"B"}})
    feb = out[out["periodo"] == pd.Period("2022-02", "M")].set_index("cd_setor")
    assert np.isclose(feb.loc["B", "n_alocado"], 6.0) and np.isclose(feb.loc["A", "n_alocado"], 0.0)
