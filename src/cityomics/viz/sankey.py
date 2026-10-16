"""Sankey de massa conservada (D47, D57), desenhado à mão com fitas de Bézier.

Três colunas: origens (identidade da classe, grupos teóricos e efeito espacial) → classes de
célula → desfecho. Cada fita tem largura proporcional ao crime esperado. As reduções (contribuições
líquidas negativas) saem das classes para um sumidouro hachurado, de modo que a massa fecha em cada
nó: entrada = identidade + aumentos = saída para o desfecho + reduções.
"""

from __future__ import annotations

import numpy as np
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle


def _ribbon(ax, x0, y0a, y0b, x1, y1a, y1b, color, alpha=0.55, hatch=None, z=1):
    xm = (x0 + x1) / 2
    verts = [(x0, y0a), (xm, y0a), (xm, y1a), (x1, y1a), (x1, y1b), (xm, y1b), (xm, y0b), (x0, y0b), (x0, y0a)]
    codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color if not hatch else "none", edgecolor=color if hatch else "none",
                           lw=0.0 if not hatch else 0.3, alpha=alpha, hatch=hatch, zorder=z))


def draw(ax, left: list[tuple[str, str]], mid: list[tuple[str, str]], right: list[tuple[str, str]],
         flows: list[tuple[str, str, float]], sink: tuple[str, str] | None = None, xs=(0.0, 0.46, 0.92), w=0.035,
         gap=0.018, label_left=True, fontsize=5.2):
    """``left/mid/right``: listas (nome, cor) na ordem de cima para baixo; ``flows``: (origem, destino, valor).
    Valores negativos não entram; reduções devem chegar como fluxos para ``sink``."""
    cols = [dict(left), dict(mid), dict(right) | ({sink[0]: sink[1]} if sink else {})]
    names = [[n for n, _ in left], [n for n, _ in mid], [n for n, _ in right] + ([sink[0]] if sink else [])]
    col_of = {n: i for i, ns in enumerate(names) for n in ns}
    out_tot = {n: 0.0 for ns in names for n in ns}
    in_tot = {n: 0.0 for ns in names for n in ns}
    for s, d, v in flows:
        out_tot[s] += v
        in_tot[d] += v
    size = {n: max(out_tot[n], in_tot[n]) for n in out_tot}
    total = max(sum(size[n] for n in ns) for ns in names)
    scale = (1 - gap * (max(len(ns) for ns in names) - 1)) / total
    pos = {}
    for i, ns in enumerate(names):
        hsum = sum(size[n] for n in ns) * scale + gap * (len(ns) - 1)
        y = 1 - (1 - hsum) / 2
        for n in ns:
            h = size[n] * scale
            pos[n] = (y - h, y)
            y -= h + gap
    cur_out = {n: pos[n][1] for n in pos}
    cur_in = {n: pos[n][1] for n in pos}
    for s, d, v in sorted(flows, key=lambda f: (names[col_of[f[0]]].index(f[0]), names[col_of[f[1]]].index(f[1]))):
        h = v * scale
        i, j = col_of[s], col_of[d]
        y0a, y0b = cur_out[s], cur_out[s] - h
        y1a, y1b = cur_in[d], cur_in[d] - h
        cur_out[s] -= h
        cur_in[d] -= h
        is_sink = sink is not None and d == sink[0]
        color = cols[i].get(s) if i == 0 else cols[i].get(s)
        _ribbon(ax, xs[i] + w, y0a, y0b, xs[j], y1a, y1b, "#9A9A9A" if is_sink else color,
                alpha=0.35 if is_sink else 0.5, hatch="//////" if is_sink else None)
    for i, ns in enumerate(names):
        for n in ns:
            y0, y1 = pos[n]
            ax.add_patch(Rectangle((xs[i], y0), w, y1 - y0, color=cols[i][n], lw=0, zorder=3))
            if i == 0 and label_left:
                ax.text(xs[i] - 0.01, (y0 + y1) / 2, n, ha="right", va="center", fontsize=fontsize)
            elif i == 1:
                ax.text(xs[i] + w + 0.008, (y0 + y1) / 2, n, ha="left", va="center", fontsize=fontsize - 0.2, zorder=4)
            elif i == 2:
                ax.text(xs[i] + w + 0.01, (y0 + y1) / 2, n, ha="left", va="center", fontsize=fontsize)
    ax.set_xlim(-0.02, 1.0)
    ax.set_ylim(-0.02, 1.02)
    ax.axis("off")
    return pos, scale
