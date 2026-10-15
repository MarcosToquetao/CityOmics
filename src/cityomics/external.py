"""Downloads de bases públicas externas (IBGE, GeoSampa, ...), com registro de procedência.

Os arquivos vão para ``data/external/<grupo>/`` e cada um é registrado em
``data/external/manifest.json`` com URL, data, tamanho e sha256 (mesmo padrão do
snapshot dos BOs, D18).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cityomics.ingest.snapshot import download, remote_size, sha256
from cityomics.paths import data_dir


def external_dir() -> Path:
    return data_dir() / "external"


def manifest_file() -> Path:
    return external_dir() / "manifest.json"


def load_manifest() -> dict:
    path = manifest_file()
    return json.loads(path.read_text()) if path.exists() else {}


GEOSAMPA_WFS = "https://wfs.geosampa.prefeitura.sp.gov.br/geoserver/geoportal/wfs"


def fetch_geosampa(layer: str, page_size: int = 100_000, log=print) -> Path:
    """Baixa uma camada do WFS do GeoSampa como GeoJSON em EPSG:31983 (uma vez) e registra.
    Camadas grandes (ex.: iluminação pública) são baixadas em páginas."""
    import requests

    name = layer.split(":")[-1]
    dest = external_dir() / "geosampa" / f"{name}.geojson"
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        base = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer,
                "outputFormat": "application/json", "srsName": "EPSG:31983"}
        hits = requests.get(GEOSAMPA_WFS, params=dict(base, resultType="hits"), timeout=300)
        import re as _re
        m = _re.search(r'numberMatched="(\d+)"', hits.text)
        if m and int(m.group(1)) <= 30_000:
            page_size = 0  # cabe numa única resposta: sem paginação
        features, start, collection = [], 0, None
        while True:
            params = dict(base, count=page_size, startIndex=start, sortBy="id") if page_size else base
            log(f"GeoSampa WFS: {layer} (a partir de {start:,})")
            r = requests.get(GEOSAMPA_WFS, params=params, timeout=900)
            if r.status_code == 400 and "sortBy" in params:  # camada sem campo id
                params.pop("sortBy")
                r = requests.get(GEOSAMPA_WFS, params=params, timeout=900)
            r.raise_for_status()
            page = r.json()
            collection = collection or {k: v for k, v in page.items() if k != "features"}
            got = page.get("features", [])
            features += got
            total = page.get("numberMatched") or page.get("totalFeatures")
            # o servidor limita cada página (30 mil feições), então avança pelo que veio
            if not page_size or not got or (isinstance(total, int) and len(features) >= total):
                break
            start += len(got)
        collection["features"] = features
        dest.write_text(json.dumps(collection))
    manifest = load_manifest()
    key = f"geosampa/{dest.name}"
    if key not in manifest:
        manifest[key] = {"url": f"{GEOSAMPA_WFS}?typeNames={layer}", "size": dest.stat().st_size,
                         "sha256": sha256(dest),
                         "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return dest


def fetch(url: str, group: str, filename: str | None = None, log=print, auth=None) -> Path:
    """Baixa ``url`` para ``data/external/<group>/`` (se ainda não estiver lá) e registra."""
    filename = filename or url.rstrip("/").rsplit("/", 1)[-1]
    dest = external_dir() / group / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    size, last_modified = remote_size(url, auth=auth)
    if not (dest.exists() and (size == 0 or dest.stat().st_size == size)):
        log(f"{filename}: baixando {size / 1e6:.0f} MB")
        download(url, dest, size, auth=auth)
    manifest = load_manifest()
    key = f"{group}/{filename}"
    if manifest.get(key, {}).get("size") != dest.stat().st_size:
        manifest[key] = {
            "url": url,
            "remote_last_modified": last_modified,
            "size": dest.stat().st_size,
            "sha256": sha256(dest),
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        manifest_file().write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return dest
