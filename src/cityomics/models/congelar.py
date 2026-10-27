"""Modelos congelados para o teste de 2026 (F4/F5; prereg §5.2; D24, D25, D52).

Tudo com dados até 2025-12; nada de 2026 é lido. As janelas são as do desenvolvimento deslocadas
um ano, como prevê ``benchmark_run``:

- **pesos do ensemble:** modelos ajustados em 2023-01..2025-06 preveem 2025-07..2025-12 (fora da
  amostra); os pesos minimizam a deviance de Poisson nesse semestre e o φ do ensemble é ajustado
  nele (no desenvolvimento: 2023-01..2024-06 → 2024-07..2024-12);
- **modelos finais:** cada um dos 14 modelos é reajustado em 2023-01..2025-12, com o φ (NB2) do
  próprio período de ajuste, e gravado. Em 2026 só os lags mudam, mês a mês (regra as-of, D25).
- **Laya (D24):** os pesos ajustados (RLCD) ficam no Drive do autor; aqui entram o recalibrador
  isotônico ajustado em 2025 e o sha256 dos pesos, registrado por ``notebooks/colab/laya_hash_pesos.py``.
- **Comparador do H2:** LightGBM no mesmo estado comprimido e no mesmo treino do Laya, com a
  recalibração isotônica de 2025.
- **Destino (H4):** Markov de família × domínio do tecido, com as transições anuais do IPTU de
  2012 a 2025 (2021 mascarado; D56), suavizado por Laplace.

Saída em ``data/models/frozen/`` (os hashes entram no manifesto do FREEZE) e um manifesto legível
em ``data/models/frozen/MANIFESTO.json``. Uso: ``cityomics models congelar``.
"""

from __future__ import annotations

import json
import subprocess
import time

import joblib
import numpy as np
import polars as pl

from cityomics.ingest.snapshot import sha256
from cityomics.paths import REPO_ROOT, interim_dir, processed_dir

VAL = ("2023-01", "2025-06", "2025-07", "2025-12")
FINAL = ("2023-01", "2025-12")
TABELA = "tabela_celular_2022_2025.parquet"
MARKOV_ALFA = 1.0
LAYA_PESOS = "laya_ft/pesos_sha256.json"   # escrito a partir da saída do caderno do Colab
IDENTIDADES = {"laya_ft": "laya_ft: laya-typed-decisions com fine-tuning RLCD (pesos por sha256) + isotônica de 2025",
               "lightgbm_compressed_state": "lgbm_estado: LightGBM binário no estado comprimido do Laya + isotônica de 2025",
               "markov_fate_baseline": "markov_familia_dominio: transições anuais do IPTU 2012–2025 por família × domínio"}


def frozen_dir():
    from cityomics.freeze import models_dir

    d = models_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def carregar_tabela() -> pl.DataFrame:
    t = pl.read_parquet(processed_dir() / "modelo" / TABELA)
    assert t["mes"].max() <= "2025-12", "a tabela de modelagem contém meses de 2026"
    return t


def _salvar(obj, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if getattr(obj, "nome", None) == "gnn":   # a GNN pode ter sido ajustada na GPU
        g = obj.obj
        g.dev, g.a, g.net = "cpu", g.a.cpu(), g.net.cpu()
    joblib.dump(obj, path, compress=3)


# --- benchmark de crime ------------------------------------------------------------------------

def crime(table: pl.DataFrame | None = None, models=None, log=print) -> dict:
    from cityomics.eval import harness, scores
    from cityomics.models import benchmark_run, ensemble, zoo

    table = carregar_tabela() if table is None else table
    models = models or benchmark_run.MODELS
    ctx = benchmark_run.make_ctx(table)
    d = frozen_dir() / "crime"
    # 1. pesos do ensemble no semestre fora da amostra
    val, phi_val = benchmark_run.predictions(table, VAL, models, ctx, log)
    val.write_parquet(processed_dir() / "modelo" / "pred_congelado_val.parquet")
    mus = np.column_stack([val[f"mu_{m}"].to_numpy() for m in models])
    y = val["y"].to_numpy()
    w = ensemble.fit_weights(y, mus)
    phi_ens = scores.fit_phi(y, mus @ w)
    log("pesos do ensemble: " + ", ".join(f"{m} {x:.2f}" for m, x in zip(models, w) if x > 0.005))
    metr = {m: harness.evaluate(val, val[f"mu_{m}"].to_numpy(), phi_val[m]) for m in models}
    metr["ensemble"] = harness.evaluate(val, mus @ w, phi_ens)
    # 2. modelos finais
    tempos, phis = {}, {}
    for m in models:
        t0 = time.time()
        aj = zoo.fit(m, table, *FINAL, ctx)
        _salvar(aj, d / f"{m}.joblib")
        tempos[m], phis[m] = round(time.time() - t0), float(aj.phi)
        log(f"{m}: congelado ({tempos[m]} s; φ = {aj.phi:.3f})")
    ens = {"componentes": list(models), "pesos": dict(zip(models, map(float, w))), "phi": float(phi_ens),
           "janela_pesos": {"ajuste": VAL[:2], "previsao": VAL[2:]}, "janela_final": FINAL}
    (d / "ensemble.json").write_text(json.dumps(ens, indent=2, ensure_ascii=False))
    return {"ensemble": ens, "phi": phis, "segundos": tempos,
            "validacao_2025s2": {k: {"crps": v["crps"], "pai1": v.get("pai1_mensal", v.get("pai1"))} for k, v in metr.items()}}


def prever(table: pl.DataFrame, pred_ini: str, pred_fim: str, ctx: dict | None = None) -> pl.DataFrame:
    """Previsões dos modelos congelados (μ por modelo e do ensemble) para os meses pedidos.

    Usado depois do congelamento, com a tabela as-of de 2026 (só depois de aberto o cofre)."""
    from cityomics.models import benchmark_run

    d = frozen_dir() / "crime"
    ens = json.loads((d / "ensemble.json").read_text())
    ctx = ctx or benchmark_run.make_ctx(table)
    pred = table.filter((pl.col("mes") >= pred_ini) & (pl.col("mes") <= pred_fim)).sort("mes", "cd_setor")
    out = pred.select("cd_setor", "mes")
    for m in ens["componentes"]:
        out = out.with_columns(pl.Series(f"mu_{m}", joblib.load(d / f"{m}.joblib").predict(pred, table, ctx)))
    mus = np.column_stack([out[f"mu_{m}"].to_numpy() for m in ens["componentes"]])
    return out.with_columns(pl.Series("mu_ensemble", mus @ np.array([ens["pesos"][m] for m in ens["componentes"]])))


# --- Laya e comparador do H2 --------------------------------------------------------------------

def laya(log=print) -> dict:
    from cityomics.laya import evaluate as E

    d = frozen_dir() / "laya_ft"
    pl_dir = processed_dir() / "laya"
    i_tr = pl.read_parquet(interim_dir() / "laya" / "index_train.parquet")
    i_ev = pl.read_parquet(interim_dir() / "laya" / "index_eval.parquet")
    assert i_ev["mes"].max() <= "2025-12" and i_ev["mes"].min() >= "2025-01"
    y25 = (i_ev["y"].to_numpy() >= 0.5).astype("float64")
    ft = i_ev.join(pl.read_csv(pl_dir / "laya_ft_eval.csv"), on="state_id", how="left")
    assert ft["p_ge1"].null_count() == 0
    iso = E.calibrate(ft["p_ge1"].to_numpy(), y25)
    _salvar(iso, d / "recalibrador_isotonico_2025.joblib")
    # comparador do H2: mesmo estado, mesmo treino do Laya, mesma recalibração em 2025
    import lightgbm as lgb

    n_tr = pl.read_parquet(pl_dir / "numeric_train.parquet")
    n_ev = pl.read_parquet(pl_dir / "numeric_eval.parquet")
    feats = [c for c in n_tr.columns if c != "state_id"]
    p = {"objective": "binary", "learning_rate": 0.05, "num_leaves": 31, "min_data_in_leaf": 200, "feature_fraction": 0.8,
         "bagging_fraction": 0.8, "bagging_freq": 1, "lambda_l2": 10, "verbose": -1, "seed": 1}   # = laya.evaluate.lgbm_on_state
    ds = lgb.Dataset(n_tr.select(feats).to_numpy().astype("float32"), (i_tr["y"].to_numpy() >= 0.5).astype(float))
    booster = lgb.train(p, ds, num_boost_round=300)
    e = frozen_dir() / "lgbm_estado"
    e.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(e / "lgbm_estado.txt"))
    (e / "features.json").write_text(json.dumps(feats))
    iso_e = E.calibrate(booster.predict(n_ev.select(feats).to_numpy().astype("float32")), y25)
    _salvar(iso_e, e / "recalibrador_isotonico_2025.joblib")
    pesos = d / "pesos_sha256.json"
    log(f"Laya: recalibrador de 2025 gravado; pesos {'registrados' if pesos.exists() else 'AINDA SEM HASH (rodar o caderno do Colab)'}")
    return {"n_recal_2025": int(len(y25)), "pesos_registrados": pesos.exists()}


# --- destino (H4) -------------------------------------------------------------------------------

def markov(log=print) -> dict:
    from cityomics.atlas.genes_lote import atlas_dir

    src = atlas_dir() / "transicoes_familia_dominio.parquet"
    if not src.exists():
        from cityomics.atlas import fate

        fate.run(log=log)
    T = pl.read_parquet(src)
    fams = sorted(set(T["de"].to_list()) | set(T["para"].to_list()))
    doms = sorted(T["dominio"].unique().to_list())
    grade = pl.DataFrame({"dominio": doms}).join(pl.DataFrame({"de": fams}), how="cross").join(pl.DataFrame({"para": fams}), how="cross")
    M = (grade.join(T, on=["dominio", "de", "para"], how="left").with_columns(pl.col("n").fill_null(0))
         .with_columns(((pl.col("n") + MARKOV_ALFA) / (pl.col("n").sum().over("dominio", "de") + MARKOV_ALFA * len(fams))).alias("p")))
    out = frozen_dir() / "destino" / "markov_familia_dominio.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    M.sort("dominio", "de", "para").write_parquet(out)
    log(f"Markov: {len(doms)} domínios × {len(fams)} famílias; {int(T['n'].sum()):,} transições lote-ano")
    return {"dominios": len(doms), "familias": fams, "transicoes": int(T["n"].sum()), "alfa": MARKOV_ALFA}


# --- tudo --------------------------------------------------------------------------------------

def run(partes=("crime", "laya", "markov"), log=print) -> dict:
    rep = {"criado_em": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip(),
           "tabela": {"arquivo": TABELA, "sha256": sha256(processed_dir() / "modelo" / TABELA)},
           "identidades": IDENTIDADES}
    for p in partes:
        rep[p] = {"crime": crime, "laya": laya, "markov": markov}[p](log=log)
    caminho = frozen_dir() / "MANIFESTO.json"
    antigo = json.loads(caminho.read_text()) if caminho.exists() else {}
    caminho.write_text(json.dumps(antigo | rep, indent=2, ensure_ascii=False, default=str))
    return rep


def selecao_proposta() -> dict:
    """``selection.json`` completo proposto (A12 + A13): só o autor o aplica, ao datar as emendas."""
    sel = json.loads((REPO_ROOT / "prereg" / "selection.json").read_text())
    viirs = json.loads((REPO_ROOT / "prereg" / "selection_viirs.json").read_text())["selecao"]
    return sel | viirs | {"laya_ft": "laya_ft", "lightgbm_compressed_state": "lgbm_estado",
                          "markov_fate_baseline": "markov_familia_dominio",
                          "status": "final: CRPS corrigido (A12) e modelos congelados (A13), dados até 2025-12"}
