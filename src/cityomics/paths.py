"""Caminhos do projeto.

As funções leem as variáveis de ambiente no momento da chamada, para que testes e
notebooks do Colab possam apontar para outro diretório de dados.

- ``CITYOMICS_DATA``: raiz dos dados (padrão: ``<repo>/data``, fora do git).
- ``CITYOMICS_PREREG_DOI_FILE``: arquivo com o DOI do pré-registro (padrão: ``<repo>/prereg/OSF_DOI``).
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def prereg_doi_file() -> Path:
    return Path(os.environ.get("CITYOMICS_PREREG_DOI_FILE", REPO_ROOT / "prereg" / "OSF_DOI"))
