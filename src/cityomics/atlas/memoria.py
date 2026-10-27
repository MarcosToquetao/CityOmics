"""Memória do lugar: o que a história do setor guarda além do tecido (P6, docs/NARRATIVA.md).

A média histórica explica mais da taxa do setor do que o tecido (R² 0,48 contra 0,25–0,31). Aqui se
separa a variância entre setores do log da taxa anual de roubo e furto de celular (2022–2025) em:

- **tecido:** a variância do log do crime esperado só pela composição (``E·λ_ano``, EM por ano);
- **memória estável:** a parte do resíduo (log observado − log esperado) que se repete entre anos,
  estimada pela covariância média dos resíduos entre anos diferentes;
- **transitória:** o resto do resíduo, que soma o ruído de Poisson (estimado por 1/(contagem média))
  e a mudança real de um ano para o outro.

E a persistência do resíduo com a defasagem (1, 2 e 3 anos), com a meia-vida de um decaimento
exponencial. Usa crime: só os distritos de exploração (D53); nada de 2026.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import YEARS, out_dir, setor_exposicao
from cityomics.paths import processed_dir

MIN_ESPERADO = 1.0   # setores com ao menos 1 caso esperado por ano entram na decomposição


def contagens(ids: pl.DataFrame) -> np.ndarray:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(
        pl.col("periodo").str.slice(0, 4).cast(pl.Int32).alias("ano"), pl.col("cd_setor").cast(pl.String))
    t = t.filter(pl.col("ano").is_in(list(YEARS))).group_by("cd_setor", "ano").agg(pl.col("n_total").sum())
    w = t.pivot(on="ano", index="cd_setor", values="n_total").fill_null(0.0)
    return ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select([str(a) for a in YEARS]).to_numpy().astype(float)


def decompoe(Y: np.ndarray, M: np.ndarray) -> dict:
    """Y, M: setores × anos (observado e esperado pelo tecido)."""
    ly, lm = np.log(Y + 0.5), np.log(M + 0.5)
    R = ly - lm
    T = Y.shape[1]
    total = float(np.mean([np.var(ly[:, t]) for t in range(T)]))
    tecido = float(np.mean([np.var(lm[:, t]) for t in range(T)]))
    covs = [np.cov(R[:, a], R[:, b])[0, 1] for a in range(T) for b in range(T) if a < b]
    estavel = float(np.mean(covs))
    residuo = float(np.mean([np.var(R[:, t]) for t in range(T)]))
    ruido = float(np.mean(1.0 / (Y.mean(axis=1) + 0.5)))
    cruz = total - tecido - residuo
    lags = {}
    for L in range(1, T):
        lags[L] = float(np.mean([np.corrcoef(R[:, t], R[:, t + L])[0, 1] for t in range(T - L)]))
    raw = {L: float(np.mean([np.corrcoef(ly[:, t], ly[:, t + L])[0, 1] for t in range(T - L)])) for L in range(1, T)}
    # decaimento exponencial r(L) = c·φ^L ajustado em log
    Ls = np.array(list(lags))
    rs = np.clip(np.array(list(lags.values())), 1e-6, None)
    slope, inter = np.polyfit(Ls, np.log(rs), 1)
    phi = float(np.exp(slope))
    meia_vida = float(np.log(0.5) / np.log(phi)) if 0 < phi < 1 else float("inf")
    return {"variancia_total": total, "tecido": tecido, "memoria_estavel": estavel, "transitoria": residuo - estavel,
            "ruido_poisson_estimado": ruido, "covariancia_tecido_residuo": cruz,
            "partes": {"tecido": tecido / total, "memoria_estavel": estavel / total, "transitoria": (residuo - estavel) / total,
                       "covariancia": cruz / total},
            "persistencia_residuo": lags, "persistencia_bruta": raw, "phi_anual": phi, "meia_vida_anos": meia_vida}


def run(log=print) -> dict:
    ids, E, names = setor_exposicao()
    Y = contagens(ids)
    lam = em_fit_multi(E, Y)
    M = E @ lam
    keep = M.mean(axis=1) >= MIN_ESPERADO
    rep = decompoe(Y[keep], M[keep]) | {"setores": int(keep.sum()), "anos": list(YEARS), "min_esperado": MIN_ESPERADO}
    # mesma decomposição só com os setores de muito crime (contagem esperada ≥ 10/ano): menos ruído de Poisson
    alto = M.mean(axis=1) >= 10
    rep["setores_altos"] = decompoe(Y[alto], M[alto]) | {"setores": int(alto.sum())}
    (out_dir() / "memoria.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    p = rep["partes"]
    log(f"memória: tecido {p['tecido']:.0%}, memória estável {p['memoria_estavel']:.0%}, transitória {p['transitoria']:.0%} "
        f"(covariância {p['covariancia']:+.0%}); persistência do resíduo {[round(v, 2) for v in rep['persistencia_residuo'].values()]}; "
        f"meia-vida {rep['meia_vida_anos']:.1f} anos")
    return rep
