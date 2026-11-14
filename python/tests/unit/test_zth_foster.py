"""Tests for thermal_cli.transient.zth_foster."""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.transient.zth_foster import zth_foster


class TestZthFoster:
    def test_single_rc_at_t_end(self):
        """Zth(t_end) for single RC == R*(1 - exp(-t_end/tau))."""
        R = np.array([0.5])
        tau = np.array([0.01])
        zth, _t = zth_foster(R, tau, t_end=0.1)
        expected = 0.5 * (1.0 - np.exp(-0.1 / 0.01))
        assert zth[-1] == pytest.approx(expected, rel=1e-6)

    def test_returns_correct_shapes(self):
        R = np.array([0.3, 0.2])
        tau = np.array([0.001, 0.01])
        zth, t = zth_foster(R, tau, t_end=1.0, n_points=50)
        assert zth.shape == (50,)
        assert t.shape == (50,)

    def test_time_axis_log_spaced(self):
        """t should be log-spaced from ~min(tau)/10 to t_end."""
        R = np.array([1.0])
        tau = np.array([0.01])
        _, t = zth_foster(R, tau, t_end=1.0, n_points=100)
        # Check log-spacing: consecutive ratios should be constant
        ratios = t[1:] / t[:-1]
        np.testing.assert_allclose(ratios, ratios[0], rtol=1e-9)

    def test_monotonically_increasing(self):
        """Zth must be monotonically non-decreasing."""
        R = np.array([0.2, 0.3, 0.1])
        tau = np.array([0.001, 0.01, 0.1])
        zth, _ = zth_foster(R, tau, t_end=10.0)
        assert np.all(np.diff(zth) >= 0)

    def test_saturates_at_sum_of_R(self):
        """For t >> max(tau), Zth → sum(R)."""
        R = np.array([0.2, 0.3, 0.1])
        tau = np.array([0.001, 0.002, 0.005])
        rth_total = float(np.sum(R))
        zth, _ = zth_foster(R, tau, t_end=1.0, n_points=200)
        assert zth[-1] == pytest.approx(rth_total, rel=1e-4)

    def test_zero_at_t_zero_approx(self):
        """Zth should be near zero at t << min(tau)."""
        R = np.array([1.0])
        tau = np.array([1.0])
        zth, t = zth_foster(R, tau, t_end=10.0, n_points=200)
        # First point is at min(tau)/10 = 0.1s
        assert zth[0] == pytest.approx(R[0] * (1 - np.exp(-t[0] / tau[0])), rel=1e-6)
