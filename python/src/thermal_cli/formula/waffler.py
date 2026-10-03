"""Literal printed Waffler 2013 liquid-channel correlations (eqs. 4.146–4.150).

Inputs are dimensionless Reynolds/Prandtl numbers and SI lengths. This module
keeps Waffler's stated transition interpolation distinct from the legacy
TO-247/Gnielinski adaptation in py2femm.
"""

from __future__ import annotations

import math
from numbers import Real


def _positive_finite(name: str, value: Real) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite positive number")
    result = float(value)
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return result


def waffler_friction_factor(reynolds_number: float) -> float:
    """Return Waffler's Darcy friction factor ``zeta`` from eq. 4.150."""
    re = _positive_finite("reynolds_number", reynolds_number)
    denominator = 0.78 * math.log(re) - 1.5
    if denominator == 0.0:
        raise ValueError("reynolds_number makes the printed friction-factor denominator zero")
    return 1.0 / denominator**2


def waffler_laminar_nusselt(
    reynolds_number: float,
    prandtl_number: float,
    hydraulic_diameter_m: float,
    channel_length_m: float,
) -> float:
    """Return the Waffler laminar Nusselt correlation, eq. 4.146."""
    re = _positive_finite("reynolds_number", reynolds_number)
    pr = _positive_finite("prandtl_number", prandtl_number)
    diameter = _positive_finite("hydraulic_diameter_m", hydraulic_diameter_m)
    length = _positive_finite("channel_length_m", channel_length_m)
    entry_term = (re * diameter / length) ** 1.5
    return (3.657**3 + 0.644**3 * pr * entry_term) ** (1.0 / 3.0)


def waffler_turbulent_nusselt(
    reynolds_number: float,
    prandtl_number: float,
    hydraulic_diameter_m: float,
    channel_length_m: float,
) -> float:
    """Return the Waffler turbulent Nusselt correlation, eq. 4.147."""
    re = _positive_finite("reynolds_number", reynolds_number)
    pr = _positive_finite("prandtl_number", prandtl_number)
    diameter = _positive_finite("hydraulic_diameter_m", hydraulic_diameter_m)
    length = _positive_finite("channel_length_m", channel_length_m)
    zeta = waffler_friction_factor(re)
    zeta_eighth = zeta / 8.0
    denominator = 1.0 + 12.7 * math.sqrt(zeta_eighth) * (pr ** (2.0 / 3.0) - 1.0)
    if denominator == 0.0:
        raise ValueError("inputs make the printed turbulent-correlation denominator zero")
    length_correction = 1.0 + (diameter / length) ** (2.0 / 3.0)
    return (zeta_eighth * re * pr / denominator) * length_correction


def waffler_nusselt(
    reynolds_number: float,
    prandtl_number: float,
    hydraulic_diameter_m: float,
    channel_length_m: float,
) -> float:
    """Return Waffler's piecewise/linearly interpolated Nusselt number, eq. 4.148."""
    re = _positive_finite("reynolds_number", reynolds_number)
    pr = _positive_finite("prandtl_number", prandtl_number)
    diameter = _positive_finite("hydraulic_diameter_m", hydraulic_diameter_m)
    length = _positive_finite("channel_length_m", channel_length_m)
    if re <= 2300.0:
        return waffler_laminar_nusselt(re, pr, diameter, length)
    if re >= 10000.0:
        return waffler_turbulent_nusselt(re, pr, diameter, length)

    gamma = (re - 2300.0) / 7700.0
    nu_laminar_at_transition = waffler_laminar_nusselt(2300.0, pr, diameter, length)
    nu_turbulent_at_transition = waffler_turbulent_nusselt(10000.0, pr, diameter, length)
    return (1.0 - gamma) * nu_laminar_at_transition + gamma * nu_turbulent_at_transition


def waffler_heat_transfer_coefficient(
    reynolds_number: float,
    prandtl_number: float,
    hydraulic_diameter_m: float,
    channel_length_m: float,
    fluid_conductivity_W_m_K: float,
) -> float:
    """Convert the printed Nusselt correlation to ``h`` in W/(m² K)."""
    conductivity = _positive_finite("fluid_conductivity_W_m_K", fluid_conductivity_W_m_K)
    diameter = _positive_finite("hydraulic_diameter_m", hydraulic_diameter_m)
    return (
        waffler_nusselt(reynolds_number, prandtl_number, diameter, channel_length_m)
        * conductivity
        / diameter
    )


__all__ = [
    "waffler_friction_factor",
    "waffler_heat_transfer_coefficient",
    "waffler_laminar_nusselt",
    "waffler_nusselt",
    "waffler_turbulent_nusselt",
]