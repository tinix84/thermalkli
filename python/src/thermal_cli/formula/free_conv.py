"""Surface temperature solver under free convection + radiation.

Uses bisection to find the surface temperature that balances the total heat
dissipation across a set of faces with natural convection and radiation.

Algorithm matches the Octave reference implementation in
``lib/free_conv_surface_temp.m``.

All temperatures in Kelvin. All functions use keyword-only arguments.
"""

from __future__ import annotations

from dataclasses import dataclass

from thermal_cli.formula.convection import h_natural, h_radiation_linearized


@dataclass
class Face:
    """A single surface participating in free convection and radiation.

    Parameters
    ----------
    area : float
        Surface area [m²].
    char_length : float
        Characteristic length [m] (plate height for vertical surfaces,
        shortest side / L/4 for horizontal surfaces).
    orientation : str
        One of ``'vertical'``, ``'horizontal_top'``, or
        ``'horizontal_bottom'``.
    emissivity : float
        Surface emissivity (0-1). Defaults to 0.9.
    """

    area: float
    char_length: float
    orientation: str
    emissivity: float = 0.9


@dataclass
class FreeConvResult:
    """Results from :func:`free_conv_surface_temp`.

    Parameters
    ----------
    t_surface : float
        Converged surface temperature [K].
    h_per_face : list[float]
        Combined (natural convection + radiation) heat transfer coefficient
        for each face [W/(m²·K)].
    q_per_face : list[float]
        Heat dissipated by each face [W].
    """

    t_surface: float
    h_per_face: list[float]
    q_per_face: list[float]


def _heat_balance(
    t_surface: float,
    faces: list[Face],
    t_ambient: float,
    p_total: float,
) -> float:
    """Return heat-balance residual [W] at *t_surface*.

    Positive residual means the surface is too hot (dissipates more than
    *p_total*), negative means too cold.
    """
    total = 0.0
    for face in faces:
        h_nat, _ = h_natural(
            orientation=face.orientation,
            length=face.char_length,
            t_ambient=t_ambient,
            t_surface=t_surface,
        )
        h_rad = h_radiation_linearized(
            emissivity=face.emissivity,
            t_ambient=t_ambient,
            t_surface=t_surface,
        )
        total += (h_nat + h_rad) * face.area * (t_surface - t_ambient)
    return total - p_total


def free_conv_surface_temp(
    *,
    faces: list[Face],
    t_ambient: float,
    p_total: float,
    tol: float = 0.01,
    max_iter: int = 100,
) -> FreeConvResult:
    """Find surface temperature balancing free convection + radiation losses.

    Uses bisection on the heat-balance residual over the interval
    ``[t_ambient + 0.1, t_ambient + 500]``.  Convergence is declared when
    ``|residual| < tol * p_total * 0.001``.

    Parameters
    ----------
    faces : list[Face]
        Surfaces participating in heat transfer.
    t_ambient : float
        Ambient (far-field) temperature [K].
    p_total : float
        Total heat to be dissipated [W].
    tol : float
        Tolerance multiplier on ``p_total * 0.001``. Default 0.01.
    max_iter : int
        Maximum bisection iterations. Default 100.

    Returns
    -------
    FreeConvResult
        Converged surface temperature and per-face breakdown.
    """
    t_low = t_ambient + 0.1
    t_high = t_ambient + 500.0
    convergence_tol = tol * p_total * 0.001

    t_mid = t_low  # will be overwritten on first iteration
    for _ in range(max_iter):
        t_mid = (t_low + t_high) / 2.0
        residual = _heat_balance(t_mid, faces, t_ambient, p_total)
        if abs(residual) < convergence_tol:
            break
        if residual > 0.0:
            t_high = t_mid
        else:
            t_low = t_mid

    # Compute per-face breakdown at the converged surface temperature
    h_per_face: list[float] = []
    q_per_face: list[float] = []
    for face in faces:
        h_nat, _ = h_natural(
            orientation=face.orientation,
            length=face.char_length,
            t_ambient=t_ambient,
            t_surface=t_mid,
        )
        h_rad = h_radiation_linearized(
            emissivity=face.emissivity,
            t_ambient=t_ambient,
            t_surface=t_mid,
        )
        h_total = h_nat + h_rad
        h_per_face.append(h_total)
        q_per_face.append(h_total * face.area * (t_mid - t_ambient))

    return FreeConvResult(
        t_surface=t_mid,
        h_per_face=h_per_face,
        q_per_face=q_per_face,
    )
