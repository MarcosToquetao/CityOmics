"""Converte um .py com blocos ``# %%`` / ``# %% [markdown]`` em .ipynb (sem dependências)."""
import json
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text().split("\n")
cells, cur, kind = [], [], None


def flush():
    global cur, kind
    body = "\n".join(cur).strip("\n")
    if body and kind:
        if kind == "markdown":
            body = "\n".join(l[2:] if l.startswith("# ") else l.lstrip("#") for l in body.split("\n"))
            cells.append({"cell_type": "markdown", "metadata": {}, "source": body.splitlines(True)})
        else:
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": body.splitlines(True)})
    cur = []


for line in src:
    if line.startswith("# %%"):
        flush()
        kind = "markdown" if "[markdown]" in line else "code"
    elif kind is None:
        continue          # docstring de cabeçalho fica fora das células
    else:
        cur.append(line)
flush()
nb = {"cells": cells, "metadata": {"accelerator": "GPU", "colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"}},
      "nbformat": 4, "nbformat_minor": 5}
out = Path(sys.argv[1]).with_suffix(".ipynb")
out.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
print(out, len(cells), "células")
