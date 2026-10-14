"""Cofre dos dados de 2026 (D10, D26, D32).

Nenhuma análise lê ``data/sealed_2026/`` antes do pré-registro. A leitura exige duas chaves:

1. ``prereg/OSF_DOI`` contém o DOI do registro no OSF. O arquivo é versionado, então o
   commit que o adiciona é um carimbo de data público.
2. A variável de ambiente ``CITYOMICS_PREREG_DONE`` tem o mesmo DOI, o que torna a
   abertura uma decisão explícita da sessão, e não um efeito colateral de um import.

Cada abertura é registrada em ``data/sealed_2026/ACCESS_LOG.jsonl`` com data, finalidade e
commit, para que o artigo possa documentar quando e para quê o teste foi lido.

Escrever no cofre (durante a ingestão, F1) é sempre permitido: guardar não vaza nada.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cityomics.paths import REPO_ROOT, prereg_doi_file, sealed_dir

ENV_FLAG = "CITYOMICS_PREREG_DONE"
ACCESS_LOG = "ACCESS_LOG.jsonl"
_DOI_RE = re.compile(r"^10\.17605/OSF\.IO/[A-Z0-9]{5,}$")


class SealedError(PermissionError):
    """Tentativa de ler o cofre de 2026 sem as duas chaves do pré-registro."""


def _normalize_doi(value: str) -> str:
    value = value.strip().upper()
    for prefix in ("HTTPS://DOI.ORG/", "DOI:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value


def registered_doi() -> str | None:
    """DOI gravado em ``prereg/OSF_DOI`` (primeira linha não comentada), ou None."""
    path = prereg_doi_file()
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            doi = _normalize_doi(line)
            return doi if _DOI_RE.match(doi) else None
    return None


def is_unsealed() -> bool:
    doi = registered_doi()
    return doi is not None and _normalize_doi(os.environ.get(ENV_FLAG, "")) == doi


def require_unsealed(purpose: str) -> str:
    """Devolve o DOI se o cofre puder ser aberto; senão levanta SealedError."""
    doi = registered_doi()
    if doi is None:
        raise SealedError(
            "Os dados de 2026 estão lacrados: falta o DOI do pré-registro em "
            f"{prereg_doi_file()} (formato 10.17605/OSF.IO/XXXXX)."
        )
    flag = _normalize_doi(os.environ.get(ENV_FLAG, ""))
    if flag != doi:
        raise SealedError(
            f"Os dados de 2026 estão lacrados: defina {ENV_FLAG}={doi} para confirmar a "
            f"abertura (finalidade declarada: {purpose!r})."
        )
    return doi


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def open_sealed(name: str, purpose: str) -> Path:
    """Caminho de um arquivo do cofre, após checar as chaves e registrar o acesso."""
    if not purpose.strip():
        raise ValueError("Declare a finalidade da leitura do cofre.")
    doi = require_unsealed(purpose)
    path = sealed_dir() / name
    if not path.exists():
        raise FileNotFoundError(path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "file": name,
        "purpose": purpose,
        "doi": doi,
        "commit": _git_commit(),
    }
    with (sealed_dir() / ACCESS_LOG).open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def sealed_path_for_write(name: str) -> Path:
    """Caminho de destino no cofre para a ingestão (F1). Não exige chaves."""
    sealed_dir().mkdir(parents=True, exist_ok=True)
    return sealed_dir() / name
