"""Tests for thermal_cli.forced_conv.plane_temp."""

from __future__ import annotations

import numpy as np

from thermal_cli.forced_conv.plane_temp import PlaneTempConfig, calc_plane_temp


def _single_source_cfg(**kwargs) -> PlaneTempConfig:
    """Minimal config with one centred 100W source, all-aluminum, push."""
    defaults = dict(
        rth_fin=0.05,
        h_eq=100.0,
        sources=[
            {
                "name": "Q1", "x_mm": 150.0, "y_mm": 100.0,
                "width_mm": 50.0, "height_mm": 30.0, "power_w": 100.0,
            }
        ],
        t_air_c=50.0,
        t_inlet_c=40.0,
        a_mm=300.0,
        b_mm=200.0,
        k_plate=200.0,
        tb_mm=15.0,
        has_piastra=False,
        k_piastra=0.0,
        tr_mm=0.0,
        n_fourier=10,
    )
    defaults.update(kwargs)
    return PlaneTempConfig(**defaults)


class TestCalcPlaneTempBasic:
    def test_returns_plane_temp_result(self):
        cfg = _single_source_cfg()
        x = np.linspace(0, 300, 7)
        y = np.linspace(0, 200, 5)
        result = calc_plane_temp(cfg, x, y)
        assert result.t_grid_c.shape == (5, 7)
        assert result.t_max_c > result.t_base_c

    def test_all_temperatures_above_base(self):
        """Every grid point must be at or above T_h_BP."""
        cfg = _single_source_cfg()
        x = np.linspace(0, 300, 11)
        y = np.linspace(0, 200, 9)
        result = calc_plane_temp(cfg, x, y)
        assert np.all(result.t_grid_c >= result.t_base_c - 1e-6)

    def test_peak_near_source_centroid(self):
        """Peak temperature should be closest to source centroid in the grid."""
        cfg = _single_source_cfg()
        x = np.linspace(0, 300, 31)
        y = np.linspace(0, 200, 21)
        result = calc_plane_temp(cfg, x, y)
        iy, ix = np.unravel_index(np.argmax(result.t_grid_c), result.t_grid_c.shape)
        # Grid point nearest centroid (150, 100) — within 15mm tolerance
        assert abs(x[ix] - 150.0) <= 15.0
        assert abs(y[iy] - 100.0) <= 15.0

    def test_higher_power_higher_t_max(self):
        """Doubling source power must increase peak temperature."""
        cfg_low = _single_source_cfg()
        cfg_high = _single_source_cfg(
            sources=[{"name": "Q1", "x_mm": 150.0, "y_mm": 100.0,
                      "width_mm": 50.0, "height_mm": 30.0, "power_w": 200.0}]
        )
        x = np.linspace(0, 300, 11)
        y = np.linspace(0, 200, 9)
        r_low = calc_plane_temp(cfg_low, x, y)
        r_high = calc_plane_temp(cfg_high, x, y)
        assert r_high.t_max_c > r_low.t_max_c

    def test_two_equal_sources_symmetric_field(self):
        """Two sources symmetric about x=a/2 must produce a symmetric temperature field."""
        cfg = PlaneTempConfig(
            rth_fin=0.05,
            h_eq=100.0,
            sources=[
                {
                    "name": "Q1", "x_mm": 75.0, "y_mm": 100.0,
                    "width_mm": 30.0, "height_mm": 30.0, "power_w": 100.0,
                },
                {
                    "name": "Q2", "x_mm": 225.0, "y_mm": 100.0,
                    "width_mm": 30.0, "height_mm": 30.0, "power_w": 100.0,
                },
            ],
            t_air_c=50.0,
            t_inlet_c=40.0,
            a_mm=300.0,
            b_mm=200.0,
            k_plate=200.0,
            tb_mm=15.0,
            has_piastra=False,
            k_piastra=0.0,
            tr_mm=0.0,
            n_fourier=15,
        )
        x = np.linspace(0, 300, 13)   # odd number so x=150 is in the grid
        y = np.linspace(0, 200, 9)
        result = calc_plane_temp(cfg, x, y)
        # T at x[i] should equal T at x[-(i+1)] for all rows
        np.testing.assert_allclose(result.t_grid_c, result.t_grid_c[:, ::-1], atol=1e-4)

    def test_with_piastra_higher_t_base(self):
        """Adding a copper spreading plate increases T_h_BP (more thermal resistance)."""
        cfg_no = _single_source_cfg()
        cfg_yes = _single_source_cfg(has_piastra=True, k_piastra=350.0, tr_mm=2.0)
        x = np.linspace(0, 300, 7)
        y = np.linspace(0, 200, 5)
        r_no = calc_plane_temp(cfg_no, x, y)
        r_yes = calc_plane_temp(cfg_yes, x, y)
        assert r_yes.t_base_c > r_no.t_base_c
