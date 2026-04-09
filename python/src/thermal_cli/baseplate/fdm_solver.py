"""2.5D FDM solver for baseplate temperature distribution.

Solves the steady-state PDE:
    -k * t * nabla^2(T) + (T - T_inf) / R''_vert = q''(x, y)

where:
    k = baseplate conductivity [W/(m K)]
    t = baseplate thickness [m]
    R''_vert = R_sa / A_base [K m^2 / W] (vertical sink resistance per area)
    q'' = heat flux from devices [W/m^2]

Discretized on a uniform rectangular grid with adiabatic (Neumann) BCs.
Uses scipy sparse direct solver (spsolve).
"""

from __future__ import annotations

import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

from thermal_cli.baseplate.types import BaseplateConfig, BaseplateResult, DeviceResult


def solve_fdm(config: BaseplateConfig) -> BaseplateResult:
    """Solve the 2.5D baseplate PDE via finite differences.

    Parameters
    ----------
    config : BaseplateConfig
        Baseplate geometry, material, devices, and grid resolution.

    Returns
    -------
    BaseplateResult
        Temperature field and per-device junction temperatures.
    """
    nx, ny = config.nx, config.ny
    lx, ly = config.lx, config.ly
    k = config.conductivity
    t = config.thickness
    r_sa = config.r_sa
    t_inf = config.t_ambient

    dx = lx / (nx - 1)
    dy = ly / (ny - 1)
    x = np.linspace(0, lx, nx)
    y = np.linspace(0, ly, ny)

    # Total baseplate area for R''_vert conversion
    a_base = lx * ly
    r_vert = r_sa / a_base  # [K m^2 / W]

    # Coefficient for vertical sink coupling
    alpha = 1.0 / (r_vert * k * t) if r_vert > 0 else 0.0

    n = nx * ny
    a_mat = lil_matrix((n, n), dtype=np.float64)
    rhs = np.zeros(n)

    def idx(i: int, j: int) -> int:
        return j * nx + i

    # Build heat source map q''(x, y) [W/m^2]
    q = np.zeros((ny, nx))
    for dev in config.devices:
        x_min = dev.x - dev.width / 2
        x_max = dev.x + dev.width / 2
        y_min = dev.y - dev.height / 2
        y_max = dev.y + dev.height / 2
        area = dev.width * dev.height
        flux = dev.power / area if area > 0 else 0.0
        for j in range(ny):
            for i in range(nx):
                if x_min <= x[i] <= x_max and y_min <= y[j] <= y_max:
                    q[j, i] = flux

    # Assemble sparse system (positive-definite form: A T = b)
    # PDE: -k*t*nabla^2(T) + (T - T_inf)/R_vert = q
    # Discretized: (2cx + 2cy + alpha)*T_ij - cx*neighbors = q/(k*t) + alpha*T_inf
    cx = 1.0 / dx**2
    cy = 1.0 / dy**2

    for j in range(ny):
        for i in range(nx):
            p = idx(i, j)
            rhs[p] = q[j, i] / (k * t) + alpha * t_inf

            center = 2.0 * cx + 2.0 * cy + alpha

            # Neumann BCs: dT/dn = 0 → ghost node = interior → double the coeff
            if i == 0:
                a_mat[p, idx(i + 1, j)] = -2 * cx
            elif i == nx - 1:
                a_mat[p, idx(i - 1, j)] = -2 * cx
            else:
                a_mat[p, idx(i - 1, j)] = -cx
                a_mat[p, idx(i + 1, j)] = -cx

            if j == 0:
                a_mat[p, idx(i, j + 1)] = -2 * cy
            elif j == ny - 1:
                a_mat[p, idx(i, j - 1)] = -2 * cy
            else:
                a_mat[p, idx(i, j - 1)] = -cy
                a_mat[p, idx(i, j + 1)] = -cy

            a_mat[p, p] = center

    # Solve
    a_csr = a_mat.tocsr()
    t_flat = spsolve(a_csr, rhs)
    t_field = t_flat.reshape((ny, nx))

    # Per-device results
    device_results = []
    for dev in config.devices:
        # Find nearest grid point to device center
        i_dev = int(np.argmin(np.abs(x - dev.x)))
        j_dev = int(np.argmin(np.abs(y - dev.y)))
        t_base = float(t_field[j_dev, i_dev])
        t_case = t_base + dev.power * dev.r_interface
        t_junction = t_case + dev.power * dev.r_jc
        device_results.append(
            DeviceResult(name=dev.name, t_base=t_base, t_case=t_case, t_junction=t_junction)
        )

    t_js = [d.t_junction for d in device_results]
    return BaseplateResult(
        t_field=t_field,
        x_grid=x,
        y_grid=y,
        devices=device_results,
        t_max=float(np.max(t_field)),
        t_mean=float(np.mean(t_field)),
        t_j_max=max(t_js) if t_js else 0.0,
        t_j_mean=sum(t_js) / len(t_js) if t_js else 0.0,
        t_j_spread=(max(t_js) - min(t_js)) if len(t_js) > 1 else 0.0,
    )
