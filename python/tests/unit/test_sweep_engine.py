"""Tests for thermal_cli.sweep.engine."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.engine import SweepResult, run_sweep


class TestRunSweep:
    def test_single_axis_scalar_output(self):
        """y = 2*x over x in [1, 2, 3]."""
        res = run_sweep(
            func=lambda x: 2 * x,
            axes={"x": [1.0, 2.0, 3.0]},
        )
        assert isinstance(res, SweepResult)
        assert res.axis_names == ("x",)
        assert res.values.shape == (3,)
        np.testing.assert_array_equal(res.values, [2.0, 4.0, 6.0])

    def test_two_axes_cartesian_product(self):
        """z = x + y over 2 x 3 grid."""
        res = run_sweep(
            func=lambda x, y: x + y,
            axes={"x": [1.0, 2.0], "y": [10.0, 20.0, 30.0]},
        )
        assert res.axis_names == ("x", "y")
        assert res.values.shape == (2, 3)
        np.testing.assert_array_equal(
            res.values,
            [[11.0, 21.0, 31.0], [12.0, 22.0, 32.0]],
        )

    def test_fixed_kwargs_forwarded(self):
        """func(x=..., k=5) — k is fixed, not swept."""
        res = run_sweep(
            func=lambda x, k: x * k,
            axes={"x": [1.0, 2.0]},
            fixed={"k": 5.0},
        )
        np.testing.assert_array_equal(res.values, [5.0, 10.0])

    def test_axis_values_stored(self):
        res = run_sweep(
            func=lambda x: x,
            axes={"x": [1.0, 2.0, 3.0]},
        )
        np.testing.assert_array_equal(res.axis_values[0], [1.0, 2.0, 3.0])

    def test_argmin_returns_dict_of_axis_values(self):
        """argmin() gives the axis values at the minimum output."""
        res = run_sweep(
            func=lambda x, y: (x - 2) ** 2 + (y - 5) ** 2,
            axes={"x": [0.0, 1.0, 2.0, 3.0], "y": [3.0, 4.0, 5.0, 6.0]},
        )
        assert res.argmin() == {"x": 2.0, "y": 5.0}

    def test_argmax_returns_dict_of_axis_values(self):
        res = run_sweep(
            func=lambda x: -((x - 3) ** 2),
            axes={"x": [0.0, 1.0, 2.0, 3.0, 4.0]},
        )
        assert res.argmax() == {"x": 3.0}

    def test_empty_axes_raises(self):
        with pytest.raises(ValueError, match="at least one axis"):
            run_sweep(func=lambda: 0.0, axes={})

    def test_empty_axis_values_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            run_sweep(func=lambda x: x, axes={"x": []})

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            run_sweep(lambda x: x, {"x": [1]})  # type: ignore[misc]
