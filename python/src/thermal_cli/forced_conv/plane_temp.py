"""Fourier-series baseplate temperature distribution.

Ports ``mfiles/SoftwareTermico/Visualizzazione_plane/Tplane_dist.m`` and
``Temp_calc.m`` to Python.

All spatial dimensions are in **mm** internally (matching the Octave source).
Temperature arguments and return values are in **°C**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PlaneTempConfig:
    """Configuration for ``calc_plane_temp``.

    Spatial dimensions in mm. Temperatures in °C. Conductivities in W/(m·K).
    """

    rth_fin: float          # equivalent fin thermal resistance [K/W]
    h_eq: float             # equivalent heat-transfer coeff over footprint [W/(m²·K)]
    sources: list[dict[str, Any]]  # each: name, x_mm, y_mm, width_mm, height_mm, power_w
    t_air_c: float          # mean air temperature [°C]
    t_inlet_c: float        # inlet air temperature [°C]
    a_mm: float             # heatsink X dimension (perpendicular to fins) [mm]
    b_mm: float             # heatsink Y dimension (parallel to fins) [mm]
    k_plate: float          # baseplate thermal conductivity [W/(m·K)]
    tb_mm: float            # baseplate thickness [mm]
    has_piastra: bool = False
    k_piastra: float = 0.0  # copper spreading-plate conductivity [W/(m·K)]
    tr_mm: float = 0.0      # copper plate thickness [mm]
    n_fourier: int = 25     # number of Fourier terms per direction


@dataclass
class PlaneTempResult:
    """Result of a Fourier-series plane temperature calculation."""

    t_base_c: float         # base plate temperature T_h_BP [°C]
    t_max_c: float          # peak surface temperature [°C]
    t_fluid_out_c: float    # fluid outlet temperature [°C]
    t_grid_c: np.ndarray    # shape (len(y_pts), len(x_pts)) [°C]
    x_grid_mm: np.ndarray   # x coordinates [mm]
    y_grid_mm: np.ndarray   # y coordinates [mm]


# ---------------------------------------------------------------------------
# Internal helpers (mirror Octave nested functions in Temp_calc.m)
# ---------------------------------------------------------------------------


def _psi(
    eps: float,
    *,
    k_plate: float,
    k_piastra: float,
    tb_mm: float,
    tr_mm: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """Spreading correction factor Ψ(ε).

    Ports ``Psicalc`` from ``Temp_calc.m``.  ``eps`` is the wavenumber [rad/m].
    """
    tb = tb_mm / 1000.0
    tr = tr_mm / 1000.0
    if has_piastra:
        rho = (eps + h_eq / k_piastra) / (eps - h_eq / k_piastra)
        alfa = (1.0 - k_piastra / k_plate) / (1.0 + k_piastra / k_plate)
        e4tb = math.exp(4.0 * eps * tb)
        e2tb = math.exp(2.0 * eps * tb)
        e_2tb_tr = math.exp(2.0 * eps * (2.0 * tb + tr))
        e_tb_tr = math.exp(2.0 * eps * (tb + tr))
        psi_n = alfa * e4tb - e2tb + rho * (e_2tb_tr - alfa * e_tb_tr)
        psi_d = alfa * e4tb + e2tb + rho * (e_2tb_tr + alfa * e_tb_tr)
        return psi_n / psi_d
    else:
        epsb = eps * tb
        return (eps * math.sinh(epsb) + (h_eq / k_plate) * math.cosh(epsb)) / (
            eps * math.cosh(epsb) + (h_eq / k_plate) * math.sinh(epsb)
        )


def _theta_x(
    x_mm: float,
    xc_mm: float,
    wid_mm: float,
    power_w: float,
    a_mm: float,
    b_mm: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_mm: float,
    tr_mm: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """X-direction Fourier component ΘX(x)."""
    a = a_mm / 1000.0
    xc = xc_mm / 1000.0
    wid = wid_mm / 1000.0
    x = x_mm / 1000.0
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate, k_piastra=k_piastra, tb_mm=tb_mm,
        tr_mm=tr_mm, h_eq=h_eq, has_piastra=has_piastra,
    )
    for m in range(1, n_fourier + 1):
        lam = m * math.pi / a
        psi = _psi(lam, **psi_kw)
        sin_term = math.sin((2 * xc + wid) * lam / 2) - math.sin((2 * xc - wid) * lam / 2)
        # denominator factor: a*b*wid in m³ = (a_mm*b_mm*wid_mm)/1e9
        denom = a_mm * b_mm * wid_mm * k_plate * lam**2 * psi / 1e9
        a1 = 2.0 * power_w * sin_term / denom
        total += a1 * math.cos(lam * x)
    return total


def _theta_y(
    y_mm: float,
    yc_mm: float,
    hgt_mm: float,
    power_w: float,
    a_mm: float,
    b_mm: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_mm: float,
    tr_mm: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """Y-direction Fourier component ΘY(y)."""
    b = b_mm / 1000.0
    yc = yc_mm / 1000.0
    hgt = hgt_mm / 1000.0
    y = y_mm / 1000.0
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate, k_piastra=k_piastra, tb_mm=tb_mm,
        tr_mm=tr_mm, h_eq=h_eq, has_piastra=has_piastra,
    )
    for n in range(1, n_fourier + 1):
        delta = n * math.pi / b
        psi = _psi(delta, **psi_kw)
        sin_term = math.sin((2 * yc + hgt) * delta / 2) - math.sin((2 * yc - hgt) * delta / 2)
        denom = a_mm * b_mm * hgt_mm * k_plate * delta**2 * psi / 1e9
        a2 = 2.0 * power_w * sin_term / denom
        total += a2 * math.cos(delta * y)
    return total


def _theta_xy(
    x_mm: float,
    y_mm: float,
    xc_mm: float,
    yc_mm: float,
    wid_mm: float,
    hgt_mm: float,
    power_w: float,
    a_mm: float,
    b_mm: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_mm: float,
    tr_mm: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """2D Fourier component ΘXY(x,y)."""
    a = a_mm / 1000.0
    b = b_mm / 1000.0
    xc = xc_mm / 1000.0
    yc = yc_mm / 1000.0
    wid = wid_mm / 1000.0
    hgt = hgt_mm / 1000.0
    x = x_mm / 1000.0
    y = y_mm / 1000.0
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate, k_piastra=k_piastra, tb_mm=tb_mm,
        tr_mm=tr_mm, h_eq=h_eq, has_piastra=has_piastra,
    )
    for m in range(1, n_fourier + 1):
        lam = m * math.pi / a
        for n in range(1, n_fourier + 1):
            delta = n * math.pi / b
            beta = math.sqrt(lam**2 + delta**2)
            psi = _psi(beta, **psi_kw)
            num = (
                16.0 * power_w
                * math.cos(lam * xc) * math.sin(lam * wid / 2)
                * math.cos(delta * yc) * math.sin(delta * hgt / 2)
            )
            # denominator: a*b*wid*hgt in m⁴ = (a_mm*b_mm*wid_mm*hgt_mm)/1e12
            denom = a_mm * b_mm * wid_mm * hgt_mm * k_plate * beta * lam * delta * psi / 1e12
            a3 = num / denom
            total += a3 * math.cos(lam * x) * math.cos(delta * y)
    return total


def _temp_at_point(
    x_mm: float,
    y_mm: float,
    t_h_bp: float,
    *,
    sources: list[dict],
    a_mm: float,
    b_mm: float,
    k_plate: float,
    k_piastra: float,
    tb_mm: float,
    tr_mm: float,
    h_eq: float,
    has_piastra: bool,
    n_fourier: int,
) -> float:
    """Temperature at a single baseplate point (x_mm, y_mm) [°C].

    Ports ``Temp_calc`` from Octave.
    """
    a_hs = a_mm * b_mm / 1e6  # heatsink footprint area [m²]
    fourier_kw = dict(
        a_mm=a_mm,
        b_mm=b_mm,
        n_fourier=n_fourier,
        k_plate=k_plate,
        k_piastra=k_piastra,
        tb_mm=tb_mm,
        tr_mm=tr_mm,
        h_eq=h_eq,
        has_piastra=has_piastra,
    )
    d_theta = 0.0
    for src in sources:
        p = float(src["power_w"])
        xc = float(src["x_mm"])
        yc = float(src["y_mm"])
        wid = float(src["width_mm"])
        hgt = float(src["height_mm"])
        if has_piastra:
            ao = (p / a_hs) * (tb_mm / (k_plate * 1e3) + tr_mm / (k_piastra * 1e3) + 1.0 / h_eq)
        else:
            ao = (p / a_hs) * (tb_mm / (k_plate * 1e3) + 1.0 / h_eq)
        d_theta += (
            ao
            + _theta_x(x_mm, xc, wid, p, **fourier_kw)
            + _theta_y(y_mm, yc, hgt, p, **fourier_kw)
            + _theta_xy(x_mm, y_mm, xc, yc, wid, hgt, p, **fourier_kw)
        )
    return t_h_bp + d_theta


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calc_plane_temp(
    cfg: PlaneTempConfig,
    x_pts_mm: np.ndarray,
    y_pts_mm: np.ndarray,
) -> PlaneTempResult:
    """Compute 2D baseplate temperature via Fourier-series superposition.

    Ports ``Tplane_dist`` from Octave. Returns temperatures in °C.

    Parameters
    ----------
    cfg : PlaneTempConfig
    x_pts_mm : np.ndarray
        X grid coordinates [mm].
    y_pts_mm : np.ndarray
        Y grid coordinates [mm].

    Returns
    -------
    PlaneTempResult
    """
    total_power = sum(float(s["power_w"]) for s in cfg.sources)

    # LMTD and base temperature (Tplane_dist.m lines 1-3)
    lmtd = cfg.rth_fin * total_power
    t_fluid_out = 2.0 * cfg.t_air_c - cfg.t_inlet_c

    dt = t_fluid_out - cfg.t_inlet_c
    if abs(dt) < 1e-12 or abs(lmtd) < 1e-12:
        # negligible power: base plate ≈ inlet temp
        t_h_bp = cfg.t_inlet_c
    else:
        exp_term = math.exp(dt / lmtd)
        t_h_bp = (cfg.t_inlet_c - t_fluid_out * exp_term) / (1.0 - exp_term) - lmtd

    # Effective base-plate surface temperature: add average piastra resistance
    # when a copper spreading plate is present.  The Ao term in _temp_at_point
    # already contains the distributed piastra contribution, so t_h_bp_eff is
    # used only as the reported base temperature — it is NOT passed to
    # _temp_at_point (which still receives t_h_bp).
    if cfg.has_piastra and cfg.k_piastra > 0.0 and cfg.tr_mm > 0.0:
        a_hs = cfg.a_mm * cfg.b_mm / 1e6  # footprint area [m²]
        rth_piastra_avg = (cfg.tr_mm / 1000.0) / (cfg.k_piastra * a_hs)
        t_base_reported = t_h_bp + rth_piastra_avg * total_power
    else:
        t_base_reported = t_h_bp

    pt_kw = dict(
        sources=cfg.sources,
        a_mm=cfg.a_mm,
        b_mm=cfg.b_mm,
        k_plate=cfg.k_plate,
        k_piastra=cfg.k_piastra,
        tb_mm=cfg.tb_mm,
        tr_mm=cfg.tr_mm,
        h_eq=cfg.h_eq,
        has_piastra=cfg.has_piastra,
        n_fourier=cfg.n_fourier,
    )
    ny, nx = len(y_pts_mm), len(x_pts_mm)
    grid = np.empty((ny, nx), dtype=float)
    for j, y in enumerate(y_pts_mm):
        for i, x in enumerate(x_pts_mm):
            grid[j, i] = _temp_at_point(float(x), float(y), t_h_bp, **pt_kw)

    return PlaneTempResult(
        t_base_c=t_base_reported,
        t_max_c=float(np.max(grid)),
        t_fluid_out_c=t_fluid_out,
        t_grid_c=grid,
        x_grid_mm=np.asarray(x_pts_mm, dtype=float),
        y_grid_mm=np.asarray(y_pts_mm, dtype=float),
    )
