"""Identificação e validação da atribuição (parecer crítico de 2026-10-20: R3, R4 metades, R10, R12).

Agente B do plano ``paper/03_plano_parecer.md``. Só distritos de exploração (D53), nada de 2026 e só
agregados por classe na saída. Não altera nenhum módulo existente: as variantes de que precisa estão aqui.

1. **Condicionamento** (R3): número de condição de E com colunas normalizadas (Belsley) e do desenho
   ponderado de Poisson, correlações entre exposições, informação de Fisher no ótimo (e sanduíche por
   distrito) e correlação das log-taxas entre reamostras por distrito.
2. **Recuperação por simulação** (R3): E real, λ* ajustado; Poisson puro, risco por distrito,
   sobredispersão gama por setor e λ* permutado entre classes da mesma unidade; cobertura do bootstrap.
3. **Metades dos geocodificados** (R4): λ das contagens inteiras da metade A contra a checagem em escala
   fina com a metade B; versão temporal (λ de 2024 contra pontos de 2025).
4. **Exposição das favelas** (R12): reescala (invariância) e alternativas que mudam a distribuição espacial.
5. **Exposição dos lotes** (R3): testada contra área do terreno e área construída.
6. **Estabilidade dos 12 tipos finais** (R10): o procedimento de ``typing.stability`` com a fusão e a
   separação vertical aplicadas a cada subamostra.
7. **Unidades das taxas** (R3b): amplitude só entre classes por km e só entre estações.

O EM é o de ``attribution.em_fit`` (mesma inicialização, atualização e regra de parada, coluna a coluna),
reescrito em numba para ajustar milhares de colunas (réplicas, reamostras) de uma vez. Reamostrar distritos
equivale a pesar cada setor pela multiplicidade do seu distrito, e é assim que o bootstrap é feito aqui.

Saída: ``data/processed/atlas/fenotipo/identificacao.json``.
"""

from __future__ import annotations

import json
import os
import time

import numpy as np
import polars as pl
from scipy.stats import spearmanr

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit, em_fit_multi
from cityomics.atlas.fenotipo import (COBERTURA_MIN, EVENTOS, _log2_enriq, _participacao, matriz, out_dir,
                                      setor_exposicao)
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.grupos import FAVELA   # nomes de grupos saem da tipagem (atlas/grupos.py), não de constantes
from cityomics.paths import interim_dir, processed_dir

SAIDA = "identificacao.json"
ANOS = (2024, 2025)
VERSAO_PUBLICADA = "v2_tipos_publicados_ruas_corrigidas"   # tipagem publicada antes da refação (2026-10-20)
TIPOS_SIM = ("carga", "letal", "residencia")
SEMENTES = (0, 1, 2, 3, 4)
N_BOOT = 200
N_SIM = 200
COB_SIM, COB_BOOT = 50, 100
BUFFER_M, MAX_DIST, STATION_M = 40.0, 60.0, 100.0   # os mesmos de attribution.point_validation
PARTE_MIN = 0.02                                     # classes com ao menos 2% do fenótipo (assinaturas)
CORR_FORTE = 0.5


def _f(x):
    """Converte para tipos do JSON (números com 4 algarismos significativos bastam no relatório)."""
    if isinstance(x, dict):
        return {str(k): _f(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_f(v) for v in x]
    if isinstance(x, np.ndarray):
        return _f(x.tolist())
    if isinstance(x, (np.bool_, bool)):
        return bool(x)
    if isinstance(x, (np.integer, int)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(f"{float(x):.6g}")
    return x


def _rho(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3 or np.ptp(a[ok]) == 0 or np.ptp(b[ok]) == 0:
        return float("nan")
    return float(spearmanr(a[ok], b[ok]).statistic)


def _q(x, qs=(2.5, 50, 97.5)) -> list[float]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(v) for v in np.percentile(x, qs)] if len(x) else [float("nan")] * len(qs)


# --- EM vetorizado (numba) ---------------------------------------------------------------------

def _kernel():
    from numba import njit, prange

    @njit(cache=False)
    def em_col(indptr, indices, data, K, Y, yc, dist, mult, f, lk, n_iter, tol):
        """Uma coluna: inicialização em ``lk`` (já zerada onde a classe não tem exposição)."""
        n = indptr.shape[0] - 1
        colsum = np.zeros(K)
        for s in range(n):
            w = mult[dist[s], f]
            if w != 0:
                for p in range(indptr[s], indptr[s + 1]):
                    colsum[indices[p]] += w * data[p]
        num = np.zeros(K)
        ll_old = -np.inf
        t = 0
        while True:
            for k in range(K):
                num[k] = 0.0
            ll = 0.0
            for k in range(K):
                ll -= lk[k] * colsum[k]          # −Σ w μ, sem passar pelos setores
            for s in range(n):
                w = mult[dist[s], f]
                ys = Y[s, yc]
                if w == 0 or ys == 0:
                    continue
                mu = 0.0
                for p in range(indptr[s], indptr[s + 1]):
                    mu += data[p] * lk[indices[p]]
                if mu > 0:
                    ll += w * ys * np.log(mu)
                    r = w * ys / mu
                    for p in range(indptr[s], indptr[s + 1]):
                        num[indices[p]] += data[p] * r
                else:
                    ll += w * ys * np.log(1e-300)
            # mesma regra de em_fit: a primeira parada possível compara ll_2 com ll_1
            if t >= 2 and abs(ll - ll_old) < tol * (1 + abs(ll)):
                break
            if t == n_iter:
                break
            ll_old = ll
            for k in range(K):
                if colsum[k] > 0:
                    lk[k] = lk[k] * num[k] / colsum[k]
                else:
                    lk[k] = 0.0
            t += 1
        return t

    @njit(cache=False)
    def init_col(indptr, indices, data, K, Y, yc, dist, mult, f, lam0, usa_lam0):
        n = indptr.shape[0] - 1
        colsum = np.zeros(K)
        ytot = 0.0
        for s in range(n):
            w = mult[dist[s], f]
            if w != 0:
                ytot += w * Y[s, yc]
                for p in range(indptr[s], indptr[s + 1]):
                    colsum[indices[p]] += w * data[p]
        tot = 0.0
        for k in range(K):
            tot += colsum[k]
        lk = np.empty(K)
        for k in range(K):
            lk[k] = lam0[k, f] if usa_lam0 else ytot / max(tot, 1e-12)
            if colsum[k] == 0:
                lk[k] = 0.0
        return lk

    @njit(parallel=True, cache=False)
    def em_csr(indptr, indices, data, K, Y, ycol, dist, mult, lam0, usa_lam0, n_iter, tol):
        F = ycol.shape[0]
        lam = np.empty((K, F))
        iters = np.zeros(F, np.int64)
        for f in prange(F):
            lk = init_col(indptr, indices, data, K, Y, ycol[f], dist, mult, f, lam0, usa_lam0)
            iters[f] = em_col(indptr, indices, data, K, Y, ycol[f], dist, mult, f, lk, n_iter, tol)
            lam[:, f] = lk
        return lam, iters

    return em_csr


_EM = None


def em(E: np.ndarray, Y: np.ndarray, ycol=None, dist=None, mult=None, lam0=None, n_iter: int = 500,
       tol: float = 1e-8, threads: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """O EM de ``em_fit`` coluna a coluna: Y (n × G), ``ycol`` (F) diz que coluna de Y cada ajuste usa e
    ``mult`` (D × F) pesa cada setor pela multiplicidade do seu distrito ``dist`` (n) na reamostra.
    Devolve Λ (K × F) e o número de iterações de cada coluna."""
    global _EM
    import numba
    from scipy.sparse import csr_matrix

    if _EM is None:
        _EM = _kernel()
    threads = threads or int(os.environ.get("OMP_NUM_THREADS", 4))
    numba.set_num_threads(max(1, min(threads, numba.config.NUMBA_NUM_THREADS)))
    Y = np.asarray(Y, dtype=np.float64)
    if Y.ndim == 1:
        Y = Y[:, None]
    keep = E.sum(axis=1) > 0
    Ek, Yk = E[keep], np.ascontiguousarray(Y[keep])
    ycol = np.arange(Y.shape[1]) if ycol is None else np.asarray(ycol)
    F = len(ycol)
    if dist is None:
        dk, mult = np.zeros(keep.sum(), np.int64), np.ones((1, F))
    else:
        dk = np.asarray(dist)[keep].astype(np.int64)
    m = csr_matrix(Ek)
    usa = lam0 is not None
    l0 = np.ascontiguousarray(lam0, dtype=np.float64) if usa else np.zeros((E.shape[1], F))
    return _EM(m.indptr.astype(np.int64), m.indices.astype(np.int64), m.data.astype(np.float64), E.shape[1], Yk,
               ycol.astype(np.int64), dk, np.ascontiguousarray(mult, dtype=np.float64), l0, usa, n_iter, tol)


def multiplicidades(clusters: np.ndarray, n_boot: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Código do distrito de cada setor e multiplicidades (D × n_boot) das reamostras por distrito, com a
    mesma sequência aleatória de ``attribution.bootstrap`` e ``fenotipo._boot_picks``."""
    rng = np.random.default_rng(seed)
    uc, inv = np.unique(clusters, return_inverse=True)
    mult = np.empty((len(uc), n_boot))
    for b in range(n_boot):
        mult[:, b] = np.bincount(rng.integers(0, len(uc), len(uc)), minlength=len(uc))
    return inv, mult


# --- dados ---------------------------------------------------------------------------------------

def celular_setor(ids: pl.DataFrame, anos, col: str = "n_total") -> np.ndarray:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet"))
    t = (t.with_columns(pl.col("periodo").str.slice(0, 4).cast(pl.Int32).alias("ano"), pl.col("cd_setor").cast(pl.String))
         .filter(pl.col("ano").is_in(list(anos))).group_by("cd_setor").agg(pl.col(col).sum().cast(pl.Float64).alias("y")))
    return ids.select("cd_setor").join(t, on="cd_setor", how="left").fill_null(0.0)["y"].to_numpy().astype(float)


def painel(ids: pl.DataFrame, anos=ANOS, col: str = "n_total") -> tuple[np.ndarray, list[str]]:
    tab = pl.read_parquet(guard.pre2026(out_dir() / "fenotipo_setor_ano.parquet"))
    return matriz(ids, tab, anos, col=col)


def _km(names) -> np.ndarray:
    return np.array([not n.startswith("n_") for n in names])


def _lotes(names) -> np.ndarray:
    return np.array([not n.startswith(("rua_", "n_")) for n in names])


# --- 1. condicionamento --------------------------------------------------------------------------

def _belsley(X: np.ndarray, names) -> dict:
    Xn = X / np.linalg.norm(X, axis=0)
    _, s, vt = np.linalg.svd(Xn, full_matrices=False)
    ci = s[0] / s
    phi = (vt.T ** 2) / s ** 2
    pi = phi / phi.sum(axis=1, keepdims=True)    # proporções de variância (classe × componente)
    dep = []
    for j in np.argsort(-ci):
        if ci[j] < 10:
            break
        envolvidas = [(names[k], float(pi[k, j])) for k in np.argsort(-pi[:, j]) if pi[k, j] >= 0.3]
        dep.append({"indice_condicao": float(ci[j]), "classes": envolvidas})
    return {"numero_condicao": float(ci.max()), "indices_condicao": sorted(ci.tolist(), reverse=True),
            "dependencias_indice_ge_10": dep}


def _pares(C: np.ndarray, names, limiar: float = CORR_FORTE) -> list[dict]:
    out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if np.isfinite(C[i, j]) and abs(C[i, j]) >= limiar:
                out.append({"a": names[i], "b": names[j], "r": float(C[i, j])})
    return sorted(out, key=lambda d: d["r"])


def _extremos(C: np.ndarray, names, n: int = 5) -> dict:
    """Os n pares mais negativos e mais positivos (fora da diagonal), qualquer que seja o valor."""
    iu = np.triu_indices(len(names), 1)
    v = C[iu]
    o = np.argsort(v)
    par = lambda i: {"a": names[iu[0][i]], "b": names[iu[1][i]], "r": float(v[i])}  # noqa: E731
    return {"negativos": [par(i) for i in o[:n]], "positivos": [par(i) for i in o[::-1][:n]],
            "max_abs": float(np.abs(v).max())}


def _corr(M: np.ndarray) -> np.ndarray:
    sd = np.sqrt(np.diag(M))
    return M / np.outer(sd, sd)


def condicionamento(ids, E, names, y, n_boot: int = N_BOOT, log=print) -> dict:
    lam, it = em(E, y)
    lam = lam[:, 0]
    keep = E.sum(axis=1) > 0
    Ek, yk = E[keep], y[keep]
    mu = Ek @ lam
    # informação de Fisher observada e esperada no ótimo, na escala log (dλ/λ)
    I_obs = (Ek * (yk / mu ** 2)[:, None]).T @ Ek
    I_esp = (Ek / mu[:, None]).T @ Ek
    D = np.diag(lam)
    cov_obs = np.linalg.inv(D @ I_obs @ D)
    cov_esp = np.linalg.inv(D @ I_esp @ D)
    # sanduíche com escores somados por distrito (o análogo analítico do bootstrap por distrito)
    g = Ek * (yk / mu - 1.0)[:, None]
    _, dk = np.unique(ids["cd_dist"].to_numpy()[keep], return_inverse=True)
    G = np.zeros((dk.max() + 1, E.shape[1]))
    np.add.at(G, dk, g)
    Iinv = np.linalg.inv(I_obs)
    cov_sand = np.diag(1 / lam) @ (Iinv @ (G.T @ G) @ Iinv) @ np.diag(1 / lam)
    R_esp = _corr(cov_esp)
    vif = np.diag(np.linalg.inv(_corr(D @ I_esp @ D)))   # inflação da variância pela co-localização
    # bootstrap por distrito (mesmas reamostras de attribution.bootstrap, seed 0)
    dist, mult = multiplicidades(ids["cd_dist"].to_numpy(), n_boot, seed=0)
    B, _ = em(E, y, ycol=np.zeros(n_boot, int), dist=dist, mult=mult)
    lb = np.log(np.clip(B, 1e-6, None))
    R_boot = np.corrcoef(lb)
    R_boot_s = spearmanr(B.T).statistic
    cv = B.std(axis=1, ddof=1) / B.mean(axis=1)
    lo, hi = np.percentile(B, [2.5, 97.5], axis=1)
    Cp = np.corrcoef(E.T)
    Cs = spearmanr(E).statistic
    w = np.sqrt(1 / mu)
    rep = {
        "setores": int(E.shape[0]), "classes": names, "iteracoes_em": int(it[0]),
        "belsley_E": _belsley(E, names),
        "belsley_desenho_poisson": _belsley(Ek * w[:, None], names),
        "correlacao_exposicoes_pearson_pares": _pares(Cp, names),
        "correlacao_exposicoes_spearman_pares": _pares(Cs, names),
        "correlacao_exposicoes_pearson_extremos": _extremos(Cp, names),
        "fisher": {
            "ep_log_observada": dict(zip(names, np.sqrt(np.diag(cov_obs)))),
            "ep_log_esperada": dict(zip(names, np.sqrt(np.diag(cov_esp)))),
            "ep_log_sanduiche_distrito": dict(zip(names, np.sqrt(np.clip(np.diag(cov_sand), 0, None)))),
            "inflacao_variancia": dict(zip(names, vif)),
            "pares_correlacao_estimativas": _pares(R_esp, names),
            "pares_correlacao_sanduiche": _pares(_corr(cov_sand), names),
            "extremos_esperada": _extremos(R_esp, names), "extremos_sanduiche": _extremos(_corr(cov_sand), names),
        },
        "bootstrap": {
            "n_boot": n_boot, "lambda": dict(zip(names, lam)), "cv": dict(zip(names, cv)),
            "ic95": {n: [float(a), float(b)] for n, a, b in zip(names, lo, hi)},
            "pares_correlacao_log": _pares(R_boot, names),
            "pares_correlacao_spearman": _pares(R_boot_s, names),
            "extremos_log": _extremos(R_boot, names), "extremos_spearman": _extremos(R_boot_s, names),
            "correlacao_log_matriz": R_boot,
        },
    }
    neg = [p for p in rep["bootstrap"]["pares_correlacao_log"] if p["r"] < 0]
    log(f"condicionamento: κ(E normalizada) = {rep['belsley_E']['numero_condicao']:.1f}; "
        f"κ(desenho Poisson) = {rep['belsley_desenho_poisson']['numero_condicao']:.1f}; "
        f"{len(neg)} pares com r ≤ −{CORR_FORTE} no bootstrap")
    return rep


# --- 2. recuperação por simulação ----------------------------------------------------------------

def _alpha(y: np.ndarray, mu: np.ndarray) -> float:
    """Sobredispersão relativa por momentos, Var = μ + α μ² (a mesma fórmula de robustez.escala_do_excesso)."""
    return float(max(0.0, np.sum((y - mu) ** 2 - y) / np.sum(mu ** 2)))


def _theta(E, Y, dist) -> tuple[np.ndarray, np.ndarray]:
    """λ (K × F) e θ por setor do modelo com risco por distrito (``robustez.em_distrito``)."""
    from cityomics.atlas.robustez import em_distrito

    _, g = np.unique(dist, return_inverse=True)
    lam_d, th = em_distrito(E, Y, dist)
    return lam_d, th[g]


def _margem_topo(lam: np.ndarray, E, names) -> dict:
    """Diferença de log2 entre a classe mais enriquecida e a segunda (entre as com ≥ 2%), por fenótipo."""
    S = _participacao(lam, E)
    enr = _log2_enriq(S)
    out = {}
    for j in range(lam.shape[1]):
        e = np.sort(np.where(S[:, j] >= PARTE_MIN, enr[:, j], -np.inf))[::-1]
        k = np.argsort(-np.where(S[:, j] >= PARTE_MIN, enr[:, j], -np.inf))
        out[j] = {"topo": names[k[0]], "segunda": names[k[1]], "margem_log2": float(e[0] - e[1])}
    return out


def _topo(S: np.ndarray, enr: np.ndarray) -> np.ndarray:
    """Classe mais enriquecida por fenótipo entre as que têm ao menos 2% (sem o critério do IC)."""
    e = np.where(S >= PARTE_MIN, enr, -np.inf)
    return np.argmax(e, axis=0)


def _metricas(Lt: np.ndarray, Lh: np.ndarray, E, names, fen) -> dict:
    """Lt e Lh: K × F × R (verdadeiro e estimado). Métricas por classe e por fenótipo."""
    K, F, R = Lh.shape
    km = _km(names)
    ex = E.sum(axis=0)
    St = Lt * ex[:, None, None]
    St = St / St.sum(axis=0, keepdims=True)
    Sh = Lh * ex[:, None, None]
    Sh = Sh / np.where(Sh.sum(axis=0, keepdims=True) > 0, Sh.sum(axis=0, keepdims=True), 1.0)
    rel = Lh / np.where(Lt > 0, Lt, np.nan) - 1.0
    big = St >= PARTE_MIN
    out = {}
    for j, f in enumerate(fen):
        rho_all = [_rho(Lt[:, j, r], Lh[:, j, r]) for r in range(R)]
        rho_km = [_rho(Lt[km, j, r], Lh[km, j, r]) for r in range(R)]
        rho_s = [_rho(St[:, j, r], Sh[:, j, r]) for r in range(R)]
        top_t = np.argmax(np.where(km[:, None], Lt[:, j, :], -np.inf), axis=0)
        top_h = np.argmax(np.where(km[:, None], Lh[:, j, :], -np.inf), axis=0)
        topS_t, topS_h = np.argmax(St[:, j, :], axis=0), np.argmax(Sh[:, j, :], axis=0)
        cls = {}
        for k, n in enumerate(names):
            cls[n] = {"lambda_verdadeiro_mediano": float(np.median(Lt[k, j])),
                      "vies_relativo": float(np.nanmean(rel[k, j])),
                      "vies_relativo_mediano": float(np.nanmedian(rel[k, j])),
                      "rmse_relativo": float(np.sqrt(np.nanmean(rel[k, j] ** 2))),
                      "erro_abs_relativo_mediano": float(np.nanmedian(np.abs(rel[k, j]))),
                      "parte_verdadeira_mediana": float(np.median(St[k, j])),
                      "vies_parte_pp": float(100 * np.mean(Sh[k, j] - St[k, j])),
                      "rmse_parte_pp": float(100 * np.sqrt(np.mean((Sh[k, j] - St[k, j]) ** 2))),
                      "parte_quase_zero": float(np.mean(Lh[k, j] < 1e-3 * np.maximum(Lt[k, j], 1e-12))),
                      "erro_abs_relativo_mediano_parte_ge_2pct": float(np.nanmedian(np.abs(rel[k, j][big[k, j]])))
                      if big[k, j].any() else None}
        out[f] = {"spearman_taxas_todas": _q(rho_all), "spearman_taxas_km": _q(rho_km),
                  "spearman_partes": _q(rho_s),
                  "topo_taxa_km_recuperado": float(np.mean(top_t == top_h)),
                  "topo_parte_recuperado": float(np.mean(topS_t == topS_h)),
                  "erro_max_parte_pp_mediano": float(100 * np.median(np.abs(Sh[:, j] - St[:, j]).max(axis=0))),
                  "erro_abs_relativo_mediano_classes_ge_2pct": float(np.nanmedian(np.abs(rel[:, j][big[:, j]]))),
                  "erro_abs_relativo_p90_classes_ge_2pct": float(np.nanpercentile(np.abs(rel[:, j][big[:, j]]), 90)),
                  "erro_abs_relativo_mediano_classes_lt_2pct": float(np.nanmedian(np.abs(rel[:, j][~big[:, j]])))
                  if (~big[:, j]).any() else None,
                  "classes": cls}
    if F > 2:
        enr_t = _log2_enriq_3d(St)
        enr_h = _log2_enriq_3d(Sh)
        tt = np.stack([_topo(St[:, :, r], enr_t[:, :, r]) for r in range(R)], axis=1)
        th = np.stack([_topo(Sh[:, :, r], enr_h[:, :, r]) for r in range(R)], axis=1)
        for j, f in enumerate(fen):
            out[f]["topo_enriquecido_recuperado"] = float(np.mean(tt[j] == th[j]))
        out["_painel"] = {"topo_enriquecido_recuperado_mediano": float(np.median(np.mean(tt == th, axis=1))),
                          "classes_distintas_no_topo_verdadeiro": _q([len(set(tt[:, r])) for r in range(R)]),
                          "classes_distintas_no_topo_estimado": _q([len(set(th[:, r])) for r in range(R)]),
                          "fenotipos_com_topo_igual": _q([(tt[:, r] == th[:, r]).sum() for r in range(R)])}
    return out


def _log2_enriq_3d(S: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    return np.log2((S + eps) / (S.mean(axis=1, keepdims=True) + eps))


def _ajusta_reps(E, MU_fn, R: int, F: int, rng, bloco: int) -> np.ndarray:
    """Simula R réplicas (n × F cada, médias dadas por ``MU_fn(r)``) e reajusta: devolve K × F × R."""
    out = np.empty((E.shape[1], F, R))
    for r0 in range(0, R, bloco):
        rs = range(r0, min(R, r0 + bloco))
        Y = np.concatenate([rng.poisson(MU_fn(r)).astype(float) for r in rs], axis=1)
        L, _ = em(E, Y)
        out[:, :, r0:r0 + len(rs)] = L.reshape(E.shape[1], len(rs), F).transpose(0, 2, 1)
    return out


def _cenarios(E, lam: np.ndarray, theta_s: np.ndarray, lam_d: np.ndarray, alpha: np.ndarray, names, R: int, seed: int,
              bloco: int) -> dict:
    """Os cenários com λ* (K × F). (b) usa λ* com o θ do distrito (renormalizado para o mesmo total); (b2) usa o
    λ e o θ ajustados juntos (``em_distrito``), e o alvo é o λ desse modelo. Devolve as métricas de cada um."""
    K, F = lam.shape
    km = np.where(_km(names))[0]
    st = np.where(~_km(names))[0]
    MU = E @ lam
    out = {}
    rng = np.random.default_rng(seed)
    Lt = np.repeat(lam[:, :, None], R, axis=2)
    Lh = _ajusta_reps(E, lambda r: MU, R, F, rng, bloco)
    out["a_poisson"] = _metricas(Lt, Lh, E, names, _FEN)
    Mb = MU * theta_s[:, None]
    Mb = Mb * MU.sum(axis=0) / Mb.sum(axis=0)
    Lh = _ajusta_reps(E, lambda r: Mb, R, F, rng, bloco)
    out["b_risco_distrito"] = _metricas(Lt, Lh, E, names, _FEN)
    Mb2 = (E @ lam_d) * theta_s[:, None]
    Lh = _ajusta_reps(E, lambda r: Mb2, R, F, rng, bloco)
    out["b2_risco_distrito_coerente"] = _metricas(np.repeat(lam_d[:, :, None], R, axis=2), Lh, E, names, _FEN)
    shape = np.where(alpha > 0, 1 / np.maximum(alpha, 1e-9), 1e9)
    Lh = _ajusta_reps(E, lambda r: MU * rng.gamma(shape, 1 / shape, size=MU.shape), R, F, rng, bloco)
    out["c_sobredispersao"] = _metricas(Lt, Lh, E, names, _FEN)
    perms = np.empty((K, F, R))
    for r in range(R):
        for j in range(F):
            p = np.arange(K)
            p[km] = rng.permutation(km)
            p[st] = rng.permutation(st)
            perms[:, j, r] = lam[p, j]
    Lh = _ajusta_reps(E, lambda r: E @ perms[:, :, r], R, F, rng, bloco)
    out["d_permutado"] = _metricas(perms, Lh, E, names, _FEN)
    return out


_FEN: list[str] = []


def _cobertura(E, lam: np.ndarray, ids, theta_s, lam_d: np.ndarray, alpha: float, names, n_sim: int, n_boot: int,
               seed: int) -> dict:
    """Cobertura dos IC 95% do bootstrap por distrito (taxas e partes) em quatro cenários, para um desfecho."""
    rng = np.random.default_rng(seed)
    mu = E @ lam
    ex = E.sum(axis=0)
    out = {}
    a = max(alpha, 1e-9)
    cen = {"a_poisson": (lambda: mu, lam),
           "b_risco_distrito": (lambda: mu * theta_s * mu.sum() / (mu * theta_s).sum(), lam),
           "b2_risco_distrito_coerente": (lambda: (E @ lam_d) * theta_s, lam_d),
           "c_sobredispersao": (lambda: mu * rng.gamma(1 / a, a, size=mu.shape), lam)}
    for nome, (fm, alvo) in cen.items():
        S_t = alvo * ex / (alvo * ex).sum()
        Y = np.column_stack([rng.poisson(fm()).astype(float) for _ in range(n_sim)])
        dist, mult = multiplicidades(ids["cd_dist"].to_numpy(), n_boot * n_sim, seed=seed + 1)
        L, _ = em(E, Y, ycol=np.repeat(np.arange(n_sim), n_boot), dist=dist, mult=mult)
        L = L.reshape(E.shape[1], n_sim, n_boot)
        S = L * ex[:, None, None]
        S = S / S.sum(axis=0, keepdims=True)
        lo, hi = np.percentile(L, [2.5, 97.5], axis=2)
        slo, shi = np.percentile(S, [2.5, 97.5], axis=2)
        cob = ((lo <= alvo[:, None]) & (alvo[:, None] <= hi)).mean(axis=1)
        cobs = ((slo <= S_t[:, None]) & (S_t[:, None] <= shi)).mean(axis=1)
        out[nome] = {"taxas": dict(zip(names, cob)), "partes": dict(zip(names, cobs)),
                     "taxas_mediana": float(np.median(cob)), "partes_mediana": float(np.median(cobs))}
    return out


def simulacao(ids, E, names, y_cel, n_sim: int = N_SIM, cob_sim: int = COB_SIM, cob_boot: int = COB_BOOT, log=print) -> dict:
    global _FEN
    dist = ids["cd_dist"].to_numpy()
    rep = {"n_sim": n_sim, "cobertura": {"n_sim": cob_sim, "n_boot": cob_boot}}
    # celular 2025
    lam_c = em(E, y_cel)[0]
    keep = E.sum(axis=1) > 0
    a_c = _alpha(y_cel[keep], (E @ lam_c)[keep, 0])
    lamd_c, th_c = _theta(E, y_cel[:, None], dist)
    _FEN = ["celular_2025"]
    t0 = time.time()
    rep["celular_2025"] = {"alpha": a_c, "theta_p10_p90": _q(th_c, (10, 90)),
                           "cenarios": _cenarios(E, lam_c, th_c, lamd_c, np.array([a_c]), names, n_sim, seed=10,
                                                 bloco=n_sim)}
    log(f"simulação celular: {time.time() - t0:.0f} s")
    t0 = time.time()
    rep["celular_2025"]["cobertura"] = _cobertura(E, lam_c[:, 0], ids, th_c, lamd_c[:, 0], a_c, names, cob_sim, cob_boot,
                                                  seed=20)
    log(f"cobertura celular: {time.time() - t0:.0f} s")
    # painel de 15 (2024–2025)
    Y, fen = painel(ids)
    lam_p = em(E, Y)[0]
    mu_p = E @ lam_p
    a_p = np.array([_alpha(Y[keep, j], mu_p[keep, j]) for j in range(len(fen))])
    lamd_p, th_p = _theta(E, Y, dist)
    _FEN = fen
    t0 = time.time()
    cen = _cenarios(E, lam_p, th_p, lamd_p, a_p, names, n_sim, seed=30, bloco=25)
    log(f"simulação do painel: {time.time() - t0:.0f} s")
    mg = _margem_topo(lam_p, E, names)
    rep["painel"] = {"fenotipos": fen, "alpha": dict(zip(fen, a_p)), "cenarios": {},
                     "margem_topo_verdadeiro": {f: mg[j] for j, f in enumerate(fen)}}
    for c, m in cen.items():
        resumo = {f: {k: v for k, v in m[f].items() if k != "classes"} for f in fen}
        rep["painel"]["cenarios"][c] = {"resumo": resumo, "painel": m.get("_painel"),
                                        "classes": {f: m[f]["classes"] for f in TIPOS_SIM}}
    rep["painel"]["cobertura"] = {}
    for f in TIPOS_SIM:
        j = fen.index(f)
        t0 = time.time()
        rep["painel"]["cobertura"][f] = _cobertura(E, lam_p[:, j], ids, th_p, lamd_p[:, j], float(a_p[j]), names, cob_sim,
                                                   cob_boot, seed=40 + j)
        log(f"cobertura {f}: {time.time() - t0:.0f} s")
    return rep


# --- 3. metades dos geocodificados ---------------------------------------------------------------

def eventos_geo(log=print) -> pl.DataFrame:
    """Eventos geocodificados de 2024–2025 (celular e painel), com o mesmo recorte de exploração da
    validação pontual (``explore_mask`` sobre o distrito; distrito nulo fica, como no original)."""
    cols = ["desfecho", "data_fato", "coord_valida", "latitude", "longitude", "cd_dist", "cd_setor"]
    cel = (pl.scan_parquet(guard.pre2026(interim_dir() / "eventos_celular_atribuidos.parquet")).select(cols)
           .filter(pl.col("data_fato").dt.year().is_in(list(ANOS)) & pl.col("coord_valida"))
           .with_columns(pl.lit("celular").alias("desfecho")).collect())
    mul = (pl.scan_parquet(guard.pre2026(interim_dir() / EVENTOS)).select(cols)
           .filter(pl.col("data_fato").dt.year().is_in(list(ANOS)) & pl.col("coord_valida")).collect())
    ev = pl.concat([cel, mul]).with_columns(pl.col("data_fato").dt.year().alias("ano"),
                                             pl.col("cd_dist").cast(pl.String), pl.col("cd_setor").cast(pl.String))
    ev = ev.filter(pl.Series(guard.explore_mask(ev["cd_dist"].fill_null("").to_numpy())))
    log(f"eventos geocodificados 2024–2025 fora do cofre: {ev.height:,}")
    return ev.select("desfecho", "ano", "latitude", "longitude", "cd_dist", "cd_setor")


def ligacao(ev: pl.DataFrame, log=print) -> dict:
    """Pré-computa ``attribution.point_validation`` para todos os eventos de uma vez: estação (≤ 100 m) ou
    segmento mais próximo (≤ 60 m) de cada evento e a repartição de cada segmento entre os lotes
    lindeiros (≤ 40 m, pela testada). A repartição de um segmento não depende de quais eventos caem
    nele, então as taxas observadas de qualquer subconjunto saem por soma."""
    import geopandas as gpd
    import pandas as pd
    from scipy.sparse import csr_matrix
    from shapely import STRtree

    from cityomics.atlas.streets import TERMINAL_LAYER, stations
    from cityomics.external import external_dir
    from cityomics.units.setores import CRS
    from cityomics.units.transit import LAYERS

    for layer in (*LAYERS, TERMINAL_LAYER):   # nenhum download: as camadas precisam estar em cache
        assert (external_dir() / "geosampa" / f"{layer.split(':')[-1]}.geojson").exists(), layer
    pts = gpd.GeoSeries(gpd.points_from_xy(ev["longitude"], ev["latitude"]), crs="EPSG:4326").to_crs(CRS)
    seg = gpd.read_parquet(atlas_dir() / "ruas.parquet")
    st = stations()
    near = STRtree(st.geometry.values).query_nearest(pts.values, max_distance=STATION_M, return_distance=False)
    is_st = np.zeros(len(pts), bool)
    is_st[near[0]] = True
    q = STRtree(seg.geometry.values).query_nearest(pts.values[~is_st], max_distance=MAX_DIST, return_distance=False)
    sub = np.full((~is_st).sum(), -1)
    sub[q[0]] = q[1]
    seg_of = np.full(len(pts), -1)
    seg_of[~is_st] = sub
    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet").filter(pl.col("x").is_not_null())
    cel = cel.filter(pl.Series(guard.explore_mask(cel["cd_dist"].to_numpy())))
    lp = gpd.GeoSeries(gpd.points_from_xy(cel["x"], cel["y"]), crs=CRS)
    used = np.unique(seg_of[seg_of >= 0])
    pairs = STRtree(lp.values).query(seg.geometry.values[used], predicate="dwithin", distance=BUFFER_M)
    expo = cel["exposicao"].to_numpy()
    tipo = cel["tipo"].to_numpy()
    lind = pd.DataFrame({"seg": used[pairs[0]], "lot": pairs[1], "w": expo[pairs[1]]})
    lind["w"] = (lind["w"] / lind.groupby("seg")["w"].transform("sum")).fillna(0.0)
    exp_tipo = pd.Series(expo).groupby(tipo).sum()
    classes = list(exp_tipo.index)
    cidx = {c: i for i, c in enumerate(classes)}
    lind["c"] = [cidx[t] for t in tipo[lind["lot"].to_numpy()]]
    M = csr_matrix((lind["w"].to_numpy(), (lind["seg"].to_numpy(), lind["c"].to_numpy())), shape=(len(seg), len(classes)))
    ruas = ("arterial", "coletora", "local")
    seg_cls = np.full(len(seg), -1)
    for i, c in enumerate(ruas):
        seg_cls[(seg["classe"] == c).to_numpy()] = i
    expo_rua = [float(seg.loc[seg["classe"] == c, "comprimento_m"].sum()) for c in ruas]
    log(f"ligação pontual: {len(pts):,} eventos; {is_st.sum():,} em estações; {(seg_of >= 0).sum():,} ligados a um segmento")
    return {"st": is_st, "seg": seg_of, "M": M, "seg_cls": seg_cls,
            "classes": classes + [f"rua_{c}_m" for c in ruas] + ["estacoes"],
            "exposicao": np.array(list(exp_tipo.to_numpy()) + expo_rua + [float(len(st))])}


def taxas_pontuais(lig: dict, sel: np.ndarray) -> dict:
    """Taxa observada por classe (eventos atribuídos / exposição) para os eventos ``sel`` (máscara)."""
    s = lig["seg"][sel]
    s = s[s >= 0]
    cnt = np.bincount(s, minlength=lig["M"].shape[0]).astype(float)
    lotes = lig["M"].T @ cnt
    ruas = np.bincount(lig["seg_cls"][s], minlength=3)[:3].astype(float)
    ev = np.concatenate([lotes, ruas, [float(lig["st"][sel].sum())]])
    return dict(zip(lig["classes"], ev / lig["exposicao"]))


def _rhos(lam: np.ndarray, names, taxa: dict) -> dict:
    """ρ como no original: todas as classes com λ e exposição > 0 (lotes, favela, sem cadastro e ruas;
    as estações não entram) e só as classes de lote (``spearman_lotes``)."""
    k = [i for i, n in enumerate(names) if n in taxa and np.isfinite(taxa[n])]
    lo = [i for i in k if not names[i].startswith(("rua_", "n_"))]
    return {"todas": _rho(lam[k], [taxa[names[i]] for i in k]), "lotes": _rho(lam[lo], [taxa[names[i]] for i in lo])}


def _contagem_setor(ids: pl.DataFrame, setor: np.ndarray) -> np.ndarray:
    pos = {c: i for i, c in enumerate(ids["cd_setor"].to_list())}
    i = np.array([pos.get(c, -1) for c in setor])
    return np.bincount(i[i >= 0], minlength=ids.height).astype(float)


def metades(ids, E, names, ev: pl.DataFrame, lig: dict, sementes=SEMENTES, log=print) -> dict:
    tab = pl.read_parquet(guard.pre2026(out_dir() / "fenotipo_setor_ano.parquet"))
    Yr, fen = matriz(ids, tab, ANOS)
    # cobertura de coordenadas como em fenotipo.assinaturas (todos os eventos de exploração, 2024–2025)
    todos = (pl.scan_parquet(guard.pre2026(interim_dir() / EVENTOS)).select("desfecho", "data_fato", "coord_valida", "cd_dist")
             .filter(pl.col("data_fato").dt.year().is_in(list(ANOS))).collect())
    todos = todos.filter(pl.Series(guard.explore_mask(todos["cd_dist"].cast(pl.String).fill_null("").to_numpy())))
    cob = todos.group_by("desfecho").agg(pl.col("coord_valida").mean(), pl.len())
    cob = {r["desfecho"]: (float(r["coord_valida"]), int(r["len"])) for r in cob.iter_rows(named=True)}
    testados = [f for f in fen if cob.get(f, (0, 0))[0] >= COBERTURA_MIN and cob[f][1] >= 500]
    alvos = [("celular_2025", "celular", (2025,))] + [(f, f, ANOS) for f in testados]
    des = ev["desfecho"].to_numpy()
    ano = ev["ano"].to_numpy()
    setor = ev["cd_setor"].fill_null("").to_numpy()
    out = {"testados": testados, "cobertura": {f: cob[f][0] for f in testados}}
    for nome, d, anos in alvos:
        base = (des == d) & np.isin(ano, anos)
        if nome == "celular_2025":
            y_rec = celular_setor(ids, (2025,))
            y24 = celular_setor(ids, (2024,))
        else:
            j = fen.index(d)
            y_rec = Yr[:, j]
            y24 = matriz(ids, tab.filter(pl.col("fenotipo") == d), (2024,))[0][:, 0]
        idx = np.where(base)[0]
        y_geo = _contagem_setor(ids, setor[idx])
        tx_all = taxas_pontuais(lig, base)
        lam_rec = em_fit(E, y_rec)["lam"]
        lam_geo = em_fit(E, y_geo)["lam"]
        r = {"eventos_geocodificados": int(len(idx)), "geocodificados_no_setor": float(y_geo.sum()),
             "original": _rhos(lam_rec, names, tx_all), "geo_completo": _rhos(lam_geo, names, tx_all), "metades": []}
        for s in sementes:
            rng = np.random.default_rng(1000 + s)
            a = rng.random(len(idx)) < 0.5
            mA = np.zeros(len(ev), bool)
            mB = np.zeros(len(ev), bool)
            mA[idx[a]] = True
            mB[idx[~a]] = True
            lam_A = em_fit(E, _contagem_setor(ids, setor[idx[a]]))["lam"]
            r["metades"].append({"semente": s, "A_para_B": _rhos(lam_A, names, taxas_pontuais(lig, mB)),
                                 "A_para_A": _rhos(lam_A, names, taxas_pontuais(lig, mA))})
        for chave in ("A_para_B", "A_para_A"):
            for g in ("todas", "lotes"):
                v = [m[chave][g] for m in r["metades"]]
                r[f"{chave}_{g}_media"] = float(np.mean(v))
                r[f"{chave}_{g}_faixa"] = [float(np.min(v)), float(np.max(v))]
        # temporal: λ de 2024 (reconciliado e só geocodificado) contra os pontos de 2025
        m25 = (des == d) & (ano == 2025)
        tx25 = taxas_pontuais(lig, m25)
        g24 = _contagem_setor(ids, setor[(des == d) & (ano == 2024)])
        r["temporal"] = {"reconciliado_2024_para_pontos_2025": _rhos(em_fit(E, y24)["lam"], names, tx25),
                         "geocodificado_2024_para_pontos_2025": _rhos(em_fit(E, g24)["lam"], names, tx25),
                         "eventos_2025": int(m25.sum())}
        out[nome] = r
        log(f"metades {nome}: original ρ = {r['original']['lotes']:.2f} (lotes) / {r['original']['todas']:.2f}; "
            f"A→B {r['A_para_B_lotes_media']:.2f} / {r['A_para_B_todas_media']:.2f}; "
            f"2024→2025 {r['temporal']['reconciliado_2024_para_pontos_2025']['lotes']:.2f}")
    pan = [f for f in testados]
    for chave in ("original", "geo_completo"):
        for g in ("todas", "lotes"):
            out[f"mediana_painel_{chave}_{g}"] = float(np.median([out[f][chave][g] for f in pan]))
    for chave in ("A_para_B", "A_para_A"):
        for g in ("todas", "lotes"):
            out[f"mediana_painel_{chave}_{g}"] = float(np.median([out[f][f"{chave}_{g}_media"] for f in pan]))
    for g in ("todas", "lotes"):
        out[f"mediana_painel_temporal_{g}"] = float(np.median(
            [out[f]["temporal"]["reconciliado_2024_para_pontos_2025"][g] for f in pan]))
        out[f"mediana_painel_temporal_geo_{g}"] = float(np.median(
            [out[f]["temporal"]["geocodificado_2024_para_pontos_2025"][g] for f in pan]))
    return out


# --- 4 e 5. definições de exposição --------------------------------------------------------------

def _perfil(E, Y, dist_codes, n_boot: int = N_BOOT) -> dict:
    """λ (EM de ``em_fit_multi``, como em assinaturas), partes, enriquecimento e IC por distrito."""
    lam = em_fit_multi(E, Y)
    S = _participacao(lam, E)
    enr = _log2_enriq(S)
    F = Y.shape[1]
    dist, mult = multiplicidades(dist_codes, n_boot, seed=0)
    L, _ = em(E, Y, ycol=np.tile(np.arange(F), n_boot), dist=dist, mult=np.repeat(mult, F, axis=1))
    L = L.reshape(E.shape[1], n_boot, F).transpose(1, 0, 2)
    eb = np.stack([_log2_enriq(_participacao(L[b], E)) for b in range(n_boot)])
    lo, hi = np.percentile(eb, [2.5, 97.5], axis=0)
    topo = []
    for j in range(F):
        ok = [k for k in range(E.shape[1]) if S[k, j] >= PARTE_MIN and lo[k, j] > 0]
        topo.append(max(ok, key=lambda k: enr[k, j]) if ok else -1)
    return {"lam": lam, "S": S, "enr": enr, "lo": lo, "hi": hi, "topo": np.array(topo)}


def _compara(p0: dict, p1: dict, names, fen) -> dict:
    rho = [_rho(p0["S"][:, j], p1["S"][:, j]) for j in range(len(fen))]
    nm = lambda k: names[k] if k >= 0 else None  # noqa: E731
    return {"spearman_partes_mediana": float(np.median(rho)), "spearman_partes_min": float(np.min(rho)),
            "spearman_partes": dict(zip(fen, rho)),
            "mesmo_topo": int(sum(int(a == b) for a, b in zip(p0["topo"], p1["topo"]))),
            "topo": {f: nm(k) for f, k in zip(fen, p1["topo"])},
            "classes_distintas_no_topo": int(len({k for k in p1["topo"] if k >= 0}))}


def favela_exposicao(ids, E, names, log=print) -> tuple[dict, dict]:
    """Colunas alternativas da favela nos setores de exploração, normalizadas para o total atual."""
    import geopandas as gpd

    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet", columns=["cd_setor", "classe", "dom_informais", "exposicao"])
    fav = cel.filter(pl.col("classe") == "favela")
    geo = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "dom_ocupados_2022", "geometry"])
    geo = geo[geo["cd_setor"].astype(str).isin(fav["cd_setor"].to_list())]
    g = pl.DataFrame({"cd_setor": geo["cd_setor"].astype(str).to_numpy(), "area": geo.geometry.area.to_numpy(),
                      "perimetro": geo.geometry.length.to_numpy(), "dom_ocupados": geo["dom_ocupados_2022"].to_numpy().astype(float)})
    t = ids.select("cd_setor").join(fav.join(g, on="cd_setor", how="left"), on="cd_setor", how="left").fill_null(0.0)
    k = names.index(FAVELA)
    atual = E[:, k]
    alt = {"atual": atual, "area": t["area"].to_numpy(), "perimetro": t["perimetro"].to_numpy(),
           "raiz_domicilios": np.sqrt(t["dom_informais"].to_numpy()), "domicilios_ocupados": t["dom_ocupados"].to_numpy(),
           "indicador_setor": (t["area"].to_numpy() > 0).astype(float)}   # o mesmo valor em todo setor FCU
    alt = {n: v * atual.sum() / v.sum() for n, v in alt.items()}
    # testada por unidade (a constante 7,0 m): família residencial horizontal (código) e só o tipo popular
    gen = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet", columns=["sql_base", "n_unidades"])
    c = (pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet", columns=["sql_base", "tipo", "familia", "exposicao"])
         .join(gen, on="sql_base", how="inner").filter(pl.col("n_unidades") > 0))
    t_fam = float((c.filter(pl.col("familia") == "res_horizontal").select(pl.col("exposicao") / pl.col("n_unidades")))
                  .to_series().median())
    from cityomics.atlas.grupos import grupos

    t_pop = float((c.filter(pl.col("tipo").is_in(grupos()["popular"])).select(pl.col("exposicao") / pl.col("n_unidades")))
                  .to_series().median())
    fx = atual > 0
    info = {"setores_fcu_exploracao": int((t["area"].to_numpy() > 0).sum()),
            "setores_fcu_sem_domicilio_informal": int(((t["area"].to_numpy() > 0) & ~fx).sum()),
            "testada_por_unidade_familia_res_horizontal": t_fam, "testada_por_unidade_so_popular": t_pop,
            "fator_implicito_m_por_domicilio": float((atual[fx] * 1000 / np.maximum(t["dom_informais"].to_numpy()[fx], 1e-9)).mean()),
            "correlacao_spearman_com_atual": {n: _rho(v[fx | (v > 0)], atual[fx | (v > 0)]) for n, v in alt.items()}}
    return alt, info


def favelas(ids, E, names, n_boot: int = N_BOOT, log=print) -> dict:
    Y, fen = painel(ids)
    dist = ids["cd_dist"].to_numpy()
    k = names.index(FAVELA)
    alt, info = favela_exposicao(ids, E, names)
    # reescala: multiplicar a coluna por uma constante só divide λ_favela pela constante
    base = em_fit_multi(E, Y, n_iter=20000, tol=1e-13)
    S0, enr0 = _participacao(base, E), _log2_enriq(_participacao(base, E))
    resc = {}
    for c in (0.1, 10.0):
        Ec = E.copy()
        Ec[:, k] *= c
        Lc = em_fit_multi(Ec, Y, n_iter=20000, tol=1e-13)
        resc[str(c)] = {"max_dif_parte": float(np.abs(_participacao(Lc, Ec) - S0).max()),
                        "max_dif_log2_enriq": float(np.abs(_log2_enriq(_participacao(Lc, Ec)) - enr0).max()),
                        "razao_lambda_favela_mediana": float(np.median(Lc[k] / base[k]))}
    perf = {}
    for n, col in alt.items():
        Ea = E.copy()
        Ea[:, k] = col
        perf[n] = _perfil(Ea, Y, dist, n_boot=n_boot)
        log(f"favela ({n}): parte em carga {perf[n]['S'][k, fen.index('carga')]:.3f}, "
            f"log2 {perf[n]['enr'][k, fen.index('carga')]:+.2f}")
    out = {"fenotipos": fen, "construcao": info, "reescala": resc, "alternativas": {}}
    for n, p in perf.items():
        out["alternativas"][n] = {
            "parte_favela": dict(zip(fen, p["S"][k])), "log2_enriq_favela": dict(zip(fen, p["enr"][k])),
            "ic_log2_favela": {f: [float(p["lo"][k, j]), float(p["hi"][k, j])] for j, f in enumerate(fen)},
            "lambda_favela": dict(zip(fen, p["lam"][k])),
            "contra_atual": _compara(perf["atual"], p, names, fen)}
    return out


def lote_exposicao(ids, names) -> dict[str, np.ndarray]:
    """Colunas dos lotes com testada (atual), área do terreno e área construída, por setor × tipo.

    Sem área do terreno no IPTU: área do polígono. Sem área construída (terreno vago, sem cadastro):
    área do terreno (ou do polígono), para a classe não sumir. As favelas mantêm a exposição atual."""
    gen = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet",
                          columns=["sql_base", "area_terreno", "area_construida", "area_m2"])
    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet", columns=["sql_base", "cd_setor", "tipo", "classe", "exposicao"])
    c = cel.join(gen, on="sql_base", how="left").with_columns(
        pl.when(pl.col("area_terreno") > 0).then(pl.col("area_terreno")).otherwise(pl.col("area_m2")).alias("terreno"))
    c = c.with_columns(
        pl.when(pl.col("area_construida") > 0).then(pl.col("area_construida")).otherwise(pl.col("terreno")).alias("construida"))
    out = {}
    for nome, col in (("testada", "exposicao"), ("area_terreno", "terreno"), ("area_construida", "construida")):
        v = c.with_columns(pl.when(pl.col("classe") == "favela").then(pl.col("exposicao")).otherwise(pl.col(col))
                           .fill_null(0.0).alias("v"))
        w = v.pivot(on="tipo", index="cd_setor", values="v", aggregate_function="sum").fill_null(0.0)
        tipos = [n for n in names if _lotes([n])[0]]
        m = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0)
        out[nome] = np.column_stack([m[t].to_numpy() if t in m.columns else np.zeros(ids.height) for t in tipos])
    return out


def exposicao_lotes(ids, E, names, y_cel, n_boot: int = N_BOOT, log=print) -> dict:
    Y, fen = painel(ids)
    dist = ids["cd_dist"].to_numpy()
    lot = np.where(_lotes(names))[0]
    cols = lote_exposicao(ids, names)
    E_test = E.copy()
    E_test[:, lot] = cols["testada"] / 1000.0
    out = {"reconstrucao_testada_max_dif_km": float(np.abs(E_test - E).max()), "fenotipos": fen, "definicoes": {}}
    p0 = _perfil(E, Y, dist, n_boot=n_boot)
    S0c = _participacao(em_fit(E, y_cel)["lam"][:, None], E)[:, 0]
    for nome in ("area_terreno", "area_construida"):
        Ea = E.copy()
        Ea[:, lot] = cols[nome] / 1e6   # km²
        p = _perfil(Ea, Y, dist, n_boot=n_boot)
        Sc = _participacao(em_fit(Ea, y_cel)["lam"][:, None], Ea)[:, 0]
        out["definicoes"][nome] = {
            "celular_2025": {"spearman_partes": _rho(S0c, Sc), "spearman_partes_lotes": _rho(S0c[lot], Sc[lot]),
                             "partes": dict(zip(names, Sc)), "partes_testada": dict(zip(names, S0c)),
                             "ordem": [names[i] for i in np.argsort(-Sc)][:8],
                             "ordem_testada": [names[i] for i in np.argsort(-S0c)][:8]},
            "painel": _compara(p0, p, names, fen),
            "parte_lotes_painel": dict(zip(fen, p["S"][lot].sum(axis=0))),
            "parte_lotes_painel_testada": dict(zip(fen, p0["S"][lot].sum(axis=0)))}
        log(f"exposição dos lotes ({nome}): celular ρ = {out['definicoes'][nome]['celular_2025']['spearman_partes']:.2f}; "
            f"painel ρ mediano = {out['definicoes'][nome]['painel']['spearman_partes_mediana']:.2f}")
    return out


# --- 6. estabilidade dos 12 tipos finais ---------------------------------------------------------

def _funde(P: np.ndarray, lab: np.ndarray, min_share: float = 0.003) -> tuple[np.ndarray, int]:
    """A fusão de ``typing.run``: tipos com < 0,3% dos lotes vão, lote a lote, ao centróide grande mais próximo."""
    lab = lab.copy()
    ks, cnt = np.unique(lab, return_counts=True)
    small = ks[cnt < min_share * len(lab)]
    if len(small):
        big = ks[cnt >= min_share * len(lab)]
        cen = np.stack([P[lab == k].mean(0) for k in big])
        for k in small:
            m = lab == k
            lab[m] = big[np.argmin(((P[m][:, None, :] - cen[None]) ** 2).sum(-1), axis=1)]
    return np.unique(lab, return_inverse=True)[1], int(len(small))


def _vertical(lab: np.ndarray, alto: np.ndarray) -> np.ndarray:
    """A regra de ``typing.subcluster_vertical(parent=None)``: lote com ≥ 4 pavimentos ou ≥ 8 unidades, em
    qualquer tipo, vai para um tipo novo."""
    out = lab.copy()
    out[alto] = lab.max() + 1
    return out


def _cruzada(a: np.ndarray, b: np.ndarray) -> dict:
    """Tabela cruzada (contagens) de dois rótulos, como {a: {b: n}}."""
    t = pl.DataFrame({"a": a, "b": b}).group_by("a", "b").len()
    out: dict = {}
    for r in t.sort("a", "len", descending=[False, True]).iter_rows(named=True):
        out.setdefault(r["a"], {})[r["b"]] = int(r["len"])
    return out


def contra_publicada(log=print) -> dict:
    """ARI e tabela cruzada da tipagem gravada contra a publicada antes da refação (coluna ``tipo``)."""
    from sklearn.metrics import adjusted_rand_score as ari

    velho = processed_dir() / "_versoes" / VERSAO_PUBLICADA / f"lote_tipos_{REF_YEAR}.parquet"
    a = pl.read_parquet(guard.pre2026(velho), columns=["sql_base", "tipo"]).rename({"tipo": "publicada"})
    b = pl.read_parquet(atlas_dir() / f"lote_tipos_{REF_YEAR}.parquet", columns=["sql_base", "tipo"]).rename({"tipo": "nova"})
    j = a.join(b, on="sql_base", how="inner")
    cad = j.filter((pl.col("publicada") != "Sem cadastro") & (pl.col("nova") != "Sem cadastro"))
    cruz = _cruzada(j["publicada"].to_numpy(), j["nova"].to_numpy())
    destino = {k: max(v.items(), key=lambda t: t[1]) for k, v in cruz.items()}
    tot = {k: sum(v.values()) for k, v in cruz.items()}
    rep = {"lotes_comuns": int(j.height), "lotes_so_publicada": int(a.height - j.height), "lotes_so_nova": int(b.height - j.height),
           "ari_todos": float(ari(j["publicada"].to_numpy(), j["nova"].to_numpy())),
           "ari_com_cadastro": float(ari(cad["publicada"].to_numpy(), cad["nova"].to_numpy())),
           "tipos_publicada": int(j["publicada"].n_unique()), "tipos_nova": int(j["nova"].n_unique()),
           "destino_principal": {k: {"tipo_novo": d[0], "parte": d[1] / tot[k], "lotes": tot[k]} for k, d in destino.items()},
           "cruzada": cruz}
    log(f"tipagem nova × publicada: ARI {rep['ari_com_cadastro']:.3f} nos lotes com cadastro ({rep['lotes_comuns']:,} lotes comuns)")
    return rep


def estabilidade_tipos(resolucao: float = 0.02, n_rep: int = 8, size: int = 80_000, n_eval: int = 40_000, seed: int = 0,
                       n_ref: int = 80_000, min_floors: float = 4, min_units: float = 8, log=print) -> dict:
    """``typing.stability`` na resolução escolhida com o refinamento final em cada subamostra (fusão dos tipos
    com < 0,3% dos lotes e a regra vertical em todos os tipos). O ARI não depende de casar rótulos; o
    casamento com a tipagem gravada (maior sobreposição nos lotes de avaliação) só descreve os tipos."""
    from sklearn.metrics import adjusted_rand_score as ari

    from cityomics.atlas import typing as T

    g = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet")
    Z, gnames, mask, raw = T.prepare(g)
    gi = g.filter(pl.col("tem_iptu")).select("sql_base", "cd_dist", "pavimentos", "n_unidades")
    del g
    P, _ = T.pca(Z)
    del Z
    fin = gi.select("sql_base").join(pl.read_parquet(atlas_dir() / f"lote_tipos_{REF_YEAR}.parquet", columns=["sql_base", "cluster"]),
                                     on="sql_base", how="left")["cluster"].to_numpy()
    alto = ((gi["pavimentos"].fill_null(0).to_numpy() >= min_floors) | (gi["n_unidades"].fill_null(0).to_numpy() >= min_units))
    tn = pl.read_parquet(atlas_dir() / f"tipos_perfil_{REF_YEAR}.parquet", columns=["cluster", "nome"])
    nome_final = dict(zip(tn["cluster"].to_list(), tn["nome"].to_list()))
    # mesma sequência de typing.stability: avaliação primeiro, depois as subamostras da primeira resolução
    rng = np.random.default_rng(seed)
    ev = rng.choice(len(P), n_eval, replace=False)
    fin_ev = fin[ev]
    brutos, fundidos, finais, info = [], [], [], []
    for i in range(n_rep):
        t0 = time.time()
        sub = rng.choice(len(P), size, replace=False)
        lab = T.leiden(P[sub], resolucao, seed=i)
        brutos.append(T.transfer(P[sub], lab, P[ev])[0])
        labm, n_fund = _funde(P[sub], lab)
        tr = T.transfer(P[sub], labm, P[ev])[0]
        fundidos.append(tr)
        fz = _vertical(tr, alto[ev])
        finais.append(fz)
        mapa = {}
        for k in np.unique(fz):
            m = fz == k
            alvo = int(np.bincount(fin_ev[m] + 1).argmax() - 1)
            mapa[int(k)] = {"tipo_final": nome_final.get(alvo, str(alvo)), "lotes_avaliacao": int(m.sum()),
                            "concordancia": float(np.mean(fin_ev[m] == alvo))}
        info.append({"subamostra": i, "clusters_leiden": int(len(np.unique(lab))), "fundidos": n_fund,
                     "tipos_apos_refino": int(len(np.unique(fz))), "lotes_vertical_avaliacao": int(alto[ev].sum()),
                     "ari_bruto_vs_final": float(ari(brutos[-1], fin_ev)), "ari_refinado_vs_final": float(ari(fz, fin_ev)),
                     "mapa": mapa})
        log(f"subamostra {i}: {info[-1]['clusters_leiden']} clusters, {n_fund} fundidos, {info[-1]['tipos_apos_refino']} tipos; "
            f"ARI contra o final {info[-1]['ari_refinado_vs_final']:.3f} ({time.time() - t0:.0f} s)")

    def pares(labs):
        a = [ari(labs[i], labs[j]) for i in range(n_rep) for j in range(i + 1, n_rep)]
        return {"medio": float(np.mean(a)), "min": float(np.min(a)), "max": float(np.max(a))}

    # estabilidade por tipo final: Jaccard com o cluster que melhor o reproduz em cada subamostra
    jac = {}
    for t in np.unique(fin_ev):
        a = fin_ev == t
        js = [max(np.sum(a & (fz == k)) / np.sum(a | (fz == k)) for k in np.unique(fz[a])) for fz in finais]
        jac[nome_final.get(int(t), str(t))] = {"jaccard_mediano": float(np.median(js)), "jaccard_min": float(np.min(js)),
                                               "lotes_avaliacao": int(a.sum())}
    # reprodução da tipagem gravada (typing.run: referência estratificada por distrito, semente 0)
    ref = T.stratified_sample(gi["cd_dist"].cast(pl.String).fill_null("NA").to_numpy(), n_ref)
    lab_ref = T.leiden(P[ref], resolucao, seed=0)
    labm, n_fund = _funde(P[ref], lab_ref)
    fz = _vertical(T.transfer(P[ref], labm, P[ev])[0], alto[ev])
    registrado = json.loads((atlas_dir() / f"tipagem_{REF_YEAR}.json").read_text())
    reproducao = {"n_ref": int(len(ref)), "clusters_leiden": int(len(np.unique(lab_ref))), "fundidos": n_fund,
                  "tipos": int(len(np.unique(fz))), "ari_vs_final_registrado": float(ari(fz, fin_ev)),
                  "ari_medio_vs_subamostras": float(np.mean([ari(fz, f) for f in finais])),
                  "registrado": {"lotes_tipados": registrado.get("lotes_tipados"), "n_ref": registrado.get("n_ref"),
                                 "n_tipos": registrado.get("n_tipos"),
                                 "n_tipos_subamostras": registrado["estabilidade"][str(resolucao)]["n_tipos"],
                                 "ari_medio": registrado["estabilidade"][str(resolucao)]["ari_medio"],
                                 "ari_min": registrado["estabilidade"][str(resolucao)]["ari_min"],
                                 "vertical": registrado.get("subagrupamento_vertical")},
                  "lotes_com_iptu": int(len(P)), "genes_iguais_ao_registrado": gnames == registrado.get("genes")}
    log(f"reprodução da tipagem gravada: {reproducao['clusters_leiden']} clusters; ARI {reproducao['ari_vs_final_registrado']:.3f}")
    rep = {"resolucao": resolucao, "subamostras": n_rep, "tamanho": size, "avaliacao": n_eval,
           "regra": {"fusao_parte_min": 0.003, "vertical": {"pavimentos_min": min_floors, "unidades_min": min_units,
                                                            "tipos": "todos"}},
           "tipos_finais": int(len(np.unique(fin[fin >= 0]))), "reproducao_final": reproducao,
           "ari_pares_brutos": pares(brutos), "ari_pares_fundidos": pares(fundidos), "ari_pares_tipos_finais": pares(finais),
           "ari_contra_final": [d["ari_refinado_vs_final"] for d in info],
           "ari_contra_final_bruto": [d["ari_bruto_vs_final"] for d in info],
           "jaccard_por_tipo": jac, "subamostra": info}
    rep["contra_publicada"] = contra_publicada(log=log)
    log(f"estabilidade: brutos {rep['ari_pares_brutos']['medio']:.3f}; tipos finais {rep['ari_pares_tipos_finais']['medio']:.3f} "
        f"(mín {rep['ari_pares_tipos_finais']['min']:.3f}); contra o final {np.mean(rep['ari_contra_final']):.3f}")
    return rep


# --- 7. unidades ---------------------------------------------------------------------------------

def unidades(ids, E, names, y, n_boot: int = N_BOOT) -> dict:
    lam = em_fit(E, y)["lam"]
    km = _km(names)
    dist, mult = multiplicidades(ids["cd_dist"].to_numpy(), n_boot, seed=0)
    B, _ = em(E, y, ycol=np.zeros(n_boot, int), dist=dist, mult=mult)
    lo = np.percentile(B, 2.5, axis=1)

    def amp(v):
        return {"max": float(v.max()), "min": float(v.min()), "razao": float(v.max() / v.min()),
                "ordens_de_grandeza": float(np.log10(v.max() / v.min()))}

    lk, nk = lam[km], [n for n, k in zip(names, km) if k]
    firme = lo[km] > 0.01 * lam[km]   # classes cujo limite inferior não encosta em zero
    return {"km": amp(lk) | {"classe_max": nk[int(np.argmax(lk))], "classe_min": nk[int(np.argmin(lk))]},
            "km_classes_com_ic_longe_de_zero": amp(lk[firme]) | {"classes_excluidas": [n for n, f in zip(nk, firme) if not f]},
            "km_razao_bootstrap": _q(B[km].max(axis=0) / np.maximum(B[km].min(axis=0), 1e-12)),
            "km_abaixo_de_1": [n for n, v in zip(nk, lk) if v < 1],
            "estacoes": {n: float(v) for n, v, k in zip(names, lam, km) if not k} | amp(lam[~km]),
            "misturando_unidades": amp(lam)}


# --- execução ------------------------------------------------------------------------------------

PARTES = ("condicionamento", "unidades", "metades", "favelas", "exposicao_lotes", "simulacao", "tipos")
# ensaio curto (``--rapido``): só confere que o código roda de ponta a ponta; os números não valem
RAPIDO = {"n_boot": 10, "n_sim": 4, "cob_sim": 2, "cob_boot": 10, "sementes": (0,),
          "tipos": {"n_rep": 2, "size": 10_000, "n_eval": 5_000, "n_ref": 10_000}}


def run(log=print, partes=PARTES, rapido: bool = False, saida=None) -> dict:
    """Roda as partes pedidas e grava o JSON (as partes não pedidas ficam como estavam no arquivo).

    ``rapido`` usa poucas réplicas e reamostras e grava em ``saida`` (obrigatório), nunca no JSON oficial."""
    from pathlib import Path

    if rapido and saida is None:
        raise ValueError("o ensaio rápido precisa de um caminho de saída fora do JSON oficial")
    path = Path(saida) if saida is not None else out_dir() / SAIDA
    cfg = RAPIDO if rapido else {"n_boot": N_BOOT, "n_sim": N_SIM, "cob_sim": COB_SIM, "cob_boot": COB_BOOT,
                                 "sementes": SEMENTES, "tipos": {}}
    rep = json.loads(path.read_text()) if path.exists() else {}
    if set(partes) - {"tipos"}:   # a tipagem não usa E nem crime
        ids, E, names = setor_exposicao()
        y = celular_setor(ids, (2025,))
        rep["base"] = {"setores": int(ids.height), "classes": names, "celular_2025": float(y.sum()), "anos_painel": list(ANOS),
                       "exposicao_total": dict(zip(names, E.sum(axis=0))), "rapido": rapido,
                       "data": time.strftime("%Y-%m-%d %H:%M")}
    nb = cfg["n_boot"]
    for p in partes:
        t0 = time.time()
        if p == "condicionamento":
            rep[p] = condicionamento(ids, E, names, y, n_boot=nb, log=log)
        elif p == "unidades":
            rep[p] = unidades(ids, E, names, y, n_boot=nb)
        elif p == "metades":
            ev = eventos_geo(log=log)
            rep[p] = metades(ids, E, names, ev, ligacao(ev, log=log), sementes=cfg["sementes"], log=log)
        elif p == "favelas":
            rep[p] = favelas(ids, E, names, n_boot=nb, log=log)
        elif p == "exposicao_lotes":
            rep[p] = exposicao_lotes(ids, E, names, y, n_boot=nb, log=log)
        elif p == "simulacao":
            rep[p] = simulacao(ids, E, names, y, n_sim=cfg["n_sim"], cob_sim=cfg["cob_sim"], cob_boot=cfg["cob_boot"], log=log)
        elif p == "tipos":
            rep[p] = estabilidade_tipos(log=log, **cfg["tipos"])
        else:
            raise ValueError(f"parte desconhecida: {p}")
        log(f"[{p}] {time.time() - t0:.0f} s")
        path.write_text(json.dumps(_f(rep), ensure_ascii=False, indent=1))
    return rep


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Identificação da atribuição (parecer R3, R4, R10, R12)")
    ap.add_argument("partes", nargs="*", default=list(PARTES), help=f"partes a rodar (padrão: todas): {', '.join(PARTES)}")
    ap.add_argument("--rapido", action="store_true", help="ensaio curto, só para conferir o código")
    ap.add_argument("--saida", default=None, help="JSON de saída (obrigatório com --rapido)")
    a = ap.parse_args()
    run(log=lambda s: print(s, flush=True), partes=tuple(a.partes), rapido=a.rapido, saida=a.saida)
