"""Convection heat transfer coefficient correlations.

All temperatures in Kelvin. All functions use keyword-only arguments.

Air properties are computed via inline correlations evaluated at the film
temperature Tf = (t_ambient + t_surface) / 2:

  rho  = 101325 / (287.058 * T)                    [ideal gas, 1 atm]
  mu   = 18.27e-6 * (411.15/T+120) * (T/291.15)^1.5  [Sutherland]
  kf   = 7e-5*T + 5.1e-3                           [linear fit]
  Pr   = 0.71                                      [constant]

References
----------
- Incropera, F.P. et al., *Fundamentals of Heat and Mass Transfer*, 7th ed.
  Chapter 7 (forced, flat-plate) and Chapter 9 (natural convection).
"""

from __future__ import annotations

from thermal_cli.formula.constants import STEFAN_BOLTZMANN

#: Constant for Sutherland formula numerator factor (T_ref + S) / T_ref^1.5
_SUTHERLAND_TREF: float = 291.15
_SUTHERLAND_S: float = 120.0
_MU_REF: float = 18.27e-6  # dynamic viscosity at T_ref [Pa·s]

#: Critical Reynolds number for flat-plate transition
_RE_CRIT: float = 5e5

#: Empirical constant for mixed laminar-turbulent flat-plate correlation
#: (Incropera eq. 7.38, A = 0.037 * Re_c^0.8 - 0.664 * Re_c^0.5 ≈ 871)
_MIXED_A: float = 871.0


def _air_properties(T: float) -> tuple[float, float, float, float]:
    """Return (rho, mu, kf, Pr) for dry air at temperature *T* [K]."""
    rho = 101325.0 / (287.058 * T)
    mu = (
        _MU_REF
        * (_SUTHERLAND_TREF + _SUTHERLAND_S)
        / (T + _SUTHERLAND_S)
        * (T / _SUTHERLAND_TREF) ** 1.5
    )
    kf = 7e-5 * T + 5.1e-3
    Pr = 0.71
    return rho, mu, kf, Pr


def h_forced(
    *,
    length: float,
    velocity: float,
    t_ambient: float,
    t_surface: float,
) -> tuple[float, float]:
    """Forced-convection heat transfer coefficient for flow over a flat plate.

    Uses the Blasius (laminar) correlation for Re < 5e5 and the mixed
    laminar-turbulent correlation for Re >= 5e5 (Incropera, eq. 7.30/7.38).

    Properties are evaluated at the film temperature
    Tf = (t_ambient + t_surface) / 2.

    Parameters
    ----------
    length : float
        Plate length in the flow direction [m].
    velocity : float
        Free-stream velocity [m/s].
    t_ambient : float
        Ambient (free-stream) temperature [K].
    t_surface : float
        Surface temperature [K].

    Returns
    -------
    h : float
        Average convective heat transfer coefficient [W/(m²·K)].
    Re : float
        Reynolds number (dimensionless).
    """
    Tf = (t_ambient + t_surface) / 2.0
    rho, mu, kf, Pr = _air_properties(Tf)
    Re = rho * velocity * length / mu

    if Re < _RE_CRIT:
        Nu = 0.664 * Re**0.5 * Pr ** (1.0 / 3.0)
    else:
        Nu = (0.037 * Re**0.8 - _MIXED_A) * Pr ** (1.0 / 3.0)

    h = Nu * kf / length
    return float(h), float(Re)


def h_natural(
    *,
    orientation: str,
    length: float,
    t_ambient: float,
    t_surface: float,
) -> tuple[float, float]:
    """Natural-convection heat transfer coefficient.

    Rayleigh-number correlations (Incropera, Ch. 9) for three surface
    orientations.  Properties are evaluated at the film temperature
    Tf = (t_ambient + t_surface) / 2;  beta = 1 / Tf (ideal gas).

    Parameters
    ----------
    orientation : str
        Surface orientation.  One of:

        ``"vertical"``
            Vertical flat plate or wall.
            Ra < 1e9 → Nu = 0.59*Ra^0.25; Ra >= 1e9 → Nu = 0.1*Ra^(1/3).
        ``"horizontal_top"``
            Horizontal surface, heated side facing up.
            Ra < 1e7 → Nu = 0.54*Ra^0.25; Ra >= 1e7 → Nu = 0.15*Ra^(1/3).
        ``"horizontal_bottom"``
            Horizontal surface, heated side facing down.
            Nu = 0.27*Ra^0.25 (single correlation).

    length : float
        Characteristic length [m] (plate height for vertical, shortest
        side / 0.5*diameter for horizontal).
    t_ambient : float
        Ambient temperature [K].
    t_surface : float
        Surface temperature [K].

    Returns
    -------
    h : float
        Average convective heat transfer coefficient [W/(m²·K)].
    Nu : float
        Nusselt number (dimensionless).

    Raises
    ------
    ValueError
        If *orientation* is not one of the three recognised strings.
    """
    Tf = (t_ambient + t_surface) / 2.0
    rho, mu, kf, Pr = _air_properties(Tf)
    beta = 1.0 / Tf
    Ra = Pr * rho**2 * 9.81 * beta * (t_surface - t_ambient) * length**3 / mu**2

    if orientation == "vertical":
        Nu = 0.59 * Ra**0.25 if Ra < 1e9 else 0.1 * Ra ** (1.0 / 3.0)
    elif orientation == "horizontal_top":
        Nu = 0.54 * Ra**0.25 if Ra < 1e7 else 0.15 * Ra ** (1.0 / 3.0)
    elif orientation == "horizontal_bottom":
        Nu = 0.27 * Ra**0.25
    else:
        raise ValueError(
            f"Unknown orientation {orientation!r}. "
            "Expected 'vertical', 'horizontal_top', or 'horizontal_bottom'."
        )

    h = Nu * kf / length
    return float(h), float(Nu)


def h_radiation_linearized(
    *,
    emissivity: float,
    t_ambient: float,
    t_surface: float,
) -> float:
    """Linearized radiation heat transfer coefficient.

    Derived from the Stefan-Boltzmann law by factoring the (Ts^4 - Ta^4) term:

        Q_rad = eps * sigma * A * (Ts^4 - Ta^4)
              = eps * sigma * A * (Ts^2 + Ta^2)*(Ts + Ta) * (Ts - Ta)
              = h_rad * A * (Ts - Ta)

    so h_rad = eps * sigma * (Ts^2 + Ta^2) * (Ts + Ta).

    Parameters
    ----------
    emissivity : float
        Surface emissivity (dimensionless, in [0, 1]).
    t_ambient : float
        Ambient (surroundings) temperature [K].
    t_surface : float
        Surface temperature [K].

    Returns
    -------
    float
        Linearized radiation heat transfer coefficient [W/(m²·K)].
    """
    return float(
        emissivity
        * STEFAN_BOLTZMANN
        * (t_surface**2 + t_ambient**2)
        * (t_surface + t_ambient)
    )
