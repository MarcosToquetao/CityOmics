"""Avaliação do Laya no protocolo de desenvolvimento (treino 2024-H1, recalibração 2024-H2, avaliação 2025).

Compara, no mesmo subconjunto de setores de 2025, o Brier de P(≥1):
- Laya-FT e Laya-ZS com recalibração isotônica (ajustada em 2024-H2);
- LightGBM no estado comprimido (H2), com e sem a mesma recalibração;
- GLM, LightGBM completo e ensemble (binomial negativa).
Testes pareados com bootstrap por distrito e Holm. Lê os CSVs de ``laya_{ft,zs}_{recal,eval}.csv``.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl
from sklearn.metrics import roc_auc_score

from cityomics.eval import calibration, inference, scores
from cityomics.laya import evaluate as E
from cityomics.models import select_run
from cityomics.paths import interim_dir, processed_dir


def _read(nome: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    idx = pl.read_parquet(interim_dir() / "laya" / f"index_{nome}.parquet")
    num = pl.read_parquet(processed_dir() / "laya" / f"numeric_{nome}.parquet")
    return idx, num


def run(table: pl.DataFrame, n_boot: int = 2000, tag: str = "dev", log=print) -> dict:
    d = processed_dir() / "laya"
    i_tr, n_tr = _read("train")
    i_rc, n_rc = _read("recal")
    i_ev, n_ev = _read("eval")
    for nome, i in (("train", i_tr), ("recal", i_rc), ("eval", i_ev)):
        assert i["state_id"].n_unique() == i.height, f"state_id repetido em {nome}"
    ev_y = (i_ev["y"].to_numpy() >= 0.5).astype("float64")
    rc_y = (i_rc["y"].to_numpy() >= 0.5).astype("float64")

    def csv(prefix, nome, idx):
        c = pl.read_csv(d / f"laya_{prefix}_{nome}.csv")
        return idx.join(c, on="state_id", how="left")

    P = {}
    for prefix, label in (("ft", "laya_ft"), ("zs", "laya_zs")):
        rc, ev = csv(prefix, "recal", i_rc), csv(prefix, "eval", i_ev)
        assert rc["p_ge1"].null_count() == 0 and ev["p_ge1"].null_count() == 0, f"faltam respostas em {prefix}"
        iso = E.calibrate(rc["p_ge1"].to_numpy(), rc_y)
        P[label + "_bruto"] = ev["p_ge1"].to_numpy()
        P[label] = iso.predict(ev["p_ge1"].to_numpy())
    # LightGBM no estado comprimido (H2): treino 2024-H1; recalibração 2024-H2 igual à do Laya
    y_tr = i_tr["y"].to_numpy()
    p_rc = E.lgbm_on_state(n_tr.drop("state_id"), y_tr, n_rc.drop("state_id"))
    p_ev = E.lgbm_on_state(n_tr.drop("state_id"), y_tr, n_ev.drop("state_id"))
    P["lgbm_estado_bruto"] = p_ev
    P["lgbm_estado"] = E.calibrate(p_rc, rc_y).predict(p_ev)

    # modelos do benchmark nas mesmas linhas (média prevista → P(≥1) pela NB)
    evb, mu, phi, dist = select_run.load(table.select("cd_setor", "cd_dist"), tag)
    key = evb.select("cd_setor", "mes").with_row_index("_r")
    j = i_ev.select("cd_setor", "mes").with_row_index("_o").join(key, on=["cd_setor", "mes"], how="left").sort("_o")
    assert j["_r"].null_count() == 0
    r = j["_r"].to_numpy()
    for m in ("glm", "media_historica", "lgbm_completo", "ensemble"):
        P[m] = scores.prob_ge1(mu[m][r], phi[m])
    dist_ev = dist[r]

    rows, brier = {}, {k: (v - ev_y) ** 2 for k, v in P.items()}
    for k, p in P.items():
        _, ece = calibration.reliability(p, ev_y)
        rows[k] = {"brier": float(brier[k].mean()), "ece": ece, "auc": float(roc_auc_score(ev_y, p)),
                   "logloss": float(-np.mean(ev_y * np.log(np.clip(p, 1e-6, 1)) + (1 - ev_y) * np.log(np.clip(1 - p, 1e-6, 1))))}
    pares = {"H2: laya_ft vs lgbm_estado": ("laya_ft", "lgbm_estado"), "laya_ft vs laya_zs": ("laya_ft", "laya_zs"),
             "laya_ft vs glm": ("laya_ft", "glm"), "laya_ft vs lgbm_completo": ("laya_ft", "lgbm_completo"),
             "laya_ft vs ensemble": ("laya_ft", "ensemble"), "lgbm_estado vs glm": ("lgbm_estado", "glm")}
    tests = {k: inference.cluster_bootstrap_diff(brier[a], brier[b], dist_ev, n_boot) for k, (a, b) in pares.items()}
    hm = inference.holm({k: t["p"] for k, t in tests.items()})
    for k in tests:
        tests[k].update(hm[k])
    out = {"n_eval": int(len(ev_y)), "taxa_evento": float(ev_y.mean()), "metricas": rows, "testes": tests}
    (d / "laya_dev_resultados.json").write_text(json.dumps(out, indent=2))
    log(json.dumps({k: {m: round(v, 4) for m, v in r_.items()} for k, r_ in rows.items()}, indent=1))
    return out
