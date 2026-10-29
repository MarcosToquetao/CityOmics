"""Contexto espacial dos gêmeos de tecido, passo 5: um modelo único com todos os contextos (exploratório).

Um só LightGBM recebe o tecido próprio e **todos** os blocos de contexto ao mesmo tempo, em dimensão
completa (não os PCA de 8 dimensões do passo 4):

- ``anel_rainha``: composição do 1º e do 2º anel de vizinhos rainha;
- ``circulos``: composição dos círculos de 250 m, 500 m, 1 km e 2 km;
- ``posicao``: distâncias a estações, corredores, favelas, cortiços, parques, praças, feiras e ao centro;
- ``rede``: métricas da rede viária e composição alcançável por ela (800 m);
- ``od``: os oito indicadores de fluxo da OD 2023;
- ``bordas``: contraste com o entorno, entropia, fronteira de domínio, favela vizinha, renda e IPVS relativos;
- ``socio`` (variante à parte): covariáveis do censo 2022 e IPVS do setor e do 1º anel (sem raça/cor).

Nenhum atributo usa crime (D53). Validação cruzada por distrito (5 dobras), sempre fora da amostra.

- **Seleção aninhada:** em cada dobra externa, as variáveis são ordenadas por ganho no treino; o número de
  variáveis (10 a 160) é escolhido por validação cruzada interna por distrito; a dobra de teste só avalia.
- **Ablação:** retirar um bloco do modelo completo (contribuição única) e parte de |SHAP| por bloco.
- **O que sobra:** correlação dos resíduos do modelo entre gêmeos a menos de 1 km e Moran do resíduo.
- **Teto:** confiabilidade do resíduo (meses pares × ímpares, Spearman-Brown) para "quanto" e "a que hora":
  o R² máximo possível se o modelo capturasse toda a parte reprodutível.

Saídas em ``data/processed/atlas/contexto/teto_<alvo>.json`` e em ``extra.json`` (chave ``teto``).
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import contexto as C
from cityomics.atlas import contexto_extra as X
from cityomics.atlas import contexto_vizinhanca as V
from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import EVENTOS, YEARS, periodo_do_dia, setor_exposicao, PERIODOS
from cityomics.atlas.memoria import MIN_ESPERADO, contagens
from cityomics.paths import interim_dir, processed_dir

KS = (10, 20, 40, 80, 160)
ALVOS = ("quanto", "quanto_dist", "fen_div", "hora_noturna", "tend_mensal")
SOCIO = ("renda_mediana_resp", "cv_renda_resp", "taxa_analfabetismo_15", "frac_0_14", "frac_60_mais", "frac_15_24",
         "frac_homens_15_29", "moradores_por_dom", "frac_apartamento", "frac_cortico", "frac_estrutura_degradada",
         "frac_faces_iluminacao", "frac_faces_pavimentadas", "frac_faces_calcada", "dens_pop_km2")
GRUPOS_CONTEXTO = ("anel_rainha", "circulos", "posicao", "rede", "od", "bordas")


def _modelo(nj: int = 3, seed: int = 0):
    import lightgbm as lgb

    return lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8,
                             subsample_freq=1, colsample_bytree=0.7, random_state=seed, verbose=-1, n_jobs=nj)


def blocos_completos(b: dict, log=print) -> dict[str, tuple[np.ndarray, list[str]]]:
    """Cada bloco em dimensão completa, na ordem das linhas de ``b['res']`` (setores de exploração)."""
    import scipy.sparse as sp

    idx, names = b["idx"], b["names"]
    viz = V.comp_aneis(b)
    B = {"proprio": (b["Xown"], [f"proprio|{n}" for n in names] + ["proprio|log_tamanho", "proprio|densidade"])}

    def comp(chaves):
        m = np.column_stack([np.sqrt(viz[k][idx]) for k in chaves])
        return m, [f"{k}|{n}" for k in chaves for n in names]

    B["anel_rainha"] = comp(("r1", "r2"))
    B["circulos"] = comp(("b250", "b500", "b1000", "b2000"))
    infra = pl.read_parquet(processed_dir() / "covariaveis" / "setor_infra.parquet")
    inf = b["res"].select("cd_setor").join(infra, on="cd_setor", how="left")
    pos = np.column_stack([np.log1p(inf[c].fill_null(inf[c].median()).to_numpy().astype(float)) for c in V.POSICAO]
                          + [np.log1p(np.hypot(*(b["xy"][idx] - b["se"]).T))])
    B["posicao"] = (pos, [f"posicao|{c}" for c in V.POSICAO] + ["posicao|dist_centro"])
    rs = pl.read_parquet(C.out_dir() / "rede_setor.parquet")
    R = sp.load_npz(C.out_dir() / "rede_alcance_800.npz")
    comp800 = np.sqrt(V.composicao_contexto(b, R))[idx]
    B["rede"] = (np.column_stack([np.log1p(rs[c].to_numpy())[idx] for c in rs.columns[1:]] + [comp800]),
                 [f"rede|{c}" for c in rs.columns[1:]] + [f"rede800|{n}" for n in names])
    od = pl.read_parquet(C.out_dir() / "od_setor.parquet")
    Fo = np.column_stack([od[c].to_numpy() for c in od.columns[1:]])[idx]
    B["od"] = (np.where(np.isfinite(Fo), Fo, np.nanmedian(Fo, 0)), [f"od|{c}" for c in od.columns[1:]])
    _, feats = V.bordas(b, {"viz": viz}, log=lambda *a, **k: None, alvos=())
    B["bordas"] = (np.column_stack([v[idx] for v in feats.values()]), [f"borda|{k}" for k in feats])
    # socioeconômico do setor e do 1º anel (sem raça/cor)
    cen = pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet").select("cd_setor", *SOCIO)
    ip = pl.read_parquet(processed_dir() / "covariaveis" / "setor_ipvs.parquet").select("cd_setor", "ipvs_codigo")
    S = b["setor"].select("cd_setor").join(cen, on="cd_setor", how="left").join(ip, on="cd_setor", how="left")
    cols = list(SOCIO) + ["ipvs_codigo"]
    M = np.column_stack([S[c].to_numpy().astype(float) for c in cols])
    A1 = b["A1"]
    ok = np.isfinite(M)
    ring = (A1 @ np.where(ok, M, 0.0)) / np.clip(A1 @ ok.astype(float), 1e-9, None)
    ring = np.where((A1 @ ok.astype(float)) > 0, ring, np.nan)
    B["socio"] = (np.column_stack([M[idx], ring[idx]]), [f"socio|{c}" for c in cols] + [f"socio_r1|{c}" for c in cols])
    log("  blocos: " + ", ".join(f"{k} {v[0].shape[1]}" for k, v in B.items()))
    return B


def _monta(B: dict, grupos: tuple[str, ...]) -> tuple[np.ndarray, list[str], dict[str, np.ndarray]]:
    mats, nomes, pos, ini = [], [], {}, 0
    for g in grupos:
        m, n = B[g]
        mats.append(m)
        nomes += n
        pos[g] = np.arange(ini, ini + m.shape[1])
        ini += m.shape[1]
    return np.column_stack(mats), nomes, pos


def selecao_aninhada(X: np.ndarray, y: np.ndarray, g: np.ndarray, own_cols: np.ndarray, nj: int = 3, log=print):
    from sklearn.model_selection import GroupKFold

    oof = {k: np.zeros(len(y)) for k in ("proprio", "completo", "selecionado")}
    escolhas, selecionadas = [], []
    for f, (tr, te) in enumerate(GroupKFold(5).split(X, y, g)):
        m0 = _modelo(nj).fit(X[tr][:, own_cols], y[tr])
        oof["proprio"][te] = m0.predict(X[te][:, own_cols])
        m = _modelo(nj).fit(X[tr], y[tr])
        oof["completo"][te] = m.predict(X[te])
        ordem = np.argsort(-m.booster_.feature_importance("gain"))
        pontos = {}
        for K in KS:
            cols = ordem[:K]
            pr = np.zeros(len(tr))
            for a, c in GroupKFold(3).split(X[tr], groups=g[tr]):
                mm = _modelo(nj).fit(X[tr][a][:, cols], y[tr][a])
                pr[c] = mm.predict(X[tr][c][:, cols])
            pontos[K] = V.r2(y[tr], pr)
        Kb = max(pontos, key=pontos.get)
        cols = ordem[:Kb]
        oof["selecionado"][te] = _modelo(nj).fit(X[tr][:, cols], y[tr]).predict(X[te][:, cols])
        escolhas.append({"K": int(Kb), "r2_interno": {int(k): float(v) for k, v in pontos.items()}})
        selecionadas.append(cols)
        log(f"    dobra {f}: K = {Kb}; R² interno " + ", ".join(f"{k}:{v:.3f}" for k, v in pontos.items()))
    return oof, escolhas, selecionadas


def ablacao(X: np.ndarray, y: np.ndarray, g: np.ndarray, pos: dict, base_r2: float, nj: int = 3) -> dict:
    from sklearn.model_selection import GroupKFold

    out = {}
    for grupo in pos:
        if grupo == "proprio":
            continue
        keep = np.setdiff1d(np.arange(X.shape[1]), pos[grupo])
        oof = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(X, y, g):
            oof[te] = _modelo(nj).fit(X[tr][:, keep], y[tr]).predict(X[te][:, keep])
        out[grupo] = {"r2_sem": V.r2(y, oof), "perda_unica": base_r2 - V.r2(y, oof)}
    return out


def parte_shap(X: np.ndarray, y: np.ndarray, pos: dict, nj: int = 3) -> dict:
    m = _modelo(nj).fit(X, y)
    S = np.abs(m.predict(X, pred_contrib=True)[:, :-1]).mean(axis=0)
    tot = S.sum()
    return {g: float(S[c].sum() / tot) for g, c in pos.items()}


def resto(b: dict, y_all: np.ndarray, p_el: np.ndarray, log=print) -> dict:
    """O que o modelo deixa: correlação entre gêmeos próximos e Moran do resíduo."""
    el = b["el"]
    r = np.zeros(len(el))
    r[el] = y_all[el] - p_el
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    out = {}
    for lo, hi in ((0, 1000), (1000, 3000), (3000, 1e9)):
        m = (d >= lo) & (d < hi)
        out[f"gemeos_{int(lo)}-{int(hi) if hi < 1e8 else 'inf'}m"] = C._corr_sim(r, i[m], j[m])
    sub = b["res"].filter(pl.col("elegivel"))
    w, keep = C._pesos(sub)
    z = r[el][keep]
    strata = (np.unique(sub["cd_dist"].to_numpy(), return_inverse=True)[1] * 10 + C._dec_densidade(sub))[keep]
    rng = np.random.default_rng(2)
    nulo = float(np.mean([C._moran_I(C._within_perm(z, strata, rng), w) for _ in range(49)]))
    out["moran_residuo"] = float(C._moran_I(z, w))
    out["moran_nulo_restrito"] = nulo
    return out


def run_alvo(alvo: str, variantes=("espacial", "com_socio"), nj: int = 3, log=print) -> dict:
    b = X.base_ext(log=log)
    B = blocos_completos(b, log=log)
    el = b["el"]
    g = b["dist"][el]
    y_all = V._alvo(b, alvo)
    y = y_all[el]
    rep = {"alvo": alvo, "setores": int(el.sum()), "variantes": {}}
    for var in variantes:
        grupos = ("proprio",) + GRUPOS_CONTEXTO + (("socio",) if var == "com_socio" else ())
        Xm, nomes, pos = _monta(B, grupos)
        Xm = Xm[el]
        log(f"  [{alvo} | {var}] {Xm.shape[1]} variáveis, {len(y):,} setores")
        oof, escolhas, selecionadas = selecao_aninhada(Xm, y, g, pos["proprio"], nj=nj, log=log)
        r2s = {k: V.r2(y, v) for k, v in oof.items()}
        log(f"  [{alvo} | {var}] R²: próprio {r2s['proprio']:.3f}; completo {r2s['completo']:.3f}; selecionado {r2s['selecionado']:.3f}")
        freq = np.bincount(np.concatenate(selecionadas), minlength=Xm.shape[1])
        estaveis = [nomes[k] for k in np.argsort(-freq) if freq[k] >= 4][:40]
        por_bloco = {}
        for k in np.where(freq >= 4)[0]:
            bl = nomes[k].split("|")[0]
            bl = next(gr for gr, c in pos.items() if k in c)
            por_bloco[bl] = por_bloco.get(bl, 0) + 1
        v = {"r2": r2s, "dobras": escolhas, "variaveis_estaveis_4_de_5": estaveis, "n_estaveis_por_bloco": por_bloco}
        if alvo != "tend_mensal" or var == "espacial":
            abl = ablacao(Xm, y, g, pos, r2s["completo"], nj=nj)
            v["ablacao"] = abl
            v["parte_shap"] = parte_shap(Xm, y, pos, nj=nj)
            log(f"  [{alvo} | {var}] perda ao retirar o bloco: " + ", ".join(f"{k} {a['perda_unica']:+.3f}" for k, a in abl.items())
                + "; |SHAP| " + ", ".join(f"{k} {s:.0%}" for k, s in v["parte_shap"].items()))
        v["resto_completo"] = resto(b, y_all, oof["completo"], log=log)
        v["resto_proprio"] = resto(b, y_all, oof["proprio"], log=log)
        log(f"  [{alvo} | {var}] resto do modelo completo: gêmeos ≤1 km {v['resto_completo']['gemeos_0-1000m']:.2f} "
            f"(só tecido {v['resto_proprio']['gemeos_0-1000m']:.2f}); Moran {v['resto_completo']['moran_residuo']:.3f} "
            f"(só tecido {v['resto_proprio']['moran_residuo']:.3f}; nulo {v['resto_completo']['moran_nulo_restrito']:.3f})")
        rep["variantes"][var] = v
    (C.out_dir() / f"teto_{alvo}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=float))
    return rep


# --- teto: confiabilidade do resíduo -----------------------------------------------------------

def _horas_meia(ids: pl.DataFrame, paridade: int) -> np.ndarray:
    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "periodo", "cd_setor"])
    ev = ev[ev["desfecho"].isin(C.RELOGIO) & ev["data_fato"].dt.year.isin(list(YEARS)) & ev["cd_setor"].notna()].copy()
    ev = ev[(ev["data_fato"].dt.year * 12 + ev["data_fato"].dt.month) % 2 == paridade]
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    i = ev["cd_setor"].astype(str).map(pos)
    per = periodo_do_dia(ev).map({p: k for k, p in enumerate(PERIODOS)})
    ok = i.notna() & per.notna()
    idx = i[ok].astype(int).to_numpy() * len(PERIODOS) + per[ok].astype(int).to_numpy()
    return np.bincount(idx, minlength=ids.height * len(PERIODOS)).reshape(ids.height, len(PERIODOS)).astype(float)


def confiabilidade(log=print) -> dict:
    ids, E, _ = setor_exposicao()
    Ya = contagens(ids)
    M = E @ em_fit_multi(E, Ya)
    el = M.mean(axis=1) >= MIN_ESPERADO
    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(pl.col("cd_setor").cast(pl.String))
    t = t.filter((pl.col("periodo") >= "2022-01") & (pl.col("periodo") < "2026-01"))
    meses = sorted(t["periodo"].unique().to_list())
    W = t.pivot(on="periodo", index="cd_setor", values="n_total").fill_null(0.0)
    Y = ids.select("cd_setor").join(W, on="cd_setor", how="left").fill_null(0.0).select(meses).to_numpy().astype(float)
    par = np.arange(48) % 2 == 0
    Mm = np.repeat(M / 12.0, 12, axis=1)
    ra, _ = C.razao_encolhida(Y[:, par].sum(1), Mm[:, par].sum(1))
    rb, _ = C.razao_encolhida(Y[:, ~par].sum(1), Mm[:, ~par].sum(1))
    r_q = float(np.corrcoef(ra[el], rb[el])[0, 1])
    out = {"quanto": {"r_metades": r_q, "confiabilidade": 2 * r_q / (1 + r_q)}}
    hs = []
    noct = [PERIODOS.index("madrugada"), PERIODOS.index("noite")]
    dia = [k for k in range(len(PERIODOS)) if k not in noct]
    for p in (0, 1):
        Yh = _horas_meia(ids, p)
        Mh = E @ em_fit_multi(E, Yh)
        R2 = C.mistura(np.column_stack([Yh[:, noct].sum(1), Yh[:, dia].sum(1)]), np.column_stack([Mh[:, noct].sum(1), Mh[:, dia].sum(1)]))
        hs.append(R2[:, 0] - R2[:, 1])
    r_h = float(np.corrcoef(hs[0][el], hs[1][el])[0, 1])
    out["hora_noturna"] = {"r_metades": r_h, "confiabilidade": 2 * r_h / (1 + r_h)}
    log(f"  confiabilidade (SB): quanto {out['quanto']['confiabilidade']:.2f} (r das metades {r_q:.2f}); "
        f"hora noturna {out['hora_noturna']['confiabilidade']:.2f} (r {r_h:.2f})")
    return out


def resumo(log=print) -> dict:
    rep = {a: json.loads((C.out_dir() / f"teto_{a}.json").read_text()) for a in ALVOS if (C.out_dir() / f"teto_{a}.json").exists()}
    rel = confiabilidade(log=log)
    for a, r in rel.items():
        if a in rep:
            for var, v in rep[a]["variantes"].items():
                v["fracao_do_teto"] = {k: v["r2"][k] / r["confiabilidade"] for k in ("proprio", "completo", "selecionado")}
    out = {"modelos": rep, "confiabilidade": rel}
    X._salva("teto", out)
    for a, r in rep.items():
        for var, v in r["variantes"].items():
            f = v.get("fracao_do_teto")
            log(f"  {a} | {var}: R² próprio {v['r2']['proprio']:.3f} → completo {v['r2']['completo']:.3f} → selecionado {v['r2']['selecionado']:.3f}"
                + (f"; teto {rel[a]['confiabilidade']:.2f}: tecido {f['proprio']:.0%}, completo {f['completo']:.0%} do reprodutível" if f else ""))
    figura(out)
    return out


def figura(d: dict | None = None, log=print) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cityomics.paths import REPO_ROOT

    d = d or json.loads((C.out_dir() / "extra.json").read_text())["teto"]
    M, rel = d["modelos"], d["confiabilidade"]
    nomes = {"quanto": "Quanto", "quanto_dist": "Quanto, sem distrito", "fen_div": "Que crime", "hora_noturna": "A que hora", "tend_mensal": "Tendência mensal"}
    pasta = REPO_ROOT / "figures" / "out" / "exploratorio" / "contexto"
    pasta.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(2, 2, figsize=(14, 9.5))
    a = ax[0, 0]
    alvos = [k for k in ALVOS if k in M]
    x = np.arange(len(alvos))
    est = [("proprio", "Só o tecido próprio", "#9ecae1"), ("completo", "+ todos os contextos espaciais", "#3182bd"),
           ("selecionado", "+ seleção aninhada", "#08519c")]
    for k, (ch, rot, cor) in enumerate(est):
        a.bar(x + (k - 1) * 0.25, [M[t]["variantes"]["espacial"]["r2"][ch] for t in alvos], width=0.25, label=rot, color=cor)
    a.bar(x[[i for i, t in enumerate(alvos) if "com_socio" in M[t]["variantes"]]] + 0.375,
          [M[t]["variantes"]["com_socio"]["r2"]["completo"] for t in alvos if "com_socio" in M[t]["variantes"]], width=0.12,
          label="+ socioeconômico", color="#e6550d")
    for i, t in enumerate(alvos):
        if t in rel:
            a.hlines(rel[t]["confiabilidade"], i - 0.45, i + 0.45, colors="k", ls="--", lw=1, label="Teto (confiabilidade)" if i == 0 else None)
    a.axhline(0, c="k", lw=0.5)
    a.set_xticks(x, [nomes[t] for t in alvos], fontsize=9)
    a.set_ylabel("R² fora da amostra (CV por distrito)")
    a.set_title("a  O que o modelo único explica e o teto", loc="left")
    a.legend(fontsize=8, frameon=False)
    a = ax[0, 1]
    grupos = list(GRUPOS_CONTEXTO)
    for k, t in enumerate(("quanto", "fen_div", "hora_noturna")):
        if t in M:
            ab = M[t]["variantes"]["espacial"]["ablacao"]
            a.barh(np.arange(len(grupos)) + (k - 1) * 0.26, [ab[g_]["perda_unica"] for g_ in grupos], height=0.26, label=nomes[t])
    a.set_yticks(np.arange(len(grupos)), [g_.replace("_", " ") for g_ in grupos])
    a.axvline(0, c="k", lw=0.5)
    a.set_xlabel("Perda de R² ao retirar o bloco do modelo completo")
    a.set_title("b  Contribuição única de cada contexto", loc="left")
    a.legend(fontsize=8, frameon=False)
    a = ax[1, 0]
    nb = {}
    for t in ("quanto", "fen_div", "hora_noturna"):
        if t in M:
            nb[t] = M[t]["variantes"]["espacial"]["parte_shap"]
    gs = ["proprio"] + grupos
    for k, t in enumerate(nb):
        a.barh(np.arange(len(gs)) + (k - 1) * 0.26, [nb[t][g_] for g_ in gs], height=0.26, label=nomes[t])
    a.set_yticks(np.arange(len(gs)), [g_.replace("_", " ") for g_ in gs])
    a.set_xlabel("Parte do |SHAP| médio")
    a.set_title("c  Quem o modelo usa", loc="left")
    a.legend(fontsize=8, frameon=False)
    a = ax[1, 1]
    itens = [t for t in ("quanto", "quanto_dist", "fen_div", "hora_noturna") if t in M]
    x = np.arange(len(itens))
    for k, (ch, rot, cor) in enumerate((("resto_proprio", "Depois do tecido próprio", "#9ecae1"), ("resto_completo", "Depois do modelo único", "#08519c"))):
        a.bar(x + (k - 0.5) * 0.35, [M[t]["variantes"]["espacial"][ch]["gemeos_0-1000m"] for t in itens], width=0.35, label=rot, color=cor)
    a.set_xticks(x, [nomes[t] for t in itens], fontsize=9)
    a.set_ylabel("Correlação entre gêmeos a menos de 1 km")
    a.set_title("d  O que sobra: gêmeos próximos continuam parecidos?", loc="left")
    a.legend(fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(pasta / "contexto_passo4.png", dpi=200)
    plt.close(fig)
    log(f"figura: {pasta / 'contexto_passo4.png'}")
