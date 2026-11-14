"""Foster thermal network transient impedance Zth(t).

Ports ``lib/zth_foster.m``.

Formula: ``Zth(t) = Σ_i R_i * (1 - exp(-t / τ_i))``

Time axis is log-spaced from ``min(τ) / 10`` to ``t_end``.
"""

from __future__ import annotations

import numpy as np


def zth_foster(
    r: np.ndarray,
    tau: np.ndarray,
    t_end: float,
    n_points: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute Foster-network transient thermal impedance Zth(t).

    Parameters
    ----------
    r : np.ndarray
        Array of Foster-branch thermal resistances [K/W].
    tau : np.ndarray
        Array of Foster-branch time constants τ_i = R_i·C_i [s].
    t_end : float
        End time of the Zth curve [s].
    n_points : int
        Number of log-spaced time points (default 200).

    Returns
    -------
    zth : np.ndarray
        Thermal impedance values [K/W], shape (n_points,).
    t : np.ndarray
        Time axis [s], log-spaced from min(τ)/10 to t_end, shape (n_points,).
    """
    r = np.asarray(r, dtype=float)
    tau = np.asarray(tau, dtype=float)
    t = np.logspace(np.log10(np.min(tau) / 10.0), np.log10(t_end), n_points)
    zth = np.zeros(n_points, dtype=float)
    for ri, taui in zip(r, tau, strict=True):
        zth += ri * (1.0 - np.exp(-t / taui))
    return zth, t
