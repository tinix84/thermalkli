"""Tests for thermal_cli.heatsinks — ExtrudedFin and factory.

Reference values from test_channel_model.m and test_literature.m.
"""

from __future__ import annotations

import pytest

from thermal_cli.fluids import fluid_registry
from thermal_cli.heatsinks import ExtrudedFin, heatsink_factory


@pytest.fixture()
def hs_ex_001() -> ExtrudedFin:
    """HS_EX_001 from database: 10-channel extruded aluminum."""
    return heatsink_factory("HS_EX_001")


@pytest.fixture()
def air_fluid():
    return fluid_registry("airDry")


# --- Geometry ---


def test_factory_loads_hs_ex_001(hs_ex_001: ExtrudedFin) -> None:
    assert hs_ex_001.num_channel == 10
    assert hs_ex_001.k_sink == 180.0
    assert hs_ex_001.thick_wall == 0.001


def test_factory_unknown() -> None:
    with pytest.raises(ValueError, match="not found"):
        heatsink_factory("NONEXISTENT")


def test_geometry_height(hs_ex_001: ExtrudedFin) -> None:
    """height = numChannel*(thickWall + widthChannel) + thickWall."""
    expected = 10 * (0.001 + 0.00105) + 0.001
    assert hs_ex_001.height == pytest.approx(expected, rel=1e-10)


def test_geometry_depth_channel(hs_ex_001: ExtrudedFin) -> None:
    """depthChannel = thickHeatsink - 2*thickWall."""
    expected = 0.01 - 2 * 0.001
    assert hs_ex_001.depth_channel == pytest.approx(expected, rel=1e-10)


def test_geometry_hydraulic_diameter(hs_ex_001: ExtrudedFin) -> None:
    """dHydro = 2*w*h / (w+h) for rectangular channel."""
    w = 0.00105
    h = 0.01 - 2 * 0.001  # 0.008
    expected = 2 * w * h / (w + h)
    assert hs_ex_001.d_hydro == pytest.approx(expected, rel=1e-10)


# --- Nusselt correlations ---


def test_nusselt_laminar_fully_developed() -> None:
    """For a square channel (aspect=1), Nu_fd ≈ 3.61."""
    hs = ExtrudedFin(
        num_channel=1,
        thick_heatsink=0.012,
        thick_wall=0.001,
        width_channel=0.01,
        k_sink=200.0,
    )
    # Very long heated length → fully developed
    nu = hs.nusselt(re=500.0, pr=0.71, l_heated=10.0)
    assert nu == pytest.approx(3.61, abs=0.5)


def test_nusselt_gnielinski_re10000() -> None:
    """test_literature.m: Gnielinski at Re=10000, Pr=0.71 → Nu ≈ 30."""
    hs = ExtrudedFin(
        num_channel=1,
        thick_heatsink=0.012,
        thick_wall=0.001,
        width_channel=0.01,
        k_sink=200.0,
    )
    nu = hs.nusselt(re=10000.0, pr=0.71, l_heated=1.0)
    assert 20.0 < nu < 45.0  # ±50% tolerance for correlation comparison


def test_nusselt_turbulent_greater_than_laminar() -> None:
    """At transition, turbulent Nu should be > laminar Nu."""
    hs = ExtrudedFin(
        num_channel=1,
        thick_heatsink=0.012,
        thick_wall=0.001,
        width_channel=0.01,
        k_sink=200.0,
    )
    nu_lam = hs.nusselt(re=2300.0, pr=0.71, l_heated=0.1)
    nu_turb = hs.nusselt(re=5000.0, pr=0.71, l_heated=0.1)
    assert nu_turb > nu_lam


# --- Reynolds ---


def test_reynolds_positive(hs_ex_001: ExtrudedFin, air_fluid) -> None:
    re = hs_ex_001.reynolds(air_fluid, flowrate=0.001)
    assert re > 0.0
    assert isinstance(re, float)


# --- Thermal resistance ---


def test_thermal_resistance_basic(hs_ex_001: ExtrudedFin, air_fluid) -> None:
    """Basic smoke test: thermal resistance is positive and decomposition sums."""
    result = hs_ex_001.thermal_resistance(
        fluid=air_fluid,
        flowrate=0.001,
        l_heated=0.02,
        a_hot=1e-4,
        pr=0.71,
    )
    assert result["r_th_total"] > 0.0
    assert result["r_th_conv"] > 0.0
    assert result["r_th_fluid"] > 0.0
    assert result["r_th_total"] == pytest.approx(
        result["r_th_conv"] + result["r_th_fluid"], rel=1e-10
    )


def test_higher_flow_lower_rth(hs_ex_001: ExtrudedFin, air_fluid) -> None:
    """test_channel_model.m: higher flow → lower thermal resistance."""
    r1 = hs_ex_001.thermal_resistance(
        fluid=air_fluid,
        flowrate=0.001,
        l_heated=0.02,
        a_hot=1e-4,
        pr=0.71,
    )
    r2 = hs_ex_001.thermal_resistance(
        fluid=air_fluid,
        flowrate=0.005,
        l_heated=0.02,
        a_hot=1e-4,
        pr=0.71,
    )
    assert r2["r_th_total"] < r1["r_th_total"]


def test_heat_transfer_coefficient_positive(hs_ex_001: ExtrudedFin, air_fluid) -> None:
    h = hs_ex_001.heat_transfer_coefficient(
        fluid=air_fluid,
        flowrate=0.001,
        l_heated=0.02,
        pr=0.71,
    )
    assert h > 0.0
    assert isinstance(h, float)


# --- Direct construction ---


def test_manual_construction() -> None:
    """Build ExtrudedFin without factory."""
    hs = ExtrudedFin(
        num_channel=5,
        thick_heatsink=0.008,
        thick_wall=0.0008,
        width_channel=0.001,
        k_sink=200.0,
    )
    assert hs.num_channel == 5
    assert hs.cross_area_fluid > 0.0
