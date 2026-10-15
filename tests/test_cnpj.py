from cityomics.covariates import cnpj


def test_grupo_cnae_by_division():
    assert cnpj.grupo_cnae("5611201") == "bar_restaurante"
    assert cnpj.grupo_cnae("4712100") == "comercio_varejista"
    assert cnpj.grupo_cnae("6422100") == "financeiro"
    assert cnpj.grupo_cnae("8511200") == "educacao_saude"
    assert cnpj.grupo_cnae("7020400") == "outros_servicos"
    assert cnpj.grupo_cnae(None) == "outros_servicos"
