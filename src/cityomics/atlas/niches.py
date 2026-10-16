"""Arquitetura do tecido: vizinhança, co-ocorrência, domínios e baselines (spec-atlas §3.3; D59).

- ``nhood_enrichment``: grafo kNN (k = 8) dos ~1,69 milhão de células (lotes + FCU). Conta as arestas
  por par de tipos e compara com um nulo de **permutação restrita**: os rótulos são embaralhados só
  dentro de cada estrato distrito × decil de densidade populacional (D59), o que tira o efeito
  trivial do zoneamento e da densidade. z = (observado − média) / desvio do nulo.
- ``colocation_quotient``: baseline urbano (Leslie & Kronenfeld 2011) com o vizinho mais próximo.
- ``cooccurrence``: razão P(B a até r | A) / P(B) nas metacélulas por quadra (47 mil), para raios de
  100 m a 2 km (versão de cidade do ``squidpy.gr.co_occurrence``).
- ``domains``: composição de cada setor (participação de cada tipo na exposição) suavizada com os
  vizinhos de contiguidade (rainha) e agrupada por k-means; o k sai da silhueta (sem crime, D53).
- ``domain_markers``: covariáveis do setor (painel 2025) enriquecidas em cada domínio (d de Cohen).

Nenhuma etapa usa crime.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.paths import processed_dir


def _codes(tipos: np.ndarray) -> tuple[np.ndarray, list[str]]:
    names, codes = np.unique(tipos, return_inverse=True)
    return codes, list(names)


def knn_edges(x: np.ndarray, y: np.ndarray, k: int = 8) -> tuple[np.ndarray, np.ndarray]:
    from scipy.spatial import cKDTree

    tree = cKDTree(np.column_stack([x, y]))
    _, nb = tree.query(np.column_stack([x, y]), k=k + 1, workers=-1)
    src = np.repeat(np.arange(len(x)), k)
    dst = nb[:, 1:].ravel()
    return src, dst


def _pair_counts(src, dst, lab, K):
    return np.bincount(lab[src] * K + lab[dst], minlength=K * K).reshape(K, K).astype(np.float64)


def nhood_enrichment(cel: pl.DataFrame, strata: np.ndarray, k: int = 8, n_perm: int = 100, seed: int = 0, log=print) -> pl.DataFrame:
    lab, names = _codes(cel["tipo"].to_numpy())
    K = len(names)
    src, dst = knn_edges(cel["x"].to_numpy(), cel["y"].to_numpy(), k=k)
    obs = _pair_counts(src, dst, lab, K)
    obs = obs + obs.T
    rng = np.random.default_rng(seed)
    order = np.argsort(strata, kind="stable")
    st_sorted = strata[order]
    acc = np.zeros((n_perm, K, K))
    for p in range(n_perm):
        key = st_sorted + rng.random(len(order))
        perm = order[np.argsort(key, kind="stable")]
        lp = np.empty_like(lab)
        lp[order] = lab[perm]
        c = _pair_counts(src, dst, lp, K)
        acc[p] = c + c.T
    mu, sd = acc.mean(0), acc.std(0)
    z = (obs - mu) / np.where(sd > 0, sd, np.nan)
    rows = [{"a": names[i], "b": names[j], "observado": obs[i, j], "esperado": mu[i, j], "z": z[i, j]}
            for i in range(K) for j in range(K)]
    log(f"vizinhança: {len(src):,} arestas, {K} tipos, {n_perm} permutações restritas")
    return pl.DataFrame(rows)


def colocation_quotient(cel: pl.DataFrame) -> pl.DataFrame:
    lab, names = _codes(cel["tipo"].to_numpy())
    K = len(names)
    src, dst = knn_edges(cel["x"].to_numpy(), cel["y"].to_numpy(), k=1)
    c = _pair_counts(src, dst, lab, K)
    n = np.bincount(lab, minlength=K).astype(float)
    N = n.sum()
    clq = (c / n[:, None]) / (n[None, :] / (N - 1))
    return pl.DataFrame([{"a": names[i], "b": names[j], "clq": clq[i, j]} for i in range(K) for j in range(K)])


def cooccurrence(q: pl.DataFrame, radii=(100, 250, 500, 1000, 2000)) -> pl.DataFrame:
    from scipy.spatial import cKDTree

    ncols = [c for c in q.columns if c.startswith("n|")]
    names = [c[2:] for c in ncols]
    C = q.select(ncols).to_numpy().astype(float)
    C = C / np.clip(C.sum(1, keepdims=True), 1, None)
    xy = q.select("x", "y").to_numpy()
    ok = ~np.isnan(xy).any(1)
    C, xy = C[ok], xy[ok]
    tree = cKDTree(xy)
    pb = C.mean(0)
    rows = []
    for r in radii:
        sp = tree.sparse_distance_matrix(tree, r, output_type="coo_matrix")
        m = sp.row != sp.col
        i, j = sp.row[m], sp.col[m]
        # P(B no vizinho | A na origem) ponderado pela composição
        num = C[i].T @ C[j]
        den = C[i].sum(0)
        cond = num / np.clip(den[:, None], 1e-12, None)
        ratio = cond / np.clip(pb[None, :], 1e-12, None)
        rows += [{"a": names[a], "b": names[b], "raio_m": r, "razao": float(ratio[a, b])}
                 for a in range(len(names)) for b in range(len(names))]
    return pl.DataFrame(rows)


def queen_neighbors():
    """Vizinhos de contiguidade (rainha) dos setores, em cache."""
    path = atlas_dir() / "setor_vizinhos_rainha.parquet"
    if path.exists():
        return pl.read_parquet(path)
    import geopandas as gpd
    from libpysal.weights import Queen

    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    w = Queen.from_dataframe(g, ids=g["cd_setor"].astype(str).tolist(), use_index=False, silence_warnings=True)
    rows = [(i, j) for i, nb in w.neighbors.items() for j in nb]
    out = pl.DataFrame({"cd_setor": [r[0] for r in rows], "vizinho": [r[1] for r in rows]})
    out.write_parquet(path)
    return out


def domains(setor: pl.DataFrame, ks=range(6, 13), seed: int = 0, log=print) -> tuple[pl.DataFrame, dict]:
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score

    from cityomics.atlas.spots import RUAS

    ecols = [c for c in setor.columns if c.startswith("e|")]
    M = setor.select(ecols + RUAS).to_numpy().astype(float)
    S = M / np.clip(M.sum(1, keepdims=True), 1e-9, None)
    ids = setor["cd_setor"].to_list()
    pos = {s: i for i, s in enumerate(ids)}
    nb = queen_neighbors()
    nb = nb.filter(pl.col("cd_setor").is_in(ids) & pl.col("vizinho").is_in(ids))
    a = np.array([pos[s] for s in nb["cd_setor"]])
    b = np.array([pos[s] for s in nb["vizinho"]])
    nsum = np.zeros_like(S)
    np.add.at(nsum, a, S[b])
    deg = np.bincount(a, minlength=len(ids))[:, None]
    smooth = 0.5 * S + 0.5 * np.divide(nsum, np.clip(deg, 1, None))
    feat = np.sqrt(smooth)  # transformação de Hellinger para composições
    rng = np.random.default_rng(seed)
    sub = rng.choice(len(feat), min(8000, len(feat)), replace=False)
    sil = {}
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(feat)
        sil[k] = float(silhouette_score(feat[sub], km.labels_[sub]))
    kbest = max(sil, key=sil.get)
    km = KMeans(n_clusters=kbest, n_init=20, random_state=seed).fit(feat)
    lab = km.labels_
    names = [c[2:] for c in ecols] + RUAS
    city = smooth.mean(0)
    nomes = {}
    for d in range(kbest):
        enr = smooth[lab == d].mean(0) / np.clip(city, 1e-9, None)
        top = [names[i] for i in np.argsort(-enr)[:2]]
        nomes[d] = " + ".join(t.replace("rua_", "ruas ").replace("_m", "") for t in top)
    out = pl.DataFrame({"cd_setor": ids, "dominio": lab.astype(int)}).with_columns(
        pl.col("dominio").replace_strict(nomes).alias("dominio_nome"))
    log(f"domínios: k = {kbest} pela silhueta ({ {k: round(v, 3) for k, v in sil.items()} })")
    return out, {"k": kbest, "silhueta": sil, "nomes": {int(k): v for k, v in nomes.items()}}


def domain_markers(dom: pl.DataFrame, year: int = REF_YEAR, top: int = 8) -> pl.DataFrame:
    core = json.loads((processed_dir().parents[1] / "prereg" / "core_covariates.json").read_text())["groups"]
    cols = sorted({c for g, cs in core.items() if g != "contexto_temporal" for c in cs})
    path = processed_dir() / "covariaveis" / "painel_setor_mes.parquet"
    have = set(pl.scan_parquet(path).collect_schema().names())
    cols = [c for c in cols if c in have]
    p = (pl.scan_parquet(path).filter(pl.col("mes").cast(pl.String).str.starts_with(str(year)))
         .select(pl.col("cd_setor").cast(pl.String), *cols).group_by("cd_setor")
         .agg([pl.col(c).cast(pl.Float64).mean() for c in cols]).collect())
    p = p.join(dom.select("cd_setor", "dominio", "dominio_nome"), on="cd_setor", how="inner")
    X = p.select(cols).to_numpy().astype(float)
    X = np.where(np.isnan(X), np.nanmedian(X, 0), X)
    lab = p["dominio"].to_numpy()
    grp = {g: [c for c in cs if c in cols] for g, cs in core.items()}
    rows = []
    for d in np.unique(lab):
        a, b = X[lab == d], X[lab != d]
        sd = np.sqrt((a.var(0) + b.var(0)) / 2)
        dd = (a.mean(0) - b.mean(0)) / np.where(sd > 0, sd, np.nan)
        for i, c in enumerate(cols):
            g = next((gg for gg, cs in grp.items() if c in cs), "outros")
            rows.append({"dominio": int(d), "covariavel": c, "grupo": g, "cohen_d": float(dd[i]),
                         "media_dominio": float(a[:, i].mean()), "media_resto": float(b[:, i].mean())})
    return pl.DataFrame(rows)


def run(n_perm: int = 100, log=print) -> dict:
    d = atlas_dir()
    cel = pl.read_parquet(d / f"celulas_{REF_YEAR}.parquet").filter(pl.col("x").is_not_null())
    setor = pl.read_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    dens = setor.select("cd_setor", (pl.col("pop_2022") / pl.col("area_km2").clip(1e-4)).alias("dens"))
    dens = dens.with_columns(pl.col("dens").qcut(10, labels=[str(i) for i in range(10)], allow_duplicates=True).cast(pl.String).alias("decil"))
    cel = cel.join(dens.select("cd_setor", "decil"), on="cd_setor", how="left").with_columns(pl.col("decil").fill_null("0"))
    strata = np.unique((cel["cd_dist"].cast(pl.String).fill_null("NA") + "|" + cel["decil"]).to_numpy(), return_inverse=True)[1]
    ne = nhood_enrichment(cel, strata, n_perm=n_perm, log=log)
    ne.write_parquet(d / "nhood_enrichment_2025.parquet")
    colocation_quotient(cel).write_parquet(d / "colocation_quotient_2025.parquet")
    q = pl.read_parquet(d / f"quadra_metacelulas_{REF_YEAR}.parquet")
    cooccurrence(q).write_parquet(d / "coocorrencia_metacelulas_2025.parquet")
    dom, info = domains(setor, log=log)
    dom.write_parquet(d / f"setor_dominio_{REF_YEAR}.parquet")
    domain_markers(dom).write_parquet(d / f"dominio_marcadores_{REF_YEAR}.parquet")
    (d / f"dominios_{REF_YEAR}.json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
    return info
