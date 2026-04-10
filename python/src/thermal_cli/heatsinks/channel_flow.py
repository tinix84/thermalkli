"""Channel-flow hydraulic operating point and fin thermal resistance.

Ported from ``mfiles/SoftwareTermico/Therm_hydr/idraulico.m`` and
``mfiles/SoftwareTermico/Therm_hydr/Rth_fin.m``.

All geometry arguments are in **SI units** (meters).  The legacy Octave
source used millimetres internally; all mm→m conversion factors have been
removed in this port.

Air properties are spline-interpolated from the legacy ``Coeff_Aria/``
tables (original data in °C, stored here against T in K).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.interpolate import CubicSpline

# ---------------------------------------------------------------------------
# Air property splines
# ---------------------------------------------------------------------------
# Source: mfiles/SoftwareTermico/Coeff_Aria/
# Original table in °C; knot temperatures converted to K here.

_T_KNOTS_K = np.array([273.15, 311.15, 366.15, 422.15])  # 0, 38, 93, 149 °C

_RHO_DATA = np.array([1.296, 1.136, 0.96, 0.832])        # kg/m³
_MU_DATA = np.array([1.732, 1.910, 2.140, 2.392]) * 1e-5  # Pa·s
# kcal/(h·m·°C) → W/(m·K): multiply by 4.1868e3/3600
_KT_DATA = np.array([0.0208, 0.0230, 0.0259, 0.0287]) * 4.1868e3 / 3600.0
# kcal/(kg·°C) → J/(kg·K): multiply by 4.1868e3
_CP_DATA = np.array([0.24, 0.240, 0.241, 0.243]) * 4.1868e3

# CubicSpline default BC ('not-a-knot') matches Octave spline() behaviour.
_cs_rho = CubicSpline(_T_KNOTS_K, _RHO_DATA)
_cs_mu = CubicSpline(_T_KNOTS_K, _MU_DATA)
_cs_kt = CubicSpline(_T_KNOTS_K, _KT_DATA)
_cs_cp = CubicSpline(_T_KNOTS_K, _CP_DATA)


def rho_air(t: float) -> float:
    """Air density [kg/m³] at temperature *t* [K]."""
    return float(_cs_rho(t))


def mu_air(t: float) -> float:
    """Air dynamic viscosity [Pa·s] at temperature *t* [K]."""
    return float(_cs_mu(t))


def kt_air(t: float) -> float:
    """Air thermal conductivity [W/(m·K)] at temperature *t* [K]."""
    return float(_cs_kt(t))


def cp_air(t: float) -> float:
    """Air specific heat [J/(kg·K)] at temperature *t* [K]."""
    return float(_cs_cp(t))


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class HydraulicResult:
    """Result of a hydraulic operating-point calculation.

    Attributes
    ----------
    reynolds : float
        Average Reynolds number (dimensionless).
    pressure : float
        Operating pressure drop / fan head [Pa].
    flowrate : float
        Volumetric flow rate at operating point [m³/s].
    """

    reynolds: float
    pressure: float  # [Pa]
    flowrate: float  # [m³/s]


@dataclass
class FinRthResult:
    """Result of a fin thermal-resistance calculation.

    Attributes
    ----------
    reynolds : float
        Average Reynolds number (dimensionless).
    v_ch1 : float
        Velocity in vertical channel (impinge only) [m/s]; 0 for push.
    v_ch2 : float
        Velocity in horizontal channel [m/s].
    rth : float
        Fin thermal resistance [K/W].
    h_eq : float
        Equivalent heat-transfer coefficient over footprint [W/(m²·K)].
    """

    reynolds: float
    v_ch1: float   # [m/s]
    v_ch2: float   # [m/s]
    rth: float     # [K/W]
    h_eq: float    # [W/(m²·K)]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fapp_rect(ld: float, fred: float, redh: float) -> float:
    """Apparent friction factor for rectangular channel.

    Combines developing-flow (3.44/√L+) and fully-developed (fReDh) terms.
    """
    return math.sqrt((3.44 / math.sqrt(ld)) ** 2 + fred**2) / redh


def _fred_rect(bch: float, h: float) -> float:
    """Fully-developed friction factor x Re for rectangular channel.

    Parameters
    ----------
    bch : float
        Channel width [m].
    h : float
        Channel height [m].
    """
    ratio = bch / h
    tanh_term = math.tanh(math.pi * h / (2.0 * bch))
    return 24.0 / (
        (1.0 + ratio**2) * (1.0 - (192.0 / math.pi**5) * ratio * tanh_term)
    )


def _nu_channel(reb: float, pr: float) -> float:
    """Muzychka-Yovanovich composite Nusselt correlation.

    Parameters
    ----------
    reb : float
        Modified Reynolds number (Re·b/L).
    pr : float
        Prandtl number.
    """
    term_fd = reb * pr / 2.0
    term_dev = 0.664 * math.sqrt(reb) * pr ** (1.0 / 3.0) * math.sqrt(1.0 + 3.65 / math.sqrt(reb))
    return (term_fd**(-3) + term_dev**(-3)) ** (-1.0 / 3.0)


# ---------------------------------------------------------------------------
# Function 1: hydraulic_operating_point
# ---------------------------------------------------------------------------


def hydraulic_operating_point(
    *,
    b: float,
    s: float,
    n_fins: int,
    tf: float,
    bch: float,
    hf: float,
    t_air: float,
    vent_type: str,
    fan_qv: np.ndarray,
    fan_hv: np.ndarray,
) -> HydraulicResult:
    """Find the hydraulic operating point of a heatsink-fan system.

    Uses bisection to find the flow rate where the fan pressure head equals
    the heatsink pressure drop.

    Parameters
    ----------
    b : float
        Heatsink dimension parallel to fins [m].
    s : float
        Air inlet aperture (impinge mode) [m].
    n_fins : int
        Number of fins.
    tf : float
        Fin thickness [m].
    bch : float
        Channel width [m].
    hf : float
        Fin height [m].
    t_air : float
        Mean air temperature [K].
    vent_type : str
        ``'push'`` or ``'impinge'``.
    fan_qv : np.ndarray
        Fan volumetric flow-rate curve [m³/s].
    fan_hv : np.ndarray
        Fan pressure-head curve [Pa].

    Returns
    -------
    HydraulicResult
        Operating point (Reynolds, pressure, flow rate).
    """
    if vent_type not in ("push", "impinge"):
        raise ValueError(f"Unknown vent_type '{vent_type}': must be 'push' or 'impinge'.")

    rho = rho_air(t_air)
    mu = mu_air(t_air)
    nu = mu / rho  # kinematic viscosity [m²/s]

    n_ch = n_fins - 1

    q1 = float(fan_qv[0])
    q2 = float(fan_qv[-1])

    error = 1.0
    qv_f = q1
    hv_hs = 0.0
    reynolds_avg = 0.0

    while abs(error) > 0.01:
        qv_f = q1 + 0.5 * (q2 - q1)
        hv_fan = float(np.interp(qv_f, fan_qv, fan_hv))

        if vent_type == "impinge":
            leff1 = hf / 2.0
            leff2 = b / 2.0 - s / 4.0

            vch1 = qv_f / (n_ch * s * bch)
            vch2 = qv_f / (2.0 * n_ch * bch * hf)

            dh1 = 4.0 * bch * s / (2.0 * s + 2.0 * bch)
            dh2 = 4.0 * bch * hf / (2.0 * bch + 2.0 * hf)

            redh1 = dh1 * vch1 / nu
            redh2 = dh2 * vch2 / nu
            reynolds_avg = (redh1 + redh2) / 2.0

            ld1 = hf / (dh1 * redh1)
            ld2 = b / (dh2 * redh2)

            fred1 = _fred_rect(bch, s)
            fred2 = _fred_rect(bch, hf)

            fapp1 = _fapp_rect(ld1, fred1, redh1)
            fapp2 = _fapp_rect(ld2, fred2, redh2)

            ratio_hs = hf / s
            if ratio_hs <= 1.0:
                k90 = (
                    3.64 - 9.15 * ratio_hs + 10.87 * ratio_hs**2 - 4.93 * ratio_hs**3
                )
            else:
                k90 = 0.5 * ((1.0 + vch2 / vch1) / 2.0)

            sigma = bch / (bch + tf)
            kc = 0.4 * (1.0 - sigma**2) + 0.4
            ke = 1.0 - sigma**2 - 0.4 * sigma

            hv_hs = (
                (kc + k90 + 4.0 * fapp1 * leff1 / dh1) * (4.0 * hf**2 / s**2)
                + 4.0 * fapp2 * leff2 / dh2
                + ke
            ) * 0.5 * rho * vch2**2

        else:  # push
            leff2 = b

            vch2 = qv_f / (n_ch * bch * hf)
            dh2 = 4.0 * bch * hf / (2.0 * bch + 2.0 * hf)
            redh2 = dh2 * vch2 / nu
            reynolds_avg = redh2

            ld2 = b / (dh2 * redh2)
            fred2 = _fred_rect(bch, hf)
            fapp2 = _fapp_rect(ld2, fred2, redh2)

            sigma = bch / (bch + tf)
            kc = 0.4 * (1.0 - sigma**2) + 0.4
            ke = (1.0 - sigma) ** 2 - 0.4 * sigma

            hv_hs = 1.2 * (kc + 4.0 * fapp2 * leff2 / dh2 + ke) * 0.5 * rho * vch2**2

        error = (hv_fan - hv_hs) / hv_fan
        if error > 0:
            q1 = qv_f
        else:
            q2 = qv_f

    return HydraulicResult(
        reynolds=reynolds_avg,
        pressure=hv_hs,
        flowrate=qv_f,
    )


# ---------------------------------------------------------------------------
# Function 2: fin_thermal_resistance
# ---------------------------------------------------------------------------


def fin_thermal_resistance(
    *,
    qv_f: float,
    a: float,
    b: float,
    s: float,
    tf: float,
    bch: float,
    hf: float,
    t_air: float,
    vent_type: str,
    k_fin: float,
    n_fins: int,
) -> FinRthResult:
    """Compute fin thermal resistance for a given volumetric flow rate.

    Parameters
    ----------
    qv_f : float
        Volumetric flow rate [m³/s].
    a : float
        Heatsink dimension perpendicular to fins [m].
    b : float
        Heatsink dimension parallel to fins [m].
    s : float
        Air inlet aperture (impinge mode) [m].
    tf : float
        Fin thickness [m].
    bch : float
        Channel width [m].
    hf : float
        Fin height [m].
    t_air : float
        Mean air temperature [K].
    vent_type : str
        ``'push'`` or ``'impinge'``.
    k_fin : float
        Fin material thermal conductivity [W/(m·K)].
    n_fins : int
        Number of fins.

    Returns
    -------
    FinRthResult
        Thermal resistance and associated parameters.
    """
    if vent_type not in ("push", "impinge"):
        raise ValueError(f"Unknown vent_type '{vent_type}': must be 'push' or 'impinge'.")

    rho = rho_air(t_air)
    mu = mu_air(t_air)
    kt = kt_air(t_air)
    cp = cp_air(t_air)
    nu = mu / rho
    pr = mu * cp / kt

    n_ch = n_fins - 1

    if vent_type == "impinge":
        leff1 = hf / 2.0
        leff2 = b / 2.0 - s / 4.0

        vch1 = qv_f / (n_ch * s * bch)
        vch2 = qv_f / (2.0 * n_ch * bch * hf)

        # Modified Reynolds numbers (Muzychka-Yovanovich)
        reb1 = bch * vch1 / nu * (bch / leff1)
        reb2 = bch * vch2 / nu * (bch / leff2)
        reb_avg = (reb1 + reb2) / 2.0

        nu1 = _nu_channel(reb1, pr)
        nu2 = _nu_channel(reb2, pr)

        h1 = nu1 * kt / bch
        h2 = nu2 * kt / bch

        # Weighted average bare heat-transfer coefficient
        hbare = h1 * s / b + h2 * (b - s) / b
        nu_avg = nu1 * s / b + nu2 * (b - s) / b

        # Fin efficiency using average Nu
        arg = 2.0 * nu_avg * (kt / k_fin) * (hf / bch) * (hf / tf) * (tf / b + 1.0)
        eta_fin = math.tanh(math.sqrt(arg)) / math.sqrt(arg)

        nu_fin = nu_avg * eta_fin
        hfin = nu_fin * kt / bch

    else:  # push
        leff2 = b
        vch1 = 0.0
        vch2 = qv_f / (n_ch * bch * hf)

        reb2 = bch * vch2 / nu * (bch / leff2)
        reb_avg = reb2

        nu2 = _nu_channel(reb2, pr)
        h2 = nu2 * kt / bch
        hbare = h2

        # Fin efficiency
        arg = 2.0 * nu2 * (kt / k_fin) * (hf / bch) * (hf / tf) * (tf / b + 1.0)
        eta_fin = math.tanh(math.sqrt(arg)) / math.sqrt(arg)

        nu_fin = nu2 * eta_fin
        hfin = nu_fin * kt / bch

    # Areas (all in m²)
    a_bare = a * b - n_fins * b * tf      # base plate between fins
    a_fin = n_ch * b * hf * 2.0           # both faces of all fins

    rth = 1.0 / (a_bare * hbare + a_fin * hfin)
    h_eq = 1.0 / (a * b * rth)

    return FinRthResult(
        reynolds=reb_avg,
        v_ch1=vch1,
        v_ch2=vch2,
        rth=rth,
        h_eq=h_eq,
    )
