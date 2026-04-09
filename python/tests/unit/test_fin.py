"""Unit tests for thermal_cli.formula.fin."""

import math

import pytest

from thermal_cli.formula.fin import fin_efficiency


def test_known_value_small_mL():
    """For small mL, efficiency approaches 1 (tanh(x)/x → 1 as x → 0)."""
    # L=0.001, very short fin → mL small → eta close to 1
    eta = fin_efficiency(L=0.001, h=10.0, A=1e-5, k=200.0, Ac=1e-6)
    # tanh(x)/x < 1 for x > 0; the bound is strict
    assert eta < 1.0
    assert math.isclose(eta, 1.0, rel_tol=2e-3)


def test_known_value_large_mL():
    """For large mL, efficiency approaches 0 (tanh(x)/x → 0 as x → ∞)."""
    # Very long, thin, low-k fin → mL large → eta small
    eta = fin_efficiency(L=1.0, h=1000.0, A=1.0, k=1.0, Ac=1e-6)
    assert 0.0 < eta < 0.1


def test_matches_reference_value():
    """Hard-coded independent reference.

    For L=0.05, h=30, A=0.01, k=200, Ac=1e-4 the analytical result is
    0.8075387894207215 (verified against Octave finEfficieny.m). This is the
    same input set used by the Task 6 regression fixture, so drift between
    Octave and Python is caught here first.
    """
    eta = fin_efficiency(L=0.05, h=30.0, A=0.01, k=200.0, Ac=1e-4)
    assert eta == pytest.approx(0.8075387894207215, rel=1e-12)


def test_returns_float():
    eta = fin_efficiency(L=0.05, h=30.0, A=0.01, k=200.0, Ac=1e-4)
    assert isinstance(eta, float)
