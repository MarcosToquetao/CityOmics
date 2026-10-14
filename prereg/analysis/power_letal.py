"""Análise de poder (pseudo-fora-da-amostra) para o desfecho de violência letal.

Só usa 2022–2025. Reproduz o layout do teste de 2026 (3 trimestres × ~96 unidades, h=1)
deslocado para 2025 (jan–set), e estima o erro-padrão da diferença média de escore entre
dois modelos plausíveis, com bootstrap por unidade (blocos espaciais = DP).

Proxy de unidade: área de DP (~93 na capital), granularidade próxima à dos 96 distritos.
"""
import sys

import numpy as np
import pandas as pd
from scipy import stats

df = pd.read_parquet(sys.argv[1])
rng = np.random.default_rng(20261014)
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)  # alfa bilateral 5%, poder 80%


def nb_logpmf(y, mu, k):
    # NB2 com parâmetro de tamanho k (var = mu + mu^2/k)
    p = k / (k + mu)
    return stats.nbinom.logpmf(y, k, p)


def nb_crps(y, mu, k, ymax=200):
    grid = np.arange(ymax + 1)
    p = k / (k + mu)
    cdf = stats.nbinom.cdf(grid[None, :], k, p[:, None])
    ind = (grid[None, :] >= y[:, None]).astype(float)
    return ((cdf - ind) ** 2).sum(axis=1)


def run(col):
    wide = df.pivot_table(index="dp", columns="trimestre", values=col, fill_value=0).sort_index(axis=1)
    qs = list(wide.columns)
    test_qs = [q for q in qs if q.startswith("2025") and q[-1] in "123"]
    rows = []
    for q in test_qs:
        i = qs.index(q)
        hist = wide.iloc[:, max(0, i - 8):i]
        y = wide[q].to_numpy()
        m_hist = hist.mean(axis=1).to_numpy().clip(0.1)
        m_pers = wide.iloc[:, i - 1].to_numpy().clip(0.5)
        # dispersão estimada só com o histórico (método dos momentos, agrupado)
        resid_var = ((hist.sub(hist.mean(axis=1), axis=0)) ** 2).mean(axis=1).to_numpy()
        k = max(0.5, float(np.mean(m_hist ** 2) / max(np.mean(resid_var - m_hist), 1e-3)))
        for name, mu in (("media8", m_hist), ("persist", m_pers)):
            rows.append(pd.DataFrame({"dp": wide.index, "q": q, "model": name, "y": y,
                                      "logs": -nb_logpmf(y, mu, k), "crps": nb_crps(y, mu, k)}))
    r = pd.concat(rows)
    piv = r.pivot_table(index=["dp", "q"], columns="model", values=["logs", "crps"])
    out = {"desfecho": col, "unidades": wide.shape[0], "celulas_teste": len(piv),
           "media_por_celula": float(r.loc[r.model == "media8", "y"].mean())}
    for metric in ("logs", "crps"):
        d = (piv[(metric, "persist")] - piv[(metric, "media8")]).rename("d").reset_index()
        per_dp = d.groupby("dp")["d"].sum()
        n_dp, n_cells = len(per_dp), len(d)
        boot = [per_dp.sample(n_dp, replace=True, random_state=int(s)).sum() / n_cells
                for s in rng.integers(0, 2**31, 2000)]
        se3 = float(np.std(boot))
        base = float(piv[(metric, "media8")].mean())
        out[f"{metric}_base"] = base
        out[f"{metric}_diff_obs"] = float(d["d"].mean())
        out[f"{metric}_mde_3tri"] = Z * se3
        out[f"{metric}_mde_3tri_pct"] = 100 * Z * se3 / base
        se4 = se3 * np.sqrt(3 / 4)  # 2026 jan–set + 1 trimestre prospectivo
        out[f"{metric}_mde_4tri_pct"] = 100 * Z * se4 / base
        se1 = se3 * np.sqrt(3)       # só o trimestre prospectivo
        out[f"{metric}_mde_1tri_pct"] = 100 * Z * se1 / base
    return out


res = pd.DataFrame([run("composto"), run("estrito")]).set_index("desfecho").T
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
print(res)
tot = df.groupby(df["trimestre"].str[:4])[["composto", "estrito"]].sum()
print(tot)
