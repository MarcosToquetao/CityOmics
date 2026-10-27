"""Ordem, cores e rótulos das classes de célula e dos tipos de crime (Figs. 3–6 e ED).

Os nomes em inglês vêm de ``cityomics.viz.names`` (um só lugar para todos os rótulos); aqui ficam só a
ordem das linhas e as cores, lidas dos dados (``tipos_perfil_2025.parquet``), sem nomes de tipo fixos.
"""

from __future__ import annotations

import polars as pl

from cityomics.atlas.genes_lote import atlas_dir
from cityomics.viz import names as N
from cityomics.viz import palette as P

FEN_EN = N.CRIME_EN
RUA_EN = {k: v for k, v in N.FIXED_LONG.items() if k.startswith(("rua_", "n_"))}
RUA_SHORT = {k: v for k, v in N.FIXED_SHORT.items() if k.startswith(("rua_", "n_"))}
ESTACAO_COR = {"n_trilho": "#7A7A7A", "n_terminal": "#B0B0B0"}
RUAS = ["rua_arterial_m", "rua_coletora_m", "rua_local_m"]
ESTACOES = ["n_trilho", "n_terminal"]


def classes():
    """Tipos (com favela e sem cadastro), famílias, chave de ordem, nomes longos e curtos em inglês."""
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    tipos = perfil["nome"].to_list() + ["Favela (FCU)", "Sem cadastro"]
    fam = perfil["familia"].to_list() + ["favela", "sem_cadastro"]
    key = (perfil["padrao_alto"] * 2 + perfil["pavimentos"] / 10).to_list() + [0.0, 0.0]
    longo, curto = N.class_labels(perfil)
    return tipos, fam, key, longo, curto


def ordem_linhas(com_estacoes: bool = True) -> list[str]:
    tipos, fam, key, _, _ = classes()
    o = P.ordered_types(tipos, fam, key) + RUAS
    return o + (ESTACOES if com_estacoes else [])


def cores() -> dict[str, str]:
    tipos, fam, key, _, _ = classes()
    return P.type_colors(tipos, fam, key) | P.RUAS | ESTACAO_COR


def tipo_por_familia(familia: str, criterio: str, maior: bool = True) -> str | None:
    """Tipo da família com o maior (ou menor) valor de um atributo do perfil médio (sem crime)."""
    p = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet").filter(pl.col("familia") == familia)
    if not p.height:
        return None
    return p.sort(criterio, descending=maior)["nome"][0]
