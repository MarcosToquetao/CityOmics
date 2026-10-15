"""Snapshot congelado dos xlsx brutos (D18).

Para cada arquivo, consulta o tamanho no servidor da SSP. Se existir uma cópia local
(por exemplo, no MapaSegurancaSP) com o mesmo tamanho, ela é copiada; senão, o arquivo é
baixado com retomada. Tudo vai para ``data/raw/xlsx/`` e é registrado em
``data/snapshot.json`` com origem, data, tamanho e sha256.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from cityomics.ingest.sources import SOURCES, YEARS, Source
from cityomics.paths import data_dir, raw_dir

CHUNK = 1 << 20
HEADERS = {"User-Agent": "Mozilla/5.0 (CityOmics research pipeline)"}


def xlsx_dir() -> Path:
    return raw_dir() / "xlsx"


def snapshot_file() -> Path:
    return data_dir() / "snapshot.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def remote_size(url: str, attempts: int = 6, auth=None) -> tuple[int, str | None]:
    for attempt in range(1, attempts + 1):
        try:
            r = requests.head(url, timeout=60, headers=HEADERS, allow_redirects=True, auth=auth)
            if r.status_code == 404:
                raise FileNotFoundError(url)
            r.raise_for_status()
            return int(r.headers.get("Content-Length", 0)), r.headers.get("Last-Modified")
        except requests.RequestException:
            if attempt == attempts:
                raise
            time.sleep(10 * attempt)
    raise RuntimeError("inalcançável")


def download(url: str, dest: Path, size: int, attempts: int = 8, auth=None) -> None:
    part = dest.with_suffix(".part")
    for attempt in range(1, attempts + 1):
        have = part.stat().st_size if part.exists() else 0
        if size and have >= size:
            break
        headers = dict(HEADERS, **({"Range": f"bytes={have}-"} if have else {}))
        try:
            with requests.get(url, stream=True, timeout=(30, 300), headers=headers, auth=auth) as r:
                r.raise_for_status()
                mode = "ab" if have and r.status_code == 206 else "wb"
                with part.open(mode) as fh:
                    for chunk in r.iter_content(CHUNK):
                        fh.write(chunk)
            break
        except (requests.RequestException, OSError):
            if attempt == attempts:
                raise
            time.sleep(10 * attempt)
    if size and part.stat().st_size != size:
        raise RuntimeError(f"{dest.name}: tamanho {part.stat().st_size} != {size}")
    part.replace(dest)


def load_snapshot() -> dict:
    path = snapshot_file()
    return json.loads(path.read_text()) if path.exists() else {"files": {}}


def fetch(source: Source, year: int, copy_from: Path | None = None, log=print) -> dict:
    """Garante o arquivo no snapshot e devolve o registro dele."""
    name, url = source.filename(year), source.url(year)
    dest = xlsx_dir() / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    size, last_modified = remote_size(url)
    local = copy_from / name if copy_from else None

    if dest.exists() and dest.stat().st_size == size:
        origin = "já no snapshot (tamanho igual ao remoto)"
    elif local is not None and local.exists() and local.stat().st_size == size:
        log(f"{name}: copiando de {local.parent} ({size / 1e6:.0f} MB)")
        shutil.copy2(local, dest)
        origin = f"cópia de {local} (tamanho igual ao remoto)"
    else:
        log(f"{name}: baixando {size / 1e6:.0f} MB")
        download(url, dest, size)
        origin = "download"

    return {
        "url": url,
        "origin": origin,
        "remote_last_modified": last_modified,
        "size": dest.stat().st_size,
        "sha256": sha256(dest),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def build(years=YEARS, copy_from: Path | None = None, log=print) -> dict:
    snap = load_snapshot()
    for source in SOURCES:
        for year in years:
            try:
                snap["files"][source.filename(year)] = fetch(source, year, copy_from, log)
            except FileNotFoundError:
                log(f"{source.filename(year)}: 404 no servidor da SSP; ignorado")
    snap["frozen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    snapshot_file().parent.mkdir(parents=True, exist_ok=True)
    snapshot_file().write_text(json.dumps(snap, indent=2, ensure_ascii=False))
    return snap


def verify() -> list[str]:
    """Confere os sha256 do snapshot contra os arquivos em disco."""
    problems = []
    for name, rec in load_snapshot()["files"].items():
        path = xlsx_dir() / name
        if not path.exists():
            problems.append(f"{name}: ausente")
        elif sha256(path) != rec["sha256"]:
            problems.append(f"{name}: sha256 diferente do snapshot")
    return problems
