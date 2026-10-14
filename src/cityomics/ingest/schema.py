"""Schema canônico dos microdados da SSP (spec-dados §1.1).

Os nomes de coluna mudam entre anos e entre bases (2022 usa ``CIDADE`` e
``DATA_COMUNICACAO_BO``; até 2025 as colunas de circunscrição vêm com o typo
``CIRCUNCRIÇÃO``; a base de celular usa o sufixo ``_CIRC``). Aqui tudo é reduzido a um
nome normalizado (maiúsculas, sem acento) e depois mapeado para o schema canônico.
"""

from __future__ import annotations

import unicodedata

import numpy as np
import pandas as pd

# Caixa generosa do município de São Paulo (graus decimais), como no MapaSegurancaSP
LAT_MIN, LAT_MAX = -24.10, -23.30
LON_MIN, LON_MAX = -47.00, -46.30
MIN_FACT_DATE = pd.Timestamp("2003-01-01")


def norm_text(value) -> str:
    """Maiúsculas, sem acento, travessão como hífen, espaços colapsados."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    s = str(value).replace("–", "-").replace("—", "-")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def norm_col(name) -> str:
    return norm_text(name).replace(" ", "_")


# nome normalizado na fonte -> nome canônico
COLUMN_MAP = {
    # registro
    "NOME_DELEGACIA": "delegacia_registro",
    "ID_DELEGACIA": "id_delegacia",
    "NOME_MUNICIPIO": "municipio_registro",
    "CIDADE": "cidade",  # 2022 na base principal = município de registro; no celular = cidade do endereço
    "ANO_BO": "ano_bo",
    "NUM_BO": "num_bo",
    "VERSAO": "versao",
    # local do fato (circunscrição)
    "NOME_MUNICIPIO_CIRCUNCRICAO": "municipio_fato",
    "NOME_MUNICIPIO_CIRCUNSCRICAO": "municipio_fato",
    "NOME_MUNICIPIO_CIRC": "municipio_fato",
    "NOME_DELEGACIA_CIRCUNCRICAO": "dp_fato",
    "NOME_DELEGACIA_CIRCUNSCRICAO": "dp_fato",
    "NOME_DELEGACIA_CIRC": "dp_fato",
    "NOME_SECCIONAL_CIRCUNCRICAO": "seccional_fato",
    "NOME_SECCIONAL_CIRCUNSCRICAO": "seccional_fato",
    "NOME_SECCIONAL_CIRC": "seccional_fato",
    # datas
    "DATA_REGISTRO": "data_registro",
    "DATA_COMUNICACAO_BO": "data_registro",
    "DATAHORA_REGISTRO_BO": "data_registro",
    "DATA_OCORRENCIA_BO": "data_fato",
    "HORA_OCORRENCIA_BO": "hora_fato",
    "HORA_OCORRENCIA": "hora_fato",
    "DESC_PERIODO": "periodo",
    "DESCR_PERIODO": "periodo",
    "MES_ESTATISTICA": "mes_estatistica",
    "ANO_ESTATISTICA": "ano_estatistica",
    "MES_REGISTRO_BO": "mes_estatistica",
    "ANO_REGISTRO_BO": "ano_estatistica",
    "MES": "mes_estatistica",
    "ANO": "ano_estatistica",
    # local
    "DESCR_TIPOLOCAL": "tipolocal",
    "DESCR_SUBTIPOLOCAL": "subtipolocal",
    "BAIRRO": "bairro",
    "CEP": "cep",
    "LOGRADOURO": "logradouro",
    "NUMERO_LOGRADOURO": "numero_logradouro",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    # classificação
    "RUBRICA": "rubrica",
    "DESCR_CONDUTA": "conduta",
    "NATUREZA_APURADA": "natureza",
    "FLAG_STATUS": "status",
}

CANONICAL = [
    "fonte", "arquivo_ano", "delegacia_registro", "id_delegacia", "ano_bo", "num_bo", "versao",
    "municipio_fato", "dp_fato", "seccional_fato", "cidade",
    "data_registro", "data_fato", "hora_fato", "periodo", "mes_estatistica", "ano_estatistica",
    "tipolocal", "subtipolocal", "bairro", "cep", "logradouro", "numero_logradouro",
    "latitude", "longitude", "coord_valida", "rubrica", "conduta", "natureza", "natureza_norm",
    "status",
]

_TEXT = ["delegacia_registro", "id_delegacia", "ano_bo", "num_bo", "municipio_fato", "dp_fato",
         "seccional_fato", "cidade", "hora_fato", "periodo", "tipolocal", "subtipolocal", "bairro",
         "cep", "logradouro", "numero_logradouro", "rubrica", "conduta", "natureza", "status"]
_NULLS = {"NULL", "", "NONE", "NAN", "NAT"}


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {}
    for col in df.columns:
        canon = COLUMN_MAP.get(norm_col(col))
        if canon and canon not in mapping.values():
            mapping[col] = canon
    return df[list(mapping)].rename(columns=mapping)


def _clean_text(s: pd.Series) -> pd.Series:
    out = s.astype("string").str.strip()
    return out.mask(out.str.upper().isin(_NULLS))


def _parse_dates(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s
    # textos com barra são sempre dd/mm/aaaa (padrão brasileiro); o resto é ISO ou datetime
    slash = s.map(lambda v: isinstance(v, str) and "/" in v)
    out = pd.to_datetime(s.where(~slash), errors="coerce", format="mixed")
    if slash.any():
        out = out.fillna(pd.to_datetime(s.where(slash), errors="coerce", dayfirst=True, format="mixed"))
    return out


def harmonize(df: pd.DataFrame, fonte: str, arquivo_ano: int) -> pd.DataFrame:
    """Aplica o schema canônico a uma aba já lida (todas as linhas, qualquer município)."""
    df = rename_columns(df)
    for col in CANONICAL:
        if col not in df.columns:
            df[col] = pd.NA
    df["fonte"] = fonte
    df["arquivo_ano"] = arquivo_ano

    for col in _TEXT:
        df[col] = _clean_text(df[col])
    # 2022 (base principal) só tem CIDADE de registro; sem coluna de fato usa-se ela
    df["municipio_fato"] = df["municipio_fato"].fillna(df["cidade"] if fonte == "ssp" else pd.NA)

    df["data_registro"] = _parse_dates(df["data_registro"]).dt.normalize()
    df["data_fato"] = _parse_dates(df["data_fato"]).dt.normalize()
    df.loc[df["data_fato"] < MIN_FACT_DATE, "data_fato"] = pd.NaT

    # MES/ANO_ESTATISTICA às vezes vêm como fórmula Excel não avaliada ("=MONTH(G12)")
    for col, attr in (("mes_estatistica", "month"), ("ano_estatistica", "year")):
        num = pd.to_numeric(df[col], errors="coerce")
        df[col] = num.fillna(getattr(df["data_registro"].dt, attr)).astype("Int64")

    for col in ("latitude", "longitude"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    ok = df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LON_MIN, LON_MAX)
    df["coord_valida"] = ok.fillna(False).astype(bool)
    df.loc[~df["coord_valida"], ["latitude", "longitude"]] = np.nan

    df["natureza_norm"] = df["natureza"].map(norm_text).astype("string")
    df["versao"] = pd.to_numeric(df["versao"], errors="coerce").astype("Int64")
    return df[CANONICAL]


def is_capital(municipio: pd.Series) -> pd.Series:
    return municipio.map(norm_text).eq("S.PAULO")
