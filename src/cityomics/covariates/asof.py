"""Montagem as-of do painel setor × mês de covariáveis (spec-dados §3.3).

**Regra de disponibilidade.** A previsão do mês ``m`` é feita no início de ``m`` (D25, h=1).
Uma fonte com defasagem de publicação de ``L`` meses publica o mês ``s`` no fim de ``s + L``;
logo o mês ``s`` só pode alimentar a linha ``m`` se ``s + L < m``, isto é, ``s ≤ m − 1 − L``.
Com ``L = 0`` (fonte completa no fim do próprio mês) a linha ``m`` usa até ``m − 1``.

Implementação: cada série mensal é deslocada ``1 + L`` meses para a frente (``deslocar``) *antes*
de qualquer janela, de modo que somas e médias móveis só enxergam o passado disponível.
O calendário é determinístico e conhecido de antemão, então entra sem deslocamento.

Defasagens (``LAG``): ITBI 1, CNPJ 1, SP156 3, VIIRS 2, BCB 0 (fotografia: ver ``bcb.py``), clima 0.
IPTU entra via ``iptu.py``/F6 (emissão do ano corrente) e o Censo 2022 é estático (análise
retrospectiva declarada).

Saída: ``data/processed/covariaveis/painel_setor_mes.parquet`` (setor × mês, 2015-01 → 2027-03).
"""

from __future__ import annotations

import polars as pl

from cityomics.paths import interim_dir, processed_dir

LAG = {"itbi": 1, "cnpj": 1, "sp156": 3, "bcb": 0, "clima": 0, "viirs": 2}
JANELAS = (3, 6, 12)
MES_INI, MES_FIM = "2015-01", "2027-03"


def meses(ini: str = MES_INI, fim: str = MES_FIM) -> list[str]:
    import pandas as pd

    return [str(p) for p in pd.period_range(ini, fim, freq="M")]


def _idx(m: str) -> int:
    y, mm = m.split("-")
    return int(y) * 12 + int(mm) - 1


def _fmt(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def deslocar(df: pl.DataFrame, lag: int, mes_col: str = "mes") -> pl.DataFrame:
    """Faz o mês ``s`` aparecer na linha ``s + 1 + lag`` (fonte com defasagem ``lag``)."""
    idx = pl.col(mes_col).str.slice(0, 4).cast(pl.Int32) * 12 + pl.col(mes_col).str.slice(5, 2).cast(pl.Int32) - 1 + 1 + lag
    novo = pl.concat_str([(idx // 12).cast(pl.String).str.zfill(4), pl.lit("-"), (idx % 12 + 1).cast(pl.String).str.zfill(2)])
    return df.with_columns(novo.alias(mes_col))


def janelas(painel: pl.DataFrame, cols: list[str], chave: str, how: str = "sum", ws=JANELAS) -> pl.DataFrame:
    """Acrescenta ``<col>_s<w>`` (soma) ou ``_m<w>`` (média) das últimas ``w`` linhas de cada ``chave``.
    O painel deve ser denso (todos os meses) e ordenado; só olha para trás."""
    exprs = []
    for c in cols:
        for w in ws:
            r = pl.col(c).rolling_sum(w, min_samples=1) if how == "sum" else pl.col(c).rolling_mean(w, min_samples=1)
            exprs.append(r.over(chave).alias(f"{c}_{'s' if how == 'sum' else 'm'}{w}"))
    return painel.sort(chave, "mes").with_columns(exprs)


def yoy(painel: pl.DataFrame, cols: list[str], chave: str) -> pl.DataFrame:
    """Diferença para 12 linhas atrás (variação anual do estoque)."""
    return painel.sort(chave, "mes").with_columns(
        [(pl.col(c) - pl.col(c).shift(12).over(chave)).alias(f"{c}_yoy") for c in cols])


def grade(setores: list[str], ms: list[str]) -> pl.DataFrame:
    return pl.DataFrame({"cd_setor": setores}).join(pl.DataFrame({"mes": ms}), how="cross")


def _wide(df: pl.DataFrame, val: str, prefix: str) -> pl.DataFrame:
    w = df.pivot(on="grupo", index=["cd_setor", "mes"], values=val, aggregate_function="sum")
    return w.rename({c: f"{prefix}_{c}" for c in w.columns if c not in ("cd_setor", "mes")})


INTERP = ("pop", "frac_homens_15_29", "frac_negra", "taxa_analfabetismo_15", "renda_media_resp")


def _censo_interp(ms: list[str]) -> pl.DataFrame:
    """Valor anual de variáveis decenais: v(a) = v2010^(1−t) · v2022^t com t = (a − 2010)/12 (2010 ≤ a ≤ 2022);
    depois de 2022 vale o de 2022; antes de 2010, o de 2010. Uso retrospectivo declarado: o Censo 2022
    só saiu em 2023+, então para anos de treino a interpolação usa informação posterior (spec-dados §3.3)."""
    cov = processed_dir() / "covariaveis"
    a = pl.read_parquet(cov / "setor_censo2010_em_2022.parquet").select("cd_setor", *INTERP)
    b = pl.read_parquet(cov / "setor_censo2022.parquet").select("cd_setor", *INTERP)
    j = b.join(a, on="cd_setor", how="left", suffix="_10")
    anos = sorted({int(m[:4]) for m in ms})
    quadros = []
    for ano in anos:
        t = min(max((ano - 2010) / 12, 0.0), 1.0)
        ex = []
        for c in INTERP:
            v22, v10 = pl.col(c), pl.col(f"{c}_10")
            # log-linear exige positivos; com zero ou ausência em 2010 usa-se interpolação linear / valor de 2022
            logl = ((v10.clip(lower_bound=1e-9).log() * (1 - t)) + (v22.clip(lower_bound=1e-9).log() * t)).exp()
            lin = v10 * (1 - t) + v22 * t
            ex.append(pl.when((v10 > 0) & (v22 > 0)).then(logl).when(v10.is_not_null() & v22.is_not_null()).then(lin)
                      .otherwise(v22).alias(f"censo_interp_{c}"))
        quadros.append(j.select("cd_setor", *ex).with_columns(pl.lit(ano).alias("_ano")))
    anual = pl.concat(quadros)
    meses_df = pl.DataFrame({"mes": ms}).with_columns(pl.col("mes").str.slice(0, 4).cast(pl.Int32).alias("_ano"))
    return anual.join(meses_df, on="_ano").drop("_ano")


def build(setores: list[str], ms: list[str] | None = None, log=print) -> pl.DataFrame:
    """Painel setor × mês. ``setores`` = códigos da malha; ``ms`` = meses de ``MES_INI`` a ``MES_FIM``."""
    ms = ms or meses()
    g = grade(setores, ms)
    cov = processed_dir() / "covariaveis"

    # SP156: contagens por grupo, normalizadas pela cobertura de coordenadas do mês (cobertura_coord)
    sp = pl.read_parquet(interim_dir() / "sp156" / "sp156_setor_mes.parquet")
    cob = pl.read_parquet(interim_dir() / "sp156" / "sp156_cobertura_mes.parquet").select("mes", "cobertura_coord")
    sp = _wide(sp, "n", "sp156")
    sp = sp.join(cob, on="mes", how="left").with_columns(
        [(pl.col(c) / pl.col("cobertura_coord")).alias(c) for c in sp.columns if c.startswith("sp156_")]).drop("cobertura_coord")
    sp = deslocar(sp, LAG["sp156"])
    spc = [c for c in sp.columns if c.startswith("sp156_")]

    # ITBI: contagem e valor (somas), preço/m² mediano (média das medianas), fração financiada
    it = pl.read_parquet(interim_dir() / "itbi" / "itbi_setor_mes.parquet").with_columns(
        pl.col("mes").dt.strftime("%Y-%m")).select("cd_setor", "mes", "n_transacoes", "preco_m2_mediana", "frac_financiada")
    it = deslocar(it, LAG["itbi"])

    # BCB: estoque de agências (nível); CNPJ: estoque, entradas e saídas por grupo
    bcb = deslocar(pl.read_parquet(cov / "setor_bcb_mes.parquet"), LAG["bcb"])
    cn_path = cov / "setor_cnpj_mes.parquet"
    cn = None
    if cn_path.exists():
        c0 = pl.read_parquet(cn_path)
        cn = _wide(c0, "estoque", "cnpj_estoque").join(_wide(c0, "entradas", "cnpj_entradas"), on=["cd_setor", "mes"], how="full", coalesce=True) \
            .join(_wide(c0, "saidas", "cnpj_saidas"), on=["cd_setor", "mes"], how="full", coalesce=True)
        cn = deslocar(cn, LAG["cnpj"])

    p = g.join(sp, on=["cd_setor", "mes"], how="left").join(it, on=["cd_setor", "mes"], how="left") \
        .join(bcb, on=["cd_setor", "mes"], how="left")
    if cn is not None:
        p = p.join(cn, on=["cd_setor", "mes"], how="left")

    # ausência de registro = zero para contagens e fluxos; estoques herdam o último valor conhecido
    cont = spc + ["n_transacoes"] + ([c for c in cn.columns if c.startswith(("cnpj_entradas", "cnpj_saidas"))] if cn is not None else [])
    p = p.sort("cd_setor", "mes").with_columns([pl.col(c).fill_null(0) for c in cont])
    estoques = ["agencias_estoque"] + ([c for c in cn.columns if c.startswith("cnpj_estoque")] if cn is not None else [])
    p = p.with_columns([pl.col(c).forward_fill().over("cd_setor").fill_null(0) for c in estoques])
    medias = ["preco_m2_mediana", "frac_financiada"]
    vi_path = cov / "setor_viirs_mes.parquet"
    if vi_path.exists():
        vi = deslocar(pl.read_parquet(vi_path), LAG["viirs"])
        p = p.join(vi, on=["cd_setor", "mes"], how="left")
        medias.append("luz_noturna")
    p = janelas(p, cont, "cd_setor", "sum")
    p = janelas(p, medias, "cd_setor", "mean")
    p = yoy(p, estoques, "cd_setor")

    # calendário (sem defasagem) e clima (defasagem 0)
    cal = pl.read_parquet(cov / "calendario_mes.parquet").with_columns(pl.col("tem_decimo_terceiro").cast(pl.Int8))
    cli = deslocar(pl.read_parquet(cov / "clima_mes.parquet").drop("dias_com_dado"), LAG["clima"])
    p = p.join(cal, on="mes", how="left").join(cli, on="mes", how="left", suffix="_clima")

    # Censo 2010→2022: interpolação log-linear por ano até 2022; depois de 2022 fica o valor de 2022
    p = p.join(_censo_interp(ms), on=["cd_setor", "mes"], how="left")
    delta = pl.read_parquet(cov / "setor_censo_delta.parquet")
    p = p.join(delta.rename({c: f"censo_{c}" for c in delta.columns if c != "cd_setor"}), on="cd_setor", how="left")

    # estáticos
    for nome in ("censo2022", "ipvs", "infra", "osm"):
        s = pl.read_parquet(cov / f"setor_{nome}.parquet")
        p = p.join(s.rename({c: f"{nome}_{c}" for c in s.columns if c != "cd_setor"}), on="cd_setor", how="left")
    p = p.sort("cd_setor", "mes")
    dest = cov / "painel_setor_mes.parquet"
    p.write_parquet(dest)
    log(f"painel: {p.height:,} linhas × {p.width} colunas ({p['cd_setor'].n_unique():,} setores, {ms[0]} a {ms[-1]})")
    return p
