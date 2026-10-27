"""Nomes de exibição em inglês, num só lugar (pedido do autor e parecer R16; tabela em paper/review/parecer/E_rotulos.md).

Todas as figuras (Figs. 1–6 e Extended Data) tiram daqui os rótulos que o leitor vê:

1. ``ATTR_EN``: atributos dos lotes ("genes" da tipagem).
2. Classes de célula:
   - nomes longos dos tipos de lote: ``name_en`` de ``tipos_perfil_2025.parquet`` (``typing._nome``);
   - nomes curtos: ``TYPE_SHORT``, que cobre todo o vocabulário de ``typing._nome`` (o sufixo numérico
     de tipos repetidos é preservado), com fallback para o nome longo;
   - classes fixas do pipeline (favela, sem cadastro, ruas, estações): ``FIXED_LONG`` e ``FIXED_SHORT``;
   - famílias: ``FAMILY_EN`` e ``FAMILY_SHORT``;
   - ``class_labels()`` devolve os dois dicionários (chave interna → longo, → curto) lidos dos dados.
3. ``CRIME_EN``: tipos de crime (fenótipos); ``PERIOD_EN``: períodos do dia; ``clock_label``.
4. ``MODEL_EN`` e ``MODEL_FAMILY_EN``: métodos de previsão e famílias de origem.
5. ``GROUP_EN``: grupos teóricos de covariáveis.
6. ``COV_EN``: covariáveis do setor (Extended Data); ``LR_EN``: ligantes e receptores criminológicos.
7. ``domain_labels`` e ``program_label``: domínios do tecido e programas de crime, nomeados pelos dados.
8. Outros: exposições alternativas da favela, cenários de simulação e de ocultação, eventos do estudo de evento.

Nenhum nome de tipo é fixado: os tipos e o número de tipos vêm dos dados.
"""

from __future__ import annotations

import re

import polars as pl

from cityomics.atlas.genes_lote import atlas_dir

# --- 1. atributos dos lotes ------------------------------------------------------------------------

ATTR_EN = {
    "area_terreno": "Lot area", "area_construida": "Built area", "n_unidades": "Units on the lot", "pavimentos": "Floors",
    "valor_m2_terreno": "Land value per m²", "valor_m2_construcao": "Building value per m²", "testada": "Street frontage",
    "aproveitamento": "Floor-area ratio", "uso_residencial": "Residential use", "uso_comercio": "Commercial use",
    "uso_servicos": "Service use", "uso_industria": "Industrial use", "uso_terreno": "Vacant-land use",
    "padrao_baixo": "Low building standard", "padrao_medio": "Middle building standard", "padrao_alto": "High building standard",
    "esquina": "Corner lot", "idade": "Building age",
    "cnpj_bar_restaurante": "Bars and restaurants (businesses)", "cnpj_comercio_varejista": "Retail shops (businesses)",
    "cnpj_comercio_atacado": "Wholesale (businesses)", "cnpj_financeiro": "Banks and finance (businesses)",
    "cnpj_industria": "Manufacturing (businesses)", "cnpj_transporte_armazenagem": "Transport and storage (businesses)",
    "cnpj_alojamento": "Lodging (businesses)", "cnpj_educacao_saude": "Education and health (businesses)",
    "cnpj_construcao_imobiliario": "Construction and real estate (businesses)",
    "cnpj_servicos_pessoais": "Personal services (businesses)", "cnpj_outros_servicos": "Other services (businesses)",
    "cnpj_mei": "Micro-entrepreneurs (businesses)",
}

# --- 2. classes de célula --------------------------------------------------------------------------

# todo o vocabulário de typing._nome (nome longo em inglês → nome curto)
TYPE_SHORT = {
    "Low-rise residential, low standard": "Low-standard houses",
    "Low-rise residential, middle standard": "Mid-standard houses",
    "Low-rise residential, high standard": "High-standard houses",
    "Corner residential": "Corner houses",
    "Mixed residential and commercial": "Houses with shops",
    "Low-rise mixed, wholesale": "Houses with wholesale",
    "Street retail, low standard": "Low-standard shops",
    "Street retail, middle standard": "Mid-standard shops",
    "Mid/high-rise, residential and mixed": "Mixed-use high-rise",
    "Mid/high-rise residential": "Apartment blocks",
    "High-rise, high standard": "High-standard high-rise",
    "Services and facilities": "Services",
    "Industry and warehouses": "Industry",
    "Vacant land": "Vacant land",
}
# classes que não vêm da tipagem (chaves internas do pipeline)
FIXED_LONG = {"Favela (FCU)": "Favelas (census areas)", "Sem cadastro": "No cadastral record",
              "rua_arterial_m": "Arterial streets", "rua_coletora_m": "Collector streets", "rua_local_m": "Local streets",
              "n_trilho": "Rail stations", "n_terminal": "Bus terminals", "estacoes": "Stations"}
FIXED_SHORT = {"Favela (FCU)": "Favelas", "Sem cadastro": "No cadastral record",
               "rua_arterial_m": "Arterial streets", "rua_coletora_m": "Collector streets", "rua_local_m": "Local streets",
               "n_trilho": "Rail stations", "n_terminal": "Bus terminals", "estacoes": "Stations"}
FAMILY_EN = {"res_horizontal": "Low-rise residential", "res_vertical_medio": "Mid/high-rise residential",
             "res_vertical_alto": "High-standard residential", "comercio": "Commerce and mixed use", "servicos": "Services",
             "industria": "Industry", "vazio": "Vacant land", "favela": "Favelas", "sem_cadastro": "No cadastral record",
             "ruas": "Streets", "estacoes": "Stations"}
FAMILY_SHORT = {"res_horizontal": "Low-rise housing", "res_vertical_medio": "High-rise", "res_vertical_alto": "High-standard",
                "comercio": "Commerce", "servicos": "Services", "industria": "Industry", "vazio": "Vacant land",
                "favela": "Favelas", "sem_cadastro": "No record", "ruas": "Streets", "estacoes": "Stations"}

# o mesmo vocabulário em português (chaves internas), só para traduzir nomes de tipo que ainda não estão no
# perfil corrente (arquivos do atlas de rodadas diferentes durante a refação); espelha typing._nome
TYPE_PT_EN = {
    "Terreno vago": "Vacant land", "Indústria e galpões": "Industry and warehouses",
    "Serviços e equipamentos": "Services and facilities", "Vertical residencial e misto": "Mid/high-rise, residential and mixed",
    "Vertical alto padrão": "High-rise, high standard", "Vertical residencial": "Mid/high-rise residential",
    "Comércio de rua popular": "Street retail, low standard", "Comércio de rua médio": "Street retail, middle standard",
    "Casa e comércio atacadista": "Low-rise mixed, wholesale", "Misto residencial e comercial": "Mixed residential and commercial",
    "Residencial de esquina": "Corner residential", "Residencial horizontal alto padrão": "Low-rise residential, high standard",
    "Residencial horizontal popular": "Low-rise residential, low standard",
    "Residencial horizontal médio": "Low-rise residential, middle standard",
}

_SUF = re.compile(r"^(.*?)( \d+)?$")


# qualificadores de typing.QUALIFICADORES na forma curta (entre parênteses depois do nome curto)
QUAL_SHORT = {"with a home business": "(home business)", "with a service business": "(service business)",
              "with personal services": "(personal services)", "with bars and restaurants": "(bars and restaurants)",
              "with shops": "(shops)", "with wholesale": "(wholesale)", "with transport businesses": "(transport)",
              "with schools or clinics": "(schools or clinics)", "with construction businesses": "(construction)",
              "with manufacturing": "(manufacturing)", "with finance businesses": "(finance)", "on corners": "on corners",
              "multi-unit": "(multi-unit)", "large buildings": "(large buildings)", "large lots": "(large lots)",
              "older buildings": "(older buildings)", "high land value": "(high land value)", "wide frontage": "(wide frontage)",
              "with retail use": "(retail use)", "with service use": "(service use)"}


def short_name(name_en: str) -> str:
    """Nome curto de um tipo a partir do nome longo (``typing._nome``): nome-base curto mais o qualificador
    (``, with a home business`` → ``(home business)``), preservando o sufixo numérico de repetição."""
    base, suf = _SUF.match(name_en).groups()
    for k in sorted(TYPE_SHORT, key=len, reverse=True):
        if base.startswith(k + ", "):
            q = base[len(k) + 2:]
            return f"{TYPE_SHORT[k]} {QUAL_SHORT.get(q, q)}" + (suf or "")
    return TYPE_SHORT.get(base, base) + (suf or "")


def _pt_en(key: str) -> str | None:
    """Tradução de uma chave interna fora do perfil corrente (``e|`` de colunas, sufixo de repetição)."""
    k = key[2:] if key.startswith(("e|", "n|")) else key
    if k in FIXED_LONG:
        return FIXED_LONG[k]
    base, suf = _SUF.match(k).groups()
    return TYPE_PT_EN[base] + (suf or "") if base in TYPE_PT_EN else None


class _Nomes(dict):
    """Dicionário de nomes cujo ``get`` traduz, pelo vocabulário de ``typing._nome``, chaves fora do perfil."""

    def __init__(self, data, curto: bool = False):
        super().__init__(data)
        self.curto = curto

    def get(self, key, default=None):
        if key in self:
            return self[key]
        en = _pt_en(key) if isinstance(key, str) else None
        if en is None:
            return default
        k = key[2:] if key.startswith(("e|", "n|")) else key
        return (FIXED_SHORT.get(k) or short_name(en)) if self.curto else en


def _perfil() -> pl.DataFrame:
    return pl.read_parquet(atlas_dir() / "tipos_perfil_2025.parquet")


def type_en() -> dict[str, str]:
    """Chave interna (nome em português) → nome longo em inglês, para tipos e classes fixas."""
    p = _perfil()
    return _Nomes(dict(zip(p["nome"].to_list(), p["name_en"].to_list())) | FIXED_LONG)


def class_labels(perfil: pl.DataFrame | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """(longo, curto): chave interna da classe de célula → nome longo e curto em inglês."""
    p = _perfil() if perfil is None else perfil
    longo = dict(zip(p["nome"].to_list(), p["name_en"].to_list()))
    curto = {k: short_name(v) for k, v in longo.items()}
    return _Nomes(longo | FIXED_LONG), _Nomes(curto | FIXED_SHORT, curto=True)


def family_of(perfil: pl.DataFrame | None = None) -> dict[str, str]:
    p = _perfil() if perfil is None else perfil
    out = dict(zip(p["nome"].to_list(), p["familia"].to_list())) | {"Favela (FCU)": "favela", "Sem cadastro": "sem_cadastro"}
    return out | {k: ("ruas" if k.startswith("rua_") else "estacoes") for k in FIXED_LONG if k.startswith(("rua_", "n_"))}


# --- 3. tipos de crime e tempo ---------------------------------------------------------------------

CRIME_EN = {
    "celular_furto": "Phone theft", "celular_roubo": "Phone robbery", "furto_outros": "Other street theft",
    "roubo_outros": "Other street robbery", "furto_veiculo": "Vehicle theft", "roubo_veiculo": "Vehicle robbery",
    "interior_veiculo": "Theft from vehicle", "fios_cabos": "Wire and cable theft", "residencia": "Residential theft/robbery",
    "comercio": "Commercial theft/robbery", "coletivo": "Public transport theft/robbery", "carga": "Cargo theft/robbery",
    "lesao_dolosa": "Assault outside the home", "transito": "Traffic casualties (control)", "letal": "Lethal violence",
    "celular": "Phone crime", "celular_2025": "Phone crime, 2025",
}
PERIOD_EN = {"madrugada": "00–06 h", "manha": "06–12 h", "tarde": "12–18 h", "noite": "18–24 h"}


def clock_label(desfecho: str, ano, sep: str = " ") -> str:
    """Rótulo de um teste do relógio: 'Phone theft 2024'."""
    return f"{CRIME_EN.get(desfecho, desfecho)}{sep}{ano}"


# --- 4. modelos ------------------------------------------------------------------------------------

MODEL_EN = {
    "media_historica": "Historical mean", "glm": "Negative binomial GLM", "kde": "Kernel density (KDE)",
    "chronos": "Chronos (zero-shot)", "gwr_distrito": "Geographically weighted (GWR)", "painel_espacial": "Spatial panel",
    "maxent": "MaxEnt", "bym2": "BYM2 spatial model", "spde": "Log-Gaussian Cox (SPDE)", "hawkes": "Hawkes (self-exciting)",
    "lgbm_nucleo": "LightGBM (core covariates)", "lgbm_sem_crime": "LightGBM (no crime history)",
    "lgbm_completo": "LightGBM (all covariates)", "gnn": "Graph neural network", "ensemble": "Ensemble",
    "lgbm": "LightGBM", "eb_espacial": "Spatial empirical Bayes",
}


def model_tick(m: str, width: int = 13) -> str:
    """Nome do modelo quebrado em linhas curtas (rótulos de eixo estreitos)."""
    import textwrap

    return "\n".join(textwrap.wrap(MODEL_EN.get(m, m), width, break_on_hyphens=False, break_long_words=False))
MODEL_FAMILY_EN = {"baseline": "Baseline", "sismologia": "Seismology", "epidemiologia": "Epidemiology", "ecologia": "Ecology",
                   "astronomia": "Astronomy", "aprendizado": "Machine learning", "fundacao": "Foundation model",
                   "ensemble": "Ensemble", "decisao": "Decision layer", "econometria": "Econometrics"}

# --- 5. grupos teóricos de covariáveis -------------------------------------------------------------

GROUP_EN = {
    "atividade_rotineira": "Routine activity", "desorganizacao_social": "Social disorganization",
    "cpted": "Environmental design (CPTED)", "mercado_imobiliario": "Real-estate market", "historico_crime": "Crime history",
    "identidade": "Cell class (identity)", "espacial": "District effect", "contexto_temporal": "Season and trend",
    "outras_atividade": "Other routine activity", "outras_social": "Other social", "outras_cpted": "Other environmental design",
    "tamanho": "Tract size", "outras": "Other",
}

# --- 6. covariáveis do setor e pares ligante–receptor ----------------------------------------------

COV_EN = {
    "infra_dist_estacao_trilhos_m": "Distance to rail station", "infra_dist_terminal_onibus_m": "Distance to bus terminal",
    "infra_dens_ponto_onibus_km2": "Bus-stop density", "cnpj_estoque_bar_restaurante": "Bars and restaurants",
    "cnpj_estoque_comercio_varejista": "Retail shops", "cnpj_estoque_financeiro": "Banks and finance firms",
    "agencias_estoque": "Bank branches", "osm_dens_poi_bar_noturno_km2": "Nightlife density",
    "osm_dens_poi_banco_atm_km2": "ATM density", "osm_dens_poi_alimentacao_km2": "Food outlets",
    "osm_dens_poi_comercio_km2": "Shop density", "osm_dist_bar_noturno_m": "Distance to nightlife",
    "pop_dasi": "Resident population", "censo2022_dens_pop_km2": "Population density",
    "ipvs_ipvs_codigo": "Social vulnerability index (IPVS)", "censo_interp_renda_media_resp": "Household income",
    "censo2022_cv_renda_resp": "Income inequality", "censo_d_renda_rel": "Change in income between censuses",
    "censo_interp_frac_homens_15_29": "Share of men aged 15–29", "censo_interp_taxa_analfabetismo_15": "Illiteracy",
    "censo2022_frac_dom_nao_ocupados": "Vacant dwellings", "censo2022_moradores_por_dom": "Residents per dwelling",
    "censo_g_pop": "Population growth between censuses", "infra_dist_favela_m": "Distance to favela",
    "censo2022_frac_cortico": "Tenements (cortiços)", "censo2022_frac_faces_iluminacao": "Street lighting (census)",
    "infra_dens_iluminacao_km2": "Lamp-post density", "censo2022_frac_faces_calcada": "Sidewalks",
    "censo2022_frac_faces_pavimentadas": "Paved streets", "osm_dens_intersecoes_km2": "Intersection density",
    "osm_betweenness_media": "Street centrality (betweenness)", "osm_frac_becos": "Share of dead-end streets",
    "sp156_iluminacao_s6": "Lighting complaints", "sp156_limpeza_entulho_s6": "Debris complaints",
    "sp156_imovel_abandonado_s12": "Abandoned-property complaints", "luz_noturna": "Night-time light (satellite)",
    "n_transacoes_s12": "Property sales", "preco_m2_mediana_m12": "Sale price per m²", "frac_financiada_m12": "Share of financed sales",
    "cnpj_entradas_construcao_imobiliario_s12": "New construction firms",
}
LR_EN = {"fluxo_trilhos": "Rail passengers", "fluxo_onibus": "Bus passengers", "vida_noturna": "Nightlife", "varejo": "Retail",
         "dinheiro": "Cash (banks, ATMs)", "alvos_a_pe": "Pedestrian targets", "pouca_iluminacao": "Poor lighting",
         "rotas_de_fuga": "Escape routes", "abandono": "Disorder", "desvantagem": "Disadvantage"}
MISTY_EN = {"intrinseca": "Intrinsic (own tract)", "justaposta": "Juxtaposed (neighbours)", "para_espacial": "Para-spatial (1 km)"}

# --- 7. domínios e programas -----------------------------------------------------------------------


def domain_labels(short: bool = True, prefix: bool = True) -> dict[int, str]:
    """D1…Dk com os elementos mais enriquecidos no domínio (tipos e classes de rua); o terceiro entra se o nome repetir."""
    import numpy as np

    longo, curto = class_labels()
    nomes = curto if short else longo
    comp = pl.read_parquet(atlas_dir() / "setor_composicao_2025.parquet")
    dom = pl.read_parquet(atlas_dir() / "setor_dominio_2025.parquet").select("cd_setor", "dominio")
    cols = [c for c in comp.columns if c.startswith("e|") and c != "e|Sem cadastro"] + ["rua_arterial_m", "rua_coletora_m", "rua_local_m"]
    s = comp.join(dom, on="cd_setor").select("dominio", *cols)
    M = s.select(cols).to_numpy().astype(float)
    M = M / np.clip(M.sum(1, keepdims=True), 1e-9, None)
    lab = s["dominio"].to_numpy()
    city = M.mean(0)
    names = [nomes.get(c[2:] if c.startswith("e|") else c, c[2:] if c.startswith("e|") else c) for c in cols]
    out, used = {}, set()
    for k in sorted(set(lab)):
        enr = M[lab == k].mean(0) / np.clip(city, 1e-9, None)
        order = list(np.argsort(-enr))
        for n in (2, 3, 4):
            parts = [names[i] for i in order[:n]]
            key = " + ".join([parts[0]] + [p[0].lower() + p[1:] for p in parts[1:]])
            if key not in used:
                break
        used.add(key)
        out[int(k)] = f"D{int(k) + 1} · {key}" if prefix else key
    return out


def program_label(p: dict, curto: dict, long: bool = True) -> str:
    """'Program 1 · Rail stations + bus terminals': classes mais associadas ao programa de crime (NMF)."""
    cls = [curto.get(c, c) for c, r in p["classes_associadas"][:2] if r >= 0.05] or [curto.get(p["classes_associadas"][0][0], "")]
    cls = [cls[0]] + [c[0].lower() + c[1:] for c in cls[1:]]
    num = re.sub(r"\D", "", str(p["programa"])) or str(p["programa"])
    return f"{'Program ' if long else 'P'}{num} · {' + '.join(cls)}"


def program_title(p: str) -> str:
    num = re.sub(r"\D", "", str(p)) or str(p)
    return f"Program {num}"


# --- 8. outros -------------------------------------------------------------------------------------

# "{m}" recebe a testada implícita por domicílio informal (identificacao.json → favelas.construcao)
FAVELA_EXPOSURE_EN = {"atual": "Current: informal dwellings × {m} m", "area": "Tract area", "perimetro": "Tract perimeter",
                      "raiz_domicilios": "√ informal dwellings", "domicilios_ocupados": "Occupied dwellings in tract",
                      "indicador_setor": "Equal weight per tract"}
SIM_SCENARIO_EN = {"a_poisson": "Poisson", "b_risco_distrito": "District risk", "b2_risco_distrito_coerente": "District risk (coherent)",
                   "c_sobredispersao": "Overdispersion", "d_permutado": "Permuted rates"}
HIDE_SCENARIO_EN = {"mar": "At random within stratum", "mnar_crime": "More where crime is high",
                    "mnar_residencial": "More on residential frontage"}
EVENT_EN = {"abre_bar": "Bar or restaurant opens", "abre_varejo": "Retail shop opens", "fecha_bar": "Bar or restaurant closes"}
EVENT_ROW_EN = {"": "Any establishment", "_estrito": "Establishments other than individual micro-entrepreneurs, on commercial or service parcels"}

# compatibilidade com o código antigo (rótulos curtos indexados pelo nome longo)
SHORT = TYPE_SHORT | {v: FIXED_SHORT[k] for k, v in FIXED_LONG.items()}
