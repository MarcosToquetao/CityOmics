"""População anual por setor, atualização dasimétrica (spec-dados §3.3).

O Censo dá a população de 2010 e 2022. Entre censos (e depois de 2022) a população de cada setor
é estimada pela **oferta residencial** do IPTU: unidades residenciais (``n_unidades`` ×
``uso_residencial``) somadas por setor em cada ano. Para o ano ``a``:

    pop(a) = pop_2022 × unidades_res(a) / unidades_res(2022)

com a razão limitada a [0,25; 4] e, onde o setor tinha menos de 3 unidades residenciais em 2022,
a população de 2022 sem correção. O IPTU do ano ``a`` é emitido no começo de ``a``; a estimativa
de ``a`` fica disponível no mesmo ano (spec-dados §3.3). Para ``a`` > 2026 vale o de 2026.

Limite: mede oferta de domicílios, não ocupação; favelas (pseudo-lotes) e cortiços ficam
subestimados no IPTU. Uma variação de moradores por domicílio ou de vacância não é capturada.

Saída: ``data/processed/covariaveis/setor_pop_ano.parquet`` (setor × ano, 2015-2027).
"""

from __future__ import annotations

import polars as pl

from cityomics.paths import interim_dir, processed_dir

ANOS = range(2015, 2028)
REF = 2022


def unidades_res_por_setor(anos=range(2015, 2027)) -> pl.DataFrame:
    lotes = pl.read_parquet(processed_dir() / "units" / "lotes.parquet", columns=["sql_base", "cd_setor"]) \
        .filter(pl.col("sql_base").is_not_null() & pl.col("cd_setor").is_not_null()).unique("sql_base")
    quadros = []
    for ano in anos:
        iptu = pl.read_parquet(interim_dir() / "iptu" / f"iptu_lote_{ano}.parquet", columns=["sql_base", "n_unidades", "uso_residencial"])
        j = iptu.join(lotes, on="sql_base", how="inner")
        quadros.append(j.group_by("cd_setor").agg((pl.col("n_unidades") * pl.col("uso_residencial")).sum().alias("unid_res"))
                       .with_columns(pl.lit(ano).alias("ano")))
    return pl.concat(quadros)


def estimar(unid: pl.DataFrame, pop22: pl.DataFrame, anos=ANOS) -> pl.DataFrame:
    """``unid``: setor×ano com unid_res; ``pop22``: cd_setor, pop. Devolve cd_setor, ano, pop_dasi."""
    ref = unid.filter(pl.col("ano") == REF).select("cd_setor", pl.col("unid_res").alias("u_ref"))
    base = pop22.join(ref, on="cd_setor", how="left").with_columns(pl.col("u_ref").fill_null(0))
    ultimo = int(unid["ano"].max())
    quadros = []
    for ano in anos:
        u = unid.filter(pl.col("ano") == min(ano, ultimo)).select("cd_setor", "unid_res")
        j = base.join(u, on="cd_setor", how="left").with_columns(pl.col("unid_res").fill_null(0))
        razao = (pl.col("unid_res") / pl.col("u_ref")).clip(0.25, 4.0)
        quadros.append(j.select("cd_setor", pl.lit(ano).alias("ano"),
                                pl.when(pl.col("u_ref") >= 3).then(pl.col("pop") * razao).otherwise(pl.col("pop")).alias("pop_dasi"),
                                pl.col("unid_res").alias("unid_res_ano")))
    return pl.concat(quadros)


def build(log=print) -> pl.DataFrame:
    unid = unidades_res_por_setor()
    pop22 = pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet").select("cd_setor", "pop") \
        .filter(pl.col("pop").is_not_null())
    out = estimar(unid, pop22)
    out.write_parquet(processed_dir() / "covariaveis" / "setor_pop_ano.parquet")
    tot = out.group_by("ano").agg(pl.col("pop_dasi").sum()).sort("ano")
    log("população dasimétrica da cidade por ano: " + ", ".join(f"{a}: {p/1e6:.2f} mi" for a, p in tot.iter_rows()))
    return out
