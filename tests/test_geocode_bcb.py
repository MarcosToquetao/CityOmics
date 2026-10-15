import polars as pl

from cityomics import geocode
from cityomics.covariates import bcb


def test_norm_logradouro_expands_abbreviations_and_strips_accents():
    assert geocode.norm_logradouro("Av. Brig. Faria Lima") == "AVENIDA BRIGADEIRO FARIA LIMA"
    assert geocode.norm_logradouro("R. São João") == "RUA SAO JOAO"
    assert geocode.norm_logradouro(None) == ""


def test_split_endereco_variants():
    assert bcb.split_endereco("RUA GOV. CELSO RAMOS, NUM 381", "") == ("RUA GOV. CELSO RAMOS", 381)
    assert bcb.split_endereco("AV PAULISTA 1000", "") == ("AV PAULISTA", 1000)
    assert bcb.split_endereco("RUA A, S/N", "") == ("RUA A, S/N", None)
    assert bcb.split_endereco("RUA B", "42") == ("RUA B", 42)


def test_geocode_levels(tmp_path, monkeypatch):
    cnefe = pl.DataFrame({
        "cd_setor": ["1", "1", "2"], "cep": ["01000000", "01000000", "02000000"],
        "logradouro": ["RUA A", "RUA A", "RUA B"], "numero": [10, 20, 5],
        "lat": [-23.5, -23.6, -23.7], "lon": [-46.5, -46.6, -46.7]})
    monkeypatch.setattr(geocode, "cnefe_path", lambda: tmp_path / "c.parquet")
    cnefe.write_parquet(tmp_path / "c.parquet")
    geocode._indices.cache_clear()
    out = geocode.geocode(pl.DataFrame({"cep": ["01000000", None, "01000000", "09999999"],
                                         "logradouro": ["x", "R. A", None, None], "numero": [10, 20, 99, 1]}))
    assert out["nivel"].to_list() == ["numero", "logradouro", "cep", None]
    assert out["cd_setor"].to_list()[:3] == ["1", "1", "1"] and out["lat"][0] == -23.5
    geocode._indices.cache_clear()
