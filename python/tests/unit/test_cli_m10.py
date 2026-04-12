"""Smoke tests for M10 CLI command: forced-conv-sim."""

from __future__ import annotations

import textwrap

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()

_BASIC_YAML = textwrap.dedent(
    """\
    heatsink:
      profile: VHSmallHeatsink28mm
      material: all_aluminum
      length_x_mm: 63.0
      length_y_mm: 130.0
      copper_plate_thickness_mm: 0.0

    fan:
      model: JF0825-1H-02
      count: 1
      ventilation: push
      impinge_gap_mm: 0.0

    sources:
      - name: Q1
        x_mm: 16.5
        y_mm: 11.0
        width_mm: 13.0
        height_mm: 13.0
        power_w: 30.0
      - name: Q2
        x_mm: 16.5
        y_mm: 35.5
        width_mm: 13.0
        height_mm: 13.0
        power_w: 30.0

    environment:
      t_inlet_c: 40.0

    grid:
      nx: 7
      ny: 7
      n_fourier: 5
    """
)


def test_forced_conv_sim_smoke(tmp_path):
    cfg = tmp_path / "sim.yaml"
    cfg.write_text(_BASIC_YAML)
    result = runner.invoke(app, ["forced-conv-sim", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "t_base_max" in result.output
    assert "q_operating" in result.output


def test_forced_conv_sim_missing_config(tmp_path):
    missing = tmp_path / "does_not_exist.yaml"
    result = runner.invoke(app, ["forced-conv-sim", "--config", str(missing)])
    assert result.exit_code != 0
