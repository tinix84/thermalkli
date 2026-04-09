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


# --- Layer spreading helpers ---


def layer_spreading_isotropic(
    thick: float, k_op: float, a_in: float, a_out: float, h_eff: float
) -> dict[str, float]:
    from thermal_cli.layers import ThermalLayer

    ly = ThermalLayer(thick=thick, k_op=k_op)
    r_th, r_spread, r_through = ly.resistance(a_in=a_in, a_out=a_out, h_eff=h_eff)
    return {"rTh": r_th, "rThSpread": r_spread, "rThThrough": r_through}
