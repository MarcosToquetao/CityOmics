"""Agências bancárias por setor (spec-dados §3.2, T2), do Banco Central.

Fonte: serviço Olinda ``Informes_Agencias`` do BCB (OData, sem chave): agências e postos de
instituições financeiras em funcionamento, com endereço, CEP e data de início. Só há a
fotografia atual (posição de 14/10/2026); agências já fechadas não aparecem, então o estoque
histórico por mês **subestima o passado** (viés de sobrevivência): uma agência aberta em 2012
e fechada em 2020 não consta. A série vale como covariável de contexto (presença de agência,
distância), não como contagem de estabelecimentos comparável ao longo do tempo.

Os endereços são geocodificados localmente pelo CNEFE (``cityomics.geocode``); só entram os
níveis ``numero`` e ``logradouro``, e o nível ``cep`` é guardado com a marca para sensibilidade.
Caixas eletrônicos externos não têm base aberta com endereço.

Saídas:
- ``data/interim/bcb/agencias_sp.parquet``: uma agência por linha (sem telefone nem nome da agência);
- ``data/processed/covariaveis/setor_bcb_mes.parquet``: setor × mês, agências em operação (estoque).
"""

from __future__ import annotations

import json
import re

import polars as pl
import requests

from cityomics import external, geocode
from cityomics.paths import interim_dir, processed_dir

URL = "https://olinda.bcb.gov.br/olinda/servico/Informes_Agencias/versao/v1/odata/Agencias"
CD_MUN_SP = "3550308"


def fetch(log=print) -> list[dict]:
    dest = external.external_dir() / "bcb" / "agencias_sp.json"
    # o Olinda recusa "+" como espaço: monta a query com %20 e limite menor
    url = f"{URL}?$filter=MunicipioIbge%20eq%20'{CD_MUN_SP}'&$format=json&$top=20000"
    r = requests.get(url, timeout=300, headers={"User-Agent": "CityOmics research pipeline"})
    r.raise_for_status()
    rows = r.json()["value"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rows, ensure_ascii=False))
    from cityomics.ingest.snapshot import sha256
    import pandas as pd
    manifest = external.load_manifest()
    manifest["bcb/agencias_sp.json"] = {"url": f"{URL}?$filter=MunicipioIbge eq '{CD_MUN_SP}'", "size": dest.stat().st_size,
                                        "sha256": sha256(dest), "recorded_at": pd.Timestamp.now("UTC").isoformat(timespec="seconds")}
    external.manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    log(f"BCB: {len(rows):,} agências em SP (posição {rows[0]['Posicao'] if rows else '?'})")
    return rows


def split_endereco(end: str | None, numero: str | None) -> tuple[str, int | None]:
    """'RUA X, NUM 381' → ('RUA X', 381). O campo Numero costuma vir vazio."""
    end = end or ""
    m = re.search(r"(?:,|\s)\s*(?:NUM|N[ºO°]?|NUMERO)?\s*\.?\s*(\d{1,6})\s*$", end.upper())
    num = int(m.group(1)) if m else None
    if not num and numero and numero.strip().isdigit():
        num = int(numero)
    rua = re.sub(r"[,\s]+(?:NUM|N[ºO°]?|NUMERO)?\s*\.?\s*\d{1,6}\s*$", "", end.upper()) if m else end.upper()
    return rua.strip(" ,"), num


def build(setores, log=print) -> pl.DataFrame:
    import geopandas as gpd
    import pandas as pd

    from cityomics.units.setores import CRS

    rows = fetch(log=log)
    recs = []
    for x in rows:
        rua, num = split_endereco(x.get("Endereco"), x.get("Numero"))
        recs.append({"cnpj_base": x["CnpjBase"], "segmento": x["Segmento"], "banco": x["NomeIf"], "logradouro": rua,
                     "numero": num, "cep": x.get("Cep"),
                     "data_inicio": pd.to_datetime(x.get("DataInicio"), format="%d/%m/%Y", errors="coerce")})
    df = geocode.geocode(pl.DataFrame(recs))
    ok = df.filter(pl.col("lat").is_not_null()).to_pandas()
    pts = gpd.GeoDataFrame(ok, geometry=gpd.points_from_xy(ok["lon"], ok["lat"]), crs="EPSG:4674").to_crs(CRS)
    j = gpd.sjoin(pts, setores[["cd_setor", "geometry"]].rename(columns={"cd_setor": "setor"}), how="left", predicate="within")
    ag = pl.from_pandas(j.drop(columns=["geometry", "index_right", "lat", "lon", "cd_setor"]).rename(columns={"setor": "cd_setor"}))
    sem = df.filter(pl.col("lat").is_null()).height
    log(f"BCB: {ag.height:,} geocodificadas ({ag.filter(pl.col('nivel') != 'cep').height:,} por número/logradouro), "
        f"{sem} sem geocódigo, {ag.filter(pl.col('cd_setor').is_null()).height} fora da malha")
    dest = interim_dir() / "bcb"
    dest.mkdir(parents=True, exist_ok=True)
    ag.write_parquet(dest / "agencias_sp.parquet")

    meses = pd.period_range("2015-01", "2026-09", freq="M")
    base = ag.filter(pl.col("cd_setor").is_not_null() & pl.col("data_inicio").is_not_null() & (pl.col("nivel") != "cep"))
    rows = []
    for m in meses:
        fim = m.to_timestamp(how="end").date()
        rows.append(base.filter(pl.col("data_inicio").dt.date() <= fim).group_by("cd_setor")
                    .agg(pl.len().alias("agencias_estoque")).with_columns(pl.lit(str(m)).alias("mes")))
    out = pl.concat(rows).select("cd_setor", "mes", "agencias_estoque").sort("cd_setor", "mes")
    d2 = processed_dir() / "covariaveis"
    d2.mkdir(parents=True, exist_ok=True)
    out.write_parquet(d2 / "setor_bcb_mes.parquet")
    return out
