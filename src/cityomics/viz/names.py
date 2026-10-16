"""Nomes de exibição (inglês) dos tipos e domínios, derivados dos dados (sem crime)."""

from __future__ import annotations

import polars as pl

from cityomics.atlas.genes_lote import atlas_dir

RUA_EN = {"ruas arterial": "arterial streets", "ruas coletora": "collector streets", "ruas local": "local streets"}
SHORT = {"Low-rise residential, low standard": "low-rise (low)", "Low-rise residential, middle standard": "low-rise (mid)",
         "Low-rise residential, high standard": "low-rise (high)", "Mid/high-rise, residential and mixed": "high-rise",
         "Street retail, middle standard": "retail (mid)", "Street retail, low standard": "retail (low)", "Vacant land": "vacant",
         "Favelas": "favelas", "Unrecorded": "unrecorded", "Services and facilities": "services", "Industry and warehouses": "industry",
         "Low-rise mixed, wholesale": "wholesale mixed", "Mixed residential and commercial": "mixed res./retail",
         "Corner residential": "corner lots", "arterial streets": "arterials", "collector streets": "collectors", "local streets": "local streets"}


def type_en() -> dict[str, str]:
    p = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    return dict(zip(p["nome"].to_list(), p["name_en"].to_list())) | {"Favela (FCU)": "Favelas", "Sem cadastro": "Unrecorded"}


def domain_labels(short: bool = False) -> dict[int, str]:
    """N1…Nk com os elementos mais enriquecidos no domínio (tipos e classes de rua); o terceiro entra se o nome repetir."""
    import numpy as np

    en = type_en()
    comp = pl.read_parquet(atlas_dir() / "setor_composicao_2025.parquet")
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet").select("cd_setor", "dominio")
    cols = [c for c in comp.columns if c.startswith("e|") and c != "e|Sem cadastro"] + ["rua_arterial_m", "rua_coletora_m", "rua_local_m"]
    s = comp.join(dom, on="cd_setor").select("dominio", *cols)
    M = s.select(cols).to_numpy().astype(float)
    M = M / np.clip(M.sum(1, keepdims=True), 1e-9, None)
    lab = s["dominio"].to_numpy()
    city = M.mean(0)
    names = [en.get(c[2:], c[2:]) if c.startswith("e|") else RUA_EN["ruas " + c.split("_")[1]] for c in cols]
    out, used = {}, set()
    for k in sorted(set(lab)):
        enr = M[lab == k].mean(0) / np.clip(city, 1e-9, None)
        order = list(np.argsort(-enr))
        for n in (2, 3, 4):
            parts = [names[i] for i in order[:n]]
            parts = [SHORT.get(x, x) if short else x for x in parts]
            key = " + ".join(parts)
            if key not in used:
                break
        used.add(key)
        out[int(k)] = f"N{int(k) + 1} · {key}"
    return out
