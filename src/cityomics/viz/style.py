"""Estilo Nature (D36, D45, D46): medidas em mm, fontes de 5–7 pt, letras de painel de 8 pt.

- ``apply()`` fixa os rcParams (Type 42, Arial ou Liberation Sans, linhas de 0,5 pt).
- ``figure(width_mm, height_mm)`` cria a figura no tamanho final.
- ``panel_label(ax, "a")`` põe a letra em negrito minúsculo no canto superior esquerdo.
- ``dark(ax)`` deixa um eixo de mapa em fundo escuro, sem molduras (cara de microscopia).
- ``save(fig, name, periodo)`` grava PDF (vetorial, fontes embutidas) e PNG de 450 dpi em
  ``figures/out/<periodo>/``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager

from cityomics.paths import REPO_ROOT

MM = 1 / 25.4
SINGLE, ONE_HALF, DOUBLE = 89, 120, 183
MAX_H = 247
DARK_BG = "#0B0B0E"
INK = "#1A1A1A"
MUTED = "#6B6B6B"
GRID = "#E3E3E3"
FONT_SIZES = {"small": 5.5, "base": 6.0, "large": 7.0, "label": 8.0}
FONT_MIN = 5.0  # piso do padrão Nature (D36; spec-figuras §9), aplicado em save()


def font_family() -> str:
    names = {f.name for f in font_manager.fontManager.ttflist}
    for f in ("Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"):
        if f in names:
            return f
    return "sans-serif"


def apply() -> None:
    fam = font_family()
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [fam, "DejaVu Sans"],
        "font.size": FONT_SIZES["base"], "axes.titlesize": FONT_SIZES["large"], "axes.labelsize": FONT_SIZES["base"],
        "xtick.labelsize": FONT_SIZES["small"], "ytick.labelsize": FONT_SIZES["small"], "legend.fontsize": FONT_SIZES["small"],
        "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4, "xtick.major.size": 2.0, "ytick.major.size": 2.0, "lines.linewidth": 0.8,
        "patch.linewidth": 0.5, "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
        "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 450, "figure.dpi": 150,
        "axes.titleweight": "normal", "axes.titlepad": 3.0, "axes.labelpad": 2.0, "xtick.major.pad": 1.5,
        "ytick.major.pad": 1.5, "image.interpolation": "nearest",
    })


def figure(width_mm: float = DOUBLE, height_mm: float = 120.0):
    apply()
    return plt.figure(figsize=(width_mm * MM, height_mm * MM))


def panel_label(ax, letter: str, dx: float = -0.02, dy: float = 1.02, color: str = INK) -> None:
    ax.text(dx, dy, letter, transform=ax.transAxes, fontsize=FONT_SIZES["label"], fontweight="bold",
            va="bottom", ha="right", color=color)


def fig_label(fig, letter: str, x_mm: float, y_mm_from_top: float, color: str = INK) -> None:
    w, h = fig.get_size_inches() / MM
    fig.text(x_mm / w, 1 - y_mm_from_top / h, letter, fontsize=FONT_SIZES["label"], fontweight="bold",
             va="top", ha="left", color=color)


def dark(ax) -> None:
    ax.set_facecolor(DARK_BG)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])


def clean(ax, grid: bool = False) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(True, color=GRID, linewidth=0.4)
        ax.set_axisbelow(True)


def out_dir(periodo: str) -> Path:
    d = REPO_ROOT / "figures" / "out" / periodo
    d.mkdir(parents=True, exist_ok=True)
    return d


def plain_log_ticks(fig) -> None:
    """Marcas de eixos log em números simples (0.01, 1, 100): os expoentes em mathtext saem com 70% do corpo (< 5 pt)."""
    from matplotlib.ticker import FuncFormatter, LogFormatter, NullFormatter

    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if axis.get_scale() == "log" and isinstance(axis.get_major_formatter(), LogFormatter):
                axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}".replace("-", "−")))
                axis.set_minor_formatter(NullFormatter())


def enforce_min_font(fig, minimum: float = FONT_MIN) -> int:
    """Sobe para ``minimum`` todo texto menor (rótulos, ticks, legendas, anotações). Devolve quantos mudaram.

    Desenha a figura antes, para alcançar as marcas criadas no desenho (barras de cor), e fixa o corpo das
    marcas no próprio eixo, para que não voltem ao tamanho antigo quando forem recriadas ao salvar.
    """
    from matplotlib.text import Text

    fig.canvas.draw()
    n = 0
    for ax in fig.axes:
        for which, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
            labs = [t for t in axis.get_ticklabels() if t.get_text().strip()]
            if labs and min(t.get_fontsize() for t in labs) < minimum:
                ax.tick_params(axis=which, labelsize=minimum)
                n += 1
    for t in fig.findobj(Text):
        if t.get_text().strip() and t.get_fontsize() < minimum:
            t.set_fontsize(minimum)
            n += 1
    return n


def save(fig, name: str, periodo: str = "dev", png: bool = True) -> Path:
    from cityomics.viz import layout_audit

    plain_log_ticks(fig)
    enforce_min_font(fig)
    d = out_dir(periodo)
    layout_audit.report(fig, name, d)
    pdf = d / f"{name}.pdf"
    fig.savefig(pdf, facecolor=fig.get_facecolor())
    if png:
        fig.savefig(d / f"{name}.png", dpi=450, facecolor=fig.get_facecolor())
    plt.close(fig)
    return pdf
