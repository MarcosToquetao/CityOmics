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


def fetch(url: str, group: str, filename: str | None = None, log=print) -> Path:
    """Baixa ``url`` para ``data/external/<group>/`` (se ainda não estiver lá) e registra."""
    filename = filename or url.rstrip("/").rsplit("/", 1)[-1]
    dest = external_dir() / group / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    size, last_modified = remote_size(url)
    if not (dest.exists() and (size == 0 or dest.stat().st_size == size)):
        log(f"{filename}: baixando {size / 1e6:.0f} MB")
        download(url, dest, size)
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
