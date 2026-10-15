"""Exporta o protocolo de desenvolvimento do Laya (treino 2024-H1, recalibração 2024-H2, avaliação 2025).

Escores de outros métodos fora da amostra:
- 2024-H1: modelos ajustados em 2023 (calculados aqui);
- 2024-H2 e 2025: previsões já gravadas pela rodada ``benchmark_run`` (ajuste até 2024-06 e 2024-12).
A avaliação usa um subconjunto fixo de setores (``frac_setores``) para caber na inferência do Colab;
todos os modelos são comparados no mesmo subconjunto.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.laya import dataset, export
from cityomics.laya import serialize as S
from cityomics.models import benchmark_run as BR, lgbm, zoo
from cityomics.paths import processed_dir

SCORE_MAP = {"hawkes": "Hawkes self-exciting model", "bym2": "BYM2 disease-mapping surface", "kde": "kernel density",
             "maxent": "MaxEnt habitat model"}


def run(table: pl.DataFrame, n_train: int = 60_000, n_recal: int = 60_000, frac_setores: float = 0.25, log=print) -> dict:
    ctx = BR.make_ctx(table)
    sal = export.salt()
    cols = lgbm.feature_sets(table.columns)["nucleo"]
    markers = [c for c in zoo.cov_cols(table.columns)]
    fit = table.filter((pl.col("mes") >= "2023-01") & (pl.col("mes") <= "2024-06"))
    sb = S.StateBuilder(fit, markers, sal)

    # escores fora da amostra
    h1 = dataset.out_of_sample_scores(table, windows=[("2023-01", "2023-12", "2024-01", "2024-06")], models=dataset.SCORE_MODELS, ctx=ctx, log=log)
    val = pl.read_parquet(processed_dir() / "modelo" / "pred_dev_val.parquet")
    ev = pl.read_parquet(processed_dir() / "modelo" / "pred_dev_eval.parquet")
    sc = pl.concat([h1,
                    val.select("cd_setor", "mes", *[pl.col(f"mu_{m}").alias(m) for m in dataset.SCORE_MODELS]),
                    ev.select("cd_setor", "mes", *[pl.col(f"mu_{m}").alias(m) for m in dataset.SCORE_MODELS])])
    t = table.join(sc, on=["cd_setor", "mes"], how="inner").sort("mes", "cd_setor")

    def part(a, b, sample_cols=None):
        d = t.filter((pl.col("mes") >= a) & (pl.col("mes") <= b))
        return d, {SCORE_MAP[m]: d[m].to_numpy() for m in dataset.SCORE_MODELS}

    out = {}
    d, s = part("2024-01", "2024-06")
    out["train"] = export.export("train", sb, d, s, train=True, max_rows=n_train)
    d, s = part("2024-07", "2024-12")
    out["recal"] = export.export("recal", sb, d, s, max_rows=n_recal, seed=1)
    d, s = part("2025-01", "2025-12")
    keep = set(np.random.default_rng(7).choice(d["cd_setor"].unique().to_numpy(), int(d["cd_setor"].n_unique() * frac_setores), replace=False))
    d = d.filter(pl.col("cd_setor").is_in(list(keep)))
    s = {SCORE_MAP[m]: d[m].to_numpy() for m in dataset.SCORE_MODELS}
    out["eval"] = export.export("eval", sb, d, s)
    log(str(out))
    return out
