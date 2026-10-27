"""Destino celular reduzido: a estabilidade do tecido (spec-atlas §3.5 emendado; D42, D56).

Só transições **anuais do cadastro (IPTU)**, de 2012 a 2025. Os pares de anos com 2021 ficam fora,
porque a cobertura do IPTU cai ~25 mil lotes naquele ano. O CNPJ não entra: o snapshot só tem a
situação final e o endereço atual (D56).

1. Um classificador (LightGBM multiclasse sobre os genes do IPTU) aprende, em 2025, a família de
   tipo de cada lote a partir só do IPTU. A acurácia fora da amostra fica registrada.
2. O classificador é aplicado aos lotes de cada ano; as famílias formam a matriz de transição
   anual.
3. A renovação de cada setor é a fração média anual de lotes que mudam de família.
4. Ligação com o "quando": correlação entre a renovação e a variabilidade do crime dentro do setor
   em 2022–2025 (desvio dos resíduos mensais em relação à média do setor). Usa crime: só setores
   fora do cofre (D53).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.paths import interim_dir, processed_dir

YEARS = list(range(2012, REF_YEAR + 1))
MASK = {2021}
IPTU_GENES = ["area_terreno", "area_construida", "n_unidades", "pavimentos", "valor_m2_terreno", "valor_m2_construcao",
              "uso_residencial", "uso_comercio", "uso_servicos", "uso_industria", "uso_terreno",
              "padrao_baixo", "padrao_medio", "padrao_alto", "ano_construcao"]
LOGS = {"area_terreno", "area_construida", "n_unidades", "pavimentos", "valor_m2_terreno", "valor_m2_construcao"}


def _matrix(df: pl.DataFrame, med: np.ndarray | None = None) -> np.ndarray:
    X = df.select(IPTU_GENES).to_numpy().astype(float)
    for i, g in enumerate(IPTU_GENES):
        if g in LOGS:
            X[:, i] = np.log1p(np.clip(X[:, i], 0, None))
    if med is None:
        med = np.nanmedian(X, 0)
    idx = np.where(np.isnan(X))
    X[idx] = np.take(med, idx[1])
    return X


def run(log=print) -> dict:
    import lightgbm as lgb
    from sklearn.preprocessing import StandardScaler

    d = atlas_dir()
    tipos = pl.read_parquet(d / f"lote_tipos_{REF_YEAR}.parquet").filter(pl.col("familia") != "sem_cadastro")
    ref = pl.read_parquet(guard.pre2026(interim_dir() / "iptu" / f"iptu_lote_{REF_YEAR}.parquet")).join(
        tipos.select("sql_base", "familia", "cd_setor", "cd_dist"), on="sql_base", how="inner")
    X = _matrix(ref)
    med = np.nanmedian(X, 0)
    sc = StandardScaler().fit(X)
    Z = sc.transform(X)
    yfam = ref["familia"].to_numpy()
    rng = np.random.default_rng(0)
    tr = rng.random(len(Z)) < 0.8
    sub = np.where(tr)[0][rng.choice(tr.sum(), min(300_000, tr.sum()), replace=False)]
    clf = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.1, num_leaves=63, verbose=-1, random_state=0).fit(Z[sub], yfam[sub])
    te = np.where(~tr)[0][:100_000]
    acc = float((clf.predict(Z[te]) == yfam[te]).mean())
    log(f"destino: acurácia do classificador IPTU → família em 2025 = {acc:.3f}")
    fam_by_year = {}
    for yr in YEARS:
        if yr in MASK:
            continue
        df = pl.read_parquet(guard.pre2026(interim_dir() / "iptu" / f"iptu_lote_{yr}.parquet"))
        Zy = sc.transform(_matrix(df, med))
        pred = np.empty(len(Zy), dtype=object)
        for s in range(0, len(Zy), 300_000):
            pred[s:s + 300_000] = clf.predict(Zy[s:s + 300_000])
        fam_by_year[yr] = pl.DataFrame({"sql_base": df["sql_base"].to_numpy(), f"f{yr}": pred.astype(str)})
    yrs = sorted(fam_by_year)
    trans = []
    lot_change = []
    for a, b in zip(yrs[:-1], yrs[1:]):
        if b - a != 1:
            continue
        j = fam_by_year[a].join(fam_by_year[b], on="sql_base", how="inner")
        trans.append(j.group_by(f"f{a}", f"f{b}").len().rename({f"f{a}": "de", f"f{b}": "para"}).with_columns(pl.lit(b).alias("ano")))
        lot_change.append(j.select("sql_base", (pl.col(f"f{a}") != pl.col(f"f{b}")).alias("mudou")).with_columns(pl.lit(b).alias("ano")))
    T = pl.concat(trans).group_by("de", "para").agg(pl.col("len").sum().alias("n"))
    # as mesmas transições por domínio do tecido do setor do lote: base do Markov congelado do H4 (models.congelar)
    dom = tipos.select("sql_base", "cd_setor").join(pl.read_parquet(d / f"setor_dominio_{REF_YEAR}.parquet").select("cd_setor", "dominio"),
                                                     on="cd_setor", how="left").select("sql_base", pl.col("dominio").fill_null(-1))
    td = []
    for a, b in zip(yrs[:-1], yrs[1:]):
        if b - a == 1:
            td.append(fam_by_year[a].join(fam_by_year[b], on="sql_base", how="inner").join(dom, on="sql_base", how="inner")
                      .group_by("dominio", f"f{a}", f"f{b}").len().rename({f"f{a}": "de", f"f{b}": "para"}))
    (pl.concat(td).group_by("dominio", "de", "para").agg(pl.col("len").sum().alias("n"))
     .write_parquet(d / "transicoes_familia_dominio.parquet"))
    T = T.with_columns((pl.col("n") / pl.col("n").sum().over("de")).alias("taxa"))
    ch = pl.concat(lot_change).join(tipos.select("sql_base", "cd_setor", "cd_dist"), on="sql_base", how="inner")
    ren = ch.group_by("cd_setor", "cd_dist").agg(pl.col("mudou").mean().alias("renovacao"), pl.len().alias("n_obs"))
    # variabilidade do crime dentro do setor (2022–2025), só fora do cofre
    cr = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet"))
    cr = cr.filter(pl.Series(guard.explore_mask(cr["cd_dist"].to_numpy())))
    var = (cr.group_by("cd_setor").agg(pl.col("n_total").mean().alias("m"), pl.col("n_total").std().alias("s"))
           .with_columns((pl.col("s") / pl.col("m").sqrt().clip(1e-6)).alias("sobredispersao_intra")))
    rv = ren.join(var, on="cd_setor", how="inner").filter(pl.col("m") > 0.5)
    from scipy.stats import spearmanr

    rho = float(spearmanr(rv["renovacao"], rv["sobredispersao_intra"]).statistic)
    diag = T.filter(pl.col("de") == pl.col("para"))
    rep = {"acuracia_classificador": acc, "anos": yrs, "anos_mascarados": sorted(MASK),
           "permanencia_media": float(diag["taxa"].mean()), "renovacao_mediana_setor": float(ren["renovacao"].median()),
           "spearman_renovacao_vs_variabilidade_crime": rho, "setores_correlacao": int(rv.height)}
    T.write_parquet(d / "transicoes_familia.parquet")
    ren.write_parquet(d / "setor_renovacao.parquet")
    rv.select("cd_setor", "renovacao", "sobredispersao_intra", "m").write_parquet(d / "renovacao_vs_crime.parquet")
    (d / "destino.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"destino: permanência média {rep['permanencia_media']:.3f}; Spearman renovação × variabilidade = {rho:.2f}")
    return rep
