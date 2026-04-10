"""Unit tests for thermal_cli.formula.convection.

Reference values computed analytically using:
  - Air properties: ideal gas + Sutherland viscosity + linear kf fit, Pr=0.71
  - Forced convection: flat-plate Blasius/mixed correlations (Incropera 7th ed., eq 7.30/7.38)
  - Natural convection: Rayleigh-number correlations (Incropera, Ch. 9)
  - Radiation: linearized Stefan-Boltzmann
"""

from __future__ import annotations

import pytest

from thermal_cli.formula.constants import STEFAN_BOLTZMANN
from thermal_cli.formula.convection import (
    h_forced,
    h_natural,
    h_radiation_linearized,
)


# ============================================================
# h_forced — forced convection on a flat plate
# ============================================================


class TestHForced:
    """h_forced(*, length, velocity, t_ambient, t_surface) -> (h, Re)."""

    def test_laminar_reference(self):
        """L=0.3 m, U=5 m/s, Ta=298.15 K, Ts=348.15 K → Re≈82664 (laminar).

        Film temp Tf=323.15 K:
          rho ≈ 1.0923 kg/m³, mu ≈ 1.982e-5 Pa·s, kf ≈ 0.027720 W/(m·K)
          Re ≈ 82664, h = 0.664*Re^0.5*Pr^(1/3)*kf/L ≈ 15.737 W/(m²·K)
        """
        h, Re = h_forced(length=0.3, velocity=5.0, t_ambient=298.15, t_surface=348.15)
        assert Re == pytest.approx(82663.7, rel=1e-3)
        assert h == pytest.approx(15.737, rel=1e-3)
        assert Re < 5e5  # verify laminar branch was taken

    def test_laminar_returns_positive_h(self):
        h, Re = h_forced(length=0.3, velocity=5.0, t_ambient=298.15, t_surface=348.15)
        assert h > 0

    def test_turbulent_reference(self):
        """L=1.0 m, U=20 m/s, Ta=298.15 K, Ts=348.15 K → Re≈1.10e6 (turbulent).

        h = (0.037*Re^0.8 - 871)*Pr^(1/3)*kf/L ≈ 40.87 W/(m²·K)
        """
        h, Re = h_forced(length=1.0, velocity=20.0, t_ambient=298.15, t_surface=348.15)
        assert Re == pytest.approx(1102182.9, rel=1e-3)
        assert Re > 5e5  # verify turbulent branch was taken
        assert h == pytest.approx(40.866, rel=2e-3)
        assert h > 0

    def test_returns_tuple_of_floats(self):
        result = h_forced(length=0.3, velocity=5.0, t_ambient=298.15, t_surface=348.15)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            h_forced(0.3, 5.0, 298.15, 348.15)  # type: ignore[misc]


# ============================================================
# h_natural — natural convection
# ============================================================


class TestHNatural:
    """h_natural(*, orientation, length, t_ambient, t_surface) -> (h, Nu)."""

    # --- vertical ---

    def test_vertical_laminar(self):
        """Vertical plate: L=0.2 m, Ta=298.15 K, Ts=348.15 K → Ra≈2.62e7 (laminar, Ra<1e9).

        Nu = 0.59*Ra^0.25, h = Nu*kf/L ≈ 5.850 W/(m²·K)
        """
        h, Nu = h_natural(orientation="vertical", length=0.2, t_ambient=298.15, t_surface=348.15)
        assert Nu == pytest.approx(42.205, rel=1e-3)
        assert h == pytest.approx(5.850, rel=1e-3)

    def test_vertical_turbulent(self):
        """Vertical plate: L=2.0 m, Ta=298.15 K, Ts=398.15 K → Ra≈3.74e10 (Ra>1e9).

        Nu = 0.1*Ra^(1/3), h ≈ 4.927 W/(m²·K)
        """
        h, Nu = h_natural(orientation="vertical", length=2.0, t_ambient=298.15, t_surface=398.15)
        assert Nu == pytest.approx(334.34, rel=1e-3)
        assert h == pytest.approx(4.927, rel=1e-3)

    # --- horizontal_top ---

    def test_horizontal_top_laminar(self):
        """Horizontal top: L=0.05 m, Ta=298.15 K, Ts=308.15 K → Ra≈1.09e5 (Ra<1e7).

        Nu = 0.54*Ra^0.25, h ≈ 5.170 W/(m²·K)
        """
        h, Nu = h_natural(
            orientation="horizontal_top", length=0.05, t_ambient=298.15, t_surface=308.15
        )
        assert Nu == pytest.approx(9.822, rel=1e-3)
        assert h == pytest.approx(5.170, rel=1e-3)

    def test_horizontal_top_turbulent(self):
        """Horizontal top: L=1.0 m, Ta=298.15 K, Ts=398.15 K → Ra≈4.67e9 (Ra>1e7).

        Nu = 0.15*Ra^(1/3), h ≈ 7.390 W/(m²·K)
        """
        h, Nu = h_natural(
            orientation="horizontal_top", length=1.0, t_ambient=298.15, t_surface=398.15
        )
        assert Nu == pytest.approx(250.75, rel=1e-3)
        assert h == pytest.approx(7.390, rel=1e-3)

    # --- horizontal_bottom ---

    def test_horizontal_bottom(self):
        """Horizontal bottom: L=0.05 m, Ta=298.15 K, Ts=308.15 K.

        Nu = 0.27*Ra^0.25, h ≈ 2.585 W/(m²·K)
        """
        h, Nu = h_natural(
            orientation="horizontal_bottom", length=0.05, t_ambient=298.15, t_surface=308.15
        )
        assert Nu == pytest.approx(4.911, rel=1e-3)
        assert h == pytest.approx(2.585, rel=1e-3)

    def test_unknown_orientation_raises(self):
        with pytest.raises(ValueError, match="orientation"):
            h_natural(orientation="diagonal", length=0.2, t_ambient=298.15, t_surface=348.15)

    def test_returns_tuple_of_floats(self):
        result = h_natural(orientation="vertical", length=0.2, t_ambient=298.15, t_surface=348.15)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            h_natural("vertical", 0.2, 298.15, 348.15)  # type: ignore[misc]


# ============================================================
# h_radiation_linearized — linearized radiation coefficient
# ============================================================


class TestHRadiationLinearized:
    """h_radiation_linearized(*, emissivity, t_ambient, t_surface) -> float."""

    def test_blackbody_reference(self):
        """Blackbody (eps=1): h = sigma*(Ts^2+Ta^2)*(Ts+Ta).

        Ta=298.15 K, Ts=348.15 K → h ≈ 7.6997 W/(m²·K)
        """
        h = h_radiation_linearized(emissivity=1.0, t_ambient=298.15, t_surface=348.15)
        expected = STEFAN_BOLTZMANN * (348.15**2 + 298.15**2) * (348.15 + 298.15)
        assert h == pytest.approx(expected, rel=1e-12)
        assert h == pytest.approx(7.6997, rel=1e-3)

    def test_gray_surface(self):
        """Gray surface eps=0.85: h = 0.85 * blackbody_h."""
        h = h_radiation_linearized(emissivity=0.85, t_ambient=298.15, t_surface=348.15)
        h_bb = h_radiation_linearized(emissivity=1.0, t_ambient=298.15, t_surface=348.15)
        assert h == pytest.approx(0.85 * h_bb, rel=1e-12)
        assert h == pytest.approx(6.5448, rel=1e-3)

    def test_returns_float(self):
        h = h_radiation_linearized(emissivity=1.0, t_ambient=298.15, t_surface=348.15)
        assert isinstance(h, float)

    def test_proportional_to_emissivity(self):
        h05 = h_radiation_linearized(emissivity=0.5, t_ambient=298.15, t_surface=348.15)
        h10 = h_radiation_linearized(emissivity=1.0, t_ambient=298.15, t_surface=348.15)
        assert h05 == pytest.approx(0.5 * h10, rel=1e-12)

    def test_keyword_only(self):
        with pytest.raises(TypeError):
            h_radiation_linearized(1.0, 298.15, 348.15)  # type: ignore[misc]
