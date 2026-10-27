"""Congelamento do plano antes de abrir 2026 (F4, D33).

O commit de congelamento fixa, antes de qualquer leitura do cofre de 2026:

- o código (commit anterior, árvore limpa) e o ambiente (locks);
- as entradas (sha256 do snapshot dos BOs, do manifesto de fontes externas, do painel de
  covariáveis e dos alvos);
- o núcleo teórico de covariáveis (``prereg/core_covariates.json``);
- os modelos congelados (sha256 dos arquivos em ``data/models/frozen/``) e a identidade dos
  melhores da classe (``prereg/selection.json``).

Duas etapas (D52, A11):

- **FREEZE-A** (``cityomics freeze commit --etapa A --confirm``): benchmark, modelos congelados
  (``cityomics freeze models``), seleção e artefatos do atlas; grava ``prereg/FREEZE_A_MANIFEST.json``
  e faz o commit, **sem** chave do cofre. Exige as emendas A12 e A13 datadas e o sha256 dos pesos do Laya.
- **FREEZE-B** (``--etapa B``): exige a A11 datada, a confirmação do atlas no cofre espacial feita
  (``prereg/atlas_confirmacao.json``) e os hashes do FREEZE-A inalterados; grava
  ``prereg/FREEZE_MANIFEST.json``, faz o commit e, num segundo commit, grava ``prereg/UNSEAL_KEY`` com
  ``FREEZE-<sha do primeiro>``. O cofre de 2026 só abre se o commit da chave contiver um manifesto
  completo (ver ``sealed.py``).

``cityomics freeze check --etapa A|B`` lista o que falta.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cityomics.ingest.snapshot import sha256
from cityomics.paths import REPO_ROOT, data_dir, processed_dir, sealed_dir

MANIFEST = "prereg/FREEZE_MANIFEST.json"
MANIFEST_A = "prereg/FREEZE_A_MANIFEST.json"
CONFIRMACAO = "prereg/atlas_confirmacao.json"
LAYA_PESOS = "laya_ft/pesos_sha256.json"   # dentro de models_dir(); ver models.congelar
EMENDAS = {"A": ("A12", "A13"), "B": ("A11",)}
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
    # narrativa B (D63, D68): alvos dos fenótipos, presença da OD 2017 e o código pré-especificado da confirmação
    "alvos_fenotipo": lambda: processed_dir() / "atlas" / "fenotipo" / "fenotipo_setor_ano.parquet",
    "presenca_od2017": lambda: processed_dir() / "atlas" / "presenca" / "setor_presenca_hora.parquet",
    "presenca_od2023": lambda: processed_dir() / "atlas" / "presenca_2023" / "setor_presenca_hora.parquet",  # a principal (revisão, 2026-10)
    "codigo_confirmacao": lambda: REPO_ROOT / "src" / "cityomics" / "atlas" / "confirmacao.py",
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


def emenda_datada(codigo: str) -> bool:
    """A emenda está em AMENDMENTS.md numa linha de tabela com data (não só no rascunho)."""
    import re

    am = REPO_ROOT / "prereg" / "AMENDMENTS.md"
    return am.exists() and any(re.match(rf"^\|\s*20\d\d-\d\d-\d\d\s*\|.*\b{codigo}\b", ln)
                               for ln in am.read_text().splitlines())


def check(run_tests: bool = True, etapa: str = "B") -> list[str]:
    """Pendências que impedem o congelamento da etapa ``A`` ou ``B`` (lista vazia = pronto)."""
    problems: list[str] = []
    for e in ("A", "B") if etapa == "B" else ("A",):
        problems += [f"emenda {c} não datada em prereg/AMENDMENTS.md" for c in EMENDAS[e] if not emenda_datada(c)]
    if not (models_dir() / LAYA_PESOS).exists():
        problems.append(f"sha256 dos pesos do Laya ausente ({models_dir() / LAYA_PESOS}; caderno notebooks/colab/laya_hash_pesos.py)")
    if etapa == "B":
        if not (REPO_ROOT / MANIFEST_A).exists():
            problems.append("FREEZE-A ainda não feito")
        elif _git("log", "--oneline", "-1", "--", MANIFEST_A) == "":
            problems.append(f"{MANIFEST_A} não está commitado")
        else:
            a = json.loads((REPO_ROOT / MANIFEST_A).read_text())
            atual = manifest(etapa="A")
            for k in ("inputs", "selection", "models", "atlas", "core_covariates"):
                if a.get(k) != atual.get(k):
                    problems.append(f"'{k}' mudou depois do FREEZE-A")
        if not (REPO_ROOT / CONFIRMACAO).exists():
            problems.append("confirmação do atlas no cofre espacial ainda não rodou (atlas.confirmacao.confirmar)")
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


def manifest(etapa: str = "B") -> dict:
    sel = json.loads((REPO_ROOT / SELECTION).read_text())
    extra = {}
    if etapa == "B":
        extra = {"freeze_a": sha256(REPO_ROOT / MANIFEST_A), "confirmacao_atlas": sha256(REPO_ROOT / CONFIRMACAO),
                 "amendments": sha256(REPO_ROOT / "prereg" / "AMENDMENTS.md")}
    return {"etapa": etapa,
        "complete": True,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code_commit": _git("rev-parse", "HEAD"),
        "inputs": {n: sha256(f()) for n, f in INPUTS.items()},
        "locks": {lock: sha256(REPO_ROOT / lock) for lock in LOCKS},
        "core_covariates": sha256(REPO_ROOT / CORE),
        "selection": sel,
        "models": model_hashes(),
        "atlas": {n: sha256(fn()) for n, fn in ATLAS.items() if fn().exists()},
        **extra,
    }


def freeze(log=print, etapa: str = "B") -> str:
    """Etapa A: manifesto parcial e commit, sem chave. Etapa B: manifesto completo, commit e chave ``FREEZE-<sha>``."""
    problems = check(etapa=etapa)
    if problems:
        raise RuntimeError("congelamento bloqueado:\n- " + "\n- ".join(problems))
    if etapa == "A":
        m = manifest(etapa="A") | {"complete": False}
        (REPO_ROOT / MANIFEST_A).write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        _git("add", MANIFEST_A, SELECTION, CORE)
        _git("commit", "-m", "F4: FREEZE-A (benchmark, modelos congelados, seleção e atlas)\n\n"
             "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        sha = _git("rev-parse", "--short", "HEAD")
        log(f"FREEZE-A: {sha}")
        return f"FREEZE-A-{sha.upper()}"
    path = REPO_ROOT / MANIFEST
    path.write_text(json.dumps(manifest(etapa="B"), indent=2, ensure_ascii=False) + "\n")
    _git("add", MANIFEST, SELECTION, CORE, CONFIRMACAO, "prereg/AMENDMENTS.md")
    _git("commit", "-m", "F4: congelamento do plano antes de abrir 2026 (manifesto de hashes)\n\n"
         "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    sha = _git("rev-parse", "--short", "HEAD")
    key = f"FREEZE-{sha.upper()}"
    (REPO_ROOT / "prereg" / "UNSEAL_KEY").write_text(f"# chave do cofre de 2026 (commit de congelamento)\n{key}\n")
    _git("add", "prereg/UNSEAL_KEY")
    _git("commit", "-m", f"F4: chave do cofre {key}\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>")
    log(f"congelado: {key}")
    return key
