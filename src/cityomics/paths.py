"""Caminhos do projeto.

As funções leem as variáveis de ambiente no momento da chamada, para que testes e
notebooks do Colab possam apontar para outro diretório de dados.

- ``CITYOMICS_DATA``: raiz dos dados (padrão: ``<repo>/data``, fora do git).
- ``CITYOMICS_UNSEAL_KEY_FILE``: arquivo com a chave do cofre de 2026 (padrão: ``<repo>/prereg/UNSEAL_KEY``).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def env_value(name: str) -> str:
    """Valor de uma chave: variável de ambiente ou linha ``NOME=valor`` do ``.env`` (fora do git). Nunca é registrada."""
    v = os.environ.get(name, "").strip()
    if v:
        return v
    f = REPO_ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            k, sep, val = line.partition("=")
            if sep and k.strip() == name:
                return val.strip().strip("\"'")
    return ""


def data_dir() -> Path:
    return Path(os.environ.get("CITYOMICS_DATA", REPO_ROOT / "data"))


def raw_dir() -> Path:
    """Microdados com NUM_BO, endereço e coordenadas. Só local (D14)."""
    return data_dir() / "raw"


def interim_dir() -> Path:
    return data_dir() / "interim"


def processed_dir() -> Path:
    """Agregados por lote/setor/distrito. Únicos dados que podem subir ao Colab (D30)."""
    return data_dir() / "processed"


def sealed_dir() -> Path:
    """Cofre dos dados de 2026 (ver ``cityomics.sealed``)."""
    return data_dir() / "sealed_2026"


def unseal_key_file() -> Path:
    return Path(os.environ.get("CITYOMICS_UNSEAL_KEY_FILE", REPO_ROOT / "prereg" / "UNSEAL_KEY"))
