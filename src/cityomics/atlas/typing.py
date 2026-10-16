"""Tipagem dos lotes: os "tipos celulares" da cidade (spec-atlas §3.1; D38, D53, D59).

Pipeline no estilo scanpy, em escala de cidade:

1. Genes do lote (``genes_lote``): log1p nas contagens e áreas, frações como estão; corte nos
   percentis 0,5 e 99,5 e padronização. Lotes sem IPTU ficam como "sem cadastro".
2. PCA (15 componentes) sobre todos os lotes com IPTU.
3. Estabilidade **sem crime** (D53): para cada resolução do Leiden, várias subamostras
   independentes; os rótulos são transferidos para um conjunto comum de avaliação e comparados
   por ARI. A resolução escolhida é a mais estável com 10 a 16 tipos. Nenhuma variável de crime
   entra em nenhuma etapa.
4. Tipagem final: Leiden numa subamostra de referência (estratificada por distrito) e
   transferência de rótulo (kNN no espaço PCA) para os 1,65 milhão de lotes, como um mapeamento
   de referência de atlas celular.
5. Marcadores (Wilcoxon, ``rank_genes_groups``) e nomes automáticos por regras sobre o perfil
   médio de cada tipo; família semântica para a paleta.
6. Baseline k-means no estilo OAC sobre os mesmos genes (ARI contra o Leiden).

Saídas em ``data/processed/atlas/``: ``lote_tipos_2025.parquet``, ``tipos_perfil_2025.parquet``,
``tipos_marcadores_2025.parquet``, ``tipos_umap_2025.parquet``, ``tipagem_2025.json``.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import genes_lote as G
from cityomics.atlas.genes_lote import atlas_dir

N_PCS = 15
RESOLUTIONS = (0.02, 0.04, 0.07, 0.11, 0.16)
N_TYPES = (10, 16)


def gene_names(columns) -> list[str]:
    return G.LOG_GENES + G.FRAC_GENES + G.LIN_GENES + G.cnpj_genes(columns)


def prepare(g: pl.DataFrame) -> tuple[np.ndarray, list[str], np.ndarray, np.ndarray]:
    """Matriz padronizada (lotes com IPTU), nomes dos genes, máscara e matriz transformada sem padronizar."""
    names = gene_names(g.columns)
    mask = g["tem_iptu"].to_numpy()
    X = g.filter(pl.col("tem_iptu")).select(names).to_numpy().astype(np.float64)
    logc = [i for i, n in enumerate(names) if n in G.LOG_GENES or n.startswith("cnpj_")]
    X[:, logc] = np.log1p(np.clip(X[:, logc], 0, None))
    med = np.nanmedian(X, axis=0)
    idx = np.where(np.isnan(X))
    X[idx] = np.take(med, idx[1])
    lo, hi = np.percentile(X, [0.5, 99.5], axis=0)
    Xc = np.clip(X, lo, hi)
    sd = Xc.std(axis=0)
    sd[sd == 0] = 1.0
    Z = ((Xc - Xc.mean(axis=0)) / sd).astype(np.float32)
    return Z, names, mask, Xc.astype(np.float32)


def pca(Z: np.ndarray, n: int = N_PCS, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.decomposition import PCA

    p = PCA(n_components=n, svd_solver="randomized", random_state=seed).fit(Z)
    return p.transform(Z).astype(np.float32), p.explained_variance_ratio_


def leiden(P: np.ndarray, resolution: float, seed: int, n_neighbors: int = 15) -> np.ndarray:
    import anndata as ad
    import scanpy as sc

    a = ad.AnnData(np.zeros((P.shape[0], 1), dtype=np.float32))
    a.obsm["X_pca"] = P
    sc.pp.neighbors(a, n_neighbors=n_neighbors, use_rep="X_pca", random_state=seed)
    sc.tl.leiden(a, resolution=resolution, random_state=seed, flavor="igraph", n_iterations=2, directed=False)
    return a.obs["leiden"].astype(int).to_numpy()


def transfer(P_ref: np.ndarray, lab_ref: np.ndarray, P: np.ndarray, k: int = 15) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.neighbors import KNeighborsClassifier

    clf = KNeighborsClassifier(n_neighbors=k, n_jobs=-1).fit(P_ref, lab_ref)
    out = np.empty(len(P), dtype=int)
    conf = np.empty(len(P), dtype=np.float32)
    for s in range(0, len(P), 200_000):
        pr = clf.predict_proba(P[s:s + 200_000])
        out[s:s + 200_000] = clf.classes_[pr.argmax(1)]
        conf[s:s + 200_000] = pr.max(1)
    return out, conf


def stability(P: np.ndarray, resolutions=RESOLUTIONS, n_rep: int = 8, size: int = 80_000, n_eval: int = 40_000,
              seed: int = 0, log=print) -> dict:
    """ARI médio entre subamostras independentes, por resolução (critério sem crime, D53/D59)."""
    from sklearn.metrics import adjusted_rand_score

    rng = np.random.default_rng(seed)
    ev = rng.choice(len(P), n_eval, replace=False)
    res = {}
    for r in resolutions:
        labs, ks = [], []
        for i in range(n_rep):
            sub = rng.choice(len(P), size, replace=False)
            lab = leiden(P[sub], r, seed=i)
            ks.append(len(np.unique(lab)))
            labs.append(transfer(P[sub], lab, P[ev])[0])
        aris = [adjusted_rand_score(labs[i], labs[j]) for i in range(n_rep) for j in range(i + 1, n_rep)]
        res[r] = {"ari_medio": float(np.mean(aris)), "ari_min": float(np.min(aris)),
                  "n_tipos_mediano": float(np.median(ks)), "n_tipos": ks}
        log(f"Leiden r={r}: ARI {res[r]['ari_medio']:.3f} (mín {res[r]['ari_min']:.3f}); tipos {ks}")
    return res


def choose(res: dict) -> float:
    ok = {r: v for r, v in res.items() if N_TYPES[0] <= v["n_tipos_mediano"] <= N_TYPES[1]}
    pool = ok or res
    if not ok:  # nenhuma resolução no intervalo: a mais próxima do intervalo entre as estáveis
        return min(pool, key=lambda r: (abs(np.clip(pool[r]["n_tipos_mediano"], *N_TYPES) - pool[r]["n_tipos_mediano"]),
                                        -pool[r]["ari_medio"]))
    return max(pool, key=lambda r: pool[r]["ari_medio"])


def stratified_sample(cd_dist: np.ndarray, size: int, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    idx = []
    dists, inv = np.unique(cd_dist, return_inverse=True)
    frac = size / len(cd_dist)
    for d in range(len(dists)):
        ii = np.where(inv == d)[0]
        k = max(1, int(round(len(ii) * frac)))
        idx.append(rng.choice(ii, min(k, len(ii)), replace=False))
    return np.sort(np.concatenate(idx))


# --- nomes e famílias ----------------------------------------------------------------------------

FAMILIAS = ["res_horizontal", "res_vertical_medio", "res_vertical_alto", "comercio", "servicos", "industria",
            "vazio", "favela", "sem_cadastro"]


def _nome(p: dict) -> tuple[str, str, str]:
    """(nome em português, nome em inglês, família) a partir do perfil médio (valores brutos, sem crime).

    Regras em ordem: uso dominante (vago, indústria, serviços); verticalização (pavimentos ≥ 3 ou
    ≥ 4 unidades); comércio de rua por padrão construtivo; uso misto horizontal; lote de esquina;
    residencial horizontal por padrão.
    """
    vertical = p["pavimentos"] >= 3 or p["n_unidades"] >= 4
    if p["uso_terreno"] >= 0.5:
        return "Terreno vago", "Vacant land", "vazio"
    if p["uso_industria"] >= 0.35:
        return "Indústria e galpões", "Industry and warehouses", "industria"
    if p["uso_servicos"] >= 0.35:
        return "Serviços e equipamentos", "Services and facilities", "servicos"
    if vertical:
        if p["uso_comercio"] >= 0.15:
            return "Vertical residencial e misto", "Mid/high-rise, residential and mixed", "res_vertical_medio"
        if p["padrao_alto"] >= 0.4:
            return "Vertical alto padrão", "High-rise, high standard", "res_vertical_alto"
        return "Vertical residencial", "Mid/high-rise residential", "res_vertical_medio"
    if p["uso_comercio"] >= 0.6:
        if p["padrao_baixo"] >= 0.5:
            return "Comércio de rua popular", "Street retail, low standard", "comercio"
        return "Comércio de rua médio", "Street retail, middle standard", "comercio"
    if p["uso_comercio"] >= 0.25:
        if p.get("cnpj_comercio_atacado", 0) >= 0.3:
            return "Casa e comércio atacadista", "Low-rise mixed, wholesale", "comercio"
        return "Misto residencial e comercial", "Mixed residential and commercial", "comercio"
    if p.get("esquina", 0) >= 0.5:
        return "Residencial de esquina", "Corner residential", "res_horizontal"
    if p["padrao_alto"] >= 0.3:
        return "Residencial horizontal alto padrão", "Low-rise residential, high standard", "res_vertical_alto"
    if p["padrao_baixo"] >= 0.5:
        return "Residencial horizontal popular", "Low-rise residential, low standard", "res_horizontal"
    return "Residencial horizontal médio", "Low-rise residential, middle standard", "res_horizontal"


def name_types(raw: np.ndarray, names: list[str], lab: np.ndarray) -> pl.DataFrame:
    """Perfil médio bruto por tipo e nomes únicos (sufixo quando dois tipos caem no mesmo nome)."""
    rows = []
    for k in np.unique(lab):
        m = raw[lab == k]
        prof = {n: float(np.mean(m[:, i])) for i, n in enumerate(names)}
        # contagens e áreas voltam da escala log1p
        for n in names:
            if n in G.LOG_GENES or n.startswith("cnpj_"):
                prof[n] = float(np.expm1(np.mean(m[:, names.index(n)])))
        pt, en, fam = _nome(prof)
        rows.append({"cluster": int(k), "nome": pt, "name_en": en, "familia": fam, "n_lotes": int(len(m))} | prof)
    df = pl.DataFrame(rows).sort("n_lotes", descending=True)
    seen: dict[str, int] = {}
    nomes, ens = [], []
    for pt, en in zip(df["nome"], df["name_en"]):
        seen[pt] = seen.get(pt, 0) + 1
        suf = "" if seen[pt] == 1 else f" {seen[pt]}"
        nomes.append(pt + suf)
        ens.append(en + suf)
    return df.with_columns(pl.Series("nome", nomes), pl.Series("name_en", ens))


def markers(raw: np.ndarray, names: list[str], lab: np.ndarray, n: int = 200_000, seed: int = 0) -> pl.DataFrame:
    import anndata as ad
    import scanpy as sc

    rng = np.random.default_rng(seed)
    sub = rng.choice(len(lab), min(n, len(lab)), replace=False)
    a = ad.AnnData(raw[sub].astype(np.float32))
    a.var_names = names
    a.obs["tipo"] = lab[sub].astype(str)
    sc.tl.rank_genes_groups(a, "tipo", method="wilcoxon", n_genes=len(names))
    r = a.uns["rank_genes_groups"]
    rows = []
    for g in r["names"].dtype.names:
        for i in range(len(names)):
            rows.append({"cluster": int(g), "gene": r["names"][g][i], "score": float(r["scores"][g][i]),
                         "logfc": float(r["logfoldchanges"][g][i]), "rank": i})
    return pl.DataFrame(rows)


def umap_coords(P: np.ndarray, idx: np.ndarray, seed: int = 0) -> np.ndarray:
    import umap

    return umap.UMAP(n_neighbors=15, min_dist=0.3, random_state=seed, n_jobs=1).fit_transform(P[idx]).astype(np.float32)


def run(n_ref: int = 80_000, min_share: float = 0.003, log=print) -> dict:
    from sklearn.cluster import MiniBatchKMeans
    from sklearn.metrics import adjusted_rand_score

    g = pl.read_parquet(atlas_dir() / f"lote_genes_{G.REF_YEAR}.parquet")
    Z, names, mask, raw = prepare(g)
    log(f"tipagem: {mask.sum():,} lotes com IPTU × {len(names)} genes")
    P, evr = pca(Z)
    log(f"PCA: {N_PCS} componentes explicam {evr.sum():.1%}")
    stab = stability(P, log=log)
    r = choose(stab)
    gi = g.filter(pl.col("tem_iptu"))
    ref = stratified_sample(gi["cd_dist"].cast(pl.String).fill_null("NA").to_numpy(), n_ref)
    lab_ref = leiden(P[ref], r, seed=0)
    # tipos minúsculos (< min_share dos lotes de referência) vão para o centróide mais próximo
    ks, cnt = np.unique(lab_ref, return_counts=True)
    small = ks[cnt < min_share * len(lab_ref)]
    if len(small):
        big = ks[cnt >= min_share * len(lab_ref)]
        cen = np.stack([P[ref][lab_ref == k].mean(0) for k in big])
        for k in small:
            m = lab_ref == k
            lab_ref[m] = big[np.argmin(((P[ref][m][:, None, :] - cen[None]) ** 2).sum(-1), axis=1)]
        log(f"tipagem: {len(small)} tipos minúsculos fundidos ao centróide mais próximo")
    _, lab_ref = np.unique(lab_ref, return_inverse=True)
    lab, conf = transfer(P[ref], lab_ref, P)
    lab[ref] = lab_ref
    conf[ref] = 1.0
    perfil = name_types(raw, names, lab)
    mk = markers(raw, names, lab)
    km = MiniBatchKMeans(n_clusters=len(np.unique(lab)), random_state=0, batch_size=50_000, n_init=5).fit(Z)
    ari_km = float(adjusted_rand_score(lab, km.labels_))
    rng = np.random.default_rng(0)
    usub = rng.choice(len(P), 150_000, replace=False)
    um = umap_coords(P, usub)
    nm = dict(zip(perfil["cluster"], perfil["nome"]))
    fam = dict(zip(perfil["cluster"], perfil["familia"]))
    tipos = gi.select("sql_base", "cd_setor", "cd_dist").with_columns(
        pl.Series("cluster", lab), pl.Series("conf", conf),
        pl.Series("tipo", [nm[k] for k in lab]), pl.Series("familia", [fam[k] for k in lab]),
        pl.Series("kmeans", km.labels_.astype(int)))
    sem = g.filter(~pl.col("tem_iptu")).select("sql_base", "cd_setor", "cd_dist").with_columns(
        pl.lit(-1).alias("cluster"), pl.lit(0.0, dtype=pl.Float32).alias("conf"), pl.lit("Sem cadastro").alias("tipo"),
        pl.lit("sem_cadastro").alias("familia"), pl.lit(-1).alias("kmeans"))
    tipos = pl.concat([tipos, sem.with_columns(pl.col("kmeans").cast(tipos["kmeans"].dtype),
                                               pl.col("cluster").cast(tipos["cluster"].dtype))])
    d = atlas_dir()
    tipos.write_parquet(d / f"lote_tipos_{G.REF_YEAR}.parquet")
    perfil.write_parquet(d / f"tipos_perfil_{G.REF_YEAR}.parquet")
    mk.write_parquet(d / f"tipos_marcadores_{G.REF_YEAR}.parquet")
    pl.DataFrame({"sql_base": gi["sql_base"].to_numpy()[usub], "cluster": lab[usub],
                  "umap1": um[:, 0], "umap2": um[:, 1]}).write_parquet(d / f"tipos_umap_{G.REF_YEAR}.parquet")
    rep = {"resolucao": r, "estabilidade": {str(k): v for k, v in stab.items()}, "n_tipos": int(len(np.unique(lab))),
           "genes": names, "pca_variancia": float(evr.sum()), "ari_kmeans_vs_leiden": ari_km,
           "confianca_transferencia_mediana": float(np.median(conf)), "n_ref": int(len(ref)),
           "lotes_tipados": int(mask.sum()), "sem_cadastro": int((~mask).sum())}
    (d / f"tipagem_{G.REF_YEAR}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"tipagem: r={r}, {rep['n_tipos']} tipos; ARI k-means × Leiden = {ari_km:.2f}")
    return rep


def rename(log=print) -> pl.DataFrame:
    """Reaplica as regras de nome sobre os rótulos já gravados (não muda os agrupamentos)."""
    d = atlas_dir()
    g = pl.read_parquet(d / f"lote_genes_{G.REF_YEAR}.parquet")
    Z, names, mask, raw = prepare(g)
    tipos = pl.read_parquet(d / f"lote_tipos_{G.REF_YEAR}.parquet")
    gi = g.filter(pl.col("tem_iptu")).select("sql_base").join(tipos.select("sql_base", "cluster"), on="sql_base", how="left")
    lab = gi["cluster"].to_numpy()
    perfil = name_types(raw, names, lab)
    nm = dict(zip(perfil["cluster"], perfil["nome"]))
    fam = dict(zip(perfil["cluster"], perfil["familia"]))
    tipos = tipos.with_columns(
        pl.when(pl.col("cluster") >= 0).then(pl.col("cluster").replace_strict(nm, default=None)).otherwise(pl.col("tipo")).alias("tipo"),
        pl.when(pl.col("cluster") >= 0).then(pl.col("cluster").replace_strict(fam, default=None)).otherwise(pl.col("familia")).alias("familia"))
    tipos.write_parquet(d / f"lote_tipos_{G.REF_YEAR}.parquet")
    perfil.write_parquet(d / f"tipos_perfil_{G.REF_YEAR}.parquet")
    log("tipos: " + "; ".join(f"{r['nome']} ({r['n_lotes']:,})" for r in perfil.iter_rows(named=True)))
    return perfil


def subcluster_vertical(parent: str = "Misto residencial e comercial", min_floors: float = 4, min_units: float = 8, log=print) -> int:
    """Sub-agrupamento por regra de genes (sem crime) do tipo misto, que absorveu os prédios no Leiden.

    É o refinamento usual de um grupo heterogêneo num atlas celular: os lotes do tipo-pai com
    ≥ ``min_floors`` pavimentos ou ≥ ``min_units`` unidades viram um tipo próprio (renomeado pelas regras).
    """
    d = atlas_dir()
    tipos = pl.read_parquet(d / f"lote_tipos_{G.REF_YEAR}.parquet")
    if "sub_vertical" in tipos.columns:
        return 0
    g = pl.read_parquet(d / f"lote_genes_{G.REF_YEAR}.parquet", columns=["sql_base", "pavimentos", "n_unidades"])
    j = tipos.join(g, on="sql_base", how="left")
    new = int(tipos["cluster"].max()) + 1
    vert = (pl.col("tipo") == parent) & ((pl.col("pavimentos") >= min_floors) | (pl.col("n_unidades") >= min_units))
    j = j.with_columns(pl.when(vert).then(pl.lit(new)).otherwise(pl.col("cluster")).alias("cluster"), vert.alias("sub_vertical"))
    j.drop("pavimentos", "n_unidades").write_parquet(d / f"lote_tipos_{G.REF_YEAR}.parquet")
    n = int(j["sub_vertical"].sum())
    rep = json.loads((d / f"tipagem_{G.REF_YEAR}.json").read_text())
    rep["subagrupamento_vertical"] = {"tipo_pai": parent, "min_pavimentos": min_floors, "min_unidades": min_units, "lotes": n}
    rep["n_tipos"] = int(j.filter(pl.col("cluster") >= 0)["cluster"].n_unique())
    (d / f"tipagem_{G.REF_YEAR}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"subagrupamento vertical: {n:,} lotes de '{parent}' viram um tipo próprio")
    rename(log=log)
    return n
