"""Unit tests for thermal_cli.formula.fin."""

import math

import pytest

from thermal_cli.formula.fin import fin_efficiency


def test_known_value_small_mL():
    """For small mL, efficiency approaches 1 (tanh(x)/x → 1 as x → 0)."""
    # L=0.001, very short fin → mL small → eta close to 1
    eta = fin_efficiency(L=0.001, h=10.0, A=1e-5, k=200.0, Ac=1e-6)
    assert 0.99 < eta <= 1.0


def test_known_value_large_mL():
    """For large mL, efficiency approaches 0 (tanh(x)/x → 0 as x → ∞)."""
    # Very long, thin, low-k fin → mL large → eta small
    eta = fin_efficiency(L=1.0, h=1000.0, A=1.0, k=1.0, Ac=1e-6)
    assert 0.0 < eta < 0.1


def test_matches_analytical_formula():
    """Explicit computation: L=0.05, h=30, A=0.01, k=200, Ac=1e-4.
    mL = sqrt(30*0.01 / (200*1e-4*0.05)) * 0.05 = sqrt(30) * 0.05
    """
    L, h, A, k, Ac = 0.05, 30.0, 0.01, 200.0, 1e-4
    mL = math.sqrt(h * A / (k * Ac * L)) * L
    expected = math.tanh(mL) / mL
    eta = fin_efficiency(L=L, h=h, A=A, k=k, Ac=Ac)
    assert eta == pytest.approx(expected, rel=1e-12)


def test_returns_float():
    eta = fin_efficiency(L=0.05, h=30.0, A=0.01, k=200.0, Ac=1e-4)
    assert isinstance(eta, float)
