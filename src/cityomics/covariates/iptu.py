"""Cadastro IPTU/TPCL anual → atributos nativos por lote (spec-dados §3.1, D22).

Cada emissão anual (``IPTU_<ano>.zip``, CSV ``;``) tem uma linha por imóvel tributado.
O número do contribuinte é o SQL: setor (3) + quadra (3) + lote (4) + dígito.
Unidades de condomínio (``NUMERO DO CONDOMINIO`` ≠ ``00-0``) são agregadas ao lote do
condomínio, identificado por setor + quadra + código do condomínio na camada de lotes.

Saída por lote e ano: número de unidades, áreas, pavimentos, idade, valores do m² e a
composição de usos e de padrões construtivos (frações de unidades).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import polars as pl

from cityomics import external
from cityomics.paths import interim_dir

COLS = {
    "NUMERO DO CONTRIBUINTE": "sql", "ANO DO EXERCICIO": "ano", "NUMERO DO CONDOMINIO": "condominio",
    "AREA DO TERRENO": "area_terreno", "AREA CONSTRUIDA": "area_construida", "AREA OCUPADA": "area_ocupada",
    "VALOR DO M2 DO TERRENO": "valor_m2_terreno", "VALOR DO M2 DE CONSTRUCAO": "valor_m2_construcao",
    "ANO DA CONSTRUCAO CORRIGIDO": "ano_construcao", "QUANTIDADE DE PAVIMENTOS": "pavimentos",
    "TIPO DE USO DO IMOVEL": "uso", "TIPO DE PADRAO DA CONSTRUCAO": "padrao", "FRACAO IDEAL": "fracao_ideal",
}
NUMERIC = ["area_terreno", "area_construida", "area_ocupada", "valor_m2_terreno", "valor_m2_construcao",
           "ano_construcao", "pavimentos", "fracao_ideal"]

# Grupos de uso e de padrão (o texto da fonte varia entre anos)
USO_GRUPOS = {
    "residencial": r"(?i)resid|apartamento|casa",
    "comercio": r"(?i)loja|comerci|escritorio|escritório|banco|hotel|garagem.*comerc",
    "servicos": r"(?i)servi|hospital|escola|templo|clube|cinema|teatro|posto",
    "industria": r"(?i)industr|armaz|deposito|depósito|oficina",
    "terreno": r"(?i)terreno|lote vago|sem constru",
}
PADRAO_GRUPOS = {"padrao_baixo": r"(?i)padr[aã]o [AB]\b", "padrao_medio": r"(?i)padr[aã]o C\b",
                 "padrao_alto": r"(?i)padr[aã]o [DEF]\b"}


def iptu_zip(year: int) -> Path:
    return external.external_dir() / "geosampa" / "iptu" / f"IPTU_{year}.zip"


def read_year(year: int) -> pl.DataFrame:
    with zipfile.ZipFile(iptu_zip(year)) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        raw = z.read(name)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    # O arquivo não usa aspas como delimitador, e há endereços com aspas soltas (2024)
    df = pl.read_csv(text.encode(), separator=";", infer_schema=False, quote_char=None, truncate_ragged_lines=True)
    df = df.rename({c: COLS[c.strip().upper()] for c in df.columns if c.strip().upper() in COLS})
    df = df.select([c for c in COLS.values() if c in df.columns])
    return df.with_columns(
        [pl.col(c).str.replace(",", ".").cast(pl.Float64, strict=False) for c in NUMERIC if c in df.columns]
    ).with_columns(
        pl.col("sql").str.replace_all(r"[^0-9]", "").alias("sql_digits"),
        pl.col("condominio").str.replace_all(r"[^0-9]", "").str.slice(0, 2).alias("cond2"),
    ).with_columns(
        pl.col("sql_digits").str.slice(0, 3).alias("setor_fiscal"),
        pl.col("sql_digits").str.slice(3, 3).alias("quadra_fiscal"),
        pl.col("sql_digits").str.slice(6, 4).alias("lote"),
    )


def lot_keys(df: pl.DataFrame, condo_lookup: pl.DataFrame) -> pl.DataFrame:
    """Chave do lote: sql_base para imóveis comuns; para condomínios, o sql_base do lote
    da camada fiscal com o mesmo setor + quadra + condomínio."""
    is_condo = pl.col("cond2").is_not_null() & (pl.col("cond2") != "00")
    df = df.with_columns(
        pl.when(is_condo).then(None).otherwise(pl.col("setor_fiscal") + pl.col("quadra_fiscal") + pl.col("lote"))
        .alias("sql_base")
    )
    df = df.join(condo_lookup, on=["setor_fiscal", "quadra_fiscal", "cond2"], how="left")
    return df.with_columns(pl.coalesce("sql_base", "sql_base_condo").alias("sql_base")).drop("sql_base_condo")


def aggregate(df: pl.DataFrame) -> pl.DataFrame:
    exprs = [
        pl.len().alias("n_unidades"),
        pl.col("area_terreno").max().alias("area_terreno"),
        pl.col("area_construida").sum().alias("area_construida"),
        pl.col("pavimentos").max().alias("pavimentos"),
        pl.col("ano_construcao").median().alias("ano_construcao"),
        pl.col("valor_m2_terreno").mean().alias("valor_m2_terreno"),
        pl.col("valor_m2_construcao").mean().alias("valor_m2_construcao"),
    ]
    exprs += [pl.col("uso").str.contains(rx).mean().alias(f"uso_{k}") for k, rx in USO_GRUPOS.items()]
    exprs += [pl.col("padrao").str.contains(rx).mean().alias(k) for k, rx in PADRAO_GRUPOS.items()]
    return df.group_by("sql_base").agg(exprs)


def build_year(year: int, condo_lookup: pl.DataFrame) -> tuple[pl.DataFrame, float]:
    df = lot_keys(read_year(year), condo_lookup)
    matched = df["sql_base"].is_not_null().mean()
    out = aggregate(df.filter(pl.col("sql_base").is_not_null())).with_columns(pl.lit(year).alias("ano"))
    (interim_dir() / "iptu").mkdir(parents=True, exist_ok=True)
    out.write_parquet(interim_dir() / "iptu" / f"iptu_lote_{year}.parquet")
    return out, matched


def condo_lookup_from(lotes) -> pl.DataFrame:
    lf = lotes[(lotes["origem"] == "lote_fiscal") & (lotes["condominio"] != "00")]
    look = lf[["setor_fiscal", "quadra_fiscal", "condominio", "sql_base"]].drop_duplicates(
        ["setor_fiscal", "quadra_fiscal", "condominio"])
    return pl.from_pandas(look.rename(columns={"condominio": "cond2", "sql_base": "sql_base_condo"})
                          .astype("string"))
