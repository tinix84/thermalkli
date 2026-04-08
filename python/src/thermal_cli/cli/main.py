"""Typer entry point for the thermal-cli package."""

from __future__ import annotations

import typer

from thermal_cli import __version__

app = typer.Typer(
    name="thermal",
    help="thermal-cli — Python port of the Octave thermal engineering library.",
    add_completion=False,
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"thermal-cli {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """thermal-cli root command."""


if __name__ == "__main__":
    app()
