"""Versão de leitura do manuscrito em PDF, com as figuras inseridas no texto.

Cada figura principal entra logo após o parágrafo que a cita pela primeira vez, com a legenda embaixo;
as figuras do Extended Data vão para uma seção no fim. Gera paper/manuscript_figuras.pdf a partir de
paper/manuscript.md (rode antes ``python paper/build.py``). Usa o pandoc do ambiente regressao_log e o
Chrome sem interface para imprimir.

Uso: python paper/build_pdf.py
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
FIGS = HERE.parent / "figures" / "out" / "dev"
PANDOC = "/home/MarcosToquetao/miniforge3/envs/regressao_log/bin/pandoc"
CHROME = "google-chrome"

CSS = """
@page { size: A4; margin: 18mm 17mm 20mm 17mm; }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 10.5pt; line-height: 1.45; color: #111; max-width: none; }
h1 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 20pt; line-height: 1.2; margin: 0 0 6pt; }
h2 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 13pt; margin: 18pt 0 6pt; }
h3 { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; margin: 14pt 0 4pt; }
p { margin: 0 0 7pt; text-align: justify; hyphens: auto; }
sup { font-size: 7pt; line-height: 0; }
figure { margin: 12pt 0 14pt; page-break-inside: avoid; break-inside: avoid; }
figure img { max-width: 100%; max-height: 196mm; width: auto; display: block; margin: 0 auto; }
figcaption { font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 8.3pt; line-height: 1.35; margin-top: 5pt; text-align: justify; }
.refs p { font-size: 8.8pt; margin-bottom: 3pt; text-align: left; }
.abstract { font-weight: 600; }
table { border-collapse: collapse; font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 7.5pt; margin: 8pt 0 14pt; page-break-inside: avoid; }
th, td { border-top: 0.5pt solid #999; padding: 2pt 4pt; vertical-align: top; text-align: left; }
"""


def legendas(md: str, cabecalho: str) -> dict[str, str]:
    bloco = md.split(cabecalho, 1)[1]
    out = {}
    for m in re.finditer(r"^\*\*((?:Extended Data )?Fig\. (\d+)) \|(.*)$", bloco, flags=re.M):
        out[m.group(1)] = "**" + m.group(1) + " |" + m.group(3)
    return out


def figura(png: Path, legenda_md: str) -> str:
    cap = subprocess.run([PANDOC, "-f", "markdown+superscript+subscript", "-t", "html"], input=legenda_md,
                         capture_output=True, text=True, check=True).stdout.strip()
    cap = re.sub(r"^<p>|</p>$", "", cap)
    return f'\n<figure><img src="file://{png}"><figcaption>{cap}</figcaption></figure>\n'


def main() -> None:
    md = (HERE / "manuscript.md").read_text()
    leg_main = legendas(md, "## Figure legends")
    leg_ed = legendas(md, "## Extended Data figure legends")
    tabelas = md.split("## Tables", 1)[1].split("## References", 1)[0] if "## Tables" in md else ""
    corpo = md.split("## Figure legends", 1)[0]
    # Tabela 1 no fim da seção de confirmação (antes da Discussão)
    if tabelas:
        corpo = corpo.replace("\n## Discussion", "\n" + tabelas.strip() + "\n\n## Discussion", 1)

    # figuras principais: no fim da subseção que cita "Fig. N" pela primeira vez (antes do próximo título)
    paras = corpo.split("\n\n")
    feitas, pendentes, novo = set(), [], []
    for p in paras:
        if p.startswith("#") and pendentes:
            novo += [figura(FIGS / f"fig{n}.png", leg_main[f"Fig. {n}"]) for n in pendentes]
            pendentes = []
        novo.append(p)
        if p.startswith(("#", "**", "[", "^", "---")):
            continue
        for n in range(1, 7):
            if n not in feitas and re.search(rf"Figs?\. {n}(?![0-9])", p):
                feitas.add(n)
                pendentes.append(n)
    corpo = "\n\n".join(novo)
    faltam = set(range(1, 7)) - feitas
    if faltam:
        raise SystemExit(f"figuras sem citação no texto: {sorted(faltam)}")

    # Extended Data no fim, depois das referências
    ed = ["\n\n## Extended Data\n"]
    for n in range(1, 11):
        png = sorted(FIGS.glob(f"ed{n}_*.png"))[0]
        ed.append(figura(png, leg_ed[f"Extended Data Fig. {n}"]))
    corpo += "".join(ed)
    sup = HERE / "supplementary.md"
    if sup.exists():  # Informações Suplementares no fim, depois do Extended Data
        corpo += "\n\n# Supplementary Information\n\n" + sup.read_text().split("---", 2)[-1]

    corpo = corpo.replace("## Abstract\n\n", "## Abstract\n\n<div class=\"abstract\">\n\n", 1)
    corpo = re.sub(r"(<div class=\"abstract\">\n\n[^\n]+\n)", r"\1\n</div>\n", corpo, count=1)
    corpo = corpo.replace("## References\n", "## References\n\n<div class=\"refs\">\n", 1)
    corpo = corpo.replace("\n\n## Extended Data\n", "\n\n</div>\n\n## Extended Data\n", 1)

    tmp_md, tmp_html = HERE / "_leitura.md", HERE / "_leitura.html"
    tmp_md.write_text(corpo)
    subprocess.run([PANDOC, str(tmp_md), "-f", "markdown+superscript+subscript", "-s", "--metadata", "lang=en",
                    "-o", str(tmp_html)], check=True)
    h = tmp_html.read_text().replace("</head>", f"<style>{CSS}</style></head>")
    tmp_html.write_text(h)
    out = HERE / "manuscript_figuras.pdf"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--allow-file-access-from-files",
                    f"--print-to-pdf={out}", f"file://{tmp_html}"], check=True, capture_output=True)
    tmp_md.unlink()
    tmp_html.unlink()
    print(out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
