"""CSPI geometry optimizer and sweep.

Ports ``lib/cspi_optimize.m`` to Python.

References
----------
Drofenik & Kolar, "Analyzing the Theoretical Limits of Forced Air-Cooling",
CIPS 2006 / PCC 2007.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from thermal_cli.cspi.formulas import air_properties, channel_rth, cspi_calc


@dataclass
class CspiOptResult:
    """Result of a single CSPI optimisation run."""

    cspi: float  # [W/(K liter)]
    rth: float  # [K/W]
    vol: float  # [liters]
    n: int  # number of channels/fins
    s: float  # optimal channel width [m]
    t: float  # fin thickness [m]
    re: float  # Reynolds number
    n_fan: float  # fan speed [rev/s]
    length: float  # heatsink length [m]
    v_max: float  # max fan flow [m^3/s]
    dp_max: float  # max fan pressure [Pa]
    feasible: bool  # Re<2300 and valid geometry


@dataclass
class CspiSweepResult:
    """Result of a 2-D CSPI parameter sweep."""

    cs: list[float]
    lambdas: list[float]
    cspi: np.ndarray  # shape (len(cs), len(lambdas))
    rth: np.ndarray  # shape (len(cs), len(lambdas))


def cspi_optimize(
    *,
    lambda_hs: float,
    a_chip: float,
    c: float,
    p_fan_max: float,
    t_min: float = 0.0,
    k1: float = 6e-3,
    k2: float = 5e-4,
    k3: float = 30e-6,
    t_air: float = 80.0,
    n_pts: int = 80,
) -> CspiOptResult:
    """Find optimal heatsink channel width that maximises CSPI.

    Parameters
    ----------
    lambda_hs:  Heatsink thermal conductivity [W/(m K)]
    a_chip:     Total chip footprint area [m^2]
    c:          Heatsink height (= fan diameter) [m]
    p_fan_max:  Maximum fan shaft power [W]
    t_min:      Minimum fin thickness [m] (0 = unconstrained)
    k1:         Fan scaling: V_MAX = k1 * N * D^3
    k2:         Fan scaling: dp_MAX = k2 * N^2 * D^2
    k3:         Fan scaling: P_FAN = k3 * N^3 * D^5
    t_air:      Reference air temperature [°C]
    n_pts:      Number of sweep points
    """
    # Heatsink is square cross-section b=c, length L along flow
    L = a_chip / c

    # Fan operating point at max power: P = k3 * N^3 * D^5  =>  N [rev/s]
    N = (p_fan_max / (k3 * c**5)) ** (1.0 / 3.0)
    v_max = k1 * N * c**3  # max volumetric flow at zero pressure [m^3/s]
    dp_max = k2 * N**2 * c**2  # max static pressure at zero flow [Pa]

    # Air fluid properties at reference temperature
    fluid = air_properties(t_air)

    # Sweep channel width s
    s_min = max(t_min * 0.5, 0.2e-3)  # at least 0.2 mm channel
    s_max = c * 0.5  # at most half the height

    s_arr = np.linspace(s_min, s_max, n_pts)
    cspi_arr = np.zeros(n_pts)

    for idx, s_try in enumerate(s_arr):
        # Number of channels that fit in cross-section c.
        # Without a min-thickness constraint, assume thin fins: t ~ s (aspect guess).
        n_try = math.floor(c / (s_try + t_min)) if t_min > 0 else math.floor(c / (2.0 * s_try))

        if n_try < 2:
            continue  # cspi_arr[idx] stays 0

        # Fin thickness from pitch
        t_try = c / n_try - s_try
        if t_try < t_min or t_try <= 0:
            continue

        # Flow per channel (fan operates at mid-point of fan curve)
        v_total = v_max * 0.5
        v_ch = v_total / n_try

        if v_ch <= 0:
            continue

        # Channel thermal resistance (rectangular: width=s, height=c)
        try:
            rth_ch, _re, _nu, _h = channel_rth(
                width=s_try,
                height=c,
                length=L,
                flow_rate=v_ch,
                fluid=fluid,
            )
        except Exception:
            continue

        if rth_ch <= 0 or not math.isfinite(rth_ch):
            continue

        # Conductive resistance through half-fin to base
        rth_fin = (t_try / 2.0) / (lambda_hs * c * L)

        # Total heatsink Rth: n channels in parallel with fin conduction in series
        rth_total = (rth_fin + rth_ch) / n_try

        if rth_total <= 0 or not math.isfinite(rth_total):
            continue

        vol_cs = L * c * c * 1000.0  # [liters]
        cspi_arr[idx] = cspi_calc(rth=rth_total, vol_cs=vol_cs)

    # Find optimal channel width
    best_idx = int(np.argmax(cspi_arr))
    s_opt = float(s_arr[best_idx])

    # --- Recompute final geometry at optimum ---
    n_fin = math.floor(c / (s_opt + t_min)) if t_min > 0 else math.floor(c / (2.0 * s_opt))

    if n_fin < 2:
        n_fin = 2

    t_fin = c / n_fin - s_opt
    if t_fin < t_min:
        t_fin = t_min
        n_fin = math.floor(c / (s_opt + t_fin))
        if n_fin < 2:
            n_fin = 2
        t_fin = c / n_fin - s_opt
    if t_fin <= 0:
        t_fin = 0.1e-3

    v_total = v_max * 0.5
    v_ch = v_total / n_fin

    rth_ch, re_fin, _nu, _h = channel_rth(
        width=s_opt,
        height=c,
        length=L,
        flow_rate=v_ch,
        fluid=fluid,
    )
    rth_fin_cond = (t_fin / 2.0) / (lambda_hs * c * L)
    rth = (rth_fin_cond + rth_ch) / n_fin

    vol_cs = L * c * c * 1000.0  # [liters]
    cspi_val = cspi_calc(rth=rth, vol_cs=vol_cs)

    feasible = bool(re_fin < 2300 and t_fin > 0 and rth > 0 and math.isfinite(rth))

    return CspiOptResult(
        cspi=float(cspi_val),
        rth=float(rth),
        vol=float(vol_cs),
        n=int(n_fin),
        s=float(s_opt),
        t=float(t_fin),
        re=float(re_fin),
        n_fan=float(N),
        length=float(L),
        v_max=float(v_max),
        dp_max=float(dp_max),
        feasible=feasible,
    )


def cspi_sweep(
    *,
    a_chip: float,
    p_fan_max: float,
    lambdas: list[float],
    cs: list[float],
    t_min: float = 0.0,
    **kwargs,
) -> CspiSweepResult:
    """Parametric 2-D sweep over heatsink cross-section and thermal conductivity.

    Parameters
    ----------
    a_chip:    Total chip footprint area [m^2]
    p_fan_max: Maximum fan shaft power [W]
    lambdas:   List of thermal conductivities to sweep [W/(m K)]
    cs:        List of heatsink heights (fan diameters) to sweep [m]
    t_min:     Minimum fin thickness [m] (forwarded to cspi_optimize)
    **kwargs:  Additional keyword arguments forwarded to cspi_optimize
    """
    n_c = len(cs)
    n_l = len(lambdas)

    cspi_grid = np.zeros((n_c, n_l))
    rth_grid = np.zeros((n_c, n_l))

    for i, c in enumerate(cs):
        for j, lam in enumerate(lambdas):
            res = cspi_optimize(
                lambda_hs=lam,
                a_chip=a_chip,
                c=c,
                p_fan_max=p_fan_max,
                t_min=t_min,
                **kwargs,
            )
            cspi_grid[i, j] = res.cspi
            rth_grid[i, j] = res.rth

    return CspiSweepResult(
        cs=list(cs),
        lambdas=list(lambdas),
        cspi=cspi_grid,
        rth=rth_grid,
    )
