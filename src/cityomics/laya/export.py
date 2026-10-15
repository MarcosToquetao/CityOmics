"""Exporta estados anonimizados para o Colab e lê as probabilidades de volta (D30).

Saem **só** textos de estado com ID anônimo e rótulos 0/1 (``data/processed/laya/``). O mapa
ID → setor e o sal ficam locais (``data/interim/laya/``). Cada estado tem uma chave
``state_id = sha256(texto)[:16]``; as respostas voltam indexadas por essa chave.

Arquivos de saída de ``export``:
- ``train.jsonl``: linhas ``{state, questions, expected}`` para ``laya.train.finetune``;
- ``score_<nome>.jsonl``: linhas ``{state_id, state}`` para inferência (recalibração, avaliação);
- ``numeric_<nome>.parquet``: vetor numérico equivalente ao texto, para o comparador LightGBM (H2);
- ``index_<nome>.parquet``: ``state_id, cd_setor, mes, y`` (fica local).
"""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

import numpy as np
import polars as pl

from cityomics.laya import serialize as S
from cityomics.paths import interim_dir, processed_dir


def salt() -> str:
    f = interim_dir() / "laya" / "anon_salt"
    f.parent.mkdir(parents=True, exist_ok=True)
    if not f.exists():
        f.write_text(secrets.token_hex(16))
    return f.read_text().strip()


def out_dir() -> Path:
    d = processed_dir() / "laya"
    d.mkdir(parents=True, exist_ok=True)
    return d


def state_id(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def build_split(sb: S.StateBuilder, df: pl.DataFrame, scores: dict[str, np.ndarray], **kw) -> tuple[list[str], pl.DataFrame]:
    texts = sb.texts(df, scores, **{k: v for k, v in kw.items() if k in ("history", "names")})
    num = sb.compressed_numeric(df, scores, history=kw.get("history", True))
    return texts, num


def export(nome: str, sb: S.StateBuilder, df: pl.DataFrame, scores: dict[str, np.ndarray], train: bool = False,
           max_rows: int | None = None, seed: int = 0, **kw) -> dict:
    """Escreve os arquivos de um conjunto (``train`` gera ``train.jsonl`` em vez de ``score_*.jsonl``)."""
    if max_rows and df.height > max_rows:
        idx = np.sort(np.random.default_rng(seed).choice(df.height, max_rows, replace=False))
        df = df[idx]
        scores = {k: v[idx] for k, v in scores.items()}
    texts, num = build_split(sb, df, scores, **kw)
    ids = [state_id(t) for t in texts]
    od = out_dir()
    y = df["y"].to_numpy()
    if train:
        with (od / f"{nome}.jsonl").open("w") as fh:
            for row in S.rows_for_finetune(texts, y):
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        with (od / f"score_{nome}.jsonl").open("w") as fh:
            for i, t in zip(ids, texts):
                fh.write(json.dumps({"state_id": i, "state": t}, ensure_ascii=False) + "\n")
    num.with_columns(pl.Series("state_id", ids)).write_parquet(od / f"numeric_{nome}.parquet")
    idx_dir = interim_dir() / "laya"
    pl.DataFrame({"state_id": ids, "cd_setor": df["cd_setor"], "mes": df["mes"], "y": y}).write_parquet(idx_dir / f"index_{nome}.parquet")
    return {"n": len(ids), "mean_words": float(np.mean([len(t.split()) for t in texts]))}
