"""Unit tests for thermal_cli.formula.radiation.

Reference values computed from Incropera, Fundamentals of Heat and Mass Transfer,
6th ed., Ch. 13, using sigma = 5.670367e-8 W/(m^2 K^4).

Octave test_formula.m provides the independent reference for each case.
"""

from __future__ import annotations

import math

import pytest

from thermal_cli.formula.constants import STEFAN_BOLTZMANN
from thermal_cli.formula.radiation import (
    concentric_cylinders,
    concentric_spheres,
    enclosure,
    parallel_planes,
    small_convex,
)

SIGMA = STEFAN_BOLTZMANN


# --- parallel_planes ---


def test_parallel_planes_blackbody():
    """Two blackbodies at 500 K and 300 K, A=1 m^2."""
    q = parallel_planes(T1=500.0, T2=300.0, A=1.0, eps1=1.0, eps2=1.0)
    expected = SIGMA * 1.0 * (500.0**4 - 300.0**4)
    assert q == pytest.approx(expected, rel=1e-12)


def test_parallel_planes_gray():
    """Gray surfaces eps=0.5, T1=500 K, T2=300 K."""
    q = parallel_planes(T1=500.0, T2=300.0, A=1.0, eps1=0.5, eps2=0.5)
    expected = SIGMA * 1.0 * (500.0**4 - 300.0**4) / (1 / 0.5 + 1 / 0.5 - 1)
    assert q == pytest.approx(expected, rel=1e-12)


def test_parallel_planes_returns_float():
    q = parallel_planes(T1=500.0, T2=300.0, A=1.0, eps1=0.8, eps2=0.8)
    assert isinstance(q, float)


# --- small_convex ---


def test_small_convex_reference():
    """Small body eps=0.9, A1=0.01, T1=500 K, T2=300 K."""
    q = small_convex(T1=500.0, T2=300.0, A1=0.01, eps1=0.9)
    expected = SIGMA * 0.01 * 0.9 * (500.0**4 - 300.0**4)
    assert q == pytest.approx(expected, rel=1e-12)


# --- concentric_cylinders ---


def test_concentric_cylinders_blackbody():
    """Blackbody concentric cylinders r1=0.05, r2=0.10, L=1.0."""
    q = concentric_cylinders(T1=500.0, T2=300.0, r1=0.05, r2=0.10, L=1.0, eps1=1.0, eps2=1.0)
    A1 = 2 * math.pi * 0.05 * 1.0
    expected = SIGMA * A1 * (500.0**4 - 300.0**4) / (1 / 1.0 + (1 - 1.0) / 1.0 * (0.05 / 0.10))
    assert q == pytest.approx(expected, rel=1e-12)


# --- concentric_spheres ---


def test_concentric_spheres_blackbody():
    """Blackbody concentric spheres r1=0.05, r2=0.10."""
    q = concentric_spheres(T1=500.0, T2=300.0, r1=0.05, r2=0.10, eps1=1.0, eps2=1.0)
    A1 = 4 * math.pi * 0.05**2
    expected = SIGMA * A1 * (500.0**4 - 300.0**4) / (1 / 1.0 + (1 - 1.0) / 1.0 * (0.05 / 0.10) ** 2)
    assert q == pytest.approx(expected, rel=1e-12)


# --- enclosure ---


def test_enclosure_f12_equals_1():
    """Two-surface enclosure, F12=1, A1=A2=1, eps=0.8."""
    q = enclosure(T1=500.0, T2=300.0, eps1=0.8, eps2=0.8, A1=1.0, A2=1.0, F12=1.0)
    expected = (
        SIGMA
        * (500.0**4 - 300.0**4)
        / ((1 - 0.8) / (0.8 * 1.0) + 1 / (1.0 * 1.0) + (1 - 0.8) / (0.8 * 1.0))
    )
    assert q == pytest.approx(expected, rel=1e-12)


# --- keyword-only enforcement ---


def test_parallel_planes_keyword_only():
    with pytest.raises(TypeError):
        parallel_planes(500.0, 300.0, 1.0, 0.5, 0.5)  # type: ignore[misc]


def test_enclosure_keyword_only():
    with pytest.raises(TypeError):
        enclosure(500.0, 300.0, 0.8, 0.8, 1.0, 1.0, 1.0)  # type: ignore[misc]
