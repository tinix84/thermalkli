"""Pulsed-power transient thermal impedance via superposition.

Ports ``lib/zth_pulsed.m``.

For a periodic square pulse with duty cycle D and period T, the effective
transient thermal impedance at time t is computed by superposition of the
Foster step-response on and off transitions:

    Zth_pulsed(t) = Σ_{n=0}^{N} [Zth_step(t - n·T) - Zth_step(t - D·T - n·T)]

where terms with a negative time argument are zero, and N is limited to 100
pulses for computational efficiency.
"""

from __future__ import annotations

import numpy as np


def _foster_step(t_val: float, r: np.ndarray, tau: np.ndarray) -> float:
    """Foster Zth at a single time point (0 for t_val <= 0)."""
    if t_val <= 0.0:
        return 0.0
    return float(np.sum(r * (1.0 - np.exp(-t_val / tau))))


def zth_pulsed(
    r: np.ndarray,
    tau: np.ndarray,
    t: np.ndarray,
    duty: float,
    period: float,
) -> np.ndarray:
    """Effective pulsed transient thermal impedance Zth_pulsed(t).

    Parameters
    ----------
    r : np.ndarray
        Foster-branch thermal resistances [K/W].
    tau : np.ndarray
        Foster-branch time constants [s].
    t : np.ndarray
        Time points at which to evaluate [s].
    duty : float
        Pulse duty cycle D in (0, 1].
    period : float
        Pulse period T [s].

    Returns
    -------
    np.ndarray
        Pulsed Zth values [K/W], same shape as ``t``.
    """
    r = np.asarray(r, dtype=float)
    tau = np.asarray(tau, dtype=float)
    zth = np.zeros(len(t), dtype=float)
    for k, tk in enumerate(t):
        n_pulses = min(int(tk / period) + 1, 100)
        val = 0.0
        for n in range(n_pulses):
            val += _foster_step(tk - n * period, r, tau)
            val -= _foster_step(tk - duty * period - n * period, r, tau)
        zth[k] = val
    return zth
