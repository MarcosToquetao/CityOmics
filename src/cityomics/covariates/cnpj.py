"""CNPJ: estabelecimentos ativos por CNAE e setor, mês a mês (spec-dados §3.2, T2).

Fonte: dados abertos do CNPJ da Receita Federal (cadastro de estabelecimentos, pasta mensal
``2026-09``). Cada estabelecimento traz data de início da atividade, situação cadastral (ativa,
suspensa, inapta, baixada) com a data dessa situação, CNAE principal, CEP, logradouro e número.
Os arquivos nacionais (10 partes, ≈5,4 GB) são filtrados para o município de São Paulo (código
da Receita 7107) e só o recorte fica em ``data/interim/cnpj/``.

**Estoque mensal.** Um estabelecimento conta como ativo no mês M se começou até o fim de M e não
foi baixado, suspenso ou considerado inapto antes de M. Só há a situação *final* e a data dela,
então reativações e mudanças de endereço não aparecem: o endereço é o atual. Estabelecimentos que
mudaram de lugar ficam no ponto novo para toda a série. É o limite dessa fonte (declarar na F5).

**Geocodificação** pelo CNEFE (``cityomics.geocode``); só níveis ``numero`` e ``logradouro``
entram nos estoques por setor, o nível ``cep`` fica marcado.

**Grupos de CNAE** (divisão de 2 dígitos): bares e restaurantes, comércio varejista, bancos,
indústria, serviços e outros, ver ``GRUPOS``.

Saídas:
- ``data/interim/cnpj/estab_sp.parquet``: um estabelecimento por linha, sem nome fantasia, telefone nem e-mail;
- ``data/processed/covariaveis/setor_cnpj_mes.parquet``: setor × mês × grupo de CNAE, estoque de ativos,
  entradas e saídas do mês.
"""

from __future__ import annotations

import subprocess
import zipfile

import polars as pl

from cityomics import external, geocode
from cityomics.paths import interim_dir, processed_dir

BASE = "https://arquivos.receitafederal.gov.br/public.php/webdav"
TOKEN = "YggdBLfdninEJX9"  # token público da pasta de dados abertos (não é segredo)
MES = "2026-09"
N_PARTES = 10
MUN_SP = "7107"

COLS = ["cnpj_basico", "cnpj_ordem", "cnpj_dv", "matriz", "fantasia", "situacao", "data_situacao", "motivo",
        "cidade_ext", "pais", "data_inicio", "cnae", "cnae_sec", "tipo_log", "logradouro", "numero",
        "complemento", "bairro", "cep", "uf", "municipio", "ddd1", "tel1", "ddd2", "tel2", "ddd_fax", "fax", "email",
        "sit_especial", "data_sit_especial"]

# divisão CNAE (2 dígitos) → grupo
GRUPOS = {
    "bar_restaurante": {"56"},
    "comercio_varejista": {f"{d}" for d in range(47, 48)},
    "comercio_atacado": {"46", "45"},
    "financeiro": {"64", "65", "66"},
    "industria": {f"{d}" for d in range(10, 34)},
    "transporte_armazenagem": {"49", "50", "51", "52", "53"},
    "alojamento": {"55"},
    "educacao_saude": {"85", "86", "87", "88"},
    "construcao_imobiliario": {"41", "42", "43", "68"},
    "servicos_pessoais": {"96", "93", "94"},
}


def grupo_cnae(cnae: str | None) -> str:
    div = (cnae or "")[:2]
    for g, divs in GRUPOS.items():
        if div in divs:
            return g
    return "outros_servicos"


def auth():
    return (TOKEN, "")


def fetch_all(log=print):
    paths = []
    for i in range(N_PARTES):
        name = f"Estabelecimentos{i}.zip"
        paths.append(external.fetch(f"{BASE}/{MES}/{name}", "cnpj", filename=f"{MES}_{name}", log=log, auth=auth()))
    return paths


def _filtra_sp(zpath) -> bytes:
    """Linhas do município 7107 do zip (unzip | grep; o campo é o 21º, entre aspas)."""
    with zipfile.ZipFile(zpath) as z:
        inner = z.namelist()[0]
    p1 = subprocess.Popen(["unzip", "-p", str(zpath), inner], stdout=subprocess.PIPE)
    p2 = subprocess.run(["grep", "-a", f';"{MUN_SP}";'], stdin=p1.stdout, capture_output=True)
    p1.stdout.close()
    p1.wait()
    return p2.stdout


def parse(log=print, mes: str = MES) -> pl.DataFrame:
    frames = []
    for i in range(N_PARTES):
        zpath = external.external_dir() / "cnpj" / f"{mes}_Estabelecimentos{i}.zip"
        raw = _filtra_sp(zpath)
        if not raw:
            log(f"parte {i}: sem linhas de SP")
            continue
        # aspas soltas em complementos quebram o leitor com aspas: lê sem aspas e tira as aspas dos campos.
        # Linhas com ";" dentro de texto saem deslocadas e caem no filtro de município (perda desprezível).
        df = pl.read_csv(raw, separator=";", has_header=False, new_columns=COLS, infer_schema=False,
                         encoding="utf8-lossy", quote_char=None, truncate_ragged_lines=True)
        df = df.select(pl.all().str.strip_chars('"')).filter((pl.col("municipio") == MUN_SP) & (pl.col("uf") == "SP"))
        df = df.select(*[c for c in COLS if c not in ("fantasia", "ddd1", "tel1", "ddd2", "tel2", "ddd_fax", "fax", "email",
                                                        "sit_especial", "data_sit_especial", "cnae_sec", "complemento", "cidade_ext", "pais")])
        log(f"parte {i}: {df.height:,} estabelecimentos em SP")
        frames.append(df)
    df = pl.concat(frames)
    d = lambda c: pl.col(c).str.strptime(pl.Date, "%Y%m%d", strict=False)  # noqa: E731
    df = df.select(
        (pl.col("cnpj_basico") + pl.col("cnpj_ordem")).alias("id_estab"),
        "matriz", "situacao", d("data_situacao").alias("data_situacao"), d("data_inicio").alias("data_inicio"),
        "cnae", "cep",
        pl.concat_str([pl.col("tipo_log"), pl.col("logradouro")], separator=" ", ignore_nulls=True).alias("logradouro"),
        pl.col("numero"),
    ).with_columns(pl.col("cnae").map_elements(grupo_cnae, return_dtype=pl.String).alias("grupo"))
    return df


def build(setores, log=print) -> pl.DataFrame:
    import geopandas as gpd
    import pandas as pd

    from cityomics.units.setores import CRS

    est = parse(log=log)
    est = geocode.geocode(est.with_columns(pl.col("numero").str.replace_all(r"\D", "")))
    dest = interim_dir() / "cnpj"
    dest.mkdir(parents=True, exist_ok=True)
    ok = est.filter(pl.col("lat").is_not_null() & (pl.col("nivel") != "cep")).to_pandas()
    pts = gpd.GeoDataFrame(ok, geometry=gpd.points_from_xy(ok["lon"], ok["lat"]), crs="EPSG:4674").to_crs(CRS)
    j = gpd.sjoin(pts, setores[["cd_setor", "geometry"]].rename(columns={"cd_setor": "setor"}), how="inner", predicate="within")
    base = pl.from_pandas(j[["id_estab", "setor", "grupo", "situacao", "data_situacao", "data_inicio"]]).rename({"setor": "cd_setor"})
    log(f"CNPJ: {est.height:,} estabelecimentos; {est.filter(pl.col('nivel').is_in(['numero','logradouro'])).height:,} "
        f"com geocódigo fino; {base.height:,} em setores")
    est.drop("lat", "lon").write_parquet(dest / "estab_sp.parquet")

    # estado ativo: de data_inicio até data_situacao (se situação ≠ ativa "02")
    ativo_ate = pl.when(pl.col("situacao") == "02").then(None).otherwise(pl.col("data_situacao"))
    base = base.filter(pl.col("data_inicio").is_not_null()).with_columns(ativo_ate.alias("fim"))
    meses = pd.period_range("2015-01", "2026-09", freq="M")
    rows = []
    for m in meses:
        ini, fim_m = m.to_timestamp().date(), m.to_timestamp(how="end").date()
        ativos = base.filter((pl.col("data_inicio") <= fim_m) & (pl.col("fim").is_null() | (pl.col("fim") >= ini)))
        est_m = ativos.group_by("cd_setor", "grupo").agg(pl.len().alias("estoque"))
        ent = base.filter((pl.col("data_inicio") >= ini) & (pl.col("data_inicio") <= fim_m)).group_by("cd_setor", "grupo").agg(pl.len().alias("entradas"))
        sai = base.filter(pl.col("fim").is_not_null() & (pl.col("fim") >= ini) & (pl.col("fim") <= fim_m)).group_by("cd_setor", "grupo").agg(pl.len().alias("saidas"))
        t = est_m.join(ent, on=["cd_setor", "grupo"], how="full", coalesce=True).join(sai, on=["cd_setor", "grupo"], how="full", coalesce=True)
        rows.append(t.with_columns(pl.lit(str(m)).alias("mes")).fill_null(0))
    out = pl.concat(rows).select("cd_setor", "mes", "grupo", "estoque", "entradas", "saidas").sort("cd_setor", "mes", "grupo")
    d2 = processed_dir() / "covariaveis"
    d2.mkdir(parents=True, exist_ok=True)
    out.write_parquet(d2 / "setor_cnpj_mes.parquet")
    return out
