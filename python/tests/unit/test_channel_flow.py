"""Tests for thermal_cli.heatsinks.channel_flow.

Covers:
  - Air property splines at table knot points (exact match)
  - Air property interpolation (range check)
  - hydraulic_operating_point: push and impinge modes
  - fin_thermal_resistance: push and impinge modes, higher flow → lower Rth
"""

from __future__ import annotations

import numpy as np
import pytest

from thermal_cli.heatsinks.channel_flow import (
    HydraulicResult,
    FinRthResult,
    rho_air,
    mu_air,
    kt_air,
    cp_air,
    hydraulic_operating_point,
    fin_thermal_resistance,
)

# ---------------------------------------------------------------------------
# Air property table (raw values before unit conversion)
# ---------------------------------------------------------------------------
# Original table points in °C; stored internally in K.
_T_CELSIUS = [0.0, 38.0, 93.0, 149.0]
_T_K = [t + 273.15 for t in _T_CELSIUS]

# Expected values at table knots
_RHO_EXPECTED = [1.296, 1.136, 0.96, 0.832]          # kg/m³
_MU_EXPECTED = [1.732e-5, 1.910e-5, 2.140e-5, 2.392e-5]  # Pa·s
_KT_EXPECTED = [
    0.0208 * 4.1868e3 / 3600,
    0.0230 * 4.1868e3 / 3600,
    0.0259 * 4.1868e3 / 3600,
    0.0287 * 4.1868e3 / 3600,
]  # W/(m·K)
_CP_EXPECTED = [
    0.24 * 4.1868e3,
    0.240 * 4.1868e3,
    0.241 * 4.1868e3,
    0.243 * 4.1868e3,
]  # J/(kg·K)


# ---------------------------------------------------------------------------
# Air property splines — exact match at table knots
# ---------------------------------------------------------------------------


class TestAirPropertySplines:
    @pytest.mark.parametrize("i", range(4))
    def test_rho_at_knot(self, i):
        assert rho_air(_T_K[i]) == pytest.approx(_RHO_EXPECTED[i], rel=1e-6)

    @pytest.mark.parametrize("i", range(4))
    def test_mu_at_knot(self, i):
        assert mu_air(_T_K[i]) == pytest.approx(_MU_EXPECTED[i], rel=1e-6)

    @pytest.mark.parametrize("i", range(4))
    def test_kt_at_knot(self, i):
        assert kt_air(_T_K[i]) == pytest.approx(_KT_EXPECTED[i], rel=1e-6)

    @pytest.mark.parametrize("i", range(4))
    def test_cp_at_knot(self, i):
        assert cp_air(_T_K[i]) == pytest.approx(_CP_EXPECTED[i], rel=1e-6)


class TestAirPropertyInterpolation:
    """Properties at T between knots should be in physical range."""

    def test_rho_mid_range(self):
        """rho at 60°C (333.15 K) should be between 0.832 and 1.296."""
        t = 60.0 + 273.15
        assert 0.832 < rho_air(t) < 1.296

    def test_mu_mid_range(self):
        """mu at 60°C should be between 1.732e-5 and 2.392e-5."""
        t = 60.0 + 273.15
        assert 1.732e-5 < mu_air(t) < 2.392e-5

    def test_kt_monotone(self):
        """kt should increase with temperature."""
        t1 = 20.0 + 273.15
        t2 = 100.0 + 273.15
        assert kt_air(t1) < kt_air(t2)

    def test_rho_monotone_decreasing(self):
        """density should decrease with temperature."""
        t1 = 20.0 + 273.15
        t2 = 100.0 + 273.15
        assert rho_air(t1) > rho_air(t2)


# ---------------------------------------------------------------------------
# Synthetic heatsink geometry for integration tests (all in meters)
# ---------------------------------------------------------------------------
# Corresponds roughly to a standard extruded heatsink:
#   a=0.14 m, b=0.08 m, Hf=0.04 m, tf=0.002 m, bch=0.004 m, s=0.06 m
#   n_fins = 20, k_fin = 200 W/(m·K) (aluminium)

_HS = dict(
    a=0.14,
    b=0.08,
    s=0.06,
    n_fins=20,
    tf=0.002,
    bch=0.004,
    hf=0.040,
    t_air=300.0,   # K
    k_fin=200.0,
)

# Synthetic fan curve: linear drop from 120 Pa at 0 flow to 0 Pa at 0.05 m³/s
_N_FAN = 11
_FAN_QV = np.linspace(0.0, 0.05, _N_FAN)
_FAN_HV = np.linspace(120.0, 0.0, _N_FAN)


# ---------------------------------------------------------------------------
# hydraulic_operating_point
# ---------------------------------------------------------------------------


class TestHydraulicOperatingPoint:
    def test_push_returns_positive(self):
        result = hydraulic_operating_point(
            b=_HS["b"],
            s=_HS["s"],
            n_fins=_HS["n_fins"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="push",
            fan_qv=_FAN_QV,
            fan_hv=_FAN_HV,
        )
        assert isinstance(result, HydraulicResult)
        assert result.reynolds > 0.0
        assert result.pressure > 0.0
        assert result.flowrate > 0.0

    def test_push_flowrate_in_fan_range(self):
        result = hydraulic_operating_point(
            b=_HS["b"],
            s=_HS["s"],
            n_fins=_HS["n_fins"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="push",
            fan_qv=_FAN_QV,
            fan_hv=_FAN_HV,
        )
        assert _FAN_QV[0] <= result.flowrate <= _FAN_QV[-1]

    def test_impinge_returns_positive(self):
        result = hydraulic_operating_point(
            b=_HS["b"],
            s=_HS["s"],
            n_fins=_HS["n_fins"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="impinge",
            fan_qv=_FAN_QV,
            fan_hv=_FAN_HV,
        )
        assert isinstance(result, HydraulicResult)
        assert result.reynolds > 0.0
        assert result.pressure > 0.0
        assert result.flowrate > 0.0

    def test_impinge_flowrate_in_fan_range(self):
        result = hydraulic_operating_point(
            b=_HS["b"],
            s=_HS["s"],
            n_fins=_HS["n_fins"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="impinge",
            fan_qv=_FAN_QV,
            fan_hv=_FAN_HV,
        )
        assert _FAN_QV[0] <= result.flowrate <= _FAN_QV[-1]

    def test_unknown_vent_type_raises(self):
        with pytest.raises(ValueError, match="vent_type"):
            hydraulic_operating_point(
                b=_HS["b"],
                s=_HS["s"],
                n_fins=_HS["n_fins"],
                tf=_HS["tf"],
                bch=_HS["bch"],
                hf=_HS["hf"],
                t_air=_HS["t_air"],
                vent_type="sideways",
                fan_qv=_FAN_QV,
                fan_hv=_FAN_HV,
            )

    def test_stiffer_fan_gives_higher_pressure(self):
        """Fan with higher pressure head gives higher operating pressure."""
        fan_hv_low = np.linspace(60.0, 0.0, _N_FAN)
        fan_hv_high = np.linspace(200.0, 0.0, _N_FAN)
        r_low = hydraulic_operating_point(
            b=_HS["b"], s=_HS["s"], n_fins=_HS["n_fins"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"], vent_type="push",
            fan_qv=_FAN_QV, fan_hv=fan_hv_low,
        )
        r_high = hydraulic_operating_point(
            b=_HS["b"], s=_HS["s"], n_fins=_HS["n_fins"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"], vent_type="push",
            fan_qv=_FAN_QV, fan_hv=fan_hv_high,
        )
        assert r_high.pressure > r_low.pressure


# ---------------------------------------------------------------------------
# fin_thermal_resistance
# ---------------------------------------------------------------------------


class TestFinThermalResistance:
    def test_push_returns_positive(self):
        # Use known operating point flow
        qv_f = 0.01  # m³/s
        result = fin_thermal_resistance(
            qv_f=qv_f,
            a=_HS["a"],
            b=_HS["b"],
            s=_HS["s"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="push",
            k_fin=_HS["k_fin"],
            n_fins=_HS["n_fins"],
        )
        assert isinstance(result, FinRthResult)
        assert result.rth > 0.0
        assert result.reynolds > 0.0
        assert result.h_eq > 0.0

    def test_push_vch1_is_zero(self):
        """Push mode has no vertical channel flow."""
        result = fin_thermal_resistance(
            qv_f=0.01, a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"], vent_type="push",
            k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
        )
        assert result.v_ch1 == 0.0

    def test_impinge_returns_positive(self):
        qv_f = 0.01  # m³/s
        result = fin_thermal_resistance(
            qv_f=qv_f,
            a=_HS["a"],
            b=_HS["b"],
            s=_HS["s"],
            tf=_HS["tf"],
            bch=_HS["bch"],
            hf=_HS["hf"],
            t_air=_HS["t_air"],
            vent_type="impinge",
            k_fin=_HS["k_fin"],
            n_fins=_HS["n_fins"],
        )
        assert isinstance(result, FinRthResult)
        assert result.rth > 0.0
        assert result.reynolds > 0.0
        assert result.h_eq > 0.0

    def test_impinge_vch1_positive(self):
        """Impinge mode has vertical channel velocity > 0."""
        result = fin_thermal_resistance(
            qv_f=0.01, a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"], vent_type="impinge",
            k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
        )
        assert result.v_ch1 > 0.0

    def test_higher_flow_lower_rth_push(self):
        """Higher volumetric flow → lower thermal resistance (push)."""
        common = dict(
            a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"],
            vent_type="push", k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
        )
        r_low = fin_thermal_resistance(qv_f=0.005, **common)
        r_high = fin_thermal_resistance(qv_f=0.02, **common)
        assert r_high.rth < r_low.rth

    def test_higher_flow_lower_rth_impinge(self):
        """Higher volumetric flow → lower thermal resistance (impinge)."""
        common = dict(
            a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"],
            vent_type="impinge", k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
        )
        r_low = fin_thermal_resistance(qv_f=0.005, **common)
        r_high = fin_thermal_resistance(qv_f=0.02, **common)
        assert r_high.rth < r_low.rth

    def test_unknown_vent_type_raises(self):
        with pytest.raises(ValueError, match="vent_type"):
            fin_thermal_resistance(
                qv_f=0.01, a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
                bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"],
                vent_type="lateral", k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
            )

    def test_rth_h_eq_consistent(self):
        """h_eq and rth should be consistent: h_eq ≈ 1 / (a*b*rth)."""
        result = fin_thermal_resistance(
            qv_f=0.01, a=_HS["a"], b=_HS["b"], s=_HS["s"], tf=_HS["tf"],
            bch=_HS["bch"], hf=_HS["hf"], t_air=_HS["t_air"], vent_type="push",
            k_fin=_HS["k_fin"], n_fins=_HS["n_fins"],
        )
        a = _HS["a"]
        b = _HS["b"]
        expected_h_eq = 1.0 / (a * b * result.rth)
        assert result.h_eq == pytest.approx(expected_h_eq, rel=1e-6)
