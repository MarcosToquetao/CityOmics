"""Genes do lote na referência de 2025 (spec-atlas §3.1; D22, D38, D51, D54, D56).

Cada lote fiscal é uma célula. Os genes são só atributos nativos do lote:

- **IPTU 2025** (``data/interim/iptu/iptu_lote_2025.parquet``): unidades, áreas, pavimentos,
  idade, valores do m², frações de uso e de padrão; e, do cadastro bruto, a **testada** (frente
  para a rua, a exposição usada na atribuição, D51) e o número de frentes (lote de esquina).
- **CNPJ ativo no snapshot de 2025-12** (D56), contado por grupo de CNAE. A ligação ao lote é
  pelo endereço do IPTU (CEP + número → SQL → lote). Estabelecimentos sem par ficam fora dos
  genes do lote (continuam nas covariáveis do setor).
- **MEI** (tabela do Simples do mesmo snapshot): contado à parte, como gene próprio. É dado de
  pessoa física no endereço de casa: nunca sai da máquina nem entra no objeto público (D60).

As favelas não têm lote fiscal: entram como pseudo-células FCU em ``atlas/spots.py`` (D54).
Nada de 2026 é lido aqui (``guard.pre2026``).

Saídas (locais, fora do git):
- ``data/processed/atlas/lote_genes_2025.parquet``: um lote por linha;
- ``data/processed/atlas/cnpj_ligacao_2025.json``: taxas de ligação (relatório agregado).
"""

from __future__ import annotations

import json
import subprocess
import zipfile

import numpy as np
import polars as pl

from cityomics import external
from cityomics.atlas.guard import pre2026
from cityomics.covariates import cnpj, iptu
from cityomics.paths import interim_dir, processed_dir

REF_YEAR = 2025
CNPJ_SNAPSHOT = "2025-12"
GRUPOS = list(cnpj.GRUPOS) + ["outros_servicos"]
SIMPLES_COLS = ["cnpj_basico", "opcao_simples", "data_opcao_simples", "data_exclusao_simples",
                "opcao_mei", "data_opcao_mei", "data_exclusao_mei"]


def atlas_dir():
    d = processed_dir() / "atlas"
    d.mkdir(parents=True, exist_ok=True)
    return d


def lot_table() -> pl.DataFrame:
    """Atributos dos lotes sem a geometria (leitura rápida)."""
    import pyarrow.parquet as pq

    cols = ["sql_base", "origem", "setor_fiscal", "quadra_fiscal", "condominio", "cd_setor", "cd_dist", "area_m2"]
    return pl.from_arrow(pq.read_table(processed_dir() / "units" / "lotes.parquet", columns=cols))


def _digits(col: str) -> pl.Expr:
    return pl.col(col).str.replace_all(r"\D", "")


def _numero(col: str) -> pl.Expr:
    return _digits(col).str.strip_chars_start("0")


def iptu_frente_endereco(lots: pl.DataFrame, year: int = REF_YEAR) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Testada e frentes por lote, e a tabela de endereços (CEP + número → lote)."""
    pre2026(iptu.iptu_zip(year))
    raw = iptu.read_year(year, extra=True)
    condo = iptu.condo_lookup_from(lots.filter(pl.col("origem") == "lote_fiscal").to_pandas())
    df = iptu.lot_keys(raw, condo).filter(pl.col("sql_base").is_not_null())
    frente = df.group_by("sql_base").agg(pl.col("testada").max(), pl.col("frentes").max())
    end = (df.select(_digits("cep").alias("cep"), _numero("numero").alias("numero"), "sql_base")
           .filter((pl.col("cep").str.len_chars() == 8) & (pl.col("numero").str.len_chars() > 0)))
    # um endereço pode ter vários imóveis do mesmo lote (condomínio) ou, raramente, de lotes diferentes:
    # fica o lote com mais imóveis naquele endereço
    end = (end.group_by("cep", "numero", "sql_base").len()
           .sort("len", descending=True).unique(["cep", "numero"], keep="first").drop("len"))
    return frente, end


def simples_mei(basicos: pl.Series, mes: str = CNPJ_SNAPSHOT, log=print) -> pl.DataFrame:
    """CNPJs básicos com opção pelo MEI vigente no snapshot."""
    zpath = pre2026(external.external_dir() / "cnpj" / f"{mes}_Simples.zip")
    tmp = interim_dir() / "cnpj" / f"simples_{mes}.csv"
    if not tmp.exists():
        with zipfile.ZipFile(zpath) as z:
            inner = z.namelist()[0]
        with open(tmp, "wb") as fo:
            subprocess.run(["unzip", "-p", str(zpath), inner], stdout=fo, check=True)
    lf = pl.scan_csv(tmp, separator=";", has_header=False, new_columns=SIMPLES_COLS, infer_schema=False,
                     encoding="utf8-lossy", quote_char='"')
    want = pl.DataFrame({"cnpj_basico": basicos.unique()}).lazy()
    out = (lf.join(want, on="cnpj_basico", how="inner")
           .with_columns(pl.col("data_exclusao_mei").str.replace_all(r"\D", "").alias("excl"))
           .select("cnpj_basico",
                   ((pl.col("opcao_mei") == "S") & (pl.col("excl").is_null() | (pl.col("excl").str.strip_chars("0") == "")))
                   .alias("mei"))
           .collect())
    tmp.unlink()
    log(f"Simples: {out.height:,} básicos de SP; MEI vigente em {out['mei'].sum():,}")
    return out


def cnpj_lote(end: pl.DataFrame, mes: str = CNPJ_SNAPSHOT, log=print) -> tuple[pl.DataFrame, dict]:
    """Estabelecimentos ativos no snapshot, ligados ao lote pelo endereço."""
    for i in range(cnpj.N_PARTES):
        pre2026(external.external_dir() / "cnpj" / f"{mes}_Estabelecimentos{i}.zip")
    est = cnpj.parse(log=log, mes=mes)
    ativos = est.filter(pl.col("situacao") == "02").with_columns(
        _digits("cep").alias("cep"), _numero("numero").alias("numero"),
        pl.col("id_estab").str.slice(0, 8).alias("cnpj_basico"))
    mei = simples_mei(ativos["cnpj_basico"], mes=mes, log=log)
    ativos = ativos.join(mei, on="cnpj_basico", how="left").with_columns(pl.col("mei").fill_null(False))
    lig = ativos.join(end, on=["cep", "numero"], how="left")
    rep = {"snapshot": mes, "ativos": ativos.height, "ligados_ao_lote": int(lig["sql_base"].is_not_null().sum()),
           "mei": int(ativos["mei"].sum()),
           "taxa_ligacao": float(lig["sql_base"].is_not_null().mean()),
           "taxa_ligacao_nao_mei": float(lig.filter(~pl.col("mei"))["sql_base"].is_not_null().mean())}
    log(f"CNPJ {mes}: {rep['ativos']:,} ativos; {rep['taxa_ligacao']:.1%} ligados a um lote pelo endereço")
    return lig.filter(pl.col("sql_base").is_not_null()), rep


def gene_matrix(lots: pl.DataFrame, iptu_lote: pl.DataFrame, frente: pl.DataFrame, est: pl.DataFrame | None) -> pl.DataFrame:
    """Uma linha por lote fiscal com os genes brutos (sem padronizar)."""
    g = (lots.filter(pl.col("origem") == "lote_fiscal")
         .join(iptu_lote.drop("ano", strict=False), on="sql_base", how="left")
         .join(frente, on="sql_base", how="left"))
    g = g.with_columns(
        (REF_YEAR - pl.col("ano_construcao")).clip(0, 150).alias("idade"),
        (pl.col("area_construida") / pl.col("area_terreno")).clip(0, 50).alias("aproveitamento"),
        (pl.col("frentes") >= 2).cast(pl.Float64).alias("esquina"),
        pl.col("n_unidades").is_not_null().alias("tem_iptu"),
    )
    if est is not None:
        cnt = (est.with_columns(pl.when(pl.col("mei")).then(pl.lit("mei")).otherwise(pl.col("grupo")).alias("g"))
               .group_by("sql_base", "g").len().pivot(on="g", index="sql_base", values="len"))
        cnt = cnt.rename({c: f"cnpj_{c}" for c in cnt.columns if c != "sql_base"})
        g = g.join(cnt, on="sql_base", how="left")
        ccols = [c for c in g.columns if c.startswith("cnpj_")]
        g = g.with_columns([pl.col(c).fill_null(0) for c in ccols])
        nm = [c for c in ccols if c != "cnpj_mei"]
        g = g.with_columns(pl.sum_horizontal(nm).alias("cnpj_total"))
    return g


# genes que entram na tipagem e a transformação de cada um
LOG_GENES = ["area_terreno", "area_construida", "n_unidades", "pavimentos", "valor_m2_terreno", "valor_m2_construcao",
             "testada", "aproveitamento"]
FRAC_GENES = ["uso_residencial", "uso_comercio", "uso_servicos", "uso_industria", "uso_terreno",
              "padrao_baixo", "padrao_medio", "padrao_alto", "esquina"]
LIN_GENES = ["idade"]


def cnpj_genes(columns) -> list[str]:
    return [c for c in columns if c.startswith("cnpj_") and c != "cnpj_total"]


def build(log=print) -> pl.DataFrame:
    lots = lot_table()
    iptu_lote = pl.read_parquet(pre2026(interim_dir() / "iptu" / f"iptu_lote_{REF_YEAR}.parquet"))
    frente, end = iptu_frente_endereco(lots)
    log(f"IPTU {REF_YEAR}: testada em {frente.height:,} lotes; {end.height:,} endereços (CEP + número)")
    est, rep = None, {}
    try:
        est, rep = cnpj_lote(end, log=log)
    except FileNotFoundError as e:
        log(f"CNPJ {CNPJ_SNAPSHOT} indisponível ({e}); genes só do IPTU")
    g = gene_matrix(lots, iptu_lote, frente, est)
    g.write_parquet(atlas_dir() / f"lote_genes_{REF_YEAR}.parquet")
    rep |= {"lotes_fiscais": g.height, "com_iptu": int(g["tem_iptu"].sum()),
            "testada_mediana": float(np.nanmedian(g["testada"].to_numpy().astype(float)))}
    (atlas_dir() / f"cnpj_ligacao_{REF_YEAR}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2))
    return g
