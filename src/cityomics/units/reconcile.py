"""Reconciliação hierárquica estratificada (D16, D27).

Para cada distrito × mês × estrato de tipo de local, os eventos sem setor (sem coordenada,
distrito pelo bairro ou pela delegacia) são distribuídos entre os setores do distrito na
proporção dos eventos geocodificados do mesmo estrato nos 12 meses anteriores (regra as-of).

    fração(s) = (W[s, estrato] + α · W[s, todos] / ΣW[d, todos]) / (ΣW[d, estrato] + α)

com W = contagens geocodificadas na janela e α = 1 (suavização para estratos raros). Sem
histórico no distrito, a fração é a da população do setor. Nos 12 primeiros meses da série,
sem janela anterior completa, usa-se a janela dos 12 primeiros meses.

Invariante: a soma dos setores de um distrito é igual ao total do distrito em cada mês.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

WINDOW = 12
ALPHA = 1.0


def _window_sums(counts: pd.DataFrame, months: pd.PeriodIndex) -> pd.DataFrame:
    """counts: linhas = chave, colunas = meses. Soma dos WINDOW meses anteriores a cada mês."""
    c = counts.reindex(columns=months, fill_value=0).to_numpy(dtype=float)
    csum = np.concatenate([np.zeros((c.shape[0], 1)), np.cumsum(c, axis=1)], axis=1)
    out = np.empty_like(c)
    first = csum[:, min(WINDOW, c.shape[1])]  # janela dos primeiros meses, para o início da série
    for j in range(c.shape[1]):
        out[:, j] = csum[:, j] - csum[:, j - WINDOW] if j >= WINDOW else first
    return pd.DataFrame(out, index=counts.index, columns=months)


def reconcile(ev: pd.DataFrame, setores: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """ev: eventos atribuídos (cd_setor, cd_dist, estrato, data_fato).
    Devolve uma linha por setor × período com n_geo, n_alocado e n_total."""
    ev = ev[ev["cd_dist"].notna() & ev["data_fato"].notna()].copy()
    ev["periodo"] = ev["data_fato"].dt.to_period(freq)
    periods = pd.period_range(ev["periodo"].min(), ev["periodo"].max(), freq=freq)
    sdist = setores.set_index("cd_setor")["cd_dist"]
    pop = setores.set_index("cd_setor")["pop_2022"].astype(float).clip(lower=0)

    geo = ev[ev["cd_setor"].notna()]
    g_st = geo.groupby(["cd_setor", "estrato", "periodo"]).size().unstack("periodo", fill_value=0)
    g_all = geo.groupby(["cd_setor", "periodo"]).size().unstack("periodo", fill_value=0)
    full_idx = pd.Index(setores["cd_setor"], name="cd_setor")
    W_all = _window_sums(g_all.reindex(full_idx, fill_value=0), periods)
    W_st = _window_sums(g_st, periods) if len(g_st) else None

    unalloc = (ev[ev["cd_setor"].isna()].groupby(["cd_dist", "estrato", "periodo"]).size()
               .rename("u").reset_index())

    alloc = pd.DataFrame(0.0, index=full_idx, columns=periods)
    dist_of = sdist.reindex(full_idx)
    W_all_d = W_all.groupby(dist_of).transform("sum")
    prior = W_all / W_all_d.replace(0, np.nan)
    pop_share = pop.reindex(full_idx) / pop.reindex(full_idx).groupby(dist_of).transform("sum")
    pop_share = pop_share.fillna(1.0 / dist_of.map(dist_of.value_counts()))  # distrito sem população
    prior = prior.apply(lambda col: col.fillna(pop_share))

    for (d, st), grp in unalloc.groupby(["cd_dist", "estrato"]):
        members = dist_of.index[dist_of == d]
        if len(members) == 0:
            continue
        if W_st is not None and st in W_st.index.get_level_values("estrato"):
            w = W_st.xs(st, level="estrato").reindex(members, fill_value=0.0)
        else:
            w = pd.DataFrame(0.0, index=members, columns=periods)
        p = prior.loc[members]
        share = (w + ALPHA * p) / (w.sum(axis=0) + ALPHA)
        u = grp.set_index("periodo")["u"].reindex(periods, fill_value=0)
        alloc.loc[members] += share.mul(u, axis=1).to_numpy()

    n_geo = g_all.reindex(full_idx, fill_value=0).reindex(columns=periods, fill_value=0)
    out = (pd.DataFrame({"n_geo": n_geo.stack(), "n_alocado": alloc.stack()}).reset_index()
           .rename(columns={"level_1": "periodo"}))
    out.columns = ["cd_setor", "periodo", "n_geo", "n_alocado"]
    out["cd_dist"] = out["cd_setor"].map(sdist)
    out["n_total"] = out["n_geo"] + out["n_alocado"]
    return out


def district_totals(ev: pd.DataFrame, freq: str) -> pd.DataFrame:
    ev = ev[ev["cd_dist"].notna() & ev["data_fato"].notna()]
    return (ev.groupby(["cd_dist", ev["data_fato"].dt.to_period(freq).rename("periodo")]).size()
              .rename("n").reset_index())
