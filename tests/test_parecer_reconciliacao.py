"""Testes da reconciliação como mensuração (parecer R2, R8; ``atlas/reconciliacao.py``), com dados sintéticos."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.stats import nbinom

from cityomics.atlas import reconciliacao as rc
from cityomics.eval import scores
from cityomics.units import reconcile

ESTRATOS = ("via_publica", "trilhos", "residencia")


def setores_sinteticos():
    return pd.DataFrame({"cd_setor": [f"S{i:02d}" for i in range(9)],
                         "cd_dist": ["D1"] * 5 + ["D2"] * 4,
                         "pop_2022": [100, 300, 50, 0, np.nan, 80, 80, 10, 400]})


def eventos_sinteticos(seed: int = 0, n: int = 3000) -> pd.DataFrame:
    """Eventos de 18 meses: taxas desiguais por setor e estrato, 25% sem coordenada."""
    rng = np.random.default_rng(seed)
    s = setores_sinteticos()
    peso = rng.gamma(0.7, 1.0, size=len(s))
    i = rng.choice(len(s), size=n, p=peso / peso.sum())
    dias = pd.to_datetime("2022-01-01") + pd.to_timedelta(rng.integers(0, 547, n), unit="D")
    ev = pd.DataFrame({"cd_setor": s["cd_setor"].to_numpy()[i], "cd_dist": s["cd_dist"].to_numpy()[i],
                       "estrato": rng.choice(ESTRATOS, size=n, p=[0.7, 0.2, 0.1]), "data_fato": dias})
    sem = rng.random(n) < 0.25
    ev.loc[sem, "cd_setor"] = None
    return ev


ELEG = {"trilhos": {"S01", "S02", "S06"}}


def _producao(ev, s):
    p = reconcile.reconcile(ev, s, freq="M", eligible=ELEG)
    return p.assign(periodo=p["periodo"].astype(str)).sort_values(["cd_setor", "periodo"]).reset_index(drop=True)


def test_nucleo_vetorizado_igual_a_producao():
    ev, s = eventos_sinteticos(), setores_sinteticos()
    prod = _producao(ev, s)
    meu = rc.reconcile_esperado(ev, s, eligible=ELEG).sort_values(["cd_setor", "periodo"]).reset_index(drop=True)
    assert (prod["cd_setor"] == meu["cd_setor"]).all() and (prod["periodo"] == meu["periodo"]).all()
    assert np.allclose(prod["n_alocado"], meu["n_alocado"], atol=1e-10)
    assert np.allclose(prod["n_geo"], meu["n_geo"])


def test_sorteio_inteiro_preserva_totais_do_distrito_e_elegiveis():
    ev, s = eventos_sinteticos(seed=1), setores_sinteticos()
    prod = _producao(ev, s)
    d = rc.reconcile_draw(ev, s, np.random.default_rng(5), eligible=ELEG)
    assert np.allclose(d["n_alocado"], np.rint(d["n_alocado"]))
    tot_p = prod.groupby(["cd_dist", "periodo"])["n_alocado"].sum()
    tot_d = d.groupby(["cd_dist", "periodo"])["n_alocado"].sum()
    assert np.allclose(tot_p.sort_index().to_numpy(), tot_d.sort_index().to_numpy())
    # trilhos só vão para os elegíveis do distrito: sem eventos de trilhos sem coordenada fora deles
    so_trilhos = ev[(ev["estrato"] == "trilhos") | ev["cd_setor"].notna()]
    d2 = rc.reconcile_draw(so_trilhos, s, np.random.default_rng(6), eligible=ELEG)
    fora = ~d2["cd_setor"].isin(ELEG["trilhos"])
    assert d2.loc[fora, "n_alocado"].sum() == 0


def test_media_dos_sorteios_igual_a_producao():
    ev, s = eventos_sinteticos(seed=2), setores_sinteticos()
    m = rc.malha(ev, s, eligible=ELEG)
    n = 3000
    r = rc.reparte(m["G_tot"], m["G"], m["U"], m["sd"], m["pop"], m["eleg"], rng=np.random.default_rng(7), n_draws=n)
    media, dp = r["sorteios"].mean(axis=0), r["sorteios"].std(axis=0)
    assert np.all(np.abs(media - r["esperado"]) <= 5 * dp / np.sqrt(n) + 1e-9)
    prod = _producao(ev, s)
    assert np.isclose(r["esperado"].sum(), prod["n_alocado"].sum())


@pytest.mark.parametrize("mu", [0.1, 0.25, 0.5, 1.0, 3.0, 10.0])
def test_teste_de_dispersao_rejeita_no_maximo_alfa_sob_poisson(mu):
    rng = np.random.default_rng(int(mu * 100))
    Y = rng.poisson(mu, size=(40_000, 12)).astype(float)
    r = rc._rejeicao(Y)
    assert r["todos"] <= rc.ALFA_TESTE + 0.005


def test_nulo_poisson_nas_medias_observadas_fica_abaixo_de_alfa():
    medias = np.r_[np.zeros(50), np.full(3000, 0.2), np.full(500, 2.0)]
    out = rc.nulo_poisson(medias, n_rep=20, seed=1)
    assert out["todos"]["media"] <= rc.ALFA_TESTE and out["setores"] == 3500


def _crps_integral(y, mu, phi, dx=2e-4, top=80.0):
    """∫ (F(x) − 1{x ≥ y})² dx por soma de Riemann numa grade fina (independente da fórmula)."""
    n, p = scores.nb_scipy(mu, phi)
    x = np.arange(0.0, top, dx) + dx / 2
    F = nbinom.cdf(np.floor(x), n, p)
    return float((((F - (x >= y)) ** 2).sum()) * dx)


@pytest.mark.parametrize("y,mu,phi", [(0.03, 0.5, 3.0), (0.6, 0.5, 3.0), (1.3, 2.0, 3.0), (2.0, 2.0, 3.0),
                                      (0.0, 0.2, 3.0), (7.4, 5.0, 1.5)])
def test_crps_nb_real_e_a_integral(y, mu, phi):
    got = rc.crps_nb_real(np.array([y]), np.array([mu]), phi)[0]
    assert got == pytest.approx(_crps_integral(y, mu, phi), abs=2e-3)
    if float(y).is_integer():
        assert got == pytest.approx(scores.crps_nb(np.array([y]), np.array([mu]), phi)[0], abs=1e-9)


def test_crps_da_producao_com_y_fracionario_e_o_de_teto_y():
    y, mu, phi = np.array([0.03, 0.6, 1.3]), np.array([0.5, 0.5, 2.0]), 3.0
    assert np.allclose(scores.crps_nb_registrado(y, mu, phi), scores.crps_nb(np.ceil(y), mu, phi))
    # perto de zero a fórmula registrada mais que dobra o correto; scores.crps_nb já é o CRPS de y real
    assert rc.crps_nb_real(y[:1], mu[:1], phi)[0] < 0.5 * scores.crps_nb_registrado(y[:1], mu[:1], phi)[0]
    assert np.allclose(scores.crps_nb(y, mu, phi), rc.crps_nb_real(y, mu, phi))


def test_calibra_acerta_a_fracao_media_por_estrato():
    rng = np.random.default_rng(3)
    w = rng.poisson(3.0, size=(500, 2)).astype(float)
    z = rc._z(rng.normal(size=500))
    p = rc._calibra(w, z, np.array([0.1, 0.8]), beta=1.0)
    assert np.average(p[:, 0], weights=w[:, 0]) == pytest.approx(0.1, abs=1e-6)
    assert np.average(p[:, 1], weights=w[:, 1]) == pytest.approx(0.8, abs=1e-6)
    assert np.all(np.diff(p[np.argsort(z), 0]) >= 0)  # mais ocultação onde z é maior
