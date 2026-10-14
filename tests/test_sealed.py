import json

import pytest

from cityomics import sealed

DOI = "10.17605/OSF.IO/AB12C"


@pytest.fixture
def vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    doi_file = tmp_path / "OSF_DOI"
    monkeypatch.setenv("CITYOMICS_PREREG_DOI_FILE", str(doi_file))
    monkeypatch.delenv(sealed.ENV_FLAG, raising=False)
    target = sealed.sealed_path_for_write("celular_2026.parquet")
    target.write_bytes(b"conteudo")
    return doi_file


def test_locked_without_registration(vault):
    with pytest.raises(sealed.SealedError, match="falta o DOI"):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_locked_without_session_flag(vault):
    vault.write_text("# DOI do pré-registro\n" + DOI + "\n")
    with pytest.raises(sealed.SealedError, match=sealed.ENV_FLAG):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_locked_when_flag_differs(vault, monkeypatch):
    vault.write_text(DOI)
    monkeypatch.setenv(sealed.ENV_FLAG, "10.17605/OSF.IO/ZZZZZ")
    with pytest.raises(sealed.SealedError):
        sealed.open_sealed("celular_2026.parquet", "avaliação F7")


def test_invalid_doi_counts_as_unregistered(vault, monkeypatch):
    vault.write_text("rascunho")
    monkeypatch.setenv(sealed.ENV_FLAG, "rascunho")
    assert sealed.registered_doi() is None
    assert not sealed.is_unsealed()


def test_opens_with_both_keys_and_logs(vault, monkeypatch):
    vault.write_text("https://doi.org/" + DOI.lower())
    monkeypatch.setenv(sealed.ENV_FLAG, DOI)
    path = sealed.open_sealed("celular_2026.parquet", "avaliação F7")
    assert path.read_bytes() == b"conteudo"
    log = (path.parent / sealed.ACCESS_LOG).read_text().splitlines()
    entry = json.loads(log[-1])
    assert entry["doi"] == DOI and entry["purpose"] == "avaliação F7"


def test_purpose_is_required(vault, monkeypatch):
    vault.write_text(DOI)
    monkeypatch.setenv(sealed.ENV_FLAG, DOI)
    with pytest.raises(ValueError):
        sealed.open_sealed("celular_2026.parquet", "  ")
