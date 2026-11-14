"""Tests for thermal_cli.transient.zth_pulsed."""

from __future__ import annotations

import numpy as np

from thermal_cli.transient.zth_foster import zth_foster
from thermal_cli.transient.zth_pulsed import zth_pulsed


class TestZthPulsed:
    def test_duty_1_equals_continuous(self):
        """Duty=1 (continuous) must equal the standard Foster Zth."""
        R = np.array([0.5])
        tau = np.array([0.01])
        zth_cont, t = zth_foster(R, tau, t_end=0.1, n_points=20)
        zth_p = zth_pulsed(R, tau, t, duty=1.0, period=1.0)
        np.testing.assert_allclose(zth_p, zth_cont, rtol=1e-4)

    def test_duty_less_than_1_lower_than_continuous(self):
        """Pulsed Zth (D<1) must be <= continuous Zth at all time points."""
        R = np.array([0.3, 0.2])
        tau = np.array([0.001, 0.01])
        _, t = zth_foster(R, tau, t_end=0.1, n_points=30)
        zth_cont, _ = zth_foster(R, tau, t_end=0.1, n_points=30)
        zth_p = zth_pulsed(R, tau, t, duty=0.5, period=0.02)
        assert np.all(zth_p <= zth_cont + 1e-10)

    def test_returns_correct_shape(self):
        R = np.array([0.5])
        tau = np.array([0.01])
        t = np.logspace(-4, -1, 15)
        zth_p = zth_pulsed(R, tau, t, duty=0.3, period=0.01)
        assert zth_p.shape == (15,)

    def test_nonnegative(self):
        R = np.array([0.2, 0.3])
        tau = np.array([0.001, 0.01])
        t = np.logspace(-4, 0, 40)
        zth_p = zth_pulsed(R, tau, t, duty=0.5, period=0.05)
        assert np.all(zth_p >= -1e-10)
