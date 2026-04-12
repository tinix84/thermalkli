"""Tests for thermal_cli.sweep.optimize_fin."""

from __future__ import annotations

import numpy as np

from thermal_cli.sweep.optimize_fin import (
    FinGeometrySweepConfig,
    evaluate_extruded_fin_rth,
    optimize_fin_geometry,
)


class TestEvaluateExtrudedFinRth:
    """``evaluate_extruded_fin_rth`` is the scalar adapter used by run_sweep."""

    def test_returns_positive_rth(self):
        rth = evaluate_extruded_fin_rth(
            thick_heatsink=0.010,
            thick_wall=0.0008,
            width_channel=0.00105,
            k_sink=180.0,
            rho_sink=2698.9,
            l_heated=0.137,
            a_hot=16.9e-3 * 13.7e-3,
            flowrate_lpm=1.0,
            fluid_ref="H2OGly50",
            num_channel=18,
        )
        assert rth > 0
        assert np.isfinite(rth)

    def test_thicker_heatsink_lower_rth(self):
        """Deeper channel = more area -> lower Rth (flow dominates)."""
        kw = dict(
            thick_wall=0.0008,
            width_channel=0.00105,
            k_sink=180.0,
            rho_sink=2698.9,
            l_heated=0.137,
            a_hot=16.9e-3 * 13.7e-3,
            flowrate_lpm=1.0,
            fluid_ref="H2OGly50",
            num_channel=18,
        )
        rth_thin = evaluate_extruded_fin_rth(thick_heatsink=0.006, **kw)
        rth_thick = evaluate_extruded_fin_rth(thick_heatsink=0.012, **kw)
        assert rth_thick < rth_thin


class TestOptimizeFinGeometry:
    def test_basic_grid_sweep(self):
        """3x3 grid, returns SweepResult with shape (3, 3)."""
        cfg = FinGeometrySweepConfig(
            axes={
                "thick_heatsink": [0.006, 0.008, 0.010],
                "thick_wall": [0.0006, 0.0008, 0.0010],
            },
            fixed={
                "width_channel": 0.00105,
                "k_sink": 180.0,
                "rho_sink": 2698.9,
                "l_heated": 0.137,
                "a_hot": 16.9e-3 * 13.7e-3,
                "flowrate_lpm": 1.0,
                "fluid_ref": "H2OGly50",
                "num_channel": 18,
            },
        )
        result = optimize_fin_geometry(cfg)
        assert result.values.shape == (3, 3)
        assert (result.values > 0).all()

    def test_returns_argmin_geometry(self):
        cfg = FinGeometrySweepConfig(
            axes={"thick_heatsink": [0.006, 0.008, 0.010]},
            fixed={
                "thick_wall": 0.0008,
                "width_channel": 0.00105,
                "k_sink": 180.0,
                "rho_sink": 2698.9,
                "l_heated": 0.137,
                "a_hot": 16.9e-3 * 13.7e-3,
                "flowrate_lpm": 1.0,
                "fluid_ref": "H2OGly50",
                "num_channel": 18,
            },
        )
        result = optimize_fin_geometry(cfg)
        best = result.argmin()
        assert "thick_heatsink" in best
        assert best["thick_heatsink"] in [0.006, 0.008, 0.010]
