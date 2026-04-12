"""Tests for thermal_cli.forced_conv.workflow."""

from __future__ import annotations

import pytest

from thermal_cli.forced_conv.workflow import ForcedConvConfig, ForcedConvResult, run_forced_conv_sim


def _vh_cfg(**kwargs) -> ForcedConvConfig:
    """Minimal config: VH small heatsink, JF0825 fan, push, 2 sources at 30W each."""
    defaults = dict(
        hs_profile="VHSmallHeatsink28mm",
        hs_material="all_aluminum",
        length_x_m=0.063,
        length_y_m=0.130,
        copper_plate_thickness_m=0.0,
        fan_model="JF0825-1H-02",
        fan_count=1,
        ventilation="push",
        impinge_gap_m=0.0,
        sources=[
            {
                "name": "Q1",
                "x_m": 0.0165,
                "y_m": 0.011,
                "width_m": 0.013,
                "height_m": 0.013,
                "power_w": 30.0,
            },
            {
                "name": "Q2",
                "x_m": 0.0165,
                "y_m": 0.0355,
                "width_m": 0.013,
                "height_m": 0.013,
                "power_w": 30.0,
            },
        ],
        t_inlet_k=313.15,
        nx=11,
        ny=11,
        n_fourier=10,
    )
    defaults.update(kwargs)
    return ForcedConvConfig(**defaults)


class TestRunForcedConvSim:
    def test_returns_forced_conv_result(self):
        result = run_forced_conv_sim(_vh_cfg())
        assert isinstance(result, ForcedConvResult)
        assert result.t_base_max_k > 0
        assert result.q_operating_m3s > 0
        assert result.rth_fin_kw > 0

    def test_peak_temperature_above_inlet(self):
        result = run_forced_conv_sim(_vh_cfg())
        assert result.t_base_max_k > 313.15

    def test_more_fans_lower_temperature(self):
        """Two fans in parallel → lower heatsink temperature than one fan."""
        r1 = run_forced_conv_sim(_vh_cfg(fan_count=1))
        r2 = run_forced_conv_sim(_vh_cfg(fan_count=2))
        assert r2.t_base_max_k < r1.t_base_max_k

    def test_t_grid_shape(self):
        cfg = _vh_cfg(nx=7, ny=5)
        result = run_forced_conv_sim(cfg)
        assert result.t_grid_k.shape == (5, 7)

    def test_unknown_hs_profile_raises(self):
        with pytest.raises(ValueError, match="not found"):
            run_forced_conv_sim(_vh_cfg(hs_profile="DoesNotExist"))

    def test_unknown_fan_raises(self):
        with pytest.raises(ValueError, match="not found"):
            run_forced_conv_sim(_vh_cfg(fan_model="DoesNotExist"))
