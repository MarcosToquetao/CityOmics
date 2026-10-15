import json

from cityomics import freeze
from cityomics.paths import REPO_ROOT


def test_core_covariates_file_is_well_formed():
    core = json.loads((REPO_ROOT / freeze.CORE).read_text())
    cols, optional = freeze.core_columns()
    assert len(cols) == len(set(cols)) and set(optional) <= set(cols)
    assert set(core["groups"]) == {"atividade_rotineira", "desorganizacao_social", "cpted", "mercado_imobiliario", "contexto_temporal"}
    assert not any(c.startswith("cnpj_saidas") for c in cols)           # D12/ onda de 2018
    assert not any(c in cols for c in ("infra_dist_delegacia_m", "infra_dist_base_pm_m", "infra_dist_base_gcm_m"))


def test_check_blocks_without_models_and_selection(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    problems = freeze.check(run_tests=False)
    assert any("nenhum modelo congelado" in p for p in problems)
    assert any("entrada ausente" in p for p in problems)


def test_check_blocks_when_vault_was_opened(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    (tmp_path / "data" / "sealed_2026").mkdir(parents=True)
    (tmp_path / "data" / "sealed_2026" / "ACCESS_LOG.jsonl").write_text('{"file": "x"}\n')
    assert any("já foi aberto" in p for p in freeze.check(run_tests=False))


def test_model_hashes_are_content_based(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path))
    d = tmp_path / "models" / "frozen" / "lgbm"
    d.mkdir(parents=True)
    (d / "m.txt").write_text("a")
    h1 = freeze.model_hashes()
    (d / "m.txt").write_text("b")
    assert h1 != freeze.model_hashes() and list(h1) == ["lgbm/m.txt"]
