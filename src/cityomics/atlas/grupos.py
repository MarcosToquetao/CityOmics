"""Grupos de classes de célula definidos pelos dados da tipagem (família e nome-base), sem nomes fixos.

As análises que comparam "habitação popular", "polos" ou "comércio" não podem depender de nomes de tipos de
uma tipagem específica: com a refação da tipagem (2026-10-20) os tipos mudam. Os grupos saem de
``tipos_perfil_2025.parquet``:

- ``popular``: tipos residenciais horizontais de padrão baixo (nome-base "Residencial horizontal popular",
  com ou sem qualificador);
- ``residencial``: famílias de habitação horizontal e de alto padrão, mais as favelas (``residencial_formal`` sem elas);
- ``comercio``: família comércio e misto;
- ``comercio_amplo``: comércio, prédios e serviços (o "domínio do comércio" do relógio sem modelo);
- ``polos``: comércio, serviços, estações e terminais (o glossário do artigo);
- ``estacoes``: estações de trilho e terminais de ônibus.
"""

from __future__ import annotations

import polars as pl

from cityomics.atlas.genes_lote import REF_YEAR, atlas_dir

FAVELA = "Favela (FCU)"
ESTACOES = ("n_trilho", "n_terminal")
BASE_POPULAR = "Residencial horizontal popular"


def perfil() -> pl.DataFrame:
    return pl.read_parquet(atlas_dir() / f"tipos_perfil_{REF_YEAR}.parquet")


def grupos(p: pl.DataFrame | None = None) -> dict[str, list[str]]:
    p = perfil() if p is None else p
    fam = dict(zip(p["nome"].to_list(), p["familia"].to_list()))
    de = lambda *fs: [n for n, f in fam.items() if f in fs]  # noqa: E731
    popular = [n for n in fam if n.startswith(BASE_POPULAR)]
    return {"popular": popular,
            "residencial": de("res_horizontal", "res_vertical_alto") + [FAVELA],
            "residencial_formal": de("res_horizontal", "res_vertical_alto"),
            "comercio": de("comercio"),
            "comercio_amplo": de("comercio", "res_vertical_medio", "servicos"),
            "polos": de("comercio", "servicos") + list(ESTACOES),
            "estacoes": list(ESTACOES)}


def indices(names: list[str], grupo: str, p: pl.DataFrame | None = None) -> list[int]:
    """Posições, em ``names`` (colunas da matriz de exposição), das classes de um grupo."""
    g = set(grupos(p)[grupo])
    return [i for i, n in enumerate(names) if n in g]
