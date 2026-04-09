"""Thin wrapper functions for regression fixtures.

The regression harness calls module-level functions, but fluid properties
are methods on class instances. These wrappers bridge the gap.
"""

from __future__ import annotations

from thermal_cli.fluids import fluid_registry


def air_density(temperature: float, pressure: float = 101325.0) -> float:
    air = fluid_registry("airDry")
    return air.density(temperature, pressure)


def air_dynamic_viscosity(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.dynamic_viscosity(temperature)


def air_thermal_conductivity(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.thermal_conductivity(temperature)


def air_specific_heat_cp(temperature: float) -> float:
    air = fluid_registry("airDry")
    return air.specific_heat_cp(temperature)


def glycol_density(temperature: float) -> float:
    g = fluid_registry("H2OGly50")
    return g.density(temperature)


def glycol_dynamic_viscosity(temperature: float) -> float:
    g = fluid_registry("H2OGly50")
    return g.dynamic_viscosity(temperature)


def sae30_density(temperature: float) -> float:
    oil = fluid_registry("SAE30")
    return oil.density(temperature)
