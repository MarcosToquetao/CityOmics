"""F2: monta unidades, atribui eventos e produz os alvos agregados (spec-dados §2).

Saídas:
- ``data/processed/units/setores_2022.parquet`` e ``distritos.parquet``
- ``data/interim/eventos_{desfecho}_atribuidos.parquet`` (com coordenadas; não sobe ao Colab)
- ``data/processed/alvos/celular_setor_mes.parquet`` (n_geo, n_alocado, n_total por setor × mês)
- ``data/processed/alvos/letal_distrito_trimestre.parquet`` (composto e estrito)
"""

from __future__ import annotations

import pandas as pd

from cityomics.paths import interim_dir, processed_dir
from cityomics.units import assign, reconcile, setores as setores_mod, transit


def alvos_dir():
    d = processed_dir() / "alvos"
    d.mkdir(parents=True, exist_ok=True)
    return d


def run(log=print) -> dict:
    setores = setores_mod.build_setores(log=log)
    distritos = setores_mod.build_distritos(setores)
    log(f"setores: {len(setores):,} | distritos: {len(distritos)}")
    lookups = assign.build_lookups(log=log)

    report = {}
    for desfecho in ("celular", "letal"):
        ev = pd.read_parquet(interim_dir() / f"eventos_{desfecho}.parquet")
        ev = ev[ev["data_fato"] >= "2022-01-01"]
        at = assign.assign_events(ev, setores, lookups)
        at.to_parquet(interim_dir() / f"eventos_{desfecho}_atribuidos.parquet", index=False)
        report[desfecho] = at["via"].value_counts(normalize=True).round(4).to_dict()
        log(f"{desfecho}: atribuição {report[desfecho]}")

    cel = pd.read_parquet(interim_dir() / "eventos_celular_atribuidos.parquet")
    perto = transit.station_setores(setores, transit.load_stations(log=log))
    log(f"setores a até {transit.BUFFER_M} m de estação de metrô/trem: {len(perto):,}")
    alvo = reconcile.reconcile(cel, setores, freq="M", eligible={"trilhos": perto})
    alvo["periodo"] = alvo["periodo"].astype(str)
    alvo.to_parquet(alvos_dir() / "celular_setor_mes.parquet", index=False)

    let = pd.read_parquet(interim_dir() / "eventos_letal_atribuidos.parquet")
    comp = reconcile.district_totals(let, "Q").rename(columns={"n": "composto"})
    estr = reconcile.district_totals(let[let["estrito"]], "Q").rename(columns={"n": "estrito"})
    full = pd.MultiIndex.from_product([distritos["cd_dist"], sorted(comp["periodo"].unique())],
                                      names=["cd_dist", "periodo"])
    letal = (comp.set_index(["cd_dist", "periodo"]).join(estr.set_index(["cd_dist", "periodo"]), how="outer")
                 .reindex(full, fill_value=0).fillna(0).astype(int).reset_index())
    letal["periodo"] = letal["periodo"].astype(str)
    letal.to_parquet(alvos_dir() / "letal_distrito_trimestre.parquet", index=False)
    return report
