import polars as pl

from cityomics.covariates import iptu


def frame():
    return pl.DataFrame({
        "setor_fiscal": ["001", "001", "001", "002"],
        "quadra_fiscal": ["003", "003", "003", "010"],
        "lote": ["0001", "0101", "0102", "0005"],
        "cond2": ["00", "12", "12", "00"],
        "uso": ["Loja", "Apartamento em condomínio", "Apartamento em condomínio", "Terreno"],
        "padrao": ["Comercial horizontal - padrão B", "Residencial vertical - padrão C",
                   "Residencial vertical - padrão C", None],
        "area_terreno": [100.0, 900.0, 900.0, 50.0], "area_construida": [90.0, 60.0, 70.0, 0.0],
        "pavimentos": [1.0, 10.0, 10.0, 0.0], "ano_construcao": [1950.0, 2005.0, 2005.0, None],
        "valor_m2_terreno": [1000.0, 2000.0, 2000.0, 300.0], "valor_m2_construcao": [800.0, 1500.0, 1500.0, None],
    })


def test_lot_keys_link_condo_units_to_condo_lot():
    look = pl.DataFrame({"setor_fiscal": ["001"], "quadra_fiscal": ["003"], "cond2": ["12"],
                         "sql_base_condo": ["0010030050"]})
    k = iptu.lot_keys(frame(), look)
    assert k["sql_base"].to_list() == ["0010030001", "0010030050", "0010030050", "0020100005"]


def test_aggregate_counts_units_and_use_shares():
    look = pl.DataFrame({"setor_fiscal": ["001"], "quadra_fiscal": ["003"], "cond2": ["12"],
                         "sql_base_condo": ["0010030050"]})
    agg = iptu.aggregate(iptu.lot_keys(frame(), look)).sort("sql_base")
    condo = agg.filter(pl.col("sql_base") == "0010030050").row(0, named=True)
    assert condo["n_unidades"] == 2 and condo["area_construida"] == 130.0
    assert condo["uso_residencial"] == 1.0 and condo["padrao_medio"] == 1.0
    loja = agg.filter(pl.col("sql_base") == "0010030001").row(0, named=True)
    assert loja["uso_comercio"] == 1.0 and loja["padrao_baixo"] == 1.0
    assert agg.filter(pl.col("sql_base") == "0020100005")["uso_terreno"].item() == 1.0
