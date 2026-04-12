"""Analytic sanity checks for the Fourier-series plane temperature solver.

All inputs in SI (m, K) as required by the plane_temp API.
"""

from __future__ import annotations

import numpy as np

from thermal_cli.forced_conv.plane_temp import PlaneTempConfig, calc_plane_temp


class TestPlaneTempLiterature:
    def test_zero_power_zero_delta_theta(self):
        """With zero source power, DTheta must be zero everywhere (T_grid == T_base)."""
        cfg = PlaneTempConfig(
            rth_fin=0.05,
            h_eq=100.0,
            sources=[
                {"name": "Q1", "x_m": 0.1, "y_m": 0.075,
                 "width_m": 0.03, "height_m": 0.02, "power_w": 0.0}
            ],
            t_air_k=323.15,
            t_inlet_k=313.15,
            a_m=0.2,
            b_m=0.15,
            k_plate=200.0,
            tb_m=0.015,
            n_fourier=15,
        )
        x = np.linspace(0, 0.2, 9)
        y = np.linspace(0, 0.15, 7)
        result = calc_plane_temp(cfg, x, y)
        np.testing.assert_allclose(result.t_grid_k, result.t_base_k, atol=1e-6)

    def test_temperature_increases_with_source_power(self):
        """Peak temperature must scale monotonically with total power."""
        def peak(p: float) -> float:
            cfg = PlaneTempConfig(
                rth_fin=0.05,
                h_eq=80.0,
                sources=[{"name": "Q1", "x_m": 0.1, "y_m": 0.075,
                           "width_m": 0.03, "height_m": 0.02, "power_w": p}],
                t_air_k=318.15,
                t_inlet_k=313.15,
                a_m=0.2,
                b_m=0.15,
                k_plate=200.0,
                tb_m=0.015,
                n_fourier=10,
            )
            x = np.linspace(0, 0.2, 9)
            y = np.linspace(0, 0.15, 7)
            return calc_plane_temp(cfg, x, y).t_max_k

        t50 = peak(50.0)
        t100 = peak(100.0)
        t200 = peak(200.0)
        assert t50 < t100 < t200

    def test_symmetric_source_symmetric_field(self):
        """Source centred on the heatsink produces a symmetric T-field."""
        cfg = PlaneTempConfig(
            rth_fin=0.04,
            h_eq=120.0,
            sources=[{"name": "Q1", "x_m": 0.1, "y_m": 0.075,
                       "width_m": 0.04, "height_m": 0.03, "power_w": 100.0}],
            t_air_k=323.15,
            t_inlet_k=313.15,
            a_m=0.2,
            b_m=0.15,
            k_plate=200.0,
            tb_m=0.015,
            n_fourier=15,
        )
        x = np.linspace(0, 0.2, 11)  # includes 0.1 at index 5
        y = np.linspace(0, 0.15, 11)  # includes 0.075 at index 5
        result = calc_plane_temp(cfg, x, y)
        np.testing.assert_allclose(result.t_grid_k, result.t_grid_k[:, ::-1], atol=1e-3)
        np.testing.assert_allclose(result.t_grid_k, result.t_grid_k[::-1, :], atol=1e-3)
