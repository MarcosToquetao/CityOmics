"""Conferência dos microdados contra a tabela mensal oficial da SSP (spec-dados §5).

A tabela oficial conta por mês de registro (``MES/ANO_ESTATISTICA``) e por natureza.
Cada arquivo anual da SSP tem um único ``ANO_ESTATISTICA``, então a comparação é feita
arquivo a arquivo. Só anos fechados e fora do cofre (2022–2025).

Diferenças pequenas são esperadas: no MapaSegurancaSP, homicídio doloso ficou −2,0%
em 2025 porque a tabela oficial inclui casos que no microdado têm outra natureza apurada.
"""

from __future__ import annotations

import re

import pandas as pd
import requests

from cityomics.ingest.schema import norm_text
from cityomics.ingest.sources import SSP_API_MENSAL
from cityomics.paths import raw_dir

NATUREZAS = ["HOMICIDIO DOLOSO", "TENTATIVA DE HOMICIDIO", "LATROCINIO", "LESAO CORPORAL SEGUIDA DE MORTE",
             "LESAO CORPORAL DOLOSA", "ROUBO - OUTROS", "ROUBO DE VEICULO", "ROUBO DE CARGA",
             "FURTO - OUTROS", "FURTO DE VEICULO"]
TOLERANCE_PCT = 2.5


def official(year: int) -> dict[str, int]:
    r = requests.get(SSP_API_MENSAL.format(year=year), timeout=90,
                     headers={"User-Agent": "Mozilla/5.0 (CityOmics research pipeline)"})
    r.raise_for_status()
    rows = r.json()["data"][0]["listaDados"]
    # rótulos oficiais trazem nota de rodapé: "HOMICÍDIO DOLOSO (2)"
    return {re.sub(r"\s*\(\d+\)$", "", norm_text(d["delito"]["delito"])): int(d["total"]) for d in rows}


def ours(year: int) -> dict[str, int]:
    df = pd.read_parquet(raw_dir() / "bo" / f"ssp_{year}.parquet",
                         columns=["natureza_norm", "ano_estatistica"])
    df = df[df["ano_estatistica"] == year]
    return df["natureza_norm"].value_counts().to_dict()


def compare(years=(2022, 2023, 2024, 2025)) -> pd.DataFrame:
    rows = []
    for year in years:
        off, mine = official(year), ours(year)
        for nat in NATUREZAS:
            if nat in off:
                o, m = off[nat], mine.get(nat, 0)
                rows.append({"ano": year, "natureza": nat, "microdado": m, "oficial": o,
                             "dif_pct": round(100 * (m - o) / o, 2) if o else None})
    out = pd.DataFrame(rows)
    out["alerta"] = out["dif_pct"].abs() > TOLERANCE_PCT
    return out
