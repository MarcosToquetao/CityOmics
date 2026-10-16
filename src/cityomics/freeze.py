"""Congelamento do plano antes de abrir 2026 (F4, D33).

O commit de congelamento fixa, antes de qualquer leitura do cofre de 2026:

- o código (commit anterior, árvore limpa) e o ambiente (locks);
- as entradas (sha256 do snapshot dos BOs, do manifesto de fontes externas, do painel de
  covariáveis e dos alvos);
- o núcleo teórico de covariáveis (``prereg/core_covariates.json``);
- os modelos congelados (sha256 dos arquivos em ``data/models/frozen/``) e a identidade dos
  melhores da classe (``prereg/selection.json``).

``cityomics freeze check`` lista o que falta. ``cityomics freeze commit --confirm`` grava
``prereg/FREEZE_MANIFEST.json``, faz o commit de congelamento e, num segundo commit, grava
``prereg/UNSEAL_KEY`` com ``FREEZE-<sha do primeiro>``. O cofre só abre se o commit da chave
contiver um manifesto completo (ver ``sealed.py``).
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cityomics.ingest.snapshot import sha256
from cityomics.paths import REPO_ROOT, data_dir, processed_dir, sealed_dir

MANIFEST = "prereg/FREEZE_MANIFEST.json"
SELECTION = "prereg/selection.json"
CORE = "prereg/core_covariates.json"
LOCKS = ["conda-linux-64.lock", "requirements-pip.lock", "R/versions.lock"]
INPUTS = {
    "snapshot_bo": lambda: data_dir() / "snapshot.json",
    "manifesto_externas": lambda: data_dir() / "external" / "manifest.json",
    "painel_covariaveis": lambda: processed_dir() / "covariaveis" / "painel_setor_mes.parquet",
    "alvo_celular": lambda: processed_dir() / "alvos" / "celular_setor_mes.parquet",
    "alvo_letal": lambda: processed_dir() / "alvos" / "letal_distrito_trimestre.parquet",
}
# artefatos do atlas que entram no manifesto (D52): rótulos por lote, domínios, composição, cofre espacial e banco L–R
ATLAS = {
    "tipos_lote": lambda: processed_dir() / "atlas" / "lote_tipos_2025.parquet",
    "dominios_setor": lambda: processed_dir() / "atlas" / "setor_dominio_2025.parquet",
    "composicao_setor": lambda: processed_dir() / "atlas" / "setor_composicao_2025.parquet",
    "cofre_espacial": lambda: REPO_ROOT / "prereg" / "atlas_vault.json",
    "banco_ligante_receptor": lambda: REPO_ROOT / "src" / "cityomics" / "atlas" / "lr_pairs.json",
}
# identidades que a seleção pré-2026 precisa declarar (spec-benchmark §5; prereg §5.2)
SELECTION_KEYS = ["best_baseline_crps", "best_baseline_pai1", "best_crossdomain_crps", "best_crossdomain_pai1",
                  "laya_ft", "lightgbm_compressed_state", "markov_fate_baseline"]


def models_dir() -> Path:
    return data_dir() / "models" / "frozen"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()


def core_columns() -> tuple[list[str], list[str]]:
    core = json.loads((REPO_ROOT / CORE).read_text())
    cols = [c for g in core["groups"].values() for c in g]
    return cols, core.get("optional_columns", [])


def model_hashes() -> dict[str, str]:
    d = models_dir()
    if not d.exists():
        return {}
    return {str(p.relative_to(d)): sha256(p) for p in sorted(d.rglob("*")) if p.is_file()}


def check(run_tests: bool = True) -> list[str]:
    """Pendências que impedem o congelamento (lista vazia = pronto)."""
    problems: list[str] = []
    if _git("status", "--porcelain", "--untracked-files=no"):
        problems.append("árvore git com alterações não commitadas")
    if run_tests:
        r = subprocess.run(["python", "-m", "pytest", "-q", "-x"], cwd=REPO_ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            problems.append("testes falhando")
    log = sealed_dir() / "ACCESS_LOG.jsonl"
    if log.exists() and log.read_text().strip():
        problems.append("o cofre de 2026 já foi aberto (ACCESS_LOG não está vazio): o plano não pode mais ser congelado")
    for nome, f in INPUTS.items():
        if not f().exists():
            problems.append(f"entrada ausente: {nome} ({f()})")
    for lock in LOCKS:
        if not (REPO_ROOT / lock).exists():
            problems.append(f"lock ausente: {lock}")
    panel = INPUTS["painel_covariaveis"]()
    if panel.exists():
        import polars as pl

        cols = set(pl.scan_parquet(panel).collect_schema().names())
        needed, optional = core_columns()
        faltam = [c for c in needed if c not in cols and c not in optional]
        if faltam:
            problems.append(f"covariáveis do núcleo ausentes no painel: {faltam}")
    sel_path = REPO_ROOT / SELECTION
    if not sel_path.exists():
        problems.append(f"{SELECTION} ausente (identidades dos melhores da classe)")
    else:
        sel = json.loads(sel_path.read_text())
        faltam_sel = [k for k in SELECTION_KEYS if not sel.get(k)]
        if faltam_sel:
            problems.append(f"seleção incompleta em {SELECTION}: {faltam_sel}")
    if not model_hashes():
        problems.append(f"nenhum modelo congelado em {models_dir()}")
    missing = [n for n, fn in ATLAS.items() if not fn().exists()]
    if missing:
        problems.append("artefatos do atlas ausentes (D52): " + ", ".join(missing))
    return problems


def manifest() -> dict:
    sel = json.loads((REPO_ROOT / SELECTION).read_text())
    return {
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_commit": _git("rev-parse", "HEAD"),
        "inputs": {n: sha256(f()) for n, f in INPUTS.items()},
        "locks": {lock: sha256(REPO_ROOT / lock) for lock in LOCKS},
        "core_covariates": sha256(REPO_ROOT / CORE),
        "selection": sel,
        "models": model_hashes(),
        "atlas": {n: sha256(fn()) for n, fn in ATLAS.items() if fn().exists()},
    }


def freeze(log=print) -> str:
    """Grava o manifesto, faz o commit de congelamento e a chave. Devolve a chave ``FREEZE-<sha>``."""
    problems = check()
    if problems:
        raise RuntimeError("congelamento bloqueado:\n- " + "\n- ".join(problems))
    path = REPO_ROOT / MANIFEST
    path.write_text(json.dumps(manifest(), indent=2, ensure_ascii=False) + "\n")
    _git("add", MANIFEST, SELECTION, CORE)
    _git("commit", "-m", "F4: congelamento do plano antes de abrir 2026 (manifesto de hashes)\n\n"
         "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    sha = _git("rev-parse", "--short", "HEAD")
    key = f"FREEZE-{sha.upper()}"
    (REPO_ROOT / "prereg" / "UNSEAL_KEY").write_text(f"# chave do cofre de 2026 (commit de congelamento)\n{key}\n")
    _git("add", "prereg/UNSEAL_KEY")
    _git("commit", "-m", f"F4: chave do cofre {key}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    log(f"congelado: {key}")
    return key
