"""Estado serializado para o Laya (D24, spec-benchmark §3.3).

Cada linha (setor × mês-alvo) vira um texto em inglês com ID anônimo, de poucas centenas de tokens
(limite do modelo: 1.024). O mesmo conteúdo existe como vetor numérico (``compressed_numeric``),
que é o que o comparador LightGBM recebe (H2): as 10 covariáveis marcadoras mais extremas entram
com seu z-score e as demais ficam ausentes, de modo que texto e vetor carreguem **a mesma
informação**.

O estado traz: perfil do setor (top-10 marcadores em z-score contra a distribuição do período de
ajuste), tendência de crime as-of (1, 3, 6, 12 meses, mesmo mês do ano anterior, vizinhança), as
previsões de outros métodos, e o calendário do mês. Opcionalmente (ablações) traz nomes reais de
distrito e bairro, ou omite o histórico de crime, ou omite blocos de escores.

Privacidade (D14/D30): o ID é ``sha256(sal + cd_setor)`` truncado; o sal e o mapa ficam locais.
Nenhum código de setor, endereço ou coordenada entra no texto.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
import polars as pl

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December"]
PREFIX = {"censo2022_": "census 2022 ", "censo_interp_": "census (interpolated) ", "censo_d_": "census change 2010-2022 ",
          "censo_g_": "census growth 2010-2022 ", "infra_": "infrastructure ", "osm_": "OpenStreetMap ", "ipvs_ipvs_": "IPVS social vulnerability ",
          "cnpj_": "business registry ", "sp156_": "city 156 requests ", "agencias_": "bank branches ", "n_transacoes": "property transactions",
          "preco_m2": "property price per m2", "frac_financiada": "share of financed property purchases", "pop_dasi": "estimated population"}
TREND_COLS = ["h_int_l1", "h_int_s3", "h_int_s6", "h_int_s12", "h_int_l12", "nb_h_int_s3"]
CAL_COLS = ["dias_uteis", "dias_feriado", "dias_carnaval", "tem_decimo_terceiro"]
QUESTIONS = {
    "ge1": {"type": "noul", "instructions": "Will at least one cellphone robbery or theft be recorded in this census tract during the forecast month?"},
    "ge3": {"type": "noul", "instructions": "Will three or more cellphone robberies or thefts be recorded in this census tract during the forecast month?"},
    "band": {"type": "score", "instructions": "How many cellphone robberies or thefts will be recorded in this census tract during the forecast month?",
             "criteria": ["none", "one", "two to three", "four to seven", "eight or more"]},
}


def anon_id(cd_setor: list[str] | np.ndarray, salt: str) -> list[str]:
    return ["T-" + hashlib.sha256((salt + str(s)).encode()).hexdigest()[:8] for s in cd_setor]


def label(col: str) -> str:
    for p, t in PREFIX.items():
        if col.startswith(p):
            return (t + col[len(p):]).replace("_", " ").strip()
    return col.replace("_", " ")


def _slog(x: np.ndarray) -> np.ndarray:
    return np.sign(x) * np.log1p(np.abs(x))


class StateBuilder:
    def __init__(self, fit: pl.DataFrame, marker_cols: list[str], salt: str):
        self.cols = [c for c in marker_cols if c in fit.columns]
        x = _slog(np.nan_to_num(fit.select(self.cols).to_numpy().astype("float64")))
        self.mu, self.sd = x.mean(0), x.std(0) + 1e-9
        self.salt = salt
        # percentis da intensidade de 12 meses no período de ajuste (para "percentil na cidade")
        self.ref = np.sort(np.nan_to_num(fit["h_int_s12"].to_numpy().astype("float64") / 12))

    def pct(self, v: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.ref, np.nan_to_num(v), side="right") / len(self.ref) * 100

    def z(self, df: pl.DataFrame) -> np.ndarray:
        x = _slog(np.nan_to_num(df.select(self.cols).to_numpy().astype("float64")))
        return (x - self.mu) / self.sd

    def top10(self, z: np.ndarray) -> np.ndarray:
        """Índices dos 10 marcadores com maior |z| por linha, ordenados por |z| decrescente."""
        k = min(10, z.shape[1])
        idx = np.argpartition(-np.abs(z), k - 1, axis=1)[:, :k]
        order = np.argsort(-np.abs(np.take_along_axis(z, idx, 1)), axis=1)
        return np.take_along_axis(idx, order, 1)

    def compressed_numeric(self, df: pl.DataFrame, scores: dict[str, np.ndarray], history: bool = True) -> pl.DataFrame:
        """Vetor numérico com a mesma informação do texto (marcadores fora do top-10 ficam NaN)."""
        z = self.z(df)
        keep = np.full(z.shape, False)
        np.put_along_axis(keep, self.top10(z), True, axis=1)
        cols = {f"marker_{c}": np.where(keep[:, j], z[:, j], np.nan) for j, c in enumerate(self.cols)}
        if history:
            for c in TREND_COLS:
                cols[c] = np.round(df[c].to_numpy().astype("float64"), 2)
            cols["city_pct_12m"] = np.round(self.pct(df["h_int_s12"].to_numpy() / 12))
        for k, v in scores.items():
            cols[f"score_{k}"] = np.round(v, 2)
        for c in CAL_COLS:
            cols[c] = df[c].to_numpy().astype("float64")
        cols["month_of_year"] = df["mes_num"].to_numpy().astype("float64")
        return pl.DataFrame(cols)

    def texts(self, df: pl.DataFrame, scores: dict[str, np.ndarray], history: bool = True, names: pl.DataFrame | None = None) -> list[str]:
        z = self.z(df)
        top = self.top10(z)
        ids = anon_id(df["cd_setor"].to_list(), self.salt)
        mes_num = df["mes_num"].to_numpy().astype(int)
        yr = df["mes"].str.slice(0, 4).to_list()
        area = df["area_km2"].to_numpy()
        pct = self.pct(df["h_int_s12"].to_numpy() / 12)
        tr = {c: np.round(df[c].to_numpy().astype("float64"), 1) for c in TREND_COLS}
        cal = {c: df[c].to_numpy() for c in CAL_COLS}
        nm = None
        if names is not None:
            nm = df.select("cd_setor").join(names, on="cd_setor", how="left")
        out = []
        for i in range(df.height):
            parts = [f"Census tract {ids[i]}, area {area[i]:.2f} km2. Forecast month: {MONTHS[mes_num[i] - 1]} {yr[i]}"
                     f" ({int(cal['dias_uteis'][i])} business days, {int(cal['dias_feriado'][i])} holidays"
                     f"{', Carnival' if cal['dias_carnaval'][i] else ''}{', 13th-salary month' if cal['tem_decimo_terceiro'][i] else ''})."]
            if nm is not None:
                parts.append(f"Located in district {nm['nm_dist'][i]}.")
            prof = ", ".join(f"{label(self.cols[j])} {z[i, j]:+.1f}" for j in top[i])
            parts.append(f"Most distinctive features versus the city (z-scores): {prof}.")
            if history:
                t = {c: tr[c][i] for c in TREND_COLS}
                parts.append(
                    f"Recent cellphone theft and robbery (coverage-corrected, as reported before the month): last month {t['h_int_l1']}, "
                    f"3-month total {t['h_int_s3']}, 6-month total {t['h_int_s6']}, 12-month total {t['h_int_s12']}, same month last year "
                    f"{t['h_int_l12']}; 12-month rate is at the {pct[i]:.0f}th percentile of the city; nearest neighbors 3-month average {t['nb_h_int_s3']}.")
            if scores:
                parts.append("Forecasts of expected count from other methods: " +
                             ", ".join(f"{k} {v[i]:.2f}" for k, v in scores.items()) + ".")
            out.append(" ".join(parts))
        return out


def rows_for_finetune(texts: list[str], y: np.ndarray) -> list[dict]:
    """Linhas ``{state, questions, expected}`` do formato de ``laya.train.finetune``."""
    bands = np.digitize(y, [0.5, 1.5, 3.5, 7.5])        # 0:none 1:one 2:2-3 3:4-7 4:8+
    out = []
    for t, yy, b in zip(texts, y, bands):
        out.append({"state": t, "questions": QUESTIONS,
                    "expected": {"ge1": bool(yy >= 0.5), "ge3": bool(yy >= 2.5), "band": int(b)}})
    return out
