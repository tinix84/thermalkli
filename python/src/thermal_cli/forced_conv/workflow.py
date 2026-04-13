"""Forced-convection single-scenario workflow.

Ports ``mfiles/SoftwareTermico/Simulazione_singola/Simulazione_Singola.m``
to Python.  Orchestrates DB lookups, hydraulic operating point, fin thermal
resistance, and Fourier-series plane temperature.

All API units are SI: meters, Kelvin, Watts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from thermal_cli.forced_conv.plane_temp import PlaneTempConfig, calc_plane_temp
from thermal_cli.heatsinks.channel_flow import (
    cp_air,
    fin_thermal_resistance,
    hydraulic_operating_point,
    rho_air,
)
from thermal_cli.heatsinks.profiles_db import lookup_fan, lookup_hs_material, lookup_hs_profile


@dataclass
class ForcedConvConfig:
    """Configuration for ``run_forced_conv_sim``. All units SI (m, K, W)."""

    hs_profile: str  # key in db/hs_profiles.csv
    hs_material: str  # key in db/hs_materials.csv
    length_x_m: float  # a [m] — heatsink dim perp. to fins
    length_y_m: float  # b [m] — heatsink dim parallel to fins
    copper_plate_thickness_m: float  # tr [m]; 0 = no spreading plate
    fan_model: str  # key in db/fans.csv
    fan_count: int  # fans in parallel
    ventilation: str  # 'push' or 'impinge'
    impinge_gap_m: float  # s [m] — inlet aperture (impinge only)
    sources: list[dict[str, Any]]  # name, x_m, y_m, width_m, height_m, power_w
    t_inlet_k: float  # inlet air temperature [K]
    nx: int = 41  # grid points along X
    ny: int = 41  # grid points along Y
    n_fourier: int = 25  # Fourier series terms


@dataclass
class ForcedConvResult:
    """Result of a forced-convection single-scenario simulation. All units SI."""

    t_base_max_k: float  # peak baseplate temperature [K]
    t_fluid_out_k: float  # fluid outlet temperature [K]
    q_operating_m3s: float  # fan operating flow rate [m³/s]
    re_hydraulic: float  # average hydraulic Reynolds number
    rth_fin_kw: float  # fin thermal resistance [K/W]
    h_eq_wm2k: float  # equivalent h over footprint [W/(m²·K)]
    t_grid_k: np.ndarray  # shape (ny, nx) [K]
    x_grid_m: np.ndarray  # [m]
    y_grid_m: np.ndarray  # [m]


def run_forced_conv_sim(cfg: ForcedConvConfig) -> ForcedConvResult:
    """Run the full forced-convection simulation (mirrors Simulazione_Singola.m).

    Steps:
    1. Load heatsink profile + material + fan curve from DB.
    2. Scale fan curve for fan_count fans in parallel.
    3. Estimate mean air temperature from midpoint flow guess.
    4. Solve hydraulic operating point (bisection).
    5. Recompute mean air temperature at actual flow rate.
    6. Compute fin thermal resistance at actual conditions.
    7. Evaluate Fourier-series plane temperature on (nx x ny) grid.
    """
    if cfg.fan_count < 1:
        raise ValueError(f"fan_count must be >= 1, got {cfg.fan_count}")
    if cfg.nx < 1 or cfg.ny < 1:
        raise ValueError(f"nx and ny must be >= 1, got nx={cfg.nx}, ny={cfg.ny}")
    if cfg.n_fourier < 1:
        raise ValueError(f"n_fourier must be >= 1, got {cfg.n_fourier}")

    # 1. DB lookups
    prof = lookup_hs_profile(cfg.hs_profile)
    mat = lookup_hs_material(cfg.hs_material)
    fan = lookup_fan(cfg.fan_model)

    # Profile geometry — convert mm→m
    a_m = cfg.length_x_m
    b_m = cfg.length_y_m
    tb_m = prof.tb_mm / 1000.0
    hf_m = prof.hf_mm / 1000.0
    tf_m = prof.tf_mm / 1000.0
    bch_m = prof.bch_mm / 1000.0
    n_fins = round(a_m / (bch_m + tf_m))

    # 2. Scale fan curve for parallel fans
    fan_qv = fan.qv * cfg.fan_count
    fan_hv = fan.hv

    # 3. Initial T_air estimate using midpoint flow guess
    q_guess = (fan_qv[0] + fan_qv[-1]) / 2.0
    total_power = sum(float(s["power_w"]) for s in cfg.sources)
    t_in_k = cfg.t_inlet_k
    t_air_k = t_in_k + 0.5 * total_power / (cp_air(t_in_k) * rho_air(t_in_k) * q_guess)

    # 4. Hydraulic operating point
    hydr = hydraulic_operating_point(
        b=b_m,
        s=cfg.impinge_gap_m,
        n_fins=n_fins,
        tf=tf_m,
        bch=bch_m,
        hf=hf_m,
        t_air=t_air_k,
        vent_type=cfg.ventilation,
        fan_qv=fan_qv,
        fan_hv=fan_hv,
    )
    qv_f = hydr.flowrate

    # 5. Recompute T_air at actual flow rate
    t_air_k = t_in_k + 0.5 * total_power / (cp_air(t_in_k) * rho_air(t_in_k) * qv_f)

    # 6. Fin thermal resistance
    fin = fin_thermal_resistance(
        qv_f=qv_f,
        a=a_m,
        b=b_m,
        s=cfg.impinge_gap_m,
        tf=tf_m,
        bch=bch_m,
        hf=hf_m,
        t_air=t_air_k,
        vent_type=cfg.ventilation,
        k_fin=mat.k_fin,
        n_fins=n_fins,
    )

    # 7. Plane temperature distribution
    x_pts = np.linspace(0.0, a_m, cfg.nx)
    y_pts = np.linspace(0.0, b_m, cfg.ny)

    effective_has_piastra = mat.has_piastra and cfg.copper_plate_thickness_m > 0
    plane_cfg = PlaneTempConfig(
        rth_fin=fin.rth,
        h_eq=fin.h_eq,
        sources=cfg.sources,
        t_air_k=t_air_k,
        t_inlet_k=t_in_k,
        a_m=a_m,
        b_m=b_m,
        k_plate=mat.k_plate,
        tb_m=tb_m,
        has_piastra=effective_has_piastra,
        k_piastra=mat.k_piastra,
        tr_m=cfg.copper_plate_thickness_m,
        n_fourier=cfg.n_fourier,
    )
    plane = calc_plane_temp(plane_cfg, x_pts, y_pts)

    return ForcedConvResult(
        t_base_max_k=plane.t_max_k,
        t_fluid_out_k=plane.t_fluid_out_k,
        q_operating_m3s=qv_f,
        re_hydraulic=hydr.reynolds,
        rth_fin_kw=fin.rth,
        h_eq_wm2k=fin.h_eq,
        t_grid_k=plane.t_grid_k,
        x_grid_m=x_pts,
        y_grid_m=y_pts,
    )
