"""Censo 2022: agregados por setor censitário (spec-dados §3.2).

Baixa os arquivos nacionais do IBGE (universo, renda do responsável, entorno), filtra os
setores da capital (código começando com 3550308) e guarda um Parquet por tema em
``data/interim/censo2022/``. As variáveis derivadas (taxas e proporções) ficam em
``derive``; os códigos ``V*`` estão nos dicionários oficiais, também baixados.

Células com valor suprimido pelo IBGE (setores pequenos) vêm como "X" e viram ausentes.
"""

from __future__ import annotations

import io
import zipfile

import polars as pl

from cityomics import external
from cityomics.paths import interim_dir

FTP = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
AGG = FTP + "Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/"
ENT = FTP + "Agregados_por_Setores_Censitarios_Caracteristicas_urbanisticas_do_entorno_dos_domicilios/"
TEMAS = {
    "basico": AGG + "Agregados_por_setores_basico_BR_20260520.zip",
    "demografia": AGG + "Agregados_por_setores_demografia_BR.zip",
    "cor_raca": AGG + "Agregados_por_setores_cor_ou_raca_BR.zip",
    "alfabetizacao": AGG + "Agregados_por_setores_alfabetizacao_BR.zip",
    "domicilio1": AGG + "Agregados_por_setores_caracteristicas_domicilio1_BR.zip",
    "domicilio2": AGG + "Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip",
    "domicilio3": AGG + "Agregados_por_setores_caracteristicas_domicilio3_BR_20250417.zip",
    "renda": FTP + "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/"
                   "Agregados_por_setores_renda_responsavel_BR_20260508_csv.zip",
    "entorno_domicilios": ENT + "Agregados_por_Setor_csv/Agregados_por_setores_entorno_domic%c3%adlios_BR.zip",
    "entorno_moradores": ENT + "Agregados_por_Setor_csv/Agregados_por_setores_entorno_moradores_BR.zip",
    "entorno_faces": ENT + "Agregados_por_Setor_csv/Agregados_por_setores_entorno_faces_BR.zip",
}
DICIONARIOS = [
    FTP + "Agregados_por_Setores_Censitarios/dicionario_de_dados_agregados_por_setores_censitarios_20260520.xlsx",
    FTP + "Agregados_por_Setores_Censitarios_Rendimento_do_Responsavel/dicionario_de_dados_renda_responsavel_20260508.xlsx",
    ENT + "dicionarios_de_dados_entorno.zip",
]
PREFIXO_SP = "3550308"


def censo_dir():
    d = interim_dir() / "censo2022"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_csv_bytes(raw: bytes) -> pl.DataFrame:
    for enc in ("utf-8", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    sep = ";" if text[:2000].count(";") > text[:2000].count(",") else ","
    return pl.read_csv(io.BytesIO(text.encode()), separator=sep, infer_schema=False, truncate_ragged_lines=True)


def extract_tema(tema: str, log=print) -> pl.DataFrame:
    path = external.fetch(TEMAS[tema], "ibge/censo2022", filename=f"{tema}.zip", log=log)
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.lower().endswith(".csv"):
                df = _read_csv_bytes(z.read(name))
                key = next(c for c in df.columns if "SETOR" in c.upper())
                frames.append(df.rename({key: "cd_setor"}).filter(pl.col("cd_setor").str.starts_with(PREFIXO_SP)))
    out = pl.concat(frames, how="diagonal_relaxed") if len(frames) > 1 else frames[0]
    var_cols = [c for c in out.columns if c.upper().startswith("V")]
    out = out.select(["cd_setor"] + var_cols).rename({c: c.upper() for c in var_cols})
    var_cols = [c.upper() for c in var_cols]
    out = out.with_columns(
        [pl.col(c).str.replace(",", ".").cast(pl.Float64, strict=False) for c in var_cols])
    out.write_parquet(censo_dir() / f"{tema}.parquet")
    log(f"censo {tema}: {out.height:,} setores × {len(var_cols)} variáveis")
    return out


def extract_all(log=print) -> None:
    for url in DICIONARIOS:
        external.fetch(url, "ibge/censo2022/dicionarios", log=log)
    for tema in TEMAS:
        extract_tema(tema, log=log)


def _load(tema: str) -> pl.DataFrame:
    return pl.read_parquet(censo_dir() / f"{tema}.parquet")


def _ratio(num, den) -> pl.Expr:
    return pl.when(den > 0).then(num / den).otherwise(None)


def derive(setores_area: pl.DataFrame | None = None) -> pl.DataFrame:
    """Indicadores por setor (proporções e taxas), a partir dos códigos dos dicionários oficiais.

    ``setores_area``: DataFrame com ``cd_setor`` e ``area_km2`` para a densidade.
    """
    c = pl.col
    df = _load("basico")
    for tema in ("demografia", "cor_raca", "alfabetizacao", "domicilio1", "domicilio2", "renda",
                 "entorno_faces"):
        df = df.join(_load(tema), on="cd_setor", how="left", suffix=f"_{tema}")

    # Supressão de células pequenas ("X"): se o setor tem total de moradores publicado, uma
    # contagem suprimida é um valor pequeno e vira 0. Setores inteiramente suprimidos seguem
    # ausentes. Não se aplica a médias e variâncias (renda, moradores por domicílio).
    counts = [col for col in df.columns if col.startswith("V") and col not in
              ("V0005", "V0006", "V06003", "V06004", "V06005", "V06006")]
    df = df.with_columns([pl.when(c("V01006").is_not_null()).then(c(col).fill_null(0)).otherwise(c(col))
                          .alias(col) for col in counts])
    morad = c("V01006")
    racas = c("V01317") + c("V01318") + c("V01319") + c("V01320") + c("V01321")
    dppo = c("V00001")
    out = df.select(
        "cd_setor",
        c("V0001").alias("pop"),
        c("V0002").alias("domicilios"),
        c("V0007").alias("dom_ocupados"),
        c("V0005").alias("moradores_por_dom"),
        _ratio(c("V0002") - c("V0007") - c("V0004").fill_null(0), c("V0002")).alias("frac_dom_nao_ocupados"),
        # idade e sexo (D12: homens jovens, rotina)
        _ratio(c("V01012") + c("V01013") + c("V01014"), morad).alias("frac_homens_15_29"),
        _ratio(c("V01034") + c("V01035"), morad).alias("frac_15_24"),
        _ratio(c("V01031") + c("V01032") + c("V01033"), morad).alias("frac_0_14"),
        _ratio(c("V01040") + c("V01041"), morad).alias("frac_60_mais"),
        _ratio(c("V01007"), c("V01008")).alias("razao_sexo"),
        # cor ou raça
        _ratio(c("V01317"), racas).alias("frac_branca"),
        _ratio(c("V01318"), racas).alias("frac_preta"),
        _ratio(c("V01320"), racas).alias("frac_parda"),
        _ratio(c("V01318") + c("V01320"), racas).alias("frac_negra"),
        _ratio(c("V01319"), racas).alias("frac_amarela"),
        # educação
        _ratio(c("V00901"), c("V00900") + c("V00901")).alias("taxa_analfabetismo_15"),
        # tipo de domicílio
        _ratio(c("V00049"), dppo).alias("frac_apartamento"),
        _ratio(c("V00047"), dppo).alias("frac_casa"),
        _ratio(c("V00048"), dppo).alias("frac_casa_vila_condominio"),
        _ratio(c("V00050"), dppo).alias("frac_cortico"),
        _ratio(c("V00052"), dppo).alias("frac_estrutura_degradada"),
        _ratio(c("V00002") * 1000, dppo).alias("improvisados_por_mil_dom"),
        # saneamento e condição do domicílio
        _ratio(c("V00111"), dppo).alias("frac_agua_rede"),
        _ratio(c("V00309") + c("V00310"), dppo).alias("frac_esgoto_rede"),
        _ratio(c("V00397") + c("V00398"), dppo).alias("frac_lixo_coletado"),
        _ratio(c("V00236") + c("V00238"), dppo).alias("frac_sem_banheiro_exclusivo"),
        _ratio(c("V00234") + c("V00235"), dppo).alias("frac_3_mais_banheiros"),
        # renda do responsável
        c("V06004").alias("renda_media_resp"),
        c("V06006").alias("renda_mediana_resp"),
        _ratio(c("V06005").sqrt(), c("V06004")).alias("cv_renda_resp"),
        # entorno (faces de quadra; CPTED)
        _ratio(c("V05412"), c("V05412") + c("V05413")).alias("frac_faces_iluminacao"),
        _ratio(c("V05406"), c("V05406") + c("V05407")).alias("frac_faces_pavimentadas"),
        _ratio(c("V05421"), c("V05421") + c("V05422")).alias("frac_faces_calcada"),
        _ratio(c("V05424"), c("V05424") + c("V05425")).alias("frac_faces_obstaculo_calcada"),
        _ratio(c("V05427"), c("V05427") + c("V05428")).alias("frac_faces_rampa"),
        _ratio(c("V05409"), c("V05409") + c("V05410")).alias("frac_faces_bueiro"),
        _ratio(c("V05415"), c("V05415") + c("V05416")).alias("frac_faces_ponto_onibus"),
        _ratio(c("V05432") + c("V05433"), c("V05430") + c("V05431") + c("V05432") + c("V05433"))
        .alias("frac_faces_3_mais_arvores"),
        _ratio(c("V05401"), c("V05400")).alias("frac_faces_onibus_caminhao"),
        _ratio(c("V05403"), c("V05400")).alias("frac_faces_so_pedestre"),
        c("V05400").alias("faces"),
    )
    if setores_area is not None:
        out = out.join(setores_area.select("cd_setor", "area_km2"), on="cd_setor", how="left").with_columns(
            _ratio(c("pop"), c("area_km2")).alias("dens_pop_km2"),
            _ratio(c("domicilios"), c("area_km2")).alias("dens_dom_km2"),
        ).drop("area_km2")
    return out
