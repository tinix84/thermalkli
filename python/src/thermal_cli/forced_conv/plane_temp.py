"""Fourier-series baseplate temperature distribution.

Ports ``mfiles/SoftwareTermico/Visualizzazione_plane/Tplane_dist.m`` and
``Temp_calc.m`` to Python.

All spatial dimensions are in **meters** (SI). Temperatures in **Kelvin**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class PlaneTempConfig:
    """Configuration for ``calc_plane_temp``.

    Spatial dimensions in meters (SI). Temperatures in Kelvin. Conductivities in W/(m·K).
    """

    rth_fin: float  # equivalent fin thermal resistance [K/W]
    h_eq: float  # equivalent heat-transfer coeff over footprint [W/(m²·K)]
    sources: list[dict[str, Any]]  # each: name, x_m, y_m, width_m, height_m, power_w
    t_air_k: float  # mean air temperature [K]
    t_inlet_k: float  # inlet air temperature [K]
    a_m: float  # heatsink X dimension (perpendicular to fins) [m]
    b_m: float  # heatsink Y dimension (parallel to fins) [m]
    k_plate: float  # baseplate thermal conductivity [W/(m·K)]
    tb_m: float  # baseplate thickness [m]
    has_piastra: bool = False
    k_piastra: float = 0.0  # copper spreading-plate conductivity [W/(m·K)]
    tr_m: float = 0.0  # copper plate thickness [m]
    n_fourier: int = 25  # number of Fourier terms per direction


@dataclass
class PlaneTempResult:
    """Result of a Fourier-series plane temperature calculation."""

    t_base_k: float  # base plate temperature T_h_BP [K]
    t_max_k: float  # peak surface temperature [K]
    t_fluid_out_k: float  # fluid outlet temperature [K]
    t_grid_k: np.ndarray  # shape (len(y_pts), len(x_pts)) [K]
    x_grid_m: np.ndarray  # x coordinates [m]
    y_grid_m: np.ndarray  # y coordinates [m]


# ---------------------------------------------------------------------------
# Internal helpers (mirror Octave nested functions in Temp_calc.m)
# ---------------------------------------------------------------------------


def _psi(
    eps: float,
    *,
    k_plate: float,
    k_piastra: float,
    tb_m: float,
    tr_m: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """Spreading correction factor Ψ(ε).

    Ports ``Psicalc`` from ``Temp_calc.m``.  ``eps`` is the wavenumber [rad/m].
    """
    tb = tb_m
    tr = tr_m
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
    x_m: float,
    xc_m: float,
    wid_m: float,
    power_w: float,
    a_m: float,
    b_m: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_m: float,
    tr_m: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """X-direction Fourier component ΘX(x)."""
    a = a_m
    xc = xc_m
    wid = wid_m
    x = x_m
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate,
        k_piastra=k_piastra,
        tb_m=tb_m,
        tr_m=tr_m,
        h_eq=h_eq,
        has_piastra=has_piastra,
    )
    for m in range(1, n_fourier + 1):
        lam = m * math.pi / a
        psi = _psi(lam, **psi_kw)
        sin_term = math.sin((2 * xc + wid) * lam / 2) - math.sin((2 * xc - wid) * lam / 2)
        denom = a_m * b_m * wid_m * k_plate * lam**2 * psi
        a1 = 2.0 * power_w * sin_term / denom
        total += a1 * math.cos(lam * x)
    return total


def _theta_y(
    y_m: float,
    yc_m: float,
    hgt_m: float,
    power_w: float,
    a_m: float,
    b_m: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_m: float,
    tr_m: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """Y-direction Fourier component ΘY(y)."""
    b = b_m
    yc = yc_m
    hgt = hgt_m
    y = y_m
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate,
        k_piastra=k_piastra,
        tb_m=tb_m,
        tr_m=tr_m,
        h_eq=h_eq,
        has_piastra=has_piastra,
    )
    for n in range(1, n_fourier + 1):
        delta = n * math.pi / b
        psi = _psi(delta, **psi_kw)
        sin_term = math.sin((2 * yc + hgt) * delta / 2) - math.sin((2 * yc - hgt) * delta / 2)
        denom = a_m * b_m * hgt_m * k_plate * delta**2 * psi
        a2 = 2.0 * power_w * sin_term / denom
        total += a2 * math.cos(delta * y)
    return total


def _theta_xy(
    x_m: float,
    y_m: float,
    xc_m: float,
    yc_m: float,
    wid_m: float,
    hgt_m: float,
    power_w: float,
    a_m: float,
    b_m: float,
    n_fourier: int,
    *,
    k_plate: float,
    k_piastra: float,
    tb_m: float,
    tr_m: float,
    h_eq: float,
    has_piastra: bool,
) -> float:
    """2D Fourier component ΘXY(x,y)."""
    a = a_m
    b = b_m
    xc = xc_m
    yc = yc_m
    wid = wid_m
    hgt = hgt_m
    x = x_m
    y = y_m
    total = 0.0
    psi_kw = dict(
        k_plate=k_plate,
        k_piastra=k_piastra,
        tb_m=tb_m,
        tr_m=tr_m,
        h_eq=h_eq,
        has_piastra=has_piastra,
    )
    for m in range(1, n_fourier + 1):
        lam = m * math.pi / a
        for n in range(1, n_fourier + 1):
            delta = n * math.pi / b
            beta = math.sqrt(lam**2 + delta**2)
            psi = _psi(beta, **psi_kw)
            num = (
                16.0
                * power_w
                * math.cos(lam * xc)
                * math.sin(lam * wid / 2)
                * math.cos(delta * yc)
                * math.sin(delta * hgt / 2)
            )
            denom = a_m * b_m * wid_m * hgt_m * k_plate * beta * lam * delta * psi
            a3 = num / denom
            total += a3 * math.cos(lam * x) * math.cos(delta * y)
    return total


def _temp_at_point(
    x_m: float,
    y_m: float,
    t_h_bp: float,
    *,
    sources: list[dict],
    a_m: float,
    b_m: float,
    k_plate: float,
    k_piastra: float,
    tb_m: float,
    tr_m: float,
    h_eq: float,
    has_piastra: bool,
    n_fourier: int,
) -> float:
    """Temperature at a single baseplate point (x_m, y_m) [K].

    Ports ``Temp_calc`` from Octave.
    """
    a_hs = a_m * b_m  # heatsink footprint area [m²]
    fourier_kw = dict(
        a_m=a_m,
        b_m=b_m,
        n_fourier=n_fourier,
        k_plate=k_plate,
        k_piastra=k_piastra,
        tb_m=tb_m,
        tr_m=tr_m,
        h_eq=h_eq,
        has_piastra=has_piastra,
    )
    d_theta = 0.0
    for src in sources:
        p = float(src["power_w"])
        xc = float(src["x_m"])
        yc = float(src["y_m"])
        wid = float(src["width_m"])
        hgt = float(src["height_m"])
        if has_piastra:
            ao = (p / a_hs) * (tb_m / k_plate + tr_m / k_piastra + 1.0 / h_eq)
        else:
            ao = (p / a_hs) * (tb_m / k_plate + 1.0 / h_eq)
        d_theta += (
            ao
            + _theta_x(x_m, xc, wid, p, **fourier_kw)
            + _theta_y(y_m, yc, hgt, p, **fourier_kw)
            + _theta_xy(x_m, y_m, xc, yc, wid, hgt, p, **fourier_kw)
        )
    return t_h_bp + d_theta


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calc_plane_temp(
    cfg: PlaneTempConfig,
    x_pts_m: np.ndarray,
    y_pts_m: np.ndarray,
) -> PlaneTempResult:
    """Compute 2D baseplate temperature via Fourier-series superposition.

    Ports ``Tplane_dist`` from Octave. Returns temperatures in Kelvin.

    Parameters
    ----------
    cfg : PlaneTempConfig
    x_pts_m : np.ndarray
        X grid coordinates [m].
    y_pts_m : np.ndarray
        Y grid coordinates [m].

    Returns
    -------
    PlaneTempResult
    """
    total_power = sum(float(s["power_w"]) for s in cfg.sources)

    # LMTD and base temperature (Tplane_dist.m lines 1-3)
    lmtd = cfg.rth_fin * total_power
    t_fluid_out = 2.0 * cfg.t_air_k - cfg.t_inlet_k

    dt = t_fluid_out - cfg.t_inlet_k
    if abs(dt) < 1e-12 or abs(lmtd) < 1e-12 or abs(dt / lmtd) > 700:
        # negligible power or overflow guard: base plate ≈ inlet temp
        t_h_bp = cfg.t_inlet_k
    else:
        exp_term = math.exp(dt / lmtd)
        t_h_bp = (cfg.t_inlet_k - t_fluid_out * exp_term) / (1.0 - exp_term) - lmtd

    # Guard: treat as no-piastra if conductivity or thickness is zero
    effective_has_piastra = cfg.has_piastra and cfg.k_piastra > 0 and cfg.tr_m > 0

    # Effective base-plate surface temperature: add average piastra resistance
    # when a copper spreading plate is present.  The Ao term in _temp_at_point
    # already contains the distributed piastra contribution, so t_h_bp_eff is
    # used only as the reported base temperature — it is NOT passed to
    # _temp_at_point (which still receives t_h_bp).
    if effective_has_piastra:
        a_hs = cfg.a_m * cfg.b_m  # footprint area [m²]
        rth_piastra_avg = cfg.tr_m / (cfg.k_piastra * a_hs)
        t_base_reported = t_h_bp + rth_piastra_avg * total_power
    else:
        t_base_reported = t_h_bp

    pt_kw = dict(
        sources=cfg.sources,
        a_m=cfg.a_m,
        b_m=cfg.b_m,
        k_plate=cfg.k_plate,
        k_piastra=cfg.k_piastra,
        tb_m=cfg.tb_m,
        tr_m=cfg.tr_m,
        h_eq=cfg.h_eq,
        has_piastra=effective_has_piastra,
        n_fourier=cfg.n_fourier,
    )
    ny, nx = len(y_pts_m), len(x_pts_m)
    grid = np.empty((ny, nx), dtype=float)
    for j, y in enumerate(y_pts_m):
        for i, x in enumerate(x_pts_m):
            grid[j, i] = _temp_at_point(float(x), float(y), t_h_bp, **pt_kw)

    return PlaneTempResult(
        t_base_k=t_base_reported,
        t_max_k=float(np.max(grid)),
        t_fluid_out_k=t_fluid_out,
        t_grid_k=grid,
        x_grid_m=np.asarray(x_pts_m, dtype=float),
        y_grid_m=np.asarray(y_pts_m, dtype=float),
    )
