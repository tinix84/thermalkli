"""Fanless heatsink thermal resistance under natural convection.

Iterative bisection solver that finds the heatsink surface temperature where
the heat dissipated by convection + radiation equals the applied power loss.

Algorithm matches the Octave reference ``lib/cmd_natural_conv_hs.m``.

All temperatures in Kelvin, lengths in meters, power in Watts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from thermal_cli.formula.convection import h_natural, h_radiation_linearized


@dataclass
class NaturalConvHsResult:
    """Results from the natural-convection heatsink solver.

    Attributes
    ----------
    t_surface : float
        Heatsink surface temperature [K].
    rth : float
        Thermal resistance from surface to ambient [K/W].
    h_fin : float
        Combined (convection + radiation) heat transfer coefficient on fin
        surfaces [W/(m² K)].
    h_base : float
        Combined heat transfer coefficient on the base (inter-fin) surfaces
        [W/(m² K)].
    eta_fin : float
        Fin efficiency [-].
    q_total : float
        Total heat dissipated at convergence [W].
    """

    t_surface: float
    rth: float
    h_fin: float
    h_base: float
    eta_fin: float
    q_total: float


def natural_conv_hs(
    *,
    n_fins: int,
    fin_height: float,
    fin_length: float,
    fin_thickness: float,
    channel_width: float,
    base_thickness: float,  # kept for API parity; not used in calculation
    k: float,
    t_ambient: float,
    p_loss: float,
    emissivity: float = 0.9,
) -> NaturalConvHsResult:
    """Solve for heatsink surface temperature and thermal resistance.

    Uses bisection on the surface temperature ``Ts`` until the heat
    dissipated by the fin array equals ``p_loss`` within 0.01%.

    Parameters
    ----------
    n_fins : int
        Number of fins.
    fin_height : float
        Fin height (vertical extent) [m].
    fin_length : float
        Fin length (horizontal depth) [m].
    fin_thickness : float
        Fin thickness [m].
    channel_width : float
        Width of the inter-fin channel [m].
    base_thickness : float
        Base plate thickness [m] — kept for API parity, not used.
    k : float
        Thermal conductivity of the fin material [W/(m K)].
    t_ambient : float
        Ambient temperature [K].
    p_loss : float
        Applied power loss [W].
    emissivity : float
        Surface emissivity (default 0.9).

    Returns
    -------
    NaturalConvHsResult
        Converged surface temperature, thermal resistance, and auxiliary data.
    """
    ts_low = t_ambient + 0.1
    ts_high = t_ambient + 200.0

    # Bisection — 100 iterations gives convergence to ~200/2^100 ≈ 1e-28 K
    ts = t_ambient  # will be overwritten in first iteration
    h_fin = 0.0
    h_base = 0.0
    eta_fin = 1.0
    q_total = 0.0

    for _ in range(100):
        ts = (ts_low + ts_high) / 2.0

        # --- Fin surfaces (treated as vertical flat plates) ---
        h_fin_nat, _ = h_natural(
            orientation="vertical",
            length=fin_height,
            t_ambient=t_ambient,
            t_surface=ts,
        )
        h_fin_rad = h_radiation_linearized(
            emissivity=emissivity,
            t_ambient=t_ambient,
            t_surface=ts,
        )
        h_fin = h_fin_nat + h_fin_rad

        # --- Fin efficiency ---
        m_hf = math.sqrt(2.0 * h_fin / (k * fin_thickness)) * fin_height
        eta_fin = math.tanh(m_hf) / m_hf if m_hf > 0.0 else 1.0

        # --- Base (inter-fin) surfaces (horizontal, heated side up) ---
        h_base_nat, _ = h_natural(
            orientation="horizontal_top",
            length=channel_width,
            t_ambient=t_ambient,
            t_surface=ts,
        )
        h_base_rad = h_radiation_linearized(
            emissivity=emissivity,
            t_ambient=t_ambient,
            t_surface=ts,
        )
        h_base = h_base_nat + h_base_rad

        # --- Heat dissipated ---
        a_fin = n_fins * 2.0 * fin_height * fin_length
        a_base = (n_fins - 1) * channel_width * fin_length
        delta_t = ts - t_ambient
        q_total = h_fin * eta_fin * a_fin * delta_t + h_base * a_base * delta_t

        # Convergence check
        if abs(q_total - p_loss) < p_loss * 1e-4:
            break

        if q_total > p_loss:
            ts_high = ts
        else:
            ts_low = ts

    rth = (ts - t_ambient) / p_loss

    return NaturalConvHsResult(
        t_surface=ts,
        rth=rth,
        h_fin=h_fin,
        h_base=h_base,
        eta_fin=eta_fin,
        q_total=q_total,
    )
