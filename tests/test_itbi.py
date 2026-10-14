import datetime as dt

import pandas as pd
import polars as pl

from cityomics.covariates import itbi


def test_monthly_tables_assign_extinct_lots_by_quadra(tmp_path, monkeypatch):
    monkeypatch.setenv("CITYOMICS_DATA", str(tmp_path / "data"))
    tx = pl.DataFrame({
        "sql_base": ["0010030001", "0010030001", "0010039999", "9999999999"],
        "sql10": ["0010030001", "0010030001", "0010039999", "9999999999"],
        "quadra_key": ["001003", "001003", "001003", "999999"],
        "data": [dt.date(2025, 1, 5), dt.date(2025, 1, 20), dt.date(2025, 2, 1), dt.date(2025, 2, 1)],
        "natureza": ["1.Compra e venda"] * 4, "valor_transacao": [100.0, 300.0, 50.0, 10.0],
        "valor_venal_prop": [None] * 4, "preco_m2": [10.0, 30.0, 5.0, 1.0],
        "financiada": [True, False, False, False], "uso": [""] * 4, "padrao": [""] * 4,
    })
    tx.write_parquet(itbi.itbi_dir() / "transacoes_2025.parquet")
    lotes = pd.DataFrame({"sql_base": ["0010030001", "0010030002"], "cd_setor": ["S1", "S1"],
                          "origem": ["lote_fiscal", "lote_fiscal"]})
    out = itbi.monthly_tables(lotes)
    lote = out["lote"].sort("mes")
    assert lote["n_transacoes"].to_list() == [2] and lote["preco_m2_mediana"].item() == 20.0
    setor = out["setor"].sort("mes")
    # fevereiro: lote extinto (0010039999) vai ao setor pela quadra; quadra desconhecida fica fora
    assert setor["n_transacoes"].to_list() == [2, 1] and setor["frac_lote_extinto"].to_list() == [0.0, 1.0]
    assert out["resumo"]["com_setor"] == 0.75
