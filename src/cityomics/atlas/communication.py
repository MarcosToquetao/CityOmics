"""Comunicação entre tipos: o multiverso exploratório (spec-atlas §3.6; D39, D40, D53, D59).

Cada abordagem responde "quanto o tipo A conversa com o tipo B" de um jeito diferente e devolve
métricas padronizadas para a tabela multiverso:
- p de permutação, com o nulo restrito ao decil de densidade;
- estabilidade por bootstrap de distritos;
- ganho fora da amostra contra um baseline, com CV por distrito.

Tudo que usa crime exclui o cofre espacial (D53).

1. ``lr``: ligante–receptor criminológico (``lr_pairs.json``) entre setores.
   - Força s→s' = L_s · R_s' · exp(−d/ℓ), com ℓ ∈ {250, 500, 1000} m, agregada aos pares de tipos
     pela participação de cada tipo na exposição dos setores (CellChat/COMMOT).
   - "Atividade" no estilo NicheNet: o sinal recebido, calculado com as covariáveis de 2024,
     melhora a previsão do crime de 2025 fora da amostra além do lag espacial do ligante?
2. ``knox``: excitação cruzada entre famílias de tipo em tempo contínuo.
   - Pares de eventos a até 400 m e de 1 a 14 dias, com A antes de B.
   - Esperado sob independência espaço-tempo; razão observado/esperado por par A→B.
3. ``misty``: quanto do crime do setor vem da visão intrínseca (o próprio setor), da justaposta
   (vizinhos de contiguidade) e da para-espacial (kernel de 1 km); LightGBM com CV por distrito.
4. ``ncem``: Poisson com ridge e interações tipo receptor × composição vizinha (≈ SLX).
   A matriz γ_AB é o efeito da vizinhança do tipo B sobre setores do tipo A.
5. ``lee``: L de Lee bivariado entre cada ligante e a taxa de crime (contiguidade rainha).
6. ``od2017``: fluxos da Pesquisa Origem-Destino 2017 contra o modelo gravitacional, se a base
   estiver disponível localmente; senão, fica registrado como não rodado.
7. A ablação do GNN fica registrada como não rodada nesta versão.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.paths import interim_dir, processed_dir

LR_FILE = guard.REPO_ROOT / "src" / "cityomics" / "atlas" / "lr_pairs.json"
SCALES = (250, 500, 1000)


# --- dados comuns -------------------------------------------------------------------------------

def setor_frame(year_cov: int = REF_YEAR - 1) -> tuple[pl.DataFrame, dict]:
    """Setores com centróide, composição (participação na exposição dos lotes), escores L/R e crime."""
    import geopandas as gpd

    lr = json.loads(LR_FILE.read_text())
    d = atlas_dir()
    setor = pl.read_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    c = g.geometry.centroid
    xy = pl.DataFrame({"cd_setor": g["cd_setor"].astype(str).to_numpy(), "x": c.x.to_numpy(), "y": c.y.to_numpy()})
    setor = setor.join(xy, on="cd_setor", how="left")
    covs = sorted({c for blk in ("ligantes", "receptores") for v in lr[blk].values() for c in v["covariaveis"]})
    path = processed_dir() / "covariaveis" / "painel_setor_mes.parquet"
    have = set(pl.scan_parquet(path).collect_schema().names())
    covs = [c for c in covs if c in have]
    p = (pl.scan_parquet(path).filter(pl.col("mes").cast(pl.String).str.starts_with(str(year_cov)))
         .select(pl.col("cd_setor").cast(pl.String), *covs).group_by("cd_setor")
         .agg([pl.col(c).cast(pl.Float64).mean() for c in covs]).collect())
    setor = setor.join(p, on="cd_setor", how="left")
    scores = {}
    for blk in ("ligantes", "receptores"):
        for name, v in lr[blk].items():
            parts = []
            for c, s in v["covariaveis"].items():
                if c not in covs:
                    continue
                x = setor[c].to_numpy().astype(float)
                x = np.where(np.isnan(x), np.nanmedian(x), x)
                if c.endswith("_m"):
                    x = np.exp(-x / 500.0)  # distância → proximidade
                    s = -s
                x = (x - x.mean()) / (x.std() or 1.0)
                parts.append(s * x)
            z = np.mean(parts, axis=0)
            scores[name] = (z - z.min()) / (z.max() - z.min() + 1e-12)  # escore em [0, 1], como uma "expressão"
    setor = setor.with_columns([pl.Series(k, v) for k, v in scores.items()])
    return setor, lr


def type_shares(setor: pl.DataFrame) -> tuple[np.ndarray, list[str]]:
    ecols = [c for c in setor.columns if c.startswith("e|") and c != "e|Sem cadastro"]
    W = setor.select(ecols).to_numpy().astype(float)
    W = W / np.clip(W.sum(1, keepdims=True), 1e-9, None)
    return W, [c[2:] for c in ecols]


def kernel(xy: np.ndarray, ell: float):
    from scipy.sparse import coo_matrix
    from scipy.spatial import cKDTree

    tree = cKDTree(xy)
    sp = tree.sparse_distance_matrix(tree, 3 * ell, output_type="coo_matrix")
    vals = np.exp(-sp.data / ell)
    n = len(xy)
    K = coo_matrix((vals, (sp.row, sp.col)), shape=(n, n)).tocsr()
    K.setdiag(1.0)
    return K


def crime(year: int) -> pl.DataFrame:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet"))
    return t.filter(pl.col("periodo").str.starts_with(str(year))).group_by("cd_setor").agg(pl.col("n_total").sum().alias(f"y{year}"))


def density_deciles(setor: pl.DataFrame) -> np.ndarray:
    dens = (setor["pop_2022"] / setor["area_km2"].clip(1e-4)).to_numpy()
    return np.searchsorted(np.quantile(dens, np.linspace(0, 1, 11)[1:-1]), dens)


def _within_perm(values: np.ndarray, strata: np.ndarray, rng) -> np.ndarray:
    order = np.argsort(strata, kind="stable")
    key = strata[order] + rng.random(len(order))
    perm = order[np.argsort(key, kind="stable")]
    out = np.empty_like(values)
    out[order] = values[perm]
    return out


# --- 1. ligante–receptor ------------------------------------------------------------------------

def lr(setor: pl.DataFrame, lrdb: dict, n_perm: int = 100, n_boot: int = 50, seed: int = 0, log=print) -> dict:
    from scipy.stats import spearmanr

    xy = setor.select("x", "y").to_numpy()
    W, tnames = type_shares(setor)
    strata = density_deciles(setor)
    rng = np.random.default_rng(seed)
    rows, pair_rows = [], []
    for ell in SCALES:
        K = kernel(xy, ell)
        for lig, rec in lrdb["pares"]:
            L = setor[lig].to_numpy()
            R = setor[rec].to_numpy()
            KRW = K.T @ (R[:, None] * W)  # (n, T): sinal que s pode enviar a receptores de cada tipo
            M = W[:, :, None] * KRW[:, None, :]  # (n, A, B)
            P = np.einsum("s,sab->ab", L, M)
            perms = np.stack([np.einsum("s,sab->ab", _within_perm(L, strata, rng), M) for _ in range(n_perm)])
            pval = (1 + (perms >= P[None]).sum(0)) / (n_perm + 1)
            # estabilidade: bootstrap de distritos do ranking dos pares de tipos
            dist = setor["cd_dist"].to_numpy()
            ud = np.unique(dist)
            rhos = []
            for _ in range(n_boot):
                pick = rng.choice(ud, len(ud), replace=True)
                wts = np.zeros(len(dist))
                for dd in pick:
                    wts[dist == dd] += 1
                Pb = np.einsum("s,sab->ab", L * wts, M)
                rhos.append(spearmanr(P.ravel(), Pb.ravel()).statistic)
            for a in range(len(tnames)):
                for b in range(len(tnames)):
                    pair_rows.append({"escala_m": ell, "ligante": lig, "receptor": rec, "emissor": tnames[a],
                                      "receptor_tipo": tnames[b], "forca": float(P[a, b]), "p": float(pval[a, b])})
            rows.append({"escala_m": ell, "ligante": lig, "receptor": rec, "forca_total": float(P.sum()),
                         "estabilidade_rho": float(np.mean(rhos)), "pares_p05": int((pval < 0.05).sum())})
        log(f"L–R ℓ={ell} m: {len(lrdb['pares'])} pares calculados")
    return {"pares": pl.DataFrame(rows), "tipos": pl.DataFrame(pair_rows)}


def nichenet_activity(setor: pl.DataFrame, lrdb: dict, ell: float = 500, folds: int = 5, log=print) -> pl.DataFrame:
    """Sinal recebido (covariáveis de 2024) prevê o crime de 2025 além do lag do ligante? CV por distrito."""
    from sklearn.linear_model import PoissonRegressor
    from sklearn.model_selection import GroupKFold

    s = setor.join(crime(REF_YEAR), on="cd_setor", how="left").join(crime(REF_YEAR - 1), on="cd_setor", how="left").fill_null(0)
    keep = guard.explore_mask(s["cd_dist"].to_numpy())
    s = s.filter(pl.Series(keep))
    xy = s.select("x", "y").to_numpy()
    K = kernel(xy, ell)
    y = s[f"y{REF_YEAR}"].to_numpy().astype(float)
    base = np.log1p(s[f"y{REF_YEAR - 1}"].to_numpy().astype(float))
    groups = s["cd_dist"].to_numpy()
    rows = []
    for lig, rec in lrdb["pares"]:
        L, R = s[lig].to_numpy(), s[rec].to_numpy()
        lag = K @ L
        rcv = R * lag
        X0 = np.column_stack([base, lag])
        X1 = np.column_stack([base, lag, rcv])
        dev0 = dev1 = 0.0
        for tr, te in GroupKFold(folds).split(X0, y, groups):
            for X, acc in ((X0, 0), (X1, 1)):
                mu_x, sd_x = X[tr].mean(0), X[tr].std(0) + 1e-9
                m = PoissonRegressor(alpha=1e-4, max_iter=500).fit((X[tr] - mu_x) / sd_x, y[tr])
                mu = np.clip(m.predict((X[te] - mu_x) / sd_x), 1e-9, None)
                d = 2 * np.sum(np.where(y[te] > 0, y[te] * np.log(np.clip(y[te], 1e-12, None) / mu), 0) - (y[te] - mu))
                if acc == 0:
                    dev0 += d
                else:
                    dev1 += d
        rows.append({"ligante": lig, "receptor": rec, "escala_m": ell, "deviance_lag": dev0, "deviance_lr": dev1,
                     "ganho_pct": float(100 * (dev0 - dev1) / dev0)})
    log("atividade L–R (NicheNet): ganho fora da amostra calculado")
    return pl.DataFrame(rows)


# --- 2. Knox entre famílias ---------------------------------------------------------------------

def knox(r_m: float = 400.0, t_days: int = 14, years=(2022, 2023, 2024, 2025), grid_m: float = 100.0, log=print) -> pl.DataFrame:
    from scipy.signal import fftconvolve
    from scipy.spatial import cKDTree

    import geopandas as gpd

    from cityomics.units.setores import CRS

    ev = (pl.scan_parquet(guard.pre2026(interim_dir() / "eventos_celular_atribuidos.parquet"))
          .filter(pl.col("coord_valida") & pl.col("data_fato").dt.year().is_in(list(years)))
          .select("latitude", "longitude", "data_fato", "cd_dist").collect())
    ev = ev.filter(pl.Series(guard.explore_mask(ev["cd_dist"].to_numpy())) & pl.col("data_fato").is_not_null())
    pts = gpd.GeoSeries(gpd.points_from_xy(ev["longitude"], ev["latitude"]), crs="EPSG:4326").to_crs(CRS)
    xy = np.column_stack([pts.x.to_numpy(), pts.y.to_numpy()])
    day = (ev["data_fato"].cast(pl.Date).cast(pl.Int32)).to_numpy()
    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet").filter(pl.col("x").is_not_null())
    tree = cKDTree(cel.select("x", "y").to_numpy())
    _, nn = tree.query(xy, k=1, workers=-1)
    fams, lab = np.unique(cel["familia"].to_numpy()[nn], return_inverse=True)
    F = len(fams)
    # observado: pares a até r e 1 ≤ Δt ≤ T dias (A antes de B), em blocos de tempo
    order = np.argsort(day)
    xy, day, lab = xy[order], day[order], lab[order]
    obs = np.zeros((F, F))
    starts = np.arange(day.min(), day.max() + 1, t_days)
    for s0 in starts:
        i0, i1 = np.searchsorted(day, [s0, s0 + 2 * t_days + 1])
        if i1 - i0 < 2:
            continue
        sub = slice(i0, i1)
        pairs = cKDTree(xy[sub]).query_pairs(r_m, output_type="ndarray")
        if len(pairs) == 0:
            continue
        a, b = pairs[:, 0] + i0, pairs[:, 1] + i0
        dt = day[b] - day[a]
        swap = dt < 0
        a2 = np.where(swap, b, a)
        b2 = np.where(swap, a, b)
        dt = np.abs(dt)
        ok = (dt >= 1) & (dt <= t_days) & (day[a2] >= s0) & (day[a2] < s0 + t_days)
        np.add.at(obs, (lab[a2[ok]], lab[b2[ok]]), 1)
    # esperado: pares próximos no espaço (grade + disco) × probabilidade de 1 ≤ Δt ≤ T sob independência
    gx = ((xy[:, 0] - xy[:, 0].min()) // grid_m).astype(int)
    gy = ((xy[:, 1] - xy[:, 1].min()) // grid_m).astype(int)
    rr = int(np.ceil(r_m / grid_m))
    yy, xx = np.mgrid[-rr:rr + 1, -rr:rr + 1]
    disk = ((xx ** 2 + yy ** 2) * grid_m ** 2 <= r_m ** 2).astype(float)
    grids = []
    for f in range(F):
        g = np.zeros((gy.max() + 1, gx.max() + 1))
        np.add.at(g, (gy[lab == f], gx[lab == f]), 1)
        grids.append(g)
    conv = [fftconvolve(g, disk, mode="same") for g in grids]
    dmin = day.min()
    tl = day.max() - dmin + 1
    daily = np.zeros((F, tl))
    for f in range(F):
        daily[f] = np.bincount(day[lab == f] - dmin, minlength=tl)
    exp = np.zeros((F, F))
    for A in range(F):
        for B in range(F):
            S = float((grids[A] * conv[B]).sum() - (grids[A].sum() if A == B else 0.0))
            cB = np.concatenate([[0], np.cumsum(daily[B])])
            idx = np.arange(tl)
            nb_after = cB[np.clip(idx + t_days + 1, 0, tl)] - cB[np.clip(idx + 1, 0, tl)]
            pt = float((daily[A] * nb_after).sum()) / max(daily[A].sum() * daily[B].sum() - (daily[A].sum() if A == B else 0), 1)
            exp[A, B] = S * pt
    from scipy.stats import poisson

    rows = [{"a": fams[A], "b": fams[B], "observado": float(obs[A, B]), "esperado": float(exp[A, B]),
             "razao": float(obs[A, B] / exp[A, B]) if exp[A, B] > 0 else np.nan,
             "p": float(poisson.sf(obs[A, B] - 1, exp[A, B])) if exp[A, B] > 0 else np.nan}
            for A in range(F) for B in range(F)]
    log(f"Knox: {len(day):,} eventos fora do cofre ({years[0]}–{years[-1]}); {int(obs.sum()):,} pares próximos no espaço-tempo")
    return pl.DataFrame(rows)


# --- 3. MISTy ------------------------------------------------------------------------------------

def misty(setor: pl.DataFrame, folds: int = 5, log=print) -> pl.DataFrame:
    import lightgbm as lgb
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import GroupKFold

    from cityomics.atlas.niches import queen_neighbors

    s = setor.join(crime(REF_YEAR), on="cd_setor", how="left").fill_null(0)
    keep = guard.explore_mask(s["cd_dist"].to_numpy())
    W, _ = type_shares(s)
    lrdb = json.loads(LR_FILE.read_text())
    sc = [k for blk in ("ligantes", "receptores") for k in lrdb[blk]]
    intr = np.column_stack([W, s.select(sc).to_numpy()])
    ids = s["cd_setor"].to_list()
    pos = {v: i for i, v in enumerate(ids)}
    nb = queen_neighbors().filter(pl.col("cd_setor").is_in(ids) & pl.col("vizinho").is_in(ids))
    a = np.array([pos[v] for v in nb["cd_setor"]])
    b = np.array([pos[v] for v in nb["vizinho"]])
    juxta = np.zeros_like(intr)
    np.add.at(juxta, a, intr[b])
    juxta /= np.clip(np.bincount(a, minlength=len(ids))[:, None], 1, None)
    K = kernel(s.select("x", "y").to_numpy(), 1000.0)
    K.setdiag(0.0)
    para = (K @ intr) / np.clip(np.asarray(K.sum(1)), 1e-9, None)
    area = s["area_km2"].to_numpy().clip(1e-3)
    y = np.log1p(s[f"y{REF_YEAR}"].to_numpy() / area)
    views = {"intrinseca": intr, "justaposta": juxta, "para_espacial": para}
    X = {k: v[keep] for k, v in views.items()}
    y, groups = y[keep], s["cd_dist"].to_numpy()[keep]
    oof = {k: np.zeros(len(y)) for k in X}
    for tr, te in GroupKFold(folds).split(y, y, groups):
        for k, M in X.items():
            m = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, verbose=-1).fit(M[tr], y[tr])
            oof[k][te] = m.predict(M[te])
    r2 = lambda p: 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)  # noqa: E731
    stack = np.column_stack([oof[k] for k in X])
    lr_ = LinearRegression(positive=True).fit(stack, y)
    contrib = lr_.coef_ * stack.std(0)
    rows = [{"visao": k, "r2_sozinha": float(r2(oof[k])), "contribuicao": float(contrib[i] / contrib.sum())} for i, k in enumerate(X)]
    rows.append({"visao": "combinada", "r2_sozinha": float(r2(lr_.predict(stack))), "contribuicao": 1.0})
    log(f"MISTy: R² intrínseca {rows[0]['r2_sozinha']:.2f}, combinada {rows[-1]['r2_sozinha']:.2f}")
    return pl.DataFrame(rows)


# --- 4. NCEM / SLX -------------------------------------------------------------------------------

def ncem(setor: pl.DataFrame, alpha: float = 1.0, folds: int = 5, log=print) -> dict:
    from sklearn.linear_model import PoissonRegressor
    from sklearn.model_selection import GroupKFold

    from cityomics.atlas.niches import queen_neighbors

    s = setor.join(crime(REF_YEAR), on="cd_setor", how="left").fill_null(0)
    keep = guard.explore_mask(s["cd_dist"].to_numpy())
    W, tn = type_shares(s)
    ids = s["cd_setor"].to_list()
    pos = {v: i for i, v in enumerate(ids)}
    nb = queen_neighbors().filter(pl.col("cd_setor").is_in(ids) & pl.col("vizinho").is_in(ids))
    a = np.array([pos[v] for v in nb["cd_setor"]])
    b = np.array([pos[v] for v in nb["vizinho"]])
    Nb = np.zeros_like(W)
    np.add.at(Nb, a, W[b])
    Nb /= np.clip(np.bincount(a, minlength=len(ids))[:, None], 1, None)
    T = W.shape[1]
    inter = (W[:, :, None] * Nb[:, None, :]).reshape(len(ids), T * T)
    expo = np.log(np.clip(s["area_km2"].to_numpy(), 1e-3, None))
    y = s[f"y{REF_YEAR}"].to_numpy().astype(float)
    X0 = np.column_stack([W, Nb, expo])
    X1 = np.column_stack([X0, inter])
    X0, X1, y, groups = X0[keep], X1[keep], y[keep], s["cd_dist"].to_numpy()[keep]
    dev = {0: 0.0, 1: 0.0}
    for tr, te in GroupKFold(folds).split(X0, y, groups):
        for k, X in ((0, X0), (1, X1)):
            mu_x, sd_x = X[tr].mean(0), X[tr].std(0) + 1e-9
            m = PoissonRegressor(alpha=alpha * 1e-3, max_iter=1000).fit((X[tr] - mu_x) / sd_x, y[tr])
            mu = np.clip(m.predict((X[te] - mu_x) / sd_x), 1e-9, None)
            dev[k] += 2 * np.sum(np.where(y[te] > 0, y[te] * np.log(np.clip(y[te], 1e-12, None) / mu), 0) - (y[te] - mu))
    mu_x, sd_x = X1.mean(0), X1.std(0) + 1e-9
    m = PoissonRegressor(alpha=alpha * 1e-3, max_iter=1000).fit((X1 - mu_x) / sd_x, y)
    gamma = (m.coef_[-T * T:] / sd_x[-T * T:]).reshape(T, T)
    rows = [{"receptor_tipo": tn[i], "vizinho_tipo": tn[j], "gamma": float(gamma[i, j])} for i in range(T) for j in range(T)]
    gain = float(100 * (dev[0] - dev[1]) / dev[0])
    log(f"NCEM/SLX: ganho fora da amostra das interações = {gain:.2f}% da deviance")
    return {"gamma": pl.DataFrame(rows), "ganho_pct": gain}


# --- 5. Lee's L ---------------------------------------------------------------------------------

def lee(setor: pl.DataFrame, n_perm: int = 99, log=print) -> pl.DataFrame:
    from esda.lee import Spatial_Pearson
    from libpysal.weights import W as PW

    from cityomics.atlas.niches import queen_neighbors

    s = setor.join(crime(REF_YEAR), on="cd_setor", how="left").fill_null(0)
    s = s.filter(pl.Series(guard.explore_mask(s["cd_dist"].to_numpy())))
    ids = s["cd_setor"].to_list()
    idset = set(ids)
    nb = queen_neighbors().filter(pl.col("cd_setor").is_in(ids) & pl.col("vizinho").is_in(ids))
    neigh = {i: [] for i in ids}
    for a, b in zip(nb["cd_setor"], nb["vizinho"]):
        if a in idset and b in idset:
            neigh[a].append(b)
    w = PW(neigh, silence_warnings=True)
    w.transform = "r"
    order = [w.id_order.index(i) for i in ids] if False else None
    yv = np.log1p(s[f"y{REF_YEAR}"].to_numpy() / s["area_km2"].to_numpy().clip(1e-3))
    pos = {v: i for i, v in enumerate(ids)}
    idx = np.array([pos[i] for i in w.id_order])
    lrdb = json.loads(LR_FILE.read_text())
    rows = []
    for lig in lrdb["ligantes"]:
        x = s[lig].to_numpy()[idx]
        sp = Spatial_Pearson(connectivity=w.sparse, permutations=n_perm).fit(x.reshape(-1, 1), yv[idx].reshape(-1, 1))
        rows.append({"ligante": lig, "L_xy": float(sp.association_[0, 1]), "p": float(sp.significance_[0, 1])})
    del order
    log("Lee's L calculado para os ligantes")
    return pl.DataFrame(rows)


# --- execução e tabela multiverso ---------------------------------------------------------------

# a OD 2017 foi baixada em 2026-10-19 para a população presente (P5, presenca.py); os fluxos contra o
# modelo gravitacional continuam exploratórios na narrativa B (comunicação no Extended Data, D63)
OD_STATUS = "não rodado: OD 2017 usada só para a população presente (P5); fluxos × gravitacional pendentes"


def run(log=print) -> pl.DataFrame:
    d = atlas_dir() / "comunicacao"
    d.mkdir(parents=True, exist_ok=True)
    setor, lrdb = setor_frame()
    multi = []
    res = lr(setor, lrdb, log=log)
    res["pares"].write_parquet(d / "lr_pares.parquet")
    res["tipos"].write_parquet(d / "lr_tipos.parquet")
    act = nichenet_activity(setor, lrdb, log=log)
    act.write_parquet(d / "lr_atividade.parquet")
    best = act.sort("ganho_pct", descending=True).row(0, named=True)
    p500 = res["pares"].filter(pl.col("escala_m") == 500)
    multi.append({"abordagem": "ligante–receptor (COMMOT + NicheNet)", "escala": "setor, ℓ = 250–1000 m",
                  "estatistica": f"melhor par {best['ligante']}→{best['receptor']}",
                  "ganho_fora_amostra_pct": best["ganho_pct"], "estabilidade": float(p500["estabilidade_rho"].mean()),
                  "pares_tipo_significativos": int(res["tipos"].filter((pl.col("escala_m") == 500) & (pl.col("p") < 0.05)).height),
                  "usa_crime": True, "status": "rodado"})
    kx = knox(log=log)
    kx.write_parquet(d / "knox_familias.parquet")
    multi.append({"abordagem": "excitação cruzada (Knox, consistente com Hawkes)", "escala": "evento, 400 m × 14 dias",
                  "estatistica": f"razão média {float(kx['razao'].mean()):.2f}; máx {float(kx['razao'].max()):.2f}",
                  "ganho_fora_amostra_pct": None, "estabilidade": None,
                  "pares_tipo_significativos": int(kx.filter(pl.col("p") < 0.05 / kx.height).height),
                  "usa_crime": True, "status": "rodado"})
    ms = misty(setor, log=log)
    ms.write_parquet(d / "misty.parquet")
    multi.append({"abordagem": "MISTy (visões intrínseca/justaposta/para-espacial)", "escala": "setor",
                  "estatistica": "; ".join(f"{r['visao']} {r['contribuicao']:.2f}" for r in ms.iter_rows(named=True) if r["visao"] != "combinada"),
                  "ganho_fora_amostra_pct": None, "estabilidade": None, "pares_tipo_significativos": None,
                  "usa_crime": True, "status": "rodado"})
    nc = ncem(setor, log=log)
    nc["gamma"].write_parquet(d / "ncem_gamma.parquet")
    multi.append({"abordagem": "NCEM / SLX (tipo receptor × vizinhança)", "escala": "setor (contiguidade)",
                  "estatistica": f"|γ| máx {float(nc['gamma']['gamma'].abs().max()):.2f}",
                  "ganho_fora_amostra_pct": nc["ganho_pct"], "estabilidade": None, "pares_tipo_significativos": None,
                  "usa_crime": True, "status": "rodado"})
    le = lee(setor, log=log)
    le.write_parquet(d / "lee.parquet")
    multi.append({"abordagem": "Lee's L bivariado (ligante × crime)", "escala": "setor (contiguidade)",
                  "estatistica": "; ".join(f"{r['ligante']} {r['L_xy']:.2f}" for r in le.iter_rows(named=True)),
                  "ganho_fora_amostra_pct": None, "estabilidade": None, "pares_tipo_significativos": int((le["p"] < 0.05).sum()),
                  "usa_crime": True, "status": "rodado"})
    multi.append({"abordagem": "fluxos OD 2017 × gravitacional", "escala": "zona OD", "estatistica": None,
                  "ganho_fora_amostra_pct": None, "estabilidade": None, "pares_tipo_significativos": None,
                  "usa_crime": False, "status": OD_STATUS})
    multi.append({"abordagem": "ablação de arestas do GNN", "escala": "setor", "estatistica": None,
                  "ganho_fora_amostra_pct": None, "estabilidade": None, "pares_tipo_significativos": None,
                  "usa_crime": True, "status": "não rodado nesta versão"})
    out = pl.DataFrame(multi, infer_schema_length=None)
    out.write_parquet(d / "multiverso.parquet")
    return out
