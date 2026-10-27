"""Leitura dos xlsx da SSP, recorte da capital, desfechos e envio ao cofre (spec-dados §1.1).

Para cada arquivo anual:

1. lê as abas de dados (as de metodologia e dicionário são ignoradas);
2. aplica o schema canônico e mantém só a capital pelo local do fato;
3. deduplica (base principal: BO × natureza × rubrica; celular: BO, maior versão);
4. separa os registros com data do fato em 2026, que vão direto para o cofre, junto com
   os eventos de desfecho correspondentes. Nada de 2026 é resumido ou impresso;
5. grava ``data/raw/bo/{fonte}_{ano}.parquet`` (contém endereço e número do BO; só local)
   e os eventos em ``data/interim/eventos_{desfecho}_{ano}.parquet`` (sem número do BO).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cityomics.ingest.schema import harmonize, is_capital, norm_text
from cityomics.ingest.snapshot import xlsx_dir
from cityomics.paths import interim_dir, raw_dir
from cityomics.sealed import sealed_path_for_write

SEAL_FROM = pd.Timestamp("2026-01-01")

LETAL_COMPOSTO = {"HOMICIDIO DOLOSO", "TENTATIVA DE HOMICIDIO", "LATROCINIO",
                  "LESAO CORPORAL SEGUIDA DE MORTE"}
LETAL_ESTRITO = LETAL_COMPOSTO - {"TENTATIVA DE HOMICIDIO"}

EVENT_COLUMNS = ["evento_id", "desfecho", "natureza", "estrito", "data_fato", "data_registro",
                 "hora_fato", "periodo", "tipolocal", "subtipolocal", "bairro", "dp_fato",
                 "seccional_fato", "latitude", "longitude", "coord_valida", "tem_logradouro",
                 "arquivo_ano"]


@dataclass(frozen=True)
class ParseResult:
    fonte: str
    ano: int
    linhas_capital: int
    selados: int
    eventos: dict


def _data_sheets(path: Path) -> dict[str, pd.DataFrame]:
    xl = pd.ExcelFile(path, engine="calamine")
    sheets = {}
    for name in xl.sheet_names:
        upper = norm_text(name)
        if "METODOLOGIA" in upper or "DICIONARIO" in upper or "CAMPOS" in upper:
            continue
        sheets[name] = xl.parse(name)
    return sheets


def is_sealed(df: pd.DataFrame) -> pd.Series:
    """Registros que pertencem ao período de teste: fato em 2026 ou, sem data do fato,
    registrados em 2026 (critério conservador)."""
    fato = df["data_fato"]
    return (fato >= SEAL_FROM) | (fato.isna() & (df["data_registro"] >= SEAL_FROM))


def event_id(df: pd.DataFrame) -> pd.Series:
    """Identificador estável do evento, derivado da chave do BO sem expô-la."""
    key = (df["fonte"].astype(str) + "|" + df["delegacia_registro"].fillna("").astype(str) + "|"
           + df["id_delegacia"].fillna("").astype(str) + "|" + df["ano_bo"].fillna("").astype(str)
           + "|" + df["num_bo"].fillna("").astype(str) + "|" + df["natureza_norm"].fillna("").astype(str))
    return key.map(lambda k: hashlib.sha1(k.encode()).hexdigest()[:16])


def dedup_ssp(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(["delegacia_registro", "ano_bo", "num_bo", "natureza_norm", "rubrica"])


def dedup_celular(df: pd.DataFrame) -> pd.DataFrame:
    return (df.assign(_v=df["versao"].fillna(-1))
              .sort_values("_v", ascending=False)
              .drop_duplicates(["id_delegacia", "ano_bo", "num_bo"])
              .drop(columns="_v"))


def celular_natureza(rubrica: pd.Series) -> pd.Series:
    r = rubrica.map(norm_text)
    return pd.Series(pd.NA, index=r.index, dtype="string").mask(
        r.str.startswith("ROUBO"), "ROUBO DE CELULAR").mask(
        r.str.startswith("FURTO"), "FURTO DE CELULAR")


def events_letal(df: pd.DataFrame) -> pd.DataFrame:
    ev = df[df["natureza_norm"].isin(LETAL_COMPOSTO)].copy()
    ev["desfecho"] = "letal"
    ev["estrito"] = ev["natureza_norm"].isin(LETAL_ESTRITO)
    ev["natureza"] = ev["natureza_norm"]
    return ev


def events_celular(df: pd.DataFrame) -> pd.DataFrame:
    ev = df[df["status"].map(norm_text).eq("CONSUMADO")].copy()
    ev["natureza"] = celular_natureza(ev["rubrica"])
    ev = ev[ev["natureza"].notna()]
    ev["desfecho"] = "celular"
    ev["estrito"] = True
    return ev


# Painel de fenótipos do atlas (docs/NARRATIVA.md, P1). Ficam fora a iniciativa policial (tráfico,
# porte), o estupro e a violência doméstica (D14). Celular e letal vêm dos próprios eventos; os BOs
# com celular saem de FURTO/ROUBO - OUTROS para os fenótipos não se sobreporem.
FENOTIPO_CONDUTA = {
    "fios_cabos": {"FIOS E CABOS"},
    "interior_veiculo": {"INTERIOR DE VEICULO"},
    "residencia": {"RESIDENCIA", "CONDOMINIO RESIDENCIAL"},
    "comercio": {"ESTABELECIMENTO COMERCIAL", "INTERIOR ESTABELECIMENTO", "ESTABELECIMENTO-OUTROS",
                 "CONDOMINIO COMERCIAL"},
    "coletivo": {"INTERIOR TRANSPORTE COLETIVO", "COLETIVO"},
}
FENOTIPO_NATUREZA = {
    "furto_veiculo": {"FURTO DE VEICULO"},
    "roubo_veiculo": {"ROUBO DE VEICULO"},
    "carga": {"ROUBO DE CARGA", "FURTO DE CARGA"},
    "lesao_dolosa": {"LESAO CORPORAL DOLOSA"},
    "transito": {"LESAO CORPORAL CULPOSA POR ACIDENTE DE TRANSITO", "HOMICIDIO CULPOSO POR ACIDENTE DE TRANSITO"},
}


def fenotipo_ssp(df: pd.DataFrame, bo_celular: pd.Series) -> pd.Series:
    """Fenótipo de cada linha da base principal (NA = fora do painel). ``bo_celular`` marca as
    linhas cujo BO está na base de celulares."""
    nat = df["natureza_norm"].fillna("")
    cond = df["conduta"].fillna("").map(norm_text)
    outros = nat.isin({"FURTO - OUTROS", "ROUBO - OUTROS"}) & ~bo_celular.fillna(False).astype(bool)
    out = pd.Series(pd.NA, index=df.index, dtype="string")
    for f, conds in FENOTIPO_CONDUTA.items():
        out = out.mask(outros & cond.isin(conds) & out.isna(), f)
    pessoa = outros & cond.isin({"OUTROS", "TRANSEUNTE"}) & out.isna()
    out = out.mask(pessoa & nat.eq("ROUBO - OUTROS"), "roubo_outros").mask(pessoa & nat.eq("FURTO - OUTROS"), "furto_outros")
    for f, nats in FENOTIPO_NATUREZA.items():
        out = out.mask(nat.isin(nats) & out.isna(), f)
    return out


def to_events(ev: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    ev["evento_id"] = event_id(ev)
    ev["tem_logradouro"] = ev["logradouro"].notna() & ~ev["logradouro"].map(norm_text).str.startswith("VEDACAO")
    return ev[EVENT_COLUMNS].reset_index(drop=True)


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def parse_file(fonte: str, ano: int, path: Path | None = None, log=print) -> ParseResult:
    """Processa um xlsx anual. ``fonte`` é 'ssp' (SPDadosCriminais) ou 'celular'."""
    stem = {"ssp": "SPDadosCriminais", "celular": "CelularesSubtraidos"}[fonte]
    path = path or xlsx_dir() / f"{stem}_{ano}.xlsx"
    parts = []
    for name, sheet in _data_sheets(path).items():
        h = harmonize(sheet, fonte, ano)
        parts.append(h[is_capital(h["municipio_fato"])])
    df = pd.concat(parts, ignore_index=True)
    df = dedup_ssp(df) if fonte == "ssp" else dedup_celular(df)

    sealed = is_sealed(df)
    open_part, sealed_part = df[~sealed], df[sealed]
    _write(open_part, raw_dir() / "bo" / f"{fonte}_{ano}.parquet")
    if len(sealed_part):
        _write(sealed_part, sealed_path_for_write(f"bo_{fonte}_{ano}.parquet"))

    make = {"ssp": [("letal", events_letal)], "celular": [("celular", events_celular)]}[fonte]
    counts = {}
    for desfecho, fn in make:
        ev_open, ev_sealed = to_events(fn(open_part)), to_events(fn(sealed_part))
        _write(ev_open, interim_dir() / f"eventos_{desfecho}_{fonte}_{ano}.parquet")
        if len(ev_sealed):
            _write(ev_sealed, sealed_path_for_write(f"eventos_{desfecho}_{fonte}_{ano}.parquet"))
        counts[desfecho] = len(ev_open)

    log(f"[{fonte} {ano}] capital fora do cofre: {len(open_part):,} linhas | "
        f"eventos: {counts} | enviados ao cofre: {int(sealed.sum()):,}")
    return ParseResult(fonte, ano, len(open_part), int(sealed.sum()), counts)


def combine_events(desfecho: str) -> pd.DataFrame:
    """Une os eventos fora do cofre de todos os anos, deduplicando entre arquivos
    (vale a versão do arquivo mais recente)."""
    files = sorted(interim_dir().glob(f"eventos_{desfecho}_*_*.parquet"))
    ev = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    ev = ev.sort_values("arquivo_ano").drop_duplicates("evento_id", keep="last")
    out = interim_dir() / f"eventos_{desfecho}.parquet"
    _write(ev.reset_index(drop=True), out)
    return ev
