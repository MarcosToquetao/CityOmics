"""Verificações de privacidade (D14, D28, D30).

Duas varreduras:

- ``scan_repo``: arquivos de texto do repositório (fora de ``data/``, ``.git`` e ambientes)
  em busca de chaves de API. ``.env`` é ignorado de propósito: é onde as chaves devem ficar,
  e ele está no ``.gitignore``.
- ``scan_tables``: tabelas de um diretório (por padrão ``data/processed``), em busca de colunas
  que identificam o BO ou o endereço. ``processed`` é o que pode subir ao Colab.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cityomics.paths import REPO_ROOT, processed_dir

FORBIDDEN_COLUMNS = frozenset({
    "NUM_BO", "LOGRADOURO", "NUMERO_LOGRADOURO", "LATITUDE", "LONGITUDE", "CEP",
})

SECRET_PATTERNS = (
    re.compile(r"sk-or-v1-[A-Za-z0-9]{32,}"),            # OpenRouter
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),           # Anthropic
    re.compile(r"\bghp_[A-Za-z0-9]{30,}"),               # GitHub
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),             # Google
    re.compile(r"(?i)\b(api[_-]?key|secret|token)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]"),
)

_SKIP_DIRS = {".git", "data", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache",
              "node_modules", ".ipynb_checkpoints", "renv"}
_SKIP_FILES = {".env"}
_TEXT_SUFFIXES = {".py", ".r", ".md", ".txt", ".toml", ".yml", ".yaml", ".json", ".cfg",
                  ".ini", ".ipynb", ".sh", ".csv", ".tsv", ".html", ".example", ""}
_MAX_BYTES = 2_000_000


@dataclass(frozen=True)
class Finding:
    path: Path
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"{self.path}: {self.kind}: {self.detail}"


def _iter_repo_files(root: Path):
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in _SKIP_DIRS for part in rel.parts[:-1]) or rel.parts[0] in _SKIP_DIRS:
            continue
        if path.is_file() and path.name not in _SKIP_FILES and path.suffix.lower() in _TEXT_SUFFIXES:
            if path.stat().st_size <= _MAX_BYTES:
                yield path


def scan_repo(root: Path = REPO_ROOT) -> list[Finding]:
    findings = []
    for path in _iter_repo_files(root):
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(Finding(path, "possível segredo", match.group(0)[:12] + "…"))
    return findings


def _columns(path: Path) -> list[str]:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        import pyarrow.parquet as pq
        return list(pq.read_schema(path).names)
    if suffix in {".csv", ".tsv"}:
        with path.open(errors="ignore") as fh:
            header = fh.readline()
        return [c.strip().strip('"') for c in re.split(r"[,;\t]", header)]
    return []


def scan_tables(directory: Path | None = None) -> list[Finding]:
    directory = directory or processed_dir()
    findings = []
    if not directory.exists():
        return findings
    for path in directory.rglob("*"):
        if path.is_file():
            bad = sorted({c for c in _columns(path) if c.upper() in FORBIDDEN_COLUMNS})
            if bad:
                findings.append(Finding(path, "coluna proibida", ", ".join(bad)))
    return findings
