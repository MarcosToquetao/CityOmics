"""Fig. 4 — O relógio de cada classe, em ordem de força da evidência (narrativa B; D63, D65, D66; parecer R16).

a: o teste pré-especificado do relógio (C4): furto de celular primeiro, depois roubo. Desvios de cada classe
   em relação ao perfil da cidade por período, 2024 × 2025, e o contraste H contra os nulos: permutação de
   eventos dentro do distrito (``relogio.json``) e permutação de blocos do mesmo setor, dia ou mês
   (``ritmo_queda.json``), com os P de cada nulo;
b: exploratório: perfil horário do roubo de celular por classe (modelo de atribuição, hora exata, 2024–2025);
c: roubo × pedestres na rua, hora a hora, em quatro classes (OD 2023, dias úteis);
d: risco por pedestre hora a hora na cidade, com a faixa de 95% do bootstrap de domicílios da OD 2023;
e: razão fim de semana / dia útil (por dia) do roubo e do furto de celular por classe, com IC de 95%
   (bootstrap por distrito, ``ritmo_queda.json``);
f: roubo por km × roubo por pedestre (OD 2023), com o ρ de Spearman e o seu IC de 95%.

As quatro classes de c saem dos dados (sem nomes de tipo fixos): o tipo residencial horizontal de maior
padrão baixo, as favelas, o tipo de comércio com maior taxa atribuída por km e as estações de trem e metrô.
"""

from __future__ import annotations

import json

import numpy as np
import polars as pl

import rotulos as R
from common import ax_mm, check_periodo, place_labels, row_swatches
from cityomics.atlas.genes_lote import atlas_dir
from cityomics.viz import names as N
from cityomics.viz import palette as P
from cityomics.viz import style as S

PERIODOS = ["madrugada", "manha", "tarde", "noite"]
PER_COR = {"madrugada": "#264653", "manha": "#E9C46A", "tarde": "#E8743B", "noite": "#8E6CC2"}
CRIME_COR = {"celular_furto": "#264653", "celular_roubo": "#D1495B"}
TESTES = [("celular_furto", 2024), ("celular_furto", 2025), ("celular_roubo", 2024), ("celular_roubo", 2025)]
VARIANTE = "pe_bici"  # pessoas a pé e de bicicleta na rua (OD 2023; a pé só dá o mesmo, G_od2023 §4)
PESO_MIN = 0.01


def _plain_log(axis, ticks):
    from matplotlib.ticker import FixedFormatter, FixedLocator, NullFormatter, NullLocator

    axis.set_major_locator(FixedLocator(ticks))
    axis.set_major_formatter(FixedFormatter([f"{v:g}" for v in ticks]))
    axis.set_minor_locator(NullLocator())
    axis.set_minor_formatter(NullFormatter())


def _log_ticks(lo: float, hi: float) -> list[float]:
    """Marcas legíveis numa escala log entre ``lo`` e ``hi`` (no máximo seis, sempre com o 1 se couber)."""
    cand = [0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100] if hi / lo > 30 else [0.1, 0.2, 0.3, 0.5, 1, 2, 3, 5, 10]
    t = [v for v in cand if lo <= v <= hi]
    while len(t) > 6:
        t = [v for i, v in enumerate(t) if i % 2 == 0 or v == 1]
    return t


def _fmt_p(p: float, n: int) -> str:
    """P de permutação; no piso 1/(n+1), "≤"."""
    if p is None or not np.isfinite(p):
        return "—"
    piso = 1 / (n + 1)
    return f"≤{piso:.3f}" if p <= piso * (1 + 1e-9) else f"{p:.3f}"


def _desvios(per: pl.DataFrame, d: str):
    """Desvio de cada classe em relação à média ponderada da cidade, por período, em 2024 e 2025 (pp)."""
    a = per.filter((pl.col("desfecho") == d) & (pl.col("ano") == 2024) & (pl.col("peso") >= PESO_MIN))
    b = per.filter((pl.col("desfecho") == d) & (pl.col("ano") == 2025) & (pl.col("peso") >= PESO_MIN))
    j = a.join(b, on="classe", suffix="_b")
    out = {}
    for q in PERIODOS:
        ma = (a["peso"] * a[q]).sum() / a["peso"].sum()
        mb = (b["peso"] * b[q]).sum() / b["peso"].sum()
        out[q] = ((j[q] - ma).to_numpy() * 100, (j[f"{q}_b"] - mb).to_numpy() * 100)
    return out


def panel_replica(ax, per: pl.DataFrame, rel: dict, d: str, lim: float, titulo: str):
    for q, (x, y) in _desvios(per, d).items():
        ax.scatter(x, y, s=5, color=PER_COR[q], alpha=0.9, linewidth=0, label=N.PERIOD_EN[q], zorder=3)
    ax.plot([-lim, lim], [-lim, lim], color="#D9D9D9", lw=0.5, zorder=0)
    ax.axhline(0, color="#EFEFEF", lw=0.4, zorder=0)
    ax.axvline(0, color="#EFEFEF", lw=0.4, zorder=0)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.set_xlabel("Departure from city, 2024 (pp)")
    ax.set_ylabel("Departure from city, 2025 (pp)")
    r = rel.get(d, {}).get("replica_r", np.nan)
    ax.set_title(f"{titulo}\nr = {r:.2f} between years", fontsize=5.5, loc="left", pad=2)


def panel_nulos(ax, rel: dict, blocos: dict):
    """H observado (losango) contra três nulos: eventos (cinza), blocos de dia e de mês (mediana–p95)."""
    rng = np.random.default_rng(0)
    top = 0.0
    for k, (d, a) in enumerate(TESTES):
        v = rel.get(d, {}).get(str(a), {})
        null = np.asarray(v.get("H_nulo", []), float) * 100
        if null.size:
            ax.scatter(k - 0.08 + rng.uniform(-0.12, 0.12, null.size), null, s=0.5, color="#BDBDBD", linewidth=0, zorder=1)
            top = max(top, null.max())
        b = blocos.get(d, {}).get(str(a), {})
        for nome, dx, mk in (("dia", 0.20, "s"), ("mes", 0.36, "^")):
            nb = b.get(nome)
            if nb:
                lo, hi = nb["H_nulo_mediana"] * 100, nb["H_nulo_p95"] * 100
                ax.plot([k + dx, k + dx], [lo, hi], color="#8C8C8C", lw=0.8, zorder=2)
                ax.scatter([k + dx], [lo], s=6, marker=mk, facecolor="white", edgecolor="#6B6B6B", linewidth=0.5, zorder=3)
                top = max(top, hi)
        if "H" in v:
            ax.scatter([k - 0.08], [v["H"] * 100], s=16, color=CRIME_COR[d], marker="D", zorder=4, edgecolor="white", linewidth=0.3)
            top = max(top, v["H"] * 100)
            hb = b.get("H")
            if hb is not None and abs(hb - v["H"]) > 1e-3 * max(abs(v["H"]), 1e-9):
                print(f"fig4a: H de {d} {a} difere entre relogio.json ({v['H']:.4f}) e ritmo_queda.json ({hb:.4f}); "
                      "rode ritmo_queda depois do relógio")
    ax.set_ylim(0, top * 1.45 if top > 0 else 1)
    ax.set_xlim(-0.55, len(TESTES) - 0.45)
    ax.set_xticks(range(len(TESTES)))
    ax.set_xticklabels([N.clock_label(d, a, "\n") for d, a in TESTES], fontsize=5)
    ax.set_ylabel("Class contrast H (×100)")
    for t, (d, _) in zip(ax.get_xticklabels(), TESTES):
        t.set_color(CRIME_COR[d])
    # tabela de P sob o eixo
    linhas = [("events", lambda d, a: (rel.get(d, {}).get(str(a), {}).get("p"), len(rel.get(d, {}).get(str(a), {}).get("H_nulo", [])) or 200)),
              ("day blocks", lambda d, a: (blocos.get(d, {}).get(str(a), {}).get("dia", {}).get("p"),
                                           blocos.get(d, {}).get(str(a), {}).get("dia", {}).get("n_perm", 999))),
              ("month blocks", lambda d, a: (blocos.get(d, {}).get(str(a), {}).get("mes", {}).get("p"),
                                             blocos.get(d, {}).get(str(a), {}).get("mes", {}).get("n_perm", 999)))]
    from matplotlib.transforms import blended_transform_factory

    tr = blended_transform_factory(ax.transData, ax.transAxes)
    h_mm = ax.get_position().height * ax.figure.get_size_inches()[1] / S.MM
    for i, (nome, fn) in enumerate(linhas):
        y = -(9.0 + 2.6 * i) / h_mm
        ax.text(-0.6, y, f"P, {nome}", transform=tr, ha="right", va="center", fontsize=5, color=S.INK)
        for k, (d, a) in enumerate(TESTES):
            p, n = fn(d, a)
            ax.text(k, y, _fmt_p(p, n), transform=tr, ha="center", va="center", fontsize=5,
                    color=S.INK if (p is not None and p < 0.05) else S.MUTED)
    from matplotlib.lines import Line2D

    h = [Line2D([], [], marker="D", ls="", color=S.INK, ms=3), Line2D([], [], marker="o", ls="", color="#BDBDBD", ms=1.5),
         Line2D([], [], marker="s", ls="-", color="#8C8C8C", mfc="white", mec="#6B6B6B", ms=2.2, lw=0.8),
         Line2D([], [], marker="^", ls="-", color="#8C8C8C", mfc="white", mec="#6B6B6B", ms=2.2, lw=0.8)]
    ax.legend(h, ["Observed", "Null: events permuted", "Null: day blocks", "Null: month blocks"], loc="upper right",
              fontsize=5, handlelength=1.2, handletextpad=0.3, borderaxespad=0.1, labelspacing=0.25)


def panel_heat(ax, h: pl.DataFrame, curto: dict, cols: dict):
    d = h.filter(pl.col("peso") >= PESO_MIN)
    M = d.select([f"h{j:02d}" for j in range(24)]).to_numpy()
    pico = M.argmax(1)
    o = np.lexsort((-d["peso"].to_numpy(), (pico + 18) % 24))  # ordena pelo pico, começando às 18 h
    M, cls = M[o], [d["classe"][int(i)] for i in o]
    vmax = float(np.ceil(np.nanpercentile(M * 100, 99) / 5) * 5)
    im = ax.imshow(M * 100, cmap=P.cmap("lajolla"), vmin=0, vmax=max(vmax, 5), aspect="auto")
    ax.set_yticks(range(len(cls)))
    ax.set_yticklabels([curto.get(c, c) for c in cls], fontsize=5)
    row_swatches(ax, [cols.get(c, "#888888") for c in cls], h=0.8)
    ax.set_xticks([0, 4, 8, 12, 16, 20, 23])
    ax.set_xlabel("Hour of day")
    for s in ax.spines.values():
        s.set_visible(False)
    return im


def destaques(rv: pl.DataFrame) -> list[str]:
    """Quatro classes do painel c, escolhidas pelos atributos e pela taxa atribuída (sem nomes fixos)."""
    lam = pl.read_parquet(atlas_dir() / "atribuicao_celular_2025.parquet")
    perfil = pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")
    com = perfil.filter(pl.col("familia") == "comercio")["nome"].to_list()
    top_com = lam.filter(pl.col("classe").is_in(com)).sort("lambda", descending=True)["classe"].to_list()
    cand = [R.tipo_por_familia("res_horizontal", "padrao_baixo"), "Favela (FCU)", top_com[0] if top_com else None, "n_trilho"]
    ok = set(rv["classe"].to_list())
    return [c for c in cand if c in ok]


def panel_crowd(fig, x, y, w, h, rv: pl.DataFrame, classes: list[str], curto: dict, cols: dict):
    axes = []
    for i, c in enumerate(classes):
        r = rv.filter(pl.col("classe") == c)
        ax = ax_mm(fig, x + (i % 2) * (w / 2 + 3), y + (i // 2) * (h / 2 + 4), w / 2 - 3, h / 2 - 4)
        if r.height:
            cr = np.array([r[f"crime_h{j:02d}"][0] for j in range(24)]) * 100
            ru = np.array([r[f"rua_h{j:02d}"][0] for j in range(24)]) * 100
            ax.fill_between(range(24), ru, color="#D9D9D9", lw=0, step="mid")
            ax.plot(range(24), cr, color=cols.get(c, S.INK), lw=1.0, drawstyle="steps-mid")
        ax.set_title(curto.get(c, c), fontsize=5.5, loc="left", pad=1.5)
        ax.set_xticks([0, 6, 12, 18])
        ax.set_xlim(-0.5, 23.5)
        ax.set_ylim(bottom=0)
        if i % 2 == 0:
            ax.set_ylabel("% of the day", fontsize=5.5)
        if i // 2 == 1:
            ax.set_xlabel("Hour (weekdays)", fontsize=5.5)
        axes.append(ax)
    if axes:
        axes[0].text(0.98, 0.95, "robbery (model)", color=S.INK, fontsize=5, ha="right", va="top", transform=axes[0].transAxes)
        axes[0].text(0.98, 0.80, "pedestrians", color="#8C8C8C", fontsize=5, ha="right", va="top", transform=axes[0].transAxes)
    return axes


def panel_risk_hour(ax, rh: pl.DataFrame, var: str = VARIANTE):
    h = rh["hora"].to_numpy()
    r = rh[f"risco_{var}"].to_numpy()
    lo, hi = rh[f"risco_{var}_ic_inf"].to_numpy(), rh[f"risco_{var}_ic_sup"].to_numpy()
    ped = rh[f"rua_{var}"].to_numpy() / rh[f"rua_{var}"].to_numpy().max()
    ax2 = ax.twinx()
    ax2.fill_between(h, ped, color="#EDEDED", lw=0, step="mid", zorder=0)
    ax2.set_ylim(0, 1.05)
    ax2.set_yticks([])
    ax2.spines["right"].set_visible(False)
    ax.set_zorder(ax2.get_zorder() + 1)
    ax.patch.set_visible(False)
    ax.fill_between(h, lo, hi, color="#5B9BD5", alpha=0.45, lw=0, step="mid")
    ax.plot(h, r, color="#264653", lw=1.0, drawstyle="steps-mid")
    ax.axhline(1, color=S.INK, lw=0.5)
    ax.set_yscale("log")
    ymin, ymax = max(min(np.nanmin(lo), np.nanmin(r)) * 0.8, 0.01), max(np.nanmax(hi), np.nanmax(r)) * 1.25
    ax.set_ylim(ymin, ymax)
    _plain_log(ax.yaxis, _log_ticks(ymin, ymax))
    ax.set_xticks([0, 6, 12, 18, 23])
    ax.set_xlim(-0.5, 23.5)
    ax.set_xlabel("Hour of day (weekdays)")
    ax.set_ylabel("Robbery risk per pedestrian\n(relative to daily mean)")
    ax.text(0.98, 0.97, "grey: pedestrians on the street", transform=ax.transAxes, fontsize=5, color="#8C8C8C", ha="right", va="top")


def panel_weekend(ax, fds: dict, rows: list[str], curto: dict):
    # só classes com estimativa informativa: razão e intervalo dentro de [0,05; 20] (classes quase sem crime ficam de fora)
    ok = lambda v: v and all(np.isfinite(x) and 0.05 <= x <= 20 for x in (v["razao"], *v["ic"]))  # noqa: E731
    fds = {d: {c: v for c, v in fds.get(d, {}).items() if ok(v)} for d in CRIME_COR}
    nos_dados = list(dict.fromkeys(c for d in CRIME_COR for c in fds.get(d, {})))
    rows = [c for c in rows if c in nos_dados] + [c for c in nos_dados if c not in rows]  # classes fora da ordem vão ao fim
    x = np.arange(len(rows))
    allv = []
    for d, dx, mk in (("celular_furto", -0.17, "s"), ("celular_roubo", 0.17, "o")):
        c = CRIME_COR[d]
        for i, r in enumerate(rows):
            v = fds.get(d, {}).get(r)
            if v is None:
                continue
            ax.plot([i + dx, i + dx], v["ic"], color=c, lw=0.7, alpha=0.8)
            allv += [v["razao"], *v["ic"]]
        ax.scatter([i + dx for i, r in enumerate(rows) if r in fds.get(d, {})],
                   [fds[d][r]["razao"] for r in rows if r in fds.get(d, {})], s=9, color=c, marker=mk, zorder=3,
                   label=N.CRIME_EN[d], edgecolor="white", linewidth=0.3)
    ax.axhline(1, color=S.INK, lw=0.5)
    ax.set_yscale("log")
    allv = np.asarray([v for v in allv if v and np.isfinite(v) and v > 0])
    lo, hi = (allv.min() * 0.85, allv.max() * 1.15) if allv.size else (0.3, 3)
    ax.set_ylim(lo, hi)
    _plain_log(ax.yaxis, _log_ticks(lo, hi))
    ax.set_xticks(x)
    ax.set_xticklabels([curto.get(r, r) for r in rows], rotation=50, ha="right", rotation_mode="anchor", fontsize=5)
    ax.set_xlim(-0.6, len(rows) - 0.4)
    ax.set_ylabel("Weekend / weekday\n(rate per day)")
    ax.legend(loc="upper left", fontsize=5, ncol=2, handletextpad=0.1, columnspacing=0.8, borderaxespad=0.1)
    ax.grid(True, axis="y", color="#F0F0F0", lw=0.4)
    ax.set_axisbelow(True)


def panel_per_person(ax, rp: pl.DataFrame, curto: dict, cols: dict, pres: dict, destaque: list[str], var: str = VARIANTE):
    d = rp.filter(pl.col("variante") == var).group_by("classe").agg(pl.col("lambda_km").sum(), pl.col("rho_pessoa").sum())
    d = d.filter(~pl.col("classe").str.starts_with("n_") & (pl.col("lambda_km") > 0) & (pl.col("rho_pessoa") > 0))
    d = d.filter(pl.col("lambda_km") >= 1e-3 * d["lambda_km"].max())  # classes quase sem roubo não informam a razão
    x = d["lambda_km"].to_numpy()
    y = d["rho_pessoa"].to_numpy()
    cls = d["classe"].to_list()
    ax.scatter(x, y, s=12, c=[cols.get(c, "#888888") for c in cls], edgecolor="white", linewidth=0.3, zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    sub = pres.get("subida_no_ranking", {})
    marcar = {c for c in destaque if c.startswith(("Favela", "rua_"))}  # poucos rótulos: o painel é estreito
    if sub:
        s = {k: float(v) for k, v in sub.items() if k in cls}
        if s:
            marcar |= {max(s, key=s.get)} | ({"Vertical residencial e misto"} & set(cls))
    if len(x):
        lx0, lx1 = np.log(x.min()) - 0.3, np.log(x.max()) + 0.3
        ax.set_xlim(np.exp(lx0), np.exp(lx1))
        ax.set_ylim(y.min() / 1.6, y.max() * 1.6)
        ax.set_xlim(np.exp(lx0), np.exp(lx1 + 0.9))  # folga à direita para os rótulos
    place_labels(ax, x, y, [curto.get(c, c) if c in marcar else None for c in cls], fontsize=5)
    ax.set_xlabel("Robbery per km (weekdays)")
    ax.set_ylabel("Robbery per pedestrian (relative)")
    rho = pres.get("spearman_km_vs_pedestre")
    ic = pres.get("bootstrap", {}).get("spearman_ic95")
    if rho is not None:
        txt = f"Spearman ρ = {float(rho):.2f}" + (f"\n(95% CI {ic[0]:.2f}–{ic[1]:.2f})" if ic else "")
        ax.set_title(txt.replace("\n", " "), fontsize=5.2, loc="left", pad=2)


def make(periodo: str = "dev"):
    check_periodo(periodo)
    fd, od = atlas_dir() / "fenotipo", atlas_dir() / "presenca_2023"
    h = pl.read_parquet(fd / "relogio_horas_roubo_celular.parquet")
    rel = json.loads((fd / "relogio.json").read_text())
    per = pl.read_parquet(fd / "relogio_periodos.parquet")
    rq = json.loads((fd / "ritmo_queda.json").read_text()) if (fd / "ritmo_queda.json").exists() else {}
    blocos = rq.get("relogio_blocos", {})
    fds = {d: v.get("classes", {}) for d, v in rq.get("relogio_ic", {}).get("fim_de_semana", {}).items() if isinstance(v, dict)}
    if not fds:  # sem intervalos: só os pontos do relógio
        fds = {d: {c: {"razao": r, "ic": [r, r]} for c, r in v.items()} for d, v in rel.get("fim_de_semana", {}).items()}
    rv = pl.read_parquet(od / "relogio_vs_rua.parquet").filter(pl.col("variante") == VARIANTE)
    rh = pl.read_parquet(od / "risco_hora_cidade.parquet")
    rp = pl.read_parquet(od / "risco_por_pessoa.parquet")
    pres = json.loads((od / "presenca_2023.json").read_text())["2023"][VARIANTE]
    _, _, _, longo, curto = R.classes()
    cols = R.cores()
    dest = destaques(rv)

    fig = S.figure(S.DOUBLE, 200)
    # a — teste pré-especificado
    lim = 0.0
    for d in CRIME_COR:
        for x, y in _desvios(per, d).values():
            if len(x):
                lim = max(lim, np.abs(x).max(), np.abs(y).max())
    lim = float(np.ceil(lim * 1.1 / 5) * 5) or 10.0
    a1 = ax_mm(fig, 13, 9, 33, 33)
    panel_replica(a1, per, rel, "celular_furto", lim, "Phone theft (pre-specified test)")
    a2 = ax_mm(fig, 60, 9, 33, 33)
    panel_replica(a2, per, rel, "celular_roubo", lim, "Phone robbery")
    a2.set_ylabel("")
    a2.legend(loc="upper left", fontsize=5, handletextpad=0.05, borderaxespad=0.1, labelspacing=0.2, markerscale=1.2,
              title="Period", title_fontsize=5)
    a3 = ax_mm(fig, 122, 6, 58, 36)
    panel_nulos(a3, rel, blocos)
    a3.set_title("Contrast against three permutation nulls", fontsize=5.5, loc="left", pad=2)
    S.fig_label(fig, "a", 1, 2)
    # b — exploratório: perfil horário por classe
    b = ax_mm(fig, 34, 70, 58, 58)
    im = panel_heat(b, h, curto, cols)
    b.set_title("Exploratory: phone robbery by hour, per class (model)", fontsize=5.5, loc="left", pad=2)
    S.fig_label(fig, "b", 1, 66)
    cb = ax_mm(fig, 94, 74, 2.0, 24)
    c1 = fig.colorbar(im, cax=cb)
    c1.set_label("% of the class's robberies", fontsize=5)
    c1.ax.tick_params(labelsize=5, length=1.5)
    # c — roubo × pedestres
    panel_crowd(fig, 120, 72, 62, 58, rv, dest, curto, cols)
    S.fig_label(fig, "c", 110, 66)
    # d, e, f
    d_ = ax_mm(fig, 15, 146, 38, 30)
    panel_risk_hour(d_, rh)
    S.fig_label(fig, "d", 1, 141)
    e = ax_mm(fig, 70, 146, 60, 30)
    panel_weekend(e, fds, R.ordem_linhas(), curto)
    S.fig_label(fig, "e", 60, 141)
    f = ax_mm(fig, 146, 146, 36, 30)
    panel_per_person(f, rp, curto, cols, pres, dest)
    S.fig_label(fig, "f", 135, 141)
    return S.save(fig, "fig4", periodo)
