import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, box

from cityomics.atlas.streets import setor_do_ponto_medio


def test_setor_do_ponto_medio_ignora_indice_com_buracos():
    setores = gpd.GeoDataFrame({"cd_setor": ["A", "B"]}, geometry=[box(0, 0, 10, 10), box(10, 0, 20, 10)], crs="EPSG:31983")
    e = gpd.GeoDataFrame({"x": [0, 1, 2]}, geometry=[LineString([(1, 1), (3, 1)]), LineString([(12, 1), (14, 1)]),
                                                     LineString([(2, 5), (4, 5)])], crs="EPSG:31983")
    e.index = [10, 3, 7]  # índice como o que sobra depois de drop_duplicates
    assert list(setor_do_ponto_medio(e, setores)) == ["A", "B", "A"]
