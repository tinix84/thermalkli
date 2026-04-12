"""Tests for thermal_cli.sweep.dsl."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.sweep.dsl import parse_axis_spec, parse_sweep_config


class TestParseAxisSpec:
    def test_explicit_values(self):
        vals = parse_axis_spec({"values": [1.0, 2.0, 3.0]})
        np.testing.assert_array_equal(vals, [1.0, 2.0, 3.0])

    def test_linspace(self):
        vals = parse_axis_spec({"linspace": {"start": 0.0, "stop": 1.0, "steps": 5}})
        np.testing.assert_allclose(vals, [0.0, 0.25, 0.5, 0.75, 1.0])

    def test_range_inclusive_of_stop(self):
        """``range`` includes stop and does not overshoot it."""
        vals = parse_axis_spec({"range": {"start": 0.0, "stop": 1.0, "step": 0.25}})
        np.testing.assert_allclose(vals, [0.0, 0.25, 0.5, 0.75, 1.0])
        assert float(vals[-1]) <= 1.0 + 1e-10

    def test_scalar_becomes_single_value(self):
        vals = parse_axis_spec(2.5)
        np.testing.assert_array_equal(vals, [2.5])

    def test_list_becomes_values(self):
        vals = parse_axis_spec([1, 2, 3])
        np.testing.assert_array_equal(vals, [1.0, 2.0, 3.0])

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match="unknown"):
            parse_axis_spec({"banana": [1, 2]})

    def test_linspace_missing_key_raises(self):
        with pytest.raises(ValueError, match="start"):
            parse_axis_spec({"linspace": {"stop": 1.0, "steps": 5}})

    def test_range_missing_key_raises(self):
        with pytest.raises(ValueError, match="start"):
            parse_axis_spec({"range": {"stop": 1.0, "step": 0.25}})


class TestParseSweepConfig:
    def test_basic(self):
        cfg = {
            "axes": {
                "x": [1.0, 2.0],
                "y": {"linspace": {"start": 0.0, "stop": 10.0, "steps": 3}},
            },
            "fixed": {"k": 5.0},
        }
        axes, fixed = parse_sweep_config(cfg)
        assert list(axes.keys()) == ["x", "y"]
        np.testing.assert_array_equal(axes["x"], [1.0, 2.0])
        np.testing.assert_allclose(axes["y"], [0.0, 5.0, 10.0])
        assert fixed == {"k": 5.0}

    def test_missing_axes_raises(self):
        with pytest.raises(ValueError, match="axes"):
            parse_sweep_config({"fixed": {}})

    def test_missing_fixed_is_empty_dict(self):
        _axes, fixed = parse_sweep_config({"axes": {"x": [1, 2]}})
        assert fixed == {}
