"""Censo 2010 por setor e conversão para os setores de 2022 (spec-dados §3.2, Δ2010→2022).

O Censo 2010 usa outra malha (18.363 setores na capital, contra 27.301 em 2022). Para
comparar, as **contagens** de 2010 (população, domicílios, homens de 15 a 29 anos, cor ou raça,
analfabetos, renda total dos responsáveis) são redistribuídas para os setores de 2022 e só
depois viram taxas.

**Redistribuição dasimétrica.** Cada setor 2010 é cortado pelos limites de 2022; a contagem vai
para cada pedaço na proporção dos **endereços residenciais do CNEFE 2022** (espécie 1, domicílio
particular) que caem no pedaço; se o setor 2010 não tem endereço residencial, vale a proporção
da área. É melhor do que só a área, porque quadras vazias, parques e vias não recebem população.
O erro continua existindo onde a ocupação mudou muito entre 2010 e 2022 (loteamentos novos).

Saídas:
- ``data/interim/censo2010/censo2010_setor.parquet``: contagens por setor 2010;
- ``setor_censo2010_em_2022.parquet``: indicadores de 2010 na malha de 2022, com os mesmos nomes
  de ``setor_censo2022.parquet``;
- ``setor_censo_delta.parquet``: variações 2010→2022 (``d_`` = diferença de taxas, ``g_`` = log da razão)
  e ``renda_rel_2010``/``renda_rel_2022`` (renda do setor relativa à média da cidade, comparável
  apesar da inflação).
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pandas as pd
import polars as pl

from cityomics import external, geocode
from cityomics.paths import interim_dir, processed_dir

FTP = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/Agregados_por_Setores_Censitarios/"
URL_AGG = FTP + "SP_Capital_20260615.zip"
URL_MALHA = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
             "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2010/setores_censitarios_shp/sp/sp_setores_censitarios.zip")
BASE = "Base informaçoes setores2010 universo SP_Capital/CSV/"
CD_MUN = "3550308"


def _csv(z: zipfile.ZipFile, nome: str) -> pd.DataFrame:
    d = pd.read_csv(io.BytesIO(z.read(BASE + nome)), sep=";", encoding="latin-1", dtype=str)
    d["Cod_setor"] = d["Cod_setor"].str.strip()
    num = [c for c in d.columns if c[:1] == "V" and c[1:].isdigit()]
    d[num] = d[num].apply(lambda s: pd.to_numeric(s.str.replace(",", ".").str.strip(), errors="coerce"))
    return d.set_index("Cod_setor")


def _idade(d: pd.DataFrame, a0: int, a1: int) -> pd.Series:
    """Soma das idades a0..a1 (anos) nos arquivos Pessoa11/12/13: idade a ≥ 1 = coluna V(034+a)."""
    cols = [f"V{34 + a:03d}" for a in range(max(a0, 1), a1 + 1)]
    return d[cols].sum(axis=1, min_count=1)


def build_setor2010(log=print) -> pd.DataFrame:
    zpath = external.fetch(URL_AGG, "ibge", filename="censo2010_agregados_sp_capital.zip", log=log)
    z = zipfile.ZipFile(zpath)
    bas, p13, p11, p12 = _csv(z, "Basico_SP1.csv"), _csv(z, "pessoa13_sp1.csv"), _csv(z, "pessoa11_sp1.csv"), _csv(z, "pessoa12_sp1.csv")
    p3, p1 = _csv(z, "pessoa03_sp1.csv"), _csv(z, "pessoa01_sp1.csv")
    out = pd.DataFrame(index=bas.index)
    out["pop"] = p13["V001"]
    out["domicilios"] = bas["V001"]                    # particulares permanentes
    out["moradores_dpp"] = bas["V002"]
    out["homens"] = p11["V001"]
    out["mulheres"] = p12["V001"]
    out["pop_0_14"] = p13["V022"] + _idade(p13, 1, 14)    # V022 = menos de 1 ano
    out["pop_15_24"] = _idade(p13, 15, 24)
    out["pop_15_mais"] = out["pop"] - out["pop_0_14"]
    out["pop_60_mais"] = _idade(p13, 60, 99) + p13["V134"]  # idades simples até 99 (V133); V134 = 100 ou mais
    out["homens_15_29"] = _idade(p11, 15, 29)
    out["branca"], out["preta"], out["amarela"], out["parda"] = p3["V002"], p3["V003"], p3["V004"], p3["V005"]
    # alfabetizados com 15+ = alfabetizados 5+ menos 5 a 14 anos (V002..V011 = 5..14)
    alf15 = p1["V001"] - p1[[f"V{i:03d}" for i in range(2, 12)]].sum(axis=1)
    out["analfabetos_15"] = out["pop_15_mais"] - alf15
    # renda: Basico V005 = média dos responsáveis (com e sem rendimento); soma = média × domicílios
    out["renda_resp_soma"] = bas["V005"] * bas["V001"]       # média de todos os responsáveis × número deles
    log(f"Censo 2010: {len(out):,} setores, população {int(out['pop'].sum()):,}")
    dest = interim_dir() / "censo2010"
    dest.mkdir(parents=True, exist_ok=True)
    out.reset_index().to_parquet(dest / "censo2010_setor.parquet", index=False)
    return out


def malha2010():
    import geopandas as gpd

    path = external.fetch(URL_MALHA, "ibge", filename="censo2010_malha_setores_sp.zip")
    g = gpd.read_file(f"zip://{path}")
    col = next(c for c in g.columns if c.upper() in ("CD_GEOCODI", "CD_GEOCODIGO"))
    g = g.rename(columns={col: "setor2010"})[["setor2010", "geometry"]]
    g = g[g["setor2010"].str.startswith(CD_MUN)]
    return g.to_crs(31983)


def pesos(setores22, log=print) -> pd.DataFrame:
    """Tabela (setor2010, cd_setor, peso) com a fração de cada setor 2010 que vai para cada setor 2022."""
    import geopandas as gpd

    a = malha2010()
    a["geometry"] = a.geometry.buffer(0)
    b = setores22[["cd_setor", "geometry"]].copy()
    b["geometry"] = b.geometry.buffer(0)
    pieces = gpd.overlay(a, b, how="intersection", keep_geom_type=True)
    pieces["area"] = pieces.geometry.area
    pieces = pieces[pieces["area"] > 1].reset_index(drop=True)
    pieces["pid"] = pieces.index
    cn = pd.read_parquet(geocode.cnefe_path())
    cn = cn[cn["especie"] == 1]
    pts = gpd.GeoDataFrame(cn[["lat", "lon"]], geometry=gpd.points_from_xy(cn["lon"], cn["lat"]), crs="EPSG:4674").to_crs(31983)
    j = gpd.sjoin(pts, pieces[["pid", "geometry"]], how="inner", predicate="within")
    pieces["n_dom"] = j.groupby("pid").size().reindex(pieces["pid"]).fillna(0).to_numpy()
    tot_dom = pieces.groupby("setor2010")["n_dom"].transform("sum")
    tot_area = pieces.groupby("setor2010")["area"].transform("sum")
    pieces["peso"] = np.where(tot_dom > 0, pieces["n_dom"] / tot_dom.where(tot_dom > 0, 1), pieces["area"] / tot_area)
    log(f"pesos: {len(pieces):,} pedaços; setores 2010 sem endereço residencial (peso por área): {int((tot_dom.groupby(pieces['setor2010']).first() == 0).sum()) if False else int((pieces.groupby('setor2010')['n_dom'].sum() == 0).sum())}")
    return pieces[["setor2010", "cd_setor", "peso"]]


EXT = ["pop", "domicilios", "moradores_dpp", "homens", "mulheres", "pop_0_14", "pop_15_24", "pop_15_mais", "pop_60_mais",
       "homens_15_29", "branca", "preta", "amarela", "parda", "analfabetos_15", "renda_resp_soma"]


def em_2022(setores22, log=print) -> pl.DataFrame:
    s10 = build_setor2010(log=log)
    w = pesos(setores22, log=log)
    m = w.merge(s10.reset_index().rename(columns={"Cod_setor": "setor2010"}), on="setor2010", how="left")
    for c in EXT:
        m[c] = m[c] * m["peso"]
    agg = m.groupby("cd_setor")[EXT].sum(min_count=1).reset_index()
    um = agg.merge(setores22[["cd_setor", "geometry"]].assign(area_km2=lambda d: d.geometry.area / 1e6)[["cd_setor", "area_km2"]], on="cd_setor", how="right")
    # taxas só onde há população redistribuída suficiente (< 20 pessoas ou < 5 domicílios vira ausente)
    r = lambda n, d: um[n] / um[d].where(um[d] >= (5 if d == "domicilios" else 20))  # noqa: E731
    out = pd.DataFrame({
        "cd_setor": um["cd_setor"], "pop": um["pop"], "domicilios": um["domicilios"],
        "moradores_por_dom": r("moradores_dpp", "domicilios"),
        "frac_homens_15_29": r("homens_15_29", "pop"), "frac_15_24": r("pop_15_24", "pop"),
        "frac_0_14": r("pop_0_14", "pop"), "frac_60_mais": r("pop_60_mais", "pop"),
        "razao_sexo": r("homens", "mulheres"),
        "frac_branca": r("branca", "pop"), "frac_preta": r("preta", "pop"), "frac_parda": r("parda", "pop"),
        "frac_amarela": r("amarela", "pop"), "taxa_analfabetismo_15": r("analfabetos_15", "pop_15_mais"),
        "renda_media_resp": r("renda_resp_soma", "domicilios"),
        "dens_pop_km2": um["pop"] / um["area_km2"],
    })
    out["frac_negra"] = out["frac_preta"] + out["frac_parda"]
    dest = processed_dir() / "covariaveis"
    dest.mkdir(parents=True, exist_ok=True)
    out.to_parquet(dest / "setor_censo2010_em_2022.parquet", index=False)
    log(f"Censo 2010 em 2022: {len(out):,} setores, população {int(out['pop'].sum()):,} (original {int(s10['pop'].sum()):,})")
    return pl.from_pandas(out)


def delta(log=print) -> pl.DataFrame:
    c10 = pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2010_em_2022.parquet")
    c22 = pl.read_parquet(processed_dir() / "covariaveis" / "setor_censo2022.parquet")
    j = c22.select("cd_setor", "pop", "frac_homens_15_29", "frac_15_24", "frac_0_14", "frac_60_mais", "frac_negra",
                   "taxa_analfabetismo_15", "renda_media_resp", "moradores_por_dom", "dens_pop_km2") \
        .join(c10.select("cd_setor", "pop", "frac_homens_15_29", "frac_15_24", "frac_0_14", "frac_60_mais", "frac_negra",
                         "taxa_analfabetismo_15", "renda_media_resp", "moradores_por_dom", "dens_pop_km2"),
              on="cd_setor", how="left", suffix="_2010")
    d = [(pl.col(c) - pl.col(f"{c}_2010")).alias(f"d_{c}") for c in
         ("frac_homens_15_29", "frac_15_24", "frac_0_14", "frac_60_mais", "frac_negra", "taxa_analfabetismo_15", "moradores_por_dom")]
    g = [((pl.col(c) + 1).log() - (pl.col(f"{c}_2010") + 1).log()).alias(f"g_{c}") for c in ("pop", "dens_pop_km2")]
    m22 = c22["renda_media_resp"].mean()
    m10 = c10["renda_media_resp"].mean()
    rr = [(pl.col("renda_media_resp") / m22).alias("renda_rel_2022"), (pl.col("renda_media_resp_2010") / m10).alias("renda_rel_2010")]
    out = j.with_columns(d + g + rr).with_columns((pl.col("renda_rel_2022") - pl.col("renda_rel_2010")).alias("d_renda_rel"))
    out = out.select("cd_setor", *[c for c in out.columns if c.startswith(("d_", "g_", "renda_rel"))], pl.col("pop_2010"))
    out.write_parquet(processed_dir() / "covariaveis" / "setor_censo_delta.parquet")
    log(f"delta: {out.height:,} setores")
    return out
