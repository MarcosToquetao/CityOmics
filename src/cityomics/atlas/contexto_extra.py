"""Contexto espacial dos gêmeos de tecido, passo 4: o que ficou pendente (exploratório, fora do artigo).

- **Equalizado:** cada contexto vira um bloco de 8 dimensões (PCA) e entra sozinho sobre o tecido próprio.
  Isso tira a vantagem dos blocos com mais variáveis. Há um bloco de ruído de 8 dimensões como nulo e
  combinações (1º anel + fluxos OD, etc.) para ver a redundância entre contextos.
- **Tendência mensal:** inclinação log-linear do crime de celular em 48 meses por setor (Poisson com
  offset do esperado pelo tecido em cada ano e ridge na inclinação), com confiabilidade pela
  separação de meses pares e ímpares. Reabre a tendência, que no artigo anual era ruído.
- **OD, incerteza e 2017:** bootstrap de domicílios estratificado pela zona (como ``presenca_od2023``)
  sobre os efeitos dos fluxos e sobre o ganho de R²; as mesmas variáveis com a OD 2017 e com as duas
  juntas.
- **Interação tipo × fluxo:** o efeito da diversidade de origens e dos visitantes por morador por domínio
  e por tipo dominante, com bootstrap por distrito e estatística Q de heterogeneidade.
- **MGWR:** as taxas por classe de célula variam no espaço? Regressão geograficamente ponderada
  multiescala sobre uma subamostra, com as cinco classes que mais respondem pelo crime esperado.
- **GNN com cinco sementes:** média e desvio dos R² da ablação de saltos, inclusive para a tendência.

Só distritos de exploração (D53) e nada de 2026. Saídas em ``data/processed/atlas/contexto/extra.json``.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl
import scipy.sparse as sp

from cityomics.atlas import contexto as C
from cityomics.atlas import contexto_grafo as G
from cityomics.atlas import contexto_vizinhanca as V
from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import setor_exposicao
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.memoria import MIN_ESPERADO, contagens
from cityomics.paths import processed_dir

ALVOS4 = ("quanto", "quanto_dist", "fen_div", "hora_noturna")
K_BLOCO = 8
SIGMA_OD = G.SIGMA_OD


def _salva(chave: str, valor) -> None:
    p = C.out_dir() / "extra.json"
    d = json.loads(p.read_text()) if p.exists() else {}
    d[chave] = valor
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2, default=float))


def base_ext(log=print) -> dict:
    """``contexto_vizinhanca.base`` com a tendência mensal anexada, se já calculada."""
    b = V.base(log=log)
    p = C.out_dir() / "residuos_tendencia.parquet"
    if p.exists():
        t = pl.read_parquet(p)
        assert (t["cd_setor"] == b["res"]["cd_setor"]).all()
        b["res"] = b["res"].with_columns(t["tend_mensal"])
        b["sem"] = b["sem"].with_columns(t["tend_mensal_sem_tecido"])
    return b


def _alvos_com_tendencia(b: dict) -> tuple[str, ...]:
    return ALVOS4 + (("tend_mensal",) if "tend_mensal" in b["res"].columns else ())


# --- blocos de contexto (8 dimensões cada) -----------------------------------------------------

def _pca(M: np.ndarray, k: int = K_BLOCO, padroniza: bool = False) -> np.ndarray:
    from sklearn.decomposition import PCA

    M = np.nan_to_num(np.asarray(M, dtype=float), nan=0.0)
    if padroniza:
        M = (M - M.mean(0)) / np.maximum(M.std(0), 1e-9)
    return PCA(min(k, M.shape[1]), random_state=0).fit_transform(M)


def blocos(b: dict) -> dict[str, np.ndarray]:
    idx = b["idx"]
    viz = V.comp_aneis(b)
    out = {k: _pca(np.sqrt(viz[k]))[idx] for k in ("r1", "r2", "b500", "b1000", "b2000")}
    infra = pl.read_parquet(processed_dir() / "covariaveis" / "setor_infra.parquet")
    inf = b["res"].select("cd_setor").join(infra, on="cd_setor", how="left")
    pos = np.column_stack([np.log1p(inf[c].fill_null(inf[c].median()).to_numpy().astype(float)) for c in V.POSICAO]
                          + [np.log1p(np.hypot(*(b["xy"][idx] - b["se"]).T))])
    out["posicao"] = _pca(pos, padroniza=True)
    rs = pl.read_parquet(C.out_dir() / "rede_setor.parquet")
    out["rede_metricas"] = _pca(np.column_stack([np.log1p(rs[c].to_numpy()) for c in rs.columns[1:]]), padroniza=True)[idx]
    R = sp.load_npz(C.out_dir() / "rede_alcance_800.npz")
    out["rede800_composicao"] = _pca(np.sqrt(V.composicao_contexto(b, R)))[idx]
    od = pl.read_parquet(C.out_dir() / "od_setor.parquet")
    Fo = np.column_stack([od[c].to_numpy() for c in od.columns[1:]])
    Fo = np.where(np.isfinite(Fo), Fo, np.nanmedian(Fo, 0))
    out["od_fluxos"] = _pca(Fo, padroniza=True)[idx]
    return out


def equalizado(log=print, alvos=None) -> dict:
    b = base_ext(log=log)
    alvos = alvos or _alvos_com_tendencia(b)
    bl = blocos(b)
    el, g = b["el"], b["dist"][b["el"]]
    rng = np.random.default_rng(0)
    nulos = [rng.normal(size=(len(el), K_BLOCO)) for _ in range(2)]
    combos = {"r1+od_fluxos": ("r1", "od_fluxos"), "r1+b2000+posicao": ("r1", "b2000", "posicao"),
              "od_fluxos+b2000+posicao": ("od_fluxos", "b2000", "posicao"),
              "todos": tuple(bl)}
    out = {}
    for col in alvos:
        y = V._alvo(b, col)

        def r2_de(X):
            p = np.zeros(len(y))
            p[el] = V.lgb_cv(X[el], y[el], g)
            return V.r2(y[el], p[el])

        r0 = r2_de(b["Xown"])
        gan = {k: r2_de(np.column_stack([b["Xown"], v])) - r0 for k, v in bl.items()}
        nul = [r2_de(np.column_stack([b["Xown"], z])) - r0 for z in nulos]
        com = {n: r2_de(np.column_stack([b["Xown"]] + [bl[k] for k in ks])) - r0 for n, ks in combos.items()}
        out[col] = {"r2_proprio": r0, "ganho": gan, "ganho_nulo": nul, "combos": com}
        log(f"  equalizado {col}: R² próprio {r0:.3f}; ganhos " + ", ".join(f"{k} {v:+.3f}" for k, v in gan.items())
            + f"; nulo {np.mean(nul):+.3f}; combos " + ", ".join(f"{k} {v:+.3f}" for k, v in com.items()))
    _salva("equalizado", out)
    return out


# --- tendência mensal ---------------------------------------------------------------------------

def _ajusta_tendencia(Y: np.ndarray, Mm: np.ndarray, tc: np.ndarray, ridge_b: float = 4.0, ridge_a: float = 0.01,
                      n_iter: int = 30) -> np.ndarray:
    """Poisson log-linear por setor: μ_t = M_t·exp(a + b·t), com ridge pequeno em a e maior em b (b em log/ano)."""
    n = Y.shape[0]
    a, bb = np.zeros(n), np.zeros(n)
    for _ in range(n_iter):
        mu = Mm * np.exp(np.clip(a[:, None] + bb[:, None] * tc[None], -20, 20))
        r = Y - mu
        ga, gb = r.sum(1) - ridge_a * a, (r * tc).sum(1) - ridge_b * bb
        haa, hab, hbb = mu.sum(1) + ridge_a, (mu * tc).sum(1), (mu * tc ** 2).sum(1) + ridge_b
        det = haa * hbb - hab ** 2
        a += (hbb * ga - hab * gb) / det
        bb += (-hab * ga + haa * gb) / det
    return bb


def tendencia(log=print) -> dict:
    ids, E, _ = setor_exposicao()
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(pl.col("cd_setor").cast(pl.String))
    t = t.filter((pl.col("periodo") >= "2022-01") & (pl.col("periodo") < "2026-01"))
    meses = sorted(t["periodo"].unique().to_list())
    assert len(meses) == 48, meses[:3]
    W = t.pivot(on="periodo", index="cd_setor", values="n_total").fill_null(0.0)
    Y = ids.select("cd_setor").join(W, on="cd_setor", how="left").fill_null(0.0).select(meses).to_numpy().astype(float)
    Ya = contagens(ids)
    M = E @ em_fit_multi(E, Ya)
    Mm = np.repeat(M / 12.0, 12, axis=1)
    tc = (np.arange(48) - 23.5) / 12.0
    b_all = _ajusta_tendencia(Y, Mm, tc)
    par, imp = np.arange(48) % 2 == 0, np.arange(48) % 2 == 1
    b_par = _ajusta_tendencia(Y[:, par], Mm[:, par], tc[par])
    b_imp = _ajusta_tendencia(Y[:, imp], Mm[:, imp], tc[imp])
    el = M.mean(axis=1) >= MIN_ESPERADO
    r = float(np.corrcoef(b_par[el], b_imp[el])[0, 1])
    rep = {"meses": 48, "setores_elegiveis": int(el.sum()), "confiabilidade_par_impar": r, "confiabilidade_spearman_brown": 2 * r / (1 + r),
           "dp_tendencia_por_ano": float(b_all[el].std()),
           "correlacao_com_tendencia_anual": float(np.corrcoef(b_all[el], pl.read_parquet(C.out_dir() / "residuos_setor.parquet")["tendencia"].to_numpy()[el])[0, 1])}
    log(f"  tendência mensal: confiabilidade par × ímpar r = {r:.2f} (Spearman-Brown {rep['confiabilidade_spearman_brown']:.2f}); "
        f"DP {rep['dp_tendencia_por_ano']:.3f} log/ano; corr. com a tendência anual {rep['correlacao_com_tendencia_anual']:.2f}")
    res = pl.read_parquet(C.out_dir() / "residuos_setor.parquet")
    assert (res["cd_setor"] == ids["cd_setor"]).all()
    # parte não explicada pelo tecido próprio (boosting, CV por distrito)
    b = V.base(log=log)
    p = np.zeros(len(b_all))
    p[b["el"]] = V.lgb_cv(b["Xown"][b["el"]], b_all[b["el"]], b["dist"][b["el"]])
    sem = b_all - p
    rep["r2_tecido_proprio"] = V.r2(b_all[b["el"]], p[b["el"]])
    pl.DataFrame({"cd_setor": ids["cd_setor"], "tend_mensal": b_all, "tend_mensal_sem_tecido": sem}).write_parquet(
        C.out_dir() / "residuos_tendencia.parquet")
    b = base_ext(log=log)
    # Moran e gêmeos
    sub = b["res"].filter(pl.col("elegivel"))
    w, keep = C._pesos(sub)
    sub = sub[keep]
    z = sub["tend_mensal"].to_numpy().astype(float)
    strata = np.unique(sub["cd_dist"].to_numpy(), return_inverse=True)[1] * 10 + C._dec_densidade(sub)
    rng = np.random.default_rng(1)
    nulo = np.array([C._moran_I(C._within_perm(z, strata, rng), w) for _ in range(199)])
    I = C._moran_I(z, w)
    rep["moran"] = {"I": float(I), "nulo_restrito_media": float(nulo.mean()), "p_restrito": float((1 + np.sum(nulo >= I)) / 200)}
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    zs, zr = b["res"]["tend_mensal"].to_numpy().astype(float), b["sem"]["tend_mensal_sem_tecido"].to_numpy().astype(float)
    gem = {}
    for lo, hi in ((0, 1000), (1000, 3000), (3000, 1e9)):
        m = (d >= lo) & (d < hi)
        gem[f"{int(lo)}-{int(hi) if hi < 1e8 else 'inf'}m"] = {"bruto": C._corr_sim(zs, i[m], j[m]), "sem_tecido": C._corr_sim(zr, i[m], j[m])}
    rep["gemeos"] = gem
    log(f"  tendência mensal: Moran I = {I:.3f} (nulo {nulo.mean():.3f}); gêmeos ≤1 km {gem['0-1000m']['bruto']:.2f} → "
        f"{gem['0-1000m']['sem_tecido']:.2f}; R² do tecido próprio {rep['r2_tecido_proprio']:.2f}")
    # contextos: bordas, delegacia, OD, rede
    viz = V.comp_aneis(b)
    rep["bordas"], _ = V.bordas(b, {"viz": viz}, log=log, alvos=("tend_mensal",))
    rep["borda_delegacia"] = V.borda_delegacia(b, log=log, extra={"tend_mensal": zr}, so_extra=True)
    od = pl.read_parquet(C.out_dir() / "od_setor.parquet")
    F = np.column_stack([od[c].to_numpy() for c in od.columns[1:]])[b["idx"]]
    rep["od"] = G._teste_features(b, np.where(np.isfinite(F), F, np.nanmedian(F, 0)), list(od.columns[1:]), log=log, rotulo="OD", alvos=("tend_mensal",))
    _salva("tendencia", rep)
    return rep


# --- OD: incerteza e 2017 ----------------------------------------------------------------------

COLS_OD = ["ID_DOM", "ZONA", "N_VIAG", "FE_VIA", "MUNI_D", "CO_D_X", "CO_D_Y", "ZONA_O", "MOTIVO_D", "H_CHEG", "IDADE", "SEXO",
           "RENDA_FA", "DISTANCIA"]
NOMES_OD = ["visitantes", "visitantes_por_morador", "noturno", "homens_15_29", "renda_visitantes", "renda_visitantes_menos_moradores",
            "distancia_media", "diversidade_origens"]


def _od_prepara(ano: int, b: dict) -> dict:
    import geopandas as gpd
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    from cityomics.atlas import presenca as P
    from cityomics.atlas.presenca_od2023 import read_od2017, read_od2023

    od = (read_od2023 if ano == 2023 else read_od2017)(cols=COLS_OD)
    doms = od.drop_duplicates("ID_DOM")[["ID_DOM", "ZONA"]].reset_index(drop=True)
    pos_dom = {d: k for k, d in enumerate(doms["ID_DOM"])}
    t = od[od["N_VIAG"].notna() & (od["FE_VIA"] > 0) & (od["MUNI_D"] == P.MUNI_SP) & (od["CO_D_X"] > 0) & (od["MOTIVO_D"] != 8)].copy()
    crs = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["geometry"]).crs
    x, y = Transformer.from_crs(P.OD_CRS, crs, always_xy=True).transform(t["CO_D_X"].to_numpy(float), t["CO_D_Y"].to_numpy(float))
    sxy = b["xy"]
    n = len(sxy)
    K = cKDTree(np.column_stack([x, y])).sparse_distance_matrix(cKDTree(sxy), 3 * SIGMA_OD, output_type="coo_matrix")
    zu, zi = np.unique(t["ZONA_O"].to_numpy(), return_inverse=True)
    pop = b["setor"]["pop_2022"].fill_null(0).to_numpy().astype(float)
    Ks = cKDTree(sxy).sparse_distance_matrix(cKDTree(sxy), 3 * SIGMA_OD, output_type="coo_matrix")
    pk = np.bincount(Ks.col, weights=np.exp(-Ks.data ** 2 / (2 * SIGMA_OD ** 2)) * pop[Ks.row], minlength=n)
    censo = b["setor"].select("cd_setor").join(pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet")
                                               .select("cd_setor", "renda_mediana_resp"), on="cd_setor", how="left")
    return {"K": K, "g0": np.exp(-K.data ** 2 / (2 * SIGMA_OD ** 2)), "w": t["FE_VIA"].to_numpy(float),
            "noct": t["H_CHEG"].isin(list(range(18, 24)) + list(range(0, 6))).to_numpy().astype(float),
            "jov": ((t["IDADE"] >= 15) & (t["IDADE"] <= 29) & (t["SEXO"] == 1)).to_numpy().astype(float),
            "lr": np.log(t["RENDA_FA"].clip(lower=0).to_numpy(float) + 100), "ldist": np.log1p(t["DISTANCIA"].clip(lower=0).to_numpy(float)),
            "zi": zi, "nz": len(zu), "pk": pk, "lr_mor": np.log(censo["renda_mediana_resp"].to_numpy().astype(float) + 100),
            "dom_trip": np.array([pos_dom[d] for d in t["ID_DOM"]]), "dom_zona": doms["ZONA"].to_numpy(), "n": n, "viagens": len(t)}


def _od_feats(pr: dict, wt: np.ndarray) -> np.ndarray:
    K, n = pr["K"], pr["n"]
    kw = pr["g0"] * wt[K.row]
    soma = np.bincount(K.col, weights=kw, minlength=n)

    def media(v):
        return np.bincount(K.col, weights=kw * v[K.row], minlength=n) / np.maximum(soma, 1e-9)

    Z = sp.csr_matrix((kw, (K.col, pr["zi"][K.row])), shape=(n, pr["nz"])).toarray()
    pz = V.norm_linhas(Z)
    ent = -np.sum(np.where(pz > 0, pz * np.log(np.clip(pz, 1e-12, None)), 0), axis=1)
    lr = media(pr["lr"])
    return np.column_stack([np.log1p(soma), np.log1p(soma) - np.log1p(pr["pk"]), media(pr["noct"]), media(pr["jov"]), lr,
                            lr - pr["lr_mor"], media(pr["ldist"]), ent])


def _efeitos(b: dict, F: np.ndarray, alvos) -> dict:
    """β (DP do resíduo sem tecido por DP da variável) com efeito fixo de distrito, uma variável por vez."""
    idx, el = b["idx"], b["el"]
    X = F[idx]
    ok = el & np.isfinite(X).all(axis=1)
    g = b["dist"][ok]
    Xd = V.demean((X[ok] - X[ok].mean(0)) / X[ok].std(0), g)
    out = {}
    for col in alvos:
        y = V._alvo(b, col, sem_tecido=True)[ok]
        yd = V.demean(y / y.std(), g)
        out[col] = (Xd * yd[:, None]).sum(0) / (Xd ** 2).sum(0)
    return out


def od_incerteza(log=print, n_boot: int = 200, n_r2: int = 24) -> dict:
    from scipy.stats import spearmanr

    from cityomics.atlas.presenca_od2023 import multiplicidades

    b = base_ext(log=log)
    alvos = _alvos_com_tendencia(b)
    el, g = b["el"], b["dist"][b["el"]]
    idx = b["idx"]
    pr23 = _od_prepara(2023, b)
    F23 = _od_feats(pr23, pr23["w"])
    out = {"viagens_2023": pr23["viagens"]}
    beta0 = _efeitos(b, F23, alvos)
    M = multiplicidades(pr23["dom_zona"], n_boot, seed=20261028)
    bs = {c: [] for c in alvos}
    for r in range(n_boot):
        Fb = _od_feats(pr23, pr23["w"] * M[r][pr23["dom_trip"]])
        e = _efeitos(b, Fb, alvos)
        for c in alvos:
            bs[c].append(e[c])
    out["efeitos_2023"] = {c: {n: {"beta": float(beta0[c][k]), "ic_bootstrap_od": [float(np.percentile(np.array(bs[c])[:, k], 2.5)),
                                                                             float(np.percentile(np.array(bs[c])[:, k], 97.5))]}
                               for k, n in enumerate(NOMES_OD)} for c in alvos}
    log("  OD 2023 (bootstrap de domicílios), quanto: " + ", ".join(
        f"{n} {v['beta']:+.2f} [{v['ic_bootstrap_od'][0]:+.2f},{v['ic_bootstrap_od'][1]:+.2f}]" for n, v in out["efeitos_2023"]["quanto"].items()))
    # ganho de R² (quanto) nas réplicas
    y = V._alvo(b, "quanto")

    def r2_de(F):
        p = np.zeros(len(y))
        p[el] = V.lgb_cv(np.column_stack([b["Xown"], np.where(np.isfinite(F[idx]), F[idx], 0.0)])[el], y[el], g)
        return V.r2(y[el], p[el])

    p0 = np.zeros(len(y))
    p0[el] = V.lgb_cv(b["Xown"][el], y[el], g)
    r0 = V.r2(y[el], p0[el])
    r_ref = r2_de(F23)
    reps = [r2_de(_od_feats(pr23, pr23["w"] * M[r][pr23["dom_trip"]])) for r in range(n_r2)]
    out["r2_quanto"] = {"proprio": r0, "com_od_2023": r_ref, "ganho_bootstrap_ic": [float(np.percentile(reps, 2.5) - r0), float(np.percentile(reps, 97.5) - r0)],
                        "ganho_media_bootstrap": float(np.mean(reps) - r0)}
    log(f"  OD: R² quanto {r0:.3f} → {r_ref:.3f}; ganho nas réplicas {out['r2_quanto']['ganho_bootstrap_ic']}")
    # OD 2017 e as duas juntas
    pr17 = _od_prepara(2017, b)
    F17 = _od_feats(pr17, pr17["w"])
    b17 = _efeitos(b, F17, alvos)
    rho = [float(spearmanr(F23[idx][el, k], F17[idx][el, k]).statistic) for k in range(len(NOMES_OD))]
    out["od_2017"] = {"viagens": pr17["viagens"], "efeitos": {c: {n: float(b17[c][k]) for k, n in enumerate(NOMES_OD)} for c in alvos},
                      "correlacao_setores_2017_2023": dict(zip(NOMES_OD, rho)),
                      "r2_quanto_com_2017": r2_de(F17), "r2_quanto_com_ambas": r2_de(np.column_stack([F23, F17]))}
    log(f"  OD 2017: R² quanto {out['od_2017']['r2_quanto_com_2017']:.3f}; ambas {out['od_2017']['r2_quanto_com_ambas']:.3f}; "
        f"efeitos 2017 quanto " + ", ".join(f"{n} {v:+.2f}" for n, v in out["od_2017"]["efeitos"]["quanto"].items()))
    _salva("od_incerteza", out)
    return out


# --- interação tipo × fluxo --------------------------------------------------------------------

def od_interacao(log=print, min_setores: int = 300) -> dict:
    from scipy.stats import chi2

    b = base_ext(log=log)
    el, idx = b["el"], b["idx"]
    od = pl.read_parquet(C.out_dir() / "od_setor.parquet")
    dom = b["setor"].select("cd_setor").join(pl.read_parquet(atlas_dir() / f"setor_dominio_{REF_YEAR}.parquet"), on="cd_setor", how="left")
    nomes_dom = dom["dominio_nome"].fill_null("?").to_numpy()[idx]
    dominante = np.array(b["names"])[np.argmax(b["P"], axis=1)][idx]
    out = {}
    for fx in ("diversidade_origens", "visitantes_por_morador", "visitantes"):
        f = od[fx].to_numpy().astype(float)[idx]
        for col in ("quanto", "hora_noturna", "fen_div"):
            y = V._alvo(b, col, sem_tecido=True)
            o = {}
            for nome_grupo, lab in (("dominio", nomes_dom), ("tipo_dominante", dominante)):
                grupos = {}
                for k in np.unique(lab[el]):
                    m = el & (lab == k) & np.isfinite(f)
                    if m.sum() < min_setores or len(np.unique(b["dist"][m])) < 8:
                        continue
                    xz, yz = (f[m] - f[m].mean()) / f[m].std(), y[m] / y[m].std()
                    be, ci = V.coef_fe(yz, xz[:, None], b["dist"][m], n_boot=100)
                    grupos[str(k)] = {"beta": float(be[0]), "ic": [float(ci[0, 0]), float(ci[1, 0])], "setores": int(m.sum())}
                be_ = np.array([v["beta"] for v in grupos.values()])
                se_ = np.array([(v["ic"][1] - v["ic"][0]) / 3.92 for v in grupos.values()])
                w_ = 1 / np.maximum(se_ ** 2, 1e-9)
                bm = float((w_ * be_).sum() / w_.sum())
                Q = float((w_ * (be_ - bm) ** 2).sum())
                o[nome_grupo] = {"grupos": grupos, "beta_ponderado": bm, "Q": Q, "gl": len(grupos) - 1,
                                 "p_heterogeneidade": float(1 - chi2.cdf(Q, max(len(grupos) - 1, 1)))}
            out[f"{fx}|{col}"] = o
            log(f"  interação {fx} → {col}: por domínio Q = {o['dominio']['Q']:.1f} (p = {o['dominio']['p_heterogeneidade']:.3f}); "
                f"por tipo dominante Q = {o['tipo_dominante']['Q']:.1f} (p = {o['tipo_dominante']['p_heterogeneidade']:.3f}); "
                f"β por domínio " + ", ".join(f"{v['beta']:+.2f}" for v in o["dominio"]["grupos"].values()))
    _salva("od_interacao", out)
    return out


# --- MGWR -------------------------------------------------------------------------------------

def mgwr(log=print, n_amostra: int = 2500, seed: int = 0, bw_min: int = 150, tentar_mgwr: bool = True) -> dict:
    """As taxas por classe variam no espaço? GWR e MGWR com banda mínima, avaliados por validação por distrito.

    O ajuste dentro da amostra com bandas pequenas superajusta (R² de 0,78 com 60 vizinhos), então a comparação
    que vale é a previsão fora da amostra: GWR treinado em quatro quintos dos distritos prevê o quinto restante
    contra o OLS global. O MGWR é descritivo; se os coeficientes explodirem (|β| > 50) ele é marcado como inválido."""
    from mgwr.gwr import GWR, MGWR
    from mgwr.sel_bw import Sel_BW
    from sklearn.model_selection import GroupKFold

    b = base_ext(log=log)
    ids, E, names = setor_exposicao()
    Y = contagens(ids)
    lam = em_fit_multi(E, Y).mean(axis=1)
    top = np.argsort(-(lam * E.sum(axis=0)))[:5]
    el = np.where(b["el"])[0]
    rng = np.random.default_rng(seed)
    amostra = np.sort(rng.choice(el, min(n_amostra, len(el)), replace=False))
    xy = b["xy"][b["idx"]][amostra]
    ym = Y.mean(axis=1)
    y = np.minimum(ym[amostra], np.percentile(ym[el], 99))
    X = E[amostra][:, top]
    yz = ((y - y.mean()) / y.std())[:, None]
    Xz = (X - X.mean(0)) / X.std(0)
    dist = b["dist"][amostra]
    cls = [names[k] for k in top]
    nomes = ["intercepto"] + cls
    out = {"n": int(len(amostra)), "classes": cls, "banda_minima": bw_min}
    log(f"  GWR: {len(amostra)} setores, classes {cls}")
    A = np.column_stack([np.ones(len(yz)), Xz])
    ols = np.linalg.lstsq(A, yz, rcond=None)[0].ravel()
    out["ols"] = {"beta": dict(zip(nomes, map(float, ols))), "r2_dentro": float(1 - ((yz.ravel() - A @ ols) ** 2).mean() / yz.var())}
    # validação por distrito: GWR (banda escolhida no treino) contra OLS global
    pred_g, pred_o = np.zeros(len(yz)), np.zeros(len(yz))
    bws = []
    for tr, te in GroupKFold(5).split(xy, groups=dist):
        sel = Sel_BW(xy[tr], yz[tr], Xz[tr], multi=False, kernel="bisquare", fixed=False)
        bw = float(sel.search(bw_min=bw_min, bw_max=len(tr)))
        bws.append(bw)
        m = GWR(xy[tr], yz[tr], Xz[tr], bw, kernel="bisquare", fixed=False)
        pr = m.predict(xy[te], Xz[te]).predictions
        pred_g[te] = np.asarray(pr).ravel()
        o = np.linalg.lstsq(A[tr], yz[tr], rcond=None)[0].ravel()
        pred_o[te] = A[te] @ o
    r2g, r2o = V.r2(yz.ravel(), pred_g), V.r2(yz.ravel(), pred_o)
    out["validacao_por_distrito"] = {"r2_gwr": r2g, "r2_ols": r2o, "ganho": r2g - r2o, "bandas_por_dobra": bws}
    log(f"  GWR por distrito: R² fora da amostra {r2g:.3f} contra OLS {r2o:.3f} (bandas {bws})")
    # coeficientes locais (ajuste na amostra toda, só descritivo)
    sel = Sel_BW(xy, yz, Xz, multi=False, kernel="bisquare", fixed=False)
    bw1 = float(sel.search(bw_min=bw_min, bw_max=len(yz)))
    r1 = GWR(xy, yz, Xz, bw1, kernel="bisquare", fixed=False).fit()
    pg = r1.params
    out["gwr"] = {"bw_vizinhos": bw1, "aicc": float(r1.aicc), "r2_dentro": float(r1.R2),
                  "coef": {nm: {"media": float(pg[:, j].mean()), "dp": float(pg[:, j].std()), "q10": float(np.percentile(pg[:, j], 10)),
                                "q90": float(np.percentile(pg[:, j], 90)),
                                "parte_sinal_oposto_ao_global": float(np.mean(np.sign(pg[:, j]) != np.sign(ols[j])))}
                           for j, nm in enumerate(nomes)}}
    log(f"  GWR: banda {bw1:.0f}, AICc {r1.aicc:.0f}, R² dentro {r1.R2:.2f}")
    if tentar_mgwr:
        selm = Sel_BW(xy, yz, Xz, multi=True, kernel="bisquare", fixed=False)
        bwm = np.atleast_1d(selm.search(multi_bw_min=[bw_min], multi_bw_max=[len(yz)]))
        rm = MGWR(xy, yz, Xz, selm, kernel="bisquare", fixed=False).fit()
        pm = rm.params
        valido = bool(np.abs(pm).max() < 50 and np.isfinite(rm.R2) and rm.R2 > -1)
        out["mgwr"] = {"valido": valido, "aicc": float(rm.aicc), "r2_dentro": float(rm.R2), "max_abs_coef": float(np.abs(pm).max()),
                       "bandas_vizinhos": dict(zip(nomes, map(float, bwm)))}
        if valido:
            out["mgwr"]["coef"] = {nm: {"media": float(pm[:, j].mean()), "dp": float(pm[:, j].std()),
                                        "parte_sinal_oposto_ao_global": float(np.mean(np.sign(pm[:, j]) != np.sign(ols[j])))}
                                   for j, nm in enumerate(nomes)}
        log(f"  MGWR: válido={valido}; AICc {rm.aicc:.0f}, R² dentro {rm.R2:.2f}; bandas " + ", ".join(f"{n} {v:.0f}" for n, v in out["mgwr"]["bandas_vizinhos"].items()))
    _salva("mgwr", out)
    return out


# --- GNN com sementes --------------------------------------------------------------------------

def gnn_sementes(log=print, seeds=(0, 1, 2, 3, 4)) -> dict:
    b = base_ext(log=log)
    alvos = _alvos_com_tendencia(b)
    cfg = [("rainha", 0), ("rainha", 1), ("rainha", 2), ("knn8", 2), ("rede800", 1)]
    rep = G.gnn(b, seeds=seeds, log=log, alvos=alvos, configs=cfg, salva=False)
    _salva("gnn_sementes", {"sementes": list(seeds), **rep})
    return rep


# --- figura do passo 3 -------------------------------------------------------------------------

def figura(log=print) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cityomics.paths import REPO_ROOT

    d = json.loads((C.out_dir() / "extra.json").read_text())
    pasta = REPO_ROOT / "figures" / "out" / "exploratorio" / "contexto"
    pasta.mkdir(parents=True, exist_ok=True)
    nomes = {"quanto": "Quanto", "quanto_dist": "Quanto, sem distrito", "fen_div": "Que crime", "hora_noturna": "A que hora",
             "tend_mensal": "Tendência mensal"}
    fig, ax = plt.subplots(2, 2, figsize=(14, 9.5))
    a = ax[0, 0]
    eq = d["equalizado"]
    blocos_ = list(eq["quanto"]["ganho"])
    x = np.arange(len(blocos_))
    for k, col in enumerate(("quanto", "fen_div", "hora_noturna", "tend_mensal")):
        a.bar(x + (k - 1.5) * 0.2, [eq[col]["ganho"][bk] for bk in blocos_], width=0.2, label=nomes[col], color=f"C{[0, 2, 3, 4][k]}")
    a.axhline(np.mean(eq["quanto"]["ganho_nulo"]), c="grey", ls="--", lw=0.8, label="Bloco de ruído (8 dim.)")
    a.set_xticks(x, [bk.replace("_", " ") for bk in blocos_], rotation=40, ha="right", fontsize=8)
    a.set_ylabel("Ganho de R² sobre o tecido próprio (8 dim. por bloco)")
    a.set_title("a  Contextos com o mesmo número de variáveis", loc="left")
    a.legend(fontsize=8, frameon=False)
    a = ax[0, 1]
    od = d["od_incerteza"]
    nm = list(od["efeitos_2023"]["quanto"])
    y = np.arange(len(nm))
    be = np.array([od["efeitos_2023"]["quanto"][n]["beta"] for n in nm])
    lo = np.array([od["efeitos_2023"]["quanto"][n]["ic_bootstrap_od"][0] for n in nm])
    hi = np.array([od["efeitos_2023"]["quanto"][n]["ic_bootstrap_od"][1] for n in nm])
    a.errorbar(be, y, xerr=[np.maximum(be - lo, 0), np.maximum(hi - be, 0)], fmt="o", ms=4, label="OD 2023 (IC do bootstrap de domicílios)")
    a.plot([od["od_2017"]["efeitos"]["quanto"][n] for n in nm], y, "D", ms=4, c="C1", label="OD 2017")
    a.set_yticks(y, [n.replace("_", " ") for n in nm], fontsize=8)
    a.axvline(0, c="k", lw=0.5)
    a.set_xlabel("Efeito sobre o resíduo de quanto (DP por DP, dentro do distrito)")
    a.set_title("b  Fluxos OD: 2023 com incerteza e 2017", loc="left")
    a.legend(fontsize=8, frameon=False, loc="center right")
    a = ax[1, 0]
    gr = d["od_interacao"]["diversidade_origens|quanto"]["dominio"]["grupos"]
    ks = list(gr)
    y = np.arange(len(ks))
    be = np.array([gr[k]["beta"] for k in ks])
    lo = np.array([gr[k]["ic"][0] for k in ks])
    hi = np.array([gr[k]["ic"][1] for k in ks])
    a.errorbar(be, y, xerr=[be - lo, hi - be], fmt="o", ms=4)
    a.set_yticks(y, [k.replace(" + ", "\n+ ") for k in ks], fontsize=7)
    a.axvline(0, c="k", lw=0.5)
    pq = d["od_interacao"]["diversidade_origens|quanto"]["dominio"]["p_heterogeneidade"]
    a.set_xlabel(f"Efeito da diversidade de origens por domínio (heterogeneidade p = {pq:.2f})")
    a.set_title("c  O efeito dos fluxos muda com o tipo de tecido?", loc="left")
    a = ax[1, 1]
    gs = d["gnn_sementes"]["r2"]
    cfg = [c for c in gs if not c.endswith("_dp")]
    x = np.arange(len(cfg))
    for k, col in enumerate(("quanto", "quanto_dist", "fen_div", "hora_noturna")):
        a.errorbar(x, [gs[c][col] for c in cfg], yerr=[gs[f"{c}_dp"][col] for c in cfg], marker="o", ms=4, capsize=2, label=nomes[col])
    a.set_xticks(x, cfg, rotation=30, fontsize=8)
    a.set_ylabel("R² fora da amostra (média ± DP de 5 sementes)")
    a.set_title("d  GNN com cinco sementes", loc="left")
    a.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(pasta / "contexto_passo3.png", dpi=200)
    plt.close(fig)
    log(f"figura: {pasta / 'contexto_passo3.png'}")
