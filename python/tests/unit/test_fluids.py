"""Tests for thermal_cli.fluids — gas and liquid property models.

Reference values from test_air_properties.m and test_fluid_properties.m.
"""

from __future__ import annotations

import pytest

from thermal_cli.fluids import GasProperty, LiquidProperty, fluid_registry

# --- GasProperty (airDry) ---


class TestGasPropertyAirDry:
    @pytest.fixture()
    def air(self) -> GasProperty:
        return GasProperty(fluid_ref="airDry")

    def test_density_at_300K(self, air: GasProperty) -> None:
        """test_fluid_properties.m: airDry @ 300K, 101325Pa → ~1.177 kg/m³."""
        rho = air.density(300.0, 101325.0)
        assert rho == pytest.approx(1.177, abs=0.05)

    def test_density_at_293K(self, air: GasProperty) -> None:
        """Octave GasProperty: airDry @ 293K → ~1.22 kg/m³ (interp + ideal gas)."""
        rho = air.density(293.15, 101325.0)
        assert rho == pytest.approx(1.22, abs=0.05)

    def test_density_at_373K(self, air: GasProperty) -> None:
        """test_air_properties.m: rho_air @ 100°C → 0.946 kg/m³."""
        rho = air.density(373.15, 101325.0)
        assert rho == pytest.approx(0.946, abs=0.03)

    def test_cp_at_293K(self, air: GasProperty) -> None:
        """FluidData.xlsx: airDry cp=1400 J/(kg·K) across full range.

        NOTE: the database value (1400) differs from the standard
        literature value for dry air (~1005). This is a known data
        quality issue in the original spreadsheet; the Python port
        faithfully reproduces the Octave behavior.
        """
        cp = air.specific_heat_cp(293.15)
        assert cp == pytest.approx(1400.0, abs=10)

    def test_dyn_visc_at_293K(self, air: GasProperty) -> None:
        """test_air_properties.m: mu_air @ 20°C → 1.825e-5 Pa·s."""
        mu = air.dynamic_viscosity(293.15)
        assert mu == pytest.approx(1.825e-5, abs=2e-7)

    def test_therm_cond_at_293K(self, air: GasProperty) -> None:
        """test_air_properties.m: Kt_air @ 20°C → 0.0257 W/(m·K)."""
        k = air.thermal_conductivity(293.15)
        assert k == pytest.approx(0.0257, abs=0.002)

    def test_therm_cond_at_373K(self, air: GasProperty) -> None:
        """test_air_properties.m: Kt_air @ 100°C → 0.0308 W/(m·K)."""
        k = air.thermal_conductivity(373.15)
        assert k == pytest.approx(0.0308, abs=0.002)

    def test_kin_visc_returns_float(self, air: GasProperty) -> None:
        nu = air.kinematic_viscosity(300.0)
        assert isinstance(nu, float)
        assert nu > 0


# --- LiquidProperty (H2OGly50) ---


class TestLiquidPropertyH2OGly50:
    @pytest.fixture()
    def glycol(self) -> LiquidProperty:
        return LiquidProperty(fluid_ref="H2OGly50")

    def test_density_at_300K(self, glycol: LiquidProperty) -> None:
        """test_fluid_properties.m: H2OGly50 @ ~300K → 1073 kg/m³."""
        rho = glycol.density(299.85)
        assert rho == pytest.approx(1073.8, abs=5)

    def test_dyn_visc_at_300K(self, glycol: LiquidProperty) -> None:
        rho = glycol.dynamic_viscosity(299.85)
        assert rho == pytest.approx(0.0028, abs=0.001)

    def test_freezing_pt(self, glycol: LiquidProperty) -> None:
        assert glycol.freezing_pt == pytest.approx(236.35, abs=1)

    def test_boiling_pt(self, glycol: LiquidProperty) -> None:
        assert glycol.boiling_pt == pytest.approx(380.35, abs=1)


# --- LiquidProperty (SAE30) ---


class TestLiquidPropertySAE30:
    @pytest.fixture()
    def oil(self) -> LiquidProperty:
        return LiquidProperty(fluid_ref="SAE30")

    def test_density_at_293K(self, oil: LiquidProperty) -> None:
        rho = oil.density(293.15)
        assert rho == pytest.approx(881.5, abs=5)

    def test_dyn_visc_at_293K(self, oil: LiquidProperty) -> None:
        mu = oil.dynamic_viscosity(293.15)
        assert mu == pytest.approx(0.2394, abs=0.01)


# --- fluid_registry ---


def test_registry_air() -> None:
    f = fluid_registry("airDry")
    assert isinstance(f, GasProperty)


def test_registry_glycol() -> None:
    f = fluid_registry("H2OGly50")
    assert isinstance(f, LiquidProperty)


def test_registry_sae30() -> None:
    f = fluid_registry("SAE30")
    assert isinstance(f, LiquidProperty)


def test_registry_unknown() -> None:
    with pytest.raises(ValueError, match="Unknown fluid"):
        fluid_registry("liquidNitrogen")
