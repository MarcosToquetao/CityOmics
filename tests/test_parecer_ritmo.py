"""Testes sintéticos de ``atlas.ritmo_queda`` (parecer crítico, Agente C). Não leem dados."""

import numpy as np

from cityomics.atlas import ritmo_queda as rq


def _eventos(seed=0, n=4000, n_setores=60, n_dist=4, dias=365):
    rng = np.random.default_rng(seed)
    i = rng.integers(0, n_setores, n)
    dist = np.arange(n_setores) % n_dist
    # agrupamento temporal: metade dos eventos repete o dia e o período de um evento anterior do mesmo setor
    t = rng.integers(0, dias, n)
    p = rng.integers(0, 4, n)
    rep = rng.random(n) < 0.5
    src = rng.integers(0, n, n)
    i[rep], t[rep], p[rep] = i[src[rep]], t[src[rep]], p[src[rep]]
    return i, t, p, dist


def test_nulo_em_blocos_preserva_eventos_por_periodo_e_setor():
    i, t, p, dist = _eventos()
    b = rq.blocos(i, t, p, dist)
    assert b["n"].sum() == len(i)
    rng = np.random.default_rng(1)
    for _ in range(20):
        pp = rq.permuta_blocos(b, rng)
        d = dist[b["i"]]
        antes = np.bincount(d * 4 + b["p"], weights=b["n"], minlength=16)
        depois = np.bincount(d * 4 + pp, weights=b["n"], minlength=16)
        np.testing.assert_array_equal(antes, depois)                       # eventos por distrito × período
        np.testing.assert_array_equal(np.bincount(b["i"], weights=b["n"]),  # eventos por setor
                                      np.bincount(i, minlength=b["i"].max() + 1)[: b["i"].max() + 1])
        # cada bloco troca de rótulo inteiro: o tamanho do bloco que recebe um rótulo é o mesmo do que cedeu
        for g in np.unique(b["grupo"]):
            m = b["grupo"] == g
            assert len(np.unique(b["n"][m])) == 1


def test_nulo_em_blocos_mexe_nos_rotulos():
    i, t, p, dist = _eventos(seed=2)
    b = rq.blocos(i, t, p, dist)
    pp = rq.permuta_blocos(b, np.random.default_rng(3))
    assert np.mean(pp != b["p"]) > 0.3


def test_concentracao_toda_a_queda_num_setor():
    y0 = np.full(200, 5.0)
    y1 = y0.copy()
    y0[17] = 50.0
    y1[17] = 0.0
    c = rq.concentracao(y0, y1)
    assert c["top1"]["unidades"] == 2
    assert np.isclose(c["top1"]["parte_queda"], 1.0)
    assert np.isclose(c["queda_liquida"], 50.0)


def test_concentracao_queda_proporcional_segue_o_crime_inicial():
    rng = np.random.default_rng(4)
    y0 = rng.gamma(0.5, 10, 1000)
    c = rq.concentracao(y0, 0.6 * y0)
    for k in ("top1", "top5", "top10"):
        assert np.isclose(c[k]["parte_queda"], c[k]["parte_ini_topo_ini"])
    assert np.isclose(c["gini_quedas"], c["gini_ini"])


def test_gini_extremos():
    assert np.isclose(rq.gini(np.ones(10)), 0.0)
    x = np.zeros(100)
    x[0] = 1.0
    assert np.isclose(rq.gini(x), 0.99)


def test_multiplicidade_fica_na_zona():
    est = {"ini": np.repeat([0, 3, 5], [3, 2, 4]), "n": np.repeat([3, 2, 4], [3, 2, 4]), "n_dom": 9, "n_zonas": 3}
    rng = np.random.default_rng(5)
    for _ in range(50):
        m = rq.multiplicidade(est, rng)
        assert m.sum() == 9
        assert m[0:3].sum() == 3 and m[3:5].sum() == 2 and m[5:9].sum() == 4


def test_att_vetorizado_igual_ao_original():
    from cityomics.atlas.perturbacao import N_MESES, att

    rng = np.random.default_rng(6)
    n = 300
    Y = rng.poisson(0.3, (n, N_MESES)).astype(float)
    celula = rng.integers(0, 5, n)
    coorte = np.full(n, -1)
    tr = rng.choice(n, 60, replace=False)
    coorte[tr] = rng.integers(12, 36, 60)
    controle = coorte < 0
    controle[rng.choice(np.where(controle)[0], 40, replace=False)] = False   # nem tratados nem controles
    a = att(Y, coorte, controle, celula)
    b = rq.att_vec(Y, coorte, celula, rq._media_controles(Y, controle, celula), np.where(coorte >= 0)[0])
    assert a["n"] == b["n"]
    for k in ("base", "pre", "efeito"):
        assert np.isclose(a[k], b[k])
