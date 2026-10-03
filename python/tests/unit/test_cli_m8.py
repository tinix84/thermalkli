"""Smoke tests for M8 CLI commands: cspi, cspi-optimize, fan-fit, cspi-sweep."""

from __future__ import annotations

import textwrap
from types import SimpleNamespace

import pytest
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
    assert "operating_point_status=converged" in result.output
    assert "flow_m3_s=" in result.output
    assert "fan_static_pressure_Pa=" in result.output
    assert "pressure_drop_Pa=" in result.output
    assert "fin_spacing_ratio_k=" in result.output
    assert "fan/channel aggregate flow equality assumes no bypass" in result.output
    assert "sink_volume_L=" in result.output
    assert "fan_curve_model=parabolic fit to similarity endpoints" in result.output


def test_cspi_optimize_reports_no_fan_system_intersection():
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
            "--fan-flow-curve",
            "0,0.0001",
            "--fan-pressure-curve",
            "0,0",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "operating_point_status=no_intersection" in result.output
    assert "flow_m3_s=unavailable" in result.output
    assert "feasible=false" in result.output


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


def test_cspi_optimize_reports_heated_faces_hydraulic_branches_and_unspecified_rpm():
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
            "--face-count",
            "2",
            "--hydraulic-branch-count",
            "1",
            "--fan-free-flow",
            "0.009",
            "--fan-shutoff-pressure",
            "300",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "heated_faces=2" in result.output
    assert "hydraulic_branches=1" in result.output
    assert "N_fan=unspecified" in result.output


def test_cspi_sweep_forwards_strict_face_and_hydraulic_counts(tmp_path, monkeypatch):
    captured = {}

    def fake_cspi_sweep(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(cs=[0.03], lambdas=[200.0], cspi={(0, 0): 1.0})

    monkeypatch.setattr("thermal_cli.cspi.optimizer.cspi_sweep", fake_cspi_sweep)
    cfg = tmp_path / "sweep.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            a_chip: 0.001
            p_fan_max: 5.0
            lambda: [200]
            c: [0.03]
            face_count: 2
            hydraulic_branch_count: 1
            """
        )
    )

    result = runner.invoke(app, ["cspi-sweep", "--config", str(cfg)])

    assert result.exit_code == 0, result.output
    assert captured["face_count"] == 2
    assert captured["hydraulic_branch_count"] == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("face_count", "2.5"),
        ("face_count", "true"),
        ("hydraulic_branch_count", "1.5"),
        ("hydraulic_branch_count", "true"),
    ],
)
def test_cspi_sweep_rejects_fractional_or_boolean_counts(tmp_path, field, value):
    cfg = tmp_path / "sweep.yaml"
    cfg.write_text(
        textwrap.dedent(
            f"""\
            a_chip: 0.001
            p_fan_max: 5.0
            lambda: [200]
            c: [0.03]
            {field}: {value}
            """
        )
    )

    result = runner.invoke(app, ["cspi-sweep", "--config", str(cfg)])

    assert result.exit_code != 0
    assert f"{field} must be an integer >= 1" in result.output


def test_cspi_sweep_rejects_multiple_hydraulic_bodies(tmp_path):
    cfg = tmp_path / "sweep.yaml"
    cfg.write_text(
        textwrap.dedent(
            """            a_chip: 0.001
            p_fan_max: 5.0
            lambda: [200]
            c: [0.03]
            hydraulic_branch_count: 2
            """
        )
    )

    result = runner.invoke(app, ["cspi-sweep", "--config", str(cfg)])

    assert result.exit_code != 0
    assert "hydraulic_branch_count must be 1" in result.output
