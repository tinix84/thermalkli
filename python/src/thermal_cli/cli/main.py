"""Typer entry point for the thermal-cli package."""

from __future__ import annotations

from pathlib import Path

import typer

from thermal_cli import __version__
from thermal_cli.cli.commands_m7 import register_all
from thermal_cli.cli.commands_m8 import register_all as register_m8
from thermal_cli.cli.commands_m9 import register_all as register_m9
from thermal_cli.cli.commands_m10 import register_all as register_m10

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


@app.command()
def convert_config(
    m_file: Path = typer.Argument(..., help="Input .m config file"),
    yaml_file: Path = typer.Argument(..., help="Output .yaml config file"),
) -> None:
    """Convert an Octave .m struct config to YAML."""
    from thermal_cli.io.convert_m_to_yaml import convert_m_to_yaml

    if not m_file.exists():
        typer.echo(f"Error: {m_file} not found")
        raise typer.Exit(1)
    convert_m_to_yaml(m_file, yaml_file)
    typer.echo(f"Converted {m_file} → {yaml_file}")


register_all(app)
register_m8(app)
register_m9(app)
register_m10(app)


if __name__ == "__main__":
    app()
