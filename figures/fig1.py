"""Fig. 1 — A cidade como tecido (spec-figuras §3; D43, D45, D50).

a: esquema tecido ↔ cidade (SVG fixo, sobreposto em vetor no PDF);
b: "corte histológico" de São Paulo, 1,7 milhão de lotes por tipo sobre fundo escuro;
c–d: ROIs em resolução de lote (centro e periferia), com contornos dos setores;
e: legenda dos tipos por família.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from common import ax_mm, check_periodo
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.paths import REPO_ROOT, processed_dir
from cityomics.viz import maps as M
from cityomics.viz import palette as P
from cityomics.viz import style as S

SCHEMA = REPO_ROOT / "figures" / "assets" / "fig1a_esquema.svg"
W, H = S.DOUBLE, 158
A_BOX = (0, 1, 183, 30)  # x, y_top, w, h em mm


def type_table():
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)", "Sem cadastro"]
    en = perfil["name_en"].to_list() + ["Favela (census FCU)", "No cadastral record"]
    fam = perfil["familia"].to_list() + ["favela", "sem_cadastro"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0, 0.0]
    return tipos, en, fam, key


def roi_centers():
    import geopandas as gpd

    d = gpd.read_parquet(processed_dir() / "units" / "distritos.parquet", columns=["nm_dist", "geometry"])
    s = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "cd_dist", "favela", "geometry"])
    se = d[d["nm_dist"].str.upper().str.contains("^SE$|^SÉ$", regex=True)].geometry.centroid.iloc[0]
    va = d[d["nm_dist"].str.upper().str.contains("VILA ANDRADE")]
    fav = s[s["favela"] & s.intersects(va.geometry.iloc[0])]
    pc = fav.dissolve().geometry.centroid.iloc[0] if len(fav) else va.geometry.centroid.iloc[0]
    return (se.x, se.y), (pc.x, pc.y)


def overlay_schema(pdf_path) -> None:
    """Sobrepõe o esquema vetorial (SVG → PDF) na caixa da Fig. 1a."""
    import io

    import cairosvg
    from pypdf import PdfReader, PdfWriter, Transformation

    base = PdfReader(str(pdf_path))
    page = base.pages[0]
    svg_pdf = PdfReader(io.BytesIO(cairosvg.svg2pdf(url=str(SCHEMA))))
    sp = svg_pdf.pages[0]
    pt_per_mm = 72 / 25.4
    x, y_top, w, h = A_BOX
    page_h = float(page.mediabox.height)
    sx = (w * pt_per_mm) / float(sp.mediabox.width)
    sy = (h * pt_per_mm) / float(sp.mediabox.height)
    tx = x * pt_per_mm
    ty = page_h - (y_top + h) * pt_per_mm
    page.merge_transformed_page(sp, Transformation().scale(sx, sy).translate(tx, ty))
    out = PdfWriter()
    out.add_page(page)
    with open(pdf_path, "wb") as fh:
        out.write(fh)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    import cairosvg
    import matplotlib.image as mpimg
    import io

    tipos, en, fam, key = type_table()
    dark_cols = P.type_colors(tipos, fam, key, dark=True)
    code = {t: i + 1 for i, t in enumerate(tipos)}
    lt = pl.read_parquet(atlas_dir() / "lote_tipos_2025.parquet").select("sql_base", "tipo")
    tipo_by_sql = dict(zip(lt["sql_base"].to_list(), lt["tipo"].to_list()))
    code_by_sql = {k: code.get(v, 0) for k, v in tipo_by_sql.items()}
    img, mask, bounds = M.type_raster(code_by_sql, code["Favela (FCU)"], res=12.0)
    rgba = M.to_rgba(img, {code[t]: dark_cols[t] for t in tipos}, mask=mask, bg="#141419")
    fig = S.figure(W, H)
    fig.patch.set_facecolor("white")
    # a — esquema
    a = ax_mm(fig, *A_BOX)
    a.axis("off")
    png = cairosvg.svg2png(url=str(SCHEMA), output_width=3000)
    a.imshow(mpimg.imread(io.BytesIO(png)), interpolation="lanczos")
    S.fig_label(fig, "a", 1, 0.5)
    # b — cidade
    x0, y0, x1, y1 = bounds
    hb = 118.0
    wb = hb * (x1 - x0) / (y1 - y0)
    b = ax_mm(fig, 2, 35, wb, hb)
    S.dark(b)
    b.set_facecolor("white")
    M.show(b, rgba, bounds)
    import geopandas as gpd

    agua = gpd.read_file(REPO_ROOT / "data" / "external" / "geosampa" / "massa_d_agua.geojson").to_crs(M.CRS)
    agua = agua[agua.geometry.area > 2e5]
    agua.plot(ax=b, color="#1F3A5A", linewidth=0, zorder=2)
    trilho = pd_concat_lines()
    trilho.plot(ax=b, color="#E8E8E8", linewidth=0.35, zorder=3)
    b.set_xlim(x0, x1)
    b.set_ylim(y0, y1)
    b.set_xlabel("")
    b.set_ylabel("")
    M.scalebar(b, 10_000, color="#1A1A1A", loc=(0.62, 0.03))
    S.fig_label(fig, "b", 1, 33)
    (cx, cy), (px, py) = roi_centers()
    half = 900.0
    for (rx, ry), lab in (((cx, cy), "c"), ((px, py), "d")):
        b.add_patch(__import__("matplotlib").patches.Rectangle((rx - half, ry - half), 2 * half, 2 * half, fill=False,
                                                               edgecolor="white", linewidth=0.7, zorder=5))
        b.text(rx + half + 400, ry + half, lab, color="white", fontsize=6, fontweight="bold", va="top", zorder=6)
    # c–d — ROIs
    xr = 2 + wb + 5
    side = 56.0
    for (rx, ry), lab, ytop in (((cx, cy), "c", 35), ((px, py), "d", 35 + side + 6)):
        ax = ax_mm(fig, xr, ytop, side, side)
        S.dark(ax)
        bbox = (rx - half, ry - half, rx + half, ry + half)
        M.roi(ax, bbox, tipo_by_sql, dark_cols, dark_cols["Favela (FCU)"], edge="#0B0B0E")
        M.scalebar(ax, 500, color="white", loc=(0.06, 0.05))
        S.fig_label(fig, lab, xr - 5, ytop - 2)
    # e — legenda
    xl = xr + side + 5
    e = ax_mm(fig, xl, 37, W - xl - 1, 110)
    e.axis("off")
    order = P.ordered_types(tipos, fam, key)
    nfam = len({fam[tipos.index(x)] for x in order})
    y = 1.0
    step = 1.0 / (len(order) + 1.6 * nfam + 1)
    last = None
    fam_en = {"res_horizontal": "Residential, low-rise", "res_vertical_medio": "Residential, high-rise",
              "res_vertical_alto": "Residential, high standard", "comercio": "Commerce", "servicos": "Services",
              "industria": "Industry", "vazio": "Vacant / green", "favela": "Informal", "sem_cadastro": "Unrecorded"}
    for t in order:
        f = fam[tipos.index(t)]
        if f != last:
            y -= step * 0.6 if last is not None else 0
            e.text(0.0, y, fam_en.get(f, f), fontsize=5.5, fontweight="bold", transform=e.transAxes, va="center")
            y -= step
            last = f
        e.add_patch(__import__("matplotlib").patches.Rectangle((0.0, y - step * 0.32), 0.08, step * 0.64,
                                                               transform=e.transAxes, color=dark_cols[t], clip_on=False))
        e.text(0.11, y, en[tipos.index(t)], fontsize=5.2, transform=e.transAxes, va="center")
        y -= step
    pdf = S.out_dir(periodo) / "fig1.pdf"
    fig.savefig(S.out_dir(periodo) / "fig1.png", dpi=450, facecolor="white")
    a.images[0].remove()
    fig.savefig(pdf, facecolor="white")
    __import__("matplotlib.pyplot").pyplot.close(fig)
    overlay_schema(pdf)
    return pdf


def pd_concat_lines():
    import geopandas as gpd
    import pandas as pd

    g = []
    for f in ("ferrovia_mdc.geojson", "linha_metro.geojson"):
        p = REPO_ROOT / "data" / "external" / "geosampa" / f
        if p.exists():
            g.append(gpd.read_file(p).to_crs(M.CRS)[["geometry"]])
    return gpd.GeoDataFrame(pd.concat(g, ignore_index=True), crs=M.CRS) if g else gpd.GeoDataFrame(geometry=[], crs=M.CRS)
