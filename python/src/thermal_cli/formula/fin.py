"""Fin efficiency for constant-cross-section fins.

Ported from ``mfiles/Thermal/Formula/finEfficieny.m``. Note the Octave source
has a typo in the function name (``finEfficieny`` → ``fin_efficiency``).
"""

from __future__ import annotations

import math


def fin_efficiency(*, L: float, h: float, A: float, k: float, Ac: float) -> float:
    """Compute the efficiency of a constant-cross-section fin.

    Uses the classical ``tanh(mL)/mL`` formula where
    ``mL = sqrt(h * A / (k * Ac * L)) * L``.

    Parameters
    ----------
    L : float
        Fin length [m].
    h : float
        Heat transfer coefficient fin surface → fluid [W/(m²·K)].
    A : float
        Fin surface area [m²].
    k : float
        Thermal conductivity of the fin material [W/(m·K)].
    Ac : float
        Fin cross-sectional area [m²].

    Returns
    -------
    float
        Fin efficiency (dimensionless, in (0, 1]).
    """
    mL = math.sqrt(h * A / (k * Ac * L)) * L
    return math.tanh(mL) / mL
