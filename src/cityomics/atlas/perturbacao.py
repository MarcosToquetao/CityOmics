"""Perturbação natural do tecido: evento-estudo de aberturas e fechamentos (piloto P4, docs/NARRATIVA.md).

Exploratório e de viabilidade (D40). Pergunta: quando um bar ou uma loja abre (ou um bar fecha) num
segmento de rua, o crime daquele segmento muda? É o análogo urbano da perturbação in situ.

- **Tratamento:** primeira abertura (ou fechamento) de estabelecimento do grupo no segmento entre
  2023-01 e 2024-12, sem outra no mesmo segmento nos 12 meses anteriores. Datas do CNPJ do snapshot
  de 2025-12 (D56), que inclui os estabelecimentos já baixados; o de 2026-09 não é lido (D55). O
  estabelecimento vai ao lote pelo endereço do IPTU (CEP + número, como em ``genes_lote``) e o lote
  ao segmento de rua mais próximo (até 40 m).
- **Controles:** segmentos sem nenhum evento do grupo em 2022–2025, no mesmo distrito e na mesma
  classe de rua.
- **Desfecho:** eventos geocodificados por segmento e mês (celular, roubo e furto a pessoa), ligados
  como na validação pontual (até 60 m; perto de estação ficam fora).
- **Estimador:** diferenças em diferenças por tempo de evento, com a base nos meses −12 a −7 de cada
  coorte e a tendência da célula de controle (distrito × classe de rua) subtraída, no espírito de
  Callaway–Sant'Anna com controles nunca tratados. Pré-tendência = média dos meses −6 a −1; efeito =
  média dos meses 0 a 11. Intervalos por bootstrap dos segmentos tratados agrupados por distrito (os
  controles, muito mais numerosos, ficam fixos).

Usa crime: só distritos fora do cofre espacial (D53); nada de 2026.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import polars as pl

from cityomics.atlas import guard
from cityomics.atlas.genes_lote import REF_YEAR, _digits, _numero, atlas_dir, iptu_frente_endereco, lot_table, simples_mei
from cityomics.paths import interim_dir

MES0 = pd.Period("2022-01", "M")
N_MESES = 48
COORTE = (12, 35)          # 2023-01 … 2024-12
BASE = (-12, -7)
PRE = (-6, -1)
POS = (0, 11)
# (grupo de CNAE, marco, filtro): "todos" usa qualquer CNPJ; "estrito" só não-MEI em lote com uso comercial ou de
# serviços no IPTU 2025, mais perto de uma porta aberta na rua do que um registro no cadastro
GRUPOS = {"abre_bar": ("bar_restaurante", "inicio", "todos"), "abre_varejo": ("comercio_varejista", "inicio", "todos"),
          "fecha_bar": ("bar_restaurante", "fim", "todos"),
          "abre_bar_estrito": ("bar_restaurante", "inicio", "estrito"), "abre_varejo_estrito": ("comercio_varejista", "inicio", "estrito"),
          "fecha_bar_estrito": ("bar_restaurante", "fim", "estrito")}
DESFECHOS = ("celular_roubo", "celular_furto", "roubo_outros", "furto_outros")
SNAPSHOT = "2025-12"


def out_dir():
    d = atlas_dir() / "perturbacao"
    d.mkdir(parents=True, exist_ok=True)
    return d


def estabelecimentos(log=print) -> pl.DataFrame:
    """CNPJ do snapshot de 2025-12 (todas as situações), com o lote pelo endereço. Cacheado."""
    from cityomics.covariates import cnpj

    path = out_dir() / f"estab_lote_{SNAPSHOT}.parquet"
    if path.exists() and "mei" in pl.read_parquet_schema(path):
        return pl.read_parquet(path)
    guard.pre2026(f"estab_{SNAPSHOT}")
    est = cnpj.parse(log=log, mes=SNAPSHOT)
    _, end = iptu_frente_endereco(lot_table())
    est = est.with_columns(_digits("cep").alias("cep"), _numero("numero").alias("numero"),
                           pl.col("id_estab").str.slice(0, 8).alias("cnpj_basico"))
    lig = est.join(end, on=["cep", "numero"], how="inner")
    mei = simples_mei(lig["cnpj_basico"], mes=SNAPSHOT, log=log)
    lig = lig.join(mei, on="cnpj_basico", how="left").with_columns(pl.col("mei").fill_null(False))
    uso = pl.read_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet", columns=["sql_base", "uso_comercio", "uso_servicos"])
    lig = lig.join(uso, on="sql_base", how="left").with_columns(
        ((pl.col("uso_comercio").fill_null(0) + pl.col("uso_servicos").fill_null(0)) > 0).alias("lote_comercial"))
    fim = pl.when(pl.col("situacao") == "02").then(None).otherwise(pl.col("data_situacao"))
    out = lig.select("sql_base", "grupo", "situacao", "data_inicio", fim.alias("data_fim"), "mei", "lote_comercial")
    out.write_parquet(path)
    log(f"CNPJ {SNAPSHOT}: {est.height:,} estabelecimentos; {out.height:,} ligados a um lote")
    return out


def _mes(d: pl.Series) -> np.ndarray:
    s = d.to_pandas()
    m = (s.dt.year - MES0.year) * 12 + (s.dt.month - MES0.month)
    return m.fillna(-999).astype(int).to_numpy()


def segmentos(log=print):
    """Segmentos de rua dos distritos de exploração, lotes → segmento e eventos → segmento × mês."""
    import geopandas as gpd
    from shapely import STRtree

    from cityomics.atlas.streets import stations
    from cityomics.units.setores import CRS

    seg = gpd.read_parquet(atlas_dir() / "ruas.parquet")
    seg["cd_dist"] = seg["cd_setor"].astype(str).str[:9]
    seg = seg[guard.explore_mask(seg["cd_dist"].to_numpy())].reset_index(drop=True)
    tree = STRtree(seg.geometry.values)
    cel = pl.read_parquet(atlas_dir() / f"celulas_{REF_YEAR}.parquet").filter(
        (pl.col("classe") == "lote") & pl.col("x").is_not_null())
    lp = gpd.points_from_xy(cel["x"], cel["y"])
    q = tree.query_nearest(lp, max_distance=40.0, return_distance=False)
    lote_seg = pl.DataFrame({"sql_base": cel["sql_base"].to_numpy()[q[0]], "seg": q[1]}).unique("sql_base", keep="first")

    ev = pl.read_parquet(interim_dir() / "eventos_multi_atribuidos.parquet",
                         columns=["desfecho", "data_fato", "coord_valida", "latitude", "longitude"])
    ev = ev.filter(pl.col("desfecho").is_in(list(DESFECHOS)) & pl.col("coord_valida"))
    pts = gpd.GeoSeries(gpd.points_from_xy(ev["longitude"], ev["latitude"]), crs="EPSG:4326").to_crs(CRS)
    st = stations()
    near = STRtree(st.geometry.values).query_nearest(pts.values, max_distance=100.0, return_distance=False)
    longe = np.ones(len(pts), bool)
    longe[near[0]] = False
    qe = tree.query_nearest(pts.values[longe], max_distance=60.0, return_distance=False)
    mes = _mes(ev["data_fato"])[longe][qe[0]]
    ok = (mes >= 0) & (mes < N_MESES)
    Y = np.zeros((len(seg), N_MESES), dtype=np.float32)
    np.add.at(Y, (qe[1][ok], mes[ok]), 1.0)
    log(f"segmentos de exploração: {len(seg):,}; lotes ligados: {lote_seg.height:,}; eventos ligados: {int(ok.sum()):,}")
    return seg, lote_seg, Y


def tratamento(est: pl.DataFrame, lote_seg: pl.DataFrame, n_seg: int, grupo: str, marco: str,
               filtro: str = "todos") -> tuple[np.ndarray, np.ndarray]:
    """Coorte (mês do primeiro evento limpo, −1 se não tratado) e marca de controle nunca tratado.

    O controle é o segmento sem nenhum evento do grupo (com qualquer filtro); o filtro "estrito" só
    restringe quais eventos tratam."""
    col = "data_inicio" if marco == "inicio" else "data_fim"
    e = est.filter(pl.col("grupo") == grupo).join(lote_seg, on="sql_base", how="inner")
    e = e.with_columns(pl.Series("mes", _mes(e[col])))
    e = e.filter((pl.col("mes") >= 0) & (pl.col("mes") < N_MESES))
    controle = np.ones(n_seg, bool)
    controle[e["seg"].unique().to_numpy()] = False
    if filtro == "estrito":
        e = e.filter(~pl.col("mei") & pl.col("lote_comercial"))
    seg_m = e.group_by("seg").agg(pl.col("mes").sort())
    coorte = np.full(n_seg, -1)
    for s, meses in zip(seg_m["seg"].to_list(), seg_m["mes"].to_list()):
        m = np.asarray(meses)
        alvo = m[(m >= COORTE[0]) & (m <= COORTE[1])]
        if len(alvo) and not np.any((m < alvo[0]) & (m >= alvo[0] - 12)):
            coorte[s] = alvo[0]
    return coorte, controle


def att(Y: np.ndarray, coorte: np.ndarray, controle: np.ndarray, celula: np.ndarray, idx: np.ndarray | None = None) -> dict:
    tr = np.where(coorte >= 0)[0] if idx is None else idx
    cel_ids = np.unique(celula)
    C = np.full((cel_ids.max() + 1, N_MESES), np.nan)
    for c in cel_ids:
        m = controle & (celula == c)
        if m.any():
            C[c] = Y[m].mean(axis=0)
    es = np.arange(PRE[0], POS[1] + 1)
    D = []
    base_tr = []
    for i in tr:
        g, c = coorte[i], celula[i]
        if np.isnan(C[c, 0]):
            continue
        b = slice(g + BASE[0], g + BASE[1] + 1)
        bt, bc = Y[i, b].mean(), C[c, b].mean()
        D.append([(Y[i, g + e] - bt) - (C[c, g + e] - bc) for e in es])
        base_tr.append(bt)
    D = np.asarray(D)
    path = D.mean(axis=0)
    pre = float(path[(es >= PRE[0]) & (es <= PRE[1])].mean())
    pos = float(path[(es >= POS[0]) & (es <= POS[1])].mean())
    return {"n": int(len(D)), "base": float(np.mean(base_tr)) if base_tr else float("nan"), "pre": pre, "efeito": pos,
            "caminho": dict(zip(es.tolist(), path.tolist()))}


def run(n_boot: int = 200, log=print) -> dict:
    est = estabelecimentos(log=log)
    seg, lote_seg, Y = segmentos(log=log)
    celula = pd.factorize(seg["cd_dist"].astype(str) + "|" + seg["classe"].astype(str))[0]
    dist = seg["cd_dist"].to_numpy()
    rng = np.random.default_rng(0)
    rep = {}
    for nome, (grupo, marco, filtro) in GRUPOS.items():
        coorte, controle = tratamento(est, lote_seg, len(seg), grupo, marco, filtro)
        r = att(Y, coorte, controle, celula)
        tr = np.where(coorte >= 0)[0]
        ud, inv = np.unique(dist[tr], return_inverse=True)
        grupos_d = [tr[inv == k] for k in range(len(ud))]
        bs_pre, bs_pos, bs_path = [], [], []
        for _ in range(n_boot):
            idx = np.concatenate([grupos_d[k] for k in rng.integers(0, len(ud), len(ud))])
            b = att(Y, coorte, controle, celula, idx=idx)
            bs_pre.append(b["pre"])
            bs_pos.append(b["efeito"])
            bs_path.append(list(b["caminho"].values()))
        r["ic_pre"] = np.percentile(bs_pre, [2.5, 97.5]).tolist()
        r["ic_efeito"] = np.percentile(bs_pos, [2.5, 97.5]).tolist()
        lo, hi = np.percentile(np.asarray(bs_path), [2.5, 97.5], axis=0)
        r["caminho_ic"] = {"lo": lo.tolist(), "hi": hi.tolist()}
        r["filtro"] = filtro
        se = float(np.std(bs_pos))
        r["efeito_relativo"] = r["efeito"] / r["base"] if r["base"] > 0 else None
        r["mde_relativo"] = 2.8 * se / r["base"] if r["base"] > 0 else None
        r["controles"] = int(controle.sum())
        r["gate_G3"] = bool(r["ic_pre"][0] <= 0 <= r["ic_pre"][1] and not (r["ic_efeito"][0] <= 0 <= r["ic_efeito"][1]))
        rep[nome] = r
        log(f"{nome}: {r['n']:,} segmentos tratados; base {r['base']:.3f}/mês; pré {r['pre']:+.3f} {np.round(r['ic_pre'], 3)}; "
            f"efeito {r['efeito']:+.3f} {np.round(r['ic_efeito'], 3)} (MDE relativo {r['mde_relativo']:.0%})")
    rep["desfechos"] = list(DESFECHOS)
    rep["n_boot"] = n_boot
    (out_dir() / "evento_estudo.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return rep
