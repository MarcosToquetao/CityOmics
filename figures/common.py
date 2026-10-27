"""Utilidades comuns aos roteiros das figuras: período, eixos em mm e textos."""

from __future__ import annotations

import numpy as np

from cityomics.viz.style import MM


def check_periodo(periodo: str) -> None:
    """``dev`` usa 2025; ``2026`` só com o cofre aberto e o pacote congelado (D52)."""
    if periodo == "dev":
        return
    if periodo == "2026":
        from cityomics import sealed

        sealed.require_unsealed("figuras do teste de 2026")
        return
    raise ValueError(f"período desconhecido: {periodo}")


def ax_mm(fig, x: float, y_top: float, w: float, h: float, **kw):
    """Eixo posicionado em mm a partir do canto superior esquerdo da figura."""
    W, H = fig.get_size_inches() / MM
    return fig.add_axes([x / W, 1 - (y_top + h) / H, w / W, h / H], **kw)


def short(n: float, digits: int = 2) -> str:
    return f"{n:.{digits}f}".replace("-", "−")


def row_swatches(ax, colors: list[str], w_mm: float = 1.8, gap_mm: float = 0.6, h: float = 0.76, axis: str = "y") -> None:
    """Quadradinhos de cor à esquerda das linhas (eixo y em coordenadas de dados) e rótulos afastados deles."""
    import matplotlib.patches as mpatches
    from matplotlib.transforms import blended_transform_factory

    fig = ax.figure
    W = ax.get_position().width * fig.get_size_inches()[0] / MM
    tr = blended_transform_factory(ax.transAxes, ax.transData)
    x0 = -(w_mm + gap_mm) / W
    for i, c in enumerate(colors):
        ax.add_patch(mpatches.Rectangle((x0, i - h / 2), w_mm / W, h, color=c, transform=tr, clip_on=False))
    ax.tick_params(axis=axis, length=0, pad=(w_mm + 2 * gap_mm) * 72 / 25.4)


def place_labels(ax, xs, ys, texts, fontsize: float = 5.0, pad_pt: float = 2.5, point_pt: float = 3.0, **kw) -> list:
    """Rótulos junto dos pontos sem sobreposição: tenta oito posições e fica com a primeira livre.

    Evita os outros rótulos já postos, todos os pontos (``xs``, ``ys``) e as bordas do eixo. Se nenhuma
    posição estiver livre, usa a que menos sobrepõe.
    """
    from matplotlib.transforms import Bbox

    fig = ax.figure
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    to_px = ax.transData.transform
    pts = to_px(np.column_stack([xs, ys])) if len(xs) else np.zeros((0, 2))
    k = fig.dpi / 72
    pboxes = [Bbox.from_extents(x - point_pt * k, y - point_pt * k, x + point_pt * k, y + point_pt * k) for x, y in pts]
    axbox = ax.get_window_extent(r)
    placed, out = [], []
    cand = [(-1, 0, "right", "center"), (1, 0, "left", "center"), (-1, 1, "right", "bottom"), (-1, -1, "right", "top"),
            (1, 1, "left", "bottom"), (1, -1, "left", "top"), (0, 1, "center", "bottom"), (0, -1, "center", "top")]
    for i, (x, y, t) in enumerate(zip(xs, ys, texts)):
        if t is None:
            continue
        best, best_cost = None, None
        for dx, dy, ha, va in cand:
            f = 1.0 if dy == 0 else 2.2  # nas diagonais, mais longe e com um fio até o ponto
            txt = ax.annotate(t, (x, y), xytext=(dx * pad_pt * f, dy * pad_pt * f), textcoords="offset points", ha=ha,
                              va=va, fontsize=fontsize,
                              arrowprops=dict(arrowstyle="-", lw=0.3, color="#9A9A9A", shrinkA=0, shrinkB=2.5) if dy else None,
                              **kw)
            bb = txt.get_window_extent(r)
            cost = sum(bb.overlaps(b) for b in placed) * 10 + sum(bb.overlaps(b) for j, b in enumerate(pboxes) if j != i)
            cost += 20 * (bb.x0 < axbox.x0 or bb.x1 > axbox.x1 or bb.y0 < axbox.y0 or bb.y1 > axbox.y1)
            if best_cost is None or cost < best_cost:
                if best is not None:
                    best[0].remove()
                best, best_cost = (txt, bb), cost
            else:
                txt.remove()
            if cost == 0:
                break
        placed.append(best[1])
        out.append(best[0])
    return out
