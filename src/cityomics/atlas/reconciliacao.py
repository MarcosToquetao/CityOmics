"""Reconciliação como parte da mensuração: imputação, nulos calibrados e ocultação (parecer R1, R2, R4, R8).

Pedido do parecer crítico (``paper/review/parecer/00_parecer_original.md``; plano em
``paper/03_plano_parecer.md``, Agente A). A reconciliação de produção (``units.reconcile``) reparte os
eventos sem coordenada de cada distrito × estrato × mês entre os setores do distrito pela proporção dos
geocodificados do mesmo estrato nos 12 meses anteriores e grava o valor esperado (contagem fracionária).
Aqui a reconciliação é tratada como parte da mensuração:

1. **Imputação multinomial (R2):** ``reconcile_draw`` reparte os u eventos de cada célula por sorteio
   multinomial com as mesmas frações (contagens inteiras; a média é a produção). Com M = 20 imputações
   recalculam-se λ de 2025, a decomposição da persistência, o teto de ruído, o R² do ensemble e o teste
   de dispersão.
2. **Calibração do teste de dispersão (R8):** nulo de Poisson puro nas médias observadas e nulo que passa
   pelo pipeline (Poisson por setor × estrato × mês → geocodificado ou não → reconciliação de produção).
3. **Ocultação (R4/R2):** esconde a coordenada de eventos geocodificados (ao acaso dentro do estrato e em
   dois cenários não aleatórios), reconcilia e compara com a verdade.
4. **Repontuação do benchmark (R2):** CRPS e captura contra o y reconciliado, o y imputado e o y
   geocodificado (previsões multiplicadas pela fração geocodificada as-of do setor).
5. **Onde mora a variação mensal (R1):** teto de ruído e R² do ensemble dentro do setor por terço de
   contagem média.
6. **CRPS de y real (R2b):** ``scores.crps_nb`` com y fracionário devolve o CRPS de ⌈y⌉; ``crps_nb_real``
   é o CRPS correto e ``repontua_crps`` refaz o benchmark gravado de 2025 com as três versões.

Só os 77 distritos de exploração (D53) e nada de 2026. A reconciliação de um distrito só usa eventos e
setores do próprio distrito, então restringir à exploração antes de reconciliar não muda nenhum número
dos setores de exploração (conferido contra ``celular_setor_mes.parquet`` em ``run``). A única exceção é
``repontua_crps``, que repontua também nos 96 distritos as previsões já gravadas do benchmark, porque esse
é o escopo do número publicado (o benchmark é anterior ao cofre espacial); nada do atlas usa o cofre.

Saídas em ``data/processed/atlas/fenotipo/``: ``reconciliacao.json`` (só agregados) e
``reconciliacao_imputacoes.parquet`` (setor × mês; local, D49).
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import polars as pl
from scipy.special import expit
from scipy.stats import chi2, spearmanr

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import out_dir, setor_exposicao
from cityomics.atlas.memoria import MIN_ESPERADO, decompoe
from cityomics.atlas.previsibilidade import dispersao, medidas, teto_sem_modelo
from cityomics.paths import interim_dir, processed_dir
from cityomics.units.reconcile import ALPHA, WINDOW

M_IMPUT = 20
ANOS = (2022, 2023, 2024, 2025)
ALFA_TESTE = 0.05
MODELOS = ("media_historica", "glm", "gnn", "lgbm_completo", "ensemble")
PARTES = ("tecido", "memoria_estavel", "transitoria", "covariancia")


# --- núcleo: a reconciliação de produção sobre matrizes ------------------------------------------

def _janela(c: np.ndarray) -> np.ndarray:
    """Cópia de ``reconcile._window_sums`` no último eixo (meses): soma dos WINDOW meses anteriores;
    nos WINDOW primeiros meses, a soma dos WINDOW primeiros meses."""
    c = np.asarray(c, dtype=float)
    P = c.shape[-1]
    csum = np.concatenate([np.zeros(c.shape[:-1] + (1,)), np.cumsum(c, axis=-1)], axis=-1)
    out = np.empty_like(c)
    first = csum[..., min(WINDOW, P)]
    for j in range(P):
        out[..., j] = csum[..., j] - csum[..., j - WINDOW] if j >= WINDOW else first
    return out


def _prior(G_tot: np.ndarray, sd: np.ndarray, pop: np.ndarray, D: int) -> np.ndarray:
    """Fração do setor nos geocodificados do distrito na janela; sem histórico, a da população."""
    W_all = _janela(G_tot)
    W_d = np.zeros((D, W_all.shape[1]))
    np.add.at(W_d, sd, W_all)
    den = W_d[sd]
    prior = np.divide(W_all, den, out=np.full_like(W_all, np.nan), where=den != 0)
    pop_d = np.bincount(sd, weights=np.nan_to_num(pop), minlength=D)[sd]
    ps = np.divide(pop, pop_d, out=np.full(len(pop), np.nan), where=pop_d > 0)
    ps = np.where(np.isnan(ps), 1.0 / np.bincount(sd, minlength=D)[sd], ps)
    return np.where(np.isnan(prior), ps[:, None], prior)


def _multinomial(rng, u: np.ndarray, share: np.ndarray) -> np.ndarray:
    """Sorteio de u[t] eventos entre os membros com probabilidades share[:, t] (membros × meses)."""
    p = share / share.sum(axis=0, keepdims=True)
    p[-1] = np.clip(1.0 - p[:-1].sum(axis=0), 0.0, None)
    return rng.multinomial(u.astype(np.int64), p.T).T


def reparte(G_tot, G, U, sd, pop, eleg=None, rng=None, n_draws: int = 0, por_estrato: bool = False) -> dict:
    """Reconciliação de produção (``units.reconcile.reconcile``) sobre matrizes.

    ``G_tot`` (S × P): geocodificados por setor; ``G`` (S × K × P): os mesmos por estrato; ``U`` (D × K × P):
    sem coordenada por distrito e estrato; ``sd`` (S): índice do distrito de cada setor; ``pop`` (S);
    ``eleg``: {k: máscara S} de setores elegíveis para o estrato k. Devolve ``esperado`` (S × P, a produção),
    ``sorteios`` (n_draws × S × P, inteiros, mesmas frações) e, se pedido, ``esperado_estrato`` (S × K × P)."""
    S, K, P = G.shape
    D = U.shape[0]
    prior = _prior(G_tot, sd, pop, D)
    W_st = _janela(G)
    out = {"esperado": np.zeros((S, P))}
    if n_draws:
        out["sorteios"] = np.zeros((n_draws, S, P), dtype=np.int32)
    if por_estrato:
        out["esperado_estrato"] = np.zeros((S, K, P))
    membros_d = [np.where(sd == d)[0] for d in range(D)]
    for d in range(D):
        for k in range(K):
            u = U[d, k]
            if u.sum() == 0 or len(membros_d[d]) == 0:
                continue
            mem = membros_d[d]
            if eleg and k in eleg:
                r = mem[eleg[k][mem]]
                mem = r if len(r) else mem
            p = prior[mem]
            tot = p.sum(axis=0)
            p = np.divide(p, tot, out=np.full_like(p, np.nan), where=tot != 0)
            p = np.where(np.isnan(p), 1.0 / len(mem), p)
            w = W_st[mem, k, :]
            share = (w + ALPHA * p) / (w.sum(axis=0) + ALPHA)
            out["esperado"][mem] += share * u
            if por_estrato:
                out["esperado_estrato"][mem, k] += share * u
            for b in range(n_draws):
                out["sorteios"][b, mem] += _multinomial(rng, u, share).astype(np.int32)
    return out


def malha(ev: pd.DataFrame, setores: pd.DataFrame, freq: str = "M", eligible: dict[str, set] | None = None) -> dict:
    """Eventos atribuídos → matrizes de ``reparte`` com as mesmas regras de ``units.reconcile``."""
    ev = ev[ev["cd_dist"].notna() & ev["data_fato"].notna()]
    per = ev["data_fato"].dt.to_period(freq)
    periods = pd.period_range(per.min(), per.max(), freq=freq)
    pidx = pd.Series(np.arange(len(periods)), index=periods)
    cd = setores["cd_setor"].astype(str).to_numpy()
    dists, sd = np.unique(setores["cd_dist"].astype(str).to_numpy(), return_inverse=True)
    estratos = sorted(ev["estrato"].dropna().unique().tolist())
    S, D, K, P = len(cd), len(dists), len(estratos), len(periods)
    spos = pd.Series(np.arange(S), index=cd)
    dpos = pd.Series(np.arange(D), index=dists)
    kpos = pd.Series(np.arange(K), index=estratos)
    t = per.map(pidx).to_numpy()
    geo = ev["cd_setor"].notna().to_numpy()
    s = ev["cd_setor"].astype("string").map(spos).to_numpy()
    k = ev["estrato"].map(kpos).to_numpy()
    G_tot = np.zeros((S, P))
    ok = geo & ~pd.isna(s)
    np.add.at(G_tot, (s[ok].astype(int), t[ok]), 1.0)
    G = np.zeros((S, K, P))
    okk = ok & ~pd.isna(k)
    np.add.at(G, (s[okk].astype(int), k[okk].astype(int), t[okk]), 1.0)
    U = np.zeros((D, K, P))
    dd = ev["cd_dist"].astype(str).map(dpos).to_numpy()
    oku = ~geo & ~pd.isna(dd) & ~pd.isna(k)
    np.add.at(U, (dd[oku].astype(int), k[oku].astype(int), t[oku]), 1.0)
    eleg = {int(kpos[st]): np.isin(cd, list(m)) for st, m in (eligible or {}).items() if st in kpos.index}
    pop = setores["pop_2022"].astype(float).clip(lower=0).to_numpy()
    return {"cd_setor": cd, "cd_dist": dists[sd], "sd": sd, "pop": pop, "estratos": estratos,
            "periodos": [str(p) for p in periods], "G_tot": G_tot, "G": G, "U": U, "eleg": eleg}


def _quadro(m: dict, alocado: np.ndarray) -> pd.DataFrame:
    S, P = alocado.shape
    out = pd.DataFrame({"cd_setor": np.repeat(m["cd_setor"], P), "periodo": np.tile(m["periodos"], S),
                        "n_geo": m["G_tot"].ravel().astype(int), "n_alocado": alocado.ravel()})
    out["cd_dist"] = np.repeat(m["cd_dist"], P)
    out["n_total"] = out["n_geo"] + out["n_alocado"]
    return out


def reconcile_esperado(ev, setores, freq: str = "M", eligible=None) -> pd.DataFrame:
    """A produção (valor esperado), pelo núcleo vetorizado; mesmo formato de ``reconcile.reconcile``."""
    m = malha(ev, setores, freq, eligible)
    return _quadro(m, reparte(m["G_tot"], m["G"], m["U"], m["sd"], m["pop"], m["eleg"])["esperado"])


def reconcile_draw(ev, setores, rng, freq: str = "M", eligible=None) -> pd.DataFrame:
    """Uma imputação: cópia da reconciliação de produção em que os u eventos de cada distrito × estrato ×
    mês são repartidos por sorteio multinomial com as mesmas frações (n_alocado inteiro; a média sobre
    sorteios é a produção e o total do distrito em cada mês é preservado)."""
    m = malha(ev, setores, freq, eligible)
    r = reparte(m["G_tot"], m["G"], m["U"], m["sd"], m["pop"], m["eleg"], rng=rng, n_draws=1)
    return _quadro(m, r["sorteios"][0].astype(float))


# --- dados de exploração -------------------------------------------------------------------------

def _eventos() -> pd.DataFrame:
    ev = pd.read_parquet(guard.pre2026(interim_dir() / "eventos_celular_atribuidos.parquet"),
                         columns=["cd_setor", "cd_dist", "estrato", "data_fato"])
    ev = ev[(ev["data_fato"] >= "2022-01-01") & (ev["data_fato"] < "2026-01-01") & ev["cd_dist"].notna()]
    return ev[guard.explore_mask(ev["cd_dist"].astype(str).to_numpy())].reset_index(drop=True)


def _setores():
    from cityomics.units.setores import load_setores

    s = load_setores()
    return s[guard.explore_mask(s["cd_dist"].astype(str).to_numpy())].reset_index(drop=True)


def _perto_estacao(setores) -> set[str]:
    """Setores a até 250 m de estação (regra de ``units.build``), só com as camadas já em cache local."""
    from cityomics.external import external_dir
    from cityomics.units import transit

    for layer in transit.LAYERS:
        f = external_dir() / "geosampa" / f"{layer.split(':')[-1]}.geojson"
        if not f.exists():
            raise FileNotFoundError(f"camada sem cache local (esta análise não baixa nada): {f}")
    return transit.station_setores(setores, transit.load_stations(log=lambda *a: None))


def malha_exploracao() -> dict:
    s = _setores()
    return malha(_eventos(), s, "M", {"trilhos": _perto_estacao(s)})


def _soma_distrito(X: np.ndarray, sd: np.ndarray, D: int) -> np.ndarray:
    """Soma das linhas (setores) por distrito, para arrays S × ..."""
    from scipy.sparse import csr_matrix

    A = csr_matrix((np.ones(len(sd)), (sd, np.arange(len(sd)))), shape=(D, len(sd)))
    return (A @ X.reshape(len(sd), -1)).reshape((D,) + X.shape[1:])


# --- resumos e testes ----------------------------------------------------------------------------

def _resumo(v) -> dict:
    v = np.asarray(v, dtype=float)
    return {"media": float(np.mean(v)), "p2_5": float(np.percentile(v, 2.5)), "p97_5": float(np.percentile(v, 97.5))}


def _rejeicao(Y: np.ndarray, alpha: float = ALFA_TESTE) -> dict:
    """Teste de dispersão de ``previsibilidade.dispersao`` numa matriz setor × mês: Σ(y − ȳ)²/ȳ contra
    χ²(n − 1), nos setores com ȳ > 0 e nos com ȳ ≥ 1."""
    n = Y.shape[1]
    m = Y.mean(axis=1)
    ss = ((Y - m[:, None]) ** 2).sum(axis=1)
    ok = m > 0
    rej = np.zeros(len(m), bool)
    rej[ok] = ss[ok] / m[ok] > chi2.ppf(1 - alpha, n - 1)
    alto = m >= 1
    return {"todos": float(rej[ok].mean()), "ge1": float(rej[alto].mean()) if alto.any() else float("nan"),
            "n_todos": int(ok.sum()), "n_ge1": int(alto.sum())}


def _resumo_rejeicao(fr: list[dict]) -> dict:
    return {k: _resumo([f[k] for f in fr]) for k in ("todos", "ge1", "n_todos", "n_ge1")}


def crps_nb_real(y, mu, phi, crps_teto: np.ndarray | None = None) -> np.ndarray:
    """CRPS da NB2 contra y real, ∫ (F(x) − 1{x ≥ y})² dx: no intervalo [j, j + 1) que contém y o termo é
    (y − j)·F(j)² + (j + 1 − y)·(F(j) − 1)², o que dá a interpolação linear entre o CRPS de ⌊y⌋ e o de ⌈y⌉
    (igual a E|X − y| − ½E|X − X'|).

    ``scores.crps_nb`` (e a fórmula de §5.3 do pré-registro) usa F(j)² no intervalo inteiro e devolve o CRPS
    de ⌈y⌉; a correção é − (⌈y⌉ − y)·(2F(⌊y⌋) − 1). ``crps_teto`` reaproveita ``scores.crps_nb`` já calculado."""
    from scipy.stats import nbinom

    from cityomics.eval import scores

    y = np.asarray(y, dtype=float)
    n, p = scores.nb_scipy(mu, phi)
    c = scores.crps_nb_registrado(y, mu, phi) if crps_teto is None else crps_teto
    return c - (np.ceil(y) - y) * (2 * nbinom.cdf(np.floor(y), n, p) - 1)


def crps_nb_teto(y, mu, phi) -> np.ndarray:
    """O CRPS da fórmula registrada (``scores.crps_nb_registrado``), que com y fracionário é o CRPS de ⌈y⌉."""
    from cityomics.eval import scores

    return scores.crps_nb_registrado(y, mu, phi)


def crps_nb_arredondado(y, mu, phi) -> np.ndarray:
    from cityomics.eval import scores

    return scores.crps_nb(np.rint(np.asarray(y, dtype=float)), mu, phi)


def verifica_crps(casos=((0.03, 0.5, 3.0), (0.6, 0.5, 3.0), (1.3, 2.0, 3.0), (2.0, 2.0, 3.0)), n_mc: int = 400_000,
                  seed: int = 51) -> list[dict]:
    """Conferência numérica: CRPS de y real por Monte Carlo (E|X − y| − ½E|X − X'|) e por integral numérica,
    contra ``crps_nb_real`` e contra o CRPS da produção (``scores.crps_nb``)."""
    from scipy.stats import nbinom

    from cityomics.eval import scores

    rng = np.random.default_rng(seed)
    dx = 2e-4
    x = np.arange(0.0, 80.0, dx) + dx / 2
    out = []
    for y, mu, phi in casos:
        n, p = scores.nb_scipy(mu, phi)
        X, X2 = rng.negative_binomial(n, p, size=n_mc), rng.negative_binomial(n, p, size=n_mc)
        F = nbinom.cdf(np.floor(x), n, p)
        out.append({"y": y, "mu": mu, "phi": phi,
                    "monte_carlo": float(np.mean(np.abs(X - y)) - 0.5 * np.mean(np.abs(X - X2))),
                    "integral": float(((F - (x >= y)) ** 2).sum() * dx),
                    "crps_nb_real": float(crps_nb_real(np.array([y]), np.array([mu]), phi)[0]),
                    "producao": float(scores.crps_nb_registrado(np.array([y]), np.array([mu]), phi)[0]),
                    "producao_em_teto_y": float(scores.crps_nb(np.array([np.ceil(y)]), np.array([mu]), phi)[0])})
    return out


def repontua_crps(n_boot: int = 2000, log=print) -> dict:
    """Repontuação das previsões gravadas de 2025 (``pred_dev_eval.parquet``, ensemble reconstruído) com
    três CRPS: o da produção (⌈y⌉), o de y real (correto) e o de y arredondado. Em dois recortes: os 96
    distritos, o escopo do benchmark original (desenvolvimento, rodado antes do cofre espacial; nada do
    atlas é calculado aqui), e os 77 de exploração. Para cada um: CRPS médio e ordem dos modelos, melhor
    baseline e melhor modelo de outras áreas (regra de ``select_run``), cada modelo contra o GLM (bootstrap
    por distrito, 2.000 reamostras, como a Fig. 6d) e o H1a de desenvolvimento com Holm junto do H1b."""
    from cityomics.eval import inference
    from cityomics.models import select_run
    from cityomics.units.setores import load_setores

    for f in ("pred_dev_eval.parquet", "pred_dev_val.parquet", "resultados_benchmark_dev.json"):
        guard.pre2026(processed_dir() / "modelo" / f)
    s = load_setores()
    tab = pl.DataFrame({"cd_setor": s["cd_setor"].astype(str).to_numpy(), "cd_dist": s["cd_dist"].astype(str).to_numpy()})
    ev, mu, phi, dist = select_run.load(tab, "dev")
    dist = np.asarray(dist).astype(str)
    y = ev["y"].to_numpy().astype(float)
    sel = json.loads(guard.pre2026(guard.REPO_ROOT / "prereg" / "selection_dev.json").read_text())
    p_h1b = sel["h1b"]["p"]
    t0 = time.time()
    c = {"producao": {}, "real": {}, "arredondado": {}}
    for k in mu:
        c["producao"][k] = crps_nb_teto(y, mu[k], phi[k])
        c["real"][k] = crps_nb_real(y, mu[k], phi[k], crps_teto=c["producao"][k])
        c["arredondado"][k] = crps_nb_arredondado(y, mu[k], phi[k])
    log(f"CRPS de {len(mu)} modelos × 3 versões em {len(y):,} linhas: {time.time() - t0:.0f}s")
    recortes = {"96_distritos": np.ones(len(y), bool), "exploracao": guard.explore_mask(dist)}
    out = {"modelos": sorted(mu), "linhas": {r: int(v.sum()) for r, v in recortes.items()},
           "fracao_y_fracionario": float(np.mean(np.abs(y - np.rint(y)) > 1e-9)),
           "fracao_y_entre_0_e_1": float(np.mean((y > 1e-9) & (y < 1 - 1e-9))),
           "p_h1b_dev": p_h1b}
    for rn, msk in recortes.items():
        out[rn] = {}
        for vn, cv in c.items():
            med = {k: float(v[msk].mean()) for k, v in cv.items()}
            ordem = sorted(med, key=med.get)
            base = min(select_run.BASELINES, key=med.get)
            cross = min(select_run.CROSS, key=med.get)
            contra_glm = {k: inference.cluster_bootstrap_diff(cv[k][msk], cv["glm"][msk], dist[msk], n_boot)
                          for k in mu if k != "glm"}
            vs_base = {k: inference.cluster_bootstrap_diff(cv[k][msk], cv[base][msk], dist[msk], n_boot) for k in select_run.CROSS}
            holm = inference.holm({k: t["p"] for k, t in vs_base.items()})
            h1a = vs_base[cross]
            h1 = inference.holm({"H1a": h1a["p"], "H1b": p_h1b})
            out[rn][vn] = {"crps_medio": med, "ordem": ordem, "melhor_baseline": base, "melhor_outras_areas": cross,
                           "melhor_modelo_unico": next(k for k in ordem if k != "ensemble"),
                           "contra_glm": {k: v | {"relativo": v["diff"] / med["glm"]} for k, v in contra_glm.items()},
                           "contra_melhor_baseline_holm": {k: {"diff": vs_base[k]["diff"], **holm[k]} for k in vs_base},
                           "h1a_dev": h1a | {"relativo": h1a["diff"] / med[base], "p_adj_holm_com_h1b": h1["H1a"]["p_adj"],
                                             "apoia": bool(h1["H1a"]["reject"] and h1a["diff"] < 0)}}
        log(f"repontuação {rn}: " + "; ".join(f"{vn}: melhor {out[rn][vn]['melhor_outras_areas']} contra {out[rn][vn]['melhor_baseline']} "
                                              f"{out[rn][vn]['h1a_dev']['diff']:+.4f}" for vn in c))
    return out


# --- 2. imputações: λ, persistência, teto, R² e dispersão ----------------------------------------

def _versoes(m: dict, r: dict) -> dict[str, np.ndarray]:
    """Contagens mensais (S × P) de cada versão: produção (esperado), só geocodificado e imputações."""
    v = {"producao": m["G_tot"] + r["esperado"], "geocodificado": m["G_tot"].copy()}
    for b in range(r["sorteios"].shape[0]):
        v[f"imp{b:02d}"] = m["G_tot"] + r["sorteios"][b]
    return v


def _imps(V: dict) -> list[str]:
    return [k for k in V if k.startswith("imp")]


def _anos(m: dict) -> np.ndarray:
    return np.array([int(p[:4]) for p in m["periodos"]])


def _anual(Y: np.ndarray, m: dict, ordem: np.ndarray) -> np.ndarray:
    a = _anos(m)
    return np.column_stack([Y[ordem][:, a == ano].sum(axis=1) for ano in ANOS])


def _d2(E: np.ndarray, y: np.ndarray, lam: np.ndarray) -> float:
    """D² de ``attribution.run``: desvio explicado contra uma contagem constante por setor."""
    mu = E @ lam
    with np.errstate(divide="ignore", invalid="ignore"):
        dev_null = 2 * np.sum(np.where(y > 0, y * np.log(y / y.mean()), 0) - (y - y.mean()))
        dev = 2 * np.sum(np.where(y > 0, y * np.log(np.clip(y, 1e-12, None) / np.clip(mu, 1e-12, None)), 0) - (y - mu))
    return float(1 - dev / dev_null)


def atribuicao_2025(E: np.ndarray, names: list[str], Y25: dict) -> dict:
    lam = {k: em_fit_multi(E, y[:, None])[:, 0] for k, y in Y25.items()}
    imp = [k for k in Y25 if k.startswith("imp")]
    rho = lambda a, b: float(spearmanr(a, b).statistic)  # noqa: E731
    out = {"producao": {"d2": _d2(E, Y25["producao"], lam["producao"]), "eventos": float(Y25["producao"].sum())},
           "geocodificado": {"d2": _d2(E, Y25["geocodificado"], lam["geocodificado"]),
                             "spearman_com_producao": rho(lam["geocodificado"], lam["producao"]),
                             "eventos": float(Y25["geocodificado"].sum())},
           "imputacoes": {"d2": _resumo([_d2(E, Y25[k], lam[k]) for k in imp]),
                          "spearman_com_producao": _resumo([rho(lam[k], lam["producao"]) for k in imp])}}
    bfile = guard.pre2026(processed_dir() / "atlas" / "atribuicao_celular_2025.parquet")
    boot = pl.read_parquet(bfile) if bfile.exists() else None
    classes, larg = {}, []
    for k, nm in enumerate(names):
        L = np.array([lam[i][k] for i in imp])
        c = {"producao": float(lam["producao"][k]), "geocodificado": float(lam["geocodificado"][k]), "imputacoes": _resumo(L)}
        if boot is not None:
            b = boot.filter(pl.col("classe") == nm)
            lo, hi = float(b["lambda_ic_lo"][0]), float(b["lambda_ic_hi"][0])
            c["ic_bootstrap_distrito"] = [lo, hi]
            if hi > lo:
                c["largura_imputacao_sobre_bootstrap"] = float((np.percentile(L, 97.5) - np.percentile(L, 2.5)) / (hi - lo))
                larg.append(c["largura_imputacao_sobre_bootstrap"])
        classes[nm] = c
    out["classes"] = classes
    out["largura_imputacao_sobre_bootstrap_mediana"] = float(np.median(larg)) if larg else None
    out["largura_imputacao_sobre_bootstrap_max"] = float(np.max(larg)) if larg else None
    return out


def _persistencia(E: np.ndarray, Y: np.ndarray) -> dict:
    """Mesma seleção de ``robustez.persistencia_geocodificada`` (≥ 1 esperado por ano) e de ``memoria``
    para os setores altos (≥ 10 esperados por ano)."""
    M = E @ em_fit_multi(E, Y)
    keep = M.mean(axis=1) >= MIN_ESPERADO
    d = decompoe(Y[keep], M[keep])
    alto = M.mean(axis=1) >= 10
    da = decompoe(Y[alto], M[alto])
    return {"setores": int(keep.sum()), **{p: d["partes"][p] for p in PARTES},
            "residuo_lag1": d["persistencia_residuo"][1], "residuo_lag3": d["persistencia_residuo"][3],
            "setores_altos": int(alto.sum()), "altos_tecido": da["partes"]["tecido"],
            "altos_memoria_estavel": da["partes"]["memoria_estavel"]}


def persistencia(E: np.ndarray, Yanual: dict) -> dict:
    res = {k: _persistencia(E, Y) for k, Y in Yanual.items()}
    imp = [k for k in res if k.startswith("imp")]
    chaves = [c for c in res["producao"]]
    return {"producao": res["producao"], "geocodificado": res["geocodificado"],
            "imputacoes": {c: _resumo([res[k][c] for k in imp]) for c in chaves}}


def _previsoes(m: dict) -> dict:
    """Previsões de 2025 (h = 1, ajustadas em 2023–2024) dos modelos de ``MODELOS``, com o ensemble
    reconstruído como em ``select_run.load``; só setores de exploração, em matrizes setor × mês na ordem
    da malha."""
    from cityomics.models import select_run
    from cityomics.units.setores import load_setores

    for f in ("pred_dev_eval.parquet", "pred_dev_val.parquet", "resultados_benchmark_dev.json"):
        guard.pre2026(processed_dir() / "modelo" / f)
    s = load_setores()
    tab = pl.DataFrame({"cd_setor": s["cd_setor"].astype(str).to_numpy(), "cd_dist": s["cd_dist"].astype(str).to_numpy()})
    ev, mu, phi, dist = select_run.load(tab, "dev")
    keep = guard.explore_mask(np.asarray(dist).astype(str))
    ev = ev.filter(pl.Series(keep))
    pos = pd.Series(np.arange(len(m["cd_setor"])), index=m["cd_setor"])
    i = pos.reindex(ev["cd_setor"].to_list()).to_numpy()
    meses = sorted(set(ev["mes"].to_list()))
    j = np.array([meses.index(x) for x in ev["mes"].to_list()])
    assert not np.isnan(i).any() and len(meses) == 12
    i = i.astype(int)
    S = len(m["cd_setor"])
    assert len(np.unique(i)) == S and ev.height == S * 12

    def mat(v):
        out = np.full((S, 12), np.nan)
        out[i, j] = v
        return out

    area = np.zeros(S)
    area[i] = ev["area_km2"].to_numpy()
    return {"mu": {k: mat(mu[k][keep]) for k in MODELOS}, "phi": {k: float(phi[k]) for k in MODELOS},
            "y": mat(ev["y"].to_numpy()), "area": area, "meses": meses,
            "dist": pd.Series(np.asarray(dist).astype(str)[keep]).groupby(i).first().reindex(range(S)).to_numpy()}


def _grade(S: int, n: int = 12) -> tuple[np.ndarray, np.ndarray]:
    return np.repeat(np.arange(S), n), np.tile(np.arange(1, n + 1), S)


def ruido_e_dispersao(V: dict, pv: dict) -> dict:
    """(c) teto de ruído e R² do ensemble (setor × mês 2025, entre + dentro e dentro dos setores);
    (d) fração de setores que rejeitam Poisson."""
    S = pv["y"].shape[0]
    unit, per = _grade(S)
    mu = pv["mu"]["ensemble"].ravel()
    res = {}
    for k, Y in V.items():
        y = Y[:, -12:]
        t = teto_sem_modelo(y.ravel(), unit, per)
        r = medidas(mu, y.ravel(), unit, per)
        res[k] = {"teto_total": t["onde_e_quando"], "teto_dentro": t["quando"], "r2_total": r["onde_e_quando"] ** 2,
                  "r2_dentro": r["quando"] ** 2, "fracao_do_teto_total": r["onde_e_quando"] ** 2 / t["onde_e_quando"],
                  "fracao_do_teto_dentro": r["quando"] ** 2 / t["quando"], **{f"rejeita_{a}": b for a, b in _rejeicao(y).items()}}
    imp = _imps(V)
    chaves = list(res["producao"])
    return {"producao": res["producao"], "geocodificado": res["geocodificado"],
            "imputacoes": {c: _resumo([res[k][c] for k in imp]) for c in chaves}}


# --- 3. calibração do teste de dispersão -------------------------------------------------------

def nulo_poisson(medias: np.ndarray, n_rep: int = 200, seed: int = 31) -> dict:
    """12 meses de Poisson na média mensal observada de cada setor (com ≥ 1 evento) e o mesmo teste."""
    rng = np.random.default_rng(seed)
    mu = medias[medias > 0]
    fr = [_rejeicao(rng.poisson(mu[:, None], size=(len(mu), 12)).astype(float)) for _ in range(n_rep)]
    return {"setores": int(len(mu)), "replicas": n_rep, **_resumo_rejeicao(fr)}


def nulo_pipeline(m: dict, esperado_estrato: np.ndarray, n_rep: int = 200, seed: int = 32) -> dict:
    """Nulo que passa pela reconciliação: eventos Poisson por setor × estrato × mês com taxa constante em
    2024–2025 (a contagem reconciliada de 2025 do estrato), cada um geocodificado com a fração observada
    do distrito × estrato em 2025 (ausência ao acaso dentro do estrato, a hipótese da reconciliação), os
    não geocodificados reconciliados como na produção (esperado e um sorteio) e o teste em 2025."""
    S, K, P = m["G"].shape
    D = m["U"].shape[0]
    a25 = slice(P - 12, P)
    lam = (m["G"][:, :, a25] + esperado_estrato[:, :, a25]).mean(axis=2)
    Gd = _soma_distrito(m["G"][:, :, a25].sum(axis=2), m["sd"], D)
    Ud = m["U"][:, :, a25].sum(axis=2)
    g = np.divide(Gd, Gd + Ud, out=np.ones_like(Gd), where=(Gd + Ud) > 0)[m["sd"]]
    rng = np.random.default_rng(seed)
    res = {"reconciliado": [], "geocodificado": [], "imputado": []}
    for _ in range(n_rep):
        N = rng.poisson(lam[:, :, None], size=(S, K, 24))
        Gs = rng.binomial(N, g[:, :, None]).astype(float)
        Us = _soma_distrito(N - Gs, m["sd"], D)
        Gt = Gs.sum(axis=1)
        r = reparte(Gt, Gs, Us, m["sd"], m["pop"], m["eleg"], rng=rng, n_draws=1)
        res["reconciliado"].append(_rejeicao((Gt + r["esperado"])[:, 12:]))
        res["geocodificado"].append(_rejeicao(Gt[:, 12:]))
        res["imputado"].append(_rejeicao((Gt + r["sorteios"][0])[:, 12:]))
    return {"replicas": n_rep, "fracao_geocodificada_media": float((lam * g).sum() / lam.sum()),
            **{k: _resumo_rejeicao(v) for k, v in res.items()}}


# --- 4. ocultação ------------------------------------------------------------------------------

RESIDENCIAL = ("Residencial horizontal popular", "Residencial horizontal médio", "Residencial de esquina",
               "Residencial horizontal alto padrão", "Favela (FCU)")


def _calibra(w: np.ndarray, z: np.ndarray, f: np.ndarray, beta: float) -> np.ndarray:
    """p_sk = expit(a_k + β z_s) com a_k tal que a média de p_sk ponderada pelos eventos w_sk seja f_k."""
    p = np.zeros(w.shape)
    for k in range(w.shape[1]):
        if w[:, k].sum() == 0 or f[k] <= 0:
            continue
        lo, hi = -40.0, 40.0
        for _ in range(100):
            a = (lo + hi) / 2
            if np.average(expit(a + beta * z), weights=w[:, k]) < f[k]:
                lo = a
            else:
                hi = a
        p[:, k] = expit((lo + hi) / 2 + beta * z)
    return p


def _z(x: np.ndarray) -> np.ndarray:
    return (x - x.mean()) / x.std() if x.std() > 0 else np.zeros_like(x)


def _ss_dentro(Y: np.ndarray, unidade: np.ndarray) -> np.ndarray:
    """Soma dos quadrados em torno da média de cada unidade (linhas de Y × grupos de colunas)."""
    out = np.zeros(Y.shape[0])
    for u in np.unique(unidade):
        b = Y[:, unidade == u]
        out += ((b - b.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
    return out


def _recuperacao(true: np.ndarray, rec: np.ndarray, Gr: np.ndarray, m: dict) -> dict:
    """Recuperada contra verdadeira em 2023–2025 (2022 só como janela)."""
    S, P = true.shape
    D = m["U"].shape[0]
    anos = _anos(m)
    av = anos >= 2023
    T, R = true[:, av], rec[:, av]
    out = {"corr_anual": float(np.mean([np.corrcoef(true[:, anos == a].sum(1), rec[:, anos == a].sum(1))[0, 1]
                                        for a in (2023, 2024, 2025)])),
           "corr_setor_mes": float(np.corrcoef(T.ravel(), R.ravel())[0, 1])}
    ua = anos[av]
    ss_t, ss_r = _ss_dentro(T, ua), _ss_dentro(R, ua)
    alto = T.mean(axis=1) >= 1
    ok = alto & (ss_t > 0)
    out["razao_var_dentro_agregada"] = float(ss_r.sum() / ss_t.sum())
    out["razao_var_dentro_mediana_ge1"] = float(np.median(ss_r[ok] / ss_t[ok]))
    unit = (np.arange(S)[:, None] * 10 + (ua - 2023)[None, :]).ravel()
    per = np.tile(np.arange(1, av.sum() + 1), S)
    for nome, Y in (("verdadeira", T), ("recuperada", R)):
        t = teto_sem_modelo(Y.ravel(), unit, per)
        out[f"teto_dentro_{nome}"] = t["quando"]
        out[f"teto_total_{nome}"] = t["onde_e_quando"]
        out[f"rejeita_2025_{nome}"] = _rejeicao(Y[:, -12:])["todos"]
        out[f"rejeita_2025_ge1_{nome}"] = _rejeicao(Y[:, -12:])["ge1"]
    # média histórica dos 12 meses anteriores: da verdade, da recuperada e dos geocodificados que restaram
    # corrigidos pela cobertura do distrito (como ``features.history``)
    Wg = _janela(Gr)
    cov = (_soma_distrito(Wg, m["sd"], D) + 1.0) / (_soma_distrito(_janela(true), m["sd"], D) + 1.25)
    hist = {"verdadeira": _janela(true) / 12, "recuperada": _janela(rec) / 12, "geo_restante": Wg / 12 / cov[m["sd"]]}
    unit2, per2 = np.repeat(np.arange(S), av.sum()), np.tile(np.arange(1, av.sum() + 1), S)
    for h, alvo in (("verdadeira", "verdadeira"), ("recuperada", "recuperada"), ("geo_restante", "recuperada"),
                    ("geo_restante", "verdadeira")):
        y = (T if alvo == "verdadeira" else R).ravel()
        r = medidas(hist[h][:, av].ravel(), y, unit2, per2)
        out[f"r2_hist_{h}_contra_{alvo}"] = r["onde_e_quando"] ** 2
        out[f"r2_dentro_hist_{h}_contra_{alvo}"] = r["quando"] ** 2
    return out


def ocultacao(m: dict, E: np.ndarray, names: list[str], ordem: np.ndarray, n_rep: int = 10, beta: float = 1.0,
              seed: int = 41) -> dict:
    """Esconde a coordenada de eventos geocodificados (perdem o setor, mantêm distrito e estrato) com a
    fração sem coordenada observada em cada estrato e reconcilia como na produção. Cenários: ao acaso
    dentro do estrato (``mar``), mais ocultação em setores com mais crime (``mnar_crime``: logit com
    β = 1 por desvio-padrão do log da contagem anual geocodificada) e em setores mais residenciais
    (``mnar_residencial``: β = 1 por desvio-padrão da parte residencial da testada), com a mesma fração
    média por estrato. Universo: só os geocodificados (a verdade conhecida)."""
    G = m["G"]
    S, K, P = G.shape
    D = m["U"].shape[0]
    Uk, Gk = m["U"].sum(axis=(0, 2)), G.sum(axis=(0, 2))
    f = np.divide(Uk, Uk + Gk, out=np.zeros(K), where=(Uk + Gk) > 0)
    Em = np.zeros((S, E.shape[1]))
    Em[ordem] = E
    lotes = [k for k, n in enumerate(names) if not n.startswith(("rua_", "n_"))]
    from cityomics.atlas import grupos as GR

    res_k = GR.indices(names, "residencial")
    den = Em[:, lotes].sum(axis=1)
    pres = np.divide(Em[:, res_k].sum(axis=1), den, out=np.full(S, np.nan), where=den > 0)
    pres = np.where(np.isnan(pres), np.nanmean(pres), pres)
    zc = _z(np.log1p(m["G_tot"].sum(axis=1) / (P / 12)))
    cen = {"mar": (np.zeros(S), 0.0), "mnar_crime": (zc, beta), "mnar_residencial": (_z(pres), beta)}
    true = m["G_tot"].copy()
    rng = np.random.default_rng(seed)
    out = {"fracao_oculta_por_estrato": dict(zip(m["estratos"], f.tolist())), "beta": beta, "replicas": n_rep,
           "corr_z_crime_residencial": float(np.corrcoef(zc, pres)[0, 1])}
    for nome, (z, b) in cen.items():
        p = _calibra(G.sum(axis=2), z, f, b)
        reps = []
        for _ in range(n_rep):
            H = rng.binomial(G.astype(np.int64), p[:, :, None]).astype(float)
            Gr3 = G - H
            Gr = Gr3.sum(axis=1)
            Uh = _soma_distrito(H, m["sd"], D)
            r = reparte(Gr, Gr3, Uh, m["sd"], m["pop"], m["eleg"])
            reps.append(_recuperacao(true, Gr + r["esperado"], Gr, m) | {"fracao_oculta": float(H.sum() / G.sum())})
        out[nome] = {c: _resumo([x[c] for x in reps]) for c in reps[0]}
    return out


# --- 5. repontuação do benchmark ---------------------------------------------------------------

def _hot(mu: np.ndarray, area: np.ndarray, share: float) -> np.ndarray:
    """Setores no hotspot de ``share`` da área em cada mês (regra de ``eval.hotspot._capture``)."""
    out = np.zeros(mu.shape, bool)
    for j in range(mu.shape[1]):
        order = np.argsort(-(mu[:, j] / area), kind="stable")
        k = min(int(np.searchsorted(np.cumsum(area[order]), share * area.sum(), side="left")) + 1, len(order))
        out[order[:k], j] = True
    return out


def _captura(mu: np.ndarray, area: np.ndarray, y: np.ndarray, shares=(0.01, 0.05)) -> dict:
    """Média mensal da fração do crime capturada (``eval.hotspot.monthly_average``, hit rate)."""
    from cityomics.eval import hotspot

    frames = [(mu[:, j], area, y[:, j]) for j in range(mu.shape[1])]
    hs = hotspot.monthly_average(frames, shares)
    return {f"captura_{int(s * 100)}pct": hs[s]["hit_rate"] for s in shares}


def _fracao_geo_asof(m: dict, V: dict) -> np.ndarray:
    """Fração geocodificada do setor nos 12 meses anteriores a cada mês de 2025 (n_geo / n_total da
    produção); sem crime na janela, a do distrito; sem nada, 1."""
    D = m["U"].shape[0]
    Wg, Wt = _janela(m["G_tot"])[:, -12:], _janela(V["producao"])[:, -12:]
    Wgd, Wtd = _soma_distrito(Wg, m["sd"], D)[m["sd"]], _soma_distrito(Wt, m["sd"], D)[m["sd"]]
    gd = np.divide(Wgd, Wtd, out=np.ones_like(Wgd), where=Wtd > 0)
    return np.divide(Wg, Wt, out=gd.copy(), where=Wt > 0)


def benchmark(m: dict, V: dict, pv: dict, n_boot: int = 2000, log=print) -> dict:
    """CRPS (habilidade contra o GLM) e captura em 1% e 5% da área, só setores de exploração, contra
    (i) o y reconciliado, com o CRPS da produção (= CRPS de ⌈y⌉), com o CRPS de y real e com y arredondado
    (o CRPS e a captura contra o y arredondado); (ii) cada
    imputação inteira (média dos escores); (iii) o y geocodificado com as previsões × fração geocodificada
    as-of do setor (o φ da NB2 não muda com o afinamento binomial)."""
    from cityomics.eval import inference, scores

    area, phi, dist = pv["area"], pv["phi"], np.repeat(pv["dist"], 12)
    assert np.allclose(pv["y"], V["producao"][:, -12:], atol=1e-6), "y das previsões ≠ produção reconciliada"
    gfr = _fracao_geo_asof(m, V)
    alvos = {"reconciliado_crps_producao": (V["producao"][:, -12:], 1.0, crps_nb_teto),
             "reconciliado_crps_real": (V["producao"][:, -12:], 1.0, crps_nb_real),
             "reconciliado_arredondado": (np.rint(V["producao"][:, -12:]), 1.0, scores.crps_nb),
             "geocodificado": (V["geocodificado"][:, -12:], gfr, scores.crps_nb)}
    pares = (("gnn", "glm"), ("ensemble", "glm"), ("media_historica", "glm"), ("ensemble", "media_historica"))
    out = {"setores": int(area.size), "linhas": int(area.size * 12), "fracao_geo_asof_media": float(gfr.mean())}

    def avalia(y, fator, fcrps):
        crps = {k: fcrps(y.ravel(), (pv["mu"][k] * fator).ravel(), phi[k]) for k in MODELOS}
        cap = {k: _captura(pv["mu"][k] * fator, area, y) for k in MODELOS}
        return crps, cap

    for nome, (y, fator, fcrps) in alvos.items():
        t0 = time.time()
        crps, cap = avalia(y, fator, fcrps)
        r = {"crps": {k: float(v.mean()) for k, v in crps.items()},
             "habilidade_crps_contra_glm": {k: float(1 - crps[k].mean() / crps["glm"].mean()) for k in MODELOS},
             "captura": cap,
             "diferencas_crps": {f"{a}-{b}": inference.cluster_bootstrap_diff(crps[a], crps[b], dist, n_boot) for a, b in pares}}
        ha, hb = _hot(pv["mu"]["ensemble"] * fator, area, 0.05), _hot(pv["mu"]["media_historica"] * fator, area, 0.05)
        r["captura5_ensemble_menos_media_historica"] = inference.cluster_bootstrap_ratio_diff(
            (y * ha).ravel(), (y * hb).ravel(), y.ravel(), dist, n_boot)
        out[nome] = r
        log(f"benchmark {nome}: {time.time() - t0:.0f}s; habilidade {r['habilidade_crps_contra_glm']}; captura {cap}")
    imp = _imps(V)
    acc = {k: np.zeros(area.size * 12) for k in MODELOS}
    por = {"crps": {k: [] for k in MODELOS}, "hab": {k: [] for k in MODELOS},
           "c1": {k: [] for k in MODELOS}, "c5": {k: [] for k in MODELOS}}
    t0 = time.time()
    for b in imp:
        y = V[b][:, -12:]
        crps, cap = avalia(y, 1.0, scores.crps_nb)
        for k in MODELOS:
            acc[k] += crps[k] / len(imp)
            por["crps"][k].append(crps[k].mean())
            por["hab"][k].append(1 - crps[k].mean() / crps["glm"].mean())
            por["c1"][k].append(cap[k]["captura_1pct"])
            por["c5"][k].append(cap[k]["captura_5pct"])
    out["imputado"] = {"crps": {k: _resumo(v) for k, v in por["crps"].items()},
                       "habilidade_crps_contra_glm": {k: _resumo(v) for k, v in por["hab"].items()},
                       "captura": {k: {"captura_1pct": _resumo(por["c1"][k]), "captura_5pct": _resumo(por["c5"][k])} for k in MODELOS},
                       "diferencas_crps_media_imputacoes": {f"{a}-{b}": inference.cluster_bootstrap_diff(acc[a], acc[b], dist, n_boot)
                                                            for a, b in pares}}
    log(f"benchmark imputado: {time.time() - t0:.0f}s")
    return out


# --- 6. onde mora a variação mensal -------------------------------------------------------------

def _grupo(Y: np.ndarray, mu: np.ndarray, g: np.ndarray, base: float) -> dict:
    y = Y[g]
    unit, per = _grade(int(g.sum()))
    mm = y.mean(axis=1)
    ss = ((y - mm[:, None]) ** 2).sum(axis=1)
    t = teto_sem_modelo(y.ravel(), unit, per)["quando"]
    r = medidas(mu[g].ravel(), y.ravel(), unit, per)["quando"] ** 2
    return {"teto_dentro": t, "r2_dentro": r, "excesso": float((ss - 11 * mm).sum() / base)}


def onde_mora(V: dict, pv: dict) -> dict:
    """Teto de ruído e R² do ensemble dentro do setor por terço da contagem média de 2025 (entre os setores
    com ≥ 1 evento, pela produção), no 1% do topo (de todos os setores, como ``dispersao``) e sem ele;
    ``excesso`` é a parte do numerador do teto agregado, Σ_s (SS_s − 11 ȳ_s), que cai em cada grupo."""
    Yp = V["producao"][:, -12:]
    mbar = Yp.mean(axis=1)
    S = len(mbar)
    pos = mbar > 0
    q1, q2 = np.quantile(mbar[pos], [1 / 3, 2 / 3])
    top = np.zeros(S, bool)
    top[np.argsort(-mbar)[: max(1, S // 100)]] = True
    grupos = {"terco_1": pos & (mbar <= q1), "terco_2": pos & (mbar > q1) & (mbar <= q2), "terco_3": pos & (mbar > q2),
              "top1pct": top, "sem_top1pct": pos & ~top, "todos": pos}
    mu = pv["mu"]["ensemble"]
    out = {"limites_tercos": [float(q1), float(q2)], "setores_zero": int((~pos).sum()),
           "grupos": {g: {"setores": int(v.sum()), "media_mensal": [float(mbar[v].min()), float(mbar[v].max())],
                          "parte_do_crime": float(Yp[v].sum() / Yp.sum())} for g, v in grupos.items()}}
    res = {}
    for k, Y in V.items():
        y = Y[:, -12:]
        mm = y.mean(axis=1)
        base = float((((y - mm[:, None]) ** 2).sum(axis=1) - 11 * mm)[pos].sum())
        res[k] = {g: _grupo(y, mu, v, base) for g, v in grupos.items()}
    imp = _imps(V)
    for g in grupos:
        out["grupos"][g]["producao"] = res["producao"][g]
        out["grupos"][g]["geocodificado"] = res["geocodificado"][g]
        out["grupos"][g]["imputacoes"] = {c: _resumo([res[k][g][c] for k in imp]) for c in res["producao"][g]}
    return out


def vantagem_historico(m: dict, V: dict, n_imp: int = 5) -> dict:
    """R² fora da amostra da Fig. 5a (``atlas.variance``: LightGBM, CV por distrito) do log da taxa de 2025
    pelo tecido, pelo tecido com covariáveis e pela média histórica 2022–2024, com o y e o histórico de cada
    versão (produção, só geocodificado e as ``n_imp`` primeiras imputações)."""
    from cityomics.atlas import variance

    s = variance.frame()
    pos = pd.Series(np.arange(len(m["cd_setor"])), index=m["cd_setor"])
    idx = pos.reindex(s["cd_setor"].cast(pl.String).to_list()).to_numpy()
    assert not np.isnan(idx).any()
    idx = idx.astype(int)
    a = _anos(m)
    chaves = ["producao", "geocodificado"] + _imps(V)[:n_imp]
    res = {}
    for k in chaves:
        Y = V[k][idx]
        s2 = s.with_columns(pl.Series("y", Y[:, a == 2025].sum(axis=1)), pl.Series("hist", Y[:, a < 2025].sum(axis=1) / 3))
        X, y, g = variance.conjuntos(s2)
        res[k] = {c: variance.r2_cv(X[c], y, g) for c in ("tecido", "tecido_mais_covariaveis", "media_historica")}
    imp = [k for k in chaves if k.startswith("imp")]
    return {"setores": int(len(idx)), "producao": res["producao"], "geocodificado": res["geocodificado"],
            "imputacoes": {c: _resumo([res[k][c] for k in imp]) for c in res["producao"]}, "n_imputacoes": len(imp)}


# --- execução ----------------------------------------------------------------------------------

def _salva_imputacoes(m: dict, V: dict) -> None:
    S, P = V["producao"].shape
    cols = {"cd_setor": np.repeat(m["cd_setor"], P), "periodo": np.tile(m["periodos"], S),
            "n_geo": V["geocodificado"].ravel().astype(np.int32), "n_total": V["producao"].ravel()}
    cols |= {k: V[k].ravel().astype(np.int32) for k in _imps(V)}
    pl.DataFrame(cols).write_parquet(out_dir() / "reconciliacao_imputacoes.parquet")


def run(n_imput: int = M_IMPUT, n_nulo: int = 200, n_ocult: int = 10, log=print) -> dict:
    t0 = time.time()
    m = malha_exploracao()
    rng = np.random.default_rng(20261020)
    r = reparte(m["G_tot"], m["G"], m["U"], m["sd"], m["pop"], m["eleg"], rng=rng, n_draws=n_imput, por_estrato=True)
    prod = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).filter(
        pl.col("cd_setor").is_in(m["cd_setor"].tolist()))
    pos = pd.Series(np.arange(len(m["cd_setor"])), index=m["cd_setor"])
    ppos = pd.Series(np.arange(len(m["periodos"])), index=m["periodos"])
    i, j = pos.reindex(prod["cd_setor"].to_list()).to_numpy(), ppos.reindex(prod["periodo"].to_list()).to_numpy()
    confere = float(np.abs(r["esperado"][i, j] - prod["n_alocado"].to_numpy()).max())
    assert confere < 1e-8, f"reconciliação vetorizada difere da produção: {confere}"
    V = _versoes(m, r)
    _salva_imputacoes(m, V)
    a25 = _anos(m) == 2025
    Uk, Gk = m["U"].sum(axis=(0, 2)), m["G"].sum(axis=(0, 2))
    rep = {"recorte": {"setores": int(len(m["cd_setor"])), "distritos": int(m["U"].shape[0]), "imputacoes": n_imput,
                       "diferenca_max_contra_producao": confere,
                       "eventos_2025": float(V["producao"][:, a25].sum()), "geocodificados_2025": float(m["G_tot"][:, a25].sum()),
                       "fracao_reconciliada_2025": float(1 - m["G_tot"][:, a25].sum() / V["producao"][:, a25].sum()),
                       "fracao_sem_coordenada_por_estrato_2022_2025": dict(zip(m["estratos"], (Uk / (Uk + Gk)).tolist())),
                       "fracao_setor_mes_2025_fracionarios": float(np.mean(np.abs(V["producao"][:, a25] - np.rint(V["producao"][:, a25])) > 1e-9)),
                       "fracao_setor_mes_2025_entre_0_e_1": float(np.mean((V["producao"][:, a25] > 1e-9) & (V["producao"][:, a25] < 1)))}}
    log(f"malha e {n_imput} imputações: {time.time() - t0:.0f}s; confere com a produção ({confere:.1e})")

    ids, E, names = setor_exposicao()
    ordem = pos.reindex(ids["cd_setor"].to_list()).to_numpy()
    assert not np.isnan(ordem).any()
    ordem = ordem.astype(int)
    rep["atribuicao_2025"] = atribuicao_2025(E, names, {k: Y[ordem][:, a25].sum(axis=1) for k, Y in V.items()})
    log(f"(a) λ 2025: {time.time() - t0:.0f}s")
    rep["persistencia"] = persistencia(E, {k: _anual(Y, m, ordem) for k, Y in V.items()})
    log(f"(b) persistência: {time.time() - t0:.0f}s")
    pv = _previsoes(m)
    rep["ruido_dispersao"] = ruido_e_dispersao(V, pv)
    rep["ruido_dispersao"]["confere_previsibilidade"] = dispersao(V["producao"][:, -12:].ravel(), _grade(len(m["cd_setor"]))[0])
    log(f"(c, d) teto, R² e dispersão: {time.time() - t0:.0f}s")

    rep["calibracao"] = {"poisson_puro_medias_reconciliadas": nulo_poisson(V["producao"][:, -12:].mean(axis=1), n_nulo),
                         "poisson_puro_medias_geocodificadas": nulo_poisson(V["geocodificado"][:, -12:].mean(axis=1), n_nulo, seed=33),
                         "pipeline": nulo_pipeline(m, r["esperado_estrato"], n_nulo)}
    log(f"3 calibração: {time.time() - t0:.0f}s")
    rep["ocultacao"] = ocultacao(m, E, names, ordem, n_ocult)
    log(f"4 ocultação: {time.time() - t0:.0f}s")
    rep["benchmark"] = benchmark(m, V, pv, log=log)
    log(f"5 benchmark: {time.time() - t0:.0f}s")
    rep["onde_mora"] = onde_mora(V, pv)
    log(f"6 onde mora: {time.time() - t0:.0f}s")
    rep["vantagem_historico"] = vantagem_historico(m, V)
    log(f"vantagem do histórico (Fig. 5a): {time.time() - t0:.0f}s")
    rep["crps_verificacao"] = verifica_crps()
    rep["crps_repontuado"] = repontua_crps(log=log)
    log(f"CRPS repontuado: {time.time() - t0:.0f}s")
    (out_dir() / "reconciliacao.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return rep


if __name__ == "__main__":
    run()
