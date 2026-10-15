"""SP156: pedidos dos cidadãos à Prefeitura, por distrito × mês × tema (spec-dados §3.2).

Cada linha é um protocolo com data de abertura, tema, assunto, serviço e o endereço onde o
serviço deve ser prestado (logradouro, número, CEP, subprefeitura, distrito), com latitude e
longitude, o que permite atribuir cada pedido direto ao setor. Pedidos de
iluminação, limpeza, entulho, veículos abandonados e árvores são sinais de desordem física,
com viés de denúncia: bairros com mais renda e conectividade reclamam mais. Entram como
covariável e como contexto, não como medida direta de desordem.

Saídas em ``data/interim/sp156/``:
- ``pedidos_<periodo>.parquet``: uma linha por protocolo (data, tema, assunto, serviço, grupo,
  coordenadas, distrito), sem logradouro, número nem texto livre;
- ``sp156_setor_mes.parquet``: contagens por setor 2022 × mês × grupo de assunto.
"""

from __future__ import annotations

import io
import re

import polars as pl
import requests

from cityomics import external
from cityomics.ingest.schema import norm_text
from cityomics.paths import interim_dir

CKAN = "https://dados.prefeitura.sp.gov.br/api/3/action/package_show?id=dados-do-sp156"
HEADERS = {"User-Agent": "Mozilla/5.0 (CityOmics research pipeline)"}

# Grupos de assunto (busca em tema + assunto + serviço, sem acento e em maiúsculas)
GRUPOS = {
    "iluminacao": r"ILUMINACAO|LAMPADA|POSTE|LUMINARIA",
    "limpeza_entulho": r"ENTULHO|LIMPEZA|VARRICAO|LIXO|RESIDUO|CACAMBA|CAPINA|BOCA DE LOBO",
    "veiculo_abandonado": r"VEICULO ABANDONADO|REMOCAO DE VEICULO|CARCACA|SUCATA",
    "arvore_poda": r"ARVORE|PODA|GALHO|VEGETACAO",
    "calcada_via": r"CALCADA|BURACO|PAVIMENT|TAPA-BURACO|VIA PUBLICA|LOGRADOURO",
    "comercio_irregular": r"AMBULANTE|COMERCIO IRREGULAR|FEIRA|ALVARA|PERTURBACAO DO SOSSEGO|RUIDO|BARULHO|POLUICAO SONORA",
    "imovel_abandonado": r"IMOVEL ABANDONADO|TERRENO|CORTICO|OCUPACAO|INVASAO",
    "pop_rua": r"SITUACAO DE RUA|MORADOR DE RUA|POPULACAO DE RUA|ABORDAGEM SOCIAL",
}


def sp156_dir():
    d = interim_dir() / "sp156"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_files() -> list[dict]:
    """Arquivos CSV de pedidos (exclui dicionários, avaliações dos canais e releases)."""
    r = requests.get(CKAN, headers=HEADERS, timeout=120)
    r.raise_for_status()
    out = []
    for res in r.json()["result"]["resources"]:
        name = (res.get("name") or "").strip()
        fmt = (res.get("format") or "").strip().lower().lstrip(".")
        if fmt != "csv" or not name.lower().startswith("dados do sp156"):
            continue
        m = re.search(r"(\d)\s*[ºo°]\s*(TRI|SEM)\s*(\d{4})", name, re.I)
        if not m:
            continue
        n, kind, year = int(m.group(1)), m.group(2).upper(), int(m.group(3))
        months = (3 * n - 2, 3 * n) if kind == "TRI" else (6 * n - 5, 6 * n)
        out.append({"label": f"{year}_{kind}{n}", "year": year, "m0": months[0], "m1": months[1],
                    "url": res["url"], "name": name})
    return sorted(out, key=lambda f: (f["year"], f["m0"]))


def fetch_all(years=None, log=print):
    paths = {}
    for f in list_files():
        if years and f["year"] not in years:
            continue
        paths[f["label"]] = external.fetch(f["url"], "sp156", filename=f"sp156_{f['label']}.csv", log=log)
    return paths


def _read_csv(path) -> pl.DataFrame:
    raw = path.read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sep = ";" if text[:5000].count(";") > text[:5000].count(",") else ","
    # sem aspas como delimitador: há endereços e serviços com aspas soltas (ex.: 2015-T1)
    return pl.read_csv(io.BytesIO(text.encode()), separator=sep, infer_schema=False, quote_char=None,
                       truncate_ragged_lines=True)


def _find(cols: list[str], *needles: str) -> str | None:
    for c in cols:
        n = norm_text(c)
        if all(x in n for x in needles):
            return c
    return None


def parse_file(label: str, path) -> pl.DataFrame:
    df = _read_csv(path)
    cols = df.columns
    sel = {
        "data_abertura": _find(cols, "DATA", "ABERTURA"),
        "tema": _find(cols, "TEMA"),
        "assunto": _find(cols, "ASSUNTO"),
        "servico": _find(cols, "SERVICO"),
        "cep": _find(cols, "CEP"),
        "subprefeitura": _find(cols, "SUBPREFEITURA"),
        "distrito": _find(cols, "DISTRITO"),
        "latitude": _find(cols, "LATITUDE"),
        "longitude": _find(cols, "LONGITUDE"),
        "status": _find(cols, "STATUS"),
    }
    keep = {k: v for k, v in sel.items() if v}
    out = df.select([pl.col(v).alias(k) for k, v in keep.items()])
    for k in sel:
        if k not in out.columns:
            out = out.with_columns(pl.lit(None, dtype=pl.String).alias(k))
    out = out.with_columns(
        pl.col("data_abertura").str.slice(0, 10).str.to_date(format="%d/%m/%Y", strict=False).alias("data"),
    )
    out = out.with_columns(pl.col("data").is_null().alias("_sem_data"))
    iso = pl.col("data_abertura").str.slice(0, 10).str.to_date(format="%Y-%m-%d", strict=False)
    out = out.with_columns(pl.when(pl.col("_sem_data")).then(iso).otherwise(pl.col("data")).alias("data")).drop("_sem_data")
    num = lambda c: pl.col(c).str.replace(",", ".").cast(pl.Float64, strict=False)  # noqa: E731
    out = out.with_columns(num("latitude"), num("longitude"))
    out = out.with_columns(grupo_expr().alias("grupo")).drop("data_abertura", "cep")
    out.write_parquet(sp156_dir() / f"pedidos_{label}.parquet")
    return out


def grupo_expr() -> pl.Expr:
    """Grupo de assunto de cada pedido (primeiro grupo cujo padrão aparece no texto)."""
    txt = (pl.col("tema").fill_null("") + " " + pl.col("assunto").fill_null("") + " " + pl.col("servico").fill_null(""))
    txt = txt.str.to_uppercase().str.replace_all("[ÁÀÂÃ]", "A").str.replace_all("[ÉÊ]", "E").str.replace_all("Í", "I")\
        .str.replace_all("[ÓÔÕ]", "O").str.replace_all("[ÚÜ]", "U").str.replace_all("Ç", "C")
    expr = pl.lit("outros")
    for nome, rx in reversed(list(GRUPOS.items())):
        expr = pl.when(txt.str.contains(rx)).then(pl.lit(nome)).otherwise(expr)
    return expr


def build_setor_mes(setores, ate: str = "2026-09-30", log=print) -> pl.DataFrame:
    """Atribui cada pedido ao setor 2022 (point-in-polygon) e agrega setor × mês × grupo.

    Pedidos com data posterior a ``ate`` (corte do snapshot) são erros de data e saem. Também grava
    ``sp156_cobertura_mes.parquet`` com o total de pedidos datados por mês e quantos têm coordenada,
    porque a cobertura de coordenadas varia no tempo (≈95% até 2019, ≈10% em 2021, 55–63% desde 2022).
    """
    import datetime as dt

    import geopandas as gpd
    import pandas as pd

    from cityomics.units.setores import CRS

    corte = dt.date.fromisoformat(ate)
    frames, cob = [], []
    for path in sorted(sp156_dir().glob("pedidos_*.parquet")):
        raw = pl.read_parquet(path).filter(pl.col("data").is_not_null() & (pl.col("data") <= corte))
        cob.append(raw.group_by(pl.col("data").dt.strftime("%Y-%m").alias("mes"))
                   .agg(pl.len().alias("n_pedidos"), pl.col("latitude").is_not_null().sum().alias("n_com_coord")))
        df = raw.filter(pl.col("latitude").is_not_null() & pl.col("data").is_not_null()
                                          & pl.col("latitude").is_between(-24.1, -23.3)
                                          & pl.col("longitude").is_between(-47.0, -46.3))
        if df.height == 0:
            continue
        pdf = df.select("latitude", "longitude", "data", "grupo").to_pandas()
        pts = gpd.GeoDataFrame(pdf, geometry=gpd.points_from_xy(pdf["longitude"], pdf["latitude"]), crs="EPSG:4674").to_crs(CRS)
        j = gpd.sjoin(pts, setores[["cd_setor", "geometry"]], how="inner", predicate="within")
        j["mes"] = pd.to_datetime(j["data"]).dt.to_period("M").astype(str)
        frames.append(pl.from_pandas(j.groupby(["cd_setor", "mes", "grupo"]).size().rename("n").reset_index()))
        log(f"{path.stem}: {raw.height:,} datados, {df.height:,} com coordenada, {len(j):,} em setores")
    out = pl.concat(frames).group_by("cd_setor", "mes", "grupo").agg(pl.col("n").sum()).sort("cd_setor", "mes", "grupo")
    out.write_parquet(sp156_dir() / "sp156_setor_mes.parquet")
    (pl.concat(cob).group_by("mes").agg(pl.col("n_pedidos").sum(), pl.col("n_com_coord").sum())
     .with_columns((pl.col("n_com_coord") / pl.col("n_pedidos")).alias("cobertura_coord")).sort("mes")
     .write_parquet(sp156_dir() / "sp156_cobertura_mes.parquet"))
    return out
