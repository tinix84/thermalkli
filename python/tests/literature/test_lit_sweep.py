"""Sanity tests for the sweep engine using an analytic minimum."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.engine import run_sweep


class TestSweepOnQuadratic:
    def test_finds_minimum_of_parabola(self):
        """f(x) = (x - 2.5)^2 — argmin over a dense grid should be near 2.5."""
        result = run_sweep(
            func=lambda x: (x - 2.5) ** 2,
            axes={"x": np.linspace(0.0, 5.0, 101)},
        )
        assert result.argmin()["x"] == pytest.approx(2.5, abs=0.05)
        assert result.min() == pytest.approx(0.0, abs=1e-3)

    def test_finds_2d_minimum(self):
        """f(x, y) = (x - 1)^2 + (y - 3)^2 over a dense grid."""
        result = run_sweep(
            func=lambda x, y: (x - 1.0) ** 2 + (y - 3.0) ** 2,
            axes={
                "x": np.linspace(-1.0, 3.0, 41),
                "y": np.linspace(1.0, 5.0, 41),
            },
        )
        best = result.argmin()
        assert best["x"] == pytest.approx(1.0, abs=0.05)
        assert best["y"] == pytest.approx(3.0, abs=0.05)
