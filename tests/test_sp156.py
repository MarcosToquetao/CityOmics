import polars as pl

from cityomics.covariates import sp156


def test_grupo_expr_assigns_first_matching_group():
    df = pl.DataFrame({
        "tema": ["Iluminação pública", "Lixo e limpeza", "Meio Ambiente", "Trânsito e Transporte", "Cidadania"],
        "assunto": ["Lâmpada apagada", "Remoção de entulho", "Árvore", "Cartão idoso", "População em situação de rua"],
        "servico": ["", "", "Poda de árvore", "", ""],
    })
    got = df.with_columns(sp156.grupo_expr().alias("g"))["g"].to_list()
    assert got == ["iluminacao", "limpeza_entulho", "arvore_poda", "outros", "pop_rua"]


def test_parse_file_handles_semicolon_and_comma_decimals(tmp_path, monkeypatch):
    monkeypatch.setattr(sp156, "sp156_dir", lambda: tmp_path)
    csv = tmp_path / "x.csv"
    csv.write_text("Data de Abertura;Tema;Assunto;Serviço;Status;Logradouro;CEP;Latitude;Longitude;Distrito\n"
                   "06/01/2021;Lixo e limpeza;Entulho;Remoção;Finalizada;Rua A;01000000;-23,55;-46,63;SE\n"
                   "07/01/2021;Animais;Cães;Vistoria;Finalizada;;;;;\n", encoding="utf-8")
    out = sp156.parse_file("t", csv)
    assert out.height == 2 and out["latitude"].null_count() == 1
    assert out["latitude"][0] == -23.55 and out["grupo"][0] == "limpeza_entulho"
    assert {"logradouro", "cep", "data_abertura"}.isdisjoint(out.columns)
