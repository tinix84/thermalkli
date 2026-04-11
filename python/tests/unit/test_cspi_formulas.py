"""Tests for cspi/formulas.py — CSPI formulas, fan scaling, channel Rth."""

import math

import pytest

from thermal_cli.cspi.formulas import (
    FluidProps,
    air_properties,
    channel_rth,
    cspi_calc,
    fan_scaling_fit,
)

# ---------------------------------------------------------------------------
# cspi_calc
# ---------------------------------------------------------------------------


class TestCspiCalc:
    def test_basic(self):
        """1/(0.5 * 2.0) == 1.0"""
        assert cspi_calc(rth=0.5, vol_cs=2.0) == pytest.approx(1.0)

    def test_low_rth_high_cspi(self):
        """Lower rth yields higher CSPI."""
        cspi_low_rth = cspi_calc(rth=0.1, vol_cs=1.0)
        cspi_high_rth = cspi_calc(rth=1.0, vol_cs=1.0)
        assert cspi_low_rth > cspi_high_rth

    def test_keyword_only(self):
        """cspi_calc must be keyword-only."""
        with pytest.raises(TypeError):
            cspi_calc(0.5, 2.0)  # type: ignore[call-arg]

    def test_known_value(self):
        """1/(0.2 * 0.5) == 10.0"""
        assert cspi_calc(rth=0.2, vol_cs=0.5) == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# fan_scaling_fit
# ---------------------------------------------------------------------------


class TestFanScalingFit:
    def test_returns_three_floats(self):
        k1, k2, k3 = fan_scaling_fit(v_max=0.05, dp_max=100.0, p_fan=2.0, d=0.08, n=2000.0)
        assert isinstance(k1, float)
        assert isinstance(k2, float)
        assert isinstance(k3, float)

    def test_k1_formula(self):
        """k1 = v_max / (n * d^3)"""
        v_max, n, d = 0.05, 2000.0, 0.08
        expected_k1 = v_max / (n * d**3)
        k1, _, _ = fan_scaling_fit(v_max=v_max, dp_max=100.0, p_fan=2.0, d=d, n=n)
        assert k1 == pytest.approx(expected_k1)

    def test_k2_formula(self):
        """k2 = dp_max / (n^2 * d^2)"""
        dp_max, n, d = 100.0, 2000.0, 0.08
        expected_k2 = dp_max / (n**2 * d**2)
        _, k2, _ = fan_scaling_fit(v_max=0.05, dp_max=dp_max, p_fan=2.0, d=d, n=n)
        assert k2 == pytest.approx(expected_k2)

    def test_k3_formula(self):
        """k3 = p_fan / (n^3 * d^5)"""
        p_fan, n, d = 2.0, 2000.0, 0.08
        expected_k3 = p_fan / (n**3 * d**5)
        _, _, k3 = fan_scaling_fit(v_max=0.05, dp_max=100.0, p_fan=p_fan, d=d, n=n)
        assert k3 == pytest.approx(expected_k3)

    def test_keyword_only(self):
        """fan_scaling_fit must be keyword-only."""
        with pytest.raises(TypeError):
            fan_scaling_fit(0.05, 100.0, 2.0, 0.08, 2000.0)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# air_properties
# ---------------------------------------------------------------------------


class TestAirProperties:
    def test_returns_fluid_props(self):
        fp = air_properties(80.0)
        assert isinstance(fp, FluidProps)

    def test_density_at_80c(self):
        """rho = 101325 / 287.058 / (80 + 273.15)"""
        fp = air_properties(80.0)
        expected_rho = 101325 / 287.058 / (80.0 + 273.15)
        assert fp.density == pytest.approx(expected_rho, rel=1e-6)

    def test_prandtl_at_80c(self):
        fp = air_properties(80.0)
        assert fp.prandtl_number == pytest.approx(0.71)

    def test_heat_capacity_at_80c(self):
        fp = air_properties(80.0)
        assert fp.heat_capacity == pytest.approx(1010.0)

    def test_default_temperature(self):
        """Default is 80 C."""
        fp_default = air_properties()
        fp_explicit = air_properties(80.0)
        assert fp_default.density == pytest.approx(fp_explicit.density)

    def test_kinematic_viscosity_positive(self):
        fp = air_properties(80.0)
        assert fp.kinematic_viscosity > 0

    def test_thermal_conductivity_formula(self):
        """kf = 7e-5 * T + 5.1e-3 at T = 353.15 K"""
        T = 80.0 + 273.15
        expected_kf = 7e-5 * T + 5.1e-3
        fp = air_properties(80.0)
        assert fp.thermal_conductivity == pytest.approx(expected_kf, rel=1e-6)

    def test_different_temperatures(self):
        """Higher temperature => lower density."""
        fp_cold = air_properties(20.0)
        fp_hot = air_properties(100.0)
        assert fp_cold.density > fp_hot.density


# ---------------------------------------------------------------------------
# channel_rth
# ---------------------------------------------------------------------------


class TestChannelRth:
    @pytest.fixture
    def air_80(self):
        return air_properties(80.0)

    # -- rectangular laminar --------------------------------------------------

    def test_rectangular_laminar_returns_four_values(self, air_80):
        rth, Re, Nu, h = channel_rth(
            width=0.003,
            height=0.010,
            length=0.05,
            flow_rate=1e-5,
            fluid=air_80,
        )
        assert rth > 0
        assert Re > 0
        assert Nu > 0
        assert h > 0

    def test_rectangular_laminar_re_below_2300(self, air_80):
        _, Re, _, _ = channel_rth(
            width=0.003,
            height=0.010,
            length=0.05,
            flow_rate=1e-5,
            fluid=air_80,
        )
        assert Re <= 2300

    def test_rectangular_laminar_rth_positive(self, air_80):
        rth, _, _, _ = channel_rth(
            width=0.003,
            height=0.010,
            length=0.05,
            flow_rate=1e-5,
            fluid=air_80,
        )
        assert rth > 0

    # -- turbulent ------------------------------------------------------------

    def test_turbulent_re_above_2300(self, air_80):
        _, Re, _, _ = channel_rth(
            width=0.005,
            height=0.005,
            length=0.20,
            flow_rate=5e-4,
            fluid=air_80,
        )
        assert Re > 2300

    def test_turbulent_rth_positive(self, air_80):
        rth, _, _, _ = channel_rth(
            width=0.005,
            height=0.005,
            length=0.20,
            flow_rate=5e-4,
            fluid=air_80,
        )
        assert rth > 0

    # -- higher flow rate => lower rth ----------------------------------------

    def test_higher_flow_lower_rth(self, air_80):
        rth_low, *_ = channel_rth(
            width=0.005,
            height=0.010,
            length=0.10,
            flow_rate=1e-5,
            fluid=air_80,
        )
        rth_high, *_ = channel_rth(
            width=0.005,
            height=0.010,
            length=0.10,
            flow_rate=5e-4,
            fluid=air_80,
        )
        assert rth_high < rth_low

    # -- circular channel -----------------------------------------------------

    def test_circular_channel(self, air_80):
        rth, Re, Nu, h = channel_rth(
            diameter=0.004,
            length=0.10,
            flow_rate=1e-4,
            fluid=air_80,
        )
        assert rth > 0
        assert Re > 0
        assert Nu > 0
        assert h > 0

    def test_circular_hydraulic_diameter(self, air_80):
        """For circular channel dh == diameter; verify Re is consistent."""
        d = 0.004
        Ac = math.pi * (d / 2) ** 2
        v = 1e-4 / Ac
        expected_Re = v * d / air_80.kinematic_viscosity
        _, Re, _, _ = channel_rth(
            diameter=d,
            length=0.10,
            flow_rate=1e-4,
            fluid=air_80,
        )
        assert Re == pytest.approx(expected_Re, rel=1e-6)

    # -- keyword-only ---------------------------------------------------------

    def test_keyword_only(self, air_80):
        """channel_rth must be keyword-only (no positional args)."""
        with pytest.raises(TypeError):
            channel_rth(0.003, 0.010, None, 0.05, 1e-5, air_80)  # type: ignore[call-arg]

    # -- rectangular vs circular consistency ----------------------------------

    def test_rectangular_and_circular_give_different_rth(self, air_80):
        """Rectangular and circular channels have different geometries -> different rth."""
        rth_rect, *_ = channel_rth(
            width=0.004,
            height=0.004,
            length=0.10,
            flow_rate=1e-4,
            fluid=air_80,
        )
        rth_circ, *_ = channel_rth(
            diameter=0.004,
            length=0.10,
            flow_rate=1e-4,
            fluid=air_80,
        )
        # They differ because Ac and P differ for same characteristic size
        assert rth_rect != pytest.approx(rth_circ)


class TestChannelRthValidation:
    """Input validation for non-physical arguments."""

    def _fluid(self) -> FluidProps:
        return air_properties(80.0)

    def test_non_positive_length_raises(self):
        with pytest.raises(ValueError, match="length"):
            channel_rth(
                width=0.002,
                height=0.020,
                length=0.0,
                flow_rate=1e-4,
                fluid=self._fluid(),
            )

    def test_non_positive_flow_rate_raises(self):
        with pytest.raises(ValueError, match="flow_rate"):
            channel_rth(
                width=0.002,
                height=0.020,
                length=0.1,
                flow_rate=0.0,
                fluid=self._fluid(),
            )

    def test_negative_diameter_raises(self):
        with pytest.raises(ValueError, match="diameter"):
            channel_rth(
                diameter=-1e-3,
                length=0.1,
                flow_rate=1e-4,
                fluid=self._fluid(),
            )

    def test_zero_width_raises(self):
        with pytest.raises(ValueError, match="width"):
            channel_rth(
                width=0.0,
                height=0.020,
                length=0.1,
                flow_rate=1e-4,
                fluid=self._fluid(),
            )
