"""IPVS 2022: Índice Paulista de Vulnerabilidade Social por setor (spec-dados §3.2).

Fonte: Fundação Seade, base cartográfica do IPVS 2022 (setores do Censo 2022 classificados
em seis grupos: 1 baixíssima, 2 muito baixa, 3 baixa, 4 média, 5 alta e 6 muito alta
vulnerabilidade). O índice combina renda, escolaridade e estrutura etária, e foi construído
a partir do mesmo Censo 2022 que alimenta ``censo.py``; por isso é redundante com a renda e
o analfabetismo, e vale como resumo composto e referência clássica em estudos de SP
(desorganização social). Variável estática de 2022.
"""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from cityomics import external
from cityomics.paths import processed_dir

URL = ("https://repositorio.seade.gov.br/dataset/5454f609-5f96-4d86-ac46-a4c58159f395/resource/"
       "aa0725d7-eb55-4926-97bf-d4ead6d05c67/download/ipvs_2022.zip")
CD_MUN_SP = "3550308"


def build(log=print) -> pd.DataFrame:
    path = external.fetch(URL, "seade", filename="ipvs_2022_carto.zip", log=log)
    g = gpd.read_file(f"zip://{path}!IPVS_2022.shp", where=f"CD_MUN = '{CD_MUN_SP}'", read_geometry=False)
    out = g.rename(columns={"CD_SETOR": "cd_setor", "N_IPVS": "ipvs_grupo", "C_IPVS": "ipvs_codigo"})
    out = out[["cd_setor", "ipvs_codigo", "ipvs_grupo"]].copy()
    out["ipvs_codigo"] = pd.to_numeric(out["ipvs_codigo"], errors="coerce")
    # setores sem classificação (população insuficiente ou sem moradores) ficam ausentes
    out.loc[out["ipvs_grupo"].eq("Não classificado"), "ipvs_codigo"] = pd.NA
    out["ipvs_alta"] = out["ipvs_codigo"].ge(5).where(out["ipvs_codigo"].notna())
    dest = processed_dir() / "covariaveis" / "setor_ipvs.parquet"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest, index=False)
    log(f"IPVS: {len(out):,} setores | classificados: {out['ipvs_codigo'].notna().sum():,}")
    return out
