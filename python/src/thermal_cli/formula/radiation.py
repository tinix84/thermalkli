"""Radiation heat transfer formulas.

Ported from ``mfiles/Thermal/Formula/heatTransfer*.m``.
Reference: Incropera, *Fundamentals of Heat and Mass Transfer*, 6th ed.
(ISBN 978-0-471-45728-2), Chapter 13, pp. 832-833.
"""

from __future__ import annotations

import math

from thermal_cli.formula.constants import STEFAN_BOLTZMANN


def parallel_planes(*, T1: float, T2: float, A: float, eps1: float, eps2: float) -> float:
    """Radiation between large parallel planes (eq. 13.24, p. 833).

    Parameters
    ----------
    T1, T2 : float
        Surface temperatures [K].
    A : float
        Surface area (same for both planes) [m^2].
    eps1, eps2 : float
        Emissivities of surfaces 1 and 2 (dimensionless).

    Returns
    -------
    float
        Net heat transfer from surface 1 to 2 [W].
    """
    return A * STEFAN_BOLTZMANN * (T1**4 - T2**4) / (1 / eps1 + 1 / eps2 - 1)


def small_convex(*, T1: float, T2: float, A1: float, eps1: float) -> float:
    """Radiation from a small convex body in a large cavity (A1 << A2), p. 833.

    Parameters
    ----------
    T1, T2 : float
        Surface temperatures [K]. T1 is the small body.
    A1 : float
        Surface area of the small body [m^2].
    eps1 : float
        Emissivity of the small body (dimensionless).

    Returns
    -------
    float
        Net heat transfer from surface 1 to 2 [W].
    """
    return STEFAN_BOLTZMANN * A1 * eps1 * (T1**4 - T2**4)


def concentric_cylinders(
    *, T1: float, T2: float, r1: float, r2: float, L: float, eps1: float, eps2: float
) -> float:
    """Radiation between long concentric cylinders, p. 833.

    Parameters
    ----------
    T1, T2 : float
        Surface temperatures [K].
    r1, r2 : float
        Radii of inner and outer cylinders [m].
    L : float
        Length of cylinders [m].
    eps1, eps2 : float
        Emissivities of inner and outer surfaces (dimensionless).

    Returns
    -------
    float
        Net heat transfer from surface 1 to 2 [W].
    """
    A1 = 2 * math.pi * r1 * L
    return STEFAN_BOLTZMANN * A1 * (T1**4 - T2**4) / (1 / eps1 + (1 - eps2) / eps2 * (r1 / r2))


def concentric_spheres(
    *, T1: float, T2: float, r1: float, r2: float, eps1: float, eps2: float
) -> float:
    """Radiation between concentric spheres, p. 833.

    Parameters
    ----------
    T1, T2 : float
        Surface temperatures [K].
    r1, r2 : float
        Radii of inner and outer spheres [m].
    eps1, eps2 : float
        Emissivities of inner and outer surfaces (dimensionless).

    Returns
    -------
    float
        Net heat transfer from surface 1 to 2 [W].
    """
    A1 = 4 * math.pi * r1**2
    return STEFAN_BOLTZMANN * A1 * (T1**4 - T2**4) / (1 / eps1 + (1 - eps2) / eps2 * (r1 / r2) ** 2)


def enclosure(
    *,
    T1: float,
    T2: float,
    eps1: float,
    eps2: float,
    A1: float,
    A2: float,
    F12: float,
) -> float:
    """Two-surface enclosure radiation (eq. 13.23, p. 832).

    Parameters
    ----------
    T1, T2 : float
        Surface temperatures [K].
    eps1, eps2 : float
        Emissivities of surfaces 1 and 2 (dimensionless).
    A1, A2 : float
        Areas of surfaces 1 and 2 [m^2].
    F12 : float
        View factor from surface 1 to 2 (dimensionless).

    Returns
    -------
    float
        Net heat transfer from surface 1 to 2 [W].
    """
    return (
        STEFAN_BOLTZMANN
        * (T1**4 - T2**4)
        / ((1 - eps1) / (eps1 * A1) + 1 / (A1 * F12) + (1 - eps2) / (eps2 * A2))
    )
