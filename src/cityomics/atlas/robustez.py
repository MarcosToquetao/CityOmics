"""Checagens de robustez pedidas na revisão simulada do artigo (paper/review/decisao_editorial.md).

Seis análises, só nos distritos de exploração (D53) e sem 2026:

1. **Persistência só com eventos geocodificados:** a decomposição de ``memoria`` com ``n_geo`` no lugar
   de ``n_total``. A reconciliação reparte os eventos sem coordenada pelos 12 meses anteriores, o que
   pode fabricar persistência.
2. **Queda separada entre furto e roubo:** razões relativas 2022→2025 por classe para cada desfecho.
   Testa se "os polos mantiveram a taxa" é só a mistura furto/roubo de cada classe.
3. **Taxas com efeito de distrito:** y_s ~ Poisson(θ_d Σ_k E_sk λ_k), ajustado por EM alternado. Testa
   se as taxas e as assinaturas sobrevivem quando o nível de risco de cada distrito é absorvido.
4. **Poder do teste de dispersão:** simulação do χ² com 12 meses e taxa latente gama, por média e CV.
5. **Excesso de variância esperado pela escala:** parte do excesso no 1% de setores com mais crime se a
   sobredispersão relativa fosse a mesma em todos (binomial negativa com θ comum).
6. **Relógio bruto do roubo:** distribuição horária, sem modelo, nos setores em que o residencial
   horizontal popular domina o roubo esperado, contra os setores dominados pelo comércio.

Saída: ``data/processed/atlas/fenotipo/robustez.json``.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl
from scipy.stats import chi2, spearmanr

from cityomics.atlas import grupos as GR
from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import (EVENTOS, YEARS, _boot_picks, _log2_enriq, _participacao, matriz, out_dir,
                                      setor_exposicao)
from cityomics.atlas.memoria import MIN_ESPERADO, decompoe
from cityomics.paths import interim_dir, processed_dir

# grupos de classes pela família da tipagem (cityomics.atlas.grupos), sem nomes de tipos fixos


def _celular_ano(ids: pl.DataFrame, col: str) -> np.ndarray:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(
        pl.col("periodo").str.slice(0, 4).cast(pl.Int32).alias("ano"), pl.col("cd_setor").cast(pl.String))
    t = t.filter(pl.col("ano").is_in(list(YEARS))).group_by("cd_setor", "ano").agg(pl.col(col).sum().cast(pl.Float64))
    w = t.pivot(on="ano", index="cd_setor", values=col).fill_null(0.0)
    return ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select(
        [str(a) for a in YEARS]).to_numpy().astype(float)


def persistencia_geocodificada(ids, E) -> dict:
    out = {}
    for col in ("n_total", "n_geo"):
        Y = _celular_ano(ids, col)
        M = E @ em_fit_multi(E, Y)
        keep = M.mean(axis=1) >= MIN_ESPERADO
        d = decompoe(Y[keep], M[keep])
        out[col] = {"setores": int(keep.sum()), "partes": d["partes"], "persistencia_residuo": d["persistencia_residuo"],
                    "geocodificado": float(Y.sum())}
    return out


def queda_por_desfecho(ids, E, names, n_boot: int = 200) -> dict:
    tab = pl.read_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    dist = ids["cd_dist"].to_numpy()
    out = {}
    mix = {}
    for f in ("celular_furto", "celular_roubo"):
        tf = tab.filter(pl.col("fenotipo") == f)
        Y = np.column_stack([matriz(ids, tf, [a])[0][:, 0] for a in (2022, 2025)])
        lam = em_fit_multi(E, Y)
        c = lam * E.sum(axis=0)[:, None]
        rtot = c[:, 1].sum() / c[:, 0].sum()
        r = lam[:, 1] / np.where(lam[:, 0] > 0, lam[:, 0], np.nan) / rtot
        boot = np.empty((n_boot, len(names)))
        for b, idx in enumerate(_boot_picks(dist, n_boot, seed=2)):
            lb = em_fit_multi(E[idx], Y[idx])
            cb = lb * E[idx].sum(axis=0)[:, None]
            boot[b] = lb[:, 1] / np.where(lb[:, 0] > 0, lb[:, 0], np.nan) / (cb[:, 1].sum() / cb[:, 0].sum())
        lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
        out[f] = {"razao_cidade": float(rtot),
                  "classes": {nm: {"razao_rel": float(r[k]), "ic": [float(lo[k]), float(hi[k])]}
                              for k, nm in enumerate(names) if np.isfinite(r[k])},
                  "grupos": {g: _razao_grupo(E, Y, dist, GR.indices(names, g), rtot, n_boot)
                             for g in ("popular", "comercio", "polos", "estacoes", "residencial", "residencial_formal")}}
        mix[f] = c[:, 0]
    tot = mix["celular_furto"] + mix["celular_roubo"]
    out["parte_roubo_2022"] = {nm: float(mix["celular_roubo"][k] / tot[k]) for k, nm in enumerate(names) if tot[k] > 0}
    return out


def _razao_grupo(E, Y, dist, k: list[int], rtot: float, n_boot: int) -> dict:
    """Razão 2025/2022 do crime atribuído ao conjunto de classes ``k``, relativa à da cidade."""
    def razao(Ei, Yi):
        lb = em_fit_multi(Ei, Yi)
        cb = lb * Ei.sum(axis=0)[:, None]
        return (cb[k, 1].sum() / max(cb[k, 0].sum(), 1e-12)) / (cb[:, 1].sum() / cb[:, 0].sum())
    obs = razao(E, Y)
    boot = [razao(E[idx], Y[idx]) for idx in _boot_picks(dist, n_boot, seed=3)]
    return {"razao_rel": float(obs), "ic": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}


def em_distrito(E: np.ndarray, Y: np.ndarray, dist: np.ndarray, n_iter: int = 30) -> tuple[np.ndarray, np.ndarray]:
    """λ (K×F) e θ_d (por distrito, comum a todos os desfechos) com y ~ Poisson(θ_d Σ E λ)."""
    _, g = np.unique(dist, return_inverse=True)
    theta = np.ones(g.max() + 1)
    for _ in range(n_iter):
        lam = em_fit_multi(E * theta[g][:, None], Y, n_iter=300)
        mu = (E @ lam).sum(axis=1)
        theta = np.bincount(g, weights=Y.sum(axis=1)) / np.maximum(np.bincount(g, weights=mu), 1e-12)
        theta /= np.average(theta[g], weights=mu)
    return em_fit_multi(E * theta[g][:, None], Y, n_iter=500), theta


def efeito_distrito(ids, E, names) -> dict:
    dist = ids["cd_dist"].to_numpy()
    y = _celular_ano(ids, "n_total")[:, -1:]
    lam0 = em_fit_multi(E, y)[:, 0]
    lam1, theta = em_distrito(E, y, dist)
    ok = (lam0 > 0) | (lam1[:, 0] > 0)
    rho_taxas = float(spearmanr(lam0[ok], lam1[ok, 0]).statistic)
    tab = pl.read_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    Yf, fen = matriz(ids, tab, (2024, 2025))
    L0 = em_fit_multi(E, Yf)
    L1, _ = em_distrito(E, Yf, dist)
    S0, S1 = _participacao(L0, E), _participacao(L1, E)
    rho_fen = [float(spearmanr(S0[:, j], S1[:, j]).statistic) for j in range(len(fen))]
    top0, top1 = np.argmax(_log2_enriq(S0), axis=0), np.argmax(_log2_enriq(S1), axis=0)
    return {"celular_2025": {"spearman_taxas": rho_taxas, "theta_p10_p90": [float(np.percentile(theta, 10)), float(np.percentile(theta, 90))],
                             "taxas_sem": {nm: float(lam0[k]) for k, nm in enumerate(names)},
                             "taxas_com": {nm: float(lam1[k, 0]) for k, nm in enumerate(names)}},
            "assinaturas": {"spearman_participacao_mediana": float(np.median(rho_fen)), "por_fenotipo": dict(zip(fen, rho_fen)),
                            "mesma_classe_no_topo": int((top0 == top1).sum()), "fenotipos": len(fen),
                            "classes_distintas_no_topo_com": int(len(set(top1.tolist())))}}


def poder_dispersao(meses: int = 12, n_sim: int = 4000, seed: int = 3) -> dict:
    rng = np.random.default_rng(seed)
    crit = chi2.ppf(0.95, meses - 1)
    out = {}
    for mu in (0.25, 0.5, 1.0, 2.0, 5.0, 10.0):
        for cv in (0.3, 0.5, 1.0):
            k = 1 / cv ** 2
            lam = rng.gamma(k, mu / k, size=(n_sim, meses))
            y = rng.poisson(lam)
            m = y.mean(axis=1)
            ok = m > 0
            stat = ((y - m[:, None]) ** 2).sum(axis=1)[ok] / m[ok]
            out[f"mu={mu}|cv={cv}"] = float(np.mean(stat > crit))
    return out


def _celular_mes_2025(ids) -> tuple[np.ndarray, np.ndarray]:
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).filter(
        pl.col("periodo").str.starts_with("2025")).with_columns(pl.col("cd_setor").cast(pl.String))
    w = t.pivot(on="periodo", index="cd_setor", values="n_total").fill_null(0.0)
    cols = sorted(c for c in w.columns if c != "cd_setor")
    Y = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select(cols).to_numpy().astype(float)
    return Y, Y.mean(axis=1)


def escala_do_excesso(ids) -> dict:
    Y, m = _celular_mes_2025(ids)
    n = Y.shape[1]
    ok = m > 0
    Y, m = Y[ok], m[ok]
    ss = ((Y - m[:, None]) ** 2).sum(axis=1)
    exc = np.clip(ss - (n - 1) * m, 0, None)
    inv_theta = float(np.sum(ss - (n - 1) * m) / ((n - 1) * np.sum(m ** 2)))
    top = np.argsort(-m)[: max(1, len(m) // 100)]
    return {"setores": int(ok.sum()), "media_mensal_mediana": float(np.median(m)), "parte_media_ge_1": float(np.mean(m >= 1)),
            "inv_theta_comum": inv_theta, "parte_excesso_top1_observada": float(exc[top].sum() / exc.sum()),
            "parte_excesso_top1_esperada_theta_comum": float((m[top] ** 2).sum() / (m ** 2).sum()),
            "parte_crime_top1": float(m[top].sum() / m.sum())}


def relogio_bruto(ids, E, names) -> dict:
    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "cd_setor"])
    ev = ev[(ev["desfecho"] == "celular_roubo") & ev["data_fato"].dt.year.isin([2024, 2025]) & ev["cd_setor"].notna()]
    ev = ev[ev["data_fato"].dt.weekday < 5]
    hh = pd.to_datetime(ev["hora_fato"].astype("string"), format="%H:%M:%S", errors="coerce")
    ev = ev.assign(h=hh.dt.hour, mi=hh.dt.minute)[hh.notna()]
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    ev["i"] = ev["cd_setor"].astype(str).map(pos)
    ev = ev[ev["i"].notna()]
    y = np.bincount(ev["i"].astype(int), minlength=ids.height).astype(float)[:, None]
    lam = em_fit_multi(E, y)[:, 0]
    contrib = E * lam[None, :]
    share = contrib / np.maximum(contrib.sum(axis=1, keepdims=True), 1e-12)
    kp = GR.indices(names, "popular")
    kc = GR.indices(names, "comercio_amplo")
    grupos = {"popular_domina": share[:, kp].sum(axis=1) >= 0.5, "comercio_domina": share[:, kc].sum(axis=1) >= 0.5,
              "todos": np.ones(ids.height, bool)}
    out = {}
    for nome, mask in grupos.items():
        sel = ev[mask[ev["i"].astype(int).to_numpy()]]
        h = sel["h"].to_numpy().astype(int)
        boot = []
        rng = np.random.default_rng(4)
        for _ in range(500):
            hb = rng.choice(h, size=len(h), replace=True)
            boot.append(np.mean((hb >= 4) & (hb < 6)))
        out[nome] = {"setores": int(mask.sum()), "eventos": int(len(sel)), "parte_04_06": float(np.mean((h >= 4) & (h < 6))),
                     "ic": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                     "pico": int(np.bincount(h, minlength=24).argmax()),
                     "parte_minuto_zero": float(np.mean(sel["mi"].to_numpy() == 0))}
    h4 = ev[(ev["h"] >= 4) & (ev["h"] < 6)]
    out["minuto_zero_04_06"] = float(np.mean(h4["mi"].to_numpy() == 0))
    return out


def relogio_bruto_composicao(ids, E, names, n_boot: int = 500) -> dict:
    """Relógio sem modelo com setores definidos pela composição (parte da testada dos lotes), não pelo roubo
    esperado: não depende de λ, que é quase nulo nas classes residenciais. Intervalos por bootstrap de distritos."""
    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "cd_setor"])
    ev = ev[(ev["desfecho"] == "celular_roubo") & ev["data_fato"].dt.year.isin([2024, 2025]) & ev["cd_setor"].notna()]
    ev = ev[ev["data_fato"].dt.weekday < 5]
    hh = pd.to_datetime(ev["hora_fato"].astype("string"), format="%H:%M:%S", errors="coerce")
    ev = ev.assign(h=hh.dt.hour)[hh.notna()]
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    ev["i"] = ev["cd_setor"].astype(str).map(pos)
    ev = ev[ev["i"].notna()]
    i = ev["i"].astype(int).to_numpy()
    pre = ((ev["h"] >= 4) & (ev["h"] < 6)).to_numpy()
    lotes = [k for k, n in enumerate(names) if not n.startswith(("rua_", "n_"))]
    fr = E[:, lotes].sum(axis=1)
    parte = lambda g: np.divide(E[:, GR.indices(names, g)].sum(axis=1), fr, out=np.zeros_like(fr), where=fr > 0)  # noqa: E731
    dist = ids["cd_dist"].to_numpy()
    rng = np.random.default_rng(5)
    out = {}
    for nome, m in (("popular_maioria_testada", parte("popular") >= 0.5), ("comercio_maioria_testada", parte("comercio_amplo") >= 0.5),
                    ("todos", np.ones(ids.height, bool))):
        sel = m[i]
        p, d = pre[sel], dist[i[sel]]
        ud = np.unique(d)
        por = {u: p[d == u] for u in ud}
        boot = [np.concatenate([por[u] for u in rng.choice(ud, len(ud))]).mean() for _ in range(n_boot)]
        out[nome] = {"setores": int(m.sum()), "eventos": int(sel.sum()), "parte_04_06": float(p.mean()),
                     "ic_distritos": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}
    return out


def run(log=print) -> dict:
    ids, E, names = setor_exposicao()
    rep = {"persistencia": persistencia_geocodificada(ids, E)}
    log(f"persistência: {rep['persistencia']}")
    rep["queda_por_desfecho"] = queda_por_desfecho(ids, E, names)
    log(f"queda por desfecho: {rep['queda_por_desfecho']}")
    rep["efeito_distrito"] = efeito_distrito(ids, E, names)
    log(f"efeito de distrito: {rep['efeito_distrito']['celular_2025']['spearman_taxas']:.2f}; "
        f"{rep['efeito_distrito']['assinaturas']['spearman_participacao_mediana']:.2f}")
    rep["poder_dispersao"] = poder_dispersao()
    rep["escala_do_excesso"] = escala_do_excesso(ids)
    log(f"escala do excesso: {rep['escala_do_excesso']}")
    rep["relogio_bruto"] = relogio_bruto(ids, E, names)
    log(f"relógio bruto: {rep['relogio_bruto']}")
    rep["relogio_bruto_composicao"] = relogio_bruto_composicao(ids, E, names)
    log(f"relógio bruto pela composição: {rep['relogio_bruto_composicao']}")
    prev = json.loads((out_dir() / "previsibilidade.json").read_text())
    rep["dispersao_geocodificada"] = prev.get("dispersao_setor_mes_geocodificado")
    (out_dir() / "robustez.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return rep


if __name__ == "__main__":
    run()
