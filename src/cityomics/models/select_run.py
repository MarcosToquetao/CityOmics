"""Seleção dos melhores da classe no período de tuning (prereg §5.2) e testes formais.

Lê as previsões de 2025 gravadas por ``benchmark_run`` (modelos ajustados em 2023–2024) e:
- escolhe o melhor baseline e o melhor modelo de outras áreas por CRPS (H1a) e por PAI a 1% (H1b);
- compara cada modelo ao melhor baseline com bootstrap por distrito (2000 reamostras) e Holm;
- compara os finalistas entre si;
- grava ``prereg/selection_dev.json`` (candidatos e estatísticas) e atualiza as chaves de seleção
  determináveis em ``prereg/selection.json``; as que dependem de Laya e do atlas ficam vazias e o
  ``cityomics freeze check`` as aponta.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.eval import hotspot, inference, scores
from cityomics.models import ensemble
from cityomics.models.benchmark_run import MODELS
from cityomics.paths import REPO_ROOT, processed_dir

BASELINES = ["media_historica", "glm", "kde"]
CROSS = [m for m in MODELS if m not in BASELINES] + ["ensemble"]
SHARE = 0.01


def load(table: pl.DataFrame, tag: str = "dev"):
    d = processed_dir() / "modelo"
    val, ev = pl.read_parquet(d / f"pred_{tag}_val.parquet"), pl.read_parquet(d / f"pred_{tag}_eval.parquet")
    res = json.loads((d / f"resultados_benchmark_{tag}.json").read_text())
    w = np.array([res["pesos"][m] for m in MODELS])
    mu_val = np.column_stack([val[f"mu_{m}"].to_numpy() for m in MODELS]) @ w
    mu = {m: ev[f"mu_{m}"].to_numpy() for m in MODELS}
    mu["ensemble"] = np.column_stack([mu[m] for m in MODELS]) @ w
    phi = dict(res["phi_eval"])
    phi["ensemble"] = scores.fit_phi(val["y"].to_numpy(), mu_val)
    dist = ev.join(table.select("cd_setor", "cd_dist").unique(), on="cd_setor", how="left")["cd_dist"].to_numpy()
    return ev, mu, phi, dist


def in_hotspot(ev: pl.DataFrame, mu: np.ndarray) -> np.ndarray:
    """1 se o setor entra no hotspot de 1% da área do mês (ranking por média prevista por km²)."""
    mes, area = ev["mes"].to_numpy(), ev["area_km2"].to_numpy()
    out = np.zeros(len(mes))
    for m in np.unique(mes):
        idx = np.where(mes == m)[0]
        order = np.argsort(-(mu[idx] / area[idx]), kind="stable")
        k = min(int(np.searchsorted(np.cumsum(area[idx][order]), SHARE * area[idx].sum(), side="left")) + 1, len(idx))
        out[idx[order[:k]]] = 1.0
    return out


def run(table: pl.DataFrame, n_boot: int = 2000, tag: str = "dev", log=print) -> dict:
    ev, mu, phi, dist = load(table, tag)
    y = ev["y"].to_numpy().astype("float64")
    crps = {m: scores.crps_nb(y, mu[m], phi[m]) for m in mu}
    brier = {m: scores.brier(scores.prob_ge1(mu[m], phi[m]), (y >= 0.5).astype("float64")) for m in mu}
    hot = {m: in_hotspot(ev, mu[m]) for m in mu}
    tot = y.sum()
    pai = {m: float((y * hot[m]).sum() / tot / SHARE) for m in mu}
    mean_crps = {m: float(v.mean()) for m, v in crps.items()}
    # PAI mensal médio (definição do pré-registro) para a escolha; o pooled só alimenta o bootstrap
    month_pai = {m: float(np.mean([pai_m for pai_m in _monthly_pai(ev, mu[m], y)])) for m in mu}

    best = {"best_baseline_crps": min(BASELINES, key=mean_crps.get),
            "best_baseline_pai1": max(BASELINES, key=month_pai.get),
            "best_crossdomain_crps": min(CROSS, key=mean_crps.get),
            "best_crossdomain_pai1": max(CROSS, key=month_pai.get)}
    log(str(best))

    def crps_test(a, b):
        return inference.cluster_bootstrap_diff(crps[a], crps[b], dist, n_boot)

    def pai_test(a, b):
        t = inference.cluster_bootstrap_ratio_diff(y * hot[a], y * hot[b], y, dist, n_boot)
        return {k: (v / SHARE if k != "p" and k != "n_clusters" else v) for k, v in t.items()}

    ref = best["best_baseline_crps"]
    vs_base = {m: crps_test(m, ref) for m in CROSS}
    holm = inference.holm({m: t["p"] for m, t in vs_base.items()})
    for m in vs_base:
        vs_base[m].update(holm[m])
    h1a = crps_test(best["best_crossdomain_crps"], ref)
    h1b = pai_test(best["best_crossdomain_pai1"], best["best_baseline_pai1"])
    h1 = inference.holm({"H1a": h1a["p"], "H1b": h1b["p"]})
    finalists = ["gnn", "ensemble", "lgbm_completo", "lgbm_nucleo", "hawkes"]
    pares = {f"{a} vs {b}": crps_test(a, b) for i, a in enumerate(finalists) for b in finalists[i + 1:]}
    ph = inference.holm({k: t["p"] for k, t in pares.items()})
    for k in pares:
        pares[k].update(ph[k])
    h2_proxy = {m: inference.cluster_bootstrap_diff(brier[m], brier[ref], dist, n_boot) for m in ["ensemble", "gnn", "lgbm_completo"]}
    out = {"selecao": best, "crps_medio": mean_crps, "pai1_mensal": month_pai, "h1a": {**h1a, **h1["H1a"]}, "h1b": {**h1b, **h1["H1b"]},
           "contra_melhor_baseline": vs_base, "finalistas": pares, "brier_contra_baseline": h2_proxy, "n_boot": n_boot}
    (REPO_ROOT / "prereg" / f"selection_{tag}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    sel_path = REPO_ROOT / "prereg" / "selection.json"
    sel = json.loads(sel_path.read_text()) if sel_path.exists() else {}
    sel.update(best)
    for k in ("laya_ft", "lightgbm_compressed_state", "markov_fate_baseline"):
        sel.setdefault(k, None)
    sel["status"] = "provisional: periodo de tuning 2025; refazer apos incluir VIIRS e congelar os modelos"
    sel_path.write_text(json.dumps(sel, indent=2, ensure_ascii=False))
    return out


def _monthly_pai(ev: pl.DataFrame, mu: np.ndarray, y: np.ndarray):
    mes, area = ev["mes"].to_numpy(), ev["area_km2"].to_numpy()
    for m in np.unique(mes):
        i = mes == m
        r = hotspot.hotspot_metrics(mu[i], area[i], y[i], (SHARE,))
        yield r[SHARE]["pai"]
