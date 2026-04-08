"""Smoke tests for the Typer CLI entry point."""

from typer.testing import CliRunner

from thermal_cli import __version__
from thermal_cli.cli.main import app

runner = CliRunner()


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_lists_thermal_cli():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "thermal-cli" in result.stdout.lower()
