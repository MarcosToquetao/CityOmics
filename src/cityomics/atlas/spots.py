"""Composição dos spots (setores), das metacélulas (quadras) e dos órgãos (distritos) — D21, D51, D54, D59.

Células do tecido:
- **lotes fiscais** tipados (``typing``), com exposição = testada do IPTU (frente para a rua; na
  falta, √área);
- **pseudo-células de favela** = setores FCU do IBGE (D54): uma por setor de favela, com exposição em
  "metros de testada equivalentes" = domicílios ocupados informais × testada mediana por unidade
  dos lotes residenciais horizontais populares. Domicílios informais = domicílios ocupados do setor
  menos as unidades residenciais dos lotes fiscais do mesmo setor (piso zero). Lotes fiscais dentro
  de setores FCU ficam marcados ``em_favela``, sem duplicar área;
- **ruas** (três classes, exposição = comprimento) e **estações/terminais** (contagem), de ``streets``.

Saídas: ``celulas_2025.parquet`` (uma célula por linha: lotes + FCU), ``setor_composicao_2025.parquet``
(contagem e exposição por tipo + ruas e estações), ``quadra_metacelulas_2025.parquet`` e
``distrito_composicao_2025.parquet``. Macrotipos do letal (D61) em ``MACRO``.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.geom import lot_points
from cityomics.paths import processed_dir

MACRO = {
    "res_horizontal": "residencial_popular", "favela": "residencial_popular",
    "res_vertical_medio": "residencial_formal", "res_vertical_alto": "residencial_formal",
    "comercio": "comercio_servicos", "servicos": "comercio_servicos",
    "industria": "industria_vazio", "vazio": "industria_vazio", "sem_cadastro": "industria_vazio",
}
RUAS = ["rua_arterial_m", "rua_coletora_m", "rua_local_m"]
ESTACOES = ["n_trilho", "n_terminal"]


def setores_attrs() -> pl.DataFrame:
    import pyarrow.parquet as pq

    t = pq.read_table(processed_dir() / "units" / "setores_2022.parquet",
                      columns=["cd_setor", "cd_dist", "favela", "pop_2022", "dom_ocupados_2022", "area_km2"])
    return pl.from_arrow(t).with_columns(pl.col("cd_setor").cast(pl.String), pl.col("cd_dist").cast(pl.String))


def cells(log=print) -> pl.DataFrame:
    tipos = pl.read_parquet(atlas_dir() / f"lote_tipos_{REF_YEAR}.parquet")
    genes = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet",
                            columns=["sql_base", "testada", "area_terreno", "n_unidades", "uso_residencial"])
    pts = lot_points().filter(pl.col("origem") == "lote_fiscal").select("sql_base", "x", "y", "setor_fiscal", "quadra_fiscal", "area_m2")
    st = setores_attrs()
    c = (tipos.join(genes, on="sql_base", how="left").join(pts, on="sql_base", how="left")
         .join(st.select("cd_setor", pl.col("favela").alias("em_favela")), on="cd_setor", how="left"))
    c = c.with_columns(
        pl.when(pl.col("testada") > 0).then(pl.col("testada")).otherwise(pl.col("area_m2").sqrt()).alias("exposicao"),
        (pl.col("setor_fiscal") + "-" + pl.col("quadra_fiscal")).alias("quadra"),
        pl.lit("lote").alias("classe"))
    # testada por unidade nos lotes residenciais horizontais populares → equivalência das favelas
    pop = c.filter((pl.col("familia") == "res_horizontal") & (pl.col("n_unidades") > 0))
    t_unid = float((pop["exposicao"] / pop["n_unidades"]).median())
    unid_res = (c.filter(pl.col("em_favela").fill_null(False))
                .group_by("cd_setor").agg((pl.col("n_unidades") * pl.col("uso_residencial")).sum().alias("unid_formais")))
    fcu = (st.filter(pl.col("favela")).join(unid_res, on="cd_setor", how="left")
           .with_columns((pl.col("dom_ocupados_2022") - pl.col("unid_formais").fill_null(0)).clip(0, None).alias("dom_informais")))
    import geopandas as gpd

    geo = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    geo = geo[geo["cd_setor"].astype(str).isin(fcu["cd_setor"].to_list())]
    rp = geo.geometry.representative_point()
    xy = pl.DataFrame({"cd_setor": geo["cd_setor"].astype(str).to_numpy(), "x": rp.x.to_numpy(), "y": rp.y.to_numpy()})
    fav = (fcu.join(xy, on="cd_setor", how="left").select(
        ("FCU" + pl.col("cd_setor")).alias("sql_base"), "cd_setor", "cd_dist",
        pl.lit(-2).alias("cluster"), pl.lit(1.0, dtype=pl.Float32).alias("conf"),
        pl.lit("Favela (FCU)").alias("tipo"), pl.lit("favela").alias("familia"),
        (pl.col("dom_informais") * t_unid).alias("exposicao"), "x", "y",
        ("FCU" + pl.col("cd_setor")).alias("quadra"), pl.lit("favela").alias("classe"), pl.lit(True).alias("em_favela"),
        pl.col("dom_informais")))
    keep = ["sql_base", "cd_setor", "cd_dist", "cluster", "conf", "tipo", "familia", "exposicao", "x", "y", "quadra", "classe", "em_favela"]
    out = pl.concat([c.select(keep).with_columns(pl.lit(None, dtype=pl.Float64).alias("dom_informais")),
                     fav.select(keep + ["dom_informais"]).with_columns(pl.col("cluster").cast(c["cluster"].dtype))],
                    how="vertical_relaxed")
    out = out.with_columns(pl.col("familia").replace_strict(MACRO, default="industria_vazio").alias("macro"))
    log(f"células: {c.height:,} lotes + {fav.height:,} pseudo-células FCU (testada/unidade popular = {t_unid:.1f} m)")
    out.write_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet")
    return out


def compositions(cel: pl.DataFrame, log=print) -> dict[str, pl.DataFrame]:
    d = atlas_dir()
    rua = pl.read_parquet(d / "setor_ruas_estacoes.parquet").with_columns(pl.col("cd_setor").cast(pl.String))
    tipos = sorted(cel["tipo"].unique().to_list())
    n = cel.pivot(on="tipo", index="cd_setor", values="sql_base", aggregate_function="len").fill_null(0)
    e = cel.pivot(on="tipo", index="cd_setor", values="exposicao", aggregate_function="sum").fill_null(0.0)
    n = n.rename({t: f"n|{t}" for t in tipos if t in n.columns})
    e = e.rename({t: f"e|{t}" for t in tipos if t in e.columns})
    st = setores_attrs()
    setor = st.join(n, on="cd_setor", how="left").join(e, on="cd_setor", how="left").join(rua, on="cd_setor", how="left").fill_null(0)
    setor.write_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    q = (cel.group_by("quadra").agg(pl.col("x").mean(), pl.col("y").mean(), pl.col("cd_setor").mode().first(),
                                    pl.col("cd_dist").mode().first(), pl.len().alias("n_celulas"),
                                    pl.col("exposicao").sum()))
    qn = cel.pivot(on="tipo", index="quadra", values="sql_base", aggregate_function="len").fill_null(0)
    q = q.join(qn.rename({t: f"n|{t}" for t in tipos if t in qn.columns}), on="quadra", how="left")
    q.write_parquet(d / f"quadra_metacelulas_{REF_YEAR}.parquet")
    num = [c for c in setor.columns if c.startswith(("n|", "e|")) or c in RUAS + ESTACOES + ["pop_2022", "dom_ocupados_2022", "area_km2"]]
    dist = setor.group_by("cd_dist").agg([pl.col(c).sum() for c in num])
    dist.write_parquet(d / f"distrito_composicao_{REF_YEAR}.parquet")
    log(f"composições: {setor.height:,} setores, {q.height:,} quadras, {dist.height} distritos; {len(tipos)} tipos")
    return {"setor": setor, "quadra": q, "distrito": dist}


def build(log=print) -> dict[str, pl.DataFrame]:
    return compositions(cells(log=log), log=log)


def exposure_matrix(setor: pl.DataFrame, by: str = "tipo") -> tuple[np.ndarray, list[str]]:
    """Matriz de exposição (setores × classes de célula): tipos de lote (testada), ruas (m) e estações (n)."""
    cols = [c for c in setor.columns if c.startswith("e|")] + RUAS + ESTACOES
    names = [c[2:] if c.startswith("e|") else c for c in cols]
    return setor.select(cols).to_numpy().astype(np.float64), names
