"""Unit tests for thermal_cli.formula.water_cooling.

Physics equations verified by hand:
    q_m3s  = flow_lpm / 1000 / 60
    m_dot  = rho * q_m3s
    dt     = p_loss / (cp * m_dot)
    t_out  = t_inlet + dt
    p_dev  = p_loss / n_devices
    t_junc = t_out + p_dev * (rth_jc + rth_cl)
"""

from __future__ import annotations

import pytest

from thermal_cli.formula.water_cooling import WaterCoolingResult, water_cooling


# ---------------------------------------------------------------------------
# Helper: reference calculation
# ---------------------------------------------------------------------------

def _ref(
    p_loss: float,
    flow_lpm: float,
    t_inlet: float,
    rth_jc: float,
    n_devices: int,
    cp: float = 3483.0,
    rho: float = 1064.0,
    rth_cl: float = 0.0,
) -> dict:
    q_m3s = flow_lpm / 1000 / 60
    m_dot = rho * q_m3s
    dt = p_loss / (cp * m_dot)
    t_outlet = t_inlet + dt
    p_dev = p_loss / n_devices
    t_junc = t_outlet + p_dev * (rth_jc + rth_cl)
    return dict(dt_coolant=dt, t_outlet=t_outlet, t_junction=t_junc, m_dot=m_dot, p_per_device=p_dev)


# ---------------------------------------------------------------------------
# Basic energy balance
# ---------------------------------------------------------------------------

def test_basic_energy_balance():
    """1000 W, 5 l/min, 4 devices, Rjc=0.5 K/W, inlet=423.15 K."""
    res = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=423.15,
        rth_jc=0.5,
        n_devices=4,
    )
    ref = _ref(1000.0, 5.0, 423.15, 0.5, 4)

    assert isinstance(res, WaterCoolingResult)
    assert res.dt_coolant == pytest.approx(ref["dt_coolant"], rel=1e-9)
    assert res.t_outlet == pytest.approx(ref["t_outlet"], rel=1e-9)
    assert res.t_junction == pytest.approx(ref["t_junction"], rel=1e-9)
    assert res.m_dot == pytest.approx(ref["m_dot"], rel=1e-9)
    assert res.p_per_device == pytest.approx(ref["p_per_device"], rel=1e-9)


def test_basic_dt_approx():
    """Spot-check dT ≈ 3.24 K and Tj ≈ 551.39 K for the reference case."""
    res = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=423.15,
        rth_jc=0.5,
        n_devices=4,
    )
    assert res.dt_coolant == pytest.approx(3.238, abs=0.001)
    assert res.t_junction == pytest.approx(551.388, abs=0.001)


# ---------------------------------------------------------------------------
# Single device case
# ---------------------------------------------------------------------------

def test_single_device():
    """Single device: p_per_device == p_loss, Tj = t_out + p_loss * rth_jc."""
    res = water_cooling(
        p_loss=500.0,
        flow_lpm=3.0,
        t_inlet=300.0,
        rth_jc=0.2,
        n_devices=1,
    )
    ref = _ref(500.0, 3.0, 300.0, 0.2, 1)

    assert res.p_per_device == pytest.approx(500.0, rel=1e-9)
    assert res.t_junction == pytest.approx(ref["t_junction"], rel=1e-9)


def test_single_device_p_per_device_equals_total():
    """With n_devices=1, p_per_device must equal p_loss."""
    res = water_cooling(
        p_loss=800.0,
        flow_lpm=4.0,
        t_inlet=310.0,
        rth_jc=0.3,
        n_devices=1,
    )
    assert res.p_per_device == pytest.approx(800.0, rel=1e-9)


# ---------------------------------------------------------------------------
# rth_cl contribution
# ---------------------------------------------------------------------------

def test_rth_cl_increases_junction_temperature():
    """Adding rth_cl must raise t_junction by p_dev * rth_cl."""
    base = water_cooling(
        p_loss=600.0,
        flow_lpm=4.0,
        t_inlet=320.0,
        rth_jc=0.4,
        n_devices=3,
        rth_cl=0.0,
    )
    with_cl = water_cooling(
        p_loss=600.0,
        flow_lpm=4.0,
        t_inlet=320.0,
        rth_jc=0.4,
        n_devices=3,
        rth_cl=0.1,
    )
    p_dev = 600.0 / 3
    assert with_cl.t_junction == pytest.approx(base.t_junction + p_dev * 0.1, rel=1e-9)


# ---------------------------------------------------------------------------
# Custom fluid properties (cp / rho override)
# ---------------------------------------------------------------------------

def test_custom_fluid_properties():
    """Override cp and rho to pure water values and verify m_dot."""
    cp_water = 4182.0
    rho_water = 998.0
    res = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=300.0,
        rth_jc=0.5,
        n_devices=2,
        cp=cp_water,
        rho=rho_water,
    )
    q_m3s = 5.0 / 1000 / 60
    expected_m_dot = rho_water * q_m3s
    assert res.m_dot == pytest.approx(expected_m_dot, rel=1e-9)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_returns_dataclass():
    res = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=300.0,
        rth_jc=0.5,
        n_devices=4,
    )
    assert isinstance(res, WaterCoolingResult)
    # All fields present and are floats
    for field in ("dt_coolant", "t_outlet", "t_junction", "m_dot", "p_per_device"):
        assert isinstance(getattr(res, field), float), f"{field} should be float"


# ---------------------------------------------------------------------------
# Keyword-only enforcement
# ---------------------------------------------------------------------------

def test_keyword_only_raises_on_positional():
    """water_cooling must reject positional arguments."""
    with pytest.raises(TypeError):
        water_cooling(1000.0, 5.0, 300.0, 0.5, 4)  # type: ignore[misc]
