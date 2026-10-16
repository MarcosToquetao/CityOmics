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




freeze_app = typer.Typer(help="F4: congelamento do plano antes de abrir 2026.")
app.add_typer(freeze_app, name="freeze")


@freeze_app.command("check")
def freeze_check(skip_tests: bool = typer.Option(False, "--skip-tests", help="Não roda o pytest.")) -> None:
    """Lista o que falta para congelar o plano."""
    from cityomics import freeze

    problems = freeze.check(run_tests=not skip_tests)
    for p in problems:
        typer.echo(f"- {p}", err=True)
    if problems:
        raise typer.Exit(code=1)
    typer.echo("Pronto para congelar.")


@freeze_app.command("commit")
def freeze_commit(confirm: bool = typer.Option(False, "--confirm", help="Confirma o congelamento (irreversível).")) -> None:
    """Grava o manifesto, faz o commit de congelamento e grava prereg/UNSEAL_KEY."""
    from cityomics import freeze

    if not confirm:
        typer.echo("Use --confirm: depois do congelamento a seleção de modelos não pode mais mudar.", err=True)
        raise typer.Exit(code=2)
    typer.echo(freeze.freeze(log=typer.echo))


atlas_app = typer.Typer(help="F6: atlas mínimo (tipos, nichos, comunicação, atribuição).")
app.add_typer(atlas_app, name="atlas")

ATLAS_STEPS = ["genes", "ruas", "tipagem", "spots", "nichos", "atribuicao", "variancia", "preditores", "comunicacao", "destino", "letal"]


@atlas_app.command("run")
def atlas_run(steps: list[str] = typer.Argument(None, help=f"Etapas, na ordem: {', '.join(ATLAS_STEPS)} (padrão: todas).")) -> None:
    """Roda as etapas do atlas. Nada de 2026 é lido; o crime exclui o cofre espacial (D53)."""
    from cityomics.atlas import attribution, communication, fate, genes_lote, niches, predictors, spots, streets, typing, variance
    from cityomics.models import letal_run
    from cityomics.units.setores import load_setores

    run = {"genes": genes_lote.build, "ruas": lambda log: streets.build(load_setores(), log=log), "tipagem": typing.run,
           "spots": spots.build, "nichos": niches.run, "atribuicao": attribution.run, "variancia": variance.run,
           "preditores": predictors.shap_celular, "comunicacao": communication.run, "destino": fate.run, "letal": letal_run.run}
    for s in steps or ATLAS_STEPS:
        typer.echo(f"== {s}")
        run[s](log=typer.echo)


@app.command("figures")
def figures(periodo: str = typer.Option("dev", help="dev (2025) ou 2026 (só com o cofre aberto, D52)."),
            only: list[str] = typer.Option(None, "--only", help="fig1 … fig6, ed")) -> None:
    """Gera as figuras do artigo em figures/out/<periodo>/ (PDF vetorial + PNG de 450 dpi)."""
    from cityomics.viz import runner

    runner.run(periodo, only=only or None, log=typer.echo)


@app.command("explorer")
def explorer(public: bool = typer.Option(False, "--public", help="Versão pública por lista branca (D49, D60)."),
             port: int = typer.Option(8790, help="Porta do servidor local."),
             reuse: bool = typer.Option(False, "--reuse", help="Reaproveita os zarr e refaz só a configuração.")) -> None:
    """Monta o explorador Vitessce em explorer/local/ ou explorer/public/."""
    from cityomics.explorer.build import build

    build(public=public, port=port, reuse=reuse, log=typer.echo)


if __name__ == "__main__":
    app()
