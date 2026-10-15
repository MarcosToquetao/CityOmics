"""Geocodificador local sobre o CNEFE 2022 (IBGE): endereço ou CEP → coordenada e setor 2022.

O CNEFE tem um ponto por endereço (face de quadra) com o código do setor censitário 2022. O
geocodificador indexa três níveis, do mais fino ao mais grosso:

1. ``numero``: CEP + número do logradouro (média dos pontos com o mesmo par);
2. ``logradouro``: nome normalizado do logradouro + número;
3. ``cep``: centroide dos pontos do CEP (CEP de logradouro, impreciso em ruas longas).

O resultado carrega ``nivel`` para o chamador descartar ou ponderar os níveis grossos. Tudo roda
local; nenhum endereço sai da máquina (D14).
"""

from __future__ import annotations

import re
import unicodedata
import zipfile
from functools import lru_cache

import polars as pl

from cityomics import external
from cityomics.paths import interim_dir

CNEFE_URL = ("https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/"
             "Arquivos_CNEFE/CSV/Municipio/35_SP/3550308_SAO_PAULO.zip")
CNEFE_FILE = "cnefe2022_3550308.zip"

_ABREV = {"R": "RUA", "AV": "AVENIDA", "AL": "ALAMEDA", "TV": "TRAVESSA", "PC": "PRACA", "PCA": "PRACA",
          "EST": "ESTRADA", "ROD": "RODOVIA", "LG": "LARGO", "VL": "VILA", "DR": "DOUTOR", "PROF": "PROFESSOR",
          "ENG": "ENGENHEIRO", "GOV": "GOVERNADOR", "PRES": "PRESIDENTE", "CEL": "CORONEL", "GEN": "GENERAL",
          "STO": "SANTO", "STA": "SANTA", "SAO": "SAO", "MAL": "MARECHAL", "CAP": "CAPITAO", "BRIG": "BRIGADEIRO"}


def norm_logradouro(s: str | None) -> str:
    """Maiúsculas, sem acento nem pontuação, abreviações comuns expandidas."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return " ".join(_ABREV.get(t, t) for t in s.split())


def cnefe_path():
    return interim_dir() / "geocode" / "cnefe_sp.parquet"


def build_cnefe(log=print) -> pl.DataFrame:
    """Extrai do zip do CNEFE os campos úteis para geocodificação."""
    zpath = external.fetch(CNEFE_URL, "ibge", filename=CNEFE_FILE, log=log)
    with zipfile.ZipFile(zpath) as z:
        raw = z.read(z.namelist()[0])
    df = pl.read_csv(raw, separator=";", infer_schema=False, encoding="utf8-lossy")
    df = df.select(
        pl.col("COD_SETOR").str.replace(r"[A-Za-z]+$", "").alias("cd_setor"),  # tira o sufixo P/N (perímetro)
        pl.col("CEP").alias("cep"),
        pl.concat_str([pl.col("NOM_TIPO_SEGLOGR"), pl.col("NOM_TITULO_SEGLOGR"), pl.col("NOM_SEGLOGR")],
                      separator=" ", ignore_nulls=True).alias("logradouro"),
        pl.col("NUM_ENDERECO").cast(pl.Int64, strict=False).alias("numero"),
        pl.col("LATITUDE").cast(pl.Float64, strict=False).alias("lat"),
        pl.col("LONGITUDE").cast(pl.Float64, strict=False).alias("lon"),
    ).filter(pl.col("lat").is_not_null() & pl.col("lon").is_not_null())
    df = df.with_columns(pl.col("logradouro").map_elements(norm_logradouro, return_dtype=pl.String).alias("logradouro"))
    dest = cnefe_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(dest)
    log(f"CNEFE SP: {df.height:,} endereços com coordenada")
    return df


@lru_cache(maxsize=1)
def _indices():
    df = pl.read_parquet(cnefe_path())
    agg = [pl.col("lat").mean(), pl.col("lon").mean(), pl.col("cd_setor").mode().first(), pl.len().alias("n_pts")]
    num = df.filter(pl.col("numero").is_not_null() & (pl.col("numero") > 0))
    por_cep_num = num.group_by("cep", "numero").agg(agg)
    por_log_num = num.filter(pl.col("logradouro") != "").group_by("logradouro", "numero").agg(agg)
    por_cep = df.group_by("cep").agg(agg)
    return por_cep_num, por_log_num, por_cep


def geocode(df: pl.DataFrame) -> pl.DataFrame:
    """Geocodifica ``df`` (colunas ``cep``, ``logradouro``, ``numero``; todas opcionais) e devolve
    ``df`` com ``lat``, ``lon``, ``cd_setor`` e ``nivel`` (numero | logradouro | cep | None)."""
    cep_num, log_num, cep = _indices()
    for c in ("cep", "logradouro", "numero"):
        if c not in df.columns:
            df = df.with_columns(pl.lit(None).alias(c))
    d = df.with_row_index("_i").with_columns(
        pl.col("cep").cast(pl.String).str.replace_all(r"\D", "").str.zfill(8).alias("_cep"),
        pl.col("logradouro").cast(pl.String).map_elements(norm_logradouro, return_dtype=pl.String).alias("_log"),
        pl.col("numero").cast(pl.Int64, strict=False).alias("_num"),
    )
    cols = ["lat", "lon", "cd_setor"]
    a = d.join(cep_num.rename({"cep": "_cep", "numero": "_num"}).select("_cep", "_num", *cols), on=["_cep", "_num"], how="left")
    b = d.join(log_num.rename({"logradouro": "_log", "numero": "_num"}).select("_log", "_num", *cols), on=["_log", "_num"], how="left")
    c = d.join(cep.rename({"cep": "_cep"}).select("_cep", *cols), on="_cep", how="left")
    out = d.select("_i")
    for tag, t in (("numero", a), ("logradouro", b), ("cep", c)):
        t = t.sort("_i").select("_i", pl.col("lat").alias(f"lat_{tag}"), pl.col("lon").alias(f"lon_{tag}"),
                                pl.col("cd_setor").alias(f"set_{tag}"))
        out = out.join(t, on="_i", how="left")
    pick = lambda col: pl.coalesce(*[pl.col(f"{col}_{t}") for t in ("numero", "logradouro", "cep")])  # noqa: E731
    out = out.with_columns(
        pick("lat").alias("lat"), pick("lon").alias("lon"), pick("set").alias("cd_setor"),
        pl.when(pl.col("lat_numero").is_not_null()).then(pl.lit("numero"))
        .when(pl.col("lat_logradouro").is_not_null()).then(pl.lit("logradouro"))
        .when(pl.col("lat_cep").is_not_null()).then(pl.lit("cep")).otherwise(None).alias("nivel"),
    ).select("_i", "lat", "lon", "cd_setor", "nivel")
    return d.join(out, on="_i").drop("_i", "_cep", "_log", "_num").select(
        [c for c in df.columns] + ["lat", "lon", "cd_setor", "nivel"])
