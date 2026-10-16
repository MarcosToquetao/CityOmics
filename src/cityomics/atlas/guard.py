"""Guardas do atlas: nada de 2026 antes do FREEZE (D10, D55) e cofre espacial de distritos (D53).

- ``pre2026(path)`` falha se um arquivo de entrada for de 2026 (IPTU, ITBI, SP156, CNPJ ou eventos
  do ano lacrado). Todo carregador do atlas passa por ela.
- ``vault()`` devolve os distritos do cofre espacial (``prereg/atlas_vault.json``). Toda análise que
  usa crime no atlas filtra esses distritos até a confirmação registrada na emenda A11.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from cityomics.paths import REPO_ROOT

YEAR_MAX = 2025
VAULT_FILE = REPO_ROOT / "prereg" / "atlas_vault.json"
_RX_2026 = re.compile(r"(?<!\d)2026(?!\d)")


class SealedYearError(PermissionError):
    """Tentativa de ler dados de 2026 no atlas antes do FREEZE."""


def pre2026(path) -> Path:
    p = Path(path)
    if _RX_2026.search(p.name):
        raise SealedYearError(f"o atlas não lê arquivos de 2026 antes do FREEZE: {p.name}")
    return p


def make_vault(distritos: list[str], share: float = 0.2, seed: int = 20261016) -> dict:
    """Sorteia o cofre espacial (uma vez). A semente e o hash da lista ficam registrados."""
    import numpy as np

    ds = sorted(distritos)
    rng = np.random.default_rng(seed)
    k = round(len(ds) * share)
    chosen = sorted(rng.choice(ds, size=k, replace=False).tolist())
    digest = hashlib.sha256(",".join(chosen).encode()).hexdigest()
    return {"seed": seed, "share": share, "n_distritos": len(ds), "cofre": chosen, "sha256": digest,
            "nota": "D53: distritos excluídos de toda análise de crime do atlas até a confirmação (emenda A11)."}


def vault() -> set[str]:
    if not VAULT_FILE.exists():
        raise FileNotFoundError("cofre espacial ainda não sorteado: rode cityomics.atlas.guard.write_vault()")
    v = json.loads(VAULT_FILE.read_text())
    assert hashlib.sha256(",".join(v["cofre"]).encode()).hexdigest() == v["sha256"], "lista do cofre alterada"
    return set(v["cofre"])


def write_vault(distritos: list[str], date: str) -> dict:
    if VAULT_FILE.exists():
        return json.loads(VAULT_FILE.read_text())
    v = make_vault(distritos) | {"data": date}
    VAULT_FILE.write_text(json.dumps(v, ensure_ascii=False, indent=2) + "\n")
    return v


def explore_mask(cd_dist):
    """True para unidades fora do cofre (podem entrar na exploração com crime)."""
    import numpy as np

    v = vault()
    return ~np.isin(np.asarray(cd_dist).astype(str), list(v))
