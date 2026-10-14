"""Linha de comando ``cityomics``."""

from __future__ import annotations

from pathlib import Path

import typer

from cityomics import __version__, paths, privacy, sealed

app = typer.Typer(add_completion=False, help="CityOmics: crime em SP e atlas urbano.")
ingest_app = typer.Typer(help="F1: ingestão dos microdados de BO da SSP.")
app.add_typer(ingest_app, name="ingest")


@app.command()
def info() -> None:
    """Mostra versão, diretórios de dados e o estado do cofre de 2026."""
    typer.echo(f"cityomics {__version__}")
    typer.echo(f"dados:     {paths.data_dir()}")
    typer.echo(f"cofre:     {paths.sealed_dir()}")
    key = sealed.registered_key()
    typer.echo(f"chave:     {key or 'nenhuma (plano ainda não congelado)'}")
    typer.echo(f"2026:      {'aberto nesta sessão' if sealed.is_unsealed() else 'lacrado'}")


@app.command("privacy-scan")
def privacy_scan() -> None:
    """Procura chaves no repositório e colunas identificadoras em data/processed."""
    findings = privacy.scan_repo() + privacy.scan_tables()
    for finding in findings:
        typer.echo(str(finding), err=True)
    if findings:
        raise typer.Exit(code=1)
    typer.echo("Nenhum problema encontrado.")


@ingest_app.command("snapshot")
def ingest_snapshot(
    copy_from: Path = typer.Option(None, help="Diretório com cópias locais dos xlsx (ex.: ../MapaSegurancaSP/data/raw)."),
    verify: bool = typer.Option(False, "--verify", help="Só confere os sha256 do snapshot existente."),
) -> None:
    """Congela os xlsx da SSP em data/raw/xlsx com sha256 (D18)."""
    from cityomics.ingest import snapshot

    if verify:
        problems = snapshot.verify()
        for p in problems:
            typer.echo(p, err=True)
        raise typer.Exit(code=1 if problems else 0)
    snapshot.build(copy_from=copy_from, log=typer.echo)


@ingest_app.command("parse")
def ingest_parse(years: list[int] = typer.Argument(None)) -> None:
    """Lê os xlsx, recorta a capital, deriva os eventos e envia 2026 ao cofre."""
    from cityomics.ingest import ssp
    from cityomics.ingest.sources import YEARS

    for fonte in ("ssp", "celular"):
        for year in years or YEARS:
            ssp.parse_file(fonte, year, log=typer.echo)
    for desfecho in ("letal", "celular"):
        ssp.combine_events(desfecho)


@ingest_app.command("check")
def ingest_check() -> None:
    """Compara os totais anuais (2022–2025) com a tabela oficial da SSP."""
    from cityomics.ingest import check

    table = check.compare()
    typer.echo(table.to_string(index=False))
    if table["alerta"].any():
        typer.echo(f"\nDiferenças acima de {check.TOLERANCE_PCT}% marcadas em 'alerta'.", err=True)


units_app = typer.Typer(help="F2: unidades, atribuição dos eventos e reconciliação.")
app.add_typer(units_app, name="units")


@units_app.command("build")
def units_build() -> None:
    """Setores 2022, distritos, atribuição dos eventos e alvos agregados."""
    from cityomics.units import build

    build.run(log=typer.echo)


@units_app.command("lotes")
def units_lotes(download: bool = typer.Option(False, "--download", help="Baixa os GPKG de lotes do GeoSampa.")) -> None:
    """Lotes fiscais + pseudo-lotes de favela, com setor 2022 pelo centroide."""
    from cityomics import geosampa
    from cityomics.units import lotes

    if download:
        geosampa.fetch_lotes(log=typer.echo)
    lotes.build_lotes(log=typer.echo)


cov_app = typer.Typer(help="F3: covariáveis.")
app.add_typer(cov_app, name="covariates")


@cov_app.command("iptu")
def covariates_iptu(
    years: list[int] = typer.Argument(None),
    download: bool = typer.Option(False, "--download", help="Baixa os zips do IPTU do GeoSampa."),
) -> None:
    """Agrega o cadastro IPTU anual por lote."""
    from cityomics import geosampa
    from cityomics.covariates import iptu
    from cityomics.units import lotes

    years = years or list(range(1995, 2027))
    if download:
        geosampa.fetch_iptu(years, log=typer.echo)
    look = iptu.condo_lookup_from(lotes.load_lotes())
    for year in years:
        out, matched = iptu.build_year(year, look)
        typer.echo(f"{year}: {out.height:,} lotes | imóveis ligados a lote: {matched:.1%}")


if __name__ == "__main__":
    app()
