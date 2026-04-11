"""CSPI formulas: FluidProps, air_properties, fan_scaling_fit, channel_rth.

References
----------
Drofenik & Kolar, "Analyzing the Theoretical Limits of Forced Air-Cooling",
CIPS 2006 / PCC 2007.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class FluidProps:
    """Fluid thermal properties at a single reference temperature."""

    density: float  # [kg/m^3]
    kinematic_viscosity: float  # [m^2/s]
    prandtl_number: float  # [-]
    thermal_conductivity: float  # [W/(m K)]
    heat_capacity: float  # [J/(kg K)]


def air_properties(t_ref_c: float = 80.0) -> FluidProps:
    """Return dry-air properties at *t_ref_c* [°C].

    Correlations match ``lib/air_properties.m`` exactly:

    * Density: ideal gas at 101 325 Pa.
    * Dynamic viscosity: Sutherland's law (S = 120 K, T_ref = 291.15 K,
      mu_ref = 18.27e-6 Pa*s).
    * Thermal conductivity: linear fit kf = 7e-5 * T + 5.1e-3 [W/m/K].
    * Prandtl = 0.71, cp = 1010 J/(kg K) (constant).
    """
    T = t_ref_c + 273.15  # [K]
    rho = 101325.0 / 287.058 / T  # ideal gas
    mu = 18.27e-6 * (291.15 + 120) / (T + 120) * (T / 291.15) ** 1.5  # Sutherland
    nu = mu / rho  # kinematic viscosity
    kf = 7e-5 * T + 5.1e-3  # linear fit
    return FluidProps(
        density=rho,
        kinematic_viscosity=nu,
        prandtl_number=0.71,
        thermal_conductivity=kf,
        heat_capacity=1010.0,
    )


def cspi_calc(*, rth: float, vol_cs: float) -> float:
    """Cooling System Performance Index.

    CSPI = 1 / (Rth * V_cs)

    Parameters
    ----------
    rth:    Thermal resistance [K/W]
    vol_cs: Cooling system volume [m^3]
    """
    return 1.0 / (rth * vol_cs)


def fan_scaling_fit(
    *,
    v_max: float,
    dp_max: float,
    p_fan: float,
    d: float,
    n: float,
) -> tuple[float, float, float]:
    """Compute Drofenik fan scaling coefficients (eq. 29-31).

    Parameters
    ----------
    v_max:  Maximum volumetric flow rate [m^3/s]
    dp_max: Maximum static pressure rise  [Pa]
    p_fan:  Fan shaft power               [W]
    d:      Fan diameter                  [m]
    n:      Fan rotational speed          [rpm]

    Returns
    -------
    (k1, k2, k3) dimensionless fan similarity coefficients.
    """
    k1 = float(v_max / (n * d**3))
    k2 = float(dp_max / (n**2 * d**2))
    k3 = float(p_fan / (n**3 * d**5))
    return k1, k2, k3


def channel_rth(
    *,
    width: float | None = None,
    height: float | None = None,
    diameter: float | None = None,
    length: float,
    flow_rate: float,
    fluid: FluidProps,
) -> tuple[float, float, float, float]:
    """Single-channel thermal resistance (matches ``lib/channel_rth.m``).

    Geometry: supply either *diameter* (circular) or *width* + *height*
    (rectangular).

    Parameters
    ----------
    width, height : float, optional
        Rectangular channel cross-section dimensions [m].
    diameter : float, optional
        Circular channel diameter [m].
    length : float
        Channel length [m].
    flow_rate : float
        Volumetric flow rate through the channel [m^3/s].
    fluid : FluidProps
        Fluid properties at the relevant reference temperature.

    Returns
    -------
    (rth, Re, Nu, h)
        rth  — thermal resistance [K/W]
        Re   — Reynolds number [-]
        Nu   — Nusselt number [-]
        h    — convective heat transfer coefficient [W/(m^2 K)]
    """
    if diameter is not None:
        dh = diameter
        Ac = math.pi * (diameter / 2) ** 2
        P = math.pi * diameter
    else:
        if width is None or height is None:
            raise ValueError("Provide either 'diameter' or both 'width' and 'height'.")
        dh = 4.0 * width * height / 2.0 / (height + width)
        Ac = width * height
        P = 2.0 * (width + height)

    v = flow_rate / Ac
    Re = v * dh / fluid.kinematic_viscosity

    Pr = fluid.prandtl_number

    if Re <= 2300:
        # Sieder-Tate / Shah-London laminar developing flow
        x = length / (dh * Re * Pr)
        Nu = (
            3.657 / math.tanh(2.264 * x ** (1.0 / 3.0) + 1.7 * x ** (2.0 / 3.0))
            + 0.0499 * math.tanh(x) / x
        ) / math.tanh(2.432 * Pr ** (1.0 / 6.0) * x ** (1.0 / 6.0))
    else:
        # Gnielinski turbulent
        f = (0.79 * math.log(Re) - 1.64) ** 2
        Nu = (
            (Re - 1000)
            * Pr
            * (1 + (dh / length) ** (2.0 / 3.0))
            / (8.0 * f)
            / (1 + 12.7 * math.sqrt(1.0 / (8.0 * f)) * (Pr ** (2.0 / 3.0) - 1))
        )

    h = Nu * fluid.thermal_conductivity / dh
    rth = 1.0 / (h * length * P) + 0.5 / (fluid.density * fluid.heat_capacity * flow_rate)

    return float(rth), float(Re), float(Nu), float(h)
