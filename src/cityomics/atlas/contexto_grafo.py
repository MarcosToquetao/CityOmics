"""Contexto espacial dos gêmeos de tecido, passo 3: grafos funcionais e GNN (exploratório, fora do artigo).

- **D1. Rede viária:** o grafo OSM ``drive`` (``covariates.osm.load_graph``). De cada setor (nó mais
  próximo do ponto representativo), Dijkstra até 1.600 m: alcance (nós atingidos), permeabilidade
  (alcance pela rede / nós no círculo euclidiano de mesmo raio, < 1 = barreiras), intermediação local
  (igraph, corte de 400/800/1.600 m) e a composição dos setores alcançáveis pela rede, comparada com a
  do círculo euclidiano de mesmo raio.
- **D2. Fluxos OD 2023:** viagens de dia útil que chegam a um destino que não é a casa, suavizadas por
  núcleo gaussiano (σ = 500 m): volume, visitantes por morador, parte noturna, parte de homens de 15 a
  29 anos, renda dos visitantes contra a dos moradores, distância média e diversidade de origens. Sem
  crime nos atributos.
- **E. GNN:** GraphSAGE-média (torch) com entrada só da composição própria (sem crime), alvo = os
  resíduos do tecido; ablação de 0 a 3 saltos no grafo rainha e comparação com kNN-8 e rede viária de
  800 m (CV por distrito). Gradiente integrado nos gêmeos discordantes a menos de 1 km: que classes
  nos vizinhos empurram o gêmeo de mais crime.

Saídas locais em ``data/processed/atlas/contexto/`` (``grafo.json``, tabelas por setor, matrizes).
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl
import scipy.sparse as sp

from cityomics.atlas import contexto as C
from cityomics.atlas import contexto_vizinhanca as V
from cityomics.paths import processed_dir

RAIOS_REDE = (400, 800, 1600)
SIGMA_OD = 500.0
LOTE_DIJKSTRA = 256
ALVOS_GNN = ("quanto", "quanto_dist", "fen_div", "hora_noturna")


def _json(nome: str) -> dict:
    p = C.out_dir() / nome
    return json.loads(p.read_text()) if p.exists() else {}


def _salva_json(nome: str, chave: str, valor) -> None:
    d = _json(nome)
    d[chave] = valor
    (C.out_dir() / nome).write_text(json.dumps(d, ensure_ascii=False, indent=2, default=float))


def _teste_features(b: dict, F: np.ndarray, nomes: list[str], log=print, rotulo: str = "", alvos=ALVOS_GNN) -> dict:
    """Ganho de R² (CV por distrito) sobre o tecido próprio, efeito de cada feature com efeito fixo de
    distrito no resíduo sem tecido, e diferença entre gêmeos a menos de 1 km."""
    el, g = b["el"], b["dist"][b["el"]]
    Fz_all = (F - np.nanmean(F[el], 0)) / np.nanstd(F[el], 0)
    i, j, d = b["pares"]["i"].to_numpy(), b["pares"]["j"].to_numpy(), b["pares"]["dist_m"].to_numpy()
    perto = d < 1000
    out = {}
    for col in alvos:
        y = V._alvo(b, col)
        p0, p1 = np.zeros(len(y)), np.zeros(len(y))
        p0[el] = V.lgb_cv(b["Xown"][el], y[el], g)
        p1[el] = V.lgb_cv(np.column_stack([b["Xown"], F])[el], y[el], g)
        ys = V._alvo(b, col, sem_tecido=True)
        ok = el & np.isfinite(Fz_all).all(axis=1)
        yz = ys[ok] / ys[ok].std()
        um = {}
        for k, n in enumerate(nomes):
            be, ci = V.coef_fe(yz, Fz_all[ok][:, [k]], b["dist"][ok], n_boot=100)
            fi, fj = F[i, k], F[j, k]
            m = perto & np.isfinite(fi) & np.isfinite(fj)
            um[n] = {"beta_dp": float(be[0]), "ic": [float(ci[0, 0]), float(ci[1, 0])],
                     "gemeos_ate_1km_r": float(np.corrcoef(ys[i[m]] - ys[j[m]], fi[m] - fj[m])[0, 1])}
        out[col] = {"r2_proprio": V.r2(y[el], p0[el]), "r2_com": V.r2(y[el], p1[el]), "features": um,
                    "gemeos_ate_1km_antes": C._corr_sim(y - p0, i[perto], j[perto]),
                    "gemeos_ate_1km_depois": C._corr_sim(y - p1, i[perto], j[perto])}
        log(f"  {rotulo} {col}: R² {out[col]['r2_proprio']:.3f} → {out[col]['r2_com']:.3f}; gêmeos ≤1 km "
            f"{out[col]['gemeos_ate_1km_antes']:.2f} → {out[col]['gemeos_ate_1km_depois']:.2f}")
    return out


# --- D1. rede viária ----------------------------------------------------------------------------

def rede(b: dict | None = None, log=print) -> dict:
    import geopandas as gpd
    import igraph as ig
    from pyproj import Transformer
    from scipy.sparse.csgraph import dijkstra
    from scipy.spatial import cKDTree

    from cityomics.covariates.osm import load_graph

    b = b or V.base(log=log)
    G = load_graph(log=log)
    nos = list(G.nodes())
    k_no = {n: k for k, n in enumerate(nos)}
    setores = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["cd_setor", "geometry"])
    setores["cd_setor"] = setores["cd_setor"].astype(str)
    tr = Transformer.from_crs("EPSG:4326", setores.crs, always_xy=True)
    nx_, ny_ = tr.transform(np.array([float(G.nodes[n]["x"]) for n in nos]), np.array([float(G.nodes[n]["y"]) for n in nos]))
    nxy = np.column_stack([nx_, ny_])
    arestas = {}
    for u, v, dd in G.edges(data=True):
        a, c = sorted((k_no[u], k_no[v]))
        if a != c:
            arestas[(a, c)] = min(arestas.get((a, c), 1e18), float(dd.get("length", 1.0)))
    del G
    ab = np.array(list(arestas.keys()))
    ln = np.array(list(arestas.values()))
    N = len(nos)
    Gs = sp.csr_matrix((np.concatenate([ln, ln]), (np.concatenate([ab[:, 0], ab[:, 1]]), np.concatenate([ab[:, 1], ab[:, 0]]))), shape=(N, N))
    # nó → setor (de todos os setores de contexto) e nó-fonte de cada setor
    cs = b["cs"]
    pos = {s: k for k, s in enumerate(cs)}
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(nx_, ny_), crs=setores.crs)
    j = gpd.sjoin(pts, setores, predicate="within", how="left")
    j = j[~j.index.duplicated()]
    no_setor = np.array([pos.get(s, -1) if isinstance(s, str) else -1 for s in j["cd_setor"].to_numpy()])
    rp = setores.set_index("cd_setor").loc[list(cs)].geometry.representative_point()
    sxy = np.column_stack([rp.x.to_numpy(), rp.y.to_numpy()])
    arv = cKDTree(nxy)
    _, fonte = arv.query(sxy)
    n = len(cs)
    alcance = {r: np.zeros(n) for r in RAIOS_REDE}
    trip = {r: ([], [], []) for r in RAIOS_REDE}
    for s0 in range(0, n, LOTE_DIJKSTRA):
        s1 = min(n, s0 + LOTE_DIJKSTRA)
        D = dijkstra(Gs, directed=False, indices=fonte[s0:s1], limit=max(RAIOS_REDE))
        for r in RAIOS_REDE:
            rr, cc = np.nonzero(D <= r)
            alcance[r][s0:s1] = np.bincount(rr, minlength=s1 - s0)
            st = no_setor[cc]
            ok = st >= 0
            key = (rr[ok] + s0).astype(np.int64) * n + st[ok]
            u, cnt = np.unique(key, return_counts=True)
            trip[r][0].append(u // n)
            trip[r][1].append(u % n)
            trip[r][2].append(cnt)
        if (s0 // LOTE_DIJKSTRA) % 20 == 0:
            log(f"  rede: {s1:,}/{n:,} setores")
    Nr = {}
    for r in RAIOS_REDE:
        a = np.concatenate(trip[r][0])
        c = np.concatenate(trip[r][1])
        v = np.concatenate(trip[r][2]).astype(float)
        M = sp.csr_matrix((v, (a, c)), shape=(n, n))
        M.setdiag(0)
        M.eliminate_zeros()
        Nr[r] = M
        sp.save_npz(C.out_dir() / f"rede_alcance_{r}.npz", M)
    perm = {r: alcance[r] / np.maximum(arv.query_ball_point(nxy[fonte], r, return_length=True), 1) for r in RAIOS_REDE}
    g = ig.Graph(n=N, edges=ab.tolist())
    g.es["w"] = ln.tolist()
    bt = {}
    for r in RAIOS_REDE:
        v = np.asarray(g.betweenness(cutoff=r, weights="w", directed=False))
        ok = no_setor >= 0
        soma = np.bincount(no_setor[ok], weights=v[ok], minlength=n)
        cnt = np.bincount(no_setor[ok], minlength=n)
        bt[r] = np.where(cnt > 0, soma / np.maximum(cnt, 1), v[fonte])
        log(f"  intermediação local {r} m pronta")
    tab = pl.DataFrame({"cd_setor": cs} | {f"alcance_{r}": alcance[r] for r in RAIOS_REDE}
                       | {f"permeabilidade_{r}": perm[r] for r in RAIOS_REDE} | {f"intermediacao_{r}": bt[r] for r in RAIOS_REDE})
    tab.write_parquet(C.out_dir() / "rede_setor.parquet")
    idx = b["idx"]
    # 1) métricas de rede
    nomes = list(tab.columns[1:])
    F = np.column_stack([np.log1p(tab[c].to_numpy()) for c in nomes])[idx]
    out = {"metricas": _teste_features(b, F, nomes, log=log, rotulo="rede métricas")}
    # 2) composição alcançável pela rede contra o círculo euclidiano de mesmo raio
    from scipy.spatial import cKDTree as KD

    t2 = KD(b["xy"])
    Dd = t2.sparse_distance_matrix(t2, max(RAIOS_REDE), output_type="coo_matrix")
    off = Dd.row != Dd.col
    el, gg = b["el"], b["dist"][b["el"]]
    comp = {}
    for col in ALVOS_GNN:
        y = V._alvo(b, col)
        o = {}
        for r in RAIOS_REDE:
            m = off & (Dd.data <= r)
            Be = sp.csr_matrix((np.ones(int(m.sum())), (Dd.row[m], Dd.col[m])), shape=(n, n))
            for nome, M in (("euclidiano", Be), ("rede", Nr[r])):
                X = np.column_stack([b["Xown"], np.sqrt(V.composicao_contexto(b, M)[idx])])
                p = np.zeros(len(y))
                p[el] = V.lgb_cv(X[el], y[el], gg)
                o[f"{nome}_{r}"] = V.r2(y[el], p[el])
        comp[col] = o
        log(f"  rede × euclidiano {col}: " + ", ".join(f"{k} {v:.3f}" for k, v in o.items()))
    out["composicao_rede_vs_euclidiano"] = comp
    _salva_json("grafo.json", "rede", out)
    return out


# --- D2. fluxos OD 2023 -------------------------------------------------------------------------

def od(b: dict | None = None, log=print) -> dict:
    import geopandas as gpd
    from pyproj import Transformer
    from scipy.spatial import cKDTree

    from cityomics.atlas import presenca as P
    from cityomics.atlas.presenca_od2023 import read_od2023

    b = b or V.base(log=log)
    cols = ["N_VIAG", "FE_VIA", "MUNI_D", "CO_D_X", "CO_D_Y", "ZONA_O", "MOTIVO_D", "H_CHEG", "IDADE", "SEXO", "RENDA_FA",
            "DISTANCIA", "DIA_SEM"]
    od_ = read_od2023(cols=cols)
    t = od_[od_["N_VIAG"].notna() & (od_["FE_VIA"] > 0) & (od_["MUNI_D"] == P.MUNI_SP) & od_["CO_D_X"].notna()
            & (od_["MOTIVO_D"] != 8)].copy()
    crs = gpd.read_parquet(processed_dir() / "units" / "setores_2022.parquet", columns=["geometry"]).crs
    x, y = Transformer.from_crs(P.OD_CRS, crs, always_xy=True).transform(t["CO_D_X"].to_numpy(float), t["CO_D_Y"].to_numpy(float))
    w = t["FE_VIA"].to_numpy(float)
    noct = t["H_CHEG"].isin(list(range(18, 24)) + list(range(0, 6))).to_numpy().astype(float)
    jov = ((t["IDADE"] >= 15) & (t["IDADE"] <= 29) & (t["SEXO"] == 1)).to_numpy().astype(float)
    lr = np.log(t["RENDA_FA"].clip(lower=0).to_numpy(float) + 100)
    ldist = np.log1p(t["DISTANCIA"].clip(lower=0).to_numpy(float))
    zona = t["ZONA_O"].to_numpy()
    log(f"  OD 2023: {len(t):,} viagens a destino que não é a casa ({w.sum() / 1e6:.1f} milhões/dia expandidas)")
    sxy = b["xy"]
    n = len(sxy)
    K = cKDTree(np.column_stack([x, y])).sparse_distance_matrix(cKDTree(sxy), 3 * SIGMA_OD, output_type="coo_matrix")
    kw = np.exp(-K.data ** 2 / (2 * SIGMA_OD ** 2)) * w[K.row]
    soma = np.bincount(K.col, weights=kw, minlength=n)

    def media(v):
        return np.bincount(K.col, weights=kw * v[K.row], minlength=n) / np.maximum(soma, 1e-9)

    zu, zi = np.unique(zona, return_inverse=True)
    Z = sp.csr_matrix((kw, (K.col, zi[K.row])), shape=(n, len(zu)))
    pz = V.norm_linhas(Z.toarray())
    entropia = -np.sum(np.where(pz > 0, pz * np.log(np.clip(pz, 1e-12, None)), 0), axis=1)
    # moradores suavizados com o mesmo núcleo, para visitantes por morador
    pop = b["setor"]["pop_2022"].fill_null(0).to_numpy().astype(float)
    Ks = cKDTree(sxy).sparse_distance_matrix(cKDTree(sxy), 3 * SIGMA_OD, output_type="coo_matrix")
    pk = np.bincount(Ks.col, weights=np.exp(-Ks.data ** 2 / (2 * SIGMA_OD ** 2)) * pop[Ks.row], minlength=n)
    censo = b["setor"].select("cd_setor").join(pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet")
                                               .select("cd_setor", "renda_mediana_resp"), on="cd_setor", how="left")
    lr_mor = np.log(censo["renda_mediana_resp"].to_numpy().astype(float) + 100)
    feats = {"visitantes": np.log1p(soma), "visitantes_por_morador": np.log1p(soma) - np.log1p(pk),
             "noturno": media(noct), "homens_15_29": media(jov), "renda_visitantes": media(lr),
             "renda_visitantes_menos_moradores": media(lr) - lr_mor, "distancia_media": media(ldist), "diversidade_origens": entropia}
    pl.DataFrame({"cd_setor": b["cs"]} | feats).write_parquet(C.out_dir() / "od_setor.parquet")
    F = np.column_stack(list(feats.values()))[b["idx"]]
    F[~np.isfinite(F)] = np.nan
    out = _teste_features(b, np.where(np.isnan(F), np.nanmedian(F, 0), F), list(feats), log=log, rotulo="OD")
    _salva_json("grafo.json", "od", out)
    return out


# --- E. GNN com ablação de saltos ---------------------------------------------------------------

def _adj_media(M: sp.spmatrix, device):
    import torch

    M = sp.csr_matrix(M, dtype=np.float32)
    M.data[:] = 1.0
    deg = np.asarray(M.sum(axis=1)).ravel()
    D = sp.diags(1.0 / np.maximum(deg, 1)).astype(np.float32)
    A = (D @ M).tocoo()
    return torch.sparse_coo_tensor(np.vstack([A.row, A.col]), A.data, A.shape, device=device).coalesce()


def _rede_gnn(d_in: int, h: int, saltos: int, d_out: int):
    import torch
    from torch import nn

    class Sage(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Sequential(nn.Linear(d_in, h), nn.ReLU())
            self.camadas = nn.ModuleList([nn.Linear(2 * h, h) for _ in range(saltos)])
            self.head = nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Dropout(0.1), nn.Linear(h, d_out))

        def forward(self, x, a):
            z = self.enc(x)
            for lin in self.camadas:
                z = torch.relu(lin(torch.cat([z, torch.sparse.mm(a, z)], 1)))
            return self.head(z)

    return Sage()


def _treina(X, Y, mask_tr, mask_va, a, saltos, seed, device, epocas=600, paciencia=50, h=64):
    import torch

    torch.manual_seed(seed)
    m = _rede_gnn(X.shape[1], h, saltos, Y.shape[1]).to(device)
    opt = torch.optim.Adam(m.parameters(), lr=3e-3, weight_decay=1e-4)
    melhor, estado, sem = np.inf, None, 0
    for ep in range(epocas):
        m.train()
        opt.zero_grad()
        p = m(X, a)
        loss = ((p[mask_tr] - Y[mask_tr]) ** 2).mean()
        loss.backward()
        opt.step()
        m.eval()
        with torch.no_grad():
            v = float(((m(X, a)[mask_va] - Y[mask_va]) ** 2).mean())
        if v < melhor - 1e-5:
            melhor, estado, sem = v, {k: t.detach().clone() for k, t in m.state_dict().items()}, 0
        else:
            sem += 1
            if sem >= paciencia:
                break
    m.load_state_dict(estado)
    m.eval()
    return m


def gnn(b: dict | None = None, seeds=(0, 1), log=print, alvos=ALVOS_GNN, configs=None, salva: bool = True) -> dict:
    import torch
    from scipy.spatial import cKDTree
    from sklearn.model_selection import GroupKFold

    from cityomics.atlas.communication import density_deciles

    b = b or V.base(log=log)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    n = len(b["cs"])
    dec = density_deciles(b["setor"].fill_null(0))
    Xa = np.column_stack([np.sqrt(b["P"]), np.log(b["E"].sum(axis=1) + 1e-9), dec]).astype(np.float32)
    Xa = (Xa - Xa.mean(0)) / np.maximum(Xa.std(0), 1e-6)
    idx, el = b["idx"], b["el"]
    lab = idx[el]
    Yl = np.column_stack([V._alvo(b, c)[el] for c in alvos])
    mu, sd = Yl.mean(0), Yl.std(0)
    Y = np.zeros((n, len(alvos)), np.float32)
    Y[lab] = (Yl - mu) / sd
    grafos = {"rainha": b["A1"]}
    _, nb = cKDTree(b["xy"]).query(b["xy"], k=9)
    rr = np.repeat(np.arange(n), 8)
    knn = sp.csr_matrix((np.ones(n * 8), (rr, nb[:, 1:].ravel())), shape=(n, n))
    grafos["knn8"] = ((knn + knn.T) > 0).astype(float)
    p800 = C.out_dir() / "rede_alcance_800.npz"
    if p800.exists():
        R = sp.load_npz(p800)
        grafos["rede800"] = ((R + R.T) > 0).astype(float)
    X = torch.tensor(Xa, device=dev)
    Yt = torch.tensor(Y, device=dev)
    dist_lab = b["dist"][el]
    configs = configs or ([("rainha", L) for L in (0, 1, 2, 3)] + [("knn8", 2)] + ([("rede800", 1), ("rede800", 2)] if "rede800" in grafos else []))
    adjs = {k: _adj_media(v, dev) for k, v in grafos.items()}
    out, oof_melhor = {}, None
    for gname, L in configs:
        r2s = []
        for seed in seeds:
            oof = np.zeros_like(Yl)
            for f, (tr, te) in enumerate(GroupKFold(5).split(lab, groups=dist_lab)):
                ud = np.unique(dist_lab[tr])
                rng = np.random.default_rng(seed * 10 + f)
                va_d = rng.choice(ud, max(1, len(ud) // 5), replace=False)
                va = tr[np.isin(dist_lab[tr], va_d)]
                tr2 = tr[~np.isin(dist_lab[tr], va_d)]
                mtr = torch.zeros(n, dtype=torch.bool, device=dev)
                mva = torch.zeros(n, dtype=torch.bool, device=dev)
                mtr[torch.tensor(lab[tr2], device=dev)] = True
                mva[torch.tensor(lab[va], device=dev)] = True
                m = _treina(X, Yt, mtr, mva, adjs[gname], L, seed, dev)
                with torch.no_grad():
                    oof[te] = m(X, adjs[gname]).cpu().numpy()[lab[te]] * sd + mu
            r2s.append([V.r2(Yl[:, k], oof[:, k]) for k in range(len(alvos))])
            if gname == "rainha" and L == 2 and seed == seeds[0]:
                oof_melhor = oof
        r2m, r2d = np.mean(r2s, axis=0), np.std(r2s, axis=0)
        out[f"{gname}_L{L}"] = {c: float(r2m[k]) for k, c in enumerate(alvos)}
        out[f"{gname}_L{L}_dp"] = {c: float(r2d[k]) for k, c in enumerate(alvos)}
        log(f"  GNN {gname} L={L}: " + ", ".join(f"{c} {r2m[k]:.3f}±{r2d[k]:.3f}" for k, c in enumerate(alvos)))
    rep = {"r2": out}
    if salva:
        rep["explicacao"] = _explica(b, X, Yt, adjs["rainha"], lab, dist_lab, dev, log=log)
    if oof_melhor is not None and salva:
        pl.DataFrame({"cd_setor": b["res"]["cd_setor"].to_numpy()[el]} | {f"gnn|{c}": oof_melhor[:, k] for k, c in enumerate(alvos)}
                     ).write_parquet(C.out_dir() / "gnn_oof.parquet")
    if salva:
        _salva_json("grafo.json", "gnn", rep)
    return rep


def _explica(b, X, Yt, a, lab, dist_lab, dev, n_pares: int = 200, passos: int = 16, log=print) -> dict:
    """Gradiente integrado de pred_i − pred_j (quanto) nos gêmeos discordantes a menos de 1 km."""
    import torch

    n = X.shape[0]
    ud = np.unique(dist_lab)
    va_d = np.random.default_rng(99).choice(ud, len(ud) // 5, replace=False)
    va = np.isin(dist_lab, va_d)
    mtr = torch.zeros(n, dtype=torch.bool, device=dev)
    mva = torch.zeros(n, dtype=torch.bool, device=dev)
    mtr[torch.tensor(lab[~va], device=dev)] = True
    mva[torch.tensor(lab[va], device=dev)] = True
    m = _treina(X, Yt, mtr, mva, a, 2, 0, dev)
    pares = b["pares"]
    ys = V._alvo(b, "quanto", sem_tecido=True)
    i, j, d = pares["i"].to_numpy(), pares["j"].to_numpy(), pares["dist_m"].to_numpy()
    dy = ys[i] - ys[j]
    perto = np.where(d < 1000)[0]
    disc = perto[np.argsort(-np.abs(dy[perto]))[:n_pares]]
    gi, gj = b["idx"][i[disc]], b["idx"][j[disc]]
    sinal = np.sign(dy[disc])
    names = b["names"] + ["log_tamanho", "densidade"]
    viz_attr = np.zeros(X.shape[1])
    prop_attr = np.zeros(X.shape[1])
    acerto = 0
    for t in range(len(disc)):
        tot = torch.zeros_like(X)
        for s in range(1, passos + 1):
            xs = (X * s / passos).detach().requires_grad_(True)
            p = m(xs, a)
            alvo = p[gi[t], 0] - p[gj[t], 0]
            g, = torch.autograd.grad(alvo, xs)
            tot += g
        A = (X * tot / passos).detach().cpu().numpy() * sinal[t]
        with torch.no_grad():
            pr = m(X, a)
            acerto += int(np.sign(float(pr[gi[t], 0] - pr[gj[t], 0])) == sinal[t])
        proprio = A[[gi[t], gj[t]]].sum(axis=0)
        A[[gi[t], gj[t]]] = 0
        viz_attr += A.sum(axis=0)
        prop_attr += proprio
    tot_abs = np.abs(viz_attr).sum() + np.abs(prop_attr).sum()
    ordem = np.argsort(-viz_attr)
    out = {"pares": int(len(disc)), "acerta_o_sentido": acerto / len(disc), "parte_vizinhos": float(np.abs(viz_attr).sum() / tot_abs),
           "vizinhos_empurram_para_o_gemeo_de_mais_crime": {names[k]: float(viz_attr[k] / tot_abs) for k in ordem[:8]},
           "vizinhos_empurram_para_o_de_menos_crime": {names[k]: float(viz_attr[k] / tot_abs) for k in ordem[::-1][:8]}}
    log(f"  explicação GNN: acerta o sentido em {out['acerta_o_sentido']:.0%} de {out['pares']} pares; vizinhos = "
        f"{out['parte_vizinhos']:.0%} da atribuição; topo: {list(out['vizinhos_empurram_para_o_gemeo_de_mais_crime'])[:4]}")
    return out


# --- figura do passo 2 -------------------------------------------------------------------------

def figura(log=print) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cityomics.paths import REPO_ROOT

    vz, gf = _json("vizinhanca.json"), _json("grafo.json")
    d = REPO_ROOT / "figures" / "out" / "exploratorio" / "contexto"
    d.mkdir(parents=True, exist_ok=True)
    nomes = {"quanto": "Quanto", "quanto_dist": "Quanto, sem distrito", "fen_div": "Que crime", "hora_noturna": "A que hora",
             "tendencia": "Tendência"}
    fig, ax = plt.subplots(2, 3, figsize=(17, 9.5))
    # a: curva de ganho por anel
    a = ax[0, 0]
    for k, col in enumerate(("quanto", "quanto_dist", "fen_div", "hora_noturna")):
        cv = vz["aneis"][col]["curva_r2"]
        ks = [k_ for k_ in cv if k_ != "proprio+posicao"]
        a.plot(range(len(ks)), [cv[k_] - cv["proprio"] for k_ in ks], marker="o", label=nomes[col], color=f"C{k}")
    a.set_xticks(range(len(ks)), [k_.replace("+", "+ ") for k_ in ks], rotation=35, fontsize=8)
    a.axhline(0, c="k", lw=0.5)
    a.set_ylabel("Ganho de R² sobre o tecido próprio")
    a.set_title("a  Anéis de contexto (cumulativo)", loc="left")
    a.legend(fontsize=8, frameon=False)
    # b: bordas (um a um, resíduo sem tecido)
    a = ax[0, 1]
    bb = vz["bordas"]
    fe = list(bb["quanto"]["um_a_um"])
    yv = np.arange(len(fe))
    for k, col in enumerate(("quanto", "hora_noturna", "fen_div")):
        v = bb[col]["um_a_um"]
        be = np.array([v[f]["beta_dp"] for f in fe])
        lo = np.array([v[f]["ic"][0] for f in fe])
        hi = np.array([v[f]["ic"][1] for f in fe])
        a.errorbar(be, yv + (k - 1) * 0.25, xerr=[be - lo, hi - be], fmt="o", ms=3, color=f"C{[0, 3, 2][k]}", label=nomes[col])
    a.set_yticks(yv, [f.replace("_", " ") for f in fe], fontsize=8)
    a.axvline(0, c="k", lw=0.5)
    a.set_xlabel("Efeito (DP do resíduo por DP da borda), dentro do distrito")
    a.set_title("b  Bordas e contraste", loc="left")
    a.legend(fontsize=8, frameon=False)
    # c: borda de delegacia
    a = ax[0, 2]
    bd = vz["borda_delegacia"]
    itens = ["quanto", "quanto_dist", "fen_div", "hora_noturna"] + sorted([k for k in bd if k.startswith("fen|")],
                                                                          key=lambda k: -bd[k]["delegacia"]["beta"])
    x = np.arange(len(itens))
    for k, tipo in enumerate(("delegacia", "distrito")):
        be = np.array([bd[i_][tipo]["beta"] for i_ in itens])
        lo = np.array([bd[i_][tipo]["ic"][0] for i_ in itens])
        hi = np.array([bd[i_][tipo]["ic"][1] for i_ in itens])
        a.errorbar(x + (k - 0.5) * 0.3, be, yerr=[be - lo, hi - be], fmt="o", ms=3, label=f"divisa de {tipo}")
    a.axhline(0, c="k", lw=0.5)
    a.axhline(1, c="grey", lw=0.5, ls="--")
    a.set_xticks(x, [nomes.get(i_, i_.replace("fen|", "")) for i_ in itens], rotation=60, fontsize=7, ha="right")
    a.set_ylabel("β (1 = salto inteiro na divisa)")
    a.set_title("c  Divisa de delegacia × divisa de distrito", loc="left")
    a.legend(fontsize=8, frameon=False)
    # d: GNN ablação
    a = ax[1, 0]
    if "gnn" in gf:
        r = gf["gnn"]["r2"]
        cfg = [c for c in r if not c.endswith("_dp")]
        for k, col in enumerate(ALVOS_GNN):
            a.plot(range(len(cfg)), [r[c][col] for c in cfg], marker="o", label=nomes[col], color=f"C{k}")
        a.set_xticks(range(len(cfg)), cfg, rotation=35, fontsize=8)
        a.set_ylabel("R² fora da amostra (CV por distrito)")
    a.set_title("d  GNN: saltos e grafos", loc="left")
    a.legend(fontsize=8, frameon=False)
    # e: rede × euclidiano
    a = ax[1, 1]
    if "rede" in gf:
        cp = gf["rede"]["composicao_rede_vs_euclidiano"]
        for k, col in enumerate(ALVOS_GNN):
            for tipo, ls in (("euclidiano", "--"), ("rede", "-")):
                a.plot(RAIOS_REDE, [cp[col][f"{tipo}_{r_}"] for r_ in RAIOS_REDE], ls=ls, marker="o", color=f"C{k}",
                       label=f"{nomes[col]} ({tipo})" if col in ("quanto", "hora_noturna") else None)
        a.set_xscale("log")
        a.set_xticks(RAIOS_REDE, [str(r_) for r_ in RAIOS_REDE])
        a.set_xlabel("Raio (m)")
        a.set_ylabel("R² (tecido próprio + composição do entorno)")
    a.set_title("e  Entorno pela rede viária × pelo círculo", loc="left")
    a.legend(fontsize=7, frameon=False)
    # f: contágio
    a = ax[1, 2]
    pn = vz["contagio"]["painel"]
    lab_, be, lo, hi = [], [], [], []
    for nome in ("nivel", "choque"):
        for fe_ in ("so_ano", "distrito_ano"):
            v = pn[nome][fe_]
            lab_.append(f"{nome}\n{fe_.replace('_', ' × ')}")
            be.append(v["vizinhos"])
            lo.append(v["ic_vizinhos"][0])
            hi.append(v["ic_vizinhos"][1])
    be, lo, hi = map(np.array, (be, lo, hi))
    a.errorbar(range(len(be)), be, yerr=[be - lo, hi - be], fmt="o", color="k")
    a.axhline(0, c="k", lw=0.5)
    a.set_xticks(range(len(be)), lab_, fontsize=8)
    a.set_ylabel("β dos vizinhos em t → setor em t+1")
    ct = vz["contagio"]
    txt = "\n".join(f"{nomes[c]}: SAR ρ {ct[c]['sar']['rho']:.2f}, SDM ρ {ct[c]['sdm']['rho']:.2f}, SEM λ {ct[c]['sem']['lambda']:.2f}"
                    for c in ("quanto", "quanto_dist", "hora_noturna"))
    a.text(0.02, 0.02, txt, transform=a.transAxes, fontsize=7, va="bottom")
    a.set_title("f  Contágio: painel anual e modelos espaciais", loc="left")
    fig.tight_layout()
    fig.savefig(d / "contexto_passo2.png", dpi=200)
    plt.close(fig)
    log(f"figura: {d / 'contexto_passo2.png'}")
