"""Luz noturna (VIIRS Black Marble, Collection 2) por setor e mês (spec-dados §3.2, T1).

Fonte: NASA LAADS DAAC, produto **VNP46A3** (mensal, V2, grade de 15 segundos de arco ≈ 460 m,
tile ``h13v11`` cobre a cidade). O produto V2 (Collection 2) tem calibração consistente desde
2012 e deve ser usado em todos os anos (spec-dados §3.2). A busca de arquivos é pública (CMR);
o **download exige token da conta gratuita NASA Earthdata**, lido da variável de ambiente
``EARTHDATA_TOKEN`` (ver ``.env.example``) e nunca gravado em código nem em log.

Banda: ``AllAngle_Composite_Snow_Free`` (nW·cm⁻²·sr⁻¹, fator de escala 0,1), com os pixels de
qualidade ruim (banda ``..._Quality`` = 2, sem dado) como ausentes. Cada setor recebe o valor do
pixel que contém o seu ponto representativo: setores são menores do que o pixel, então a luz é uma
medida de vizinhança (~460 m), não do próprio setor.

Saída: ``data/processed/covariaveis/setor_viirs_mes.parquet`` (setor × mês, a partir de 2015-01).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl
import requests

from cityomics import external
from cityomics.paths import env_value, processed_dir

CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
TILE = "h13v11"
BBOX = "-46.9,-24.1,-46.2,-23.3"
BANDA = "AllAngle_Composite_Snow_Free"
FILL = 65535
PX = 240          # pixels por grau (15 segundos de arco)
H, V = 13, 11     # tile: lon0 = -180 + 10·h, lat0 = 90 − 10·v


def token() -> str:
    t = env_value("EARTHDATA_TOKEN")
    if not t:
        raise RuntimeError("EARTHDATA_TOKEN ausente: crie um token em urs.earthdata.nasa.gov (gratuito) e coloque no .env")
    return t


def list_granules(inicio: str = "2015-01-01", fim: str = "2026-12-31") -> list[dict]:
    out, page = [], 1
    while True:
        r = requests.get(CMR, params={"short_name": "VNP46A3", "version": "2", "bounding_box": BBOX,
                                      "temporal": f"{inicio}T00:00:00Z,{fim}T23:59:59Z", "page_size": 200,
                                      "page_num": page, "sort_key": "start_date"}, timeout=120)
        r.raise_for_status()
        ent = r.json()["feed"]["entry"]
        if not ent:
            break
        for g in ent:
            if TILE not in g["title"] and not any(TILE in l["href"] for l in g["links"]):
                continue
            href = next((l["href"] for l in g["links"] if l["href"].endswith(".h5") and TILE in l["href"]), None)
            if href:
                out.append({"mes": g["time_start"][:7], "url": href})
        page += 1
    return sorted({x["mes"]: x for x in out}.values(), key=lambda x: x["mes"])


def pixel_index(lat: np.ndarray, lon: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linha e coluna do pixel (tile h13v11, 2400×2400) que contém cada ponto."""
    lat0, lon0 = 90 - 10 * V, -180 + 10 * H
    row = np.floor((lat0 - lat) * PX).astype(int)
    col = np.floor((lon - lon0) * PX).astype(int)
    return row, col


def read_tile(path: Path) -> np.ndarray:
    """Matriz de radiância (nW/cm²/sr) com NaN nos pixels sem dado ou de má qualidade."""
    import h5py

    with h5py.File(path, "r") as f:
        found = {}

        def visit(name, obj):
            if hasattr(obj, "shape") and name.split("/")[-1] in (BANDA, BANDA + "_Quality"):
                found[name.split("/")[-1]] = obj

        f.visititems(visit)
        if BANDA not in found:
            raise KeyError(f"{BANDA} não encontrada em {path.name}")
        ds = found[BANDA]
        raw = ds[...].astype("float64")
        scale = float(np.ravel(ds.attrs.get("scale_factor", [0.1]))[0])
        bad = raw == FILL
        q = found.get(BANDA + "_Quality")
        if q is not None:
            bad |= q[...] == 2        # 2 = sem qualidade (preenchimento)
    raw[bad] = np.nan
    return raw * scale


def download(g: dict, tok: str) -> Path:
    """Baixa um mês (retomável: só grava o arquivo final quando completo)."""
    dest = external.external_dir() / "viirs" / f"VNP46A3_{g['mes']}_{TILE}.h5"
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(".part")
    with requests.get(g["url"], headers={"Authorization": f"Bearer {tok}"}, stream=True, timeout=(30, 600)) as r:
        r.raise_for_status()
        with part.open("wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    part.replace(dest)
    return dest


def download_all(gran: list[dict], tok: str, workers: int = 6, log=print) -> None:
    """Baixa os meses em paralelo: o servidor limita a velocidade por conexão."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    todo = [g for g in gran if not (external.external_dir() / "viirs" / f"VNP46A3_{g['mes']}_{TILE}.h5").exists()]
    log(f"VIIRS: {len(todo)} arquivos a baixar com {workers} conexões")
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(download, g, tok): g["mes"] for g in todo}
        for i, f in enumerate(as_completed(futs), 1):
            f.result()
            log(f"baixado {futs[f]} ({i}/{len(todo)})")


def build(setores, inicio: str = "2015-01-01", workers: int = 6, log=print) -> pl.DataFrame:
    """Baixa os meses (retomável, em paralelo) e extrai o valor por setor. ``setores``: GeoDataFrame com cd_setor."""
    tok = token()
    rep = setores.to_crs(4674).representative_point()
    row, col = pixel_index(rep.y.to_numpy(), rep.x.to_numpy())
    ok = (row >= 0) & (row < 2400) & (col >= 0) & (col < 2400)
    gran = list_granules(inicio)
    log(f"VIIRS: {len(gran)} meses de {gran[0]['mes']} a {gran[-1]['mes']}")
    download_all(gran, tok, workers, log)
    rows = []
    for g in gran:
        arr = read_tile(download(g, tok))
        v = np.full(len(setores), np.nan)
        v[ok] = arr[row[ok], col[ok]]
        rows.append(pl.DataFrame({"cd_setor": setores["cd_setor"].to_list(), "mes": g["mes"], "luz_noturna": v}))
        log(f"{g['mes']}: mediana {np.nanmedian(v):.2f}")
    out = pl.concat(rows).with_columns(pl.col("luz_noturna").fill_nan(None))
    d = processed_dir() / "covariaveis"
    d.mkdir(parents=True, exist_ok=True)
    out.write_parquet(d / "setor_viirs_mes.parquet")
    return out
