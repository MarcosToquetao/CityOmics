"""Repontuação do benchmark de desenvolvimento com o CRPS corrigido para y real (2026-10-20).

O CRPS registrado (§5.3, emenda A6) com contagem reconciliada fracionária dava o CRPS de ⌈y⌉
(``scores.crps_nb_registrado``); ``scores.crps_nb`` agora integra a função de distribuição contra y real.
As previsões de 2025 gravadas por ``benchmark_run`` não mudam; só os escores e as estatísticas
derivadas. Este módulo:

- reescreve ``resultados`` em ``data/processed/modelo/resultados_benchmark_<tag>.json`` com o CRPS
  corrigido, guardando o anterior em ``crps_registrado`` e ``crps_nz_registrado``;
- refaz ``prereg/selection_<tag>.json`` (seleção, testes contra o melhor baseline e Holm), guardando a
  versão anterior em ``prereg/selection_<tag>_crps_registrado.json``;
- **não** altera ``prereg/selection.json``: trocar o modelo selecionado para o H1 é decisão do autor,
  na emenda A12 (``prereg/A12_DRAFT.md``).

Uso: ``python -m cityomics.models.repontua_crps``.
"""

from __future__ import annotations

import json
import shutil

import numpy as np
import pyarrow.parquet as pq
import polars as pl

from cityomics.eval import harness, scores
from cityomics.models import select_run
from cityomics.paths import REPO_ROOT, processed_dir


def resultados(tag: str = "dev", log=print) -> dict:
    d = processed_dir() / "modelo"
    caminho = d / f"resultados_benchmark_{tag}.json"
    res = json.loads(caminho.read_text())
    if any("crps_registrado" in v for v in res["resultados"].values()):
        log("resultados já repontuados; nada a fazer")
        return res
    t = pl.from_arrow(pq.read_table(d / "tabela_celular_2022_2025.parquet", columns=["cd_setor", "cd_dist"]))
    ev, mu, phi, _ = select_run.load(t, tag)
    y = ev["y"].to_numpy().astype("float64")
    nz = y >= 0.5
    for m, v in res["resultados"].items():
        c = scores.crps_nb(y, mu[m], phi[m])
        v["crps_registrado"], v["crps_nz_registrado"] = v["crps"], v["crps_nz"]
        v["crps"], v["crps_nz"] = float(c.mean()), float(c[nz].mean())
        log(f"{m}: CRPS {v['crps_registrado']:.4f} → {v['crps']:.4f}")
    res["nota_crps"] = ("2026-10-20: crps e crps_nz recalculados com scores.crps_nb corrigido (CRPS de y real); "
                        "os valores anteriores (CRPS de ⌈y⌉) ficam em *_registrado.")
    caminho.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    return res


def selecao(tag: str = "dev", log=print) -> dict:
    pre = REPO_ROOT / "prereg"
    sel_dev, sel = pre / f"selection_{tag}.json", pre / "selection.json"
    copia = pre / f"selection_{tag}_crps_registrado.json"
    if not copia.exists():
        shutil.copy2(sel_dev, copia)
    guarda = sel.read_bytes() if sel.exists() else None
    t = pl.from_arrow(pq.read_table(processed_dir() / "modelo" / "tabela_celular_2022_2025.parquet",
                                    columns=["cd_setor", "cd_dist"]))
    try:
        out = select_run.run(t, tag=tag, log=log)
    finally:
        if guarda is not None:
            sel.write_bytes(guarda)  # a seleção vigente para o H1 só muda por emenda do autor
    return out


def run(tag: str = "dev", log=print) -> dict:
    res = resultados(tag, log)
    out = selecao(tag, log)
    melhor = min((m for m in res["resultados"]), key=lambda m: res["resultados"][m]["crps"])
    log(f"melhor por CRPS corrigido: {melhor}; seleção: {out['selecao']}")
    return {"resultados": res, "selecao": out}


if __name__ == "__main__":
    run()
