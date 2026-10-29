"""Auditoria de layout das figuras: texto sobre texto, texto sobre outro painel, texto fora da tela e dados cortados.

Chamada por ``style.save`` antes de gravar. Cada achado vira uma linha em
``figures/out/<periodo>/layout_audit.json`` e é impresso; com ``CITYOMICS_FIG_STRICT=1`` a geração falha.

- Textos girados são comparados pelo retângulo girado (não pela caixa alinhada aos eixos, que acusaria falsos
  choques entre rótulos inclinados vizinhos).
- "Outro painel" é a área de um eixo diferente do eixo dono do texto; textos da figura (letras de painel) contam
  como sem dono.
- "Dados cortados" são barras de erro e linhas cujos valores passam dos limites do eixo.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.text import Text
from shapely.geometry import Polygon, box

TOL_PX = 1.0  # sobreposições menores que isto (em px a 150 dpi) são ignoradas


def _poly(t: Text, r) -> Polygon | None:
    bb = t.get_window_extent(r)
    if bb.width <= 0 or bb.height <= 0:
        return None
    rot = t.get_rotation() % 180
    if rot in (0, 90) or abs(rot - 90) < 1e-6:
        return box(bb.x0, bb.y0, bb.x1, bb.y1)
    old = t.get_rotation()
    t.set_rotation(0)
    b0 = t.get_window_extent(r)
    t.set_rotation(old)
    w, h = b0.width, b0.height
    cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
    a = math.radians(old)
    ca, sa = math.cos(a), math.sin(a)
    pts = [(cx + dx * ca - dy * sa, cy + dx * sa + dy * ca) for dx, dy in
           ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return Polygon(pts)


def _texts(fig, r):
    """(texto, eixo dono, polígono) de todo texto visível e não vazio."""
    out = []

    def add(t, owner):
        if t is None or not t.get_visible() or not t.get_text().strip() or (t.get_alpha() == 0):
            return
        p = _poly(t, r)
        if p is not None and p.area > 0:
            out.append((t, owner, p))

    for ax in fig.axes:
        if not ax.get_visible():
            continue
        axbb = ax.get_window_extent(r)
        for axis, along in ((ax.xaxis, "x"), (ax.yaxis, "y")) if ax.axison else ():
            if not axis.get_visible():
                continue
            for t in axis.get_majorticklabels() + axis.get_minorticklabels():
                if not t.get_visible() or not t.get_text().strip():
                    continue
                bb = t.get_window_extent(r)
                c = (bb.x0 + bb.x1) / 2 if along == "x" else (bb.y0 + bb.y1) / 2
                lo, hi = (axbb.x0, axbb.x1) if along == "x" else (axbb.y0, axbb.y1)
                if lo - 2 <= c <= hi + 2:  # marcas fora da vista não são desenhadas
                    add(t, ax)
            add(axis.label, ax)
            add(axis.get_offset_text(), ax)
        for t in (ax.title, ax._left_title, ax._right_title):
            add(t, ax)
        for t in ax.texts:
            add(t, ax)
        leg = ax.get_legend()
        if leg is not None and leg.get_visible():
            for t in leg.get_texts():
                add(t, ax)
            add(leg.get_title(), ax)
    for t in fig.texts:
        add(t, None)
    for leg in fig.legends:
        for t in leg.get_texts():
            add(t, None)
    return out


def _clipped(ax) -> int:
    """Quantos segmentos de linhas e barras de erro passam dos limites do eixo (com tolerância de 0,5%)."""
    x0, x1 = sorted(ax.get_xlim())
    y0, y1 = sorted(ax.get_ylim())
    tx = (x1 - x0) * 0.005
    ty = (y1 - y0) * 0.005
    if ax.get_xscale() == "log" or ax.get_yscale() == "log":
        tx = ty = 0.0
    n = 0
    for coll in ax.collections:
        if isinstance(coll, LineCollection) and coll.get_visible() and coll.get_clip_on():
            for seg in coll.get_segments():
                s = np.asarray(seg)
                if s.size and (np.nanmin(s[:, 0]) < x0 - tx or np.nanmax(s[:, 0]) > x1 + tx
                               or np.nanmin(s[:, 1]) < y0 - ty or np.nanmax(s[:, 1]) > y1 + ty):
                    n += 1
    for ln in ax.lines:
        if not isinstance(ln, Line2D) or not ln.get_visible() or not ln.get_clip_on():
            continue
        if ln.get_transform() != ax.transData:
            continue
        xd = np.asarray(ln.get_xdata(), dtype=float)
        yd = np.asarray(ln.get_ydata(), dtype=float)
        if xd.size < 2 or xd.size > 200:  # linhas longas (curvas, eixos de referência) ficam de fora
            continue
        if (np.nanmin(yd) < y0 - ty or np.nanmax(yd) > y1 + ty) and (np.nanmin(xd) >= x0 - tx and np.nanmax(xd) <= x1 + tx):
            n += 1
    return n


def audit(fig, name: str = "") -> list[dict]:
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.canvas.get_width_height()
    figbox = box(-TOL_PX, -TOL_PX, W + TOL_PX, H + TOL_PX)
    items = _texts(fig, r)
    axes = [(ax, box(*ax.get_window_extent(r).extents)) for ax in fig.axes if ax.get_visible()]
    found = []

    def rec(kind, a, b=None):
        found.append({"figura": name, "tipo": kind, "texto": a[:60], "outro": (b or "")[:60]})

    for t, owner, p in items:
        if not figbox.contains(p):
            rec("fora da tela", t.get_text())
        for ax, abox in axes:
            if ax is owner or owner is None and ax.get_label() == "<colorbar>":
                continue
            # o texto pode invadir outro painel; legenda e anotação dentro do próprio eixo não contam
            if owner is not None and (ax in owner.child_axes or owner in getattr(ax, "child_axes", [])):
                continue
            inter = p.intersection(abox).area
            if inter > 4 * TOL_PX ** 2 and inter > 0.15 * p.area:
                if owner is None and ax.get_facecolor()[:3] != (1.0, 1.0, 1.0):
                    continue  # letras e rótulos de figura sobre mapas escuros são intencionais
                rec("texto sobre outro painel", t.get_text(), ax.get_title() or ax.get_ylabel() or ax.get_xlabel() or "eixo")
    for i in range(len(items)):
        ti, _, pi = items[i]
        for j in range(i + 1, len(items)):
            tj, _, pj = items[j]
            if not pi.intersects(pj):
                continue
            inter = pi.intersection(pj).area
            if ti.get_text() == tj.get_text() and inter > 0.8 * min(pi.area, pj.area):
                continue  # o mesmo texto desenhado duas vezes (eixos gêmeos ou compartilhados)
            if inter > 4 * TOL_PX ** 2 and inter > 0.05 * min(pi.area, pj.area):
                rec("texto sobre texto", ti.get_text(), tj.get_text())
    for ax, _ in axes:
        if not len(ax.get_xticks()) and not len(ax.get_yticks()):
            continue  # mapas: o recorte das geometrias é intencional
        n = _clipped(ax)
        if n:
            rec("dados cortados no eixo", f"{n} segmento(s)", ax.get_title() or ax.get_ylabel() or "eixo")
    return found


def report(fig, name: str, out_dir: Path) -> list[dict]:
    found = audit(fig, name)
    f = out_dir / "layout_audit.json"
    todos = json.loads(f.read_text()) if f.exists() else {}
    todos[name] = found
    f.write_text(json.dumps(todos, ensure_ascii=False, indent=1))
    for x in found:
        print(f"  [layout] {name}: {x['tipo']}: {x['texto']!r} × {x['outro']!r}")
    if found and os.environ.get("CITYOMICS_FIG_STRICT") == "1":
        raise RuntimeError(f"{name}: {len(found)} problema(s) de layout")
    return found
