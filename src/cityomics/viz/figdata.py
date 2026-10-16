"""Tabelas prontas para as figuras (cache em ``data/processed/figdata/``).

Cada função lê os resultados já gravados pelo benchmark e pelo atlas e devolve só agregados. O
período ``dev`` usa a avaliação de 2025; o período ``2026`` lê o pacote congelado e exige o cofre
aberto (D52), checado em ``figures/common.py``.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

from cityomics.eval import inference, scores
from cityomics.paths import processed_dir

NOMES_MODELO = {
    "media_historica": "Historical mean", "glm": "NB-GLM", "kde": "KDE", "chronos": "Chronos (zero-shot)",
    "gwr_distrito": "GWR (district)", "painel_espacial": "Spatial panel", "maxent": "MaxEnt", "bym2": "BYM2",
    "spde": "SPDE / LGCP", "hawkes": "Hawkes", "lgbm_nucleo": "LightGBM (core)", "lgbm_sem_crime": "LightGBM (no crime history)",
    "lgbm_completo": "LightGBM (full)", "gnn": "Graph neural network", "ensemble": "Ensemble",
}


def figdata_dir():
    d = processed_dir() / "figdata"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cached(name: str, fn, refresh: bool = False) -> pl.DataFrame:
    p = figdata_dir() / f"{name}.parquet"
    if p.exists() and not refresh:
        return pl.read_parquet(p)
    df = fn()
    df.write_parquet(p)
    return df


def load_eval(tag: str = "dev"):
    """Previsões de 2025 com o ensemble reconstruído, dispersões e distrito de cada linha."""
    import pyarrow.parquet as pq

    from cityomics.models import select_run

    t = pl.from_arrow(pq.read_table(processed_dir() / "modelo" / "tabela_celular_2022_2025.parquet", columns=["cd_setor", "cd_dist"]))
    ev, mu, phi, dist = select_run.load(t, tag)
    geo = pl.read_parquet(processed_dir() / "alvos" / "celular_setor_mes.parquet", columns=["cd_setor", "periodo", "n_geo"])
    ev = ev.join(geo.rename({"periodo": "mes"}), on=["cd_setor", "mes"], how="left").with_columns(pl.col("n_geo").fill_null(0))
    return ev, mu, phi, dist


def forest(tag: str = "dev", refresh: bool = False) -> pl.DataFrame:
    def build():
        ev, mu, phi, dist = load_eval(tag)
        y = ev["y"].to_numpy().astype(float)
        crps = {m: scores.crps_nb(y, mu[m], phi[m]) for m in mu}
        sel = json.loads((processed_dir().parents[1] / "prereg" / f"selection_{tag}.json").read_text())
        rows = []
        for m in mu:
            if m == "glm":
                continue
            r = inference.cluster_bootstrap_diff(crps[m], crps["glm"], dist, n_boot=2000)
            pre = sel["contra_melhor_baseline"].get(m, {})
            rows.append({"modelo": m, "nome": NOMES_MODELO[m], "diff": r["diff"], "ci_low": r["ci_low"], "ci_high": r["ci_high"],
                         "p_adj": pre.get("p_adj", np.nan), "crps": float(np.mean(crps[m])), "crps_glm": float(np.mean(crps["glm"]))})
        return pl.DataFrame(rows).sort("diff")
    return _cached(f"fig5_forest_{tag}", build, refresh)


def capture_curves(tag: str = "dev", models=("media_historica", "ensemble"), shares=None, n_sim: int = 50,
                   refresh: bool = False) -> pl.DataFrame:
    """Curvas de captura médias dos 12 meses: acaso, modelos, teto de ruído e oráculo; n_total e n_geo."""
    shares = np.unique(np.concatenate([np.geomspace(0.001, 0.3, 60), [0.01, 0.05]])) if shares is None else np.asarray(shares)

    def build():
        ev, mu, phi, _ = load_eval(tag)
        mes = ev["mes"].to_numpy()
        area = ev["area_km2"].to_numpy().astype(float)
        obs = {"n_total": ev["y"].to_numpy().astype(float), "n_geo": ev["n_geo"].to_numpy().astype(float)}
        rng = np.random.default_rng(0)
        rows = []

        def curve(rank, a, o):
            order = np.argsort(-rank, kind="stable")
            ca = np.cumsum(a[order]) / a.sum()
            co = np.cumsum(o[order]) / max(o.sum(), 1e-12)
            return np.interp(shares, ca, co)

        for alvo, y in obs.items():
            acc = {}
            for m in np.unique(mes):
                i = mes == m
                a = area[i]
                for name in models:
                    acc.setdefault(name, []).append(curve(mu[name][i] / a, a, y[i]))
                acc.setdefault("oraculo", []).append(curve(y[i] / a, a, y[i]))
                best = "ensemble"
                n, p = scores.nb_scipy(mu[best][i], phi[best])
                sims = [curve(mu[best][i] / a, a, rng.negative_binomial(n, p).astype(float)) for _ in range(n_sim)]
                acc.setdefault("teto_ruido", []).append(np.mean(sims, axis=0))
            for name, cs in acc.items():
                c = np.mean(cs, axis=0)
                rows += [{"alvo": alvo, "curva": name, "area": float(s), "captura": float(v)} for s, v in zip(shares, c)]
            rows += [{"alvo": alvo, "curva": "acaso", "area": float(s), "captura": float(s)} for s in shares]
        return pl.DataFrame(rows)
    return _cached(f"fig5_captura_{tag}", build, refresh)


def within_corr(tag: str = "dev", refresh: bool = False) -> pl.DataFrame:
    def build():
        ev, mu, _, _ = load_eval(tag)
        y = ev["y"].to_numpy().astype(float)
        s = ev["cd_setor"].to_numpy()
        _, inv = np.unique(s, return_inverse=True)
        cnt = np.bincount(inv)
        dy = y - (np.bincount(inv, weights=y) / cnt)[inv]
        rows = []
        for m, v in mu.items():
            dm = v - (np.bincount(inv, weights=v) / cnt)[inv]
            r = float(np.corrcoef(dy, dm)[0, 1])
            tot = float(np.corrcoef(y, v)[0, 1])
            rows.append({"modelo": m, "nome": NOMES_MODELO[m], "r_dentro": r, "r_total": tot})
        return pl.DataFrame(rows).sort("r_dentro")
    return _cached(f"fig5_dentro_{tag}", build, refresh)


def calibration(tag: str = "dev", models=("glm", "lgbm_completo", "ensemble"), refresh: bool = False) -> pl.DataFrame:
    from cityomics.eval.calibration import reliability

    def build():
        ev, mu, phi, _ = load_eval(tag)
        ev_y = (ev["y"].to_numpy() >= 0.5).astype(float)
        rows = []
        for m in models:
            p = scores.prob_ge1(mu[m], phi[m])
            tab, ece = reliability(p, ev_y, bins=12)
            rows += [{"modelo": m, "nome": NOMES_MODELO[m], "prev": a, "obs": b, "n": c, "ece": ece} for a, b, c in tab]
        return pl.DataFrame(rows)
    return _cached(f"fig5_calibracao_{tag}", build, refresh)


def district_contrast() -> pl.DataFrame:
    """Habilidade relativa à média histórica (1 − CRPS/CRPS_média) por desfecho, distrito × trimestre."""
    r = json.loads((processed_dir() / "modelo" / "resultados_distrito_trimestre_2025.json").read_text())
    rows = []
    for o, v in r.items():
        ref = v["modelos"]["media_historica"]["crps"]
        for m, mv in v["modelos"].items():
            if m == "media_historica":
                continue
            rows.append({"desfecho": o, "modelo": m, "skill": 1 - mv["crps"] / ref, "crps": mv["crps"]})
    return pl.DataFrame(rows)


GENE_EN = {
    "area_terreno": "Lot area", "area_construida": "Built area", "n_unidades": "Units", "pavimentos": "Floors",
    "valor_m2_terreno": "Land value / m²", "valor_m2_construcao": "Building value / m²", "testada": "Street frontage",
    "aproveitamento": "Floor-area ratio", "uso_residencial": "Residential use", "uso_comercio": "Commercial use",
    "uso_servicos": "Service use", "uso_industria": "Industrial use", "uso_terreno": "Vacant land",
    "padrao_baixo": "Low building standard", "padrao_medio": "Middle building standard", "padrao_alto": "High building standard",
    "esquina": "Corner lot", "idade": "Building age", "cnpj_bar_restaurante": "Bars and restaurants",
    "cnpj_comercio_varejista": "Retail shops", "cnpj_comercio_atacado": "Wholesale", "cnpj_financeiro": "Banks and finance",
    "cnpj_industria": "Manufacturing firms", "cnpj_transporte_armazenagem": "Transport and storage", "cnpj_alojamento": "Lodging",
    "cnpj_educacao_saude": "Education and health", "cnpj_construcao_imobiliario": "Construction and real estate",
    "cnpj_servicos_pessoais": "Personal services", "cnpj_outros_servicos": "Other services", "cnpj_mei": "Micro-entrepreneurs (MEI)",
}


def dotplot(refresh: bool = False) -> pl.DataFrame:
    """Tipo × gene: fração de lotes que 'expressam' o gene e média padronizada (como no scanpy)."""
    def build():
        from cityomics.atlas import typing as T
        from cityomics.atlas.genes_lote import atlas_dir

        g = pl.read_parquet(atlas_dir() / "lote_genes_2025.parquet")
        Z, names, mask, raw = T.prepare(g)
        tipos = pl.read_parquet(atlas_dir() / "lote_tipos_2025.parquet").select("sql_base", "tipo")
        sq = g.filter(pl.col("tem_iptu"))["sql_base"]
        tp = pl.DataFrame({"sql_base": sq}).join(tipos, on="sql_base", how="left")["tipo"].to_numpy()
        med = np.median(raw, axis=0)
        rows = []
        for t in np.unique(tp):
            i = tp == t
            for j, n in enumerate(names):
                expr = raw[i, j] > (0 if (n.startswith("cnpj_") or n in ("esquina",) or n.startswith("uso_") or n.startswith("padrao_")) else med[j])
                rows.append({"tipo": t, "gene": n, "frac": float(expr.mean()), "z": float(Z[i, j].mean())})
        return pl.DataFrame(rows)
    return _cached("fig2_dotplot", build, refresh)
