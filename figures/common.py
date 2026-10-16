"""Utilidades comuns aos roteiros das figuras: período, eixos em mm e textos."""

from __future__ import annotations

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
