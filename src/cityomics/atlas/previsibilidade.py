"""Limite de previsibilidade por escala (P7, docs/NARRATIVA.md; no espírito de Song et al. 2010).

Pergunta: quanto do crime é previsível em cada escala, e quanto o melhor modelo alcança? Para cada
agregação no espaço (setor, distrito) e no tempo (mês, trimestre, ano) de 2025:

- **observado:** correlação entre a previsão agregada (soma das médias da NB do ensemble, ajustado
  até 2024, h = 1) e a contagem agregada;
- **teto de ruído:** a mesma correlação se o modelo fosse a verdade, com contagens simuladas da NB
  preditiva (50 sorteios; meses e setores independentes);
- **"quando":** as mesmas duas correlações depois de tirar a média de cada unidade espacial (só faz
  sentido com mais de um período por unidade).

A razão observado/teto mede quanto do previsível o modelo já alcança; o teto mede quanto é previsível.
O teto sem modelo (``teto_sem_modelo``) é a fração da variância acima do ruído de Poisson; o teste de
dispersão por setor (``dispersao``) mostra se esse excesso é geral ou concentrado em poucos polos.
Só distritos de exploração (D53) para manter o mesmo recorte do atlas.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.fenotipo import out_dir
from cityomics.eval import scores

ESPACO = ("setor", "distrito")
TEMPO = ("mes", "trimestre", "ano")


def _corr(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else float("nan")


def agrega(unit: np.ndarray, per: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    key = unit.astype(np.int64) * 100 + per
    uk, inv = np.unique(key, return_inverse=True)
    return np.bincount(inv, weights=v), uk // 100, uk % 100


def medidas(mu: np.ndarray, y: np.ndarray, unit: np.ndarray, per: np.ndarray) -> dict:
    m, u, _ = agrega(unit, per, mu)
    o, _, _ = agrega(unit, per, y)
    out = {"onde_e_quando": _corr(m, o)}
    _, inv = np.unique(u, return_inverse=True)
    cnt = np.bincount(inv)
    if cnt.max() > 1:
        dm = m - (np.bincount(inv, weights=m) / cnt)[inv]
        do = o - (np.bincount(inv, weights=o) / cnt)[inv]
        out["quando"] = _corr(dm, do)
    return out


def teto_sem_modelo(y: np.ndarray, unit: np.ndarray, per: np.ndarray) -> dict:
    """R² máximo sem modelo: a fração da variância que excede o ruído de Poisson (média = variância).

    Total: 1 − média/variância das contagens agregadas. "Quando": o mesmo dentro de cada unidade
    (variância em torno da média da unidade, com n − 1 por unidade)."""
    o, u, _ = agrega(unit, per, y)
    out = {"onde_e_quando": float(np.clip(1 - o.mean() / o.var(), 0, 1))}
    _, inv = np.unique(u, return_inverse=True)
    cnt = np.bincount(inv)
    if cnt.max() > 1:
        do = o - (np.bincount(inv, weights=o) / cnt)[inv]
        var_w = float((do ** 2).sum() / (len(o) - len(cnt)))
        out["quando"] = float(np.clip(1 - o.mean() / var_w, 0, 1))
    return out


def dispersao(y: np.ndarray, unit: np.ndarray, salvar: str | None = None) -> dict:
    """Teste de dispersão de Poisson por setor ao longo dos meses: Σ(o − ō)²/ō ~ χ²(n − 1).

    Diz em quantos setores o mês a mês se distingue de ruído de Poisson e onde fica o excesso de
    variância (soma de (o − ō)² − (n − 1)·ō, truncada em zero) entre os setores de maior contagem."""
    from scipy.stats import chi2

    _, inv = np.unique(unit, return_inverse=True)
    cnt = np.bincount(inv)
    mean_u = np.bincount(inv, weights=y) / cnt
    ss = np.bincount(inv, weights=(y - mean_u[inv]) ** 2)
    ok = mean_u > 0
    D = np.full(len(cnt), np.nan)
    D[ok] = ss[ok] / (cnt[ok] - 1) / mean_u[ok]
    p = np.full(len(cnt), np.nan)
    p[ok] = chi2.sf(ss[ok] / mean_u[ok], cnt[ok] - 1)
    excesso = np.clip(ss - (cnt - 1) * mean_u, 0, None)
    ordem = np.argsort(-mean_u)
    top1 = ordem[: max(1, len(ordem) // 100)]
    alto = mean_u >= 1
    if salvar:
        pl.DataFrame({"media_mensal": mean_u, "D": D, "p_poisson": p, "excesso": excesso}).write_parquet(out_dir() / salvar)
    return {"setores": int(ok.sum()), "D_mediano": float(np.nanmedian(D[ok])), "D_mediano_media_ge_1": float(np.nanmedian(D[alto])),
            "fracao_rejeita_poisson_5pct": float(np.mean(p[ok] < 0.05)),
            "fracao_rejeita_poisson_5pct_media_ge_1": float(np.mean(p[alto] < 0.05)),
            "parte_do_excesso_no_top1pct": float(excesso[top1].sum() / max(excesso.sum(), 1e-12)),
            "parte_do_crime_no_top1pct": float(mean_u[top1].sum() / mean_u.sum())}


def run(n_sim: int = 50, log=print) -> dict:
    from cityomics.viz.figdata import load_eval

    ev, mu, phi, dist = load_eval("dev")
    dist = np.asarray(dist).astype(str)
    keep = guard.explore_mask(dist)
    ev = ev.filter(pl.Series(keep))
    dist = dist[keep]
    m_ens, ph = mu["ensemble"][keep], phi["ensemble"]
    ph = ph[keep] if np.ndim(ph) else ph
    y = ev["y"].to_numpy().astype(float)
    mes = ev["mes"].to_numpy()
    mi = np.array([int(s[5:7]) for s in mes])
    per = {"mes": mi, "trimestre": (mi - 1) // 3 + 1, "ano": np.ones_like(mi)}
    unit = {"setor": np.unique(ev["cd_setor"].to_numpy(), return_inverse=True)[1],
            "distrito": np.unique(dist, return_inverse=True)[1]}
    rng = np.random.default_rng(0)
    n, p = scores.nb_scipy(m_ens, ph)
    sims = [rng.negative_binomial(n, p).astype(float) for _ in range(n_sim)]
    rows = []
    for e in ESPACO:
        for t in TEMPO:
            obs = medidas(m_ens, y, unit[e], per[t])
            teto = [medidas(m_ens, s, unit[e], per[t]) for s in sims]
            livre = teto_sem_modelo(y, unit[e], per[t])
            for k, v in obs.items():
                tv = float(np.mean([d[k] for d in teto]))
                rows.append({"espaco": e, "tempo": t, "medida": k, "observado": v, "teto": tv, "razao": v / tv if tv else float("nan"),
                             "r2_observado": v ** 2, "r2_max_sem_modelo": livre[k],
                             "fracao_do_previsivel": v ** 2 / livre[k] if livre[k] > 0 else float("nan")})
    tab = pl.DataFrame(rows)
    tab.write_parquet(out_dir() / "previsibilidade_escala.parquet")
    rep = {r["espaco"] + "×" + r["tempo"] + "|" + r["medida"]: {k: r[k] for k in ("observado", "teto", "razao", "r2_observado",
                                                                                     "r2_max_sem_modelo", "fracao_do_previsivel")}
           for r in tab.iter_rows(named=True)}
    rep["dispersao_setor_mes"] = dispersao(y, unit["setor"], salvar="dispersao_setor.parquet")
    rep["dispersao_setor_mes_geocodificado"] = dispersao(ev["n_geo"].to_numpy().astype(float), unit["setor"])
    (out_dir() / "previsibilidade.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    d = rep["dispersao_setor_mes"]
    log(f"dispersão setor × mês: D mediano {d['D_mediano']:.2f} ({d['D_mediano_media_ge_1']:.2f} nos setores com ≥ 1/mês); "
        f"rejeitam Poisson a 5%: {d['fracao_rejeita_poisson_5pct']:.1%} ({d['fracao_rejeita_poisson_5pct_media_ge_1']:.1%}); "
        f"1% dos setores com mais crime: {d['parte_do_crime_no_top1pct']:.0%} do crime e {d['parte_do_excesso_no_top1pct']:.0%} do excesso")
    for r in tab.iter_rows(named=True):
        log(f"{r['espaco']:>8} × {r['tempo']:<9} {r['medida']:<13} r {r['observado']:.3f} (teto do modelo {r['teto']:.3f}); "
            f"R² {r['r2_observado']:.3f} de no máximo {r['r2_max_sem_modelo']:.3f} sem modelo ({r['fracao_do_previsivel']:.0%})")
    return rep
