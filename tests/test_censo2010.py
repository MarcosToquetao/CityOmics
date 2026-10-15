import pandas as pd

from cityomics.covariates import censo2010


def test_idade_maps_age_to_column_v034_plus_age():
    cols = {f"V{i:03d}": [i] for i in range(35, 135)}   # valor = número da coluna
    d = pd.DataFrame(cols)
    assert censo2010._idade(d, 1, 1)["0"] if False else censo2010._idade(d, 1, 1).iloc[0] == 35    # 1 ano = V035
    assert censo2010._idade(d, 15, 24).iloc[0] == sum(range(49, 59))                              # V049..V058
    assert censo2010._idade(d, 60, 99).iloc[0] == sum(range(94, 134))                             # V094..V133
