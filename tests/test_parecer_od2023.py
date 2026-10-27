"""Testes da réplica com a OD 2023 (parecer R5, ``cityomics.atlas.presenca_od2023``), só com dados sintéticos."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cityomics.atlas import presenca, presenca_od2023 as od23


def _od() -> pd.DataFrame:
    """Três pessoas: a 1 anda até o trabalho e volta de ônibus, a 2 vai de bicicleta, a 3 não sai de casa."""
    base = {"FE_PESS": 10.0, "MUNI_DOM": 36, "CO_DOM_X": 330000.0, "CO_DOM_Y": 7390000.0, "ID_DOM": "d1", "ZONA": 1}
    linhas = [
        dict(ID_PESS="p1", N_VIAG=1, FE_VIA=12.0, CO_O_X=330000.0, CO_O_Y=7390000.0, CO_D_X=331000.0, CO_D_Y=7391000.0,
             H_SAIDA=8, MIN_SAIDA=0, H_CHEG=8, MIN_CHEG=40, ANDA_O=np.nan, ANDA_D=np.nan, TIPVG=3),
        dict(ID_PESS="p1", N_VIAG=2, FE_VIA=12.0, CO_O_X=331000.0, CO_O_Y=7391000.0, CO_D_X=330000.0, CO_D_Y=7390000.0,
             H_SAIDA=17, MIN_SAIDA=50, H_CHEG=18, MIN_CHEG=50, ANDA_O=5.0, ANDA_D=10.0, TIPVG=1),
        dict(ID_PESS="p2", N_VIAG=1, FE_VIA=8.0, CO_O_X=330000.0, CO_O_Y=7390000.0, CO_D_X=332000.0, CO_D_Y=7392000.0,
             H_SAIDA=23, MIN_SAIDA=30, H_CHEG=0, MIN_CHEG=10, ANDA_O=1.0, ANDA_D=2.0, TIPVG=4),
        dict(ID_PESS="p3", N_VIAG=np.nan, FE_VIA=np.nan, CO_O_X=np.nan, CO_O_Y=np.nan, CO_D_X=np.nan, CO_D_Y=np.nan,
             H_SAIDA=np.nan, MIN_SAIDA=np.nan, H_CHEG=np.nan, MIN_CHEG=np.nan, ANDA_O=np.nan, ANDA_D=np.nan, TIPVG=np.nan),
    ]
    return pd.DataFrame([base | r for r in linhas])


def _minutos(seg: pd.DataFrame) -> pd.Series:
    return (seg["b"] - seg["a"]).groupby(seg["w"]).sum()


def test_rua_de_viagem_a_pe_soma_a_duracao():
    _, rua = od23.segmentos(_od(), ativos=(3, 4))
    a_pe = rua[rua["w"] == 12.0]
    # viagem a pé de 40 min: metade na origem, metade no destino; a de ônibus soma só os 5 + 10 min andando
    assert np.isclose((a_pe["b"] - a_pe["a"]).sum(), 40 + 15)
    h = presenca.hour_overlap(a_pe["a"].to_numpy(), a_pe["b"].to_numpy())
    assert np.isclose(h.sum() * 60, 55)
    # bicicleta que passa da meia-noite (23h30 → 0h10): 40 min inteiros como rua na definição a pé + bicicleta
    bici = rua[rua["w"] == 8.0]
    assert np.isclose((bici["b"] - bici["a"]).sum(), 40)
    assert np.isclose(presenca.hour_overlap(bici["a"].to_numpy(), bici["b"].to_numpy()).sum() * 60, 40)


def test_so_a_pe_deixa_a_bicicleta_com_os_minutos_andando():
    _, rua = od23.segmentos(_od(), ativos=(3,))
    assert np.isclose(_minutos(rua)[8.0], 1 + 2)
    assert np.isclose(_minutos(rua)[12.0], 40 + 15)


def test_segmentos_reproduz_presenca_segments():
    od = _od()
    p0, r0 = presenca.segments(od)
    p1, r1 = od23.segmentos(od, ativos=(3, 4))
    for a, b in ((p0, p1), (r0, r1)):
        pd.testing.assert_frame_equal(a.reset_index(drop=True), b.drop(columns="u").reset_index(drop=True), check_dtype=False)


def test_recorte_por_municipio():
    od = pd.DataFrame({"MUNI_DOM": [36, 15, 36.0, np.nan], "MUNI_O": [36, 36, 24, np.nan], "ID_PESS": list("abcd")})
    assert od23.recorte_municipio(od)["ID_PESS"].tolist() == ["a", "c"]
    assert od23.recorte_municipio(od, campo="MUNI_O")["ID_PESS"].tolist() == ["a", "b"]
    assert od23.recorte_municipio(od, muni=15)["ID_PESS"].tolist() == ["b"]


def test_normaliza_2023_recupera_quem_nao_viajou():
    od = _od()
    cru = od.copy()
    sem = cru["N_VIAG"].isna()
    for c in od23.VIAGEM:
        if c in cru:
            cru[c] = cru[c].fillna(0)
    cru.loc[sem, "TIPVG"] = 2  # a 2023 grava TIPVG = 2 em quem não viajou
    cru["ANDA_O"] = cru["ANDA_O"].map(lambda v: "NU" if v == 0 else str(int(v)))
    cru["ANDA_D"] = cru["ANDA_D"].map(lambda v: "NU" if v == 0 else str(int(v)))
    norm = od23.normaliza_2023(cru)
    assert norm.loc[sem, ["N_VIAG", "TIPVG", "CO_O_X", "FE_VIA"]].isna().all().all()
    assert norm.loc[0, "ANDA_O"] != norm.loc[0, "ANDA_O"]  # "NU" vira nulo
    assert norm.loc[1, "ANDA_D"] == 10.0
    pres, _ = od23.segmentos(norm)
    p3 = pres[pres["w"].eq(10.0) & pres["a"].eq(0.0) & pres["b"].eq(1440.0)]
    assert len(p3) == 1  # a pessoa sem viagem fica o dia todo em casa


def test_multiplicidades_preservam_o_tamanho_de_cada_zona():
    zona = np.array([1, 1, 1, 2, 2, 3])
    M = od23.multiplicidades(zona, n_boot=20, seed=1)
    assert M.shape == (20, 6)
    for z in (1, 2, 3):
        assert (M[:, zona == z].sum(axis=1) == (zona == z).sum()).all()


def test_somar_sigma_padrao_e_zero():
    from cityomics.atlas import presenca as P
    from cityomics.atlas.presenca_od2023 import somar

    nx = ny = 30
    ids = np.zeros(nx * ny, dtype="int32")
    ids[:] = 1                                          # um setor cobrindo a grade
    g = {"n": 1, "nx": nx, "ny": ny, "ids": ids, "riy": np.array([15]), "rix": np.array([15]), "area_cells": np.array([900.0]),
         "n_cells": np.array([900])}
    cell = np.array([15 * nx + 15, 10 * nx + 10])
    W = np.zeros((2, 24))
    W[:, 3] = [2.0, 3.0]
    np.testing.assert_allclose(somar(cell, W, g)[0, 3], 5.0)                      # o total é conservado
    np.testing.assert_allclose(somar(cell, W, g), somar(cell, W, g, sigma_m=P.SIGMA_M))
    np.testing.assert_allclose(somar(cell, W, g, sigma_m=0.0)[0, 3], 5.0)
