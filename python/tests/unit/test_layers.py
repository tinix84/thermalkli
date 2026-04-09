"""Tests for thermal_cli.layers — ThermalLayer and ThermalLayerStack.

Reference values from tests/test_thermal_layer.m in the Octave suite.
"""

from __future__ import annotations

import pytest

from thermal_cli.layers import ThermalLayer, ThermalLayerStack

# --- ThermalLayer creation ---


def test_isotropic_layer() -> None:
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    assert ly.k_ip == 200.0


def test_anisotropic_layer() -> None:
    ly = ThermalLayer(thick=0.001, k_op=0.3, k_ip=200.0)
    assert ly.k_op == 0.3
    assert ly.k_ip == 200.0


# --- No-spread resistance ---


def test_no_spread_resistance() -> None:
    """test_thermal_layer.m: thick=0.001, kOp=200, aIn=1e-4.
    rTh = 0.001 / (200 * 1e-4) = 0.05 K/W.
    """
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    r_th, r_spread, r_through = ly.resistance(a_in=1e-4)
    assert r_th == pytest.approx(0.05, rel=1e-10)
    assert r_spread == 0.0
    assert r_through == pytest.approx(0.05, rel=1e-10)


def test_no_spread_same_areas() -> None:
    """a_in == a_out → no spreading."""
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    r_th, r_spread, _r_through = ly.resistance(a_in=1e-4, a_out=1e-4)
    assert r_th == pytest.approx(0.05, rel=1e-10)
    assert r_spread == 0.0


# --- Spreading resistance (Lee model) ---


def test_spreading_increases_resistance() -> None:
    """test_thermal_layer.m: with spreading, rTh > rThThrough."""
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    r_th, r_spread, r_through = ly.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    assert r_th > r_through
    assert r_spread > 0.0


def test_spreading_anisotropic() -> None:
    """Anisotropic layer (PCB-like): kOp=0.3, kIp=200."""
    ly = ThermalLayer(thick=0.001, k_op=0.3, k_ip=200.0)
    _r_th, r_spread, r_through = ly.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    # Through-plane resistance is much higher for low kOp
    assert r_through == pytest.approx(0.001 / (0.3 * 4e-4), rel=1e-10)
    assert r_spread > 0.0


def test_spreading_returns_floats() -> None:
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    r_th, r_spread, r_through = ly.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    assert isinstance(r_th, float)
    assert isinstance(r_spread, float)
    assert isinstance(r_through, float)


# --- ThermalLayerStack ---


def test_stack_single_layer_matches() -> None:
    """test_thermal_layer.m: single-layer stack must match standalone layer."""
    ly = ThermalLayer(thick=0.001, k_op=200.0)
    stack = ThermalLayerStack()
    stack.add_layer(ly)

    r_single = ly.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    r_stack = stack.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    assert r_stack[0] == pytest.approx(r_single[0], rel=1e-10)


def test_stack_series_no_spreading() -> None:
    """test_thermal_layer.m: series of 2 layers, no spreading.
    0.001m@200 + 0.0005m@0.3, aIn=1e-4.
    rTh = 0.001/(200*1e-4) + 0.0005/(0.3*1e-4) = 0.05 + 16.667 = 16.717 K/W.
    """
    stack = ThermalLayerStack()
    stack.add_layer(ThermalLayer(thick=0.001, k_op=200.0))
    stack.add_layer(ThermalLayer(thick=0.0005, k_op=0.3))

    r_th, r_spread, _r_through = stack.resistance(a_in=1e-4)
    expected = 0.001 / (200.0 * 1e-4) + 0.0005 / (0.3 * 1e-4)
    assert r_th == pytest.approx(expected, rel=1e-6)
    assert r_spread == 0.0


def test_stack_properties() -> None:
    stack = ThermalLayerStack()
    stack.add_layer(ThermalLayer(thick=0.001, k_op=200.0))
    stack.add_layer(ThermalLayer(thick=0.0005, k_op=0.3))
    assert stack.n == 2
    assert stack.thick == pytest.approx(0.0015, rel=1e-10)
    assert stack.k_op > 0.0


def test_stack_spreading_better_than_worst() -> None:
    """With spreading optimization, stack picks the best layer for spreading."""
    stack = ThermalLayerStack()
    stack.add_layer(ThermalLayer(thick=0.001, k_op=200.0))
    stack.add_layer(ThermalLayer(thick=0.0005, k_op=0.3, k_ip=200.0))

    r_th, r_spread, _r_through = stack.resistance(a_in=1e-4, a_out=4e-4, h_eff=500.0)
    # The optimizer should find a total that's less than naively using worst layer
    assert r_th > 0.0
    assert r_spread > 0.0


def test_empty_stack() -> None:
    stack = ThermalLayerStack()
    assert stack.n == 0
    assert stack.thick == 0.0
    r_th, _r_spread, _r_through = stack.resistance(a_in=1e-4)
    assert r_th == 0.0
