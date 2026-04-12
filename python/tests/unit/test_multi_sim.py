"""Tests for thermal_cli.sweep.multi_sim."""

from __future__ import annotations

import pytest

from thermal_cli.sweep.multi_sim import (
    MultiSimResult,
    MultiSimScenario,
    run_multi_sim,
)


def _sample_scenario(name: str, k: float) -> MultiSimScenario:
    """Small 2-device baseplate, parameterised only by conductivity."""
    return MultiSimScenario(
        name=name,
        lx=0.12,
        ly=0.08,
        thickness=0.005,
        conductivity=k,
        r_sa=0.1,
        t_ambient=298.15,
        devices=[
            {"name": "Q1", "x": 0.03, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
            {"name": "Q2", "x": 0.09, "y": 0.04, "width": 0.02, "height": 0.02, "power": 100.0},
        ],
        nx=21,
        ny=21,
    )


class TestRunMultiSim:
    def test_runs_all_scenarios(self):
        scenarios = [
            _sample_scenario("Al", 200.0),
            _sample_scenario("Cu", 385.0),
        ]
        result = run_multi_sim(scenarios)
        assert isinstance(result, MultiSimResult)
        assert len(result.rows) == 2
        assert [r.name for r in result.rows] == ["Al", "Cu"]

    def test_higher_conductivity_lower_t_max(self):
        al = _sample_scenario("Al", 200.0)
        cu = _sample_scenario("Cu", 385.0)
        result = run_multi_sim([al, cu])
        row_al = next(r for r in result.rows if r.name == "Al")
        row_cu = next(r for r in result.rows if r.name == "Cu")
        assert row_cu.t_j_max < row_al.t_j_max

    def test_per_device_peaks_present(self):
        result = run_multi_sim([_sample_scenario("Al", 200.0)])
        row = result.rows[0]
        assert set(row.t_j_per_device.keys()) == {"Q1", "Q2"}
        assert all(v > row.t_ambient for v in row.t_j_per_device.values())

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            run_multi_sim([])
