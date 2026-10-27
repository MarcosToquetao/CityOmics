"""Ritmo, queda e evento-estudo: análises do parecer crítico de 2026-10-20 (Agente C, paper/03_plano_parecer.md).

Exploratório, só distritos fora do cofre espacial (D53) e nada de 2026 (todo caminho passa por
``guard.pre2026``). Não altera os módulos de origem: as variantes de função ficam aqui.

1. **Denominador de pedestres (R5):** a OD 2017 codifica TIPVG = 1 coletivo, 2 individual, 3 a pé,
   4 bicicleta (``LAYOUT OD2017_v1.xlsx``). ``presenca`` conta as viagens 3 e 4 inteiras como rua.
   Aqui: parte das pessoas-hora na rua que vem da bicicleta; tudo de novo só a pé (nas viagens de
   bicicleta ficam só os minutos andando nas pontas, ANDA_O e ANDA_D); bootstrap da amostra da OD por
   domicílio dentro da zona (a zona é o estrato do desenho); sensibilidade a σ = 150 e 600 m.
2. **Relógio com nulo em blocos:** os eventos do mesmo setor, mesmo dia (ou mês) e mesmo período formam
   um bloco que leva o seu rótulo junto; os rótulos trocam entre blocos do mesmo tamanho no mesmo
   distrito. Preserva o total de eventos por setor e por período em cada distrito.
3. **Intervalos do relógio:** bootstrap por distrito da fração 04–06h do roubo no residencial horizontal
   popular (modelo e contagem) e da razão fim de semana/dia útil por classe.
4. **Concentração da queda (R11):** roubo de celular 2022 → 2025 por setor e por segmento de rua.
5. **Evento-estudo (R6):** tratados por variante e coorte, repetições, estimador e o que ele detecta.

``run(log=print)`` grava ``data/processed/atlas/fenotipo/ritmo_queda.json`` (só agregados).
"""

from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import grupos as GR
from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.fenotipo import (EVENTOS, PERIODOS, PESO_MIN, _contraste, _eventos_relogio, out_dir,
                                      setor_exposicao)
from cityomics.paths import interim_dir

POPULAR = "Residencial horizontal popular"
COMERCIO = ("Comércio de rua médio", "Comércio de rua popular", "Vertical residencial e misto", "Serviços e equipamentos")
RESIDENCIAL = (POPULAR, "Residencial horizontal médio", "Residencial de esquina", "Residencial horizontal alto padrão",
               "Favela (FCU)")
POLOS = ("Comércio de rua médio", "Comércio de rua popular", "Serviços e equipamentos", "n_trilho", "n_terminal")
TIPVG = {1: "coletivo", 2: "individual", 3: "a pé", 4: "bicicleta"}
MODOS = {"pe_bici": (3, 4), "pe": (3,)}
HORAS_PERIODO = {"madrugada": range(0, 6), "manha": range(6, 12), "tarde": range(12, 18), "noite": range(18, 24)}
ANOS = (2024, 2025)
TOL_BOOT = 1e-7
SAIDA = "ritmo_queda.json"


def _ic(x, q=(2.5, 97.5)) -> list[float]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return [float(v) for v in np.percentile(x, q)] if len(x) else [float("nan")] * 2


def _boot_distritos(dist: np.ndarray, n_boot: int, seed: int):
    """Índices de linhas de cada réplica, sorteando distritos inteiros com reposição."""
    rng = np.random.default_rng(seed)
    uc, inv = np.unique(dist, return_inverse=True)
    rows = [np.where(inv == i)[0] for i in range(len(uc))]
    for _ in range(n_boot):
        yield np.concatenate([rows[i] for i in rng.integers(0, len(uc), len(uc))])


# --- 1. OD: rua por modo, grade e bootstrap --------------------------------------------------------

def ler_od() -> pd.DataFrame:
    import pyogrio

    from cityomics.atlas.presenca import COLS, OD_DBF
    from cityomics.external import external_dir

    path = guard.pre2026(external_dir() / OD_DBF)
    od = pyogrio.read_dataframe(path, columns=COLS + ["ID_DOM", "ZONA"], read_geometry=False)
    return od[od["MUNI_DOM"].notna()]


def segmentos_rua(od: pd.DataFrame, modo: str = "pe_bici") -> pd.DataFrame:
    """Segmentos de rua (x, y, início, fim, peso, domicílio, zona) como em ``presenca.segments``.

    ``pe_bici`` reproduz o artigo (viagens a pé e de bicicleta inteiras na rua); ``pe`` conta inteiras só
    as viagens a pé, e das de bicicleta só os minutos andando nas pontas; ``bici`` é só o tempo pedalando."""
    trips = od[od["N_VIAG"].notna() & od["H_SAIDA"].notna() & od["H_CHEG"].notna()]
    dep = (trips["H_SAIDA"] * 60 + trips["MIN_SAIDA"].fillna(0)).to_numpy()
    arr = (trips["H_CHEG"] * 60 + trips["MIN_CHEG"].fillna(0)).to_numpy()
    arr = np.where(arr < dep, arr + 1440, arr)
    dur = arr - dep
    tip = trips["TIPVG"].to_numpy()
    if modo == "bici":
        ao = ad = np.where(tip == 4, dur / 2, 0.0)
    else:
        ativo = np.isin(tip, MODOS[modo])
        ao = np.where(ativo, dur / 2, trips["ANDA_O"].fillna(0).to_numpy())
        ad = np.where(ativo, dur / 2, trips["ANDA_D"].fillna(0).to_numpy())
    comum = {"w": trips["FE_VIA"].to_numpy(), "dom": trips["ID_DOM"].astype(str).to_numpy(),
             "zona": trips["ZONA"].fillna(-1).to_numpy()}
    rua = pd.concat([
        pd.DataFrame({"x": trips["CO_O_X"].to_numpy(), "y": trips["CO_O_Y"].to_numpy(), "a": dep, "b": dep + ao, **comum}),
        pd.DataFrame({"x": trips["CO_D_X"].to_numpy(), "y": trips["CO_D_Y"].to_numpy(), "a": arr - ad, "b": arr, **comum}),
    ], ignore_index=True)
    return rua[(rua["b"] > rua["a"]) & rua["x"].gt(0)].reset_index(drop=True)


def grade(setores) -> dict:
    """Grade de 100 m sobre o município, com o setor de cada célula (como em ``presenca.to_setores``)."""
    from rasterio import features
    from rasterio.transform import from_origin

    from cityomics.atlas.presenca import RES, _grid

    gx0, gy1, nx, ny = _grid(tuple(setores.total_bounds))
    ids = features.rasterize(zip(setores.geometry.values, np.arange(1, len(setores) + 1)), out_shape=(ny, nx),
                             transform=from_origin(gx0, gy1, RES, RES), fill=0, dtype="int32").ravel()
    rp = setores.geometry.representative_point()
    return {"gx0": gx0, "gy1": gy1, "nx": nx, "ny": ny, "ids": ids, "n": len(setores),
            "rix": np.clip(np.floor((rp.x.to_numpy() - gx0) / RES).astype(int), 0, nx - 1),
            "riy": np.clip(np.floor((gy1 - rp.y.to_numpy()) / RES).astype(int), 0, ny - 1),
            "area_cells": setores.geometry.area.to_numpy() / RES ** 2,
            "n_cells": np.bincount(ids, minlength=len(setores) + 1)[1:]}


def prepara(seg: pd.DataFrame, g: dict) -> dict:
    """Célula da grade e horas de sobreposição (n × 24) de cada segmento, uma vez por modo."""
    from pyproj import Transformer

    from cityomics.atlas.presenca import CRS, OD_CRS, RES, hour_overlap

    x, y = Transformer.from_crs(OD_CRS, CRS, always_xy=True).transform(seg["x"].to_numpy(float), seg["y"].to_numpy(float))
    ix = np.floor((x - g["gx0"]) / RES).astype(int)
    iy = np.floor((g["gy1"] - y) / RES).astype(int)
    ok = (ix >= 0) & (ix < g["nx"]) & (iy >= 0) & (iy < g["ny"])
    return {"cell": (iy[ok] * g["nx"] + ix[ok]), "H": hour_overlap(seg["a"].to_numpy()[ok], seg["b"].to_numpy()[ok]).astype(np.float32),
            "w": seg["w"].to_numpy()[ok], "dom": seg["dom"].to_numpy()[ok], "zona": seg["zona"].to_numpy()[ok]}


def rasteriza(p: dict, g: dict, sigma: float, mult: np.ndarray | None = None) -> np.ndarray:
    """Pessoas-hora na rua por setor × hora, suavizadas por um núcleo gaussiano de desvio ``sigma`` metros."""
    from scipy.ndimage import gaussian_filter

    from cityomics.atlas.presenca import RES

    w = p["w"] if mult is None else p["w"] * mult
    out = np.zeros((g["n"], 24))
    for h in range(24):
        G = np.bincount(p["cell"], weights=p["H"][:, h] * w, minlength=g["nx"] * g["ny"]).reshape(g["ny"], g["nx"])
        Gs = gaussian_filter(G, sigma / RES, mode="constant")
        Gs *= G.sum() / max(Gs.sum(), 1e-12)
        soma = np.bincount(g["ids"], weights=Gs.ravel(), minlength=g["n"] + 1)[1:]
        out[:, h] = np.where(g["n_cells"] >= 1, soma, Gs[g["riy"], g["rix"]] * g["area_cells"])
    return out


def estratos_od(p: dict) -> dict:
    """Domicílios ordenados por zona (estrato do desenho da OD) e o índice do domicílio de cada segmento."""
    dz = pd.DataFrame({"dom": p["dom"], "zona": p["zona"]}).drop_duplicates("dom").sort_values(["zona", "dom"])
    zonas, n_z = np.unique(dz["zona"].to_numpy(), return_counts=True)
    ini = np.concatenate([[0], np.cumsum(n_z)[:-1]])
    z_slot = np.repeat(np.arange(len(zonas)), n_z)
    pos = pd.Series(np.arange(len(dz)), index=dz["dom"].to_numpy())
    return {"ini": ini[z_slot], "n": n_z[z_slot], "n_dom": len(dz), "n_zonas": len(zonas)}, pos


def multiplicidade(est: dict, rng) -> np.ndarray:
    """Vezes que cada domicílio entra numa réplica: n_z sorteios com reposição dentro de cada zona."""
    draws = est["ini"] + np.floor(rng.random(est["n_dom"]) * est["n"]).astype(int)
    return np.bincount(draws, minlength=est["n_dom"]).astype(float)


def _densidade(R: np.ndarray, pos_ex: np.ndarray, area: np.ndarray) -> np.ndarray:
    """Pessoas na rua por km² nos setores de exploração (n × 24); setores sem área ficam com zero."""
    return np.nan_to_num(R[pos_ex] / np.where(area > 0, area, np.nan)[:, None])


# --- 1. estatísticas do denominador ---------------------------------------------------------------

def crime_rua(ids: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Roubo de celular em dias úteis 2024–2025 (setor × período, setor × hora exata), como em ``presenca``."""
    from cityomics.atlas.presenca import _crime

    ev = _crime(ids, "celular_roubo")
    n = ids.height
    e4 = ev[ev["per"].notna()]
    p = e4["per"].map({q: j for j, q in enumerate(PERIODOS)}).to_numpy().astype(int)
    Y4 = np.bincount(e4["i"].to_numpy() * 4 + p, minlength=n * 4).reshape(n, 4).astype(float)
    e24 = ev[ev["h"].notna()]
    Y24 = np.bincount(e24["i"].to_numpy() * 24 + e24["h"].astype(int).to_numpy(), minlength=n * 24).reshape(n, 24).astype(float)
    return Y4, Y24


def rho_km_pedestre(E, names, Y4, lam4, D, tol=1e-8) -> float:
    """ρ de Spearman entre a taxa por km e a taxa por pedestre (classes por km), como em ``presenca.analise``."""
    from scipy.stats import spearmanr

    rho = np.zeros_like(lam4)
    for j, q in enumerate(PERIODOS):
        Dp = D[:, list(HORAS_PERIODO[q])].mean(axis=1)
        Dp = Dp / Dp[Dp > 0].mean()
        rho[:, j] = em_fit_multi(E * Dp[:, None], Y4[:, [j]], tol=tol)[:, 0]
    tot_l, tot_r = lam4.sum(axis=1), rho.sum(axis=1)
    km = np.array([not nm.startswith("n_") for nm in names])
    ok = (tot_l > 0) & (tot_r > 0) & km
    return float(spearmanr(tot_l[ok], tot_r[ok]).statistic)


def relogio_rua(E, names, Y24, lam24, D, R) -> dict:
    """Perfil horário do roubo × perfil dos pedestres por classe e risco relativo por hora na cidade.

    ``risco_dens`` reproduz o código do artigo (soma das densidades dos setores); ``risco_pess`` divide pelo
    total de pessoas na rua (densidade × área), que é o que Methods descreve."""
    _, Pc, w = _contraste(lam24, E)
    fr = E.T @ D
    Pr = fr / np.where(fr.sum(1, keepdims=True) > 0, fr.sum(1, keepdims=True), 1.0)
    cor = {nm: float(np.corrcoef(Pc[k], Pr[k])[0, 1]) for k, nm in enumerate(names) if w[k] >= PESO_MIN}
    c = Y24.sum(0) / Y24.sum()
    risco_dens = c / (D.sum(0) / D.sum())
    risco_pess = c / (R.sum(0) / R.sum())
    kp = names.index(POPULAR)
    return {"cor": cor, "cor_mediana": float(np.median(list(cor.values()))),
            "risco_dens": risco_dens, "risco_pess": risco_pess,
            "pop_crime_04_06": float(Pc[kp, 4:6].sum()), "pop_rua_04_06": float(Pr[kp, 4:6].sum())}


def _resumo_rua(rho: float, rr: dict) -> dict:
    out = {"rho_km_pedestre": rho, "cor_mediana": rr["cor_mediana"], "cor_por_classe": rr["cor"],
           "pop_crime_04_06": rr["pop_crime_04_06"], "pop_rua_04_06": rr["pop_rua_04_06"]}
    for v in ("dens", "pess"):
        r = rr[f"risco_{v}"]
        out[f"risco_{v}"] = {"por_hora": r.tolist(), "h03": float(r[3]), "hora_pico": int(np.argmax(r)), "pico": float(r.max())}
    return out


def amostra_por_hora(p: dict, g: dict, pos_ex: np.ndarray) -> dict:
    """Segmentos de rua da amostra (sem expansão) em setores de exploração por hora, domicílios distintos e
    tamanho efetivo de Kish (Σw)²/Σw² do peso expandido: mostra em quantas viagens se apoia cada hora."""
    setor = g["ids"][p["cell"]] - 1
    ex = np.isin(setor, pos_ex)
    out = {"segmentos": [], "domicilios": [], "n_efetivo": []}
    for h in range(24):
        m = ex & (p["H"][:, h] > 0)
        w = p["w"][m] * p["H"][m, h]
        out["segmentos"].append(int(m.sum()))
        out["domicilios"].append(int(len(np.unique(p["dom"][m]))))
        out["n_efetivo"].append(float(w.sum() ** 2 / max((w ** 2).sum(), 1e-12)))
    return out


def pedestres(ids, E, names, n_boot: int = 500, n_boot_sigma: int = 200, n_boot_conj: int = 200, Ec=None, log=print) -> dict:
    from cityomics.atlas.spots import setores_attrs
    from cityomics.units.setores import load_setores

    t0 = time.time()
    od = ler_od()
    setores = load_setores()
    g = grade(setores)
    pos_all = pd.Series(np.arange(len(setores)), index=setores["cd_setor"].astype(str).to_numpy())
    pos_ex = pos_all.loc[ids["cd_setor"].to_list()].to_numpy()
    area = ids.join(setores_attrs().select("cd_setor", "area_km2"), on="cd_setor", how="left")["area_km2"].fill_null(0).to_numpy()
    Y4, Y24 = crime_rua(ids)
    lam4, lam24 = em_fit_multi(E, Y4), em_fit_multi(E, Y24)
    prep = {m: prepara(segmentos_rua(od, m), g) for m in ("pe_bici", "pe", "bici")}
    viagens = od[od["N_VIAG"].notna()]
    rep = {"tipvg": TIPVG, "fonte_codigos": "LAYOUT OD2017_v1.xlsx (TIPVG; MODO 15 bicicleta, 16 a pé)",
           "viagens_por_tipvg": {TIPVG[int(k)]: int(v) for k, v in viagens["TIPVG"].value_counts().items()},
           "viagens_expandidas_milhoes": {TIPVG[int(k)]: float(v) / 1e6 for k, v in viagens.groupby("TIPVG")["FE_VIA"].sum().items()},
           "amostra_por_hora": amostra_por_hora(prep["pe"], g, pos_ex)}
    a = rep["amostra_por_hora"]
    log(f"amostra na rua (exploração, só a pé): 3h {a['segmentos'][3]} segmentos de {a['domicilios'][3]} domicílios "
        f"(n efetivo {a['n_efetivo'][3]:.0f}); 18h {a['segmentos'][18]} ({a['n_efetivo'][18]:.0f})")

    # fração da bicicleta nas pessoas-hora na rua
    Rb = rasteriza(prep["bici"], g, 300.0)
    Rt = rasteriza(prep["pe_bici"], g, 300.0)
    rep["fracao_bicicleta"] = {"municipio": float(Rb.sum() / Rt.sum()), "exploracao": float(Rb[pos_ex].sum() / Rt[pos_ex].sum()),
                               "por_hora_exploracao": (Rb[pos_ex].sum(0) / Rt[pos_ex].sum(0)).tolist(),
                               "h03_exploracao": float(Rb[pos_ex, 3].sum() / Rt[pos_ex, 3].sum())}
    log(f"bicicleta: {rep['fracao_bicicleta']['exploracao']:.1%} das pessoas-hora na rua (exploração); "
        f"às 3h {rep['fracao_bicicleta']['h03_exploracao']:.1%}")

    # pontos: modo × σ
    pontos = {}
    for m in ("pe_bici", "pe"):
        for s in (150.0, 300.0, 600.0):
            R = rasteriza(prep[m], g, s)
            D = _densidade(R, pos_ex, area)
            pontos[f"{m}_s{int(s)}"] = _resumo_rua(rho_km_pedestre(E, names, Y4, lam4, D), relogio_rua(E, names, Y24, lam24, D, R[pos_ex]))
            p = pontos[f"{m}_s{int(s)}"]
            log(f"{m} σ={int(s)}: ρ={p['rho_km_pedestre']:.3f}; risco 3h={p['risco_dens']['h03']:.1f} (pico {p['risco_dens']['hora_pico']}h); "
                f"por pessoa 3h={p['risco_pess']['h03']:.1f} (pico {p['risco_pess']['hora_pico']}h); r mediana={p['cor_mediana']:.3f}")
    rep["pontos"] = pontos
    if Ec is not None:   # exposição de ruas corrigida (achado colateral), só pontos
        l4c, l24c = em_fit_multi(Ec, Y4), em_fit_multi(Ec, Y24)
        for m in ("pe", "pe_bici"):
            R = rasteriza(prep[m], g, 300.0)
            D = _densidade(R, pos_ex, area)
            rep.setdefault("pontos_ruas_corrigidas", {})[f"{m}_s300"] = _resumo_rua(
                rho_km_pedestre(Ec, names, Y4, l4c, D), relogio_rua(Ec, names, Y24, l24c, D, R[pos_ex]))
        pc = rep["pontos_ruas_corrigidas"]["pe_s300"]
        log(f"ruas corrigidas, só a pé σ=300: ρ={pc['rho_km_pedestre']:.3f}; r mediana={pc['cor_mediana']:.3f}")

    # bootstrap da OD: domicílios com reposição dentro da zona (estrato), crime fixo
    rep["bootstrap_od"] = {}
    for m, s, B in (("pe", 300.0, n_boot), ("pe_bici", 300.0, n_boot), ("pe", 150.0, n_boot_sigma), ("pe", 600.0, n_boot_sigma)):
        est, pos_dom = estratos_od(prep[m])
        dom_idx = pos_dom.loc[prep[m]["dom"]].to_numpy()
        rng = np.random.default_rng(11)
        draws = []
        for b in range(B):
            mult = multiplicidade(est, rng)[dom_idx]
            R = rasteriza(prep[m], g, s, mult)
            D = _densidade(R, pos_ex, area)
            draws.append(_resumo_rua(rho_km_pedestre(E, names, Y4, lam4, D, tol=TOL_BOOT),
                                     relogio_rua(E, names, Y24, lam24, D, R[pos_ex])))
        rep["bootstrap_od"][f"{m}_s{int(s)}"] = _resume_boot(draws, est)
        log(f"bootstrap OD {m} σ={int(s)} (B={B}): {_linha_boot(rep['bootstrap_od'][f'{m}_s{int(s)}'])} [{time.time() - t0:.0f}s]")

    # bootstrap conjunto: OD (domicílio na zona) e crime (distritos), só a pé e σ = 300 m
    est, pos_dom = estratos_od(prep["pe"])
    dom_idx = pos_dom.loc[prep["pe"]["dom"]].to_numpy()
    rng = np.random.default_rng(12)
    draws = []
    for b, idx in enumerate(_boot_distritos(ids["cd_dist"].to_numpy(), n_boot_conj, seed=13)):
        R = rasteriza(prep["pe"], g, 300.0, multiplicidade(est, rng)[dom_idx])
        D = _densidade(R, pos_ex, area)[idx]
        Eb, Y4b, Y24b = E[idx], Y4[idx], Y24[idx]
        l4, l24 = em_fit_multi(Eb, Y4b, tol=TOL_BOOT), em_fit_multi(Eb, Y24b, tol=TOL_BOOT)
        draws.append(_resumo_rua(rho_km_pedestre(Eb, names, Y4b, l4, D, tol=TOL_BOOT), relogio_rua(Eb, names, Y24b, l24, D, R[pos_ex][idx])))
    rep["bootstrap_conjunto"] = _resume_boot(draws, est) | {"modo": "pe_s300", "unidade_crime": "distrito"}
    log(f"bootstrap conjunto (B={n_boot_conj}): {_linha_boot(rep['bootstrap_conjunto'])} [{time.time() - t0:.0f}s]")
    rep["eventos"] = {"periodo": float(Y4.sum()), "hora_exata": float(Y24.sum())}
    return rep


def _resume_boot(draws: list[dict], est: dict) -> dict:
    out = {"B": len(draws), "domicilios": int(est["n_dom"]), "zonas": int(est["n_zonas"])}
    out["rho_km_pedestre"] = _ic([d["rho_km_pedestre"] for d in draws])
    out["cor_mediana"] = _ic([d["cor_mediana"] for d in draws])
    out["pop_rua_04_06"] = _ic([d["pop_rua_04_06"] for d in draws])
    for v in ("dens", "pess"):
        h03 = [d[f"risco_{v}"]["h03"] for d in draws]
        pico = [d[f"risco_{v}"]["pico"] for d in draws]
        hp = np.array([d[f"risco_{v}"]["hora_pico"] for d in draws])
        curva = np.array([d[f"risco_{v}"]["por_hora"] for d in draws])
        out[f"risco_{v}"] = {"h03": _ic(h03), "pico": _ic(pico),
                             "hora_pico_freq": {str(h): float(np.mean(hp == h)) for h in np.unique(hp)},
                             "por_hora_lo": np.percentile(curva, 2.5, axis=0).tolist(),
                             "por_hora_hi": np.percentile(curva, 97.5, axis=0).tolist()}
    return out


def _linha_boot(b: dict) -> str:
    return (f"ρ {np.round(b['rho_km_pedestre'], 2)}; risco 3h {np.round(b['risco_dens']['h03'], 1)} "
            f"(pico {b['risco_dens']['hora_pico_freq']}); por pessoa 3h {np.round(b['risco_pess']['h03'], 1)}; "
            f"r mediana {np.round(b['cor_mediana'], 3)}")


# --- 2. relógio: nulo em blocos ---------------------------------------------------------------------

def blocos(i: np.ndarray, t: np.ndarray, p: np.ndarray, dist: np.ndarray) -> dict:
    """Blocos de eventos do mesmo setor ``i``, mesma unidade de tempo ``t`` e mesmo período ``p``.

    Devolve o setor, o período, o tamanho e o grupo de troca (distrito × tamanho) de cada bloco."""
    T = int(t.max()) + 1
    key = (i.astype(np.int64) * T + t.astype(np.int64)) * 4 + p.astype(np.int64)
    uk, n = np.unique(key, return_counts=True)
    bi = (uk // 4) // T
    grupo = dist[bi].astype(np.int64) * (int(n.max()) + 1) + n
    _, grupo = np.unique(grupo, return_inverse=True)
    return {"i": bi, "p": (uk % 4).astype(int), "n": n.astype(float), "grupo": grupo}


def permuta_blocos(b: dict, rng) -> np.ndarray:
    """Rótulos de período permutados entre blocos do mesmo grupo (distrito × tamanho)."""
    o0 = np.argsort(b["grupo"], kind="stable")
    o1 = np.lexsort((rng.random(len(b["grupo"])), b["grupo"]))
    pp = np.empty_like(b["p"])
    pp[o0] = b["p"][o1]
    return pp


def _fixos(b: dict) -> float:
    """Parte dos eventos em blocos sem par no grupo (não trocam de rótulo)."""
    cnt = np.bincount(b["grupo"])
    return float(b["n"][cnt[b["grupo"]] == 1].sum() / b["n"].sum())


def relogio_blocos(ids, E, names, desfechos=("celular_roubo", "celular_furto"), n_perm_ind: int = 200,
                   n_perm_bloco: int = 999, log=print) -> dict:
    n = ids.height
    dist_all = np.unique(ids["cd_dist"].to_numpy(), return_inverse=True)[1]
    rng = np.random.default_rng(0)          # mesma semente e mesma ordem de ``fenotipo.relogio``
    rng_b = np.random.default_rng(21)
    rep = {}
    for d in desfechos:
        ev_all = _eventos_relogio(ids, d, ANOS)
        res = {}
        for a in ANOS:
            ev = ev_all[(ev_all["data_fato"].dt.year == a) & ev_all["per"].notna()]
            i = ev["i"].to_numpy()
            p = ev["per"].map({q: j for j, q in enumerate(PERIODOS)}).to_numpy().astype(int)
            Y = np.bincount(i * 4 + p, minlength=n * 4).reshape(n, 4).astype(float)
            H = _contraste(em_fit_multi(E, Y), E)[0]
            g = dist_all[i]
            # nulo do artigo (eventos independentes dentro do distrito), reproduzido
            o0 = np.argsort(g, kind="stable")
            Hp = np.empty(n_perm_ind)
            for k in range(n_perm_ind):
                o1 = np.lexsort((rng.random(len(g)), g))
                pp = np.empty_like(p)
                pp[o0] = p[o1]
                Hp[k] = _contraste(em_fit_multi(E, np.bincount(i * 4 + pp, minlength=n * 4).reshape(n, 4).astype(float), tol=1e-6), E)[0]
            r = {"eventos": int(len(ev)), "H": H,
                 "individual": {"n_perm": n_perm_ind, "p": float((1 + np.sum(Hp >= H)) / (1 + n_perm_ind)),
                                "H_nulo_mediana": float(np.median(Hp)), "H_nulo_p95": float(np.percentile(Hp, 95))}}
            dia = (ev["data_fato"].dt.normalize() - pd.Timestamp(f"{a}-01-01")).dt.days.to_numpy()
            mes = ev["data_fato"].dt.month.to_numpy() - 1
            for nome, t in (("dia", dia), ("mes", mes)):
                b = blocos(i, t, p, dist_all)
                Hb = np.empty(n_perm_bloco)
                for k in range(n_perm_bloco):
                    Yb = np.bincount(b["i"] * 4 + permuta_blocos(b, rng_b), weights=b["n"], minlength=n * 4).reshape(n, 4)
                    Hb[k] = _contraste(em_fit_multi(E, Yb, tol=1e-6), E)[0]
                r[nome] = {"n_perm": n_perm_bloco, "p": float((1 + np.sum(Hb >= H)) / (1 + n_perm_bloco)),
                           "H_nulo_mediana": float(np.median(Hb)), "H_nulo_p95": float(np.percentile(Hb, 95)),
                           "blocos": int(len(b["n"])), "eventos_em_blocos_maiores_que_1": float(b["n"][b["n"] > 1].sum() / b["n"].sum()),
                           "eventos_em_blocos_fixos": _fixos(b), "maior_bloco": int(b["n"].max())}
            res[str(a)] = r
            log(f"relógio {d} {a}: H={H:.4f}; P individual={r['individual']['p']:.3f}, dia={r['dia']['p']:.3f}, "
                f"mês={r['mes']['p']:.3f}; eventos em blocos >1: dia {r['dia']['eventos_em_blocos_maiores_que_1']:.1%}, "
                f"mês {r['mes']['eventos_em_blocos_maiores_que_1']:.1%}")
        rep[d] = res
    return rep


# --- 3. intervalos do relógio ---------------------------------------------------------------------

def _dominio(E, names, Y24) -> dict:
    """Setores em que o popular (ou o comércio) tem ao menos metade do roubo esperado (``robustez.relogio_bruto``)."""
    lam = em_fit_multi(E, Y24.sum(axis=1, keepdims=True))[:, 0]
    contrib = E * lam[None, :]
    share = contrib / np.maximum(contrib.sum(axis=1, keepdims=True), 1e-12)
    return {"popular": share[:, GR.indices(names, "popular")].sum(axis=1) >= 0.5,
            "comercio": share[:, GR.indices(names, "comercio_amplo")].sum(axis=1) >= 0.5}


def _parte_04_06(E, lam24, Y24, mask) -> tuple[float, float]:
    """Parte das 04–06h prevista pelo modelo e observada nos setores ``mask``."""
    mu = E[mask] @ lam24
    return float(mu[:, 4:6].sum() / mu.sum()), float(Y24[mask, 4:6].sum() / max(Y24[mask].sum(), 1e-12))


def relogio_ic(ids, E, names, n_boot: int = 200, log=print) -> dict:
    t0 = time.time()
    Y4, Y24 = crime_rua(ids)
    kp = names.index(POPULAR)
    dom = _dominio(E, names, Y24)
    lam24 = em_fit_multi(E, Y24)
    _, P, _ = _contraste(lam24, E)
    pt = {"classe_modelo": float(P[kp, 4:6].sum())}
    for nm, m in dom.items():
        pt[f"{nm}_previsto"], pt[f"{nm}_observado"] = _parte_04_06(E, lam24, Y24, m)
        pt[f"{nm}_setores"], pt[f"{nm}_eventos"] = int(m.sum()), float(Y24[m].sum())
    draws = {k: [] for k in ("classe_modelo", "popular_previsto", "popular_observado", "comercio_previsto", "comercio_observado")}
    dist = ids["cd_dist"].to_numpy()
    for idx in _boot_distritos(dist, n_boot, seed=31):
        lb = em_fit_multi(E[idx], Y24[idx], tol=TOL_BOOT)
        _, Pb, _ = _contraste(lb, E[idx])
        draws["classe_modelo"].append(Pb[kp, 4:6].sum())
        for nm, m in dom.items():
            pv, ob = _parte_04_06(E[idx], lb, Y24[idx], m[idx])
            draws[f"{nm}_previsto"].append(pv)
            draws[f"{nm}_observado"].append(ob)
    out = {"pre_amanhecer": {"ponto": pt, "ic": {k: _ic(v) for k, v in draws.items()}, "B": n_boot,
                             "nota": "dias úteis 2024–2025, hora exata, roubo de celular; bootstrap de distritos"}}
    log(f"04–06h popular: modelo {pt['classe_modelo']:.3f} {np.round(out['pre_amanhecer']['ic']['classe_modelo'], 3)}; "
        f"previsto nos setores dominados {pt['popular_previsto']:.3f}; observado {pt['popular_observado']:.3f} [{time.time() - t0:.0f}s]")
    out["fim_de_semana"] = fim_de_semana_ic(ids, E, names, dom["popular"], n_boot=n_boot)
    log(f"fim de semana/dia útil, roubo popular: {out['fim_de_semana']['celular_roubo']['classes'].get(POPULAR)} [{time.time() - t0:.0f}s]")
    return out


def _razao_fds(E, Y, n_fds, n_util, tol=1e-8) -> tuple[np.ndarray, np.ndarray]:
    lam = em_fit_multi(E, Y, tol=tol)
    _, _, w = _contraste(lam, E)
    return (lam[:, 1] / n_fds) / np.where(lam[:, 0] > 0, lam[:, 0] / n_util, np.nan), w


def _razao_obs(Y: np.ndarray, m: np.ndarray, n_fds: int, n_util: int) -> float:
    """Razão fim de semana/dia útil das contagens diárias, sem modelo, nos setores ``m``."""
    return float((Y[m, 1].sum() / n_fds) / max(Y[m, 0].sum() / n_util, 1e-12))


def fim_de_semana_ic(ids, E, names, mask_pop, desfechos=("celular_roubo", "celular_furto", "roubo_outros", "transito"),
                     n_boot: int = 200) -> dict:
    """Razão fim de semana/dia útil das taxas diárias por classe (``fenotipo._fim_de_semana``) com bootstrap de distritos."""
    dias = pd.date_range(f"{ANOS[0]}-01-01", f"{ANOS[-1]}-12-31")
    n_fds, n_util = int((dias.dayofweek >= 5).sum()), int((dias.dayofweek < 5).sum())
    n = ids.height
    dist = ids["cd_dist"].to_numpy()
    out = {"dias_fim_de_semana": n_fds, "dias_uteis": n_util, "B": n_boot}
    for d in desfechos:
        ev = _eventos_relogio(ids, d, ANOS)
        fds = (ev["data_fato"].dt.dayofweek >= 5).to_numpy().astype(int)
        Y = np.bincount(ev["i"].to_numpy() * 2 + fds, minlength=n * 2).reshape(n, 2).astype(float)
        r, w = _razao_fds(E, Y, n_fds, n_util)
        boot = np.array([_razao_fds(E[idx], Y[idx], n_fds, n_util, tol=TOL_BOOT)[0] for idx in _boot_distritos(dist, n_boot, seed=32)])
        lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
        res = {"classes": {nm: {"razao": float(r[k]), "ic": [float(lo[k]), float(hi[k])]} for k, nm in enumerate(names) if w[k] >= PESO_MIN}}
        # contagem sem modelo nos setores dominados pelo popular
        res["popular_domina_sem_modelo"] = {"razao": _razao_obs(Y, mask_pop, n_fds, n_util), "eventos": float(Y[mask_pop].sum()),
                                            "ic": _ic([_razao_obs(Y[idx], mask_pop[idx], n_fds, n_util)
                                                       for idx in _boot_distritos(dist, n_boot, seed=33)])}
        out[d] = res
    return out


# --- 4. concentração da queda ---------------------------------------------------------------------

def gini(x: np.ndarray) -> float:
    x = np.sort(np.asarray(x, float))
    if x.sum() <= 0:
        return float("nan")
    n = len(x)
    return float((2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum())) - (n + 1) / n)


def concentracao(y0: np.ndarray, y1: np.ndarray, fracs=(0.01, 0.05, 0.10)) -> dict:
    """Parte da queda líquida (Σ y0 − y1) vinda das unidades com maior queda absoluta, e o mesmo para o crime inicial."""
    d = y0 - y1
    F = d.sum()
    ordem = np.argsort(-d, kind="stable")
    ordem0 = np.argsort(-y0, kind="stable")
    out = {"unidades": int(len(d)), "total_ini": float(y0.sum()), "total_fim": float(y1.sum()), "queda_liquida": float(F),
           "queda_bruta": float(d[d > 0].sum()), "aumento_bruto": float(-d[d < 0].sum()),
           "unidades_com_queda": float(np.mean(d > 0)), "unidades_com_aumento": float(np.mean(d < 0)),
           "gini_quedas": gini(np.clip(d, 0, None)), "gini_ini": gini(y0)}
    for q in fracs:
        k = max(1, int(np.ceil(q * len(d))))
        top, top0 = ordem[:k], ordem0[:k]
        out[f"top{int(round(q * 100))}"] = {"unidades": k, "parte_queda": float(d[top].sum() / F),
                                             "parte_ini_mesmas": float(y0[top].sum() / y0.sum()),
                                             "parte_ini_topo_ini": float(y0[top0].sum() / y0.sum()),
                                             "parte_queda_topo_ini": float(d[top0].sum() / F)}
    return out


def nulo_proporcional(y0: np.ndarray, y1: np.ndarray, n_sim: int = 200, seed: int = 41) -> dict:
    """Concentração esperada se todas as unidades caíssem na mesma proporção, com ruído de Poisson."""
    r = y1.sum() / y0.sum()
    mu0 = (y0 + y1) / (1 + r)
    rng = np.random.default_rng(seed)
    sims = [concentracao(rng.poisson(mu0).astype(float), rng.poisson(r * mu0).astype(float)) for _ in range(n_sim)]
    out = {"n_sim": n_sim, "razao": float(r), "gini_quedas": _ic([s["gini_quedas"] for s in sims]) + [float(np.mean([s["gini_quedas"] for s in sims]))]}
    for t in ("top1", "top5", "top10"):
        v = [s[t]["parte_queda"] for s in sims]
        out[t] = {"parte_queda_media": float(np.mean(v)), "parte_queda_ic": _ic(v)}
    return out


def queda_setores(ids, E, names, n_sim: int = 200, log=print) -> dict:
    tab = pl.read_parquet(guard.pre2026(out_dir() / "fenotipo_setor_ano.parquet")).filter(pl.col("fenotipo") == "celular_roubo")
    tab = tab.filter(pl.Series(guard.explore_mask(tab["cd_dist"].to_numpy())))
    _, Y24 = crime_rua(ids)
    dom = _dominio(E, names, Y24)
    out = {}
    for col in ("n_total", "n_geo"):
        w = tab.filter(pl.col("ano").is_in([2022, 2025])).pivot(on="ano", index="cd_setor", values=col, aggregate_function="sum").fill_null(0.0)
        Y = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select(["2022", "2025"]).to_numpy().astype(float)
        y0, y1 = Y[:, 0], Y[:, 1]
        res = {"todos": concentracao(y0, y1), "nulo_proporcional": nulo_proporcional(y0, y1, n_sim)}
        m = dom["popular"]
        res["popular_domina"] = concentracao(y0[m], y1[m]) | {"nulo_proporcional": nulo_proporcional(y0[m], y1[m], n_sim)}
        res["grupos"] = _queda_por_grupo(E, names, y0, y1)
        out[col] = res
        log(f"queda {col}: total {y0.sum():,.0f} → {y1.sum():,.0f}; top1% → {res['todos']['top1']['parte_queda']:.1%} da queda "
            f"(nulo {res['nulo_proporcional']['top1']['parte_queda_media']:.1%}); top10% → {res['todos']['top10']['parte_queda']:.1%} "
            f"(nulo {res['nulo_proporcional']['top10']['parte_queda_media']:.1%}); Gini {res['todos']['gini_quedas']:.2f}")
    return out


def _queda_por_grupo(E, names, y0, y1) -> dict:
    """Parte da queda líquida e do roubo de 2022 nos setores dominados (≥ 50% do esperado em 2022) por polos,
    residencial ou ruas, e a composição por grupo dos setores com maior queda absoluta."""
    lam = em_fit_multi(E, y0[:, None])[:, 0]
    c = E * lam[None, :]
    s = c / np.maximum(c.sum(axis=1, keepdims=True), 1e-12)
    grupos = {"residencial": GR.indices(names, "residencial"), "polos": GR.indices(names, "polos"),
              "ruas": [k for k, n in enumerate(names) if n.startswith("rua_")]}
    d = y0 - y1
    out, masks = {}, {}
    for g, ks in grupos.items():
        m = masks[g] = s[:, ks].sum(axis=1) >= 0.5
        out[g] = {"setores": int(m.sum()), "parte_queda": float(d[m].sum() / d.sum()), "parte_2022": float(y0[m].sum() / y0.sum()),
                  "razao_2025_2022": float(y1[m].sum() / max(y0[m].sum(), 1e-12))}
    masks["misto"] = ~np.any(np.column_stack(list(masks.values())), axis=1)
    out["misto"] = {"setores": int(masks["misto"].sum()), "parte_queda": float(d[masks["misto"]].sum() / d.sum()),
                    "parte_2022": float(y0[masks["misto"]].sum() / y0.sum()),
                    "razao_2025_2022": float(y1[masks["misto"]].sum() / max(y0[masks["misto"]].sum(), 1e-12))}
    ordem = np.argsort(-d, kind="stable")
    for q in (0.01, 0.10):
        top = np.zeros(len(d), bool)
        top[ordem[:max(1, int(np.ceil(q * len(d))))]] = True
        out[f"top{int(q * 100)}_composicao"] = {g: {"setores": int((m & top).sum()), "parte_da_queda_do_topo": float(d[m & top].sum() / d[top].sum()),
                                                     "parte_2022_do_topo": float(y0[m & top].sum() / y0[top].sum())} for g, m in masks.items()}
    return out


# --- achado colateral: setor dos segmentos de rua ----------------------------------------------------

def ruas_setor_correto():
    """``ruas.parquet`` com o setor recalculado pelo ponto médio de cada segmento.

    Em ``streets.segments`` o ``reset_index`` vem antes do ``drop_duplicates``: o GeoDataFrame dos pontos
    médios é montado com ``np.arange`` e geometria de índice não contíguo, o geopandas alinha pelo rótulo e
    cada linha recebe o ponto médio de outro segmento (ou nenhum). A geometria, a classe e o comprimento de
    cada linha estão certos; só ``cd_setor`` está trocado."""
    import geopandas as gpd

    from cityomics.atlas.genes_lote import atlas_dir
    from cityomics.units.setores import load_setores

    seg = gpd.read_parquet(guard.pre2026(atlas_dir() / "ruas.parquet"))
    mid = gpd.GeoDataFrame({"i": np.arange(len(seg))}, geometry=seg.geometry.interpolate(0.5, normalized=True).values, crs=seg.crs)
    j = gpd.sjoin(mid, load_setores()[["cd_setor", "geometry"]], how="left", predicate="within").drop_duplicates("i").sort_values("i")
    seg["cd_setor_ok"] = j["cd_setor"].to_numpy()
    return seg


def diagnostico_ruas(seg) -> dict:
    """Quanto o setor gravado em ``ruas.parquet`` difere do setor do ponto médio, e o efeito na exposição por setor."""
    from scipy.stats import pearsonr, spearmanr

    from cityomics.atlas.genes_lote import atlas_dir

    ok = seg.pivot_table(index="cd_setor_ok", columns="classe", values="comprimento_m", aggfunc="sum", fill_value=0.0)
    old = pd.read_parquet(guard.pre2026(atlas_dir() / "setor_ruas_estacoes.parquet")).set_index("cd_setor")
    old.index = old.index.astype(str)
    cmp = old.join(ok, how="left").fillna(0.0)
    out = {"segmentos": int(len(seg)), "sem_setor_gravado": float(seg["cd_setor"].isna().mean()),
           "setor_gravado_igual_ao_ponto_medio": float(np.mean(seg["cd_setor"].astype(str).to_numpy() == seg["cd_setor_ok"].astype(str).to_numpy())),
           "distrito_gravado_igual": float(np.mean(seg["cd_setor"].astype(str).str[:9].to_numpy() == seg["cd_setor_ok"].astype(str).str[:9].to_numpy()))}
    for c in ("arterial", "coletora", "local"):
        a, b = cmp[f"rua_{c}_m"].to_numpy(), cmp[c].to_numpy()
        out[c] = {"km_gravado": float(a.sum() / 1e3), "km_correto": float(b.sum() / 1e3), "pearson": float(pearsonr(a, b)[0]),
                  "spearman": float(spearmanr(a, b).statistic)}
    return out


def setor_exposicao_corrigida(ids: pl.DataFrame, E: np.ndarray, names: list[str], seg) -> np.ndarray:
    """E com as três classes de rua refeitas com o setor do ponto médio (km), mesmos setores e classes."""
    ok = seg.pivot_table(index="cd_setor_ok", columns="classe", values="comprimento_m", aggfunc="sum", fill_value=0.0)
    ok.index = ok.index.astype(str)
    Ec = E.copy()
    for c in ("arterial", "coletora", "local"):
        Ec[:, names.index(f"rua_{c}_m")] = ok[c].reindex(ids["cd_setor"].to_list()).fillna(0.0).to_numpy() / 1000.0
    return Ec


def _celular_2025(ids) -> np.ndarray:
    from cityomics.paths import processed_dir

    t = pl.read_parquet(guard.pre2026(processed_dir() / "alvos" / "celular_setor_mes.parquet")).with_columns(pl.col("cd_setor").cast(pl.String))
    t = t.filter(pl.col("periodo").str.starts_with("2025")).group_by("cd_setor").agg(pl.col("n_total").sum())
    return ids.select("cd_setor").join(t, on="cd_setor", how="left").fill_null(0.0)["n_total"].to_numpy().astype(float)[:, None]


def sensibilidade_ruas(ids, E, names, seg, n_perm: int = 200, log=print) -> dict:
    """Números deste relatório e do artigo com E original e com a exposição de ruas corrigida (só pontos)."""
    from scipy.stats import spearmanr

    from cityomics.atlas.robustez import queda_por_desfecho

    Ec = setor_exposicao_corrigida(ids, E, names, seg)
    y25 = _celular_2025(ids)
    Y4, Y24 = crime_rua(ids)
    out = {"diagnostico": diagnostico_ruas(seg)}
    kp = names.index(POPULAR)
    for rot, M in (("original", E), ("corrigida", Ec)):
        lam = em_fit_multi(M, y25)[:, 0]
        mu = M @ lam
        y = y25[:, 0]
        dev = 2 * np.sum(np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / np.maximum(mu, 1e-12)), 0) - (y - mu))
        m0 = y.mean()
        dev0 = 2 * np.sum(np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / m0), 0) - (y - m0))
        lam24 = em_fit_multi(M, Y24)
        _, P, w = _contraste(lam24, M)
        r = {"celular_2025_lambda": dict(zip(names, lam.tolist())), "celular_2025_D2": float(1 - dev / dev0),
             "pop_04_06_modelo": float(P[kp, 4:6].sum())}
        qd = queda_por_desfecho(ids, M, names, n_boot=2)
        r["queda_roubo_razao_rel"] = {k: v["razao_rel"] for k, v in qd["celular_roubo"]["classes"].items()}
        dias = pd.date_range(f"{ANOS[0]}-01-01", f"{ANOS[-1]}-12-31")
        n_fds, n_util = int((dias.dayofweek >= 5).sum()), int((dias.dayofweek < 5).sum())
        ev = _eventos_relogio(ids, "celular_roubo", ANOS)
        Yf = np.bincount(ev["i"].to_numpy() * 2 + (ev["data_fato"].dt.dayofweek >= 5).to_numpy().astype(int),
                         minlength=ids.height * 2).reshape(ids.height, 2).astype(float)
        r["fds_roubo_popular"] = float(_razao_fds(M, Yf, n_fds, n_util)[0][kp])
        r["relogio"] = _relogio_pontos(ids, M, n_perm)
        out[rot] = r
    a, b = out["original"]["celular_2025_lambda"], out["corrigida"]["celular_2025_lambda"]
    out["spearman_lambda_celular_2025"] = float(spearmanr([a[n] for n in names], [b[n] for n in names]).statistic)
    tipos = [n for n in names if not n.startswith(("rua_", "n_"))]
    out["spearman_lambda_tipos"] = float(spearmanr([a[n] for n in tipos], [b[n] for n in tipos]).statistic)
    log(f"ruas corrigidas: ρ(λ) = {out['spearman_lambda_celular_2025']:.3f} (só tipos {out['spearman_lambda_tipos']:.3f}); "
        f"D² {out['original']['celular_2025_D2']:.3f} → {out['corrigida']['celular_2025_D2']:.3f}; "
        f"04–06h popular {out['original']['pop_04_06_modelo']:.3f} → {out['corrigida']['pop_04_06_modelo']:.3f}")
    return out, Ec


def _relogio_pontos(ids, M, n_perm: int) -> dict:
    """H e P (nulo individual do artigo, 200 permutações) para furto e roubo de celular, 2024 e 2025."""
    n = ids.height
    dist_all = np.unique(ids["cd_dist"].to_numpy(), return_inverse=True)[1]
    rng = np.random.default_rng(0)
    out = {}
    for d in ("celular_roubo", "celular_furto"):
        ev_all = _eventos_relogio(ids, d, ANOS)
        for a in ANOS:
            ev = ev_all[(ev_all["data_fato"].dt.year == a) & ev_all["per"].notna()]
            i = ev["i"].to_numpy()
            p = ev["per"].map({q: j for j, q in enumerate(PERIODOS)}).to_numpy().astype(int)
            H = _contraste(em_fit_multi(M, np.bincount(i * 4 + p, minlength=n * 4).reshape(n, 4).astype(float)), M)[0]
            g = dist_all[i]
            o0 = np.argsort(g, kind="stable")
            Hp = np.empty(n_perm)
            for k in range(n_perm):
                pp = np.empty_like(p)
                pp[o0] = p[np.lexsort((rng.random(len(g)), g))]
                Hp[k] = _contraste(em_fit_multi(M, np.bincount(i * 4 + pp, minlength=n * 4).reshape(n, 4).astype(float), tol=1e-6), M)[0]
            out[f"{d}_{a}"] = {"H": H, "p": float((1 + np.sum(Hp >= H)) / (1 + n_perm))}
    return out


# --- 4–5. segmentos de rua ------------------------------------------------------------------------

def segmentos_estrito(desfechos=("celular_roubo", "celular_furto", "roubo_outros", "furto_outros"), log=print):
    """Variante de ``perturbacao.segmentos``: setor de cada segmento pelo ponto médio (``ruas_setor_correto``),
    eventos só de distritos de exploração e contagens por desfecho."""
    import geopandas as gpd
    from shapely import STRtree

    from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir
    from cityomics.atlas.perturbacao import N_MESES, _mes
    from cityomics.atlas.streets import stations
    from cityomics.units.setores import CRS

    seg = ruas_setor_correto()
    seg["cd_dist"] = seg["cd_setor_ok"].astype(str).str[:9]
    seg = seg[seg["cd_setor_ok"].notna() & guard.explore_mask(seg["cd_dist"].to_numpy())].reset_index(drop=True)
    tree = STRtree(seg.geometry.values)
    cel = pl.read_parquet(guard.pre2026(atlas_dir() / f"celulas_{REF_YEAR}.parquet"), columns=["classe", "sql_base", "x", "y"]).filter(
        (pl.col("classe") == "lote") & pl.col("x").is_not_null())
    q = tree.query_nearest(gpd.points_from_xy(cel["x"], cel["y"]), max_distance=40.0, return_distance=False)
    lote_seg = pl.DataFrame({"sql_base": cel["sql_base"].to_numpy()[q[0]], "seg": q[1]}).unique("sql_base", keep="first")
    del cel

    ev = pl.read_parquet(guard.pre2026(interim_dir() / EVENTOS),
                         columns=["desfecho", "data_fato", "coord_valida", "latitude", "longitude", "cd_dist"])
    ev = ev.filter(pl.col("desfecho").is_in(list(desfechos)) & pl.col("coord_valida"))
    ev = ev.filter(pl.Series(guard.explore_mask(ev["cd_dist"].cast(pl.String).fill_null("").to_numpy())))
    pts = gpd.GeoSeries(gpd.points_from_xy(ev["longitude"], ev["latitude"]), crs="EPSG:4326").to_crs(CRS)
    st = stations()
    near = STRtree(st.geometry.values).query_nearest(pts.values, max_distance=100.0, return_distance=False)
    longe = np.ones(len(pts), bool)
    longe[near[0]] = False
    qe = tree.query_nearest(pts.values[longe], max_distance=60.0, return_distance=False)
    mes = _mes(ev["data_fato"])[longe][qe[0]]
    fen = ev["desfecho"].to_numpy()[longe][qe[0]]
    ok = (mes >= 0) & (mes < N_MESES)
    Y = {}
    for f in desfechos:
        m = ok & (fen == f)
        Y[f] = np.zeros((len(seg), N_MESES), dtype=np.float32)
        np.add.at(Y[f], (qe[1][m], mes[m]), 1.0)
    log(f"segmentos de exploração: {len(seg):,}; eventos ligados: {int(ok.sum()):,} (só distritos de exploração)")
    return seg, lote_seg, Y


def queda_segmentos(Y: dict, n_sim: int = 200) -> dict:
    Yr = Y["celular_roubo"]
    y0, y1 = Yr[:, 0:12].sum(axis=1).astype(float), Yr[:, 36:48].sum(axis=1).astype(float)
    return {"todos": concentracao(y0, y1), "nulo_proporcional": nulo_proporcional(y0, y1, n_sim),
            "com_roubo": {"segmentos_com_algum_roubo": int(((y0 + y1) > 0).sum())}}


# --- 5. evento-estudo -----------------------------------------------------------------------------

def att_vec(Y: np.ndarray, coorte: np.ndarray, celula: np.ndarray, C: np.ndarray, tr: np.ndarray) -> dict:
    """Mesmo estimador de ``perturbacao.att``, vetorizado: média, sobre os tratados, de
    (Y_i,g+e − base_i) − (C_c,g+e − base_c), com base = média dos meses −12 a −7."""
    from cityomics.atlas.perturbacao import BASE, POS, PRE

    tr = tr[~np.isnan(C[celula[tr], 0])]
    g, c = coorte[tr][:, None], celula[tr][:, None]
    es, bs = np.arange(PRE[0], POS[1] + 1), np.arange(BASE[0], BASE[1] + 1)
    bt, bc = Y[tr[:, None], g + bs].mean(axis=1), C[c, g + bs].mean(axis=1)
    D = (Y[tr[:, None], g + es] - bt[:, None]) - (C[c, g + es] - bc[:, None])
    path = D.mean(axis=0)
    return {"n": int(len(tr)), "base": float(bt.mean()), "pre": float(path[es < 0].mean()), "efeito": float(path[es >= 0].mean()),
            "caminho": path}


def _media_controles(Y, controle, celula) -> np.ndarray:
    from cityomics.atlas.perturbacao import N_MESES

    nc = int(celula.max()) + 1
    cnt = np.bincount(celula[controle], minlength=nc).astype(float)
    S = np.zeros((nc, N_MESES))
    np.add.at(S, celula[controle], Y[controle])
    return S / np.where(cnt > 0, cnt, np.nan)[:, None]


def evento_estudo(seg, lote_seg, Y: dict, n_boot: int = 200, log=print) -> dict:
    from cityomics.atlas.perturbacao import COORTE, GRUPOS, N_MESES, _mes, estabelecimentos, tratamento

    est = estabelecimentos(log=log)
    Yt = sum(Y.values()).astype(float)
    celula = pd.factorize(seg["cd_dist"].astype(str) + "|" + seg["classe"].astype(str))[0]
    dist = seg["cd_dist"].to_numpy()
    publicado = json.loads((guard.pre2026(out_dir().parent / "perturbacao" / "evento_estudo.json")).read_text())
    rng = np.random.default_rng(51)
    rep = {}
    for nome, (grupo, marco, filtro) in GRUPOS.items():
        coorte, controle = tratamento(est, lote_seg, len(seg), grupo, marco, filtro)
        C = _media_controles(Yt, controle, celula)
        tr = np.where(coorte >= 0)[0]
        r = att_vec(Yt, coorte, celula, C, tr)
        com_ctrl = tr[~np.isnan(C[celula[tr], 0])]
        # eventos do grupo em cada segmento tratado: repetições depois do primeiro evento limpo
        col = "data_inicio" if marco == "inicio" else "data_fim"
        e = est.filter(pl.col("grupo") == grupo).join(lote_seg, on="sql_base", how="inner")
        if filtro == "estrito":
            e = e.filter(~pl.col("mei") & pl.col("lote_comercial"))
        m = _mes(e[col])
        sg = e["seg"].to_numpy()
        okm = (m >= 0) & (m < N_MESES)
        g_ev = coorte[sg[okm]]
        rel = m[okm] - g_ev
        tratado = g_ev >= 0
        mesmo_mes = np.bincount(sg[okm][tratado & (rel == 0)], minlength=len(seg))[com_ctrl]
        depois = np.bincount(sg[okm][tratado & (rel >= 1) & (rel <= 11)], minlength=len(seg))[com_ctrl]
        anos = (coorte[com_ctrl] // 12) + 2022
        sem = (coorte[com_ctrl] % 12) // 6
        r_rel = []
        dd = np.unique(dist[com_ctrl], return_inverse=True)
        grupos_d = [com_ctrl[dd[1] == k] for k in range(len(dd[0]))]
        for _ in range(n_boot):
            idx = np.concatenate([grupos_d[k] for k in rng.integers(0, len(grupos_d), len(grupos_d))])
            b = att_vec(Yt, coorte, celula, C, idx)
            r_rel.append((b["pre"], b["efeito"], b["efeito"] / b["base"], b["pre"] / b["base"]))
        r_rel = np.asarray(r_rel)
        pub = publicado.get(nome, {})
        ic_pub = [v / pub["base"] for v in pub["ic_efeito"]] if pub else None
        rep[nome] = {
            "grupo": grupo, "marco": marco, "filtro": filtro,
            "tratados_limpos": int(len(tr)), "tratados_com_controle": r["n"], "controles": int(controle.sum()),
            "celulas_distrito_classe_com_tratado": int(len(np.unique(celula[com_ctrl]))),
            "coortes_por_ano": {str(int(a)): int(v) for a, v in zip(*np.unique(anos, return_counts=True))},
            "coortes_por_semestre": {f"{int(a)}S{int(s) + 1}": int(((anos == a) & (sem == s)).sum()) for a in (2023, 2024) for s in (0, 1)},
            "eventos_mesmo_mes_media": float(mesmo_mes.mean()), "parte_com_outro_evento_no_mes_0": float(np.mean(mesmo_mes > 1)),
            "parte_com_repeticao_meses_1_11": float(np.mean(depois > 0)), "repeticoes_meses_1_11_media": float(depois.mean()),
            "base": r["base"], "pre": r["pre"], "efeito": r["efeito"], "efeito_rel": r["efeito"] / r["base"],
            "ic_pre": _ic(r_rel[:, 0]), "ic_efeito": _ic(r_rel[:, 1]), "ic_efeito_rel": _ic(r_rel[:, 2]),
            "ic90_efeito_rel": _ic(r_rel[:, 2], (5, 95)), "ic_pre_rel": _ic(r_rel[:, 3]),
            "meia_largura_rel": float((np.percentile(r_rel[:, 2], 97.5) - np.percentile(r_rel[:, 2], 2.5)) / 2),
            "publicado": {"n": pub.get("n"), "base": pub.get("base"), "efeito_rel": pub.get("efeito_relativo"), "ic_efeito_rel": ic_pub,
                          "ic_pre_rel": [v / pub["base"] for v in pub["ic_pre"]] if pub else None},
        }
        for lim in (-0.10, -0.14):
            rep[nome][f"exclui_{int(round(-lim * 100))}pct"] = {
                "recalculado": bool(rep[nome]["ic_efeito_rel"][0] > lim), "publicado": bool(ic_pub[0] > lim) if ic_pub else None}
        log(f"{nome}: {len(tr):,} limpos, {r['n']:,} com controle; efeito {r['efeito'] / r['base']:+.1%} "
            f"{np.round(rep[nome]['ic_efeito_rel'], 3)}; publicado {np.round(ic_pub, 3) if ic_pub else None}")
    rep["coorte_janela_meses"] = [int(COORTE[0]), int(COORTE[1])]
    rep["n_boot"] = n_boot
    return rep


# --- execução ---------------------------------------------------------------------------------------

def run(log=print, n_boot: int = 200, n_perm_bloco: int = 999, partes=("ruas", "pedestres", "relogio_blocos", "relogio_ic",
                                                                         "queda", "segmentos")) -> dict:
    path = out_dir() / SAIDA
    rep = json.loads(path.read_text()) if path.exists() else {}
    ids, E, names = setor_exposicao()
    rep["meta"] = {"distritos": int(ids["cd_dist"].n_unique()), "setores": int(ids.height), "classes": names,
                   "anos_relogio": list(ANOS), "data": pd.Timestamp.today().strftime("%Y-%m-%d")}
    Ec = None
    for parte in partes:
        t0 = time.time()
        if parte == "ruas":
            rep["ruas_setor"], Ec = sensibilidade_ruas(ids, E, names, ruas_setor_correto(), log=log)
        elif parte == "pedestres":
            if Ec is None:
                Ec = setor_exposicao_corrigida(ids, E, names, ruas_setor_correto())
            rep["pedestres"] = pedestres(ids, E, names, Ec=Ec, log=log)
        elif parte == "relogio_blocos":
            rep["relogio_blocos"] = relogio_blocos(ids, E, names, n_perm_bloco=n_perm_bloco, log=log)
        elif parte == "relogio_ic":
            rep["relogio_ic"] = relogio_ic(ids, E, names, n_boot=n_boot, log=log)
        elif parte == "queda":
            rep["queda_setores"] = queda_setores(ids, E, names, log=log)
        elif parte == "segmentos":
            seg, lote_seg, Y = segmentos_estrito(log=log)
            rep["queda_segmentos"] = queda_segmentos(Y)
            q = rep["queda_segmentos"]
            log(f"queda por segmento: top1% → {q['todos']['top1']['parte_queda']:.1%} (nulo {q['nulo_proporcional']['top1']['parte_queda_media']:.1%})")
            rep["evento_estudo"] = evento_estudo(seg, lote_seg, Y, n_boot=n_boot, log=log)
            del seg, lote_seg, Y
        log(f"[{parte}] {time.time() - t0:.0f}s")
        path.write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=float))
    return rep


if __name__ == "__main__":
    import sys

    run(partes=tuple(sys.argv[1:]) or ("ruas", "pedestres", "relogio_blocos", "relogio_ic", "queda", "segmentos"))
