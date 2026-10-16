"""Executa os roteiros de ``figures/figN.py`` (``cityomics figures --periodo dev|2026``)."""

from __future__ import annotations

import importlib.util
import sys

from cityomics.paths import REPO_ROOT

FIGS = ["fig1", "fig2", "fig3", "fig4", "fig5", "fig6", "ed"]


def load(name: str):
    path = REPO_ROOT / "figures" / f"{name}.py"
    if str(path.parent) not in sys.path:
        sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"figures_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(periodo: str = "dev", only: list[str] | None = None, log=print) -> list:
    common = load("common")
    common.check_periodo(periodo)
    out = []
    for name in only or FIGS:
        if not (REPO_ROOT / "figures" / f"{name}.py").exists():
            log(f"{name}: roteiro ainda não existe")
            continue
        path = load(name).make(periodo)
        log(f"{name}: {path}")
        out.append(path)
    return out
