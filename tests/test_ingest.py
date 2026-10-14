import datetime as dt

import pandas as pd
import pytest

from cityomics.ingest import schema, ssp

HDR_2022 = ["NOME_DELEGACIA", "CIDADE", "NUM_BO", "ANO_BO", "DATA_COMUNICACAO_BO", "DATA_OCORRENCIA_BO",
            "HORA_OCORRENCIA_BO", "DESCR_PERIODO", "DESCR_SUBTIPOLOCAL", "BAIRRO", "LOGRADOURO",
            "NUMERO_LOGRADOURO", "LATITUDE", "LONGITUDE", "NOME_DELEGACIA_CIRCUNCRIÇÃO",
            "NOME_MUNICIPIO_CIRCUNCRIÇÃO", "RUBRICA", "DESCR_CONDUTA", "NATUREZA_APURADA",
            "MES_ESTATISTICA", "ANO_ESTATISTICA"]
HDR_2026 = [h.replace("CIDADE", "NOME_MUNICIPIO").replace("DATA_COMUNICACAO_BO", "DATA_REGISTRO")
            .replace("DESCR_PERIODO", "DESC_PERIODO").replace("CIRCUNCRIÇÃO", "CIRCUNSCRICAO")
            for h in HDR_2022]


def row(num, nat, fato, reg, mun="S.PAULO", lat=-23.55, lon=-46.63, mes=1):
    return ["01 DP", mun, num, "2025", reg, fato, "10:00:00", None, "VIA PUBLICA", "SE", "RUA A",
            "10", lat, lon, "01 DP", mun, "Art. 121", None, nat, mes, 2025]


def test_harmonize_aligns_2022_and_2026_headers():
    a = schema.harmonize(pd.DataFrame([row("1", "HOMICÍDIO DOLOSO", "2025-01-02", "2025-01-03")],
                                      columns=HDR_2022), "ssp", 2022)
    b = schema.harmonize(pd.DataFrame([row("1", "HOMICÍDIO DOLOSO", "2025-01-02", "2025-01-03")],
                                      columns=HDR_2026), "ssp", 2026)
    assert list(a.columns) == list(b.columns) == schema.CANONICAL
    assert a.loc[0, "municipio_fato"] == b.loc[0, "municipio_fato"] == "S.PAULO"
    assert a.loc[0, "data_registro"] == b.loc[0, "data_registro"] == pd.Timestamp("2025-01-03")
    assert a.loc[0, "natureza_norm"] == "HOMICIDIO DOLOSO"


def test_harmonize_fixes_formula_months_coords_and_junk_dates():
    rows = [row("1", "FURTO – OUTROS", "1700-01-13", "2025-03-04", mes="=MONTH(G2)"),
            row("2", "FURTO - OUTROS", "2025-03-01", "2025-03-04", lat=0, lon=0),
            row("3", "FURTO - OUTROS", "02/03/2025", "2025-03-04", lat="NULL", lon="NULL")]
    h = schema.harmonize(pd.DataFrame(rows, columns=HDR_2026), "ssp", 2025)
    assert h["mes_estatistica"].tolist() == [3, 1, 1]
    assert pd.isna(h.loc[0, "data_fato"])
    assert h.loc[2, "data_fato"] == pd.Timestamp("2025-03-02")
    assert h["coord_valida"].tolist() == [True, False, False]
    assert set(h["natureza_norm"]) == {"FURTO - OUTROS"}


def test_is_sealed_routes_by_fact_date():
    df = pd.DataFrame({"data_fato": pd.to_datetime(["2026-01-01", "2025-12-31", None, None]),
                       "data_registro": pd.to_datetime(["2026-01-02", "2026-01-05", "2026-02-01",
                                                        "2025-06-01"])})
    assert ssp.is_sealed(df).tolist() == [True, False, True, False]


def test_dedup_celular_keeps_latest_version():
    df = pd.DataFrame({"id_delegacia": ["10", "10", "11"], "ano_bo": ["2025"] * 3,
                       "num_bo": ["A", "A", "A"], "versao": pd.array([1, 3, pd.NA], dtype="Int64"),
                       "logradouro": ["v1", "v3", "outro"]})
    out = ssp.dedup_celular(df)
    assert len(out) == 2 and "v3" in out["logradouro"].tolist()


def test_celular_natureza_and_letal_flags():
    nat = ssp.celular_natureza(pd.Series(["Roubo (art. 157)", "Furto (art. 155)", "Perda/Extravio"]))
    assert nat.tolist()[:2] == ["ROUBO DE CELULAR", "FURTO DE CELULAR"] and pd.isna(nat.iloc[2])
    df = pd.DataFrame({"natureza_norm": ["HOMICIDIO DOLOSO", "TENTATIVA DE HOMICIDIO",
                                         "HOMICIDIO DOLOSO POR ACIDENTE DE TRANSITO"]})
    ev = ssp.events_letal(df)
    assert ev["estrito"].tolist() == [True, False]


@pytest.fixture
def data_root(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    return tmp_path / "data"


def test_parse_file_end_to_end_seals_2026(data_root, tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    wb.active.title = "CAMPOS_DA_TABELA_SPDADOS"
    wb.active.append(["dicionário"])
    ws = wb.create_sheet("JAN-JUN_2026")
    ws.append(HDR_2026)
    d = dt.datetime
    ws.append(row("1", "HOMICÍDIO DOLOSO", d(2026, 2, 1), d(2026, 2, 2)))             # cofre
    ws.append(row("2", "TENTATIVA DE HOMICÍDIO", d(2025, 12, 20), d(2026, 1, 5)))   # 2025, registro tardio
    ws.append(row("2", "TENTATIVA DE HOMICÍDIO", d(2025, 12, 20), d(2026, 1, 5)))   # duplicata
    ws.append(row("3", "HOMICÍDIO DOLOSO", d(2025, 11, 1), d(2026, 1, 2), mun="GUARULHOS"))
    ws.append(row("4", "FURTO - OUTROS", d(2025, 10, 1), d(2026, 1, 2)))
    path = tmp_path / "SPDadosCriminais_2026.xlsx"
    wb.save(path)

    res = ssp.parse_file("ssp", 2026, path=path, log=lambda *_: None)
    assert res.selados == 1 and res.linhas_capital == 2 and res.eventos == {"letal": 1}

    raw = pd.read_parquet(data_root / "raw" / "bo" / "ssp_2026.parquet")
    assert (raw["data_fato"] < ssp.SEAL_FROM).all()
    ev = pd.read_parquet(data_root / "interim" / "eventos_letal_ssp_2026.parquet")
    assert ev["natureza"].tolist() == ["TENTATIVA DE HOMICIDIO"] and "num_bo" not in ev.columns
    assert (data_root / "sealed_2026" / "eventos_letal_ssp_2026.parquet").exists()
