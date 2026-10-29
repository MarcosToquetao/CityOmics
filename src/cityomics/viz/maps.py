"""Mapas do tecido (Fig. 1, 3, 4 e 6): cidade rasterizada, ROIs vetoriais e coropletos rasterizados.

- ``type_raster``: os 1,7 milhão de lotes (e as pseudo-células FCU por baixo) queimados numa grade
  de ~12 m com o código do tipo. Dá o "corte histológico" da cidade sem pesar o PDF.
- ``roi``: recorte vetorial em resolução de lote, com contornos dos setores (spots) e as ruas como
  o espaço escuro entre as células.
- ``setor_raster``: valores por setor rasterizados (risco, acerto/erro), para que nenhum valor de
  setor seja extraível de um polígono vetorial (D60).
- ``scalebar`` e marcos (rios e trilhos), discretos.
"""

from __future__ import annotations

import numpy as np

from cityomics.paths import processed_dir
from cityomics.viz.style import DARK_BG

CRS = "EPSG:31983"


_CACHE: dict = {}


def layer(name: str):
    """Camadas lidas uma vez por processo (lotes: 1,7 milhão de polígonos)."""
    import geopandas as gpd

    if name not in _CACHE:
        cols = {"lotes": ["sql_base", "origem", "geometry"], "setores": ["cd_setor", "favela", "geometry"]}[name]
        f = {"lotes": "lotes.parquet", "setores": "setores_2022.parquet"}[name]
        _CACHE[name] = gpd.read_parquet(processed_dir() / "units" / f, columns=cols)
    return _CACHE[name]


def _bounds():
    import geopandas as gpd

    s = gpd.read_parquet(processed_dir() / "units" / "distritos.parquet", columns=["geometry"])
    return tuple(s.total_bounds), s


def rasterize(geoms, values, res: float, bounds, fill: int = 0, dtype="uint8") -> np.ndarray:
    from rasterio import features
    from rasterio.transform import from_origin

    x0, y0, x1, y1 = bounds
    w, h = int(np.ceil((x1 - x0) / res)), int(np.ceil((y1 - y0) / res))
    tr = from_origin(x0, y1, res, res)
    return features.rasterize(zip(geoms, values), out_shape=(h, w), transform=tr, fill=fill, dtype=dtype,
                              all_touched=False)


def type_raster(tipo_by_sql: dict[str, int], fcu_code: int, res: float = 12.0):
    """Grade com o código do tipo (0 = fundo). Favelas FCU por baixo, lotes por cima."""
    import geopandas as gpd

    bounds, dist = _bounds()
    lots = gpd.read_parquet(processed_dir() / "units" / "lotes.parquet", columns=["sql_base", "origem", "geometry"])
    lots = lots[lots["origem"] == "lote_fiscal"]
    codes = lots["sql_base"].astype(str).map(tipo_by_sql).fillna(0).astype(int).to_numpy()
    setores = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "favela", "geometry"])
    fav = setores[setores["favela"]]
    base = rasterize(fav.geometry.values, [fcu_code] * len(fav), res, bounds)
    top = rasterize(lots.geometry.values, codes, res, bounds)
    img = np.where(base > 0, base, top)  # favela FCU prevalece sobre o cadastro (D54)
    mask = rasterize(dist.geometry.values, [1] * len(dist), res, bounds)
    return img, mask, bounds


def to_rgba(img: np.ndarray, colors: dict[int, str], mask: np.ndarray | None = None, bg: str = DARK_BG,
            outside: str | None = None) -> np.ndarray:
    from matplotlib.colors import to_rgba as _c

    lut = np.zeros((max(max(colors), int(img.max())) + 1, 4))
    lut[0] = _c(bg)
    for k, c in colors.items():
        lut[k] = _c(c)
    out = lut[img]
    if mask is not None and outside is not None:
        out[mask == 0] = _c(outside)
    elif mask is not None:
        out[mask == 0, 3] = 0.0
    return out


def show(ax, rgba: np.ndarray, bounds, **kw) -> None:
    x0, y0, x1, y1 = bounds
    ax.imshow(rgba, extent=(x0, x0 + rgba.shape[1] * (x1 - x0) / rgba.shape[1], y0, y1), origin="upper",
              interpolation="nearest", rasterized=True, **kw)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")


def roi(ax, bbox, tipo_by_sql: dict[str, str], colors: dict[str, str], fcu_color: str, edge: str = DARK_BG,
        setor_edge: str = "#FFFFFF", setor_lw: float = 0.35) -> None:
    """Recorte vetorial: lotes coloridos por tipo, favelas FCU e contornos de setor."""
    import geopandas as gpd
    from matplotlib.collections import PatchCollection
    from shapely.geometry import box

    b = box(*bbox)
    lots = layer("lotes").cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    lots = lots[(lots["origem"] == "lote_fiscal") & lots.intersects(b)]
    setores = layer("setores").cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
    setores = setores[setores.intersects(b)]
    fav = setores[setores["favela"]]
    cols = lots["sql_base"].astype(str).map(lambda s: colors.get(tipo_by_sql.get(s, ""), "#3A3A40"))
    lots.clip(b).plot(ax=ax, color=cols.loc[lots.clip(b).index] if len(lots) else None, edgecolor=edge, linewidth=0.08)
    if len(fav):  # favela FCU por cima do cadastro (D54)
        fav.clip(b).plot(ax=ax, color=fcu_color, edgecolor=edge, linewidth=0.15, zorder=2)
    setores.boundary.clip(b).plot(ax=ax, color=setor_edge, linewidth=setor_lw, alpha=0.9)
    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    ax.set_aspect("equal")
    ax.set_xlabel("")
    ax.set_ylabel("")
    del PatchCollection


def setor_raster(values: dict[str, float], res: float = 30.0, fill: float = np.nan):
    """Valores por setor queimados numa grade (float). Fora dos setores = NaN."""
    import geopandas as gpd

    bounds, _ = _bounds()
    s = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    s["v"] = s["cd_setor"].astype(str).map(values)
    s = s[s["v"].notna()]
    codes = np.arange(1, len(s) + 1)
    idx = rasterize(s.geometry.values, codes, res, bounds, fill=0, dtype="int32")
    lut = np.concatenate([[fill], s["v"].to_numpy().astype(float)])
    return lut[idx], bounds


def scalebar(ax, length_m: float, color: str = "#FFFFFF", loc=(0.06, 0.06), label: str | None = None, lw: float = 1.2,
             backing: str | None = None) -> None:
    """Barra de escala; ``backing`` põe um retângulo opaco atrás (mapas de lotes, onde a barra some no desenho)."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    xs = x0 + loc[0] * (x1 - x0)
    ys = y0 + loc[1] * (y1 - y0)
    if backing:
        import matplotlib.patches as mpatches

        px, py = 0.025 * (x1 - x0), 0.025 * (y1 - y0)
        ax.add_patch(mpatches.FancyBboxPatch((xs - px, ys - py), length_m + 2 * px, 0.075 * (y1 - y0) + py,
                                             boxstyle="round,pad=0,rounding_size=0", facecolor=backing, edgecolor="none",
                                             alpha=0.85, zorder=9))
    ax.plot([xs, xs + length_m], [ys, ys], color=color, lw=lw, solid_capstyle="butt", zorder=10)
    txt = label or (f"{length_m / 1000:g} km" if length_m >= 1000 else f"{length_m:g} m")
    ax.text(xs + length_m / 2, ys + 0.012 * (y1 - y0), txt, color=color, ha="center", va="bottom", fontsize=5.5, zorder=10)


def roads(ax, bbox=None, color: str = "#2B3440", lw: float = 0.15, classes=("arterial", "coletora")) -> None:
    import geopandas as gpd

    from cityomics.atlas.genes_lote import atlas_dir

    r = gpd.read_parquet(atlas_dir() / "ruas.parquet")
    r = r[r["classe"].isin(classes)]
    if bbox is not None:
        from shapely.geometry import box

        r = r[r.intersects(box(*bbox))]
    r.plot(ax=ax, color=color, linewidth=lw)
