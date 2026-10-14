"""ITBI: transações imobiliárias por lote e mês (spec-dados §3.1, D22, D23).

Fonte: Secretaria da Fazenda, "Guias de ITBI pagas", um XLSX por ano com abas mensais
(2006 a 2026, o ano corrente atualizado mensalmente). Cada linha é uma transação, com SQL,
natureza, valor declarado, data, valor venal de referência, financiamento e áreas.

O SQL de unidades em condomínio identifica a unidade, não o lote. A ligação com o lote usa
o cadastro IPTU do mesmo ano (``covariates.iptu``), que dá o lote de cada SQL.

Saídas:
- ``data/interim/itbi/transacoes_<ano>.parquet``: uma linha por transação, com o lote;
- ``data/interim/itbi/itbi_lote_mes.parquet``: por lote e mês (transações ligadas a lote existente);
- ``data/interim/itbi/itbi_setor_mes.parquet``: por setor 2022 e mês, incluindo transações de
  lotes já extintos (unificados ou desmembrados), atribuídas pela quadra fiscal.

Transações em lotes que depois desaparecem do cadastro são um sinal de incorporação
imobiliária (compra de casas vizinhas → unificação → prédio), não um erro de ligação.
"""

from __future__ import annotations

import polars as pl

from cityomics import external
from cityomics.covariates import iptu
from cityomics.paths import interim_dir

_BASE = "https://www.prefeitura.sp.gov.br/cidade/secretarias/upload/fazenda/arquivos/"
URLS = {y: _BASE + f"itbi/guias_de_itbi_pagas_{y}.xlsx" for y in range(2006, 2019)}
URLS.update({y: _BASE + f"itbi/ITBI_Setembro_2022/GUIAS_DE_ITBI_PAGAS_({y}).xlsx" for y in (2019, 2020, 2021)})
URLS.update({
    2022: _BASE + "XLSX/GUIAS_DE_ITBI_PAGAS_12-2022.xlsx",
    2023: _BASE + "XLSX/GUIAS-DE-ITBI-PAGAS-2023.xlsx",
    2024: _BASE + "itbi/GUIAS-DE-ITBI-PAGAS-2024.xlsx",
    2025: _BASE + "itbi/GUIAS%20DE%20ITBI%20PAGAS%20%2828012026%29%20XLS.xlsx",
    2026: _BASE + "itbi/GUIAS%20DE%20ITBI%20PAGAS%20%2830092026%29.xlsx",
})

COLS = {  # início normalizado do cabeçalho -> nome canônico
    "N° DO CADASTRO": "sql", "NATUREZA DE TRANSACAO": "natureza",
    "VALOR DE TRANSACAO": "valor_transacao", "DATA DE TRANSACAO": "data_transacao",
    "VALOR VENAL DE REFERENCIA (PROPORCIONAL)": "valor_venal_prop", "TIPO DE FINANCIAMENTO": "financiamento",
    "VALOR FINANCIADO": "valor_financiado", "AREA DO TERRENO": "area_terreno",
    "AREA CONSTRUIDA": "area_construida", "FRACAO IDEAL": "fracao_ideal", "USO (IPTU)": "uso",
    "PADRAO (IPTU)": "padrao",
}


def itbi_dir():
    d = interim_dir() / "itbi"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_all(years=None, log=print):
    return {y: external.fetch(URLS[y], "fazenda/itbi", filename=f"ITBI_{y}.xlsx", log=log)
            for y in (years or sorted(URLS))}


def _canon(header: str) -> str | None:
    from cityomics.ingest.schema import norm_text
    h = norm_text(header).replace("Nº", "N°")
    for prefix, name in COLS.items():
        if h.startswith(norm_text(prefix)) or h.startswith(prefix):
            return name
    return None


def read_year(year: int) -> pl.DataFrame:
    import pandas as pd

    path = external.external_dir() / "fazenda" / "itbi" / f"ITBI_{year}.xlsx"
    xl = pd.ExcelFile(path, engine="calamine")
    frames = []
    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        mapping = {}
        for col in df.columns:
            name = _canon(str(col))
            if name and name not in mapping.values():
                mapping[col] = name
        if "sql" not in mapping.values() or "data_transacao" not in mapping.values():
            continue  # abas de legenda e tabelas auxiliares
        frames.append(df[list(mapping)].rename(columns=mapping).astype(str))
    raw = pl.from_pandas(pd.concat(frames, ignore_index=True))
    num = ["valor_transacao", "valor_venal_prop", "valor_financiado", "area_terreno", "area_construida", "fracao_ideal"]
    return raw.with_columns(
        [pl.col(c).str.replace(",", ".").cast(pl.Float64, strict=False) for c in num if c in raw.columns]
    ).with_columns(
        pl.col("sql").str.replace(r"\.0$", "").str.replace_all(r"[^0-9]", "").str.zfill(11).str.slice(0, 10)
        .alias("sql10"),
        pl.col("data_transacao").str.slice(0, 10).str.to_date(strict=False).alias("data"),
    )


def _iptu_sql_map(y: int, condo_lookup: pl.DataFrame) -> pl.DataFrame | None:
    """Mapa SQL (10 dígitos) → lote para um ano do IPTU, com cache em disco."""
    cache = itbi_dir() / f"iptu_sql_map_{y}.parquet"
    if cache.exists():
        return pl.read_parquet(cache)
    if not iptu.iptu_zip(y).exists():
        return None
    df = iptu.lot_keys(iptu.read_year(y), condo_lookup)
    out = (df.select(pl.col("sql_digits").str.slice(0, 10).alias("sql10"), "sql_base")
             .filter(pl.col("sql_base").is_not_null()).unique("sql10"))
    out.write_parquet(cache)
    return out


def sql_map(year: int, condo_lookup: pl.DataFrame) -> pl.DataFrame:
    """SQL (10 dígitos) → lote, pelos cadastros IPTU do ano, do seguinte e do anterior, nessa
    ordem de preferência. Unidades novas (lançamentos) só aparecem no IPTU do ano seguinte."""
    maps = [m.with_columns(pl.lit(rank).alias("rank"))
            for rank, y in enumerate((year, year + 1, year - 1))
            if (m := _iptu_sql_map(y, condo_lookup)) is not None]
    if not maps:
        raise FileNotFoundError(f"sem IPTU para {year}")
    return pl.concat(maps).sort("rank").unique("sql10", keep="first").drop("rank")


def build_year(year: int, condo_lookup: pl.DataFrame) -> tuple[pl.DataFrame, float]:
    tx = read_year(year)
    tx = tx.join(sql_map(year, condo_lookup), on="sql10", how="left").with_columns(
        pl.when(pl.col("sql_base").is_null())
        .then(pl.col("sql10"))  # imóvel comum fora do cadastro do ano: a chave do SQL é a do lote
        .otherwise(pl.col("sql_base")).alias("sql_base")
    )
    area = pl.when(pl.col("area_construida") > 0).then(pl.col("area_construida")).otherwise(pl.col("area_terreno")
                                                                                          * pl.col("fracao_ideal"))
    tx = tx.with_columns(
        pl.when(area > 0).then(pl.col("valor_transacao") / area).otherwise(None).alias("preco_m2"),
        (pl.col("valor_financiado").fill_null(0) > 0).alias("financiada"),
        pl.col("sql10").str.slice(0, 6).alias("quadra_key"),
    ).select("sql_base", "sql10", "quadra_key", "data", "natureza", "valor_transacao", "valor_venal_prop",
             "preco_m2", "financiada", "uso", "padrao")
    tx.write_parquet(itbi_dir() / f"transacoes_{year}.parquet")
    with_date = tx["data"].is_not_null().mean()
    return tx, with_date


AGG = [pl.len().alias("n_transacoes"),
       pl.col("valor_transacao").sum().alias("valor_total"),
       pl.col("preco_m2").median().alias("preco_m2_mediana"),
       pl.col("financiada").mean().alias("frac_financiada")]


def _transactions(start: str = "2006-01-01") -> pl.DataFrame:
    tx = pl.concat([pl.read_parquet(p) for p in sorted(itbi_dir().glob("transacoes_*.parquet"))])
    return (tx.filter(pl.col("data") >= pl.lit(start).str.to_date())
              .with_columns(pl.col("data").dt.truncate("1mo").alias("mes")))


def monthly_tables(lotes) -> dict[str, pl.DataFrame]:
    """Tabelas mensais por lote (só transações ligadas a um lote existente) e por setor 2022
    (todas, pelo lote ou, sem lote, pela quadra fiscal → setor da maioria dos seus lotes)."""
    cells = pl.from_pandas(lotes.loc[lotes["origem"] == "lote_fiscal", ["sql_base", "cd_setor"]].astype("string"))
    lot_setor = cells.unique("sql_base")
    quadra_setor = (cells.with_columns(pl.col("sql_base").str.slice(0, 6).alias("quadra_key"))
                    .group_by("quadra_key", "cd_setor").len().sort("len", descending=True)
                    .unique("quadra_key", keep="first").select("quadra_key", pl.col("cd_setor").alias("setor_q")))
    tx = (_transactions().join(lot_setor, on="sql_base", how="left")
                         .join(quadra_setor, on="quadra_key", how="left")
                         .with_columns(pl.col("cd_setor").is_not_null().alias("lote_existe"),
                                       pl.coalesce("cd_setor", "setor_q").alias("cd_setor")))
    por_lote = tx.filter(pl.col("lote_existe")).group_by("sql_base", "mes").agg(AGG)
    por_setor = tx.filter(pl.col("cd_setor").is_not_null()).group_by("cd_setor", "mes").agg(
        AGG + [(~pl.col("lote_existe")).mean().alias("frac_lote_extinto")])
    por_lote.write_parquet(itbi_dir() / "itbi_lote_mes.parquet")
    por_setor.write_parquet(itbi_dir() / "itbi_setor_mes.parquet")
    resumo = {"transacoes": tx.height, "com_lote": tx["lote_existe"].mean(),
              "com_setor": tx["cd_setor"].is_not_null().mean()}
    return {"lote": por_lote, "setor": por_setor, "resumo": resumo}
