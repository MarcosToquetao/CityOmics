"""Melhores preditores de cada desfecho (Fig. 4e): SHAP do LightGBM por grupo teórico (D12).

Mesmo protocolo de desenvolvimento do benchmark: o modelo é ajustado em 2023-01..2024-12 com os
parâmetros de ``models/zoo.py`` e explicado em uma amostra de 2025 com o TreeSHAP nativo do
LightGBM (``pred_contrib``). Dois modelos para o celular:

- ``completo``: histórico de crime + vizinhança + covariáveis (o melhor preditor);
- ``sem_crime``: só covariáveis (a "assinatura do tecido" sem memória de crime, ablação D6).

As importâncias são a média de |SHAP| por variável, agrupadas pelos grupos teóricos pré-registrados
(``prereg/core_covariates.json``), mais "histórico de crime" e as famílias de fonte para as demais.
A letal (distrito × trimestre) é explicada em ``models/letal_run.py``.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.models import lgbm
from cityomics.models.zoo import LGBM_PARAMS
from cityomics.paths import REPO_ROOT, processed_dir

HIST = ("h_", "nb_h_", "nr_w")


def group_of(feature: str, core: dict) -> str:
    if feature.startswith(HIST):
        return "historico_crime"
    for g, cs in core.items():
        if feature in cs:
            return g
        if any(feature == f"{c}_m3" or feature == f"{c}_m6" or feature == f"{c}_m12" for c in cs):
            return g
    fam = feature.split("_")[0]
    return {"cnpj": "outras_atividade", "osm": "outras_atividade", "infra": "outras_atividade", "agencias": "outras_atividade",
            "censo": "outras_social", "censo2022": "outras_social", "ipvs": "outras_social", "pop": "outras_social",
            "sp156": "outras_cpted", "luz": "cpted", "dias": "contexto_temporal", "temp": "contexto_temporal",
            "chuva": "contexto_temporal", "mes": "contexto_temporal", "area": "tamanho"}.get(fam, "outras")


def shap_celular(n_sample: int = 60_000, seed: int = 0, log=print) -> pl.DataFrame:
    t = pl.read_parquet(processed_dir() / "modelo" / "tabela_celular_2022_2025.parquet")
    core = json.loads((REPO_ROOT / "prereg" / "core_covariates.json").read_text())["groups"]
    fit = t.filter((pl.col("mes") >= "2023-01") & (pl.col("mes") <= "2024-12"))
    ev = t.filter(pl.col("mes").str.starts_with("2025"))
    rng = np.random.default_rng(seed)
    ev = ev[rng.choice(ev.height, min(n_sample, ev.height), replace=False)]
    sets = lgbm.feature_sets(t.columns)
    rows = []
    for nome, rounds in (("completo", 350), ("sem_crime", 800)):
        fs = sets[nome]
        m = lgbm.fit(fit, fs, LGBM_PARAMS, rounds=rounds)
        contrib = m.predict(ev.select(fs).to_numpy().astype("float32"), pred_contrib=True)[:, :-1]
        imp = np.abs(contrib).mean(0)
        for f, v in zip(fs, imp):
            rows.append({"modelo": nome, "variavel": f, "grupo": group_of(f, core), "shap_abs_medio": float(v)})
        log(f"SHAP celular ({nome}): {len(fs)} variáveis")
    out = pl.DataFrame(rows).with_columns(
        (pl.col("shap_abs_medio") / pl.col("shap_abs_medio").sum().over("modelo")).alias("fracao"))
    out.write_parquet(atlas_dir() / "shap_celular_2025.parquet")
    return out
