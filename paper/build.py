"""Gera paper/manuscript.md a partir de manuscript_src.md.

- Citações {chave1,chave2} viram números sobrescritos (^1,2^ ou ^1–3^) na ordem da primeira aparição,
  como pede a Nature; a lista de referências sai na mesma ordem.
- Referências com DOI são formatadas a partir da Crossref (cache em refs_cache.json); as demais são
  fontes institucionais com URL, escritas à mão em MANUAIS.
- Conta palavras do resumo, do texto principal, dos Methods e das legendas, e falha se passar dos
  limites da Nature Cities (Article) ou se houver chave sem referência.

Uso: python paper/build.py [--src manuscript_src.reescrito.md] [--out manuscript.md] [--anon]

``--anon`` gera a versão para revisão duplo-anônima: tira autores, afiliações, correspondência, contribuições
e agradecimentos, e troca as frases que identificam os autores (a autoria vai na carta de apresentação).
"""

from __future__ import annotations

import json
import os
import shutil
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
SRC, OUT, CACHE = HERE / "manuscript_src.md", HERE / "manuscript.md", HERE / "refs_cache.json"

DOI = {
    "weisburd2015": "10.1111/1745-9125.12070", "lee2017": "10.1186/s40163-017-0069-x",
    "weisburd2004": "10.1111/j.1745-9125.2004.tb00521.x", "chainey2019": "10.1186/s40163-019-0100-5",
    "demelo2015": "10.1016/j.apgeog.2015.05.012", "farrell2015": "10.1186/s40163-014-0015-0",
    "cohen1979": "10.2307/2094589", "hollispeel2011": "10.1007/s10611-011-9309-2",
    "brantingham1995": "10.1007/BF02242925", "kinney2008": "10.2148/benv.34.1.62",
    "robinson1950": "10.2307/2087176", "twinam2017": "10.1016/j.jue.2017.05.006",
    "andresen2017": "10.1007/s10940-016-9301-1", "felson2003": "10.1016/S0169-2070(03)00093-1",
    "haberman2015": "10.1111/1745-9125.12076", "vansleeuwen2021": "10.1186/s40163-021-00139-8",
    "stahl2016": "10.1126/science.aaf2403", "marx2021": "10.1038/s41592-020-01033-y",
    "moses2022": "10.1038/s41592-022-01409-2", "newman2019": "10.1038/s41587-019-0114-2",
    "kleshchevnikov2022": "10.1038/s41587-021-01139-4", "cable2022": "10.1038/s41587-021-00830-w",
    "schurch2020": "10.1016/j.cell.2020.07.005", "palla2022": "10.1038/s41592-021-01358-2",
    "kotliar2019": "10.7554/eLife.43803", "zhang2014": "10.1073/pnas.1408886111",
    "palazzo2022": "10.1093/jue/juac007", "delmelle2016": "10.1080/00045608.2015.1096188",
    "lunarivera2025": "10.1038/s42949-025-00265-1", "traag2019": "10.1038/s41598-019-41695-z",
    "gale2016": "10.5311/JOSIS.2016.12.232", "andresen2006": "10.1093/bjc/azi054",
    "hipp2019": "10.1080/07418825.2018.1445276", "hanaoka2018": "10.1177/0265813516672454",
    "sampson1997": "10.1126/science.277.5328.918", "kitagawa1955": "10.1080/01621459.1955.10501299",
    "callaway2021": "10.1016/j.jeconom.2020.12.001", "cochran1954": "10.2307/3001616",
    "elowitz2002": "10.1126/science.1070919", "song2010": "10.1126/science.1177170",
    "mohler2011": "10.1198/jasa.2011.ap09546", "riebler2016": "10.1177/0962280216660421",
    "gneiting2007": "10.1198/016214506000001437", "braga2019": "10.1002/cl2.1046",
    "hipp2026": "10.1016/j.jcrimjus.2026.102712", "mohler2015": "10.1080/01621459.2015.1077710",
    "lum2016": "10.1111/j.1740-9713.2016.00960.x", "nosek2018": "10.1073/pnas.1708274114",
    "holm1979": "10.2307/4615733", "sherman1989": "10.1111/j.1745-9125.1989.tb00862.x",
    "bernasco2011": "10.1177/0022427810384135", "caplan2011": "10.1080/07418825.2010.486037",
    "bernasco2017": "10.1177/0022427816680681", "tompson2013": "10.1177/0022427812469114",
    "braga2011": "10.1177/0022427810384137", "nagin2000": "10.1023/a:1007502804941",
    "akpinar2021": "10.1145/3442188.3445877", "builgil2021": "10.1093/bjc/azaa067",
    "chalfin2022": "10.1007/s10940-020-09490-6", "goodman1953": "10.2307/2088121",
    "shenorr2010": "10.1038/nmeth.1439", "ceccato2007": "10.1068/a38283",
    "biderman2019": "10.1007/s10940-018-9393-x", "sarkar2021": "10.1038/s41588-021-00873-4", "johnson2007": "10.1007/s10940-007-9025-3",
    # parecer crítico de 2026-10-20 (paper/review/parecer/D_literatura.md)
    "quick2019": "10.1177/2399808317744779", "wu2022": "10.1140/epjds/s13688-022-00366-2",
    "alborszumel2026": "10.1007/s10940-025-09629-3", "denadai2020": "10.1038/s41598-020-70808-2",
    "gorr2015": "10.1007/s10940-014-9223-8", "bernascosteenbeek2017": "10.1007/s10940-016-9324-7",
    "stucky2009": "10.1111/j.1745-9125.2009.00174.x", "quick2018": "10.1016/j.jcrimjus.2018.06.003",
    "andresen2007": "10.1068/a38187",
}

MANUAIS = {
    "eck2007": "Eck, J. E., Clarke, R. V. & Guerette, R. T. Risky facilities: crime concentration in homogeneous sets of "
               "establishments and facilities. *Crime Prev. Stud.* **21**, 225–264 (2007).",
    "park1925": "Park, R. E., Burgess, E. W. & McKenzie, R. D. *The City* (Univ. Chicago Press, 1925).",
    "shaw1942": "Shaw, C. R. & McKay, H. D. *Juvenile Delinquency and Urban Areas* (Univ. Chicago Press, 1942).",
    "celularseguro": "Ministério da Justiça e Segurança Pública. *Celular Seguro* https://celularseguro.mj.gov.br (2023).",
    "ssp_data": "Secretaria da Segurança Pública do Estado de São Paulo. *Transparência SSP: dados de boletins de "
                "ocorrência* https://www.ssp.sp.gov.br/transparenciassp (2026).",
    "geosampa": "Prefeitura de São Paulo. *GeoSampa: mapa digital da cidade de São Paulo* "
                "https://geosampa.prefeitura.sp.gov.br (2026).",
    "cnpj": "Receita Federal do Brasil. *Cadastro Nacional da Pessoa Jurídica (CNPJ), dados abertos* "
            "https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj (2025).",
    "ibge2022": "Instituto Brasileiro de Geografia e Estatística. *Censo Demográfico 2022: agregados por setores "
                "censitários* https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/ (2024).",
    "metro2017": "Companhia do Metropolitano de São Paulo. *Pesquisa Origem e Destino 2017* "
                 "https://transparencia.metrosp.com.br/dataset/pesquisa-origem-e-destino (2019).",
    "metro2023": "Companhia do Metropolitano de São Paulo. *Pesquisa Origem e Destino 2023* "
                 "https://transparencia.metrosp.com.br/dataset/pesquisa-origem-e-destino-2023-anexos (2025).",
}

# abreviações ISO 4, como a Nature usa
ABREV = {
    "Criminology": "Criminology", "Crime Science": "Crime Sci.", "American Sociological Review": "Am. Sociol. Rev.",
    "European Journal on Criminal Policy and Research": "Eur. J. Crim. Policy Res.",
    "Journal of Urban Economics": "J. Urban Econ.", "Journal of Quantitative Criminology": "J. Quant. Criminol.",
    "Nature Methods": "Nat. Methods", "Nature Biotechnology": "Nat. Biotechnol.", "Scientific Reports": "Sci. Rep.",
    "eLife": "eLife", "Science": "Science", "Cell": "Cell",
    "Annals of the American Association of Geographers": "Ann. Am. Assoc. Geogr.",
    "The British Journal of Criminology": "Br. J. Criminol.", "British Journal of Criminology": "Br. J. Criminol.",
    "Environment and Planning B: Urban Analytics and City Science": "Environ. Plan. B Urban Anal. City Sci.",
    "International Journal of Forecasting": "Int. J. Forecast.",
    "Proceedings of the National Academy of Sciences": "Proc. Natl Acad. Sci. USA",
    "Journal of the American Statistical Association": "J. Am. Stat. Assoc.", "Significance": "Significance",
    "Journal of Econometrics": "J. Econom.", "Biometrics": "Biometrics",
    "Crime, Law and Social Change": "Crime Law Soc. Change", "Built Environment": "Built Environ.",
    "Justice Quarterly": "Justice Q.", "Journal of Spatial Information Science": "J. Spat. Inf. Sci.",
    "Campbell Systematic Reviews: Better Evidence for a Better World": "Campbell Syst. Rev.",
    "Campbell Systematic Reviews": "Campbell Syst. Rev.", "Applied Geography": "Appl. Geogr.",
    "Statistical Methods in Medical Research": "Stat. Methods Med. Res.", "npj Urban Sustainability": "npj Urban Sustain.",
    "Journal of Urban Ecology": "J. Urban Ecol.", "Journal of Criminal Justice": "J. Crim. Justice",
    "Scandinavian Journal of Statistics": "Scand. J. Stat.",
    "Journal of Research in Crime and Delinquency": "J. Res. Crime Delinq.",
    "Proceedings of the 2021 ACM Conference on Fairness, Accountability, and Transparency": "Proc. 2021 ACM Conf. Fairness Account. Transpar.",
    "Environment and Planning A: Economy and Space": "Environ. Plan. A", "Nature Genetics": "Nat. Genet.",
    "EPJ Data Science": "EPJ Data Sci.", "Environment and Planning A": "Environ. Plan. A",
}

# títulos que a Crossref traz em caixa alta ou com marcas; reescritos como no original
TITULOS = {
    "weisburd2015": "The law of crime concentration and the criminology of place",
    "weisburd2004": "Trajectories of crime at places: a longitudinal study of street segments in the city of Seattle",
    "haberman2015": "Testing for temporally differentiated relationships among potentially criminogenic places and "
                    "census block street robbery counts",
    "kitagawa1955": "Components of a difference between two rates",
    "sherman1989": "Hot spots of predatory crime: routine activities and the criminology of place",
    "traag2019": "From Louvain to Leiden: guaranteeing well-connected communities",
    "bernasco2011": "Robberies in Chicago: a block-level analysis of the influence of crime generators, crime attractors, and offender anchor points",
    "mohler2011": "Self-exciting point process modeling of crime",
    "callaway2021": "Difference-in-differences with multiple time periods",
    "cochran1954": "Some methods for strengthening the common χ² tests",
    "townsley2003": "Infectious burglaries. A test of the near repeat hypothesis",
    "stucky2009": "Land use and violent crime",
    "andresen2007": "Location quotients, ambient populations, and the spatial analysis of crime in Vancouver, Canada",
}
# campos que faltam na Crossref
EXTRA = {"wu2022": {"authors": [("Wu", "J."), ("Abrar", "S. M."), ("Awasthi", "N."), ("Frías-Martínez", "E."),
                            ("Frías-Martínez", "V.")],
                "title": "Enhancing short-term crime prediction with human mobility flows and deep learning architectures",
                "container": "EPJ Data Science", "volume": "11", "page": "53", "year": 2022},
         "gale2016": {"volume": "12", "page": ""}, "cohen1979": {"page": "588-608"}, "robinson1950": {"page": "351-357"},
         "cochran1954": {"page": "417-451"}, "holm1979": {"container": "Scandinavian Journal of Statistics",
                                                              "volume": "6", "page": "65-70", "year": 1979,
                                                              "title": "A simple sequentially rejective multiple test procedure",
                                                              "authors": [("Holm", "S.")]}}


def crossref(doi: str, cache: dict) -> dict:
    if doi not in cache:
        with urllib.request.urlopen(f"https://api.crossref.org/works/{doi}", timeout=30) as r:
            cache[doi] = json.load(r)["message"]
    return cache[doi]


def iniciais(given: str) -> str:
    partes = re.split(r"[\s]+", given.replace(".", ". ").strip())
    out = []
    for p in partes:
        if not p:
            continue
        sub = [s for s in p.split("-") if s]
        out.append("-".join(s[0].upper() + "." for s in sub))
    return " ".join(out)


PROPRIOS = {"Seattle", "Chicago", "New", "York", "City", "Brazil", "Brazilian", "São", "Paulo", "Latin", "America",
            "Leiden", "Louvain", "Bayesian", "Poisson", "Cell2location", "Squidpy", "RNA-Seq", "DNA", "OAC", "Primeiro",
            "Comando", "Capital", "Pax", "Monopolista", "Method", "Brazil", "Vancouver", "Boston", "England", "Wales",
            "GIS", "Year", "Canada", "Pittsburgh"}


def frase(t: str) -> str:
    """Caixa de frase (estilo Nature): mantém a primeira palavra, siglas, nomes próprios e a palavra após dois-pontos."""
    ws = t.split(" ")
    out = []
    for i, w in enumerate(ws):
        prev = out[-1] if out else ""
        core = w.strip("(),:?")
        keep = i == 0 or prev.endswith("?") or core in PROPRIOS or sum(c.isupper() for c in core) > 1 or not w[:1].isupper()
        w = w if keep else w[:1].lower() + w[1:]
        if "-" in w and i > 0 and core not in PROPRIOS:  # Block-Level -> block-level; Self-Exciting -> self-exciting
            w = "-".join([w.split("-")[0]] + [p[:1].lower() + p[1:] if sum(c.isupper() for c in p) == 1 else p for p in w.split("-")[1:]])
        out.append(w)
    return " ".join(out)


def autores(lista: list[tuple[str, str]]) -> str:
    if len(lista) > 5:
        return f"{lista[0][0]}, {lista[0][1]} et al."
    nomes = [f"{f}, {g}".strip(", ") for f, g in lista]
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + " & " + nomes[-1]


def sobrenome(f: str) -> str:
    return f.title() if f.isupper() else f


def formata(chave: str, cache: dict) -> str:
    if chave in MANUAIS:
        return MANUAIS[chave]
    doi = DOI[chave]
    ex = EXTRA.get(chave, {})
    if "authors" in ex:
        m, aut = {}, ex["authors"]
    else:
        m = crossref(doi, cache)
        aut = [(sobrenome(a.get("family", a.get("name", ""))), iniciais(a.get("given", ""))) for a in m.get("author", [])]
    titulo = ex.get("title") or TITULOS.get(chave) or re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m["title"][0])).strip()
    titulo = frase(titulo.rstrip(".*"))
    fim = "" if titulo.endswith(("?", "!")) else "."
    cont = ex.get("container") or (m.get("container-title") or [""])[0]
    rev = ABREV.get(cont, cont)
    vol = ex.get("volume", m.get("volume", ""))
    pag = ex.get("page", m.get("page", m.get("article-number", "")))
    if chave == "braga2019":
        pag = "e01046"
    ano = ex.get("year") or (m.get("published-print") or m.get("published-online") or m.get("issued"))["date-parts"][0][0]
    pag = pag.replace("-", "–") if pag else ""
    corpo = f"*{rev}*" + (f" **{vol}**" if vol else "") + (f", {pag}" if pag else "")
    return f"{autores(aut)} {titulo}{fim} {corpo} ({ano}). https://doi.org/{doi}"


def comprime(nums: list[int]) -> str:
    nums = sorted(set(nums))
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"{nums[i]}–{nums[j]}" if j - i >= 2 else ",".join(map(str, nums[i:j + 1])))
        i = j + 1
    return ",".join(out)


def bloco(texto: str, nome: str) -> str:
    m = re.search(rf"<!--{nome}-->(.*?)<!--/{nome}-->", texto, re.S)
    return m.group(1) if m else ""


def palavras(texto: str) -> int:
    texto = re.sub(r"\^[^^]*\^", "", texto)
    texto = re.sub(r"^#+ .*$", "", texto, flags=re.M)
    texto = re.sub(r"[*_`]", "", texto)
    return len(re.findall(r"[\w’'−–.,%-]+", texto))


PANDOC = os.environ.get("PANDOC") or shutil.which("pandoc") or "pandoc"


def limpa_docx(path: Path) -> None:
    """Propriedades do documento sem autor nem programa (revisão duplo-anônima e higiene de metadados)."""
    import zipfile

    tmp = path.with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "docProps/core.xml":
                data = re.sub(rb"<dc:creator>.*?</dc:creator>", b"<dc:creator></dc:creator>", data)
                data = re.sub(rb"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", b"", data)
            zout.writestr(item, data)
    tmp.replace(path)


# frases que identificam os autores na versão anônima (Nature Cities, revisão duplo-anônima)
ANON = [
    ("had been seen on the first author's public crime website", "had been seen on a public crime-statistics website"),
    ("first author's public crime website", "a public crime-statistics website"),
    # Repositório e arquivo de código: GitHub e Zenodo mostram os nomes dos autores
    ("https://github.com/MarcosToquetao/CityOmics", "[ANONYMOUS LINK]"),
    ("is archived at Zenodo (https://doi.org/10.5281/zenodo.23778358)", "is archived at Zenodo (DOI withheld for review)"),
    ("are deposited at Zenodo (https://doi.org/10.5281/zenodo.23778485)", "are deposited at Zenodo (DOI withheld for review)"),
]


def anonimiza(src: str) -> str:
    cab, resto = src.split("<!--ABSTRACT-->", 1)
    titulo = re.search(r"^---\n.*?\n---\n", cab, re.S).group(0)
    src = titulo + "\n<!--ABSTRACT-->" + resto
    for a, b in ANON:
        src = src.replace(a, b)
    for sec in ("Acknowledgements", "Author contributions"):
        src = re.sub(rf"## {sec}\n\n.*?\n\n(?=## )", "", src, flags=re.S)
    return src


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--anon", action="store_true")
    a = ap.parse_args()
    src = a.src.read_text() if a.src.is_absolute() else (Path.cwd() / a.src if (Path.cwd() / a.src).exists() else HERE / a.src).read_text()
    if a.anon:
        src = anonimiza(src)
    OUT_ = a.out if a.out.is_absolute() else HERE / a.out.name
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    ordem: list[str] = []
    for grupo in re.findall(r"\{([a-z0-9_,]+)\}", src):
        for k in grupo.split(","):
            if k not in ordem:
                ordem.append(k)
    faltam = [k for k in ordem if k not in DOI and k not in MANUAIS]
    if faltam:
        print("chaves sem referência:", faltam)
        return 1
    num = {k: i + 1 for i, k in enumerate(ordem)}
    corpo = re.sub(r"\{([a-z0-9_,]+)\}", lambda m: "^" + comprime([num[k] for k in m.group(1).split(",")]) + "^", src)
    refs = "\n".join(f"{num[k]}. {formata(k, cache)}" for k in ordem)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    corpo = corpo.replace("<!--/END-->", "<!--/END-->\n\n## References\n\n" + refs + "\n")
    corpo = re.sub(r"<!--/?[A-Z]+-->\n?", "", corpo)
    OUT_.write_text(corpo)
    sufixo = "_anon" if a.anon else ""
    si = (HERE / "supplementary_src.md").read_text()
    si = re.sub(r"<!--/?[A-Z0-9]+-->\n?", "", si)
    if a.anon:
        for x, y in ANON:
            si = si.replace(x, y)
    si_md = HERE / f"supplementary{sufixo}.md"
    si_md.write_text(si)
    if shutil.which(PANDOC):  # Word para o envio (a Nature Cities aceita Word ou PDF na primeira submissão)
        import subprocess

        for md in (OUT_, si_md):
            subprocess.run([PANDOC, str(md), "-f", "markdown+superscript+subscript", "-o", str(md.with_suffix(".docx"))],
                           check=True)
            limpa_docx(md.with_suffix(".docx"))

    n = {"resumo": palavras(bloco(src, "ABSTRACT").replace("## Abstract", "")), "texto principal": palavras(bloco(src, "MAIN")),
         "Methods": palavras(bloco(src, "METHODS")), "legendas": palavras(bloco(src, "LEGENDS"))}
    titulo = re.search(r'title: "(.*)"', src).group(1)
    limites = {"resumo": 150, "texto principal": 3500, "Methods": 3000}
    print(f"título: {len(titulo)} caracteres (máx. 90)")
    for k, v in n.items():
        print(f"{k}: {v} palavras" + (f" (máx. {limites[k]})" if k in limites else ""))
    main_refs = []
    for grupo in re.findall(r"\{([a-z0-9_,]+)\}", bloco(src, "ABSTRACT") + bloco(src, "MAIN")):
        main_refs += [k for k in grupo.split(",") if k not in main_refs]
    print(f"referências: {len(ordem)} no total, {len(main_refs)} no texto principal (guia: até 50)")
    secoes = re.split(r"^#{2,3} ", bloco(src, "MAIN"), flags=re.M)
    for s in secoes[1:]:
        print(f"  {s.splitlines()[0]}: {palavras(s)}")
    ok = len(titulo) <= 90 and all(n[k] <= v for k, v in limites.items())
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
