"""Cliente do repositório de downloads do novo GeoSampa.

A interface lista os arquivos de uma camada com ``Download/Nas/Tree`` (download da camada)
ou ``Download/Nas/TreeGeneric`` (download genérico, ex.: o cadastro IPTU anexado à camada
"Lote") e entrega cada arquivo por POST em ``Download/Download`` ou ``DownloadGeneric``.
Este módulo reproduz essas chamadas e registra cada arquivo no manifesto de fontes externas.

Camada 352 ("Lote", Cadastro Fiscal):
- download da camada: lotes fiscais por distrito (GPKG/SHP/KMZ, SIRGAS 2000);
- download genérico: ``IPTU_<ano>.zip`` (emissão geral anual, 1995 em diante).
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from cityomics import external
from cityomics.ingest.snapshot import sha256

BASE = "https://novogeosampa.prefeitura.sp.gov.br/"
HEADERS = {"User-Agent": "Mozilla/5.0 (CityOmics research pipeline)"}
LAYER_LOTE = 352
BASE_PATH = {
    (LAYER_LOTE, False): r"\\nas.prodam\du0110_download\GEOPORTAL_DOWNLOAD_SEM_INTERACAO\12_Cadastro\Lotes",
    (LAYER_LOTE, True): r"\\nas.prodam\du0110_download\GEOPORTAL_DOWNLOAD_SEM_INTERACAO\12_Cadastro\IPTU_INTER",
}


def list_files(layer_id: int, generic: bool = False) -> list[dict]:
    endpoint = "TreeGeneric" if generic else "Tree"
    r = requests.get(BASE + f"Download/Nas/{endpoint}", headers=HEADERS, timeout=180,
                     params={"layerId": layer_id, "path": "", "depth": 1, "includeFiles": "true"})
    r.raise_for_status()
    files = []

    def walk(node):
        for child in node.get("children") or []:
            if child["type"] == "file":
                files.append(child)
            else:
                walk(child)

    walk(r.json()["node"])
    return files


def download(layer_id: int, entry: dict, group: str, generic: bool = False, attempts: int = 5, log=print) -> Path:
    dest = external.external_dir() / group / entry["name"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size == entry["size"]:
        return dest
    body = {"IdLayer": layer_id, "RelativePathAndFile": entry["relativePath"], "FileName": entry["name"],
            "BasePath": BASE_PATH[(layer_id, generic)]}
    url = BASE + ("Download/DownloadGeneric" if generic else "Download/Download")
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, attempts + 1):
        try:
            with requests.post(url, json=body, headers=HEADERS, stream=True, timeout=(30, 600)) as r:
                r.raise_for_status()
                ctype = r.headers.get("content-type", "")
                if "html" in ctype or "json" in ctype:
                    raise RuntimeError(f"{entry['name']}: resposta não é arquivo ({ctype})")
                with part.open("wb") as fh:
                    for chunk in r.iter_content(1 << 20):
                        fh.write(chunk)
            if part.stat().st_size != entry["size"]:
                raise RuntimeError(f"{entry['name']}: {part.stat().st_size} != {entry['size']} bytes")
            part.replace(dest)
            break
        except (requests.RequestException, RuntimeError):
            if attempt == attempts:
                raise
            time.sleep(10 * attempt)
    manifest = external.load_manifest()
    manifest[f"{group}/{entry['name']}"] = {
        "url": f"{url} (layer {layer_id}, {entry['relativePath']})",
        "remote_last_modified": entry.get("modified"),
        "size": dest.stat().st_size,
        "sha256": sha256(dest),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    external.manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    log(f"{entry['name']}: {entry['size'] / 1e6:.1f} MB")
    return dest


def fetch_lotes(log=print) -> list[Path]:
    files = [f for f in list_files(LAYER_LOTE) if f["relativePath"].startswith("GPKG_ZIP/")]
    return [download(LAYER_LOTE, f, "geosampa/lotes", log=log) for f in files]


def fetch_iptu(years=None, log=print) -> list[Path]:
    files = list_files(LAYER_LOTE, generic=True)
    if years is not None:
        wanted = {f"IPTU_{y}.zip" for y in years}
        files = [f for f in files if f["name"] in wanted]
    return [download(LAYER_LOTE, f, "geosampa/iptu", generic=True, log=log) for f in files]
