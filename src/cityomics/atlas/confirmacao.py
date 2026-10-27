"""Confirmação das afirmações do atlas no cofre espacial (A11; D40, D53; narrativa B, docs/NARRATIVA.md).

Cada afirmação compara um "desenvolvimento" com um "teste" por conjuntos de distritos:

- **confirmação** (``confirmar``): desenvolvimento = 77 distritos de exploração; teste = 19 distritos
  do cofre. Roda **uma vez**, só depois que a emenda A11 estiver datada em ``prereg/AMENDMENTS.md`` e
  antes do FREEZE-B; grava ``prereg/atlas_confirmacao.json`` e recusa rodar de novo.
- **ensaio** (``ensaiar``): as mesmas funções numa divisão aleatória dos distritos de exploração em
  duas metades (pseudo-cofre, D53). Não lê o cofre; serve para conferir o código e o poder.

Afirmações (família do atlas, Holm próprio, α = 0,05; p unilateral):

| ID | Afirmação | Estatística | Critério de efeito |
|---|---|---|---|
| A-R1 | O ranking das taxas atribuídas por classe (celular 2025) se repete | Spearman dev × teste | ρ ≥ 0,7 |
| A-R2 | Validação pontual no teste | Spearman(λ do teste, taxa observada por ponto) | ρ > 0 |
| A-R5 | O tecido explica a taxa do setor além dos genes sem tipagem (H3, D55) | ΔR² no teste (modelos ajustados no dev) | ΔR² > 0 |
| A-R6 | As assinaturas classe × fenótipo se repetem | mediana do Spearman das participações | ≥ 0,7 |
| A-R7 | O relógio do furto de celular difere entre classes | contraste H contra permutação no distrito | p < α |
| A-R8 | Na queda 2022→2025, os polos (estações, terminais, comércio e serviços) perdem menos que as ruas locais | log(razão) do crime atribuído aos polos − log(razão) das ruas locais | > 0 |

A-R3 e A-R4 (comunicação) ficam exploratórias na narrativa B (comunicação no Extended Data). A família
padrão é ``FAMILIA_B``; o autor pode trocá-la na A11. Uma afirmação é sustentada se o p ajustado por
Holm < 0,05 **e** o critério de efeito é cumprido.
"""

from __future__ import annotations

import json
import re
from datetime import date

import numpy as np
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.attribution import crime_setor, em_fit, em_fit_multi, point_validation
from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
from cityomics.atlas.spots import exposure_matrix
from cityomics.paths import REPO_ROOT, processed_dir

FAMILIA_B = ("A-R1", "A-R2", "A-R6", "A-R7", "A-R8")
TODAS = ("A-R1", "A-R2", "A-R5", "A-R6", "A-R7", "A-R8")
ALPHA = 0.05
RESULTADO = REPO_ROOT / "prereg" / "atlas_confirmacao.json"
CRITERIO = {"A-R1": 0.7, "A-R2": 0.0, "A-R5": 0.0, "A-R6": 0.7, "A-R7": None, "A-R8": 0.0}
MIN_EVENTOS_FENOTIPO = 200


class ConfirmacaoBloqueada(PermissionError):
    """A confirmação no cofre só roda com a A11 datada, e uma vez."""


# --- dados por conjunto de distritos ------------------------------------------------------------

def _setores():
    s = pl.read_parquet(atlas_dir() / f"setor_composicao_{REF_YEAR}.parquet")
    E, names = exposure_matrix(s)
    E = E / 1000.0
    est = [i for i, n in enumerate(names) if n.startswith("n_")]
    E[:, est] *= 1000.0
    return s.select("cd_setor", "cd_dist"), E, names


def _mask(ids: pl.DataFrame, distritos: set[str]) -> np.ndarray:
    return np.isin(ids["cd_dist"].to_numpy().astype(str), list(distritos))


def _vetor(ids: pl.DataFrame, t: pl.DataFrame, col: str) -> np.ndarray:
    return ids.select("cd_setor").join(t.select("cd_setor", col), on="cd_setor", how="left").fill_null(0.0)[col].to_numpy().astype(float)


def _perm_spearman(a: np.ndarray, b: np.ndarray, rng, n: int = 9999) -> tuple[float, float]:
    from scipy.stats import rankdata

    ra, rb = rankdata(a), rankdata(b)
    rho = float(np.corrcoef(ra, rb)[0, 1])
    null = np.array([np.corrcoef(ra, rng.permutation(rb))[0, 1] for _ in range(n)])
    return rho, float((1 + np.sum(null >= rho)) / (1 + n))


# --- afirmações ---------------------------------------------------------------------------------

def a_r1(ids, E, names, dev, teste, rng) -> dict:
    y = _vetor(ids, crime_setor(), "y")
    md, mt = _mask(ids, dev), _mask(ids, teste)
    ld, lt = em_fit(E[md], y[md])["lam"], em_fit(E[mt], y[mt])["lam"]
    ok = (E[md].sum(0) > 0) & (E[mt].sum(0) > 0) & (ld > 0)
    rho, p = _perm_spearman(ld[ok], lt[ok], rng)
    return {"estatistica": rho, "p": p, "classes": int(ok.sum())}


def a_r2(ids, E, names, dev, teste, rng, log=print) -> dict:
    y = _vetor(ids, crime_setor(), "y")
    mt = _mask(ids, teste)
    lt = pl.DataFrame({"classe": names, "lambda": em_fit(E[mt], y[mt])["lam"]})
    pv = point_validation(distritos=teste, log=log).join(lt, on="classe", how="inner").filter(
        (pl.col("exposicao") > 0) & (pl.col("lambda") > 0))
    rho, p = _perm_spearman(pv["lambda"].to_numpy(), pv["taxa_observada"].to_numpy(), rng)
    return {"estatistica": rho, "p": p, "classes": pv.height}


def a_r5(ids, E, names, dev, teste, rng, n_boot: int = 2000) -> dict:
    import lightgbm as lgb

    from cityomics.atlas import variance

    s = variance.frame(mask="todos")
    X, y, dist = variance.conjuntos(s)
    dist = dist.astype(str)
    md, mt = np.isin(dist, list(dev)), np.isin(dist, list(teste))
    pred = {}
    for nome in ("tecido", "genes_sem_tipagem"):
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, num_leaves=31, min_child_samples=40, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.8, random_state=0, verbose=-1)
        pred[nome] = m.fit(X[nome][md], y[md]).predict(X[nome][mt])
    yt, dt = y[mt], dist[mt]

    def r2(p, yy):
        return 1 - np.sum((yy - p) ** 2) / np.sum((yy - yy.mean()) ** 2)
    delta = float(r2(pred["tecido"], yt) - r2(pred["genes_sem_tipagem"], yt))
    ud, inv = np.unique(dt, return_inverse=True)
    rows = [np.where(inv == k)[0] for k in range(len(ud))]
    bs = []
    for _ in range(n_boot):
        i = np.concatenate([rows[k] for k in rng.integers(0, len(ud), len(ud))])
        bs.append(r2(pred["tecido"][i], yt[i]) - r2(pred["genes_sem_tipagem"][i], yt[i]))
    return {"estatistica": delta, "p": float((1 + np.sum(np.asarray(bs) <= 0)) / (1 + n_boot))}


def a_r6(ids, E, names, dev, teste, rng, n_perm: int = 9999) -> dict:
    from scipy.stats import rankdata

    from cityomics.atlas.fenotipo import ANOS_ASSINATURA, _participacao, matriz

    tab = pl.read_parquet(atlas_dir() / "fenotipo" / "fenotipo_setor_ano.parquet")
    Y, fen = matriz(ids, tab, ANOS_ASSINATURA)
    md, mt = _mask(ids, dev), _mask(ids, teste)
    usa = [j for j in range(len(fen)) if Y[mt, j].sum() >= MIN_EVENTOS_FENOTIPO]
    Sd = _participacao(em_fit_multi(E[md], Y[md][:, usa]), E[md])
    St = _participacao(em_fit_multi(E[mt], Y[mt][:, usa]), E[mt])
    ok = (E[md].sum(0) > 0) & (E[mt].sum(0) > 0)
    Rd = np.apply_along_axis(rankdata, 0, Sd[ok])
    Rt = np.apply_along_axis(rankdata, 0, St[ok])

    def med(R2):
        return float(np.median([np.corrcoef(Rd[:, j], R2[:, j])[0, 1] for j in range(Rd.shape[1])]))
    obs = med(Rt)
    null = np.array([med(Rt[rng.permutation(Rt.shape[0])]) for _ in range(n_perm)])
    return {"estatistica": obs, "p": float((1 + np.sum(null >= obs)) / (1 + n_perm)), "fenotipos": [fen[j] for j in usa],
            "por_fenotipo": {fen[j]: float(np.corrcoef(Rd[:, i], Rt[:, i])[0, 1]) for i, j in enumerate(usa)}}


def a_r7(ids, E, names, dev, teste, rng, n_perm: int = 999) -> dict:
    from cityomics.atlas.fenotipo import ANOS_ASSINATURA, PERIODOS, _contraste, _eventos_relogio

    mt = _mask(ids, teste)
    it = ids.filter(pl.Series(mt))
    Et = E[mt]
    ev = _eventos_relogio(it, "celular_furto", ANOS_ASSINATURA)
    ev = ev[ev["per"].notna()]
    i = ev["i"].to_numpy()
    p = ev["per"].map({q: j for j, q in enumerate(PERIODOS)}).to_numpy().astype(int)
    n = it.height
    g = np.unique(it["cd_dist"].to_numpy(), return_inverse=True)[1][i]

    def H(pp):
        Y = np.bincount(i * 4 + pp, minlength=n * 4).reshape(n, 4).astype(float)
        return _contraste(em_fit_multi(Et, Y, tol=1e-6), Et)[0]
    obs = H(p)
    o0 = np.argsort(g, kind="stable")
    null = []
    for _ in range(n_perm):
        pp = np.empty_like(p)
        pp[o0] = p[np.lexsort((rng.random(len(g)), g))]
        null.append(H(pp))
    return {"estatistica": float(obs), "p": float((1 + np.sum(np.asarray(null) >= obs)) / (1 + n_perm)), "eventos": int(len(ev))}


def a_r8(ids, E, names, dev, teste, rng, n_boot: int = 2000) -> dict:
    from cityomics.atlas.memoria import contagens

    mt = _mask(ids, teste)
    Y = contagens(ids)[mt][:, [0, -1]]
    Et = E[mt]
    # polos (estações e classes de comércio, pela família da tipagem) contra as ruas locais: log da razão
    # 2025/2022 do crime atribuído a cada conjunto (refeito em 2026-10-20 para não depender de nomes de tipos)
    from cityomics.atlas import grupos as GR

    kh, kl = GR.indices(names, "polos"), [names.index("rua_local_m")]

    def d(Ei, Yi):
        lam = em_fit_multi(Ei, Yi)
        c = lam * Ei.sum(axis=0)[:, None]
        r = lambda k: np.log(max(c[k, 1].sum(), 1e-12) / max(c[k, 0].sum(), 1e-12))  # noqa: E731
        return float(r(kh) - r(kl))
    obs = d(Et, Y)
    dist = ids.filter(pl.Series(mt))["cd_dist"].to_numpy()
    ud, inv = np.unique(dist, return_inverse=True)
    rows = [np.where(inv == j)[0] for j in range(len(ud))]
    bs = []
    for _ in range(n_boot):
        i = np.concatenate([rows[j] for j in rng.integers(0, len(ud), len(ud))])
        bs.append(d(Et[i], Y[i]))
    return {"estatistica": obs, "p": float((1 + np.sum(np.asarray(bs) <= 0)) / (1 + n_boot))}


FUNCOES = {"A-R1": a_r1, "A-R2": a_r2, "A-R5": a_r5, "A-R6": a_r6, "A-R7": a_r7, "A-R8": a_r8}


def holm(p: dict[str, float]) -> dict[str, float]:
    ordem = sorted(p, key=p.get)
    m, out, acc = len(ordem), {}, 0.0
    for i, k in enumerate(ordem):
        acc = max(acc, min(1.0, (m - i) * p[k]))
        out[k] = acc
    return out


def avaliar(dev: set[str], teste: set[str], familia=FAMILIA_B, seed: int = 20261019, log=print) -> dict:
    ids, E, names = _setores()
    rng = np.random.default_rng(seed)
    res = {}
    for a in familia:
        fn = FUNCOES[a]
        res[a] = fn(ids, E, names, dev, teste, rng, log=log) if a == "A-R2" else fn(ids, E, names, dev, teste, rng)
        log(f"{a}: estatística {res[a]['estatistica']:.3f}, p = {res[a]['p']:.4f}")
    adj = holm({a: r["p"] for a, r in res.items()})
    for a, r in res.items():
        c = CRITERIO[a]
        if c is None:
            efeito = True
        elif a in ("A-R2", "A-R5", "A-R8"):   # critérios estritos (> 0)
            efeito = r["estatistica"] > c
        else:                                 # critérios de limiar (≥ 0,7)
            efeito = r["estatistica"] >= c
        r["p_holm"] = adj[a]
        r["criterio"] = c
        r["sustentada"] = bool(adj[a] < ALPHA and efeito)
    return res


# --- ensaio e confirmação -------------------------------------------------------------------------

def ensaiar(seed: int = 1, familia=TODAS, log=print) -> dict:
    """Pseudo-confirmação: metades aleatórias dos distritos de exploração. Não lê o cofre."""
    ids, _, _ = _setores()
    expl = sorted(set(ids["cd_dist"].to_numpy().astype(str)) - guard.vault())
    rng = np.random.default_rng(seed)
    teste = set(rng.choice(expl, size=len(guard.vault()), replace=False).tolist())
    dev = set(expl) - teste
    assert not (teste | dev) & guard.vault()
    res = avaliar(dev, teste, familia=familia, log=log)
    out = {"modo": "ensaio (pseudo-cofre na exploração)", "seed": seed, "n_dev": len(dev), "n_teste": len(teste), "resultados": res}
    (atlas_dir() / "confirmacao_ensaio.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return out


def a11_datada() -> bool:
    """A A11 está em AMENDMENTS.md numa linha de tabela com data (não no rascunho)."""
    am = REPO_ROOT / "prereg" / "AMENDMENTS.md"
    if not am.exists():
        return False
    return any(re.match(r"^\|\s*20\d\d-\d\d-\d\d\s*\|.*\bA11\b", ln) for ln in am.read_text().splitlines())


def confirmar(familia=FAMILIA_B, log=print) -> dict:
    """A confirmação no cofre: uma vez, depois da A11 datada."""
    if not a11_datada():
        raise ConfirmacaoBloqueada("a emenda A11 ainda não está datada em prereg/AMENDMENTS.md")
    if RESULTADO.exists():
        raise ConfirmacaoBloqueada(f"a confirmação já rodou: {RESULTADO.name}")
    ids, _, _ = _setores()
    cofre = guard.vault()
    dev = set(ids["cd_dist"].to_numpy().astype(str)) - cofre
    res = avaliar(dev, cofre, familia=familia, log=log)
    out = {"modo": "confirmação no cofre", "data": date.today().isoformat(), "familia": list(familia),
           "n_dev": len(dev), "n_teste": len(cofre), "resultados": res}
    RESULTADO.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    return out
