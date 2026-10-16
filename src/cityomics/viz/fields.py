"""Campo vetorial do sinal no estilo COMMOT (Fig. 3f).

Para um par ligante → receptor, cada setor recebe um vetor que aponta na direção de onde vem o sinal
ponderado: v_i = R_i · Σ_j K_ij · L_j · (x_i − x_j)/|x_i − x_j|. O campo é interpolado numa grade e
desenhado com ``streamplot`` sobre o fundo escuro; a cor e a espessura seguem a intensidade.
"""

from __future__ import annotations

import numpy as np


def signal_field(xy: np.ndarray, L: np.ndarray, R: np.ndarray, K) -> tuple[np.ndarray, np.ndarray]:
    Kc = K.tocoo()
    m = Kc.row != Kc.col
    i, j, w = Kc.row[m], Kc.col[m], Kc.data[m]
    d = xy[i] - xy[j]
    nrm = np.linalg.norm(d, axis=1)
    nrm[nrm == 0] = 1.0
    u = d / nrm[:, None]
    contrib = (w * L[j])[:, None] * u
    V = np.zeros_like(xy, dtype=float)
    np.add.at(V, i, contrib)
    V *= R[:, None]
    mag = np.linalg.norm(V, axis=1)
    return V, mag


def to_grid(xy: np.ndarray, V: np.ndarray, bounds, n: int = 220):
    from scipy.interpolate import griddata

    x0, y0, x1, y1 = bounds
    gx = np.linspace(x0, x1, n)
    gy = np.linspace(y0, y1, int(n * (y1 - y0) / (x1 - x0)))
    GX, GY = np.meshgrid(gx, gy)
    U = griddata(xy, V[:, 0], (GX, GY), method="linear")
    W = griddata(xy, V[:, 1], (GX, GY), method="linear")
    return gx, gy, np.nan_to_num(U), np.nan_to_num(W)


def stream(ax, gx, gy, U, W, cmap, density: float = 1.6, lw_max: float = 1.1):
    M = np.hypot(U, W)
    mx = np.nanpercentile(M[M > 0], 98) if (M > 0).any() else 1.0
    lw = 0.15 + lw_max * np.clip(M / mx, 0, 1)
    return ax.streamplot(gx, gy, U, W, color=np.clip(M / mx, 0, 1), cmap=cmap, linewidth=lw, density=density,
                         arrowsize=0.35, arrowstyle="-|>", minlength=0.08, zorder=3)
