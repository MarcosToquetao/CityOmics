import json
import subprocess

import pytest

from cityomics import sealed
from cityomics.paths import REPO_ROOT

DOI = "10.17605/OSF.IO/AB12C"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    key_file = tmp_path / "UNSEAL_KEY"
    monkeypatch.setenv("CITYOMICS_UNSEAL_KEY_FILE", str(key_file))
    monkeypatch.delenv(sealed.ENV_FLAG, raising=False)
    sealed.sealed_path_for_write("celular_2026.parquet").write_bytes(b"conteudo")
    return key_file


def head_sha():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def test_locked_without_key(vault):
    with pytest.raises(sealed.SealedError, match="falta uma chave"):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_locked_without_session_flag(vault):
    vault.write_text("# chave do cofre\n" + DOI + "\n")
    with pytest.raises(sealed.SealedError, match=sealed.ENV_FLAG):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_locked_when_flag_differs(vault, monkeypatch):
    vault.write_text(DOI)
    monkeypatch.setenv(sealed.ENV_FLAG, "10.17605/OSF.IO/ZZZZZ")
    with pytest.raises(sealed.SealedError):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_invalid_key_counts_as_unregistered(vault, monkeypatch):
    vault.write_text("rascunho")
    monkeypatch.setenv(sealed.ENV_FLAG, "rascunho")
    assert sealed.registered_key() is None
    assert not sealed.is_unsealed()


def test_freeze_key_requires_existing_commit(vault, monkeypatch):
    vault.write_text("FREEZE-deadbeefdeadbeef")
    monkeypatch.setenv(sealed.ENV_FLAG, "FREEZE-deadbeefdeadbeef")
    assert sealed.registered_key() is None


def test_opens_with_freeze_commit(vault, monkeypatch):
    key = f"FREEZE-{head_sha()}"
    vault.write_text(key.lower())
    monkeypatch.setenv(sealed.ENV_FLAG, key)
    assert sealed.open_sealed("celular_2026.parquet", "avaliação F7").read_bytes() == b"conteudo"


def test_opens_with_doi_and_logs(vault, monkeypatch):
    vault.write_text("https://doi.org/" + DOI.lower())
    monkeypatch.setenv(sealed.ENV_FLAG, DOI)
    path = sealed.open_sealed("celular_2026.parquet", "avaliação F7")
    entry = json.loads((path.parent / sealed.ACCESS_LOG).read_text().splitlines()[-1])
    assert entry["key"] == DOI and entry["purpose"] == "avaliação F7"


def test_purpose_is_required(vault, monkeypatch):
    vault.write_text(DOI)
    monkeypatch.setenv(sealed.ENV_FLAG, DOI)
    with pytest.raises(ValueError):
        sealed.open_sealed("celular_2026.parquet", "  ")
