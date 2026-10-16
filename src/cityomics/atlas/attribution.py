"""Atribuição do crime às classes de célula (spec-atlas §3.2; D21, D29, D47, D51, D53, D57, D61).

O crime de cada spot é a soma do que cada classe de célula "produz":
``y_s ~ Poisson(δ_d · Σ_k E_sk · λ_k)``. As classes k são os tipos de lote (exposição = testada),
as pseudo-células FCU, as três classes de rua (comprimento) e as estações/terminais (contagem);
δ_d é um efeito de distrito ("espacial") opcional.

- ``em_fit``: máxima verossimilhança com λ ≥ 0 por EM (atualização multiplicativa de
  Richardson–Lucy, que é o EM do Poisson linear). Bootstrap por distrito para os intervalos.
- ``fit_covariates``: λ_k(x) = exp(β_k0 + Σ_g β_kg z_g), com os 4 grupos teóricos não temporais
  (o contexto temporal é igual para a cidade toda e não entra no total anual, D57). L-BFGS com
  gradiente analítico e ridge leve nas inclinações.
- ``shapley_flows``: decomposição exata do crime esperado de 2025 por (classe, grupo) contra a
  referência do setor médio (z = 0): nó "identidade da classe" = v(∅), contribuições de Shapley
  separadas em aumento e redução, e o nó "espacial" = (δ_d − 1)·Σ_k c_sk. É a base do Sankey (D57).
- ``point_validation``: eventos geocodificados (locais) → segmento de rua mais próximo → lotes
  lindeiros (dentro de 40 m do segmento), com o evento repartido pela testada; perto de estações,
  vai para a estação. Só as taxas agregadas por classe saem.

Toda análise com crime exclui os distritos do cofre espacial (D53).
"""

from __future__ import annotations

import itertools
import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.spots import exposure_matrix
from cityomics.paths import interim_dir, processed_dir

GROUPS = ["atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario"]


# --- EM do Poisson linear -----------------------------------------------------------------------

def em_fit(E: np.ndarray, y: np.ndarray, groups: np.ndarray | None = None, n_iter: int = 500, tol: float = 1e-8):
    """λ ≥ 0 (e δ por grupo, se ``groups``) que maximizam a verossimilhança de y ~ Poisson(δ_g · E λ)."""
    keep = E.sum(axis=1) > 0
    E, y = E[keep], y[keep]
    g = groups[keep] if groups is not None else None
    colsum = E.sum(axis=0)
    lam = np.full(E.shape[1], y.sum() / max(colsum.sum(), 1e-12))
    lam[colsum == 0] = 0.0
    delta = np.ones(len(y))
    ll_old = -np.inf
    for _ in range(n_iter):
        mu0 = E @ lam
        mu = delta * mu0
        ratio = np.divide(y, mu, out=np.zeros_like(y, dtype=float), where=mu > 0)
        den = (E * delta[:, None]).sum(axis=0)
        lam = lam * np.divide(E.T @ (ratio * delta), den, out=np.zeros_like(lam), where=den > 0)
        if g is not None:
            mu0 = E @ lam
            num = np.bincount(g, weights=y)
            den_g = np.bincount(g, weights=mu0)
            dg = np.divide(num, den_g, out=np.ones_like(num), where=den_g > 0)
            dg = dg / np.exp(np.mean(np.log(np.clip(dg[den_g > 0], 1e-9, None))))
            delta = dg[g]
        mu = delta * (E @ lam)
        ll = float(np.sum(y * np.log(np.clip(mu, 1e-300, None)) - mu))
        if abs(ll - ll_old) < tol * (1 + abs(ll)):
            break
        ll_old = ll
    out = {"lam": lam, "ll": ll}
    if g is not None:
        out["delta_grupo"] = dg
    return out


def bootstrap(E, y, clusters, n_boot: int = 500, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    uc, inv = np.unique(clusters, return_inverse=True)
    rows = [np.where(inv == i)[0] for i in range(len(uc))]
    out = np.empty((n_boot, E.shape[1]))
    for b in range(n_boot):
        pick = rng.integers(0, len(uc), len(uc))
        idx = np.concatenate([rows[i] for i in pick])
        out[b] = em_fit(E[idx], y[idx])["lam"]
    return out


# --- grupos teóricos (z_g) ----------------------------------------------------------------------

def group_scores(year: int = REF_YEAR) -> pl.DataFrame:
    """PC1 padronizado de cada grupo teórico, por setor, com as covariáveis médias do ano."""
    core = json.loads((guard.REPO_ROOT / "prereg" / "core_covariates.json").read_text())["groups"]
    cols = sorted({c for gname in GROUPS for c in core[gname]})
    path = processed_dir() / "covariaveis" / "painel_setor_mes.parquet"
    have = set(pl.read_parquet_schema(path).keys()) if hasattr(pl, "read_parquet_schema") else set(pl.scan_parquet(path).collect_schema().names())
    cols = [c for c in cols if c in have]
    p = (pl.scan_parquet(path).filter(pl.col("mes").cast(pl.String).str.starts_with(str(year)))
         .select("cd_setor", *cols).group_by("cd_setor").agg([pl.col(c).cast(pl.Float64).mean() for c in cols]).collect())
    out = p.select(pl.col("cd_setor").cast(pl.String))
    for gname in GROUPS:
        gc = [c for c in core[gname] if c in cols]
        X = p.select(gc).to_numpy().astype(float)
        X = np.where(np.isnan(X), np.nanmedian(X, axis=0), X)
        sign = np.array([-1.0 if ("dist_" in c or c.endswith("_m")) else 1.0 for c in gc])
        Zs = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1.0) * sign
        u, s, vt = np.linalg.svd(Zs - Zs.mean(0), full_matrices=False)
        pc = u[:, 0] * s[0]
        if np.corrcoef(pc, Zs.mean(1))[0, 1] < 0:
            pc = -pc
        out = out.with_columns(pl.Series(gname, (pc - pc.mean()) / pc.std()))
    return out


# --- λ dependente das covariáveis + Shapley -----------------------------------------------------

def fit_covariates(E: np.ndarray, y: np.ndarray, Z: np.ndarray, groups: np.ndarray | None = None,
                   ridge: float = 200.0, max_slope: float = 1.0, n_outer: int = 6) -> dict:
    from scipy.optimize import minimize

    keep = E.sum(axis=1) > 0
    E, y, Z = E[keep], y[keep], Z[keep]
    g = groups[keep] if groups is not None else None
    K, Gn = E.shape[1], Z.shape[1]
    Zt = np.hstack([np.ones((len(y), 1)), Z])  # coluna 0 = intercepto
    base = em_fit(E, y)["lam"]
    b0 = np.zeros((K, Gn + 1))
    b0[:, 0] = np.log(np.clip(base, 1e-12, None))
    active = E.sum(axis=0) > 0
    delta = np.ones(len(y))

    def nll(theta):
        B = theta.reshape(K, Gn + 1)
        eta = Zt @ B.T  # (n, K)
        C = E * np.exp(np.clip(eta, -30, 30))
        mu = delta * C.sum(1)
        mu = np.clip(mu, 1e-12, None)
        f = -(y * np.log(mu) - mu).sum() + 0.5 * ridge * (B[:, 1:] ** 2).sum()
        w = (y / mu - 1.0) * delta
        grad = -(C * w[:, None]).T @ Zt
        grad[:, 1:] += ridge * B[:, 1:]
        grad[~active] = 0.0
        return f, grad.ravel()

    theta = b0.ravel()
    for _ in range(n_outer):
        # inclinações limitadas a ±max_slope por desvio-padrão do escore: λ_k só pode variar e^±1 por DP,
        # o que evita a explosão de classes quase sem crime (inferência ecológica com grupos colineares)
        bounds = [(None, None) if j == 0 else (-max_slope, max_slope) for _ in range(K) for j in range(Gn + 1)]
        r = minimize(nll, theta, jac=True, method="L-BFGS-B", bounds=bounds, options={"maxiter": 800})
        theta = r.x
        if g is None:
            break
        B = theta.reshape(K, Gn + 1)
        mu0 = (E * np.exp(np.clip(Zt @ B.T, -30, 30))).sum(1)
        num, den = np.bincount(g, weights=y), np.bincount(g, weights=mu0)
        dg = np.divide(num, den, out=np.ones_like(num), where=den > 0)
        dg = dg / np.exp(np.mean(np.log(np.clip(dg[den > 0], 1e-9, None))))
        delta = dg[g]
    B = theta.reshape(K, Gn + 1)
    return {"B": B, "delta": delta, "keep": keep, "nll": float(r.fun)}


def shapley_flows(E: np.ndarray, Z: np.ndarray, B: np.ndarray, delta: np.ndarray) -> dict:
    """Shapley exato por classe sobre os grupos (referência z = 0), somado na cidade."""
    n, K = E.shape
    Gn = Z.shape[1]
    phi = np.zeros((K, Gn))
    ident = np.zeros(K)
    total = np.zeros(K)
    from math import factorial

    w = {s: factorial(s) * factorial(Gn - s - 1) / factorial(Gn) for s in range(Gn)}
    for k in range(K):
        if E[:, k].sum() == 0:
            continue
        lin = Z * B[k, 1:]  # (n, G): contribuição de cada grupo ao log da taxa
        v = lambda S: E[:, k] * np.exp(B[k, 0] + lin[:, list(S)].sum(1)) if S else E[:, k] * np.exp(B[k, 0])  # noqa: E731
        cache = {S: v(S) for r in range(Gn + 1) for S in itertools.combinations(range(Gn), r)}
        ident[k] = cache[()].sum()
        total[k] = cache[tuple(range(Gn))].sum()
        for gi in range(Gn):
            acc = np.zeros(n)
            others = [x for x in range(Gn) if x != gi]
            for r in range(Gn):
                for S in itertools.combinations(others, r):
                    acc += w[len(S)] * (cache[tuple(sorted(S + (gi,)))] - cache[S])
            phi[k, gi] = acc.sum()
    c_full = np.zeros(n)
    for k in range(K):
        c_full += E[:, k] * np.exp(B[k, 0] + (Z * B[k, 1:]).sum(1))
    espacial = float(((delta - 1.0) * c_full).sum())
    return {"identidade": ident, "phi": phi, "total": total, "espacial": espacial}


# --- validação pontual --------------------------------------------------------------------------

def point_validation(year: int = REF_YEAR, buffer_m: float = 40.0, max_dist: float = 60.0, station_m: float = 100.0,
                     log=print) -> pl.DataFrame:
    import geopandas as gpd
    from shapely import STRtree

    from cityomics.units.setores import CRS

    ev = (pl.scan_parquet(guard.pre2026(interim_dir() / "eventos_celular_atribuidos.parquet"))
          .filter((pl.col("data_fato").dt.year() == year) & pl.col("coord_valida"))
          .select("latitude", "longitude", "cd_dist").collect())
    ev = ev.filter(pl.Series(guard.explore_mask(ev["cd_dist"].to_numpy())))
    pts = gpd.GeoSeries(gpd.points_from_xy(ev["longitude"], ev["latitude"]), crs="EPSG:4326").to_crs(CRS)
    seg = gpd.read_parquet(atlas_dir() / "ruas.parquet")
    from cityomics.atlas.streets import stations

    st = stations()
    st_tree = STRtree(st.geometry.values)
    near_st = st_tree.query_nearest(pts.values, max_distance=station_m, return_distance=False)
    is_st = np.zeros(len(pts), bool)
    is_st[near_st[0]] = True
    tree = STRtree(seg.geometry.values)
    q = tree.query_nearest(pts.values[~is_st], max_distance=max_dist, return_distance=False)
    seg_of = np.full((~is_st).sum(), -1)
    seg_of[q[0]] = q[1]
    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet").filter(pl.col("x").is_not_null())
    cel = cel.filter(pl.Series(guard.explore_mask(cel["cd_dist"].to_numpy())))
    lp = gpd.GeoSeries(gpd.points_from_xy(cel["x"], cel["y"]), crs=CRS)
    used = np.unique(seg_of[seg_of >= 0])
    lt = STRtree(lp.values)
    pairs = lt.query(seg.geometry.values[used], predicate="dwithin", distance=buffer_m)
    seg_ids = used[pairs[0]]
    lot_ids = pairs[1]
    expo = cel["exposicao"].to_numpy()
    tipo = cel["tipo"].to_numpy()
    # repartição do evento entre lotes lindeiros, proporcional à testada
    import pandas as pd

    lind = pd.DataFrame({"seg": seg_ids, "lot": lot_ids, "w": expo[lot_ids]})
    lind["w"] = lind["w"] / lind.groupby("seg")["w"].transform("sum")
    cnt = pd.Series(seg_of[seg_of >= 0]).value_counts()
    lind["ev"] = lind["seg"].map(cnt).fillna(0) * lind["w"]
    lind["tipo"] = tipo[lind["lot"].to_numpy()]
    obs = lind.groupby("tipo")["ev"].sum()
    exp_tipo = pd.Series(expo).groupby(tipo).sum()
    rows = [{"classe": t, "eventos": float(obs.get(t, 0.0)), "exposicao": float(exp_tipo.get(t, 0.0))} for t in exp_tipo.index]
    seg_cls = seg["classe"].to_numpy()
    seg_len = seg.assign(cd_dist=seg["cd_setor"].astype(str).str[:9])
    rows += [{"classe": f"rua_{c}_m", "eventos": float((seg_cls[seg_of[seg_of >= 0]] == c).sum()),
              "exposicao": float(seg.loc[seg["classe"] == c, "comprimento_m"].sum())} for c in ("arterial", "coletora", "local")]
    rows.append({"classe": "estacoes", "eventos": float(is_st.sum()), "exposicao": float(len(st))})
    out = pl.DataFrame(rows).with_columns((pl.col("eventos") / pl.col("exposicao")).alias("taxa_observada"))
    log(f"validação pontual: {len(pts):,} eventos de {year} fora do cofre; {is_st.sum():,} em estações; "
        f"{(seg_of >= 0).sum():,} ligados a um segmento")
    del seg_len
    return out


# --- execução ---------------------------------------------------------------------------------

def crime_setor(year: int = REF_YEAR) -> pl.DataFrame:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet"))
    return (t.filter(pl.col("periodo").str.starts_with(str(year))).group_by("cd_setor")
            .agg(pl.col("n_total").sum().alias("y"), pl.col("n_geo").sum().alias("y_geo")))


def run(n_boot: int = 500, log=print) -> dict:
    d = atlas_dir()
    setor = pl.read_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    setor = setor.join(crime_setor(), on="cd_setor", how="left").fill_null(0)
    setor = setor.join(group_scores(), on="cd_setor", how="left").fill_null(0.0)
    ex = setor.filter(pl.Series(guard.explore_mask(setor["cd_dist"].to_numpy())))
    E, names = exposure_matrix(ex)
    E = E / 1000.0  # metros → km (taxas por km de frente ou de rua; estações por unidade × 1000)
    est = [i for i, n in enumerate(names) if n.startswith("n_")]
    E[:, est] *= 1000.0
    y = ex["y"].to_numpy().astype(float)
    dist = np.unique(ex["cd_dist"].to_numpy(), return_inverse=True)[1]
    base = em_fit(E, y)
    bdist = em_fit(E, y, groups=dist)
    boot = bootstrap(E, y, ex["cd_dist"].to_numpy(), n_boot=n_boot)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    lam = pl.DataFrame({"classe": names, "lambda": base["lam"], "lambda_ic_lo": lo, "lambda_ic_hi": hi,
                        "lambda_com_distrito": bdist["lam"], "exposicao_total": E.sum(0)})
    Z = ex.select(GROUPS).to_numpy()
    cov = fit_covariates(E, y, Z, groups=dist)
    keep = cov["keep"]
    fl = shapley_flows(E[keep], Z[keep], cov["B"], cov["delta"])
    flows = []
    for k, n in enumerate(names):
        flows.append({"classe": n, "origem": "identidade", "valor": float(fl["identidade"][k])})
        for gi, gname in enumerate(GROUPS):
            flows.append({"classe": n, "origem": gname, "valor": float(fl["phi"][k, gi])})
    flows = pl.DataFrame(flows)
    pv = point_validation(log=log).join(lam.select("classe", "lambda"), on="classe", how="left")
    lam.write_parquet(d / "atribuicao_celular_2025.parquet")
    flows.write_parquet(d / "sankey_celular_2025.parquet")
    pv.write_parquet(d / "validacao_pontual_2025.parquet")
    pv_ok = pv.filter(pl.col("lambda").is_not_null() & (pl.col("exposicao") > 0))
    from scipy.stats import spearmanr

    rho = float(spearmanr(pv_ok["lambda"], pv_ok["taxa_observada"]).statistic) if pv_ok.height > 3 else float("nan")
    mu = E @ base["lam"]
    dev_null = 2 * np.sum(np.where(y > 0, y * np.log(y / y.mean()), 0) - (y - y.mean()))
    dev = 2 * np.sum(np.where(y > 0, y * np.log(np.clip(y, 1e-12, None) / np.clip(mu, 1e-12, None)), 0) - (y - mu))
    rep = {"setores_exploracao": int(ex.height), "crime_total": float(y.sum()), "d2_composicao": float(1 - dev / dev_null),
           "espacial_total": fl["espacial"], "spearman_validacao_pontual": rho,
           "ridge": 1.0, "grupos": GROUPS, "n_boot": n_boot}
    (d / "atribuicao_celular_2025.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"atribuição celular: D² da composição = {rep['d2_composicao']:.3f}; Spearman validação pontual = {rho:.2f}")
    return rep


def refit_sankey(ridge: float = 200.0, max_slope: float = 1.0, log=print) -> pl.DataFrame:
    """Recalcula só a decomposição do Sankey (sem refazer bootstrap nem validação pontual)."""
    d = atlas_dir()
    setor = pl.read_parquet(d / f"setor_composicao_{REF_YEAR}.parquet")
    setor = setor.join(crime_setor(), on="cd_setor", how="left").fill_null(0)
    setor = setor.join(group_scores(), on="cd_setor", how="left").fill_null(0.0)
    ex = setor.filter(pl.Series(guard.explore_mask(setor["cd_dist"].to_numpy())))
    E, names = exposure_matrix(ex)
    E = E / 1000.0
    est = [i for i, n in enumerate(names) if n.startswith("n_")]
    E[:, est] *= 1000.0
    y = ex["y"].to_numpy().astype(float)
    dist = np.unique(ex["cd_dist"].to_numpy(), return_inverse=True)[1]
    Z = ex.select(GROUPS).to_numpy()
    cov = fit_covariates(E, y, Z, groups=dist, ridge=ridge, max_slope=max_slope)
    keep = cov["keep"]
    fl = shapley_flows(E[keep], Z[keep], cov["B"], cov["delta"])
    rows = []
    for k, n in enumerate(names):
        rows.append({"classe": n, "origem": "identidade", "valor": float(fl["identidade"][k])})
        for gi, gname in enumerate(GROUPS):
            rows.append({"classe": n, "origem": gname, "valor": float(fl["phi"][k, gi])})
    flows = pl.DataFrame(rows)
    flows.write_parquet(d / "sankey_celular_2025.parquet")
    pl.DataFrame({"classe": names, **{f"beta_{g}": cov["B"][:, i + 1] for i, g in enumerate(GROUPS)},
                  "beta0": cov["B"][:, 0]}).write_parquet(d / "sankey_coeficientes_2025.parquet")
    rep = json.loads((d / "atribuicao_celular_2025.json").read_text())
    rep |= {"ridge": ridge, "inclinacao_max": max_slope, "espacial_total": fl["espacial"],
            "sankey_total_identidade": float(fl["identidade"].sum()), "sankey_total_phi": float(fl["phi"].sum())}
    (d / "atribuicao_celular_2025.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"Sankey: identidade {fl['identidade'].sum():,.0f}; Σφ {fl['phi'].sum():,.0f}; espacial {fl['espacial']:,.0f}")
    return flows
