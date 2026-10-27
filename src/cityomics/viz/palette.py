"""Paleta semântica (D45; spec-figuras §4).

Cada família de tipo tem uma cor-base com variante clara (gráficos em fundo branco) e escura
(mapas em fundo escuro). Quando o Leiden encontra vários tipos na mesma família, eles recebem tons
da mesma família, do mais claro ao mais escuro, por ordem de padrão e de verticalização.
"""

from __future__ import annotations

import colorsys

import numpy as np

from cityomics.viz.names import GROUP_EN

FAMILIAS = {
    #                  clara      escura (mapa)
    "res_horizontal": ("#9CC3E6", "#4F86C6"),
    "res_vertical_medio": ("#3FA7B5", "#5FD0DC"),
    "res_vertical_alto": ("#1F4E89", "#B4D4FF"),
    "comercio": ("#E8743B", "#FF8A4C"),
    "servicos": ("#8E6CC2", "#B99BF0"),
    "industria": ("#8C7B6B", "#B0A190"),
    "vazio": ("#8DBF7A", "#5DBB6C"),
    "favela": ("#E3B23C", "#F5C451"),
    "sem_cadastro": ("#CFCFCF", "#3A3A40"),
}
ORDEM_FAMILIAS = list(FAMILIAS)
RUAS = {"rua_arterial_m": "#C9D6E3", "rua_coletora_m": "#8EA3B8", "rua_local_m": "#55697E"}
RUA_MAPA = "#2B3440"
ESTACAO = "#F5F5F5"
GRUPOS = {
    "atividade_rotineira": "#E8743B", "desorganizacao_social": "#8E6CC2", "cpted": "#2A9D8F",
    "mercado_imobiliario": "#C9A227", "historico_crime": "#5F6B7A", "identidade": "#B0B0B0",
    "espacial": "#7A8FA6", "contexto_temporal": "#A3A3A3", "outras_atividade": "#F2B48E",
    "outras_social": "#C4B2E2", "outras_cpted": "#92CFC6", "tamanho": "#D9D9D9", "outras": "#D0D0D0",
}
NOMES_GRUPOS_EN = GROUP_EN  # nomes centralizados em viz/names.py
FAMILIAS_MODELO = {
    "baseline": "#9E9E9E", "sismologia": "#D1495B", "epidemiologia": "#2A9D8F", "ecologia": "#6A994E",
    "astronomia": "#3D5A80", "aprendizado": "#E9C46A", "fundacao": "#8E6CC2", "decisao": "#F4A261", "ensemble": "#264653",
}
MODELO_FAMILIA = {
    "media_historica": "baseline", "glm": "baseline", "kde": "astronomia", "hawkes": "sismologia", "bym2": "epidemiologia",
    "spde": "epidemiologia", "maxent": "ecologia", "gwr_distrito": "baseline", "painel_espacial": "baseline",
    "lgbm_nucleo": "aprendizado", "lgbm_sem_crime": "aprendizado", "lgbm_completo": "aprendizado", "gnn": "aprendizado",
    "chronos": "fundacao", "laya_ft": "decisao", "ensemble": "ensemble",
}


def _shade(hexcolor: str, f: float) -> str:
    """Clareia (f > 0) ou escurece (f < 0) mantendo o matiz."""
    r, g, b = (int(hexcolor[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    l = float(np.clip(l + f * (1 - l if f > 0 else l), 0, 1))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(b * 255))


def type_colors(tipos: list[str], familias: list[str], order_key: list[float] | None = None, dark: bool = False) -> dict[str, str]:
    """Cor de cada tipo: tons da cor-base da família, espalhados entre os tipos da mesma família."""
    idx = 1 if dark else 0
    out = {}
    key = order_key if order_key is not None else [0.0] * len(tipos)
    for fam in set(familias):
        members = sorted([(k, t) for t, f, k in zip(tipos, familias, key) if f == fam])
        base = FAMILIAS.get(fam, ("#BBBBBB", "#888888"))[idx]
        n = len(members)
        for i, (_, t) in enumerate(members):
            f = 0.0 if n == 1 else np.linspace(0.35, -0.35, n)[i]
            out[t] = _shade(base, f if not dark else -f)
    return out


def ordered_types(tipos: list[str], familias: list[str], order_key: list[float] | None = None) -> list[str]:
    key = order_key if order_key is not None else [0.0] * len(tipos)
    rank = {f: i for i, f in enumerate(ORDEM_FAMILIAS)}
    return [t for _, _, t in sorted(zip([rank.get(f, 99) for f in familias], key, tipos))]


def cmap(name: str):
    """Escalas perceptualmente uniformes do cmcrameri, com fallback do matplotlib."""
    try:
        import cmcrameri.cm as cmc

        return getattr(cmc, name)
    except (ImportError, AttributeError):
        import matplotlib.pyplot as plt

        return plt.get_cmap({"batlow": "viridis", "lajolla": "magma", "vik": "RdBu_r", "lipari": "inferno",
                             "acton": "magma", "roma": "RdYlBu", "bamako": "YlGn"}.get(name, "viridis"))
