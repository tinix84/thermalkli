"""Smoke tests for M8 CLI commands: cspi, cspi-optimize, fan-fit, cspi-sweep."""

from __future__ import annotations

import textwrap

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# cspi
# ---------------------------------------------------------------------------


def test_cspi_smoke():
    """cspi with --rth and --vol returns cspi= in output."""
    result = runner.invoke(
        app,
        [
            "cspi",
            "--rth",
            "0.5",
            "--vol",
            "2.0",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "cspi=" in result.output


# ---------------------------------------------------------------------------
# cspi-optimize
# ---------------------------------------------------------------------------


def test_cspi_optimize_smoke():
    """cspi-optimize returns cspi=, rth=, n_fins= in output."""
    result = runner.invoke(
        app,
        [
            "cspi-optimize",
            "--lambda",
            "200",
            "--a-chip",
            "10e-4",
            "--c",
            "0.04",
            "--p-fan",
            "5",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "cspi=" in result.output
    assert "rth=" in result.output
    assert "n_fins=" in result.output


# ---------------------------------------------------------------------------
# fan-fit
# ---------------------------------------------------------------------------


def test_fan_fit_smoke():
    """fan-fit returns k1=, k2=, k3= in output."""
    result = runner.invoke(
        app,
        [
            "fan-fit",
            "--v-max",
            "0.05",
            "--dp-max",
            "50",
            "--p-fan",
            "3",
            "--diameter",
            "0.12",
            "--speed",
            "2500",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "k1=" in result.output
    assert "k2=" in result.output
    assert "k3=" in result.output


# ---------------------------------------------------------------------------
# cspi-sweep
# ---------------------------------------------------------------------------


def test_cspi_sweep_smoke(tmp_path):
    """cspi-sweep with a valid YAML config returns a table with lambda values."""
    cfg = tmp_path / "sweep.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            a_chip: 10e-4
            p_fan_max: 5.0
            lambda: [200, 385]
            c: [0.030, 0.040]
            t_min: 0.0
            """
        )
    )
    result = runner.invoke(app, ["cspi-sweep", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    # Should contain lambda values in header
    assert "200" in result.output
    assert "385" in result.output
