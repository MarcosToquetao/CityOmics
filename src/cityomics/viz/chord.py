"""Círculo de comunicação no estilo CellChat (Fig. 3d).

Os tipos ficam num círculo, com tamanho proporcional à abundância. Cada aresta é uma curva de
Bézier do emissor ao receptor, com largura proporcional à força agregada do sinal e a cor do emissor.
"""

from __future__ import annotations

import numpy as np
from matplotlib.patches import FancyArrowPatch


def circle(ax, names: list[str], sizes: np.ndarray, strength: np.ndarray, colors: dict, labels: dict | None = None,
           top: int = 30, max_lw: float = 3.0, fontsize: float = 5.0):
    n = len(names)
    ang = np.linspace(np.pi / 2, np.pi / 2 - 2 * np.pi, n, endpoint=False)
    xy = np.column_stack([np.cos(ang), np.sin(ang)])
    S = strength.copy()
    np.fill_diagonal(S, 0.0)
    thr = np.sort(S.ravel())[::-1][min(top, S.size) - 1] if S.max() > 0 else np.inf
    smax = S.max() if S.max() > 0 else 1.0
    for i in range(n):
        for j in range(n):
            if S[i, j] >= thr and S[i, j] > 0:
                lw = 0.25 + max_lw * S[i, j] / smax
                p = FancyArrowPatch(xy[i] * 0.92, xy[j] * 0.92, connectionstyle="arc3,rad=0.28", arrowstyle="-|>",
                                    mutation_scale=3 + 3 * S[i, j] / smax, lw=lw, color=colors[names[i]], alpha=0.65, zorder=1)
                ax.add_patch(p)
    s = 12 + 90 * sizes / sizes.max()
    ax.scatter(xy[:, 0], xy[:, 1], s=s, c=[colors[k] for k in names], edgecolor="white", linewidth=0.5, zorder=3)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.figure.canvas.draw()
    rend = ax.figure.canvas.get_renderer()
    feitos = []
    for k, (x, y), a in zip(names, xy, ang):
        ha = "left" if np.cos(a) > 0.1 else ("right" if np.cos(a) < -0.1 else "center")
        va = "bottom" if np.sin(a) > 0.1 else ("top" if np.sin(a) < -0.1 else "center")
        for r in (1.12, 1.26, 1.40, 1.54):  # afasta o rótulo do círculo até não encostar nos já postos
            t = ax.text(r * x, r * y, (labels or {}).get(k, k), ha=ha, va=va, fontsize=fontsize)
            bb = t.get_window_extent(rend)
            if not any(bb.overlaps(o) for o in feitos) or r == 1.54:
                break
            t.remove()
        feitos.append(bb)
    ax.set_xlim(-1.55, 1.55)
    ax.set_ylim(-1.35, 1.35)
    ax.set_aspect("equal")
    ax.axis("off")
