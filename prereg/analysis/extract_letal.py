"""Extrai contagens de violência letal (capital) por DP x trimestre, 2022–2025, dos xlsx brutos.

Uso exclusivo para a análise de poder do pré-registro. NÃO lê 2026.
Saída: letal_dp_trimestre.parquet (sem NUM_BO, sem endereço).
"""
import sys
import unicodedata
from pathlib import Path

import pandas as pd

RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])

COMPOSTO = {"HOMICIDIO DOLOSO", "TENTATIVA DE HOMICIDIO", "LATROCINIO", "LESAO CORPORAL SEGUIDA DE MORTE"}
ESTRITO = {"HOMICIDIO DOLOSO", "LATROCINIO", "LESAO CORPORAL SEGUIDA DE MORTE"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().replace("–", "-").split())


def pick(cols, *needles, exclude=()):
    for c in cols:
        n = norm(c)
        if all(x in n for x in needles) and not any(e in n for e in exclude):
            return c
    raise KeyError(needles)


frames = []
for ano in (2022, 2023, 2024, 2025):  # 2026 deliberadamente excluído (cofre)
    path = RAW / f"SPDadosCriminais_{ano}.xlsx"
    xl = pd.ExcelFile(path, engine="calamine")
    for sh in xl.sheet_names:
        if not norm(sh).startswith(("JAN", "JUL")):
            continue
        df = xl.parse(sh, dtype=str)
        cols = df.columns
        c_nat = pick(cols, "NATUREZA")
        c_mun = pick(cols, "MUNICIPIO", "CIRCUN")
        c_dp = pick(cols, "DELEGACIA", "CIRCUN")
        c_dat = pick(cols, "DATA_OCORRENCIA")
        c_bo = pick(cols, "NUM_BO")
        c_del = pick(cols, "NOME_DELEGACIA", exclude=("CIRCUN",))
        c_abo = pick(cols, "ANO_BO")
        d = df[[c_nat, c_mun, c_dp, c_dat, c_bo, c_del, c_abo]].copy()
        d.columns = ["nat", "mun", "dp", "data", "bo", "del", "ano_bo"]
        d["nat"] = d["nat"].map(norm)
        d = d[d["mun"].map(norm).eq("S.PAULO") & d["nat"].isin(COMPOSTO)]
        frames.append(d)
    print(ano, sum(len(f) for f in frames), flush=True)

d = pd.concat(frames, ignore_index=True)
d = d.drop_duplicates(["del", "ano_bo", "bo", "nat"])
d["data"] = pd.to_datetime(d["data"], errors="coerce", dayfirst=False)
d = d[d["data"].dt.year.between(2022, 2025)]
d["trimestre"] = d["data"].dt.to_period("Q").astype(str)
d["estrito"] = d["nat"].isin(ESTRITO)
agg = (d.groupby(["dp", "trimestre"])
         .agg(composto=("nat", "size"), estrito=("estrito", "sum"))
         .reset_index())
agg.to_parquet(OUT)
print(agg.groupby(agg["trimestre"].str[:4])[["composto", "estrito"]].sum())
print("DPs:", agg["dp"].nunique())
