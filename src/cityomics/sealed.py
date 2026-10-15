"""Cofre dos dados de 2026 (D10, D26, D32, D33).

Nenhuma análise lê ``data/sealed_2026/`` antes de o plano estar congelado. A leitura exige
duas chaves iguais:

1. ``prereg/UNSEAL_KEY`` (versionado), que contém uma de duas formas:
   - o DOI do registro no OSF (``10.17605/OSF.IO/XXXXX``), quando houver;
   - ``FREEZE-<sha>``, o commit de congelamento que registra os hashes dos modelos e a
     seleção dos melhores da classe (D33: o registro no OSF ficou para a etapa final).
     O commit precisa existir no histórico e conter ``prereg/FREEZE_MANIFEST.json`` completo
     (``cityomics.freeze``): um commit qualquer não abre o cofre.
2. A variável de ambiente ``CITYOMICS_UNSEAL_KEY`` com o mesmo valor, o que torna a
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

from cityomics.paths import REPO_ROOT, sealed_dir, unseal_key_file

ENV_FLAG = "CITYOMICS_UNSEAL_KEY"
ACCESS_LOG = "ACCESS_LOG.jsonl"
_DOI_RE = re.compile(r"^10\.17605/OSF\.IO/[A-Z0-9]{5,}$")
_FREEZE_RE = re.compile(r"^FREEZE-([0-9A-F]{7,40})$")


class SealedError(PermissionError):
    """Tentativa de ler o cofre de 2026 sem as duas chaves."""


def _normalize(value: str) -> str:
    value = value.strip().upper()
    for prefix in ("HTTPS://DOI.ORG/", "DOI:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value


def _git(*args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None


def _commit_exists(sha: str) -> bool:
    out = _git("cat-file", "-e", f"{sha.lower()}^{{commit}}")
    return out is not None and out.returncode == 0


def _commit_has_manifest(sha: str) -> bool:
    """O commit de congelamento precisa conter um manifesto completo (``prereg/FREEZE_MANIFEST.json``)."""
    out = _git("show", f"{sha.lower()}:prereg/FREEZE_MANIFEST.json")
    if out is None or out.returncode != 0:
        return False
    try:
        return json.loads(out.stdout).get("complete") is True
    except ValueError:
        return False


def registered_key() -> str | None:
    """Chave válida gravada em ``prereg/UNSEAL_KEY`` (primeira linha não comentada), ou None."""
    path = unseal_key_file()
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key = _normalize(line)
        if _DOI_RE.match(key):
            return key
        freeze = _FREEZE_RE.match(key)
        if freeze and _commit_exists(freeze.group(1)) and _commit_has_manifest(freeze.group(1)):
            return key
        return None
    return None


def is_unsealed() -> bool:
    key = registered_key()
    return key is not None and _normalize(os.environ.get(ENV_FLAG, "")) == key


def require_unsealed(purpose: str) -> str:
    """Devolve a chave se o cofre puder ser aberto; senão levanta SealedError."""
    key = registered_key()
    if key is None:
        raise SealedError(
            "Os dados de 2026 estão lacrados: falta uma chave válida em "
            f"{unseal_key_file()} (DOI do OSF ou FREEZE-<sha de um commit existente>)."
        )
    if _normalize(os.environ.get(ENV_FLAG, "")) != key:
        raise SealedError(
            f"Os dados de 2026 estão lacrados: defina {ENV_FLAG}={key} para confirmar a "
            f"abertura (finalidade declarada: {purpose!r})."
        )
    return key


def _git_commit() -> str | None:
    out = _git("rev-parse", "--short", "HEAD")
    return (out.stdout.strip() or None) if out else None


def open_sealed(name: str, purpose: str) -> Path:
    """Caminho de um arquivo do cofre, após checar as chaves e registrar o acesso."""
    if not purpose.strip():
        raise ValueError("Declare a finalidade da leitura do cofre.")
    key = require_unsealed(purpose)
    path = sealed_dir() / name
    if not path.exists():
        raise FileNotFoundError(path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "file": name,
        "purpose": purpose,
        "key": key,
        "commit": _git_commit(),
    }
    with (sealed_dir() / ACCESS_LOG).open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def sealed_path_for_write(name: str) -> Path:
    """Caminho de destino no cofre para a ingestão (F1). Não exige chaves."""
    sealed_dir().mkdir(parents=True, exist_ok=True)
    return sealed_dir() / name
