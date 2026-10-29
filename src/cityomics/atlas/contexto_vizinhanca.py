"""Contexto espacial dos gêmeos de tecido, passo 2: vizinhança (exploratório, fora do artigo).

Parte dos resíduos do passo 1 (``contexto``: ``residuos_setor``, ``residuos_sem_tecido``, ``gemeos``).
O contexto vem da composição de **todos** os setores (a composição não usa crime, D53), mas o crime
continua só nos distritos de exploração. Seis análises:

- **B. Anéis:** composição do 1º e do 2º anel de vizinhos rainha e dos círculos de 250 m a 2 km, mais a
  posição (distância a estações, corredores, favelas, centro). Curva de ganho do R² fora da amostra (CV
  por distrito) ao somar cada anel ao tecido próprio, e quanto o contexto previsto explica da diferença
  entre gêmeos.
- **C. Bordas:** contraste entre o setor e o entorno (Hellinger, entropia, fronteira de domínio, borda
  de favela, contraste de renda e de IPVS), com efeito fixo de distrito e controles do próprio setor.
- **Borda de delegacia:** pares contíguos no mesmo distrito, em delegacias diferentes. Se a diferença
  do resíduo no par acompanha inteira a diferença entre as delegacias medida no interior delas
  (β ≈ 1), há um salto na divisa (registro); se β ≈ 0, a variação é gradual (bairro). O mesmo teste
  nas divisas de distrito dentro da mesma delegacia serve de comparação.
- **Interações entre tipos:** valores SHAP de interação do boosting da composição própria: o que o
  modelo aditivo (uma taxa por classe) não captura.
- **F. Motivos:** agrupamento sem crime do contexto multiescala; se os subcontextos separam o resíduo
  dentro dos domínios e entre gêmeos.
- **G. Contágio contra contexto:** SLX, SAR, SEM e SDM (spreg) no resíduo, e o painel anual: o choque
  dos vizinhos num ano prevê a mudança do setor no ano seguinte?

Saídas locais em ``data/processed/atlas/contexto/`` (``vizinhanca.json`` e tabelas por setor).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl
import scipy.sparse as sp

from cityomics.atlas import contexto as C
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.niches import queen_neighbors
from cityomics.atlas.spots import exposure_matrix
from cityomics.paths import interim_dir, processed_dir

RAIOS = (250, 500, 1000, 2000)
ALVOS = ("quanto", "quanto_dist", "fen_div", "hora_noturna", "tendencia")
SE_LONLAT = (-46.6339, -23.5503)       # Praça da Sé
POSICAO = ("dist_estacao_metro_m", "dist_estacao_trem_m", "dist_terminal_onibus_m", "dist_corredor_onibus_m",
           "dist_favela_m", "dist_cortico_m", "dist_parque_m", "dist_praca_m", "dist_feira_m")
PUREZA_DP = 0.8
N_BOOT = 200


# --- base comum ---------------------------------------------------------------------------------

def norm_linhas(M) -> np.ndarray:
    M = np.asarray(M, dtype=float)
    return M / np.clip(M.sum(axis=1, keepdims=True), 1e-12, None)


def hellinger(P: np.ndarray, Q: np.ndarray) -> np.ndarray:
    return np.sqrt(0.5 * np.sum((np.sqrt(P) - np.sqrt(Q)) ** 2, axis=1))


def demean(z: np.ndarray, g: np.ndarray) -> np.ndarray:
    k = np.unique(g, return_inverse=True)[1]
    if z.ndim == 1:
        return z - (np.bincount(k, weights=z) / np.bincount(k))[k]
    return np.column_stack([demean(z[:, c], g) for c in range(z.shape[1])])


def base(log=print) -> dict:
    """Composição de todos os setores, adjacências e resíduos do passo 1 alinhados."""
    import geopandas as gpd
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    setor = pl.read_parquet(atlas_dir() / f"setor_composicao_{REF_YEAR}.parquet")
    E, names = exposure_matrix(setor)
    E = E / 1000.0
    est = [i for i, n in enumerate(names) if n.startswith("n_")]
    E[:, est] *= 1000.0
    cs = setor["cd_setor"].to_numpy()
    n = len(cs)
    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    c = g.geometry.centroid
    xy_t = pl.DataFrame({"cd_setor": g["cd_setor"].astype(str).to_numpy(), "x": c.x.to_numpy(), "y": c.y.to_numpy()})
    xy = setor.select("cd_setor").join(xy_t, on="cd_setor", how="left").select("x", "y").to_numpy()
    se = np.array(Transformer.from_crs("EPSG:4326", g.crs, always_xy=True).transform(*SE_LONLAT))
    pos = {s: k for k, s in enumerate(cs)}
    viz = queen_neighbors()
    a = np.array([pos[s] for s in viz["cd_setor"].to_list()])
    b = np.array([pos[s] for s in viz["vizinho"].to_list()])
    A1 = sp.csr_matrix((np.ones(len(a)), (a, b)), shape=(n, n))
    A1.data[:] = 1.0
    A2 = (A1 @ A1).tocsr()
    A2.data[:] = 1.0
    A2 = (A2 - A1 - sp.identity(n, format="csr")).tocsr()
    A2.data = (A2.data > 0).astype(float)
    A2.eliminate_zeros()
    tree = cKDTree(xy)
    D = tree.sparse_distance_matrix(tree, max(RAIOS), output_type="coo_matrix")
    off = D.row != D.col
    Br = {r: sp.csr_matrix((np.ones(int((off & (D.data <= r)).sum())), (D.row[off & (D.data <= r)], D.col[off & (D.data <= r)])),
                           shape=(n, n)) for r in RAIOS}
    res = pl.read_parquet(C.out_dir() / "residuos_setor.parquet")
    sem = pl.read_parquet(C.out_dir() / "residuos_sem_tecido.parquet")
    assert (res["cd_setor"] == sem["cd_setor"]).all()
    idx = np.array([pos[s] for s in res["cd_setor"].to_list()])
    pares = pl.read_parquet(C.out_dir() / "gemeos.parquet")
    P = norm_linhas(E)
    Xown = np.column_stack([np.sqrt(P[idx]), np.log(E[idx].sum(axis=1) + 1e-9), C._dec_densidade(res)])
    log(f"base: {n:,} setores de contexto, {len(idx):,} de exploração, {A1.nnz // 2:,} arestas rainha")
    return {"setor": setor, "E": E, "P": P, "names": names, "cs": cs, "xy": xy, "se": se, "A1": A1, "A2": A2, "Br": Br,
            "res": res, "sem": sem, "idx": idx, "pares": pares, "Xown": Xown,
            "el": res["elegivel"].to_numpy(), "dist": res["cd_dist"].to_numpy()}


def composicao_contexto(b: dict, M: sp.csr_matrix) -> np.ndarray:
    """Composição (participação na exposição) do conjunto de vizinhos em M, para todos os setores."""
    return norm_linhas(M @ b["E"])


def lgb_cv(X: np.ndarray, y: np.ndarray, groups: np.ndarray, seed: int = 0, folds: int = 5) -> np.ndarray:
    import lightgbm as lgb
    from sklearn.model_selection import GroupKFold

    oof = np.zeros(len(y))
    for tr, te in GroupKFold(folds).split(X, y, groups):
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.7, random_state=seed, verbose=-1)
        m.fit(X[tr], y[tr])
        oof[te] = m.predict(X[te])
    return oof


def r2(y, p) -> float:
    return float(1 - np.var(y - p) / np.var(y))


def coef_fe(y: np.ndarray, X: np.ndarray, g: np.ndarray, n_boot: int = N_BOOT, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """OLS com efeito fixo de grupo (demean) e IC 95% por bootstrap de grupos."""
    yd, Xd = demean(y, g), demean(X, g)
    beta = np.linalg.lstsq(Xd, yd, rcond=None)[0]
    rng = np.random.default_rng(seed)
    ug, inv = np.unique(g, return_inverse=True)
    rows = [np.where(inv == k)[0] for k in range(len(ug))]
    bs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(ug), len(ug))
        ix = np.concatenate([rows[k] for k in pick])
        gg = np.concatenate([np.full(len(rows[k]), t) for t, k in enumerate(pick)])
        bs.append(np.linalg.lstsq(demean(X[ix], gg), demean(y[ix], gg), rcond=None)[0])
    return beta, np.percentile(np.array(bs), [2.5, 97.5], axis=0)


def _alvo(b: dict, col: str, sem_tecido: bool = False) -> np.ndarray:
    return (b["sem"][f"{col}_sem_tecido"] if sem_tecido else b["res"][col]).to_numpy().astype(float)


# --- B. anéis -----------------------------------------------------------------------------------

def comp_aneis(b: dict) -> dict:
    """Composição do 1º e 2º anel rainha e dos círculos de 250 m a 2 km, para todos os setores."""
    viz = {"r1": composicao_contexto(b, b["A1"]), "r2": composicao_contexto(b, b["A2"])}
    return viz | {f"b{r}": composicao_contexto(b, b["Br"][r]) for r in RAIOS}


def aneis(b: dict, log=print) -> tuple[dict, dict]:
    idx, el, names = b["idx"], b["el"], b["names"]
    viz = comp_aneis(b)
    infra = pl.read_parquet(processed_dir() / "covariaveis" / "setor_infra.parquet")
    inf = b["res"].select("cd_setor").join(infra, on="cd_setor", how="left")
    pos = np.column_stack([np.log1p(inf[c].fill_null(inf[c].median()).to_numpy().astype(float)) for c in POSICAO]
                          + [np.log1p(np.hypot(*(b["xy"][idx] - b["se"]).T))])
    conjuntos = {k: np.sqrt(v[idx]) for k, v in viz.items()} | {"posicao": pos}
    ordem = ["r1", "r2", "b250", "b500", "b1000", "b2000", "posicao"]
    g = b["dist"][el]
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    out, oofs = {}, {}
    for col in ALVOS:
        y = _alvo(b, col)
        X = b["Xown"]
        p_own = np.zeros(len(y))
        p_own[el] = lgb_cv(X[el], y[el], g)
        curva = {"proprio": r2(y[el], p_own[el])}
        for k in ordem:
            X = np.column_stack([X, conjuntos[k]])
            p = np.zeros(len(y))
            p[el] = lgb_cv(X[el], y[el], g)
            curva[f"+{k}"] = r2(y[el], p[el])
        so_pos = np.zeros(len(y))
        so_pos[el] = lgb_cv(np.column_stack([b["Xown"], pos])[el], y[el], g)
        curva["proprio+posicao"] = r2(y[el], so_pos[el])
        ctx = p - p_own
        gem = {}
        for lo, hi in ((0, 1000), (1000, 3000), (3000, 1e9)):
            m = (d >= lo) & (d < hi)
            dy, dc = y[i[m]] - y[j[m]], ctx[i[m]] - ctx[j[m]]
            gem[f"{int(lo)}-{int(hi) if hi < 1e8 else 'inf'}m"] = {
                "r_delta_contexto": float(np.corrcoef(dy, dc)[0, 1]),
                "r_gemeos_antes": C._corr_sim(y - p_own, i[m], j[m]),
                "r_gemeos_depois": C._corr_sim(y - p, i[m], j[m]), "pares": int(m.sum())}
        out[col] = {"curva_r2": curva, "gemeos": gem}
        oofs[col] = {"p_own": p_own, "p_full": p}
        log(f"  anéis {col}: " + ", ".join(f"{k} {v:.3f}" for k, v in curva.items())
            + f"; gêmeos ≤1 km {gem['0-1000m']['r_gemeos_antes']:.2f} → {gem['0-1000m']['r_gemeos_depois']:.2f}")
    out["importancia"] = _importancia(b, conjuntos, ordem, names)
    return out, {"conjuntos": conjuntos, "ordem": ordem, "oof": oofs, "viz": viz}


def _importancia(b: dict, conjuntos: dict, ordem: list[str], names: list[str]) -> dict:
    """Contribuições (SHAP exato do LightGBM) agrupadas por anel e por classe, no modelo completo."""
    import lightgbm as lgb

    el = b["el"]
    blocos = [("proprio", b["Xown"], [f"proprio|{n}" for n in names] + ["proprio|log_tamanho", "proprio|densidade"])]
    blocos += [(k, conjuntos[k], [f"{k}|{n}" for n in names] if k != "posicao" else [f"posicao|{c}" for c in POSICAO] + ["posicao|dist_centro"])
               for k in ordem]
    X = np.column_stack([x for _, x, _ in blocos])
    fn = [f for _, _, fs in blocos for f in fs]
    out = {}
    for col in ("quanto", "quanto_dist", "fen_div", "hora_noturna"):
        y = _alvo(b, col)
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.7, random_state=0, verbose=-1).fit(X[el], y[el])
        S = m.predict(X[el], pred_contrib=True)[:, :-1]
        a = np.abs(S).mean(axis=0)
        grupo = {}
        for f, v in zip(fn, a):
            grupo[f.split("|")[0]] = grupo.get(f.split("|")[0], 0.0) + float(v)
        tot = sum(grupo.values())
        top = np.argsort(-a)[:15]
        sinal = [float(np.corrcoef(X[el][:, k], S[:, k])[0, 1]) if np.std(X[el][:, k]) > 0 and np.std(S[:, k]) > 0 else 0.0 for k in top]
        # classes de contexto (soma sobre os anéis, sem o próprio)
        cls = {}
        for f, v in zip(fn, a):
            blk, nm = f.split("|", 1)
            if blk not in ("proprio", "posicao"):
                cls[nm] = cls.get(nm, 0.0) + float(v)
        out[col] = {"por_bloco": {k: v / tot for k, v in grupo.items()},
                    "top": [{"feature": fn[k], "parte": float(a[k] / tot), "sinal": s} for k, s in zip(top, sinal)],
                    "classes_contexto": dict(sorted(((k, v / tot) for k, v in cls.items()), key=lambda t: -t[1])[:10])}
    return out


# --- C. bordas ----------------------------------------------------------------------------------

def bordas(b: dict, aux: dict, log=print, alvos=("quanto", "quanto_dist", "fen_div", "hora_noturna")) -> tuple[dict, dict]:
    idx, el = b["idx"], b["el"]
    P, A1 = b["P"], b["A1"]
    viz = aux["viz"]
    deg = np.asarray(A1.sum(axis=1)).ravel()
    dom = b["setor"].select("cd_setor").join(pl.read_parquet(atlas_dir() / f"setor_dominio_{REF_YEAR}.parquet"),
                                             on="cd_setor", how="left")["dominio"].fill_null(-1).to_numpy()
    rr, cc = A1.nonzero()
    outro_dom = np.bincount(rr, weights=(dom[rr] != dom[cc]).astype(float), minlength=len(dom)) / np.clip(deg, 1, None)
    fav = b["setor"]["favela"].to_numpy().astype(float)
    viz_fav = (A1 @ fav) / np.clip(deg, 1, None)
    censo = b["setor"].select("cd_setor").join(pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet")
                                               .select("cd_setor", "renda_mediana_resp"), on="cd_setor", how="left")
    lr = np.log(censo["renda_mediana_resp"].to_numpy().astype(float) + 100)
    ok_r = np.isfinite(lr)
    lr_f = np.where(ok_r, lr, 0.0)
    lr_viz = (A1 @ lr_f) / np.clip(A1 @ ok_r.astype(float), 1e-9, None)
    lr_viz = np.where(A1 @ ok_r.astype(float) > 0, lr_viz, np.nan)
    ipvs = b["setor"].select("cd_setor").join(pl.read_parquet(processed_dir() / "covariaveis" / "setor_ipvs.parquet")
                                              .select("cd_setor", "ipvs_codigo"), on="cd_setor", how="left")["ipvs_codigo"].to_numpy().astype(float)
    ok_i = np.isfinite(ipvs)
    ip_viz = (A1 @ np.where(ok_i, ipvs, 0.0)) / np.clip(A1 @ ok_i.astype(float), 1e-9, None)
    feats = {
        "contraste_r1": hellinger(P, viz["r1"]), "contraste_b500": hellinger(P, viz["b500"]),
        "contraste_b1000": hellinger(P, viz["b1000"]),
        "entropia_r1": -np.sum(np.where(viz["r1"] > 0, viz["r1"] * np.log(np.clip(viz["r1"], 1e-12, None)), 0), axis=1),
        "fronteira_dominio": outro_dom,
        "formal_junto_favela": (1 - fav) * viz_fav, "favela_junto_formal": fav * (1 - viz_fav),
        "renda_acima_viz": lr - lr_viz, "contraste_renda_abs": np.abs(lr - lr_viz),
        "ipvs_acima_viz": ipvs - ip_viz, "contraste_ipvs_abs": np.abs(ipvs - ip_viz),
    }
    ctrl = np.column_stack([lr, ipvs, fav])
    F = np.column_stack([feats[k] for k in feats])[idx]
    Ct = ctrl[idx]
    ok = el & np.isfinite(F).all(axis=1) & np.isfinite(Ct).all(axis=1)
    Fz = (F[ok] - F[ok].mean(0)) / F[ok].std(0)
    Cz = (Ct[ok] - Ct[ok].mean(0)) / Ct[ok].std(0)
    g = b["dist"][ok]
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    out = {"setores": int(ok.sum())}
    for col in alvos:
        y = _alvo(b, col, sem_tecido=True)
        yz = y[ok] / y[ok].std()
        um, conj = {}, {}
        for k, nome in enumerate(feats):
            be, ci = coef_fe(yz, np.column_stack([Fz[:, k], Cz]), g, n_boot=100)
            um[nome] = {"beta_dp": float(be[0]), "ic": [float(ci[0, 0]), float(ci[1, 0])]}
        be, ci = coef_fe(yz, np.column_stack([Fz, Cz]), g, n_boot=100)
        conj = {nome: {"beta_dp": float(be[k]), "ic": [float(ci[0, k]), float(ci[1, k])]} for k, nome in enumerate(feats)}
        r2_fe = float(1 - np.var(demean(yz, g) - demean(np.column_stack([Fz, Cz]), g) @ be) / np.var(demean(yz, g)))
        # gêmeos: a diferença de borda acompanha a diferença de resíduo?
        Fall = np.column_stack([feats[k] for k in feats])[idx]
        gem = {}
        for k, nome in enumerate(feats):
            fi, fj = Fall[i, k], Fall[j, k]
            m = np.isfinite(fi) & np.isfinite(fj) & (d < 1000)
            gem[nome] = float(np.corrcoef(y[i[m]] - y[j[m]], fi[m] - fj[m])[0, 1]) if m.sum() > 50 else None
        out[col] = {"um_a_um": um, "conjunto": conj, "r2_dentro_distrito": r2_fe, "gemeos_ate_1km_r": gem}
        sig = [n for n, v in um.items() if v["ic"][0] > 0 or v["ic"][1] < 0]
        log(f"  bordas {col}: R² dentro do distrito {r2_fe:.3f}; significativas: "
            + ", ".join(f"{n} {um[n]['beta_dp']:+.2f}" for n in sig))
    return out, feats


# --- borda de delegacia -------------------------------------------------------------------------

def _dp_pureza(b: dict) -> tuple[np.ndarray, np.ndarray]:
    ev = pl.scan_parquet(interim_dir() / C.EVENTOS).select("cd_setor", "dp_fato", "data_fato").filter(
        pl.col("cd_setor").is_not_null() & pl.col("dp_fato").is_not_null() & (pl.col("data_fato").dt.year() <= 2025)).collect()
    t = ev.group_by("cd_setor", "dp_fato").len()
    tot = t.group_by("cd_setor").agg(pl.col("len").sum().alias("tot"))
    m = t.sort("len", descending=True).group_by("cd_setor").first().join(tot, on="cd_setor").with_columns(
        (pl.col("len") / pl.col("tot")).alias("pureza")).select(pl.col("cd_setor").cast(pl.String), "dp_fato", "pureza")
    r = b["res"].select("cd_setor").join(m, on="cd_setor", how="left")
    return r["dp_fato"].fill_null("?").to_numpy(), r["pureza"].fill_null(0.0).to_numpy()


def _efeitos_celula(y, grupo, unidade, interior, min_n: int = 5) -> dict:
    """Média do interior de cada célula (grupo, unidade) menos a média do interior do grupo."""
    out = {}
    df = pl.DataFrame({"y": y, "g": grupo, "u": unidade, "i": interior}).filter(pl.col("i"))
    gm = df.group_by("g").agg(pl.col("y").mean().alias("gm"))
    cm = df.group_by("g", "u").agg(pl.col("y").mean().alias("cm"), pl.len().alias("n")).filter(pl.col("n") >= min_n).join(gm, on="g")
    for g, u, c, m in zip(cm["g"], cm["u"], cm["cm"], cm["gm"]):
        out[(g, u)] = c - m
    return out


def borda_delegacia(b: dict, log=print, extra: dict | None = None, so_extra: bool = False) -> dict:
    dp, pureza = _dp_pureza(b)
    res, el = b["res"], b["el"]
    dist = b["dist"]
    cs = res["cd_setor"].to_list()
    pos = {s: k for k, s in enumerate(cs)}
    viz = queen_neighbors().filter(pl.col("cd_setor").is_in(cs) & pl.col("vizinho").is_in(cs))
    a = np.array([pos[s] for s in viz["cd_setor"].to_list()])
    c = np.array([pos[s] for s in viz["vizinho"].to_list()])
    puro = el & (pureza >= PUREZA_DP)
    # interior: todos os vizinhos com a mesma delegacia (para o efeito de delegacia) / o mesmo distrito
    mesma_dp = np.ones(len(cs), bool)
    np.logical_and.at(mesma_dp, a, dp[a] == dp[c])
    mesmo_dist = np.ones(len(cs), bool)
    np.logical_and.at(mesmo_dist, a, dist[a] == dist[c])
    keep = a < c
    a, c = a[keep], c[keep]
    pares_ok = puro[a] & puro[c]
    alvos = {"quanto": _alvo(b, "quanto", True), "quanto_dist": _alvo(b, "quanto_dist", True),
             "fen_div": _alvo(b, "fen_div", True), "hora_noturna": _alvo(b, "hora_noturna", True)}
    alvos |= {k: res[k].to_numpy().astype(float) for k in res.columns if k.startswith("fen|")}
    if extra:
        alvos = (extra if so_extra else alvos | extra)
    out = {"pares_dp": 0, "pares_distrito": 0}
    rng = np.random.default_rng(3)
    for nome, y in alvos.items():
        o = {}
        for tipo, grupo, unidade, interior, sel in (
                ("delegacia", dist, dp, puro & mesma_dp, pares_ok & (dist[a] == dist[c]) & (dp[a] != dp[c])),
                ("distrito", dp, dist, puro & mesmo_dist, pares_ok & (dp[a] == dp[c]) & (dist[a] != dist[c]))):
            ef = _efeitos_celula(y, grupo, unidade, interior)
            ia, ic = a[sel], c[sel]
            de = np.array([ef.get((grupo[x], unidade[x]), np.nan) - ef.get((grupo[z], unidade[z]), np.nan) for x, z in zip(ia, ic)])
            m = np.isfinite(de)
            ia, ic, de = ia[m], ic[m], de[m]
            dy = y[ia] - y[ic]
            beta = float(np.sum(dy * de) / np.sum(de ** 2)) if len(de) > 20 else float("nan")
            gs = grupo[ia]
            ug = np.unique(gs)
            bs = []
            for _ in range(N_BOOT):
                pick = rng.choice(ug, len(ug))
                ix = np.concatenate([np.where(gs == u)[0] for u in pick])
                bs.append(np.sum(dy[ix] * de[ix]) / max(np.sum(de[ix] ** 2), 1e-12))
            # variância da diferença no par contra pares contíguos sem divisa
            base_sel = pares_ok & (dist[a] == dist[c]) & (dp[a] == dp[c])
            vr = float(np.var(dy) / np.var(y[a[base_sel]] - y[c[base_sel]]))
            o[tipo] = {"beta": beta, "ic": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], "pares": int(len(de)),
                       "razao_var_diferenca": vr}
            out[f"pares_{'dp' if tipo == 'delegacia' else 'distrito'}"] = max(out[f"pares_{'dp' if tipo == 'delegacia' else 'distrito'}"], int(len(de)))
        out[nome] = o
    for nome in [k for k in alvos if not k.startswith("fen|")]:
        o = out[nome]
        log(f"  borda {nome}: β delegacia {o['delegacia']['beta']:.2f} [{o['delegacia']['ic'][0]:.2f}, {o['delegacia']['ic'][1]:.2f}] "
            f"({o['delegacia']['pares']} pares) × β distrito {o['distrito']['beta']:.2f} [{o['distrito']['ic'][0]:.2f}, "
            f"{o['distrito']['ic'][1]:.2f}] ({o['distrito']['pares']} pares)")
    fen = {k: out[k]["delegacia"]["beta"] for k in alvos if k.startswith("fen|")}
    log("  borda por fenótipo (β delegacia): " + ", ".join(f"{k[4:]} {v:.2f}" for k, v in sorted(fen.items(), key=lambda t: -t[1])))
    out["pureza_min"] = PUREZA_DP
    return out


# --- interações entre tipos ---------------------------------------------------------------------

def interacoes(b: dict, n_amostra: int = 1500, log=print) -> tuple[dict, pl.DataFrame]:
    import lightgbm as lgb
    import shap

    el, names = b["el"], b["names"]
    fn = list(names) + ["log_tamanho", "densidade"]
    X = b["Xown"][el]
    rng = np.random.default_rng(0)
    amostra = rng.choice(len(X), min(n_amostra, len(X)), replace=False)
    out, linhas = {}, []
    for col in ("quanto", "fen_div", "hora_noturna"):
        y = _alvo(b, col)[el]
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.7, random_state=0, verbose=-1).fit(X, y)
        I = shap.TreeExplainer(m).shap_interaction_values(X[amostra])
        A = np.abs(I).mean(axis=0)
        diag = np.trace(A)
        fora = A.sum() - diag
        K = len(fn)
        pares = []
        Xa = X[amostra]
        for p in range(K):
            for q in range(p + 1, K):
                v = 2 * A[p, q]
                altos = (Xa[:, p] > np.quantile(Xa[:, p], 0.75)) & (Xa[:, q] > np.quantile(Xa[:, q], 0.75))
                sin = float(2 * I[altos, p, q].mean()) if altos.sum() >= 20 else None
                pares.append((fn[p], fn[q], float(v), sin))
        pares.sort(key=lambda t: -t[2])
        S = I.sum(axis=2)
        principais = np.argsort(-np.abs(S).mean(axis=0))[:8]
        forma = {}
        for k in principais:
            x = Xa[:, k]
            nz = x > 0
            if nz.sum() < 50:
                continue
            qs = np.quantile(x[nz], [0, 0.2, 0.4, 0.6, 0.8, 1.0])
            bins = np.clip(np.searchsorted(qs, x[nz], side="right") - 1, 0, 4)
            forma[fn[k]] = {"zero": float(S[~nz, k].mean()) if (~nz).sum() else None,
                            "quintis": [float(S[nz][bins == t, k].mean()) for t in range(5)]}
        out[col] = {"parte_interacao": float(fora / A.sum()),
                    "pares_top": [{"a": a, "b": c, "media_abs": v, "sinal_ambos_altos": s} for a, c, v, s in pares[:12]],
                    "efeito_principal_forma": forma}
        linhas += [{"desfecho": col, "a": a, "b": c, "media_abs": v, "sinal_ambos_altos": s} for a, c, v, s in pares[:50]]
        log(f"  interações {col}: {out[col]['parte_interacao']:.0%} da contribuição é interação; topo "
            + "; ".join(f"{a} × {c} ({s:+.2f})" if s is not None else f"{a} × {c}" for a, c, _, s in pares[:3]))
    return out, pl.DataFrame(linhas)


# --- F. motivos de contexto ---------------------------------------------------------------------

def motivos(b: dict, aux: dict, ks=(8, 10, 12, 14, 16), log=print) -> tuple[dict, pl.DataFrame]:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.metrics import silhouette_score

    viz = aux["viz"]
    Z = np.column_stack([np.sqrt(b["P"]), np.sqrt(viz["r1"]), np.sqrt(viz["b500"]), np.sqrt(viz["b1000"])])
    Zp = PCA(20, random_state=0).fit_transform(Z)
    rng = np.random.default_rng(0)
    sub = rng.choice(len(Zp), 6000, replace=False)
    sil, labs = {}, {}
    for k in ks:
        lab = KMeans(k, n_init=10, random_state=0).fit_predict(Zp)
        sil[k] = float(silhouette_score(Zp[sub], lab[sub]))
        labs[k] = lab
    k = max(sil, key=sil.get)
    lab = labs[k]
    names = b["names"]
    cid = lab[b["idx"]]
    dom = b["res"].select("cd_setor").join(pl.read_parquet(atlas_dir() / f"setor_dominio_{REF_YEAR}.parquet"),
                                           on="cd_setor", how="left")["dominio"].fill_null(-1).to_numpy()
    el = b["el"]
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    out = {"k": k, "silhueta": sil}

    def eta2(z, g):
        return float(1 - np.var(demean(z, g)) / np.var(z))

    for col in ("quanto", "quanto_dist", "fen_div", "hora_noturna"):
        y = _alvo(b, col, sem_tecido=True)[el]
        o = {}
        for nome, g in (("dominio", dom[el]), ("contexto", cid[el]), ("dominio_x_contexto", dom[el] * 100 + cid[el])):
            obs = eta2(y, g)
            nulo = np.mean([eta2(y, rng.permutation(g)) for _ in range(20)])
            o[nome] = {"eta2": obs, "eta2_acaso": float(nulo)}
        same = cid[i] == cid[j]
        z = _alvo(b, col, sem_tecido=True)
        for nome, m in (("mesmo_contexto", same), ("outro_contexto", ~same),
                        ("mesmo_contexto_longe", same & (d > 3000)), ("outro_contexto_perto", ~same & (d < 1000)),
                        ("mesmo_contexto_perto", same & (d < 1000))):
            o[f"gemeos_{nome}"] = {"r": C._corr_sim(z, i[m], j[m]), "pares": int(m.sum())}
        out[col] = o
        log(f"  motivos {col}: η² contexto {o['contexto']['eta2']:.3f} (acaso {o['contexto']['eta2_acaso']:.3f}), domínio "
            f"{o['dominio']['eta2']:.3f}; gêmeos mesmo contexto longe {o['gemeos_mesmo_contexto_longe']['r']:.2f}")
    # marcadores: classes mais enriquecidas no entorno (500 m) e no próprio setor
    city_r = viz["b500"].mean(axis=0)
    city_o = b["P"].mean(axis=0)
    marc = {}
    for c in range(k):
        m = lab == c
        er = np.log2((viz["b500"][m].mean(0) + 1e-6) / (city_r + 1e-6))
        eo = np.log2((b["P"][m].mean(0) + 1e-6) / (city_o + 1e-6))
        marc[int(c)] = {"setores": int(m.sum()), "entorno": [names[t] for t in np.argsort(-er)[:4]],
                        "proprio": [names[t] for t in np.argsort(-eo)[:3]]}
    out["marcadores"] = marc
    return out, pl.DataFrame({"cd_setor": b["cs"], "contexto": lab})


# --- G. contágio contra contexto ----------------------------------------------------------------

def contagio(b: dict, aux: dict, log=print) -> dict:
    from sklearn.decomposition import PCA
    from spreg import ML_Error, ML_Lag, OLS

    sub = b["res"].filter(pl.col("elegivel"))
    w, keep = C._pesos(sub)
    rows = np.where(b["el"])[0][keep]
    W = w.sparse
    pcs = PCA(10, random_state=0).fit_transform(np.sqrt(b["P"][b["idx"]]))
    out = {}
    for col in ("quanto", "quanto_dist", "hora_noturna"):
        y = _alvo(b, col)[rows]
        p_own = aux["oof"][col]["p_own"][rows]
        X = np.column_stack([p_own, pcs[rows]])
        WX = W @ X
        nm = ["p_tecido"] + [f"pc{k}" for k in range(10)]
        o = {}
        m = OLS(y[:, None], X, name_x=nm)
        o["ols"] = {"r2": float(m.r2), "aic": float(m.aic)}
        m = OLS(y[:, None], np.column_stack([X, WX]), name_x=nm + [f"W_{n}" for n in nm])
        o["slx"] = {"r2": float(m.r2), "aic": float(m.aic), "W_p_tecido": float(m.betas[1 + len(nm)][0])}
        m = ML_Lag(y[:, None], X, w=w, method="LU", name_x=nm)
        o["sar"] = {"rho": float(m.rho), "aic": float(m.aic), "pr2": float(m.pr2)}
        m = ML_Error(y[:, None], X, w=w, method="LU", name_x=nm)
        o["sem"] = {"lambda": float(m.lam), "aic": float(m.aic), "pr2": float(m.pr2)}
        m = ML_Lag(y[:, None], np.column_stack([X, WX]), w=w, method="LU", name_x=nm + [f"W_{n}" for n in nm])
        o["sdm"] = {"rho": float(m.rho), "aic": float(m.aic), "pr2": float(m.pr2)}
        out[col] = o
        log(f"  contágio {col}: SAR ρ {o['sar']['rho']:.2f}, SDM ρ {o['sdm']['rho']:.2f}, SEM λ {o['sem']['lambda']:.2f}; "
            f"AIC ols {o['ols']['aic']:.0f} slx {o['slx']['aic']:.0f} sar {o['sar']['aic']:.0f} sem {o['sem']['aic']:.0f} sdm {o['sdm']['aic']:.0f}")
    out["painel"] = _painel(b, rows, W, log=log)
    return out


def _painel(b: dict, rows: np.ndarray, W, log=print) -> dict:
    """Painel anual: o resíduo (ou o choque) dos vizinhos em t prevê o do setor em t+1?"""
    from cityomics.atlas.attribution import em_fit_multi
    from cityomics.atlas.fenotipo import YEARS, setor_exposicao
    from cityomics.atlas.memoria import contagens

    ids, E, _ = setor_exposicao()
    assert (ids["cd_setor"] == b["res"]["cd_setor"]).all()
    Y = contagens(ids)
    M = E @ em_fit_multi(E, Y)
    R = np.column_stack([C.razao_encolhida(Y[:, k], M[:, k])[0] for k in range(len(YEARS))])[rows]
    WR = W @ R
    dist = b["dist"][rows]
    out = {}
    for nome, (yv, x_own, x_viz) in {
            "nivel": (R[:, 1:], R[:, :-1], WR[:, :-1]),
            "choque": (np.diff(R, axis=1)[:, 1:], np.diff(R, axis=1)[:, :-1], np.diff(WR, axis=1)[:, :-1])}.items():
        T = yv.shape[1]
        y = yv.T.ravel()
        X = np.column_stack([x_own.T.ravel(), x_viz.T.ravel()])
        g = np.concatenate([np.char.add(dist.astype(str), f"|{t}") for t in range(T)])
        be, ci = coef_fe(y, X, g, n_boot=N_BOOT)
        be2, ci2 = coef_fe(y, X, np.concatenate([np.full(len(dist), str(t)) for t in range(T)]), n_boot=N_BOOT)
        out[nome] = {"distrito_ano": {"proprio": float(be[0]), "vizinhos": float(be[1]), "ic_vizinhos": [float(ci[0, 1]), float(ci[1, 1])]},
                     "so_ano": {"proprio": float(be2[0]), "vizinhos": float(be2[1]), "ic_vizinhos": [float(ci2[0, 1]), float(ci2[1, 1])]}}
        log(f"  painel {nome}: vizinhos em t → setor em t+1: β {be[1]:+.3f} [{ci[0, 1]:+.3f}, {ci[1, 1]:+.3f}] com distrito×ano "
            f"(só ano {be2[1]:+.3f}); próprio {be[0]:+.3f}")
    return out


# --- orquestração -------------------------------------------------------------------------------

def run(log=print) -> dict:
    b = base(log=log)
    rep = {}
    rep["aneis"], aux = aneis(b, log=log)
    rep["bordas"], feats = bordas(b, aux, log=log)
    rep["borda_delegacia"] = borda_delegacia(b, log=log)
    rep["interacoes"], tab_int = interacoes(b, log=log)
    tab_int.write_parquet(C.out_dir() / "interacoes_tipos.parquet")
    rep["motivos"], lab = motivos(b, aux, log=log)
    lab.write_parquet(C.out_dir() / "motivos_setor.parquet")
    rep["contagio"] = contagio(b, aux, log=log)
    pl.DataFrame({"cd_setor": b["res"]["cd_setor"]} | {f"ctx|{c}": aux["oof"][c]["p_full"] - aux["oof"][c]["p_own"] for c in ALVOS}
                 | {f"borda|{k}": v[b["idx"]] for k, v in feats.items()}).write_parquet(C.out_dir() / "vizinhanca_setor.parquet")
    (C.out_dir() / "vizinhanca.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=float))
    return rep
