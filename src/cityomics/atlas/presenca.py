"""Pessoas presentes e pessoas na rua por setor × hora, e o risco por pessoa (P5, docs/NARRATIVA.md).

O "tamanho de biblioteca" do tecido: estações e comércio têm muito crime por km, mas também muita
gente. Fonte: microdados da Pesquisa Origem-Destino 2017 do Metrô (dia útil típico; coordenadas em
Córrego Alegre / UTM 23S, EPSG:22523; `data/external/od/OD-2017.zip`, sha256 no manifesto).

- **Presença (estoque):** a linha do tempo de cada pessoa começa na origem da primeira viagem (ou no
  domicílio, sem viagem), passa ao destino de cada viagem na chegada e fica lá até a saída seguinte.
  Em viagem, a pessoa não está em local de atividade. Peso: fator de expansão da pessoa (FE_PESS).
- **Rua (fluxo):** pessoas a pé no espaço público. Cada viagem soma os minutos andando na origem
  (ANDA_O, a partir da saída) e no destino (ANDA_D, até a chegada); nas viagens a pé ou de bicicleta,
  a duração toda, metade junto da origem e metade junto do destino. Peso: fator da viagem (FE_VIA).
- **Espaço:** pessoas-hora numa grade de 100 m, suavizadas por um núcleo gaussiano (σ = 300 m, a
  amostra é de domicílios) e somadas por setor; setores menores que uma célula usam a densidade do
  ponto representativo × área. Só o município de São Paulo.
- **Risco por pessoa:** o EM do Poisson linear com a exposição de cada setor multiplicada pela
  densidade de pessoas do período (presentes ou na rua, por km²): ``y_sp ~ Poisson(Σ_k E_sk·D_sp·ρ_kp)``.
  ρ é o crime por km de frente (ou por estação) por unidade de densidade de pessoas, comparável entre
  classes depois de descontar a multidão. Crime: roubo e furto de celular em dias úteis de 2024–2025,
  geocodificados, distritos de exploração (D53).
- **Relógio:** o perfil horário do roubo de celular de cada classe contra o perfil horário das pessoas
  na rua na mesma classe, e o risco por pessoa na rua hora a hora na cidade.

Ressalvas: a OD é de 2017 (antes da pandemia) e só de dias úteis; o crime é de 2024–2025.
Saídas em ``data/processed/atlas/presenca/``; as tabelas por setor ficam locais.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.attribution import em_fit_multi
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.external import external_dir
from cityomics.paths import interim_dir, processed_dir

OD_ZIP = "od/OD-2017.zip"
OD_DBF = "od/OD-2017/Banco de Dados-OD2017/OD_2017_v1.dbf"
OD_CRS = "EPSG:22523"
CRS = "EPSG:31983"
RES = 100.0
SIGMA_M = 300.0
MUNI_SP = 36
COLS = ["ID_PESS", "FE_PESS", "MUNI_DOM", "CO_DOM_X", "CO_DOM_Y", "N_VIAG", "FE_VIA", "CO_O_X", "CO_O_Y", "CO_D_X",
        "CO_D_Y", "H_SAIDA", "MIN_SAIDA", "H_CHEG", "MIN_CHEG", "ANDA_O", "ANDA_D", "TIPVG", "CD_ENTRE"]
PERIODOS = {"madrugada": range(0, 6), "manha": range(6, 12), "tarde": range(12, 18), "noite": range(18, 24)}
ANOS = (2024, 2025)


def out_dir():
    d = atlas_dir() / "presenca"
    d.mkdir(parents=True, exist_ok=True)
    return d


def read_od() -> pd.DataFrame:
    import pyogrio

    path = external_dir() / OD_DBF
    if not path.exists():
        import zipfile

        with zipfile.ZipFile(external_dir() / OD_ZIP) as z:
            z.extractall(external_dir() / "od")
    return pyogrio.read_dataframe(path, columns=COLS, read_geometry=False)


# --- linhas do tempo ----------------------------------------------------------------------------

def hour_overlap(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Horas de sobreposição de cada intervalo [a, b) (minutos, b pode passar de 1440) com cada uma
    das 24 horas de um dia típico; o que passa da meia-noite volta para o começo do dia."""
    a, b = np.asarray(a, float)[:, None], np.asarray(b, float)[:, None]
    h0 = np.arange(24)[None, :] * 60.0
    ov = np.clip(np.minimum(b, h0 + 60) - np.maximum(a, h0), 0, 60)
    ov += np.clip(np.minimum(b, h0 + 1500) - np.maximum(a, h0 + 1440), 0, 60)
    return ov / 60.0


def segments(od: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Segmentos de presença (x, y, início, fim, peso) e de rua (idem), em minutos do dia."""
    od = od.copy()
    trips = od[od["N_VIAG"].notna() & od["H_SAIDA"].notna() & od["H_CHEG"].notna()].sort_values(["ID_PESS", "N_VIAG"])
    dep = trips["H_SAIDA"] * 60 + trips["MIN_SAIDA"].fillna(0)
    arr = trips["H_CHEG"] * 60 + trips["MIN_CHEG"].fillna(0)
    arr = np.where(arr < dep, arr + 1440, arr)
    trips = trips.assign(dep=dep.to_numpy(), arr=arr)

    # presença: antes da 1ª viagem na origem; entre viagens no destino anterior; depois da última no destino
    g = trips.groupby("ID_PESS", sort=False)
    first, last = g.head(1), g.tail(1)
    pres = [pd.DataFrame({"x": first["CO_O_X"].fillna(first["CO_DOM_X"]), "y": first["CO_O_Y"].fillna(first["CO_DOM_Y"]),
                          "a": 0.0, "b": first["dep"], "w": first["FE_PESS"]})]
    nxt = g["dep"].shift(-1)
    mid = trips[nxt.notna()]
    pres.append(pd.DataFrame({"x": mid["CO_D_X"], "y": mid["CO_D_Y"], "a": mid["arr"], "b": nxt[nxt.notna()],
                              "w": mid["FE_PESS"]}))
    pres.append(pd.DataFrame({"x": last["CO_D_X"], "y": last["CO_D_Y"], "a": last["arr"], "b": 1440.0, "w": last["FE_PESS"]}))
    sem = od[od["N_VIAG"].isna()].drop_duplicates("ID_PESS")
    pres.append(pd.DataFrame({"x": sem["CO_DOM_X"], "y": sem["CO_DOM_Y"], "a": 0.0, "b": 1440.0, "w": sem["FE_PESS"]}))
    pres = pd.concat(pres, ignore_index=True)
    pres = pres[(pres["b"] > pres["a"]) & pres["x"].gt(0)]

    # rua: minutos andando na origem e no destino; viagem a pé ou de bicicleta, metade em cada ponta
    ativo = trips["TIPVG"].isin([3, 4])
    dur = trips["arr"] - trips["dep"]
    ao = np.where(ativo, dur / 2, trips["ANDA_O"].fillna(0))
    ad = np.where(ativo, dur / 2, trips["ANDA_D"].fillna(0))
    rua = pd.concat([
        pd.DataFrame({"x": trips["CO_O_X"], "y": trips["CO_O_Y"], "a": trips["dep"], "b": trips["dep"] + ao, "w": trips["FE_VIA"]}),
        pd.DataFrame({"x": trips["CO_D_X"], "y": trips["CO_D_Y"], "a": trips["arr"] - ad, "b": trips["arr"], "w": trips["FE_VIA"]}),
    ], ignore_index=True)
    rua = rua[(rua["b"] > rua["a"]) & rua["x"].gt(0)]
    return pres, rua


# --- espaço ------------------------------------------------------------------------------------

def _grid(bounds):
    x0, y0, x1, y1 = bounds
    return x0, y1, int(np.ceil((x1 - x0) / RES)), int(np.ceil((y1 - y0) / RES))


def to_setores(seg: pd.DataFrame, setores, log=print) -> np.ndarray:
    """Pessoas-hora por setor × hora (n_setores × 24), suavizadas na grade."""
    from pyproj import Transformer
    from rasterio import features
    from rasterio.transform import from_origin
    from scipy.ndimage import gaussian_filter

    tr = Transformer.from_crs(OD_CRS, CRS, always_xy=True)
    x, y = tr.transform(seg["x"].to_numpy(float), seg["y"].to_numpy(float))
    bounds = tuple(setores.total_bounds)
    gx0, gy1, nx, ny = _grid(bounds)
    ix = np.floor((x - gx0) / RES).astype(int)
    iy = np.floor((gy1 - y) / RES).astype(int)
    ok = (ix >= 0) & (ix < nx) & (iy >= 0) & (iy < ny)
    cell = iy[ok] * nx + ix[ok]
    W = hour_overlap(seg["a"].to_numpy()[ok], seg["b"].to_numpy()[ok]) * seg["w"].to_numpy()[ok, None]
    ids = features.rasterize(zip(setores.geometry.values, np.arange(1, len(setores) + 1)), out_shape=(ny, nx),
                             transform=from_origin(gx0, gy1, RES, RES), fill=0, dtype="int32").ravel()
    rp = setores.geometry.representative_point()
    rix = np.clip(np.floor((rp.x.to_numpy() - gx0) / RES).astype(int), 0, nx - 1)
    riy = np.clip(np.floor((gy1 - rp.y.to_numpy()) / RES).astype(int), 0, ny - 1)
    area_cells = setores.geometry.area.to_numpy() / RES ** 2
    n_cells = np.bincount(ids, minlength=len(setores) + 1)[1:]
    out = np.zeros((len(setores), 24))
    for h in range(24):
        G = np.bincount(cell, weights=W[:, h], minlength=nx * ny).reshape(ny, nx)
        Gs = gaussian_filter(G, SIGMA_M / RES, mode="constant")
        Gs *= G.sum() / max(Gs.sum(), 1e-12)
        soma = np.bincount(ids, weights=Gs.ravel(), minlength=len(setores) + 1)[1:]
        ponto = Gs[riy, rix] * area_cells
        out[:, h] = np.where(n_cells >= 1, soma, ponto)
    log(f"grade {nx}×{ny} de {RES:.0f} m; {ok.sum():,} segmentos dentro; pessoas-hora/dia: {out.sum():,.0f}")
    return out


def build(log=print) -> pl.DataFrame:
    from cityomics.units.setores import load_setores

    od = read_od()
    od = od[od["MUNI_DOM"].notna()]
    pres, rua = segments(od)
    setores = load_setores()
    P = to_setores(pres, setores, log=log)
    R = to_setores(rua, setores, log=log)
    ids = setores["cd_setor"].astype(str).to_numpy()
    out = pl.DataFrame({"cd_setor": np.repeat(ids, 24), "hora": np.tile(np.arange(24), len(ids)),
                        "presenca": P.ravel(), "rua": R.ravel()})
    out.write_parquet(out_dir() / "setor_presenca_hora.parquet")
    # total no município (pessoas presentes às 12h e pessoas-hora na rua por dia), para checar a escala
    log(f"presença às 3h: {P[:, 3].sum():,.0f} pessoas; às 15h: {P[:, 15].sum():,.0f}; "
        f"rua: {R.sum():,.0f} pessoas-hora/dia (pico às {int(np.argmax(R.sum(0)))}h)")
    return out


# --- risco por pessoa ---------------------------------------------------------------------------

def _crime(ids: pl.DataFrame, desfecho: str, anos=ANOS) -> pd.DataFrame:
    from cityomics.atlas.fenotipo import EVENTOS, periodo_do_dia

    ev = pd.read_parquet(interim_dir() / EVENTOS, columns=["desfecho", "data_fato", "hora_fato", "periodo", "cd_setor"])
    ev = ev[(ev["desfecho"] == desfecho) & ev["data_fato"].dt.year.isin(list(anos)) & ev["cd_setor"].notna()
            & (ev["data_fato"].dt.dayofweek < 5)].copy()
    pos = pd.Series(np.arange(ids.height), index=ids["cd_setor"].to_list())
    ev["i"] = ev["cd_setor"].astype(str).map(pos)
    ev = ev[ev["i"].notna()].copy()
    ev["i"] = ev["i"].astype(int)
    ev["per"] = periodo_do_dia(ev)
    ev["h"] = pd.to_datetime(ev["hora_fato"].astype("string"), format="%H:%M:%S", errors="coerce").dt.hour
    return ev


def _densidade(ids: pl.DataFrame, tab: pl.DataFrame, col: str) -> np.ndarray:
    """Pessoas por km² do setor, por hora (n × 24)."""
    from cityomics.atlas.spots import setores_attrs

    area = ids.join(setores_attrs().select("cd_setor", "area_km2"), on="cd_setor", how="left")["area_km2"].fill_null(0).to_numpy()
    w = tab.pivot(on="hora", index="cd_setor", values=col).fill_null(0.0)
    M = ids.select("cd_setor").join(w, on="cd_setor", how="left").fill_null(0.0).select([str(h) for h in range(24)]).to_numpy()
    return M / np.where(area > 0, area, np.nan)[:, None]


def analise(log=print) -> dict:
    from scipy.stats import spearmanr

    from cityomics.atlas.fenotipo import PERIODOS as PER_ORDEM
    from cityomics.atlas.fenotipo import setor_exposicao

    ids, E, names = setor_exposicao()
    tab = pl.read_parquet(out_dir() / "setor_presenca_hora.parquet")
    D = {c: np.nan_to_num(_densidade(ids, tab, c)) for c in ("presenca", "rua")}
    n = ids.height
    rows, rep = [], {"anos_crime": list(ANOS), "dias": "úteis", "od": "2017"}
    peso_km = E.sum(axis=0)
    for desfecho in ("celular_roubo", "celular_furto"):
        ev = _crime(ids, desfecho)
        ev = ev[ev["per"].notna()]
        p = ev["per"].map({q: j for j, q in enumerate(PER_ORDEM)}).to_numpy().astype(int)
        Y = np.bincount(ev["i"].to_numpy() * 4 + p, minlength=n * 4).reshape(n, 4).astype(float)
        lam = em_fit_multi(E, Y)
        res = {"eventos": int(len(ev))}
        for c in ("presenca", "rua"):
            rho = np.zeros_like(lam)
            dens_k = np.zeros_like(lam)
            for j, q in enumerate(PER_ORDEM):
                Dp = D[c][:, list(PERIODOS[q])].mean(axis=1)
                Dp = Dp / Dp[Dp > 0].mean()
                rho[:, j] = em_fit_multi(E * Dp[:, None], Y[:, [j]])[:, 0]
                dens_k[:, j] = (E * Dp[:, None]).sum(axis=0) / np.where(peso_km > 0, peso_km, np.nan)
            # estações têm taxa por unidade, não por km: ficam fora da ordem e entram pelo fator multidão
            tot_l, tot_r = lam.sum(axis=1), rho.sum(axis=1)
            km = np.array([not nm.startswith("n_") for nm in names])
            ok = (tot_l > 0) & (tot_r > 0) & km
            dens_tot = np.nansum(dens_k * lam, axis=1) / np.where(tot_l > 0, tot_l, np.nan)
            res[c] = {"spearman_km_vs_pessoa": float(spearmanr(tot_l[ok], tot_r[ok]).statistic),
                      "topo_km": [names[k] for k in np.argsort(-np.where(ok, tot_l, -1))[:5]],
                      "topo_pessoa": [names[k] for k in np.argsort(-np.where(ok, tot_r, -1))[:5]],
                      "fator_multidao": {nm: float(dens_tot[k]) for k, nm in enumerate(names) if tot_l[k] > 0}}
            for k, nm in enumerate(names):
                for j, q in enumerate(PER_ORDEM):
                    rows.append({"desfecho": desfecho, "exposicao": c, "classe": nm, "periodo": q, "lambda_km": float(lam[k, j]),
                                 "rho_pessoa": float(rho[k, j]), "densidade_relativa": float(dens_k[k, j])})
        rep[desfecho] = res
        log(f"{desfecho}: ρ(km × pessoa presente) = {res['presenca']['spearman_km_vs_pessoa']:.2f}; "
            f"(km × pessoa na rua) = {res['rua']['spearman_km_vs_pessoa']:.2f}; topo por pedestre: {res['rua']['topo_pessoa'][:3]}")
    pl.DataFrame(rows).write_parquet(out_dir() / "risco_por_pessoa.parquet")
    rep["relogio_vs_rua"] = _relogio_vs_rua(ids, E, names, D["rua"], log=log)
    (out_dir() / "presenca.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return rep


def _relogio_vs_rua(ids, E, names, Drua: np.ndarray, log=print) -> dict:
    """Perfil horário do roubo (hora exata, dias úteis) × perfil horário das pessoas na rua, por classe."""
    from cityomics.atlas.fenotipo import PESO_MIN, _contraste

    ev = _crime(ids, "celular_roubo")
    ev = ev[ev["h"].notna()]
    n = ids.height
    Y = np.bincount(ev["i"].to_numpy() * 24 + ev["h"].astype(int).to_numpy(), minlength=n * 24).reshape(n, 24).astype(float)
    lam = em_fit_multi(E, Y)
    _, Pc, w = _contraste(lam, E)
    fr = E.T @ Drua                                   # exposição × densidade de pedestres, classe × hora
    Pr = fr / np.where(fr.sum(1, keepdims=True) > 0, fr.sum(1, keepdims=True), 1.0)
    cor = {nm: float(np.corrcoef(Pc[k], Pr[k])[0, 1]) for k, nm in enumerate(names) if w[k] >= PESO_MIN}
    cidade_crime = Y.sum(0)
    cidade_rua = Drua.sum(0)
    risco = (cidade_crime / cidade_crime.sum()) / (cidade_rua / cidade_rua.sum())
    rows = [{"classe": nm, "peso": float(w[k]), **{f"crime_h{h:02d}": float(Pc[k, h]) for h in range(24)},
             **{f"rua_h{h:02d}": float(Pr[k, h]) for h in range(24)}} for k, nm in enumerate(names)]
    pl.DataFrame(rows).write_parquet(out_dir() / "relogio_vs_rua.parquet")
    pl.DataFrame({"hora": np.arange(24), "crime": cidade_crime, "rua": cidade_rua, "risco_relativo": risco}).write_parquet(
        out_dir() / "risco_hora_cidade.parquet")
    k_pop = names.index("Residencial horizontal popular") if "Residencial horizontal popular" in names else None
    out = {"eventos_hora_exata": int(len(ev)), "correlacao_por_classe": cor,
           "correlacao_mediana": float(np.median(list(cor.values()))),
           "risco_relativo_por_hora": risco.tolist(), "hora_maior_risco": int(np.argmax(risco)),
           "hora_menor_risco": int(np.argmin(risco))}
    if k_pop is not None:
        out["res_popular_4_6h"] = {"crime": float(Pc[k_pop, 4:6].sum()), "rua": float(Pr[k_pop, 4:6].sum())}
    log(f"relógio × rua: correlação mediana por classe = {out['correlacao_mediana']:.2f}; risco por pedestre "
        f"máximo às {out['hora_maior_risco']}h, mínimo às {out['hora_menor_risco']}h")
    return out


def run(log=print) -> dict:
    guard.pre2026(OD_ZIP)
    if not (out_dir() / "setor_presenca_hora.parquet").exists():
        build(log=log)
    return analise(log=log)
