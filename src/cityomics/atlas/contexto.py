"""Contexto espacial do estado além do tipo: gêmeos de tecido (exploratório, fora do artigo).

O artigo deixa 46% da variância entre setores num componente persistente "além do tipo"
(``memoria``). Aqui se pergunta se o entorno explica por que dois setores de tecido igual divergem.
Passo 1 do plano (Etapa 0 + A + H):

- **Resíduos do tecido por setor**, em quatro desfechos:
  - *quanto*: log da razão observado/esperado do celular 2022–2025, encolhida por gama-Poisson
    (e a mesma razão com o efeito de distrito de ``robustez.em_distrito``);
  - *que crime*: desvio da mistura dos 15 fenótipos contra a mistura esperada pela composição;
  - *a que hora*: desvio da mistura por período do dia (celular e roubo-outros), e a razão noturna;
  - *tendência*: inclinação anual do resíduo de celular 2022→2025.
  As misturas são encolhidas com uma pseudocontagem na direção da mistura esperada.
- **Gêmeos de tecido**: vizinhos mais próximos na distância de Hellinger da exposição, com calibre de
  tamanho (exposição total) e de densidade. A correlação do resíduo entre gêmeos, pela distância
  geográfica do par, separa "o lugar" (sem estrutura) de "o entorno" (gêmeos próximos parecidos).
- **Geografia do resíduo**: Moran global (permutação livre e restrita a distrito × decil de
  densidade), LISA e correlograma por faixa de distância.
- **Controles**: geocodificação (``n_geo`` × ``n_total``), delegacia da área (``dp_fato``) contra
  distrito, e placebo com o resíduo permutado dentro de distrito × decil.

Só distritos de exploração (D53) e nada de 2026. Saídas locais em ``data/processed/atlas/contexto/``
(tabelas por setor não saem do computador, D49/D60).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.communication import _within_perm, density_deciles
from cityomics.atlas.fenotipo import EVENTOS, YEARS, matriz, out_dir as fenotipo_dir, periodo_do_dia, setor_exposicao, PERIODOS
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.memoria import MIN_ESPERADO, contagens, decompoe
from cityomics.atlas.niches import queen_neighbors
from cityomics.atlas.robustez import _celular_ano, em_distrito
from cityomics.paths import interim_dir, processed_dir

PSEUDO = 10.0                          # pseudocontagem do encolhimento das misturas
RELOGIO = ("celular_roubo", "celular_furto", "roubo_outros")
BANDAS = (0, 250, 500, 1000, 1500, 2000, 3000, 5000, 7500, 10000, 15000, 20000)
N_GEMEOS = 3                           # gêmeos por setor
CALIBRE_TAMANHO = np.log(1.5)          # |Δ log exposição total| máximo dentro do par
DESFECHOS = ("quanto", "quanto_dist", "fen_div", "hora_noturna", "tendencia")


def out_dir():
    d = atlas_dir() / "contexto"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- Etapa 0: resíduos do tecido ----------------------------------------------------------------

def razao_encolhida(Y: np.ndarray, M: np.ndarray) -> tuple[np.ndarray, dict]:
    """log E[razão | Y] com priori gama na razão Y/M (média e variância além do Poisson pelos momentos)."""
    ok = M >= MIN_ESPERADO
    r = Y[ok] / M[ok]
    m = float(np.average(r, weights=M[ok]))
    s2 = float(max(np.average((r - m) ** 2 - m / M[ok], weights=M[ok]), 1e-6))
    a, b = m * m / s2, m / s2
    return np.log((Y + a) / (M + b)) - np.log(m), {"media": m, "var_extra": s2, "a": a, "b": b}


def mistura(Y: np.ndarray, M: np.ndarray, c: float = PSEUDO) -> np.ndarray:
    """log(participação observada encolhida / participação esperada), setor × categoria."""
    p = M / np.clip(M.sum(axis=1, keepdims=True), 1e-12, None)
    p = np.clip(p, 1e-6, None)
    p = p / p.sum(axis=1, keepdims=True)
    post = (Y + c * p) / (Y.sum(axis=1, keepdims=True) + c)
    return np.log(post) - np.log(p)


def _horas(ids: pl.DataFrame) -> np.ndarray:
    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "periodo", "cd_setor"])
    ev = ev[ev["desfecho"].isin(RELOGIO) & ev["data_fato"].dt.year.isin(list(YEARS)) & ev["cd_setor"].notna()].copy()
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    i = ev["cd_setor"].astype(str).map(pos)
    per = periodo_do_dia(ev).map({p: k for k, p in enumerate(PERIODOS)})
    ok = i.notna() & per.notna()
    idx = i[ok].astype(int).to_numpy() * len(PERIODOS) + per[ok].astype(int).to_numpy()
    return np.bincount(idx, minlength=ids.height * len(PERIODOS)).reshape(ids.height, len(PERIODOS)).astype(float)


def _dp_modal(ids: pl.DataFrame) -> np.ndarray:
    ev = pl.scan_parquet(interim_dir() / EVENTOS).select("cd_setor", "dp_fato", "data_fato").filter(
        pl.col("cd_setor").is_not_null() & pl.col("dp_fato").is_not_null() & (pl.col("data_fato").dt.year() <= 2025)).collect()
    m = (ev.group_by("cd_setor", "dp_fato").len().sort("len", descending=True).group_by("cd_setor").first()
         .select(pl.col("cd_setor").cast(pl.String), "dp_fato"))
    return ids.select("cd_setor").join(m, on="cd_setor", how="left")["dp_fato"].fill_null("?").to_numpy()


def _centroides(ids: pl.DataFrame) -> np.ndarray:
    import geopandas as gpd

    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    c = g.geometry.centroid
    xy = pl.DataFrame({"cd_setor": g["cd_setor"].astype(str).to_numpy(), "x": c.x.to_numpy(), "y": c.y.to_numpy()})
    return ids.select("cd_setor").join(xy, on="cd_setor", how="left").select("x", "y").to_numpy()


def residuos(log=print) -> tuple[pl.DataFrame, np.ndarray, dict]:
    ids, E, names = setor_exposicao()
    dist = ids["cd_dist"].to_numpy()
    rep = {}
    # quanto
    Y = contagens(ids)
    M = E @ em_fit_multi(E, Y)
    keep = M.mean(axis=1) >= MIN_ESPERADO
    d = decompoe(Y[keep], M[keep])
    rep["replica_memoria"] = {k: round(v, 3) for k, v in d["partes"].items()} | {"setores": int(keep.sum())}
    quanto, pri = razao_encolhida(Y.sum(axis=1), M.sum(axis=1))
    rep["priori_quanto"] = pri
    lamd, theta = em_distrito(E, Y, dist)
    _, g = np.unique(dist, return_inverse=True)
    Md = (E * theta[g][:, None]) @ lamd
    quanto_dist, _ = razao_encolhida(Y.sum(axis=1), Md.sum(axis=1))
    # tendência: inclinação do log-resíduo anual encolhido
    t = np.arange(len(YEARS)) - (len(YEARS) - 1) / 2
    Ra = np.column_stack([razao_encolhida(Y[:, k], M[:, k])[0] for k in range(len(YEARS))])
    tend = Ra @ t / (t @ t)
    # geocodificação
    Yg = _celular_ano(ids, "n_geo")
    Mg = E @ em_fit_multi(E, Yg)
    quanto_geo, _ = razao_encolhida(Yg.sum(axis=1), Mg.sum(axis=1))
    geo_frac = Yg.sum(axis=1) / np.clip(Y.sum(axis=1), 1e-9, None)
    # que crime
    tab = pl.read_parquet(fenotipo_dir() / "fenotipo_setor_ano.parquet")
    Yf, fen = matriz(ids, tab, YEARS)
    Mf = E @ em_fit_multi(E, Yf)
    Rf = mistura(Yf, Mf)
    pf = Mf / np.clip(Mf.sum(axis=1, keepdims=True), 1e-12, None)
    fen_div = np.sqrt(np.sum(pf * Rf ** 2, axis=1))          # afastamento ponderado da mistura esperada
    # a que hora
    Yh = _horas(ids)
    Mh = E @ em_fit_multi(E, Yh)
    Rh = mistura(Yh, Mh)
    noct = [PERIODOS.index("madrugada"), PERIODOS.index("noite")]
    dia = [k for k in range(len(PERIODOS)) if k not in noct]
    R2 = mistura(np.column_stack([Yh[:, noct].sum(1), Yh[:, dia].sum(1)]), np.column_stack([Mh[:, noct].sum(1), Mh[:, dia].sum(1)]))
    hora_noturna = R2[:, 0] - R2[:, 1]                        # log da razão de chances noturna, obs/esperada
    cols = {"cd_setor": ids["cd_setor"], "cd_dist": ids["cd_dist"], "elegivel": keep,
            "esperado_ano": M.mean(axis=1), "observado_ano": Y.mean(axis=1), "quanto": quanto, "quanto_dist": quanto_dist,
            "quanto_geo": quanto_geo, "geo_frac": geo_frac, "tendencia": tend, "fen_div": fen_div, "hora_noturna": hora_noturna,
            "eventos_fen": Yf.sum(axis=1), "eventos_hora": Yh.sum(axis=1)}
    cols |= {f"fen|{f}": Rf[:, j] for j, f in enumerate(fen)}
    cols |= {f"hora|{p}": Rh[:, k] for k, p in enumerate(PERIODOS)}
    res = pl.DataFrame(cols).with_columns(pl.Series("dp", _dp_modal(ids)))
    res.write_parquet(out_dir() / "residuos_setor.parquet")
    rep["n_setores"] = int(ids.height)
    log(f"resíduos: {ids.height:,} setores ({keep.sum():,} elegíveis); réplica da memória {rep['replica_memoria']}")
    return res, E, rep


# --- Etapa 0: gêmeos de tecido -------------------------------------------------------------------

def gemeos(res: pl.DataFrame, E: np.ndarray, xy: np.ndarray, k: int = N_GEMEOS, log=print) -> tuple[pl.DataFrame, dict]:
    from sklearn.neighbors import NearestNeighbors

    el = np.where(res["elegivel"].to_numpy())[0]
    S = np.sqrt(E[el] / np.clip(E[el].sum(axis=1, keepdims=True), 1e-12, None))
    tam = np.log(E[el].sum(axis=1))
    dec = _dec_densidade(res)[el]
    nn = NearestNeighbors(n_neighbors=40).fit(S)
    dd, jj = nn.kneighbors(S)
    rows = []
    for a in range(len(el)):
        n = 0
        for d, b in zip(dd[a, 1:], jj[a, 1:]):
            if abs(tam[a] - tam[b]) <= CALIBRE_TAMANHO and abs(int(dec[a]) - int(dec[b])) <= 1:
                rows.append((min(el[a], el[b]), max(el[a], el[b]), d / np.sqrt(2)))
                n += 1
                if n == k:
                    break
    p = pl.DataFrame(rows, schema=["i", "j", "hellinger"], orient="row").unique(["i", "j"])
    i, j = p["i"].to_numpy(), p["j"].to_numpy()
    dist_m = np.hypot(*(xy[i] - xy[j]).T)
    dd_ = res["cd_dist"].to_numpy()
    viz = queen_neighbors()
    par = set(zip(viz["cd_setor"].to_list(), viz["vizinho"].to_list()))
    cs = res["cd_setor"].to_numpy()
    p = p.with_columns(pl.Series("dist_m", dist_m), pl.Series("mesmo_distrito", dd_[i] == dd_[j]),
                       pl.Series("contiguos", [(a, b) in par for a, b in zip(cs[i], cs[j])]),
                       pl.Series("cd_setor_i", cs[i]), pl.Series("cd_setor_j", cs[j]))
    # balanço: Hellinger dos gêmeos contra pares ao acaso entre elegíveis
    rng = np.random.default_rng(0)
    a, b = rng.integers(0, len(el), 20000), rng.integers(0, len(el), 20000)
    h_rand = np.linalg.norm(S[a] - S[b], axis=1) / np.sqrt(2)
    bal = {"pares": p.height, "hellinger_mediana": float(np.median(p["hellinger"])), "hellinger_mediana_acaso": float(np.median(h_rand)),
           "dist_mediana_m": float(np.median(dist_m)), "mesmo_distrito": float(p["mesmo_distrito"].mean()),
           "contiguos": float(p["contiguos"].mean())}
    p.write_parquet(out_dir() / "gemeos.parquet")
    log(f"gêmeos: {p.height:,} pares; Hellinger mediana {bal['hellinger_mediana']:.2f} (ao acaso {bal['hellinger_mediana_acaso']:.2f}); "
        f"distância mediana {bal['dist_mediana_m'] / 1000:.1f} km; {bal['mesmo_distrito']:.0%} no mesmo distrito")
    return p, bal


def _dec_densidade(res: pl.DataFrame) -> np.ndarray:
    s = pl.read_parquet(atlas_dir() / f"setor_composicao_{REF_YEAR}.parquet").select("cd_setor", "pop_2022", "area_km2")
    return density_deciles(res.select("cd_setor").join(s, on="cd_setor", how="left").fill_null(0))


def _corr_sim(z: np.ndarray, i: np.ndarray, j: np.ndarray) -> float:
    """Correlação simétrica (intraclasse) entre os membros dos pares."""
    a, b = np.concatenate([z[i], z[j]]), np.concatenate([z[j], z[i]])
    return float(np.corrcoef(a, b)[0, 1])


def correlacao_gemeos(res: pl.DataFrame, pares: pl.DataFrame, bandas=(0, 1000, 3000, 10000, 1e9)) -> dict:
    i, j, d = pares["i"].to_numpy(), pares["j"].to_numpy(), pares["dist_m"].to_numpy()
    out = {}
    for col in DESFECHOS:
        z = res[col].to_numpy()
        o = {"todos": _corr_sim(z, i, j)}
        for lo, hi in zip(bandas[:-1], bandas[1:]):
            m = (d >= lo) & (d < hi)
            o[f"{int(lo)}-{int(hi) if hi < 1e8 else 'inf'}m"] = {"r": _corr_sim(z, i[m], j[m]), "pares": int(m.sum())}
        for nome, m in (("mesmo_distrito", pares["mesmo_distrito"].to_numpy()), ("outro_distrito", ~pares["mesmo_distrito"].to_numpy()),
                        ("contiguos", pares["contiguos"].to_numpy())):
            o[nome] = {"r": _corr_sim(z, i[m], j[m]), "pares": int(m.sum())}
        out[col] = o
    return out


def tecido_nao_linear(res: pl.DataFrame, E: np.ndarray, pares: pl.DataFrame, log=print) -> tuple[dict, pl.DataFrame]:
    """Quanto do resíduo o próprio tecido explica fora do modelo aditivo (boosting na composição, CV por
    distrito), e a correlação entre gêmeos depois de tirar essa parte. Gêmeos distantes que continuam
    parecidos indicam tecido mal modelado, não entorno."""
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import GroupKFold, cross_val_predict

    S = np.sqrt(E / np.clip(E.sum(axis=1, keepdims=True), 1e-12, None))
    X = np.column_stack([S, np.log(E.sum(axis=1) + 1e-9), _dec_densidade(res)])
    el, g = res["elegivel"].to_numpy(), res["cd_dist"].to_numpy()
    i, j, d = pares["i"].to_numpy(), pares["j"].to_numpy(), pares["dist_m"].to_numpy()
    out, cols = {}, {}
    for col in DESFECHOS:
        z = res[col].to_numpy().astype(float)
        p = np.zeros_like(z)
        p[el] = cross_val_predict(HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, min_samples_leaf=50, random_state=0),
                                  X[el], z[el], groups=g[el], cv=GroupKFold(5))
        zr = z - p
        cols[f"{col}_sem_tecido"] = zr
        o = {"r2_tecido_proprio": float(1 - np.var(zr[el]) / np.var(z[el]))}
        for lo, hi in ((0, 1000), (1000, 3000), (3000, 10000), (10000, 1e9)):
            m = (d >= lo) & (d < hi)
            o[f"gemeos_{int(lo)}-{int(hi) if hi < 1e8 else 'inf'}m"] = _corr_sim(zr, i[m], j[m])
        out[col] = o
        log(f"  tecido não linear {col}: R² {o['r2_tecido_proprio']:.2f}; gêmeos depois: "
            f"{[round(v, 2) for k, v in o.items() if k.startswith('gemeos')]}")
    return out, pl.DataFrame(cols)


# --- A: geografia do resíduo --------------------------------------------------------------------

def _pesos(res: pl.DataFrame):
    from libpysal.weights import W

    cs = res["cd_setor"].to_list()
    idx = {c: k for k, c in enumerate(cs)}
    viz = queen_neighbors().filter(pl.col("cd_setor").is_in(cs) & pl.col("vizinho").is_in(cs))
    nb = {k: [] for k in range(len(cs))}
    for a, b in zip(viz["cd_setor"].to_list(), viz["vizinho"].to_list()):
        nb[idx[a]].append(idx[b])
    ilha = np.array([len(nb[k]) == 0 for k in range(len(cs))])
    keep = np.where(~ilha)[0]
    re = {o: n for n, o in enumerate(keep)}
    w = W({re[k]: [re[x] for x in nb[k]] for k in keep}, silence_warnings=True)
    w.transform = "r"
    return w, keep


def _moran_I(z: np.ndarray, w) -> float:
    z = z - z.mean()
    return float(z @ (w.sparse @ z) / (z @ z))


def moran(res: pl.DataFrame, n_perm: int = 199, log=print) -> tuple[dict, pl.DataFrame]:
    from esda.moran import Moran, Moran_Local

    sub = res.filter(pl.col("elegivel"))
    w, keep = _pesos(sub)
    sub = sub[keep]
    strata = np.unique(sub["cd_dist"].to_numpy(), return_inverse=True)[1] * 10 + _dec_densidade(sub)
    rng = np.random.default_rng(1)
    out, lisa = {}, {"cd_setor": sub["cd_setor"]}
    for col in DESFECHOS:
        z = sub[col].to_numpy().astype(float)
        mi = Moran(z, w, permutations=999)
        restr = np.array([_moran_I(_within_perm(z, strata, rng), w) for _ in range(n_perm)])
        # quanto do I se explica por diferenças entre distritos: I do resíduo centrado no distrito
        g = np.unique(sub["cd_dist"].to_numpy(), return_inverse=True)[1]
        zc = z - (np.bincount(g, weights=z) / np.bincount(g))[g]
        out[col] = {"I": float(mi.I), "p_livre": float(mi.p_sim), "I_nulo_restrito_media": float(restr.mean()),
                    "p_restrito": float((1 + np.sum(restr >= mi.I)) / (1 + n_perm)), "I_dentro_distrito": _moran_I(zc, w),
                    "eta2_distrito": float(1 - np.var(zc) / np.var(z))}
        if col in ("quanto", "quanto_dist", "hora_noturna"):
            ml = Moran_Local(z, w, permutations=999, seed=0)
            sig = ml.p_sim < 0.05
            lisa[f"q|{col}"] = np.where(sig, ml.q, 0)
            out[col]["lisa"] = {nm: float(np.mean(sig & (ml.q == q))) for q, nm in ((1, "HH"), (2, "LH"), (3, "LL"), (4, "HL"))}
        log(f"  Moran {col}: I = {mi.I:.3f} (nulo restrito {restr.mean():.3f}); dentro do distrito {out[col]['I_dentro_distrito']:.3f}; "
            f"eta² distrito {out[col]['eta2_distrito']:.2f}")
    return out, pl.DataFrame(lisa)


def correlograma(res: pl.DataFrame, xy: np.ndarray, cols=DESFECHOS, n_sub: int = 6000, reps: int = 3, permutar=None,
                 seed: int = 0) -> pl.DataFrame:
    """Correlação de Moran por faixa de distância (pares de uma subamostra de setores elegíveis)."""
    from scipy.spatial.distance import pdist

    el = np.where(res["elegivel"].to_numpy())[0]
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(reps):
        s = rng.choice(el, size=min(n_sub, len(el)), replace=False)
        d = pdist(xy[s])
        b = np.digitize(d, BANDAS) - 1
        iu = np.triu_indices(len(s), 1)
        for col in cols:
            z = res[col].to_numpy().astype(float)
            if permutar is not None:
                z = _within_perm(z, permutar, rng)
            z = (z[s] - z[s].mean()) / z[s].std()
            prod = z[iu[0]] * z[iu[1]]
            sm, ct = np.bincount(b, weights=prod, minlength=len(BANDAS)), np.bincount(b, minlength=len(BANDAS))
            for k in range(len(BANDAS) - 1):
                rows.append((col, r, BANDAS[k], BANDAS[k + 1], sm[k] / max(ct[k], 1), int(ct[k])))
    t = pl.DataFrame(rows, schema=["desfecho", "rep", "de_m", "ate_m", "r", "pares"], orient="row")
    return t.group_by("desfecho", "de_m", "ate_m").agg(pl.col("r").mean(), pl.col("r").std().alias("r_dp"),
                                                      pl.col("pares").sum()).sort("desfecho", "de_m")


def _alcance(cg: pl.DataFrame) -> dict:
    """Distância em que a correlação cai abaixo de 1/e da primeira faixa (e o ajuste exponencial)."""
    out = {}
    for col, g in cg.group_by("desfecho"):
        g = g.sort("de_m")
        mid = ((g["de_m"] + g["ate_m"]) / 2).to_numpy()
        r = g["r"].to_numpy()
        ok = r > 0.005
        lim = r[0] / np.e
        abaixo = np.where(r < lim)[0]
        fit = np.polyfit(mid[ok], np.log(r[ok]), 1) if ok.sum() >= 3 else (np.nan, np.nan)
        out[col[0]] = {"r_0_250m": float(r[0]), "cai_1_e_em_m": float(mid[abaixo[0]]) if len(abaixo) else None,
                       "escala_exp_m": float(-1 / fit[0]) if fit[0] < 0 else None}
    return out


# --- H: controles ----------------------------------------------------------------------------

def controles(res: pl.DataFrame, pares: pl.DataFrame, xy: np.ndarray, log=print) -> dict:
    from scipy.stats import spearmanr

    el = res.filter(pl.col("elegivel"))
    out = {"quanto_total_vs_geo_spearman": float(spearmanr(el["quanto"], el["quanto_geo"]).statistic),
           "quanto_vs_geo_frac_spearman": float(spearmanr(el["quanto"], el["geo_frac"]).statistic),
           "geo_frac_mediana": float(el["geo_frac"].median())}
    i, j = pares["i"].to_numpy(), pares["j"].to_numpy()
    gf = res["geo_frac"].to_numpy()
    q = res["quanto"].to_numpy()
    out["delta_quanto_vs_delta_geo_spearman"] = float(spearmanr(np.abs(q[i] - q[j]), np.abs(gf[i] - gf[j])).statistic)
    # delegacia contra distrito: variância do resíduo entre grupos
    for col in ("quanto", "hora_noturna", "fen_div"):
        z = el[col].to_numpy()
        o = {}
        for nome in ("cd_dist", "dp"):
            g = np.unique(el[nome].to_numpy(), return_inverse=True)[1]
            zc = z - (np.bincount(g, weights=z) / np.bincount(g))[g]
            o[f"eta2_{nome}"] = float(1 - np.var(zc) / np.var(z))
            o[f"grupos_{nome}"] = int(g.max() + 1)
        k = np.unique(np.char.add(el["cd_dist"].to_numpy().astype(str), el["dp"].to_numpy().astype(str)), return_inverse=True)[1]
        o["eta2_distrito_x_dp"] = float(1 - np.var(z - (np.bincount(k, weights=z) / np.bincount(k))[k]) / np.var(z))
        o["grupos_distrito_x_dp"] = int(k.max() + 1)
        out[f"eta2_{col}"] = o
    # gêmeos no mesmo distrito: mesma delegacia contra delegacias diferentes
    dp = res["dp"].to_numpy()
    md = pares["mesmo_distrito"].to_numpy()
    for nome, m in (("mesma_dp", md & (dp[i] == dp[j])), ("outra_dp", md & (dp[i] != dp[j]))):
        out[f"gemeos_mesmo_distrito_{nome}"] = {"r_quanto": _corr_sim(q, i[m], j[m]), "pares": int(m.sum())}
    # placebo: resíduo permutado dentro de distrito × decil
    strata = np.unique(res["cd_dist"].to_numpy(), return_inverse=True)[1] * 10 + _dec_densidade(res)
    rng = np.random.default_rng(7)
    qp = _within_perm(q, strata, rng)
    near = pares["dist_m"].to_numpy() < 1000
    out["placebo"] = {"r_gemeos_todos": _corr_sim(qp, i, j), "r_gemeos_ate_1km": _corr_sim(qp, i[near], j[near]),
                      "r_gemeos_ate_1km_real": _corr_sim(q, i[near], j[near])}
    cgp = correlograma(res, xy, cols=("quanto",), reps=2, permutar=strata, seed=11)
    out["placebo"]["correlograma_quanto"] = {f"{int(a)}-{int(b)}": round(float(r), 3)
                                             for a, b, r in zip(cgp["de_m"], cgp["ate_m"], cgp["r"])}
    log(f"controles: quanto total × geocodificado ρ = {out['quanto_total_vs_geo_spearman']:.2f}; "
        f"eta² delegacia {out['eta2_quanto']['eta2_dp']:.2f} × distrito {out['eta2_quanto']['eta2_cd_dist']:.2f}; "
        f"placebo gêmeos até 1 km r = {out['placebo']['r_gemeos_ate_1km']:.2f} (real {out['placebo']['r_gemeos_ate_1km_real']:.2f})")
    return out


# --- figura exploratória -----------------------------------------------------------------------

def figura(cg: pl.DataFrame, cg_placebo: dict, gem: dict, tnl: dict, lisa: pl.DataFrame) -> None:
    import geopandas as gpd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cityomics.paths import REPO_ROOT

    d = REPO_ROOT / "figures" / "out" / "exploratorio" / "contexto"
    d.mkdir(parents=True, exist_ok=True)
    nomes = {"quanto": "Quanto (celular)", "quanto_dist": "Quanto, sem distrito", "fen_div": "Que crime (afastamento)",
             "hora_noturna": "A que hora (noturna)", "tendencia": "Tendência 2022–25"}
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.6))
    for col in DESFECHOS:
        g = cg.filter(pl.col("desfecho") == col).sort("de_m")
        mid = ((g["de_m"] + g["ate_m"]) / 2).to_numpy() / 1000
        ax[0].plot(mid, g["r"], marker="o", ms=3, label=nomes[col])
    pl_ = cg_placebo["correlograma_quanto"]
    mid = [(float(k.split("-")[0]) + float(k.split("-")[1])) / 2000 for k in pl_]
    ax[0].plot(mid, list(pl_.values()), ls="--", c="grey", label="Placebo (quanto permutado\ndentro de distrito × densidade)")
    ax[0].axhline(0, c="k", lw=0.5)
    ax[0].set_xscale("log")
    ax[0].set_xlabel("Distância entre setores (km)")
    ax[0].set_ylabel("Correlação do resíduo")
    ax[0].set_title("a  Correlograma do resíduo do tecido", loc="left")
    ax[0].legend(fontsize=7, frameon=False)
    faixas = [k for k in gem["quanto"] if k.endswith("m")]
    x = np.arange(len(faixas))
    for n, col in enumerate(DESFECHOS):
        c = f"C{n}"
        ax[1].bar(x + (n - 2) * 0.16, [tnl[col][f"gemeos_{k}"] for k in faixas], width=0.16, color=c, label=nomes[col])
        ax[1].bar(x + (n - 2) * 0.16, [gem[col][k]["r"] for k in faixas], width=0.16, fill=False, edgecolor=c, lw=0.8)
    ax[1].set_xticks(x, [k.replace("-", "–").replace("inf", "∞") for k in faixas], fontsize=8)
    ax[1].set_xlabel("Distância entre os gêmeos")
    ax[1].set_ylabel("Correlação entre gêmeos")
    ax[1].set_title("b  Gêmeos de tecido (cheio: sem o tecido não linear;\n    contorno: só modelo aditivo)", loc="left", fontsize=10)
    ax[1].axhline(0, c="k", lw=0.5)
    g = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    g["cd_setor"] = g["cd_setor"].astype(str)
    g = g.merge(lisa.select("cd_setor", "q|quanto").to_pandas(), on="cd_setor", how="inner")
    cores = {0: "#e6e6e6", 1: "#c0392b", 2: "#85c1e9", 3: "#1f4e79", 4: "#f1948a"}
    g.plot(ax=ax[2], color=g["q|quanto"].map(cores), linewidth=0, rasterized=True)
    ax[2].set_axis_off()
    ax[2].set_title("c  LISA do resíduo (quanto)", loc="left")
    from matplotlib.patches import Patch

    ax[2].legend(handles=[Patch(color=cores[k], label=l) for k, l in ((1, "Alto–alto"), (3, "Baixo–baixo"), (4, "Alto–baixo"),
                                                                       (2, "Baixo–alto"), (0, "n.s."))], fontsize=7, frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(d / "contexto_passo1.png", dpi=200)
    plt.close(fig)


# --- orquestração ------------------------------------------------------------------------------

def run(log=print) -> dict:
    res, E, rep = residuos(log=log)
    ids = res.select("cd_setor")
    xy = _centroides(ids)
    pares, rep["gemeos_balanco"] = gemeos(res, E, xy, log=log)
    rep["gemeos_correlacao"] = correlacao_gemeos(res, pares)
    rep["tecido_nao_linear"], sem = tecido_nao_linear(res, E, pares, log=log)
    res.select("cd_setor").hstack(sem).write_parquet(out_dir() / "residuos_sem_tecido.parquet")
    for col in DESFECHOS:
        g = rep["gemeos_correlacao"][col]
        log(f"  gêmeos {col}: r = {g['todos']:.2f}; até 1 km {g['0-1000m']['r']:.2f}, 1–3 km {g['1000-3000m']['r']:.2f}, "
            f"3–10 km {g['3000-10000m']['r']:.2f}, >10 km {g['10000-infm']['r']:.2f}")
    rep["moran"], lisa = moran(res, log=log)
    lisa.write_parquet(out_dir() / "lisa_setor.parquet")
    cg = correlograma(res, xy)
    cg.write_parquet(out_dir() / "correlograma.parquet")
    rep["alcance"] = _alcance(cg)
    log(f"  alcance: {json.dumps({k: v['cai_1_e_em_m'] for k, v in rep['alcance'].items()})}")
    rep["controles"] = controles(res, pares, xy, log=log)
    (out_dir() / "contexto.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=float))
    figura(cg, rep["controles"]["placebo"], rep["gemeos_correlacao"], rep["tecido_nao_linear"], lisa)
    return rep
