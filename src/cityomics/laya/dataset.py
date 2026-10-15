"""Dataset do Laya: previsões fora da amostra dos outros métodos como entrada do estado (F5).

Os escores de Hawkes, BYM2, KDE e MaxEnt que entram no estado precisam ser **fora da amostra** também
nas linhas de treino do Laya; senão o Laya aprenderia a confiar em escores bons demais. Por isso
cada bloco de linhas recebe escores de modelos ajustados só com meses anteriores ao bloco
(``WINDOWS``). O mesmo esquema serve para 2026 com uma janela a mais (F7, depois do congelamento).

Protocolo de desenvolvimento (tuning): treino do Laya = 2024-H1, recalibração isotônica = 2024-H2,
avaliação = 2025. Protocolo final (D24): treino ≤ 2024, recalibração 2025, teste 2026.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from cityomics.models import zoo

SCORE_MODELS = ("hawkes", "bym2", "kde", "maxent")
DEV_WINDOWS = [("2023-01", "2023-12", "2024-01", "2024-06"),
               ("2023-01", "2024-06", "2024-07", "2024-12"),
               ("2023-01", "2024-12", "2025-01", "2025-12")]


def out_of_sample_scores(table: pl.DataFrame, windows=DEV_WINDOWS, models=SCORE_MODELS, ctx=None, log=print) -> pl.DataFrame:
    """Escores (média prevista) fora da amostra por (cd_setor, mes) para os meses de previsão de cada janela."""
    parts = []
    for fi, ff, pi, pf in windows:
        cols = {}
        pred = None
        for m in models:
            log(f"  {m}: ajuste {fi}..{ff} -> previsão {pi}..{pf}")
            _, mp, _ = zoo.run(m, table, fi, ff, pi, pf, ctx)
            cols[m] = mp
            pred = table.filter((pl.col("mes") >= pi) & (pl.col("mes") <= pf)).sort("mes", "cd_setor").select("cd_setor", "mes")
        parts.append(pred.with_columns([pl.Series(k, v) for k, v in cols.items()]))
    return pl.concat(parts)
