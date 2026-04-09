"""Single thermal layer with spreading resistance.

Ported from ``mfiles/Thermal/Designer/ThermalLayer.m``.
Uses the Lee/Simons/Ying analytical spreading model with
circular-equivalent area substitution.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ThermalLayer:
    """A single material layer with out-of-plane and in-plane conductivity.

    Parameters
    ----------
    thick : float
        Layer thickness [m].
    k_op : float
        Out-of-plane thermal conductivity [W/(m K)].
    k_ip : float | None
        In-plane thermal conductivity [W/(m K)].
        If None, isotropic: k_ip = k_op.
    """

    thick: float
    k_op: float
    k_ip: float | None = None

    def __post_init__(self) -> None:
        if self.k_ip is None:
            self.k_ip = self.k_op

    def resistance(
        self,
        a_in: float,
        a_out: float | None = None,
        h_eff: float | None = None,
    ) -> tuple[float, float, float]:
        """Compute thermal resistance through this layer.

        Parameters
        ----------
        a_in : float
            Heat source area [m^2].
        a_out : float | None
            Heat sink area [m^2]. If None, a_out = a_in (no spreading).
        h_eff : float | None
            Effective heat transfer coefficient at the bottom [W/(m^2 K)].
            Required when a_in != a_out for spreading calculation.

        Returns
        -------
        tuple[r_th, r_th_spread, r_th_through]
            Total resistance [K/W], spreading component [K/W],
            through-plane component [K/W].
        """
        if a_out is None:
            a_out = a_in

        r_th_through = self.thick / (self.k_op * a_out)

        if a_in == a_out or h_eff is None:
            return r_th_through, 0.0, r_th_through

        return _spreading_resistance(
            thick=self.thick,
            k_op=self.k_op,
            k_ip=self.k_ip,  # type: ignore[arg-type]
            a_in=a_in,
            a_out=a_out,
            h_eff=h_eff,
        )


def _spreading_resistance(
    *,
    thick: float,
    k_op: float,
    k_ip: float,
    a_in: float,
    a_out: float,
    h_eff: float,
) -> tuple[float, float, float]:
    """Lee/Simons/Ying spreading resistance with circular-equivalent areas.

    Reference: Lee et al. (1995), Simons simplified formula, Ying anisotropic model.

    The formula converts rectangular areas to circular equivalents, then
    computes a correction factor psi_max that accounts for finite-thickness
    constriction and convective boundary conditions.
    """
    sqrt_pi = math.sqrt(math.pi)

    # Circular-equivalent radii
    r_in = math.sqrt(a_in / math.pi)
    r_out = math.sqrt(a_out / math.pi)

    eps = r_in / r_out
    tau = thick / r_out
    alpha = math.sqrt(k_op / k_ip)  # anisotropy ratio
    bi = h_eff * r_out / k_op  # Biot number

    lam = math.pi + 1.0 / (eps * sqrt_pi)

    # phi: correction for finite thickness + convective BC
    lam_tau_alpha = lam * tau / alpha
    lam_alpha_bi = lam / (alpha * bi)

    tanh_val = math.tanh(lam_tau_alpha)
    phi = (tanh_val + lam_alpha_bi) / (1.0 + lam_alpha_bi * tanh_val)

    # psi_max: dimensionless spreading parameter
    psi_max = eps * tau / sqrt_pi + alpha * (1.0 / sqrt_pi) * (1.0 - eps) * phi

    # Total resistance
    r_th = psi_max / (k_op * r_in * sqrt_pi)
    r_th_through = thick / (k_op * a_out)
    r_th_spread = r_th - r_th_through

    return r_th, r_th_spread, r_th_through
