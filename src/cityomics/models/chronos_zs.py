"""Chronos-Bolt zero-shot (séries temporais fundacionais; spec-benchmark §3.2).

Para cada setor e mês-alvo ``m``, o contexto é a série **as-of** de 12 meses
(``h_int_l12 … h_int_l1``, já corrigida pela cobertura e só com BOs registrados antes de ``m``) e o
horizonte é 1. O modelo preexistente (Amazon Chronos-Bolt) não é ajustado; a média preditiva
(média dos quantis) passa pela mesma calibração dos baselines (``mu = a·x + b``, dispersão NB do
período de ajuste), para que a comparação seja justa.

Roda em GPU local pequena em fp16/fp32; o contexto são agregados por setor, sem microdados.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import torch

MODEL = "amazon/chronos-bolt-small"
CONTEXT_COLS = [f"h_int_l{l}" for l in range(12, 0, -1)]


def load(model: str = MODEL, device: str | None = None):
    from chronos import BaseChronosPipeline

    dev = device or ("cuda" if torch.cuda.is_available() else "cpu")
    return BaseChronosPipeline.from_pretrained(model, device_map=dev, torch_dtype=torch.float32)


def forecast(pipe, df: pl.DataFrame, batch: int = 4096) -> np.ndarray:
    """Média preditiva h=1 por linha de ``df`` (contexto = 12 lags as-of; NaN vira 0 nos primeiros meses)."""
    ctx = np.nan_to_num(df.select(CONTEXT_COLS).to_numpy().astype("float32"), nan=0.0)
    out = np.empty(len(ctx), dtype="float64")
    qs = list(pipe.quantiles) if hasattr(pipe, "quantiles") else None
    for i in range(0, len(ctx), batch):
        x = torch.tensor(ctx[i:i + batch])
        q, mean = pipe.predict_quantiles(x, prediction_length=1, quantile_levels=[0.1, 0.3, 0.5, 0.7, 0.9])
        out[i:i + batch] = mean[:, 0].cpu().numpy()
    return np.clip(out, 0, None)
