"""Thin wrapper functions for regression fixtures.

The regression harness calls module-level functions, but fluid properties
are methods on class instances. These wrappers bridge the gap.
"""

from __future__ import annotations

from thermal_cli.fluids import fluid_registry

# ---------------------------------------------------------------------------
# M7 convection wrappers
# ---------------------------------------------------------------------------

#: Sutherland constants (must match convection.py)
_SUTHERLAND_TREF: float = 291.15
_SUTHERLAND_S: float = 120.0
_MU_REF: float = 18.27e-6


def _air_mu(T: float) -> float:
    return _MU_REF * (_SUTHERLAND_TREF + _SUTHERLAND_S) / (T + _SUTHERLAND_S) * (T / _SUTHERLAND_TREF) ** 1.5


def _air_rho(T: float) -> float:
    return 101325.0 / (287.058 * T)


def _air_kf(T: float) -> float:
    return 7e-5 * T + 5.1e-3


def run_h_forced_laminar(
    length: float, velocity: float, t_ambient: float, t_surface: float
) -> dict:
    """Return {'h': h, 'Re': Re} for forced convection over flat plate.

    Parameters use K (Python convention), matching h_forced.
    """
    from thermal_cli.formula.convection import h_forced

    h, Re = h_forced(length=length, velocity=velocity, t_ambient=t_ambient, t_surface=t_surface)
    return {"h": h, "Re": Re}


def run_h_natural_vertical(
    length: float, t_ambient: float, t_surface: float
) -> dict:
    """Return {'h': h, 'Ra': Ra} for natural convection, vertical plate.

    Ra is computed from first principles (matching the Octave formula) since
    h_natural() only returns (h, Nu).
    """
    from thermal_cli.formula.convection import h_natural

    h, _Nu = h_natural(orientation="vertical", length=length, t_ambient=t_ambient, t_surface=t_surface)
    Tf = (t_ambient + t_surface) / 2.0
    rho = _air_rho(Tf)
    mu = _air_mu(Tf)
    beta = 1.0 / Tf
    Ra = 0.71 * rho**2 * 9.81 * beta * (t_surface - t_ambient) * length**3 / mu**2
    return {"h": h, "Ra": Ra}


def run_h_radiation(emissivity: float, t_ambient: float, t_surface: float) -> dict:
    """Return {'h': h} for linearized radiation coefficient.

    Parameters use K (Python convention).
    """
    from thermal_cli.formula.convection import h_radiation_linearized

    h = h_radiation_linearized(emissivity=emissivity, t_ambient=t_ambient, t_surface=t_surface)
    return {"h": h}


def run_water_cooling_basic() -> dict:
    """Return {'dT_coolant': ..., 'T_out': ..., 'T_junction': ...} in °C.

    Octave cmd_water_cooling takes °C inputs and outputs °C temperatures.
    Python water_cooling takes K and returns K, so this helper converts back.
    """
    from thermal_cli.formula.water_cooling import water_cooling

    r = water_cooling(
        p_loss=1000.0,
        flow_lpm=5.0,
        t_inlet=298.15,
        rth_jc=0.5,
        n_devices=4,
        cp=3483.0,
        rho=1064.0,
        rth_cl=0.0,
    )
    return {
        "dT_coolant": r.dt_coolant,
        "T_out": r.t_outlet - 273.15,
        "T_junction": r.t_junction - 273.15,
    }


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
