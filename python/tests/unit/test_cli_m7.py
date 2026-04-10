"""Smoke tests for M7 CLI commands.

Tests that each command returns exit_code 0 and key output fields are present.
All temperatures passed via CLI are in degrees Celsius; commands convert to K internally.
"""

from __future__ import annotations

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# h-coeff forced
# ---------------------------------------------------------------------------


def test_h_coeff_forced_smoke():
    """h-coeff forced returns h= and Re= in output."""
    result = runner.invoke(
        app,
        [
            "h-coeff",
            "forced",
            "--length",
            "0.3",
            "--velocity",
            "5.0",
            "--t-ambient",
            "40",
            "--t-surface",
            "80",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "h=" in result.output
    assert "Re=" in result.output


# ---------------------------------------------------------------------------
# h-coeff natural
# ---------------------------------------------------------------------------


def test_h_coeff_natural_smoke():
    """h-coeff natural returns h= and Nu= in output."""
    result = runner.invoke(
        app,
        [
            "h-coeff",
            "natural",
            "--orientation",
            "vertical",
            "--length",
            "0.2",
            "--t-ambient",
            "25",
            "--t-surface",
            "65",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "h=" in result.output
    assert "Nu=" in result.output


# ---------------------------------------------------------------------------
# h-coeff radiation
# ---------------------------------------------------------------------------


def test_h_coeff_radiation_smoke():
    """h-coeff radiation returns h= in output."""
    result = runner.invoke(
        app,
        [
            "h-coeff",
            "radiation",
            "--emissivity",
            "0.9",
            "--t-ambient",
            "25",
            "--t-surface",
            "70",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "h=" in result.output


# ---------------------------------------------------------------------------
# radiation parallel
# ---------------------------------------------------------------------------


def test_radiation_parallel_smoke():
    """radiation parallel returns q= in output."""
    result = runner.invoke(
        app,
        [
            "radiation",
            "parallel",
            "--t1",
            "500",
            "--t2",
            "300",
            "--area",
            "1.0",
            "--eps1",
            "0.9",
            "--eps2",
            "0.9",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "q=" in result.output


def test_radiation_cylinder_smoke():
    """radiation cylinder returns q= in output."""
    result = runner.invoke(
        app,
        [
            "radiation",
            "cylinder",
            "--t1",
            "500",
            "--t2",
            "300",
            "--r1",
            "0.05",
            "--r2",
            "0.1",
            "--length",
            "1.0",
            "--eps1",
            "0.9",
            "--eps2",
            "0.9",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "q=" in result.output


def test_radiation_sphere_smoke():
    """radiation sphere returns q= in output."""
    result = runner.invoke(
        app,
        [
            "radiation",
            "sphere",
            "--t1",
            "500",
            "--t2",
            "300",
            "--r1",
            "0.05",
            "--r2",
            "0.1",
            "--eps1",
            "0.9",
            "--eps2",
            "0.9",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "q=" in result.output


def test_radiation_enclosure_smoke():
    """radiation enclosure returns q= in output."""
    result = runner.invoke(
        app,
        [
            "radiation",
            "enclosure",
            "--t1",
            "500",
            "--t2",
            "300",
            "--eps1",
            "0.9",
            "--eps2",
            "0.9",
            "--a1",
            "1.0",
            "--a2",
            "2.0",
            "--f12",
            "0.5",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "q=" in result.output


def test_radiation_convex_smoke():
    """radiation convex returns q= in output."""
    result = runner.invoke(
        app,
        [
            "radiation",
            "convex",
            "--t1",
            "500",
            "--t2",
            "300",
            "--a1",
            "0.5",
            "--eps1",
            "0.9",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "q=" in result.output


# ---------------------------------------------------------------------------
# free-conv
# ---------------------------------------------------------------------------


def test_free_conv_smoke():
    """free-conv returns t_surface= in output."""
    result = runner.invoke(
        app,
        [
            "free-conv",
            "--t-ambient",
            "25",
            "--p-total",
            "50",
            "--face",
            "area=0.04,length=0.2,orientation=vertical,emissivity=0.9",
            "--face",
            "area=0.02,length=0.1,orientation=horizontal_top,emissivity=0.9",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "t_surface=" in result.output


# ---------------------------------------------------------------------------
# water-cooling
# ---------------------------------------------------------------------------


def test_water_cooling_smoke():
    """water-cooling returns t_junction= in output."""
    result = runner.invoke(
        app,
        [
            "water-cooling",
            "--p-loss",
            "1000",
            "--flow",
            "10",
            "--t-in",
            "40",
            "--rth-jc",
            "0.05",
            "--n-devices",
            "6",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "t_junction=" in result.output


# ---------------------------------------------------------------------------
# natural-conv-hs
# ---------------------------------------------------------------------------


def test_natural_conv_hs_smoke():
    """natural-conv-hs returns rth= in output."""
    result = runner.invoke(
        app,
        [
            "natural-conv-hs",
            "--n-fins",
            "12",
            "--fin-height",
            "0.08",
            "--fin-length",
            "0.15",
            "--fin-thickness",
            "0.002",
            "--channel-width",
            "0.006",
            "--base-thickness",
            "0.01",
            "--k",
            "200",
            "--t-ambient",
            "25",
            "--p-loss",
            "30",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "rth=" in result.output


# ---------------------------------------------------------------------------
# hydraulic-op (YAML config required)
# ---------------------------------------------------------------------------


def test_hydraulic_op_smoke(tmp_path):
    """hydraulic-op with a valid YAML config returns reynolds= in output."""
    cfg = tmp_path / "hs_op.yaml"
    cfg.write_text(
        """\
heatsink:
  profile: I117
  length: 0.2
  width: 0.15
fan:
  model: EBMW2E200_axial_AC_50Hz
  count: 1
ventilation:
  type: push
ambient:
  tInlet: 313.15
"""
    )
    result = runner.invoke(app, ["hydraulic-op", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "reynolds=" in result.output
    assert "flowrate=" in result.output


# ---------------------------------------------------------------------------
# fin-rth (YAML config required)
# ---------------------------------------------------------------------------


def test_fin_rth_smoke(tmp_path):
    """fin-rth with a valid YAML config and --flowrate returns rth= in output."""
    cfg = tmp_path / "hs_rth.yaml"
    cfg.write_text(
        """\
heatsink:
  profile: I117
  material: all_aluminum
  length: 0.2
  width: 0.15
fan:
  model: EBMW2E200_axial_AC_50Hz
  count: 1
ventilation:
  type: push
ambient:
  tInlet: 313.15
"""
    )
    result = runner.invoke(app, ["fin-rth", "--config", str(cfg), "--flowrate", "0.05"])
    assert result.exit_code == 0, result.output
    assert "rth=" in result.output
