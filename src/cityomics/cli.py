"""Linha de comando ``cityomics``.

Por enquanto expõe só utilitários de F0. Os comandos de pipeline (ingest, units, run…)
entram junto com as fases correspondentes.
"""

from __future__ import annotations

import typer

from cityomics import __version__, paths, privacy, sealed

app = typer.Typer(add_completion=False, help="CityOmics: crime em SP e atlas urbano.")


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


if __name__ == "__main__":
    app()
