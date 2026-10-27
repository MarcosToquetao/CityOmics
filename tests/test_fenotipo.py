"""Testes dos pilotos do painel de fenótipos e do relógio do tecido (docs/NARRATIVA.md, P1–P3)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from cityomics.atlas import fenotipo, guard
from cityomics.atlas.attribution import em_fit, em_fit_multi
from cityomics.ingest.ssp import fenotipo_ssp


def test_em_multi_matches_single_output():
    rng = np.random.default_rng(4)
    E = rng.gamma(2.0, 1.0, size=(3000, 4))
    L = np.array([[0.5, 2.0], [2.0, 0.1], [0.0, 1.0], [5.0, 0.3]])
    Y = rng.poisson(E @ L).astype(float)
    multi = em_fit_multi(E, Y, n_iter=50000, tol=1e-14)
    for j in range(2):
        single = em_fit(E, Y[:, j], n_iter=50000, tol=1e-14)["lam"]
        assert np.allclose(multi[:, j], single, atol=1e-3)
    assert np.allclose(multi, L, atol=0.3)


def test_fenotipo_classification_and_phone_overlap():
    df = pd.DataFrame({
        "natureza_norm": ["FURTO - OUTROS", "FURTO - OUTROS", "ROUBO - OUTROS", "FURTO - OUTROS", "FURTO DE VEICULO",
                          "TRAFICO DE ENTORPECENTES", "LESAO CORPORAL DOLOSA", "ROUBO - OUTROS",
                          "LESAO CORPORAL CULPOSA POR ACIDENTE DE TRANSITO", "FURTO - OUTROS"],
        "conduta": ["Outros", "Outros", "Transeunte", "Fios e Cabos", "Veículo", None, None, "Residência", None,
                    "Caixa Eletrônico"],
    })
    cel = pd.Series([False, True, False, False, False, False, False, False, False, False])
    got = fenotipo_ssp(df, cel).tolist()
    want = ["furto_outros", pd.NA, "roubo_outros", "fios_cabos", "furto_veiculo", pd.NA, "lesao_dolosa", "residencia",
            "transito", pd.NA]
    assert [g if g is not pd.NA else None for g in got] == [w if w is not pd.NA else None for w in want]


def test_periodo_do_dia_uses_hour_then_text():
    ev = pd.DataFrame({"hora_fato": ["03:10:00", "18:30:00", None, None, "12:00:00"],
                       "periodo": [None, None, "Pela manhã", "Em hora incerta", None]})
    got = fenotipo.periodo_do_dia(ev).tolist()
    assert got[:3] == ["madrugada", "noite", "manha"]
    assert pd.isna(got[3])
    assert got[4] == "tarde"


def test_contraste_is_zero_for_identical_profiles():
    E = np.ones((10, 3))
    lam = np.tile([1.0, 2.0, 3.0, 4.0], (3, 1)) * np.array([[1.0], [2.0], [0.5]])
    H, P, w = fenotipo._contraste(lam, E)
    assert abs(H) < 1e-12
    assert np.isclose(w.sum(), 1.0)


def test_pilots_stay_before_2026():
    assert max(fenotipo.YEARS) <= guard.YEAR_MAX
    assert max(fenotipo.ANOS_ASSINATURA) <= guard.YEAR_MAX


def test_event_study_recovers_injected_effect():
    from cityomics.atlas import perturbacao as pt

    rng = np.random.default_rng(5)
    n = 4000
    celula = rng.integers(0, 4, n)
    trend = np.linspace(0.5, 1.0, pt.N_MESES)
    Y = rng.poisson(np.outer(np.ones(n), trend) * (1 + 0.2 * celula[:, None])).astype(float)
    coorte = np.full(n, -1)
    tr = rng.choice(n, 800, replace=False)
    coorte[tr] = rng.integers(pt.COORTE[0], pt.COORTE[1] + 1, len(tr))
    for i in tr:
        Y[i, coorte[i]:] += rng.poisson(0.3, pt.N_MESES - coorte[i])
    controle = coorte < 0
    r = pt.att(Y, coorte, controle, celula)
    assert abs(r["pre"]) < 0.08
    assert abs(r["efeito"] - 0.3) < 0.08


def test_hour_overlap_splits_and_wraps_midnight():
    from cityomics.atlas.presenca import hour_overlap

    ov = hour_overlap([30, 1400], [90, 1500])
    assert np.isclose(ov[0, 0], 0.5) and np.isclose(ov[0, 1], 0.5) and np.isclose(ov[0].sum(), 1.0)
    assert np.isclose(ov[1, 23], 40 / 60) and np.isclose(ov[1, 0], 1.0)


def test_presence_timeline_covers_the_day_once():
    from cityomics.atlas.presenca import hour_overlap, segments

    od = pd.DataFrame({
        "ID_PESS": [1, 1, 2], "FE_PESS": [2.0, 2.0, 3.0], "MUNI_DOM": [36, 36, 36],
        "CO_DOM_X": [1.0, 1.0, 5.0], "CO_DOM_Y": [1.0, 1.0, 5.0], "N_VIAG": [1.0, 2.0, np.nan], "FE_VIA": [2.0, 2.0, np.nan],
        "CO_O_X": [1.0, 9.0, np.nan], "CO_O_Y": [1.0, 9.0, np.nan], "CO_D_X": [9.0, 1.0, np.nan], "CO_D_Y": [9.0, 1.0, np.nan],
        "H_SAIDA": [7.0, 18.0, np.nan], "MIN_SAIDA": [0.0, 0.0, np.nan], "H_CHEG": [8.0, 19.0, np.nan], "MIN_CHEG": [0.0, 0.0, np.nan],
        "ANDA_O": [10.0, 10.0, np.nan], "ANDA_D": [5.0, 5.0, np.nan], "TIPVG": [1.0, 1.0, np.nan], "CD_ENTRE": [1, 1, 2]})
    pres, rua = segments(od)
    horas = (hour_overlap(pres["a"], pres["b"]).sum(1) * pres["w"]).sum()
    assert np.isclose(horas, 2.0 * 22 + 3.0 * 24)          # a pessoa 1 passa 2 h viajando
    assert np.isclose((rua["b"] - rua["a"]).sum(), 30)       # 10 + 5 minutos andando em cada viagem


def test_memory_decomposition_separates_tissue_from_stable_residual():
    from cityomics.atlas.memoria import decompoe

    rng = np.random.default_rng(6)
    M = np.exp(rng.normal(1.5, 1.0, (4000, 1))) * np.ones((1, 4))
    memoria = np.exp(rng.normal(0, 0.6, (4000, 1)))
    Y = rng.poisson(M * memoria).astype(float)
    r = decompoe(Y, M)
    assert r["partes"]["memoria_estavel"] > 0.1
    assert r["persistencia_residuo"][1] > 0.4


def test_model_free_ceiling_is_zero_for_poisson_noise():
    from cityomics.atlas.previsibilidade import dispersao, teto_sem_modelo

    rng = np.random.default_rng(7)
    unit = np.repeat(np.arange(3000), 12)
    per = np.tile(np.arange(1, 13), 3000)
    y = rng.poisson(np.repeat(rng.gamma(2.0, 2.0, 3000), 12)).astype(float)
    t = teto_sem_modelo(y, unit, per)
    assert t["quando"] < 0.03 and t["onde_e_quando"] > 0.5
    d = dispersao(y, unit)
    assert abs(d["fracao_rejeita_poisson_5pct"] - 0.05) < 0.02


def test_holm_and_confirmation_lock(tmp_path, monkeypatch):
    import pytest

    from cityomics.atlas import confirmacao

    adj = confirmacao.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert np.isclose(adj["a"], 0.03) and np.isclose(adj["c"], 0.06) and np.isclose(adj["b"], 0.06)
    monkeypatch.setattr(confirmacao, "REPO_ROOT", tmp_path)
    (tmp_path / "prereg").mkdir()
    with pytest.raises(confirmacao.ConfirmacaoBloqueada):
        confirmacao.confirmar()
    (tmp_path / "prereg" / "AMENDMENTS.md").write_text("| (data) | 3.4 | A11. rascunho |\n")
    assert not confirmacao.a11_datada()
    (tmp_path / "prereg" / "AMENDMENTS.md").write_text("| 2026-11-30 | 3.4 | A11. Integrated paper |\n")
    assert confirmacao.a11_datada()


def test_em_distrito_recupera_taxas_com_risco_por_distrito():
    from cityomics.atlas.robustez import em_distrito

    rng = np.random.default_rng(0)
    n, k = 3000, 4
    E = rng.gamma(2.0, 1.0, size=(n, k))
    lam = np.array([5.0, 1.0, 0.2, 0.05])
    dist = rng.integers(0, 30, size=n)
    theta = rng.gamma(4.0, 0.25, size=30)
    y = rng.poisson(theta[dist] * (E @ lam))[:, None].astype(float)
    est, th = em_distrito(E, y, dist, n_iter=40)
    razao = est[:, 0] / lam
    assert list(np.argsort(-est[:, 0])) == [0, 1, 2, 3]          # a ordem das classes é recuperada
    assert np.all(np.abs(razao[:2] / razao[:2].mean() - 1) < 0.1)  # as taxas dominantes, em escala relativa
    assert np.corrcoef(th, theta)[0, 1] > 0.9                      # o risco de cada distrito é recuperado


def test_poder_dispersao_cresce_com_contagem():
    from cityomics.atlas.robustez import poder_dispersao

    p = poder_dispersao(n_sim=800)
    assert p["mu=0.25|cv=0.3"] < 0.1 < p["mu=10.0|cv=1.0"]
