"""Smoke tests for M9 CLI commands."""

from __future__ import annotations

import textwrap

from typer.testing import CliRunner

from thermal_cli.cli.main import app

runner = CliRunner()


def test_optimize_fin_smoke(tmp_path):
    cfg = tmp_path / "opt.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            axes:
              thick_heatsink: [0.006, 0.008, 0.010]
              thick_wall: [0.0006, 0.0008]
            fixed:
              width_channel: 0.00105
              k_sink: 180.0
              rho_sink: 2698.9
              l_heated: 0.137
              a_hot: 0.00023153
              flowrate_lpm: 1.0
              fluid_ref: H2OGly50
              t_fluid_in: 343.15
              num_channel: 18
            """
        )
    )
    result = runner.invoke(app, ["optimize-fin", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "best" in result.output.lower()
    assert "r_th_total" in result.output


def test_multi_sim_smoke(tmp_path):
    cfg = tmp_path / "msim.yaml"
    cfg.write_text(
        textwrap.dedent(
            """\
            scenarios:
              - name: Al
                lx: 0.12
                ly: 0.08
                thickness: 0.005
                conductivity: 200.0
                r_sa: 0.1
                t_ambient: 298.15
                nx: 21
                ny: 21
                devices:
                  - {name: Q1, x: 0.03, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
                  - {name: Q2, x: 0.09, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
              - name: Cu
                lx: 0.12
                ly: 0.08
                thickness: 0.005
                conductivity: 385.0
                r_sa: 0.1
                t_ambient: 298.15
                nx: 21
                ny: 21
                devices:
                  - {name: Q1, x: 0.03, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
                  - {name: Q2, x: 0.09, y: 0.04, width: 0.02, height: 0.02, power: 100.0}
            """
        )
    )
    result = runner.invoke(app, ["multi-sim", "--config", str(cfg)])
    assert result.exit_code == 0, result.output
    assert "Al" in result.output
    assert "Cu" in result.output
    assert "t_j_max" in result.output


def test_optimize_fin_missing_config_exits_nonzero():
    result = runner.invoke(app, ["optimize-fin", "--config", "/tmp/does_not_exist_m9.yaml"])
    assert result.exit_code != 0


def test_multi_sim_missing_config_exits_nonzero():
    result = runner.invoke(app, ["multi-sim", "--config", "/tmp/does_not_exist_m9.yaml"])
    assert result.exit_code != 0
