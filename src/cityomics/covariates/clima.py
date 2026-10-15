"""Clima diário da cidade de São Paulo (spec-dados §3.2).

Fonte: reanálise ERA5 (Copernicus/ECMWF) servida pela API de arquivo do Open-Meteo, para o
ponto central da cidade (-23,55; -46,63), sem chave. É uma série para a cidade inteira,
não por setor: chuva e temperatura variam pouco dentro do município na escala mensal.
O INMET (estação A701 Mirante de Santana) exige cadastro para o histórico; a reanálise é
uma alternativa aberta e contínua. Valores de reanálise suavizam extremos locais.

Variáveis diárias: temperatura máxima, mínima e média, precipitação, vento máximo e
radiação de onda curta. Mensais: médias, total de chuva, dias de chuva forte (≥20 mm),
dias muito quentes (máxima ≥ 30 °C) e dias frios (mínima ≤ 10 °C).
"""

from __future__ import annotations

import json
from datetime import date

import pandas as pd
import requests

from cityomics import external
from cityomics.ingest.snapshot import sha256
from cityomics.paths import processed_dir

URL = "https://archive-api.open-meteo.com/v1/archive"
LAT, LON = -23.55, -46.63
DAILY = ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum",
         "wind_speed_10m_max", "shortwave_radiation_sum"]
RENAME = {"temperature_2m_max": "temp_max", "temperature_2m_min": "temp_min", "temperature_2m_mean": "temp_media",
          "precipitation_sum": "chuva_mm", "wind_speed_10m_max": "vento_max_kmh",
          "shortwave_radiation_sum": "radiacao_mj_m2"}


def fetch(start: str = "2015-01-01", end: str | None = None) -> pd.DataFrame:
    end = end or date.today().isoformat()
    params = {"latitude": LAT, "longitude": LON, "start_date": start, "end_date": end,
              "daily": ",".join(DAILY), "timezone": "America/Sao_Paulo"}
    r = requests.get(URL, params=params, timeout=180, headers={"User-Agent": "CityOmics research pipeline"})
    r.raise_for_status()
    raw = r.json()
    dest = external.external_dir() / "clima" / "era5_openmeteo_sp.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(raw))
    manifest = external.load_manifest()
    manifest["clima/era5_openmeteo_sp.json"] = {
        "url": f"{URL}?latitude={LAT}&longitude={LON}&start_date={start}&end_date={end}&daily=" + ",".join(DAILY),
        "size": dest.stat().st_size, "sha256": sha256(dest),
        "recorded_at": pd.Timestamp.now("UTC").isoformat(timespec="seconds")}
    external.manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    df = pd.DataFrame(raw["daily"]).rename(columns={"time": "data", **RENAME})
    df["data"] = pd.to_datetime(df["data"])
    return df


def monthly(df: pd.DataFrame) -> pd.DataFrame:
    df = df.assign(mes=df["data"].dt.to_period("M").astype(str))
    g = df.groupby("mes")
    return pd.DataFrame({
        "dias_com_dado": g["temp_media"].count(),
        "temp_media": g["temp_media"].mean(), "temp_max_media": g["temp_max"].mean(),
        "temp_min_media": g["temp_min"].mean(),
        "chuva_total_mm": g["chuva_mm"].sum(min_count=1),
        "dias_chuva": g["chuva_mm"].apply(lambda s: int((s >= 1).sum())),
        "dias_chuva_forte": g["chuva_mm"].apply(lambda s: int((s >= 20).sum())),
        "dias_muito_quentes": g["temp_max"].apply(lambda s: int((s >= 30).sum())),
        "dias_frios": g["temp_min"].apply(lambda s: int((s <= 10).sum())),
        "vento_max_medio_kmh": g["vento_max_kmh"].mean(),
        "radiacao_media_mj_m2": g["radiacao_mj_m2"].mean(),
    }).reset_index()


def build(start: str = "2015-01-01", end: str | None = None) -> dict[str, pd.DataFrame]:
    d = fetch(start, end)
    m = monthly(d)
    dest = processed_dir() / "covariaveis"
    dest.mkdir(parents=True, exist_ok=True)
    d.to_parquet(dest / "clima_dia.parquet", index=False)
    m.to_parquet(dest / "clima_mes.parquet", index=False)
    return {"dia": d, "mes": m}
