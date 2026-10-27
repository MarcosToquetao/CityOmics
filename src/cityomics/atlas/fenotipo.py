"""Painel de fenótipos, relógio do tecido e queda 2022→2025 (pilotos P1–P3, docs/NARRATIVA.md).

Exploratório (D40): usa os tipos já fixados (D53), só distritos fora do cofre espacial e nada de 2026.

- ``build_eventos``: fenótipos da base principal (``ingest.ssp.fenotipo_ssp``) atribuídos a setor e
  distrito, mais celular (roubo e furto) e letal dos próprios eventos
  → ``data/interim/eventos_multi_atribuidos.parquet`` (com coordenadas; só local).
- ``alvos``: reconciliação estratificada (``units.reconcile``) de cada fenótipo, setor × ano.
- ``assinaturas`` (P1): λ por classe de célula × fenótipo (EM do Poisson linear), participação de cada
  classe no crime esperado de cada fenótipo, enriquecimento contra a média dos fenótipos com bootstrap
  conjunto por distrito, controle positivo (trânsito → vias arteriais) e validação pontual por fenótipo.
- ``programas`` (P1): NMF setor × fenótipo, com o número de programas escolhido pela estabilidade entre
  sementes, e a associação de cada programa com a composição do setor.
- ``relogio`` (P2): λ por período do dia, contraste entre classes contra permutação dos períodos dentro
  do distrito, réplica 2024 × 2025; perfil por hora (roubo, hora exata) e dia útil × fim de semana.
- ``queda`` (P3): λ por ano (2022–2025) com a composição de 2025 (98% dos lotes ficam na mesma família
  por ano) e a contribuição de cada classe para a variação do total.

Saídas em ``data/processed/atlas/fenotipo/``: só agregados por classe, exceto as tabelas setor × ano e o
uso dos programas por setor, que ficam locais (D49, D60).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi, point_validation
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.spots import exposure_matrix
from cityomics.ingest import ssp
from cityomics.ingest.schema import norm_text
from cityomics.paths import interim_dir, processed_dir, raw_dir

YEARS = (2022, 2023, 2024, 2025)
ANOS_ASSINATURA = (2024, 2025)
KEY = ["delegacia_registro", "ano_bo", "num_bo"]
PERIODOS = ["madrugada", "manha", "tarde", "noite"]
PERIODO_TXT = {"DE MADRUGADA": "madrugada", "PELA MANHA": "manha", "A TARDE": "tarde", "A NOITE": "noite"}
COBERTURA_MIN = 0.8   # fenótipos com ao menos 80% de coordenadas entram na validação pontual
PESO_MIN = 0.01       # classes com ao menos 1% do crime esperado entram nos contrastes
RELOGIO = ("celular_roubo", "celular_furto", "roubo_outros", "transito")
EVENTOS = "eventos_multi_atribuidos.parquet"


def out_dir():
    d = atlas_dir() / "fenotipo"
    d.mkdir(parents=True, exist_ok=True)
    return d


# --- eventos e alvos ----------------------------------------------------------------------------

def build_eventos(years=YEARS, log=print) -> pd.DataFrame:
    from cityomics.units import assign
    from cityomics.units.setores import load_setores

    keys = (pd.concat([pd.read_parquet(guard.pre2026(raw_dir() / "bo" / f"celular_{y}.parquet"), columns=KEY)
                       for y in years]).astype(str).drop_duplicates().assign(_cel=True))
    frames = []
    for y in years:
        df = pd.read_parquet(guard.pre2026(raw_dir() / "bo" / f"ssp_{y}.parquet"))
        cel = df[KEY].astype(str).merge(keys, on=KEY, how="left")["_cel"].eq(True).to_numpy()
        f = ssp.fenotipo_ssp(df, pd.Series(cel, index=df.index))
        sel = df[f.notna()].copy()
        sel["desfecho"] = f[f.notna()].astype(str)
        sel["natureza"] = sel["natureza_norm"]
        sel["estrito"] = True
        frames.append(ssp.to_events(sel))
        log(f"ssp {y}: {len(sel):,} eventos no painel ({cel.mean():.1%} das linhas com BO de celular)")
    ev = pd.concat(frames, ignore_index=True).sort_values("arquivo_ano").drop_duplicates("evento_id", keep="last")
    ev = ev[(ev["data_fato"] >= "2022-01-01") & (ev["data_fato"] < "2026-01-01")]
    at = assign.assign_events(ev, load_setores(), assign.load_lookups())
    # lesão dolosa só fora de residências (violência doméstica fora do escopo, D14)
    at = at[~((at["desfecho"] == "lesao_dolosa") & (at["estrato"] == "residencia"))]
    cel = pd.read_parquet(guard.pre2026(interim_dir() / "eventos_celular_atribuidos.parquet"))
    cel["desfecho"] = np.where(cel["natureza"].eq("ROUBO DE CELULAR"), "celular_roubo", "celular_furto")
    let = pd.read_parquet(guard.pre2026(interim_dir() / "eventos_letal_atribuidos.parquet"))
    out = pd.concat([at, cel, let], ignore_index=True)
    out = out[(out["data_fato"] >= "2022-01-01") & (out["data_fato"] < "2026-01-01")].reset_index(drop=True)
    out.to_parquet(interim_dir() / EVENTOS, index=False)
    log("painel: " + ", ".join(f"{k} {v:,}" for k, v in out["desfecho"].value_counts().items()))
    return out


def alvos(log=print) -> pl.DataFrame:
    from cityomics.units import reconcile, transit
    from cityomics.units.setores import load_setores

    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "cd_setor", "cd_dist", "estrato", "data_fato"])
    setores = load_setores()
    perto = transit.station_setores(setores, transit.load_stations(log=log))
    rows = []
    for f, g in ev.groupby("desfecho"):
        a = reconcile.reconcile(g, setores, freq="M", eligible={"trilhos": perto})
        a["ano"] = a["periodo"].dt.year
        rows.append(a.groupby(["cd_setor", "cd_dist", "ano"], as_index=False)[["n_geo", "n_total"]].sum().assign(fenotipo=f))
    out = pl.from_pandas(pd.concat(rows, ignore_index=True)).with_columns(
        pl.col("cd_setor").cast(pl.String), pl.col("cd_dist").cast(pl.String), pl.col("ano").cast(pl.Int32))
    out.write_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    log(f"alvos: {out['fenotipo'].n_unique()} fenótipos × {out['cd_setor'].n_unique():,} setores × anos {sorted(out['ano'].unique().to_list())}")
    return out


# --- composição e matrizes ----------------------------------------------------------------------

def setor_exposicao() -> tuple[pl.DataFrame, np.ndarray, list[str]]:
    """Setores de exploração, matriz de exposição na escala de ``attribution.run`` (km; estações por unidade)."""
    setor = pl.read_parquet(atlas_dir() / f"setor_composicao_{REF_YEAR}.parquet")
    ex = setor.filter(pl.Series(guard.explore_mask(setor["cd_dist"].to_numpy())))
    E, names = exposure_matrix(ex)
    E = E / 1000.0
    est = [i for i, n in enumerate(names) if n.startswith("n_")]
    E[:, est] *= 1000.0
    return ex.select("cd_setor", "cd_dist"), E, names


def matriz(ids: pl.DataFrame, tab: pl.DataFrame, anos, col: str = "n_total") -> tuple[np.ndarray, list[str]]:
    t = tab.filter(pl.col("ano").is_in(list(anos))).group_by("cd_setor", "fenotipo").agg(pl.col(col).sum())
    w = t.pivot(on="fenotipo", index="cd_setor", values=col).fill_null(0.0)
    fen = sorted([c for c in w.columns if c != "cd_setor"], key=lambda c: -float(w[c].sum()))
    Y = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select(fen).to_numpy().astype(float)
    return Y, fen


def _boot_picks(clusters: np.ndarray, n_boot: int, seed: int):
    rng = np.random.default_rng(seed)
    uc, inv = np.unique(clusters, return_inverse=True)
    rows = [np.where(inv == i)[0] for i in range(len(uc))]
    for _ in range(n_boot):
        yield np.concatenate([rows[i] for i in rng.integers(0, len(uc), len(uc))])


def _participacao(lam: np.ndarray, E: np.ndarray) -> np.ndarray:
    c = lam * E.sum(axis=0)[:, None]
    return c / np.where(c.sum(axis=0) > 0, c.sum(axis=0), 1.0)


def _log2_enriq(S: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    return np.log2((S + eps) / (S.mean(axis=1, keepdims=True) + eps))


# --- P1: assinaturas ----------------------------------------------------------------------------

def assinaturas(anos=ANOS_ASSINATURA, n_boot: int = 200, validar: bool = True, log=print) -> dict:
    from scipy.stats import spearmanr

    ids, E, names = setor_exposicao()
    tab = pl.read_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    Y, fen = matriz(ids, tab, anos)
    lam = em_fit_multi(E, Y)
    S = _participacao(lam, E)
    enr = _log2_enriq(S)
    dist = ids["cd_dist"].to_numpy()
    boot = np.empty((n_boot, *enr.shape))
    for b, idx in enumerate(_boot_picks(dist, n_boot, seed=0)):
        boot[b] = _log2_enriq(_participacao(em_fit_multi(E[idx], Y[idx]), E[idx]))
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)

    rows = []
    for j, f in enumerate(fen):
        for k, n in enumerate(names):
            rows.append({"fenotipo": f, "classe": n, "lambda": float(lam[k, j]), "participacao": float(S[k, j]),
                         "log2_enriq": float(enr[k, j]), "ic_lo": float(lo[k, j]), "ic_hi": float(hi[k, j])})
    mat = pl.DataFrame(rows)
    mat.write_parquet(out_dir() / "assinaturas.parquet")

    # classe mais enriquecida por fenótipo, entre as que têm ao menos 2% do fenótipo e IC acima de zero
    topo = {}
    for j, f in enumerate(fen):
        ok = [k for k in range(len(names)) if S[k, j] >= 0.02 and lo[k, j] > 0]
        topo[f] = names[max(ok, key=lambda k: enr[k, j])] if ok else None
    rho = spearmanr(S).statistic if len(fen) > 2 else np.array([[1.0]])
    off = rho[np.triu_indices(len(fen), 1)]
    k_art = names.index("rua_arterial_m")
    ruas = [names.index(c) for c in ("rua_arterial_m", "rua_coletora_m", "rua_local_m")]
    jt = fen.index("transito") if "transito" in fen else None
    controle = None
    if jt is not None:
        controle = {"lambda_por_km": {names[k]: float(lam[k, jt]) for k in ruas},
                    "arterial_maior_lambda_entre_ruas": bool(np.argmax(lam[ruas, jt]) == 0),
                    "log2_enriq_arterial": float(enr[k_art, jt]), "ic": [float(lo[k_art, jt]), float(hi[k_art, jt])],
                    "participacao_ruas": float(S[ruas, jt].sum())}

    val = {}
    if validar:
        ev = pl.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "coord_valida", "latitude",
                                                                "longitude", "cd_dist"])
        ev = ev.filter(pl.col("data_fato").dt.year().is_in(list(anos)))
        ev = ev.filter(pl.Series(guard.explore_mask(ev["cd_dist"].cast(pl.String).fill_null("").to_numpy())))
        tipos = [n for n in names if not n.startswith(("rua_", "n_"))]
        for j, f in enumerate(fen):
            e = ev.filter(pl.col("desfecho") == f)
            cob = float(e["coord_valida"].mean()) if e.height else 0.0
            if cob < COBERTURA_MIN or e.height < 500:
                val[f] = {"cobertura": cob, "eventos": e.height, "spearman": None, "spearman_lotes": None}
                continue
            pv = point_validation(ev=e.filter(pl.col("coord_valida")).select("latitude", "longitude", "cd_dist"), log=log)
            lam_f = pl.DataFrame({"classe": names, "lambda": lam[:, j]})
            pv = pv.join(lam_f, on="classe", how="inner").filter(pl.col("exposicao") > 0)
            lt = pv.filter(pl.col("classe").is_in(tipos))
            val[f] = {"cobertura": cob, "eventos": e.height,
                      "spearman": float(spearmanr(pv["lambda"], pv["taxa_observada"]).statistic),
                      "spearman_lotes": float(spearmanr(lt["lambda"], lt["taxa_observada"]).statistic)}
            log(f"validação pontual {f}: ρ = {val[f]['spearman']:.2f} (só lotes {val[f]['spearman_lotes']:.2f})")

    distintos = sorted({v for v in topo.values() if v})
    rho_lotes = [v["spearman_lotes"] for v in val.values() if v.get("spearman_lotes") is not None]
    rep = {"anos": list(anos), "fenotipos": fen, "eventos": {f: float(Y[:, j].sum()) for j, f in enumerate(fen)},
           "classe_mais_enriquecida": topo, "classes_distintas_no_topo": distintos,
           "spearman_participacao_mediana": float(np.median(off)), "spearman_participacao_min": float(off.min()),
           "controle_positivo_transito": controle, "validacao_pontual": val,
           "gate_G1": {"tres_ou_mais_assinaturas": len(distintos) >= 3,
                       "controle_positivo": bool(controle and controle["arterial_maior_lambda_entre_ruas"] and controle["ic"][0] > 0),
                       "validacao_mediana_lotes": float(np.median(rho_lotes)) if rho_lotes else None},
           "n_boot": n_boot}
    (out_dir() / "assinaturas.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"assinaturas: topo distinto em {len(distintos)} classes; ρ mediano entre fenótipos = {rep['spearman_participacao_mediana']:.2f}")
    return rep


# --- P1: programas (NMF) -----------------------------------------------------------------------

def _estabilidade(Hs: list[np.ndarray]) -> float:
    from scipy.optimize import linear_sum_assignment

    sims = []
    for a in range(len(Hs)):
        for b in range(a + 1, len(Hs)):
            A = Hs[a] / np.linalg.norm(Hs[a], axis=1, keepdims=True)
            B = Hs[b] / np.linalg.norm(Hs[b], axis=1, keepdims=True)
            C = A @ B.T
            r, c = linear_sum_assignment(-C)
            sims.append(C[r, c].mean())
    return float(np.mean(sims))


def programas(anos=ANOS_ASSINATURA, ks=range(2, 8), seeds: int = 10, alvo: float = 0.95, log=print) -> dict:
    from scipy.stats import spearmanr
    from sklearn.decomposition import NMF

    ids, E, names = setor_exposicao()
    tab = pl.read_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    Y, fen = matriz(ids, tab, anos)
    keep = Y.sum(axis=1) > 0
    X = Y[keep] / Y[keep].mean(axis=0)
    estab, erro = {}, {}
    for k in ks:
        fits = [NMF(k, init="random", random_state=s, max_iter=2000).fit(X) for s in range(seeds)]
        estab[k] = _estabilidade([m.components_ for m in fits])
        erro[k] = float(np.mean([m.reconstruction_err_ for m in fits]) / np.linalg.norm(X))
    # o menor k ≥ 3 estável: com k grande os programas viram fenótipos isolados, estáveis por construção
    estaveis = [k for k in ks if k >= 3 and estab[k] >= alvo]
    kstar = min(estaveis) if estaveis else max(estab, key=estab.get)
    m = NMF(kstar, init="nndsvda", random_state=0, max_iter=4000)
    W = m.fit_transform(X)
    H = m.components_ / m.components_.sum(axis=1, keepdims=True)
    uso = W / np.where(W.sum(axis=1, keepdims=True) > 0, W.sum(axis=1, keepdims=True), 1.0)
    comp = E[keep] / np.where(E[keep].sum(axis=1, keepdims=True) > 0, E[keep].sum(axis=1, keepdims=True), 1.0)
    progs = []
    for p in range(kstar):
        assoc = [(names[k], float(spearmanr(uso[:, p], comp[:, k]).statistic)) for k in range(len(names))]
        assoc.sort(key=lambda t: -t[1])
        progs.append({"programa": f"P{p + 1}", "fenotipos": {f: float(H[p, j]) for j, f in enumerate(fen)},
                      "fenotipos_topo": [fen[j] for j in np.argsort(-H[p])[:3]], "classes_associadas": assoc[:3]})
    pl.DataFrame({"cd_setor": ids["cd_setor"].to_numpy()[keep], **{f"P{p + 1}": uso[:, p] for p in range(kstar)}}).write_parquet(
        out_dir() / "programas_uso_setor.parquet")
    rep = {"anos": list(anos), "estabilidade": {str(k): v for k, v in estab.items()},
           "erro_relativo": {str(k): v for k, v in erro.items()}, "k": kstar, "programas": progs}
    (out_dir() / "programas.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"programas: k = {kstar} (estabilidade {estab[kstar]:.3f}); " +
        "; ".join(f"{p['programa']}: {'+'.join(p['fenotipos_topo'])}" for p in progs))
    return rep


# --- P2: relógio do tecido ---------------------------------------------------------------------

def periodo_do_dia(ev: pd.DataFrame) -> pd.Series:
    """Período do dia pela hora exata (0–5, 6–11, 12–17, 18–23) ou, sem ela, pelo campo período."""
    h = pd.to_datetime(ev["hora_fato"].astype("string"), format="%H:%M:%S", errors="coerce").dt.hour
    p_h = pd.cut(h, [-1, 5, 11, 17, 23], labels=PERIODOS).astype("string")
    p_t = ev["periodo"].astype("string").fillna("").map(norm_text).map(PERIODO_TXT).astype("string")
    return p_h.fillna(p_t)


def _contraste(lam: np.ndarray, E: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    tot = lam.sum(axis=1)
    P = lam / np.where(tot[:, None] > 0, tot[:, None], 1.0)
    w = tot * E.sum(axis=0)
    w = w / w.sum()
    pbar = w @ P
    H = float(np.sum(w[:, None] * (P - pbar) ** 2 / np.where(pbar > 0, pbar, 1.0)))
    return H, P, w


def _eventos_relogio(ids: pl.DataFrame, desfecho: str, anos) -> pd.DataFrame:
    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "periodo", "cd_setor", "cd_dist"])
    ev = ev[(ev["desfecho"] == desfecho) & ev["data_fato"].dt.year.isin(list(anos)) & ev["cd_setor"].notna()].copy()
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    ev["i"] = ev["cd_setor"].astype(str).map(pos)
    ev = ev[ev["i"].notna()].copy()
    ev["i"] = ev["i"].astype(int)
    ev["per"] = periodo_do_dia(ev)
    return ev


def relogio(desfechos=RELOGIO, anos=ANOS_ASSINATURA, n_perm: int = 200, log=print) -> dict:
    ids, E, names = setor_exposicao()
    n = ids.height
    dist_all = np.unique(ids["cd_dist"].to_numpy(), return_inverse=True)[1]
    rng = np.random.default_rng(0)
    rep, perfis = {}, []
    for d in desfechos:
        ev_all = _eventos_relogio(ids, d, anos)
        res = {"cobertura_periodo": float(ev_all["per"].notna().mean())}
        dev = {}
        for a in anos:
            ev = ev_all[(ev_all["data_fato"].dt.year == a) & ev_all["per"].notna()]
            i = ev["i"].to_numpy()
            p = ev["per"].map({q: j for j, q in enumerate(PERIODOS)}).to_numpy().astype(int)
            Y = np.bincount(i * 4 + p, minlength=n * 4).reshape(n, 4).astype(float)
            lam = em_fit_multi(E, Y)
            H, P, w = _contraste(lam, E)
            g = dist_all[i]
            o0 = np.argsort(g, kind="stable")
            Hp = np.empty(n_perm)
            for b in range(n_perm):
                o1 = np.lexsort((rng.random(len(g)), g))
                pp = np.empty_like(p)
                pp[o0] = p[o1]
                Yp = np.bincount(i * 4 + pp, minlength=n * 4).reshape(n, 4).astype(float)
                Hp[b] = _contraste(em_fit_multi(E, Yp, tol=1e-6), E)[0]
            pval = float((1 + np.sum(Hp >= H)) / (1 + n_perm))
            res[str(a)] = {"eventos": int(len(ev)), "H": H, "H_nulo_mediana": float(np.median(Hp)), "p": pval,
                           "H_nulo": Hp.tolist(), "cidade": dict(zip(PERIODOS, (w @ P).tolist()))}
            dev[a] = (P - w @ P, w)
            for k, nm in enumerate(names):
                perfis.append({"desfecho": d, "ano": a, "classe": nm, "peso": float(w[k]),
                               **{q: float(P[k, j]) for j, q in enumerate(PERIODOS)}})
        a0, a1 = anos[0], anos[-1]
        ok = (dev[a0][1] >= PESO_MIN) & (dev[a1][1] >= PESO_MIN)
        res["replica_r"] = float(np.corrcoef(dev[a0][0][ok].ravel(), dev[a1][0][ok].ravel())[0, 1])
        res["gate_G2"] = bool(all(res[str(a)]["p"] < 0.05 for a in anos) and res["replica_r"] >= 0.7)
        rep[d] = res
        log(f"relógio {d}: p = {[res[str(a)]['p'] for a in anos]}; réplica r = {res['replica_r']:.2f}")
    pl.DataFrame(perfis).write_parquet(out_dir() / "relogio_periodos.parquet")
    rep["horas_roubo_celular"] = _horas(ids, E, names, anos, log=log)
    rep["fim_de_semana"] = _fim_de_semana(ids, E, names, desfechos, anos)
    (out_dir() / "relogio.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return rep


def _horas(ids, E, names, anos, desfecho: str = "celular_roubo", log=print) -> dict:
    ev = _eventos_relogio(ids, desfecho, anos)
    h = pd.to_datetime(ev["hora_fato"].astype("string"), format="%H:%M:%S", errors="coerce").dt.hour
    ev = ev[h.notna()]
    h = h[h.notna()].astype(int).to_numpy()
    n = ids.height
    Y = np.bincount(ev["i"].to_numpy() * 24 + h, minlength=n * 24).reshape(n, 24).astype(float)
    lam = em_fit_multi(E, Y)
    _, P, w = _contraste(lam, E)
    rows = [{"classe": nm, "peso": float(w[k]), **{f"h{j:02d}": float(P[k, j]) for j in range(24)}} for k, nm in enumerate(names)]
    pl.DataFrame(rows).write_parquet(out_dir() / "relogio_horas_roubo_celular.parquet")
    pico = {nm: int(np.argmax(P[k])) for k, nm in enumerate(names) if w[k] >= PESO_MIN}
    log("pico horário do roubo de celular: " + ", ".join(f"{k} {v}h" for k, v in pico.items()))
    return {"eventos_hora_exata": int(len(ev)), "pico": pico}


def _fim_de_semana(ids, E, names, desfechos, anos) -> dict:
    dias = pd.date_range(f"{anos[0]}-01-01", f"{anos[-1]}-12-31")
    n_fds, n_util = int((dias.dayofweek >= 5).sum()), int((dias.dayofweek < 5).sum())
    n = ids.height
    out = {}
    for d in desfechos:
        ev = _eventos_relogio(ids, d, anos)
        fds = (ev["data_fato"].dt.dayofweek >= 5).to_numpy().astype(int)
        Y = np.bincount(ev["i"].to_numpy() * 2 + fds, minlength=n * 2).reshape(n, 2).astype(float)
        lam = em_fit_multi(E, Y)
        _, _, w = _contraste(lam, E)
        razao = (lam[:, 1] / n_fds) / np.where(lam[:, 0] > 0, lam[:, 0] / n_util, np.nan)
        out[d] = {nm: float(razao[k]) for k, nm in enumerate(names) if w[k] >= PESO_MIN}
    return out


# --- P3: queda 2022 → 2025 ---------------------------------------------------------------------

def _decompoe(lam: np.ndarray, E: np.ndarray, j0: int = 0, j1: int = -1) -> dict:
    c = lam * E.sum(axis=0)[:, None]
    tot = c.sum(axis=0)
    delta = c[:, j1] - c[:, j0]
    return {"r": lam[:, j1] / np.where(lam[:, j0] > 0, lam[:, j0], np.nan), "r_total": tot[j1] / tot[j0],
            "part_ini": c[:, j0] / tot[j0], "part_delta": delta / delta.sum() if delta.sum() != 0 else delta * np.nan}


def queda(n_boot: int = 200, log=print) -> dict:
    ids, E, names = setor_exposicao()
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(
        pl.col("periodo").str.slice(0, 4).cast(pl.Int32).alias("ano"), pl.col("cd_setor").cast(pl.String))
    t = t.filter(pl.col("ano").is_in(list(YEARS))).group_by("cd_setor", "ano").agg(pl.col("n_total").sum())
    w = t.pivot(on="ano", index="cd_setor", values="n_total").fill_null(0.0)
    cols = [str(a) for a in YEARS]
    Y = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select(cols).to_numpy().astype(float)
    lam = em_fit_multi(E, Y)
    dec = _decompoe(lam, E)
    dist = ids["cd_dist"].to_numpy()
    rel = np.empty((n_boot, len(names)))
    for b, idx in enumerate(_boot_picks(dist, n_boot, seed=1)):
        db = _decompoe(em_fit_multi(E[idx], Y[idx]), E[idx])
        rel[b] = db["r"] / db["r_total"]
    lo, hi = np.nanpercentile(rel, [2.5, 97.5], axis=0)
    rows = [{"classe": nm, **{f"lambda_{a}": float(lam[k, j]) for j, a in enumerate(YEARS)}, "razao": float(dec["r"][k]),
             "razao_rel": float(dec["r"][k] / dec["r_total"]), "ic_lo": float(lo[k]), "ic_hi": float(hi[k]),
             "part_2022": float(dec["part_ini"][k]), "part_queda": float(dec["part_delta"][k])} for k, nm in enumerate(names)]
    tab = pl.DataFrame(rows).sort("part_queda", descending=True)
    tab.write_parquet(out_dir() / "queda_celular.parquet")
    grandes = tab.filter(pl.col("part_2022") >= 0.05)
    heterog = grandes.filter((pl.col("ic_lo") > 1) | (pl.col("ic_hi") < 1))["classe"].to_list()
    top3 = tab.head(3)
    conc = float((top3["part_queda"] - top3["part_2022"]).sum())

    # todos os fenótipos, 2022 contra 2025 (pontual)
    fen_tab = pl.read_parquet(out_dir() / "fenotipo_setor_ano.parquet")
    fen = {}
    for f in fen_tab["fenotipo"].unique().sort().to_list():
        Yf = np.column_stack([matriz(ids, fen_tab.filter(pl.col("fenotipo") == f), [a])[0][:, 0] for a in (2022, 2025)])
        if Yf.sum() < 500:
            continue
        df = _decompoe(em_fit_multi(E, Yf), E)
        ordem = np.argsort(-np.nan_to_num(df["part_delta"]))[:3]
        fen[f] = {"total_2022": float(Yf[:, 0].sum()), "total_2025": float(Yf[:, 1].sum()), "r_total": float(df["r_total"]),
                  "classes_que_mais_mudaram": [(names[k], float(df["part_delta"][k]), float(df["part_ini"][k])) for k in ordem]}
    rep = {"celular": {"totais": dict(zip(cols, Y.sum(axis=0).tolist())), "r_total": float(dec["r_total"]),
                       "classes_heterogeneas": heterog, "concentracao_top3": conc},
           "gate_G4": bool(heterog) or conc > 0.10, "fenotipos": fen, "n_boot": n_boot}
    (out_dir() / "queda.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    log(f"queda do celular 2022→2025: razão total {dec['r_total']:.2f}; classes fora do ritmo da cidade: {heterog}; "
        f"concentração top-3 = {conc:+.2f}")
    return rep


def run(log=print) -> dict:
    if not (interim_dir() / EVENTOS).exists():
        build_eventos(log=log)
    if not (out_dir() / "fenotipo_setor_ano.parquet").exists():
        alvos(log=log)
    return {"assinaturas": assinaturas(log=log), "programas": programas(log=log), "relogio": relogio(log=log),
            "queda": queda(log=log)}
